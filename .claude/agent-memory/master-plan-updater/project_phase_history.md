---
name: Phase completion history and schema deviations
description: Tracks which phases are confirmed complete in git, known schema deviations from the plan, and untracked files found on disk
type: project
---

Phase 1 (Foundation) — confirmed complete in git. Commits: d9c055a ("phase1: complete foundation layer"), ecbfdc4 ("update master plan and added settings and schema files"). Files: settings.py, schema.sql, database.py, main.py skeleton.

Phase 2 (Ingestion) — confirmed complete in git. Commits: 5c3a6d1 ("built fetcher.py and add price to database"), 053ab80 ("finish phase 2"). Files: fetcher.py, validator.py, scheduler.py, test_validator.py. Note: schema.sql was also modified in 5c3a6d1 to add a `price` column to the quotes table.

Phase 3 (Storage) — in progress as of 2026-03-14. summarizer.py exists on disk and has been executed (pycache present) but is NOT committed to git. database.py and schema.sql are committed.

**Why:** User confirmed phases 1-3 as complete with key implementation details, but git evidence only supports 1 and 2 as fully committed. Phase 3 requires a commit of summarizer.py before it can be marked complete.

**How to apply:** Do not mark Phase 3 complete until summarizer.py appears in a git commit. Prompt the user to commit it if they ask why Phase 3 is still "In progress".

Known schema deviations (user-reported, not yet updated in plan protected sections):
- quotes table has a `price` column added in Phase 2 (visible in git commit 5c3a6d1)
- transactions table: `price_paid` replaced by `fill_price`, `predicted_spread`, `actual_spread`, `slippage_vs_mid`
- TARGET_ALLOCATIONS in settings.py: HXQ=40%, VFV=35% (plan document and CLAUDE.md still show HXQ=35%, VFV=40%) — awaiting user confirmation of which is authoritative

validator.py uses relative spread threshold: (ask-bid)/price > 2% rejects the quote.
scheduler.py auto-triggers compute_daily_summary at 16:01 ET via APScheduler cron.
