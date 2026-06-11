# Goal Iteration 2 — Finish deep-linkable ?asof + major-indexes & regime-band charts (J-43, J-44, J-45)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 2
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-43, J-44, J-45
- **Required-still-passing journeys:** J-01, J-06, J-13, J-18, J-20, J-42
- **Anti-goal reminders:**
  - **Regime overlays read stored regime only.** "The dashboard index-chart bands and the stock-detail bands MUST be built from the persisted per-run regime values (label + score from the immutable runs); no endpoint, view, or client may recompute a regime, and the same date MUST show the same regime label/color on every surface. Bands MUST NOT render past the resolved as-of date."
  - **The index chart is honest and never data-gated.** "A configured index series without stored bars MUST be omitted with no synthesized line; the chart MUST render fully from the committed ETFs without DIA; the normalized % series MUST be computed server-side from stored bars (the frontend only re-formats, no client-side return math)."
  - **The `?asof` URL param is a serialization, not a second date state.** "Date-scoped pages MUST reflect the single global as-of state in the URL while historical (and stay date-free at latest), and a URL carrying `?asof` MUST restore it through the one global control; no page may parse, hold, or mutate its own independent date state. An invalid `?asof` MUST degrade to the latest view — never crash or fabricate a date."
  - **No recompute in the read path.** "Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request."
  - **No lookahead.** "Scoring for a snapshot dated D MUST use only price bars with date ≤ D … Chart visualization MAY render bars dated > D strictly as a labelled forward/after-as-of display; this display path MUST NOT feed any score, bucket, setup status, pattern flag, factor value, or ranking."
  - **No magic numbers.** "Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file" — applied here to the index-chart symbol list + display names and range presets.
  - **One date format, displayed — ISO contracts unchanged.** "Every user-facing calendar date MUST render `yyyy-MM-dd` through one shared formatter/constant" — the new chart tooltips MUST route through `apps/frontend/lib/dates.ts`.

## GOAL

Deep links carrying `?asof` survive reload, fresh tabs, and click-through (J-43 finished), and the user can see the market's path and its regime at a glance: a dashboard "Major indexes & regime" chart and matching regime bands behind the stock-detail price chart, both reading stored regime history only (J-44, J-45).

## BACKGROUND

The iter-1 evaluator (CONTINUE, lean recommended) root-caused J-43's remaining failure precisely: in `apps/frontend/components/asof-provider.tsx`, the `AsOfUrlSync` serialize effect declares deps `[asOf, latest, ready, pathname]` but reads `searchParams` from the closure — on deep-link load the strip fires with `asOf=null`, then the `asOf=D` re-run reads a stale `searchParams` (`current === next`) and early-returns, so the strip wins permanently. The fix is surgical (add `searchParams` / a `searchParams.toString()` key to the dependency set, or defer serialization until the restored state commits), small enough to bundle with starting J-44 + J-45 per the evaluator's explicit recommendation. J-44 and J-45 share one new stored-data read path and are already registered as TARGET rows in the session blueprint: `regime_history:get_regime_history` → `GET /api/regime-history` and `indexes:compute_index_series` → `GET /api/indexes`. Both are read-only derivations over immutable stored rows — no schema change, no scoring change — so lean depth holds; this is the 3-journey cap for one iteration.

**Lesson applied (iter-1, episodic memory):** a Next.js App Router URL↔state sync needs `searchParams` in the serialize effect's dependency array, and HTTP-200 smoke cannot catch the strip — only a **post-hydration `window.location.href` assertion** can. Browser QA MUST verify the reload / fresh-tab / click-through legs that way. Also: ESLint is not installed in `apps/frontend` — `tsc --noEmit` is the frontend gate, never `npm run lint`.

## IN SCOPE

### Backend

- [ ] New read-only engine module `apps/backend/app/engine/regime_history.py` exposing `get_regime_history(...)`: returns the per-date series (date → regime label + score) read **verbatim** from the immutable `scanner_runs` rows, bounded to dates ≤ the resolved as-of date. No regime value is ever recomputed; labels/scores are the stored ones.
- [ ] New endpoint `GET /api/regime-history` (new `apps/backend/app/api/` route or mounted on an existing router file) serving that series, honoring an `as_of` query param exactly like the other read endpoints (resolution semantics consistent with `snapshot_serving`); rows dated after the resolved as-of are never returned.
- [ ] New read-only engine module `apps/backend/app/engine/indexes.py` exposing `compute_index_series(...)`: server-side normalized % lines (rebased to the selected range start) for the **config-listed** index ETFs, computed from stored bars only. A configured symbol with no stored bars (e.g. DIA) is omitted honestly — never synthesized. Series are bounded to dates ≤ the resolved as-of date.
- [ ] New endpoint `GET /api/indexes` serving the normalized series + legend names + the available range presets, with `range` (preset key) and `as_of` params; unknown preset → explicit 4xx (422), never a silent fallback to a fabricated range.
- [ ] `config.yaml` additions (no magic numbers): the index-chart symbol list + display names (SPY, QQQ, IWM, RSP; DIA listed but bar-less is fine) and the range presets (e.g. 3M/6M/1Y/All). Wire through `app/config.py` validation. **If any new key is required by the typed config, add it to ALL FOUR inline test config dicts (MINIMAL_VALID, VALID, test_sectors, test_themes) — a documented past failure mode in this repo.**
- [ ] Unit/API tests: regime-history verbatim-read + as-of bounding (no row > D); index-series rebase-at-range-start correctness, as-of bounding, barless-symbol omission, config-driven symbols/presets, unknown-preset 422.

### Frontend

- [ ] **J-43 fix:** in `apps/frontend/components/asof-provider.tsx` `AsOfUrlSync`, include `searchParams` (or its `.toString()` key) in the serialize effect's dependency set — or defer serialization until the restored state has committed — so a deep-linked `?asof=D` survives hydration, reload, and fresh tabs. No other `?asof` reader/writer may appear; the provider stays the sole owner.
- [ ] **J-44 dashboard card "Major indexes & regime"** on `/`: normalized % lines for the served index series with a legend; soft regime background bands from `GET /api/regime-history` drawn as an honest **step function between snapshot dates**, colored by three risk families with the exact six-value stored label + score on hover; hover tooltip shows the `yyyy-MM-dd` date (via `lib/dates.ts`), each index's % value, and the regime label + score; range-preset switcher (presets from the API/config, not hardcoded) re-normalizes to the new range start; enable toggle **default ON**, persisted client-side, fully hides the card when off; with a historical global as-of, no bar and no band renders after D.
- [ ] **J-45 regime bands behind the stock-detail price chart** (`components/price-chart.tsx` / `app/stocks/[ticker]/page.tsx`): the same stored regime values via the same endpoint — identical label and color for the same date as the dashboard card; a **Regime** toggle (default ON, persisted client-side); bands render only for dates ≤ the resolved as-of; the post-as-of forward region keeps its J-20 muted display-only treatment with **no** regime bands; the three scores, setup status, pattern flags, as-of marker, and every J-20 behavior unchanged.
- [ ] One shared label→risk-family/color mapping module used by BOTH chart surfaces (no duplicated mapping; same date ⇒ same color everywhere).
- [ ] `tsc --noEmit` clean.

### New user-facing capability

Shareable historical URLs that actually survive reload/new-tab; a glanceable market-path + regime-history visualization on the dashboard; regime context behind every stock's price history.

### New information displayed

Normalized % performance lines for the committed index ETFs over selectable ranges; per-date stored market-regime label + score as background bands (dashboard chart and stock-detail chart), with exact label/score on hover.

### New user actions

Range-preset switcher and show/hide toggle on the dashboard indexes card; Regime band toggle in the stock-detail chart controls; durable copy/paste of `?asof` deep links.

### UI surface changes

New "Major indexes & regime" card on `/` (default visible); regime band overlay + toggle on the existing stock-detail chart. No new pages, no nav change.

### Product surface delta

The dashboard gains its J-44 evidence card; Stock Detail gains regime context; the as-of state becomes fully deep-linkable. No page moves; no second home for anything.

### Blueprint conformance

Both surfaces live under their already-registered IA homes: the indexes card on **Dashboard `/`** (blueprint: "J-44 Major-indexes & regime card [TARGET]") and the bands on **Stock Detail `/stocks/[ticker]`** (blueprint: "J-45 regime bands [TARGET]"). No new pages, no nav-skeleton change.

### Data-contract additions

None beyond the two rows ALREADY registered as TARGET in `blueprint.md`, which this iteration builds exactly as written: **Regime history series** → `regime_history:get_regime_history` → `GET /api/regime-history` (labels/scores read verbatim from immutable `scanner_runs`, consumed by BOTH chart surfaces), and **Normalized index display series** → `indexes:compute_index_series` → `GET /api/indexes` (presentation series, not a canonical score). Do NOT add any second path that computes or serves a regime label/score or an index return — every other displayed value reads its existing registered canonical endpoint.

## OUT OF SCOPE

- J-46 (parallel fetch / vectorized backfill / benchmark script) and J-47 (≥100-term glossary + inline term help) — next iterations.
- The one-shot DIA fetch (data-walled; providers currently rate-limit/refuse this host — see NOTES). J-44 is explicitly NOT gated on DIA: render fully from the committed ETFs and omit DIA from the legend honestly.
- J-22 / J-23 / J-24 (data-walled, non-halting NA per goal.md).
- Any change to scoring, regime computation, snapshot creation, schema, or the import pipeline.
- Any per-page date control or second `?asof` reader/writer.

## DEFINITION OF DONE

- [ ] J-43 passes ALL legs via browser-qa-agent: interactive select writes `?asof=D`; leaderboard→detail click-through keeps it; reload keeps it; fresh tab keeps it; switch-to-latest removes it everywhere; invalid/unknown `?asof` degrades to latest — URL legs asserted via post-hydration `window.location.href`, not HTTP smoke.
- [ ] J-44 and J-45 pass via browser-qa-agent per their verbatim goal.md acceptance (band coloring identical across both surfaces for the same date; nothing rendered past a historical as-of; toggles persist across reload; defaults ON).
- [ ] Required-still-passing journeys remain green: J-01 (dashboard at a glance with the new card present), J-06, J-13, J-18, J-20 (forward region unchanged, no bands past as-of), J-42 (new tooltips/dates ISO via the shared formatter).
- [ ] No anti-goal violation introduced (esp. no regime recompute anywhere, no client-side return math, no second date state).
- [ ] New unit/API tests pass; full pytest suite green once before handoff (~14 min — do not run two pytest invocations concurrently); `tsc --noEmit` clean.
- [ ] Blueprint TARGET rows for J-44/J-45 implemented under exactly the registered module/endpoint names (or the blueprint updated additively if a name must differ).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-43 (deep-link/reload/fresh-tab/click-through legs with `window.location.href` extraction after hydration), J-44 (card render + legend + range-preset re-normalization + toggle off→reload→still off→on + historical as-of bound), J-45 (bands on detail + identical color for the same date as dashboard + Regime toggle persistence + historical as-of bound + J-20 forward region band-free). Re-verify J-01, J-06, J-13, J-18, J-20, J-42.
- Unit/integration: `regime_history` returns stored label/score verbatim and never a row > resolved as-of; `compute_index_series` rebases to the range start (first point ≈ 0%), matches a hand-computed series from stored bars, bounds to as-of, omits barless configured symbols, reads symbols/presets from config; API tests for both endpoints incl. `as_of` resolution and 422 on unknown preset; config-validation tests updated for new keys (all four inline fixture dicts).
- Error cases: `GET /api/indexes?range=<bogus>` → 422; `as_of` predating all runs → honest empty series (no crash, no fabricated rows); configured symbol with zero bars omitted from response and legend; `?asof=not-a-date` and `?asof=<date-with-no-run>` still degrade to latest after the J-43 fix.

## NOTES

- **Evaluator feedback driving scope:** iter-1 eval explicitly recommended lean iter-2 = finish J-43 (root cause quoted in BACKGROUND) bundled with starting J-44+J-45, required-still-passing J-06/J-13/J-18, and flipping the J-42 blueprint row to built (done — see `runs/goal-session-<sid>/state/blueprint.md`). J-43 remains the blueprint TARGET row until the reload/fresh-tab legs pass.
- **Browser-QA gotchas (project memory):** (1) the as-of `<select>` is React-controlled — Chrome MCP `select` doesn't fire React `onChange` on this frontend; use the native-setter + bubbled change event in eval, then assert live DOM. (2) If every page is a dead un-hydrated shell (404 on `_next/static/chunks/main-app.js`), the dev server's `.next` was clobbered by a prod build — record SKIPPED, not FAIL. (3) Per the amended J-18, `?asof=` in the page URL while historical is REQUIRED (the serialization of the one state) — judge J-18 on "no page-local independent date state", never on URL date-freeness.
- **Canvas hover:** the lightweight-charts tooltip is not hover-automatable; per the accepted J-42 precedent, the hover-tooltip legs of J-44/J-45 may be accepted on code inspection of a single tooltip hook reading the served stored label/score + `formatIsoDate`, provided the bands themselves are visible in screenshots.
- **Provider access (memory):** Yahoo EOD persistently 429s this IP, Tiingo 403s, Stooq needs a key — hence DIA stays an honest legend omission; do not burn the iteration on live fetches.
- **Backend suite runtime:** full pytest ≈ 14 min (heavy walk-forward boot); run it once, never two invocations concurrently.
- Escalation flag: none. Prior verdict CONTINUE, coherence COHERENCE-PASS, no regressions.
