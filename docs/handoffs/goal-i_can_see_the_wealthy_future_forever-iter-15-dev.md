# goal-i_can_see_the_wealthy_future_forever-iter-15 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-15
**Date:** 2026-06-03
**Agent:** developer
**Status:** complete

## What Was Built

J-31 — the **synthesis capstone**: a navigable bridge from the Research labs' evidence to the
Stock Leaderboard names and on to Stock Detail. **Frontend-only; no backend change, no new
endpoint/query-param/computation, no new dependency.** Two edits:

- **A. Deep-linkable Stock Leaderboard filters** (`apps/frontend/app/stocks/page.tsx`):
  - The existing `sector` / `setup` / `pattern` filters now **initialize from URL query params** on
    load (lazy `useState` initializers reading `useSearchParams()`), so `/stocks` can be opened
    pre-filtered (e.g. `?pattern=pullback_to_rising_dma__only`, `?setup=Breakout-watch`,
    `?sector=Energy`). Encodings are the **existing** filter-state encodings verbatim.
  - Filter changes are **reflected back into the URL** via `router.replace(..., { scroll: false })`
    so the view is shareable / back-navigable. `__all__` values are omitted (clean URLs).
  - `pattern` is **strictly validated** against the in-file `PATTERNS` registry (`<key>__only` /
    `<key>__none` for a known key, else `__all__`); `sector`/`setup` are taken verbatim (an unmatched
    value harmlessly renders the existing honest empty-state). An absent/unrecognized param never
    crashes and fabricates no filter.
  - The page body is wrapped in a **`<Suspense>` boundary** (the first in this codebase) — required by
    the Next 15 App Router production build when `useSearchParams()` is used. The default export is now
    a thin `<Suspense fallback={<StocksSkeleton/>}><StocksInner/></Suspense>` wrapper; today's body
    moved into `StocksInner`.

- **B. Lab → leaderboard cross-link** (`apps/frontend/app/research/page.tsx`, `EventStudyLab`):
  - For the resolved event-study subject, a new **"View the names expressing this on the leaderboard →"**
    `next/link` cross-link, deep-linking the leaderboard to the matching filter derived from the
    subject's `kind` (payload/config-driven — **no hard-coded subject↔filter table**):
    - `kind === "pattern"` → `/stocks?pattern=<key>__only`
    - `kind === "setup"`  → `/stocks?setup=<key>` (the key IS the status string)
  - Rendered whenever a subject resolves — **including a low-sample / NA subject** (the "names
    expressing it today" set is independent of the historical event-study sample).
  - Honest framing caption next to it naming the synthesis path; it asserts **no count** it cannot
    prove (no extra fetch).

### Why this is the faithful bridge (no new computation)
The leaderboard has no factor filter, and adding one would be new computation (explicitly out of
scope). J-31's own steps route a factor's expression through an **aligned setup/pattern**, which is
simultaneously a forward-tested lab subject (J-29), an existing leaderboard filter (J-16/J-28), and a
per-name badge on detail (J-05/J-16). The cross-link maps the event-study `subject.kind`/`key` onto
that existing filter. **Source-verified alignment:** `subject_catalog()` builds setup subjects with
`key == setup_status` and pattern subjects with `key == cfg.patterns` key (the same keys the
leaderboard `PATTERNS` registry uses), so the deep-link lands on the correct, populated cohort.

## Files Changed
- `apps/frontend/app/stocks/page.tsx` — init the 3 filters from `useSearchParams` (lazy); reflect
  changes to the URL via `router.replace({scroll:false})`; `<Suspense>` wrapper + `StocksInner`; added
  the pure `parsePatternParam()` validator. Fetch effect **unchanged** (still keyed to `[asOf]` only).
- `apps/frontend/app/research/page.tsx` — added `import Link`; added the `SubjectLeaderboardLink`
  component (kind-driven href) and rendered it in `EventStudyLab` with an honest synthesis caption.
- `docs/handoffs/...-iter-15-dev.md`, `...-iter-15-frontend.md`,
  `reports/phase-...-iter-15-implementation-summary.md`, `runs/.../status.json` — artifacts.

## Tests Run
- **Frontend build + typecheck:** `cd apps/frontend && npm run build` — **PASS**.
  `✓ Compiled successfully` · `✓ Checking validity of types` (no type errors) ·
  `✓ Generating static pages (14/14)`. `/stocks` remained `○ (Static)` prerendered, confirming the
  `<Suspense>` boundary satisfies the Next 15 `useSearchParams` build requirement (a missing boundary
  fails the build).
- **Backend suite:** `apps/backend/.venv/bin/python -m pytest tests/ -q` — **PASS (no incidental
  breakage).** Result: **453 passed, 4 skipped** in 1244.83s (exit 0); the 4 skips are pre-existing
  (data-walled / intraday). No backend file was touched, so this is a confirmation run only (full
  result in `runs/.../iter-15/backend-test.log`).
- **No new frontend unit test** added: this frontend has no unit suite by project convention
  (`project-template.md` → "UI behaviour is covered by browser QA, not a unit suite"); correctness is
  covered by `npm run build` (typecheck) + the downstream browser flow. The param encode/decode logic
  is small and pure (`parsePatternParam`, the cross-link href) and exercised by the J-31 browser flow.

## Anti-goal / source verification (J-18 is the principal risk this iter)
- **Exactly one date selector (J-18):** the only URL params written/read are `sector`/`setup`/`pattern`
  (filters). **No `as_of`/date query param** is introduced (`git diff` grep confirms the only `as_of`
  hits are explanatory comments). `useAsOf()` remains the sole date source; the `fetchStocks` effect
  stays keyed to `[asOf]` only, so toggling the as-of re-points by date without touching the URL filter
  state and without firing a second date param.
- **No recompute / single source of truth:** no new endpoint, query param, or computation; filtering
  stays the existing pure client-side `visible` memo over server rows. The cross-link is
  `kind`/registry-driven (no hard-coded table).
- **Diff scope:** only `apps/frontend/app/stocks/page.tsx` + `apps/frontend/app/research/page.tsx`
  (+89/−4). No backend, config, or blueprint file touched.

## Known Issues
- **State↔URL is reflect-out only.** Filters initialize from the URL once (on mount) and reflect OUT on
  change; the page does **not** react to browser back/forward to re-read the URL into state (an optional
  nicety, not required by the spec, and deliberately avoided to prevent a state↔URL render loop — see
  plan risk #2). Opening a shareable deep-link works because that is a fresh mount.
- **Cross-link tracks the resolved (loaded) subject.** During a subject re-fetch the link briefly points
  at the previously-resolved subject until the new payload lands (sub-second), consistent with how the
  event-study body dims-and-keeps prior values during a re-fetch. Browser QA should let the lab finish
  loading before clicking.
- **J-31 step 4 "across timeframes" scoped to the canonical DAILY timeframe** per the iter-14 lesson:
  J-24 (the 1D/1h/15m/5m selector) is unbuilt and externally Yahoo-429 data-walled. Not a J-31 blocker;
  not built here; the intraday fetch was not retried.
- **Live browser verification is delegated to browser-qa-agent** (the pipeline's next stages). The
  production build (stricter than a dev-server smoke test for compile/type errors) passed; servers were
  not started by this agent (and none were left running).

## Suggested Next Phase
J-31 is the **last buildable journey**. After it is verified green, GOAL_ACHIEVED is **not**
autonomously reachable: J-22 / J-23 / J-24 remain externally Yahoo-429 data-walled and unblock only on
operator confirmation of a reachable no-key data egress (or a `docs/goal.md` scope edit). Expect the
evaluator to return CONTINUE (28/31) or a correct STALLED on the data-walled remainder. The decomposer
must **not** manufacture work against the data-walled journeys.
