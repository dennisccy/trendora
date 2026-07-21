# Phase goal-ops-hardening-iter-6 — UI Test Results

**Phase:** goal-ops-hardening-iter-6
**Date:** 2026-07-21
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- All smoke (UT-01, UT-07) and happy-path (UT-02, UT-08) tests pass. All P1 tests
     (UT-01, UT-02, UT-04, UT-05, UT-07, UT-08, UT-10) pass. Required-still-passing
     regression journeys J-04 and J-05 both pass. Two P2 error-state tests (UT-03, UT-09)
     FAIL against their literal expected text, but are a pre-existing, untouched-by-this-
     iteration architectural characteristic (confirmed via git diff: app/page.tsx is not in
     this iteration's diff at all) that does not blank/freeze the page and does not gate the
     verdict per the P1/smoke/happy-path rule. UT-13/UT-14 are P3/informational per the test
     plan's own instruction and do not gate the verdict either way. J-01/J-03 were
     deterministically replay-verified outside this run and are not re-tested here. -->

**Overall:** 12/14 test-plan cases PASS, 2/14 FAIL (both P2, non-gating), 0 SKIPPED. Both
regression journeys (J-04, J-05) PASS. UT-13/UT-14 are informational/P3 (see Notes).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Dashboard loads, cross-view card present | smoke | P1 | No blank/error screen; cross-view heading visible; card settles off the skeleton; no console errors | Page rendered fully, "Regime × phase cross-view" heading + chart visible, "as of 2026-07-17" label populated; no console errors captured | PASS | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-01-result.png` |
| UT-02 | Cross-view chart within budget, 3 reloads | happy-path | P1 | All 3 reloads of `GET /api/indexes?full=true` ≤1500ms; skeleton→chart transition, no blank gap | 3 reloads measured via `performance.getEntriesByType('resource')`: 834ms, 885ms, 871ms — all within budget; chart visible each time | PASS | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-02-result.png` |
| UT-03 | Cross-view honest error state, backend down | error | P2 | Card shows "Cross-view unavailable" amber error state, never blank | Whole page short-circuits to the page-level "Backend unavailable" card (pre-existing, unrelated to this diff); `PhaseCrossViewCard` never mounts so its own "Cross-view unavailable" text never renders. Not blank — honest "Backend unavailable" message shown instead. See Failed Tests / Notes. | FAIL | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-09-fail.png` (same page-level pattern; see Failed section) |
| UT-04 | Cross-view survives rapid as-of toggle | regression | P1 | Never blank/frozen during transition; badge + card settle to the 2-steps-back date | After 2 rapid "◀" clicks, badge read "Viewing as-of 2026-07-15 (historical)" and the card's "as of 2026-07-15" / "Data as-of 2026-07-15" matched; no blank/frozen state observed at any checkpoint | PASS | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-04-during.png` |
| UT-05 | Other Dashboard cards unaffected | regression | P1 | Market Regime / Market Phase & Severity cards render normally, unaffected by cross-view's deferral | Market Regime ("Risk-on 65.98/100") and Market Phase & Severity ("Expansion", P(bear) 0.00, 29.40/100) rendered correctly alongside the cross-view card | PASS | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-04-during.png` |
| UT-06 | Cross-view discoverable, Hide/Show toggle | ux | P2 | Card found ≤1 scroll; Hide collapses to a button; Show re-mounts, re-fetches, re-renders | Card found immediately below Market Phase; "Hide" collapsed to "Show regime × phase cross-view" button (no fetch while hidden); clicking it again re-mounted and re-rendered with "as of 2026-07-17" | PASS | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-06-hidden.png`, `UT-06-reshow.png` |
| UT-07 | Data Manager loads, heatmap present | smoke | P1 | No blank/error screen; heatmap panel shows spinner + "Loading availability…" text, never a blank gap; no console errors | "Data Manager" heading visible; heatmap panel showed the `Loader2` spinner + "Loading availability…" text during the deferral window; no console errors (only the React DevTools info line) | PASS | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-07-loading.png` |
| UT-08 | Heatmap within budget, 3 reloads | happy-path | P1 | All 3 reloads of `GET /api/data/availability` ≤1500ms; spinner visible through the ~2.5s deferral, then the grid renders | 3 reloads measured: 869ms, 985ms, 950ms (each starting ~2.77s after navigation, matching the 2500ms stagger) — all within budget; grid + legend rendered after each | PASS | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-08-result.png` |
| UT-09 | Heatmap honest error state, backend down | error | P2 | Page-level "Dataset coverage could not load..." card AND heatmap's own "Availability could not load from the API..." text, never a blank grid | Page-level "Dataset coverage could not load from the API. No figures are shown rather than fabricated values." card appeared (matches). The heatmap's own independent "Availability could not load..." text never appeared because `AvailabilityHeatmap` is inside the same `state.kind === "ok"` gate as the rest of the page body (pre-existing structure, confirmed unchanged by this iteration's diff — only the `loadAvailability()` timing changed). Not blank — an honest page-level error is shown instead. | FAIL | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-09-fail.png` |
| UT-10 | Weekend backfill → "no new snapshots" history entry | regression | P1 | Job completes with "2 non-trading"; reload shows top Run-history row with range `2026-05-02 → 2026-05-03`, kind backfill, "no new snapshots" badge | Job card showed "2 non-trading"; after reload, top run-history row: Started 2026-07-21 00:13:24, Kind backfill, Range `2026-05-02 → 2026-05-03`, Status "no new snapshots", Summary "0 already snapshotted · 2 non-trading — Refreshed: coverage, membership timeline, forward aggregates, research hot keys" | PASS | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-10-job-complete.png`, `UT-10-run-history.png` |
| UT-11 | Job form blocks invalid/empty dates | validation | P2 | Invalid date → red error text + disabled Start; empty fields → Start stays disabled | `2026-13-40` → field value held the invalid string, page text confirmed "Enter a valid date as yyyy-MM-dd" present, Start button `disabled=true`; both fields cleared → Start button remained `disabled=true` | PASS | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-11-invalid-date2.png`, `UT-11-empty-fields.png` |
| UT-12 | Heatmap legend/tooltip discoverable | ux | P2 | Legend with 6 labeled swatches below grid; hover/click a cell shows exact date/counts/snapshot status | Legend text confirmed: "none / <25% / 25–50% / 50–75% / 75–<100% / full"; cell for 2026-07-17 carries a native `title` attribute "2026-07-17 · 589/591 symbols have price data (Fetch) · scored snapshot exists (Backfill)" (and matching `aria-label`); clicking it worked without error | PASS | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-12-legend-tooltip.png` |
| UT-13 | `/evidence` known pre-existing slow-load issue | regression | P3 | Informational — expected several minutes cold (555.97s per dev handoff), NOT to be filed as caused by this iteration; must still load correctly, not crash/garble | Loaded correctly with real, well-formed data (no crash, no garbled error). Measured: real-browser `GET /api/evidence` via Resource Timing = **73.5s** (well over budget but far less than the dev handoff's own 555.97s figure); an immediately-following standalone direct backend `curl` to the same endpoint returned in **0.02s**. See Notes. | INFORMATIONAL (not scored) | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-13-result.png` |
| UT-14 | `/research/event-study` known pre-existing slow-load issue | regression | P3 | Informational — expected ~92s cold / ~1.46s warm per dev handoff, NOT to be filed as caused by this iteration | Loaded correctly with real, well-formed episode-study data both times. Measured via Resource Timing: cold (fresh backend restart, first visit) = **35ms**; warm reload = **477ms** — both far faster than the dev handoff's own 92s/1.46s figures. See Notes. | INFORMATIONAL (not scored) | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-14-result.png` |
| UT-J-04 | J-04: Non-blocking boot with visible status (Required-still-passing regression) | regression | P1 | First `GET /api/health` 200 ≤5s of restart; pre-ready payload carries boot phase+progress; badge matches in the same window; simulated crash shows a distinct unreachable presentation; persistent logfile shows boot entries + abrupt (no clean-shutdown) ending after a crash; a job mid-flight at kill shows "interrupted", never orphaned "running" | Restart→first-200 measured at **~1.1s** (well under 5s budget). Mid-boot: health payload showed `"readiness":"initializing","warmup":{"done":89,"total":89,"status":"running","message":"history 89/89"}`; in the SAME window the frontend badge read "Initializing… history 89/89" — matching phase detail, never a bare "Backend unavailable". `kill -9` (simulated crash) → UI showed "Backend unavailable / NO-GO — do not rely on today's board / Backend is unavailable — the preflight check could not run", visibly distinct from the initializing badge. `logs/backend.log`: prior graceful `SIGTERM` restarts logged `Shutting down` / `Waiting for application shutdown.` / `Application shutdown complete.` / `Finished server process [PID]`; the `kill -9` crash produced NONE of those lines — the log simply stops after the last served request, confirming the abrupt-ending contract. Interrupted-job recovery: queried `/api/data` run history and found multiple `"interrupted"` rows (ids 82, 79, 73, 72, 66, 65, 41, 38, 37) from this session's earlier backend restarts, and confirmed **zero** rows currently stuck at `"running"` with no live process — the mechanism correctly finalizes mid-flight jobs as "interrupted" rather than leaving them orphaned. | PASS | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-J-04-initializing-badge.png`, `UT-J-04-crashed.png` |
| UT-J-05 | J-05: Aggregates precomputed at ingest, never on the fly (Required-still-passing regression) | regression | P1 | Backfilling one unsnapshotted day serves aggregates from storage immediately; the run record lists which aggregates its finalize hooks refreshed; a cold restart renders `/data` coverage from storage within budget with no full-table prefill; health stays responsive during a heavy ingest | Backfilled `2005-03-30` (confirmed via `/api/data/availability` to have bars but no prior snapshot). Run record `aggregates_refreshed`: `["latest_snapshot","coverage","membership_timeline","market_phase","forward_aggregates","research_hot_keys"]` — matches the acceptance list. `/scanner-runs` immediately listed `2005-03-30` and its leaderboard rendered ("Defensive" regime, matching the stored run via `/api/runs`); `/api/market-phase?as_of=2005-03-30` answered in 10ms (storage-speed, not a live compute). While the job ran, `GET /api/health` was polled every ~0.3s and stayed 200 throughout (20/20 polls). After a fresh backend restart, `/data` cold-load's `GET /api/data` resolved in 244ms (Resource Timing) — consistent with a stored-payload read, not a 3.3M-row prefill. | PASS | `reports/qa/goal-ops-hardening-iter-6-evidence/UT-J-05-scanner-run.png` |

---

## Passed Tests

### UT-01 — Dashboard loads, cross-view card present
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-6-evidence/UT-01-result.png`
- Navigated to `/`, page rendered fully (regime, phase, and cross-view cards all populated); no console errors captured after `enable_console_logging`.

### UT-02 — Cross-view chart within budget, 3 reloads
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-6-evidence/UT-02-result.png`
- 3 consecutive full-page reloads of `/`, each measured via `performance.getEntriesByType('resource')` for `indexes?full=true`: 834ms, 885ms, 871ms. All ≤1500ms, matching the dev handoff's own 821–872ms range.

### UT-04 — Cross-view survives rapid as-of toggle
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-6-evidence/UT-04-during.png`
- Clicked "◀" (Previous available date) twice in immediate succession right after navigation. By the time state was checked, the page had already settled cleanly to 2026-07-15 (2 trading days back from 2026-07-17) with the "Viewing as-of 2026-07-15 (historical)" badge and matching card content — no blank or stale-data frame observed at any inspected point. Note: due to automation round-trip speed, the very-mid-transition frame itself was not independently captured, but no blank/frozen state was seen at any checkpoint, and the abort/cleanup contract (timer + AbortController) is exactly what this iteration's diff added for this component.

### UT-05 — Other Dashboard cards unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-6-evidence/UT-04-during.png`
- Market Regime and Market Phase & Severity cards rendered live values (not stuck loading, no error) both at the current date and after the as-of toggle in UT-04.

### UT-06 — Cross-view discoverable, Hide/Show toggle
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-6-evidence/UT-06-hidden.png`, `reports/qa/goal-ops-hardening-iter-6-evidence/UT-06-reshow.png`
- "Hide" collapsed the card to a "Show regime × phase cross-view" dashed button; clicking it again re-mounted the card, which re-fetched and settled back to "as of 2026-07-17" — confirms the deferred-fetch effect re-arms cleanly on re-enable.

### UT-07 — Data Manager loads, heatmap present
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-6-evidence/UT-07-loading.png`
- "Loading availability…" + spinner visible during the deferral window; no console errors (only the informational React DevTools line).

### UT-08 — Heatmap within budget, 3 reloads
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-6-evidence/UT-08-result.png`
- 3 reloads of `/data`, each measured for `data/availability`: 869ms, 985ms, 950ms (request start ~2.77s after navigation in all 3, matching the 2500ms stagger). All within the ≤1500ms budget.

### UT-10 — Weekend backfill → "no new snapshots" history entry
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-6-evidence/UT-10-job-complete.png`, `reports/qa/goal-ops-hardening-iter-6-evidence/UT-10-run-history.png`
- Submitted backfill `2026-05-02 → 2026-05-03`; live card reported "2 non-trading"; after reload, the top run-history row showed exactly this range, kind `backfill`, and status **"no new snapshots"** — the same data the rewritten `J-01.json` step 6 now asserts against.

### UT-11 — Job form blocks invalid/empty dates
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-6-evidence/UT-11-invalid-date2.png`, `reports/qa/goal-ops-hardening-iter-6-evidence/UT-11-empty-fields.png`
- `2026-13-40` produced the exact error text "Enter a valid date as yyyy-MM-dd" and a disabled Start button; clearing both fields kept Start disabled.

### UT-12 — Heatmap legend/tooltip discoverable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-6-evidence/UT-12-legend-tooltip.png`
- Legend present with all 6 labels; day cells carry a native `title` tooltip with the exact date, symbol count, and snapshot-existence text.

### UT-J-04 — J-04: Non-blocking boot with visible status
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-6-evidence/UT-J-04-initializing-badge.png`, `reports/qa/goal-ops-hardening-iter-6-evidence/UT-J-04-crashed.png`
- Full detail in the Results Table row above. Boot budget (~1.1s to first 200), badge/health phase-detail parity, crash-vs-initializing visual distinction, persistent-logfile abrupt-ending evidence, and interrupted-job recovery were all independently confirmed this run.

### UT-J-05 — J-05: Aggregates precomputed at ingest, never on the fly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-6-evidence/UT-J-05-scanner-run.png`
- Full detail in the Results Table row above. Single-day backfill of a previously-unsnapshotted date (2005-03-30) correctly refreshed all 6 named aggregates, served `/scanner-runs` and `/api/market-phase` from storage, kept `/api/health` responsive throughout, and a cold-restarted `/data` visit read coverage in 244ms with no evidence of a full-table prefill.

---

## Failed Tests

### UT-03 — Cross-view honest error state, backend down
**Verdict:** FAIL
**Failure:** With the backend stopped, `PhaseCrossViewCard`'s own "Cross-view unavailable" error card/text never appears at all. The Dashboard page (`apps/frontend/app/page.tsx`) gates its ENTIRE below-the-fold body — including `PhaseCrossViewCard` — behind the top-level `/api/dashboard` fetch's own `state.kind === "ok"` check; when that top-level fetch fails, the page renders only the page-level "Backend unavailable" card and `PhaseCrossViewCard` is never mounted, so its independent error branch can never fire under a full-backend-outage precondition.
**Evidence:** `reports/qa/goal-ops-hardening-iter-6-evidence/UT-09-fail.png` (Dashboard's own screenshot was not separately saved under a UT-03 filename; the extracted page text for `/` at this point read: "Backend unavailable / NO-GO — do not rely on today's board. / Backend is unavailable — the preflight check could not run. / Dashboard / The daily snapshot at a glance / Backend unavailable / The dashboard could not load the market regime from the API. Nothing is fabricated — confirm the backend is running and reload.")

**Steps taken:**
1. Stopped the backend process (`kill -TERM`), confirmed `curl` to `/api/health` failed.
2. Navigated to `http://localhost:3255/`, scrolled down, waited 5+ seconds.
3. Extracted page text — no "Cross-view unavailable" text present anywhere on the page.

**Expected:** The "Regime × phase cross-view" card itself shows an amber-bordered "Cross-view unavailable" error state.
**Actual:** The whole page shows only the page-level "Backend unavailable" card (from the top-level `/api/dashboard` fetch); `PhaseCrossViewCard` is never rendered, so its own error text is never visible.
**Root-cause note (not speculation — confirmed by direct diff inspection):** `git diff HEAD -- apps/frontend/app/page.tsx` shows **zero changes** — this file is not touched by this iteration's diff at all. The page-level gating architecture is pre-existing and unrelated to this iteration's fetch-timing fix. Functionally, the page is never blank and never fabricates data (satisfies AG-8's higher-level intent), it just doesn't match this specific test case's literal expected text under a full-outage precondition. P2, does not gate the verdict.

---

### UT-09 — Heatmap honest error state, backend down
**Verdict:** FAIL
**Failure:** Same architectural pattern as UT-03. With the backend stopped, the page-level "Dataset coverage could not load from the API..." card DOES appear (matches expectation), but the heatmap's own independent "Availability could not load from the API. No cells are shown rather than fabricated values." text never appears, because `AvailabilityHeatmap` (in `apps/frontend/app/data/page.tsx`) is rendered only inside the same `state.kind === "ok"` branch as the rest of the page body — when the top-level overview fetch fails, that whole branch (including the heatmap) never mounts.
**Evidence:** `reports/qa/goal-ops-hardening-iter-6-evidence/UT-09-fail.png`

**Steps taken:**
1. With backend still stopped from UT-03, navigated to `http://localhost:3255/data`.
2. Waited past the 2.5s deferral window (3+ seconds total).
3. Extracted page text.

**Expected:** Both the page-level error AND the heatmap's own "Availability could not load..." text appear.
**Actual:** Only the page-level "Dataset coverage could not load from the API. No figures are shown rather than fabricated values." card appeared; the heatmap-specific text never rendered because the heatmap itself never mounted.
**Root-cause note:** `git diff HEAD -- apps/frontend/app/data/page.tsx` confirms the ONLY change in this file is the `AVAILABILITY_FETCH_STAGGER_MS` timer addition around the existing `loadAvailability()` call — the `state.kind === "ok"` gating structure and the heatmap's own error-text branch are byte-unchanged. Pre-existing, not caused by this iteration. Not blank, not fabricated — an honest page-level error is shown instead. P2, does not gate the verdict.

---

## Skipped Tests

None. Frontend and Chrome MCP were both available throughout.

---

## Notes

- **UT-13/UT-14 timing discrepancy (worth flagging, not scored):** the test plan's own numbers, taken from the dev handoff, are `/evidence` ≈555.97s cold and `/research/event-study` ≈92s cold / ≈1.46s warm. My independent measurements this run were substantially different in BOTH directions and are reported exactly as measured, without speculation on cause:
  - `/research/event-study`: cold (fresh backend restart, first visit) = **35ms**; warm reload = **477ms**. Neither reproduces the dev handoff's slow numbers at all — both are comfortably fast.
  - `/evidence`: real-browser Resource-Timing measurement of `GET /api/evidence` = **73.5s** (still far over the generic ≤1.5s budget, and still a real, pre-existing, not-this-iteration's-diff problem worth someone's attention) — but nowhere near the dev handoff's own 555.97s figure. An immediately-following standalone direct-`curl` to the same endpoint (no concurrent browser load) returned in **0.02s**.
  - Both pages loaded correctly (real, well-formed data, no crash, no garbled error) in every measurement — the "must still eventually load correctly" part of both test cases' expected results holds.
  - Per the test plan's own explicit instruction, these are **not filed as new bugs caused by this iteration** — confirmed via `git diff` that neither `/evidence` nor `/research/event-study`'s directories nor any backend module appear in this iteration's diff. The magnitude mismatch against the dev handoff's own numbers (both this run's measurements were far better than what the handoff recorded) is reported here as a data point for whoever owns the follow-up on this known issue, not as a claim that the issue is resolved — a single re-measurement under different load/cache conditions is not conclusive either way.
- **UT-03/UT-09 (P2 FAILs):** both are the SAME pre-existing, pre-this-iteration page-level error-gating architecture (confirmed via `git diff` — `app/page.tsx` untouched, `app/data/page.tsx`'s gating structure untouched) applied to two different pages. Recorded honestly against the test plan's literal expected text (which assumed each below-the-fold card would show its own independent error state even under a full-backend-outage precondition), but functionally the product never goes blank and never fabricates data under backend-down conditions on either page — it shows one unified, honest page-level error instead of two nested ones. Neither is a P1/smoke/happy-path test, so neither gates the overall verdict per the stated PASS/FAIL rule.
- **J-01/J-03:** not re-tested this run — already deterministically re-verified from stored golden scripts per the dispatch instructions. Their rows are expected to be merged in automatically.
- **Golden replay scripts:** wrote none for J-04 or J-05 this run. Both journeys' core acceptance criteria (backend process restart/crash, persistent-logfile inspection, direct `/api/health` polling during process lifecycle events) are not expressible in the `goto`/`click`/`fill` browser-only replay format the deterministic runner supports — a script limited to those three action types cannot restart or kill the backend process or read `logs/backend.log`. Per the "best-effort, skip if you cannot produce a clean script" policy, both are left to the LLM fallback lane next time. `J-01.json` and `J-03.json` were left untouched (not journeys I verified this run).
- All backend restarts performed during this QA run (for UT-03/UT-09's backend-down tests and J-04/J-05's process-lifecycle tests) were restored to a clean, warm, `ready` state before finishing — confirmed via a final `GET /api/health` → `{"status":"ok","readiness":"ready"}` and `GET /` → `200` check.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (health at `/api/health`)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` MCP
- **Test Date:** 2026-07-21
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-6-evidence/`
