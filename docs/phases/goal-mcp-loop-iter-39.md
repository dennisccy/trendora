# Goal Iteration 39 — Lean verify-only closeout: deterministic replay closes the iter-38 CLOSURE-FAIL

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 39
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes (verification is browser/replay-driven over EXISTING surfaces; ZERO frontend source changes)
- **Target journeys:** J-01, J-02, J-03, J-05, J-10, J-13, J-20, J-23
- **Required-still-passing journeys:** J-04, J-06, J-07, J-08, J-09, J-11, J-12, J-14, J-17, J-18, J-19, J-21, J-22
- **Evidence Claim:** none (pure verification/record closeout — no new "proven" claim; the post-decompose gate passes automatically; canonical Bonferroni divisor stays 8)
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

Formally re-verify the required-still-passing journeys by **deterministic golden-script replay** (no product change), producing the `regression-replay-results` report the iter-38 FULL iteration structurally could not write — which re-clears phase closure to **CLOSURE-PASS** and folds the new **J-23.json** golden into the replayed set for the first time.

## BACKGROUND

iter-38 (FULL) delivered J-23 cleanly but ended **CLOSURE-FAIL** on a single narrow DoD line: the required-still-passing set (J-01/02/03/05/10/13/20) was carried on byte-identity and never golden-replayed, because a FULL iteration routes through `run-phase.sh`, which has **zero** deterministic-replay-lane machinery — the replay lane lives ONLY in `goal-iter-lean.sh` (the recurring iter-33 / iter-36 / iter-38 structural gap; documented in `lessons.md` iter-33 and iter-36). The evaluator's iter-38 verdict explicitly mandates **iter-39 = lean verify-only closeout** (the proven iter-33→34 / iter-36→37 pattern). Verified on disk before planning: git HEAD is `66bb348` (the iter-38 J-23 delivery), `reports/phase-goal-mcp-loop-iter-38-regression-replay-results.md` does NOT exist (gap open), and all eight target goldens are present in `runs/goal-session-mcp-loop/journey-scripts/`. Depth is **lean** because the replay lane is only reachable through the lean path (running full would re-route through `run-phase.sh` and re-skip it) and the work is verify-only, no code, low risk; prior verdict was CONTINUE (not ESCALATE), so no forced-full applies. Coherence was COHERENCE-PASS at iter-38 — no coherence consolidation is owed; this iteration consolidates the OPEN closure gap before any J-24/J-25 feature work, so the replay debt does not compound across two consecutive FULL iters.

## IN SCOPE

### Backend
- [ ] None. No backend source changes. This is a verify-only closeout — the developer step is a no-op on product code.

### Frontend
- [ ] None. No frontend source changes.

### Verification / record work (the substance of this iteration)
- [ ] Run the lean deterministic-replay lane (`goal-iter-lean.sh` → `demo_runner.py --mode verify`) over the **full on-disk golden set** — J-01–J-14 and J-17–J-23 (21 journeys) — **folding in the new `J-23.json` golden for the first time in a required replay** (it was linted clean at iter-38 but never yet replayed).
- [ ] Emit `reports/phase-goal-mcp-loop-iter-39-regression-replay-results.md` recording the assertion-driven per-journey PASS results (named by the running iter, matching the iter-34 / iter-37 on-disk precedent).
- [ ] Merge the replay results into `reports/phase-goal-mcp-loop-iter-39-ui-test-results.md` so the required-still-passing set is on-record re-verified.
- [ ] Correct the record item the iter-38 QA lane over-claimed: its **TC-17** row graded a target PASS on a bare HTTP-200 smoke rather than a golden replay (the exact iter-33/iter-36 over-claim) — the corrected row must reflect the deterministic replay evidence, not an HTTP-200 probe. (Documentation/record correction only; no source or test-logic change.)

### New user-facing capability
None — no user-visible change. This iteration re-verifies already-shipped capability and closes an evidence-trail gap.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — the product is byte-identical to the iter-38 commit. The only deltas are verification artifacts under `reports/` (+ standard harness bookkeeping under `runs/`).

### Blueprint conformance
No new surfaces. All replayed journeys render on their existing canonical homes already registered in `blueprint.md` (`/stocks`, `/stocks/{ticker}`, `/evidence`, `/data`, `/watchlist`, the layout-level preflight banner). No Information-Architecture change; no nav-skeleton change; no `blueprint.reapproval-requested`.

### Data-contract additions
None. This iteration introduces no displayed value. Every replayed value reads from its already-registered canonical computing module + serving endpoint per `blueprint.md`; no second computation or endpoint is introduced.

## OUT OF SCOPE

- **All J-24 / J-25 feature work** — per the evaluator's plan, J-24 (backlog B-201 per-stock risk-budget card) is iter-40 (FULL) and J-25 (backlog B-205 phase-conditional drawdown/dry-spell) is iter-41 (FULL). One risky surface per iteration; do NOT start either here.
- Any new feature code, new endpoint, new page, new displayed value, or any `## Evidence Claim` (divisor must stay 8; never re-submit a closed FAIL).
- **J-15 and J-16 deterministic replay** — these are performance journeys with no golden script; they are carried on byte-identity (logic files git-untouched) and their `last_verified_iter` stays unchanged (J-15 at iter-27, J-16 at iter-35), matching the iter-34 / iter-37 precedent. Do NOT attempt to golden-replay them.
- **Non-blocking carry-forwards from the iter-38 eval — do NOT bundle** (they belong to the next iteration that TOUCHES the watchlist X-ray, i.e. not this one): B1 (tighten `WatchlistXrayCfg` validator `>` → `>=`); F1 (surface `enb_member_count` in the ENB headline); T2 (optional 3-ticker composer test asserting clusters + ENB together).
- Any product/source edit whatsoever. If the replay surfaces a genuine defect, that is a finding to be escalated to the evaluator — NOT fixed inside this verify-only pass (a fix would change product bytes and break the "zero product diff" DoD, and a rendered-surface fix would itself need a fresh canonical browser-qa re-run — the iter-22/iter-31 partial-trap).

## DEFINITION OF DONE

- [ ] The lean deterministic-replay lane runs `demo_runner.py --mode verify` over the full golden set (J-01–J-14, J-17–J-23; 21 journeys, J-23.json folded in) and **every journey replays PASS** (assertion-driven — "all expects held", not screenshot-driven).
- [ ] `reports/phase-goal-mcp-loop-iter-39-regression-replay-results.md` exists and records the all-PASS result; the merged `reports/phase-goal-mcp-loop-iter-39-ui-test-results.md` shows the Target set (J-01/02/03/05/10/13/20 + J-23) re-verified.
- [ ] Phase closure re-clears to **CLOSURE-PASS** (the iter-38 required-still-passing replay gap is closed).
- [ ] **Zero product diff:** `git diff HEAD` is empty on `apps/backend/app`, `apps/frontend`, `config.yaml`, `apps/backend/data/seed`, and all three ledgers — `runs/goal-session-mcp-loop/state/certified-claims.jsonl` (7 entries / 0 PASS), `staging-ledger.jsonl` (7 / 0 PASS), `pre-registrations.jsonl` — so the canonical Bonferroni divisor stays 8 and there is no regression mechanism.
- [ ] The iter-38 QA **TC-17** over-claim is corrected in the iter-39 record (deterministic-replay evidence, not an HTTP-200 smoke).
- [ ] Required-still-passing journeys remain green (re-verified via the same replay).
- [ ] No anti-goal violation introduced (trivially satisfied — no code diff means no new violation mechanism; all 8 anti-goals upheld).
- [ ] Unit tests: no new tests required; no product code changed, so nothing to regress.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-39-dev.md` documenting the verify-only / no-op-on-product nature and pointing to the replay report.

## TESTING REQUIREMENTS

- **Browser / deterministic replay:** the primary and only substantive test surface. Run the golden-script replay over the full set; the closure-relevant Target journeys are **J-01, J-02, J-03, J-05, J-10, J-13, J-20** (the iter-38 byte-identity-carried required set) plus **J-23** (its new golden's first replay). All must replay PASS by assertion.
- **Unit/integration:** none new. This is a verify-only closeout — do NOT introduce or pin any slow, rarely/never-completed test (e.g. the ~30-year `loaded_engine` fixture suite) as a hard DoD gate (lessons.md iter-23): the product bytes are unchanged from the iter-38 verified commit, so there is nothing new to unit-test, and pinning a fixture that fork-locks the box would contradict the zero-code scope.
- **Error cases:** N/A — no code paths added or modified.

## NOTES

- **Why lean is mandatory (lessons.md iter-33, iter-36):** the "required-still-passing deterministic replay" DoD line is structurally UNSATISFIABLE by any FULL iteration — `run-phase.sh` has zero replay-lane refs; only `goal-iter-lean.sh` owns the lane (`demo_runner`/`journey-scripts`/`REQUIRED_JOURNEYS`). Running iter-39 as full would re-route through `run-phase.sh` and re-create the exact gap it is meant to close. **Systemic flag (recurred iter-33, iter-36, iter-38 — carried, not owed to this iter):** the durable framework fix is to add the replay lane to `run-phase.sh` / the full path of `run-goal.sh`, or run the closure one-liner replay inline inside full iters. Recording only — no action taken here.
- **This is hygiene/record remediation of an OPEN closure failure, not a J-23 re-litigation:** J-23's own canonical browser-qa evidence was complete and clean on the final build at iter-38 (closure explicitly exempted it). This pass exists solely to produce the deterministic-replay record for the OTHER (required-still-passing) journeys and re-clear closure.
- **Benign dup-md5 among `-verify.png` replay frames is expected (lessons.md iter-29):** several journeys legitimately share an endpoint (J-01–J-09 land on `/evidence`, J-13/J-14 on `/data`), so their replay frames may be byte-identical. This is NOT the reused/error-frame anti-pattern — the discriminator is that replay PASS is assertion-driven and opening one colliding frame shows a real, byte-correct page. Do not flag dup-md5 as a defect; do open one to confirm it is not a shared ERROR page.
- **A required-replay journey can FAIL a P1 UT case without being a regression (lessons.md iter-21):** before treating any replay FAIL as a regression, grep the journey's OWN golden script for the failing page/assertion, confirm `git diff` shows the implicated files were untouched this iter, and confirm the substantive capability elsewhere. A stale test reference is a test-plan defect (retarget it), not a `passing→failing`.
- **Stale prod-frontend-build caution (lessons.md iter-20 / iter-35):** if the lane drives any live browser step, confirm `.next/BUILD_ID` postdates the touched source before trusting a "missing element" observation. Low risk here — no frontend source changes this iter, so the existing build is already current — but the replay lane should still verify service reachability rather than record a blanket SKIP over a live stack.
- **Assumption ledger:** no entry — this is a routine scoping pick (a verify-only closeout mandated by the open CLOSURE-FAIL + the evaluator's explicit recommendation + the structural fact that replay runs only in the lean lane), not an interpretation of ambiguous goal text.
- **After this closeout:** iter-40 = FULL J-24 (backlog B-201 per-stock risk-budget card — read the binding B-201 card in `docs/improvement-backlog.md` before planning), then iter-41 = FULL J-25 (backlog B-205). After those two, all 25 Must-haves are passing and GOAL_ACHIEVED becomes reachable.
