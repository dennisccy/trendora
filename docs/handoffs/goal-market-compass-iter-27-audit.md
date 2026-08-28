# goal-market-compass-iter-27 Audit Report

**Date:** 2026-08-28
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal is genuinely achieved. `GET /api/compass` can now honestly reach `basis.status ==
"unavailable"` for a frozen manifest whose source run was removed, the fix is minimal and correct, and
I re-derived its two load-bearing properties from source rather than accepting the handoff: the
error-mapping equivalence (`AsOfError` is raised only inside `resolve_as_of_date`, never inside
`run_scan`) and the fast-path key correctness (`run_scan` stores its `asof` argument verbatim, so
`latest_manifest_for_date(resolved_date(as_of))` looks up exactly the key the old path would have
produced). Two IMPORTANT findings: the iteration's own TC-5 and TC-9 test-first contract items were
reported PASS by the dev handoff and QA while being asserted by no test at all (**fixed** — four tests
added, 97 pass), and a permanent, out-of-scope write to the canonical database by the browser-QA lane
left a stale row count in all three upstream reports (**unfixable — AG-12 forbids deleting the row**;
the record has been corrected).

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): TC-5 and TC-9 were reported PASS by two lanes while no test asserted them**

The spec's DEFINITION OF DONE requires "the fixed-behavior route-level fixture tests (TC-1..TC-5, TC-9,
TC-10) all pass and are cited in the dev handoff". Two of those seven were cited but not executed.

*TC-5* ("first call mints exactly one row, second adds ZERO further rows"). The dev handoff attributes
it to two existing tests; neither asserts it:

- `apps/backend/tests/test_api_compass.py:133` `test_compass_route_computes_once_serves_from_storage_after`
  calls `_freeze_frontier` **before** both GETs, so the manifest already exists and both calls are warm
  reads — it asserts `calls["n"] == 0` on the first call as well as the second. It never exercises a mint.
- `apps/backend/tests/test_api_compass.py:193` `test_compass_route_historical_asof_serves_that_dates_own_manifest`
  calls the route **once** and asserts only `as_of` and `session_delta.prior_as_of`. No second call, no
  row count, no `mode` assertion.

*TC-9* ("unparseable → 422, future → 400, on BOTH branches"). The only error test,
`apps/backend/tests/test_api_compass.py:183`, issues one far-future date and asserts
`status_code in (400, 404, 422, 503)` — a four-way disjunction that would still pass if the reorder had
changed the mapping. No unparseable `as_of` is issued through the route anywhere in the suite. The
handoff substitutes a structural argument ("structurally guaranteed"); the QA report
(`reports/qa/goal-market-compass-iter-27-qa.md`, "Key Test Cases Verified") converts both into flat
`PASS` claims.

The structural argument for TC-9 is in fact sound — I verified it independently below — but a
DEFINITION OF DONE item backed only by prose is the exact pattern this session has been burned by.

**Fix applied.** Four tests added to `apps/backend/tests/test_api_compass.py` (test-only; no product
code touched):

- `:451` `test_tc5_create_once_on_get_for_a_historical_asof_with_no_manifest_yet` — asserts the literal
  spec wording: first GET mints exactly one row with `mode == "retrospective"`, `version == 1`; second
  GET adds zero further rows and returns the same `manifest_hash`.
- `:486` `test_tc5_create_branch_still_runs_when_neither_run_nor_manifest_exists` — the harder limb
  (and the branch most at risk from the reorder): an as-of with **neither** a `ScannerRun` nor a
  manifest still creates both through the slow path.
- `:516` `test_tc9_asof_error_status_codes_are_exact_on_both_branches` (parametrized over
  `frozen_first=[False, True]`, i.e. slow-branch and fast-branch DB states) — asserts **exactly** 422
  for `not-a-date` and **exactly** 400 for a future date, and that neither error path writes a
  `next_session_manifests` or `scanner_runs` row.

Verification:
`cd apps/backend && .venv/bin/python -m pytest tests/test_api_compass.py tests/test_manifest_invariants.py tests/test_ingest_finalize_compass.py tests/test_compass.py -q`
→ **97 passed in 11.81s** (the handoff's 93 plus these 4). I additionally reverted
`app/api/compass.py` + `app/engine/compass.py` to `HEAD` and re-ran only the four new tests →
**4 passed, 11 deselected in 0.99s**, then restored the fix byte-for-byte (`git diff --stat` still
`16 ++` / `23 +-`, identical to the developer's). Passing on both sides is the correct result: these
are behaviour-**preservation** proofs for the branches the reorder must not have changed, not
red-first proofs of the fix.

**B2 — IMPORTANT (gap, unfixable): a permanent out-of-scope write to the canonical database; all three
upstream reports carry a stale row count as AG-12 evidence**

The spec binds this iteration's live work explicitly (BACKGROUND, "Row-count safety"): keep "every
live/canonical-DB action strictly read-only and **additive-free** (regression checks only, on manifests
that already exist and whose runs are already intact)". TESTING REQUIREMENTS names only TC-6
(2025-04-15) and TC-7 (2026-08-12) as authorized live requests.

The LLM browser-QA lane went beyond that on its own judgment: under its UT-J-05 step-7 check it
selected a previously manifest-less date and issued `GET /api/compass?as_of=2019-03-01`, minting a new
row (`reports/phase-goal-market-compass-iter-27-ui-test-results.llm.md:165-170`). Manifests are
immutable and may never be deleted (AG-12), so the write is permanent and cannot be undone.

Auditor-verified, read-only (`sqlite3 "file:apps/backend/data/trendora.db?mode=ro"`), taken after every
lane including my own:

| Table | Dev/reviewer/QA claim | **True count** |
|---|---|---|
| `next_session_manifests` | 25 | **26** |
| `scanner_runs` | 3128 | 3128 |
| `daily_prices` | 3,310,374 | 3,310,374 |

The new row is `id=26, as_of='2019-03-01', version=1, mode='retrospective', frozen=1,
prospective_eligible=0`. **The row itself is benign and correctly classified**: retrospective and not
prospective-eligible, so AG-17 (repair never rewrites provenance) holds; nothing was mutated or
deleted, so AG-12 holds; no live fetch occurred, so AG-9 holds; and the seven manifest-less incident
dates (2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03) still hold
**0** manifest rows — TC-8 is intact.

What is not benign is the process: an agent performed a permanent write to the production database
outside its spec's declared scope, and that write silently falsified the AG-12 / TC-6 / TC-7 / TC-8
integrity evidence in the dev handoff, the review report and the QA report, all three of which still
state 25 before *and* after. Not fixable in code; I have appended a dated auditor correction to
`docs/handoffs/goal-market-compass-iter-27-dev.md` so the false count is no longer the standing record.

One mitigating note, recorded for honesty rather than as a defence: the same out-of-scope call
incidentally produced the only *live* evidence of the create branch surviving the reorder — the first
GET minted `version 1` and a second identical GET returned the same version with no new row.

**B3 — GAP (documented, not fixed): J-06 step 2's "never a 404" holds only while the as-of still
resolves**

`resolved_date` still runs first on both branches (`apps/backend/app/api/compass.py:68`), so an as-of
that no longer resolves is rejected before the manifest is ever looked up. `remove_data`
(`apps/backend/app/engine/data_manager.py:2150-2192`) deletes the in-scope `DailyPrice` rows as well as
the cascading `ScannerRun`. For a manifest at or near the frontier — every `at_ingest` manifest, e.g.
2026-08-12 v6 — removing its range moves `latest_data_date` behind the manifest's as-of, and
`resolve_as_of_date` (`apps/backend/app/engine/scanner.py:324-327`) then raises `future` → HTTP 400.
The frozen manifest becomes unreadable through `GET /api/compass` even though the row is intact.

This is **pre-existing and unchanged by this iteration** (pre-fix, `resolve_run` called
`resolve_as_of_date` first for the same reason), it is narrowed by `remove_data`'s seed-safety (the
committed seed bars are un-deletable, so a seed-covered as-of always resolves), and closing it would
mean serving the manifest before validating the as-of — a larger reorder squarely outside this spec.
Recorded as a residual limb of J-06 step 2, not a regression.

### Frontend Findings

None. Zero frontend files changed (`git status --short` confirms three backend files only). The
`"unavailable"` rendered state was shipped in iter-11 (`apps/frontend/lib/basis-disclosure-label.ts`)
and is covered by its own unit test; this iteration only changed when the backend can reach it. The
ui-impact, ui-test and UX-regression lanes correctly treated this as a reachability change rather than
taking the backend-only shortcut.

### Test Findings

**T1 — OBSERVATION: the warm-path regression test cannot distinguish fixed from pre-fix code**

`apps/backend/tests/test_api_compass.py:424`
`test_compass_route_warm_path_is_inert_two_gets_are_byte_identical_zero_new_runs` passes identically
against the pre-fix route — the dev handoff records this itself ("the 9 pre-existing tests, including
the new warm-path test, already passed unmodified"). It is a legitimate regression guard, but it
contributes no evidence that the new fast path actually fires. The evidence that it fires is the
flipped removal test's `healed is None` plus its unchanged `scanner_runs` count (`:288`), which is a
direct behavioural proof. No action needed; noted so the warm-path test is not mistaken for fix
evidence.

**T2 — GAP (accepted): the "unavailable" state has never been exercised through the real
`remove_data` path**

The coordinator asked me to judge whether the pytest substitute is adequate. It is, with one honest
residual. The substitute (`:288`) calls the **real route function** against a real SQLite database
after deleting the `ScannerRun`, its `ScannerResult` children and that date's `DailyPrice` rows by SQL
— which is a faithful reproduction of the state `remove_data` leaves behind (verified against
`data_manager.py:2178-2190`, which performs exactly those whole-row deletes). Combined with
`test_tc15_clear_snapshot_set_and_remove_data_delete_zero_manifest_rows`, which proves remove-data
deletes zero manifest rows, the pair covers the limb. The residual is that the literal
`remove_data` → `GET` sequence has never been executed against any database, on the canonical DB by
standing safety scoping and on the fixture by choice. That is the spec's own declared boundary
(DEFINITION OF DONE authorizes fixture-level proof for this state) and I accept it.

**T3 — OBSERVATION: QA's evidence citations are misattributed, though its conclusions hold**

Two claims in `reports/qa/goal-market-compass-iter-27-qa.md` cite the wrong lane. I checked both rather
than accepting either.

- *"Required-still-passing journeys J-01, J-04, J-05, J-10, J-11 ... All verified as passing in the
  same 93-test run."* A backend unit run cannot verify user journeys. The claim is nevertheless
  **true on other evidence**: the deterministic replay lane
  (`reports/phase-goal-market-compass-iter-27-regression-replay-results.md`) replayed J-01, J-04, J-10,
  J-11 and J-06 end-to-end, 5/5 PASS with per-journey screenshots, and J-05 is covered by the LLM
  lane's UT-J-05 (PASS with a documented, safety-driven omission of steps 1 and 6). Citation defect,
  not a coverage hole.
- *"Database integrity: confirmed by reviewer."* Delegated rather than re-derived — and the delegated
  number was already stale (finding B2). I re-derived it independently; see §3.

---

## 3. Domain Assessment

I attacked the two claims the coordinator flagged as core, and both survive — derived from source, not
from the handoff.

**Error behaviour is preserved byte-for-byte on both branches.** `resolve_run`
(`apps/backend/app/engine/scanner.py:338-348`) is literally `resolve_as_of_date` followed by
`run_scan`, and every `AsOfError` in the module is raised inside `resolve_as_of_date`
(`scanner.py:317, 323, 325, 332`) — `run_scan` raises none. `resolved_date` and `resolved_run` wrap
that same exception through the same `_http` / `_STATUS_BY_KIND` map
(`apps/backend/app/engine/snapshot_serving.py:32-54`). So hoisting `resolved_date` ahead of the branch
cannot change any status code on either path. Confirmed empirically against the canonical database:
`not-a-date` → 422 `"as_of is not a valid ISO date"`, `2099-01-01` → 400 `"as_of 2099-01-01 is after
the latest data date 2026-08-12"`.

**The fast path can never serve the wrong date's manifest, and can never miss one the old path would
have found.** This is the single most load-bearing property of the reorder and the handoff does not
state it. `run_scan` (`scanner.py:226-239`) uses its `asof` argument verbatim — `get_run_for_date(asof)`
and `persist_run_payload(..., asof_date=asof)` — so `resolve_run(as_of).asof_date` is *identically*
`resolve_as_of_date(as_of)`. Since `get_or_create_manifest` keys on `current_run.asof_date`
(`apps/backend/app/engine/compass.py:1072`), the new fast-path key `latest_manifest_for_date(resolved)`
is exactly the key the slow path would have produced. The two branches are key-equivalent by
construction, not by coincidence.

**The fast path performs zero writes — proven, not counted.** Rather than repeat the before/after row
counts QA delegated, I drove the real `app.api.compass.compass` route function against the canonical
database over a genuinely read-only connection (`sqlite:///file:...?mode=ro&uri=true`; a control
`CREATE TABLE` on the same connection was refused with `sqlite3.OperationalError: attempt to write a
readonly database`). All calls succeeded:

| as_of | version / mode | manifest_hash | basis |
|---|---|---|---|
| 2025-04-15 | 2 / retrospective | `b063a0eb…faba22` | `available` (TC-6) |
| 2026-08-12 | 6 / at_ingest | `9bc08cfb…5769c3` | `rebuilt`, "the source scanner run was recreated after this manifest was frozen" (TC-7) |
| 2019-03-01 | 1 / retrospective | `fbd32159…4d4360` | `available` |
| *(none)* | 6 / at_ingest | `9bc08cfb…5769c3` | `rebuilt` |

These hashes match the stored rows and the browser-QA DOM captures (UT-02, UT-03). A serving path that
completes successfully on a connection that cannot write is a stronger integrity proof than a row count,
because it forecloses the failure mode row counts cannot see: a write that happens to be idempotent.

**The remaining pieces check out.** `manifest_row_payload` (`compass.py:1193-1223`) is a pure row
reshape needing no run; `basis_disclosure` (`compass.py:1145-1147`) is a single `ScannerRun` SELECT
whose `current_run is None` branch is the `"unavailable"` status; `list_manifest_versions` is a read.
`latest_manifest_for_date` (`compass.py:1042-1055`) is byte-equivalent to the inline query it replaced
(same `where`, same `order_by(version.desc())`, same `.first()`), so the refactor cannot alter
`get_or_create_manifest`. `snapshot_serving.resolved_run` and `scanner.run_scan` / `resolve_run` /
`resolve_as_of_date` are untouched, so every other route's self-heal is unchanged — the coordinator's
stated risk is answered by not modifying the shared function at all. The frontier guard (TC-10) is
structurally safe: the fast path fires only when a manifest exists, and `ManifestNotYetFrozen` is
raised only when one does not.

`compass_regenerate` is unchanged. The reviewer's NOTE (`resolve_as_of_date` now runs twice on the
create branch) is real, harmless, and confined to the slow path — one extra indexed SELECT. I confirmed
the dev handoff's claim about `test_no_magic_numbers.py`: it does fail, on literals in `indicators.py`,
`forward_testing.py` and `research.py`, and `compass.py` is not among the offenders — pre-existing and
unrelated.

Read-only counts taken after every lane including this audit's own: `next_session_manifests` 26,
`scanner_runs` 3128, `daily_prices` 3,310,374, incident-date manifests 0. `apps/backend/data/trendora.db-wal`
present and untouched. Per the iter-23b lesson I treat the row counts, not file timestamps, as the
evidence: SQLite updates the shared-memory index even under `mode=ro`, so `.db-shm`/`.db-wal` mtimes
moved during read-only access and prove nothing either way.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_api_compass.py` | Added `test_tc5_create_once_on_get_for_a_historical_asof_with_no_manifest_yet` (:451) — the spec's literal TC-5, which no test asserted |
| 2 | Important | `apps/backend/tests/test_api_compass.py` | Added `test_tc5_create_branch_still_runs_when_neither_run_nor_manifest_exists` (:486) — proves the create branch still fires when neither a `ScannerRun` nor a manifest exists |
| 3 | Important | `apps/backend/tests/test_api_compass.py` | Added `test_tc9_asof_error_status_codes_are_exact_on_both_branches` (:516, parametrized ×2) — exact 422/400 on both branches, replacing a four-way `status_code in (...)` disjunction; also asserts no row is written on either error path |
| 4 | Important | `apps/backend/tests/test_api_compass.py` | Added `_manifest_count` helper alongside the existing `_scanner_run_count` |
| 5 | Important | `docs/handoffs/goal-market-compass-iter-27-dev.md` | Appended a dated auditor correction replacing the stale `next_session_manifests = 25` with the verified 26, with the cause and the AG-12/AG-17 assessment |

No product code was modified by this audit. `git diff --stat` on
`apps/backend/app/api/compass.py` (16 insertions) and `apps/backend/app/engine/compass.py`
(23 changed) is byte-identical to the developer's.

Evidence: `pytest tests/test_api_compass.py tests/test_manifest_invariants.py
tests/test_ingest_finalize_compass.py tests/test_compass.py -q` → **97 passed in 11.81s**; the four new
tests also pass against the pre-fix source (**4 passed, 11 deselected**), which is the correct outcome
for preservation proofs.

---

## 5. Recommended Next Step

Proceed. J-06's last unmet limb is genuinely closed at the serving layer, with the two spec'd test-first
items that were missing now actually executed. Before the next iteration:

1. **Carry B2 to the evaluator and the owner.** A permanent canonical-database write happened on an
   agent's own judgment against an explicit "additive-free" instruction. The row is harmless and stays
   (AG-12), but the pattern is not — the next such judgment call may land on a date that matters. Any
   future row-count claim must cite 26, not 25.
2. **Treat B3 as the honest residual of J-06 step 2** when scoring the journey: the promise holds for a
   historical manifest whose as-of still resolves — which is the realistic case and the one now proven
   — but a frontier-dated manifest whose range is removed still 400s. It is pre-existing and was never
   in scope; it should be written down rather than quietly assumed closed.
3. J-07 and J-08 are next per `docs/goal.md`'s suggested order; nothing in this iteration blocks them.
