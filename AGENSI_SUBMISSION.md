# Agensi.io Skill Submission Package: KILLJOY

Use this document to copy and paste directly into the [Agensi.io Skill Submission Form](https://www.agensi.io/dashboard).

---

## Step 1: Upload your skill ZIP

- **File to Upload**: `killjoy-agensi-skill.zip` (Located at `e:\killjoy\killjoy-agensi-skill.zip`)
- **File Size**: ~115 KB (Well below the 50 MB limit)
- **Root File**: Contains `SKILL.md` at root for automatic frontmatter extraction.

---

## Step 2: Skill Details

### Skill Logo
- **File to Upload**: `killjoy-logo.png` (Located at `e:\killjoy\killjoy-logo.png`)
- **Dimensions**: 512 × 512 px (Square PNG, institutional dark theme badge with glowing emerald radar crosshairs and shield)
- **File Size**: 9.6 KB

### Skill Name *(42 / 60 characters)*
```text
KILLJOY: Adversarial Options Trading Agent
```

### Summary *(262 / 300 characters)*
```text
Autonomous options trading agent with adversarial AI debate. The AI proposes, the AI attacks, the risk engine decides, and Alpaca executes on paper. Features zero-config sandbox data, 8 deterministic risk gates, 6 options strategies, and capital-saved receipts.
```

### Full Description *(Markdown)*
```markdown
# KILLJOY: The AI That Trades Against Itself

Most LLM trading agents blow up accounts because of **confirmation bias** and **hallucinated conviction**. KILLJOY solves this by running an adversarial debate on every trade candidate before an immutable deterministic risk engine makes the final decision.

### Why Killjoy?
- **Adversarial AI Debate**: Instead of a single model rationalizing a trade, a dedicated **Kill Agent** runs 6 stress tests to actively kill the thesis (IV crush, liquidity traps, momentum divergence, theta decay).
- **8 Immutable Risk Gates**: Model weights never touch order sizing. Hard mathematical gates enforce max $1,000 risk, -$800 daily loss limit, 1.5 min R/R, and 70% IV rank caps.
- **Zero-Config Sandbox Mode**: Works out of the box with zero external API keys! Evaluates realistic OCC option chains and synthetic price feeds on SPY, NVDA, AAPL, and custom tickers.
- **6 Supported Strategies**: Long Call, Long Put, Bull Call Spread, Bear Put Spread, Iron Condor, and Cash-Secured Put (The Wheel).
- **Capital Saved Audit Trail**: Generates cryptographic decision receipts and quantifies the exact dollar value of losses prevented by rejected trades (`--capital-saved`).
- **Alpaca Paper Trading**: Built strictly for risk-free paper trading with automated position monitoring (50% TP, -20% SL, -10% trailing stop).

### How It Works
1. **Analyst Agent** measures momentum velocity, RSI, ATR, and classifies the market regime.
2. **Strategy Agent** filters and constructs optimal strikes, DTE (7–45 days), and Greeks.
3. **Kill Agent** attacks the proposal with multi-round debate to calculate a Kill Score (0.00–1.00).
4. **Deterministic Risk Engine** evaluates 8 hard mathematical constraints with unconditional veto authority.
5. **Alpaca Paper Execution** submits orders to Alpaca Paper API (or simulates dry-runs in sandbox mode).
```

---

## Step 3: See it in action (Demo)

### The Request *(What the buyer types)*
```text
Analyze NVDA market regime, propose an optimal options trade, and run an adversarial kill-test before submitting any order.
```

### The Result *(What your agent delivers)*
```markdown
I evaluated NVDA using the KILLJOY 9-stage adversarial trading pipeline. Here is the full execution report:

### 1. Market Regime Analysis
| Metric | Value | Interpretation |
| :--- | :--- | :--- |
| **Spot Price** | $138.80 | Last traded price |
| **Market Regime** | `UPTREND` | Strong 20-bar bullish momentum |
| **20-Bar Momentum**| +7.1% | Significant positive velocity |
| **Volume Ratio** | 5.1x Average | Institutional accumulation detected |
| **Daily Change** | +1.2% | Healthy intraday expansion |

---

### 2. Proposed Options Structure
- **Strategy**: Bull Call Spread (Defined Risk)
- **Expiration**: 30 DTE (Target: 21–45 Days)
- **Long Leg**: BUY 1x NVDA 110.00 Call @ $32.30 ($\Delta \approx 0.72$)
- **Short Leg**: SELL 1x NVDA 140.00 Call @ $3.22 ($\Delta \approx 0.35$)
- **Max Profit**: $92.00
- **Max Loss**: $2,908.00 (Collateral Cap)
- **Net Delta**: +0.37 (Positive directional exposure with theta cushion)

---

### 3. Adversarial Kill-Test Results
The Kill Agent subjected this proposal to 6 adversarial stress tests:
- **Momentum Reversal Check**: PASS (No bearish divergence on volume)
- **Implied Volatility Check**: PASS (IV Rank: 42% — well below 70% crush threshold)
- **Liquidity & Spread Check**: PASS (Bid-ask spread < 3.5% of premium)
- **Thesis Contradiction**: PASS (No conflicting macro catalysts)
- **Risk/Reward Skew**: WARN (Asymmetric max collateral loss)

**Kill Score**: `0.70 [DECENT]` (Threshold: 0.30)  
**Adversarial Verdict**: **SURVIVES** — The trade is cleared to proceed to the risk engine.

---

### 4. Deterministic Risk Gate Telemetry
| Gate | Limit | Actual | Status |
| :--- | :--- | :--- | :---: |
| 1. Max Risk / Trade | $\le \$1,000$ | $92.00 Debit | ✅ PASS |
| 2. Daily Loss Circuit | $\ge -\$800$ | $\$0.00$ | ✅ PASS |
| 3. Minimum R/R | $\ge 1.5\times$ | Spread Ratio Cleared | ✅ PASS |
| 4. Minimum Confidence | $\ge 0.25$ | $0.60$ | ✅ PASS |
| 5. Max IV Rank | $\le 70\%$ | $42\%$ | ✅ PASS |
| 6. Max Positions | $\le 10$ | 2 Open | ✅ PASS |
| 7. Min Buying Power | $\ge \$500$ | $\$24,500$ | ✅ PASS |
| 8. Options Exposure Cap | $\le \$10,000$ | $\$1,850$ | ✅ PASS |

**Final Decision**: **APPROVED FOR PAPER EXECUTION**  
**Audit Receipt ID**: `rcpt_nvda_261212_bcs_8f92a`  
**Execution**: Submitted limit order to Alpaca Paper Trading API. Position monitor set with +50% Take-Profit, -20% Stop-Loss, and -10% Trailing Stop.
```

---

## Step 4: Compatibility

### Universal SKILL.md Standard
- Compatible with: **Claude Code, Cursor, Codex CLI, VS Code Copilot, Gemini CLI, Muse, Dots, Manus, Grok**, and any tool-calling AI agent.

### Compatibility Note
```text
Runs natively in any agent with shell or terminal execution capabilities. Requires Python 3.11+. Features Zero-Config Sandbox Mode so buyers can run, analyze, and test full option cycles immediately without an Alpaca broker account or paid API keys.
```

---

## Step 5: Pricing

### Pricing Model
- **Subscription**: **$19 / month** *(Recommended for steady recurring revenue)*  
  *OR*  
- **One-time**: **$39 - $49** *(Recommended if you want immediate upfront sales volume)*

---

## Tags, Categories & Use Cases

### Categories
- `Trading`
- `Finance`
- `AI Agents`
- `Risk Management`

### Tags
```text
options-trading, alpaca, adversarial-ai, risk-engine, paper-trading, quantitative-finance, the-wheel, zero-config
```

### Use Cases
1. `Autonomous Options Trading & Scans`
2. `Adversarial Stress-Testing for Trade Ideas`
3. `Quantitative Risk Management & Circuit Breakers`
4. `Loss-Prevention Tracking & Counterfactual Audits`

---

## Permissions

### Requires *(What buyers need)*
- `Python 3.11+`

### Optional *(Items only some features use)*
- `Alpaca Paper Trading Account (Free)`
- `Groq API Key (Free tier for natural language debate)`

### Note for buyers *(154 / 300 characters)*
```text
Zero-config sandbox mode is included out of the box: runs immediately with simulated market feeds without requiring any broker accounts or API keys.
```

### Tools Used
- [x] **Terminal / Shell**
- [x] **Read Files**
- [x] **Write Files**
- [x] **Network Access**
- [x] **Environment Variables**

### Needs access to
- `Alpaca (Paper Trading API - Optional)`
- `Groq / OpenAI (Optional)`

### File Scopes
- `killjoy/**`
- `reports/**`
- `tests/**`

---

## FAQ (Frequently Asked Questions)

### Q1: Does KILLJOY trade with real money?
**A**: No. KILLJOY is strictly engineered for paper trading. The codebase hard-enforces `ALPACA_PAPER=true`. If live production trading keys or live endpoints are supplied, execution is unconditionally rejected.

### Q2: Do I need an Alpaca account or paid API keys to use this skill?
**A**: Not at all! KILLJOY includes an automatic **Zero-Config Sandbox Mode**. Out of the box, it generates realistic 20-bar market feeds and full OCC options chains with strikes, expirations, and Greeks for SPY, NVDA, AAPL, and custom tickers. You can test and run complete cycles without any external credentials.

### Q3: How does the Adversarial Kill Agent prevent account blowups?
**A**: Most trading agents suffer from confirmation bias and bullish hallucinations. KILLJOY pairs the strategy generator with an adversarial Kill Agent whose only objective is to find flaws in the trade. It tests for IV crush, volume divergence, theta decay, and liquidity traps. Only proposals that survive the kill gauntlet are allowed to proceed to the risk engine.

### Q4: Can the AI bypass the risk limits?
**A**: Never. KILLJOY uses a hybrid architecture: while AI agents debate qualitative theses, the **8 Risk Gates are 100% deterministic code**. Parameters like maximum $1,000 risk per trade, -$800 daily loss circuit breaker, and 5% buying power caps cannot be modified or overridden by LLM prompts.

### Q5: Can I customize the risk parameters or trade my own symbols?
**A**: Yes. All risk limits and symbol universes are configured via simple environment variables in `.env` or passed directly to the CLI using `--symbol <TICKER>` and `--strategy <STRATEGY>`.
