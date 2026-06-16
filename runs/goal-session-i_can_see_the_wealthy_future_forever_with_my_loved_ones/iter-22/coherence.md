**Verdict:** COHERENCE-PASS

## Iteration 22 — Coherence Audit

Session: i_can_see_the_wealthy_future_forever_with_my_loved_ones
Iteration index: 22
Snapshot SHA: 635b5506226499d8da60b2f536279f5838b55f40
Target journeys: J-79, J-80
Depth: lean (frontend-only, zero backend diff)

---

## Step 1 — Data Contract check

### J-80 — Market regime re-display on /stocks

The `/stocks` header reads the as-of date's regime label + score from `GET /api/dashboard` via `fetchDashboard` (`apps/frontend/lib/api.ts:167`). This is the registered canonical source in the blueprint Data Contract ("Market regime score + label … served by `GET /api/dashboard`"). No new computation, no new endpoint, no new stored value. The `regimeVariant` helper extracted into `apps/frontend/lib/regime-variant.ts` is a presentation-only label→color mapping — it does not compute or recompute the regime value. It also consolidates what was previously an inline function in `apps/frontend/app/page.tsx` (removing a previous duplication, not introducing one).

### J-80 — Theme rank re-display on /stocks

The `/stocks` header reads theme rank/score from `GET /api/themes` via `fetchThemes` (`apps/frontend/lib/api.ts:451`). This is the registered canonical source in the blueprint Data Contract ("Theme score + rank … served by `GET /api/themes`"). The `rankedThemes` memo (`apps/frontend/app/stocks/page.tsx:335-337`) sorts `themes.rows` by the served `rank` field in ascending display order — a re-order of already-served values for presentation, not a re-ranking. The `themeRank` map (`apps/frontend/app/stocks/page.tsx:339-342`) is a lookup table over the same served rows. No client-side re-ranking, no new endpoint, no new computation.

### J-79 — Resolved as-of date stepping

`resolveStep` in `apps/frontend/lib/asof-step.ts` computes the step target in the UI. It operates on the `dates` array already held in the asof-provider context (derived from `GET /api/runs`) and feeds the result to the existing `setAsOf` via `useAsOfStep` (`apps/frontend/components/asof-provider.tsx:267-283`). The asof-provider remains the sole owner of the as-of value and its `?asof` URL serialization. No second date state, no new endpoint, no new stored value. This is consistent with the blueprint's "Resolved as-of date" contract row (the stepping UI is a new affordance driving the SAME single state).

### New values summary

No new canonical displayed value is introduced. All three surface additions (regime label/score on /stocks, theme rank on /stocks, ◀ ▶ / arrow-key / year-month stepping in the top bar) read from registered canonical sources.

---

## Step 2 — Information Architecture check

### J-79 — Top-bar as-of stepping (◀ ▶ buttons, checkbox, year/month dropdowns)

These controls are rendered inside `AsOfSwitcher` (`apps/frontend/components/asof-switcher.tsx`), which is mounted in the app shell at `apps/frontend/app/layout.tsx:31`. The blueprint registers J-79 as a cross-cutting affordance on the "top-bar as-of switcher / calendar popover" — the same home as J-62/J-71. The controls are visible on every page without any click (0 clicks from any surface). No navigation violation.

### J-80 — Stocks leaderboard header (regime + Top-Themes strip)

The new `RegimeThemeHeader` component is rendered inside `/stocks` (`apps/frontend/app/stocks/page.tsx:432-440`). The blueprint registers J-80's canonical home as Stocks (`/stocks`). The sidebar at `apps/frontend/components/sidebar.tsx:32` carries a direct link to `/stocks` — reachable in 1 click from any page. No navigation violation.

### No new pages or nav sections

This iteration introduces no new route, no new top-level nav section, and no parallel shell. All changes are additive to existing surfaces registered in the blueprint.

---

## Step 3 — Advisory observations

- `MONTH_NAMES` in `apps/frontend/components/asof-calendar.tsx` is a display-only array of abbreviated month labels for the year/month dropdowns. It is a presentation constant (like weekday labels), not a canonical value or magic threshold. No coherence concern.
- The `TOP_THEMES_STRIP_LIMIT = 5` constant in `apps/frontend/app/stocks/page.tsx:640` caps how many themes appear in the header strip display (mirroring the Dashboard's Top Themes slice). This is a display-capping constant, not a scoring weight or data boundary — cosmetic only. Advisory note; the blueprint does not prohibit this kind of display limit.

---

## Verdict rationale

No Part A (Data Contract) violations found: all new surfaces read from registered canonical endpoints; no value is recomputed outside its canonical module; `regimeVariant` extraction removes a previous inline duplication rather than creating one.

No Part B (Information Architecture) violations found: J-79 lands on the cross-cutting top-bar home; J-80 lands on the existing `/stocks` home; both are reachable in ≤1 click; no duplicate home or parallel shell.

Only minor advisory observations (display constants). No objective FAIL triggers.
