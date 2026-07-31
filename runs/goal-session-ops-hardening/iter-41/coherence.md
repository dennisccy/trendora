# Iteration 41 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-41
**Date:** 2026-07-31
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

This iteration touches two already-registered rows (Coverage payload; Job history & per-date exclusion
reasons) and adds one opt-in diagnostic (no served value). No new displayed value, no new endpoint.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Coverage payload (universe counts, per-symbol coverage, gaps, capacity) | OK | `apps/backend/app/engine/prices.py:58-121` (new `_SymbolColumns` class) + `apps/backend/app/engine/prices.py:220-247` (`_BarCache.prefill` accumulator rewrite). Still the SAME canonical computing module (`app.engine.data_manager._compute_coverage_uncached`) and SAME endpoint (`GET /api/data`) — this only changes `_BarCache.prefill`'s resident storage shape (per-symbol `array.array('d')` columns instead of a `list[Bar]`), publishing values through `Sequence.__getitem__`/`__len__` so every existing consumer (`bars_asof`, `bars_asof_window`, `bars_after`, `close_on`) reads it via the same `full[:cut]`/`full[cut-1]`/`len(full)` operations, unchanged. Byte-identity is proven, not merely asserted: `apps/backend/tests/test_bar_cache.py:99-146` reimplements the OLD `list[Bar]` accumulation as a reference oracle (`_old_prefill_by_symbol`) and asserts every symbol/date's `Bar` tuple is identical, and every synthesized element is a real `Bar` NamedTuple (not a lookalike). No second producer, no schema change. |
| Job history & per-date exclusion reasons | OK | `apps/backend/app/engine/data_manager.py:2082-2088` (new unserialized `JobProgress._dates_since_checkpoint` scratch field) + `data_manager.py:4094-4104,4118-4134` (`_checkpoint_run_record` count-based floor). Still writes only the existing `message` field via the SAME `_run_detail()` serializer every other Job history field uses — this only widens *when* a checkpoint fires (time-based OR count-based), never what gets written or read. No new field, no second endpoint. |
| (diagnostic, not a Data Contract value) `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1` | OK — not a served value | `apps/backend/main.py:54-68`. Opt-in, default-off `faulthandler.register(SIGUSR1, ...)` for the throwaway wedge-drill; not displayed anywhere, no endpoint. Matches the iter-18/23 "pipeline/diagnostic artifact, not a served/displayed value" precedent already established in the blueprint. |

No new UI surface was added this iteration (`git diff --stat` against the snapshot SHA shows zero files
under `apps/frontend/`, confirmed independently by `reports/phase-goal-ops-hardening-iter-41-ui-surface-map.md`'s
"Frontend surfaces changed: 0"), so Part A.2 (non-canonical source in a new UI surface) does not apply.
The `incredible_auto_dev/scripts/automation/**` and `incredible_auto_dev/agents/ui-test-designer/**`
changes (health-URL resolution fix, `ui-test-designer` regression-test carve-out, `merge_ui_test_results.py`
all-SKIP detection, `BLOCKED` verdict plumbing) are this project's own AI-dev-pipeline tooling — not
Trendora product code, no Trendora UI surface, no Data Contract row, per the blueprint's own iter-18/23
precedent ("a pipeline/test artifact is not a served/displayed value").

## Information Architecture check

No new page/route/feature this iteration — the iteration spec's own "Blueprint conformance" and "UI
surface changes: None" fields, and the ui-surface-map's "New pages/routes: 0" / "Navigation changes: no",
are all consistent with the diff (zero `apps/frontend/` files touched).

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new surface this iteration) | OK | Not applicable; `git diff --stat` confirms zero frontend files changed. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. The iteration is a clean, narrowly-scoped memory-bound fix plus pipeline/verification-lane
  tooling, exactly matching its own blueprint narrative — no drift observed.
