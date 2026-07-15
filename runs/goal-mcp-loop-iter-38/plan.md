# goal-mcp-loop-iter-38 Execution Plan

**Journey:** J-23 (watchlist concentration X-ray) · **Backlog card:** B-204 · **Depth:** full ·
**Evidence Claim:** none (descriptive-only journey; post-decompose gate passes automatically;
both ledgers stay byte-identical, 7/7 FAIL, canonical Bonferroni divisor stays 8).

**Alignment check:** J-23's text in `docs/goal.md` matches this phase spec verbatim (owner-pulled
backlog card, no Evidence Claim, no advice language). No drift from the goal doc. The session
blueprint (`runs/goal-session-mcp-loop/state/blueprint.md`) already carries the full iter-38 Data
Contract clarification (line ~274) and the IA "Feature / journey homes" row (line ~91) and Data
Contract row (line ~122) for this exact value — read those verbatim before implementing; this plan
summarizes but does not restate every clause. `runs/goal-session-mcp-loop/state/assumptions.md`
(iter-38 entry) already logged the build-order call: J-23 lands first and creates the ONE canonical
ENB/correlation helper; the future B-104 evidence-correlation audit will import it later.

## What to Build

- **`app.engine.concentration`** (NEW, pure module) — the one canonical ENB/correlation helper:
  `correlation_matrix(series_by_name)` (Pearson over aligned daily returns; an undefined/zero-variance
  pair → honest `None`, never a fabricated 0) and `effective_number_of_bets(corr_matrix)` =
  `(Σλ)²/Σλ²` over the matrix's eigenvalues via `numpy.linalg.eigvalsh` (numpy is already a runtime
  dependency — see `app/engine/referee.py`). This is the ONLY ENB implementation in the codebase.
- **`app.engine.watchlist_xray:build_xray_payload(session, cfg, tickers, asof)`** (NEW, pure
  composer) — over the watchlist's own tickers: pairwise return-correlation matrix from bounded
  per-symbol `prices:bars_asof_window` reads (bars ≤ as-of, trailing `corr_window_days`; NEVER a
  whole-table load), a deterministic correlation-threshold cluster grouping (connected components at
  `cluster_threshold`; no ML), ENB via the shared helper over the honest sub-matrix, sector + theme
  concentration bars and a shared-setup count read from the SAME canonical rows `GET /api/stocks`
  serves (`snapshot_serving:filtered_stock_rows` — recomputes no score/sector/setup/theme value), and
  honest NA for any member with `< min_overlap_days` overlapping history.
- **Config surface** — new top-level `watchlist:` block in `config.yaml` (does not exist today) with
  `xray.{corr_window_days (~126 default), cluster_threshold, min_overlap_days}`, plus a typed
  `WatchlistCfg`/`WatchlistXrayCfg` in `app/config.py`, wired into `Config` as
  `Field(default_factory=...)` — **default-populated**, matching the established pattern for every
  prior iter-added config block (`chart_bars`, `data_quality`, `server`, etc.) so a config/fixture
  predating this key still loads unchanged.
- **Additive `xray` field on the EXISTING `GET /api/watchlist`** (`app/api/watchlist.py`) — computed
  once alongside the existing response; `asof_date` + `entries[]` stay byte-identical. No new
  endpoint. No `Watchlist` table/schema change (computed on read only).
- **Frontend X-ray section on `/watchlist`** (`app/watchlist/page.tsx`) — correlation matrix heatmap
  (NA cells rendered honestly), cluster groupings, sector/theme concentration bars, shared-setup
  count, and the headline "effective independent bets ≈ N.N (over the last W trading days)" with the
  window explicitly stated. Reads the served `xray` payload **verbatim** — no browser-side
  correlation/ENB recompute (B-204's named dominant failure mode). Add the additive `WatchlistXray`
  type in `lib/api.ts`.
- Backend unit/integration tests: the B-204 fixture (two perfectly correlated + one independent
  synthetic series → ENB ≈ 2, clusters correct), a pairwise-correlation spot-check vs an independent
  offline computation, additive-shape + byte-identity tests, null-sector "Unassigned" bucketing,
  determinism, and the three honest-degrade error cases (short-overlap NA, empty/1-name watchlist
  200, missing-bars NA — never a 500).
- Dev handoff at `docs/handoffs/goal-mcp-loop-iter-38-dev.md`.

### Explicit out of scope (per phase spec — do not creep into these)
- The `/evidence`-side B-104 claim-correlation audit UI — this iteration builds ONLY the shared
  helper; no `/evidence` change.
- Any advice language ("trim"/"add"/"reduce"/"rebalance") or position-tracking concept
  (quantity/cost-basis/P&L/order/buy/sell/broker) — descriptive only.
- Any `Watchlist` table/schema change or persisted X-ray field (computed on read every time).
- J-24 (risk-budget card) / J-25 (drawdown expectations) — separate future iterations.
- Any `## Evidence Claim` / referee submission — none registered this iteration.
- Fancy/ML clustering — deterministic correlation-threshold connected components only.

### Judgment call flagged for the developer
"Count of names sharing the same detected setup" most naturally reads as the existing six-status
`setup.status` classification (`app.engine.setups` — Actionable/Breakout-watch/.../Risk-off-watchlist)
already shown per-row in the watchlist table today, NOT the pattern-level VCP/pullback/flat-base
flags from `app/engine/patterns.py` (a different, more granular concept). Recommend adopting the
`setup.status` reading since it is cheap (already in the canonical row), consistent with what the
page already surfaces, and matches "setup" vocabulary used elsewhere in this journey's own acceptance
text. If the developer disagrees, log the alternate choice to `assumptions.md` per project convention.

## Agents Required
- backend-data: yes -- new `app.engine.concentration` helper, new `app.engine.watchlist_xray`
  composer, typed `watchlist.xray` config surface, additive `xray` field on `GET /api/watchlist`,
  and the backend unit/integration/error-case tests listed above.
- frontend-ux: yes -- additive X-ray section on `/watchlist` (heatmap, clusters, ENB headline+window,
  sector/theme concentration bars, shared-setup count), `WatchlistXray` type in `lib/api.ts`, honest
  empty/insufficient/NA states, zero browser-side recompute.

## Frontend Present
Frontend Present: yes

## Files to Create/Modify

Backend (new):
- `apps/backend/app/engine/concentration.py` — `correlation_matrix()`, `effective_number_of_bets()`
- `apps/backend/app/engine/watchlist_xray.py` — `build_xray_payload()`
- `apps/backend/tests/test_concentration.py` — ENB/correlation helper unit tests + B-204 fixture
- `apps/backend/tests/test_watchlist_xray.py` — composer tests (NA, determinism, sector bucketing)

Backend (modify):
- `apps/backend/app/config.py` — add `WatchlistXrayCfg`/`WatchlistCfg`, wire into `Config`
- `config.yaml` — new top-level `watchlist:` block (`xray.corr_window_days/cluster_threshold/min_overlap_days`)
- `apps/backend/app/api/watchlist.py` — attach additive `xray` field in `list_watchlist()`
- `apps/backend/tests/test_api_watchlist.py` — extend for the additive field + unchanged existing shape

Frontend (modify):
- `apps/frontend/lib/api.ts` — `WatchlistXray` type (+ matrix/cluster/concentration sub-types), extend `WatchlistResponse`
- `apps/frontend/app/watchlist/page.tsx` — the new X-ray section + empty/insufficient/NA states

Frontend (new, optional split — developer's call):
- `apps/frontend/components/correlation-heatmap.tsx` — if a standalone matrix component reads
  cleaner than inlining; the watchlist is small (typically well under a few dozen names) so none of
  the `availability-heatmap.tsx` (~7,800-cell) memoization concerns apply here.

No change needed: `apps/backend/app/models.py` (no schema change), `runs/goal-session-mcp-loop/state/blueprint.md`
(already carries the iter-38 Data Contract entry).

## UI Evolution
- New user-facing capability: the owner can see how concentrated their watchlist really is — how
  many independent bets it represents, which names move together, and where sector/theme/setup
  crowding sits.
- New information displayed: pairwise return-correlation matrix; correlation-threshold clusters;
  effective-number-of-bets headline + its trailing window; sector and theme concentration bars;
  count of names sharing the same setup status.
- New user actions: none — read-only descriptive section. Existing add/remove/reason controls unchanged.
- UI surface changes: one additive section on the existing `/watchlist` page (below/alongside the
  current entries table). No new page, no new route.
- Navigation changes: none — Watchlist is already a persistent top-level nav item.

## Visual Requirements
- Component patterns: `Card` wrapper for the new section (matches the existing table's `Card`
  container); `Badge` for cluster/sector/theme chips reusing the existing variant vocabulary
  (ok/warn/danger/accent/default) already used for setup status; `info-tooltip.tsx` next to the ENB
  headline to explain the methodology/window in one line; reuse the `EmptyState` pattern (already
  used for zero watchlist entries) for the "insufficient watchlist for an X-ray" sub-state.
- Layout: stack the new section below the existing entries table inside the same page container
  (`space-y-4`, matching the page's current layout rhythm) — correlation matrix as a compact
  cell-grid table (same spirit as `components/availability-heatmap.tsx`'s cell grid, but far smaller
  — no virtualization/memoization needed at watchlist scale).
- Key visual effects: color the correlation cells with the app's EXISTING sign tokens (`text-pos` /
  `text-neg` / muted), the same family already used for `price_since_added` on this very page —
  positive correlation tinted positive, negative tinted negative, NA cells visibly muted/hatched
  (never a fabricated color implying a number). Do not invent a new color scale. Keep the existing
  dense, minimal, data-first look — no glassmorphism/glow on this page.
- States to handle: loading skeleton (mirror the existing `WatchlistSkeleton` treatment); empty/short
  watchlist (0–1 names, or too few for a meaningful matrix) → an honest, distinct "not enough names
  yet for an X-ray" state (not the same copy as the zero-entries `EmptyState`, but same visual
  family); NA cells for thin-overlap pairs inside an otherwise-populated matrix; the existing
  page-level "Backend unavailable" error state already covers this section since it's part of the
  same `GET /api/watchlist` response — no separate fetch/error state needed.

## Key Test Scenarios
- ENB/correlation fixture: two perfectly correlated synthetic series + one independent series →
  ENB ≈ 2, clusters correctly group the two correlated names and isolate the independent one.
- A spot-checked pairwise correlation from the composer matches an independent offline computation
  over the identical window (anti-goal #3, correctness).
- An undefined/zero-variance pair renders honest NA, never a fabricated 0.
- A member with `< min_overlap_days` overlapping history renders NA in the matrix, not a crash.
- A watchlist member whose bars are absent for the window → NA row, no crash.
- Empty or 1-name watchlist → HTTP 200 with an honest empty/insufficient `xray` state, never a 500.
- Null `sector` buckets into "Unassigned" in the concentration bars (iter-18/19 nullable-field
  lesson), never a crash and never silently dropped.
- `GET /api/watchlist`: existing `asof_date` + `entries[]` shape is byte-identical pre/post change;
  existing watchlist API tests stay green; the new `xray` field is purely additive.
- Determinism: the same seed/as-of reproduces the X-ray byte-identically across repeated calls
  (anchored to `latest_data_date`, never wall-clock).
- `grep` confirms exactly ONE `effective_number_of_bets`/ENB implementation in the codebase (no
  second helper introduced).
- Neither the `xray` payload nor the rendered section contains proven-language ("Proven"/"Not yet
  proven") or advice language ("trim"/"add"/"reduce"/"rebalance").
- Browser (J-23, all 3 steps): with several correlated names + one unrelated name on the watchlist,
  the X-ray shows the correlation view, cluster groupings, sector/theme concentration, and the ENB
  headline with its window stated; a spot-checked pair matches an offline computation; a
  short-history name renders NA in the matrix rather than a fabricated value.
- Regression: existing add/remove/reason controls on `/watchlist` still work unchanged.
- Ledger byte-identity: `certified-claims.jsonl` and `staging-ledger.jsonl` unchanged (7/7 FAIL, no
  new rows); no `## Evidence Claim` heading anywhere in this iteration's artifacts; canonical
  Bonferroni divisor stays 8.
- Required-still-passing set (per DoD) — **J-01, J-02, J-03, J-05, J-10, J-13, J-20** must remain
  green, re-verified either by the inline deterministic golden-script replay or an immediately
  -following lean verify pass. Flag for whichever agent owns closure: iter-33 and iter-36 both
  CLOSURE-FAILed on this exact DoD line because `run-phase.sh`/this full-iteration path has no
  deterministic-replay lane — do not let this iteration silently skip that re-verification and repeat
  the gap (a durable framework fix is out of scope for this iteration; it's recorded in the phase
  spec's NOTES for the framework maintainer).
