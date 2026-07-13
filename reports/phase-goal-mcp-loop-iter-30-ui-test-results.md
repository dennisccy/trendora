# Phase goal-mcp-loop-iter-30 — UI Test Results

**Phase:** goal-mcp-loop-iter-30
**Date:** 2026-07-13
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 10/10 tests passed (0 skipped)

All five P1 tests (UT-01, UT-02, UT-05, UT-06, UT-09) pass. All five P2 tests (UT-03, UT-04,
UT-07, UT-08, UT-10) also pass — no failures anywhere in this plan. UT-02 (the J-18 step-1
centerpiece: discoverability + all 11 rows correctly populated) is fully verified; a
deterministic golden replay script was written to
`runs/goal-session-mcp-loop/journey-scripts/J-18.json` and lints clean via `demo_runner.py --mode lint`.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/research/registry` loads directly, structure present | smoke | P1 | Back-link, heading, subtitle, 5 headers (Selectors/Rationale/Registered/Source/Status) in order, no console error | Direct nav to `/research/registry` rendered "← Back to Research", heading "Pre-registration registry", exact subtitle text, table with exactly the 5 expected headers in order, 11 populated rows; 0 console messages captured | PASS | `reports/qa/goal-mcp-loop-iter-30-evidence/UT-01-initial.png` |
| UT-02 | CENTERPIECE: discover from hub + all 11 rows populated (J-18 step 1) | happy-path | P1 | 1 click from `/research` reaches `/research/registry` with a clean URL (no `?asof=`); exactly 11 rows; all 5 cells non-empty per row; Registered column `yyyy-mm-dd` | Clicked "Pre-registration registry" card from `/research`; `window.location.href` resolved to `http://localhost:3255/research/registry` (no query string); DOM query confirmed `rowCount:11`; all 11 rows' 5 cells inspected via JS — none blank; Registered = `2026-07-03` for all 11 rows | PASS | `reports/qa/goal-mcp-loop-iter-30-evidence/UT-02-hub-governance-section.png` |
| UT-03 | Selectors render as chips, never raw JSON | validation | P2 | vcp_contraction/h60 row: 6 chips (`decile=10, direction=positive, factor=vcp_contraction, horizon=60, kind=factor, slice_kind=decile`); combination row: 5 chips incl. `condition=rs_spy_3m:top:quintile+atr_pct:bottom:tertile` joined by `+`; no raw `{...}` | DOM query on both rows returned exactly those chip texts in that order, each chip a separate `<div class="...border...bg-surface-2...">` element; rawHTML dump showed no `{`/`}` anywhere in either cell | PASS | Confirmed in `UT-01-initial.png` (pill-chip styling visible); precise chip list captured via in-page `eval` (see transcript) |
| UT-04 | Status badges neutral + vocabulary-only + "backfill" label | validation | P2 | `ma_stack` row = `closed`; all other 10 = `tested`; every row also shows a `backfill` badge; both badges neutral gray, never green/red; no proven-language | DOM query over all 11 rows: `ma_stack` row badge text = `closed`, all other 10 = `tested`; every row had a second badge reading `backfill`; badge classes were `bg-surface-2 text-text-muted` / `bg-surface-2 text-text-faint` (no color-verdict classes); Source-column "certified-claims.jsonl" filename citations present but correctly not proven-language | PASS | `reports/qa/goal-mcp-loop-iter-30-evidence/UT-01-initial.png` (visible neutral gray `tested`/`closed`/`backfill` pills); full badge-class dump via `eval` |
| UT-05 | Backend unavailable → one contained error card | error | P1 | Single "Backend unavailable" card, red border, warning icon; heading/back-link still render; sidebar stays clickable; recovers cleanly after restart | Stopped backend (`kill -TERM`, confirmed port 8255 no longer listening); reload showed exactly the expected card text, red-tinted border, warning-triangle icon, heading + back-link intact; clicked sidebar "Evidence" link — navigated successfully (nav not frozen); restarted backend via `start-backend.sh`, polled healthy in <2s; reload showed the populated 11-row table again with no leftover error card | PASS | `reports/qa/goal-mcp-loop-iter-30-evidence/UT-05-backend-unavailable.png` |
| UT-06 | Missing file → honest empty state, no crash | error | P1 | Book-icon card "No registrations yet" with the specified body text; NOT the error card, NOT a crash; recovers after file restore | Renamed `pre-registrations.jsonl` → `.bak`; confirmed `GET /api/research/registry` returned `{"registrations":[]}` (200, no crash); reload showed exactly "No registrations yet" with the exact expected body text and book icon, neutral (non-red) styling, distinct from the UT-05 error card; renamed file back; reload confirmed `tableRowCount:11`, no leftover empty-state or error text | PASS | `reports/qa/goal-mcp-loop-iter-30-evidence/UT-06-empty-state.png` |
| UT-07 | Loading skeleton (8 bars) shown, then fully replaced | smoke | P2 | 8 pulsing placeholder bars before data; no flash of empty table/premature empty-state; fully replaced by the 11-row table with no leftover skeleton | Chrome MCP has no native network-throttle action, so the registry fetch was delayed in-page (client-side route transition preserved the patched `window.fetch`, delaying only the `/api/research/registry` call). Immediately after the click, DOM query found `pulseElementCount:8` (`animate-pulse` class, `bg-surface-2`), `tablePresent:false`, no "No registrations yet" text. After the delayed fetch resolved: `pulseElementCountAfterLoad:0`, `tableRowCount:11` | PASS | `reports/qa/goal-mcp-loop-iter-30-evidence/UT-07-loading-skeleton.png`, `UT-07-skeleton-8bars-confirmed.png`, `UT-07-loaded-after-skeleton.png` |
| UT-08 | Existing 10-lab grid completely unchanged | regression | P2 | Exactly 10 cards, same order/labels as before, "Pre-registration registry" only in the separate Governance section | Markdown extract of `/research` listed exactly 10 lab cards in the exact expected reading order (Factor Lab … Downtrend Opportunity), followed by a separate "Governance & process" heading with exactly 1 card | PASS | `reports/qa/goal-mcp-loop-iter-30-evidence/UT-02-hub-governance-section.png` |
| UT-09 | `/evidence` unaffected — 7 FAIL claims, confirms router wiring safe | regression | P1 | Heading/subtitle correct; exactly 7 claim cards; every one shows red FAIL (none PASS/INSUFFICIENT); no console error | `/evidence` loaded heading "Evidence" + exact subtitle; DOM query confirmed 7 "Backs:" links (= 7 cards); screenshot confirmed all 7 show a red-outlined "FAIL" badge; 0 console messages captured — confirms `main.py`'s new `registry.router` registration did not break backend startup or this pre-existing page | PASS | `reports/qa/goal-mcp-loop-iter-30-evidence/UT-09-evidence-page.png` |
| UT-10 | Discoverable in ≤2 clicks from Dashboard, clear label | ux | P2 | Dashboard → Research = click 1; Governance card visible on ordinary scroll; card → registry = click 2 (2 total); sidebar unchanged | From `/`, clicked sidebar "Research" (7th item) → `window.location.href` = `/research` (click 1); scrolled down (no find/search) to reveal "Governance & process" + the card, description in plain language; clicked card → `/research/registry` (click 2); sidebar order across all pages visited (Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Evidence, Watchlist, Methodology, Data Manager) identical and unchanged | PASS | `reports/qa/goal-mcp-loop-iter-30-evidence/UT-10-from-dashboard-research-scrolled.png` |

---

## Passed Tests

### UT-01 — `/research/registry` loads directly, structure present
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-30-evidence/UT-01-initial.png`
- Navigated directly to `http://localhost:3255/research/registry` (no hub pass-through). "← Back to Research" link, heading "Pre-registration registry", and the exact subtitle text all rendered. `extract` (text mode) on the `table` element confirmed the 5-column header row `SELECTORS | RATIONALE | REGISTERED | SOURCE | STATUS` in that exact order, and all 11 data rows below it. `get_console_messages` (logging enabled before navigation) returned zero messages.

### UT-02 — CENTERPIECE: discover from hub + all 11 rows populated (J-18 step 1)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-30-evidence/UT-02-hub-governance-section.png`
- From `/research`, scrolled past the 10-card lab grid to the "Governance & process" heading and its single "Pre-registration registry" card (book icon visible), description ending exactly "The gate refuses to certify anything that isn't here." Clicked the card; `window.location.href` resolved to `http://localhost:3255/research/registry` with no query string. A DOM query (`document.querySelectorAll('table tbody tr')`) returned `rowCount:11`; a second query dumped all 11 rows' 5 cell texts — every cell in every row was non-empty, and the Registered column read `2026-07-03` for all 11 rows.

### UT-03 — Selectors render as chips, never raw JSON
**Verdict:** PASS
**Evidence:** Chip content and DOM structure captured via in-page `eval` (see transcript); visual confirmation in `UT-01-initial.png`.
- Row "Does the post-contraction expansion edge persist/strengthen over a quarter?" (vcp_contraction/h60): DOM query found exactly 6 chip elements reading `decile=10`, `direction=positive`, `factor=vcp_contraction`, `horizon=60`, `kind=factor`, `slice_kind=decile` (alphabetical), each its own `<div>` with pill styling — no `{`/`}` in the cell's raw HTML.
- Row "Momentum leadership that is NOT volatile/extended" (combination): 5 chips — `cohort=composite`, `condition=rs_spy_3m:top:quintile+atr_pct:bottom:tertile` (the two condition legs joined by a single `+`, not an array), `direction=positive`, `horizon=20`, `kind=combination`.

### UT-04 — Status badges neutral + vocabulary-only + "backfill" label
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-30-evidence/UT-01-initial.png`; badge text/class dump via in-page `eval`.
- DOM query over all 11 rows' Status cells: the `ma_stack` row ("Moving-average-stack…") read `closed`; all other 10 rows read `tested`. Every one of the 11 rows additionally carried a second badge reading `backfill`. No row anywhere read "Proven", "Not yet proven", "PASS", "FAIL", or any confidence wording. Badge CSS classes for both badge types used only neutral tokens (`bg-surface-2`, `text-text-muted`, `text-text-faint`, plain `border-border`) — no green/red/accent classes, visually distinct from `/evidence`'s colored verdict badges (confirmed side-by-side against UT-09). Source-column citations like "certified-claims.jsonl (original canonical claim…)" are honest provenance text, correctly not flagged as proven-language.

### UT-05 — Backend unavailable → one contained error card
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-30-evidence/UT-05-backend-unavailable.png`
- With the backend running, the table rendered normally (per UT-01/02). Stopped the backend (`kill -TERM` on the uvicorn PID; confirmed port 8255 no longer listening, `curl` returned `000`). Reloaded `/research/registry`: a single card appeared reading "Backend unavailable" / "The pre-registration registry could not load from the API. Confirm the backend is running and reload." — red-tinted border, warning-triangle icon, heading and "Back to Research" link still rendered above it (contained, not full-page). No blank page, no browser network-error page, no unhandled JS overlay. Clicked the sidebar "Evidence" link during the outage — navigation succeeded (`window.location.href` → `/evidence`), confirming the nav stayed clickable. Restarted the backend via `scripts/start-backend.sh` (`CHAIN_BACKEND_PORT=8255 CHAIN_FRONTEND_PORT=3255`), polled `/api/health` to 200 in ~1-2s. Reloaded the registry page: `tableRowCount:11`, `leftoverErrorCard:false`.

### UT-06 — Missing file → honest empty state, no crash
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-30-evidence/UT-06-empty-state.png`
- Renamed `runs/goal-session-mcp-loop/state/pre-registrations.jsonl` → `.bak` (no backend restart). Confirmed via `curl` that `GET /api/research/registry` now returns `{"registrations":[]}` (200, no crash). Reloaded `/research/registry` in the browser: a card appeared with a book icon, heading "No registrations yet", and body text beginning "Nothing is registered yet. Once a hypothesis is registered, it appears here with its selectors, rationale, registration date, and source" — a calm, neutral-styled card, visibly distinct from UT-05's red error card (also confirmed the top-bar status pill read "Ready"/"provider: seed", not "Backend unavailable", proving this is a data-shape state, not a connectivity failure). Page heading/subtitle still rendered above it. Renamed the file back, confirmed via `curl` (`count: 11`) and then in-browser reload: `tableRowCount:11`, `leftoverEmptyState:false`, `leftoverErrorCard:false`, 0 console messages.

### UT-07 — Loading skeleton (8 bars) shown, then fully replaced
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-30-evidence/UT-07-loading-skeleton.png`, `UT-07-skeleton-8bars-confirmed.png`, `UT-07-loaded-after-skeleton.png`
- The Chrome MCP tool exposes no dedicated network-throttle action (no DevTools-protocol passthrough for `Network.emulateNetworkConditions` in its action set). As a best-effort equivalent, `window.fetch` was monkey-patched on `/research` (while the JS context was still live) to delay only requests to `/api/research/registry` by 10s, then the "Pre-registration registry" card was clicked — a Next.js client-side route transition, which does not reset the JS context, so the patched `fetch` carried over to the destination route exactly as a slow network would. Immediately after the click, a DOM query found `pulseElementCount:8` (all `class*="animate-pulse" bg-surface-2"`, e.g. `h-7 w-full animate-pulse rounded bg-surface-2`), `tablePresent:false`, and no "No registrations yet" text (no flash of an empty/premature state). After the delayed fetch resolved, a second DOM query confirmed `pulseElementCountAfterLoad:0` and `tableRowCount:11` — the skeleton was fully and cleanly replaced.

### UT-08 — Existing 10-lab grid completely unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-30-evidence/UT-02-hub-governance-section.png`
- Markdown extract of `/research` listed exactly 10 lab cards, in the exact expected reading order: Factor Lab, Regime Lab, Market Phase & Severity Lab, Regime × Phase × Factor, Regime × Setup × Pattern, Severity-velocity × Regime, Multi-factor combination, Setup & Pattern event study, Recovery-Turn Edge, Downtrend Opportunity. The "Governance & process" heading and its single "Pre-registration registry" card appear only afterward, in a visually separate section — confirmed both textually and in the screenshot (3-column grid of 10, then a separate single-card row below a section heading).

### UT-09 — `/evidence` unaffected — 7 FAIL claims, confirms router wiring safe
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-30-evidence/UT-09-evidence-page.png`
- `/evidence` loaded with heading "Evidence" and the exact expected subtitle. A DOM query for `Backs:`-labeled links returned `backsLinkCount:7`. The full-page screenshot confirms all 7 cards (`leadership_score`, `Breakout-watch setup`, `ma_stack — top decile`, `vcp_contraction — top decile` ×2, `rs_spy_3m × high_proximity — composite`, `rs_spy_3m — top decile`) each show a red-outlined "FAIL" badge — none PASS or INSUFFICIENT. Zero console messages captured. This confirms `apps/backend/main.py`'s new `registry.router` registration (added beside the pre-existing `evidence.router` line) did not break backend startup or this pre-existing page.

### UT-10 — Discoverable in ≤2 clicks from Dashboard, clear label
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-30-evidence/UT-10-from-dashboard-research-scrolled.png`
- From `http://localhost:3255/` (Dashboard), clicked the sidebar's "Research" entry (7th item, microscope icon) — `window.location.href` resolved to `/research` (**click 1**). Scrolled down with ordinary scroll (no find/search) and the "Governance & process" heading with its single "Pre-registration registry" card appeared directly below the main lab grid, title and one-line description in plain language (no internal jargon). Clicked the card — `window.location.href` resolved to `/research/registry` (**click 2**, 2 total). The sidebar's 11 entries (Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Evidence, Watchlist, Methodology, Data Manager) were identical and in the same order across every page visited this session — no new entry, no reordering.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Golden Replay Script

Per the goal-mode addendum, a deterministic replay script was written for **J-18** (the target
journey, whose browser-testable half is UT-01/UT-02/UT-10 above) to
`runs/goal-session-mcp-loop/journey-scripts/J-18.json`:

```json
{
  "schema_version": 1,
  "journey": "J-18",
  "name": "Pre-registration registry — discoverable from Research hub, lists every registered hypothesis",
  "default_timeout_ms": 8000,
  "steps": [
    {"n": 1, "journey": "J-18", "action": {"type": "goto", "url": "/research"}, "expect": {"text": "Pre-registration registry"}},
    {"n": 2, "journey": "J-18", "action": {"type": "click", "target": {"role": "link", "name": "Pre-registration registry"}}, "expect": {"text": "factor=vcp_contraction"}}
  ]
}
```

Validated with `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-mcp-loop/journey-scripts --journeys J-18` → `J-18 ok`.

---

## Notes on test-plan scope (not gaps)

Per the UI test plan's own "Context for the tester", the following are intentionally **not**
covered here because they have no browser surface by design and are fixture-proven instead
(see `reports/qa/goal-mcp-loop-iter-30-test-plan.md` TC-04–TC-10, TC-13–TC-15): the gate's
registered/unregistered/near-miss/enforcement-off cross-check in
`project-extensions/gates/verify_claim.py` (CLI/backend-only, never reachable from a browser),
the loader/endpoint single-source byte-comparison, the missing-file loader-level unit test, the
backfill round-trip proof, the registry-file status-vocabulary artifact check, and the
pre/post ledger checksum diff. This is consistent with the phase spec's own testing-requirements
split and is not a limitation of this browser pass.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-13
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-30-evidence/`
- **Operational note:** the backend was intentionally stopped (UT-05) and restarted
  (`scripts/start-backend.sh`, `CHAIN_BACKEND_PORT=8255 CHAIN_FRONTEND_PORT=3255`), and the
  registry data file was intentionally renamed away and restored (UT-06), both as prescribed by
  their test steps. Both round-trips were confirmed fully recovered (11/11 rows, no leftover
  error/empty-state artifacts, backend healthy) before the test pass concluded.
