# KILLJOY

> **The Autonomous Options Trading Agent with Adversarial AI Debate**  
> *The AI Proposes. The AI Attacks. The Risk Engine Decides. Alpaca Executes on Paper.*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-113_passing-00C853?style=flat&logo=pytest&logoColor=white)](#testing--verification)
[![Paper Only](https://img.shields.io/badge/mode-paper_only_enforced-FFD600?style=flat&logo=shield&logoColor=black)](#security--paper-only-guarantee)
[![Agensi.io](https://img.shields.io/badge/agensi.io-ready_skill-6366F1?style=flat&logo=codewars&logoColor=white)](#agensiio--agent-skill-integration)
[![Zero-Config Sandbox](https://img.shields.io/badge/sandbox-zero_config-10B981?style=flat)](#zero-config-sandbox-mode)
[![Next.js 15](https://img.shields.io/badge/frontend-Next.js_15-000000?style=flat&logo=next.js&logoColor=white)](#institutional-trading-terminal)

---

## Table of Contents

- [Why KILLJOY?](#why-killjoy)
- [How It Works: 9-Stage Pipeline](#how-it-works-9-stage-pipeline)
- [Zero-Config Sandbox Mode](#zero-config-sandbox-mode)
- [Agensi.io & Agent Skill Integration](#agensiio--agent-skill-integration)
- [Command Line Interface (CLI)](#command-line-interface-cli)
- [Supported Options Strategies](#supported-options-strategies)
- [Deterministic 8-Gate Risk Engine](#deterministic-8-gate-risk-engine)
- [The Adversarial Kill Agent](#the-adversarial-kill-agent)
- [Autonomous Execution & Safeguards](#autonomous-execution--safeguards)
- [Institutional Trading Terminal](#institutional-trading-terminal)
- [Capital Saved & Audit Analytics](#capital-saved--audit-analytics)
- [API Reference](#api-reference)
- [Project Architecture](#project-architecture)
- [Quick Start](#quick-start)
- [Testing & Verification](#testing--verification)
- [Security & Paper-Only Guarantee](#security--paper-only-guarantee)
- [License & Disclaimer](#license--disclaimer)

---

## Why KILLJOY?

Most LLM trading agents suffer from **fatal flaws**:
1. **Bullish Hallucination & Confirmation Bias**: LLMs naturally rationalize trades and fall victim to recency bias.
2. **Missing Risk Guardrails**: Prompt-engineered "risk management" can be bypassed by edge cases or model drift.
3. **Black-Box Execution**: Trades are placed without audit trails, counterfactual tracking, or explainability.

**KILLJOY solves this by trading against itself.**

```
       +-------------------------------------------------------------+
       |                     PROPOSAL PHASE                          |
       |  Market Analyst + Strategy Agent generate trade candidate   |
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |                   ADVERSARIAL ATTACK                        |
       |  Kill Agent runs 6 stress tests to disprove thesis & abort  |
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |                   DETERMINISTIC VETO                        |
       |  8 Hard Mathematical Risk Gates (Model CANNOT bypass)       |
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |                 EXECUTION & VERIFICATION                    |
       |  Alpaca Paper Submission + Decision Receipts + Capital Log  |
       +-------------------------------------------------------------+
```

Every single trade must survive an adversarial gauntlet. If the Kill Agent detects IV crush, liquidity traps, or momentum decay, the trade is discarded. If the deterministic Risk Engine detects breached exposure caps, the trade is vetoed with zero exceptions.

---

## How It Works: 9-Stage Pipeline

```
[1. Market Data] ──> [2. Market Analyst] ──> [3. Strategy Agent]
                                                     │
                                                     ▼
[6. Debate/Refine] <── [5. Kill Agent] <── [4. Trade Proposal]
        │
        ▼
[7. Portfolio Check] ──> [8. Risk Engine] ──> [9. Alpaca Paper Order]
```

1. **Market Data Ingestion** — Real-time quote bars and option chains via Alpaca Market Data API (or Zero-Config Sandbox when offline).
2. **Market Analyst** — Computes ATR, RSI, momentum velocity, moving average regimes, and volatility rank.
3. **Strategy Agent** — Maps regime to suitable options structure (Long Call, Long Put, Spreads, Condor, Cash-Secured Put).
4. **Trade Proposal Generator** — Builds exact contract specifications, strike spacing, DTE window (7–45 days), and Greeks ($\Delta, \Gamma, \Theta, \text{Vega}$).
5. **Kill Agent Attack** — Subject proposal to 6 adversarial stress tests (Momentum Reversal, IV Crush, Bid-Ask Spread Drag, Thesis Contradiction, R/R Skew, Timing Decay).
6. **Adversarial Debate** — Trader agent and Kill agent exchange counter-theses (Groq/OpenAI LLM or rule-based deterministic reasoning).
7. **Portfolio Correlation Check** — Evaluates existing asset concentration and prevents duplicate underlying exposure.
8. **Deterministic Risk Engine** — 8 mathematical limits evaluate risk/reward, buying power, and daily circuit breakers with final veto power.
9. **Alpaca Paper Execution** — Submits limit/market orders to Alpaca Paper Trading API and generates a cryptographically sound decision receipt.

---

## Zero-Config Sandbox Mode

You do **not** need an Alpaca account or any API keys to evaluate, test, or run KILLJOY.

When credentials are omitted, KILLJOY automatically activates **Zero-Config Sandbox Mode**:
- **Simulated Market Feeds**: Synthetic 20-bar daily candlesticks and live snapshots for major underlyings (`SPY`, `NVDA`, `AAPL`, `MSFT`, `TSLA`, `AMD`, `QQQ`, `AMZN`).
- **Realistic Options Chains**: Generates OCC-formatted options chains across 14, 30, and 45 DTE with accurate strikes, bid-ask spreads, and Black-Scholes Greeks.
- **Dry-Run Paper Cycles**: Run full 9-stage pipeline simulations with zero risk and zero external network calls.

```bash
# Run analysis on NVDA without any API keys
python main.py --symbol NVDA --analyze

# Propose a Cash-Secured Put on SPY without any API keys
python main.py --symbol SPY --strategy cash_secured_put --propose
```

---

## Agensi.io & Agent Skill Integration

KILLJOY is packaged as a ready-to-sell, drop-in **Agent Skill** for [Agensi.io](https://www.agensi.io), Claude Code, Cursor, Codex, and other agentic runners.

Skill specification file: [`skills/killjoy/SKILL.md`](skills/killjoy/SKILL.md) (and [`.agents/skills/killjoy/SKILL.md`](.agents/skills/killjoy/SKILL.md)).

### Running Inside Claude Code, Cursor, or Codex

Agents can invoke KILLJOY commands directly through terminal tools:

```bash
# 1. Inspect market regime for an underlying
python main.py --symbol NVDA --analyze

# 2. Generate a proposed options structure
python main.py --symbol SPY --strategy cash_secured_put --propose

# 3. Put a user or agent trade through the Kill Gauntlet
python main.py --symbol TSLA --strategy long_call --kill-test

# 4. View total capital saved by rejected trades
python main.py --capital-saved
```

### Marketplace Listing & Revenue Model

KILLJOY is optimized for monetization on the Agensi.io marketplace:
- **Zero-Setup Barrier**: Runs on sandbox data out of the box; connects to user Alpaca keys for live paper trading.
- **Value Demonstration**: The `--capital-saved` command quantifies the exact dollar value preserved by rejecting flawed trades.
- See [`AGENSI.md`](AGENSI.md) for full pricing strategy, listing copy, and publisher documentation.

---

## Command Line Interface (CLI)

KILLJOY features an on-demand CLI for granular scrutiny of single underlyings and strategies:

### 1. Market Analysis (`--analyze`)
Analyzes market regime, momentum, ATR, and volatility rank.
```bash
python main.py --symbol NVDA --analyze
```
```text
=== Market Analysis: NVDA ===
Price:            $128.50
Regime:           STRONG_UPTREND
Momentum:         0.0420
RSI:              64.2
ATR:              $3.85
IV Rank:          0.42 (42.0%)
Thesis:           Strong upward momentum with healthy RSI headroom
```

### 2. Strategy Proposal (`--propose`)
Synthesizes market conditions and produces an options contract proposal.
```bash
python main.py --symbol SPY --strategy cash_secured_put --propose
```
```text
=== Trade Proposal: SPY ===
Strategy:         CASH_SECURED_PUT
Action:           SELL TO OPEN 1x SPY 30DTE 570.00 Put
Max Profit:       $480.00
Max Loss:         $56,520.00
Reward/Risk:      0.085
Confidence:       0.75
Reasoning:        High probability premium harvest in mild bullish regime
```

### 3. Adversarial Kill-Test (`--kill-test`)
Sends any proposed trade through the Kill Agent's 6 adversarial filters.
```bash
python main.py --symbol TSLA --strategy long_call --kill-test
```
```text
=== Adversarial Kill Test: TSLA ===
Score:            0.20 (KILL)
Verdict:          REJECTED - Excessive IV crush risk and deteriorating volume
Kill Objections:
  - IV Rank exceeds 70th percentile (IV crush post-earnings imminent)
  - Bid-ask spread ($0.35) exceeds 5% of mid-price (liquidity drag)
  - Momentum divergence detected on 4-hour timeframe
```

### 4. Capital Saved Audit (`--capital-saved`)
Aggregates all trades killed by the agent and shows total capital protected.
```bash
python main.py --capital-saved
```
```text
=== Capital Saved by Killjoy ===
Total Trades Screened: 48
Trades Executed:       11
Trades Killed:         37
Kill Rate:             77.1%
Capital Protected:     $24,650.00
Simulated P&L of Kills: -$4,120.00 (Losses Avoided)
```

### 5. Single Decision Cycle (`--paper-cycle`)
Executes an end-to-end dry-run across default watchlist symbols (`SPY`, `NVDA`, `AAPL`).
```bash
python main.py --paper-cycle
```

---

## Supported Options Strategies

KILLJOY implements 6 options strategies mapped dynamically to market regime:

| Strategy | Ideal Market Regime | DTE Target | Target Delta ($\Delta$) | R/R Target |
| :--- | :--- | :--- | :--- | :--- |
| **Long Call** | Strong Uptrend | 14–30 Days | 0.50–0.65 | $\ge 2.0$ |
| **Long Put** | Strong Downtrend | 14–30 Days | -0.50 to -0.65 | $\ge 2.0$ |
| **Bull Call Spread** | Mild Uptrend | 21–45 Days | Long 0.55 / Short 0.30 | $\ge 1.5$ |
| **Bear Put Spread** | Mild Downtrend | 21–45 Days | Long -0.55 / Short -0.30 | $\ge 1.5$ |
| **Iron Condor** | Range-Bound / Low Vol | 30–45 Days | Wings $\pm 0.15$ to $\pm 0.20$ | $\ge 0.33$ |
| **Cash-Secured Put** | Mild Bullish / Neutral | 21–45 Days | -0.20 to -0.30 (The Wheel) | Premium Harvest |

---

## Deterministic 8-Gate Risk Engine

The Risk Engine is mathematically deterministic. Even if an LLM is hallucinating or bullishly biased, the trade **cannot pass** if any of these 8 gates fail:

| # | Gate | Threshold | Description |
| :---: | :--- | :--- | :--- |
| **1** | **Max Risk Per Trade** | $\le \$1,000$ | Hard cap on worst-case single-position loss |
| **2** | **Daily Loss Circuit Breaker**| $\ge -\$800$ | Freezes trading for the remainder of the trading day |
| **3** | **Minimum Reward-to-Risk** | $\ge 1.5\times$ | Enforces positive statistical expectancy |
| **4** | **Minimum Confidence** | $\ge 0.25$ | Rejects low-conviction signals |
| **5** | **Implied Volatility Rank** | $\le 70\%$ | Prevents buying into inflated options volatility |
| **6** | **Concurrent Positions** | $\le 10$ | Controls operational overhead and spread risk |
| **7** | **Minimum Buying Power** | $\ge \$500$ | Preserves cash reserves for slippage and maintenance |
| **8** | **Total Options Exposure** | $\le \$10,000$ | Portfolio-level risk cap across all active legs |

### Position Sizing Formula
Contracts are strictly sized to the minimum of:
1. $5\%$ of available buying power divided by contract premium.
2. $\$1,000$ max loss divided by max loss per contract.
3. Hard ceiling of **5 contracts** per trade.

---

## The Adversarial Kill Agent

The Kill Agent is KILLJOY’s signature adversarial defense. Rather than confirming the trader's thesis, it acts as the devil's advocate.

### Kill Score Matrix

| Kill Score | Rating | Action Taken |
| :--- | :--- | :--- |
| `0.00 – 0.20` | **KILL** | Fatal flaw detected. Trade permanently rejected. |
| `0.20 – 0.40` | **WEAK** | Significant structural risk. Rejected. |
| `0.40 – 0.60` | **MARGINAL** | Cautionary concerns. Scaled back or vetoed by gates. |
| `0.60 – 0.80` | **DECENT** | Minor friction. Permitted if risk gates pass. |
| `0.80 – 1.00` | **STRONG** | High probability setup with clean market mechanics. |

---

## Autonomous Execution & Safeguards

When running in autonomous mode (`python main.py --autonomous` or via cron trigger):

- **Market Hours Gating**: Cycles execute strictly during NYSE regular trading hours (Mon–Fri, 9:30 AM – 4:00 PM ET).
- **Opening Bell Buffer**: Skips the first 15 minutes of trading (9:30–9:45 AM ET) to avoid wide bid-ask spreads and false morning breakouts.
- **Concurrency Locks**: Process-level lockfile prevents overlapping executions if a cycle takes longer than expected.
- **End-of-Day (EOD) Protocol** (3:55 PM – 4:00 PM ET):
  - If portfolio is net profitable $\to$ closes all open positions to secure gains.
  - If portfolio is net negative $\to$ harvests profitable legs and protects underwater positions.
- **Position Monitor**:
  - Automatic Take-Profit at **+50%**.
  - Automatic Stop-Loss at **-20%**.
  - Trailing Stop at **-10% from peak**.
  - Time-based expiration at **45 days**.

---

## Institutional Trading Terminal

KILLJOY includes a Next.js 15 command center designed for professional quantitative trading:

- **Obsidian / Zinc Dark Theme**: Monospace typography (`tabular-nums`), high-contrast state badges, and glassmorphic telemetry cards.
- **Live NYSE ET Clock & Countdown**: Real-time synchronization showing current market state and countdown to open/close.
- **Interactive 9-Stage Pipeline Visualizer**: Step through each phase from data ingestion to execution.
- **Real-Time 8-Gate Risk Telemetry**: Visual indicator pills showing pass/warn/fail status for every risk gate.
- **Counterfactual Loss Prevention Board**: Real-time dollar tracking of losses prevented by the Kill Agent.

To launch the web interface:
```bash
# Terminal 1: Backend API
python -m uvicorn backend.main:app --port 8000

# Terminal 2: Next.js Frontend
npm run dev
# Open http://localhost:3000
```

---

## Capital Saved & Audit Analytics

Every action taken by KILLJOY produces an immutable audit record:

1. **Decision Receipts** (`/api/receipts`): Detailed logs recording which agents voted, disagreement metrics, and execution metadata.
2. **"Why Not Trade?" Log** (`/api/rejections`): Captures every rejection reason for continuous postmortem analysis.
3. **Counterfactual Portfolio** (`/api/counterfactual`): Simulates what would have happened if rejected trades had been entered, proving kill accuracy.
4. **Strategy Graveyard** (`/api/graveyard`): Tracks decay in strategy performance and retires failing strategies.

---

## API Reference

The FastAPI backend exposes the following endpoints (with loopback protection and authentication):

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Health check & mode status | No |
| `GET` | `/api/check` | Alpaca paper connectivity check | No |
| `GET` | `/api/account` | Account equity and buying power | No |
| `GET` | `/api/positions` | Live paper positions and unrealized P&L | No |
| `GET` | `/api/analyze` | Deterministic market analysis for watchlist | No |
| `GET` | `/api/paper-cycle` | Dry-run decision cycle (no orders submitted) | No |
| `POST`| `/api/live-cycle` | Execute cycle with paper order submission | Yes (Secret / Loopback) |
| `GET` | `/api/rejections` | Rejection log and kill analytics | No |
| `GET` | `/api/counterfactual` | Counterfactual portfolio performance | No |
| `GET` | `/api/precision` | Kill precision score | No |
| `GET` | `/api/receipts` | Cryptographic trade decision receipts | No |
| `GET` | `/api/graveyard` | Strategy graveyard lifecycle statistics | No |
| `GET` | `/api/cron/run` | Cron trigger endpoint (checks market hours) | Yes (Cron Secret) |

---

## Project Architecture

```
killjoy/
├── killjoy/
│   ├── agent/                 # AI & Deterministic Agents
│   │   ├── analyst.py         # Technical & regime analysis
│   │   ├── strategy_agent.py  # Strategy selection
│   │   ├── kill_agent.py      # Adversarial challenge agent
│   │   ├── llm_analyst.py     # Optional LLM reasoning layer
│   │   ├── llm_strategy.py    # Optional LLM strategy layer
│   │   ├── llm_kill.py        # Optional LLM adversarial debate
│   │   └── models.py          # Pydantic data schemas
│   ├── alpaca/                # Broker & Market Data Integration
│   │   ├── client.py          # Paper-only Alpaca client
│   │   ├── market_data.py     # Stock bars & Sandbox data generator
│   │   ├── options_data.py    # Option chains & Sandbox OCC generator
│   │   └── trading.py         # Paper order execution
│   ├── risk/                  # Deterministic Risk Engine
│   │   └── engine.py          # 8 hard risk gates
│   ├── strategies/            # Options Strategy Definitions
│   │   ├── base.py            # Base strategy interface
│   │   ├── long_call.py       # Long Call
│   │   ├── long_put.py        # Long Put
│   │   ├── bull_call_spread.py# Bull Call Spread
│   │   ├── bear_put_spread.py # Bear Put Spread
│   │   ├── iron_condor.py     # Iron Condor
│   │   └── cash_secured_put.py# Cash-Secured Put (The Wheel)
│   ├── monitoring/            # Active Position Monitoring
│   │   └── position_monitor.py# TP/SL, Trailing stops, Expiry
│   ├── analytics/             # Audit & Postmortem Systems
│   │   ├── counterfactual.py  # Rejected trade simulator
│   │   ├── receipts.py        # Decision receipts generator
│   │   └── graveyard.py       # Strategy lifecycle manager
│   └── autonomy/              # Autonomous Scheduler
│       └── scheduler.py       # Market hours & EOD liquidation loop
├── app/                       # Next.js 15 Terminal Frontend
├── backend/                   # FastAPI Backend Server
├── skills/                    # Standalone Agent Skill for Agensi.io
├── tests/                     # Pytest Suite (113 tests)
├── main.py                    # Unified CLI Entry Point
└── package.json               # Node.js dependencies
```

---

## Quick Start

### 1. Prerequisites
- Python 3.11 or higher
- Node.js 18+ (for web terminal)

### 2. Clone and Setup Environment
```bash
git clone https://github.com/rawrkey/killjoy.git
cd killjoy

# Python environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -e ".[dev,api]"
```

### 3. Immediate Sandbox Evaluation (No Keys Required)
```bash
# Verify system and run zero-config sandbox tests
pytest tests/ -q
python main.py --symbol NVDA --analyze
python main.py --symbol SPY --strategy cash_secured_put --propose
```

### 4. Connect Alpaca Paper Trading (Optional)
Copy `.env.example` to `.env` and enter your paper trading keys:
```env
ALPACA_API_KEY=your_alpaca_paper_key
ALPACA_SECRET_KEY=your_alpaca_paper_secret
ALPACA_PAPER=true

# Optional Groq/OpenAI key for natural language thesis debate
KILLJOY_LLM_API_KEY=your_llm_api_key
KILLJOY_LLM_MODEL=qwen/qwen3.8-27b
```

### 5. Launch Full Stack Terminal
```bash
# Start backend
python -m uvicorn backend.main:app --reload --port 8000

# In another terminal, start frontend
npm install
npm run dev
```

---

## Testing & Verification

KILLJOY maintains a comprehensive test suite across every component:

```bash
# Run complete test suite (113 passing tests)
pytest tests/ -v
```

```text
tests/test_alpaca_client.py ........               [ 7%]
tests/test_models.py ..............                [19%]
tests/test_options.py .............                [30%]
tests/test_strategies.py .................         [46%]
tests/test_kill_agent.py ........                  [53%]
tests/test_risk_engine.py .........                [61%]
tests/test_portfolio.py ......                     [66%]
tests/test_position_sizing.py ....                 [70%]
tests/test_monitoring.py .......                   [76%]
tests/test_analytics.py .........                  [84%]
tests/test_agensi_features.py ....                 [88%]
tests/test_comprehensive.py .............          [100%]

======================== 113 passed in 1.17s =========================
```

Frontend production build verification:
```bash
npm run build
```

---

## Security & Paper-Only Guarantee

KILLJOY is engineered from the ground up for strict capital safety:

1. **Enforced Paper Trading**: The codebase unconditionally validates `ALPACA_PAPER=true`. If live trading keys or endpoints are configured, initialization halts immediately with an exception.
2. **Loopback Protection**: Mutating endpoints (`/api/live-cycle`, `/api/autonomous/toggle`) strictly restrict execution to loopback interfaces (`127.0.0.1`, `::1`) unless an explicit `KILLJOY_CONTROL_SECRET` is set.
3. **No Key Leakage**: API secrets are never printed to terminal logs, serialised into receipts, or committed to Git.
4. **Deterministic Veto**: No model prompt can instruct the system to ignore risk limits, daily loss boundaries, or position sizing caps.

---

## License & Disclaimer

KILLJOY is distributed for educational, research, and paper-trading evaluation purposes only.

> **Disclaimer**: Options trading involves substantial risk of loss and is not suitable for all investors. Past performance of simulated or paper trades does not guarantee future results. KILLJOY is strictly a software automation framework; users are solely responsible for their own trading decisions and risk management.
