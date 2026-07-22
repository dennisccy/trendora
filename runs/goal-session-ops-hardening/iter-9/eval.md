# Iteration 9 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-05 — the session's regressed target since iter-7 — is genuinely recovered and, for the first time,
proven by a qualified lane: all four acceptance steps carry live browser evidence (UT-04/05/06/07/08,
screenshots I opened myself) and step 4 was closed by the 18-minute operator-authorized heavy-ingest run
whose raw CSVs I re-derived independently (439/439 `GET /api/health` polls HTTP 200, peak VmPeak
4,738,948 KB vs the 6,291,456 KB cap). J-01 and J-03 move out of `unknown` on live LLM re-verification
(the replay-lane FAILs are stale-build false positives with a reconciliation footer on file), and the
AG-10 launcher gap is closed and live-verified on `/proc`. But J-04 does NOT pass: its step 6 failed in a
real browser (an interrupted job persisted `0 snapshots · 0 trading days`), the product defect was fixed
intra-iteration (F1 `_checkpoint_run_record`) and confirmed post-fix at the API level by the operator
(run 114 frozen at 59 snapshots / 64-of-84 dates vs. the all-zero pre-fix control run 113) — but no
browser lane re-drove `/data` after the fix, so J-04 is scored `partial`, not `passing`.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | unknown | **passing** | `...-ui-test-results.llm.md` § "J-01" (8/8 steps) + `reports/qa/goal-ops-hardening-iter-9-evidence/UT-J-01-result.png` — I opened it: `no new snapshots` badge, "0 snapshots over 19 dates", "28 calendar days · 19 already snapshotted · 9 non-trading", explicit "Zero-work outcome … this is not a failure" callout (matches goal.md's run-summary contract exactly: 19 + 9 = 28). Replay-lane FAIL overturned — see reconciliation footer in `phase-goal-ops-hardening-iter-9-regression-replay-results.md:44`. |
| J-03 | unknown | **passing** | `...-ui-test-results.llm.md` § "J-03" (live end-to-end this pass) + `UT-J-03-result.png` — I opened it: `no new snapshots`, "0 snapshots over 283 dates", "412 calendar days · 283 already snapshotted · 129 non-trading", `Refreshed:` list populated. No range-cap rejection; ran to completion; health 200 throughout, RSS ~4.2 GB of the 6144 MB cap. |
| J-04 | unknown | **partial** (steps 1–5 pass, step 6 fixed but not browser-re-verified) | Steps 1–5: `...-ui-test-results.llm.md` § UT-J-04 breakdown (UT-11/UT-12 badge+banner, live `logs/backend.log` truncation trace). Step 6 FAIL: `UT-10-result.png` — I opened it, `interrupted` badge with "backfill: 0 snapshots over 0 dates" / "0 snapshots · 0 trading days in range". Post-fix operator evidence: `runs/goal-ops-hardening-iter-9/pump-j04-crash-recovery-evidence.md` (run 114 `interrupted`, `snapshots_created 59`, `dates_done 64/84` vs. pre-fix control run 113 all-zero, same `GET /api/data` response). API-level only — no browser lane re-ran. |
| J-05 | regressed | **passing** | Step 1: `UT-04-result.png` — I opened it: badge `ok`, "1 snapshots over 1 dates, 1440 forward returns", `Refreshed: latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, drawdown expectations` (all 7). Step 2: `UT-06-result.png` (run detail 2026-05-15 — Regime 67.83/Risk-on, Actionable 2 / Breakout-watch 59 / Pullback-watch 3, leaderboard rows) + `UT-07-result.png` (Market Phase 32.21/100, Pullback, P(bear) 0.00 at the new as-of, no spinner). Step 3: `UT-08-result.png` (cold `/data` after restart, coverage from the persisted payload — 591 symbols / 5380 trading days / 1113 snapshot dates; `GET /api/data` responseEnd 436.9 ms). Step 4: `runs/goal-ops-hardening-iter-9/heavy-ingest-vm-samples-health.csv` — I re-derived it: 439 rows, all `http_status=200`, max elapsed 3.646 s; `heavy-ingest-vm-samples.csv` max VmPeak 4,738,948 KB (cap 6,291,456); `heavy-ingest-pytest.log` `1 passed in 1092.93s`. Corroborated by UT-J-03's live 4-min chunked backfill. |
| J-06 | partial | partial (carried, not re-tested) | Out of scope this iteration (spec OUT OF SCOPE). No fresh 11-page sweep; `last_verified_iter` left at iter-7. |

Note (audit P3, non-blocking): no artifact emits an explicit `UT-J-05` verdict row — J-05's evidence is
assembled by citation across UT-04/05/06/07/08 + the heavy run. I traced and opened each cited row myself
rather than relying on the audit's trace.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (proven-language only from the ledger) | OK | Zero frontend files in the diff (coherence.md §Data Contract, independently confirmed `git diff --stat -- apps/frontend` empty); no new displayed value. No proven/confidence claim added. |
| AG-2 (decision-quality only) | OK | Diff is launcher scripts + a libc-handle memoization + a run-record checkpoint + tests. No returns/targets/orders anywhere. |
| AG-3 (displayed numbers correct) | OK | Checked positively, not assumed: UT-J-01's breakdown partitions 28 calendar days (19+9); UT-J-03's partitions 412 (283+129); UT-06's run-detail counts match the UT-05 leaderboard row. The F1 checkpoint writes through the pre-existing single `_run_detail()` serializer (coherence.md, `data_manager.py:3668-3708`) — no second derivation, no fabricated breakdown. UT-10's `0 snapshots` was an honest report of genuinely-absent data, not a fabrication. |
| AG-4 (no overfit edges) | OK | No scoring/referee/evidence-ledger code in the diff. |
| AG-5 (determinism / no lookahead) | OK | No scoring or forward-return window touched; snapshots re-served from storage (UT-06 "Stored exactly as scanned; never recomputed for today"). |
| AG-6 (referee gate) | OK | No evidence-derived claims this iteration (goal.md Loop mechanics: J-01…J-06 carry none). |
| AG-7 (no hard-coded credentials) | OK | `iter-9/scan-report.md`: **CLEAN** — no secret, dependency, or license findings on added lines. I also eyeballed the two launcher hunks: every value is sourced from `host-guard.env` / `app.config.get_config()`; no literals. |
| Paid/external SaaS | OK | scan-report CLEAN; no manifest changes in the 6-file diff. |
| License changes | OK | scan-report CLEAN; no LICENSE file in the diff file list. |
| Fabricated/substituted data | OK | The heavy run used a throwaway copy of the real dev DB with only `database.url` rewritten (perf-budgets iter-9 §Method); its job-2 target date is now resolved AT RUN TIME from the instance's own `/api/data/availability` (audit T3 fix) rather than hardcoded — the opposite of substitution. |
| AG-8 (resilience / no memory exhaustion) | **iter-7 violation now RESOLVED**; one distinct dimension still open | RESOLVED: the iter-7 failure mode (7+ min health hang, worker MemoryError at the 6144 MB ulimit, manual restart) is refuted by the qualified evidence iter-8 lacked — back-to-back full-universe rebuild + heavy backfill in ONE long-lived process, 1092.93 s, 439/439 health polls 200, both jobs `status: ok` with all 7 aggregate categories, VmPeak 24.7% under the cap, under caps applied BY THE SHIPPED LAUNCHER (`logs/backend.log` boot line `host-guard: cpu_list=0-3,8-11 blas_threads=4`) — closing iter-8's own attribution objection. WATCH ITEM (honest, not a violation): margin narrowed 43.6% → 24.7%, and the audit (P1) proved sampling cadence contributes 0 KB (VmPeak is a monotone kernel high-water mark; re-subsampling at 1 Hz and 10 s yields the identical peak), so the narrowing is real demand growth. STILL OPEN, distinct: the deferred on-load `/api/backtest` → `forward_aggregates_cached` MemoryError (iter-7 observation, not re-tested here, explicitly OUT OF SCOPE pending an owner decision) — recorded unresolved; it blocks GOAL_ACHIEVED but is not a new/worsened violation, so it does not fire the REGRESSION branch (see Verdict reasoning). |
| AG-10 (host resource ceiling) | **RESOLVED** (was minor/unresolved from iter-8) | `scripts/start-backend.sh` and `scripts/dev.sh`'s **backend subshell only** now carry a marked HOST-GUARD block sourcing `host-guard.env` (`iter-diff.md` lines 787-868: `taskset -c "$HOST_GUARD_CPU_LIST"`, the 4 BLAS/OMP/MKL/NUMEXPR vars, plus `dev.sh` mirroring `ulimit -v` + `MALLOC_ARENA_MAX`); no magic numbers. Live-verified independently on the running process by browser-qa (`/proc/1214476`: `Cpus_allowed_list 0-3,8-11`, `OMP_NUM_THREADS=4`, `MALLOC_ARENA_MAX=2`, Max address space 6442450944) and again by the audit + TC-7/TC-8/TC-9 (incl. proof the `next dev` frontend subshell carries NONE of the caps). Nothing stripped or weakened. |

Coherence: `iter-9/coherence.md` = **COHERENCE-PASS** — no consolidation mandate. (One advisory: the
blueprint's iter-9 paragraph omits the `_checkpoint_run_record` change; recommend a one-sentence fix.)

## Next-Step Recommendation

Full depth, verification-and-currency only — no new features. In priority order:

1. **Close J-04 step 6 with a browser-lane pass.** Re-drive the `/data` page after a kill/restart on the
   current (F1 + audit-B1) tree: start a multi-date backfill, let ≥ 1 checkpoint land (10 s throttle),
   `kill -9`, restart, and read the RENDERED Run History / Job progress panel — the operator already
   proved the persisted data is real (run 114: 59 snapshots, 64/84 dates); what is missing is the
   rendered surface. Emit an explicit `UT-J-04` verdict row and supersede the AUDITOR ADDENDUM in
   `reports/phase-goal-ops-hardening-iter-9-regression-replay-results.md` (or its iter-10 successor).
   This is the single item standing between the session and all-five-passing.
2. **Emit an explicit `UT-J-05` row** (audit P3) so J-05's pass stops requiring a manual citation
   assembly across UT-04/05/06/07/08.
3. **Refresh the stale QA artifact** — `reports/qa/goal-ops-hardening-iter-9-qa.md` (09:30 UTC) still
   records the heavy run as "DEFERRED — host safety" and TC-10/11/12/14 as "NOT EXECUTED", and carries a
   `PASS` / "ready to move forward" conclusion written before both the browser lane (12:34) and the heavy
   run (15:18–15:36). Regenerate or add a dated addendum, then re-run the closure gate (currently
   CLOSURE-FAIL on DoD item 2 + this staleness).
4. **Owner decisions still outstanding — do not let an agent invent either resolution:** (a) the deferred
   on-load `/api/backtest` MemoryError (J-06/AG-8) — new scoped iteration budget or explicit deferral;
   (b) the unproduced `demo.sh ops-hardening --session-live` walkthroughs for J-05 and J-06; (c) whether
   to flip `HOST_GUARD_REQUIRE_MARKERS` to `1` now that the launcher blocks exist and are live-verified.
   Note `session.json max_iterations: 9` — continuing at all requires an owner budget extension.
5. **Framework maintainer (unchanged, still unfixed):** `merge_ui_test_results.py:57` drops emphasised
   `**FAIL**` verdict cells (this iteration's merged headline had to be hand-corrected by the audit), and
   the `Frontend Present: no` → browser-qa-skip misrouting that caused iter-8's blank iteration.
   Also carried: `tests/test_db.py::test_create_all_produces_expected_tables` (pre-existing failure,
   stale expected-table set since iter-2) and audit B3 (no `command -v taskset` guard).

## Halt Justification

Not halting. REGRESSION was considered and rejected: no journey moved `passing`/`already_passing` →
`failing` this iteration (J-04 entered as `unknown` and its step-6 defect is documented pre-existing,
untouched by this diff, and fixed intra-iteration), and the one still-open critical AG-8 dimension
(the on-load `/api/backtest` MemoryError) is a carried, human-known, spec-declared out-of-scope deferral
awaiting an owner decision — not a new or worsened violation; re-halting on it would re-present a choice
the human already made (logged in `assumptions.md`). STALLED was rejected: item 1 above is concrete,
agent-owned work (the operator has already demonstrated the kill/restart cooperation it needs).
GOAL_ACHIEVED was rejected: J-04 is `partial` and J-06 is `partial`, closure is CLOSURE-FAIL, and two
owner-decision items remain open.
