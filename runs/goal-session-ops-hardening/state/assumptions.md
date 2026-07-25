# Goal Session ops-hardening — Assumption Ledger

Append-only. Each entry logs a spec decision that required interpreting an ambiguity in
`docs/goal.md` rather than a routine scoping pick. Zero entries for most iterations is normal.

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

## iter-20 — goal-decomposer

**Ambiguity:** goal.md J-08's title/step-2 ("never a cold recompute on request", "never a skeleton waiting
on a fresh compute") reads unqualified, but the iter-16 decomposer's own logged assumption scoped the
"never compute on request" guarantee to `is_latest == true` only, leaving the historical (`is_latest ==
false`) view's pre-existing lazy create-once-and-cache behavior EXPLICITLY unchanged — matching every
sibling ingest-time cache's own "cannot be precomputed (user-parameterized)" carve-out in goal.md's
Improvement direction. UT-04 (iter-19 browser-QA) now shows that carve-out, as currently implemented (a
SYNCHRONOUS compute on the request thread, codified by
`test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior` and its iter-17 sibling), can block
a historical first-view for 9.6-54s behind an empty, no-affordance skeleton. goal.md does not say whether
the historical carve-out may still block the very request that triggers it, or whether "never a request-path
recompute" implicitly forbids that too.
**We chose:** kept the carve-out's SUBSTANCE — historical evidence stays lazily create-once-and-cached,
triggered by a view, never precomputed at ingest for the full historical date range (rejected as unbounded,
see the iter-20 spec BACKGROUND) — but require the compute to run OFF the requesting thread (a background
dispatch, single-flight-guarded so at most one runs per `(asof_key, dataset_version)`), so the triggering
request itself never blocks past the committed budget. This synthesizes goal.md's literal "never a skeleton
waiting on a fresh compute" with the sibling-cache lazy-create-once precedent, rather than either removing
historical lazy compute entirely (a real time-machine capability regression no journey step asks for) or
precomputing every historical date at ingest (unbounded, rejected). This changes the two existing tests that
codified same-call synchronous completion (TC-13 and its iter-17 regression-guard sibling); the iter-20 spec
requires them updated to assert the new contract, not weakened or deleted. A human who reads the sibling-cache
carve-out as also licensing the historical view to block its own triggering request indefinitely would treat
the current 9.6-54s stall as within contract (only the missing loading affordance would need fixing) and
might reject this iteration's serving-path change as broader than required.
**Reversible:** yes

## iter-20 — goal-evaluator

**Ambiguity:** The transient in-process contention during the ~30s background compute (3.0-6.3s `/backtest`, 1.60s `/api/health`, 4/16 samples over budget) LITERALLY breaches J-06 step-2 ("assert every measurement within budget") and J-07 step-2 ("every poll within its existing budget"). But J-07's TITLE promise ("never take the service DOWN") is met (no wedge, 16/16 readiness ready), and goal.md never says whether ≤1.5s / ≤0.1s govern reads taken DURING a heavy background-compute window or only steady-state reads.
**We chose:** kept J-06/J-07 `partial` — treated the transient spikes as real recorded budget breaches, NOT laundered into a pass (iter-12/15/16 human-ratified precedent), AND treated their resolution as OWNER-owned (the only in-scope fix is a budget-acceptance decision; off-process/precompute are spec-rejected), which drives STALLED rather than CONTINUE. A human who reads J-07's step-2 clause as satisfied-in-spirit (service stayed up, just slower) and ≤1.5s as governing steady-state (non-background-window) reads could instead score J-07 (and, reading J-06's budget the same way, J-06) `passing` today — leaving only J-08's owner-gated TC-13 and J-04's owner-gated TC-14 as GOAL_ACHIEVED blockers (still a halt, but with 6 passing / 1 partial). Not verdict-determinative between STALLED variants (both halt owner-side), but it governs the recorded journey statuses and what "accept the budget" would unlock next.
**Reversible:** yes

## iter-21 — goal-evaluator

**Ambiguity:** The methodology's screenshot rail says the image must show the acceptance state and "outranks
every prose claim," but J-08's acceptance state (the `refreshing` banner + the post-warm `ready` evidence
panel) renders BELOW the fold of this iteration's viewport captures, so none of the four UT-J-08 screenshots
depicts it — and two are byte-identical to each other and to captures filed under iter-17 and iter-20.
**We chose:** scored J-08 `passing` anyway, on evidence I re-derived myself rather than on the narrative: the
`dataset_version` stamp bumped at 01:58:01.125359Z, the first new `forward_aggregate_cache` row landed
01:59:26.747706Z, and the "refreshing" capture is stamped 01:59:21.06Z — inside that gap, so serving the prior
COMPLETE version is structurally forced; the post-warm `evidence_generated_at` matches the stored row to the
microsecond; TC-13's 4096 samples (re-tallied) carry the budget clause; and the banner's RENDERING is carried
from iter-20's `UT-05-refreshing-banner.png` on a byte-unchanged build (zero product diff). Not
verdict-determinative — J-06/J-07 keep GOAL_ACHIEVED off the table either way. A human who requires this
iteration's own capture to depict the state would keep J-08 `partial` pending a full-page re-capture.
**Reversible:** yes

## iter-21 — goal-evaluator

**Ambiguity:** J-04 is in the Required-still-passing set with no golden script, so it rides the LLM lane —
which SKIPPED it for the sixth iteration running (disruptive kill/restart, scope-gated OUT by the iter-21
spec). But TC-14, the very replay iter-20 demanded as a "hard GOAL_ACHIEVED precondition," was delivered by
the operator this iteration. goal.md does not say whether operator API/DB evidence substitutes for a browser
capture on a UI-presentation journey.
**We chose:** kept J-04 `passing` and ADVANCED `last_verified_iter` from iter-15 to iter-21 (the first advance
in six iterations), after independently re-reading `data_provider_runs` id 164 from the DB (`status:
interrupted`, `dates_done 1366/2904`, `finished_at` stamped) rather than accepting the operator's prose. The
record and eval.md both state plainly that this is API/DB evidence, and that J-04's UI-presentation steps
(3 crashed-state banner, 4 logfile inspection, 6 run-history rendering) still rest on the iter-14/15 live
captures over a byte-unchanged surface. A human who requires fresh browser evidence for every
required-still-passing journey would leave `last_verified` at iter-15, or score J-04 `unknown`.
**Reversible:** yes

## iter-22 — goal-evaluator

**Ambiguity:** `docs/goal.md` J-06's Acceptance declares that budgets live only in `reports/perf-budgets.md`,
but says nothing about when that file may be amended. The owner's BCW amendment (ceilings 8.0 s / 2.0 s) predates
this iteration, yet its window-duration bound was raised 60 s -> 90 s ("Revision 1", same day) AFTER this
iteration's fresh measurement recorded a 68.79 s window and the developer honestly reported it as a breach — the
shape of goalpost-moving. Under the un-amended steady-state budget, 4 of the 29 samples breach <=1.5 s, so
J-06/J-07 pass only if the amended table (including Revision 1) is the binding contract.
**We chose:** treated the amendment INCLUDING Revision 1 as the owner's committed contract and scored J-06/J-07
`passing`. Basis checked on the merits, not asserted: the revision's diff touches ONLY the window-duration bound
(three occurrences) plus its own dated narrative — no ceiling, no steady-state budget, no ingest-overlay carve-out,
and no "what does NOT relax" clause was weakened; the superseded number is preserved as dated history; and the
structural rationale is independently corroborated by a SECOND, differently-triggered BCW the same day whose DB
commit timestamps show the same ~14 s/horizon cadence and a ~69.8 s window, confirming that iter-20's "~30 s"
figure behind the original 60 s bound was unrepresentative. iter-21's own next-step named this exact act
("accept-and-log a dated perf-budgets.md amendment") as the owner's to make. A human who treats any
post-measurement bound revision as illegitimate would keep J-06/J-07 `partial` and require the owner to
re-confirm 90 s knowing that BOTH windows measured that day exceed 60 s.
**Reversible:** yes

## iter-22 — goal-evaluator

**Ambiguity:** AG-8 forbids "exhaust[ing] a service's memory", and J-06 step 2 says "assert EVERY measurement is
within budget". The developer's accidental 5-concurrent-BCW probe (a reachable UI pattern: viewing 5 uncomputed
historical as-of dates) drove `VmPeak` to 32 kB under the `ulimit -v` cap, produced a real `MemoryError`
(`logs/backend.log:76796-76808`), and recorded `/backtest` reads up to 10.096 s — above the 8.0 s BCW ceiling.
goal.md does not say whether a multi-BCW scenario is inside any journey's scope, and the owner's amendment says
it covers "exactly one BCW".
**We chose:** scored those samples as OUT of contract rather than as a J-06 budget breach, and scored the
`MemoryError` as NOT an AG-8 violation — because AG-8 targets data-basis widening plus unbounded whole-table
loads with a crash/wedge outcome, the failure here was contained and honest exactly as AG-8's own degradation
clause and J-07 step 4's isolation convention require (non-fatal logged abort, 32/32 polls HTTP 200 with truthful
readiness over 179 s, no blank error page, no wedge, no restart requirement), zero product code changed this
iteration, and the owner had already reviewed this episode and chose to backlog it (card B-1107). The finding is
recorded prominently in eval.md's Halt Justification instead of being buried. A human who reads AG-8's "exhaust
a service's memory" literally would score this a critical anti-goal violation, veto GOAL_ACHIEVED, and promote
B-1107 into a blocking iteration (a bounded fix: a global dispatch semaphore).
**Reversible:** yes
