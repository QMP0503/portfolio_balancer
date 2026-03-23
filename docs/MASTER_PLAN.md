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
│   │   ├── database.py       # engine + session factory only (no query functions)
│   │   ├── schema.sql        # hypertable definitions
│   │   ├── summarizer.py     # pre-computes daily summaries from raw data
│   │   ├── quotes.py         # all queries for quotes table
│   │   ├── portfolios.py     # all queries for portfolios + portfolio_allocations
│   │   ├── holdings.py       # all queries for holdings table
│   │   └── summaries.py      # all queries for daily_summaries table
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
| 5 | API layer | 6 routers, JWT cookies, 36 tests | ✅ Done |
| 6 | React frontend | `Dashboard`, `Allocation`, `BuyRecommendation`, `ExecutionTiming`, `Settings`, `AddPortfolioModal` | 🔲 In progress |
| 8 | Deploy + README | Docker, Nginx, benchmark results | 🔲 Not started — **deploy target, unlocks data collection** |
| 6.5 | Gmail transaction parser | `gmail_parser.py` | 🔲 Deferred — after deploy; requires Gmail API OAuth setup |
| 6.6 | First-login setup wizard | Onboarding flow for new users | 🔲 Deferred — add after deploy when missing UX is clear |
| 7 | Pattern analysis | `spread.py`, `volatility.py`, `anomaly.py` | 🔲 Deferred — needs weeks of collected data |
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
JWT stored in **httpOnly cookie** (SameSite=strict, not Bearer header).
Default expiry 1 day, 30 days with "remember me".
Secret stored in `.env` as `JWT_SECRET`. Algorithm HS256.
Endpoints: POST /auth/login, /auth/register, /auth/logout.
get_current_user reads from Cookie header — no Authorization header needed.

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
| 4 — Rebalancer | ✅ Done | allocator.py + timing.py committed in 47e0f9f and d5d6913. Bug fix in 5866ae4: rebalancer now shows all 4 tickers, greedy-fills leftover cash, and displays correct post-buy percentages. |
| 5 — API | ✅ Done | JWT httpOnly cookies, 6 routers (auth/quotes/portfolios/holdings/rebalancer/summaries), 36 tests. Schema refactored: etf_config → per-user portfolios + portfolio_allocations. storage/ split into one file per domain. Committed abaaff5. |
| 6 — Frontend | ✅ Done | All 11 components complete 2026-03-21: Login, Register, Dashboard, Allocation (Recharts), BuyRecommendation, ExecutionTiming, AddPortfolioModal (3-step), Settings. Docker service added. |
| 6.5 — Gmail parser | 🔲 Deferred | After deploy. Requires Gmail API OAuth setup. |
| 6.6 — Setup wizard | 🔲 Deferred | First-login onboarding flow. Build after deploy when missing UX is clearer. |
| 7 — Analysis | 🔲 Deferred | Needs weeks of collected data to be meaningful. |
| 8 — Deploy + README | 🔧 In progress | nginx config, Dockerfile, prod compose overlay (a3e0a86), Prometheus metrics on FastAPI + ingestion (437d544), Grafana provisioning configs (6d54473), /api prefix added to all routes (75feca6). |
| 9 — C++ Simulator | 🔲 Not started | Shopify internship. |

---

## Agent Notes

_Added 2026-03-14, updated 2026-03-23 by master-plan-updater agent._

**1. summarizer.py was untracked as of 2026-03-14 — status unknown.**
The 2026-03-14 session found summarizer.py untracked in git. Phases 3 through 5 have since been marked complete by the user. If summarizer.py was committed as part of a later commit with a vague message, it is not individually traceable in git history. No further action required unless Phase 3 is re-examined.

**2. Schema deviations from the Data Architecture section (not yet reflected in plan).**
The following changes were made during implementation but are not documented in the protected "What Gets Stored" section above:
- `quotes` table: a `price` column was added (committed in 5c3a6d1).
- `transactions` table: `price_paid` was replaced by `fill_price`, `predicted_spread`, `actual_spread`, and `slippage_vs_mid`.

**3. TARGET_ALLOCATIONS deviate from plan document.**
settings.py has HXQ=40%, VFV=35%. The Data Architecture section and CLAUDE.md ETF table still show HXQ=35%, VFV=40%. Awaiting user confirmation of which is authoritative before the protected sections can be updated.

**4. Phase 8 deploy infrastructure committed but not yet confirmed complete.**
As of 2026-03-23, commits a3e0a86 through 1a2b2c2 show nginx, Dockerfile, prod compose, Prometheus, and Grafana all committed. Phase 8 is marked `🔧 In progress`. User should confirm whether the stack is live on the Linux server and README is written before marking complete.

**5. Phase 4 rebalancer fix (5866ae4) post-dates phase completion.**
commit 5866ae4 modified allocator.py and test_allocator.py after Phase 4 was marked done — this was a correctness fix (missing tickers, greedy fill, post-buy % display), not a new feature. Phase 4 remains `✅ Done`; the fix is noted in the Notes column.
