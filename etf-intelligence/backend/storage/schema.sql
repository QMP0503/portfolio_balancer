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
-- 3. users
-- Authentication table. Multi-user ready.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id               SERIAL       PRIMARY KEY,
    email            TEXT         NOT NULL UNIQUE,
    first_name       TEXT         NOT NULL,
    last_name        TEXT         NOT NULL,
    hashed_password  TEXT         NOT NULL,
    is_active        BOOLEAN      DEFAULT TRUE,
    role             TEXT         DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    created_at       TIMESTAMPTZ  DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 4. portfolios
-- One row per account (TFSA, FHSA, RRSP, or any custom name).
-- A user can have multiple portfolios. account_name is free text — the UI
-- offers standard options (TFSA, FHSA, RRSP, Non-registered, Other).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS portfolios (
    id           SERIAL       PRIMARY KEY,
    user_id      INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_name TEXT         NOT NULL,
    created_at   TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (user_id, account_name)
);

-- -----------------------------------------------------------------------------
-- 5. portfolio_allocations
-- Target allocation % per ETF per portfolio.
-- Replaces the old etf_config table — allocations are now per-user per-account.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS portfolio_allocations (
    id           SERIAL        PRIMARY KEY,
    portfolio_id INTEGER       NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    ticker       TEXT          NOT NULL,
    target_pct   NUMERIC(5,2)  NOT NULL CHECK (target_pct > 0 AND target_pct <= 100),
    goal         TEXT,
    UNIQUE (portfolio_id, ticker)
);

-- -----------------------------------------------------------------------------
-- 6. holdings
-- Current share counts per ETF per portfolio.
-- Updated manually after each payday buy.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS holdings (
    portfolio_id  INTEGER       NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    ticker        TEXT          NOT NULL,
    shares        NUMERIC(12,4) NOT NULL DEFAULT 0,
    last_updated  TIMESTAMPTZ   DEFAULT NOW(),
    PRIMARY KEY (portfolio_id, ticker)
);

-- -----------------------------------------------------------------------------
-- 7. transactions
-- Immutable log of every buy. Never deleted.
-- Linked to a portfolio so account type is derived from portfolios.account_name.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id                SERIAL        PRIMARY KEY,
    portfolio_id      INTEGER       NOT NULL REFERENCES portfolios(id),
    date              DATE          NOT NULL,
    ticker            TEXT          NOT NULL,
    shares            NUMERIC(12,4),
    fill_price        NUMERIC(10,4),  -- actual fill price from Wealthsimple email
    predicted_spread  NUMERIC(10,4),  -- spread from quotes table at fill time
    actual_spread     NUMERIC(10,4),  -- ask - bid from quotes table at fill time
    slippage_vs_mid   NUMERIC(10,4)   -- fill_price - midpoint at fill time
);
