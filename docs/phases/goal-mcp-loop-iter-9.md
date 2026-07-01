# Goal Iteration 9 — Sustainable trial economy (online-FDR staging ledger), build A before widening the scan

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 9
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-07, J-08 — ENABLEMENT ONLY. Neither flips to `passing` this iteration. iter-9 builds ONLY the shared trial-economy prerequisite both new Must-have journeys require; success is measured by the DEFINITION OF DONE below (economy live in a staging ledger + canonical `/evidence` byte-identical + J-01..J-06 still green), NOT by a J-07/J-08 status change. This is a backend infrastructure milestone, in the same sense the iter-2 evaluator recorded "backend milestone (not a journey-state change)."
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06 (ALL of them — a FULL regression. This iteration refactors the shared certification engine — `referee` / `ledger` / `verify_edge` — that every "Proven" badge on every surface reads through. Per the decomposer rule "changing a value's computing module can break every reader," the entire evidence-status reader set is re-verified.)
- **Anti-goal reminders:**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## GOAL

Stand up the **sustainable trial economy** — an injectable, default-off online-FDR (LORD++) deflation policy running in a SEPARATE internal **staging** ledger — so future iterations can explore multi-horizon and multi-factor-combination edges (J-07, J-08) without permanently tightening the user-facing canonical Bonferroni bar, while the canonical `/evidence` ledger and every "Proven" badge stay byte-identical.

## BACKGROUND

`docs/goal.md` has been extended with two NEW human-authored Must-have journeys — **J-07** (a certified edge at a NON-20 forward horizon, surfaced on the Research factor lab + `/evidence`) and **J-08** (a curated 2-factor combination certified edge, surfaced on the Combination lab + `/evidence`) — plus an "Improvement direction (engineering)" section addressed explicitly to the iteration planner. That section is unambiguous about sequencing: **"build the economy first, then widen the scan"**, "**(A) Sustainable trial economy … build this FIRST**", and "**(B) Open the scan aperture (after A)**". J-07 and J-08 are literally Part B Phase 1. So iter-9 builds Part A only.

This is not manufactured work: J-07/J-08 are unbuilt Must-have journeys (absent from `journey-history.json`), so the goal is no longer achieved despite the iter-8 GOAL_ACHIEVED. The motivation is structural, not cosmetic: the canonical `certified-claims.jsonl` now holds 4 Bonferroni entries (divisors 1–4; line 3 `ma_stack` is a permanent FAIL), so the **next** canonical claim faces divisor 5 (`required_p = 0.05/5 = 0.010`) and **every** future probe — pass or fail — tightens it forever (`ledger.count_trials`). Exploring J-07's horizons and J-08's combinations directly against that bar would risk a gate FAIL that both blocks the iteration and permanently raises the bar for everyone. The economy fixes this: exploration runs in an isolated staging ledger under a replenishing online-FDR economy; only deliberately promoted winners reach canonical, which stays strict Bonferroni. Build it first so the wider aperture has a sustainable economy to run in.

iter-9 ships **NO new "Proven" claim** and therefore carries **no Evidence-Claim JSON block** — the post-decompose gate passes through automatically (it only certifies claim-bearing specs), so this iteration cannot block on the referee and cannot tighten the canonical bar. Full depth because this is a load-bearing refactor of the shared certification engine (`referee` / `ledger` / `verify_edge` / the gate / the harness) with a strict byte-identical-defaults invariant that demands the full QA + auditor pipeline.

## IN SCOPE

### Backend
- [ ] NEW `apps/backend/app/engine/online_fdr.py` — a PURE LORD++ online-FDR module (no RNG, no IO; the test wealth/level is derived deterministically from the sequence of prior rejection times). Exposes the per-trial significance `test_level` an online-FDR economy would allocate given the rejection history. Pure ⇒ trivially unit-testable and determinism-preserving.
- [ ] `apps/backend/app/engine/referee.py` — make the multiple-testing deflation an **injectable policy** on `RefereeState` (e.g. a `test_level` / `deflation` selector) with the **DEFAULT = Bonferroni** so `certify_edge` reproduces today's `required_p = alpha_per_test / divisor` byte-identically. The `Verdict` already records `required_p` + `deflation_divisor` + `deflation`; keep recording the policy used per verdict for audit. No behavior change on the default path.
- [ ] `apps/backend/app/engine/ledger.py` — add a DERIVED `rejection_offsets` accessor (the ordinals of PASS entries; on the live canonical ledger this is `[1, 2, 4]` — lines 1/2/4 PASS, line 3 FAIL). Derived only — **no schema change, no rewrite of any existing entry.** This feeds the LORD++ wealth reconstruction.
- [ ] `apps/backend/app/mcp/tools.py` — `verify_edge` threads the economy: it selects the target ledger (canonical vs staging) and the matching deflation policy (canonical ⇒ Bonferroni, staging ⇒ the configured economy), reads the cumulative state from THAT ledger, and appends there. `verify_edge` MUST remain the **ONLY** ledger writer (iter-1 lesson) and MUST stay READ-ONLY w.r.t. the snapshot DB (the sole write is the ledger append).
- [ ] `apps/backend/app/engine/forward_walk.py` — preserve the reproduce-contract by reconstructing the policy `test_level` from each entry's recorded `required_p` (so a re-score reproduces the original verdict byte-for-byte; only newer/matured data may move it).
- [ ] `apps/backend/app/config.py` — extend `EvidenceCfg` with a typed `FdrCfg` (defaults reproduce today: FDR **off**) and a `staging_ledger_path`. Defaults must keep a config predating this block loading + behaving identically.
- [ ] `config.yaml` — add a documented `evidence.staging_ledger_path` (a NEW internal ledger file, e.g. `runs/goal-session-mcp-loop/state/staging-ledger.jsonl`) and an `fdr` sub-block (`enabled: false` by default + LORD++ tunables), consumed VERBATIM (no magic numbers in code). Default-off ⇒ canonical behavior unchanged.
- [ ] `project-extensions/gates/verify_claim.py` — read an OPTIONAL per-claim `"ledger"` key on each Evidence Claim (default `"staging"`, explicit `"canonical"` for promoted winners) and route `verify_edge` to the corresponding ledger path (`STAGING_LEDGER_PATH` vs `LEDGER_PATH`). The `exit 3`-on-non-PASS blocking and the fail-closed behavior when a required path is unset stay UNCHANGED. An unrecognized `"ledger"` value is fail-closed (block), never silently certified.
- [ ] `scripts/automation/run-goal.sh` — export `STAGING_LEDGER_PATH` (pointing at the staging ledger under `state/`) alongside the existing `LEDGER_PATH`, at the same two dispatch sites that currently set `LEDGER_PATH` (≈ lines 1070 and 1401).

### Frontend (if applicable)
- None. This iteration introduces no new surface and changes no frontend source. The staging ledger and the FDR economy are INTERNAL (goal.md: "Self-improving evidence loop (internal)"; "exploration is isolated"); they are never served to an endpoint and never displayed. A user-visible change here would be a DEFECT — canonical `/evidence` and every "Proven" badge must stay byte-identical.

### New user-facing capability
None this iteration (foundational/internal). It ENABLES the later user-facing J-07 (multi-horizon proven edge) and J-08 (multi-factor combination proven edge) by giving their exploration a sustainable, canonical-bar-safe place to run.

### New information displayed
None. Canonical `GET /api/evidence` (claims list + `proven_signals`) is byte-identical before/after.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
No visible delta by design. Internally, the platform gains a sustainable discovery economy: exploration probes accumulate in an isolated staging ledger under a replenishing online-FDR policy, while the user-facing `/evidence` ledger keeps its strict family-wise (Bonferroni) "Proven" guarantee untouched.

### Blueprint conformance
No new surfaces and no nav-skeleton change — Information Architecture is untouched (no `blueprint.reapproval-requested` written). The change is confined to the certification engine behind the already-registered Data-Contract value "Evidence status + certified-claim" served by `GET /api/evidence`. An additive **iter-9 clarification** note is appended to the blueprint's Data Contract recording the new internal deflation-policy seam + staging ledger (NOT a displayed value, NOT a new serving endpoint; canonical proven-ness still flows solely from `verdict.status == PASS` under strict Bonferroni).

### Data-contract additions
None. No NEW displayed value and no new serving endpoint. The staging ledger is internal-only (never reaches the UI). Canonical `GET /api/evidence` and `proven_signals` are unchanged. The existing single source of truth for proven-ness is preserved — and explicitly hardened (FDR is weaker than family-wise control, so it is fenced to staging and never touches the canonical badge).

## OUT OF SCOPE

- **Part B — opening the scan aperture** (this is iter-10+, "after A"): multi-horizon scan config (`triad.horizons`), the combination enumerator + selector translation in `triad_scan.py`, raising `triad.top_k` / the `screen.haircut_coef`, and the PRE-REGISTERED, config-backed combination candidate set (mirrored into `project-extensions/proposer-guidance.md`).
- **J-07 surfacing** — the non-20-horizon factor-lab "Proven" badge, its `/evidence` claim row, and its canonical certified claim.
- **J-08 surfacing** — the `/research/factor-combination` "Proven" badge, its `/evidence` claim row, and its canonical certified claim.
- **Any new "Proven" claim of any kind**, and any write to the canonical `certified-claims.jsonl`. This iteration carries no Evidence-Claim block by design.
- Any frontend change, any new page, any nav change.
- The note's explicitly-deferred ideas (NOT this direction): quantile spreads (D10−D1), regime conditioning, sector cohorts, scoped α-split families.

## DEFINITION OF DONE

- [ ] **Canonical is byte-identical (the load-bearing invariant).** The 4 existing entries of `runs/goal-session-mcp-loop/state/certified-claims.jsonl` are unchanged (`deflation="bonferroni"`, divisors 1–4 — honest history), `build_evidence_payload(canonical)` / `GET /api/evidence` returns a byte-identical payload, and `proven_signals == {leadership_score}`. ⇒ J-01..J-06 unperturbed.
- [ ] **Defaults reproduce today.** Every existing referee / ledger / evidence / api-evidence unit test stays green with no expectation edits; the default deflation path is Bonferroni and `certify_edge` yields the identical `required_p` for the same inputs.
- [ ] `online_fdr.py` is PURE (no RNG/IO) and unit-tested: its allocated `test_level` is asserted on a known rejection sequence (deterministic), and `rejection_offsets` derives `[1, 2, 4]` from the live canonical ledger.
- [ ] **Staging is isolated and routed.** A staging-routed claim writes the staging ledger and NOT the canonical file; a `"ledger":"canonical"` claim writes canonical under strict Bonferroni. Verified by an integration test that drives `verify_edge` / the gate both ways.
- [ ] The gate (`verify_claim.py`) reads the optional `"ledger"` key (default `"staging"`), routes correctly, keeps `exit 3`-on-non-PASS + fail-closed-on-unset-path, and fail-closes an unrecognized ledger value.
- [ ] `run-goal.sh` exports `STAGING_LEDGER_PATH` at both `LEDGER_PATH` dispatch sites; FDR is `enabled: false` in `config.yaml` (canonical stays strict Bonferroni — anti-goal #1/#4 honesty constraint upheld).
- [ ] Target journeys J-07, J-08 do NOT regress to a worse state (they remain unbuilt/unknown — expected); Required-still-passing journeys J-01..J-06 remain green via deterministic golden-script replay.
- [ ] No anti-goal violation introduced (secret scan of the diff clean; no buy/sell/return language; determinism + no-lookahead preserved; canonical proven-ness unchanged).
- [ ] This spec carries no Evidence-Claim block ⇒ the post-decompose gate passes through (no canonical-bar tightening).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-9-dev.md`; post-QA audit handoff written at `docs/handoffs/goal-mcp-loop-iter-9-audit.md`.

## TESTING REQUIREMENTS

- **Unit/integration (primary — this is a backend iteration):**
  - `online_fdr.py` LORD++: allocated `test_level` asserted exactly on a known rejection-offset sequence; pure/deterministic (same input ⇒ same output, no RNG/IO).
  - Referee default path: `certify_edge` with the default (Bonferroni) policy yields byte-identical `required_p` / `deflation_divisor` / verdict for the existing fixtures — existing `test_referee.py` stays green unedited.
  - `ledger.rejection_offsets` derives `[1, 2, 4]` from the live canonical ledger; no entry rewritten.
  - Ledger routing: a staging-routed `verify_edge` appends to the staging file only; a canonical-routed one appends to `certified-claims.jsonl` under Bonferroni only (cross-contamination test).
  - `forward_walk` reproduce-contract: reconstructing `test_level` from a recorded `required_p` reproduces the original verdict byte-for-byte.
  - Canonical regression: `GET /api/evidence` payload + the 4 ledger entries byte-identical (frozen golden); `proven_signals == {leadership_score}`.
- **Error cases (must be rejected, not silently weakened):**
  - A claim with an unrecognized `"ledger"` value ⇒ gate fail-closed (block / `exit 3`), never certified.
  - `STAGING_LEDGER_PATH` (or `LEDGER_PATH`) unset for a claim that needs it ⇒ fail-closed block, never a silent canonical write.
  - Malformed `fdr` config ⇒ a loud `ConfigError` or a documented fall-back to the Bonferroni default — never a silent weakening of the canonical bar.
- **Browser:** no new surfaces to test. The Required-still-passing set J-01, J-02, J-03, J-04, J-05, J-06 must be re-confirmed by the goal-mode deterministic golden-script replay (every evidence badge byte-identical against the unchanged canonical `/evidence`). If that replay does not run for a backend-only full iteration, the executor must run a browser-qa-agent regression pass over J-01..J-06 instead. Judge regression on the canonical `/api/evidence` byte-match + the unit suite + (where run) the canonical `…-ui-test-results.md` — NOT on the dead `browser_checks_run` flag (iter-6 lesson).

## NOTES

- **Sequencing rationale (load-bearing):** goal.md's engineering direction is explicit — "build the economy first, then widen the scan"; Part A is "build this FIRST"; Part B (multi-horizon + combinations = J-07/J-08) is "after A". Doing J-07/J-08 before the economy would force blind canonical claims against a divisor-5 bar, risking a gate FAIL that blocks the iteration AND permanently tightens the bar.
- **Honesty constraint (anti-goal #1 + #4), verbatim from goal.md:** "FDR controls the false-discovery *rate* and is weaker than family-wise control — it runs ONLY in staging; the user-facing `/evidence` 'Proven' badge stays Bonferroni-curated. Every verdict records its `deflation` + `required_p` for audit. No unbacked or overfit edge is ever shown as proven." The default-off design and the canonical-byte-identical DoD enforce this.
- **Lessons applied:**
  - iter-1 ("the writer is the single source"): `verify_edge` must remain the ONLY ledger writer after threading the economy — do not add a second write path for staging; route the same writer to a different file.
  - iter-6 ("`browser_checks_run` is a DEAD flag — judge on canonical evidence + the engine log, never the flag"): score this iteration's regression on the byte-identical `/api/evidence` payload + the green unit suite, not on the status flag.
  - iter-8 ("expect every certified cohort to read Proven; never special-case the matcher"): the inverse guard here — the economy must NOT change which signals read "Proven"; `proven_signals` must stay exactly `{leadership_score}` and no canonical entry may move.
- **No Evidence Claim by design:** the gate greps for a `## Evidence Claim` heading; this spec deliberately contains none, so a plain (non-data-derived) iteration passes the gate instantly and risks no canonical-bar movement.
- **Escalation flag for the developer:** if the LORD++ "injectable, default-off / defaults-reproduce-today" invariant cannot be met without altering any of the 4 canonical ledger entries or changing the default `certify_edge` output, STOP and flag in the handoff — do NOT modify the canonical entries or the default path. Honest history is non-negotiable.
- **Next iterations (for context, not this spec):** iter-10 uses the new staging ledger to explore non-20 horizons cheaply and promotes one winner to canonical to surface J-07; iter-11 does the same for a pre-registered 2-factor combination to surface J-08.
