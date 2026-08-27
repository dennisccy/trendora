# Iteration 22 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

## Summary

The database repair is finished and I checked it myself. Stage G — the final acceptance check of
the damage caused by the iteration-5 drill — ran against the live 8.4 GB database, passed all
twelve of its checks, and wrote the one thing it was allowed to write: it switched the "do not
touch these eleven days" quarantine flag off. I opened the database read-only and re-measured
every headline claim rather than trusting any report. Every number matched. But the loop must now
stop, because every next step needs a decision only the owner can make: the application has been
switched off for fourteen iterations, and turning it back on is now both possible and risky. It is
also the only way to finish the last piece of Stage G that the goal file itself asks for.

## Journey Results This Iteration

Iteration 22 ran under **maintenance isolation**: starting the application, browser testing and the
deterministic replay lane were forbidden by this iteration's own contract (engine refusal record:
`runs/goal-session-market-compass/iter-22/maintenance-isolation-refusals`, entry
`2026-08-27T13:25:03Z operation=browser-qa-phase`). `reports/phase-goal-market-compass-iter-22-ui-test-results.md`
is therefore all-SKIPPED with that exact reason. Every journey keeps its prior recorded status; no
journey is promoted to `passing` on an iteration that produced no serving evidence.

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest and near-complete | passing | passing (carried; spot-checked) | reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png — GRMN shows a real stored sector ("Consumer Discretionary"), 1/539, regime 73.24, all three scores badged "Not yet proven"; `scoring.py` zero diff since |
| J-02 What changed since previous session | partial | partial (carried, not re-verified) | reports/qa/goal-market-compass-iter-4-evidence/J-02-verify.png (prior) |
| J-03 Plain-English summary with cited facts | partial | partial (carried, not re-verified) | reports/qa/goal-market-compass-iter-4-evidence/J-03-verify.png (prior) |
| J-04 Candidate why and why-not | passing | passing (carried; `evidence_makeup` still set, 4th iteration) | reports/qa/goal-market-compass-iter-4-evidence/J-04-verify.png — behaviour proven by the iter-4 results row; the framing of the picture is wrong, no capture possible under isolation |
| J-05 Close freezes one manifest | partial | partial (carried, not re-verified) | reports/qa/goal-market-compass-iter-3-evidence/UT-02-manifest-historical-badges.png (prior) |
| J-06 A frozen manifest never changes | partial | partial (carried, not re-verified) | reports/qa/goal-market-compass-iter-3-evidence/UT-02-manifest-historical-badges.png (prior) |
| J-07 Today page ten-second read | failing | failing (carried, not re-verified) | reports/qa/goal-market-compass-iter-0-evidence/UT-J-07-fail.png (prior) |
| J-08 Market page moves over intact | failing | failing (carried, not re-verified) | reports/qa/goal-market-compass-iter-1-evidence/UT-J-08-fail.png (prior) |
| J-09 Backend fits the host | partial | partial (carried, not re-verified) | reports/perf-budgets.md:12114-12236 (prior) |
| J-10 Bounded recovery of two trading days | passing | passing (carried; spot-checked live) | my own read-only re-derivation: 585 `daily_prices` rows on each of 2026-08-11 and 2026-08-12; AVB volumes 554757 / 3706010 intact; whole-table fingerprint reproduces `80441b37f816d41c…` exactly |
| J-11 Incident-bounded clean regeneration | partial | **partial — advanced; Stage G executed and passed** | runs/goal-market-compass-iter-22/j11-stage-g-verify-*.json (26 live artifacts) + my own read-only re-derivation of every headline figure (below) |

### What I verified myself for J-11, read-only, against the live database

- **The one authorized flag write landed and nothing else did.** `maintenance_boundaries` holds one
  row, `id=1`, `j11-incident-recovery`, `active=0`, `updated_at 2026-08-27 09:27:08.662797`, and all
  eleven quarantined dates are still listed — deactivated, not deleted, exactly as ruling item 11
  requires.
- **A check no lane ran:** I asked every one of the 25 tables for its newest creation timestamp. The
  newest anywhere is `scanner_runs` at 2026-08-26 10:53:02 (Stage D). The single 2026-08-27 write in
  the whole database is the boundary flag. Nothing else has been written since.
- **The eleven rebuilt days are frozen and unique.** Ids 3148–3158 map one-to-one onto the eleven
  incident dates, all stamped `53d2ffd10cdb…`, created 10:52:55.552946 → 10:53:02.010362. Exactly
  eleven runs in the whole table carry that stamp (no twelfth), and 3158 is the highest id in the
  table.
- **Raw prices untouched:** 3,310,374 rows, 1996-01-02 → 2026-08-12; I recomputed the certified
  recipe (`count/min_date/max_date/id_sum/ohlcv_sum` → sha256) and got
  `80441b37f816d41c3182d9559f03095b89d6c7973acf781c18f12b77be5024cc` — the certified post-AVB
  baseline, to the character.
- **Forward-looking figures:** 6,814,320 rows total, 16,592 on the eleven rebuilt runs — identical to
  Stage E's record and to my own iteration-20/21 measurements.
- **Manifests are byte-identical.** I compared all 24 stored manifests field-by-field across all 28
  columns against the certified iteration-16 copy: **zero differences**, no extra rows, no missing
  rows. Zero manifests exist for the seven manifest-less incident dates. Every `prospective_eligible`
  is still 0.
- **Evidence ledgers unchanged:** both files hash to the recorded values (`5d435cff…`, `3e85847e…`),
  7 entries each, all FAIL. `data_provider_runs` 549, `watchlist` 6.
- **Caches:** the five deliberately-cleared tables are at 0; `index_series_cache` holds its one row;
  `membership_timeline_cache` is now 0 — this iteration's second authorized write.
- **The stale-cache find is real and was closed.** The preserved membership row held
  `exits = ['AMSC','MARA']` for 2026-08-10 while a fresh recompute gives `['MARA']`
  (`j11-stage-g-verify-membership-timeline-check.json`). The row was deleted, per the fallback
  Stage F had already pre-approved. That is a stale value caught before it could ever be shown.
- **The guard edit is exactly what was specified:** two hunks in `data_manager.py` (one import, one
  `if not boundary["blocked"]:` around the existing self-heal write) and nothing else;
  `scanner.py`, `compass.py`, `scoring.py`, `j10_recovery.py`, `j11_preboot_guard.py` all show zero
  diff against the iteration snapshot.
- **The application really is off:** nothing is listening on ports 8000 or 3000, and no backend or
  frontend process exists on this host.

### Two things I weighed against the iteration's own claim

1. **The corrected check never ran on this write.** The reviewer's first pass failed this iteration
   because the check guarding the irreversible flag write could not fail, and the flag was written
   before the one real reconciliation check. The fix came after the live run. I did not accept the
   reviewer's word that the corrected gate would have passed: the corrected rule requires the delete
   to report success **and** a live count of zero afterwards. The evidence records `deleted: true`,
   and I measured the live count myself — it is 0. So the corrected gate reconciles on this
   historical write. The verdict-then-write ordering is fixed for any future run.
2. **`FULLY REPAIRED` is a database-level claim, not a serving claim.** `docs/goal.md:1408` names
   Stage G "final serving/replay verification", and `:1978-1985` places on Stage G the assertions
   that the rebuilt days serve the complete raw basis and that J-01/J-02/J-03 replay clean. None of
   that happened, because ruling item 4 forbade starting the application until Stage G passed. I
   confirmed line 1408 reads exactly as quoted. This is a real contradiction inside the goal file —
   not a developer mistake — and the coherence lane explicitly left the ruling to me. My ruling is in
   the Halt Justification.

## Anti-goal Check

Worked from `runs/goal-session-market-compass/iter-22/scan-report.md` (**CLEAN**) and
`iter-diff.md` (5 files, all backend: `data_manager.py` +9/-1, the new `j11_stage_g_verify.py`,
its CLI, and two new test files; no manifest, no config, no `docs/goal.md` change), plus my own
greps and live queries.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 not-yet-proven badging | OK | No score/claim surface touched; both ledgers still 7 entries, all FAIL (I hashed both files) |
| AG-2 decision-quality only | OK | No product surface, no order/return language anywhere in the diff |
| AG-3 displayed numbers correct | OK | No computation changed; the only displayed-value-adjacent change is a write **guard**. The stale-cache delete strictly improves this (a wrong `exits` list can no longer be served) |
| AG-4 no overfit edges | OK | No pattern promoted; no ledger entry added |
| AG-5 determinism / no-lookahead | OK | No scoring or forward-return code touched; `forward_returns` count unchanged at 6,814,320 |
| AG-6 referee gate | OK | No Evidence Claims introduced this cycle |
| AG-7 no hard-coded credentials | OK | Scan CLEAN; my own grep for key/secret/password/token patterns in both new source files returned nothing |
| AG-8 data-shape/scale resilience | OK | No schema or basis change; no unbounded whole-table ORM load added; peak memory 1,010.5 MB |
| AG-9 offline-deterministic ingest | OK | No provider or network call. The one `import socket` is a loopback `connect_ex` probe of 127.0.0.1:8000/3000 — no external host, no data fetched. Raw prices byte-identical (fingerprint re-derived by me) |
| AG-10 host resource ceiling | OK | No launch script or host-guard file in the diff; measured peak 1,010.5 MB against the 8192 MB cap (`j11-stage-g-verify-memory-check.json`) |
| AG-11 no new composite number | OK | No candidate-facing value added |
| AG-12 manifest immutability | OK | All 24 manifests field-identical across 28 columns vs the certified iteration-16 copy (my own comparison); `source_run_id` values still historical (3112/3048/3049/3081), never rebound to 3148–3158 |
| AG-13 system-vs-market vocabulary | OK | No vocabulary or label changed |
| AG-14 no Tapeology coupling | OK | No import, call or write; the sibling project's services were not contacted (and are not even running) |
| AG-15 no outcome-tuned selection | OK | No selection rule or threshold touched |
| AG-16 cohorts are not controls | OK | No cohort surface or narrative touched |
| AG-17 repair never rewrites provenance | OK | Every one of the 24 manifests is still `prospective_eligible = 0`; no `available_at_utc`, version or hash moved. The repair changed no historical classification |
| AG-18 bounded manifest migration | OK | No schema migration; `next_session_manifests` untouched (verified live) |

**Ledger:** unchanged at **7 total, 0 unresolved**. No new violation, minor or critical.
**Coherence:** COHERENCE-PASS (`runs/goal-session-market-compass/iter-22/coherence.md`) — no veto.
**Goal-edit drift:** none. I ran `goal_gate.py hash-journeys` myself; all eleven journey hashes are
byte-identical to the recorded ones, so `docs/goal.md` has not moved since iteration 19 and no
`journeys-changed.md` fired.

## Next-Step Recommendation

The database repair is done. The next step is a decision, not a task, and it belongs to the owner:
**may the application be started again?** Everything that could still move a journey depends on that
one answer, because no journey can be checked while the application is off.

If the answer is yes, the first job of the next iteration should be the piece the goal file still
asks for and that has never been done: start the backend under supervision, open the Today, Market
and Compass pages for a rebuilt day, and confirm the repaired data serves correctly. Please read the
warnings in the Halt Justification first — with the quarantine now switched off, one page request
for the wrong date can permanently create a record that the goal forbids.

If the answer is not yet, there is one useful job that needs no application at all: close the seven
remaining unguarded write paths (the owner's own written plan already reserved this as work to do
after Stage G). Say which of the two you want, and the loop can carry on.

## Halt Justification

I am halting rather than continuing, and three separate stop rules from
`.claude/judgment-rubrics.md` §3 fire at once. None of them is "nothing works".

**1. Every path to journey progress needs an owner decision.** Ten of the eleven journeys can only
be verified by looking at pages in a browser. The application has been switched off by contract for
fourteen iterations. Only a person can lift that: the session is running with the isolation switch
on, and an agent must never turn off its own safety setting. The owner has also said in writing that
whether the application may now boot is their decision and that they have not made it.

**2. The next step is genuinely irreversible and was not pre-approved.** Starting the application
now is riskier than it was a week ago, and I checked each reason in the code and the database myself:

- The quarantine that used to block the eleven damaged days is now **off** — correctly, as the
  owner's plan required, but it means the seven remaining unguarded request paths are unguarded in
  fact, not just in principle.
- Seven damaged days still have **no saved briefing** (12 and 13 May, 10, 13, 24 and 27 July,
  3 August — I confirmed zero rows for each). One ordinary page request for any of them would
  permanently create one. The goal file forbids exactly that, and nothing in the code stops it now.
- Sixteen dates inside the damaged window have prices but no day-record; a page request for one
  would create a twelfth day-record carrying the same stamp as the eleven rebuilt ones.
- The first request after start-up can do heavy work while someone waits, because two "serve last
  time's answer" caches were deliberately emptied — on a machine that froze once from memory
  pressure. Let the background warm-up finish first and record peak memory.

**3. Two honest readings of the goal file conflict, and the choice changes what "repaired" means.**
The goal file calls Stage G "final serving/replay verification" and puts on Stage G the claim that
the rebuilt days serve correctly — while the same owner ruling forbids running the application until
Stage G passes. Stage G therefore cannot do what one line of the goal file assigns to it. **My
ruling:** the owner's latest written instruction (ruling item 9) lists Stage G's required checks and
that list is entirely database-level; every one of those checks passed and I re-derived them myself.
So the repair attempt legitimately reached its owner-defined success state, and the terminal lines it
emitted are honest. But the serving check is still owed, so J-11 stays **partial**, not passing. I
will not certify a journey complete on the strength of a check the goal file names and nobody ran.
One owner line settles this either way: either "the serving check is part of Stage G — do it and then
J-11 is done", or "Stage G was the database gate; the serving check is ordinary product work".

**What would unblock the loop — any one of these:**

1. **Authorize the supervised boot.** Resume with the isolation switch off so the application can
   start and browser testing can run again. Next iteration then does the serving/replay check first,
   then normal product work (the goal file's own order puts J-09 next, then J-05/J-06, then
   J-07/J-08).
2. **Authorize the hardening pass first, application still off.** Close the seven unguarded write
   paths using the same guard pattern this iteration used for the eighth, then boot. Slower, safer.
3. **Settle the wording.** Say whether the serving/replay check belongs to Stage G or comes after it,
   and optionally remove the contradiction from `docs/goal.md:1408`.
4. **Do nothing else and simply resume** — but then the loop can only produce work that cannot be
   verified, which is what the last fourteen iterations already were.

**Not REGRESSION:** nothing that worked stopped working; no journey was tested, so none could fail;
outside the two authorized writes not a single value in the whole database changed; the anti-goal
ledger gained no entry. **Not GOAL_ACHIEVED:** seven journeys are still `partial` or `failing`, no
journey has fresh serving evidence, and J-11's own serving check is unperformed. **Not ESCALATE:**
this run already used full depth, which is what produced these findings.

**One standing note before any future GOAL_ACHIEVED certification:** the goal-slicing tool still
emits J-10's line twice (12 headings for 11 journeys, `iter-22/goal-slice.md:508-509`), a known
framework defect the owner deferred until after Stage G. It is harmless today and must be fixed
before certification.
