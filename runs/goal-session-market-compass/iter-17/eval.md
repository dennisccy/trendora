# Iteration 17 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

## Summary

The team built exactly what the owner allowed and stopped exactly where the owner said to stop. The safety
catch that is meant to stop the app from writing to the eleven damaged days is now well built, properly
bounded, and covered by 39 passing tests, which I ran myself. Nothing was written to the real database —
I checked the file myself and it has the same timestamp, the same size and an empty write log as before.
But the catch is still switched off on the real database, and switching it on needs a table that does not
exist there. The owner has said that table must not be created yet. So the danger this catch exists to
remove is still fully present: if anyone starts the app today, that single act would both create the
forbidden table and write a new day's results onto 12 August, one of the damaged days. Everything that
would fix this is the owner's decision to make, so the loop stops here.

## Journey Results This Iteration

Browser testing and the automatic replay check were **forbidden by this iteration's contract**
(`reports/phase-goal-market-compass-iter-17-ui-test-results.md` records `Browser QA Verdict: SKIPPED` with
a `**Reason:**` naming maintenance isolation; the engine logged its own refusal in
`runs/goal-session-market-compass/iter-17/maintenance-isolation-refusals` at `2026-08-25T19:33:59Z`).
Under the methodology's maintenance-isolation rule every journey therefore **keeps its prior recorded
status** and none may be promoted. No journey was tested, so none could fail.

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest on new runs | passing | passing (carried, not re-verified) | Spot-check: `reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png` — re-opened; the GRMN row shows a real stored sector ("Consumer Discretionary"), consistent with `passing` |
| J-02 What changed since previous session | partial | partial (carried, not re-verified) | `reports/qa/goal-market-compass-iter-4-evidence/J-02-verify.png` (iter-4) |
| J-03 Plain-English summary with cited facts | partial | partial (carried, not re-verified) | `reports/qa/goal-market-compass-iter-4-evidence/J-03-verify.png` (iter-4) |
| J-04 Candidate why and why-not | passing | passing (carried, not re-verified) | `reports/qa/goal-market-compass-iter-4-evidence/J-04-verify.png` (iter-4) |
| J-05 Close freezes one manifest | partial | partial (carried, not re-verified) | `reports/qa/goal-market-compass-iter-3-evidence/UT-02-manifest-historical-badges.png` |
| J-06 A frozen manifest never changes | partial | partial (carried, not re-verified) | `reports/qa/goal-market-compass-iter-3-evidence/UT-02-manifest-historical-badges.png` |
| J-07 Today page ten-second read | failing | failing (carried, not re-verified) | `reports/qa/goal-market-compass-iter-0-evidence/UT-J-07-fail.png` |
| J-08 Market page moves over intact | failing | failing (carried, not re-verified) | `reports/qa/goal-market-compass-iter-1-evidence/UT-J-08-fail.png` |
| J-09 Backend fits the host | partial | partial (carried, not re-verified) | `reports/perf-budgets.md:12114-12236` |
| J-10 Bounded recovery of two deleted days | passing | passing (carried, NOT re-stamped) | Spot-check: my own read-only query (`mode=ro` + `PRAGMA query_only=ON`) — `daily_prices` holds 585 rows on 2026-08-11 and 585 on 2026-08-12, exactly the owner-accepted terminal state. Iter-15's dollar-volume caveat is now closed by iter-16's correction, which I re-derived: `round(provider_volume / bridge_factor)` reproduces both stored values exactly |
| J-11 Incident-bounded clean regeneration | partial | **partial — advanced** (re-stamped `last_verified_iter` = iter-17; `spec_hash` re-stamped to `8cf4ace6…`, was `e7927ff5…`, because the owner's 2026-08-25 lifecycle ruling changed J-11's text and I re-verified against the current text) | `runs/goal-market-compass-iter-17/j11-iter17-live-preboot-guard-verification.json`, `-readiness-db-file-true-start.json` / `-true-end.json`, `j11-iter17-stage-d-readiness.json`, `j11-avb-bridge-diagnostic.json`; plus my own re-run of `tests/test_j11_preboot_guard.py` + `tests/test_j11_preboot_guard_cli_scripts.py` → 39 passed, and my own read-only re-derivation of every load-bearing figure |

No journey is `pending_infra` (nothing is owed by the browser infrastructure — the contract withheld the
lane) and none is `evidence_makeup` (no capture is defective). No `journeys-changed.md` was emitted; I
re-ran `goal_gate.py hash-journeys` and all ten other journeys' hashes are identical to the recorded ones.

### What I verified myself, rather than taking from a report

- **The live database was not written to.** My own `stat`: mtime `1787670395.652078900`, size
  `8365871104`, `-wal` size `0` — identical to the recorded true-start, true-end and the decomposer's
  pre-iteration baseline.
- **The boot-path exposure (auditor finding B1) is real.** Read-only (`mode=ro` + `PRAGMA query_only=ON`):
  `max(daily_prices.date)` = `2026-08-12`, which is `j11_maintenance.INCIDENT_DATES[-1]`;
  `max(scanner_runs.asof_date)` = `2026-07-23`; all eleven real incident dates carry **0** `scanner_runs`;
  `maintenance_boundaries` is absent from the live `sqlite_master` (24 tables). `apps/backend/main.py`
  calls `create_db_and_tables(engine)` → `SQLModel.metadata.create_all` **before** it calls
  `ensure_latest_snapshot(engine, config)`, and `MaintenanceBoundary` is a `table=True` SQLModel
  (`apps/backend/app/models.py:992`). So one boot mints the forbidden table and then, with that table
  freshly created and empty, `evaluate_boundary_for_date` returns `blocked=False` and
  `warmup.py:121 run_scan(...)` writes a canonical `ScannerRun` onto 2026-08-12.
- **The AG-8 fix is genuine.** Read directly at `j11_preboot_guard.py:173-182` and `:218-228`: filtered to
  `active IS NOT FALSE` (which keeps SQL-`NULL` rows that plain `active == True` would silently drop),
  projected to the four fields the decision reads, bounded `LIMIT 101` **with** a `len(rows) > 100`
  fail-closed return — a bound that is enforced, not one that silently truncates.
- **The arm path is safe by construction.** `INCIDENT_DATES` equals the owner's eleven dates exactly (I
  imported and compared them); the script has no default `--database-url`, validates the date set against
  `docs/goal.md` before touching any database, and refuses with a named STALLED when the table is absent
  (`run_j11_maintenance_boundary_arm.py:116-125`). No `create_all`/`CREATE TABLE` executes in any new
  script.
- **TC-13's headline ratio proves nothing new.** I reproduced it exactly as
  `volume_a × bridge_factor / volume_b` — `close_a` cancels entirely — and confirmed
  `round(provider_volume / bridge_factor)` equals the stored volume on **both** dates (554757 and
  3706010). The ratio can only land at ≈1.0. The `AVB-A` label itself is sound, because it rests on the
  engine-computed decision-impact trace, and both `AVB-A` and `AVB-B` sit in
  `j11_stage_d._AVB_READY_CLASSIFICATIONS:507`, so the correction could not move `READY: YES`.
- **Iteration 16's evidence is untouched.** My own `sha256sum`: `e794dbf2…f7a0138` and `1e35942c…fedb57079`
  — both matching the handoff. Iteration 13's evidence also remains intact
  (`git status --porcelain runs/goal-market-compass-iter-13/` → 0 lines).

## Anti-goal Check

Worked from `runs/goal-session-market-compass/iter-17/scan-report.md` (**CLEAN** — no secret, dependency or
license findings; 5 untracked files scanned) plus `iter-diff.md` (7 files, all shown in full) plus my own
greps over all 7 changed files, tracked and untracked.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language | OK | No Evidence Claim introduced; no ledger append — grep for `append_entry`/`verify_edge`/`forward_walk`/`certified-claims` over all 7 files returns nothing |
| AG-2 decision-quality only | OK | No candidate/market presentation surface touched; no frontend file in the change set |
| AG-3 displayed numbers correct | OK | No displayed value produced or changed; coherence audit independently confirms zero touches to `app/api/*`, `scoring.py`, `sectors.py`, `compass.py` |
| AG-4 no overfit edges | OK | No claim certified or re-scored |
| AG-5 determinism / no-lookahead | OK | No scoring, manifest or forward-return code touched |
| AG-6 referee gate | OK | No Evidence Claim this cycle — gate passes automatically |
| AG-7 credentials | OK | scan-report CLEAN; my own grep for `api_key`/`secret`/`token`/`password`/`Bearer` over all 7 files returns nothing; both new CLI scripts take an explicit `--database-url` with no default |
| AG-8 data-scale resilience | **VIOLATION FIXED** | This iteration's core deliverable. Iteration 16's minor unresolved entry is now **resolved**: the unbounded `select(MaintenanceBoundary)` on the boot path is gone, replaced by the filtered/projected/`LIMIT 101` statement with a fail-closed overflow branch (`j11_preboot_guard.py:173-182`, `:218-228`), verified by me directly and by 39 passing tests |
| AG-9 offline-deterministic ingest | OK | Zero network calls — my grep for `requests`/`urllib`/`yfinance`/`http://`/`urlopen` over all 7 files returns nothing; the AVB rider reads iteration-15's committed fetch artifact from disk. Both dated exceptions stay exhausted |
| AG-10 host resource ceiling | OK | No launch script or host-guard block touched; the full suite was not run |
| AG-11 no new composite number | OK | No new score attached to anything |
| AG-12 manifest immutability | OK | No manifest row created or mutated — the live DB file is byte-identical on my own `stat`, which is conclusive at file level |
| AG-13 system-vs-market separation | OK | No vocabulary surface touched |
| AG-14 no Tapeology coupling | OK | No import, call or write toward that repository anywhere in the change set |
| AG-15 no outcome-tuned selection | OK | No selection rule or threshold touched |
| AG-16 cohorts are not controls | OK | No cohort claim made |
| AG-17 repair never rewrites provenance | OK | No repair invoked. Iteration 16's two artifacts are byte-unedited (my own `sha256sum`); iteration 13's evidence is intact (0 lines from `git status`) |
| AG-18 bounded migration only | OK | No `ALTER`, no `CREATE TABLE`, no `create_all` executed against the live file — verified by grep and by the unchanged file fingerprint |

**Ledger: 7 total, 0 unresolved.** No new violation. No critical violation.

**Coherence:** `COHERENCE-PASS` (`runs/goal-session-market-compass/iter-17/coherence.md`) — no blocking
violations, no advisory notes.

**Pipeline health:** Review `PASS_WITH_NOTES` (one MINOR: the two new evidence scripts have no tests).
QA `PASS`. Audit `PASS_WITH_GAPS` (B1 IMPORTANT, T1 IMPORTANT; B3/T2/T3/D1 gaps; B2/T4/D2 observations).
Depth dispatched was `full`, matching the spec's own `Depth: full` — the silent full→lean demotion that
fired in iterations 2, 6 and 8 did **not** recur, for the ninth iteration running.

## Next-Step Recommendation

**ONE DECISION IS NEEDED FROM THE OWNER, and it is a safety decision, not a research one.**

Right now the app cannot be started at all without breaking two of the owner's own rules at once. Starting
it would create the very table the owner said not to create, and would then write a new day's results onto
12 August, one of the eleven damaged days. That write cannot be undone. The only thing stopping it today is
that nobody starts the app — and the owner's own rule says in plain words that "do not start the backend"
is not an acceptable control. So the situation is circular: the safety catch cannot be switched on without
the table, and the ordinary way that table appears is the very start-up the catch exists to prevent.

Please pick one:

- **(a) Allow the one small table to be created.** This is a single, additive, empty table on the real
  database — nothing else changes, no existing data is touched. The tool that then switches the catch on is
  already built, already tested, and already refuses to run if anything looks wrong. This is the smallest
  step that makes starting the app safe again.
- **(b) Order the rebuild of the eleven damaged days.** Once those days hold results again, the start-up
  path becomes safe on its own, because the newest stored price day would no longer be an empty day. The
  rebuild runs as a controlled script, not as a started app, so it is safe to run while the catch is off.
  This still needs a separate, fresh written instruction from the owner.
- **(c) Change the plan in `docs/goal.md`** — for example by allowing the table's creation as part of the
  existing permission, or by saying in writing that the freeze may be lifted some other way.

Please note for the record: the honest reading of this iteration's green tick on the live check is that it
**measured the danger**, it did not remove it. The check asked "does the app currently refuse to write to
12 August?", the answer was "no, it would write", and the plan recorded that answer as a pass. Nobody
stated anything false — the four owner-facing status lines are exactly right, and the owner's own ruling
already describes how start-up creates the table — but a reader of the developer's, reviewer's and quality
reports alone would not learn how exposed the system is today. The independent auditor was the one who
said so, and I confirmed every step of it myself.

**FOUR SMALL JOBS RIDE ALONG** whenever the next run happens. None of them can change the decision above:

1. Add a small test for each of the two new evidence-writing tools, proving they refuse to run when the
   destination folder is not named. One of them can currently overwrite three of iteration 16's saved
   evidence files if the folder is mistyped — the same shape of accident that already happened once in
   iteration 14. Those files are in version control, so it would be recoverable, but it should not be
   possible.
2. Correct the wording in the saved AVB evidence file that calls the two compared versions "genuinely
   independent". They are not: one is exactly the other rescaled by the same factor, so the number it
   produces cannot come out any other way. The AVB-A conclusion itself is sound and should stay — it rests
   on the decision comparison, not on that number.
3. Correct the quality report's list of damaged dates. It lists eleven dates, of which only two are
   actually damaged dates, and seven of them hold no data at all — so those checks passed without testing
   anything. The underlying fact still holds: all eleven real damaged dates hold zero results, which I
   confirmed myself.
4. Stop proving "we did not touch the other journeys' code" with `git diff` alone. That command cannot see
   five of this iteration's seven changed files, because they are new and not yet in version control. The
   claim is true — I re-checked it over both kinds of file — but it was not validly proved.

**ONE MECHANICAL ITEM:** this iteration's five new code files and its whole evidence folder are still not in
version control at the time of writing. Please confirm they get committed.

**FIVE OLDER OWNER QUESTIONS** remain open and non-blocking: whether 3.44 GB is acceptable for J-09; J-06's
"underlying run unavailable" wording; the rewording of J-01's first two test steps; whether an empty
"next-session focus" is acceptable; and whether MNST joins the recovery list.

**TWO STANDING FRAMEWORK NOTES:** the defect that once let a forbidden test lane run is still unfixed in
`scripts/automation/` — nine iterations running have avoided it with the maintenance-isolation contract
rather than curing it; and `goal_gate.py`'s duplicate-journey-heading defect is still unfixed and must be
closed before any GOAL_ACHIEVED certification.

**In one sentence:** the owner should decide whether to allow that one small empty table to be created so
the safety catch can be switched on, or instead order the rebuild of the eleven damaged days — and until
then nobody should start the Trendora app.

## Halt Justification

I am halting because every way forward belongs to the owner, and because stopping is the safer choice here.

**Why not CONTINUE.** The blocker is the switched-off safety catch, and every route past it is an owner
decision: creating the table is forbidden by name in the owner's own ruling ("do not create it and do not
migrate to it"); arming the catch needs that table; the rebuild of the eleven days is explicitly not
authorised and needs a separate fresh instruction; and re-wording the rule is a change to `docs/goal.md`.
That is the methodology's human-owned-blocker case, and it matches before the "keep going" case does. Real
non-owner work exists — the four small jobs listed above — but not one of them can switch the catch on or
make starting the app safe. I also checked whether an engineer could close the hole without the owner, and
they cannot: making the catch refuse when the table is missing would have no effect, because start-up
creates the table before the catch ever runs; and making it refuse on an empty table would block every
normal start-up forever, which is a design decision with wide consequences that only the owner should make.
Letting the loop continue would put the planner one step from the rebuild, the single step the owner
forbade.

**Why halting is also the safer choice.** A stopped engine starts no backend, and starting the backend is
exactly what must not happen while the catch is off and the forbidden table would be created by the act of
starting.

**Why not REGRESSION.** Nothing that worked stopped working. No journey was tested, so none could fail. Not
one value in the real database moved — I verified the file's timestamp, size and empty write log myself.
The one open ledger entry from iteration 16 was closed by this iteration's fix, leaving zero unresolved
violations, and no new violation was introduced.

**Why not ESCALATE.** This run already used the careful full depth, and the careful depth is what found
the problem.

**One process fact for the record.** This is the eighth iteration running in which the independent auditor
found what the developer, the reviewer and the quality check all missed. This time the finding was not a
false statement but a framing one: three green reports described an open safety exposure as a completed
check.
