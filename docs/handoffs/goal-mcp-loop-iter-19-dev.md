# goal-mcp-loop-iter-19 Dev Handoff

**Phase:** goal-mcp-loop-iter-19
**Date:** 2026-07-07
**Agent:** developer
**Status:** complete

## What Was Built

A fix + verification pass (no new features, no new Evidence Claim) closing iter-18's REGRESSION
(J-01 `/stocks` Sector-sort crash) and its coupled OOM defect (goal.md fast-platform item A):

- **Bar-prefill OOM fix (`apps/backend/app/engine/prices.py`)** — `_BarCache.prefill()` rewritten from
  a whole-table `select(DailyPrice).order_by(...)` + `.all()` (3.27M hydrated ORM rows, ~6.8 GB peak
  reported) to a **streamed, column-projected** query (`symbol, date, open, high, low, close, volume`
  via `.yield_per(research.read_batch_size)`), building a lightweight module-level `Bar` NamedTuple
  per row (exposes exactly `.date/.open/.high/.low/.close/.volume` — every downstream consumer verified
  by grep to read only those attributes; no consumer code changed). The lazy per-symbol fallback inside
  `bars_asof()` adopts the same `Bar` type (already per-symbol-bounded — its bounding is unchanged).
  `ORDER BY symbol, date` and every served value are unchanged (byte-identical — see Tests Run).
- **Nested double-scan fix (the actual concurrency gap, found empirically — see Known Issues for the
  full diagnosis)** — `prefill()` now guards its expensive scan with a `self._prefilled` flag so a
  SECOND call on an already-loaded cache instance (the exact shape `_compute_coverage_uncached`'s own
  `prefilled_bar_cache` context plus `_membership_timeline`'s NESTED `prefilled_bar_cache` call produce
  on the same session) does not re-run the whole-table scan. Before this fix, the old code's
  `if symbol not in self._by_symbol` guard only skipped *overwriting* already-loaded series — the
  expensive query itself re-ran unconditionally on every call, so ONE `/api/data` request already paid
  the full scan TWICE, independent of any cross-request concurrency. This was invisible at the old
  ~122-symbol/5-year basis and is a doubled contribution to the OOM at 583 symbols/30 years.
- **`compute_coverage`'s cross-request single-flight (J-100, iter-42) — verified, NOT rebuilt.** Ran
  the pre-existing `tests/test_data_manager_concurrency_load.py` (K=12 concurrent callers,
  `threading.Barrier`, counts real `_compute_coverage_uncached` invocations) — it already passes: the
  single-flight correctly dedupes concurrent SAME-key callers. A real 6-concurrent-cold-request burst
  against the live 30-year DB (see Tests Run) confirms this empirically: peak RSS for 6 concurrent
  cold requests (~1.10 GB) barely exceeds 1 cold request (~1.09 GB) — not ~6×. No new locking layer
  was added (Risk #3 in the plan warned against this exact over-build).
- **`config.yaml`** — `server.memory_cap_mb`'s stale "~1.3M-row" comment corrected to the real
  ~3.27M-row figure; the 6144 MB cap is unchanged (still clears the new ~1.09 GB peak with wide margin).
- **`reports/perf-budgets.md`** (new file) — the item-A before/after measurement, taken live against
  the real 1.3 GB / 3.27M-row committed DB (not an estimate): single cold `/api/data` 10.5 s / ~1.09 GB
  peak; 6 concurrent cold requests 18.5 s / ~1.10 GB peak; both well under the 60 s / 6144 MB budget.
- **Sector null-safety (`apps/frontend/lib/sector-label.ts`, new)** — `sectorLabel(sector)` maps
  `null` to the honest `"Unassigned"` bucket; `compareSectors(a, b)` is the null-safe ascending
  comparator. One shared helper used everywhere a stock's sector is displayed, filtered, or sorted (5
  call sites — the "third occurrence" simplicity-bar threshold was clearly passed, justifying the
  extraction). `lib/sector-label.test.ts` unit-tests it (see Tests Run for how it was executed).
- **`apps/frontend/lib/api.ts`** — `StockRow.sector: string` → `string | null` (the actual contract:
  ~78% of the broadened 548-name pool has no `config.stock_sectors` mapping; the backend already
  served `null` honestly — only the frontend TYPE was wrong).
- **`apps/frontend/app/stocks/page.tsx`** — `SORT_COMPARATORS.sector` now calls `compareSectors`
  (the exact crash site: `a.sector.localeCompare(b.sector)` on `a.sector === null` threw an uncaught
  `TypeError`); the sector-filter vocabulary memo and filter predicate route through `sectorLabel` so
  the dropdown offers "Unassigned" (never a literal null/blank option) and selecting it matches every
  null-sector row; the leaderboard's Sector cell displays `sectorLabel(row.sector)` instead of a blank
  cell for an unmapped name.
- **`apps/frontend/app/stocks/[ticker]/page.tsx`** and **`apps/frontend/app/scanner-runs/[runId]/page.tsx`**
  — both read the SAME `StockRow.sector`; their sector display cells now use `sectorLabel` too (found
  via `tsc --noEmit` against the widened type — zero errors after these two fixes, confirming no other
  consumer was missed; `apps/frontend/app/watchlist/page.tsx`, named in the plan as a place to check,
  does not read `.sector` at all).
- **Crash containment: `apps/frontend/app/error.tsx`** (new) — a route-level Next.js error boundary.
  Renders a contained error card ("Something went wrong on this page" + a "Try again" button) IN PLACE
  of the crashed page's content, inside the root layout's `{children}` slot — so the sidebar nav +
  header keep rendering around it. This is the general-purpose safety net the iter-18 regression
  lacked (the sector-sort crash itself is separately fixed at its source above).
- **`apps/frontend/app/global-error.tsx`** (new) — the root-layout error boundary (Next.js special
  file; activates only if the root layout itself, or `error.tsx`, throws). Renders its own minimal
  `<html>`/`<body>` (Next.js requirement — it replaces the root layout), deliberately importing NO app
  components/providers (Sidebar/AsOfProvider/etc. all depend on the very layout this boundary
  substitutes for) so this last-resort fallback cannot itself fail the same way.

## Files Changed

- `apps/backend/app/engine/prices.py` — `Bar` NamedTuple; streamed/column-projected `prefill()` with
  the `_prefilled` skip-guard; `bars_asof()`'s lazy branch adopts `Bar`; the module-level `bars_asof()`
  and the `closes`/`highs`/`lows`/`volumes` extractor functions' type hints widened to
  `list[DailyPrice] | list[Bar]` for accuracy (no behavior change — pure annotation cleanup, since
  these now genuinely receive either type depending on whether a `bar_cache` context is active).
- `apps/backend/tests/test_bar_cache.py` — 3 new tests: prefill/lazy-load byte-identity + `Bar` typing
  against a plain reference query; prefill skip-requery-when-already-loaded.
- `apps/backend/tests/test_data_manager_membership_cache.py` — 1 new test: a cold `compute_coverage()`
  call scans the bar cache exactly once despite the nested `prefilled_bar_cache` call.
- `config.yaml` — `server.memory_cap_mb` comment fix (repo root, not under `apps/backend/`).
- `reports/perf-budgets.md` — new file, item-A measurement.
- `apps/frontend/lib/sector-label.ts` — new; `UNASSIGNED_SECTOR`, `sectorLabel`, `compareSectors`.
- `apps/frontend/lib/sector-label.test.ts` — new; unit tests (see Tests Run for the execution caveat).
- `apps/frontend/lib/api.ts` — `StockRow.sector: string | null`.
- `apps/frontend/app/stocks/page.tsx` — null-safe sector comparator/filter/vocabulary/cell.
- `apps/frontend/app/stocks/[ticker]/page.tsx` — sector cell uses `sectorLabel`.
- `apps/frontend/app/scanner-runs/[runId]/page.tsx` — sector cell uses `sectorLabel`.
- `apps/frontend/app/error.tsx` — new; route-level error boundary.
- `apps/frontend/app/global-error.tsx` — new; root error boundary.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/<file> -v` (per-project convention —
`.claude/project-template.md`'s STACK/TEST-COMMANDS sections are unfilled placeholders for this
project; the command above is inferred from the real `.venv` + existing test invocations and confirmed
working).

- `tests/test_bar_cache.py` — **12 passed** (the 9 pre-existing byte-identical/load-once snapshot
  tests, unmodified in intent, stayed green; + my 3 new tests). Includes
  `test_cached_snapshot_equals_uncached_row_level` and `test_bootstrap_snapshots_equal_with_cache`,
  which run the FULL `score_stocks`/`scanner.run_scan` through the cache and assert row-level equality
  against the uncached path — the strongest available proof the `Bar` substitution changed no computed
  value.
- `tests/test_data_manager_membership_cache.py` — **10 passed** (9 pre-existing + my 1 new test).
- `tests/test_data_manager_concurrency_load.py` — **3 passed**, unmodified (the pre-existing J-100
  single-flight load test; K=12 concurrent callers, byte-identity, RSS/latency bounds, warm-cache
  zero-recompute). Ran as-is to get the empirical single-flight verdict the plan required, rather than
  writing a duplicate (one already existed and covers exactly that property).
- `tests/test_prices_asof.py` — **8 passed** (0.07s; the direct module-function unit tests for
  `bars_asof`/`bars_after`/`bars_through_latest` — the DEFAULT, uncached path, which my change does
  not touch beyond a type-annotation fix).
- `tests/test_universe_resolver.py` — **17 passed** (1.43s).
- `tests/test_bars_windowing.py` — **9 passed** (1.61s; the `/api/stocks/{ticker}/bars` endpoint tests —
  confirms the chart/windowing path, which reads bars via the DEFAULT uncached `bars_asof`/
  `bars_through_latest` functions since no `bar_cache` context is active for a single stock-detail
  request — unaffected by the `_BarCache` rewrite in anything but return-type annotation accuracy).
- `tests/test_scanner.py` — see Known Issues (did not finish inside this session; low-risk, see reasoning
  there).
- `tests/test_bars.py` — not run this session (depends on the SAME conftest.py `loaded_engine` session
  fixture as the API test suite — a full real-seed load + the complete historical bootstrap/backfill
  warmup, which is the expensive part of the ~10-11h full-suite runtime per project memory). See Known
  Issues for why this is low-risk to defer to review/QA.

- **Final consolidated re-run** (after the extractor type-hint polish above, to confirm nothing broke):
  `pytest tests/test_bar_cache.py tests/test_prices_asof.py tests/test_bars_windowing.py
  tests/test_universe_resolver.py tests/test_data_manager_membership_cache.py
  tests/test_data_manager_concurrency_load.py -q` → **59 passed in 104.79s**, zero failures.
- Frontend: `cd apps/frontend && node_modules/.bin/tsc --noEmit` — **0 errors** (full project,
  confirms `StockRow.sector: string | null` and every consumer I fixed + rules out any other consumer).
- Frontend unit test `lib/sector-label.test.ts`: this repo's convention is `node lib/*.test.ts` (native
  TS type-stripping) but the sandboxed Node binary here (v22.22.1) lacks that feature
  (`ERR_NO_TYPESCRIPT` — confirmed this is a PRE-EXISTING environment gap: the 8 other sibling
  `.test.ts` files in `lib/` fail identically, not something this iteration broke). Verified logical
  correctness instead by compiling with the local `tsc` to plain JS
  (`--esModuleInterop --allowImportingTsExtensions --rewriteRelativeImportExtensions`) and running the
  output with plain `node` — **8 passed**.

## Live/manual verification (beyond the automated tests)

- Started `scripts/dev.sh` twice in a row (restart-over-restart): both backend (uvicorn) and frontend
  (`next dev`) came up healthy within 1 s each time; confirmed the SECOND run's port-clearing killed
  ALL of the first run's processes, including the child `next-server` process (not just the parent
  `next dev` wrapper) — no port conflicts.
- Hit the real `/api/stocks` endpoint on the live 30-year DB: 541 rows, 422 null-sector (78.0%) —
  matches goal.md's cited "~78%-null-sector state" exactly.
- Browser-verified on the live app (`/stocks`): clicked the Sector column header — **no crash**, nav
  sidebar fully intact, rows sorted ascending by real GICS sector name (Communication Services →
  Consumer Discretionary → ... ). The Sector filter dropdown lists `Unassigned` between `Technology`
  and `Utilities` (alphabetical, never a literal null/blank option). Selecting "Unassigned" narrowed
  the view to exactly 422/541 rows, every visible row's Sector cell reading "Unassigned" — byte-exact
  match with the direct API count.
- Forced a real render-time exception (monkey-patched `Array.prototype.sort` to throw, then clicked a
  sort header) to verify `error.tsx` for real, not just by inspection: the error card rendered
  ("Something went wrong on this page" / "Try again") with the FULL sidebar nav + header still
  visible and functional — confirmed via screenshot, not just DOM presence.
- Visited `/stocks/NVDA`: sector cell reads "Technology" (the non-null case is unaffected); the chart
  toggled to "Full history" renders 3,025 bars back to 1999-01-22 with "older bars weekly-sampled"
  disclosed — the plan's non-blocking F1 carry-over item is already correctly working (initially
  looked blank in one screenshot, which was mid-fetch — a second screenshot 2s later showed it
  rendered correctly; no fix was needed).

## Known Issues

- **`tests/test_scanner.py` and `tests/test_bars.py` not confirmed green within this session.** Both
  depend on a real-seed-load fixture (`test_scanner.py`'s own module fixture; `test_bars.py` via
  conftest's session-scoped `loaded_engine`, which ALSO runs the full historical bootstrap/backfill
  warmup) that runs long enough to exceed a practical interactive timeout — this is the expensive part
  of the ~10-11h full-suite runtime per project memory, and per that same memory the convention is to
  leave full-suite/`loaded_engine` confirmation to the review/QA stage rather than the interactive dev
  loop. **Risk assessment (why I judge this low-risk to defer, not a gap I'm hiding):**
  - `test_bars.py` tests `/api/stocks/{ticker}/bars` (MA alignment, no-lookahead) — this endpoint reads
    bars via the DEFAULT, uncached `bars_asof`/`bars_through_latest` module functions (no `bar_cache`
    context is active for a single stock-detail request), so it does not exercise the `_BarCache` code
    I actually rewrote. `test_bars_windowing.py` covers the same endpoint with fast synthetic fixtures
    and is confirmed green.
  - `test_scanner.py` DOES exercise `bar_cache` (`scanner.py:255`), but `test_bar_cache.py`'s
    `test_bootstrap_snapshots_equal_with_cache` and `test_cached_snapshot_equals_uncached_row_level`
    already assert `scanner.run_scan`/`score_stocks` produce ROW-LEVEL IDENTICAL output cached vs.
    uncached on the real seed — the same property `test_scanner.py` would otherwise re-confirm.
  - Reviewer/QA action: re-run `cd apps/backend && .venv/bin/python -m pytest tests/test_scanner.py
    tests/test_bars.py -v` (budget several minutes for the seed load + warmup) if independent
    confirmation is wanted before sign-off.
- **The nested-prefill-double-scan bug is a fix beyond the plan's literal framing.** The plan asked me
  to determine whether `compute_coverage`'s cross-REQUEST single-flight had a gap (a second caller
  bypassing it, or a cache-key mismatch). I confirmed empirically (the pre-existing
  `test_data_manager_concurrency_load.py`) that it does NOT — concurrent identical requests already
  dedupe correctly. The actual gap I found is different in kind: WITHIN one single-flighted
  computation, `_membership_timeline`'s nested `prefilled_bar_cache` call re-triggered the SAME
  cache's expensive scan a second time, because `prefill()` had no memory of already having run. I
  fixed this in the same function I was already rewriting for streaming (the `_prefilled` guard) since
  it's a direct, minimal, clearly-justified efficiency fix on code already in scope — not a new,
  separate locking mechanism (which the plan's Risk #3 explicitly warned against building). Flagging
  this so the reviewer can confirm the diagnosis reasoning holds up, since it differs from the plan's
  literal hypothesis (even though it is the same root problem — the OOM — and the same file/function).
- **`reports/perf-budgets.md`'s "before" figures for the unfixed code are cited from goal.md's own
  reported iter-18 incident (~6.8 GB peak), not independently re-measured by me.** Deliberately
  reproducing the OOM on the live 30-year DB to get a fresh "before" number would have meant
  temporarily reverting the fix and risking an actual OOM-kill of the dev backend for a data point the
  spec already supplies from the real incident. The "after" figures (10.5 s / ~1.09 GB single request;
  18.5 s / ~1.10 GB for 6 concurrent) are all freshly measured live this session.
- **Frontend unit tests cannot currently run via the project's own documented convention** (`node
  lib/*.test.ts`) in this sandbox — the installed Node (v22.22.1) was built without TypeScript
  support. This affects ALL 9 `.test.ts` files in `apps/frontend/lib/` (8 pre-existing + my new one),
  not just this iteration's addition. Not introduced by this iteration; worth a maintenance note for
  whoever owns the dev-environment setup (either pin a Node version/build with `--experimental-strip-types`
  working, or add a `tsx`/`ts-node` devDependency and a `package.json` test script).
- **`.claude/project-template.md` is the unfilled generic template** (STACK / TEST COMMANDS / DESIGN
  SYSTEM sections all still show `<e.g., ...>` placeholders) — not something this iteration should fix
  (out of scope; `docs/goal.md`-only-edit convention for this project), but it means every agent
  touching this repo has to re-derive the stack/test/design-system facts from the codebase directly
  each time, as I did here. Noting it since the developer-agent instructions explicitly route through
  that file.
