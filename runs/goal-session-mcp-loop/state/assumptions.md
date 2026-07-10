
## iter-26 — goal-evaluator

**Ambiguity:** Decision-tree rule 1 says "a critical anti-goal violation is unresolved -> REGRESSION," but the crash frame (regime `full[:cut]` + the pre-existing full-universe prefill in `_do_backfill`) is unmodified by iter-26's diff, so it is genuinely uncertain whether iter-26 CAUSED the anti-goal #8 violation or merely surfaced a pre-existing latent VSZ bomb while probing a heavier fallback job path.
**We chose:** Scored REGRESSION on the ground that a critical anti-goal is demonstrably, reproducibly violated on the current tree and is unresolved (root-cause fix deliberately not applied) — the verdict does not depend on this-iteration causation (matching the auditor's and ux-regression reviewer's explicit reasoning, and the iter-24 memory-crash precedent). The framework's fail-closed rule for critical anti-goal violations is to halt for human review rather than auto-loop.
**Reversible:** yes

## iter-26b — goal-evaluator

**Ambiguity:** J-16's target proof (UT-02) was executed and the backend crashed, but its perf/byte-identity half is real and one honest-progress sub-criterion showed positive (counter ticked 0->117->246 with no premature "done") — so J-16 could be read as `partial` (capability landed, verification incomplete) rather than `failing`.
**We chose:** `failing`, because there is a VERIFIED negative outcome (a reproduced backend-wide crash) and J-16's own DoD explicitly requires no-OOM/no-crash under the cap plus a browser-qa pass — both violated. This session reserves `partial` for "correct-but-not-cleanly-verified" (a verification gap), not for a verified failure.
**Reversible:** yes
