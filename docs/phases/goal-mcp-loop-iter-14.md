# Goal Iteration 14 — Clean browser-verification of J-08 (combination "Proven" badge + Evidence row) → GOAL_ACHIEVED gate

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 14
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-08
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07
- **Anti-goal reminders:**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## GOAL

Deliver a clean, backend-up browser verification that the already-shipped J-08 capability works end-to-end — the `/research/factor-combination` composite "Proven" badge for `rs_spy_3m:top:quintile × high_proximity:top:tertile @ h20` renders "Proven" and deep-links to its backing 6th `/evidence` combination row — flipping J-08 from `partial` to `passing` and opening the terminal GOAL_ACHIEVED gate.

## BACKGROUND

iter-13 landed the terminal J-08 basis **correctly at the data/logic layer** — a genuine, honest 6th canonical PASS row (byte-exact `git diff` = exactly one appended line, `p=0.0009995 < required_p=0.008333` at Bonferroni divisor 6, ~8x margin), served `proven=true`/`signal=null` through the existing `GET /api/evidence`, with a pure read-side resolver (37/37 unit tests) and COHERENCE-PASS. But the **browser verification was unclean**: the canonical browser-qa lane returned overall **FAIL** (UT-05/UT-14 — the `/evidence` deep-link anchor did not scroll the combination row into the viewport), phase-closure returned **CLOSURE-FAIL**, the backend dropped mid-run (a red "Backend unavailable" pill appeared on the `/evidence` captures), and the claimed "Proven"-badge screenshot was a relabeled **default-state** frame that actually showed the FAILED `atr_pct` pair reading "Not yet proven". The iter-13 audit's hash-scroll fix to `apps/frontend/app/evidence/page.tsx` was applied *after* that browser run and is now **committed at HEAD** (verified: `useEffect` L57-63 `scrollIntoView`s the URL-hash row after the async fetch). This iteration is **verification-only** — no new feature code, no new Evidence Claim — per the iter-13 evaluator's explicit LEAN recommendation: bring the stack up, hold the backend up for the whole run, re-run the canonical browser-qa lane against the committed fix, and capture md5-distinct, correctly-labeled, scrolled-into-frame screenshots. J-08 is the SOLE remaining Must-have journey.

## IN SCOPE

### Backend
- [ ] **No code change.** Read-only verification: confirm `GET /api/evidence` (backend `:8255`) serves exactly **6 claims** with the combination row (`kind=combination`, `condition=[rs_spy_3m:top:quintile, high_proximity:top:tertile]`, `horizon=20`) reading `proven=true` / `signal=null`, `holdout_edge≈0.046932`, `p_value=0.0009995`. The backend MUST stay up for the entire browser run. `certified-claims.jsonl` MUST remain byte-identical (6 rows).

### Frontend
- [ ] **No code change by default.** The iter-13 audit's committed hash-scroll fix (`apps/frontend/app/evidence/page.tsx` — the `useEffect` that scrolls the URL-hash row into view after the async fetch resolves) is the mechanism under test; it is already at HEAD.
- [ ] **Contingency ONLY (do not pre-emptively edit):** if — and only if — the browser-qa re-run demonstrates the deep-link still does not land the combination row in the viewport, apply a **minimal additive read-side scroll/anchor correction** so the badge `href` anchor (`combination-high_proximity-rs_spy_3m-h20`) and the `/evidence` combination row `id` align and scroll cleanly. No new "proven" claim, no new endpoint, no data-contract change, no nav change.

### New user-facing capability
None built. This iteration **proves** the already-shipped J-08 capability: selecting `rs_spy_3m:top:quintile × high_proximity:top:tertile @ h20` on `/research/factor-combination` shows a "Proven" badge that deep-links to the backing 6th `/evidence` combination row.

### New information displayed
None (re-verification of already-shipped surfaces).

### New user actions
None.

### UI surface changes
None (re-verification of `/research/factor-combination` + `/evidence`).

### Product surface delta
None — this closes verification debt on the terminal journey; the product itself does not change.

### Blueprint conformance
No new surfaces. Both surfaces are already registered homes in `blueprint.md`: `/evidence` (J-05 home, Evidence [NEW] nav section, 1 click) and `/research/factor-combination` (J-08 home, Research section, link-reached, 2 clicks). The evidence-status contract value and the combination reader (`resolveCombinationEvidence`, `combinationClaimId`) were registered in the iter-13 clarification. **No blueprint edit required** and no nav-skeleton change.

### Data-contract additions
None. This iteration introduces NO new displayed value and NO new Evidence Claim — it reads the EXISTING "Evidence status + certified-claim" value (the 6th `certified-claims.jsonl` row) from the EXISTING `GET /api/evidence`. **Do NOT add an `## Evidence Claim` block:** the combination claim already landed as the 6th canonical row in iter-13; re-certifying would duplicate the row and permanently tighten the canonical Bonferroni bar to divisor 7 (a documented footgun — see lessons iter-10/iter-12).

## OUT OF SCOPE

- Any new `## Evidence Claim` / referee run (the claim already landed; re-running duplicates the row and tightens the bar).
- Any backend/ledger/engine change; any change to `certified-claims.jsonl` (must stay byte-identical, 6 rows).
- Any new factor/combination cohort, page, endpoint, or nav change.
- Any `/stocks` inline-badge change — the signal-less combination MUST NOT light a `/stocks` badge (`proven_signals` stays `{leadership_score}`).
- Broad "fix the product-wide deep-link scroll everywhere" work — this iteration only confirms the combination deep-link lands and that J-01..J-07 remain green; unrelated surfaces are not re-engineered unless a regression surfaces.

## DEFINITION OF DONE

- [ ] Target journey **J-08 passes** via the canonical browser-qa-agent lane: the `/research/factor-combination` composite "Proven" badge for `rs_spy_3m:top:quintile × high_proximity:top:tertile @ h20` renders **"Proven"** (`data-proven=true`) and deep-links to `/evidence#combination-high_proximity-rs_spy_3m-h20`; the 6th `/evidence` combination row scrolls into the viewport on that deep-link and renders the standard fields.
- [ ] Backend `:8255` stayed up for the **entire** run — **NO "Backend unavailable" pill** in any capture; `GET /api/evidence` returns 6 claims both before and after the browser flow.
- [ ] Screenshots are **md5-DISTINCT** and **correctly labeled**: (a) a frame that ACTUALLY shows the composite "Proven" badge for the `rs_spy_3m × high_proximity` selection scrolled into view — NOT the default `atr_pct` "Not yet proven" frame; (b) a frame showing the 6th `/evidence` combination row scrolled into view. The browser-qa agent md5sums its own PNGs and confirms no two asserted-state captures share a hash and none is a page-top/"Backend unavailable" frame.
- [ ] Honest marking holds (J-03 / anti-goal #1): the DEFAULT `rs_spy_3m × atr_pct` composite and every non-certified combination read **"Not yet proven"**.
- [ ] Displayed numbers byte-match the ledger (anti-goal #3): edge **+4.69%** (`0.046931…`), control vs SPY **+4.69%**, `p=0.0009995`, register date `2026-07-01`, divisor 6 — never a UI recompute.
- [ ] Required-still-passing journeys **J-01..J-07 remain green** (full regression this terminal iteration).
- [ ] No anti-goal violation introduced; `certified-claims.jsonl` byte-identical (6 rows); `proven_signals` stays `{leadership_score}`.
- [ ] Unit tests pass; no regressions (37/37 evidence unit tests; the `resolveCombinationEvidence`/`combinationClaimId`/`claimAnchorId` expectation tests are UNEDITED and green).
- [ ] A **PASS** `ui-test-results` is written by the browser-qa lane so the goal-evaluator can flip J-08 to `passing`.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-14-dev.md`.

## TESTING REQUIREMENTS

**Operational preconditions (HARD — the iter-2/iter-4 lesson):** free `:3255` before binding the frontend; start backend `:8255` and frontend `:3255`; confirm the frontend can reach the backend (`GET /api/evidence` → 200 with 6 claims) BEFORE the browser flow AND keep the backend up for the whole run. A single "Backend unavailable" pill or empty frame invalidates a fail-safe "Not yet proven" reading and voids the verification.

**Browser (canonical `browser-qa-agent` lane) — J-08 primary flow:**
1. Precondition curl: `GET /api/evidence` → assert 6 claims; the combination row `proven=true`, `signal=null`, `holdout_edge≈0.046932`, `p_value=0.0009995`.
2. Navigate to `/research/factor-combination`; assert the page loads with NO red "Backend unavailable" pill.
3. **Default (honest-marking) check:** observe the default composite (leg 2 = `atr_pct`); assert `combination-evidence-badge` has `data-proven=false` and reads "Not yet proven". Capture a DISTINCT default-state frame.
4. **Compose the certified selection:** keep leg 1 (`condition-factor-0`) = `rs_spy_3m`, side top, quantile `top:quintile`; set leg 2 (`condition-factor-1`) = `high_proximity`, side top, quantile (`condition-quantile-1`) = `top:tertile`; set `horizon-select` = 20.
5. **Proven badge:** assert `combination-evidence-badge` now has `data-proven=true`, `data-legs` contains both `rs_spy_3m` and `high_proximity`, and reads "Proven". **Scroll the badge into the viewport, THEN capture** — the frame must actually show "Proven" for THIS selection (not the default `atr_pct` frame). md5-distinct.
6. **Deep-link:** click the "Proven" badge → navigates to `/evidence#combination-high_proximity-rs_spy_3m-h20`.
7. **Evidence row lands:** on `/evidence`, assert the 6th combination `ClaimRow` **scrolls into the viewport** (the committed hash-scroll fix — UT-05/UT-14) and renders the standard fields: hypothesis incl. the two legs + horizon 20, out-of-sample verdict PASS, control vs SPY +4.69%, register date 2026-07-01, forward-walk score-to-date, and a "Backs: Multi-factor combination lab →" linkback. **Scroll into frame, THEN capture.** md5-distinct.
8. **Byte-match (anti-goal #3):** the displayed +4.69% edge and `p=0.0009995` match the ledger verdict for the same as-of.

**Browser — J-01..J-07 regression (full re-verify, terminal gate):**
- J-01: `/stocks` — every leaderboard row shows an evidence badge; `proven_signals={leadership_score}`; **0** `combination-evidence-badge` elements on `/stocks` (no leakage).
- J-02: `/stocks/{ticker}` — the `leadership_score` proof drill reads the canonical `/api/evidence` payload; **0** combination-badge leakage.
- J-03: default combination + any non-certified combination read "Not yet proven".
- J-04: the event-study regime-scoped row renders on `/evidence` ("Regime: <label>").
- J-05: the `/evidence` ledger lists 6 rows, each with the standard fields.
- J-06: `vcp_contraction` D10 **h20** row + factor-lab "Proven" badge.
- J-07: `vcp_contraction` D10 **h60** (non-20) row + factor-lab per-horizon badge.

**Unit/integration:** the existing evidence unit suite (`resolveCombinationEvidence`, `combinationClaimId`, `claimAnchorId`, `combinationCohortFromClaim`) stays green (37/37); the expectation tests MUST be UNEDITED (an edited expectation test would itself be a regression signal — lesson iter-9).

**Error / honest-status cases:** the default `atr_pct` pair and every non-pre-registered combination read "Not yet proven"; the signal-less combination lights no `/stocks` inline score badge.

**Screenshot hygiene (HARD — 5th-recurrence guard):** md5sum every evidence PNG; the three asserted-state captures (default "Not yet proven", composite "Proven", 6th `/evidence` row) must be mutually distinct, each scrolled into frame, correctly labeled, and none a page-top or "Backend unavailable" frame. Do NOT trust a PASS label or a DOM-text assertion alone for the terminal gate — open the actual "Proven" frame and confirm the CERTIFIED selection is composed in-frame.

## NOTES

**Lessons applied (episodic memory — surfaced for developer / browser-qa / evaluator):**
- **iter-13:** a fix applied AFTER the browser-qa run does NOT count toward journey verification until a browser-qa RE-RUN follows — **iter-14 IS that re-run**. For a terminal GOAL gate, open the actual claimed-"Proven" screenshot and confirm the certified selection is composed in-frame; do not trust the PASS label or the DOM-text line. A "Backend unavailable" pill on an `/evidence` capture invalidates a fail-safe "Not yet proven" reading.
- **iter-11:** always `md5sum` the evidence PNGs — a screenshot referenced by N test ids can be one reused capture. Do NOT trust an auditor's "screenshots show X" claim without spot-checking pixels. When pixels are weak, ground the pass in the DOM assertions + the byte-exact ledger + green unit tests.
- **iter-3:** scroll the target element into the viewport BEFORE capturing any below-the-fold / disclosure / deep-link element — a frame named for an element that only shows the page header proves nothing.
- **iter-2 / iter-4:** confirm the frontend can actually reach the backend and keep it up for the whole run; free `:3255` before the browser-qa lane binds; a QA-parallel-lane PASS does NOT substitute for the canonical `ui-test-results.md` on the terminal gate.
- **iter-10 / iter-12:** do NOT re-submit any Evidence Claim this iteration — a canonical claim permanently tightens the Bonferroni bar and a duplicate would violate coherence.

**Grounding — deep-link anchor & selectors:** the combination badge `href` resolves via `combinationClaimId` = `combination-<sorted factor keys>-h<horizon>` = `combination-high_proximity-rs_spy_3m-h20`; the `/evidence` combination `ClaimRow` carries the SAME `id`, and `apps/frontend/app/evidence/page.tsx`'s hash `useEffect` scrolls it into view. Combination-lab selectors: `condition-factor-{idx}`, `condition-side-{idx}`, `condition-quantile-{idx}`, `horizon-select`, `combination-evidence-badge` (`data-proven` / `data-legs`). The config-default leg 2 is the FAILED `atr_pct` pair — the browser-qa MUST actively set leg 2 to `high_proximity:top:tertile` to reach the "Proven" state.

**Terminal gate & escalation path:** J-08 is the SOLE remaining Must-have journey. On a clean re-run with J-01..J-07 non-regressed, GOAL_ACHIEVED becomes declarable by the goal-evaluator. Depth is **lean** per the prior evaluator's explicit recommendation. If the lean browser-qa re-run cannot cleanly verify J-08 (e.g. the committed hash-scroll fix proves insufficient AND the contingency read-side correction is non-trivial), the iteration should **ESCALATE to full** so the phase-closure gate re-runs before the terminal GOAL_ACHIEVED judgment — do not force full up front.
