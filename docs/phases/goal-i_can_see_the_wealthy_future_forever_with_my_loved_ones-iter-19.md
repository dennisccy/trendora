# Goal Iteration 19 — No as-of date-flash (synchronous URL hydration) + dashboard indexes default to All

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 19
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-73, J-78
- **Required-still-passing journeys:** J-18, J-43, J-50, J-13, J-44, J-49, J-42
- **Anti-goal reminders (verbatim from `docs/goal.md`, critical for this iteration):**
  - **Exactly one date selector** — "the global as-of control drives every date-scoped page; `?asof` (J-43) is its SERIALIZATION, never a second state ... never a second/page-local date state." J-73 changes only *when* the one state is read (synchronously from the URL on first mount instead of after the async run-list fetch); it MUST NOT introduce a second or page-local date state.
  - **No magic numbers** — "weights/thresholds/edges/universe/themes/providers/chunking/startup/range-presets/glossary ... from `config.yaml`/design tokens." J-78 is a config-only default change (`index_chart.default_range` `6M` → `all`) — NO hardcoded range literal in code, no second code path.
  - **No recompute in the read path** — reads serve persisted-snapshot values; J-78 changes the default display window only (the indexes endpoint still serves full-history regardless of as-of per J-49 — clamp optional for this surface); J-73 changes no served value.
  - **No lookahead** — as-of-D uses bars ≤ D; J-73's earlier (synchronous) resolution of the as-of date must still resolve to a valid stored snapshot date; an invalid `?asof` still degrades to latest (J-43).
  - **No fabricated data** — an invalid/unknown `?asof` must not render a fabricated date; it degrades to latest and the stale param is stripped (J-43 unchanged).

## GOAL

Arriving at any historical `?asof=D` URL (in-app nav, deep link, reload, new tab) renders the destination's data at D from first paint with no latest→D flash, and the Dashboard major-indexes chart defaults to the full period (All) on a fresh load.

## BACKGROUND

J-74 and J-76 went live-green in iter-18 (CONTINUE); five non-data-dependent Must-haves of the J-72..J-78 extension remain (J-72, J-73, J-75, J-77, J-78). Per the iter-18 evaluator's standing plan, iter-19 is **lean**: J-78 (a one-line `config.yaml` default-range change, the lowest-risk remaining item) bundled with J-73 (synchronous `?asof` URL hydration). J-73 touches `asof-provider.tsx` — the J-18/J-43/J-50 single-global-as-of invariant core — so it is planned carefully: the asof-provider remains the SOLE `?asof` owner, the fix only moves the *timing* of the one state's read to first mount, and no second/page-local date state is introduced. The backend cluster (J-72 / J-75 / J-77) is deferred to later full-depth iterations where the audit step earns its cost.

Source verified before planning (so the dev scope is precise, not exploratory):
- `apps/backend/config.yaml:305` reads `default_range: "6M"`; the valid preset keys are `3M / 6M / 1Y / all` (lines 301-304, `all` is lowercase). `apps/backend/app/engine/indexes.py:50` falls back to `cfg.index_chart.default_range` when no range is requested, and `config.py:137` already validates `default_range` against the preset keys — so J-78 is the single value edit `"6M"` → `"all"`, no code change.
- `apps/frontend/components/major-indexes-card.tsx:40` initializes `rangeKey = null` ("the server's config default"), calls `fetchIndexes(rangeKey ?? undefined, ...)` (line 53, sends no `range`), and reads the active preset back from `indexes.range.key` (line 87). There is NO hardcoded "6M" in the frontend — so J-78 needs ONLY the config change; the frontend will show "All" active on a fresh load automatically.
- `apps/frontend/components/asof-provider.tsx` today initializes `asOf` to `null` (`useState(null)`, line 60) and restores `?asof` only in an effect gated on `ready` (lines 157-171), i.e. AFTER the `GET /api/runs` fetch resolves — this is the exact cause of the latest→D flash: a `?asof=D` URL first renders at latest, then re-fetches at D once the run list arrives. J-73's fix: hydrate `asOf` synchronously from the URL on first mount (a lazy `useState` initializer reading the `?asof` param) so the first data fetch is already at D, while keeping the run-list result as a *validation/degrade* step (unknown/invalid/now-latest → strip to latest, exactly as J-43 does today).

Lessons applied this iteration (from the session lessons ledger):
- **iter-1 lesson (critical for J-73):** a Next.js App Router URL↔state sync needs `searchParams` (its stable `.toString()` key) in the serialize effect's dependency array — the iter-2 `searchKey` fix at `asof-provider.tsx:185-194` is load-bearing. Do NOT remove or weaken it; any rework must keep the deep-link restore from racing the serializer (HTTP-200 `?asof` smoke tests cannot catch this — assert the post-hydration `window.location.href`).
- **iter-1 lesson:** ESLint is NOT installed in `apps/frontend`; the frontend gate is `tsc --noEmit` (do not write an `npm run lint` DoD line).
- **iter-16 lesson (critical for J-73):** the cheap decisive check on this surface is static, not visual — `grep` the diff for any `window`/`document.addEventListener` keydown (must be none) and confirm `asof-provider.tsx` adds NO new `useState` holding a date value (a lazy initializer on the EXISTING `asOf` state is fine; a second date state is a violation).
- **iter-18 / recurring heatmap lesson:** not in this iteration's primary scope, but if QA captures the `/data` availability heatmap as a regression smoke, scroll the colored grid into the viewport and capture full-VIEWPORT — a coverage-table or blank dark frame is a rejected capture.

## IN SCOPE

### Backend
- [ ] **J-78:** Change `apps/backend/config.yaml` `index_chart.default_range` from `"6M"` to `"all"` (a valid preset key, line 304). No Python code change — `indexes.py:50` already resolves the default from this field and `config.py:137` already validates it. This is the only backend edit.

### Frontend
- [ ] **J-73:** In `apps/frontend/components/asof-provider.tsx`, hydrate the single global as-of state synchronously from the `?asof` URL param on FIRST MOUNT — replace the unconditional `useState<string | null>(null)` initial for `asOf` with a lazy initializer that reads `?asof` from the current URL (a valid ISO date param → that date; absent/malformed → null/latest) so a date-scoped page's first fetch is already at D. The asof-provider stays the SOLE reader/writer of `?asof` (one owner). NO second/page-local date state, NO new `useState` holding a date.
- [ ] **J-73:** Keep the existing run-list `ready` step as a VALIDATION/degrade pass — once `GET /api/runs` resolves, if the synchronously-hydrated `asOf` is not a known historical run date (unknown date, or it equals latest), degrade to latest and strip the stale `?asof` param via the existing `writeAsofParam` path (J-43 behaviour unchanged: invalid→latest, no fabricated date). Preserve the iter-2 `searchKey` dependency fix (lines 185-194) and the single-restore `restored` ref guard so the deep-link read never races the serializer.
- [ ] **J-73:** Confirm `useAsOfHref` (J-50) and the `AsOfUrlSync` serialize effect continue to behave identically — synchronous hydration must not double-stamp, strip, or scroll-jump the URL on first paint, and at latest the URL stays date-free.

### New user-facing capability
- Opening a `?asof=D` historical URL (deep link, reload, new tab/middle-click, or in-app nav from another historical page) shows the destination's data at D immediately, with no transient flash of the latest-date values.
- A fresh Dashboard load shows the major-indexes chart over the full available history (All) by default.

### New information displayed
- None new. J-73 changes *when* (first paint vs after a fetch) already-served D-dated values appear; J-78 changes the *default window* of the already-served full-history index series. No new value, no new column, no new endpoint.

### New user actions
- None. The as-of switcher, calendar popover, keyboard stepping (J-62/J-71), the indexes range-preset selector, and its enable/persistence toggle are all unchanged.

### UI surface changes
- Dashboard `/` major-indexes & regime card: default range preset reads "All" on a fresh load (was 6M). All presets (3M / 6M / 1Y / All) still switch the view.
- No visual surface change for J-73 — it is the ABSENCE of a flash; the historical badge, dated values, and `?asof` URL all look identical once settled, just correct from first paint.

### Product surface delta
- The historical as-of experience becomes flicker-free across every arrival path; the dashboard market-context chart opens on full history by default. No nav, page, or contract change.

### Blueprint conformance
- No new surfaces. J-73 refines the existing cross-cutting **as-of switcher** behaviour (top bar; `asof-provider.tsx`) — registered under "Resolved as-of date + available dates (ONE global state)" in the Data Contract and the J-13/J-43/J-50/J-62/J-71 cross-cutting row in the IA. J-78 amends the existing **Dashboard `/`** major-indexes card — registered under "Normalized index display series" / the J-44/J-49 IA rows. Both surfaces already exist in `blueprint.md`; this iteration adds amendment notes only (additive edits, no nav-skeleton change).

### Data-contract additions
- None. No new displayed value. J-73 reads the already-registered single global as-of state (no second computation, no second endpoint); J-78 reads the already-registered normalized-index-series endpoint with a different default `range` param (no recompute). Blueprint updated with J-73/J-78 amendment notes on the two existing rows.

## OUT OF SCOPE

- J-72 (Research perf/cache), J-75 (forward-return columns 1/5/10/20/60d on /stocks + detail), J-77 (regime × setup × pattern ranked study) — deferred to later FULL-depth iterations (backend, with hard byte-identity / no-lookahead / count-coherence gates and the audit step).
- Any change to the as-of switcher UI, calendar popover, keyboard stepping, the indexes endpoint's served data, regime bands, or the chart's enable/persistence toggle.
- Any new `useState` holding a date, any `window`/`document` keydown or scroll listener, any second date-state path (would violate the critical "Exactly one date selector" anti-goal).
- Any backend Python change for J-78 (config-value edit only) and any new endpoint or stored column.
- J-22/J-23/J-24 (data-walled, non-halting, NA) — unchanged.

## DEFINITION OF DONE

- [ ] Target journeys J-73, J-78 pass via browser-qa-agent with distinct, full-viewport, md5-verified captures (one per claimed surface).
- [ ] J-73 verified with the post-hydration `window.location.href` assertion (NOT just HTTP-200) AND a no-flash observation on a historical `?asof=D` arrival: the first rendered data is at D, never a latest→D swap (deep link + reload + new tab + in-app nav from a historical page). At latest, the latest view renders with no flash; an invalid `?asof` degrades to latest without flashing a wrong date.
- [ ] J-78 verified: a fresh Dashboard load shows the major-indexes range selector with "All" active and the chart over full history; 3M / 6M / 1Y / All all still switch.
- [ ] Required-still-passing journeys remain green: J-18 (exactly one date selector — re-smoke the single-control invariant), J-43 (`?asof` serialization + invalid→latest degrade), J-50 (`?asof` embedded in in-app hrefs / new tabs), J-13 (browse a past date), J-44 + J-49 (indexes & regime card full history + as-of marker), J-42 (yyyy-MM-dd dates).
- [ ] No anti-goal violation introduced (static check: zero new date `useState`, zero `window`/`document` keydown listener; the asof-provider remains the sole `?asof` owner; no hardcoded range literal in code).
- [ ] `tsc --noEmit` is clean (the frontend gate — ESLint is not installed; do NOT add a lint DoD line).
- [ ] Backend unit tests pass for the config validation path (`index_chart.default_range = "all"` is accepted and resolves to the all-history preset); no regressions in the indexes engine / config suite.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-19-dev.md`.

## TESTING REQUIREMENTS

- **Browser (by ID):**
  - J-73 — historical `?asof=D` arrival via (a) direct deep link, (b) reload of that URL, (c) new tab / middle-click, (d) in-app nav from another historical page: first paint at D, NO latest→D flash; assert post-hydration `window.location.href` carries `?asof=D`. Latest URL → latest view, no flash. Invalid `?asof` → degrades to latest, stale param stripped, no wrong-date flash.
  - J-78 — fresh Dashboard `/` load: major-indexes selector defaults to "All", chart spans full history; switch through 3M / 6M / 1Y / All and confirm each re-renders.
  - Regression smoke: J-18, J-43, J-50, J-13, J-44, J-49, J-42 (the single-date-control invariant + `?asof` durability + dates formatting must stay green after the asof-provider edit).
- **Unit/integration:**
  - Backend: a config test confirms `index_chart.default_range = "all"` validates and `indexes.py` resolves the default to the all-history preset (`days = null`); existing indexes-engine + config-validation tests stay green.
  - Frontend: `tsc --noEmit` clean; if the harness supports it, a test/assertion that the synchronous hydration sets `asOf` from a `?asof=D` URL on first render (before any fetch resolves) and that an invalid param yields `null`.
- **Error cases:**
  - Invalid / malformed `?asof` (non-ISO, or a date with no run) → degrades to latest, param stripped, no fabricated/flashed date.
  - A `?asof` equal to the latest date → normalized to the clean latest view (date-free URL), no historical badge.
  - `index_chart.default_range` set to a non-preset value → still rejected by the existing `config.py:137` validator (the no-magic-number guard is intact).

## NOTES

- **Critical-invariant iteration.** J-73 edits the J-18/J-43/J-50 core (`asof-provider.tsx`). The whole point is to change ONLY the *timing* of the one global state's read (synchronous URL hydration on first mount) — not to add a second state. The reviewer/coherence-auditor should confirm: (1) the asof-provider is still the sole `?asof` reader/writer; (2) no new `useState` holds a date value (a lazy initializer on the existing `asOf` state is the intended shape); (3) no `window`/`document` keydown or scroll listener was added; (4) the iter-2 `searchKey` dependency fix and the `restored` single-restore guard are preserved so the deep-link restore never races the serializer; (5) at latest the URL stays date-free and the invalid→latest degrade (J-43) is unchanged.
- **J-78 is the lowest-risk leg:** a single config value edit (`config.yaml:305` `"6M"` → `"all"`). It is a valid preset key (line 304) already accepted by the `config.py` validator, resolved by `indexes.py:50`, and surfaced by the frontend with no code change (`major-indexes-card.tsx` reads `null ⇒ server default` and the active key from the payload). Verify NO hardcoded "6M"/range literal sneaks into code (no-magic-number anti-goal).
- Per the iter-18 evaluator: after J-73/J-78 close green, the remaining backend cluster J-72 / J-75 / J-77 goes at FULL depth (byte-identity, no-lookahead/no-recompute, and count-coherence gates respectively).
- J-22/J-23/J-24 stay honestly blocked-NA (data-walled, non-halting per goal.md "Data-dependent journeys (non-halting)") — they neither halt the loop nor block this iteration.
