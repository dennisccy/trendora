# goal-mcp-loop-iter-26 Execution Plan

## Alignment check
Directly implements goal.md's "Improvement direction (engineering): fast platform on the deep basis"
**item F** (bound the scoring-input window) + the warmup forward-return cache-scope fix, surfacing
target journey **J-16** (data jobs — Fetch/Backfill/warmup — fast + honest progress). Confirmed unbuilt
against the tree: no `max_lookback_bars` anywhere in `apps/backend/app/` or `config.yaml`. Items
A/B/C/D/G/H are already landed (iter-19/24); this is the exact "smaller, self-contained" next step the
iter-25 evaluator named priority-1, and the phase spec is explicit it must NOT be bundled with the
evidence-recertification work (J-02/J-06/J-07/J-08/J-09) — a separate, risky, referee-gated change
(rubric rule 5: two risky changes in one diff are undiagnosable). No drift from goal.md.

`runs/goal-session-mcp-loop/state/blueprint.md` (tail) already carries a full "iter-26 clarification"
paragraph written by the goal-decomposer, registering this as an internal compute-path change with no
new displayed value/module/endpoint/nav change — **no developer edit to blueprint.md is needed**, only
consistency with it (same precedent as iter-24/25's handoffs).

No `## Evidence Claim` is carried (pure performance/correctness) — the post-decompose gate auto-passes;
both ledgers stay byte-identical all-FAIL and the canonical Bonferroni divisor stays 8.

## Critical implementation detail (read before touching warmup.py — this is not a trivial move)
The spec's own phrasing — "move `warmup.py`'s `backfill_forward_returns(engine, cfg)` inside the shared
`bar_cache` context" — is necessary but **NOT sufficient by itself**. Verified against the live code:

- `warmup.py:155` calls `backfill_forward_returns(engine, cfg)` — passing the **engine**, not the
  session already open in `_run_warmup`. `forward_testing.backfill_forward_returns` (`:428-439`)
  branches on `isinstance(session_or_engine, Session)`: passed an engine, it opens a **brand-new**
  `Session(engine)` with a different `id()`. The bar-cache registry (`_BAR_CACHES`, `prices.py`) is
  keyed by `id(session)`, so that new inner session is **never found in the registry** — relocating the
  call inside the existing `with bar_cache(session):` block (`warmup.py:145-152`) alone changes nothing;
  the new session still misses the cache and every `close_on`/`bars_after` call still round-trips the DB.
- `close_on` (`prices.py:328`) and `bars_after` (`prices.py:344`) are **raw, uncached queries today** —
  unlike `bars_asof` (`prices.py:308`), neither ever checks `_BAR_CACHES`/`active_bar_cache(session)`.
  Passing the *same* session is therefore also not sufficient on its own.
- **Two changes are both required:**
  1. In `warmup.py`, move the `backfill_forward_returns(...)` call inside the `with bar_cache(session):`
     block AND change the call to pass `session`, not `engine` — `backfill_forward_returns(session, cfg)`
     — so it takes the `isinstance(Session)` branch and reuses the exact session/cache already active.
  2. In `prices.py`, make `close_on` and `bars_after` cache-aware: check `active_bar_cache(session)`
     first; if present, derive the answer from the cache's already-loaded `_by_symbol`/`_dates_by_symbol`
     lists (mirror `_BarCache.bars_asof`'s `bisect.bisect_right(dates, d)` idiom — `close_on` = the close
     of the last bar at/before the cut; `bars_after` = the bars strictly after the cut, optionally
     `[:limit]`); else fall back to the existing raw query unchanged (byte-identical default path for
     every other caller). This most likely needs one new `_BarCache` method (e.g. `bars_after`) alongside
     its existing `bars_asof`/`trailing_count` (`prices.py:81-212`ish).
- **Bonus, must-verify-not-just-assume:** `data_manager._do_backfill` (`:2370-2513`, the EXISTING
  per-date Data Manager Backfill job — distinct from `warmup.py`) **already** attaches a shared prefilled
  cache to its per-date write session (`attach_shared_cache`, `:2441`) around its own
  `forward_testing.backfill_run_forward_returns` call (`:2450`) — but because `close_on`/`bars_after`
  are not cache-aware today, that attachment currently buys nothing for the forward-return step. Making
  them cache-aware will *also* speed up this pre-existing Backfill job's forward-return step for free —
  a good side effect, but it means the byte-identity harness must cover **both** call paths (the warmup
  cadence loop AND `_do_backfill`), not only the one path the spec names by name.

## What to Build
- **Config:** `indicators.max_lookback_bars` in `config.yaml` (`indicators:` block, ~`:633-649`) +
  `IndicatorsCfg` (`config.py:264-296`) — a validated positive int, no inline literal. The TRUE max
  lookback across every `bars_asof`-fed consumer in scoring is `high_window_52w = 252`
  (`config.yaml:640`); every other window is smaller (`ma_periods` max 200, `rs_windows` max 126 (6m —
  note: `rs_windows` config carries `1m`/`3m`/`6m` even though only 1m/3m are read in `_raw_components`
  today; use the full configured set's max to be safe), VCP `min_history_bars` 65,
  `pullback_to_rising_dma.min_history_bars` 90, `flat_base_breakout.min_history_bars` 45,
  `semivol_window`/`vol_contraction_prior` 63, `hv_window` 21, `atr_period` 14). Start at ~320
  (252 + ~68 margin) per the spec's own suggestion — but **the byte-identity harness is the sole
  authority**: if it shows any diff, widen the value; never accept drift as "close enough".
- **`scoring.py`:** at both `bars_asof` call sites — `_raw_components` (`:113`) and pass-3 (`:339`) —
  slice the returned series to the last `max_lookback_bars` bars (`bars[-N:]`) immediately after the
  call, before any indicator/detector runs on it. A member with fewer than N bars keeps its whole
  (shorter) series unchanged — short-history NA propagation is unaffected.
- **`warmup.py` + `prices.py`:** the two-part fix in "Critical implementation detail" above. No-lookahead
  is unaffected either way (scoring still reads ≤ as-of; forward returns still read > as-of — only the
  *load scope* changes, never the temporal boundary).
- **Byte-identity harness (new, committed, green):** `score_stocks` over ≥3 real cadence dates × the full
  ~583-symbol pool, window enabled vs. a disabled/huge window — 0 diffs required. Model it on the
  existing `test_bar_cache.py` idiom (`test_cached_snapshot_equals_uncached_row_level`,
  `test_bootstrap_snapshots_equal_with_cache`) rather than inventing a new comparison style.
- **New targeted tests** proving `close_on`/`bars_after` are byte-identical inside vs. outside an active
  `bar_cache` context — ADD alongside (never edit) the existing
  `test_forward_testing.py::test_close_on_is_the_asof_close` /
  `test_bars_after_returns_only_future_bars_ascending` / `test_bars_after_limit_is_the_unbounded_prefix`.
- **Real before/after performance measurement.** The existing `scripts/measure-perf.sh --backfill-days 5`
  methodology lands on an empty 2005 range (0 cadence-eligible dates, a 0.23 s no-op — see
  `reports/perf-budgets.md`'s iter-24/25 sections) and is **not** a valid item-F measurement as-is.
  Developer's choice: (a) extend the harness to resolve a real cadence-eligible date/range itself
  (config-driven, no bare literal), or (b) time `score_stocks` directly on a fixed late deep-history
  cadence date over the full pool, before vs. after. The DoD only requires a REAL (non-empty-range),
  same-host / prod-mode / same-subset-both-runs before→after pair for both per-date-backfill and a full
  (or ≥10-date representative) warmup pass, plus peak RSS confirmed under the 6144 MB cap. Record in
  `reports/perf-budgets.md` as a new, clearly-labeled iter-26 section — existing iter-19/24/25 sections
  stay untouched.
- Dev handoff at `docs/handoffs/goal-mcp-loop-iter-26-dev.md` (DoD requirement).

## Out of scope (do not implement this iteration)
- Evidence re-certification of J-02/J-06/J-07/J-08/J-09 — a separate, deliberately-not-bundled risky
  referee-gated change (rubric rule 5). Zero evidence work; no `## Evidence Claim`; both ledgers stay
  byte-identical all-FAIL, divisor stays 8.
- Fast-platform items E (lean `/api/stocks` summary DTO), I (frontend interaction costs — heatmap memo /
  leaderboard debounce), J (`record_json` shrink) — later, separate iterations.
- Deleting the dead-duplicate `index-regime-chart.tsx` / `major-indexes-card.tsx` (coherence-WARN
  carry-forward) — a dedicated tidy iteration.
- Hardening/down-weighting the non-terminal QA lane's recurring weak-evidence flag — a separate tidy
  iteration, not this perf change.
- Any new UI value, new endpoint, nav change, `/bars`/chart change, or frontend source edit of any kind.
- Widening `triad_scan.py`'s scan aperture / the online-FDR staging economy — a different "Improvement
  direction" section entirely, unrelated to this iteration.

## Agents Required
- backend-data: yes -- implement the config addition, the two `scoring.py` window sites, the
  `warmup.py` + `prices.py` cache-scope fix (both parts — see "Critical implementation detail"), the
  byte-identity harness, the extended `close_on`/`bars_after` cache tests, the real before/after
  performance measurement, and the `reports/perf-budgets.md` update; run the targeted (not full-suite)
  test selection; write the dev handoff.
- frontend-ux: no -- zero frontend source change this iteration (phase spec: "No frontend source
  change"). browser-qa still runs live against the existing `/data` surface to verify honest job progress
  on the faster backend and to replay the required-still-passing journeys — verification, not
  implementation, so no frontend-ux dev dispatch is needed.

Frontend Present: yes

## Files to Create/Modify
- `config.yaml` -- add `indicators.max_lookback_bars` under the existing `indicators:` block (~`:633-649`)
- `apps/backend/app/config.py` -- add `max_lookback_bars: int` to `IndicatorsCfg` (`:264-296`) with a
  positivity check in the existing `_validate` model_validator (`:282-300`); optionally cross-check it is
  >= the largest individually-configured window as a sanity guard (style precedent: the `ma_periods`
  cross-check at `:2206-2227`) — but treat the byte-identity harness, not a static check, as the real
  authority on correctness
- `apps/backend/app/engine/scoring.py` -- slice `bars` to `cfg.indicators.max_lookback_bars` right after
  each `bars_asof(session, ticker, asof)` call, at `:113` (`_raw_components`) and `:339` (pass-3)
- `apps/backend/app/engine/prices.py` -- make `close_on` (`:328`) and `bars_after` (`:344`) cache-aware
  (check `active_bar_cache(session)`/`_BAR_CACHES` first, mirroring `bars_asof`'s `:308-326` pattern,
  falling back to the existing raw query when no cache is active); add a `bars_after`-equivalent method
  on `_BarCache` (alongside its existing `bars_asof`/`trailing_count`, class starts `:71`) built from
  `_by_symbol`/`_dates_by_symbol` (`:82-83`) via the same `bisect.bisect_right` idiom
- `apps/backend/app/engine/warmup.py` -- move the `backfill_forward_returns(engine, cfg)` call (`:155`)
  inside the `with bar_cache(session):` block (`:145-152`) and change it to
  `backfill_forward_returns(session, cfg)`
- `reports/perf-budgets.md` -- append a new, clearly-labeled iter-26 section (existing iter-19/24/25
  sections untouched) with the real before/after per-date-backfill + warmup timings and peak-RSS
  confirmation
- Backend tests (additive only — do NOT edit existing expectations; an edited expectation is itself the
  regression signal per the iter-9 lesson):
  - a new byte-identity harness (e.g. `apps/backend/tests/test_scoring_window.py`, or extend
    `test_scoring.py`) proving `score_stocks` windowed == unwindowed over ≥3 dates × the full pool
  - extend `test_forward_testing.py` and/or `test_bar_cache.py` with new cases proving `close_on`/
    `bars_after` inside an active `bar_cache` context byte-match the raw-query path row-for-row, for both
    a long-history and a short-history symbol
  - a query-count assertion that the warm-up's cadence loop + `backfill_forward_returns` together load
    each symbol's series at most once for the whole run (style precedent:
    `test_kdate_backfill_loads_each_symbol_at_most_once`)
  - confirm UNEDITED + green: `test_bar_cache.py` (all 12 existing cases), `test_forward_testing.py`,
    `test_forward_testing_streaming.py`, `test_forward_walk.py`, `test_scoring.py`, `test_data_manager.py`
    (covers `_do_backfill`'s forward-return path, the "bonus" path noted above)
- `docs/handoffs/goal-mcp-loop-iter-26-dev.md` -- dev handoff (DoD requirement)

## UI Evolution
- New user-facing capability: none — no frontend source change. The existing `/data` job-progress panel,
  storage card, and availability legend are byte-identical.
- New information displayed: none in the UI. The only new content is the before/after job-timing rows in
  `reports/perf-budgets.md` (a committed report + the J-16 walkthrough source — not a UI value).
- New user actions: none — existing Fetch/Backfill/warmup controls unchanged, only faster.
- UI surface changes: none.
- Navigation changes: none.

## Visual Requirements
- Component patterns: N/A — no new or changed component.
- Layout: N/A — no page/panel change.
- Key visual effects: N/A.
- States to handle: browser-qa must confirm the EXISTING `/data` job-progress surface still shows honest
  LIVE progress on the faster backend (ticking `done/total`, never jumping straight to "done", never
  marking partial data complete) — a regression check on existing behavior, not a new state to design.

## Key Test Scenarios
- Byte-identity harness: `score_stocks` output (every score, bucket, setup, detected pattern) is
  IDENTICAL windowed vs. unwindowed across ≥3 real cadence dates × the full ~583-symbol pool — 0 diffs.
  A member with fewer than `max_lookback_bars` bars scores identically (short series untouched).
- `close_on`/`bars_after` return byte-identical results whether or not a `bar_cache` context is active,
  for both a full-deep-history symbol and a short-history symbol.
- The warm-up's cadence loop + `backfill_forward_returns` share ONE full-series load per symbol for the
  whole run (query-count proof), and `_do_backfill`'s forward-return step benefits the same way without
  changing its output.
- Existing scoring / bar-cache / forward-return suites (`test_bar_cache.py`, `test_forward_testing.py`,
  `test_forward_testing_streaming.py`, `test_forward_walk.py`, `test_scoring.py`) pass UNEDITED. If any
  expectation needs editing to pass, STOP — that is the regression signal (iter-9 lesson), not a fix to
  make.
- Per-date backfill on a REAL deep-history cadence date/subset improves ≥30% vs. a freshly-measured
  baseline (network fetch time excluded), same host, prod mode.
- A full warmup pass (or a fixed ≥10-date representative subset, same subset both runs) improves ≥30%;
  recorded as the new never-regress budget in `reports/perf-budgets.md`.
- Peak process RSS during warmup/backfill stays under the 6144 MB `server.memory_cap_mb` cap.
- A cadence date with 0 eligible members is an honest no-op (not a failure); no-lookahead holds (scoring
  ≤ as-of; forward returns > as-of) throughout.
- Browser (canonical browser-qa-agent, live, prod mode, `rm -rf apps/frontend/.next` + fresh start
  first): J-16 — `/data` job progress shows honest live progress on the faster backend, never "done
  early". Replay required-still-passing J-01, J-03, J-04, J-05, J-10, J-12, J-13, J-15.
- Both evidence ledgers stay byte-identical all-FAIL; canonical Bonferroni divisor stays 8; no anti-goal
  violation introduced.

## Operational hygiene (carried from the phase spec's Notes)
- Before browser QA: `rm -rf apps/frontend/.next`; bring up both services in prod mode
  (`start-backend.sh` / `start-frontend.sh` — never `dev.sh`) and confirm HTTP-200 on both first.
- The J-13/J-15 replay MUST include a genuine cold-path `/data` repro (stop backend -> cold start ->
  `/data` as the FIRST request, ≥2×) confirming no OOM under 6144 MB (iter-24 lesson: an `/api/health`
  boot is a different code path and gives a false "cold path OK").
- Clear `/tmp/pytest-of-*` before any test phase (the 30-year fixture exhausts `/tmp` every ~2-3 phases).
- Do NOT pin the full ~2h+ 30-year pytest suite as a hard mid-pipeline gate — targeted/affected tests
  only; confirm full green on an idle box as a deferred, non-blocking follow-up.
- Even on a clean J-16 pass, this iteration does NOT reach GOAL_ACHIEVED — J-02/J-06/J-07/J-08/J-09
  remain sanctioned-partial and are separate, later work per the iter-25 evaluator's priority-2.
