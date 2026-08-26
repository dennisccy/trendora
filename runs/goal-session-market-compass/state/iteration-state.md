# Iteration State — market-compass

**After iteration:** 18 · **Date:** 2026-08-26 · **Verdict:** STALLED

## Journeys

3 passing (J-01 J-04 J-10) · 6 partial (J-02 J-03 J-05 J-06 J-09 J-11) · 2 failing (J-07 J-08) — 11 total. None re-verified this iteration: browser QA + replay lane forbidden by maintenance isolation.

## Active blockers

- **J-11 Stage D (rebuild the 11 damaged days) — OWNER.** `docs/goal.md:1738-1743` ruling item 9: "Even if all three are established, STOP... requires a separate later explicit owner authorization." All three status lines ARE now established.
- **All other journeys — OWNER, blocked by the same chain.** `docs/goal.md:2087-2090` shuts every lane against the damaged DB until J-11 Stage G passes. J-07/J-08 untouched since iter-1 for this reason.
- **Request-path write hole — OWNER decision (product behaviour).** `apps/backend/app/engine/scanner.py:348` (`resolve_run`, reached from every read endpoint's `?as_of=` via `app/engine/snapshot_serving.py:42`) writes a canonical ScannerRun for any date with NO boundary check. Boot paths are now guarded; this one is not. Fixing it edits `app/api/*`/serving code — the exact files whose untouched state is the ONLY basis for J-01/J-04/J-10 carrying forward, and unverifiable while browser QA is off.

## Last 2 verdicts

- iter 18: STALLED — owner-authorized table-create + live arm SUCCEEDED and was independently re-verified read-only; ruling item 9 mandates STOP even on success, and every remaining path is owner-owned.
- iter 17: STALLED — arm path built and tested but the live guard was NOT ARMED (table absent); creating it was forbidden by name at that time.

## Do not redo

- **`maintenance_boundaries` table + `j11-incident-recovery` row: LIVE, ARMED, VERIFIED.** Do not re-create, re-arm, disarm, or re-run `run_j11_maintenance_boundary_table_create.py` / `..._arm.py`. Evidence: `runs/goal-market-compass-iter-18/j11-iter18-live-preboot-guard-verification.json`.
- **Both boot-initiated `run_scan` gaps are closed** at `warmup.py:361` and `forward_testing.py:551`, sharing `j11_preboot_guard.evaluate_boundary_for_date_fail_closed`. Do not re-derive the boot call graph.
- **AVB volume correction (iter-16) is spent and verified intact** (554757 / 3706010). Never re-run `run_j11_avb_correction.py`. J-10 is CLOSED by owner ruling 2026-08-24.
- **Stage D readiness = YES (AVB-A)** is carried by citation from `runs/goal-market-compass-iter-17/j11-iter17-stage-d-readiness.json`. Do not re-derive; READY is not authorization.
- **Riders done:** evidence-collision refusals on both iter-17 CLI tools; AVB "genuinely independent" wording corrected; iter-17 UI-test-plan damaged-date list corrected. Iter-17's QA report list is deliberately NOT rewritten (annotate only, AG-17).
- **Framework defects are out of product scope, carried forward:** the `scripts/automation/` forbidden-lane defect, `goal_gate.py`'s duplicate-journey-heading defect (must close before any GOAL_ACHIEVED), and `build_review_packet`'s untracked-file blindness.
