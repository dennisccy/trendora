# goal-mcp-loop-iter-27 Execution Plan

## Context (do not re-diagnose)

iter-26 shipped a correct, byte-identity-gated scoring-window feature (`indicators.max_lookback_bars`,
committed `320`) — **out of scope, do not rebuild**. It was scored **REGRESSION**: driving J-16's own
"Rebuild snapshots for current universe" job (322 dates × 541 members) crashed the backend with
`MemoryError` at `apps/backend/app/engine/prices.py:191` (`_BarCache.bars_asof`, `full[:cut]`), reached via
`data_manager._compute_one_backfill_date → scanner.compute_run_payload → regime.score_regime →
regime._index_ma_stack`. The coordinator confirmed via `/proc/self/status` that the dying process was
**VSZ-pinned at exactly 6144 MB** (RSS only ~4932 MB) — virtual-address-space exhaustion, not RSS overflow.
An audit fix-mode pass already removed a real-but-non-dominant iter-26 regression (`close_on`/`bars_after`
materializing a discarded `full[:cut]` prefix) — already committed at HEAD (`907cd6d`), byte-identity
verified. **The dominant, still-open driver is the pre-existing, unwindowed `regime.py` consumers**: they
call `bars_asof` directly and read the WHOLE `<= d` prefix (up to ~5,300 `Bar` tuples on a late date) even
though they only need a small trailing window — this repeats every (date × symbol) across the full
322-date rebuild, piling up transient large-list allocations under CPython arena fragmentation (the same
symptom class as the already-fixed `close_on`/`bars_after` regression, just in code iter-26 never touched).

Two prior measurement mistakes must not recur: (1) an **RSS-only** probe cannot catch a **VSZ** ceiling
hit — sample both; (2) a **12-date subset** cannot reproduce the crash — the repro must be the **full
322-date × 541-member shape**.

## What to Build

- **A bounded-window bar accessor in `prices.py`** (additive — `bars_asof` itself, its contract, and every
  other consumer stay untouched): a new `_BarCache.bars_asof_window(session, symbol, d, lookback)` that
  computes `cut = bisect.bisect_right(dates, d)` and returns `full[max(0, cut - lookback):cut]` directly
  — i.e. it never materializes the full `<= d` prefix, only the bounded trailing slice. A module-level
  `bars_asof_window(session, symbol, d, lookback)` mirrors the existing `close_on`/`bars_after` dispatch
  pattern: cache-aware branch when a `bar_cache` context is active, else a raw
  `WHERE date <= d ORDER BY date DESC LIMIT lookback` query (reversed to ascending) on the default path.
  Both branches are mathematically `bars_asof(session, symbol, d)[-lookback:]` — same rows, same order —
  so this is a pure allocation-shape change, not a value change.
- **Route `regime.py`'s three `bars_asof` call sites through the bounded accessor**, using
  `cfg.indicators.max_lookback_bars` (the SAME canonical bound iter-26 already validated — do not invent a
  second config value):
  - `_index_ma_stack` (`regime.py:39`) — needs only `ma_periods` (max 200 from config) worth of trailing
    closes for `ind.ma_stack`.
  - `_universe_stats` (`regime.py:53`) — needs only `breadth_long_ma` (200) / `high_window_52w` (252)
    worth of trailing closes; `len(series) >= icfg.high_window_52w` and `window = series[-icfg.high_window_52w:]`
    stay correct because `max_lookback_bars` (320) is already validated `>=` every one of these windows
    (`IndicatorsCfg._validate`, iter-26) — windowing only truncates the front of the series, never the tail
    the indicators actually read.
  - `_latest_vix` (`regime.py:91`) — currently does `closes(bars_asof(...))[-1]`, i.e. builds the whole
    prefix just to read one value. Route this through the ALREADY-optimized module-level `close_on`
    (`prices.py`, O(1) via `_BarCache.close_on`, already fixed and tested in the prior audit pass) instead
    of adding a second bounded-window call for a single scalar.
  - `bars_asof` (the un-windowed accessor) MUST remain the accessor for every other existing consumer
    (scoring.py, chart display, etc.) — this change touches ONLY `regime.py`'s three functions plus the
    new additive accessor in `prices.py`.
- **Byte-identity gate for the regime change**: extend `test_scoring_window.py` (or add a sibling file,
  developer's call — follow the existing `_with_max_lookback_bars` config-override idiom) with a
  `score_regime` windowed-vs-effectively-disabled-window comparison over the same real cadence dates the
  existing scoring harness uses, 0 diffs. Also add direct unit coverage that
  `bars_asof_window(session, symbol, d, lookback) == bars_asof(session, symbol, d)[-lookback:]` for both
  the cache-active and default (no-context) paths, long- and short-history symbols — the same
  cache-vs-default pairing style `test_forward_testing.py`'s `close_on`/`bars_after` cache-awareness tests
  already use.
- **Fallback levers if the regime fix alone does not clear the memory budget** (measure first, only add
  if needed — "developer picks the minimal set that clears the memory budget," per the spec):
  1. Extend the same `bars_asof_window` accessor to scoring.py's two existing `bars_asof` call sites
     (`scoring.py:113`, `:339`), replacing `bars = bars_asof(...); bars = bars[-icfg.max_lookback_bars:]`
     with `bars = bars_asof_window(..., lookback=icfg.max_lookback_bars)`. This is mathematically identical
     to the current two-step slice (so `test_scoring_window.py`'s existing byte-identity harness continues
     to pass unchanged) but avoids materializing the full prefix before truncating — it is "building the
     memory fix on top of" iter-26's feature, not rebuilding it.
  2. Give `_BarCache.prefill` OPTIONAL `symbols=` / `min_date=` bounds (goal.md fast-platform item A),
     BOTH defaulting to today's behavior so `test_bar_cache.py`'s byte-identical snapshot shims
     (monkeypatch at `:91`/`:256`; 2-arg call at `:102`) stay green untouched.
  - Do NOT touch the other per-symbol-bounded `.all()` sites in `prices.py` (`:115`, `:253`, `:292`,
    `:312`) — out of scope (iter-18 addendum, repeated in this spec).
- **Measure the crashing shape** — the full 322-date × 541-member "Rebuild snapshots" job under a literal
  `ulimit -v 6291456`, sampling `VmPeak`/`VmSize` AND `VmRSS` from `/proc/self/status`. Must run in a
  **single foreground turn** (background processes are reaped at turn end — do not background-and-wait
  across turns; wrap in `timeout` if needed to stay inside one Bash call). The "before" data point may cite
  the already-recorded iter-26 audit crash evidence (VSZ pinned at 6,291,456 KB / RSS 4,932 MB,
  `docs/handoffs/goal-mcp-loop-iter-26-audit.md` finding B1) rather than re-triggering a fresh crash purely
  for documentation — the new evidence that matters is the AFTER (fixed) run completing under budget on the
  full shape. Record before → after in `reports/perf-budgets.md` as a new dated section (follow the
  existing "Item F" format/style), both VSZ and RSS, as a **never-regress budget**.
- **Live re-verification (browser-qa, canonical lane)**: J-16 driven to a verified completed (or
  monotonically-advancing, no-early-"done") state on the live `/data` page without crashing the backend;
  the cold `GET /api/data` no-OOM repro (stop → cold-start → `/data` as FIRST request, ×2 — the iter-24/25
  sequence); all 8 required-still-passing journeys (J-01, J-03, J-04, J-05, J-10, J-12, J-13, J-15)
  re-verified live PASS (they were SKIPPED, not regressed, behind iter-26's outage).
- **Dev handoff** at `docs/handoffs/goal-mcp-loop-iter-27-dev.md` documenting the fix, the byte-identity
  evidence, and the memory measurement — honest about what was/wasn't cleared, matching this project's
  existing handoff style.

## Explicitly Out of Scope (per spec — flag, do not build)

- No new feature or evidence work; no `## Evidence Claim`; both ledgers stay byte-identical all-FAIL; the
  canonical Bonferroni divisor stays 8.
- Do NOT rebuild/re-litigate iter-26's scoring-window feature (`config.yaml` `indicators.max_lookback_bars`,
  `scoring.py`'s two slice sites, `test_scoring_window.py`'s existing tests) — it is correct; build on it.
- Do NOT run the full pytest suite (~10-11h at this data scale) — targeted tests only (see below).
- Do NOT touch the per-symbol-bounded `.all()` sites in `prices.py` (`:115`, `:253`, `:292`, `:312`).
- No new displayed value, no new endpoint, no nav-skeleton change — this is an internal memory-path
  hardening beneath already-registered canonical values (three scores, regime score, forward returns,
  bars, `data_manager.compute_availability`/`compute_coverage`/`compute_capacity`); every one re-serves
  byte-identically from its existing single computing module and single serving endpoint.

## Agents Required

- backend-data: yes — the entire fix is backend (prices.py bounded accessor, regime.py routing, targeted
  tests, memory measurement, perf-budgets.md update).
- frontend-ux: no — no frontend source change planned. The `/data` job-progress surface is re-verified live
  by browser-qa, not modified.

## Frontend Present: yes

(Verification-only per the phase spec's own metadata — 8 required-still-passing journeys plus the J-16
target journey must be re-driven live in the browser; no frontend source is touched.)

## Files to Create/Modify

- `apps/backend/app/engine/prices.py` -- add `_BarCache.bars_asof_window` + module-level `bars_asof_window`
  (new, additive; bounded trailing-window accessor, cache-aware + default-path branches; `bars_asof` and
  every other existing function unchanged)
- `apps/backend/app/engine/regime.py` -- route `_index_ma_stack`/`_universe_stats` through
  `bars_asof_window(..., lookback=cfg.indicators.max_lookback_bars)`; route `_latest_vix` through the
  existing `close_on`
- `apps/backend/tests/test_scoring_window.py` (or a new sibling test file) -- `score_regime`
  windowed-vs-disabled-window byte-identity harness + direct `bars_asof_window` equivalence tests
  (cache-active + default paths, long- and short-history symbols)
- `apps/backend/app/engine/scoring.py` -- OPTIONAL fallback lever only (see "Fallback levers" above); do
  not touch unless the primary regime fix alone does not clear the memory budget
- `apps/backend/app/engine/prices.py` `_BarCache.prefill` -- OPTIONAL fallback lever (`symbols=`/`min_date=`
  bounds, both defaulting to current behavior); only if needed
- `reports/perf-budgets.md` -- new dated section: full 322-date × 541-member rebuild VSZ/RSS before→after
  under literal `ulimit -v 6291456`, committed as a never-regress budget
- `docs/handoffs/goal-mcp-loop-iter-27-dev.md` -- dev handoff (new)

## UI Evolution

- New user-facing capability: none — this is a de-regression (the product stops crashing under its
  heaviest offline job), not a new capability.
- New information displayed: none.
- New user actions: none.
- UI surface changes: none — `/data` job-progress surface is unchanged code; re-verified live only.
- Navigation changes: none.

## Visual Requirements

- Component patterns: n/a (no UI change).
- Layout: n/a.
- Key visual effects: n/a.
- States to handle (re-verify only, unchanged code): `/data`'s job-progress panel must keep showing honest,
  monotonically-advancing progress (never "done early") through the full-universe rebuild; a genuinely-down
  backend must degrade to the single contained "Backend unavailable" card (nav/shell intact, no fabricated
  values) — the iter-25 boundary, not the iter-18/24 blank-app-error crash.

## Key Test Scenarios

- **Targeted unit/integration (NOT the full suite)**: `test_scoring_window.py` (existing 2 + new regime
  cases), `test_forward_testing.py` cache-awareness cases (existing, must stay green — untouched by this
  change), `test_bar_cache.py` (existing 12, must stay green — `bars_asof`/`prefill` signatures unchanged
  unless the fallback prefill lever is used, in which case its new params must be OPTIONAL and the existing
  monkeypatch shims at `:91`/`:256`/`:102` must still pass).
- **Memory measurement (mandatory, single foreground turn)**: full 322-date × 541-member "Rebuild
  snapshots" job under literal `ulimit -v 6291456`, sampling `VmPeak`/`VmSize` AND `VmRSS` from
  `/proc/self/status`; both must sit under 6144 MB with margin; recorded in `reports/perf-budgets.md`.
- **Cold `/api/data` no-OOM repro (mandatory, iter-24 lesson)**: stop backend → cold-start → `/data` as the
  FIRST request, ×2; backend survives, `/data` renders populated, `/stocks` loads after, `/api/health` 200.
- **J-16 live (target journey)**: drive the actual "Rebuild snapshots for current universe" job on `/data`
  past the deep-history dates that crashed iter-26 (dot-com/GFC/COVID/recent), backend survives, honest
  live progress throughout, verified completed (or monotonically-advancing) state — no `MemoryError`, no
  wedged backend, every endpoint stays 200 during and after.
- **8 required-still-passing journeys live PASS**: J-01, J-03, J-04, J-05, J-10, J-12, J-13, J-15 —
  re-verified on the fixed, live build (closing the iter-26 skipped-behind-the-outage gap), not merely
  cited as "unaffected by this diff."
- **Anti-goal #8 resolved**: re-verified by the canonical browser-qa lane specifically (an engine-level
  ablation/unit-test fix alone is NOT sufficient to mark it `resolved=true` — iter-24 lesson).
- **No-lookahead preserved**: `bars_asof_window` never returns a bar with `date > d` (same boundary as
  `bars_asof`); forward returns still read exclusively through `bars_after` (`date > d`).
