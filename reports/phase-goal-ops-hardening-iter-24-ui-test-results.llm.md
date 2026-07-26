# Phase goal-ops-hardening-iter-24 — UI Test Results

**Phase:** goal-ops-hardening-iter-24
**Date:** 2026-07-26
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 12/12 tests passed (0 skipped)

---

## IMPORTANT — Chrome MCP screenshot-capture limitation discovered this run

Independent of the coordinator's known "below-the-fold" screenshot-blindness lesson, this run
uncovered a **more severe, deterministic Chrome MCP tool limitation**: on this host, **any
non-zero scroll position (even 500-800px on a short page) causes the `screenshot` action to
return a solid single-color image** (verified by pixel-color-count analysis with PIL — every
scrolled capture came back as exactly 1 distinct color across the whole frame). This reproduced
on multiple pages (`/data`, `/backtest`), with the native `scroll` action, `eval`-based
`scrollTo`/`scrollIntoView`, with and without a `requestAnimationFrame`+500ms settle delay,
with `fullpage:true`, with an element-scoped `selector`, and even after artificially shrinking
the page via CSS `zoom` to bring `scrollY` under 6000px. Screenshots at `scrollY: 0` were
reliably real (thousands of distinct colors) on the very same pages, both before and after each
failed scrolled attempt — ruling out a crashed tab or dead renderer. This is a tool/environment
issue, not a product defect.

**Mitigation used:** every below-the-fold assertion in this report (the `BackgroundComputePanel`
on `/data`, which is the last panel on a ~24,800px-tall page) was verified instead via direct DOM
extraction (`eval`/auto-captured `.html` snapshots reading `outerHTML` of the exact
`data-testid` elements) cross-checked against direct `GET /api/health` / sqlite reads of
`forward_aggregate_cache` against the SAME backend process the browser was pointed at. Verbatim
DOM text is quoted below for every below-the-fold claim so this is falsifiable, not just
asserted. Two of the blank captures are kept as evidence of the limitation itself (renamed
`*-blank-scrollY-tool-limitation.png`) rather than discarded.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Header/readiness pill loads cleanly | smoke | P1 | `readiness-badge` visible, no `background-compute-indicator`, no console errors | `data-testid="readiness-badge" data-state="ready"` present; no `background-compute-indicator` in DOM; console showed only the React DevTools info line | PASS | `reports/qa/goal-ops-hardening-iter-24-evidence/UT-01-initial.png` |
| UT-02 | Historical backtest triggers a real background-compute window, badge appears | happy-path | P1 | Badge "background compute running (N)" appears next to readiness pill within a few attempts across historical dates | Found uncached date 2026-07-17 (checked `forward_aggregate_cache` for current `dataset_version` first to pick efficiently); after loading `/backtest?asof=2026-07-17`, DOM showed `data-testid="background-compute-indicator"` text "background compute running (1)" next to `data-testid="readiness-badge" data-state="ready"` "Ready" — both siblings, neither hidden | PASS | `reports/qa/goal-ops-hardening-iter-24-evidence/UT-02-badge-active.png` |
| UT-03 | `/data` panel shows live active-window detail | happy-path | P1 | Active row shows as-of/elapsed>0/horizons X<Y; on re-poll elapsed increases, horizons never decreases/exceeds total | DOM (`013-eval.html`) showed `background-compute-active-row` with `background-compute-asof`="as-of 2026-07-17", `background-compute-elapsed`="elapsed 41.8s", `background-compute-horizons`="horizons 2/5". Direct `/api/health` reads bracketing this window showed monotonic progress: `elapsed_ms=5643,horizons_done=0` → `elapsed_ms=47126,horizons_done=3` (both < `horizons_total=5`). By the 5s-later reload the window had already completed (see UT-05) — a clean active→completed transition, not a hang. See note below. | PASS | DOM-verified (see note); screenshot attempt blank per tool-limitation above (`UT-03-blank-scrollY-tool-limitation.png`) |
| UT-04 | `/data` panel shows honest idle message when nothing has ever run | smoke | P1 | Exact text "No background compute running. Last outcome: none yet." (`background-compute-idle`), no active-row/last-outcome section | After a clean backend restart (fresh process, confirmed `background_compute:{active:[],recent_outcomes:[]}` via `/api/health`), DOM (`040-navigate.html`) showed exactly `<p ... data-testid="background-compute-idle">No background compute running. Last outcome: none yet.</p>` with no active-row and no Last-outcome block | PASS | DOM-verified; panel below the fold, no reliable screenshot (see limitation note) |
| UT-05 | Last-outcome summary appears once the triggered window finishes | happy-path | P1 | "Completed" badge (ok/green), as-of date, non-zero duration, no failure reason | DOM (`015-eval.html`) showed `data-testid="background-compute-last-outcome"` with a `capitalize` green/`border-pos` badge reading "completed", "as-of 2026-07-17", duration "1m 15s". Cross-checked `GET /api/health`: `recent_outcomes[0] = {asof_key:"2026-07-17", outcome:"completed", duration_ms:75108, reason:null}` — 75108ms = 1m15.1s, matching the UI to the millisecond (AG-3 correctness) | PASS | DOM+API verified (`UT-05-blank-scrollY-tool-limitation.png` — capture attempt blank per limitation) |
| UT-06 | Numeric fields never fabricated/malformed | validation | P2 | No NaN/undefined/Infinity/null/negative; unit-suffixed; done ≤ total | All observed values ("41.8s", "elapsed 47.1s"-equivalent from API ms, "1m 15s", "horizons 2/5"/"3/5") are real, unit-suffixed, non-negative; horizons done never exceeded total in any reading (0→2→3, total fixed at 5) | PASS | Same DOM/API captures as UT-03/UT-05 |
| UT-07 | Backend-unavailable degrades badge/panel honestly, no crash | error | P2 | Readiness pill → "Backend unavailable" (danger); no bg-compute badge; `/data` doesn't crash; after restart readiness recovers and panel shows fresh idle state | Stopped the actual backend process (`kill -TERM`); `/` showed `data-testid="readiness-badge" data-state="unavailable"` text "Backend unavailable", `background-compute-indicator` absent. `/data` did not blank/crash — it rendered the header plus an honest "Dataset coverage could not load from the API. No figures are shown rather than fabricated values." message (see note — this iteration's `BackgroundComputePanel` doesn't render independently in this state; the whole `/data` page uses one shared all-or-nothing loading gate, which is **pre-existing page architecture, not a regression introduced by this iteration** — every panel, not just the new one, is equally absent). Restarted backend: readiness returned to `data-state="initializing"` "Initializing… history 89/89", then "ready"; `background_compute` reset to empty; `/data` correctly showed the fresh UT-04 idle text, confirming non-persistence | PASS | `reports/qa/goal-ops-hardening-iter-24-evidence/UT-07-backend-unavailable.png` |
| UT-08 | Process-lifetime disclosure sentence always visible | ux | P3 | Exact sentence visible in idle, active, and completed states | Verbatim text `"Since the last backend restart — this history is process-lifetime only, never persisted."` confirmed present in all three captured DOM states: idle-after-restart (`040-navigate.html`), active window (`013-eval.html`), and last-outcome/idle-with-history (`015-eval.html`) | PASS | DOM-verified across 3 states |
| UT-09 | Pre-existing `/data` panels unchanged and unremoved | regression | P3 | All prior panels present, in order; "Background compute" new and last | Extracted every `<h1-h4>` on `/data` in document order: Data Manager → Dataset coverage → Per-symbol coverage → Storage footprint → Live-vs-seed drift → Rebuild snapshots... → Universe resolution... → Dynamic-universe membership timeline → Extend history backward → Per-date availability → Missing-data diagnostic → FRED (macro feed) → Index & benchmark data provenance → Start a fetch/backfill job → Job progress → Unfinished imports → Remove imported data → Run history → **Background compute** (last). Matches the surface map's expected order exactly; no field removed | PASS | Full heading list extracted from `015-eval.html` |
| UT-10 | Readiness pill states unaffected by new badge | regression | P3 | Pill wording/color unchanged in Ready/Initializing/Unavailable; badge always a separate sibling | Confirmed "Ready" (pos/green) + badge sibling together (UT-02); confirmed "Initializing… history 89/89" (warn/amber) post-restart with badge correctly absent (no compute active); confirmed "Backend unavailable" (danger) with badge correctly absent (UT-07). In every state the badge element is a sibling `<div>`, never nested inside or overlapping the pill's markup | PASS | `reports/qa/goal-ops-hardening-iter-24-evidence/UT-10-initializing-state.png`, `UT-02-badge-active.png`, `UT-07-backend-unavailable.png` |
| UT-11 | Panel discoverable within 2 clicks, hint text plain-language | ux | P3 | 1-click reachability from Dashboard; heading exactly "Background compute"; jargon-free hint | From `/`, clicked the "Data Manager" sidebar link once; confirmed via `window.location.pathname === "/data"` and `document.querySelector('h1').textContent === "Data Manager"` — 1 click. Panel `<h2>` reads exactly "Background compute". Hint text: "The in-process historical forward-aggregate compute a /backtest (or MCP query_backtest) request starts in the background when a historical as-of's evidence is not yet ready. Read-only disclosure — no fabricated finish-time estimate or completion percentage, only real observed horizon counts and elapsed time." — explains the trigger (a Backtest request for a not-yet-ready historical date) in plain terms; "MCP query_backtest" is a minor technical aside but the primary trigger ("a /backtest request... when a historical as-of's evidence is not yet ready") is understandable without backend jargon | PASS | `reports/qa/goal-ops-hardening-iter-24-evidence/UT-11-top-check.png` (top-of-page proof of the 1-click path; panel text itself DOM-verified per limitation note) |
| UT-J-07 | Heavy aggregates never take the service down (regression journey, goal.md) | regression | — | `GET /api/health` answers 200 throughout a real forward-aggregate background-compute window; no frozen/unresponsive window; service recovers cleanly | Triggered a second real background-compute window (`/backtest?asof=2026-07-16`, confirmed via `/api/health` as a fresh dispatch: `horizons_total=5`). Polled `GET /api/health` once per second for 20 consecutive seconds *during* the active window: **20/20 polls returned HTTP 200** (latencies 0.10s–1.22s — elevated vs. the settled ≤0.1s steady-state budget, but that BCW-window elevation is pre-existing, owner-accepted behavior per `reports/perf-budgets.md`, not a new regression — zero timeouts, zero non-200s, zero frozen windows). Window completed cleanly ~66s later (`outcome:"completed"`, `duration_ms:66297`); backend `readiness` returned to `"ready"` immediately after. Full step-4 memory-pressure fault-injection and peak-VmPeak measurement are backend-internal test-hook scenarios outside browser-QA's reach and were already covered by TC-13/TC-14, which are binding "do not redo" this iteration per the phase spec | PASS | Poll log in this report; `/api/health` JSON captured directly (see conversation transcript) |

---

## Passed Tests

### UT-01 — Header/readiness pill loads cleanly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-24-evidence/UT-01-initial.png`
- `data-testid="readiness-badge" data-state="ready"` present; no `background-compute-indicator` in DOM (correct — nothing had been triggered yet); console log showed only the benign React DevTools info line, no errors.

### UT-02 — Historical backtest triggers a real background-compute window, badge appears
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-24-evidence/UT-02-badge-active.png`
- Read `apps/backend/data/trendora.db`'s `forward_aggregate_cache` table directly (read-only) to find, for the *current* `dataset_version` (`r1865-f3954530`), which historical `asof_key`s were already cached (`2005-03-01/02, 2026-04-15, 2026-05-15, 2026-06-15, 2026-07-08/09, 2026-07-20/21/22`) — this made picking an uncached date deterministic instead of trial-and-error clicking through up to 5 dates.
- Confirmed via UI first that `asof-indicator` correctly reads "Latest", then correctly flips to "Viewing as-of 2026-07-21 (historical)" (amber/warn, `History` icon) after one click of `asof-step-prev` — this date turned out already-cached (no dispatch), consistent with "some dates will already be cached" in the test-plan guidance.
- Loaded `/backtest?asof=2026-07-17` (uncached) — `GET /api/health` immediately showed `background_compute.active=[{asof_key:"2026-07-17", horizons_total:5, horizons_done:0, elapsed_ms:5643,...}]`. On reload, DOM showed `data-testid="background-compute-indicator"` = "background compute running (1)" directly beside `data-testid="readiness-badge" data-state="ready"` = "Ready" — both visible together, badge never hides/replaces the pill.

### UT-03 — `/data` panel shows live active-window detail
**Verdict:** PASS
**Note on timing:** The active window (`horizons_total=5`) completed in ~75s total, faster than the test-plan's illustrative 5s-then-reload gap allowed for observing two *still-active* reads of the same row. This is not a defect — it is direct proof the panel updates promptly and transitions correctly. Evidence of real progression, not a static/fabricated display:
  - Direct `/api/health` reads bracketing the window: `{elapsed_ms:5643, horizons_done:0}` (t≈6s after dispatch) → `{elapsed_ms:47126, horizons_done:3}` (t≈47s after dispatch) — strictly increasing elapsed, non-decreasing (in this case increasing) horizons_done, both `< horizons_total=5`.
  - The DOM's own render at ~mount time (`013-eval.html`) independently showed `background-compute-elapsed`="elapsed 41.8s", `background-compute-horizons`="horizons 2/5" — consistent with (slightly behind) the API reads above, confirming the panel is reading the SAME live registry, not a separate/stale source.
  - By the reload 5s later, the window had moved to the completed state (see UT-05) — a clean state-machine transition, not a hang or wedge.

### UT-04 — `/data` panel shows the honest idle message when nothing has ever run
**Verdict:** PASS
- Restarted the actual backend process (`kill -TERM` + `scripts/start-backend.sh`), confirmed via `GET /api/health` that `background_compute` reset to `{"active": [], "recent_outcomes": []}` (in-memory state genuinely cleared).
- Loaded `/data` fresh; DOM (`040-navigate.html`) contained exactly: `<p class="text-sm text-text-muted" data-testid="background-compute-idle">No background compute running. Last outcome: none yet.</p>` — no active-row list, no Last-outcome section rendered alongside it.

### UT-05 — Last-outcome summary appears once the triggered window finishes
**Verdict:** PASS
- DOM (`015-eval.html`): `data-testid="background-compute-last-outcome"` block containing a `capitalize` badge with `border-pos`/`text-pos` (green/"ok") styling and raw text `completed`, plus `as-of 2026-07-17` and duration `1m 15s`. No active-row present anymore, no failure-reason text.
- Cross-checked directly against `GET /api/health`: `recent_outcomes[0] = {asof_key:"2026-07-17", dataset_version:"r1865-f3954530", outcome:"completed", started_at:"2026-07-26T12:55:48.777096+00:00", finished_at:"2026-07-26T12:57:03.885921+00:00", duration_ms:75108, reason:null}`. `75108ms = 1m 15.108s`, matching the UI's "1m 15s" exactly (AG-3: displayed number matches the engine's own record, not merely rendered).

### UT-06 — Numeric fields never render fabricated or malformed values
**Verdict:** PASS
- All observed elapsed/duration values carried explicit unit suffixes ("41.8s", "1m 15s") and all horizon pairs satisfied `0 ≤ done ≤ total` (`0/5`, `2/5`, `3/5`, final total `5/5` via 5 completed horizons). No `NaN`/`undefined`/`Infinity`/`null`/negative value observed anywhere in the panel or the raw `/api/health` payload backing it.

### UT-07 — Backend-unavailable state degrades the badge and panel honestly, no crash
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-24-evidence/UT-07-backend-unavailable.png`
- With the backend process killed, `/` showed `data-testid="readiness-badge" data-state="unavailable"` = "Backend unavailable" and no `background-compute-indicator` (correctly never claims an active window while unreachable).
- `/data` did not blank or show an unhandled-exception screen: header + description rendered, plus an honest message ("Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry."). **Observation (not a new regression):** in this fully-unreachable state, `/data`'s panels — including the pre-existing Coverage/Storage/Drift/etc. panels *and* the new `BackgroundComputePanel` — are ALL absent behind one shared page-level loading gate, rather than each degrading independently; this is a pre-existing characteristic of the page's data-loading architecture that predates this iteration (every panel is affected equally, not something specific to the new panel), so it is reported as an observation for the record rather than a defect attributable to J-09.
- After restarting the backend: readiness returned to `data-state="initializing"` = "Initializing… history 89/89", then settled to "ready"; `background_compute` was confirmed reset to empty via `/api/health`; `/data` then correctly showed the fresh UT-04 idle text — confirming in-memory history does not survive a restart, as documented.

### UT-08 — Process-lifetime disclosure sentence is always visible
**Verdict:** PASS
- Verbatim sentence `"Since the last backend restart — this history is process-lifetime only, never persisted."` confirmed present, byte-for-byte, in all three reachable panel states: idle-after-restart, active-window, and completed/last-outcome.

### UT-09 — Pre-existing `/data` panels are unchanged and unremoved
**Verdict:** PASS
- Full ordered heading extraction (`h1`-`h4`) from a rendered `/data` DOM snapshot: Data Manager (h1) → Dataset coverage → Per-symbol coverage → Storage footprint → Live-vs-seed drift → Rebuild snapshots for current universe → Universe resolution as of ... → Dynamic-universe membership timeline → Extend history backward → Per-date availability → Missing-data diagnostic → FRED (macro feed) → Index & benchmark data provenance → Start a fetch / backfill job → Job progress → Unfinished imports → Remove imported data → Run history → **Background compute**. Order matches the surface map's expected sequence exactly; "Background compute" is the only new, and last, panel.

### UT-10 — Readiness pill states are unaffected by the new badge, in every state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-24-evidence/UT-10-initializing-state.png`, `UT-02-badge-active.png`, `UT-07-backend-unavailable.png`
- "Ready" (pos/green) confirmed with badge present as a sibling during an active window (UT-02).
- "Initializing… history 89/89" (warn/amber) confirmed post-restart, wording/styling unchanged from prior iterations, badge correctly absent (no compute active at that moment).
- "Backend unavailable" (danger/red) confirmed with badge correctly absent (UT-07).
- In all captured DOM snapshots the badge is a separate sibling `<div>` adjacent to, never nested in or overlapping, the pill's own markup.

### UT-11 — "Background compute" panel is discoverable within 2 clicks and its hint text is plain-language
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-24-evidence/UT-11-top-check.png`
- From `/` (Dashboard), clicked the "Data Manager" sidebar link once (`a[href="/data"]`); confirmed via `window.location.pathname` = `/data` and `h1.textContent` = "Data Manager" — exactly 1 click, well within the 2-click bar.
- Panel heading is exactly `<h2>Background compute</h2>`. Hint paragraph beneath it (verbatim): "The in-process historical forward-aggregate compute a /backtest (or MCP query_backtest) request starts in the background when a historical as-of's evidence is not yet ready. Read-only disclosure — no fabricated finish-time estimate or completion percentage, only real observed horizon counts and elapsed time." — a non-technical operator can read the trigger condition ("a /backtest request... when a historical as-of's evidence is not yet ready") without needing to know backend internals.

### UT-J-07 — Heavy aggregates never take the service down (regression journey)
**Verdict:** PASS
- Triggered a second, independent real background-compute window (`/backtest?asof=2026-07-16`; confirmed fresh dispatch via `/api/health`, `horizons_total=5`, not previously cached under the current `dataset_version`).
- Polled `GET /api/health` once per second for 20 straight seconds while that window was active. All 20 polls returned **HTTP 200** (observed latencies ranged 0.10s–1.22s — elevated above the settled ≤0.1s steady-state budget during the compute window, which is the same pre-existing, owner-accepted BCW behavior documented in `reports/perf-budgets.md`, not new). No timeout, no non-200 response, no frozen window at any point.
- The window completed cleanly (`outcome:"completed"`, `duration_ms:66297`) and `readiness` returned to `"ready"` immediately, confirming the service was never wedged.
- Scope note: J-07's step-3/step-4 (peak-VmPeak measurement, induced memory-pressure fault injection) require backend-internal test hooks that are outside what a browser-QA pass can exercise, and were already executed and dated 2026-07-25 as TC-13/TC-14 — both explicitly listed as binding "do not redo" items in this iteration's phase spec. This regression check therefore covers the browser-observable subset of J-07's acceptance (health stays responsive and the service doesn't crash under a real, naturally-triggered forward-aggregate compute), which is the part relevant to confirming no regression from this iteration's read-only instrumentation.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Golden replay scripts written this run

- `runs/goal-session-ops-hardening/journey-scripts/J-09.json` — target journey, verified PASS above. Scripted as a structural smoke check (loads `/backtest`, steps to a historical date via the "Previous available date" button and confirms the `(historical)` indicator text, then confirms the `/data` panel heading "Background compute" and its process-lifetime disclosure sentence are present) rather than asserting a live active-window/outcome, since triggering a *real* uncached dispatch is inherently cache-state-dependent across replay runs (dates cache permanently per `dataset_version`) and not safely deterministic for an unattended replay. Linted clean via `demo_runner.py --mode lint`.
- `runs/goal-session-ops-hardening/journey-scripts/J-07.json` — regression journey, verified PASS above. Scripted as a minimal smoke check (loads `/backtest`, `/`, `/data` and confirms each renders) since J-07's actual acceptance criteria (peak memory measurement, induced memory-pressure fault injection) are backend load-test scenarios that cannot be expressed as `goto`/`click`/`fill` UI replay steps. Linted clean via `demo_runner.py --mode lint`.

J-01, J-03, J-04, J-05, J-06, J-08 were re-verified this iteration via deterministic replay from their existing golden scripts (per the dispatch instructions) and are not re-tested or re-scripted here.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (stopped and restarted once during UT-07/UT-04 testing; healthy and `readiness: "ready"` at end of run)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-26
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-24-evidence/`
- **Known tooling issue this run:** scrolled-viewport screenshots return a blank solid-color frame on this host (see note at top of report); below-the-fold assertions were verified via DOM extraction and direct backend API/DB reads instead, quoted verbatim throughout this report.
