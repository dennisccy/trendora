# Iteration 19 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

**Owner-facing status lines** (all four checked by this evaluator against the live database; no correction needed):
`J-11 STAGE D AUTHORIZED: YES` · `J-11 STAGE D EXECUTED: YES` · `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE` · `J-11 MAINTENANCE BOUNDARY: ACTIVE` · `J-11 LIVE PRE-BOOT GUARD: ARMED`.
Stage E, Stage F and Stage G are all still `NO`.

## Summary

The one big job the owner allowed was done, and it worked. Eleven damaged days now hold results again.
I did not take that from anyone's write-up — I opened the 8.4 GB database read-only and measured
everything myself. The work stayed inside its lines: comparing the whole database against the state it
was in at the end of the last iteration, exactly four tables changed, and they are the four the owner
allowed. Nothing else moved at all. But this is the middle of a four-step repair, not the end of it. The
eleven rebuilt days still have no forward-looking figures and their saved copies of old answers have not
been refreshed. Two further steps are already approved in writing, so there is real, allowed work to do
next. The app must stay switched off until the last step passes.

## Journey Results This Iteration

Browser testing and the replay lane were **forbidden by contract** this iteration (maintenance
isolation), so no journey was tested and every journey keeps its prior recorded status. The results file
records this in its own `**Reason:**` line, and the engine logged its refusal at
`runs/goal-session-market-compass/iter-19/maintenance-isolation-refusals` (2026-08-26T14:01:10Z).

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest on new runs | passing | passing (carried, NOT re-verified) | spot-check: `reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png` — GRMN carries a real stored sector; corroborated live (0 unknown sectors on all 11 rebuilt runs) |
| J-02 What changed since last session | partial | partial (carried, NOT re-verified) | `reports/phase-goal-market-compass-iter-19-ui-test-results.md` (SKIPPED — maintenance isolation) |
| J-03 Plain-English summary with cited facts | partial | partial (carried, NOT re-verified) | same |
| J-04 Candidates explain why and why-not | passing | passing (carried, NOT re-verified) | spot-check: `reports/qa/goal-market-compass-iter-4-evidence/J-04-verify.png` — **capture defect**, `evidence_makeup: true` set; behaviour confirmed by `reports/phase-goal-market-compass-iter-4-ui-test-results.md:21` (UT-J-04 PASS) |
| J-05 Close freezes one manifest | partial | partial (carried, NOT re-verified) | same as J-02 |
| J-06 A frozen manifest never changes | partial | partial (carried, NOT re-verified) | corroborated live: all 24 manifest rows content-identical to the iter-16 certified baseline |
| J-07 Today page ten-second read | failing | failing (carried, NOT re-verified) | same as J-02 |
| J-08 Market page moves over intact | failing | failing (carried, NOT re-verified) | same as J-02 |
| J-09 Backend fits the host | partial | partial (carried, NOT re-verified) | same as J-02 |
| J-10 Bounded recovery of two deleted days | passing | passing (carried, NOT re-verified) | spot-check re-derived read-only: 585 `daily_prices` rows on each of 2026-08-11/12; AVB volumes 554757 / 3706010 intact; whole-table fingerprint reproduces iter-16/17's `80441b37…` |
| J-11 Incident-bounded clean regeneration | partial | **partial — advanced** (Stage D executed) | `runs/goal-market-compass-iter-19/j11-stage-d-execute-regeneration.json`, `…-mutation-accounting.json`, `…-frozen-identity.json`; plus this evaluator's own read-only live-DB re-derivation (below) |

### What I verified myself on the live database (read-only, no service started)

- **Eleven rebuilt days.** Exactly one new run per damaged day, ids 3148–3158, created 10:52:55 →
  10:53:02 UTC, every one stamped `53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55`,
  each with 539–542 result rows, 31 sector rows and 11 theme rows.
- **Nothing else changed — proven across iterations, not just inside this one.** I recomputed the
  whole-database table sweep live and diffed it against `runs/goal-market-compass-iter-18/
  j11-iter18-full-table-sweep-after.json`. Exactly four tables differ (`scanner_runs`,
  `scanner_results`, `sector_scores`, `theme_scores`); no table appeared or disappeared; the other 21
  are fingerprint-identical. The deltas reconcile exactly: +11 runs (rowid sum +34,683 = sum of
  3148…3158), +5,942 results, +341 sector rows (31×11), +121 theme rows (11×11).
- **Saved briefings untouched, by content and not by row id.** All 24 `next_session_manifests` rows
  compared field-by-field across all 28 columns against `runs/goal-market-compass-iter-16/
  j11-stage-d-certified-baseline.json` — identical once only serialization differences are normalized.
  This closes the auditor's B2 concern for the one table where it mattered most.
- **Raw prices untouched.** I recomputed the price-table content fingerprint live and reproduced
  iterations 16 and 17's independently recorded `80441b37…` byte-for-byte (3,310,374 rows, ohlcv sum
  52,367,098,848,872.56). Both evidence ledgers are byte-identical by `sha256`.
- **The identity was recomputed, not copied.** Hashing the three provenance source files on disk plus
  the recorded config values reproduces `53d2ffd1…` exactly. `git log` shows those three files last
  changed at iteration 12 and `config.yaml` at iteration 4, and all four are clean in the working tree —
  so the equality with the iteration-14/16/17/18 readiness values is forced arithmetic, not a copy.
- **The rebuilt numbers are faithful.** I compared the rebuilt 2026-08-12 board against the pre-incident
  screenshot captured at iteration 4: GRMN is rank 2 in both, sector "Consumer Discretionary" in both,
  leadership 89.12 in both, same B/E/E grades, 539 results in both; entry 28.66 vs 28.74, risk 58.55 vs
  58.50, market regime 73.18 vs 73.24 — tiny shifts consistent with the authorized AVB volume correction
  and engine drift since iteration 4. Regime and breadth also join the surviving history smoothly at
  every boundary (05-11 → 05-12 → 05-13 → 05-20; 07-09 → 07-10 → 07-13; 07-23 → 07-24).
- **No service ran.** `ss -ltnp` and `ps aux` show nothing on ports 8000/3000 now, matching the
  handoff's own before-and-after checks.

### Three things I found that no other lane reported

1. **The "latest" pointer moved.** Before this iteration the app's default view fell back to 23 July.
   Now the newest stored day is 12 August (run 3158) — a rebuilt day with **zero** forward-looking
   figures and un-refreshed saved answers. Start-up is still blocked (the quarantine covers 12 August),
   but the cost of an accidental start is higher than it was.
2. **A new way to create a forbidden saved briefing.** With 12 August now the newest stored day, the
   seven damaged days that have no saved briefing count as historical, and
   `apps/backend/app/engine/compass.py:1040-1053` creates one automatically for a historical date on a
   plain page request. That is the exact trap the plan's own acceptance section warns about, and it is
   only harmless while the app stays off.
3. **The rebuilt days now carry better sector labels than their neighbours.** Every rebuilt day has 0
   rows with a missing sector; every retained neighbour has 422 missing out of 540. This is the sector
   work behaving as designed on new runs, not a fault — but it means the eleven rebuilt days are not
   directly comparable with their neighbours in any sector-level chart, which the final verification
   step must account for.

## Anti-goal Check

Worked from `runs/goal-session-market-compass/iter-19/scan-report.md` (**CLEAN**) and
`iter-19/iter-diff.md` (4 files, all new, all under `apps/backend/`), plus my own
`git status --porcelain -uall` (65 paths; the only product code is the four new backend files).

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 no unproven claim presented as proven | OK | No new claim; both evidence ledgers byte-identical by `sha256`; every manifest still `prospective_eligible = 0` |
| AG-2 decision-quality only | OK | No user-facing text or surface added; backend maintenance tooling only |
| AG-3 displayed numbers correct | OK | Nothing displayed (no service ran). Positive evidence gathered instead: the rebuilt 2026-08-12 board reproduces the pre-incident screenshot's rank, sector, leadership and grades (see above) |
| AG-4 no overfit edges | OK | No pattern, referee or claim touched |
| AG-5 determinism / no lookahead | OK | The write loop uses `prices.bar_cache`; `bars_asof` (`prices.py:395-397`) slices `date <= d` by `bisect_right`, and Stage D adds no price bars, so the cache caveat does not apply. Read the code myself |
| AG-6 no unrefereed evidence claim | OK | No evidence-derived claim shipped; ledgers unchanged |
| AG-7 no hard-coded credentials | OK | Grep for key/secret/token/password/private-key across all four new files: zero matches; scan-report CLEAN |
| AG-8 no unbounded whole-table ORM loads | OK | The only `select(Model)` in production code is `j11_stage_d_execute.py:128`, filtered by `.where(name == …).first()`. The `.all()` at line 446 is column-projected and filtered to NULL-or-legacy rows, which the plan's TC-13 explicitly requires. The unfiltered ones are in fixture tests only |
| AG-9 offline-deterministic ingest | OK | Grep for `requests.`/`httpx`/`urllib`/`socket.`/`aiohttp`/`http.client`/`urlopen` across all four new files: zero matches. Sector labels come from the committed `universe_pool.csv` / config map, not a fetch |
| AG-10 host resource ceiling | OK (with a forward-looking caution) | No launch script edited, no cap removed or weakened; the maintenance script was run bare, the same way every prior J-11 live script in this session was. **Caution, not a violation:** the auditor's B3 notes the run held ~540 symbols' full price series through the lazy cache path on a host with a documented 2026-08-20 freeze. Stage E touches a 6.8-million-row table and should use the pre-filled cache or a capped launcher |
| AG-11 no new composite number | OK | Grep for fit/conviction/match/probability/blended/composite: zero matches; no new score attached to anything |
| AG-12 manifest immutability | OK | Strongest check I ran: all 24 rows content-identical across all 28 columns against the iteration-16 certified baseline. Count still 24; the four damaged dates still hold 12 rows; the seven others still hold zero |
| AG-13 system-vs-market vocabulary | OK | No readiness or regime wording added or changed |
| AG-14 no Tapeology coupling | OK | Grep: zero matches |
| AG-15 no outcome-tuned selection | OK | No selection rule or threshold touched; `scoring.py`, `compass.py`, `config.yaml` all clean in the working tree |
| AG-16 cohorts are not controls | OK | No cohort logic touched |
| AG-17 repair never rewrites provenance | OK | Raw prices content-identical to the iteration-16/17 record; all manifests still marked not-usable-as-prospective; no prior evidence file modified (`git status` shows every iteration-19 artifact as new, and the new script refuses to write into a directory that already holds its filenames) |
| AG-18 the authorized migration preserves everything | OK | No schema change this iteration; manifest table shape and contents unchanged |

**Ledger: 7 total, 0 unresolved. No new violation, no critical violation.**

**Coherence:** COHERENCE-PASS (`runs/goal-session-market-compass/iter-19/coherence.md`) — no blocking
violations, one advisory note cross-referencing the auditor's B1.
**Deterministic scan:** CLEAN. **Review:** PASS (one NOTE, since resolved). **QA:** PASS.
**Audit:** PASS_WITH_GAPS (B1 IMPORTANT; B2/B3 gaps; B4/T1–T4/P1 observations; P2 resolved).

## Next-Step Recommendation

**Do the next step of the repair: Stage E, the forward-looking figures.** The owner already approved
Stages D, E, F and G together in writing on 2026-08-26, and nothing failed this time — so no new
permission is needed to carry on. The eleven rebuilt days currently hold no forward-looking figures at
all (I checked: zero rows). Stage E fills the gaps the incident caused, without overwriting anything
that survived. Then Stage F refreshes the saved answers, and only then may Stage G decide whether the
damage is truly repaired.

Three things must ride along, and one must be settled before the final step:

1. **Keep the app switched off, and keep browser testing off.** The rule already says so until the last
   step passes. Two specific reasons, both of which I confirmed myself: a page request for a date with
   no stored day would create a twelfth day carrying the same stamp as the eleven rebuilt ones, and a
   page request for one of the seven damaged days without a saved briefing would create the very
   briefing the plan forbids.
2. **Settle the stamp question before the final step is designed.** The final step's approval rule says
   "all eleven rebuilt days carry the single fresh stamp". That is true today, but the stamp is simply
   the current engine's stamp, so any future ordinary day would carry it too. The final step should
   instead check against the exact list recorded here — **run ids 3148–3158, created between
   2026-08-26 10:52:55.552946 and 10:53:02.010362 UTC** — and should also confirm that no twelfth day
   carries that stamp. This does not block Stage E; it blocks designing Stage G.
3. **Watch memory on the next step.** Stage E touches a 6.8-million-row table on a machine that froze
   once before from memory pressure. Use the pre-filled cache with the known symbol list, or a capped
   launcher.

Smaller items that change nothing above: re-capture J-04's screenshot showing a candidate's why and
why-not the first time browser testing runs again (the behaviour is proven; only the picture is wrong);
tighten the four test observations the auditor listed; and note that a quality test plan file was never
produced this iteration.

**One mechanical item:** this iteration's four new backend files and its whole evidence folder are still
untracked in git at the time of scoring — confirm they reach version control.

**Five older owner questions remain open and non-blocking:** whether 3.44 GB is acceptable for J-09;
J-06's "underlying run unavailable" wording; the rewording of J-01's first two test steps; whether an
empty "next-session focus" is acceptable; and whether MNST joins the recovery list.

**Two standing framework notes:** the defect that once let a forbidden test lane run is still unfixed in
`scripts/automation/` — eleven iterations running have avoided it with the maintenance-isolation
contract rather than curing it; and `goal_gate.py`'s duplicate-journey-heading defect is still unfixed
and must be closed before any GOAL_ACHIEVED certification.

## Halt Justification (if halting)

Not halting.

**Why not STALLED, after six halts in a row (iterations 13–18)?** Because for the first time there is
approved work that no person has to unlock. The owner's 2026-08-26 ruling approves Stages D, E, F and G
in one instruction and even lists what each may and may not do. The ruling's "stop" instruction is
attached to a failure, a refusal or an unmet gate — and none of those happened: every check passed and
the step finished cleanly. Requiring another written approval now would invent a gate the owner did not
write. I am recording openly that this is a judgement call: the same paragraph also says the attempt
must end in one of two states, and someone could read that as "stop after every unfinished step". If the
owner reads it that way, one line stops the run and nothing is lost. Logged to `assumptions.md`.

**Why not REGRESSION?** Nothing that worked stopped working. No journey was tested, so none could fail.
Outside the four tables the owner authorized, not one value moved — I proved that against the previous
iteration's own recorded state, not against this iteration's self-report. The anti-goal ledger gained no
entry and still stands at 7 total, 0 unresolved.

**Why not ESCALATE?** This run already used the careful full depth, which the owner's launch conditions
require for the whole repair, and full depth is what produced the findings.

**Why not GOAL_ACHIEVED?** Two journeys are still failing (J-07 "The Today page answers the ten-second
read" and J-08 "Market page moves over intact"), six are only partly done, and the repair itself is
three steps from finished.
