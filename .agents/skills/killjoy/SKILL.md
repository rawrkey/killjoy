---
name: killjoy
description: >-
  Autonomous options trading agent with adversarial AI debate. The AI proposes,
  the AI attacks, the risk engine decides, and Alpaca executes on paper.
  Use when the user wants to scan market regimes, evaluate options spreads (calls, puts, vertical spreads, iron condors),
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
        - debate
        - risk-check
        - paper-cycle
        - live-cycle
        - counterfactual
        - receipts
        - graveyard
      description: The trading action or pipeline stage to execute.
    symbol:
      type: string
      description: Underlying stock ticker (e.g. SPY, QQQ, AAPL, NVDA, TSLA).
    strategy:
      type: string
      enum:
        - long_call
        - long_put
        - bull_call_spread
        - bear_put_spread
        - iron_condor
      description: Options strategy to evaluate.
---

# KILLJOY: The AI That Trades Against Itself

> **Autonomous AI Options Trading Agent with Adversarial AI Debate & Deterministic Risk Gates**

KILLJOY stops autonomous trading agents from greedily blowing up accounts. Instead of an unconstrained LLM executing trades, KILLJOY forces every trade proposal to survive a multi-round debate with a dedicated **Kill Agent** whose sole purpose is to destroy the thesis. If a trade survives adversarial testing, it must still pass through **8 immutable deterministic risk gates** before any order is submitted.

---

## When to Use This Skill

Activate KILLJOY when:
- The user asks to analyze options chains, Greeks, or market volatility for tickers like `SPY`, `QQQ`, `AAPL`, `NVDA`, `TSLA`.
- The user wants a structured, defined-risk options trade proposal (Long Call, Long Put, Bull Call Spread, Bear Put Spread, Iron Condor).
- The user wants to stress-test or poke holes in a trading thesis using adversarial AI debate (`kill-test` or `debate`).
- The user wants to run an autonomous paper trading decision cycle.
- The user wants to verify risk limits, counterfactual performance of rejected trades, or decision receipts.

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

### 1. Account & Connection Status
Verify paper connectivity, account equity, buying power, and active risk limits.
```bash
python main.py --check
python main.py --status
```

### 2. Market Regime Analysis
Analyze momentum, volume ratio, 20-bar volatility, and market regime for top universe symbols.
```bash
python main.py --analyze
```
**Regimes Classified**:
- `strong_uptrend` / `uptrend` → Bullish calls or Bull Call Spreads
- `strong_downtrend` / `downtrend` → Bearish puts or Bear Put Spreads
- `sideways` / `neutral` → Iron Condors
- `high_volatility` → Volatility alerts (Iron Condors locked out)

### 3. Dry-Run Decision Cycle
Executes the full 9-stage pipeline without submitting orders. Evaluates candidates, tests them against the Kill Agent, runs deterministic risk gates, and records counterfactuals.
```bash
python main.py --paper-cycle
```

### 4. Autonomous Loop
Runs continuous scans every 30 minutes during market hours (Mon-Fri 9:30 AM – 4:00 PM ET). Automatically closes positions on **Take-Profit (+50%)**, **Stop-Loss (-20%)**, **Trailing Stop (-10% from peak)**, or **Time Exit (45 days)**.
```bash
python main.py --autonomous
```

---

## The Kill Agent: How Adversarial Debate Works

The Kill Agent actively attempts to find reasons to reject every trade:
1. **Confidence Floor**: Rejects if proposal confidence $< 0.20$.
2. **Reward-to-Risk Ratio**: Rejects if $R/R < 1.50$.
3. **Loss Ceiling**: Rejects if max loss $> \$1,000$.
4. **Thesis Contradiction**: Identifies bullish setups in downtrend regimes or vice-versa.
5. **Regime Misalignment**: Forbids selling Iron Condors into high volatility.
6. **Risk Factor Stacking**: Flags proposals with more than 2 distinct event risks.
7. **Expiration Timing**: Rejects expiration $< 7$ days (gamma risk) or $> 60$ days (stagnation).
8. **Leg Complexity**: Penalizes structures with excessive legs.
9. **Single-Ticker Concentration**: Enforces portfolio diversification.

**Kill Score Scale**:
- `0.00 - 0.20`: **KILL** — Critical flaws, immediate reject.
- `0.20 - 0.40`: **WEAK** — Significant hazards, rejected by threshold.
- `0.40 - 0.60`: **MARGINAL** — High caution, requires debate defense.
- `0.60 - 0.80`: **DECENT** — Acceptable risk.
- `0.80 - 1.00`: **STRONG** — Clean thesis, passes to risk engine.

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

---

## Agensi.io & Marketplace Integration

When running in an environment powered by Agensi.io:
1. Market quotes and options chains are automatically provided via Agensi's 4,500+ tool API keys.
2. Users do not need their own Alpaca or Market Data accounts to run simulations or receive trade theses.
3. Live paper execution connects directly to Alpaca paper trading accounts via `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`.

