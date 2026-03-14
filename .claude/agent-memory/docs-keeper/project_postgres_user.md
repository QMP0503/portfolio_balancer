---
name: Canonical POSTGRES_USER value
description: The .env file sets POSTGRES_USER=postgres, not quang — any psql verify commands must use -U postgres
type: project
---

The `.env` at `etf-intelligence/.env` sets `POSTGRES_USER=postgres`. The `settings.py` fallback also defaults to `postgres`.

**Why:** Early doc drafts used `-U quang` in all psql verify commands, which would fail because the actual DB user is `postgres`.

**How to apply:** Any verify command in a phase doc that calls `psql` must use `-U postgres`. Flag `-U quang` as a divergence immediately.
