**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-mcp-loop-iter-40
date: 2026-07-15
reviewer: reviewer
summary: |
  Implements J-24/B-201's risk-budget card + leaderboard columns correctly. Two new pure functions
  (overnight_gap_profile, worst_20d_window) in indicators.py; scoring.py pass-3 computes the bundle
  once, correctly REUSES atr_pct/downside_vol (verified by call-count test), reframes
  distance-to-invalidation from the existing level (NA-safe on null level), and adds an 8-leaf
  cross-sectional percentile pass, all additive and score-invariant (verified). Frontend card +
  5 leaderboard columns single-source the same served field via a shared formatter. Independently
  re-ran: fast lanes (162 passed), sectors/themes/indexes subset (20 passed), tsc (0 errors), and
  the full test_scoring_window.py byte-identity harness (4 passed, 533s, real seed) — all green,
  confirming no regression and no window-config-dependent instability in the new fields.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: MINOR
    file: docs/handoffs/goal-mcp-loop-iter-40-dev.md
    line: 182
    category: backend
    summary: trendora.db was not rebuilt this session, so served snapshots (bootstrap+latest) still lack risk_budget until regenerated
    fix: before browser-qa, rm -f apps/backend/data/trendora.db* , start the backend, poll /api/health, confirm GET /api/stocks/AAPL carries non-null risk_budget
  - severity: MINOR
    file: apps/backend/tests/test_scoring.py
    line: 493
    category: tests
    summary: the 6 new risk-budget tests (loaded_engine fixture) were not pytest-executed this session or by dev — corroborated by dev's real-seed standalone script and by my independent full run of test_scoring_window.py's byte-identity harness (same score_stocks code path, real seed, all green) but not pytest-certified
    fix: run `pytest tests/test_scoring.py -k risk_budget -v` to completion in the next lean pass for final certification
  - severity: NOTE
    file: apps/frontend/app/stocks/[ticker]/page.tsx
    line: 305
    category: ui
    summary: generic "NA — insufficient history" copy also covers the rare zero-total-variance case for overnight_variance_share, whose real cause is an undefined ratio, not short history
    fix: optional — a distinct message for that edge case if ever revisited
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  ui_evolved_with_capability: pass
  navigation_updated: n/a
  architecture_principles: pass
```
