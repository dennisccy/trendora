# Iteration 35 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The one job this round set out to do was done, and I checked every number myself instead of
believing the write-up. A label shown next to company names was simply false: 37 of 539 names were
marked "below the selection floor" when their leadership scores were actually above it — the best of
them, HPE, scored 92.7 against a floor of 80. After the fix, that count is zero, and the three groups
add up exactly (502 + 27 + 10 = 539). Nothing that already worked broke, and no frozen record was
altered: the old, wrong file is still on disk with its original fingerprint, exactly as the project's
own rules demand.

The goal is not finished, because the goal grew. Two new must-have jobs were added to the goal file on
1 September. This round built the first one (J-12). The second one, J-13 "Leadership rotation says
which way", has not been started, and I confirmed by hand that it does not work today. So 12 of 13
jobs pass and 1 fails.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest and near-complete | passing | passing (replay) | reports/qa/goal-market-compass-iter-35-evidence/J-01-verify.png |
| J-02 What changed since previous session | passing | passing (replay) | reports/qa/goal-market-compass-iter-35-evidence/J-02-verify.png |
| J-03 Plain-English summary with cited facts | passing | passing (replay) | reports/qa/goal-market-compass-iter-35-evidence/J-03-verify.png |
| J-04 Candidate explains why and why-not | passing | passing (replay; **spot-checked by me**) | reports/qa/goal-market-compass-iter-35-evidence/J-04-verify.png |
| J-05 Each close freezes one manifest | passing | passing (replay) | reports/qa/goal-market-compass-iter-35-evidence/J-05-verify.png |
| J-06 A frozen manifest never changes | passing | passing (replay; **spot-checked by me**) | reports/qa/goal-market-compass-iter-35-evidence/J-06-verify.png |
| J-07 Today page answers the ten-second read | passing | passing (replay) | reports/qa/goal-market-compass-iter-35-evidence/J-07-verify.png |
| J-08 Market page moves over intact | passing | passing (replay) | reports/qa/goal-market-compass-iter-35-evidence/J-08-verify.png |
| J-09 Backend fits the host | passing | passing (carried, A.6 — not in required set; surfaces byte-unchanged) | iter-34 evidence; `warmup.py`/`prices.py` untouched |
| J-10 Bounded recovery of two trading days | passing | passing (carried, A.6) | iter-34 evidence |
| J-11 Clean regeneration of derived state | passing | passing (carried, A.6) | iter-34 evidence |
| **J-12 Every frozen disposition is true** | **(new — not in history)** | **passing (NEWLY PASSING)** | reports/qa/goal-market-compass-iter-35-evidence/UT-J-12-result.png + my own re-derivation from `2026-08-12_v8.json` |
| **J-13 Leadership rotation says which way** | **(new — not in history)** | **failing** | measured by me on `2026-08-12_v8.json` + `compass-leadership-rotation-section.tsx:38`; duplication visible in UT-J-12-result.png |

Merged results `reports/phase-goal-market-compass-iter-35-ui-test-results.md`: **9/9 executed PASS, 0
skipped, 0 FAIL, 0 `DEFERRED-BUDGET`.** No `browser-infra.json`, no `journeys-changed.md`, NOT
maintenance isolation. Golden-script hygiene **clean, 4th round running** — all ten pre-existing
goldens carry mtimes predating the 11:15 start; the only new one (`J-12.json`, 12:02) was written
*after* the 12:01 verification, never before it.

### What I re-derived myself rather than accepting

| Claim | My independent result |
|---|---|
| TC-1 pre-fix baseline | 37 of 539 mislabeled in `v7`; top five HPE 92.71, GRMN 89.12, NTAP 87.65, ABNB 87.10, DELL 86.43 — matches the goal text exactly |
| TC-2 post-fix | **0** mislabeled in `v8`; reverse predicate also holds (0 `excluded_by_cap` rows below the floor) in **both** versions |
| TC-3 partition | 502 + 27 + 10 = **539** = `universe.member_count` — the goal file's own predicted numbers |
| TC-10 shadow cohort | 25 rows, **identical ticker set** in v7 and v8 |
| TC-5 / TC-6 | HPE reasons cite only the two genuinely-cleared checks; caution cites threshold 70.0 **and** actual 21.5; checklist tags leadership `gating:true`, entry/risk `gating:false` |
| Spec "Error case" (fails BOTH) | **CRL** (L 86.23 / E 23.62 / R 64.2) is a candidate carrying both cautions — proven on real data |
| AG-12 / AG-17 byte-identity | `v7` export md5 `d905dcfeb788…` = the value captured before the change; mtime 01:12 predates the run; DB row 28 hashes unchanged |
| Database delta | 28 → 29 manifest rows (+1 only); distinct `as_of` still 18, `scanner_runs` still 3128, `data_provider_runs` still 549, `MAX(daily_prices.date)` still 2026-08-12 |

## Anti-goal Check

Scan report `iter-35/scan-report.md`: **CLEAN** (no secret, dependency, or license findings). Product
diff is 5 files: `compass.py`, three backend test files, and `config.yaml`. **Zero frontend files.**

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language gating | OK | I scanned all 4,033 strings in v8's `selection` + `comparison_cohort` against `compass.vocabulary.banned_terms` — **0 hits**. No evidence-ledger surface touched. |
| AG-2 decision-quality only | OK | Same 0-hit scan. New caution text is fact-only ("is below the 70.0 qualifier … advisory only"); no imperative, forecast, or order action. |
| AG-3 displayed numbers correct | OK | The whole point of the fix. Screenshot's HPE card (92.7 / 21.5 / 58.9) matches the served payload I read; UI tally 502/27 matches the API tally. |
| AG-4 no overfit edges | OK | No pattern surfaced as proven; no Evidence Claim introduced. |
| AG-5 determinism / no lookahead | OK | No scoring or bar-window code touched; `MAX(daily_prices.date)` unchanged at 2026-08-12. |
| AG-6 referee gate | OK | No Evidence Claim introduced — gate passes automatically. |
| AG-7 no credentials | OK | Scan CLEAN; my own grep of added lines for key/secret/token/password returned nothing. |
| AG-8 data-shape resilience | OK | No ORM load path touched; `prefill`/`warmup.py`/`prices.py` untouched (binding "Do not redo" respected). |
| AG-9 offline ingest | OK | No network call in added lines; `data_provider_runs` still **549** and the price frontier still 2026-08-12 — no fetch occurred. |
| AG-10 host resource ceiling | OK | `host-guard.env` untouched (mtime 2026-08-19), both HOST-GUARD blocks present, `memory_cap_mb` 8192 / `malloc_arena_max` 2 unchanged — no cap widened. |
| AG-11 no new composite number | OK | Numeric keys across all 10 candidates are exactly `{leadership_score, entry_quality_score, risk_score}` plus checklist threshold/actual echoes. The new `gating` field is a **boolean**. |
| AG-12 manifest immutability | OK | The correction was made the way AG-12 requires — as a **new version row** (v8), never a rewrite. All 28 pre-existing rows survive; `v7`'s export md5 and both its hashes are unchanged; exactly one new export file appeared. |
| AG-13 system-vs-market vocabulary | OK | No readiness token added; the new caution codes are `ENTRY_QUALITY_QUALIFIER` / `RISK_QUALIFIER`. |
| AG-14 no Tapeology coupling | OK | Zero `tapeology` matches in the product diff. |
| AG-15 no outcome-tuned selection | OK | I read the full `config.yaml` diff: **only `rule_version` "v1"→"v2"** plus comments. `leadership_min_score` 80.0, `entry_min_score` 70.0, `risk_max_score` 60.0 appear as unchanged context lines. Which checks GATE changed; no VALUE did. |
| AG-16 cohorts are not controls | OK | Cohort definition text and `caveats.cohort_semantics` untouched; no causal framing added. |
| AG-17 repair never rewrites provenance | OK | Both v7 and v8 carry `prospective_eligible: false`; the DB has **0** rows with `prospective_eligible=1`, same as iter-34. The mislabeled v7 keeps its original values exactly. |
| AG-18 bounded migration preserves all | OK | No schema migration; no DDL change; no schema-file edit. |

**Ledger unchanged: 9 total, 0 unresolved.** No new violation, and I was not unsure about any category.

### Deterministic gates (all run by me)

`results` **exit 0** · `journeys` **exit 1** → `{"total":13,"passing":12,"blocking":["J-13"]}` ·
`regressions` **exit 0** · `coherence --for-achievement` **exit 0** · drift `changed: []`.
The gate names exactly the journey I scored failing, so machine and judgment agree.
Review: **PASS_WITH_NOTES** (2 MINOR). Coherence: **COHERENCE-PASS**.

### Findings no lane made

1. **The reviewer's fixture finding is correct, and I confirmed it in the file.**
   `test_manifest_invariants.py:933` creates the HPE row with risk `58.9` and comments it "fails BOTH
   qualifiers" — but the risk ceiling is `60.0` and lower is safer, so `58.9` **passes** risk. Only
   entry fails. The spec's stated error case is therefore not exercised by any test in this diff. It
   *is* satisfied by real data (CRL), which I verified, so the behaviour is proven — but by luck of
   the dataset, not by design of the suite.
2. **This is the same fixture-confounding mistake that hid the original bug.** The reason the old bug
   was invisible for 34 iterations is that the only qualifier-failing fixture row (CCC, L=77) was
   *also* below the 80 floor, so no test could tell "gated by leadership" from "gated by all three".
   The replacement fixture repeats the shape of that error.
3. **Residual exposure is bounded and now machine-detectable, which no lane quantified.** Three frozen
   export files still carry the 37 mislabeled rows (`2026-08-12` v5, v6, v7) — correctly left alone.
   Every one is stamped `rule_version: "v1"`; the corrected v8 is `"v2"`. So a downstream consumer can
   filter corrected from buggy artifacts, which is precisely what the version bump is for. I confirmed
   the field is present and distinguishing in all eight export files.
4. **The bare `assert` guards no-op under `python -O`** (flagged independently by the reviewer and the
   coherence auditor). I checked the launch path: no `-O` or `PYTHONOPTIMIZE` anywhere in `scripts/` or
   the backend, so the guards are live as actually run. A hardening item, not a live defect.
5. **The new J-12 golden is brittle.** Step 3 clicks the literal string
   `"Audit table — comparison cohort (529) + near-threshold shadow (25)"` and step 1 expects
   `"10 names worth monitoring next session."` — both embed today's counts, so a data-basis move would
   fail the replay on wording rather than on behaviour.

## Next-Step Recommendation

Build **J-13 "Leadership rotation says which way"** — the one remaining job. Today that panel is
broken in three ways I measured myself on the file the system produced this morning:

1. It is a **copy**. The "Leadership rotation" list repeats all 17 rows the "What changed" list
   directly above it already shows — you can see the two identical lists in
   `reports/qa/goal-market-compass-iter-35-evidence/UT-J-12-result.png`.
2. It **never says which way**. A row reads "Home Construction (iShares) 21 → 25" with no word for
   whether that is better or worse; the reader has to know that a smaller rank number is better.
3. It **quietly loses two rows**. For sectors, 5 shown plus 24 held back = 29, but 31 sector and
   industry groups are configured. Two movers are in neither list and are not disclosed anywhere.

Run that round at **full depth**. The reason is concrete, not cautious: J-13 changes the shared piece
of code that produces the "what changed" figures, and four jobs that pass today read those same
figures — J-02, J-05, J-06 and J-07. J-13's own text also requires proving the "What changed" panel
comes out unchanged. That is exactly the situation this project has been burned by before, and it is
the first round in a while with real screen changes for the visual-regression check to look at.

**Two small repairs to carry along, neither worth its own round:** change the test fixture's risk
value above 60.0 so it genuinely fails both qualifiers as its comment claims, and turn the two new
`assert` guards into real errors so they cannot be switched off.

**Still owed, and never a round of their own:** J-04's picture has now been taken 17 times with the
same wrong crop, and seven jobs still owe a labelled walkthrough recording. These are photography
tasks on features that already work.

**One thing worth an owner's eye, not blocking:** the corrected labels are visible today because a
"regenerate" button was pressed during this round. Older frozen files keep the wrong labels forever —
that is deliberate and is what your own rules demand, and each file now carries a version stamp
("v1" wrong, "v2" corrected) so anything reading them can tell which is which. If you would rather the
main page always show freshly corrected figures without pressing that button, say so and it becomes a
small, separate piece of work.

**Next action for you:** approve building J-13 at full depth, or tell the loop to stop here with 12 of
13 jobs passing.
