# Goal Iteration 54 — Research: Market Phase & Severity Lab (cross-sectional forward returns + max-drawdown by phase label & severity-score decile)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 54
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-111
- **Required-still-passing journeys:** J-110, J-25, J-26, J-29, J-107, J-109, J-104, J-105, J-86, J-87, J-51, J-65, J-77, J-103, J-80, J-06, J-18, J-07
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. … The relocated **as-of-scoped evidence aggregate** … is likewise derived once per resolved as-of date over the snapshots dated ≤ D, persisted/cached, and read from storage — never recomputed per request and never including a snapshot dated > D. *(extends Single source of truth)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Honest forward-test for partial windows.** The per-date forward-test scorecard and the VCP-vs-non-VCP breakdown MUST show NA/partial for horizons or cohorts lacking enough samples and MUST show sample size — never fabricate or extrapolate a return to fill a gap. *(extends No fabricated data)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Honest limitations surfaced.** … walk-forward evidence MUST be labelled as carrying survivorship bias (current-membership universe) so results are never overstated.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **Exactly one date selector.** (coherence invariant 5) the global as-of control drives every date-scoped page; `?asof` (J-43) is its serialization, never a second state; the Research As-of toggle is a MODE, not a second date control. *(critical)*
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical — must stay green; J-07)*

## GOAL

Ship a new **Research — Market Phase & Severity Lab** at `/research/phase-severity-lab` that shows, as descriptive survivorship-biased evidence, how stocks' realized forward returns and paired max-drawdowns relate to the market context — grouped (a) by the five canonical market-phase labels (Expansion / Recovery / Pullback / Correction / Bear) and (b) into deciles of the 0–100 severity score — at every configured horizon, with rank-IC and count-coherent `N=` drill-downs.

## BACKGROUND

iter-53 landed J-110 (the Research — Regime Lab) → CONTINUE; the evaluator's standing gate is "every buildable Must-have positive-evidenced," and two new buildable, NON-data-dependent Must-haves remain unbuilt with no positive evidence: **J-111** and **J-112** (goal.md commit ab7de8c, goal.md:2461-2488). Per the iter-53 next-step recommendation and the blueprint's J-109..J-112 extension plan, this iteration builds **J-111 only** (one heavy cross-sectional lab per iter; iter-55 = J-112). Depth is **full**: J-111 adds a NEW read-only endpoint + a NEW cached study `kind` + a NEW samples cohort `kind` + a NEW frontend page/tile, and it lives on the iter-46/47/48 OOM-sensitive cached-aggregate/streamed research read path — the area where two real regressions surfaced this session (iter-35 perf, iter-46 OOM), so the full pytest gate and live render evidence both matter.

J-111 is the **structural twin of J-110**: a read-only re-surfacing of already-stored canonical values grouped + cached byte-identically — it recomputes nothing. The ONLY material difference from J-110 is the grouping subject: where J-110 read the regime score/label VERBATIM from the immutable `ScannerRun`, **J-111 reads each observation's snapshot-date phase label + 0–100 severity score VERBATIM from the served `/api/market-phase` causal timeline** (the J-87/J-97/J-102 single derived series, `market_phase._timeline_series`/`timeline_full`), joined by snapshot date. It is DISTINCT from J-103 (severity-velocity sign vs SPY) — this studies the severity **level** (and the phase label) against **cross-sectional stock returns**.

**Lessons that apply to this iteration (from `lessons.md` — heed them):**
- **iter-53 (whole-cross-section labs degenerate under the J-63 Episodes collapse):** for a WHOLE-UNIVERSE cross-sectional study (every stock × snapshot, like the Regime Lab / this Phase & Severity Lab) the first-trigger Episodes collapse degenerates to first-appearances and is meaningless. The API may still serve + unit-prove both views (so the samples builder stays a structural twin), but the frontend MUST expose NO Episodes/Pooled toggle and MUST **pin `view=pooled`** on both the lab fetch AND the `N=` chips so counts stay coherent. The byte-identity keystone is that the single-horizon samples observation builder is byte-identical (row-for-row, same `(run_id, id)` order) to the all-horizons builder per horizon.
- **iter-12/20 (new-table & magic-number guards fire only in the full suite):** REUSE the existing `event_study_cache` table for the new study `kind` — add **NO** new `table=True` model, so `test_db.py`'s expected-tables guard stays UNCHANGED. Write **no** float/int literal into the `apps/backend/app/engine/` CALC_FILES (`research.py`) — source min-sample/horizons/decile counts from config (`test_no_magic_numbers` blanket-forbids inline literals, even a `0.0` sentinel; use the J-21 boolean-sentinel idiom if a sort-key needs one).
- **iter-38/39/44 (cached-payload schema drift):** the new study `kind`'s cached payload is a NEW shape — fold a **schema token** into the `EventStudyCache` key (not just `_dataset_version`) and UNIT-TEST it against an ALREADY-POPULATED old-schema cache row (a real HIT), never a fresh compute that masks the bug. **Additional twist unique to J-111:** the phase/severity values are read from the `market_phase` series, whose cache carries its OWN `SCHEMA_VERSION` (bumped `s1`→`s2` at iter-44). Fold the market-phase dataset stamp into the lab cache key too, so a phase/severity refresh invalidates the lab.
- **iter-46/47/48 (bounded/streamed read path):** the observation pool MUST be read over the J-105 streamed/column-projected path — **NO** unbounded `select(...).all()` over `ForwardReturn` or `ScannerResult`; order ScannerResult reads by **`(run_id, id)`** (rides `ix_scanner_results_run_id`, no temp-B-tree spill — a bare `id` order returned `disk is full` on this host) not bare `id`; probe the lab **cold** (a cache HIT can mask a cold-miss OOM on the uncached first request).
- **iter-23/32 (additive-key blanket guards):** this is a NEW endpoint so existing `served == engine_output` / `set(payload) ==` guards should not apply — but if any `test_api_*` shape/byte-equality guard does touch the touched modules, update it in THIS iter (don't defer to a consolidation iter).
- **iter-45 (heavy-research browser-QA):** run heavy-lab probes on a **freshly-restarted, warmed, single-fetch-at-a-time** backend; verify the EXACT `as_of=` query-param spelling (not `asof=`) before trusting any "ignores param" curl FAIL.
- **iter-36/39/40/42/43/49/52 (live render evidence):** keep BOTH servers up THROUGH the dedicated browser-qa-agent step (iter-52 that step SKIPPED on a torn-down frontend); **PLAN the Playwright fallback UP FRONT** (Chrome MCP CDP has emptied the evidence dir on iters 38/39/40/42); `md5sum` the evidence dir FIRST and reject skeleton / "Backend unavailable" / byte-identical "before"/"after" frames; resolve sort / `N=` chip controls by **`aria-label`**, not visible `text()`.
- **iter-50/53 (suite gate):** launch the full pytest suite **nohup-async** this iter; the eventual GOAL_ACHIEVED candidacy (iter-55, after J-112) gates on its FLUSHED `0 failed, EXIT 0` line — never block the evaluator on the in-flight suite. Re-confirm `test_api_data.py::test_post_job_returns_job_id_and_reaches_final_summary` green on a quiescent run before attributing it (the iter-53 async-backfill timing flake, passes in isolation). Ensure the full pipeline (including the audit handoff) completes — iter-53's audit handoff was not written.

## IN SCOPE

### Backend
- [ ] Add `research:compute_phase_severity_lab(session, *, view, as_of, config)` to `apps/backend/app/engine/research.py` — pools the SAME cross-sectional per-observation forward returns the Factor Lab / Regime Lab / event study already build (stock × snapshot) over the J-105 streamed/column-projected bounded path, each observation tagged with **its snapshot date's served phase label + 0–100 severity score read VERBATIM from the `market_phase` causal timeline** (`market_phase._timeline_series`/`timeline_full` — the SAME single derived series the Dashboard panel + J-97/J-102/J-103 read; no phase/severity recomputed) joined BY SNAPSHOT DATE, and joined to the stored append-only `forward_returns` (`realized_return` + the J-86 `max_drawdown`, read verbatim).
- [ ] Group two ways, mirroring the Regime Lab: (a) by the **five canonical market-phase labels** (Expansion / Recovery / Pullback / Correction / Bear); (b) into **deciles D1…D10 of the 0–100 severity score** via the EXISTING generic `_deciles` / `_decile_member_slice` machinery. For each bucket compute, per `config.walk_forward.horizons` horizon: mean realized forward return, paired mean max-drawdown, n; for the decile view also the score range and the **rank-IC** of the severity score vs the forward return.
- [ ] Read the observation pool over the **J-105 streamed/column-projected bounded path** — no unbounded `select(...).all()` over `ForwardReturn`/`ScannerResult`; ScannerResult reads ordered `(run_id, id)`.
- [ ] Derive once and serve from a cache: add a NEW study `kind` to the EXISTING `EventStudyCache` + `_dataset_version` idiom, with a **folded schema token** in the key (iter-38/39/44 discipline) **AND** folding the `market_phase` dataset/`SCHEMA_VERSION` stamp so a phase/severity refresh invalidates the lab. REUSE the `event_study_cache` table — add NO new `table=True` model.
- [ ] Add a NEW read-only endpoint `GET /api/research/phase-severity-lab` in `apps/backend/app/api/research.py` with `view` (Episodes/Pooled — served + unit-proven for both, though the frontend pins Pooled) + `as_of` (J-32 FILTER-only) params mirroring `/api/research/event-study`; no `horizon` selector (all-horizons paired shape).
- [ ] Add a NEW `phase-severity-lab` cohort `kind` to `apps/backend/app/engine/samples.py` `compute_samples` (mirroring `_regime_setup_pattern_samples` / the J-110 regime-lab kind) reproducing the exact `(phase label | severity-score decile, horizon)` cohort from the SAME shared-membership observation builder; widen the samples validation/vocabulary to accept EVERY bucket the study emits so no displayable `N=` chip returns a 4xx.
- [ ] Source min-sample / NA threshold from `config.walk_forward.min_sample`, decile count + horizons from config; the five phase-label vocabulary from the EXISTING config-backed `config.market_phase` labels — NO magic-number / hardcoded-label literal in `research.py`.

### Frontend
- [ ] New lazy sub-route page `apps/frontend/app/research/phase-severity-lab/` (mirroring the existing per-lab `/research/*` sub-routes, esp. the iter-53 `regime-lab/`), and a NEW **Market Phase & Severity Lab** tile on the `/research` hub linking to it (deep-linkable, ≤2 clicks from the nav).
- [ ] Render the **by-phase-label summary table** (five phase-label rows) and the **severity-score decile table** (D1…D10): each with the paired (forward-return, max-drawdown) columns per horizon, n, score range (decile view), and the rank-IC row/column — colour-graded.
- [ ] **Pin `view=pooled`** on the lab fetch AND every `N=` chip; expose NO Episodes/Pooled toggle (iter-53 lesson — the collapse degenerates for whole-cross-section labs).
- [ ] Columns client-side sortable **NA-last in both directions** under the J-48 view-transform contract (re-orders the rendered rows only — recomputes/refetches nothing); use the J-82 NA-last predicate.
- [ ] **As-of vs All-history** toggle (J-32) that only FILTERS the observation set — NO second/page-local date state; the single global as-of stays the only date control (J-18).
- [ ] Every `N=` chip opens `/research/samples` for the exact `(phase label | severity-score decile, horizon)` cohort in a NEW tab (J-65, pinned `view=pooled`), with `?asof` carried in the `href` (J-50).
- [ ] Persist the survivorship-bias / descriptive-evidence labels and an honest empty/NA state for thin buckets and at/near latest.
- [ ] Add `fetchPhaseSeverityLab` (+ types) to `apps/frontend/lib/api.ts` calling `GET /api/research/phase-severity-lab` (send `as_of=` via the existing `withAsOf` helper — correct param spelling).

### New user-facing capability
The user can open a new Market Phase & Severity Lab from the Research hub and see, as descriptive evidence, how forward returns and downside risk (max-drawdown) have differed across the five market-phase labels and across deciles of the 0–100 severity score — at 1/5/10/20/60-day horizons — and drill any bucket into the exact underlying observations.

### New information displayed
Cross-sectional mean realized forward return + paired mean max-drawdown per horizon, per market-phase label and per severity-score decile; per-bucket sample size n; per-decile severity-score range; rank-IC of the severity score vs the forward return per horizon; survivorship-bias / descriptive-evidence labels.

### New user actions
Click the Market Phase & Severity Lab hub tile; sort any column (NA-last); toggle As-of vs All-history; click an `N=` chip to open the cohort in Research Samples (new tab).

### UI surface changes
One new page `/research/phase-severity-lab` and one new tile on the `/research` hub. No change to any other page.

### Product surface delta
Research gains its phase/severity-keyed cross-sectional study, completing the per-context lab family alongside Factor Lab (factor deciles), Regime Lab (J-110, regime label/score), Regime × Setup × Pattern (J-77), and Severity-velocity × Regime (J-103) — and is explicitly DISTINCT from all of them (the severity LEVEL + phase label vs cross-sectional stock returns; no duplicate home).

### Blueprint conformance
Lands under the EXISTING **Research** top-level nav section (the `/research` hub built at iter-45/J-104) as a new hub-linked, lazy sub-route — an **additive new page within an existing nav section**, not a top-level-section/canonical-home change. The IA tree and Data Contract are already updated additively in `runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/blueprint.md` this iteration (the J-111 `/research/phase-severity-lab` IA line directly after the Regime Lab line + the Phase-&-Severity-Lab Data-Contract row). Per the blueprint's J-109..J-112 extension note and the additive-edit rule, this is an additive page under an existing section, so **no `blueprint.reapproval-requested` marker is filed** — the top-level nav skeleton is unchanged and there is no duplicate home (same decision and reasoning as the iter-53 Regime Lab, which the iter-53 coherence-auditor returned COHERENCE-PASS on).

### Data-contract additions
ONE new displayed aggregate: **Phase & Severity Lab cross-sectional study** — canonical computing module `research:compute_phase_severity_lab`, serving endpoint `GET /api/research/phase-severity-lab` (registered in `blueprint.md` this iter). It introduces NO new canonical value: it READS the already-registered `forward_returns.realized_return` + J-86 `forward_returns.max_drawdown` and the already-registered **served `market_phase` phase label + 0–100 severity score** (J-87/J-97/J-102, from `market_phase._timeline_series`/`timeline_full` served by `GET /api/market-phase`) from their single canonical sources — never a second computation, never a second slope/phase/severity derivation, never a second endpoint for those values.

## OUT OF SCOPE

- J-112 (Regime × Phase × Factor 3-way decile study) — next iteration (55).
- Any change to how the market-phase label, severity score, realized forward return, or max-drawdown are COMPUTED or STORED — all are read verbatim from their canonical sources (`market_phase` engine; `forward_returns` table).
- Any new `table=True` model / new stored column / DB migration; the J-85 snapshot rebuild (destructive ~11h — do NOT trigger); any live data fetch.
- J-22/J-23/J-24 (data-walled, non-vetoing — leave honestly blocked-NA).
- Any top-level nav-skeleton change.

## DEFINITION OF DONE

- [ ] Target journey **J-111** passes via browser-qa-agent on genuine live rendered pixels (not skeleton): the Market Phase & Severity Lab hub tile → page with the by-phase-label (five rows) + severity-decile (D1…D10) tables (paired return/MDD columns per horizon + rank-IC + n + score range), a byte-distinct sort toggle, an As-of FILTER toggle that shrinks n, and an `N=` chip that opens a count-coherent Samples cohort (total == chip n).
- [ ] Required-still-passing journeys remain green (deterministic replay + live where rendered): J-110, J-25, J-26, J-29, J-107, J-109, J-104, J-105, J-86, J-87, J-51, J-65, J-77, J-103, J-80, J-06 (CRITICAL), J-18 (CRITICAL), J-07 (CRITICAL).
- [ ] No anti-goal violation introduced (Single source / No recompute / No lookahead / No magic numbers / No fabricated data / Honest limitations / No order path / Exactly one date selector).
- [ ] Unit/integration tests pass; the FULL pytest suite is launched **nohup-async** and the GOAL_ACHIEVED candidacy (iter-55) gates on its FLUSHED `0 failed, EXIT 0`.
- [ ] `test_db.py` expected-tables guard UNCHANGED (no new table); `test_no_magic_numbers` green.
- [ ] Coherence: COHERENCE-PASS (new value registered, single canonical source/endpoint, distinct home).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54-dev.md`.

## TESTING REQUIREMENTS

- **Browser (live, on a freshly-restarted/warmed backend, one heavy fetch at a time; Playwright fallback planned up front; md5sum the dir first):**
  - **J-111** — Research hub shows the Market Phase & Severity Lab tile → `/research/phase-severity-lab` renders the by-phase-label table (five phase-label rows) + the severity-score decile table (D1…D10) with paired forward-return + max-drawdown columns per horizon + rank-IC + n + score range; survivorship-bias label present; NO native `input[type=date]` on the page (J-18); NO Episodes/Pooled toggle (pinned Pooled).
  - **J-111 sort** — toggling a column sort produces a BYTE-DISTINCT frame (md5 before ≠ after), NA-last; resolve the header by `aria-label`.
  - **J-111 As-of** — toggling As-of (or arriving at a historical `?asof=`) FILTERS the observation set so rendered n values DECREASE; confirm the param is `as_of=` (sent automatically by the frontend); no second date control appears.
  - **J-111 drill-down** — an `N=` chip opens `/research/samples` in a new tab for the exact `(phase label | severity-score decile, horizon)` cohort; the Samples "Total observations" equals the clicked n (J-51/J-65 count-coherence, pinned `view=pooled`).
  - Required-still-passing live smoke: J-06 (single-source), J-18 (0 native date inputs), J-07 (Risk-Off → 0 Actionable), J-110 (the sibling Regime Lab still renders real figures), and a market-phase reader (J-87 Dashboard Market-Phase panel renders the same phase/severity this lab joins on, proving the shared source is intact).
- **Unit/integration (pytest, `apps/backend/tests/`):**
  - `compute_phase_severity_lab` byte-identity: each per-(bucket, horizon) mean return / mean max-drawdown / n equals the reference aggregation over the SAME observation set across Pooled (and Episodes where served) and All-history/As-of (deep-equality, mirroring the J-105/J-109/J-110 byte-identity tests).
  - Phase/severity provenance: each observation's tagged phase label + severity equals the `market_phase` series value for that snapshot date (read verbatim — assert against the engine's `_timeline_series`/`timeline_full`, NOT a re-derivation), with the correct snapshot-date join.
  - Bounded read: assert the observation builder streams (no unbounded `select(...).all()` over `ForwardReturn`/`ScannerResult`; ScannerResult ordered `(run_id, id)`).
  - Cache schema: a seeded ALREADY-POPULATED old-schema `event_study_cache` row MISSES (folded schema token) and is repopulated; a real cache HIT returns byte-identical figures; refresh on `_dataset_version` change AND on a market-phase `SCHEMA_VERSION`/dataset-stamp change.
  - Samples count-coherence: the `phase-severity-lab` cohort `kind` drill-down `total` == published bucket n (pinned `view=pooled`; assert both views where served); every displayable bucket resolves without a 4xx.
  - `test_db.py` expected-tables guard UNCHANGED; `test_no_magic_numbers` green.
- **Error cases:** thin / zero-n buckets and at/near-latest horizons show **NA + n**, never a fabricated number; an unknown/empty phase label or out-of-range decile request returns an honest empty state (no fabricated row); a malformed cohort param is rejected (4xx), but every bucket the study actually emits resolves without a 4xx; a snapshot date with no `market_phase` series value (warm-up head) yields an honest unclassified/NA bucket, never a fabricated phase.

## NOTES

- **No duplicate home (coherence-critical).** J-111 MUST be DISTINCT from J-103 (severity-velocity SIGN/slope vs SPY) and J-110 (regime score/label): it studies the severity **LEVEL** + the market-phase **label** against **cross-sectional stock returns**, on its own `/research/phase-severity-lab` home, reading the canonical phase/severity/return/MDD values — never recomputing them and never adding a second home for an existing entity (blueprint coherence invariant 12). The severity it groups by is the served 0–100 **level** from the `market_phase` timeline, NOT the J-102 velocity/slope.
- **Single-source subtlety unique to J-111.** Unlike J-110 (which read regime from `ScannerRun`), J-111's phase/severity come from the **served `market_phase` causal timeline**. Read them VERBATIM from `market_phase._timeline_series`/`timeline_full` (the same series the Dashboard panel + J-97/J-102/J-103 consume) and join by snapshot date — do NOT add a second phase/severity computation. Because that series is cached behind its own `SCHEMA_VERSION` + dataset stamp, fold that stamp into the lab cache key so a phase/severity refresh invalidates the lab (no stale phase tags).
- **Blueprint marker decision.** This iteration does NOT file `blueprint.reapproval-requested`: adding one lazy sub-route + tile under the already-existing Research hub is an additive page within an existing nav section (the top-level nav skeleton at `blueprint.md` is unchanged), which the additive-edit rule and the blueprint's own J-109..J-112 extension note classify as not owing reapproval — the same decision the iter-53 Regime Lab made (COHERENCE-PASS). The new page IS registered with a nav path + Data-Contract row this iter, so the coherence-auditor's "feature has a nav path / no duplicate home" checks are satisfied. (Default `run-goal.sh` is hands-off and would auto-approve such a marker anyway; the loop is not gated on it.)
- This is NOT a GOAL_ACHIEVED candidate: J-112 remains an unbuilt buildable Must-have after this iter; the every-buildable-Must-have gate stays unmet until iter-55 lands J-112 with a flushed-GREEN suite + COHERENCE-PASS + zero regression. J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per goal.md:105-108).
- Do NOT re-trigger the J-85 `kind:rebuild` (destructive; data is correct). NEVER run the full pytest suite concurrently with the heavy-lab browser probes (its RAM pressure exacerbated the iter-47 factor-lab OOM).
