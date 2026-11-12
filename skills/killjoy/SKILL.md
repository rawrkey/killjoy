---
name: killjoy
description: >-
  Autonomous options trading agent with adversarial AI debate. The AI proposes,
  the AI attacks, the risk engine decides, and Alpaca executes on paper.
  Use when the user wants to scan market regimes, evaluate options spreads (calls, puts, vertical spreads, iron condors, cash-secured puts),
  run adversarial kill-tests on trade proposals, simulate counterfactual outcomes, or execute paper options trades.
parameters:
  type: object
  properties:
    action:
      type: string
      enum:
        - status
        - analyze
        - propose
        - kill-test
        - capital-saved
        - paper-cycle
        - live-cycle
        - positions
      description: The trading action or pipeline stage to execute.
    symbol:
      type: string
      description: Underlying stock ticker (e.g. SPY, QQQ, AAPL, NVDA, TSLA, AMD, MSFT).
    strategy:
      type: string
      enum:
        - long_call
        - long_put
        - bull_call_spread
        - bear_put_spread
        - iron_condor
        - cash_secured_put
      description: Options strategy to evaluate.
---

# KILLJOY: The AI That Trades Against Itself

> **Autonomous AI Options Trading Agent with Adversarial AI Debate & Deterministic Risk Gates**

KILLJOY stops autonomous trading agents from greedily blowing up accounts. Instead of an unconstrained LLM executing trades, KILLJOY forces every trade proposal to survive a multi-round debate with a dedicated **Kill Agent** whose sole purpose is to destroy the thesis. If a trade survives adversarial testing, it must still pass through **8 immutable deterministic risk gates** before any order is submitted.

---

## Zero-Config Sandbox Mode

KILLJOY works out of the box with **zero required API keys**. When running without Alpaca or Groq credentials:
- **Market Data**: Runs in Sandbox Mode with realistic pricing feeds for `SPY`, `QQQ`, `AAPL`, `NVDA`, `TSLA`, `MSFT`, `AMZN`, `GOOGL`, `META`, `AMD` (or dynamic feeds for any custom ticker).
- **Options Chains**: Synthesizes fully compliant OCC options chains with strikes, expirations, and Greeks ($\Delta, \Gamma, \Theta, \text{Vega}$).
- **Adversarial Engine**: Runs complete 9-stage decision cycles and records counterfactuals.
- When live credentials are added to `.env`, KILLJOY automatically switches to live Alpaca Paper trading feeds!

---

## When to Use This Skill

Activate KILLJOY when:
- The user asks to analyze options chains, Greeks, or market volatility for tickers like `SPY`, `QQQ`, `AAPL`, `NVDA`, `TSLA`, `AMD`.
- The user wants a structured, defined-risk options trade proposal (Long Call, Long Put, Bull Call Spread, Bear Put Spread, Iron Condor, Cash-Secured Put).
- The user wants to stress-test or poke holes in a trading thesis using adversarial AI debate (`kill-test`).
- The user wants to run an autonomous paper trading decision cycle (`paper-cycle`).
- The user wants to verify risk limits, counterfactual performance of rejected trades, or capital preservation receipts (`capital-saved`).

---

## 9-Stage Decision Pipeline

```
1. Market Ingestion ──> 2. Analyst Agent (Regime/Momentum) ──> 3. Strategy Agent
                              │
                              ▼
5. Kill Agent (Adversarial) <── 4. Structured Trade Proposal (Legs, Greeks, R/R)
      │
      ▼
6. Adversarial Debate (Trader vs Kill Agent) ──> 7. Portfolio Fit Check
                                                       │
                                                       ▼
9. Alpaca Execution (Paper Only) <── 8. Deterministic Risk Engine (8 Gates)
```

---

## Available Commands & Actions

### 1. Market Regime Analysis (On-Demand Single Symbol or Universe)
Analyze momentum, volume ratio, 20-bar volatility, and market regime for any target symbol.
```bash
python main.py --analyze --symbol NVDA
python main.py --analyze
```
**Regimes Classified**:
- `strong_uptrend` / `uptrend` → Bullish calls or Bull Call Spreads
- `strong_downtrend` / `downtrend` → Bearish puts or Bear Put Spreads
- `sideways` / `neutral` → Iron Condors & Cash-Secured Puts
- `high_volatility` → Volatility alert (Iron Condors locked out)

### 2. Generate Options Proposals
Generate ranked, regime-filtered options candidates with exact strikes, expirations, and max profit/loss:
```bash
python main.py --propose --symbol AAPL
python main.py --propose --symbol NVDA --strategy cash_secured_put
```

### 3. Adversarial Kill Test
Attack any trade proposal with 9 adversarial checks and LLM debate to compute an objective **Kill Score (0.00 – 1.00)**:
```bash
python main.py --kill-test --symbol TSLA
python main.py --kill-test --symbol SPY --strategy iron_condor
```

### 4. Capital Preservation & Avoided Losses Report
Review exactly how much capital the Kill Agent saved your portfolio by vetoing bad trades:
```bash
python main.py --capital-saved
```

### 5. Dry-Run Decision Cycle
Executes the full 9-stage pipeline without submitting orders. Evaluates candidates, tests them against the Kill Agent, runs deterministic risk gates, and records counterfactuals:
```bash
python main.py --paper-cycle --symbol NVDA
python main.py --paper-cycle
```

### 6. Autonomous Loop
Runs continuous scans every 30 minutes during market hours (Mon-Fri 9:30 AM – 4:00 PM ET). Automatically closes positions on **Take-Profit (+50%)**, **Stop-Loss (-20%)**, **Trailing Stop (-10% from peak)**, or **Time Exit (45 days)**:
```bash
python main.py --autonomous
```

---

## Supported Options Strategies

1. **Long Call** (Strong Uptrend) — Bullish directional play.
2. **Long Put** (Strong Downtrend) — Bearish directional play.
3. **Bull Call Spread** (Mild Uptrend) — Defined-risk debit spread.
4. **Bear Put Spread** (Mild Downtrend) — Defined-risk debit spread.
5. **Iron Condor** (Sideways) — Defined-risk neutral credit spread.
6. **Cash-Secured Put (CSP / Wheel Strategy)** (Neutral to Mild Uptrend) — High probability theta income with cash collateral backing.

---

## Deterministic Risk Engine: 8 Immutable Gates

Even if the LLM approves a trade, the deterministic risk engine has **absolute veto authority**:

| Gate | Limit | Action on Violation |
| :--- | :--- | :--- |
| **Max Risk / Trade** | $\le \$1,000$ | Veto & log rejection |
| **Daily Loss Limit** | $> -\$1,000$ | Hard circuit breaker stops all trading |
| **Total Options Exposure** | $\le \$10,000$ | Blocks new derivative allocation |
| **Single Underlying Risk** | $\le \$3,000$ | Blocks concentration in one symbol |
| **Min Reward / Risk** | $\ge 1.50\times$ | Rejects negative expectancy setups |
| **Buying Power Floor** | $\ge \$500 + \text{loss}$ | Protects account solvency |
| **Max Concurrent Positions**| $\le 10$ | Prevents execution spam |
| **Max IV Rank** | $\le 70\%$ | Rejects buying premium in high IV |
