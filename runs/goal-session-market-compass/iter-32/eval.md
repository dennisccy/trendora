# Iteration 32 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The one job asked for was done properly, and I checked it myself rather than trusting the
write-ups. The backend's memory use was measured again on a fresh start, every reading was saved
to a file that survives, and the honest answer is that it is still too big: 3,038,684 kB against
a 2,621,440 kB goal, 15.9 percent over. Nobody widened the goal or rounded the number. All ten
working journeys were re-run and all ten still pass, twice over. But I found something in the raw
readings that changes what should happen next: the big number is a five-second spike while the
backend is still starting up. Once it is serving, it holds about a third of that. And the one
remaining way to shrink that spike is already written down in the owner's own binding rules as
work to be done — so this is not, yet, a decision only the owner can make.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels are honest | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-32-evidence/audit-rerun/J-01-verify.png |
| J-02 What changed since previous session | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-32-evidence/audit-rerun/J-02-verify.png |
| J-03 Plain-English summary with cited facts | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-32-evidence/audit-rerun/J-03-verify.png |
| J-04 Candidate explains why and why-not | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-32-evidence/audit-rerun/J-04-verify.png (opened — capture defect, 14th round) |
| J-05 Each close freezes one manifest | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-32-evidence/audit-rerun/J-05-verify.png |
| J-06 A frozen manifest never changes | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-32-evidence/audit-rerun/J-06-verify.png + byte-identity cmp 6/6 |
| J-07 Today page ten-second read | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-32-evidence/audit-rerun/J-07-verify.png (opened — spot-check) |
| J-08 Market page moves over intact | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-32-evidence/audit-rerun/J-08-verify.png |
| J-09 Backend fits the host | partial | **partial** (targeted; step 2 assertion fails) | runs/goal-market-compass-iter-32/j09-vmpeak-samples.csv + reports/perf-budgets.md Addendum 43 |
| J-10 Bounded recovery of two trading days | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-32-evidence/audit-rerun/J-10-verify.png |
| J-11 Incident-bounded regeneration | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-32-evidence/audit-rerun/J-11-verify.png |

Zero status changes. Newly passing: none. Newly failing: none. Regressed: none.

**Where the journey evidence came from (important).** The browser-QA lane recorded 0/11 with every
row `SKIP` — `reports/phase-goal-market-compass-iter-32-ui-test-results.md` says the frontend and
backend were both unreachable at its dispatch (`curl` → `000`). Its `**Reason:**` line names
"frontend not running", NOT maintenance isolation, so that carve-out does not apply and no journey
may rest on it. There is no `browser-infra.json` token either. What saves the round is that the
deterministic replay lane ran the full ten-journey set TWICE with real screenshots — once by the
developer (04:15-04:16 local) and once by the auditor (05:18-05:19) — 10/10 PASS both times, and I
opened those images myself. The replay lane's PASS rows simply never got merged into the browser-QA
file; the merged file itself defers to the replay lane in writing.

**Spot-checks I opened (methodology A.4).** All ten stable journeys sit inside the replay set, so
both spot-checks come from it. `audit-rerun/J-07-verify.png` at 2026-08-03 reads regime 66.07
improving / severity 29.35 improving / breadth 45.1% little changed, with the Summary agreeing
("+4.7 regime-score points") — consistent with iter-29 and iter-31. `audit-rerun/J-04-verify.png`
is AGAIN the 2026-03-30 top-of-page viewport that stops above the candidate card, so
`evidence_makeup: true` is KEPT for the fourteenth iteration running. Neither spot-check
contradicts its recorded status, so no widening was needed.

**Golden-script hygiene: clean for the first time in four rounds.** I read the mtimes of all ten
goldens myself. Every one predates this iteration's 04:03 start (`J-02.json` 03:35:14, `J-03.json`
03:35:18, `J-11.json` 01:51:59, the rest older). No golden was written or rewritten after the
replay lane this round. `J-02.json` and `J-03.json` — rewritten at iter-31 and never executed —
executed twice this round and passed both times. I also read their assertions directly: they are
exact-string checks on rendered values (`"vs 2026-08-11 (1 day ago)"`, `"0.26 < 5.00"`,
`"73.18"`, the four-sentence summary, the earliest-session and retrospective stamps), not page-load
checks. That is real coverage.

### J-09 in detail — what I verified myself

Satisfied and independently re-derived by me:
- `config.yaml` `cache_size: -65536`, `pool_size: 24`, `max_overflow: 44`; `git diff -- config.yaml`
  empty; `git diff HEAD -- apps config.yaml scripts project-extensions` empty. HOST-GUARD markers
  present in both launch scripts; `project-extensions/host-guard/host-guard.env` untouched
  (mtime 2026-08-19).
- `reports/perf-budgets.md` Addendum 43 appended: 144 insertions, **0 deletions**.
- Bursts: `concurrent64-burst-results.jsonl` 320/320 HTTP 200, `replica-burst-results.jsonl`
  482/482 HTTP 200, all against `http://localhost:8255`, zero errors. The measurement instance's
  log segment has 940 request lines, all 200, and **zero `QueuePool` lines**.
- Byte identity: I ran `cmp` over all nine before/after pairs. The six compass and dashboard pairs
  are byte-identical. The three health pairs differ in exactly one field, `stale_for_s`
  (0.243… → 0.446…), a liveness timer, not a served value.
- Raw capture: 80 rows, single pid 1724495, window 2026-09-01T03:19:41Z → 03:26:17Z, max
  `VmPeak_kB` = **3,038,684**, readiness first `ready` at t+25.97s.

Not satisfied: the ≤ 2,621,440 kB bar. 3,038,684 kB is **+417,244 kB (+15.9%)** over.

**The finding that changes the next step.** VmPeak is a boot transient, not the serving footprint.
From the same CSV: VmSize climbs to 3,038,684 kB at **t+15.94s while still `initializing`**, then
drops to 1,750,504 kB at t+20.94s, and finishes the window at 1,298,796 kB virtual / **725,856 kB
resident**. So a roughly 1.29 GB block is taken for about five seconds during start-up and then
given back. `apps/backend/app/engine/warmup.py:351` opens `with bar_cache(session):` around the
cold cadence-date computation, which is the allocation of that shape and lifetime. `docs/goal.md`
Constraints (c) already directs that this cache family be "re-bounded to a configured memory
budget (AG-8 restored)", and `docs/goal.md:2396-2400` records the whole Host-resource-fit block as
owner-authored **binding** work that "rides the nearest applicable slices", noting that (a) and (b)
already landed at iter-5. That makes the remaining lever scheduled developer work, not a pending
owner permission — which is why this is CONTINUE and not STALLED.

**Host quietness was not achieved, and it does not explain the miss.** The developer disclosed
up front that a sibling `tensteps` goal-mode session was dispatching throughout. I confirmed it
independently from `~/.cache/iad/host-guard/events.jsonl`: a `tensteps` iteration-summarizer ran
04:18:47-04:23:53 and a goal-decomposer 04:18:48-04:28:01, both overlapping the 04:19:41-04:26:17
local measurement window. But VmPeak is a per-process high-water mark, `MemAvailable` held
19-20 GB, swap stayed at 0 B, and the value was identical across 77 of 80 samples. A neighbour
burning CPU cannot inflate another process's peak address space by 417 MB. Re-measuring again
would not close this gap.

## Anti-goal Check

The product diff this iteration is **EMPTY** (`iter-32/iter-diff.md`: "no changes";
`scan-report.md`: CLEAN). The only tracked change is `reports/perf-budgets.md` (+144/−0). Strongest
single fact, re-derived by me: **the database file was never written.**
`apps/backend/data/trendora.db` has mtime `2026-09-01 01:32`, which is BEFORE this iteration began
at 04:03, and the WAL is 0 bytes.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven/confident language | OK | Zero code change; no new claim surface. Byte-identity proves no served text moved. |
| AG-2 decision-quality only | OK | No new UI, no new copy. Screenshots I opened show "Research-only · decision support · no orders" intact. |
| AG-3 displayed numbers correct | OK | Zero engine change plus 6/6 byte-identical compass/dashboard payloads at the three authorized as-of values. Replay goldens assert exact rendered numbers and passed twice. |
| AG-4 no overfit edges | OK | No selection/referee code touched; diff empty. |
| AG-5 determinism / no-lookahead | OK | No scoring or ingest code touched; `MAX(daily_prices.date)` still 2026-08-12, `scanner_runs` still 3128 (re-derived read-only). |
| AG-6 referee gate | OK | No Evidence Claims introduced; gate passes automatically. |
| AG-7 no hard-coded credentials | OK | scan-report CLEAN. The scanner path-excludes `runs/`, so I read the two new scripts myself: `vmpeak_sampler.py` and `pool_pressure_burst.py` take their URL as a CLI argument, contain no keys/tokens/passwords, and use only `urllib` against localhost. |
| AG-8 data-shape/scale resilience | OK, with a note | No consumer widened. Related but not a violation: the ~1.29 GB unbounded boot allocation this iteration measured is the very thing Constraints (c) exists to bound — it is a pre-existing, already-known condition, not something introduced here. |
| AG-9 offline-deterministic ingest | OK | Every request in both burst JSONLs targets `http://localhost:8255`. No external host, no provider fetch, no ingest job. Database untouched (mtime proof above). |
| AG-10 host resource ceiling | OK | `git diff HEAD -- config.yaml scripts project-extensions` empty; `memory_cap_mb` 8192, `malloc_arena_max` 2, `pool_size` 24, `max_overflow` 44, `limit_concurrency` 64 all unchanged; both HOST-GUARD blocks present; backend launched only via `scripts/start-backend.sh`. No cap widened to make the number pass. |
| AG-11 no new composite number | OK | No new served field. |
| AG-12 manifest immutability | OK | Re-derived read-only AFTER every lane: 28 rows / 18 distinct `as_of` / max id 28, max `created_at` 2026-09-01 00:12:07 (predates this iteration), `state_band_json` non-null on exactly 2 rows, `prospective_eligible=1` on 0 rows. Nothing mutated, nothing minted — the DB file was never written at all. |
| AG-13 system-vs-market separation | OK | No UI change; readiness chrome unchanged in every screenshot I opened. |
| AG-14 no Tapeology coupling | OK | Grepped the two new scripts — no `tapeology` reference, no cross-project import or write. |
| AG-15 no outcome-tuned selection | OK | No selection rule or threshold touched; diff empty. |
| AG-16 cohorts are not controls | OK | No cohort code or data touched. |
| AG-17 repair never rewrites provenance | OK | No repair or restore ran. No `available_at_utc` moved (max still 2026-09-01 00:13:07, from iter-30). |
| AG-18 authorized manifest migration preserves everything | OK | No schema change; no migration ran; census identical before and after. |

**Ledger: 9 total, 0 unresolved — unchanged. No new entry this round.**

One thing I considered and did NOT log as a violation: the replay lane requested four `as_of`
values (`2026-03-30`, `2026-07-23`, `2026-08-03`, `2026-08-11`) outside the spec's authorized
three-value set. I re-derived the histogram from `logs/backend.log` myself and confirm 24 compass
GETs across 8 as-of forms on the 03:14:26Z instance and again on the audit's 04:17:28Z instance.
This is a spec self-contradiction (the auditor's B4: the same spec both mandates replaying those
goldens and forbids the calls those pages make), not an anti-goal breach: all four dates are
already among the 18 stored `as_of` values, `GET /api/compass` has no write path, and the census
is unchanged. Harm is nil.

## Pipeline honesty findings the owner should read

1. **Two gates signed off on a file that did not exist.** The deterministic replay lane was run
   without `--results`, so `reports/phase-goal-market-compass-iter-32-regression-replay-results.md`
   was never written. The reviewer (04:39) wrote "the replay results file shows 10/10 journeys
   PASS" and the QA report (04:47) marked it "✓ exists" — but the file's mtime is **05:19**, and
   it was created by the auditor's own re-run. I checked the timestamps myself. The claim was
   true; nobody had read it. This is the fifth consecutive round of the same defect family, which
   has now mutated from "a golden rewritten after the replay is not coverage" to "a replay with no
   surviving record".
2. **A true-sounding safety claim was scoped to the wrong process.** The dev handoff's "exactly 6
   compass calls this iteration" counted only the second backend instance. The auditor caught it
   and appended a correction to the handoff. `reports/perf-budgets.md` Addendum 43 still carries
   the same wrong sentence ("No `as_of` outside this 3-value set was requested at any point this
   iteration") and was NOT corrected — the safety conclusion it supports is nevertheless true, and
   I re-verified it from the database directly.
3. **Depth held at `full`, but coverage was partial.** `iter-32/depth-dispatched` reads `full`
   and the ninth demotion did not happen. However browser-QA produced zero executed rows (services
   down), the demo lane was SKIPPED (frontend never came up), and ux-regression was shed by the
   wall-clock trim. Reviewer, QA, coherence, closure and the independent auditor did run. Read this
   as "full dispatched, partially covered". For the twenty-third round running, a later lane found
   what the earlier ones missed — this time the auditor, on both items above.

Coherence: **COHERENCE-PASS** (deterministic zero-change pass — product diff empty). Deterministic
scan: CLEAN. Review: PASS. QA: PASS. Closure: CLOSURE-PASS. Audit: PASS_WITH_GAPS (B1, B2 fixed;
B3, B4, B5, B6, T1, T2). No `journeys-changed.md`, no `browser-infra.json`, no `DEFERRED-BUDGET`
rows, not maintenance isolation. All eleven `spec_hash` values are byte-identical to the recorded
ones — I ran `goal_gate.py hash-journeys` and compared every one.

## Next-Step Recommendation

**Do the one remaining memory fix, then measure again.** The next round should bound the
five-second start-up spike that the raw readings now pin down precisely: the backend takes about
1.29 GB while it warms up and gives it back straight away. Bounding that block to a size set in
`config.yaml` is exactly what the owner's own binding rule (c) already asks for, and rules (a) and
(b) from the same list were finished long ago. If bounding it would break correctness, the rule
itself says to stop and ask the owner rather than guess — follow that. Then re-run the same
measurement with the same saved-readings method and append one new dated entry beside the others.
Never move the 2.5 GB line to make it pass.

**Run it at full depth.** A later lane has now found what the earlier lanes missed for
twenty-three rounds running, and this next round changes real code in the part of the program that
uses the most memory, on the machine that a run of this system froze on 20 August 2026. Only the
owner may add `Depth enforcement: required`; standing guidance keeps `CHAIN_REQUIRE_FULL_DEPTH`
and `CHAIN_MAINTENANCE_ISOLATION` OFF.

**TWO OWNER DECISIONS, NEITHER BLOCKING.** (a) You can close J-09 today with one line if you want
to: the honest number is 2,967.5 MB at its worst moment, but while the program is actually serving
it holds only 725,856 kB, and two backends together sit far inside this machine — which is the
thing you originally asked for. If you accept that, J-09 passes as it stands and the whole goal is
finished. (b) If you would rather the next round did not touch the warm-up code at all, say so and
the answer to (a) becomes the only path.

**THREE REPAIR ITEMS THAT SHOULD RIDE ALONG, all mechanical.** (1) Always pass `--results <path>`
when running the replay lane, and make the lane refuse to report success when that file is missing
— that ends a defect family that is now five rounds old. (2) Bring the replay lane's real results
into the merged browser-QA file; this round the merged file said 0/11 skipped while the same ten
journeys had actually passed twice. (3) Correct the one wrong sentence in `perf-budgets.md`
Addendum 43 about which as-of dates were requested — the dev handoff was corrected, the report
was not. Also fix the next spec's own contradiction: it both requires replaying goldens that visit
certain dates and forbids visiting them.

**NINE CARRIED ITEMS, none blocking.** J-04's picture still needs re-taking to include the
candidate card (14th round owed — a fresh picture was taken this round and has the same framing
fault); J-02, J-03, J-05, J-06 and J-08 all still owe a recorded walkthrough and J-07's is only
four steps (passenger tasks, never an iteration goal); one test is red on three files untouched
since an old commit and should be fixed or formally waived; the "What changed" and "Leadership
rotation" lists still show identical rows; the iteration-23 throw-away copy (7.8 GB) may still be
deleted; `apps/frontend/.next-verify/` build cache is tracked in git; J-01's automatic re-check
still asserts far less than the journey claims; this round's bookkeeping again records
`browser_checks_run: false` although twenty pictures were taken; and the whole iteration is
uncommitted at scoring time — confirm it lands.

**FIVE OLDER OWNER QUESTIONS remain open and non-blocking:** J-06's "underlying run unavailable"
wording; J-01's first two test steps; whether an empty "next-session focus" is acceptable; whether
MNST joins the recovery list; and whether 12 August should keep showing its "rebuilt" note.
**ONE STANDING FRAMEWORK NOTE:** `goal_gate.py`'s duplicate-journey-heading defect is still unfixed
(this round's goal slice again lists J-10 twice) and must be closed before any GOAL_ACHIEVED
certification.
