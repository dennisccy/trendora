# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54 Execution Plan

Target journey: **J-111** — Research → Market Phase & Severity Lab at `/research/phase-severity-lab`.
J-111 is the **structural twin of iter-53's Regime Lab (J-110)**: a read-only re-surfacing of already-stored
canonical values, grouped + cached byte-identically. It **recomputes nothing**. Mirror the J-110 code paths
closely; the ONLY material difference is the grouping subject.

## What to Build
- A descriptive, survivorship-biased cross-sectional study of how realized forward returns and paired
  max-drawdowns differ (a) across the **five canonical market-phase labels** (Expansion / Recovery / Pullback /
  Correction / Bear) and (b) across **deciles D1…D10 of the 0–100 severity score**, at every configured horizon.
- The grouping subject is read **VERBATIM from the served `market_phase` causal timeline**
  (`market_phase._timeline_series` / `timeline_full` — the SAME series the Dashboard panel + J-97/J-102/J-103
  consume), joined to each observation **by snapshot date**. This is the one structural difference from J-110,
  which read regime from `ScannerRun`. Do NOT add a second phase/severity computation.
- Per bucket per horizon: mean realized forward return, paired mean max-drawdown (J-86, read verbatim), n,
  low-sample flag; decile view also carries the **score range** and the per-horizon **rank-IC** (severity score
  vs forward return).
- New read-only endpoint, a new cached study `kind` (reusing the existing `event_study_cache` table), a new
  samples cohort `kind`, and a new frontend page + Research-hub tile.

## Agents Required
- developer: yes -- implements both backend (engine/API/samples/tests) and frontend (page/tile/api client),
  TDD, closely mirroring the iter-53 Regime Lab. (This project has a single `developer` agent covering both
  backend-data and frontend-ux work.)

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/engine/research.py` -- add `compute_phase_severity_lab(session, *, view, as_of, config)`
  + `phase_severity_lab_cached` + bounded observation builder (`_phase_severity_lab_members_by_horizon` /
  single-horizon `_phase_severity_lab_observation_set`) + a phase/severity-by-snapshot-date reader off the
  `market_phase` timeline. Reuse `_deciles`/`_decile_member_slice`/`_rank_ic`/`_mean_or_none`/
  `_collapse_to_episodes`/`_dataset_version`/`_cache_asof_key`. Add `_PHASE_SEVERITY_LAB_SUBJECT` sentinel +
  a folded `_PHASE_SEVERITY_LAB_SCHEMA_TOKEN`, AND fold the market-phase stamp
  `f"{_dataset_version(session)}|{market_phase.SCHEMA_VERSION}"` (currently `s2`) into the cache key so a
  phase/severity refresh invalidates the lab.
- `apps/backend/app/api/research.py` -- new `GET /api/research/phase-severity-lab` route (params `view`
  Episodes/Pooled, `as_of` FILTER-only; NO `horizon` selector — all-horizons paired shape), mirroring
  `/research/regime-lab`; import the new cohort kind; widen the samples view-validation set + `slice` doc.
- `apps/backend/app/engine/samples.py` -- new `KIND_PHASE_SEVERITY_LAB` + `_phase_severity_lab_samples`
  reproducing the exact `(phase label | severity-score decile, horizon, view)` cohort from the SAME shared
  observation builder; wire into `compute_samples` + `ALL_KINDS`; widen vocabulary so every displayable bucket
  resolves (no 4xx).
- `apps/backend/tests/test_phase_severity_lab.py` (new) -- byte-identity, read-verbatim provenance,
  NA-honesty, cache schema-token + market-phase-stamp invalidation, bounded-read source guard,
  samples count-coherence, invalid-selector 4xx. Mirror `test_regime_lab.py`.
- `apps/backend/tests/test_api_research.py` -- new endpoint shape + view validity + as-of scoping + HTTP
  samples count-coherence + invalid-selector 4xx.
- `apps/backend/tests/test_samples.py` -- `phase-severity-lab` label + decile cohort count-coherence.
- `apps/frontend/app/research/_labs.tsx` -- new `PhaseSeverityLabPage` + by-phase-label / decile tables +
  sort/return/MDD cells (mirror the `RegimeLab*` components).
- `apps/frontend/app/research/phase-severity-lab/page.tsx` (new) -- lazy sub-route page.
- `apps/frontend/app/research/page.tsx` -- new **Market Phase & Severity Lab** tile in the hub `LABS` list.
- `apps/frontend/lib/api.ts` -- `fetchPhaseSeverityLab` + response/row types (send `as_of=` via the existing
  `withAsOf` helper — correct param spelling, NOT `asof=`).
- `apps/frontend/lib/samples-link.ts` -- `PhaseSeverityLabCohortParams` + its `buildSamplesHref` serialization.

## UI Evolution
- New user-facing capability: open a Market Phase & Severity Lab from the Research hub and see how forward
  returns + downside risk (max-drawdown) differ across the five market-phase labels and across severity-score
  deciles, at 1/5/10/20/60-day horizons; drill any bucket into the exact underlying observations.
- New information displayed: per-bucket mean realized forward return + paired mean max-drawdown per horizon;
  per-bucket n; per-decile severity-score range; per-horizon rank-IC (severity vs forward return);
  survivorship-bias / descriptive-evidence labels.
- New user actions: click the hub tile; sort any column (NA-last, both directions); toggle As-of vs
  All-history (FILTER only); click an `N=` chip to open the cohort in Research Samples (new tab).
- UI surface changes: one new page `/research/phase-severity-lab` (by-phase-label table = 5 rows; severity
  decile table = D1…D10 + rank-IC row/column) and one new tile on the `/research` hub. No other page changes.
- Navigation changes: one new hub tile under the existing **Research** section; ≤2 clicks from nav,
  deep-linkable. No top-level nav-skeleton change.

## Visual Requirements
- Component patterns: reuse the iter-53 Regime Lab patterns — Card-wrapped wide tables with
  `overflow-x-auto`; colour-graded return cells (return tokens) + `lib/mdd-color` for max-drawdown; sort
  headers resolvable by `aria-label`; `N=` chips as the Samples drill links.
- Layout: standard `/research/*` sub-route page — heading + survivorship caveat in the SSR shell, two tables
  rendered client-side after the fetch.
- Key visual effects: match existing lab pages (the project dark research theme); no new effects introduced.
- States to handle: loading (pre-fetch shell), empty/NA for thin or zero-n buckets and at/near-latest horizons
  (show NA + n, never a fabricated number), 503-no-data and backend-unavailable honest states.

## Anti-goal / discipline guardrails (heed `lessons.md`)
- **Single source / no recompute:** read forward return + J-86 max-drawdown from `forward_returns`, and the
  phase label + 0–100 severity LEVEL from the served `market_phase` timeline — never recompute, never add a
  second phase/severity derivation, never a second endpoint for those values.
- **No magic numbers:** source min-sample/NA threshold from `config.walk_forward.min_sample`, decile count +
  horizons from config, and the five phase labels from `config.market_phase.labels`. No float/int/label
  literal in `research.py` (use the J-21 boolean-sentinel idiom for sort keys). Keep `test_no_magic_numbers`
  green.
- **No new table:** reuse `event_study_cache`; add NO `table=True` model so `test_db.py`'s expected-tables
  guard stays UNCHANGED.
- **Cache schema discipline (iter-38/39/44):** fold BOTH a new schema token AND the market-phase dataset/
  `SCHEMA_VERSION` stamp into the key; unit-test the MISS against a real ALREADY-POPULATED old-schema row,
  and a real HIT returning byte-identical figures.
- **Bounded read (iter-46/47/48 OOM):** stream/column-project the observation pool; NO unbounded
  `select(...).all()` over `ForwardReturn`/`ScannerResult`; order ScannerResult reads `(run_id, id)` (rides
  `ix_scanner_results_run_id`; bare `id` order spilled "disk is full" on this host). Probe the lab COLD.
- **Whole-cross-section Episodes (iter-53):** the API serves + unit-proves both views, but the frontend
  exposes NO Episodes/Pooled toggle and **pins `view=pooled`** on both the lab fetch AND the `N=` chips.
- **Exactly one date selector (J-18):** the As-of toggle is a MODE/FILTER only; no native `input[type=date]`
  on the page; the single global as-of stays the only date control.
- **Live-render evidence (iter-36..52):** keep BOTH servers up through the browser-qa step; PLAN the
  Playwright fallback up front; `md5sum` the evidence dir first and reject skeleton / "Backend unavailable" /
  byte-identical before/after frames; resolve sort + `N=` controls by `aria-label`.
- **Suite gate (iter-50/53):** launch the FULL pytest suite **nohup-async**; never block the evaluator on the
  in-flight suite; never run it concurrently with the heavy-lab browser probes. Ensure the full pipeline
  including the audit handoff completes.

## Out of scope (excluded — do not build)
- J-112 (Regime × Phase × Factor 3-way decile study) — next iteration (55).
- Any change to how phase label / severity score / forward return / max-drawdown are COMPUTED or STORED.
- Any new `table=True` model / stored column / DB migration; the J-85 destructive snapshot rebuild; any live
  data fetch.
- J-22/J-23/J-24 (data-walled) — leave honestly blocked-NA.
- Any top-level nav-skeleton change. This iteration files NO `blueprint.reapproval-requested` marker
  (additive page within the existing Research section; same decision the iter-53 Regime Lab made → COHERENCE-PASS).
- **Not a GOAL_ACHIEVED candidate** — J-112 remains an unbuilt buildable Must-have until iter-55.

## Key Test Scenarios
- **J-111 page (live, real pixels):** hub shows the Market Phase & Severity Lab tile → `/research/phase-severity-lab`
  renders the by-phase-label table (5 rows) + severity-decile table (D1…D10) with paired forward-return +
  max-drawdown columns per horizon + rank-IC + n + score range; survivorship-bias label present; NO native
  date input; NO Episodes/Pooled toggle.
- **J-111 sort:** toggling a column sort yields a BYTE-DISTINCT frame (md5 before ≠ after), NA-last; header
  resolved by `aria-label`.
- **J-111 As-of:** toggling As-of (or arriving at a historical `?asof=`) FILTERS so rendered n values
  DECREASE; param sent as `as_of=`; no second date control.
- **J-111 drill-down:** an `N=` chip opens `/research/samples` (new tab) for the exact
  `(phase label | severity-score decile, horizon)` cohort; Samples "Total observations" == the clicked n
  (count-coherent, pinned `view=pooled`).
- **Provenance unit test:** each observation's tagged phase label + severity equals the `market_phase`
  series value for that snapshot date (assert against `_timeline_series`/`timeline_full`, NOT a re-derivation),
  correct snapshot-date join; a warm-up-head date with no series value yields an honest unclassified/NA bucket.
- **Byte-identity unit test:** each per-(bucket, horizon) mean return / mean MDD / n equals the reference
  aggregation over the same observation set across views and All-history/As-of; single-horizon builder is
  row-for-row byte-identical to the all-horizons builder per horizon.
- **Cache unit test:** old-schema row MISSES (folded schema token); real HIT byte-identical; refresh on
  `_dataset_version` change AND on a market-phase `SCHEMA_VERSION`/dataset-stamp change.
- **Bounded-read guard:** observation builder streams (no unbounded `.all()`; ScannerResult ordered `(run_id, id)`).
- **Guards green:** `test_db.py` expected-tables UNCHANGED; `test_no_magic_numbers` green; FULL suite launched
  nohup-async (flushed `0 failed` is owed by the iter-55 candidacy, not this iter).
- **Required-still-passing (replay + live where rendered):** J-110, J-25, J-26, J-29, J-107, J-109, J-104,
  J-105, J-86, J-87, J-51, J-65, J-77, J-103, J-80, J-06 (CRITICAL single-source), J-18 (CRITICAL one date
  selector), J-07 (CRITICAL Risk-Off → 0 Actionable).
