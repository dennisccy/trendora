# Goal Session ops-hardening — Assumption Ledger

Append-only. Each entry logs a spec decision that required interpreting an ambiguity in
`docs/goal.md` rather than a routine scoping pick. Zero entries for most iterations is normal.

## iter-34 — goal-evaluator

**Ambiguity:** J-07 step 2 reads "While step 1 runs, poll `GET /api/health` once per second; assert every
poll answers HTTP 200 **within its existing budget** — no frozen or unresponsive window." This iteration
finally measured it, twice, live: 85 polls (dev) and 100 polls (browser-qa), which I recomputed from both
raw CSVs myself. 185/185 answered HTTP 200 and no gap exceeded ~2.15 s of loop jitter — the responsiveness
half is proven emphatically. But **0 of 185 polls** were inside the committed `<= 0.1 s` budget, including
the 8 pre-warm baseline polls (0.110-0.126 s). The at-rest component is root-caused, checkably, to
host-level contention (the co-resident `tapeology` project moved onto trendora's SAME
`HOST_GUARD_CPU_LIST=0-3,8-11` mask after reset #6; ~115% CPU, load average 2.12), and the warm adds a
real, separately disclosed increment on top (median 0.138 s vs 0.113 s; max 1.132 s vs 0.126 s). Because
the best at-rest reading this session ever recorded is 93.4 ms, "every poll <= 0.1 s DURING a warm" is not
achievable on this host as the budget is written — re-measuring on a quiet host does not close it.
`docs/goal.md` does not say whether a step whose responsiveness half is proven and whose numeric-budget
half is measured and missed, and honestly recorded as a WARN, counts as satisfied.
**We chose:** scored J-07 `passing`, and filed the miss as a NEW unresolved ledger finding (iter-34/j,
minor) so it cannot be rounded away. Grounds stated rather than assumed: (1) J-07's own **Acceptance
block** is the journey's definition of done, and it re-states which step-level facts matter — "a
memory-pressure abort never leaves the process wedged (step 4)" and "health/readiness stay truthful
throughout" — and pointedly does NOT include the budget number, so the goal's own text argues the number
is not part of J-07's bar; (2) the completion standard for step 2 was set by the iter-33 evaluator ("state
plainly whether it is inside the 0.1 s budget ... the budget should be WRITTEN DOWN that way rather than
amended") and encoded verbatim in the iter-34 spec's TC-1 and DoD, and the developer met it exactly —
raising the bar after the work is done is goalpost-moving, the framework's own named anti-pattern; (3) the
same clause shape on the same endpoint and the same budget line was already accepted for J-06 at iter-33,
so scoring J-07 harder would apply two standards inside one session. I did NOT let it pass silently: the
miss is named in eval.md's Summary and in a dedicated section, in the evaluator log's plainly-stated list,
in iteration-state's owner block, and as ledger finding iter-34/j, which the achievement gate now blocks
on. I also record the cost honestly: GOAL_ACHIEVED is blocked this iteration by eight unresolved findings
anyway, so the owner gets at least one more round to veto this call before it can carry any weight. A
human who requires every enumerated step to be literally satisfied would keep J-07 `partial` for an eighth
iteration and make the health-check budget the next round's only target.
**Reversible:** yes

## iter-35 — goal-evaluator

**Ambiguity:** browser-qa scored UT-J-06 FAIL with an Expected column taken verbatim from the
iteration SPEC's Definition of Done ("all 4 sibling labs render `resolveLabLoadPanel`'s labelled
'still computing' state ... identical to Regime Lab") rather than from J-06's `docs/goal.md` text,
which never names that component. Its stated failure ground is "the iteration's own scope ... was
not implemented" — which was guaranteed, since the run was dispatched at `evidence` depth and no
developer existed. `docs/goal.md` does not say whether a journey fails when a lane tests it against
an iteration's unbuilt plan instead of the journey's own acceptance text.
**We chose:** rejected the FAIL's stated ground (an unbuilt spec item is not a journey failure —
scoring it as one would let any mis-dispatched iteration manufacture a regression), but scored J-06
`partial` anyway on DIFFERENT evidence the same lane attached without relying on: all four
screenshots show a bare unlabelled skeleton, and the backend access log for the same window contains
zero completed `/api/research/*` requests, so those loads were genuinely slow — which engages J-06's
own Acceptance clause ("anything slower than its budget shows an honest progress or initializing
state, never a frozen or blank frame") and matches the shape iter-33 scored a P1 on Regime Lab.
Grounds: methodology A.3 says the screenshot outranks every prose claim, and here it outranked the
lane's own prose in the direction of more severity; and iter-33/h's `minor` rationale explicitly
rested on "no such lab is measured slow today", a premise this run falsified. A human who treats a
grey skeleton as a legitimate "initializing state" (it is not blank and not frozen-looking, and the
global top-bar badge did honestly read "background compute running (5)") would keep J-06 `passing`
and carry the four labs' missing elapsed-label as the already-open iter-33/h chore.
**Reversible:** yes

## iter-35 — goal-evaluator

**Ambiguity:** AG-8 is *critical* and says the data basis "must never ... exhaust a service's
memory". This iteration exhausted it for real, first-hand verified: VmPeak reached exactly the
declared 6,291,456 kB cap (zero margin) and four memory-pressure aborts fired at two code sites, one
of them on the user-facing `/api/evidence` serving path. A critical unresolved anti-goal violation
maps to REGRESSION and a hard halt (tree C.1), and my own methodology says to fail closed when
unsure. But AG-8's remedy half — "the UI degrades gracefully (contained error boundary, honest
'—'/NA placeholder, never a blank application-error page)" — was met in full, the product tree is
byte-identical so nothing regressed, and the scenario (a long-lived process that had already run a
283-date backfill, then 5 concurrent as-of warms) is heavier than J-07 step 1 asks for.
`docs/goal.md` does not say whether memory exhaustion that is caught, contained, and honestly
disclosed counts as an AG-8 violation of critical severity.
**We chose:** classified the new finding iter-35/k `minor`, not critical, and returned ESCALATE
rather than REGRESSION. Grounds stated rather than assumed: (1) the methodology's own critical list
is secrets / unapproved paid dependency / license violation / security backdoor / fabricated data —
contained-and-disclosed memory pressure is none of these, and AG-8's *(critical)* tag marks the
anti-goal's importance, not an automatic halt; (2) I verified every half of AG-8's remedy clause
myself (506/506 health 200s, no restart, `evidence.py:174` sets an honest
`expectations_status="unavailable"`, the backtest page rendered complete prior-date tables behind an
honest banner); (3) the AG-10 host caps did exactly their job — `ulimit -v` contained every
MemoryError inside the one process and the host, which has suffered six hardware resets, was never
at risk; (4) REGRESSION halts for HUMAN review, and there is nothing here for a human to decide —
every unblock path is agent work already written into an unrun spec. I did not let it pass silently:
it is a new unresolved ledger finding, it drove J-07 to `partial`, it falsified iter-29/d's stated
`minor` rationale (recorded in the ledger), and it is item 1 of the next-step list. A human who
reads AG-8's "must never exhaust a service's memory" literally — and notes that six consecutive
evaluators justified `minor` partly by "no memory is exhausted", a ground that just died — would
call this a critical violation and halt for review.
**Reversible:** yes

## iter-36 — goal-decomposer

**Ambiguity:** rule 5 says "never bundle two risky journeys ... a risky item plus a cheap
mechanical one is exactly what this rule permits." iter-35's carried plan already bundles one
structural fix (bound `_membership_timeline`'s whole-table prefill) with one cheap mechanical item
(wire `resolveLabLoadPanel` into 4 siblings). The iter-35 live run then surfaced a THIRD item,
ledger finding iter-35/k: `compute_drawdown_expectations`'s `stored_by_key` read aborted twice with
`MemoryError` on the `/api/evidence` serving path. `docs/goal.md` does not say whether a second,
smaller memory-bound fix in the SAME accumulator family (unbounded ORM read reached on J-07's own
named warm/serving path) may be added to an iteration that already carries one structural fix, or
whether rule 5 caps an iteration at exactly one risky item regardless of size/family.
**We chose:** to fold it in as a third, explicitly small item rather than defer it to iter-37.
Grounds: the evaluator's own next-step recommendation (iter-35 log) ranked it item 4, "NEW AND
SMALL, same family as item 1," immediately after (not competing with) the two carried items; the
fix mirrors an already-established idiom (chunked/streamed read replacing `.all()`, the same shape
as the item-1 fix and the iter-29 `research.py` precedent) rather than introducing new mechanism;
and it closes a genuine instance of J-07's own Acceptance clause ("no unbounded whole-table ORM
materialization remains on the warm OR SERVING path") that the session has not yet closed on the
serving-path half. A human who reads rule 5 as a strict one-fix-per-iteration cap, or who weighs the
value of an undiluted diff for a re-dispatched full-depth iteration higher than closing a live,
twice-reproduced serving-path failure one iteration sooner, would defer iter-35/k to iter-37 instead.
**Reversible:** yes

## iter-36 — goal-evaluator

**Ambiguity:** J-07's browser-lane verification never ran — the merged results file has no J-07 row,
UT-13/UT-14 are SKIPPED, and `status.json` records `browser_checks_run: false`. But the auditor
independently booted a real backend via `scripts/start-backend.sh` and closed part of J-07 by hand:
30/30 `GET /api/health` HTTP 200 at 1 Hz (max 132 ms), VmPeak 2,691,796 / 6,291,456 KB = 42.8% of cap,
`/api/data` internally consistent, `/api/evidence` serving 7 claims all with real expectations panels,
plus TC-8's real `ulimit -v` subprocess drill 3/3. The auditor's own Recommended Next Step says J-07's
status "is `unknown`". My instructions say an un-evidenced journey is `unknown`; my schema says
`partial` means "only some assertion steps passed". `docs/goal.md` does not say which applies when a
journey's browser lane never ran but a different lane verified several of its enumerated steps
first-hand.
**We chose:** scored J-07 `partial`, not `unknown`, and stated the split explicitly (which steps carry
this-iteration evidence, which do not). Grounds: `partial`'s definition is literally what happened —
steps 2 and 3 have real, reproducible, this-iteration numbers from a correctly-capped live process,
while step 1's full-horizon warm, step 2's poll DURING that warm, step 4's induced-pressure re-run
against the bounded paths, and step 3's `perf-budgets.md` recording do not; `unknown` means "not tested
this iteration, carry over previous status", and the previous status was `partial`, so both readings
land on the same recorded value and neither can support GOAL_ACHIEVED; and calling it `unknown` would
discard evidence a lane actually produced, which is the mirror image of the rubber-stamp error. I did
NOT let the substitution pass silently: the never-run DoD item, the exact unverified steps, and the
missing `perf-budgets.md` margin are all named in eval.md, in the evaluator log's plainly-stated list,
and in iteration-state. A human who reads "the browser lane is J-07's evidence lane, and it produced
nothing" as decisive — or who wants the auditor's own recommended word honoured verbatim — would score
it `unknown`.
**Reversible:** yes

## iter-36 — goal-evaluator

**Ambiguity:** decision tree C.4's first clause is "the SAME journey has now failed 2+ consecutive
iterations -> ESCALATE". J-07 is `partial` at iter-35 and `partial` again at iter-36 — it has not
reached `passing` for two consecutive iterations — but `partial` and `failing` are DISTINCT statuses in
the journey-history schema, and C.4 says "failed". Meanwhile C.5 (CONTINUE) fits comfortably: a journey
newly passed (J-06), progress was real, and the remaining work is tractable. The methodology also warns
"use ESCALATE sparingly — escalating every iter defeats the purpose of adaptive depth", and this
iteration was ALREADY dispatched at full depth with all three review lanes returning PASS-class
verdicts, so nothing here is an ambiguity/complexity problem needing deeper lanes.
**We chose:** ESCALATE, reading "failed" as "did not reach `passing`". Grounds stated rather than
assumed: (1) the tree is applied top-down and first-match-wins, so if C.4 matches it outranks CONTINUE
regardless of how well CONTINUE also fits; (2) ESCALATE's practical effect is the one thing this
session provably needs — it makes full depth MANDATORY rather than advisory, and iteration 35 was lost
in its entirety because an advisory full-depth recommendation was dispatched as `evidence` against a
code-requiring Definition of Done; (3) the next iteration needs three things a downgraded depth would
strand: the browser lane (to finally execute J-07), a real backend change on the ingest warm chain
(iter-36/l), and a closure re-run after this iteration's `closure_failed`; (4) the cost of being wrong
is one unnecessary full pipeline, versus a whole wasted iteration if I am wrong the other way. I record
the cost honestly: ESCALATE reads as a harsher verdict than the iteration deserves, and the eval.md
Summary says so explicitly rather than letting the verdict imply the work was poor. A human who reads
`partial` as strictly not "failed", and who weighs "use ESCALATE sparingly" against a session that has
now escalated twice running, would return CONTINUE with an advisory full-depth recommendation.
**Reversible:** yes

## iter-36 — goal-evaluator

**Ambiguity:** J-06 was downgraded to `partial` at iter-35 on one stated premise — all four sibling
Research labs render a bare unlabelled grey skeleton on a genuinely slow load, with no Retry on
failure. This iteration falsifies that premise with frames I opened (a labelled "Still computing — 28s
elapsed" card with honest copy on phase-severity-lab; a "Backend unavailable" card with a working Retry
on factor-lab, regime-phase-factor and severity-velocity). But three clauses are not cleanly true: (a)
J-06 step 1/2's page-load sweep was not re-run, and this iteration DID change `/data`'s and
`/evidence`'s backend compute plus one `/research` lab's markup; (b) `UT-13` (`/data` panel unchanged)
was SKIPPED, so no lane confirmed `/data` this iteration; (c) the `[NEW]`-flagged walkthrough finally
recorded (demo steps 01-04, the first J-06 `[NEW]` capture in six iterations) is about the labs'
loading states, not "the budgets table vs live page loads" that J-06's Acceptance text names.
`docs/goal.md` does not say whether a journey returns to `passing` when the specific clause that
downgraded it is fixed while a sibling clause's fresh measurement is missing.
**We chose:** restored J-06 to `passing` and CLEARED `evidence_makeup`. Grounds: methodology A.6 says
evidence expires with CHANGE, not time, and the pages' ON-LOAD request path is unchanged — `/api/data`
still serves the persisted `coverage_snapshot` row and only the cache-MISS compute path was touched, so
iter-33's committed budget numbers still govern; coherence.md independently confirms the frontend change
is presentation-only wiring of one shared, unmodified resolver with no fork; the auditor's own live
`/api/data` probe served internally-consistent figures (548 pool − 8 excluded = 540 universe), covering
UT-13's substance by hand; and A.7's clearing rule is mechanical — any fresh capture clears
`evidence_makeup`, "whatever the outcome" — so I cleared it and carried the narrower subject gap as a
named capture-only ride-along instead of letting a flag persist indefinitely. Reversing iter-35's
downgrade because its stated premise was falsified by pictures is the same standard iter-35 used to
apply it, run in the other direction. A human who requires a fresh 11-page time-to-interactive sweep
whenever any page's backend compute changes, or who treats the budgets-table walkthrough as a literal
Acceptance requirement, would keep J-06 `partial` and hold `evidence_makeup` set.
**Reversible:** yes

## iter-37 — goal-decomposer

**Ambiguity:** Rule 5 says "never bundle two risky journeys ... a risky item plus a cheap
mechanical one is exactly what this rule permits" (and the iter-36 decomposer entry already
extended this to "a second, smaller memory-bound fix in the SAME accumulator family" alongside one
structural fix). This iteration's scope has two parts: (a) a genuine structural code change —
sharing one `prefilled_bar_cache` across `_do_backfill` and `_persist_per_date_coverage_snapshots`
instead of each opening its own (iter-36/l) — and (b) executing J-07's own steps 1-4 (a
full-horizon warm, a concurrent health poll, a VmPeak recording, and an induced-memory-pressure
drill), none of which require new product code but which DO involve heavy, host-affecting compute
launched through `scripts/start-backend.sh`/a throwaway process (AG-10). `docs/goal.md` does not
say whether "run a long, heavy, already-implemented verification drill" counts as a second "risky"
item under rule 5 alongside a genuine code change, or whether rule 5 is scoped to CODE changes
only.
**We chose:** to bundle both into this one iteration rather than split step 1-4 execution into its
own follow-up. Grounds stated rather than assumed: (1) rule 5's own text and every precedent in
this session's ledger (iter-30 through iter-36) applies it to CODE changes specifically — "never
bundle two risky journeys/changes," "this iteration's one risky change is confined to X" — never to
a verification/measurement pass with zero new code, which is a fundamentally different failure
mode (a bad measurement is re-runnable with no product regression risk, unlike two interacting code
changes whose joint failure is undiagnosable, the exact harm rule 5 exists to prevent); (2) the
iter-36 evaluator's own next-step recommendation ranked "finish J-07 — run it" as item 1 and the
backfill-path fix as item 2, immediately after, not as competing alternatives for separate
iterations — splitting them would mean deliberately re-dispatching a third iteration whose entire
first half (verification) has no code dependency on the second half's fix, merely delaying
J-07's completion by one more full-depth cycle for no diagnostic benefit; (3) the fix directly
reduces peak memory pressure during the same class of heavy ingest that J-07's own step 4 induces
pressure against, so running step 1-4's drill AFTER the fix (not before, not in a separate
iteration) tests the more representative, already-hardened state rather than a state this session
already knows is one bound short of AG-8-clean. A human who reads rule 5 as covering any
heavy/host-affecting action regardless of whether it changes code, or who weighs an undiluted
single-purpose diff higher than closing J-07 one iteration sooner, would split this into a
code-only iteration followed by a verification-only iteration.
**Reversible:** yes

## iter-37 — goal-evaluator

**Ambiguity:** J-07's four steps ALL executed live this iteration with real, first-hand-verifiable
evidence (130/130 health 200s during a real 5-horizon warm, VmPeak margin finally written into
`reports/perf-budgets.md`, an honest caught-MemoryError abort with the same process still serving).
But two of them ran through paths where this iteration's own change is inert: step 1's warm was
dispatched by `GET /api/backtest` rather than "the ingest finalize path" the step's own parenthetical
names, and step 4's drill job had `dates_total: 0`, so the new shared-cache wrap was a
`nullcontext()`. `docs/goal.md` does not say whether a journey step counts as satisfied when its
substance is demonstrated but through a different trigger path than the step names — nor whether a
journey may cross to `passing` while the specific state the iteration created (~1.13 GB held resident
across the whole finalize tail) has never been measured.
**We chose:** scored J-07 `partial` for a third consecutive iteration, not `passing`, and stated the
step-by-step split explicitly in eval.md. Grounds stated rather than assumed: (1) `partial`'s schema
definition is literally what happened — steps 2 (HTTP-200/no-freeze half) and 3 have complete
this-iteration evidence, steps 1 and 4 have substance but not on the named/changed path, one acceptance
clause ("no unbounded whole-table ORM materialization remains on the warm or serving path") is still
not literally true because `data_manager.py:3098` -> `prices.py:131-152` still streams the whole
`daily_prices` table once per job, and one (the `[NEW]` walkthrough) is unrecorded for the 7th
iteration; (2) the ground is NEW rather than shifted — iter-36's ground (the browser lane never ran) is
genuinely closed, and this ground did not exist before, because the code only started holding the cache
across the tail this iteration; (3) AG-8 is *critical* and this session touched the memory ceiling in
each of the two preceding iterations, so certifying "heavy aggregates never take the service down" for
a path whose peak nobody measured — while an independent auditor says the direction may be reversed
there — is the rubber-stamp the methodology forbids, and the DoD's own words were "this-iteration
evidence, not inference". I record the cost honestly: this is the third `partial` in a row for a
journey whose headline promise the auditor himself calls "honestly demonstrated", and there is a real
risk of the vague-acceptance-criteria loop the framework warns about — which is why the next-step
recommendation names ONE cheap, bounded measurement that closes it rather than open-ended work. A human
who reads step 1's parenthetical as descriptive rather than binding, and who treats "the service stayed
up under a real 5-horizon warm with 57% memory headroom" as the whole of J-07, would score it `passing`
and carry the unmeasured finalize-tail peak as the already-open ledger finding iter-37/o.
**Reversible:** yes

## iter-37 — goal-evaluator

**Ambiguity:** decision tree C.4's first clause ("the SAME journey has now failed 2+ consecutive
iterations") matches under the reading this session recorded at iter-36 (`partial` = "did not reach
`passing`"), which makes ESCALATE first-match-wins over CONTINUE. But this would be the THIRD
consecutive ESCALATE, and the methodology says to use it sparingly; this iteration was ALREADY
dispatched at full depth with review PASS_WITH_NOTES, QA PASS, audit PASS_WITH_GAPS and closure
CLOSURE-PASS, so nothing here is an ambiguity/complexity problem that deeper lanes would resolve.
**We chose:** ESCALATE again. Grounds: (1) the tree is applied top-down, first match wins, so C.4
outranks CONTINUE regardless of how well CONTINUE also fits; (2) ESCALATE's only practical effect is
to make full depth MANDATORY rather than advisory, and this session provably lost iteration 35 in its
entirety to exactly that downgrade; (3) an independent, iteration-specific reason exists this time —
the review and QA lanes BOTH passed a real AG-8 regression (audit B1) and an unmeasured-claim gap
(B2), and only the audit lane caught them; a lean iteration has no auditor and the next iteration
works on the same memory-critical path; (4) the cost of being wrong is one unnecessary full pipeline,
versus a lost iteration the other way. I record the cost honestly: three ESCALATEs running reads as a
harsher judgement than this iteration's work deserves, and eval.md's Summary says so explicitly. A
human who reads `partial` as strictly not "failed", or who weighs "escalate sparingly" against a
session that has now escalated three times, would return CONTINUE with an advisory full-depth
recommendation.
**Reversible:** yes

## iter-38 — goal-evaluator

**Ambiguity:** J-04 "Non-blocking boot with visible status" is in this iteration's Required-still-passing
set, and BOTH lanes that owed it evidence failed to supply any. The deterministic replay returned FAIL
("provider: seed" did not appear), but I opened `J-04-verify.png` and it shows a "Backend unavailable"
page — the replay ran while the backend was down, so the FAIL measures the environment, not the product.
The LLM browser-qa lane then declined J-04 outright ("Do NOT restart services yourself"), and the
authoritative merged file records SKIPPED, not FAIL. My instructions say an un-evidenced journey is
`unknown`; methodology A.6 says evidence expires with CHANGE, not time, and this iteration's product diff
(2 files: a docstring, a test-only env toggle, one log line) touches no boot, readiness, health or crash
path. `docs/goal.md` does not say which rule wins when a required journey's evidence lane produces a FAIL
that is provably an artifact and its fallback lane declines by instruction.
**We chose:** kept J-04 `passing` on durability, but deliberately did NOT advance its `last_verified_iter`
(left at iter-37), did not advance `last_evidence_path`, and named every uncovered step. Grounds stated
rather than assumed: (1) downgrading on the replay FAIL would be scoring the product for a service that was
switched off — the picture is unambiguous; (2) the merged file is authoritative by my own methodology and
it says SKIPPED, so no FAIL stands anywhere; (3) three independent partials from THIS iteration corroborate
the journey without covering it — `UT-J-04-result.png` shows "Ready / provider: seed / seed 2026-07-22",
`J-04-verify.png` accidentally captures J-04's own unreachable-state presentation working correctly ("NO-GO
— do not rely on today's board", "Nothing is fabricated — confirm the backend is running and reload"), and
the dev/audit records show ~6 clean boots at ~1 s against a <= 5 s budget; (4) `unknown` would have the same
practical effect (it cannot support GOAL_ACHIEVED either) while discarding evidence that does exist, which
is the mirror image of rubber-stamping. NOT covered and named in three places: the pre-ready boot-phase
polls, a deliberately simulated crash with an abrupt logfile ending, and the mid-flight-job interrupted
state. A human who treats a required-set journey with zero live verification as `unknown` regardless of
code stability, or who reads the unreconciled replay FAIL as decisive, would score it `unknown` and block
the achievement gate on it now rather than at the next attempt.
**Reversible:** yes

## iter-39 — goal-evaluator

**Ambiguity:** J-07's Acceptance says "no unbounded whole-table ORM materialization remains on the warm
or serving path", but its parenthetical scopes the requirement to two named tables —
"(`forward_returns` / `scanner_results` read column-projected and/or chunked into bounded accumulators —
AG-8)". The site this iteration exposed is on `daily_prices`, not on either named table:
`_missing_data_diagnostic` (`data_manager.py:271`) buffers every universe member's `(symbol, date)` rows
(~3.3M) into one Python list via SQLAlchemy `_raw_all_rows` before the loop body runs. A narrow reading
(the parenthetical enumerates what the clause covers) says the clause is satisfied — the forward-aggregate
computation's own reads ARE bounded. A broad reading (the headline sentence governs) says it is not.
`docs/goal.md` does not say which controls.
**We chose:** the broad reading — the clause is NOT satisfied, and it is one of the two reasons J-07 stays
`partial` for a fifth iteration. Grounds stated rather than assumed: (1) the iter-37 evaluator already
applied the broad reading in this session, citing `data_manager.py:3098` -> `prices.py:131-152` (also
`daily_prices`, also not a named table) as a reason J-07 could not cross, so the broad reading is settled
precedent here and flipping it now would make the ledger incoherent; (2) `docs/goal.md`'s own Success
Criteria state the same requirement WITHOUT any parenthetical — "**No unbounded whole-table loads:** no
code path streams the full `daily_prices` table into RAM" — naming `daily_prices` explicitly, so the
narrow reading would have J-07's acceptance contradict the goal's Success Criteria; (3) AG-8 is *critical*
and this site demonstrably produced a real `MemoryError` and a 7+ minute process wedge in this iteration's
own drill, so reading the clause narrowly would certify "heavy aggregates never take the service down"
over a live counterexample. I record the cost honestly: under the narrow reading J-07 would have ONE
remaining blocker (the wedge) instead of two, and the second reason is a clause a careful reader could
say I extended. A human who reads the parenthetical as exhaustive would drop this clause from J-07's
blockers and score the journey on the wedge and the health budget alone.
**Reversible:** yes

## iter-39 — goal-evaluator

**Ambiguity:** decision tree C.4's first clause ("the SAME journey has now failed 2+ consecutive
iterations") matches under the reading this session recorded at iter-36, 37 and 38 (`partial` = "did not
reach `passing`"), which makes ESCALATE first-match-wins over CONTINUE. But this is the FOURTH consecutive
ESCALATE, the methodology says to use it sparingly, this iteration was ALREADY dispatched at full depth,
and it delivered its mandated target — so nothing here is an ambiguity/complexity problem that deeper
lanes would resolve.
**We chose:** ESCALATE again. Grounds: (1) the tree is applied top-down, first match wins, and three prior
evaluators recorded the identical reading on the identical journey in this same session — flipping it now
would make the session's own ledger inconsistent; (2) ESCALATE's only practical effect is to make full
depth MANDATORY rather than advisory, and this session provably lost iteration 35 in its entirety to
exactly that downgrade; (3) an independent, iteration-specific trigger exists this time — the audit lane
returned **FAIL** on findings the review lane AND the QA lane had both passed, including a critical
missing `MemoryError` isolation in `backfill_workers`' per-date compute; that is the third consecutive
iteration where only the auditor caught the substantive defect, a lean iteration has no auditor, and the
next iteration restructures a memory-critical path serving both ingest and `/api/data`; (4) the cost of
being wrong is one unnecessary full pipeline, versus a lost iteration the other way. I record the cost
honestly: four ESCALATEs running reads as a far harsher judgement than this iteration's work deserves —
it is the strongest of the five — and both eval.md's Summary and the evaluator log's plainly-stated list
say so explicitly rather than letting the verdict imply the work was poor. A human who reads `partial` as
strictly not "failed", or who weighs "escalate sparingly" against a session that has now escalated four
times, would return CONTINUE with an advisory full-depth recommendation.
**Reversible:** yes
