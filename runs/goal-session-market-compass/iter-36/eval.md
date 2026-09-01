# Iteration 36 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The work asked for this round was done, and I checked it myself instead of trusting the reports. The
Leadership rotation panel on the Today page now serves its own content: two labelled sides per group
(gaining and losing), a signed number, and a plain word saying whether the move is better or worse. I
opened the freshly written data file and re-counted every row against the stored rankings — all nine
rows match exactly, and the counts now add up to every one of the 31 sector groups and all 11 themes,
closing the two-groups-missing hole from last round. Nothing that already worked was disturbed.

I am still not closing the project this round, for two reasons that have nothing to do with whether the
feature works. First, this round was supposed to run the FULL checking team, its own plan says so in
writing, and the previous round's binding note said a drop to the light team "must be surfaced
explicitly and marked unmet". The light team ran instead, and nobody said so. The independent checker,
the quality lane, the visual-change reviewer and the sign-off lane never ran — on the one round that
rewrote a real screen. Second, the single picture meant to show that new screen is completely empty: a
flat dark rectangle with exactly one colour in it. So no picture of the new panel exists anywhere. The
light team did work well here — its reviewer caught a fault that would have crashed the Today page on
every past date — which is itself the reason the fuller check is worth one more round.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest | passing | passing (carried, not re-tested) | reports/qa/goal-market-compass-iter-35-evidence/J-01-verify.png (A.6 durability; no scanner/market-page file in the diff) |
| J-02 What changed | passing | passing | reports/qa/goal-market-compass-iter-36-evidence/J-02-verify.png + my own v8-vs-v9 comparison (17 entries, order, thresholds, suppressed 36 all identical) |
| J-03 Plain-English summary | passing | passing (carried, not re-tested) | reports/qa/goal-market-compass-iter-35-evidence/J-03-verify.png; `narrative` block byte-identical v8 vs v9 |
| J-04 Candidate why / why-not | passing | passing | reports/qa/goal-market-compass-iter-36-evidence/J-04-verify.png (crop defect, 18th round — `evidence_makeup` kept) |
| J-05 Freeze + export | passing | passing | reports/qa/goal-market-compass-iter-36-evidence/J-05-verify.png; v7 md5 `d905dcfeb788…` unchanged, all pre-existing exports predate the snapshot |
| J-06 Frozen manifest never changes | passing | passing | reports/qa/goal-market-compass-iter-36-evidence/J-06-verify.png; v1..v8 rows/files untouched while v9 was minted |
| J-07 Today page ten-second read | passing | passing | reports/qa/goal-market-compass-iter-36-evidence/J-07-verify.png (66.07 / 29.35 / 45.1%, +4.7 pts — matches iters 29-34 to the decimal) |
| J-08 Market page intact | passing | passing | reports/qa/goal-market-compass-iter-36-evidence/J-08-verify.png |
| J-09 Backend fits the host | passing | passing (carried, not re-tested) | runs/goal-market-compass-iter-34/j09-vmpeak-samples-*.csv; `warmup.py`/`prices.py` untouched, memory caps unmoved |
| J-10 Bounded data recovery | passing | passing (carried, not re-tested) | reports/qa/goal-market-compass-iter-34-evidence/J-10-verify.png; price frontier still 2026-08-12 |
| J-11 Clean regeneration | passing | passing (carried, not re-tested) | reports/qa/goal-market-compass-iter-34-evidence/J-11-verify.png; `prospective_eligible=1` on 0 rows |
| J-12 Frozen disposition true | passing | passing | reports/qa/goal-market-compass-iter-36-evidence/J-12-verify.png; re-derived on v9: 502 + 27 = 529 cohort + 10 candidates = 539, zero mislabelled |
| **J-13 Leadership rotation** | **failing** | **passing** (`evidence_makeup`) | Results row UT-J-13 PASS; **acceptance screenshot `UT-J-13-rotation-both-directions.png` is 100% blank (one colour)** — substance re-derived by me from `2026-08-12_v9.json` + stored ranks in runs 3157/3158; real browser image at `reports/qa/goal-market-compass-iter-36-evidence/J-13-legacy-asof-rotation-not-recorded.png` |

Deterministic gates, all run by me: `results` exit 0 · `journeys` exit 0 `{"total":13,"passing":13,"blocking":[]}` ·
`regressions` pre→post exit 0 · `coherence --for-achievement` exit 0 · drift `changed: []`.
Merged results 8/8 executed PASS, 0 skipped, 0 FAIL, 0 `DEFERRED-BUDGET`. No `browser-infra.json`, no
`journeys-changed.md`, NOT maintenance isolation. Golden hygiene clean: every replayed golden's mtime
predates the 13:30 replay run.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven/confident language | OK | Zero added strings claim proof; rotation words are only `improving`/`deteriorating` from the existing `compass.vocabulary.direction_words` map. |
| AG-2 no advice/orders | OK | Grep of added frontend lines for buy/sell/target/forecast/guarantee: zero hits. |
| AG-3 displayed numbers correct | OK | All 7 sector + 2 theme rotation rows' from/to and signed delta re-derived by me against `sector_scores`/`theme_scores` at runs 3157 (2026-08-11) and 3158 (2026-08-12): exact match, including the two previously uncounted rows. |
| AG-4 no overfit edges | OK | No Evidence Claim, referee entry, or forward-return use introduced. |
| AG-5 determinism / no-lookahead | OK | Rank pairs read only the two named runs; no forward-return code touched. |
| AG-6 referee verdict for claims | OK | No evidence-derived claim shipped; evidence/referee paths have an empty diff. |
| AG-7 no credentials | OK (critical) | `scan-report.md` CLEAN; my own grep of added lines for key/secret/token/password/bearer: zero hits. |
| AG-8 data-shape/scale resilience | OK (critical) | New reads are column-projected `select(ticker, name, rank)` bounded to one `run_id` (31/11 rows) — no whole-table or `record_json` sweep. The legacy-row branch degrades honestly instead of crashing (this was the review's round-1 CRITICAL, now fixed and re-verified live). |
| AG-9 offline ingest | OK | Zero URLs added; no ingest job touched; `data_provider_runs` still 549. |
| AG-10 host resource ceiling | OK (critical) | `host-guard.env` untouched (mtime 2026-08-19); `memory_cap_mb` 8192, `malloc_arena_max` 2, `pool_size` 24, `max_overflow` 44 all show an empty diff. |
| AG-11 no new composite number | OK (critical) | Rotation row keys are exactly `{label, from, to, delta, direction_word, drill_href}`; `delta` is a signed integer rank difference, not a blended score. Banned-term scan of the whole rotation block: zero hits. |
| AG-12 manifest immutability | OK (critical) | v1..v8 rows and files byte-untouched; v7 md5 `d905dcfeb7883d86602d64d4c24682ad` still matches iter-35's record; the correction shipped as a NEW v9 minted via the sanctioned regenerate route on the frontier as-of. |
| AG-13 system-vs-market vocabulary | OK | New strings are group-rotation wording only; no readiness vocabulary added. |
| AG-14 no Tapeology coupling | OK | Zero `tapeology` hits in the diff. |
| AG-15 no outcome-tuned selection | OK (critical) | `config.yaml` diff is exactly ONE added line (`rotation_top_k: 5`); no existing threshold value changed; `compass.selection.*` and `evaluate_selection` untouched. |
| AG-16 cohorts are not controls | OK | `comparison_cohort` and `near_threshold_shadow` byte-identical between v8 and v9. |
| AG-17 repair never rewrites provenance | OK (critical) | `prospective_eligible = 1` on 0 rows; no `available_at_utc`, version, or hash of any stored row changed. |
| AG-18 authorized migration preserves everything | OK | No migration run this iteration. |

Ledger unchanged: **9 total, 0 unresolved.** No new violation, minor or critical.

## Next-Step Recommendation

Run one more round at FULL depth and make it a closing round — there is no new feature work left to do.
Three concrete things must come back green, and all three are cheap:

1. **Actually run the full checking team.** This round's plan said full, the engine ran the light team,
   and nobody flagged it. The proof that it ran is simple: files for the independent checker, the
   quality lane, the visual-change reviewer and the sign-off lane must exist on disk for iteration 37.
   Do not accept a marker file as proof; check for the reports themselves.
2. **Take the Leadership rotation picture again.** The one taken this round is completely blank, so
   nobody has ever seen a picture of the new panel. This rides along as a passenger task, never as the
   round's purpose.
3. **Replay the new J-13 check script.** It was written at 13:35, five minutes after the replay run at
   13:30, so it has never actually been executed once. Running it is the only way to know the new panel
   can be re-checked automatically in future rounds.

Two small repairs carried from last round can ride along if the developer is already in those files:
raise the test fixture's risk value above 60.0, and turn the two bare guard statements into real errors.

**One point for the owner, not blocking.** The rotation panel shows up to five rows on each side, while
the "What changed" list above it shows five per group in total. So a mover can appear in the rotation
panel but not in the list above — this round, two sectors (Banks and Technology) do exactly that. That
is deliberate and is what closes the counting hole, but if you would rather the two panels always show
the same rows, say so and it is a small change.

**Still owed, and never a round of their own:** J-04's picture is now 18 rounds owed with the same wrong
crop, and eight journeys still owe a labelled step-by-step recording. Both are photography tasks on
features that already work.

**One mechanical item:** the whole iteration is uncommitted at scoring time; confirm it lands.

## Halt Justification (if halting)

Not halting. ESCALATE keeps the loop running and forces the next round to use the full checking team.

For the record, so nobody thinks I overlooked it: every automatic gate passes right now — all thirteen
journeys are recorded as working, nothing broke, no rule was broken, and the structure check passed. A
"finished" verdict was mechanically available and I am declining to give it for one round only. The
reason is that this round did not perform the checking it was told to perform, and the one picture of
its new screen is empty, so a "finished" stamp would rest on a round that skipped its own inspection.
The same thing happened at iteration 33; the round after it ran the full team, which then found five
real problems nobody else had found. That is the cost of one extra round, and it is worth paying once.
