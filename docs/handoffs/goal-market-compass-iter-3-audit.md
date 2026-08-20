# goal-market-compass-iter-3 Audit Report

**Date:** 2026-08-20
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The freeze/integrity pair (J-05/J-06) is genuinely built, not merely rendered: one writer
(`compass._freeze_manifest`, `compass.py:881`) behind all three producer paths, a fail-closed
`prospective_eligible`, correctly-scoped dual + split-rule hashes, real 539-row cohorts read through
bounded per-run queries, a committed schema that actually rejects a missing required field, and a
manifest strip that re-derives nothing client-side. Two real defects were found by tracing the unhappy
paths the handoffs did not: the export writer **silently overwrote an already-frozen artifact** (AG-12,
reproduced and fixed during this audit), and TC-10's "underlying run unavailable" basis disclosure is
**unreachable through the sole read path** because a plain GET silently re-creates the removed source
run (reproduced, not fixed — it needs an owner decision about the product-wide as-of contract). Neither
breaks the phase goal: stored manifests remain immutable and every served value traces to a stored row.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the at-ingest export writer silently overwrote an existing frozen artifact (AG-12)**

`compass._write_export` (`apps/backend/app/engine/compass.py:841`) wrote
`export_dir/<as_of>_v<version>.json` with an unconditional `path.write_text(...)`. Any second write for
the same `(as_of, version)` replaced the bytes of an artifact an existing immutable row's `export_path`
already pointed at — precisely what AG-12 forbids ("a stored row **and its exported file** are never
mutated ... by any later ingest, rebuild, data removal, config change, or code change").

Reproduced (throwaway probe, isolated export dir): a second freeze of the same `(as_of, version)` wrote
the *same* path with *different* bytes and a different embedded `manifest_hash`
(`2024-06-03_v1.json`: `d2547fb2eb17` → `72b8e03a339f`; `same path: True | bytes changed: True`).

Two reachable triggers, neither theoretical:
1. **Concurrency.** `_freeze_manifest` writes the export *before* the INSERT (`compass.py:980-982`,
   deliberate — `export_path` must be in the single write). A losing create-once/regenerate race
   (`compass.py:1014-1037`) therefore leaves the **loser's** bytes on disk while returning the winner's
   row, whose `export_path` names that file. Two concurrent `POST /api/compass/regenerate` calls both
   compute `latest.version + 1` (`compass.py:1087`) and both target the same file name.
2. **Shared export dir.** Unit tests inherit the product's configured
   `compass.manifest.export_dir` — proven on disk: `apps/backend/data/exports/next_session_manifests/`
   holds four synthetic test artifacts (`2024-06-08_v1.json`, `2024-07-01_v1.json`, `2024-07-08_v1.json`,
   `2024-08-01_v1.json`, all written 12:10 during the QA test run) sitting beside the real
   `2026-08-12_v5.json`. A test fixture whose synthetic as-of ever matched a real frozen at-ingest date
   would have overwritten the real artifact.

**Fix applied.** Exclusive create (`open(path, "x")`, `compass.py:860`); on `FileExistsError`
(`compass.py:862`) identical bytes return the path unchanged (idempotent), differing bytes log an error
and return `None` so `export_path` stays NULL — an honest gap, never a mutated artifact. Plus a
session-autouse fixture (`apps/backend/tests/conftest.py:31-45`) pointing
`TRENDORA_COMPASS_EXPORT_DIR` at a per-run temp dir so no test writes into the product directory at
all, and a regression test
(`test_manifest_invariants.py:138 test_tc15_export_writer_never_rewrites_an_existing_artifact`).

Verification: `cd apps/backend && .venv/bin/python -m pytest tests/test_manifest_invariants.py -q` →
**37 passed** (was 34; the 3 additions are mine); `pytest tests/test_api_compass.py tests/test_compass.py
tests/test_ingest_finalize_compass.py tests/test_engine_identity.py -q` → **46 passed**. After both runs
the product export dir was byte-for-byte unchanged (no new files, timestamps still 12:10).

**B2 — IMPORTANT (gap, not fixed): TC-10's "unavailable" basis disclosure cannot be produced by
`GET /api/compass`; a plain read silently re-creates the removed source run**

`basis_disclosure`'s `unavailable` branch (`compass.py:1107`) requires no `ScannerRun` for the as-of at
read time. The route can never observe that state: `api/compass.py:59` calls
`snapshot_serving.resolved_run` → `scanner.resolve_run` (`scanner.py:338-348`) → `run_scan(...)`, which
**re-creates** the missing run before the manifest is ever read.

Reproduced: with the source run deleted, `compass_route("2024-06-03", session)` returned
`basis={'status': 'rebuilt', ...}` and `scanner_runs` afterwards contained `['2024-06-10', '2024-06-03']`
— the run reappeared as a side effect of a GET. Called directly at the engine layer with the run absent,
the same row correctly yields `{'status': 'unavailable', ...}`.

Consequences against the spec's own TC-10 ("still serves the manifest verbatim with a read-time basis
disclosure stating the underlying run is unavailable — never a 404, never a recompute"):
- the disclosure says `rebuilt`, never `unavailable`, for a removed-then-read date;
- when the removal also drops the frontier bars — J-05 step 1's own "remove the last two trading days"
  precondition — `resolve_as_of_date` raises `future` (`scanner.py:324-327`) and the endpoint answers
  **4xx**, the opposite of "never a 404";
- a read of a frozen manifest triggers a full scan recompute of its source run (the manifest *content*
  is still served verbatim from storage, so immutability itself is not breached).

Not fixed deliberately: making `unavailable` reachable means the compass read path must resolve a stored
manifest *before*, and independently of, the as-of resolution contract every other as-of endpoint shares
(including its "as_of after the latest data date is an error" honesty rule). That is a product-contract
decision for the owner/evaluator, not a surgical audit edit. Both branches are now pinned at the engine
level by the two tests added below, so a future regression in either is caught cheaply.

**B3 — GAP: the exported-file byte-equality contract (TC-4) has no automated test**

The spec's TESTING REQUIREMENTS list "the exported-file byte-equality + tamper detection" as a
unit/integration item. Tamper detection exists (`test_manifest_invariants.py:300`, document-level);
byte-equality is evidenced only by the dev handoff's manual live check. The spec's export-failure error
case ("write failure ... leaves `export_path` NULL") is likewise untested (the *phase-level*
isolate-and-continue is tested at `test_ingest_finalize_compass.py:78`). After B1's fix the
overwrite-refusal path is covered; a genuine `read exported bytes == stored payload` assertion is still
absent.

### Frontend Findings

**F1 — GAP: TC-1 and TC-9/10/11 were executed by no lane**

UT-12 (the finalize "Refreshed: next-session manifest" disclosure, TC-1) was **skipped** for
host-safety, and the remove/backfill basis-flip trio (TC-9/10/11) has no browser test at all and — as
the reviewer noted for the code half — no unit test either before this audit. TC-1's rendered string is
correct by construction: `refreshed.append("next-session_manifest")`
(`data_manager.py:4554`) through the humanizer `a.replace(/_/g, " ")`
(`apps/frontend/app/data/page.tsx:2653`) → "next-session manifest". The DoD's "J-05 (TC-1..TC-8) /
J-06 (TC-9..TC-25) pass via browser-qa-agent" is therefore partially, not fully, browser-substantiated.

**F2 — OBSERVATION: the regenerate control's `asOf !== null` gate does not exclude the live frontier**

`compass-manifest-strip.tsx:240` enables Regenerate whenever the as-of switcher is off "Latest".
Stepping *to the frontier date* makes `asOf` non-null, so the live frontier's manifest is regenerable
from the UI (mode `at_ingest`, export written) — the frontend handoff documents this as a convenience
gate, not a safety guarantee, and the backend contract intentionally allows it. Pre-fix this was the
user-reachable path into B1; post-fix the artifact is protected. The in-flight `disabled` state
(`:244`) blocks a double-click within one tab but not two tabs.

**F3 — OBSERVATION: `formatFactValue` renders every number with two decimals**, so an integer fact
renders as `candidate_count: 0.00` (browser QA UT-09 recorded exactly that). Honest and TC-36-compliant,
but a count reading "0.00" is marginally less human-readable than the artifact it replaced was wrong.

**F4 — OBSERVATION: after a regenerate the default read serves the newest version** and the UI lists v1
only as a stamp row (version/mode/eligibility/timestamp, `:224-238`) — its frozen *content* is not
viewable anywhere in the UI. This matches TC-12 as written ("the UI lists both versions with their
stamps"); flagged only because "a historical view never substitutes a newer manifest" (AG-12) reads
close to this behaviour under a version-level interpretation.

### Test Findings

**T1 — GAP: `test_tc15_clear_snapshot_set_and_remove_data_delete_zero_manifest_rows`
(`test_manifest_invariants.py:118`) never calls `remove_data`** — only `clear_snapshot_set`. The name
claims coverage the body does not have. I verified the underlying claim independently: no code path
anywhere deletes a `NextSessionManifest` row (`data_manager.remove_data:2170-2178` and
`clear_snapshot_set:2224-2228` delete only ForwardReturn / ScannerResult / SectorScoreRow /
ThemeScoreRow / ScannerRun; a repo-wide grep finds no other manifest delete). The invariant holds; the
test is misnamed.

**T2 — OBSERVATION: TC-15's static UPDATE audit is a blunt proxy.** It flags *any* `.update(...)`
attribute call and scans only `app/engine/*.py` — effectively compass.py alone. It would false-positive
on a `dict.update` and does not cover `app/api/*.py`, which does call `payload.update(...)`
(`api/compass.py:70`, a dict update). It passes today for the right reason, but not because of what it
measures.

**T3 — OBSERVATION: TC-22 flips a field in a parsed dict**, not a byte in a copied export file as the
spec's wording asks; TC-16's "two independent builds" are two sequential calls in one session; TC-14
perturbs a post-as-of bar but never deletes one. All three still prove their invariant's core, with
less strength than the spec's phrasing implies.

**T4 — GAP: TC-32/TC-33's evidence make-up is not closed.**
`runs/goal-session-market-compass/state/journey-history.json` still records `evidence_makeup: true` for
J-01–J-04, and no `demo.sh market-compass --session-live` `[NEW]` walkthrough set exists for them (the
iter-3 demo run recorded 8 iter-3 steps only). Partial substitutes exist and are real: deterministic
replay recordings `J-01..J-04-verify.png` and the Risk-off caution screenshot `UT-10-result.png`
(as-of 2025-04-15, ATR + REGIME_RISK_OFF cautions on a candidate card). Flipping that flag is the
goal-evaluator's call, not this audit's.

---

## 3. Domain Assessment

The freeze/integrity domain logic is sound and, in the places that matter most, better than the
handoffs claim.

- **Immutability (the J-06 core) holds.** `_freeze_manifest` is INSERT-only; both IntegrityError guards
  return the already-committed row rather than overwriting (`compass.py:1014-1037`); no UPDATE and no
  DELETE targets `next_session_manifests` anywhere in the tree (verified by grep, not by the test that
  claims it — see T1). `manifest_row_payload` (`compass.py:1118`) is a pure re-shape of stored columns.
- **Fail-closed eligibility is real.** `_derive_prospective_eligible` (`compass.py:797`) requires all
  nine conditions conjunctively; `regenerate_manifest` needs no special-casing because `producer` and
  `version` alone already force `false` — version-shopping is structurally impossible, not policed.
- **Hash scoping is correct.** `manifest_hash` covers the whole document with only itself excluded and
  is assembled pre-INSERT; the three rule identities partition exactly as TC-23 demands (I re-derived
  the subsets at `compass.py:684-715` against the matrix). `available_at_utc` reuses the single
  `generated_at` instant, so the fence is exactly reproducible rather than approximately.
- **AG-8 bounded reads are genuine.** Cohorts use one column-projected member sweep plus two per-run
  fetches (`_record_json_by_ticker`, `_theme_rank_by_slug`), and every cohort field is a *read* of an
  already-stored value — I verified the two non-obvious derivations against the producer:
  `distance_from_52w_high` = the stored `high_proximity` raw (`scoring.py:163,179`, `dist_from_high`,
  ≤ 0) and `adv_dollars` = `-liquidity` raw (`scoring.py:190`, stored as `_neg(adv)`). AG-3 holds for
  the new numbers.
- **AG-2/AG-11/AG-13 hold.** The banned-language guard now runs over candidate reasons/cautions/
  invalidation/why-not before any candidate is returned (`compass.py:604`); cohort rows carry no new
  numeric beyond the named context fields; `preflight_verdict` is recorded in `generation` and rendered
  nowhere in the strip.
- **One honest wart, spec-mandated:** every non-qualifying member is labelled
  `below_selection_floor`, including names that clear the leadership floor and fail only the Entry or
  Risk qualifier (the handoff's own HPE example: leadership 92.7, entry 21.7). The spec explicitly
  ordered this partition reuse, so it is not drift — but as a frozen, exported label it will read to a
  downstream consumer as "leadership below floor", which is not what it means.
- **`content_hash` is no longer recomputable from the served document:** the writer pops
  `comparison_cohort` / `near_threshold_shadow` / `member_count` out of `selection` *after* hashing
  (`compass.py:884-887`), so the exported shape differs from the hashed shape. The consumer contract
  AG-16 actually specifies (`manifest_hash` over the artifact bytes) is fully satisfied; `content_hash`
  is a producer-side identity only.
- **Schema/DDL:** the committed schema's `required` list covers every field the spec names and really
  does reject a missing one; the `(as_of, version)` swap follows the idempotent guarded pattern with no
  table rewrite. Minor: `models.py:817` still declares `as_of` `index=True`, and `_INDEX_DROPS`
  (`db.py:172`) drops that index at every boot — model and boot state disagree, harmless because the
  composite unique index serves as-of-prefix lookups.

**Spot-verification note (mechanical DoD items).** TC-34/TC-35/TC-36 and the manifest strip's
visibility/reachability/controls were accepted on the reviewer's PASS (`reports/reviews/…-review.md`:
`definition_of_done: complete`, `scope_creep: none`, single MINOR test-coverage issue) **plus** an
executed browser row each (UT-10, UT-09, UT-01/02/03/04/05/06/11/13). Everything touching state
transitions, persistence or immutability — the freeze writer, all three producer paths, eligibility,
hashing, the export writer, the DDL swap and the basis disclosure — was traced through the code, and
the two riskiest paths were additionally executed.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/compass.py:854-871` | `_write_export` now creates the artifact exclusively (`open(path,"x")`); an existing file with identical bytes is idempotently accepted, one with different bytes is refused with a logged error and a NULL `export_path` — a frozen export is never rewritten (AG-12) |
| 2 | Important | `apps/backend/tests/conftest.py:31-45` | Session-autouse fixture pointing `TRENDORA_COMPASS_EXPORT_DIR` at a per-run temp dir, so no test can write into the product's configured `compass.manifest.export_dir` |
| 3 | Important | `apps/backend/tests/test_manifest_invariants.py:138` | New `test_tc15_export_writer_never_rewrites_an_existing_artifact` — a second freeze of the same `(as_of, version)` leaves the existing bytes untouched and reports `export_path is None` |
| 4 | Important | `apps/backend/tests/test_manifest_invariants.py:170,188` | New `test_basis_disclosure_reads_unavailable_when_the_source_run_is_gone` and `…_rebuilt_when_the_source_run_is_recreated` — close the reviewer's flagged zero-coverage gap on both non-default basis branches and assert the frozen document is served byte-identically across a rebuild |

Post-fix verification (single pytest process, targeted files only):
`cd apps/backend && .venv/bin/python -m pytest tests/test_manifest_invariants.py -q` → **37 passed**;
`… -m pytest tests/test_api_compass.py tests/test_compass.py tests/test_ingest_finalize_compass.py
tests/test_engine_identity.py -q` → **46 passed**. No previously-passing test changed behaviour, and
the product export directory was untouched by both runs. No dev-handoff claim was invalidated by these
fixes (the handoff's "rare orphan-file case" note is now obsolete — that case is refused, not orphaned).

---

## 5. Recommended Next Step

Proceed to the goal-evaluator with J-05/J-06 substantiated, carrying three items forward:

1. **Owner/evaluator decision on B2** — should `GET /api/compass` serve a stored manifest for an as-of
   whose source run (or whose bars) are gone, ahead of the shared as-of resolution contract? Until that
   is decided, TC-10's "unavailable" disclosure is engine-only and the removed-frontier read answers
   4xx. This is the one acceptance criterion the implementation cannot currently meet.
2. **Cheap follow-ups, not blockers:** an automated export byte-equality assertion (B3); rename or
   extend the misnamed `remove_data` immutability test (T1); delete the four stray synthetic export
   artifacts now sitting in `apps/backend/data/exports/next_session_manifests/` (pre-existing pollution;
   fix #2 prevents recurrence).
3. **Evidence lane:** TC-32/TC-33's `evidence_makeup` flag for J-01–J-04 is still `true` in
   `state/journey-history.json`; decide whether the replay recordings + `UT-10-result.png` discharge it
   or whether a `--session-live` walkthrough pass is still owed. Note also that the ux-regression lane
   was shed by the SPEED-15 trim this iteration.
