# goal-ops-hardening-iter-56 — UI Test Results

**Phase:** goal-ops-hardening-iter-56
**Date:** 2026-08-10
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass. -->

**Overall:** 1/1 tests passed (0 skipped)

Lean-mode scope: only J-06 was dispatched to this agent this run (J-01, J-03, J-04, J-08, J-09
are required-still-passing journeys verified separately by deterministic golden replay this
iteration).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-06 | Pages load only what they need | regression/perf | P1 | All 11 nav-listed pages load with expected heading + content on a warm prod-mode backend; every on-load API call answers within budget (specifically `GET /api/runs` and `GET /api/data/availability`, this iteration's fix targets, must be far under the ≤1.5s budget in real-browser conditions) | All 11 pages loaded cleanly with correct headings and substantial interactive DOM content, no error-boundary/blank shell. Real-browser `performance` API confirms `GET /api/runs` 216-433ms (was 3.2-7.5s WARN pre-fix) and `GET /api/data/availability` 90ms (was 15.1-21.2s WARN pre-fix) — both now comfortably inside budget | PASS | `reports/qa/goal-ops-hardening-iter-56-evidence/J-06-result.png` |

---

## Passed Tests

### UT-J-06 — Pages load only what they need
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-56-evidence/J-06-result.png` (screenshot of `/data` with the availability heatmap rendered)

**Environment confirmed:** backend running via `scripts/start-backend.sh` (uvicorn, port 8255, host-guard flags present in the process's own launch args) and frontend via `scripts/start-frontend.sh` (`next start -p 3255`, prod mode — confirmed by process list, not `next dev`), both already warm at dispatch time (`GET /api/health` → 200, `readiness: "ready"`, `warmup.done == warmup.total == 89`).

**Steps executed (goal.md J-06 step 1 — load each listed page, record TTI + on-load API latencies):**

1. `/` (Dashboard) — heading "Dashboard" rendered, 14 buttons / 12 links. On-load API calls observed via `performance.getEntriesByType('resource')`: `health` 241/243/245ms, `dashboard` 16ms, `methodology` 13ms, **`runs` 234ms**, `market-phase` 81/106ms, `sectors` 9ms, `themes` 6ms, `indexes?full=true` 120ms, `regime-history?full=true` 217ms, `market-phase?full=true` 106ms. All within budget.
2. `/stocks` — heading "Stocks", 772 buttons / 555 links (full stock table rendered). `stocks` 183ms, `runs` 433ms.
3. `/stocks/AAPL` — heading "AAPL", 6 buttons / 13 links. Loaded cleanly.
4. `/sectors` — heading "Sectors", 15 buttons / 11 links. Loaded cleanly.
5. `/themes` — heading "Themes", 15 buttons / 11 links. Loaded cleanly.
6. `/data` — heading "Data Manager", 82 buttons / 9 inputs / 11 links. `data` (coverage) 233ms, **`runs` 229ms**, `indexes?full=true` 123ms. The per-trading-date "Availability" heatmap section (J-61 widget, this iteration's second fix target) fires its own `GET /api/data/availability` call after a pre-existing 2500ms client-side stagger (`AVAILABILITY_FETCH_STAGGER_MS` in `apps/frontend/app/data/page.tsx`, unchanged by this iteration — confirmed by reading the surrounding code comment, which documents that stagger as a prior fix for GIL contention with `IndexVendorPanel`'s concurrent `indexes?full=true` call). Re-checked resource timings 3.5s after navigation: **`data/availability` started at t=2556ms, took 90ms** — far under the ≤1.5s budget, and a dramatic improvement over Addendum 18's pre-fix 15.1-21.2s browser-observed reading. Heatmap rendered with real per-date cells (screenshot evidence).
7. `/evidence` — heading "Evidence", 3 buttons / 18 links. Loaded cleanly.
8. `/scanner-runs` — heading "Scanner Runs", 2956 links (matches the live DB's 2,945+ `scanner_runs` rows — confirms the full run list rendered, not a paginated/truncated stub). This is the page most directly exercising the `/api/runs` N+1 fix: **`runs` 414ms and 350ms** across two measurement windows — consistent with the dev handoff's live-HTTP measurement (1.01-1.23s) and far under budget; previously this endpoint measured 3.2-7.5s WARN (Addendum 18) on this same page.
9. `/backtest` — heading "Backtest", 21 buttons / 11 links. Loaded cleanly.
10. `/watchlist` — heading "Watchlist", 11 buttons / 3 inputs / 17 links. Loaded cleanly.
11. `/research/factor-lab` (one research lab) — heading "Research — Factor Lab", 20 buttons / 11 links. `research/factor-lab?all=true` 27/18ms, `runs` 216ms. Also spot-checked `/research/regime-lab` (the golden's pinned lab) — heading "Research — Regime Lab" rendered correctly too, 5 buttons / 11 links.

**Error-boundary / console check:** grepped all 11 pages' captured DOM/markdown snapshots for "something went wrong", "application error", "unhandled", "failed to fetch" — zero matches across all pages. (Note: the Chrome MCP tool's own console-message capture reports "Console logging not yet implemented" in this build — a tool limitation, not a test failure; DOM-level error-boundary text search was used as the fallback signal, per the skill's "Element not found" guidance for tooling gaps.)

**Acceptance assessed:**
- **Consistency (single source):** not independently re-verified by browser QA (code-level claim — see dev handoff / Addendum 20); browser evidence is consistent with it (identical `n_stocks`-driven `/scanner-runs` row count, identical heatmap cell shape).
- **Correctness:** the `/scanner-runs` page rendered 2,945 run rows and the `/data` heatmap rendered real per-date cells — values match what the dev handoff's byte-identity proof claims (not independently diffed pixel-by-pixel by this agent, but no honest-fallback/empty-state text was observed where real data was expected).
- **Honest status & anti-goals:** no frozen/blank frame observed on any of the 11 pages; the availability heatmap's own staggered fetch showed no visible loading-state hang (heatmap resolved to real cells well before the 3.5s check).
- **Walkthrough:** out of scope for this agent — the `demo.sh --session-live` walkthrough capture is the demo-narrator's artifact, not browser-qa's.

---

## Failed Tests

None.

---

## Skipped Tests

None. J-01, J-03, J-04, J-08, J-09 were explicitly excluded from this dispatch (verified separately by deterministic golden replay per the dispatch instructions) — not skipped by this agent, out of scope for this run.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (headless, pinned profile)
- **Test Date:** 2026-08-10
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-56-evidence/`
- **Golden replay script written/updated:** `runs/goal-session-ops-hardening/journey-scripts/J-06.json` (lint-clean via `demo_runner.py --mode lint`)
