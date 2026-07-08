# Phase goal-mcp-loop-iter-20 — UI Test Results

**Phase:** goal-mcp-loop-iter-20
**Date:** 2026-07-08
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

**Overall:** 0/22 tests passed (22 skipped)

**Reason:** Frontend not running. Precondition check confirmed both service endpoints unreachable before any test was attempted:
- `curl -s -o /dev/null -w "%{http_code}" http://localhost:3255` → `000` (connection failure)
- `curl -s -o /dev/null -w "%{http_code}" http://localhost:8255/health` → `000` (connection failure)

Per dispatch instructions ("Frontend is NOT available... Do NOT attempt to run browser tests"), no Chrome MCP session was opened and no navigation was attempted. All 22 test cases from `reports/phase-goal-mcp-loop-iter-20-ui-test-plan.md` are recorded as SKIPPED below.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/data` loads, required panels visible | smoke | P1 | Sidebar shows "Data Manager" active; "Start a fetch / backfill job" panel and "Per-date availability" card visible; no "Backend unavailable" card; no console errors | Frontend not running | SKIP | none |
| UT-02 | Job-kind picker: exactly 3 options, no Expand | smoke | P1 | Dropdown lists exactly "Backfill snapshots", "Fetch EOD prices", "Fetch + backfill" (default "Backfill snapshots"); no "Expand" option | Frontend not running | SKIP | none |
| UT-03 | Fetch EOD prices now covers ~588-symbol pool | happy-path | P1 | "Symbols fetched" counter total ≥548 (~588, not old ~162); progress bar advances; job reaches `{total}/{total}` | Frontend not running | SKIP | none |
| UT-04 | Backfill snapshots still starts and runs | regression | P1 | No error alert; "Snapshots backfilled" row shown; job runs with no client-side error or blank page | Frontend not running | SKIP | none |
| UT-05 | Fetch + backfill still starts, no Universe-screen block | regression | P1 | Both "Symbols fetched" and "Snapshots backfilled" rows appear; no "Universe screen" / "N passed"/"N omitted" block ever appears | Frontend not running | SKIP | none |
| UT-06 | Import-source options never disabled, no cap suffix | validation | P2 | Every option label ends "· available" or "· needs key"; none greyed out/unselectable; no "market cap"/"cannot supply"/"expand" text | Frontend not running | SKIP | none |
| UT-07 | No market-cap-ineligibility alert, any combination | validation | P2 | No amber "cannot supply market cap" alert for any job-kind/source combination; only a grey "{label}: available/needs key · {reason}" line | Frontend not running | SKIP | none |
| UT-08 | Panel title + explainer paragraph read post-removal copy | ux | P2 | Heading reads exactly "Start a fetch / backfill job"; explainer paragraph matches exact post-removal copy; no occurrence of "Expand" | Frontend not running | SKIP | none |
| UT-09 | Market-cap figures presented as static, not refreshable | ux | P3 | "Candidate universe" tile definition includes the word "static"; no claim anywhere of refresh/update-on-demand for market-cap figures | Frontend not running | SKIP | none |
| UT-10 | Availability legend renders two labeled groups | happy-path | P1 | Two stacked, separately labeled rows: "PRICE DATA — CELL FILL" (6 swatches) and "SCORED SNAPSHOT — INDICATOR" (ringed swatch) | Frontend not running | SKIP | none |
| UT-11 | Density top bucket is blue not amber; 6 steps distinct | happy-path | P1 | "full" swatch computed `background-color` is `rgb(166, 200, 242)` / `#a6c8f2`, not amber `#f0b429`; all 6 swatches one blue family, each visibly distinct from its neighbor | Frontend not running | SKIP | none |
| UT-12 | Snapshot ring is violet not green | happy-path | P1 | Ring computed color is `rgb(167, 139, 250)` / `#a78bfa`, not green `#34d399`; visually distinct on every fill shade | Frontend not running | SKIP | none |
| UT-13 | Hover readout shows "snapshot yes" in violet | happy-path | P2 | Ringed-cell hover readout shows "snapshot yes" in violet text; non-ringed cell shows "snapshot no" in muted grey; readout resets when mouse leaves | Frontend not running | SKIP | none |
| UT-14 | Hover distinguishes Backfill-gap day from snapshotted day | happy-path | P1 | No-ring, highly-filled cell's tooltip reads "...no snapshot yet — Backfill gap"; ringed cell's tooltip reads "...scored snapshot exists (Backfill)"; final clauses differ and both name Fetch/Backfill | Frontend not running | SKIP | none |
| UT-15 | Header blurb + caption name Fetch/Backfill workflow | ux | P2 | Header paragraph and calendar caption both explicitly state cell fill is "filled by Fetch" and ring is "produced by Backfill" | Frontend not running | SKIP | none |
| UT-16 | Availability card degrades honestly on API failure | error | P2 | Card shows "Availability could not load from the API. No cells are shown rather than fabricated values."; rest of page (form, sidebar) still usable; no uncaught JS error dialog | Frontend not running | SKIP | none |
| UT-17 | J-01: `/stocks` Sector sort, no crash | regression | P1 | Table renders with Ticker/Sector/Leadership/Entry Quality/Risk columns; two sector-sort clicks re-order visibly with arrow indicator; sidebar stays visible; no console error | Frontend not running | SKIP | none |
| UT-18 | J-03: "Not yet proven" badges intact | regression | P1 | Every inspected score (Leadership/Entry Quality/Risk) on first 5 rows shows "Not yet proven" beneath it; none reads "Proven"/"PASS" | Frontend not running | SKIP | none |
| UT-19 | J-05: `/evidence` ledger renders | regression | P1 | Page loads with "Evidence" heading; empty-state card or claim-row list renders; no "Backend unavailable" card, no blank page | Frontend not running | SKIP | none |
| UT-20 | J-10: deep-history chart still renders | regression | P1 | "Full history" toggle re-renders chart back many years with no blank area/error; caption date updates; "Recent" restores shorter window without error | Frontend not running | SKIP | none |
| UT-21 | J-12: universe count consistent across pages | regression | P1 | Universe/symbol count on `/methodology` is consistent with the total shown on `/stocks` leaderboard | Frontend not running | SKIP | none |
| UT-22 | "Data Manager" discoverable in 1 click from Dashboard | ux | P3 | "Data Manager" visible in sidebar without scrolling; 1 click navigates to `/data`; nav item highlights as active once there | Frontend not running | SKIP | none |

---

## Passed Tests

None.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-01 — `/data` loads, required panels visible
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-02 — Job-kind picker: exactly 3 options, no Expand
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-03 — Fetch EOD prices now covers ~588-symbol pool
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-04 — Backfill snapshots still starts and runs
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-05 — Fetch + backfill still starts, no Universe-screen block
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-06 — Import-source options never disabled, no cap suffix
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-07 — No market-cap-ineligibility alert, any combination
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-08 — Panel title + explainer paragraph read post-removal copy
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-09 — Market-cap figures presented as static, not refreshable
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-10 — Availability legend renders two labeled groups
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-11 — Density top bucket is blue not amber; 6 steps distinct
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-12 — Snapshot ring is violet not green
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-13 — Hover readout shows "snapshot yes" in violet
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-14 — Hover distinguishes Backfill-gap day from snapshotted day
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-15 — Header blurb + caption name Fetch/Backfill workflow
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-16 — Availability card degrades honestly on API failure
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-17 — J-01: `/stocks` Sector sort, no crash
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-18 — J-03: "Not yet proven" badges intact
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-19 — J-05: `/evidence` ledger renders
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-20 — J-10: deep-history chart still renders
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-21 — J-12: universe count consistent across pages
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-22 — "Data Manager" discoverable in 1 click from Dashboard
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

---

## Environment

- **Frontend URL:** http://localhost:3255 (unreachable — curl returned `000`)
- **Backend URL:** http://localhost:8255/health (unreachable — curl returned `000`)
- **Browser:** Chrome via MCP (not invoked — precondition check failed before any browser session was opened)
- **Test Date:** 2026-07-08
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-20-evidence/` (not created — no screenshots captured, no tests executed)
