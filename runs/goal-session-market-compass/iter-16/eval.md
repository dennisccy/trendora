# Iteration 16 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

**Owner-facing lines:** `J-11 STAGE D READY: YES` · `J-11 STAGE D AUTHORIZED: NO`

## Summary

The engine did exactly the four jobs the owner ordered on 25 August, in order, and then stopped
where the owner said to stop. It corrected two stored trading-volume numbers for one company
(AVB) on two days, proved the new data state, built a safety catch meant to stop the app writing
to the eleven damaged days, and re-ran the readiness check. The readiness check now answers YES
for the first time in this session. I did not take any of this from the reports. I opened the
8.4 GB database read-only and re-measured every figure myself, including re-hashing all
3,304,977 non-AVB price rows. The two volume cells moved by exactly the right amount and
nothing else in the whole price table moved at all.

But the most important thing this iteration produced is not the YES. It is a hole in the safety
catch, and I confirmed it myself. The safety catch is built correctly and sits in the right
place, but it is switched off against the real database: the list of days it is supposed to
protect was never written there, and the catch lets everything through when that list is empty.
So if anyone starts the app today, it would still write a new day's results onto 12 August —
the exact accident the owner's rule was written to prevent. The rule's literal test ("prove it
on throwaway data") is passed. The rule's purpose is not yet met. Because of that, and because
the next real step needs the owner's word, the engine stops here.

## Journey Results This Iteration

This iteration ran under **maintenance isolation**: `reports/phase-goal-market-compass-iter-16-ui-test-results.md`
is all-SKIPPED and its `**Reason:**` line names maintenance isolation, and the engine logged its
refusal at 2026-08-25T15:46:48Z in `runs/goal-session-market-compass/iter-16/maintenance-isolation-refusals`.
Application-service boot, browser QA and the deterministic replay lane were **forbidden by contract**,
not missing. Every journey therefore keeps its prior recorded status and none was re-verified; no
journey could be promoted on this iteration's evidence. No `browser-infra.json` and no
`journeys-changed.md` were emitted.

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest on new runs | passing | passing (carried, not re-verified) | spot-checked `reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png` — shows GRMN with stored sector "Consumer Discretionary"; consistent |
| J-02 What changed since previous session | partial | partial (carried, not re-verified) | `reports/qa/goal-market-compass-iter-4-evidence/J-02-verify.png` (prior) |
| J-03 Plain-English summary with cited facts | partial | partial (carried, not re-verified) | `reports/qa/goal-market-compass-iter-4-evidence/J-03-verify.png` (prior) |
| J-04 Candidate explains why and why-not | passing | passing (carried, not re-verified) | spot-checked `reports/qa/goal-market-compass-iter-4-evidence/J-04-verify.png` — historical as-of 2026-03-30 with focus count and retrospective label; consistent |
| J-05 Close freezes one manifest | partial | partial (carried, not re-verified) | `reports/qa/goal-market-compass-iter-3-evidence/UT-02-manifest-historical-badges.png` (prior) |
| J-06 A frozen manifest never changes | partial | partial (carried, not re-verified) | `reports/qa/goal-market-compass-iter-3-evidence/UT-02-manifest-historical-badges.png` (prior) |
| J-07 Today page ten-second read | failing | failing (carried, not re-verified) | `reports/qa/goal-market-compass-iter-0-evidence/UT-J-07-fail.png` (prior) |
| J-08 Market page moves over intact | failing | failing (carried, not re-verified) | `reports/qa/goal-market-compass-iter-1-evidence/UT-J-08-fail.png` (prior) |
| J-09 Backend fits the host | partial | partial (carried, not re-verified) | `reports/perf-budgets.md:12114-12236` (prior) |
| J-10 Bounded recovery of two deleted days | passing | passing (carried, NOT re-stamped) — its measured AVB defect is now corrected in the raw layer | evaluator's own read-only re-derivation: both volumes = `round(provider_volume / 2.7930001225759193)`, OHLC byte-identical, all three isolating hashes unchanged |
| J-11 Incident-bounded clean regeneration | partial | **partial — advanced; this iteration's sole target**; `READY: YES`, `AUTHORIZED: NO`; re-stamped `spec_hash` `54e9cdd8…` → `e7927ff5…` | `runs/goal-market-compass-iter-16/j11-avb-correction-mutation-evidence.json`, `j11-stage-d-preflight-gate-vs-old-baseline.json`, `j11-stage-d-preflight-gate.json`, `j11-stage-d-readiness.json` — every figure re-derived by the evaluator, not read out |

**Independently re-derived by the evaluator (read-only, `sqlite3` `mode=ro` + `PRAGMA query_only=ON`):**
AVB 2026-08-11 volume `1,549,436 → 554,757`; 2026-08-12 `10,350,885 → 3,706,010`; both exactly
`round(provider_volume / bridge_factor)` with `bridge_factor = 2.7930001225759193`; OHLC byte-identical
on both rows. All three isolating hashes byte-identical to the pre-resume true-start capture — AVB
OHLC-only `757c3c63…c8fd3`, AVB other-dates full rows `53bca571…c14f`, and the non-AVB full rows
`78146554…4997` (all 3,304,977 rows re-hashed in full by the evaluator). `daily_prices` 3,310,374 /
`1996-01-02` / `2026-08-12` / `id_sum 5,479,295,003,075` unchanged; `ohlcv_sum` moved by exactly
`7,639,554.0`. `scanner_runs` 3,117 (34 stamped `6261ca17…`, 3,083 NULL) · `forward_returns` 6,797,728
with 16,614 measured into the 11 incident dates · `data_provider_runs` 549 · manifests 24 rows,
row-dump hash `bb954b60…6d2a2e6`, DDL hash `9f653c81…c501ee`, no `FOREIGN KEY` clause · `watchlist` 6 —
every one unchanged. All 11 incident dates hold **zero** `ScannerRun`s and the newest surviving run is
2026-07-23 (authorized mid-repair state, not a regression). Live schema still exactly **24** tables.
DB file mtime `1787670395`, size `8365871104`, `-wal` 0 bytes.

## Anti-goal Check

Worked from `runs/goal-session-market-compass/iter-16/scan-report.md` (**CLEAN**, 7 untracked files
scanned) and `iter-diff.md` (12 files), plus the evaluator's own greps over all 12 changed files.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 not-yet-proven display | OK | No served surface exists this iteration; no page rendered, no endpoint called |
| AG-2 decision-quality only | OK | No candidate/advice text touched |
| AG-3 displayed numbers correct | OK | Nothing displayed; no UI or API file changed (`git diff a99b16c9 -- apps/backend/app/api/` empty; `git status` under `apps/frontend/` empty) |
| AG-4 no overfit edges | OK | No claim, no referee entry |
| AG-5 determinism / no-lookahead | OK | The correction changes two stored raw volumes; the guard reads a boundary table at boot. Neither reads a bar later than an as-of |
| AG-6 referee gate | OK | No Evidence Claim introduced |
| AG-7 no credentials | OK | scan-report CLEAN; evaluator grep for key/secret/token/password over all 12 files returns only a docstring at `apps/backend/app/models.py:153` |
| **AG-8 resilience / no unbounded ORM loads** | **MINOR — recorded unresolved** | `apps/backend/app/engine/j11_preboot_guard.py:143` `select(MaintenanceBoundary)` is an unbounded whole-table ORM load, now on the shared boot path (`warmup.py:107`). Impact today is nil (one row per boundary, read once per boot). Letter-but-not-subject: AG-8's subject is data-SCALE change and this control table never widens. QA's own AG-8 line ("No new unbounded whole-table loads") is wrong on this point. One-line fix |
| AG-9 offline-deterministic ingest | OK | Zero network calls: evaluator grep for `requests.`/`httpx`/`urllib`/`yfinance`/`yahoo_provider`/`stooq`/`socket.`/`aiohttp`/`http(s)://` over all 12 changed files returns **nothing**. Dated exception #2 stays exhausted |
| AG-10 host resource ceiling | OK | No launch script or host-guard block touched; full suite never run |
| AG-11 no new composite number | OK | No score added |
| AG-12 manifest immutability | OK | Manifest row count 24, row-dump hash and DDL hash all byte-identical — evaluator re-derived both |
| AG-13 system-vs-market separation | OK | No vocabulary surface touched |
| AG-14 no Tapeology coupling | OK | No import, call or write |
| AG-15 no outcome-tuned selection | OK | No threshold or rule changed |
| AG-16 cohorts are not controls | OK | No cohort surface touched |
| AG-17 repair never rewrites provenance | OK | No manifest, provider row or incident-evidence file touched; `git status --porcelain` returns **0 lines** on `runs/goal-market-compass-iter-9/` through `-iter-15/` |
| AG-18 authorized migration preserves everything | OK | No schema migration ran; manifest DDL hash unchanged |

**No critical violation. Ledger: 7 total, 1 unresolved (the AG-8 minor above).**

## Findings The Owner Must Carry Forward

1. **The safety catch is switched off against the real database (headline).** Confirmed by the
   evaluator's own grep and code reading, not taken from the audit.
   `register_j11_incident_boundary` has **no production caller** — `grep -rn
   register_j11_incident_boundary apps/backend --include=*.py` returns only its own definition, its
   own tests, and two docstrings. The `maintenance_boundaries` table does not exist in the live
   file at all (live schema still exactly 24 tables). And `evaluate_boundary_for_date` returns
   `blocked=False` when that table is empty (`j11_preboot_guard.py:143-145`). So starting the
   backend today would resolve the latest price date to 2026-08-12, sail past the catch, and write
   a `ScannerRun` onto a day deliberately held at zero.
   **Adjudication (asked for by the coordinator):** the ruling's literal test — "proven on
   disposable test state" — **is met**, and the catch is genuinely reusable and state-driven (its
   core check contains no AVB-specific or date-specific condition; the date list comes from the
   canonical `INCIDENT_DATES` only inside the separate registration helper). But that clause is a
   **necessary** condition for lifting isolation, not a sufficient one. Reading it as sufficient
   would let a catch that is inert in production unlock booting the live backend, which would
   immediately cause the very write the ruling forbids. Fail-closed reading: **maintenance
   isolation stays ACTIVE and the ruling's precondition for resuming application lanes is NOT
   satisfied.** This is fairly described as a scope collision rather than an oversight — arming
   the catch needs a live write, and this iteration was authorized for exactly two volume cells.
   **Precise scope of the danger:** the window is *now until Stage D completes*. Stage D itself is
   not endangered (it runs as a controlled writer script, not a booted service), and once Stage D
   refills the eleven days the boot path becomes safe again on its own, because `run_scan` is
   create-once.
2. **The recorded AVB label is AVB-B; the honest label is AVB-A.** Confirmed by the evaluator's own
   arithmetic. `run_j11_iter16_stage_d_readiness.py:247-248` calls the decision-impact traces
   **without** `volume_override`, so after the correction the counterfactual became provider-scale
   close × Trendora-scale volume — a hybrid that matches no real state. Evaluator's own recompute:
   A/B is exactly `2.7930001226` on both dates as run, versus `1.0000002382` (08-11) and
   `1.0000001337` (08-12) with the fetched volume supplied. So the recorded "material signals"
   (1 other ticker on 08-11, 11 on 08-12) are a scale artifact, and the dev handoff's claim that
   correcting AVB's volume measurably shifts other tickers' percentiles **is not what was
   measured** — it must not be inherited. `READY: YES` is unaffected:
   `_AVB_READY_CLASSIFICATIONS = ("AVB-A", "AVB-B")` and `ready = preflight_passed and not
   avb_blocks` (`j11_stage_d.py:507,520`). AVB-B is the more conservative of the two labels, so the
   record errs safe.
3. **The re-run cannot disconfirm the correction.** Confirmed: the corrected dates hit the target
   volume ratio about 180× more tightly than any genuine calibration date (2.4e-07 and 1.3e-07 versus
   1.6e-05 to 5.9e-05). `READY: YES` therefore rests on the **pre-correction** evidence chain —
   iteration 15's genuine provider fetch, J-10's persisted bridge factor, and the untouched
   calibration window — not on the post-correction re-classification. That chain is sound. The
   re-run is **not** independent corroboration and must not be read as one. Accepted as reasonable:
   the owner authorized exactly this transform, so a re-test of the same transform is tautological
   by construction; that is a labelling caution, not a defect.
4. **The certified-baseline gate genuinely moves.** The same fresh capture reports
   `daily_prices_fingerprint_unchanged: False` against the OLD baseline (one failing check, named)
   and `True` against the NEW one, with every other check `True` in both. This is iteration 13's
   lesson applied correctly — a gate that can fail, not a gate that always passes.
5. **Process hazard (auditor P1, evaluator-confirmed).** `runs/goal-market-compass-iter-16/review-packet.md:8`
   advertises "Files changed: 5. Shown in full: 5" while **7 new untracked files — 100% of the new
   code, including the live-write script and the entire guard — were invisible** to `git diff HEAD`.
   The evaluator's own `iter-diff.md` correctly says "Files changed: 12", so the evaluator lane's
   diff tool already unions untracked files while `build_review_packet` does not. Reviewer, auditor
   and coherence each caught it independently and read past the packet, so no harm landed.

## Next-Step Recommendation

**One instruction is needed from the owner, and one safety job should come first.**

**The safety job first, because it is the only thing that can go wrong on its own.** Ask for the
list of eleven damaged days to be written into the real database, so the safety catch that was
built this iteration actually switches on. Until that happens, anyone who starts the app for any
reason silently writes 12 August's results into the real database, and it cannot be undone. This
needs the owner's word because it means writing to the real database, and the only writes this
session has ever allowed were each granted one at a time, in writing. Nobody should read
"the guard is done" as "it is safe to start the app" — it is not, yet.

**Then the decision.** Pick one:

- **(a)** Instruct the engine to run Stage D — rebuild the eleven damaged days — and `--resume`.
- **(b)** Order a small, non-destructive tidy-up run first (see the three riders below), then decide.
- **(c)** Change the plan in `docs/goal.md`.

**Three small riders for whichever run happens next, none of which changes the readiness answer:**
1. Re-run the readiness check with the volume figure supplied to the comparison
   (`volume_override={date: provider_volume}` at `run_j11_iter16_stage_d_readiness.py:247-248`), so
   the recorded label becomes the honest AVB-A and the unsupported sentence about other companies
   shifting is removed from the record.
2. Fix the one-line unbounded table read at `apps/backend/app/engine/j11_preboot_guard.py:143`, since
   it now sits on the path every page's data depends on.
3. Add a test named for the real situation — "table exists, is empty, and the newest stored day is a
   damaged day" — so the gap in finding 1 can never hide behind a test called "the common no-incident
   case" again.

**Two mechanical items.** This iteration's new code, tests and evidence are still untracked in git at
the time of scoring (`runs/goal-market-compass-iter-16/` and all 7 new source files); confirm they
reach version control, as iterations 13-15 eventually did. And `build_review_packet` should include
untracked files, or at least name them as an exclusion.

**Five older owner questions remain open and non-blocking, unchanged:** whether 3.44 GB is acceptable
for J-09 "The backend fits the host"; J-06's "underlying run unavailable" wording; the rewording of
J-01's first two test steps; whether an empty "next-session focus" is acceptable; whether MNST joins
the recovery list. **Two standing framework notes, unchanged:** the defect that once let a forbidden
test lane run is still unfixed in `scripts/automation/` — eight iterations running have avoided it
with the maintenance-isolation contract rather than curing it; and `goal_gate.py`'s
duplicate-journey-heading defect is still unfixed and must be closed before any GOAL_ACHIEVED
certification.

**In one sentence:** switch the new safety catch on against the real database first, then tell the
engine whether to rebuild the eleven damaged days.

## Halt Justification

**Why halt when nothing is broken?** Because every road forward belongs to the owner. The owner's
own words end this step: "Even if the subsequent readiness evaluation returns `J-11 STAGE D READY:
YES`, STOP for owner review. Stage D is NOT authorized by this ruling and requires a separate
explicit owner instruction." The engine reached that exact stopping point and stopped. The only
remaining work on this repair's critical path is the rebuild of the eleven days, which is forbidden
without a fresh instruction, and the goal file shuts every other lane until this repair's last step
passes. A "keep going" verdict would let the engine plan the one step nobody has authorized.

The second road is owner-owned too. Switching the new safety catch on means writing to the real
database — creating a table and one row — which is outside the two-cell permission this iteration
was given. Every live write in this session has been granted separately and in writing.

**Halting is also the safer choice here.** A stopped engine starts no backend, and starting the
backend is precisely the accident that is currently unguarded.

**Why not REGRESSION?** Nothing that worked stopped working. No journey was tested, so none could
fail. Outside the two authorized volume cells, not one value in the 3.31 million-row price table
moved — I re-hashed every row myself to check. No critical rule was broken. The only ledger entry
this iteration is a minor one, recorded openly.

**Why not CONTINUE?** Real work exists that does not need the owner — the three riders above — but
none of it can change the readiness answer, and continuing would put the planner one step from the
forbidden rebuild. The one item that genuinely matters operationally, arming the safety catch, is
the owner's to authorize.

**Why not ESCALATE?** This run already used the careful full depth, and the careful depth is exactly
what found the hole in the safety catch.

**Note for the record.** This is the seventh iteration in a row where the independent auditor found
something the developer, the reviewer and the quality check all missed — and this time all three
lanes described the boot path as protected when it is not.
