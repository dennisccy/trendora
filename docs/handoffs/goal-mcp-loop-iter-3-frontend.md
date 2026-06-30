# goal-mcp-loop-iter-3 Frontend Handoff

**Phase:** goal-mcp-loop-iter-3
**Date:** 2026-06-30
**Agent:** developer
**Status:** complete

## What Was Built

**No frontend source change.** `apps/frontend/**` is frozen and unchanged. The only change is to how
the frontend is **served for QA**: `scripts/start-frontend.sh` now serves a pre-built production bundle
via `next start` (deterministic, every route pre-compiled) instead of `next dev` (per-route on-demand
compile). This makes the browser-QA lane reliable so the already-shipped evidence UI can be browser-proven.

This iteration adds **no new component, page, route, nav entry, or user action.** It makes an
already-built capability **observably true in the browser**.

## Files Changed

- `scripts/start-frontend.sh` — QA serve switched from `next dev` to a pre-built `next start`
  (see the dev handoff for the full root-cause analysis). No `apps/frontend/**` file changed.

## UI State — browser-verified against the new `next start` serve (Chrome MCP, localhost:3255 → localhost:8255)

All displayed numbers were cross-checked to be **byte-identical to `GET /api/evidence`**.

- **`/stocks` (J-01 / J-03):** 120 leaderboard rows at as-of `2026-06-25`. Leadership column shows the
  green **"Proven"** chip on every row (120 total). Entry Quality and Risk show the muted
  **"Not yet proven"** chip (240 total). No "Checking backend…" and no "Backend unavailable" frame.
  Health badge reads **"Ready"**.
- **`/stocks/{ticker}` proof drill-down (J-02):** on `/stocks/MU`, the Leadership score card exposes a
  **"Why proven?"** toggle (absent on Entry Quality and Risk). Expanding it shows the OOS test
  **PASS**, holdout edge **+6.36 %**, **p ≈ 0.0005**, cohort **n = 12,297**, the **vs SPY (benchmark
  control)** excess, claim id `leadership_score`, **"registered 2026-06-30"**, and a
  **"View backing evidence row →"** link to `/evidence#signal-leadership_score`.
- **`/evidence` ledger (J-05):** renders the `leadership_score` claim row with hypothesis, PASS OOS
  verdict, SPY control, +6.36 % edge, and registration date; the **"Backs: Stocks leaderboard →"**
  linkback is present.

## States Handled (verified)

- **Populated (happy path):** Ready badge + ~120-row leaderboard + correct proven/unproven chips.
- **Honest negative states preserved:** "Checking backend…", empty leaderboard, and "Backend
  unavailable" are NOT shown when services are healthy; the J-40 honest health badge logic is unchanged
  (no fabricated "Ready" when the backend is down — `resolveApiBase` untouched).

## Notes for the UI pipeline (ui-impact / ui-test-designer / browser-qa-agent)

- **No new UI surface to map.** Reuse the iter-2 UI test plan (UT-01..UT-18) verbatim — the flows are
  identical; this iteration only made them reliably runnable.
- **The leaderboard renders client-side.** The server returns a "Checking backend…" shell (200), then
  client JS fetches `/api/stocks` and populates the 120 rows. So a root-URL 2xx alone does NOT prove
  data rendered — wait for the **"Proven"** text / a ticker row before asserting/screenshotting.
- **Default view = no `?as_of=`** (the seed frontier `2026-06-25`), which renders ~120 rows.
- Services must be brought up via `scripts/start-frontend.sh` (now `next start`) — the developer left a
  pre-built, correctly-baked `.next` so bring-up is a fast `next start` with no in-window build.
