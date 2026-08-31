# goal-market-compass-iter-29 Audit Report

**Date:** 2026-09-01
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's one authorized action did exactly what the spec asked and nothing more: a single
`GET /api/compass?as_of=2026-08-03` minted `next_session_manifests` id=27 (`version=1`,
`mode=retrospective`, `prospective_eligible=0`) carrying a non-null `state_band_json`, and the three
direction badges render real words on that date — I re-derived all three from stored inputs and
confirmed them against two independent screenshots. I re-derived AG-12 myself **after every lane
finished** (the check the dev handoff could not close): 27 rows, and the 26 pre-existing rows are
byte-identical to the pre-mint snapshot (sha256 `c070dcf1…`); AG-9 and AG-5 also hold. The gaps are
record-accuracy, not behavior: the declared-safe-`as_of` process control was enforced and logged for
the dev lane only (the replay lane requested three out-of-set dates, harmlessly, unflagged), DoD's
"all 7 J-07 steps verified live" is overstated, and one test in the DoD's named set is red
(pre-existing). I corrected the record in the dev handoff; the remaining items are documented gaps.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed — record corrected): the declared-safe-`as_of` process control was enforced
and logged for the dev lane only; three out-of-set dates were requested by the replay lane and none
was flagged.**

The spec's TESTING REQUIREMENTS are unambiguous: "any live `as_of` request outside the declared safe
set … occurring in **any lane** this iteration is a process violation and must be flagged in the dev
handoff, not silently absorbed (iter-27 lesson)", and DoD item 5 requires the handoff to cite "every
`as_of` value any lane actually requested". The deterministic replay lane executed
`runs/goal-session-market-compass/journey-scripts/J-04.json:7` (`asof=2026-03-30`, `asof=2026-07-23`)
and `J-10.json` / `J-11.json` (`asof=2026-08-11`) — three values outside
`{no param, "2026-08-12", "2025-04-15", "2026-08-03"}`
(`reports/phase-goal-market-compass-iter-29-regression-replay-results.md`, 8/8 PASS).
`docs/handoffs/goal-market-compass-iter-29-dev.md` §"As-of values requested this iteration (TC-6)"
states "**Full set actually requested: `{"2026-08-03"}`** … zero exceptions" — a cross-lane claim
made from dev-lane evidence only. `reports/qa/goal-market-compass-iter-29-qa.md` §3 then marked TC-6
**PASS** citing only that same dev-lane list, and `reports/reviews/goal-market-compass-iter-29-review.md`
recorded `definition_of_done: complete`. This is the exact class of gap the iter-28 ESCALATE was
about (a control asserted rather than re-derived), which is why I rate it IMPORTANT rather than GAP.

*No harm materialized, and I proved that rather than assuming it:* each out-of-set date already
carried at least one stored manifest row (ids 5, 2, and 15/16/20), so the create-once path returned
an existing row. Post-all-lanes read-only re-derivation at `2026-08-31T23:12:45Z`:
`SELECT COUNT(*) FROM next_session_manifests` → **27**; exactly **1** row for `2026-08-03`; the 26
non-`2026-08-03` rows dumped to CSV hash to
`c070dcf1c29e9824cacd8f715fb5d40b498888dfd5001e388ab4a1f46c2d7218`, identical to
`runs/goal-market-compass-iter-29/evidence/manifests-pre-mint.csv` (`diff` empty). The spec's own
NOTES also pre-scope TC-6's *constraint* to create-once mints, which held with zero exceptions; what
was missed is the *logging/flagging* obligation.

*Fix applied:* appended the complete per-lane `as_of` ledger, with the three out-of-set values
explicitly flagged, to `docs/handoffs/goal-market-compass-iter-29-dev.md` (§B of the auditor
addendum), together with the post-all-lanes re-derivation that proves zero collateral mints.

**B2 — OBSERVATION (fixed): TC-5's "re-derive AFTER every lane" obligation was open at handoff time.**
The dev handoff's Known Issue #1 correctly said the check "is not yet closeable by this agent" and
preserved the snapshot files for whoever ran last. I ran last and closed it (see B1's numbers, plus
`apps/backend/data/exports/next_session_manifests/` untouched since `2026-08-20 15:50`, so no exported
manifest was mutated or deleted either). Honest deferral, now discharged — recorded in §A of the
addendum.

**B3 — GAP (documented): the DoD's named test set is not fully green —
`apps/backend/tests/test_no_magic_numbers.py:106::test_engine_calc_code_has_no_magic_numbers` fails.**
I re-ran it: `1 failed, 1 passed in 0.07s`, offenders `indicators.py` (`0.5`, `0.95`),
`forward_testing.py` (`45.0`, `0.5`, `0.9`), `research.py` (`0.0` ×4). Pre-existence verified, not
taken on trust: `git diff --quiet HEAD` is clean for all three files **and** for the test file
itself, and `git log -1` on them returns `0c445647` (iter-18 era) — so the failure is a pure function
of content identical to HEAD and cannot have been introduced by iter-28 or iter-29. Critically,
`compass.py` and `session_delta.py` **are** in the test's `CALC_FILES`
(`apps/backend/tests/test_no_magic_numbers.py:57`) and produce zero offenders, so iter-28's
`state_band` code introduced no magic number (`stress_velocity_flat_band` comes from
`config.yaml:1411`). Not fixed: this was a zero-code-change operational iteration and editing three
engine modules would be scope creep.

**B4 — OBSERVATION: `available_at_utc`/provenance on the new row are honest.** `generation_json` =
`{"producer": "on_demand_get", "frontier_bar_date": "2026-08-12", "generated_at":
"2026-08-31T22:25:25.683323+00:00", "preflight_verdict": null, "engine_identity": "b704527b…",
"source_run_created_at": "2026-08-26T10:52:59.462404+00:00"}` with `prospective_eligible=0` — AG-17
respected (a retrospective mint is never marked prospectively eligible). The empty `export_path` is
consistent with every other `retrospective` row (ids 12, 14–22, 24–26); only `at_ingest` rows carry
one, because `_write_export` is called solely from `_freeze_manifest`
(`apps/backend/app/engine/compass.py`).

**B5 — OBSERVATION (pre-existing, already logged): export-file/row mismatches predating this
iteration.** Rows 9, 10, 11 record `export_path` values for `2026-08-12_v2/v3/v4.json` that are
absent from disk, and four files (`2024-06-08_v1`, `2024-07-01_v1`, `2024-07-08_v1`,
`2024-08-01_v1`) exist with no matching manifest row. Already surfaced by an earlier evaluator
(`runs/goal-session-market-compass/state/evaluator-log.md:688-689`) and unchanged by this iteration
(directory mtime `2026-08-20 15:50`). Carried, not introduced.

**B6 — OBSERVATION: the plan and handoff describe iter-28's work as "uncommitted"; it was committed.**
`runs/goal-market-compass-iter-29/plan.md` ("iter-28 never got a git commit") and the dev handoff
("iter-28's uncommitted work") were already stale when written — `a8dc7f6b` (2026-08-31 22:59:50
+0100) contains `apps/backend/app/engine/compass.py`, `models.py`, `db.py`, `config.yaml`,
`compass-state-band-card.tsx` and the two test files, ~18 minutes before iter-29 started. No
functional impact; the code they exercised is the code they described.

### Frontend Findings

**F1 — GAP (documented): the default view a user lands on still shows the iter-28 contradiction.**
On `/` at Latest (2026-08-12) all three badges read **"NA"** while the Summary card one row below
reads "Conditions are little changed since the prior session (-0.2 regime-score points)" —
`reports/qa/goal-market-compass-iter-29-evidence/UT-04-result.png`. That is the same shape as the
finding TC-4 was written to prevent, surviving on the landing page; TC-4 is scoped to the
`?asof=2026-08-03` load, where I confirmed it does **not** recur (badge "improving" and the sentence
"Conditions are improving since the prior session (+4.7 regime-score points)." agree —
`UT-02-result.png`, `UT-03-result.png`). The spec's OUT OF SCOPE forbids backfilling any other date,
so this is a spec-sanctioned limitation, not a defect: J-07's ten-second read answers in real words
on exactly one hand-minted historical date and still reads "NA" everywhere a user arrives by default.
Every future `at_ingest` freeze will carry the field, so the gap closes with the next ingest — worth
saying plainly rather than letting "J-07's NA gap is closed" stand unqualified.

**F2 — OBSERVATION: the frontend does no word selection, as J-07's acceptance requires.**
`apps/frontend/components/compass-state-band-card.tsx:30` renders `{word ?? "NA"}` and lines 84/115/141
pass `stateBand?.<band>.direction_word` straight through — no threshold comparison, no delta
computation, no client-side vocabulary. The `?.` chain also yields NA (never throws) for the 26
`state_band: null` rows, which matches
`test_compass_route_state_band_null_on_pre_iter28_row`.

### Test Findings

**T1 — GAP (documented): the J-07 replay golden's new step guards the wrong field and has never run.**
`runs/goal-session-market-compass/journey-scripts/J-07.json` gained step 4 this iteration:
`goto /?asof=2026-08-03` expecting `"Conditions are improving since the prior session (+4.7
regime-score points)."` Two problems. (a) That sentence comes from `narrative`
(`build_narrative`'s direction sentence), **not** from `state_band` — it already rendered non-NA
before iter-28 existed, so the badges this iteration exists to expose still have **no** durable
browser-level regression guard; the three `compass-state-band-*-direction` testids are asserted
nowhere in any golden. (b) The file's mtime is `2026-08-31 23:50`, after the replay lane's own
artifacts (`J-07-verify.png`, `23:47`), so the added step executed zero times this iteration — the
`UT-J-07 PASS` row in `reports/phase-goal-market-compass-iter-29-regression-replay-results.md` is a
pass of the previous 3-step script. The assertion text is factually correct (it matches the live
string in `UT-03`), so the risk is coverage, not falsity. Not fixed: adding badge assertions requires
restarting both services and re-running the replay to produce the evidence a fix must cite, which
exceeds this audit's remit on a zero-code iteration — recommended for the next iteration instead.

**T2 — OBSERVATION: the recorded walkthrough shows "NA" in the frames that claim to demonstrate the
capability.** Demo steps 03/04/05 — `[NEW]`, J-07-flagged, titled "Jump to August 3rd", "Read the
market state badges", "Check the summary for consistency" — captured the **Latest** page with all
three badges reading NA, because their clicks did not resolve
(`reports/phase-goal-market-compass-iter-29-demo-results.md` soft notes; `step-04.png`). Step 06's
plain `goto /?asof=2026-08-03` does show the capability correctly (`step-06.png`: improving /
improving / little changed), so the gallery is not uniformly wrong, and the failures are disclosed in
the demo's own notes. Showcase-only and non-blocking, and walkthroughs are explicitly OUT OF SCOPE
this iteration — but a reader skimming the gallery would draw the wrong conclusion.

**T3 — OBSERVATION: the 11 `state_band` tests are tight, not loose.** Spot-read
`test_state_band_regime_matches_direction_word_and_stress_flips_polarity`
(`apps/backend/tests/test_compass.py:430`) — exact `pytest.approx` values (+8.0 regime, +20.0 stress),
asserts the stress word is the *opposite* polarity of regime's for the same run pair, so an
accidental copy of regime's sign transform would fail — and
`test_compass_route_serves_state_band_directly` (`apps/backend/tests/test_api_compass.py:205`), which
pins the exact key set, both deltas, and the honest `{"direction_word": None, "delta": None}` NA
state. No accept-either-outcome assertions found.

**T4 — verified: DoD item 1's "all 7 steps verified live" is overstated (record corrected).**
`docs/goal.md`'s J-07 has 7 numbered steps; the browser lane's UT-01…UT-07 are a different set of
seven. Live coverage this iteration: step 3 **in full** (`UT-02-result.png` + QA §4's API/DOM
comparison), step 1 partially, step 6 via the replay golden's link-out; **steps 2, 4, 5 and 7 were
not exercised by any lane**. `reports/qa/…-qa.md` §8 ticks the box unqualified. I was genuinely
unsure between GAP and IMPORTANT here and chose the higher, because a goal-mode evaluator reading an
unqualified checkbox may promote J-07 to `passing` on an overstated basis, and per
`.claude/judgment-rubrics.md` §6 a wrong `passing` poisons every later iteration's baseline. Fixed by
writing the honest per-step coverage table into §C of the dev-handoff addendum.

---

## 3. Domain Assessment

The domain logic is correct, and I checked it against stored inputs rather than against the handoff.

**The three words are right, and so are their numbers (AG-3).** From the live DB, read-only:
`scanner_runs` 2026-08-03 (id 3154) `regime_score=66.07`, `breadth_above_50dma=45.08`; 2026-07-27
(id 3153) `regime_score=61.41`, `breadth_above_50dma=45.90`; `market_phase_cache` severity
`29.35` (2026-08-03) and `35.52` (2026-07-27). Therefore regime Δ `+4.66` vs
`velocity_flat_band 2.0` → "improving"; breadth Δ `-0.82` vs `breadth_min_change_pts 5.0` → "little
changed"; stress Δ `-6.17` classified on its **negation** (`compass.py:324-328`) vs
`stress_velocity_flat_band 5.0` → "improving" (severity fell, i.e. stress eased). The stored
`state_band_json` is exactly `{"regime": {"improving", 4.659999999999997}, "stress": {"improving",
-6.170000000000002}, "breadth": {"little changed", -0.8200000000000003}}`, and the rendered page
shows `66.07`, `29.35`, `45.1%` with those same three words (`UT-02-result.png`). The stress
polarity flip is the one place this could silently lie — a rising severity labelled "improving" —
and it is both correct here and pinned by a test that asserts the opposite word from regime's for a
shared run pair.

**No-lookahead (AG-5) holds for the new row.** Scanning every JSON column of id=27 for ISO dates
after the as-of: `session_delta` max `2026-08-03`; `narrative`, `selection`, `dataset`, `universe`,
`caveats` contain none; only `generation_json` carries later dates (`2026-08-12` dataset frontier,
`2026-08-31` generation time) — provenance, which retrospective mode is required to record. The
phase payload feeding severity is as-of-bounded (`observations`/`timeline` max date `2026-08-03`);
its `timeline_full` reaching `2026-08-12` is the pre-existing, opt-in (`full=true`) full-history
causal series stripped from the card payload (`apps/backend/app/engine/market_phase.py:1006-1027`),
not something `state_band` reads.

**System-vs-market separation (AG-13) holds on the new render.** Readiness vocabulary ("Ready", "GO —
today's board is current") appears only in the chrome strip; the market cards carry only market
vocabulary ("Risk-on", "Expansion", "improving", "little changed"), and the three new words come from
`config.yaml:1428-1431`, which contains no readiness token. The retrospective disclosure ("This is a
retrospective view, reconstructed under the CURRENT selection rule and config…") renders on the
2026-08-03 page, so the reconstruction is labelled rather than passed off as a live read.

**Idempotency is real, not asserted.** Two identical `GET`s produced byte-identical responses
(`compass-2026-08-03.json` and `-repeat.json` are both 334125 bytes) and the row count stayed at 27
across every subsequent lane — create-once behaves as create-once.

Tests re-run by me (targeted, sequential, per the resource contract):
`pytest tests/test_manifest_invariants.py` → **51 passed**;
`pytest tests/test_compass.py tests/test_api_compass.py` → **54 passed**;
`pytest tests/test_no_magic_numbers.py` → **1 failed, 1 passed** (B3).

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `docs/handoffs/goal-market-compass-iter-29-dev.md` | Appended an auditor addendum: (§A) the TC-5/AG-12 re-derivation run **after every lane** — 27 rows, 1 row for 2026-08-03, 26 pre-existing rows sha256 `c070dcf1…` identical to the pre-mint snapshot, exports untouched since 2026-08-20, no provider run since 2026-08-23 — closing the handoff's open Known Issue #1; (§B) the complete per-lane TC-6 `as_of` ledger with the replay lane's three out-of-set dates (`2026-03-30`, `2026-07-23`, `2026-08-11`) explicitly flagged as the spec requires, plus the proof that none of them minted anything; (§C) the honest J-07 per-step live-coverage table replacing the unqualified "all 7 steps verified live" claim. |

No source file, test, config, or journey script was modified — `git status` shows no change under
`apps/` or `config.yaml`, which is exactly what a zero-code operational iteration should show.
Verification for this fix is the evidence it cites: every number in the addendum comes from a command
I ran in this audit (`sqlite3 … mode=ro` counts/CSV/sha256/diff, three `pytest` runs, `git diff
--quiet HEAD`, the journey-script greps), and each is reproducible from the paths named.

---

## 5. Recommended Next Step

**Proceed.** The phase goal was achieved and independently verified: one authorized mint, real words
on real data, AG-12/AG-9/AG-5/AG-13 intact, and the byte-identity proof re-derived after every lane
rather than inherited from a snapshot.

Carry these into the next iteration, in priority order:

1. **Give `state_band` a durable regression guard (T1).** Add an assertion on the three
   `compass-state-band-{regime,stress,breadth}-direction` testids at `?asof=2026-08-03` to
   `J-07.json`, and *run* the golden so the new step has an executed PASS behind it. Today a
   regression to "NA" on that date would not fail any replay.
2. **Decide what Latest should show (F1).** The landing page still pairs three "NA" badges with a
   Summary sentence that states the same comparison in words. Either mint/backfill so the frontier
   date carries `state_band`, or render an explanatory NA state ("this session was frozen before
   direction words existed") instead of a bare "NA" — an owner call, since backfilling touches the
   protected table.
3. **Close the `test_no_magic_numbers` red (B3)** — three engine modules, nine float literals, no
   relation to the compass cluster; it is currently the only red test inside a DoD-named set and it
   masks any future magic number added to those files.
4. **Process, for the next database-mutating spec:** the safe-`as_of` control worked, but its
   *evidence* was collected by only one of five lanes. Whoever runs last should own the cross-lane
   ledger by construction (e.g. the pipeline records each lane's requested `as_of` values as it goes),
   rather than leaving it to a handoff written before three lanes have run.
