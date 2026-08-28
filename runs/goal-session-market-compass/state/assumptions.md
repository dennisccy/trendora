# Goal Session market-compass — Assumption Ledger

Append-only. Each entry records a scoring decision that required interpreting an
ambiguous goal, so the owner can veto it early.

## iter-20 — goal-decomposer (scoping this iteration to Stage E alone, not Stage E+F or E+F+G)

**Ambiguity:** `docs/goal.md`'s Stage D→G ruling authorizes the full Stage D→E→F→G sequence in one
instruction and frames it as one continuous "Goal Mode resume" (item 13), and item 7 authorizes Stage E
unconditionally once Stage D succeeds — so no further owner action gates starting it. But as iteration
19's own logged assumption entry already established for Stage D, nothing in the ruling requires the
authorized sequence to be delivered inside one decomposer iteration/dispatch, and nothing forecloses a
future decomposer from continuing to split it stage-by-stage.

**We chose:** scope iteration 20 to Stage E alone — re-verify Stage D's frozen state fresh, repair
forward-return holes over the retained + rebuilt snapshot set, and STOP with the item-14 terminal-outcome
status lines — leaving Stage F (cache invalidation) and Stage G (full verification/acceptance gate) to
later iterations. Reasoning: (a) this is the exact discipline iteration 19 already established and logged
for Stage D, and every prior J-11 stage/step in this session (B1, Stage C, the AVB correction, the guard
build, the table-create-and-arm, Stage D) has been its own iteration; (b) Stage E has its own distinct
live-database mutation with its own failure mode (a three-population forward-return classification, and a
real risk — found during this planning pass — that the wrong existing entry point could mint a
`ScannerRun` outside the eleven-date incident boundary) that deserves focused reviewer/auditor attention
undiluted by Stage F's separate cache-invalidation risk surface (seven named caches, each requiring its
own disposition proof); (c) the decomposer's own priority rubric forbids bundling two risky changes in one
diff, and Stage F is easily large enough on its own to count as a second risky change.

**Reversible:** yes — if Stage E's live execution succeeds cleanly this iteration, nothing about stopping
there forecloses Stage F/G in a later iteration; if a future decomposer judges the stages should have been
combined, no work already done needs to be undone, only continued.

## iter-20 — goal-decomposer (requiring the per-run `backfill_run_forward_returns` loop; forbidding `backfill_forward_returns()`'s whole-DB entry point for Stage E)

**Ambiguity:** `docs/goal.md` J-11 step 5 names two existing functions side by side — "run the existing
create-once canonical forward-return machinery (`forward_testing.backfill_forward_returns` /
`backfill_run_forward_returns`...)" — without stating which one Stage E's execution should call, or
whether the choice matters.

**We chose:** require the execution module to iterate every existing `ScannerRun` (retained + the 11
Stage-D-rebuilt rows) and call `forward_testing.backfill_run_forward_returns(session, run, config)` once
per run, and forbid calling `forward_testing.backfill_forward_returns()`'s whole-database entry point
anywhere in the new module or its CLI script. Reasoning: (a) reading `forward_testing._backfill()` (the
function `backfill_forward_returns()` delegates to) directly shows that BEFORE it inserts any forward
return, it first "ensures a persisted snapshot for every walk-forward cadence date" by calling
`scanner.run_scan` for any `walk_forward_asof_dates()`-computed date lacking an existing `ScannerRun`,
guarded only by the J-11 boundary check for dates that happen to be incident dates;
`walk_forward_asof_dates()` computes a `quarterly`, 30-year cadence grid independent of the scanner's own
`monthly` deep-cadence snapshot schedule, so nothing already on record proves every one of its target
dates already carries a run — calling the whole-DB entry point risks minting a `ScannerRun` outside the
11-date incident boundary as a side effect, which the ruling's item 7 forbids ("may not... broaden into
unrelated historical cleanup") and which no lane in this session has yet audited; (b)
`backfill_run_forward_returns()` performs the identical create-once forward-return INSERT with no such
side effect (its own docstring: "it never UPDATEs a `scanner_runs` / `scanner_results` / `*_scores`
row"), and per step 5's own wording this per-run path, applied "over the retained + rebuilt snapshot set,"
is sufficient to fill every derivable hole in both named hole populations; (c) this is exactly the class
of gap this session's own lessons (iter-15, iter-18) warn against — trusting a hand-built or textually
side-by-side summary of two functions instead of reading the called function's actual body before a live
write.

**Reversible:** yes — this is an implementation-path constraint on code not yet written; a future
iteration could revisit it if live evidence later proves `walk_forward_asof_dates()`'s target set is
provably a subset of already-existing runs, but the safer per-run path costs nothing today (same
create-once semantics, same resulting rows, only a different iteration surface) and needs no retraction.

## iter-20 — goal-evaluator (a harness permission refusal is not the ruling's "refusal")

**Ambiguity:** `docs/goal.md` ruling item 14 puts the attempt into INCOMPLETE-and-STOP on "any failure,
refusal or unmet gate from Stage D onward", and item 10 makes any such failure require a complete C→G
restart. The developer's own first attempt to run the Stage E CLI was refused by Claude Code's Bash
permission classifier BEFORE the Python process started (recorded, and retained as SUPERSEDED, in
`runs/goal-market-compass-iter-20/j11-stage-e-live-execution-blocked.json`). The ruling never says
whether a tooling-permission denial counts as the "refusal" that voids the attempt.

**We chose:** read "refusal" as a refusal by the recovery machinery itself — a preflight gate refusing to
proceed, the live guard refusing a write, an unmet acceptance check — and NOT as a harness-level
permission denial. Reasoning: (a) the denial produced zero database side effects (I verified the
pre-run count 6,797,728 independently three ways, and the whole 16,592-row insert forms one contiguous
id block ending at the table maximum, so no earlier partial write exists); (b) the owner then executed
the identical command themselves and it completed with every pre-check and post-check passing, so the
attempt has exactly one live execution, not a failed one plus a retry; (c) the strict reading would force
a complete C→G restart — re-deleting and re-regenerating eleven days — over an event that touched
nothing, which cannot be the intent of a ruling whose failure semantics exist to prevent piecemeal
half-repairs; (d) the developer correctly refused to work around the denial, which is the behaviour the
rule protects.

**Reversible:** yes — one owner line settles it. Stage E's write is additive and create-once/idempotent,
so if the owner reads item 14 strictly, the remedy is a fresh whole-attempt restart and nothing recorded
here needs to be undone or hidden; the retained SUPERSEDED marker preserves the full first-attempt record.

## iter-20 — goal-evaluator (goal.md step 5's retained-run holes read as a mistaken premise, not an unmet requirement)

**Ambiguity:** `docs/goal.md` J-11 step 5 asserts "So holes exist on retained runs" and requires the audit
to distinguish population (b), "holes on otherwise-retained runs caused by the original 2026-08-11/12 bar
deletion". Stage E inserted ZERO rows on all 3,117 retained runs. The goal text does not say what it means
if that population turns out to be empty — a correct outcome, or a repair that did not happen.

**We chose:** score population (b) = 0 as CORRECT and complete, not as an unmet requirement, on the
strength of my own re-derivation (the cascade deletes an affected run's forward returns whole, so a
retained-run hole cannot exist; live data shows zero non-rebuilt rows measuring into 2026-08-10/11/12).
Reasoning: (a) the requirement is to REPORT the three populations with their own counts, which was done;
(b) the alternative reading would demand fabricating rows to reach a non-zero count, which the same step
forbids outright ("Never fabricate a forward return to reach row-count parity"); (c) the premise is a
factual claim about the code, and the code says otherwise. What I explicitly did NOT do: treat this as
harmless — I carried it forward as a binding design input for Stage G, whose acceptance list will ask
whether the forward-return holes were repaired.

**Reversible:** yes — nothing is mutated by this reading; if the owner wants the premise re-examined, the
underlying evidence (the cascade code path and the live grouped counts) is recorded and re-runnable
read-only, and no row was created or withheld on the strength of the interpretation.

## iter-21 — goal-decomposer (scoping this iteration to Stage F alone, not Stage F+G)

**Ambiguity:** `docs/goal.md`'s Stage D→G ruling authorizes the full D→E→F→G sequence in one instruction
and item 8 authorizes Stage F unconditionally once Stage E succeeds, so no further owner action gates
starting it. But nothing in the ruling requires the authorized sequence to be delivered inside one
decomposer iteration, and nothing forecloses continuing to split it stage-by-stage, as iterations 19 and
20 already chose to do for Stage D and Stage E respectively.

**We chose:** scope iteration 21 to Stage F alone — re-verify Stage D/E's frozen state fresh, classify and
where warranted invalidate the seven dependency-affected caches, and STOP with the item-14 terminal-outcome
status lines — leaving Stage G (the full verification/acceptance gate) to a later iteration. Reasoning:
(a) this is the identical discipline iterations 19 and 20 already established and logged for Stage D and
Stage E, and every prior J-11 stage/step in this session has been its own iteration; (b) Stage F has its
own distinct failure mode (a seven-table classification exercise with a real, planning-time-discovered
correctness risk in `availability_from_storage` — see BACKGROUND) that deserves focused reviewer/auditor
attention undiluted by Stage G's separate, larger verification-contract surface; (c) the decomposer's own
priority rubric forbids bundling two risky changes in one diff, and Stage G is easily large enough on its
own (the full acceptance gate covering raw inputs, snapshot scope, forward returns, manifests, audit/
evidence/user state, caches, and operational isolation) to count as a second risky change.

**Reversible:** yes — if Stage F's live execution succeeds cleanly this iteration, nothing about stopping
there forecloses Stage G in a later iteration; if a future decomposer judges the stages should have been
combined, no work already done needs to be undone, only continued.

## iter-21 — goal-decomposer (per-cache disposition design: `created_at`-vs-Stage-D-start as the decisive
classification signal, and a conditional preserve for `membership_timeline_cache`)

**Ambiguity:** `docs/goal.md` J-11 step 6 requires classifying each of the seven named caches into one of
three dispositions (guaranteed-invalidates / explicit-delete / regenerate-through-canonical-producer, plus
"prove unaffected and leave alone" as a fourth legitimate outcome for a cache proven data-independent of
J-11) but does not assign a specific disposition to any specific cache, nor does it say how to resolve the
"same-count/same-ID stamp collision" risk it names when a pure `dataset_version` string comparison cannot
by itself distinguish a coincidental collision from a genuine fresh post-repair compute.

**We chose:** (1) use each cache row's `created_at` compared against Stage D's frozen execution-start
instant as the decisive classification signal — corroborated by, never replacing, the `dataset_version`
stamp comparison — since maintenance isolation has forbidden any write to these tables since before that
instant, so every currently-stored row in the six scanner-run/forward-return-dependent caches must predate
the repair regardless of what its stamp string reads; an unexplained row at or after that instant is
treated as a maintenance-isolation breach requiring escalation, never as a routine case. (2) Default five
caches (`event_study_cache`, `market_phase_cache`, `forward_aggregate_cache`, `coverage_snapshot`,
`availability_cache`) to `explicit_delete`, required outright for `availability_cache` on the strength of a
concrete finding this planning pass made by reading `data_manager.availability_from_storage` directly
(`:1741-1747`/`:1760-1763`): its own serving logic would otherwise serve a stale, pre-repair payload
labeled `stale: False` (i.e., current) the first time `/api/data/availability` is requested post-reboot
with no ingest job in flight — a live AG-3/AG-8 risk, not a hygiene question. (3) Preserve
`index_series_cache` untouched, since its only dependency (index-symbol `daily_prices` bars) is proven
byte-unchanged by Stage D's and Stage E's own mutation accounting. (4) Give `membership_timeline_cache` a
conditional recommendation — preserve its stale row (rather than delete) specifically so its own
MISS-repair fast path can take the cheaper "historical gap-insert" branch instead of forcing the next real
request onto the documented >300s full cold-compute path on a host that has already frozen once from
memory pressure — but only if Stage F's own live proof confirms the safe branch (not the narrower
append-forward branch) would actually run; if that proof does not hold, fall back to deletion. Reasoning
for the whole design: (a) iter-15b's lesson (never trust a single fingerprint alone) argues directly against
a stamp-string-only comparison; (b) the `availability_cache` finding is concrete, evidence-backed code
reading, not speculation, so treating it as "required" rather than "optional" is proportionate; (c) forcing
uniform deletion across all six caches would be simpler to specify but would reintroduce exactly the
memory/host risk `docs/goal.md`'s own Constraints section and the 2026-08-20 freeze incident warn against,
for a cache (`membership_timeline_cache`) whose own code already has machinery built to avoid it.

**Reversible:** yes — this is an implementation-path/classification-policy choice about code not yet
written. A future iteration could revisit any single cache's disposition if live evidence at Stage-F
execution time contradicts this planning pass's reasoning (e.g., the `membership_timeline_cache`
incremental-reuse proof fails, which the spec already routes to a safe deletion fallback); no destructive
step depends on this reasoning being right on the first try, since every disposition is proven live before
Stage F's one authorized write executes.

## iter-21 — goal-evaluator (a post-deletion cold-compute on the request path read as an operational risk, not an AG-10 violation)

**Ambiguity:** AG-10 requires that "heavy compute MUST be launched only via the project launch
scripts, which MUST apply the host caps". Stage F's deletion of `event_study_cache` and
`forward_aggregate_cache` removed two serve-a-prior-generation fallbacks, so after Stage G the first
`/api/evidence` request can now run `compute_drawdown_expectations_cached` synchronously on the
request path (`forward_testing.py:2874-2877`), and `market_phase_cached`/`event_study_cached` will
cold-compute on first view (auditor B3). The goal text does not say whether *making an existing
in-process compute heavier or more likely* counts as "launching heavy compute" for AG-10's purposes,
on a host with a documented freeze history (2026-08-20).

**We chose:** score this as an operational risk and a binding Stage-G design input, NOT as an
anti-goal violation (not even minor). Reasoning: (a) AG-10's mechanism is the CAPS, and the future
compute would run inside the normal backend, which is started by `scripts/start-backend.sh` and
therefore still inherits the HOST-GUARD affinity/thread caps and `server.memory_cap_mb` — no cap is
removed, weakened or bypassed by this iteration; (b) Stage F's own measured peak was 479.9 MB against
an 8192 MB ceiling, so the iteration itself launched nothing heavy; (c) the alternative reading would
make *any* cache invalidation an AG-10 violation by construction, which would forbid the very repair
the owner authorized in ruling item 8; (d) the app is OFF, so no such request can land before Stage G
designs the boot sequence. What I explicitly did NOT do: call it harmless — I carried the auditor's
recommendation forward as a required Stage-G design item (let `warmup._warm_drawdown_expectations` /
`_warm_membership_timeline` / `_warm_coverage_snapshot` / `_warm_availability` complete before any
request lands, and record measured peak memory across that warm).

**Reversible:** yes — nothing is mutated by this reading, and the deleted rows are all recomputable
from `daily_prices`/`scanner_results` through their existing canonical producers; if the owner reads
AG-10 more strictly, the remedy is a warm-ordering requirement in the Stage G spec, which is already
the recommendation either way.

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
