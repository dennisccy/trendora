**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-i_can_see_the_wealthy_future_forever-iter-6
date: 2026-06-02
reviewer: reviewer
summary: |
  J-20 (display-only chart full-path through latest) and J-21 (Backtest leadership cohorts
  below Return Attribution with horizon-linked realized returns) are implemented additively —
  no new endpoint, no new canonical value, no nav change. Both critical anti-goal seams hold in
  source and are guarded by tight new tests. Two non-blocking notes only; shippable.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: NOTE
    file: apps/backend/app/engine/forward_testing.py
    line: 503
    category: spec
    summary: Cohort projection iterates cfg.universe.symbols, not the plan's literal "stored ScannerResult tickers".
    fix: None required — frontend joins by ticker so values are identical (symbol's own stored return); the complete-keyed projection avoids a row-count literal and needs no Session/query. Documented in handoff.
  - severity: NOTE
    file: apps/backend/tests/test_bars.py
    line: 196
    category: tests
    summary: No-lookahead "scores/VCP unchanged" is proven structurally (bars_asof invariance + source-seam) rather than by a direct score_stocks before/after call.
    fix: None required — the two structural proofs are equivalent (and arguably stronger); an explicit score_stocks before/after assert would only add redundancy.
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  ui_evolved_with_capability: pass
  navigation_updated: n/a
  architecture_principles: pass
```

Notes (non-blocking):
- **No-lookahead (J-20) verified:** `bars_through_latest` is referenced only by the chart endpoint (grep + `test_bars_through_latest_not_in_scoring_path_source_seam`); `sma_series` is purely trailing (`sma(values[:i+1], period)`), so `test_bars_through_latest_ma_le_d_region_matches_default` confirms ≤D MA is byte-identical with/without the forward extension; the default `/bars` contract stays ≤D and byte-identical.
- **Attribution-read-only (J-21) verified:** `_leadership_returns` takes no Session, issues no query, recomputes no return — pure projection of the same `ret_by_symbol` the scorecard built from stored `forward_returns`; the keystone test monkeypatches `forward_return` to raise and the projection still serves from storage. Honest null/NA on unobserved (row, horizon).
- **Exactly-one-date-selector (J-18) preserved:** the lifted `viewHorizon` is a VIEW selector (no refetch/date param/date state); one `HorizonViewSelector` re-points attribution + all three leadership return columns via the single `selected` row; global as-of switcher still owns the date.
- Backtest section order matches spec (scan summary → scorecard → Return Attribution → the three lists); returns join by stable keys with honest NA via the existing `<Return>`; palette tokens only on the chart; blueprint updated additively with no nav-skeleton change.
- Test execution is QA's gate; handoff reports 42 passed (3 targeted files) + 312 passed/1 skipped (full suite, offline integration skip). New-test logic reviewed and sound.
