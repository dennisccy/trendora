# Goal Session ops-hardening — Assumption Ledger

Append-only. Each entry logs a spec decision that required interpreting an ambiguity in
`docs/goal.md` rather than a routine scoping pick. Zero entries for most iterations is normal.

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

## iter-40 — goal-evaluator

**Ambiguity:** All seven required-still-passing journeys got ZERO verification this iteration (browser QA
headlined `SKIPPED` with 8/8 `SKIP` rows, `reports/qa/goal-ops-hardening-iter-40-evidence/` was never
created, no iter-40 replay artifact exists, demo produced zero steps). My agent file says an un-evidenced
journey that the browser lane skipped is `unknown`; methodology A.6 says evidence expires with CHANGE, not
time, and the auditor's own instruction is the middle position — "do not treat them as re-verified", i.e.
keep the inherited status without advancing verification (the precedent iter-38 set for J-04). `docs/goal.md`
does not say which wins, and the diff's behaviour-neutrality is unusually well proven (a fixture equality
test replaying the OLD path, plus an independent structural trace by the auditor showing neither row order
nor fetch strategy can reach the output).
**We chose:** a code-path split rather than one blanket answer. A journey keeps `passing` on durability ONLY
when no hunk in this iteration's diff lies on the path that produces what that journey asserts; otherwise,
with zero fresh evidence, it drops to `unknown`. That gives J-03/J-08/J-09 `passing` (neither hunk touches
range validation, `/api/backtest`-from-storage, or the `/api/health` disclosure) and J-01/J-04/J-05/J-06
`unknown` (hunk 1 sits inside the coverage-payload producer they read; hunk 2 writes the very
`data_provider_runs` row J-01 and J-04 assert on). Grounds stated rather than assumed: (1) A.6's durability
carve-out is scoped by its own words to code that is UNCHANGED, and for four journeys it is not — the
no-screenshot rail (A.3) then forbids `passing`; (2) the asymmetry of the two errors is one-sided —
`unknown` costs a replay run the next iteration was going to owe anyway, while a stale `passing` row
mechanically satisfies the achievement gate and could carry an unverified journey into a GOAL_ACHIEVED
attempt; (3) the auditor named this exact risk ("Before any GOAL_ACHIEVED attempt, the deterministic replay
lane must actually run against this build"), and a machine-checkable `unknown` enforces it where prose does
not; (4) nothing anywhere shows a journey broken, so I recorded the reason as "not tested" in plain words in
eval.md rather than letting `unknown` imply a defect. I record the cost honestly: this discards real,
recent, high-quality evidence (iter-39's live 7/7 replay with seven distinct screenshots, one code state
ago) and it is harsher than the iter-38 precedent I am extending. A human who reads A.6's "change" as
BEHAVIOURAL change — and this diff's byte-identity is proven twice over — or who follows the auditor's
"inherited, not re-established" wording literally, would keep all seven `passing` with `last_verified_iter`
frozen at iter-39.
**Reversible:** yes

## iter-40 — goal-evaluator

**Ambiguity:** decision tree C.4's first clause ("the SAME journey has now failed 2+ consecutive
iterations") matches under the reading this session recorded at iter-36, 37, 38 and 39 (`partial` = "did
not reach `passing`"), which makes ESCALATE first-match-wins over CONTINUE. But this is the FIFTH
consecutive ESCALATE, the methodology says to use it sparingly, this iteration was ALREADY dispatched at
full depth, and it delivered its mandated code target well.
**We chose:** ESCALATE again. Grounds: (1) the tree is applied top-down, first match wins, and four prior
evaluators recorded the identical reading on the identical journey in this same session — flipping it now
would make the session's own ledger inconsistent; (2) ESCALATE's only practical effect is to make full depth
MANDATORY rather than advisory, and this session provably lost iteration 35 in its entirety to exactly that
downgrade; (3) an independent, iteration-specific trigger exists and it is the strongest of the session — an
iteration shipped with a DoD checkbox entirely unexecuted and seven required journeys unverified, and the
review lane, the QA lane AND the deterministic closure gate all reported clean; only the auditor caught it,
the fourth consecutive iteration where that is true, and a lean iteration has no auditor; (4) the cost of
being wrong is one unnecessary full pipeline, versus a lost iteration the other way. I record the cost
honestly: five ESCALATEs running reads as a far harsher judgement than this iteration's code work deserves,
and both eval.md's Summary and the evaluator log's plainly-stated list say so explicitly. A human who reads
`partial` as strictly not "failed", or who weighs "escalate sparingly" against a session that has now
escalated five times, would return CONTINUE with an advisory full-depth recommendation.
**Reversible:** yes

## iter-41 — goal-decomposer

**Ambiguity:** the iter-40 evaluator's next-step recommendation lists five ordered items for
"the next iteration" (verification-lane fix; faulthandler thread ID; bound `prices.py`'s
accumulator; monitor-past-terminal polling; two small hygiene items) without saying whether
they are one iteration's scope or should split across several. Rule 5 ("never bundle two risky
journeys") and rule 4 ("smallest spec wins ties") could argue for splitting the verification-lane
repair (tooling) into its own iteration before touching `_BarCache.prefill` (product code).
**We chose:** bundled all five into iter-41. Grounds: (1) the verification-lane fix and the drill
diagnostics are tooling/instrumentation, not product code — only `_BarCache.prefill`'s bound is a
risky product-code action, so rule 5's "one risky item" cap still holds; (2) the evaluator's own
prose frames items 1-5 as one ordered do-list for "the next iteration" (singular), and four prior
evaluators have already logged that ESCALATE-driven full-depth iterations in this session
routinely bundle a QA-tooling fix with one risky product change (iter-38/39/40 precedent); (3)
without the verification-lane fix landing FIRST inside this same iteration, J-05's own re-check
(needed because `_BarCache.prefill` is called from J-05's coverage-payload producer) would have
nothing to verify against — splitting would strand the risky change unverified for a whole extra
iteration. A human who weighs rule 4's tie-break more heavily than the evaluator's explicit
single-iteration framing would split this into a verification-lane-only iteration followed by a
separate `_BarCache.prefill` iteration.
**Reversible:** yes

## iter-41 — goal-evaluator

**Ambiguity:** decision tree C.4's first clause ("the SAME journey has now failed 2+ consecutive
iterations") matches under the reading this session recorded at iters 36-40 (`partial` = "did not reach
`passing`"), making ESCALATE first-match-wins over CONTINUE. But this is the SIXTH consecutive ESCALATE,
the methodology says to use it sparingly, this iteration was already dispatched at full depth, and it is
the best iteration in six — real progress (three journeys recovered from `unknown`), not a stalled one.
**We chose:** ESCALATE again. Grounds: (1) the tree is applied top-down, first match wins, and five prior
evaluators recorded the identical reading on the identical journey in this same session — flipping it now
would make the session's own ledger inconsistent; (2) ESCALATE's only practical effect is to make full
depth MANDATORY rather than advisory, and this session provably lost iteration 35 in its entirety to
exactly that downgrade; (3) an independent, iteration-specific trigger exists — the audit returned a
CRITICAL that review PASS and QA PASS both missed, and it was load-bearing (the anti-regression guard
this iteration shipped did not catch the very incident it was written for, proven against iter-40's own
committed artifact); that is the fifth consecutive iteration where only the auditor caught the
substantive defect, and a lean iteration has no auditor; (4) the cost of being wrong is one unnecessary
full pipeline, versus a lost iteration the other way. I record the cost honestly: six ESCALATEs running
reads as a far harsher judgement than this iteration deserves, and eval.md's Summary plus the evaluator
log's plainly-stated list both say so explicitly. A human who reads `partial` as strictly not "failed",
or who weighs "escalate sparingly" against six consecutive escalations, would return CONTINUE with an
advisory full-depth recommendation.
**Reversible:** yes

## iter-41 — goal-evaluator

**Ambiguity:** J-04 "Non-blocking boot with visible status" moved `unknown` → `passing` on a
deterministic replay row whose golden script has only TWO steps (goto `/` expecting "provider: seed";
goto `/data` expecting "Run history"). J-04's goal text has SIX steps, and this iteration changed the
mechanism behind step 6 (`_checkpoint_run_record`'s new count-based floor, `data_manager.py:4094-4134`)
— the very "interrupted job shows its last persisted progress" path. My agent file requires positive
evidence of passing; methodology A.3 requires a screenshot showing the acceptance state, which this one
does for the ready half only. `docs/goal.md` does not say whether a journey passes when its replay
script covers a subset of its steps and the uncovered part's code just changed.
**We chose:** `passing`, with every uncovered step named in journey-history and in eval.md. Grounds:
(1) the fresh evidence is real, dated and live — I opened the frame and it shows "Ready / provider: seed
/ seed 2026-07-22 / 591 symbols" with real coverage figures; (2) J-04's prior recorded status was
`passing` on iter-39's genuine live `kill -9` + restart drill, one code state back, so this is a
re-verification of a working journey, not a first claim; (3) the step-6 change only makes checkpoints
MORE frequent and is unit-proven with a frozen clock (TC-8) plus a companion test proving the existing
time-based path still fires — it cannot make the interrupted row staler; (4) scoring it `unknown` would
have the same practical effect on the achievement gate while discarding evidence that does exist. Cost
recorded honestly: the pre-ready boot phase, the crash presentation, the truncated logfile and the
interrupted mid-flight row got NO this-iteration evidence, and a full J-04 drill belongs in any
achievement run. A human who requires a journey's replay script to cover the steps whose code changed
would score J-04 `unknown` and block on it now rather than at the next attempt.
**Reversible:** yes

## iter-42 — goal-decomposer

**Ambiguity:** the iter-41 evaluator's next-step item (3) — "settle what 'no whole-table load' means
— either write the real per-symbol bound or amend goal.md to a per-row budget the current design
meets — and correct the QA report's AG-8 row either way" — offers two dispositions without marking
either OWNER the way item (8)'s health-budget/host-guard items explicitly are. Four prior iterations
(35, 36, 37, 41) each attempted a narrower fix at this exact code (`_BarCache.prefill`,
`app/engine/prices.py`) and each fell short of a genuine bound — iter-41's own columnar rewrite is,
by its own evaluator's words, "a COMPRESSION, not a BOUND." A fifth attempt risks repeating the
pattern; amending goal.md's Success Criteria (owner-authored, per docs/goal.md's Vision) is not
something this agent edits unilaterally.
**We chose:** plan a fifth, narrower-scoped attempt as agent-actionable dev work (not an owner
escalation) for iter-42, because a concrete, previously-unexplored path exists that the prior four
attempts did not take: `_BarCache.prefill`'s SELECT has no `WHERE symbol IN (...)` filter at all —
it always scans every symbol in `daily_prices` regardless of the `expected_symbols` pool callers
already pass it — while its own sibling `load_only` (same file) already implements exactly that
symbol-filtered, `yield_per`-streamed pattern for the identical query shape. Reusing that
already-proven pattern, plus auditing whether `_compute_coverage_uncached`/`_membership_timeline`'s
resolver loops need a symbol's FULL history or only a bounded trailing window, is new ground, not a
sixth retread of the columnar-compression approach. Grounds: (1) it is a genuinely different lever
than iter-35/36/37/41's attempts (query-time filtering / windowing vs. per-row storage format), so
"the same fix failing a fifth time" does not apply; (2) the fallback is written into this iteration's
DoD explicitly — if analysis shows every current caller genuinely needs full history for the full
universe, the developer documents that finding for evaluator/owner disposition instead of re-claiming
a fix that isn't one, so the iteration cannot silently repeat iter-41's overstatement risk; (3) editing
docs/goal.md's Success Criteria is out of this agent's remit per this session's "goal.md-only" governance
convention — that path stays available to the human owner, not self-authorized here. Cost recorded
honestly: if this fifth attempt also falls short, twelve-plus iterations of ambiguity will have become
thirteen, and the next decomposer should read this entry as evidence favoring an owner escalation
next, not a sixth agent attempt. A human who reads four consecutive partial results as sufficient
proof that no further bound is reachable without a caller-semantics change would skip straight to
amending goal.md's per-row budget language now rather than dispatching a fifth attempt.
**Reversible:** yes

## iter-42 — goal-evaluator

**Ambiguity:** decision tree C.1's first clause reads "any journey moved `passing`/`already_passing`
→ `failing`". J-05's IMMEDIATE prior recorded status was `unknown` (iters 40-41, not tested), not
`passing` — so the clause's literal wording does not match. But the journey-history schema in my own
agent file defines the `regressed` status as "was passing in a **prior iteration**, now failing"
(not "the immediately prior iteration"), and J-05 was verified passing at iter-39. Methodology E.1
then makes any `regressed` status force REGRESSION. `docs/goal.md` does not say which reading
controls, and the two give different verdicts (REGRESSION vs ESCALATE).
**We chose:** `regressed`, and therefore REGRESSION. Grounds stated rather than assumed: (1) the
schema's own words are "a prior iteration", and the narrower reading would require inserting
"immediately", which the text does not say; (2) `unknown` was never an assertion that the journey
worked — the iter-40 evaluator who set it wrote explicitly "nothing anywhere shows a journey broken,
so I recorded the reason as 'not tested'... rather than letting `unknown` imply a defect", so the
last thing this session actually KNEW about J-05 was that it passed; treating a not-tested gap as
erasing a prior pass would let any journey launder a regression by going unverified for one round —
precisely the hole iters 40-42 were spent closing; (3) the underlying facts are worse than the label
regardless: a user cannot load a day of history at all, and the health endpoint returned HTTP 500
four times and then stopped answering, which no reading calls acceptable; (4) the cost asymmetry is
one-sided — REGRESSION halts for an owner decision that is genuinely owner-only (AG-10 forbids any
agent from raising `memory_cap_mb`, and eight iterations have failed to fit inside it), whereas
ESCALATE dispatches a ninth attempt at a wall the owner must move first. I record the cost honestly:
this is the session's first halt in 42 iterations, it stops a round whose headline deliverable
genuinely worked, and the proximate cause of the failure is a PRE-EXISTING memory ceiling I verified
myself (7,004 MemoryErrors across ten days, four of them hours before this iteration's code existed)
— iter-42 did not break J-05. A human who requires C.1's "moved" to mean the immediately prior
recorded status, or who weighs the pre-existing attribution as disqualifying a REGRESSION, would
score J-05 `failing` and return ESCALATE with a full-depth recommendation.
**Reversible:** yes

## iter-42 — goal-evaluator

**Ambiguity:** the six required-still-passing journeys have genuine, dated, this-iteration replay
rows and screenshots (07:32-07:34) — but they were captured in the SAME run that, twelve minutes
later, drove the process into its memory ceiling and produced HTTP 500s on `/api/health`. My agent
file requires positive evidence of passing, which they have; it does not say whether evidence taken
minutes before the same run's service outage still certifies a journey.
**We chose:** keep all six `passing`, with the caveat recorded verbatim in each journey's note, in
eval.md's journey table, and in the evaluator log. Grounds: (1) methodology A.3's bar is a results
row plus a screenshot showing the acceptance state, and all six clear it — I opened two and both
corroborate, including re-adding J-01's regime components to the displayed 75.20 myself;
(2) the outage was induced by the J-07 warm the LLM lane deliberately triggered, not by these six
journeys' own paths; (3) downgrading them on a later, different event would be inferring failure
without evidence, which the honesty rail forbids as firmly as it forbids inferring success. Cost
recorded honestly: these six passes attest this build's CODE on a healthy process, NOT the instance's
stability, and J-01 is the sharpest case — its replay ran three real backfill jobs that all finished,
and eight minutes later a backfill job in the same process never started at all. Any achievement run
must re-check all six after the memory question is settled. A human who reads a service outage as
voiding every result from the same run would score all six `unknown`.
**Reversible:** yes

## iter-43 — goal-decomposer

**Ambiguity:** the owner's 2026-07-31 amendment commissions four follow-up actions (prefill-filter
revert, health-budget re-measurement, warm-seam unfreeze, `start-frontend.sh` host-guard) "for the
iterations that follow" (plural) without saying whether they are one iteration's scope or should
split, and separately states the warm-seam functions "may now be modified to bound their peak
footprint" — permissive language, not a mandate — leaving open whether THIS iteration must actually
rewrite `compute_forward_aggregates` et al. or may instead re-measure first and rewrite only if the
live number still requires it. Rule 5 ("never bundle two risky journeys") could argue for isolating
the one genuinely risky lever (a warm-seam rewrite) into its own later iteration rather than bundling
it with the revert + job-launch fix.
**We chose:** bundle the revert, the job-launch honesty fix, the `start-frontend.sh` host-guard
extension, and a real live re-verification of J-05/J-07 into this one iteration, but make the
warm-seam rewrite CONDITIONAL — attempted only if the live TC-7/TC-9 measurement against the
now-raised 8192 MB cap still shows the warm over budget or the pressure-abort still wedging, not
committed upfront. Grounds: (1) three of the four commissioned items (revert, host-guard extension,
re-measurement) are small, mechanical, and either owner-directed with a clear rationale (the revert)
or pure re-verification — none is a second risky product-code action alongside the job-launch fix, so
rule 5's "one risky item" cap still holds even bundled; (2) the ground-truth evidence already on
record (`reports/perf-budgets.md`'s OWNER AMENDMENT section: isolated warms measured 2.6-3.7 GB
against the new 8192 MB cap, i.e. 32-44%) makes a passing measurement the likelier outcome, so
committing to a warm-seam rewrite upfront risks exactly the pattern this session has repeatedly
learned to avoid (a fix attempted before confirming the problem still exists at the new operating
point); (3) splitting the mechanical items into their own iteration would leave J-05/J-07 stranded on
stale evidence for a whole extra iteration for no diagnostic benefit, since none of them depends on
the warm-seam question. I record the cost honestly: if the live measurement DOES show the warm still
over budget, this iteration's DoD only documents that finding rather than fixing it, and a further
iteration is needed — a human who reads "may now be modified" as "should be modified this iteration
regardless of measurement" would commit to the warm-seam rewrite unconditionally now, accepting the
added risk of bundling it with the other three items.
**Reversible:** yes

## iter-43 — goal-evaluator

**Ambiguity:** the merged results row for J-05 reads `PASS` and its evidence is real and dated (job
258 ran 325.4 s to terminal `ok`; `/scanner-runs/1882` rendered a 152-row leaderboard; the run record
listed the refreshed aggregates). But J-05's own step 1 requires a backfill over an **unsnapshotted**
historical trading day, and the tested day (2005-04-12) was already snapshotted (run id 237), so the
job created 0 snapshots and the leaderboard shown had been stored the previous day. `docs/goal.md`
does not say whether a journey passes when its check exercises the serve-from-storage half but never
the ingest→fresh-aggregates half its first step names.
**We chose:** `partial`, not `passing`, with every unexercised step named in journey-history and in
eval.md. Grounds: (1) J-05's headline promise is "aggregates are precomputed at INGEST", and a run
that ingested nothing cannot evidence it — the browser-QA agent said so itself, unprompted ("a
lighter case … reported honestly rather than implying this proves the heavier case is now fast
too"); (2) the schema's own definition of `partial` is "only some assertion steps passed", which is
literally this; (3) the developer's attempt at the genuine case ran 1,001 s without terminating, so
the heavier path is not merely untested, it is untested BECAUSE it may not finish — scoring `passing`
would hide the open question; (4) `partial` still clears `regressed`, so the genuine repair (the
launch guard) is credited and no false REGRESSION is forced. Cost recorded honestly: `partial`
understates a round where the specific iter-42 breakage was demonstrably closed, and it keeps J-05
off the achievement gate for at least one more round. A human who treats a green results row plus a
matching screenshot as sufficient — the bar every other journey was scored against this session —
would score J-05 `passing` and carry the unsnapshotted-day gap as a note instead.
**Reversible:** yes

## iter-43 — goal-evaluator

**Ambiguity:** decision tree C.4's first clause ("the SAME journey has now failed 2+ consecutive
iterations") matches — J-07 failed outright at iter-42 and again here. But this is the seventh
ESCALATE in eight scored iterations, the methodology says to use ESCALATE sparingly, this iteration
was already dispatched at full depth, and it made genuine forward progress (the owner's memory raise
proved out at 32.4% of cap, J-05 came off `regressed`, three of five deliverables landed clean and
two standing owner items closed).
**We chose:** ESCALATE. Grounds: (1) the tree is applied top-down, first match wins, and C.4's first
clause matches on the plainest possible reading — J-07 is `failing`, not `partial`, in two
consecutive rounds; (2) ESCALATE's only practical effect is to make full depth MANDATORY rather than
advisory, and this session provably lost iteration 35 in its entirety to exactly that downgrade;
(3) an independent, iteration-specific trigger exists and it is strong — the audit lane returned the
two load-bearing findings (B1 latency, B2 total outage) that review (PASS_WITH_NOTES), QA (PASS, "No
blockers to shipping") and the deterministic closure gate (CLOSURE-PASS over a `FAIL` headline) all
passed over; that is the seventh consecutive round where only the auditor caught the substantive
defect, and a lean round has no auditor; (4) the cost of being wrong is one unnecessary full
pipeline, versus a lost round the other way. Cost recorded honestly: a seventh ESCALATE reads as a
far harsher judgement than this round's work deserves, and eval.md's Summary and the evaluator log's
plainly-stated list both say so explicitly. A human who weighs "escalate sparingly" against seven
escalations, or who notes that this round already ran full depth so the verdict changes nothing
operationally, would return CONTINUE with an advisory full-depth recommendation.
**Reversible:** yes

## iter-44 — goal-decomposer

**Ambiguity:** the iter-43 evaluator's next-step item (1) says "give shutdown a deadline, and make a
calculation that stops making progress give up and say so instead of freezing" — two verbs, no
mechanism named. "Give up and say so" could mean (a) a new watchdog that actively times out and
cancels the stalled background dispatch, (b) a new disclosed field marking it stalled while it keeps
running, or (c) simply making the existing shutdown path bounded so the PROCESS gives up even though
the stuck computation itself does not. `docs/goal.md` does not specify which; J-07's acceptance text
only requires the service stay reachable and truthful, not any particular stall-handling shape.

**We chose:** (c) first — wire the ALREADY-DECLARED-but-never-enforced `ServerOpsCfg` launcher flags
(`limit_concurrency`/`timeout_keep_alive_seconds`/`graceful_timeout_seconds`) into `start-backend.sh`,
which bounds how long a stuck process can hold the port unreachable — plus a genuine live diagnostic
(the SIGUSR1 all-thread dump, armed at iter-40 and never fired) to find the ACTUAL blocked call, with
the fix shape (a)/(b)/neither left CONDITIONAL on what that diagnostic finds, rather than committing to
a specific watchdog mechanism upfront. Grounds: (1) the launcher-flag gap is concrete, previously
undiscovered, and low-risk — a direct code read found `ServerOpsCfg`'s own docstring already claims
`start-backend.sh` is "the SINGLE source" of these timeouts, which is false today; wiring it needs no
new mechanism, only reading already-declared config, mirroring the exact pattern iter-2 used for
`memory_cap_mb`; (2) the binding iter-38 lesson (mixing a "prove a failure mode" experiment with a
"compare two arms" experiment silently kills the first) argues against guessing a watchdog's threshold
values without first seeing what the live stack actually blocks on — a threshold picked before the
diagnostic runs would be exactly that kind of unevidenced guess; (3) the binding iter-39 lesson (three
probes without hitting the target is diagnosing the wrong thing) argues for reading the live dump
before writing any fix, which this iteration does for the first time in four attempts at this class of
freeze; (4) making TC-4's outcome conditional (fix OR honest disclosure) follows the iter-42 precedent
already used for an inconclusive AG-8 attempt, so this iteration cannot silently overclaim a fix that
isn't one. Cost recorded honestly: if the diagnostic implicates something outside this iteration's
evidenced reach (e.g., a kernel/host-level cause), the shutdown-deadline wiring alone will bound the
OUTAGE duration but not eliminate the underlying stall, and a further iteration is still needed. A
human who reads "give up and say so" as requiring an ACTIVE stall-detector shipped this same iteration
regardless of what the diagnostic finds would commit to option (a)/(b) upfront rather than making it
conditional.
**Reversible:** yes

## iter-44 — goal-evaluator

**Ambiguity:** my agent file's journey-history schema defines `regressed` as "was passing in a
**prior iteration**, now failing", and methodology E.1 makes any `regressed` status force REGRESSION.
J-05 was passing at iter-39 and is failing here, so the literal wording matches — but decision tree
C.1's own clause is narrower ("any journey moved `passing`/`already_passing` → `failing`") and J-05's
IMMEDIATE prior recorded status was `partial`, not `passing`. The two readings give different
verdicts (REGRESSION vs ESCALATE), and `docs/goal.md` does not say which controls. The iter-42
evaluator faced the same fork with `unknown` as the intervening status, chose `regressed`, and the
session halted; the owner acknowledged it, raised the memory envelope, and resumed. J-05 has not
reached `passing` since.
**We chose:** `failing`, and therefore not REGRESSION. Grounds stated rather than assumed: (1) the
`regressed` label exists to fire a halt at the TRANSITION from working to broken, and that halt
already fired at iter-42 for this exact journey and was acknowledged by the owner — re-firing it
every iteration until J-05 passes is an unbounded halt loop, which is the failure shape the framework
names as its first anti-pattern; (2) nothing is laundered by the narrower reading: `last_passing_iter`
stays at iter-39 in journey-history, the note records the full arc (iter-39 passing → iter-42
regressed/halt → iter-43 partial → iter-44 failing), and the achievement gate still blocks on a
`failing` journey exactly as it would on a `regressed` one; (3) iter-43 already set this precedent by
recording `partial` rather than carrying `regressed` forward; (4) the product did not newly break
here — this iteration ran J-05's defining case (an unsnapshotted day) for the FIRST time in the
session and discovered a long-standing defect whose root cause (`_excluded_counts_by_date`'s
O(dates × pool) recompute) predates every line of this iteration's diff; (5) the practical purpose of
a halt is to obtain something only the owner can give, and unlike iter-42 (where AG-10 forbade any
agent from raising `memory_cap_mb`) there is no owner-only lever here — the audit names two concrete
agent-actionable fixes and both standing owner items closed at iter-43. Cost recorded honestly: the
narrower reading means the owner is NOT stopped to look at a product that currently goes offline for
twenty minutes when you add one day of history, and a reader who wants that decision in his hands
this round is not wrong to want it. A human who reads the schema's "a prior iteration" literally — or
who holds that any 21-minute total outage is a critical AG-8 breach regardless of authorship — would
score J-05 `regressed`, return REGRESSION, and halt.
**Reversible:** yes

## iter-45 — goal-decomposer

**Ambiguity:** the iter-44 evaluator's next-step recommendation lists two items "in order" — (1) an
out-of-process watchdog/shutdown-deadline, (2) the membership-timeline incremental-invalidation fix —
and phrases EACH as deserving "its own round," but `docs/goal.md` says nothing about which must come
first, and rule 5 ("never bundle two risky journeys/changes in one iteration") only says they must be
separate, not which is separate first.

**We chose:** do item (2), the membership-timeline incremental fix, this iteration, deferring item (1)
(the watchdog) to a later one — reversing the evaluator's literal listed order. Grounds stated rather
than assumed: (1) a direct code read (`app.engine.data_manager._refresh_ingest_aggregates`) confirms the
SAME root cause — `refresh_coverage_snapshot`'s call into `membership_timeline_cached`, the FIRST step
of the finalize hook, runs BEFORE the forward-aggregate warm loop — is why J-07's warm never advances
past `horizons_done: 0/5` AND why J-05's own defining case never completes; fixing it is rule 3's
"unblocker" for BOTH currently-failing journeys' actual defect, not merely a bound on one symptom's
duration; (2) `reports/perf-budgets.md`'s own "For the evaluator" section independently names the
membership-timeline fix "the fix the evidence actually points at," ranking it above the watchdog in
substance even though the evaluator's prose listed the watchdog first; (3) the SAME artifact calls the
watchdog "small and mechanical," and J-07's own acceptance text ("never a deadlock, wedge, or restart
requirement") means a watchdog alone cannot make any currently-failing J-07 acceptance clause pass — it
only bounds an outage's duration, whereas the membership-timeline fix has a plausible path to making
both J-05 and J-07 pass. Cost recorded honestly: the app has no out-of-process safety net for one more
iteration — if this iteration's fix is incomplete or a different freeze recurs, the same unbounded-outage
risk stands until the watchdog iteration lands. A human who reads the evaluator's "(1)... (2)..."
enumeration as a mandated sequence would build the watchdog first this iteration instead.
**Reversible:** yes

## iter-45 — goal-decomposer

**Ambiguity:** `perf-budgets.md`'s framing of the fix ("scoping the cache key per-date, or merging
incrementally... a real design change to order-dependent `entries`/`exits` state") does not say whether
the incremental path must correctly handle EVERY ingest shape — including a historical gap-fill day
inserted BEFORE an already-cached later date, which can retroactively change that later date's `entries`/
`exits` — or may be scoped to the common append-forward case with a full-recompute fallback for the
rarer shape. `docs/goal.md`'s J-05 step 1 names only "one unsnapshotted historical trading day," without
specifying its position relative to already-cached dates.

**We chose:** scope the incremental fast path to the append-forward case (the new date is at or after
every already-cached date), falling back to the EXISTING full recompute whenever an ingest lands a date
strictly earlier than an already-cached date. Grounds: (1) neither iter-43's nor iter-44's live attempts
at J-05's defining case exercised the reorder-sensitive shape, so nothing in evidence requires solving it
this iteration; (2) mirrors this session's own established precedent (iter-16's `is_latest=true`-only
scoping, iter-27's stamp-narrowing) of shipping a scoped fix for the common case rather than an unproven
general-case rewrite, per the binding iter-38 lesson against speculative rewrites; (3) correctness for the
harder case is fully preserved — it falls back to the already-correct full recompute, so nothing is wrong
or fabricated, only unaccelerated for a shape this iteration doesn't evidence as broken. Cost recorded
honestly: a historical gap-fill inserted behind an already-cached later date still pays the full O(dates x
pool) cost after this iteration — if that shape is a common operator workflow, a further iteration is
needed to extend the fast path to it. A human prioritizing full generality over evidenced scope would
mandate the incremental path handle every insertion order in this same iteration.
**Reversible:** yes

## iter-45 — goal-evaluator

**Ambiguity:** `iter-45/scan-report.md` returns `CRITICAL — 1 critical` for a `secret-assignment`,
`sk-FATAL-HANDLER-LEAK-9c4a2d` at `apps/backend/tests/test_data_manager.py:6055`. AG-7's text is
absolute — "No hard-coded credentials, API keys, or tokens in source files" — and does not carve out
test fixtures, while my methodology's section B says a committed secret is critical and "when unsure
whether critical: treat as critical and say you were unsure (fail-closed)". A critical unresolved
anti-goal violation forces REGRESSION and halts the session.
**We chose:** not a violation — a deterministic-scanner shape match, recorded openly in eval.md's
anti-goal table rather than silently dropped. Grounds stated rather than assumed: (1) I opened the
site: the literal is a synthetic sentinel handed to `_KeyLeakingProvider`, a deliberately fake
provider, inside `test_fatal_job_failure_log_never_leaks_the_provider_key`, whose entire purpose is
to assert the key is scrubbed OUT of the log — the string exists to prove AG-7's intent is enforced,
not to authenticate anything; (2) it authenticates to no service and its own text spells out
"FATAL-HANDLER-LEAK"; (3) three identical-shape fixtures already live in this repo and predate this
iteration (`test_api_data.py:329`, `:487`, `:878`), so treating this one as a breach would either
be inconsistent or would retroactively condemn three prior accepted iterations; (4) I was not
unsure, so the fail-closed rule's precondition does not apply — I record that I applied it
deliberately rather than skipped it. Cost recorded honestly: a scanner CRITICAL was overruled by a
judgement call, and the standing risk is that a future real key gets waved through under this same
precedent. A human who reads AG-7 literally, or who holds that no agent may overrule a deterministic
security scanner, would call this critical and return REGRESSION.
**Reversible:** yes

## iter-45 — goal-evaluator

**Ambiguity:** AG-8 is marked *(critical)* and says the app must never "exhaust a service's memory".
This iteration the backend exhausted its memory and was fully unreachable for ~42 minutes (double
iter-44's), and the exhaustion is now proven reachable from ordinary page browsing, not only from an
ingest. Decision tree C.1 turns an unresolved *critical* anti-goal violation into REGRESSION and a
halt; C.4 turns the same iteration into ESCALATE. `docs/goal.md` does not say whether an
availability/memory-exhaustion defect that an iteration inherited rather than introduced is critical
or minor.
**We chose:** minor, and therefore ESCALATE rather than REGRESSION. Grounds: (1) authorship — this
iteration's product diff neither introduced nor widened it, and I proved the new code never ran at
all (`grep` for `_membership_timeline_incremental`/`append-forward` over 173,043 log lines → 0),
while the two driving accumulators are pre-existing and were placed out of scope by the spec before
this request-path evidence existed; (2) my methodology's own CRITICAL enumeration is secrets /
unapproved paid dependency / license violation / security backdoor / fabricated data, and an
availability defect is none of those; (3) the UI degraded honestly — I opened both captures and they
show "Checking backend…" and skeleton panels, which is what AG-8's own degradation clause asks for,
never a blank application-error page; (4) nothing was lost, fabricated, or presented as real;
(5) this family has been scored minor since iter-35/k and re-scoring it without the product changing
would make the verdict depend on which evaluator ran; (6) a halt exists to obtain something only the
owner can give, and there is nothing here — every remedy is named with a file and line and is
agent-actionable. Cost recorded honestly: the owner is NOT stopped to look at a product that goes
dark for 42 minutes and can be knocked over by opening a page, and the trend across four rounds is
the wrong way (multi-minute → 21 min → 42 min). A human who holds that a total outage of that length
on a session whose stated purpose is "available in seconds" is a critical AG-8 breach regardless of
who authored it — or who weighs the doubling as the new fact that breaks the prior precedent — would
score it critical, return REGRESSION, and halt.
**Reversible:** yes

## iter-46 — goal-decomposer

**Ambiguity:** the iter-45 evaluator's next-step gives "the next round" ONE explicit job — bound the
two unbounded evidence-serving-path accumulators (`research.py:777`, `forward_testing.py:2343`) — and
that fix's own mechanism does not touch J-05's failure mode (a backfill job's OWN `MemoryError`,
`_run_job`'s ingest path, never `evidence.py`'s request path). `docs/goal.md` does not say whether a
journey may be listed as a `Target journey` when the iteration's code change does not directly address
that journey's own root cause.

**We chose:** list J-05 as a Target journey alongside J-07, not only in a carried/deferred note.
Grounds: (1) `iteration-state.md`'s "Do not redo" list itself frames outstanding J-05 work as "it needs
one live drill, never a rewrite" — the append-forward fast path (iter-45) is built and
coherence-tagged `[TARGETED, not yet built]` pending exactly that live proof, and this iteration
supplies the live drill (TC-7), which is real, planned, agent-actionable work aimed at J-05, not mere
bookkeeping; (2) this iteration's two accumulator bounds reduce TOTAL system memory pressure during a
concurrent-load window, which is the SAME class of cascading-OOM failure (AG-10's 8192MB ceiling
shared across every concurrent compute) implicated in J-05's own recent failures, even though the two
sites are not J-05's own code path; (3) leaving J-05 out of Target journeys entirely, given it has now
failed 2 consecutive rounds, risks under-signaling standing work on a Must-have journey the framework's
own `unknown`/gap lesson (iter-42) warns against. Cost recorded honestly: TC-7 may reproduce a DIFFERENT
failure than run 281's (the true root cause of run 281's own death is still not fully diagnosed beyond
"MemoryError, now loggable"), so J-05 may still fail this round for a reason this iteration's diff does
not touch — the DEFINITION OF DONE and TESTING REQUIREMENTS below score that outcome honestly rather
than assuming a pass. A human who reads "Target journey" as requiring the iteration's OWN diff to
address that journey's root cause would keep J-05 out of Target journeys this round and record the live
drill as carried verification work instead.
**Reversible:** yes

## iter-46 — goal-evaluator

**Ambiguity:** decision tree C.1 fires REGRESSION when a journey moves `passing` → `failing`. This
iteration's only browser lane scored J-01, J-03 and J-06 FAIL (and J-04 PASS with a measurement that
misses its own ≤5 s clause) — but that lane ran at 05:45-05:49Z and the build then changed twice
inside the same iteration (`warmup.py` 06:17:39Z, `data_manager.py` 08:38:10Z), both changes aimed at
those very failures. Neither `docs/goal.md` nor the methodology says what status a journey carries
when its only evidence describes a build that no longer exists.
**We chose:** `partial` for all four, not `failing` — and therefore ESCALATE, not REGRESSION. Grounds
stated rather than assumed: (1) `partial`'s own definition is "only some assertion steps passed", and
that is literally what each row records (J-03's no-cap claim held and only its chunk-completion step
did not; J-06 passed 10 of 11 routes; J-04 passed 5 of 6 steps; J-01 computed its zero-work breakdown
correctly and only failed to reach a terminal state); (2) for J-01 and J-03 I verified the specific
repair in the machine record rather than in a handoff — `data_provider_runs` id=289/291 (zero-work
weekend backfill, 0.22 s, `ok`) and id=290 (the identical 412-day range that hung, 0.19 s, `ok`)
against id=280's 29 minutes on the iter-45 build — so `failing` would assert something about the
shipped build that the DB contradicts; (3) `partial` blocks GOAL_ACHIEVED exactly as `failing` does,
so nothing is laundered — the deterministic gate is unaffected and every gap is filed as an open
ledger entry (iter-46/av, iter-46/az); (4) the two rows whose defect is NOT repaired (J-06, J-04) were
still downgraded, so this is not a blanket pardon; (5) this session already uses `partial` for exactly
this shape (iter-37/o's ledger entry reads "the reason J-07 stays `partial`"). Cost recorded honestly:
the owner is NOT stopped to look at a round in which three previously-passing journeys failed their
live checks, and a reader who holds that a FAIL row on a previously-passing journey is a regression
regardless of what the build did afterwards would score all four `failing`, return REGRESSION, and
halt. The counter-cost of that reading is a halt for a defect the iteration itself discovered and
repaired before it ended.
**Reversible:** yes

## iter-46 — goal-evaluator

**Ambiguity:** the browser lane scored UT-J-07 FAIL on a single sub-criterion: `GET /api/evidence` did
not answer within 300 s under concurrent load. But `/api/evidence` appears nowhere in J-07's own four
steps in `docs/goal.md` (which cover the forward-aggregate warm, 1 Hz health polling, VmPeak margin,
and an induced-pressure abort); it comes from TC-4, this iteration's own DoD item, which the spec's
TESTING REQUIREMENTS lists as "a dedicated Evidence-page-under-concurrent-load scenario" SEPARATE from
"J-07 (all 4 steps)". The UI test plan merged the two into one row.
**We chose:** score J-07 against its own four steps and the iteration DoD separately — giving J-07
`partial` (up from `failing`, its first movement since iter-34) while recording TC-4 as UNMET and
filing the `/api/evidence` cost as its own open ledger entry (iter-46/av) attached to J-06. Grounds:
(1) J-07 step 2 and step 3 were independently met with strong evidence (34/34 health polls at
0.10-0.40 s under two concurrent backfills; 120/120 at max 104 ms; VmPeak 3,123 MB against the
8192 MB cap, recorded in perf-budgets Item O); (2) I verified the journey's headline claim myself —
no silent window anywhere in `logs/backend.log` and zero MemoryErrors, against iter-44's 20m51s and
iter-45's ~42 minutes; (3) it is not `passing` either, and I say why: J-07's acceptance clause "no
unbounded whole-table ORM materialization remains on the warm or serving path" is still false
(`samples.py:145/156`), the warm never reached all five horizons, and step 4 was not drilled live.
Cost recorded honestly: a reader who treats the UI test plan's merged UT-J-07 row as authoritative
over the journey text would keep J-07 `failing` for a fifth consecutive round, and would lose the
signal that the availability failure mode actually stopped.
**Reversible:** yes

## iter-47 — goal-decomposer

**Ambiguity:** `docs/goal.md` does not rank J-05 (the session's sole `failing` journey, 3 consecutive
rounds) above J-06/J-07 (both `partial`, sharing one already-diagnosed Evidence-page serving-path
defect cluster). The priority rubric's rule 1 (regressed first — none this round) and rule 3 (prefer a
failing journey that unblocks others) do not by themselves resolve which single risky change to take
this round, and the iter-46 evaluator's own next-step recommendation lists the Evidence-page fix as
item (2) and J-05's old-day case as item (4) — an explicit but non-binding ordering, not a mandate.

**We chose:** target J-06/J-07 this iteration (the `/api/evidence` cache-thrash fix plus the
`samples.py:145/156` bound), deferring J-05's old-day-insert fix to a later iteration. Grounds stated
rather than assumed: (1) the Evidence-page fix is the evaluator's own explicitly-named "one real job"
for this round, and it closes a defect on the SAME serving path (`/evidence`) implicated in BOTH J-06's
acceptance and J-07's "no unbounded whole-table ORM materialization remains on the warm or serving
path" acceptance clause — a genuine two-journey unblocker (rule 3), unlike J-05's fix, which only moves
J-05 itself; (2) J-05's remaining case is a separate, riskier change to a different subsystem
(`_membership_timeline`'s order-dependent recompute, per iter-45's own scoping note on
entries/exits correctness for a historical gap-fill) — bundling it with the Evidence-page work would
violate rule 5's "never bundle two risky journeys/changes in one iteration"; (3) this iteration's full
8-journey re-verification (driven by the evaluator's item (1) and by the prior ESCALATE) gives J-05 its
first dedicated live capture in 3 rounds regardless of whether its own code changes this round, closing
part of its standing evidence gap at zero extra risk. Cost recorded honestly: J-05 will very likely still
read `failing` after this iteration (a 4th consecutive round) since its root-cause fix is not attempted
here. A reader who weighs "the sole failing Must-have journey" above "an evaluator-labeled unblocker for
two partial journeys sharing one defect cluster" would target J-05 instead this round.
**Reversible:** yes

## iter-47 — goal-evaluator

**Ambiguity:** AG-9 is marked *(critical)* and says ingest jobs "run only against the committed seed /
local provider fixtures — no live external network calls or paid data services may be introduced
without an explicit goal.md amendment." During this iteration `data_provider_runs` id=297 — a `both`
(fetch+backfill) job for 2026-08-03, 12:47-13:17, 588 bars fetched, `snapshots_created: 1` — ran with
`provider='yahoo'`, and `apps/backend/app/data_providers/yahoo_provider.py` is a real live HTTP client
against `query1.finance.yahoo.com`. That job is what moved this working DB's latest bar from
2026-07-31 to 2026-08-03, which `GET /api/health` now reports as `seed_latest_date`. AG-9's text does
not say whether a PRE-EXISTING, product-goal-sanctioned live import path being exercised by a test
lane counts as a live external call "introduced" without an amendment.
**We chose:** minor and open (ledger iter-47/bh), not a critical violation — so ESCALATE, not
REGRESSION. Grounds stated rather than assumed: (1) nothing was introduced by this iteration — the
live import path is declared in `config.yaml` itself ("an import LIVE provider is resolved ONLY by
the on-demand Data Manager fetch path ... never by the boot lifespan", lines 12-16) and the
`data_manager.providers` catalog names yahoo "the no-key runbook source, listed first (the default
import source)" at :30-33, all of it predating this ops-hardening cycle; (2) 27 `provider='yahoo'`
runs exist in this DB going back to 2026-07-20, spanning many iterations that every prior evaluator
accepted — re-scoring the same behaviour as critical now would make the verdict depend on which
evaluator ran; (3) the data is REAL market data, never fabricated or substituted, and my
methodology's critical enumeration is secrets / unapproved paid dependency / license / backdoor /
fabricated data — a free, no-key public endpoint is none of those; (4) `apps/backend/data/trendora.db`
is untracked (`git ls-files` errors on it), so nothing entered version control; (5) a halt exists to
obtain something only the owner can give, and there is nothing here he must decide. Cost recorded
honestly: the session's stated premise is "local-first, deterministic, offline against the committed
seed", and its own automated lanes can reach the internet and permanently move the data basis for
every later iteration — I have put that in front of the owner in the eval and the log rather than
absorbing it. A human who reads AG-9 literally ("run ONLY against the committed seed"), or who holds
that a data basis silently changed by a network fetch breaks determinism for every subsequent
measurement, would call this critical and return REGRESSION.
**Reversible:** yes

## iter-47 — goal-evaluator

**Ambiguity:** no lane verified ANY journey against the build this iteration shipped: the only browser
artifact reads BLOCKED with zero rows for both target journeys, and the six replay rows came from
scripts I read and confirmed assert almost nothing, on a build that changed three times afterwards.
Neither `docs/goal.md` nor the methodology says whether a journey whose prior `passing` was earned
one iteration ago keeps that status when its module changed but its own code path did not, and its
only fresh "evidence" is a null test.
**We chose:** keep J-08 and J-09 `passing` while scoring J-01/J-03/J-04/J-06/J-07 `partial` and J-05
`failing`. Grounds: (1) methodology A.6 — evidence expires with CHANGE, not time, and I verified at
the source that J-08's and J-09's own producers are untouched by this diff (every `forward_testing.py`
edit sits on the drawdown-expectations path; `compute_forward_aggregates`,
`resolved_forward_aggregate_evidence` and `get_background_compute_status` are unchanged); (2) I
spot-checked both live on the shipped build rather than resting on durability alone — `/api/backtest`
200 in 0.023 s with `evidence_status: "refreshing"` and a populated scorecard, and
`/api/health.background_compute` present and honestly idle; (3) the methodology forbids downgrading
for evidence age alone, and downgrading them would punish the product for a process failure; (4) the
null-test rows are explicitly NOT what I scored on, and I say so in every artifact. Cost recorded
honestly: two journeys carry `passing` into the next round without a journey-level check on this
build, and if the next lane finds either of them broken, this call will have delayed that discovery by
one iteration. A reader who holds that "no lane ran, therefore nothing is verified" would score both
`unknown`, which changes no gate (GOAL_ACHIEVED is blocked either way) but would show 0 of 8 journeys
green rather than 2.
**Reversible:** yes

## iter-48 — goal-decomposer

**Ambiguity:** the iter-47 evaluator's next-step gives a NUMBERED order — (1) re-run all eight journey
checks, (2) harden J-05's golden assertion, (3) fix the historical-gap-insert finalize-tail (J-05's own
remaining defect, 4 consecutive failing rounds), (4) bound the Regime Lab's separate 8192MB-cap hit
(deferred 13 times already), (5) several small items (`samples.py:161`/`:168`, a shared warm-in-progress
flag, health-poll slowness, J-09's background-worker visibility gap). `docs/goal.md` does not say whether
a numbered evaluator order is a single iteration's checklist or a multi-iteration sequence, and the
priority rubric's rule 5 ("never bundle two risky journeys/changes... a joint failure is undiagnosable")
does not by itself say which items in a 5-item list count as "risky."

**We chose:** this iteration (iter-48) takes items (1) and (3) as its PRIMARY scope (full 8-journey
re-verification + the J-05 finalize-tail fix), takes the FIRST bullet of item (5) (`samples.py:161`/
`:168`) as a bundled TRIVIAL addition since it is the mechanical continuation of an already-proven
pattern (the iter-47 decile-branch bound, 5/5 pressure runs) on the SAME already-registered Data
Contract row, and explicitly DEFERS item (4) (Regime Lab) and the remainder of item (5) (the shared
warm-in-progress flag, health-poll slowness re-measurement, J-09 background-worker visibility) to a
later iteration. Grounds stated rather than assumed: (1) J-05's finalize-tail fix is a genuine
correctness-adjacent change to `_membership_timeline`'s recompute path — the ONLY subsystem in this
5-item list that risks changing computed values (entries/exits) if scoped wrong, which is exactly rule
5's "risky change" category; the Regime Lab fix is a SEPARATE, not-yet-diagnosed memory investigation
(VmPeak hit the 8192MB cap even though the read feeding it is already column-projected/streamed, per
the iter-47 evaluator's own measurement, meaning the true culprit is still unknown) — bundling a second
undiagnosed memory investigation alongside an order-dependent correctness fix is exactly the "joint
failure is undiagnosable" case rule 5 warns against; (2) `samples.py:161`/`:168` carries none of that
risk — it is the SAME function family, SAME already-registered row, SAME proven two-pass bounding
pattern applied a third time, so treating it as "trivial" (rule 5's other bucket: "several trivial
journeys OR one risky journey") rather than a second risky change is consistent with how this session
already treated the decile-branch fix at iter-47; (3) the evaluator's own numbering already sequences
item (4) AFTER item (3) rather than presenting them as co-equal, and iter-47's own decomposer precedent
(assumptions.md, iter-47) made the identical call in the other direction — deferring J-05's own fix
that round to avoid bundling it with the Evidence-page work, citing the same rule 5; this iteration
completes that deferred pairing without repeating the risk it was designed to avoid. Cost recorded
honestly: J-07 stays `partial` after this iteration (the Regime Lab's own acceptance-relevant defect is
untouched), and item (4) becomes a 14th deferral of the SAME named item (iter-33/g) — a number the next
evaluator should read as a standing cost, not a clean bill. A reader who holds that "the evaluator's
numbered order is the round's mandate in full" would target J-05 AND the Regime Lab together this
round, accepting the risk of an undiagnosable joint failure if the browser lane comes back with a new
regression neither fix's own tests explain.
**Reversible:** yes
