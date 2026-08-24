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

## iter-8 — 2026-08-21T13:55:00Z

**Verdict:** CONTINUE
**Lesson:** A cross-source agreement gate can return a *perfect* score because both sides are
secretly the SAME source. J-10's gate reported 20/20 `agree`, 88/88 pairs bit-identical, bridge
factor exactly 1.0 — which reads as overwhelming confirmation and is actually a tautology: the
committed Stooq seed ends 2026-07-01, so the "stored" side of the 2026-08-04..08-10 comparison
window is Yahoo (`data_provider_runs`: seed 508 / yahoo 34 / stooq 1, and that one stooq run is
id 541, `status='failed'`, `symbols_ok=0`). Suspiciously clean output is a provenance question, not
a success. Before trusting any agreement/convention/parity check, verify the PROVENANCE of both
sides independently of the numbers — a zero delta is equally consistent with "they agree" and with
"you compared a thing to itself".
**Applies to:** any iteration adding or citing a cross-vendor / cross-source / A-vs-B agreement
check, anything touching `j10_recovery.py`'s convention gate, and any future work that reads the
`daily_prices` history across the 2026-07-01/07-02 seed boundary (a real, never-examined vendor
discontinuity lives there).

## iter-8 — 2026-08-21T13:56:00Z

**Verdict:** CONTINUE
**Lesson:** Fixing the depth arbiter did NOT fix the forbidden lane. The iter-6/iter-8 quarantine
notes both blamed the `Depth: full → lean` demotion (lean auto-enables
`CHAIN_LEAN_PARALLEL_BROWSER_QA`), and a framework fix landed at `046dd956`. Then
`depth-dispatched` read `full` and the deterministic J-01/J-04 replay ran anyway at 12:54, inside
the very re-dispatch commissioned to add the missing audit lane — starting a frontend and attempting
a backend on the host that froze on 2026-08-20, and overwriting AG-17-protected quarantined evidence.
`docs/goal.md`'s Loop-mechanics lane gate is prose the engine has never been able to read; depth is
not the lane control. Any goal-level "no lane may run" rule needs its own enforcement point, and the
evaluator must check the lane actually stayed shut rather than trusting a prior remediation note
(the reviewer's "already remediated" line was written before the recurrence and is wrong).
**Applies to:** every remaining market-compass iteration while the lane gate is open (J-10's 567-symbol
continuation, all of J-11), and any goal whose `docs/goal.md` forbids a pipeline lane rather than a
code path.

## iter-9 — 2026-08-23T13:05:00Z

**Verdict:** CONTINUE
**Lesson:** A summary statistic of the form "all N were X" is exactly where the single counter-example
gets erased — and the counter-example is always the row that actually needed review. The iter-9 handoff
reported `bridge_factor == 1.0` for all 566 agreeing symbols; the persisted evidence artifact records
`AVB` at `2.7930001225759193`, and AVB's two rows are the ONLY values in the 1,170-row batch produced by
the bridge arithmetic at all (structurally confirmed: they are the only two whose OHLC values are not
float32-exact). The safety argument the handoff built on "all 1.0 ⇒ same-vendor tautology ⇒ no scale
break possible" was therefore false for precisely the one symbol where a scale break was possible. When
a handoff states a uniform value across a population, open the per-row artifact and query for
`!= that value` before accepting it.
**Applies to:** any iteration whose acceptance rests on a population-wide uniform figure (all bridge
factors, all hashes equal, all deltas zero, 100% coverage) — especially J-11's "all 11 rebuilt runs share
the frozen engine_identity" and its cache-invalidation proofs.

## iter-9 — 2026-08-23T13:05:00Z

**Verdict:** CONTINUE
**Lesson:** The reviewer and QA both re-stated the developer's framing verbatim (`issues: []`, TC-2 row
"all 1.0") on the one fact that was wrong, while independently re-running tests and re-querying row
counts that were right. Re-deriving *counts* is not re-deriving *claims*: the two lanes checked what the
handoff pointed them at and inherited its interpretation of what those numbers meant. Only the audit lane
re-derived the claim from primary sources. This is the third consecutive iteration (7, 8, 9) where the
audit caught something both earlier lanes missed — treat "reviewer PASS + QA PASS" as evidence about
mechanics, never about narrative.
**Applies to:** any iteration where full depth is optional; and specifically J-11, whose acceptance is a
long list of narrative claims ("no stale cache survives", "no new historical manifest appears") that a
row-count check cannot confirm.

## iter-10 — 2026-08-23T13:36:00Z

**Verdict:** STALLED
**Lesson:** A "schema contract proven by fixture-DB tests" can be fully green and still be false on the
production database: `apps/backend/app/models.py`'s FK-declaration drop makes the manifest↔run contract
true for any DB built from current SQLModel metadata, while the live `next_session_manifests` DDL still
carries `FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)` with `PRAGMA foreign_keys=0` and 12
standing `foreign_key_check` violations. Both the reviewer and QA recorded that DoD item complete on the
strength of the passing fixture tests; only the auditor queried the live DDL. Second, smaller edge from
the same iteration: `compass.basis_disclosure`'s `if not row.generation_json: return {"status":
"available"}` short-circuit (`compass.py:1108-1109`) fabricates an honest-looking state on 10 of 24 live
manifests — the degenerate input that bites is "row exists but records no basis", not "no row at all",
and the TC-5 orphan test covered only the latter.
**Applies to:** any iteration whose acceptance items say "the LIVE schema/database" — verify against the
live artifact (`sqlite_master`, `pragma_foreign_key_check`) and not only against a metadata-built fixture;
and any fail-closed read path, where the missing-field branch deserves its own test alongside the
missing-row branch.

## iter-11 — 2026-08-23T23:45:00Z

**Verdict:** REGRESSION
**Lesson:** A SQLite "drop a constraint" rebuild has TWO possible sources of truth for the replacement
table — the captured live DDL and the ORM model — and they are not the same object. `create_shadow_table`
(`apps/backend/app/engine/j11_schema_migration.py:172-192`) captured the live DDL with `fetch_object_ddl`,
reissued the captured INDEXES verbatim, and then built the TABLE from `NextSessionManifest.__table__`,
so every difference between the live table's accumulated history (`app/db.py::_COLUMN_ADDS`
server-side `DEFAULT`s, original column order) and the model's shape silently rode along with the one
authorized change. The developer caught two consequences of that choice (four spurious indexes, a
duplicate autoindex) and guarded them with a test — proof they were reasoning about exactly this class
of drift — but never asserted the `CREATE TABLE` body itself was otherwise unchanged, so the reviewer
and QA both re-verified only "the FK clause is gone" and the delta reached the live 7.8 GB database.
**Rule for next time: a bounded schema migration must diff the whole pre/post `CREATE TABLE` text as an
acceptance item, not just assert the absence of the one clause it set out to remove — and rebuild from
what it captured, not from a second source of truth.**
**Applies to:** any iteration performing a table rebuild/migration on a live SQLite database, any work
touching `apps/backend/app/engine/j11_schema_migration.py` or `app/db.py`'s additive-schema path, and
any acceptance item phrased as "removes X and nothing else".

## iter-12 — 2026-08-24T14:45:21Z

**Verdict:** STALLED
**Lesson:** The deterministic goal-edit-drift alarm is narrower than it looks. `goal_gate.py
hash-journeys` computes J-10's `spec_hash` over only the TAIL of its block — I probed `docs/goal.md`
line by line and perturbations at lines 590-880 leave the hash byte-identical while 890-938 change it.
The cause looks structural: J-10 contains a nested bullet (`    - **J-10 CLOSED — residual set
accepted…`, line ~879) whose text starts with the same `- **J-<NN>` shape the block extractor treats as
a journey heading, so both the hasher AND the goal slicer latch onto it (the iter-12 slice lists the
J-10 digest line twice for exactly this reason). Consequence: the owner's 2026-08-24 edit to J-10 step
2d produced NO `journeys-changed.md`, so a recorded pass carried forward across changed goal text with
no alarm. Harmless here — the edit only annotates a spent instruction as historical, and I re-derived
J-10 from the live database anyway — but the rail is not the safety net an evaluator assumes it is.
**Applies to:** any evaluator carrying a `passing` journey forward on the absence of
`journeys-changed.md`, and any goal whose journey block contains nested `- **J-NN` bullets (this file
now has one in J-10 and the same shape could appear anywhere) — diff `docs/goal.md` against the
iteration snapshot for the journey's own line range instead of trusting the hash alone.

## iter-12 — 2026-08-24T14:45:22Z

**Verdict:** STALLED
**Lesson:** "Zero live writes" was proven this iteration by a before/after fingerprint pair that
bracketed only 101 seconds of a 90-minute iteration (`j11-stage-b1-cleanup-fingerprint-diff.json`:
before 10:50:08Z, after 10:51:49Z; `status.json` `started_at` 10:25:29Z) — the auditor caught the
overclaim (T2) and the dev handoff's "run once at the START and once at the END" wording was simply
false. The claim survives only because a much cheaper instrument is stronger: the SQLite main-file
mtime (1787522416 = 2026-08-23 23:00:16, iter-11's own last write) plus a 0-byte write-ahead log proves
no committed write reached the file by ANY route across the whole iteration, without a purpose-built
capture at all. In WAL mode both halves are needed: an uncheckpointed write hides in the `-wal` file
(main mtime unchanged), and a checkpoint would move the main mtime — so mtime-unchanged AND WAL-empty
together are conclusive, while either alone is not. The `-shm`/`-wal` mtimes move on any read-only open
and are NOT evidence of a write.
**Applies to:** any iteration claiming zero writes to `apps/backend/data/trendora.db` — J-11 Stage C's
mutation accounting above all, and any future maintenance-isolation iteration. Record the file mtime +
size + WAL size at the true start and end, and treat a purpose-built fingerprint pair as corroboration,
never as the primary instrument.

## iter-13 — 2026-08-24T19:35:00Z

**Verdict:** STALLED
**Lesson:** A "frozen" identity is only frozen against the world, not against yourself: iteration 10
froze `engine_identity=6261ca17…`, then iterations 11 and 12 edited `apps/backend/app/engine/compass.py`
— one of `config.yaml`'s three `provenance.engine_files` — and iteration 13's re-derivation returned
`53d2ffd1…` (I recomputed it independently). The repair's own safety fixes silently invalidated the
repair's own baseline. Worse, the preflight comparison gate (`app/engine/j11_stage_c.py:264-334`)
CAPTURED both identities and never COMPARED either — 11 checks, none touching
`stage_c_attempt_identity` — so the drift was invisible to the developer, reviewer and QA and only the
auditor caught it. Capturing an invariant's value is not checking it, and a gate that cannot compare
(iteration 12's certified artifact records no identity at all) is a gate that always passes.
**Applies to:** any iteration that freezes an identity/fingerprint for a multi-iteration attempt —
especially J-11 Stage D, whose whole correctness claim is "all 11 rebuilt runs share ONE frozen
identity"; and generally to any preflight/gate artifact: for every field captured, state whether it is
compared, and against what.

## iter-13 — 2026-08-24T19:36:00Z

**Verdict:** STALLED
**Lesson:** A bounded delete's strongest proof is not the count that moved but the counts that did NOT.
Against iteration 12's COMMITTED baseline, exactly 5 of 24 tables moved and by exactly the pre-declared
amounts, 19 were identical, no table appeared or vanished, and residue for the deleted run ids was 0 in
all four child tables — and because Stage C issues no INSERT on any path (grep-verified: no INSERT,
UPDATE or `session.add` in the new module or script), delta == |enumerated set| AND residue == 0 proves
the removed set is exactly the intended set. A pre/post count pair alone could have masked a swap; this
combination cannot. Cheapest instrument in the whole check: the db file's mtime at the TRUE process
start equalled the prior iteration's own recorded "after" mtime, and the file still carries the
true-end mtime now — one `stat` proving the single authorized write was the only write.
**Applies to:** any future destructive maintenance iteration (J-11 Stages D/E/F), and any "we wrote
nothing" or "we wrote only X" claim on `trendora.db`.
