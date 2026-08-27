# Goal Session market-compass — Assumption Ledger

Append-only. Each entry records a scoring decision that required interpreting an
ambiguous goal, so the owner can veto it early.

## iter-16 — goal-decomposer (grounding the AVB correction formula in the diagnostic's own already-proven transform)

**Ambiguity:** The coordinator's ruling states the corrected values "must be derived deterministically from the already-committed iteration-15 provider evidence... and the proven surrounding stored convention" but deliberately does not prescribe the formula or the literal corrected values — "deriving them is the implementation's job." Two evidence-grounded formulas are numerically available at plan time: `corrected_volume = stored_volume_before / bridge_factor` (since `stored_volume_before` currently equals the raw provider volume on both bad dates) or `corrected_volume = provider_volume / bridge_factor` (reading the provider figure directly from the iteration-15 fetch artifact). These are numerically identical today but conceptually different derivations.

**We chose:** Specify `corrected_volume(date) = provider_volume(date) / bridge_factor`, reading `provider_volume` directly from the committed `j11-avb-provider-fetch-evidence.json` artifact — the SAME `expected_inverse_volume_ratio = 1/bridge_factor` transform the AVB diagnostic already computes and has proven matches the four surrounding calibration dates. Reasoning: grounding the formula in the independently-sourced provider figure (rather than in Trendora's own currently-wrong stored value, which happens to coincide with it only because the defect being fixed IS "stored volume was never transformed from the raw provider figure") keeps the derivation's provenance honest and auditable even though the two paths are numerically identical right now; it also directly reuses a formula and tolerance check the codebase already has tested and proven, rather than introducing a new one.

**Reversible:** yes — this is a specification choice for which input variable the derivation formula names, not a persisted decision; the spec itself requires the developer to fail closed and STOP if the resulting cross-check does not land within tolerance, so a wrong formula choice cannot silently produce an unverified write.

## iter-16 — goal-decomposer (the pre-boot guard's "cleared" state must be explicit, never inferred from partial per-date progress)

**Ambiguity:** The owner ruling requires the guard be "reusable and state-driven, not hardcoded" and "preserve normal latest-snapshot startup behaviour once the maintenance boundary is legitimately cleared," without specifying HOW "cleared" is determined. A plausible simpler design would infer clearance per-date from whether a `ScannerRun` already exists for that date (no new state needed at all) — but `docs/goal.md` J-11 step 13's failure/retry semantics separately establish that a partially-completed multi-date regeneration attempt must NOT be treated as accepted progress ("the clean-regeneration unit is the complete 11-date incident set, not an individual date checkpoint"), and per-date `ScannerRun`-presence inference would silently violate that rule the first time a future Stage D attempt fails partway through.

**We chose:** Require the guard's active/cleared decision to be driven by an EXPLICIT, persisted boundary-state marker (active-by-default for the current 11-date incident, date membership sourced from the existing `INCIDENT_DATES` canonical set) rather than inferred from partial per-date `ScannerRun` presence, and required a dedicated test (TC-28) simulating a partially-completed attempt to prove the guard still blocks in that case. Reasoning: this is the only design that is simultaneously state-driven (satisfies the ruling's literal requirement) and consistent with the ALREADY-BINDING step-13 whole-unit retry semantics; inferring clearance from row presence would be simpler to build but would create exactly the kind of silent, undetected safety regression this session's lessons (iteration 15's own B1 finding) exist to prevent.

**Reversible:** yes — this is a design constraint on a not-yet-built module; nothing is persisted or executed yet. If a future iteration's implementation finds a better-justified state representation that still satisfies both the ruling's text and step 13's whole-unit semantics, this entry does not bind it, and no evidence or artifact depends on this exact mechanism.

## iter-16 — goal-decomposer (certified-baseline supersession scope: only the daily_prices fingerprint field, not a wholesale re-certification)

**Ambiguity:** The "Raw inputs" Acceptance amendment states "the post-correction fingerprint becomes the new certified J-11 raw-input baseline... every check above is evaluated against that new baseline" without specifying whether the WHOLE certified-baseline artifact must be rebuilt from a fresh iteration-16 capture, or only the one field the correction actually affects.

**We chose:** Scope the supersession narrowly — `load_stage_d_certified_baseline`'s `daily_prices_fingerprint` field is superseded by the post-correction value; every other field it composes (`manifest_ddl`, `manifest_dump`, `manifest_row_count`, `data_provider_runs_count`, `watchlist_count`) continues to source, unchanged, from the original iteration-13 artifacts. Reasoning: the AVB correction touches only `daily_prices`; none of the other certified fields' underlying tables are touched by this iteration (proven by TC-17), so re-deriving them from a fresh iteration-16 capture would be a needless second source of truth for values that have not changed and are already certified — exactly the kind of drift iteration 11's REGRESSION lesson warns against ("a SQLite rebuild has two possible sources of truth... they are not the same object"). Narrow supersession keeps the baseline's provenance chain honest and auditable field-by-field.

**Reversible:** yes — this is a composition-scope choice for a not-yet-built artifact; if a future iteration or the owner prefers a wholesale re-certification instead, that is an additive change (capture everything fresh) with no prior evidence to unwind, since the narrow version's fields are a strict subset of what a wholesale capture would also produce.

## iter-16 — goal-evaluator (reading "proven on disposable test state" as necessary, not sufficient)

**Ambiguity:** The owner's 2026-08-25 pre-boot-guard ruling says "Until that guard is proven on
disposable test state, maintenance isolation remains ACTIVE and the live backend must not be booted."
The guard IS proven on disposable test state (19 fixture tests, all passing, calling the real
`warmup.ensure_latest_snapshot`). But its state was never registered against the live database — no
`maintenance_boundaries` table exists there, `register_j11_incident_boundary` has no production caller,
and `evaluate_boundary_for_date` returns `blocked=False` on an empty table — so booting the backend
today still writes a `ScannerRun` onto 2026-08-12. The ruling does not say whether satisfying its
literal proof clause is enough to lift isolation, or whether its stated purpose ("prevents canonical
producer writes for dates explicitly quarantined") must also hold in production.

**We chose:** treat the clause as a NECESSARY condition only — maintenance isolation stays ACTIVE, and
the ruling's precondition for resuming any application/browser/replay lane is recorded as NOT
satisfied. Reasoning: (a) the sufficient reading is self-defeating — it would let a guard that is inert
in production unlock booting the live backend, immediately causing the exact write the ruling was
written to prevent; (b) the ruling's own operative sentence requires a guard that "prevents ... writes
for dates explicitly quarantined by an ACTIVE ... boundary", and on the live database there is no
active boundary, so nothing is prevented; (c) fail-closed is this goal file's posture throughout J-10
and J-11. What I explicitly did NOT do: call the implementation defective — it is correct, genuinely
reusable and genuinely state-driven (its core check contains zero incident-specific conditionals), and
arming it needs a live write that this iteration was never authorized to make, so I recorded it as a
scope collision rather than an oversight. I also scoped the danger honestly: the window is now until
Stage D completes, Stage D itself is not endangered (controlled writer, not a booted service), and the
boot path self-heals once the eleven dates hold runs again because `run_scan` is create-once.

**Reversible:** yes — one owner line either way. Nothing is mutated, deleted or foreclosed by keeping
isolation active; if the owner reads their own clause as sufficient, lifting isolation is a one-line
instruction, and the recommendation already names arming the boundary as option one.

## iter-16 — goal-evaluator (recording the boot-path `select(MaintenanceBoundary)` as a MINOR AG-8 entry)

**Ambiguity:** AG-8's text forbids "unbounded whole-table ORM loads", and
`j11_preboot_guard.py:143` issues `session.exec(select(MaintenanceBoundary)).all()` on the shared boot
path (auditor observation B7, evaluator-confirmed by reading the code). But AG-8's title and body are
about resilience to data-shape and data-SCALE change ("widening the data basis must never crash an
existing page or exhaust memory"), and `maintenance_boundaries` is a control table holding one row per
named boundary, read once per boot — it never widens with the data basis. `docs/goal.md` does not say
whether AG-8's letter binds outside its stated subject.

**We chose:** record it in the ledger as `severity: minor`, `resolved: false`, with the
letter-but-not-subject reasoning stated openly in the entry itself. Reasoning: (a) the pattern the
anti-goal names is literally present, and on the boot path every journey's serving depends on, so
silently declaring it a non-violation would be the evaluator overruling the owner's text without
saying so; (b) the fail-closed "when unsure, treat as critical" rail governs the critical/minor axis
and I am NOT unsure there — a one-row table read once per boot cannot exhaust memory or crash a page;
(c) recording it costs one boolean and gives the next iteration a concrete one-line rider, whereas
omitting it would leave QA's incorrect "No new unbounded whole-table loads" line as the only record.
Consequence I accepted knowingly: an unresolved entry blocks GOAL_ACHIEVED until fixed — acceptable,
since the fix is one line and GOAL_ACHIEVED is far away (J-07 and J-08 still failing, J-11 incomplete).

**Reversible:** yes — one boolean, or one owner line downgrading it to a non-violation; the full
reasoning and file:line are preserved in the ledger entry either way.

## iter-16 — goal-evaluator (STALLED again, on the first iteration whose gate answered YES)

**Ambiguity:** This is the fourth consecutive STALLED, and it is the first where the readiness gate
answered `YES`. Real non-owner work exists (re-run readiness with `volume_override` to correct the
recorded label, bound the AG-8 select, add the missing live-shaped guard test), which reads like
CONTINUE under the methodology's C.5. The stall-window reading is also arguable — iterations 13-16
each made genuine forward progress, so this is not a "no progress" stall.

**We chose:** STALLED under C.2 (every unblock path for the current blocker is human-owned),
first-match-wins, with the three tractable items named explicitly as riders rather than hidden.
Reasoning: (a) the owner's own ruling text ends this step verbatim — "Even if the subsequent readiness
evaluation returns `J-11 STAGE D READY: YES`, STOP for owner review" — so a CONTINUE would let the
decomposer plan the one step the owner forbade; (b) arming the pre-boot guard, the only item with real
operational consequence, requires a live write outside this iteration's two-cell authorization, and
every live write this session has been separately and explicitly authorized; (c) none of the tractable
riders can change the gate's answer — both AVB-A and AVB-B are in `_AVB_READY_CLASSIFICATIONS`; (d) the
mechanical consequence is asymmetric in the SAFE direction, as in iteration 15: a stopped engine starts
no backend, and an unarmed guard means starting the backend is exactly what must not happen. What I
explicitly did NOT do: describe the tractable work as out of scope or illegal — it is listed as three
named riders, and arming the guard is promoted to the FIRST item of the recommendation, ahead of the
Stage D decision itself.

**Reversible:** yes — one owner line (or an instruction plus `--resume`) restarts the session with
nothing repaired, nothing lost and no journey status changed.

## iter-17 — goal-decomposer (bundling the AVB-A label-correction rider into the maintenance-boundary lifecycle iteration)

**Ambiguity:** The owner's 2026-08-25 "J-11 maintenance-boundary lifecycle AUTHORIZED" ruling scopes
this iteration precisely to the guard/lifecycle work (arm/disarm entrypoints, the AG-8 fix, fail-closed
hardening, 9 named tests) and is silent on iteration 16's three small riders. The AG-8 fix and a named
test for the live-shaped case are already subsumed by the ruling's own requirements 3 and 6, but the
`volume_override` AVB label correction is not mentioned anywhere in the new ruling.

**We chose:** fold the `volume_override` re-run into this iteration as one small additional backend
item. Reasoning: (a) it is read-only against the live DB (same discipline iterations 12-16 already use),
writes nothing, and cannot change the `READY: YES` answer (both `AVB-A` and `AVB-B` are in
`_AVB_READY_CLASSIFICATIONS`); (b) iteration 16's own recommendation explicitly asked for it to "ride
along whenever the next run happens," and this is that next run; (c) leaving a known-dishonest `AVB-B`
label and an unsupported "other tickers shifted" claim on the live record for a further iteration would
compound exactly the uncorrected-record risk this goal's AG-1 honesty posture exists to prevent, at
effectively zero marginal risk or scope cost. This is explicitly NOT a re-run of
`run_j11_avb_correction.py` (spent, "do not redo") — only the read-only classification/diagnostic is
re-derived, into a new iter-17 artifact, leaving iteration 16's own artifact byte-unedited.

**Reversible:** yes — this produces one new, additive, read-only evidence artifact; it edits no code path
any other requirement depends on, and if a future decomposer or the owner judges it should not have been
bundled, the artifact can simply be ignored with nothing to unwind.

## iter-17 — goal-evaluator (scoring an understated-but-not-false safety framing)

**Ambiguity:** The coordinator asked me to judge whether this iteration's claims are "honestly stated" given
that TC-11's green `blocked: False` records an open live exposure. `docs/goal.md` sets no rule for the case
where an iteration's every stated fact is true, its owner-facing status lines are exactly as specified, and
the ONE thing omitted is what the recorded result means for the live system. AG-1's honesty posture governs
proven-language about scores, not the framing of a safety probe; the methodology's honesty self-check (E.5)
asks whether I marked unverifiable things `unknown`, not how to grade another lane's emphasis.

**We chose:** score it as UNDERSTATED, not dishonest — no anti-goal entry, no verdict penalty, no downgrade
of J-11's advance — while making the exposure the HEADLINE of eval.md, the evaluator log and J-11's `gap`,
ahead of the delivered work. Reasoning: (a) every individual claim checks out and I re-derived all of them;
the four owner-facing lines (`NOT ACTIVE`, `NOT ARMED`, `READY: YES`, `AUTHORIZED: NO`) are exactly right
and do carry the substance; (b) the owner's own ruling text already documents that ordinary boot mints the
table, so the owner is not being misled about a fact they do not have; (c) the root cause is the SPEC, which
defined the probe's unsafe answer as its passing value — blaming the developer for inheriting his own
spec's framing would misplace the defect; (d) the fail-closed rail applies to critical/minor severity, and
there is no violation to grade here. What I explicitly did NOT do: soften the exposure, call it a footnote,
or leave it at the auditor's placement — I raised it above the delivered slice everywhere it appears, and
stated plainly that a reader of the developer/reviewer/QA reports alone would not learn it.

**Reversible:** yes — nothing is mutated or foreclosed. If the owner judges the framing a reportable
honesty breach, adding a ledger entry is one JSON object, and every figure and derivation is preserved.

## iter-17 — goal-evaluator (STALLED a fifth time, when the safety hole is real but no non-owner action closes it)

**Ambiguity:** This is the fifth consecutive STALLED (iters 13-17), and it carries the strongest pull toward
CONTINUE the session has seen: B1 is an exposure that is live RIGHT NOW and fires from an ordinary act
(anyone starting the backend), with no decision required for it to happen. `docs/goal.md`'s Loop-mechanics
gate arguably permits safety work ("plus explicit prerequisites such as the depth/safety control"), and
iteration 15 faced this same shape and the tractable answer then WAS to build something (the guard, which
iteration 16 duly built). Real non-owner work also exists this iteration (four named riders). The
methodology's C.5 would read that as CONTINUE.

**We chose:** STALLED under C.2 (first-match-wins), with the four riders named explicitly rather than
hidden, and the safety decision promoted to the first item of the recommendation. The load-bearing new
reasoning, which distinguishes this from iteration 15: I checked directly whether ANY non-owner engineering
closes the hole, and none does. Making the guard fail closed on a missing table has zero effect, because
`main.py` creates the table before the guard ever runs (verified by reading `main.py` and
`warmup.py`). Making it fail closed on an EMPTY table would block every normal boot forever and break every
other journey's future browser lane — a design decision with wide blast radius that the owner owns. And
inferring quarantine from per-date `ScannerRun` absence would re-introduce exactly the inference the
iter-16 decomposer rejected against step 13's whole-unit retry semantics. So unlike iteration 15, there is
no buildable safety deliverable left: arming needs a table whose creation the owner forbade by name, and
the rebuild needs a fresh written instruction. The mechanical consequence is also asymmetric in the SAFE
direction — a stopped engine starts no backend, and starting the backend is precisely what must not happen.

**Reversible:** yes — one owner line (or an instruction plus `--resume`) restarts the session with nothing
repaired, nothing lost and no journey status changed; if the owner prefers the riders done first, they are
already listed and need no rework here.

## iter-18 — goal-decomposer (bundling three small evidence/test riders into the table-create-and-live-arm iteration; excluding framework-level riders)

**Ambiguity:** The owner's newest 2026-08-25 ruling ("J-11 exact maintenance-boundary table creation
and live arm AUTHORIZED") scopes this iteration precisely to schema creation, boundary activation, and
closing the background-warmup coverage gap, and is silent on iteration 17's own "FOUR SMALL JOBS RIDE
ALONG" plus "TWO STANDING FRAMEWORK NOTES" recommendations. `docs/goal.md` does not say whether an
evaluator's recommended non-owner riders should ride along with an owner-authorized live-database
iteration.

**We chose:** fold in three of the four small jobs — refusal tests for the two iteration-17
evidence-writing CLI tools; correcting the AVB diagnostic note's "genuinely independent" wording;
correcting the iteration-17 report's damaged-date list — as low-risk backend/evidence-artifact edits,
explicitly sequenced after the primary safety work and marked non-blocking. We excluded the fourth small
job (the `build_review_packet`/git-diff-only proof gap) and both "standing framework notes" (the
`scripts/automation` forbidden-lane defect and `goal_gate.py`'s duplicate-journey-heading defect), because
all three are `.claude`/`scripts/automation` FRAMEWORK/tooling defects, not Trendora product code —
outside a goal-mode product iteration's remit per CLAUDE.md's mode separation, and consistent with how
iterations 13-17 have already carried them forward untouched rather than pulling them into product specs.
Reasoning for including the first three: each is a zero-risk, isolated edit to evidence artifacts or test
coverage for already-built tooling (no live-database interaction, no code path any Data Contract value
depends on), directly requested by the immediately-prior evaluator as safe to ride along ("none of which
can change that decision"), and mirrors iteration 17's own precedent of bundling the AVB label-correction
rider into the maintenance-boundary lifecycle iteration.

**Reversible:** yes — all three folded-in riders are additive test coverage or corrections to
already-written prose in evidence/report artifacts; none touches the live database or any code path a
Data Contract value depends on. If a future decomposer or the owner judges any of the three should not
have been bundled, they can be reverted or ignored with nothing else to unwind.

## iter-18 — goal-evaluator (the ruling's boot gate opened, but the Loop-mechanics lane gate did not)

**Ambiguity:** The owner's 2026-08-25 ruling items 5 and 6 (`docs/goal.md:1703-1711`) state the boot
prohibition as a condition: *"Do not boot the app until: the table exists; the J-11 row is active; and a
direct live guard probe proves the latest quarantined date is blocked"* and *"The live guard must be
proven ARMED before normal backend boot is allowed."* All three conditions are now satisfied and
independently verified, so by its own terms that specific prohibition has lapsed. But item 9 of the same
ruling says *"Even if all three are established, STOP"*, and the separate, older Loop-mechanics clause
(`docs/goal.md:2087-2090`) says *"No developer, reviewer, QA, browser-QA, evaluator, coherence, research or
proposer lane may run against the knowingly damaged database before J-11 Stage G passes."* The goal file
never says which of these governs iteration 19's depth/isolation setting.

**We chose:** read them as governing DIFFERENT things and both still binding — the ruling's boot gate has
lapsed (booting is no longer forbidden by that clause), while the Loop-mechanics gate independently keeps
every normal lane shut until Stage G, so maintenance isolation should stay ON and browser QA must NOT
resume. Reasoning: (a) the two clauses have different subjects (an act vs. a set of lanes) and different
triggers (guard ARMED vs. Stage G passed), so satisfying one cannot discharge the other; (b) item 9's
STOP is scoped to the table-create/arm iteration and its stated rationale is Stage D authorization, so it
does not by itself re-impose the boot ban; (c) independently of both, I found that
`scanner.resolve_run` still writes a canonical `ScannerRun` for any `?as_of=` date with no boundary check,
so treating the boot gate's lapse as "safe to run the app again" would re-open, by a different door, the
exact accident the ruling exists to prevent. What I explicitly did NOT do: call the boot gate still
closed — that would misquote the owner's own condition, which is met.

**Reversible:** yes — one owner line either way, and it is an operator-only control (maintenance isolation
is set by the human dispatching the spec, `.claude/anti-patterns/25`), so this evaluator's reading is a
recommendation, not a setting. Nothing is mutated or foreclosed by keeping isolation on for one more
iteration.

## iter-18 — goal-evaluator (STALLED a sixth time, with a real engineering item on the table)

**Ambiguity:** This is the sixth consecutive STALLED (iters 13-18) and the first where the authorized work
fully SUCCEEDED. Genuinely buildable non-owner work exists: a boundary check on `scanner.resolve_run`
(my own finding), a boundary check on `data_manager._do_backfill` (auditor B4), and the warm-up counter
decision (auditor B2 / reviewer MINOR). The methodology's C.5 would read available tractable work as
CONTINUE, and iteration 15 faced a similar shape where the answer WAS to build something.

**We chose:** STALLED under C.2 (first-match-wins), with all three items named explicitly as riders rather
than hidden. The load-bearing new reasoning: closing the `resolve_run` hole requires editing
`app/api/*` / the serving path, and the untouched state of exactly those files
(`apps/backend/app/api/*`, `scoring.py`, `sectors.py`, `compass.py`) is the ONLY basis on which J-01, J-04
and J-10 currently carry forward as passing — the iteration spec's own TC-17 makes that argument. Editing
them while browser QA is forbidden would destroy the carry-forward argument for three journeys and could
not be verified by anything. It also requires deciding what a blocked page request should RETURN, which is
a user-visible product decision, the same class the auditor declined to make unilaterally for B2. So none
of the three is safe non-owner work; each needs an owner call, and the critical path (Stage D -> Stage G ->
lanes reopen) is owner-owned end to end. The mechanical consequence is asymmetric in the SAFE direction:
a stopped engine boots no backend and issues no `?as_of=` request.

**Reversible:** yes — one owner line (or an instruction plus `--resume`) restarts the session with nothing
repaired, nothing lost and no journey status changed; if the owner prefers the riders done first, they are
already listed and need no rework here.

## iter-18 — goal-evaluator (riders 6b/6c edited prior-iteration evidence artifacts; scored as NOT an AG-17 breach)

**Ambiguity:** AG-17 says *"The incident record itself is evidence: the iter-5 drill result, its handoff,
the reviewer/QA evidence already produced ... MUST NOT be deleted, rewritten, or silently superseded."*
Rider 6b rewrote two `note` fields IN PLACE inside `runs/goal-market-compass-iter-17/j11-avb-bridge-diagnostic.json`,
and rider 6c inserted a correction block into `reports/phase-goal-market-compass-iter-17-ui-test-plan.md`.
The auditor, meanwhile, declined to correct iteration 17's QA report (finding E1) *citing AG-17*. So the
same iteration applies two different standards to three iteration-17 artifacts.

**We chose:** score both riders as NOT an AG-17 violation, and record no ledger entry. Reasoning: (a) AG-17's
protected set is the *iter-5 drill* incident record specifically, and neither artifact is iter-5 drill
evidence; (b) neither correction is *silent* — 6b's replacement text names itself as an iter-18 correction
and quotes the wording it repudiates, and 6c is purely additive with a dated correction heading, so the
prior claim remains readable in both; (c) both riders were ordered by the iteration spec, which the owner's
own ruling scope permits. What I explicitly did NOT do: endorse the inconsistency — the auditor's stricter
line on the QA report is defensible and its recommendation to *annotate rather than rewrite* is the better
pattern; 6b's in-place edit would have been safer as an appended correction, as 6c's was.

**Reversible:** yes — both artifacts are committed text with the original recoverable from git; adding a
ledger entry later is one JSON object, and every figure is preserved.

## iter-19 — goal-decomposer (scoping this iteration to Stage D alone, not the full authorized D→G sequence)

**Ambiguity:** The owner's 2026-08-26 ruling ("J-11 Stage D through Stage G recovery execution
AUTHORIZED") authorizes the complete Stage D → E → F → G sequence in one ruling and states failure/retry
semantics as a single "whole attempt," but it never states whether that authorized sequence must be
delivered inside one decomposer iteration/dispatch or may span several, each re-verifying the frozen
identity and boundary state before continuing.

**We chose:** scope iteration 19 to Stage D only — freeze the fresh attempt identity, regenerate exactly
the 11 canonical incident dates through the existing `scanner.run_scan`/`persist_run_payload` path, and
STOP with the ruling's own item-14 terminal-outcome status lines — leaving Stage E (forward-return hole
repair), Stage F (cache invalidation) and Stage G (full verification/acceptance gate) to later
iterations. Reasoning: (a) every prior J-11 stage/step in this session (B1 migration, Stage C clear, the
AVB correction, the pre-boot guard build, the table-create-and-arm) was its own iteration, and the
codebase's own `j11_stage_d.py` module is deliberately readiness-only ("It performs NO Stage D
execution") — a separation of concerns the existing code already encodes; (b) Stage D, Stage E and Stage
F are each independently risky live mutations with distinct failure modes (identity/layer-boundary
correctness; forward-return hole classification; per-cache disposition), and the decomposer's own
priority rubric forbids bundling two risky changes in one diff because a joint failure is undiagnosable —
that risk is worse, not smaller, when the changes are sequential stages of the SAME destructive attempt;
(c) nothing in the ruling requires single-dispatch delivery — it requires a consistent frozen identity and
continuous maintenance isolation across the attempt, both of which hold whether the attempt spans one
iteration or several, and item 13's "next Goal Mode resume" language describes one continuous engine run
(which can still process multiple internal iterations), not one single dispatch; iteration 20's Stage E
work will re-verify the frozen identity is unchanged before proceeding rather than assuming it.

**Reversible:** yes — if Stage D's live execution succeeds cleanly this iteration, nothing about stopping
there forecloses Stage E/F/G in iteration 20; if the owner or a future decomposer judges the stages should
have been combined, no work already done needs to be undone, only continued.

## iter-19 — goal-decomposer (excluding iteration 18's remaining evidence-correction riders from this iteration)

**Ambiguity:** Iteration 18's evaluator recommendation carried four small non-blocking jobs. This
iteration's owner ruling explicitly defers two of them (the ordinary-request and Data-Manager guard gaps:
"Ordinary request / Data-Manager guard gaps are recorded but deferred... Record these gaps as post-J-11
maintenance-boundary hardening work after Stage G"). It does not explicitly say whether the two remaining
low-risk documentation items — annotating iteration 17's QA report and fixing the "nothing else changed"
evidence method to a true content hash — should ride along with the Stage D iteration, the way similar
small riders rode along with iterations 17 and 18.

**We chose:** defer both to a future iteration rather than bundling them into iteration 19. Reasoning: (a)
the new ruling's own repeated language ("Do not expand the Stage D recovery iteration...", item 12's "Do
not use this authorization to work on...unrelated product backlog while J-11 remains incomplete") sets a
materially stricter scope tone than the two prior rulings that authorized the small riders iterations
17/18 bundled; (b) Stage D is itself the single riskiest live-database operation this session has
performed since Stage C, and the decomposer's own tie-breaking rule prefers the smallest concrete change
set for a risky journey — adding unrelated evidence-file edits, however low-risk in isolation, dilutes
reviewer/auditor attention at exactly the iteration needing maximum scrutiny; (c) unlike iterations 17/18's
riders, neither remaining item blocks or is blocked by Stage D's own correctness, so no cost is paid by
waiting one more iteration.

**Reversible:** yes — both are pure evidence/documentation corrections to already-committed text;
deferring them loses no information and either can be picked up in the very next non-Stage-D-critical
iteration.

## iter-19 — goal-decomposer (requiring a fresh live preflight re-verification, including a re-derived AVB classification, immediately before Stage D's first write)

**Ambiguity:** The iteration-18 "Do not redo" note in the iteration-state digest says Stage D readiness
(`READY: YES`, `AVB-A`) is "carried by citation... do not re-derive." Taken literally that could be read
to forbid re-running the AVB diagnostic or the Stage D preflight gate this iteration. But `docs/goal.md`'s
own Stage C precedent (C2) required a mandatory fresh preflight immediately before Stage C's first
destructive statement, "do NOT trust iteration-10/11/12 counts merely because they were certified," and
`j11_stage_d.py`'s own docstring states a real future Stage D execution "must call
[`freeze_stage_d_attempt_identity`] fresh, immediately before its first write" — the existing code was
built expecting exactly this re-verification step.

**We chose:** read the "do not redo" note as governing the PLANNING question (whether Stage D is
theoretically ready and authorized — settled, and not to be re-litigated) rather than the EXECUTION
precondition (whether the live state a destructive write is about to act on still matches what was
certified) and require the Stage D execution script to re-run the existing preflight/readiness tooling —
the same functions, not a reimplementation — immediately before writing. Reasoning: (a) this is the
identical pattern C2 already established for Stage C, and the goal text never suspends it for Stage D; (b)
two live-database iterations (17, table-missing; 18, table-create-and-arm) happened between the iter-17
readiness capture and now, and while neither should have touched `daily_prices` or engine/scoring code,
"should not have" is exactly the kind of claim this session's own audits have repeatedly found needs
independent re-derivation rather than trust; (c) the check is cheap (read-only, reuses existing functions)
against an irreversible, high-consequence write.

**Reversible:** yes — this only adds a read-only verification step; if the re-verification simply
reproduces the iter-17 figures (the expected outcome), nothing changes and no extra artifact contradicts
anything already on record.

## iter-19 — goal-evaluator (CONTINUE rather than a seventh STALLED, on the ruling's own STOP condition)

**Ambiguity:** The owner's 2026-08-26 ruling item 14 says the recovery attempt "must end in one of two
honest states" — SUCCESS (D/E/F/G all YES, FULLY REPAIRED) or INCOMPLETE — and adds "There is no third
state." The INCOMPLETE block's instruction ends "...and STOP." But INCOMPLETE's stated trigger is "any
failure, refusal or unmet gate from Stage D onward before Stage G passes," and none of those occurred:
Stage D executed completely with every check passing. The ruling never says whether a *clean, unfinished*
attempt (Stage D done, E/F/G not yet started, which is the shape the iteration-19 decomposer deliberately
chose and logged) is the INCOMPLETE state that must STOP, or simply the middle of an authorized sequence.

**We chose:** read the STOP as attached to its stated trigger — a failure, refusal or unmet gate — and
therefore NOT fired this iteration, so the verdict is CONTINUE with Stage E as the target. Reasoning:
(a) the ruling's items 1, 7, 8 and 9 explicitly authorize Stage E, Stage F and Stage G, so no human-owned
action gates the next step and decision-tree C.2 does not match; (b) unlike the three prior rulings
(iters 16/17/18), this one contains NO unconditional "even if everything succeeds, STOP" clause — the
earlier rulings' item 9 said exactly that, and its absence here is a deliberate change; (c) item 13 frames
the D→G execution as one continuous "Goal Mode resume" with fixed launch conditions, which supports
continuing inside the same engine run; (d) the strict "no third state ⇒ stop after every unfinished stage"
reading would make a multi-iteration D→G impossible, so Stage G could never be reached — which cannot be
the intent of a ruling that authorizes Stage G. What I explicitly did NOT do: treat this as permission to
relax anything else — maintenance isolation, the ACTIVE boundary and the app staying OFF all remain
binding, and I said so as the first rider.

**Reversible:** yes — one owner line stops the run with nothing repaired further, nothing lost and no
journey status changed; the Stage D evidence and the recorded attempt-membership set (run ids 3148-3158)
survive either way, and if the owner prefers a per-stage authorization the riders are already listed and
need no rework here.

## iter-19 — goal-evaluator (ruling item 2's "do not reuse the iteration-14 identity" read procedurally, not as a value requirement)

**Ambiguity:** Ruling item 2 says "Do **not** reuse: the iteration-10 identity; the iteration-14 identity;
the iteration-16/17/18 readiness identity; or any historical frozen identity," and the phase spec's
DEFINITION OF DONE bullet 2 requires the frozen identity be "distinct from every historical identity
already on disk." The frozen Stage D identity `53d2ffd1…` EQUALS the iteration-14 and
iteration-16/17/18 readiness values (the auditor's B1). The spec's own TC-3 contradicts both, requiring
only an honest "equal-or-not" comparison.

**We chose:** score the requirement as MET on the procedural reading — recompute fresh with the canonical
function, never copy — and record the equality openly rather than as a violation. Reasoning: (a) I
recomputed the digest myself from the three provenance files on disk plus the recorded config subset and
reproduced `53d2ffd1…` exactly, and `git log` shows those files last changed at iter-12 and `config.yaml`
at iter-4, all clean in the working tree — so the equality is mathematically forced, not a copied value;
(b) the same ruling's item 6 forbids changing scoring formulas/thresholds and item 12 requires the
identity be "recomputed with the canonical `compute_engine_identity` ... never hardcoded", so the value
reading is unsatisfiable without violating the same ruling; (c) `compute_engine_identity` hashes only code
files and config keys and never touches data, so item 2's "must represent the actual code, config and
certified data baseline" cannot be a value test on the data component either. What I explicitly did NOT
do: call this harmless — I carried the auditor's real consequence forward as a blocking design input for
Stage G (identity alone cannot establish attempt membership; use the recorded run-id set 3148-3158 and
assert no twelfth run carries the stamp), and named it as the one item to settle before Stage G is
designed.

**Reversible:** yes — nothing is mutated by this reading; if the owner intends the value reading, the
remedy is an owner ruling recorded in `docs/goal.md`, and the eleven rebuilt runs' membership is already
recorded independently of the stamp.

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
