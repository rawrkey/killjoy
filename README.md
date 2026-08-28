# KILLJOY

KILLJOY is a paper-trading-first technical foundation for an autonomous AI options trading agent. This repository deliberately begins with typed interfaces, deterministic controls, and safe Alpaca boundaries—not autonomous trading logic or a user interface.

## Current architecture

- `killjoy.config`: environment-backed, paper-only configuration.
- `killjoy.agent`: typed trading-domain models and future agent interfaces.
- `killjoy.strategies`: strategy interfaces.
- `killjoy.risk`: deterministic risk validation.
- `killjoy.execution`: execution orchestration separated from strategy and risk.
- `killjoy.alpaca`: the only package permitted to communicate with Alpaca.
- `killjoy.database`: future persistence models and repositories.

Alpaca MCP is not configured yet. When added, it will be an agent-facing tool layer; risk assessment and execution safeguards remain deterministic KILLJOY code.

## Setup

Requires Python 3.11 or later.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Populate `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` in your untracked `.env` only with Alpaca **paper** credentials. `ALPACA_PAPER` must remain `true`.

## Commands

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe main.py
```

The demo command will never place an order. Until credentials are configured, it should report the missing-credentials state safely. More usage details will be added with the Alpaca wrapper and demo entry point.

## Safety

- Live trading is unsupported and rejected by configuration validation.
- No API keys, secret keys, or `.env` files are committed.
- No order placement is initiated automatically.

## Planned next layers

- Typed options/trade proposal models.
- Deterministic risk evaluation.
- Paper-only Alpaca account and position adapter.
- Safe connection demo and broader tests.
- Future LLM agent, options strategy, persistence, and MCP tool integration.
