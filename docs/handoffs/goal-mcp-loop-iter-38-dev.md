# goal-mcp-loop-iter-38 Dev Handoff

**Phase:** goal-mcp-loop-iter-38
**Date:** 2026-07-15
**Agent:** developer
**Status:** complete

## What Was Built

- **`app.engine.concentration`** (new, pure module) — the ONE canonical ENB / pairwise-correlation
  helper: `correlation_matrix(series_by_name)` (Pearson correlation, aligned on the trailing overlap of
  each pair; an undefined/zero-variance pair -> honest `None`, never a fabricated 0) and
  `effective_number_of_bets(corr_matrix)` = `(Σλ)²/Σλ²` over the eigenvalues of a clean correlation
  matrix via `numpy.linalg.eigvalsh`. No database, no I/O — fully pure and reusable by the future B-104
  evidence-correlation audit.
- **`app.engine.watchlist_xray:build_xray_payload(session, cfg, tickers, asof)`** (new, pure composer)
  — over the watchlist's own tickers: bounded per-symbol return series via
  `prices.bars_asof_window` (bars <= as-of, trailing `corr_window_days`, never a whole-table read), the
  full pairwise correlation matrix, deterministic correlation-threshold clustering (connected
  components, no ML), the effective-number-of-bets over the "honest sub-matrix" (only tickers whose
  correlation against every other included ticker is defined), sector/theme/setup concentration read
  from the SAME canonical rows `GET /api/stocks` serves (`snapshot_serving.filtered_stock_rows`) — setup
  concentration reuses `app.engine.setups.summarize_candidates` rather than a second tally — and an
  honest `"insufficient"` status when fewer than 2 tickers are on the watchlist.
- **Config surface** — new top-level `watchlist:` block in `config.yaml`
  (`xray.corr_window_days=126`, `xray.cluster_threshold=0.7`, `xray.min_overlap_days=60`) plus typed
  `WatchlistXrayCfg`/`WatchlistCfg` in `app/config.py`, wired into `Config` as
  `Field(default_factory=_default_watchlist)` — default-populated, so any config/fixture predating this
  key still loads unchanged.
- **Additive `xray` field on the existing `GET /api/watchlist`** (`app/api/watchlist.py`) — computed
  once alongside the existing response via `build_xray_payload`; the existing `asof_date` + `entries[]`
  shape stays byte-identical. No new endpoint, no schema change (computed on read only).
- **Frontend X-ray section on `/watchlist`** (`app/watchlist/page.tsx` + new
  `components/correlation-heatmap.tsx`) — a correlation matrix heatmap (NA cells rendered honestly,
  reusing the page's existing `text-pos`/`text-neg` sign tokens, never a new color scale), cluster
  badges, the headline "≈ N.N effective independent bets (over the last W trading days)" with an
  `InfoTooltip` explaining the methodology, and sector/theme/shared-setup concentration bars (the setup
  bars reuse the existing `setupVariant()` Badge coloring — the same mapping the entries table's Setup
  column already uses). Zero browser-side correlation/ENB recompute — the section reads the served
  `xray` payload verbatim. A watchlist with fewer than 2 names renders a distinct, honest "not enough
  names yet for an X-ray" `EmptyState` (different copy from the zero-entries state, same visual family).
- **`WatchlistXray` type family** added to `lib/api.ts` (`WatchlistXray`,
  `WatchlistXraySectorConcentration`, `WatchlistXrayThemeConcentration`, `WatchlistXraySetupConcentration`),
  and `WatchlistResponse` extended with the additive `xray` field.
- Backend unit/integration tests: the B-204 fixture (two perfectly correlated + one independent
  synthetic series -> ENB close to the hand-derived exact 1.8; two-name uncorrelated/correlated pairs
  hitting the exact [1,2] mathematical ENB bound), a pairwise-correlation spot-check against an
  independent offline computation, the `min_overlap_days` honesty floor (never a fabricated
  correlation), missing-bars handling (no crash), null-sector grouping (never dropped, never a crash),
  multi-membership theme concentration, the shared-setup reuse of `summarize_candidates`, determinism
  (byte-identical regardless of input ticker order), the additive-shape/byte-identity contract on
  `GET /api/watchlist`, and a no-proven/no-advice-language check on the served JSON.

## Files Changed

- `apps/backend/app/engine/concentration.py` (new) — `correlation_matrix()`, `effective_number_of_bets()`
- `apps/backend/app/engine/watchlist_xray.py` (new) — `build_xray_payload()` and its private helpers
- `apps/backend/tests/test_concentration.py` (new) — 14 tests, pure math, hand-derived exact values
- `apps/backend/tests/test_watchlist_xray.py` (new) — 10 tests, synthetic DB (no seed boot)
- `apps/backend/app/config.py` — added `WatchlistXrayCfg`, `WatchlistCfg`, `_default_watchlist()`;
  wired `watchlist: WatchlistCfg` into `Config`
- `config.yaml` — new top-level `watchlist.xray.{corr_window_days,cluster_threshold,min_overlap_days}`
- `apps/backend/app/api/watchlist.py` — `list_watchlist()` now attaches the additive `xray` field
- `apps/backend/tests/test_api_watchlist.py` — extended with 4 new tests (additive shape, `status: "ok"`
  with two real watchlist entries, no proven/advice language, determinism)
- `apps/frontend/lib/api.ts` — `WatchlistXray` + 3 sub-types; `WatchlistResponse.xray`
- `apps/frontend/components/correlation-heatmap.tsx` (new) — the matrix grid component
- `apps/frontend/app/watchlist/page.tsx` — `WatchlistXraySection` + `ConcentrationBars` local
  components, wired in below the existing entries table

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_concentration.py tests/test_watchlist_xray.py -v`
Result: 24 passed, 0 failed (0.07s + 1.32s — both files use synthetic/no-seed-boot DBs, no shared fixture cost)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_api_watchlist.py -v`
Result: INTERRUPTED (not run to completion) — this file shares the session-scoped `loaded_engine`
fixture (real committed seed + full historical cadence warm-up), which is slow by design on this
project's 30-year basis (see the "30y test suite slow, not the product" project convention); the
background run was still in fixture setup when reaped at a turn boundary. See the "Addendum" section
below for the independent live-verification evidence and why this is deferred to the reviewer's own run
rather than re-paying the ~28-minute fixture cost here.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_no_magic_numbers.py tests/test_config.py -q`
Result: 70 passed, 0 failed (fast, no DB dependency — confirms `config.yaml`/`config.py` changes are
valid and no calc-module literal was introduced)

Command: `cd apps/frontend && npx tsc --noEmit`
Result: exit 0, zero type errors

**Live end-to-end verification** (real production seed via `scripts/dev.sh`, backend :8255 / frontend
:3255): `GET /api/watchlist` against the persistent watchlist (MSFT, ABBV) returned a fully-populated
`status: "ok"` X-ray — correlation −0.114 between the two, `effective_number_of_bets = 1.9743`
(matches the exact closed-form 2-asset formula `2/(1+ρ²)` to 10+ significant digits), two singleton
clusters (correctly, since |−0.114| < the 0.7 cluster threshold), sector concentration (Technology 50%
/ null-sector 50%), three theme bars, and all-six setup-status concentration (Avoid 2 · 100%).
Temporarily added a third ticker (ARM) to confirm the 3-asset path (ENB ≈ 2.91, three singleton
clusters) and removed it afterward, restoring the watchlist to its prior state. The `/watchlist` page
rendered the full X-ray section correctly (matrix, ENB headline + working `InfoTooltip`, cluster
badges, concentration bars with the setup badge reusing `setupVariant()` coloring); zero console
errors. Regression spot-check: `/`, `/stocks`, `/evidence`, `/sectors`, `/research/factor-lab`, `/data`
and their backing `/api/*` endpoints all returned 200 after the config/watchlist changes.

## Known Issues

- The `test_api_watchlist.py` full-file run (which now includes 4 new tests alongside the ~9 pre-existing
  ones) takes several minutes because of the shared `loaded_engine` session fixture's real-seed
  historical-cadence warm-up — this is a pre-existing project characteristic (see
  `docs/handoffs/*-dev.md` history and the project's "30y test suite slow, not the product" note), not
  something introduced by this iteration. The new tests themselves add negligible incremental cost once
  the fixture is warm.
- Frontend lint (`npm run lint` / `next lint`) is not configured in this project (no `eslint.config.js`
  committed; running it launches an interactive first-time setup prompt) — pre-existing, not introduced
  or fixed by this iteration. `npx tsc --noEmit` was used instead as the correctness gate, and passed
  cleanly.
- No dedicated automated test asserts "exactly one `effective_number_of_bets` implementation exists in
  the codebase" (the DoD's `grep`-confirms-single-implementation line) — verified manually via
  `grep -rn "def effective_number_of_bets" apps/backend` (see verification below), not via a committed
  test, since there is no existing precedent in this codebase for a source-scanning pytest test outside
  `test_no_magic_numbers.py`'s narrow, purpose-built AST/tokenize scan.

## Addendum — full-file `test_api_watchlist.py` run interrupted (not a product issue)

The `cd apps/backend && .venv/bin/python -m pytest tests/test_api_watchlist.py -v` run referenced above
as "PENDING_FILL_IN" was backgrounded because it shares this file's pre-existing session-scoped
`loaded_engine` fixture (real committed seed + full 30-year historical-cadence warm-up — the same slow,
by-design fixture cost documented elsewhere in this project's handoff history). The run was still in its
fixture-setup phase (~28 minutes CPU time, no test output yet) when this session's turn paused between
tool calls; its background process was reaped at that boundary and no pass/fail result was captured.
Re-running the full file would re-pay the ~28-minute fixture cost for no new information, so per the
coordinator's direction it is deliberately NOT re-run here — the reviewer's independent
`test_api_watchlist.py` pass will confirm the 4 new additive tests
(`test_xray_field_is_additive_existing_shape_unchanged`, `test_xray_status_ok_with_two_watchlist_entries`,
`test_xray_no_proven_or_advice_language`, `test_xray_determinism_same_asof_repeated_calls`) alongside the
~9 pre-existing ones.

This does not leave the additive `GET /api/watchlist` behavior unverified. Before the pytest run was
launched, the same additive contract these 4 tests check was independently confirmed via a live
end-to-end pass against the real production seed (`scripts/dev.sh`, backend on :8255 / frontend on
:3255, persistent `apps/backend/data/trendora.db`):

- `GET /api/watchlist` with the persistent 2-entry watchlist (MSFT, ABBV) returned `xray.status == "ok"`
  with the existing `asof_date`/`entries[]` shape untouched and the new `xray` field additive alongside it.
- `effective_number_of_bets = 1.9743...` for the real MSFT/ABBV pair, matching the exact closed-form
  2-asset formula `2/(1+ρ²)` (ρ = the real −0.1141 correlation) to 10+ significant digits — independent
  numeric confirmation of the same code path `test_xray_status_ok_with_two_watchlist_entries` exercises.
- Temporarily added a third real ticker (ARM), confirmed the 3-name path (ENB ≈ 2.91, three singleton
  clusters), then removed it — restoring the watchlist to its prior state.
- `json.dumps` of the live response was manually scanned for the same banned proven/advice vocabulary
  `test_xray_no_proven_or_advice_language` checks — none present.
- Two consecutive `GET /api/watchlist` calls against the unchanged seed returned identical `xray`
  payloads (the same determinism property `test_xray_determinism_same_asof_repeated_calls` checks).
- The isolated, fast, non-`loaded_engine` suites already confirmed green in-session:
  `test_concentration.py` (14 passed), `test_watchlist_xray.py` (10 passed),
  `test_no_magic_numbers.py` + `test_config.py` (70 passed) — 94 tests total, 0 failed.

Net assessment: the underlying logic and the additive API contract are verified through two independent
channels (unit tests + live production-data E2E); only the FORMAL pytest confirmation of the 4 new
lines in `test_api_watchlist.py` is deferred to the reviewer's own run, which was already the next
pipeline step regardless.
