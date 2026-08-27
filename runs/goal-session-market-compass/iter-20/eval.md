# Iteration 20 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The next step of the data repair was done, and it worked. The tool filled in 16,592 missing
performance records on the eleven damaged trading days, and it touched nothing else in the
database. I did not take that from anyone's write-up: I opened the 8.4 GB database read-only
and re-measured every important figure myself. The repair is not finished — two more steps
(F and G) remain before anyone may say the damage is fixed — and the Trendora app must stay
switched off until then. Nothing that used to work stopped working.

## Journey Results This Iteration

This iteration ran under **maintenance isolation**: starting the app, browser testing and the
replay lane were forbidden by contract (`reports/phase-goal-market-compass-iter-20-ui-test-results.md`
is all-SKIPPED, reason line names maintenance isolation; the engine's own refusal is recorded at
`runs/goal-session-market-compass/iter-20/maintenance-isolation-refusals`, 2026-08-26T21:40:14Z).
So every journey KEEPS its prior recorded status; none was promoted on this iteration's evidence.

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest on new runs | passing | passing (carried, not re-verified) | spot-check: `reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png` — GRMN shows a real stored sector "Consumer Discretionary" with "Not yet proven" badges; plus my own read-only query: rebuilt runs 3148/3158 carry 542/539 results with 0 missing sector labels |
| J-02 What changed since previous session | partial | partial (carried, not re-verified) | maintenance isolation — no lane ran |
| J-03 Plain-English summary with cited facts | partial | partial (carried, not re-verified) | maintenance isolation — no lane ran |
| J-04 Candidate explains why and why-not | passing | passing (carried, not re-verified) | `evidence_makeup: true` retained — the picture is still the wrong one; no capture was possible this iteration |
| J-05 Close freezes one manifest | partial | partial (carried, not re-verified) | maintenance isolation — no lane ran |
| J-06 A frozen manifest never changes | partial | partial (carried, not re-verified) | my own read-only query: all 24 manifests still dated 2026-08-20, none created or changed |
| J-07 Today page ten-second read | failing | failing (carried, not re-verified) | blocked by the Loop-mechanics gate until Stage G passes |
| J-08 Market page moves over intact | failing | failing (carried, not re-verified) | blocked by the Loop-mechanics gate until Stage G passes |
| J-09 Backend fits the host | partial | partial (carried, not re-verified) | maintenance isolation — no lane ran |
| J-10 Bounded recovery of two trading days | passing | passing (carried, not re-verified) | spot-check re-derived read-only: 585 price rows on each of 2026-08-11 and 2026-08-12; AVB volumes 554757 / 3706010 intact; `daily_prices` row count 3,310,374 and value total 52,367,098,848,872.56 identical to the iter-19 record |
| J-11 Incident-bounded clean regeneration | partial | **partial — advanced (Stage E complete)** | `runs/goal-market-compass-iter-20/j11-stage-e-execute-{preflight-gate,runs-check,population-report,mutation-accounting,memory-check,outcome}.json` + my own read-only re-derivation (below) |

**J-11 — what I verified myself, read-only, against the live database:**
- `forward_returns` now 6,814,320 (was 6,797,728) — delta **+16,592**, exactly the tool's own
  self-reported total. The 16,592 new rows occupy ids 6,844,114–6,860,705: a perfectly
  contiguous block ending at the table's maximum, containing no row belonging to any other run.
- Per rebuilt run: 2771, 2769, 2216, 2215, 1659, 1658, 1103, 1103, 549, 549, and 0 for the
  newest day (2026-08-12) — matching every lane's report.
- No-lookahead (AG-5): 0 of the 16,592 new rows measure on or before their own as-of date, and
  0 disagree with their run's as-of date. Newest measured date equals the newest stored price day.
- Nothing else moved: `scanner_runs` 3,128 with exactly ONE run per incident date (ids 3148–3158,
  created 2026-08-26 10:52:55.552946–10:53:02.010362, all stamped `53d2ffd1…` — byte-matching
  iteration 19's record); `next_session_manifests` 24, all created 2026-08-20; the quarantine row
  still `active=1` over exactly the 11 dates, unchanged since 2026-08-25 23:49:26.
- The load-bearing "zero repairs needed on the other 3,117 days" claim: I confirmed it two ways.
  Live data — 16,614 rows measure into an incident date from a non-rebuilt run, spread over exactly
  8 dates, and **zero** measure into 2026-08-10, 08-11 or 08-12, the only three where a real hole
  could sit. Code — I read `data_manager._cascade_targets` (`apps/backend/app/engine/data_manager.py:1967-2011`)
  and `remove_price_data` (`:2173-2192`): a run losing even one measurement bar is itself invalidated
  and its records deleted whole, so a surviving day carrying a partial hole is impossible by
  construction. The team's calendar-based explanation reaches the right answer by a weaker route
  (measurement dates resolve per symbol, not on one shared calendar), which the auditor caught.
- Tests: I ran them myself — **55 passed** (`apps/backend/tests/test_j11_stage_e_execute.py`,
  `test_j11_stage_e_execute_cli_script.py`), neither opening the real database.
- Memory: peak 769.3 MB against the 8,192 MB ceiling.

## Anti-goal Check

Worked from `runs/goal-session-market-compass/iter-20/scan-report.md` (CLEAN) and
`iter-diff.md` (4 files, all new backend files), plus my own reading of both production files.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unproven values must render "not yet proven" | OK | nothing displayed this iteration; no certified-claim ledger file changed (`git status` shows none) |
| AG-2 decision-quality only, no advice/orders | OK | forward returns are realized historical measurements; no page, wording or action added |
| AG-3 displayed numbers must be correct | OK | nothing displayed; rebuilt numbers re-derived above against the engine's own stored rows |
| AG-4 no overfit edges | OK | no pattern surfaced as proven; no selection or referee code touched |
| AG-5 determinism / no lookahead | **HELD — verified** | 0 of 16,592 new rows with measured date ≤ as-of date; 0 with a mismatched as-of date |
| AG-6 no shipping without referee verdict | OK | no evidence-derived claim made this iteration |
| AG-7 no hard-coded credentials | OK | scan-report CLEAN; my own grep of both production files found no key, token, password or URL |
| AG-8 resilience / no unbounded whole-table loads | OK | every query is a bounded aggregate or a column-projected 3,128-row read (`j11_stage_e_execute.py:238-242, 262-267, 305`); measured peak 769.3 MB vs 8,192 MB cap |
| AG-9 offline-deterministic ingest, no network | **HELD — verified** | zero network imports in either production file (my grep + the module's own AST test TC-20) |
| AG-10 host resource ceiling | OK, with a note | peak memory measured and recorded (769.3 MB / 8,192 MB) as the spec required; the maintenance script is not launched through `start-backend.sh`, matching how Stages C and D were run — measured-and-recorded, not capped in process |
| AG-11 no new composite candidate number | OK | no new score of any kind |
| AG-12 manifest immutability | **HELD — verified** | 24 manifests, every one created 2026-08-20, per-row per-column comparison equal; none minted, changed or deleted |
| AG-13 system-vs-market vocabulary separation | OK | terminal lines describe system state only |
| AG-14 no Tapeology coupling | OK | zero matches for "tapeology" anywhere in the four new files |
| AG-15 no outcome-tuned selection | OK | 16,592 realized returns were created but no selection rule or threshold was revised; `scoring.py`/`sectors.py` untouched |
| AG-16 cohorts are not controls | OK | untouched |
| AG-17 repair never rewrites provenance | **HELD — verified** | incident record `data_provider_runs` id=538 intact (11 runs, 16,566 records, dates 2026-08-11/12); the blocked first attempt kept and marked SUPERSEDED rather than deleted; quarantine still ACTIVE; no manifest's eligibility changed |
| AG-18 manifest migration preserves everything | OK | no migration this iteration |

**Result: no new violation, none unresolved. Ledger stays at 7 total, 0 unresolved.**
Coherence: COHERENCE-PASS. Deterministic scan: CLEAN. Review: PASS_WITH_NOTES (2 MINOR).
QA: PASS. Audit: PASS_WITH_GAPS (T1 IMPORTANT, fixed in-audit; B1/B2/B3/B4/T2 gaps;
B5/B6/B7 observations). Closure gate: CLOSURE-PASS.

## Next-Step Recommendation

**DO THE NEXT REPAIR STEP — Stage F, refreshing the stored answers the app keeps in memory.**
No one needs to approve it: the owner's written instruction in `docs/goal.md` (item 8) already
allows Stage F once Stage E succeeds, and Stage E succeeded cleanly. I read that instruction
myself rather than taking it from a report.

**KEEP THE APP OFF, and keep browser testing off.** This is the most important thing on the page,
and it has become MORE important, not less. I checked the two dangerous routes myself in the code:

1. `apps/backend/app/engine/scanner.py:338-348` still creates a new day-record for any date a web
   address asks for, and the file contains no quarantine check at all.
2. `apps/backend/app/engine/compass.py:1041-1060` still creates a saved briefing for any date that
   is not the newest one. Seven of the eleven damaged days (12 and 13 May, 10, 13, 24 and 27 July,
   3 August) have no saved briefing, and I confirmed that against the database. One ordinary page
   request for any of those seven would permanently create a briefing that never existed. That is
   exactly what the plan forbids by name.

Only the app being switched off prevents both. The owner's own instruction (item 5) already
defers fixing these until after the final step, so this is not new work — it is a rule to keep.

**THREE THINGS THE FINAL STEP (Stage G) MUST BE DESIGNED AROUND**, all recorded now so nobody
has to rediscover them:
1. The plan's own text says holes exist on days that survived the accident. They do not, and cannot
   — I proved that from the deletion code and from the live data. So the final check must read
   "zero" there as the correct answer, not as a missing repair.
2. The accident deleted 16,566 records; the repair created 16,592. The 26-record difference is
   expected (the underlying price data changed in between, and the repair must reflect today's data),
   but no saved document says so. Write it down before the final check asks "is this complete?".
3. The step's own safety check does not compare the creation time of the eleven rebuilt days and does
   not insist there is exactly one day-record per date. Today both are true — I verified it. But
   because a stray web request could still create a duplicate, the final check must test this
   properly rather than reuse the current weaker version.

**SMALLER ITEMS, none of which changes the above:** three of the tool's own self-checks pass without
really testing anything (one compares zero against a hard-coded zero) — worth tightening when the
next stage copies this code; one unused import; and the retained record of the blocked first attempt
still ends with a stale "STAGE E COMPLETE: NO" line, which a careless search would find.
**ONE MECHANICAL ITEM:** this iteration's four new backend files and its whole evidence folder are
still untracked in git at the time of scoring — confirm they reach version control.
**FIVE OLDER OWNER QUESTIONS** remain open and non-blocking: whether 3.44 GB is acceptable for J-09
"The backend fits the host"; J-06 "A frozen manifest never changes" and its "underlying run
unavailable" wording; the rewording of J-01 "Sector labels are honest" first two test steps; whether
an empty "next-session focus" is acceptable; and whether MNST joins the recovery list.
**TWO STANDING FRAMEWORK NOTES:** the defect that once let a forbidden test lane run is still
unfixed in `scripts/automation/` — twelve iterations running have avoided it with the
maintenance-isolation contract rather than curing it; and `goal_gate.py`'s duplicate-journey-heading
defect is still unfixed and must be closed before any GOAL_ACHIEVED certification.

**In one sentence for the owner: let the loop continue to Stage F, and do not let anyone start
Trendora or open a browser against it until the final step (Stage G) has passed.**
