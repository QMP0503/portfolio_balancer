---
name: Phase completion history and schema deviations
description: Tracks which phases are confirmed complete in git, known schema deviations from the plan, and untracked files found on disk
type: project
---

Phase 1 (Foundation) — confirmed complete. Commits: d9c055a, ecbfdc4. Files: settings.py, schema.sql, database.py, main.py skeleton.

Phase 2 (Ingestion) — confirmed complete. Commits: 5c3a6d1, 053ab80. Files: fetcher.py, validator.py, scheduler.py, test_validator.py. Note: schema.sql modified in 5c3a6d1 to add `price` column to quotes table.

Phase 3 (Storage) — confirmed complete by user. summarizer.py was untracked as of 2026-03-14 but user confirmed phase complete; traceability gap noted in Agent Notes of MASTER_PLAN.md.

Phase 4 (Rebalancer) — confirmed complete. Commits: 47e0f9f, d5d6913. Post-completion bug fix in 5866ae4: rebalancer now shows all 4 tickers, greedy-fills leftover cash, correct post-buy percentages.

Phase 5 (API) — confirmed complete. JWT httpOnly cookies, 6 routers, 36 tests. Schema refactor: etf_config → per-user portfolios + portfolio_allocations. storage/ split into one file per domain. Commits: e996e9a, 214fa1b, c271863, abaaff5.

Phase 6 (Frontend) — confirmed complete 2026-03-21. Commits: bbdccad through 5866ae4 (phase6 prefix). Components: Login, Register, Dashboard, Allocation (Recharts), BuyRecommendation, ExecutionTiming, AddPortfolioModal (3-step), Settings. Docker service added in c71dcb5.

Phase 8 (Deploy) — in progress as of 2026-03-23. Commits: 75feca6 (/api prefix), a3e0a86 (nginx, Dockerfile, prod compose), 437d544 (Prometheus metrics), 6d54473 (Grafana provisioning), 1a2b2c2 (fix docker grafana). Not yet confirmed live on Linux server. README not yet written.

Phase 7 (Analysis) — deferred. Needs weeks of collected data.
Phase 6.5 (Gmail parser) — deferred. Requires Gmail API OAuth setup.
Phase 6.6 (Setup wizard) — deferred. Build after deploy.
Phase 9 (C++ Simulator) — not started. Shopify internship timeline.

Known schema deviations (user-reported, protected sections not yet updated):
- quotes table has a `price` column added in Phase 2 (visible in git commit 5c3a6d1)
- transactions table: `price_paid` replaced by `fill_price`, `predicted_spread`, `actual_spread`, `slippage_vs_mid`
- TARGET_ALLOCATIONS in settings.py: HXQ=40%, VFV=35% (plan document and CLAUDE.md still show HXQ=35%, VFV=40%) — awaiting user confirmation of which is authoritative

validator.py uses relative spread threshold: (ask-bid)/price > 2% rejects the quote.
scheduler.py auto-triggers compute_daily_summary at 16:01 ET via APScheduler cron.

**Why:** Tracking phase completion state across sessions so the agent does not re-litigate what is already confirmed done.

**How to apply:** Use as baseline when a new session asks about current project state. Verify against git log before relying on this — git is always authoritative.
