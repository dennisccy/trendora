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

