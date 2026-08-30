# KILLJOY — Monday Runbook

**Date:** Monday, August 31, 2026  
**Market Hours:** 9:30 AM – 4:00 PM ET  
**Mode:** Paper Trading (development account first)

---

## Pre-Market Checklist (9:00 – 9:30 AM ET)

### 1. Environment Verification

```bash
# Verify Alpaca connectivity
python main.py --check

# Expected output:
# KILLJOY — Connectivity Check
# Alpaca: CONNECTED
# Paper Trading: TRUE
# Account Status: ACTIVE
# Buying Power: $XXX,XXX
# Portfolio Value: $XXX,XXX
# Open Positions: X
```

### 2. Test Suite

```bash
python -m pytest tests/ -v

# Expected: 109 passed, 2 warnings
```

### 3. Dry Run (No Orders Submitted)

```bash
python main.py --paper-cycle

# Expected output shows full pipeline:
# KILLJOY — Paper Decision Cycle (DRY RUN)
# LLM: ACTIVE (or DETERMINISTIC)
# ============================================================
# ANALYST SPY: sideways (conf: 0.50) [LLM/DETERMINISTIC]
# Processing SPY bull_call_spread (R/R: 1.8, conf: 0.51)
# KILL SPY bull_call_spread: score=0.62 survives=True ...
# PORTFOLIO PASS / RISK PASS
# DRY RUN: Would execute SPY bull_call_spread
```

### 4. Verify LLM Path (if configured)

```bash
# Check LLM status in output
python main.py --analyze

# Expected: "LLM: ACTIVE" (not "DETERMINISTIC")
```

---

## Market Open (9:30 AM ET)

### 5. Enable Paper Execution

Edit `main.py` or use the autonomous mode:

```bash
# Run autonomous loop with 30-second scan interval
python main.py --autonomous --interval 30
```

**OR** use the API-triggered cycle:

```bash
# Single cycle with live execution
python main.py --paper-cycle
```

### 6. Verify Execution Path

Watch for these log entries:

```
ORDER SUBMITTED: SPY — <order_id>
```

### 7. Verify Position Exists

```bash
python main.py --positions

# Expected:
# Open Positions (1):
# ------------------------------------------------------------
#   SPY250919C00555000: long 1 @ $5.25 → $5.50 (P&L: $25.00)
```

---

## Position Monitoring

### 8. Monitor via Dashboard

Open the web GUI and verify:
- ✅ Connection status shows CONNECTED
- ✅ Account overview shows buying power and portfolio value
- ✅ Open positions table shows the new position
- ✅ Recent activity shows order_submitted event
- ✅ Pipeline visualization shows all stages

### 9. Monitor via CLI

```bash
python main.py --status
python main.py --positions
```

---

## Position Exit

### 10. Exit Conditions

The position monitor will evaluate:
- **HOLD**: P&L positive, days held < max, no stop-loss triggered
- **EXIT**: P&L < -20% of max loss, or days held > 45

### 11. Manual Exit (if needed)

```python
from killjoy.execution.executor import Executor
from killjoy.alpaca.trading import AlpacaTradingClient
from killjoy.config import get_settings

settings = get_settings()
client = AlpacaTradingClient.from_settings(settings)
executor = Executor(client._trading_client)
result = executor.close_position("SPY250919C00555000")
print(result)
```

---

## Post-Trade

### 12. Verify Realized P&L

```bash
python main.py --positions
# Position should be gone

# Check journal
# API: GET /api/journal
```

### 13. Postmortem

The postmortem agent will analyze:
- Entry thesis vs actual outcome
- Kill score accuracy
- Timing and exit quality
- Lessons for future trades

---

## Verification Checklist

After the first complete cycle (proposal → fill → monitoring → exit → P&L):

- [ ] Order submitted (log shows `order_submitted`)
- [ ] Order filled (Alpaca shows position)
- [ ] Position exists (`python main.py --positions`)
- [ ] Position monitored (dashboard shows position)
- [ ] Position closed (exit triggered or manual)
- [ ] Realized P&L recorded (journal entry)
- [ ] Postmortem generated (analytics)

---

## Troubleshooting

### No Orders Submitted

1. Check market hours (9:30 AM – 4:00 PM ET)
2. Check `python main.py --check` shows CONNECTED
3. Check LLM status: "LLM: ACTIVE" or "DETERMINISTIC"
4. Check risk engine logs for rejections

### Kill Agent Kills Everything

1. Check market regime (sideways = fewer trades)
2. Lower confidence threshold temporarily
3. Review kill agent objections in event log

### Dashboard Shows OFFLINE

1. Verify API server is running
2. Check Alpaca credentials in `.env`
3. Verify `GET /api/health` returns `{"status": "ok"}`

---

## Safety Reminders

1. **Use development paper account first** — Keep judging account clean
2. **Never force a trade** — If market is closed, just validate
3. **Watch the first fill** — Verify the full chain works before scaling
4. **Log everything** — Event log provides audit trail
