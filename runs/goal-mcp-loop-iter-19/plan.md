# goal-mcp-loop-iter-19 Execution Plan

Depth: **full** (mandatory — prior verdict was REGRESSION; verified directly in
`runs/goal-session-mcp-loop/iter-18/eval.md`: J-01's `/stocks` leaderboard crashed to a blank
"Application error" on Sector-sort, wiping nav, on the default ~78%-null-sector state). This
iteration is a **fix + verification pass only** — no new features, no new evidence claims. It
implements exactly the sequencing goal.md itself prescribes ("the iter-19 regression pass =
sector-null crash fix + fast-platform item A") — **no drift from goal.md, no scope creep found.**

## What to Build

**Backend — bound the `/api/data` prefill OOM (blocking; unblocks browser-QA)**
- Rewrite `_BarCache.prefill()` in `apps/backend/app/engine/prices.py` (currently
  `select(DailyPrice).order_by(DailyPrice.symbol, DailyPrice.date)` + `.all()` → 3.27M hydrated
  ORM rows, ~6.8 GB peak). Replace with a **streamed, column-projected** load — select only
  `symbol, date, open, high, low, close, volume`, iterated with `.yield_per(batch)` (idiom already
  in the codebase: `forward_testing.py`'s `_streamed_existing_keys`, lines ~367-378) — building a
  lightweight `Bar` record (module-level `NamedTuple` or `__slots__` class; developer's choice)
  with **exactly** the attributes `.date/.open/.high/.low/.close/.volume` so no consumer code
  changes. Apply the same `Bar` type to the lazy per-symbol fallback inside `_BarCache.bars_asof()`
  (the `if full is None:` branch, ~line 100-114 — this path is already per-symbol-bounded, so it is
  in scope only to adopt the lightweight type, not to change its bounding).
- Batch size from config, no inline literals: reuse `research.read_batch_size` (confirmed in
  `config.yaml:815` = `2000`) or add `data_manager.prefill_batch_size`.
- **Preserve byte-identity** — keep `ORDER BY symbol, date` and the `expected_symbols` semantics
  exactly. Any new parameter threaded through `prefilled_bar_cache()` → `_BarCache.prefill()`
  **must be optional** (confirmed: `apps/backend/tests/test_bar_cache.py` monkeypatches
  `prices._BarCache.bars_asof` / `.prefill` directly at ~lines 91 & 256, and calls
  `prefilled_bar_cache(session, expected_symbols=[...])` at ~line 102 — a new required arg breaks
  these). These are the correctness gate: they must stay green, unmodified in intent.
- **Diagnose, then fix, the `compute_coverage` single-flight** — IMPORTANT FINDING: this is not a
  build-from-scratch task. `apps/backend/app/engine/data_manager.py` already has a J-100 (iter-42)
  single-flight — `_COVERAGE_LOCK` / `_COVERAGE_INFLIGHT` / `_COVERAGE_RESULTS` around
  `compute_coverage()` (~line 680), gating `_compute_coverage_uncached()` (~line 758) which wraps
  its body in `with prefilled_bar_cache(session, expected_symbols=pool_symbols):`. On its face this
  should already serialize cold computes — so the developer must **empirically prove** (a
  concurrency test, not inspection) whether it actually does, and if not, find the gap: e.g. a
  cache-key mismatch across concurrent request sessions (`_coverage_cache_key` →
  `_db_identity`/`_config_fingerprint`/`_resolve_coverage_asof`/`_membership_dataset_version`), or a
  second, un-gated caller of `prefilled_bar_cache` (check `compute_availability` and the other
  4 call sites `grep` turns up in `data_manager.py`/`scanner.py`/`warmup.py`/`market_phase.py`) that
  bypasses `compute_coverage` entirely. Fix whichever is true.
- **Sequencing note (do not skip the streaming rewrite in favor of only fixing concurrency):** a
  SINGLE prefill already peaks at ~6.8 GB against the 6144 MB cap — concurrency control alone
  cannot fix this (one caller already OOMs). The streaming rewrite is the primary, blocking fix
  (target retained footprint ~0.4-0.5 GB); the single-flight fix is necessary hardening on top so N
  concurrent probes don't multiply even the smaller footprint.
- Fix the stale comment at **`config.yaml:1183`** (repo root, not under `apps/backend/`) —
  `server.memory_cap_mb`'s "~1.3M-row" comment → the real ~3.27M-row figure; keep the cap at 6144.
- Record before/after measurement in **`reports/perf-budgets.md`** — this file does **not exist
  yet** (confirmed), so this iteration creates it: cold `/api/data` completes ≤ 60 s without OOM
  under the 6144 MB cap; retained footprint ~0.4-0.5 GB vs the current ~3+ GB.
- Do **not** touch `scoring.py:377`'s null-sector return — it is honest absence, not a bug.
- Out of scope (per goal.md sequencing + phase spec): fast-platform items B-K, the other `.all()`
  sites in `prices.py` (`:253/:292/:312`, per-symbol-bounded, leave as-is), any DO-NOT-EDIT engine
  file (`referee.py`/`ledger.py`/`online_fdr.py`/`evidence.py`/`mcp/tools.py`).

**Frontend — guard the sector-sort crash + add crash containment**
- `apps/frontend/app/stocks/page.tsx`: guard `SORT_COMPARATORS.sector` —
  `(a, b) => (a.sector ?? "").localeCompare(b.sector ?? "")` (confirmed current code calls
  `.localeCompare` directly on `a.sector`/`b.sector` with no null guard — this is the exact crash).
- Same file, the `sectors` filter vocabulary memo (confirmed at ~line 354:
  `Array.from(new Set(rows.map((r) => r.sector))).sort()`) and its `<Select>` render (confirmed at
  line 517, `{sectors.map((s) => (...))}`): map `null` to an explicit **"Unassigned"** bucket, never
  a literal `null`/blank option; update the `visible` filter predicate (`r.sector !== sector`) so
  selecting "Unassigned" matches the null rows.
- `apps/frontend/lib/api.ts` (~line 279): `StockRow.sector: string` → `sector: string | null`. Then
  run `tsc` and fix **every** flagged consumer product-wide — not just this page (iter-18's own
  lesson: "empty diff = no regression" and a green `tsc` both gave false comfort last time because
  the type was still `string`). Grep for `.sector` across `apps/frontend/` (stock detail page,
  watchlist, any CSV/export, any other format/sort/filter site) and guard each one found.
- Add **`apps/frontend/app/error.tsx`** and **`apps/frontend/app/global-error.tsx`** (confirmed:
  neither exists today). `error.tsx` = contained error card with the sidebar nav still rendered.
  `global-error.tsx` is a Next.js App Router special case — it replaces the root layout, so it must
  render its own `<html>`/`<body>`; flagging this so the developer doesn't get a build error.
- Non-blocking carry-over (F1, only if time permits, does not block DoD): confirm whether the
  Full-history chart on `/stocks/NVDA` (or another >8y name) actually plots pre-2018 weekly bars;
  widen the x-domain to `first_available_date` if not.

## Agents Required
- backend-data: yes -- prefill streaming rewrite + `Bar` record type, single-flight diagnosis/fix,
  config comment fix, perf-budgets.md measurement.
- frontend-ux: yes -- null-safe sector comparator/filter, `sector: string | null` contract fix +
  product-wide consumer sweep, `error.tsx`/`global-error.tsx` crash containment.

## Frontend Present
Frontend Present: yes

## Testing Strategy

**Unit**
- Backend: a targeted test asserting the streamed, column-projected prefill returns the SAME
  rows/order as the prior whole-table load for a sample symbol set (byte-identical values).
- Backend: a concurrency test asserting `compute_coverage`'s single-flight runs **≤ 1** cold
  `_compute_coverage_uncached` (or prefill) invocation under N concurrent callers for the same key
  — this must be written and run BEFORE deciding whether the existing mechanism needs a fix.
- Frontend: a test/type-check proving `StockRow.sector: string | null` and that the sector
  comparator + filter vocabulary handle `null` without throwing, with "Unassigned" selectable.

**Integration**
- `apps/backend/tests/test_bar_cache.py` — the byte-identical snapshot tests are the correctness
  gate for the prefill rewrite; they and the monkeypatch shims (~lines 91, 102, 256) must stay
  green with no signature changes to existing required args.
- Per project memory, the full backend pytest suite is slow (~10-11h on the 30-year fixture) and is
  test-only overhead, not a product issue — run the targeted files above during development; leave
  the full-suite confirmation to the review/QA stage rather than the interactive dev loop, and
  never run it concurrently with anything else (fork-lock risk).

**Browser (canonical `browser-qa-agent` lane — run to completion; iter-18's crashed at exit 70 with
tasks #18-22 pending, a stale task list from that run may still be visible and should not be
confused with this iteration's fresh test plan)**
- J-01: `/stocks` Sector-sort ascending AND descending on the default (~78% null-sector) state — no
  crash, nav intact, rows render sorted; Sector filter dropdown shows "Unassigned" and filtering by
  it works; every row still shows an evidence status badge.
- J-12 verification: `/methodology` membership timeline entries/exits; a mid-history-IPO name
  absent-before/present-after its `min_history_bars` accrual; the `/data` `stale_series` reason
  card rendered in frame.
- Regression smoke (required-still-passing): J-03 (evidence badges on `/stocks`), J-04 + J-05
  (`/evidence` rows + regime label), J-10 (`/stocks/{ticker}` Full-history chart renders
  byte-identical bars post-prefill-rewrite), J-11 (`/evidence` all-FAIL, no stale edge value).
- Deferred iter-18 checks to complete now: Watchlist negative paths (unknown-ticker 404, duplicate
  409); Backtest 2005-02-25 as-of floor.
- Highest priority (goal.md-critical): complete the product-wide anti-goal-#2 language sweep
  (UT-29) — only ~25% executed in iter-18.
- Crash-containment check: force an uncaught client exception → `error.tsx`/`global-error.tsx` card
  renders, nav preserved, never a blank page.
- Screenshot hygiene (recurring lesson): scroll asserted elements into frame or use full-page/clip
  capture; `md5sum` PNGs to confirm distinct + correctly labeled; open the actual asserted frame;
  keep both backend and frontend up for the whole run; confirm no "Backend unavailable" pill.

## Risks and Mitigations

1. **Risk:** the OOM fix silently changes bar values or ordering, corrupting J-10's byte-identical
   chart requirement. **Mitigation:** `test_bar_cache.py` snapshot tests are the hard gate; the
   `Bar` record must expose exactly `.date/.open/.high/.low/.close/.volume`; preserve `ORDER BY
   symbol, date` and `expected_symbols` semantics unchanged.
2. **Risk:** a new prefill/batch parameter becomes required, breaking the monkeypatch shims and the
   2-arg `prefilled_bar_cache(session, expected_symbols=...)` call in `test_bar_cache.py`.
   **Mitigation:** any new parameter must default to today's behavior; no signature-breaking changes.
3. **Risk:** the developer assumes the single-flight is simply "missing" and writes a second,
   redundant locking layer instead of finding why the existing J-100 mechanism let ≥6 concurrent
   prefills through. **Mitigation:** write the concurrency test FIRST, empirically locate the gap
   (key mismatch vs. a bypassing caller), then fix that specific gap.
4. **Risk:** treating concurrency control as sufficient on its own. **Mitigation:** the streaming
   rewrite is the primary fix (a single prefill already exceeds the cap); land it first regardless
   of the single-flight's state.
5. **Risk:** sector-nullability fallout beyond `stocks/page.tsx` (iter-18's own lesson: empty diff +
   green `tsc` both gave false comfort because the type stayed `string`). **Mitigation:** flip the
   type first, then fix every site `tsc` flags product-wide, not just the one file the spec names.
6. **Risk:** repeating iter-18's audit gap — that audit (`docs/handoffs/goal-mcp-loop-iter-18-audit.md`,
   verdict PASS_WITH_GAPS) ran with the backend down and missed the crash sitting in its own cited
   evidence folder; the REAL verdict (REGRESSION) came from the goal-evaluator afterward.
   **Mitigation:** this iteration's auditor must keep both services running for its own checks and
   explicitly reconcile against the ux-regression-reviewer and phase-closure-auditor verdicts before
   writing status.json/qa.md — no "zero blockers" claim may contradict a `-fail-`-named evidence file.
7. **Risk:** `global-error.tsx` breaks the build if written like a normal error boundary.
   **Mitigation:** it must include its own `<html>`/`<body>` (Next.js App Router requirement since
   it replaces the root layout on an error in the root layout itself).
8. **Risk:** several backend engine files (`stocks.py`, `watchlist.py`, `config.py`, `data_manager.py`,
   `forward_testing.py`, `methodology.py`, `universe_resolver.py`, `seed_loader.py`) already carry
   iter-18's uncommitted basis-swap changes in the working tree. **Mitigation:** review/audit should
   scope "this iteration's diff" carefully (e.g. diff against the iter-18 handoff snapshot, not
   assume a clean tree) so iter-18's changes aren't mistaken for iter-19's or vice versa.
