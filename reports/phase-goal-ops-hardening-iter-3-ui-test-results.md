# UI Test Results (merged)

**Date:** 2026-07-20
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 10/13 journeys passed (1 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-3-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-3-evidence/J-03-verify.png |
| UT-01 | `/data` loads with coverage panel visible | smoke | P1 | Heading, subtitle, all 7 stat tiles populated, both panels visible, no error card | All present exactly as specified; Universe 540, Symbols 591, Trading days 5380, Snapshot dates 762, Backfill gaps 4618 all non-blank | PASS | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-01-result.png` |
| UT-02 | Fetch lands new bar -> coverage refreshes + persists after reload | happy-path | P1 | Job settles ok/partial; coverage panel auto-updates with Symbols/Trading days/Snapshot dates higher; same numbers survive hard reload; never false all-zero | Job settled ("partial") both times tried; NONE of Symbols/Trading days/Snapshot dates increased (see Failed Tests); Price History end-date DID advance and DID persist after reload, proving the underlying storage-refresh mechanism fires, but the test's specific named fields did not move | FAIL | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-02-coverage-after-reload.png` |
| UT-03 | Repeat fetch is a fast, silent no-op | regression | P1 | 2nd run no slower than 1st; coverage numbers identical; normal terminal status, nothing new | Run1 12.98s, Run2 8.49s (2nd faster, not slower); all 6 tracked coverage fields byte-identical before/after; both settled "partial" (steps text explicitly allows partial as a settle state) with the same stable 429 ok/162 failed split both times | PASS | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-03-repeat-fetch-noop.png` |
| UT-04 | Fresh DB boot shows honest all-zero coverage | regression | P1 | All-zero coverage on very first request against a never-ingested DB | Not executed — see Skipped Tests | SKIP | none |
| UT-05 | Multi-day backfill still renders breakdown + updates coverage | regression | P1 | Breakdown line with real numbers, chunk badge if applicable, Snapshot dates up / Backfill gaps down by the right amount | "8 calendar days . 1 already snapshotted . 2 non-trading" rendered; chunk 1/1 (range too small to need chunking, correctly omitted); Snapshot dates 762->767 (+5), Backfill gaps 4618->4613 (-5), exact match to snapshots_created=5 | PASS | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-05-backfill-breakdown.png` |
| UT-06 | Backend stays "Ready", job panel keeps ticking during heavy job | regression | P1 | Header badge stays "Ready" throughout; heartbeat/activity line keeps advancing, never freezes or shows "possibly stalled"; ends "ok" | Header badge DID stay "Ready" throughout (confirmed) BUT the Job progress panel's heartbeat froze for ~260-270s (of ~316-327s total) after the per-date scan finished, and the UI visibly showed "updated 33s ago . possibly stalled" live in the browser; reproduced twice | FAIL | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-06-possibly-stalled.png` |
| UT-07 | Malformed date blocks submit with inline error | validation | P2 | Red inline "Enter a valid date..." message + triangle icon, red border, Start disabled | All confirmed via DOM inspection: `aria-invalid="true"`, `border-neg` class, `lucide-triangle-alert` svg, exact message text, `btnDisabled: true` | PASS | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-07-invalid-date.png` |
| UT-08 | Backend-unavailable shows honest error card | error | P2 | Warning-triangle card, bold "Backend unavailable", exact explanatory text below, no coverage numbers shown | Backend killed; page rendered exactly: "Backend unavailable" / "Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry." with AlertTriangle icon (confirmed in source); zero coverage numbers rendered | PASS | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-08-backend-unavailable-card.png` |
| UT-09 | "Refreshed:" line absent for fetch, present for backfill | regression | P2 | Fetch run/row: no "Refreshed:" line despite coverage updating; backfill run/row: "Refreshed: coverage, ..." present | Every fetch job this session showed `aggregates_refreshed: []` (API) and no "Refreshed:" text anywhere in its Run-history entry; every backfill job showed a populated `aggregates_refreshed` list including "coverage" and the matching UI line, e.g. "Refreshed: latest snapshot, coverage, membership timeline, market phase, research hot keys" | PASS | see UT-02/UT-05 evidence + inline JSON in this report |
| UT-10 | "Job kind" dropdown is clear and form adapts | ux | P3 | 3 plain-worded options, Import source shown only for Fetch/Fetch+backfill, no layout breakage | Options exactly "Backfill snapshots" / "Fetch EOD prices" / "Fetch + backfill" (no raw codes); Import source select appears (2 selects) for both fetch kinds and disappears (1 select) for Backfill snapshots; no visual breakage across all 3 states | PASS | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-10-fetch-backfill-form.png` |
| UT-J-04 | J-04: Non-blocking boot with visible status (regression journey, executed per goal.md) | regression | P1 | Restart->first-200 <=5s; a pre-ready payload carries boot phase + progress n/m; kill->explicit crashed presentation distinct from initializing; logfile has boot events and ends abruptly after a kill; restart->mid-flight job shows explicit "interrupted" state, never still-"running" | All 6 steps confirmed directly: first 200 at 1.49s; captured "initializing" + "history 89/89" + status="running" for a real ~2s pre-ready window; killed backend -> badge "Backend unavailable" + banner "Backend is unavailable — the preflight check could not run." (distinct wording from the initializing/servability-gap case); logfile's fresh boot marker present, prior lines end on a plain request log with no shutdown line; restarted -> the killed job (id 65, 2012-01-01->2013-12-31) now shows `"status": "interrupted"` with its last real persisted progress (0/0, honestly reflecting how little it had done) in Run history | PASS | `reports/qa/goal-ops-hardening-iter-3-evidence/J-04-crashed-badge.png` |

## Failed Tests

### UT-02 — Fetch lands new bar -> coverage refreshes + persists after reload

**Verdict:** FAIL
**Failure:** Job settled ("partial") both times tried; NONE of Symbols/Trading days/Snapshot dates increased (see Failed Tests); Price History end-date DID advance and DID persist after reload, proving the underlying storage-refresh mechanism fires, but the test's specific named fields did not move
**Evidence:** ``reports/qa/goal-ops-hardening-iter-3-evidence/UT-02-coverage-after-reload.png``

### UT-06 — Backend stays "Ready", job panel keeps ticking during heavy job

**Verdict:** FAIL
**Failure:** Header badge DID stay "Ready" throughout (confirmed) BUT the Job progress panel's heartbeat froze for ~260-270s (of ~316-327s total) after the per-date scan finished, and the UI visibly showed "updated 33s ago . possibly stalled" live in the browser; reproduced twice
**Evidence:** ``reports/qa/goal-ops-hardening-iter-3-evidence/UT-06-possibly-stalled.png``

## Skipped Tests

### UT-04 — Fresh DB boot shows honest all-zero coverage

**Verdict:** SKIPPED
**Reason:** Not executed — see Skipped Tests

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-20

