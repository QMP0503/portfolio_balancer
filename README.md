# ETF Portfolio Intelligence System

A self-hosted portfolio rebalancer that ingests minute-level market data for 4 Canadian ETFs, analyzes historical spread patterns, and tells you exactly what to buy on payday.

## ETFs Tracked

| Ticker | Name | Target |
|--------|------|--------|
| HXQ.TO | Horizons Nasdaq 100 | 35% |
| VFV.TO | Vanguard S&P 500 | 40% |
| VCN.TO | Vanguard Canada | 15% |
| ZEM.TO | BMO Emerging Markets | 10% |

## Stack

- **Backend:** FastAPI + Python asyncio
- **Database:** TimescaleDB (Docker)
- **Frontend:** React + Vite
- **Data:** yfinance (minute-level bid/ask)
- **Scheduling:** APScheduler
- **Deploy:** Docker Compose + Nginx

## Performance Targets

| Metric | Target |
|--------|--------|
| Ingestion latency | < 200ms (all 4 ETFs concurrent) |
| Dashboard load | < 100ms (cached) |
| Historical query | < 500ms (2M+ rows) |
| Rebalancer compute | < 10ms |

## Build Phases

1. Foundation — schema, DB connection, config
2. Ingestion — fetcher, validator, scheduler
3. Storage — summarizer, daily pre-computation
4. Rebalancer — allocation algorithm
5. API — FastAPI endpoints
6. Frontend — React dashboard
7. Analysis — spread, volatility, anomaly detection
8. Timing + Benchmarks — profiler, execution windows
9. Deploy + README — Docker, Nginx, benchmark results

## Status

All phases in progress. See `docs/MASTER_PLAN.md` for full plan.
