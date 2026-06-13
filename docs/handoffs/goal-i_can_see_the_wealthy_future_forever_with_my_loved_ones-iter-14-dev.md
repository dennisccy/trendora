# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete

## What Was Built

J-63 — Event study is overlap-honest (first-trigger **Episodes** by default, one-click **Pooled** for byte-identical prior figures).

### Backend
- **Episode-collapse helper** (`apps/backend/app/engine/research.py`):
  - `_run_position_index(session, as_of)` — builds `run_id → ordinal` over the GLOBAL ordered `ScannerRun.asof_date` sequence (unique per run). Consecutiveness is judged on this run-date SEQUENCE (ordinal difference == 1), NOT calendar adjacency. Scoped by `as_of` to the same point-in-time window.
  - `_collapse_to_episodes(members, run_position)` — pure in-memory grouping: for each ticker, maximal runs of consecutive ordinals collapse to ONE first-trigger observation carrying stored `return`/`mae`/`mfe`/`regime`/`sector` verbatim; a gap in the ordinal sequence splits episodes. Deterministic; recomputes nothing.
  - `_event_study_observation_set(session, subject, horizon, view, as_of)` — the SINGLE membership builder used by both the aggregate and the samples drill-down. `view="pooled"` returns the unchanged `_event_study_members` list; `view="episodes"` returns its collapse.
  - Constants `VIEW_EPISODES` / `VIEW_POOLED` / `ALL_VIEWS`.
- **`view` threaded through `compute_event_study(...)`** (default `episodes`). The pooled branch routes through the UNCHANGED pre-J-63 code path (byte-identity guard). The episode collapse is per-horizon; the run-ordinal index is loaded once and reused.
- **Three disclosure values** on the payload (both views): `n` (current view, selected horizon), `unique_symbols`, `episode_count` (view-independent — counts first-trigger episodes regardless of which view renders).
- **`view` param on `GET /api/research/event-study`** (`apps/backend/app/api/research.py`), validated to `{episodes, pooled}` → 422 otherwise.
- **Samples cohort `view`** — `_event_study_samples(...)` + `GET /api/research/samples` accept `view` (event-study kind), reuse the SAME `_event_study_observation_set` builder, echo `view` on the cohort, validate → 422.
- **Glossary entries** — `config.yaml` `methodology.terms`: "Episode" + "Pooled (per-signal-day)" (category `forward_evidence`, plain authored terms, no `ref`/threshold). Served catalog grows to 122 terms (>=100 holds).

### Frontend
- `apps/frontend/app/research/page.tsx` — `EventStudyViewToggle` segmented group (Episodes/Pooled, active pill, default Episodes, styled like `AnalysisModeToggle`); local `view` state in `EventStudyLab` threaded into `fetchEventStudy` and into every `N=` chip cohort; `EventStudyDisclosure` line (n / unique symbols / episodes, read verbatim, `TermInfo` tooltip kept outside the buttons — no nested-interactive hazard). The stale "Pooled occurrences" meta line was replaced by the view-aware disclosure line.
- `apps/frontend/lib/api.ts` — `fetchEventStudy(..., view?, signal?)`; `EventStudyResponse` gains `view`/`n`/`unique_symbols`/`episode_count`; `SampleCohort` gains `view`.
- `apps/frontend/lib/samples-link.ts` — `EventStudyCohortParams.view` + serialized into the samples href (cohort selector only — does NOT touch `?asof`/scope).
- `apps/frontend/app/research/samples/page.tsx` — the cohort detail line shows the resolved view (Episodes/Pooled); the `view` param flows to the backend automatically via `samplesFetchParams` (no scope/asof leakage).

## Files Changed
- `apps/backend/app/engine/research.py` — episode-collapse helpers; `view` threaded through `compute_event_study`; disclosure values; view constants.
- `apps/backend/app/engine/samples.py` — `view` cohort param on `_event_study_samples` + `compute_samples`; reuse the shared observation builder.
- `apps/backend/app/api/research.py` — `view` query param + 422 validation on event-study + samples endpoints.
- `config.yaml` — two `methodology.terms` glossary entries (Episode, Pooled).
- `apps/backend/tests/test_research.py` — J-63 engine battery (byte-identity guard, collapse determinism, gap-split + verbatim carry, disclosure values, default=episodes, unknown-view, read-only under episode path, shared-builder identity).
- `apps/backend/tests/test_samples.py` — J-63 samples count-coherence (both views), first-trigger drill-down rows, pooled byte-identical membership, default=episodes, unknown-view.
- `apps/backend/tests/test_api_research.py` — J-63 API tests (default=episodes + disclosure, pooled byte-identity, 422 on both endpoints, count-coherence both modes, default-view drill-down).
- `apps/frontend/app/research/page.tsx`, `apps/frontend/lib/api.ts`, `apps/frontend/lib/samples-link.ts`, `apps/frontend/app/research/samples/page.tsx` — frontend toggle + disclosure + cohort serialization.

## Tests Run (targeted, foreground, GREEN)
Backend (`cd apps/backend && .venv/bin/python -m pytest <module> -q`):
- `tests/test_research.py` — **77 passed** (incl. 12 new J-63 tests; byte-identity guard green).
- `tests/test_samples.py` — **15 passed** (incl. 5 new J-63 count-coherence tests).
- `tests/test_api_research.py -k "view or default_view or disclosure or coherence"` — **11 passed** (byte-identity + count-coherence both modes + 422 both endpoints, against the warm loaded_engine).
- `tests/test_config.py tests/test_glossary.py tests/test_methodology.py tests/test_no_magic_numbers.py tests/test_config_engine.py` — **131 passed** (glossary +2 terms, no magic-number trip).
- `tests/test_api_methodology.py` — **6 passed** (served glossary).
- Full `tests/test_api_research.py` — handed to the pump (see below; warm-up ~5 min).

Frontend: `cd apps/frontend && node_modules/.bin/tsc --noEmit` — **exit 0** (the frontend gate; ESLint not installed per lessons iter-1).

Live smoke (against `apps/backend/data/trendora.db`, in-process): every subject shows episodes_n < pooled_n (e.g. Risk-off-watchlist 707 episodes vs 2242 pooled); count-coherence holds in both modes (707/707, 2242/2242); pooled `by_horizon` + `best_exit_horizon` byte-identical to the unchanged reconstruction.

## HAND TO THE PUMP — full suite
The full backend pytest (~46–59 min) was NOT run to completion in the dev turn (exceeds the turn budget). Run, gating on the flushed terminal summary line, NOT the in-flight run:

```
cd apps/backend && .venv/bin/python -m pytest tests/ -q
```

Modules I verified green in the foreground (do not need re-debugging unless the full run flags them): `test_research`, `test_samples`, `test_api_research` (targeted + full in-flight at handoff), `test_config`, `test_glossary`, `test_methodology`, `test_no_magic_numbers`, `test_config_engine`, `test_api_methodology`. Run ONE instance only (never two concurrent — lessons: walk-forward boot is heavy).

## Known Issues
- None functional. The episode collapse adds NO stored column/table/migration (in-memory grouping of stored rows), so the live `trendora.db` needs no migration.
- The `view` parameter is fully orthogonal to `?asof`, the global as-of provider, and the J-32 analysis-mode `mode` state (independent local React state; separate backend cohort param). J-18 one-date-control is held — no second date state introduced.
- Servers: no long-running server processes were started (all verification was in-process / TestClient). Nothing to clean up by port.
