# Iteration 29 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The one job this round was asked to do was done, and done well. One allowed request created a
saved daily briefing for 3 August 2026, and on that date the Today page now says in plain words
whether things are improving or getting worse — "improving", "improving", "little changed" — and
the sentence just below it agrees. I checked the three words myself against the stored numbers and
the rule file, and I checked that not one of the twenty-six older briefings was changed. But the
journey is still not finished: on the page a user actually lands on, all three words still read
"NA" while the sentence one line below reports a real change. The goal file says the reader must
get direction "from `/` alone", so I am holding J-07 "The Today page answers the ten-second read"
open for one more small piece of work.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels are honest | passing | passing (re-verified, replay) | reports/qa/goal-market-compass-iter-29-evidence/J-01-verify.png |
| J-02 What changed since the previous session | partial | partial (not targeted, carried) | reports/qa/goal-market-compass-iter-6-evidence/ (unchanged) |
| J-03 Plain-English summary with cited facts | partial | partial (not targeted, carried) | reports/qa/goal-market-compass-iter-6-evidence/ (unchanged) |
| J-04 Each candidate explains why and why-not | passing | passing (re-verified, replay) | reports/qa/goal-market-compass-iter-29-evidence/J-04-verify.png |
| J-05 Each close freezes one manifest | passing | passing (re-verified, replay) | reports/qa/goal-market-compass-iter-29-evidence/J-05-verify.png |
| J-06 A frozen manifest never changes | passing | passing (re-verified, replay) | reports/qa/goal-market-compass-iter-29-evidence/J-06-verify.png |
| J-07 Today page ten-second read | partial | **partial** (step 3 now live on one date; landing view still NA) | reports/qa/goal-market-compass-iter-29-evidence/UT-02-result.png · UT-03-result.png · UT-06-result.png · **UT-04-result.png (gap)** |
| J-08 Market page moved over intact | passing | passing (re-verified, replay) | reports/qa/goal-market-compass-iter-29-evidence/J-08-verify.png |
| J-09 Backend fits the host | partial | partial (not targeted, carried) | reports/qa/goal-market-compass-iter-25-evidence/ (unchanged) |
| J-10 Bounded recovery of two deleted days | passing | passing (re-verified, replay + spot-check) | reports/qa/goal-market-compass-iter-29-evidence/J-10-verify.png |
| J-11 Incident-bounded clean regeneration | passing | passing (re-verified, replay) | reports/qa/goal-market-compass-iter-29-evidence/J-11-verify.png |

Merged browser results: `reports/phase-goal-market-compass-iter-29-ui-test-results.md` — 15/15 PASS,
0 skipped, no `DEFERRED-BUDGET` rows, no `browser-infra.json`, no `journeys-changed.md`, NOT
maintenance isolation. All eleven `spec_hash` values are byte-identical to the recorded ones (I ran
`goal_gate.py hash-journeys` and compared every one).

Spot-checks I opened myself (2, per methodology A.4): **J-04** — again the 2026-03-30 top-of-page
viewport stopping above the candidate card, so `evidence_makeup: true` is KEPT for the eleventh
iteration running; **J-10** — AVB at 2026-08-11 renders real figures and "Invalid below the 50-DMA
at $187.94", the golden's exact value. Neither contradicts its recorded status.

## What I re-derived myself (read-only, not taken from any report)

| Claim | My check | Result |
|---|---|---|
| One row minted, nothing else | `select count(*)` on `next_session_manifests` | **27**, ids 1..27 with none missing; exactly 1 row for `2026-08-03` (id 27, version 1, retrospective, `prospective_eligible=0`) |
| AG-12 after EVERY lane | dumped the 26 non-`2026-08-03` rows to CSV and diffed against the preserved pre-mint snapshot | sha256 `c070dcf1c29e9824cacd8f715fb5d40b498888dfd5001e388ab4a1f46c2d7218` on both; `diff` empty — byte-identical |
| Exported files untouched | `apps/backend/data/exports/next_session_manifests/` mtimes | newest file `2026-08-12_v6.json` at 2026-08-20 15:50 — nothing written, changed or deleted this iteration |
| The three words are correct (AG-3) | stored runs + `config.yaml` thresholds | regime 66.07−61.41 = **+4.66** vs `velocity_flat_band` 2.0 → "improving"; severity 29.35−35.52 = **−6.17** vs `stress_velocity_flat_band` 5.0, polarity flipped → "improving"; breadth 45.08−45.90 = **−0.82** vs `breadth_min_change_pts` 5.0 → "little changed". All three match the badges on screen and the stored `state_band_json`. |
| The gap is total elsewhere | `select count(*) ... where state_band_json is not null` | **1 of 27** |
| No outside data was fetched (AG-9) | newest `data_provider_runs` row | id 549, 2026-08-23 — eight days before this iteration; zero provider activity |
| Nothing else in the database moved | row counts | `scanner_runs` **3128**, `daily_prices` **3,310,374**, manifests with `prospective_eligible=1` **0**, `next_session_manifests` column count **29** — every one identical to the iter-27/28 recorded baselines |
| The new golden never ran (auditor T1) | file mtimes | `journey-scripts/J-07.json` 23:50:41 vs `J-07-verify.png` 23:47:10 — the added step 4 was written after the replay ran, and it asserts the narrative sentence, not the three badge testids; `grep` finds no badge testid in any golden |

## Anti-goal Check

Worked from `iter-29/scan-report.md` (**CLEAN**) and `iter-29/iter-diff.md` (**one file changed:
`README.md`** — documentation only; zero source-code change, confirmed independently by the dev
handoff, the UI surface map and the coherence audit).

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 no unproven "edge" presented as proven | OK | No claim surface touched; no evidence-ledger entry added. |
| AG-2 decision-quality only | OK | Screenshots read "Research-only · decision support · no orders"; no verbs, targets or signals anywhere on the captured pages. |
| AG-3 displayed numbers correct | OK | Re-derived all three direction words and both tile values myself from stored runs + config (table above). |
| AG-4 no overfit edges | OK | No referee/holdout surface touched. |
| AG-5 determinism / no lookahead | OK | The new manifest for 2026-08-03 compares against 2026-07-27, the immediately preceding stored run; both at or before the as-of. Mode is `retrospective` and says so on screen. |
| AG-6 evidence claims refereed | OK | No Evidence Claim introduced. |
| AG-7 no hard-coded credentials | OK | Deterministic scan CLEAN; only `README.md` in the product diff. |
| AG-8 data-shape/scale resilience | OK | No schema or field change; the card renders "NA" without throwing for the 26 rows that lack the field (`compass-state-band-card.tsx` uses a null-safe read). |
| AG-9 offline-deterministic ingest | OK | Newest provider run is 2026-08-23 (id 549) — I checked the table myself. The one authorized call reads already-stored state only. |
| AG-10 host resource ceiling | OK | No launch script or host-guard file in the diff. |
| AG-11 no new composite number | OK | No new score; the three words come from the committed word map. |
| AG-12 manifest immutability | OK | Re-derived by me AFTER every lane: 26 pre-existing rows byte-identical, exports untouched, one additive row created (creation is permitted; mutation and deletion are not). |
| AG-13 system vs market separation | OK | In every capture "Ready"/"GO" sit in the chrome above the body; "Risk-on"/"Expansion" appear only inside the body. |
| AG-14 no Tapeology coupling | OK | Nothing in the diff references it. |
| AG-15 no outcome-tuned selection | OK | No threshold changed. |
| AG-16 cohorts are not controls | OK | No cohort narrative added; the new row is `prospective_eligible=0`. |
| AG-17 repair never rewrites provenance | OK | The new row is retrospective and prospective-ineligible; no older row's version, hash, timestamp or eligibility changed. |
| AG-18 authorized migration preserves everything | OK | No schema change this iteration; the manifest table still has 29 columns, the same as after iter-28. |

**New violations: none.** The ledger stays at **9 total, 0 unresolved**.

One thing I considered and decided is NOT a ledger entry: the deterministic replay lane requested
three dates outside this iteration's declared safe list (`2026-03-30`, `2026-07-23`, `2026-08-11`),
which the auditor found and flagged (B1). Unlike the comparable iter-27 event, nothing permanent
resulted — each of those dates already had a stored briefing, and I confirmed myself afterwards that
the table holds exactly 27 rows with the 26 older ones untouched. So this is a process-record gap
that the auditor has already corrected in the handoff, not a broken rule.

## Pipeline health

Depth dispatched: **full — as the spec required.** `iter-29/depth-dispatched` reads `full`; the
full→lean demotion that hit iterations 2, 6, 8, 23, 24, 26 and 28 did NOT recur. My predecessor's
iter-28 ESCALATE bought it. Reviewer **PASS_WITH_NOTES** (one MINOR — a pre-existing red test),
QA **PASS** / UI-PASS, coherence **COHERENCE-PASS**, closure **CLOSURE-PASS**, auditor
**PASS_WITH_GAPS** (findings B1, B3, F1, T1, T4 — I re-derived B1, F1 and T1 myself and all three
are accurate). UX-regression was **SKIPPED** by the wall-clock budget trim (non-blocking lane).
The auditor lane was again the one that found what the earlier lanes missed — the twentieth
iteration running.

## Next-Step Recommendation

FINISH J-07 "The Today page answers the ten-second read". Only one piece is missing: make the three
direction words appear on the page a person lands on. Right now they appear on 3 August 2026 and
nowhere else, and the front page still shows "NA" beside a sentence that reports a real change on
the very same screen. The known, already-proven way to fix this is to create a NEW VERSION of the
saved briefing for the newest date, 12 August 2026 — the same kind of action the product already
performed successfully at iteration 26 for a different date. The older versions must stay exactly as
they are, and the new one must stay marked as not usable as forward-looking evidence. The next plan
must name that one date and permit no other, and must re-check the briefing table after every lane
has finished, exactly as this round did.

RUN IT AT FULL DEPTH. This is a permanent write to the protected briefings table on the newest date
— the most sensitive write this project has attempted — and this round is fresh proof that the
independent checker earns its keep: it alone caught that the safe-date rule was only enforced for
one lane, that the front page still contradicts itself, and that the new automatic re-test guards
the wrong sentence and never actually ran. Only the owner may add the `Depth enforcement: required`
line; standing guidance keeps `CHAIN_REQUIRE_FULL_DEPTH` and `CHAIN_MAINTENANCE_ISOLATION` OFF.

ONE QUESTION FOR THE OWNER THAT COULD END THIS IMMEDIATELY: if you decide that showing the
direction words correctly on one real date is enough, and that the front page reading "NA" is
acceptable because the data set has no newer trading day, then J-07 is finished today and no
further work is needed. I have written that choice into the assumption ledger so you can settle it
with one line.

TWO REPAIR ITEMS THAT SHOULD RIDE ALONG, small and not blocking: (1) the automatic re-test for the
Today page checks a sentence that already worked before this feature existed, so the three new words
have no automatic guard at all — point it at the three badges instead; (2) the recorded walkthrough
for this round shows "NA" in the three frames that claim to demonstrate the new words, because the
clicks did not work — re-record it as a passenger task, never as an iteration goal.

SEVEN CARRIED ITEMS, none blocking: J-04's picture still needs re-taking to include the candidate
card (eleventh round owed); J-05, J-06, J-07 and J-08 all still owe a recorded walkthrough; one
test in the named test set is red on three files nobody has touched since an old commit
(`indicators.py`, `forward_testing.py`, `research.py`) and should be fixed or formally waived; the
"What changed" and "Leadership rotation" lists still show the same rows on some dates (keep, merge
or narrow — owner's call); the iteration-23 throw-away copy (7.8 GB) may still be deleted; the
automatic re-test lane replays its own stored dates, so future plans should say that the safe-date
rule applies to new writes only, as this round's plan correctly did; and J-01's automatic re-check
still asserts far less than the journey claims. FIVE OLDER OWNER QUESTIONS remain open and
non-blocking: J-09's ~2.99 GB acceptability; J-06's "underlying run unavailable" wording; J-01's
first two test steps; whether an empty "next-session focus" is acceptable; whether MNST joins the
recovery list. ONE STANDING FRAMEWORK NOTE: `goal_gate.py`'s duplicate-journey-heading defect is
still unfixed (this round's goal slice again lists J-10 twice) and must be closed before any
GOAL_ACHIEVED certification.
