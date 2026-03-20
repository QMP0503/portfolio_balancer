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
| HXQ | Horizons Nasdaq 100 | 40% | Retirement (TFSA) |
| VFV | Vanguard S&P 500 | 35% | Retirement (TFSA) |
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
| Execution Simulator | C++ | Low-latency order replay engine, HFT interview signal |
| Email Parsing | Gmail API + Python regex | Auto-ingests Wealthsimple fill confirmations |

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
│   ├── transactions/
│   │   └── gmail_parser.py   # parses Wealthsimple fill emails → POST /transactions
│   │
│   ├── benchmark/
│   │   └── profiler.py       # measures ingestion throughput + query latency
│   │
│   └── main.py               # FastAPI endpoints
│
├── simulator/                            # C++ order execution simulator
│   ├── src/
│   │   ├── order_book.cpp    # price-time priority matching engine
│   │   ├── replay.cpp        # replays historical bid/ask tape from TimescaleDB
│   │   └── main.cpp          # CLI entry point + benchmark runner
│   ├── include/
│   │   └── order_book.h
│   ├── benchmarks/
│   │   └── results.md        # Python vs C++ replay latency comparison
│   └── CMakeLists.txt
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
│   ├── PHASE_8_DEPLOY.md
│   └── PHASE_9_SIMULATOR.md
│
├── docker-compose.yml
├── nginx.conf
└── README.md                 # benchmark results + setup instructions
```

---

## Build Order

Each phase is independently shippable. Never move to the next phase until the current one works.

**Deployment priority:** Ship phases 5 → 6 → 8 before anything else. The scheduler must be live on the server collecting minute-level data as early as possible — Phase 7 (pattern analysis) is only valuable with a strong historical baseline, so getting data collection running takes priority over analysis features.

| Phase | What | Files | Status |
|-------|------|-------|--------|
| 1 | Foundation | `schema.sql`, `database.py`, `settings.py` | ✅ Done |
| 2 | Data ingestion | `fetcher.py`, `validator.py`, `scheduler.py` | ✅ Done |
| 3 | Storage + summaries | `summarizer.py` | ✅ Done |
| 4 | Rebalancer | `allocator.py`, `timing.py` | ✅ Done |
| 5 | API layer | `main.py` endpoints | 🔲 Not started |
| 6 | React frontend | `Dashboard`, `Allocation`, `BuyRecommendation`, `ExecutionBenchmark` | 🔲 Not started |
| 8 | Deploy + README | Docker, Nginx, benchmark results | 🔲 Not started — **deploy target, unlocks data collection** |
| 6.5 | Gmail transaction parser | `gmail_parser.py` | 🔲 Not started — deferred after deploy; requires Gmail API OAuth setup |
| 7 | Pattern analysis | `spread.py`, `volatility.py`, `anomaly.py` | 🔲 Not started — deferred until sufficient historical data exists (weeks of collection) |
| 9 | C++ execution simulator | `order_book.cpp`, `replay.cpp`, Python vs C++ benchmarks | 🔲 Not started — Shopify internship |

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

Transactions (auto-ingested from Wealthsimple fill emails)
├── date
├── ticker
├── shares bought
├── fill price (from email)
├── predicted spread (from yfinance data at fill time)
├── actual spread (ask - bid at fill time, from quotes table)
├── slippage vs mid
└── account (TFSA/FHSA/RRSP)

Config (your target allocations)
├── ticker
├── target percentage
└── goal

Users (authentication — multi-user ready)
├── id (serial primary key)
├── email (unique login identifier)
├── first_name
├── last_name
├── hashed_password (bcrypt)
├── is_active (disable without deleting)
├── role (admin | user)
├── created_at
└── updated_at

Note: holdings and transactions will gain a user_id FK when multi-user is enabled post-graduation.
```

### Auth
JWT tokens. Default expiry 1 day, 30 days with "remember me".
Secret and algorithm stored in `.env` as `JWT_SECRET` and `JWT_ALGORITHM`.

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

## The C++ Simulator Story

### What It Does
Replays historical minute-level bid/ask data through a price-time priority order book to simulate execution quality. Answers: "if I had placed a limit order at $X, would it have filled? How long would I have waited? What was my slippage vs mid?"

### Why C++ (not Python)
```
Python replay (naive):  ~50ms per simulated trading day
C++ replay engine:      ~200μs per simulated trading day
Speedup:                ~250x — fast enough to run Monte Carlo
                        simulations across 6 months of data in < 1 second
```

### How It Connects to the ETF System
```
Rebalancer recommends: buy 3 VFV @ market
        ↓
Simulator replays historical tape for that ticker
        ↓
Reports: expected fill price, time to fill, slippage vs mid
        ↓
You execute on Wealthsimple
        ↓
Gmail parser ingests actual fill from confirmation email
        ↓
App compares: predicted slippage vs actual slippage over time
```

### Benchmark Targets
```
Order replay throughput  : > 1M orders/second
Simulated day latency    : < 500μs
Python vs C++ comparison : documented in simulator/benchmarks/results.md
Slippage prediction acc  : tracked against real fills over time
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

## Future Roadmap (Post-Graduation)

### During Shopify Internship (May–Aug 2026)
- C++ simulator (Phase 8) — build during evenings/weekends
- Phase 9 AI Analyzer (see MASTER_PLAN_PART2.md) — Ollama locally, Claude API for prod

### After Graduation
- Multi-user support (database already has user_id hooks)
- Questrade or Interactive Brokers API → automated execution
- Money hits account → rebalancer runs → orders execute automatically
- Correlation analysis: flag HXQ/VFV overlap

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

*"Built a self-hosted ETF portfolio intelligence system — a high-performance minute-level market data ingestion engine storing 2M+ records in TimescaleDB, with intraday spread pattern analysis, volatility scoring, and a React rebalancing dashboard. Optimized concurrent ingestion pipeline from 800ms to 50ms using asyncio. Extended with a C++ order execution simulator that replays historical bid/ask data at 250x the speed of a Python equivalent, used to validate slippage predictions against real Wealthsimple fills auto-ingested from Gmail. Deployed on personal Linux server via Docker."*

---

## The Interview Conversation

**"Tell me about your project"**

*"I built a tool I actually use for my own investing. The interesting engineering problem was the data layer — I needed to ingest minute level bid/ask data for 4 ETFs continuously and query it fast enough to power real time rebalancing decisions. I hit a bottleneck with sequential API calls taking 800ms so I rewrote the fetcher with asyncio and got it down to 50ms. The historical spread data feeds a pattern analyzer that tells me the optimal time of day to execute my monthly buys. I then extended it with a C++ order execution simulator — it replays the historical bid/ask tape through a price-time priority matching engine so I can simulate what my fill price would have been at different times. The C++ version runs about 250x faster than my Python prototype, which lets me run Monte Carlo simulations across months of data in under a second. I validate the simulator's slippage predictions against my actual fills, which get auto-ingested from my Wealthsimple confirmation emails via Gmail API."*

**"What would you do differently or next?"**

*"The natural next step is tick level data which would require a fundamentally different storage architecture — probably switching from row oriented to columnar storage and adding a message queue between ingestion and storage to handle the volume spikes at market open."*

---

## Status Tracker

| Phase | Status | Notes |
|-------|--------|-------|
| 1 — Foundation | ✅ Done | settings.py, schema.sql, database.py, main.py skeleton committed in d9c055a and ecbfdc4. |
| 2 — Ingestion | ✅ Done | fetcher.py, validator.py, scheduler.py committed in 053ab80 and 5c3a6d1; test_validator.py included. |
| 3 — Storage | ✅ Done | summarizer.py committed in 8c5b9ed. compute_daily_summary + backfill_summaries working. |
| 4 — Rebalancer | ✅ Done | allocator.py + timing.py committed in 47e0f9f and d5d6913. 15 tests passing. `gmail_parser.py` deferred to Phase 6.5. |
| 5 — API | ✅ Done | 6 endpoints across 4 routers + JWT auth + 23 integration tests passing. |
| 6 — Frontend | 🔲 Not started | |
| 7 — Analysis | 🔲 Not started | |
| 8 — Deploy + README | 🔲 Not started | |
| 9 — C++ Simulator | 🔲 Not started | Shopify internship. |

---

## Agent Notes

_Added 2026-03-14 by master-plan-updater agent._

**1. summarizer.py is untracked in git.**
The file exists at `etf-intelligence/backend/storage/summarizer.py` and its `__pycache__` confirms it has been executed, but it has never been committed. Phase 3 cannot be marked complete until this file is committed. Recommend: `git add etf-intelligence/backend/storage/summarizer.py && git commit -m "phase3: add summarizer.py"`.

**2. Schema deviations from the Data Architecture section (user-reported, not yet reflected in plan).**
The following changes were made during Phase 2 and Phase 3 implementation but are not documented in the "What Gets Stored" section above:
- `quotes` table: a `price` column was added (committed in 5c3a6d1 "built fetcher.py and add price to database").
- `transactions` table: `price_paid` was replaced by `fill_price`, `predicted_spread`, `actual_spread`, and `slippage_vs_mid`.

**3. TARGET_ALLOCATIONS deviate from plan document.**
The user reports settings.py now has HXQ=40%, VFV=35%. The Data Architecture section and CLAUDE.md ETF table still show HXQ=35%, VFV=40%. These sections are protected from direct edits — confirm which is authoritative before updating the plan document.

**4. scheduler.py cron behavior (user-reported, not verifiable from git message alone).**
User reports APScheduler triggers `compute_daily_summary` at 16:01 ET daily; commit 053ab80 "finish phase 2" is the relevant commit, but the message does not confirm this detail. Recorded here for traceability.

**5. validator.py rejection logic (user-reported).**
User reports the relative spread threshold is `(ask - bid) / price > 2%`; committed in 053ab80. Not verifiable from the commit message alone — recorded here for traceability.
