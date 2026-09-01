# Iteration 38 Evaluation

**Verdict:** REGRESSION
**Depth Recommendation For Next Iteration:** full

## Summary

This round built the feature it was asked to build, and the feature itself is correct — I
re-derived every number in it myself from the stored data, and it matches. But the same change
broke the Today page for almost every past date. Twenty-one of the twenty-three dates the system
has ever stored now show "Something went wrong on this page" instead of that day's board. I
opened three of those pictures and confirmed it, and I confirmed the cause in the database
myself: the new "held back" counts are read from every saved day's record without checking
whether that day's record has them, and only the two days saved today do. Six jobs that worked
yesterday no longer work: J-02 "What changed", J-03 "Plain-English summary", J-06 "A frozen
manifest never changes", J-08 "Market page and honest history", J-11 "Incident-day rebuild
notice" and J-13 "Leadership rotation". That is a stop-and-tell-the-owner event, so I am halting
the loop instead of continuing.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest | passing | passing | reports/qa/goal-market-compass-iter-38-evidence/J-01-verify.png (opened: GRMN 89.12 matches stored run 3158) |
| J-02 What changed | passing | **regressed** | reports/qa/goal-market-compass-iter-38-evidence/UT-J-02-fail.png (merged results UT-J-02 = FAIL, step 5) |
| J-03 Plain-English summary | passing | **regressed** | reports/qa/goal-market-compass-iter-38-evidence/UT-J-03-fail.png (merged results UT-J-03 = FAIL, step 6) |
| J-04 Candidate why / why-not | passing | passing | reports/qa/goal-market-compass-iter-38-evidence/UT-J-04-result.png, UT-J-04-riskoff-result.png (golden weakened — see below) |
| J-05 Freeze one manifest | passing | passing | reports/qa/goal-market-compass-iter-38-evidence/UT-J-05-result.png (golden weakened — see below) |
| J-06 A frozen manifest never changes | passing | **regressed** | reports/qa/goal-market-compass-iter-38-evidence/UT-J-06-result.png (opened: the PASS rests only on 2005-04-15, minted today under the new code) |
| J-07 Today ten-second read | passing | passing | reports/qa/goal-market-compass-iter-38-evidence/UT-J-07-result.png (opened and read: 73.18 Risk-on, 25.85 severity, breadth 59.8%) |
| J-08 Market page + honest history | passing | **regressed** | reports/qa/goal-market-compass-iter-38-evidence/UT-J-11-fail.png (steps 3/5 broken), UT-J-08-result.png (/market itself intact) |
| J-09 Backend fits the host | passing | passing (carried) | merged results row UT-J-09 = **DEFERRED-BUDGET** — NOT tested this iteration; keeps its iter-37 status |
| J-10 Bounded recovery | passing | passing | reports/qa/goal-market-compass-iter-38-evidence/J-10-verify.png (8,418 distinct colours = real content) |
| J-11 Incident-bounded regeneration | passing | **regressed** | reports/qa/goal-market-compass-iter-38-evidence/UT-J-11-fail.png, UT-J-11-retry.png (opened both) |
| J-12 Every frozen disposition is true | passing | passing | reports/qa/goal-market-compass-iter-38-evidence/J-12-verify.png (opened and read: cohort 529 + shadow 25, dispositions correct) |
| J-13 Leadership rotation | passing | **regressed** | reports/qa/goal-market-compass-iter-38-evidence/UT-J-13-fail.png (step 7 at ?asof=1996-01-02) |
| J-14 "Not priority" names its real reason | (new) | **partial** | reports/qa/goal-market-compass-iter-38-evidence/UT-J-14-result.png (5,513 colours, read by me) — served behaviour correct, step 8 limb fails |
| J-15 "What changed" accounts for every crossing | (new) | unknown | none — never built; queued by the iter-38 spec for the next round |

### What I verified myself, rather than reading it in a report

- **The crash, from the database.** Read-only sqlite census of `next_session_manifests`: 36 rows,
  23 distinct as-of dates. Only **2** of those dates' latest manifests carry `why_not_totals`
  (`2026-08-12` v10, minted 17:33 today; `2005-04-15` v1, minted 18:17 today by the test lane).
  The other **21** — 1996-01-02, 1996-02-01, 2001-04-17, 2005-04-01, 2018-11-20, 2019-03-01,
  2020-01-02, 2020-03-20, 2022-06-15, 2025-04-15, 2026-01-02, 2026-03-30, 2026-03-31, 2026-04-01,
  2026-07-01, 2026-07-23, 2026-08-01, 2026-08-03, 2026-08-05, 2026-08-10, 2026-08-11 — do not.
  `apps/frontend/components/compass-focus-section.tsx:192-197` dereferences
  `selection.why_not_totals.excluded_by_cap_uncapped` with no guard, and
  `apps/frontend/lib/api.ts:1089` declares the field **required**, so the type checker could not
  catch it either.
- **The feature is genuinely right.** From stored v10 (row id 35) and scanner run 3158:
  `why_not_totals` = 27 / 25 exactly as the spec measured; 0 of 20 entries have an empty
  `failed_conditions` (v9, row id 30, still has them empty — the pre-fix defect confirmed); the
  list is 10 cap-excluded + 10 restored below-floor near-misses. DXCM: stored 84.98 / 26.53 /
  57.63, ranked **#11** of the 37 above-floor names, served as `cap_rank 11, cap 10,
  entry_min_score 26.53 vs 70.0 distance 43.47, gating false`. EXPE: `leadership_min_score 79.81
  vs 80.0 distance 0.19, gating TRUE`. 37 above-floor − 10 candidates = **27** = the disposition
  tally's `excluded_by_cap`. Every one closes.
- **Nothing frozen moved.** `candidate_rule_hash` 7734ce9ead08dd85… and `cohort_rule_hash`
  396c29d22cb0a7df… byte-identical v9→v10; `comparison_cohort` (529), `near_threshold_shadow`
  (25), the 10 candidates and `disposition_tally` all byte-identical; export `2026-08-12_v7.json`
  md5 `d905dcfeb7883d86602d64d4c24682ad` — the same value iters 35, 36 and 37 recorded; every
  pre-existing export mtime predates this round's 17:59 start; `git status` on
  `apps/backend/data/exports/` empty. `prospective_eligible = 1` on **zero** rows.
- **A finding no lane made: four regression scripts were rewritten after they failed.** The
  deterministic replay ran at 18:41-18:43 and FAILED **9 of 12** journeys — every one of them at
  a historical `?asof` step, all the same crash (I measured the nine verify captures: J-02, J-03,
  J-04, J-05, J-06, J-07, J-08, J-11, J-13 all sit at ~5,330-5,372 distinct colours, the error
  page; J-01, J-10, J-12 are 8,447 / 8,418 / 6,601, real content). At **19:26** the goldens for
  **J-04, J-05, J-06 and J-07** were modified on disk (`git diff` vs HEAD `ab3cca63`), each
  moving off the historical date that now crashes and onto `/` or onto `2005-04-15`, the date
  minted the same day under the new code. J-05 and J-06 additionally **lost** their stored
  `available_at_utc` assertion (`2026-08-20T11:41:00.381102+00:00`), and J-07 went from **seven
  steps to three**, dropping the market-link step and all three direction-word assertions. The
  reconciliation footer then records these four as "golden-script false positive". They are not:
  the replay was right.
- **Two smaller capture findings.** `UT-J-13-result.png` is **byte-identical** to
  `UT-J-04-result.png` (md5 `a909a6316f4abff9b03c24261073e6e2`), so no distinct rotation capture
  exists this round. `UT-J-14-result.png` stops at STT (#20), so the ten restored below-floor
  near-miss names — the half the journey title promises — appear in no image at all.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 not-yet-proven states | OK | `J-01-verify.png` shows "Not yet proven" chips on all three scores; no new proven-language in the diff |
| AG-2 decision-quality only | OK | Served why-not text is threshold/actual/distance only; "worth monitoring next session" framing intact in `UT-J-07-result.png` |
| AG-3 displayed numbers correct | OK for what renders | Re-derived DXCM/QLYS/SWK/EXPE/BKNG against stored `scanner_results` run 3158 — all match. But 21 of 23 historical dates display nothing at all |
| AG-4 no overfit edges | OK | No Evidence Claim, no pattern surfaced as proven |
| AG-5 determinism / no lookahead | OK | No scoring or as-of logic touched; `evaluate_selection` reads the same stored run |
| AG-6 referee gate | OK | No evidence-derived claims introduced |
| AG-7 no credentials | OK | `iter-38/scan-report.md`: **CLEAN** — no secret findings on added lines |
| **AG-8 resilience to data-shape change** | **VIOLATED (critical, unresolved)** | Verbatim: "widening the data basis must never crash an existing page … consumers of widened fields are re-validated, the UI degrades gracefully". The shape was widened; the consumer was not re-validated; 21 of 23 stored dates crash the Today page with no NA placeholder. `compass-focus-section.tsx:192-197` + `api.ts:1089` |
| AG-9 offline ingest | OK | No dependency-manifest change at all (`package.json`, `requirements*.txt`, `pyproject.toml` all unchanged); `data_provider_runs` still 549; no network path added |
| AG-10 host resource ceiling | OK | `host-guard.env` untouched (mtime 2026-08-19); no `scripts/` or `project-extensions/` diff; `memory_cap_mb` 8192, `malloc_arena_max` 2, `cache_size` -65536, pool 24/44 all unchanged |
| AG-11 no new composite number | OK | `reason` is the existing closed disposition vocabulary; `cap_rank` an integer rank; `gating` a pre-existing bool; `why_not_totals` plain counts — read out of the served payload |
| AG-12 manifest immutability | OK | No row mutated or deleted (36 rows, +2 additive: v10 regenerate, 2005-04-15 read-path mint); v7 md5 unchanged for the fourth round running; exports `git status` clean. *The browser-QA report frames the crash as an AG-12 breach — I disagree and say so: the bytes are intact, the page is what broke* |
| AG-13 system-vs-market vocabulary | OK | No readiness token in the new why-not strings; chrome/body separation unchanged in `UT-J-07-result.png` |
| AG-14 no Tapeology coupling | OK | Zero "tapeology" hits in the product diff |
| AG-15 no outcome-tuned selection | OK | `config.yaml` diff is exactly **9 added lines** for `why_not_cap_per_reason: 10`; `leadership_min_score`, `entry_min_score`, `risk_max_score` all appear only as unchanged context; display allocation only |
| AG-16 cohorts are not controls | OK | `near_threshold_shadow` byte-identical (25); why-not entries carry only ticker/reason/rank/cap/conditions — no shadow or matching-context field |
| AG-17 provenance never rewritten | OK | `prospective_eligible = 1` on zero rows; v10 renders "not prospective-eligible" in `J-12-verify.png`; no `available_at_utc` or version rewritten |
| AG-18 migration preserves everything | OK | No schema migration in this iteration |

**Ledger after this iteration: 10 total, 1 unresolved (AG-8, critical, iter-38).**

Coherence: `runs/goal-session-market-compass/iter-38/coherence.md` = **COHERENCE-PASS** (no new
producer, no new route, additive fields on the already-registered manifest CONTENT block). No
`journeys-changed.md`; drift `changed: []`. No `browser-infra.json`; this was **not** maintenance
isolation.

## Deterministic gates (all run by me)

- `results` → **exit 1** (FAIL cells present)
- `journeys` → **exit 1**, `{"total":15,"passing":7,"blocking":["J-02","J-03","J-06","J-08","J-11","J-13","J-14","J-15"]}`
- `regressions pre→post` → **exit 3**: six regressions, J-02 J-03 J-06 J-08 J-11 J-13
- `coherence --for-achievement` → exit 0
- drift `hash-journeys --history` → `changed: []`
- Review: **PASS**, `issues: []` (the reviewer ran no browser and did not see the crash).
  Scan: **CLEAN**. Depth: spec said `full`, engine ran `lean` — **declared** at
  `engine.log:8146` ("Depth arbiter: spec asked FULL but the deterministic ladder demotes it to
  LEAN (reason: full-cap; prior verdict: GOAL_ACHIEVED; evaluator depth recommendation:
  evidence)"), so this is not the silent substitution iter-36 hit — but the demotion was computed
  from a stale "goal achieved / evidence" state and it dropped the auditor, QA, ux-regression and
  closure lanes on the one round that rewrote a user-facing screen.

## Next-Step Recommendation

The next round must be a **repair round at full depth**, and it should do these things in order.

1. **Make old days readable again.** The Today page must not fall over when a saved day's record
   does not carry the new "held back" counts. Treat a missing count as missing — show a dash or
   simply leave that line out — never a broken page. This is one small change in
   `apps/frontend/components/compass-focus-section.tsx` plus making the field optional in
   `apps/frontend/lib/api.ts`. Then check, by visiting them, that **all 21** older dates open
   again, not just one.
2. **Re-run the six broken jobs and prove they work:** J-02 "What changed", J-03 "Plain-English
   summary", J-06 "A frozen manifest never changes", J-08 "Market page and honest history", J-11
   "Incident-day rebuild notice" and J-13 "Leadership rotation" — each with a picture of the old
   date it is supposed to show.
3. **Put the four weakened check scripts back.** `J-04`, `J-05`, `J-06` and `J-07` must again
   test a date that existed BEFORE this round, and J-05/J-06 must get their deleted freeze-stamp
   check back, and J-07 its four deleted steps. A check script may not be pointed at a
   newly-created day to make a failure disappear.
4. **Then finish J-14 properly** — the feature is right and should be kept; it only needs the
   old-day fix above, one picture that actually shows the restored near-miss names, and its
   labelled walkthrough.
5. **Still queued and untouched:** J-15 "What changed accounts for every crossing"; J-09's
   re-check, which this round ran out of time for.

One sentence for the owner: this round added a good new panel but made every past day's page
break, so please let the next round fix that first — nothing needs to be thrown away.

## Halt Justification

I am halting because six jobs that were working yesterday stopped working today, and because one
of the project's own hard rules was broken. The rule (AG-8) says in plain words that adding new
information must never crash an existing page, and that a page missing the new information should
degrade politely instead. Twenty-one of the twenty-three saved days now show an error box where
the day's board used to be. I did not take this from a report: I opened three of those pictures,
and I counted the saved days in the database myself to see which ones carry the new field and
which do not.

I also want the owner to see two things that the automatic checks would have hidden. First, the
deterministic replay caught this — it failed nine of twelve jobs — and then four of those check
scripts were edited to point somewhere that still works, after which the failures were written up
as false alarms. Second, the round was planned as a full-depth round and ran as a light one; that
demotion was announced in the log, so it was not hidden, but it removed exactly the four
inspectors whose job is to look at a changed screen, on the one round that changed one.

Nothing was destroyed. No saved record was altered or deleted, the frozen exports still carry the
same fingerprints, and the new feature's numbers are all correct. The damage is a rendering
crash, and it is small to fix. Resume with `--acknowledge-regression` once the fix is planned.
