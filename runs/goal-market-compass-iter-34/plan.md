# goal-market-compass-iter-34 Execution Plan

## Context check against docs/goal.md
All eleven Must-have journeys are `passing` as of iter-33. This iteration targets J-09 again
(confirmation only — the binding "Do not redo" list forbids touching `warmup.py`'s cadence loop
or `prices.py`'s `_BarCache`/prefill, which shipped and closed at iter-33 with Addendum 44:
2,467,888 kB VmPeak, under the 2,621,440 kB / 2.5 GB target). No new capability, no drift from
`docs/goal.md`. Prior verdict was ESCALATE for two non-product reasons only: (1) `Depth: full`
was silently dispatched as `lean` at iter-33 (no auditor/QA/closure/ux-regression step, no
disclosure), and (2) `goal_gate.py results` exits 1 on the merged file because J-09 — whose
`docs/goal.md` Acceptance literally reads `**Walkthrough:** waived` — has no browser row and is
listed under "Missing Target Journeys", forcing `BLOCKED`. This iteration is a closing
measurement + harness fix, genuinely at full depth (confirmed: `depth-dispatched` at
`runs/goal-session-market-compass/iter-34/depth-dispatched` already reads `full`). `Frontend
Present: no` is correct and matches the spec's own Goal Mode Metadata block verbatim.

## What to Build

### A. Extended, twice-independent J-09 re-measurement (developer + auditor)
- Re-run the standing-warm VmPeak/VmSize/VmRSS sampler at 1-second intervals for **≥360 seconds**
  post-boot (`bash scripts/start-backend.sh`), reusing/adapting the existing
  `runs/goal-market-compass-iter-33/vmpeak_sampler.py` tooling (extend its window, and record
  VmSize_kB/VmRSS_kB columns alongside VmPeak_kB — Addendum 44 already captured all three at a
  few checkpoints, this round needs them on every row).
- Independently repeat the identical measurement a second time from a **fresh** backend boot as
  the auditor's own from-scratch re-derivation (not copied from the developer's CSV/numbers) —
  this is the specific "independent checker take the measurement again from scratch" request the
  prior evaluator made. Two separate CSVs, two separately computed max(`VmPeak_kB`).
- Append **Addendum 45** to `reports/perf-budgets.md` (append-only; `git diff --stat` must show
  only `+N/-0`) recording, for BOTH runs: max `VmPeak_kB` vs the 2,621,440 kB bar and vs
  Addendum 44's 2,467,888 kB; and the settled `VmRSS_kB`/`VmSize_kB` pair read at the row where
  `VmPeak_kB` last increased (the plateau) — distinct from the high-water mark, per iter-32's
  lesson.
- Re-run the byte-identity spot check (`cmp`) over the same 7 authorized `as_of` values ×
  `/api/compass` + `/api/dashboard` = 16 captures (same set Addendum 44 used) against the current
  backend; record compared/differing counts.
- Re-prove zero DB writes across both boots this round via the iter-27b `mode=ro` control
  connection (must refuse `CREATE TABLE`) plus `.db` mtime + WAL byte-size before/after both boots.
- Host-quiet note: no other goal-mode engine (this session or the sibling `tensteps`) should run
  concurrently during either sampling window — disclose actual host state (as Addendum 43/44 did)
  regardless.

### B. Goal-mode harness fix — walkthrough-waived evidence recording (backend/tooling only)
- Patch `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` (the real file;
  `scripts/` is a tracked symlink into it — never edit both copies) so a target/required journey
  whose **`docs/goal.md` Acceptance text carries the literal marker `**Walkthrough:** waived`**
  (verified present verbatim for J-09/J-10/J-11 at `docs/goal.md:585,931,2193`) can be recorded
  verified through a cited non-UI evidence row (e.g. `UT-J-09`, Evidence cell naming Addendum 45
  + the sampler CSV paths) instead of being forced to `BLOCKED`.
  - Read the exemption list from `docs/goal.md` itself (never journey-ID pattern matching) so the
    scope is provably tied to the literal marker and cannot silently generalize.
  - Trace exactly which mechanism currently forces BLOCKED for a walkthrough-waived journey with
    no browser row and fix that specific one — three candidate points found while planning, verify
    which fire in practice:
    1. `missing_target_journeys`/`missing_required_journeys` (lines ~159-234): checks
       `present_ids = {r["test_id"] for r in rows}` — a `UT-J-09` row from ANY source (not just
       browser) already counts as "present" here, so if J-09 truly has zero rows today, adding a
       cited-evidence row may already satisfy this guard without a code change to these functions.
    2. `compute_overall` (line ~124): BLOCKED has priority over PASS — if any lane (browser-qa or
       replay) emits an explicit `| BLOCKED |` cell for J-09 because it cannot execute a UI check,
       that alone forces the headline to BLOCKED even with a good evidence row elsewhere; the fix
       may need to stop that lane from emitting a raw BLOCKED cell for a waived journey, or have
       the cited-evidence row supersede it (parse_rows already has "later row for the same test_id
       wins" — see `t_later_wins` in the self-tests).
    3. `goal_gate.py`'s `_BLOCKED_CELL_RE` (line ~89): scans the WHOLE merged file text for any
       literal `| BLOCKED |` cell regardless of headline — a stray BLOCKED row for J-09 would still
       fail `goal_gate.py results` even if `merge_ui_test_results.py`'s own headline is fixed. If
       the browser-qa/replay lane's waived-journey row is not eliminated, this file needs a
       parallel, equally strictly-scoped exemption.
  - Add the `UT-J-09` (and analogous J-10/J-11 pattern, unchanged this iteration) evidence row
    through whichever step is the right owner — likely a small step in the merge invocation or a
    developer-authored synthetic results fragment merged alongside the replay lane's output, not a
    one-off manual edit of the final report (per the spec's own assumption-ledger entry).
- Add a focused regression test in `merge_ui_test_results.py`'s existing self-test suite (`_self_test`)
  proving BOTH directions (TC-8a/TC-8b):
  (a) a synthetic walkthrough-waived target journey with a cited-evidence row → merged headline
      non-BLOCKED;
  (b) a synthetic target/required journey WITHOUT the `docs/goal.md` marker, missing or SKIP-only
      → still forces BLOCKED exactly as before (iter-41/42's own guard must not regress into a
      general loophole).
- Only if required to close point 3 above, patch `goal_gate.py` with an equally strictly-scoped
  exemption (same literal-marker read, never broadened).
- Re-run `python3 scripts/automation/lib/goal_gate.py results
  reports/phase-goal-market-compass-iter-34-ui-test-results.md` after the merge and record the
  **observed** exit code + headline verdict in the dev handoff (never asserted from memory —
  iter-32's "a gate that asserts an artifact without opening it" lesson).

### C. Regression widening (browser-qa / replay lane)
- Re-verify all ten Required-still-passing journeys (J-01..J-08, J-10, J-11) via deterministic
  replay (`demo_runner.py --mode verify` against `runs/goal-session-market-compass/journey-scripts/`)
  plus browser-qa where live checks are warranted — write to
  `reports/phase-goal-market-compass-iter-34-regression-replay-results.md`.
  - Golden-script hygiene check (third clean round): confirm every `journey-scripts/*.json` mtime
    predates this iteration's replay-run timestamp. Current mtimes (all before this iteration
    starts): J-01 Aug 20, J-02/J-03 Sep 1 03:35, J-04 Aug 20, J-05 Aug 28, J-06 Aug 28, J-07 Sep 1
    01:14, J-08 Aug 31 22:42, J-10 Aug 27, J-11 Sep 1 01:51 — do not edit any of them this
    iteration.
- Merge those results with the new J-09 evidence row into
  `reports/phase-goal-market-compass-iter-34-ui-test-results.md`.

### D. Depth disclosure + bookkeeping
- State explicitly, in words, in the dev handoff which depth actually dispatched, cross-checked
  against `runs/goal-session-market-compass/iter-34/.steps/` (the session engine's real marker
  directory — confirmed from iter-33's own `.steps/` layout; the phase spec's own text says
  `runs/goal-market-compass-iter-34/.steps/`, which is the flat per-iteration artifacts dir, not
  where the engine's step markers actually land — check both, report what is actually found)
  containing `auditor.done`, a QA-or-browser-qa completion marker, `closure.done`, and
  `ux-regression.done`. `depth-dispatched` for this iteration already reads `full`
  (`runs/goal-session-market-compass/iter-34/depth-dispatched`) — if any of those four markers end
  up missing, disclose the demotion explicitly per `docs/goal.md:2423-2436`, never silently.
- Append an iter-34 informational note to `runs/goal-session-market-compass/state/blueprint.md`
  (matching the iter-25/32/33 precedent — no IA/Data Contract row changes; this iteration adds no
  new surface).
- Write the dev handoff at `docs/handoffs/goal-market-compass-iter-34-dev.md` naming the two
  pre-existing unrelated red unit tests explicitly as carried (neither fixed nor silently ignored).

## Out of scope (do NOT build)
- Any change to `apps/backend/app/engine/warmup.py`'s cadence loop or
  `apps/backend/app/engine/prices.py`'s `_BarCache`/`bar_cache`/`prefill` — binding "Do not redo".
- Widening the 2.5 GB target or touching `memory_cap_mb`, `pool_size`, `max_overflow`, or
  `project-extensions/host-guard/host-guard.env` — owner-only (AG-10).
- Any change to the shipped compass journeys' engine/UI code (J-01..J-08, J-10, J-11) — this is a
  regression re-verify only, not a rebuild.
- Broadening the walkthrough-waived exemption beyond journeys literally carrying the
  `**Walkthrough:** waived` marker in `docs/goal.md` — must not become a general "no browser row"
  loophole (TC-8b guards this explicitly).
- The carried, non-blocking backlog items listed in the phase spec's OUT OF SCOPE section
  (J-04 screenshot re-take, J-02/J-03/J-05/J-06/J-08 walkthrough recordings, J-07 recording, the
  two pre-existing red unit tests, cosmetic notes, the iteration-23 throwaway clone,
  `apps/frontend/.next-verify/` tracked in git, J-01's re-check assertion strength,
  `browser_checks_run: false`) and the five older open owner questions — none blocking, do not
  bundle.

## Agents Required
- backend-data: yes — extended VmPeak/VmSize/VmRSS re-measurement (developer + independent
  auditor re-derivation), Addendum 45, byte-identity spot check, zero-write proof,
  `merge_ui_test_results.py`/`goal_gate.py` harness fix + regression tests, deterministic replay
  lane, blueprint note, dev handoff.
- frontend-ux: no — zero UI surface change; J-09's Acceptance waives its walkthrough; the harness
  fix touches no UI surface; all ten Required-still-passing journeys are re-verified through pages
  that already exist.

Frontend Present: no

## Files to Create/Modify
- `runs/goal-market-compass-iter-34/*-samples.csv` (×2) -- developer run + independent auditor
  re-derivation, ≥360s, VmPeak_kB/VmSize_kB/VmRSS_kB every row
- `reports/perf-budgets.md` -- append Addendum 45 only (append-only, `+N/-0`)
- `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` -- walkthrough-waived
  evidence exemption (scoped to the literal `docs/goal.md` marker) + new TC-8a/TC-8b self-tests
- `incredible_auto_dev/scripts/automation/lib/goal_gate.py` -- only if the `_BLOCKED_CELL_RE` raw
  scan (or another mechanism) is found to still force BLOCKED after the merge fix
- `reports/phase-goal-market-compass-iter-34-regression-replay-results.md` -- new deterministic
  replay results (10 required journeys)
- `reports/phase-goal-market-compass-iter-34-ui-test-results.md` -- merged results incl. the new
  J-09 evidence row
- `docs/handoffs/goal-market-compass-iter-34-dev.md` -- new dev handoff
- `runs/goal-session-market-compass/state/blueprint.md` -- informational iter-34 note only
- No files under `apps/frontend/`, `apps/backend/app/engine/warmup.py`, or
  `apps/backend/app/engine/prices.py` should change this iteration.

## Key Test Scenarios
- TC-1: ≥360s sampler run post-`start-backend.sh` boot produces a CSV with ≥360 rows and
  VmPeak_kB/VmSize_kB/VmRSS_kB columns for the single sampled pid.
- TC-2: an independently-run second CSV (fresh boot, auditor-derived, not copied) exists with its
  own ≥360 rows and its own computed max VmPeak_kB.
- TC-3: Addendum 45 states both figures vs the 2,621,440 kB bar and vs Addendum 44's 2,467,888 kB;
  `git diff --stat reports/perf-budgets.md` shows only `+N/-0`.
- TC-4: the plateau `VmRSS_kB`/`VmSize_kB` pair (row where VmPeak_kB last increased) is recorded
  distinctly from the high-water mark, for both runs.
- TC-5: `cmp` over the same 16 before/after `/api/compass`+`/api/dashboard` captures (7 as-of
  values) records "16 compared, 0 differing" (or the honest non-zero count).
- TC-6: a `mode=ro` control connection refuses `CREATE TABLE` against
  `apps/backend/data/trendora.db`; `.db` mtime + WAL byte-size unchanged before/after both boots.
- TC-7: the merged `reports/phase-goal-market-compass-iter-34-ui-test-results.md` carries a J-09
  evidence row citing Addendum 45 + CSV paths, non-BLOCKED verdict, AND `goal_gate.py results`
  against it exits 0 (observed and recorded, not assumed).
- TC-8: new regression test proves (a) a synthetic waived-marker journey with cited evidence →
  non-BLOCKED, and (b) a synthetic journey without the marker, missing/SKIP-only → still BLOCKED.
- TC-9: all ten Required-still-passing journeys PASS via the replay lane; every
  `journey-scripts/*.json` mtime predates this iteration's replay-run timestamp (third clean
  golden-hygiene round).
- TC-10: dev handoff states the actual dispatched depth explicitly, cross-checked against the
  `.steps/` markers (`auditor.done`, a QA/browser-qa completion marker, `closure.done`,
  `ux-regression.done`) at `runs/goal-session-market-compass/iter-34/.steps/`; any demotion
  disclosed per `docs/goal.md:2423-2436`, never silent.
- TC-11: targeted pytest for changed files (`merge_ui_test_results.py`'s self-test, any sampler
  script test) reports 0 new failures; the two pre-existing unrelated red tests are named
  explicitly as carried in the dev handoff.
