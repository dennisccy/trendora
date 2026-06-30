# Goal Iteration 5 — Decisive canonical verification pass (free the QA frontend port; re-confirm all five journeys; write the audit handoff)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05
- **Required-still-passing journeys:** J-01, J-02, J-03, J-05
- **Evidence Claim:** none — this iteration ships NO new "proven" claim (pure verification + QA-harness fix), so per `docs/goal.md` Loop mechanics the post-decompose gate passes automatically. Do NOT add an `## Evidence Claim` block.
- **Anti-goal reminders:**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## GOAL

Close the verification-integrity gap that is the sole blocker to GOAL_ACHIEVED: fix the QA harness so the **canonical** `browser-qa-agent` lane can bind the frontend port, then capture fresh canonical screenshots that re-confirm all five Must-have journeys end-to-end through that lane (flipping J-04 partial → passing), and produce the post-QA audit handoff.

## BACKGROUND

The features for all five journeys are already built and referee-certified — `certified-claims.jsonl` carries two PASS entries (leadership_score; Breakout-watch × Risk-on regime event-study), and iter-4 visually confirmed J-04 via the QA agent's parallel lane. GOAL_ACHIEVED is withheld for two tractable, non-feature reasons the iter-4 evaluator named: (1) the **canonical** `browser-qa-agent` lane SKIPPED all 11 checks ("frontend not running") because a stale `next-server` held the frontend port — `scripts/start-frontend.sh` lacks the pre-bind port-free that `scripts/dev.sh` already has (confirmed in the script and in iter-4 dev-handoff Known Issue #2) — so J-01/J-02/J-03 carry without fresh canonical pixels and J-04 is stuck at `partial`; and (2) the spec-required post-QA **audit handoff is absent** (the audit stage stopped at `qa_complete` in both iter-3 and iter-4). Depth is **full** because the auditor stage — which only the full 11-step pipeline runs (the lean cycle has no auditor) — must this time complete and write `docs/handoffs/goal-mcp-loop-iter-5-audit.md`, and because this is a terminal hardening/verification pass. The iter-4 evaluator explicitly recommended **full**.

## IN SCOPE

### Backend
- [ ] None. **Zero `apps/backend/app/**` diff** (no engine / referee / ledger / endpoint change) — this trivially preserves the determinism / no-lookahead anti-goal and keeps every served number byte-identical.

### Frontend (if applicable)
- [ ] None (no `apps/frontend/**` **product-code** change). The evidence surfaces (`/stocks`, `/stocks/{ticker}`, `/evidence`, Dashboard regime card + affordance) are already built and certified; this iteration **re-verifies** them through the canonical browser lane, it does not modify them. `Frontend Present: yes` because the browser-qa-agent lane must run against the live frontend — that verification *is* this iteration's deliverable.

### Test harness / QA infrastructure (the ONE allowed code change)
- [ ] `scripts/start-frontend.sh` — insert a **pre-bind port-free block** immediately before `exec npx next start -p "$FRONTEND_PORT"` (currently the last line, ~line 55), mirroring the proven pattern already in `scripts/dev.sh` (lines 23–41): for `$FRONTEND_PORT`, `lsof -ti :$PORT | kill -9`, then `fuser -k -9 $PORT/tcp`, then a **bounded** wait loop (≤ ~5s) that re-kills until `lsof` shows no owner AND `ss -tlnH sport = :$PORT` shows no lingering socket. This guarantees a stale `next-server` from a prior run cannot hold the port and force the canonical lane to SKIP ("frontend not running") or serve a stale bundle — the exact iter-4 failure. Leave the existing stamp-guarded `next build` / `next start` logic unchanged; only ADD the preamble. The loop exits immediately when the port is already free, so the normal path is unaffected. **Do NOT touch `apps/`.**

### New user-facing capability
None — verification + harness only. No new product capability this iteration.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None. Existing surfaces are re-verified, not changed.

### Product surface delta
None. The user-visible product is byte-identical to iter-4; this iteration only proves it on the session-standard lane and hardens the QA bring-up so that proof is reproducible.

### Blueprint conformance
No new surfaces. All re-verified pages already have canonical homes in `blueprint.md`: J-01 `/stocks`; J-02 `/stocks/{ticker}`; J-03 cross-cutting badge state on `/stocks` + detail; J-04 `/` (regime + affordance) + `/evidence` (regime-labeled row); J-05 `/evidence`. No nav-skeleton change, so no `blueprint.reapproval-requested`.

### Data-contract additions
None. No new displayed value. Every value captured this iteration reads from its already-registered canonical source: evidence status / certified-claims via `GET /api/evidence` (Data Contract row 1); scores via `GET /api/stocks` / `GET /api/stocks/{ticker}`; regime via `GET /api/dashboard`. The harness script computes and serves nothing — zero data-contract impact. No `blueprint.md` edit is required this iteration.

## OUT OF SCOPE

- Any change under `apps/backend/**` or `apps/frontend/**` (product code). The feature is complete and certified; modifying it would re-introduce risk and could require re-certification. If the browser lane reveals a genuine **product** defect (not a harness/capture issue), stop and flag it — do not silently patch UI here.
- Any new Evidence Claim / new "proven" signal / new certified-claims entry. No new edge is proposed this iteration.
- Adding the optional `tsx` frontend devDependency (iter-3/iter-4 reviewer NOTE). It is explicitly **not required for DoD**, an `npm install` risks the local-first/offline constraint, and the existing `tsc`-transpile path runs the frontend unit tests fine. If ever added, it must go through the supply-chain security gate — but NOT in this verification pass.
- Any nav / IA change, new page, or new displayed value.

## DEFINITION OF DONE

- [ ] `scripts/start-frontend.sh` frees `$FRONTEND_PORT` before binding (mirrors `dev.sh`: `lsof`+`kill -9`, `fuser -k -9`, bounded wait-until-released), so a pre-occupied port no longer causes the canonical lane to SKIP or serve a stale bundle.
- [ ] The **canonical** `browser-qa-agent` lane actually RUNS (`browser_checks_run=true`; the result file is NOT all-SKIP) and renders fresh canonical **UT-*** screenshots for all five journeys in `reports/phase-goal-mcp-loop-iter-5-ui-test-results.md`.
- [ ] Target journeys J-01, J-02, J-03, J-04, J-05 PASS via the canonical browser-qa-agent lane (J-04 flips `partial` → `passing`; the other four re-confirmed with fresh canonical pixels, not carried, not via the parallel TC-* lane).
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-05 remain green.
- [ ] No anti-goal violation introduced (verified: zero `apps/` diff; displayed numbers byte-match `GET /api/evidence` and `certified-claims.jsonl`; Entry Quality + Risk still read "Not yet proven"; the signal-less regime claim lights no inline score badge; no buy/sell/return-promise language; secret scan clean).
- [ ] Unit tests pass; no regressions (`apps/backend/tests/test_evidence.py`, `test_api_evidence.py`; `apps/frontend/lib/evidence.test.ts`, `lib/api-base.test.ts`) — the harness change touches no app code, so these must be unchanged and green.
- [ ] **Post-QA audit handoff** written at `docs/handoffs/goal-mcp-loop-iter-5-audit.md` with a PASS or PASS_WITH_GAPS verdict (the audit stage stalled at `qa_complete` in iter-3 and iter-4 — it MUST complete this time; this is the gating process gap).
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-5-dev.md`.

## TESTING REQUIREMENTS

**Pre-flight reachability gate (do this BEFORE scoring any journey — iter-2 lesson).** Confirm the frontend can reach the backend: `GET /api/evidence` returns the **2 claims** (`proven_signals` keys == `["leadership_score"]`, proven `true`; the 2nd row `kind=event-study`, `signal=null`, `regime=Risk-on`, `subject=Breakout-watch`), and the `/stocks` leaderboard renders **non-empty**. An empty leaderboard / empty frame is the "frontend can't reach backend" tell — treat it as a HARD verification gap, NOT a pass.

- **Browser (canonical `browser-qa-agent` lane → `reports/phase-goal-mcp-loop-iter-5-ui-test-results.md`, UT-* screenshots).** This canonical lane is the ONLY lane that counts for the terminal verdict; the QA agent's parallel TC-* lane does NOT substitute (iter-4 lesson). Capture all five:
  - **J-01 — `/stocks`:** each leaderboard row's score area shows an evidence badge; Leadership reads **"Proven"**, Entry Quality + Risk read **"Not yet proven"**; assert ≥1 badge present and no score lacks a status.
  - **J-02 — `/stocks/{ticker}`:** open a stock detail, locate a "Proven" badge, expand the proof panel; **scroll the expanded panel into the viewport before capturing** (iter-3 lesson — it renders below the fold); assert the panel shows the out-of-sample test, the control comparison (vs SPY/QQQ/sector ETF/random), and the certified-claim id + registration date.
  - **J-03 — `/stocks` (or detail):** Entry Quality + Risk render **"Not yet proven"** (not a confident number); the signal-less Breakout-watch regime claim lights **no** inline per-stock score badge.
  - **J-04 — Dashboard → `/evidence`:** Dashboard shows the current regime (**Risk-on 76.05/100**) + the **"See evidence proven in this regime →"** affordance; follow it to `/evidence`; **scroll the 2nd row ("Breakout-watch setup", "Regime: Risk-on") into frame before capturing** (iter-3 lesson); assert the row is regime-scoped and labeled, with values byte-matching `GET /api/evidence` line 2 (holdout **+6.12%**, p=0.0004998 < alpha/2=0.025, control **+6.12%** vs SPY, registered **2026-06-30**).
  - **J-05 — `/evidence`:** the claims list renders both rows (leadership_score + Breakout-watch); click a claim and verify the **linkback round-trip** (leadership row "Backs: Stocks leaderboard →" → `/stocks` and back); confirm the new regime row did not break the list.
- **Unit/integration:** re-run and confirm green — backend `apps/backend/tests/test_evidence.py` (incl. `test_build_payload_regime_event_study_claim_adds_no_signal`) and `test_api_evidence.py`; frontend `lib/evidence.test.ts`, `lib/api-base.test.ts`. No code-path regression expected (harness-only change).
- **Harness / error case:** with a stale process deliberately holding `$FRONTEND_PORT`, `scripts/start-frontend.sh` must free it and bind successfully, and the readiness probe must return 2xx serving the current bundle (not the stale one). This is the precise iter-4 failure mode the fix must eliminate.

## NOTES

- **This is a verification-integrity + harness-fix iteration, not a feature delivery.** All five journeys' features are built and gate-certified; the only blockers are the SKIPPED canonical lane and the missing audit handoff. Keep the diff to `scripts/start-frontend.sh` only — any `apps/` change is out of scope and would re-open feature risk.
- **No Evidence Claim → post-decompose gate auto-passes.** Do not add an `## Evidence Claim` block; there is no new "proven" claim this iteration (`docs/goal.md` Loop mechanics: pure verification/navigation iterations need none).
- **Lessons applied (surfaced for developer / browser-qa-agent / evaluator):**
  - *(iter-4)* There are TWO browser lanes and they can disagree: the canonical `browser-qa-agent` (UT-*, `reports/phase-*-ui-test-results.md`) vs the QA agent's own Chrome MCP run (TC-*, `reports/qa/*-qa.md`). Only the **canonical** lane counts for the terminal GOAL_ACHIEVED gate — it must RUN (not SKIP) and render all five.
  - *(iter-2)* `browser_checks_run=false` OR an all-SKIP `ui-test-results.md` is a HARD verification gap — journeys stay `unknown`/`partial`, never `passing`. Confirm frontend↔backend reachability (non-empty leaderboard, `/api/evidence` → 2 claims) before scoring.
  - *(iter-3)* A screenshot proves nothing unless the target element was scrolled into the viewport first — scroll the J-02 proof panel and the J-04 2nd `/evidence` row into frame before capturing.
  - *(iter-1)* A signal is "Proven" only if a PASS certified-claim NAMES it; `proven_signals` stays keyed **only** on `leadership_score`, so Entry Quality + Risk must remain "Not yet proven".
- **ESCALATION / process flag:** the audit stage has stalled at `qa_complete` in iter-3 AND iter-4. The full pipeline MUST reach and complete the auditor this time and write `docs/handoffs/goal-mcp-loop-iter-5-audit.md` — it is a DoD item, not optional.
- On a clean full run — canonical lane renders all five fresh + the audit handoff exists — the iter-4 evaluator's own assessment is that **all five Must-have journeys go green through the session-standard lane and GOAL_ACHIEVED is reachable**.
