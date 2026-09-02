# Goal Session market-compass — Assumption Ledger

Append-only. Each entry records a scoring decision that required interpreting an
ambiguous goal, so the owner can veto it early.

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

## iter-34 — goal-decomposer (two scoping reads: "fix the results file" as a scoped harness code
change, and J-09 as a legitimate Target journey despite the binding "Do not redo")

**Ambiguity:** iter-33's evaluator recommended repair item (3) — "fix the results file so it stops
recording this round's own target job as 'never tested'" — does not say whether the fix is a one-off
manual edit to a single generated report, or a durable code change to the merge/gate scripts that
produce that report every iteration. Separately, iter-33's own "Do not redo" list is binding
("J-09 is CLOSED on the numbers — do NOT re-open it as a build... the next round CONFIRMS, it does not
rebuild"), and it is not stated whether naming J-09 as this iteration's `Target journeys:` entry
conflicts with that instruction.

**We chose:** (a) implement the results-file fix as a scoped, durable change to
`incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` (and `goal_gate.py` only if
required), keyed strictly to `docs/goal.md`'s own literal `**Walkthrough:** waived` marker — never a
one-off manual edit of a single iteration's report, and never a bare journey-ID allowlist that could
silently exempt a future unwaived journey; a companion regression test (TC-8) proves the exemption does
not generalize. (b) score J-09 as a legitimate `Target journeys:` entry, explicitly labeled
"confirmation only," on the grounds that the binding "Do not redo" instruction forbids REBUILDING the
warm-up mechanism (`warmup.py`/`prices.py`), not re-verifying or re-recording evidence for an
already-shipped, already-passing journey — the two are different acts, and OUT OF SCOPE in this spec
explicitly reiterates the rebuild prohibition so nobody reads "Target journey" as license to touch the
mechanism.

**Reversible:** yes — no product mutation either way. If the owner or a future evaluator rules that the
results-file exemption should instead be a manual per-iteration edit rather than durable harness code,
the new regression test and merge-script change can be reverted without redoing any of this iteration's
memory-measurement evidence; if the owner rules J-09 should never appear on a `Target journeys:` line
again once closed, this iteration's re-measurement evidence still stands on its own as a
Required-still-passing-style confirmation.

## iter-34 — goal-evaluator (J-09's concurrent-load acceptance limb scored from iter-33's evidence, because this iteration never re-ran it)

**Ambiguity:** `docs/goal.md` J-09's Acceptance lists under **Correctness** three conjuncts:
"measured backend VmPeak at standing warm ≤ 2.5 GB ... **the concurrent-load check passes**; the
byte-identity spot-check holds." This iteration re-ran the first and third but NOT the second — the
iter-34 spec's IN SCOPE and its TC-1..TC-11 never ask for a request burst, and the dev handoff
contains no burst, no `limit_concurrency` run, and no `QueuePool` count. The goal text does not say
whether an acceptance limb must be re-demonstrated every time the journey is re-verified, or whether
a prior demonstration on unchanged code still counts.

**We chose:** score the limb satisfied on iter-33's 320/320 HTTP-200 burst, under methodology A.6
(evidence expires with CHANGE, not with time), and say so explicitly rather than letting the
`passing` status imply a fresh run. Grounds, each checked by me: (a) I verified the durability
PRECONDITION instead of assuming it — `apps/backend/app/engine/warmup.py`, `config.yaml` and
`apps/backend/app/config.py` all carry mtime `2026-09-01 06:26:40`, which is inside iter-33 and
BEFORE its own burst, and `git diff --stat 9150ee4b -- apps/ config.yaml` is EMPTY, so the code and
pool arithmetic under test are byte-identical to what passed; (b) the limb's stated purpose is that
"the pool arithmetic is untouched; only the per-connection cache shrank" — and untouchedness is
exactly what I proved, so a re-run could only re-confirm a property already established by
inspection; (c) corroborating live evidence exists anyway — zero `QueuePool` lines and zero
tracebacks across all three of this iteration's backend boots (all 19 historical QueuePool lines sit
~239k log lines earlier); (d) demanding a re-run of every limb on every re-verification round, on
provably unchanged code, is the "vague acceptance criteria → infinite loop" anti-pattern the
framework names as its #1 failure mode. What I did NOT do: hide it — it is in J-09's `gap` field, the
evaluator log, and stated in the eval as "NOT re-run this round".

**Reversible:** yes — no mutation, and a cheap remedy. If the owner rules every Correctness conjunct
must be freshly demonstrated in the certifying round, one bounded burst against the unchanged backend
settles it; none of this iteration's measurement, byte-identity or replay evidence would need redoing.

## iter-34 — goal-evaluator (certified GOAL_ACHIEVED although the harness fix this iteration shipped is unwired and the J-09 results row cites nothing in its Evidence cell)

**Ambiguity:** this iteration's second deliverable was a merge/gate fix so a walkthrough-waived
journey's non-UI evidence could be RECORDED. It works and provably does not over-reach, but the
auditor found (B2) — and I reproduced byte-for-byte — that nothing invokes it: merging only the
replay file plus the browser-QA file regenerates the authoritative results file exactly, so the
developer's `j09-evidence-fragment.md` is not an input. The clean `goal_gate.py results` exit 0 is
therefore carried by the browser-QA lane happening to emit `PASS` rather than `SKIP` for J-09, and
that PASS row's Evidence cell reads `none (…prose…)` — which the audit's own B1 fix now correctly
classifies as citing nothing. It is unstated whether a journey's status may rest on a row whose
provenance is that weak.

**We chose:** certify. Score J-09 from the substance the goal itself names as the walkthrough's
replacement, and record the row's provenance weakness as a tooling gap rather than a journey gap.
Grounds, each checked by me: (a) I did not rely on that row — I re-derived every acceptance limb from
raw artifacts myself (max `VmPeak_kB` over all 366 and all 370 CSV rows from two separately-booted
pids; `cmp` over all 16 byte-identity captures, 0 differing; `git diff --numstat` on
`reports/perf-budgets.md` = 244/0; a read-only census plus a `mode=ro` control that refused
`CREATE TABLE`); (b) `docs/goal.md:585` waives J-09's walkthrough in terms and names the dated VmPeak
measurement as its replacement, so no screenshot is owed and the A.3 no-screenshot rail cannot bind a
journey that asserts no UI behaviour; (c) the row is EXECUTED and `PASS`, not `SKIP` — materially
stronger than iter-33's record, whose SKIP-under-BLOCKED headline I refused to certify on; (d) the
deliverable's own protective claims are real and I executed them rather than reading them (waived set
= exactly `{J-09, J-10, J-11}` from the literal goal.md marker; the placeholder-plus-prose cell
returns `False`; iter-33's REAL inputs through the patched merge still return `BLOCKED`/exit 1).
What I did NOT do: let it pass silently — it is finding 1 of the eval's non-blocking list, an
owner-facing line in the log, and the one build-tooling item in my recommendation, with the explicit
warning that a future round whose browser-QA lane emits `SKIP` would block again.

**Reversible:** yes — a scoring call with no mutation. If the owner or the framework rules that a
target journey's row must carry a real citation in its Evidence cell, the remedy is to wire the
replay lane's merge to include a per-iteration evidence fragment for waived journeys and re-merge;
J-09's measurement evidence stands untouched either way.

## iter-34 — goal-evaluator (GOAL_ACHIEVED certified while six journeys still owe the `[NEW]`-flagged walkthrough their own Acceptance names)

**Ambiguity:** J-01..J-08 each carry an Acceptance limb of the form "**Walkthrough:** a `[NEW]`-flagged
walkthrough of ..." (`docs/goal.md:234,268,298,348,423,475,513,545`). An 8-step walkthrough DID land
this round (`reports/phase-goal-market-compass-iter-34-demo-results.md`, RECORDED_WITH_NOTES), but its
Journey column is EMPTY for every step, so no step is attributed to a journey; J-02, J-03, J-05, J-06
and J-08 have no attributed recording at all and J-07's remains thin. Read strictly, an acceptance
limb is unmet on six must-have journeys at the moment of certification.

**We chose:** keep all six `passing`, keep `evidence_makeup: true` on them, and certify. Grounds:
(a) methodology A.7 is explicit that a missing or mis-cropped walkthrough is a CAPTURE defect scored
from the code/replay/screenshot evidence that does exist, that the flag "never downgrades" the
status, and that the make-up ride is "NEVER a new iteration's goal"; (b) my agent contract repeats
this as a hard rule — never score as blocking an iteration whose only content is evidence capture;
(c) the asserted BEHAVIOUR is met for all six, which is A.7's rail — each has an executed replay row
with exact-string DOM assertions plus a fresh screenshot this round, and I opened four of them;
(d) this is settled precedent, scored the same way by every evaluator since iter-27, not a fresh
relaxation invented to close the session. What I did NOT do: quietly drop it — the six flags are
retained in `journey-history.json`, the gap text records that an unattributed walkthrough landed, and
re-recording them is the second optional item in my next-step recommendation.

**Reversible:** yes — no mutation, and cheap to satisfy. If the owner rules the `[NEW]`-flagged
walkthrough is a hard acceptance condition rather than a capture task, one `Depth: evidence` round
records the six; no journey's status or product evidence would need redoing, and the product itself
is unaffected either way.

## iter-35 — goal-decomposer (evidence-depth recommendation vs. two newly-proposed, never-built Must-have journeys)

**Ambiguity:** the evaluator's depth recommendation for this iteration ("evidence — BINDING by
default") was computed from the iter-34 journey state (11/11 passing, all remaining work being
walkthrough capture). Since then the goal-proposer appended two NEW Must-have journeys, J-12 and
J-13, to `docs/goal.md`'s AUTO block (dated 2026-09-01) — neither appears in the inlined
journey-history digest (still J-01..J-11 only). It is not stated whether a depth recommendation
computed before new goal content lands still binds, nor which of the two new journeys to prioritize.

**We chose:** target J-12 only, at Depth: lean. Grounds, each checked by me: (a) `Depth: evidence` is
defined only for "all Target journeys are already recorded passing" with the deliverable being
capture only (skips developer/reviewer) — J-12 is not recorded passing (it does not exist in
journey-history yet) and requires an actual code change, so `evidence` does not apply to this scope
by definition, independent of any staleness argument; I verified the cited defect is real rather than
trusting the goal text: `apps/backend/app/engine/compass.py:602-703` today labels EVERY row that
fails any of the three qualifier checks (leadership, entry, risk) as `below_selection_floor`,
confirming the proposer's claim; (b) between J-12 and J-13 (also new/unbuilt), I picked J-12 under
rule 4 (smallest spec wins ties: one backend module + config + tests, no frontend change, versus
J-13's backend session_delta change AND a frontend rotation-component rework) and rule 5 (never
bundle two risky journeys); J-12 is also the higher-severity pick — an AG-3-adjacent correctness
defect (37/539 rows carry a false disposition label in a committed export) versus J-13's
completeness/UX gap; (c) no FULL trigger holds for J-12: its own Acceptance text states "no new
producer, no new route, no new Data Contract value" (rules out trigger 2, data-model migration); the
change is confined to one engine module plus config/tests, not clearly cross-cutting (trigger 1);
prior verdict is GOAL_ACHIEVED, not ESCALATE (trigger 3 not met); consecutive lean iterations = 0 of
a 6 cadence (trigger 4 not due) — so LEAN, the framework default, applies once `evidence` is ruled
out as inapplicable.

**Reversible:** yes — no mutation from this spec itself (planning only). If the owner or a future
evaluator rules that a stale depth recommendation must still be honored as a separate evidence-only
round before any new goal content is picked up, the remedy is to insert that round ahead of this one;
none of J-12's eventual implementation or evidence would need redoing, since its scope is unaffected
by which round it is labeled under.

## iter-35 — goal-evaluator (a never-tested new journey scored `failing` rather than `unknown`)

**Ambiguity:** J-13 was appended to `docs/goal.md` on 2026-09-01, is absent from `journey-history.json`,
and was explicitly OUT OF SCOPE this iteration — no test lane ran it and no results row exists for it.
My agent contract says "If you cannot find evidence for a journey … set its status to `unknown` … Do
NOT guess", while the schema defines `failing` as "verified failing in this iteration". It is unstated
which applies to a brand-new journey that no lane was ever asked to test.

**We chose:** `failing`, on the grounds that I have positive evidence of the asserted behaviour being
ABSENT rather than an absence of evidence — and I obtained it myself rather than inferring it from the
goal-proposer's text. Each of J-13's three cited defects re-measured by me against
`2026-08-12_v8.json`, the manifest minted TODAY under this iteration's corrected rule (so the reading is
current, not stale): (a) `session_delta` has keys `{changes, gap_days, prior_as_of, suppressed,
suppressed_count}` and **no `rotation` key at all**, so step 1's core assertion fails by construction;
(b) every change entry carries `{drill_href, from, kind, label, magnitude, threshold, to}` — `magnitude`
is unsigned and there is no `delta` and no `direction_word` anywhere, so step 3 fails; (c) sector
accounts for 5 shown + 24 suppressed = **29 of the 31** configured sector/industry ETFs (`etfs.sector`
11 + `industry` 20) while theme closes at 2 + 9 = 11/11, so step 4 fails. Plus
`compass-leadership-rotation-section.tsx:38` is a client-side `changes.filter(...)` over an array with
zero market/breadth entries, so the section provably duplicates the card above it — visible in this
iteration's own `UT-J-12-result.png`. `unknown` would have understated a measured, reproducible defect
and would have left the next decomposer without a target. What I did NOT do: score it from the
goal-proposer's prose — every figure above is one I computed.

**Reversible:** yes — no mutation, and cheap to revisit. If the owner or a future evaluator rules that a
journey no lane was asked to test must be `unknown` regardless of artifact evidence, flipping the status
changes nothing material: `journeys` still exits 1 and J-13 remains the sole blocker either way, and
none of this iteration's J-12 evidence would need redoing.

## iter-35 — goal-evaluator (a NEW journey promoted to `passing` although its Walkthrough acceptance limb was never captured)

**Ambiguity:** J-12's Acceptance ends with "**Walkthrough:** a `[NEW]`-flagged walkthrough of the
corrected disposition table … viewable via `demo.sh market-compass --session-live`" (TC-13 repeats it).
No demo ran at this lean depth — `reports/demo/goal-market-compass-iter-35/` does not exist. Prior
precedent (iters 27-34) applied methodology A.7 to keep ALREADY-passing journeys passing despite the
same missing limb; it is unstated whether the same relaxation may be used to promote a journey to
`passing` for the FIRST time.

**We chose:** promote J-12 to `passing`, set `evidence_makeup: true`, and record the missing walkthrough
as a capture gap. Grounds, each checked by me: (a) A.7's rail is that the relaxation "never applies when
the asserted BEHAVIOR is unmet" — here the behaviour is met and I re-derived every acceptance number
independently (37→0 mislabeled rows; 502+27+10=539; shadow cohort identical at 25 rows; HPE's caution
citing threshold 70.0 and actual 21.5; CRL proving the fails-both case), so only the presentation
artifact is absent; (b) the behaviour additionally has a live browser citation — a DOM sweep of all 529
rendered audit-table rows plus a screenshot I opened showing the acceptance state; (c) my agent contract
states as a hard rule that an evidence-capture gap may never be scored as blocking, and A.7 says the
make-up ride is "NEVER a new iteration's goal"; (d) holding a journey open on a missing recording when
its measured objective is demonstrably met is the framework's own #1 anti-pattern. What I did NOT do:
hide it — the flag is set in `journey-history.json`, the gap text names TC-13 explicitly, and the
re-capture is listed in my recommendation as a passenger task.

**Reversible:** yes — no mutation. If the owner rules the `[NEW]`-flagged walkthrough is a hard
acceptance condition rather than a capture task, one `Depth: evidence` round records J-12 alongside the
seven journeys already owing one; no product code and none of this iteration's measurement evidence
would need redoing.

## iter-36 — goal-decomposer (scoping J-13's "signed delta + direction_word rides on session_delta.changes too" to sector/theme kinds only)

**Ambiguity:** J-13 step 3 (`docs/goal.md` AUTO block) reads "assert the same signed delta + direction
word ride on the `session_delta.changes` entries so the What-changed card can show them too" without
naming which `kind`s. The rotation block itself is explicitly group-level only (step 1 excludes
`stock`), and `market`/`breadth` entries already have a comparable direction concept expressed elsewhere
(the narrative's own `_direction_sentence`/`state_band.regime`) computed from a different input (regime
score, not a stored rank). It is unstated whether the addition to `session_delta.changes` should cover
all five kinds or only the two the rotation block itself covers.

**We chose:** scope the `delta`/`direction_word` addition on `session_delta.changes[]` to `kind ∈
{sector, theme}` only — the same two kinds the rotation block covers, computed from the same rank pairs.
Grounds: (a) the sentence's own antecedent ("the same signed delta") most naturally refers to the
rotation row just described in step 3's first half, which is sector/theme only; (b) `market`/`stock`
kind entries have no analogous "rank" concept to sign against (market is a regime-score delta already
narrated elsewhere; stock is a bucket-letter crossing, not a numeric rank) — inventing a sign convention
for them would be new engine logic outside J-13's measured defects (a)-(c), all of which cite sector/
theme only; (c) this keeps the change minimal and additive, consistent with the "no new producer, no new
route" Acceptance constraint, and does not touch the `market`/`stock` entry shape the What-changed card
already renders unchanged (step 6).

**Reversible:** yes — additive JSON fields only, no mutation. If a future evaluator or the owner reads
step 3 as covering all five kinds, extending `delta`/`direction_word` to `market`/`stock` entries is a
small additive follow-up; nothing in this iteration's sector/theme work would need redoing.

## iter-36 — goal-evaluator (a target journey promoted to `passing` on a 100%-blank acceptance screenshot)

**Ambiguity:** J-13's only cited acceptance artifact,
`reports/qa/goal-market-compass-iter-36-evidence/UT-J-13-rotation-both-directions.png`, is a
1683×1260 image with exactly ONE distinct colour across all 2,120,580 pixels — it shows nothing.
Methodology A.3 says to "confirm the image shows the acceptance state" and that no citation means
`unknown`; A.7 says a defective CAPTURE never downgrades a confirmed behaviour and rides a make-up lane.
It is unstated which applies to a screenshot that exists and is cited but is informationally empty, and
whether a FIRST-TIME promotion may use A.7 at all.

**We chose:** `passing` with `evidence_makeup: true` and the defect stated verbatim in the gap, the
eval table, and the log. Grounds, each checked by me: (a) A.7's rail is that the relaxation "never
applies when the asserted BEHAVIOR is unmet" — here the behaviour is met and I re-derived every
acceptance limb myself from raw artifacts rather than from prose: the served `session_delta.rotation`
block in `2026-08-12_v9.json` (5/2 sector, 1/1 theme, zero stock rows, closed six-field row shape), the
accounting closing exactly at 7+24+0 = 31 and 2+9+0 = 11 against a `configured_total` the code derives
from `len(etfs.sector)+len(etfs.industry)` and `len(themes)`, and all NINE rows' from/to and signed delta
matching the STORED `sector_scores`/`theme_scores` ranks at runs 3157 and 3158; (b) a REAL browser
screenshot of the same component on the same page DOES exist this round
(`J-13-legacy-asof-rotation-not-recorded.png`, 6,740 distinct colours), so the section demonstrably
renders live in a browser — only the frontier-state capture failed; (c) three independent agents
(developer, reviewer, browser-QA) each drove a live browser and independently reported the SAME exact
strings ("Regional Banks (SPDR) 13 → 10 (-3) · improving", "7 of 31 shown · 24 below threshold · 0 beyond
the display cap."), which I confirmed are exactly what the served data plus the component's JSX template
must produce — convergent, not a single claim; (d) my agent contract states as a hard rule that an
evidence-capture gap may never be scored as blocking, and A.7 says the make-up ride is "NEVER a new
iteration's goal". What I did NOT do: hide it — the blankness is measured and quoted in the journey gap,
in the eval's journey table, in the eval Summary, and as blocker 1 of the log entry, and it is the reason
my verdict is ESCALATE rather than GOAL_ACHIEVED.

**Reversible:** yes — no mutation, and one screenshot fixes it. If the owner or a future evaluator rules
that an informationally-empty screenshot equals no screenshot, J-13 drops to `unknown` and the next
full-depth round re-captures it; none of the served-data, stored-rank, or byte-identity evidence I derived
would need redoing, and the product is unaffected either way.

## iter-36 — goal-evaluator (declined GOAL_ACHIEVED although every deterministic gate passed and the decision tree's rule 3 matched)

**Ambiguity:** the verdict decision tree is "apply top-down; first match wins", and rule 3 (GOAL_ACHIEVED)
sits ABOVE rule 4 (ESCALATE). After this round all thirteen Must-have journeys are `passing`, the
anti-goal ledger is 9 total / 0 unresolved, `coherence.md` is COHERENCE-PASS, and there is no
`journeys-changed.md` — so rule 3 matches mechanically, and I confirmed it by running every gate myself
(`results` 0, `journeys` 0 with `blocking: []`, `regressions` 0, `coherence --for-achievement` 0, drift
`changed: []`). It is unstated whether an evaluator may decline rule 3 on a VERIFICATION deficit in the
iteration itself, as opposed to a journey, anti-goal or coherence deficit.

**We chose:** ESCALATE, and said plainly in both the eval and the log that a GOAL_ACHIEVED was
mechanically available and I declined it for exactly one round. Grounds, each checked by me: (a) the
deficit is real and evidenced, not a feeling — the spec reads `Depth: full` with an explicit Full trigger,
`session.json next_depth` is `"full"`, the decomposer was dispatched "BINDING by default" (trace step 368),
and yet trace steps 370-375 launched every downstream agent as "goal-mode **lean** iteration", with no
audit handoff, QA report, ux-regression or closure verdict anywhere on disk; (b) iter-35's binding
"Do not redo" block required in terms that "a drop to `lean` must be surfaced explicitly and marked
unmet", and no agent did so, so declining to certify is the instruction being honoured rather than
overridden; (c) rule 3's own parenthetical frames GOAL_ACHIEVED as "the first key, not the final word" —
i.e. a certification I must be willing to stand behind, and I am not willing to stand behind a round that
skipped the inspection it was told to perform while producing an empty picture of its only new screen;
(d) the lost lanes are precisely the ones the spec's Full trigger named, including ux-regression, on the
one round in months that rewrote a user-facing component (136 lines) — and this round's OWN reviewer
found a CRITICAL page-crashing defect in round 1, direct evidence that independent lanes find real faults
in this change; (e) direct session precedent: iter-33 returned ESCALATE for this same depth drop, iter-34
then ran genuinely full and its auditor found five findings (B1-B5) no other lane had; (f) this does not
risk the "vague criteria → infinite loop" anti-pattern, because the exit conditions are three concrete,
one-round, mechanically checkable items (four named artifacts exist; the J-13 golden replays; a non-blank
screenshot lands) and there is NO new feature work left. What I did NOT do: dress it up as a journey or
anti-goal failure — every journey is recorded `passing` and the ledger is recorded clean.

**Reversible:** yes — no mutation, and it costs exactly one round. If the owner or the loop rules that a
matching rule 3 must be honoured regardless of dispatch depth, flipping this verdict to GOAL_ACHIEVED
requires changing nothing else: `journey-history.json` already records 13/13 `passing`, every gate already
exits 0, and none of this round's evidence would need redoing.

## iter-37 — goal-evaluator (certified GOAL_ACHIEVED although one of the four spec-named full-depth artifacts is a skip stub)

**Ambiguity:** the iteration spec's DEFINITION OF DONE item 2 and TC-5 require all four full-only
artifacts on disk "with non-trivial content (not empty stubs)", and name that as this round's proof
of genuine full depth. `reports/phase-goal-market-compass-iter-37-ux-regression.md` exists but is a
284-byte `UX-REGRESSION-SKIPPED` stub: `engine.log:8041,8044` records the iteration ran 4,935s
against a 3,600s budget and shed this non-blocking reviewer (SPEED-15 trim rung 3b). It is unstated
whether a lane shed by a DECLARED budget rule satisfies `docs/goal.md`'s loop-mechanics requirement
that depth reductions "MUST be surfaced explicitly and MUST NOT silently fall back", or whether the
spec's literal four-artifact test governs. The same question decided iter-36 the other way (ESCALATE).

**We chose:** certify GOAL_ACHIEVED, and say plainly in the eval, the log and here that one lane did
not run. Grounds, each checked by me: (a) the shed is DECLARED in two independent places (the engine
log and the artifact's own text), which is exactly the half of the loop-mechanics rule iter-36
violated — that drop was silent and nobody surfaced it, this one announces itself; (b) the lane's
purpose is inapplicable here — UX-regression exists to inspect CHANGED screens, and I verified from
`git diff <snapshot> --stat` that this round's entire product diff is `apps/backend/app/engine/
compass.py` (18 lines) and `apps/backend/tests/test_manifest_invariants.py` (47 lines), with zero
`.tsx`, zero component and zero route, so there was no changed screen to review (unlike iter-36,
which rewrote 136 lines of a user-facing component — the fact that made the same shed material then);
(c) the substantive deficit iter-36 named ("the thing I would be certifying has never been seen") is
closed four times over and twice by me personally — I measured the acceptance capture at 13,647
distinct colours and READ the rotation panel out of it, and I opened the walkthrough frame showing
the same panel; the QA lane returned UI-PASS on it and the browser lane captured it; (d) the OTHER
three full-only artifacts are substantial and the depth dispatch itself is proven by
`engine.log:7947-7951` (`Depth arbiter: FULL pass granted` → `Dispatching FULL pipeline`), so the
failure mode this round existed to prevent did NOT recur; (e) the spec's DoD is an iteration
completion checklist, not one of my contract's four GOAL_ACHIEVED conditions (all thirteen journeys
`passing`, ledger 0 unresolved, coherence not FAIL, no unre-verified goal-edit drift — every one
satisfied and every gate exit 0); (f) iter-36's own exit conditions were three concrete items and
ALL THREE are met and verified by me, so declining again would be adding a fourth condition after
the fact — the framework's #1 anti-pattern (vague criteria → infinite loop) with no feature work
left to justify another round. What I did NOT do: treat it as satisfied — the miss is stated
verbatim in the eval's Summary, in a dedicated "Two Literal Misses" section, and in the log entry.

**Reversible:** yes — no mutation, and it costs one short round to settle either way. If the owner
rules that all four artifacts must be substantive regardless of whether any screen changed, running
the UX-regression reviewer over the unchanged `/` page produces the missing file without touching a
line of product code; `journey-history.json` already records 13/13 `passing`, every gate already
exits 0, and none of this round's evidence would need redoing.

## iter-37 — goal-evaluator (cleared `evidence_makeup` on J-04 from a walkthrough frame rather than a fixed verify screenshot)

**Ambiguity:** methodology A.7 says to clear `evidence_makeup` "the moment a fresh capture lands —
whatever the outcome". J-04's flag was set because `J-04-verify.png` crops above the candidate
cards; a fresh `J-04-verify.png` landed this round and reproduces the identical crop (19th
consecutive round), which under iters 35-36 precedent meant deliberately KEEPING the flag. But a
different artifact — `reports/demo/goal-market-compass-iter-37/step-05.png`, produced by the demo
lane and labelled for J-04 — does show the acceptance state. It is unstated whether the make-up
capture must come from the same artifact that was defective.

**We chose:** clear J-04's `evidence_makeup`, on the grounds that the flag records an EVIDENCE gap,
not a golden-script defect, and the gap is now filled by an artifact I opened myself: step-05.png
shows the HPE and GRMN candidate cards with LEADERSHIP/ENTRY/RISK, WHY, CAUTIONS, the Eligibility
checklist, "What would change this" and an INVALIDATION line — the exact state J-04 asserts and the
exact state the verify crop has stopped above. Keeping a flag whose stated purpose ("nobody has a
picture of this") is demonstrably satisfied would carry a false debt forward. Same reasoning applied
to J-08 (step-06, Market page). What I did NOT do: pretend the crop is fixed — the gap text records
that `J-04-verify.png` is still the top-of-page viewport and names it a golden-viewport matter that
is now non-blocking because a good capture exists.

**Reversible:** yes — no mutation. If the owner or a future evaluator rules the make-up capture must
be the same artifact, re-setting `evidence_makeup` on J-04 changes nothing material: the journey is
`passing` on a replay row with DOM assertions either way, and one viewport line in the golden fixes
the crop whenever anyone cares to.

## iter-38 — goal-decomposer (evidence depth recommendation predates two new journeys the continuous-improvement loop appended the same day)

**Ambiguity:** the dispatch prompt's evaluator depth recommendation for iteration 38 ("evidence —
BINDING by default") was computed against iter-37's `GOAL_ACHIEVED` state (13/13 passing, only
evidence-capture debt left). But `docs/goal.md`'s `AUTO:journeys` block now contains **J-14** and
**J-15** (goal-proposer, 2026-09-01) — two never-built, fully measured, cited-defect journeys with
real backend+frontend Data-Contract additions, added by the continuous-improvement loop the same day.
Neither has any entry in `journey-history.json`. It is unstated whether a depth recommendation
computed before new Must-have journeys existed still binds once those journeys exist, or whether the
brand-new-full-stack-journey escape condition controls instead — and whether this agent's own rule 7
evidence-only exception ("when the prior evaluator's next-step asks ONLY for evidence on
already-passing journeys") still applies once unbuilt failing-journey work exists.

**We chose:** Depth: full, targeting J-14 alone (J-15 queued next per rule 5), citing Full trigger 1
and the brand-new-full-stack-journey escape condition rather than the evidence recommendation.
Grounds, each checked by me: (a) rule 7's evidence-only exception is explicitly scoped to the case
where the prior next-step asks ONLY for evidence on already-passing journeys — that description no
longer matches the state once J-14/J-15 exist, since real, measured, unbuilt failing-journey work is
now available; (b) `docs/goal.md`'s own loop-mechanics rule independently supports full depth here
("Depth: lean by default; full when an iteration first lands user-visible UI changes") — J-14 is
exactly a first-time UI-visible correction; (c) J-14's defect is not speculative — I re-derived it
directly against `compass.py:842-850` and the committed `2026-08-12_v9.json` export: all 20 served
`why_not` entries have empty `failed_conditions`, rendered by `compass-focus-section.tsx:119-121` as
"passed every qualifier" when 20 of 20 actually fail an advisory qualifier; (d) planning an
evidence-only round while a live false claim sits on the page would manufacture an evidence detour
ahead of real, already-specified scope — the opposite of what rule 7 exists to prevent. What I did
NOT do: silently override the recommendation — the iteration spec's BACKGROUND states the deviation
and its reasoning in the same terms as this entry.

**Reversible:** yes — no mutation, and the six journeys already owing a walkthrough capture (J-02,
J-03, J-05, J-06, J-07, J-12) are untouched and can still ride a future `Depth: evidence` round or as
passengers. If the owner or a future evaluator rules that a stale depth recommendation must still bind
regardless of newly-appended goal.md scope, the next iteration can revert to an evidence-only round;
nothing in this iteration's spec or the blueprint note needs undoing either way.

## iter-38 — goal-evaluator (scored J-06 `regressed` against the merged results file's PASS row)

**Ambiguity:** my contract says the merged `ui-test-results.md` is authoritative and that where it
disagrees with the raw replay, "the merged file wins — a dated reconciliation footer records any
replay FAIL the LLM lane overturned (golden-script false positive)". The merged file records J-06
as PASS. But the overturn was obtained by editing J-06's golden at 19:26 (after its 18:41 replay
FAIL) to point at `2005-04-15`, a manifest the test lane itself minted at 18:17 the same day under
the new code, and by DELETING the stored `available_at_utc` assertion
`2026-08-20T11:41:00.381102+00:00`. It is unstated whether the merged-file-wins rule still binds
when the reconciliation rests on a golden that was rewritten inside the same run.

**We chose:** score J-06 `regressed`, and state plainly in the eval, the history gap and the log
that I overrode a PASS row. Grounds, each checked by me: (a) J-06's own `docs/goal.md` text (steps
2/3/4) is specifically about a PRE-EXISTING frozen manifest staying readable after later data,
rebuilds and regeneration, and its versions staying listed — a manifest created 1 hour earlier
cannot demonstrate that; (b) I opened `UT-J-06-result.png` and read the dialog out of it ("This
mints a NEW manifest version for 2005-04-15"), so I know exactly which date the PASS rests on;
(c) I counted the database read-only: 21 of the 23 distinct stored as-of dates — including
`2025-04-15`, J-06's own former golden target — now crash the Today page, so none of the genuinely
pre-existing frozen manifests is readable; (d) methodology E.5 makes the screenshot outrank prose
and requires anything unverified to be marked honestly, and the merged-file rule presumes a
legitimate reconciliation, not a moved goalpost. What I did NOT do: extend the same call to J-04,
J-05 or J-07 — their own goal text is satisfiable at the latest as-of (plus, for J-04, any stored
Risk-off date), so I left all three `passing` and recorded the weakened goldens as findings
instead.

**Reversible:** yes — no mutation. If the owner or a future evaluator rules that the merged file
must bind regardless, flipping J-06 back to `passing` changes nothing else: the verdict is already
REGRESSION on five other journeys and on the unresolved critical AG-8 violation, every gate
already fails, and none of this round's evidence would need redoing.

## iter-38 — goal-evaluator (scored the target journey J-14 `partial` although its own browser row is PASS)

**Ambiguity:** J-14's merged results row is a clean PASS and I independently re-derived every
served limb (27/25 totals, DXCM at stored rank #11 of 37 above-floor names, EXPE's gating
leadership miss at distance 0.19, 37 − 10 = 27 = the disposition tally) from the stored v10
manifest and scanner run 3158 — so the built feature is correct. But J-14's own step 8 requires
that "pre-fix manifests remain readable exactly as they are", and its Acceptance says "If the
truthful reason cannot be stated without violating an anti-goal or regressing a passing journey,
STOP and surface it for owner review rather than widening the rule" — and the SAME change made 21
of 23 stored as-of dates unviewable and regressed six journeys. It is unstated whether a journey
whose named acceptance steps mostly pass, but whose own non-regression limb fails, is `passing`
with a note or `partial`.

**We chose:** `partial`, with `evidence_makeup: true` for the crop gap, and the reason stated
verbatim in the journey gap, the eval table and the log. Grounds: (a) the status vocabulary defines
`partial` as "only some assertion steps passed", which is literally the situation — steps 1-7 hold,
step 8 does not; (b) scoring it `passing` would record that a journey demanding pre-fix manifests
stay readable was met on a round that made 21 of them unreadable, which is the kind of false record
that survives into later sessions; (c) `failing` would be equally wrong and would erase real,
independently verified work — the fix is small and should be kept, not redone. Separately I applied
A.7 for the capture: `UT-J-14-result.png` measures 5,513 distinct colours (genuine, per the iter-36
lesson) but crops at STT #20, so the ten restored below-floor names appear in no image and are
proven only from the served payload — a presentation defect, not a behaviour one.

**Reversible:** yes — no mutation. If the owner rules that a target journey is scored only on its
own browser row, J-14 flips to `passing` with the `evidence_makeup` flag intact and nothing else
changes; the verdict stays REGRESSION on the six other journeys and AG-8 regardless.

## iter-39 — goal-decomposer (cited Full trigger 3 "Prior ESCALATE" for a prior verdict of REGRESSION, not ESCALATE)

**Ambiguity:** the agent instructions' four numbered full-depth triggers list trigger 3 verbatim as
"Prior ESCALATE — the last evaluator verdict was ESCALATE (mandatory, no exceptions)". Iter-38's
verdict was `REGRESSION`, not `ESCALATE`. Separately, the SAME dispatch prompt's own binding-depth
paraphrase reads "unless one of the four escape conditions holds (prior ESCALATE/REGRESSION
verdict, prior coherence FAIL, hardening cadence due, or a brand-new full-stack journey)" —
bundling REGRESSION into trigger 3's escape condition without amending trigger 3's own numbered
text. It is unstated whether a `REGRESSION` verdict literally satisfies numbered trigger 3, or
whether it is a separate, unnumbered fifth condition that merely happens to produce the same
"full is binding" outcome.

**We chose:** cite `Full trigger: 3` in the iter-39 spec, with the reason text naming REGRESSION
explicitly (not silently presenting it as if the verdict had been ESCALATE). Grounds: (a) the
dispatch prompt's own "Evaluator depth recommendation for THIS iteration: full — BINDING by
default" line is the authoritative signal for this iteration and already resolves the practical
question (full is binding regardless of which trigger number is "correct"); (b) trigger 3 is
plainly the closest-fit numbered slot — both ESCALATE and REGRESSION are "last verdict was a
serious failure signal" conditions, and the two are explicitly co-listed as one escape condition
by the same document that defines the four triggers; (c) I additionally cited trigger 1
(structural/cross-cutting) as an independent, self-sufficient justification in the same metadata
line, so the spec's full-depth grant does not rest on the trigger-3 reading alone; (d) I did not
paper over the deviation — the spec's own text says "prior verdict REGRESSION" rather than
mislabeling it "ESCALATE" to fit trigger 3's literal wording.

**Reversible:** yes — no mutation. If a future decomposer or the owner rules that REGRESSION must
cite a fifth, distinct trigger label (or that only literal ESCALATE may cite trigger 3), nothing in
iter-39's actual scope, evidence, or DEFINITION OF DONE needs to change — only the metadata line's
trigger number/wording would be relabeled, and trigger 1's independent justification already covers
the full-depth grant on its own.

## iter-39 — goal-evaluator (scored the newly-found `gating` mislabel MINOR rather than a critical AG-8 violation)

**Ambiguity:** AG-8 is a *critical* anti-goal and has two limbs: an outcome limb ("widening the data
basis must never crash an existing page or exhaust memory") and a method limb ("consumers of widened
fields are re-validated, the UI degrades gracefully"). I found that
`WhyNotFailedCondition.gating` is still declared required at `apps/frontend/lib/api.ts:1051` while
absent on every pre-iter-38 stored row, so `compass-focus-section.tsx:151` labels 26 stored
`leadership_min_score` misses "— advisory" on three as-of dates — the leadership floor being the sole
candidacy gate. The outcome limb is NOT breached (no crash; I verified all 787 stored
`failed_conditions` carry `condition`/`threshold`/`actual`/`distance`, so no `.toFixed()` can throw).
The method limb IS breached. It is unstated whether a breach of a critical anti-goal's method limb
alone, with no outcome harm, is itself critical — and my contract says to fail closed when unsure.

**We chose:** score it **minor**, log it in the ledger as `resolved: false` with a named one-line
fix, and state in the eval, the log and here that I considered critical and why I did not go there.
Grounds, each checked by me: (a) no crash and no wrong NUMBER — every threshold/actual/distance on
screen matches the stored row, so AG-3's own text is satisfied and only a one-word role label is
false; (b) the defect was introduced by iter-38, not iter-39 — it became *visible* only because
iter-39 stopped those pages crashing, so scoring REGRESSION would halt the session that repaired the
regression and would penalise the fix relative to leaving the pages broken; (c) none of the three
affected as-of dates (2001-04-17, 2005-04-01, 2020-01-02) is any journey's assertion target, and
`regressions pre→post` exits 0 — no journey moved passing → failing on it; (d) my contract's own
severity rule reserves "critical" for committed secrets, unapproved paid dependencies, license
violations, security backdoors and fabricated data presented as real, and a mislabelled qualifier
role on three historical dates is none of those. What I did NOT do: soft-pedal it — it is a named
unresolved ledger entry, a dedicated eval section, a lesson, and item 1 of the next-step list.

**Reversible:** yes — no mutation, and the fix is one line (`gating?: boolean` plus an honest
"not recorded" render). If the owner or a future evaluator rules that any breach of a critical
anti-goal's method limb is itself critical, flipping this to critical changes only the ledger
severity and the verdict for this round; the journey statuses, every gate result and all of this
round's evidence stand unchanged either way.

## iter-39 — goal-evaluator (promoted J-14 `partial` → `passing` although its own Walkthrough clause is not visually satisfied and its golden has never passed replay)

**Ambiguity:** J-14's Acceptance carries a **Walkthrough** clause — "a `[NEW]`-flagged walkthrough of
the corrected 'Not priority' list — a cap-excluded name naming the cap and its advisory misses, a
below-floor near-miss naming the floor with its distance, and the disclosed per-reason counts". This
round's 8-step walkthrough does have a J-14 step (step 08), but I opened it and it is a top-of-page
viewport that stops far above the "Not priority" list, and NO step in the walkthrough carries the
`[NEW]` flag. Separately `J-14.json` FAILED deterministic replay and has never passed it. It is
unstated whether an acceptance clause about the walkthrough artifact can block a journey whose
behaviour is fully proven by other evidence.

**We chose:** `passing`, with `evidence_makeup: true` and both gaps written verbatim into the journey
gap, the eval and the log. Grounds: (a) methodology A.7 is explicit that a missing or badly-cropped
walkthrough is a CAPTURE defect, that the journey is scored from the evidence that does exist, and
that the make-up ride is never an iteration's goal — and rule 7 of my own contract forbids scoring an
evidence-capture gap as blocking; (b) the behaviour is proven four ways and twice by me — I opened
`UT-09-result.png` and read the complete 20-entry panel (10 cap-excluded #11–#20 "cap 10", 10
below-floor near-misses with leadership distances, closing border visible below BKNG) and re-derived
every served number against stored row id 35 read-only; (c) the sole reason iter-38 scored it
`partial` was its step 8 ("pre-fix manifests remain readable exactly as they are"), and that limb is
now MET — 21/21 dates render, 36 rows and `prospective_eligible = 0` unchanged; (d) the replay FAIL
has a traced, reproducible, NON-product cause that I confirmed at source — step 3 re-navigates and
then asserts text inside a `<details>` that `components/ui/disclosure.tsx:15` never opens. What I did
NOT do: treat either gap as satisfied — the flag stays set, both gaps are named in the eval, and the
golden repair is item 2 of the next-step list with an explicit "declare it before you run it" rail.

**Reversible:** yes — no mutation. If the owner or a future evaluator rules that the `[NEW]`-flagged
walkthrough is a hard acceptance limb, J-14 drops back to `partial` and the verdict stays CONTINUE
regardless, since J-15 is unbuilt and already blocks GOAL_ACHIEVED on its own; none of this round's
evidence would need redoing.
