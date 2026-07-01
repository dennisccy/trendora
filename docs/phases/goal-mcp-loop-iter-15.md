# Goal Iteration 15 — Surface the rs_spy_3m 60-day certified edge on the factor lab + Evidence (J-09)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 15
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-09
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## Evidence Claim

<!-- REQUIRED by goal.md "Loop mechanics": the post-decompose gate certifies this cohort through the
     referee (sealed out-of-sample holdout + SPY control + multiple-testing deflation at the canonical
     Bonferroni divisor) BEFORE any code is built. `"ledger":"canonical"` is EXPLICIT and load-bearing:
     an omitted key silently re-certifies the winner into the INTERNAL staging ledger and it would never
     surface on /evidence or the factor lab (iter-9b / iter-10 lesson). This promotes the pre-registered
     multi-horizon staging winner (project-extensions/proposer-guidance.md §4.1 #3; recorded staging PASS,
     block-bootstrap p=0.00049975, holdout +0.2134) — NOT an ad-hoc data-mined slice. A non-PASS verdict
     (FAIL/INSUFFICIENT) BLOCKS the iteration — that is the correct, honest outcome; do NOT force it. -->

```json
{"kind": "factor", "factor": "rs_spy_3m", "slice_kind": "decile", "decile": 10, "horizon": 60, "direction": "positive", "ledger": "canonical"}
```

## GOAL

Surface a 7th referee-certified canonical edge — the pre-registered relative-strength (`rs_spy_3m`) top-decile **60-day-horizon** factor claim — as a "Proven" badge on the Research factor lab and a new row on the Evidence ledger, while leaving every `/stocks` inline score badge unchanged (the claim is signal-less).

## BACKGROUND

The prior verdict was **GOAL_ACHIEVED** (iter-14): all Must-haves J-01..J-08 pass. The continuous-improvement proposer then appended a new journey **J-09** to the `AUTO:journeys` block — promote the pre-registered §4.1 #3 staging winner (`rs_spy_3m` D10 @ h60) to the canonical ledger and surface it, exactly as J-07 surfaced `vcp_contraction` h60. This is **depth: full** because it writes a **permanent canonical ledger row that tightens the user-facing Bonferroni divisor 6 → 7 forever**, and the chosen candidate carries a documented **yellow flag** — its holdout edge of **+0.2134 is implausibly large** and was flagged by the iter-10 auditor (B3); a p-floor PASS with an outsized edge is something the coherence-auditor **and** the phase auditor must scrutinize (the auditor + closure + ux-regression gates run only in the full pipeline, and they are exactly the guards that caught the iter-13 CLOSURE-FAIL). Verified preconditions: the staging verdict EXISTS (staging-ledger row 3: PASS, p=0.00049975, edge +0.2134), that recorded raw p clears the new divisor-7 bar (`required_p = 0.05/7 ≈ 0.007143`) by ~14×, and `rs_spy_3m` is already a selectable factor-lab factor (`config.yaml:806`) whose per-horizon cohort rows currently read "Not yet proven". The read-side machinery is fully general and already built by J-07 (`resolveCohortEvidence` resolves each horizon in `[1,5,10,20,60]`; `cohortClaimId → factor-rs_spy_3m-d10-h60`), so this iteration is near-zero application code and high verification rigor.

## IN SCOPE

### Certification (pre-build gate — not developer code)
- [ ] The post-decompose gate certifies the `## Evidence Claim` above through the referee at the **canonical** ledger (strict Bonferroni, divisor 7) and appends the **7th** entry to `runs/goal-session-mcp-loop/state/certified-claims.jsonl` with `status: PASS`, `deflation: "bonferroni"`, `deflation_divisor: 7`, `required_p ≈ 0.007143`. The gate is the ONLY writer — no hand-editing of the ledger.
- [ ] **Honest-stop guard:** if the gate returns a non-PASS verdict, the iteration BLOCKS (`exit 3`). Report it and stop — do NOT re-submit, re-slice, tweak the cohort, or append a FAIL to force a pass (a canonical FAIL permanently tightens the bar — the iter-8 `ma_stack` disaster).

### Backend
- [ ] No engine/referee/ledger/config source change. `app/engine/{referee,ledger,forward_walk}.py`, `app/mcp/tools.py:verify_edge`, and `app/engine/evidence.py` stay **byte-identical**; the referee/ledger expectation tests stay **UNEDITED** and green (an unedited passing suite is the "defaults reproduce" proof — iter-9 lesson).

### Frontend
- [ ] No frontend source change expected. The existing general per-horizon `resolveCohortEvidence` matcher + the `/evidence` `ClaimRow` `factor` branch surface the new row automatically once the ledger has the 7th entry. Verification-only: confirm the `rs_spy_3m` factor-lab **h60** cohort now reads "Proven" and deep-links to `/evidence#factor-rs_spy_3m-d10-h60`, while its **h1/h5/h10/h20** cohorts still read "Not yet proven". (If — and only if — a real gap is found, keep any change surgical and re-run the browser lane after it.)

### New user-facing capability
The user can see that the platform's 3-month relative-strength leadership factor carries a **referee-certified out-of-sample edge specifically at the 60-day hold** (a NON-20 horizon), and can audit that proof from both the Research factor lab badge and the Evidence ledger row — with every uncertified horizon of the same factor honestly marked "Not yet proven".

### New information displayed
A 7th certified-claim row on `/evidence` for `rs_spy_3m` D10 @ h60 (hypothesis incl. the 60-day horizon, out-of-sample PASS verdict, SPY control, registration date, forward-walk score-to-date, "Backs: Research factor lab →"), and a "Proven" badge on the `rs_spy_3m` h60 cohort in `/research/factor-lab`.

### New user actions
None new — the existing badge → ledger deep-link and the existing factor/horizon selection on `/research/factor-lab` are reused.

### UI surface changes
No new pages/panels. One additional claim row on the existing `/evidence` ledger; one additional "Proven" badge state on the existing `/research/factor-lab` `rs_spy_3m` factor view (h60 cohort).

### Product surface delta
The Evidence ledger grows from 6 to 7 certified claims; the factor lab now shows two proven horizons for two different factors (`vcp_contraction` h20/h60 and `rs_spy_3m` h60), reinforcing the "multi-horizon, provable" story without touching any `/stocks` score badge.

### Blueprint conformance
J-09 lives on the **existing** Information-Architecture homes `/research/factor-lab` (Research, lab, link-reached) + `/evidence` (Evidence [NEW]) — the same homes as J-06/J-07, already registered in `blueprint.md`. No new page, route, endpoint, or nav section. Additive blueprint edits applied this iteration: a J-09 row in the "Feature / journey homes" table and an "iter-15 clarification" paragraph in the Data Contract (mirroring the iter-11 clarification for J-07). No nav-skeleton change ⇒ no `blueprint.reapproval-requested`.

### Data-contract additions
**None** (no new displayed value type). The 7th canonical claim is a new DATA ROW under the EXISTING "Evidence status + certified-claim" contract value, resolved by the EXISTING per-horizon `resolveCohortEvidence` reader and served by the EXISTING `GET /api/evidence` — one more reader position, never a second computation or a second endpoint. `rs_spy_3m` is read from the canonical ledger; the UI never recomputes proven-ness.

## OUT OF SCOPE

- Any change to the referee/ledger/evidence-resolver/`verify_edge`/FDR/staging engine code (must stay byte-identical — anti-goal #5 determinism).
- Any new page, route, serving endpoint, computing module, or nav section.
- Any `/stocks` inline score-badge change: `rs_spy_3m` is signal-less (∉ the three score columns), so `proven_signals` MUST stay `{leadership_score}` and no new inline badge may light (J-01/J-02/J-03 unaffected).
- Any additional canonical Evidence Claim beyond the single `rs_spy_3m` h60 promotion — each canonical claim permanently tightens the Bonferroni bar; do NOT casually append another.
- The proposer-backlog `leadership_score` h60 (score-column fallback) and the speculative horizon-term-structure view — backlog only, not this iteration.
- Re-submitting or re-slicing the cohort if the gate blocks (honest-stop).

## DEFINITION OF DONE

- [ ] The post-decompose gate certified the `rs_spy_3m` D10 h60 canonical claim (PASS, divisor 7, `required_p ≈ 0.007143`) and appended the 7th row to `certified-claims.jsonl`. *(If non-PASS: iteration BLOCKS — reported, not forced.)*
- [ ] Target journey **J-09** passes via browser-qa-agent: `/evidence` shows the new `rs_spy_3m` h60 row with all standard fields; `/research/factor-lab` `rs_spy_3m` **h60** cohort shows a "Proven" badge deep-linking to `#factor-rs_spy_3m-d10-h60`; h1/h5/h10/h20 read "Not yet proven".
- [ ] Displayed edge / p-value / SPY control on the new `/evidence` row **byte-match** `certified-claims.jsonl` row 7 (anti-goal #3) — read the ledger file directly to confirm, never trust the rendered label alone.
- [ ] `proven_signals` stays `{leadership_score}`; no `/stocks` inline badge lights (J-01/J-02/J-03 unaffected).
- [ ] Required-still-passing journeys J-01..J-08 remain green.
- [ ] No anti-goal violation introduced.
- [ ] Unit tests pass; engine/referee/ledger tests UNEDITED and green; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-15-dev.md`.

## TESTING REQUIREMENTS

- **Browser (backend held UP the whole run):** verify **J-09** (primary) plus re-verify the shared surfaces J-05 (`/evidence` ledger now 7 rows), J-06 and J-07 (factor-lab badges via the same matcher/page), and the signal-less no-leak guard on J-01/J-02/J-03 (`/stocks` badge set unchanged, `proven_signals` = `{leadership_score}`). Capture **md5-DISTINCT, correctly-labeled, full-page or element-clip** screenshots with the target element scrolled into frame — never a scrolled headless viewport capture (returns a ~5855-byte blank frame; iter-14 lesson). **Open the actual "Proven" frame and confirm it is the `rs_spy_3m` h60 cohort that reads "Proven"** (not a relabeled default-state or other-horizon frame; iter-13 lesson).
- **Unit/integration:** add a case to `apps/frontend/lib/evidence.test.ts` asserting `resolveCohortEvidence` resolves the `rs_spy_3m` D10 h60 cohort to "Proven" with `href = /evidence#factor-rs_spy_3m-d10-h60` when a matching PASS claim is present, and to "Not yet proven" at h1/h5/h10/h20 (mirror the existing `vcp_contraction` h60 case). Existing frontend + backend expectation tests stay UNEDITED and green.
- **Error cases:** uncertified `rs_spy_3m` horizons MUST read "Not yet proven"; a signal-less claim MUST NOT enter `proven_signals`; the gate MUST block a non-PASS canonical claim (verify the block path is honored, not worked around).

## NOTES

- **`"ledger":"canonical"` is explicit and load-bearing** (iter-9b / iter-10): omit it and the winner silently re-stages and never surfaces — the journey would fail to build with no gate error.
- **Yellow flag — scrutinize, don't rubber-stamp** (iter-10, load-bearing): the +0.2134 holdout edge is implausibly large (iter-10 auditor B3). It cleared the referee out-of-sample in staging and its recorded p clears divisor 7, so it is honest to surface IF the canonical gate re-certifies it; but the coherence-auditor and phase auditor must scrutinize it, and the honest-stop guard governs a non-PASS.
- **Precondition verified this plan** (iter-12 lesson): the recorded staging verdict for `rs_spy_3m` D10 h60 exists (staging-ledger row 3, PASS, p=0.00049975) — this is not a blind promotion on a prior recommendation.
- **General matcher, don't special-case** (iter-8 lesson): `resolveCohortEvidence` lights "Proven" on every certified cohort it matches; expect `rs_spy_3m` h60 to light automatically and assert the deep-link lands on the row's real `factor-rs_spy_3m-d10-h60` anchor — do not add a factor-specific branch.
- **Regression proof for a shared-value iteration** (iter-9 lesson): the proof of no regression is the engine's canonical output being byte-identical + the referee/ledger expectation tests unedited-and-green, alongside the browser pass — not the dead `browser_checks_run` flag.
- **Terminal-quality screenshot hygiene** (iter-11 / iter-13 / iter-14): md5 every evidence PNG; a screenshot referenced by multiple test ids can be one reused capture; when pixels are weak, ground the pass in DOM assertions + the byte-exact ledger/unit-test triangle; a "Backend unavailable" pill on an `/evidence` capture invalidates a fail-safe "Not yet proven" reading.
- The referee re-runs the same seeded (20240601), block-bootstrap (block_length 87 at h60) cohort canonically, so the block-bootstrap `p_value` (a property of the seeded data) should reproduce at the floor `0.00049975`; only `deflation`/`deflation_divisor`/`required_p`/`n_trials_at_test` differ from the staging row. The gate — not this spec — is authoritative on the verdict.
