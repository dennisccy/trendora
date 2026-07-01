# Goal Iteration 13 — Surface J-08: multi-factor combination certified edge on the Combination lab + Evidence

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 13
- **Mode:** next  (non-baseline / normal iteration)
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-08
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## GOAL

Surface J-08: promote the pre-registered 2-factor combination staging winner to the canonical evidence ledger and render its "Proven" evidence status on the Multi-factor combination lab composite cohort and as a new claim row on `/evidence` — both reading the same `GET /api/evidence` payload verbatim.

## Evidence Claim

<!-- GATE-CRITICAL: the post-decompose gate certifies this claim through the referee BEFORE any code is built.
     Selectors byte-match the recorded staging PASS (staging-ledger.jsonl entry #7); `"ledger":"canonical"` is
     REQUIRED and explicit (an omitted key silently re-stages and never surfaces — iter-9b/iter-10/iter-12 lesson).
     A non-PASS verdict (FAIL/INSUFFICIENT) BLOCKS the iteration — do NOT force a promotion (honest-stop guard). -->

```json
{"kind": "combination", "cohort": "composite", "horizon": 20, "direction": "positive", "condition": ["rs_spy_3m:top:quintile", "high_proximity:top:tertile"], "ledger": "canonical"}
```

## BACKGROUND

iter-12 (discovery/enablement, backend-only) landed the recorded staging basis J-08 needs: a FIXED pre-registered 3-pair 2-factor combination candidate set was certified through the unchanged referee into the internal staging ledger. I independently verified the recorded winner against `staging-ledger.jsonl` line 7 (the iter-12 lesson: never trust a prior evaluator's "the basis exists" — grep the ledger): `rs_spy_3m:top:quintile` × `high_proximity:top:tertile`, composite cohort, h20, **status PASS**, recorded block-bootstrap `p_value` = 0.0009995, `holdout_edge` = +4.69% beating SPY out-of-sample. Promoting it appends the 6th canonical entry, which faces Bonferroni divisor 6 (required_p = 0.05/6 = 0.008333); the recorded p clears it with ~8x margin, so this is a safe promotion — NOT the iter-8 `ma_stack` bar-tightening disaster (whose recorded p 0.0195 did not clear its bar) and NOT a p-floor-saturated outsized-edge yellow flag (iter-10 lesson): p=0.0009995 sits just above the block-bootstrap floor and the +4.69% edge is modest and credible. J-08 is the SOLE remaining Must-have journey; landing it browser-verified with J-01..J-07 non-regressed makes GOAL_ACHIEVED reachable. Depth is FULL: this crosses the certification/ledger layer + frontend, touches the shared evidence-status contract value (a new canonical entry that permanently tightens the bar), needs new unit tests beyond a browser smoke, and is the terminal GOAL gate.

Applied lessons (episodic memory): iter-9b/iter-10/iter-12 — the promotion claim MUST set `"ledger":"canonical"` explicitly (done above); iter-8 — a `kind=combination` claim is signal-less (`_resolve_signal` returns `None`), so it must NOT carry a `signal` key and must NEVER light a `/stocks` inline badge; iter-3/iter-11 — browser-QA must scroll each asserted badge/row into the viewport and capture md5-DISTINCT screenshots (do not accept one relabeled full-page frame); iter-2/iter-4/iter-5/iter-6 — before trusting the browser lane, confirm the frontend can reach the backend and free the frontend port; if a verification artifact is missing, read `engine.log` for where the pipeline actually died.

## IN SCOPE

### Backend
- [ ] No application code change is expected. The 6th canonical ledger entry is written by the **post-decompose gate** running the `## Evidence Claim` above through the referee (`verify_edge(ledger="canonical")`) — the developer does NOT hand-write `certified-claims.jsonl`. `app.engine.evidence:build_evidence_payload` already re-displays any ledger row into `claims[]` verbatim and `_resolve_signal` already returns `None` for `kind=combination`, so the new combination row flows into `GET /api/evidence` automatically with `signal: null, proven: true`. If any backend edit turns out necessary, it must be additive and must NOT alter the referee, `verify_edge`, `evidence.py`, `api/evidence.py`, or the existing 5 canonical entries (all must stay byte-identical / git-unmodified except the single appended row).

### Frontend
- [ ] `lib/evidence.ts` (pure, unit-testable, no React/fetch): add a `CombinationCohort` type (`kind:combination`, `cohort:composite`, `condition[]`, `horizon`, `direction`), a `combinationCohortFromClaim(claim)` extractor (sibling of `factorCohortFromClaim`), and a `resolveCombinationEvidence(cohort, claims)` matcher (sibling of `resolveCohortEvidence`) that scans the served `claims[]` for a PASS entry matching on `kind=combination` + `cohort=composite` + the `condition` **leg-set (order-independent)** + `horizon` + `direction`, returning "Proven" (+ the backing row's `/evidence#…` anchor) only for a PASS match, else "Not yet proven" with no link. Never recompute proven-ness.
- [ ] `lib/evidence.ts`: add a deterministic, collision-free combination anchor id (sibling of `cohortClaimId`, derived from the **sorted** condition legs + horizon, e.g. `combination-high_proximity-rs_spy_3m-h20`), and extend `claimAnchorId` to return it for a combination claim so the `/evidence` row carries a deep-linkable `id`.
- [ ] `lib/evidence.ts`: extend `claimSurface` with a `combination` branch — an honest composite title naming the two legs, a historical-evidence subtitle (never a return/buy-sell promise), and a `href:"/research/factor-combination"` + label `Multi-factor combination lab` "Backs:" linkback (replacing the misleading "Unmapped signal" fallback for this claim).
- [ ] `app/research/factor-combination` (via `_labs.tsx` `CombinationSection`, `combination-row-composite`): attach an evidence badge to the composite cohort row that reads the SAME `GET /api/evidence` payload (existing `fetchEvidence` / `claims[]` — no new fetch path) and resolves status via `resolveCombinationEvidence` for the currently-selected composite conditions + the lab's selected horizon. Show "Proven" (deep-linking to the `/evidence` combination row) ONLY when the selection matches the certified cohort; every other combination reads "Not yet proven".
- [ ] `app/evidence/page.tsx` (`ClaimRow`): no structural change beyond what the `lib/evidence.ts` `claimSurface`/`claimAnchorId` combination branch enables — the combination claim row must render the standard five fields verbatim (Hypothesis chips already show `condition=[...]`, `kind`, `horizon`, `direction`), the honest combination title + "Backs: Multi-factor combination lab →" linkback, and the deterministic combination anchor `id`.

### New user-facing capability
The user can see that a specific, pre-registered 2-factor combination (relative-strength leaders that are also near their 52-week high) has been referee-certified out-of-sample, read its evidence on the Multi-factor combination lab as a "Proven" badge, click through to its ledger row on `/evidence`, and confirm every other (uncertified) combination they compose honestly reads "Not yet proven".

### New information displayed
A 6th certified-claims row on `/evidence` for the `rs_spy_3m × high_proximity` composite @ horizon 20 (hypothesis incl. the two `condition` legs + horizon, out-of-sample verdict + holdout edge ≈ +4.69%, control comparison vs SPY, registration date, forward-walk score-to-date, "Backs: Multi-factor combination lab →"), and a "Proven" / "Not yet proven" evidence badge on the combination lab's composite cohort row.

### New user actions
Click the composite-cohort "Proven" badge on `/research/factor-combination` to deep-link to its backing `/evidence` row; compose a different 2-factor combination and observe the badge honestly flip to "Not yet proven".

### UI surface changes
`/research/factor-combination` composite cohort row gains an inline evidence badge; `/evidence` gains one combination claim row. No new page, no new route.

### Product surface delta
The evidence layer now proves a *composite* (multi-factor) edge, not just single-factor / single-horizon ones — the combination lab stops being purely descriptive and gains an honest, referee-gated "Proven" status on exactly one certified composite, closing the last Must-have journey.

### Blueprint conformance
J-08's canonical homes — `/research/factor-combination` (composite badge) and `/evidence` (claim row) — are already registered in the blueprint Information Architecture (the J-08 feature/journey-home row). Both routes already exist. No nav-skeleton change; no new top-level section; no `blueprint.reapproval-requested`.

### Data-contract additions
None — no new displayed value. This surfaces the EXISTING single canonical value (**Evidence status + certified-claim**, row 1 of the Data Contract) computed once by the referee (`certify_edge` via `verify_edge`) and served once by `GET /api/evidence`. The combination claim is a NEW ENTRY in the EXISTING `certified-claims.jsonl`; the combination-lab badge and the `/evidence` combination row are additional READERS of that same payload (no new computing module, no new serving endpoint, no second computation). The `blueprint.md` Data Contract gains an additive **iter-13 clarification** paragraph documenting this reader (already written this iteration).

## OUT OF SCOPE

- Any change to the referee, `verify_edge`, `online_fdr`, `evidence.py`, `api/evidence.py`, or the existing 5 canonical ledger entries (must stay byte-identical — only the single new row is appended by the gate).
- Any `/stocks`, `/stocks/{ticker}`, `/sectors`, `/themes`, or Dashboard inline-badge change — a signal-less combination claim backs NONE of them; `proven_signals` must stay exactly `{leadership_score}`.
- Adding a `signal` key to the combination Evidence Claim (it is signal-less by design — adding one would wrongly attempt to light a per-stock score badge).
- Promoting or exploring any OTHER combination/horizon, quantile spreads (D10−D1), regime conditioning, or sector cohorts (deferred per goal.md Part B "later phases").
- Re-proposing any closed FAIL hypothesis (`ma_stack`, `hv`, `high_proximity` single-factor, or the two FAILed anchor combinations `rs_spy_3m+atr_pct`, `leadership_score+atr_pct`) — each failed submission permanently tightens the Bonferroni bar.

## DEFINITION OF DONE

- [ ] The post-decompose gate certifies the `## Evidence Claim` as **PASS** (canonical, Bonferroni divisor 6, required_p ≈ 0.00833) and appends exactly one row to `certified-claims.jsonl` (now 6 entries; prior 5 byte-identical). Honest-stop guard: if the gate returns FAIL/INSUFFICIENT, the iteration is BLOCKED — report it, do NOT force the promotion.
- [ ] Target journey J-08 passes via browser-qa-agent: the `/evidence` combination row renders with correct verbatim fields, and the `/research/factor-combination` composite cohort shows a "Proven" badge for the certified selection that deep-links to that row, while a different combination reads "Not yet proven".
- [ ] Required-still-passing journeys J-01..J-07 remain green (regression set below); `proven_signals` stays `{leadership_score}`; the existing 5 canonical rows are unchanged.
- [ ] No anti-goal violation introduced (all seven upheld; combination stays signal-less; no return/price/buy-sell language; displayed numbers byte-match the referee verdict).
- [ ] Unit tests pass; no regressions in the existing `lib/evidence.test.ts` factor/event-study/score matchers or backend default-path suites.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-13-dev.md`.

## TESTING REQUIREMENTS

- **Browser (canonical `browser-qa-agent` lane):**
  - J-08 — `/evidence`: the combination claim row renders (scroll it into the viewport before capturing) with hypothesis chips showing the two `condition` legs + `horizon=20` + `kind=combination`, the PASS verdict + holdout edge, control vs SPY, registration date, and the "Backs: Multi-factor combination lab →" linkback.
  - J-08 — `/research/factor-combination`: the composite cohort row shows "Proven" for the certified `rs_spy_3m × high_proximity` selection (scroll into view; capture) and the badge deep-links to the `/evidence` combination row; compose a different combination and assert the badge reads "Not yet proven".
  - Re-verify J-01/J-02/J-03 on `/stocks` + `/stocks/{ticker}`: inline score badges unchanged (no combination leakage; `proven_signals` = `{leadership_score}`).
  - Re-verify J-05/J-04/J-06/J-07 on `/evidence` + `/research/factor-lab`: the existing 5 rows and the factor-lab per-horizon badges are unchanged; the combination row is additive.
  - **HARD requirement (iter-3/iter-11 recurring lesson):** every asserted badge/row must be scrolled into the viewport before the screenshot; md5-check that the captured PNGs are DISTINCT (not one relabeled full-page frame). Before running, confirm the frontend can reach the backend and the frontend port is free (iter-2/iter-4/iter-5).
- **Unit/integration:**
  - `lib/evidence.test.ts`: `resolveCombinationEvidence` returns "Proven" + the correct anchor for the certified cohort (order-independent legs), and "Not yet proven" for a non-matching combination, a matched-but-non-PASS entry, and an empty/null list; `combinationCohortFromClaim` extracts/rejects correctly; `claimAnchorId`/`claimSurface` combination branch (title, linkback to `/research/factor-combination`, deterministic anchor distinct from any factor anchor).
  - Backend: assert `GET /api/evidence` now includes the combination row with `signal: null`, `proven: true`, and verdict fields byte-matching the ledger entry (no UI/endpoint recompute); assert it is ABSENT from `proven_signals` (`_resolve_signal` → `None`); existing referee/evidence default-path tests stay green and unedited.
- **Error cases:**
  - A combination selection that does not match the certified cohort (different legs, different horizon, or the `direction` reversed) must resolve to "Not yet proven" with no link.
  - A matched combination whose ledger verdict is not PASS must stay "Not yet proven" (proven-ness flows only from `verdict.status == PASS`).

## NOTES

- Regression set rationale: this iteration edits the shared `lib/evidence.ts` (every evidence reader depends on it) and the `/evidence` `ClaimRow` (which renders the J-04/J-05/J-06/J-07 rows), and this is the terminal GOAL_ACHIEVED gate — so the full J-01..J-07 regression is warranted (also refreshes the golden replay scripts / catches selector drift per the periodic-full-pass guidance).
- The J-08 acceptance also expects a `[NEW]`-flagged demo-narrator walkthrough of the combination row + composite badge (viewable via `demo.sh mcp-loop --session-live`). The demo-narrator runs in the full pipeline and is non-gating (showcase, never halts) — produce it, but it does not block J-08.
- GOAL_ACHIEVED is the evaluator's call, not this spec's: once J-08 lands browser-verified with J-01..J-07 non-regressed and coherence COHERENCE-PASS, the evaluator may declare it.
