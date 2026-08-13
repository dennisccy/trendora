# Phase goal-ops-hardening-iter-78 — UI Test Results

**Phase:** goal-ops-hardening-iter-78
**Date:** 2026-08-13
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 11/11 tests passed (0 failed, 0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Home page loads with readiness badge visible | smoke | P1 | Page renders without blank/error screen; "Ready" badge (`data-testid="readiness-badge"`, `data-state="ready"`) visible top-right; no console errors | Navigated to `/`. `readiness-badge` resolved `data-state="ready"` / text "Ready". Full styled Dashboard rendered (Market Regime chart, breadth stats, leaderboards, causal-episode table) — no blank screen, no error boundary. Console-log capture via this Chrome MCP build produced no messages in this environment (its own auto-captured `*-console.txt` files read "TODO: Console logging not yet implemented" — a tool-side limitation, not a page defect); no visible error UI was observed across ~15 page loads this session | PASS | `reports/qa/goal-ops-hardening-iter-78-evidence/UT-01-result.png` |
| UT-02 | Readiness badge staleness annotation ticks live every second | happy-path | P1 | `readiness-staleness` text increases by ~+10 over a 10s wait with no click/nav; never resets to "<1s ago" or disappears mid-window | Isolated same-page measurement (no navigation between reads), anchored with browser-side `Date.now()`: t=...437491ms → "as of 2s ago"; t=...457185ms (Δ19.694s real) → "as of 22s ago" (Δdisplayed 20s, within tolerance). A `window.fetch` interceptor confirmed only 1 real `/api/health` poll landed in a subsequent ~24.4s window — consistent with the documented 30s idle poll cadence — proving the annotation ticks locally between polls and resets only when a genuine poll lands. (An earlier read taken without a `Date.now()` anchor, immediately after page navigation, appeared to reset sooner than expected; re-investigated with precise timestamps — no reset occurs absent a real poll landing. Root-caused to imprecise wall-clock `sleep` estimation around the initial navigate's own render latency, not a product defect.) | PASS | `reports/qa/goal-ops-hardening-iter-78-evidence/UT-02-result.png` |
| UT-03 | Preflight banner staleness annotation ticks live every second | happy-path | P1 | `preflight-staleness` moves in lockstep with UT-02's badge value; banner's verdict text itself unchanged | Same measurement window as UT-02: `preflight-staleness` = "(as of 2s ago)" → "(as of 22s ago)" (Δ20s, matching the badge exactly). `preflight-banner` text stayed "GO — today's board is current." throughout — only the parenthetical number moved | PASS | `reports/qa/goal-ops-hardening-iter-78-evidence/UT-03-result.png` |
| UT-04 | Fresh/synchronous compute (`stale_for_s===0`) never starts ticking | validation | P2 | Neither staleness testid renders text at any point during a 10s wait when the base is `0` | Deviated from the literal test-plan steps: code inspection (`apps/backend/app/engine/readiness.py:642-666`) confirmed `stale_for_s===0` is only ever served on a process cold-start (before the background tick's first publish) or the unavailable-fallback path — not reachable on this already-steady-state backend (`stale_for_s` sampled 0.04-0.16s via direct curl) without restarting it, which this dispatch is not permitted to do. Instead exercised the real shipped frontend bundle with a controlled input: a `window.fetch` wrapper called through to the real backend and rewrote only the `stale_for_s` field of the parsed `/api/health` JSON to `0` before returning it (every other field/status passed through untouched). After the next poll landed with the forced `0`, `readiness-staleness`/`preflight-staleness` were both absent while "Ready"/"GO" rendered normally; after a further 10s with no interaction, both remained absent — no fabricated ticking from a `0` base. Original `fetch` restored afterward | PASS | `reports/qa/goal-ops-hardening-iter-78-evidence/UT-04-result.png` |
| UT-05 | Backend unreachable shows no fabricated staleness | error | P2 | Badge → `data-state="unavailable"` "Backend unavailable"; banner → `data-verdict="NO-GO"` with the unavailable reason; neither staleness testid renders, including through an extra 10s wait; recovers after | Deviated from the literal test-plan step of killing the real backend process — this dispatch is explicitly not permitted to restart/stop the app this run (same constraint iter-77's equivalent tests, UT-03/UT-08, resolved identically). Installed a `window.fetch` wrapper rejecting only `/api/health` requests (every other request passed through untouched), simulating an unreachable backend without touching the real process. After the next scheduled poll failed: badge → `data-state="unavailable"` text "Backend unavailable"; banner → `data-verdict="NO-GO"` text "NO-GO — do not rely on today's board." + "Backend is unavailable — the preflight check could not run."; both staleness testids absent, and still absent after a further 10s wait. Restored the original `fetch`; badge recovered to `data-state="ready"` with staleness ticking resumed ("as of 9s ago") within ~5s | PASS | `reports/qa/goal-ops-hardening-iter-78-evidence/UT-05-result.png` |
| UT-06 | Existing background-compute indicator on /data is untouched | regression | P1 | `background-compute-active-row` present with as-of/elapsed/horizons; header `background-compute-indicator` reads "background compute running (N)" alongside Ready | Clicked "Previous available date" on `/backtest` (asof 2026-07-31, an on-demand-dispatch date) → `GET /api/health` confirmed `background_compute.active` populated. On `/data`, `background-compute-active-row` read "as-of 2026-07-31 · elapsed Xs/1m27s · horizons 0/5→3/5 · dataset r2998-f6609160" across repeated reads (progressing, confirming a genuine live compute, not a static fixture); header `background-compute-indicator` read "background compute running (1)" alongside "Ready" simultaneously | PASS | `reports/qa/goal-ops-hardening-iter-78-evidence/UT-06-result.png` (target element pinned via a temporary inline-style overlay to work around a known Chrome-MCP headless screenshot-blanking quirk on this page's very tall DOM — the same quirk documented in this session's own J-09 golden `_notes` at iter-75/76; DOM content was verified live via `textContent`, not fabricated) |
| UT-07 | Header does not overflow with badge + staleness + compute chip together at 1280x800 | regression | P2 | All three elements remain fully visible, no clipping/overlap | Viewport set to 1280x800. With the same background compute in flight, `getBoundingClientRect()` on `/`: badge right-edge 601.6px; staleness spans 609.6-696.3px; indicator spans 704.3-953.1px — all three fully inside the 1280px viewport width, on one row, no overlap between any pair | PASS | `reports/qa/goal-ops-hardening-iter-78-evidence/UT-07-result.png` |
| UT-08 | Staleness annotation is visible and legible next to the Ready pill on first load | ux | P3 | Small gray "as of Ns ago" text plainly legible, no hover/click/dev-tools needed | Same load as UT-01/02 — `readiness-staleness` renders as plain inline `<span class="text-xs text-text-faint">` text immediately right of the Ready pill, legible at normal render with zero interaction required — not hidden behind an icon or tooltip | PASS | `reports/qa/goal-ops-hardening-iter-78-evidence/UT-01-result.png` (same acceptance state) |
| UT-J-04 | J-04: Non-blocking boot with visible status (target-journey re-verification) | regression | P1 | Readiness badge `data-state="ready"`; preflight banner mounted with a real verdict; `/data`'s `last-run-status` renders a real persisted value | `[data-testid="readiness-badge"]` `data-state="ready"` on `/`; `[data-testid="preflight-banner"]` `data-verdict="GO"`; on a fresh `/data` navigation `[data-testid="last-run-status"]` read "ok" (a real `data_provider_runs`-backed value, never fabricated). Steps 5-6 of J-04's full spec (restart timing, crash/kill-9 presentation) not re-exercised — restarting/killing the live QA backend is forbidden this run, and this iteration's diff touches only the client-side tick derivation, never boot/crash-computation logic, consistent with this journey's own carried reasoning across iterations 58-77 | PASS | `reports/qa/goal-ops-hardening-iter-78-evidence/UT-01-result.png`, `UT-06-result.png` |
| UT-J-07 | J-07: Heavy aggregates never take the service down (target-journey re-verification) | regression | P1 | Readiness stays ready and `/backtest` serves real stored scorecard content while a background compute is in flight; no service disruption | While the SAME background-compute window from UT-06 was active (asof 2026-07-31), navigated to `/backtest` and clicked "Previous available date": badge stayed `data-state="ready"` throughout; `[data-testid="backtest-asof"]` read "Viewing as-of 2026-07-31 (historical)"; `[data-testid="scorecard-row-1d"]` read "1d +0.70% n=20" — byte-identical to the value independently recorded across this session's own iter-75/76/77 live checks (AG-3 consistency: the same as-of date always yields the same computed number). No 500s, no blank/error page, no stall observed at any point `GET /api/health` was sampled this session (dozens of direct curl + browser reads, all HTTP 200). Per the phase spec's binding "Do not redo," the VmPeak/memory-pressure drill (J-07 steps 3-4) was intentionally NOT re-run — this iteration's diff touches only the frontend tick, the launcher purge, and a walkthrough-capture script, none of `app.engine.readiness`'s server compute or `compute_forward_aggregates` | PASS | `reports/qa/goal-ops-hardening-iter-78-evidence/UT-J-07-result.png` |
| UT-J-09 | J-09: The backend discloses its own background-compute activity (target-journey re-verification) | regression | P1 | Badge + `/data` panel disclose in-flight compute with real, progressing values; transitions cleanly to idle + last-outcome on completion | Full active→idle lifecycle observed fresh this run: dispatched via `/backtest`'s "Previous available date" (asof 2026-07-31) → `background-compute-active-row` progressed 0/5→1/5→2/5→3/5 with a real elapsed-time readout, header `background-compute-indicator` reading "background compute running (1)" simultaneously with "Ready" (never a bare Ready) → after completion, `/data` showed `background-compute-idle`=true and `background-compute-last-outcome`="completed as-of 2026-07-31 1m 51s" (matching `GET /api/health`'s own `recent_outcomes` entry exactly). This directly re-observes the "compute in flight" scene iter-77/e flagged as missing from the walkthrough-gallery frame — this browser-qa pass verifies the LIVE product behavior only; the dev-owned walkthrough-capture *script* timing fix is a separate artifact (per the dev handoff), not something this browser-qa run produces or claims to fix | PASS | `reports/qa/goal-ops-hardening-iter-78-evidence/UT-06-result.png`, `UT-J-09-idle-result.png` |

---

## Passed Tests

### UT-01 — Home page loads with readiness badge visible
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-78-evidence/UT-01-result.png`
- `readiness-badge` `data-state="ready"` / "Ready"; full Dashboard content rendered; no blank/error page.

### UT-02 — Readiness badge staleness annotation ticks live every second
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-78-evidence/UT-02-result.png`
- "as of 2s ago" → "as of 22s ago" over a precisely-measured ~19.7s real elapsed window with zero interaction; a `fetch`-interceptor confirmed no extra poll landed in that window (1 poll / 24.4s, matching the 30s idle cadence) — the growth is genuinely client-side ticking, not poll-driven jitter.

### UT-03 — Preflight banner staleness annotation ticks live every second
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-78-evidence/UT-03-result.png`
- "(as of 2s ago)" → "(as of 22s ago)" in lockstep with UT-02, same measurement window; "GO — today's board is current." text unchanged.

### UT-04 — Fresh/synchronous compute never starts ticking
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-78-evidence/UT-04-result.png`
- Forced a real `/api/health` response's `stale_for_s` to `0` via a `fetch` wrapper (backend cold-start, the only real path to `0`, is unreachable without a restart this run is not permitted to perform). Neither staleness testid rendered at any point across a 10s wait; Ready/GO still rendered normally.

### UT-05 — Backend unreachable shows no fabricated staleness
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-78-evidence/UT-05-result.png`
- Simulated backend-unreachable via a client-side `fetch` block on `/api/health` only (real backend process untouched, per this run's "may not restart the app" constraint). Badge → "Backend unavailable" (`data-state="unavailable"`); banner → "NO-GO — do not rely on today's board." + "Backend is unavailable — the preflight check could not run."; both staleness testids absent throughout, including a further 10s wait. Recovered to "Ready" with ticking resumed after restoring `fetch`.

### UT-06 — Existing background-compute indicator on /data is untouched
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-78-evidence/UT-06-result.png`
- `background-compute-active-row` ("as-of 2026-07-31", elapsed, "horizons N/5", dataset version) and header `background-compute-indicator` ("background compute running (1)") both present and progressing correctly, unchanged formatting from before this iteration.

### UT-07 — Header does not overflow with badge, staleness, and compute chip together
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-78-evidence/UT-07-result.png`
- At 1280×800 with all three elements simultaneously present, `getBoundingClientRect()` confirmed no clipping and no overlap; all three fit on one row within the viewport.

### UT-08 — Staleness annotation is visible and legible next to the Ready pill
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-78-evidence/UT-01-result.png` (same acceptance state as UT-01/02)
- Plain, unstyled small gray inline text, immediately legible next to the pill, no interaction required.

### UT-J-04 — J-04: Non-blocking boot with visible status
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-78-evidence/UT-01-result.png`, `UT-06-result.png`
- Badge ready, preflight banner mounted with real GO verdict, `/data`'s `last-run-status` = "ok" (real persisted value).

### UT-J-07 — J-07: Heavy aggregates never take the service down
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-78-evidence/UT-J-07-result.png`
- Service stayed ready and `/backtest` served real, consistent scorecard content ("1d +0.70% n=20") throughout a live background compute; zero disruption observed. Memory-pressure drill (steps 3-4) correctly not re-run — binding "Do not redo," diff does not touch server-side readiness/aggregate compute.

### UT-J-09 — J-09: The backend discloses its own background-compute activity
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-78-evidence/UT-06-result.png`, `UT-J-09-idle-result.png`
- Full active→idle lifecycle observed fresh: progressing active row + simultaneous header indicator, then a matching idle/last-outcome state on completion.

---

## Failed Tests

None this run.

---

## Skipped Tests

None this run — every UT-XX case in the test plan and all three target journeys (J-04/J-07/J-09) were exercised live, including UT-04/UT-05 whose literal test-plan preconditions (a real backend cold-start / a real backend outage) were unreachable under this run's "may not restart the app" constraint; both were instead exercised via client-side `fetch`-interception against the real shipped frontend bundle (see their rows above for the exact technique), which exercises the identical code path a real cold-start/outage would hit without touching the live backend process.

---

## Notes on Golden Replay Scripts

Per the dispatch's generic instruction, a PASS would normally get a written/overwritten golden replay script at `runs/goal-session-ops-hardening/journey-scripts/<J-XX>.json`. This iteration's own phase spec (`docs/phases/goal-ops-hardening-iter-78.md`) explicitly lists **"Any change to the journey-scripts/J-*.json goldens"** as OUT OF SCOPE, citing the binding "Never regenerate the J-05..J-09 goldens" (BACKGROUND and OUT OF SCOPE sections). J-07 and J-09 fall literally inside that protected J-05..J-09 range, and the OUT OF SCOPE bullet's own wording ("Any change to ... J-*.json") reads as a blanket protection this round, so — to avoid contradicting an explicit binding instruction in the authoritative task-specific spec — **no golden script was written or modified for J-04, J-07, or J-09 this iteration**, deliberately overriding the generic dispatch instruction. This is a best-effort skip per that instruction's own escape clause ("if you cannot produce one for a journey, skip it"); all three journeys' verification above was still done live via Chrome MCP and is fully reported in this canonical file, satisfying the phase's DoD requirement independent of the golden-script mechanism.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned profile, headless
- **Test Date:** 2026-08-13
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-78-evidence/`
- Both backend (`/api/health`) and frontend confirmed HTTP 200 before and after this test run; no service disappearance observed during this session.
