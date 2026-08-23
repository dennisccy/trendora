# goal-market-compass-iter-10 Audit Report

**Date:** 2026-08-23
**Auditor:** Hard audit pass — skeptical, evidence-based (maintenance isolation active: no service boot, no browser lane, no replay lane, read-only DB access only)

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

Stage B (pre-reset inventory) and Stage B2 (frozen attempt identity) are genuinely delivered: I re-derived every one of the inventory's 11-date × 7-column figures, both ledger hashes, and the `daily_prices` aggregate independently against the live database read-only, and they match the artifact exactly; the zero-write requirement (TC-8) holds under my own before/after check as well. Stage B1 is **partially** delivered: the model-declaration change is real and its fixture tests are meaningful (I verified the tests are not passing vacuously), but **two of the six acceptance items `docs/goal.md` J-11 step 11 gates Stage C on are not satisfied on the live database, and the review + QA reports record that DoD item as complete anyway.** Three IMPORTANT findings ride forward; none could be fixed inside this iteration's binding constraints (zero writes to `trendora.db`, `Product surface delta: None`, `compass.py`/config-provenance explicitly out of scope), and one of them is the owner decision goal.md step 11 already prescribes.

**Stage C is not unblocked by this iteration.** See §5.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap, owner decision required): the DoD claims all six Stage B1 acceptance items are proven; items 1 and 4 are false on the live database**

`docs/phases/goal-market-compass-iter-10.md:91` (DoD) claims "Stage B1's six schema-contract acceptance items are each proven by a named fixture-DB test". `reports/reviews/goal-market-compass-iter-10-review.md:19` records `definition_of_done: complete`; `reports/qa/goal-market-compass-iter-10-qa.md:182` checks the box. No artifact in the chain maps the six items one-by-one, and two of them cannot be true today:

- Item 1 — *"the live schema's manifest/run relationship matches the documented manifest-survives-rebuild contract"* (goal.md:1141-1142). Verified false, read-only:
  `sqlite3 'file:apps/backend/data/trendora.db?mode=ro' "SELECT sql FROM sqlite_master WHERE name='next_session_manifests'"` still ends in `FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)`, and `pragma_foreign_key_list` still returns one row. The change in `apps/backend/app/models.py:848` is a **model-declaration** change only (correctly so — a live rewrite would violate TC-8 and the additive-ALTER-only rule), so it makes the contract true for any DB created from current metadata, **not** for the 7.8 GB database Stage C will actually delete from.
- Item 4 — *"the solution holds by schema/contract, not merely because SQLite FK checking is off"* (goal.md:1146). On the live DB, `PRAGMA foreign_keys` reads `0` and `SELECT count(*) FROM pragma_foreign_key_check('next_session_manifests')` returns **12** — i.e. the live rows already violate the live constraint, so manifest survival there still rests on enforcement being off. That is precisely what goal.md:1102 forbids as a safety model.
- Item 5 is partially satisfied: verified via `sqlalchemy.schema.CreateTable` that current SQLModel metadata emits **no** `FOREIGN KEY` for `next_session_manifests` and `tbl.foreign_keys == []`, so a Postgres/enforced-FK backend created **from metadata** is fine; one created by carrying the live DDL forward is not.
- Items 2, 3, 6 are genuinely proven by `tests/test_j11_maintenance.py::test_tc3_*`, `::test_tc4_*`, `::test_tc6_*` (subject to B2 below).

Not fixed, and must not be: making item 1 true requires rewriting the live `next_session_manifests` table, which is a write to `trendora.db` — forbidden by DoD TC-8 and by the spec's own "cannot and must not attempt to rewrite the already-created live table" (`docs/phases/goal-market-compass-iter-10.md:39`). goal.md:1158-1159 already names the correct route: *"If this contradiction cannot be resolved safely inside the current repository without a risky migration, STOP before J-11 and surface it as an owner decision."* This finding is that surfacing.

Practical-risk note, recorded honestly so the owner decision is informed: with enforcement off (the default; nothing in `app/db.py:46-65` turns it on), Stage C's deletion will not be blocked, and even **with** enforcement on it would not be blocked by these rows — all 24 manifests' `source_run_id` values on incident dates (3112, 3048, 3049, 3081) point at runs that are *already* gone, not at the four surviving runs (3114, 3148, 3149, 3150) Stage C would delete. The blocking fact is the literal gate wording plus the 12 standing violations, not an imminent failure.

**B2 — IMPORTANT (gap): `basis_disclosure` reports a fabricated `available` for a real incident-date manifest — a live counter-example to acceptance item 6 that the test set misses**

`apps/backend/app/engine/compass.py:1108-1109` short-circuits: `if not row.generation_json: return {"status": "available", "detail": None}`. On live data that branch is reachable on an incident date. Read-only reproduction (`sqlite:///file:…?mode=ro&uri=true`, calling the real `compass.basis_disclosure`):

```
--- 2026-08-12: current run id=3148 created_at=2026-08-21 00:26:04.189714
    v1 src_run=3081 gen_json=EMPTY   -> {'status': 'available', 'detail': None}      <-- fabricated
    v2..v6 src_run=3081 gen_json=present -> {'status': 'rebuilt', ...}
```

Run 3081 no longer exists; the current run for that `as_of` is 3148, created during the recovery era. So version 1 of the 2026-08-12 manifest asserts its original basis is intact while its five sibling versions correctly say `rebuilt` — the exact fabricated-state class TC-5 was written to exclude (`docs/phases/goal-market-compass-iter-10.md:111`), and the exact shape of the iter-7 lesson (a gate proven only against complete fixtures silently agrees on a degenerate input). The degenerate input here is not "no run" (covered) but "no recorded basis": `generation_json` empty. 10 of the 24 live manifests have empty `generation_json`; one of them is on an incident date. It is served — `apps/backend/app/api/compass.py:43` attaches `basis_disclosure` to every `GET /api/compass` payload.

This survives Stage C/D unchanged: after the 2026-08-12 run is deleted and rebuilt, v1 will *still* read `available`. Any Stage G check of the form "every incident-date manifest discloses honestly" must handle it.

Not fixed: `compass.py` is declared reference-only/unchanged by the plan (`runs/goal-market-compass-iter-10/plan.md:65-66`), the spec declares `Product surface delta: None`, changing the fallback alters the served `basis` for 10 manifests, and the browser/replay lanes that would verify a served-behaviour change are forbidden this iteration. It belongs to Stage C/D/G. I was not torn on severity: it fails in a scenario that is not merely realistic but *currently live*.

**B3 — IMPORTANT (gap; I was unsure between IMPORTANT and GAP and chose the higher): the Stage B2 identity invariant cannot detect a change to the code that actually regenerates runs**

`freeze_attempt_identity` (`apps/backend/app/engine/j11_maintenance.py:194-223`) correctly reuses `engine_identity.compute_engine_identity` — the same function `scanner.persist_run_payload` stamps onto new runs (`apps/backend/app/engine/scanner.py:119`), so it compares like with like. But that digest covers only what `config.yaml` `provenance` lists, verified from the produced artifact `runs/goal-market-compass-iter-10/j11-frozen-identity.json`:

```
provenance_engine_files: ['apps/backend/app/engine/compass.py',
                          'apps/backend/app/engine/session_delta.py',
                          'apps/backend/app/engine/engine_identity.py']
provenance_config_keys:  ['compass.selection', 'compass.delta', 'compass.manifest']
```

`scanner.py`, `scoring.py`, `indicators.py`, `universe_resolver.py` and every scoring/threshold config key are **not** covered. So goal.md step 12's invariant — "dates 1–5 under engine A → code or config changes → dates 6–11 under engine B is not a successful clean regeneration" (goal.md:1164-1167) — is not actually detectable by this mechanism for the scoring path. `check_attempt_identity_consistency` would return `True` for both halves. This is not hypothetical: this iteration's own OUT OF SCOPE list (`docs/phases/goal-market-compass-iter-10.md:86`) parks the AVB dollar-volume fix in `scoring._avg_dollar_volume` / `universe_resolver._adv_dollar` as "a Stage D/G concern once regeneration actually runs" — i.e. an edit to exactly the uncovered files is *planned* between this freeze and Stage D.

Not fixed: widening `provenance.engine_files` moves `engine_identity` for every future manifest and run — a research-provenance change requiring owner sign-off, and squarely inside this iteration's OUT OF SCOPE ("any change to … research logic"). The pre-existing narrowness dates to iter-3, not to this diff; what is new is that Stage B2 now *depends* on it.

**B4 — GAP (not fixed, by rule): the inventory script's "read-only" is a convention, not a structural guarantee**

`apps/backend/scripts/run_j11_pre_reset_inventory.py:102` uses `app.db.get_engine()`, which opens the SQLite file **read/write** and, per `app/db.py:54-65`, issues `PRAGMA journal_mode=WAL` on every connection. This iteration was safe and I confirmed it empirically (`PRAGMA journal_mode` already reads `wal`, so the pragma was a no-op; mtime/size identical throughout — see §3), but the guarantee is *detect-after*, not *prevent*: the script's `zero_write_proof` compares mtime **after** the connection has already been used, so a write would be reported, not prevented. The scenario that matters is the one goal.md step 13 prescribes: a failed Stage C attempt is followed by "(3) re-inventory the exact 11-date incident state" — and opening a database with a hot WAL read/write triggers WAL recovery/checkpoint, i.e. a write to `trendora.db` at the exact moment forensic evidence must be preserved. My own probes used `sqlite:///file:…?mode=ro&uri=true` (`connect_args={"uri": True}`) and read live rows fine; that is the structural form. Recorded as a GAP because this iteration's specified requirement (zero writes *during this iteration*) was met and proven — GAPs are documented, not fixed.

**B5 — OBSERVATION: `_count(session, Model, run_id=None)` renders `WHERE run_id IS NULL`, not "0 by construction"**

`app/engine/j11_maintenance.py:92-97` + `:153-156`: for a date with no run, `run_id` is `None` and SQLAlchemy turns `Model.run_id == None` into `IS NULL`, so the reported count is a *global* NULL-run_id count rather than a date-scoped zero. It is honest today — I verified all four columns are `NOT NULL` in the live DDL (`pragma_table_info` `notnull=1` for `scanner_results.run_id`, `sector_scores.run_id`, `theme_scores.run_id`, `forward_returns.run_id`) — so the value is necessarily 0. Latent only.

**B6 — OBSERVATION: private-symbol import.** `j11_maintenance.py:212` calls `engine_identity._config_value(...)`. It is the right function to reuse (it guarantees the cleartext `config_subset` decomposes the same values the digest folds in), but it is a private name; if that helper is ever renamed, the frozen artifact's human-auditable half breaks silently.

### Frontend Findings

None — `Frontend Present: no`, zero UI surface, and the UI-chain artifacts correctly record a contract skip rather than a pass: `reports/phase-goal-market-compass-iter-10-ui-test-results.md` reads `**Browser QA Verdict:** SKIPPED` with "no backend or frontend was started, no browser was opened, and no replay was partitioned or run", and no journey is marked from a lane that did not run.

### Test Findings

**T1 — VERIFIED SOUND (no finding): TC-3 is not passing vacuously.** The obvious way this test set could be worthless is if the fixture's connect-time `PRAGMA foreign_keys=ON` never actually landed — then "delete succeeded, no FK violation" would prove nothing. I ran a control through the identical engine + `event.listens_for(eng, "connect")` mechanism: `PRAGMA foreign_keys` reads `1`, and deleting a parent row of a hand-made table pair **that does** carry an FK raises `IntegrityError`. The pragma enforces; TC-3's pass is meaningful. Separately confirmed that current metadata emits no FK for `next_session_manifests`, so re-adding `foreign_key="scanner_runs.id"` would make TC-3 fail — the declaration is genuinely pinned by a test.

**T2 — GAP: no test covers the empty-`generation_json` degenerate input.** See B2. `test_tc5_degenerate_orphan_...` covers "no surviving run"; nothing covers "run exists, no recorded basis", which is the branch that fabricates `available` on live data.

**T3 — OBSERVATION: `test_capture_pre_reset_inventory_shape_and_counts` is shape-only.** It asserts presence/absence and zeros on an empty fixture; the substantive correctness of the inventory is carried entirely by the live artifact. That is acceptable here because I re-derived the live numbers independently (§3), but the function's per-date count semantics are not pinned by any test with non-trivial data.

**T4 — Pre-existing failure independently reproduced and confirmed out of scope.** `tests/test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` fails (`1 failed, 1 passed in 0.06s`); every offender is in `indicators.py`, `forward_testing.py`, `research.py`. `git log -1 -- <those three files>` → `99142a43 2026-08-11`, i.e. before this iteration; none appears in `status.json:changed_files`. The dev/reviewer/QA triage of this is correct.

---

## 3. Domain Assessment

**Stage B (inventory) — solid, and independently re-derived, not accepted on trust.** I re-ran the whole 11-date × 7-column matrix against the live DB read-only with a single self-contained SQL statement and got an exact match with `runs/goal-market-compass-iter-10/j11-pre-reset-inventory.json`, including the two counter-intuitive rows that would expose a lazy capture (2026-08-12 `fr_own=0` while `fr_into=20`; 2026-08-10 `fr_into=124`), plus `data_provider_runs=549`, `watchlist=6`, and both ledger sha256s (`5d435cff…`, `3e85847e…`, matched with `sha256sum`). `daily_prices` re-verified a third independent time: `3310374 | 1996-01-02 | 2026-08-12` — identical to the artifact's `row_count`/`min_date`/`max_date` and to QA's figures. The `.first()`-per-date lookup cannot under-report, because `scanner_runs` carries `CREATE UNIQUE INDEX ix_scanner_runs_asof_date` (verified) — one run per `as_of` maximum. The dual `forward_returns` populations (originated-from-run vs measured-into-date) are a genuine improvement over the spec's minimum and matter directly to Stage E.

**Stage B2 (frozen identity) — mechanism correct, scope narrower than its claim.** The helper is pure, per-run, and fail-closed on `None` (`j11_maintenance.py:226-236`), with matching, mismatched, and `None` cases asserted as separate assertions rather than an aggregate — the iter-9 lesson is genuinely applied, not merely cited. Reuse of `compute_engine_identity` is the right call and is corroborated by live data: the frozen `6261ca17…` equals the `engine_identity` already stamped on run 3148. The limitation is B3: the digest covers three compass-side files and three compass config keys, so it certifies "same manifest engine", not "same scoring engine".

**Stage B1 (schema contract) — the declaration is right; the proof is narrower than recorded.** The `models.py` comment reproduces goal.md:1151-1157's "Intended end state" verbatim (I diffed it phrase by phrase; only markdown bold markers differ) and correctly states that `basis_disclosure` never dereferences `source_run_id` — which I confirmed by reading `compass.py:1100-1115`. The FK declaration drop is real and test-pinned. What is over-claimed is coverage: five of six acceptance items hold for a metadata-built database, two do not hold for the live one, and item 6's read path has a live counter-example (B2).

**Zero writes (TC-8) — independently verified.** `apps/backend/data/trendora.db` reads `mtime=1787482245 size=8365871104` before my work and identically after every audit command including two pytest runs, five read-only sqlite sessions, and a live `basis_disclosure` evaluation. That matches the dev handoff's pre-work value exactly (and the artifact's `mtime_before=1787482245.3511636`), so nothing in the dev, review, QA **or** audit phases wrote to it.

One honest correction about my own footprint, which doubles as evidence for B4: `apps/backend/data/` held no `-wal`/`-shm` sidecars when I began, and holds two now — my read-only probes created them. They are `trendora.db-wal size=0` (zero frames: nothing was ever staged for a write) and `trendora.db-shm size=32768` (the shared-memory index every WAL reader needs). `trendora.db` itself is untouched — `size=8365871104 mtime=2026-08-23 11:50:45.351163677`, identical to its pre-iteration value — so TC-8 holds. The point worth carrying to Stage C is that even a `mode=ro` connection touches the database *directory*; on a database with a **hot** WAL, a read/write open (what `get_engine()` does today) would go further and checkpoint into the main file.

**Lane compliance (TC-9/TC-10) — verified.** `runs/goal-market-compass-iter-10/depth-dispatched` reads `full` (the dev handoff's note that it was missing is stale — it exists now, so TC-9 is satisfied). `journey-history.json` is byte-identical to the pre-iteration snapshot: `md5sum` of `runs/goal-session-market-compass/state/journey-history.json` and `runs/goal-session-market-compass/iter-10/journey-history.pre.json` are both `9757ed93107f9f3a4f3e24eee4947379`, and per-journey statuses for J-01…J-11 are unchanged. No `reports/qa/goal-market-compass-iter-10-evidence/` directory and no replay output exist.

**Tests re-run by me (targeted only, sequential, never concurrent):**
- `cd apps/backend && .venv/bin/python -m pytest tests/test_j11_maintenance.py -q` → **9 passed in 0.67s**
- `cd apps/backend && .venv/bin/python -m pytest tests/test_manifest_invariants.py -q` → **37 passed in 3.24s** (no regression)
- `tests/test_j10_recovery.py` (50 passed) accepted on the reviewer's and QA's two independent executions rather than a third run, per the resource contract.

---

## 4. Fixes Applied During This Audit

**None.** No source file was modified. Each IMPORTANT finding is barred from an in-audit fix by an explicit binding constraint, and applying one anyway would have traded a documented gap for a contract violation:

| # | Severity | Would-be fix | Why not applied |
|---|----------|--------------|-----------------|
| B1 | Important | Rewrite the live `next_session_manifests` DDL | Writes to `trendora.db` — violates DoD TC-8 and spec line 39; goal.md:1158 routes it to an owner decision instead |
| B2 | Important | Change `compass.basis_disclosure`'s empty-`generation_json` fallback | `compass.py` is reference-only in the plan; changes the served `basis` for 10 manifests while `Product surface delta: None` and the verifying browser/replay lanes are forbidden |
| B3 | Important | Widen `config.yaml` `provenance.engine_files` | Moves `engine_identity` for every future run/manifest — research-provenance change, explicitly OUT OF SCOPE, owner sign-off |
| B4 | Gap | Open the live DB via a `mode=ro` URI | GAP-level by the severity tree — documented, not fixed (fixing would be scope creep) |

---

## 5. Recommended Next Step

**Do not treat Stage C's precondition gate as cleared.** goal.md:1140 is literal — "Stage C may not begin until all six of these are proven" — and items 1 and 4 are demonstrably unmet on the live database (B1). The next iteration should **not** be a C→G destructive slice by default. Order of business:

1. **Owner decision on B1 (blocking).** Present the two options goal.md:1158-1159 anticipates: (a) accept the live DDL as-is with an explicit, dated amendment recording that acceptance items 1 and 4 are satisfied at the model/metadata layer only and that the live table keeps an inert, already-violated FK; or (b) authorize a bounded 24-row rewrite of `next_session_manifests` (small in rows, but a write to the 7.8 GB file, so it needs its own single-writer isolation and byte-for-byte preservation proof). Until one is chosen, Stage C stays shut.
2. **Fold B2 into Stage C/D/G scope explicitly.** Whatever clears the 2026-08-12 derived state must also decide what `basis` the empty-`generation_json` v1 manifest discloses after the rebuild — today it will still say `available`, contradicting its own v2–v6. AG-12 forbids mutating the manifest, so the fix belongs in `basis_disclosure`'s degenerate branch (an honest "no recorded basis" state), with a fixture test for it, executed in an iteration whose verification lanes are open.
3. **Re-freeze identity at Stage C time and decide B3's scope.** `freeze_attempt_identity` must be called again immediately before Stage C (the dev handoff already says this, correctly). Separately, decide whether the attempt-identity invariant is allowed to be blind to `scanner.py`/`scoring.py`; if the AVB dollar-volume fix lands between the freeze and Stage D, the invariant will not notice, so Stage G needs an independent check that all 11 rebuilt runs came from one code state.
4. **Adopt the `mode=ro` URI in the Stage C retry inventory (B4)** before any re-inventory that could run against a hot WAL.
5. **Correct the record:** the review's `definition_of_done: complete` and QA's checked DoD line for the six acceptance items should be read as superseded by §2/B1 of this audit. Stage B and Stage B2 stand as delivered.
