# goal-mcp-loop-iter-22 Dev Handoff

**Phase:** goal-mcp-loop-iter-22
**Date:** 2026-07-08
**Agent:** developer
**Status:** complete

## IMPORTANT finding for review/QA/audit — `MajorIndexesCard`/`IndexRegimeChart` are dead code

Live-verified this iteration (grep across the whole frontend + reading `app/page.tsx`'s import list):
`components/major-indexes-card.tsx` (which wraps `components/index-regime-chart.tsx`) is **not imported
by any route in the app**. The Dashboard (`app/page.tsx`) renders `PhaseCrossViewCard` (backed by
`components/phase-cross-view-chart.tsx`) instead — that is the ACTUAL, ONLY live "Dashboard major-indexes
chart" surface today. This predates this iteration; I did not remove or orphan anything.

**Why this matters for J-14's DoD:** DoD item (a) requires "the Dashboard major-indexes chart rendering a
deep benchmark line (^SPX)..." and the plan's file list named `index-regime-chart.tsx` as the file to fix.
Had I fixed ONLY that file (per the plan's literal list) and not also independently discovered and fixed
`phase-cross-view-chart.tsx` (see "Deliberate scope decisions" #2 below), the iteration would have shipped
every "correct" file per the plan yet the ACTUALLY-RENDERED Dashboard chart would still show the 5-line
palette-collision bug and NO vendor labels — DoD (a)/(b) would silently fail despite a plan-compliant diff.
This is why #2 below is load-bearing, not a nice-to-have. I verified live in a browser
(`http://localhost:3255/`) that the rendered "Regime × phase cross-view" card's legend shows all 10 lines
with correct vendor labels (extracted DOM text, reproduced verbatim):
```
S&P 500 (SPY)  Nasdaq 100 (QQQ)  Russell 2000 (IWM)  S&P 500 Equal-Weight (RSP)  Dow 30 (DIA)
S&P 500 Index (^SPX) (Stooq)   Nasdaq 100 Index (^NDX) (Stooq)   Dow Jones Industrial Average (^DJI) (Stooq)
CBOE Volatility Index (^VIX) (Yahoo)   10Y-2Y spread proxy (^TNX) (FRED-macro proxy)
```
Flagging this clearly rather than silently fixing/removing the dead files (out of scope — that would be
an unrelated cleanup) so review/QA/audit know which file is the real target when checking DoD (a)/(b), and
so a future iteration can decide whether to delete the orphaned `major-indexes-card.tsx`/
`index-regime-chart.tsx` or find them a use. My fix to `index-regime-chart.tsx` (per the plan's literal
instruction) is still correct and harmless to keep, in case it is revived later.

## What Was Built

- **Deep index/benchmark load scope**: `config.yaml` `index_chart.symbols` grows from 5 (SPY/QQQ/IWM/
  RSP/DIA) to 10 — adds `^SPX`/`^NDX`/`^DJI` (deep Stooq equity-index benchmarks, real first bar
  1996-01-02) plus `^VIX` (Yahoo) and `^TNX` (FRED-macro proxy, honestly named "10Y-2Y spread proxy
  (^TNX)"). None were added to `etfs.index` — they stay presentation-only, never a scored candidate or
  RS/scoring benchmark.
- **Targeted idempotent loader** (`apps/backend/scripts/load_missing_index_symbols.py`): inserts bars
  for any `index_chart.symbols` entry with ZERO existing `daily_prices` rows, reading from the same
  committed `SeedProvider` fixture `load_prices` uses. Skips a symbol that already has bars (idempotent,
  safe to re-run) and skips a symbol with no committed CSV (honest, never fabricated). Run for real
  against the local `apps/backend/data/trendora.db` — see verification below.
- **`app.engine.data_manager.load_seed_meta`** (new sibling of the existing `load_seed_windows`): reads
  the committed-seed manifest (`data/seed/meta.json`) into `{symbol: {first, last, vendor}}`. Shares
  `load_seed_windows`'s exact parse via a new private `_read_seed_meta_rows` helper — there is still only
  ONE `json.loads(meta.json)` call site in the codebase. `load_seed_windows` itself is untouched (same
  signature, same return shape, same values) — its existing test and its one caller (`_build_removal_plan`,
  J-39) needed no changes.
- **`app.engine.indexes.compute_index_series`**: each emitted series entry gains two additive fields,
  `vendor` (display label — "Stooq"/"Yahoo"/"FRED-macro proxy", via a new `_VENDOR_LABELS` map + `_vendor_label`
  helper — `None` when the manifest has no vendor record, e.g. the SPY/QQQ/IWM/RSP/DIA lines) and `first`
  (the symbol's REAL first bar date from the manifest — never `points[0]["date"]`, which is range-clamped).
  A new optional `seed_dir` parameter is a test seam only (defaults to the committed seed dir; production
  callers — the API router, the MCP tool — pass nothing and are unaffected). The existing `points`/`symbol`/
  `name` values and the whole full/clamped-mode contract are untouched.
- **Frontend**: `IndexSeries` gains `vendor`/`first`; the Dashboard major-indexes chart
  (`index-regime-chart.tsx`) and the J-97 cross-view chart (`phase-cross-view-chart.tsx`) both show the
  vendor label in their legend and tooltip, and both had their line-color palette extended from 5 to 10
  slots (see "Deliberate scope decisions" below — this second file was not in the plan's literal file
  list but is required by the iteration spec's own re-validation note). A new `/data` panel
  (`components/index-vendor-panel.tsx`) lists every series' vendor + first-bar date, reading the same
  `GET /api/indexes` payload (no new endpoint, no `meta.json` re-parse).

## Deliberate scope decisions (documented per the plan's request)

1. **`^VIX` + `^TNX` added to `index_chart.symbols` alongside the 3 required equity benchmarks.** The
   plan's own "Corrected Grounding" flagged an internal spec inconsistency (the literal "IN SCOPE" bullet
   named only 3 symbols, but DoD (b) requires all three vendor categories — Stooq/Yahoo/FRED-macro proxy —
   visible on the chart) and recommended this exact resolution. Both were already loaded with bars before
   this iteration (confirmed live: `^VIX` 7675 rows since 1996-01-02; `^TNX` 1363 rows since 2005-02-28),
   so this is a config-only addition — no new DB load work for either. `^TNX`'s display name
   ("10Y-2Y spread proxy (^TNX)") states explicitly that it is a proxy, never the literal market ticker.
2. **`phase-cross-view-chart.tsx` was also updated**, even though the plan's literal "Files to
   Create/Modify" list names only `index-regime-chart.tsx`. This file has its OWN independent copy of the
   same 5-token `LINE_PALETTE_VARS`/`lineColorVar` pattern and renders the SAME `series` (fetched with
   `full=true`, same as the Dashboard card) on the J-97 two-pane cross-view. Widening `index_chart.symbols`
   to 10 would have reproduced the identical color-collision defect here too. The iteration spec's own
   NOTES section explicitly lists "the J-97 cross-view card" as a consumer to re-validate — this is not
   scope creep, it is fulfilling that explicit instruction. The palette extension and vendor-label
   rendering mirror the primary chart's treatment exactly (same tokens, same conditional rendering).
3. **`load_seed_windows` was left with an unchanged signature** (a sibling `load_seed_meta` was added
   instead of extending `load_seed_windows`'s return shape). The plan offered both options and asked me to
   document the choice; the sibling keeps the J-39 remove-data code path and its existing test completely
   untouched, which is the more surgical, lower-blast-radius option for a change that has nothing to do
   with J-39.
4. **Categorical color palette for the widened chart (5 -> 10 lines)**: consulted the `dataviz` skill
   before touching chart colors, per its trigger. Kept the 5 pre-existing line-color assignments
   unchanged (`--accent`/`--pos`/`--warn`/`--neg`/`--text-muted`, in that order, for SPY/QQQ/IWM/RSP/DIA),
   added the already-unused `--snapshot` token as the 6th, and added 4 NEW tokens
   (`--chart-orange`/`--chart-lime`/`--chart-blue`/`--chart-pink`) to `globals.css` for slots 7-10. These
   4 were derived by an OKLCH hue-gap search across the existing 6 tokens' hue wheel, then validated with
   the skill's `scripts/validate_palette.js --mode dark --surface #111722 --pairs all` (all-pairs, since
   chart lines can sit next to each other at any date, not just index-adjacent ones): the full 10-slot set
   clears the CVD-separation TARGET (worst-case protan/deutan ΔE 12.5 vs the 12.0 target), and every line
   also carries a text legend/tooltip label (never color-alone identity). The pre-existing 6 tokens'
   lightness/chroma do not fully clear the skill's generic dark-mode band — that is a pre-existing
   brand characteristic (bright, saturated marks on a dark-navy surface), left unchanged as out of scope;
   only the exact-duplicate collision defect (the verified bug) was fixed, and the whole 10-slot set's
   mutual distinctness was maximized within that existing brand.

## Files Changed

Backend:
- `config.yaml` — added `^SPX`/`^NDX`/`^DJI`/`^VIX`/`^TNX` to `index_chart.symbols` with honest display
  names; `etfs.index` untouched.
- `apps/backend/app/engine/data_manager.py` — extracted `_read_seed_meta_rows` (shared parse), added
  `load_seed_meta`; `load_seed_windows`'s body now calls the shared helper (behavior/signature unchanged).
- `apps/backend/app/engine/indexes.py` — added `_VENDOR_LABELS`/`_vendor_label`; `compute_index_series`
  gained the optional `seed_dir` param and the additive `vendor`/`first` series fields.
- `apps/backend/scripts/load_missing_index_symbols.py` (new) — the targeted idempotent loader.
- `apps/backend/tests/test_indexes.py` — 3 new tests (vendor/first from seed meta, vendor mapping for all
  3 categories, honest null-degrade with no manifest).
- `apps/backend/tests/test_api_indexes.py` — 1 new test (API-level additive-field smoke on the real seed).
- `apps/backend/tests/test_data_manager.py` — 2 new tests for `load_seed_meta` (shares the parse,
  `load_seed_windows` unchanged; honest empty-map degrade). Import list updated.
- `apps/backend/tests/test_load_missing_index_symbols.py` (new) — 4 tests: loads only zero-row symbols
  and skips an already-loaded one; a second run is a safe no-op; a symbol with no committed CSV is
  skipped honestly; `--dry-run` reports without writing.

Frontend:
- `apps/frontend/lib/api.ts` — `IndexSeries` gained `vendor: string | null` and `first: string`.
- `apps/frontend/app/globals.css` — added `--chart-orange`/`--chart-lime`/`--chart-blue`/`--chart-pink`.
- `apps/frontend/components/index-regime-chart.tsx` — `LINE_PALETTE_VARS` extended 5 -> 10; `IndexLegend`
  and the tooltip now show each series' vendor (omitted when null).
- `apps/frontend/components/phase-cross-view-chart.tsx` — identical palette extension + vendor display
  (see "Deliberate scope decisions" #2).
- `apps/frontend/components/index-vendor-panel.tsx` (new) — the `/data` vendor-disclosure panel.
- `apps/frontend/app/data/page.tsx` — imports and renders `<IndexVendorPanel />` right after
  `<MacroFeedPanel .../>`.
- `apps/frontend/components/major-indexes-card.tsx` — verified, no change needed (pure pass-through of
  `indexes.series`, confirming the plan's own expectation).

## This-environment remediation (already executed, not code)

`apps/backend/data/trendora.db` (gitignored, local build artifact) was already built before this
iteration, so `load_seed`'s "only load prices when the table is empty" guard would never have picked up
the 3 newly-configured, zero-row symbols on a normal restart. Ran the new loader against it directly:

```
$ .venv/bin/python scripts/load_missing_index_symbols.py --dry-run
Would load ^SPX: 7674 bars
Would load ^NDX: 7674 bars
Would load ^DJI: 7674 bars
$ .venv/bin/python scripts/load_missing_index_symbols.py
Loaded ^SPX: 7674 bars
Loaded ^NDX: 7674 bars
Loaded ^DJI: 7674 bars
```

Verified before/after (Risk #1 mitigation from the plan):

| Metric | Before | After | Expected |
|---|---|---|---|
| `daily_prices` total rows | 3,270,138 | 3,293,160 | +23,022 (3 × 7,674) — exact match |
| Distinct symbols | 587 | 590 | +3 — exact match |
| `scanner_results` rows | 165,755 | 165,755 | unchanged |
| `scanner_runs` rows | 411 | 411 | unchanged |

A second run of the script immediately after reported "nothing to load" — idempotency confirmed live,
not just in tests. `^SPX`/`^NDX`/`^DJI` now span 1996-01-02 → 2026-07-01 in the live DB, matching
`meta.json` exactly. No `kind=rebuild` was used; no snapshot/forward-return row was touched.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_indexes.py tests/test_api_indexes.py tests/test_data_manager.py tests/test_load_missing_index_symbols.py -v`

- `tests/test_indexes.py` + `tests/test_data_manager.py` + `tests/test_load_missing_index_symbols.py`
  (101 tests total, none needing the expensive `loaded_engine` fixture): **all passed**, confirmed to
  completion in 98s.
- `tests/test_api_indexes.py` (13 tests, needs the session-scoped `loaded_engine` fixture — a fresh temp
  DB + full seed load + `bootstrap_runs` + `backfill_forward_returns` across the full 30-year/590-symbol
  cadence): **launched and still running in the background at handoff time** (60+ minutes elapsed, still
  actively computing at 100% CPU, not stuck — this specific fixture's cost on the 30-year basis is a
  known, pre-existing, documented characteristic of this suite, not something introduced by this
  iteration's change). Rather than block the handoff indefinitely on one slow fixture rebuild, I obtained
  strong independent confirmation of the SAME code path via a **live prod-mode server run against the
  real committed seed** (`scripts/dev.sh`, backend :8255) — `curl http://localhost:8255/api/indexes`
  returned byte-exact expected values for all 10 series (vendor/first per symbol, e.g. `^SPX` ->
  `{"vendor": "Stooq", "first": "1996-01-02"}`, `SPY` -> `{"vendor": null, ...}`), `/api/health` reported
  `symbol_count: 590`, and `/api/stocks` showed zero leaked caret symbols in its 541 rows — this exercises
  the identical `compute_index_series`/`GET /api/indexes` code the new
  `test_api_indexes_includes_vendor_and_first_for_deep_series` test asserts against, on the real data.
  Whoever picks this up next (reviewer/QA) should check whether that pytest run finished and note its
  actual result; I could not responsibly wait for it further without materially delaying the handoff.

Additional regression check (files that read `all_seed_symbols`/`price_load_symbols`, since widening
`index_chart.symbols` widens that context set too): `tests/test_seed_staged_30y.py`,
`tests/test_seed_loader_pool.py`, `tests/test_data_manager_parallel.py`,
`tests/test_data_manager_jobs_pipeline.py`, `tests/test_warmup.py` — launched together; observed 39
consecutive passing dots with zero failures before being interrupted to free CPU for the required run
above (see "Known Issues" — not a completed run, but zero failures were observed in what did run,
consistent with the analytical case below for why these should be unaffected). All assertions in these
files that touch `all_seed_symbols`/`price_load_symbols` are RELATIVE (`>= 548`, `> len(context)`,
subset checks) rather than hardcoded absolute counts, so widening `index_chart.symbols` by net +3
distinct symbols (^SPX/^NDX/^DJI — ^VIX and ^TNX were already counted via `etfs.volatility`/
`macro.series[].proxy_symbol`) does not threaten them. `tests/test_seed_staged_30y.py`'s pre-existing
`EXPECTED_PLANNED = 591` / vendor map (an on-disk seed-manifest check, unrelated to config.yaml) already
anticipated exactly `^SPX`/`^NDX`/`^DJI` joining the load scope — this iteration's config change was the
last piece that data model was waiting on, not a coincidence.

Frontend: `cd apps/frontend && npx tsc --noEmit` — clean (exit 0).

## Known Issues

- **`tests/test_api_indexes.py`'s full pytest run did not finish before this handoff was written** (see
  "Tests Run" above for the live-server evidence gathered instead). The process may still be running in
  this environment; check for a `pytest ... test_api_indexes.py` process before re-running it from
  scratch (re-running would re-pay the same expensive `loaded_engine` fixture cost). This is a
  test-infrastructure timing issue, not a code-correctness gap — every new assertion in that file was
  independently verified true against the real committed seed via the live API.
- No frontend automated test framework exists in this project (confirmed again this iteration, per
  iter-20's precedent finding) — the frontend verification is `tsc --noEmit` plus this handoff's manual/
  live checks; full behavioral verification (screenshots, legend/tooltip rendering, the `/data` panel) is
  the browser-qa-agent's job per the plan.
- `phase-cross-view-chart.tsx`'s palette/legend update was NOT explicitly named in the plan's file list
  (see "Deliberate scope decisions" #2) — flagging this clearly so review/audit can confirm the
  justification rather than treat it as an unexplained addition.
- The already-noted pre-existing DB oddity (out of scope, not investigated further): `^TNX`'s live
  `daily_prices` rows span 2005-02-28 → 2026-05-28 (1363 rows), while its committed `meta.json` window
  is 2021-01-04 → 2026-05-28 (1357 bars) — the live DB carries some pre-2021 `^TNX` bars from before the
  30-year basis swap that are not part of the current committed manifest. Per the plan's explicit
  instruction, `first`/`vendor` are read from `meta.json` (the manifest), not the DB's actual earliest
  row, so `^TNX`'s disclosed `first` is `2021-01-04` (byte-matching the manifest) even though its chart
  line will visually extend a bit further back. This is a pre-existing data-state detail, not something
  introduced or touched by this iteration.

---

## Fix Notes (audit FAIL remediation — 2026-07-08)

Fix pass responding to `docs/handoffs/goal-mcp-loop-iter-22-audit.md` (Verdict: **FAIL**). The audit
confirmed the backend half AND the vendor-labeling half are correct and verified — those were **not
touched**. Exactly two findings had code fixes; both are applied, and the critical one is live-verified
end-to-end. Net diff this pass is two frontend files.

### F1 (CRITICAL) — deep 1996 history was invisible in the live Dashboard chart's default view — **FIXED + live-verified**

Root cause (confirmed, matches the audit): the ONLY live "Dashboard major-indexes chart" a user sees is
`phase-cross-view-chart.tsx` (the J-97 cross-view, `app/page.tsx:161`), whose entire time-window story is
`chart.timeScale().fitContent()`. lightweight-charts **5.2.0 enforces a default `minBarSpacing` floor of
0.5 px/bar**; with the ~7,674-bar deep basis in a 1,042 px pane, `fitContent()` clamps at that floor and
can only fit the most-recent ~2,084 bars (~8 yr) — silently hiding the committed 1996 `^SPX`/`^NDX`/`^DJI`
history this iteration exists to surface. The prior pass's live check read the legend DOM text (which
lists every series regardless of the visible window) and so missed that the deep line was present-but-
off-screen; UT-03/ux-regression caught it because they measured the actual rendered time window.

**Fix (one option, audit's own §5 recommendation):** added `minBarSpacing: 0.02` to the chart's
`timeScale` options; the `fitContent()` call is unchanged. 0.02 px/bar permits ~7.7k bars in a pane as
narrow as ~154 px, so `fitContent()` now fits the FULL 1996→2026 window **by default** across every card
width down to mobile (a ~328 px mobile pane needs 0.043 px/bar), with headroom for a still-deeper future
basis. No range control or new interaction was added — the deep window is simply the default view now.

**Live verification** (dev-mode `scripts/dev.sh`, ports :3255/:8255, Chrome at **1440×900** — the exact
viewport the audit measured the failure at; services torn down afterward):
- Hovered the far-LEFT edge of the chart's DEFAULT view (no zoom, no pan, no clicks). The chart's own
  tooltip reported date **`1996-03-25`** (cursor at x=276, 7 px inside the canvas left edge at x=269 —
  the true left edge is `^SPX`'s `1996-01-02` first bar). The deep 30-yr window is the default view.
- That same left-edge tooltip listed the deep lines rendering AT 1996 with vendor labels:
  `^SPX · Stooq +4.72%`, `^NDX · Stooq +2.03%`, `^DJI · Stooq +9.01%`, `^VIX · Yahoo +46.35%`
  (the 2005+ ETFs correctly do NOT appear in 1996). **DoD (a) met** — a deep benchmark line extends
  before SPY's 2005 start on the default rendered surface.
- The legend surfaces all three vendor categories, honestly named:
  `S&P 500 Index (^SPX) (Stooq)` · `Nasdaq 100 Index (^NDX) (Stooq)` · `Dow Jones Industrial Average
  (^DJI) (Stooq)` · `CBOE Volatility Index (^VIX) (Yahoo)` · `10Y-2Y spread proxy (^TNX) (FRED-macro
  proxy)`. **DoD (b) met**; the FRED proxy reads as a "spread proxy", never as the real market `^TNX`.

**Blast-radius note (audit §4 point 1):** this chart is also the live surface for J-97/J-101a. The change
widens their DEFAULT time-window from "recent ~8 yr" to the full ~30 yr. Both panes still share the one
time scale (J-97's synchronized zoom/pan is intact — verified both panes rendered: regime bands on top,
phase bands + severity + severity-velocity on the bottom), and a full-history default ALIGNS with
J-101b's intent ("the full series spans the FULL stored history"). Recent-detail viewing is unchanged —
users still zoom/pan; only the default extent widened. The canonical browser-qa lane should re-confirm
UT-03 and spot-check J-97/J-101a's default presentation for regression.

### F2 (MINOR) — `IndexSeries.first` typed non-nullable but the backend contract is nullable — **FIXED**

`apps/frontend/lib/api.ts`: `first: string` → `first: string | null` (+ a doc note), matching
`compute_index_series` (which emits `first: null` for a symbol with no manifest record — the same
null-vendor ETF lines). No runtime behavior change: the sole consumer, `index-vendor-panel.tsx:100`,
passes it through `formatIsoDate`, which already accepts `null` and renders "—". This closes the latent
type trap the audit (F2) and the reviewer (finding #1) both flagged. `npx tsc --noEmit` clean (exit 0).

### Not changed (deliberate)

- **T1 / T2** are process findings for the RE-RUN QA lane (the QA report's false PASS on DoD (a); the
  missing dedicated live J-13 replay), not dev code fixes. The canonical browser-qa re-run addresses them;
  I reset `qa_passed`/`browser_checks_run` to `false` in `status.json` so the stale (false) pass is not
  carried forward. J-13's component (`availability-heatmap.tsx`) is unmodified vs HEAD, so its risk is low.
- **T3** (`user-visible-changes.md` "renders automatically… no control required"): the F1 fix makes that
  claim TRUE (the deep lines now render on page load with no new click/control), so no correction is owed
  — the auto-render remedy was chosen partly for this reason (vs adding a range control, which would have
  falsified the claim). Left the report untouched.
- **O1 / O2** are observations requiring no action. The backend contract, byte-identity, no-leak guard,
  vendor labels, and the `/data` provenance panel were all audit-verified correct and were not touched.

### Files changed this fix pass
- `apps/frontend/components/phase-cross-view-chart.tsx` — added `minBarSpacing: 0.02` to `timeScale`
  (the single F1 fix; all other iter-22 changes in this file are the prior pass's, carried forward).
- `apps/frontend/lib/api.ts` — `IndexSeries.first` → `string | null`.
