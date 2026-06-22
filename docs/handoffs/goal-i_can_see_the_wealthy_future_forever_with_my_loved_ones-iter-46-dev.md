# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-46 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-46
**Date:** 2026-06-22
**Agent:** developer
**Status:** complete (verify-only — zero source diff)

## What Was Built
Nothing. This is the **verify-only** sixth-repeat lean-reverify iteration (iter-30→31 / 36→37 / 42→43 pattern). **Zero source files changed** — the working tree carries no `apps/`, `scripts/`, or source-code diff against HEAD (only framework-managed `runs/` telemetry/dispatch artifacts + the new iter-46 spec). The intent was to capture LIVE rendered evidence for J-103/J-104 on a fresh, warmed, single-fetch-at-a-time backend.

**Outcome: PARTIAL. J-103 and the light J-104 labs render live and correct; but two heavy J-104 labs (event-study, factor-lab) hit a `MemoryError` on the now-3.3 GB live DB — a GENUINE defect, NOT a regression. Per the iter spec OUT OF SCOPE ("if a genuine defect surfaces, record it and STOP — do not patch it in this verify-only pass"), it is recorded here and NOT patched. The evaluator must scope a follow-up; this iteration is NOT a clean GOAL_ACHIEVED candidate.**

## Zero-source-diff verification (the verify-only contract)
- `git diff --stat HEAD` over `apps/`, `scripts/`, `docs/goal.md`, and all `*.py/*.ts/*.tsx/*.js/*.json`: **empty**.
- No untracked source files. Confirmed the verify-only baseline holds.

## Live evidence captured (fresh, warmed `:8835`; one heavy fetch at a time)
Operational prereq done: prior hung uvicorn was already cleaned (port :8835 free on arrival). Brought up a fresh backend, waited for `GET /api/health` `readiness: ready` / `warmup: ok` (585 symbols, seed latest 2026-06-16, db_ok). All fetches sequential — never concurrent (pool-exhaustion lesson).

### J-103 — Severity-velocity × Regime study — CONFIRMED (renders + As-of leg works)
- `GET /api/research/severity-velocity` → **HTTP 200**. Real **3×3 regime-family × velocity-sign matrix**: 9 cells, 6 with real data, **3 zero-N cells correctly NA** (`mean=None, win_rate=None` — no fabrication). `n_total=1147`, sum of cell N == 1147 (coherent).
- Verbatim honest verdict/caveats all present: **"not supported"**, **"bounce"**, **survivorship**, **bull-dominated**, **underpowered**.
- **As-of leg (closes the iter-45 UT-09 false-negative with POSITIVE evidence):** `GET /api/research/severity-velocity?as_of=2022-12-31` → HTTP 200, `asof_date=2022-12-31`, **N shrinks 1147 → 301**. The param IS honored at the correct underscore spelling `as_of=` (the frontend's `withAsOf` sends exactly this); the iter-45 `?asof=` curl was the false-negative, not the code.
- **N= drill-down count-coherence** (`kind=severity-velocity&family=risk_on&velocity_sign=rising&horizon=20`): all-history samples `total=241 == chip N`; As-of=2022-12-31 samples `total=14 == chip N` (14 < 241). All As-of sample rows dated ≤ 2022-12-31 (**no lookahead**). Rows carry ticker + snapshot_date + regime + values + forward_return.

### J-104 — relocated labs — PARTIAL
- **RENDER OK (HTTP 200, real figures):** `regime-setup-pattern` (14.7 KB), `recovery-turn-edge` (4.1 KB), `factor-combination` (4.7 KB), `severity-velocity` (3.3 KB). `downtrend-opportunity` returned 200 with real figures on the first fresh boot.
- **FAIL (HTTP 500 — `MemoryError`):** `event-study` and `factor-lab`. Reproducible on a fresh, fully-warmed, low-memory (~100 MB RSS) backend — i.e. NOT memory pressure from prior hammering this time.

## THE DEFECT (recorded, NOT patched — OUT OF SCOPE for this verify-only pass)
**`/api/research/event-study` and `/api/research/factor-lab` raise `MemoryError` on the live DB.**

- **Root cause:** `_event_study_members_by_horizon` (apps/backend/app/engine/research.py:824) runs `select(ForwardReturn).where(ForwardReturn.horizon.in_(horizons))` and materializes the entire result via `.all()` into ORM objects. The live `apps/backend/data/trendora.db` is **3.3 GB** with **3,081,454 `forward_returns` rows** (1,371 daily `scanner_runs` spanning 2021-01-04 → 2026-06-16; 609,166 `scanner_results`). All-history materializes ~3.08M ORM objects → `MemoryError`. Even As-of=2022-12-31 still materializes **799,485** rows → same error.
- **NOT a regression:** `git log -S` shows this unbounded all-history `.all()` materialization was introduced in **iter-20 (commit 6733c1d, 2026-06-15)** and is **byte-identical** to what shipped in the iter-21 / iter-43 / iter-45 GOAL_ACHIEVED-candidate states. The iter-44/45 route-split did NOT touch it. The code did not change; the **data scale grew** (the restored daily-history backfills — MEMORY: J-85 rebuild + chunked backfills — took the DB from a small seed to 1,371 daily snapshots / 3 M forward returns).
- **Environmental aggravator:** host RAM dropped from **18 GiB → 10 GiB** mid-iteration (this is a shared multi-project machine; another cgroup/process reclaimed ~8 GiB). The lower ceiling is why the all-history materialization now overflows where it previously fit. A third fresh boot's background warm-up (`backfill_forward_returns` at warmup.py:155) also hit `MemoryError` — **non-fatal** (the J-40/J-41 serve-fast design: warm-up flips to `failed` but the backend still serves `/api/stocks` 200, `/api/runs` 200, `/api/research/severity-velocity` 200).
- **No fabrication:** the labs return an honest HTTP 500 / "Backend unavailable" under the failure — they never synthesize figures. That part of the anti-goal contract holds.

## Why this is NOT the iter-45 false-failure
Iter-45's event-study/factor-lab skips were a CPU-saturated backend (PID 72189 pegged); a quiet restart fixed them. **This iter-46 failure reproduces on a freshly-booted, fully-warmed, ~100 MB-RSS, idle backend at the very first fetch** — it is a data-volume/host-memory ceiling, not transient contention. A restart does NOT fix it; only a code change (server-side chunking/streaming or an `as_of`-bounded cap on the all-history fetch) or more host RAM would. That code change is OUT OF SCOPE here.

## Files Changed
None. Zero source diff (verify-only).

## Tests Run
Targeted isolated corroboration modules on the quiet host (TestClient fixtures, small seed — do NOT exercise the 3.3 GB live DB, so they pass):
Command: `cd apps/backend && .venv/bin/python -m pytest <module> -q`
- `tests/test_severity_velocity.py` — **15 passed** (J-103 as_of-filter + cache byte-identity)
- `tests/test_research.py` — **93 passed** (J-29/J-63/J-91/J-90 + count-coherence)
- `tests/test_samples.py` — **15 passed** (J-51/J-65 count-coherence)
- `tests/test_no_magic_numbers.py` — **2 passed**
- `tests/test_db.py::test_create_all_produces_expected_tables` — **1 passed**

Full backend suite: launched **nohup-async** (`/tmp/iter46-fullsuite.log`) on the now-quiet host; NOT blocked on. The flushed `0 failed, EXIT 0` gate is the pump's to confirm. Note: the suite uses small test fixtures (not the live 3.3 GB DB), so it will NOT hit the live-DB MemoryError; re-run any `test_warmup.py` / `test_watchlist_persistence.py` E/F in isolation before attributing (documented slow-boot flake).

## Known Issues
1. **(BLOCKER for J-104 / GOAL_ACHIEVED candidacy)** `event-study` and `factor-lab` all-history labs `MemoryError` on the live 3.3 GB / 3.08M-row DB (and even at As-of=2022-12-31, 799K rows). Genuine defect, recorded not patched per OUT OF SCOPE. Suggested follow-up scope (a real lean fix, not this verify pass): bound/stream the `_event_study_members_by_horizon` `ForwardReturn` fetch — e.g. `yield_per`/server-side chunking, or push the per-horizon grouping into the cached aggregate so the read path never materializes ~3M ORM rows. The J-104 acceptance ("load without error under normal use") is currently UNMET on this DB scale for these two labs.
2. Host RAM was reduced from 18 GiB → 10 GiB mid-iteration on this shared machine; the third backend boot's background warm-up hit a non-fatal `MemoryError` (serving unaffected). The currently-running backend on :8835 serves all light endpoints (stocks/runs/severity-velocity + the 3 light labs) at HTTP 200 despite `warmup: failed`.
3. J-22/J-23/J-24 remain honestly **blocked-NA** (data-walled; non-vetoing per goal.md:105-108) — unchanged, untouched.

## Servers left running
A fresh backend on **:8835** (serves the light endpoints + J-103 severity-velocity + the 3 light labs for the browser-QA agent's render-capture; the 2 heavy labs will return the honest 500/"Backend unavailable" under the live-DB MemoryError). The frontend `next dev` on **:3835** (PID 72299, pre-existing) is up. No stray uvicorns on other ports (port-scoped cleanup only, per MEMORY — no broad pkill on this multi-project machine).
