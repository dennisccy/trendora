# Goal Session ops-hardening — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-19T15:19:32Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter touching `data_manager.py` `_do_backfill` / `_cadence_allowed_dates`
(build J-01's explicit-request override before J-05); any iter building J-04's logfile/memory-cap
layer in `scripts/start-backend.sh`.

## iter-1 — 2026-07-19T19:21:22Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter adding persisted/served numeric fields to `data_provider_runs` /
`JobProgress` / a run-summary or aggregate payload (J-05's `coverage_snapshot` finalize hooks next
cycle) — cover the interrupted/orphan-sweep and >sample-cap paths, not just the happy path.

## iter-2 — 2026-07-20T06:06:21Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter warming/serving an ingest-time cache keyed on a dataset-version fingerprint —
EVERY count-changing ingest path (fetch/expand/remove-data too) must refresh it or the sentinel must
do a cheap real existence check; verify the fetch-then-view path, not just backfill-then-view.

## iter-3 — 2026-07-20T11:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter that first drives a new load pattern (heavy job / real fetch) through the
browser; any iter touching `app/engine/readiness.py`, `_refresh_ingest_aggregates`, or the shared
`HealthBadge`/`PreflightBanner`/`JobProgressPanel` status surfaces; any eval where the QA PASS and
the raw browser-qa verdict diverge.

## iter-4 — 2026-07-20T15:02:47Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any future goal-evaluator reading browser-qa results for this repo while the merge
script stays unfixed — whenever the merged `ui-test-results.md` references a `## Notes` section it
does not contain, open the `.llm.md` sibling before scoring any target journey.

## iter-5 — 2026-07-20T22:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter measuring or asserting page-load performance budgets; any iter adding on-load API
calls to an already call-heavy page (Dashboard, Data Manager).

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

## iter-9 — 2026-07-22T19:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration where an audit/fix round lands product code AFTER the browser-qa step, and
any evaluation weighing operator/API evidence against a stale lane verdict.

## iter-9 — 2026-07-22T19:05:00Z (second entry)  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration recording VmPeak/VmSize/RSS headroom against `server.memory_cap_mb`, and any
future J-05/AG-8 re-measurement as the price basis deepens.

## iter-10 — 2026-07-22T20:55:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration verifying crash/restart, orphan-sweep or checkpoint behaviour; any spec writing a
run-summary arithmetic assertion that must also hold for partial runs.

## iter-11 — 2026-07-22T21:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose verdict rests on browser-measured latency or on an anomaly
explained away as host contention; also any perf sweep, since the same log read reveals whether the
product's own ingest was running during the measurement.

## iter-11 — 2026-07-22T21:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose DoD says "record X in `reports/perf-budgets.md`" while X is
produced by browser-qa rather than by the developer.

## iter-12 — 2026-07-23T02:00:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose target is "measure-and-record" work against committed budgets
(`reports/perf-budgets.md`), and any evaluator tempted to accept a downstream agent's "may be scored passing"
when the recorded measurement breaches the acceptance metric.

## iter-13 — 2026-07-23T04:39:47Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter carrying an UNRESOLVED critical anti-goal on a "smaller blast radius than the
acknowledged incident" rationale — especially memory/availability bugs whose severity is load-dependent;
re-read logs/backend.log + the audit + closure for a worse-than-before manifestation before re-deferring.

## iter-14 — 2026-07-23T14:25:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter that replaces a `.all()` fetch-and-release with a streamed/`yield_per` read on a
hot path shared by concurrent ingest writers — measure latency under concurrent load on the deep basis, not
just peak memory.

## iter-15 — 2026-07-23T18:00:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration proposing a wrapper/cache/concurrency fix validated on a synthetic fixture
before a deep-basis pass; any "the fix fully accounts for X" claim not yet reconciled against a live
full-scale measurement; future decomposers tempted to loop CONTINUE on an owner-owned direction decision.

## iter-16 — 2026-07-23T23:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding a cache/precompute layer keyed on a derived identity (`asof_key`,
`dataset_version`, tenant, run id) — enumerate the ways the *identity* can move, not just the ways the
*value* can go stale, and make sure the live test exercises the identity-advancing shape, not only the
convenient one.

## iter-16 — 2026-07-23T23:22:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding user-facing status/progress/explanatory copy — verify each sentence
against the code that would have to be true for it, the same way a displayed number is verified against
the engine (AG-3's discipline, applied to prose).

## iter-17 — 2026-07-24T07:44:45Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter where a page/endpoint misses a committed `reports/perf-budgets.md` budget and the
mechanism is not yet pinned — check whether the diagnosis is blocked by missing telemetry (agent work)
before treating the residual as an owner budget-amendment decision.

## iter-18 — 2026-07-24T11:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter touching `apps/backend/app/api/backtest.py` / `mcp/tools.py` serving path or the
`resolved_forward_aggregate_evidence` resolver; more generally, any "read" endpoint that lazily
creates-once-on-first-view — instrument phases and test under a concurrent-ingest overlay, not pure reads.

## iter-19 — 2026-07-24T16:10:00Z

**Verdict:** CONTINUE
**Lesson:** "THE one shared latency blocker" framing was incomplete: fixing the create-once forward_returns INSERT on `/backtest` (backfill_forward_returns_ms, 877->13.9ms) left a SEPARATE cold-recompute subsystem on the SAME page (`ensure_loop_ms`, historical first-view, 9.6-54s no-affordance skeleton) untouched — same page, same user-visible latency class, different code path. A same-symptom latency/UX gap can hide in a different subsystem than the one you instrumented and fixed; a per-phase timing breakdown that only covers the phase you suspected will not surface it — the browser first-view walk (UT-04) did.
**Applies to:** any iter closing a "single root-cause" latency/perf journey on a page that has more than one on-load compute path — verify the OTHER first-touch paths (cold historical as-of, empty-store, first-of-day) with a live browser walk, not just the instrumented phase.

## iter-20 — 2026-07-24T19:30:00Z

**Verdict:** STALLED
**Lesson:** Moving a synchronous request-path compute to an in-process BACKGROUND thread eliminates the request-path BLOCK (9.6-54s -> 0.082s) but does NOT eliminate latency impact — the CPU-bound compute now contends for the GIL, transiently pushing OTHER concurrent traffic (and `/api/health`) over budget for the bounded compute window (3.0-6.3s `/backtest`, 1.60s health here). "Off the request thread" is not "no latency cost"; measure the CONCURRENT-traffic budget during the background window, not just the triggering request. Meta-lesson: an iteration can be a complete, correct success at its stated target yet move NO journey to passing — when the agent-tractable chain is exhausted and the journey stays blocked on owner-gated proofs + a spec-rejected-to-fix residual, STALLED is the honest verdict even after real progress (do not reflexively CONTINUE just because work landed).
**Applies to:** any iter that moves a heavy compute to an in-process thread/daemon (verify concurrent-window budgets, not just the trigger); any evaluator facing "target fully achieved but no journey crossed" (weigh C.2 human-owned-blocker before defaulting to CONTINUE).

## iter-21 — 2026-07-25T03:25:00Z

**Verdict:** STALLED
**Lesson:** A journey's acceptance state can be structurally UNPHOTOGRAPHABLE by the default capture:
`/backtest`'s `RefreshingEvidenceBanner` renders at the page BOTTOM (`page.tsx:241-274`, after
AsOfScanSummary/Scorecard/ReturnAttribution/LeadershipLists), so every viewport screenshot of the
`ready -> refreshing -> ready` cycle looked identical — `UT-J-08-01` and `-04` came back byte-identical to each
other (md5 `67e7793a…`) and to iter-17's `TC-07-backtest-page.png` and iter-20's
`TC-12-historical-view-loaded.png`. Two takeaways: (a) browser-QA must use a full-page or element-scoped
capture for any state that renders below the fold, and (b) when screenshots are uninformative, this codebase
offers a *stronger* substitute — the `dataset_version` stamp is literally `(scanner_runs count,
forward_returns count)`, so cross-referencing the stamp bump, `forward_aggregate_cache.created_at`, and the
screenshot mtimes proves the serving state machine from the DB without trusting any prose.
**Applies to:** any iteration verifying `/backtest` evidence states (`refreshing` / `not_yet_computed` /
`ready`), and any evaluator receiving screenshots whose md5s repeat across iterations — hash the evidence
directory before crediting a status change.

## iter-22 — 2026-07-25T08:55:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A measured "window duration" reported by a polling lane can be the POLLER's elapsed time, not the
window's. The browser-qa lane reported its BCW as "28.06 s (well inside the bound)"; the
`forward_aggregate_cache` commit rows for that same `(asof_key, dataset_version)` show 07:31:59.453 ->
07:32:56.164 (56.71 s first-to-last commit, ~14 s/horizon), so with the usual ~13 s trigger->first-commit lead
the real window was ~69.8 s — inside the amended 90 s bound but NOT inside the 60 s one it was cited against.
Re-derive any window/elapsed claim from the source-of-truth timestamps (DB rows, server logs), never from the
measuring script's own clock start. Corollary from the same iteration: a handoff's "I grepped the log for X and
found none" is checkable in seconds and was FALSE here — `logs/backend.log:76796-76808` contains both the exact
string the developer said they searched for and a real `MemoryError`.
**Applies to:** any iteration whose acceptance rests on a timed window, poll series, or "no errors in the log"
claim — especially perf/latency measurement passes and any goal-closing evaluation.

## iter-23 — 2026-07-25T11:05:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A served `evidence_generated_at` can legitimately have NO surviving row in
`forward_aggregate_cache` — the iter-16 cutover contract (`apps/backend/app/engine/forward_testing.py:1135-1156`)
deletes the prior `dataset_version`'s rows for an `asof_key` the instant the current version becomes complete.
An evaluator who checks the refreshing banner's timestamp against the DB *after* the warm finishes will find
nothing and can wrongly conclude the number was fabricated (I nearly did). Check the pruning contract before
calling an AG-3 violation; the absence is actually positive evidence for the "never mixes versions" clause.
**Applies to:** any iteration or evaluation that verifies `/backtest` refreshing/last-good evidence against
`forward_aggregate_cache`, or that audits AG-3 on a `generated_at`/`evidence_asof` label.

## iter-23 — 2026-07-25T11:05:00Z (second)

**Verdict:** GOAL_ACHIEVED
**Lesson:** A spec can contradict itself and produce a "violation" that is really the developer obeying the
other half: iter-23's BACKGROUND (line 114) instructed the exact 4-decimal figures "7.1191 s / 0.2530 s"
while its own TC-2 demanded figures "verbatim in `perf-budgets.md`" (which prints 3 decimals). The developer
followed BACKGROUND; the reviewer flagged TC-2. Resolve these by going to the raw source
(`runs/goal-ops-hardening-iter-22/bcw-measure.csv` — max `bt_latency_s` is 7.1191 exactly), not by picking a
side between two spec clauses.
**Applies to:** any iteration whose DoD requires "verbatim" citation of a figure that exists at two
precisions (raw CSV vs rounded report); decomposers should name ONE canonical rendering.

## iter-24 — 2026-07-26T13:52:22Z

**Verdict:** CONTINUE
**Lesson:** A goal-proposer auto-appended journey (J-09) inherited this session's standard Acceptance
clauses verbatim — including the `demo.sh --session-live` walkthrough clause — but the iteration spec's
IN SCOPE / DEFINITION OF DONE never mapped that clause to any task, so the journey shipped fully working and
still could not be scored `passing`. Nothing in `run-goal.sh` writes
`reports/goal-session-ops-hardening-demo.json`, so a walkthrough clause is only ever closed by an explicit
task — the same gap that made the iter-22 second-key CONFIRM reject GOAL_ACHIEVED, now repeated one journey
later.
**Applies to:** any iteration targeting a journey whose Acceptance block was auto-appended between the
`<!-- AUTO:journeys -->` markers, and any decomposer writing a DoD — enumerate EVERY Acceptance bullet,
especially the walkthrough/demo-manifest one, before declaring scope.

## iter-24 — 2026-07-26T13:52:22Z (second)

**Verdict:** CONTINUE
**Lesson:** On this host Chrome MCP returns a solid-colour blank frame for ANY scrolled screenshot (verified
by the browser-QA agent across pages, scroll methods, `fullpage`, element selectors and CSS zoom), so the
new `/data` panel — the last panel on a ~24,800px page — is unphotographable. The workable substitute is the
auto-saved raw DOM capture (`~/.cache/superpowers/browser/<date>/session-*/NNN-*.html`) read verbatim and
cross-checked against the live API and the SQLite rows; that chain proved AG-3 to 1.68 ms, stronger than any
screenshot would have.
**Applies to:** any future iteration whose acceptance state renders below the fold on this host, and any
evaluator weighing "no screenshot" against the absolute no-screenshot rail.
