"""KILLJOY — Autonomous AI Options Trading Agent.

Usage:
    python main.py --check        Verify Alpaca connectivity
    python main.py --analyze      Analyze market for universe
    python main.py --paper-cycle  Run one complete paper decision cycle
    python main.py --autonomous   Run the autonomous trading loop
    python main.py --status       Show account status
    python main.py --positions    Show open positions
"""

from __future__ import annotations

import argparse
import logging
import sys
from decimal import Decimal

from killjoy.config import get_settings
from killjoy.config.logging import configure_logging

logger = logging.getLogger("killjoy")


def cmd_check() -> int:
    """Verify Alpaca paper connectivity."""
    settings = get_settings()
    if not settings.has_alpaca_credentials:
        print("KILLJOY\nAlpaca: NOT CONFIGURED\nPaper Trading: TRUE")
        print("Set paper credentials in an untracked .env to verify connectivity.")
        return 0

    try:
        from killjoy.alpaca.trading import AlpacaTradingClient
        client = AlpacaTradingClient.from_settings(settings)
        account = client.get_account()
        positions = client.get_positions()
        print("KILLJOY — Connectivity Check")
        print(f"Alpaca: CONNECTED")
        print(f"Paper Trading: TRUE")
        print(f"Account Status: {getattr(account, 'status', 'unknown')}")
        print(f"Buying Power: ${getattr(account, 'buying_power', 0)}")
        print(f"Portfolio Value: ${getattr(account, 'portfolio_value', 0)}")
        print(f"Open Positions: {len(positions)}")
        return 0
    except Exception as e:
        print(f"KILLJOY\nAlpaca: UNAVAILABLE\nReason: {e}")
        return 1


def cmd_status() -> int:
    """Show detailed account status."""
    settings = get_settings()
    if not settings.has_alpaca_credentials:
        print("No Alpaca credentials configured.")
        return 1

    try:
        from killjoy.alpaca.trading import AlpacaTradingClient
        from killjoy.alpaca.status import format_connection_status, get_connection_status
        client = AlpacaTradingClient.from_settings(settings)
        account, positions = get_connection_status(client)
        print(format_connection_status(account, positions))
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_positions() -> int:
    """Show open positions."""
    settings = get_settings()
    if not settings.has_alpaca_credentials:
        print("No Alpaca credentials configured.")
        return 1

    try:
        from killjoy.alpaca.trading import AlpacaTradingClient
        client = AlpacaTradingClient.from_settings(settings)
        positions = client.get_positions()
        if not positions:
            print("No open positions.")
            return 0

        print(f"Open Positions ({len(positions)}):")
        print("-" * 60)
        for pos in positions:
            sym = getattr(pos, "symbol", "?")
            qty = getattr(pos, "qty", 0)
            side = getattr(pos, "side", "?")
            entry = getattr(pos, "avg_entry_price", 0)
            current = getattr(pos, "current_price", 0)
            pnl = getattr(pos, "unrealized_pl", 0)
            print(f"  {sym}: {side} {qty} @ ${entry} → ${current} (P&L: ${pnl})")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_analyze() -> int:
    """Analyze market for the configured universe."""
    settings = get_settings()
    if not settings.has_alpaca_credentials:
        print("Alpaca credentials required for market analysis.")
        return 1

    try:
        from killjoy.alpaca.market_data import MarketDataClient, DEFAULT_UNIVERSE
        from killjoy.agent.llm_analyst import analyze_market_llm

        market_data = MarketDataClient(settings)
        llm = _init_llm(settings)
        llm_status = "LLM: ACTIVE" if llm.is_available else "LLM: UNAVAILABLE (deterministic fallback)"
        print("KILLJOY — Market Analysis")
        print(f"{llm_status}")
        print("=" * 60)

        for symbol in DEFAULT_UNIVERSE[:5]:  # Top 5
            thesis = analyze_market_llm(market_data, symbol, llm)
            print(f"\n{symbol}: {thesis.regime.value} (conf: {thesis.confidence:.2f})")
            print(f"  Price: ${thesis.current_price}")
            print(f"  Thesis: {thesis.thesis}")
            if thesis.observations:
                for obs in thesis.observations[:3]:
                    print(f"  • {obs}")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def _init_llm(settings) -> "LLMProvider":
    """Initialize the LLM provider from settings."""
    from killjoy.llm.provider import LLMProvider
    api_key = ""
    if settings.killjoy_llm_api_key:
        api_key = settings.killjoy_llm_api_key.get_secret_value()
    return LLMProvider(
        api_key=api_key,
        base_url=settings.killjoy_llm_base_url,
        model=settings.killjoy_llm_model,
        temperature=settings.killjoy_llm_temperature,
        max_tokens=settings.killjoy_llm_max_tokens,
    )


def cmd_paper_cycle() -> int:
    """Run one complete paper decision cycle."""
    settings = get_settings()
    if not settings.has_alpaca_credentials:
        print("Alpaca credentials required for paper trading cycle.")
        return 1

    try:
        from killjoy.alpaca.trading import AlpacaTradingClient
        from killjoy.alpaca.market_data import MarketDataClient
        from killjoy.alpaca.options_data import OptionsDataClient
        from killjoy.portfolio.manager import PortfolioManager
        from killjoy.database.repository import TradeJournal
        from killjoy.autonomy.scheduler import KilljoyScheduler

        # Initialize components
        trading_client = AlpacaTradingClient.from_settings(settings)
        account = trading_client.get_account()
        positions = trading_client.get_positions()

        market_data = MarketDataClient(settings)
        options_data = OptionsDataClient(settings)
        portfolio = PortfolioManager()
        llm = _init_llm(settings)

        from killjoy.agent.models import AccountSnapshot, PositionSnapshot
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
            executor=None,  # Dry run first
            portfolio=portfolio,
            journal=journal,
            llm=llm,
            dry_run=True,
        )

        llm_status = "LLM: ACTIVE" if llm.is_available else "LLM: UNAVAILABLE (deterministic fallback)"
        print(f"KILLJOY — Paper Decision Cycle (DRY RUN)")
        print(f"{llm_status}")
        print("=" * 60)
        results = scheduler.run_once()
        print(f"\nScan Results:")
        for k, v in results.items():
            print(f"  {k}: {v}")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_autonomous(scan_interval: int = 30) -> int:
    """Run the autonomous trading loop."""
    settings = get_settings()
    if not settings.has_alpaca_credentials:
        print("Alpaca credentials required for autonomous trading.")
        return 1

    try:
        from killjoy.alpaca.trading import AlpacaTradingClient
        from killjoy.alpaca.market_data import MarketDataClient
        from killjoy.alpaca.options_data import OptionsDataClient
        from killjoy.portfolio.manager import PortfolioManager
        from killjoy.database.repository import TradeJournal
        from killjoy.execution.executor import Executor
        from killjoy.autonomy.scheduler import KilljoyScheduler

        # Initialize components
        trading_client = AlpacaTradingClient.from_settings(settings)
        account = trading_client.get_account()
        positions = trading_client.get_positions()

        market_data = MarketDataClient(settings)
        options_data = OptionsDataClient(settings)
        portfolio = PortfolioManager()
        journal = TradeJournal()
        executor = Executor(trading_client._trading_client, journal=journal)
        llm = _init_llm(settings)

        from killjoy.agent.models import AccountSnapshot, PositionSnapshot
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

        scheduler = KilljoyScheduler(
            market_data=market_data,
            options_data=options_data,
            executor=executor,
            portfolio=portfolio,
            journal=journal,
            llm=llm,
            scan_interval=scan_interval,
            dry_run=False,
        )

        llm_status = "LLM: ACTIVE" if llm.is_available else "LLM: UNAVAILABLE (deterministic fallback)"
        print("KILLJOY — Autonomous Trading Loop")
        print(f"{llm_status}")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        scheduler.run_loop()
        return 0

    except KeyboardInterrupt:
        print("\nShutting down.")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main() -> int:
    configure_logging()
    parser = argparse.ArgumentParser(description="KILLJOY — Autonomous AI Options Trading Agent")
    parser.add_argument("--check", action="store_true", help="Verify Alpaca connectivity")
    parser.add_argument("--status", action="store_true", help="Show account status")
    parser.add_argument("--positions", action="store_true", help="Show open positions")
    parser.add_argument("--analyze", action="store_true", help="Analyze market for universe")
    parser.add_argument("--paper-cycle", action="store_true", help="Run one paper decision cycle (dry run)")
    parser.add_argument("--autonomous", action="store_true", help="Run autonomous trading loop")
    parser.add_argument("--interval", type=int, default=30, help="Scan interval in seconds (default: 30)")

    args = parser.parse_args()

    if args.check:
        return cmd_check()
    elif args.status:
        return cmd_status()
    elif args.positions:
        return cmd_positions()
    elif args.analyze:
        return cmd_analyze()
    elif args.paper_cycle:
        return cmd_paper_cycle()
    elif args.autonomous:
        return cmd_autonomous(scan_interval=args.interval)
    else:
        # Default: show status
        return cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
