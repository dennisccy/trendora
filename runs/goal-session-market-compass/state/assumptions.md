# Goal Session market-compass — Assumption Ledger

Append-only. Each entry records a scoring decision that required interpreting an
ambiguous goal, so the owner can veto it early.

## iter-22 — goal-decomposer (Stage G write-path scoping: foreclose only the freshly-found
`data_manager.coverage_from_storage` self-heal write; leave `scanner.resolve_run` and
`compass.get_or_create_manifest` explicitly deferred)

**Ambiguity:** `docs/goal.md` ruling item 5 explicitly names and defers exactly two request-path guard
gaps — `scanner.resolve_run()` and "ordinary Data Manager persistence paths capable of calling
`run_scan()` or `persist_run_payload()`" — to "post-J-11 maintenance-boundary hardening work after
Stage G," and explicitly forbids "expand[ing]... into a generalized `ScannerRun` writer redesign" or
introducing "a new generic persistence architecture merely to satisfy this ruling." Iteration 21's
evaluator then found a THIRD, different unguarded write path — `data_manager.coverage_from_storage`'s
self-heal branch, which calls `_upsert_coverage_snapshot`, never `run_scan`/`persist_run_payload`, so it
is not literally covered by ruling item 5's enumerated list — and this iteration's coordinator note
relayed it as "the single most important new finding," stating "Stage G must therefore either assert
cache cleanliness AFTER the app is permitted to boot, or foreclose that write first," while also noting
this is "the third unguarded write path found (after scanner.resolve_run and
compass.get_or_create_manifest)" without explicitly directing Stage G to fix all three. Neither
`docs/goal.md` nor the coordinator note states whether closing the newly-found gap should also extend to
the other two now that a fix is being made at all.

**We chose:** wire the existing, already-tested `j11_preboot_guard.evaluate_boundary_for_date_fail_closed`
— the identical idiom already used at `warmup.py:361` and `forward_testing.py:551` — into
`data_manager.coverage_from_storage`'s self-heal branch ONLY. `scanner.py::resolve_run` and
`compass.py::get_or_create_manifest` are left untouched and explicitly re-recorded as open, deferred
gaps. Reasoning: (a) the coordinator note's "must therefore either... or foreclose" sentence's own
grammatical subject is "that write" — the data_manager.py self-heal call just described in the
immediately preceding sentences — not the other two, which are only mentioned for context/pattern-
recognition ("this keeps happening"); (b) ruling item 5 explicitly, by name, defers
`scanner.resolve_run()` and forbids broadening the fix into a "generalized... redesign" — fixing it now,
absent an explicit fresh instruction to do so, risks exactly the scope-creep item 5 warns against, and
the risk of under-fixing (leaving an already-explicitly-deferred, already-isolated-by-maintenance-mode
gap open one more iteration) is far smaller and more easily corrected than the risk of over-fixing
(overriding an explicit "do not expand" instruction from the same ruling block that authorizes Stage G's
own existence); (c) `compass.get_or_create_manifest` was already known as of iteration 19 and was not
newly escalated by this iteration's coordinator note the way the data_manager.py path was — nothing
about THIS iteration's fresh instruction set demands closing it now; (d) resource-constraint guidance in
this iteration's coordinator note explicitly says "do not broaden scope."

**Reversible:** yes — this is a code-scope decision, not a live-database mutation. A future iteration
(the "post-J-11 maintenance-boundary hardening" pass ruling item 5 itself anticipates) can extend the
identical guard idiom to the other two call sites at any time; nothing about fixing only one now
forecloses fixing the rest later, and the dev handoff explicitly records both as still-open so no future
lane has to rediscover them from scratch.

## iter-22 — goal-decomposer (membership_timeline_cache B2 closure: required read-only per-date
recompute-and-compare, not an optional "consider")

**Ambiguity:** Iteration 21's auditor raised gap B2 — the preserved `membership_timeline_cache` row holds
pre-incident `points` for several incident dates never touched by an append-only incremental refresh —
and this iteration's coordinator note relayed it with soft framing ("Consider whether Stage G should
assert against this"), not as an explicit mandate. `docs/goal.md`'s own Stage G acceptance list, however,
independently requires "no stale derived state remains for the incident set" as a binding, named
requirement, and Stage F's own recorded proof for this table only established that the CHEAP repair
branch would run on the next MISS (a performance/branch-selection proof), never that the row's own
ALREADY-CACHED content for those dates is still correct post-repair (a content-correctness proof) — the
goal text does not say which kind of proof this specific binding requirement demands for a table Stage F
chose to preserve rather than delete.

**We chose:** treat the per-date content-correctness proof as REQUIRED this iteration, not optional —
recompute each already-cached incident date's `size`/`entries`/`exits`/`excluded` values read-only via
`_membership_timeline` (the pure, non-cache-writing compute `membership_timeline_cached` wraps) against
current post-Stage-D storage, and compare field-by-field against the row's stored point; any mismatch
deletes the row (the exact fallback Stage F's own design already anticipated for this table), any full
match records the explicit proof and confirms the preserve decision. Reasoning: (a) "no stale derived
state remains for the incident set" is `docs/goal.md`'s own binding acceptance wording, not a
discretionary hardening nicety Stage G could reasonably skip; (b) the two kinds of proof (branch-
selection safety vs. content correctness) are logically independent — Stage F's own recorded evidence
answers only the first, so treating the question as already settled would be exactly the kind of
un-re-derived assumption this session's own lessons (iter-14b, iter-18) warn against; (c) the check is
cheap (read-only, in-memory, bounded to the handful of already-cached incident dates) and has a
pre-approved, already-safe fallback (deletion) if it fails, so requiring it adds negligible resource risk
for a real correctness gap in the session's terminal gate.

**Reversible:** yes — the check is purely read-only unless it finds a mismatch, in which case its only
action is deleting one already-superseded cache row (recomputable from canonical storage through the
existing producer at the next real request); nothing about requiring this proof forecloses a future
iteration from revisiting the methodology if live evidence contradicts this reasoning.

## iter-22 — goal-evaluator (the B3 circularity: Stage G's DB-level gate is complete; the serving/replay
half is still owed, so J-11 stays `partial` rather than `passing`)

**Ambiguity:** `docs/goal.md:1408` defines the stage sequence with "G (final serving/replay verification)",
and `:1978-1985` places on Stage G the assertions that rebuilt `ScannerRun`s serve the current complete raw
basis, that J-01/J-02/J-03 replay clean, and that Market Compass historical serving is internally
consistent. The SAME goal file's owner ruling item 4 (`:1793-1800`) forbids browser QA, replay, ordinary API
requests and any backend boot "throughout the D → G attempt", and forbids deactivating the boundary before
Stage G passes. Stage G therefore cannot perform the verification one line of the goal assigns to it. Owner
ruling item 9 — the latest instruction, 2026-08-26 — enumerates Stage G's minimum acceptance requirements
and every one of them is database-level; serving/replay is absent from that list. The goal text does not say
which reading governs, and the coherence auditor explicitly declined the question and left it to me.

**We chose:** score the recovery ATTEMPT as having honestly reached its owner-defined SUCCESS terminal state
(`J-11 STAGE G VERIFIED: YES` / `FULLY REPAIRED`, ruling item 14's SUCCESS block, boundary deactivated per
item 11) — because ruling item 9's enumerated acceptance list is the operative, latest, and only
satisfiable definition of the gate, and I independently re-derived every item on it live and read-only. But
score the JOURNEY J-11 as `partial`, not `passing`, with the gap recorded verbatim as the unperformed
serving/replay verification. Reasoning: (a) the two instruments are different — ruling item 14 governs how
the ATTEMPT is reported and this iteration reported it exactly as required, while journey status feeds the
achievement gate and must reflect what was actually verified; (b) my own methodology's maintenance-isolation
rail forbids promoting any journey TO `passing` on an iteration that produced no serving evidence, and this
iteration produced none by contract; (c) the missing check is now POSSIBLE for the first time (the boundary
is inactive), so recording it as owed costs nothing and preserves a check the goal file asks for; (d) the
independent auditor reached the same reading unprompted (B3: read `FULLY REPAIRED` as "the database-level
incident state is proven clean", not "the product has been observed serving correctly"). What I explicitly
did NOT do: describe the attempt as partially repaired, or invent ruling item 14's forbidden third state —
the terminal lines stand exactly as emitted.

**Reversible:** yes — one owner line settles it, in either direction, and nothing is mutated by this
reading. If the owner rules that Stage G was the database gate and serving verification is ordinary product
work, J-11 flips to `passing` on the next iteration's evidence with no work redone; if the owner rules the
serving check belongs to Stage G, the next iteration performs it under a supervised boot and closes the gap
by name. No row was written, withheld, or deleted on the strength of this interpretation.

## iter-23 — goal-decomposer (verification launch mechanism: `TRENDORA_CONFIG` override, not a
`config.yaml` edit; Depth kept at `full` despite the ruling saying full depth is "not required")

**Ambiguity:** The 2026-08-27 owner ruling ("OWNER RULING — J-11 database recovery accepted; one final
serving verification remains" + its "Post-Stage-G launch-condition clarification") requires booting the
real app against "a disposable, byte-faithful SQLite snapshot/clone" while the canonical database AND its
committed `config.yaml` stay untouched, but names no specific technical mechanism for pointing the app at
the clone. Separately, it states `CHAIN_REQUIRE_FULL_DEPTH=true` is "NOT required" for this task without
saying whether full depth remains permitted or should default to lean; the dispatch's own engine-computed
depth recommendation for this iteration is independently `full`.

**We chose:** (1) direct the developer to the already-existing, already-tested `TRENDORA_CONFIG` env-var
config-file override (`apps/backend/app/config.py:3147-3157`, "used by tests" per its own docstring) to
load a disposable verification-only YAML whose only delta from the committed `config.yaml` is
`database.url`, rather than editing the committed `config.yaml` in place or inventing a new override
mechanism — the smallest, already-proven lever, needing no new code. (2) keep `Depth: full` for this
iteration rather than downshifting to lean, because the dispatch's binding engine recommendation is `full`
and the task independently meets full-depth Trigger 1 (cross-cutting): real backend + frontend + browser +
replay execution exercising the interaction of ≥5 distinct engine modules (scanner, data_manager, compass,
forward_testing, the seven cache tables), none of which is covered end-to-end by any single existing
journey's own test suite. The owner's "not required" wording removes an obligation; it does not forbid
using full depth when independently justified by the dispatch recommendation and the trigger rubric.

**Reversible:** yes — both are execution-mechanism/process choices, not data mutations. A future iteration
could pick a different override mechanism or a different depth with no rework of already-completed
verification evidence, since neither choice touches the canonical database or any already-frozen J-11
Stage D-G evidence.

## iter-23 — goal-evaluator (the `/market` 404: "Today / Market Compass serving path works" read as
satisfied by `/`, not blocked by a route that does not exist yet)

**Ambiguity:** Owner ruling item 4 requires the verification to establish that "the Today / Market Compass
serving path works". The iter-23 spec's TC-4 turned that into a literal check that `/market` renders
HTTP 200 with every card from the former dashboard inventory. `/market` does not exist —
`apps/frontend/app/market/` is absent and J-08 (the journey that would build it) has never shipped, so the
route returns 404. The goal text does not say whether "Market Compass serving path" names the `/market`
ROUTE or the Market Compass FEATURE (the compass content), which today lives on `/`.

**We chose:** read it as the feature, and score TC-4 as inapplicable rather than failed. Reasoning:
(a) the Compass content — summary, what-changed, next-session focus, manifest strip with basis disclosure
— demonstrably renders on `/` in both J-11 screenshots, so the serving path the ruling cares about was
genuinely exercised; (b) `/market` is a `[TARGET]`-tagged, not-yet-built row in `blueprint.md`, and the
coherence auditor independently reached the same reading; (c) the alternative would make this iteration
fail on a J-08 product gap that ruling item 9 explicitly defers ("Advancing J-08... resumes in a LATER
iteration"), i.e. it would block J-11 closure on work the owner forbade this iteration from doing; (d) the
developer flagged it honestly instead of silently building the route, which is the correct call under the
spec's own scope boundary. What I explicitly did NOT do: treat `/market` as working, or drop it — it is
recorded as a live-re-confirmed J-08 gap for the next decomposer.

**Reversible:** yes — one owner line settles it. If he rules that `/market` itself had to render, the
remedy is to re-run the same clone-backed verification after J-08 ships the route; nothing about J-11's
already-captured clone evidence would need redoing.

## iter-23b — goal-evaluator (J-11 closed even though the ITERATION breached the canonical-DB
protection, because the BREACH sat outside J-11's own verification)

**Ambiguity:** Owner ruling item 3 requires that "Backend/frontend/browser verification runs against the
disposable verification DB only" and that the canonical DB "must not be mutated by this verification".
Item 8 then says J-11 may be marked PASSING once "the disposable repaired-state serving/replay
verification passes without an unacceptable product-data side effect", adding "No further owner
authorization is required". This iteration satisfied item 8 on the clone AND breached item 3 on the
canonical database in the same window. The text does not say whether a breach elsewhere in the iteration
voids an otherwise-conforming verification.

**We chose:** close J-11 (`passing`) and halt the SESSION on the breach, rather than withhold the journey
status. Reasoning: (a) every J-11 artifact traces to the guarded clone-backed boot — the browser-QA lane
verified via `/proc` that its backend held only the clone open, and I independently matched every cache
row on each database to its own boot by `created_at`, so the canonical writes provably belong to the
J-01/J-04 regression replay, a separate activity that is not part of J-11's verification; (b) item 8's
condition is met on its own terms and its "no further authorization required" wording means withholding
the status would be me adding a condition the owner did not write; (c) the breach is not silently
absorbed — it is recorded as an unresolved critical ledger entry and is the stated reason for the halt, so
the owner decides it explicitly. What I explicitly did NOT do: call the iteration compliant, or let the
loop continue.

**Reversible:** yes — nothing was mutated by this reading. If the owner rules that any canonical-DB
contact voids the verification, J-11 returns to `partial` and the same check re-runs on a fresh clone once
the launcher is fixed; the existing clone evidence would still stand as the method proof.

## iter-24 — goal-decomposer (which copy of `goal-iter-lean.sh` the owner's launcher-fix
authorization covers)

**Ambiguity:** Owner ruling item 3 (uncommitted `docs/goal.md` addition inside J-11, 2026-08-27)
authorizes fixing "the demonstrated launcher defect in
`incredible_auto_dev/scripts/automation/goal-iter-lean.sh`" by name. The repo actually contains
two byte-identical copies of that file — `scripts/automation/goal-iter-lean.sh` (the live copy
`run-goal.sh` actually executes for this project) and
`incredible_auto_dev/scripts/automation/goal-iter-lean.sh` (the vendored framework mirror kept in
sync via periodic "chore(framework): sync vendored incredible_auto_dev" commits). The ruling names
only the second path; it does not say whether the fix must also land in the first.

**We chose:** apply the identical patch to BOTH copies, keeping them byte-identical exactly as the
existing vendoring convention already maintains. Reasoning: (a) fixing only the vendored mirror
would leave the actually-executing copy (`scripts/automation/...`) carrying the live defect,
defeating the ruling's stated purpose ("Normal Market Compass product work resumes... once the
launcher defect is fixed and verified") since every subsequent goal-mode iteration runs the live
copy, not the mirror; (b) fixing only the live copy would silently diverge it from the vendored
mirror the project already keeps in lockstep, contradicting the established sync pattern and
risking the bug re-appearing on the next mirror sync; (c) the two files are currently identical,
so the same diff applies to both with zero extra design work.

**Reversible:** yes — a pure code-scope decision; if the owner intended only one copy, the other's
identical patch can be reverted or left as a harmless duplicate with no data implication either
way.

## iter-24 — goal-decomposer (Target journeys = none for an owner-authorized harness-safety fix
with no journey-visible change)

**Ambiguity:** The priority rubric ranks target selection by regressed journeys, consolidation,
journey-level unblockers, tie-breaks among journeys, and human-blocked avoidance — all framed
around advancing a specific Must-have journey (J-01..J-11). This iteration's entire authorized
scope (owner ruling items 3 and 5, 2026-08-27) is a Goal Mode harness/tooling fix —
`goal-iter-lean.sh`'s launch-context propagation — that touches no product code, no journey
acceptance criterion, and no UI surface. No single journey ID names this defect, so the spec
format's "Target journeys" field has no natural non-empty value, yet the DEFINITION OF DONE
template's default line ("Target journeys J-XX pass via browser-qa-agent") does not fit.

**We chose:** leave Target journeys empty ("none — infrastructure fix"), treat the owner ruling as
a binding directive that supersedes normal journey-based target selection for this one iteration,
and substitute a Required-still-passing regression check (J-01/J-04/J-10 replay) plus the fix's
own regression test as the iteration's pass bar in place of a browser-qa journey verification.
Reasoning: (a) the owner ruling is the LATEST, most specific instruction and explicitly names this
as the next authorized task, ranking above the general rubric; (b) rule 6 (don't plan
human-blocked work) and rule 3 (unblockers next) both point the same direction once read
functionally — this fix unblocks every future browser-QA/replay lane's safety, which is a
stronger unblocker than any single journey; (c) inventing a fake journey mapping would
misrepresent what the iteration actually verifies.

**Reversible:** yes — a scoping/process choice; the next iteration reverts to normal
journey-based targeting (J-09 per the goal file's own build order) as soon as this fix lands and
is verified.

## iter-24 — goal-evaluator (J-11's goal-edit drift resolved as verified-against-current-text, not `unknown`)

**Ambiguity:** `iter-24/journeys-changed.md` flagged J-11 (recorded `passing`) because its `docs/goal.md`
text changed since it was last verified (`spec_hash 55ef995c… → 012568db…`). My standing rule is that such
a pass is VOID: re-verify against the CURRENT text this iteration, or drop the journey to `unknown`. But
the text change IS the owner's new ruling (2026-08-27, "OWNER RULING — J-11 CLOSED"), whose item 1 both
declares "J-11 STATUS: PASSING — CLOSED" and forbids re-verification ("Do not reopen J-11 recovery or J-11
serving verification"), and whose scope for this iteration (item 3) is an automation-only fix that could
produce no journey evidence at all. The drift rule and the goal text it points at demand opposite actions,
and the rule does not say what to do when the new text's own content is a status declaration.

**We chose:** keep J-11 `passing`, record the NEW `spec_hash`, and set `last_verified_iter` to iter-24 —
treating a DOCUMENTARY + STATE-INTEGRITY check as the re-verification the current text admits of, and
saying so explicitly in `last_evidence_path` so no reader mistakes it for a fresh browser pass. The check
had three parts, all performed by me: (a) I read the entire delta — ONE hunk at `docs/goal.md:2194`,
+46/-0, purely additive, adding NO acceptance criterion and tightening none, so nothing in the new text
could be unmet by the iter-23 evidence; (b) I proved the state J-11 certifies is byte-intact —
`apps/backend/data/trendora.db` (8365871104 / mtime 1787822829), `-wal` (2599752 / 1787862368) and `-shm`
(32768 / 1787863696) all identical to their iter-23 post-verification values, so nothing could have
invalidated the pass; (c) I confirmed the new text's own checkable directives hold — item 2 (no cleanup
writes: none occurred), item 3 (exactly one narrow tooling fix: the diff is 5 automation files, zero
product code), item 4 (clone retained: still on disk). Reasoning for not choosing `unknown`: it would
contradict a binding owner ruling that states the journey is passing, and would schedule work the same
ruling forbids. What I explicitly did NOT do: re-stamp `last_passing_iter` (it stays iter-23, the
iteration whose serving evidence established the pass), and I did not extend this treatment to J-01/J-04/
J-10 — they were genuinely not re-verified and keep `last_verified_iter: iter-23`.

**Reversible:** yes — nothing was mutated by this reading and no database was opened. One owner line
settles it either way: if he rules that any goal-text edit inside a journey block demands fresh browser
evidence regardless of the edit's content, J-11 drops to `unknown` and the next browser iteration re-runs
the same clone-backed serving check, with the iter-23 clone evidence still standing as the method proof.

## iter-25 — goal-decomposer (re-measure J-09 now, rather than treating its iter-4 honest miss as fully
discharged / owner-blocked)

**Ambiguity:** J-09's own five steps (config edit, standing-warm measurement, addendum, concurrent-load
check, byte-identity spot check) all ran to completion at iter-4, producing a recorded HONEST MISS
(3,439,100 kB vs a ≤ 2,621,440 kB target) and stopping for owner review exactly as its acceptance text
instructs ("record the honest measured figure... never widen the target to pass"). The
iteration-state digest separately lists "whether 3.44 GB is acceptable for J-09" among five open,
non-blocking owner questions. It is not stated whether that closes J-09's actionable work until the
owner rules on the figure, or whether a stale measurement (taken before J-10's raw recovery and J-11's
full derived-state regeneration materially changed the database's content and likely its cache
footprint) is itself grounds for a fresh, current re-measurement without waiting on that ruling.

**We chose:** treat this as fresh re-verification work, not owner-blocked work — re-run J-09's
steps 2-5 (measurement, addendum, concurrent-load check, byte-identity spot check) against the CURRENT
live database with NO config edit (the one authorized config change already stands), and append a new
dated addendum rather than waiting on the open 3.44 GB acceptability question. Reasoning: (a) the
measured system materially changed since iter-4 (two large recovery/regeneration passes touched the
canonical database), so the iter-4 figure's currency is itself in question independent of whether 3.44
GB was ever going to be accepted; (b) re-measuring requires no new owner authorization — it is read-only
against already-authorized, already-landed config, exactly "ordinary non-destructive product work" per
owner ruling item 5; (c) it does not attempt to resolve the open acceptability question itself — a
repeat or different miss is recorded honestly and left exactly as open as before, per J-09's own
acceptance text; (d) both the iter-24 evaluator's next-step recommendation and the iteration-state
digest's "Do not redo" list independently name J-09 (not "wait for owner") as the next target.

**Reversible:** yes — pure measurement, zero config/code/data mutation. If the owner rules J-09's
iter-4 result was already sufficient to close the loop on it, this iteration's fresh figure is simply
additional corroborating (or updated) evidence beside it, not rework; nothing recorded here needs to be
undone either way.

## iter-25 — goal-evaluator (the canonical-DB boot read as SANCTIONED, not a repeat of the iter-23 breach)

**Ambiguity:** `docs/goal.md`'s "Post-Stage-G launch-condition clarification" (owner, 2026-08-27,
`docs/goal.md:2080-2105`) states "The canonical repaired database remains OFF and protected" and "Do not
interpret removal of those D→G launch conditions as permission to boot or mutate the canonical database."
The LATER "OWNER RULING — J-11 CLOSED" (`docs/goal.md:2197`) item 5 states "Normal Market Compass product
work resumes immediately once the launcher defect is fixed and verified. No further owner authorization is
needed for ordinary non-destructive product iterations," and item 6 forbids stalling for "correctly
recomputable derived-cache residue." This iteration booted the canonical database via
`scripts/start-backend.sh` and served ~2,614 read requests. The two passages can be read as conflicting;
the goal text does not say which governs an ordinary post-closure iteration.

**We chose:** read the §13 clarification as SPENT and scoped — its own closing paragraph says it
"supersedes §13 only for the new post-Stage-G disposable serving-verification task," and that task
completed at iter-23 — so the later item 5 governs, and this iteration's read-only canonical boot was
sanctioned rather than a repeat of the iter-23 breach. I did not take that on the text alone: I verified
read-only that the boot touched nothing in the categories item 6 still reserves for owner approval —
`next_session_manifests` still 24 rows with `prospective_eligible` true on zero of them and newest
`available_at_utc` still 2026-08-20 (no briefing minted — the exact hazard the iter-22 note warned a
single page request could cause); `scanner_runs` max id still 3158, newest `created_at` 2026-08-26 (no
twelfth day-record minted); `daily_prices` frontier still 2026-08-12 with 585 rows on each recovered day.
The only residue is 4 rows in two recomputable cache tables (`market_phase_cache`, `event_study_cache`),
which item 6 names explicitly. What I did NOT do: open a new anti-goal ledger entry, or treat the boot as
a contract deviation on the three replayed journeys the way iter-23's evaluator did.

**Reversible:** yes — nothing was mutated by this reading and I opened the database read-only. One owner
line settles it: if he rules that the canonical database stays off regardless of item 5, the remedy is to
re-arm an isolated clone for future browser/replay lanes; the four cache rows are recomputable and his own
item 6 already directs the non-destructive default for exactly that residue.

## iter-25 — goal-evaluator (J-09's absent browser row read as an acceptance-text WAIVER, not a missing citation)

**Ambiguity:** `reports/phase-goal-market-compass-iter-25-ui-test-results.md` lists `UT-J-09` under
**Missing Target Journeys** — "no test case executed for J-09 by any lane" — a machine-level flag whose
own explanatory text says an iteration must never show a clean headline while a target journey has no row.
My standing rule is that a journey with no results row and no screenshot is `unknown`. But J-09's own
acceptance text in `docs/goal.md` says "**Walkthrough:** waived — deliberately backend-only (no UI surface
changes); the demo requirement is replaced by the dated VmPeak measurement and drill citations in the dev
handoff." The two point opposite ways for the same journey.

**We chose:** treat the goal's own waiver as authoritative and score J-09 from the measurement evidence
(`reports/perf-budgets.md` Addendum 41 + the dev handoff), not as `unknown`. The practical stake is low —
J-09's measured 3,064,772 kB misses its ≤2,621,440 kB target, so it stays `partial` either way and is
never promoted on this reading. What I explicitly did NOT do: treat the "Missing Target Journeys" row as
noise — it is recorded in the eval as reflecting the waiver, so a later reader is not left thinking a
browser test was silently skipped.

**Reversible:** yes — a scoring-interpretation call with no mutation. If the owner rules that every target
journey needs a browser row regardless of a walkthrough waiver, J-09 drops to `unknown` and the next
browser iteration adds a UT case; none of this iteration's measurement evidence would need redoing.

## iter-26 — goal-decomposer (J-05 step 1 / J-06 steps 1-3's literal "remove the last two trading
days on /data" drill is NOT executed against the canonical database; routed to fixtures + safe
additive-only live actions instead)

**Ambiguity:** `docs/goal.md` J-05 step 1 literally instructs "On `/data`, remove the last two trading
days of snapshots (seed-safe) and backfill the same range," and J-06 steps 1-3 build on that same
live drill (a further backfill elsewhere, then a remove-data pass covering the frozen manifest's
as-of, then a restore). The goal text does not name which two calendar dates "the last two trading
days" are, and does not flag that — as of this iteration — those two dates are STILL 2026-08-11 and
2026-08-12: the exact pair whose removal via this same class of drill (iter-5) caused the session's
core incident (`docs/goal.md`'s own "Destructive-drill isolation" constraint: "the drill removed
2026-08-11/2026-08-12; the seed window ends 2026-07-01, so nothing local could put them back"). I
independently confirmed the frontier is unchanged (`daily_prices`/`scanner_runs` both still max at
2026-08-12) and that `remove_data()` structurally can only ever target non-seed (post-2026-07-01)
dates — so "the last two trading days" today has no other reading. Re-running literally the same
drill class against literally the same two dates, whose AG-9 recovery exception is now EXHAUSTED (no
further live fetch of these dates is authorized without a new dated amendment), is both a
safety repeat of the session's worst incident and very plausibly AG-9-blocked if the backfill needed
a live fetch to restore what removal deleted.

**We chose:** do NOT call `remove_data()` / `clear_snapshot_dates()` / any backfill against the
canonical `apps/backend/data/trendora.db` this iteration. Instead: (a) route J-05 step 1's flagship
`mode=at_ingest`/`prospective_eligible=true` freeze proof, and J-06 steps 1-3's remove/restore/basis
proofs, to the EXISTING isolated-engine fixture suite (`test_ingest_finalize_compass.py`,
`test_manifest_invariants.py` — never the canonical DB), extending it only where a genuine gap exists
(API-level, not just unit-level, coverage of "removed source run -> `GET /api/compass` never 404s,
basis reads unavailable"); (b) use ONLY safe, additive, already-shipped LIVE actions against the
canonical DB for real browser-qa evidence — a read-only manifest-strip render of an existing clean
retrospective manifest (`as_of=2025-04-15`, zero incident-window contact) and its confirm-gated
`POST /api/compass/regenerate` (pure INSERT, AG-12-safe, never deletes/mutates version 1) to observe
a live version-2 mint. Reasoning: (a) this directly mirrors the iter-5 decomposer's own precedent of
routing the at_ingest "burned slot" proof to fixtures instead of a live drill, now extended for a
stronger reason (safety, not just slot exhaustion); (b) `docs/goal.md`'s "Destructive-drill isolation"
constraint says drill isolation infrastructure is NOT this cycle's build, but it does not say the
literal drill must be repeated live regardless of risk — building nothing new and simply not
re-running the incident-causing action is the more conservative reading; (c) owner ruling item 5
authorizes "ordinary non-destructive product iterations" — a live remove+backfill of the exact
incident dates is not ordinary or non-destructive by any reading available to me. What I explicitly
did NOT do: skip J-05/J-06 verification entirely, or treat the fixture suite as a substitute for ALL
live evidence (the manifest-strip render and regenerate-to-v2 are real, live, canonical-DB browser-qa
evidence for the parts that are safe).

**Reversible:** yes for the scoping choice itself — nothing this iteration touches is undone by a
future change of mind; if the owner rules the literal live remove+backfill drill on 2026-08-11/08-12
(or a different, freshly-chosen non-incident date pair beyond the seed window) should run for real,
a future iteration can do so with its own explicit authorization, and none of this iteration's fixture
or regenerate evidence would need to be redone — it stands on its own as valid coverage of the parts
it was scoped to prove. The one NOT reversible piece is narrow and intentional: the live
`POST /api/compass/regenerate?as_of=2025-04-15` call mints a permanent version-2 row (by AG-12 design,
regenerate rows are never deleted) — this is the accepted cost of getting real live evidence for J-06
step 4 without touching removal/backfill at all.

## iter-26 — goal-evaluator (J-05 promoted to `passing` although step 2's flagship state is fixture-only)

**Ambiguity:** J-05 step 2 requires `GET /api/compass` for the frontier date to serve `mode: at_ingest`,
`version: 1`, `frozen: true`, `prospective_eligible: true`, `generation.producer: ingest_finalize`. That
state cannot be observed on the canonical database and never can be again: `2026-08-12`'s version 1 (row
id 1) is a legacy pre-freeze row with NULL `mode`, versions 2–6 were minted by `producer=regenerate`
during the incident-recovery window and are `prospective_eligible=false` by AG-17's own requirement, the
create-once rule means version 1 can never be re-minted, and AG-9 forbids fetching a newer trading day.
The goal text does not say whether a step whose live premise has been destroyed by a prior incident may be
satisfied by fixture evidence.

**We chose:** promote J-05 to `passing`, scoring step 2 from route-level fixture evidence
(`apps/backend/tests/test_api_compass.py::test_compass_route_serves_every_new_field_directly`, which
asserts all six field values plus `verify_manifest_hash` at the response layer, not at unit level), while
scoring steps 3, 4 and 5 from live canonical-database evidence I re-derived myself read-only (export byte
equality 355,711/355,711 with hash `9bc08cfba0…` reproduced; strip figures 531/10/521/28 and 539/0/539/26
matching the stored payload; disposition tallies 513+8=521; 45 `engine_identity`-stamped ScannerRuns vs
3,083 NULL). Reasoning: (a) no live observation CONTRADICTS the fixture — the live frontier's ineligible
state is what AG-17 mandates, so the product is behaving correctly, not failing; (b) the limb is
permanently unprovable live, so holding the journey open is an unsatisfiable criterion looping forever —
the framework's own #1 anti-pattern; (c) the fixture proof is at the serving-route layer, which is the
strongest substitute available short of new market data. What I explicitly did NOT do: treat the fixture
as covering the limbs I could check live (I checked those myself), and I recorded `evidence_makeup: true`
so the still-missing walkthrough is not silently forgiven.

**Reversible:** yes — a scoring-interpretation call with no mutation. One owner line settles it: if he
rules that J-05 step 2 needs a live observation regardless, J-05 returns to `partial` and stays there
until a goal.md amendment authorizes a new trading day's data; none of this iteration's live evidence
would need redoing.

## iter-26 — goal-evaluator (the permanent version-2 mint read as authorized ordinary work, not an owner-gated act)

**Ambiguity:** The owner's ruling of 2026-08-27 item 5 says "Normal Market Compass product work resumes
immediately... No further owner authorization is needed for ordinary non-destructive product iterations",
while item 6 still REQUIRES owner approval for "immutable-manifest mutation... or another genuinely
irreversible product-contract decision". This iteration triggered the confirm-gated regenerate action
against the canonical database, minting `next_session_manifests` row id 25 (`as_of=2025-04-15, version 2`)
— a row that is permanent by design (regenerate rows are never deleted). The decomposer's own ledger entry
flags it as "the one NOT reversible piece". It is not obvious whether a permanent additive row counts as
"ordinary non-destructive work" or as a "genuinely irreversible" act needing approval.

**We chose:** read it as authorized, and opened no anti-goal ledger entry. Grounds, each checked: (a)
nothing was mutated or deleted — I verified read-only that version 1 (row id 17) still verifies its own
`manifest_hash` over its own payload, keeps `created_at 2026-08-20 11:41:00.381102`, and that ids 1–25 are
complete so no row was removed; (b) AG-12 names new version rows as the SANCTIONED correction mechanism,
and AG-18's prohibition is textually scoped to the J-11 schema migration ("by it or around it"), which did
not run; (c) J-06 step 4 — written by the owner — explicitly instructs "Trigger the explicit regenerate
action for that as-of (confirm-gated)", so performing it is executing the goal, not exceeding it; (d) the
action was taken through its own shipped confirm gate on a clean 2025 date with zero incident-window
contact, and I confirmed the rest of the database was untouched (`daily_prices` 3,310,374, `scanner_runs`
3,128 with max id 3158 and newest `created_at` 2026-08-26, unchanged even after the later replay and
browser lanes ran).

**Reversible:** no for the row itself — it is permanent by design, and that is stated plainly in the
evaluation's owner-facing lines. Reversible for the POLICY: if the owner rules that any permanent write to
the canonical database needs his sign-off regardless of how additive it is, future iterations simply stop
triggering regenerate live and J-06 step 4 falls back to fixture proof; the existing row stays, correctly
marked not usable as forward-looking evidence, exactly like every other row.

## iter-27 — goal-evaluator (J-06 promoted to `passing` although step 2's "unavailable" state is proven only on a fixture database)

**Ambiguity:** J-06 step 2 instructs "Run seed-safe remove-data over a range covering that manifest's
as-of (its snapshots cascade away); assert `GET /api/compass` still serves the manifest verbatim with a
read-time basis disclosure showing the underlying run is unavailable — never a 404, never a recompute."
The literal `remove_data()` call has never been executed against any database in this scoping: not
against the canonical DB (no live `ScannerRun` deletion is authorized, and the binding `iter-26 —
goal-decomposer` ledger entry routes the drill to fixtures because "the last two trading days" still
resolves to the incident pair 2026-08-11/12), and not against the fixture DB (the test deletes the run,
its `ScannerResult` children and that date's `DailyPrice` rows by SQL instead). The goal text does not say
whether a route-level fixture reproduction of the post-removal STATE satisfies a step written in terms of
the removal ACTION.

**We chose:** promote J-06 to `passing`, scoring step 2 from the route-level fixture proof
(`apps/backend/tests/test_api_compass.py:288` — the REAL `app.api.compass.compass` function against a real
SQLite database, asserting `basis.status == "unavailable"`, `"no longer stored"` in the detail,
`healed is None`, zero new `scanner_runs` rows, and the manifest's `manifest_hash`/`version`/full payload
byte-identical to the pre-removal response), combined with live canonical-DB evidence for steps 3 and 4
(UT-02 "Basis: available" at 2025-04-15 v2 with v1 and v2 both listed; UT-03 "Basis: rebuilt" at the
frontier with its honest detail sentence). Grounds, each checked: (a) this iteration's spec DEFINITION OF
DONE explicitly authorizes fixture-level proof for this state and instructs the evaluator to score J-06
from combined fixture + live-regression evidence, "as it did for J-05 in iter-26"; (b) the auditor verified
against `data_manager.py:2178-2190` that the fixture's deletes are a faithful reproduction of what
`remove_data` leaves behind, and accepted the substitute (finding T2); (c) I confirmed the behavioural flip
myself by comparing the same test at `HEAD` (asserting the bug) with the working tree (asserting the fix);
(d) requiring the literal live drill would mean re-running the exact action class that caused this
session's worst incident, on data whose AG-9 recovery exception is exhausted. What I did NOT do: treat the
fixture as covering steps 3 and 4 — those I scored from live evidence and re-derived the displayed numbers
myself against stored row id 25.

**Reversible:** yes — a scoring-interpretation call with no mutation. One owner line settles it: if he rules
that step 2 needs a real `remove_data()` execution, J-06 returns to `partial` and the cheapest closure is a
throw-away database copy (the iter-23 clone at `runs/goal-market-compass-iter-23/verify-clone/` still
exists and the launcher guard that protects such runs was verified at iter-24); none of this iteration's
route-level or live evidence would need redoing.

## iter-27 — goal-evaluator (audit finding B3 accepted as an out-of-scope residual rather than an unmet J-06 limb)

**Ambiguity:** J-06 step 2 promises the route "still serves the manifest verbatim ... never a 404". The
auditor's B3 shows the promise holds only while the as-of still RESOLVES: `resolved_date` runs first on
both branches, and because `remove_data` deletes the in-scope `DailyPrice` rows too, removing the range of
a FRONTIER-dated manifest (every `at_ingest` manifest, e.g. 2026-08-12 v6) moves `latest_data_date` behind
that manifest's as-of, so `resolve_as_of_date` raises `future` -> HTTP 400 and the intact frozen row becomes
unreadable. J-05's own flagship manifest IS the frontier one, so a literal reading of step 2 applied to it
would fail. The goal text does not say whether an honest 4xx that is not a 404, over a row that was never
mutated, breaks the step.

**We chose:** record B3 as an honest residual and promote J-06 anyway. Grounds: (a) I read
`scanner.resolve_as_of_date` (`scanner.py:304-334`) myself and confirm the behaviour is exactly
pre-existing — pre-fix, `resolve_run` called the same validator first for the same reason, so this
iteration neither caused nor worsened it; (b) it is narrowed by `remove_data`'s seed-safety — the committed
seed bars cannot be deleted, so every seed-covered as-of always resolves and the promise holds fully for the
realistic historical case now proven; (c) reaching the failing case requires removing post-seed price data,
which is precisely the destructive act AG-9 and the standing safety scoping now forbid; (d) closing it would
mean serving a manifest BEFORE validating the as-of, a larger reorder squarely outside this spec and
arguably at odds with the honest as-of resolution contract every other route shares. What I did NOT do:
leave it unstated — it is written into J-06's `gap` field in journey-history, into the evaluation, and into
the next-step recommendation, so no later reader assumes step 2 is unconditionally closed.

**Reversible:** yes — nothing was mutated by this reading. If the owner rules that a frozen manifest must
remain readable even when its own price range is gone, J-06 returns to `partial` and the fix is a bounded
follow-up (serve the stored manifest on an exact-date match before as-of validation, keeping today's error
mapping for every other path).

## iter-28 — goal-decomposer ("Leadership rotation" read as a display-only filtered re-presentation of the already-served `session_delta.changes`, not a new computed value)

**Ambiguity:** `docs/goal.md` names "leadership rotation" as one of J-07's six body sections (step 1) and
one of the Today compass's Key Capabilities, but gives it no independent computation spec — unlike
what-changed (J-02), the summary (J-03), or next-session focus (J-04), each of which has its own
Acceptance/Steps block. It is not stated whether "rotation" is a new engine-computed value or a
re-presentation of already-served data.

**We chose:** treat it as a presentational grouping of the already-registered `session_delta.changes` array
(`GET /api/compass`), filtered client-side to `kind ∈ {sector, theme, stock}` — the SAME field What-changed
already renders, just narrowed to rotation-relevant kinds for a focused view. Grounds: (a) the goal's own
"Consistency (single source)" acceptance text for every J-07 section requires "every word, delta, and echo
on `/` is a served field... the frontend performs no threshold comparison, delta computation, or word
selection" — filtering an already-closed-vocabulary `kind` field is a display concern, not a computation;
(b) a second computation would duplicate `session_delta`'s already-canonical stock-leadership-bucket-
crossing and sector/theme rank-move logic, which the coherence audit would flag as a second producer for
the same value; (c) no goal.md text anywhere else defines a distinct "rotation" algorithm to build against.

**Reversible:** yes — a scoping/interpretation call with no schema or data-model impact. If the owner rules
"leadership rotation" needs its own distinct computation (e.g. a rotation-specific ranking not present in
`session_delta`), a future iteration adds a new field under the existing single producer
(`build_manifest_payload`) without touching what this iteration ships.

## iter-28 — goal-decomposer (new `state_band` direction words frozen inside the manifest content block, computed once at write, not recomputed at read)

**Ambiguity:** J-07 step 3 requires three served direction words (regime, stress, breadth) that do not
exist as a field anywhere today. `docs/goal.md` does not say whether these words belong inside the
persisted, immutable `next_session_manifests` content (frozen with the rest of the manifest, like
`session_delta`) or should instead be computed fresh on every read from the two already-canonical endpoints
(`GET /api/dashboard`, `GET /api/market-phase`) without ever being persisted.

**We chose:** compute and freeze `state_band` inside `build_manifest_payload`, the same single producer as
`session_delta`/`narrative`, stored as part of the manifest content and served via the existing
`GET /api/compass` — never recomputed at read. Grounds: (a) the goal's own "Compute-at-ingest" constraint
says "the manifest freeze and everything the compass serves are produced in the ingest finalize tail or by
create-once, and served from storage; no request-path recompute (warm reads perform zero producer calls)"
— a read-path recompute would violate this directly; (b) `session_delta`'s run-over-run comparison (the
closest existing precedent for a "current vs previous run" derived value) is already frozen inside the
manifest for exactly this reason; (c) freezing it makes historical/retrospective reads of `state_band`
stable and reproducible under `content_hash`, matching every other derived-content field's contract.

**Reversible:** yes — an implementation-placement call, additive and non-destructive. If the owner rules
`state_band` should NOT be part of the immutable manifest (e.g., because it is presentation-only and should
be free to change if the word map is retuned), a future iteration can move the computation to a read-time
helper without any stored-data migration, since no other value depends on `state_band` being frozen.

## iter-28 — goal-decomposer (all live browser-qa `as_of` values this iteration constrained to the already-manifested safe set, to guarantee zero new manifest mints)

**Ambiguity:** J-08 steps 3-5 require exercising a historical `?asof=D` view (a "pre-feature historical run
date D", the J-05 frontier date, and a fresh-tab load of D) but do not name which calendar date(s) to use.
Per the pump coordinator note and the iter-27 incident, ANY live `GET /api/compass?as_of=<D>` for a `D`
without an existing manifest row permanently mints one (create-once-on-GET) — sanctioned ordinary product
behaviour, but this iteration's own safety posture (nine prior process incidents this session) favors
proving J-08 without any new live mint at all if an already-safe date can satisfy every step.

**We chose:** constrain every live browser-qa `as_of` this iteration to `{no param (Latest), "2026-08-12",
"2025-04-15"}` — both explicitly named dates already carry manifest rows (2025-04-15 has v1/v2 from
iter-26/27's own regenerate evidence; 2026-08-12 is the frontier with v1-v6), so EVERY live call this
iteration is a pure read, zero new mints, while still satisfying J-08's literal requirements: 2025-04-15
serves the "pre-feature historical run date D" with a visible retrospective label (step 3) and the fresh-tab
scoped-load check (step 5); 2026-08-12 serves the frontier at-ingest check (step 4).

**Reversible:** yes — a test-data scoping call with no product-code or database impact. If a future iteration
needs to exercise the create-once-on-GET mint path itself (a date with NO existing manifest), that is a
new, explicitly authorized live action for that iteration's own plan — none of this iteration's evidence
would need redoing.
