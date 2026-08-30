# KILLJOY

> **The AI That Trades Against Itself**

An autonomous AI options trading agent that uses adversarial AI debate to challenge every trade before execution. The AI proposes, the AI attacks, the risk engine decides, and Alpaca executes on paper.

**Built for the Alpaca AI Hackathon**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-113_passing-00C853?style=flat&logo=pytest&logoColor=white)](#testing)
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

### Auto-Sell

Every cycle also monitors existing positions and auto-sells when thresholds are hit:

| Trigger | Threshold | Description |
| --- | --- | --- |
| Take-Profit | +50% | Close winning positions automatically |
| Stop-Loss | -20% | Cut losses before they deepen |
| Trailing Stop | -10% from peak | Protect profits from reversal |
| Time Exit | 45 days | Close stale positions |

---

## Autonomous Mode

KILLJOY can run fully autonomously — no browser tab needed.

1. **Enable on Dashboard** — Click "Start Auto-Trading" during market hours
2. **Cron job pings backend** every 15 minutes via cron-job.org
3. **Backend checks market hours** — only runs Mon-Fri 9:30 AM – 4:00 PM ET
4. **Each cycle**: closes winners/losers → scans for new entries → submits orders
5. **Disable anytime** — Click "Stop Auto-Trading" or disable the cron job

The "Run LIVE Cycle" and "Start Auto-Trading" buttons are **disabled outside market hours** to prevent accidental trades.

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

## Analytics Dashboard

### Kill Precision
Tracks how accurate the Kill Agent is — what percentage of killed trades would have lost, and what percentage of approved trades actually won.

### Counterfactual Portfolio
Simulates "what if we submitted rejected trades?" — tracks simulated P&L of the trades the Kill Agent blocked.

### Decision Receipts
Full audit trail for every trade decision — which agents approved, which disagreed, kill score, risk check results, and outcome.

### Strategy Graveyard
Tracks every strategy's lifecycle — wins, losses, current kill rate, and average P&L. Shows which strategies are working and which are dead.

### Agent Disagreement
Measures when the analyst, strategy agent, and kill agent disagree. High disagreement = high uncertainty.

### Judge Mode
One-page hackathon overview — shows all key metrics, pipeline status, and agent performance at a glance.

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

## LLM Architecture

KILLJOY uses a hybrid architecture where deterministic logic provides the safety foundation and LLM reasoning adds qualitative intelligence.

Each agent has two files:

- **`analyst.py`** / **`kill_agent.py`** / **`strategy_agent.py`** — Deterministic baseline. Pure rule-based logic that always runs. This is the safety fallback.
- **`llm_analyst.py`** / **`llm_kill.py`** / **`llm_strategy.py`** — LLM wrapper. Calls the deterministic version first, then enhances with AI reasoning.

1. Call deterministic version to get quantitative baseline
2. If LLM is available, serialize features and get structured AI response
3. Merge: deterministic data stays primary, AI adds qualitative reasoning
4. If LLM fails, return deterministic result unchanged

The LLM **cannot bypass safety** — deterministic gates have final veto.

### Supported Providers

Any OpenAI-compatible endpoint works: OpenAI, OmniRouter, Ollama, vLLM, LiteLLM.

---

## Deployment

### Backend (Render)

1. Push to GitHub
2. Connect repo to [Render](https://render.com)
3. Auto-deploys on push (free tier)

### Frontend (Vercel)

1. Push to GitHub
2. Connect repo to [Vercel](https://vercel.com)
3. Set environment variable: `NEXT_PUBLIC_API_URL=<your-render-url>`
4. Auto-deploys on push

### Autonomous Mode (cron-job.org)

1. Create free account at [cron-job.org](https://cron-job.org)
2. Create cron job:
   - URL: `<your-render-url>/api/cron/run`
   - Schedule: `*/15 * * * *` (every 15 minutes)
3. Click "Start Auto-Trading" on the dashboard

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

Or use the web dashboard at `http://localhost:3000`.

---

## API Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/health` | GET | Health check |
| `/api/check` | GET | Alpaca connectivity |
| `/api/account` | GET | Account info |
| `/api/positions` | GET | Open positions |
| `/api/analyze` | GET | LLM market analysis |
| `/api/paper-cycle` | GET | Dry-run cycle (no orders) |
| `/api/live-cycle` | GET | Live cycle (submits orders) |
| `/api/performance` | GET | Win rate, P&L, drawdown |
| `/api/journal` | GET | Trade journal |
| `/api/rejections` | GET | Rejection analytics |
| `/api/counterfactual` | GET | Counterfactual portfolio |
| `/api/precision` | GET | Kill precision metrics |
| `/api/receipts` | GET | Decision receipts |
| `/api/graveyard` | GET | Strategy graveyard |
| `/api/disagreement` | GET | Agent disagreement |
| `/api/judge-mode` | GET | Judge mode overview |
| `/api/autonomous/status` | GET | Autonomous mode status |
| `/api/autonomous/toggle` | POST | Toggle autonomous mode |
| `/api/cron/run` | GET | Cron endpoint (market hours check) |
| `/api/reports/last` | GET | Latest cycle report |
| `/api/reports/all` | GET | All cycle reports |

---

## Dashboard Pages

| Page | Description |
| --- | --- |
| **Dashboard** | Account overview, autonomous mode toggle, performance, kill precision, counterfactual, agent disagreement |
| **Market** | LLM analysis, correlation matrix, paper/live cycle buttons, latest cycle report (disabled outside market hours) |
| **Trades** | Alpaca orders, trade journal, decision receipts, kill precision |
| **Positions** | Open positions with live P&L |
| **Reports** | All cycle reports — filterable by dry run vs live, expandable per-symbol breakdown |
| **Judge Mode** | One-page hackathon overview with all key metrics |
| **Graveyard** | Strategy lifecycle tracker — wins, losses, kill rates |
| **Settings** | Connection config, MCP tools, risk parameters, strategy list |

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
│   └── scheduler.py          Main trading loop with auto-sell
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
│   ├── params.py             Parameter management
│   ├── counterfactual.py     Counterfactual portfolio tracker
│   ├── kill_precision.py     Kill precision analytics
│   ├── graveyard.py          Strategy graveyard lifecycle
│   ├── disagreement.py       Agent disagreement scorer
│   └── receipts.py           Decision receipt manager
├── portfolio/              Portfolio Management
│   └── manager.py            Portfolio state and evaluation
├── execution/              Order Execution
│   └── executor.py           Alpaca order submission + close
├── monitoring/             Position Monitoring
│   └── position_monitor.py   Take-profit / stop-loss / trailing stop
├── database/               Persistence
│   ├── repository.py         Trade journal (JSON)
│   └── rejected.py           "Why Not Trade?" log
├── config/                 Configuration
│   ├── settings.py           Environment settings
│   └── logging.py            Logging setup
app/                        Next.js Frontend
backend/                    FastAPI Backend
.mcp/                       MCP Server Config
tests/                      Test Suite (113 tests)
main.py                     CLI Entry Point
```

---

## Testing

```bash
pytest tests/ -v
```

113 tests covering config, Alpaca client, models, options, strategies, kill agent, risk engine, portfolio, position sizing, monitoring, journal, postmortem, LLM layer, analytics, and strategy graveyard.

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
| `NEXT_PUBLIC_API_URL` | No | — | Backend URL for Vercel frontend |

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
- LIVE buttons disabled outside market hours (Mon-Fri 9:30 AM – 4:00 PM ET)
- Autonomous mode requires explicit enable + cron job setup

---

## MCP Integration

KILLJOY integrates with the Alpaca MCP server for AI-agent tool access with account, trading, assets, stock-data, options-data, and news toolsets.

---

## License

Internal hackathon project.
