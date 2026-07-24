# Goal Session ops-hardening — Assumption Ledger

Append-only. Each entry logs a spec decision that required interpreting an ambiguity in
`docs/goal.md` rather than a routine scoping pick. Zero entries for most iterations is normal.

## iter-13 — goal-evaluator

**Ambiguity:** Decision-tree C.1 reads "an unresolved critical anti-goal → REGRESSION," but iters 11/12
established (and the human ratified by continuing) a doctrine that C.1's halt only fires for a violation
INTRODUCED/WORSENED/NEWLY-DISCOVERED *by this iteration's code*, and here the AG-8 code path is
byte-unchanged (TC-12). The trigger for the ~12-min outage was concurrent browser-qa test load, not
iter-13's product diff — so whether the observed-severity escalation counts as "worsened/newly
discovered" (fire REGRESSION) vs "same carried bug, just re-observed" (CONTINUE, as iter-12 did) is a
genuine interpretation call.
**We chose:** fired REGRESSION. Treated the escalation from "silent internal abort, zero client 500s"
(iter-12) to "full ~12-min availability outage requiring an operator hard-restart" (iter-13) as
NEWLY-DISCOVERED damage that changes the stakes of the deferred owner decision — not a re-presentation of
the settled call. The specific justification iters 11/12 used to withhold the halt (blast radius smaller
than iter-7, self-recovers, no manual restart) is directly falsified this iteration, and the affected
property (availability / "never a frozen frame") is the exact thing this ops-hardening goal exists to
guarantee. Corroborated by three independent artifacts (audit, closure, screenshot), not just the pump
note. A human who reads C.1 as strictly code-scoped, or who regards AG-8 as already-decided-defer
regardless of severity, would instead score CONTINUE (or plain STALLED, since all remaining GOAL_ACHIEVED
blockers are owner-owned) — I note STALLED as the true second decision-tree match in the eval.
**Reversible:** yes

## iter-14 — goal-decomposer

**Ambiguity:** J-07 step 4 permits either "a test hook OR a tightened cap in a throwaway process" and its
step 1 literally describes a SINGLE long-lived sequential process (warm all horizons, then poll health).
But iter-13's actual REGRESSION trigger was CONCURRENT load (4 replay backfills + a diagnostic read), and
the repo's existing "no leaked lock" tests (`test_finalize_hook_memory_error_leaves_no_leaked_lock_subsequent_read_succeeds`
and siblings in `test_data_manager.py`) are all `monkeypatch`-injected MemoryError, a same-layer stub that
already failed to predict iter-11's live 500s or iter-13's live 12-minute wedge. goal.md does not say
whether J-07's Acceptance ("a memory-pressure abort never leaves the process wedged") must be proven under
a REAL tightened-`ulimit -v` induction and under concurrent callers, or whether the literal single-process/
test-hook-or-monkeypatch reading suffices.
**We chose:** wrote TESTING REQUIREMENTS to require BOTH a real (non-monkeypatched) tightened-`ulimit -v`
subprocess test AND a concurrent-caller (N>=4) test mirroring iter-13's actual trigger shape, in addition
to the byte-identity tests J-07 literally asks for. This is a stricter reading than the letter of step 4's
permissive "or," chosen because the cheaper (monkeypatch-only, single-process) reading is exactly the
methodology that already missed this defect twice this session (iter-11, iter-13) — repeating it would let
the recovery iteration "pass" its own tests while leaving the reproduced failure mode unverified. A human
who reads J-07 literally (test hook OR monkeypatch is sufficient, no concurrency requirement) may consider
TC-3/TC-4 as this iteration's own scope-add rather than something goal.md strictly requires.
**Reversible:** yes

## iter-14 — goal-decomposer

**Ambiguity:** The pump note instructed "write it as operator-supervised" for J-07 steps 1/3's full-basis
warm + VmPeak measurement (an AG-10-class heavy pass), stating the owner's plan approval already
authorizes it, but did not specify whether "operator-supervised" means the agent runs the confined
measurement itself (as iter-3/8/9's own heavy passes were performed, per `reports/perf-budgets.md`'s own
protocol descriptions) or whether the human must literally type the launch command this session, given
other pump/decomposer notes this session (iter-10, iter-11) that treated backend process starts as
potentially blocked by a permission classifier.
**We chose:** wrote the standard path as the developer/reviewer running the confined pass directly
(`scripts/start-backend.sh` under the declared host-guard caps, sampler, and watchdog — the same
mechanism iter-3/8/9 used), with an explicit operator-fallback if this session's environment blocks the
process start: the operator starts/monitors and reports console output, pids, and timestamps verbatim for
attributed recording. This mirrors the accepted fallback pattern from iter-10/iter-11's own ledger entries
applied to a new action (the J-07 heavy pass) in the same operational context. A human who reads
"operator-supervised" as requiring the literal human-typed command every time may instead treat this
iteration's TC-5/TC-6 as blocked pending an explicit operator action, regardless of the standard-path
attempt's outcome.
**Reversible:** yes

## iter-14 — goal-evaluator

**Ambiguity:** TC-6's literal GWT (induce memory pressure on the LIVE full-deep-basis TC-5 process; assert
isolated abort + continued serving in that SAME process) was not executed — the operator judged ballooning a
6 GB-capped process on this two-hard-reset host an unjustified AG-10 hazard. The spec explicitly assigns the
sufficiency call to the evaluator: is TC-3 (a REAL `ulimit -v` induction, but on a synthetic 60K-row
subprocess) + TC-5's organic MemoryError-absence enough for J-07 step 4?
**We chose:** ruled the two-leg evidence REASONABLE — TC-3 is a real (non-monkeypatched) RLIMIT_AS induction
that demonstrates the exact honest-abort-then-same-process-recovery mechanism TC-6 wants, and forcing a
live-process induction on this crash-history host is a genuine hardware hazard the host-guard regime exists
to prevent. So I did NOT treat TC-6-partial as a hard blocker requiring a halt. I did NOT upgrade it to a
literal PASS either: J-07 stays partial (independently held there by UT-04 + the unproduced walkthrough), and
a live-process induction remains a candidate owner-authorized follow-up. A human who requires TC-6's literal
GWT before crediting J-07 step 4 would keep that step explicitly unproven.
**Reversible:** yes

## iter-14 — goal-evaluator

**Ambiguity:** Decision-tree C.1 fires on an unresolved critical anti-goal. AG-8 drove iter-13's REGRESSION;
UT-04 shows the SAME trigger (concurrent load on the deep basis) still produces a 211.8s `/backtest` anomaly,
so "the fix fully holds under the reproduced trigger" is not proven — is AG-8 resolved or still open?
**We chose:** marked AG-8 RESOLVED. AG-8's own text forbids a crash, memory exhaustion, or an unbounded
whole-table ORM load; UT-04 is none of these (I opened `UT-04-resolved-slow.png`: page rendered fully, Ready
badge, health green, VmPeak flat, self-resolved) — it is a latency/lock-contention regression (J-06 budget
territory), a DISTINCT non-critical follow-up. Keeping AG-8 critical/unresolved would falsely imply the
memory-exhaustion/crash defect persists, which three independent verifications (evaluator CSV recompute,
reviewer rerun, audit rerun) contradict. I did NOT launder UT-04 away — it keeps J-06 and J-07 partial and is
next-step item 1. A human who reads AG-8 as "the guarantee must hold under the exact reproduced concurrent
trigger before it is resolved" would keep AG-8 open and likely score STALLED (remaining blockers then
owner-owned) or CONTINUE.
**Reversible:** yes

## iter-15 — goal-decomposer

**Ambiguity:** J-06's acceptance ties latency to "page loads stay within committed never-regress
budgets" via a step-1 sweep that reads as a single-page-at-a-time measurement; J-07's acceptance
literally requires only "no unbounded whole-table ORM materialization," "a memory-pressure abort
never leaves the process wedged," and "health/readiness stay truthful" — it does not explicitly
require `/backtest`'s OWN response time to stay in budget during the very concurrent warm+serve
scenario its own step 1 constructs. Whether UT-04's 211.8s concurrent-cache-miss finding is
therefore a J-06 budget violation, a J-07 "honestly responsive... while serving" violation, both, or
neither (health stayed green, no wedge, no crash) is not settled by goal.md's literal text — iter-14's
own audit flagged exactly this: "the ≤1.5s budget belongs to a prior phase under a condition that
phase never tested — it is not one of iter-14's DEFINITION-OF-DONE items."
**We chose:** followed iter-14's evaluator, who already read UT-04 as blocking BOTH J-06 and J-07
(scored `partial`, not `passing`, specifically because of this finding) rather than treating it as
out-of-contract disclosure. This iteration's entire scope — root-causing and fixing the
concurrent-load latency, gated PASS/WARN against the committed ≤1.5s budget — builds on that same
reading, continuing rather than re-litigating it. A human who reads J-06/J-07 literally (no
concurrent-load latency requirement in either journey's own step text) could instead score both
`passing` today with UT-04 disclosed as a footnote, in which case this iteration is still legitimate
hardening but not literally required for GOAL_ACHIEVED.
**Reversible:** yes

## iter-15 — goal-evaluator

**Ambiguity:** With the stacking pathology fixed, the residual `/backtest` cold-MISS is 178.74s (~119x
over the ≤1.5s budget) but the page renders honestly (Ready, honest NA, never frozen) and the WARM load
is fast (116-554ms). The pump note explicitly asks whether J-06/J-07's serve-responsiveness clause is
"satisfied by stacking-fixed + honest-skeleton + warm-path-fast (the cold-MISS being an inherent one-compute
cost the ingest warm exists to pre-empt)" — which would flip both to passing → GOAL_ACHIEVED — or whether
it stays partial pending an owner decision. J-06 step 2 ("assert every measurement is within budget") and
the acceptance's honest-status bullet ("anything slower than its budget shows honest progress, never a
frozen frame") pull opposite directions, and J-07's own step text arguably requires only health/no-wedge,
not `/backtest`'s own response time.
**We chose:** did NOT flip J-06/J-07 to passing on the evaluator's own authority; kept both `partial` and
returned STALLED to route the acceptance decision to the owner. The goal's Success Criteria commit to
"page loads stay within committed never-regress budgets", a 119x breach (plus a distinct 5.37s breach) is
a real recorded budget violation, and iter-12's human-ratified precedent kept J-06 partial rather than
launder a budget breach into a green check. The pump note, audit §5, and QA #3 all independently frame the
acceptance as an owner call. A human who reads J-06/J-07 literally (no concurrent-cold-MISS response-time
requirement in either journey's own step text; honest-status clause governs the slow path) could instead
accept option (3), score both passing, and reach GOAL_ACHIEVED — which is exactly why this halts for the
owner rather than the evaluator deciding it silently.
**Reversible:** yes

## iter-16 — goal-decomposer

**Ambiguity:** J-08 step 4 reads literally as "GET /api/backtest and the MCP query_backtest tool perform
zero aggregate computation on ANY request" — unqualified by is_latest/historical. But every other
ingest-time cache in this session (EventStudyCache/MarketPhaseCache/IndexSeriesCache/CoverageSnapshot)
keeps an explicit "cannot be precomputed (user-parameterized)" carve-out for a non-default/historical
parameterization, which lazily computes-once-and-caches on first view — and `/backtest`'s own historical
as-of viewing ("time machine", J-14/17/18) is pre-existing, goal.md's Non-Goals bar "not a rewrite," and
the ingest finalize warm only ever targets the current latest run's date (never a swept set of historical
dates). Reading step 4 fully literally (zero compute for EVERY as-of, including historical) would mean a
historical `?as_of=` view almost always renders "not yet computed" instead of real evidence, since the
GLOBAL `dataset_version` stamp invalidates a historical row on virtually every subsequent backfill — a
real regression to existing time-machine capability that none of J-08's 5 steps actually exercise (all 5
describe the default/latest view only).
**We chose:** scoped the "never compute on request" guarantee (and its call-count-zero proof) to requests
where the resolved run is the current latest (`is_latest == true`) — matching exactly what the ingest
finalize warm targets and every one of J-08's 5 steps' own scenario (none names a historical as-of). A
historical (`is_latest == false`) request keeps its existing, unchanged lazy create-once-and-cache
behavior — the same carve-out every sibling cache already documents. This is scoped, not silently
expanded: IN SCOPE/OUT OF SCOPE/TESTING REQUIREMENTS in the iter-16 spec all say so explicitly (TC-13) so
the evaluator can check the historical path was not silently broken. A human who reads step 4 fully
literally would require historical as-of viewing to also degrade to "not yet computed" whenever its
dataset-version stamp is stale, and might score this iteration's historical-path carve-out a gap rather
than a correct scope boundary.
**Reversible:** yes

## iter-16 — goal-evaluator

**Ambiguity:** goal.md J-08 step 2 says the refresh window serves the last complete stored version
"labeled with that version's served as-of"; step 5 defines `not_yet_computed` as "a store where no warm
has ever completed for any version (fresh-install shape, a test fixture)". The implementation resolves all
three states strictly within ONE `asof_key`, so an ingest that ADVANCES the latest date (audit B1, the
"common single-latest-date backfill" per `data_manager.py:3172`) yields `not_yet_computed` on a store that
is full of complete versions. goal.md never states whether the fallback must cross as-of boundaries, and
the iteration spec's own IN SCOPE bullet 2 + TC-6 encode the per-`asof_key` scoping — so the
implementation is spec-conformant while arguably not goal-conformant. The auditor graded it GAP and
explicitly routed the call to me.
**We chose:** ruled that the fallback MUST cross as-of boundaries, and therefore kept J-08 `partial` (and
with it J-06/J-07) rather than scoring the iteration's own spec as sufficient. Reasons: "labeled with that
version's served as-of" is meaningless unless the served as-of can differ from the current one; step 5
reserves the empty state for the fresh-install shape, which B1's flow is not; and the resulting UX shows
an empty evidence section plus copy telling the user to "run an ingest" they are already running (audit
F2). Treated this as reading the goal text (mine to do) rather than a product-direction decision (the
owner's), because the fix is bounded and agent-owned — which is also why the verdict is CONTINUE rather
than iter-15's STALLED. A human who reads J-08's per-`asof_key` scoping as the intended contract (the
iteration spec's own reading) would score B1 an acceptable documented gap and could score J-08 `passing`,
subject to the separate latency and browser-evidence gaps.
**Reversible:** yes

## iter-16 — goal-evaluator

**Ambiguity:** J-04 is in this iteration's Required-still-passing set but has no golden replay script, so
it rode the LLM browser-qa lane — which SKIPPED it, because its steps need a backend kill/restart and
service actions were blocked this session. The methodology's screenshot rail says no fresh evidence means
no fresh pass, but its stable-journey rule also lets unchanged journeys carry over, and `unknown` in the
history schema means "not tested this iteration; carry over previous status".
**We chose:** carried J-04 as `passing` rather than dropping it to `unknown`, but deliberately did NOT
advance its `last_verified_iter` (left at iter-15) and did not re-stamp its `spec_hash` — so the record
shows plainly that this iteration produced no evidence for it. Basis: iter-13's identical, human-ratified
precedent; a live end-to-end pass at iter-14; and the audit's own `git status` confirmation that
`main.py`, `app/api/health.py`, `app/engine/readiness.py`, `app/engine/warmup.py` and `scripts/` are
untouched (the spec's OUT OF SCOPE binds them). The call is not verdict-determinative (three journeys are
`partial`, so GOAL_ACHIEVED was never on the table), and my next-step makes a live J-04 replay a hard
precondition for any future GOAL_ACHIEVED. A human who requires fresh evidence for every
required-still-passing journey every iteration would score J-04 `unknown` today.
**Reversible:** yes

## iter-17 — goal-evaluator

**Ambiguity:** The DoD names TC-8 (a LIVE browser capture of the cross-`asof_key` refreshing case, where
the served `evidence_asof` is OLDER than the requested date) as a required bullet, and its
document-and-defer escape is worded for TC-9 only, not TC-8. But that live state is unproducible on the
committed seed: MAX(daily_prices.date) == MAX(scanner_runs.asof_date) == 2026-07-22 (auditor-verified
read-only), so no ingest can advance the asof_key without fabricating price data (AG-9/AG-5-barred; an
owner-owned data-cycle action). The auditor explicitly routed to the evaluator whether resolver-level unit
tests plus the audit's client-side cross-boundary render are a sufficient evidence floor for the B1 fix.
**We chose:** ACCEPTED that floor for B1's CODE CORRECTNESS — 15 unit tests (incl. TC-1 cross-boundary,
TC-4 tie-break, TC-5 strictly-older SQL, TC-6 historical carve-out) + the auditor's Playwright client-side
render of the exact cross-boundary payload (AUDIT-A1, banner + "≤older-date" window label + n_runs all
bound to the older served as-of) + the same-key refreshing live banner (TC-07). Therefore TC-8's missing
live capture is NOT treated as a standalone blocker, and the next iteration should NOT keep chasing it.
J-08 nonetheless stays `partial` — held by the SEPARATE, un-remediated ≤1.5s serving-budget breaches (step
2), not by TC-8 — so this call is not verdict-determinative this iteration; it governs what the next
iteration targets. A human who requires a genuine end-to-end live cross-boundary capture before crediting
B1 would keep J-08 partial specifically on TC-8 and route it to an owner data-cycle action.
**Reversible:** yes

## iter-18 — goal-evaluator

**Ambiguity:** J-04 is in the Required-still-passing set but has no golden script, so it rides the LLM
browser-qa lane — which SKIPPED it this iteration because Chrome MCP is wedged (port 9224 never ready). There
is NO `browser-infra.json` token, so the methodology's REL-14 `pending_infra` carve-out (score `partial`,
set `pending_infra: true`) does not mechanically fire; the dispatch/pump note nonetheless said "treat per your
pending-infra methodology." The screenshot rail ("no fresh screenshot → no fresh pass") and the
stable-journey carry-over rule (unchanged surface carries prior status) point in opposite directions.
**We chose:** carried J-04 `passing` (last_verified deliberately LEFT at iter-15), NOT `partial`+pending_infra
and NOT `unknown`. Basis: J-04's entire code surface (main.py, health.py, readiness.py, warmup.py) is
coherence-confirmed OUT of this iteration's 5-file backend diff; a live end-to-end pass exists at iter-14;
this is the identical, human-ratified carry-over iter-16 and iter-17 made; and it is NOT verdict-determinative
(J-06/J-07/J-08 partial keep GOAL_ACHIEVED off the table regardless). A fresh live DISRUPTIVE kill/restart
replay remains a HARD precondition for any future GOAL_ACHIEVED, flagged in the next-step. A human who
requires fresh browser evidence for every required-still-passing journey every iteration — or who reads the
"treat per pending-infra" note as mandating `partial`+pending_infra even without the token — would score J-04
`partial` this iteration instead.
**Reversible:** yes

## iter-19 — goal-evaluator

**Ambiguity:** J-08's title + step 2 read broadly — "Backtest evidence serves from storage only — never a cold recompute on request", "never a skeleton waiting on a fresh compute". The iter-16 decomposer (assumptions.md, human-un-vetoed) scoped the "never compute on request" guarantee to `is_latest == true` requests, keeping the historical (`is_latest == false`) path's existing lazy create-once-and-cache behavior as a documented sibling-cache carve-out. UT-04's 9.6-54s `ensure_loop_ms` stall is on exactly that historical (2025-05-30, is_latest==false) path — so under the iter-16 scoping the COMPUTE itself is arguably sanctioned (the goal's own "Cannot be precomputed (user-parameterized)" list allows a create-once cold arbitrary as_of snapshot).
**We chose:** kept J-08 `partial` rather than score it `passing` on the is_latest carve-out. Basis: even if the historical cold compute is sanctioned, the honest-status clause shared across J-06/J-07/J-08 ("never a frozen or blank frame") is independently failed by a 9.6-54s empty skeleton with NO loading affordance; and this session's human-ratified precedent (iter-12/15/16) does not launder a latency/UX shortfall into a green check. Not verdict-determinative (J-06/J-07 partial keep GOAL_ACHIEVED off the table regardless), but it governs J-08's status and the next-iteration target. A human who reads J-08 strictly through the iter-16 is_latest scoping AND treats the missing affordance as an out-of-J-08 concern (a J-06 page-budget item the spec's OUT OF SCOPE excludes) could score J-08 `passing` today, with the ensure_loop_ms stall tracked solely under J-06.
**Reversible:** yes
