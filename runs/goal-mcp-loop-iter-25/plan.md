# goal-mcp-loop-iter-25 Execution Plan

## Context (why this iteration exists)
iter-24 shipped goal.md's fast-platform mechanical backend pass (items B/C/D/G/H/K) but was scored
**REGRESSION**: item B's SQLite `mmap_size_bytes=1073741824` (1 GB) x the new 10+20 connection pool
exhausted the `server.memory_cap_mb=6144` `ulimit -v` cap, OOM-crashing the backend on the FIRST cold
`GET /api/data` load after any restart (browser-qa UT-16, reproduced 2/2) -- a critical **anti-goal #8**
violation ("widening the data basis must never crash an existing page or exhaust a service's memory").
That broke prior-passing **J-13** and failed target **J-15**'s own cold-path criterion.

The iter-24 audit already root-caused and fixed this in-tree: `config.yaml:108` -> `mmap_size_bytes: 0`,
committed at HEAD (`665565a`, "wip(goal): iter 24 REGRESSION -- parked uncommitted work (not pushed)").
I confirmed by direct inspection: `config.yaml:108` reads `mmap_size_bytes: 0` with the audit's rationale
comment, `git diff -- config.yaml` is clean (no pending edit), and the rest of the working tree carries
no stray backend/frontend source diffs -- only goal-engine bookkeeping files (session.json, summary.md,
telemetry.jsonl, trace/, blueprint.md, the HTML report index) are modified, which is normal live-engine
housekeeping, not code.

**But an engine-level fix is not journey evidence until the canonical browser-qa lane re-runs it live**
(session lesson, repeated at iter-13/20/22/24). So iter-25 ships **zero new feature code** -- it is a
fix-VERIFICATION + artifact-reconciliation pass only, run at full depth because the gates that must
formally re-clear this (`ux-regression-reviewer`, `auditor`, `phase-closure-auditor`) only run in the
full 11-step pipeline.

## What to Build
- Nothing new. No new features, no new UI, no new backend logic, no new endpoints.
- Confirm the already-committed fix is still present at run start (it is, per the check above); restore
  ONLY `mmap_size_bytes: 0` and nothing else if it is somehow absent.
- Bring up both prod-mode services and LIVE-drive the cold-path repro (stop backend -> cold-start ->
  `GET /data` as the FIRST request, at least twice) -- proving the OOM is gone is the actual deliverable.
- Correct `reports/perf-budgets.md`'s cold-path entry with a REAL fresh-restart measurement.
- Re-run (unedited) the targeted byte-identity test files to prove nothing drifted.
- Freshly LIVE-replay the required-still-passing journeys (J-03, J-04, J-05, J-11, J-14) and smoke-check
  J-01/J-10/J-12 -- iter-24's crash aborted their replay, so these need fresh evidence, not carried-over
  screenshots.
- Produce iter-25's own handoff/summary/status artifacts with an honest crash -> fix -> re-verify narrative.
- Get `ux-regression-reviewer` and `phase-closure-auditor` to actually flip to PASS this time (both FAILed
  in iter-24, while QA fail-opened to PASS on a claim later invalidated by the audit -- do not repeat that).

## Agents Required
- backend-data: yes -- operational/verification pass only: bring up services, drive the live cold-path
  repro, run the targeted unedited test selection, correct `reports/perf-budgets.md`, regenerate
  `status.json`, write the dev handoff + implementation-summary + user-visible-changes. This is NOT a
  code-writing task except the single-line contingency restore of `mmap_size_bytes: 0` in the unexpected
  case it has reverted (it has not, as of this plan). Any `pool_size`/`max_overflow`/`cache_size`/
  `memory_cap_mb` retuning is explicitly OUT OF SCOPE -- touching those re-opens the regression.
- frontend-ux: no -- zero frontend source change (the storage card, availability legend, and every
  `/data` surface stay byte-identical to iter-24). The only frontend-adjacent step is operational
  (`rm -rf apps/frontend/.next` before the browser-qa lane, the iter-20 staleness-stamp dodge) and rides
  along with the backend-data agent's / browser-qa lane's own setup -- it is not a UI implementation task.

Frontend Present: yes

## Files to Create/Modify
- `config.yaml` -- READ-ONLY confirm `mmap_size_bytes: 0` at line 108; edit ONLY if it has reverted, and
  only that one value.
- `reports/perf-budgets.md` -- append/correct the cold-path section with a fresh iter-25 restart
  measurement (a real `GET /data` first-request timing under the live 6144 MB cap), alongside the
  still-valid warm-budget table.
- `reports/phase-goal-mcp-loop-iter-25-implementation-summary.md` -- new; crash -> fix (already applied)
  -> re-verify narrative.
- `reports/phase-goal-mcp-loop-iter-25-user-visible-changes.md` -- new; the only user-visible delta is
  "`/data` no longer crashes the backend on a cold load" -- no new UI.
- `runs/goal-mcp-loop-iter-25/status.json` -- regenerate at the end so `qa_verdict`/`blockers` accurately
  reflect the real gate outcomes (no stale PASS-with-empty-`blockers` while anything stays unresolved --
  the iter-24 contradiction this iteration exists to not repeat).
- `docs/handoffs/goal-mcp-loop-iter-25-dev.md` -- new dev handoff.
- No `apps/backend/**` or `apps/frontend/**` source edits are expected (contingency-only, see above).
- Downstream pipeline artifacts (not the developer's job; listed so reviewer/QA/audit expect the same
  file set iter-24 produced): `reports/reviews/goal-mcp-loop-iter-25-review.md`,
  `reports/qa/goal-mcp-loop-iter-25-{test-plan,qa}.md` + `-evidence/` dir,
  `reports/phase-goal-mcp-loop-iter-25-{ui-test-plan,ui-test-results,ui-surface-map,ux-regression,
  closure-verdict,what-to-click}.md`.

## UI Evolution
- New user-facing capability: none -- recovery/verification pass only.
- New information displayed: none.
- New user actions: none.
- UI surface changes: none -- `/data` and all core pages must render byte-identical to iter-24; the only
  behavioral difference is the ABSENCE of the cold-load crash.
- Navigation changes: none.

## Visual Requirements
- Component patterns: N/A -- no new components; iter-24's `StorageCapacityPanel`/`CoveragePanel`/
  availability heatmap carry forward unchanged.
- Layout: unchanged from iter-24.
- Key visual effects: unchanged from iter-24.
- States to handle: the one state that must now behave correctly is the cold-boot state on `/data` -- it
  must render the coverage/storage/missing-data panels within budget, never a blank application-error
  page, and the backend process must not die. If the backend is genuinely unreachable, exactly one
  contained error card (anti-goal #8 / the existing UT-05 contract) -- never a blank crash page.

## Key Test Scenarios
- **Cold-path repro (P1, the crux):** stop backend -> cold-start -> `GET /data` as the FIRST request, at
  least twice -> backend stays up, `/data` renders (flips iter-24's UT-16 -> UT-06 -> UT-05 FAIL sequence
  to PASS). Must be driven LIVE by `browser-qa-agent` -- never accepted from an engine-level ablation
  alone (iter-13/20/22/24 lesson: an `/api/health` boot is a different code path and gives a false
  "cold path OK").
- **Storage card sanity (P1):** UT-01/UT-02 -- `/data`'s storage-footprint card values match the live
  `GET /api/data` `capacity` payload.
- **Perf budget re-confirmation:** cold `/api/data` completes <= 60 s with no OOM under the 6144 MB cap
  (the corrected, real measurement replacing iter-24's false claim); warm budgets still hold (pages
  <= 3 s; `/api/stocks` <= 1.5 s; `/api/stocks/{ticker}` <= 0.3 s; `/api/data` <= 1.5 s warm; `/api/health`
  <= 0.1 s).
- **Required-still-passing fresh LIVE replay (not carried from iter-24's aborted run):** J-03 (`/stocks` +
  `/evidence` "Not yet proven"), J-04 (Dashboard regime + evidence link), J-05 (`/evidence` all-FAIL
  ledger rows), J-11 (both ledgers all-FAIL, no stale edge), J-14 (deep vendor-labeled index/macro
  context).
- **Smoke re-confirm:** J-01 (`/stocks` leaderboard incl. sector-sort, 541/541), J-10 (Full/Recent history
  toggle), J-12 (`/data` 541 == `/stocks` 541/541).
- **Unit/integration (run, do not edit):** `test_bar_cache.py`,
  `test_api_engine.py::test_filtered_stock_rows_byte_identical_to_full_scan_row`, `test_health.py`,
  `test_data_manager.py`'s diagnostic query-count test -- all green, unedited (an edit to any of these is
  itself a regression signal). Do NOT run the full ~10-11h 30-year suite as a gate (iter-23 lesson); clear
  `/tmp/pytest-of-*` first if any targeted run touches the DB fixture.
- **Gate flips required (this is what iter-24 failed):** `ux-regression-reviewer` -> UX-REGRESSION-PASS;
  `phase-closure-auditor` -> CLOSURE-PASS; anti-goal #8 marked `resolved=true` with no other anti-goal
  violated.
- **Evidence hygiene (carried lessons):** every referenced screenshot `md5`-distinct, full-page or
  element-clip, of the actually-asserted frame (iter-11/13/14/15 lesson) -- never trust a PASS label or
  DOM-text line alone. Check BOTH `reports/phase-goal-mcp-loop-iter-25-ui-test-results.md` (canonical,
  terminal gate) AND `reports/qa/goal-mcp-loop-iter-25-qa.md` (iter-4/5 two-lane discipline) -- a QA-lane
  PASS never substitutes for the canonical lane; trust the browser-qa CONTENT over `status.json`/QA prose
  (iter-24 carryforward process flag: QA graded a since-invalidated claim PASS while its own browser-qa
  read FAIL).

## Operational Notes (pre-flight)
- Free ports :8255 / :3255 before binding; `rm -rf apps/frontend/.next` before dispatching browser-qa
  (iter-20 staleness-stamp trap).
- Confirm BOTH services return HTTP-200 before dispatching browser-qa -- never accept a "ready to ship"
  status over an empty evidence dir or a CLOSURE-FAIL.
- No Evidence Claim this iteration (none proposed in the spec; both ledgers stay byte-identical all-FAIL,
  canonical Bonferroni divisor stays 8) -- the post-decompose gate passes automatically.

## Alignment Check
Directly serves goal.md's Must-have journeys **J-13** (Data Manager reflects the broadened universe,
unambiguous availability legend) and **J-15** (core pages/APIs stay fast, cold path never OOMs), and
closes a critical **anti-goal #8** violation (resilience to data-shape/scale change -- no unbounded
whole-table load, no blank crash page, no memory exhaustion). No drift: the spec explicitly excludes
evidence/ledger work, J-16, any re-tuning beyond the single committed fix, and the non-blocking follow-ups
(F1 `/data` no-retry desync, T1 cadence-aware backfill-timing range) -- correctly scoped as a surgical
recovery pass, not a feature iteration. GOAL_ACHIEVED is correctly not expected this cycle (J-02/J-06/
J-07/J-08/J-09 remain sanctioned-partial -- no staging winner clears the Bonferroni divisor-8 today -- and
J-16 is deliberately unbuilt); CONTINUE is the expected verdict on a clean run.
