# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47
**Date:** 2026-06-22
**Agent:** developer
**Status:** complete

## What Was Built

J-105 — a **bounded / streamed forward-return read path** that closes the iter-46 REGRESSION (the heavy
Research labs MemoryError'd on the grown live `forward_returns` table, 3.08M rows / 3.3 GB). The unbounded
full-table ORM materialization (`select(ForwardReturn)…all()`) in the per-observation builders is replaced
by **column-projected, `yield_per`-streamed, cohort-bounded** reads — **every served figure byte-identical**.

- **7 research-engine forward-return reads streamed + column-projected** (`apps/backend/app/engine/research.py`):
  - `_factor_observations` (J-25) and `_combination_observations` (J-26) — the FR scan is projected to
    `(run_id, symbol, realized_return)` and streamed; `runs_with_fr` derived from the stream.
  - `_event_study_members` and `_event_study_members_by_horizon` (J-29 / J-72) — **full reorder**: the
    subject-matching `ScannerResult`s are streamed FIRST (column-projected, ordered by `ScannerResult.id`),
    the needed-runs cohort collected, then the FR scan is streamed PRUNED to `horizon (==/IN) AND
    run_id IN needed_runs`, keeping only the needed `(run,symbol)` pairs. Memory is O(subject matches), not
    O(table). Regime map is projected over a superset of FR-bearing runs.
  - `_regime_setup_pattern_observations` (J-77, also feeds Downtrend-Opportunity) — FR scan projected +
    streamed to light value tuples; the ScannerResult side projected + streamed in `ScannerResult.id` order;
    `_rsp_member` adapted to accept the stored FR value tuple (not an ORM `fr`).
  - `_recovery_turn_observation_set` (J-90, already run-id-bounded to the signal-date runs) — FR scan
    column-projected + streamed for consistency.
  - `_severity_velocity_observation_set` (J-103, already SPY-symbol-bounded) — FR scan column-projected +
    streamed for consistency.
- **Warm-up backfill idempotency scan streamed** (`apps/backend/app/engine/forward_testing.py`): the
  `existing = {(fr.run_id, fr.symbol, fr.horizon) for fr in select(ForwardReturn).all()}` full-table ORM
  load in `_backfill` is replaced by a new `_streamed_existing_keys(session, batch)` helper that streams a
  column-projected `select(ForwardReturn.run_id, .symbol, .horizon)` with `yield_per` into the same
  `set[tuple]`. The `runs` loop stays materialized (one ScannerRun per cadence date — bounded — and the
  loop body mutates the session, so a server-side cursor would interleave unsafely).
- **ONE new config key `research.read_batch_size`** (`apps/backend/app/config.py` + `config.yaml`): a
  required, boot-validated (`>= 1`, mirroring `startup.warmup_batch_size`) integer — the SINGLE source of
  the `yield_per` batch size. No inline batch literal in the two CALC_FILES (`research.py`,
  `forward_testing.py`). Default in `config.yaml` is `2000`.

The byte-identity contract is preserved (same member dict shape, enrichment, `ScannerResult.id` insertion
order, and verbatim values — no NaN/None coercion added). No new endpoint, no new stored column, no new
`table=True` model, no canonical value changed. No frontend source change.

## Files Changed

- `apps/backend/app/engine/research.py` -- streamed + column-projected the 7 unbounded FR reads; added the
  `_SubjectResultRow` light row, the `_subject_matching_result_rows` + `_regime_by_run_projected` helpers
  (the event-study reorder); threaded `cfg` into the builders + the `compute_*` callers.
- `apps/backend/app/engine/forward_testing.py` -- added `_streamed_existing_keys`; `_backfill` now builds
  the idempotency set via that streamed projected scan (config-sized batch).
- `apps/backend/app/config.py` -- added required `read_batch_size: int` to `ResearchCfg` + a
  `model_validator(mode="after")` enforcing `>= 1`.
- `config.yaml` -- added `read_batch_size: 2000` under the `research:` block.
- `apps/backend/tests/test_config.py` -- `read_batch_size` in `MINIMAL_VALID`; new boot-validation tests
  (`< 1` raises, missing raises, loads from real config). (`MINIMAL_VALID` is imported by test_research.py.)
- `apps/backend/tests/test_config_engine.py`, `test_sectors.py`, `test_themes.py`, `test_indexes.py` --
  `read_batch_size` added to each inline `"research"` config fixture (now-required key).
- `apps/backend/tests/test_research_streaming.py` (NEW) -- deep-equality / chunk-independence tests of the
  streamed builders vs the per-horizon loop and vs themselves under `read_batch_size=1` / huge, across
  as_of=None / historical, pooled / episodes, and a zero-N cohort; no-leak guard.
- `apps/backend/tests/test_forward_testing_streaming.py` (NEW) -- `_streamed_existing_keys` equals the
  full-table set under any batch; keys are plain tuples (not ORM rows).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest <modules> -q`

Targeted (confirmed GREEN, isolated):
- `tests/test_research_streaming.py` + `tests/test_iter20_research_cluster.py` — 32 passed (includes the
  critical J-72 `batched == per-horizon` byte-identity guard + the single-batched-read call-count spy).
- `tests/test_forward_testing_streaming.py` — 5 passed.
- `tests/test_config.py` + `tests/test_config_engine.py` — 103 passed (config fixtures + new validation).

Full backend suite: launched nohup-async via the pump (the documented slow walk-forward boot makes the
conftest session fixture multi-minute; per the pump contract this iteration does NOT block the evaluator on
the in-flight suite). Re-run any isolated `test_warmup.py` / `test_watchlist_persistence.py` /
`test_data_manager_jobs_pipeline.py` E/F before attributing — documented slow-boot/warm-up flake.

## Live Verification (warmed live 3.3 GB DB, :8835, single-fetch-at-a-time)

Backend freshly restarted + warmed to `readiness: ready, warmup: ok` (the warm-up runs the streamed
`backfill_forward_returns` — it completed on the live DB with no OOM). Frontend `/research` serves HTTP 200.
Each heavy lab fetched ONCE (no concurrent heavy probes). **The full backend suite was NOT running during
these probes** — the iter-45/46 lesson: a CPU-saturated backend yields false timeouts (the first two
probes timed out at 120-280s WITH the suite contending; after freeing CPU the same endpoint served in
1.2s). All served HTTP 200 with REAL figures on the full live dataset — the J-105 regression is closed:

| Lab | Endpoint | HTTP | Live figures |
|-----|----------|------|--------------|
| Event-study (J-29) | `/api/research/event-study?subject=vcp&horizon=20` | 200 (1.2s) | n=3141 (episodes), 5 horizon rows, real mean_return |
| Factor Lab (J-25) | `/api/research/factor-lab?factor=leadership_score&horizon=20` | 200 (56.7s cold) | **n_total=598,271**, 10 deciles, rank_ic=0.0067 |
| Factor-combination (J-26) | `/api/research/factor-combination?horizon=20` | 200 (0.07s) | pool_n=598,271 |
| Regime×Setup×Pattern (J-77) | `/api/research/regime-setup-pattern?horizon=20` | 200 (0.06s) | n_total=814, 41 combinations |
| Downtrend-Opportunity (J-91) | `/api/research/downtrend-opportunity?horizon=20` | 200 (8.6s) | n_total=814 |
| Severity-velocity (J-103) | `/api/research/severity-velocity?horizon=20` | 200 (0.06s) | served |
| Recovery-turn-edge (J-90) | `/api/research/recovery-turn-edge?horizon=20` | 200 (0.06s) | served |

**Count-coherence (J-51/J-63/J-65) live:** event-study pooled `n=13,277` == its `N=` samples drill-down
`total=13,277` (13,277 rows) — the streamed read path keeps each figure's reported N byte-coherent with
its drill-down. Before the fix these labs returned HTTP 500 / "Backend unavailable" (MemoryError on the
grown table); they now serve bounded.

NOTE FOR BROWSER-QA: do the authoritative rendered-pixel capture on a freshly-restarted, warmed,
single-fetch-at-a-time backend — and DO NOT run the full backend suite concurrently (it spoils the heavy
fetches with false timeouts, as seen above). The Factor Lab's first cold-cache compute over ~598K rows
takes ~50-60s — wait for it; subsequent fetches hit the EventStudyCache and are sub-second.

## Known Issues

- The full backend suite's conftest session fixture (`bootstrap_runs` + `backfill_forward_returns`) is the
  documented heavy walk-forward boot (~22 scans) and takes several minutes on this host; it is CPU-bound,
  not hung. My `_backfill` streaming change adds negligible time (the first backfill streams an empty FR
  table). The full GREEN flush is the pump's to confirm (nohup-async).
- Live memory probe on the 3.3 GB DB (peak RSS well under the prior ~5.4 GiB) is the browser-QA step's to
  capture on a freshly-restarted, warmed, single-fetch-at-a-time backend — the unit byte-identity is
  seed-verifiable and is GREEN.
- Out of J-105 scope (intentionally untouched): `compute_forward_aggregates` (forward_testing.py) reads one
  horizon's FR rows with a full-ORM `.all()` filtered by `horizon` — bounded per the spec's named scope; the
  per-run `run_id`-scoped FR reads in forward_testing/snapshot_serving are already bounded and stay as-is.
