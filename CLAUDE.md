# CLAUDE.md

## Instructions for Coding Agents

### Before Every Task
1. Read `handover.md` first
2. Run `git status --short`
3. Inspect relevant files in the repository
4. Compare documented state against actual code
5. Trust the repository over stale documentation
6. Correct `handover.md` if documentation is stale

### During Work
- Do not duplicate existing implementation
- Check `killjoy/` structure before creating new files
- Follow existing code patterns and naming conventions
- Use Pydantic for all new data models
- Keep Alpaca-specific code in `killjoy/alpaca/`
- Keep deterministic logic separate from AI/LLM logic

### After Every Task
- Update `handover.md` with exact changes
- Record files created/modified
- Record test results
- Record any architecture decisions
- Record the recommended next step

### Safety Rules
- **NEVER** commit secrets or API keys
- **NEVER** enable live trading (`ALPACA_PAPER` must be `true`)
- **NEVER** bypass the deterministic risk engine
- **NEVER** allow LLM to directly submit orders
- **ALWAYS** verify against current official Alpaca documentation
- **ALWAYS** run `pytest tests/ -v` before reporting completion
- **ALWAYS** add `.env` to `.gitignore` (already configured)

### Running Tests
```bash
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

### Alpaca Integration
- SDK: `alpaca-py>=0.44,<0.45`
- Paper endpoint: `paper-api.alpaca.markets` (via `paper=True`)
- Options orders: `MarketOrderRequest` with `OrderClass.MLEG` + `OptionLegRequest`
- MCP server: `uvx alpaca-mcp-server`
- Verify all SDK methods against the installed package before implementing
- Official docs: https://docs.alpaca.markets/us/

### Key Architecture
- `killjoy/agent/` — AI agents (analyst, strategy, kill, portfolio, postmortem)
- `killjoy/alpaca/` — Alpaca SDK adapters (client, trading, market data, options data)
- `killjoy/options/` — Options engine (chain, contracts, greeks, liquidity, pricing)
- `killjoy/strategies/` — Strategy implementations (5 strategies)
- `killjoy/risk/` — Deterministic risk engine
- `killjoy/execution/` — Order execution
- `killjoy/portfolio/` — Portfolio management
- `killjoy/monitoring/` — Position monitoring
- `killjoy/database/` — Trade journal persistence
- `killjoy/autonomy/` — Autonomous scheduler
- `killjoy/config/` — Settings and logging
