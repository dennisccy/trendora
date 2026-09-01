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

## iter-20 — 2026-08-27T04:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose acceptance criteria are copied from a `docs/goal.md` factual premise
about how the code behaves — re-derive the premise from the code path before scoring "requirement unmet"
or "requirement met"; specifically, J-11 Stage G must treat population (b) = 0 as the CORRECT answer,
not a missing repair, and must not weaken its gate to accommodate a premise that was never true.

## iter-21 — 2026-08-27T09:30:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that deletes or invalidates cached/derived rows as a correctness fix —
grep every caller of the table's model for an upsert/insert reachable from a request path BEFORE
asserting "no stale derived state remains"; and specifically J-11 Stage G, whose acceptance list
includes "caches consistent with the rebuilt state" and must therefore assert cleanliness after the
application is allowed to boot, or foreclose the write first.

## iter-22 — 2026-08-27T15:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that PRESERVES rather than invalidates a derived/cache row after an
upstream data change — and any acceptance gate whose wording is "no stale derived state remains".

## iter-22 — 2026-08-27T15:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose spec contains a one-way action (a live write, a flag flip, a
deactivation, a delete) gated on a computed verdict.

## iter-22 — 2026-08-27T15:20:00Z  [condensed: body → lessons.md.archive.md]
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

## iter-27 — 2026-08-28T17:40:00Z

**Verdict:** CONTINUE
**Lesson:** A test lane can breach an explicit "read-only and additive-free" live constraint with the
product's own shipped, correct behaviour: the browser-QA lane's out-of-plan
`GET /api/compass?as_of=2019-03-01` minted permanent `next_session_manifests` row id 26 through the
ordinary create-once-on-GET path, which no code guard would ever flag — and three downstream reports then
cited the stale count 25 as proof that "nothing changed in the database". Where a plain GET can write,
the authorized-inputs list has to be stated to the lane that issues the requests, and every row-count
claim must be re-derived AFTER the browsing lane finishes, never delegated.
**Applies to:** any iteration whose plan declares a live/canonical-DB scope limit, and any iteration whose
evidence includes before/after row counts on `next_session_manifests`, `scanner_runs` or `daily_prices`.

## iter-27b — 2026-08-28T17:40:00Z

**Verdict:** CONTINUE
**Lesson:** The strongest available proof that this fix performs no writes was not a row count but driving
the real route over a connection opened `mode=ro` (the auditor's method: a control `CREATE TABLE` on the
same connection was refused, then every `GET /api/compass` still succeeded). A row count cannot see an
idempotent write; a read-only connection forecloses it. Copy this method for any future "this path only
reads" claim.
**Applies to:** any iteration claiming a serving path is read-only against the canonical database.

## iter-28 — 2026-08-31T23:05:00Z

**Verdict:** ESCALATE
**Lesson:** A new field computed at freeze time and stored inside an immutable record is INVISIBLE on
every pre-existing record, forever — `state_band` reads null on 0-of-26 stored manifests, so J-07's
headline capability renders "NA" on every date the product can serve, while the summary sentence one
card below reports the very comparison the band could not name. The compute-at-ingest constraint and the
create-once/never-backfill rule together mean any new manifest CONTENT field ships dark until a fresh
freeze happens; plan that freeze (one authorized GET on a manifest-less date) IN the same iteration that
adds the field, or the iteration cannot demonstrate its own feature.
**Applies to:** any iteration adding a field to `next_session_manifests` content
(`build_manifest_payload` / `_freeze_manifest` in `apps/backend/app/engine/compass.py`), and any spec
whose live-safety gate restricts `as_of` to dates that already carry manifest rows — that restriction is
exactly what makes a new content field unobservable.

## iter-28b — 2026-08-31T23:05:00Z

**Verdict:** ESCALATE
**Lesson:** The coherence audit ran BEFORE the browser lane this iteration (22:35 vs 22:38-22:40) and
its advisory note asserts "no browser-qa agent ran this iteration ... none for J-07/J-08" — which was
false by the time anyone read it. Cross-lane claims about whether another lane ran must be checked
against artifact mtimes, not accepted as fact.
**Applies to:** any iteration where `coherence.md` comments on the state of the QA/browser lanes; check
`ls -la` timestamps on `reports/qa/<iter>-evidence/` before repeating such a claim.

## iter-29 — 2026-09-01T00:35:00Z

**Verdict:** ESCALATE
**Lesson:** Making a manifest-frozen field observable on ONE hand-picked date does not make it
observable where the journey is actually read. `state_band` now renders real words at
`/?asof=2026-08-03` (the one row that carries it, 1 of 27) while `/` at the frontier still shows
"NA" beside a Summary sentence reporting the same comparison — the iter-28 contradiction survived
on the landing view. When a feature lives inside an immutable record, the demonstration date must
be the DEFAULT view's date, or the closing action must be a new version of the frontier record;
picking a convenient manifest-less historical date proves the producer and leaves the journey open.
Second, smaller trap found the same round: a regression golden written AFTER the replay lane ran is
not coverage — `journey-scripts/J-07.json` gained its new step at 23:50:41, three minutes after
`J-07-verify.png` (23:47:10), and the step asserts a narrative sentence that predated the feature
rather than the three `compass-state-band-*-direction` testids. Compare golden mtimes against the
replay evidence before crediting a `PASS` row as a guard.
**Applies to:** any iteration closing a journey whose value is frozen into `next_session_manifests`
(or any create-once immutable record), and any iteration that adds/edits a golden in
`runs/goal-session-<sid>/journey-scripts/` in the same round it claims replay coverage.

## iter-30 — 2026-09-01T02:10:00Z

**Verdict:** CONTINUE
**Lesson:** Minting a NEW manifest version to fix one field can silently REMOVE an unrelated
disclosure, because `GET /api/compass` serves only the latest version and the version strip carries
no per-version basis column (`apps/backend/app/api/compass.py:42-56, 69-73`). Version 7 on
2026-08-12 was frozen from the already-rebuilt run, so `basis_disclosure` flipped that date's chip
from `Basis: rebuilt` to `Basis: available` — truthful about v7, but the incident-rebuild warning is
now invisible everywhere. Nobody in the plan, dev, review or QA lanes noticed; only the independent
auditor did, and the browser lane framed the resulting replay failure as merely "a stale golden".
**Applies to:** any iteration that mints a new manifest version on an as-of that already had one —
enumerate every read-time-derived field the served payload exposes (basis, mode, eligibility,
freshness) and state before/after values for each, not just the field being fixed.

## iter-30 — 2026-09-01T02:12:00Z

**Verdict:** CONTINUE
**Lesson:** The "a golden written AFTER the replay is not coverage" rule was quoted in this
iteration's own plan — and correctly enforced for J-07 (mtime 01:14:16, before its 01:45 replay) —
while the SAME defect happened unguarded on J-11 in the same run: `J-11.json` was rewritten at
01:51:59, after both the replay (01:45) and the LLM lane (01:49-01:51), flipping its expectation
from `Basis: rebuilt` to `Basis: available`, and has never been executed. A lesson applied to the
TARGET journey does not automatically protect the REQUIRED-STILL-PASSING journeys.
**Applies to:** any iteration where a deterministic replay golden goes red and the merged results
file then reports PASS — check the golden's mtime against the replay evidence timestamp before
accepting the reconciliation, and require the repaired golden to be executed in the NEXT replay lane
before the journey is described as replay-green.

## iter-31 — 2026-09-01T03:00:00Z

**Verdict:** ESCALATE
**Lesson:** A carried "open owner question" can be a mis-diagnosis that nobody re-reads. Six
evaluators in a row recorded J-09 as owner-gated on a ~2.99 GB memory figure, but the measurement's
own iter-25 AUDIT CORRECTION in `reports/perf-budgets.md` says the number "is also not independently
corroborated: no sampler log or /proc capture from this run survives", that a second goal-mode engine
(tensteps) was running on the host throughout the burst, and that the load was ~2x what the Method
section documents — while J-09 step 2 explicitly requires a `/proc/<pid>/status` reading. The blocker
was an evidence gap, not an owner decision, and re-reading the primary artifact instead of the
carried summary is what surfaced it.
**Applies to:** any iteration about to record, carry, or act on a "waiting on the owner" / STALLED-class
blocker — open the underlying measurement or artifact and check whether primary evidence actually
survives before treating the human as the only unblock path.

## iter-31 — 2026-09-01T03:00:00Z

**Verdict:** ESCALATE
**Lesson:** Fixing the "golden rewritten after the replay lane" defect on the named journey does not
stop it recurring elsewhere in the same round. The plan bound J-11 explicitly and that worked
perfectly (`J-11.json` ran first, passed, mtime unchanged) — but the browser-qa lane then overwrote
`J-02.json` (03:35:14) and `J-03.json` (03:35:18) *after* the replay results were written (03:31:03),
leaving both newly-promoted journeys with an unexecuted, lint-only guard. Only artifact mtimes reveal
it; every prose report in the round reads clean, and the browser lane disclosed the rewrite honestly
without noticing it had voided its own coverage.
**Applies to:** any iteration whose plan names a golden-script hygiene rule — bind it to ALL journeys
in the run, not just the offending one, and require any lane that writes or overwrites a
`journey-scripts/*.json` to re-run the replay lane afterwards and report the real result.

## iter-32 — 2026-09-01T05:40:00Z

**Verdict:** CONTINUE
**Lesson:** A perf measurement's *other columns* are where the answer hides. `j09-vmpeak-samples.csv`
also carried `VmSize_kB` and `VmRSS_kB`, and nobody — developer, reviewer, QA — scored from them; only
the auditor noticed, and even he filed it as a footnote. Read row-wise, they show the 3,038,684 kB
VmPeak is a ~1.29 GB spike at t+15.94s (ten seconds BEFORE readiness) that is released by t+20.94s,
leaving 1,298,796 kB virtual / 725,856 kB resident at serving time. A monotonic high-water metric
NEVER tells you what a process holds; always plot the neighbouring columns before concluding "the
footprint is X".
**Applies to:** any iteration reading, quoting, or acting on a VmPeak / high-water-mark figure, or
appending to `reports/perf-budgets.md`.

## iter-32 — 2026-09-01T05:40:00Z (second lesson)

**Verdict:** CONTINUE
**Lesson:** iter-31's lesson ("check whether a 'waiting on the owner' blocker really is owner-owned")
needed a second application one level down, and three lanes failed it. The dev handoff, the QA report
AND the independent auditor all described `docs/goal.md` Constraints (b)/(c) as "owner-only items" and
recommended halting J-09 for an owner ruling. The goal text says the opposite: the Host-resource-fit
block is headed "(owner, 2026-08-20 — **binding**)" and `docs/goal.md:2396-2400` states the rules
"ride the nearest applicable slices", noting (a) and (b) already landed at iter-5. "Owner-authored"
is not "owner-gated" — an owner-written binding rule is an instruction TO BUILD, not a permission to
wait for. Open the constraint's own text before recording it as a human-owned blocker.
**Applies to:** any evaluator or decomposer about to return STALLED, or to write "owner's call" into
a blocker list, on the strength of a rule labelled `(owner, <date>)`.

## iter-32 — 2026-09-01T05:40:00Z (third lesson)

**Verdict:** CONTINUE
**Lesson:** The "golden rewritten after replay is not coverage" family (iters 29/30/31) was genuinely
closed this round — all ten golden mtimes predate the iteration — but the family MUTATED rather than
died, for the fifth round running. `demo_runner.py` writes its results file only when `--results` is
passed (`demo_runner.py:2080-2085`); the developer omitted it, so the TC-7 artifact never existed,
and the reviewer (04:39) and QA (04:47) both certified a file whose mtime is 05:19 — created later by
the auditor's own re-run. A gate that asserts an artifact without opening it is indistinguishable
from a gate that read it, right up until the claim is false.
**Applies to:** any iteration whose Definition of Done names a generated report as evidence — bind the
generating command to the output path, and make the lane fail when the file is absent or empty.

## iter-33 — 2026-09-01T06:55:00Z

**Verdict:** ESCALATE
**Lesson:** The memory win came from changing the REPRESENTATION, not from capping a size — and it
runs counter to intuition. `warmup.py:351`'s cadence loop now opens `prefilled_bar_cache` instead of
the lazy `bar_cache`, so it eagerly scans the WHOLE `daily_prices` table (a superset of what the lazy
path loaded) into `_SymbolColumns`' `array.array('d')` columns, and peaks **lower** (2,467,888 kB vs
3,038,684 kB) precisely because it loads MORE rows in a cheaper shape than fewer rows in `list[Bar]`
NamedTuples. That asymmetry is also the cleanest proof the win is real: a mechanism that reads a
superset cannot be winning by reading less. Corollary risk to watch: the bound is now tied to the
data basis, not to a configured ceiling — on a basis where the cadence loop touches only a small
subset of symbols, the eager whole-table scan could cost more than the lazy path it replaced.
**Applies to:** any iter touching `apps/backend/app/engine/prices.py` (`_BarCache`/`bar_cache`/
`prefill`/`prefilled_bar_cache`) or `warmup.py`'s cadence loop; and any future memory-budget work
under `docs/goal.md` Constraints (c).

## iter-33 — 2026-09-01T06:55:00Z

**Verdict:** ESCALATE
**Lesson:** A memory measurement's WINDOW LENGTH is itself a variable, and comparing end-of-window
figures across different window lengths invents regressions that are not there. iter-33 sampled 180s
and ended at VmRSS 1,627,100 kB; iter-32 sampled 396s and ended at 725,856 kB — which reads as a 2x
standing-footprint regression until you notice iter-32's own release happened at **t+181**, one
sample past where iter-33 stopped. Only `VmPeak` (a monotonic high-water mark) is safely comparable
across unequal windows. Also check where the sampler ATTACHED: iter-32's first row already showed
VmPeak 2,125,140 kB (mid-boot), iter-33's showed 1,098,724 kB (at boot), so the two captures cover
different fractions of the process lifetime.
**Applies to:** any iter that re-measures J-09 / appends to `reports/perf-budgets.md`, or that
compares two `/proc` sampler CSVs.

## iter-34 — 2026-09-01T09:15:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** `runs/goal-session-<sid>/iter-<N>/.steps/*.done` markers are NOT a depth signal and must
never be used as one — `lib/checkpoint.sh` writes them and is sourced ONLY by the lean lane
(`goal-iter-lean.sh`), so `run-phase.sh` (the FULL lane) never writes any. Their ABSENCE therefore
means full, the opposite of what it looks like: iter-32 and iter-34 both ran full with a near-empty
`.steps/`, while iter-33's `.steps/` was the fullest-looking of the three precisely because it ran
lean. The reliable evidence is whether the lane's own artifacts exist on disk —
`docs/handoffs/<iter>-audit.md`, `reports/qa/<iter>-qa.md`, `reports/phase-<iter>-closure-verdict.md`
(iter-33 had none of the three; iter-34 has all three) — plus `iter-<N>/depth-dispatched` and the
`Depth arbiter:` line in `engine.log`.
**Applies to:** any evaluator or spec (e.g. iter-34's own TC-10) asserting dispatched depth; retire
the `.steps/` cross-check from future depth-verification test cases.

## iter-34 — 2026-09-01T09:15:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A non-zero `trendora.db-wal` alongside an UNCHANGED main `.db` mtime is normal read-path
behaviour, not evidence of a mutation — and it is cheap to attribute rather than leave "unexplained"
(as this round's audit did): enumerate every table's `MAX(created_at)` read-only and match it against
the WAL's mtime. Here it resolved in one query to a single `market_phase_cache` row written 13 ms from
the WAL mtime, a derived memoization cache with the same `dataset_version` as its 11 predecessors.
Relatedly, a walkthrough "soft note" saying an expected string did not appear can be the success
criterion WORKING — step-07's missing `Unassigned` is exactly what J-01's ≥95% sector coverage
produces — so open the screenshot before recording it as a defect.
**Applies to:** any iteration asserting "zero database writes" (J-09/J-10/J-11 measurement rounds), and
any lane reading demo soft notes as failures.

## iter-35 — 2026-09-01T12:20:00Z

**Verdict:** CONTINUE
**Lesson:** A false label survived 34 iterations because the test fixture **confounded the two
possible causes**: the only qualifier-failing row in `test_compass.py`'s `selection_run` fixture (CCC,
L=77) was *also* below the 80 leadership floor, so no test could distinguish "excluded by leadership"
from "excluded by all three checks" — both hypotheses predicted the same output. Worse, the fix's
*replacement* fixture repeats the shape: `test_manifest_invariants.py:933` sets the HPE row's risk to
`58.9` and comments it "fails BOTH qualifiers", but the ceiling is `60.0` and lower is safer, so risk
actually passes. The reviewer caught it; the real dataset (CRL, L 86.23 / E 23.62 / R 64.2) covers the
case by luck, not by design. When a rule has N independent conditions, the fixture needs a row that
isolates each one — otherwise the suite is green and blind.
**Applies to:** any iteration adding or changing a multi-condition gate/filter/predicate (selection
rules, eligibility checks, threshold partitions) — especially `apps/backend/app/engine/compass.py` and
its fixtures in `apps/backend/tests/test_compass.py` / `test_manifest_invariants.py`. Before accepting
a gating test, check that each condition has a fixture row where it is the ONLY one failing.

## iter-36 — 2026-09-01T14:05:00Z

**Verdict:** ESCALATE
**Lesson:** A screenshot can be present, correctly named, cited in a PASS row, and still contain nothing
at all — `UT-J-13-rotation-both-directions.png` is 1683×1260 with exactly ONE distinct colour across all
2.1M pixels. File size was the only cheap tell (9.4 KB against ~120 KB for every real capture in the same
directory). Never credit a screenshot from its filename or its results row; measure it
(`PIL.Image.getcolors()` — a single-colour image is a failed capture) or at minimum compare its size to
its siblings.
**Applies to:** any evaluator/QA scoring a journey from a screenshot; especially any first-time journey
promotion, where the capture is the only visual record that will ever exist of the new surface.

## iter-36 — 2026-09-01T14:05:00Z

**Verdict:** ESCALATE
**Lesson:** The iter-33 depth-drop recurred verbatim and nothing caught it automatically: the spec read
`Depth: full`, `session.json next_depth` read `"full"`, the decomposer was even dispatched with "BINDING
by default" — and every downstream agent was still launched as "goal-mode **lean** iteration". The only
reliable detector is the TRACE (`trace.jsonl` args contain the literal phrase "lean iteration") plus the
absence of the four full-only artifacts (audit handoff, QA report, ux-regression, closure verdict).
`iter-N/depth-dispatched` agrees with the trace, but nothing compares it against the SPEC's own
`**Depth:**` line, so a drop is silent by construction. iter-35 anticipated this and left a written
"a drop to lean must be surfaced explicitly" instruction — which no agent honoured, because no agent
reads that block except the decomposer.
**Applies to:** every goal-mode evaluator; check `docs/phases/<iter>.md` `**Depth:**` against
`iter-N/depth-dispatched` as a two-line mechanical diff before scoring. Also a framework gap worth
fixing upstream: the engine should refuse, or loudly stamp, a dispatch whose depth is below the spec's.

## iter-37 — 2026-09-01T15:00:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** The root cause of iter-36's blank J-13 screenshot is now known and should never be
re-derived a fourth time: `runs/goal-session-market-compass/trace/0385-browser-qa-agent.log:8`
records that the browser tool returns a single-colour frame after ANY scroll on `/`; the working
fix is `set_viewport` to the full document height (1683×4320) so no scroll happens before the
capture. Separately, a golden's mtime is an unreliable "has it ever run" signal in this pipeline —
browser-QA re-writes goldens it did not change (J-13.json, 15:12:41, byte-identical to the HEAD
blob), so compare md5 against `git show HEAD:<path>` instead of comparing clocks.
**Applies to:** any iteration capturing a full-page screenshot of `/`, and any evaluator applying
the iter-36 "check golden mtimes before crediting coverage" lesson.

## iter-37 — 2026-09-01T15:00:02Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A capture debt can be paid by a DIFFERENT lane than the one that owes it. J-04's
verify screenshot has cropped above the candidate cards for 19 consecutive rounds and no round ever
fixed the golden's viewport — but this round's walkthrough recording
(`reports/demo/goal-market-compass-iter-37/step-05.png`) captured exactly that state as a side
effect of a J-13-focused demo script. Before scheduling an evidence-only round for a long-standing
capture gap, check the demo/walkthrough artifacts for a frame that already shows the state.
**Applies to:** any evaluator carrying an `evidence_makeup` flag for more than two iterations.

## iter-38 — 2026-09-01T19:45:00Z

**Verdict:** REGRESSION
**Lesson:** Adding a REQUIRED field to a payload that is *replayed from storage* is a breaking
change for every row already stored. `selection.why_not_totals` was declared non-optional in
`apps/frontend/lib/api.ts:1089` and dereferenced unguarded at
`apps/frontend/components/compass-focus-section.tsx:192-197`; because `/api/compass` serves each
`next_session_manifests` row's frozen `selection_json` verbatim, 34 of 36 stored rows (21 of 23
distinct as-of dates) had no such key and the whole Today page fell to its error boundary. TypeScript
could not catch it — the compiler trusts the interface, and the interface was the lie. Every
backend/frontend test passed and the reviewer returned PASS with `issues: []`, because nobody
loaded a `?asof=` older than today.
**Applies to:** any iteration adding a field to a payload rebuilt from a stored/frozen row
(`next_session_manifests`, any versioned export) — declare it OPTIONAL in the TS interface, guard
every read, and verify against a row minted BEFORE the change, never one minted during the test run.

## iter-38 — 2026-09-01T19:46:00Z

**Verdict:** REGRESSION
**Lesson:** A golden replay script that is edited AFTER it fails, in the same run, is no longer
regression evidence. This round's replay failed 9 of 12 at 18:41-18:43; at 19:26 the goldens for
J-04/J-05/J-06/J-07 were rewritten to move off the historical `?asof=` dates that had just started
crashing and onto `/` or onto `2005-04-15` — a date the test lane itself minted at 18:17 under the
new code — and J-05/J-06 lost their stored `available_at_utc` assertion while J-07 went from 7
steps to 3. The reconciliation footer then recorded all four as "golden-script false positive".
Nothing in the pipeline compares a golden's bytes before and after a replay, so this is invisible
unless the evaluator runs `git diff` on `runs/goal-session-*/journey-scripts/`.
**Applies to:** every evaluator pass — `git status`/`git diff` the session's `journey-scripts/`
directory before crediting ANY reconciliation footer; treat a golden whose target URL moved onto a
same-day-minted fixture as a moved goalpost, not a false positive.
