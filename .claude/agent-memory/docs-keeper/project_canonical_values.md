---
name: Canonical implementation values — Phases 1-3
description: Verified source-of-truth values for schema, allocations, validator logic, and scheduler behavior as of 2026-03-14
type: project
---

Verified from source files on 2026-03-14. These are authoritative — code is the source of truth.

**TARGET_ALLOCATIONS (settings.py)**
- HXQ.TO: 40.0%
- VFV.TO: 35.0%
- VCN.TO: 15.0%
- ZEM.TO: 10.0%
MASTER_PLAN.md Data Architecture section and CLAUDE.md ETF table still show the old values (HXQ=35%, VFV=40%) and are not to be touched by this agent. The code and schema.sql seed data are consistent with HXQ=40/VFV=35.

**quotes table columns (schema.sql)**
time, ticker, bid, ask, spread, price, volume — `price NUMERIC(10,4)` is present as a full column, not an afterthought.

**transactions table columns (schema.sql)**
id, date, ticker, shares, fill_price, predicted_spread, actual_spread, slippage_vs_mid, account — `price_paid` does NOT exist; it was replaced by the four fill/spread columns.

**validator.py rejection logic**
Relative spread threshold: `(ask - bid) / price > MAX_SPREAD_RATIO` where `MAX_SPREAD_RATIO = 0.02` (2%). This is NOT a flat dollar amount. Variable name is `spread_ratio`.

**scheduler.py — daily summary cron**
`compute_daily_summary` fires at 16:01 ET via APScheduler cron. Derived from: `hour=_close_hour` (16), `minute=_close_minute + 1` (0+1=1). Confirmed by reading scheduler.py lines 90-96.

**summarizer.py behavior**
- Uses `time_bucket('1 day', time)` grouped by ticker
- Filters `WHERE spread IS NOT NULL` (excludes outside-hours rows)
- Idempotent via `ON CONFLICT (date, ticker) DO UPDATE`
- Computes: avg_spread, min_spread, max_spread, volatility_score (STDDEV)
- Does NOT compute spread_by_hour — that is reserved for analysis/spread.py

**Why:** These values were all confirmed by user report and verified against actual source files. They diverge from MASTER_PLAN.md in places, but MASTER_PLAN.md is off-limits for this agent.

**How to apply:** When any future phase doc references allocations, quotes columns, transactions columns, validator thresholds, or summary scheduling, use these values. Do not trust MASTER_PLAN.md Data Architecture section for schema column lists — read schema.sql directly.
