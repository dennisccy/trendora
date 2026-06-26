# Goal Iteration 51 — GOAL_ACHIEVED close-out: flushed-suite confirm + live re-render of J-107 (NO code change)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 51
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-107
- **Required-still-passing journeys:** J-06 (CRITICAL), J-07 (CRITICAL), J-18 (CRITICAL), J-104, J-51, J-25, J-26, J-29, J-01
- **Anti-goal reminders (verbatim from docs/goal.md — zero code change this iter, so none may be newly introduced; the verification must positively re-confirm them):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. Chart **visualization** MAY render bars dated > D strictly as a labelled forward/after-as-of display; this display path MUST NOT feed any score, bucket, setup status, pattern flag, factor value, or ranking — all of which remain computed from bars with date ≤ D — and the moving-average lines drawn past D are visualization only, never as-of signals. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. The scan is computed once per date (bootstrap, scheduled, or first view) and then read from storage. The relocated as-of-scoped evidence aggregate … is likewise derived once per resolved as-of date over the snapshots dated ≤ D, persisted/cached, and read from storage — never recomputed per request and never including a snapshot dated > D. *(extends Single source of truth)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.
  - **Exactly one date selector** (the single global as-of switcher): no page-local or second date state may be introduced.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere.
  - **Honest limitations surfaced.** Walk-forward evidence MUST be labelled as carrying survivorship bias; breadth/new-high-low metrics labelled "universe-relative".

## GOAL

Close out the goal: confirm the standing flushed full-suite gate (`0 failed` / `SUITE_EXIT=0`) and re-render J-107 (Factor Lab all-factors table) plus the critical trio and a sibling research lab on a freshly-warmed live backend, so the evaluator can make a sound GOAL_ACHIEVED determination — with NO code change.

## BACKGROUND

iter-50 landed J-107 (Factor Lab all-factors Rank-IC + downside-risk-adjusted table with expandable per-factor decile sort) — the last unbuilt buildable Must-have — genuinely BUILT and LIVE-PASSING on evaluator-VIEWED evidence, COHERENCE-PASS, review/QA/audit PASS, zero regression. Every buildable Must-have is now positive-evidenced (105/108; the only 3 `unknown` are the data-walled, non-vetoing J-22/J-23/J-24). The single remaining GOAL_ACHIEVED-candidacy gate is the flushed full-suite `0 failed, EXIT 0`, which iter-50 never ran end-to-end; the evaluator launched it nohup-async to `/tmp/iter50_full_suite.log`. As of this planning, that suite is still in flight (~86%, zero failures so far). This iteration is therefore the established lean verify-only close-out (the iter-36→37 / iter-39→40 / iter-42→43 / iter-48 pattern): NO code rework — confirm the suite flushes green and capture the live re-render evidence the strict no-passing-without-live-render rule requires. `Frontend Present: yes` is set deliberately to force the browser-QA render step on a zero-diff iteration (iter-36/39/43 lesson: the auto-skip keys off "did frontend FILES change", not "is a render the acceptance"); there are no frontend edits.

## IN SCOPE

### Backend
- [ ] None — NO code change. (If `git diff HEAD` over `apps/`, `scripts/`, `config*.yaml` is non-empty at execution time, that is a defect: this is a verify-only iteration.)

### Frontend (if applicable)
- [ ] None — NO code change. `Frontend Present: yes` is set only to force the live browser-QA render-capture step (no frontend edits are requested or permitted).

### New user-facing capability
None — verification-only close-out. No new capability.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — this iteration confirms the iter-50 deliverable (J-107) renders on a freshly-warmed backend and that the full test suite is green, enabling the GOAL_ACHIEVED determination.

### Blueprint conformance
No new surfaces. J-107 already lives on its registered home `/research/factor-lab` (Research hub → Factor Lab, 2 clicks from the persistent sidebar; coherence-confirmed iter-50). No blueprint edit required.

### Data-contract additions
None. No new displayed value. J-107's figures are byte-identical re-presentations of the registered canonical Factor-Lab analytics (`research:compute_factor_lab` / `_rank_ic` / `_deciles` / `_risk_adjusted` served via `GET /api/research/factor-lab`); this iteration reads from that registered canonical source only and introduces no second computation or endpoint.

## OUT OF SCOPE

- Any source-code change (backend, frontend, config, scripts). This is verify-only.
- Re-triggering the J-85 `kind:rebuild` snapshot rebuild (~11h, destructive — the data is correct).
- J-22 / J-23 / J-24 — data-walled, NON-VETOING per goal.md:105-108; do NOT attempt the real upstream Yahoo cap-screen / intraday seed here.
- Any new feature, factor, lab, or column.

## DEFINITION OF DONE

- [ ] **Flushed full-suite gate confirmed.** `/tmp/iter50_full_suite.log` (or a freshly relaunched nohup-async full suite if the iter-50 run was killed/never flushed) ends with `0 failed` and `SUITE_EXIT=0`, zero ERROR lines. Any isolated `test_warmup.py` / `test_watchlist_persistence.py` / `test_data_manager_jobs_pipeline.py` E/F is re-run in isolation and confirmed a slow-boot/contention flake before attributing it (iter-29/30/50 lesson). Never block the evaluator on an in-flight suite — if still running at evaluation time, record its progress + zero-failures and let the evaluator confirm the flushed terminal line.
- [ ] Target journey J-107 re-verified `passing` via browser-qa-agent on a freshly-warmed, single-fetch-at-a-time live backend.
- [ ] Required-still-passing journeys (J-06, J-07, J-18 CRITICAL; J-104, J-51, J-25, J-26, J-29, J-01) remain green (live where rendered; the research-cluster siblings via deterministic replay / isolated tests where a live heavy fetch is impractical).
- [ ] No anti-goal violation introduced (trivially held — zero code diff; positively re-confirm Single-source / No-recompute / No-fabrication / Exactly-one-date-selector on the captured frames).
- [ ] Unit tests pass; no regressions (the flushed full suite IS this check).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-51-dev.md` (a no-op handoff documenting "verify-only; zero source diff; suite confirmation owner").

## TESTING REQUIREMENTS

- **Browser (PLAN the Playwright fallback UP FRONT — Chrome MCP CDP has emptied the evidence dir on iters 38/39/40/42; `md5sum` the evidence dir FIRST and reject blank/skeleton/byte-identical frames):**
  - **J-107** on a freshly-warmed backend: the all-factors Factor Lab table renders with real Rank-IC / N / downside-risk-adjusted cells (NOT "Backend unavailable", NOT a "Loading…" skeleton); the sort toggle produces **two byte-DISTINCT frames** (ascending vs descending — `md5sum` the pair, NA-last in both directions); expand a factor row in place to its D1-D10 decile table (raw + downside risk-adjusted + N); a decile `N=` chip opens Research Samples with **Total observations == the chip N** (count-coherent, J-51). Resolve sort/decile/`N=` controls by **`aria-label`, not visible `text()`** (iter-27/28b selector lesson).
  - **CRITICAL trio:** J-06 (single source — a factor's value in the all-factors view == its single-factor view == its breakdown; NVDA/any ticker score identical across pages), J-18 (exactly one date control — 0 native `input[type=date]`; the As-of toggle reduces N via the single global top-bar date, no second date state), J-07 (Risk-Off → 0 Actionable — backend gate untouched).
  - **Sibling lab:** J-104 (a sibling `/research/*` lab — e.g. event-study or factor-combination — loads reliably without OOM / 500 on the warmed backend; honest "Backend unavailable" is acceptable ONLY if the live backend is genuinely contended, in which case re-run the touched module in isolation rather than calling it a regression — iter-45 lesson).
  - **Headline flow:** J-01 (Dashboard hydrates — regime + market-phase + cross-view chart, badge Ready).
- **Operational discipline for the live probes:** bring up `:8835` and WAIT for health `ready` (warm-up finished) before probing; `:3835`; `:9222`. Fetch **one heavy `/research/*` lab at a time** — NEVER concurrently probe heavy research, and NEVER run the full pytest suite concurrently with the heavy-lab probes (pool-exhaustion / OOM lesson, iters 45/46/47). Factor Lab is intentionally uncached (~50-120s cold compute over ~598K rows) — allow time before the first cache hit. Use the correct query param spelling `?as_of=` (the frontend sends it automatically — do NOT curl `?asof=`; iter-45 false-negative).
- **Unit/integration:** the full pytest suite is the gate (flushed `0 failed` / `SUITE_EXIT=0`). No new tests (no code change). If the iter-50 suite was killed, relaunch it nohup-async via the pump and gate on the flushed terminal line.
- **Error cases:** none new. The honest "Backend unavailable — No figures are shown rather than fabricated values" state under genuine contention is correct behaviour, not a fabrication (No-fabricated-data anti-goal).

## NOTES

- This is a verify-only close-out. The developer agent is effectively a no-op; the value is entirely in the flushed-suite confirmation + the browser-qa live re-render. Do NOT introduce any code change to "improve" anything — a non-empty `apps/`/`scripts`/`config` diff is itself a defect this iteration.
- After the suite flushes `0 failed, EXIT 0` with COHERENCE-PASS (trivial — zero source diff) and zero regression, AND J-107 + the critical trio re-render green, this is a sound **GOAL_ACHIEVED** close-out: every buildable Must-have (J-01..J-21, J-25..J-108) positive-evidenced; J-22/J-23/J-24 stay honestly blocked-NA (data-walled, NON-VETOING per goal.md:105-108).
- **Applied lessons (episodic memory):**
  - iter-50: a correct, COHERENCE/review/QA/audit-PASS feature is NOT a GOAL_ACHIEVED close-out until the flushed full-suite gate is positively confirmed — iter-50 produced no flushed log; the evaluator launched it. Confirm `/tmp/iter50_full_suite.log` reaches `SUITE_EXIT=0` (or relaunch).
  - iter-40: a differential leg (the J-107 sort toggle) must produce **byte-DISTINCT** before/after frames — `md5sum` the pair and reject byte-identical "before"/"after" (recurring false-positive trap).
  - iter-43/36/39: set `Frontend Present: yes` on a zero-diff verify iter to force the browser-QA render-capture step (done here); plan the Playwright fallback up front.
  - iter-45/46/47/48: heavy `/research/*` browser-QA MUST run on a freshly-restarted, warmed, single-fetch-at-a-time backend; never run the full suite concurrently with heavy-lab probes; order any ScannerResult read by `(run_id, id)` (no code change here, but relevant if a probe is mis-attributed); "Backend unavailable" under contention is not a regression — disambiguate by re-running the touched module in isolation.
  - iter-44: on an early/pre-history as-of, wait for the rendered NA card to hydrate before capturing — reject a "Checking backend…" skeleton as evidence.
  - iter-27/28b: resolve sort buttons by `aria-label`, not visible `text()`.
- Reference: iter-50 eval recommendation (`runs/goal-session-…/iter-50/eval.md` §Next-Step) and iter-50 coherence verdict (COHERENCE-PASS, snapshot SHA bd97d19).
