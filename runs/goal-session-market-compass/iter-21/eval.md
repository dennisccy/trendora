# Iteration 21 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

**Owner-facing lines:** `J-11 STAGE D EXECUTED: YES` · `J-11 STAGE E COMPLETE: YES` ·
`J-11 STAGE F COMPLETE: YES` · `J-11 STAGE G VERIFIED: NO` ·
`J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE` · `J-11 MAINTENANCE BOUNDARY: ACTIVE` ·
`J-11 LIVE PRE-BOOT GUARD: ARMED`. Every one confirmed by this evaluator against the live database,
read-only, with no correction needed.

## Summary

The one job the owner's written plan allowed was done, and it worked. This step cleared out old
saved answers that the app had kept from before the accident, so that when the app is finally
switched back on it cannot show pre-accident figures as if they were current. I did not take that
from anyone's write-up: I opened the 8.4 GB database read-only and re-measured everything myself.
Five stores of old answers are now empty, two were deliberately kept for good reasons I re-proved
myself, and nothing else in the database moved by a single row. Nothing was tested in a browser
this run, because the owner's own rule forbids starting the app until the repair's last step
passes, so every journey keeps the status it already had. One thing is worse than anyone
recorded, and I found it myself: a single ordinary page visit would put one of those old-answer
stores straight back, for one of the eleven damaged days, and nothing stops it.

## Journey Results This Iteration

Browser QA and the deterministic replay lane were FORBIDDEN BY CONTRACT (maintenance isolation).
`reports/phase-goal-market-compass-iter-21-ui-test-results.md` records `Browser QA Verdict: SKIPPED`
with a `**Reason:**` line naming maintenance isolation, and
`runs/goal-session-market-compass/iter-21/maintenance-isolation-refusals` records the engine's own
refusal of `browser-qa-phase` at 2026-08-27T06:50:06Z. No `browser-infra.json` token exists — the
lane was withheld, not failed — so no journey is scored `pending_infra`, and per methodology A.3's
second carve-out every journey KEEPS its prior recorded status. No journey may be promoted on this
iteration's evidence, and none was.

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest on new runs | passing | passing (carried, spot-checked) | `reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png` re-opened — GRMN "Consumer Discretionary", 1/539, regime 73.24 Risk-on, scores badged "Not yet proven" |
| J-02 What changed since previous session | partial | partial (carried, not re-verified) | maintenance isolation — no lane could run |
| J-03 Plain-English summary with cited facts | partial | partial (carried, not re-verified) | maintenance isolation — no lane could run |
| J-04 Candidate why and why-not | passing | passing (carried; `evidence_makeup` kept) | `reports/qa/goal-market-compass-iter-4-evidence/J-04-verify.png` is a CAPTURE DEFECT for the 3rd iteration running; behaviour proven by `reports/phase-goal-market-compass-iter-4-ui-test-results.md` line 21 (UT-J-04 PASS) |
| J-05 Close freezes one manifest | partial | partial (carried, not re-verified) | maintenance isolation — no lane could run |
| J-06 A frozen manifest never changes | partial | partial (carried, not re-verified) | maintenance isolation — no lane could run |
| J-07 Today page ten-second read | failing | failing (carried, blocked) | blocked by `docs/goal.md` loop-mechanics gate until Stage G passes |
| J-08 Market page moves over intact | failing | failing (carried, blocked) | blocked by `docs/goal.md` loop-mechanics gate until Stage G passes |
| J-09 Backend fits the host | partial | partial (carried, not re-verified) | maintenance isolation — no lane could run |
| J-10 Bounded recovery of two trading days | passing | passing (carried, spot-checked) | evaluator's own read-only re-derivation: 585 `daily_prices` rows on each of 2026-08-11/12; AVB volumes 554757.0 / 3706010.0; whole-table total reproduces `ohlcv_sum` 52367098848872.56 and fingerprint `80441b37…` |
| J-11 Incident-bounded clean regeneration | partial | partial — ADVANCED (Stage F complete) | `runs/goal-market-compass-iter-21/j11-stage-f-execute-{dispositions,mutation-accounting,preflight-gate,verification-result,memory-check}.json` (16 artifacts) + this evaluator's own read-only live-DB re-derivation |

Spot-checks: 2 of 2 done (J-01 screenshot, J-10 live re-derivation). Both consistent with their
recorded status; no widening needed. `spec_hash`: I ran
`goal_gate.py hash-journeys docs/goal.md` myself — all ELEVEN journeys' live hashes are
byte-identical to the recorded ones, so `docs/goal.md` has not moved since iteration 19's ruling
commit `5fe72f5c`, and no `journeys-changed.md` fired.

### What Stage F actually did — verified by me, not read from a report

Read-only `sqlite3 "file:…?mode=ro"` against `apps/backend/data/trendora.db`:

- Five tables now hold ZERO rows: `event_study_cache`, `market_phase_cache`,
  `forward_aggregate_cache`, `availability_cache`, `coverage_snapshot` (1,643 rows deleted).
- Two tables hold exactly one row each, byte-identical `dataset_version`/`created_at`:
  `index_series_cache` `d2026-08-12-c60699` @ 2026-08-23 10:34:44.025990;
  `membership_timeline_cache` `r3150-rc3121-b2026-08-12-bc3310374-h200` @ 2026-08-23 10:32:55.645968.
  Both predate Stage D's start (2026-08-26 10:52:55.552946) by three days.
- I RECOMPUTED both live stamps rather than reading them: broad `r3158-f6814320`; narrow
  `r3158-rc3128-b2026-08-12-bc3310374-h200`. I also recomputed `index_series_cache`'s own narrow
  stamp from the ten configured `index_chart` symbols — MAX(date) 2026-08-12, COUNT(\*) 60699 ⇒
  `d2026-08-12-c60699`, EQUAL to the stored value. `prove_unaffected_leave_alone` is right on my
  own arithmetic.
- I REPRODUCED the membership preservation proof from the live payload: 3,121 points, tail
  2026-08-12, payload sha256 `c953d8a4…`, 7 new dates (2026-05-13, 07-10, 07-13, 07-24, 07-27,
  08-03, 08-05), 0 missing, `append_forward = False`. The same read independently CONFIRMS the
  auditor's B2: the preserved payload holds pre-incident points for exactly four incident dates
  (2026-05-12, 2026-08-10, 2026-08-11, 2026-08-12).
- Nothing outside the five authorized tables moved, on my own counts: `daily_prices` 3,310,374
  (fingerprint `80441b37…` pre == post), `scanner_runs` 3,128 / max id 3158, `scanner_results`
  1,331,727, `sector_scores` 96,968, `theme_scores` 34,408, `forward_returns` 6,814,320,
  `next_session_manifests` 24, `data_provider_runs` 549, `watchlist` 6 — every figure identical to
  iteration 20's recorded post-Stage-E values.
- The 11 Stage-D runs are present, unrestamped, ids 3148–3158, creation times
  2026-08-26 10:52:55.552946 → 10:53:02.010362 to the microsecond, 539–542 / 31 / 11 derived rows
  each (sums 5,942 / 341 / 121 — identical to iteration 19's record); their per-run
  `forward_returns` counts (2771 2769 2216 2215 1659 1658 1103 1103 549 549, run 3158 = 0) match
  Stage E's recorded outcome exactly. Exactly 11 runs carry the frozen identity `53d2ffd1…`, and
  they are exactly ids 3148–3158 — no twelfth run carries it.
- Module integrity: `sha1sum apps/backend/app/engine/j11_stage_f_execute.py` =
  `5fccfa1da95bd1abee4f24d689247beae439d871`, equal to the auditor's pre-mutation hash, so all six
  audit mutations were genuinely reverted. I re-ran the targeted suite myself: **76 passed in
  3.49s** (the dev handoff's "75" is wrong — auditor T1).
- Peak memory 479.9 MB against `server.memory_cap_mb` 8192 (`j11-stage-f-execute-memory-check.json`).

## Anti-goal Check

Worked from `runs/goal-session-market-compass/iter-21/scan-report.md` (**CLEAN** — no secret,
dependency, or license findings; 4 untracked files scanned) plus `iter-diff.md`, plus my own
`git status --porcelain -uall` (the diff caveat is real: the four source files are UNTRACKED, so
`git diff <sha>` renders empty). Zero TRACKED production file is modified — the only 11 ` M `
entries are harness bookkeeping under `runs/goal-session-market-compass/`.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unproven values render "not yet proven" | OK | No value displayed or scored this iteration; the J-01 spot-check screenshot still shows all three scores badged "Not yet proven" |
| AG-2 decision-quality only | OK | No advice, target, signal or order surface exists in the diff |
| AG-3 displayed numbers correct | OK — improved | Deleting `availability_cache`'s stale row removes the branch (`data_manager.py:1741-1747`/`:1760-1763`) that served pre-incident figures labelled `stale: False`; the same unmodified function now returns the honest "not yet computed" sentinel |
| AG-4 no overfit edges | OK | No pattern, claim or referee artifact touched |
| AG-5 determinism / no lookahead | OK | Only cache ROWS deleted; no producer, scoring rule or forward-return path modified (OUT OF SCOPE list verified against `git status`) |
| AG-6 evidence claims refereed | OK | No Evidence Claim introduced |
| AG-7 no hard-coded credentials | OK | My own grep for `api[_-]?key|secret|token|password|bearer` over the four new files returns only a TEST's `_NETWORK_TOKENS` tuple; scan-report CLEAN |
| AG-8 data-shape/scale resilience, no unbounded ORM sweeps | OK | Every `select(` in the module is column-projected or an aggregate (`:228 :235 :270 :291 :293 :303 :414 :547 :625`); no full record_json sweep; VmPeak 479.9 MB |
| AG-9 offline-deterministic ingest, no network | OK | My own grep for `requests|httpx|urllib|socket|aiohttp|http://|https://` over the module and CLI returns ZERO — the only hits are in a test asserting their absence (TC-19) |
| AG-10 host resource ceiling | OK | 479.9 MB peak vs 8192 MB cap, margin 7712.1 MB; no launch script's HOST-GUARD block touched; no eager cache regeneration (explicitly out of scope) |
| AG-11 no new composite number | OK | No score, blend or candidate field added |
| AG-12 manifest immutability | OK — proven by content | I compared all 24 `next_session_manifests` rows field-by-field across all 28 columns against `runs/goal-market-compass-iter-16/j11-stage-d-certified-baseline.json` — ZERO real mismatches after normalizing only ORM-vs-sqlite bool serialization |
| AG-13 system-vs-market vocabulary | OK | No narrative, badge or readiness string touched |
| AG-14 no Tapeology coupling | OK | My own grep for `tapeology` over the four new files returns ZERO |
| AG-15 no outcome-tuned selection | OK | No selection rule or threshold touched |
| AG-16 cohorts are not controls | OK | No cohort surface or artifact touched |
| AG-17 repair never rewrites provenance | OK | Same 24-manifest content comparison; `prospective_eligible` is 0 on every row — nothing upgraded. Only recomputable caches were deleted, never a manifest or an eligibility flag |
| AG-18 bounded manifest migration only | OK | `next_session_manifests` untouched — 24 rows, all dated 2026-08-20, content-identical to the certified baseline |

**Result: NO new violation.** Ledger unchanged at **7 total, 0 unresolved**. The five at real risk
this iteration were AG-3, AG-8, AG-10, AG-12 and AG-17, and all five HELD — each verified by my own
greps, code reading and read-only database queries, not by any lane's assertion.

**Coherence:** `runs/goal-session-market-compass/iter-21/coherence.md` = **COHERENCE-PASS**. No
structural veto. **Lane verdicts:** review PASS (zero issues), QA PASS, audit PASS_WITH_GAPS
(B1–B3 gaps, B4–B7/T1–T2 observations, Q1 IMPORTANT fixed in-audit), closure CLOSURE-PASS, scan CLEAN.
**Depth:** `runs/goal-session-market-compass/iter-21/depth-dispatched` reads `full`, matching the
spec's own `Depth: full` line — the silent full→lean demotion that fired in iterations 2, 6 and 8
did NOT recur, for the thirteenth iteration running.

## Next-Step Recommendation

**DO THE LAST STEP OF THE REPAIR — Stage G, the final check.** Nobody needs to approve it. The
owner's written instruction of 2026-08-26 approves Stages D, E, F and G in one ruling, and item 9
makes Stage G the acceptance gate that follows Stage F. The ruling's "stop" is attached to a
failure, a refusal or an unmet gate, and none happened here: every pre-check passed, every
after-check passed, and all five review lanes agreed.

**KEEP THE APP OFF AND KEEP BROWSER TESTING OFF.** This matters more now, not less, and I confirmed
all three reasons myself by reading the code:

1. **NEW, AND NOBODY ELSE RECORDED IT** (the developer, reviewer, quality check, auditor and
   coherence check are all silent — I searched each one). Asking a page for an explicit date writes
   a fresh coverage record on the spot: `coverage_from_storage`'s self-healing branch
   (`apps/backend/app/engine/data_manager.py:1544-1546`) calls
   `refresh_coverage_snapshot_for` → `_upsert_coverage_snapshot`, and that file imports no
   safety catch at all. Because all eleven damaged days now have day-records, this fires for them
   too. In plain terms: **one page visit puts back part of what this iteration just cleared, for a
   quarantined day.** The same visit would also throw away the memory record this iteration
   deliberately kept. So the final check must either test cleanliness AFTER the app is allowed to
   start, or close this write first.
2. Asking a page for a date that has no day-record still creates one with no safety catch —
   `apps/backend/app/engine/scanner.py` contains ZERO references to the quarantine, and sixteen
   dates inside the damaged window (2026-05-14 … 2026-08-07) have prices but no record. Such a
   record would carry the same stamp as the eleven rebuilt ones, which is exactly why the final
   check must confirm membership from the recorded record numbers 3148–3158 and the execution
   evidence, never from the stamp.
3. Seven of the eleven damaged days still have no saved briefing (12 and 13 May, 10, 13, 24 and 27
   July, 3 August). With 12 August the newest day, all seven count as historical, so one ordinary
   page request would permanently create the very briefing the plan forbids
   (`apps/backend/app/engine/compass.py:1041-1066`, no safety catch anywhere in that file).

**FOUR THINGS THE FINAL CHECK MUST BE DESIGNED AROUND**, recorded so nobody rediscovers them:
(a) the kept memory record is safe today but the proof is a snapshot, not a standing promise — the
final check should re-run the safety test immediately before the app starts and delete the record if
the answer has changed (auditor B2, which I reproduced myself); (b) clearing two of the stores
removed a "serve last time's answer" fallback, so the first request after the app starts can now do
heavy work while the person waits — on a machine that froze once from memory pressure, the final
check should let the background warm-up finish before any request lands, and record the peak memory
(auditor B3); (c) the plan's claim that surviving days carry gaps is false for this codebase, so the
final check must read "zero" there as the right answer, not a missing repair (iteration 20's finding,
still binding); (d) the final check must confirm no twelfth day-record carries the repair stamp — I
verified today that exactly eleven do, ids 3148–3158.

**ONE MECHANICAL ITEM, now at its third repetition.** This iteration's four new backend files and its
whole evidence folder are STILL untracked at the time of scoring, and `HEAD` is still `fe17a81a`
(iteration 20). The quality check originally ticked "committed before scoring" on a false
observation; the auditor caught it and corrected it. Confirm the commit actually lands.

**SMALLER ITEMS, none of which changes the above:** the stored notes for the membership store in
`apps/backend/app/models.py:695-701` and `:712` both name the wrong stamp function and should be
fixed in a later, non-maintenance iteration (auditor B1); the deletion count falls back to a number
it did not observe if the driver stays quiet (B5); two delete fallbacks skip the late-row alarm (B6);
the "main file unchanged" line in the dev handoff was read before the database checkpointed, so it
overstates what the artifact shows (B7); the dev handoff says 75 tests when the true figure is 76
(T1); and J-04's screenshot still needs re-capturing the first time browser testing runs again — the
behaviour is proven, only the picture is wrong.

**FIVE OLDER OWNER QUESTIONS remain open and non-blocking:** whether 3.44 GB is acceptable for J-09;
J-06's "underlying run unavailable" wording; the rewording of J-01's first two test steps; whether an
empty "next-session focus" is acceptable; and whether MNST joins the recovery list.

**TWO STANDING FRAMEWORK NOTES:** the defect that once let a forbidden test lane run is still unfixed
in `scripts/automation/` — thirteen iterations running have avoided it with the maintenance-isolation
contract rather than curing it; and `goal_gate.py`'s duplicate-journey-heading defect is still unfixed
and must be closed before any GOAL_ACHIEVED certification. Per the owner's ruling, neither may be
touched until after Stage G.

**In one sentence for the owner: let the loop run the final check (Stage G) next, keep Trendora
switched off while it runs, and make sure this iteration's new files actually get committed.**
