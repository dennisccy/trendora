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

