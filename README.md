<div align="center">

# KILLJOY

### Autonomous options intelligence. Deterministic risk. Paper-only execution.

<p>
  <img src="https://img.shields.io/badge/mode-PAPER%20ONLY-20c997?style=for-the-badge" alt="Paper only">
  <img src="https://img.shields.io/badge/python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/tests-7%20passing-22c55e?style=for-the-badge" alt="7 tests passing">
</p>

<p><em>A safety-first technical foundation for an autonomous AI options trading agent, built for the Alpaca hackathon.</em></p>

</div>

---

## The idea

KILLJOY is being built to find options opportunities—and then aggressively try to reject them before capital is put at risk. Its future agent pipeline will generate a thesis, propose a structure, attack the proposal, check portfolio fit, enforce deterministic limits, and only then allow paper execution.

> **Current release:** Phase 1 foundation. It safely connects to a configured Alpaca paper account for read-only account and position status. It does not submit orders, use MCP, or contain AI trading logic yet.

## Design principles

| Principle | What it means in KILLJOY |
| --- | --- |
| 🛡️ Paper first | Live mode is rejected by configuration. |
| 🧠 AI advises, code decides | Future LLM output cannot directly create an order. |
| 🧱 Clear boundaries | Alpaca, strategies, risk, execution, and future agents stay separated. |
| 🔎 Observable by default | Typed data, structured errors, tests, and a persistent handover keep the system inspectable. |

## Architecture

```text
                    ┌─────────────────────────────┐
                    │  Future agent / MCP tool layer│
                    │  thesis · strategy · kill test│
                    └──────────────┬──────────────┘
                                   │ structured proposals only
                                   ▼
┌─────────────┐           ┌──────────────────┐           ┌──────────────┐
│ Alpaca APIs │ ◄──────── │ KILLJOY adapters │ ────────► │ Status CLI   │
│ paper only  │           └──────────────────┘           └──────────────┘
└─────────────┘                    │
                                   ▼
                    ┌─────────────────────────────┐
                    │ Future deterministic controls │
                    │ portfolio · risk · execution  │
                    └─────────────────────────────┘
```

| Package | Responsibility | Status |
| --- | --- | --- |
| `killjoy.config` | Environment settings and paper-only guard | ✅ Implemented |
| `killjoy.alpaca` | Isolated, read-only Alpaca paper adapter | ✅ Implemented |
| `killjoy.agent` | Provider-neutral domain models | 🟡 Initial models |
| `killjoy.strategies` | Options proposal generation | ⏳ Planned |
| `killjoy.risk` | Deterministic risk decisions | ⏳ Planned |
| `killjoy.execution` | Approved paper-order orchestration | ⏳ Planned |
| `killjoy.database` | Trade journal and persistence | ⏳ Planned |

## Quick start

**Prerequisite:** Python 3.11 or later.

```powershell
git clone https://github.com/rawrkey/killjoy.git
cd killjoy
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Open the untracked `.env` file and use **Alpaca paper-trading** credentials only:

```dotenv
ALPACA_API_KEY=
ALPACA_SECRET_KEY=
ALPACA_PAPER=true
```

Run the safe account-status check:

```powershell
.\.venv\Scripts\python.exe main.py
```

Without credentials, this exits cleanly and prints:

```text
KILLJOY
Alpaca: NOT CONFIGURED
Paper Trading: TRUE
```

With valid paper credentials, it reads and displays account status, buying power, portfolio value, and open-position count. It never places an order.

## Development

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Current suite: **7 passing tests** covering configuration guards, missing credentials, read-only client behavior, response normalization, and status formatting.

## Safety contract

- `ALPACA_PAPER=false` is rejected.
- `.env` and virtual environments are ignored by Git.
- Credentials use secret-aware configuration and are never intentionally logged.
- The current Alpaca wrapper exposes read operations only: account, positions, orders, and portfolio history.
- No automatic order submission exists in this release.

## Alpaca MCP

MCP is **not integrated yet**. When verified and added, it will sit at the future agent-tool layer for contextual data/actions. Deterministic risk and execution gates will remain inside KILLJOY and retain final control.

## Roadmap

- [x] Safe Python project foundation
- [x] Paper-only configuration and Alpaca read adapter
- [x] Read-only paper-account status command
- [ ] Verify and configure Alpaca MCP capabilities
- [ ] Options contracts, market data, and strategy proposals
- [ ] Market Analyst, Strategy Agent, and adversarial Kill Agent
- [ ] Portfolio controls, deterministic risk engine, and paper execution
- [ ] Monitoring, trade journal, postmortems, and scheduled autonomy

## Project continuity

[`handover.md`](handover.md) is the source of truth for current implementation state, technical decisions, commands, tests, known issues, and the recommended next task.

---

<div align="center">
  <strong>Build conviction. Then try to kill it.</strong><br>
  <sub>KILLJOY · Alpaca Hackathon · Paper trading only</sub>
</div>
