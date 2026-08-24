# Iteration 12 — Coherence Audit

**Iteration:** goal-market-compass-iter-12
**Date:** 2026-08-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration touches exactly one registered Data Contract row — "Next-session manifest —
FREEZE/INTEGRITY block", specifically its `basis_disclosure` sub-contributor — plus one internal
tooling fix (`j11_schema_migration`) and one comment correction (`models.py`) that touch no
displayed value at all.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `basis.status` (manifest FREEZE/INTEGRITY block) | OK | `apps/backend/app/engine/compass.py:1100` (sole producer, unchanged identity — `app.engine.compass.basis_disclosure`); sole call site `apps/backend/app/api/compass.py:43` (`GET /api/compass`); reuses the existing `_utc_isoformat` helper (`compass.py:664`, called again at `compass.py:1153,1174`) rather than a new parser |
| `j11_schema_migration.create_shadow_table` (internal migration tooling, not a displayed value) | OK — no Data Contract row; fixture-only this iteration | `apps/backend/app/engine/j11_schema_migration.py:277-303`; call site updated in `apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py:124` — not invoked against `apps/backend/data/trendora.db` (confirmed by the read-only fingerprint diff below) |
| `models.py` `source_run_id` provenance comment | OK — documentation only, no code/value change | `apps/backend/app/models.py:819-856` |

Verification detail: `grep -rn "basis_disclosure" apps/backend/app` shows exactly one production
definition (`app/engine/compass.py:1100`) and exactly one production call site
(`app/api/compass.py:43`); the only other match is `run_j11_stage_b1_live_reverification.py:88`,
which calls the SAME canonical function read-only for evidence generation, not a second producer. That
script's local `_is_degenerate_generation_json` helper (`run_j11_stage_b1_live_reverification.py:65-75`)
computes a different predicate (whether `generation_json` is degenerate, for the TC-23 `preFreezeEra`
overlap tally) — it never assigns or returns a `basis.status` value itself, so it is not a duplicate
computation of the registered value.

No new endpoint reads or recomputes `basis.status`; no new UI surface exists this iteration (no
frontend file changed, confirmed by `git diff <snapshot-sha> --stat -- apps/frontend/` returning
empty). The A4-bis change narrows which raw inputs map onto the EXISTING `unverifiable` literal
(already registered in the blueprint since iter-11) — no new literal, no new field, no schema change.
The blueprint's iter-12 update note (`runs/goal-session-market-compass/state/blueprint.md:143-156`)
correctly records this as additive/no-contract-change, matching what the diff actually shows.

Zero-live-write constraint (the operational contract for this audit and the iteration's own DoD):
confirmed via `runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-diff.json`
(`"diffs": []`, `"identical_except_capture_timestamps": true`) — before/after fingerprints of
`daily_prices`, `scanner_runs`, `next_session_manifests` (rows + DDL + indexes), `forward_returns`,
`data_provider_runs`, `watchlist` are identical. This audit itself opened no database file and issued
no queries against `apps/backend/data/trendora.db`.

## Information Architecture check

No new page, route, or nav-reachable feature this iteration — confirmed by an empty
`apps/frontend/` diff and by `reports/phase-goal-market-compass-iter-12-ui-surface-map.md`, which
records "Not mapped this iteration — maintenance isolation... No surface was opened or inspected."
The blueprint's IA skeleton (`runs/goal-session-market-compass/state/blueprint.md:18-57`) is
unchanged.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no frontend/route change this iteration) | N/A | — |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None material to coherence. (The reviewer separately flagged a cosmetic NOTE — a nearby comment in
  `models.py` around line 868 still credits only iter-11's fix, not this iteration's A4-bis follow-on —
  but that is a code-quality nit already tracked by review, not a coherence/IA/Data-Contract issue.)
