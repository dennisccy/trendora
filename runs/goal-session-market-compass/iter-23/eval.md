# Iteration 23 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

**Owner-facing lines (owner ruling item 8):**
`J-11 SERVING/REPLAY VERIFICATION: PASS` · `J-11 STATUS: PASSING` · J-11 incident **CLOSED**.
Countervailing line, new this iteration: `CANONICAL DATABASE WAS BOOTED AND WRITTEN TO` — contrary to
the same ruling's item 3.

## Summary

The one job the owner asked for is done, and it worked. The repaired data was copied to a throw-away
copy of the database, the real app was started against that copy, and the pages served the repaired days
correctly — I opened the pictures myself and checked the numbers against the database, read-only. J-11
"Repair the damaged saved results" can close.

But while that was happening, something else went wrong that nobody in the pipeline noticed. The routine
re-test of two older journeys started a **second copy of the app pointed at the real, protected
database** — the one the owner said in writing must stay switched off. It wrote ten rows into five
scratch tables there. No real data was harmed: I checked every one of the twenty-five tables myself and
the prices, the saved briefings, the eleven rebuilt days and the audit records are all exactly as they
were. The cause is in the automation, not in anything a person wrote this week, and it will happen again
on the very next run. That is why I am stopping and asking the owner.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels are honest | passing | passing (re-verified) | `reports/qa/goal-market-compass-iter-23-evidence/J-01-verify.png` — replay UT-J-01 PASS; GRMN shows stored sector "Consumer Discretionary", 1/539, regime 73.18. **Ran on the canonical DB, not the clone.** |
| J-02 What changed since last session | partial | partial (not tested) | out of scope this iteration (owner ruling item 9) |
| J-03 Plain-English summary | partial | partial (not tested) | out of scope this iteration |
| J-04 Candidates explain why / why-not | passing | passing (re-verified) | `.../J-04-verify.png` — replay UT-J-04 PASS; expects held: "Strong leader (81.2)", "Not priority (20)"→"TRV", "REGIME_RISK_OFF". Capture still crops above the candidate card → `evidence_makeup`. **Ran on the canonical DB.** |
| J-05 Close freezes one manifest | partial | partial (not tested) | out of scope this iteration |
| J-06 A frozen manifest never changes | partial | partial (not tested) | out of scope this iteration |
| J-07 Today page ten-second read | failing | failing (not tested) | out of scope this iteration |
| J-08 Market page moves over | failing | failing (not tested) | out of scope; `/market` re-confirmed 404 (route not built) |
| J-09 Backend fits the host | partial | partial (not tested) | out of scope this iteration |
| J-10 Recovery of the two deleted days | passing | passing (re-verified) | `.../J-10-AVB-2026-08-12-result.png` — clone-backed; AVB renders real scores; bars API returned 554757.0 / 3706010.0, exact match |
| **J-11 Clean regeneration of derived state** | **partial** | **passing** | `.../J-11-today-frontier-result.png` + `.../J-11-incident-2026-08-11-result.png` (clone-backed boot, `/proc` fd-checked) + `runs/goal-market-compass-iter-23/j11-disposable-clone-*.json` + this evaluator's own read-only re-derivation on both databases |

J-11's two screenshots were opened and read: the frontier (2026-08-12) renders regime 73.18 / Expansion
severity 25.85 with manifest version 6, frozen, **not prospective-eligible**; the incident date
(2026-08-11) renders regime 73.44 / severity 26.03 with a **retrospective**, version 3, frozen,
not-prospective-eligible manifest and the honest banner `Basis: rebuilt — the source scanner run was
recreated after this manifest was frozen`. That is precisely the honesty AG-12 and AG-17 demand.

## Anti-goal Check

Every one of AG-1..AG-18 was checked; the eight that this iteration could plausibly touch are listed with
what I actually looked at. Deterministic scan (`iter-23/scan-report.md`): **CLEAN**. Diff:
`iter-23/iter-diff.md` — 5 new files, zero existing production files modified, no dependency manifest, no
LICENSE, no `config.yaml` change.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unproven values badged | OK | "Not yet proven" badges visible on all three scores in J-01 and J-10 screenshots |
| AG-3 displayed numbers correct | OK | Screen values (73.18 / 25.85 / 73.44 / 26.03) match the dev's API captures; AVB volumes match the certified 554757.0 / 3706010.0 |
| AG-7 no secrets | OK | scan-report CLEAN on added lines; no config/env file added |
| AG-8 no crash / no unbounded load | OK | No error boundary fired in any screenshot; the one log ERROR was a shutdown-time task cancellation, not a page failure |
| AG-9 offline ingest | OK | `daily_prices` byte-identical on both DBs (3,310,374 rows, ohlcv_sum 52,367,098,848,872.56); the pre-boot check's own import scan shows no network module in the new files |
| AG-10 host caps | OK | All four boots logged `memory_cap_mb=8192 malloc_arena_max=2` + `host-guard: cpu_list=0-15 blas_threads=8`; the new wrapper `exec`s the unmodified `scripts/start-backend.sh` |
| AG-12 manifest immutability | OK | 24 rows on BOTH databases, every column field-identical to the iter-16 certified dump; 0 rows for the 7 manifest-less incident dates |
| AG-17 provenance not rewritten | OK | `prospective_eligible` = 0 on all 24 rows on both DBs; the incident-date manifest still shows retrospective / not eligible / `Basis: rebuilt` on screen |
| AG-2, AG-4, AG-5, AG-6, AG-11, AG-13..AG-16, AG-18 | OK | Not implicated: the diff adds only clone/provenance tooling + tests + one launch wrapper; no scoring, selection, schema, UI or evidence-ledger code changed |
| **Owner ruling item 3 (not an AG, but binding)** | **VIOLATED — unresolved** | The canonical database was booted and written to. See below. |

Paid/external SaaS: none — no dependency manifest changed. License: unchanged. Fabricated/substituted
data: none — every displayed number traces to stored rows I re-read.

### The violation, precisely

`scripts/automation/goal-iter-lean.sh:256-257` starts the backend with
`bash $REPO_ROOT/scripts/start-backend.sh` and no `TRENDORA_CONFIG`, so the deterministic replay lane
served J-01 and J-04 from the **canonical** database (`logs/backend.log` boots at 2026-08-27T20:16:49Z and
20:18:01Z carry no launch-guard line, unlike the clone boot at 20:29:15Z recorded in
`runs/goal-market-compass-iter-23/verify-clone/backend-qa-boot.log`). Ten rows were written into five
derived caches of `apps/backend/data/trendora.db`: `event_study_cache` 0→5, `market_phase_cache` 0→2
(keys `2026-07-23` and `2026-03-30` — exactly the J-04 replay dates), `coverage_snapshot` 0→1,
`availability_cache` 0→1, `membership_timeline_cache` 0→1, `created_at` 20:19:57.215888 … 20:26:08.352318
UTC — the last matching the canonical `trendora.db-wal` mtime `20:26:08.352941` to the millisecond.

Two things make this worse than it looks:

1. **The safety proof could not have caught it.** The iteration proves the canonical DB unchanged by
   sha256 of the main `.db` file. That file is unchanged — because SQLite in WAL mode puts new writes in
   the sibling `-wal` file until a checkpoint. The database's *content* changed while its *bytes* did
   not. The final sha256 was also taken at 20:13Z, three minutes **before** the breach.
2. **It was a near miss, not a safe outcome.** `GET /api/compass?as_of=<historical date>` mints a
   manifest for any date that lacks one. The replay asked for 2026-07-23 and 2026-03-30; both already
   carry manifests, so nothing was minted. Had the script used any other historical date — for instance
   one of the seven damaged days that still have no manifest — it would have permanently created one on
   the protected database. That is the exact irreversible act AG-12/AG-17 and three separate owner
   rulings forbid.

What was **not** harmed, re-derived by me across all 25 tables on both databases: prices
(3,310,374 rows; id_sum 5,479,295,003,075; ohlcv_sum 52,367,098,848,872.56 — the certified `80441b37…`
inputs), scanner runs (3,128; max id 3158; all eleven rebuilt runs 3148–3158 present; newest creation
time still 2026-08-26), all 24 manifests field-identical, provider runs 549, results / sector / theme /
forward-return / watchlist rows fingerprint-identical, and the quarantine row untouched
(`active: 0`, `updated_at 2026-08-27 09:27:08.662797` — still iteration 22's write).

## Coherence

`iter-23/coherence.md` = **COHERENCE-PASS**. No structural veto. Its two advisory notes (the `/market`
404 as a pre-existing J-08 gap; the `[TARGET]` blueprint rows) match what I found independently.

## Process note

The iteration spec declares `Depth: full` with a written Trigger-1 justification, but
`iter-23/depth-dispatched` reads `lean` and only decomposer / developer / review / browser-qa / coherence
ran — no QA agent, no independent auditor, no closure lane. The silent full→lean demotion that last fired
in iterations 2, 6 and 8 has recurred after fourteen clean iterations. On every one of those fourteen
iterations the independent auditor found something the earlier lanes missed; on this one there was no
auditor, and the canonical-database boot went unreported by every lane that did run.

## Next-Step Recommendation

Please answer three questions. Nothing else should run until then, because the next run would repeat the
same mistake automatically.

1. **The ten scratch rows now sitting in your protected database — leave them, or remove them?** They are
   correct, they were computed from the repaired data, and the app would create them anyway the first
   time anyone uses it. Removing them means writing to that database again, which is also something you
   said should not happen without your say-so.
2. **May the automation be fixed so it can never start the app against the real database again?** Today
   the routine re-test always starts the app with the normal settings file. Your written instruction
   defers this kind of tool work, so it needs your permission. Until it is fixed, every future run that
   re-tests an old journey will start the real database again — and next time the date it asks for may be
   one that creates a permanent saved briefing, which is the thing you have forbidden three times.
3. **Do you agree J-11 is finished?** I am recording it as passing, because the check you asked for was
   run on the throw-away copy exactly as you specified and it passed. Three small things are still owed
   and none of them blocks it: the 7.8 GB throw-away copy is still on disk and should be deleted; the
   "what changed" and "plain-English summary" journeys were not re-tested on the repaired data; and the
   `/market` page still does not exist (that is the J-08 job, not this one).

If the answer to 1 is "leave them" and to 2 is "yes, fix it", then the next run should be: fix the
launcher so it refuses to start against the real database whenever a copy is in force, then go back to
normal product work in your own order — J-09 "the backend fits the host", then J-05/J-06 "freeze one
manifest and never change it", then J-07/J-08 "the Today page and the Market page". Run it at full depth:
this iteration was meant to be full depth and was quietly downgraded, and the missing auditor is part of
why the database mistake went unreported.

## Halt Justification

Halting as STALLED, not CONTINUE, because every way forward needs a decision only the owner can make:

- **Deciding what to do about the ten rows now in the protected canonical database.** Leaving them
  contradicts a written instruction; removing them means another write to the same protected database.
  Either way it is the owner's call — an irreversible-class step needing sanction.
- **Authorising the automation fix.** Owner ruling items 7 and 9 explicitly defer Goal Mode tooling work
  ("Do not spend another J-11 iteration improving automation infrastructure"). The loop cannot lawfully
  grant itself that scope.
- **No safe alternative task exists.** Every remaining journey (J-02, J-03, J-05, J-06, J-07, J-08, J-09)
  needs a browser, and every browser iteration also re-tests the still-passing set — which is exactly the
  lane that boots the canonical database. The loop also cannot protect itself by re-arming maintenance
  isolation: the owner's own clarification says isolation MUST NOT be required for this work, and the
  session memory says both engine flags must not be re-armed.

Not REGRESSION: no journey moved from passing to failing (J-11 in fact moved partial → passing), and no
enumerated anti-goal AG-1..AG-18 was violated — I checked all eighteen and re-derived the data-integrity
ones live. What was violated is a binding owner ruling, and the harm is confined to ten rows in five
recomputable derived caches with zero canonical-data change. It is recorded in `journey-history.json` as
an unresolved critical entry so no future GOAL_ACHIEVED can pass over it.

Not ESCALATE: escalation asks the next iteration to run deeper. The next iteration must not run at all
until questions 1 and 2 are answered.
