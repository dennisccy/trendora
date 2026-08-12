# Iteration State — ops-hardening

**After iteration:** 70 · **Date:** 2026-08-12 · **Verdict:** CONTINUE

## Journeys

8 partial, all pending-infra (J-01 J-03 J-04 J-05 J-06 J-07 J-08 J-09) — 8 total · 0 failing · 0 regressed. NOTHING FAILED: the QA backend died between lanes, so browser QA was SKIPPED 0/8 and replay BLOCKED 0/7 ("never checked", not FAIL). Seven were passing at iter-69; J-07 was already partial.

## Active blockers

- **Re-verification owed for all 8 journeys** (dev) — the engine auto-schedules the make-up ride from `pending_infra`; the lane must confirm `GET /api/health` on :8255 answers 200 BEFORE checking starts. Backend is live now (PID 2027165). **Two-strike rule: if the lane is blocked a second consecutive round, that is human-owned → STALLED.**
- **J-07 last gaps** (dev + human) — browser half of TC-3 never ran; the poller started 32.1s late so `coverage_membership_timeline_refresh` is unmeasured, not proven clean; walkthrough clause unmet. Human: the 2-second ceiling policy (22nd round), `scripts/automation/browser-qa-phase.sh` sign-off, cost sanction (10th over-budget round, 18,042s vs 3,600s).
- **New silent failure mode** (dev) — `apps/backend/app/engine/readiness.py:567-575` serves the cache with no age check; a dead tick thread would answer 200 with a frozen "ready" forever (iter-70/d).

## Last 2 verdicts

- iter 70: CONTINUE — the fix landed and was verified from raw artifacts (1,030 polls, 0 breaches, 0 non-answers, max 1.226s; `readiness_s` p90 0.5631s → 0.000003s), but zero journey evidence was produced this round.
- iter 69: ESCALATE — a lean round surfaced a design change to a canonical producer (readiness/preflight off the request path), landing alongside the session's first non-answers.

## Do not redo

- **Moving readiness/preflight off the request path is DONE and PROVEN** — `app.engine.readiness` background-refresh cache, `health.py` reads `get_readiness_and_preflight`; TC-7 confirmed (`readiness_s`/`preflight_s` p90 ≈ 1e-6s across 1,065 records). Do not re-instrument these two components.
- **Bounding `factor_lab_all_warm` / `coverage_membership_timeline_refresh` by code change is NOT NEEDED** — 565 polls inside `factor_lab_all_warm` with 0 breaches (was 74/400). Released-but-unused alternative; revisit only if a re-measurement shows breaches there again.
- **iter-69/a /b /c /d are CLOSED** (phase grouping shipped; 83-record count corrected; 60d label corrected; the non-answers gone). Do not re-fix them. `reports/perf-budgets.md` Addendum 36 is append-only and audit-corrected — do not edit prior addenda.
- **Steps 3 (VmPeak) and 4 (memory-pressure abort) of J-07 carry on evidence durability** — warm-path code (`compute_forward_aggregates`, `research.py`) byte-identical. Re-measure only if that seam changes.
- **The three DB reads in `GET /api/health` stay on the request path** — deliberate, out of scope; `db_reads_s` is now the dominant server-side component but max 0.480s against a 2.0s ceiling.
- **Do not touch `config.yaml` caps, `project-extensions/host-guard/`, or the HOST-GUARD blocks** — AG-10 envelope is owner-set and verified intact this round.
