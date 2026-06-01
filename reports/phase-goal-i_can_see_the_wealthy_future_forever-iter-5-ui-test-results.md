# Goal Iteration 5 — UI Test Results (Closure re-verify: J-06, J-11, J-15)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-5
**Date:** 2026-06-01
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- FINAL — all three target journeys captured end-to-end via the browser; the defining step of each
     was actually recorded (J-06 = both numbers legible on both pages; J-11 = the after-restart shot;
     J-15 = a real warm-load number). Run completed without the iter-4 timeout. -->

**Overall:** 3/3 target journeys PASS (J-06, J-15, J-11); 16/16 required-still-passing journeys spot-checked green (no regression — zero code changed this iteration).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-06 | Score consistency across pages (coherence) | target | P1 | NVDA's Leadership/Entry Quality/Risk (bucket+number) identical on `/stocks` and `/stocks/NVDA` | Leaderboard **E 47.48 / D 66.24 / E 33.79**; Detail **E 47.48 / D 66.24 / E 33.79** — byte-identical | PASS | `UT-J-06-leaderboard-nvda-crop.png`, `UT-J-06-detail-nvda-scores-crop.png` |
| UT-J-15 | Fast page loads from persisted snapshots | target | P1 | Warm `/stocks` load measured; values equal `/stocks/NVDA` | Warm hard reload: responseEnd **56 ms**, domInteractive **86 ms**, fully-loaded **513 ms** (122 rows server-rendered); backend `/api/stocks` **32–50 ms** — all < ~1.5 s budget | PASS | `UT-J-15-warm-load.png` |
| UT-J-11 | Watchlist persistence across REAL backend restart | target | P1 | `ANET` added; survives backend restart-by-port | Added ANET (all fields); killed backend PID **130503** by port :8835 → fresh PID **161123**; after restart `/watchlist` still shows ANET (id=1, same date_added/reason/score, form now empty) | PASS | `UT-J-11-before-restart.png`, `UT-J-11-after-restart.png` |

---

## Passed Tests

### UT-J-06 — Score consistency across pages (coherence)
**Verdict:** PASS
**Evidence (distinct, legible captures):**
- `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-5-evidence/UT-J-06-leaderboard-nvda.png` (full leaderboard, Technology+Avoid filtered, NVDA row highlighted)
- `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-5-evidence/UT-J-06-leaderboard-nvda-crop.png` (upscaled crop: column headers + NVDA row)
- `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-5-evidence/UT-J-06-detail-nvda-scores.png` (detail page `/stocks/NVDA`)
- `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-5-evidence/UT-J-06-detail-nvda-scores-crop.png` (upscaled crop: three score cards with component breakdowns)
- `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-5-evidence/UT-J-06-leaderboard-full.png` (full-page leaderboard, all rows)

**Steps & observations:**
1. Opened `/stocks` (as-of Latest, resolving to the latest snapshot **2026-05-28**). Located the NVDA row (rank 65). To make the three scores legible (not a zoomed-out thumbnail) the leaderboard was narrowed with the page's own Sector=Technology + Setup=Avoid filters and the viewport enlarged so the NVDA row renders in-frame. Leaderboard read (DOM + screenshot): **Leadership E 47.48, Entry Quality D 66.24, Risk E 33.79**, Setup **Avoid**, reason "Leadership is too weak for a setup — avoid. Top driver: moving-average stack."
2. Clicked the NVDA row → navigated to `/stocks/NVDA`. Scrolled the three score cards into view. Detail read (DOM + screenshot): **Leadership E 47.48 (/100), Entry Quality D 66.24 (/100), Risk E 33.79 (/100)**, each with its named component breakdown (e.g. Leadership: RS vs SPY·1m, RS vs SPY·3m, RS vs sector, RS vs theme).
3. **Assertion:** all three values — A–E bucket **and** 0–100 number — are **identical** across the two pages (E 47.48 / D 66.24 / E 33.79). The leaderboard and detail captures are distinct images (verified by sha256; not byte-identical — iter-3 lesson). Single source of truth holds: no per-view recomputation.

---

### UT-J-15 — Fast page loads from persisted snapshots
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-5-evidence/UT-J-15-warm-load.png` (annotated with the real measured numbers over the rendered leaderboard)

**Steps & observations:**
1. `/stocks` route was already compiled (visited multiple times during J-06) — the first/cold timing is discarded per plan.
2. Measured a **warm** load of `/stocks` (latest as-of) via the synchronous Navigation Timing API (the `eval` action does not await promises, so an in-app-nav promise timer was not reliable; a hard reload with Navigation Timing is the rigorous, reproducible alternative — and a hard reload resets the in-memory as-of to Latest, which is the date J-15 tests, per the iter-1 lesson):
   - `responseEnd` = **56 ms** (server delivered the HTML — snapshot-served)
   - `domInteractive` = **86 ms** (interactive)
   - `domContentLoaded` = **86 ms**
   - `loadEventEnd` / `domComplete` = **513 ms** (fully loaded, all **122** leaderboard rows server-rendered, 11 KB doc transfer)
   - → well under the **~1.5 s** warm-load budget; **not** borderline.
3. **Backend corroboration (snapshot-served read, no per-request recompute):** `GET /api/stocks` returned HTTP 200 in **50 / 32 / 32 ms** across three warm samples (359 KB payload); `GET /api/stocks/NVDA` in **22 ms**. A per-request scan recompute would take seconds — these millisecond reads confirm the structural guarantee in `apps/backend/app/engine/snapshot_serving.py` (reads serve the persisted immutable snapshot for the resolved as-of date).
4. **Coherence:** the leaderboard values equal the `/stocks/NVDA` detail values (NVDA E 47.48 / D 66.24 / E 33.79, established in J-06) — rendered from the same stored snapshot, no recomputation per view.

---

### UT-J-11 — Watchlist persistence across a REAL backend restart
**Verdict:** PASS
**Evidence (distinct images — sha256 differ):**
- `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-5-evidence/UT-J-11-before-restart.png` (ANET added, all fields rendered)
- `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-5-evidence/UT-J-11-after-restart.png` (after a real restart — the defining proof — banner records the PID change)

**Steps & observations:**
1. Opened `/watchlist` (empty to start — confirmed `count: 0` via `GET /api/watchlist`). Added **ANET** with reason **"ANET — strong leader, watching pullback"** via the page's Ticker/Reason form + **Add**.
2. The entry rendered immediately with **all required fields**: date-added **2026-06-01**, the reason, current **Leadership E 46.61 / Entry Quality E 57.69 / Risk E 39.62**, setup **Avoid**, **price-since-added +0.00%**, and an invalidation level **"Invalid below the 50-DMA at $148.38"**. Captured `UT-J-11-before-restart.png`. **Result flushed before the restart.**
3. Confirmed the add is **persisted to disk**, not in-memory client state: `GET /api/watchlist` (response shape `{asof_date, entries:[…]}`) returned **1 entry** — `id=1, ticker=ANET, date_added=2026-06-01T14:09:22.769416, reason="ANET — strong leader, watching pullback", leadership.score=46.61`. The DB is a file-based SQLite at `apps/backend/data/trendora.db` (not `:memory:`).
4. **Restarted the backend by PORT, bounded (iter-4 + machine-memory lesson — never a broad `pkill`):** captured the old PID (**130503**) on `:8835`, killed **only** the port-bound process with `fuser -k 8835/tcp`, waited for the port to free, relaunched detached via `setsid bash scripts/start-backend.sh` (logs `/tmp/iter5-backend.log`), and health-polled `GET /api/health` capped at 30 s → **healthy after ~3 s**. New PID **161123** (≠ 130503) ⇒ a genuine fresh process, not a reconnect.
5. Reloaded `/watchlist` (hitting the fresh backend). **ANET is still present** with the same `id=1` / `date_added` / reason / score 46.61 (verified both via `GET /api/watchlist` on the new process and in the browser). Critically, the **Add form is now empty** (placeholders showing) — so the rendered ANET row comes from the persisted DB, not leftover client form state. Captured `UT-J-11-after-restart.png`. **Result flushed.**
6. **Conclusion:** the watchlist survives a real backend process restart — persisted in SQLite, exactly what J-11 requires.

---

## Required-still-passing journeys — regression spot-check (coherence only)

Per the iteration spec this is a **verify-only** iteration with **zero source/config/frontend/schema change** (developer NO-OP), so no regression is structurally possible; a coherence spot-check (not a full re-test) was performed and is green.

- **Frontend routes** (all server-render HTTP 200): `/` (J-01), `/stocks` (J-02), `/themes` (J-03), `/sectors` (J-04), `/scanner-runs` (J-07/J-08), `/system-health` (J-09/J-10/J-19), `/methodology` (J-12), `/backtest` (J-14/J-18), `/data` (J-17). The as-of switcher (J-13) and VCP filter (J-16) live on these same already-passing surfaces.
- **Backend journey endpoints on the freshly-restarted process** (HTTP 200, non-empty payloads): `/api/dashboard` (914 B), `/api/themes` (7.9 KB), `/api/sectors` (24.8 KB), `/api/runs` (12.1 KB), `/api/system-health` (5.0 KB), `/api/methodology` (4.3 KB), `/api/backtest` (6.1 KB), `/api/data` (5.9 KB) — the data layer is intact after the restart.
- **Coherence holds:** NVDA's three scores read **identically** on `/stocks` and `/stocks/NVDA` (J-06), and the leaderboard renders from the same stored snapshot served in milliseconds (J-15) — single source of truth, no per-view/per-request recompute.

| Journey | How spot-checked | Verdict |
|---------|------------------|---------|
| J-01 Dashboard | `/` 200; `/api/dashboard` serves regime/candidates/top lists | NO-REGRESSION |
| J-02 Stocks leaderboard + filters | `/stocks` 200; Sector & Setup filters exercised during J-06 (rows narrowed correctly) | NO-REGRESSION |
| J-03 Themes | `/themes` 200; `/api/themes` 7.9 KB | NO-REGRESSION |
| J-04 Sectors | `/sectors` 200; `/api/sectors` 24.8 KB | NO-REGRESSION |
| J-05 Stock detail explainable scores | `/stocks/NVDA` rendered chart-less score cards with ≥4 named components each (seen in J-06 detail crop) | NO-REGRESSION |
| J-07 Risk-Off gating | `/scanner-runs` 200; `/api/runs` 12.1 KB | NO-REGRESSION |
| J-08 Immutable run history | `/scanner-runs` 200; `/api/runs` lists dated runs | NO-REGRESSION |
| J-09 System Health evidence | `/system-health` 200; `/api/system-health` 5.0 KB | NO-REGRESSION |
| J-10 Control-group honesty | `/system-health` 200 (same surface) | NO-REGRESSION |
| J-12 Glossary | `/methodology` 200; `/api/methodology` 4.3 KB | NO-REGRESSION |
| J-13 Global as-of switcher | as-of select present on `/stocks` & `/watchlist` (`aria-label="View as-of date"`) | NO-REGRESSION |
| J-14 Backtest scorecard | `/backtest` 200; `/api/backtest` 6.1 KB | NO-REGRESSION |
| J-16 VCP | VCP filter present on `/stocks` (`aria-label="Filter by VCP pattern"`); detail shows VCP section (NVDA: "No VCP pattern detected") | NO-REGRESSION |
| J-17 Data Manager | `/data` 200; `/api/data` 5.9 KB | NO-REGRESSION |
| J-18 One date control | `/backtest` 200; single global as-of switcher (no page-local picker observed) | NO-REGRESSION |
| J-19 Attribution | `/system-health` & `/backtest` 200 (attribution surfaces) | NO-REGRESSION |

---

## Environment

- **Frontend URL:** http://localhost:3835 (Next.js dev server; untouched by the restart)
- **Backend:** http://localhost:8835 (FastAPI/uvicorn; restarted by port during J-11: PID 130503 → 161123); provider **seed**, latest snapshot **2026-05-28**, 158 symbols
- **DB:** SQLite `apps/backend/data/trendora.db` (file-based, persistent)
- **Browser:** Chrome via Chrome MCP (`mcp__plugin_superpowers-chrome__use_browser`)
- **Test Date:** 2026-06-01
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-5-evidence/` (8 distinct PNGs)

## Notes on method (iter-3/iter-4 lessons applied)

- **Order & incremental flush (iter-4 hardening):** ran the two no-restart journeys (J-06, J-15) first and wrote each result before starting J-11; the J-11 restart was bounded (kill-by-port + 30 s health cap) so it could not hang the runner. No `exit 124` this run.
- **Legibility (iter-3):** J-06's two captures are genuinely distinct images (verified by sha256) and the scores are shown legibly (upscaled crops), not as a zoomed-out thumbnail.
- **No fabrication:** every number above is a real measurement/read — warm-load timings from the Navigation Timing API, API latencies from `curl`, the persisted ANET row from `GET /api/watchlist` before and after a real process restart. Nothing was synthesized.
- **Zero code change:** consistent with the verify-only NO-OP iteration; the value delivered is the evidence capture that was missing after the iter-4 timeout.
