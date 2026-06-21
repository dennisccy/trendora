**Verdict:** COHERENCE-PASS

## Coherence Audit — Iteration 42 (J-100 bounded-resource backend hardening)

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration index:** 42
**Iter name:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-42
**Snapshot SHA:** eebbc02013b7c8d5da3a4890baa53925ed709fb5

---

### Files changed (from diff stat)

- `apps/backend/app/config.py` — new `ServerOpsCfg` class + `server` field on `Config`
- `apps/backend/app/engine/data_manager.py` — single-flight/result-cache wrapper around `compute_coverage`; `_compute_coverage_uncached` / `_compute_coverage_body` refactor; process-level bar-cache reuse; `reset_coverage_cache` helper; `_coverage_cache_key` / `_db_identity` / `_config_fingerprint` internal helpers
- `apps/backend/app/engine/research.py` — new `_membership_dataset_version` narrow cache-key stamp
- `apps/backend/app/engine/warmup.py` — comment update to reflect new narrow stamp in warm-up commentary
- `apps/backend/tests/test_data_manager_membership_cache.py` — updated tests: `test_forward_return_insert_does_NOT_invalidate_membership_cache`, `test_bar_backfill_DOES_invalidate_membership_cache`
- `apps/backend/tests/test_warmup.py` — import updated from `_dataset_version` to `_membership_dataset_version`
- `config.yaml` — new `server:` block with concurrency/keep-alive/graceful/memory-cap values
- `incredible_auto_dev/scripts/start-backend.sh` — reads ops bounds from config; sets `ulimit -v`; passes `--limit-concurrency`, `--timeout-keep-alive`, `--timeout-graceful-shutdown` to uvicorn

No frontend files changed. New test file: `apps/backend/tests/test_data_manager_concurrency_load.py` (untracked).

---

### Step 1 — Data Contract check

The blueprint's Data Contract (line 385) explicitly pre-registers J-100 as a bounded-resource hardening annotation on the EXISTING canonical path:

> `data_manager:compute_coverage` (single producer; thresholds from config) → `GET /api/data` `coverage`

and describes it as:
> "(a) a SINGLE-FLIGHT guard + result cache … (b) the coverage/membership cache key DECOUPLED from `forward_returns` churn … (c) ONE reused process-level bar cache (load-once) … (d) heavy compute offloaded … NO new displayed value, NO new endpoint, NO new canonical computation … the served `membership_timeline` / `coverage` payload stays byte-identical."

**Duplicate computation check:** The iteration does NOT add a second computation of any canonical value. The public `compute_coverage` function (`data_manager.py`) becomes a single-flight wrapper that delegates all computation to `_compute_coverage_uncached` → `_compute_coverage_body` — the same canonical derivation path. The wrapper adds concurrency control, not a new algorithm.

**New `_membership_dataset_version` stamp:** This is introduced in `research.py` as a narrow internal cache-invalidation key. It queries the DB for `max(scanner_runs.id)`, `count(scanner_runs)`, `max(daily_prices.date)`, `count(daily_prices)`, and `cfg.indicators.min_history_bars`. It does NOT compute membership, does NOT compute coverage, and does NOT appear in any served payload — it is an internal cache-key input only. This is not a duplicate of `_dataset_version` (the J-72/J-87 stamp): the blueprint explicitly calls for this decoupling and the two stamps serve distinct cache layers with distinct invalidation semantics.

**Non-canonical source check:** No new UI surface fetches any registered value from a non-canonical endpoint. No frontend changed. The UI surface map confirms: "Backend-only phase — No UI surfaces affected."

**New displayed values:** None. The iter spec states "New information displayed: None. Every served `coverage` / `membership_timeline` / `universe_diagnostic` value is byte-identical to today." No unregistered values to note.

Result: **no Data Contract violation.**

---

### Step 2 — Information Architecture check

The UI surface map (`reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-42-ui-surface-map.md`) states: "Status: N/A — Backend-only phase (Frontend Present: no). No UI surfaces affected."

The diff confirms: zero frontend files changed (no `apps/frontend/` files in the diff). No new routes, pages, nav entries, or layout shells were introduced.

Result: **no IA violation.**

---

### Step 3 — Subjective observations (advisory)

None. This is a pure backend performance/stability iteration: single-flight concurrency guard, narrow cache-key decoupling, shared bar-cache reuse, and ops guards in the start script. No display changes, no label changes, no layout drift.

---

### Summary

| Check | Result |
|---|---|
| Duplicate computation of a registered canonical value | PASS — none found |
| Non-canonical source for a registered value | PASS — none found |
| New displayed value not in Data Contract | PASS — no new displayed value |
| New page/route with no nav path | PASS — no new pages/routes |
| New page/route reachable in >2 clicks | PASS — no new pages/routes |
| Duplicate home for an existing entity | PASS — none |
| Parallel shell | PASS — none |

**Verdict: COHERENCE-PASS** — no objective violations. Iteration 42 is a backend-only performance/stability hardening that introduces no new displayed value, no new endpoint, no new canonical computation, and no navigational surface. All changes are internal cache-key refinement, single-flight concurrency guard, shared bar-cache reuse, and ops guards — fully aligned with the blueprint's pre-registered J-100 annotation on the existing `compute_coverage` → `GET /api/data` canonical path.
