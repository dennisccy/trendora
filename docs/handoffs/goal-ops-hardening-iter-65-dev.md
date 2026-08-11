# goal-ops-hardening-iter-65 Dev Handoff

**Phase:** goal-ops-hardening-iter-65
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete — investigation performed exactly as scoped; no product-code change was warranted by
the evidence (see "What Was Built" and the honest framing in "Known Issues"/perf-budgets.md Item Y).

## What Was Built

This iteration's IN SCOPE list asked to (1) re-run iter-52's own interrupt-driven stall-profiling method
against `factor_lab_all_warm` to find a "third" still-unbounded GIL/lock hold, (2) bound whatever it finds,
(3) add an equality test for the bound, (4) re-run the health-poll drill and publish a dated addendum, (5)
confirm `CHAIN_BACKEND_READY_WAIT_S`'s 90s value fired live, and (6) root-cause `/scanner-runs`'s iter-64
contained-error-boundary render. Items 1, 4, 5, 6 were completed. Items 2/3 have **no deliverable this
round** because item 1's own profiling — run at four escalating levels of fidelity, the most rigorous
re-application of iter-52's method since iter-52 itself — found nothing to bound. Full detail, tables, and
the honesty framing are in `reports/perf-budgets.md` **Item Y / Addendum 31** (new, append-only); this
section summarizes.

- **Profiling pass 1 (solo, in-process)** — `runs/goal-ops-hardening-iter-65/evidence-drill/stall_profile.py`:
  `compute_factor_lab_all(session, cfg, as_of=None)` in a worker thread against the real committed DB, a
  probe thread sleeping 0.02s in a loop flagging any wake-up overrun > 0.30s (iter-52's own threshold),
  capturing the worker's stack via `sys._current_frames()` the instant a stall resolves (iter-52's exact
  technique). **558.34s wall-clock, 70,201,933 observations (within 1% of iter-52's own 69,608,603) — 0
  stalls > 0.30s.**
- **Profiling pass 2 (concurrent with the real `/api/health` route)** —
  `stall_profile_concurrent.py`: the same worker thread, plus a second thread calling
  `app.api.health.health()` (the actual route function) once per second on its own dedicated session,
  timing every call. **566.09s compute, 561 real health calls, 0 breaches > 2.0s, worst 1.272s.**
- **Profiling pass 3 (through the real ASGI/uvicorn stack, over real HTTP)** — `scripts/start-backend.sh`
  launched (AG-10 caps live), `GET /api/research/factor-lab?all=true&as_of=2021-03-15` fired (a never-
  cached `as_of`, forcing a genuine MISS on a Starlette-threadpool-dispatched thread — the exact code path
  `factor_lab_all_warm` calls, reachable without a full ingest job), a dedicated external process polling
  the real `/api/health` endpoint at 1 Hz throughout. **276.8s request, 296 real HTTP polls, 0 breaches,
  worst 1.449s.**
- **TC-1 acceptance drill (a real, full live ingest)** — `POST /api/data/jobs` (`backfill`, `2005-06-28`,
  live-verified unsnapshotted with a real SPY bar before dispatch), the same 1 Hz `poll_health.py` prior
  iterations used, reconciled against `logs/backend.log`'s own millisecond-timestamped phase markers.
  **1,057 polls, 1 breach (0.09%), 0 breaches inside `factor_lab_all_warm`'s own 569.03s window** — the
  single breach (2.370s) fell inside the much shorter, earlier `coverage_membership_timeline_refresh`
  phase, unrelated to and out of scope for this iteration.
- **Cross-iteration comparison** (perf-budgets.md Item Y): iter-61 (Addendum 28) was ALSO clean (1 of
  1,078, 0 inside `factor_lab_all_warm`); iter-63 (Addendum 29) and iter-64 (Addendum 30) were elevated (53
  of 983, 59 of 930, ~52-58 inside the phase). This iteration's result (1 of 1,057, 0 inside the phase)
  matches iter-61's clean baseline, not iter-63/64's elevated one — on byte-identical code. A genuine
  uninterruptible C-level hold (like the pre-iter-52 `sorted()`/GC pair) reproduces deterministically under
  controlled profiling regardless of host state, which is exactly what iter-52's own profile demonstrated
  and exactly the opposite of what four independent tests found this round. The most defensible reading,
  given the evidence, is that the residual iter-63/64 breach counts are an INTERMITTENT condition tied to
  transient host/scheduling state (this machine's own documented thermal/scheduling variance history), not
  a fourth still-unbounded call site inside `compute_factor_lab_all`'s chain.
- **TC-4** — `CHAIN_BACKEND_READY_WAIT_S`: `grep -n "CHAIN_BACKEND_READY_WAIT_S:-" scripts/automation/lib/*.sh`
  confirms both sites still read `90` (iter-64's edit, unchanged). The engine's own log
  (`runs/goal-session-ops-hardening/engine.log`) shows the only two live firings of `_wait_for_backend_
  readiness` both print `(max 60s)` at `17:33:58`/`20:22:03` — both are iter-63/64's OWN pipeline runs,
  predating iter-65's fresh shell invocation (`goal-iter-lean.sh` logged `Iteration: goal-ops-hardening-
  iter-65` at `21:38:11`, after iter-64's 60→90 edit landed). Since `common.sh`/`replay-lane.sh` are
  `source`d once at that fresh shell's own startup, the NEXT such log line this iteration's own pipeline
  prints (during review/QA/replay-lane, downstream of this dev dispatch) will read `90` — grounded, but not
  yet directly observed live as of this dispatch (the pipeline is paused waiting on this handoff). The next
  stage should confirm and this item can then close.
- **TC-5** — `/scanner-runs` root-cause: inspected `logs/backend.log` around iter-64's own `J-05-verify.png`
  capture window (`21:04`-`21:09` local BST) — zero ERROR/Exception/Traceback lines, zero non-200
  access-log lines. Reproduction attempted this round: `GET /api/runs` (the exact endpoint
  `apps/frontend/app/scanner-runs/page.tsx`'s `fetchRuns()` reads) called directly against this iteration's
  own freshly-backfilled live backend — HTTP 200, 791,437 bytes, 0.31s, valid JSON, did not recur. Written
  into the ledger per the spec's own "either way" instruction: reproduction attempted, did not recur, no
  backend traceback found either time — plausibly a client-side (React) transient rather than a backend
  fault, not investigated further since `apps/frontend/*` is out of this iteration's scope.

## Files Changed

- `reports/perf-budgets.md` — new `## Item Y` / `### Addendum 31` (append-only; Items S-X and Addenda 1-30
  untouched) — the full profiling methodology, the TC-1/TC-4/TC-5 results, and the honest "no fix made"
  conclusion.
- `runs/goal-ops-hardening-iter-65/evidence-drill/` — every raw artifact behind the numbers above:
  `stall_profile.py`/`.log`/`stall_summary.json` (pass 1), `stall_profile_concurrent.py`/`.log`/
  `stall_profile_concurrent_summary.json` (pass 2), `tc1-preflight-*` (pass 3), `poll_health.py`/
  `tc1-health-poll.csv`/`tc1-job-create.json` (the TC-1 acceptance drill), `dev1.log`/`dev2.log`
  (pre-handoff service-startup verification).
- `docs/handoffs/goal-ops-hardening-iter-65-dev.md` — this file.
- `runs/goal-ops-hardening-iter-65/status.json` — `current_step: dev_complete`.

**No change to `apps/backend/app/engine/research.py`, `data_manager.py`, `config.py`, or any test file** —
confirmed via `git status --porcelain` before writing this handoff. Nothing under `apps/frontend/*` was
touched (matches the spec's own "None" Frontend scope).

## Tests Run

No product code changed, so no NEW test was needed; the following targeted subset was re-run to confirm
the untouched tree is still green (not a formality skipped, since this handoff's whole claim rests on the
code being byte-identical to iter-64's shipped tree):

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_research_streaming.py tests/test_research.py tests/test_factor_lab_all.py -q -p no:randomly`
Result: **233 passed** in 98.05s — includes the existing `_cooperative_sorted`/`_cyclic_gc_paused`
byte-identity tests (iter-52) unmodified and still passing.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_ingest_finalize_fault_injection.py -q -p no:randomly`
Result: **5 passed** in 0.80s.

Command (TC-1 live drill): `curl -X POST http://localhost:8255/api/data/jobs -d '{"kind":"backfill","start":"2005-06-28","end":"2005-06-28"}'` + 1 Hz `GET /api/health` poll for the job's full duration (1,057 polls)
Result: job `status: ok`, 1 snapshot, terminal in 1,033.02s; **1 of 1,057 polls breached the ≤2.0s
ceiling (0.09%), 0 inside `factor_lab_all_warm`**. Full detail: `reports/perf-budgets.md` Item Y /
Addendum 31.

The full 30-year backend suite was NOT run (this project's established convention — ~10-11h; targeted and
downstream-of-diff files only — and doubly unnecessary here since nothing under `apps/backend/app/` diffed).

Service startup (pre-handoff checklist): ran `scripts/dev.sh` twice back-to-back on its default project
ports (8255/3255) — both backend (`GET /api/health` → 200) and frontend (`GET /` → 200) started cleanly
each time (ready within 1s both times), the second launch correctly reaped the first run's leftover
`next dev`/`next-server`/`uvicorn` processes before binding fresh (confirmed via `ps`/`ss` before and
after — no port conflict). Both instances torn down cleanly at the end (`ps`/`ss` confirm no `8255`/`3255`
listeners remain; the unrelated `tapeology` project's own backend/frontend on different ports were left
untouched).

## Known Issues

- **No code fix was made this iteration.** This is the section's most important entry, not a gap to bury:
  the iteration's own IN SCOPE items 2/3 ("bound whatever call site the profile names" / "add a
  fixture-backed equality test proving the bounded call site...") are conditional on the profile naming a
  site. It did not, at four independent, escalating-fidelity levels, including a full real live ingest.
  Reported honestly per the project's own convention (AG-1 / judgment-rubrics: "unknown is a first-class
  answer", never round toward "fixed") rather than inventing a speculative bound with no evidence behind
  it. See perf-budgets.md Item Y for the full argument.
- **TC-1's target journey acceptance number is genuinely ambiguous given the intermittency.** This round's
  drill (1/1,057, 0 in `factor_lab_all_warm`) meets TC-1's literal "0 breaches attributable to
  `factor_lab_all_warm`" bar. But iter-63/64 (unchanged code) measured 52-58 such breaches each. Whether
  J-07 should be scored `passing` off this round's clean number, `partial` off the cross-iteration
  pattern, or something else is an evaluator judgment call this dev pass does not make for it — the spec's
  own NOTES section explicitly reserves that decision ("the evaluator, not this spec, decides whether J-07
  moves off partial").
- **TC-4's live firing is grounded but not yet directly observed** in `engine.log` — the next pipeline
  stage (review/QA/replay-lane) should confirm from its own fresh `Waiting for backend readiness (max Xs)`
  log line and this item can then close.
- **TC-5 did not reproduce, and no backend traceback exists to attribute the iter-64 capture to.** If it
  recurs in a future iteration's own browser-qa pass, the next step would be a frontend-side (React
  DevTools / component stack) investigation, since the backend side is now checked twice with no fault
  found.
- **The intermittency hypothesis (transient host/scheduling load, not code) is not proven, only the most
  evidence-consistent explanation available.** A future iteration wanting to settle it should record
  concurrent host CPU load (the existing hwmon sampler / `host-guard-registry.sh` already collects this)
  alongside the next health-poll drill, to test directly whether elevated-count runs correlate with higher
  concurrent load on the shared 16-core host.
