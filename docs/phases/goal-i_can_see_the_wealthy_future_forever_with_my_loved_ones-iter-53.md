# Goal Iteration 53 — Research: Regime Lab (cross-sectional forward returns + max-drawdown by regime label & regime-score decile)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 53
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-110
- **Required-still-passing journeys:** J-109, J-25, J-26, J-29, J-107, J-104, J-105, J-86, J-51, J-65, J-77, J-103, J-80, J-06, J-18, J-07
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. … The relocated **as-of-scoped evidence aggregate** … is likewise derived once per resolved as-of date over the snapshots dated ≤ D, persisted/cached, and read from storage — never recomputed per request and never including a snapshot dated > D. *(extends Single source of truth)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. … *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Honest forward-test for partial windows.** The per-date forward-test scorecard and the VCP-vs-non-VCP breakdown MUST show NA/partial for horizons or cohorts lacking enough samples and MUST show sample size — never fabricate or extrapolate a return to fill a gap. *(extends No fabricated data)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Honest limitations surfaced.** … walk-forward evidence MUST be labelled as carrying survivorship bias (current-membership universe) so results are never overstated.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **Exactly one date selector.** (coherence invariant 5) the global as-of control drives every date-scoped page; `?asof` (J-43) is its serialization, never a second state; the Research As-of toggle is a MODE, not a second date control. *(critical)*
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical — must stay green; J-07)*

## GOAL

Ship a new **Research — Regime Lab** at `/research/regime-lab` that shows, as descriptive survivorship-biased evidence, how stocks' realized forward returns and paired max-drawdowns relate to the market regime — grouped (a) by the six canonical regime labels and (b) into deciles of the 0–100 regime score — at every configured horizon, with rank-IC and count-coherent `N=` drill-downs.

## BACKGROUND

iter-52 landed J-109 (Factor Lab all-horizon paired columns) → CONTINUE; the evaluator's standing gate is "every buildable Must-have positive-evidenced," and three new buildable, NON-data-dependent Must-haves (J-110/J-111/J-112, goal.md commit ab7de8c, goal.md:2451-2488) remain unbuilt with no positive evidence. Per the iter-52 next-step recommendation and the blueprint's J-109..J-112 extension plan, this iteration builds **J-110 only** (one heavy cross-sectional lab per iter; iter-54=J-111, iter-55=J-112). Depth is **full**: J-110 adds a NEW read-only endpoint + a NEW cached study `kind` + a NEW samples cohort `kind` + a NEW frontend page/tile, and it lives on the iter-46/47/48 OOM-sensitive cached-aggregate/streamed research read path — exactly the area where two real regressions surfaced this session (iter-35 perf, iter-46 OOM), so the full pytest gate and live render evidence both matter. J-110 is a read-only re-surfacing of already-stored canonical values (stored `forward_returns.realized_return` + the J-86 `max_drawdown`, and the stored `ScannerRun` regime score/label, J-80) grouped + cached byte-identically — it recomputes nothing.

**Lessons that apply to this iteration (from `lessons.md` — heed them):**
- **iter-12/20 (new-table & magic-number guards fire only in the full suite):** REUSE the existing `event_study_cache` table for the new study `kind` — add **NO** new `table=True` model, so `test_db.py`'s expected-tables guard stays UNCHANGED. Write **no** float/int literal into the `apps/backend/app/engine/` CALC_FILES (`research.py`) — source min-sample/horizons/decile counts from config (`test_no_magic_numbers` blanket-forbids inline literals, even a `0.0` sentinel; use the J-21 boolean-sentinel idiom if a sort-key needs one).
- **iter-38/39/44 (cached-payload schema drift):** the new study `kind`'s cached payload is a NEW shape — fold a **schema token** into the `EventStudyCache` key (not just `_dataset_version`) and UNIT-TEST it against an ALREADY-POPULATED old-schema cache row (a real HIT), never a fresh compute that masks the bug.
- **iter-46/47/48 (bounded/streamed read path):** the Regime Lab observation pool MUST be read over the J-105 streamed/column-projected path — **NO** unbounded `select(...).all()` over `ForwardReturn` or `ScannerResult`; order ScannerResult reads by **`(run_id, id)`** (rides `ix_scanner_results_run_id`, no temp-B-tree spill — a bare `id` order returned `disk is full` on this host) not bare `id`; probe the lab **cold** (a cache HIT can mask a cold-miss OOM on the uncached first request).
- **iter-23/32 (additive-key blanket guards):** this is a NEW endpoint so existing `served == engine_output` / `set(payload) ==` guards should not apply — but if any `test_api_*` shape/byte-equality guard does touch the touched modules, update it in THIS iter (don't defer to a consolidation iter).
- **iter-45 (heavy-research browser-QA):** run heavy-lab probes on a **freshly-restarted, warmed, single-fetch-at-a-time** backend; verify the EXACT `as_of=` query-param spelling (not `asof=`) before trusting any "ignores param" curl FAIL.
- **iter-36/39/40/42/43/49/52 (live render evidence):** keep BOTH servers up THROUGH the dedicated browser-qa-agent step (iter-52 that step SKIPPED on a torn-down frontend); **PLAN the Playwright fallback UP FRONT** (Chrome MCP CDP has emptied the evidence dir on iters 38/39/40/42); `md5sum` the evidence dir FIRST and reject skeleton / "Backend unavailable" / byte-identical "before"/"after" frames; resolve sort / `N=` chip controls by **`aria-label`**, not visible `text()`.
- **iter-50 (suite gate):** launch the full pytest suite **nohup-async** this iter; the eventual GOAL_ACHIEVED candidacy gates on the FLUSHED `0 failed, EXIT 0` line — never block the evaluator on the in-flight suite.

## IN SCOPE

### Backend
- [ ] Add `research:compute_regime_lab(session, *, view, as_of, config)` to `apps/backend/app/engine/research.py` — pools the SAME cross-sectional per-observation forward returns the Factor Lab / event study already build (stock × snapshot), each observation tagged with its run's stored `regime_score` + `regime_label` read VERBATIM from the immutable `ScannerRun` (J-80 — no regime recomputed) joined to the stored append-only `forward_returns` (`realized_return` + the J-86 `max_drawdown`, read verbatim).
- [ ] Group two ways, mirroring Factor Lab: (a) by the **six canonical regime labels**; (b) into **deciles D1…D10 of the 0–100 regime score** via the EXISTING generic `_deciles` / `_decile_member_slice` machinery. For each bucket compute, per `config.walk_forward.horizons` horizon: mean realized forward return, paired mean max-drawdown, n; for the decile view also the score range and the **rank-IC** of the regime score vs the forward return.
- [ ] Read the observation pool over the **J-105 streamed/column-projected bounded path** — no unbounded `select(...).all()` over `ForwardReturn`/`ScannerResult`; ScannerResult reads ordered `(run_id, id)`.
- [ ] Derive once and serve from a cache: add a NEW study `kind` to the EXISTING `EventStudyCache` + `_dataset_version` idiom, with a **folded schema token** in the key (iter-38/39/44 discipline). REUSE the `event_study_cache` table — add NO new `table=True` model.
- [ ] Add a NEW read-only endpoint `GET /api/research/regime-lab` in `apps/backend/app/api/research.py` with `view` (Episodes/Pooled, J-63) + `as_of` (J-32 FILTER-only) params mirroring `/api/research/event-study`; no `horizon` selector (all-horizons paired shape).
- [ ] Add a NEW `regime-lab` cohort `kind` to `apps/backend/app/engine/samples.py` `compute_samples` (mirroring `_regime_setup_pattern_samples`) reproducing the exact `(regime label | regime-score decile, horizon)` cohort from the SAME shared-membership observation builder; widen the samples validation/vocabulary to accept EVERY bucket the study emits so no displayable `N=` chip returns a 4xx.
- [ ] Source min-sample / NA threshold from `config.walk_forward.min_sample`, decile count + horizons from config — NO magic-number literal in `research.py`.

### Frontend
- [ ] New lazy sub-route page `apps/frontend/app/research/regime-lab/` (mirroring the existing per-lab `/research/*` sub-routes), and a NEW **Regime Lab** tile on the `/research` hub linking to it (deep-linkable, ≤2 clicks from the nav).
- [ ] Render the **by-label summary table** (six regime-label rows) and the **regime-score decile table** (D1…D10): each with the paired (forward-return, max-drawdown) columns per horizon, n, score range (decile view), and the rank-IC row/column — colour-graded.
- [ ] Columns client-side sortable **NA-last in both directions** under the J-48 view-transform contract (re-orders the rendered rows only — recomputes/refetches nothing); use the J-82 NA-last predicate.
- [ ] **As-of vs All-history** toggle (J-32) that only FILTERS the observation set — NO second/page-local date state; the single global as-of stays the only date control (J-18).
- [ ] Every `N=` chip opens `/research/samples` for the exact `(regime label | regime-score decile, horizon)` cohort in a NEW tab (J-65), with `?asof` carried in the `href` (J-50).
- [ ] Persist the survivorship-bias / descriptive-evidence labels and an honest empty/NA state for thin buckets and at/near latest.
- [ ] Add `fetchRegimeLab` (+ types) to `apps/frontend/lib/api.ts` calling `GET /api/research/regime-lab` (send `as_of=` via the existing `withAsOf` helper — correct param spelling).

### New user-facing capability
The user can open a new Regime Lab from the Research hub and see, as descriptive evidence, how forward returns and downside risk (max-drawdown) have differed across market-regime labels and across deciles of the regime score — at 1/5/10/20/60-day horizons — and drill any bucket into the exact underlying observations.

### New information displayed
Cross-sectional mean realized forward return + paired mean max-drawdown per horizon, per regime label and per regime-score decile; per-bucket sample size n; per-decile regime-score range; rank-IC of the regime score vs the forward return per horizon; survivorship-bias / descriptive-evidence labels.

### New user actions
Click the Regime Lab hub tile; sort any column (NA-last); toggle As-of vs All-history; click an `N=` chip to open the cohort in Research Samples (new tab).

### UI surface changes
One new page `/research/regime-lab` and one new tile on the `/research` hub. No change to any other page.

### Product surface delta
Research gains its first regime-keyed cross-sectional study, complementing Factor Lab (factor deciles), Regime × Setup × Pattern (J-77), and Severity-velocity × Regime (J-103) — and is explicitly DISTINCT from both (regime score/label alone vs cross-sectional stock returns; no duplicate home).

### Blueprint conformance
Lands under the EXISTING **Research** top-level nav section (the `/research` hub built at iter-45/J-104) as a new hub-linked, lazy sub-route — an **additive new page within an existing nav section**, not a top-level-section/canonical-home change. The IA tree and Data Contract are already updated additively in `runs/goal-session-…/state/blueprint.md` this iteration (the J-110 `/research/regime-lab` IA line + the Regime-Lab Data-Contract row). Per the blueprint's J-109..J-112 extension note and the additive-edit rule, this is an additive page under an existing section, so **no `blueprint.reapproval-requested` marker is filed** — the top-level nav skeleton is unchanged and there is no duplicate home.

### Data-contract additions
ONE new displayed aggregate: **Regime Lab cross-sectional study** — canonical computing module `research:compute_regime_lab`, serving endpoint `GET /api/research/regime-lab` (registered in `blueprint.md` this iter). It introduces NO new canonical value: it READS the already-registered `forward_returns.realized_return` + J-86 `forward_returns.max_drawdown` and the already-registered stored `ScannerRun` `regime_score`/`regime_label` (J-80) from their single canonical sources — never a second computation or a second endpoint for those values.

## OUT OF SCOPE

- J-111 (Market Phase & Severity Lab) and J-112 (Regime × Phase × Factor) — next iterations (54/55).
- Any change to how the regime score/label, realized forward return, or max-drawdown are COMPUTED or STORED — all are read verbatim from their canonical sources.
- Any new `table=True` model / new stored column / DB migration; the J-85 snapshot rebuild (destructive ~11h — do NOT trigger); any live data fetch.
- J-22/J-23/J-24 (data-walled, non-vetoing — leave honestly blocked-NA).
- Any top-level nav-skeleton change.

## DEFINITION OF DONE

- [ ] Target journey **J-110** passes via browser-qa-agent on genuine live rendered pixels (not skeleton): the Regime Lab hub tile → page with the by-label + decile tables (paired return/MDD columns per horizon + rank-IC), a byte-distinct sort toggle, an As-of FILTER toggle that shrinks n, and an `N=` chip that opens a count-coherent Samples cohort (total == chip n).
- [ ] Required-still-passing journeys remain green (deterministic replay + live where rendered): J-109, J-25, J-26, J-29, J-107, J-104, J-105, J-86, J-51, J-65, J-77, J-103, J-80, J-06 (CRITICAL), J-18 (CRITICAL), J-07 (CRITICAL).
- [ ] No anti-goal violation introduced (Single source / No recompute / No lookahead / No magic numbers / No fabricated data / Honest limitations / No order path / Exactly one date selector).
- [ ] Unit/integration tests pass; the FULL pytest suite is launched **nohup-async** and the GOAL_ACHIEVED candidacy (next iter) gates on its FLUSHED `0 failed, EXIT 0`.
- [ ] `test_db.py` expected-tables guard UNCHANGED (no new table); `test_no_magic_numbers` green.
- [ ] Coherence: COHERENCE-PASS (new value registered, single canonical source/endpoint, distinct home).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53-dev.md`.

## TESTING REQUIREMENTS

- **Browser (live, on a freshly-restarted/warmed backend, one heavy fetch at a time; Playwright fallback planned up front; md5sum the dir first):**
  - **J-110** — Research hub shows the Regime Lab tile → `/research/regime-lab` renders the by-label table (six regime-label rows) + the regime-score decile table (D1…D10) with paired forward-return + max-drawdown columns per horizon + rank-IC + n + score range; survivorship-bias label present; NO native `input[type=date]` on the page (J-18).
  - **J-110 sort** — toggling a column sort produces a BYTE-DISTINCT frame (md5 before ≠ after), NA-last; resolve the header by `aria-label`.
  - **J-110 As-of** — toggling As-of (or arriving at a historical `?asof=`) FILTERS the observation set so rendered n values DECREASE; confirm the param is `as_of=` (sent automatically by the frontend); no second date control appears.
  - **J-110 drill-down** — an `N=` chip opens `/research/samples` in a new tab for the exact `(regime label | regime-score decile, horizon)` cohort; the Samples "Total observations" equals the clicked n (J-51/J-65 count-coherence).
  - Required-still-passing live smoke: J-06 (single-source), J-18 (0 native date inputs), J-07 (Risk-Off → 0 Actionable), and a sibling lab (J-104/J-103/J-77 render real figures, not "Backend unavailable").
- **Unit/integration (pytest, `apps/backend/tests/`):**
  - `compute_regime_lab` byte-identity: each per-(bucket, horizon) mean return / mean max-drawdown / n equals the reference aggregation over the SAME observation set across Episodes/Pooled and All-history/As-of (deep-equality, mirroring the J-105/J-109 byte-identity tests).
  - Bounded read: assert the observation builder streams (no unbounded `select(...).all()` over `ForwardReturn`/`ScannerResult`; ScannerResult ordered `(run_id, id)`).
  - Cache schema: a seeded ALREADY-POPULATED old-schema `event_study_cache` row MISSES (folded schema token) and is repopulated; a real cache HIT returns byte-identical figures; refresh on `_dataset_version` change.
  - Samples count-coherence: the `regime-lab` cohort `kind` drill-down `total` == published bucket n in BOTH Episodes+Pooled and BOTH All-history+As-of; every displayable bucket resolves without a 4xx.
  - `test_db.py` expected-tables guard UNCHANGED; `test_no_magic_numbers` green.
- **Error cases:** thin / zero-n buckets and at/near-latest horizons show **NA + n**, never a fabricated number; an unknown/empty regime label or out-of-range decile request returns an honest empty state (no fabricated row); a malformed cohort param is rejected (4xx), but every bucket the study actually emits resolves without a 4xx.

## NOTES

- **No duplicate home (coherence-critical).** J-110 MUST be DISTINCT from J-77 (regime × setup × pattern) and J-103 (severity-velocity sign vs SPY): it studies the regime score/label ALONE against cross-sectional stock returns, on its own `/research/regime-lab` home, reading the canonical regime/return/MDD values — never recomputing them and never adding a second home for an existing entity (blueprint coherence invariant 12).
- **Blueprint marker decision.** The iter-52 evaluator recommended filing `blueprint.reapproval-requested`. This iteration deliberately does NOT file it: adding one lazy sub-route + tile under the already-existing Research hub is an additive page within an existing nav section (the top-level nav skeleton at blueprint.md is unchanged), which the additive-edit rule and the blueprint's own J-109..J-112 extension note classify as not owing reapproval. The new page IS registered with a nav path + Data-Contract row this iter, so the coherence-auditor's "feature has a nav path / no duplicate home" checks are satisfied. (Default `run-goal.sh` is hands-off and would auto-approve such a marker anyway; the loop is not gated on it.)
- This is NOT a GOAL_ACHIEVED candidate: J-111 and J-112 remain unbuilt buildable Must-haves after this iter; the every-buildable-Must-have gate stays unmet until iter-55 lands J-112 with a flushed-GREEN suite + COHERENCE-PASS + zero regression. J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per goal.md:105-108).
- Do NOT re-trigger the J-85 `kind:rebuild` (destructive; data is correct). NEVER run the full pytest suite concurrently with the heavy-lab browser probes (its RAM pressure exacerbated the iter-47 factor-lab OOM).
