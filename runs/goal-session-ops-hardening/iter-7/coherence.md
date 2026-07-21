# Iteration 7 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-7
**Date:** 2026-07-21
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

The iteration's whole diff is: one function extension in `apps/backend/app/engine/data_manager.py`
(`_refresh_ingest_aggregates`) and its accompanying unit tests in `apps/backend/tests/test_data_manager.py`.
No file under `apps/backend/app/api/**` or `apps/frontend/**` appears in the diff (confirmed via
`git diff 10e55a3c...HEAD -- apps/frontend` and `-- apps/backend/app/api`, both empty).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `drawdown_expectations` (per-claim expectations panel, `/evidence`) | OK | New warm call at `apps/backend/app/engine/data_manager.py:3171` invokes `forward_testing.compute_drawdown_expectations_cached(session, claim, cfg)` — the exact same function `build_evidence_payload` calls at `apps/backend/app/engine/evidence.py:153`. Same module (`app.engine.forward_testing`), same underlying cache table (`event_study_cache`), no new endpoint. Verified the claim-extraction is identical too: the new code's `entry.get("claim") if isinstance(entry.get("claim"), dict) else {}` (`data_manager.py:3161`) is byte-for-byte the same expression `_claim_row` uses at `evidence.py:96`, and the `FORWARD_WALK_TYPE` skip filter at `data_manager.py:3159` matches `evidence.py:141` exactly — so the warm path and the serving path key the cache identically (no risk of a warm/serve mismatch masquerading as "canonical"). |
| `aggregates_refreshed` (enumerated list field) | OK | Existing field on the existing `_run_detail()`/`JobProgress` record; this iteration only appends one more legal string, `"drawdown_expectations"`, gated on "actually warmed ≥1 key" (`data_manager.py:3172-3173`), mirroring the honesty convention already used for every other member of the list. No new field, no second record — matches `blueprint.md`'s Backfill run-summary contract row (updated in the same commit, additive only). |
| `/evidence` claim rows / proven-ness (`Evidence status / certified-claim`) | OK (untouched) | This row's own producer (`app.engine.referee` + `app.engine.ledger`, served by `GET /api/evidence`) is not touched by the diff; `drawdown_expectations` is a distinct, already-registered value (see the "Membership timeline / research hot-key caches" row), not a re-derivation of claim proven-ness. |

No new value/entity was introduced that isn't already in the Data Contract — `drawdown_expectations`
was already a registered concept (the blueprint's "Membership timeline / research hot-key caches" row
already named `event_study_cache` and `compute_drawdown_expectations_cached` as its producer before this
iteration per the iter-6 handoff record); this iteration only widens that row's "Served by" list and the
`aggregates_refreshed` enum to reflect the new warm timing, exactly as `docs/phases/goal-ops-hardening-iter-7.md`'s
"Data-contract additions" section states ("None new... same field, same computing module, same serving
endpoints").

## Information Architecture check

No new page, route, panel, or nav entry. `reports/phase-goal-ops-hardening-iter-7-ui-surface-map.md`
lists 4 changed surfaces (`/evidence` main panel latency; `/data`'s live Job progress panel, persisted-run
fallback card, and Run History table row) — all four are existing components on existing IA homes,
updated only because they render the pre-existing generic `aggregates_refreshed` list (`.map(...).join(", ")`)
which now has one more possible entry. `apps/frontend/**` has zero diff lines this iteration (confirmed by
`git diff` stat), so there is no new component to place or wire into nav.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/evidence` (latency-only change) | OK | Pre-existing nav item in `sidebar.tsx` per blueprint IA; no route change. |
| `/data` — `aggregates_refreshed` new list value | OK | Pre-existing nav item; rendered through the already-shipped generic renderer, no new component. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. The iteration is a textbook "extend the existing single producer, widen an already-registered
  enum" change: the blueprint.md diff (`runs/goal-session-ops-hardening/state/blueprint.md`) is purely
  additive documentation of the same rows already present, consistent with the code diff and the iter-7
  spec's own "Blueprint conformance" / "Data-contract additions" sections. No scattered navigation, no
  duplicate computation, no non-canonical source.
