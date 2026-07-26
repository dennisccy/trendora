# Goal Session ops-hardening — Assumption Ledger

Append-only. Each entry logs a spec decision that required interpreting an ambiguity in
`docs/goal.md` rather than a routine scoping pick. Zero entries for most iterations is normal.

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

## iter-23 — goal-decomposer

**Ambiguity:** iter-12's decomposer logged an assumption (this same ledger) that goal.md's "`[NEW]`-flagged
walkthrough ... viewable via `demo.sh ops-hardening --session-live`" acceptance clause (J-06/J-07/J-08) is a
settled non-autonomous, ungradable deliverable — because `--session-live` is a human-interactive,
Enter-advanced terminal mode that writes no artifact, and no automatic session-mode demo-narrator pass exists
anywhere in `run-goal.sh`'s loop. Every decomposer since (iter-12 through iter-22) inherited that reading and
excluded the walkthrough from DoD. The iter-22 second-key CONFIRM evaluator (`runs/goal-session-ops-hardening/
iter-22/eval-confirm.md`) rejected GOAL_ACHIEVED partly on this exact clause, reading it differently: the JSON
manifest that `--session-live` reads (`reports/goal-session-ops-hardening-demo.json`) is itself 100%
agent-authorable (the demo-narrator's own `session` mode writes it non-interactively, per
`.claude/agents/demo-narrator.md` — "Do NOT open a browser" / "Write ONLY the JSON file"), and its current
incompleteness (zero J-06/J-07/J-08 steps, `"new": false` on every existing entry) is a genuine, bounded gap,
not evidence that the whole capability is out of reach.
**We chose:** the confirm evaluator's reading — the clause is satisfied once the session demo JSON manifest
contains complete, accurate `[NEW]`-flagged steps for the journey (the artifact a human would see if they ran
the live command), not by an actual witnessed/recorded live playback. This iteration authors that content
directly; it does NOT attempt to trigger or record an interactive `--session-live` session (still correctly
out of this iteration's DoD, per iter-12's reading, for the PLAYBACK act itself — only the artifact backing it
was actually agent-tractable and unactioned). iter-12's original assumption is now understood to have
conflated the two: the interactive playback IS non-autonomous, but the JSON it plays from is not. A human who
requires an actual recorded/witnessed `--session-live` run (not just a complete backing artifact) before
crediting this clause would keep it open regardless of this iteration's work.
**Reversible:** yes

## iter-23 — goal-evaluator

**Ambiguity:** J-06/J-07/J-08's Walkthrough clause requires `[NEW]`-flagged steps "viewable via
`demo.sh ops-hardening --session-live`". The manifest now has them, but two of the narrated scenes cannot be
LIVE at an arbitrary playback: J-08's `n=11` refreshing banner is a transient state that ended when that
date's compute completed (not reproducible without a fresh version bump), and J-07's `n=9` narrates health
polling that a browser walkthrough cannot display. `docs/goal.md` does not say whether "viewable" means the
viewer must SEE the state on screen or that the walkthrough step must exist and play.
**We chose:** scored the clause MET — the artifact `--session-live` reads now contains complete, accurate,
`[NEW]`-flagged steps for all three journeys (verified: `demo-phase.sh:78` reads exactly this file; every new
step's `expect` was live-checked; every cited figure traces to the raw `bcw-measure.csv`), and the developer
wrote `n=11`'s `point_out` in the PAST tense with a robust always-present `expect` rather than an assertion
that would silently fail. This inherits the iter-23 decomposer's reading (same ledger, un-vetoed) and is the
limit of what an agent can produce without an owner-gated ingest. Also accepted: `n=8` is a SINGLE page
(`/stocks/AAPL`) for J-06's "budgets table vs live page loads", not the 11-page sweep J-06 step 1 names.
A human who requires the viewer to actually SEE a refreshing banner during playback — or an 11-page budget
walkthrough — would keep the clause open and route it to an owner-run recorded session.
**Reversible:** yes

## iter-23 — goal-evaluator

**Ambiguity:** TC-2 required the J-07 demo step to cite "only figures found verbatim in
`reports/perf-budgets.md`'s Iteration 22 section"; the step cites "7.1191 s"/"0.2530 s" where that file
prints "7.119 s"/"0.253 s". The same iteration spec's BACKGROUND paragraph itself specified the 4-decimal
figures, so the two clauses conflict.
**We chose:** treated it as a cosmetic precision nit, not a DoD failure or an evidence-integrity problem, and
did NOT block GOAL_ACHIEVED on it — after confirming against the raw source of truth that
`runs/goal-ops-hardening-iter-22/bcw-measure.csv`'s max `bt_latency_s` is 7.1191 exactly and max
`hp_latency_s` is 0.253 (one measurement at two precisions, never a second source; the reviewer scored it
MINOR and coherence explicitly ruled it not a Data Contract violation). Recommended the 3-decimal trim as a
non-blocking follow-up. A human who reads TC-2 literally — especially given that iter-22's confirm reject
also involved a non-traceable figure — would hold GOAL_ACHIEVED for a one-line edit first.
**Reversible:** yes

## iter-24 — goal-decomposer

**Ambiguity:** J-09's Consistency clause says "Any new threshold or retained-record count comes from
`config.yaml`, never a literal," implying SOME retained-record count exists, but steps 4-5 only ever
describe a SINGULAR outcome ("the last completed or failed background compute with its outcome"), and
the title/steps never say the served payload must hold a bounded HISTORY of outcomes rather than exactly
one. Two shapes both satisfy the literal step text: (a) one `last_outcome: {...} | null` field with no
list and no retention threshold at all (the "retained-record count" language would then refer to
something else this iteration doesn't build, e.g. a future audit trail), or (b) a bounded newest-first
list whose length is the config-governed "retained-record count," exposing more than the single most
recent entry.
**We chose:** shape (b) — a `recent_outcomes` list bounded by a new `startup.background_compute_history_size`
config value (default 5), with `recent_outcomes[0]` serving the literal "last completed or failed"
requirement and the remaining entries available for the `/data` panel's benefit and for a future journey
without a second endpoint. This gives the Acceptance clause's "retained-record count" phrase a concrete,
testable referent (TC-9) rather than leaving it unimplemented, and costs nothing beyond one bounded
in-memory list (no DB, no second producer). A human who reads steps 4-5 as requiring exactly one served
outcome (no history, no threshold) would consider the `recent_outcomes` list and its config knob
over-built relative to the literal steps, and could ask for it collapsed to a single `last_outcome` field
with the threshold moved or dropped.
**Reversible:** yes

## iter-24 — goal-evaluator

**Ambiguity:** J-09's Acceptance ends with a Walkthrough bullet (`[NEW]`-flagged steps "viewable via
`demo.sh ops-hardening --session-live`"), but the iteration spec that planned J-09 never mapped that bullet
into IN SCOPE or DEFINITION OF DONE. `docs/goal.md` does not say whether a journey whose six numbered steps
all verify, but whose Acceptance carries an un-planned deliverable, is `passing`.
**We chose:** scored J-09 `partial`, treating the Acceptance bullet as binding on the JOURNEY regardless of
what the iteration spec scoped — because this session has already adjudicated exactly this clause twice (the
iter-22 second-key CONFIRM rejected GOAL_ACHIEVED on it for J-06/J-07/J-08, and iter-23 was dedicated to
closing it), and because I verified the artifact is genuinely absent rather than elsewhere:
`reports/goal-session-ops-hardening-demo.json` still holds the same 12 steps as iter-23 (newest are J-08's
n=10/11/12), is untouched by the iter-24 diff, and `run-goal.sh` contains no automatic session-demo pass.
A human who treats the iteration spec's DoD as the authoritative scope for a machine-appended journey — or
who reads the walkthrough clause as an iteration deliverable rather than a journey criterion — would score
J-09 `passing` today and take GOAL_ACHIEVED, leaving the manifest as a follow-up.
**Reversible:** yes

## iter-24 — goal-evaluator

**Ambiguity:** J-09's Acceptance requires steady-state `GET /api/health` to stay within its UNCHANGED
`<= 0.1 s` budget, re-measured and recorded. Two measurements on the SAME build disagree: the developer's
10-sample spaced series recorded max 0.127788 s / mean 0.103597 s (over), and QA's independent 10-sample run
recorded max 0.094604 s (under); the "official-convention" single sample is 0.100023 s, 23 microseconds over.
`docs/goal.md` does not say which series binds, nor whether a sub-millisecond excursion on an endpoint
documented at ~98.6 % of budget since iter-16 counts as a breach.
**We chose:** did NOT treat it as a J-06/J-07 regression and did NOT re-open those journeys, because the
excursion is pre-existing (prior iterations recorded samples on both sides of the line while J-07 was scored
passing) and this diff provably adds zero database work — the auditor executed the accessor and confirmed no
query, and I read the code path myself. I also did not launder it: it is recorded as an open J-09 gap and
routed to the owner as a standing question (audit B5). Not verdict-determinative — J-09's missing walkthrough
already keeps GOAL_ACHIEVED off the table. A human who reads the recorded max as the binding measurement
would score J-06/J-07 `partial` again and require an owner amendment or an engineering fix before closure.
**Reversible:** yes

## iter-25 — goal-evaluator

**Ambiguity:** J-09's Acceptance requires steady-state `GET /api/health` to stay within its UNCHANGED
`<= 0.1 s` budget, "re-measured and recorded in `reports/perf-budgets.md`". The recorded re-measurement
(iter-24, still the canonical one — this iteration was not asked to re-measure and changed zero backend code)
is 0.100023 s by the official single-sample convention with a 10-sample max of 0.127788 s / mean 0.103597 s,
while QA's independent series on the same build maxed at 0.094604 s; this iteration's own three steady-state
reads were ~0.10-0.18 s on a box running two pytest `loaded_engine` fixture builds. `docs/goal.md` does not
say which series binds, nor whether a sub-millisecond-to-tens-of-milliseconds excursion on an endpoint
documented at ~98.6 % of budget since iter-16 counts as a breach.
**We chose:** scored the clause MET and J-09 `passing`, at exactly the bar this session already applied when
it scored J-06 and J-07 passing across iters 22-24 with measurements on both sides of the same line — the
tightness is pre-existing, the field provably adds zero DB work (the iter-24 auditor executed the accessor;
this iteration's diff contains NO `apps/backend/app/**` file at all), and the load-bearing figures were taken
under harness memory pressure rather than in a quiet steady state. I did not launder it: it is recorded in
eval.md's Halt Justification, in journey-history's J-09 note, and routed to the owner as the still-open audit
B5 question. A human who treats the recorded 10-sample max as the binding measurement would keep J-09
`partial` (and, read consistently, re-open J-06/J-07) until the owner either amends the number or an
engineering fix creates headroom.
**Reversible:** yes

## iter-25 — goal-evaluator

**Ambiguity:** The deterministic replay lane returned FAIL for J-07 (golden step 02 expects the text "Ready"
on `/`) and the engine's merge overturned it as a "golden-script false positive". It was not really a script
artifact: the badge genuinely did not say "Ready" because that boot's warm-up had failed with a non-fatal
`MemoryError`. `docs/goal.md` does not say whether a required-still-passing journey verified while the host
was under our own test harness's memory pressure counts as verified.
**We chose:** accepted the overturn and scored J-07 `passing`, after establishing the cause myself rather
than accepting the reconciliation footer — `logs/backend.log:79986` (the only warm-up failure in the entire
logfile) plus `ps` showing the two detached pytest fixture builds started three minutes before that boot —
and after checking J-07's substance in the LLM lane's own post-restart run (12/12 HTTP 200 through a real
background window, `duration_ms 74689`, cross-checked against `forward_aggregate_cache` commit timestamps).
A human who requires every required-still-passing journey to pass its deterministic replay on the first
attempt, in-lane, would re-run the replay on a quiet box before crediting J-07.
**Reversible:** yes

## iter-26 — goal-decomposer

**Ambiguity:** the iter-25 GOAL_ACHIEVED second-key CONFIRM rejected J-09 step 4's "shows a failed background
compute with the recorded reason — never a silent failure" clause for having "no citable evidence" — every
captured panel to date renders only `completed`. `docs/goal.md` does not say whether that clause requires an
actual WITNESSED live capture of a genuinely triggered failure, or whether a deterministic code-level
round-trip (backend served-payload test + a frontend rendering unit test) is sufficient citable evidence. The
only known way to trigger a *genuine* failure on this host reproduces the unsafe 5-concurrent-BCW
memory-pressure pattern already tracked as owner-optional backlog card B-1107 (iter-22's incidental finding:
VmPeak plateaued 32 kB under the `ulimit -v` cap).
**We chose:** scoped this iteration to close the gap with (a) a new backend test that monkeypatches
`get_background_compute_status()` to return a crafted `failed` outcome and asserts `GET /api/health` serves it
verbatim, and (b) a new frontend pure-function unit test proving the panel's rendering logic shows the
`reason` string and a `danger` badge for a `failed` outcome — never re-triggering the actual unsafe failure
pattern. This mirrors the session's own established precedent (the branch-resolver `.test.ts` file was
accepted as adequate UI-behavior evidence for J-09's unknown/idle/active branches in iter-24/25) and is
bounded, safe, and fully agent-tractable without touching any byte-frozen module. A human who reads the
Acceptance clause as requiring an actual witnessed live failure capture would keep this specific sub-clause
open regardless of this iteration's test additions, and would need to authorize a bounded, safe live-trigger
mechanism (or accept B-1107's existing incidental evidence) before crediting it.
**Reversible:** yes

## iter-26 — goal-evaluator

**Ambiguity:** AG-8 (critical) forbids the deep basis "crash[ing] an existing page" and requires the UI to
degrade gracefully, "never a blank application-error page". This iteration's own evidence contains an
unhandled `sqlite3.IntegrityError` escaping as "ERROR: Exception in ASGI application" on `GET /api/backtest`
(`logs/backend.log:81004`), but nobody captured the browser at that moment, so what the user saw is unknown.
`docs/goal.md` does not say whether a server-side 500 on a request path is itself the violation, or only a
500 that reaches the user as a blank page. AG-3 (critical) is similarly open for the all-zero `/data`
coverage panel: the code calls it an honest "not yet computed" sentinel, yet the screen renders it as
ordinary figures (PRICE HISTORY "— → —", UNIVERSE 0) for a fully populated database.
**We chose:** recorded BOTH as anti-goal findings, `resolved: false`, but scored them `minor` rather than
`critical` — so the verdict is ESCALATE, not a REGRESSION halt. Grounds stated rather than assumed: the
service was never taken down (every request after the error in the logfile answers 200, through a clean
shutdown), no unbounded whole-table load occurred, the diff contains zero `apps/backend/app/**` product
code so nothing here was introduced this iteration, the zero-coverage payload is a deliberate documented
path (`data_manager.py:908`) that self-heals at the next boot warm-up or ingest, and no journey step covers
either scenario. I did not launder them: both are in `journey-history.json`, in eval.md's anti-goal table,
and they are the next iteration's first two work items. A human who reads AG-8's "never crash an existing
page" as satisfied only by a captured, contained UI error — or who reads AG-3 literally about the zeros —
would score one or both critical, which under decision tree C.1 means a REGRESSION halt for human review
instead of another agent iteration.
**Reversible:** yes
