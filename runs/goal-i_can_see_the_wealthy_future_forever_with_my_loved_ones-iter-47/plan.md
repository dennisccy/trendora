# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47 Execution Plan

Backend read-path refactor (J-105) that closes the iter-46 REGRESSION: the heavy Research
labs MemoryError on the grown live `forward_returns` table (3.08M rows / 3.3 GB) because
`_event_study_members_by_horizon` and siblings materialize the whole table as ORM objects via
`select(ForwardReturn)…all()`. Replace those with column-projected, `yield_per`-streamed,
cohort-bounded reads — every served figure byte-identical. Restores J-25 / J-26 / J-29 (and
J-104 "labs load reliably") to passing. Resume flag `--acknowledge-regression`.

## What to Build
- Replace the unbounded `select(ForwardReturn)…all()` ORM materialization with a column-projected,
  `yield_per`-streamed read in the per-observation builders that feed the heavy labs — primary
  culprit `_event_study_members_by_horizon` (research.py:823/828) and the same-shape per-horizon
  siblings (research.py:196/201, 392/397, 759/764, 1408/1413, 1633/1637, 2232/2239). Project to the
  lightweight field tuple the join + member shape actually consume (e.g. `horizon, run_id, symbol,
  realized_return, mae, mfe, max_drawdown`). Push subject-/factor-/horizon-scoped cohort filters into
  the SQL scan so the stream only yields rows the study reads.
- Replace the warm-up idempotency-set materialization in `_backfill_all_runs`
  (forward_testing.py:379-380, `{(fr.run_id, fr.symbol, fr.horizon) for fr in select(ForwardReturn).all()}`)
  with a streamed, key-projected scan (`select(ForwardReturn.run_id, ForwardReturn.symbol,
  ForwardReturn.horizon)` consumed with `yield_per`). Per-run reads already scoped by `run_id`
  (forward_testing.py:865-867, :908) are bounded — leave them unless they share the unbounded shape.
- Add ONE new config key `research.read_batch_size` (int `>= 1`), validated at boot in `config.py`
  `ResearchCfg` exactly like `startup.warmup_batch_size` (a `model_validator(mode="after")` raising
  `ValueError("research.read_batch_size must be >= 1")`). Set it in `config.yaml` under the existing
  `research:` block (line 789). Read it for every `yield_per(...)` batch size — NO inline numeric
  literal in calc code (`test_no_magic_numbers` will reject it). Add the key to EVERY inline test
  config dict that builds a `ResearchCfg`/full config (grep the `research` section key across
  `apps/backend/tests` — known fixtures: test_research.py, test_config.py, test_config_engine.py,
  test_sectors.py, test_themes.py, test_indexes.py; the count grows — do not trust a fixed list).
- Preserve the byte-identity contract: the returned `{horizon: [members]}` (member dict shape,
  enrichment, and insertion order — `ScannerResult.id` ascending) MUST be byte-identical per horizon
  to the prior implementation, across `as_of=None` (all-history) and `as_of` (≤ D scoping). The stream
  MUST preserve the exact `order_by(ScannerResult.id)` ordering the prior `.all()` produced.

## Agents Required
- developer: yes -- backend read-path refactor (research.py + forward_testing.py streaming), the
  `research.read_batch_size` config key + boot validation + every test fixture, and the new
  deep-equality / idempotency-count tests. No frontend source change expected.
- backend-data: yes -- this IS the backend read-path / data-volume work.
- frontend-ux: no -- no frontend source change; the labs already render the served aggregates.
  `Frontend Present: yes` is set ONLY to force the live browser-QA render-capture in THIS iteration.

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/engine/research.py` -- stream/column-project the 7 unbounded `select(ForwardReturn)`
  reads (lines 196, 392, 759, 823, 1408, 1633, 2232); push cohort filters into SQL; preserve ordering.
- `apps/backend/app/engine/forward_testing.py` -- stream the warm-up idempotency-key scan (line 379-380).
- `apps/backend/app/config.py` -- add `read_batch_size: int` to `ResearchCfg` (~line 1116) + a
  `model_validator(mode="after")` enforcing `>= 1`, mirroring `startup.warmup_batch_size` (line 472).
- `config.yaml` -- add `read_batch_size` under the `research:` block (line 789).
- `apps/backend/tests/test_config.py`, `test_config_engine.py`, `test_research.py`, `test_sectors.py`,
  `test_themes.py`, `test_indexes.py` (+ any other grep hit) -- add `read_batch_size` to each inline
  `ResearchCfg`/config fixture so they still construct.
- `apps/backend/tests/test_research.py` (or a new `test_research_streaming.py`) -- deep-equality test
  of the bounded/streamed builder vs the prior per-observation reference across as_of=None / historical
  as_of, pooled / episodes, and a zero-N cohort; drive the REAL builder/endpoint (no hand-rolled stand-in).
- `apps/backend/tests/test_forward_testing.py` (or equivalent) -- assert `_backfill_all_runs` /
  `backfill_forward_returns` builds the SAME idempotency set and inserts 0 duplicate rows after the
  streamed-key change (idempotency + INSERT-only contract preserved).
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-dev.md` -- dev handoff.

## UI Evolution
- New user-facing capability: RESTORED capability — the five heavy Research labs (event-study,
  factor-lab, factor-combination, regime×setup×pattern, downtrend-opportunity) and their `N=` samples
  drill-downs load on the full live dataset again instead of "Backend unavailable"/"Loading…". No new feature.
- New information displayed: None. Every matrix cell, mean/win-rate/N, and every `N=` cohort is
  byte-identical to before.
- New user actions: None.
- UI surface changes: None — the `/research` hub and its `/research/*` sub-routes (built iter-45) are unchanged.
- Navigation changes: none.

## Visual Requirements
- Component patterns: No new components. Existing `/research/*` lab pages, matrices, `N=` chips, and the
  `/research/samples` drill-down render unchanged.
- Layout: Unchanged — existing Research hub + sub-route pages.
- Key visual effects: None new. Verify existing loading / error / empty treatments still display correctly
  (the labs must show REAL figures, not skeleton / "Backend unavailable" frames, on the live dataset).
- States to handle: confirm loading → loaded transition completes (no permanent skeleton), and that a
  genuine fault still surfaces the honest stale/unavailable state (never fabricated figures).

## Key Test Scenarios
- Target journeys via browser-qa-agent on REAL rendered figures, captured on a FRESHLY-RESTARTED, WARMED,
  single-fetch-at-a-time backend (reject "Loading…"/"Backend unavailable"/skeleton frames):
  - J-29 `/research/event-study`: per-horizon mean/win-rate/N matrix renders REAL cells; `N=` chip drills
    into count-coherent `/research/samples`.
  - J-25 `/research` Factor Lab: decile sort + rank-IC per factor render REAL figures; `N=` drill-down works.
  - J-26 Factor Lab multi-factor composite cohort renders REAL figures.
  - J-105: all five heavy labs + their `N=` drill-downs return HTTP 200 on the full live dataset; capture
    rendered pixels of each.
- Required-still-passing live smoke: J-104 (all 5 heavy labs reliable), J-77 (regime×setup×pattern),
  J-91 (downtrend-opportunity), J-90 (recovery-turn-edge), J-32 (As-of⇄All-history toggle),
  J-51/J-65 (`N=` count-coherence), J-72 (vectorized-refactor figures), J-63 (count-coherence),
  J-06 (single source: NVDA detail == leaderboard), J-18 (0 native `input[type=date]`),
  J-07 (Risk-Off → 0 Actionable).
- Offline unit/integration (committed seed — byte-identity is seed-verifiable):
  - Deep-equality of the streamed `_event_study_members_by_horizon` + siblings vs the prior reference
    across as_of=None / historical as_of, pooled / episodes, and a zero-N cohort (REAL builder, no stub).
  - `test_research.py` + `test_samples.py` count-coherence stay green (each figure's reported N equals
    its `N=` samples drill-down).
  - `_backfill_all_runs` / `backfill_forward_returns` builds the SAME idempotency set, inserts 0
    duplicate rows after the streamed-key change.
  - `research.read_batch_size` validated `>= 1` at boot; `test_no_magic_numbers` green (config-sourced,
    no inline literal in CALC_FILES).
  - `test_db.py::test_create_all_produces_expected_tables` green AND UNCHANGED — J-105 adds NO new table.
- Error cases: a genuine compute fault still surfaces an honest error/unavailable state (No fabricated
  data); a horizon/cohort short on samples shows NA/partial with sample size (Honest partial windows);
  an invalid `view`/`horizon`/cohort param is still rejected — but no 4xx on a displayable `N=` cell.
- Full backend suite reaches `0 failed, EXIT 0` (nohup-async via the pump; NEVER block the evaluator on
  the in-flight suite; re-run any isolated `test_warmup.py` / `test_watchlist_persistence.py` /
  `test_data_manager_jobs_pipeline.py` E/F before attributing — documented slow-boot/warm-up flake).

## Assumptions & Execution Notes (documented, not blocking)
- `config.yaml` lives at the REPO ROOT (`/home/dennisccy/Git/trendora/config.yaml`), `research:` block at
  line 789 — NOT under `apps/backend/`. Add `read_batch_size` there.
- Boot validation goes in `ResearchCfg` (`extra="allow"`, no existing validator) as a
  `model_validator(mode="after")`, mirroring the `startup.warmup_batch_size < 1` raise at config.py:472.
- All 7 research + 1 forward_testing line numbers in this plan were confirmed accurate against HEAD; the
  developer should re-confirm exact lines before editing (the file may shift as edits land).
- Browser-QA: plan the Playwright fallback UP FRONT and `md5sum` the evidence dir FIRST (Chrome MCP CDP
  has emptied the dir on iters 38/39/40/42). KILL any stale uvicorn by PORT (no broad pkill on this
  multi-project machine), wait for `GET /api/health` readiness `ready`, and NEVER concurrently probe
  heavy `/research/*` (one heavy fetch per page — pool-exhaustion lesson). Verify the EXACT query-param
  spelling `as_of` (underscore) before trusting any curl-based "ignores param" FAIL.
- Seed-loading fixtures can exceed a subagent Bash 10-min cap (SIGKILL 137 in a bg wrapper is the harness
  kill, NOT a test failure) — split fast no-boot byte-identity tests from slow seed-boot ones; gate the
  GOAL_ACHIEVED candidacy on the pump's `nohup`-launched flushed full suite.

## Scope Guard (out of scope — excluded per spec)
- NO change to any canonical score / return / membership / aggregate value, or the Risk-Off→Actionable gate.
- NO new endpoint, new stored column, or new `table=True` model (`test_db.py` expected-tables stays
  UNCHANGED — the iter-20/21 new-table trap does NOT apply).
- NO re-trigger of the J-85 `kind:rebuild` (~11h, destructive — data is correct).
- NO frontend feature edits (touch frontend ONLY if browser-QA finds a genuine render defect).
- J-22/J-23/J-24 stay honestly blocked-NA (data-walled; non-vetoing per goal.md:105-108) — untouched.

## Goal Alignment
J-105 was authored in `docs/goal.md` (lines 2379-2388) specifically to close this regression; the spec
matches it exactly. No drift. This iteration restores every buildable Must-have (J-01..J-21, J-25..J-105)
to positive-evidenced and is a sound GOAL_ACHIEVED candidate once J-25/J-26/J-29 flip back on LIVE figures,
J-104 reliability is MET, the byte-identity deep-equality + count-coherence tests are green, the full suite
flushes `0 failed, EXIT 0`, and coherence passes with zero new anti-goal violation.
