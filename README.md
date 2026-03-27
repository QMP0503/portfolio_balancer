# ETF Portfolio Intelligence System

A self-hosted portfolio rebalancer that ingests minute-level market data for 4 Canadian ETFs, analyzes historical spread patterns, and tells you exactly what to buy on payday.

## What It Does

- Ingests minute-level bid/ask/volume data for 4 Canadian ETFs every minute during market hours
- Stores time series data in TimescaleDB (~2,600+ rows per ticker and growing)
- Calculates optimal buy amounts on payday given a contribution budget
- Shows current vs target allocation with deviation indicators
- Displays best execution windows based on historical spread patterns
- Self-hosted on a Linux server, accessible over Tailscale

## ETFs Tracked

| Ticker | Name | Target |
|--------|------|--------|
| HXQ.TO | Horizons Nasdaq 100 | 40% |
| VFV.TO | Vanguard S&P 500 | 35% |
| VCN.TO | Vanguard Canada | 15% |
| ZEM.TO | BMO Emerging Markets | 10% |

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + Python asyncio |
| Database | TimescaleDB (PostgreSQL extension) |
| Frontend | React 19 + Vite + Tailwind |
| Data source | yfinance (minute-level bid/ask) |
| Scheduling | APScheduler |
| Auth | JWT in httpOnly cookies |
| Deploy | Docker Compose + Nginx |
| Monitoring | Prometheus + Grafana |

## Performance

| Metric | Target | Approach |
|--------|--------|----------|
| Ingestion latency | < 200ms | `asyncio.gather` fetches all 4 ETFs concurrently |
| Dashboard load | < 100ms | Pre-computed daily summaries, cached quotes |
| Historical query | < 500ms | TimescaleDB hypertable on `time` column |
| Rebalancer compute | < 10ms | Pure Python, no DB call at compute time |

Sequential fetching would take ~800ms (4 × 200ms). Concurrent fetching brings this down to ~200ms wall time.

## Local Setup

**Prerequisites:** Docker, Docker Compose

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd portfolio_balancer/etf-intelligence

# 2. Create environment file
cp .env.example .env
# Edit .env — set JWT_SECRET, POSTGRES_PASSWORD, GRAFANA_PASSWORD

# 3. Start all services
docker compose up -d --build

# 4. Run database migrations
docker compose exec db psql -U postgres -d etf_db -f /docker-entrypoint-initdb.d/schema.sql

# 5. Seed sample data (optional)
docker compose exec backend python seed.py
```

App is at `http://localhost:80`. Grafana is at `http://localhost:3000`.

## Production Deploy

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

After `git pull`, rebuild with:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Grafana is exposed directly on port `3000` — no Nginx proxy needed (access via Tailscale).

## Project Structure

```
etf-intelligence/
├── backend/
│   ├── ingestion/        # fetcher, validator, scheduler
│   ├── storage/          # one file per domain (quotes, holdings, portfolios, summaries)
│   ├── rebalancer/       # allocation algorithm + execution timing
│   ├── analysis/         # spread, volatility, anomaly (Phase 7)
│   ├── routers/          # FastAPI route handlers (thin — no business logic)
│   ├── tests/            # 36 tests across all modules
│   └── main.py
├── frontend/
│   └── src/components/   # Dashboard, Allocation, BuyRecommendation, ExecutionTiming, Settings
├── nginx/
├── grafana/              # provisioning configs
└── docker-compose.yml
```

## Rebalancer Algorithm

Given a contribution amount in CAD:

1. Compute `new_total = current_portfolio_value + contribution`
2. For each ticker: `needed = new_total × target_pct − current_value`
3. Allocate whole shares proportionally to need
4. Greedy-fill leftover cash: buy 1 share at a time of the most underweight affordable ticker

This ensures the full budget is deployed and the result is as balanced as possible.

## Build Status

| Phase | Status |
|-------|--------|
| 1 — Foundation | Done |
| 2 — Ingestion | Done |
| 3 — Storage + summaries | Done |
| 4 — Rebalancer | Done |
| 5 — API + auth + tests | Done |
| 6 — React frontend | Done |
| 8 — Deploy + monitoring | Done |
| 7 — Spread/volatility analysis | Deferred — needs more historical data |
| 9 — C++ execution simulator | Planned |
