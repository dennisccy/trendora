# Iteration 42 Evaluation

**Verdict:** REGRESSION
**Depth Recommendation For Next Iteration:** full

## Summary

The tool fix this iteration was built to make worked, and the first thing it found is bad news. Until
now, when the team picked a journey to work on, that journey stopped being checked. This iteration
closed that hole. The moment the checks ran, two journeys came back broken — and one of them,
J-05 "Aggregates are precomputed at ingest", was last checked as working three rounds ago.

What a user would see right now: you ask the app to load one day of history, it says "started", and
then nothing happens — no progress, no error, no result, forever. I confirmed this myself in the
server log: the job was accepted, asked about 290 times, and its worker never started once. A second
job on a different day did the same thing. Separately, during a heavy background calculation the
whole backend ran out of memory and fell over: the health check itself returned an error four times
and then stopped answering, and the Backtest and Data pages showed "Backend unavailable".

The six other journeys were all re-checked and passed, with dated pictures I opened. But they were
photographed a few minutes BEFORE the crash, in the same run. I am halting because the running app is
now in a worse state than the last state we confirmed good, and the main cause is a memory limit the
owner alone is allowed to change.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | reports/qa/goal-ops-hardening-iter-42-evidence/J-01-verify.png (opened; regime 75.20 = 35.00+17.21+14.75+8.24+0.00, re-added by me) |
| J-03 No per-run range cap | passing | passing | reports/qa/goal-ops-hardening-iter-42-evidence/J-03-verify.png |
| J-04 Non-blocking boot with visible status | passing | passing | reports/qa/goal-ops-hardening-iter-42-evidence/J-04-verify.png |
| J-05 Aggregates are precomputed at ingest, never on the fly | unknown (passing at iter-39) | **regressed** | reports/qa/goal-ops-hardening-iter-42-evidence/UT-J-05-fail.png (opened — a completely blank page); merged row FAIL in reports/phase-goal-ops-hardening-iter-42-ui-test-results.md; logs/backend.log:152717 (job POST 200) → :154483 (290th poll, no worker ever started) |
| J-06 Pages load only what they need | passing | passing | reports/qa/goal-ops-hardening-iter-42-evidence/J-06-verify.png |
| J-07 Heavy aggregates never take the service down | partial | **failing** | reports/qa/goal-ops-hardening-iter-42-evidence/UT-J-07-fail.png (opened — /backtest shows "Backend unavailable"); logs/backend.log:153050-153075 (`RuntimeError: can't start new thread` → `GET /api/health 500`); :154035-154049 (MemoryError under `compute_forward_aggregates`) |
| J-08 Backtest evidence serves from storage only | passing | passing | reports/qa/goal-ops-hardening-iter-42-evidence/J-08-verify.png |
| J-09 The backend discloses its own background-compute activity | passing | passing | reports/qa/goal-ops-hardening-iter-42-evidence/J-09-verify.png (opened; green "background compute running (1)" chip) |

Deferred (`DEFERRED-BUDGET`): none. `browser-infra.json`: absent. `journeys-changed.md`: absent — all
8 `spec_hash` values match `goal_gate.py hash-journeys docs/goal.md`, so no goal-edit drift.

Spot-checks (methodology A.4): J-01 and J-09. Both corroborate their recorded rows; neither
contradicts, so no widening was needed. All six replay screenshots are dated 07:32-07:34 local and
were written sequentially by a live run against backend PID 2451515 (started 07:20:12, running this
iteration's `prices.py`).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials (AG-7) | OK | `scan-report.md` CLEAN over the product diff (tracked + 1 untracked). No new config/env file in the changed-file list; both bench scripts read only the local seed DB. |
| Paid / external SaaS (AG-9) | OK | `git status --porcelain` over `*requirements*.txt`, `*pyproject.toml`, `*package.json` is EMPTY — no manifest changed. New imports are stdlib (`array`, `math`). Both measurement scripts are read-only local SELECTs; no network call added. |
| License changes | OK | No `LICENSE*` path in the diff; `scan-report.md` reports no license findings. |
| Fabricated / substituted data (AG-3) | OK | I re-added J-01's regime components on the frame itself (35.00+17.21+14.75+8.24+0.00 = 75.20, matching the headline). UT-J-07-fail.png is the product explicitly refusing to fabricate: "No figures are shown rather than fabricated values." Byte-identity of served values is proven by an unmodified fixture harness and re-confirmed by the auditor. |
| AG-1 / AG-2 / AG-4 / AG-6 (proven-language, decision-quality, referee) | OK | No evidence claim, no displayed-value change, no new user-facing surface (`Frontend Present: no`; zero `apps/frontend/` hunks). |
| AG-5 (no lookahead) | OK | `_BarCache`'s slice semantics unchanged; byte-identity tests cover both the filtered-eager and lazy-fallback paths. |
| AG-10 (host resource ceiling) | OK — no violation trigger | I ran `git diff` over `scripts/dev.sh`, `scripts/start-backend.sh`, `scripts/start-frontend.sh` and `project-extensions/host-guard/host-guard.env`: **0 lines**. `config.yaml` byte-unchanged, so `memory_cap_mb: 6144` / `malloc_arena_max: 2` remain the committed caps. Observation only (audit B4): both dev bench scripts ran as bare `.venv/bin/python`, matching the precedent iter-41's audit accepted; the auditor's own re-measurement replicated the caps explicitly. |
| **AG-8 (data-shape/scale resilience)** | **VIOLATED — demonstrated live, three findings** | **(a) iter-42/ae, open:** the service exhausted its memory ceiling and went down. I read the traceback myself at `logs/backend.log:153050-153075` and counted 4 × `GET /api/health` 500 and 2 × `/api/backtest` 500; MemoryError at `:154035-154049`; 5 consecutive HTTP-000 timeouts per the merged row; `/backtest` and `/data` rendered "Backend unavailable". The UI half of AG-8 (graceful degradation, no blank error page) is SATISFIED; the "never exhaust a service's memory" half is not. **Pre-existing, not introduced here** — I dated every MemoryError in the log: 7,004 across ten days, including 26 on 07-30 and four on 07-31 at 00:08/00:11/01:44/01:54, hours before this iteration's `prices.py` existed. **(b) iter-42/ac, open:** the shipped `prefill` filter is a **+5.1% peak-memory regression** (698,400 vs 664,328 kB VmPeak), not the recorded 2.5% reduction — audit B2, record corrected in three places. **(c) iter-42/ad, resolved in-audit:** the filter made a half-published lazy load reachable, raising `KeyError` from `bars_asof` in the parallel backfill (`prices.py:362-363`/`:420-421`); fixed at `:364-377`/`:422-427` with a failing-then-passing regression test — but AFTER browser QA ran. |
| Severity call | all three recorded `minor` | My agent file's critical class is secrets / unapproved paid dependency / license / backdoor / fabricated data — none of these is that, and this session has scored the AG-8 family `minor` for 13 iterations. I considered `critical` for (a) and record that I decided against it on those stated grounds. The verdict is REGRESSION on journey evidence regardless, so nothing is softened by this classification. Ledger now: **43 total, 14 unresolved, 0 critical.** |

Other gates: `scan-report.md` CLEAN · `coherence.md` **COHERENCE-PASS** (no blocking violations; two
advisory notes) · review **PASS** · QA **PASS** · audit **PASS_WITH_GAPS** · ux-regression
**UX-REGRESSION-SKIPPED** (budget-shed, credited nothing) · closure **CLOSURE-PASS**.

Resolved this iteration: **iter-41/z** (the target-journey verification hole — closed and *proved* by
this iteration's own FAIL headline) and **iter-41/ab** (the QA report's inaccurate AG-8 row — now
reads "not addressed — measured as a net memory REGRESSION"). Twelve carried items each received an
ITER-42 UPDATE recording what I verified rather than inherited.

## Next-Step Recommendation

Do not start another build round yet. One decision belongs to the owner and it blocks everything
else.

**The decision.** The app is asked to work with 30 years of prices (about 3.3 million rows) while the
backend is held to a 6 GB memory limit. Those two numbers no longer fit together: the heavy
background calculation runs out of room and takes the whole service down. No agent is allowed to fix
this by raising the limit — the goal file says in its own words that this limit is a physical
protection for the machine, added after two hardware crashes. So the owner needs to pick one of
three:

1. Raise the memory limit, if the machine can now safely take it.
2. Use less history (a shorter price basis) so the work fits inside the current limit.
3. Change the goal so the heavy calculation is allowed to run in smaller pieces over more time,
   and accept that it will take longer.

**Then, in order, once that is settled:**

1. Fix the stuck job. When a background job is accepted but cannot actually start, the app must say
   so — right now it says "running" forever and shows nothing. This breaks the goal's own promise of
   "no silent zero-work jobs" (J-05 "Aggregates are precomputed at ingest").
2. Decide what to do with this round's memory change to the price cache. Measured properly it made
   memory 5.1% worse, not better. The three options the auditor lists are: keep it, undo it, or
   finish it. Undoing it is the simplest and also removes the new race condition risk it created.
3. Re-run all eight journey checks after the memory decision lands. The six that passed this round
   were photographed minutes before the crash, so they show the code works on a healthy server, not
   that the server stays healthy.
4. Look at the slow read path found this round: reading a symbol's prices is now 70-80 times slower
   per call than before the previous round's change. Nobody had measured this until now.
5. Carried and untouched: the boot warm-up failure (twelve rounds), the Regime Lab slow page (deferred
   seven times), and the small hygiene items already written down in the ledger.

**Praise where it is due:** the one thing this round set out to build works, and works well. Choosing
a journey to improve no longer switches its safety check off. It found a real fault on its very first
run.

**One sentence for the owner:** please choose between raising the memory limit, shortening the price
history, or relaxing the goal's timing promise — then the team can fix the stuck job and re-check
everything.

## Halt Justification

I am halting with REGRESSION for two reasons.

**First, a journey that we had confirmed working is now confirmed broken.** J-05 "Aggregates are
precomputed at ingest" was checked and passing three rounds ago. It was then not checked at all for
two rounds — recorded as "unknown", which the earlier evaluator wrote down explicitly as "not
tested", never as "broken". This round it was checked and it failed, twice, on two different dates.
The journey record's own rule for this situation says: a journey that was passing in an earlier round
and is now failing is *regressed*. And the rule I work to says a regressed journey means this
verdict. I am not stretching a rule to reach a dramatic answer — this is the plain reading, and the
underlying facts are worse than the label: a person using the app cannot load a day of history at
all.

**Second, the fix needs a person, not another round.** The service ran out of memory and stopped
answering. The memory limit that it hit is one the goal file forbids any agent from changing, in
capital letters, because two real hardware crashes led to it being set. The amount of history the app
loads is the owner's choice. Changing the goal's wording is the owner's choice. Eight rounds have now
tried to squeeze this calculation inside the current limit and eight have fallen short — this round's
attempt actually moved the number backwards. Letting a ninth round start without the owner choosing
the envelope would repeat work we already know does not fit.

I considered STALLED and rejected it: real agent work does remain (make the stuck job report itself
honestly, undo or finish the cache change, bound the heavy calculation itself), so it is not true
that *every* path needs a person. I considered ESCALATE and rejected it: this round already ran at
full depth, and continuing would send a ninth attempt at a wall the owner has to move first. The
halt is the honest answer.

To resume after deciding: `--acknowledge-regression`.
