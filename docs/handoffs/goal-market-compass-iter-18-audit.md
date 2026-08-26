# goal-market-compass-iter-18 Audit Report

**Date:** 2026-08-26
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's safety property is real and I verified it myself against the live database, not from the
handoff: `maintenance_boundaries` exists on `apps/backend/data/trendora.db` with a schema exactly matching
`app.models.MaintenanceBoundary.__table__`, carries exactly one active `j11-incident-recovery` row whose
persisted date set equals `j11_maintenance.INCIDENT_DATES`, and the real production entry point
(`j11_preboot_guard.evaluate_boundary_for_date_fail_closed`) returns `blocked=True, ambiguous=False` for
all eleven quarantined dates and `blocked=False` for four separate control dates when run against the live
file through a read-only handle. Every boot-initiated `run_scan` call site is now guarded — I re-derived
the call graph independently and found exactly three (`warmup.ensure_latest_snapshot`,
`warmup._run_warmup`, `forward_testing._backfill`), all covered; the fourth (`data_manager`) is
user/API-triggered and correctly out of scope. Two IMPORTANT gaps found and fixed during this audit (a
missing DEFINITION-OF-DONE artifact statement, and a false test-coverage claim in the new entrypoint's own
docstring); the remaining findings are documented limitations, not defects that compromise the goal.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the dev handoff omitted the DEFINITION-OF-DONE-required J-01/J-04/J-10
carry-forward citation (TC-17).**

The spec's DoD (`docs/phases/goal-market-compass-iter-18.md:91`) requires: *"the dev handoff cites that
this iteration's diff touches none of `apps/backend/app/api/*`, `scoring.py`, `sectors.py`, or
`compass.py`"*. The delivered `docs/handoffs/goal-market-compass-iter-18-dev.md` contained no such
statement anywhere — the only match for those paths in the whole file was line 181's unrelated *"no
`GET /api/compass` call"*. The reviewer nonetheless recorded `definition_of_done: complete`
(`reports/reviews/goal-market-compass-iter-18-review.md`) and QA asserted the check under its own
"Changed Files Verification" heading (`reports/qa/goal-market-compass-iter-18-qa.md`), so the *fact* was
checked — but by the wrong artifact. This is precisely the shape iteration 17's own audit filed as T2
(`docs/handoffs/goal-market-compass-iter-17-audit.md:70-78`), which is why iteration 18's spec promoted it
to a DoD checkbox.

The underlying fact is TRUE. I re-derived it over tracked and untracked files together:

```bash
{ git diff --name-only HEAD; git status --porcelain | awk '{print $NF}'; } | sort -u \
  | grep -E 'app/api|scoring\.py|sectors\.py|compass\.py'
# -> no matches (42 changed paths scanned)
```

**Fix applied:** appended an "Audit addendum" section to
`docs/handoffs/goal-market-compass-iter-18-dev.md` carrying the claim, the exact re-derivation command and
its result, and an explicit honesty qualifier that this is a code-identity argument and that J-01/J-04/J-10
were **not** re-exercised (isolation forbids it). Verification: the command above re-run at fix time, 0
matches over 42 paths; no test covers a handoff's text, so the command output is the cited evidence.

---

**B2 — GAP (not fixed, deliberately): `prog.dates_done` / `prog.snapshots_created` advance even for a date
the boundary blocked (`apps/backend/app/engine/warmup.py:371-372`).**

The reviewer filed this as MINOR and proposed *"only advance the counter readiness.py trusts when
`run_scan` actually ran"*. I traced the consequence before accepting that fix, and it is not safe to apply
blind. `readiness.py:204` does `done = max(done, int(warmup.get("dates_done", 0)))` and
`readiness.py:227` flips to `READY` only when `done >= total`. With the counter left as-is, a completed
warm-up reports `history n/n` even though the quarantined dates hold no snapshot — the badge overstates.
With the reviewer's fix applied, `done` would be permanently `total - blocked` while any boundary is
armed, so readiness would report `INITIALIZING` forever — a worse, user-visible outcome on exactly the
journeys (J-01/J-04) this iteration must not disturb, and one no test in the suite pins down either way.
The spec pins the counters only for the unblocked (TC-2) and no-boundary (TC-4) cases, both of which pass.

Choosing between "slightly optimistic badge" and "permanently stuck badge" changes product behaviour and
is not this audit's call to make unilaterally — recorded as a limitation for a future iteration, with the
trade-off written down. Note also B3: on the live database as armed today, this code path is not reachable
on boot at all.

---

**B3 — GAP: arming the boundary disables the entire background warm-up on the live database, and no
artifact said so.**

`ensure_latest_snapshot` returns `None` when the latest stored date is blocked
(`apps/backend/app/engine/warmup.py:113-120`), and `apps/backend/main.py:113` starts the warm-up only
`if latest is not None`. The live `max(daily_prices.date)` is `2026-08-12` — one of the eleven quarantined
dates (verified read-only against the live file). Therefore, while this boundary stays armed, a boot
skips the latest snapshot **and never launches the background warm-up thread at all**, so the two call
sites this iteration guarded (`warmup._run_warmup:370`, `forward_testing._backfill:559`) are currently
unreachable on boot, and every *non*-incident cadence date also goes unwarmed. Readiness would report
`awaiting_snapshot` rather than `ready` (`readiness.py:171-173, 223-230`).

This is fail-closed and safe — arguably *stronger* than claimed — and the dev handoff's before/after prose
is accurate as written (it describes the pre-arm state). But it means the headline new guards are
defence-in-depth for a future state rather than today's only protection, and the operator-visible
consequence of the arm was nowhere on the record. Per the iter-17 lesson the spec itself cites ("state the
consequence in prose, not just the boolean"), I added this to the handoff addendum, explicitly marked as
derived by reading the code, **not** by booting.

---

**B4 — GAP: `data_manager`'s backfill job can still write a canonical `ScannerRun` onto a quarantined
date (`apps/backend/app/engine/data_manager.py:3754-3756`).**

Agrees with the reviewer's filed NOTE. I independently enumerated `main.py`'s whole `lifespan` (lines
75-131) to confirm this is genuinely not boot-reachable: boot calls `create_db_and_tables`, `load_seed`,
`sweep_orphaned_runs`, `ensure_latest_snapshot`, `start_warmup`, `start_readiness_refresh`,
`health_watchdog` — none reaches `_do_backfill`, and `sweep_orphaned_runs` marks orphaned jobs
`interrupted` rather than resuming them. The owner ruling's requirement 7 scopes this iteration to
boot-initiated paths, so this is correctly out of scope, not a delivery defect. Recorded because the
quarantine is only as strong as its weakest *authorized* writer: an operator clicking Data Manager
backfill today would still mint a run on a quarantined date.

---

**B5 — OBSERVATION: the mutation-accounting "content fingerprint" is a rowid-aggregate fingerprint, and
the mtime "primary instrument" cannot discriminate across the full-sequence bracket.**

`j11_maintenance.capture_full_table_sweep` hashes `count / min(rowid) / max(rowid) / sum(rowid)` per table.
Its own docstring is honest that a same-rowid in-place UPDATE would not be caught, and points to
mtime/size/`-wal` as the primary instrument. But across the *whole* live sequence the mtime necessarily
moved (two authorized writes), and the file size is byte-identical either way — so for this particular
bracket the corroborating sweep is effectively the only instrument, weaker than the spec's phrase "content
fingerprint" implies. A true content hash over 3.3M `daily_prices` + 6.8M `forward_returns` rows would
itself strain the project's resource contract, so this is a reasonable trade, honestly documented. I
corroborated it independently, read-only: `daily_prices` = 3,310,374 rows, `scanner_runs` = 3,117 rows,
`max(daily_prices.date)` = `2026-08-12`, zero `scanner_runs` on any of the eleven dates, table count 24 →
25, file size unchanged at 8,365,871,104 bytes — all matching the handoff exactly.

### Frontend Findings

None — no file under `apps/frontend/` appears in the changed-file set (tracked or untracked). Verified.
The UI-chain artifacts correctly record the isolation contract rather than fabricating a verdict:
`reports/phase-goal-market-compass-iter-18-ui-test-results.md` reads **SKIPPED** with the contract cited,
and `runs/goal-session-market-compass/iter-18/maintenance-isolation-refusals` logs the refused browser-QA
dispatch at `2026-08-26T00:20:05Z`. TC-16's "no browser-QA invocation anywhere in the evidence trail"
holds.

### Test Findings

**T1 — IMPORTANT (fixed): `_schema_mismatches`' docstring claimed all four of its labels are exercised by a
real test; only one was.**

`apps/backend/scripts/run_j11_maintenance_boundary_table_create.py:78-82` states: *"Every label in this
small, closed vocabulary (missing / extra / type mismatch / nullable mismatch) is exercised by a real test
(TC-7) — never merely declared reachable (goal-market-compass iter-14/14b's lesson)."* TC-7
(`test_tc7_table_create_stops_on_mismatch_and_names_the_missing_column`) exercises **only** the `missing`
label. The `extra`, `type mismatch` and `nullable mismatch` labels were declared reachable and never
proven — the exact inversion of the lesson the phase spec cites at
`docs/phases/goal-market-compass-iter-18.md:27`. I was genuinely unsure between GAP and IMPORTANT here
(the branches turn out to work, and the spec's own TC-7 only demands the missing-column case) and took the
higher level, because a false coverage claim standing in the codebase is what the cited lesson exists to
prevent.

I first proved all four labels are genuinely reachable and correctly worded by driving the classifier
directly, then closed the gap with real tests rather than by weakening the docstring.

**Fix applied:** two tests appended to `apps/backend/tests/test_j11_preboot_guard_cli_scripts.py` —
`test_audit_schema_mismatch_classifier_exercises_every_declared_label` (exact-value assertions on all four
labels plus the empty exact-match case) and `test_audit_table_create_stops_on_an_extra_column_and_names_it`
(end-to-end: a live table carrying a `stowaway` column must STOP, exit non-zero, name the column, write
nothing, and never `ALTER` it away). Verification:

```
cd apps/backend && .venv/bin/python -m pytest tests/test_j11_preboot_guard.py \
  tests/test_j11_preboot_guard_cli_scripts.py tests/test_j11_maintenance.py -q
-> 82 passed in 2.79s        (80 before my fix, +2 new; no pre-existing test changed)
```

---

**T2 — OBSERVATION: one assertion in TC-1 is tautological, but the load-bearing one is present.**

`test_iter18_tc1_warmup_cadence_loop_skips_a_blocked_date_no_run_created_logs_it` asserts
`get_run_for_date(session, blocked_date) is None` while `run_scan` is monkeypatched to a list-append, so
that assertion could not fail regardless of the guard. The real proof — `assert calls == []` — is present
and tight, and the log-line assertion checks both the date and the boundary name. No action needed.

---

**T3 — OBSERVATION: `_wal_effectively_unchanged`'s new accepting branch is unit-tested but was not
exercised by the final live run.**

In the final evidence (`runs/goal-market-compass-iter-18/j11-iter18-live-preboot-guard-verification.json`)
`db_file_true_start.wal` and `db_file_true_end.wal` are identical (`exists: true, size_bytes: 0, mtime
1787701771.8940818`), so the plain equality branch carried it; the new `absent -> present-at-zero-bytes`
branch was needed only for the first, discarded run. I checked the fix is a genuine narrowing, not a
blunted detector: a WAL that grew past zero, disappeared, or is present-but-different still fails, and
those three cases are asserted in `test_wal_effectively_unchanged_still_fails_on_a_real_change`.

### Evidence / Report Findings

**E1 — GAP: iteration 17's QA report still carries the wrong eleven-date list that iteration 17's own
audit filed as IMPORTANT.**

`reports/qa/goal-market-compass-iter-17-qa.md:100-101` still claims *"All 11 incident dates confirmed at 0
scanner_runs"* over `2026-08-09, 08-10, 08-12, 08-14 … 08-22` — nine of which are not incident dates and
seven of which hold no rows at all, so the row proves nothing (iter-17 audit finding T1,
`docs/handoffs/goal-market-compass-iter-17-audit.md:60-68`). Rider 6c corrected only
`reports/phase-goal-market-compass-iter-17-ui-test-plan.md`. The spec's rider text says "and any sibling
report repeating it", which arguably reaches this row. Not fixed here: AG-17 forbids rewriting the incident
evidence record, and a past iteration's QA verdict is part of that record — correcting it is an owner call,
not an auditor's. Recorded so it is not lost a third time.

---

**E2 — OBSERVATION (developer got this right against a mis-paraphrasing spec): rider 6c.**

The spec's TC-15 instructs the correction to match iter-17 eval.md's *"only two are actually damaged
dates, and seven of them hold no data at all"*. Those two clauses describe **different lists** — the
"seven hold no data" clause is about the QA report's *wrong* list (E1), not the canonical eleven. A literal
transcription would have introduced a new falsehood. The developer instead re-derived live and wrote what
is true. I re-verified independently, read-only: all eleven canonical dates carry `daily_prices` rows
(585–590 each) and zero `scanner_runs`; only `2026-08-11`/`2026-08-12` fall outside the committed seed
window. The delivered correction in `reports/phase-goal-market-compass-iter-17-ui-test-plan.md:81-93` is
accurate.

---

**E3 — OBSERVATION: the handoff's status lines are whitespace-aligned, not byte-exact to the spec.**

The spec's TC-16 asks for exactly `J-11 LIVE PRE-BOOT GUARD: ARMED`; the handoff writes
`J-11 LIVE PRE-BOOT GUARD:  ARMED` (two spaces, aligned with the other three lines). I grepped
`scripts/` and `.claude/` for any machine parser of these strings and found none, so this is cosmetic.

---

## 3. Domain Assessment

The domain logic is sound and, unusually for this surface, I could not find a hole in the core safety
property. Three things persuade me rather than the handoff's own summary:

1. **The state-driven design holds under inspection.** `evaluate_boundary_for_date`
   (`j11_preboot_guard.py:185-263`) contains no incident-specific conditional; the date-set wiring lives
   only in `register_j11_incident_boundary`. Its query filters `active.isnot(False)` rather than
   `active == True`, so a NULL-`active` row is *fetched* and reaches the ambiguous/fail-closed branch
   instead of being silently dropped by SQL's three-valued logic — the exact trap the owner's ruling
   named. Table-absence is handled explicitly as the same true no-op as "zero rows", so the module was
   already correct before the table existed and did not need to change when it appeared.
2. **Fail-closed is real, at both layers.** Row-level ambiguity blocks inside
   `evaluate_boundary_for_date`; call-level exceptions block inside the new
   `evaluate_boundary_for_date_fail_closed` wrapper, which both new call sites and the live-verification
   tool share — so the thing the tool proves is the literal function the boot paths invoke, not a
   look-alike. TC-3 and its `_backfill` twin exercise this by making the evaluation raise mid-loop and
   asserting the loop continues rather than marking the whole warm-up `failed`.
3. **The bounded-write discipline held on the real file.** The table-create entrypoint sources its schema
   from `MaintenanceBoundary.__table__` and creates through that Table object's own `.create()` — never
   `create_db_and_tables()`/`metadata.create_all()`, so no unrelated missing table could be minted as a
   side effect. On the live file the result is exactly one new table (7 columns, types and nullability
   matching the model, plus its own `ix_maintenance_boundaries_name` unique index) and exactly one row.
   Both refusal gates (`--confirm`, no-default `--database-url`) refuse before `make_engine` is ever
   called, asserted with a mock rather than inferred.

The one place the delivered work is weaker than its own description is evidence *strength*, not
correctness: the mutation-accounting sweep is a rowid-aggregate check wearing the words "content
fingerprint" (B5), and the second-order consequence of arming — that the whole background warm-up now
stops firing on boot (B3) — was traced only during this audit. Neither changes the answer to the question
the iteration exists to answer.

The mandatory stop was honoured. No Stage D artifact exists under `runs/goal-market-compass-iter-18/`, no
execution identity was frozen, `J-11 STAGE D READY: YES` is carried by citation from
`runs/goal-market-compass-iter-17/j11-iter17-stage-d-readiness.json` (`ready: true`,
`avb_classification: "AVB-A"`, `preflight_gate_passed: true`) rather than re-derived, and
`J-11 STAGE D AUTHORIZED` remains `NO`. AG-7/AG-9/AG-12 verified clean by direct grep of the new and
changed modules (no credential-shaped literal, no network import, no `NextSessionManifest` reference);
AG-8 holds because the new call sites reuse the already-bounded, column-projected, `LIMIT`-ed statement
rather than introducing a new load; AG-17 holds because nothing rewrote provenance — the arm added state,
it did not reclassify anything.

Live database integrity after my own read-only work: `size=8365871104 mtime=1787701766.627290700` —
byte-identical to the developer's recorded true-end. This audit wrote nothing to `trendora.db`.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `docs/handoffs/goal-market-compass-iter-18-dev.md` | Appended an "Audit addendum" carrying the DoD-required TC-17 J-01/J-04/J-10 carry-forward citation (with the tracked+untracked re-derivation command and its 0-match result over 42 paths), an explicit "not re-verified, code-identity claim only" qualifier, and the B3 second-order boot consequence with its `file:line` citations. Verified: command re-run at fix time; cited line ranges checked against the current files. |
| 2 | Important | `apps/backend/tests/test_j11_preboot_guard_cli_scripts.py` | Added `test_audit_schema_mismatch_classifier_exercises_every_declared_label` and `test_audit_table_create_stops_on_an_extra_column_and_names_it`, closing the untested `extra` / `type mismatch` / `nullable mismatch` labels that the entrypoint's docstring already claimed were tested. Verified: targeted suite re-run, **82 passed** (was 80); no existing test modified; no production code touched. |

No production code was changed by this audit. My whole diff is additive: one test block and one handoff
section.

---

## 5. Recommended Next Step

**Proceed — and stop, exactly as the ruling requires.** The safety substrate is live, armed, and
independently verified; nothing further is tractable on this surface without a fresh owner instruction.
`J-11 STAGE D AUTHORIZED: NO` stands, and `READY: YES` must not be read as permission.

For whoever picks this up next, in priority order:

1. **Before the next boot of the live backend**, read B3. Booting now yields
   `awaiting_snapshot`/`initializing` readiness and no background warm-up at all — expected, not a
   regression, but it will look like one to anyone who has not read this report.
2. **Decide B2 deliberately, not incidentally.** Neither the current counter behaviour nor the reviewer's
   proposed fix is clearly right; the choice is a product call about what the health badge should say
   while a quarantine is armed, and it needs a test either way.
3. **Consider B4** — boundary-checking the Data Manager backfill path — if the quarantine is expected to
   survive operator interaction and not just boot.
4. **E1 is an owner call**: iteration 17's QA report still carries a functional-verification row that
   verifies nothing. It should be annotated rather than rewritten (AG-17).

Per the spec's own escalation note: if iteration 19 again finds no tractable non-owner work, write the
one-line "all remaining work is human-blocked" spec rather than inventing further riders.
