# Goal Session market-compass — Assumption Ledger

Append-only. Each entry records a scoring decision that required interpreting an
ambiguous goal, so the owner can veto it early.

## iter-14 — goal-decomposer (closing the iter-13 identity-comparison blind spot at Stage D, not by patching completed Stage C code)

**Ambiguity:** The coordinator's directive to "close the identity-comparison blind spot the iteration-13
auditor found" names the finding (`j11_stage_c.py:264-334`'s `compare_preflight_to_certified` CAPTURES
`stage_c_attempt_identity` but never COMPARES it) without saying whether the fix is a patch to that
already-executed function, or new comparison call-sites built for Stage D. `docs/goal.md` does not
itself define what "closing" this gap requires.

**We chose:** Realize the fix entirely as NEW code for Stage D — the three fail-closed identity checks
(A/B/C) reusing `j11_maintenance.check_attempt_identity_consistency` — and leave `j11_stage_c.py`
unmodified. Reasoning: Stage C's own deletion reads no identity at all (grep-verified, iter-13's own
docstring states this), so the captured-but-uncompared value was always inert for Stage C specifically;
the blind spot's real future consequence is entirely at Stage D, whose whole correctness claim is "every
rebuilt run shares one frozen identity" (step 12). Stage C already executed and is on the binding
"do not redo" list (`iteration-state.md`); patching dead code in a completed, closed stage for cosmetic
completeness adds risk (touching frozen, already-audited code) for no operational benefit, since no future
call site would ever exercise the patched comparison.

**Reversible:** yes — if a future iteration finds value in also patching `j11_stage_c.py`'s inert capture
for documentation/consistency, that is a small additive change; nothing in this iteration's Stage D work
depends on `j11_stage_c.py` being touched, and no evidence or artifact from Stage C is altered either way.

## iter-14 — goal-decomposer (AVB counterfactual B's "raw provider close" is derived arithmetically, never re-fetched)

**Ambiguity:** The coordinator's three counterfactual ADV representations name "B: raw provider close ×
raw provider volume" without saying how to obtain a raw (unbridged) provider close for 2026-08-11/12,
when only the bridged close is stored in `daily_prices` and AG-9's recovery-fetch exception is exhausted
(no new network call is authorized).

**We chose:** Derive representation B's close arithmetically as `stored_bridged_close / bridge_factor`
(the persisted `2.7930001225759193` from `runs/goal-market-compass-iter-9/j10-population-evidence.json`),
never via a new fetch. Reasoning: `j10_recovery.py`'s bridge step is a single scalar multiply applied to
all four OHLC fields and explicitly never to volume (verified: `volume=b.volume` unchanged at the
application site) — the transform is invertible with the already-known, already-persisted factor, so the
"raw provider" scale is fully recoverable from stored data without touching the network, AG-9, or J-10's
closed status. Volume for both A and B is identical (the same stored value), since volume was never
bridged in either direction — this is itself a finding the diagnostic must state plainly, not obscure.

**Reversible:** yes — this is a read-only arithmetic derivation choice for a diagnostic artifact; it
mutates nothing, and if the developer's own re-derivation of the bridge application disagrees (finds
volume WAS touched, or finds the multiply was not a single uniform scalar), the spec's own TC requires
reporting that correction and re-deriving representation B correctly rather than trusting this entry.

## iter-14 — goal-evaluator (overturning four lanes' AVB-B to AVB-D on the volume half)

**Ambiguity:** The iteration spec's Goal 4 defines AVB-B as "material effect, but the canonical stored
convention is internally consistent" and AVB-D as "evidence insufficient — STAGE D NOT READY, do not
guess", without saying whether "internally consistent" may be established from the transform's CODE
(what J-10 did) plus contract text (`docs/goal.md`: "volume is not a price and is not scaled"), or must
be established from MEASUREMENT of the stored series (the spec's own TC-21 says "from the stored series
itself, never from finance convention alone"). The developer, reviewer, QA and auditor all landed on
AVB-B; the auditor explicitly noted that on the artifact's own evidence it is "AVB-D territory".
**We chose:** AVB-D, i.e. `J-11 STAGE D READY: NO`. Reasoning: (a) the code and the contract establish
what J-10 DID and that it was authorized, not that the RESULT is on one consistent basis — which is
what AVB-B asserts; (b) the artifact's classifier never reads volume and cannot emit the one label that
would flag a volume problem, so its "+raw" half is an assertion, not a measurement; (c) the auditor's
two rescuing props do not survive checking (the calibration series does carry volume —
`j10_recovery.py:643` + `yahoo_provider.py:351-369`; the pool-wide check excludes the only symbol at
risk); (d) the deciding measurement was discarded in iteration 9 (`j10_recovery.py:644` kept only
`b.close`) and now needs a network call AG-9 forbids; (e) my own read-only statistics lean the other
way on 2026-08-11 (deflating by the exact bridge factor moves it from the 98.7th to the 39.8th
percentile of AVB's own distribution) and the provider demonstrably re-based AVB's price series between
the ingest and the comparison fetch. Fail-closed is the goal file's own posture throughout J-10/J-11.
What I explicitly did NOT do: claim AVB-C (the "materially affects canonical Stage D output" half is
not met — the traced impact is bucket E→E, admission unchanged, eligibility False→False), or assert
that the volume IS wrong.
**Reversible:** yes — one bounded read-only comparison fetch of AVB's volume for already-stored days
(one dated goal.md amendment) settles it either way, and a dated owner acceptance of the residual
reaches the same place without any fetch; nothing is mutated, deleted or foreclosed by recording NO,
and the AVB rows themselves are untouched.

## iter-14 — goal-evaluator (recording the in-iteration evidence overwrite as a CRITICAL but RESOLVED anti-goal entry)

**Ambiguity:** A new test overwrote three committed iteration-13 Stage C evidence files — the class of
act AG-17 ("the incident record ... MUST NOT be deleted, rewritten") and ruling C5 ("do not rewrite ...
incident evidence") forbid. But it never shipped: the reviewer FAILed the iteration, the files were
restored byte-for-byte, and the root cause was fixed inside the same iteration. `docs/goal.md` does not
say whether a violation caught and fully reversed within its own iteration belongs in the ledger at all,
and a `critical` + `unresolved` pair would mechanically force a REGRESSION halt.
**We chose:** record it, severity `critical`, `resolved: true`, with the mechanism and the restoration
proof preserved verbatim. Reasoning: (a) omitting it would make the ledger dishonest about what the
iteration actually did to the repository; (b) the `resolved` flag's operative question is whether the
violation still demands action, and it does not — three parties plus my own `git status --porcelain`
check confirm the byte-for-byte restoration; (c) this matches the session's own precedent (the iter-8
entry was resolved after the damage was undone byte-for-byte), whereas the iter-11 entry was resolved
only by an explicit owner acceptance because the damage was NOT undone.
**Reversible:** yes — one boolean, with the full original evidence text retained, so the owner or a
later evaluator can flip it back at no cost.

## iter-14 — goal-evaluator (STALLED again, when a non-owner-owned honesty fix demonstrably exists)

**Ambiguity:** Iteration 13 returned STALLED partly because ruling C10 reserved an owner inspection
point; the owner answered by commissioning this hardening iteration, so that particular gate is spent.
Real, non-destructive, non-owner-owned work exists right now (close the classifier gap, give the
readiness artifact a producer, port the missing negative tests, commit the artifacts), which reads like
CONTINUE on the methodology's C.5.
**We chose:** STALLED, with the honesty fix offered as explicit option (c). Reasoning: (a) that work
cannot change the answer — re-running the corrected classifier on the same inputs still has no volume
comparable and still lands on AVB-D, so it converts a dishonest YES into an honest NO and stops there;
(b) every path that can actually clear the gate is human-owned — a new AG-9 amendment for a bounded
comparison fetch, a dated acceptance of the residual, or a rewording of the gate — and C.2 sits above
C.5 with first-match-wins; (c) Stage D itself still requires a separate, fresh owner instruction by the
owner's own C10/A12 pattern, so a CONTINUE would let the engine plan the one iteration that is
forbidden; (d) `docs/goal.md`'s Loop-mechanics gate shuts every other product/research/browser lane
until Stage G. What I explicitly did NOT do: hide the tractable work or call it illegal — it is named
as its own option and as a mechanical rider.
**Reversible:** yes — one owner line (or an instruction plus `--resume`) restarts the session with
nothing repaired, nothing lost and no status changed.

## iter-15 — goal-decomposer (the "compensating" volume hypothesis's exact arithmetic)

**Ambiguity:** The coordinator's Goal 3 asks for "whatever bridge-adjusted comparison tests whether price and volume rebasing compensate" and an "expected inverse volume ratio where relevant," without stating the exact formula. `docs/goal.md`/AG-9's dated exception #2 authorizes the fetch but not a specific compensation formula, and J-10's own evidence never modeled volume at all, so there is no precedent in this codebase for what "compensating" means numerically.

**We chose:** Modeled the compensating hypothesis as a reverse-split-like rebase where price and share-count-traded move inversely: `expected_inverse_volume_ratio = 1 / bridge_factor`, i.e. `volume_ratio = stored_volume/provider_volume` should land near `1/bridge_factor` under "bridged+compensating" (dollar volume `close*volume` approximately conserved across the rebase), versus near `1` under "bridged+raw" (volume never transformed) and near `1` for both ratios under "raw+raw". This spec instructs the tolerance to reuse the SAME relative-tolerance idiom the existing calibration-window price-ratio check already uses, as a named, documented module-level constant.

**Reversible:** yes — this is a diagnostic formula choice, not a decision affecting any persisted row. The spec explicitly requires the developer to treat this as a testable hypothesis validated against the REAL fetched evidence (Goal 2), not an assumption to encode blindly; if the fetched data implies a different rebase mechanic (e.g., a non-inverse relationship), the classifier must follow the actual evidence and the dev handoff must record the correction, per this iteration's own fail-closed, evidence-over-assumption posture.

## iter-15 — goal-decomposer (readiness-time identity re-derivation vs the binding "do not redo" protection on iteration 14's frozen artifact)

**Ambiguity:** `iteration-state.md`'s binding "Do not redo" list protects `runs/goal-market-compass-iter-14/j11-stage-d-attempt-identity.json` ("recompute at Stage D freeze time, never hardcode") and the coordinator's Goal 9 separately asks this iteration to "recompute and report the current engine identity honestly" for readiness purposes while explicitly forbidding treating it as a frozen, reusable Stage D execution identity. It is not stated whether re-deriving the identity again THIS iteration, for a different (readiness-reporting) purpose, counts as "redoing" the protected iteration-14 item.

**We chose:** Re-deriving the identity again this iteration is NOT a violation of the "do not redo" protection, because the protected item is Stage D's own freeze-for-execution act (a specific, consequential, do-not-repeat operational step), not the general capability of computing `engine_identity` read-only. This spec requires the re-derivation to be written to a distinctly-purposed artifact (this iteration's own fresh preflight capture, under `runs/goal-market-compass-iter-15/`) carrying explicit `readiness_time_only: true` / `authorizing: false` / `reusable_for_stage_d_execution: false` fields, and forbids writing it anywhere a future Stage D freeze would read as a pre-existing frozen value — so iteration 14's artifact stays untouched and un-superseded as the historical record of ITS OWN attempt, while this iteration's observation is clearly a new, separate, non-binding reading.

**Reversible:** yes — this is a labeling/scoping choice for a read-only observation; it deletes nothing, mutates nothing, and does not freeze any value a future Stage D could accidentally inherit. If a future decomposer or the owner judges even a readiness-time re-derivation should be avoided, that is a one-line spec change with no prior evidence to unwind.

## iter-15 — goal-evaluator (keeping J-10 `passing` after measuring a real defect in its own output)

**Ambiguity:** J-10 "Bounded recovery of the two deleted trading days" is recorded `passing` and was
explicitly CLOSED by the owner (`docs/goal.md`, 2026-08-24: "J-10 is closed and MUST NOT be reopened").
This iteration's authorized fetch proves, for the first time from measurement rather than inference, that
J-10's own output is defective for AVB: it multiplied the close by the bridge factor 2.7930 and wrote the
provider's untouched volume beside it, while Trendora's own stored convention on the four surrounding days
divides volume by the same factor (dollar_volume_ratio ~1.0000 there vs exactly 2.7930 on the two
recovered dates). So a journey recorded `passing` demonstrably produced two bars whose dollar volume is
2.793x too high. `docs/goal.md` does not say whether a closed journey's status may be reopened by a later
measurement of its output.

**We chose:** keep `passing`, do NOT re-stamp `last_verified_iter`, and record the full measurement as a
prominent caveat in J-10's `gap` plus in `eval.md`'s journey table and the iteration-state digest.
Reasoning: (a) the methodology's REGRESSION trigger requires a journey to MOVE `passing` -> `failing` from
this iteration's verification, and under maintenance isolation NO journey was tested at all — the
methodology's own carve-out says never `failing`/`regressed` on that basis; (b) nothing that worked stopped
working and no stored value moved — the condition has been in the data unchanged since iteration 9, so
this iteration measured it rather than caused it; (c) the owner's own ruling closed J-10, and flipping its
status would reopen it in substance, which the ruling forbids by name; (d) the finding already has a
correct home with real consequences — it is exactly what J-11's AVB-C gate is blocking on, so it is
recorded where it actually gates work rather than where it would only relitigate a closed decision. What I
explicitly did NOT do: soften the finding, describe it as hypothetical, or let `passing` stand without the
caveat attached — the J-10 gap now states the measurement, the 2.793x figure, and the honest nuance
(deflated, 2026-08-12 is still a ~96.9th-percentile share day, so only the DOLLAR figure is unambiguously
wrong; 2026-08-11 is almost entirely a scale artifact) so no later reader can take `passing` to mean AVB's
recovered bars are on the right basis.

**Reversible:** yes — one string. Every figure, the derivation and the full narrative are preserved in the
journey history and the evaluator log, so the owner or a later evaluator can reclassify at no cost and with
nothing to re-derive.

## iter-15 — goal-evaluator (STALLED again, when the tractable non-owner work is now a SAFETY item)

**Ambiguity:** Iterations 13 and 14 both returned STALLED while acknowledging tractable non-owner work
existed; both times that work was cosmetic-to-moderate (honesty fixes, negative tests) and provably could
not change the gate's answer. This iteration is different in kind: the tractable work now includes the
auditor's B1 — a pre-boot guard preventing an irreversible unauthorized write that is ARMED RIGHT NOW and
can fire from an ordinary act (anyone starting the backend), with no decision required for it to happen.
That is a much stronger pull toward CONTINUE with a safety target than iters 13/14 faced, and
`docs/goal.md`'s Loop-mechanics gate arguably permits it ("plus explicit prerequisites such as the
depth/safety control").

**We chose:** STALLED, with the B1 guard promoted to the FIRST item of the recommendation — ahead of the
AVB decision itself, and ahead of where the auditor placed it in emphasis. Reasoning: (a) the methodology's
tree is first-match-wins and C.2 matches — every route through the CURRENT blocker (the AVB convention) is
owner-owned, and Stage D is an irreversible step needing sanction by the plan's own C10/A12 pattern; (b)
the B1 guard is not pure engineering — what it should do (refuse to boot? boot read-only? keyed on which
condition?) is a design decision about application behaviour, and the auditor reached the same conclusion
independently from a different direction; (c) the mechanical consequence is ASYMMETRIC IN THE SAFE
DIRECTION here, unlike a normal stall: a stopped engine starts no backend, so halting is strictly safer for
B1 than continuing, whereas CONTINUE puts the decomposer one step from the unauthorized rebuild; (d) B1
cannot change the gate's answer either — it protects the gate's preconditions, it does not clear them.
What I explicitly did NOT do: bury B1, call it out of scope, or leave it at the auditor's priority — I
raised it above the AVB decision in the recommendation precisely because it is the only item that can go
wrong without anyone deciding anything.

**Reversible:** yes — one owner line (or an instruction plus `--resume`) restarts the session with nothing
repaired, nothing lost and no status changed; if the owner prefers the guard built first, that is option
one of the recommendation and needs no rework here.

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
