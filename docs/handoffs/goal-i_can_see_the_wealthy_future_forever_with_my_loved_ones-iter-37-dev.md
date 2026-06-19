# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37
**Date:** 2026-06-19
**Agent:** developer
**Status:** complete

> This handoff REPLACES the aborted verify-only stub. iter-37 is now a real fix-and-verify pass:
> the iter-36 load-once regression is fixed in the engine read path, byte-identity is proven, and
> the live `/data` re-verify (J-94/J-96) is handed downstream to browser-qa-agent (`Frontend Present: yes`).

## What Was Built

- **PRIMARY — restored the J-46 "each symbol loaded at most once per parallel backfill job" invariant**
  that the iter-36 resolver cold-miss optimization silently broke.
  - **Root cause (confirmed + reproduced):** `_BarCache.prefill` only recorded symbols that have rows in
    `daily_prices`. A candidate-pool symbol with **zero bars** was never in the cache, so the iter-36
    active-cache branch in `universe_resolver.resolve_with_reasons` (`cache.trailing_count(sym, asof)`)
    fell through to `bars_asof`'s lazy per-symbol load — re-issued **every snapshot date / per worker
    session** of a parallel K-date backfill. `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once`
    failed `assert 3 == 1` (e.g. `A` loaded 3×).
  - **Fix (sanctioned approach (a) + a defensive belt for (b)):**
    - `_BarCache.prefill(session, expected_symbols=None)` now records an **empty series `[]`** for every
      expected candidate-pool symbol that has no bars, up front, in the single prefill query's publish
      step. A no-bar candidate therefore resolves to a trailing count of `0` from the once-loaded cache
      with **no per-date lazy re-load** — load-once-per-job holds for no-bar names too.
    - `prefilled_bar_cache(session, expected_symbols=None)` forwards the candidate-pool set.
    - The two `prefilled_bar_cache` call sites (`_do_backfill` — the K-date parallel job — and
      `_membership_timeline` — the J-96 timeline derivation) now pass the committed candidate pool
      (`{row["symbol"] for row in read_pool()}`).
    - `_BarCache.trailing_count` was hardened defensively: a not-yet-recorded symbol is loaded **exactly
      once** and a no-bar symbol is memoized as `[]` (via `bars_asof`'s under-lock record), so even a
      non-expected name is never re-loaded on later dates / other worker sessions.
- **Byte-identity (non-negotiable) — PROVEN.** A zero-bar symbol's trailing count is `0` and yields
  `below_history` exactly as the grouped-count path does. Confirmed directly on seed data:
  - `membership_timeline` payload: **byte-identical** new (`expected_symbols`-aware) vs. pre-fix prefill.
  - `resolve_with_reasons`: **byte-identical** active-cache path vs. default per-request (no-cache) path
    (`admitted_count=96`, `excluded={below_history:433, below_price:5, below_adv:14}` on the seed sample).
  - `compute_coverage` coverage block: **byte-identical** cold vs. warm.
  - `score_stocks(D)` cached vs. uncached: byte-identical (existing `test_cached_snapshot_equals_uncached_row_level`).

## Files Changed

- `apps/backend/app/engine/prices.py` -- `prefill` + `prefilled_bar_cache` take an optional
  `expected_symbols`; a no-bar expected symbol is recorded as an empty series up front. `trailing_count`
  hardened to load-once + memoize the no-bar result. Default (no-context) per-request path untouched.
- `apps/backend/app/engine/data_manager.py` -- `_membership_timeline` and `_do_backfill` pass the
  committed candidate-pool symbols to `prefilled_bar_cache`. No resolver/scoring/coverage math changed.
- `apps/backend/tests/test_bar_cache.py` -- NEW fast unit test
  `test_prefill_expected_symbols_records_zero_bar_symbol_once` (a zero-bar candidate counts as 0 trailing
  bars from the prefilled cache with at most one load). The `_counting_prefill` shim in the K-date test
  updated for the new optional kwarg; **`assert max(load_counts.values()) == 1` is UNCHANGED**.
- `docs/handoffs/...-iter-37-dev.md` -- this handoff (rewrites the aborted verify-only stub).
- `reports/phase-...-iter-37-implementation-summary.md` -- operator-facing summary.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/<module> -q` (targeted modules, per the
suite-handling constraint — the FULL ~3.5 h suite is handed to the pump nohup-async).

| Module | Result |
|--------|--------|
| `tests/test_bar_cache.py` | **9 passed** (incl. the previously-failing `test_kdate_backfill_loads_each_symbol_at_most_once`, assertion unchanged, + the new fast no-bar test) |
| `tests/test_data_manager_membership_cache.py` | **8 passed** (membership-timeline byte-identity: cached==fresh, warm==cold, warm-no-recompute, empty-DB, causality) |
| `tests/test_data_manager_backfill_parallel.py` | **10 passed** (parallel==sequential ScannerRun/ScannerResult/ForwardReturn byte-identity) |
| `tests/test_db.py` | **9 passed** (expected-tables guard — no new table added, so unchanged) |
| `tests/test_warmup.py` | **handed to pump** — module-scoped heavy seed-boot exceeds the 10-min Bash cap on this 1370-date host (known slow-boot module per operator note). The warm-up's `_membership_timeline` path is covered byte-identically by `test_data_manager_membership_cache` + the direct proof above. |

Direct byte-identity proofs (one-off scripts, not committed): membership_timeline new-vs-old = identical;
resolve_with_reasons cache-vs-no-cache = identical; compute_coverage cold-vs-warm = identical.

**FULL backend pytest suite:** NOT run by dev (it is ~3.5 h on this 1370-date DB and cannot finish under
the Bash cap). Handed to the pump **nohup-async**; the evaluator gates GOAL_ACHIEVED candidacy on the
**flushed `0 failed, EXIT 0`** line — never on the in-flight suite. Treat any `test_warmup.py` /
`test_data_manager_jobs_pipeline.py` timeout/`F` as a known concurrent-QA / slow-boot contention flake
and **re-run it isolated** before attributing a regression (iter-11/29/30/34 lesson).

## Live `/data` re-verify (J-94 / J-96)

Owned by **browser-qa-agent** downstream (`Frontend Present: yes` is set ONLY to force that step — the
iter-36 auto-skip lesson). Dev did not drive the browser. Required technique (from the spec): a SINGLE
sequential `/data` page load with a ~30 s hydration wait; `md5sum` the evidence dir FIRST; **never**
concurrent `/api/data` probing (that exhausts the SQLAlchemy pool — size 5 + overflow 10 — since one
`/api/data` call holds a connection ~10 s); reject any un-hydrated skeleton / dead-shell frame. WAIT for
`/api/health` `readiness:"ready"` before driving the page.

## Known Issues / Limitations

- **The optional `GET /api/data` coverage optimization was DESCOPED (developer judgement, permitted by
  the spec).** The residual ~10–12 s on the full 1370-date DB is the **single-as-of** `_resolved_universe`
  / `_coverage_diagnostic_absent` resolve inside `compute_coverage` (the per-request grouped-count +
  full-series loads for history-clearing symbols at the resolved as-of) — NOT the now-cached J-96
  timeline. It was descoped because: (1) the PRIMARY load-once fix is the required gating deliverable and
  is complete + proven byte-identical; (2) the optimization adds real regression surface (a new
  `dataset_version`-keyed cache table, a warm-up precompute path, byte-identity tests, a `test_db.py`
  guard entry) whose full verification needs the ~3.5 h suite I cannot run; (3) a SINGLE sequential
  `/data` load hydrates within the ~30 s live-verify wait (the iter-36 steady-state was ~12–16 s, not the
  iter-35 >300 s hang). **Residual:** `/api/data` is ~10 s on the full DB and a SECOND concurrent reader
  during that window can still pressure the connection pool — hence the strict single-sequential-load
  live-verify discipline above. If a later iteration optimizes it: cache the coverage block on the
  EXISTING `research._dataset_version` stamp (no second stamp / no second computed value), precompute in
  `warmup._run_warmup` (own guard, non-fatal), and register any new table in `test_db.py`'s expected-tables
  guard (standalone table, NOT `_ADDITIVE_COLUMNS`) — iter-20/29 lesson.
- **`test_warmup.py` could not be flushed under the dev Bash cap** (module-scoped heavy seed-boot). It is
  in the pump's full-suite run; its membership-timeline assertion is independently covered byte-identically.
- **No frontend code change** (none expected; the `/data` surface is unchanged — it simply hydrates from a
  correct, fast `GET /api/data`).
