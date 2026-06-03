# goal-i_can_see_the_wealthy_future_forever-iter-15 Execution Plan

**Target journey:** J-31 — synthesis capstone: travel lab evidence → leaderboard names → Stock Detail.
**Goal alignment:** J-31 is goal journey #31 and the LAST buildable journey. It rides only existing approved homes (`/research`, `/stocks`, `/stocks/[ticker]`). **Frontend-only — NO backend change, NO new computation, NO new endpoint/route/nav entry, NO blueprint re-approval.** The blueprint is ALREADY updated for iter-15 (nav note line 84 + the J-31 home row line 117 + the "no new Data-Contract value" note) — the dev does NOT author it; the coherence-auditor verifies the diff against it.
**Grounded this pass (source-verified):** `/stocks` filters (`sector`/`setup`/`pattern`) are `useState`-only with no URL hooks; `useAsOf()` is the sole date source; `fetchStocks` effect is keyed to `[asOf]` only; `pattern` encodes as `<key>__only`/`<key>__none`, `setup` is the status string, `sector` is a sector string (sentinel `__all__`). `/research`'s `EventStudyLab` resolves `data.subject = {key, label, kind: "setup"|"pattern"}` and already discriminates on `kind`. `useSearchParams`/`useRouter`/`Suspense` appear **nowhere** in the frontend yet (grep-confirmed) → introducing `useSearchParams` REQUIRES a new `<Suspense>` boundary (see risks).

## What to Build

Two frontend edits in two files. No backend, no config, no new dependency.

- **A. Deep-linkable Stock Leaderboard filters — `apps/frontend/app/stocks/page.tsx`.**
  - **Init-from-URL:** seed the existing `sector`/`setup`/`pattern` `useState` from `useSearchParams()` on mount (lazy initializer — read once). Encodings are the EXISTING ones verbatim: `?sector=Energy`, `?setup=Breakout-watch`, `?pattern=pullback_to_rising_dma__only`. Absent ⇒ `__all__`.
  - **Reflect-to-URL:** when a filter changes, push the new query string with `router.replace(pathname + "?" + params, { scroll: false })` (shallow, shareable, no scroll jump). Omit a param when its value is `__all__` (clean URLs).
  - **No refetch (J-15, critical):** the `fetchStocks(asOf)` effect dependency array stays `[asOf]` ONLY. Filter changes must NOT refetch. Filtering remains the existing pure client-side `visible` memo over server rows — never re-sorts or recomputes a score/flag.
  - **Unrecognized/absent param → `__all__` fallback** (no crash, no fabricated filter). Strictly validate `pattern` against the `PATTERNS` registry (`<key>` ∈ registry AND mode ∈ {`only`,`none`}, else `__all__`); `sector`/`setup` accepted verbatim — an unmatched value harmlessly renders the EXISTING honest empty-state (acceptable per J-02/J-16), nothing is fabricated.
  - **`<Suspense>`:** wrap the `useSearchParams`-consuming body in a `<Suspense fallback={<StocksSkeleton/>}>` boundary (Next 15 App-Router build requirement — see risks). Recommended: keep the default export a thin wrapper that renders `<Suspense><StocksInner/></Suspense>`; move today's body into `StocksInner`.

- **B. Lab → leaderboard cross-link — `apps/frontend/app/research/page.tsx` (`EventStudyLab`).**
  - For the resolved `data.subject`, render a `next/link` `Link`: **"View the names expressing this on the leaderboard →"**, mapped from `subject.kind` (config/payload-driven — NO hard-coded subject↔filter table):
    - `kind === "pattern"` → `/stocks?pattern=${encodeURIComponent(subject.key)}__only`
    - `kind === "setup"`  → `/stocks?setup=${encodeURIComponent(subject.key)}`
  - **Placement:** adjacent to the `SubjectSelector` / subject meta line (where `data` is in scope), so it renders whenever a subject resolves — INCLUDING low-sample NA subjects (the "names expressing this today" set is independent of the historical event-study sample). Style as the existing accent link (`text-accent hover:underline`, focus-visible ring).
  - **Honest copy:** the link points to "the names flagged for this pattern / classified as this setup **at the current as-of date**" — it claims no count it cannot prove. Do NOT add a fetch to compute a count.
  - **Optional (nice-to-have, only if trivially tight):** a one-line synthesis caption ("Factor Lab evidence → an aligned setup/pattern's event study → the names expressing it on the leaderboard → Stock Detail"). No new component, no new data. Skip if it bloats the diff.

### Out of scope (STOP and flag if it seems needed) — verbatim from spec
- **Any backend change** — no new endpoint, query param, model column, or computation. If a backend change seems unavoidable, STOP and flag in the handoff (do NOT add a second computation/serving path — that is exactly the drift the coherence-auditor hard-fails).
- A **"filter by factor decile"** leaderboard control (factor is expressed through its aligned setup/pattern — existing filters).
- **J-24** chart timeframe selector / any intraday data, **J-22 / J-23** — externally Yahoo-429 data-walled; do NOT build, do NOT autonomously retry. J-31 step 4 "across timeframes" is scoped to the canonical **daily** timeframe (J-20), intraday honestly coverage-limited.
- Any change to the labs' analytics, scoring/forward-testing engines, the as-of provider, or the date control. No localStorage/cookie persistence (URL only).

## Agents Required
- developer: yes — frontend-only. (A) URL-back the `/stocks` filters (init-from-URL + reflect-to-URL + `<Suspense>`); (B) add the `kind`-driven cross-link to `/research`'s `EventStudyLab`. No backend work.
- backend-data: no — no endpoint/model/config/computation touched.
- frontend-ux: yes — both edits are user-facing navigation/affordance changes.

## Frontend Present
yes

Frontend Present: yes

## Files to Create/Modify
- `apps/frontend/app/stocks/page.tsx` — init the 3 filters from `useSearchParams`; reflect changes via `router.replace(..., {scroll:false})`; `<Suspense>` boundary (wrapper + `StocksInner`). Fetch effect stays keyed to `[asOf]` only. No table/column/score change.
- `apps/frontend/app/research/page.tsx` — add the `kind`-driven `<Link>` cross-link in `EventStudyLab` (and optional one-line caption). No analytics change.
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-15-dev.md` — dev handoff (What Built / Files / Tests Run incl. `npm run build` + one backend-suite confirmation / Known Issues / Next).
- **Do NOT author:** `blueprint.md` (already updated by the decomposer); any backend file; any `config.yaml`.
- (Optional) `apps/frontend/lib/` only if a tiny pure encode/decode helper + a frontend unit test is added (see Key Test Scenarios) — must assert exact values; not required.

## UI Evolution
- **New user-facing capability:** travel the full evidence→action path inside the product — from "which factor/volatility measure/pattern drives positive risk-adjusted forward return (with n + regime context)" in the Research labs, to "which names express it now" on the pre-filtered Stock Leaderboard (one click), to a single name's Stock Detail (scores + pattern badge + invalidation + daily chart) — no hand-copied ticker, no recomputed/fabricated number.
- **New information displayed:** none canonical. The only new affordances are the **cross-link** on the Setup & Pattern Lab and the **shareable/deep-linkable URL state** of the leaderboard filters (a re-display control over the SAME stored rows).
- **New user actions:** click "View the names expressing this on the leaderboard →" (lands on `/stocks` pre-filtered); open `/stocks?pattern=…` / `?setup=…` directly (shareable); change a filter and see it reflected in the URL.
- **UI surface changes:** `/research` `EventStudyLab` gains one cross-link (+ optional caption); `/stocks` filter state becomes URL-backed. No new page/route.
- **Navigation changes:** none in the sidebar (NO nav-skeleton change → NO `blueprint.reapproval-requested` marker). J-31's "home" is the cross-page travel across existing homes.

## Visual Requirements
- **Component patterns:** reuse `next/link` `Link` (already imported in `stocks/page.tsx`; add to `research/page.tsx`) and the existing `Select`/`PanelTitle` patterns — no new component library surface. The cross-link is a plain accent link, not a button.
- **Layout:** additive — one link line inside the existing `EventStudyLab` card; the `/stocks` filter row is visually unchanged.
- **Key visual effects:** palette tokens only (`text-accent` for the link; `hover:underline`; `focus-visible:ring-accent`). No new colors/spacing/type. Numbers stay `tabular-nums`.
- **States to handle:** cross-link renders whenever a subject resolves (incl. low-sample NA subjects); a deep-link to a zero-match filter shows the EXISTING honest empty-state (no fabricated row); unrecognized param → `__all__`; loading/error states on `/stocks` unchanged.

## Key Test Scenarios
**Browser (the J-31 defining flow — capture the FULL travel, not isolated renders; iter-4 lesson):**
1. `/research` Factor Lab — pick a factor (e.g. volatility-family `vcp_contraction` or `RS-vs-SPY-3m`): decile mean fwd return + downside risk-adjusted column + rank-IC + n (J-25/J-30); by-regime split renders per-regime spread + n (J-27).
2. Same page Setup & Pattern Lab — select a **data-rich** aligned subject (per iter-14 handoff: pattern `pullback_to_rising_dma` ~163 occ, or setup `Breakout-watch` ~99; avoid `vcp`/`Actionable`/`Pullback-watch` which are honest NA) → event study renders distribution / expectancy / MAE-MFE / best-exit-horizon / by-regime / by-sector with n + honest NA (J-29).
3. Click **"View the names expressing this on the leaderboard →"**.
4. **Land on `/stocks` pre-filtered** — DOM-assert the active filter control reflects the subject (Pattern = "Pullback only" / Setup = "Breakout-watch") AND the `visible / total` count is the narrowed subset; pick a subject with ≥1 expressing name today so step 5 lands on a real row.
5. Click a row → `/stocks/[ticker]` → confirm the subject's badge (pattern pivot/invalidation, or setup status) + the three A–E scores + invalidation render, byte-consistent with the leaderboard row (J-06), on the daily chart (J-20).
- **J-18 cross-check (PRINCIPAL RISK):** with a filter deep-linked, toggle the global as-of switcher → page re-points by DATE while the filter stays intact and **NO `as_of`/date param appears in any leaderboard fetch**; confirm exactly one date control. Ground on DISTINCT screenshots + a network/DOM assertion (iter-6 lesson; serialize Chrome access between `qa` and `browser-qa-agent`, de-dup evidence by sha256). The iter-1 lesson (the only historical anti-goal violation was a second date control) makes this the seam to verify in source: no `?as_of`/date query param introduced; `useAsOf()` remains the sole date source.
- **Shareable-link check:** open `/stocks?pattern=<key>__only` (and `?setup=<status>`) directly in a fresh nav → filter pre-applied. (In-app nav carries the global as-of; the as-of resets on hard reload per iter-1 lesson — drive the travel by CLICKS, not hard reloads.)
- **Honesty/edge cases:** unrecognized/empty filter param → `__all__` (no crash); a filter matching zero rows → existing honest empty-state (no fabricated row); low-sample lab cells stay NA + n along the travel; intraday timeframe honestly absent (daily only), never faked.

**Build / suite:**
- `cd apps/frontend && npm run build` — compiles + typechecks (the `<Suspense>` boundary MUST make the production build pass; a missing boundary fails the build).
- Backend suite stays green: no backend change → run once to confirm no incidental breakage (`cd apps/backend && .venv/bin/python -m pytest tests/ -q`). Note: full suite ~14 min (MEMORY: backend-test-suite-runtime) — run ONCE, do not parallelize.
- **Optional unit:** if a pure param encode/decode helper is added, assert exact mapping (e.g. pattern subject `vcp` → `/stocks?pattern=vcp__only`; setup `Breakout-watch` → `/stocks?setup=Breakout-watch`). Not required (build + browser flow cover correctness).

## Definition of Done (mirrors the spec)
- J-31 passes via browser-qa-agent through the FULL cross-page travel (lab evidence → cross-link → pre-filtered leaderboard with DOM-asserted active filter + narrowed count → a real row opened on Stock Detail with badge + 3 scores + invalidation).
- Required-still-passing journeys green — especially **J-18** (filter-only URL, one date control, no extra date param on as-of toggle), **J-02** (dropdown filters work + sync to URL), **J-15** (warm load unchanged — no new fetch), **J-06** (detail scores byte-identical to leaderboard), **J-25/J-27/J-29/J-30** (labs still render; cross-link is additive).
- No anti-goal violation — verified IN SOURCE: diff touches only `stocks/page.tsx` + `research/page.tsx` (+ the in-file `<Suspense>` wrapper); no `as_of`/date query param; no new endpoint/computation; cross-link mapping is `kind`/registry-driven (no hard-coded table).
- Frontend build + typecheck pass; backend suite green; dev handoff written.

## Risks & Notes (read before coding)
1. **`<Suspense>` is mandatory, not optional.** Next 15 App Router throws a build error ("useSearchParams() should be wrapped in a suspense boundary") if `useSearchParams` is used without one. No Suspense pattern exists in this codebase yet — the dev introduces the first. Verify with `npm run build` (dev mode may not surface it).
2. **State↔URL loop hazard.** Initialize state from the URL ONCE (lazy `useState` initializer reading `searchParams.get(...)`); reflect changes OUT via `router.replace`. Do NOT also drive state FROM a `searchParams` effect that itself fires on the `router.replace` — that risks a render loop. Reflecting-out only (init-once + replace-on-change) satisfies the spec's two required behaviors (open-pre-filtered, change-reflected-in-URL); reacting to browser back/forward is an optional nicety, not required.
3. **No date param, ever (J-18).** The only URL params are `sector`/`setup`/`pattern`. The as-of date stays in the global `asof-provider`. This is the one iter where a second date state could regress.
4. **Depth = full** per the iter-14 evaluator: J-31 is the capstone whose purpose is cross-surface coherence, so the full pipeline runs (coherence-auditor on the read-only/one-date-control seams; ux-regression on cross-link discoverability; closure gate on the cross-page travel) — chosen for verification rigor, not because a functional gap requires it.
5. **Forward outlook (not this iter's work):** after J-31 lands green, GOAL_ACHIEVED is NOT autonomously reachable — J-22/J-23/J-24 remain externally Yahoo-429 data-walled. Expect the evaluator to return CONTINUE (28/31) or a correct STALLED on the data-walled remainder. Do NOT manufacture work against the data-walled journeys.
