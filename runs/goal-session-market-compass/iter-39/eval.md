# Iteration 39 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The repair worked. Twenty-one older dates that showed an error box yesterday now show their board
again — I checked the count in the database myself and opened five of those pages as pictures. The
six jobs that broke last round all work again, and this time they were tested on days that already
existed, not on a day created during the test. The one hard rule that was broken last round (adding
new information must never crash an old page) is fixed. Nothing stored was changed: the same 36
saved records, the same fingerprints on the exported files, no record added or deleted. I am not
calling the project finished, for one plain reason: J-15 "What changed accounts for every stock
move" was never built. It is the only job left. I also found one small honesty problem nobody else
noticed, described below.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest on new runs | passing | passing (spot-check, opened) | reports/qa/goal-market-compass-iter-39-evidence/J-01-verify.png |
| J-02 What changed since previous session | regressed | **passing** | reports/qa/goal-market-compass-iter-39-evidence/J-02-verify.png (opened, `?asof=1996-02-01`) + UT-02-result.png |
| J-03 Plain-English summary with cited facts | regressed | **passing** | reports/qa/goal-market-compass-iter-39-evidence/J-03-verify.png + UT-06-result.png (opened, `?asof=2025-04-15`) |
| J-04 Candidate why and why-not | passing | passing (live lane; golden gap) | reports/qa/goal-market-compass-iter-39-evidence/UT-05-result.png + J-04-verify.png (opened) |
| J-05 Close freezes one manifest | passing | passing | reports/qa/goal-market-compass-iter-39-evidence/J-05-verify.png + UT-06-result.png |
| J-06 A frozen manifest never changes | regressed | **passing** | reports/qa/goal-market-compass-iter-39-evidence/J-06-verify.png (opened, `?asof=2025-04-15`, pre-existing manifest) |
| J-07 Today page ten-second read | passing | passing | reports/qa/goal-market-compass-iter-39-evidence/J-07-verify.png + UT-07-result.png |
| J-08 Market page intact, history honest | regressed | **passing** | reports/qa/goal-market-compass-iter-39-evidence/J-08-verify.png + UT-06-result.png |
| J-09 Backend memory fits the host | passing | passing (re-verified; not deferred) | reports/phase-goal-market-compass-iter-39-ui-test-results.md row UT-J-09 |
| J-10 Bounded recovery of two trading days | passing | passing | reports/qa/goal-market-compass-iter-39-evidence/J-10-verify.png |
| J-11 Incident-bounded clean regeneration | regressed | **passing** | reports/qa/goal-market-compass-iter-39-evidence/J-11-verify.png (opened) + UT-02-result.png (opened, "Basis: rebuilt" at 2026-08-11) |
| J-12 Every frozen disposition is true | passing | passing (spot-check, opened) | reports/qa/goal-market-compass-iter-39-evidence/J-12-verify.png |
| J-13 Leadership rotation both directions | regressed | **passing** | reports/qa/goal-market-compass-iter-39-evidence/J-13-verify.png (opened, `?asof=1996-01-02` — the exact date iter-38 captured crashing) |
| J-14 "Not priority" names its real reason | partial | **passing** | reports/qa/goal-market-compass-iter-39-evidence/UT-09-result.png (opened; full 20-entry panel, not cropped) |
| J-15 "What changed" accounts for every crossing | unknown | unknown (never built) | none — explicitly out of scope this iteration |

Deterministic gates, all run by me: `results` **exit 0** · `journeys` **exit 1**,
`{"total":15,"passing":14,"blocking":["J-15"]}` · `regressions pre→post` **exit 0** ·
`coherence --for-achievement` **exit 0** · drift `changed: []`, no `journeys-changed.md`.
Review **PASS** (`issues: []`) · QA **PASS** · Audit **PASS_WITH_GAPS** · Coherence
**COHERENCE-PASS** (zero advisory notes) · Closure **CLOSURE-PASS** · Scan **CLEAN**.
No `browser-infra.json`; this was NOT maintenance isolation; no `DEFERRED-BUDGET` row.

### What I verified myself rather than accepted

- **The root cause, at source.** Read-only sqlite census (`mode=ro`): exactly 2 of 36 stored
  `selection_json` rows carry `why_not_totals` (2026-08-12 v10 = 27/25, 2005-04-15 v1); the other
  **21 distinct as-of dates lack it** — precisely the crashing set. Pre-iter-38 `why_not` entries
  carry only `{ticker, failed_conditions}`, so widening `reason`/`cap_rank`/`cap` was genuinely
  required too.
- **The degraded string, byte-for-byte.** I opened `UT-02-result.png` (`?asof=2026-08-11`) and read
  `Not priority (20 shown — held-back counts unavailable for this manifest version)` with all 20
  per-entry advisory distances rendering below it and **no** "ranked #N … cap" lead-in anywhere
  (TC-1 and TC-2, confirmed visually).
- **The golden restoration.** `git diff ab3cca63 -- J-04/J-05/J-06/J-07.json` → **zero
  differences**. I read the four scripts: J-05/J-06 point at `2025-04-15` (a genuinely pre-existing
  manifest, not iter-38's same-day-minted `2005-04-15`) and carry back the deleted
  `available_at_utc` assertion `2026-08-20T11:41:00.381102+00:00`; J-07 is back to its full 7 steps
  with the market-link click and all three direction-word assertions. Three of the four re-pass
  replay.
- **J-14's numbers.** Re-derived from stored row id 35: `why_not_totals` 27/25 (= the header's "52
  held back"); DXCM `cap_rank 11, cap 10, entry_min_score 26.53 vs 70.0 d 43.47, gating false`;
  EXPE `leadership_min_score 79.81 vs 80.0 d 0.19, gating true`; BKNG d 1.60. Every value on screen
  matches (AG-3).
- **Nothing frozen moved.** 36 manifest rows / 23 distinct as-of dates (identical to the
  post-iter-38 state), `sum(prospective_eligible) = 0`, `max(created_at) = 2026-09-01 18:17`, before
  this iteration began. Export v7 md5 `d905dcfeb7883d86602d64d4c24682ad` — the same value iters
  35/36/37/38 recorded, now a fifth round. Every export mtime predates this run; `git status` on the
  exports directory is empty.
- **Both stable spot-checks agree with their recorded status** (J-01 GRMN 89.12 with "Not yet
  proven" chips; J-12 cohort 529/25, DXCM 85.0/26.5/57.6 "excluded by cap"), so I did not widen.

### A finding no lane made

`apps/frontend/lib/api.ts:1051` still declares `WhyNotFailedCondition.gating` as **required**, but
`gating` was added by the same iter-38 change and is **absent on every pre-iter-38 stored row** — my
read-only census of all 787 stored failed conditions found exactly two keysets, with and without
`gating`. `compass-focus-section.tsx:151` renders `{failed.gating ? "" : " — advisory"}`, so on
those older manifests every failed condition is labelled "— advisory", including **26 stored
`leadership_min_score` misses** across three as-of dates (2001-04-17: 11, 2005-04-01: 5,
2020-01-02: 10) — and the leadership floor is the *sole candidacy gate*, never advisory. The
auditor's own consumer grep (finding F1) covered `why_not_totals`/`reason`/`cap_rank`/`cap` but not
this nested field.

It is **not** a crash (a truthiness read on an absent property is safe, and all 787 conditions carry
`condition`/`threshold`/`actual`/`distance`, so no `.toFixed()` can throw) and **not** a wrong
number. It was introduced by iter-38 and became *visible* only because iter-39 stopped those pages
crashing — none of the three dates is a journey assertion target. I therefore score it a **minor**
AG-8 violation (the re-validation clause), not critical, and say so explicitly rather than letting a
silent judgment carry it.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 No unproven "edge" language | OK | J-01-verify.png (opened) shows GRMN's three scores each carrying a "Not yet proven" chip. No new score, no ledger change. |
| AG-2 Decision-quality only | OK | Diff adds one display string ("held-back counts unavailable for this manifest version"). No target, promise, or imperative verb; grep for forecast wording on the two new files returned nothing. |
| AG-3 Displayed numbers correct | OK (one label caveat) | Every number on UT-09/UT-02/J-12 re-derived by me against stored rows and matching. Caveat: the "— advisory" *word* is wrong on 26 old-manifest rows (see the finding above); numbers themselves are correct. |
| AG-4 No overfit edges | OK | No pattern surfaced as proven; no referee-bearing claim introduced. |
| AG-5 Determinism / no lookahead | OK | Zero backend change (`git diff 69e86ef2 -- apps/backend` empty); no scoring path touched. |
| AG-6 Referee gate on evidence claims | OK | This iteration introduces no Evidence Claim. |
| AG-7 No hard-coded credentials | OK | `scan-report.md` CLEAN; I additionally grepped the two new files for key/secret/token/password/bearer — none. No config or env file in the diff. |
| AG-8 Resilience to data-shape change | **RESOLVED (iter-38 critical) + one NEW minor** | The iter-38 critical violation is closed: 21/21 dates HTTP 200 and 21/21 DOM checks with no error card (UT-08); I opened five of those pages myself. New **minor**: `gating` still declared required and mislabels 26 gating misses as "advisory" — see the finding above. |
| AG-9 Offline-deterministic ingest | OK | No dependency manifest touched at all (`git diff` on package.json / lock / requirements / pyproject empty). `daily_prices` frontier still 2026-08-12 — no dataset advancement. |
| AG-10 Host resource ceiling | OK | `config.yaml` diff **empty**; `host-guard.env` untouched (mtime 2026-08-19). `memory_cap_mb` 8192, `malloc_arena_max` 2, `cache_size` -65536 all unchanged. |
| AG-11 No new composite number | OK | I extracted every new numeric literal from the product diff: **none**. No "fit"/"conviction"/"blended"/"probability" wording in the new files. |
| AG-12 Manifest immutability | OK | 36 rows / 23 as-of dates unchanged; `max(created_at)` predates this run; all 10 export md5s stable, v7 = `d905dcfeb788…` for a fifth round; exports `git status` empty. Structurally guaranteed too — the diff has no backend and no DB write path. |
| AG-13 System vs market vocabulary | OK | No readiness token in the changed render code; the new string names only held-back counts. |
| AG-14 No Tapeology coupling | OK | Grepped all four touched/new frontend files: zero hits. |
| AG-15 No outcome-tuned selection | OK | `config.yaml` diff **empty** — `leadership_min_score` 80.0, `entry_min_score` 70.0, `risk_max_score` 60.0, `max_candidates` 10, `why_not_cap` 20, `why_not_cap_per_reason` 10 all unmoved. |
| AG-16 Cohorts are not controls | OK | J-12-verify.png (opened): the shadow cohort renders only inside the "research-only substrate" audit table, never in the focus section, and is never an ordering input. |
| AG-17 Repair never rewrites provenance | OK | `sum(prospective_eligible) = 0` across all 36 rows; UT-02's version list reads v1/v2/v3 each "retrospective  not eligible"; no version minted by viewing (row count unchanged). |
| AG-18 Migration preserves everything | OK | No schema change, no migration, no ORM/DDL work in the diff. |

**Ledger after this iteration: 11 total, 1 unresolved (the new minor AG-8).** The iter-38 critical
AG-8 entry is marked resolved with the evidence above.

### Two declared process gaps (neither blocks, both need a named owner action)

1. **J-04's restored golden does not re-pass replay**, so the spec's DoD item "restored goldens
   re-pass with no reconciliation-footer override" is unmet for one of four. The cause is benign and
   I traced it end-to-end: step 2 clicks the literal text `Not priority (20)`, which was the summary
   string at `ab3cca63`; this iteration deliberately changed that string, so the click target no
   longer resolves. I opened `J-04-verify.png` and the page at `?asof=2026-07-23` renders in full —
   this is a stale click target, not a page failure. **The auditor was right to refuse to edit it
   here** (the spec ordered it byte-exact), and right to replace the "false positive" footer with
   the true cause. This is the second consecutive round in which that boilerplate footer converted
   replay FAILs into merged PASSes; last round it hid a real crash, this round it hid nothing, but
   the pattern needs the owner's decision.
2. **J-14's golden has never passed replay and cannot as written** — its step 3 re-navigates and
   then asserts text that lives inside a collapsed `<details>`. I read
   `apps/frontend/components/ui/disclosure.tsx` myself: there is no `open` attribute, so the
   assertion correctly finds nothing. The product is fine (I read the exact string out of
   `UT-09-result.png`). It needs a click-then-assert repair, declared in advance.

Also noted, non-blocking: the UX-regression reviewer was shed again by the **declared** wall-clock
trim (`UX-REGRESSION-SKIPPED`, SPEED-15 rung 3b). Unlike iter-37 this round *did* change a
user-facing string, so I did not wave it through on the "no screen changed" ground — instead the
changed screen was inspected four other ways and I read the new string out of a screenshot myself.
And `UT-10-result.png` is a **1-colour blank image**; UT-10 is a P2 UX check whose assertions were
DOM-based (`querySelectorAll('summary')`, unchanged `window.location.href`), so nothing rests on the
picture, but the iter-36 blank-capture failure mode reappeared on one artifact and should not be
ignored.

## Next-Step Recommendation

Run one more full round and build **J-15 "What changed accounts for every stock move"** — it is the
only job never built, and the only thing standing between this project and finished. Nothing else
needs new features.

Carry these as passengers of that round, none of them a round of their own:

1. **Fix the wrong word on old pages.** On three older dates (17 Apr 2001, 1 Apr 2005, 2 Jan 2020)
   the page says a name missed the *main* entry bar "advisory", which is untrue — that bar is the
   only real gate. One line: make the `gating` field optional like the others, and when a saved
   record does not record it, say so honestly instead of guessing "advisory".
2. **Repair two check scripts, in the open.** J-04's script should click the new wording; J-14's
   should open the "Not priority" panel before looking inside it. Say what you are changing and why
   *before* running them — never edit a script after it fails, and never point one at a day created
   the same day.
3. **Take the three missing walkthrough photographs** — J-05 "Freeze one manifest", J-06 "A frozen
   manifest never changes", J-12 "Every frozen disposition is true" — and re-take J-14's, which this
   round captured from the top of the page instead of the list it was supposed to show. Also mark
   the walkthrough's new step as new.
4. **Ask the browser step to scroll before it photographs.** One picture this round (`UT-10`) came
   out completely blank, and several others stop above the thing they are meant to prove.

**Three carried housekeeping items, none urgent and none blocking:** one pre-existing failing test on
three files this project has not touched in weeks (fix it or formally waive it); the 7.8 GB throwaway
copy from round 23 can be deleted; and `apps/frontend/.next-verify/` is still stored in version
control — 61 of this round's 65 changed files are that build folder. Adding it to the ignore list
would make every future review readable.

**One mechanical item:** the whole round is uncommitted at scoring time. Please confirm it lands.
