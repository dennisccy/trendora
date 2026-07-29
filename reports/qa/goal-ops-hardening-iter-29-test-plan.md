# Goal Iteration 29 Functional Test Plan

**Phase:** goal-ops-hardening-iter-29  
**Date:** 2026-07-27  
**Frontend Present:** yes

## Phase Goal

Close the session's last open AG-8 (critical) finding: bound the Evidence page's per-claim compute so it can never exhaust the backend's memory or crash `GET /api/evidence`, and make residual per-claim compute failure degrade honestly instead of silently rendering nothing.

## Test Cases

### TC-01 — Bounded accumulator never exceeds one chunk during `_factor_observations`

**Type:** api  
**Preconditions:**
- Backend test suite loaded with `test_research_streaming.py` extended with a new fixture
- New fixture uses `prune_engine` hand-built pattern with rows spanning >1 `read_batch_size` chunk across ≥2 distinct `run_id`s
- `app.engine.research._factor_observations` receives bounded implementation

**Steps:**
1. Load new test fixture with multi-chunk, multi-run-id structure
2. Call `_factor_observations(as_of=None)` on the test fixture
3. Instrument the function to track live `ret_by_run_symbol` accumulator dict size during execution
4. Record peak dict size reached at any point during the call

**Expected outcome:**
Peak accumulator dict size never exceeds `config.research.read_batch_size` (2000) entries at any point during the call.

**Pass criteria:**
`assert max(observed_accumulator_sizes) <= 2000` — the bounded rewrite processes the fixture in chunks, never materializing the full `(run_id, symbol)` cross-product into memory.

---

### TC-02 — Bounded implementation produces byte-identical output to current implementation

**Type:** api  
**Preconditions:**
- Same extended fixture from TC-01 is prepared
- Both bounded (post-fix) and current (pre-fix) implementations are available for comparison

**Steps:**
1. Run current (pre-fix) implementation against the extended fixture with `as_of=None`
2. Run bounded (post-fix) implementation against the same fixture with `as_of=None`
3. Compare full returned observation lists: `run_id`, `ticker`, `factor`, `return`, `max_drawdown`, `regime`, and order
4. Repeat for an `as_of=D` call (specific date) on the same fixture

**Expected outcome:**
Both implementations return observations in identical order with identical field values for both `as_of=None` and `as_of=D` cases.

**Pass criteria:**
`_eq(pre_fix_output, post_fix_output) == True` for both as_of conditions; the fix preserves correctness.

---

### TC-03 — No-lookahead preserved: `as_of=D` observations never reference runs dated after `D`

**Type:** api  
**Preconditions:**
- Extended fixture from TC-01/TC-02 is prepared
- At least one `ScannerRun` row in fixture has `asof_date` > test `as_of` date

**Steps:**
1. Call `_factor_observations(as_of=D)` with specific test date `D`
2. Iterate returned observations and check each observation's `run_id` against `ScannerRun.asof_date`
3. Record all `run_id`s with `asof_date > D` (should be empty)

**Expected outcome:**
Zero returned observations reference a run whose `asof_date` is after `D`.

**Pass criteria:**
`len([obs for obs in results if obs['run_id'].asof_date > D]) == 0` — no lookahead introduced by bounded rewrite.

---

### TC-04 — Per-claim compute failure isolated: one claim's `expectations_status: "unavailable"`, other claims unaffected

**Type:** api  
**Preconditions:**
- `test_evidence.py`'s `evidence_dd_engine` fixture extended with second resolvable claim
- `compute_drawdown_expectations_cached` monkeypatched to raise `MemoryError` for exactly one claim (claim A) only
- `build_evidence_payload` receives per-claim isolate-and-continue guard

**Steps:**
1. Call `build_evidence_payload(ledger_path, session=session, config=...)`
2. Inspect returned payload's claim rows
3. Verify claim A (monkeypatched) row: has `expectations_status: "unavailable"`, has no `expectations` key
4. Verify claim B (unaffected) row: has `expectations` key (normal), no `expectations_status` field

**Expected outcome:**
Payload contains exactly two claim rows; claim A row has failure disclosure; claim B row is byte-unchanged from pre-fix behavior.

**Pass criteria:**
```
payload['claims'][0]['expectations_status'] == "unavailable"
'expectations' not in payload['claims'][0]
'expectations' in payload['claims'][1]
'expectations_status' not in payload['claims'][1]
```

---

### TC-05 — Frontend rendering-state helper distinguishes unavailable from no-field case

**Type:** artifact  
**Preconditions:**
- New pure rendering-state helper function added to `apps/frontend/lib/evidence.ts`
- Test cases added to `apps/frontend/lib/evidence.test.ts`
- Helper correctly identifies both "unavailable" and "no field" states

**Steps:**
1. Create test object A: `{ expectations_status: "unavailable", expectations: undefined }`
2. Create test object B: `{ expectations: undefined }` (no `expectations_status` field)
3. Call helper on object A
4. Call helper on object B
5. Compare returned state values

**Expected outcome:**
Helper returns distinct state values for the two objects (e.g., "unavailable" for A, "not_applicable" for B).

**Pass criteria:**
`helper(A) !== helper(B)` — the rendering-state helper correctly distinguishes the new compute-failure case from the pre-existing unresolvable-cohort case.

---

### TC-06 — Live `/evidence` load on deep-basis DB: within budget, zero MemoryError logs

**Type:** browser  
**Preconditions:**
- Backend running via `scripts/start-backend.sh`
- Deep-basis DB loaded with evidence ledger's 7 claims
- `reports/perf-budgets.md` Item I lists `/evidence` budget
- `logs/backend.log` monitored for exceptions

**Steps:**
1. Open browser, navigate to `http://localhost:3000/evidence`
2. Wait for page fully load (all claim cards rendered)
3. Record page load time
4. Check `logs/backend.log` for MemoryError or ASGI exception lines during request window

**Expected outcome:**
Page renders every claim's card within committed budget; no MemoryError or "Exception in ASGI application" in backend logs for this request window.

**Pass criteria:**
- Load time ≤ budget threshold in `reports/perf-budgets.md` Item I
- `grep -i "memoryerror\|exception in asgi" logs/backend.log` returns zero matches during this test window

---

### TC-07 — Single-day backfill completes: ingest-finalize warm loop processes all claims, zero MemoryError

**Type:** api  
**Preconditions:**
- Backend running with data manager ingest loop enabled
- Pick unsnapshotted date NOT in `runs/goal-session-ops-hardening/state/iteration-state.md` "Do not redo" list (already used: 2011-03-10, 2015-09-09, 2018-02-15, 2018-03-15, 2025-05-15, 2026-05-02..29)
- Confirm fresh date via `GET /api/scanner-runs` at test time

**Steps:**
1. Trigger single-day backfill via backend API for chosen fresh date (e.g., `POST /api/data/backfill?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`)
2. Poll for backfill completion
3. Read `logs/backend.log` for MemoryError lines from ingest-finalize loop (search around `data_manager.py:3361`)
4. Query backfill run record for `aggregates_refreshed` list

**Expected outcome:**
Backfill completes without crashing; run's persisted `aggregates_refreshed` list includes `"drawdown_expectations"`; zero MemoryError lines in logs during this run.

**Pass criteria:**
- Backfill exit code: 0 (success)
- `"drawdown_expectations" in run.aggregates_refreshed == True`
- `grep "memoryerror" logs/backend.log` for this run time window: 0 matches

---

### TC-08 — J-06 `/evidence` page latency regression check: within existing budget, no regression

**Type:** browser  
**Preconditions:**
- J-06 full 11-page sweep defined in journey-scripts
- Pre-fix baseline latency recorded in prior iteration's results
- Bounded implementation deployed to backend

**Steps:**
1. Run J-06's 11-page load sweep
2. Record `/evidence` page load time this iteration
3. Compare to pre-fix baseline

**Expected outcome:**
This iteration's `/evidence` latency ≤ pre-fix baseline; stays within budget in `reports/perf-budgets.md` Item I.

**Pass criteria:**
`latency_iter29 <= latency_iter28` — no regression introduced by the bounded rewrite.

---

### TC-09 — Secondary consumer (`/research` Factor Lab) unaffected: decile table and rank-IC render with real values

**Type:** browser  
**Preconditions:**
- Frontend running via `npm run dev`
- Backend running with bounded `_factor_observations` implementation
- `/research` page accessible

**Steps:**
1. Navigate to `http://localhost:3000/research`
2. Select any factor and horizon combination from the UI
3. Wait for table and rank-IC chart to render
4. Inspect browser console for errors
5. Verify decile table contains numeric values, not blank/error placeholders

**Expected outcome:**
Page renders decile table with real numeric values; rank-IC chart displays; no console error or exception.

**Pass criteria:**
- Table cell content is numeric (not "—" or "N/A" for all cells)
- Browser console has no "Uncaught Error" or "TypeError" during this test
- `_factor_observations` was successfully called and returned data

---

### TC-10 — Deterministic replay of J-06 golden script: zero FAIL rows, all-PASS

**Type:** artifact  
**Preconditions:**
- J-06 golden replay script at `runs/goal-session-ops-hardening/journey-scripts/J-06.json`
- Script was fixed at iter-28, never exercised through deterministic replay lane since
- Replay runner configured to execute script end-to-end

**Steps:**
1. Run deterministic golden replay: `python3 scripts/automation/replay_ui_tests.py runs/goal-session-ops-hardening/journey-scripts/J-06.json`
2. Capture merged test-results output to `reports/qa/J-06-replay-results.md`
3. Count PASS vs FAIL rows

**Expected outcome:**
Deterministic golden replay of J-06 runs end-to-end with all steps returning PASS; zero FAIL rows in merged results.

**Pass criteria:**
- FAIL row count == 0
- PASS row count == expected (11 pages per spec)
- No timeout or runner crash

---

### TC-11 — Error case regression: unresolvable cohort keeps silent-omission behavior

**Type:** api  
**Preconditions:**
- Test evidence with at least one claim whose cohort is genuinely unresolvable (unknown factor, out-of-scope horizon)
- `build_evidence_payload` called with this claim in ledger

**Steps:**
1. Call `build_evidence_payload(ledger_path, session=session, config=...)`
2. Find the unresolvable claim row in returned payload
3. Check for presence of `expectations_status` field
4. Check for presence of `expectations` field

**Expected outcome:**
Unresolvable claim row has no `expectations` key AND no `expectations_status` key — the pre-existing honest-None behavior is unchanged.

**Pass criteria:**
```
'expectations' not in unresolvable_claim_row
'expectations_status' not in unresolvable_claim_row
```
This proves the new code path is additive (only for compute-failure case), not a replacement of pre-existing logic.

---

## Summary

**Total test cases:** 11

| Type | Count | Description |
|------|-------|-------------|
| API | 7 | TC-01 (accumulator bound), TC-02 (byte-identity), TC-03 (no-lookahead), TC-04 (per-claim isolate), TC-07 (ingest warm loop), TC-11 (unresolvable cohort) |
| Browser | 4 | TC-06 (live evidence load), TC-08 (J-06 regression), TC-09 (Factor Lab secondary), TC-10 (J-06 replay) |
| Artifact | 1 | TC-05 (rendering-state helper) |

**Coverage:**
- Memory safety: TC-01, TC-02, TC-03, TC-06, TC-07
- Honesty/disclosure: TC-04, TC-05
- Regression: TC-08, TC-09, TC-10
- Error handling: TC-11
- Depth: full (3+ modules touched: research.py, evidence.py, data_manager.py)
- Frontend: yes (J-06/J-07 journeys required-still-passing via browser-qa-agent)
- Regression sweep: J-01, J-03, J-04, J-05, J-08, J-09 (golden replay, unchanged this iteration)
