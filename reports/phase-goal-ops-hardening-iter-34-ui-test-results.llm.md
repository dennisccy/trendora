# Phase goal-ops-hardening-iter-34 — UI Test Results

**Phase:** goal-ops-hardening-iter-34
**Date:** 2026-07-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | Heavy aggregates never take the service down | regression | P1 | Live full-horizon forward-aggregate warm runs in the same long-lived backend process; `GET /api/health` stays HTTP 200 throughout with no frozen window; readiness badge and `/backtest` never blank or crash; VmPeak stays under the memory cap; an induced memory-pressure abort is caught honestly with the same process still serving health + cached reads | Warm triggered live via the browser (`/backtest?asof=2026-07-15`, an uncached date under `dataset_version=r1879-f3971375`); badge showed "Ready · background compute running (1)" and the page showed the honest "Refreshing — showing the last complete evidence" state throughout the ~75 s warm, never blank/erroring; 100/100 `/api/health` polls at 1 Hz returned HTTP 200 (min 0.105 s / median 0.113 s / max 0.877 s — exceeds the ≤0.1 s budget, an honest WARN consistent with the existing documented convention, not a functional failure); warm completed (`background_compute.recent_outcomes: outcome=completed, duration_ms=74888`) and the page then rendered full evidence for 2026-07-15 ("Snapshots contributing (≤ 2026-07-15): 1873") with the badge still "Ready" and the SAME backend PID (2213604) alive throughout, no restart. Step 3 (VmPeak vs `memory_cap_mb`) and step 4 (induced-memory-pressure abort in a throwaway process) are backend/process-level actions with no browser affordance to drive — not re-executed by this browser session; they were independently verified live by the developer this iteration with log-corroborated evidence and a new passing permanent regression test (`test_ingest_finalize_memory_pressure.py`, 2 passed), documented in `reports/perf-budgets.md` ("Iteration 34 — J-07 step 2" / "step 4" sections). | PASS | `reports/qa/goal-ops-hardening-iter-34-evidence/J-07-result.png` |

---

## Passed Tests

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-34-evidence/J-07-result.png` (acceptance state), `reports/qa/goal-ops-hardening-iter-34-evidence/J-07-warming-state.png` (mid-warm honest state)

J-07 has no dedicated page (per the iter spec's Blueprint conformance note); it is proven via the global readiness badge (top bar, every page) and `/backtest`'s existing evidence display. This test drove the browser-observable surface directly and cross-checked the backend-only surface against the developer's own live evidence, per the iter-26/28 lessons (verify from logs/artifacts, not narrative).

**Step 1 — trigger the warm, in one long-lived process:**
- Navigated to `/` — confirmed `GET /api/health` had no active background compute yet.
- Issued `GET /api/backtest?as_of=2026-07-15` (a date confirmed not yet cached under the live `dataset_version=r1879-f3971375`) — this dispatched the SAME background full-5-horizon forward-aggregate warm the dev's own iter-32/iter-34 measurements use (`background_compute.active`: `asof_key=2026-07-15, horizons_total=5`).
- Navigated the browser to `/backtest?asof=2026-07-15` while the warm was in flight: the top-bar badge read "Ready" + "background compute running (1)" (never "crashed"/blank), and the page body showed the honest disclosure banner — *"Refreshing — showing the last complete evidence… This date's own evidence is being computed in the background… Reload this page shortly…"* — while still rendering the full prior-date (2026-07-14) evidence tables, never a blank or frozen frame. Screenshot: `J-07-warming-state.png`.
- All of this ran in the SAME already-running backend process (PID 2213604, confirmed alive before, during, and after via `ps`).

**Step 2 — poll `GET /api/health` at 1 Hz throughout:**
- Ran a 100-poll, 1 Hz `curl -s -o /dev/null -w "%{http_code},%{time_total}"` loop spanning the full warm (warm ran 74.888 s per `background_compute.recent_outcomes`).
- Result: **100/100 HTTP 200**, 0 failures. Latency: min 0.105 s, median 0.113 s, mean 0.130 s, max 0.877 s. No poll gap indicated a frozen/unresponsive window.
- Every poll exceeded the committed `<=0.1 s` budget — an honest **WARN**, consistent with the SAME "PASS at rest, WARN under load" convention already on record in `reports/perf-budgets.md` for this endpoint (this run added further concurrent load: the warm itself, plus this session's own browser/page-load traffic). The budget line was NOT amended (binding "Do not redo" — not this agent's file to edit in any case).
- Reloaded `/backtest?asof=2026-07-15` after the warm completed: the "Refreshing" banner was gone, and the page showed fresh 2026-07-15 evidence — "Snapshots contributing (≤ 2026-07-15): 1873" (up from 1859 pre-warm), confirming the warm's result was actually served, not silently dropped. Badge still read "Ready". Screenshot (acceptance state): `J-07-result.png`.
- `logs/backend.log`'s tail for this session's requests shows the exact `GET /api/backtest?as_of=2026-07-15` / dashboard/themes/sectors/stocks calls this browser session issued, all `200 OK`, with zero `error`/`exception`/`traceback` lines in that window — corroborating the browser observation from the log, not narrative alone.

**Step 3 — VmPeak margin (not browser-drivable):**
- A browser cannot read backend process memory. Not re-executed here. Independently confirmed by the developer's live iter-32/iter-34 measurement (`reports/perf-budgets.md`): `VmPeak` plateaued at 2,691,732 kB against a `memory_cap_mb=6144` (6,291,456 kB) cap — ample margin, zero measurable growth from the warm itself.

**Step 4 — induced memory-pressure abort in a throwaway process (not browser-drivable):**
- Requires launching a separate throwaway backend process via `scripts/start-backend.sh` with a tightened `server.memory_cap_mb` override — outside what browser automation can perform. Not re-executed here.
- Independently confirmed by the developer this iteration: a genuine (non-monkeypatched) `MemoryError` was caught by the existing `except MemoryError` branch inside `_refresh_ingest_aggregates`'s `forward_aggregates` loop (`memory_cap_mb=970`, throwaway PID 2072993); `GET /api/health` kept returning 200 on the SAME PID immediately after and repeatedly thereafter, no restart; a previously-cached `GET /api/backtest` read served its pre-seeded stored value untouched. Corroborated against `logs/backend.log` (verbatim excerpt saved at `runs/goal-ops-hardening-iter-34/mem-drill/pass6/drill-log-excerpt.txt`) per the iter-26/28 lesson. A new permanent regression test (`apps/backend/tests/test_ingest_finalize_memory_pressure.py`) reproduces this mechanism plus a control case: **2 passed** (190.98 s). Full write-up: `reports/perf-budgets.md`, "Iteration 34 — J-07 step 4".

**Anti-goal check (AG-8):** no unbounded whole-table load was observed or reintroduced; the warm ran bounded/streamed as documented, and the page degraded honestly (never a blank application-error page) while its own evidence was still computing.

---

## Failed Tests

None.

---

## Skipped Tests

None. J-01, J-03, J-04, J-05, J-06, J-08, J-09 were explicitly excluded from this run's scope per the dispatch (verified separately by deterministic golden replay) — not tested and not recorded as SKIPPED rows here.

---

## Golden Replay Script

Written to `runs/goal-session-ops-hardening/journey-scripts/J-07.json` (lint-checked with
`demo_runner.py --mode lint`, passes):
1. `goto /` → expect text "Ready" (readiness badge truthful at rest).
2. `goto /backtest?asof=2026-07-15` → expect text "Snapshots contributing (≤ 2026-07-15): 1873" (a
   real post-load data value tied to this journey's own historical as-of, now persisted — stable across
   future iterations unless a future backfill adds new snapshots dated on/before 2026-07-15, which is not
   expected of ops-hardening iterations targeting recent/latest data). This also replaces the previous
   script's `n=8869` literal, which was tied to the "latest" as-of and drifts as new trading days roll in
   (a known carried framework-hygiene item per the iter-34 spec's OUT OF SCOPE list).

Note: the golden replay intentionally does NOT re-trigger a fresh warm or re-poll health latency each
run (the `goto`/`click`/`fill` action set has no HTTP-latency-polling primitive, and 2026-07-15 is now
permanently cached under this `dataset_version`, so replaying it will serve instantly). It regression-checks
that the badge and `/backtest` page still render truthfully for this journey's scenario; it is not a
substitute for re-running the live warm-and-poll measurement, which is a backend/perf-budgets concern
outside browser QA's replay contract.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned profile
- **Test Date:** 2026-07-30
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-34-evidence/`
- **Backend process:** PID 2213604, confirmed alive unchanged before/during/after the test (no restart)
