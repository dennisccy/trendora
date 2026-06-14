# Iteration 15 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

J-68 (multi-month / full-history backfill no longer crashes with the `'committed'`-session error — fixed at the source via a fresh per-date write session the orchestrator owns) and J-69 (removing imported data is now range-scoped and accident-proof — no symbols input, both dates mandatory, counts-only confirm modal with an always-visible Confirm button) both ship and pass with positive, independently-verified evidence. No regression, no anti-goal violation, coherence COHERENCE-PASS. This is NOT GOAL_ACHIEVED because J-70 and J-71 — two Must-have journeys appended to `docs/goal.md` (commit `aefc120`) — were explicitly deferred to iter-16 and are not yet built.

## Independent verification performed (evidence was partly degraded — did not trust summaries)

- **Targeted/regression pytest re-run by the evaluator (79 tests, 0 failures):**
  - `test_data_manager_backfill_committed_session.py` (J-68) + `test_api_data_remove_range.py` (J-69) = **19 passed** (173s).
  - `test_data_manager_backfill_parallel.py` + `test_data_manager_parallel.py` + `test_data_manager_jobs_pipeline.py` (J-53/J-67/J-41/J-59) = **31 passed** (174s).
  - `test_scanner.py` + `test_no_magic_numbers.py` + `test_data_manager.py -k "remov/scope/seed/cascade/refus/immutab/lookahead/magic/create_once/idempot"` = **29 passed** (337s).
- **Live backend (port 8835) J-69 endpoint:** `{start}` only → **HTTP 400** ("a date range removal requires BOTH a start and an end date…"); `{}` → **HTTP 400**; valid `{start,end}` (no `symbols`) → **HTTP 200** with `removable_bar_count=10`, `removable_symbol_count=1` (DIA user-added), `not_removable_bar_count=1580` (committed seed protected).
- **Diff review:** J-68 per-date `Session(eng)` with shared cache attached, shared session never rolled back after commit, `_cleanup_orphan_run` only drops a run THIS call created (`if not existed_before` — immutability preserved). J-69 `require_range` threaded through validate/plan/preview/remove; frontend `symbolsText` state + input removed, both dates mandatory, `buildScope` sends `{start,end}` only, modal counts-only with `max-h-[55vh] overflow-y-auto` body + footer outside the scroll region.
- **Schema trap (iter-12) check:** `models.py` and `db.py` confirmed untouched (git status clean for both).
- **Full pytest suite (handed to the pump, `nohup`):** in-flight at evaluation time (~17%, 0 failures); per project memory + the iter-15 spec, the evaluator does NOT block on it. The 79 targeted+regression tests above are the binding proof.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-68 (multi-month backfill no 'committed' crash) | new | **passing** | `apps/backend/tests/test_data_manager_backfill_committed_session.py` (6 of 19 passed, evaluator re-ran); browser-QA UT-13 (`reports/qa/.../iter-15-evidence/UT-13-run-history.png`) |
| J-69 (range-only accident-proof removal) | new | **passing** | live backend (400/400/200); `test_api_data_remove_range.py` (13 of 19 passed); `reports/qa/.../iter-15-evidence/UT-01-result.png` (real /data page + Remove panel) |
| J-39 (seed-safe removal, amended by J-69) | already_passing | **passing** (upgraded, live-verified) | live `/api/data/remove/preview` seed-protected counts |
| J-08 (immutable scanner-run history) | already_passing | passing (re-confirmed) | scanner immutability tests green (29 passed) |
| J-17 (grow dataset by date/range) | passing | passing (re-confirmed) | browser-QA UT-13 backfill → `ok`; jobs-pipeline green |
| J-41 (create-once / idempotency / concurrency) | already_passing | passing (re-confirmed) | J-68 re-run create-once assertion; 31 passed |
| J-53 (parallel multi-date backfill + stage timings) | passing | passing (re-confirmed) | parallel byte-identity tests green (31 passed) |
| J-59 (stage-resume / covered-range) | passing | passing (re-confirmed) | jobs-pipeline green (31 passed) |
| J-60 (run-history from start) | passing | passing (re-confirmed) | browser-QA UT-13 running→ok lifecycle |
| J-61 (availability heatmap reads /api/data/availability) | passing | passing (re-confirmed) | browser-QA UT-15; evaluator-viewed UT-01-result.png grid |
| J-66 (honest fine-grained progress) | passing | passing (re-confirmed) | J-68 forced-failure → honest `partial`; suites green |
| J-67 (transactionally-sound parallel backfill) | passing | passing (HARDENED by J-68) | parallel failure-isolation + byte-identity (31 passed) |
| J-42 (ISO dates everywhere) | passing | passing (re-confirmed) | shared `fmtDate` in modal; UT-06 invalid-date gating |
| J-13 / J-18 (single global as-of state) | passing | passing (re-confirmed) | remove dates are action params (coherence IA check) |
| J-70 (heatmap readable/compact) | new | **unknown — not yet built** | deferred to iter-16 per iter-15 spec OUT OF SCOPE |
| J-71 (as-of calendar keyboard stepping) | new | **unknown — not yet built** | deferred to iter-16 per iter-15 spec OUT OF SCOPE |

All other J-01..J-67 journeys carried forward unchanged (not in iter-15 scope; code paths untouched). J-22/J-23/J-24 remain blocked-NA (data-walled, non-vetoing).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead (critical) | OK | scanner no-lookahead tests green (29 passed); J-68 forward-return INSERT stays bars > D |
| Snapshots immutable (critical) | OK | `_cleanup_orphan_run` only drops a run THIS call created (`if not existed_before`); pre-existing committed snapshots untouched (coherence advisory note); immutability tests green |
| Single source of truth (critical) | OK | canonical scan/forward outputs byte-identical (parallel==sequential test green); no recompute/second endpoint (coherence Data Contract check) |
| No magic numbers | OK | J-68 added `Session(eng)` + `attach_shared_cache` (no new threshold literal); `test_no_magic_numbers.py` green |
| No fabricated data | OK | removal impact counts single-sourced from `_build_removal_plan` (live-verified); a failed date leaves NO fabricated snapshot |
| Exactly one date selector (critical) | OK | J-69 remove dates are ACTION parameters (PanelTitle hint + `RemoveScope` docstring + coherence IA check); no second date state |
| No order/execution path (critical) | OK | none added; Data Manager only |
| No secrets in source | OK | no credentials/keys in diff |
| Risk-Off gates Actionable (critical) | OK | scoring untouched; scanner tests green |
| Scores explainable | OK | scoring/UI score surfaces untouched |
| Honest limitations surfaced | OK | seed-protected counts + honest `partial` terminal state |

## Next-Step Recommendation

Run **iter-16 as lean** to build the two deferred Must-haves:
- **J-70** — `availability-heatmap.tsx`: legible day-number contrast across density buckets 0–5 (use existing design tokens, no hardcoded hex), descending month order (newest first), two-up-per-row layout at standard width (collapsing to one column on narrow screens). Still reads `GET /api/data/availability` (descriptive-only, no canonical recompute).
- **J-71** — `asof-calendar.tsx`: `onKeyDown` ArrowLeft/ArrowRight stepping among snapshot dates only, bounded at oldest/newest, driving the single global as-of via the existing dialog handler — **no global window listener, no second date state** (the J-18 "exactly one date selector" critical anti-goal must hold).

Both are pure frontend on the committed seed (NOT data-dependent). Verify with browser-QA + `tsc --noEmit`. **Evidence hygiene:** instruct browser-QA to md5sum the evidence dir first and re-capture any blank/byte-identical close-ups at full viewport (iter-15 produced a cluster of blank 6830-byte modal/button captures). After J-70 + J-71 pass, the appended J-68..J-71 scope is complete and the next evaluation should reach GOAL_ACHIEVED.

## Halt Justification (if halting)

Not halting. Progress was made (J-68, J-69 newly passing; J-39 upgraded), no regression, no anti-goal violation, coherence PASS — but two Must-have journeys (J-70, J-71) remain unbuilt and tractable, so the goal is not yet achieved. CONTINUE.
