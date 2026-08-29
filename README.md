<div align="center">

# `⚡ KILLJOY`

### Autonomous AI Options Trading Agent

**The AI proposes. The AI attacks. The risk engine decides. Alpaca executes.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Alpaca SDK](https://img.shields.io/badge/alpaca--py-0.44-green.svg)](https://github.com/alpacahq/alpaca-py)
[![Tests](https://img.shields.io/badge/tests-62%20passing-brightgreen.svg)](#testing)
[![Paper Only](https://img.shields.io/badge/mode-paper%20only-yellow.svg)](#safety)

---

</div>

## Architecture

```
Market Data ──► Market Analyst ──► Strategy Agent ──► Kill Agent ──► Portfolio Check ──► Risk Engine ──► Execution ──► Alpaca Paper
      ↑                                                                                          │
      └──────────────────────── Position Monitor ◄── Trade Journal ◄── Postmortem ◄──────────────┘
```

Every trade passes through **9 stages** before execution. The Kill Agent actively tries to **disprove** every proposal before it reaches the risk engine.

---

## Quick Start

```bash
# Clone
git clone https://github.com/rawrkey/killjoy.git
cd killjoy

# Setup
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev,api]"

# Configure
copy .env.example .env          # Add your Alpaca paper keys

# Run CLI
python main.py --check          # Verify connectivity
python main.py --status         # Account status
python main.py --analyze        # Market analysis
python main.py --paper-cycle    # One-shot dry run
python main.py --autonomous     # Autonomous loop (30s scans)

# Run Web GUI
cd web && npm install && npm run dev    # Frontend on :3000
cd api && uvicorn main:app --port 8000  # Backend on :8000
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Kill Agent** | Adversarial testing — tries to disprove every trade proposal |
| **Risk Engine** | 8 deterministic gates with final veto authority |
| **5 Strategies** | Long Call, Long Put, Bull Call Spread, Bear Put Spread, Iron Condor |
| **MCP Server** | AI-agent tool layer for Alpaca (65 tools) |
| **Web GUI** | Real-time dashboard with account, positions, market analysis |
| **Trade Journal** | Full trade lifecycle persisted to JSON |
| **Paper Only** | Live trading rejected at configuration level |

---

## Pipeline

| Stage | Component | What It Does |
|-------|-----------|-------------|
| 1 | **Market Analyst** | Regime detection, momentum, volume analysis |
| 2 | **Strategy Agent** | Converts thesis into options trade proposals |
| 3 | **Kill Agent** | Adversarially tests every proposal (score 0.0–1.0) |
| 4 | **Portfolio Agent** | Evaluates fit against existing positions |
| 5 | **Risk Engine** | 8 deterministic gates — final veto authority |
| 6 | **Execution Engine** | Constructs and submits validated orders |
| 7 | **Position Monitor** | Watches P&L, decides HOLD/EXIT |
| 8 | **Trade Journal** | Persists full trade lifecycle |
| 9 | **Postmortem** | Analyzes completed trades |

---

## Risk Engine

8 deterministic gates — the AI **cannot** bypass them:

| Gate | Default | Description |
|------|---------|-------------|
| Max Risk/Trade | $500 | Maximum loss per single trade |
| Daily Loss Limit | $1,000 | Maximum total daily loss |
| Options Exposure | $10,000 | Maximum total options exposure |
| Underlying Exposure | $3,000 | Maximum per-underlying exposure |
| Min Reward/Risk | 1.0 | Minimum reward-to-risk ratio |
| Min Buying Power | $500 | Minimum required buying power |
| Max Positions | 10 | Maximum concurrent positions |
| Min Confidence | 0.3 | Minimum strategy confidence |

---

## MCP Server

Configured in `.mcp/config.json` for AI-agent tool access:

```json
{
  "servers": {
    "alpaca": {
      "command": "uvx",
      "args": ["alpaca-mcp-server"],
      "env": {
        "ALPACA_API_KEY": "your_key",
        "ALPACA_SECRET_KEY": "your_secret",
        "ALPACA_PAPER_TRADE": "true",
        "ALPACA_TOOLSETS": "account,trading,assets,stock-data,options-data,news"
      }
    }
  }
}
```

**Toolsets:** `account` · `trading` · `assets` · `stock-data` · `options-data` · `news`

---

## Web GUI

Real-time dashboard built with Next.js + FastAPI:

| Page | Description |
|------|-------------|
| **Dashboard** | Account overview, connection status, positions |
| **Positions** | Open positions with P&L |
| **Market** | Live regime analysis, run paper cycles |
| **Trade Log** | Alpaca orders + trade journal |
| **Settings** | Risk parameters, strategies, MCP config |

---

## Market Universe

`SPY` · `QQQ` · `IWM` · `AAPL` · `MSFT` · `NVDA` · `AMZN` · `META` · `GOOGL` · `TSLA`

Configurable via `killjoy/alpaca/market_data.py`.

---

## Testing

```bash
pytest tests/ -v
```

62 tests covering: config, client, status, models, options (chain, greeks, liquidity, pricing), strategies (all 5), kill agent, risk engine, portfolio agent, position sizing, exposure, monitoring, journal, postmortem.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ALPACA_API_KEY` | Yes | — | Alpaca API key ID |
| `ALPACA_SECRET_KEY` | Yes | — | Alpaca secret key |
| `ALPACA_PAPER` | Yes | `true` | Must be `true` (live rejected) |
| `ALPACA_PAPER_TRADE` | No | `true` | MCP paper mode |
| `ALPACA_TOOLSETS` | No | `all` | Comma-separated toolsets |

---

## Safety

- **Paper trading only** — live trading rejected at config level
- **LLM never directly controls order execution**
- **Deterministic risk engine has final veto authority**
- **Kill Agent tries to kill every trade**
- **All orders originate from validated `TradeProposal` objects**

---

## Project Structure

```
killjoy/
├── agent/          # AI agents (analyst, strategy, kill, portfolio, postmortem)
├── alpaca/         # Alpaca SDK adapters
├── autonomy/       # Autonomous scheduler
├── config/         # Settings and logging
├── database/       # Trade journal persistence
├── execution/      # Order execution
├── monitoring/     # Position monitoring
├── options/        # Options engine (chain, greeks, liquidity, pricing)
├── portfolio/      # Portfolio management
├── risk/           # Deterministic risk engine
├── strategies/     # 5 strategy implementations
api/                # FastAPI backend (web GUI)
web/                # Next.js frontend (Vercel deployable)
.mcp/               # MCP server config
```

---

## License

Internal hackathon project.
