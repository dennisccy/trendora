# Iteration 26 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-26
**Date:** 2026-07-10
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

This iteration ships **zero frontend changes** (confirmed via `git status`/`git diff` — no file under
`apps/frontend/` is touched) and is a pure internal compute-path optimization (fast-platform item F):
bounding the scoring engine's per-member bar window and moving the warm-up's forward-return backfill
inside the shared `bar_cache` session. Per the agent's no-op rule ("iteration changed no frontend and
registered no values"), this is close to the textbook no-op case; I nonetheless walked the Data
Contract check below because the diff does touch the canonical scoring module, and I wanted to confirm
the byte-identity claim is actually proven rather than merely asserted.

Diffed against snapshot `b738b76dac08db67609e332e08a2be8ce668e551`. The noise-excluded diff also
contains a large, unrelated `incredible_auto_dev/` tree change (commit `eaf42d1 chore(framework): pull
vendored incredible_auto_dev up to auto_dev/main@9a8951f`, sitting between the snapshot and HEAD). That
directory is a vendored copy of the meta-framework itself (agents/skills/scripts under
`incredible_auto_dev/`), not Trendora product code — it has no IA surface and no Data Contract value in
this session's blueprint, so it is out of this audit's scope and excluded from the findings below.

I did not treat the browser-qa/auditor/ux-regression MemoryError FAIL as a coherence matter, per the
coordinator note — that is a resource/correctness failure at the `ulimit -v` ceiling during a
full-universe rebuild, not a structural or data-contract drift. Nothing in the diff suggests the OOM is
caused by a second computation path or a nav/IA problem; it reads as an out-of-scope operational issue
for this gate.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Three per-stock scores (Leadership/Entry Quality/Risk) — `scoring:score_stocks` → `GET /api/stocks`, `GET /api/stocks/{ticker}` | OK | `apps/backend/app/engine/scoring.py:114` (`_raw_components`) and `apps/backend/app/engine/scoring.py:349` (pass-3) add a `bars = bars[-icfg.max_lookback_bars:]` slice INSIDE the existing canonical function — same module, same two call sites the function already had, not a new/parallel computation. Byte-identity is proven, not merely claimed: `apps/backend/tests/test_scoring_window.py` runs `score_stocks` windowed (320) vs. effectively-unwindowed (1,000,000) over 3 real cadence dates × the full pool plus a dedicated short-history date, asserting full dict equality (`windowed == unwindowed`), with an explicit non-vacuousness guard (`max(deep_counts) > max_lookback_bars`). |
| Realized forward-return evidence — `forward_testing:compute_forward_aggregates`/`compute_run_scorecard` → `GET /api/backtest`, `GET /api/research/samples` | OK | `forward_testing.py` itself is untouched (only its test file changed). `apps/backend/app/engine/prices.py:193-238` adds cache-aware `_BarCache.bars_after`/`.close_on` and wires module-level `close_on`/`bars_after` (`prices.py:388-390`, `:415-417`) to use them when a `bar_cache` is active — an internal load-path optimization beneath the write side (`_backfill`) of the already-registered value, not a second computation of the aggregate/scorecard value itself. `apps/backend/app/engine/warmup.py:150-166` passes `session` instead of `engine` into the pre-existing `backfill_forward_returns(session_or_engine, cfg)` — confirmed at `forward_testing.py:428-439` that this already-existing `isinstance(session_or_engine, Session)` branch routes to the SAME `_backfill` function; no new writer, no new endpoint. `test_forward_testing.py` adds byte-identity tests (`test_close_on_cache_aware_matches_uncached`, `test_bars_after_cache_aware_matches_uncached`) proving the cache path matches the uncached query. |
| `indicators.max_lookback_bars` (new config field, `config.py`/`config.yaml`) | OK — not a displayed value | Internal tuning knob bounding scoring's input window; never rendered in any UI surface or API response body as a distinct field. Not a Data Contract entry and the iteration spec correctly lists "Data-contract additions: None." |

No new function/service/endpoint was found that independently recomputes any registered value, and no
new UI surface fetches a registered value from a non-canonical source (there is no new UI surface at
all this iteration).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK | `apps/frontend/` has zero changed files (`git status`/`git diff` confirm); J-16's existing home `/data` is unchanged code. No nav/sidebar file needed inspection since nothing new was added. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `reports/perf-budgets.md` gained new "Item F" before/after timing rows — correctly treated by the
  iteration spec as a committed engineering report, not a UI-displayed value; no Data Contract entry
  needed.
- Pre-existing, unrelated-to-this-diff oddity noticed while reading `warmup.py`/`test_warmup.py`
  context: both files carry surrounding (unchanged) comments referencing "iter-36 (J-96)" — a much
  later iteration number than this session's current iter-26. This is untouched context, not introduced
  by this diff, and outside this gate's scope; flagging only so a future coherence pass isn't surprised
  by it.
- The `incredible_auto_dev/` vendored-framework diff riding along in the noise-excluded range (via
  commit `eaf42d1`, unrelated to this iteration's dev/review/QA dispatch) is not product code and was
  excluded from this audit; if it was landed unintentionally alongside iter-26's work, that is worth a
  quick sanity check outside this gate, but it introduces no IA or Data Contract concern for Trendora.
