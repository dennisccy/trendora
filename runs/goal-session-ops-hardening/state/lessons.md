# Goal Session ops-hardening — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-19T15:19:32Z

**Verdict:** CONTINUE
**Lesson:** J-01's real blocker is NOT the obvious missing exclusion-reason schema but the
cadence gate: `_do_backfill` (`data_manager.py` ~:2496) filters every backfill through
`_cadence_allowed_dates`, and because `snapshot_cadence.daily_start` is `2026-06-01`, the exact
goal.md-suggested May 2026 range (and J-05's 2026-05-15 single-day date) both compute
`dates_total=0` and ingest nothing. So J-01 and J-05 share ONE root cause — "requested range
always wins" must land before either journey can even be exercised. Secondary: the iter-25 prose
in `reports/perf-budgets.md` claims `start-backend.sh` applies a `ulimit -v` cap, but the current
script applies none (confirmed by source read + `/proc/<pid>/environ`) — whoever builds J-04's
memory-cap enforcement must not assume that doc reflects reality.
**Applies to:** any iter touching `data_manager.py` `_do_backfill` / `_cadence_allowed_dates`
(build J-01's explicit-request override before J-05); any iter building J-04's logfile/memory-cap
layer in `scripts/start-backend.sh`.

## iter-1 — 2026-07-19T19:21:22Z

**Verdict:** CONTINUE
**Lesson:** A new persisted numeric-display field's honesty risk lives in its NOT-YET-COMPUTED and
mass-failure edges, not its happy path. The breakdown fields (`calendar_days` etc.) were exact on
completed backfills but (a) served a fabricated literal `0` on interrupted/job-start rows — because
`_create_run_record` serializes `_run_detail(prog)` while `prog` is still at dataclass defaults and
the orphan-sweep freezes that row without recomputing — and (b) `error_other = len(date_failures)`
silently under-counted past the 20-sample cap. Both are direct AG-3 hits; the browser-qa's exact
DOM reads found (a) and the audit found both, yet the reviewer rated (b) MINOR/out-of-scope and QA
did not act — so DO NOT rely on reviewer/QA alone to catch honesty edges on a new field. Fix
pattern: gate each field's serialization on "actually computed" (a sentinel like `calendar_days>0`)
and mirror the existing bounded-sample/`_total` split (`omitted`/`omitted_total`) for any count.
**Applies to:** any iter adding persisted/served numeric fields to `data_provider_runs` /
`JobProgress` / a run-summary or aggregate payload (J-05's `coverage_snapshot` finalize hooks next
cycle) — cover the interrupted/orphan-sweep and >sample-cap paths, not just the happy path.

## iter-2 — 2026-07-20T06:06:21Z

**Verdict:** CONTINUE
**Lesson:** Keying a served ingest-time cache on a LIVE dataset fingerprint (`coverage_snapshot`'s
`dataset_version` = `_membership_dataset_version`, embedding bar/symbol/run counts) means ANY
count-changing ingest silently invalidates EVERY cached row for every as-of — and if some ingest
kinds are (correctly, per scope) excluded from the refresh hook, the read path serves the
honest-empty all-zero sentinel for a fully-populated DB until a restart or backfill re-persists. Two
individually-correct decisions (exclude `fetch`/`expand` from the finalize hook; key on a fingerprint
for byte-identity) compose into an emergent AG-3-class false-zero on the DEFAULT `/data` view (audit
B1, live-reproduced in UT-07 when a fetch landed 1 bar). The offline "fetch is always zero-work"
assumption also proved false — the committed fixture had a landable 2026-07-17 bar.
**Applies to:** any iter warming/serving an ingest-time cache keyed on a dataset-version fingerprint —
EVERY count-changing ingest path (fetch/expand/remove-data too) must refresh it or the sentinel must
do a cheap real existence check; verify the fetch-then-view path, not just backfill-then-view.

## iter-3 — 2026-07-20T11:20:00Z

**Verdict:** CONTINUE
**Lesson:** A tightly-scoped, correct backend fix (B1/B2, independently audit-verified) can still
fail to advance its target journey to `passing`, because the FIRST iteration to drive a realistic
load pattern (a heavy rebuild + a real fetch) through the browser exposes latent trust-surface
defects on SHARED components that no prior iteration exercised: B3 (`app/engine/readiness.py:129`
`latest_servable` flips the app-wide badge to a crash-identical false "Backend unavailable"/NO-GO
when a fetched bar out-dates the latest snapshot) and F1 (`_refresh_ingest_aggregates`'s per-date
loop emits no `tick()`, so the job heartbeat freezes → false "possibly stalled"). Both are
pre-existing and out-of-scope, but they gate a clean journey pass. Second lesson: the QA report
claimed a clean 12/12 and marked TC-11 PASS on a STATIC page load, burying the raw browser-qa FAIL
— only the audit (T1) and closure caught it. Always cross-check the QA verdict against the raw
`ui-test-results.md` browser verdict; never score a target journey clean on backend-correctness
alone.
**Applies to:** any iter that first drives a new load pattern (heavy job / real fetch) through the
browser; any iter touching `app/engine/readiness.py`, `_refresh_ingest_aggregates`, or the shared
`HealthBadge`/`PreflightBanner`/`JobProgressPanel` status surfaces; any eval where the QA PASS and
the raw browser-qa verdict diverge.

## iter-4 — 2026-07-20T15:02:47Z

**Verdict:** CONTINUE
**Lesson:** `merge_ui_test_results.py` silently corrupts the merged
`reports/phase-<iter>-ui-test-results.md`: it DROPS the raw browser-qa `## Notes` section (even
though the merged table cells still say "see Notes for the one caveat" 3×) and mis-sums the header
("12/13 journeys passed" over a 13-row all-PASS table). Those Notes hold the load-bearing caveats
(UT-03's DEGRADED-banner-is-unrelated-drift explanation, UT-04's blank-tiny-screenshot disclosure,
UT-08's architecturally-unreachable-precondition scope adjustment). The fix: read the raw
`reports/phase-<iter>-ui-test-results.llm.md` directly — which is exactly this session's own iter-3
lesson, now shown to be un-followable from the merged file alone. The closure auditor independently
reached the same finding.
**Applies to:** any future goal-evaluator reading browser-qa results for this repo while the merge
script stays unfixed — whenever the merged `ui-test-results.md` references a `## Notes` section it
does not contain, open the `.llm.md` sibling before scoring any target journey.

## iter-5 — 2026-07-20T22:45:00Z

**Verdict:** CONTINUE
**Lesson:** curl-based perf measurement systematically UNDER-reports real page latency: the developer's
harness measured /api/indexes?full=true at 0.79–0.95s (in-budget) while a real browser hit 1.68–2.19s
(over-budget, 3/3) because Chrome caps at 6 connections/origin against HTTP/1.1 uvicorn and the Dashboard
fires 10-13 same-origin calls in one ~10ms window. Any "pages load within budget" journey must be scored
on browser-measured latency, not curl — and a page's TOTAL on-load call fan-out is itself the risk, not
just each endpoint's isolated cost. Two endpoints (/api/indexes, /api/data/availability) are in this class.
**Applies to:** any iter measuring or asserting page-load performance budgets; any iter adding on-load API
calls to an already call-heavy page (Dashboard, Data Manager).

## iter-5 — 2026-07-20T22:45:00Z

**Verdict:** CONTINUE
**Lesson:** deterministic golden-script replay assertions that check for a hard-coded historical value on a
GROWING unpaginated list go stale silently: J-01's step-6 expected "2026-05-15" on /scanner-runs, but the
run history grew from ~180 (when the script was authored, iter-1) to 750 rows, pushing that date below the
fold / past the runner's step timeout — producing a FAIL that looks like a regression but is a test-harness
artifact (the run row still exists; the display path was untouched). A required-still-passing replay FAIL
must be adjudicated (DB query + is-the-code-path-in-the-diff check + screenshot), not auto-treated as
REGRESSION — and golden scripts should assert on data the journey's own action produces, not on a fixed
proxy row on a page the journey doesn't change.
**Applies to:** any iter whose measurement/backfill runs add rows to /scanner-runs or /api/runs; any
goal-evaluator triaging a required-still-passing deterministic-replay FAIL with no LLM-fallback adjudication.


## iter-6 — 2026-07-21T01:43:56Z

**Verdict:** CONTINUE
**Lesson:** A page can be "within its committed budget" on the shipped seed yet violate the journey's
intent on the basis the session actually runs: `/evidence`'s one-time cold recompute is ~9.5s on the
170k-row seed but ~73s on the accumulated ~1.5M-row live dev DB (UT-13 real-browser 73.5s vs 0.02s warm
curl), because `event_study_cache`/`drawdown_expectations` are lazy-warmed and any dataset change (e.g.
this cycle's own verification backfill) invalidates them. Item I's "warm ≤3s + bounded cold miss" clause
technically covers it, but for the LAST Must-have journey ("pages load only what they need") the honest bar
is first-view-in-budget on the grown basis — warm the hot keys at ingest finalize, don't lean on the
cold-miss clause. Also: iter-5's own curl-under-reports lesson recurred in reverse — the same page's first
handoff numbers (555s/92s) were contamination artifacts (concurrent 84-min pytest + stale cache), so
re-measure on an IDLE host before filing OR retracting a "severe regression."
**Applies to:** any iter closing J-06 / touching a lazy-warmed derived cache (event_study_cache,
market_phase_cache, drawdown_expectations); any perf claim measured while a heavy pytest/ingest runs concurrently.

## iter-7 — 2026-07-21T08:10:00Z

**Verdict:** REGRESSION
**Lesson:** An upstream audit that reasons about "orthogonality" (frontend/boot/readiness untouched →
"cannot have regressed those journeys") can be empirically WRONG when the diff touches a shared
hot-path function: iter-7's `_refresh_ingest_aggregates` warm looked orthogonal to J-05, but it runs
7 synchronous `compute_drawdown_expectations` calls on the ingest FINALIZE path — exactly J-05's
"health responsive during heavy ingest" window — and browser-qa caught a 7-min health hang + MemoryError
at the enforced 6144MB ulimit that the audit (which ran before browser-qa and never exercised that step)
declared impossible. Adding ANY synchronous per-item compute to the ingest finalize hook is a memory/
availability risk on the grown live DB, not a free timing move — its peak-RAM cost must be measured
during a real back-to-back heavy ingest, not just unit-tested.
**Applies to:** any iter that adds work to `_refresh_ingest_aggregates` / the ingest finalize hook, or
any "warm-a-cache-earlier" change; any iter where the audit runs before browser-qa and asserts a required
journey is orthogonal to the diff — the evaluator must still weight the live browser evidence over the
orthogonality argument.
