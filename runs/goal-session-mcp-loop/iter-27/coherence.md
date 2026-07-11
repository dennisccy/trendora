# Iteration 27 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-27
**Date:** 2026-07-12
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

Iter-27 is a memory-hardening recovery pass (fixing iter-26's REGRESSION VSZ-exhaustion crash on the
full-universe backfill). Diff scope confirmed via `git diff bc9eb91a..HEAD -- apps/backend/app
apps/frontend`: only `config.py`, `engine/data_manager.py`, `engine/prices.py`, `engine/regime.py`,
`engine/scoring.py` changed; **zero** `apps/frontend` files touched, **zero** new API routes.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Three per-stock scores (Leadership/Entry Quality/Risk) — `scoring:score_stocks` → `GET /api/stocks`, `/api/stocks/{ticker}` | OK | `apps/backend/app/engine/scoring.py:383,399` — `_raw_components`/pass-3 now call the new `bars_asof_window(session, ticker, asof, icfg.max_lookback_bars)` instead of `bars_asof(...)` + a Python `[-N:]` slice. Same module, same canonical function name unchanged; new accessor is byte-identity-proven equal to the old two-step slice by `test_scoring_window.py::test_bars_asof_window_matches_tail_slice_default_and_cached`. Not a second computation path — an internal accessor swap inside the already-canonical module. |
| Market regime score — `regime:score_regime` → `GET /api/dashboard`, `/api/runs/{runId}` | OK | `apps/backend/app/engine/regime.py:301,328,346` — `_index_ma_stack`/`_universe_stats` route through `bars_asof_window`; `_latest_vix` routes through the existing `close_on` (already the canonical single-value accessor, added iter-26). Byte-identity proven by the new `test_score_regime_windowed_equals_unwindowed_across_dates` (3 real cadence dates × full pool, 0 diffs, with a non-vacuous guard that ≥1 regime input actually exceeds the window). |
| Bars / `daily_prices` (underlying data) | OK | `apps/backend/app/engine/prices.py:186-226,235-265` — new `_BarCache.bars_asof_window` + module-level `bars_asof_window` are ADDITIVE siblings of the existing `bars_asof` (unchanged, still present, still the function every other consumer calls). No second serving path: `bars_asof_window` is not exposed through any API route (confirmed via the UI-surface-map's "Backend-Only Changes" section and the empty `apps/frontend` diff). |
| `data_manager.compute_availability` / `compute_coverage` / `compute_capacity` → `GET /api/data`, `/api/data/availability` | OK | Untouched by this diff (`data_manager.py`'s only change is the new `_release_process_memory()` gc/malloc_trim wrapper around `_do_backfill`'s existing compute loop — a process-memory-hygiene step, not a value computation). |
| `server.malloc_arena_max` (new config field) | Not a displayed value | `apps/backend/app/config.py:+9 field, config.yaml:567` — read only by `incredible_auto_dev/scripts/start-backend.sh` at process launch to export `MALLOC_ARENA_MAX`; never served to or rendered by any page/API response. Correctly not registered in the Data Contract (matches the blueprint's own iter-27 clarification). |

No duplicate computation, no non-canonical source, no new unregistered displayed value. The
blueprint (`runs/goal-session-mcp-loop/state/blueprint.md`, iter-27 clarification paragraph) already
documents this exact change as "INTERNAL memory/load-path change BENEATH the already-registered
values... every registered Data Contract value re-serves BYTE-IDENTICALLY" — the diff matches that
description precisely, and the byte-identity claim is backed by concrete new tests
(`test_scoring_window.py`), not merely asserted.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK | `reports/phase-goal-mcp-loop-iter-27-ui-surface-map.md` §Summary: "Frontend surfaces changed: 0, New pages/routes: 0, Modified components: 0, Navigation changes: no." Confirmed independently via `git diff bc9eb91a..HEAD --stat -- apps/frontend` returning empty. |

`/data` (J-16's existing home) and `/` (Dashboard's regime card) are re-verification targets only —
their source files are unchanged; only the backend compute path beneath them changed. No parallel
shell, no duplicate home, no nav-skeleton edit.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The diff range also contains a large vendored `incredible_auto_dev/` framework-subtree pull
  (agents/skills/scripts/tests under `incredible_auto_dev/.claude/`, `incredible_auto_dev/scripts/`,
  `incredible_auto_dev/tests/`) — non-product framework tooling, out of scope for this product-coherence
  audit per the coordinator note. One file in that tree, `incredible_auto_dev/scripts/start-backend.sh`,
  carries a genuine product-relevant edit (exports the new `MALLOC_ARENA_MAX` env var from
  `server.malloc_arena_max` before `exec`ing uvicorn) — reviewed above as part of the memory-hardening
  change; it is process-launch-time only and invisible to the browser, so it has no Data Contract or IA
  implications.
- `dev.sh` (the local dev launcher) is intentionally left uncapped/unhardened per the ui-surface-map —
  this is a known, documented scope boundary (prod/browser-qa launch path only), not a coherence gap.
