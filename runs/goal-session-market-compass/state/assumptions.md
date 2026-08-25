# Goal Session market-compass — Assumption Ledger

Append-only. Each entry records a scoring decision that required interpreting an
ambiguous goal, so the owner can veto it early.

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

## iter-13 — goal-decomposer (Stage C's forward-return clear scope: run-owned rows only, not measured-date "holes on retained runs")

**Ambiguity:** J-11 step 2's classification names "the associated derived forward-return state" among Stage C's rebuildable-and-cleared allowlist "as the real dependency graph requires," while step 5 and ruling C7 route "repair[ing] the full forward-return damage... including holes on retained runs" and "the final global/create-once forward-return repair" to a later stage (E), explicitly forbidding it in Stage C "unless this contract explicitly assigns that action to Stage C." `docs/goal.md` does not spell out, in one place, whether Stage C's own DELETE touches ONLY `ForwardReturn` rows whose owning `ScannerRun` is itself one of the 11 incident-date runs being deleted, or also rows whose `measured_date` merely lands on an incident date while their originating run is retained.

**We chose:** Scoped `clear_snapshot_dates` to delete only rows keyed by `run_id` belonging to an incident-date `ScannerRun` (mirroring `clear_snapshot_set`'s own child-before-parent, run-scoped deletion), and explicitly excluded any deletion keyed by `measured_date` membership alone. Reasoning: the original iter-5 cascade's defensive sweep already removed the `measured_date`-only population (`data_manager.py:2185-2192`), so those rows are ALREADY absent today — Stage C has nothing left to delete there, and the pre-reset inventory's `forward_returns_measured_into_count` per-date field (already captured in iteration 10's artifact) is exactly the count Stage E's repair, not Stage C's clear, must fill. Deleting anything beyond the run-owned population would exceed C4's "Layer 2 ONLY" boundary and C7's explicit prohibition on performing the global repair here.

**Reversible:** yes — this is a scoping choice for the DELETE statement's WHERE clause, not a structural decision; if the developer's own re-derivation of the dependency graph disagrees, the spec's own TC-4/TC-5 require fixture proof either way before the live run executes, and no live delete happens until that proof exists.

## iter-13 — goal-decomposer (a NEW "Stage C attempt identity" per ruling C2, layered on Stage B2's engine/config identity rather than replacing it)

**Ambiguity:** Ruling C2 says "Freeze a NEW Stage C attempt identity," distinct wording from step 12's Stage B2 "freeze ONE engine identity for the whole attempt" (already delivered in iteration 10 and re-verified since). `docs/goal.md` does not define what a "Stage C attempt identity" contains beyond the preflight capture list C2 itself enumerates (git HEAD, goal.md contract hash, engine identity, config identity, dates, fingerprints, etc.), nor whether it supersedes or sits alongside the existing B2 `engine_identity`.

**We chose:** Treated "Stage C attempt identity" as a NEW, distinct bookkeeping identifier (e.g., an attempt id/timestamp) that WRAPS and re-asserts the SAME B2 `engine_identity` value (re-derived fresh via `freeze_attempt_identity`, expected to be byte-identical to the certified iteration-10/12 value since no code/config change has landed since), rather than a second, competing engine identity. This satisfies C2's "re-derive live state rather than trusting iteration-10/11/12 certified counts" instruction while preserving step 12's single-identity invariant that Stage D will later check per rebuilt run.

**Reversible:** yes — it is purely an evidence-artifact naming/structuring choice for `j11-stage-c-preflight.json`; if the developer's re-derivation of `engine_identity` differs from the certified value, ruling C2's own "STOP before deletion" clause fires regardless of how the attempt-identity artifact is shaped.

## iter-13 — auditor CORRECTION (2026-08-24): both iter-13 entries above rest on a factual premise that the live database contradicts

**The two entries above are preserved verbatim — this is an additive correction, never a rewrite.** The
DECISIONS both entries reached are correct and were implemented correctly; the FACTUAL PREMISES quoted in
their "We chose" paragraphs are not. Recorded here because the Stage D/E decomposer reads this file.

**Correction to entry #2 (Stage C attempt identity).** The premise "expected to be byte-identical to the
certified iteration-10/12 value since no code/config change has landed since" is FALSE. Re-derived at
audit: `runs/goal-market-compass-iter-10/j11-frozen-identity.json` froze
`engine_identity=6261ca1791b59771f3b6b6829142e2cf7c0f33d0fa4ea00a2f1e2c8d1d6b3a6e`;
`runs/goal-market-compass-iter-13/j11-stage-c-preflight.json` re-derived
`53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55`, and
`engine_identity.compute_engine_identity(get_config())` recomputed independently at audit returns the
same `53d2ffd1…`. Cause: `apps/backend/app/engine/compass.py` is one of `config.yaml`'s three
`provenance.engine_files` and changed in commits `a7380009` (iter-11) and `a9e651c4` (iter-12).
`config_subset_hash` is unchanged at `10bc4504ed9f28961a6342c3306d8a8eaeceac5ec7d233645540dffb0a653614`,
so the drift is code-side only. **Stage C is unaffected** (deletion-only; no delete predicate reads an
engine identity) and this is not a step-12 violation, since step 12's invariant is scoped to ONE attempt
and iteration 13 freezes a new Stage C attempt. **Stage D precondition:** two frozen-identity artifacts
now exist with different values, and the live database holds 34 surviving non-incident `scanner_runs`
stamped `6261ca17…` plus 3,083 stamped NULL. Stage D must state explicitly which frozen identity its
step-12 per-run check compares against, and must not "repair" the surviving runs' stamps.

**Correction to entry #1 (forward-return delete scope).** The premise that the `measured_date`-only
population "is ALREADY absent today" is FALSE. Live read-only count after Stage C: 16,614 `forward_returns`
rows whose `measured_date` lands on an incident date, all owned by RETAINED runs — 2026-05-12: 2,770 ·
05-13: 2,216 · 07-10: 2,769 · 07-13: 2,217 · 07-24: 1,660 · 07-27: 1,660 · 08-03: 1,662 · 08-05: 1,660
(08-10/08-11/08-12: 0). The scoping decision itself — delete only `run_id`-owned rows — is exactly what
rulings C6/C7 require and is what `clear_snapshot_dates` does, so the wrong premise produced the right
action: of the 11 dates' pre-delete `forward_returns_measured_into_count`, only the four whose rows were
owned by a deleted run moved (05-13 2,771→2,216 = −555 · 08-10 124→0 · 08-11 20→0 · 08-12 20→0, i.e. 719
rows), and those 719 are a SUBSET of the 2,811 `run_id`-owned rows Stage C removed — not an additional
`measured_date`-keyed deletion. The other seven dates' counts are byte-identical pre and post.
**Stage E must not inherit the premise:** the surviving 16,614 rows are
retained-run history that C6 forbids deleting, and are distinct from the "holes on retained runs" that
Stage E repairs.

**Reversible:** yes — this entry adds no decision. It corrects two factual statements and names one Stage D
precondition; nothing in the delivered iteration-13 code or evidence changes as a result.

## iter-13 — goal-evaluator (STALLED rather than CONTINUE when tractable NON-Stage-D work demonstrably exists)

**Ambiguity:** Iteration 12's STALLED rested on "the blocker is human-owned AND there is no substitute
work". Half of that is now false: the auditor's B2/T2/T3 gaps (the preflight gate captures engine/config
identity but never compares it; nine of eleven gate invariants have no negative test and the positive
test is a self-diff; the `--confirm` refusal and four non-zero-exit paths are untested) are ordinary,
non-destructive engineering work that is NOT Stage D and is arguably inside the J-11 window that
`docs/goal.md`'s Loop-mechanics gate leaves open ("Only work needed to execute and verify J-10/J-11 —
plus explicit prerequisites such as the depth/safety control — may run in that window"). On the
methodology's tree that reads like CONTINUE with a hardening target; on C.2 it reads like STALLED.
**We chose:** STALLED, with the Halt Justification's first sentence saying nothing is wrong or missing,
and with the hardening run offered to the owner as explicit option (b). Reasoning: (a) ruling C10 is not
merely a gate on Stage D, it is a direct instruction about the ENGINE — "After the bounded clear
completes and is independently verified, **STOP THE ENGINE**" — followed by "The owner inspects Stage C
mutation accounting first"; a CONTINUE verdict would let the engine decompose iteration 14 without that
inspection, which is the thing the ruling forbids, whatever iteration 14 then contained; (b) the
mechanical consequence is asymmetric — STALLED preserves the owner's inspection point at zero cost, and
the hardening work loses nothing by waiting one owner message, whereas CONTINUE cannot be un-run; (c) the
dispatching coordinator independently records the same reading of C10; (d) the session's own precedent is
consistent (iters 10 and 12 both returned STALLED on human-owned J-11 gates). What I explicitly did NOT
do: claim the hardening work is illegal or impossible, or hide it from the recommendation — it is named
first among the three Stage D preconditions and offered as its own option.
**Reversible:** yes — the owner answers with one dated line in `docs/goal.md` (or an instruction plus
`--resume`) and the session continues with nothing repaired, nothing lost and no status changed; the
owner-facing lines `J-11 STAGE C COMPLETE: YES` and `J-11 STAGE D AUTHORIZED: NO` are recorded either way.

## iter-13 — goal-evaluator (keeping J-11 `partial` after a fully successful, fully verified Stage C)

**Ambiguity:** `docs/goal.md` gives J-11 seven stages (B/B1/B2 → C → D → E → F → G) and states "Only
after G passes is the incident repaired." The journey-history schema has no vocabulary for "one stage of
seven delivered cleanly"; `partial` is defined as "only some assertion steps passed", which reads like a
weaker outcome than what happened here — Stage C met every one of its own acceptance items, on the live
database, verified independently by four lanes and again by me.
**We chose:** `partial`, unchanged in label but with the gap text rewritten to state plainly that Stage C
is COMPLETE and verified while D-G are not started and not authorized, and with the owner-facing lines
carried in the gap itself. Reasoning: the status field drives the achievement gate, and J-11 genuinely
cannot be `passing` until Stage G's verification exists; recording anything stronger would let a later
reader (or the deterministic gate) treat a one-seventh-complete repair as a finished journey — exactly
the "summary statistic erases the counter-example" failure iteration 9 logged. The progress is recorded
where a human and the next decomposer will actually read it (the gap text, `iteration-state.md`, and the
evaluator log), not by inflating a machine-parsed status.
**Reversible:** yes — the label is one string; if the owner or a later evaluator prefers a per-stage
representation, nothing here is deleted and the full stage-by-stage evidence is preserved verbatim.

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
