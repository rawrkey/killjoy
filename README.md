# KILLJOY

> **The AI proposes. The AI attacks. The risk engine decides. Alpaca executes.**

KILLJOY is an autonomous AI options-trading agent built on Alpaca's paper-trading infrastructure. Its defining feature: **every trade is adversarially tested before execution**. The Kill Agent actively tries to disprove every proposal.

## Architecture

```
Market Data → Market Analyst → Strategy Agent → Kill Agent → Portfolio Check → Risk Engine → Execution → Alpaca Paper
     ↑                                                                              ↓
     └──────────────── Position Monitor ← Trade Journal ← Postmortem ←──────────────┘
```

### Core Pipeline

1. **Market Analyst** — analyzes price action, trend, momentum, volume, regime
2. **Strategy Agent** — converts thesis into options trade proposals
3. **Kill Agent** — adversarially tests every proposal (kill score 0.0-1.0)
4. **Portfolio Agent** — evaluates fit against existing positions
5. **Risk Engine** — 8 deterministic gates with final veto authority
6. **Execution Engine** — constructs and submits validated orders via Alpaca SDK
7. **Position Monitor** — watches P&L, decides HOLD/EXIT
8. **Trade Journal** — persists full trade lifecycle
9. **Postmortem** — analyzes completed trades

### Key Design Principles

- **LLM never directly controls order execution**
- **Deterministic risk engine has final veto authority**
- **Kill Agent tries to kill every trade**
- **Paper trading only** — live trading is rejected at configuration level
- **All orders originate from validated structured TradeProposal objects**

## Alpaca Integration

### Trading API / Python SDK

- `alpaca-py>=0.44,<0.45` — official Alpaca Python SDK
- Account, positions, orders, portfolio history
- Options orders via `MarketOrderRequest` with `OrderClass.MLEG`
- All Alpaca code isolated in `killjoy/alpaca/`

### MCP Server

KILLJOY is prepared for Alpaca MCP as the AI-agent tool layer:

```json
{
  "servers": {
    "alpaca": {
      "command": "uvx",
      "args": ["alpaca-mcp-server"],
      "env": {
        "ALPACA_API_KEY": "your_key",
        "ALPACA_SECRET_KEY": "your_secret",
        "ALPACA_PAPER_TRADE": "true"
      }
    }
  }
}
```

Toolsets: `account`, `trading`, `assets`, `stock-data`, `options-data`, `news`

### CLI

```bash
# Verify connectivity
python main.py --check

# Show account status
python main.py --status

# Show open positions
python main.py --positions

# Analyze market
python main.py --analyze

# Run one-shot dry run
python main.py --paper-cycle

# Run autonomous loop
python main.py --autonomous
```

## Setup

```bash
# Clone and setup
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -e ".[dev]"

# Configure credentials
copy .env.example .env
# Edit .env with your Alpaca paper trading keys

# Run
python main.py --check
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ALPACA_API_KEY` | Yes | Alpaca paper-trading API key |
| `ALPACA_SECRET_KEY` | Yes | Alpaca paper-trading secret key |
| `ALPACA_PAPER` | Yes | Must be `true` (live trading rejected) |

## Options Support

| Strategy | Status |
|----------|--------|
| Long Call | Implemented |
| Long Put | Implemented |
| Bull Call Spread | Implemented |
| Bear Put Spread | Implemented |
| Iron Condor | Implemented |

### Market Universe

SPY, QQQ, IWM, AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA (configurable)

## Risk Engine

8 deterministic gates with configurable limits:

| Gate | Default Limit |
|------|--------------|
| Max risk per trade | $500 |
| Daily loss limit | $1,000 |
| Total options exposure | $10,000 |
| Single underlying exposure | $3,000 |
| Minimum reward/risk | 1.0 |
| Minimum buying power | $500 |
| Max concurrent positions | 10 |
| Minimum confidence | 0.3 |

## Testing

```bash
pytest tests/ -v
```

62 tests covering: config, client, status, models, options (chain, greeks, liquidity, pricing), strategies, kill agent, risk engine, portfolio agent, position sizing, exposure, monitoring, journal, postmortem.

## Limitations

- MCP integration prepared but not connected (requires credentials)
- Real paper-trading connection unverified (requires credentials)
- No live-trading path exists
- Self-improvement limited to bounded parameter updates
- Options support depends on account options trading level

## Architecture Decisions

- Python 3.11+ supported; 3.13.7 used in development
- Pydantic 2.x for typed models with validation
- JSON-based trade journal (simple, no database dependency)
- Deterministic risk engine (no LLM override)
- Kill score semantics: 0.0 = kill, 1.0 = safe, threshold = 0.4
- All Alpaca SDK signatures verified against installed 0.44.0 package

## License

Internal hackathon project.
