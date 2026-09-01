# goal-market-compass-iter-32 Execution Plan

## Context check against docs/goal.md
This iteration targets J-09 (backend memory footprint), the last open journey in the
market-compass session — consistent with the goal's Constraints section ("compute-at-ingest",
"host resource-fit" binding note (a)/(b)/(c)) and does not touch any of the six shipped
compass journeys (J-01..J-08, J-10, J-11), all of which stay in the Required-still-passing
regression set. No drift from `docs/goal.md`; no scope creep detected. This is a pure
re-measurement + evidence-durability pass, not a new capability — `Frontend Present: no` is
correct and is stated verbatim by the spec's own Goal Mode Metadata block.

## What to Build
- Verify `config.yaml` `database.pragmas.cache_size` still reads `-65536` (set at iter-4) and
  `pool_size`/`max_overflow` still read `24`/`44` (already spot-checked while planning — no
  drift found: `config.yaml:109,126,127`). No edit expected; if drift is found, restore
  `-65536` only and note it — nothing else in the `database:` block changes.
- Start a fresh backend via `bash scripts/start-backend.sh` with nothing else of ours running
  on the host (no sibling `tensteps`/other goal-mode session). Wait for standing-warm plateau
  (readiness `ready`, `VmPeak` flat across ≥3 consecutive `/proc/<pid>/status` samples).
- Capture the raw sampler output — UTC start/end timestamps, every sample (not just the peak)
  — to a durable file under `runs/goal-market-compass-iter-32/` (e.g.
  `j09-vmpeak-samples.csv`). This is the evidence iter-25's figure lacked; it must survive the
  iteration.
- Re-run the concurrent-load check: a request burst at `server.limit_concurrency` = 64
  simultaneous connections against the same running backend. Record pass/fail — zero
  `QueuePool` `TimeoutError`, zero non-200s attributable to pool starvation.
- Byte-identity spot-check: capture `GET /api/compass` plus 1-2 other already-served read
  endpoints for the exact as-of set `{no param (frontier, 2026-08-12), "2025-04-15",
  "1996-02-01"}` — before and after the cache_size verification step — and confirm byte-for-byte
  identical responses. No other as-of value may be requested (no new manifest mint).
- Append exactly ONE new dated addendum to `reports/perf-budgets.md` — next sequential number
  after the current highest (**Addendum 43**; do not renumber or edit Addendum 40/41/42) —
  recording: measured VmPeak in kB and MB, comparison to the ≤ 2,621,440 kB (2.5 GB) target,
  comparison to iter-4's (3,439,100 kB) and iter-25's (3,064,772 kB, now flagged unsupported)
  figures, the concurrent-load result, the byte-identity result, and a citation of the raw
  evidence file path with its capture start/end UTC timestamps.
- If the ≤ 2.5 GB target is still missed: record the honest figure, do NOT widen the target,
  state plainly in the dev handoff that owner review is the remaining path.
- Run the targeted pragma test (`test_sqlite_pragmas_applied_on_connect` or equivalent in
  `apps/backend/tests/test_db.py`) to confirm `cache_size` still resolves to `-65536` from
  `config.yaml`. Targeted pytest only — never the full suite.
- Run the deterministic replay lane (`scripts/automation/lib/demo_runner.py --mode verify`)
  over the full widened Required-still-passing set — `J-01,J-02,J-03,J-04,J-05,J-06,J-07,J-08,
  J-10,J-11` — against `runs/goal-session-market-compass/journey-scripts/`, writing results to
  `reports/phase-goal-market-compass-iter-32-regression-replay-results.md`. `J-02.json` and
  `J-03.json` were rewritten AFTER iter-31's replay run recorded results (mtimes 03:35:14 /
  03:35:18, after 03:31:03) and have never actually been executed in their current form — this
  is their first real run. Report the real PASS/FAIL verbatim for every journey. **Do not edit
  either script again after this replay run, regardless of outcome.**
- Re-derive the manifest row count AFTER the replay lane finishes (read-only connection): expect
  unchanged at 28 rows / 18 distinct `as_of` / max id 28, matching the iter-31 census. Cite this
  in the dev handoff.
- Add an informational iter-32 note only to `runs/goal-session-market-compass/state/blueprint.md`
  (no IA or Data Contract row changes — matches the convention set by the iter-25/26/27 notes
  for prior ops-only iterations).
- Write the dev handoff at `docs/handoffs/goal-market-compass-iter-32-dev.md` covering all of the
  above, and stating explicitly whether this `Depth: full` spec was executed at full depth or
  demoted to `lean` (per `docs/goal.md`'s binding loop-mechanics rule — never silently treat
  `lean` output as satisfying a `full` requirement).

## Out of scope (do NOT build)
- Any change to `pool_size`, `max_overflow`, `server.memory_cap_mb`, `malloc_arena_max`, or any
  other AG-10 host-guard value — owner-only.
- Any code change to `app.engine.compass`, `build_manifest_payload`, `build_state_band`,
  `_derive_prospective_eligible`, `_severity_at`, `compass.vocabulary.direction_words`,
  `session_delta.py`, `compass.build_narrative`, `compass-whatchanged-card.tsx`,
  `compass-summary-card.tsx` — binding "Do not redo".
- Any live `/api/compass*` call outside the exact 3-value as-of set above — no new manifest
  mint, no backfill.
- Editing `J-02.json`/`J-03.json` after this iteration's replay lane runs, regardless of result.
- `_BarCache.prefill` re-bounding, the `next build` worker cap, `*_memory_pressure` test gating,
  `test_no_magic_numbers.py`'s pre-existing red failure — all owner's call / carried items.
- No UI change of any kind — J-09's Walkthrough clause is explicitly waived this iteration.

## Agents Required
- backend-data: yes — config verification, backend boot + VmPeak sampling, concurrent-load
  check, byte-identity spot-check, perf-budgets.md addendum, targeted pytest, deterministic
  replay lane execution, manifest census, blueprint note, dev handoff.
- frontend-ux: no — zero UI surface change; no displayed value may move (proven by the
  byte-identity spot-check).

Frontend Present: no

## Files to Create/Modify
- `runs/goal-market-compass-iter-32/j09-vmpeak-samples.csv` -- new raw VmPeak sampler capture (UTC start/end + every sample)
- `reports/perf-budgets.md` -- append Addendum 43 (J-09 clean re-measurement); Addendum 40/41/42 untouched
- `reports/phase-goal-market-compass-iter-32-regression-replay-results.md` -- new deterministic replay results (10 journeys)
- `docs/handoffs/goal-market-compass-iter-32-dev.md` -- new dev handoff
- `runs/goal-session-market-compass/state/blueprint.md` -- informational iter-32 note only, no IA/contract row changes
- `config.yaml` -- only IF drift is found in `database.pragmas.cache_size` (not expected; current value already confirmed `-65536`)
- No files under `apps/frontend/` or `apps/backend/app/` should change this iteration.

## Key Test Scenarios
- TC-1: `git diff -- config.yaml` after the iteration shows no change (cache_size already
  `-65536`, pool_size/max_overflow already `24`/`44`) — or, if drift was corrected, shows only
  the single `cache_size` line differing.
- TC-2: fresh `scripts/start-backend.sh` boot, nothing else of ours running; standing-warm
  plateau reached (ready, VmPeak flat ≥3 samples); every sample + UTC start/end timestamps
  saved to a durable file under `runs/goal-market-compass-iter-32/`.
- TC-3: peak VmPeak compared to 2,621,440 kB (2.5 GB); dev handoff states exact kB figure and
  met/missed — target itself never edited either way.
- TC-4: request burst at `limit_concurrency`=64 completes with zero `QueuePool` TimeoutError;
  result recorded in the new perf-budgets.md addendum.
- TC-5: `GET /api/compass` (+1-2 other read endpoints) at the fixed 3-value as-of set, captured
  before/after the cache_size verification, byte-identical — cited in the dev handoff.
- TC-6: `reports/perf-budgets.md` gains exactly one new addendum (43), appended below the
  existing ones; no existing addendum edited; new addendum cites the TC-2 evidence file path.
- TC-7: `J-02.json`/`J-03.json` (rewritten post-iter-31-replay, never executed in that form)
  actually execute this round; `reports/phase-goal-market-compass-iter-32-regression-replay-results.md`
  records a real PASS/FAIL for each — not a lint-only note; neither script edited afterward.
- TC-8: all ten Required-still-passing journeys (J-01..J-08, J-10, J-11) re-verify PASS with
  zero newly-failing/regressed journeys via the replay lane; any deviation reported explicitly,
  not silently reconciled.
- Targeted pytest: `test_sqlite_pragmas_applied_on_connect` (or equivalent in
  `apps/backend/tests/test_db.py`) confirms `cache_size` resolves to `-65536`.
