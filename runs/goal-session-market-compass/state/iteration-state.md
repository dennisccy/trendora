# Iteration State — market-compass

**After iteration:** 12 · **Date:** 2026-08-24 · **Verdict:** STALLED

## Journeys

3 passing (J-01 J-04 J-10) · 6 partial (J-02 J-03 J-05 J-06 J-09 J-11) · 2 failing (J-07 J-08) — 11 total. Maintenance isolation (ruling A5) has forbidden the browser + replay lanes since iter-9, so every status except J-11's is CARRIED, not re-verified; J-11 stays `partial` (Stage B1 complete, Stages C-G not started).

## Active blockers

- **HUMAN-OWNED, single, everything waits on it:** J-11 Stage C (destructive clear + rebuild of 11 dates on the live 8.4 GB `apps/backend/data/trendora.db`) may not begin without an explicit owner instruction — `docs/goal.md` J-11 step 11 ruling A12's closing sentence. Readiness answer produced and independently confirmed by the evaluator: **`J-11 STAGE C READY: YES`** (all 13 A12 items re-derived read-only). Owner options: (a) say go + `--resume`; (b) require the future-migration gap closed first (`j11_schema_migration.py:301` + `verify_and_finalize` read the ORM model's column list, not the real table's — no causal path into Stage C); (c) reword the gate in `docs/goal.md`.
- **Standing (non-blocking):** the forbidden-lane defect in `scripts/automation/` is still uncured — suppressed by the isolation contract for 4 iterations.
- **New, non-blocking:** `goal_gate.py hash-journeys` covers only the TAIL of J-10's block (a nested `- **J-10` bullet fools the extractor), so owner edits to J-10's Steps do not trip `journeys-changed.md`. Verify goal-text drift by diffing the journey's line range, not by the hash alone.

## Last 2 verdicts

- iter 12: STALLED — the four scoped cleanup jobs are genuinely done with ZERO live writes (db mtime 1787522416 = iter-11's own last write, 0-byte WAL, every table count unchanged, 24×28 manifest values identical); halting only because the next step is irreversible and owner-sanctioned.
- iter 11: REGRESSION — the authorized live migration removed the FK but also dropped 3 DEFAULTs and moved `version` ordinal 9→3, beyond AG-18's "and nothing else"; the owner has since accepted exactly that four-item residual (2026-08-24) and the verdict STANDS unrewritten (A14).

## Do not redo

- **J-10 is CLOSED and must not be reopened** — 585 restored, EA + EQR accepted unrestorable, AG-9's fetch exception exhausted. Re-derived read-only in iter-12 (585 symbols on each date, frontier 2026-08-12, `daily_prices` 3,310,374, `data_provider_runs` 549). Never re-run `run_j10_population_recovery.py`.
- **The four DDL residuals are ACCEPTED, not to be repaired** — no second live rewrite of `next_session_manifests` is authorized (A8/A9, AG-18 "Bounded exception on record"). Re-verified: column set identical, only 3 DEFAULTs + `version`'s ordinal differ.
- **Stage B1 is COMPLETE** — live FK absent, `foreign_key_check` 0 rows with enforcement ON, 24 rows × 28 columns preserved, 3 original indexes. Do not re-migrate.
- **The migration utility fix (A10) is DONE and is fixture-only** — `create_shadow_table` derives from captured live DDL and fails closed; it must NOT be run against `apps/backend/data/trendora.db` (and now raises against today's FK-free DDL anyway).
- **`basis_disclosure` A4-bis is DONE** (`compass.py:1131-1178`) — live distribution independently re-derived as `unverifiable 8 / rebuilt 9 / available 5 / unavailable 2`; `models.py`'s provenance comment is corrected. Do not re-open either.
- **Deferred to Stage G, verified non-blocking, do NOT pull forward:** the `preFreezeEra` branch (honest — asserts no basis status; complete 8/8 overlap re-derived) and the manifest export-file discrepancies (3 recorded-missing, 4 on-disk orphans, all pre-dating this work).
