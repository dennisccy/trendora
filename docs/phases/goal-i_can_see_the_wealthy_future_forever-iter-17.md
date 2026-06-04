# Goal Iteration 17 — Forward-test evidence aggregate moves to Backtest, as-of-scoped (expanding window ≤ D); retire System Health

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 17
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-09, J-10
- **Required-still-passing journeys:** J-14, J-18, J-15, J-19, J-16, J-28, J-21, J-13, J-06, J-07
- **Nav-skeleton change this iteration:** YES — `/system-health` is retired and the forward-test **evidence aggregate** relocates to `/backtest` (as-of-scoped). A `blueprint.reapproval-requested` marker is written; `run-goal.sh` pauses for human re-approval before iter-18's decomposer. This executes the operator's goal re-scope (Product Shape now drops System Health and homes the as-of-scoped evidence on Backtest).
- **Anti-goal reminders (verbatim from `docs/goal.md` — must all hold):**
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. The scan is computed once per date (bootstrap, scheduled, or first view) and then read from storage. The relocated **as-of-scoped evidence aggregate** (forward returns by bucket / setup / regime, excess vs benchmarks, control-group, and VCP-vs-non-VCP) is likewise derived once per resolved as-of date over the snapshots dated ≤ D, persisted/cached, and read from storage — never recomputed per request and never including a snapshot dated > D. *(extends Single source of truth)*
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. *(extends Single source of truth)* *(critical)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. *(critical)*
  - **No fabricated data** + **Honest forward-test for partial windows.** Low-sample horizons/cohorts MUST show NA/partial **and** the sample size `n`; never fabricate or extrapolate a return to fill a gap.
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **Honest limitations surfaced.** Breadth/new-high-low are "universe-relative"; walk-forward evidence is labelled survivorship-biased.

## GOAL

A user visiting **`/backtest`** sees the forward-tested **evidence aggregate** (forward return by A–E bucket, excess vs SPY/QQQ, by setup, by regime, VCP-vs-non-VCP / pattern-vs-non-pattern, and the control-group comparison) **scoped to an expanding window of every snapshot dated ≤ the global as-of date** — moving the single global as-of switcher to an earlier date re-points the evidence and shrinks the sample size `n`, and at the latest date it equals the full all-history aggregate — with `/system-health` retired so this evidence has exactly one home.

## BACKGROUND

The session was **STALLED** at iter-16 because J-31 (the last buildable journey of the old scope) had landed and the only remaining failing journeys (J-22/J-23/J-24) were externally Yahoo-429 data-walled. The operator resumed via the iter-16 "resume path 2": commit `d723133` **re-scoped `docs/goal.md`** to (a) make **J-22/J-23/J-24 explicitly non-halting** (recorded as honestly blocked/NA; they MUST NOT drive STALLED or veto GOAL_ACHIEVED), and (b) add three new buildable pieces — **J-09 as-of-scoped Backtest evidence**, **J-26 composite factor cohort**, and **J-32 Research as-of toggle**. This unblocks the autonomous loop.

This iteration takes the **foundational** piece, **J-09** (+ **J-10**, the control-group, which rides the same aggregate). Today `app.engine.forward_testing:compute_forward_aggregates(session, horizon, config)` aggregates **ALL** snapshots with **no date filter** and is served on **`GET /api/system-health`** (a cross-date, no-`as_of` page). The revised goal requires that exact aggregate to be (1) **as-of-scoped** to snapshots whose `ScannerRun.asof_date ≤ D` (an expanding walk-forward window), (2) **homed on `/backtest`** and driven by the **single global as-of switcher** (no second date control — the principal anti-goal risk), and (3) the **only** home for this evidence (the goal's Product Shape drops `/system-health`). Because coherence forbids serving one contract value from two homes, retiring System Health is coupled to this delivery — hence the nav-skeleton change + re-approval marker.

**Why full depth:** touches the critical `forward_testing` read path, changes a serving endpoint's payload shape, removes a top-level nav surface, and puts the critical **Exactly-one-date-selector (J-18)** invariant at risk on `/backtest`.

**Lessons applied (from `lessons.md` / MEMORY — surfaced for dev/reviewer/QA):**
- **iter-2:** the `distribution.mean == overall.mean` consistency invariant binds the **aggregate** (the value moving here), not the per-date scorecard (whose distribution mean legitimately differs — different population). When the aggregate relocates, **move that invariant's unit test to the as-of-scoped aggregate; do not delete it**, and do NOT "fix" the per-date scorecard's legitimate mean mismatch.
- **MEMORY `j18-asof-on-stocks-fetch-is-correct`:** a single global `?as_of=D` appended to a snapshot-served read is the **single global date being transmitted**, NOT a second date state. Judge J-18 on the **page URL being date-free** and there being no page-local date picker — NOT on the `/api/backtest?as_of=` call (that call is correct and required).
- **iter-15 / MEMORY `browser-qa-dead-shell-next-cache`:** do NOT run `npm run build` against the live `next dev` `.next/` — it produces a dead un-hydrated shell (every route "Checking backend…", framework-chunk 404). Before driving any browser test: stop `next dev` by port, `rm -rf apps/frontend/.next`, restart, and confirm `GET /_next/static/chunks/main-app.js → 200` and the health badge clears.
- **iter-6:** if both the `qa` agent and `browser-qa-agent` drive Chrome, serialize access; de-dup evidence by sha256; ground every "before/after as-of" claim on **distinct** screenshots + a DOM/network assertion, never a single pair.
- **iter-1:** the global as-of lives in an in-memory provider (no URL/localStorage persistence) — drive as-of journeys via **in-app nav/clicks, not a hard reload**.
- **MEMORY `config-fixtures-need-new-required-keys`:** only relevant if a new **required** config key is added (this iteration should not need one — the as-of cutoff is a function parameter, not config); if one is added, update ALL 4 inline test config dicts.
- **MEMORY `backend-test-suite-runtime`:** full pytest ≈ 14 min — run it ONCE; never two concurrent pytest invocations.

## IN SCOPE

### Backend
- [ ] **As-of-scope the aggregate.** Add an optional cutoff parameter to `app.engine.forward_testing:compute_forward_aggregates` — e.g. `compute_forward_aggregates(session, horizon, config=None, *, as_of: Optional[date] = None)`. When `as_of` is given, restrict the observation pool to snapshots with `ScannerRun.asof_date <= as_of` (the single-point filter at the `select(ScannerRun)` / `runs_with_fr` step, `forward_testing.py:~555-567`). `as_of=None` keeps today's all-history behaviour (which MUST stay byte-identical → equals the latest-date case). The **only** change to the aggregation is the membership filter; the grouping/excess/control-group/attribution math is untouched.
  - This stays a **read-only grouping** over the persisted `forward_returns` (the canonical value, computed once per run at bootstrap/first-view) — it recomputes **no** return/score/bucket, exactly like the existing System Health aggregate and the J-19 attribution slices. No snapshot dated `> D` may contribute. *(No-recompute / No-lookahead / Single-source criticals.)*
  - Low-sample / empty cells (`n < walk_forward.min_sample`, or a bucket/setup/regime with no observations in the ≤ D window) must show NA + `n` — never a fabricated number.
- [ ] **Surface it on `/api/backtest`.** Extend the `GET /api/backtest` response (`apps/backend/app/api/backtest.py`) with an as-of-scoped evidence aggregate keyed by horizon — e.g. `evidence_by_horizon: { "<h>": <compute_forward_aggregates(session, h, cfg, as_of=run.asof_date)> for h in config.walk_forward.horizons }` — using the **resolved run's `asof_date`** as the cutoff (the run already resolved by `resolved_run(session, as_of, cfg)`). Computing all horizons in the single payload keeps the existing **client-side horizon selector** working with **one fetch** (no per-horizon refetch → J-15/J-18 preserved). Do NOT add a page-local date param to this endpoint — it already takes the global `as_of` (which is the single global date being read).
- [ ] **Retire System Health.** Remove the `GET /api/system-health` route (`apps/backend/app/api/system_health.py`) and unregister its router. Keep `compute_forward_aggregates` (now the Backtest evidence source). Re-home any test that asserted the consistency invariant or the aggregate shape onto the new Backtest path (see Testing).
- [ ] **No scoring/scanner/regime/patterns/snapshot change.** `score_stocks`, `scanner.run_scan`, `regime.score_regime`, `patterns.*`, and the immutable snapshot tables are **untouched** → the six canonical scores/buckets/setups and the Risk-Off gate stay byte-identical (J-06/J-07). No DB regen required.

### Frontend
- [ ] **Backtest page — add the evidence-aggregate sections** (`apps/frontend/app/backtest/page.tsx`): render, from the new `evidence_by_horizon[selectedHorizon]` already in the single `/api/backtest` payload — forward return **by A–E bucket** (the J-09 headline), **excess vs SPY and vs QQQ**, **by setup type**, **by market regime**, **VCP-vs-non-VCP** and the **new-pattern breakdowns** (`by_pullback_to_rising_dma`, `by_flat_base_breakout`), and the **control-group comparison** (top-ranked cohort vs random-same-sector vs SPY/QQQ/sector ETF) — each cell showing its sample size `n` and honest NA below `min_sample`. Carry the **survivorship-bias / universe-relative** label.
  - The section re-points on **(a)** the global as-of change (via the existing fetch effect keyed `[asOf]`) and **(b)** the existing **client-side horizon selector** (no refetch). Label it clearly as the **expanding-window aggregate ("evidence from every snapshot dated ≤ D")**, visually distinct from the existing **per-date scorecard** ("what this date's cohort did") so the two are not confused.
  - **Preserve J-21 ordering:** the three leadership lists (Top Sectors / Top Themes / Ranked Cohort) MUST remain **below** Return Attribution. Place the new evidence-aggregate panel at the **bottom** (after the leadership lists) or at the very **top** (before the as-of scan summary) — never between the scorecard, attribution, and leadership lists.
  - **No page-local date control** of any kind. The horizon selector is a horizon view selector, not a date selector (J-18).
- [ ] **Remove the System Health page + nav entry.** Delete `apps/frontend/app/system-health/page.tsx` and the `{ href: "/system-health", label: "System Health", … }` entry from `apps/frontend/components/sidebar.tsx` (NAV, ~line 37). Remove the now-unused `fetchSystemHealth` client + its types in `apps/frontend/lib/api.ts`. (Optional, dev's discretion: a `/system-health → /backtest` redirect for stale deep links — not required.)

### New user-facing capability
The Backtest workspace now shows **time-machine evidence**: at any historical as-of date D, the user reads the forward-tested track record accumulated from **only** the snapshots taken on or before D — by bucket/setup/regime, excess vs benchmarks, VCP/pattern, and the control group — and watches the sample grow as they move the date toward the present. One page, one date control.

### New information displayed
On `/backtest`: an as-of-scoped (expanding-window ≤ D) forward-return-by-bucket table (A–E), excess-vs-SPY/QQQ, by-setup, by-regime, VCP-vs-non-VCP and pattern-vs-non-pattern breakdowns, and the control-group comparison — each with `n` and honest NA. (These previously lived on the now-retired `/system-health`, all-history and date-blind.)

### New user actions
No new control. The **existing** global as-of switcher and the **existing** Backtest horizon selector now also drive the evidence aggregate. (Removing the System Health nav entry is the only nav change.)

### UI surface changes
- `/backtest` gains the evidence-aggregate panel; `/system-health` page and its sidebar entry are removed.

### Product surface delta
Forward-test evidence consolidates onto a single, date-aware home (`/backtest`), replacing the separate date-blind System Health page — so "as of this date, did the rankings work?" is answerable in one place under the single global as-of control.

### Blueprint conformance
- **Information Architecture:** `/system-health` is **removed** from the nav skeleton; J-09 / J-10 (and the relocated J-16 evidence half, J-19 aggregate attribution, J-28 pattern breakdown) now home on **`/backtest`**. This is a **nav-skeleton change** → the blueprint IA is edited AND `state/blueprint.reapproval-requested` is written.
- **Data Contract:** no NEW value is introduced. The existing **"Forward-return aggregates"** row's serving endpoint changes from `GET /api/system-health` to `GET /api/backtest` (as-of-scoped, expanding window ≤ D); its computing module stays the single `app.engine.forward_testing:compute_forward_aggregates` (now with an `as_of` cutoff parameter). The J-19 attribution row's aggregate serving path likewise moves to `/api/backtest`. Edited directly in `blueprint.md`.

### Data-contract additions
None — this is a **relocation + as-of scoping of an existing canonical value**, not a new one. Do NOT introduce a second computing module or a second serving path for the aggregate (that is exactly the drift the coherence-auditor FAILs): `compute_forward_aggregates` stays the single source; `/api/backtest` becomes its single serving home.

## OUT OF SCOPE

- **J-26 (composite factor-combination cohort)** — the next iteration. Do NOT touch `compute_factor_combination` / the Combination Lab this iter.
- **J-32 (Research all-history ⟷ as-of toggle)** — a later iteration; it will reuse this iteration's `asof_date ≤ D` scoping seam on the three `research.py` lab functions. Do NOT add an as-of param to `/api/research/*` this iter.
- **J-22 / J-23 / J-24** — externally Yahoo-429 data-walled and **non-halting** per the re-scoped goal. Do **NOT** autonomously re-probe or retry the data fetch (re-confirmed pointless iters 7–8); they remain honestly `failing`/NA and MUST NOT block this iteration.
- **No new caching/persistence table** for the aggregate. It stays a read-only live grouping over the persisted `forward_returns` (computed once per run), now filtered to ≤ D — the same model System Health used and that coherence has passed every iteration. Per-request memoization is an optional optimization, NOT required for J-09.
- No new factors, patterns, scores, or config scoring literals. No DB schema change, no DB regen.

## DEFINITION OF DONE

- [ ] `compute_forward_aggregates(..., as_of=D)` returns the aggregate over **only** snapshots with `asof_date ≤ D`; `as_of=None` is byte-identical to today's all-history result and equals the latest-date case.
- [ ] `GET /api/backtest?as_of=D` includes the as-of-scoped evidence aggregate (per horizon); the by-bucket A–E table, excess vs SPY/QQQ, by-setup, by-regime, VCP/pattern breakdowns, and control-group all render on `/backtest` with `n` and honest NA.
- [ ] Moving the global as-of switcher to an earlier date re-points the Backtest evidence and **reduces `n`** (sample is non-decreasing toward latest); returning to latest reproduces the full all-history aggregate. **No snapshot dated > D contributes.**
- [ ] **J-09, J-10 pass** via browser-qa-agent on `/backtest`.
- [ ] **J-18 holds:** `/backtest` has **no** page-local date control; the page URL carries no date param; the single global switcher (plus the horizon view selector) drives the evidence. Verified live (distinct before/after shots + network).
- [ ] Required-still-passing journeys remain green — **J-14** (per-date scorecard still renders alongside the aggregate), **J-15** (one fetch keyed `[asOf]`; horizon change does not refetch), **J-19** (attribution; aggregate now on Backtest), **J-16** (VCP-vs-non-VCP breakdown renders on Backtest), **J-28** (pattern breakdown renders on Backtest), **J-21** (leadership lists still below Return Attribution), **J-13**, **J-06**, **J-07**.
- [ ] `/system-health` page, nav entry, route, and unused client are removed; no dangling references (grep clean in `apps/`).
- [ ] No anti-goal violation introduced (see reminders); coherence audit passes.
- [ ] Unit + integration tests pass; full backend pytest green (run ONCE); frontend typechecks/builds.
- [ ] `blueprint.md` updated (IA + Data Contract) and `state/blueprint.reapproval-requested` written.
- [ ] Dev handoff at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-17-dev.md`.

## TESTING REQUIREMENTS

- **Unit/integration (backend, `apps/backend/tests/`):**
  - As-of scoping: with a fixture of runs across several `asof_date`s, assert `compute_forward_aggregates(..., as_of=D)` includes only runs with `asof_date ≤ D`; `n` for an early D < `n` at latest; `as_of=None` == `as_of=latest` == today's all-history result (byte-identical top-level + per-group `n`/means).
  - **No >D leak:** assert no observation from a run dated `> D` appears in the as-of-D aggregate (e.g. a run strictly after D contributes 0 to every group).
  - **Consistency invariant (relocated, not deleted):** the aggregate's `attribution.distribution.mean == overall.mean_return` at a horizon, for the as-of-scoped pool — re-home the existing System Health test onto the Backtest/aggregate path.
  - Endpoint: `GET /api/backtest?as_of=<historical>` returns `evidence_by_horizon` with the expected keys; `GET /api/system-health` is gone (404 / route removed). Unknown/short horizons → NA, not fabricated.
  - Edge: a date with too few snapshots in-window → low-sample cells NA + `n`; an empty regime/bucket → NA + `n=0`, never 0-as-a-number.
- **Browser (Chrome MCP, on a clean hydrated build — see iter-15 lesson):**
  - **J-09:** on `/backtest` read the by-bucket A–E table + excess vs SPY/QQQ + by-setup + by-regime, each with `n`; move the global as-of switcher to an earlier historical date → assert (distinct shots + DOM) the evidence re-points and `n` drops; return to latest → matches all-history. No `as_of` date param in the page URL.
  - **J-10:** on `/backtest` read the control-group comparison (top-ranked cohort vs random-same-sector vs SPY/QQQ/sector ETF) at a stated horizon, each numeric and labelled.
  - **J-18 (principal anti-goal):** confirm `/backtest` has no page-local date dropdown; toggling the global switcher re-points both the per-date scorecard AND the new evidence aggregate; the page URL stays date-free; the single `/api/backtest?as_of=` call is the global date being read (not a 2nd state).
  - Regression spot-checks on `/backtest`: J-14 scorecard, J-19 attribution, J-21 leadership-lists-below-attribution, J-16/J-28 breakdowns present; and J-13 global as-of still re-points other pages.
- **Error cases:** invalid `as_of` / `horizon` rejected or defaulted exactly as today; provider/empty-pool states surface NA + `n`, never fabricated returns.

## NOTES

- **Principal risk = J-18 (Exactly one date selector, critical).** Adding a date-scoped aggregate to `/backtest` is precisely the temptation to introduce a second date state. There MUST be no page-local date picker; the aggregate's cutoff is the **resolved global as-of** (`run.asof_date`), transmitted as the existing `?as_of=` on the snapshot-served read — which MEMORY `j18-asof-on-stocks-fetch-is-correct` confirms is the single global date being read, not a second state. The horizon selector is a view selector, not a date control.
- **Coupling justification for the nav change:** the goal's revised Product Shape drops `/system-health` and homes the evidence on `/backtest`; coherence invariant #12 ("no second home for an existing entity") forbids serving the same `compute_forward_aggregates` value from both pages. Therefore retiring System Health is part of delivering J-09 coherently, not separable scope. The `blueprint.reapproval-requested` marker lets the operator confirm the System Health retirement at iter-18's pre-decomposer pause before the session proceeds to J-26.
- **Sequencing for the wave:** iter-17 establishes the `asof_date ≤ D` scoping seam on `forward_testing`. **iter-18 → J-26** (composite percentile-rank-blend cohort, replacing the strict AND-intersection at `research.py:479` so the Combined cohort is non-empty and scales to all factors). **iter-19 → J-32** (Research all-history ⟷ as-of toggle, reusing this seam on `compute_factor_lab` / `compute_factor_combination` / `compute_event_study`, as a MODE not a second date control). After those land, GOAL_ACHIEVED is reachable on the buildable set (J-22/J-23/J-24 stay honestly NA and non-halting).
- **GOAL_ACHIEVED reachability:** per the re-scoped goal, J-22/J-23/J-24 are non-halting and do not veto completion. Once J-09 (this iter), J-26, and J-32 pass and nothing regresses, the evaluator may declare GOAL_ACHIEVED with J-22/23/24 recorded as honestly blocked (NA) — they auto-heal via the committed runbook with no code change if a reachable egress is later confirmed. **Do not autonomously retry them.**
- **Process reality (this session):** full-depth iters here historically ship without an `-audit.md` handoff and write `status.json` to the **phase-namespace** path `runs/goal-i_can_see_the_wealthy_future_forever-iter-17/status.json` (NOT `runs/goal-session-.../iter-17/`, which holds only `coherence.md` + `snapshot-sha`). The evaluator should verify the critical seams in **source** (the `asof_date ≤ D` filter; no scoring-path change; no page-local date state) rather than trusting the QA artifact table, and de-dup evidence by sha256.
