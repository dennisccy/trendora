# UI Test Results (merged)

**Date:** 2026-08-11
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** BLOCKED

**Overall:** 13/14 journeys passed (1 skipped, 2 target-missing)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work (live job card, not persisted history) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-61-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-61-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status — regression-hardening golden (J-04's product behavior is already proven/evidenced; this asserts the readiness badge's REAL data-state attribute and a persisted data_provider_runs-backed field, never a bare page-title/heading match) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-61-evidence/J-04-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-61-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request (payload-gated) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-61-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-61-evidence/J-09-verify.png |
| UT-01 | `/data` loads without errors | smoke | P1 | Page renders, no "Backend unavailable" card, Dataset coverage panel visible with numeric Snapshot dates/Backfill gaps, Start panel visible, no console errors | Rendered cleanly; "GO — today's board is current."; Snapshot dates=2955, Backfill gaps=2441 (both numeric); "Start a fetch / backfill job" panel present; no error text; no console errors observed | PASS | `reports/qa/goal-ops-hardening-iter-61-evidence/UT-01-result.png` |
| UT-02 | Ambient refresh picks up an externally-triggered change | happy-path | P1 | Within 35s, Tab A auto-fires a new `GET /api/data` + `GET /api/data/availability` with no user action, panel updates in place | A script (`curl`, an unrelated request-path event: `GET /api/backtest?as_of=2019-01-24`, a not-yet-scanned historical date) created a new `ScannerRun` and bumped `_membership_dataset_version` mid-session, entirely independent of this tab's own job state (no job was ever started in this tab this session). The open tab, untouched, continued firing automatic `GET /api/data` + `GET /api/data/availability` pairs on schedule (`performance` resource-timing entries at t=0/2592ms [mount], 30192ms, 60192ms, 90192ms — every ~30.0s, `performance.getEntriesByType('navigation').length` stayed at 1 throughout, i.e. no full-page reload). This proves the refresh fires regardless of any externally-triggered event and is not gated on "this tab's own job" — the exact defect this iteration fixes. (Note: this specific external event did not itself change the coverage_snapshot payload — `coverage_snapshot` is precomputed only by a real ingest job's finalize hook, by design [J-05] — so the displayed Snapshot Dates/Backfill Gaps numbers did not move from this particular trigger; UT-04 below separately confirms the panel picks up a real value change immediately.) | PASS | `reports/qa/goal-ops-hardening-iter-61-evidence/UT-02-result.png` |
| UT-03 | Refresh cadence matches the configured 30s interval | validation | P2 | No new `GET /api/data` in first ~25s; exactly one new fetch between 25-35s | `GET /api/health` confirmed `poll_idle_interval_seconds: 30.0`. Resource-timing entries showed zero new `/api/data` calls through t=27755ms, then exactly one new `GET /api/data` + one new `GET /api/data/availability` pair at t=30192ms — on the money, no early fire, no double fire. Two further cycles (60192ms, 90192ms) confirmed the steady 30.0s cadence continuing with no drift. | PASS | `reports/qa/goal-ops-hardening-iter-61-evidence/UT-03-result.png` |
| UT-04 | Same-tab job completion still refreshes immediately | regression | P1 | Immediately after the button reverts to "Start", the coverage panel reflects the just-completed job | Started a backfill job (kind=backfill, 2026-08-03→2026-08-03) from this tab. The job resolved to a zero-new-snapshot run ("1 calendar day · 1 already snapshotted · 0 non-trading") but — because an earlier unrelated event in this same session had already bumped `_membership_dataset_version` — its finalize hook still re-ran the full aggregate refresh (`aggregates_refreshed`: coverage, membership_timeline, forward_aggregates, research_hot_keys, availability_heatmap, factor_lab_all, drawdown_expectations). Button reverted "Job running…" → "Start"; a fresh mount of `/data` immediately after showed Snapshot dates=2956, Backfill gaps=2440. Verified byte-exact against sqlite in the same evidence pass: `coverage_snapshot` row id=1 (asof_key=2026-08-03, dataset_version=r2956-…) payload `snapshot_count=2956`, `gap_count=2440`, and `GET /api/data` served the identical 2956/2440 — rendered value = persisted value = served value, no staleness. | PASS | `reports/qa/goal-ops-hardening-iter-61-evidence/UT-04-result.png` |
| UT-05 | Readiness badge unaffected by new context field | regression | P2 | Badge still shows "Ready" exactly as before; no console error referencing the new field/provider | `[data-testid="readiness-badge"]` read `{text: "Ready", state: "ready"}` on `/`; no error-boundary text; `document.body.innerText` did not contain "pollIdleIntervalSeconds"; no console errors observed | PASS | `reports/qa/goal-ops-hardening-iter-61-evidence/UT-05-result.png` |
| UT-06 | "Unavailable" indicator renders under armed fault | error | P2 | Cell shows grey triangle + "Unavailable" (`data-testid="sample-link-unavailable"`), tooltip text, non-clickable | SKIPPED — see Skipped Tests section | SKIP | none (dev-captured evidence referenced below) |
| UT-07 | Normal sample-link chips render without fault injection | regression | P1 | Cell shows a normal clickable `n=...` chip (`data-testid="sample-link"`), no "Unavailable" text; click opens `/research/samples` in a new tab | On `/research/regime-lab?asof=2010-11-05` (As-of-date mode, selected via the toggle), after the pooled evidence finished computing: 80 `[data-testid="sample-link"]` chips, 0 `[data-testid="sample-link-unavailable"]`. First chip text `"n=16452"`, href `/research/samples?kind=regime-lab&horizon=1&slice=label&view=pooled&regime=Strong+risk-on&scope=asof&asof=2010-11-05`. Clicking it opened a second tab whose `window.location.href` resolved to exactly that URL. | PASS | `reports/qa/goal-ops-hardening-iter-61-evidence/UT-07-result.png` |
| UT-08 | Ambient refresh causes no visible flicker/error flash | ux | P3 | Panel numbers update in place, no full-panel spinner, no "Backend unavailable" flash, no new toast/banner/modal | Across the same ~93s, 3-cycle observation window used for UT-02/UT-03: no `[data-testid="coverage-panel-loading"]` element ever appeared, `document.body.innerText` never contained "Backend unavailable", `performance.getEntriesByType('navigation').length` stayed at 1 (no reload/flash), and the visible screenshot mid-session shows the panel rendered normally (with an honest "background compute running (1)" badge reflecting real in-flight work, not a fabricated state) | PASS | `reports/qa/goal-ops-hardening-iter-61-evidence/UT-08-result.png` |

## Missing Target Journeys

_Target journeys named in the iteration spec's `Target journeys:` line — the journeys THIS iteration exists to verify — that were NOT verified this iteration, either no lane produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-41 audit finding B2 / iter-42 fix: promoting a journey to an iteration's own target silently removed its verification — iter-41 itself shipped a clean PASS 6/6 headline while its two target journeys had zero rows anywhere)._

- `UT-J-05` — no test case executed for J-05 by any lane
- `UT-J-07` — no test case executed for J-07 by any lane

## Skipped Tests

### UT-06 — "Unavailable" indicator renders under armed fault

**Verdict:** SKIPPED
**Reason:** SKIPPED — see Skipped Tests section

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-11

