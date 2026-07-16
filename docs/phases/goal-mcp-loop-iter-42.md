# Goal Iteration 42 — LEAN deterministic-replay closeout (pay down the required-set replay debt before GOAL_ACHIEVED)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 42
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-24
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15, J-16, J-17, J-18, J-19, J-20, J-21, J-22, J-23, J-25
- **Anti-goal reminders:**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*

## GOAL

Prove — by deterministic golden replay of the 22 scripted journeys, a live browser-qa walk of the one un-scripted journey (J-24), and a fresh perf re-measurement of J-15/J-16 — that all 25 Must-have journeys are reproducibly correct and within budget on the current build, closing the accumulated replay debt so the evaluator can honestly assess GOAL_ACHIEVED. This iteration delivers **verification confidence, not a new capability**.

## BACKGROUND

All 25 Must-have journeys now carry status `passing` (J-25 flipped unknown → passing at iter-41, the last unbuilt Must-have). The iter-41 evaluator deliberately returned CONTINUE, not GOAL_ACHIEVED, because iter-41's own DoD **deferred** the required-set deterministic golden-replay to this iter-42 lean closeout, and three goldens have never been mechanically replayed. This iteration pays that debt down and is the sanctioned **periodic full-regression pass** (re-replay every golden + refresh the golden set + catch selector drift).

Depth is **lean and mandatory**: the deterministic-replay lane (`demo_runner.py --mode verify`) lives ONLY in `goal-iter-lean.sh`. A FULL iter routes through `run-phase.sh`, which has zero replay-lane machinery and would re-skip it — the recurring iter-33/36/38/40/41 gap. The iter-41 eval explicitly recommends lean; there was no ESCALATE. This is verify-only with **zero product source changes** — a code change now would introduce regression risk immediately before a GOAL_ACHIEVED assessment.

Two evidence-driven scoping corrections drive the target/required split below (see NOTES for detail):
- **J-24.json does not exist.** Verified on disk (`find . -name J-24.json` → nothing; 22 of 25 journeys have a golden — J-15/J-16 are perf journeys with none by design, and J-24's was never authored because iter-40's Chrome-MCP DevTools-port outage made the canonical browser-qa lane record 0/16 SKIPPED). So the eval's "fold in J-24.json" is executed as **author** J-24.json via the now-healthy live walk (Chrome MCP recovered at iter-41). Hence J-24 is the sole **Target** (LLM browser-qa lane walks it live AND writes its golden on PASS).
- **iter-39 trap (lessons.md iter-39):** a golden placed in the *Target* set is LLM-walked, NOT `demo_runner`-replayed — which is exactly why J-23.json still had zero replay coverage after a prior "fold it in" mandate. To actually run J-23.json and J-25.json through `demo_runner` this iter, J-23 and J-25 (and every other existing golden) are in **Required-still-passing**, never Target.

## IN SCOPE

This is a verify-only closeout: the "scope" is verification actions and their artifacts, not code. There are no product-code changes.

### Backend
- [ ] None — verify-only; zero changes to `apps/backend/app/**`, `config.yaml`, or the seed.

### Frontend (if applicable)
- [ ] None — verify-only; zero changes to `apps/frontend/**`.

### Verification actions (no product code)
- [ ] **Deterministic golden replay** of the 22 golden-bearing Required-still-passing journeys via `demo_runner.py --mode verify` (the lean lane runs this automatically over the Required set that has goldens on file), writing `reports/phase-goal-mcp-loop-iter-42-regression-replay-results.md`. This is the **first-ever** `demo_runner` replay of `J-23.json` and `J-25.json`.
- [ ] **Author + lint J-24.json**: the live browser-qa walk of J-24 writes a self-contained golden replay script to `runs/goal-session-mcp-loop/journey-scripts/J-24.json` (the lane writes a golden per PASS lacking one), so J-24 is deterministically replayable in future iterations.
- [ ] **Perf re-measurement (J-15/J-16)**: run `scripts/measure-perf.sh` in prod mode and append to `reports/perf-budgets.md`; confirm warm endpoint latencies + one bounded K-date backfill timing + the DB capacity snapshot are within budget and memory stays under the 6144 MB cap.
- [ ] **Ledger invariant check**: confirm `certified-claims.jsonl` and `staging-ledger.jsonl` are each 7 FAIL / 0 PASS and the canonical Bonferroni divisor stays 8 (currently verified 7/7 FAIL each, divisor 8).

### New user-facing capability
None. The existing product is unchanged; this iteration produces reproducible verification evidence for it.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — the product experience is identical to iter-41. The deliverable is a fresh, reproducible replay + perf record proving the 25-journey product is correct and within budget on the current build.

### Blueprint conformance
No new surfaces. Every journey verified here uses its existing canonical home already registered in `runs/goal-session-mcp-loop/state/blueprint.md` (Stocks / Stock Detail, Evidence, Watchlist, Data Manager, Research labs, Dashboard, cross-cutting chrome). No nav-skeleton change; no blueprint edit and no `blueprint.reapproval-requested` this iteration.

### Data-contract additions
None. No new displayed value is introduced, so nothing is added to the Data Contract (blueprint.md is left unchanged — additive-only edits are only made when a new value appears).

## OUT OF SCOPE

- **Any product code change.** Verify-only; a diff here is a regression risk before a GOAL_ACHIEVED assessment.
- **Phase-badge color polish** (iter-41 COHERENCE-WARN / review MINOR: color the `/evidence` expectations-panel phase `Badge` via `lib/phase.ts` `phasePosture`) — explicitly deferred by the iter-41 eval ("do NOT bundle into the closeout"); belongs to a future `/evidence` touch.
- **Audit T1 method-note sentence** (disclose that time-to-recover is measured only over names that recovered within the horizon) — deferred to the same future `/evidence` touch.
- **Any new feature, new journey, or new `## Evidence Claim`** — no edge hunt; both ledgers stay byte-identical (divisor stays 8).
- **Re-running the full pytest suite** (test-only ~10 h cost on the 30-year basis; out of scope per goal §K and prior notes — the product boots fast; the deterministic replay + perf lane are the verification here).
- **The 6 deferred `risk_budget` integration tests** — optional, non-blocking, byte-match-mitigated (see NOTES); do not gate iter-42.
- **The durable framework fix** (add the replay lane to `run-phase.sh` / the full path of `run-goal.sh`) — a maintainer-owned framework change, not product-iteration work; noted for the maintainer, excluded here.

## DEFINITION OF DONE

- [ ] `reports/phase-goal-mcp-loop-iter-42-regression-replay-results.md` EXISTS and records PASS for every deterministically-replayed golden-bearing Required journey — J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-17, J-18, J-19, J-20, J-21, J-22, J-23, J-25 (22 journeys) — **including the first-ever `demo_runner` replay of J-23.json and J-25.json**.
- [ ] `runs/goal-session-mcp-loop/journey-scripts/J-24.json` exists (newly authored, lint-clean) AND J-24 passes via a live browser-qa walk of the `/stocks/{ticker}` risk-budget card + the `/stocks` leaderboard ATR% / downside-vol columns.
- [ ] J-15 and J-16 re-verified against `reports/perf-budgets.md`: a fresh measurement is appended, all core-page/API latency + job-timing budgets hold (no regression), and memory stays under the 6144 MB cap.
- [ ] Both ledgers (`certified-claims.jsonl` + `staging-ledger.jsonl`) confirmed 7 FAIL / 0 PASS each; canonical Bonferroni divisor stays 8; no `## Evidence Claim` in this spec ⇒ the post-decompose gate passes automatically.
- [ ] Zero product source diff: `git diff` empty on `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, `apps/backend/data/seed/**`, and all three ledgers — the closeout adds only test-golden + report artifacts.
- [ ] Target journey J-24 and all 24 Required-still-passing journeys remain `passing`; none regressed.
- [ ] No anti-goal violation introduced.
- [ ] Unit tests pass; no regressions (no new code paths this iter — the deterministic replay + perf lane are the regression proof).
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-42-dev.md`.

## TESTING REQUIREMENTS

- **Browser (live LLM browser-qa lane) — J-24:** confirm Chrome-MCP health first (recovered at iter-41). Walk the risk-budget card on `/stocks/AAPL` (6 tiles: ATR%, downside vol, worst-20d window, distance-to-invalidation, overnight-gap median/p95/worst, overnight share of 20d variance — each with its "pXX of universe" chip + "Descriptive only; not a recommendation.") and the ATR% / downside-vol columns on the `/stocks` leaderboard. **Author + lint `J-24.json`** as a golden for future deterministic replay. (J-24 is the live-walk target because its golden was never written — iter-40 Chrome outage.)
- **Deterministic replay (Required golden set):** `python3 scripts/automation/lib/demo_runner.py --mode verify --scripts-dir runs/goal-session-mcp-loop/journey-scripts --journeys <the 22 golden-bearing Required journeys>` → `reports/phase-goal-mcp-loop-iter-42-regression-replay-results.md`. The lean lane runs this automatically for the Required-still-passing journeys that have goldens on file; **J-23.json and J-25.json replay for the first time.** A replay FAIL must be re-confirmed by the LLM lane before it is treated as a real regression (a brittle selector must not fake a regression — the lane's own rule).
- **Perf (J-15/J-16 — measurement journeys, NOT browser/replay lanes):** run `scripts/measure-perf.sh` in prod mode (`start-backend.sh` / `start-frontend.sh`, not `--reload`/`next dev`); append to `reports/perf-budgets.md`. Verify warm endpoint latencies + one bounded backfill timing + the DB capacity snapshot are within budget; memory under the 6144 MB cap. J-15/J-16 have no golden by design — do not browser-walk or replay them.
- **Unit/integration:** no new code paths (verify-only); the existing suite is not re-run wholesale (test-only cost, out of scope). The deterministic replay + the perf lane are the verification.
- **Error cases:** N/A (no new inputs). The deterministic replay is precisely the mechanism that catches selector drift / silent regressions the LLM browser-qa lane might miss.

## NOTES

- **Depth justification (rubric trigger):** lean is mandatory — the deterministic-replay lane exists ONLY in `goal-iter-lean.sh`; a FULL iter routes through `run-phase.sh` (zero replay-lane refs) and would re-skip the closeout (recurring iter-33/36/38/40/41 gap). Also: verify-only / zero-code = lean by the rubric; no ESCALATE from iter-41.
- **J-24.json did not exist** (verified: `find . -name J-24.json` → nothing; disk has 22 goldens, J-15/J-16/J-24 absent). It was never authored because iter-40's Chrome-MCP DevTools-port outage made the canonical browser-qa lane record 0/16 SKIPPED — no golden was written for the journey it built. So "fold in J-24.json" is executed as **author it via the now-healthy live walk**, then it exists for future replay; a live walk is at least as strong as a scripted replay (iter-39 lesson). Logged to `assumptions.md`.
- **iter-39 trap avoidance (load-bearing, lessons.md iter-39):** J-23 and J-25 are in the **Required-still-passing** set (NOT Target) SO THEIR GOLDENS ACTUALLY RUN THROUGH `demo_runner`. At iter-39, J-23 was placed in Target, got LLM-walked, and its golden got zero replay coverage despite a "fold it in" mandate. Do not repeat: this iter's deterministic replay must cover J-23.json + J-25.json.
- **Do NOT paper over the replay** (iter-33/36 CLOSURE-FAIL trap, lessons.md iter-33/36): the `regression-replay-results.md` artifact must ACTUALLY be written and opened — a "replay runs next step" claim is unacceptable; the closure auditor and evaluator will re-open the artifact and re-check the ledger 7/7-FAIL state.
- **Required-set widening is intentional:** this is the sanctioned periodic full-regression pass (all 22 goldens re-replayed + J-24.json newly authored), which also refreshes goldens and catches selector drift — matching the iter-41 eval's "full required-still-passing golden set" mandate.
- **Stale-frontend-build guard (lessons.md iter-35):** before the browser walk, confirm `.next/BUILD_ID` postdates any touched frontend source (there is none this iter) and services are freshly restarted (the pump restarts services before browser-qa) so a "card missing / zero occurrences" observation is never a stale-build artifact.
- **If the replay surfaces a genuine regression the browser-qa lane missed, ESCALATE / REGRESSION as warranted** — that is exactly why this closeout exists (iter-41 eval). Otherwise, after a clean iter-42 (replay green + J-24 walked/authored + J-15/J-16 budgets hold + ledgers 7/7 FAIL), the evaluator should assess GOAL_ACHIEVED. That call belongs to the goal-evaluator + the two-key confirm + deterministic gates, not this spec — a lean feature-free closeout cannot self-declare done.
- **Optional, explicitly NON-BLOCKING (not bundled):** the phase-badge color polish + the audit T1 method-note sentence (both future `/evidence` touch), and the 6 deferred `risk_budget` integration tests (`pytest tests/test_scoring.py -k risk_budget`, byte-match-mitigated). None gate iter-42.
- **Durable framework fix owed to the maintainer** (recurred iter-33/36/38/40/41): add the deterministic-replay lane to `run-phase.sh` / the full path of `run-goal.sh` so a FULL iter no longer structurally re-creates this replay gap. Out of scope for this product iteration; recorded for the maintainer.
