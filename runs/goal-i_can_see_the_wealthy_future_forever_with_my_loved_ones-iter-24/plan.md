# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-24 Execution Plan

## What to Build
- TEST-ONLY reconciliation. Update two stale `served == engine_output` byte-equality guards in
  `apps/backend/tests/test_api_engine.py` that J-81's legitimate additive `forward_returns` key broke.
  No source, served-payload, endpoint, schema, config, or UI change.
- `test_api_sectors_equals_engine_output` (line 27): before `served == expected`, strip/pop
  `forward_returns` from each served sector row; then SEPARATELY assert each served row carries
  `forward_returns` with `[fr["horizon"] for fr in row["forward_returns"]] == list(cfg.walk_forward.horizons)`.
  Keep the existing `served["benchmark"] == "SPY"` and `len(served["rows"]) == 31` assertions.
- `test_api_themes_equals_engine_output` (line 172): identical treatment — strip `forward_returns`
  per served theme row before `served == expected`, then separately assert the additive field exists
  with the configured horizons per row. Keep the existing `len(served["rows"]) == len(cfg.themes)` assertion.
- Mirror the IN-FILE blessed precedent `test_api_stocks_equals_engine_output` (lines 121-143) verbatim
  in shape (`stripped = {**served, "rows": [{k: v for k, v in row.items() if k != "forward_returns"} ...]}`
  then `assert stripped == expected`). Do NOT invent a new approach.
- The canonical-payload byte-equality (all scores/ranks/components/breadth/trend/members) MUST remain
  asserted — only the additive `forward_returns` key is excluded from the equality. The reconciliation
  must still fail if a genuine score/rank/component drift were introduced.
- Confirm the two targeted tests pass directly (dev), then HAND the FULL backend pytest suite to the
  pump (nohup-async) to confirm `EXIT_CODE=0` — target ~846 passed, 4 skipped, 0 failed.

## Agents Required
- developer: yes -- edit only `apps/backend/tests/test_api_engine.py` (two tests). Run the two targeted
  tests to confirm green; hand the full suite to the pump (nohup-async — see Assumptions). Write the
  dev handoff stating the full-suite result and EXIT_CODE.
- backend-data: yes -- the change lives in the backend test suite.
- frontend-ux: no -- zero frontend changes.

## Frontend Present
no

## Files to Create/Modify
- `apps/backend/tests/test_api_engine.py` -- reconcile the two stale byte-equality guards
  (`test_api_sectors_equals_engine_output`, `test_api_themes_equals_engine_output`) to exclude J-81's
  additive `forward_returns` from the equality and separately assert it exists with configured horizons.
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-24-dev.md` -- dev
  handoff: what changed, the two targeted-test results, and the FULL-suite result + EXIT_CODE.

## Key Test Scenarios
- `apps/backend/tests/test_api_engine.py::test_api_themes_equals_engine_output` passes: byte-equality
  asserted on the canonical scored payload modulo `forward_returns`, AND each served theme row carries
  `forward_returns` with horizons == `config.walk_forward.horizons`; `len(rows) == len(cfg.themes)` holds.
- `apps/backend/tests/test_api_engine.py::test_api_sectors_equals_engine_output` passes: same canonical
  byte-equality modulo `forward_returns`, plus the additive-field/horizons assertion; `benchmark == "SPY"`
  and `len(rows) == 31` hold.
- The corrected guards STILL detect real drift: stripping ONLY `forward_returns` (no other key) leaves
  every canonical scored field under `served == expected`, so a genuine score/rank change would still fail.
- The FULL backend pytest suite reaches `EXIT_CODE=0` — the prior 2 failures are now green and NO other
  test regressed (~846 passed, 4 skipped, 0 failed).
- Target journeys J-81, J-82 unchanged (served payloads byte-identical); required-still-passing
  J-03, J-04, J-06, J-09, J-21, J-75 remain green (no served-value change; J-06 single-source intact).

## Scope / Anti-Goal Notes (assumptions documented, not asked)
- IN SCOPE is strictly the two test edits + the full-suite confirmation. OUT OF SCOPE: any change under
  `apps/backend/app/` or `apps/frontend/` (no served-payload/endpoint/schema/config/UI change); any new
  feature, journey, or refactor; loosening the no-drift / single-source guarantee.
- Anti-goal preservation is intrinsic: the canonical byte-equality stays asserted, so single-source,
  no-recompute, immutability, no-lookahead, and no-fabrication remain proven by the still-asserted guard.
  `forward_returns` is already a registered Data-Contract value (J-75/J-81), served VERBATIM via the
  shared `forward_testing:_leadership_returns` builder Backtest uses — never a second computation.
- J-22/J-23/J-24 stay honestly blocked-NA (data-walled, non-vetoing) — NOT in scope.

## QA / Browser Note (Frontend Present: no)
- This is a test-only change with zero UI surface delta — no full per-journey browser re-run is required.
- Optional LIGHT smoke only (non-blocking): `/themes` and `/sectors` still serve 200 and render their
  five forward-return columns (J-81). J-06 single-source byte-identity is already proven by
  `test_iter23_leaderboard_returns.py`; no new browser evidence is needed to close this iteration.

## Operational Assumptions (from MEMORY / lessons — for dev/reviewer/evaluator)
- `backend-test-suite-runtime`: the full pytest suite is ~34 min and a SUBAGENT cannot finish it
  (10-min Bash cap + bg job dies on turn-end). DEV runs the two targeted `test_api_engine.py` tests
  directly to confirm the fix, and HANDS the full suite to the pump.
- `goal-pump-never-block-evaluator-on-suite`: do NOT make the pump wait for the background full-suite
  before answering a CLAIMED dispatch; run it nohup-async and answer promptly with "targeted fix tests
  green + full suite re-run in progress" if it isn't done.
- `goal-pump-background-helpers-need-nohup`: launch the full-suite run via `nohup bash -c '...' &` so it
  outlives the ~3h wrapper-kill.
- `dev-server-cleanup-by-port`: never broad `pkill -f` on this multi-project machine; kill by port. No
  service restart should be needed for a test-only change.
