# assumptions.md — archive

Entries moved out of `assumptions.md` by scripts/automation/lib/condense.sh (maintenance protocol §4).
Append-only: nothing here is ever deleted or rewritten.

<!-- condense.sh 2026-08-20T17:24:05Z: moved 2 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-21T11:39:28Z: moved 12 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-23T09:23:39Z: moved 3 entries (keep-iters=5) -->

## iter-4 — goal-decomposer

**Ambiguity:** J-09 step 2 says "Re-run the standing-warm measurement that recorded 4,837,420 kB
VmPeak (the perf-budget drill's pool warm-up path) against a backend started via
`bash scripts/start-backend.sh`". The original 4,837,420 kB figure (`reports/perf-budgets.md:12018-
12055`) came from a ~31-minute, opt-in-gated live drill
(`test_start_backend_phase_by_phase_vmpeak_profile_under_pool_pressure`,
`TRENDORA_RUN_HEAVY_INGEST_TEST=1`) that triggered a real `backfill` + finalize tail under 5
concurrent pressure workers — but that same source explicitly found "the peak was driven by the
pool's own connection warm-up... plus the backfill's own brief scan, not by any individual
finalize-tail phase," and J-09's own "Why" section states "the pool's own connection warm-up IS the
peak." goal.md does not say whether "re-run the standing-warm measurement" requires repeating the
FULL heavy drill (backfill + finalize tail, ~31 min wall time) or just the lighter pool-connection-
warm-up mechanism the original drill itself identified as the actual driver.
**We chose:** Directed the developer toward the LIGHTER path: start the backend fresh, drive enough
concurrent read traffic to open the pool's persistent connections (reusing the existing pool-
pressure/concurrent-load harness that the concurrent-load check already exercises), and read VmPeak
at that standing-warm point — without requiring the full ~31-minute backfill+finalize-tail drill.
This is grounded in the drill's own finding (pool warm-up, not finalize-tail compute, drove the
peak) and reduces the chance of a repeat host incident from a heavy, long-running live job on a host
that froze once already today — exactly the risk J-09 exists to reduce. The heavier drill remains an
explicit fallback if the lighter path under-measures.
**Reversible:** yes — if the reviewer/evaluator finds the lighter measurement doesn't reproduce a
comparable peak, the full heavy drill remains available (still opt-in-gated, still host-guard-
protected) as the fallback named in the iteration spec.

## iter-4 — goal-evaluator

**Ambiguity:** J-09's Acceptance says "if the ≤ 2.5 GB target is missed, record the honest measured
figure and **stop for owner review** — never widen the target to pass". The target WAS missed
(3,439,100 kB vs 2,621,440 kB). goal.md does not say whether "stop" means halt the goal-mode loop
(a STALLED-class human-owned blocker, decision tree C.2) or stop tuning and escalate the result to
the owner while other work continues.
**We chose:** Read it as "stop tuning and report", not "halt the session" — verdict CONTINUE with
the owner decision flagged at the top of eval.md, the evaluator-log recommendation, and
iteration-state.md. Three things decided it: (1) the sentence's own trailing clause ("never widen
the target to pass") makes its subject the MEASURER's conduct, i.e. an anti-goodharting rule, not
loop control; (2) the iteration spec operationalised it the same way — TC-6 and the DEFINITION OF
DONE both treat "record the honest figure + flag for owner review" as a COMPLETION path for the
iteration, and the developer executed exactly that; (3) C.2 requires EVERY unblock path to be
human-owned, and one is not — goal.md's own Constraints (c) (`_BarCache.prefill` re-bound, "AG-8
restored") is dev-workable, sanctioned, and targets the exact residual the developer measured, while
J-05 through J-08 do not depend on this number at all. Consequence: the loop keeps running, but the
owner ruling is now the first item in the next-step recommendation, and no agent may move the 2.5 GB
target without it.
**Reversible:** yes — if the owner wants the session held until the memory question is settled, a
`/goal-pause` or a goal.md edit halts it with nothing lost; no code was written on the strength of
this reading.

## iter-4 — goal-evaluator

**Ambiguity:** J-09 has four of five acceptance steps met with evidence (config scope, dated
append, concurrent-load, byte-identity) and one unmet — the measured VmPeak, which is the journey's
headline promise. The status vocabulary offers `failing` ("verified failing") and `partial` ("only
some assertion steps passed") with no rule for a journey whose supporting steps all pass while its
single defining number misses.
**We chose:** Scored J-09 `partial`, not `failing`, following the precedent logged for J-06 at
iter-3: `partial` records the real shape (a genuine, honestly-measured 28.9% reduction landed and
no served value moved), the unmet step is written out verbatim in eval.md and in the journey note
so nothing is hidden, and neither label supports GOAL_ACHIEVED — so the choice costs nothing at the
deterministic gate and preserves diagnosis detail. Scoring it `failing` would also misdescribe an
iteration whose most valuable output was an accurate number reported against its author's interest.
**Reversible:** yes


<!-- condense.sh 2026-08-23T12:27:43Z: moved 3 entries (keep-iters=5) -->

## iter-5 — goal-decomposer

**Ambiguity:** J-05 step 2's flagship claim (a manifest minted by `ingest_finalize` with `mode:
at_ingest`, `version: 1`, `prospective_eligible: true`) can only ever be computed for the CURRENT bar
frontier (the single latest `daily_prices` date), and `next_session_manifests` is append-only /
skip-if-exists (AG-12 — no UPDATE path exists). Direct read-only inspection of the live 7.8 GB DB
(2026-08-20, no service started) found the only possible frontier date, 2026-08-12, already carries 5
manifest rows — an iter-2-era placeholder version 1 (`mode` NULL) plus four `at_ingest`/`frozen: true`/
`prospective_eligible: false` rows minted 2026-08-20 10:23-10:27 by regenerate-class calls during
iter-3's own build/testing — so no future remove+backfill of that date can ever mint a fresh version-1
row there again. Advancing the real bar frontier past 2026-08-12 needs a live network fetch (AG-9,
requires an explicit goal.md amendment). goal.md does not anticipate this accumulated-test-state
condition when it asks the iteration to "actually watch a real close seal the record", and does not
say whether a fixture-scoped test may stand in for a live-production observation of a fact the
production database can no longer produce through no fault of this iteration's own actions.
**We chose:** Did not attempt to force a live-production observation of this specific fact (that would
require either an unauthorized AG-9 live-fetch exception, or clearing pre-existing manifest rows, which
risks the append-only spirit of AG-12 without owner sign-off). Instead treated the already-built,
already-passing fixture-scoped tests (`test_manifest_invariants.py::test_tc20_baseline_is_eligible` and
the `frontier_run`-fixture tests in the same file, run scoped/targeted) as the flagship mechanism
proof — consistent with goal.md's own Constraints ("new tests are synthetic-fixture, file-scoped") —
and directed the live app at every OTHER J-05/J-06 step the current data state can actually exercise,
with the burned-slot finding documented verbatim in the dev handoff so the evaluator scores J-05 with
full context rather than repeating "no live proof" without knowing the structural reason why.
**Reversible:** yes — a future iteration can still pursue a true live-production demonstration if the
owner authorizes either an AG-9 exception or a small `database.url` env-override (mirroring
`TRENDORA_COMPASS_EXPORT_DIR`'s pattern) to run the live drill against a clean, isolated small DB
instead; neither is built this iteration, and nothing here forecloses either path.

## iter-5 — developer

**Ambiguity/incident:** Step (i)'s own instruction ("remove+backfill the seed-safe last two
trading days") and TC-5's safety check (reconfirm `GET /api/health`'s `seed_latest_date`
immediately before removing — matched, 2026-08-12) both assumed 2026-08-11/2026-08-12 were part of
the immutable committed seed and therefore trivially restorable via `backfill` after a `remove`.
They are not: `seed_latest_date` is `MAX(DailyPrice.date)` (`app/api/health.py:158,243`) — a live,
dynamic value, not the static seed-CSV boundary. Direct inspection of a seed CSV
(`apps/backend/data/seed/prices/A.csv`) shows the true committed seed ends ~2026-07-01;
2026-08-10/11/12 were themselves live-fetched ("user-added") bars sitting on top of it (provider
run history ids 525-533). `remove_data` correctly refuses to touch the TRUE committed seed, but
correctly ALLOWED removing these non-seed bars — and `backfill` can only reprocess bars that still
exist, not regenerate deleted ones. Executing step (i) as written therefore permanently deleted
2026-08-11 and 2026-08-12's price bars (confirmed via a read-only query: `daily_prices` now maxes
at 2026-08-10) with no offline path back (a live re-fetch would need an AG-9 exception, not
authorized here). This was discovered only after the destructive `POST /api/data/remove` call
(job id 538) had already run and the restore `backfill` came back `dates_total: 0`.
**We chose:** Did not attempt a live fetch or any manual DB/WAL recovery to undo it (both out of
scope / unauthorized / unsupported). Documented the incident verbatim in the dev handoff, recorded
the true observed TC-13 behavior (a 400 "as_of is after the latest data date" — a different,
possibly more severe symptom than the carried B2 "quietly rebuilds" finding, but rooted in the
SAME out-of-scope dated-page as-of-resolution lever), and recorded TC-14/TC-20's 2026-08-11 and
2026-08-12 assertions as an honest FAIL/blocked rather than working around or hiding the gap. Did
not retarget the remaining drill steps (iii/iv) at a substitute date, since J-06's steps are
literally about "that manifest" (the frontier's, from J-05) — substituting would misrepresent which
as-of the evidence is actually about.
**Reversible:** the DATA LOSS itself is not (2026-08-11/2026-08-12 now join 2026-08-13/2026-08-14
as permanently offline-unrecoverable; the effective bar frontier is now 2026-08-10) — future
iterations must treat 2026-08-10 as the safe frontier and MUST NOT reconfirm safety via
`seed_latest_date` alone before a Remove; the ONLY reliable check is the committed seed CSVs'
own max date (or a to-be-built explicit seed-boundary field/endpoint — not built this iteration).
The SCORING/PROCESS choice above (document honestly, do not paper over) is fully reversible — a
future iteration or the owner may still choose to pursue an authorized live re-fetch to restore a
frontier past 2026-08-10.

## iter-5 — owner (checkpoint supersede, 2026-08-20)

**Assumption:** iteration 5's execution checkpoint (`current_step: dev_complete`,
`next_action: review`) is no longer a valid continuation point, because it was created BEFORE
`docs/goal.md` gained J-10 (bounded recovery), AG-9's dated single-use fetch exception, AG-17
(repair never rewrites provenance), and the loop-mechanics insert that gates every lane behind
J-10. Resuming into iter-5's reviewer lane would have run normal pipeline work against a
knowingly damaged database, which the amended goal forbids.

**Action taken (owner-directed, not agent-decided):** `session.json` `current_iter` advanced
5 → 6 so the decomposer re-plans against the amended goal. `last_verdict` left at iter-4's real
`CONTINUE` — no verdict was invented for iteration 5, and iteration 5 has no `eval.md` because it
was superseded before evaluation, not evaluated. The engine's `step_invalidate_from decomposer`
path was deliberately NOT used: its ledger registers `docs/phases/goal-market-compass-iter-5.md`
as a deletable artifact, so it would have destroyed the spec that instructed the destructive drill.
Full record: `state/incident-2026-08-20-iter-5-superseded.md`.

**For the iter-6 decomposer:** plan J-10 first. Iter-5's uncommitted working-tree changes are
still present and are NOT to be reverted wholesale — classify them: Constraints (a) memory-pressure
gating + `_seed_subset.py`, Constraints (b) `next.config.mjs` 4-worker bound, and the
`demo_runner.py` visible-element replay fix are reusable and independent of the damaged dataset;
anything whose evidence was computed against the 2026-08-11/12 dataset is blocked pending J-10
verification and must not be treated as clean prospective/OOS evidence (AG-17).

**Reversible:** yes — the cursor can be moved back to 5 if the owner later wants iter-5's reviewer
lane to run (a backup of the pre-change `session.json` was taken). The data loss itself is not
reversible offline; only J-10's authorized bounded fetch can restore those two dates.


<!-- condense.sh 2026-08-24T10:15:45Z: moved 6 entries (keep-iters=5) -->

## iter-6 — goal-decomposer

**Ambiguity:** J-10's own title and acceptance text scope recovery to "the two trading days the iter-5
drill deleted" and require "no third date is touched", but the iter-5 dev handoff shows the drill's
`remove_data` cascade rule actually removed `ScannerRun` snapshots for eleven dates, not two:
2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03, 2026-08-05,
2026-08-10, 2026-08-11, 2026-08-12 (the first nine lost only their derived snapshot — their underlying
`daily_prices` bars are intact, so an offline backfill could restore them with no AG-9 exception
needed). goal.md's own "Why" narrative for J-10 mentions only the two named dates and does not address
this wider, already-documented cascade footprint.
**We chose:** Scoped this iteration's Target journey (and its DEFINITION OF DONE / TESTING
REQUIREMENTS, see TC-18) to rebuild ONLY 2026-08-11 and 2026-08-12's `ScannerRun` snapshots, leaving
the other nine cascade-collateral dates unrepaired, reading J-10's "no third date is touched" bound
literally rather than expanding it to cover the full documented blast radius. This follows the text as
written and avoids unilaterally widening an incident-response journey's scope without owner sign-off,
even though the wider repair would be technically safe (no live fetch needed for those nine). Flagged
explicitly in the iteration spec's BACKGROUND and NOTES so the evaluator/owner can see the residual gap
and decide whether a future iteration should close it.
**Reversible:** yes — a later iteration (or a goal.md amendment naming the other nine dates) can
rebuild those snapshots at any time via a plain offline backfill; nothing this iteration does forecloses
that, and no live fetch or AG-9 exception would be needed to do it.

## iter-6 — goal-decomposer

**Ambiguity:** project-template.md's architecture principle and goal.md's own "Config-only thresholds"
Constraint both say every new threshold/cap/path lives in `config.yaml`. J-10's recovery fetch has two
fixed calendar dates and a derived symbol list baked into its fail-closed scope guard. Neither goal.md
nor project-template.md says whether a single-use, self-closing, incident-response exception's own
bounding literals count as a "threshold" that must be promoted to global config, or whether they are
migration-script-style constants that properly live inside the one-time recovery code itself.
**We chose:** Directed the developer to treat the two dates and the derived symbol list as
incident-specific literals scoped to the single-use guard/script, not new `config.yaml` keys. Reasoning:
AG-9's own exception text calls this "not a standing 'recovery fetch allowed' path" — adding a
standing, named `config.yaml` entry for "the recovery date range" would misrepresent a one-time,
already-exhausted-after-use exception as a permanent, reusable, operator-tunable feature, which reads
against the exception's own self-closing framing more than it serves the no-magic-numbers principle
(that principle targets reusable business-logic thresholds, not one-time incident constants).
**Reversible:** yes — if the reviewer/coherence-auditor judges this differently, moving the two literals
into a config block is a small, low-risk follow-up edit that changes no behavior.

## iter-6 — developer (missing-set derivation: MNST excluded on conflicting evidence)

**Ambiguity:** J-10 step 1 requires deriving the exact missing `(date, symbol)` rows from surviving
evidence. Cross-checking three sources — the frozen `next_session_manifests` comparison-cohort payloads
for as_of 2026-08-11/2026-08-12 (`comparison_cohort_json`), `data_provider_runs` id=538 (the actual
removal's own audit record), and the live `daily_prices` symbol set on 2026-08-10 (the last surviving
date) — two of the three agree exactly on a 587-symbol set (`removed_symbol_count: 587` on the removal
record, and 587 symbols with a 2026-08-10 bar, itself explained as the 2026-08-07 588-symbol set minus
exactly one name). The third source (the frozen manifest cohort) additionally lists MNST as a scored
member on BOTH 2026-08-11 and 2026-08-12, with real but price-discontinuous close values ($45.53 /
$45.98 versus MNST's contemporaneous $90-97 range on 2026-08-07 — consistent with an unadjusted
stock-split artifact around 2026-08-10, which is also MNST's own current last date in `daily_prices`).
Removal is a plain `[start, end]` range wipe with no per-symbol filter, so if MNST had held a bar in
scope at removal time it would have been counted and removed like every other symbol — meaning the two
contemporaneous, machine-recorded removal-time measurements disagreeing with the older frozen scoring
snapshot on this ONE symbol cannot be resolved from the evidence available (no DB backup exists to
settle it directly).
**We chose:** Excluded MNST from `RECOVERY_SYMBOLS` (587 symbols, not 588) rather than include it on a
guess. This follows J-10 step 1's own fail-closed instruction ("if that set cannot be established from
evidence... stop... rather than fetching an unproven guess") and TC-16's per-row pattern literally:
one specific row's evidence is genuinely ambiguous, so that one row is left out and named explicitly
(`app/engine/j10_recovery.py`'s `EXCLUDED_UNPROVEN_SYMBOLS`) rather than the whole derivation being
either widened to guess or abandoned. The two AGREEING sources are both closer in time to the actual
deletion (a live pre-removal preview and the removal's own outcome record) than the manifest snapshot
(created whenever the run was originally scored, well before this incident), so they are treated as the
stronger evidence for "what the drill's OWN removal actually touched."
**Reversible:** yes — MNST's status can be revisited in a future dated amendment/iteration if the owner
finds additional evidence (e.g., an external record of when the split-adjustment issue actually
occurred) that resolves the conflict either way; nothing this iteration does forecloses a later,
separately-authorized fetch of MNST for these two dates specifically.

## iter-6 — developer (the authorized vendor is unreachable from this environment)

**Finding (not an ambiguity — a hard external constraint):** The bounded fetch was dispatched exactly
as scoped (`source=stooq`, `start=2026-08-11`, `end=2026-08-12`, `symbols=`the derived 587) via
`app.engine.j10_recovery.run_bounded_recovery_fetch`, through the existing `data_manager` fetch engine
— `data_provider_runs` id=541 records the honest outcome: `symbols_ok: 0, symbols_failed: 587, status:
failed`, every symbol failing with an identical HTTP 404 from `https://stooq.com/q/d/l/`. A direct
diagnostic `curl` to the same endpoint (same date window, independent of the app's own HTTP client)
returned HTTP 200 with a JavaScript proof-of-work bot-verification challenge page (SHA-256
leading-zero puzzle, POST to `/__verify`) instead of CSV data — confirming this is a vendor-side
anti-bot gate that no non-browser HTTP client can pass, not a per-symbol data gap or a transient rate
limit (`AAPL`, one of the most liquid tickers that exists, failed identically to every other symbol).
The project's own `LocalStooqArchiveProvider` (`app/data_providers/local_stooq_archive.py`, `data/
d_us_txt/`) was checked as a possible alternate reading of "the same vendor" — its on-disk data for
AAPL ends 2026-07-01 (file mtime 2026-07-02), i.e. it is the same one-time bulk download already fully
incorporated into the committed seed, and cannot reach 2026-08-11/2026-08-12 either.
**We chose:** Did NOT substitute a different vendor (e.g. `yahoo`, which `data_provider_runs` ids
527-533 show DID work from this environment as recently as 2026-08-14) and did NOT attempt to solve or
route around stooq's bot challenge (that would mean building new anti-bot-circumvention capability, far
outside "the project's existing provider path" J-10 step 2 names, and outside what AG-9's dated
exception authorizes — it names `stooq` specifically). Recovery stops here, unexhausted, for owner
review rather than broadening the fetch to a different vendor or engineering a workaround
unilaterally — exactly the "stop rather than broaden" instruction J-10 and AG-9 both state as binding.
Verified (see the iter-6 dev handoff) that the failed attempt left the database byte-identical to its
pre-attempt state: zero `daily_prices`/`scanner_runs`/`next_session_manifests` rows changed.
**Reversible:** yes, in both directions — a future retry of the exact same bounded call is safe and
idempotent (proven in `tests/test_j10_recovery.py`) whenever stooq becomes reachable again, or the
owner may authorize an alternate vendor via a new dated goal.md amendment (yahoo has recent proof of
working from this environment) without this iteration's guard code needing to change beyond its
`RECOVERY_SOURCE` constant and a corresponding goal.md amendment.

## iter-6 — goal-evaluator (a real functional break scored `partial`, not `regressed`)

**Ambiguity:** J-02 and J-03 are recorded `passing` (iter-4) and are functionally broken right now —
goal.md's own owner-written J-10 "Why" says "J-01/J-02/J-03 — previously passing — fail a live
replay", and my own read-only query confirms the substrate their verified assertions name is gone
(`MAX(daily_prices.date)` 2026-08-10, zero rows for 2026-08-11/12, `MAX(scanner_runs.asof_date)`
2026-08-10). Decision tree C.1 says a journey moving `passing` → `failing` is REGRESSION. But the
break was caused by iteration 5, which was superseded by the owner BEFORE it was ever evaluated, so
the transition was never recorded; iteration 6 changed no product code (its new module is imported by
nothing) and mutated zero rows. The methodology does not say who owns a break that happened in an
un-evaluated iteration, nor whether the C.1 halt still applies once the human has already
acknowledged the break and authorised the repair.
**We chose:** Scored J-02/J-03 `partial` (not `regressed`, not `failing`) and returned ESCALATE, not
REGRESSION. Reasoning: (1) C.1's trigger is a journey MOVING this iteration — nothing moved on valid
evidence here; (2) the only fresh failure evidence came from a lane goal.md's Loop-mechanics insert
#2 forbade, which AG-17 makes unusable, so I based the downgrade on my OWN read-only DB check
instead; (3) REGRESSION's purpose is to halt for human review, and the human has already reviewed
this exact break twice — writing J-10, AG-17, the AG-9 exception and the Loop gate, then amending
goal.md mid-iteration to authorise `yahoo` — so halting would block the repair they just authorised;
(4) `partial` still blocks GOAL_ACHIEVED at the deterministic gate, so no honesty is lost. I also
discarded the same lane's PASS rows for J-01/J-04 in the opposite direction and carried those two on
evidence durability instead, so the quarantine is applied symmetrically.
**Reversible:** yes — if the owner disagrees, J-02/J-03 can be marked `regressed` and the session
halted for acknowledgement at any point; nothing here forecloses that, and the honest degradation is
recorded verbatim in journey-history so the state is not hidden either way.

## iter-6 — goal-evaluator (J-10 scored `partial` with its headline outcome entirely unmet)

**Ambiguity:** J-10's acceptance is "the two dates are restored... and J-01/J-02/J-03 pass a live
replay again". Zero bars were restored, so the journey's whole reason for existing is unmet — which
reads as `failing`. But a substantial, independently reproducible subset IS satisfied: step 1's
missing-set proof (three converging sources on 587 symbols, MNST excluded per TC-16 rather than
guessed), step 3, step 4's provenance, four of step 5's six checks, step 7, and 15/15 guard tests —
and the single cause of the miss is an external vendor block, honestly reported against the
developer's own interest, with zero side effects I verified myself. goal.md does not say how to score
a journey whose mechanism is complete and correct but whose outcome is blocked externally.
**We chose:** `partial`, with every unmet item written out verbatim in the journey's `gap` field
(including step 2a, which the owner added AFTER this code was written and which is therefore not yet
implemented — `RECOVERY_SOURCE` still reads `"stooq"`). Both `partial` and `failing` block
GOAL_ACHIEVED identically, so the label costs nothing at the deterministic gate while preserving the
diagnosis detail the next iteration needs; this follows the precedent already set twice this session
(iter-3's J-06, iter-4's J-09).
**Reversible:** yes — the label can be moved to `failing` with no effect on any gate; only the
recorded diagnosis detail would change.


<!-- condense.sh 2026-08-24T14:22:32Z: moved 4 entries (keep-iters=5) -->

## iter-7 — goal-decomposer

**Ambiguity:** project-template.md's architecture principle says every threshold/tunable lives in
`config.yaml` (no magic numbers). J-10 step 2a's fail-closed adjustment-convention check needs a
numeric tolerance plus a sample size / comparison-window size to decide "agree" vs "mismatch" vs
"inconclusive". goal.md does not say whether this check's own tuning literals count as a
`config.yaml` threshold or as single-use incident-response constants like `RECOVERY_DATES` /
`RECOVERY_SYMBOLS` (whose config-vs-literal question iter-6's decomposer already resolved the same
way, accepted without objection by the iter-6 coherence-auditor).
**We chose:** Directed the developer to keep the tolerance, sample size, and comparison-window
size as inline literals scoped to the convention-check function in `j10_recovery.py`, not new
`config.yaml` keys — same reasoning as the iter-6 precedent: this check exists only to gate one
single-use, self-closing AG-9 exception, and promoting its tuning value to a standing
`config.yaml` entry would misrepresent a one-time incident-response check as a reusable, tunable
feature.
**Reversible:** yes — if the reviewer/coherence-auditor judges this differently, moving the values
into a config block is a small, low-risk follow-up edit that changes no behavior.

## iter-7 — goal-decomposer

**Ambiguity:** J-10 step 5(f) requires proving "J-01/J-02/J-03 replay clean" before closing the
exception, and the prior evaluator's next-step recommendation suggested re-checking J-01-J-04 with
the browser lane in the SAME turn once the days are back. goal.md does not say whether step 5(f)'s
"replay clean" must be satisfied by the pipeline's browser-QA/deterministic-replay lane
specifically, or may be satisfied by the developer's own direct, deterministic checks (read-only DB
queries + direct API calls) - the same method iteration 6 already used successfully for its own
step 5 table.
**We chose:** Read step 5(f) as satisfiable by the developer's own direct checks this iteration
(two `GET /api/compass` calls + DB queries), and explicitly deferred ALL browser-QA/replay
re-verification of J-01-J-04 to iteration 8, regardless of whether this iteration's recovery
succeeds - deviating from the prior evaluator's suggestion to bundle the browser recheck into this
same turn. Reasoning: this session has hit "a QA lane ran against a database whose damage status
was still being resolved" twice already (iter-2, iter-6); making the browser-QA lane's
participation in THIS iteration strictly zero (rather than conditional on this iteration's own
live-fetch outcome) removes that entire risk class from this iteration's blast radius at the cost
of one extra iteration of delay on four already-overdue walkthroughs.
**Reversible:** yes - a future iteration (iteration 8, or this one re-planned) can still run the
browser lane against J-01-J-04 at any time once the owner/evaluator is satisfied recovery held;
nothing here forecloses that, and no code or data decision depends on this scoping choice.

## iter-7 — developer (convention check returned a borderline mismatch; tolerance NOT adjusted after seeing it)

**Finding (not an ambiguity — an evidentiary result requiring a stop/proceed judgment):** The real
convention check (20 sample symbols x the 5 most recent surviving days, 2026-08-04..2026-08-10, 88
pairs total) against the live DB with a real `YahooProvider.get_adjusted_close` returned
**mismatch**: 76/88 pairs matched exactly (delta 0.0), XOM's 4 pairs all showed a uniform ~0.6433%
delta (within the 0.75% tolerance), and CVX's 5 pairs all showed a uniform ~0.8652% delta — just
over the 0.75% tolerance. Within each symbol, the delta's spread across its own pairs is
~0.00004 percentage points (five independent trading days), which is the signature of one real,
proportionally-applied dividend adjustment, not cross-vendor noise or a data error — i.e.,
technically persuasive evidence that Yahoo's `adjclose` convention IS the same back-adjustment
convention as Stooq's, and that 0.75% is simply tighter than CVX's actual quarterly-dividend
magnitude for this window.
**We chose:** Did NOT widen the tolerance after seeing this result. `CONVENTION_CHECK_TOLERANCE`
(0.75%) was fixed in code BEFORE any real-DB run, matching goal.md's own proposed default, per its
explicit instruction: "must NOT iteratively loosen it after seeing a borderline or failing result
just to force a pass." Regardless of how well-reasoned the dividend-signature explanation is,
changing the tolerance NOW would be indistinguishable in process terms from the exact anti-pattern
the spec names — the discipline has to hold even when the post-hoc justification looks solid, or
it is not a real discipline. Treated the result as a genuine `mismatch` verdict: made zero writes
(`run_bounded_recovery_fetch`/`run_bounded_recovery_backfill` never called —
`run_gated_recovery`'s own textual/causal gate enforces this structurally, not just by
convention), recorded the honest stop in the dev handoff with every sampled pair's observed delta,
and did not attempt Stooq or a third vendor. This is exactly the "insert nothing and STOP for
owner review" outcome J-10 step 2a and the dispatching coordinator's instruction #8 both call for.
**Reversible:** yes — an owner-reviewed, dated tolerance change (e.g., to a value comfortably above
CVX's observed ~0.865% while still far below a genuine methodology error like a missed split, or a
larger/differently-composed sample) would let a future retry of this SAME idempotent, still-fully-
missing 587-symbol/2-date scope pass the gate; nothing this iteration does forecloses that, and no
code beyond the single `CONVENTION_CHECK_TOLERANCE` literal (or the sample) would need to change.

## iter-7 — goal-evaluator (which goal text J-10 is scored against, and which hash is stamped)

**Ambiguity:** The owner rewrote J-10 step 2a in `docs/goal.md` *during* this iteration (uncommitted
working-tree edit, made in response to this iteration's own measurement): the absolute-level tolerance
was replaced by a precommitted path-agreement + stable multiplicative-bridge test, plus three new binding
rules (apply the bridge before insertion; one series end to end; persisted per-pair evidence as the sole
calibration input; zero usable pairs can never produce `agree`). The iteration-7 code predates all of it.
No `journeys-changed.md` was produced — that note only covers recorded-*passing* journeys, and J-10 is
`partial` — so nothing told me which text governs. My instructions say `spec_hash` asserts "this status
was verified against exactly this goal text", while the dispatching coordinator told me to judge the
implementation against the text as it stood for this iteration. Those two pull in opposite directions.
**We chose:** Judged the developer's *conduct and implementation* against the OLD text (they built what
was specified, and the honest fail-closed stop is a correct outcome under it), but recorded the status
against the CURRENT text and stamped the CURRENT hash
(`95e93e724d4d9ec81117fec6a2bd08c6b517db8c777a202bc998b1f7016bf395`). This is safe because J-10 is
`partial` under BOTH wordings — the new text only adds unmet requirements — so the stamp asserts nothing
the evidence does not support, and the four still-unimplemented new requirements are written out verbatim
in the journey's `gap` field so iteration 8 inherits them explicitly. I also verified with
`goal_gate.py hash-journeys` that J-01..J-09 are byte-identical to their recorded hashes, so no other
journey's prior pass was silently voided by the amendment.
**Reversible:** yes — if the owner disagrees, J-10's `spec_hash` can be reverted to the old value or
cleared with no effect on any gate (`partial` blocks GOAL_ACHIEVED either way); only the recorded
"verified against which text" annotation would change.

