# KILLJOY

> **The AI That Trades Against Itself**

An autonomous AI options trading agent that uses adversarial AI debate to challenge every trade before execution. The AI proposes, the AI attacks, the risk engine decides, and Alpaca executes on paper.

**Built for the Alpaca AI Hackathon**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-97_passing-00C853?style=flat&logo=pytest&logoColor=white)](#testing)
[![Paper Only](https://img.shields.io/badge/mode-paper_only-FFD600?style=flat&logo=shield&logoColor=black)](#safety)

---

## How It Works

KILLJOY runs a 9-stage autonomous pipeline where multiple AI agents analyze, propose, challenge, and validate every trade:

1. **Market Data** — Real-time quotes and options chains from Alpaca
2. **LLM Market Analyst** — AI interprets momentum, regime, and volatility
3. **LLM Strategy Agent** — AI selects the best options strategy
4. **Trade Proposal** — Structured proposal with legs, Greeks, and R/R
5. **Kill Agent** — AI adversarially attacks the proposal (tries to kill it)
6. **Adversarial Debate** — Trader and Kill Agent argue back and forth
7. **Portfolio Check** — Concentration and exposure limits
8. **Risk Engine** — 8 deterministic gates with final veto authority
9. **Alpaca Execution** — Paper order submission via Alpaca

---

## The Kill Agent

The Kill Agent is KILLJOY's defining feature. It is an AI agent whose **sole purpose is to find reasons to reject every trade**. It actively tries to disprove the thesis and kill the proposal.

### Adversarial Debate Example

```
TRADER:   "NVDA momentum and volume support continued upside.
           Bull call spread limits downside exposure."

KILL:     "Your thesis assumes continuation despite elevated IV
           and weakening intraday breadth. Reward/risk after
           spread cost is marginal."

TRADER:   "IV is elevated, but the spread structure caps premium
           exposure. The 2.1 R/R justifies the risk."

KILL:     "Expected reward after spread cost remains insufficient
           for the volatility regime. 30-day DTE adds theta decay."

SCORE: 0.42 (MARGINAL) — REJECTED
```

### Kill Score

| Score | Rating | Meaning |
| --- | --- | --- |
| `0.00 - 0.20` | **KILL** | Major red flags, trade is dead |
| `0.20 - 0.40` | **WEAK** | Significant concerns, likely reject |
| `0.40 - 0.60` | **MARGINAL** | Some concerns, proceed with caution |
| `0.60 - 0.80` | **DECENT** | Minor concerns, acceptable |
| `0.80 - 1.00` | **STRONG** | Few or no concerns, should proceed |

---

## LLM Architecture

KILLJOY uses a hybrid architecture where deterministic logic provides the safety foundation and LLM reasoning adds qualitative intelligence.

### How It Works

Each agent has two files:

- **`analyst.py`** / **`kill_agent.py`** / **`strategy_agent.py`** — Deterministic baseline. Pure rule-based logic that always runs. This is the safety fallback.
- **`llm_analyst.py`** / **`llm_kill.py`** / **`llm_strategy.py`** — LLM wrapper. Calls the deterministic version first, then enhances with AI reasoning.

The scheduler imports only the LLM versions. Each follows the same pattern:

1. Call deterministic version to get quantitative baseline
2. If LLM is available, serialize features and get structured AI response
3. Merge: deterministic data stays primary, AI adds qualitative reasoning
4. If LLM fails, return deterministic result unchanged

### Why This Architecture

- The LLM **cannot bypass safety** — deterministic gates have final veto
- The LLM **can reason** — it explains why, not just what
- **Fallback is graceful** — if LLM fails, deterministic rules continue
- **Everything is structured** — Pydantic schemas ensure valid outputs

### Supported Providers

Any OpenAI-compatible endpoint works: OpenAI, OmniRouter, Ollama, vLLM, LiteLLM.

---

## Risk Engine

8 deterministic gates that the AI cannot bypass:

| Gate | Limit | Description |
| --- | --- | --- |
| Max Risk/Trade | $500 | Maximum loss per single trade |
| Daily Loss Limit | $1,000 | Maximum total daily loss |
| Options Exposure | $10,000 | Maximum total options exposure |
| Underlying Exposure | $3,000 | Maximum per-underlying exposure |
| Min Reward/Risk | 1.0 | Minimum reward-to-risk ratio |
| Min Buying Power | $500 | Minimum required buying power |
| Max Positions | 10 | Maximum concurrent positions |
| Min Confidence | 0.3 | Minimum strategy confidence |

The risk engine has **final veto authority**. Even if every AI agent approves a trade, the risk engine can kill it.

---

## Options Strategies

5 built-in strategies, each filtered by market regime:

| Strategy | Regime | Description |
| --- | --- | --- |
| Long Call | Strong Uptrend | Bullish directional play |
| Long Put | Strong Downtrend | Bearish directional play |
| Bull Call Spread | Mild Uptrend | Defined-risk bullish |
| Bear Put Spread | Mild Downtrend | Defined-risk bearish |
| Iron Condor | Sideways | Range-bound income |

Each strategy filters by regime, selects optimal DTE (7-45 days), checks liquidity, computes precise R/R, and passes through the Kill Agent.

---

## "Why Not Trade?" Analytics

Every rejected opportunity is recorded with full reasoning:

```json
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

## Quick Start

### Install

```bash
git clone https://github.com/rawrkey/killjoy.git
cd killjoy
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,api]"
```

### Configure

```bash
copy .env.example .env
```

Edit `.env`:

```env
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_PAPER=true
KILLJOY_LLM_API_KEY=your_openai_key
KILLJOY_LLM_MODEL=gpt-4o-mini
```

### Run

```bash
python main.py --check          # Verify Alpaca connectivity
python main.py --analyze        # LLM-enhanced market analysis
python main.py --paper-cycle    # One complete decision cycle (dry run)
python main.py --autonomous     # Autonomous trading loop
```

---

## CLI Commands

| Command | Description |
| --- | --- |
| `--check` | Verify Alpaca paper connectivity |
| `--status` | Show account status and positions |
| `--analyze` | Run LLM-enhanced market analysis |
| `--paper-cycle` | Execute one complete decision cycle (dry run) |
| `--autonomous` | Run autonomous trading loop |
| `--interval N` | Set scan interval in seconds (default: 30) |

---

## Dashboard

The web dashboard provides real-time visibility into the trading system.

- **Dashboard** — Account overview, performance metrics, recent activity
- **Positions** — Open positions with live P&L
- **Market** — LLM analysis, correlation matrix, paper cycle results
- **Trades** — Alpaca orders, trade journal, rejection analytics
- **Settings** — Connection config, live risk parameters, strategy list

Start the backend and frontend (both from project root):

```bash
# Terminal 1: Backend API
cd backend && uvicorn main:app --reload

# Terminal 2: Frontend (from project root)
npm install
npm run dev
```

The dashboard runs at `http://localhost:3000`.

---

## Project Structure

```
killjoy/
├── agent/                  AI Agents
│   ├── analyst.py            Deterministic baseline
│   ├── llm_analyst.py        LLM-enhanced analysis
│   ├── strategy_agent.py     Deterministic baseline
│   ├── llm_strategy.py       LLM-enhanced selection
│   ├── kill_agent.py         Deterministic baseline
│   ├── llm_kill.py           LLM adversarial + debate
│   ├── portfolio_agent.py    Portfolio fit evaluation
│   ├── postmortem_agent.py   Deterministic baseline
│   ├── llm_postmortem.py     LLM-enhanced postmortem
│   └── models.py             Pydantic data models
├── llm/                    LLM Provider Abstraction
│   └── provider.py           OpenAI-compatible provider
├── alpaca/                 Alpaca SDK Integration
│   ├── client.py             Paper-only read client
│   ├── trading.py            Order submission
│   ├── market_data.py        Stock quotes and bars
│   ├── options_data.py       Options chain and snapshots
│   └── status.py             Connection status
├── autonomy/               Autonomous Scheduler
│   └── scheduler.py          Main trading loop
├── strategies/             Options Strategies
│   ├── base.py               Strategy base class
│   ├── long_call.py          Long Call
│   ├── long_put.py           Long Put
│   ├── bull_call_spread.py   Bull Call Spread
│   ├── bear_put_spread.py    Bear Put Spread
│   └── iron_condor.py        Iron Condor
├── risk/                   Deterministic Risk Engine
│   ├── engine.py             8 risk gates
│   ├── exposure.py           Exposure calculations
│   └── position_size.py      Position sizing
├── options/                Options Analytics
│   ├── chain.py              Chain parsing
│   ├── contracts.py          Contract selection
│   ├── greeks.py             Black-Scholes Greeks
│   ├── liquidity.py          Liquidity checks
│   └── pricing.py            Pricing helpers
├── analytics/              Performance and Audit
│   ├── performance.py        P&L, win rate, Sharpe
│   ├── events.py             JSONL audit log
│   ├── correlation.py        Cross-asset correlation
│   └── params.py             Parameter management
├── portfolio/              Portfolio Management
│   └── manager.py            Portfolio state and evaluation
├── execution/              Order Execution
│   └── executor.py           Alpaca order submission
├── monitoring/             Position Monitoring
│   └── position_monitor.py   HOLD/EXIT decisions
├── database/               Persistence
│   ├── repository.py         Trade journal (JSON)
│   └── rejected.py           "Why Not Trade?" log
├── config/                 Configuration
│   ├── settings.py           Environment settings
│   └── logging.py            Logging setup
app/                        Next.js Frontend
backend/                    FastAPI Backend
.mcp/                       MCP Server Config
tests/                      Test Suite (97 tests)
main.py                     CLI Entry Point
```

---

## Testing

```bash
pytest tests/ -v
```

97 tests covering config, Alpaca client, models, options, strategies, kill agent, risk engine, portfolio, position sizing, monitoring, journal, postmortem, LLM layer, and analytics.

---

## Environment Variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `ALPACA_API_KEY` | Yes | — | Alpaca API key ID |
| `ALPACA_SECRET_KEY` | Yes | — | Alpaca secret key |
| `ALPACA_PAPER` | Yes | `true` | Must be true (live rejected) |
| `KILLJOY_LLM_API_KEY` | No | — | LLM API key (OpenAI-compatible) |
| `KILLJOY_LLM_BASE_URL` | No | `https://api.openai.com/v1` | LLM endpoint URL |
| `KILLJOY_LLM_MODEL` | No | `gpt-4o-mini` | LLM model name |
| `KILLJOY_LLM_TEMPERATURE` | No | `0.3` | LLM temperature |
| `KILLJOY_LLM_MAX_TOKENS` | No | `2048` | Max tokens per request |

---

## Safety

- Paper trading only (`ALPACA_PAPER=true` enforced at config level)
- LLM never directly controls order execution
- Deterministic risk engine has final veto authority
- Kill Agent adversarially tests every trade
- All orders originate from validated `TradeProposal` (Pydantic)
- Schema validation on all LLM outputs
- No live credentials in configuration
- Credentials never logged or persisted

---

## MCP Integration

KILLJOY integrates with the Alpaca MCP server for AI-agent tool access with account, trading, assets, stock-data, options-data, and news toolsets.

---

## License

Internal hackathon project.
