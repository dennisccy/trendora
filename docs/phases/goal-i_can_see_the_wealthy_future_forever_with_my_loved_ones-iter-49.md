# Goal Iteration 49 — 52w-high proximity column + honest readiness badge fix

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 49
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-106, J-108
- **Required-still-passing journeys:** J-01, J-06, J-07, J-18, J-40, J-48, J-75, J-80, J-104
- **Anti-goal reminders:**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Readiness is reported honestly.** The health / readiness signal MUST distinguish **serving-ready** from **warming (with real progress)** from **unavailable**; it MUST NOT report ready before the latest snapshot is servable, MUST NOT mislabel a still-warming backend as "unavailable", and MUST NOT present a still-loading analytics aggregate as a complete or fabricated result.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.
  - **Setup & pattern vocabulary is config-driven in the UI too.** The glossary and tooltips MUST be generated from the single config-backed catalog — no hard-coded per-entry copy in the frontend.
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page reads the single global as-of control. *(critical)*
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere; any live-provider key is read only from the environment.

## GOAL

Show a sortable "Proximity to 52w high" column on the Stocks leaderboard (re-displaying the stored value the Leadership breakdown already shows), and fix the readiness badge so it honestly reflects backend status instead of being stuck on "Backend unavailable".

## BACKGROUND

This is an in-place resume after the iter-48 GOAL_ACHIEVED close-out. `docs/goal.md` was extended (commit 95b4926) with three new buildable, NOT-data-dependent Must-haves — J-106 (52w-high column), J-107 (Factor Lab all-factors table), J-108 (readiness-badge fix). Per the iter-22 lesson, these queued Must-haves have no journey-history entry yet, so they are `unknown` and drive CONTINUE until built and live-verified. This iteration takes the two smaller, independent, user-facing fixes (J-106 + J-108) and deliberately leaves the heavy backend Factor-Lab restructure (J-107) isolated for iter-50, so its full cached-aggregate / streamed read-path work does not entangle these clean wins. Depth is **full** because J-108 is a regression-class diagnosis touching the universal client fetch base (`lib/api.ts`) and possibly backend CORS, needs dedicated unit tests plus a `./scripts/dev.sh` verification, and benefits from the full pipeline (ui-impact / ux-regression / closure).

## IN SCOPE

### Backend
- [ ] **(J-108) Diagnose, then fix the root cause of the live `/api/health` request path** under `./scripts/dev.sh` so the badge reaches Ready / Initializing when the backend is genuinely serving. The dev MUST document the diagnosed root cause (step 4 of J-108) before fixing. Strongest hypothesis to confirm/refute first: the host/CORS mismatch — `dev.sh` advertises both `http://localhost:<port>` and `http://<LAN_IP>:<port>`, the frontend bakes `NEXT_PUBLIC_API_URL=http://localhost:<backend_port>`, and `CORS_ORIGINS` only lists `localhost` origins, so a browser opened at the LAN-IP origin is CORS-blocked / fetches the wrong host → `fetchHealth()` throws → badge stuck "unavailable". If confirmed, widen `CORS_ORIGINS` (or use a dev origin allowance) so the LAN-IP frontend origin is accepted. Also confirm `readiness.py latest_servable` returns the correct state. **No new endpoint, no new served value, no canonical-value change.**
- [ ] **(J-106) NO backend change.** `high_proximity` is already served as a Leadership `ScoreComponent` (carrying its raw value) on every `/api/stocks` and `/api/stocks/{ticker}` row (`scoring:score_stocks`, scoring.py:145). Do NOT add a new top-level field to the `/api/stocks` payload — that would trip the byte-equality / `set(payload)==` guards (iter-23/24/32 trap). Read the existing component value.

### Frontend
- [ ] **(J-106)** Add a **"Proximity to 52w high"** column to the `/stocks` leaderboard (`apps/frontend/app/stocks/page.tsx`), **directly after the Risk column** (the existing `SortHeader col="risk"`). Display the stored `high_proximity` value read from each row's `leadership.components` — the SAME value the Leadership component breakdown shows (single source; no recompute; no new served field). Render **NA-honest** where the component value is null (≤ 0 normally, 0 at a fresh high). Make it **client-side sortable** via the existing `SortHeader` / `comparatorFor` view-transform contract (J-48), **NA-last**; expose the sort control with an `aria-label` (e.g. "Sort by Proximity to 52w high"). Give the header the **config-backed glossary tooltip** the term already has via `TermInfo` / `InfoTooltip` (J-47 — `component-breakdown.tsx` already maps `high_proximity → "Proximity to 52w high"`). No second date state.
- [ ] **(J-108)** Apply the diagnosed client-side fix to the readiness/health request path. Most likely: make `API_BASE` in `apps/frontend/lib/api.ts` **host-aware at runtime** — when the configured base points at `localhost` but the page is opened on a non-localhost host, resolve the backend origin from `window.location.hostname` + the already-exported `NEXT_PUBLIC_API_PORT` (so the browser hits the backend on the same host it loaded the page from); use an explicit non-localhost `NEXT_PUBLIC_API_URL` verbatim when provided. And/or correct the `ReadinessProvider` poll success/failure/timeout handling. The badge MUST be honest — **never hardcoded, inverted, stuck, or faked Ready when the backend is down.**

### New user-facing capability
The Stocks leaderboard shows each name's distance below its 52-week high at a glance and lets the user sort by it; the top-bar readiness badge correctly reads Ready / Initializing / Unavailable instead of always showing "Backend unavailable".

### New information displayed
Per-stock proximity-to-52w-high percentage on the leaderboard (a re-display of the existing stored Leadership `high_proximity` component value).

### New user actions
Click the new column header to sort the leaderboard by proximity-to-52w-high.

### UI surface changes
`/stocks` leaderboard table gains one column after Risk. The readiness badge (app shell) behavior is corrected — no new surface.

### Product surface delta
The leaderboard becomes more informative without a new fetch, and the whole app stops misreporting backend availability on every page — a visible trust/correctness fix.

### Blueprint conformance
J-106 lives on the existing `/stocks` Stocks leaderboard home (Information Architecture). J-108 fixes the existing readiness badge in the persistent app shell. No new pages and no nav-skeleton change → no `blueprint.reapproval-requested`. An additive prose note (the J-106..J-108 SESSION EXTENSION) has been appended to `blueprint.md`.

### Data-contract additions
None. `high_proximity` is already a registered Leadership component value (Data Contract: computing module `scoring:score_stocks`, served via `GET /api/stocks` + `GET /api/stocks/{ticker}` — blueprint line 369); the new column re-displays it (not a new value, endpoint, or computation). The readiness state is already registered (`readiness:compute_readiness` → `GET /api/health` — blueprint line 396); J-108 fixes its request path and introduces no new value. Never introduce a second computation or endpoint for either.

## OUT OF SCOPE

- **J-107** (Factor Lab all-factors Rank-IC + risk-adjusted table with expandable per-factor decile sort) — deferred to iter-50 (FULL, isolated) because it touches the cached-aggregate / streamed research read path (the iter-46/47/48 OOM-sensitive area).
- Any change to the heavy research read path, `EventStudyCache`, or `compute_factor_lab`.
- Adding `high_proximity` — or any new field — to the `/api/stocks` payload (read the already-served component value; avoids the iter-23/24/32 byte-equality-guard trap).
- Any change to canonical scores, the Risk-Off→Actionable gate, the as-of / `?asof` contract, or a second date state.
- J-22 / J-23 / J-24 (data-walled, non-vetoing per goal.md:105-108).

## DEFINITION OF DONE

- [ ] J-106 passes via browser-qa: the "Proximity to 52w high" column renders directly after Risk, shows the same value as the Leadership breakdown, is client-side sortable (NA-last), is NA-honest, and its header carries the config-backed glossary tooltip.
- [ ] J-108 passes: with the backend genuinely serving under `./scripts/dev.sh`, the badge reaches **Ready** (or **Initializing… n/m** during warm-up) and shows **Unavailable** only when the backend is truly down — with a documented diagnosed root cause; the diagnosed failing scenario (e.g. the LAN-IP origin) now reaches Ready.
- [ ] Required-still-passing journeys remain green (J-01, J-06, J-07, J-18, J-40, J-48, J-75, J-80, J-104) — in particular confirm data still loads on every page after the `API_BASE` change.
- [ ] No anti-goal violation introduced (single source, no recompute, no magic numbers, honest readiness, no secrets, exactly one date selector, Risk-Off gate intact).
- [ ] Unit tests pass; no regressions; the full backend suite flushes `0 failed, EXIT 0` (run nohup-async via the pump — do NOT block the evaluator on the in-flight suite).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-dev.md`, including the diagnosed J-108 root cause.

## TESTING REQUIREMENTS

- **Browser:**
  - **J-106** — Stocks leaderboard: the new column renders directly after Risk; a row's value equals what that stock's Leadership breakdown shows for `high_proximity`; sorting by the column reorders the table (capture two byte-distinct frames); a null value renders NA and sorts last; the header tooltip surfaces the glossary copy.
  - **J-108** — readiness badge: with a freshly-restarted, warmed, genuinely-serving backend the badge reaches **Ready** (or **Initializing… n/m**); **exercise the diagnosed failing scenario** (e.g. open the frontend at the dev.sh-printed LAN-IP origin) and confirm the badge now reaches Ready rather than "Backend unavailable"; with the backend genuinely down the badge shows **Unavailable** (honest — not faked Ready).
  - **Required-still-passing smoke:** J-01 (dashboard hydrates), J-06 (stock detail == leaderboard), J-07 (Risk-Off → 0 Actionable — CRITICAL), J-18 (0 native `input[type=date]` — CRITICAL), J-48 (a column sort reorders), J-75 / J-80 (/stocks forward-return columns + header regime/theme strip), J-104 (a research lab still loads after the `API_BASE` change).
- **Unit/integration:**
  - A test for the host-aware `API_BASE` resolution: given a `localhost`-configured base + a non-localhost page host, it resolves the backend on the page host's hostname + the configured `NEXT_PUBLIC_API_PORT`; given an explicit non-localhost `NEXT_PUBLIC_API_URL`, it is used verbatim.
  - If CORS is changed, a backend test that a request bearing the LAN-IP frontend origin is allowed; confirm `readiness.py` readiness states are unchanged.
  - J-106 is frontend-only — add/confirm a rendering/sort test if the frontend suite supports it; otherwise rely on browser-qa.
- **Error cases:**
  - Backend genuinely down → badge shows **Unavailable** (must NOT fake Ready).
  - `high_proximity` null → column shows **NA** and sorts NA-last (never fabricated).

## NOTES

- **Lessons applied (episodic memory):**
  - iter-23 / iter-24 / iter-32: do NOT add a new field to `/api/stocks` (or any scored endpoint payload) — read the already-served component value, or the `test_api_*_equals_engine_output` / `set(payload)==` byte-equality guards go red. J-106 is frontend-only by design.
  - iter-27 / iter-28b: resolve sort-header buttons by `aria-label`, not visible `text()` (`SortHeader` labels live in a nested `<span>`); before calling a sort a regression, confirm the `SortHeader` / `comparatorFor` path is the existing one.
  - iter-17 / iter-25 / iter-36 / iter-39 / iter-40 / iter-43: render-gated journeys need LIVE evidence — **plan the Playwright fallback UP FRONT** (Chrome MCP CDP has repeatedly emptied the evidence dir on this host), `md5sum` the evidence dir first, reject blank/skeleton/byte-identical frames; a differential leg (the J-106 sort reorder) needs two byte-distinct frames.
  - iter-45: when the badge shows "Backend unavailable", first disambiguate a genuine code bug from a contended/hung backend — run on a freshly-restarted, warmed, single-fetch-at-a-time backend, and verify the EXACT request path (URL + Origin + status) the browser uses. A curl from localhost bypasses the CORS/host bug, so it cannot prove J-108 fixed — exercise the actual failing scenario in the browser.
- **J-108 verification subtlety:** the standard browser-qa opens the frontend at `localhost`, where the localhost-hardcoded `API_BASE` may already work — so QA MUST exercise the diagnosed failing scenario (the LAN-IP / dev.sh-printed origin) to prove the regression is actually fixed, not masked by same-host localhost.
- **Depth rationale:** full because J-108 touches the universal client fetch base + possibly backend CORS and is a regression-class diagnosis needing dedicated tests and dev.sh verification. This iteration is **not** a GOAL_ACHIEVED candidate (J-107 still unbuilt), so the flushed-suite gate is non-load-bearing here — run it nohup-async and never block the evaluator (iter-11/29/37).
- **Next:** iter-50 FULL builds J-107 (all-factors Factor Lab table, cached-aggregate + streamed per J-105, expandable per-factor decile sort, retiring the per-regime effectiveness table from that view) in isolation. After J-106/J-107/J-108 all pass on live evidence with a flushed-GREEN suite + COHERENCE-PASS, the next evaluation is a sound GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay blocked-NA, non-vetoing).
