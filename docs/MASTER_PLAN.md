# ETF Portfolio Intelligence System — Master Plan

## One Line
A self-hosted portfolio rebalancer powered by a high-performance market data ingestion engine that learns from historical patterns to make smarter buy decisions.

## Why This Exists
Manual ETF investing on Wealthsimple involves too much guesswork:
- Buying on payday without knowing if timing is good
- Manually calculating how much of each ETF to buy to maintain target allocation
- No visibility into whether current market conditions are normal or unusual
- No historical context for when spreads are tightest

This tool solves all of that.

---

## Current Portfolio

| ETF | Name | Target Allocation | Goal |
|-----|------|------------------|------|
| HXQ | Horizons Nasdaq 100 | 35% | Retirement (TFSA) |
| VFV | Vanguard S&P 500 | 40% | Retirement (TFSA) |
| VCN | Vanguard Canada | 15% | Retirement (TFSA) |
| ZEM | BMO Emerging Markets | 10% | Retirement (TFSA) |

**Accounts:** TFSA (primary) → FHSA → RRSP
**Contribution:** $1,000–1,500 CAD monthly on payday
**Broker:** Wealthsimple (no public API — manual execution for now)
**Horizon:** 20+ years

---

## The Three Layers

```
Layer 1: Data Engine          ← performance story for HFT firms
Layer 2: Pattern Analysis     ← quant story for Two Sigma, Citadel
Layer 3: Rebalancer Product   ← practical tool you actually use
```

Each layer feeds the next. Each is independently impressive.

---

## What This Is NOT Building

```
✗ Automated trade execution (no Wealthsimple API yet)
✗ Price prediction or ML models
✗ Multi-user auth (Phase 2 — architecture supports it)
✗ Options or individual stocks
✗ Tax optimization
✗ Mobile native app (responsive React covers this)
```

---

## Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| Frontend | React + Vite | Mobile responsive, you know it |
| Backend | FastAPI (Python) | Fast to build, async support |
| Database | TimescaleDB | Justified at 2M+ rows, industry relevant |
| Data Source | yfinance | Free, minute level, works for Canadian ETFs |
| Ingestion | Python asyncio | Concurrent fetching, measurably faster |
| Scheduling | APScheduler | Runs ingestion every minute during market hours |
| Hosting | Your Linux server | Self-hosted, shows infrastructure ownership |
| Reverse Proxy | Nginx | Public URL, clean routing |
| Benchmarking | Python time + custom profiler | Documents performance story |
| Containerization | Docker Compose | Reproducible, portable |

---

## Full File Structure

```
etf-intelligence/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx             # payday home screen
│   │   │   ├── Allocation.jsx            # current vs target chart
│   │   │   ├── BuyRecommendation.jsx     # what to buy + how many shares
│   │   │   ├── ExecutionTiming.jsx       # best time of day to buy
│   │   │   ├── Performance.jsx           # portfolio value over time
│   │   │   ├── SpreadAnalysis.jsx        # historical spread patterns
│   │   │   └── Settings.jsx              # allocation config + holdings
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
│
├── backend/
│   ├── ingestion/
│   │   ├── fetcher.py        # pulls minute level bid/ask/volume from yfinance
│   │   ├── validator.py      # handles missing, stale, bad data
│   │   └── scheduler.py      # runs fetcher every minute during market hours
│   │
│   ├── storage/
│   │   ├── database.py       # TimescaleDB connection + query helpers
│   │   ├── schema.sql        # hypertable definitions
│   │   └── summarizer.py     # pre-computes daily summaries from raw data
│   │
│   ├── analysis/
│   │   ├── spread.py         # intraday spread patterns by time of day
│   │   ├── volatility.py     # rolling volatility scoring per ETF
│   │   └── anomaly.py        # detects unusual spread or volume conditions
│   │
│   ├── rebalancer/
│   │   ├── allocator.py      # core buy recommendation algorithm
│   │   └── timing.py         # best execution window from historical patterns
│   │
│   ├── benchmark/
│   │   └── profiler.py       # measures ingestion throughput + query latency
│   │
│   └── main.py               # FastAPI endpoints
│
├── config/
│   └── settings.py           # tickers, target allocations, intervals
│
├── docs/
│   ├── MASTER_PLAN.md        # this file
│   ├── PHASE_1_FOUNDATION.md
│   ├── PHASE_2_INGESTION.md
│   ├── PHASE_3_STORAGE.md
│   ├── PHASE_4_REBALANCER.md
│   ├── PHASE_5_API.md
│   ├── PHASE_6_FRONTEND.md
│   ├── PHASE_7_ANALYSIS.md
│   └── PHASE_8_DEPLOY.md
│
├── docker-compose.yml
├── nginx.conf
└── README.md                 # benchmark results + setup instructions
```

---

## Build Order

Each phase is independently shippable. Never move to the next phase until the current one works.

| Phase | What | Files | Timeline |
|-------|------|-------|----------|
| 1 | Foundation | `schema.sql`, `database.py`, `settings.py` | Week 1 |
| 2 | Data ingestion | `fetcher.py`, `validator.py`, `scheduler.py` | Week 2 |
| 3 | Storage + summaries | `summarizer.py` | Week 3 |
| 4 | Core rebalancer | `allocator.py` | Week 4 |
| 5 | API layer | `main.py` endpoints | Week 4–5 |
| 6 | React frontend | `Dashboard`, `Allocation`, `BuyRecommendation` | Week 5–6 |
| 7 | Pattern analysis | `spread.py`, `volatility.py`, `anomaly.py` | Week 6–7 |
| 8 | Timing + benchmarks | `timing.py`, `profiler.py` | Week 7–8 |
| 9 | Deploy + README | Docker, Nginx, benchmark results | Week 8 |

---

## Phase Implementation Guide

> One file at a time. Verify before moving on. Commit after every working file.

---

### Phase 1 — Foundation
**Goal:** Database running, schema loaded, settings defined, connection verified.

#### File 1: `config/settings.py`

**Prompt:**
```
Create config/settings.py.

It should define:
- TICKERS: list = ["HXQ.TO", "VFV.TO", "VCN.TO", "ZEM.TO"]
- TARGET_ALLOCATIONS: dict mapping each ticker to its target percentage
  (HXQ=35, VFV=40, VCN=15, ZEM=10)
- MARKET_OPEN: time = "09:30"
- MARKET_CLOSE: time = "16:00"
- TIMEZONE: str = "America/Toronto"
- DATABASE_URL: str loaded from environment variable DATABASE_URL
- FETCH_INTERVAL_SECONDS: int = 60

Use python-dotenv to load the .env file.
Include type hints and a module docstring.
No classes, just module-level constants.
```

**Verify:** `python -c "from config.settings import TICKERS; print(TICKERS)"` should print the 4 tickers.

---

#### File 2: `backend/storage/schema.sql`

**Prompt:**
```
Create backend/storage/schema.sql.

Tables needed:

1. quotes — raw minute-level data, hypertable on time
   columns: time TIMESTAMPTZ NOT NULL, ticker TEXT NOT NULL,
   bid NUMERIC(10,4), ask NUMERIC(10,4),
   spread NUMERIC(10,4), volume BIGINT

2. daily_summaries — pre-computed from raw
   columns: date DATE NOT NULL, ticker TEXT NOT NULL,
   avg_spread NUMERIC(10,4), min_spread NUMERIC(10,4),
   max_spread NUMERIC(10,4), volatility_score NUMERIC(6,4)

3. holdings — shares owned per ticker
   columns: ticker TEXT PRIMARY KEY, shares NUMERIC(12,4),
   last_updated TIMESTAMPTZ DEFAULT NOW()

4. transactions — log of every buy
   columns: id SERIAL PRIMARY KEY, date DATE NOT NULL,
   ticker TEXT NOT NULL, shares NUMERIC(12,4),
   price_paid NUMERIC(10,4), account TEXT CHECK (account IN ('TFSA','FHSA','RRSP'))

5. etf_config — target allocations
   columns: ticker TEXT PRIMARY KEY, target_pct NUMERIC(5,2), goal TEXT

After creating tables:
- Call create_hypertable('quotes', 'time')
- Add compression policy on quotes with INTERVAL '7 days', segmentby ticker
- Add unique constraint on daily_summaries(date, ticker)
- Seed etf_config with the 4 ETFs and their targets

No SELECT *, no inline SQL elsewhere. This file is the single source of truth for schema.
```

**Verify:**
```bash
docker compose exec db psql -U quang -d etf_db -f /app/storage/schema.sql
docker compose exec db psql -U quang -d etf_db -c "\dt"
```
Should show all 5 tables.

---

#### File 3: `backend/storage/database.py`

**Prompt:**
```
Create backend/storage/database.py.

Requirements:
- Use SQLAlchemy async engine with asyncpg driver
- Load DATABASE_URL from config/settings.py
- Create async engine and session factory
- Define get_db() as an async generator (for FastAPI Depends)
- Define two query helper functions:
    fetch_latest_quotes() -> list[dict]: returns most recent quote per ticker
    fetch_quote_history(ticker: str, days: int) -> list[dict]: returns rows for date range
- All functions must have type hints and docstrings
- No SELECT * in any query
- Use text() from sqlalchemy for raw SQL, explicitly name all columns

Do not create any endpoints. This file is only the DB layer.
```

**Verify:**
```bash
docker compose exec backend python -c "
import asyncio
from storage.database import fetch_latest_quotes
asyncio.run(fetch_latest_quotes())
print('DB connection OK')
"
```

---

#### File 4: `backend/main.py` (skeleton only)

**Prompt:**
```
Create backend/main.py as a skeleton only.

Include:
- FastAPI app instantiation
- GET /health endpoint returning {"status": "ok", "version": "0.1.0"}
- Import settings from config/settings.py
- A startup event that logs "ETF Intelligence System starting"
- CORS middleware allowing localhost:5173 (Vite dev server)

Do not add any other endpoints yet. Those come in Phase 5.
Every endpoint must have a response_model — define a simple HealthResponse Pydantic model.
```

**Verify:** `curl http://localhost:8000/health` returns `{"status":"ok","version":"0.1.0"}`

**Phase 1 complete when:** All 4 files exist, DB has 5 tables, health endpoint responds.

---

### Phase 2 — Data Ingestion
**Goal:** Minute-level quotes flowing into TimescaleDB automatically.

#### File 1: `backend/ingestion/fetcher.py`

**Design this in chat before implementing.** Key decisions:
- How to handle yfinance returning no data outside market hours
- What fields to extract from yfinance response
- Return type contract (what dict shape does the scheduler expect)

**Prompt (after design):**
```
Create backend/ingestion/fetcher.py.

[PASTE THE DESIGN WE AGREED ON]

Requirements:
- async def fetch_all(tickers: list[str]) -> list[dict]
- Uses asyncio.gather() for concurrent fetching
- Uses asyncio.to_thread() to wrap synchronous yfinance calls
- return_exceptions=True on gather — log errors, don't crash
- async def fetch_one(ticker: str) -> dict — single ETF fetch
- Both functions need type hints and docstrings
- No blocking calls inside async functions
```

**Verify:**
```bash
docker compose exec backend python -c "
import asyncio
from ingestion.fetcher import fetch_all
from config.settings import TICKERS
results = asyncio.run(fetch_all(TICKERS))
print(results)
"
```

---

#### File 2: `backend/ingestion/validator.py`

**Prompt:**
```
Create backend/ingestion/validator.py.

Define validate_quote(quote: dict) -> dict | None

Rules:
- Return None if bid or ask is missing or zero
- Return None if ask < bid (crossed market)
- Return None if spread > 2.0 (likely bad data, not a real spread)
- Return None if volume is negative
- If valid, add computed field: spread = ask - bid
- Log a warning for each rejected quote with the reason

Type hints and docstring required.
No side effects — pure function, no DB calls.
```

**Verify:** Write 3 test cases in the terminal — one valid quote, one with missing ask, one with crossed market.

---

#### File 3: `backend/ingestion/scheduler.py`

**Prompt:**
```
Create backend/ingestion/scheduler.py.

Requirements:
- Use APScheduler AsyncIOScheduler
- Run fetch_and_store() every 60 seconds
- fetch_and_store() should:
    1. Check if current time is within market hours (use settings.MARKET_OPEN/CLOSE/TIMEZONE)
    2. If outside market hours, log and skip
    3. Call fetch_all() from fetcher.py
    4. Call validate_quote() on each result
    5. Insert valid quotes into DB using database.py
- Define start_scheduler() and stop_scheduler() functions
- Log each ingestion cycle: how many fetched, how many valid, how many inserted

Type hints and docstrings required.
Do not hardcode tickers — use config.settings.TICKERS.
```

**Verify:** Run scheduler manually for 2 minutes during market hours, check DB row count increases.

---

### Phase 3 — Storage + Summaries
**Goal:** Daily summaries auto-computed from raw data.

#### File: `backend/storage/summarizer.py`

**Design the SQL query in chat first** — uses `time_bucket()` and is the first non-trivial TimescaleDB query.

**Prompt (after design):**
```
Create backend/storage/summarizer.py.

Define:
- async def compute_daily_summary(date: date) -> None
  Aggregates quotes for the given date into daily_summaries table.
  Uses time_bucket('1 day', time) grouped by ticker.
  Computes: avg_spread, min_spread, max_spread, volatility_score (stddev of spread).
  Uses INSERT ... ON CONFLICT (date, ticker) DO UPDATE for idempotency.

- async def backfill_summaries(start_date: date, end_date: date) -> None
  Calls compute_daily_summary for each date in range.
  Logs progress.

Type hints and docstrings. No SELECT *. No inline SQL — use named query constants at top of file.
```

**Verify:** Insert a few fake quotes manually, run `compute_daily_summary(today)`, check daily_summaries table.

---

### Phase 4 — Core Rebalancer
**Goal:** Given holdings + contribution amount → buy recommendations.

**Design the entire algorithm in chat before touching Claude Code.**

Work through:
- How to compute current allocation % from shares × price
- How to decide which ETFs are underweight
- How to allocate a contribution across underweight ETFs
- How to convert dollar amounts to whole share counts

#### File: `backend/rebalancer/allocator.py`

**Prompt (after full algorithm design):**
```
Create backend/rebalancer/allocator.py.

[PASTE FULL ALGORITHM SPEC FROM CHAT]

Define:
- async def get_recommendations(contribution_cad: float) -> list[BuyRecommendation]
- BuyRecommendation is a Pydantic model with:
  ticker, shares_to_buy, price, total_cost, reason

Type hints, docstrings, single-purpose functions.
The allocation math must be in pure helper functions (no async, no DB) so it's testable.
```

**Verify:** Call with a $1200 contribution, confirm recommendations add up to ≤ $1200 and target underweight ETFs.

---

### Phase 5 — API Layer
**Goal:** All endpoints working, documented at /docs.

#### File: `backend/main.py` (full implementation)

**Prompt:**
```
Expand backend/main.py to add all endpoints.

Endpoints:
- GET /quotes/latest — response_model: list[QuoteResponse]
- GET /quotes/{ticker} with query param days: int = 7 — response_model: list[QuoteResponse]
- GET /spreads/summary — response_model: list[SpreadSummaryResponse]
- GET /rebalancer/recommend with query param contribution: float — response_model: list[BuyRecommendation]
- GET /holdings — response_model: list[HoldingResponse]
- POST /holdings — request body: HoldingUpdate, response_model: HoldingResponse

Define all Pydantic response models in a separate backend/models.py file.
Every endpoint is async def.
Every endpoint uses Depends(get_db).
HTTPException 404 if no data found.
Do not modify the /health endpoint.
```

**Verify:** Hit every endpoint via `http://localhost:8000/docs` Swagger UI.

---

### Phase 6 — React Frontend
**Goal:** Dashboard usable on payday.

Build components in this order — each is independently useful:

| Component | Focus |
|-----------|-------|
| `Allocation.jsx` | Bar chart: current % vs target % per ticker |
| `BuyRecommendation.jsx` | Table: ticker, shares, price, total |
| `Dashboard.jsx` | Assembles Allocation + BuyRecommendation, contribution input |
| `ExecutionTiming.jsx` | "Best time to buy today" from /rebalancer/timing |
| `SpreadAnalysis.jsx` | Historical spread chart per ticker |
| `Settings.jsx` | Edit holdings after a buy |

**For each component:**
```
Create frontend/src/components/[ComponentName].jsx.

Data comes from GET [endpoint] via a custom hook in frontend/src/api.js.
If api.js doesn't exist yet, create it with a fetch wrapper.
Component must be under 150 lines.
Use only Tailwind utility classes for styling.
No prop drilling — fetch data inside the component hook.
No default exports that need props — use internal state.
```

**Verify each component:** Open in browser, confirm data loads, no console errors.

---

### Phase 7 — Pattern Analysis
**Goal:** Spread patterns, volatility scores, anomaly detection.

**Design each algorithm in chat first.**

| File | What to design first |
|------|---------------------|
| `spread.py` | How to compute "best hour to buy" from historical spread-by-hour |
| `volatility.py` | Rolling window size, what volatility_score means in plain English |
| `anomaly.py` | What threshold makes a spread "abnormal" vs normal variation |

These feed the `ExecutionTiming` component and the ⚠️ warnings on the dashboard.

---

### Phase 8 — Timing + Benchmarks
**Goal:** Documented performance story for interviews.

#### File: `backend/benchmark/profiler.py`

**Prompt:**
```
Create backend/benchmark/profiler.py.

Define two benchmark functions:

1. benchmark_ingestion(runs: int = 10) -> dict
   - Runs fetch_all() sequentially 10 times, records wall time each run
   - Runs fetch_all() concurrently (asyncio.gather of 10 runs), records wall time
   - Returns: {sequential_avg_ms, concurrent_avg_ms, speedup_factor}

2. benchmark_query(rows: int) -> dict
   - Inserts `rows` fake quotes into DB
   - Times a 7-day range query on the hypertable
   - Returns: {row_count, query_time_ms}

Print results in a readable table.
This is the data that goes in README.md.
```

**Run this and save the output** — it becomes the benchmark results section in README.

---

### Phase 9 — Deploy + README

#### Nginx config
```
Create nginx.conf that:
- Proxies /api/* to backend:8000
- Serves frontend static files from /usr/share/nginx/html
- Listens on port 80
```

#### README.md
Write this yourself — it's your voice. Use benchmark numbers from Phase 8. Structure:
1. What it does (one paragraph)
2. Architecture diagram (text art is fine)
3. Benchmark results table
4. How to run locally (`docker compose up -d`)
5. The interview answer from this document

---

## Quick Reference: Verification Commands

```bash
# Check containers
docker compose ps

# Check DB tables
docker compose exec db psql -U quang -d etf_db -c "\dt"

# Count quotes in DB
docker compose exec db psql -U quang -d etf_db -c "SELECT COUNT(*) FROM quotes;"

# Tail backend logs
docker compose logs -f backend

# Restart backend after code change
docker compose restart backend

# Connect to DB directly
docker compose exec db psql -U quang -d etf_db
```

---

## Red Flags — Stop and Check

If Claude Code does any of these, undo and re-prompt:

- Modifies a file you didn't ask it to touch
- Uses `SELECT *` anywhere
- Creates a synchronous DB function inside an async endpoint
- Hardcodes tickers or allocations instead of reading from settings.py
- Writes a component over 150 lines
- Creates a class where a function would do
- Skips type hints or docstrings

---

## Data Architecture

### What Gets Stored

```
Raw minute quotes (keep forever — source of truth)
├── ticker
├── timestamp
├── bid price
├── ask price
├── spread (ask - bid)
└── volume

Daily summaries (pre-computed from raw — recomputable anytime)
├── date
├── ticker
├── avg spread
├── min spread
├── max spread
├── spread by hour (for execution timing)
└── volatility score

Holdings (you update after each payday buy)
├── ticker
├── shares owned
└── last updated

Transactions (log of every buy)
├── date
├── ticker
├── shares bought
├── price paid
└── account (TFSA/FHSA)

Config (your target allocations)
├── ticker
├── target percentage
└── goal
```

### Why TimescaleDB Not SQLite

| | SQLite | TimescaleDB |
|--|--------|------------|
| 2M+ rows | Slow range queries | Built for this |
| Time series compression | None | 90% storage reduction |
| Concurrent ingestion | Single writer bottleneck | Handles it |
| Industry relevance | Generic | Financial systems standard |

### Data Retention Policy

```
Raw minute data  → keep forever, TimescaleDB compresses after 7 days
Daily summaries  → keep forever
Reason           → raw data is source of truth, 
                   summaries always recomputable,
                   never delete financial data
```

---

## The Performance Story

### The Problem (naive approach)
```python
# Sequential fetching — 800ms total
fetch HXQ  → 200ms
fetch VFV  → 200ms
fetch VCN  → 200ms
fetch ZEM  → 200ms
```

### The Solution (optimized approach)
```python
# Concurrent fetching with asyncio — ~50ms total
fetch all 4 simultaneously → 200ms wall time
+ caching with smart invalidation
+ pre-computation on schedule
= ~50ms perceived latency on dashboard load
```

### Benchmark Targets
```
Ingestion latency    : < 200ms per cycle (all 4 ETFs)
Dashboard load       : < 100ms (cached)
Historical query     : < 500ms (2M rows, date range)
Rebalancer compute   : < 10ms
```

---

## What The App Shows On Payday

```
─────────────────────────────────────────
Portfolio Rebalancer              Mar 9
─────────────────────────────────────────
Total Value: $46,397 CAD     +25.1% all time

Allocation
HXQ  ████████████  46.7% → 35%  ↓ overweight
VFV  █████████     32.6% → 40%  ↑ underweight
VCN  ████          12.1% → 15%  ↑ underweight
ZEM  █             4.3%  → 10%  ↑ underweight

─────────────────────────────────────────
Contribute: $1,200

Recommended buys:
VFV  → 3 shares  @ $108.79  =  $326
VCN  → 4 shares  @ $67.89   =  $272
ZEM  → 15 shares @ $40.02   =  $600
HXQ  → skip this month (overweight)

─────────────────────────────────────────
Best time to buy today: 11am – 2pm EST
ZEM spread currently 2.1x wider than normal ⚠️
─────────────────────────────────────────
```

---

## Future Roadmap (Post-May)

### Phase 2 — During Shopify Internship
- Wealthsimple CSV import → auto-update holdings
- ETF rater: score each holding on risk, growth, goal alignment
- Correlation analysis: flag HXQ/VFV overlap

### Phase 3 — After Graduation
- Multi-user support (database already has user_id hooks)
- Questrade or Interactive Brokers API → automated execution
- Money hits account → rebalancer runs → orders execute automatically

---

## Things To Learn Before Building

### This Week (concepts)
```
1. TimescaleDB basics
   → What is a hypertable
   → How time series compression works
   → docs.timescale.com/getting-started

2. asyncio in Python
   → What is async/await
   → Why concurrent fetching beats sequential
   → realpython.com/async-io-python

3. Bid/ask spread in real data
   → Pull one day of SPY minute data with yfinance
   → Observe how spread changes throughout the day
   → Just run yfinance in a notebook
```

### Next Week (tools)
```
4. FastAPI basics
   → How to define an endpoint
   → How to return JSON
   → fastapi.tiangolo.com/tutorial

5. Docker Compose
   → How to define two services
   → How frontend talks to backend
   → docs.docker.com/compose/gettingstarted
```

### Not Yet
```
✗ React (you already know enough)
✗ TimescaleDB advanced features
✗ Nginx config (covered in Phase 8)
✗ APScheduler (covered in Phase 2)
```

---

## Resume Line (When Complete)

*"Built a self-hosted ETF portfolio intelligence system — a high-performance minute-level market data ingestion engine storing 2M+ records in TimescaleDB, with intraday spread pattern analysis, volatility scoring, and a React rebalancing dashboard. Optimized concurrent ingestion pipeline from 800ms to 50ms using asyncio. Deployed on personal Linux server via Docker."*

---

## The Interview Conversation

**"Tell me about your project"**

*"I built a tool I actually use for my own investing. The interesting engineering problem was the data layer — I needed to ingest minute level bid/ask data for 4 ETFs continuously and query it fast enough to power real time rebalancing decisions. I hit a bottleneck with sequential API calls taking 800ms so I rewrote the fetcher with asyncio and got it down to 50ms. The historical spread data then feeds a pattern analyzer that tells me the optimal time of day to execute my monthly buys."*

**"What would you do differently or next?"**

*"The natural next step is tick level data which would require a fundamentally different storage architecture — probably switching from row oriented to columnar storage and adding a message queue between ingestion and storage to handle the volume spikes at market open."*

---

## Status Tracker

| Phase | Status | Notes |
|-------|--------|-------|
| 1 — Foundation | 🔲 Not started | |
| 2 — Ingestion | 🔲 Not started | |
| 3 — Storage | 🔲 Not started | |
| 4 — Rebalancer | 🔲 Not started | |
| 5 — API | 🔲 Not started | |
| 6 — Frontend | 🔲 Not started | |
| 7 — Analysis | 🔲 Not started | |
| 8 — Deploy | 🔲 Not started | |
| 9 — README + Benchmarks | 🔲 Not started | |
