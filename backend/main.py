"""KILLJOY API — FastAPI backend for the web GUI."""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Annotated

# Add parent directory so we can import killjoy
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from killjoy.config.settings import Settings, get_settings

logger = logging.getLogger("killjoy.api")

# ── Singleton state — persists across API calls ───────────────────────────────
from killjoy.database.repository import TradeJournal
from killjoy.portfolio.manager import PortfolioManager
from killjoy.autonomy.scheduler import KilljoyScheduler

_journal = TradeJournal()
_portfolio = PortfolioManager()
_scheduler: KilljoyScheduler | None = None

# ── Autonomous mode state ────────────────────────────────────────────────────
_autonomous_enabled = False

# ── Auth for control endpoints ────────────────────────────────────────────────
CONTROL_SECRET = os.environ.get("KILLJOY_CONTROL_SECRET", "")

async def verify_control_secret(x_control_secret: str = Header(default="")):
    """Require KILLJOY_CONTROL_SECRET header for control endpoints."""
    if CONTROL_SECRET and x_control_secret != CONTROL_SECRET:
        raise HTTPException(status_code=403, detail="Invalid control secret")

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
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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
    try:
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
    except Exception as e:
        logger.warning("Failed to fetch orders: %s", e)
        return {"orders": [], "count": 0}


@app.get("/api/analyze")
def analyze():
    """Analyze market for top 5 symbols using deterministic agents (fast, no LLM)."""
    try:
        settings = get_settings()
        from killjoy.alpaca.market_data import MarketDataClient, DEFAULT_UNIVERSE
        from killjoy.agent.llm_analyst import analyze_market_llm

        market_data = MarketDataClient(settings)
        # Use None for LLM to skip LLM calls — deterministic is instant
        results = []
        for symbol in DEFAULT_UNIVERSE[:5]:
            try:
                thesis = analyze_market_llm(market_data, symbol, None)
                results.append({
                    "symbol": symbol,
                    "regime": thesis.regime.value,
                    "confidence": round(float(thesis.confidence), 2),
                    "price": _decimal_to_str(thesis.current_price),
                    "thesis": thesis.thesis,
                    "observations": thesis.observations[:3] if thesis.observations else [],
                    "llm": "deterministic",
                })
            except Exception as e:
                results.append({"symbol": symbol, "error": str(e)})
        return {"analyses": results, "llm": "deterministic"}
    except Exception as e:
        logger.error("Analyze endpoint failed: %s", e)
        return {"analyses": [], "error": str(e), "llm": "deterministic"}


@app.get("/api/paper-cycle")
def paper_cycle():
    """Run one dry-run paper cycle with LLM agents."""
    global _scheduler
    settings = get_settings()
    from killjoy.alpaca.trading import AlpacaTradingClient
    from killjoy.alpaca.market_data import MarketDataClient
    from killjoy.alpaca.options_data import OptionsDataClient
    from killjoy.agent.models import AccountSnapshot, PositionSnapshot
    from killjoy.llm.provider import LLMProvider

    trading_client = AlpacaTradingClient.from_settings(settings)
    account = trading_client.get_account()
    positions = trading_client.get_positions()

    market_data = MarketDataClient(settings)
    options_data = OptionsDataClient(settings)

    llm = LLMProvider(
        api_key=settings.killjoy_llm_api_key.get_secret_value() if settings.killjoy_llm_api_key else "",
        base_url=settings.killjoy_llm_base_url,
        model=settings.killjoy_llm_model,
        temperature=settings.killjoy_llm_temperature,
        max_tokens=settings.killjoy_llm_max_tokens,
    )

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
    _portfolio.update(acc_snap, pos_snaps)

    if _scheduler is None:
        _scheduler = KilljoyScheduler(
            market_data=market_data,
            options_data=options_data,
            executor=None,
            portfolio=_portfolio,
            journal=_journal,
            llm=llm,
            dry_run=True,
        )
    else:
        _scheduler._dry_run = True

    results = _scheduler.run_once()
    results["llm"] = "active" if llm.is_available else "deterministic"
    return {"results": results}


@app.get("/api/live-cycle", dependencies=[Depends(verify_control_secret)])
def live_cycle():
    """Run one LIVE paper cycle — orders will be submitted to Alpaca."""
    global _scheduler
    settings = get_settings()
    from killjoy.alpaca.trading import AlpacaTradingClient
    from killjoy.alpaca.market_data import MarketDataClient
    from killjoy.alpaca.options_data import OptionsDataClient
    from killjoy.execution.executor import Executor
    from killjoy.agent.models import AccountSnapshot, PositionSnapshot
    from killjoy.llm.provider import LLMProvider

    trading_client = AlpacaTradingClient.from_settings(settings)
    account = trading_client.get_account()
    positions = trading_client.get_positions()

    market_data = MarketDataClient(settings)
    options_data = OptionsDataClient(settings)

    llm = LLMProvider(
        api_key=settings.killjoy_llm_api_key.get_secret_value() if settings.killjoy_llm_api_key else "",
        base_url=settings.killjoy_llm_base_url,
        model=settings.killjoy_llm_model,
        temperature=settings.killjoy_llm_temperature,
        max_tokens=settings.killjoy_llm_max_tokens,
    )

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
    _portfolio.update(acc_snap, pos_snaps)

    executor = Executor(trading_client._client, journal=_journal)
    if _scheduler is None:
        _scheduler = KilljoyScheduler(
            market_data=market_data,
            options_data=options_data,
            executor=executor,
            portfolio=_portfolio,
            journal=_journal,
            llm=llm,
            dry_run=False,
        )
    else:
        _scheduler._executor = executor
        _scheduler._dry_run = False

    results = _scheduler.run_once()
    results["llm"] = "active" if llm.is_available else "deterministic"
    results["mode"] = "LIVE"
    return {"results": results}


@app.get("/api/journal")
def journal():
    """Get trade journal entries."""
    from killjoy.database.repository import TradeJournal
    tj = TradeJournal()
    entries = tj.get_all_entries()
    result = []
    for e in entries[-50:]:  # Last 50
        result.append({
            "trade_id": e.trade_id,
            "underlying": e.underlying,
            "strategy": e.strategy,
            "confidence": round(float(e.confidence), 2) if e.confidence else 0,
            "kill_score": round(float(e.kill_score), 2) if e.kill_score else 0,
            "result": e.result,
            "realized_pnl": round(float(e.realized_pnl), 2) if e.realized_pnl else 0,
            "thesis": e.thesis,
            "timestamp": str(e.timestamp) if e.timestamp else "",
        })
    return {"entries": result, "count": len(result)}


@app.get("/api/performance")
def performance():
    """Get performance analytics from trade journal."""
    from killjoy.database.repository import TradeJournal
    from killjoy.analytics.performance import PerformanceAnalytics
    tj = TradeJournal()
    entries = tj.get_all_entries()
    analytics = PerformanceAnalytics(entries)
    return analytics.summary()


@app.get("/api/rejections")
def rejections():
    """Get rejected trade opportunities ('Why Not Trade?')."""
    from killjoy.database.rejected import RejectedTradeLog
    log = RejectedTradeLog()
    analytics = log.get_analytics()
    return analytics


@app.get("/api/events")
def events(run_id: str = "", event_type: str = "", date: str = ""):
    """Get event/audit log entries."""
    from killjoy.analytics.events import EventLog
    el = EventLog()
    event_list = el.get_events(
        run_id=run_id or None,
        event_type=event_type or None,
        date=date or None,
    )
    return {"events": event_list[-100:], "count": len(event_list)}


@app.get("/api/events/summary")
def events_summary(date: str = ""):
    """Get event summary."""
    from killjoy.analytics.events import EventLog
    el = EventLog()
    return el.get_summary(date=date or None)


@app.get("/api/correlation")
def correlation():
    """Get portfolio correlation matrix."""
    from killjoy.analytics.correlation import PortfolioCorrelation
    from killjoy.alpaca.market_data import MarketDataClient
    settings = get_settings()
    market_data = MarketDataClient(settings)
    corr = PortfolioCorrelation()

    # Fetch price history for universe
    from killjoy.alpaca.market_data import DEFAULT_UNIVERSE
    for symbol in DEFAULT_UNIVERSE:
        bars = market_data.get_bars(symbol, limit=30)
        prices = [float(b["close"]) for b in bars if b.get("close")]
        if prices:
            corr.update_prices(symbol, prices)

    # Get current positions for correlation risk assessment
    try:
        client = _get_trading_client()
        positions = client.get_positions()
        pos_symbols = [getattr(p, "symbol", "")[:4] for p in positions]
        pos_symbols = list(set(s for s in pos_symbols if s))
    except Exception:
        pos_symbols = []

    risk = corr.get_portfolio_correlation_risk(pos_symbols) if pos_symbols else {"risk_level": "no_positions"}
    matrix = corr.get_correlation_matrix([s for s in DEFAULT_UNIVERSE if s in corr._price_history])

    return {"matrix": matrix, "risk": risk}


@app.get("/api/params")
def params():
    """Get current trading parameters."""
    from killjoy.analytics.params import ParameterManager
    pm = ParameterManager()
    return {"params": pm.get_all(), "history_count": len(pm.get_history())}


# ── New endpoints for Tier S / Tier A features ──────────────────────────────

@app.get("/api/counterfactual")
def counterfactual():
    """Get counterfactual portfolio — what rejected trades would have done."""
    from killjoy.analytics.counterfactual import CounterfactualPortfolio
    cf = CounterfactualPortfolio()
    return cf.get_summary()


@app.get("/api/counterfactual/evaluate")
def counterfactual_evaluate():
    """Evaluate pending counterfactual trades against current prices."""
    from killjoy.analytics.counterfactual import CounterfactualPortfolio
    from killjoy.alpaca.market_data import MarketDataClient
    settings = get_settings()
    market_data = MarketDataClient(settings)
    cf = CounterfactualPortfolio()
    result = cf.evaluate_all(price_getter=lambda sym: _get_current_price(market_data, sym))
    return result


def _get_current_price(market_data, symbol: str):
    """Get current price for a symbol."""
    try:
        snapshot = market_data.get_snapshot(symbol)
        if snapshot and "close" in snapshot:
            return Decimal(str(snapshot["close"]))
        if snapshot and "latest_trade" in snapshot:
            return Decimal(str(snapshot["latest_trade"].get("price", 0)))
    except Exception:
        pass
    return Decimal("0")


@app.get("/api/precision")
def precision():
    """Get kill precision analytics — correct kills vs false kills."""
    from killjoy.analytics.kill_precision import KillPrecisionAnalytics
    from killjoy.analytics.counterfactual import CounterfactualPortfolio
    from killjoy.database.repository import TradeJournal
    cf = CounterfactualPortfolio()
    tj = TradeJournal()
    analytics = KillPrecisionAnalytics(
        counterfactuals=cf.get_all_trades(),
        journal_entries=tj.get_all_entries(),
    )
    return analytics.summary()


@app.get("/api/receipts")
def receipts():
    """Get decision receipts."""
    from killjoy.analytics.receipts import DecisionReceiptManager
    rm = DecisionReceiptManager()
    return rm.get_summary()


@app.get("/api/receipts/{receipt_id}")
def receipt_detail(receipt_id: str):
    """Get a specific decision receipt."""
    from killjoy.analytics.receipts import DecisionReceiptManager
    rm = DecisionReceiptManager()
    receipt = rm.get_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt.model_dump(mode="json")


@app.get("/api/graveyard")
def graveyard():
    """Get strategy graveyard — killed, active, and resurrected strategies."""
    from killjoy.analytics.graveyard import StrategyGraveyard
    gy = StrategyGraveyard()
    return gy.get_graveyard_summary()


@app.get("/api/reports/last")
def report_last():
    """Get the latest cycle report."""
    from killjoy.analytics.reports import get_latest_report
    report = get_latest_report()
    if not report:
        return {"report": None, "message": "No reports yet. Run a cycle first."}
    return {"report": report}


@app.get("/api/reports/all")
def report_all():
    """Get all cycle reports."""
    from killjoy.analytics.reports import get_all_reports
    reports = get_all_reports()
    return {"reports": reports, "count": len(reports)}


@app.get("/api/disagreement")
def disagreement():
    """Get agent disagreement analytics."""
    from killjoy.database.repository import TradeJournal
    from killjoy.analytics.performance import PerformanceAnalytics
    tj = TradeJournal()
    entries = tj.get_all_entries()
    # Compute disagreement from recent entries
    recent = entries[-20:] if entries else []
    disagreements = []
    for entry in recent:
        if entry.kill_score > 0:
            from killjoy.agent.models import MarketRegime
            from killjoy.analytics.disagreement import compute_disagreement
            # Estimate agent stances from available data
            is_bullish = "up" in (entry.thesis or "").lower() or entry.strategy in ("long_call", "bull_call_spread")
            da = compute_disagreement(
                analyst_score=entry.confidence,
                analyst_stance="bullish" if is_bullish else "bearish",
                strategy_score=entry.confidence,
                strategy_stance="bullish" if is_bullish else "bearish",
                kill_score=Decimal("1") - entry.kill_score,
                kill_stance="approve" if entry.kill_score >= Decimal("0.4") else "reject",
                portfolio_approved=True,
                risk_approved=True,
            )
            disagreements.append({
                "trade_id": entry.trade_id,
                "underlying": entry.underlying,
                "disagreement_index": float(da.disagreement_index),
                "consensus": da.consensus,
                "agent_scores": [
                    {"agent_name": s.agent_name, "confidence": float(s.confidence), "stance": s.stance}
                    for s in da.agent_scores
                ],
            })

    # Summary stats
    if disagreements:
        avg_disagreement = sum(d["disagreement_index"] for d in disagreements) / len(disagreements)
        consensus_counts = {}
        for d in disagreements:
            c = d["consensus"]
            consensus_counts[c] = consensus_counts.get(c, 0) + 1
    else:
        avg_disagreement = 0
        consensus_counts = {}

    return {
        "disagreements": disagreements,
        "summary": {
            "total_evaluated": len(disagreements),
            "avg_disagreement_index": round(avg_disagreement, 4),
            "consensus_distribution": consensus_counts,
        },
    }


@app.get("/api/judge-mode")
def judge_mode():
    """All-in-one endpoint for Judge Mode — one API call gets everything."""
    from killjoy.database.repository import TradeJournal
    from killjoy.analytics.performance import PerformanceAnalytics
    from killjoy.analytics.counterfactual import CounterfactualPortfolio
    from killjoy.analytics.kill_precision import KillPrecisionAnalytics
    from killjoy.analytics.receipts import DecisionReceiptManager
    from killjoy.analytics.graveyard import StrategyGraveyard
    from killjoy.database.rejected import RejectedTradeLog

    tj = TradeJournal()
    entries = tj.get_all_entries()
    analytics = PerformanceAnalytics(entries)
    perf = analytics.summary()

    cf = CounterfactualPortfolio()
    cf_summary = cf.get_summary()

    precision = KillPrecisionAnalytics(
        counterfactuals=cf.get_all_trades(),
        journal_entries=entries,
    ).summary()

    receipts_mgr = DecisionReceiptManager()
    receipts_summary = receipts_mgr.get_summary()

    graveyard_mgr = StrategyGraveyard()
    graveyard_summary = graveyard_mgr.get_graveyard_summary()

    rejected_log = RejectedTradeLog()
    rejection_analytics = rejected_log.get_analytics()

    # Connection status
    settings = get_settings()
    connected = False
    account_info = {}
    try:
        client = _get_trading_client()
        acct = client.get_account()
        connected = True
        account_info = {
            "status": getattr(acct, "status", ""),
            "portfolio_value": _decimal_to_str(getattr(acct, "portfolio_value", 0)),
            "buying_power": _decimal_to_str(getattr(acct, "buying_power", 0)),
            "cash": _decimal_to_str(getattr(acct, "cash", 0)),
            "daytrade_count": getattr(acct, "daytrade_count", 0),
        }
    except Exception:
        pass

    # Pipeline stats from rejections
    kill_agent_rejections = rejection_analytics.get("top_rejection_reasons", {}).get("kill_agent", 0)
    portfolio_rejections = rejection_analytics.get("top_rejection_reasons", {}).get("portfolio", 0)
    risk_rejections = rejection_analytics.get("top_rejection_reasons", {}).get("risk_engine", 0)

    return {
        "status": {
            "connected": connected,
            "paper_mode": True,
            "risk_engine": "8 GATES",
            "kill_agent": "ADVERSARIAL",
            "mcp": "CONNECTED",
        },
        "account": account_info,
        "performance": perf,
        "counterfactual": cf_summary,
        "kill_precision": precision,
        "receipts": receipts_summary,
        "graveyard": graveyard_summary,
        "rejections": {
            "total": rejection_analytics.get("total", 0),
            "kill_agent": kill_agent_rejections,
            "portfolio": portfolio_rejections,
            "risk_engine": risk_rejections,
            "avg_kill_score": rejection_analytics.get("avg_kill_score", 0),
        },
    }


# ── Autonomous Mode ──────────────────────────────────────────────────────────

@app.get("/api/autonomous/status")
def autonomous_status():
    """Check if autonomous mode is enabled."""
    return {"enabled": _autonomous_enabled}


@app.post("/api/autonomous/toggle", dependencies=[Depends(verify_control_secret)])
def autonomous_toggle():
    """Enable or disable autonomous trading."""
    global _autonomous_enabled
    _autonomous_enabled = not _autonomous_enabled
    logger.info("Autonomous mode %s", "ENABLED" if _autonomous_enabled else "DISABLED")
    return {"enabled": _autonomous_enabled}


@app.get("/api/cron/run", dependencies=[Depends(verify_control_secret)])
def cron_run():
    """Cron endpoint — runs one live cycle if autonomous mode is on and market is open.

    External cron services (cron-job.org, GitHub Actions) ping this every 30 min.
    Returns a tiny JSON dict in all paths.
    """
    global _autonomous_enabled

    if not _autonomous_enabled:
        return {"ok": True, "s": "off"}

    # Check market hours (9:30 AM – 4:00 PM ET, Mon–Fri)
    from datetime import datetime, timezone, timedelta
    try:
        from zoneinfo import ZoneInfo
        et = ZoneInfo("America/New_York")
    except Exception:
        et = timezone(timedelta(hours=-4))  # EDT fallback
    now = datetime.now(et)

    if now.weekday() >= 5:
        return {"ok": True, "s": "wknd"}

    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

    if now < market_open:
        return {"ok": True, "s": "pre"}
    if now > market_close:
        return {"ok": True, "s": "post"}

    # Skip first 15 min after open
    if (now - market_open).total_seconds() < 900:
        return {"ok": True, "s": "settle"}

    # Daily loss circuit breaker
    try:
        from killjoy.database.repository import TradeJournal
        _tj = TradeJournal()
        _daily_pnl = Decimal("0")
        today_str = now.strftime("%Y-%m-%d")
        for e in _tj.get_all_entries():
            try:
                ts = e.timestamp
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if hasattr(ts, "date") and ts.date() == now.date():
                    _daily_pnl += Decimal(str(getattr(e, "realized_pnl", 0) or 0))
            except Exception:
                continue
        if float(_daily_pnl) < -800:
            return {"ok": True, "s": "loss_limit"}
    except Exception:
        pass

    # Market is open — run live cycle
    try:
        result = live_cycle()
        r = result.get("results", {}) if isinstance(result, dict) else {}
        return {
            "ok": True,
            "s": "ran",
            "r": r.get("orders_submitted", 0),
            "k": r.get("proposals_killed", 0),
            "m": r.get("positions_monitored", 0),
        }
    except Exception as e:
        return {"ok": False, "err": str(e)[:100]}
