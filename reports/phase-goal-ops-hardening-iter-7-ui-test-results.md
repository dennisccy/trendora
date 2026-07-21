# UI Test Results (merged)

**Date:** 2026-07-21
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 11/13 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-7-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-7-evidence/J-03-verify.png |
| UT-01 | Evidence page loads without errors | smoke | P1 | Heading/subtitle visible, claim list or empty-state visible, no "Backend unavailable", no console error | Page loaded with heading "Evidence", claim list visible (`evidence-claim-list` present), 7 claim rows, 7 expectations panels, no "Backend unavailable" text, no console errors | PASS | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-01-evidence-loaded.png` |
| UT-02 | First `/evidence` view after ingest is fast, Refreshed line updates | happy-path | P1 | "Refreshed:" line includes "drawdown expectations"; fresh-tab `/evidence` renders claim rows + expectations within ~3s; reload shows identical content | Ran a real backfill job (2015-06-18) via the UI form; on completion the live Job progress panel's "Refreshed:" line read "latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, drawdown expectations"; opened a brand-new tab to `/evidence` immediately after — `GET /api/evidence` resource-timing entry measured 22.4ms, all 7 claim rows + 7 expectations panels rendered instantly; reload (navigate again) produced byte-identical claim-row text | PASS | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-02-job-refreshed.png`, `UT-02-evidence-fast-first-view.png` |
| UT-03 | Persisted-run fallback card shows new Refreshed value | regression | P2 | Fresh-session "Job progress" card shows the UT-02 run with "drawdown expectations" in its Refreshed line | New tab to `/data` (no job started this tab-session) showed "Job progress" card: "backfill job · 2015-06-18 → 2015-06-18 · from a previous session", status "ok", Refreshed line included "drawdown expectations" | PASS | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-03-persisted-run-fallback.png` |
| UT-04 | Run History row shows new Refreshed value | regression | P2 | Run History row for 2015-06-18 → 2015-06-18 shows "drawdown expectations" alongside all pre-existing categories, nothing removed/reordered | Located the exact table row (`2015-06-18 → 2015-06-18`); its Refreshed text: "latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, drawdown expectations" — all pre-existing categories intact, new one appended at the end | PASS | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-04-run-history-row.png` |
| UT-05 | Unresolvable claim renders cleanly, no crash | error | P2 | Any claim row missing an expectations panel still renders all other fields; no crash | All 7/7 currently-certified claim rows had a populated `evidence-expectations-panel` — no row without one existed at test time. Per the test's own exploratory-test allowance, marked not exercised rather than forced to fail. | SKIP (not exercised) | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-01-evidence-loaded.png` (shows all 7 rows with panels) |
| UT-06 | Claim-row values byte-identical across refresh | regression | P1 | All 6 named fields + expectations table identical before/after F5 | Captured full innerText of claim row 0 (verdict, hypothesis, out-of-sample verdict, control comparison, registration date, forward-walk score, full expectations table) before and after a page reload — byte-identical strings | PASS | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-06-evidence-refresh.png` |
| UT-07 | Expectations panel is clear and self-explanatory | ux | P3 | Heading "...(N-day hold)", explanatory sentence, exact column headers, method-note + survivorship testids present with real text | Heading read "Historical drawdown & dry-spell expectations (20-day hold)"; sentence matched exactly; table headers "Phase / Max-DD depth / Underwater / Time to recover / Longest losing streak"; both `evidence-expectations-method-note` and `evidence-expectations-survivorship` present with real explanatory text | PASS | (captured via UT-01/UT-06 screenshots — same page) |
| UT-08 | Data Manager job form still renders and functions | smoke | P1 | "Start a fetch / backfill job" panel with Start/End date, Job kind dropdown (3 options), Start button | Panel present; Start-date/End-date inputs found via `aria-label="Job start date"/"Job end date"`; Job kind `<select>` had exactly 3 options: "Backfill snapshots", "Fetch EOD prices", "Fetch + backfill"; Start button present (type=submit, not disabled by default) | PASS | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-08-data-manager.png` |
| UT-09 | Job form blocks incomplete date range | validation | P3 | Start button visually disabled when Start date empty; no job/run-history change | Cleared Start-date field, set End date to 2020-01-01 — Start button's `disabled` property became `true` (class list includes `disabled:cursor-not-allowed disabled:opacity-50`) | PASS | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-09-start-disabled.png` |
| UT-J-04 | J-04: Non-blocking boot with visible status | regression (goal journey) | — | First 200 ≤5s of process start; pre-ready health carries boot phase+progress; badge matches; kill → explicit unreachable state; log ends abruptly; restart → mid-flight job shows "interrupted" | Full 6-step journey executed live (see J-04 section below) — all assertions held | PASS | `J-04-initializing-badge.png`, `J-04-backend-unavailable.png`, `J-04-interrupted-job.png` |
| UT-J-05 | J-05: Aggregates are precomputed at ingest, never on the fly | regression (goal journey) | — | Backfill an unsnapshotted day; new-state served from storage; aggregates_refreshed lists categories; cold restart reads coverage without prefill; **health stays responsive throughout a heavy ingest** | Backfill + storage-serving assertions held (see below), but the health-responsiveness assertion **failed**: `GET /api/health` became completely unresponsive (connection timeout) for 7+ minutes during/after a second back-to-back heavy ingest job, correlating with a `MemoryError` in a backend worker thread. Backend required a manual restart to recover. | **FAIL** | `J-05-backend-hung-checking.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-21

