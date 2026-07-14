# Phase goal-mcp-loop-iter-35 — UI Test Results

**Phase:** goal-mcp-loop-iter-35
**Date:** 2026-07-14
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 14/14 tests passed (0 skipped)

All P1 tests pass (UT-01, UT-02, UT-03, UT-04, UT-07, UT-08, UT-09). The J-21 live-vs-seed
drift monitor is correctly implemented end-to-end: the `/data` drift card renders all four
specified states with exact copy, the site-wide preflight banner correctly surfaces and
clears the drift reason, and all four required-still-passing journeys (J-20, J-13, J-01,
J-05) were re-verified live with no regression.

**Read the Environment & Infrastructure Findings section below before treating this PASS as
routine** — reaching it required diagnosing and correcting two environment issues that were
not product defects but materially affected what the browser initially saw.

---

## Environment & Infrastructure Findings (read first)

These are not application bugs in the drift feature; they are documented here because they
materially shaped this test run and are relevant to the pipeline/dev process.

### 1. Stale production frontend build (found and corrected)

At the start of this run, `/data` rendered with **zero** occurrences of "drift" anywhere in
the page — the entire `DriftReportPanel` card was missing, not just showing a wrong state.
Diagnosis: the frontend is served via `next start` (a pre-built production bundle, per
`scripts/start-frontend.sh`'s own documented design). `.next/BUILD_ID` was stamped
**12:40:31**, while `apps/frontend/app/data/page.tsx` and `apps/frontend/lib/api.ts` (the
files implementing the drift feature) were last modified **14:37–14:38** — nearly two hours
*after* the build. `start-frontend.sh`'s conditional-build logic only rebuilds when
`BUILD_ID` is absent or the backend-URL stamp changed, neither of which was true here, so it
had been silently serving a pre-drift-feature bundle.

**Action taken:** forced a rebuild via the project's own `start-frontend.sh` (removed only
the `.next/BUILD_ID` build artifact to trigger its existing "no usable build" branch — no
source file was touched), then re-verified. After the rebuild, the drift card and all its
states rendered correctly and matched spec exactly for the remainder of this run. This is
purely a deployment-freshness issue, not a code defect — but it means **any browser-qa run
in this harness where frontend source changed after the last build will silently test a
stale bundle** unless something rebuilds first. Worth a pipeline-level fix (e.g., the
dev/QA-launch step comparing source mtimes to `BUILD_ID` before handing off to browser-qa).

### 2. Backend unavailability observed twice during UT-05 (not conclusively attributed to product code)

While testing UT-05 (corrupted drift artifact), the backend became unreachable twice in
immediate proximity to writing the `not-json` fixture and loading `/data`:
- The backend's own uvicorn log for the run in question ended with a **clean, ordinary
  shutdown sequence** (`Shutting down` / `Waiting for application shutdown` / `Application
  shutdown complete` / `Finished server process`) — **no traceback, no error, no OOM
  signal**. This is not what an unhandled-exception crash looks like.
- This machine is a shared, multi-tenant automation environment: at the time, an unrelated
  project's backend (`/home/dennis-chan/Git/tapeology`, port 8301, identical uvicorn launch
  pattern) was also running concurrently, consistent with an external
  process-lifecycle/supervisor layer cycling backend processes independently of this test.
- On a clean restart with the **identical** corrupted-file fixture still in place, the
  backend came up and stayed stable through 50+ consecutive requests (including
  `/api/data` and `/api/health`, both correctly returning the honest `"status":
  "unreadable"` degradation with **zero** crashes) for the remainder of this entire test
  run. The failure did not reproduce.
- **Conclusion:** recorded as an observed-but-unconfirmed event, not a confirmed product
  bug. I cannot rule out that this fixture triggers it, but the evidence (clean shutdown
  logs, non-reproduction on retry, confirmed shared-tenant environment) points more toward
  external process-lifecycle management than an application crash. Flagging for visibility
  given this project's documented history of data-path memory issues (anti-goal #8
  lineage), even though this specific evidence doesn't confirm that class of bug here.

### 3. Self-inflicted CORS misconfiguration during my own restart (found and corrected, not a product bug)

When I restarted the backend after finding it down (per #2), I initially reconstructed the
launch command from `/proc/<pid>/cmdline`, which captures process **arguments** but not
**environment variables**. This silently dropped `CORS_ORIGINS` (normally set by
`scripts/start-backend.sh` to include `http://localhost:3255`), so the backend fell back to
its documented default of `http://localhost:3000` only. Result: `curl` and direct browser
navigation to the backend worked fine (neither is subject to CORS), but the frontend's own
`fetch()`/XHR calls were browser-side CORS-blocked, making `/data` show "Backend
unavailable" even though the backend was healthy and reachable. This is entirely an
artifact of my own incomplete manual restart, **not a product defect** — confirmed by
restarting properly via `CHAIN_BACKEND_PORT=8255 CHAIN_FRONTEND_PORT=3255
scripts/start-backend.sh` (which correctly derives `CORS_ORIGINS`), after which the
frontend worked normally for the rest of the run. Noted for completeness/transparency, and
as a caution for any future agent reconstructing a launch command from `/proc/pid/cmdline`
instead of the project's own start script.

### 4. Test-plan environment note did not match observed initial state

The UI test plan's "Environment Note" warned that a leftover `drift-report.json` with
`status:"drift"` for 435 symbols would already be on disk at test start. At the time I
began testing, no such file existed (confirmed via `ls`) — the artifact was genuinely
absent, and `GET /api/health` reported the `drift` component as `ok` with "No fetch has run
yet". This did not affect test validity (every test case sets its own precondition
explicitly, as the note itself anticipated), just recorded as a factual discrepancy from
the plan's prediction.

**Net effect on this report's evidence:** every PASS below rests on live DOM assertions
(exact `textContent`/`data-testid` checks via `eval`) taken *after* both infrastructure
issues were corrected and re-verified stable, not on the initial broken state. Screenshots
were re-captured (with full-page capture + deterministic crop, after discovering the
`/data` drift card sits below the fold and a plain viewport screenshot was landing on an
unrelated, coincidentally identical scroll position) so that each evidence file visually
shows the actual state it documents rather than a duplicate top-of-page frame.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Drift card renders in some valid state | smoke | P1 | Card present in one of 4 valid states, no crash | After frontend rebuild (see Finding 1), card present with exact absent-state text; no console error, no "Backend unavailable" box | PASS | `UT-01-valid-state-absent.png` |
| UT-02 | Drift card: absent/"no fetch yet" state | smoke | P1 | Exact gray text, no amber styling, no list | `data-testid="drift-status-absent"` text = "No fetch has run yet — nothing to compare against the committed seed." verbatim; class list has no warn styling | PASS | `UT-02-drift-status-absent.png` |
| UT-03 | Drift card: names symbol + dates on drift | happy-path | P1 | Exact heading + 2 rows (AAPL, MSFT) with dates + "adjustment seam"; GOOGL absent | `data-testid="drift-status-drift"` heading = "Live-vs-seed drift detected — the provider re-adjusted already-committed history for 2 symbols." exactly; rows "AAPL: 2026-07-08, 2026-07-09 — adjustment seam" and "MSFT: 2026-07-07 — adjustment seam" present; `drift-affected-GOOGL` not found; amber `border-warn bg-warn/10` styling confirmed | PASS | `UT-03-drift-detected-2-symbols.png`, `UT-03-drift-card-closeup.png` |
| UT-04 | Drift card: clean/quiet state | happy-path | P1 | Green-dot exact text with "20" from config, no amber styling | `data-testid="drift-status-clean"` text = "The most recent fetch matched the committed seed over the last 20 common date(s)." exactly; class = `text-pos`, no `border-warn` | PASS | `UT-04-drift-clean-state.png` |
| UT-05 | Drift card: corrupted artifact degrades honestly | error | P2 | Exact amber "could not be read" text; page doesn't crash; other panels intact; bonus: banner shows unreadable reason | `data-testid="drift-status-unreadable"` text exact match; Dataset coverage/Storage footprint/Rebuild/Job progress panels all confirmed present; site-wide banner confirmed DEGRADED with "Drift report is unreadable: the artifact exists but could not be parsed." (see Finding 2 for backend-availability caveats encountered while reaching this result) | PASS | `UT-05-drift-unreadable.png`, `UT-05-drift-card-closeup.png`, `UT-05-bonus-banner-unreadable.png` |
| UT-06 | Drift card: null field degrades gracefully | validation | P2 | Em-dash placeholder, no NaN/null/undefined, no amber | Text = "The most recent fetch matched the committed seed over the last — common date(s)." exactly; no "NaN"/"null"/"undefined" substrings found; class = `text-pos` (clean styling preserved) | PASS | `UT-06-null-overlap-days.png` |
| UT-07 | Banner: surfaces drift DEGRADED reason site-wide | happy-path | P1 | Exact DEGRADED heading + reason line, visible on Dashboard and other pages without visiting `/data` | `data-verdict="DEGRADED"`; heading "DEGRADED — treat today's board with caution." exact; reason "Live-vs-seed drift detected (adjustment seam) for: AAPL, MSFT." exact; confirmed identical on `/` and `/stocks` | PASS | `UT-07-banner-degraded-dashboard.png` |
| UT-08 | Banner: recovers to GO after clean fetch | happy-path | P1 | Banner returns to quiet GO strip, reasons list gone; `/data` also shows clean | `data-verdict="GO"`, text "GO — today's board is current." exact, 0 `<li>` reasons; `/data` reload confirmed `drift-status-clean` with matching text | PASS | `UT-08-banner-recovered-go.png` |
| UT-09 | Banner: GO unchanged when artifact absent (J-20) | regression | P1 | GO on every page, no reasons, when artifact absent | Confirmed on `/`, `/stocks`, `/data`: `data-verdict="GO"`, text exact, 0 reasons on all three | PASS | `UT-09-banner-go-absent-dashboard.png` |
| UT-10 | `/data` existing panels + card placement (J-13) | regression | P2 | Card order Coverage→Storage→**Drift**→Rebuild; all 7 coverage tiles present | Heading order confirmed exactly `["Dataset coverage","Storage footprint","Live-vs-seed drift","Rebuild snapshots for current universe",...]`; all 7 tiles (Price history, Universe, Candidate universe, Symbols, Trading days, Snapshot dates, Backfill gaps) present with values | PASS | `UT-10-panel-order.png` |
| UT-11 | Leaderboard evidence badges unaffected (J-01) | regression | P3 | Heading "Stocks", ≥1 evidence badge Proven/Not yet proven | Heading "Stocks" confirmed; 1623 `evidence-badge` elements found, first = "Not yet proven"; banner GO, no console error | PASS | `UT-11-stocks-leaderboard.png` |
| UT-12 | Evidence ledger page unaffected (J-05) | regression | P3 | Heading "Evidence", claim rows present, no error/empty state | Heading "Evidence" confirmed; 7 `evidence-claim-row` elements, no error card, no empty state; bonus check: `certified-claims.jsonl` line count = 7, matching the rendered row count exactly (no new ledger entry from this iteration) | PASS | `UT-12-evidence-page.png` |
| UT-13 | Drift card discoverable, no hover needed | ux | P2 | 1-click reach from sidebar; explanation visible with no interaction | Clicked "Data Manager" sidebar link from Dashboard, landed on `/data`; exact explanatory sentence ("Byte/fixed-precision compares the last N dates a Fetch job returns against the committed seed. A mismatch means the live provider silently re-adjusted already-committed history (an adjustment seam) — descriptive integrity reporting, recomputes nothing, never auto-repairs or re-fetches.") present in DOM without any hover/click simulated | PASS | `UT-13-discoverability.png` |
| UT-14 | Backend-unavailable fallback still works | error | P2 | Existing red error card shown; drift card absent entirely; recovers after backend restored | With backend stopped: "Backend unavailable" heading + exact body text confirmed; zero `[data-testid^="drift-"]` elements found (no partial fragment); after restoring backend properly, `/data` reload showed the clean-state drift card correctly (one of UT-01's 4 valid states) | PASS | `UT-14-backend-unavailable.png`, `UT-14-recovered.png` |

---

## Passed Tests

### UT-01 — Drift card renders in some valid state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-35-evidence/UT-01-valid-state-absent.png`
- After correcting the stale-build issue (Finding 1), navigated to `/data` and confirmed via
  `eval` that `[data-testid="drift-report-panel"]` exists, contains the `git-compare` icon,
  the title "Live-vs-seed drift", the state-independent explanatory sentence, and the
  absent-state body — no crash, no missing card, no empty card body.

### UT-02 — Drift card: absent/"no fetch yet" state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-35-evidence/UT-02-drift-status-absent.png`
- Confirmed `runs/goal-session-mcp-loop/state/drift-report.json` absent via `ls`. Loaded
  `/data`; `data-testid="drift-status-absent"` text is byte-exact: "No fetch has run yet —
  nothing to compare against the committed seed." No amber classes, no affected list.

### UT-03 — Drift card: names symbol + dates on drift
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-35-evidence/UT-03-drift-detected-2-symbols.png`, `UT-03-drift-card-closeup.png`
- Wrote the two-symbol drift fixture, reloaded `/data`. Heading text matches the spec
  exactly; `drift-affected-AAPL` = "AAPL: 2026-07-08, 2026-07-09 — adjustment seam";
  `drift-affected-MSFT` = "MSFT: 2026-07-07 — adjustment seam"; `drift-affected-GOOGL`
  confirmed absent; container has `border-warn bg-warn/10 text-warn` classes.

### UT-04 — Drift card: clean/quiet state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-35-evidence/UT-04-drift-clean-state.png`
- Wrote the clean fixture (`overlap_days: 20`), reloaded `/data`. Text is byte-exact: "The
  most recent fetch matched the committed seed over the last 20 common date(s)." — the "20"
  matches `config.yaml`'s `data_quality.drift.overlap_days`, rendered verbatim, not
  hardcoded. `text-pos` styling, no warn classes, no list.

### UT-05 — Drift card: corrupted artifact degrades honestly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-35-evidence/UT-05-drift-unreadable.png`, `UT-05-drift-card-closeup.png`, `UT-05-bonus-banner-unreadable.png`
- Wrote literal `not-json` to the artifact. After resolving the environment issues described
  in Findings 2–3, confirmed via `eval`: `data-testid="drift-status-unreadable"` text is
  byte-exact: "The drift report exists but could not be read. Re-run a Fetch job to
  regenerate it." Confirmed "Dataset coverage", "Storage footprint", "Rebuild snapshots",
  "Job progress" all still present around it. Bonus cross-surface check: reloaded `/`, banner
  `data-verdict="DEGRADED"` with reason "Drift report is unreadable: the artifact exists but
  could not be parsed." — matching the `/data` card's finding exactly, confirming the single
  `read_drift_report()` source. Re-tested stability with 50+ consecutive requests against
  this exact fixture with zero further incident.

### UT-06 — Drift card: null field degrades gracefully
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-35-evidence/UT-06-null-overlap-days.png`
- Wrote `{"status":"clean",...,"overlap_days":null,...}`. Text is byte-exact: "The most
  recent fetch matched the committed seed over the last — common date(s)." Confirmed no
  "NaN"/"null"/"undefined" substrings anywhere in the panel; `status` still renders as clean
  (`text-pos`, no amber) since only the number is missing.

### UT-07 — Banner: surfaces drift DEGRADED reason site-wide
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-35-evidence/UT-07-banner-degraded-dashboard.png`
- With the two-symbol drift fixture active, navigated directly to `/` (Dashboard).
  `data-verdict="DEGRADED"`; heading exact: "DEGRADED — treat today's board with caution.";
  reason exact: "Live-vs-seed drift detected (adjustment seam) for: AAPL, MSFT." Confirmed
  identical banner state persists after navigating to `/stocks`, proving layout-level
  mounting, not page-local.

### UT-08 — Banner: recovers to GO after clean fetch
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-35-evidence/UT-08-banner-recovered-go.png`
- From the DEGRADED state in UT-07, overwrote the artifact with the clean fixture and
  reloaded `/`. `data-verdict="GO"`, text exact: "GO — today's board is current.", zero
  `<li>` reason elements (amber box + reasons list fully gone, not just visually hidden).
  Reloading `/data` confirmed the drift card also shows the clean line, proving both
  surfaces recovered from the same artifact.

### UT-09 — Banner: GO unchanged when artifact absent (J-20)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-35-evidence/UT-09-banner-go-absent-dashboard.png`
- With the artifact file absent, checked the banner on `/`, `/stocks`, and `/data`: all
  three show `data-verdict="GO"`, exact text, zero reasons. This is the load-bearing
  non-regression property — confirmed byte-identical to pre-iter-35 expected behavior.

### UT-10 — `/data` existing panels + card placement (J-13)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-35-evidence/UT-10-panel-order.png`
- Queried all `<h2>` headings on `/data` in DOM order: `Dataset coverage` (0) →
  `Storage footprint` (1) → `Live-vs-seed drift` (2) → `Rebuild snapshots for current
  universe` (3) — the new card slotted in additively with no existing card moved, split, or
  disappeared. All 7 Dataset coverage tiles confirmed present with values.

### UT-11 — Leaderboard evidence badges unaffected (J-01)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-35-evidence/UT-11-stocks-leaderboard.png`
- `/stocks` heading "Stocks" confirmed; 1623 elements with `data-testid="evidence-badge"`
  found, first reads "Not yet proven"; banner GO; page unaffected by this iteration's
  backend/frontend changes (no code on this page was touched).

### UT-12 — Evidence ledger page unaffected (J-05)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-35-evidence/UT-12-evidence-page.png`
- `/evidence` heading "Evidence" confirmed; 7 `evidence-claim-row` elements rendered; no
  "could not load from the API" error text; no "No certified claims yet" empty state.
  Filesystem check: `certified-claims.jsonl` has exactly 7 lines, matching the 7 rendered
  rows — confirms this iteration added no new ledger entry.

### UT-13 — Drift card discoverable, no hover needed
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-35-evidence/UT-13-discoverability.png`
- From the Dashboard, clicked the "Data Manager" sidebar link (`a[href="/data"]`) — one
  click, landed on `/data` (confirmed via `window.location.href`). The full explanatory
  sentence beneath the card title is present in the DOM verbatim without any hover/click
  simulated to reveal it — it is plain static text, not a tooltip.

### UT-14 — Backend-unavailable fallback still works
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-35-evidence/UT-14-backend-unavailable.png`, `UT-14-recovered.png`
- Stopped the backend (`kill -TERM`, confirmed port free) for this test only. Loaded
  `/data`: "Backend unavailable" heading and exact body text present; confirmed **zero**
  `[data-testid^="drift-"]` elements anywhere on the page (no partial/broken drift
  fragment). Restored the backend via the project's own `start-backend.sh` (correct
  `CORS_ORIGINS`), reloaded: the clean-state drift card reappeared correctly, confirming
  full recovery.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Golden Replay Script

Wrote `runs/goal-session-mcp-loop/journey-scripts/J-21.json` (new; lint-checked with
`demo_runner.py --mode lint`, result: `J-21 ok`) asserting the state-independent parts of
the journey (card title + explanation always render regardless of drift status; the
preflight banner mounts and reflects a verdict on every page) since the deterministic
replay runner has no fixture-file-write action and therefore cannot reproduce a specific
drift/clean state at replay time.

J-20/J-13/J-01/J-05's existing golden scripts were **not** modified — I re-verified the
regression properties those journeys care about live (UT-09/UT-10/UT-11/UT-12), but through
different concrete steps than what's encoded in those existing scripts (e.g., I did not
visit `/stocks/NVDA` or `/watchlist`, and did not click a backfill "Start" button), so
overwriting them would have reduced their coverage below what's already committed without
new evidence to support the full replacement.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-14
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-35-evidence/`
- **Final state left behind:** both services running and healthy (`GET /api/health` →
  `200`, `preflight.verdict: GO`); drift artifact left in a valid clean state
  (`{"status":"clean","reference":"2026-07-10","overlap_days":20,"affected":[]}`) at
  `runs/goal-session-mcp-loop/state/drift-report.json`.
