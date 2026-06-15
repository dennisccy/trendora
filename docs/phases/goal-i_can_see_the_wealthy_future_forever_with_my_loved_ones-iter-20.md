# Goal Iteration 20 — Backend research cluster: event-study perf/cache (J-72), per-stock forward returns (J-75), regime×setup×pattern ranked study (J-77)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 20
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-72, J-75, J-77
- **Required-still-passing journeys:** J-29, J-63, J-25, J-26, J-32 (other /research labs + event study, byte-identity), J-51, J-64, J-65 (samples count-coherence), J-05, J-06 (stock-detail/leaderboard single-source coherence for J-75), J-21 (Backtest reads the same stored forward_returns), J-48 (view-transform sorting contract), J-18 (single date control), J-50 (?asof href stamping into the new-tab samples chips)
- **Anti-goal reminders** (verbatim from `docs/goal.md`):
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. … The relocated **as-of-scoped evidence aggregate** … is likewise derived once per resolved as-of date …, persisted/cached, and read from storage — never recomputed per request and never including a snapshot dated > D. *(extends Single source of truth)*
  - **Research lab is read-only, honest & not predictive.** Every Factor-Lab and event-study figure … MUST be derived once from the stored per-observation forward returns + stored factor values + post-snapshot price path; the API and frontend MUST NOT recompute returns or factors to build them; low-sample cells show NA + n; results carry the survivorship-bias label. The lab is **descriptive evidence, not a fitted/ML predictive model** …
  - **Sample drill-downs are read-only and count-coherent.** Every research samples page MUST list exactly the observations behind the published aggregate — the observation total MUST equal the N shown on `/research` (same membership filter, same observation set) … the drill-down MUST NOT recompute a factor, return, or membership, and an empty cohort renders an honest empty state, never a fabricated row.
  - **Episode mode recomputes nothing.** The event-study episode view MUST be a deterministic collapse (grouping) of the SAME stored per-observation rows the pooled view reads — one membership rule, the same observation builders, no return/excursion/factor recomputed; the pooled figures stay byte-identical; both modes disclose n + unique symbols + episode count; aggregates and samples drill-downs MUST stay count-coherent in both modes. *(J-63)*
  - **Honest forward-test for partial windows.** … MUST show NA/partial for horizons or cohorts lacking enough samples and MUST show sample size — never fabricate or extrapolate a return to fill a gap. *(extends No fabricated data)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. … The Research **all-history / as-of-date** toggle is likewise a MODE, NOT a date control … The `?asof` URL query param (J-43) is the **serialization of that single global state** … *(extends Single source of truth)*
  - **Leaderboard sorting, searching, and table filtering are view transforms.** Column sorting on `/stocks` (and on the `/research/samples` table — J-64) … MUST re-order or narrow only the client-rendered rows of the already-served payload; they MUST NOT change, recompute, or re-rank any stored value … *(extends Single source of truth + No recompute in the read path)*
  - **Risk-adjusted reporting is honest & must not conflate up/down volatility.** Every risk-adjusted figure (return/vol, return/MAE, Sharpe-like, expectancy) MUST be derived once from the stored per-observation forward returns + post-snapshot price path; "risk" MUST use downside volatility / MAE / drawdown — never total volatility …; raw and risk-adjusted MUST be shown side by side; low-sample cells show NA + n. *(extends Research lab is read-only)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **No order/execution path.** Trendora is research-only. *(critical)*
  - **No secrets in source.** *(critical)*

## GOAL

Deliver the three remaining backend Must-haves of the appended J-72..J-78 extension: the Setup & Pattern Lab / event study becomes fast (each lab section fetches independently; the event study is derived once per `(subject, mode, as-of)` over the stored forward returns with a cached aggregate that refreshes after dataset changes, figures byte-identical — J-72); every `/stocks` row and the Stock Detail page show five forward-return columns (1/5/10/20/60-day) read from the stored `forward_returns` table, NA near latest, sortable, matching the leaderboard (J-75); and a new ranked **Regime × Setup × Pattern** Research study groups the SAME enriched event-study observation set, count-coherent with the N= samples drill-downs (J-77).

## BACKGROUND

J-73 and J-78 closed green in iter-19 (CONTINUE); J-72/J-75/J-77 are now the only remaining unbuilt buildable Must-haves — the backend cluster the iter-13/iter-18/iter-19 evaluators repeatedly recommended dispatching at FULL depth so the audit + the full ~790-test pytest suite earn their cost on backend research-module + serving work with hard property gates. All three share the `apps/backend/app/engine/research.py` event-study / observation-builder surface and the stored append-only `forward_returns` table; they are provable offline against the committed seed with byte-identity assertions and count-coherence assertions (none is data-dependent — `docs/goal.md:2093`). iter-19 coherence was COHERENCE-PASS, so no consolidation pass is owed. The blueprint already pre-registers all three journeys' homes and Data-Contract rows (no nav-skeleton change). Config (`config.yaml`) confirms `walk_forward.horizons: [1,5,10,20,60]` (the five J-75 columns) and `walk_forward.min_sample: 30` (the J-77 threshold to REUSE — no new magic number).

Lessons applied (from `runs/.../state/lessons.md`):
- **iter-11 / iter-12 config + column traps** — J-77 introduces config-backed vocabulary (regime/setup/pattern lists for the study) and may add a new validated config sub-section. ANY new validated `config.yaml` section MUST be pruned at EVERY config-narrowing site (grep, do not trust a fixed list): `apps/backend/scripts/build_qa_fixture_db.py`, `apps/backend/scripts/apply_universe_to_config.py`, AND every inline test config dict under `apps/backend/tests/`. Prefer reusing the EXISTING `config.research` catalog + the EXISTING `walk_forward.min_sample` threshold and deriving the regime/setup/pattern vocabularies from existing config so NO new validated section is needed at all. If J-72 persists a cached derived aggregate in a NEW column on an EXISTING table (e.g. a cache row), register it in `apps/backend/app/db.py` `_ADDITIVE_COLUMNS` + the guard test `test_every_model_column_on_existing_table_is_covered_by_additive_registry`, and exercise a real (non-fresh) live-DB read of the affected endpoint. A standalone cache table (create_all-managed) avoids the `_ADDITIVE_COLUMNS` trap entirely — prefer it.
- **iter-7 count-coherence is same-instant** — J-77's published N per row MUST equal the `/research/samples` drill-down total asserted SAME-INSTANT against the live aggregate (Ns drift between backend boots as warm-up matures forward returns). Never assert against a hardcoded N from an earlier capture.
- **iter-8 perf-ratio honesty** — J-72 is a perf property, NOT a displayed speedup number; the binding gate is the byte-identity of figures + a single-batched-read assertion, not a wall-clock ratio in a capture.
- **iter-11 operational** — the full pytest suite (~790 tests, ~50 min) is the gate. Hand it to the pump as a background (nohup) run; the goal-evaluator MUST NOT block on the in-flight suite — gate it on the flushed terminal summary line.
- **iter-18 evidence hygiene** — md5sum the evidence dir first; for any below-the-fold /research study table, scroll it into the viewport and capture full-viewport; reject blank / byte-duplicate frames.

## IN SCOPE

### Backend

**J-72 — event-study perf + cache (figures byte-identical):**
- [ ] In `apps/backend/app/engine/research.py` `compute_event_study`, replace the per-horizon re-scan of stored `forward_returns` with a SINGLE batched read of the subject's observation pool plus a run-position index computed once for ALL configured horizons (the per-horizon loop must NOT issue one `ForwardReturn` scan per horizon). Output MUST be byte-identical to the current payload in BOTH `episodes` (default) and `pooled` views and for `as_of=None` (all-history) and an `as_of`-scoped window (J-32). The `view="pooled"` path stays the unchanged byte-identical route; the episode collapse stays a pure in-memory grouping of the SAME stored rows (`_collapse_to_episodes`, J-63 untouched).
- [ ] Derive the event-study aggregate ONCE per `(subject, mode/view, as-of)` and serve it from a **persisted/cached derived aggregate** (the same "derived once… persisted/cached, read from storage" contract the as-of evidence aggregate already uses). Prefer a standalone cache table (create_all-managed; key = subject + view + resolved as-of + a dataset-version stamp; value = the serialized derived aggregate) so the iter-12 `_ADDITIVE_COLUMNS` trap does not apply. The cache MUST **refresh after dataset changes** (a backfill that adds snapshots, or a removal) — invalidate/recompute via a dataset-version key derived from stored state (e.g. max run id + forward-return count, or the existing coverage stamp), never a stale read.
- [ ] The `GET /api/research/event-study` payload is unchanged in shape and value; reads serve the cached/derived aggregate, never recompute per request (No recompute in the read path).

**J-75 — per-stock forward returns (1/5/10/20/60-day), served from stored data:**
- [ ] Extend the served `/api/stocks` (list) and `/api/stocks/{ticker}` (detail) row shape in `apps/backend/app/engine/snapshot_serving.py` (`stocks_payload` / `stored_stock_rows` / `stock_detail_payload`) so each stock row carries its FIVE realized forward returns (1/5/10/20/60 trading days) for the resolved as-of run, read VERBATIM from the stored append-only `forward_returns` table (keyed by `run_id` + `symbol` + `horizon`) — the SAME data Backtest/J-21 reads, NEVER recomputed in the API or the view, using only bars dated > D (no-lookahead is intrinsic to the stored rows).
- [ ] A horizon with no stored forward-return row for that (run, symbol, horizon) renders **NA** (so at/near the latest date all five are honestly NA — never a fabricated number). The leaderboard and detail values are IDENTICAL for the same ticker/date/horizon (J-06-style coherence — same stored row, single source of truth).
- [ ] The five horizons MUST come from `config.walk_forward.horizons` (no hardcoded `[1,5,10,20,60]` literal in serving code — No magic numbers); config currently lists exactly those, so the columns map to them.

**J-77 — Regime × Setup × Pattern ranked combinations study:**
- [ ] Enrich the event-study per-observation pool (`research.py` `_event_study_members` / `_event_study_observation_set`) so each observation ADDITIVELY carries its STORED `regime_label`, `setup_status`, and pattern flags (read VERBATIM from the stored `ScannerRun.regime_label` + `ScannerResult` — no regime/setup/pattern recomputed). This enrichment MUST be additive: existing event-study figures (J-29/J-63) and the existing samples drill-downs stay BYTE-IDENTICAL (assert it).
- [ ] Add a new read-only aggregate `research.py:compute_regime_setup_pattern_study(...)` that groups the SAME enriched observation set by the (regime, setup, pattern) key (using the same observation builders / one membership rule the rest of the event study uses) and reports, per the selected horizon, each combination's `n`, mean, median, %positive (hit-rate), expectancy, and the downside-only risk-adjusted figure(s) (return/vol AND return/MAE — downside only, never total volatility). Honors `view` (Episodes default / Pooled, J-63) and `as_of` (J-32 — FILTER only, no recompute, no second date state). Combinations below `config.walk_forward.min_sample` (= 30) show NA + n or are honestly held below the threshold (reuse the EXISTING `min_sample` — no new magic number).
- [ ] Serve it via a new endpoint `GET /api/research/regime-setup-pattern` (mirroring `GET /api/research/event-study`'s parameter style: `horizon`, `view`, `as_of`). Default ranking by the risk-adjusted figure.
- [ ] Extend the EXISTING `/research/samples` machinery (`app/engine/samples.py` + `GET /api/research/samples`) with a new cohort selector for a (regime, setup, pattern) combination so a row's `N=` chip drills down through the SAME observation builder; the drill-down `total` MUST EQUAL the row's published `n` in BOTH Episodes and Pooled modes (count-coherence keystone — same membership filter, same observation set). The regime/setup/pattern vocabularies come from the EXISTING `config`-backed catalog (no hardcoded lists in code).

### Frontend

**J-72:**
- [ ] On `/research` (`apps/frontend/app/research/page.tsx` + lab section components), each lab section (Factor Lab, Combination Lab, Setup & Pattern Lab) fetches independently with its OWN loading/skeleton state so no single slow query blocks the whole page; the event study reaches interactive without a long blocking full-page spinner (J-15 warm-load discipline). No figure changes (speed/UX only).

**J-75:**
- [ ] `/stocks` leaderboard (`apps/frontend/app/stocks/page.tsx`) renders five forward-return columns (1d/5d/10d/20d/60d), colour-graded by sign, sortable under the J-48 view-transform contract (re-orders only, recomputes/refetches nothing; the default order stays the scanner's stored rank; NA cells render an honest "NA"). Stock Detail (`apps/frontend/app/stocks/[ticker]/page.tsx`) shows the SAME five forward returns for the resolved as-of date. The single global as-of control still drives the date (no page-local date picker — J-18); `?asof` href-stamping (J-50) unchanged.

**J-77:**
- [ ] A new **Regime × Setup × Pattern** study section on `/research` renders a ranked, client-side-sortable table (J-48 contract) — each row a (regime, setup, pattern) combination with n, mean, median, hit-rate, expectancy, and the risk-adjusted figure for the selected horizon; default ranked by risk-adjusted return; honors the horizon selector, Episodes ⇄ Pooled toggle (J-63), and As-of vs All-history toggle (J-32). Each row's `N=` chip opens `/research/samples` for that exact combination cohort in a NEW tab (J-65, with `?asof` href-stamping J-50). Low-sample/empty combinations show NA + n; the survivorship-bias label persists. Reads the SAME J-47 glossary for column headers.

### New user-facing capability
Research loads section-by-section without a single blocking spinner; the leaderboard and stock detail expose realized forward returns at 1/5/10/20/60 days; a new ranked Regime × Setup × Pattern evidence table lets the user see which market-regime / setup / pattern combinations have historically led to the strongest (risk-adjusted) forward returns and drill into the exact observations behind each.

### New information displayed
Five per-stock forward-return columns (1/5/10/20/60d) on `/stocks` + Stock Detail; a ranked Regime × Setup × Pattern combinations table on `/research` (n, mean, median, hit-rate, expectancy, risk-adjusted, per horizon).

### New user actions
Sort the forward-return columns (`/stocks`) and the combinations table (`/research`); flip Episodes/Pooled and As-of/All-history on the new study; click a combination row's `N=` chip to open its samples drill-down in a new tab.

### UI surface changes
`/research` gains a new study section (and per-section independent loading states); `/stocks` and `/stocks/[ticker]` gain forward-return columns. No new page or top-level nav section.

### Product surface delta
The research workstation gets materially faster (no full-page block) and gains its highest-value evidence view (regime × setup × pattern returns), while the leaderboard/detail finally surface the realized forward returns that were previously only visible in Backtest.

### Blueprint conformance
All three land on EXISTING Information-Architecture homes — J-72 + J-77 under **Research** (`/research`), J-75 under **Stocks** (`/stocks`) + **Stock Detail** (`/stocks/[ticker]`). No new page, no new top-level nav section. The `/research/samples` drill-down (link-reached under Research) is reused, not duplicated. All three are already pre-registered in `blueprint.md`'s IA + Data Contract (the iter-20 [TARGET] rows), so no `blueprint.md` edit and no nav-skeleton change → no `blueprint.reapproval-requested`.

### Data-contract additions
Already registered additively in `blueprint.md` (NOT a second computation/endpoint for any existing value):
- **Per-stock forward returns (per symbol × horizon: 1/5/10/20/60d)** — already a named canonical value in goal.md "Canonical values" (J-75); computed once by `forward_testing` (the stored append-only `forward_returns` table — the SAME source Backtest/J-21 reads), now ADDITIONALLY served (read VERBATIM, never recomputed) on `GET /api/stocks` + `GET /api/stocks/{ticker}` rows. NO new computation, NO new endpoint — a new read surface of existing stored data.
- **Regime × Setup × Pattern combination study (per-combination per-horizon forward-return stats)** — a grouping of the SAME enriched event-study observation set; computed by `research:compute_regime_setup_pattern_study` over `_event_study_members` enriched with stored regime/setup/pattern; served by the NEW read-only `GET /api/research/regime-setup-pattern`; sampled by the EXISTING `GET /api/research/samples` (new cohort selector). Existing event-study figures (J-29/J-63) byte-identical; count-coherent with the published N.
- **Event-study cached derived aggregate (J-72)** — a performance property of the EXISTING `research:compute_event_study` / `GET /api/research/event-study` value (figures byte-identical); register the cache store (prefer a standalone create_all-managed cache table; if a new column on an existing table is used instead, also register it in `db.py` `_ADDITIVE_COLUMNS` + guard test). NOT a new displayed value.

## OUT OF SCOPE

- Any change to the canonical scores, buckets, setup statuses, pattern flags, or regime labels — J-75/J-77 read them VERBATIM; J-72 is byte-identical.
- Any new computation of forward returns or excursions — all read from the stored `forward_returns` table.
- A new top-level nav section or a second `/research/samples`-style page.
- A predictive/fitted/ML model over the combinations — the study is descriptive evidence only.
- The data-walled J-22/J-23/J-24 (non-halting, no code change this iteration).
- J-44's persistent toggle-off-persistence sub-step debt (non-gating, carried).

## DEFINITION OF DONE

- [ ] Target journeys J-72, J-75, J-77 pass via browser-qa-agent (live `/research` + `/stocks` + Stock Detail evidence; the new study table scrolled into view and captured full-viewport)
- [ ] Required-still-passing journeys remain green: J-29, J-63, J-25, J-26, J-32, J-51, J-64, J-65, J-05, J-06, J-21, J-48, J-18, J-50
- [ ] **J-72:** the event-study output is byte-identical to before (committed assertion in BOTH views, all-history + as-of-scoped) AND the per-horizon computation issues a SINGLE batched read rather than one scan per horizon (committed assertion); the cache refreshes after a dataset change (no stale figures)
- [ ] **J-75:** leaderboard and detail forward returns are identical for the same ticker/date/horizon; near-latest horizons are NA (never fabricated); columns are view-transform sortable (no refetch/recompute); only bars dated > D ever contributed (no-lookahead, inherited from stored rows)
- [ ] **J-77:** every figure derives from the SAME enriched observation set; existing J-29/J-63 figures byte-identical; the `N=` drill-down total equals the published n SAME-INSTANT in both Episodes and Pooled; vocabularies are config-backed; low-sample cells NA + n; survivorship-bias label present
- [ ] No anti-goal violation introduced (no recompute in read path; single source of truth; no lookahead; no magic numbers; exactly one date selector; no order path; no secrets); coherence-auditor returns COHERENCE-PASS
- [ ] Any new validated `config.yaml` section is pruned at EVERY config-narrowing site (`build_qa_fixture_db.py`, `apply_universe_to_config.py`, every inline test dict — grep-verified); any new column on an existing table is registered in `db.py` `_ADDITIVE_COLUMNS` + guard test and exercised against the live DB
- [ ] Unit/integration tests pass; the full backend pytest suite (~790 tests) is GREEN (handed to the pump as a background run — the evaluator gates on the flushed summary line, never blocks on the in-flight suite); `tsc --noEmit` clean (frontend gate; ESLint is not installed — per iter-1 lesson)
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20-dev.md`

## TESTING REQUIREMENTS

- **Browser:** J-72 (each `/research` lab section shows its own loading state, event study interactive without a full-page block, figures unchanged), J-75 (`/stocks` five forward-return columns at a historical as-of with post-D bars; sort a column re-orders; Stock Detail shows the same five; latest → all NA; further-back populates more horizons), J-77 (new ranked combinations table renders; sort re-orders; flip Episodes/Pooled + As-of/All-history re-points figures; `N=` chip opens `/research/samples` in a new tab with total == row n). Plus the required-still-passing smoke: J-29/J-25/J-26/J-32 (research labs unchanged), J-05/J-06 (detail/leaderboard score coherence), J-51/J-64/J-65 (samples count-coherence), J-18 (single date control). md5sum the evidence dir first; capture below-the-fold tables full-viewport.
- **Unit/integration:** J-72 byte-identity (both views × all-history/as-of) + single-batched-read assertion + cache-refresh-after-dataset-change; J-75 leaderboard==detail==stored `forward_returns` per (ticker, horizon), NA where no stored row, no-lookahead (only run-keyed stored rows), config-driven horizons; J-77 byte-identity of existing event-study figures after enrichment, group-by correctness over the enriched set, count-coherence (study row n == `/research/samples` total == len(rows)) SAME-INSTANT in both modes, config-backed vocabulary, min-sample NA honesty. Run the FULL backend suite (~790 tests) to completion via the pump (background/nohup) as the final gate.
- **Error cases:** unknown subject/horizon/view on the new study endpoint → explicit 4xx (never silent empty 200, mirroring `compute_event_study`); unknown combination cohort selector on `/research/samples` → 4xx; an n=0 combination → honest empty drill-down (total 0, no fabricated row); a horizon lacking post-D bars → NA, never a fabricated forward return.

## NOTES

- Depth is **full** per the standing iter-13/iter-18/iter-19 recommendation: this crosses backend (research engine + serving + a cache store + possibly config) and frontend, touches the count-coherence keystone, and needs the audit step + the full pytest gate. (Not an ESCALATE — prior verdict was CONTINUE.)
- Operational (recurring lessons): hand the ~790-test suite to the pump as a `nohup` background run; the goal-evaluator MUST NOT block on the in-flight suite (the failure that aborted iter-11's first run) — gate it on the flushed terminal summary line. Budget the full dev turn and the long suite against the long-dispatch/heartbeat timeouts noted in session memory (`CHAIN_DISPATCH_INFLIGHT_TIMEOUT` / `CHAIN_PUMP_HEARTBEAT_TIMEOUT`).
- After J-72/J-75/J-77 close green with no regression, coherence COHERENCE-PASS, AND the full suite green, the next evaluation is a GOAL_ACHIEVED candidate — these are the last buildable Must-haves. J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per `docs/goal.md:2111-2126`).
- Evidence-hygiene carry-forward: QA should also capture the `/backtest` browser console next session to confirm the iter-19 dev-overlay "1 error" badge is a pre-existing warning (non-verdict-changing; `/backtest` is not in iter-20 scope).
- Prefer NO new validated config section for J-77 — derive regime/setup/pattern vocabularies from the EXISTING `config.research` catalog + reuse `walk_forward.min_sample` (= 30). If a new validated section is unavoidable, prune it at every config-narrowing site (grep `build_qa_fixture_db.py`, `apply_universe_to_config.py`, `tests/`).
