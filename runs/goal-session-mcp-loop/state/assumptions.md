
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
