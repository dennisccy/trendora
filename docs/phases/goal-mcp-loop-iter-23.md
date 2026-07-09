# Goal Iteration 23 — J-14 verification-only re-run (clear CLOSURE-FAIL, flip J-14 partial → passing)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 23
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-14
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-10, J-11, J-12, J-13
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*

## GOAL

Cleanly verify the already-built J-14 deep, vendor-labeled index/macro context through the canonical `browser-qa-agent` lane so J-14 flips partial → passing and the iter-22 `CLOSURE-FAIL` is cleared — with **zero new feature code**.

## BACKGROUND

iter-22 landed the J-14 code (deep `^SPX`/`^NDX`/`^DJI`/`^VIX`/`^TNX` overlays + per-series vendor labels on the Dashboard chart, plus a new `/data` vendor-disclosure panel) and a follow-up `minBarSpacing: 0.02` fix that surfaces the deep 1996 chart window — all independently verified correct on multiple channels. But the canonical `browser-qa-agent` and `ux-regression-reviewer` were never re-run against the FIXED build, so their reports-of-record stayed stale FAIL and `phase-closure` returned `CLOSURE-FAIL`, leaving J-14 `partial` (the iter-13/iter-20/iter-22 verification-tax pattern; lesson iter-22: an in-pipeline audit-fail → dev-fix does NOT auto-re-invoke browser-qa / ux-regression). Per the priority rubric this is the smallest, lowest-risk, unblocking pick — it carries zero risky changes and is the last near-done target (J-02/J-06/J-07/J-08/J-09 need a separate new-basis staging-discovery + honest promotion; J-15/J-16 are unbuilt). Depth = **full** (not lean) because only the full 11-step pipeline re-runs `phase-closure` + `ux-regression-reviewer` + a fresh audit — a lean cycle (developer → reviewer → browser-qa) cannot formally re-clear a `CLOSURE-FAIL`; this matches the iter-22 evaluator's explicit `iter-23 (FULL)` recommendation.

## IN SCOPE

### Backend
- [ ] None — no backend source changes (verification-only).

### Frontend
- [ ] None — no frontend source changes. The `minBarSpacing: 0.02` deep-window fix at `apps/frontend/components/phase-cross-view-chart.tsx:162` already exists in the working tree from iter-22; **ensure it is committed and present in the built bundle under test**. Do NOT add or alter feature code.

### Verification setup (operational, not code)
- [ ] `rm -rf apps/frontend/.next` before serving (iter-20/21 staleness-stamp trap: `start-frontend.sh`'s freshness stamp checks only the backend URL and can silently serve a stale pre-fix bundle).
- [ ] Bring up BOTH prod-mode services — backend `scripts/start-backend.sh` (:8255) and frontend `scripts/start-frontend.sh` (:3255) — and confirm HTTP 200 reachability of BOTH **before** dispatching browser-qa. An empty leaderboard / "Backend unavailable" pill / `curl 000` means STOP and fix the stack; never grade browser cases from code inspection (lessons iter-2/4/13/20).
- [ ] Keep the backend UP for the whole run (the iter-19 item-A OOM fix is in place; do not let a `/api/data` visit hang the run).

### Re-run the verification lanes (the actual work)
- [ ] Canonical `browser-qa-agent` **executes (not code-inspects)** all iter-23 ui-test-plan cases LIVE against the fixed build; regenerate `reports/phase-goal-mcp-loop-iter-23-ui-test-results.md` to a PASS with md5-DISTINCT, correctly-labeled full-page / element-clip screenshots.
- [ ] The J-14 deep-window case flips FAIL → PASS: a deep `^SPX` line is visible in the DEFAULT Dashboard chart view starting before SPY's 2005 first bar (the pre-fix FAIL showed the x-axis floored ~2018). md5-check that the money frame actually shows the deep line in-frame — prefer a full-page / element-clip capture over a scrolled viewport (lessons iter-3/11/13/14); a PASS label or DOM-text line is not proof.
- [ ] The `/data` vendor-disclosure panel renders per-series vendor labels byte-matching `meta.json` (`^SPX` first = 1996-01-02, vendor Stooq; `^VIX` = Yahoo; `^TNX`/`^DXY`/`^VXN` disclosed as "FRED-macro proxy", never as a market index; ETF series carry no vendor label — honest omission, never fabricated).
- [ ] Add a **dedicated J-13 live replay** (two-group availability legend "Price data — cell fill" vs "Scored snapshot — indicator", monotonic non-amber density ramp, violet snapshot ring, an md5-distinct hover-tooltip pair, 548-pool coverage) to close the audit-B5 / ux-regression J-13 replay gap (last dedicated pixel was iter-21).
- [ ] Live-replay the required-still-passing set J-01 / J-03 / J-04 / J-05 / J-10 / J-11 / J-12 against the running stack (grade each against its own golden script in `runs/goal-session-mcp-loop/journey-scripts/`, not test-plan wording — lesson iter-21).
- [ ] `ux-regression-reviewer` re-runs against the FRESH evidence → UX-REGRESSION-PASS; reconcile `user-visible-changes.md`'s "renders automatically" wording.
- [ ] `phase-closure` re-runs → CLOSURE-PASS; reconcile `status.json` / `qa.md` against the real evidence set (no `-fail-` frame sitting under a `blockers:[]` claim — the iter-18 contradiction).

### Permitted test-fixture refresh (only if pinned)
- [ ] If the J-13 golden replay script or any availability test pins the `daily_prices` symbol denominator at 587, refresh it 587→590 as an INTENDED additive change (iter-22 added `^SPX`/`^NDX`/`^DJI` to the load scope; iter-21 lesson: a moved denominator from an intended additive load is not a regression). No other expectation edits.

### New user-facing capability
None new — this iteration makes the ALREADY-BUILT J-14 capability (deep, vendor-labeled index/macro context on the 30-year basis) canonically browser-verified. After it, the deep benchmark render + vendor disclosure is proven, not just code-correct.

### New information displayed
None new. J-14's per-series vendor label + honest first-bar window were introduced and registered in iter-22.

### New user actions
None.

### UI surface changes
None new. Surfaces exercised: Dashboard `/` (the "Regime × phase cross-view" chart with the deep index overlays + vendor legend/tooltip) and `/data` (the index/benchmark vendor-disclosure panel).

### Product surface delta
No functional delta — the delta is verification integrity: J-14's already-shipped surfaces move from "code-correct but not browser-proven" (partial) to "canonically browser-verified" (passing), and the pipeline's closure gate re-clears.

### Blueprint conformance
J-14's homes — Dashboard `/` + `/data` — are already registered in the blueprint Information Architecture homes table; **no new surfaces**. This iteration additionally corrects one stale IA label in `blueprint.md` (J-14's Dashboard home renamed "major-indexes & regime card" → "Regime × phase cross-view card", per the coherence-auditor iter-22 advisory). The registered route `/` is unchanged → no nav-skeleton change, no re-approval.

### Data-contract additions
None. The per-series **vendor label + honest first-bar window** value was registered in the Data Contract in iter-22: computed once by `app.engine.indexes:compute_index_series` (reading the single vendor source `meta.json` `symbols[].vendor` via the existing `data_manager` seed-meta reader), served as additive `vendor`/`first` fields on the EXISTING `GET /api/indexes`, with two readers (Dashboard chart legend/tooltip + `/data` vendor panel). This iteration introduces no new value and reads only the registered canonical source.

## OUT OF SCOPE

- Any new feature code, any chart-config change beyond the already-landed `minBarSpacing` fix, any new UI.
- Any evidence/ledger work — J-02 / J-06 / J-07 / J-08 / J-09 stay sanctioned-partial this iteration (no new-basis staging discovery, no canonical promotion; no staging winner clears the divisor-8 bar today). **NO `## Evidence Claim`** — the post-decompose gate passes automatically (pure verification/context surfacing).
- J-15 / J-16 fast-platform perf (unbuilt; a separate future iteration).
- Deleting the dead-duplicate `index-regime-chart.tsx` / `major-indexes-card.tsx` (coherence-WARN carry-forward) — a source change that would muddy this verification-only signal; defer to a dedicated tidy iteration.
- Altering the `^TNX` first-bar disclosure semantics (audit F4) beyond confirming its honest label renders.

## DEFINITION OF DONE

- [ ] J-14 passes via the canonical `browser-qa-agent`: `reports/phase-goal-mcp-loop-iter-23-ui-test-results.md` = PASS; the deep-window case flips FAIL → PASS (deep `^SPX` line visible in the default Dashboard view before SPY's 2005 start); evidence screenshots are md5-distinct and correctly labeled.
- [ ] Required-still-passing J-01, J-03, J-04, J-05, J-10, J-11, J-12, J-13 re-verified green via live replay (J-13 via a dedicated replay).
- [ ] `ux-regression-reviewer` returns UX-REGRESSION-PASS against the fresh evidence.
- [ ] `phase-closure` returns CLOSURE-PASS; `status.json` not `blocked`; no `-fail-`-named frame sits under a `blockers:[]` claim.
- [ ] No anti-goal violation introduced: both ledgers stay byte-unchanged all-FAIL (7 canonical / 0 PASS, 7 staging); no return/price/buy-sell language; a FRED-macro proxy is never labeled a market index.
- [ ] Unit/integration tests pass; no regressions (backend pytest green including `test_api_indexes.py`; frontend tests green).
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-23-dev.md`.

## TESTING REQUIREMENTS

- **Browser (canonical `browser-qa-agent`, LIVE, every case executed — the DoD-named lane):**
  - **J-14** (target): deep-window default-view case (deep `^SPX` before 2005) FAIL → PASS; Dashboard vendor legend/tooltip labels; `/data` vendor-disclosure panel byte-matching `meta.json`.
  - **J-13** (dedicated replay): two-group availability legend, monotonic non-amber density ramp, violet snapshot ring, md5-distinct hover-tooltip pair, 548/590-pool coverage.
  - **J-01** (/stocks 541/541, zero leaked index carets), **J-03** (all "Not yet proven"), **J-04** (Dashboard regime + evidence link), **J-05** (/evidence all-FAIL auditable rows), **J-10** (Full ↔ Recent history toggle, no crash), **J-11** (no stale edge; ledgers all-FAIL), **J-12** (/data count == /stocks count).
- **Unit/integration:** no new code — re-run existing suites to confirm green. Explicitly confirm `apps/backend/tests/test_api_indexes.py` passes (audit T2 flagged its fixture as expensive/deferred — it backs J-14's `GET /api/indexes` `vendor`/`first` fields). Confirm `test_bar_cache.py` and the evidence frozen-golden suites remain green (unchanged).
- **Error cases:** backend-down / cold state must degrade honestly on the exercised pages (contained state, honest "—"/NA, never a blank application-error page — anti-goal #8); an ETF series with no `meta.json` vendor record renders NO fabricated label.

## NOTES

- **Lessons applied:**
  - iter-22 — an audit-fail → dev-fix on a rendered surface does NOT auto-re-invoke `browser-qa-agent` / `ux-regression-reviewer`; this iteration explicitly re-runs both against the fixed build (a `qa.md` TC-* retest does not satisfy the "pass via browser-qa-agent" DoD).
  - iter-20 — do NOT flip a target to `passing` on code-verification over an empty evidence dir / a `CLOSURE-FAIL`; require a clean canonical lane; `rm -rf .next` + confirm BOTH services reachable BEFORE QA.
  - iter-3/11/13/14 — md5-check evidence PNGs; prefer full-page / element-clip capture for the deep-line money frame; open the actual frame and confirm the deep `^SPX` line is in-frame, never trust a PASS label or a DOM-text line for the target gate.
  - iter-21 — grade a required-still-passing replay against the journey's OWN golden script (`journey-scripts/J-XX.json`), not the test-plan wording; a denominator moved by an intended additive load (587→590) is not a regression.
- The `minBarSpacing: 0.02` fix is uncommitted in the working tree (per iter-22 eval). The build under test MUST contain it — confirm before QA, or the deep-window case will not flip.
- **GOAL_ACHIEVED is NOT reachable this iteration regardless of outcome:** J-02/J-06/J-07/J-08/J-09 remain sanctioned-partial and J-15/J-16 remain unbuilt. This iteration's success = J-14 `passing` + CLOSURE-PASS + zero regressions.
- Coherence was COHERENCE-WARN (not FAIL) at iter-22 → no mandatory consolidation pass. The two WARN carry-forwards are handled as: IA-label drift fixed in `blueprint.md` now (doc-only); dead-duplicate component deletion deferred (OUT OF SCOPE, to avoid muddying this verification-only signal).
- Blueprint updated this iteration: an iter-23 clarification (verification-only, no contract change) + the J-14 Dashboard-home IA-label rename.
