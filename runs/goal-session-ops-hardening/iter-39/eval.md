# Iteration 39 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This was a good iteration and I want to say that before anything else. The team finally proved the
last open piece of J-07 "Heavy aggregates never take the service down": they made the memory failure
happen on purpose, inside the exact step the journey names, in a real running server, and the server
kept answering every single request while it happened. I checked those numbers myself in the live log
file, not in the report. Seven other journeys were re-checked against a live app and all seven passed
with real, different screenshots. But J-07 still cannot be called finished, and the reason comes from
this iteration's own honest testing: at a deliberately tightened memory limit the server stopped
answering for more than seven minutes, and the team found a place in the code that loads about 3.3
million rows of price data into memory at once. J-07's own wording says the app must never get stuck
like that, and must not have loads like that. So J-07 stays partly done for a fifth time, and the next
run must stay at full depth.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | reports/qa/goal-ops-hardening-iter-39-evidence/J-01-verify.png (replay PASS) |
| J-03 No per-run range cap | passing | passing | reports/qa/goal-ops-hardening-iter-39-evidence/J-03-verify.png (replay PASS) |
| J-04 Non-blocking boot with visible status | passing | passing | reports/qa/goal-ops-hardening-iter-39-evidence/J-04-verify.png (opened: "Ready / provider: seed / seed 2026-07-22 / 591 symbols", "GO — today's board is current") + runs/goal-ops-hardening-iter-39/live-restart/post-restart-data-payload.json (TC-8: run 243 `interrupted`, dates_done 2/18, snapshots_created 1 — real, non-zero) |
| J-05 Aggregates are precomputed at ingest, never on the fly | passing | passing | reports/qa/goal-ops-hardening-iter-39-evidence/J-05-verify.png (opened: "Immutable snapshot — as of 2005-04-12 · Stored exactly as scanned; never recomputed for today"; regime components 21.25+10.98+15.00+7.50+0.00 = 54.73, arithmetic checks out) + live-restart/tc9-historical-coverage-cold.json (TC-9: `coverage_status: stale`, snapshot_count 1902 — real, not the all-zero sentinel) |
| J-06 Pages load only what they need | passing | passing | reports/qa/goal-ops-hardening-iter-39-evidence/J-06-verify.png (replay PASS) |
| J-07 Heavy aggregates never take the service down | partial | **partial** (5th consecutive; `evidence_makeup` kept) | runs/goal-ops-hardening-iter-39/fault-drill/tc3-containment.json + logs/backend.log:147787 / :148264-148270 (live abort at the NAMED handler) + fault-drill/health-monitor.csv (68/68 HTTP 200) — see step-by-step split below |
| J-08 Backtest evidence serves from storage only | passing | passing | reports/qa/goal-ops-hardening-iter-39-evidence/J-08-verify.png (replay PASS) |
| J-09 The backend discloses its own background-compute activity | passing | passing | reports/qa/goal-ops-hardening-iter-39-evidence/J-09-verify.png (replay PASS) |

**No journey regressed. No journey is `unknown`. No `DEFERRED-BUDGET` row. No `browser-infra.json`.
No `journeys-changed.md`.** All 8 `spec_hash` values match `goal_gate.py hash-journeys docs/goal.md`.

### J-07 step-by-step split (why `partial`, not `passing`)

| J-07 item | This iteration | Evidence I opened myself |
|---|---|---|
| Step 1 — warm every horizon via the ingest finalize path | closed at iter-38, byte-frozen by this spec's "Do not redo" | (carried) |
| Step 2 — 1 Hz `/api/health`, every poll 200 **within its existing budget** | **HALF met** | 68 polls, **68/68 HTTP 200**, max gap 2.298 s, whole-job coverage (last sample t=81.965 s caught `job_status: ok`), no `MAX_SECONDS` backstop — but latency min/mean/max 0.0953 / 0.2267 / 1.2970 s and only **3 of 68** inside the committed ≤ 0.1 s budget (`fault-drill/health-monitor.csv`, recomputed by me). Sixth consecutive miss — owner item iter-34/j. |
| Step 3 — VmPeak under `memory_cap_mb`, margin in perf-budgets | met | VmPeak max 3,100,072 kB = **49.27%** of the 6,291,456 kB cap (50.73% margin); recorded in `reports/perf-budgets.md` "Iteration 39 FIX PASS" |
| Step 4 — induced pressure aborts honestly, same process keeps serving | **MET via the test-hook branch** | Live log (not the excerpt): `:147787` job-scoped liveness `job=c67a6b0a…`, `:148264-148270` abort whose traceback names `data_manager.py:3550 _refresh_ingest_aggregates → _fault_inject_memory_error("forward_aggregates")` — the NAMED per-horizon handler. `final-job-status.json`: `status: ok`, 2/2 dates, `aggregates_refreshed` omits `forward_aggregates` while `research_hot_keys` and `drawdown_expectations` (which run after it) completed. TC-3 recomputed from raw `backtest-poll.jsonl`: 1,246 requests, **1,246/1,246 HTTP 200**, exactly one whose interval contains the abort epoch. TC-4: PID 982870 unchanged. Whole drill-process log window `:146509-149317` = **1,486 responses, ALL 200**. |
| Acceptance — "a memory-pressure abort never leaves the process wedged (step 4)" | **FALSIFIED this iteration** | `mem-drill/trial3-2650mb-wedge-evidence.txt` — at a 2650 MB throwaway cap the job persisted `status: ok` and the SAME process then stopped answering `/api/health` for 7+ minutes (curl `000`, zero new log lines, 14 threads in `futex_do_wait`, host 15 GiB free). Step 4's own text sanctions "a tightened cap in a throwaway process" as a method. Dying thread never identified; the first attribution was retracted by the developer and the retraction confirmed by the auditor. |
| Acceptance — "no unbounded whole-table ORM materialization remains on the warm or serving path" | **still false, now with a second confirmed site** | `_missing_data_diagnostic` (`data_manager.py:271`) buffers every universe member's `(symbol, date)` rows (~3.3M) into one list before the loop runs — traceback at `trial3-2650mb-wedge-evidence.txt:17-29` (`loading.py:220 chunks → result.py:580 _raw_all_rows`). On BOTH the ingest finalize path and `/api/data` coverage compute (`data_manager.py:936`). Plus the carried iter-29/d site. |
| Walkthrough — `[NEW]` steps via `demo.sh --session-live` | **unrecorded, 9th iteration** | demo lane SKIPPED, "invalid demo script: missing or empty steps[]", `reports/demo/goal-ops-hardening-iter-39/` empty. Capture-only ride-along — `evidence_makeup` kept. |

## Anti-goal Check

Worked from `iter-39/scan-report.md` (**CLEAN** — no secret, dependency or license findings) and
`iter-39/iter-diff.md` (32 files, 31 shown in full; the one truncation is a framework host-guard script).

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials (AG-7) | OK | scan-report CLEAN. New file `apps/backend/app/logging_config.py` reviewed: attaches a root `StreamHandler` only. Audit B5 grepped every `logger.info`/`.debug` under `apps/backend/app` for key/token/secret/password/url material — one benign line (`warmup.py:147`). No new config/env file in the diff. |
| Paid / external SaaS (AG-9) | OK | No manifest touched: `git diff snapshot..HEAD -- '*package.json' '*requirements*' '*pyproject*'` is empty, and `git status --porcelain` shows no manifest. Every drill ran on a local throwaway DB from the committed seed; no network calls. |
| License changes | OK | No `LICENSE*` file in the diff or working tree. |
| Fabricated / substituted data (AG-3) | **VIOLATION — minor, open (iter-39/w)** | Nothing fabricated. But after `kill -9` the `/data` Run History row shows `dates_done 2/18` while the process had reached `18/18` in memory (`live-restart/kill-test-mid-flight-state.json` vs `post-restart-data-payload.json`, both read by me). TC-8's literal bar is met (real non-zero row), so J-04 stays `passing`; the user still sees ~11% of the work done. Audit B7. |
| AG-1 / AG-2 / AG-4 / AG-6 (proven-language, order placement, overfit, referee) | OK | No evidence-derived claim, no scoring/ranking change, no proven-language. The diff is a test-only fault injector, a worker-thread `MemoryError` catch, an env-toggle guard, a logging handler, and pipeline tooling. Coherence audit confirms zero frontend files changed. |
| AG-5 (determinism / no-lookahead) | OK | No scoring or forward-return code touched. `compute_forward_aggregates` / `resolved_forward_aggregate_evidence` / `ensure_historical_forward_aggregates_dispatched` are byte-frozen by this spec and absent from the diff. |
| **AG-8 (data-scale resilience, unbounded whole-table loads)** | **VIOLATION — minor, open (iter-39/u, iter-39/v + carried iter-29/d, 31/e, 32/f, 35/k, 37/o)** | See the J-07 table above. Classified minor, not critical, and I state the grounds rather than assume them: both are **pre-existing code**, newly *observed* rather than newly *introduced*; neither is reachable in shipped configuration (`config.yaml:1363 memory_cap_mb: 6144` byte-unchanged — I diffed it); and the same code at 6144 MB served **1,486/1,486 HTTP 200** in this iteration's own drill. This iteration's product change *improves* memory isolation. Ten iterations of session precedent classify this family as minor/open. |
| **AG-10 (host resource ceiling)** | OK — but a fact the owner must see | `git diff snapshot..HEAD` over `scripts/start-backend.sh`, `scripts/dev.sh`, `scripts/start-frontend.sh` and `project-extensions/host-guard/*.sh` is **EMPTY** — no HOST-GUARD block stripped, so AG-10's own REGRESSION trigger did not fire. Every drill was launched only via `scripts/start-backend.sh`, and the boot banner (`logs/backend.log:146507-146509`) shows the declared caps applied verbatim. **However `host-guard.env` itself changed (+36/-24)** — by the OWNER, commit `1130a36b` "release the CPU mask to the whole machine", inside this window's framework-sync commits; `HOST_GUARD_CPU_LIST` `0-3,8-11` → `0-15`, `BLAS_THREADS` 4 → 8, with a recorded hardware root cause. `docs/goal.md` puts `host-guard.env` in owner/framework scope, and the memory cap is unchanged. Recorded so no future evaluator mistakes this for an agent weakening the caps. |
| Host hygiene (iter-36/m precedent) | OK | `ps -eo pid,rss,args` shows no uvicorn, no `next-server`, no drill poller; no listener on 8255/18255/3255/8256. Clean shutdown, unlike iter-36. |

**Ledger: 36 total, 15 unresolved, 0 critical.** Two RESOLVED this iteration (iter-38/s — J-07 step 4
now genuinely proven; iter-38/t — the deterministic replay lane is repaired *and* worked). Four new,
all minor (iter-39/u, /v, /w, /x). Eleven carried, each given an ITER-39 UPDATE recording what I
verified rather than inherited.

## Pipeline Health

`iter-39/depth-dispatched` = `full`, matching the spec. `status.json` = `complete` / `closure_passed`
(its `browser_checks_run: false` is stale relative to the 23:31 replay — I scored from artifacts, not
that field). The audit ran **twice**: the first returned **FAIL** (B1-B9, including a *critical* B2 —
`backfill_workers`' per-date compute carried no `MemoryError` isolation), the developer ran a fix pass,
the reviewer re-passed (PASS), QA re-passed (PASS), and the second audit returned **PASS_WITH_GAPS**.
Coherence **COHERENCE-PASS** (two non-blocking advisories). ux-regression UX-REGRESSION-PASS. Closure
CLOSURE-PASS. Demo lane SKIPPED (empty `steps[]`).

Two staleness facts I record plainly rather than round away:
- **Audit T1:** the 7-journey replay (mtime 23:31:56) predates the fix pass's edits to
  `data_manager.py` (00:05:31) and `replay-lane.sh` (00:03:25), so the browser evidence is one code
  state stale. The auditor traced the delta and it is inert on every non-`MemoryError` path (both old
  `except Exception` arms now resolve to the wrapper's own, producing the identical error string; the
  only added per-call work is one `os.environ.get` and one `Event.is_set()`), and
  `test_data_manager_backfill_parallel.py` re-ran 12/12 green afterwards under both the reviewer and
  the auditor. I kept the seven `passing` on that basis and say so here.
- **`reports/perf-budgets.md:4996`** still carries the RETRACTED attribution of the wedge to a
  `backfill_workers` thread. The later "FIX PASS" section corrects it honestly, but its supersession
  sentence names only TC-1..TC-4, so a reader of the earlier section alone gets the withdrawn story.

## Next-Step Recommendation

Run the next iteration at **full depth** (mandatory — this verdict makes it so). Give it **one**
target: fix the place in the code that reads about 3.3 million price rows into memory in one go
(`_missing_data_diagnostic`, `apps/backend/app/engine/data_manager.py:271`) so it reads them in small
batches instead. Everyone who looked at this iteration — the developer, the reviewer and the auditor —
independently picked the same item, the change gives exactly the same answer as today, and it is the
one fix that moves three separate things at once: it is the last blocker on J-07 "Heavy aggregates
never take the service down", it is very likely the cause of the seven-minute freeze, and it is the
reason the earlier memory tests could never reach the part of the code they were aiming at. While
doing it, also correct the comment above that code, which today says the read is safe when it is not.

Then, in order, and only after the above is green:
1. Re-run the tightened-cap drill once to see whether the freeze still happens. If it does, find which
   background thread dies. Keep it on a throwaway database, launched only through
   `scripts/start-backend.sh`.
2. Make the crash-recovery number honest (iter-39/w): after a crash the job list shows 2 of 18 days
   done when 18 were really done. Either save progress after every day, or label the number as "last
   saved point" instead of "progress".
3. Record J-07's short walkthrough video/steps. This is a capture task only — never an iteration's
   own goal.
4. Still waiting, deferred four times: give Regime Lab's slow "All history" view the same background
   handling `/api/backtest` already has (iter-33/g).

**Two decisions only the owner can make, and both should be settled before anyone tries to declare the
goal finished:**
- **(a) The health-check speed rule.** The app is asked to answer its own health question in under
  0.1 seconds. While heavy background work runs, it takes 0.1-1.3 seconds. That has now happened six
  times in a row, and no agent can decide it. Three choices: accept the current honest warning as good
  enough, relax the rule for the short period while background work runs, or ask for the fix that
  serves the health answer from a saved copy. This is the most likely place a final independent check
  would refuse to sign off.
- **(b)** Whether `start-frontend.sh` should also be covered by the host-protection marker list
  (iter-33/i), unchanged.
