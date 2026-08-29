"""KILLJOY API — FastAPI backend for the web GUI."""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory so we can import killjoy
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from killjoy.config.settings import Settings, get_settings

logger = logging.getLogger("killjoy.api")

# ── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    logger.info("KILLJOY API starting")
    yield
    logger.info("KILLJOY API shutting down")


app = FastAPI(
    title="KILLJOY API",
    description="Autonomous AI Options Trading Agent — Web Interface",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_trading_client():
    from killjoy.alpaca.trading import AlpacaTradingClient
    settings = get_settings()
    if not settings.has_alpaca_credentials:
        raise HTTPException(status_code=503, detail="Alpaca credentials not configured")
    return AlpacaTradingClient.from_settings(settings)


def _decimal_to_str(v: Any) -> str:
    if isinstance(v, Decimal):
        return str(v)
    return str(v)


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "alpaca_configured": settings.has_alpaca_credentials,
        "paper_mode": True,
    }


@app.get("/api/check")
def check():
    """Verify Alpaca connectivity."""
    settings = get_settings()
    if not settings.has_alpaca_credentials:
        return {"connected": False, "reason": "No credentials configured"}
    try:
        client = _get_trading_client()
        account = client.get_account()
        positions = client.get_positions()
        return {
            "connected": True,
            "paper_mode": True,
            "account_status": getattr(account, "status", "unknown"),
            "buying_power": _decimal_to_str(getattr(account, "buying_power", 0)),
            "portfolio_value": _decimal_to_str(getattr(account, "portfolio_value", 0)),
            "position_count": len(positions),
        }
    except Exception as e:
        return {"connected": False, "reason": str(e)}


@app.get("/api/account")
def account():
    """Get account details."""
    client = _get_trading_client()
    acct = client.get_account()
    return {
        "status": getattr(acct, "status", ""),
        "buying_power": _decimal_to_str(getattr(acct, "buying_power", 0)),
        "portfolio_value": _decimal_to_str(getattr(acct, "portfolio_value", 0)),
        "equity": _decimal_to_str(getattr(acct, "equity", 0)),
        "cash": _decimal_to_str(getattr(acct, "cash", 0)),
        "initial_margin": _decimal_to_str(getattr(acct, "initial_margin", 0)),
        "maintenance_margin": _decimal_to_str(getattr(acct, "maintenance_margin", 0)),
        "daytrade_count": getattr(acct, "daytrade_count", 0),
        "pattern_day_trader": getattr(acct, "pattern_day_trader", False),
        "trading_blocked": getattr(acct, "trading_blocked", False),
        "options_trading_level": getattr(acct, "options_trading_level", None),
    }


@app.get("/api/positions")
def positions():
    """Get open positions."""
    client = _get_trading_client()
    pos = client.get_positions()
    result = []
    for p in pos:
        result.append({
            "symbol": getattr(p, "symbol", ""),
            "qty": _decimal_to_str(getattr(p, "qty", 0)),
            "side": str(getattr(p, "side", "")),
            "avg_entry_price": _decimal_to_str(getattr(p, "avg_entry_price", 0)),
            "current_price": _decimal_to_str(getattr(p, "current_price", 0)),
            "unrealized_pl": _decimal_to_str(getattr(p, "unrealized_pl", 0)),
            "unrealized_plpc": _decimal_to_str(getattr(p, "unrealized_plpc", 0)),
            "market_value": _decimal_to_str(getattr(p, "market_value", 0)),
        })
    return {"positions": result, "count": len(result)}


@app.get("/api/orders")
def orders():
    """Get recent orders."""
    client = _get_trading_client()
    from alpaca.trading.enums import QueryOrderStatus
    from alpaca.trading.requests import GetOrdersRequest
    req = GetOrdersRequest(status=QueryOrderStatus.ALL)
    ords = client.get_orders(req)
    result = []
    for o in ords:
        result.append({
            "id": str(getattr(o, "id", "")),
            "symbol": getattr(o, "symbol", ""),
            "side": str(getattr(o, "side", "")),
            "type": str(getattr(o, "type", "")),
            "status": str(getattr(o, "status", "")),
            "qty": _decimal_to_str(getattr(o, "qty", 0)),
            "filled_qty": _decimal_to_str(getattr(o, "filled_qty", 0)),
            "submitted_at": str(getattr(o, "submitted_at", "")),
            "filled_at": str(getattr(o, "filled_at", "")),
        })
    return {"orders": result, "count": len(result)}


@app.get("/api/analyze")
def analyze():
    """Analyze market for top 5 symbols."""
    settings = get_settings()
    from killjoy.alpaca.market_data import MarketDataClient, DEFAULT_UNIVERSE
    from killjoy.agent.analyst import analyze_market

    market_data = MarketDataClient(settings)
    results = []
    for symbol in DEFAULT_UNIVERSE[:5]:
        try:
            thesis = analyze_market(market_data, symbol)
            results.append({
                "symbol": symbol,
                "regime": thesis.regime.value,
                "confidence": round(float(thesis.confidence), 2),
                "price": _decimal_to_str(thesis.current_price),
                "thesis": thesis.thesis,
                "observations": thesis.observations[:3] if thesis.observations else [],
            })
        except Exception as e:
            results.append({"symbol": symbol, "error": str(e)})
    return {"analyses": results}


@app.get("/api/paper-cycle")
def paper_cycle():
    """Run one dry-run paper cycle."""
    settings = get_settings()
    from killjoy.alpaca.trading import AlpacaTradingClient
    from killjoy.alpaca.market_data import MarketDataClient
    from killjoy.alpaca.options_data import OptionsDataClient
    from killjoy.portfolio.manager import PortfolioManager
    from killjoy.database.repository import TradeJournal
    from killjoy.autonomy.scheduler import KilljoyScheduler
    from killjoy.agent.models import AccountSnapshot, PositionSnapshot

    trading_client = AlpacaTradingClient.from_settings(settings)
    account = trading_client.get_account()
    positions = trading_client.get_positions()

    market_data = MarketDataClient(settings)
    options_data = OptionsDataClient(settings)
    portfolio = PortfolioManager()

    acc_snap = AccountSnapshot(
        status=getattr(account, "status", ""),
        buying_power=Decimal(str(getattr(account, "buying_power", 0))),
        portfolio_value=Decimal(str(getattr(account, "portfolio_value", 0))),
    )
    pos_snaps = [
        PositionSnapshot(
            symbol=getattr(p, "symbol", ""),
            qty=Decimal(str(getattr(p, "qty", 0))),
            side=str(getattr(p, "side", "")),
            avg_entry_price=Decimal(str(getattr(p, "avg_entry_price", 0))),
            current_price=Decimal(str(getattr(p, "current_price", 0))),
            unrealized_pl=Decimal(str(getattr(p, "unrealized_pl", 0))),
            unrealized_plpc=Decimal(str(getattr(p, "unrealized_plpc", 0))),
        )
        for p in positions
    ]
    portfolio.update(acc_snap, pos_snaps)

    journal = TradeJournal()
    scheduler = KilljoyScheduler(
        market_data=market_data,
        options_data=options_data,
        executor=None,
        portfolio=portfolio,
        journal=journal,
        dry_run=True,
    )

    results = scheduler.run_once()
    return {"results": results}


@app.get("/api/journal")
def journal():
    """Get trade journal entries."""
    from killjoy.database.repository import TradeJournal
    tj = TradeJournal()
    entries = tj.load_all()
    result = []
    for e in entries[-50:]:  # Last 50
        result.append({
            "trade_id": e.trade_id,
            "underlying": e.underlying,
            "strategy": e.strategy,
            "confidence": round(float(e.confidence), 2) if e.confidence else 0,
            "kill_score": round(float(e.kill_score), 2) if e.kill_score else 0,
            "result": e.result,
            "timestamp": str(e.timestamp) if e.timestamp else "",
        })
    return {"entries": result, "count": len(result)}
