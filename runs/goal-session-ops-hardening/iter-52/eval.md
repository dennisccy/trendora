# Iteration 52 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This round did the hardest thing well and then could not prove it. The team found the real
reason the app stops answering during a data job — two pieces of work the computer cannot be
interrupted during — and fixed both, and the fix is honest and well tested. But the eight
journey checks ran *before* that fix was written, so the only independent check of the round
measured software that no longer exists, and it failed the two journeys the round existed to
close. The pipeline noticed this itself and stopped: the run is marked "blocked", waiting for
the checks to be run again. Nothing on the scoreboard moved. Four journeys still pass, four
are still part-way, none got worse. Two good things did happen: all four part-way journeys got
a real check for the first time in three rounds, and the picture that has been owed since round
50 was finally taken.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | `reports/qa/goal-ops-hardening-iter-52-evidence/J-01-verify.png` (opened: immutable snapshot as of 2026-05-29, regime 75.2, Risk-on, provider seed) + DB run 329 read by me: `dates_total=19`, `already_snapshotted=19`, `calendar_days=28`, `non_trading_days=9` |
| J-03 No per-run range cap | passing | passing | `reports/qa/goal-ops-hardening-iter-52-evidence/J-03-verify.png` + DB run 331 read by me: `dates_total=283` over `calendar_days=412` — far past the retired 370-day cap |
| J-04 Non-blocking boot with visible status | partial (DEFERRED-BUDGET x2) | partial — **really tested this round** | `reports/phase-goal-ops-hardening-iter-52-ui-test-results.md:31` (UT-J-04, `2 passed in 5.04s`: first 200 in **1.73s**, `readiness='initializing'`, `warmup={done:89,total:89}`; SIGKILL → unreachable → restart → same run row `status='interrupted'`, progress preserved at 2/5) + `reports/perf-budgets.md` Addendum 14 (live boot **2.2s**). **No screenshot exists**; steps 3/4's badge-and-banner half and step 5's logfile were not observed |
| J-05 Aggregates are precomputed at ingest, never on the fly | partial | partial | `reports/qa/goal-ops-hardening-iter-52-evidence/UT-J-05-scanner-run-result.png` (opened: "Immutable snapshot — as of 2005-05-24 · Scanned 2026-08-08 00:00:10 · provider seed", regime 74.36) + DB run 332 read by me (5 snapshots, all 8 aggregate categories). **Step 4 fails**: 47/1007 unanswered health polls (`ui-test-results.md:32`), 2/1285 on the shipped tree (`perf-budgets.md` Addendum 14) |
| J-06 Pages load only what they need | partial | partial | `reports/qa/goal-ops-hardening-iter-52-evidence/J-06-verify.png` (opened) + `ui-test-results.md:33` (J-06.json replayed 1/1, 11 pages — first execution in 3 rounds). **Step 1 is a shell-text pass on the Regime Lab page**, whose own data call raised MemoryError twice in that window (`logs/backend.log:212191,212240,212296`); step 2 records 1 of 11 pages; step 3's code audit absent from the dev handoff |
| J-07 Heavy aggregates never take the service down | partial | partial | `reports/perf-budgets.md` Addendum 14: step 3 **MET** (VmPeak 4,886.2 MB, 40.4% margin under concurrency), step 4 **MET for the first time this session** (TC-6 live re-run on the shipped tree, `1 passed in 1076.19s`; I counted its 110 injected MemoryErrors in `logs/backend.log`). **Step 2 fails**: 2/1285 non-answers, 34/1283 polls over 2.0s, worst 4.901s |
| J-08 Backtest evidence serves from storage only | passing | passing | `reports/qa/goal-ops-hardening-iter-52-evidence/J-08-verify.png` (UT-J-08 replay PASS) |
| J-09 The backend discloses its own background-compute activity | passing | passing | `reports/qa/goal-ops-hardening-iter-52-evidence/J-09-verify.png` (opened: top-bar badge reads **"background compute running (1)"**) |

No `browser-infra.json`, no `journeys-changed.md`, no `DEFERRED-BUDGET` row. All eight
`spec_hash`es match `goal_gate hash-journeys` run by me — zero goal-edit drift.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 / AG-4 / AG-6 (proven-language, referee) | OK | No evidence-claim language added; the diff is 3 engine modules + 4 test modules. `ui-test-results.md:27` shows the "Not yet proven" badges still rendering as the honest `data-proven="false"` state |
| AG-2 (decision-quality only) | OK | No return promise, price target or order path anywhere in the diff |
| AG-3 (displayed numbers correct) | OK | Factor Lab: 11 real rows, rank-IC −0.01, N=1,265,499 (`ui-test-results.md:27`); Factor Combination percentages byte-identical to iter-51's baseline (`:28`). Byte-identity of the new chunked sort proved by object-identity tests AND re-derived independently by the auditor at 260K rows. UT-03's "Snapshot dates 2921" cross-checks against the DB's 2923 after two later runs |
| AG-5 (determinism / no-lookahead) | OK | Scheduling-only change; TC-4 asserts byte-identity by object identity, not equality |
| AG-7 (no hard-coded credentials) | OK | `iter-52/scan-report.md` = **CLEAN**; audit's own `git diff apps/backend \| grep -Ei "api[_-]?key\|secret\|token\|password\|bearer"` = no hits; no new config/env file in the diff |
| AG-8 (resilience, no unbounded loads) | **VIOLATION — minor, pre-existing** | `/research/regime-lab`'s data call raises MemoryError on the live request path (`logs/backend.log:212191,212240,212296`, frames `compute_regime_lab` → `_regime_lab_members_by_horizon`), aborting the response with no HTTP status. NOT introduced here — that function is absent from the 13-file diff and the same frame appears on 2026-08-04. Filed `iter-52/cn`. MemoryError accounting: total 8,085 vs iter-51's 7,862 = +223, of which **220 are the developer's own deliberate TC-6 fault injections** (55 entries x 2 lines x 2 runs) and exactly **3 are real** — all three this Regime Lab frame |
| AG-9 (offline-deterministic ingest) | OK | I read every run created this round in sqlite: ids **326-334, all `provider='seed'`**; Addendum 14's drill record reads `"source": null` |
| AG-10 (host resource ceiling) | OK | I ran `git diff --stat` AND `git status --porcelain` over `config.yaml`, `host-guard.env`, `start-backend.sh`, `dev.sh`, `start-frontend.sh` myself — **both EMPTY**; `config.yaml:1363-1364` still reads 8192 / 2 |
| Verification contract (TC-9, lane runs last) | **VIOLATION — minor** | `iter-52/cj`. Lane results 01:41:48; `research.py` 02:39:48 (the actual fix) and 03:55:25 (comments). Sixth breach in seven rounds |
| Definition-of-Done honesty | **VIOLATION — minor** | `iter-52/ck`. "TC-1 through TC-12 all pass" is false (TC-2/TC-3/TC-5/TC-9). Mitigated: Addendum 14 says so plainly and the review recorded `definition_of_done: partial`, not "complete" |
| Golden-script quality | **VIOLATION — minor** | `iter-52/cl`. J-06.json step 11 asserts only the page heading |
| Walkthrough capture | **VIOLATION — minor** | `iter-52/cm`. Demo verdict SKIPPED, empty step table, `demo JSON parse error`. Capture-only |

Ledger after this round: **102 total, 44 unresolved, 0 unresolved critical.** Three prior
entries CLOSED (iter-50/ca, iter-51/cg, iter-51/ch) — all four target journeys produced real
executed rows, and I md5'd the evidence directory: 13 files, 13 unique hashes, zero copied
from iter-51.

Other lane verdicts: coherence **COHERENCE-WARN** (zero blocking, one advisory — the blueprint's
Notes describe only the first pass, not the sort/GC fix that actually shipped); review
**PASS_WITH_NOTES** (1 MINOR, 1 NOTE); audit **FAIL** (B1 CRITICAL = the TC-9 breach; B2/B3/B4
subsequently closed by the audit-fix pass; B5/B6 documentation); QA **FAIL** (hard gate);
browser QA **FAIL** (14/17, 2 FAIL, 1 SKIPPED); deterministic replay **PASS 4/4**; demo
**SKIPPED**; ux-regression **SKIPPED** (wall-clock trim). `status.json` = **blocked** /
`audit_qa_failed` / `browser_checks_run: false`.

## Next-Step Recommendation

FULL depth (required by ESCALATE). Please give the next round this order.

1. **Before writing any code, run the eight journey checks again.** The app's code has not
   been touched since 03:55 and the run is already stopped waiting for exactly this. The
   checks that were run this round tested the app as it was *before* the repair was written,
   so they cannot tell us whether the repair worked. Re-running them costs no new code and
   cannot break anything. This is the single most valuable action available.
2. **Then finish the repair in the two places it was never applied.** The app now answers
   reliably while the heaviest step of a data job runs, but it still went briefly silent twice
   during two other steps of the same job — the step that refreshes coverage and the step that
   works out the market phase. Those two steps never received the treatment that fixed the
   heaviest one. Apply the same treatment there.
3. **Then run the eight checks one final time, and change nothing afterwards.** This rule has
   now been broken in six of the last seven rounds, and it keeps breaking for the same
   structural reason: the checks are scheduled before the final review, so any repair the
   review asks for lands after them. Moving the checks to run after the final review would fix
   it once, instead of asking people to remember it every round.
4. **Look at the Regime Lab page.** During this round's own checking, that page's data ran out
   of memory and returned nothing at all — twice. It has been on the "later" list for
   seventeen rounds. It is now failing in front of the checks, and the check for it passes
   anyway because it only looks for the page title. Two things to do: make the check look at
   the page's actual data, and find out why the data runs out of memory.
5. SMALL AND ALREADY WRITTEN DOWN: the total time for a data job's finishing work went 5%
   over its agreed limit when the app was also busy (1,261 seconds against 1,200); a single
   heavy research request can still wait more than ten minutes during a data job; the health
   check still does about 0.14 seconds of real database work every time; a second overlapping
   request can quietly cancel the new memory-pause protection.
6. CARRIED, untouched: iter-29/b + the badge wording after a permanently failed warm-up (25th
   round unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u;
   iter-46/az; iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj. Deferred an
   EIGHTEENTH time: iter-33/g, the Regime Lab — though item 4 above now touches it.
7. CAPTURE ONLY, never a round's goal: the walkthrough recording failed to start at all this
   round (a file-format error, not a product fault) and J-07's walkthrough is 22 rounds
   unrecorded; one screenshot came back blank again. Also worth one line: the design record
   still describes only the first attempt at this round's fix, not the repair that actually
   shipped.
8. OWNER: two decisions and three facts. The decisions — (a) may a future round move the heavy
   calculation into a separate process? Asked at rounds 50 and 51, still unanswered, and it is
   still the only way to guarantee the app never pauses. (b) Is the 20-minute limit on a data
   job's finishing work meant to hold when the app is also serving people, or only when it is
   idle? It was met when idle and missed by 5% when busy. (The older question from round 50,
   about the two rules that cannot both hold, is still open too.) The facts — the page that
   used to take twelve minutes to open now answers in hundredths of a second, and the memory
   it uses fell to about 4.9 GB against your 8 GB ceiling; adding an old day of history
   succeeded every time it was tried, and for the first time the app was proven to survive
   running out of memory mid-job without needing a restart; and the checks that would show all
   this on the scoreboard were run too early to count, so the scoreboard did not move.
