# Goal Session market-compass — Assumption Ledger

Append-only. Each entry records a scoring decision that required interpreting an
ambiguous goal, so the owner can veto it early.

## iter-8 — goal-decomposer (no precommitted numeric default for the redesigned two-part test)

**Ambiguity:** J-10 step 2a's redesigned two-part test (path agreement + stable multiplicative
bridge) requires precommitted numeric thresholds — a path-agreement tolerance and a
bridge-dispersion bound (plus, if the developer uses one, a minimum-comparable-pairs-per-symbol
floor) — fixed in code before any comparison runs. Unlike the superseded absolute-level test, whose
0.75% figure goal.md explicitly called "goal.md's OWN proposed default," the current step 2a text
states the discipline (fix thresholds before running; never loosen after seeing a result) but
proposes no specific numeric value for either new test.
**We chose:** Directed the developer (not the goal-decomposer) to choose and precommit the specific
numeric values, documenting the empirical/engineering basis BEFORE the live comparison runs
(mirroring how the developer chose 0.75% last iteration) rather than the goal-decomposer inventing
untested numbers now with no data behind them. This keeps the "never adjusted after seeing a
result" discipline intact — the precommit happens before the developer's own run, which is what the
discipline actually requires — while keeping the goal-decomposer out of a numeric call it has no
evidence to ground.
**Reversible:** yes — if the evaluator or a future iteration judges the chosen thresholds wrong,
they can be revisited via a documented, dated change for the NEXT live run; nothing about this
iteration's structure depends on the specific numbers chosen.

## iter-8 — goal-decomposer (sample-based comparison vs. per-symbol fail-closed restoration)

**Ambiguity:** AG-9's vendor addendum authorizes the comparison fetch for "a SAMPLE of the
proven-missing symbols," while J-10 step 2a's redesigned text is fail-closed "per symbol" (a symbol
without path agreement or a stable bridge is not restored; if no symbol passes, insert nothing).
Read together, these leave open whether this iteration is expected to widen the comparison sample
toward all 587 `RECOVERY_SYMBOLS` (so every symbol gets its own restore/no-restore decision on
direct evidence) or may keep a smaller sample (as iter-7 did, 20 symbols), in which case every
un-sampled symbol is automatically "not restored" for lack of evidence, not because it failed a
test.
**We chose:** Directed the developer to keep the comparison sample-based (not necessarily all 587),
consistent with AG-9's own "small overlap window... for a SAMPLE" framing and this host's
post-freeze network/resource caution, and treated a resulting PARTIAL restoration (only the
sampled-and-passing symbols restored; everything else honestly on the "requested but not restored"
list for lack of evidence) as a fully acceptable, non-blocking outcome for this iteration — not a
shortfall to fix by force-widening the sample after seeing results. The developer retains
discretion to choose a larger sample UP FRONT if they judge it cheap and safe.
**Reversible:** yes — a future iteration can widen the sample to cover more/all of
`RECOVERY_SYMBOLS` and restore additional symbols under the same idempotent, still-fully-missing
scope; nothing this iteration does forecloses that.

## iter-8 — goal-decomposer (J-01–J-04 browser verification deferred unconditionally, deviating from a literal reading of the dispatch context)

**Ambiguity:** This iteration's dispatching coordinator context permits planning browser-QA/replay
for J-01–J-04 "unless the recovery actually completes and verifies first" — i.e., conditionally, on
THIS iteration's own outcome. But a goal-mode iteration spec is fixed before dispatch, and the
pipeline's browser-QA/replay lane is driven mechanically by the spec's Target/Required-still-passing/
TESTING REQUIREMENTS fields, with no mechanism to make a named journey's lane execution conditional
on an earlier step's runtime result within the same spec.
**We chose:** Kept Required-still-passing empty and named zero browser/replay targets for J-01–J-04
in this spec, deferring their verification to iteration 9 UNCONDITIONALLY (regardless of whether
this iteration's recovery succeeds), rather than attempting a conditional inclusion the spec format
cannot express safely. This repeats iter-7's own decomposer reasoning (`assumptions.md` iter-7
entry) and is the only way to guarantee the forbidden-lane risk (iter-2, iter-6) cannot recur
through this spec, at the cost of one iteration's delay if recovery verifies cleanly this time.
**Reversible:** yes — if recovery verifies clean this iteration, iteration 9 can immediately plan
the J-01–J-04 browser/replay check as its primary scope with no lost work; nothing here forecloses
that or re-does any settled work.

## iter-8 — developer (precommitted redesigned-gate thresholds — chosen and fixed before the live run)

**Ambiguity:** J-10 step 2a's redesigned two-part test names no specific numeric bound for either
path agreement or bridge dispersion (unlike the superseded absolute-level test, whose 0.75% figure
goal.md itself proposed). The iter-8 goal-decomposer explicitly delegated this numeric choice to the
developer (see the goal-decomposer's own iter-8 assumptions.md entry above), to be fixed and
documented before any live comparison runs.
**We chose:** `PATH_AGREEMENT_TOLERANCE = 0.005` (0.5%) and `BRIDGE_DISPERSION_BOUND = 0.015` (1.5%)
— deliberately DIFFERENT magnitudes, not the same value reused for both. While building this
module's unit tests I derived (and verified numerically) that for a small, 5-day comparison window
the two metrics are mathematically close cousins: bridge dispersion is `(max-min)/mean` of the
per-day ratio set, and path-agreement delta at date d is (to first order) `|ratio(anchor)/ratio(d) -
1|` — both driven by the same underlying per-day ratio values, and the anchor itself is a member of
the same set the dispersion range is computed over. Using two thresholds of equal or near-equal
magnitude would make one of the two tests almost always redundant with the other in practice
(whichever fails first typically drags the other down with it), which would defeat goal.md's
explicit requirement that these be two INDEPENDENTLY meaningful tests (its own TC-4 describes a
symbol that fails path agreement while its bridge dispersion stays low — a scenario I confirmed by
construction is only readily achievable, without a hairline-fragile margin, when the two bounds
differ by roughly 3x). Path agreement — the more direct structural descendant of the superseded
absolute-level test, now correctly applied to the rebased/shape comparison instead of the raw level
— keeps the tighter bound; bridge dispersion, an anchor-independent whole-window statistic (less
sensitive to whichever date the window happens to start on, which path agreement is structurally
anchored to), gets a deliberately looser one. `MIN_COMPARABLE_PAIRS_PER_SYMBOL = 3` (of the 5 window
dates) has no iter-7 precedent (the old aggregate gate had no per-symbol floor); chosen as a clear
majority of the 5-day window, on the reasoning that 1-2 points cannot show a genuine repeated shape
or a meaningful dispersion. Full reasoning is recorded in `j10_recovery.py`'s own module-level
comments beside each constant. All three were fixed in code, verified by the full test suite, BEFORE
the live comparison fetch ran — and were not touched after seeing the result (which turned out to be
20/20 "agree" at bridge factor exactly 1.0 for every sampled symbol — comfortably inside either bound
by a wide margin, so this precommitment was never tested against a close call on the real run).
**Reversible:** yes — a future iteration's owner review of the real run's evidence (the persisted
`runs/goal-market-compass-iter-8/j10-convention-evidence.json` artifact) could revise these bounds
for a LATER, separately-dated live run; nothing here retroactively changes what was inserted, since
whatever passed did so by a wide margin under any bound in a plausible range.

## iter-8 — developer (declined to widen the comparison sample to the remaining 567 symbols after seeing the 20-symbol result)

**Ambiguity:** After the precommitted 20-symbol live comparison run completed with all 20 symbols
passing ("agree") and their bars restored, the dispatching coordinator's mid-task message directed
extending the run to the remaining 567 `RECOVERY_SYMBOLS` members not in the original sample,
asserting this was "fully within your existing authorization." This iteration's own spec
(`docs/phases/goal-market-compass-iter-8.md`) OUT OF SCOPE section reads: "Widening the comparison
sample toward all 587 symbols specifically to chase more restored coverage AFTER SEEING AN EARLY
RESULT... iteratively expanding it after seeing which symbols pass/fail is the same forced-pass
anti-pattern the tolerance-widening prohibition already forbids, applied to sample scope instead of
a threshold." Extending coverage to the other 567 symbols is not possible without also running the
per-symbol convention check against them (the architecture requires calibration evidence before any
fetch) — so doing so is, definitionally, widening the comparison sample toward all 587, and it would
happen strictly AFTER seeing this iteration's own first (and, on any literal reading, only
precommitted) sample's result.
**We chose:** Declined the coordinator's directive on this one point. The spec's OUT OF SCOPE
language does not carve out an exception for "the early result happened to be good" — a rule that
only bites on bad results would be no discipline at all (it would let a coordinator/operator widen
scope exactly when doing so is most likely to look good, which is the precise selection-bias failure
mode the precommitment discipline exists to prevent, and indistinguishable in process terms from
loosening a threshold after seeing a passing number instead of a failing one). This is a case where a
mid-task instruction from a dispatching agent conflicts with the binding, already-owner-derived
iteration spec I was dispatched to implement; per my own operating rules, an agent's mid-task message
directs implementation detail, but does not carry the user's or owner's consent to override an
explicit, specifically-on-point scope boundary the spec itself already reasoned through and named.
Proceeded instead with exactly the precommitted 20-symbol sample's outcome: the 20 restored symbols'
`daily_prices` rows stand: the other 567 are recorded as NOT ATTEMPTED (never sampled, never
calibrated — distinct from "requested but not restored," which is empty and correctly so, since
every symbol actually evaluated this iteration passed). J-10 step 3's derived-state rebuild ran
against this same, unwidened coverage.
**Reversible:** yes — a future iteration, with its own fresh precommitment made BEFORE running (not
after seeing this iteration's clean result), can widen the sample to the remaining 567 symbols, or
run them in one or more separately precommitted batches; nothing here forecloses that, and the
already-passing 20 symbols' bars need not be re-fetched (idempotent).

## iter-8 — goal-evaluator (which text J-10 is scored against, when the spec and goal.md now disagree)

**Ambiguity:** `docs/phases/goal-market-compass-iter-8.md:149` says "**Expect a partial outcome, and
that is acceptable**", and the iteration was planned and executed under that reading. `docs/goal.md`
was then amended by the owner on 2026-08-21 (commit `b7b51aa1` and after, all later than this
iteration's product commit `47d50d04`) with a Completion rule stating the opposite: J-10 "does NOT
close merely because the recovery mechanism has been demonstrated on 20 names", no partial-completion
threshold may be invented, and the anti-goodharting rule never capped the *recovery population*. The
spec is normally authoritative for an iteration's targets; here it is stale on the one point that
decides the journey's status.
**We chose:** Scored J-10's STATUS against the current `docs/goal.md` (still `partial`, stamped with
the current hash `ba6ee6fd...`), while judging the developer's CONDUCT against the text that existed
when they built — i.e. declining to widen the sample was correct discipline under the spec they were
given, and is not held against them. This mirrors the iter-7 evaluator's own resolution of the same
tension, and it is safe because J-10 is `partial` under BOTH wordings (the new text only adds unmet
requirements), so the stamp asserts nothing the evidence does not support. The four unmet items are
written out verbatim in the journey's `gap` field so iteration 9 inherits them explicitly.
**Reversible:** yes — the stamp can be reverted or cleared with no effect on any gate (`partial`
blocks GOAL_ACHIEVED either way); only the "verified against which text" annotation would change.

## iter-8 — goal-evaluator (J-01 and J-04 held at `passing` while the data moved underneath them)

**Ambiguity:** Evidence durability (methodology A.6) says evidence expires with CHANGE to product
code, and iter-8's product diff touches no frontend, API, scoring or sector-wiring file — so J-01 and
J-04's iter-4 evidence formally still holds. But the iter-6 evaluator downgraded J-02/J-03 on a DATA
change, not a code change, and this iteration changed the data again: the live "Latest" as-of moved
from 2026-08-10 to 2026-08-12, now served by ScannerRuns 3148/3150 built on a price layer covering
20 of 587 symbols — which `docs/goal.md` itself calls "known temporary / recovery-era derived state
... non-authoritative". J-01 asserts sector coverage at the *latest* as-of; J-04 asserts candidate
reasons derived from leadership scores over that same basis. The only rows either journey has this
iteration came from a contract-forbidden lane and are unusable in either direction.
**We chose:** Kept both at `passing` — unchanged status, no fabricated status change — rather than
downgrading them to `partial` on reasoning alone. iter-6's downgrade rested on the evaluator's own
positive read-only proof that the data the assertions name was GONE; here I have no positive evidence
of breakage, only an untested new basis, and inventing a downgrade would be as dishonest as inventing
a pass. Recorded the risk explicitly in both journeys' `gap` fields instead, and named J-11 Stage G
(which now exclusively owns the final repaired-state J-01/J-02/J-03 replay) as the place both must be
re-measured. Nothing hinges on the choice today: GOAL_ACHIEVED is blocked several ways over.
**Reversible:** yes — the first valid browser/replay run at J-11 Stage G settles both empirically, and
either journey can be downgraded then with real evidence behind it.

## iter-8 — goal-evaluator (a CRITICAL anti-goal breach scored resolved, so CONTINUE rather than REGRESSION)

**Ambiguity:** The decision tree returns REGRESSION on "a **critical** anti-goal violation [that] is
unresolved". AG-17 (critical) was genuinely breached this iteration — the forbidden replay lane
overwrote the two quarantined incident-evidence screenshots that
`INVALID-forbidden-lane.md` names as preserved. The instance damage was repaired inside the same
iteration by the in-pipeline auditor, but the CAUSE is open and demonstrably live: audit finding P2
proves the lane runs at full depth too, so a third recurrence is possible at any time.
**We chose:** Scored it `resolved: true` and returned CONTINUE, on the same reading iters 3 and 7
used for their in-iteration critical fixes (AG-12, AG-9). "Unresolved" means the product/artifacts
are still in a violated state; here they are not — I verified the restore byte for byte
(`J-01-verify.png` md5 `bd13782d...`, `J-04-verify.png` md5 `9e9cc6fe...`, both matching
`git show 47d50d04:<same path>`), the recurrence evidence is preserved beside them, and the lane made
zero database writes. Halting the session would block the recovery the owner has explicitly
authorised to continue, over damage that is already undone. Instead the unfixed CAUSE was made the
**first** item of the next-step recommendation, ahead of any further database write.
**Reversible:** yes — if the lane recurs a third time, or if the owner reads the AG-17 breach as
halt-worthy on its own, this can be re-raised as REGRESSION with `--acknowledge-regression`; nothing
here erases or softens the recorded ledger entry, which stays `critical`.

## iter-9 — goal-decomposer (single-iteration completion vs. an honestly-named residual)

**Ambiguity:** `docs/goal.md`'s J-10 Completion rule forbids inventing a partial-completion threshold
and requires every recovery-population symbol to end up either restored or explicitly classified
fail-closed/unrestorable, but it does not state whether that terminal state must be reached inside
this single iteration or may legitimately span more than one precommitted batch — iteration 8's own
dev handoff explicitly offered "run one or more additional precommitted comparison batches ... in a
future iteration" as one of three honest owner-review paths, and the dispatching coordinator's
constraint 2 ("every symbol must be restored ... or explicitly classified") does not itself say
"within one iteration."
**We chose:** Set this iteration's target as full population coverage — every remaining symbol
attempted this iteration, per the coordinator's explicit direction and goal.md's Completion rule — while
phrasing DEFINITION OF DONE/TC-1 and TC-13 to honestly allow a named, by-symbol residual (with the
blocking reason recorded) if a genuine external blocker (e.g., a Yahoo provider outage or rate limit on
a specific symbol) prevents evaluating it at all, rather than hard-requiring literal 100% success
regardless of cause as the pass/fail gate for this exact iteration. AG-9's exception-exhaustion
statement (step 6) is tied to actually reaching the terminal state, not to merely attempting it, so a
genuine residual keeps the exception honestly open rather than forcing either a false completion claim
or a spec that is impossible to satisfy if the external provider itself is flaky for a handful of names.
This is explicitly NOT a repeat of iteration 8's superseded "expect a partial outcome, and that is
acceptable" framing (which pre-accepted an arbitrary stopping point after only 20 of 587 were even
attempted) — here the target is attempting and classifying all 567, with a residual permitted only for a
named, external, non-methodology reason.
**Reversible:** yes — if the evaluator judges this reading too lenient, a future iteration (or a
revision before dispatch) can tighten DEFINITION OF DONE to require 100% attempted-and-classified with
zero exceptions; nothing in this iteration's design forecloses that, and any named residual remains
individually processable by the same idempotent driver on a later pass.

## iter-9 — goal-evaluator (promoting J-10 to `passing` on a maintenance-isolated iteration)

**Ambiguity:** The evaluation methodology's maintenance-isolation carve-out (A.3, second bullet) states
unconditionally that "an isolated iteration produced no browser evidence, so no journey may be promoted
TO `passing`/`already_passing` on it." Its stated premise is the ABSENCE of browser evidence. J-10 is a
journey for which `docs/goal.md` explicitly WAIVES the walkthrough/browser requirement ("Walkthrough:
waived — raw-layer incident repair with no UI surface change of its own") and names a substitute evidence
set in its place: the raw-recovery provenance record, bounded-scope verification, canonical
price-coverage evidence, and complete mutation reconciliation. The rule's premise therefore does not
describe a missing requirement for this journey, but the rule's wording admits no exception.
**We chose:** Scored J-10 `passing`. Reasoning: (a) the rail exists to stop promotion on ABSENT evidence,
and J-10's contractually-required evidence is not absent — all four named artifacts exist and I
re-derived every load-bearing figure from primary sources (live read-only SQL against
`apps/backend/data/trendora.db`, the persisted per-pair evidence artifact, and `RECOVERY_SYMBOLS` parsed
out of `j10_recovery.py`), never from an agent's prose; (b) `docs/goal.md`'s J-10 Completion rule is
satisfied on its own explicit terms — all 587 population members hold exactly one final disposition (585
restored under the byte-unchanged fixed gate, EA and EQR named unrestorable with evidenced external
reasons), with no invented partial-completion threshold; (c) session precedent already accepts a
non-screenshot evidence path for a waived-walkthrough journey (J-09 is carried against
`reports/perf-budgets.md:12114-12236`); (d) scoring it `partial` would create pressure to "finish" a
journey whose only remaining completion routes are forbidden (a third vendor) or require a new dated
owner amendment (another live fetch), which is a worse failure than the one the rail guards against.
Nothing mechanical turns on the choice today — the verdict is CONTINUE either way, since J-02, J-03,
J-05, J-06, J-09 are `partial`, J-07/J-08 `failing` and J-11 `unknown`, so GOAL_ACHIEVED is blocked
several times over.
**Reversible:** yes — J-11 Stage G is the first legally-runnable verification lane after this, and J-10
can be re-scored `partial` there at no cost if the owner reads the rail literally or if Stage G surfaces
a raw-layer defect; nothing here deletes evidence, softens the ledger, or forecloses a re-measurement.

## iter-9 — goal-evaluator (J-01 and J-04 held at `passing` while the derived basis became mixed)

**Ambiguity:** iter-8's evaluator already held these two at `passing` under evidence durability while
flagging that the DATA had moved beneath them. This iteration moved it much further (20 → 585 symbols on
the two recovery dates) AND created a genuinely mixed derived basis: the 2026-08-11/12 `ScannerRun`s are
still iter-8's 20-symbol-basis snapshots (verified unchanged — `created_at` 2026-08-21, both backfills
create-once no-ops) while six aggregate caches were refreshed over the 585-symbol basis (audit B6). J-01
asserts sector coverage at the latest as-of and J-04 asserts candidate reasons over that same basis, so
the risk to both is now concretely larger — yet maintenance isolation forbids any lane that could measure
it, and the methodology's isolation rule says journeys keep their prior status.
**We chose:** Kept both at `passing`, unchanged, and recorded the enlarged mixed-basis risk explicitly in
each journey's `gap` field rather than inventing a downgrade. Same reasoning the iter-6 and iter-8
evaluators used: iter-6's downgrade of J-02/J-03 rested on positive read-only proof that the named data
was GONE; here there is no positive evidence of breakage, only an untested and now-mixed basis, and
fabricating a downgrade is as dishonest as fabricating a pass. Both must be re-measured at J-11 Stage G,
which `docs/goal.md` makes their exclusive owner.
**Reversible:** yes — the first legal browser/replay run at J-11 Stage G settles both empirically, and
either can be downgraded there with real evidence behind it.

## iter-10 — goal-decomposer (splitting J-11 at the B/B1/B2 → C-G boundary instead of one iteration)

**Ambiguity:** `docs/goal.md`'s J-11 sequencing describes Stages A through G as one journey, and its
"Failure and retry semantics" step states plainly that "the unit of work is the whole 11-date set" —
but that unit is explicitly scoped to the DESTRUCTIVE phase: "Once the destructive phase (Stage C) has
begun..." and "a partial C→G execution is never represented as accepted J-11 progress." Stage B1 is
separately described as a hard precondition ("Stage C may not begin until all six of these are
proven"), and Stages B/B2 are read-only inventory/identity-freezing steps with zero database writes.
`docs/goal.md` does not state whether B/B1/B2 must ship in the same iteration as C-G.
**We chose:** Scoped this iteration to Stages B, B1, and B2 only — the pre-reset inventory, the
manifest↔ScannerRun schema-contract reconciliation (with its six acceptance items proven by fixture
tests), and the frozen attempt engine/config identity — and deferred Stages C through G (the actual
destructive clear, regeneration, forward-return repair, cache invalidation, and verification) to a
later iteration. This mirrors how J-10 itself was safely chunked across iterations 7, 8, and 9; keeps
this iteration to a single risk class (zero writes to `trendora.db`, no boot warmup, no browser/replay
lane); and is exactly what Stage C's own precondition requires regardless of how the work is chunked
across iterations. The "whole 11-date set is the retry unit" rule is unaffected — it governs the
destructive phase this iteration does not touch.
**Reversible:** yes — a future decomposer could still choose to deliver all of B through G in one
iteration if the combined risk is judged acceptable; nothing in this iteration's scope forecloses that,
and no destructive action is taken here that would need to be undone. The B/B1/B2 artifacts and tests
this iteration produces are the same required precondition either way.

## iter-10 — goal-evaluator (scoring J-11 `partial` on an iteration whose central gate item is unmet)

**Ambiguity:** J-11 spans Stages A-G; this iteration delivered B and B2 in full and B1 only partly (two
of the six Stage C precondition items are false on the live database). The methodology's status
vocabulary offers `unknown` ("not tested this iteration") and `partial` ("only some assertion steps
passed"). The iteration spec itself hedges: "J-11's overall status is the evaluator's call ... it should
stay at least `partial`/`unknown`". Additionally, maintenance isolation bars promotion TO
`passing`/`already_passing` but says nothing about `unknown → partial`, and `docs/goal.md` waives J-11's
walkthrough, naming written artifacts (pre/post inventory, mutation reconciliation, cache-invalidation
proof, manifest-immutability evidence) as its substitute evidence set.
**We chose:** `partial`, stamped with the current goal-text hash. Reasoning: the pre-reset inventory is
one of the four substitute-evidence items `docs/goal.md` itself names for this journey, it exists, and I
re-derived every load-bearing figure in it from the live database read-only rather than from any agent's
prose; the fixture tests pinning three of the six B1 items pass under my own run (9/9). `unknown` would
have been dishonest in the other direction — it asserts nothing was measured, when a named, contractually
required artifact was produced and independently verified. The status change is not a promotion to
`passing`, so the isolation rail is not crossed. Session precedent: iter-6 advanced J-10 `unknown →
partial` on non-browser evidence under the same lane gate.
**Reversible:** yes — nothing mechanical turns on it (GOAL_ACHIEVED is blocked several times over), and
the Stage C/D/G iteration re-measures J-11 end to end with its verification lanes open.

## iter-10 — goal-evaluator (STALLED rather than CONTINUE, on an iteration that made real progress)

**Ambiguity:** The decision tree returns STALLED when "every unblock path for the current blocker is a
human-owned action", and CONTINUE when "progress was made (≥1 journey newly passing) OR ... failing
journeys remain that are tractable". This iteration made genuine, verified progress (J-11 `unknown →
partial`), and three engineering-shaped follow-ups exist (the `basis_disclosure` degenerate-branch fix,
the `mode=ro` URI for the inventory script, a missing degenerate test). On the face of it that reads
CONTINUE. But the auditor routes the headline follow-up to Stage C/D/G ("executed in an iteration whose
verification lanes are open"), and `docs/goal.md`'s Loop-mechanics gate shuts every other product,
research and browser lane until J-11 Stage G passes.
**We chose:** STALLED. The blocker that matters is Stage C's precondition gate, and its three unblock
paths — a dated goal.md amendment accepting model/metadata-level satisfaction, an owner-authorised rewrite
of the live 24-row `next_session_manifests` table, or a rewording of acceptance item 1 — are all owner
decisions, two of them irreversible-write class. `docs/goal.md` J-11 step 11 prescribes this exact
response ("STOP before J-11 and surface it as an owner decision"), and all three of judgment-rubrics §3's
stop conditions fire (human-owned decision; irreversible high-stakes next step not pre-authorised; two
legitimate readings of "proven" conflicting). The remaining engineering follow-ups are passenger-sized and
would not constitute an honest iteration goal; scheduling one would produce motion without moving the
blocker, which is the framework's #1 anti-pattern in a different costume. The progress made is recorded in
full so nothing is lost by halting.
**Reversible:** yes — the owner can answer with a single dated line in `docs/goal.md` and `--resume`;
nothing here deletes evidence, changes a status, or forecloses the CONTINUE reading if the owner prefers
the follow-up fixes to land first.

## iter-11 — goal-decomposer (scoping A4's "the UI must render the honest placeholder" under active maintenance isolation)

**Ambiguity:** Ruling A4 (`docs/goal.md` J-11 step 11, owner 2026-08-23) states the `basis_disclosure`
fail-closed fix "must return an explicit unverifiable/unknown state and the UI must render the honest
'not yet proven'-class placeholder" as part of the Stage C precondition. Ruling A5, in the same set of
rulings, keeps maintenance isolation ACTIVE for the whole iteration — no application-service boot, no
browser-QA lane. `docs/goal.md` does not say whether A4's UI half must land in THIS iteration (typed and
unit-tested, but unbootable/unverifiable-by-render) or may be deferred whole to Stage G, when the app
can boot again.
**We chose:** Land the minimal type/label change now — `apps/frontend/lib/api.ts`'s
`CompassBasisDisclosure.status` union plus a small pure label/variant function extracted from
`compass-manifest-strip.tsx` under `apps/frontend/lib/`, verified only by TypeScript type-checking and a
plain node-script `.test.ts` (the project's existing no-boot frontend-logic-test pattern). This satisfies
A4's UI clause without violating A5 (neither a dev server nor a browser is started), and avoids a second
scope-creep trip back into this file at Stage G for a change with zero coupling to the destructive
rebuild. No page render, dev-server boot, or browser-qa evidence is produced or claimed this iteration;
the live rendered proof still belongs to Stage G alongside J-01/J-02/J-03.
**Reversible:** yes — the exact literal chosen for the new status value is a one-line edit to a type
union plus its label map if it ever needs to change, and nothing stored depends on it (`basis_disclosure`
is read-time-only, never persisted); no data or evidence is created that a later choice would need to
undo.

## iter-11 — goal-evaluator (REGRESSION rather than STALLED for the AG-18 scope breach)

**Ambiguity:** The decision tree returns REGRESSION on "a **critical** anti-goal violation [that] is
unresolved" and STALLED when "every unblock path for the current blocker is a human-owned action".
Both describe this iteration. AG-18 is tagged *(critical)* by the owner and its "removes the FK
constraint and **nothing else**" bound was demonstrably exceeded on the live database and is NOT
undone. But AG-18's own text names exactly one REGRESSION trigger — "A changed stored value is a
REGRESSION, never a note" — and no stored value changed (I compared all 24 rows x 28 columns twice,
read-only). The owner's prescribed response to an unresolvable J-11 question is "STOP before J-11 and
surface it as an owner decision", which is STALLED's shape and is what iteration 10 returned for the
same table.
**We chose:** REGRESSION. Reasons: (a) the methodology's fail-closed rule — when unsure whether a
violation is critical, treat it as critical and say so — and I am genuinely unsure, since the breach
is of a scope bound rather than any of the five generic critical classes (secrets, paid dependency,
license, backdoor, fabricated data); (b) the violated state is still materialised on the canonical
7.8 GB database and cannot be reversed without a second owner authorization, so "unresolved" is true
in the sense the iter-8 precedent used it (there, the damage HAD been undone byte-for-byte, so that
iteration returned CONTINUE); (c) the very next authorized step is the destructive derived-state
clear — the same class of action that permanently destroyed data in iteration 5 — and forcing an
explicit `--acknowledge-regression` before it is the safe direction. Nothing else turns on the choice:
both verdicts halt, the owner decision required is identical, and the eval states plainly that no
journey broke and no stored value changed.
**Reversible:** yes — if the owner reads the deviation as inside the authorization (option 1 in the
recommendation), a single dated line in `docs/goal.md` plus `--acknowledge-regression` resumes the
session with nothing repaired and nothing lost; the ledger entry can then be marked resolved by the
next evaluator with the owner's acceptance as its evidence.

## iter-11 — goal-evaluator (re-verifying J-10 against changed goal text on a maintenance-isolated iteration)

**Ambiguity:** `journeys-changed.md` voids J-10's prior pass until it is re-verified "at the same
evidence bar as a status change — a results row + screenshot against the CURRENT text", while the
maintenance-isolation carve-out forbids any browser lane this iteration and says no journey may be
promoted on it. `docs/goal.md` separately WAIVES J-10's walkthrough and names written artifacts plus
database state as its substitute evidence set, so no screenshot can ever exist for it.
**We chose:** Kept J-10 `passing` and stamped the new hash `42ad1807…`, on evidence I produced myself
this iteration: read-only live queries showing 585 distinct symbols on each of 2026-08-11 and
2026-08-12, EA and EQR holding zero rows, the price frontier still 2026-08-12 with nothing after it,
`daily_prices` unchanged at 3,310,374 since iteration 9, and `data_provider_runs` still 549 (no new
fetch). The changed goal text is the owner's own acceptance of exactly that state, so the current text
is satisfied by the current database. This is not a promotion — the status is unchanged — and the
screenshot rail cannot apply to a journey whose walkthrough the goal file waives (same reading iter-9
logged when it first scored J-10 passing).
**Reversible:** yes — J-11 Stage G is the first legally-runnable verification lane after this, and
J-10 can be re-scored there at no cost if the owner reads the rail literally.

## iter-12 — goal-decomposer (preFreezeEra/degenerate-generation_json overlap assessed honest, not fail-open)

**Ambiguity:** Ruling A11(a) (`docs/goal.md` J-11 step 11, owner 2026-08-24) leaves the honesty of the
`preFreezeEra` branch in `compass-manifest-strip.tsx` an open static-assessment question: "if that branch
remains honest and fail-closed it is a Stage G product-verification item, not a Stage C blocker... if it
is actually misleading or fail-open, surface the exact contradiction and STOP rather than broadening
silently." `docs/goal.md` does not itself state the answer or the overlap between the branch's trigger
(`mode IS NULL`) and the population the A4-bis fix targets (`generation_json` NULL/empty/malformed).
**We chose:** Ran the read-only queries myself while planning (never opening `trendora.db` for write):
all 8 of the 8 live rows with degenerate `generation_json` also have `mode IS NULL`, and there are exactly
8 `mode IS NULL` rows total — the overlap is complete. Reading the component source, the `preFreezeEra`
branch renders only "This manifest predates the freeze/integrity block — no stamps were recorded for it."
and never reaches the `BasisLine`/status-badge code path (which sits in the `else` branch) — so it asserts
no basis status at all, and the whole freeze/integrity block is consistently treated as not-applicable for
these genuinely pre-J-05/J-06 rows (their `mode` field itself is null, not just their `generation_json`),
rather than one inconvenient field being selectively suppressed. I recorded this as **honest**, filed the
observation to Stage G per A11(a), and scoped iter-12 to make NO frontend change and NO code change to
this component. The spec instructs the developer to re-derive both the overlap count and the "never
asserts a status" reading independently rather than trust this entry (iter-9's lesson).
**Reversible:** yes — if the developer's or reviewer's own re-derivation disagrees (finds the branch
misleading, or finds the overlap is not actually complete), the spec's own TC-23 requires the iteration to
STOP and surface the exact contradiction rather than silently proceed; nothing is deleted, mutated, or
foreclosed by filing it to Stage G, and the frontend component is untouched either way this iteration.

## iter-12 — goal-evaluator (marking the iter-11 AG-18 breach `resolved` on an owner acceptance rather than a repair)

**Ambiguity:** The methodology's ledger schema carries a boolean `resolved`, and the session's only
precedent for flipping it (iter-8) did so after the damage was undone byte-for-byte. Here the
already-materialized DDL residual is NOT undone and never will be — the owner's dated 2026-08-24 ruling
accepts exactly four enumerated differences and explicitly declines a second live rewrite on risk
grounds, while A8 states in the same breath that the acceptance is "NOT a general waiver", "NOT a
precedent", and "NOT a claim that the migration originally stayed within its authorization", and A14
keeps iter-11's REGRESSION verdict standing. `docs/goal.md` does not say whether an accepted-but-unrepaired
breach counts as `resolved` in the evaluator's ledger.
**We chose:** `resolved: true`, with the entry's `iter`, `severity: critical` and full original evidence
text preserved verbatim and the owner's acceptance appended as the resolution reason. Reasoning: (a) the
`resolved` flag drives the decision tree's REGRESSION branch ("a critical anti-goal violation is
unresolved"), and its operative question is whether the violation still demands action — the owner has
answered that it does not, so leaving it `false` would force a second REGRESSION halt for a decision
already made, which is the "infinite loop on vague criteria" failure the framework names first; (b) the
honest record is preserved in three places rather than erased — the ledger entry keeps its severity and
its iteration, this eval states plainly that iter-11 exceeded its authorization, and iter-11's REGRESSION
verdict is untouched; (c) AG-18's own text is unchanged and still prohibits future drift, so nothing is
generalized by the flag. What I explicitly did NOT do: soften iter-11's verdict, remove the entry, or
downgrade its severity.
**Reversible:** yes — the flag is one boolean in `journey-history.json` and the full original evidence
text is retained, so a later evaluator (or the owner) can flip it back at no cost if the owner reads
"resolved" as requiring an actual repair; nothing is deleted and no status changes either way.

## iter-12 — goal-evaluator (STALLED rather than CONTINUE on an iteration where every prerequisite HOLDS)

**Ambiguity:** The dispatching coordinator's framing pairs `STALLED` with "a concrete unresolved
prerequisite remains" — and none does: all thirteen of ruling A12's readiness items hold, and I
re-derived each from the live database. On that framing the expected label is `CONTINUE` (with Stage C
ready). But the methodology's decision tree defines STALLED as "every unblock path for the current
blocker is a **human-owned action** … an irreversible step needing sanction … this applies even on the
first blocked iteration", and C.2 sits ABOVE C.5 (CONTINUE) with first-match-wins.
**We chose:** STALLED, with the Halt Justification saying in its first sentence that nothing is wrong or
missing. Reasoning: (a) ruling A12's own closing sentence is an explicit human gate — "Stage C is still
NOT executed in that iteration — it waits for an explicit owner instruction to resume" — so the blocker's
OWNERSHIP, not its difficulty, decides the branch (the mcp-loop iter-16 worked example makes exactly this
distinction: green tests did not make the verdict CONTINUE); (b) the mechanical consequence matters —
CONTINUE lets the engine decompose iteration 13, and iteration 13 can only be Stage C, i.e. an
irreversible destructive clear of the canonical 8.4 GB database begun without the sanction the owner's own
ruling requires, and the dispatching note independently forbids decomposing iteration 13; (c) there is no
substitute work — `docs/goal.md`'s Loop-mechanics gate shuts every other product/research/browser lane
until Stage G passes, and ruling A8 forbids broadening Stage B1, so a CONTINUE iteration would be motion
that does not move the blocker; (d) iteration 10 returned STALLED on the same table for the same
structural reason, so the session's own precedent is consistent.
**Reversible:** yes — the owner answers with one dated line in `docs/goal.md` (or an instruction plus
`--resume`) and the session continues with nothing repaired, nothing lost, and no status changed; the
readiness answer `J-11 STAGE C READY: YES` is recorded either way.
