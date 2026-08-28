# Goal Session market-compass — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-08-19T22:30:56Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any baseline (iter-0) evaluation, and any iteration whose `snapshot-sha` file is
empty or whose scan-report scope reads "changes since HEAD~1".

## iter-0 — 2026-08-19T22:30:56Z (evidence quality)  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration scoring journeys as failing because a section/page is missing,
especially baselines where several journeys share one page.

## iter-1 — 2026-08-20T05:04:26Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose deliverable is a new API field or new served payload key —
restart backend + frontend after the dev/audit steps and BEFORE browser-qa, and treat "key absent
from the API" as an environment hypothesis until the process start time is checked.

## iter-1 — 2026-08-20T05:04:26Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding content behind an existing feature gate — assert the new value
at the layer the spec words its acceptance against (the served response), and never let the
acceptance test skip on the gate it is meant to prove independence from.

## iter-1 — 2026-08-20T05:04:26Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any journey step that instructs a data Remove — check `seed_latest_date` covers the
range first, and prefer the backend's own boot/persist path over a destructive remove+rebuild cycle
to obtain a fresh run.

## iter-2 — 2026-08-20T09:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose spec metadata says `Depth: full` — the evaluator should diff
`depth-dispatched` against the spec's Depth line during the evidence walk and treat a downgrade as
an ESCALATE trigger, not just note it.

## iter-2 — 2026-08-20T09:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter touching `apps/frontend/app/page.tsx` layout, and specifically J-07/J-08's
Today-page recomposition and `/market` relocation.

## iter-2 — 2026-08-20T09:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iter adding user-facing generated prose under `app/engine/compass.py`, and the
J-05/J-06 manifest work that will serialise these same strings into an exported artifact.

## iter-3 — 2026-08-20T13:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every iteration's evidence review — run `md5sum` over
`reports/qa/<iter>-evidence/*.png` before citing any of them, and expect long pages (audit tables,
cohort lists) to need an element-scoped capture rather than a full-page one.

## iter-3 — 2026-08-20T13:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose acceptance depends on the ingest-finalize tail
(`data_manager._refresh_ingest_aggregates`) — plan the remove+backfill drill as a first-class,
budgeted step, or state up front that the journey cannot close this round.

## iter-4 — 2026-08-20T15:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose acceptance is a measured resource/latency threshold, and any
goal.md amendment that sets one.

## iter-4 — 2026-08-20T15:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration reading `*-regression-replay-results.md`; any journey whose golden
asserts on a multi-word value inside a narrow table column.

## iter-6 — 2026-08-20T22:15:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose `docs/goal.md` declares a lane gate or dataset quarantine; any
evaluator reading a merged results file after a depth demotion (check `iter-<N>/depth-dispatched`
against the spec's `**Depth:**` line FIRST, and treat quarantined evidence as unusable in both
directions); any iteration spec that names a Full trigger.

## iter-6 — 2026-08-20T22:16:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any journey involving a live data refetch, backfill, or vendor migration; any code
adding a provider-scoped recovery path.

## iter-7 — 2026-08-21T01:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any fail-closed gate, precondition check or verification step whose verdict ladder can
be reached with an empty/partial input set — especially incident-recovery and data-repair paths, where
the missing data IS the trigger; also any iteration whose new tests all seed complete fixtures.

## iter-8 — 2026-08-21T13:55:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding or citing a cross-vendor / cross-source / A-vs-B agreement
check, anything touching `j10_recovery.py`'s convention gate, and any future work that reads the
`daily_prices` history across the 2026-07-01/07-02 seed boundary (a real, never-examined vendor
discontinuity lives there).

## iter-8 — 2026-08-21T13:56:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every remaining market-compass iteration while the lane gate is open (J-10's 567-symbol
continuation, all of J-11), and any goal whose `docs/goal.md` forbids a pipeline lane rather than a
code path.

## iter-9 — 2026-08-23T13:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose acceptance rests on a population-wide uniform figure (all bridge
factors, all hashes equal, all deltas zero, 100% coverage) — especially J-11's "all 11 rebuilt runs share
the frozen engine_identity" and its cache-invalidation proofs.

## iter-9 — 2026-08-23T13:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration where full depth is optional; and specifically J-11, whose acceptance is a
long list of narrative claims ("no stale cache survives", "no new historical manifest appears") that a
row-count check cannot confirm.

## iter-10 — 2026-08-23T13:36:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose acceptance items say "the LIVE schema/database" — verify against the
live artifact (`sqlite_master`, `pragma_foreign_key_check`) and not only against a metadata-built fixture;
and any fail-closed read path, where the missing-field branch deserves its own test alongside the
missing-row branch.

## iter-11 — 2026-08-23T23:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration performing a table rebuild/migration on a live SQLite database, any work
touching `apps/backend/app/engine/j11_schema_migration.py` or `app/db.py`'s additive-schema path, and
any acceptance item phrased as "removes X and nothing else".

## iter-12 — 2026-08-24T14:45:21Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any evaluator carrying a `passing` journey forward on the absence of
`journeys-changed.md`, and any goal whose journey block contains nested `- **J-NN` bullets (this file
now has one in J-10 and the same shape could appear anywhere) — diff `docs/goal.md` against the
iteration snapshot for the journey's own line range instead of trusting the hash alone.

## iter-12 — 2026-08-24T14:45:22Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration claiming zero writes to `apps/backend/data/trendora.db` — J-11 Stage C's
mutation accounting above all, and any future maintenance-isolation iteration. Record the file mtime +
size + WAL size at the true start and end, and treat a purpose-built fingerprint pair as corroboration,
never as the primary instrument.

## iter-13 — 2026-08-24T19:35:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that freezes an identity/fingerprint for a multi-iteration attempt —
especially J-11 Stage D, whose whole correctness claim is "all 11 rebuilt runs share ONE frozen
identity"; and generally to any preflight/gate artifact: for every field captured, state whether it is
compared, and against what.

## iter-13 — 2026-08-24T19:36:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any future destructive maintenance iteration (J-11 Stages D/E/F), and any "we wrote
nothing" or "we wrote only X" claim on `trendora.db`.

## iter-14 — 2026-08-25T01:15:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that adds a classifier, gate, or verdict function — before trusting its
output, check that every label/branch in its declared vocabulary is reachable from its actual inputs,
and that no reported "finding" is true by construction.

## iter-14b — 2026-08-25T01:15:00Z

**Verdict:** STALLED
**Lesson:** An auditor who finds a real gap and then closes it "from independent evidence" can close it
wrongly, and that is harder to catch than the original gap because it arrives wearing the auditor's
credibility. Here the audit correctly identified that the AVB convention's volume half was untested
(explicitly: "AVB-D territory, and AVB-D forces NO"), then rescued it by asserting the bridge was
calibrated against `adjclose`, "which carries no volume" — but `j10_recovery.py:643` calibrates with
`provider.get_daily`, and `yahoo_provider.py:351-369` reads close and volume from the same
`indicators.quote[0]` block, so the calibration series is exactly the series the volume came from. The
second prop, a pool-wide volume check, could not speak to AVB at all: 565 of 566 symbols carry a bridge
factor ~1.0, so the only symbol at risk is the one the test excludes by construction.
**Applies to:** any evaluation where an audit finding is marked "closed on my own evidence" — open the
cited call site rather than the cited claim, and ask whether the corroborating population actually
contains the case in question.

## iter-15 — 2026-08-25T11:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that clears or rebuilds one storage layer while deliberately preserving
another — before declaring the clear safe, grep the boot/warmup/resolve paths for anything that derives
its target from the PRESERVED layer, and check whether the two layers now disagree in a way that makes a
routine start-up destructive.

## iter-15b — 2026-08-25T11:05:00Z

**Verdict:** STALLED
**Lesson:** A fingerprint quoted into a spec without its recipe is an unfalsifiable verification target,
and it costs more than the check was ever worth. The iter-15 spec's TC-1 required matching
`avb_daily_prices_sha256 = 0257c56d…0b11cd`; the developer honestly recorded "unknown", and the auditor
tried nine candidate recipes and concluded it "matches nothing on disk" and "could not succeed by
construction". Both wrong on the reproducibility point: `sha256` over the **concatenated `repr()`** of
`(symbol,date,open,high,low,close,volume)` for all 5,397 AVB rows ordered by date reproduces it exactly
(I recomputed it in one attempt once the recipe was stated). There was never a data discrepancy. The
corollary is the sharper half: an auditor who tries N recipes and concludes "unreproducible" has proven
only that N recipes failed — that is evidence about the search, not about the artifact.
**Applies to:** any spec or handoff that quotes a hash/fingerprint as a comparison target — state the
exact recipe (query, column order, serialization, separator, sort) beside the value, and when a
fingerprint fails to reproduce, downgrade the conclusion to "recipe unknown" rather than "value
unreproducible" unless the underlying data is independently shown to differ.

## iter-16 — 2026-08-25T18:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding a guard/gate/feature-flag/quarantine whose behaviour keys on
persisted state (`apps/backend/app/engine/j11_preboot_guard.py`, `warmup.py`, and any future
boot-path or middleware check); also any "prove it on disposable test state" acceptance clause —
treat it as necessary, never sufficient.

## iter-16 — 2026-08-25T18:06:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that mutates stored state which an existing diagnostic, A/B trace, or
counterfactual reads (`j11_avb_diagnostic.py`'s trace functions, `run_j11_iter16_stage_d_readiness.py`),
and any spec that tells an implementer to drop a substitution argument because "the real data now has
that value".

## iter-17 — 2026-08-25T21:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose spec asserts an expected value for a probe of a KNOWN-BROKEN or
quarantined condition — especially `runs/**/j11-*verification*.json`-style evidence and any future
"confirm the guard is not armed / confirm X is still absent" check.

## iter-17 — 2026-08-25T21:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any future J-11/AVB Stage-D readiness or verification spec proposing a ratio/tolerance
assertion over values in `j11_avb_diagnostic.py` / `j11_avb_correction.py`, and any "independent
cross-check" claim in `runs/goal-market-compass-iter-*/j11-*.json`.

## iter-18 — 2026-08-26T00:55:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding a guard/quarantine/kill-switch scoped by trigger class; any
iteration that would lift maintenance isolation or re-enable browser QA on this project; anything
touching `warmup.py`, `forward_testing.py`, `scanner.py`, `snapshot_serving.py` or `data_manager.py`.

## iter-18 — 2026-08-26T00:55:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any future iteration that boots the backend or resumes browser QA on this project (the
different readiness badge and the 2026-07-23 "latest" are EXPECTED, not a regression); any change to
`warmup.py`/`main.py` boot sequencing or `readiness.py`.

## iter-19 — 2026-08-26T15:40:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration executing J-11 Stage E/F/G, and any future live rebuild that changes which
date is `max(ScannerRun.asof_date)` or populates a previously-empty date.

## iter-19b — 2026-08-26T15:40:00Z

**Verdict:** CONTINUE
**Lesson:** The strongest mutation-accounting evidence is a CROSS-ITERATION diff, not the iteration's own
before/after pair. Recomputing `j11_maintenance.capture_full_table_sweep` live and diffing it against the
PREVIOUS iteration's recorded end-state sweep (`iter-18/j11-iter18-full-table-sweep-after.json`) proves
both "this iteration wrote only where authorized" AND "nothing drifted between the iterations" in one
step — something an in-iteration pair structurally cannot show. Pair it with a real field-by-field
content comparison on the one table whose immutability is an anti-goal (all 28 columns of
`next_session_manifests` vs the iter-16 certified baseline), because the rowid sweep alone cannot see an
in-place UPDATE (auditor B2). Normalize ORM-vs-sqlite serialization first (datetime `T` separator, bool
`False` vs `0`) or the comparison false-alarms.
**Applies to:** any evaluator or auditor scoring a live-database write iteration in this session.

## iter-20 — 2026-08-27T04:20:00Z

**Verdict:** CONTINUE
**Lesson:** `docs/goal.md` J-11 step 5 states as fact that the incident left forward-return holes on
retained (non-incident) runs. It is wrong about this codebase: `data_manager._cascade_targets`
(`apps/backend/app/engine/data_manager.py:1967-2011`) invalidates a run when ANY of its `ForwardReturn`
rows measures into a removed bar date, and `remove_price_data` (`:2173-2177`) then deletes that run's
rows WHOLE — so a run that would carry a partial hole is deleted entirely and becomes an incident date.
A retained-run hole is structurally impossible, and the live data agrees (zero non-rebuilt rows measure
into 2026-08-10/11/12). Three lanes reached the right "zero" answer via a 15-combination single-calendar
enumeration, which is not exhaustive because `measured_date` resolves PER SYMBOL (run 3154 horizon 1
splits into 2026-08-04 for 428 symbols and 08-05 for 124).
**Applies to:** any iteration whose acceptance criteria are copied from a `docs/goal.md` factual premise
about how the code behaves — re-derive the premise from the code path before scoring "requirement unmet"
or "requirement met"; specifically, J-11 Stage G must treat population (b) = 0 as the CORRECT answer,
not a missing repair, and must not weaken its gate to accommodate a premise that was never true.

## iter-21 — 2026-08-27T09:30:00Z

**Verdict:** CONTINUE
**Lesson:** Emptying a cache table is not a durable state — it is only durable if every WRITE path
back into that table is enumerated and closed. Stage F correctly deleted `coverage_snapshot`, but
`coverage_from_storage`'s self-heal branch (`apps/backend/app/engine/data_manager.py:1544-1546`)
calls `refresh_coverage_snapshot_for` → `_upsert_coverage_snapshot` on the READ path whenever an
explicit `?as_of=` names a date backed by a real `ScannerRun` — which, after Stage D, includes all
eleven incident dates — and `data_manager.py` imports no boundary guard at all. One page visit
would repopulate a table the repair just cleared, for a quarantined date, and the same visit's
`membership_timeline_cached` MISS would prune the row Stage F deliberately preserved. Five lanes
(dev, review, QA, audit, coherence) each verified the deletion happened; none asked what could put
the rows back. The spec named this function once, but only as a reason to *classify* the table.
**Applies to:** any iteration that deletes or invalidates cached/derived rows as a correctness fix —
grep every caller of the table's model for an upsert/insert reachable from a request path BEFORE
asserting "no stale derived state remains"; and specifically J-11 Stage G, whose acceptance list
includes "caches consistent with the rebuilt state" and must therefore assert cleanliness after the
application is allowed to boot, or foreclose the write first.

## iter-22 — 2026-08-27T15:20:00Z

**Verdict:** STALLED
**Lesson:** A "the cache will refresh cheaply on the next miss" proof is NOT a "the cached content is
still correct" proof — they are logically independent, and iteration 21 shipped the first while the
acceptance text required the second. Stage G's per-date recompute-and-compare against
`membership_timeline_cache`'s stored points (`j11_stage_g_verify.verify_membership_timeline_preserved_row`)
found a genuinely stale value nobody had reported — 2026-08-10's `exits` stored as `['AMSC','MARA']` where
the fresh recompute gives `['MARA']` — and the pre-approved delete fallback closed it. When a preserve
decision is made for performance reasons, the content correctness of what is being preserved is a separate
required check.
**Applies to:** any iteration that PRESERVES rather than invalidates a derived/cache row after an
upstream data change — and any acceptance gate whose wording is "no stale derived state remains".

## iter-22 — 2026-08-27T15:20:00Z

**Verdict:** STALLED
**Lesson:** Third appearance in this session of one defect class: a boolean that cannot fail sitting inside
the gate that authorizes an irreversible write (iter-20's Stage E checks, iter-21's, and here
`stage_g_verdict`'s `membership_timeline_reconciled`, which accepted both of the only two dispositions its
source function can return). What made this one worse was ordering: the CLI performed the boundary write
BEFORE the one real reconciliation check. The reviewer caught it — the first time in this arc the reviewer,
not the auditor or the evaluator, found the decisive defect — and the fix pass had to reorder the CLI, not
just the expression. Two rules earned: (a) for any check gating an irreversible action, mutate the REAL
production module and prove the suite fails, never a hand-built fixture; (b) the proof must run BEFORE the
action, or it is a post-mortem, not a gate.
**Applies to:** any iteration whose spec contains a one-way action (a live write, a flag flip, a
deactivation, a delete) gated on a computed verdict.

## iter-22 — 2026-08-27T15:20:00Z

**Verdict:** STALLED
**Lesson:** A goal file can make a stage's own acceptance criterion physically impossible and nobody
notices, because the impossible criterion gets "resolved" by a check that asserts rather than measures.
`docs/goal.md:1408` assigns Stage G the "final serving/replay verification" while the same owner ruling
(item 4) forbids booting the app until Stage G passes; the trap check for it returned an unconditional
`ok: True` on the reasoning "this module IS Stage G". Detection rule: any acceptance item that no live
query or test could ever falsify must be labelled as procedural/asserted, counted separately, and
surfaced to the evaluator — never allowed to contribute a silent `true` to a gate.
**Applies to:** any spec whose acceptance list is assembled from goal.md prose, especially where a safety
constraint and a verification requirement reference each other.

## iter-23 — 2026-08-27T21:45:00Z

**Verdict:** STALLED
**Lesson:** A "run only against a disposable clone" contract cannot be enforced by convention — the
harness enforces nothing. `scripts/automation/goal-iter-lean.sh:256-257` starts the deterministic replay
lane with `bash scripts/start-backend.sh` and no `TRENDORA_CONFIG`, so it silently booted the CANONICAL
`apps/backend/data/trendora.db` and wrote 10 cache rows into it while the iteration's own boot correctly
used the clone. The developer had already built the right guard (`scripts/start-backend-j11-verify.sh`
refuses to boot without an off-canonical override) — it just was not on the lane's path. If a future
iteration must confine the app to a clone, the ONLY reliable lever is making the default launcher itself
fail closed, never a wrapper the harness does not call.
**Applies to:** any iteration that boots services against a non-default database (clone, snapshot,
fixture, restore drill), and any change to `scripts/automation/goal-iter-lean.sh` / `browser-qa-phase.sh`
/ `qa-phase.sh` service-start blocks.

## iter-23b — 2026-08-27T21:45:00Z

**Verdict:** STALLED
**Lesson:** sha256 of a WAL-mode SQLite `.db` file is NOT a proof that the database is unmutated. This
iteration proved "canonical byte-unchanged" with matching file checksums — and it was literally true, yet
the database's CONTENT had changed: SQLite kept the new rows in the sibling `trendora.db-wal` (mtime
2026-08-27 20:26:08.352941 UTC) and never checkpointed them into the main file, whose sha256 and mtime
both stayed at their 09:27 values. The instrument that actually caught it was the `-wal`/`-shm` mtime plus
per-table `created_at` reconciliation. Any future immutability claim over a SQLite file must bracket
`.db` + `-wal` + `-shm`, or read logical row state, and must be captured AFTER the last lane finishes —
this run's final checksum was taken 3 minutes before the breach it was supposed to detect.
**Applies to:** any iteration asserting a database file is unchanged (J-10/J-11-style repair or drill
work, any `db_file_fingerprint` / provenance check in `app/engine/j11_*`), and any evaluator re-deriving
such a claim.

## iter-24 — 2026-08-28T00:05:00Z

**Verdict:** ESCALATE
**Lesson:** A spec's PROSE can silently disable a whole verification lane. `replay_lane_spec_journeys`
(`scripts/automation/lib/replay-lane.sh:75-77`) does `grep -iE '<label>' "$SPEC" | head -1` — FIRST
matching line wins. Iter-24's `Target journeys` bullet wrapped onto a line reading "…see
Required-still-passing and TESTING", which matched before the real bullet two lines later and carries no
`J-NN` token, so `REQUIRED_JOURNEYS` parsed EMPTY, `_use_replay=no`, and J-01/J-04/J-10 went unverified
with NO error — the engine logged only "replay: no", indistinguishable from "nothing to replay". Two
durable rules: never let a journey-set label appear in prose before its own bullet, and never read
"replay: no" as benign — cross-check that `reports/phase-<iter>-regression-replay-results.md` exists
whenever the spec names a non-empty Required-still-passing set.
**Applies to:** any iteration whose spec mentions "Target journeys" / "Required-still-passing" outside
its own metadata bullet; any evaluator scoring an iteration where the replay lane reported no results;
any future fix to `lib/replay-lane.sh`'s journey-set parsing.

## iter-24b — 2026-08-28T00:05:00Z

**Verdict:** ESCALATE
**Lesson:** The iter-24 launch-context lock guarantees CONSISTENCY, not canonical-DB PROTECTION. It
resolves the launch command ONCE at iteration start and refuses later drift — so with no override set at
start-up, the locked value IS `bash scripts/start-backend.sh` and every lane consistently boots the
canonical DB, by design. Protection therefore still depends on `CHAIN_START_BACKEND_CMD`/`TRENDORA_CONFIG`
being present in the ENGINE's environment BEFORE `goal-iter-lean.sh` starts; an override established
mid-run (inside a dispatch) is too late to be locked. Corollary for verification: iter-24's live
clone-only boot does NOT prove the fix, because the owner had set the ambient override and the pre-fix
code (`git show HEAD:…/goal-iter-lean.sh:254-261`) would have honoured it identically — the regression
test is the proof, the live boot is only a confound-free demonstration of the outcome.
**Applies to:** any iteration needing an isolated/disposable database; any claim that the canonical DB
"can no longer be booted"; any future extension of the guard to the five sibling scripts
(`browser-qa-phase.sh`, `qa-phase.sh`, `run-phase.sh`, `demo-phase.sh`, `run-benchmark.sh`).

## iter-25 — 2026-08-28T13:10:00Z

**Verdict:** CONTINUE
**Lesson:** A fix for a silent-wrong-parse can introduce its exact mirror, and the guard shipped
alongside it can be blind to the mirror by construction. `replay_lane_spec_journeys` was changed from
"first label-matching line" to "first label-matching line containing a J-NN token" — which also skips a
legitimate `**Required-still-passing journeys:** None this iteration` bullet and lets an incidental prose
mention later in the document supply the set (real, demonstrated on the committed
`docs/phases/goal-market-compass-iter-7.md`, which returned `J-10` for a spec that declares none). The new
`replay_lane_warn_if_zero_parse` could never catch it because it only fires on EMPTY parses. Reviewer, QA,
coherence and ux-regression all passed it; the independent auditor caught it, and I reproduced both the
bug and the fix myself. Second, smaller lesson from the same iteration: a perf addendum asserted a causal
story ("no second engine shared the host") written purely from the client-side harness's own output while
`host-guard/events.jsonl` and `logs/backend.log` — which flatly contradict it — sat on disk untouched.
**Applies to:** any iteration that patches a parser/guard in `incredible_auto_dev/scripts/automation/`
(always run the old-vs-new differential across ALL of `docs/phases/*.md`, and ask what shape of wrong
answer the new guard structurally cannot see); and any iteration writing a `reports/perf-budgets.md`
addendum (cross-check every causal and load claim against the server log and host-guard event stream, and
retain the raw sampler output with UTC start/end times).

## iter-26 — 2026-08-28T14:30:00Z

**Verdict:** ESCALATE
**Lesson:** A documented, unit-tested state can be structurally UNREACHABLE through the live route and
still look like coverage: `basis.status == "unavailable"` in `app/engine/compass.py` has passing unit
tests, but `app/api/compass.py:59` calls `resolved_run()` first and `run_scan`'s self-heal recreates the
missing `ScannerRun`, so no request can ever observe it — and the self-heal is itself the "recompute"
that J-06 step 2 forbids. Test the state through the ACTUAL serving entry point before crediting it; a
green unit test on a branch no request can reach is an honesty gap, not coverage. (Found at iter-3 as
audit finding B2, still open at iter-26.)
**Applies to:** any journey whose acceptance names a specific served status/disclosure value; any change
to `resolved_run` / `snapshot_serving` / `run_scan` self-heal ordering; any future "the code handles X"
claim backed only by a unit test.

## iter-26 — 2026-08-28T14:31:00Z

**Verdict:** ESCALATE
**Lesson:** An earlier incident can make a journey's literal acceptance step permanently unprovable on
the live database. J-05 step 2 wants a frontier manifest reading `at_ingest / version 1 /
prospective_eligible true`; 2026-08-12's v1 is a legacy pre-freeze row, v2–v6 were regenerated during the
incident window and are AG-17-correctly ineligible forever, and AG-9 forbids fetching a new trading day —
so that state can never exist again here. The correct resolution is route-level fixture proof plus an
explicit assumption-ledger entry, NOT holding the journey open forever (that is the framework's #1
anti-pattern, an unsatisfiable acceptance criterion looping).
**Applies to:** any journey step whose premise depends on the frontier/newest date; any evaluator deciding
whether fixture evidence may substitute for a live observation.
