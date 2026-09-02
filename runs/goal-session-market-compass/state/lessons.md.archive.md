# lessons.md — archive

Entries moved out of `lessons.md` by scripts/automation/lib/condense.sh (maintenance protocol §4).
Append-only: nothing here is ever deleted or rewritten.

<!-- condense.sh 2026-08-21T11:39:28Z: moved 5 entries (keep-iters=5) -->

## iter-0 — 2026-08-19T22:30:56Z

**Verdict:** CONTINUE
**Lesson:** The engine reported "product diff this iteration: non-empty" at a zero-code-change
baseline — the diff was the owner's three `docs/goal.md` authoring commits (b01f90e4, 4c676a73,
21e97a44), not iteration output, because `iter-0/snapshot-sha` was empty and the scanner fell
back to `HEAD~1`. Always confirm attribution with `git diff <base>..HEAD --name-only` before
treating a non-empty diff as work the iteration performed.
**Applies to:** any baseline (iter-0) evaluation, and any iteration whose `snapshot-sha` file is
empty or whose scan-report scope reads "changes since HEAD~1".

## iter-0 — 2026-08-19T22:30:56Z (evidence quality)

**Verdict:** CONTINUE
**Lesson:** Four journeys (J-02, J-03, J-04, J-07) were evidenced by one byte-identical
above-the-fold capture of `/` (md5 `9dfcc1cf…`), which shows the legacy Dashboard but cannot by
itself prove the six missing compass sections; the absence claims only held up because the
results file recorded `document.body.innerText` sweeps and the code check confirmed no compass
module exists. Absence-of-feature claims need a text sweep or a code citation, not just a
screenshot of a page that lacks the feature.
**Applies to:** any iteration scoring journeys as failing because a section/page is missing,
especially baselines where several journeys share one page.

## iter-1 — 2026-08-20T05:04:26Z

**Verdict:** CONTINUE
**Lesson:** Browser QA tested a STALE backend: the dev/audit code was on disk but the running
uvicorn process (:8255) predated it, so UT-07/UT-J-01 reported `sector_basis` "absent from
`GET /api/methodology`" when the same call returns it correctly once the process is restarted
(verified by the evaluator post-run). A whole P1 journey step was scored "not observable" against a
process, not against the product.
**Applies to:** any iteration whose deliverable is a new API field or new served payload key —
restart backend + frontend after the dev/audit steps and BEFORE browser-qa, and treat "key absent
from the API" as an environment hypothesis until the process start time is checked.

## iter-1 — 2026-08-20T05:04:26Z

**Verdict:** CONTINUE
**Lesson:** A test that `pytest.skip()`s in the only environment that exists is not coverage. TC-5's
API test guarded itself on the same `data/seed/universe.json` gate that was hiding the feature, so a
green "22 passed, 1 skipped" run concealed an undelivered, user-invisible deliverable
(`apps/backend/app/engine/methodology.py` emitted `sector_basis` inside the section the J-22 gate
pops). The audit caught it only by fetching the live endpoint.
**Applies to:** any iteration adding content behind an existing feature gate — assert the new value
at the layer the spec words its acceptance against (the served response), and never let the
acceptance test skip on the gate it is meant to prove independence from.

## iter-1 — 2026-08-20T05:04:26Z

**Verdict:** CONTINUE
**Lesson:** J-01's own written precondition ("Remove the last two trading days, then backfill the
same range") is destructive in this environment: 2026-08-13/14 were user-added bars with no
committed seed beneath them (`seed_latest_date` = 2026-08-12), so the Remove permanently destroyed
1,174 bars / 18 snapshots / 30,439 forward returns and the offline bars-only Backfill correctly
refused to fabricate them back. The fresh run the journey needed appeared anyway — the backend's own
boot created run 3081 for 2026-08-12 from seed bars.
**Applies to:** any journey step that instructs a data Remove — check `seed_latest_date` covers the
range first, and prefer the backend's own boot/persist path over a destructive remove+rebuild cycle
to obtain a fresh run.


<!-- condense.sh 2026-08-23T09:23:39Z: moved 3 entries (keep-iters=5) -->

## iter-2 — 2026-08-20T09:05:00Z

**Verdict:** ESCALATE
**Lesson:** The engine dispatched this iteration LEAN even though the spec's own metadata said
`Depth: full` and the iter-1 evaluator's recommendation was binding-full. Nothing warned anyone —
the depth divergence is only visible by comparing `runs/goal-session-market-compass/iter-2/depth-dispatched`
("lean") against the spec's `**Depth:** full` line. The cost was silent: the auditor, ux-regression,
closure and demo/walkthrough lanes never ran, so four journeys inherited a `[NEW]`-walkthrough gap
they did not need to have, and the developer's explicit "this is a product-quality question for
review/audit/the evaluator to triage" (zero candidates on the frontier date) reached no auditor.
**Applies to:** any iteration whose spec metadata says `Depth: full` — the evaluator should diff
`depth-dispatched` against the spec's Depth line during the evidence walk and treat a downgrade as
an ESCALATE trigger, not just note it.

## iter-2 — 2026-08-20T09:05:00Z

**Verdict:** ESCALATE
**Lesson:** The strongest AG-3 ("displayed numbers are correct") evidence in this iteration cost
nothing extra: because the three new compass cards were placed ABOVE the untouched legacy dashboard
body on the same page, one full-page screenshot contains both the new cited fact (regime_score 73.24,
severity 25.84, breadth 59.84/66.39) and the pre-existing canonical tile serving the same value.
Cross-checking within a single image is stronger than any prose claim and needs no running backend —
worth preserving deliberately until J-08 relocates the dashboard body to `/market`, after which the
two surfaces separate and this free cross-check disappears.
**Applies to:** any iter touching `apps/frontend/app/page.tsx` layout, and specifically J-07/J-08's
Today-page recomposition and `/market` relocation.

## iter-2 — 2026-08-20T09:05:00Z

**Verdict:** ESCALATE
**Lesson:** The runtime banned-language guard (`_assert_no_banned_language`,
`apps/backend/app/engine/compass.py:175`) is called only from `build_narrative` (`:208`) — it never
sees the candidate reason, caution or why-not strings produced by `evaluate_selection`. That is
exactly where advice-flavoured wording actually appeared ("ATR is 2.23% of price — sized risk
accordingly", `compass.py:294`), because reasons/cautions are free-form f-strings assembled in code
rather than config templates. A guard that covers the safest text and skips the riskiest text reads
as coverage but is not.
**Applies to:** any iter adding user-facing generated prose under `app/engine/compass.py`, and the
J-05/J-06 manifest work that will serialise these same strings into an exported artifact.


<!-- condense.sh 2026-08-23T12:27:43Z: moved 2 entries (keep-iters=5) -->

## iter-3 — 2026-08-20T13:20:00Z

**Verdict:** CONTINUE
**Lesson:** Five of this iteration's fourteen browser-QA screenshots are the SAME 20 KB file
(`UT-01/06/11/13/14-result.png`, md5 `e83381c1…`) and two more are one identical BLANK 6 KB file
(`UT-04/UT-05-result.png`, md5 `ad732856…`) — every one of them bottom-anchored so the card under test
is off-frame. The prose rows were accurate (they were read from the DOM), but the cited images prove
nothing, and a checksum sweep of the evidence directory exposed it in seconds. The only usable
acceptance frames came from the QA agent's full-page captures — which themselves truncate at
~29,500 px, cutting the shadow-cohort table off the end of a 539-row page.
**Applies to:** every iteration's evidence review — run `md5sum` over
`reports/qa/<iter>-evidence/*.png` before citing any of them, and expect long pages (audit tables,
cohort lists) to need an element-scoped capture rather than a full-page one.

## iter-3 — 2026-08-20T13:20:00Z

**Verdict:** CONTINUE
**Lesson:** A feature can be fully built, fully unit-tested, review-passed and audit-passed and still
have its headline claim unobserved. J-05's whole point is that a real close seals the record with
`prospective_eligible: true`, and NOTHING in this iteration ever produced that state: the ingest test
was skipped for host safety, the live frontier still served a pre-freeze-era row, and every `at_ingest`
manifest anyone saw came from the regenerate button — which by design is always
`prospective_eligible: false`. The producer path with the strictest acceptance rule is also the one no
lane can exercise cheaply, so it silently becomes the untested path.
**Applies to:** any iteration whose acceptance depends on the ingest-finalize tail
(`data_manager._refresh_ingest_aggregates`) — plan the remove+backfill drill as a first-class,
budgeted step, or state up front that the journey cannot close this round.


<!-- condense.sh 2026-08-23T21:20:10Z: moved 2 entries (keep-iters=5) -->

## iter-4 — 2026-08-20T15:05:00Z

**Verdict:** CONTINUE
**Lesson:** J-09's ≤2.5 GB VmPeak target was derived from a THEORETICAL calculation
(`cache_size` 256 MB × `pool_size` 24 = 6.1 GB) without checking this project's own recorded
floor. `config.yaml:1377`'s `memory_cap_mb` comment already documented 2,691,600 kB (iter-32) and
3,688,916 kB (iter-38) VmPeak for an isolated heavy warm on the 30y basis, and two cold boots with
the NEW value peaked at 837,860-1,423,852 kB before any load — so a >2.5 GB floor existed
independent of the pool cache, and the config change could not have reached the target no matter
how it was measured. Before committing to a numeric performance target, grep the project's own
prior measurements (`reports/perf-budgets.md`, the cap comments in `config.yaml`) for an existing
floor; a theoretical worst-case multiplication is not a baseline.
**Applies to:** any iteration whose acceptance is a measured resource/latency threshold, and any
goal.md amendment that sets one.

## iter-4 — 2026-08-20T15:05:00Z

**Verdict:** CONTINUE
**Lesson:** The deterministic replay golden for J-01 has now produced the IDENTICAL false FAIL in
two consecutive iterations ("step 03 expected 'Consumer Discretionary' did not appear") — the
sector cell renders the string wrapped across two DOM lines, which the golden's contiguous-text
match cannot see (`reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png` shows the value
plainly). Reconciling an overturned replay FAIL is a workaround, not a fix: leaving the golden
broken trains every future evaluator to wave the same row through, so a REAL J-01 failure would be
dismissed as "the usual false positive". A golden overturned twice must be repaired (match the
cell's text content, not a contiguous string) in the next iteration that touches the lane.
**Applies to:** any iteration reading `*-regression-replay-results.md`; any journey whose golden
asserts on a multi-word value inside a narrow table column.


<!-- condense.sh 2026-08-24T10:15:45Z: moved 2 entries (keep-iters=5) -->

## iter-6 — 2026-08-20T22:15:00Z

**Verdict:** ESCALATE
**Lesson:** A goal-level lane gate written in `docs/goal.md` prose ("no browser-QA lane may run
against the damaged database") is NOT enforced by the engine: when the depth arbiter silently
demoted iter-6 full→lean under a "full-cap", lean depth auto-enabled
`CHAIN_LEAN_PARALLEL_BROWSER_QA`, which fired the forbidden replay against the damaged DB at
18:15-18:16Z and produced FAIL rows for J-02/J-03 that looked exactly like a fresh regression. Two
compounding traps followed: the merge step reconciled the damaged-DB FAILs down to SKIP but left the
damaged-DB PASSes (J-01, J-04) standing as clean rows — a one-sided read of evidence the contract
declares unusable in BOTH directions; and a "full" depth requested by an iteration spec is advisory,
not binding, so the audit lane silently skipped the one change whose entire purpose was preventing a
repeat of a live-fetch scope violation. Only ESCALATE makes the next `full` binding.
**Applies to:** any iteration whose `docs/goal.md` declares a lane gate or dataset quarantine; any
evaluator reading a merged results file after a depth demotion (check `iter-<N>/depth-dispatched`
against the spec's `**Depth:**` line FIRST, and treat quarantined evidence as unusable in both
directions); any iteration spec that names a Full trigger.

## iter-6 — 2026-08-20T22:16:00Z

**Verdict:** ESCALATE
**Lesson:** "Refetch from the same vendor the rows came from" is the wrong default for incident
recovery — the vendor IS often the reason recovery is needed. Stooq went from working to serving a
SHA-256 proof-of-work JS challenge on `https://stooq.com/q/d/l/`, so all 587 requests 404'd
including AAPL, and no non-browser HTTP client can ever pass it. The seemingly obvious fallback
(`LocalStooqArchiveProvider`, `data/d_us_txt/`) is structurally useless for this class of repair: it
is the same one-time bulk download already baked into the committed seed, so it ends at the seed
boundary (2026-07-01) and can NEVER cover a post-seed date. Pin a recovery journey's vendor as a
single named constant (`j10_recovery.py:83 RECOVERY_SOURCE`) so a vendor swap is a one-line change
plus an owner amendment, not a rewrite — that is exactly what made this block a one-iteration delay
instead of a dead end.
**Applies to:** any journey involving a live data refetch, backfill, or vendor migration; any code
adding a provider-scoped recovery path.


<!-- condense.sh 2026-08-24T16:29:59Z: moved 1 entries (keep-iters=5) -->

## iter-7 — 2026-08-21T01:05:00Z

**Verdict:** CONTINUE
**Lesson:** A fail-closed gate needs a minimum-EVIDENCE floor, not just a threshold: iteration 7's
`check_adjustment_convention` skipped any sampled pair whose *stored* side was missing (correct on its
own — never fabricate) and then fell through an empty pair list straight to `verdict="agree"`, reason
`"all 0 sampled pairs within 0.7500% relative delta"` — so "nothing contradicted it" was reported as
"positively proven", and the auditor reproduced `run_gated_recovery` writing rows on that vacuum. The
trigger condition was *rows unexpectedly missing*, i.e. precisely the damage the gate exists to guard
against, and the reason every test missed it is that all nine new tests seeded a complete fixture: a
guard is only proven fail-closed when a test constructs the degenerate input the guard will actually
meet in production. Placement matters too — the floor must sit AFTER the disagreement branch, or a real
out-of-tolerance pair gets downgraded to "cannot tell" by an unrelated coverage gap.
**Applies to:** any fail-closed gate, precondition check or verification step whose verdict ladder can
be reached with an empty/partial input set — especially incident-recovery and data-repair paths, where
the missing data IS the trigger; also any iteration whose new tests all seed complete fixtures.


<!-- condense.sh 2026-08-24T21:07:21Z: moved 2 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-25T08:17:52Z: moved 2 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-25T12:50:14Z: moved 1 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-25T18:24:59Z: moved 1 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-25T21:58:12Z: moved 2 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-26T08:55:13Z: moved 2 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-26T15:14:37Z: moved 1 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-27T03:07:04Z: moved 1 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-27T19:44:50Z: moved 4 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-27T22:20:06Z: moved 2 entries (keep-iters=5) -->

## iter-18 — 2026-08-26T00:55:00Z

**Verdict:** STALLED
**Lesson:** A guard scoped to "boot-initiated paths" leaves the request-triggered path open, and this
codebase's read path WRITES: `scanner.resolve_run` (`apps/backend/app/engine/scanner.py:348`) calls
`run_scan` create-once for whatever date `?as_of=` names, reached from every read endpoint via
`app/engine/snapshot_serving.py:42`. Four lanes (dev, reviewer, QA, auditor) enumerated the `run_scan`
call graph and all four missed it — the auditor explicitly counted "exactly three boot-initiated plus a
fourth (data_manager)" when `grep -rn "run_scan(" app/` returns six. The generalizable rule: enumerate
writers with a grep over the whole package and classify each one, never from a hand-built call graph;
and when a safety property is scoped by TRIGGER ("boot-initiated"), the artifact must name the triggers
it does NOT cover, because the reader will hear "the writes are blocked".
**Applies to:** any iteration adding a guard/quarantine/kill-switch scoped by trigger class; any
iteration that would lift maintenance isolation or re-enable browser QA on this project; anything
touching `warmup.py`, `forward_testing.py`, `scanner.py`, `snapshot_serving.py` or `data_manager.py`.

## iter-18 — 2026-08-26T00:55:00Z

**Verdict:** STALLED
**Lesson:** Arming the quarantine silently disabled a whole subsystem: `ensure_latest_snapshot` returns
`None` for a blocked latest date, and `main.py:113` starts the background warm-up only `if latest is not
None`, so no background warm-up runs at all and readiness reports `awaiting_snapshot` instead of `ready`.
Safe and fail-closed, but it means the two call sites this iteration guarded are currently unreachable on
boot — the delivered guards are defence-in-depth for a future state, not today's protection. Ask of every
new blocking guard: what ELSE keys off the value this guard now suppresses?
**Applies to:** any future iteration that boots the backend or resumes browser QA on this project (the
different readiness badge and the 2026-07-23 "latest" are EXPECTED, not a regression); any change to
`warmup.py`/`main.py` boot sequencing or `readiness.py`.


<!-- condense.sh 2026-08-28T09:15:20Z: moved 1 entries (keep-iters=5) -->

## iter-19 — 2026-08-26T15:40:00Z

**Verdict:** CONTINUE
**Lesson:** A successful destructive rebuild can make the system MORE dangerous to boot, not less, and
the danger moves rather than disappears. Before Stage D the risk was "an `?as_of=` request mints a run on
an empty quarantined date"; after Stage D those 11 dates are populated (so that specific accident is now
impossible), but three NEW exposures opened that no lane reported: `as_of=None` now resolves to the
rebuilt 2026-08-12 (zero `forward_returns`, stale caches) instead of the complete 2026-07-23; the 7
manifest-less incident dates are now HISTORICAL, so `compass.get_or_create_manifest`
(`compass.py:1040-1053`) would create-once-mint a forbidden manifest on any ordinary
`GET /api/compass?as_of=<date>`; and a 12th run minted on any of the 16 runless-but-barred dates would
carry the identical `engine_identity`, silently breaking the final stage's membership check. After any
live rebuild, re-derive what an ordinary request would now DO — do not carry forward the previous
iteration's exposure analysis.
**Applies to:** any iteration executing J-11 Stage E/F/G, and any future live rebuild that changes which
date is `max(ScannerRun.asof_date)` or populates a previously-empty date.


<!-- condense.sh 2026-08-28T16:17:25Z: moved 2 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-28T19:14:14Z: moved 3 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-09-02T06:46:36Z: moved 17 entries (keep-iters=5) -->

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

