# Goal Iteration 3 — Browser-prove the shipped evidence layer (J-01/J-02/J-03/J-05) by fixing the QA bring-up

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 3
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-02, J-05
- **Required-still-passing journeys:** J-01, J-03
- **Evidence Claim:** none (this iteration surfaces NO new "proven" signal — it browser-verifies the already-certified `leadership_score` claim; the post-decompose gate passes automatically)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## GOAL

Make the QA browser lane actually run and prove, with real screenshots, that the already-shipped evidence layer works end-to-end: the Leadership "Proven" badge and its proof drill-down render correctly on `/stocks` + stock detail, the `/evidence` ledger row and its linkback round-trip, while Entry Quality and Risk stay honestly "Not yet proven".

## BACKGROUND

The evidence read-path is fully built, reviewed, unit-tested, coherence-clean, and data-verified: the post-decompose gate certified `leadership_score` (sealed holdout 279 dates, SPY control n=1137, bonferroni, p=0.0004998 < 0.05 → PASS), the ledger entry stamps `signal=leadership_score`, and `GET /api/evidence` serves `proven_signals.leadership_score.proven == true` (curl-verified iter-2 TC-13). **What is missing is browser proof.** In iter-2 the full pipeline's browser lane SKIPPED all 18 UI tests with reason "Frontend not running" (`status.json browser_checks_run: false`), and the lone screenshot showed `/stocks` stuck on "Checking backend…" with an empty leaderboard — an unambiguous frontend↔backend reachability failure in the QA bring-up, **not** a code regression (`next build`, `tsc --noEmit`, backend + frontend units, and the `/api/evidence` curl were all green). Per the iter-2 evaluator recommendation, this iteration **verifies the shipped code — it does NOT rebuild it.** Depth is **full** because the browser-QA lane is the entire deliverable and is most robustly gated by the full pipeline (ui-impact → ui-test-design → browser-qa → ux-regression → closure), and because the lean lane has twice now (iter-0, iter-2) silently lost the browser step.

**Lessons applied (from `lessons.md`):**
- *iter-0:* a missing/empty `ui-test-results` + no `browser-qa-agent` telemetry record means NOTHING was verified — seed `unknown`, never infer pass/fail from a static code scan. DoD below requires a real telemetry record + non-empty evidence dir.
- *iter-1:* a certified ledger row only matters if a PASS actually flips a badge **end-to-end, browser-verified** — the `signal` stamp is already in place; this iteration confirms the flip in pixels.
- *iter-2:* `browser_checks_run: false` OR an all-SKIP `ui-test-results.md` is a **HARD verification gap** — a QA "READY TO SHIP" on build+units+API alone does not count. Before running the browser lane, confirm the frontend can actually reach the backend (service-start order, API base URL, health proxy); an empty-leaderboard / "Checking backend…" frame is the tell, and is a FAIL of the bring-up gate, never a pass.

## IN SCOPE

### Backend (app source)
- [ ] NONE. The evidence read-path (`apps/backend/app/engine/evidence.py`, `apps/backend/app/api/evidence.py`, `apps/backend/app/api/health.py`, `apps/backend/app/engine/ledger.py`, `apps/backend/app/engine/referee.py`) is shipped and serving correct values. Do NOT modify it.

### QA service bring-up (operational — the iter-2 root cause; project QA scripts only, NOT app feature code)
- [ ] **Reproduce the failure the way the harness does:** start services via `scripts/start-backend.sh` + `scripts/start-frontend.sh` (the commands `browser-qa-phase.sh` / `goal-iter-lean.sh` invoke through `ensure_services_running`) and load `http://localhost:<FRONTEND_PORT>/stocks` in a real browser. Determine whether the frontend reaches the backend.
- [ ] **Gate the browser lane on mutual reachability BEFORE tests run:** assert `GET /api/health` → 200 **and** `GET /api/evidence` → `proven_signals.leadership_score.proven == true` from the harness host, **and** that `/stocks` renders ≥1 leaderboard row (not "Checking backend…" / not an empty leaderboard). Only then dispatch the browser-qa-agent.
- [ ] **If a concrete bring-up defect is diagnosed**, apply the MINIMAL fix in the project QA start scripts only — likely candidates: backend not healthy before the frontend is deemed ready (ordering/race), a stale `.next` or a baked-in `NEXT_PUBLIC_API_URL`, a `next dev` cold-compile race exceeding the readiness budget, or port/env propagation. Prefer a deterministic serve (e.g. `next build && next start`) **only** if cold `next dev` compile is the proven flake source. Document the root cause + fix in the dev handoff. Do NOT touch the evidence feature code.

### Frontend (app source)
- [ ] NONE expected. `apps/frontend/lib/api-base.ts:resolveApiBase` already returns the configured base verbatim for a localhost page (rule 3), so a localhost-frontend → localhost-backend QA run needs no code change. Apply a minimal fix ONLY if diagnosis proves an API-base / env-propagation defect, and document it.

### New user-facing capability
None new. This iteration makes an already-built capability **observably true in the browser**: the user can see the Leadership "Proven" badge, drill into its proof, and audit the backing claim on `/evidence`.

### New information displayed
None new. The Leadership proof panel and the populated `/evidence` row already exist in code; this iteration proves they render with values byte-identical to `/api/evidence`.

### New user actions
None new.

### UI surface changes
None new — `/stocks`, `/stocks/{ticker}`, `/evidence` are unchanged. This is verification, not surface work.

### Product surface delta
The product moves from "evidence layer shipped but unverified in the browser" to "evidence layer browser-proven end-to-end" — the difference between a claimed feature and a demonstrated one.

### Blueprint conformance
No new surfaces. All pages touched (`/stocks`, `/stocks/{ticker}`, `/evidence`) already have their canonical home in the Information Architecture (Stocks; Stocks → Stock Detail; Evidence). No nav-skeleton change → no `blueprint.reapproval-requested`.

### Data-contract additions
None. No new displayed value is introduced. The evidence status / certified-claim value (and the three scores, regime, forward-return aggregates) are already registered with their single canonical computing module + serving endpoint (`GET /api/evidence` and the existing score/regime endpoints). This iteration reads those verbatim — it introduces no second computation or fetch. The blueprint is left unchanged.

## OUT OF SCOPE

- **J-04 (regime-conditioned evidence)** — deferred to a later iteration that proposes a narrow, regime-scoped `## Evidence Claim` and earns a referee PASS at the post-decompose gate. There is no regime-scoped certified claim yet, so nothing "proven" exists to show for J-04; surfacing it now would either show an honest "not yet proven" (no journey progress) or risk an uncertified edge. Tackle it next, after the four browser-verifiable journeys are green.
- Any rebuild, refactor, or "improvement" of the shipped evidence feature code (backend or frontend).
- Any new Evidence Claim or any new "proven" signal beyond the already-certified `leadership_score`.
- Any change to the scoring / regime / forward-return / research engines (determinism + no-lookahead invariants must remain untouched).
- Adding evidence badges to `/sectors`, `/themes`, or research labs (J-03 is satisfied on the stock surfaces this iteration; cross-surface expansion is not required to pass the targeted journeys).

## DEFINITION OF DONE

- [ ] `runs/goal-mcp-loop-iter-3/status.json` shows `browser_checks_run: true` (NOT false), and `telemetry.jsonl` contains a `browser-qa-agent` `agent_invocation` record (iter-0 lesson — a missing record = nothing verified).
- [ ] `reports/phase-goal-mcp-loop-iter-3-ui-test-results.md` exists with a non-SKIPPED verdict, and `reports/qa/goal-mcp-loop-iter-3-evidence/` holds ≥1 **real** screenshot per target journey (an empty leaderboard or "Checking backend…" frame does NOT count).
- [ ] **J-02 browser-verified:** `/stocks` → click a stock → expand "Why proven?" on the Leadership card → the panel shows the OOS test (PASS, holdout edge +6.36%, p≈0.0005, cohort n=12297), the "vs SPY (benchmark control)" excess, and the claim id + "registered 2026-06-30" — **byte-identical to `GET /api/evidence`**.
- [ ] **J-05 browser-verified:** `/evidence` renders the populated `leadership_score` claim row with all five fields (hypothesis, OOS verdict, SPY control, registration date, forward-walk score-to-date); the "Backs: Stocks leaderboard →" linkback round-trips; and the leaderboard "Proven" badge links to `/evidence#signal-leadership_score`.
- [ ] **J-01 re-confirmed (fresh capture):** every `/stocks` leaderboard row shows an evidence status; Leadership reads "Proven"; no displayed score lacks a status.
- [ ] **J-03 re-confirmed (fresh capture):** Entry Quality and Risk read "Not yet proven" (muted) on `/stocks` and stock detail, with no "Why proven?" toggle on those two cards.
- [ ] Displayed numbers match `/api/evidence` (and the engine) for the same as-of date — anti-goal #3 (correctness, not mere rendering).
- [ ] No anti-goal violation introduced; no return/price/buy-sell/alpha language on any proof surface; secret scan clean; determinism/no-lookahead untouched.
- [ ] Backend + frontend unit suites pass; no regression; no source diff to the evidence feature code (any diff is confined to QA bring-up scripts and is justified in the handoff).
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-3-dev.md`, stating the diagnosed bring-up root cause and the exact fix (or explicitly "no code change needed — verification-only").

## TESTING REQUIREMENTS

- **Browser:** J-01, J-02, J-03, J-05. Reuse the iter-2 UI test plan (UT-01..UT-18 already enumerate exactly these flows). Capture real screenshots; treat `browser_checks_run: false`, any all-SKIP result, an empty leaderboard, or a "Checking backend…" frame as a **hard FAIL of the bring-up gate**, never a pass.
- **Pre-flight (must pass before the browser lane):** `curl /api/health` → 200; `curl /api/evidence` → `proven_signals.leadership_score.proven == true`; `/stocks` renders ≥1 row. Use the same default as-of date iter-1 verified against (it rendered 120 leaderboard rows), so once connectivity is restored the leaderboard is populated.
- **Unit/integration:** re-run backend `pytest` (incl. `tests/test_evidence.py`) and frontend `lib/evidence.test.ts` + `lib/api-base.test.ts`; all green. No new unit coverage is required for operational bring-up scripts, but the dev must demonstrate both services boot and are mutually reachable.
- **Error cases / invariants to NOT regress:** empty/absent ledger still returns 200 with `{"claims": [], "proven_signals": {}}` (never 500); a backend-down state must still render the honest health badge ("Backend unavailable…", nothing fabricated as Ready — the J-40 invariant), never a faked "Ready".

## NOTES

- **Verify, do not rebuild.** Per the iter-2 evaluator: the dev work is reviewed, unit-tested, coherence-clean, and the certified claim is already in the ledger. The failure was operational (QA bring-up), so the smallest correct change set is likely just the bring-up gate — possibly **zero app-source diff**. That is an acceptable and expected outcome; the value of this iteration is a green, evidence-backed browser lane.
- **Why "Frontend not running" yet the shell renders "Checking backend…":** the symptom set (skip reason "Frontend not running" + a shell that renders but never resolves health + empty leaderboard / "No regime for this date" / "No ranked themes for this date") points to backend-unreachable-from-the-browser during the test window — a service-start ordering / readiness / env-propagation race in the harness, not app code. A prior session already fixed a LAN-IP variant of this class (host-aware `resolveApiBase` + dev CORS, J-40/J-108); the localhost QA path should not need that, so confirm the localhost case specifically.
- **No Evidence Claim is intentional.** This iteration presents no new signal as "Proven" — it verifies the already-certified `leadership_score`. The post-decompose gate should pass with no claim block. Do not add one.
- **Path forward:** once J-01/J-02/J-03/J-05 are browser-proven here, only J-04 remains, and the next iteration can propose a narrow regime-conditioned Evidence Claim for it — after which GOAL_ACHIEVED becomes reachable.
- **Required-still-passing = full-regression refresh this iteration.** J-01 and J-03 are currently "passing" on stale iter-1 evidence (never re-verified in iter-2 because the browser lane skipped), so they are re-captured FRESH in this run rather than replayed — there are no trustworthy golden scripts since the lane last succeeded in iter-1, and this run re-establishes them.
