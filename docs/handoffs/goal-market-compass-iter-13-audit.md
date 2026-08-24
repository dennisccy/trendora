# goal-market-compass-iter-13 Audit Report

**Date:** 2026-08-24
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The owner-authorized Stage C bounded destructive clear was executed correctly and within its narrow
authorization. I did not adjudicate the other three lanes' prose — I re-derived every load-bearing claim
myself against the live database and against iteration 12's **committed** pre-Stage-C baseline
(`runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-after.json`, commit `78df5309`,
working tree clean). Exactly 4 `ScannerRun`s (ids 3114/3148/3149/3150) and their run-owned children were
removed; 19 of the 24 tables are byte-identical in row count; `daily_prices`, all 24 manifests (28 columns
each), the manifest DDL and its three indexes, `data_provider_runs` and `watchlist` are unchanged; zero
orphans; zero residue; zero network activity. **I concur with developer, reviewer and QA: `J-11 STAGE C
COMPLETE: YES`, and `J-11 STAGE D AUTHORIZED: NO`.**

The gaps are not in the deletion. They are in the **evidence narrative** around it: the Stage B2 engine
identity re-derived by the preflight is **not** the value iteration 10 certified, and both the dev handoff
and `assumptions.md` state the opposite (finding B1, IMPORTANT, fixed at audit). Two logged assumptions
carry factually false premises that Stage D/E would otherwise inherit. None of this affected Stage C —
the deletion is deletion-only and reads no identity — but all three prior lanes missed it.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the Stage C preflight's re-derived Stage B2 `engine_identity` is NOT the
certified iteration-10 value, and the handoff reports it as though it were.**

- `runs/goal-market-compass-iter-10/j11-frozen-identity.json` (committed) froze
  `engine_identity = 6261ca1791b59771f3b6b6829142e2cf7c0f33d0fa4ea00a2f1e2c8d1d6b3a6e`.
- `runs/goal-market-compass-iter-13/j11-stage-c-preflight.json` →
  `stage_c_attempt_identity.b2_engine_identity.engine_identity = 53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55`.
- I recomputed it independently at audit: `engine_identity.compute_engine_identity(get_config())` returns
  `53d2ffd1…`. The two values differ.
- **Cause:** `apps/backend/app/engine/compass.py` is one of the three `provenance.engine_files` in
  `config.yaml`, and it changed in commits `a7380009` (iter-11 `basis_disclosure` fix) and `a9e651c4`
  (iter-12). `config_subset_hash` is unchanged at `10bc4504ed9f28961a6342c3306d8a8eaeceac5ec7d233645540dffb0a653614`
  — the drift is code-side only.
- **The claim that contradicts the evidence:** `runs/goal-session-market-compass/state/assumptions.md`
  iter-13 entry #2 predicts byte-identity "since no code/config change has landed since";
  `docs/handoffs/goal-market-compass-iter-13-dev.md:50-52` reported `53d2ffd1…` as a re-derivation "per
  the logged interpretive assumption" without flagging the mismatch. The phase spec's own NOTES
  (`docs/phases/goal-market-compass-iter-13.md:144`) required the developer to "independently re-derive
  both readings … rather than trust these entries verbatim". The value was re-derived; the prediction was
  not.
- **Impact on Stage C: none.** `clear_snapshot_dates` (`apps/backend/app/engine/data_manager.py:2247-2321`)
  is deletion-only and no delete predicate reads an engine identity. It is also not a step-12 violation:
  step 12's invariant is scoped to ONE attempt, and iteration 13 freezes a new Stage C attempt.
- **Impact on Stage D: real.** Two frozen-identity artifacts now exist with different values, and step 12
  says the per-run check compares against "the identity frozen in **that attempt's** pre-reset inventory".
  The live database additionally holds 34 surviving non-incident `scanner_runs` stamped `6261ca17…` and
  3,083 stamped NULL (3,083 + 34 = 3,117, the full surviving population).
- **Fix applied:** corrected the dev handoff's preflight bullet and Known Issues; appended a dated,
  additive auditor correction to `assumptions.md` (56 insertions, 0 deletions — the original entries are
  preserved verbatim, never rewritten). No code change: freezing the *current* identity is precisely what
  step 12 requires of a new attempt.

**B2 — GAP (observation, do not fix here): the preflight comparison gate captures engine and config
identity but never compares either.** `apps/backend/app/engine/j11_stage_c.py:264-334` runs 11 checks;
none touches `stage_c_attempt_identity`. Ruling C2 lists engine identity and config identity among the
mandatory captures and requires a STOP if the fresh preflight "materially differs from the certified
iteration-12 state" — but iteration 12's certified artifact carries no frozen identity, so the comparison
is not merely unimplemented, it is not currently possible. This is why B1 went undetected by the gate,
the reviewer and QA. Harmless for a deletion-only stage; **must be closed before Stage D**, whose entire
correctness claim is the single-identity invariant. Not fixed here: adding the check now would be Stage D
tooling, and it could not be exercised without a second live run, which the authorization forbids.

**B3 — GAP: `assumptions.md` iter-13 entry #1's factual premise is false.** It asserts the
`measured_date`-only forward-return population "is ALREADY absent today". Live read-only count after
Stage C: **16,614** `forward_returns` rows whose `measured_date` lands on an incident date, all owned by
**retained** runs — 2026-05-12: 2,770 · 05-13: 2,216 · 07-10: 2,769 · 07-13: 2,217 · 07-24: 1,660 ·
07-27: 1,660 · 08-03: 1,662 · 08-05: 1,660. The **decision** the entry reached (delete only `run_id`-owned
rows) is exactly what rulings C6/C7 require and is exactly what the code does, so the wrong premise
produced the right action. Corrected in the same auditor note, because Stage E must not inherit it: those
16,614 rows are retained-run history C6 forbids deleting, and are a different population from the "holes
on retained runs" Stage E repairs.

**B4 — OBSERVATION: SQLite foreign-key enforcement was OFF during the live run, correctly.**
`config.yaml` `database.pragmas` sets `journal_mode/synchronous/busy_timeout/cache_size/mmap_size/temp_store`
and not `foreign_keys`, so `app/db.py:_apply_sqlite_pragmas` leaves it at SQLite's default (my read-only
connection confirms `PRAGMA foreign_keys = 0`). The child-before-parent ordering was therefore not
DB-enforced live. That is acceptable and in fact compliant: goal.md's step-11 rule is that "J-11 must not
rely on SQLite foreign-key enforcement being disabled as part of its safety", and the fixture tests set
`PRAGMA foreign_keys=ON` (`tests/test_j11_stage_c_bounded_clear.py:36-40`), so the ordering is proven
correct under enforcement. Post-run orphan count is 0 in all four child tables. No action.

**B5 — GAP: DoD item "All new code, tests, and evidence artifacts are committed to git" is not met at
audit time.** All Stage C code, tests and evidence are untracked; `data_manager.py`, `goal.md` and the
session state files are modified-uncommitted. There is no SHA to cite, which is the evidence floor for a
"committed" claim (`.claude/judgment-rubrics.md` §5). This is the session's normal pipeline ordering (the
iteration-close commit follows the audit — cf. `48e83a8e` / `78df5309` for iteration 12) and the handoff
makes no false claim about it. Recorded so the closing commit is not skipped.

### Frontend Findings

None. No frontend file exists in the diff, no service was booted, no browser lane ran — verified by
`git status` on `apps/frontend/` (clean) and by `pgrep` finding no `uvicorn`/`next` process. Maintenance
isolation held.

### Test Findings

**T1 — GAP: TC-4's fixture test asserts the `daily_prices` row count but not the content fingerprint that
TC-4's own wording requires.** `tests/test_j11_stage_c_bounded_clear.py:154-156` checks only
`result["bars_before"] == result["bars_after"]`, and `clear_snapshot_dates`
(`data_manager.py:2268, 2287-2291`) computes only a `COUNT(*)` — the spec's IN SCOPE bullet asked the
function to assert "the row count **AND** the same content fingerprint". The substantive guarantee still
holds: the fingerprint is computed pre/post at process level
(`scripts/run_j11_stage_c_bounded_clear.py:175, 190` → `build_mutation_accounting`'s
`daily_prices_unchanged` check, which gates the completion marker), and I independently confirmed the live
fingerprint `572691772b7313b893055a9ada984945292bbcd07686f4702193a03e9223451a` is byte-identical to the
committed iteration-12 baseline. Unit-level assertion only is thinner than specified.

**T2 — GAP: only 2 of the comparison gate's 11 invariants have a negative test, and the positive test is
a self-diff.** `tests/test_j11_stage_c_preflight.py:140-148` sets `certified = copy.deepcopy(preflight)`,
so the pass case is tautological. Negative coverage exists for `manifest_row_count` (line 150) and
`per_date_scanner_run` drift (line 162) only. Nothing proves the gate STOPS on manifest DDL drift,
manifest value drift, a changed `source_run_id`, a `daily_prices` fingerprint change, or a reintroduced
live FK — the five checks that most directly protect Layer 3. Those five all passed on the live run and I
re-derived each one independently, so the iteration's own result is sound; the *gate's* fail-closed
behaviour on them is unproven.

**T3 — GAP: the `--confirm` refusal and the script's non-zero-exit paths are untested.** The TESTING
REQUIREMENTS name "verification-fail ⇒ no marker + non-zero exit"; the tests cover only the helper level
(`stage_c_overall_verdict`, `build_completion_marker` raising). The script's four `return 1` paths
(`run_j11_stage_c_bounded_clear.py:134, 148, 159, 235`) and its no-database-interaction-without-`--confirm`
refusal (lines 86-93) are correct by inspection but have no test. Since the authorized destructive run has
already executed once and must not be repeated, this cannot be closed by exercising it now — but the same
idiom is the safety skeleton Stage D will reuse.

**T4 — OBSERVATION: 42 targeted tests pass.** I ran them myself rather than citing the handoff:
`apps/backend/.venv/bin/python -m pytest tests/test_j11_stage_c_bounded_clear.py
tests/test_j11_stage_c_preflight.py tests/test_j11_maintenance.py tests/test_j11_stage_b1_migration.py -q`
→ `42 passed in 1.72s`, single process, in-memory `sqlite://` fixtures only, never the live database.

---

## 3. Domain Assessment

**The deletion mechanism cannot over-reach, and I verified that structurally rather than trusting the
accounting.** `clear_snapshot_dates` (`data_manager.py:2247-2321`) deletes only via
`ForwardReturn/ScannerResult/SectorScoreRow/ThemeScoreRow.run_id == <one resolved run id>` and
`ScannerRun.id == <that id>`. Three structural facts close the escape hatches:

1. **No twelfth date is reachable.** The only production caller is
   `run_j11_stage_c_bounded_clear.py:183`, which passes the module constant `INCIDENT_DATES` — there is no
   date CLI argument, no range, no cadence inference. `grep` confirms no other caller exists anywhere in
   the repo. `clear_snapshot_set()` is never called by the new code; its one pre-existing call site
   (`data_manager.py:5930`, the J-85 rebuild) did not run — had it run, all 3,121 runs would be gone.
2. **The date list is gated against the contract, not asserted in prose.** I re-ran
   `check_c1_date_set_boundary` against the **live** `docs/goal.md` myself: the authoritative "incident
   date set — all 11" bullet, the C1 restatement, and the code's `INCIDENT_DATES` are all three byte-
   identical, and the extracted contract hash `6fbefa8c4ee9e121638fd4be1a570092ec82e8402cd4803630b9fbb9810f65e1`
   matches the preflight artifact. The extraction is anchor-based and fails closed (`ValueError`) rather
   than guessing from a broad date pattern, with negative tests for both a disagreement and a missing
   anchor.
3. **Under-deletion is impossible and the child set is complete.** The live schema carries
   `CREATE UNIQUE INDEX ix_scanner_runs_asof_date ON scanner_runs (asof_date)`, so `.first()` cannot leave
   a second run behind on a date. `PRAGMA foreign_key_list` over all 24 tables returns exactly four tables
   referencing `scanner_runs`, all `NO ACTION` — no cascade — and the database has **0 triggers and
   0 views**, so deleting the parent row can have no hidden side effect. The four are precisely the four
   the code deletes.

**The over/under-deletion proof is a genuine ID-set diff, and I closed it arithmetically myself rather
than relying on the aggregate fingerprint.** Against the *committed* iteration-12 baseline, exactly five
tables moved and by exactly the enumerated amounts: `scanner_runs` 3,121→3,117 (−4), `forward_returns`
6,800,539→6,797,728 (−2,811), `scanner_results` 1,327,944→1,325,785 (−2,159), `sector_scores`
96,751→96,627 (−124), `theme_scores` 34,331→34,287 (−44). All **19 other tables are identical** — including
`market_phase_cache` (1,290), `forward_aggregate_cache` (333), `event_study_cache` (18),
`import_checkpoints` (37), `macro_series` (5,428), `stocks`, `etfs`, `sectors`, `themes`, `theme_members`.
The intended-delete-set enumerates every removed id explicitly (2,811 unique `forward_returns` ids, etc.),
and post-delete the residue for run ids {3114,3148,3149,3150} is 0 in every child table. **Delta ==
|enumerated set| AND residue == 0 ⇒ the removed set is exactly the enumerated set** — an unchanged count
could not have masked a swap, because Stage C issues no INSERT on any path.

**The C7 forward-return boundary held, and this is the sharpest check available.** Comparing the
preflight's per-date `forward_returns_measured_into_count` against my live post-run counts: seven of the
eleven dates are byte-identical, and only the four whose rows were owned by a deleted run moved (05-13
2,771→2,216 = −555 · 08-10 124→0 · 08-11 20→0 · 08-12 20→0). Those 719 rows are a **subset** of the 2,811
`run_id`-owned rows removed — no `measured_date`-keyed deletion occurred. The 16,614 rows measured into
incident dates from retained runs survive untouched, which is exactly what C6's "do not delete unrelated
derived history merely because it references an affected measured date" demands and what C7 reserves for
Stage E.

**Layer 3 is provably byte-invariant.** I recomputed the manifest comparison myself, type-normalizing
SQLite's raw storage against the committed iteration-12 typed dump: **all 24 rows × 28 columns identical,
zero diffs**. Manifest ids are contiguous 1-24 (nothing minted, nothing deleted); `prospective_eligible`
is 0 on all 24 rows (nothing upgraded — AG-17); per-`as_of` version ordinals are unchanged (nothing
re-versioned — AG-12/AG-18); manifest DDL sha256 `9f653c8147c7c8931b07ea4a88d46ef1d6ddefb2ef5177b700d2b60e7fc501ee`
and all three indexes are byte-identical to the certified capture (no further drift beyond the four
owner-accepted iter-11 residuals — AG-18). Manifest counts on incident dates are unchanged at 08-05: 2,
08-10: 1, 08-11: 3, 08-12: 6, and **no historical manifest was created for the seven dates that have none**
(C8). Notably, the 12 manifests with an unresolvable `source_run_id` point at runs 3112/3048/3049/3081 —
**none of the four ids deleted this iteration** — so Stage C created no new orphan and "repaired" no
existing one, exactly as C3 requires. `create_db_and_tables()` / `_apply_additive_columns` were never
called: the script uses `get_engine()` only, which creates the engine and applies session PRAGMAs and
nothing else (`app/db.py:80-91`) — the iteration-11-class DDL residual has no path here, and the
byte-identical DDL confirms it empirically.

**Zero network activity, confirmed two ways.** No `requests`/`urllib`/`httpx`/`yfinance`/`socket` import
appears anywhere in the new module or script, and `data_provider_runs` is unchanged at 549 rows with an
identical id set — every real fetch in this codebase appends a provider-run row. J-10 stayed closed.

**The write boundary is honest.** Iteration 12's committed `db_file_mtime_after_capture`
(1787522416.2308807) equals iteration 13's true-start mtime exactly, proving nothing wrote to the database
between the two iterations. The true-end mtime is 1787591622.4277432 (2026-08-24T17:13:42Z) — and the file
**still carries that exact mtime and size right now**, so nothing has written to it since Stage C
finished; every subsequent check by reviewer, QA, the coordinator and me was genuinely read-only. `-wal` is
0 bytes and no process holds the file open for write. The completion marker (17:13:44.533848Z) is strictly
after the mutation accounting (17:13:44.533268Z), and `build_completion_marker` refuses to construct a
marker on a non-passing verdict at all. `run.log` is a single linear transcript — one attempt, no retry,
no "resume from halfway".

**Scope held.** `git status` on the six forbidden paths (`scanner.py`, `forward_testing.py`, `research.py`,
`j11_schema_migration.py`, `models.py`, `apps/frontend/`) is clean. The only modified tracked files are
`data_manager.py` (+88/−1, purely the new function plus one `typing` import line) and `docs/goal.md`
(+95/−0, exactly the owner's own authorization block, no deletion, no redesign — C12 holds). No Stage
D/E/F/G work leaked in.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `docs/handoffs/goal-market-compass-iter-13-dev.md` | Corrected the preflight bullet's engine-identity claim: states that `53d2ffd1…` is **not** iteration 10's certified `6261ca17…`, names the cause (`compass.py` changed in `a7380009`/`a9e651c4`; `config_subset_hash` unchanged), states that Stage C is unaffected, and names the Stage D consequence. |
| 2 | Important | `docs/handoffs/goal-market-compass-iter-13-dev.md` | Replaced "Known Issues: None discovered" with the two audit findings (B1 identity drift; B3 the false `measured_date` premise, with the 16,614-row breakdown). The original "every gate passed on the first live attempt" statement is retained — it is true. |
| 3 | Important | `runs/goal-session-market-compass/state/assumptions.md` | Appended a dated auditor correction covering both iter-13 entries (56 insertions, **0 deletions** — the original entries are preserved verbatim, per AG-17's "incident evidence is never rewritten"). |

**Post-fix verification.** The fixes are documentary, so verification is re-derivation of every figure I
wrote, not a test run. All re-confirmed after editing:
`iter10 6261ca17… ≠ iter13 53d2ffd1…`; `compute_engine_identity(get_config())` → `53d2ffd1…`;
`config_subset_hash` equal on both sides (`10bc4504…`); `git log -- compass.py` → `a9e651c4`, `a7380009`;
surviving run stamps 34 × `6261ca17…` + 3,083 NULL = 3,117; measured-into pre/post table showing 16,614
surviving and 719 removed with only the four deleted-run dates moving. `git diff --numstat` on
`assumptions.md` = `56 0` (additions only). No code, test, database or `docs/goal.md` content was touched
by these fixes, and the live database mtime is unchanged by the audit.

---

## 5. Recommended Next Step

**Report to the owner and STOP the engine, exactly as ruling C10 directs.** Return:

- **`J-11 STAGE C COMPLETE: YES`** — I concur with developer, reviewer and QA, on independently
  re-derived evidence rather than on their reports.
- **`J-11 STAGE D AUTHORIZED: NO`** — confirmed. Successful Stage C is not implicit authorization for
  Stage D; a separate, fresh owner instruction is required, and the next decomposer must wait for it the
  way this one waited for C's.

Before any Stage D iteration is planned, three items from this audit must be resolved — none of them is
Stage C work and none should be pulled into this iteration:

1. **Decide which frozen identity Stage D's step-12 check compares against** (B1). Two artifacts now hold
   different values, 34 surviving non-incident runs carry the older stamp, and the correct answer is almost
   certainly "the Stage D attempt's own freshly frozen identity, with the surviving runs' stamps left
   untouched" — but the owner/contract should say so, not the developer.
2. **Close the preflight gate's identity blind spot** (B2) before a stage whose correctness claim *is* the
   single-identity invariant, and capture a frozen identity into the certified baseline so the comparison
   becomes possible.
3. **Close the test gaps T2/T3** in the safety skeleton Stage D will reuse — negative tests for the
   remaining nine gate invariants, and a subprocess-level test of the `--confirm` refusal and the
   non-zero-exit-without-marker path.

Also pending, and purely mechanical: the iteration-close commit (B5) — no Stage C code, test or evidence
artifact is in git yet, so no SHA can be cited for the "committed" DoD item.

Carried forward unchanged and correctly untouched this iteration: the two C11 framework findings
(`goal_gate.py` duplicate J-ID hashing; the manifest-migration live-vs-model column-list defect), the AVB
restored-price / un-rescaled-volume mismatch on 2026-08-11/12, the five older non-blocking owner
questions, and the unfixed forbidden-lane defect in `scripts/automation/`.
