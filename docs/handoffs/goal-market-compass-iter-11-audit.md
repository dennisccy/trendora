# goal-market-compass-iter-11 Audit Report

**Date:** 2026-08-23
**Auditor:** Hard audit pass — skeptical, evidence-based
**Phase:** goal-market-compass-iter-11 (J-11 Stage B1-completion)
**Execution mode:** maintenance isolation (ruling A5) — no service boot, no browser lane, no replay
lane, no write to `trendora.db`. Every live query below ran through a `mode=ro` URI handle whose
read-only status was itself proven (a `CREATE TABLE` probe returned *"attempt to write a readonly
database"*).

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The two Stage-C preconditions the iteration-10 evaluator found FALSE on the live database are now
TRUE, and I re-derived both myself rather than accepting the reviewer's or QA's word (ruling A6): the
live `next_session_manifests` DDL carries no `FOREIGN KEY` clause, `pragma_foreign_key_check` returns
zero rows with `PRAGMA foreign_keys=ON` explicitly issued, all 24 rows × 28 columns are unchanged, the
four orphaned `source_run_id` values are stored exactly as before, the index set is identical, no other
table was touched, Stage C has not begun, and `basis_disclosure` — executed live against all 24 real
rows — now returns `unverifiable` for all 8 no-recorded-basis manifests and `available` for none of
them. That is the phase goal, and it was achieved.

It was achieved with one real deviation the reviewer, QA and the dev handoff all missed: the migration
removed the FK constraint **and** three `DEFAULT` clauses **and** reordered a column, while the code
asserted in writing that the result was "byte-for-byte identical to the original except for the one
authorized change". Ruling A1/AG-18 authorized "the FK constraint and **nothing else**". No stored value
changed and nothing in the codebase breaks, but the deviation is already materialised on the live 7.8 GB
database, cannot be corrected inside this audit (the single authorized write window is closed), and is
the owner's to accept or reject. **Ruling A6's hard gate on Stage C should not be treated as cleared
until the owner rules on finding B1.**

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap — NOT fixable in this audit; owner decision required): the "constraint-only"
migration also dropped three `DEFAULT` clauses and reordered a column, and the code claimed otherwise.**

`apps/backend/app/engine/j11_schema_migration.py:172-192` (`create_shadow_table`) builds the replacement
table from `NextSessionManifest.__table__` — i.e. from the **model's** shape, not from the live table's
historical shape captured two functions earlier by `fetch_object_ddl`. The developer correctly caught
two consequences of that choice (four spurious indexes, a duplicate autoindex) and guarded both with a
test. A third and fourth consequence went unnoticed. Diffing the two persisted DDL artifacts
(`runs/goal-market-compass-iter-11/j11-stage-b1-premigration-ddl.json` vs
`…-postmigration-ddl.json`, and re-read live from `sqlite_master` — the live text matches the
post-migration artifact byte for byte):

| | pre-migration | post-migration |
|---|---|---|
| `FOREIGN KEY(source_run_id)` | present | **removed — authorized** |
| `version` | `INTEGER NOT NULL DEFAULT 1` | `INTEGER NOT NULL` |
| `frozen` | `BOOLEAN NOT NULL DEFAULT 0` | `BOOLEAN NOT NULL` |
| `prospective_eligible` | `BOOLEAN NOT NULL DEFAULT 0` | `BOOLEAN NOT NULL` |
| `version` column ordinal | 9 | 3 |

Nothing else differs: the column name set, and every column's type and NOT NULL-ness, are preserved
(asserted mechanically by the new test named below).

`j11_schema_migration.py`'s module docstring stated, before this audit, *"the resulting schema is
byte-for-byte identical to the original except for the one authorized change: no `FOREIGN KEY`
clause"*, and `copy_rows_to_shadow`'s docstring dismissed the column reorder as "cosmetic only". Both
were false against ruling A1's "nothing else" bound. The reviewer re-verified the FK clause was gone
and the index set was intact; QA did the same; neither diffed the two `CREATE TABLE` texts they both
had in hand as persisted artifacts. This is the same shape of failure ruling A6 was written to prevent
— a claim verified only at the level at which it was asserted.

*Why this is IMPORTANT and not CRITICAL:* no stored value changed (I compared all 24 rows × 28 columns
myself — see B-evidence below); the three defaults were artifacts of `app/db.py::_COLUMN_ADDS`
(SQLite demands a non-null default when ALTERing in a NOT NULL column), the model has only Python-side
defaults, so a database built fresh from the model has never carried them either; every write to this
table goes through SQLModel, which supplies all three values client-side; and `grep` confirms no raw
SQL `INSERT` targets `next_session_manifests` anywhere in the repo. Practical breakage risk today is
nil.

*Why it is not fixed here:* correcting it requires a **second** live-schema rebuild. Ruling A5's single
authorized write window is closed, ruling A1 explicitly forbids treating this authorization as "a
precedent for any other table or any later convenience", and the dispatching operational note bound this
audit to read-only queries. Applying a fix would be exactly the unauthorized destructive act the ruling
exists to prevent.

*What I did fix (documentation honesty + enforcement, no database write):*
- corrected the false claim in `j11_schema_migration.py`'s module docstring with an explicit
  "RESIDUAL SCHEMA DELTA" block stating all four differences and naming the owner decision;
- corrected `copy_rows_to_shadow`'s "cosmetic only" phrasing;
- added `test_audit_ddl_delta_beyond_fk_removal_is_exactly_the_known_residual_set` (see T1), which
  pins the delta so it can never again be silently described as "nothing else changed";
- appended an attributed correction block to the dev handoff.

**B2 — IMPORTANT (fixed): `basis_disclosure` raised instead of failing closed when `generation_json`
held valid JSON that was not an object.**

`apps/backend/app/engine/compass.py:1132` (pre-fix): `if "source_run_created_at" not in generation:`.
When `generation_json` parses to a non-dict, this path is reached — the `except (ValueError, TypeError)`
above catches only *parse* failure, and a bare scalar parses fine. Demonstrated concretely:
`"source_run_created_at" in json.loads("5")` → `TypeError: argument of type 'int' is not a container or
iterable`; the same for `null`; and `'"a string"'` / `'[1,2,3]'` survive the `in` test only to fail one
line later at `generation.get(...)` with `AttributeError`. All four escape the guard as a 500 on the
served `GET /api/compass` payload rather than an honest status. Ruling A4 admits no such escape — it
requires that when `source_run_created_at` is absent the function returns the unverifiable state, and
the spec's own TESTING REQUIREMENTS say the function "must not raise". The reviewer flagged this as a
NOTE and it was left unfixed; I rated it higher because a fail-closed guard on a served surface that
can raise is not fail-closed, and the iter-7 lesson quoted in this very spec says a guard is only proven
fail-closed once a test constructs the degenerate input.

*Fix applied:* `if not isinstance(generation, dict) or "source_run_created_at" not in generation:`.
*Verification:* new test `test_tc12b_basis_disclosure_reports_unverifiable_when_generation_json_is_a_non_object`
in `apps/backend/tests/test_manifest_invariants.py` exercises all four non-object shapes (`5`,
`"a string"`, `[1,2,3]`, `null`).
`cd apps/backend && .venv/bin/python -m pytest tests/test_j11_stage_b1_migration.py tests/test_manifest_invariants.py tests/test_j11_maintenance.py tests/test_compass.py tests/test_api_compass.py -q`
→ **96 passed in 8.66s** (was 94 before my two added tests; baseline of the two files I touched was
49 passed before the edits). No live row is affected — my live scan found 16 rows with well-formed
`generation_json` and **zero** non-dict values, so behaviour on real data is unchanged.

**B3 — GAP (observation): mutation accounting proves "no other table was written" only at row-count
granularity.** `capture_full_db_snapshot` (`j11_schema_migration.py:133-148`) records `COUNT(*)` per
table plus the file's size/mtime. An in-place `UPDATE` to another table would not move a row count and
would not be detected. This is exactly what TC-7 and A3.4 asked for, so it is a spec-level limitation
rather than a developer failure, and I closed most of the residual doubt independently rather than
leaving it open: (a) `sqlite_master` contains **zero views and zero triggers**, and no other table's DDL
mentions `next_session_manifests`, so the `ALTER TABLE … RENAME` could not have rewritten any other
object's schema (SQLite ≥3.25 rewrites references on rename); (b) the migration code's only write
statements target the shadow table and the manifest table — there is no statement that could reach
another table; (c) I re-counted **all 24 tables on the live database right now** and every count is
identical to the pre-migration snapshot. Residual risk: acceptable.

**B4 — GAP (observation): pre/post equality is proven at typed-value level, not stored-byte level.**
`dump_table` (`j11_schema_migration.py:83-100`) coerces any value with `.isoformat()` before recording
it, so the persisted dumps hold `2026-08-20T06:15:19.547230` where the database stores
`2026-08-20 06:15:19.547230`. Both dumps go through the same coercion, so the diff is apples-to-apples
and the semantic equality proof is sound — but a hypothetical storage-class or text-format change would
be invisible to it. Byte preservation instead rests on the copy mechanism: `copy_rows_to_shadow` issues
one `INSERT … SELECT` executed entirely inside SQLite against a destination whose column affinities are
identical, so values are relocated, never re-serialised. Sound, but worth stating rather than assuming.

**B5 — GAP: the DEFINITION OF DONE item "migration script, evidence artifacts, fix, tests and corrected
doc comments are all committed to git" is not true as of this audit.** `git status --porcelain` shows
every one of them modified-or-untracked; `git log` shows the last commit is `f08e05d6 wip(goal): iter 10
STALLED`. The developer's stated reason is correct — `scripts/automation/run-goal.sh` performs a scoped
`git add -A -- reports runs README.md` plus commit/push at the iteration boundary, not inside an agent
dispatch — and I confirmed nothing involved is gitignored (`git check-ignore` returns clean for the
evidence JSONs, the migration engine module and the CLI script), so the item should become true at the
boundary. It is nevertheless **not** true now, and QA asserted it as verified (see P1).

### Frontend Findings

**F1 — GAP (adjudication of the carried-forward question): the new `unverifiable` badge is unreachable
for every manifest row that currently exists, but the masking is HONEST, not fail-open.**

`apps/frontend/components/compass-manifest-strip.tsx:146` computes `preFreezeEra = view.mode === null`
and renders the whole freeze/integrity block — `BasisLine` included — only in the `else` branch. I
confirmed on the live database that the set of rows with `generation_json` NULL and the set with
`mode` NULL are the *same* eight rows (ids 1-8), so `BasisLine` renders for none of them today.

I judge this honest rather than a fail-open gap, for three independent reasons:
1. The branch that does render for those rows says *"This manifest predates the freeze/integrity block
   — no stamps were recorded for it."* That is an absence claim, not a confidence claim. AG-1 forbids
   presenting something as proven without backing; this presents nothing as proven.
2. It is factually accurate. Those eight rows were created 2026-08-20 06:15-06:52, before the iter-3
   freeze block existed (the first row carrying `available_at_utc` is id=9 at 10:24 the same day), so
   they genuinely are pre-freeze-era rows.
3. The direction of failure is safe. If a future stage ever backfills `mode` on those rows, the
   `preFreezeEra` branch switches off and `BasisLine` then renders `Basis: unverifiable` — which is
   precisely correct. The fix protects that future rather than depending on it.

What remains a genuine gap: this iteration's frontend change is verified only at pure-function level
(TC-14), and no live row can currently exercise it end-to-end, so the honest rendering those eight rows
receive today comes from a **different** branch than the one this iteration changed. Stage G owns the
first real confirmation. The label/variant choice itself is right: `unverifiable` → neutral `default`
variant, distinct from `available`/`ok` and `unavailable`/`danger`, with an exhaustiveness `never` guard
(`apps/frontend/lib/basis-disclosure-label.ts:32-48`).

### Test Findings

**T1 — IMPORTANT (fixed): the fixture migration test asserted the FK was gone and the index set was
unchanged, but never asserted the `CREATE TABLE` body was otherwise unchanged.**

`apps/backend/tests/test_j11_stage_b1_migration.py:115-155` checks `"FOREIGN KEY" not in
new_ddl["table_sql"]`, row counts, the orphan value, and — in a dedicated regression test — that the
index set matches the original exactly. That last test proves the developer was reasoning about
precisely this class of schema drift; the same rigor was simply never applied to the table definition
itself, which is why B1 passed three review lanes untouched. A schema-migration test that asserts only
the *absence of one clause* cannot detect what else the rebuild changed.

*Fix applied:* added `test_audit_ddl_delta_beyond_fk_removal_is_exactly_the_known_residual_set`, which
parses both `CREATE TABLE` texts and asserts the column name set is identical, each column's type and
NOT NULL-ness is preserved, the FK is removed, the set of columns that lost a `DEFAULT` is *exactly*
`["frozen", "prospective_eligible", "version"]`, no column *gained* one, `version` moved from ordinal 8
to ordinal 2 (0-based), and **no other column definition differs at all**. If a corrective rebuild ever
restores the original clauses, this is the test that must be updated deliberately.
*Verification:* included in the 96-passed run cited under B2.

**T2 — OBSERVATION: the four degenerate-input tests assert the status but not that the four `detail`
strings differ.** `test_tc9…test_tc12` (`test_manifest_invariants.py:210-280`) assert
`status == "unverifiable"` and, for TC-9 only, `detail is not None`. The implementation does return
three distinct details, so the operator-facing distinction exists but is unpinned. Not worth fixing —
noting it.

### Process Findings

**P1 — OBSERVATION: QA asserted a fact it had not verified.** `reports/qa/goal-market-compass-iter-11-qa.md:184`
states *"All evidence persisted, **committed to git** (per iter-9's lesson), and independently verified"*.
Nothing was committed (B5). Small in consequence, but it is the identical failure mode ruling A6 names:
an unverified claim carried forward as verified.

**P2 — RESOLVED, no irregularity: QA did not edit source files after the reviewer's PASS.** The
coordinator flagged that the QA summary described having "corrected" the two stale doc comments. File
mtimes settle it: every touched source file was last written between 22:58 and 23:06 (`compass.py`
23:02:13, `j11_maintenance.py` 23:02:19, `models.py` 23:02:47, `test_manifest_invariants.py` 23:03:12,
`basis-disclosure-label.ts` 23:04:52, `compass-manifest-strip.tsx` 23:05:59), while the review packet
was written at 23:13, the review report at 23:17, and the QA report at 23:43. No source file was
modified after the developer finished, let alone after the reviewer's PASS. QA's "Item 8" wording was
descriptive of state, not a claim of authorship. Both comments are in fact corrected and now cite the
A4 fix (`models.py:829-853`, `j11_maintenance.py` module docstring).

**P3 — OBSERVATION: the `Frontend Present` metadata mismatch is real but was disclosed, not hidden.**
The phase spec and plan both declare `yes`; the ui-test-designer worked to `no`. It did not paper over
the conflict — `reports/phase-goal-market-compass-iter-11-ui-test-plan.md:19-27` states the discrepancy
explicitly, reconciles it against the spec's own body text ("New user-facing capability: None", "New
user actions: None", "UI surface changes: None structurally"), and applies backend-only handling
deliberately. Given maintenance isolation forbade the browser lane either way, the outcome is identical
under both readings. Worth correcting in the metadata for future iterations; not a defect here.

---

## 3. Domain Assessment

**What I re-derived myself, read-only, on `apps/backend/data/trendora.db` (ruling A6):**

| Claim | My result |
|---|---|
| Live `CREATE TABLE` has no `FOREIGN KEY` clause | Confirmed; live text matches the persisted post-migration artifact exactly |
| `PRAGMA foreign_keys=ON` then `PRAGMA foreign_key_check(next_session_manifests)` | pragma reads `1`; **zero violation rows**; `foreign_key_list` is empty |
| 24 rows survive, every stored value unchanged | 24 rows, no missing/extra ids, **672 cells (24 × 28) compared against the persisted PRE-migration dump — zero substantive differences**; the only 40 formatting deltas are the dump's `.isoformat()` "T" separator vs SQLite's stored space, on `created_at`/`available_at_utc` only (see B4) |
| Orphans 3048/3049/3081/3112 not nulled, rebound or "repaired" | All four still stored, still unresolvable against `scanner_runs`, across 12 manifest rows; **zero `source_run_id` values differ from the pre-migration dump** |
| No unauthorized index added, no original index dropped | Exactly the three original indexes, `CREATE INDEX` text identical to the pre-migration artifact |
| No table other than `next_session_manifests` written | All **24** tables' current row counts identical to the pre-migration snapshot; zero views/triggers; no other object references the table |
| `basis_disclosure` fails closed, never `available`, on degenerate input | **Executed the real function against all 24 live rows** through a read-only engine: 8 `unverifiable`, 9 `rebuilt`, 5 `available`, 2 `unavailable`. **Zero degenerate rows report `available`.** |
| Live count of no-recorded-basis rows | **8** (ids 1-8), all NULL, zero empty-string, zero malformed, zero missing-key — matching the spec's re-derivation, not goal.md's earlier "10" |
| Stage C has not begun | `scanner_results` 1327944, `sector_scores` 96751, `theme_scores` 34331, `forward_returns` 6800539, `scanner_runs` 3121, all caches — every count unchanged. No derived state was cleared. |

Two points deserve emphasis. First, the dev handoff proved TC-15 *structurally* ("the fixed function's
logic is `not row.generation_json` → `unverifiable`, which is exactly what all 8 rows carry"). That is
reasoning, not evidence, and the auditor's job is not to accept it — so I executed the actual
`app.engine.compass.basis_disclosure` against the actual live rows through a `mode=ro` handle with
`PRAGMA query_only=ON`, and the specific defect `docs/goal.md` cites by name (the 2026-08-12 version-1
manifest, id=1, recorded source run 3081, long gone) now reports `unverifiable` where it previously
reported `available`. The AG-1 violation on the served surface is genuinely closed.

Second, the domain logic itself is correct and correctly ordered. `basis_disclosure` resolves the
current run by `as_of` and never dereferences `source_run_id` — I read the function line by line to
confirm it, not the handoff's assertion of it. The `current_run is None` check deliberately precedes
the `generation_json` checks, so a degenerate row whose scanner run is also gone reports `unavailable`
rather than `unverifiable`; that ordering is right (the stronger, more specific fact wins) and TC-15's
requirement — never `available` — holds under both branches. The abort-before-rename ordering in
`verify_and_finalize` is genuine rollback safety, not a comment claiming it: the drop and rename are in
the same `engine.begin()` block *after* the equality check, and TC-8 proves the original table survives
a simulated mismatch with its FK clause and every value intact.

The one place the domain reasoning broke down is B1, and it broke down in a specific, instructive way:
the migration captured the original DDL verbatim (`fetch_object_ddl`) and then rebuilt from the ORM
model instead of from what it had captured. It reissued the captured *indexes* verbatim but regenerated
the *table* from a different source of truth. Every consequence of that choice the developer thought to
look for was caught and guarded; the ones nobody thought to look for went to the live database.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/compass.py` | `basis_disclosure`: added `not isinstance(generation, dict) or …` so valid-but-non-object `generation_json` fails closed instead of raising `TypeError`/`AttributeError` on the served payload; docstring bullet updated to name the case |
| 2 | Important | `apps/backend/tests/test_manifest_invariants.py` | New `test_tc12b_…_generation_json_is_a_non_object` covering `5`, `"a string"`, `[1,2,3]`, `null` |
| 3 | Important | `apps/backend/tests/test_j11_stage_b1_migration.py` | New `test_audit_ddl_delta_beyond_fk_removal_is_exactly_the_known_residual_set` pinning the full pre/post `CREATE TABLE` delta (B1/T1) |
| 4 | Important | `apps/backend/app/engine/j11_schema_migration.py` | Replaced the false "byte-for-byte identical … except … no `FOREIGN KEY` clause" claim with an explicit RESIDUAL SCHEMA DELTA block; corrected `copy_rows_to_shadow`'s "cosmetic only" phrasing |
| 5 | Important | `docs/handoffs/goal-market-compass-iter-11-dev.md` | Appended an attributed auditor correction recording the residual schema delta |

No database write of any kind was performed by this audit. No service was started. No browser or replay
lane ran.

**Post-fix verification:** `cd apps/backend && .venv/bin/python -m pytest
tests/test_j11_stage_b1_migration.py tests/test_manifest_invariants.py tests/test_j11_maintenance.py
tests/test_compass.py tests/test_api_compass.py -q` → **96 passed, 0 failed, 8.66s** (single process,
targeted files only, never concurrent). Baseline before my edits, same runner, the two files I touched:
**49 passed**. The two new tests account for the 94 → 96 delta. `git diff` on each touched file
re-read: changes confined to the guard clause, the two new tests, and the docstring corrections —
nothing else.

---

## 5. Recommended Next Step

**Do not treat ruling A6's Stage C gate as cleared yet. Take B1 to the owner first.**

Everything A6 requires of the *implementation* is done and independently re-derived: both fixes are
correct on the live database, and I verified them from the artifact rather than from anyone's prose.
But A6 is a gate on the migration being what the owner authorized, and AG-18's language is absolute —
"removes the `source_run_id` foreign-key constraint and **nothing else**", with "a changed stored value
is a REGRESSION". No stored value changed, so this is not the REGRESSION clause; it is the "nothing
else" clause, and only the owner can decide whether a dropped `DEFAULT 1` / `DEFAULT 0` / `DEFAULT 0`
and a moved column ordinal fall inside or outside it. The three options, stated plainly:

1. **Accept the delta as immaterial** (my technical read: it is — the live table now matches the shape
   a fresh database built from the model has always had, no stored value moved, no code path depends on
   the dropped server defaults, and no raw `INSERT` targets this table) and record the acceptance
   explicitly in `docs/goal.md` so the next iteration is not blocked by it.
2. **Require a corrective rebuild** restoring the three `DEFAULT` clauses and the original column order
   — which is a *second* destructive live-schema operation and needs its own authorization, its own
   pre/post evidence, and its own audit. My recommendation is against this: it doubles the risk on a
   7.8 GB production file to restore clauses nothing reads.
3. **Defer** — proceed to Stage B2/C on the strength of option 1's reasoning, with the delta recorded
   as an accepted deviation.

Whichever is chosen, three items should carry forward regardless: fix the `Frontend Present` metadata
inconsistency (P3); confirm at the iteration boundary that the evidence artifacts, the migration script
and the engine module actually landed in git (B5 — the mechanism is right, but iter-9's lesson was
precisely that an unreproducible run looks fine until someone tries to reproduce it); and, when Stage G
reopens the browser lane, re-verify J-05, J-06 and J-08 first, with explicit attention to F1 — the new
`unverifiable` badge has never been rendered by a browser and no live row currently reaches it.

Stage B1 itself is complete. Stage C should begin only after the owner's answer to B1 is written down.
