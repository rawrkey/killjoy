<div align="center">

# KILLJOY

### The AI That Trades Against Itself

**The AI proposes. The AI attacks. The risk engine decides. Alpaca executes.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Alpaca SDK](https://img.shields.io/badge/alpaca--py-0.44-000000?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMMyA3djEwbDkgNSA5LTVIN0wxMiAweiIgZmlsbD0iI0ZGQiIvPjwvc3ZnPg==&logoColor=white)](https://github.com/alpacahq/alpaca-py)
[![Tests](https://img.shields.io/badge/tests-79%20passing-00C853?style=for-the-badge&logo=pytest&logoColor=white)](#testing)
[![LLM](https://img.shields.io/badge/LLM-GPT--4o%20mini-FF6B00?style=for-the-badge&logo=openai&logoColor=white)](#llm-architecture)
[![Paper Only](https://img.shields.io/badge/mode-PAPER%20ONLY-FFD600?style=for-the-badge&logo=shield&logoColor=black)](#safety)

---

## How It Works

KILLJOY is not a simple trading bot. It's an **adversarial AI system** where multiple AI agents debate every trade before it reaches the market.

```
                 ┌─────────────────────────────────────────┐
                 │            KILLJOY PIPELINE             │
                 └─────────────────────────────────────────┘

                              MARKET DATA
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
               ┌─────────┐  ┌─────────┐  ┌─────────┐
               │ANALYST  │  │VOLATLTY │  │PORTFOLIO│
               │  AGENT  │  │ AGENT   │  │  AGENT  │
               └────┬────┘  └────┬────┘  └────┬────┘
                    │            │             │
                    └────────────┼─────────────┘
                                 ▼
                          ┌─────────────┐
                          │  STRATEGY   │
                          │    AGENT    │
                          └──────┬──────┘
                                 ▼
                          ┌─────────────┐
                          │   TRADE     │
                          │  PROPOSAL   │
                          └──────┬──────┘
                                 ▼
                          ┌─────────────┐
                          │  KILL AGENT │ ◄─── TRIES TO KILL IT
                          └──────┬──────┘
                                 ▼
                       ┌─────────────────┐
                       │   ADVERSARIAL   │
                       │     DEBATE      │
                       │  (Trader vs AI) │
                       └────────┬────────┘
                                ▼
                       ┌─────────────────┐
                       │   DETERMINISTIC │ ◄─── FINAL VETO
                       │   RISK ENGINE   │
                       └────────┬────────┘
                                ▼
                       ┌─────────────────┐
                       │     ALPACA      │
                       │  PAPER ACCOUNT  │
                       └────────┬────────┘
                                ▼
                       ┌─────────────────┐
                       │    POSITION     │
                       │    MONITOR      │
                       └────────┬────────┘
                                ▼
                       ┌─────────────────┐
                       │   POSTMORTEM    │ ◄─── LEARNS FROM EVERY TRADE
                       └─────────────────┘
```

---

## The Kill Agent: Your Worst Enemy

The Kill Agent is KILLJOY's defining feature. It's an AI agent whose **sole purpose is to find reasons to reject every trade**.

### The Adversarial Debate

```
TRADER: "NVDA momentum and volume support continued upside.
         Bull call spread limits downside exposure."

KILL AGENT: "Your thesis assumes continuation despite elevated IV
             and weakening intraday breadth. Reward/risk after
             spread cost is marginal."

TRADER: "IV is elevated, but the spread structure caps premium
         exposure. The 2.1 R/R justifies the risk."

KILL AGENT: "However, expected reward after spread cost remains
             insufficient for the volatility regime. The 30-day
             DTE adds theta decay pressure."

FINAL SCORE: 0.42 (MARGINAL) — REJECTED
REASON: Insufficient edge in current volatility regime
```

### Kill Score Semantics

| Score | Rating | Action |
|-------|--------|--------|
| `0.00 - 0.20` | **KILL** | Major red flags — trade is dead |
| `0.20 - 0.40` | **WEAK** | Significant concerns — likely reject |
| `0.40 - 0.60` | **MARGINAL** | Some concerns — proceed with caution |
| `0.60 - 0.80` | **DECENT** | Minor concerns — acceptable |
| `0.80 - 1.00` | **STRONG** | Few or no concerns — should proceed |

**Survival Score = 1 - Kill Score** (exposed for analytics)

---

## LLM Architecture

KILLJOY uses a **deterministic + LLM** hybrid architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 1: DETERMINISTIC                    │
│  Feature extraction · Regime detection · Risk calculations  │
└──────────────────────────────┬──────────────────────────────┘
                               │ features
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 2: LLM REASONING                    │
│  Thesis generation · Strategy selection · Adversarial test  │
└──────────────────────────────┬──────────────────────────────┘
                               │ structured output
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 3: SCHEMA VALIDATION                │
│  Pydantic models · Type checking · Field constraints        │
└──────────────────────────────┬──────────────────────────────┘
                               │ validated data
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 4: DETERMINISTIC SAFETY             │
│  Risk gates · Portfolio checks · Paper trading guard        │
└─────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

1. **The LLM CAN'T bypass safety** — deterministic gates have final veto
2. **The LLM CAN reason** — it explains *why*, not just *what*
3. **Fallback is graceful** — if LLM fails, deterministic rules continue
4. **Everything is structured** — Pydantic schemas ensure valid outputs

### Supported LLM Providers

Any **OpenAI-compatible** endpoint works:

| Provider | Setup |
|----------|-------|
| OpenAI | Set `KILLJOY_LLM_API_KEY` to your API key |
| OmniRouter | Set `KILLJOY_LLM_BASE_URL` to your router URL |
| Ollama | Run `ollama serve` and set base URL to `http://localhost:11434/v1` |
| vLLM | Set base URL to your vLLM server |

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/rawrkey/killjoy.git
cd killjoy

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate    # macOS/Linux

pip install -e ".[dev,api]"
```

### 2. Configure

```bash
copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux
```

Edit `.env` with your keys:

```env
# Alpaca Paper Trading (REQUIRED)
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_PAPER=true

# LLM Provider (OPTIONAL — falls back to deterministic)
KILLJOY_LLM_API_KEY=your_openai_key
KILLJOY_LLM_MODEL=gpt-4o-mini
```

### 3. Run

```bash
python main.py --check          # Verify Alpaca connectivity
python main.py --status         # Account status
python main.py --analyze        # LLM-enhanced market analysis
python main.py --paper-cycle    # One complete decision cycle (dry run)
python main.py --autonomous     # Autonomous loop (30s scans)
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `--check` | Verify Alpaca paper connectivity |
| `--status` | Show account status and positions |
| `--analyze` | Run LLM-enhanced market analysis on universe |
| `--paper-cycle` | Execute one complete decision cycle (dry run) |
| `--autonomous` | Run autonomous trading loop |
| `--interval N` | Set scan interval (default: 30s) |

---

## Risk Engine

**8 deterministic gates** — the AI **cannot** bypass them:

```
┌─────────────────────────────────────────────────────────┐
│                   RISK ENGINE GATES                      │
├─────────────────────┬─────────┬─────────────────────────┤
│ Gate                │ Limit   │ Description             │
├─────────────────────┼─────────┼─────────────────────────┤
│ Max Risk/Trade      │ $500    │ Max loss per trade      │
│ Daily Loss Limit    │ $1,000  │ Max daily portfolio loss│
│ Options Exposure    │ $10,000 │ Max total options exposure│
│ Underlying Exposure │ $3,000  │ Max per-underlying      │
│ Min Reward/Risk     │ 1.0     │ Min R/R ratio           │
│ Min Buying Power    │ $500    │ Min required BP         │
│ Max Positions       │ 10      │ Max concurrent positions│
│ Min Confidence      │ 0.3     │ Min strategy confidence │
└─────────────────────┴─────────┴─────────────────────────┘
```

**The risk engine has FINAL VETO AUTHORITY.** Even if every AI agent approves a trade, the risk engine can kill it.

---

## 5 Options Strategies

| Strategy | Regime | Description |
|----------|--------|-------------|
| **Long Call** | Uptrend | Bullish directional play |
| **Long Put** | Downtrend | Bearish directional play |
| **Bull Call Spread** | Mild Uptrend | Defined-risk bullish |
| **Bear Put Spread** | Mild Downtrend | Defined-risk bearish |
| **Iron Condor** | Sideways | Range-bound income |

Each strategy:
- Filters by regime (won't propose bullish in downtrend)
- Selects optimal DTE (7-45 days)
- Filters for liquidity (volume, OI, bid-ask spread)
- Computes precise reward/risk
- Passes through Kill Agent for adversarial testing

---

## "Why Not Trade?" Analytics

Every rejected opportunity is recorded. This is a **first-class feature**.

```python
# Example rejection analytics
{
    "total_analyzed": 100,
    "trades_executed": 7,
    "trades_rejected": 93,
    "top_rejection_reasons": {
        "kill_agent": 45,
        "portfolio": 28,
        "risk_engine": 20
    },
    "avg_kill_score": 0.34
}
```

---

## Project Structure

```
killjoy/
├── agent/                  # AI Agents
│   ├── analyst.py          # Deterministic market analysis
│   ├── llm_analyst.py      # LLM-enhanced market analysis
│   ├── strategy_agent.py   # Deterministic strategy generation
│   ├── llm_strategy.py     # LLM-enhanced strategy selection
│   ├── kill_agent.py       # Deterministic kill testing
│   ├── llm_kill.py         # LLM adversarial kill + debate
│   ├── portfolio_agent.py  # Portfolio fit evaluation
│   ├── postmortem_agent.py # Deterministic postmortem
│   ├── llm_postmortem.py   # LLM-enhanced postmortem
│   └── models.py           # Pydantic data models
├── llm/                    # LLM Provider Abstraction
│   └── provider.py         # OpenAI-compatible provider
├── alpaca/                 # Alpaca SDK Integration
│   ├── client.py           # Paper-only read client
│   ├── trading.py          # Order submission
│   ├── market_data.py      # Stock quotes/bars
│   ├── options_data.py     # Options chain/snapshots
│   └── status.py           # Connection status
├── autonomy/               # Autonomous Scheduler
│   └── scheduler.py        # Main trading loop
├── strategies/             # Options Strategies
│   ├── base.py             # Strategy base class
│   ├── long_call.py        # Long Call
│   ├── long_put.py         # Long Put
│   ├── bull_call_spread.py # Bull Call Spread
│   ├── bear_put_spread.py  # Bear Put Spread
│   └── iron_condor.py      # Iron Condor
├── risk/                   # Deterministic Risk Engine
│   ├── engine.py           # 8 risk gates
│   ├── exposure.py         # Exposure calculations
│   └── position_size.py    # Position sizing
├── options/                # Options Analytics
│   ├── chain.py            # Chain parsing
│   ├── contracts.py        # Contract selection
│   ├── greeks.py           # Black-Scholes Greeks
│   ├── liquidity.py        # Liquidity checks
│   └── pricing.py          # Pricing helpers
├── portfolio/              # Portfolio Management
│   └── manager.py          # Portfolio state/evaluation
├── execution/              # Order Execution
│   └── executor.py         # Alpaca order submission
├── monitoring/             # Position Monitoring
│   └── position_monitor.py # HOLD/EXIT decisions
├── database/               # Persistence
│   ├── repository.py       # Trade journal (JSON)
│   └── rejected.py         # "Why Not Trade?" log
├── config/                 # Configuration
│   ├── settings.py         # Environment settings
│   └── logging.py          # Logging setup
api/                        # FastAPI Backend
web/                        # Next.js Frontend
.mcp/                       # MCP Server Config
tests/                      # Test Suite
main.py                     # CLI Entry Point
```

---

## Testing

```bash
pytest tests/ -v
```

**79 tests** covering:

| Module | Tests |
|--------|-------|
| Config | Settings, validation, credentials |
| Alpaca Client | Connection, paper mode |
| Models | All Pydantic models |
| Options | Chain, Greeks, liquidity, pricing |
| Strategies | All 5 strategies |
| Kill Agent | Deterministic + LLM kill testing |
| Risk Engine | All 8 gates |
| Portfolio | Concentration, exposure |
| Position Sizing | Sizing logic |
| Monitoring | HOLD/EXIT decisions |
| Journal | Record, persist, retrieve |
| Postmortem | Win/loss analysis |
| **LLM Layer** | Provider, analysts, kill agent, debate |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ALPACA_API_KEY` | Yes | — | Alpaca API key ID |
| `ALPACA_SECRET_KEY` | Yes | — | Alpaca secret key |
| `ALPACA_PAPER` | Yes | `true` | Must be `true` (live rejected) |
| `ALPACA_PAPER_TRADE` | No | `true` | MCP paper mode |
| `ALPACA_TOOLSETS` | No | `all` | Comma-separated toolsets |
| `KILLJOY_LLM_API_KEY` | No | — | LLM API key (OpenAI-compatible) |
| `KILLJOY_LLM_BASE_URL` | No | `https://api.openai.com/v1` | LLM endpoint URL |
| `KILLJOY_LLM_MODEL` | No | `gpt-4o-mini` | LLM model name |
| `KILLJOY_LLM_TEMPERATURE` | No | `0.3` | LLM temperature |
| `KILLJOY_LLM_MAX_TOKENS` | No | `2048` | Max tokens per request |

---

## Safety Model

```
┌─────────────────────────────────────────────────────────┐
│                    SAFETY LAYERS                         │
├─────────────────────────────────────────────────────────┤
│ 1. Paper trading only (ALPACA_PAPER=true enforced)     │
│ 2. LLM never directly controls order execution         │
│ 3. Deterministic risk engine has final veto authority   │
│ 4. Kill Agent tries to kill every trade                │
│ 5. All orders originate from validated TradeProposal   │
│ 6. Schema validation on all LLM outputs                │
│ 7. No live credentials in configuration                │
│ 8. Credentials never logged or persisted               │
└─────────────────────────────────────────────────────────┘
```

---

## MCP Integration

KILLJOY integrates with the official Alpaca MCP server for AI-agent tool access:

```json
{
  "servers": {
    "alpaca": {
      "command": "uvx",
      "args": ["alpaca-mcp-server"],
      "env": {
        "ALPACA_API_KEY": "${ALPACA_API_KEY}",
        "ALPACA_SECRET_KEY": "${ALPACA_SECRET_KEY}",
        "ALPACA_PAPER_TRADE": "true",
        "ALPACA_TOOLSETS": "account,trading,assets,stock-data,options-data,news"
      }
    }
  }
}
```

**Toolsets:** `account` · `trading` · `assets` · `stock-data` · `options-data` · `news`

---

## Market Universe

```
SPY  QQQ  IWM  AAPL  MSFT  NVDA  AMZN  META  GOOGL  TSLA
```

Configurable via `killjoy/alpaca/market_data.py`.

---

## License

Internal hackathon project.

---

<div align="center">

**Built for the Alpaca AI Hackathon**

*The AI proposes. The AI attacks. The risk engine decides. Alpaca executes.*

</div>
