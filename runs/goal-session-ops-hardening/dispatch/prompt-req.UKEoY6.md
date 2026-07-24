You are the goal-decomposer agent for goal-mode iteration planning.

Mode: next
Session ID: ops-hardening
Iteration index: 18
Iter name: goal-ops-hardening-iter-18
Prior verdict: CONTINUE
Prior depth: full
Consecutive lean iterations dispatched: 0 (hardening cadence: 4; 0 = disabled)

Project template: .claude/project-template.md
Project goal (SLICED — vision + anti-goals + failing/target journeys verbatim; stable passing journeys digested to one line): /home/dennis-chan/Git/trendora/runs/goal-session-ops-hardening/iter-18/goal-slice.md
  Full goal file: /home/dennis-chan/Git/trendora/docs/goal.md — Read it ONLY if a digested journey becomes relevant to your plan.
Agent instructions: .claude/agents/goal-decomposer.md  <-- read this first
(CLAUDE.md is already in your system prompt — do not Read it again.)

Recent evaluator log entries (last 3, pre-trimmed):
```
`demo.sh --session-live` walkthrough (owner) is unproduced and UT-04 (P1 FAIL, opened by me: `/backtest`
cache-MISS 211.8s under a concurrent warm; honest/non-catastrophic, page rendered, NOT an AG-8 crash) leaves
J-07's serve-responsiveness edge open. Rejected STALLED: UT-04 root-cause is concrete, cross-cutting,
agent-tractable work. Rejected ESCALATE: full depth already, all gates PASS/PASS_WITH_NOTES/PASS_WITH_GAPS,
no fail-open, no journey failing twice. Coherence PASS → CONTINUE.

**Next-step recommendation:** FULL depth, focused follow-up, no new features. (1) AGENT (the item between
J-07 and passing): root-cause UT-04's 211.8s concurrent-warm `/backtest` contention (audit F1 hypothesis: a
streamed cursor holds a longer read-lock window under concurrent writes than the old fetch-and-release
`.all()`) — the exact iter-13 trigger shape neither TC-4 (concurrent-on-fixture) nor TC-5
(sequential-on-deep-basis) reproduces; spot-check `/stocks`/`/sectors`/`/scanner-runs`/`/evidence` under a
concurrent warm; consider an elapsed-time affordance on the `/backtest` skeleton. (2) OWNER DECISIONS (each
independently blocks GOAL_ACHIEVED, do not let an agent invent them): the `[NEW] demo.sh --session-live`
walkthrough J-05/J-06/J-07 name (no autonomous mechanism, iter-12 finding); whether TC-3's real
synthetic-subprocess induction + TC-5's organic absence suffice for TC-6 or an operator-authorized
live-process induction is still owed (AG-10 hazard on this crash-history host). (3) AGENT non-blocking: UT-10
(P3) per-horizon heartbeat cadence (`data_manager.py:3220`, outpaced ~9×); reconcile the stale "not done
yet" line in `implementation-summary.md` (audit B2 / closure Non-Blocking #1). Carried: pre-existing
`test_db.py::test_create_all_produces_expected_tables` failure (unrelated, no schema change).

## Iteration 15 — goal-ops-hardening-iter-15

**Date:** 2026-07-23T18:00:00Z
**Verdict:** STALLED
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: none (J-01/J-03/J-05 re-verified passing by deterministic golden replay; J-04
  re-verified passing by the LLM lane + carry-forward of iter-14's live kill/restart pass + this
  session's fresh steady-state sanity re-check, `UT-J-04-carryforward-sanity.png` opened)
- Advanced but NOT closed: **J-06 & J-07 stay `partial`** — the ONE agent-tractable item iter-14 named
  (root-cause + fix UT-04's 211.8s concurrent cache-MISS) is DONE and correct, but the live pass proves
  it does not close the budget.
- Newly failing: none. Regressed (passing→failing): none.
- Anti-goal violations: **NONE this iteration.** scan-report CLEAN; iter-diff = `forward_testing.py`
  (single-flight wrapper only) + `test_forward_testing_concurrency.py` + a README showcase leftover;
  coherence COHERENCE-PASS. AG-8 (iter-9/13 dimension) STAYS RESOLVED — `compute_forward_aggregates`
  byte-unchanged, no unbounded ORM/OOM/crash; the 178.74s is latency, not exhaustion. AG-10 honored
  (operator pass via `start-backend.sh`, taskset confirmed live on pid 4166118, 84°C < 95°C trip).

**Reasoning:** The single-flight de-dup is a correct, byte-identity-preserving fix (root cause measured
not guessed: 9.91x→1.04x on a 60k fixture; TC-1 call-count==1; I confirmed the diff touches only the
wrapper + `import threading` + 3 module globals, `compute_forward_aggregates` body untouched). But the
one operator-supervised deep-basis pass (`reports/perf-budgets.md` TC-4, which I cross-read line by line)
shows the live cold MISS is still **178.74s WARN (~119x over the ≤1.5s budget)** plus an unflagged
**5.37s** second breach — because the dominant residual is ONE cold full-basis compute a wrapper-scoped
fix cannot reduce (audit B1/B2 reconciled the dev's "stacking fully accounts for 211.8s" overclaim to
~15.6%). I opened `UT-01-result.png`: `/backtest` renders fully and honestly (Ready, all 5 horizons
"— n=0", "No numbers are fabricated") — so the honest-status clause holds and this is a latency/budget
shortfall, NOT an AG-8 crash. Rejected REGRESSION: no journey passing→failing; AG-8 resolved and the fix
introduces no new violation. Rejected GOAL_ACHIEVED: J-06/J-07 partial (budget clause fails). Rejected
CONTINUE: the tractable "fix the bug" work is exhausted — the residual is definitively a hard cost, and
every remaining path (affordance / precompute-before-serve redesign / accept-and-amend-budget) is a
human-owned product-direction decision the spec's own escalation flag, the pump note, audit §5, and QA #3
all route to the owner. Decision tree C.2 matches: all unblock paths for the current blocker are
human-owned → STALLED. I declined to unilaterally adopt the "warm-fast + honest-skeleton = passing"
reading (interpretation c): the goal Success Criteria commit to "page loads stay within committed
never-regress budgets", and iter-12's human-ratified precedent kept J-06 partial rather than launder a
budget breach into a green check — that acceptance is the owner's to grant.

**Next-step recommendation:** HALT. Owner picks one direction for the `/backtest` cold-MISS residual —
(1) add a `/backtest` elapsed-time/progress affordance (deferred iter-16 candidate) and read the budget
as governing warm loads only; (2) authorize a precompute-before-serve / incremental-aggregate redesign so
a request never eats a cold full-basis compute; or (3) accept the deep-basis cold-MISS as a disclosed
constraint (a conscious logged `reports/perf-budgets.md` budget amendment, never a silent loosening) — under
(3) the evaluator can score J-06/J-07 passing next iteration → GOAL_ACHIEVED. Then `--resume` at FULL depth
(shared-infrastructure change). Non-blocking owner/operator items to weigh (none closes J-06/J-07 alone):
the undiagnosed 5.37s spike (needs another AG-10 heavy pass); the 84°C-vs-64°C thermal reporting
discrepancy (host crash history); the 4 unguarded sibling caches (reuse this iteration's single-flight
idiom if ever patched); VmPeak grew +66.6% vs iter-14 (36.3% margin — under cap, WATCH). The
`demo.sh --session-live` walkthrough now has operator evidence (iter-14 walkthrough file, exit 0, 7 steps)
— no longer a distinct blocker. Carried unrelated: `test_db.py::test_create_all_produces_expected_tables`.

## Iteration 16 — goal-ops-hardening-iter-16

**Date:** 2026-07-23T23:20:00Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: none
- **New journey: J-08 (`partial`)** — the owner's precompute-before-serve journey. Core architecture
  lands and is genuinely verified; three clauses stay open (below).
- Advanced but not closed: **J-06 & J-07 stay `partial`** — the 178.74s cold-MISS residual that held
  them since iter-11 is architecturally CLOSED (request path structurally cannot compute), but J-08 is
  not `passing`, so neither is freed.
- Re-verified passing: J-01, J-03, J-05 (deterministic golden replay, 3/3 PASS, raw file agrees with the
  merged file, no reconciliation footer). **J-04 CARRIED, NOT re-verified** — UT-J-04 SKIPPED
  (kill/restart is a blocked service action); `last_verified_iter` deliberately left at iter-15.
- Newly failing: none. Regressed (passing→failing): none.
- Anti-goal violations: **NONE this iteration.** scan-report CLEAN; all 10 categories answered explicitly
  in eval.md; all 8 historical records stay `resolved: true` (0 unresolved). coherence COHERENCE-PASS.

**Reasoning:** The redesign is real and I proved the load-bearing parts myself rather than inheriting
them. I recomputed the whole 68-row `tc16-backtest-poll.csv`: 68/68 HTTP 200, exactly TWO generations ever
(never a third, never mixed), all 16 `refreshing` polls serving the PRIOR complete generation, and the
generation flip landing on the same row as the `ready` flip — the state machine holds end-to-end. I read
`forward_testing.py:1163-1242` directly (no branch can reach `compute_forward_aggregates`; the
completeness read is `asof_key`-filtered and column-projected — TC-18 confirmed in source), and opened
UT-04 to confirm the cutover is a real value change (1800/743634 → 1801/744166), not just an absent
banner. So iter-15's 178.74s blocking cold recompute is genuinely gone (worst read now 12.655s, a
stored-row read). But J-08 is `partial` on three counts I checked myself. **(a) Audit B1, confirmed in
source independent of the auditor's probe:** `backtest.py:70` resolves the default view to the latest
stored run and `:1209` scopes the lookup to that ONE `asof_key`, so the *common single-latest-date*
backfill (`data_manager.py:3172`'s own words) leaves the default `/backtest` serving `not_yet_computed`
— an empty evidence section — for the whole warm window. I RULED this must not stand: J-08 step 2
promises the last-good "labeled with that version's served as-of" (a label meaningless unless the served
as-of can differ), and step 5 reserves `not_yet_computed` for the "fresh-install shape", which this is
not. Both TC-16 and UT-02 backfilled historical gap dates, so the most common shape has zero coverage.
**(b) Latency:** 11/68 polls breach the committed ≤1.5s budget (max 12.655s) on a thermally-verified
host-guard-confined pass; the owner chose iter-15's option (2) redesign, NOT option (3) budget amendment,
so ≤1.5s binds unamended and J-06 step 2's "assert every measurement is within budget" fails. A 14x
improvement is not the same as a pass. **(c) Evidence gaps:** `not_yet_computed` has ZERO browser
evidence (UT-03 SKIPPED), and I opened UT-02 and read the FALSE banner copy on screen ("is still being
warmed", "updates automatically" — audit F1); the corrected wording IS in the tree
(`page.tsx:270-276`, verified) but has never been rendered, so J-08's honest-disclosure clause is
evidenced only in its dishonest form. Rejected REGRESSION: no journey passing→failing and no anti-goal
implicated — B1 yields a contained honest-shaped `EmptyState`, not a crash, blank error page, or wrong
number, and the pipeline's own auditor surfaced it. Rejected STALLED (iter-15's verdict): the auditor
itself scopes B1's fix as a bounded follow-up iteration, and items 1-4 of my next-step are all
agent-owned — this is emphatically not "every unblock path is human-owned". Rejected GOAL_ACHIEVED:
three journeys `partial`, J-04 without fresh evidence. Rejected ESCALATE: already full depth, no
fail-open, no journey failing twice. Coherence PASS → no consolidation mandate. Progress made → CONTINUE.

**Next-step recommendation:** FULL depth, no new features — close J-08. (1) AGENT: fix B1 — when the
requested `asof_key` has no complete version but an earlier one does, serve that earlier version as
`refreshing` LABELED WITH ITS SERVED AS-OF, reserving `not_yet_computed` for the true fresh-install
shape; add the as-of-advancing case to `test_forward_testing_serving_split.py` (currently zero coverage)
and re-word the empty state so it never tells a mid-ingest user to "run an ingest" (audit F2).
(2) AGENT: browser evidence for the two unrendered states — re-capture the CORRECTED refreshing banner
(services are up), and render `not_yet_computed` on a DISPOSABLE copy of `trendora.db`, never the working
one. (3) AGENT: root-cause the 11/68 breaches — all inside the ingest window on a stored-row read, so
writer/reader contention, not compute; check SQLite journal mode + ingest transaction span; audit B5 (the
historical branch deserializes every payload twice) is a cheap adjacent win. (4) AGENT non-blocking: B3
(`evidence_generated_at` serialized naive despite an "ISO 8601 UTC" contract — fix while the field is
young), B2 (sticky `refreshing`, no self-heal), F3 (duplicated empty-state sentence). (5) OPERATOR: a live
J-04 kill/restart replay — J-04 is carried, not re-verified, and MUST be freshly verified before any
GOAL_ACHIEVED; plus one `loaded_engine` test to close T1; plus a fresh `demo.sh --session-live` run (the
iter-14 walkthrough predates J-08 and cannot cover its `[NEW]` steps). (6) OWNER, optional: if ≤1.5s is
not meant to govern reads taken DURING a heavy ingest, that is a conscious logged `perf-budgets.md`
amendment, never a silent loosening. Framework-maintainer note: `J-01-verify.png` and `J-03-verify.png`
are BYTE-IDENTICAL (md5 `7d8f6681…`) and both show only the `/data` page-top landing frame — the replay
lane's PASS rests on its scripted DOM expects, but two of three replay screenshots are not independently
informative. Carried unrelated: `test_db.py::test_create_all_produces_expected_tables`.

## Iteration 17 — goal-ops-hardening-iter-17

**Date:** 2026-07-24T07:44:45Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: none
- Advanced (evidence, not status): **J-08 stays `partial`** — iter-16's audit-B1 gap is CLOSED in code
  (resolved_forward_aggregate_evidence crosses asof_key boundaries, strictly-older/AG-5-safe, groups by
  (asof_key,dataset_version) pair, tie-break most-recent-older-complete; new evidence_asof served
  identically by GET /api/backtest + MCP query_backtest). TWO first-ever live states captured:
  not_yet_computed (TC-09, throwaway DB 0-rows, 0 rows after 4 requests = zero request-path compute) and
  the corrected refreshing banner w/ evidence_asof (TC-07). Auditor found+fixed F1 (window labels bound to
  requested not served as-of; AUDIT-A1). 15 unit tests re-run green by reviewer+QA+auditor independently.
- Re-verified passing: J-01, J-03, J-05 (deterministic golden replay UT-J-01/03/05 PASS; spot-checked
  J-05-verify.png = immutable stored snapshot 2025-05-15). **J-04 CARRIED, NOT re-verified** — UT-J-04
  SKIPPED (kill/restart blocked + binding OUT OF SCOPE); TC-11 steady-state sanity only (health 200/ready,
  no crash banner); last_verified deliberately left at iter-15.
- Newly failing: none. Regressed (passing→failing): none.
- Anti-goal violations: **NONE unresolved.** scan-report CLEAN; coherence COHERENCE-PASS. AG-8 stays
  resolved (compute byte-unchanged; the new widened fallback query is bounded by distinct-as-of count,
  ~650KB/25 rows today, NOT the deep basis — auditor explicitly not a violation). One NEW minor+resolved
  entry logged: an operator AG-10 process lapse (raw uvicorn on throwaway :18255, disclosed + corrected via
  start-backend.sh, auditor /proc-verified capped; NO launch script modified → no code-level regression).

**Reasoning:** The load-bearing B1 fix is real and I verified it at every reachable level — 15 unit tests
(TC-1 cross-boundary, TC-4 tie-break, TC-5 strictly-older SQL, TC-6 historical carve-out) re-run green by
three independent gates; AG-3 byte-identity + AG-5 no-lookahead hold; coherence confirms one producer/one
resolver. I opened the two first-ever live captures myself (TC-09 not_yet_computed empty state with the
reworded no-"run an ingest" copy; TC-07 refreshing banner reading "evidence as of 2026-07-22" over
fully-populated numbers) and the auditor's AUDIT-A1 cross-boundary client render (banner + "≤ 2026-07-21"
window label + n_runs all bound to the older served as-of — the F1 fix). But no journey crossed to passing:
J-06/J-07/J-08 stay partial on the un-remediated ≤1.5s serving-budget breaches (11/68, max 12.655s), which
this iteration NARROWED (thermal + single-long-transaction ruled out) but did not PIN (two contention
mechanisms indistinguishable — logs/backend.log has zero per-request timestamps), and TC-10 was not
re-measured. Rejected REGRESSION: no passing→failing; no unresolved critical anti-goal; the browser-QA
OVERALL=FAIL is UT-01 only, traced to an operator dev-server build collision — I confirmed the implicated
readiness/health/preflight/data-page files are NOT in the 8-file iter-diff and /backtest renders fully in
three captures. Rejected STALLED (iter-15's verdict on this same surface): iter-15 halted because the cost
was KNOWN (cold full-basis compute) and only the product response was owner-owned; here the cost is
UNKNOWN (undiagnosed contention) and the next step — add per-request timing instrumentation, then diagnose
— is agent-owned, so not every unblock path is human-owned. Rejected GOAL_ACHIEVED: three journeys partial
+ J-04 without fresh live evidence. Rejected ESCALATE: already full, review PASS (no fail-open), no journey
failed twice. Progress made + tractable work remains → CONTINUE.

**Next-step recommendation:** FULL depth, no new features. (1) AGENT (unblocking step): add per-request
timing instrumentation to the /backtest serving path — the diagnosis is blocked ONLY by missing wall-clock
timestamps. (2) OPERATOR (AG-10-class): re-run the deep-basis 68-poll TC-10 WITH the instrumentation, to
distinguish SQLite writer/checkpoint contention vs GIL/threadpool scheduling, recorded in perf-budgets.md.
(3) AGENT-then-OWNER-fork: apply a bounded mitigation if the contention is fixable (→ J-06/J-08 pass), else
route the ≤1.5s budget-amendment to the owner (iter-15 option-3 precedent; the fork fires only AFTER the
agent diagnosis). (4) AGENT cheap wins: project metadata columns in the widened fallback query before
reading payloads (auditor B1); add one endpoint-level test carrying an OLDER evidence_asof (auditor T1).
(5) TC-8 cross-boundary LIVE capture is NOT a blocker — unproducible on this seed (MAX daily_prices.date ==
MAX scanner_runs.asof_date == 2026-07-22; advancing needs new price data, owner-owned + AG-9/AG-5-barred);
evaluator accepts the unit+client-render+same-key-live floor for B1 code correctness. (6) OPERATOR: a fresh
live J-04 kill/restart replay is still owed before any GOAL_ACHIEVED (TC-11 sanity is not a substitute).
```
Lessons learned (full file, append-only):
```

## iter-5 — 2026-07-20T22:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter whose measurement/backfill runs add rows to /scanner-runs or /api/runs; any
goal-evaluator triaging a required-still-passing deterministic-replay FAIL with no LLM-fallback adjudication.

## iter-6 — 2026-07-21T01:43:56Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter closing J-06 / touching a lazy-warmed derived cache (event_study_cache,
market_phase_cache, drawdown_expectations); any perf claim measured while a heavy pytest/ingest runs concurrently.

## iter-7 — 2026-07-21T08:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter that adds work to `_refresh_ingest_aggregates` / the ingest finalize hook, or
any "warm-a-cache-earlier" change; any iter where the audit runs before browser-qa and asserts a required
journey is orthogonal to the diff — the evaluator must still weight the live browser evidence over the
orthogonality argument.

## iter-8 — 2026-07-21T23:53:18Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any backend-only iteration whose spec names browser journeys in TESTING REQUIREMENTS or
targets a regressed journey — check `browser_checks_run` and the existence of the evidence directory before
believing any completion claim.

## iter-8 — 2026-07-21T23:53:18Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration claiming an AG-8 memory/availability regression is closed, and any perf
measurement taken after host-guard settings changed.

## iter-8 — 2026-07-21T23:53:18Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration inserting a large block into an existing test file — re-read the function
boundaries on BOTH sides of the insertion point, and treat "a long-standing test still passes" as
suspicious when the diff touched its file.

## iter-9 — 2026-07-22T19:05:00Z

**Verdict:** CONTINUE
**Lesson:** A journey can fail its browser lane and have the defect FIXED inside the same iteration, which
leaves every downstream artifact (raw `.llm.md`, merged results, regression-replay-results) frozen at the
pre-fix verdict while the newest evidence sits in an operator note nobody's lane owns. J-04 step 6 hit
exactly this: `UT-10-result.png` shows the real pre-fix "0 snapshots · 0 trading days", the F1
`_checkpoint_run_record` fix landed hours later, and the post-fix proof (run 114 frozen at 59 snapshots /
64-of-84 dates vs. the all-zero control run 113 in the same `GET /api/data` response) exists only in
`runs/goal-ops-hardening-iter-9/pump-j04-crash-recovery-evidence.md`. Neither `failing` (cites a build
that no longer exists) nor `passing` (no rendered-surface evidence) is honest — `partial` is. When a fix
lands after its own verification lane has run, the fix does not close the journey; it schedules a
re-verification.
**Applies to:** any iteration where an audit/fix round lands product code AFTER the browser-qa step, and
any evaluation weighing operator/API evidence against a stale lane verdict.

## iter-9 — 2026-07-22T19:05:00Z (second entry)

**Verdict:** CONTINUE
**Lesson:** iter-8's "the margin is comfortable" reading was doubly unsafe, and only iter-9's audit (P1)
caught why: `VmPeak` in `/proc/<pid>/status` is a kernel-maintained monotone high-water mark, so a finer
sampling cadence CANNOT raise it — re-subsampling the 4,347-row trace at 1 Hz and at 10 s yields the
identical 4,738,948 KB. The 43.6% → 24.7% margin narrowing is therefore real growth in peak demand, not a
measurement artifact, and the benign-sounding cadence explanation had to be struck from
`reports/perf-budgets.md`. Never let a plausible measurement-artifact story stand unverified next to a
number that is trending the wrong way.
**Applies to:** any iteration recording VmPeak/VmSize/RSS headroom against `server.memory_cap_mb`, and any
future J-05/AG-8 re-measurement as the price basis deepens.

## iter-10 — 2026-07-22T20:55:00Z

**Verdict:** CONTINUE
**Lesson:** A crash journey can be scored without trusting anyone's narration of the crash: the persisted run
row proves it by itself. `data_provider_runs` id 119 stopped at `dates_done 158 / dates_total 504` (mid-flight by
construction) and its `finished_at` lands 1.3 s AFTER the successor's `=== start-backend.sh: launching ... ===`
banner in `logs/backend.log`, which means the dead process wrote nothing on the way out and the new one's orphan
sweep finalized the row — with no `Shutting down`/`Finished server process [pid]` line anywhere before that
banner (the same log demonstrably records clean shutdowns for other pids). Two related traps this iteration hit:
the first crash rehearsal (run 118) missed because the job self-completed 38 s before the kill — use a range long
enough that the completion buffer exceeds poll-to-kill latency — and the run-summary identity for an INTERRUPTED
run is `snapshots_created + already_snapshotted + error_other = dates_done`, not `= dates_total` (TC-2 as written
assumes a completed run).
**Applies to:** any iteration verifying crash/restart, orphan-sweep or checkpoint behaviour; any spec writing a
run-summary arithmetic assertion that must also hold for partial runs.

## iter-11 — 2026-07-22T21:10:00Z

**Verdict:** ESCALATE
**Lesson:** A browser lane that only reads `performance.getEntriesByType('resource')` cannot tell a
15 ms success from a 15 ms **HTTP 500** — iter-11's lane called `/api/research/event-study` "already
succeeded" and blamed the page's "Backend unavailable" render on ambient host load, while
`logs/backend.log:27660` shows that exact call returning 500 (`RuntimeError: can't start new thread`
after a MemoryError). Always cross-read `logs/backend.log` for the measurement window before accepting
an "environmental, not code" explanation, and rule ambient load in/out with `logs/hwmon/hwmon.csv`
(MemAvailable was 12–20 GB — nothing ambient can consume a process's own `ulimit -v` cap).
**Applies to:** any iteration whose verdict rests on browser-measured latency or on an anomaly
explained away as host contention; also any perf sweep, since the same log read reveals whether the
product's own ingest was running during the measurement.

## iter-11 — 2026-07-22T21:10:00Z

**Verdict:** ESCALATE
**Lesson:** The developer pass writes `reports/perf-budgets.md` *before* the browser lane produces the
numbers, so in a lean pipeline a "measurement iteration" can finish with its measurements living only
in a QA evidence `.txt` and never reaching the artifact the journey's Acceptance names as the single
source (verified by mtime: file 20:24Z, sweep 20:38–20:52Z). Check the artifact's timestamp against
the lane's timestamps before scoring any "recorded in the budgets table" step.
**Applies to:** any iteration whose DoD says "record X in `reports/perf-budgets.md`" while X is
produced by browser-qa rather than by the developer.

## iter-12 — 2026-07-23T02:00:00Z

**Verdict:** CONTINUE
**Lesson:** Closing a journey's EVIDENCE gap is not the same as the journey passing — the evidence can be the
adverse finding. J-06's G1/G2 measurement work was completed correctly and in full, yet the G2 control
reading it produced (`/api/indexes?full=true` at 2.1–2.3 s vs a committed ≤1.5 s budget, on a verifiably idle
host) is exactly the shortfall that keeps J-06 out of `passing`. The audit recommended `passing` because the
work was done; the honest score is `partial` because J-06's own step-2 assertion ("every measurement within
budget") fails. Score on the contract, not on the fact that a measurement happened — and when a real number
contradicts a "may pass" prose recommendation, the number wins.
**Applies to:** any iteration whose target is "measure-and-record" work against committed budgets
(`reports/perf-budgets.md`), and any evaluator tempted to accept a downstream agent's "may be scored passing"
when the recorded measurement breaches the acceptance metric.

## iter-13 — 2026-07-23T04:39:47Z

**Verdict:** REGRESSION
**Lesson:** A carried, byte-unchanged critical anti-goal can REGRESS in observed severity without any
code change: AG-8 (`forward_testing.py:826` unbounded ScannerResult load) was "degraded-but-alive,
mitigation holds, smaller than iter-7" for iters 9/11/12 — then at iter-13, under heavier concurrent
load (4 replay backfills + a diagnostic read on one browser-qa turn), it wedged the entire backend into
a ~12-min futex deadlock needing an operator hard-restart, i.e. back to the original iter-7 full-outage
severity. The "blast-radius-smaller-than-the-acknowledged-incident" argument that justifies deferring a
critical anti-goal is only valid until a heavier load profile falsifies it; an evaluator must re-test
that premise every iteration against fresh load evidence, not carry it forward. When it flips, C.1's
literal "unresolved critical anti-goal → REGRESSION" is the right call even though prior iters deferred.
**Applies to:** any iter carrying an UNRESOLVED critical anti-goal on a "smaller blast radius than the
acknowledged incident" rationale — especially memory/availability bugs whose severity is load-dependent;
re-read logs/backend.log + the audit + closure for a worse-than-before manifestation before re-deferring.

## iter-14 — 2026-07-23T14:25:00Z

**Verdict:** CONTINUE
**Lesson:** Bounding the READS (column-projected `yield_per` streaming) closed the AG-8 memory-exhaustion/
crash dimension with a wide 61.8% margin, but the SAME rewrite surfaced a NEW concurrent-load latency: a
`/backtest` cache-MISS took 211.8s during a concurrent forward-aggregate warm (audit F1 hypothesis — a
streamed cursor holds a longer read-lock window under concurrent writes than the old fetch-and-release
`.all()` did). A memory fix and a lock-contention fix are different problems; proving the former (flat
VmPeak, health 200) does not prove the latter, and only a browser pass under the EXACT concurrent trigger
exposed it — neither TC-4 (concurrent-on-fixture, no cap) nor TC-5 (sequential-on-deep-basis) reproduces it.
**Applies to:** any iter that replaces a `.all()` fetch-and-release with a streamed/`yield_per` read on a
hot path shared by concurrent ingest writers — measure latency under concurrent load on the deep basis, not
just peak memory.

## iter-15 — 2026-07-23T18:00:00Z

**Verdict:** STALLED
**Lesson:** A small-fixture concurrency ratio does not extrapolate to a deep-basis cost. The 60k-row
fixture's 9.91x same-key stacking ratio predicted the single-flight de-dup would "fully account for" the
211.8s finding; the live deep-basis pass showed stacking was only ~15.6% and the dominant ~84% is ONE
cold full-basis `compute_forward_aggregates` pass (178.74s) a wrapper-scoped fix cannot touch. When a
targeted fix's own live evidence contradicts its root-cause extrapolation, the root-cause conclusion is
the thing to trust the LIVE number over — and the investigation *reaching* "this is a hard architectural
cost" is itself the terminal deliverable that hands the decision to the owner, not a bug to re-attempt.
**Applies to:** any iteration proposing a wrapper/cache/concurrency fix validated on a synthetic fixture
before a deep-basis pass; any "the fix fully accounts for X" claim not yet reconciled against a live
full-scale measurement; future decomposers tempted to loop CONTINUE on an owner-owned direction decision.

## iter-16 — 2026-07-23T23:20:00Z

**Verdict:** CONTINUE
**Lesson:** Removing a request-path compute silently changes what the page shows when the *identity*
moves, not just when the version moves. `resolved_forward_aggregate_evidence` resolves all three serving
states inside ONE `asof_key` (`forward_testing.py:1209`), while the default `/backtest` view resolves to
`max(ScannerRun.asof_date)` (`backtest.py:70`) — so the common single-latest-date ingest advances the
as-of into a key with no rows and the page shows an EMPTY evidence section, where the old code would have
blocked and eventually served real numbers. Neither the operator's live pass nor browser QA could catch it
because both backfilled *historical gap* dates (2025-05-22 / 2025-05-20), which leave the latest as-of
fixed — the only shape either lane ever exercised.
**Applies to:** any iteration adding a cache/precompute layer keyed on a derived identity (`asof_key`,
`dataset_version`, tenant, run id) — enumerate the ways the *identity* can move, not just the ways the
*value* can go stale, and make sure the live test exercises the identity-advancing shape, not only the
convenient one.

## iter-16 — 2026-07-23T23:22:00Z

**Verdict:** CONTINUE
**Lesson:** Four gates (review, QA, browser-QA UT-02/UT-09, ux-regression) all checked the new refreshing
banner for tone, colour token, position and heading, and all passed it — while it asserted two things that
were factually false ("a newer dataset version is still being warmed"; "this updates automatically"). No
lane's checklist contained "is the sentence true?", and the second claim is false in *every* case (the
page's only fetch effect depends on `[asOf, readiness]`, which never changes — browser QA's own UT-04
needed a manual reload). Status-disclosure copy is a testable assertion about system state, not styling.
**Applies to:** any iteration adding user-facing status/progress/explanatory copy — verify each sentence
against the code that would have to be true for it, the same way a displayed number is verified against
the engine (AG-3's discipline, applied to prose).

## iter-17 — 2026-07-24T07:44:45Z

**Verdict:** CONTINUE
**Lesson:** Do NOT STALL on a latency-budget breach until it is DIAGNOSED. iter-15 correctly STALLED
because the cost was a KNOWN cold full-basis compute and only the product-direction response was
owner-owned. iter-17's residual (11/68 stored-row-read breaches, max 12.655s) looks similar but is
categorically different: it is UNDIAGNOSED (narrowed to SQLite-writer-contention vs GIL/threadpool but
indistinguishable because `logs/backend.log` carries zero per-request timestamps). Missing instrumentation
is agent-fixable, so the unblock path is agent-owned → CONTINUE, not STALLED. The routing test is "is the
cost proven, or merely unmeasured?" — a proven hard cost routes to the owner; an unmeasured one routes to
an agent instrumentation pass first.
**Applies to:** any iter where a page/endpoint misses a committed `reports/perf-budgets.md` budget and the
mechanism is not yet pinned — check whether the diagnosis is blocked by missing telemetry (agent work)
before treating the residual as an owner budget-amendment decision.
```
Assumption ledger (append-only): /home/dennis-chan/Git/trendora/runs/goal-session-ops-hardening/state/assumptions.md  <-- when a spec decision requires interpreting an ambiguous goal, append an entry per your agent instructions; zero entries is normal. Do not read the full file — recent tail below.
Recent assumption entries (pre-trimmed):
```
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
```
Journey state (inline digest; Read /home/dennis-chan/Git/trendora/runs/goal-session-ops-hardening/state/journey-history.json only for fields the digest omits):
```
J-01 | passing         | last_passing=goal-ops-hardening-iter-17 | Backfill honors the requested range and explains zero-work
J-03 | passing         | last_passing=goal-ops-hardening-iter-17 | No per-run range cap
J-04 | passing         | last_passing=goal-ops-hardening-iter-15 | Non-blocking boot with visible status
J-05 | passing         | last_passing=goal-ops-hardening-iter-17 | Aggregates are precomputed at ingest, never on the fly
J-06 | partial         | last_passing=- | Pages load only what they need
J-07 | partial         | last_passing=- | Heavy aggregates never take the service down
J-08 | partial         | last_passing=- | Backtest evidence serves from storage only — never a cold recompute on request
```

Iteration state (single-file digest the goal-evaluator overwrote after the last iteration; inlined verbatim):
```
# Iteration State — ops-hardening

**After iteration:** 17 · **Date:** 2026-07-24 · **Verdict:** CONTINUE

## Journeys

4 passing (J-01 J-03 J-05 replayed; **J-04 CARRIED — UT-J-04 SKIPPED, not re-verified live since iter-14**) · 3 partial (J-06 J-07 J-08) — 7 total

## Active blockers

- **/backtest ≤1.5s serving-budget (dev → operator → owner): the one thing between J-06/J-07/J-08 and passing.** 11/68 breaches, max 12.655s, all in the ingest window on a stored-row read — UNDIAGNOSED (thermal + single-txn ruled out; SQLite-writer vs GIL/threadpool indistinguishable, `logs/backend.log` has zero per-request timestamps). Next: **dev** adds per-request timing instrumentation → **operator** re-runs TC-10 (AG-10-class) → bounded fix, or **owner** amends the budget (logged, never silent). `reports/perf-budgets.md` iter-17 section.
- **Fresh live J-04 kill/restart replay (operator)** — required before any GOAL_ACHIEVED; iter-17 did only TC-11 steady-state sanity (health 200/ready, no crash banner). J-04 code surface byte-unchanged.
- Non-blocking cheap wins (dev): project metadata columns before reading payloads in the widened fallback query (audit B1); one endpoint-level test carrying an OLDER `evidence_asof` (audit T1).

## Last 2 verdicts

- iter 17: CONTINUE — B1 cross-asof_key fix + 2 first-ever live states (TC-09/TC-07) landed & verified; journeys held partial by latency that is undiagnosed (agent instrumentation), NOT a proven hard cost → not STALLED.
- iter 16: CONTINUE — J-08 precompute-before-serve redesign landed `partial` on 3 agent-owned gaps.

## Do not redo

- **B1 cross-asof_key fallback** (`forward_testing.py` resolver) — DONE + correct, 15 unit tests, AG-5 strictly-older SQL-verified, AG-3 byte-identical. Never add a compute branch to the read path; never revert cutover pruning to per-horizon deletion.
- **`compute_forward_aggregates` body** — byte-unchanged since iter-14 (AG-8 resolved). Not reopened. The new widened query is bounded by distinct-as-of count, not the deep basis — not an AG-8 violation.
- **`evidence_asof`** served identically by /api/backtest + MCP + its blueprint.md Data Contract row; F1 fix (`page.tsx:258-261` `asofDate={evidence_asof ?? asof_date}`) — keep.
- **Live not_yet_computed (TC-09) + refreshing banner w/ evidence_asof (TC-07)** — captured & verified; don't re-capture.
- **TC-8 live cross-boundary capture** — unproducible on this seed (max date 2026-07-22); evaluator accepted the unit + client-render floor. Do NOT chase it as a blocker (needs an owner data cycle).
- **Out of bounds:** `main.py`, `app/api/health.py`, `app/engine/readiness.py`, `warmup.py`, `scripts/*`. No full pytest; `loaded_engine` ~80min — cite, don't run. Heavy passes: `scripts/start-backend.sh` only, `taskset -c 0-3,8-11`, BLAS/OMP=4 (AG-10). Carried unrelated: `test_db.py::test_create_all_produces_expected_tables`.
```
"Do not redo" entries above are BINDING — do not re-plan or re-test them — unless docs/goal.md changed for that item.


Last iteration eval: /home/dennis-chan/Git/trendora/runs/goal-session-ops-hardening/iter-17/eval.md

Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.

Write the iteration spec to: docs/phases/goal-ops-hardening-iter-18.md
Also keep /home/dennis-chan/Git/trendora/runs/goal-session-ops-hardening/state/blueprint.md current per your agent instructions: register any new displayed value in the Data Contract and place new pages under an existing Information-Architecture home (additive edits only). For a nav-skeleton change, make the edit AND write a one-line reason to /home/dennis-chan/Git/trendora/runs/goal-session-ops-hardening/state/blueprint.reapproval-requested.

The spec MUST include a 'Goal Mode Metadata' section with at minimum:
  - Mode: next
  - Depth: lean | full
  - Target journeys: <comma-separated journey IDs>

Do NOT write code or implement anything. The iteration spec and any blueprint edits are planning documents, not code. STOP after writing them.

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-b612f488.372082" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-b612f488.372082" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-b612f488.372082"