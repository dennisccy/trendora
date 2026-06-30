# goal-mcp-loop-iter-4 Frontend Handoff

**Phase:** goal-mcp-loop-iter-4
**Date:** 2026-06-30
**Agent:** developer
**Status:** complete

## What Was Built

The UI for **J-04 (regime-conditioned evidence)** — the user can now, for the first time, see a certified
decision-support edge **conditioned on and labeled with the current market regime**, reached from the
Dashboard regime panel. **No new page, no new route, no nav change** (the **Evidence** nav entry already
exists). Additive reads of the already-registered `GET /api/evidence` payload — nothing recomputed,
nothing fabricated.

### New / changed UI surfaces

1. **`/evidence` `ClaimRow` — regime label.** When a claim's cohort carries a `regime` selector, a calm
   accent **"Regime: Risk-on"** `Badge` sits in the row header beside the verdict badge, read **verbatim**
   from `claim.claim.regime`. Hidden when absent (score rows have no regime → look unchanged).
2. **`/evidence` `ClaimRow` — honest non-score title + linkback.** The signal-less Breakout-watch
   event-study claim now shows:
   - title **"Breakout-watch setup"** (prominent, not the old muted "Unmapped signal");
   - subtitle **"Out-of-sample edge in the Risk-on regime"** (honest, historical-evidence framing — never
     a buy/sell or return promise);
   - linkback **"Backs: Research event-study lab →"** → `/research/event-study` (NOT the Stocks
     leaderboard).
3. **Dashboard `RegimeGlanceCard` — Evidence affordance.** A new link **"See evidence proven in this
   regime →"** → `/evidence`, below the component-breakdown disclosure. The regime number/label
   (Risk-on, 76.05) is unchanged.

### Component patterns (reuse only — no new component or effect)

- `Badge` (`variant="accent"`) for the "Regime: <label>" header label — calm and unmissable, never hype.
- Existing `Card` / `CardContent` row layout, unchanged.
- Existing link style (`text-accent hover:underline focus-visible:ring-1`) for both the Dashboard
  affordance and the honest non-score linkback — every interactive element keeps hover/focus states.

## Files Changed

- `apps/frontend/lib/evidence.ts` — pure `regimeLabel()` + `claimSurface()` helpers (+ `ClaimSurface`).
- `apps/frontend/lib/evidence.test.ts` — 5 new unit cases for the helpers.
- `apps/frontend/app/evidence/page.tsx` — `ClaimRow` regime label + honest title/subtitle/linkback;
  removed the superseded `surfaceForSignal`.
- `apps/frontend/app/page.tsx` — `RegimeGlanceCard` Evidence affordance (+ `next/link` import).

## UI State — browser-verified (Chrome MCP, localhost:3255 → localhost:8255)

All displayed numbers were cross-checked **byte-identical to `GET /api/evidence`**.

- **Dashboard (`/`):** "Market Regime **Risk-on** **76.05**" + the **"See evidence proven in this
  regime →"** affordance (href `/evidence`). Regime figure unchanged.
- **`/evidence` — regime claim (J-04):** row 2 renders **"PASS"**, **"Breakout-watch setup"**,
  **"Regime: Risk-on"**, **"Out-of-sample edge in the Risk-on regime"**, **"Backs: Research event-study
  lab →"**, hypothesis chips (`kind=event-study`, `regime=Risk-on`, `subject=Breakout-watch`,
  `view=pooled`, …), **"PASS · holdout edge +6.12%"**, **vs SPY +6.12%**, **2026-06-30**.
- **`/evidence` — leadership row (J-05, no regression):** **"PASS"**, **"leadership_score"**,
  **"Backs: Stocks leaderboard →"**, +6.36%, 2026-06-30 — **no** regime badge, unchanged.

## States Handled

- **Regime label hidden** when `claim.regime` is absent / blank / whitespace (no empty "Regime:" chip;
  score rows unchanged) — unit-asserted.
- **Below-the-fold disclosure (iter-3 lesson):** the regime row renders **below** the leadership row.
  Browser-QA MUST **scroll the regime row into the viewport before capturing** the screenshot.
- **Backend down / empty ledger:** the page's existing honest states are untouched — "Backend
  unavailable" alert on fetch error, the empty-state card when `claims.length === 0`; every badge then
  reads "Not yet proven". `/api/evidence` still returns `{claims: [], proven_signals: {}}` (200, never
  500) for an absent/empty ledger.

## Notes for the UI pipeline (ui-impact / ui-test-designer / browser-qa-agent)

- **Client-rendered:** both pages fetch their data client-side. A root-URL 2xx alone does NOT prove the
  claims rendered — **wait for "Regime: Risk-on"** (on `/evidence`) / **"See evidence proven in this
  regime →"** (on `/`) before asserting/screenshotting.
- **The regime claim is row 2, below the fold** — scroll it into frame before the shot (iter-3 gap).
- **Bring-up:** use `scripts/start-frontend.sh` (`next start`, pre-built + stamped). If the lane shows
  stale UI, verify no orphan `next-server` owns :3255 (see the dev handoff's stale-process note).
- **Default view** = no `?as_of=` (seed frontier `2026-06-25`), ~120 leaderboard rows for J-01/J-03.
