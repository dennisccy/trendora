
## iter-26 — goal-evaluator

**Ambiguity:** Decision-tree rule 1 says "a critical anti-goal violation is unresolved -> REGRESSION," but the crash frame (regime `full[:cut]` + the pre-existing full-universe prefill in `_do_backfill`) is unmodified by iter-26's diff, so it is genuinely uncertain whether iter-26 CAUSED the anti-goal #8 violation or merely surfaced a pre-existing latent VSZ bomb while probing a heavier fallback job path.
**We chose:** Scored REGRESSION on the ground that a critical anti-goal is demonstrably, reproducibly violated on the current tree and is unresolved (root-cause fix deliberately not applied) — the verdict does not depend on this-iteration causation (matching the auditor's and ux-regression reviewer's explicit reasoning, and the iter-24 memory-crash precedent). The framework's fail-closed rule for critical anti-goal violations is to halt for human review rather than auto-loop.
**Reversible:** yes

## iter-26b — goal-evaluator

**Ambiguity:** J-16's target proof (UT-02) was executed and the backend crashed, but its perf/byte-identity half is real and one honest-progress sub-criterion showed positive (counter ticked 0->117->246 with no premature "done") — so J-16 could be read as `partial` (capability landed, verification incomplete) rather than `failing`.
**We chose:** `failing`, because there is a VERIFIED negative outcome (a reproduced backend-wide crash) and J-16's own DoD explicitly requires no-OOM/no-crash under the cap plus a browser-qa pass — both violated. This session reserves `partial` for "correct-but-not-cleanly-verified" (a verification gap), not for a verified failure.
**Reversible:** yes

## iter-27 — goal-evaluator

**Ambiguity:** Anti-goal #7 ("No hard-coded credentials, API keys, or tokens in source files") vs the deterministic scan-report flagging 12 CRITICAL secrets in this iteration's commit range. All 12 are planted fake keys inside the vendored `incredible_auto_dev/tests/judgment/` framework subtree (self-test fixtures designed to be detected), which entered via a framework squash-merge, not the iteration's product dev work — leaving open whether "source files" in the anti-goal covers vendored framework test tooling committed into the same repo.
**We chose:** Read anti-goal #7 as scoped to the Trendora PRODUCT source (`apps/`, `config.yaml`, product `data/`/`scripts/`), not the vendored multi-agent framework's own judgment-eval fixtures. The iter-27 product diff (6 backend memory files + config.yaml) carries zero credentials; the flagged keys are non-real (AWS-doc example + fictional LISTVAULT) fixtures whose purpose is to BE flagged. Scored anti-goal #7 upheld / not a violation. Checked fail-closed first (are these real, exploitable, product secrets? no) and corroborated by reviewer + auditor + coherence all treating the subtree as out-of-scope framework tooling.
**Reversible:** yes

## iter-28 — goal-decomposer

**Ambiguity:** goal.md's loop mechanics leave open how many iterations to keep re-attempting the five evidence journeys (J-02/J-06/J-07/J-08/J-09) when a staging exploration surfaces no promotable edge — keep trying vs. acknowledge a plateau. iter-28's dispatch inherited a prior FULL recommendation to "run a new-basis staging exploration and promote a divisor-8-clearing winner."
**We chose:** A verify-only / plateau-acknowledgement pass with NO `## Evidence Claim`, after verifying directly on disk that the complete pre-registered candidate set (proposer-guidance.md §4.1 + §4.2) has already been re-tested on the 30-year basis and ALL FAIL (7 canonical + 7 staging, six of seven staging members wrong-direction; best holdout +8.03e-05 vs required_p=0.00625) — so no candidate is promotable and re-submitting any would self-defeat by permanently tightening the divisor. Per the §4.2 escape valve, the remaining unblock is a human revision of the pre-registered registry; the decomposer surfaces that to the evaluator rather than manufacturing a claim.
**Reversible:** yes

## iter-28 — goal-evaluator

**Ambiguity:** The browser-qa lane marked J-02/J-06/J-07/J-08/J-09 "PASS (see note)", scoring the honest-status half of each journey (badge correctly reads "Not yet proven", displayed numbers byte-match the FAIL verdict). Each journey's written acceptance, however, requires a *Proven* certified edge to surface (J-06/07/08/09: "certified edge surfaced… cohort shows a 'Proven' badge") or drill into (J-02: "Locate a score with a 'Proven' badge and expand it"). The goal text leaves open whether an honest all-FAIL rendering satisfies the journey or only its anti-goal-#1 guardrail.
**We chose:** Held all five at `partial`, not `passing`, per the strict journey acceptance and the 10-iteration session precedent (sanctioned-partial since the iter-18 data-basis reset): the honest-status half is satisfied but the proven-edge half is absent because no certified edge exists on the 30-year basis. A browser-qa PASS on the honest-status half does not constitute journey acceptance; GOAL_ACHIEVED remains gated on a real PASS certified-claim, which is human-unblock-gated (widen the pre-registered candidate registry or re-scope the journeys in goal.md).
**Reversible:** yes

## iter-29 — goal-evaluator

**Ambiguity:** J-02's DoD requires "each score's inline evidence-status element reads 'Not yet proven'" on `/stocks/{ticker}`. Both captured frames (J-02-stock-detail-badges.png, J-02-verify.png) show the AAPL detail page rendering with the "no orders" header and NO fabricated proof panel, but the three inline score badges sit BELOW the captured fold — so there is no single pixel directly showing the three "Not yet proven" score badges on the detail page itself.
**We chose:** Scored J-02 `passing`. The acceptance is met by the visible negative assertion (no fabricated proof panel — the load-bearing anti-goal #1 check) PLUS strong multi-channel corroboration in lieu of the direct pixel: (a) the browser-qa DOM assertion (3x `data-testid=evidence-badge` `data-proven=false`, tooltip naming the Evidence ledger, click-diff test showing no proof panel expands); (b) the same three scores (Leadership/Entry Quality/Risk) demonstrably reading "Not yet proven" at every horizon on the factor-lab fullpage the evaluator opened; (c) J-01's 3,246 "Not yet proven" leaderboard instances from the same `GET /api/evidence` source; (d) zero code diff since the iter-28 live capture. This mirrors the iter-14 precedent (J-01/J-02 kept passing on zero-diff + DOM re-check + backing-row rendering). Under the owner's outcome-neutral re-scope, the honest "Not yet proven" state IS the acceptance.
**Reversible:** yes

## iter-30 — goal-decomposer
**Ambiguity:** B-901's backfill instruction ("registry complete for all existing registrations" / "proposer-guidance tables + already-certified claims as historical rows") leaves the SCOPE of "every registered hypothesis" open — whether "already-certified claims" means the canonical ledger only or every distinct claim across BOTH the canonical and staging ledgers (including FAILs and the closed ma_stack), and how the §4.1/§4.2 candidate tables relate. This session has 0 PASS, so "certified" is itself ambiguous.
**We chose:** Backfill = the UNION of the proposer-guidance §4.1/§4.2 pre-registered candidate rows and every distinct claim selector-set across BOTH `certified-claims.jsonl` and `staging-ledger.jsonl`, deduplicated by hypothesis, each labeled with its source + recorded status (the closed `ma_stack` FAIL included as a `closed` row) — the honest superset that makes the registry the true pre-registration memory the enforcement gate checks against and J-19's graveyard later reads. A narrower reading would under-populate the registry and wrongly refuse a future legitimate revisit once enforcement is on.
**Reversible:** yes

## iter-30 — goal-evaluator

**Ambiguity:** The iter-30 DoD literally reads "Backfill complete: registry contains ... (≥14 ledger-derived rows)", but the committed registry has 11 rows. The goal text leaves open whether the binding requirement is the literal "≥14" or the substantive clause "the proposer-guidance §4.1/§4.2 rows ∪ every distinct claim from both ledgers, deduplicated by hypothesis".
**We chose:** Scored the DoD's backfill-completeness line as MET by 11 rows — treating "≥14" as the decomposer's uncomputed estimate (not a binding threshold) and the substantive dedup clause as the real bar. Grounds: 14 raw ledger entries contain 3 exact-selector-set cross-ledger duplicates (staging candidates later promoted under ledger:canonical with identical selectors), and `match_registration` must map one exact selector-set to ONE row, so 11 is the forced-correct count; `test_registry.py`'s round-trip tests prove every one of the 14 raw entries matches exactly one backfilled row (completeness satisfied), the dev flagged the deviation, and the reviewer + auditor independently re-derived 11 against the live ledgers. Not a silent call (documented in 3 pipeline reports), recorded here because the SCORING decision accepts a count that differs from the literal DoD checkbox.
**Reversible:** yes

## iter-31 — goal-decomposer
**Ambiguity:** J-19's "every non-PASS verdict" (backlog B-902 "read-compose from ledgers + registry; page") leaves open (a) whether the STAGING ledger's non-PASS verdicts are in scope — the blueprint's iter-9/10/12 clarifications declared the staging ledger "internal-only ... never read by any page, never served, never displayed" — and (b) whether the composition is backend-side (a new endpoint) or frontend-side (the page reads existing endpoints).
**We chose:** Surface BOTH ledgers' NON-PASS verdicts via a NEW backend composition endpoint `GET /api/research/graveyard` (a new PURE `app.engine.graveyard` read-compose module joining `ledger.read_entries` over both ledgers with `registry.match_registration` lineage). Grounds: the graveyard's stated purpose (institutional memory of what does NOT work, so no future model re-derives a dead idea) squarely includes the staging explorations — exactly the dead ideas most likely re-derived; the honesty fence is preserved (the graveyard shows ONLY non-PASS, staging carries 0 PASS, so no staging edge is ever surfaced as proven, and `/evidence` + `proven_signals` + the "Proven" badge stay byte-identical); `GET /api/evidence` serves the canonical ledger only, so a frontend-only compose cannot reach the staging FAILs without a new served surface regardless; and both B-902's named "UI-recompute" failure mode and the blueprint's compute-once-serve-verbatim discipline point to backend composition. This narrows the prior "staging internal-only" invariant, documented in the blueprint iter-31 clarification.
**Reversible:** yes

## iter-31 — goal-evaluator

**Ambiguity:** J-19's goal.md acceptance (steps 1-3 + the 4 bullets) is fully browser-verified PASS; the disputed UT-07 is the lineage link's *auto-scroll-to-exact-row* assist, which the ui-test-designer elevated to a P1 and the DoD's TESTING REQUIREMENTS phrase as "a row's lineage link resolves to its registry row." The click DOES resolve to the correct registry URL + fragment and the target row exists in the DOM — only the scroll-into-position didn't fire on SPA navigation (fixed post-lane, but the canonical lane wasn't re-run). So it is open whether J-19 is "passing" (its own goal.md acceptance is met and the failure is an out-of-acceptance refinement now fixed) or "partial" (a DoD-named P1 browser case reads FAIL and the fix is not canonically re-verified).
**We chose:** Held J-19 at `partial`, not `passing` — treating the lineage-link scroll as a real (if minor) part of the "links to its registry row" acceptance AND, decisively, applying the session's "correct-but-not-cleanly-canonical-verified = partial" discipline (the auditor's own browser re-check is not the DoD-named canonical lane). The asymmetry drove it: the overall verdict is CONTINUE regardless (7 journeys unbuilt), and iter-32 runs a full browser-qa lane anyway, so re-recording one clean UT-07 frame is nearly free — whereas marking `passing` on a canonical-FAIL-not-re-run would erode exactly the guard that caught iter-18/24. A human who judges the graveyard's core sufficient could reasonably flip this to `passing`.
**Reversible:** yes

## iter-32 — goal-evaluator

**Ambiguity:** J-11 ("Every displayed 'Proven' edge is re-certified... no stale edge survives") is in
iter-32's required-still-passing set but got NO dedicated golden replay or browser case this iteration
(J-11.json exists but was not run; audit T1 + ux-regression both flagged the gap). Whether J-11 must
be re-verified via its OWN dedicated case each iteration, or whether "0-PASS ledger + byte-identical
certification economy + corroborating /evidence and /stocks frames both showing 0 'Proven'" suffices,
is left open.
**We chose:** Scored J-11 `passing` on byte-identity + corroboration rather than holding it `unknown`.
Grounds: the invariant is trivially satisfied on a 0-PASS ledger (no 'Proven' edge exists to go
stale), the entire economy is git-diff EMPTY (no stale-edge mechanism), and I directly observed 0
'Proven' on both surfaces J-11 depends on (UT-13 /evidence 7 FAIL/0 PASS; UT-14 /stocks 3 'Not yet
proven'/row). Matches the audit/ux-regression/closure consensus that the risk is nil. Recorded here
(not silent) because it accepts corroboration in lieu of a dedicated re-verification; a human who
wants the required set fully closed should add the J-11 replay to iter-33 (recommended in the eval).
**Reversible:** yes

## iter-33 — goal-decomposer
**Ambiguity:** B-301's preflight "data freshness (latest bar age vs expectation), market-calendar aware" is underspecified for an offline/DETERMINISTIC app that runs against a FROZEN committed seed (goal.md Constraints): "now"/"expectation" is undefined, and a wall-clock `date.today()` anchor would both make the healthy `GO` state impossible (the seed's latest bar is always "stale" vs the real current date) and break determinism (anti-goal #5) / demo reproducibility.
**We chose:** Anchor freshness to a DETERMINISTIC config/seed-derived reference (default = the seed's own latest available date, so a fully-loaded seed reads `GO`), count the age in trading days via the existing SPY market calendar, and induce the stale (DEGRADED/NO-GO) test state via a controlled config/env override (`readiness.freshness_max_age_days` / a pinned reference) — never wall-clock time and never by mutating committed seed data.
**Reversible:** yes

## iter-33 — goal-evaluator

**Ambiguity:** The iteration ended CLOSURE-FAIL, and this session's strong precedent (iter-20/22/24/31)
is that a TARGET journey does not flip to `passing` in a CLOSURE-FAIL iteration. But in every prior
case the CLOSURE-FAIL was about the TARGET's OWN canonical browser evidence (skipped / stale / a
post-lane fix not re-verified). Here J-20's own evidence is complete and clean on the FINAL build (no
post-lane fix — audit made zero repo changes; closure explicitly EXEMPTS J-20 — "tested to an unusually
high standard ... not the source of the blocking finding"); the CLOSURE-FAIL is entirely about a
DIFFERENT DoD line (6 OTHER required journeys — J-01/02/04/05/13/18 — not deterministically replayed
because full iters route through run-phase.sh, which lacks the replay lane). So it was open whether
J-20 is `passing` or `partial`.
**We chose:** Scored J-20 `passing`. The session's `partial` discipline exists to avoid claiming a
journey done when ITS OWN canonical lane didn't verify it — a guard fully satisfied for J-20 (browser-qa
PASS 20/20 on the final build; all 3 states md5-distinct; exact NO-GO phrase pixel-confirmed;
single-source UT-19; correctness matrix auditor-verified against the real compute_preflight). Marking
`partial` would misattribute a replay gap in OTHER journeys to J-20's own evidence, which is false and
contradicts the closure auditor's own read. The guard is instead honored at the OVERALL level: verdict
is CONTINUE (not GOAL_ACHIEVED), the required-still-passing replay gap is recorded explicitly on
J-01/02/04/05/13/18, and the mandated next step is the cheap lean replay closeout that re-clears closure.
**Reversible:** yes

## iter-34 — goal-evaluator

**Ambiguity:** J-20 was this iteration's named Target to "re-confirm passing via browser-qa on the final tree," but only its GO state was re-induced live this pass (all 5 surfaces, single-source, DOM===API); the loud DEGRADED/NO-GO states — including the mandated "do not rely on today's board" phrase — were NOT re-induced live (a tool-permission boundary). J-20's acceptance names all three states. It was open whether a GO-only live re-confirmation counts as "re-confirmed passing."
**We chose:** Scored J-20 `passing` (re-confirmed). Grounds: J-20 was ALREADY fully verified passing at iter-33 (all three states, exact NO-GO phrase, browser-qa 20/20 on the final build — the iter-33 CLOSURE-FAIL was about OTHER journeys' replay gap, not J-20's own evidence), and readiness.py + config.yaml + all apps/frontend are git-identical to that verified iter-33 commit (4561da1) — zero product diff this iter — so there is no regression mechanism for the loud states. The live GO re-confirmation + byte-identity carry of the loud states is sufficient; requiring a fresh live NO-GO induction on an already-verified, byte-identical journey would be verification for its own sake. The pipeline artifact (merged ui-test-results) discloses the GO-only live scope openly; this entry records that the SCORING acceptance of it is my call.
**Reversible:** yes
