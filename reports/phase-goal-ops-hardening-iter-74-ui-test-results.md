# UI Test Results (merged)

**Date:** 2026-08-13
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** BLOCKED

**Overall:** 6/8 journeys passed (2 skipped, 2 required-unverified)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work (live job card, not persisted history) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-74-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-74-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status — regression-hardening golden (J-04's product behavior is already proven/evidenced; this asserts the readiness badge's REAL data-state attribute and a persisted data_provider_runs-backed field, never a bare page-title/heading match) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-74-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | Backfill of one unsnapshotted day computes and persists aggregates from storage; health stays responsive throughout | Ran a full independent live backfill (2019-01-31, job data_provider_runs.id=484); completed in 17m43s with all 9 finalize-tail aggregates refreshed; `/scanner-runs` and market-phase served correctly from storage; health responsive throughout (38 direct polls, 0 non-200s) | PASS | `reports/qa/goal-ops-hardening-iter-74-evidence/J-05-verify-final.png` |
| UT-J-06 | Pages load only what they need | regression | P1 | All 11 nav pages load with expected content and budgeted on-load API latency; readiness badge shows `ready` | All 11 pages loaded with correct headings/content; readiness badge `data-state="ready"` immediately (domInteractive 52ms); all budgeted endpoints (`/api/health`, bars, availability, `/api/runs`) responded well within their gates | PASS | `reports/qa/goal-ops-hardening-iter-74-evidence/J-06-pages-load.png` |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request (payload-gated) | regression | P1 | journey replays end-to-end; all expects hold | voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks | SKIP | reports/qa/goal-ops-hardening-iter-74-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks | SKIP | reports/qa/goal-ops-hardening-iter-74-evidence/J-09-verify.png |
| UT-J-07 | Heavy aggregates never take the service down | target | P1 | All 4 numbered steps hold: (1) a full deep-basis forward-aggregate warm runs while `/api/backtest` keeps serving every horizon; (2) `GET /api/health` answers HTTP 200 on every 1 Hz poll throughout, no frozen window; (3) the process's peak VmPeak during the warm is measured and recorded under `server.memory_cap_mb` with its margin in `reports/perf-budgets.md`; (4) an induced memory-pressure abort during a warm is graceful — the SAME process keeps serving `/api/health` and cached reads, never wedged/restarted | Steps 1+2 (browser-observable): readiness badge `data-state="ready"` on `/`; `/backtest` served real stored scorecard/leadership-cohort/expanding-window content (2,919 contributing snapshots) with no "Refreshing" banner; all 5 `GET /api/backtest?horizon={1,5,10,20,60}` calls answered HTTP 200 in 0.05–0.13s; a fresh 150-poll (2.5 min) 1 Hz `GET /api/health` run via the canonical `scripts/qa/poll_health.py` returned 150/150 HTTP 200, 0 breaches, max 0.098s. Step 3 (this round's actual target): **CLOSED** — this iteration's dev pass (`reports/perf-budgets.md` Addendum 39, corroborated directly: code diff confirmed in `test_start_backend_script.py`, `pytest --collect-only` re-confirmed 23 tests collected, `config.yaml` confirmed byte-unchanged) produced a COMPLETE, clean 9-of-9-finalize-tail-phase VmPeak profile under realistic pool pressure — peak 4,837,420 kB / 4,724.0 MB, 42.3% margin against the 8192 MB cap — plus 1,795/1,795 clean `GET /api/health` polls DURING that same real warm (bonus corroboration of step 2 under actual load, stronger than this pass's own steady-state poll). Step 4: not re-exercised this round (no live fault-injection lane in this dispatch or this iteration's dev scope) — carried on iter-58's own organically-witnessed real MemoryError (VmPeak pegged at the then-6144 MB cap) that left `/api/health` at 0 non-200 across 229 samples and the SAME process (pid 782444) serving a clean J-05 backfill minutes later; no lane this pass found any contradiction to that finding. | PASS | `reports/qa/goal-ops-hardening-iter-74-evidence/J-07-backtest-live.png` |

## Missing Required Journeys

_Required-still-passing journeys named in the iteration spec that were NOT verified this iteration — either no lane (deterministic replay or LLM browser-qa) produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-40 lesson: this is exactly how required journeys shipped with zero evidence while every gate reported clean)._

- `UT-J-08` — only a SKIP row for J-08: named but never executed
- `UT-J-09` — only a SKIP row for J-09: named but never executed

## Skipped Tests

### UT-J-08 — Backtest evidence serves from storage only — never a cold recompute on request (payload-gated)

**Verdict:** SKIPPED
**Reason:** voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks

### UT-J-09 — Disclose in-flight background-compute activity (badge + /data panel)

**Verdict:** SKIPPED
**Reason:** voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-13

