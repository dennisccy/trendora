# Goal Session market-compass — Assumption Ledger

Append-only. Each entry records a scoring decision that required interpreting an
ambiguous goal, so the owner can veto it early.

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

## iter-1 — goal-decomposer

**Ambiguity:** The agent instructions describe two related but not identical trigger sets for
depth=full: the "four escape conditions" that govern when a full spec is justified relative to
the evaluator's binding recommendation (prior ESCALATE/REGRESSION, prior coherence-audit FAIL,
hardening cadence due, or a brand-new full-stack journey) versus the four NUMBERED triggers
required in the `Full trigger:` metadata line (1 Structural/cross-cutting, 2 Data-model
migration, 3 Prior ESCALATE, 4 Hardening cadence). Neither text says how "brand-new full-stack
journey" (the condition that genuinely holds here — this is the session's first code-changing
iteration, matching goal.md's own "full when an iteration first lands user-visible UI changes"
rule) maps onto one of the four numbered triggers for the metadata line and the engine's
arbiter re-validation.
**We chose:** Cited numbered Trigger 1 (Structural/cross-cutting) in the metadata line, grounded
in an objective, mechanically-checkable fact rather than the "first UI" framing: this iteration's
J-01 wiring touches config (`UniverseCfg` + `config.yaml`), the engine's sector-writing module
(`scoring.score_stocks`), the methodology content producer (`app.engine.methodology`), and the
`/methodology` frontend page — four modules whose combined interaction (alias resolution, staying
descriptive-only/isolated from every score input, and disclosure rendering) has no single existing
test today. Trigger 3 and trigger 4 were checked and do not hold (last verdict CONTINUE;
consecutive-lean counter 0/6).
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** The browser-QA lane returned FAIL for J-01 (its precondition step died and it ran
against a stale backend), while the auditor — after fixing the shipped-hidden disclosure — verified
the journey's substance live (fresh run 3081 at as-of 2026-08-12: 0/539 Unassigned via API and a
full 539-row DOM sweep; DELL/GRMN consistent across all three surfaces). goal.md does not say how to
score a journey whose asserted behavior is confirmed live but whose browser-lane capture never
reached the acceptance state.
**We chose:** Scored J-01 `partial` (unchanged label, materially advanced) with
`evidence_makeup: true` and the gap recorded as `capture-defect`, per methodology A.7 — NOT `passing`
(the no-screenshot rail is absolute and no screenshot of the /stocks coverage state exists from any
iteration, nor does the acceptance-required `[NEW]` walkthrough), and NOT `failing` (the behavior is
demonstrably met — I re-measured `GET /api/stocks` myself at 0/539 null). The consequence is that the
make-up capture rides the next iteration as a passenger task, never as its goal.
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** The browser-QA run permanently destroyed 1,174 bars, 18 snapshots and 30,439 forward
returns for 2026-08-13/14, recoverable only via a live network fetch that AG-9 forbids without an
amendment. No anti-goal names data destruction, and the decision tree's REGRESSION rule fires only
on a passing→failing journey or a critical anti-goal violation.
**We chose:** Did not treat the loss as a REGRESSION or an anti-goal violation — the destroyed bars
were user-added (outside the committed seed, which is intact through 2026-08-12), the product
behaved correctly and refused to fabricate replacements, and no journey depended on those dates.
Recorded it instead as a prominent owner-facing flag in eval.md plus a binding goal.md-amendment
request for J-01 step 1.
**Reversible:** yes

## iter-2 — goal-decomposer

**Ambiguity:** The Data Contract's baseline row treats the "Next-session manifest" as one document
with ONE producer (`build_manifest_payload`) covering both the content this iteration targets
(session delta, narrative, candidate selection + why-not) and the freeze/integrity fields goal.md
assigns to J-05/J-06 (mode, version, hashes, provenance, frozen cohort storage,
`prospective_eligible`, `available_at_utc`, export). goal.md's own suggested build order sequences
J-02+J-03+J-04 ("engine cluster... one manifest producer") strictly before J-05+J-06 ("freeze/integrity
pair"), but does not say which manifest fields the engine-cluster iteration must actually persist and
serve versus which stay unbuilt until the freeze iteration — and J-03's own acceptance step 3 names
`content_hash` explicitly ("via the manifest `content_hash`") while the Improvement-direction section
defines `content_hash` as covering exactly "the content block" (session delta + narrative +
candidates/trace), which is exactly the field set this iteration owns.
**We chose:** This iteration builds `build_manifest_payload`'s content-computation logic (session
delta, narrative, `evaluate_selection`'s candidates/why-not/disposition tally) plus `content_hash`
over that block, persisted in a new, minimally-shaped `next_session_manifests` table and served via
`GET /api/compass` (compute-once, serve-from-storage — no per-request recompute). Freeze/versioning/
mode, `manifest_hash`, engine-identity/rule-hash provenance, the frozen `comparison_cohort` /
`near_threshold_shadow` storage and their audit-view rendering, `prospective_eligible`,
`available_at_utc`, and export stay explicitly OUT OF SCOPE, deferred to J-05/J-06, which will extend
the same table with additive columns only.
**Reversible:** yes

## iter-2 — goal-decomposer

**Ambiguity:** The blueprint's Information Architecture already names `/` as the canonical home for
J-02/J-03/J-04's new cards, but `/` is still the unmodified legacy Dashboard (confirmed live:
`sidebar.tsx`'s NAV still labels it "Dashboard", `page.tsx` is the old dashboard component) — goal.md's
full Today-page ordering/chrome (state band above these cards, readiness/preflight separated into
chrome) is J-07's acceptance target and the old dashboard body's relocation to `/market` is J-08's,
both explicitly out of this iteration's targeted journeys per the evaluator's own recommendation.
**We chose:** Add the three new cards (Summary, What-changed, Next-session focus) to the existing `/`
page, above the current unmodified dashboard body, reading only the new `GET /api/compass` endpoint;
leave final section ordering, chrome/readiness separation, and the old body's removal to J-07 and
J-08's own iterations rather than attempting the full page recomposition now.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** J-02, J-03 and J-04 each carry a `Walkthrough` acceptance bullet requiring a
`[NEW]`-flagged walkthrough viewable via `demo.sh market-compass --session-live`, and J-01 carries
the same. The pipeline ran at lean depth, so no demo lane executed and no walkthrough exists for any
of the four. goal.md does not say whether a missing walkthrough blocks a journey whose behaviour is
otherwise fully demonstrated by a screenshot.
**We chose:** Scored all four `passing` and recorded `evidence_makeup: true` with the gap noted as
`capture-defect`, per methodology A.7, which names a missing walkthrough recording as a capture defect
that must NOT downgrade an evidence-confirmed status. The no-screenshot rail (A.3) is separately
satisfied: each of the four has its own cited screenshot showing acceptance state. The consequence is
that the make-up recording rides the next iteration as a passenger task, never as its goal.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** J-04's steps 2 through 6 read "On `/` at the latest as-of..." and then require opening
a candidate card. On the latest stored as-of (2026-08-12) zero members clear the three-qualifier rule,
so no candidate card exists to open. goal.md's own step 8 requires the honest-empty state and step 7
requires stepping `?asof` to a historical Risk-off date, but it never says which date steps 2-6 should
use when the frontier date is legitimately empty.
**We chose:** Accepted the browser lane's approach — step 1 and step 8 verified live at the latest
as-of (0 candidates, explicit `candidates_empty_reason`), and steps 2-6 verified at the stored
historical as-of 2026-07-23 (1 real candidate, GWW) using genuine stored data rather than a synthetic
fixture. Treated this as satisfying the journey, because the assertions are about the card's content
being traceable to stored rows, not about a particular calendar date.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** J-01 step 1 (destructive Remove + backfill) was deliberately not executed this
iteration, and step 2 as written ("select the Sector filter's 'Unassigned' option") is literally
unexecutable now that coverage is 100% and the option no longer renders. goal.md does not say whether
a journey can pass when a precondition step is skipped and an assertion step is unexecutable as
worded.
**We chose:** Scored J-01 `passing`. The Acceptance block — not the Steps list — is the bar, and every
acceptance clause is met with evidence (coverage 100% vs the >=95% requirement, single stored source,
honest NULL/"Unassigned" for unknowns, disclosure on /methodology, byte-identity fixture cited).
Step 1's purpose (prove the mapping applies to a NEWLY produced run) was already achieved in iter-1 by
run 3081, and step 2's intent was met more strongly than its literal wording — the browser lane read
`select.options` directly and confirmed the Unassigned option does not exist at all. The owner-facing
request to reword both steps stays open and is repeated in this iteration's evaluation.
**Reversible:** yes

## iter-3 — goal-decomposer

**Ambiguity:** Priority-rubric rule 5 says "never bundle two risky journeys... a joint failure is
undiagnosable," but the iter-2 evaluator's binding next-step explicitly recommends building J-05
"Each close freezes one next-session manifest" together with J-06 "A frozen manifest never changes"
in one iteration. Nothing in the agent instructions or goal.md says whether a journey PAIR whose
acceptance steps are sequentially dependent (every J-06 step operates on a manifest J-05's own step 1
already produced) counts as "two risky journeys" for rule 5's purposes.
**We chose:** Treated J-05+J-06 as one cohesive feature examined from two acceptance angles (freeze-and-
stamp, then prove immutability) rather than two independent risky bets, and built them together at full
depth per the evaluator's explicit recommendation. The determining fact is dependency direction: J-06's
five steps all require J-05's manifest/columns to already exist, so splitting them into separate
iterations would not reduce diagnosability (a J-06-only iteration cannot even start without J-05's
schema) — it would only mean opening the same writer path twice. This reading is consistent with, not a
deviation from, priority-rubric rule 3 (unblocker) and rule 4 (smallest coherent spec).
**Reversible:** yes

## iter-3 — goal-evaluator

**Ambiguity:** AG-12 ends "a historical view never substitutes a newer manifest". After a regenerate,
`GET /api/compass` serves the NEWEST version for that same date and the UI lists version 1 only as a
stamp row — its frozen content is not viewable anywhere (auditor finding F4, explicitly left to me).
goal.md does not say whether "newer manifest" means a newer DATE's manifest or a newer VERSION of the
same date's manifest.
**We chose:** Read it as date-scoped, not version-scoped: serving the newest version for the SAME
as-of is in-spec, because J-06 step 4 explicitly requires that "version 2 appears… version 1 remains
readable and byte-identical… and the UI lists both versions with their stamps", and J-08 step 3 is
where the date-substitution rule actually lives ("never a newer manifest's contents" for a historical
date D). Recorded as OK in the anti-goal table rather than as a violation.
**Reversible:** yes

## iter-3 — goal-evaluator

**Ambiguity:** J-01–J-04 carry `evidence_makeup: true` for a missing `[NEW]` walkthrough. Methodology
A.7's clearing rule says the flag clears "the moment a fresh capture lands — whatever the outcome", and
fresh captures DID land this iteration (`J-01..J-04-verify.png`, `UT-J-01-result.png`). But the
specific make-up asked for — the `demo.sh --session-live` walkthrough, TC-32 — was not produced: the
iter-3 demo run recorded 8 iter-3 steps with an empty Journey column.
**We chose:** KEPT `evidence_makeup: true` on all four, reading the flag as tracking the outstanding
CAPTURE KIND (a walkthrough recording), not merely "any newer image". Clearing it would delete the only
scheduling hook for a make-up that is now two iterations overdue. The flag does not affect their
`passing` status either way.
**Reversible:** yes

## iter-3 — goal-evaluator

**Ambiguity:** J-06 step 2's "unavailable" basis disclosure is demonstrably unreachable (auditor B2,
reproduced), while J-06's other steps are met with evidence. The status vocabulary offers `failing`
("verified failing") and `partial` ("only some assertion steps passed") with no rule for a journey that
has both a proven defect and proven working parts.
**We chose:** Scored J-06 `partial` rather than `failing`, and wrote the unmet step out in full in
eval.md and in the journey note so nothing is hidden. `partial` records the real shape (regenerate,
versioning, immutability and the confirm gate all verified; one step unmet, two steps unrun); neither
label supports GOAL_ACHIEVED, so the choice costs nothing at the gate and preserves diagnosis detail.
**Reversible:** yes
