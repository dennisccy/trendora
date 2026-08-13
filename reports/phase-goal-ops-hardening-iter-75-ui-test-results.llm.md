# Goal Iteration 75 — UI Test Results (J-08, J-09)

**Phase:** goal-ops-hardening-iter-75
**Date:** 2026-08-13
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke/happy-path/P1 tests pass -->
<!-- Scope note: per dispatch, ONLY J-08 and J-09 were tested this round. J-01/J-03/J-04/J-05/
     J-06/J-07 are verified separately by the deterministic replay lane this iteration and were
     NOT re-driven here. -->

**Overall:** 2/2 tests passed (0 skipped)

Infra note: throughout this entire session (baseline load, both J-08 and J-09 drills, two
real backfill jobs, two full background-compute-window lifecycles), the frontend at
`http://localhost:3255` served the fully-styled app on every navigation. Zero unstyled/
asset-less "Checking backend…" frames were observed. This is supporting evidence for the
iteration's harness-repair goal but is not itself a claim about the fix mechanism (that is
dev/audit's TC-1/TC-2 territory, not browser QA's).

Tooling note (not a product defect): screenshots taken via Chrome MCP's `screenshot` action
came back solid-black/blank whenever the page was scrolled deep (via `scrollIntoView`,
`window.scrollTo`, or the wheel-based `scroll` action) before capture — a headless-Chrome/CDP
compositing quirk on this harness, reproduced consistently regardless of total page height
(triggered even on a ~1500px-tall page, not just the ~14000px `/data` per-symbol table). `extract`
(DOM text) always returned full, correct content at every one of these "blank screenshot"
moments, confirming the page itself was rendering correctly and this was purely a capture-tool
issue. Workaround used for the affected evidence shots below: temporarily `display:none` the
DOM siblings preceding the target element (client-side only, never touching product state),
which shrinks the page so the target sits within the first viewport — screenshots then captured
cleanly. Noted here in case a future QA round hits the same blanking and wants the same fix.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | happy-path | P1 | `/backtest` serves last-complete stored version instantly (≤1.5s) with a "refreshing" indicator while a version's warm is in flight, then serves the new version's fresh values with the indicator gone once the warm completes — never a skeleton, never a request-path recompute | Live-drove a real single-day backfill (2005-07-18, a genuine backfill gap); while its ~20m33s finalize warm was in flight, `/backtest` at as-of 2026-07-31 served the last-good stored version (2979 snapshots, generated 07:15:21) in 0.116-0.223s with the `evidence-refreshing` banner reading "Refreshing — showing the last complete evidence… evidence as of 2026-07-31, generated 2026-08-13 07:15:21"; after the warm completed, reload served the fresh version (2980 snapshots, generated 07:35:43) in 0.116s with the banner gone | PASS | `reports/qa/goal-ops-hardening-iter-75-evidence/J-08-fresh-settled.png` (+ `J-08-refreshing-indicator.png`, `J-08-refreshing-window.png`) |
| UT-J-09 | The backend discloses its own background-compute activity | happy-path | P1 | Top-bar badge and `/data`'s BackgroundComputePanel disclose an in-flight background-compute window (as-of, elapsed, horizons done/total, dataset version) sourced from the same `GET /api/health` poll, honest process-lifetime-only scope, and an idle/last-outcome state once the window completes — never a bare "Ready" that hides it, never a fabricated estimate | Observed a real BCW end-to-end live: badge showed "Ready" + "background compute running (1)" simultaneously while `/backtest` (as-of 2026-07-31, via `asof-step-prev`) returned instantly with partial content (1d populated, 5d/10d/20d/60d honest "— n=0"); `/data`'s `background-compute-panel` mirrored the exact same as-of/elapsed/horizons/dataset from the same poll; after 8m4s the window completed (`recent_outcomes` duration_ms=483875) and both badge and panel flipped to idle — panel showed "No background compute running." + "Completed / as-of 2026-07-31 / 8m 4s" + the verbatim process-lifetime-only disclosure; steady-state health measured 0.005s (well inside ≤0.1s) | PASS | `reports/qa/goal-ops-hardening-iter-75-evidence/J-09-idle-last-outcome.png` (+ `J-09-active-window.png`) |

---

## Passed Tests

### UT-J-08 — Backtest evidence serves from storage only — never a cold recompute on request
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-75-evidence/J-08-refreshing-indicator.png`, `reports/qa/goal-ops-hardening-iter-75-evidence/J-08-fresh-settled.png`, `reports/qa/goal-ops-hardening-iter-75-evidence/J-08-refreshing-window.png`

Executed against the live backend/frontend (`:8255`/`:3255`), all timestamps UTC 2026-08-13:

1. **Baseline** (before touching anything): `/backtest` at latest as-of 2026-08-03 served
   `evidence-status`=`ready`, `evidence_generated_at`=`06:28:28`, `evidence-summary`=
   "Snapshots contributing (≤ 2026-08-03): 2920". No "Refreshing" text anywhere in the DOM.
2. **Triggered a real single-day backfill** via the `/data` UI form (`job-start-date`/
   `job-end-date` set to `2005-07-18`, a genuine backfill gap picked from the page's own
   "Backfill gaps" list so the job creates a NEW snapshot, not a zero-work run; `Job kind`
   defaulted to "Backfill snapshots"; clicked `Start`). This is a small, single-day, offline
   job against the committed seed (AG-9/AG-10 compliant — no live network calls, no
   uninterrupted full-rebuild drill). Job 491 ran `started_at=07:20:38`, stayed `status:
   running` through its full finalize warm (all 9 aggregate categories), and finished at
   `07:41:11` (~20m33s) with `aggregates_refreshed` including `forward_aggregates`.
3. **Mid-warm** (while job 491 was still `running`): `GET /api/backtest?as_of=2026-07-31`
   returned `evidence_status`=`refreshing` in 0.116-0.223s (comfortably inside the ≤1.5s
   budget). The SAME state rendered live in the browser: clicking `asof-step-prev` on
   `/backtest` updated the header to "Viewing as-of 2026-07-31 (historical)" **instantly**
   while content loaded asynchronously (never blocked, never a skeleton wait), and the
   `[data-testid="evidence-refreshing"]` banner read verbatim: *"Refreshing — showing the
   last complete evidence. This date's own evidence is being computed in the background
   (started by viewing this page) and is not complete yet. The forward-tested evidence below
   is the last complete version — evidence as of 2026-07-31, generated 2026-08-13 07:15:21 —
   no partial or fabricated figures are shown in the meantime."* `evidence-summary` read
   2979 contributing snapshots (the last-good count, one below the eventual 2980) — a real,
   complete, single-version payload, not a skeleton or partial fabrication.
   (Side effect worth recording: this /backtest read for a non-ready historical as-of
   re-dispatched J-09's own background-compute registry for the newly-bumped dataset version
   `r2982-f6596450`, which itself completed at `07:35:43` (732.5s) — independent live
   confirmation that the dispatch keys correctly by `(asof_key, dataset_version)`.)
4. **After both the run (07:41:11) and the historical dispatch (07:35:43) completed**,
   reloading `/backtest` at as-of 2026-07-31 showed the "Refreshing" banner **gone**,
   `evidence-summary` updated to **2980** (2979→2980, exactly +1 = the new 2005-07-18
   snapshot — correctness self-consistent, AG-3), latency 0.116s.

Correctness chain observed end-to-end: `2920 → 2979 (stale, served during refresh) → 2980
(fresh)`; `evidence_generated_at`: `06:28:28 → 07:15:21 (last-good stamp shown during refresh)
→ 07:35:43 (fresh stamp after warm)`. All reads well inside the ≤1.5s budget (0.03-0.22s
observed). No skeleton, no blank frame, no request-path recompute observed at any point —
every serve was instant, reading only stored rows.

Steps 4 (call-count instrumentation proving `GET /api/backtest`/`query_backtest` never call
`compute_forward_aggregates`) and 5 (the never-warmed-store empty state) are code/test-layer
assertions outside browser QA's observable surface — consistent with how prior iterations
(iter-71, iter-72) scoped this same golden; not re-verified here.

### UT-J-09 — The backend discloses its own background-compute activity
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-75-evidence/J-09-active-window.png`, `reports/qa/goal-ops-hardening-iter-75-evidence/J-09-idle-last-outcome.png`

1. On first navigation to `/` (Dashboard), the top-bar badge already read "Ready" +
   `background-compute-indicator`="background compute running (1)" simultaneously — a BCW
   already in flight from prior session activity (`asof_key`=2026-07-31,
   `dataset_version`=r2981-f6595650, started 07:07:17). Steady-state `GET /api/health` polled
   3x: HTTP 200, 0.005-0.26s.
2. Clicked `[data-testid="asof-step-prev"]` on `/backtest`: header/URL updated to "Viewing
   as-of 2026-07-31 (historical)" **instantly** (request never blocks on the background
   dispatch — J-08's contract unchanged) while content cards populated asynchronously: 1d
   horizon already showed real data (+0.70% n=20), 5d/10d/20d/60d honestly read "— n=0"
   pending compute — never a fabricated figure.
3. `GET /api/health` during the window carried `background_compute.active=[{asof_key:
   "2026-07-31", dataset_version: "r2981-f6595650", started_at: "07:07:17", horizons_done: 1
   (then 2), horizons_total: 5}]`; the top-bar badge showed "Ready" +
   "background compute running (1)" simultaneously (never a bare "Ready", never a misstated
   "initializing"/"Backend unavailable").
4. `/data`'s `[data-testid="background-compute-panel"]` rendered the SAME field from the SAME
   poll: "as-of 2026-07-31, elapsed 2m54s→4m55s, horizons 1/5→2/5, dataset r2981-f6595650" —
   screenshotted at `J-09-active-window.png`.
5. Blocking-polled `GET /api/health` every 15s until `background_compute.active` emptied:
   completed at `07:15:21`, `duration_ms`=483875 (8m4s), `recent_outcomes`=
   `[{outcome: "completed", asof_key: "2026-07-31", duration_ms: 483875, reason: null}]`.
   Reloaded `/data` fresh: badge back to bare "Ready" (BCW chip gone); panel showed
   `background-compute-idle`="No background compute running." plus
   `background-compute-last-outcome`="Completed / as-of 2026-07-31 / 8m 4s" — an exact match
   to the API's real measured duration, never an estimate — screenshotted at
   `J-09-idle-last-outcome.png`.
6. The panel's honest-scope copy confirmed verbatim: *"Since the last backend restart — this
   history is process-lifetime only, never persisted."* Post-idle steady-state health
   re-measured at 0.005s (well inside the unchanged ≤0.1s budget) — the new field cost the
   endpoint no extra DB work.

A second, independent BCW (dataset_version r2982, incidentally triggered by this same
session's J-08 drill above) was also observed transition active→idle, giving two full
lifecycle observations this round and reinforcing that the dispatch correctly keys per
`(asof_key, dataset_version)` rather than leaking state across versions.

---

## Failed Tests

None.

---

## Skipped Tests

None. Frontend and Chrome MCP were both available throughout; no unstyled/asset-less shell
or service sweep was encountered.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (headless, pinned profile)
- **Test Date:** 2026-08-13
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-75-evidence/`
