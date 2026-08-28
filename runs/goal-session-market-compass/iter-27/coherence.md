# Iteration 27 — Coherence Audit

**Iteration:** goal-market-compass-iter-27
**Date:** 2026-08-28
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Next-session manifest — FREEZE/INTEGRITY block (`basis.status`, incl. the `"unavailable"` literal) | OK | Computed by the SAME `app.engine.compass.build_manifest_payload`/`basis_disclosure`, served by the SAME `GET /api/compass` — `apps/backend/app/api/compass.py:60-69` only reorders which pre-existing calls run first; `apps/backend/app/api/compass.py:71-73` (unchanged `resolved_run`+`get_or_create_manifest` fallback) still owns the create branch |
| "Does a manifest already exist for this as-of" internal fact | OK — de-duplication, not a second producer | `apps/backend/app/engine/compass.py:1042-1057` (`latest_manifest_for_date`, new) is a pure `SELECT ... ORDER BY version DESC .first()` lookup of an EXISTING stored row — it computes nothing. `get_or_create_manifest`'s own existing-row check (`apps/backend/app/engine/compass.py:1072`, was an inline duplicate of the same query at old lines 1067-71) now calls this same helper. Before the diff there were two inline copies of one query shape; after, there is one function with two callers — this reduces divergence risk rather than introducing it. |
| Next-session manifest CONTENT block, engine identity, stock sector label, regime/phase/breadth, sector/theme scores, evidence ledger status (all other registered rows) | OK — untouched | `git diff <snapshot-sha> --stat` confirms zero changes to `apps/backend/app/engine/snapshot_serving.py`, `apps/backend/app/engine/scanner.py`, or any file under `apps/frontend/` — the shared self-heal machinery every other route depends on is byte-identical, and no other Data Contract row's producer or endpoint moved. |

No new displayed value is introduced this iteration (per the spec's own "New information displayed: None new" and confirmed against the diff — `apps/backend/tests/test_api_compass.py` is test-only). `basis.status == "unavailable"` was already registered in the blueprint's Data Contract since the iter-11 update; this iteration only makes an already-registered literal reachable through the live route, exactly as the blueprint's iter-27 note states.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /api/compass` (backend route reorder only) | OK — no new/changed page or nav | `apps/frontend/components/sidebar.tsx` not touched (confirmed via `git diff --stat` on frontend paths: zero files). The ui-surface-map (`reports/phase-goal-market-compass-iter-27-ui-surface-map.md`) independently confirms "0 files touched" on the frontend and "Navigation changes: no." The newly reachable `"unavailable"` badge state renders through the already-shipped `CompassManifestStrip`/`BasisLine` component on the existing Today (`/`) page — its canonical home per the blueprint's IA row "J-05 / J-06 manifest freeze + immutability" — no parallel shell, no duplicate home. |

No new page, route, or nav entry is introduced. The one behavior change (a previously-unreachable badge variant becoming reachable) surfaces inside the manifest strip that already lives on the Today page's registered home.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- Out of my Data-Contract/IA remit but worth carrying forward for the next iteration's awareness: per the pump coordinator's note and `docs/handoffs/goal-market-compass-iter-27-audit.md` (lines 97-111, 245, 261, 282), browser QA this iteration issued `GET /api/compass?as_of=2019-03-01` — a date outside the iteration's own TC-6/TC-7 authorized live-check list — which minted a real `next_session_manifests` row (id=26, `mode=retrospective`, `prospective_eligible=0`), taking the canonical DB's manifest count from 25 to 26. This is a test-scope/spec-discipline issue already caught and corrected by the independent auditor (dated correction appended to the dev handoff), not a Data Contract or IA violation: the new row was minted through the SAME unchanged create branch (`resolved_run`/`get_or_create_manifest`) that mints every other retrospective manifest, served from the SAME canonical `GET /api/compass` endpoint — no second producer, no second endpoint. Flagging only so any report still citing "25" is read as stale, per the auditor's own instruction.
- No unregistered values, no label/formatting drift observed in this iteration's diff — there is nothing new to render (0 frontend files changed).
