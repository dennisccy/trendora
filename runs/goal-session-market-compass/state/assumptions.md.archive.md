# assumptions.md — archive

Entries moved out of `assumptions.md` by scripts/automation/lib/condense.sh (maintenance protocol §4).
Append-only: nothing here is ever deleted or rewritten.

<!-- condense.sh 2026-08-20T17:24:05Z: moved 2 entries (keep-iters=5) -->

## iter-0 — goal-evaluator

**Ambiguity:** J-01's acceptance bundles four things (single stored source, >=95% coverage,
honest "Unassigned" for unknowns, methodology disclosure). goal.md does not say how to score a
journey where the honesty rails hold but the coverage target is missed by a wide margin.
**We chose:** Scored J-01 `partial` rather than `failing`, on the basis that some acceptance
steps genuinely passed with evidence (DELL/GRMN labels identical across leaderboard, stock detail
and API; unknown serves null, never a fabricated sector) while coverage (78.4% Unassigned vs the
<=5% target) and the methodology disclosure are entirely absent. `partial` here is a factual
record, not credit toward the deliverable — it does not support GOAL_ACHIEVED and the remaining
work is spelled out in the recommendation.
**Reversible:** yes

## iter-0 — goal-evaluator

**Ambiguity:** goal.md's loop mechanics say "lean by default; full when an iteration first lands
user-visible UI changes", but do not say whether J-01 (mostly backend sector wiring plus one new
Methodology paragraph and changed sector labels on /stocks) counts as a user-visible UI change.
**We chose:** Treated it as user-visible and recommended `full` depth for iteration 1, because
the owner will see different sector labels on /stocks and new disclosure text on /methodology,
and because J-01's "scores must be byte-identical" and "never fabricate a sector" claims benefit
from the audit lane on this session's first product change.
**Reversible:** yes

