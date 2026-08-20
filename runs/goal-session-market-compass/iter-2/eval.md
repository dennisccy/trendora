# Iteration 2 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The home page now answers three of the eight questions the goal asks for: a plain-English summary of
the market, a list of what changed since the previous session, and a "next-session focus" section
that explains why each name was chosen and why twenty others were not. I checked the four pictures
myself rather than trusting the write-ups, and the numbers in the new text match the older tiles
sitting further down the same page, so the new words are quoting the site's own figures. Nothing
that worked before stopped working. I am still returning ESCALATE, because the engine ran this
iteration in the light "lean" mode although its own plan asked for the full mode, so the independent
auditor, the visual-regression check and the walkthrough recorder never ran — and the developer
raised a genuine product question (today no stock passes all three selection rules, so the headline
section is honestly empty) that those missing lanes were supposed to settle.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels are honest and nearly complete | partial | passing (`evidence_makeup`) | `reports/qa/goal-market-compass-iter-2-evidence/UT-J-01-result.png`; row UT-J-01 in `reports/phase-goal-market-compass-iter-2-ui-test-results.md` |
| J-02 What changed since the previous session | failing | passing (`evidence_makeup`) | `reports/qa/goal-market-compass-iter-2-evidence/UT-J-02-result.png`; row UT-J-02 |
| J-03 Plain-English summary with cited facts | failing | passing (`evidence_makeup`) | `reports/qa/goal-market-compass-iter-2-evidence/UT-J-03-result.png`; row UT-J-03 |
| J-04 Each candidate explains why and why-not | failing | passing (`evidence_makeup`) | `reports/qa/goal-market-compass-iter-2-evidence/UT-J-04-result.png`; row UT-J-04 |
| J-05 Each close freezes one manifest | failing | failing (not re-tested; out of scope) | `reports/qa/goal-market-compass-iter-0-evidence/UT-J-05-fail.png` |
| J-06 A frozen manifest never changes | failing | failing (not re-tested; out of scope) | `reports/qa/goal-market-compass-iter-0-evidence/UT-J-06-fail.png` |
| J-07 The Today page answers the ten-second read | failing | failing (not re-tested; out of scope) | `reports/qa/goal-market-compass-iter-0-evidence/UT-J-07-fail.png` |
| J-08 Market page moves over intact | failing | failing (not re-tested; out of scope) | `reports/qa/goal-market-compass-iter-1-evidence/UT-J-08-fail.png` |

### What I verified personally (not taken from the reports)

- **Numbers are real (AG-3), proven inside the screenshots.** In `UT-J-02-result.png` the Summary
  card cites regime score 73.24, severity 25.84, breadth 59.84% / 66.39% — and the pre-existing
  Market Regime tile, Market Phase & Severity tile and More-detail breadth cards further down the
  *same image* read 73.24, 25.84, 59.84%, 66.39%. In `UT-J-04-result.png` the same holds at as-of
  2026-07-23: summary text 57.9 / 36.6 / 39.3% / 57.4% against tiles 57.87 / 36.61 / 39.34% / 57.38%.
- **`UT-J-03-result.png` shows the cited-facts disclosure open**, listing each sentence's template id
  and facts. I confirmed in code that those labels really are the template ids, not a nicer synonym:
  `apps/backend/app/engine/compass.py:90,117,142,153` emit `"state"`, `"direction"`, `"breadth"`,
  `"focus_count"`, rendered at `apps/frontend/components/compass-summary-card.tsx:45`.
- **`UT-J-02-result.png`** shows the What-changed header "vs 2026-08-11 (1 day ago)", 17 entries in
  kind order (5 Sector, 2 Theme, 10 Stock) and a "Suppressed moves (28)" disclosure.
- **`UT-J-04-result.png`** shows the GWW card with three WHY lines each citing threshold and actual,
  the ATR caution, a 3-row eligibility checklist all Pass, a "What would change this" panel, the
  invalidation note, and "Not priority (20)" with per-name distances.
- **`UT-J-01-result.png`** shows `/stocks` at as-of 2026-08-12 with GRMN = "Consumer Discretionary",
  1/539 filtered, and the three "Not yet proven" chips intact (AG-1 holds).
- Code-level checks I ran myself: no UPDATE or DELETE path on `next_session_manifests`
  (`compass.py:441-475`), the table is absent from the remove-data cascade in `data_manager.py`, no
  network client anywhere in the 27-file diff, no launch script or host-guard file touched.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 no unproven "proven" claims | OK | `UT-J-01-result.png` shows the three "Not yet proven" chips unchanged on the GRMN row; no confidence or proven wording added in the new narrative templates. |
| AG-2 decision-quality only, never advice | OK — MINOR wording note | Candidate framing is "worth monitoring next session"; the Risk-off caution reads "context, not a signal to act" (`compass.py:301-305`). MINOR: the ATR caution ends "— sized risk accordingly" (`compass.py:294`), which reads as advice and brushes the goal's own "no position sizing" non-goal. Related gap: the runtime banned-word guard (`compass.py:175-183`) is called only from `build_narrative` (`:208`), so candidate reasons/cautions/why-not strings are unchecked. Neither is critical; both belong in the next iteration. |
| AG-3 displayed numbers correct | OK | Verified by the evaluator inside two screenshots (see above), plus the browser lane's byte-exact spot-checks of sector rank 21→25 and SMCI bucket E→D at both dates. |
| AG-4 no overfit edges | OK | No Evidence Claim, ledger entry or referee interaction anywhere in the diff. |
| AG-5 determinism / no lookahead | OK | `session_delta.py` contains no `forward_returns` / `bars_after` reference (grep + AST test `test_no_forward_returns_or_lookahead_import`); `compass.py` guarded by `test_no_network_or_lookahead_imports_in_compass_module`; `_record_json_by_ticker` deliberately avoids `filtered_stock_rows` because that helper attaches forward returns. `_is_retrospective` (`compass.py:167-172`) does read whether a LATER run exists, but only to add the honesty stamp J-03 step 6 requires; it feeds no number. |
| AG-6 referee gate | OK | No Evidence Claim introduced this cycle; the gate passes automatically, as goal.md states. |
| AG-7 no credentials in source | OK | `iter-2/scan-report.md` = CLEAN; I additionally grepped added lines for api_key/token/password/secret — no product match; no new config or env file. |
| AG-8 data-shape / scale resilience | OK | Column-projected selects only, enforced by `test_column_projected_reads_only_no_full_record_json_sweep`; `_record_json_by_ticker` bounded to the selected tickers; `max_stock_items` bounds the stock sweep; the three cards degrade to an honest "unavailable" state when the API is unreachable. |
| AG-9 offline-deterministic ingest | OK | No `requests`/`httpx`/`urllib`/`aiohttp` in any of the 27 changed files; no dependency manifest changed; everything reads already-stored runs. |
| AG-10 host resource ceiling | OK | No file under `scripts/` and no `host-guard` file appears in the changeset (checked the full file list in `iter-diff.md`); no cap value touched. |
| AG-11 no new composite number | OK | The candidate card carries exactly the three existing scores (81.2 / 70.3 / 43.3 in `UT-J-04-result.png`); `test_compass.py:209` asserts no other numeric field exists. |
| AG-12 manifest immutability | OK | SELECT plus one INSERT, no UPDATE/DELETE (`compass.py:441-475`); table absent from the clear/remove cascade. Reviewer's NOTE about the retrospective stamp being a generation-time signal is a J-05/J-06 formalisation item, not a breach. |
| AG-13 system vs market vocabulary | OK | No readiness token appears in the two new engine modules (grep); in the screenshots "Ready"/"GO" appear only in the pre-existing top chrome, never inside the compass cards. |
| AG-14 no Tapeology coupling | OK | Zero occurrences of "tapeology" anywhere in the iteration diff. |
| AG-15 no outcome-tuned selection | OK — actively upheld | Thresholds are the spec-prescribed 80.0 / 70.0 / 60.0 in `config.yaml:1417-1419`; the developer explicitly refused to loosen them when they produced zero candidates (dev handoff, Known Issue 1). That refusal is the AG-15-correct behaviour. |
| AG-16 cohorts are not controls | OK | The comparison and shadow cohorts are not built this iteration; `test_compass.py:220` proves "shadow" appears nowhere in the served payload; the why-not list states rule distances only, with no causal framing. |

**Coherence:** `runs/goal-session-market-compass/iter-2/coherence.md` = **COHERENCE-PASS** — one
producer per value, no duplicate home, no new route. No structural veto.
**Goal-edit drift:** no `journeys-changed.md`; I re-computed every journey hash with
`goal_gate.py hash-journeys` and all eight match the recorded values, so no prior pass is void.
**Review lane:** PASS_WITH_NOTES — the pipeline did not proceed fail-open.

## Next-Step Recommendation

Run the next iteration in **full** mode and build **J-05 "Each close freezes one next-session
manifest"** together with **J-06 "A frozen manifest never changes"**. These two turn the daily
briefing into a sealed, dated, tamper-evident file that can never be altered afterwards. It is the
riskiest part of the whole plan — twelve separate promises have to be proved — and the substrate it
extends (the storage table, the endpoint, the compute-once path) already landed this iteration, so
it is ready to build.

Carry three small jobs along with it. None is big enough to deserve a turn of its own:

1. Record the missing walkthroughs for J-01 to J-04, and take one picture of the "Risk-off" warning
   state on 2026-03-30.
2. Reword the ATR caution so it stops sounding like advice, and extend the automatic banned-word
   check to cover the candidate reason and caution lines, not just the summary sentences.
3. Note for the builder: the summary's cited fact currently prints `-0.20000000000000284` instead of
   `-0.20` (visible in `UT-J-03-result.png`) — the value is right, only its display is untidy.

Two things need the owner, not the robot:

- **Please approve rewording J-01's first two test steps.** Step 1 tells the tester to delete and
  rebuild two days of data, which in this offline setup destroys data that cannot be recovered. Step
  2 tells the tester to pick an "Unassigned" option in the sector filter that no longer exists, now
  that every stock has a sector. Both steps are unusable as written.
- **Please decide about the empty focus list.** On the newest date, not one stock passes all three
  selection rules at once, so the "next-session focus" section honestly shows nothing. That is
  correct behaviour, not a fault. Say whether you accept it as-is, or whether the three cut-off
  numbers should be revisited — bearing in mind the rules forbid changing them just because past
  prices would have looked better.

## Halt Justification (if halting)

Not halting. ESCALATE keeps the loop running; it only forces the next iteration to use the full
pipeline. The reason is that this iteration was dispatched at lean depth
(`runs/goal-session-market-compass/iter-2/depth-dispatched` = `lean`) even though its own plan
recorded `**Depth:** full` and the previous evaluation's recommendation was binding-full. As a
result three safety lanes never ran on the largest change of the session so far — a new engine
producer, a new stored table, a new step in the data-loading tail, a new API address and three new
cards on the home page. The independent auditor lane matters here specifically: one iteration ago it
caught a real bug in which a new disclosure shipped hidden from users. It also never saw the
developer's own explicitly-raised triage question about the empty candidate list. The walkthrough
recorder, likewise skipped, is why all four passing journeys carry an evidence make-up flag.
