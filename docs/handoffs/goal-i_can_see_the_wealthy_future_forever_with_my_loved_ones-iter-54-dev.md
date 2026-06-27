# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54
**Date:** 2026-06-27
**Agent:** developer
**Status:** complete

## What Was Built

J-111 — the **Market Phase & Severity Lab** at `/research/phase-severity-lab`, the structural twin of
iter-53's Regime Lab (J-110). A read-only re-surfacing of already-stored canonical values: it recomputes
nothing. The ONLY material difference from J-110 is the grouping subject's SOURCE — instead of reading the
regime off the immutable `ScannerRun`, it reads each observation's snapshot-date **market-phase label + 0–100
severity score VERBATIM from the served `market_phase` causal timeline** (`phase_context_by_date` — the SAME
single series the Dashboard panel + J-97/J-102/J-103 consume), joined by snapshot date.

- **Engine** `research:compute_phase_severity_lab(session, *, view, as_of, config)` — pools the SAME
  cross-sectional per-observation forward returns the Factor/Regime Lab build (stock × snapshot) over the
  J-105 bounded/streamed path, tags each with its snapshot date's served phase + severity, and groups two
  ways at every config horizon: (a) by the five `config.market_phase.labels`; (b) into deciles D1…D10 of the
  severity score (the generic `_deciles`/`_decile_member_slice` machinery). Per bucket per horizon: mean
  forward return, paired mean max-drawdown (J-86, verbatim), n, low_sample; decile view also carries the
  severity-score range + the per-horizon rank-IC (severity vs forward return).
- **Cache** `phase_severity_lab_cached` over the SHARED `event_study_cache` table under a new sentinel
  subject `__phase_severity_lab__`. The cache key folds a NEW schema token (`phaseseverlab-v1`) AND the
  served `market_phase` stamp (`_phase_severity_lab_cache_version` = dataset stamp + lab token +
  `market_phase._cache_version` = `{dataset}|{SCHEMA_VERSION}`), so a phase/severity refresh (a
  `SCHEMA_VERSION` bump OR a market-phase dataset change) invalidates the lab — no stale phase tags. NO new
  `table=True` model.
- **Endpoint** `GET /api/research/phase-severity-lab` (params `view` Episodes/Pooled served + unit-proven,
  `as_of` J-32 FILTER-only; no `horizon` selector — all-horizons paired shape), mirroring `/regime-lab`.
- **Samples cohort** new `KIND_PHASE_SEVERITY_LAB` + `_phase_severity_lab_samples` reproducing the exact
  `(phase label | severity decile, horizon, view)` cohort from the SAME shared observation builder, so every
  `N=` chip's `total` equals its published n; wired into `compute_samples` + `ALL_KINDS`; the label slice
  reuses the existing `phase` samples param.
- **Frontend** new page `/research/phase-severity-lab` (by-phase-label table = 5 rows + severity-decile table
  = D1…D10 + rank-IC row), a new **Market Phase & Severity Lab** hub tile, `fetchPhaseSeverityLab` + types in
  `lib/api.ts`, and the `PhaseSeverityLabCohortParams` serialization in `lib/samples-link.ts`. View pinned
  `pooled` on the lab fetch AND every `N=` chip (iter-53 lesson — Episodes degenerates for whole-cross-section
  labs). The samples page now renders correct cohort headers for the phase-severity-lab kind (and the
  previously-unhandled regime-lab kind).

## Files Changed

- `apps/backend/app/engine/research.py` — added `_phase_severity_meta_by_run`,
  `_phase_severity_lab_members_by_horizon`, `_severity_ordered`, `_phase_severity_lab_observation_set`,
  `compute_phase_severity_lab`, `_phase_severity_lab_cache_version`, `phase_severity_lab_cached`, and the
  `_PHASE_SEVERITY_LAB_SUBJECT`/`_PHASE_SEVERITY_LAB_SCHEMA_TOKEN` sentinels.
- `apps/backend/app/engine/samples.py` — added `KIND_PHASE_SEVERITY_LAB`, `_PHASE_SEVERITY_LAB_SLICES`,
  `_phase_severity_lab_samples`; wired into `compute_samples` + `ALL_KINDS` + imports.
- `apps/backend/app/api/research.py` — new `GET /research/phase-severity-lab` route; imported
  `phase_severity_lab_cached` + `KIND_PHASE_SEVERITY_LAB`; widened the samples view-validation set + `slice`/
  `phase` param docs.
- `apps/backend/tests/test_phase_severity_lab.py` (new, 32 tests) — byte-identity vs the single-horizon
  builder, read-verbatim by-snapshot-date provenance + warm-up-head NA, NA-honesty, cache schema-token +
  market-phase-stamp invalidation, bounded-read source guard, chunk-independence, samples count-coherence,
  invalid-selector raises.
- `apps/backend/tests/test_api_research.py` — 7 new phase-severity-lab endpoint tests (shape, no-date-control,
  pooled byte-identity to engine, as-of scoping, invalid-view 422, samples coherence over HTTP, invalid
  selectors 4xx).
- `apps/backend/tests/test_samples.py` — `phase-severity-lab` label + decile cohort count-coherence (new
  monkeypatched fixture).
- `apps/frontend/app/research/_labs.tsx` — `PhaseSeverityLabPage` + `PhaseSeverityLabByLabelTable` +
  `PhaseSeverityLabDecileTable` (reusing the Regime-Lab cell/sort helpers).
- `apps/frontend/app/research/phase-severity-lab/page.tsx` (new) — lazy sub-route.
- `apps/frontend/app/research/page.tsx` — new hub tile (Thermometer icon).
- `apps/frontend/app/research/samples/page.tsx` — `describeCohort` branches for phase-severity-lab (and
  regime-lab, previously falling through to the event-study default).
- `apps/frontend/lib/api.ts` — `PhaseSeverityLab*` types + `fetchPhaseSeverityLab`; extended `SampleCohort`
  kind union.
- `apps/frontend/lib/samples-link.ts` — `PhaseSeverityLabCohortParams` + its `buildSamplesHref` branch.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`

- `tests/test_phase_severity_lab.py` — **32 passed**.
- `tests/test_phase_severity_lab.py tests/test_samples.py tests/test_regime_lab.py tests/test_no_magic_numbers.py tests/test_db.py` — **88 passed** (guards: `test_no_magic_numbers` green; `test_db` expected-tables UNCHANGED).
- `tests/test_api_research.py -k phase_severity` — **7 passed** (against the real loaded engine).
- FULL suite launched **nohup-async** at
  `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54-fullsuite.log` (per the
  iter-50/53 suite-gate lesson — not blocking the evaluator; the GOAL_ACHIEVED candidacy is iter-55, after
  J-112).

## Live render evidence (both servers up, freshly restarted)

Backend `:8255`, frontend `:3255` via `scripts/dev.sh`; cold-computed (no OOM):

- `GET /api/research/phase-severity-lab?view=pooled` → **HTTP 200, 7.3s cold**. Real figures: all five phase
  labels populated (Expansion n=51351, Pullback 24378, Correction 9962, Bear 11695, Recovery 25578 @20d),
  D1…D10 severity-score ranges (17.3 → 95.34), rank-IC@20 = 0.0203 over 122,964 obs, survivorship +
  descriptive caveats present.
- Samples count-coherence over HTTP: Bear label total = **11695** == published n; D10 decile total = **12297**
  == published n; rows carry `phase` + `severity` + `forward_return`.
- As-of FILTER shrinks: all-history total@20 = 122,964 → `as_of=2024-06-01` = 67,727 (`0 < scoped < all`).
- Episodes < Pooled (245 < 122,964) — both served + unit-proven; the frontend pins pooled.
- Invalid view / unknown phase / out-of-range decile → **422**.
- Frontend `/research/phase-severity-lab` → HTTP 200, title "Market Phase & Severity Lab" present, 3
  survivorship mentions in SSR shell, **0 native `type="date"` inputs** (J-18). Hub `/research` carries the
  `phase-severity-lab` tile.
- Shared source intact: `GET /api/market-phase` → 200 (phase=Expansion, severity=25.7 — the SAME source the
  lab joins on); `GET /api/research/regime-lab?view=pooled` → 200; `GET /api/dashboard` → 200.

Both servers were stopped after verification; ports `:8255` and `:3255` confirmed free (no lingering
uvicorn/next processes).

## Known Issues

- **As-of at the very oldest snapshot returns 0 classified observations** (honest, not a bug): the first
  stored snapshot (2021-01-04) is the `market_phase` warm-up head with no severity reading, so its
  observations tag unclassified and are excluded from the displayed buckets (NA-honest). The browser-QA As-of
  check should use a mid-history `?asof` (e.g. 2024-06-01) where classified observations exist — verified to
  shrink there.
- No live external integration in this iteration (read-only re-surfacing of stored values + the served
  market-phase timeline; no new adapter/scraper/native dependency).
- Not a GOAL_ACHIEVED candidate: J-112 (Regime × Phase × Factor 3-way decile study) remains an unbuilt
  buildable Must-have until iter-55.
