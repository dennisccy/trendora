# goal-market-compass-iter-12 Audit Report

**Date:** 2026-08-24
**Auditor:** Hard audit pass — skeptical, evidence-based
**Governing contract:** `docs/goal.md` J-11 step 11 — owner rulings **A4-bis, A8–A14**, the **"J-10 prerequisite SATISFIED"** bullet, and **AG-18**'s *"Bounded exception on record"* paragraph (owner, 2026-08-24)
**Isolation:** maintenance isolation ACTIVE — no backend/frontend boot, no browser, no replay lane, no network fetch, no demo. Live database opened **read-only only** (`mode=ro` + `PRAGMA query_only=ON`); the corrected migration was **never** run against `apps/backend/data/trendora.db`.

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The four scoped jobs are genuinely done, and I re-derived every load-bearing claim myself rather than adjudicating the other lanes' prose. The corrected `create_shadow_table` really does build the replacement table from captured live DDL and really does fail closed; run against the **actual** persisted pre-iter-11 live DDL (not the hand-written fixture), its `PRAGMA table_info` output is **byte-identical** to the input's — column order, types, NOT NULL, all three DEFAULT clauses, `version` at ordinal 9, primary key — with the FK clause as the only semantic change, all three indexes and all row values preserved. `basis_disclosure`'s A4-bis matrix holds under **execution**, not inspection. Live state is untouched: `trendora.db` mtime is still 2026-08-23 23:00:16 with byte-identical size, 24 rows, no FK, three indexes, zero FK violations, and every table count identical to iter-11's post-migration snapshot — Stage C has not begun.

The gaps are real but do not compromise the phase goal. The most substantive (**B1**) is a silent-data-loss path that survives this fix: the row copy and the equality proof both read the *model's* column list, so a live column the model does not declare would be silently NULLed while the migration reports `completed`/`equal: True`. I reproduced it. It cannot fire on today's live table (model and live column sets and order are identical, 28 = 28) and I deliberately did **not** patch it, because doing so would repeat iter-11's exact failure mode — exceeding an owner-bounded authorization. It is surfaced as a precondition on any *future* authorized live run.

**I concur with the developer, reviewer and QA that `J-11 STAGE C READY: YES`** — on my own evidence, not theirs. See §5.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap, deliberately not fixed): the row copy and the equality proof are both blind to any live column the ORM model does not declare — silent data loss with `status: "completed"`**

`copy_rows_to_shadow` (`apps/backend/app/engine/j11_schema_migration.py:301`) takes its column list from `NextSessionManifest.__table__.columns`, and `verify_and_finalize`'s final proof (`:332`) dumps the post-swap table through `dump_table(engine, NextSessionManifest.__table__)` — the model's Table object, not the reflected one. `diff_dumps` (`:212`) iterates `for col in pre_row`, i.e. only the model's columns. Before this iteration's fix the shadow table's column set *came from* the model, so the three were consistent. The fix decouples them: the shadow body now comes from the captured live DDL, so the shadow can carry columns the copy never fills and the proof never checks.

Reproduced (fixture only, never the live DB). I took the **real** persisted pre-iter-11 live DDL from `runs/goal-market-compass-iter-11/j11-stage-b1-premigration-ddl.json`, inserted one extra column `legacy_note VARCHAR` with the value `IRREPLACEABLE-PROVENANCE`, and ran `rebuild_manifest_table`:

```
probe1 status: completed | verify_and_finalize diff.equal: True
probe1 legacy_note AFTER migration: [(None,)]
probe1 column still declared: True
```

The migration reported success, ruling A7's equality check passed, the column survived in the DDL — and the data was gone. The schema *looks* preserved, which makes this quieter than the pre-fix behaviour (where the column would have visibly vanished from the DDL).

Why it cannot fire today, verified read-only: the model's 28 columns and the live table's 28 columns are identical as **sets and as ordered lists** (`live-only: []`, `model-only: []`, `ORDER same: True`).

Why I did not fix it. The spec's IN SCOPE line (`docs/phases/goal-market-compass-iter-12.md:44`) states `copy_rows_to_shadow` and `verify_and_finalize` "must not be redesigned, only the table-body source changes", and ruling A10 (`docs/goal.md:1306`) itself prescribes "copy rows by explicit column name". Ruling A8 (`:1290-1292`) is explicit that the acceptance is "**NOT** permission to broaden Stage B1". A patch here — even a surgical fail-closed precondition — would be an auditor exceeding an owner-bounded authorization in the very iteration whose purpose is to atone for exactly that. The correct disposition is to surface it, which this finding does.

**Owner precondition for any FUTURE authorized live run of this utility:** require a proof that the captured DDL's column set equals the copy's column set (or copy by the *reflected* shadow's columns and diff against the reflected table), before the destructive drop/rename is reached.

*Severity note: this sits on the IMPORTANT/GAP boundary — the failure needs a future live/model divergence AND a fresh owner authorization to run live at all. I was genuinely unsure and chose the higher level, per the rubric.*

**B2 — OBSERVATION: the finished table's `CREATE TABLE` text carries a second, cosmetic difference the docstring's "minus ONLY the FK clause" wording does not mention**

`j11_schema_migration.py:60-61` states the corrected implementation "reproduces the pre-migration DDL text minus ONLY the FK clause". My whole-text diff against the real pre-iter-11 DDL shows two differences, not one:

```
-CREATE TABLE next_session_manifests (
+CREATE TABLE "next_session_manifests" (
...
-	PRIMARY KEY (id),
-	FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)
+	PRIMARY KEY (id)
```

The identifier re-quoting is produced by SQLite's own `ALTER TABLE … RENAME TO` at `verify_and_finalize:328`, not by the transform — the transform's output is byte-exact. Nothing schema-level changes: my `PRAGMA table_info` comparison of pre vs post is `identical: True`, index names and index SQL are identical, and the row dump is identical. TC-7's test asserts the weaker, true column-level proposition, so no test is wrong. Recorded only because iter-11's REGRESSION *was* an over-claimed exactness statement, and A14 asks that the lineage stay legible.

**B3 — GAP: `basis_disclosure`'s "canonicalization" is not a canonicalization for tz-aware non-UTC offsets**

`compass.py:1174` re-serialises the parsed value through `_utc_isoformat`, and the comment at `:1172-1173` claims this is "never a raw string compare between two independently-formatted timestamps". But `_utc_isoformat` (`:664-670`) only *reattaches* UTC to a **naive** datetime; for an already-aware value it returns `.isoformat()` unchanged. So a recorded value denoting the same instant in a different offset is compared as raw text. Executed:

```
EXTRA: 'Z'-suffixed same instant       -> available
EXTRA: naive same instant (no tz)      -> available
EXTRA: same instant, +01:00 offset     -> rebuilt      <-- same instant, reported as rebuilt
```

The failure direction is conservative — a less-confident `rebuilt`, never a fabricated `available` — so AG-1 is not violated and this is not a fail-open. Zero live rows are affected: all 16 non-degenerate manifests carry explicit `+00:00` (I dumped every recorded value per row), and my A/B run of the fixed vs pre-fix implementation over all 24 live rows produced **identical** distributions with **zero** rows changing status. Left unfixed: widening the comparison beyond A4-bis's stated table is scope this iteration does not have.

**B4 — OBSERVATION: `text(shadow_sql)` is not quite "executed verbatim as raw SQL"**

`create_shadow_table:286` passes the captured DDL through SQLAlchemy's `text()`, whose bind-parameter parser claims `:token` sequences. Executed against a DDL carrying `DEFAULT ':sentinel'`:

```
probe2: colon-bearing DDL raised StatementError | (sqlalchemy.exc.InvalidRequestError)
        A value is required for bind parameter 'sentinel'
```

It fails **loud**, never silently, and no such text exists in this table's DDL. Noted only because the docstring (`:27-28`, `:274`) says "verbatim as raw SQL".

**B5 — OBSERVATION: an adjacent `models.py` comment still credits only iter-11's `basis_disclosure` fix**

`apps/backend/app/models.py:870-871` reads "Fixed directly in `basis_disclosure` (iter-11) -- not here" without naming iter-12's A4-bis follow-on. Not false. Self-disclosed by the developer (`docs/handoffs/goal-market-compass-iter-12-dev.md:216-220`) and already filed by the reviewer as a NOTE (`reports/reviews/goal-market-compass-iter-12-review.md:20-25`). Leaving the `models.py` diff narrow was the spec's own instruction.

### Frontend Findings

**None — no frontend file was modified** (`git status` shows zero changes under `apps/frontend/`), which is what the spec required.

TC-23 re-derived independently rather than accepted: `preFreezeEra = view.mode === null` (`apps/frontend/components/compass-manifest-strip.tsx:123`); the branch at `:146-149` renders exactly one sentence — "This manifest predates the freeze/integrity block — no stamps were recorded for it." — and `BasisLine` sits in the `else` branch at `:186`, unreachable when `preFreezeEra` is true. My own read-only query returns `mode IS NULL` = ids {1…8} and degenerate-`generation_json` = ids {1…8} — **complete 8/8 overlap**, re-derived, not copied from the spec or the handoff. The branch asserts no basis status, confident or otherwise. **Honest, not fail-open. No STOP condition. Correctly filed as a Stage G product-verification item per A11(a).**

### Test Findings

**T1 — OBSERVATION: no test covers a non-string recorded timestamp.** The A4-bis cluster (`apps/backend/tests/test_manifest_invariants.py`, `test_a4bis_*`) covers `null`, `""`, `"garbage"`, valid-mismatch and the iter-11 degenerate matrix, but not a non-string value, although the production guard `not isinstance(recorded, str)` (`compass.py:1158`) handles it. I executed it: `{"source_run_created_at": 1234567890}` → `unverifiable`. Uncovered but correct.

**T2 — OBSERVATION: the TC-22 before/after fingerprints do not bracket the iteration's work, and the handoff says they do.** `j11-stage-b1-cleanup-fingerprint-diff.json` records `before_captured_at: 2026-08-24T10:50:08Z` and `after_captured_at: 2026-08-24T10:51:49Z` — **101 seconds apart** — while `runs/goal-market-compass-iter-12/status.json:6` gives `started_at: 2026-08-24T10:25:29Z`. The dev handoff (`:115`) states the capture was "Run once at the START of this iteration's work and once at the END"; that is imprecise. **The substantive zero-write claim nevertheless holds across the whole iteration by a stronger instrument**: the *before* capture itself records `db_file_mtime_before_capture = 1787522416.2308807` = 2026-08-23 23:00:16, i.e. iter-11's own last write, which retroactively covers 10:25:29 → 10:50:08; and I re-`stat`'d the identical value at audit time. Evidence chain complete; wording overstated.

**T3 — positive, recorded for the record: the regression pin is stronger than its own assertion.** TC-12 asserts the old construction loses three DEFAULTs and moves `version` from ordinal 9 to 3. I re-ran the OLD `NextSessionManifest.__table__.to_metadata(...)` construction — verified line-by-line against the removed production code in `git diff` — against the **real** persisted pre-iter-11 DDL, and compared its shape to the **actual** iter-11 post-migration live DDL:

```
OLD construction lost these server DEFAULTs: ['frozen', 'prospective_eligible', 'version']
version ordinal  pre: 8   old-construction: 2
OLD-construction shape == ACTUAL iter-11 live post-migration shape: True
```

The pin reproduces the real, materialized drift — not an approximation of it. The defect this fix closes is demonstrably real.

---

## 3. Domain Assessment

**Job 1 — migration utility (ruling A10).** Sound, and the fail-closed discipline is genuine rather than decorative. `_strip_source_run_id_foreign_key` (`:112-133`) raises unless the regex matches **exactly once** — enforced in both directions, so zero matches and two matches both abort — and `_rename_create_table` (`:136-149`) applies the same discipline to the header. Both raise **before** the single `engine.begin()` at `:285`, so nothing is created or touched on the abort path. I probed the "could it strip something unrelated" question directly rather than reasoning from the regex:

| probe | result |
|---|---|
| table whose only FK is `FOREIGN KEY(other_id) REFERENCES other_table (id)` | raises (0 matches) — unrelated constraint cannot be stripped |
| table with BOTH the target FK and an unrelated FK | only the target removed; `FOREIGN KEY(other_id) REFERENCES other_table (id)` survives verbatim |
| `FOREIGN KEY(x_source_run_id) REFERENCES scanner_runs (id)` | rejected |
| `FOREIGN KEY(source_run_id, x) REFERENCES scanner_runs (id)` | rejected |
| `FOREIGN KEY(source_run_id) REFERENCES scanner_runs_archive (id)` | rejected |
| `FOREIGN KEY(source_run_id) REFERENCES scanner_runs (other_id)` | rejected |
| **today's live DDL** (no FK at all) | raises `MigrationDdlShapeError` — the utility cannot silently re-run against the current table |

The comma-swallowing at `:129-133` only ever consumes a **separator** comma (it requires the text to end in `,\s*$`, which a `','` string literal cannot satisfy), so the remaining clause list stays valid without touching column text. TC-11's AST audit checks the function body with the docstring stripped, so the docstring's own explanatory prose cannot false-positive — a well-made static test.

**Job 2 — `basis_disclosure` (ruling A4-bis).** The ordering lesson from iter-7 is correctly applied: shape guards (`:1135-1150`), then **value validation** (`:1158-1171`), then and only then the match/mismatch comparison (`:1175-1177`). A value can never reach `rebuilt` by raw string inequality against something that was never a timestamp. I executed the full matrix against real `NextSessionManifest`/`ScannerRun` rows in a throwaway in-memory DB rather than reading the branches:

| input | result | required |
|---|---|---|
| `{"source_run_created_at": null}` | `unverifiable` | ✔ never `available` |
| `{"source_run_created_at": ""}` | `unverifiable` | ✔ never `rebuilt` |
| `{"source_run_created_at": "   "}` | `unverifiable` | ✔ |
| `{"source_run_created_at": "garbage"}` | `unverifiable` | ✔ never `rebuilt`, never `available` |
| `{"source_run_created_at": 1234567890}` | `unverifiable` | ✔ (untested — see T1) |
| valid, mismatched | `rebuilt` | ✔ |
| valid, matched | `available` | ✔ |
| `generation_json` NULL / `""` / malformed / `[]` / `{}` | `unverifiable` ×5 | ✔ iter-11 branches unchanged |
| no current `ScannerRun` | `unavailable` | ✔ branch untouched |

Live re-derivation over all 24 manifests, using the real function through a read-only handle: `unverifiable 8, rebuilt 9, available 5, unavailable 2` — matching the handoff exactly. I additionally A/B-ran the pre-iter-12 implementation over the same rows: **zero rows change status**, confirming the fix is purely preventive today, as the spec predicted. All 8 `unverifiable` rows are exactly the degenerate-`generation_json` set {1…8}; none reports `available`.

**Job 3 — `models.py` comment.** Corrected at `:828-843`. It explicitly withdraws the false claim by quoting it, states the referential-contract-vs-physical-DDL distinction, and names all four accepted residuals. The false strings no longer appear anywhere in the comment. TC-21 asserts both the absence of the withdrawn wording and the presence of the true wording.

**Job 4 — `preFreezeEra`.** See Frontend Findings. Honest; no code change, correctly deferred.

**Live-database state (ruling A13), re-derived by me, not read from the artifacts:**

| check | value |
|---|---|
| `trendora.db` mtime / size | 1787522416.2308807 = **2026-08-23 23:00:16** / **8,365,871,104** — unchanged, and unchanged again after my own reads and after I re-ran all five test files |
| `-wal` / `-shm` mtimes | 2026-08-24 — 0-byte WAL; SQLite touches these sidecars when *any* connection opens a WAL-mode DB, including read-only. **Not evidence of a write** |
| manifest DDL | no `FOREIGN KEY` clause; `PRIMARY KEY (id)`; `version` at ordinal 3 with no DEFAULT; `frozen`/`prospective_eligible` no DEFAULT — the four accepted residuals, exactly as ruled |
| manifest rows | 24 |
| indexes | the original three, no extras, no autoindex |
| `PRAGMA foreign_key_check` with `foreign_keys=ON` | 0 violations |
| every table's row count vs **iter-11's own post-migration snapshot** | **no differences** — `daily_prices` 3,310,374 · `scanner_runs` 3,121 · `forward_returns` 6,800,539 · `data_provider_runs` 549 · `watchlist` 6 |
| Stage C started? | **No** — no manifest minted, no derived state cleared, no regeneration; counts and mtime prove it |
| J-10 reopened? | **No** — `daily_prices` untouched; no fetch script invoked |

**Maintenance isolation.** Honored. `reports/phase-goal-market-compass-iter-12-ui-test-results.md` records `Browser QA Verdict: SKIPPED` by contract; `runs/goal-session-market-compass/iter-12/maintenance-isolation-refusals` is empty; no QA evidence/screenshot directory exists; no service was started at any point during this audit either.

**Targeted tests, re-run by me** — sequentially, one process at a time, never the full suite, with a live-DB mtime guard before and after (unchanged):

```
test_j11_stage_b1_migration.py   14 passed in 0.54s
test_manifest_invariants.py      48 passed in 4.50s
test_j11_maintenance.py           9 passed in 0.66s
test_compass.py                  28 passed in 2.96s
test_api_compass.py               8 passed in 1.46s
                                = 107 passed, 0 failed
```

**Scope discipline.** `git diff --stat` touches only the files the spec names, plus the three new read-only scripts and four evidence artifacts. No frontend file, no `preFreezeEra` change, no export-file reconciliation, no second live rewrite, no rewriting of iter-11's REGRESSION verdict. The only stale-`20/567` occurrences left in `docs/goal.md` are inside the owner's own explicit supersession note (`:951`) and the A12 checklist item that names it (`:1325`) — no operative stale wording, and this iteration correctly did not touch either.

**Process observations (not defects in the work):**

- **P1 — the DoD's "committed to git" item is objectively unmet at audit time.** HEAD is `4c41dd35` (iter-11 bookkeeping); all six source/test files show as modified and the three scripts plus four evidence JSONs as untracked. This is goal mode's normal ordering — the commit happens after the evaluator (cf. `a7380009`, `06367ba9`) — so it falls to the finalize step, not to the developer. Recorded so it is not lost.
- **P2 — the plain-language summary softens the owner's wording.** `reports/phase-goal-market-compass-iter-12-implementation-summary.md:19` calls the four residual differences "accepted by the owner as harmless"; ruling A8 (`docs/goal.md:1295-1296`) says they are "**not desirable**; they are merely accepted as the current bounded end state" and "must not become a precedent". The engineering artifacts (module docstring, `models.py` comment) carry the honest framing; only the showcase summary drifts. Worth a one-line correction next time that file is touched.

---

## 4. Fixes Applied During This Audit

**None.**

No CRITICAL issue was found. The one IMPORTANT finding (**B1**) was deliberately left unpatched: the owner's binding 2026-08-24 ruling narrows this iteration to four named jobs, the spec forbids redesigning `copy_rows_to_shadow`/`verify_and_finalize`, and ruling A8 states the acceptance is "NOT permission to broaden Stage B1". An auditor silently widening the diff into the authorized migration module would reproduce iter-11's exact failure mode — exceeding an owner-bounded authorization — in the iteration convened to atone for it. B1 is therefore surfaced with a reproduction and an explicit owner precondition rather than absorbed into the diff.

Nothing in the working tree was modified by this audit. All audit probes ran in the session scratchpad against throwaway fixture databases; the live database was opened read-only and its mtime and size are identical before and after (`1787522416.2308807` / `8365871104`).

---

## 5. `J-11 STAGE C READY` — my own verdict against ruling A12

**J-11 STAGE C READY: YES**

**I concur with the developer, reviewer and QA.** I am the lane that caught iter-11's DDL residual after all three missed it, and iter-10's two false acceptance items, so I re-derived all eleven items from primary evidence rather than from their reports. Every item below is backed by something I ran or read this session.

| # | A12 item | Held? | My own evidence |
|---|---|---|---|
| 1 | J-10 closed, no stale `20/567` operative wording | YES | `grep` over `docs/goal.md`: only `:951` (the owner's own "is **stale**; corrected here rather than deleted" note) and `:1325` (the A12 item naming it). No operative use. Not touched by this iteration. |
| 2 | Four-item DDL residual accepted and documented | YES | `models.py:830-836` names all four; `j11_schema_migration.py:38-50` preserves the residual section reframed as historical. I re-derived the residual myself: OLD construction vs real pre-iter-11 DDL loses `frozen`/`prospective_eligible`/`version` DEFAULTs and moves `version` 8→2 (0-based), and its shape **equals the actual iter-11 live post-migration shape** (T3). |
| 3 | Live manifest FK still absent | YES | My own `sqlite_master` read (`mode=ro`): no `FOREIGN KEY` clause. `PRAGMA foreign_key_check` with `foreign_keys=ON`: **0** rows. |
| 4 | 24 manifest rows still unchanged | YES | My own count: 24. Per-row/per-column values, DDL and index set identical across the persisted before/after fingerprints (`diffs: []`); every table count identical to **iter-11's** post-migration snapshot. |
| 5 | Migration utility fixed for future exact-DDL-minus-FK behaviour | YES | Run against the **real** persisted pre-iter-11 DDL: `PRAGMA table_info` pre vs post **identical**; index names and SQL identical; row dump identical; only the FK clause removed (plus SQLite's cosmetic re-quoting, B2). Fail-closed on 6 adversarial probes and on today's live DDL. **Caveat: B1 must be attached as a precondition to any future authorized live run** — it does not affect Stage C, which performs no schema rebuild. |
| 6 | `basis_disclosure` null/malformed timestamp cases fail closed | YES | Executed, not inspected: the full A4-bis matrix in §3, including `null` → `unverifiable` (never `available`) and `"garbage"` → `unverifiable` (never `rebuilt`). Live: 8 degenerate rows all `unverifiable`, **zero** `available`. |
| 7 | `models.py` comment no longer falsely claims exact physical match | YES | Read `models.py:820-874` in full. The withdrawn claim appears only inside an explicit quotation marking it FALSE; the true referential-contract-vs-physical-DDL end state is stated; all four residuals named. |
| 8 | Maintenance isolation still active | YES | Browser lane SKIPPED by contract; empty refusals file; no evidence/screenshot dir; no boot, browser, replay, demo or network in this audit either. Live DB read-only throughout. |
| 9 | All targeted tests passing | YES | I re-ran all five files myself, sequentially: **107 passed, 0 failed**. |
| 10 | Zero live-database writes | YES | `trendora.db` mtime `2026-08-23 23:00:16` and size `8,365,871,104` — identical before the iteration (recorded inside the before-capture), at audit start, and after my own reads and test runs. `-wal` is 0 bytes; sidecar mtimes are read-open artifacts, not writes. Every table count identical to iter-11's post-migration snapshot. |
| 11 | No new blocker discovered | YES | `preFreezeEra` independently re-derived and honest (complete 8/8 overlap, no `BasisLine`, no status claim). B1–B5 and T1–T2 are gaps and observations, none of which blocks a destructive-clear/regeneration stage. |

**Iteration 11's REGRESSION verdict stands, unchanged** (ruling A14). Nothing in this report softens it: the fixture tests being clean and the comment being honest do not retroactively make iter-11 a PASS. The lineage stays as the owner recorded it — primary goal succeeded, stored state preserved, unauthorized DDL residual detected, REGRESSION recorded, owner later accepted the exact residual instead of ordering a second rewrite.

**Stage C is not executed by this iteration and still requires an explicit owner instruction to resume.**

---

## 6. Recommended Next Step

Proceed — but not automatically into Stage C. The correct next action is to put this readiness answer in front of the owner, since ruling A12 makes Stage C an owner-gated resume rather than a pipeline continuation.

1. **Commit the iteration** (P1) — the DoD's git item is the only unmet checkbox and belongs to the finalize step.
2. **Surface B1 to the owner** as a written precondition on any future authorized live run of `j11_schema_migration`, with the reproduction in §2. It is not a Stage C blocker.
3. **Carry forward to Stage G, unchanged:** the `preFreezeEra` product-verification item (A11a) and the manifest export-file reconciliation (A11b) — both correctly untouched here.
4. **Optional, next time the files are touched:** B5 (`models.py:870-871` naming the A4-bis fix), P2 (the summary's "harmless" wording vs ruling A8's "not desirable"), T1 (a non-string test case for the A4-bis cluster). None warrants a diff of its own.
5. **First things to re-verify once Stage G reopens the browser and replay lanes:** J-05/J-06 (manifest freeze/integrity) and J-08 (retrospective `basis` disclosure at `/market` and `/?asof=`) — the journeys whose served Data-Contract value this iteration's read-path fix touches. No journey could be replayed under maintenance isolation, so none is claimed here.
