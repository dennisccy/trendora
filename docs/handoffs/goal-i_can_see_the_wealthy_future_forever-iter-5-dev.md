# goal-i_can_see_the_wealthy_future_forever-iter-5 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-5
**Date:** 2026-06-01
**Agent:** developer
**Status:** complete
**Depth:** lean — closure / re-verify (verification only)

## TL;DR — NO-OP DEVELOPER PASS (zero code changed)

This iteration is a **closure / evidence-capture re-verify** of the three remaining `partial`
journeys — **J-06** (three scores byte-identical on `/stocks` and `/stocks/NVDA`), **J-11** (watchlist
entry persists across a **real backend restart**), and **J-15** (a measured **warm** load of `/stocks`
from the persisted snapshot). The iter spec scopes Backend and Frontend to **"None — no code change"**:
all three journeys are already built and structurally verified in source / API / DB. The ONLY gap is
**browser evidence capture** — the iter-4 browser-QA step **timed out (exit 124, SKIPPED stub)**
during/after the J-11 backend restart, so the three defining screenshots were never recorded.

**No code was changed. None was needed.** Per the iter-4 lesson, a browser-QA `exit 124` timeout is a
**tooling failure, not a functional gap** — escalating to `full` or touching source would be scope
creep and a regression risk. The value of this pass is (a) the source-level confirmation below that all
three paths are wired to canonical values, and (b) a fast, bounded **sanity test run** proving the three
journeys' structural guarantees still hold. The **browser-qa-agent** completes the closure by driving
each journey's full UI click-path (the only thing that converts a `partial` to `passing`).

## What Was Built

- **Nothing.** No backend code, no frontend code, no `config.yaml`, no schema, no migration, no new
  tests. This is a verification-only iteration per the iter spec's IN SCOPE (Backend: None / Frontend:
  None / New capability: None).

## Files Changed

- **None.** Confirmed by `git diff --stat -- apps/ config.yaml config/` → **0 tracked source files
  changed**. The only working-tree deltas are framework bookkeeping
  (`runs/goal-session-.../telemetry.jsonl`, `trace/`), the decomposer-authored iter-5 spec, and this
  iteration's `runs/` dir + this handoff. No source/config/frontend/schema diff exists — exactly as
  required (and exactly as iter-4 did). If any code change appears in the diff before evaluation, it is
  out-of-scope and must be reverted.

## Verification performed (the actual work of this pass)

### A. Source-level confirmation — all three journeys wired to canonical values

| Journey | Surface(s) | Source confirmation |
|---|---|---|
| **J-06** (score consistency `/stocks` ↔ `/stocks/NVDA`) | `apps/backend/app/api/stocks.py` + `app/engine/snapshot_serving.py` | Both `GET /api/stocks` (`stocks.py:33-35`) and `GET /api/stocks/{ticker}` (`stocks.py:38-41`) resolve the same `ScannerRun` and serve rows via `snapshot_serving.stored_stock_rows()` (`snapshot_serving.py:55-61`), which rehydrates the **same** `ScannerResult.record_json` ordered by rank. The list row and the detail row are the **same object** ⇒ byte-identical Leadership / Entry Quality / Risk (bucket **and** 0–100 number). Detail handler comment: *"the SAME stored row the leaderboard serves (J-06)."* |
| **J-15** (warm load from persisted snapshot, no recompute) | `apps/backend/app/engine/snapshot_serving.py` (module) | Module docstring: *"NO score / regime / sector / theme / return is recomputed here … every served value is read from the snapshot rows that the one `run_scan` persisted once."* Reads are snapshot-served — there is no per-request scan recompute on the `/stocks` read path, which is the structural basis of the warm-load budget. |
| **J-11** (watchlist persistence across a real restart) | `apps/backend/app/api/watchlist.py` + `Watchlist` model (`app/models.py:243`) + `app/db.py` | `Watchlist` is the product's first user-mutable, **DB-backed** table (INSERT on add, DELETE on remove); it stores only `{ticker, reason, created_at, asof_date_added, entry_close}` and reads current scores/setup/invalidation **verbatim** from the same snapshot row `/api/stocks` serves (single source). `db.py` resolves `sqlite:///` to a **file** under the repo (not `:memory:`) and add is `session.commit()`-persisted ⇒ the row survives a backend restart (the J-11 crux: DB persistence, not in-memory). |

The three frontend pages the browser-QA flows drive all exist:
`apps/frontend/app/stocks/page.tsx` (320 lines), `apps/frontend/app/stocks/[ticker]/page.tsx`
(365 lines), `apps/frontend/app/watchlist/page.tsx` (309 lines).

### B. Sanity test run (DoD: "Unit tests still pass — a sanity run, not new tests")

Full suite is heavy (~14 min walk-forward boot — machine memory), so I ran a **tight, journey-relevant
subset** in a single bounded invocation (`loaded_engine` is session-scoped → one boot, shared). This
directly exercises the J-06 / J-11 / J-15 structural guarantees:

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_api_engine.py
tests/test_watchlist_persistence.py tests/test_api_watchlist.py -v`
Result: **26 passed in 220.89s (3m40s)** — 0 failed, bounded by `timeout 600` (no hang).

Keystone tests, by journey:
- **J-06** — `test_api_stock_detail_equals_list_row_single_source_j06` ✓;
  `test_api_watchlist.py::test_single_source_equals_stocks_row_byte_for_byte` ✓;
  `test_asof_detail_equals_list_row_for_historical_date` ✓.
- **J-15** — `test_repointed_handlers_serve_persisted_date_without_recompute` ✓;
  `test_asof_serves_stored_snapshot_matching_run_detail` ✓;
  `test_vcp_served_from_storage_not_recomputed_keystone` ✓.
- **J-11** — `test_watchlist_entry_survives_engine_restart` ✓;
  `test_persisted_watchlist_does_not_create_snapshot_rows` ✓;
  `test_api_watchlist.py::test_add_get_delete_roundtrip` ✓.

(Spec forbids a speculative full ~14-min run; this subset is the agreed "sanity check". Zero code
changed ⇒ no regression is structurally possible — this run only re-confirms the green baseline.)

## The three flows browser-QA MUST capture (the actual closure work)

Run in this **hardened order** (iter-4 lesson — do the two no-restart journeys first and **flush each
result line before** starting the restart journey, so a J-11 hang cannot lose earlier passes):

1. **J-06 (no restart) — score consistency.** Open `/stocks` (latest as-of); make the `NVDA` row
   **legible** (not a zoomed-out thumbnail) and capture `UT-J-06-leaderboard-nvda.png`; note NVDA's
   Leadership, Entry Quality, Risk (bucket **+** number). Click the row → `/stocks/NVDA`; **scroll to
   the three score cards** so all three are fully visible and capture `UT-J-06-detail-nvda-scores.png`.
   Assert the three (bucket + number) are **identical** across the two captures. The two screenshots
   must be **distinct** images (iter-3 lesson — no byte-identical duplicate).
2. **J-15 (no restart) — warm load.** Navigate to `/stocks` once to compile the route (dev mode) and
   **discard** that first timing; navigate away (e.g. `/`) then **back to `/stocks` via in-app
   client-side nav** and measure time-to-interactive of this **warm** load; capture
   `UT-J-15-warm-load.png` and record the number. Confirm leaderboard values equal `/stocks/NVDA`
   (reuse the J-06 observation). If the dev-server warm number is borderline above ~1.5 s, record it
   **honestly** and cite the structural guarantee (snapshot-served, **no per-request recompute** —
   `apps/backend/app/engine/snapshot_serving.py`). **Do not fabricate a passing number.**
3. **J-11 (do LAST — the restart is the timeout risk) — persistence across a real restart.** Open
   `/watchlist`; add `ANET` with reason `"ANET — strong leader, watching pullback"`; confirm it renders
   with date-added, reason, current Leadership/Entry/Risk + setup, price-since-added, and an
   invalidation level; capture `UT-J-11-before-restart.png` and **flush the note now**. Restart the
   backend **by PORT, bounded** (never a broad `pkill -f uvicorn`/`next dev` — machine memory):
   ```bash
   PORT="${CHAIN_BACKEND_PORT:-8835}"
   fuser -k "${PORT}/tcp" 2>/dev/null || (lsof -ti "tcp:${PORT}" | xargs -r kill)
   bash scripts/start-backend.sh >/tmp/iter5-backend.log 2>&1 &
   for i in $(seq 1 30); do curl -sf "http://localhost:${PORT}/api/health" >/dev/null && break; sleep 1; done
   ```
   Reload `/watchlist` and confirm `ANET` is **still present** with its fields; capture
   `UT-J-11-after-restart.png` (**the defining proof** — DB persistence, not in-memory) and flush.

## Known Issues

- **The blocker is QA-tooling, not code.** The reason J-06/J-11/J-15 are still `partial` is solely the
  iter-4 browser-QA `exit 124` timeout that left a SKIPPED stub `ui-test-results.md`; all three are
  built and structurally verified (source above + sanity tests pass). Browser-QA must complete the UI
  capture to convert them.
- **Don't trust a stub — reconcile with the evidence dir (iter-4 lesson).** If `ui-test-results.md` is
  again a SKIPPED/stub but the `*-evidence/` dir has shots, inspect the directory + timestamps directly;
  convert a `partial` **only** if its **defining** step was actually captured (J-06 = both numbers
  legible on both pages; J-11 = the after-restart shot; J-15 = a real warm-load number).
- **Backend may be down.** Nothing may be listening on `:8835` after iter-4 — start the backend
  (`bash scripts/start-backend.sh`) before the browser flows, and on finish kill **only** by port.
- **No regression risk.** Zero code changed this iteration ⇒ the 16 already-green required journeys
  (J-01–J-05, J-07–J-10, J-12–J-14, J-16–J-19) cannot regress; the coherence-auditor should return
  COHERENCE-PASS with only bookkeeping/status-text edits in the diff.
