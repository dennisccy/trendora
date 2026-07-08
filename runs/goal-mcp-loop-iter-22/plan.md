# goal-mcp-loop-iter-22 Execution Plan

Target journey: **J-14** (deep, vendor-labeled index/macro context on the 30-year basis). Depth:
full. No `## Evidence Claim` — pure surfacing/disclosure change; the post-decompose gate passes
automatically (mirrors iter-20). `blueprint.md` already carries the "iter-22 clarification" note
(`runs/goal-session-mcp-loop/state/blueprint.md:220`) and the J-14 IA homes row (`:82`) — **no
blueprint edit needed**, same as iter-20's precedent.

**Alignment check:** directly implements the human-authored J-14 Must-have journey in `docs/goal.md`
and the iter-21 evaluator's #1 recommendation. No drift found. The spec's grounding claims were
independently re-verified against the live codebase this pass (see Corrected Grounding below) —
one factual correction and one internal inconsistency were found and are resolved below so the
developer doesn't lose a retry cycle to either.

## Corrected Grounding (verified live, differs from the spec's own grounding text)

The spec states "`^SPX`/`^NDX`/`^DJI`/`^VIX` (+ `^TNX`/`^DXY`/`^VXN`) are 0 rows" in `daily_prices`.
**A direct query of the live DB shows this is only true for `^SPX`/`^NDX`/`^DJI`:**

```
^SPX  (0,    None,         None)         <- needs loading
^NDX  (0,    None,         None)         <- needs loading
^DJI  (0,    None,         None)         <- needs loading
^VIX  (7675, '1996-01-02', '2026-07-01') <- ALREADY loaded (etfs.volatility)
^TNX  (1363, '2005-02-28', '2026-05-28') <- ALREADY loaded (macro.series proxy_symbol)
^DXY  (1357, '2021-01-04', '2026-05-28') <- ALREADY loaded (macro.series proxy_symbol)
^VXN  (1363, '2005-02-28', '2026-05-28') <- ALREADY loaded (macro.series proxy_symbol)
```
`^VIX` is already in `config.etfs.volatility`; the three FRED proxies are already reached via
`config.macro.series[].proxy_symbol` — both paths already flow through `all_seed_symbols`. **Only
`^SPX`/`^NDX`/`^DJI` are actually missing rows.** This shrinks the "load the deep series" task from
7 symbols to 3, and removes any reason to touch the already-correct `^VIX`/macro-proxy price rows.

**Why this matters (biggest risk this iteration):** `apps/backend/data/trendora.db` is gitignored
(`.gitignore:66`) — a local build artifact, 1.3 GB, 3,270,138 rows across 587 symbols, 410 snapshot
runs, ~165k `scanner_results` rows. `seed_loader.load_seed()` only (re)loads prices when the table is
EMPTY (`if existing and not force: return {"loaded": False, ...}`, `seed_loader.py:315`) — a normal
restart will NOT pick up the 3 new symbols. The data-manager `kind="rebuild"` job WIPES this DB and
reprocesses everything from scratch — iter-18's own dev handoff explicitly warns "Do NOT run
`kind=rebuild`" because it is multi-hour and destroys the 410 existing snapshot runs (the evidence
ledger's underlying historical data) unless a full backfill/warmup is re-run after. **Do not use
`kind=rebuild` for this iteration.** The correct fix is two-part:
1. **Permanent:** add the new symbols to config (`index_chart.symbols`). This alone is sufficient for
   any FUTURE fresh DB build (CI, a clean clone, or a deliberately deleted local DB) — `load_seed`
   naturally includes them via `all_seed_symbols`/`price_load_symbols` with zero special-casing.
2. **This-environment remediation:** the already-built local DB needs a small, additive, idempotent
   loader that inserts bars for ONLY the 3 missing symbols (`SeedProvider(seed_dir).get_daily(symbol)`
   per symbol, bulk-insert into `daily_prices`, guarded by a `SELECT COUNT(*)` pre-check per symbol so
   re-running it is a safe no-op) — touching nothing else in the DB. Sub-second cost, zero risk to the
   410 snapshot runs. Do not delete/recreate `trendora.db`.

## What to Build

- Add `^SPX` (Stooq), `^NDX` (Stooq), `^DJI` (Stooq) to `config.index_chart.symbols` with honest
  display names (e.g. "S&P 500 Index (^SPX)"). Do **not** add them to `etfs.index` (would make them
  scored/RS-benchmark candidates — anti-goal).
- **Resolve a spec-internal inconsistency, in the direction the DoD requires:** the "Backend IN
  SCOPE" bullet names only `^SPX`/`^NDX`/`^DJI` for `index_chart.symbols`, but DoD item (b) requires
  the chart legend/tooltip to show vendor labels spanning **all three** vendor categories ("Stooq /
  Yahoo / FRED-macro proxy") — which is only possible if at least one Yahoo-vendor series (`^VIX`)
  and one FRED-macro-proxy series (e.g. `^TNX`) are ALSO in `index_chart.symbols` (the only config
  surface that feeds `compute_index_series`'s per-series output). **Recommendation: add `^VIX` and
  one macro proxy alongside the three equity benchmarks** — all four already have bars loaded (no
  extra DB work), so this is a config-only addition that fully satisfies DoD (b) and (c) and J-14's
  "Stooq / Yahoo / FRED-macro proxy" disclosure acceptance in one pass. Document this resolution
  explicitly in the dev handoff so review/audit see it was a deliberate, DoD-driven call, not scope
  creep or an oversight. Give the FRED-macro-proxy entries an honestly-qualified display name (e.g.
  "10Y-2Y spread proxy (^TNX)") — never implying it is the real market ^TNX (anti-goal: a proxy is
  never presented as a market index).
- Targeted, idempotent load of `^SPX`/`^NDX`/`^DJI` bars into the local `daily_prices` (see risk above)
  — a small script or guarded function, not the `rebuild` job.
- `compute_index_series` (`apps/backend/app/engine/indexes.py`): add additive `vendor` and `first`
  fields per emitted series entry.
  - `vendor`: read via the ONE existing seed-meta reader, `data_manager.load_seed_windows`
    (`apps/backend/app/engine/data_manager.py:959`) — extend it (or add a sibling that shares its
    `meta.json` parse) to also expose `vendor`, keyed on the canonical `^`-symbol. Do not add a
    second raw `json.loads(meta.json)` call anywhere.
  - `first`: **must be the symbol's real first bar date from `meta.json`** (e.g. `^SPX` →
    `1996-01-02`), NOT `points[0]["date"]` — the latter is the RANGE-CLAMPED/rebased window start
    (e.g. ~3 months ago on the "3M" preset) and would silently violate DoD's byte-match requirement
    the moment a non-"all" range is selected. `load_seed_windows` already parses `first`/`last` per
    symbol from the same `meta.json` — reuse that value.
  - Symbols with no `meta.json` vendor record (SPY/QQQ/IWM/RSP/DIA) get `vendor: null` (the key is
    simply absent in `meta.json` for these — `.get("vendor")` naturally yields `None`, not a KeyError).
  - Existing SPY/QQQ/IWM/RSP/DIA `points` arrays must stay byte-identical (freeze/golden them).
- Frontend: render the vendor label on the chart legend/tooltip where present (nothing for `vendor:
  null`); add a new small `/data` vendor-disclosure panel reading the same `GET /api/indexes` payload
  (no re-parse of `meta.json`, no new `/api/data` field).
- **Fix a concrete, verified UI defect this change would otherwise trigger:** `index-regime-chart.tsx`
  cycles only **5** color tokens (`LINE_PALETTE_VARS`, line 39: `--accent, --pos, --warn, --neg,
  --text-muted`), assigned by `index % 5` (`lineColorVar`, line 41). Today's 5 configured ETFs map
  1:1 with no collision. Adding 3-5 more series pushes indices 5-8+ into a modulo wrap that REUSES
  colors 0-2 — e.g. SPY (index 0, `--accent`) and the 6th series (index 5, `--accent` again) would
  render as visually identical lines/legend swatches. Extend the palette to enough perceptually
  distinct tokens for the new total series count (consult the `dataviz` skill's categorical-palette
  method) before shipping the extra lines, or the DoD's own screenshot evidence will show a
  color collision.

## Agents Required

- backend-data: yes -- `config.yaml` (`index_chart.symbols`), `apps/backend/app/engine/indexes.py`
  (`compute_index_series` additive fields), `apps/backend/app/engine/data_manager.py` (extend/wrap
  `load_seed_windows` for vendor), a targeted idempotent loader for the 3 missing symbols, and the
  backend test updates below.
- frontend-ux: yes -- `apps/frontend/lib/api.ts` (additive `IndexSeries` fields),
  `apps/frontend/components/index-regime-chart.tsx` (vendor label + color-palette fix),
  `apps/frontend/app/data/page.tsx` (new vendor-disclosure panel, placed after the existing
  `MacroFeedPanel`).

Frontend Present: yes

## Files to Create/Modify

Backend:
- `config.yaml:298-304` -- add `^SPX`/`^NDX`/`^DJI` (+ recommended `^VIX` + one macro proxy) entries
  to `index_chart.symbols` with honest display names; leave `etfs.index` untouched.
- `apps/backend/app/engine/indexes.py` -- `compute_index_series`: add `vendor`/`first` to each
  `series` entry; source both from the seed-meta reader, never from `points`.
- `apps/backend/app/engine/data_manager.py:959` (`load_seed_windows`) -- extend to also return
  `vendor` per symbol (or add a small sibling reader sharing its `meta.json` parse). Update its one
  existing caller/test if the return shape changes shape rather than gaining a second value.
- New: a small targeted/idempotent price loader for the 3 missing symbols (script under
  `apps/backend/scripts/` or a guarded function near `load_prices`) — reusable if the local DB is
  ever rebuilt again before a fresh-clone environment naturally picks the config change up.
- `apps/backend/tests/test_indexes.py` -- extend: new deep series appear when loaded; each carries
  correct `vendor` (from `meta.json`) and honest `first` (byte-matches `meta.json`, independent of
  the selected range); existing SPY/QQQ/IWM/RSP/DIA `points` stay byte-identical (freeze/golden);
  vendor mapping `stooq`→"Stooq", `yahoo`→"Yahoo", `fred-macro-proxy`→"FRED-macro proxy"; a symbol
  with no meta vendor record → `vendor: null`.
- `apps/backend/tests/test_api_indexes.py` -- API-level smoke for the additive fields (unchanged
  status codes/shape otherwise).
- `apps/backend/tests/test_data_manager.py::test_load_seed_windows_and_is_seed_bar` -- update for
  whatever shape change `load_seed_windows` gains.

Frontend:
- `apps/frontend/lib/api.ts:459-463` (`IndexSeries`) -- add `vendor: string | null` and `first:
  string` (additive/optional so no existing typed consumer breaks).
- `apps/frontend/components/index-regime-chart.tsx` -- `IndexLegend` (~line 258-280): render the
  vendor label next to/under the symbol name where `vendor` is non-null; tooltip: same. `line 39`
  `LINE_PALETTE_VARS`: extend to avoid the collision described above.
- `apps/frontend/components/major-indexes-card.tsx` -- verify it passes the additive fields through
  unchanged (likely no edit needed; it forwards `indexes.series` as-is to `IndexRegimeChart`).
- `apps/frontend/app/data/page.tsx` (~after line 468, following `<MacroFeedPanel .../>`) -- add a new
  vendor-disclosure panel (new component, e.g. `components/index-vendor-panel.tsx` or inline)
  fetching `fetchIndexes(...)` and listing each `series[]` entry with a `vendor` value (Stooq /
  Yahoo / FRED-macro proxy) + its honest `first` date; a `fred-macro-proxy` entry must read as
  exactly that, never as a market index.
- `docs/handoffs/goal-mcp-loop-iter-22-dev.md` + `-frontend.md` -- dev handoffs (DoD requirement).

**No `blueprint.md` edit** — already carries the iter-22 clarification (verified present at
`runs/goal-session-mcp-loop/state/blueprint.md:220`).

## UI Evolution

- New user-facing capability: the Dashboard's major-indexes chart shows deep equity-benchmark lines
  (`^SPX`/`^NDX`/`^DJI`) reaching back to 1996, beyond the ETFs' ~2005/1999 floors.
- New information displayed: a per-series vendor label (Stooq / Yahoo / FRED-macro proxy) on the
  chart legend/tooltip, an honest first-bar date per series, and a new `/data` panel listing the same
  per series.
- New user actions: none — existing range/hover controls only.
- UI surface changes: Dashboard `/` major-indexes & regime card (more lines + vendor labels); `/data`
  gains one new small disclosure panel.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `Card`/legend patterns already on the Dashboard chart and
  `/data` (mirror `MacroFeedPanel`'s card structure for the new vendor panel) — no new component
  library primitive.
- Layout: unchanged page structure; the new `/data` panel slots into the existing single-column panel
  stack right after `MacroFeedPanel`.
- Key visual effects: none new. The one required visual fix is the line-color palette extension
  described above (dataviz skill: pick perceptually distinct hues for however many series can render
  simultaneously, not just "not identical to its modulo neighbor").
- States to handle: chart keeps its existing loading/ok/empty/error states (`major-indexes-card.tsx`
  lines ~128-159) unmodified; the new `/data` panel needs its own honest loading/error/empty (API
  unreachable → honest "could not load," never a blank/fabricated row), matching the surrounding
  panels' convention.

## Key Test Scenarios

**Unit/integration (backend)** — run scoped, not the full suite (project convention: full pytest is
~10-11h on the 30-year basis and fork-locks the box; clear `/tmp/pytest-of-*` first if disk is tight):
`cd apps/backend && .venv/bin/python -m pytest tests/test_indexes.py tests/test_api_indexes.py tests/test_data_manager.py -v`
- New deep series appear once loaded; each carries the correct `vendor` + honest `first`
  (byte-matches `meta.json`, e.g. `^SPX` → `1996-01-02`, independent of the selected range preset).
- Existing SPY/QQQ/IWM/RSP/DIA `points` are byte-identical before/after (frozen/golden).
- A configured symbol with no bars (still-honest DIA-style omission) and a symbol with no meta
  vendor record (`vendor: null`, no fabricated vendor) both degrade honestly.
- `load_seed_windows` (or its extended sibling) still passes its existing test with the new shape.
- Load-scope: `^SPX`/`^NDX`/`^DJI` are absent from the scored universe/leaderboard (`etfs.index`
  untouched) — a quick `/stocks` count / universe-count sanity check, not a full re-run of J-01/J-12
  (that's the browser replay's job).

**Frontend**: `cd apps/frontend && npx tsc --noEmit` clean; if any vendor/color logic is factored into
a small pure function, it can follow the existing `lib/*.test.ts` convention (no new test framework —
this project has none installed, per iter-20's precedent finding).

**Browser (canonical browser-qa-agent lane, live, prod-mode services on `:3255`/`:8255`,
`rm -rf apps/frontend/.next` first per iter-20/21 lesson):**
- J-14 (target): Dashboard major-indexes chart shows a deep line (`^SPX`) extending before SPY's 2005
  start; the chart legend/tooltip shows vendor labels spanning Stooq/Yahoo/FRED-macro-proxy; `/data`'s
  new panel lists each series' vendor + first-bar date.
- Regression replay (required-still-passing, live not code-inspected): J-01 (`/stocks` no leaked
  index rows, no crash), J-03 (all "Not yet proven" — no new "Proven" leaked by this change), J-04
  (Dashboard regime label/evidence affordance intact after the chart gains lines), J-05 (`/evidence`
  ledger unaffected), J-10 (`/stocks/{ticker}` deep-history chart + `/backtest`), J-12 (`/data`
  "Universe" count == `/stocks` count, unchanged by the new index/macro symbols), J-13 (`/data`
  availability legend + 548 reflection unchanged).
- Screenshot hygiene (recurring lesson): scroll the chart legend and the `/data` panel into frame;
  full-page or element-clip captures; `md5sum` every PNG so the three DoD assertions ((a)/(b)/(c))
  aren't satisfied by one relabeled screenshot.
- If a required-still-passing replay's golden script asserts the exact prior major-indexes legend
  set, the added deep-benchmark lines are an INTENDED additive change — refresh the stale assertion,
  don't treat it as a regression (iter-21 lesson).

## Risks and Mitigations

1. **Destructive DB rebuild** (by far the highest-stakes risk this iteration) — see Corrected
   Grounding above. Mitigation: targeted 3-symbol additive load only; never `kind=rebuild`; verify
   row counts before/after for all 587 pre-existing symbols are unchanged and `scanner_results`
   count (~165,670) is unchanged.
2. **Vendor-symbol config scope ambiguity** — the literal "IN SCOPE" bullet names only 3 symbols, but
   DoD (b) requires all three vendor categories visible on the chart legend. Mitigation: the
   recommended resolution above (add `^VIX` + one macro proxy too, all already loaded) — document the
   choice explicitly in the dev handoff so reviewer/audit don't flag it as an unexplained scope change.
3. **Line-color palette collision** once more than 5 series render simultaneously (verified defect,
   `index-regime-chart.tsx:39,41`) — mitigation above.
4. **FRED-macro-proxy naming honesty** — a display name for `^TNX`/`^DXY`/`^VXN` must not read as the
   real market ticker (anti-goal: never present a proxy as a market index); qualify it in the name
   itself, not just the vendor badge, since a user could otherwise assume "^TNX" on a chart legend is
   the literal 10-year Treasury yield.
5. **`first` sourced from the wrong place** — must come from `meta.json`, not `points[0].date` (which
   is range-clamped); a naive implementation passes casual testing on the "all" preset and silently
   fails DoD's byte-match check on any other preset. Call this out explicitly in code review.
6. **Byte-identical existing lines is a hard constraint** (anti-goal #3) — a git diff/test on the
   existing SPY/QQQ/IWM/RSP/DIA computation path must show no numeric change, only additive fields +
   additional entries.
7. **Scope-creep guards**: do not touch `MacroFeedPanel`'s own computation/endpoint (`/api/data`
   `macro` stays as-is — only the new panel reads `/api/indexes`); do not re-fetch `^TNX`/`^DXY`/`^VXN`
   from Yahoo (goal.md §H forbids it — they stay the committed deterministic FRED proxies); do not
   touch the Regime VIX-gate; do not attempt J-15/J-16 (fast-platform perf) or any evidence
   re-certification (separate, already-sequenced iterations).

## Out of Scope

- Evidence re-certification (J-02/J-06/J-07/J-08/J-09) — separate discovery iteration, per spec.
- Fast-platform perf budgets (J-15/J-16) — separate iteration.
- Re-fetching `^TNX`/`^DXY`/`^VXN` from Yahoo — forbidden by goal.md §H.
- Any change to the FRED macro catalog / `MacroFeedPanel` computation (`/api/data` `macro` value).
- Regime VIX-gate behavior (pre-existing, not J-14).
- Any intra-series vendor splice; adding the deep indices to `etfs.index` or any scoring/RS/universe
  path.
- Any `## Evidence Claim` / referee submission / ledger write (none is warranted — pure
  surfacing/disclosure of already-committed, already-vendor-tagged data).
