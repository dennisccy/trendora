**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-ops-hardening-iter-36
date: 2026-07-30
reviewer: reviewer
summary: |
  Re-dispatch of iter-35's unbuilt spec: bounds _membership_timeline's candidate-pool bar loading via
  a new _BarCache.load_only() batched-replace method (config-driven batch width, 50), removes
  _compute_coverage_uncached's own eager whole-table prefill wrap, chunks compute_drawdown_expectations'
  stored_by_key ForwardReturn read (config-driven ticker chunk, 50), and wires resolveLabLoadPanel into
  the 4 sibling research labs matching Regime Lab's proven pattern. Verified directly: TypeScript compiles
  clean, config boot-validates both new keys, new unit tests pass, and both bound/byte-identity/mutation
  proofs read soundly against the live seed DB. One pre-existing test failure is honestly disclosed and
  independently confirmed (via git stash) to be a net improvement, not a regression.
spec_alignment:
  definition_of_done: partial
  scope_creep: none
issues:
  - severity: MINOR
    file: apps/backend/tests/test_membership_timeline_batch_bound.py
    line: 197
    category: tests
    summary: TC-2's git-show-HEAD-pinned reference-oracle test only compares _membership_timeline's own
      narrower dict (candidate_pool_count/points/labels), not the full _compute_coverage_uncached payload
      (universe_count, per_symbol, gap_count/gaps_preview) the phase spec's TC-2 and DoD explicitly name.
      _resolved_universe's cache-vs-no-cache resolver path (which now runs standalone) is pre-existing and
      documented-equivalent, and a small-fixture test (test_compute_coverage_exact) plus the dev's live
      /api/data check give reasonable indirect assurance, but no live-basis pinned proof covers the full
      payload as TC-2 literally requires.
    fix: extend the live_comparison fixture (or add a sibling test) to also compare
      _compute_coverage_uncached's/_compute_coverage_body's full return dict (universe_count, per_symbol,
      gap_count, gaps_preview) between the pinned pre-fix reference and the shipped implementation on the
      live seed DB.
  - severity: NOTE
    file: apps/backend/tests/test_bar_cache.py
    line: 424
    category: tests
    summary: test_kdate_backfill_loads_each_symbol_at_most_once still fails post-fix (confirmed live via
      git stash — max load count per symbol 11 pre-fix vs 10 post-fix on this host, typical-case 3→2 as
      the dev handoff states); this iteration reduces but does not eliminate the pre-existing redundancy,
      and is explicitly disclosed in the dev handoff and perf-budgets.md as a non-blocking follow-up.
    fix: no action required this iteration; keep the disclosed follow-up ledger item for
      _persist_per_date_coverage_snapshots' own separate whole-table prefill.
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
