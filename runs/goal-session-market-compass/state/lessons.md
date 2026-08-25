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

## iter-14 — 2026-08-25T01:15:00Z

**Verdict:** STALLED
**Lesson:** A classifier whose vocabulary contains a label it can never emit has already decided. The
AVB diagnostic (`apps/backend/app/engine/j11_avb_diagnostic.py:159-267`) offers four labels including
`bridged+compensating` — the only one that could flag a volume problem — but no code path can produce
it, because the function never reads `volume` at all; it also reports `volume_a_equals_b: true` as a
finding when `volume_b` is literally assigned `stored_volume`. Both signatures — an unreachable branch
and a tautological assertion — are cheap to grep for and each one silently converted an untested half
of a question into a "proven" answer that four review lanes accepted.
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

## iter-15 — 2026-08-25T11:05:00Z

**Verdict:** STALLED
**Lesson:** A destructive repair can ARM a trap in code it never touched, by putting two layers out of
sync. Stage C emptied the derived layer for 11 dates but (correctly) left the raw price layer intact, so
`SELECT MAX(date) FROM daily_prices` is now `2026-08-12` — an incident date with zero `ScannerRun`s.
`main.py:100` calls `warmup.ensure_latest_snapshot` on **every** boot, which resolves that same
`latest_data_date` and calls `run_scan`, which on a missing run falls through to `persist_run_payload`.
So merely starting the backend now performs exactly the Stage D-class write the whole contract is
withholding authorization for, before any request arrives — and `GET /api/compass` on an incident as-of
additionally mints AG-12-immutable manifests for the 7 dates that have none. Both irreversible. Nothing
in the diff caused this; the *gap between* a cleared derived layer and an untouched raw layer did. Six
iterations of maintenance isolation have been the only thing preventing it, and that is an operator
convention, not a code guard.
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

## iter-16 — 2026-08-25T18:05:00Z

**Verdict:** STALLED
**Lesson:** A guard can be built, wired at the right call site, exhaustively tested and fully
passing, and still protect nothing — because its *state* was never registered.
`j11_preboot_guard.evaluate_boundary_for_date` correctly returns `blocked=False` on an empty
`maintenance_boundaries` table, `register_j11_incident_boundary` has no production caller, and the
table does not exist in the live DB at all — so the live boot path is exactly as unprotected as
before. Worse, the guard's own green tests
(`test_tc25_no_boundary_registered_is_a_true_noop`) are framed as "the common no-incident case"
while being a precise model of the unprotected live state, so nothing in the suite names the gap.
Ask of every new guard: *what is the live value of the state it reads, right now?* — the code's
correctness and the deployment's effect are separate questions.
**Applies to:** any iteration adding a guard/gate/feature-flag/quarantine whose behaviour keys on
persisted state (`apps/backend/app/engine/j11_preboot_guard.py`, `warmup.py`, and any future
boot-path or middleware check); also any "prove it on disposable test state" acceptance clause —
treat it as necessary, never sufficient.

## iter-16 — 2026-08-25T18:06:00Z

**Verdict:** STALLED
**Lesson:** Correcting the data invalidated a counterfactual that was written against the
pre-correction data, and nothing flagged it. `_build_bars_with_transformed_close` substitutes close
only unless `volume_override` is passed; that was coherent while stored volume was raw, but once the
AVB volume was corrected to the compensating scale, representation B silently became
provider-scale close × Trendora-scale volume — a hybrid matching no real state. Its fingerprint is
unmissable once looked for: A/B came out *exactly* `bridge_factor` on both dates. The spec itself
sanctioned dropping the override ("the write already landed, so read the corrected rows directly"),
which is why developer, reviewer and QA all passed it — but the override never fed representation A,
it fed B. After any state correction, re-derive every counterfactual's inputs; an exactly-round ratio
between a representation and its counterfactual is the signature of a one-sided rescale, not a finding.
**Applies to:** any iteration that mutates stored state which an existing diagnostic, A/B trace, or
counterfactual reads (`j11_avb_diagnostic.py`'s trace functions, `run_j11_iter16_stage_d_readiness.py`),
and any spec that tells an implementer to drop a substitution argument because "the real data now has
that value".

## iter-17 — 2026-08-25T21:05:00Z

**Verdict:** STALLED
**Lesson:** A test case can turn the MEASUREMENT OF AN OPEN DANGER into a green checkbox, and every
downstream lane will inherit that framing without lying. TC-11 was specified as "the live guard returns
`blocked: False` → PASS", but on the live DB `blocked: False` IS the exposure: `max(daily_prices.date)` is
`2026-08-12`, an incident date with 0 `scanner_runs`, and `main.py`'s `create_db_and_tables()` runs BEFORE
`ensure_latest_snapshot()`, so one boot both mints the owner-forbidden `maintenance_boundaries` table and
writes a `ScannerRun` onto that quarantined date. Dev handoff, review and QA all recorded the pass; none
stated what it means. When a spec's expected value for a safety probe is the UNSAFE value, the test case
must require the artifact to state the consequence in prose, not just record the boolean.
**Applies to:** any iteration whose spec asserts an expected value for a probe of a KNOWN-BROKEN or
quarantined condition — especially `runs/**/j11-*verification*.json`-style evidence and any future
"confirm the guard is not armed / confirm X is still absent" check.

## iter-17 — 2026-08-25T21:05:00Z

**Verdict:** STALLED
**Lesson:** A cross-check whose inputs are both derived from the correction being checked cannot fail. TC-13
asked for an A/B dollar-volume ratio "within relative tolerance of 1.0", but
`ratio = (close_a·volume_a)/((close_a/bf)·volume_b)` cancels `close_a` entirely and reduces to
`volume_a·bf/volume_b` — and `volume_a` was DEFINED by iter-16 as `round(provider_volume/bf)`. I confirmed
`round(provider_volume/bf)` equals the stored volume exactly on both dates, so the ratio was algebraically
pinned to ≈1.0 before anyone ran it, and it reproduces iter-16's own `dollar_volume_ratio_after` digit for
digit. Before specifying a numeric tolerance check as evidence, substitute the definitions of its inputs and
confirm the quantity can actually come out wrong.
**Applies to:** any future J-11/AVB Stage-D readiness or verification spec proposing a ratio/tolerance
assertion over values in `j11_avb_diagnostic.py` / `j11_avb_correction.py`, and any "independent
cross-check" claim in `runs/goal-market-compass-iter-*/j11-*.json`.
