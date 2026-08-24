# Iteration 13 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

**J-11 STAGE C COMPLETE: YES**
**J-11 STAGE D AUTHORIZED: NO**

## Summary

The owner said "go" for the one destructive step, and it was done exactly as written. Eleven damaged
days now hold no calculated results at all, ready to be rebuilt later. I did not take that from the
reports: I opened the database in read-only mode and re-counted everything myself against the saved
picture from the last run. Nothing outside the eleven days moved. The prices, the saved briefings, the
watchlist and the audit records are all untouched. I am halting because the owner's own written rule
says the engine must stop here so the owner can inspect the result, and the next step needs a fresh
"go" that only the owner can give.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels are honest | passing | passing (carried, not tested — maintenance isolation) | `reports/phase-goal-market-compass-iter-13-ui-test-results.md` (all-SKIPPED, reason: maintenance isolation) |
| J-02 What changed since last session | partial | partial (carried, not tested) | same all-SKIPPED results file |
| J-03 Plain-English summary | partial | partial (carried, not tested) | same all-SKIPPED results file |
| J-04 Candidate why and why-not | passing | passing (carried, not tested) | same all-SKIPPED results file |
| J-05 Each close freezes one manifest | partial | partial (carried, not tested) | same all-SKIPPED results file |
| J-06 A frozen manifest never changes | partial | partial (carried, not tested) | same all-SKIPPED results file |
| J-07 The Today page ten-second read | failing | failing (carried, not tested) | same all-SKIPPED results file |
| J-08 Market page moves over intact | failing | failing (carried, not tested) | same all-SKIPPED results file |
| J-09 The backend fits the host | partial | partial (carried, not tested) | same all-SKIPPED results file |
| J-10 Bounded recovery of two deleted days | passing | **passing — re-derived read-only by me** | 585 symbols on each of 2026-08-11/12; `daily_prices` 3,310,374 with a fingerprint byte-identical to `runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-after.json` (committed @ 78df5309); frontier still 2026-08-12; `data_provider_runs` 549, identical id-set |
| J-11 Incident-bounded clean regeneration | partial | **partial — Stage C now COMPLETE; D-G not started** | `runs/goal-market-compass-iter-13/j11-stage-c-preflight.json`, `-preflight-comparison-gate.json`, `-intended-delete-set.json`, `-mutation-accounting.json`, `-complete.json`, `-db-file-true-start.json` / `-true-end.json`, `-run.log` — every figure below re-derived by me read-only, not read out of those files |

**No journey regressed. No journey newly failed. No journey was promoted** — an isolated iteration
produces no browser evidence, so none could be.

### What I re-derived myself, read-only, on the live 8.4 GB database

1. **All 11 damaged days now hold nothing derived** — zero scanner runs and zero child rows on every
   one of 2026-05-12, 05-13, 07-10, 07-13, 07-24, 07-27, 08-03, 08-05, 08-10, 08-11, 08-12.
2. **Exactly five tables moved, by exactly the declared amounts**, against iteration 12's committed
   baseline: `scanner_runs` 3,121→3,117 (−4: ids 3114/3148/3149/3150, all confirmed gone),
   `forward_returns` 6,800,539→6,797,728 (−2,811), `scanner_results` 1,327,944→1,325,785 (−2,159),
   `sector_scores` 96,751→96,627 (−124), `theme_scores` 34,331→34,287 (−44). The other **19 of 24
   tables are identical**; no table was added or dropped.
3. **Zero orphans** in all four child tables. **Zero leftovers**: no row anywhere still points at a
   deleted run.
4. **Prices untouched**: `daily_prices` 3,310,374 with a byte-identical fingerprint.
5. **Saved briefings untouched**: 24 rows × 28 columns value-identical to the certified baseline (I
   recomputed the comparison myself); table definition sha256 `9f653c81…c501ee` byte-identical with no
   foreign key; the three original indexes; `prospective_eligible` false on all 24; ids contiguous
   1–24; per-date counts unchanged at 08-05:2, 08-10:1, 08-11:3, 08-12:6; and **none created for the
   seven dates that had none**.
6. **User state and audit records untouched**: watchlist 6, `data_provider_runs` 549 with an identical
   id-set, certified-claims ledger sha256 `5d435cff…` unchanged.
7. **The forward-return boundary held**: the 16,614 rows measured into a damaged day but owned by a
   surviving run all remain; only 719 rows on four dates moved, and those 719 are a subset of the
   2,811 run-owned rows removed.
8. **Deletion-only and offline**: no INSERT, UPDATE or `session.add` in the new code, and no network
   library imported anywhere in it; the whole-history clear function is never called by it.
9. **The write boundary is honest**: the file's timestamp at the true process start equals iteration
   12's own recorded "after" timestamp exactly, the end timestamp reflects the one authorized write,
   and the file still carries that exact timestamp and size (8,365,871,104) right now — so nothing has
   written since, and every later check was genuinely read-only. The write-ahead log is 0 bytes.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language | OK | No serving or narrative code changed; nothing new is displayed. Confirmed by the diff file list. |
| AG-2 decision-quality only | OK | No candidate, reason, caution or config string in the diff. |
| AG-3 displayed numbers correct | OK | No display path changed. The 11 days now hit the existing missing-run path — an authorized mid-repair state (C4/C7/C10), not a wrong number. |
| AG-4 / AG-6 evidence claims | OK | None introduced; ledger file hash `5d435cff…` unchanged. |
| AG-5 no-lookahead | OK | Deletion-only; `daily_prices` fingerprint identical either side. |
| AG-7 secrets | OK | `iter-13/scan-report.md` = CLEAN, no secret/dependency/license finding on added lines. |
| AG-8 data-shape resilience | OK | No widened basis; the new function selects one run row per date and deletes by `run_id` — no whole-table load. |
| AG-9 offline ingest | OK | `data_provider_runs` 549 with identical id-set (every real fetch appends a row); I grepped the new module and script — no `requests`/`urllib`/`httpx`/`yfinance`/`socket` import. |
| AG-10 host resource ceiling | OK | No launch script touched; the 8.4 GB file was never copied; one pytest process only. |
| AG-11 no new composite number | OK | Nothing computed at all this iteration. |
| AG-12 manifest immutability | OK | 24 × 28 values identical to the certified baseline — verified by me, not quoted. |
| AG-13 system-vs-market vocabulary | OK | No surface or vocabulary file in the diff. |
| AG-14 no Tapeology coupling | OK | No such import anywhere in the diff. |
| AG-15 / AG-16 selection + cohorts | OK | No threshold, rule or cohort text changed. |
| AG-17 provenance never rewritten | OK | Manifests unchanged, `prospective_eligible` false on all 24; iteration 11's REGRESSION verdict untouched; the auditor's correction to `assumptions.md` is additive (56 insertions, 0 deletions). |
| AG-18 migration preserves everything | OK | Table definition and all three indexes byte-identical to the certified state; no further schema drift; the migration tool was not run. |

**No new violation. Ledger unchanged at 5 entries, 0 unresolved.**

Two honesty problems were found inside the run and both were fixed there, so neither is an open
violation — but both belong in the record because the independent auditor found them while the
developer, the reviewer and the quality check all reported the opposite:

- **The frozen "engine identity" has drifted since it was certified.** Iteration 10 froze
  `6261ca17…`; this run re-derived `53d2ffd1…`. I recomputed it independently and got `53d2ffd1…`,
  so the drift is real. The cause is that `compass.py` is one of the three files the identity is
  built from, and it was edited in commits `a7380009` and `a9e651c4`; the configuration half is
  unchanged. This changes nothing about the deletion, which reads no identity — but it is a real
  trap for the next stage.
- **A written assumption said a group of forward-return rows was "already absent". It is not** — I
  counted 16,614 of them surviving on retained runs. The decision built on that wrong belief was
  nevertheless the correct one, and the code does the right thing.

## Coherence

`runs/goal-session-market-compass/iter-13/coherence.md` = **COHERENCE-PASS**. No structural veto.

## Next-Step Recommendation

**One instruction is needed from the owner, and nothing may proceed without it.** The owner's own rule
(C10) says a successful Stage C is not permission for Stage D, and that the owner inspects the deletion
record first. Pick one:

- **(a) Give the fresh instruction to start Stage D** — rebuild the eleven days through the normal
  production path. Before that starts, three things must be settled, and none of them is work the
  developer should decide alone: **first**, say in writing which frozen identity the rebuilt days are
  checked against, and confirm that the 34 surviving days already stamped with the older value are left
  alone; **second**, close the blind spot in the safety check that captures the identity but never
  compares it — that is exactly why the drift went unnoticed, and the next stage's whole correctness
  claim rests on that comparison; **third**, close the missing safety tests (nine of the eleven gate
  checks have no failure test, and the "refuse without the confirm flag" path has none at all), because
  the next stage reuses that same skeleton.
- **(b) Order a small hardening run first** that does only those second and third items, with no
  rebuild — safe, non-destructive, and it makes the next destructive stage stronger.
- **(c) Change the plan** in `docs/goal.md`.

**Three facts to carry into whichever is chosen.** The application's "Latest" day has moved back about
three weeks: the newest stored day is now 2026-07-23, because the four newest days were among the
eleven cleared. That is expected and authorized, and it reverses when the rebuild runs. The stored
caches still hold their old answers, but their keys no longer match today's data, so they are currently
ignored rather than wrongly served — the danger returns during the rebuild, when the key could land
back on an old value byte-for-byte, which is precisely the trap the goal file names. And AVB's restored
prices sit on the stored scale while its trading volume does not, so any figure multiplying price by
volume reads about 2.79 times too high on 11 and 12 August — check what that does to its ranking once
the days are rebuilt.

**Also pending and purely mechanical:** nothing from this iteration is saved into version control yet,
so no version number can be quoted for that checklist item. **Five older owner questions remain open
and none of them blocks anything:** whether 3.44 GB is acceptable for J-09 "The backend fits the host";
J-06's "underlying run unavailable" wording; the rewording of J-01's first two test steps; whether an
empty "next-session focus" is acceptable; and whether MNST joins the recovery list. **One standing
framework note:** the defect that once let a forbidden test lane run is still unfixed in
`scripts/automation/`; five iterations running have avoided it with the maintenance-isolation contract
rather than curing it.

**In one sentence:** the dangerous step is done and verified clean, and the owner should now look at the
deletion record and either say "start the rebuild" or ask for the small safety-hardening run first.

## Halt Justification

Nothing is wrong and nothing is missing. The iteration did exactly what it was told to do, and I
checked it myself against the live database rather than trusting the reports. I am halting because
every way forward belongs to the owner, not to the engine:

1. The owner's written rule ends this stage with "STOP THE ENGINE" and requires a separate, fresh
   instruction before the next stage — the same way this stage waited for one.
2. There is no other work available. The goal file shuts every other product, research and browser lane
   until the final stage of this repair passes, so a "keep going" verdict would only let the engine plan
   the rebuild — the one thing the owner has explicitly not authorized.
3. The next step writes to the same canonical 8.4 GB database whose damage this whole repair exists to
   fix. Halting to ask is the safe direction.

Why not REGRESSION: nothing that worked stopped working, no stored value outside the authorized set
moved, and no critical rule was broken. Why not CONTINUE: see point 2 — continuing would start the
unauthorized stage. Why not ESCALATE: this run already used the careful full depth, and the careful
depth is exactly what caught the identity drift. Why not GOAL_ACHIEVED: eight journeys are still
unfinished, the repair has four stages left, and this iteration produced no browser evidence at all.
