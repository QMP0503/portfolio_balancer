# Docs-Keeper Agent Memory Index

## Project State
- [project_phase1_complete.md](project_phase1_complete.md) — Phase 1 Foundation is complete as of 2026-03-12; all four files verified
- [project_phase_docs_missing.md](project_phase_docs_missing.md) — As of 2026-03-14, NO PHASE_N_NAME.md files exist on disk; only docs/MASTER_PLAN.md exists

## Canonical Values / Recurring Divergences
- [project_postgres_user.md](project_postgres_user.md) — `.env` uses `POSTGRES_USER=postgres`; all psql verify commands must use `-U postgres`, never `-U quang`
- [project_canonical_values.md](project_canonical_values.md) — Verified schema columns, allocations (HXQ=40/VFV=35), validator threshold (2% relative), scheduler cron (16:01 ET), summarizer behavior
