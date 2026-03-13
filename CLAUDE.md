# CLAUDE.md — ETF Portfolio Intelligence System

## First Thing Every Session
1. Read `docs/MASTER_PLAN.md`
2. Read the current phase file in `docs/`
3. Check the status tracker at the bottom of MASTER_PLAN.md
4. Ask clarifying questions before writing any code

---

## What This Project Is
A self-hosted ETF portfolio rebalancer powered by a high-performance
market data ingestion engine. It ingests minute-level bid/ask data for
4 Canadian ETFs, stores it in TimescaleDB, analyzes historical spread
patterns, and tells the user exactly what to buy on payday.

**The three layers:**
- Layer 1: Data ingestion engine (performance story)
- Layer 2: Pattern analysis (spread, volatility, anomaly)
- Layer 3: React rebalancer dashboard (the product)

---

## Non-Negotiable Rules

### Process
- Ask clarifying questions BEFORE writing any code
- Write one function at a time, not entire files at once
- Never refactor code that wasn't asked to be refactored
- Never move to the next phase until the current one works
- Never exceed 250 lines per response
- When in doubt, do less and ask

### Python
- Type hints required on every function signature
- Docstring required on every function
- No function longer than 30 lines
- Explicit error handling — no silent failures or bare excepts
- No commented-out code in commits

### FastAPI
- Every endpoint must have a Pydantic response model
- No business logic inside endpoint functions
- Endpoints are thin routers only — logic lives in modules
- All endpoints must handle errors and return proper HTTP codes

### SQL
- No `SELECT *` ever
- No inline SQL strings anywhere outside database.py
- Every query gets a comment explaining what it does and why
- Use parameterized queries always — no string formatting in SQL

### React
- Components capped at ~150 lines
- No data fetching directly inside components
- All API calls go through a dedicated `src/api.js` file
- Mobile responsive by default — test on small screen first

---

## File Ownership
Each file has one job. Never put logic in the wrong layer.

| Directory | Owns |
|-----------|------|
| `ingestion/` | Fetching and scheduling only |
| `storage/` | Database connection and summarization only |
| `analysis/` | Spread, volatility, anomaly patterns only |
| `rebalancer/` | Allocation algorithm and timing only |
| `benchmark/` | Profiling and latency measurement only |
| `main.py` | Routing only — no business logic |
| `backend/config/` | Settings and constants only |

---

## Tech Stack
| Component | Choice |
|-----------|--------|
| Backend | FastAPI (Python) |
| Database | TimescaleDB (Docker) |
| Frontend | React + Vite |
| Data source | yfinance |
| Concurrency | Python asyncio |
| Scheduling | APScheduler |
| Hosting | Linux server + Docker Compose + Nginx |

---

## ETFs Being Tracked
| Ticker | Name | Target |
|--------|------|--------|
| HXQ.TO | Horizons Nasdaq 100 | 35% |
| VFV.TO | Vanguard S&P 500 | 40% |
| VCN.TO | Vanguard Canada | 15% |
| ZEM.TO | BMO Emerging Markets | 10% |

---

## Performance Targets
These are the benchmarks the project is optimizing toward.
Always measure before and after any optimization.

```
Ingestion latency    : < 200ms per cycle (all 4 ETFs concurrently)
Dashboard load       : < 100ms (from cache)
Historical query     : < 500ms (2M rows, date range)
Rebalancer compute   : < 10ms
```

---

## Phase Status
Update this every time a phase is completed.

| Phase | Status | Notes |
|-------|--------|-------|
| 1 — Foundation | 🔲 Not started | |
| 2 — Ingestion | 🔲 Not started | |
| 3 — Storage | 🔲 Not started | |
| 4 — Rebalancer | 🔲 Not started | |
| 5 — API | 🔲 Not started | |
| 6 — Frontend | 🔲 Not started | |
| 7 — Analysis | 🔲 Not started | |
| 8 — Timing + Benchmarks | 🔲 Not started | |
| 9 — Deploy + README | 🔲 Not started | |

---

## How To Start A Session
Always begin with this prompt pattern:

```
Read CLAUDE.md before writing any code.
We are building the ETF Portfolio Intelligence System per MASTER_PLAN.md.
Current phase: [PHASE NUMBER AND NAME]
Current file: [FILENAME]
Do not refactor existing files unless I ask.
Ask clarifying questions before writing code.
```

## Orchestration Rules
- One file at a time — never ask for an entire phase in one shot
- Verify each file before moving to the next (verification commands are in MASTER_PLAN.md)
- Commit after every working file: `git add -A && git commit -m "phase1: add schema.sql"`
- Design non-trivial algorithms (allocator, spread analysis) in chat before handing to Claude Code
- If Claude Code touches a file you didn't ask about, undo it

---

## What This Project Is NOT Building
- Automated trade execution
- Price prediction or ML models
- Multi-user auth (Phase 2 — but architect for it)
- Options or individual stocks
- Tax optimization
- Native mobile app
