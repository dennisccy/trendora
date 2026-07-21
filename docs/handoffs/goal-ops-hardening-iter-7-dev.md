# goal-ops-hardening-iter-7 Dev Handoff

**Phase:** goal-ops-hardening-iter-7
**Date:** 2026-07-21
**Agent:** developer
**Status:** complete

## What Was Built

- **`drawdown_expectations` ingest-time warm** — `_refresh_ingest_aggregates` (`app.engine.data_manager`)
  gained one more non-fatal warm step, placed after the existing `research_hot_keys` block, that closes
  J-06's last residual gap (audit B1, iter-6): `/evidence`'s per-claim `drawdown_expectations` panel used
  to pay a lazy cold-miss compute on the FIRST live `/evidence` request after any ingest (measured 73.3s
  on the grown live dev DB). It now warms at ingest time instead:
  1. Resolves the certified-claims ledger via `evidence.resolve_ledger_path()` + `read_entries()`.
  2. Applies the SAME `type == FORWARD_WALK_TYPE` filter `build_evidence_payload` already applies (a
     forward-walk monitoring record re-scores an existing claim; it is not itself a claim to warm).
  3. For each remaining claim, extracts the claim dict the SAME way `evidence._claim_row` does
     (`entry.get("claim")` if it's a dict, else `{}`), and calls the EXISTING
     `forward_testing.compute_drawdown_expectations_cached(session, claim, cfg)` — the SAME function
     `GET /api/evidence` already calls lazily. No new table, no new endpoint, no new computing module.
  4. A `prog.tick()` heartbeat stamps before each claim's warm call (mirrors the `forward_aggregates`
     per-horizon tick already in this function).
  5. Each claim's warm call runs inside its own try/except (log + continue) — one unresolvable or
     erroring claim never blocks another or fails the ingest job.
  6. `"drawdown_expectations"` is appended to the function's returned `refreshed` list ONLY when at least
     one claim's warm call returned an actual non-None payload — never on an empty ledger or a ledger
     whose every claim is out-of-scope/unresolvable (mirrors the existing "actually did something"
     honesty gate already applied to `market_phase`/`research_hot_keys` in this same function).
  7. The whole ledger-resolution step (steps 1-2) is wrapped in its own top-level try/except, so a
     missing/corrupt ledger file degrades to zero warm calls (an honest omission) rather than aborting
     the rest of the finalize hook.
  8. The function's docstring enumeration of refreshable categories was updated to include
     `"drawdown_expectations"`.

## Files Changed

- `apps/backend/app/engine/data_manager.py` — extended `_refresh_ingest_aggregates` with the
  `drawdown_expectations` warm step (~35 new lines); added imports `from app.engine import evidence` and
  `from app.engine.ledger import FORWARD_WALK_TYPE, read_entries`; updated the function's docstring.
- `apps/backend/tests/test_data_manager.py` — added a `finalize_hook_drawdown_engine` fixture (a
  `finalize_hook_engine`-shaped DB extended with one real `ForwardReturn` row + a monkeypatched causal
  phase classification, so a claim genuinely resolves) and 7 new tests:
  - `test_finalize_hook_warms_drawdown_expectations_for_resolvable_claim` (TC-1)
  - `test_finalize_hook_drawdown_expectations_byte_identical_to_fresh_compute` (TC-3)
  - `test_finalize_hook_drawdown_expectations_unresolvable_claim_not_reported` (TC-4 / honesty gate)
  - `test_finalize_hook_drawdown_expectations_isolates_claim_that_raises` (TC-4 / failure isolation)
  - `test_finalize_hook_drawdown_expectations_missing_ledger_not_reported` (TC-5)
  - `test_finalize_hook_drawdown_expectations_forward_walk_only_ledger_not_reported` (TC-5 variant)
  - `test_finalize_hook_drawdown_expectations_corrupt_ledger_degrades_gracefully` (top-level try/except)
  The existing `test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates` exact-set assertion
  was checked against the real project ledger (7 real entries) and needed NO update — that ledger's
  claims do not resolve against the tiny hand-built fixture's sparse data (no `ForwardReturn` rows at
  all), so `"drawdown_expectations"` legitimately does not appear in that test's expected set; verified by
  running it unmodified after the code change (still PASSED).
- `reports/perf-budgets.md` — new dated section "J-06 closeout — `/evidence` first-view-after-ingest warm
  (iter-7, audit B1 fix)": live proof the mechanism fires end-to-end against the real running dev backend
  (a genuine new-date backfill's job record shows `"drawdown_expectations"` in `aggregates_refreshed`),
  the post-warm `/evidence` first-view timing (curl, method disclosed), and a full curl-based
  reconfirmation of all 11 J-06 pages/endpoints. No committed budget number was loosened.
- `runs/goal-session-ops-hardening/state/blueprint.md` — checked, not edited. The decomposer had already
  added `"drawdown_expectations"` to the Data Contract's `aggregates_refreshed` enumeration and listed
  `/evidence` as a served page of the "Membership timeline / research hot-key caches" row before this
  iteration started; the shipped code matches that contract exactly (list membership, gating convention,
  no new field/endpoint). No drift found.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py tests/test_forward_testing.py tests/test_api_backtest.py tests/test_mcp_window.py -v`
Result: **228 passed, 0 failed, 0 errors** (8846.54s / 2h27m — dominated by the session-scoped `loaded_engine`
fixture's one-time 30-year seed rebuild inside `test_forward_testing.py`, a known, documented project
characteristic — see the `trendora-30y-test-suite-slow-not-product` project lesson; this run time is
test-harness-only and unrelated to product boot/request latency).

Also independently confirmed before the full run: the 19-test `finalize_hook`-scoped subset (`pytest
tests/test_data_manager.py -k finalize_hook`) passed in 112.88s in isolation, including the 7 new
`drawdown_expectations` tests.

## Live Verification (real backend, not just unit tests)

Beyond the unit tests, the fix was exercised live against the running dev backend
(`scripts/start-backend.sh`, prod mode):

1. **Mechanism fires for real:** a genuine new-date backfill (`2015-06-15` — chosen because May/June/July
   2026 and 2015's own monthly-cadence dates were already snapshotted by prior iterations' work, so this
   date guarantees a real, non-zero-work dataset change) via `POST /api/data/jobs` produced 1 new
   snapshot + 1840 new forward returns, and the job's own persisted `aggregates_refreshed` list came back
   including `"drawdown_expectations"` alongside every pre-existing category.
2. **First-view timing:** immediately after that job completed (no intervening `/evidence` request), three
   successive `curl` reads of `GET /api/evidence` measured 17.6ms / 44.3ms / 15.4ms — all 7 real ledger
   claims carried a populated `expectations` panel. This replaces the previously-documented 73.3s
   one-time cold miss (iter-6 CORRECTION) with a sub-50ms first view.
3. **Clean restart verified:** stopped and restarted both `scripts/start-backend.sh` and
   `scripts/start-frontend.sh` — no port conflicts, both answered 200 within ~1s of relaunch. All spawned
   server processes were killed before finishing this task (no lingering uvicorn/next processes).

Full numbers, method disclosure, and the 11-page reconfirmation are in `reports/perf-budgets.md`'s new
"J-06 closeout — `/evidence` first-view-after-ingest warm (iter-7, audit B1 fix)" section.

## Known Issues

None outstanding for this iteration's scope. For clarity (per the plan's explicit instruction not to
restate iter-6's retracted framing): the PRIOR "555.97s severe regression" figure was already established
in iter-6 as a measurement-contamination artifact, and the corrected 73.3s one-time cold-miss baseline it
replaced is now itself closed by this iteration's fix — the CURRENT state is a sub-50ms `/evidence`
first view, live-verified above, not a residual cold-miss of any size.

Two minor, out-of-scope observations for the record (neither blocks this iteration, neither touched):
- The live measurement above used `curl`, not a real Chrome browser, per the plan's explicit disclosed
  fallback clause (a same-process cold `curl` taken immediately after a real ingest is an accepted
  substitute for confirming a one-time warm happened before first view). The authoritative real-browser
  TC-6 pass across all 11 J-06 pages remains browser-qa-agent's own job.
- Starting the dev backend for live verification (twice, for the restart check) refreshed the tracked
  `runs/goal-session-mcp-loop/state/drift-report.json` / `preflight-verdict-history.jsonl` files as a
  normal side effect of the existing boot-time drift check (unrelated to this iteration's diff, not
  something this iteration modifies the logic of) — flagged here only for transparency in case the
  reviewer's diff inspection notices those files touched.
