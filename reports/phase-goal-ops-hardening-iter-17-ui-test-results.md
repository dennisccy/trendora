# UI Test Results (merged)

**Date:** 2026-07-24
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 8/10 journeys passed (1 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-17-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-17-evidence/J-03-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-17-evidence/J-05-verify.png |
| UT-01 | `/backtest` loads without errors (main) | smoke | P1 | Page renders; heading+as-of badge+Survivorship card visible; scorecard/leadership headings above populated tables; no console errors | **Raw/real (as literally specified):** stuck on "Backend unavailable"/NO-GO indefinitely — Environment Finding 1. **Under the diagnostic workaround:** heading, "Ready"/DEGRADED banner, Survivorship card, populated scorecard/leadership all render correctly, no console errors | FAIL | `reports/qa/goal-ops-hardening-iter-17-evidence/UT-01-top.png` (raw), `UT-01-top-workaround.png` (workaround) |
| UT-02 | `not_yet_computed` empty state renders (throwaway) | smoke | P1 | Page renders, no Backend-unavailable card; bottom dashed card w/ flask icon, exact title+description, no "run an ingest", not duplicated; survives refresh | Loaded via `http://localhost:13255/backtest` (Finding 2 — the dispatched `127.0.0.1` form is CORS-blocked); rendered cleanly, **no workaround needed**. Bottom card text matches spec verbatim; F5-equivalent refresh reproduced identical content, zero new console errors. As-of-scan-summary was POPULATED (not "unavailable" as the plan assumed) — the throwaway DB has real snapshot data through 2026-07-01 with only `forward_aggregate_cache` emptied (matches the pump note precisely); the plan itself flags that bullet as "not the focus of this test" | PASS | `reports/qa/goal-ops-hardening-iter-17-evidence/TC-09-not-yet-computed-state.png` |
| UT-03 | Live capture: corrected banner + `evidence_asof` (main) | happy-path | P1 (time-boxed) | Banner text exact match; real calendar date before "generated"; evidence still populated below; screenshot saved to the reserved filename | `/data`'s own page could not be driven via browser (Finding 1b — missing chunk); submitted the IDENTICAL `POST /api/data/jobs {kind:"backfill",start:"2025-05-29",end:"2025-05-29"}` a real "Start" click would issue (fresh gap date, not one of the 5 already-taken dates). `/backtest` (workaround-patched) then rendered the banner with the EXACT expected sentence, "2026-07-22" as a real date before "generated", and fully populated evidence below it | PASS | `reports/qa/goal-ops-hardening-iter-17-evidence/TC-07-refreshing-banner-with-asof.png` |
| UT-04 | Evidence section populated in ready state (main) | regression | P1 | Populated evidence section; either no banner (ready) or a refreshing banner over still-populated numbers — both PASS; only an empty not-yet-computed card is a FAIL | Workaround-patched: confirmed BOTH accepted shapes — plain ready/no-banner (DOM-verified before UT-03's job existed) and refreshing-with-populated-numbers (screenshot, captured mid-UT-03-job) — never the empty card | PASS | `reports/qa/goal-ops-hardening-iter-17-evidence/UT-04-ready-evidence-bottom-refreshing.png` |
| UT-05 | Scorecard/leadership sections unaffected (main) | regression | P1 | Scorecard: one row/horizon, numeric or "—"; Top Sectors/Themes: ranked w/ score+return; Ranked cohort: rank/ticker/setup/leadership/return populated | Workaround-patched: Forward-test scorecard shows 5 horizon rows (1d/5d/10d/20d/60d), each "—"/n=0 (correct NA — latest date has no elapsed forward window); Top Sectors (5) + Top Themes (5) ranked w/ score badges; Ranked cohort shows 10 rows, all columns populated | PASS | `reports/qa/goal-ops-hardening-iter-17-evidence/UT-01-top-workaround.png` (scorecard), extracted DOM text for leadership/ranked-cohort (see below) |
| UT-06 | Empty-state copy reads factually (throwaway) | ux | P2 | States fact + resolution without commanding; discloses no-fabrication; one clean sentence, no duplicated opening clause | Same page load as UT-02 (`localhost:13255`): text confirmed verbatim — no "run an ingest"; explicit "no numbers are fabricated in the meantime"; single clean sentence, title not repeated in the body | PASS | `reports/qa/goal-ops-hardening-iter-17-evidence/TC-09-not-yet-computed-state.png` |
| UT-J-04 | J-04: Non-blocking boot with visible status (regression journey) | regression | P1 (journey) | This iteration's own scope is a non-disruptive steady-state check only (no kill/restart) — health 200/ready; log shows no new crash/restart banner | Fresh `GET /api/health` → 200, `readiness:"ready"`, `db_ok:true`. `logs/backend.log` grew 41568→42382 lines with zero new `launching`/`Shutting down`/`Finished server process` lines (no crash since the last recorded launch, 2026-07-24T01:41:20Z). Full kill/restart replay not performed (binding out-of-scope this iteration, matching iter-14/15/16 precedent). The badge's real-time browser observability is currently compromised by Environment Finding 1 on the raw path; the workaround shows the underlying readiness-computation-and-display logic itself is unaffected and correct | SKIPPED | n/a — see dedicated section below |

## Failed Tests

### UT-01 — `/backtest` loads without errors (main)

**Verdict:** FAIL
**Failure:** **Raw/real (as literally specified):** stuck on "Backend unavailable"/NO-GO indefinitely — Environment Finding 1. **Under the diagnostic workaround:** heading, "Ready"/DEGRADED banner, Survivorship card, populated scorecard/leadership all render correctly, no console errors
**Evidence:** ``reports/qa/goal-ops-hardening-iter-17-evidence/UT-01-top.png` (raw), `UT-01-top-workaround.png` (workaround)`

## Skipped Tests

### UT-J-04 — J-04: Non-blocking boot with visible status (regression journey)

**Verdict:** SKIPPED
**Reason:** Fresh `GET /api/health` → 200, `readiness:"ready"`, `db_ok:true`. `logs/backend.log` grew 41568→42382 lines with zero new `launching`/`Shutting down`/`Finished server process` lines (no crash since the last recorded launch, 2026-07-24T01:41:20Z). Full kill/restart replay not performed (binding out-of-scope this iteration, matching iter-14/15/16 precedent). The badge's real-time browser observability is currently compromised by Environment Finding 1 on the raw path; the workaround shows the underlying readiness-computation-and-display logic itself is unaffected and correct

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-24

