-- =============================================================================
-- ETF Portfolio Intelligence System — Database Schema
-- Single source of truth for all table definitions.
-- Run once against a fresh TimescaleDB instance.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. quotes
-- Raw minute-level bid/ask data ingested from yfinance.
-- Partitioned as a hypertable on time for fast range queries.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quotes (
    time    TIMESTAMPTZ  NOT NULL,
    ticker  TEXT         NOT NULL,
    bid     NUMERIC(10,4),
    ask     NUMERIC(10,4),
    spread  NUMERIC(10,4),
    price   NUMERIC(10,4),
    volume  BIGINT
);

-- Convert to hypertable — partitions data by time automatically
SELECT create_hypertable('quotes', 'time', if_not_exists => TRUE);

-- Compress chunks older than 7 days, co-locate rows by ticker for fast per-ETF scans
ALTER TABLE quotes SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'ticker'
);

SELECT add_compression_policy('quotes', INTERVAL '7 days', if_not_exists => TRUE);

-- -----------------------------------------------------------------------------
-- 2. daily_summaries
-- Pre-computed aggregates over quotes, one row per (date, ticker).
-- Always recomputable from raw quotes — never the source of truth.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_summaries (
    date              DATE         NOT NULL,
    ticker            TEXT         NOT NULL,
    avg_spread        NUMERIC(10,4),
    min_spread        NUMERIC(10,4),
    max_spread        NUMERIC(10,4),
    volatility_score  NUMERIC(6,4)
);

-- Prevent duplicate summary rows; also used by INSERT ... ON CONFLICT in summarizer.py
ALTER TABLE daily_summaries
    ADD CONSTRAINT daily_summaries_date_ticker_key
    UNIQUE (date, ticker);

-- -----------------------------------------------------------------------------
-- 3. holdings
-- Current share counts per ETF. Updated manually after each payday buy.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS holdings (
    ticker        TEXT          PRIMARY KEY,
    shares        NUMERIC(12,4),
    last_updated  TIMESTAMPTZ   DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 4. transactions
-- Immutable log of every buy. Never deleted.
-- account must be one of the three registered account types.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id                SERIAL       PRIMARY KEY,
    date              DATE         NOT NULL,
    ticker            TEXT         NOT NULL,
    shares            NUMERIC(12,4),
    fill_price        NUMERIC(10,4),  -- actual fill price from Wealthsimple email
    predicted_spread  NUMERIC(10,4),  -- spread from quotes table at fill time
    actual_spread     NUMERIC(10,4),  -- ask - bid from quotes table at fill time
    slippage_vs_mid   NUMERIC(10,4),  -- fill_price - midpoint at fill time
    account           TEXT         CHECK (account IN ('TFSA', 'FHSA', 'RRSP'))
);

-- -----------------------------------------------------------------------------
-- 5. etf_config
-- Target allocation percentages and investor goals per ETF.
-- Seeded below — application reads this instead of hardcoding values.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS etf_config (
    ticker      TEXT         PRIMARY KEY,
    target_pct  NUMERIC(5,2),
    goal        TEXT
);

-- Seed target allocations — INSERT OR IGNORE pattern for idempotency
INSERT INTO etf_config (ticker, target_pct, goal) VALUES
    ('HXQ.TO', 40.0, 'Retirement (TFSA)'),
    ('VFV.TO', 35.0, 'Retirement (TFSA)'),
    ('VCN.TO', 15.0, 'Retirement (TFSA)'),
    ('ZEM.TO', 10.0, 'Retirement (TFSA)')
ON CONFLICT (ticker) DO NOTHING;
