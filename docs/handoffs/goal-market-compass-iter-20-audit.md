# goal-market-compass-iter-20 Audit Report

**Date:** 2026-08-26
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-11 Stage E genuinely achieved its goal: the live, additive-only write inserted exactly 16,592
`ForwardReturn` rows onto the eleven Stage-D-rebuilt incident runs, touched no other table, minted no
`ScannerRun`, preserved every no-lookahead invariant, and was reported in the exact terminal-state
vocabulary the owner ruling requires. I re-derived every load-bearing figure myself, read-only against
the live 8.4 GB database, and each one held. The three prior lanes' central conclusion — that zero
retained-run holes existed, so zero retained-run insertions was correct — is **true**, and I confirmed it
two independent ways, one of them stronger than any lane produced; but the calendar-geometry reasoning
all three presented as the proof is not exhaustive over the real per-symbol measurement geometry, and one
DEFINITION-OF-DONE test scenario (TC-6) was claimed as covered while being proven by neither a test nor
the live run. That claim is corrected and the coverage added during this audit. The remaining gaps are
evidence-strength shortfalls against the DoD's literal wording — they matter for Stage G, not for the
correctness of what shipped.

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap): the "unrestamped" preflight check never compares `created_at`, and a duplicate run on an incident date could evade it**

`apps/backend/app/engine/j11_stage_e_execute.py:120-158`. The DEFINITION OF DONE requires the eleven
Stage-D runs be proven "present, unrestamped (same id, same `asof_date`, same `created_at`)". The
function captures `observed_created_at` at line 152 but the verdict at line 155 is
`present and id_matches and identity_matches and zero_forward_returns` — `created_at` is recorded and
never compared. Separately, the row is fetched at lines 134-137 with
`select(...).where(ScannerRun.asof_date == one_date)` followed by `.first()`, with no `ORDER BY` and no
assertion that exactly one row matches; a second `ScannerRun` minted on an incident date could be
returned or skipped nondeterministically.

Both are benign in fact, and I verified so rather than assuming: live query returns exactly one run per
incident date (ids 3148–3158, one row each), and their `created_at` values span
`2026-08-26 10:52:55.552946` → `10:53:02.010362`, byte-matching the window iteration 19 recorded. The
finding is that the *check* is weaker than the spec, not that the *state* drifted. This matters because
Stage F and Stage G will reuse this same preflight, and the coordinator's own standing warning is that
`scanner.resolve_run` remains unguarded from any `?as_of=` read path — precisely the mechanism that could
mint a duplicate incident-date run between now and Stage G. Not fixed: the module is already-executed
live code whose persisted evidence corresponds to it as written; changing it now would decouple the
evidence from the code for no live benefit. Recommended for the Stage F/G preflight instead.

**B2 — GAP (gap): mutation-accounting evidence is weaker than the DoD's wording for five of the eight out-of-scope tables**

`apps/backend/app/engine/j11_stage_e_execute.py:526-549`. The DoD claims zero writes to every table
outside `forward_returns`, "proven by before/after full-table sweep plus the whole-file mtime/size/WAL
bracket as the primary instrument". Tracing what each instrument actually proves:

- **Genuinely content-compared** (strong): `scanner_runs` (full per-row `id`/`asof_date`/
  `engine_identity`/`created_at` payload equality, line 539-542), `next_session_manifests` and
  `maintenance_boundaries` (`migration.diff_dumps`, per-row per-column, lines 536, 548), and
  `daily_prices` (`capture_pre_reset_inventory`'s fingerprint includes
  `SUM(open+high+low+close+volume)` — `j11_maintenance.py:166-185` — so any value change moves it).
- **Not content-compared**: `scanner_results`, `sector_scores`, `theme_scores` are covered only by
  `capture_full_table_sweep`, whose own docstring (`j11_maintenance.py:247-253`) states it "would NOT be
  caught by this sweep alone" for a same-`rowid` content UPDATE; and `data_provider_runs` / `watchlist`
  use `j11_stage_c.small_table_id_snapshot` (`j11_stage_c.py:434-440`), which returns `{count, ids}` —
  an id set, not column values.

The designated *primary* instrument cannot close this: the db-file bracket recorded identical
`size_bytes` (8,365,871,104) at both ends, so it establishes only that *a* write happened in the expected
window, never which table. TC-4 asks specifically for `scanner_results`/`sector_scores`/`theme_scores`
row identity byte-unchanged; row count plus rowid aggregate is not that. No live consequence here — the
sole write path is `backfill_run_forward_returns`, whose exclusive use the reviewer AST-proved and which
by construction touches no other table — but Stage G is the acceptance gate that must make this claim for
real, and it will need a content-level instrument for those five tables.

**B3 — GAP (gap): the cross-iteration sweep corroboration the spec asked for was skipped silently, and this iteration propagates the same gap forward**

The spec's BACKGROUND ("Lessons applied") required applying iter-19/19b's cross-iteration-diff technique
where iteration 19 left a reusable end-state artifact, and — if none exists — to "state that gap honestly
rather than skip the corroboration silently". No artifact of this iteration does either: grepping the dev
handoff, review report and QA report for `cross-iteration|previous iteration|raw sweep|corrobor` returns
zero matches. Compounding it, `j11-stage-e-execute-mutation-accounting.json` persists only
`table_sweep_diff` — the *diff* — and not the raw pre/post `per_table` sweeps, so iteration 20 reproduces
for Stage F/G exactly the gap iteration 19 created for it.

I performed the corroboration myself, and it passes cleanly. Against
`runs/goal-market-compass-iter-19/j11-stage-d-execute-mutation-accounting.json`'s recorded post-state,
compared to iteration 20's pre, iteration 20's post, and a fresh live read just now — four points:

| value | iter-19 post | iter-20 pre | iter-20 post | live now |
|---|---|---|---|---|
| `daily_prices` row_count | 3,310,374 | 3,310,374 | 3,310,374 | 3,310,374 |
| `daily_prices` id_sum | 5,479,295,003,075 | same | same | same |
| `daily_prices` ohlcv_sum | 52,367,098,848,872.56 | same | same | same |
| `data_provider_runs` count | 549 | 549 | 549 | 549 |
| `watchlist` count | 6 | 6 | 6 | 6 |
| `scanner_runs` legacy+null | 3,117 | — | — | 34 + 3,083 = 3,117 |

The last row reconciles exactly: 3,117 legacy/null-stamped runs + 11 Stage-D runs stamped `53d2ffd1…`
= 3,128 total, which is both iteration 19's certified end state and the live count now. Nothing drifted
between the two iterations. This is a documentation/evidence gap, not a state problem — and the spec
itself pre-declared it "not blocking".

**B4 — GAP (gap): the CLI's outcome marker is not written on a mid-loop failure, contrary to its own docstring**

`apps/backend/scripts/run_j11_stage_e_execute.py:29-31` states the final outcome is "written
UNCONDITIONALLY as the LAST evidence artifact … never a bare non-zero exit with no persisted outcome
record". The `_stop()` helper (lines 221-231) delivers that for a preflight refusal, but the repair loop
at lines 296-297 has no `try`/`except`: an exception mid-loop propagates out of `main()`, so
`j11-stage-e-execute-outcome.json` and `-db-file-true-end.json` are never written and the terminal-state
lines are never printed. The DoD's `STAGE E COMPLETE: NO` branch requires "full evidence preserved" —
every pre-write checkpoint *is* eagerly persisted, so the forensic trail survives, but the docstring's
unconditional claim is inaccurate. Stage E's idempotent-retry semantics make the consequence mild; the
same idiom carried into Stage F/G (which may not be idempotent) would not be mild.

**B5 — OBSERVATION (gap): 16,566 rows were deleted by the incident; 16,592 were restored, and no artifact reconciles the +26**

The incident's own audit record (`data_provider_runs` id=538) records
`"forward_return_count": 16566` cascade-deleted alongside the 11 snapshots. Stage E inserted 16,592.
The difference is expected and correct — the raw-bar basis changed between the incident and the repair
(J-10 recovery and the AVB corrections), so the set of *currently derivable* (run, symbol, horizon)
combinations is not the set that existed pre-incident, and AG-17 requires the repair reflect current
data rather than resurrect the old rows. But no artifact in this iteration states this, and Stage G's
acceptance gate will be asked whether the repair is "complete" — a question that cannot be answered
against 16,566 without this reconciliation being on the record. Recording it here so it is.

**B6 — OBSERVATION (gap): unused import**

`apps/backend/app/engine/j11_stage_e_execute.py:82` imports `j11_stage_d_execute as jsde`; `jsde` appears
nowhere else in the module (the actual reuse of `recheck_maintenance_boundary_and_guard` happens in the
CLI script's own import at `run_j11_stage_e_execute.py:65`). The module docstring's claim that the
function is "REUSED directly" is true of the iteration, not of this file. Matches the reviewer's NOTE.

**B7 — OBSERVATION (gap): the retained blocked-attempt marker still carries a stale terminal-state block**

`runs/goal-market-compass-iter-20/j11-stage-e-live-execution-blocked.json` ends with a `terminal_state`
object reading `"J-11 STAGE E COMPLETE": "NO"`. It is disclaimed twice above it — `"SUPERSEDED": true` at
the top, and a `superseded_by` field that says explicitly "everything from 'attempted_command' through
'terminal_state' below describes that first, blocked attempt and is no longer the current status". I
checked the retained record against the corrected handoff line by line and they tell a consistent, honest
story: the file's `zero_writes_proof.forward_returns_count_unchanged: 6797728` is in fact a *third*
independent source for the pre-run baseline, agreeing with the pump's own measurement and with iteration
20's mutation accounting. Keeping it is right (AG-17 forbids deleting the incident record). The only
residue is that a naive grep for terminal-state vocabulary across `runs/` would surface a stale `NO`.

### Test Findings

**T1 — IMPORTANT (fixed): TC-6's retained-run refill path was proven by no test and by no live evidence, while the handoff claimed fixture-level proof for every scenario**

The reviewer and QA both flagged that TC-15 (`test_j11_stage_e_execute.py`) asserts only the composite
`all_checks_pass` and that `never_decreased` is vacuous there from an empty pre-count. The problem was
larger than either reported. The *other* test — then named
`test_tc5_tc6_tc8_repair_loop_fills_both_hole_populations_and_leaves_immature_absent` — claimed TC-6 in
its own name, yet its only retained-run assertion was on a **classification string**:
`assert per_run[retained_run_id]["classification"] == "retained_run"`. It asserted nothing about a row
being inserted. Worse, its justifying comment read "the live run's own before/after population-report
proves the incident-cascade hole-fill live" — which is **false**: the live run inserted zero rows on
retained runs, so the live evidence exercises that path no more than the fixture does. I also checked the
fixture geometry directly: that test's retained run sits at `incident_asof - 40 days`, whose horizons
(1/5/10/20/60 over consecutive calendar-day bars) land on 04-03/04-07/04-12/04-22/06-01 — not one of them
an incident date, so it never constructed a population-B row at all.

Net effect: `execute_stage_e_repair_loop`'s retained-run fill path and
`live_verify_three_populations`'s population-B accounting had **zero asserting coverage**, while the dev
handoff stated "fixture-level proof for every scenario". Ranked IMPORTANT rather than GAP because a
spec'd DoD/TESTING-REQUIREMENTS scenario was claimed covered and was not, and because a test whose name
and comment both overstate coverage actively misleads the Stage F/G lanes that will build on it — I was
genuinely unsure between IMPORTANT and GAP here and took the higher level, per the rubric.

**Fix applied.** Test-only; no production code touched, no database interaction:

1. Added `test_tc6_retained_run_incident_dated_hole_is_refilled_and_reported_in_population_b`
   (`tests/test_j11_stage_e_execute.py:428-497`). It builds **two** retained runs 5 days before the first
   two real `INCIDENT_DATES` members (so horizon 5 measures into 2026-05-12 / 2026-05-13), backfills both
   through the module's own loop, then **deletes** one incident-dated row to manufacture a genuine
   defensive-sweep hole while leaving the other intact — the second run is what makes the pre-map
   non-empty, without which `never_decreased` is vacuous over `all([])`. It then asserts the deleted row
   comes back, that `rows_inserted_on_retained_runs == 1` (the counter is real, not hardwired), that the
   already-complete run inserts 0, and that population B's live `post_total` grew from a real
   `pre_total` of 1 to 2 with `post_by_run_id` exactly right.
2. Tightened TC-15 with the explicit assertion the reviewer recommended
   (`tests/test_j11_stage_e_execute.py:832`): `population_b_retained_run_holes["post_total"] > 0`.
3. Corrected the false comment and the overstated test name
   (`tests/test_j11_stage_e_execute.py:380`, `:412-417`) so the file no longer claims coverage it does
   not provide, and points at the new test instead.
4. Updated the dev handoff's now-stale claims (test counts, and the "fixture-level proof for every
   scenario" sentence, which now excepts TC-6 and cites this finding).

**Verification of the fix** — evidence, not assertion:

- `apps/backend/.venv/bin/python -m pytest tests/test_j11_stage_e_execute.py
  tests/test_j11_stage_e_execute_cli_script.py -q` → **55 passed** (was 54; +1 new test, zero regressions).
- **Mutation check** — a test that passes must be shown able to fail. I temporarily replaced
  `retained_inserted = sum(...)` in `execute_stage_e_repair_loop` with a hardwired `0` and re-ran the new
  test alone: it **failed** on
  `assert result["rows_inserted_on_retained_runs"] == 1` → `assert 0 == 1`. The module was then restored
  from a byte-identical backup (`diff -q` silent) and the full suite re-run: **55 passed**. The new test
  therefore genuinely catches the defect class the old one could not.
- Scope re-read: the only file I modified is `apps/backend/tests/test_j11_stage_e_execute.py` (plus the
  handoff correction). `j11_stage_e_execute.py` and `run_j11_stage_e_execute.py` are byte-unchanged from
  the versions the live run executed.

**T2 — GAP (gap): three further checks in the module have narrow or vacuous failure surfaces**

The coordinator asked whether the reviewer's tautology (`population_a_pre_was_zero` at
`j11_stage_e_execute.py:422`, comparing the hardcoded `"pre": 0` from line 370 against 0) repeats
elsewhere. I enumerated every boolean check in the module. It does, twice more, plus one near-vacuous
assertion:

- **`population_c_latest_run_observable_ceiling_respected`** (`:416`):
  `observable_horizon_count > 0 or latest_run_fr_count == 0`. This auto-passes for *any* database whose
  latest run has even one elapsed horizon — it asserts nothing about row counts in that case. It was
  substantive in this run only by accident of timing: run 3158 sits exactly on the frontier
  (2026-08-12), so `observable_days == 0` and the check really did require zero rows. Once the data
  frontier advances, Stage F/G reusing it get a free pass. The in-code comment is honest about the
  limitation, which is why this is a GAP and not a correctness defect.
- **`population_b_never_decreased`** (`:381-383`): `all(...)` over `pre_retained_hole_counts_by_run`,
  vacuously true on an empty mapping — which is exactly the state in every fixture test that existed
  before T1's fix. It was real in production (24 live per-run counts compared). Note also that this is an
  anti-regression check, not the completeness check TC-6 specifies ("a row present for every (retained
  run, symbol, horizon) combination whose horizon is now elapsed"); no code in this iteration verifies
  that stronger property.
- **The B4-style hard assertion** (`:304-311`) compares `COUNT(*)` against the row set fetched by the
  same function on the same session with nothing in between, so it can only fire on a concurrent writer.
  The plan's intent was to catch a *caller-narrowed subset*, but the function takes no caller-supplied
  run list, so there is nothing to narrow. Defensive, near-zero failure surface.

For balance, the checks that carry the actual weight are sound and fail closed: the preflight's
`zero_forward_returns` (`:144`) genuinely queried all 11 runs live and per-date before the write — that,
not the line-422 tautology, is what proves population A's `pre` was zero;
`confirm_stage_d_runs_present_unrestamped` fails closed on an empty expected-map via `bool(per_date)`
(`:157`); `confirm_manifests_unchanged` fails closed on a missing baseline because `diff_dumps` reports
24 `extra_ids`; and `forward_returns_delta_reconciles_with_self_reported_total` (`:552-554`) is a real
and decisive reconciliation. Not fixed, deliberately: these live in already-executed code whose persisted
evidence corresponds to it as written. They should be tightened when Stage F/G forks this module.

---

## 3. Domain Assessment

**The write itself is correct, and I did not take anyone's word for it.** Independent read-only
re-derivation against `apps/backend/data/trendora.db`:

- `forward_returns` = **6,814,320**, against a pre-run 6,797,728 attested independently by three sources
  (the pump's own pre-run measurement, iteration 20's mutation accounting, and the blocked-attempt
  marker's own pre-run read). Delta **+16,592**, matching the loop's self-report exactly.
- Per-run counts on 3148–3158: 2771, 2769, 2216, 2215, 1659, 1658, 1103, 1103, 549, 549, **0** — every
  figure matching the three lanes' reports.
- **The strongest single piece of corroboration, which no lane reported:** the 16,592 new rows occupy the
  id range 6,844,114–6,860,705, a **perfectly contiguous block of exactly 16,592 ids** ending at the
  table's maximum. Nothing else was inserted into `forward_returns` during that window, and nothing was
  inserted after.
- **No-lookahead (AG-5), confirmed independently:** zero rows among the 16,592 with
  `measured_date <= asof_date`, and — a check no lane ran — zero rows whose
  `forward_returns.asof_date` disagrees with their `scanner_runs.asof_date`.
- **Horizon geometry is self-consistent:** distinct horizons per rebuilt run decrease monotonically
  toward the frontier — 5, 5, 4, 4, 3, 3, 2, 2, 1, 1, 0 — exactly the shape `observable_horizons`
  dictates. Run 3158 at the frontier correctly carries zero.
- **No collateral damage:** exactly one `ScannerRun` per incident date (no duplicates), total 3,128,
  `created_at` matching iteration 19's window byte-for-byte, manifests 24, boundary `active=1`,
  `daily_prices` aggregate identical across four measurement points (see B3).

**The retained-run question (the load-bearing claim): the conclusion is right, the published reasoning is
not the proof.** Developer, reviewer and QA all concluded that zero insertions on 3,117 retained runs was
correct, via a 15-combination calendar enumeration (5 horizons × the 3 frontier-adjacent incident dates),
each resolving to a rebuilt run or to no run. I verified the conclusion two ways:

1. **Empirically.** A fresh grouped scan of every `ForwardReturn` whose `measured_date` is an incident
   date and whose `run_id` is not 3148–3158 returns exactly 16,614 rows across exactly **8** dates
   (05-12: 2,770 · 05-13: 2,216 · 07-10: 2,769 · 07-13: 2,217 · 07-24: 1,660 · 07-27: 1,660 · 08-03:
   1,662 · 08-05: 1,660). **Zero** rows measure into 2026-08-10, 08-11 or 08-12 — the only dates where a
   cascade-created hole could sit. Total matches the lanes' 16,614 exactly.
2. **Structurally — and this is decisive in a way the calendar argument is not.** Reading the deletion
   path rather than reasoning about dates: `data_manager._cascade_targets`
   (`apps/backend/app/engine/data_manager.py:1967-2011`) invalidates a `ScannerRun` when **any** of its
   `ForwardReturn` rows has `measured_date` among the removed bar dates (condition (b), lines 1974-1976),
   and `remove_price_data` then deletes that run's forward returns **whole** (line 2174). A run that
   would have suffered a partial hole is therefore deleted entirely and becomes an incident date; the
   defensive sweep at lines 2189-2192 provably operates on an already-empty set, as its own comment
   states. **A retained run carrying an incident-created forward-return hole is structurally impossible**
   — independent of calendar geometry, horizon set, or which dates were removed. The incident's own audit
   record (`data_provider_runs` id=538) closes the loop: `removed_first` 2026-08-11, `removed_last`
   2026-08-12, cascade `run_ids` exactly 11, `snapshot_dates` exactly the 11 `INCIDENT_DATES`.

**Where the three lanes' shared reasoning is weaker than presented.** Their enumeration assumes
`measured_date` is "h trading days after `asof_date`" on a single (SPY) calendar. It is not — it is
resolved per symbol. The live data shows this plainly: run 3154 at horizon 1 splits into `measured_date`
2026-08-04 for 428 symbols and 2026-08-05 for 124 (SPY is in the 124-symbol group, whose calendar lacks
2026-08-04). Six of the ten non-empty (run, horizon) pairs at the long end split the same way. A
15-combination single-calendar enumeration is therefore not exhaustive over the real geometry, and three
agreeing lanes reached the right answer partly by a route that does not carry the weight they placed on
it. The conclusion survives because of the structural argument above; it should be recorded that way in
the Stage G record, not as a calendar count.

**Scope discipline held.** `forward_testing.backfill_forward_returns` — the whole-database entry point
that would have minted `ScannerRun`s outside the 11-date boundary — is neither imported nor called
(AST-proven by test, and confirmed live: `scanner_runs` is still 3,128). Maintenance isolation held: the
refusal log at `runs/goal-session-market-compass/iter-20/maintenance-isolation-refusals` records
the browser-QA/replay lane refused at 21:40:14Z, no application service is running, and `git status
--porcelain -uall` returns zero matches against `app/api/*`, `scoring.py`, `sectors.py`, `compass.py`,
`data_manager.py` (TC-19), with zero network-capable references in the new files (TC-20). The terminal
vocabulary is an exact match. My own audit performed no writes: the DB's main file mtime and size are
unchanged from the Stage E run, `-wal` is at 0 bytes, and only the `-shm` sidecar's mtime advanced — the
documented and expected signature of read-only WAL-mode access.

**One anomaly, checked and cleared as out of scope.** Run 1868 (`asof_date` 1996-02-01) carries zero
`ForwardReturn` rows despite decades of subsequent history. Cause: it has zero `ScannerResult` rows, and
`forward_symbols_for_run` falls back to the benchmarks, but SPY and QQQ have no `daily_prices` bars
before 1996-03 — so `close_on` yields nothing. Entirely pre-existing (the run was created 2026-07-26),
outside the incident cascade, and outside Stage E's scope. Recorded so a later lane does not rediscover
it as a Stage E defect. Every other run in the database is horizon-complete for its position relative to
the frontier: 3,080 runs carry all 5 horizons, and the 38 retained runs carrying fewer are **exactly**
the 38 whose `asof_date` falls within 60 trading days of the frontier — an exact count match that
independently confirms the loop behaved correctly across the whole retained population.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_j11_stage_e_execute.py` | Added `test_tc6_retained_run_incident_dated_hole_is_refilled_and_reported_in_population_b` (lines 428-497): manufactures a genuine deleted-row hole on a retained run measuring into a real incident date, keeps a second retained run so the pre-map is non-empty, and asserts the row is refilled, `rows_inserted_on_retained_runs == 1`, and population B's live `post_total` grows 1 → 2 |
| 2 | Important | `apps/backend/tests/test_j11_stage_e_execute.py:832` | Tightened TC-15 with the explicit `population_b_retained_run_holes["post_total"] > 0` assertion the reviewer recommended, so it no longer passes only via a vacuous composite |
| 3 | Important | `apps/backend/tests/test_j11_stage_e_execute.py:380, 412-417` | Removed the false claim that the live run proves the retained-run hole-fill, and corrected the test name that asserted TC-6 coverage it did not provide |
| 4 | Important | `docs/handoffs/goal-market-compass-iter-20-dev.md:47-51, 210, 225-228, 230-232` | Corrected the test counts (54 → 55) and excepted TC-6 from the "fixture-level proof for every scenario" claim, citing this finding |

No production code was modified. No database write of any kind was performed — under maintenance
isolation, any finding requiring a DB mutation would have been reported for the owner rather than acted
on, and none arose.

---

## 5. Recommended Next Step

**Proceed to Stage F.** Stage E's live write is correct, in scope, additive-only, and honestly reported;
`J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE` with the boundary still `ACTIVE` remains the
correct terminal state, and nothing found here calls for redoing Stage E or reopening Stage D.

Carry these four into the Stage F/G specs — none blocks Stage F, but all three of B1, B2 and T2 land on
Stage G, which is the only stage permitted to declare the incident repaired:

1. **Stage G's preflight must compare `created_at` and assert exactly one run per incident date** (B1) —
   the `?as_of=` read path is still unguarded, so a duplicate incident-date run is a live possibility
   between now and then, and the current check would not reliably see it.
2. **Stage G needs a content-level instrument for `scanner_results`, `sector_scores`, `theme_scores`,
   `data_provider_runs` and `watchlist`** (B2). The rowid-aggregate sweep cannot see a same-rowid UPDATE
   and the id-set snapshot cannot see a column change; the acceptance gate should not rest on them.
3. **Persist the raw pre/post `per_table` sweeps, not only their diff** (B3), and state the
   cross-iteration corroboration explicitly. This iteration's own is recorded in B3 above and passes —
   Stage F should start from that rather than re-derive it.
4. **Record the 16,566 → 16,592 reconciliation in the Stage G acceptance record** (B5) before answering
   whether the repair is "complete", and record the retained-run conclusion via the structural
   cascade-predicate argument in §3 rather than the calendar enumeration, which does not survive the
   per-symbol geometry.

Optionally, when Stage F forks this module, tighten the three narrow-surface checks in T2 and drop the
unused import (B6). Those are cleanups, not obligations.
