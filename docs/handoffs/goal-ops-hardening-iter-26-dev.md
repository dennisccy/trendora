# goal-ops-hardening-iter-26 Dev Handoff

**Phase:** goal-ops-hardening-iter-26
**Date:** 2026-07-26
**Agent:** developer
**Status:** complete

## What Was Built

This iteration closes the two named gaps the iter-25 GOAL_ACHIEVED second-key CONFIRM run rejected on
(`runs/goal-session-ops-hardening/iter-25/eval-confirm.md`). No product-code change; no new Data Contract
value; no new user-facing capability (per the spec's own "New user-facing capability: None").

- **Gap 1 — the ambiguous `<= 0.1 s` health-budget re-measurement.** Took one fresh quiet-host
  `GET /api/health` re-measurement (official single sample + a 10-sample, 0.5 s-spaced series — same
  convention as iter-24) and recorded it in a NEW dated section of `reports/perf-budgets.md` ("Iteration
  26 — J-09 confirm-gap 1..."). All prior sections (including the OWNER BUDGET AMENDMENT + its Revision 1)
  are byte-unchanged — verified via `git diff --stat` (70 insertions, 0 deletions). **Result: all 4
  statistics hold cleanly** (official 0.092222 s, min 0.087875 s, mean 0.092081 s, max 0.094309 s — all
  `<= 0.1 s`), the opposite pattern from iter-24's mixed read (3 of 4 over budget). The new section states
  in plain prose that this iteration's reading is now the CURRENT BINDING figure for J-09's Acceptance
  clause, superseding iter-24's for scoring purposes, and frames the two-iteration split as host-noise
  variance on an already-documented near-ceiling endpoint (~98.6% of budget at rest since iter-16) — not a
  regression either iteration introduced.
- **Gap 2 — the unexercised "failed background compute" disclosure branch.** Added one new backend test,
  `test_health_background_compute_serves_failed_outcome_verbatim`
  (`apps/backend/tests/test_health.py`), that monkeypatches
  `app.engine.forward_testing.get_background_compute_status` to return a crafted `failed` outcome (with a
  non-null `reason`) and asserts `GET /api/health`'s `background_compute.recent_outcomes[0]` equals the
  crafted dict verbatim, field-for-field. Ran it in the SAME combined pytest invocation as the two
  previously-stalled tests (see "Tests Run" below) so the session-scoped `loaded_engine` fixture builds
  once, not three times.
- **Frontend refactor (byte-identical, no behavior change).** Extracted the completed/failed rendering
  decision that was inline in `LastOutcomeSummary` (`apps/frontend/app/data/page.tsx`) into one new pure
  function, `resolveLastOutcomeSummary` (`apps/frontend/lib/background-compute-last-outcome.ts`), returning
  `{ reasonText: string | null; badgeVariant: "ok" | "danger" }`. `LastOutcomeSummary` now calls it instead
  of its own inline ternaries — the rendered JSX is unchanged for the existing `completed` case (verified
  by direct diff read: `Badge variant={badgeVariant}` replaces `Badge variant={failed ? "danger" : "ok"}`,
  `{reasonText ? ... : null}` replaces `{failed ? ... : null}`, same conditional/value shape).

## Files Changed

- `apps/backend/tests/test_health.py` -- added `test_health_background_compute_serves_failed_outcome_verbatim` (TC-4)
- `apps/frontend/lib/background-compute-last-outcome.ts` -- new file, exports `resolveLastOutcomeSummary` (TC-5)
- `apps/frontend/lib/background-compute-last-outcome.test.ts` -- new file, covers `completed`/`failed` cases (TC-5)
- `apps/frontend/app/data/page.tsx` -- `LastOutcomeSummary` now calls the extracted function (refactor only)
- `reports/perf-budgets.md` -- new dated section "Iteration 26 — J-09 confirm-gap 1..." (append-only; all
  prior sections byte-unchanged)

Also see `docs/handoffs/goal-ops-hardening-iter-26-frontend.md` for the frontend-focused summary.

## Tests Run

**Coordinator note followed:** two stale detached pytest processes from the iter-25 reviewer (PID
1620313 / 1620524, ~73 min in with no pass/fail line, the same two selectors this iteration needed) were
terminated (`kill 1620313 1620524`, confirmed gone via `ps`) before launching a fresh combined run, per the
dispatch instructions — never adding a third concurrent `loaded_engine` build.

**Command (combined invocation — TC-3/TC-4):**
```
cd apps/backend && .venv/bin/python -m pytest tests/test_health.py tests/test_readiness.py \
  -k "test_health_background_compute_is_single_source or test_health_background_compute_serves_failed_outcome_verbatim or test_compute_readiness_composes_background_compute_empty_shape" \
  -v
```
Launched via `setsid nohup ... &` from a foreground shell (per the dispatch note that backgrounded/long
commands get reaped otherwise) and polled to completion without ending the turn.

**Result:**
```
tests/test_health.py::test_health_background_compute_is_single_source PASSED [ 33%]
tests/test_health.py::test_health_background_compute_serves_failed_outcome_verbatim PASSED [ 66%]
tests/test_readiness.py::test_compute_readiness_composes_background_compute_empty_shape PASSED [100%]

================ 3 passed, 41 deselected in 5151.48s (1:25:51) =================
```
The `loaded_engine` session-scoped fixture build took the bulk of that wall time (single build, shared
across all 3 selected tests, one process — no contention this time); CPU stayed pegged near 100% the
whole run with steadily-plateauing RSS (~722 MB peak), consistent with legitimate 30-year-history compute,
not a hang. `free -h`/`ps` were checked periodically; no swap pressure, no OOM.

**Frontend (TC-5/TC-6):** this dev box's Node build (`v22.22.1`) lacks type-stripping (`amaro`), so
`node lib/*.test.ts` fails with `ERR_UNKNOWN_FILE_EXTENSION` — the SAME pre-existing, documented limitation
noted in `lib/background-compute-last-outcome.test.ts`'s own header comment and in prior handoffs
(`docs/handoffs/*iter-49-dev.md`). Verified instead via `npx tsx`, which IS available on this box:
```
cd apps/frontend && npx --no-install tsx lib/background-compute-last-outcome.test.ts
  ok - a completed outcome resolves to reasonText null and badgeVariant ok (TC-5, existing case)
  ok - a failed outcome resolves to reasonText equal to the exact reason string and badgeVariant danger (TC-5)
2 passed
```
Sibling `lib/background-compute-panel-branch.test.ts` re-run the same way for regression sanity: 8/8
passed, unchanged. `npx tsc --noEmit -p tsconfig.json`: zero errors (whole-project type-check, touched
files included).

**TC-8 (byte-frozen module check):** `git diff --stat -- apps/backend/app/` is empty — zero lines changed
anywhere under `apps/backend/app/**` (only `apps/backend/tests/test_health.py` was touched on the backend
side). Full diff stat: `test_health.py` (+30), `page.tsx` (+4/-3, refactor only),
`reports/perf-budgets.md` (+70/-0). `app.engine.forward_testing`, `compute_readiness`,
`compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, and J-08's serving split are all
untouched, confirming the binding "Do not redo" held.

## Pre-Handoff Verification

- **Service startup (first boot):** `scripts/start-backend.sh` (port 8255, host-guard confirmed active in
  `logs/backend.log`: `cpu_list=0-3,8-11 blas_threads=4`) warmed to `readiness: "ready"` (`89/89`) with no
  errors. Used this SAME boot for the quiet-host `/api/health` re-measurement (see perf-budgets.md), then
  additionally started `scripts/start-frontend.sh` (port 3255, `next dev`, "Ready in 1208ms") and confirmed
  `GET /data` returns 200 and compiles cleanly (`Compiled /data in 1874ms (765 modules)`, no errors in the
  frontend log).
- **Stop -> restart -> verify no port conflicts:** both services killed (confirmed via `ps`/curl 000 on
  both ports), then started again from a cold shell. Both came up cleanly a second time (backend
  `readiness: ready` within ~10 s of poll, frontend "Ready" immediately) — no port-in-use errors, no
  leftover child process blocking the retry. Both stopped again at the end of the session; final `ps aux`
  check shows no `uvicorn`/`next dev`/`next-server`/`npm exec` process remaining.
- **No native-dependency/external-integration changes this iteration** — nothing applicable to check
  beyond the above.

## Known Issues

- **Full browser regression capture (TC-6/TC-7) not run by this developer pass.** The frontend change is a
  pure logic extraction proven byte-identical by direct diff inspection (same JSX shape, same
  conditional/value semantics) plus a passing unit test for both the `completed` and `failed` cases; I did
  not drive a Chrome-based capture of the idle/active/unknown panel states or the 7 required-still-passing
  journeys myself — that is left to the downstream QA/browser-qa step, consistent with how this pipeline
  splits developer vs. QA responsibilities. I did confirm `GET /data` renders 200 with no compile/console
  errors on a fresh boot (see above), and `tsc --noEmit` is clean project-wide.
- **A second, unrelated project's pytest job was observed running on this shared host** partway through
  the wait for the combined TC-3/TC-4 run (a `tapeology` project's full-suite audit run, different repo,
  different session/agent). It had exited before the quiet-host health measurement was taken (confirmed
  via `ps aux` immediately before measuring — zero pytest processes anywhere, load average 0.63/1.04/1.27).
  Noting it here for transparency since it briefly shared host CPU/memory with this iteration's own pytest
  run, though it never overlapped with the measurement itself.
- Everything else the iter-26 spec places OUT OF SCOPE was left untouched, as directed (B-1107, the
  OWNER BUDGET AMENDMENT/Revision 1/TC-13/TC-14 sections, the demo-steps JSON, the panel's idle/active/
  unknown branch logic, the dangling imports at `backtest.py:75`/`mcp/tools.py:38`).
