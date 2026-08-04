# Iteration 46 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This round did the best engineering work of the session, and the journey table hides it. For five
rounds the app ran out of memory and went dark for many minutes; this round it stayed up under the
heaviest load anyone has put on it, with **zero out-of-memory errors** and **no silent window at all**
in its own log. The round also stumbled into a defect nobody was looking for — adding zero days of
history used to take 29 minutes — and fixed it inside the same round, down to a fifth of a second.
But one fact governs every row below: **the only browser check ran at 05:49, and the app was changed
twice afterwards (06:17 and 08:38), both times to fix the very things that had just failed.** Nobody
re-ran the check. So no journey can be scored on this round's own work, four previously-passing
journeys drop to "partly working", and the round's headline promise — that the Evidence page stops
being slow — is still not delivered.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | **partial** | `reports/phase-goal-ops-hardening-iter-46-ui-test-results.md:31` (FAIL, pre-fix build) + `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-01-fail.png` (opened: generic /data coverage frame, does NOT show the stuck row) + sqlite `data_provider_runs` id=287 vs id=289/291 (**0.22 s, `ok`** on the shipped build) |
| J-03 No per-run range cap | passing | **partial** | `ui-test-results.md:32` (FAIL; no cap rejection = core claim held) + `UT-J-03-fail.png` (opened; md5 8ecffcd4, distinct but same generic frame) + sqlite id=280 (**29 min**, iter-45 build) vs id=290 (**0.19 s, `ok`**, shipped build) |
| J-04 Non-blocking boot with visible status | passing | **partial** | `ui-test-results.md:33` + `:47-51` (lane PASS; first health 200 at **~29 s** vs the ≤5 s clause) + `UT-J-04-result.png` + `ui-test-plan.md:259-262` (the disclosure the lane cited, read by me — it covers the badge, not the first-200) |
| J-05 Aggregates are precomputed at ingest, never on the fly | failing | **failing** (3rd consecutive) | `ui-test-results.md:34` + sqlite `data_provider_runs` id=284 (`dates_done 0/1`, `snapshots_created 0`, ~21 min, `interrupted`) + `logs/backend.log` (no MemoryError; last one in the file precedes the 01:34:45Z launch) — **no J-05 screenshot exists** |
| J-06 Pages load only what they need | passing | **partial** | `ui-test-results.md:35` (10/11 routes 2-5 s; `/api/evidence` HTTP 000 at `time_total=300.000568s`) + `UT-J-06-evidence-slow.png` (opened: skeleton bars, no claim rows) + dev fix-pass measurement 163.3 s cold on an idle backend |
| J-07 Heavy aggregates never take the service down | failing | **partial** (first movement since iter-34) | `ui-test-results.md:36` (34/34 health polls HTTP 200 at 0.10-0.40 s under 2 backfills + background compute) + `UT-J-07-badge-ready-under-load.png` (opened: Dashboard fully rendered under load) + `reports/perf-budgets.md` Item O (120/120 polls, max 104 ms; VmPeak 3,123.0 MB vs 8192 MB cap) + my own log scan (no silent window; zero MemoryErrors) |
| J-08 Backtest evidence serves from storage only | passing | **passing** | `ui-test-results.md:37` + `UT-J-08-result.png` (spot-checked by me: /backtest at "Viewing as-of 2026-07-31 (latest)", Market Regime 60.23, Candidate Counts, forward-test scorecard — rendered while 2 jobs ran) |
| J-09 The backend discloses its own background-compute activity | passing | **passing** | `ui-test-results.md:38` + `UT-J-09-result.png` (spot-checked by me: "Viewing as-of 2026-07-30 (historical)" returned without blocking, "running (1)" chip in the same frame) |

Deferred (`DEFERRED-BUDGET`): none. No `browser-infra.json` (no `pending_infra`). No
`journeys-changed.md`; all eight `spec_hash`es match `goal_gate hash-journeys`, which I ran myself.
`evidence_makeup` cleared everywhere (J-03 and J-04 carried it from iter-45 and now have fresh,
distinct captures). No deterministic replay lane ran this iteration — all eight journeys rode the LLM
lane, which drilled them far harder than the replay ever has.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials (AG-7) | OK | `iter-46/scan-report.md`: **CLEAN**, no findings on added lines; 1 untracked file scanned. I also eyeballed the changed-file list — no new config/env files. |
| Paid / external SaaS (AG-9) | OK | No manifest changes in `iter-diff.md`'s file list (backend engine + tests + one JSON anchor + reports only); ingest still runs `provider: seed` (confirmed in every run record I read and on the dashboard capture). |
| License changes | OK | scan-report reports no license findings; no LICENSE file in the diff. |
| Fabricated / substituted data (AG-1/AG-3/AG-4) | OK | Both refactors are proven byte-identical against a pinned pre-fix oracle; reviewer and auditor each re-derived it from the code. The auditor's **B1** caught a genuine AG-3 risk *created by this iteration's own fix* — a clear-and-recreate rebuild would have kept serving pre-rebuild coverage numbers — and closed it in-audit at `data_manager.py:3803` with before/after proof (TC-A1/A2/A3). Resolved inside the iteration. |
| AG-8 — memory exhaustion / unbounded loads | **PARTLY VIOLATED (minor, open)** | Two of three evidenced sites are bounded and **zero MemoryErrors occurred anywhere this iteration** (verified by me: last one in the 178,613-line log is at line 172956, before the 01:34:45Z launch). The third, `samples.py:145`/`:156`, is untouched and was seen failing at 02:20:31 via `evidence.py:168` — filed **iter-46/au**. |
| AG-8 — graceful degradation | **MINOR, open** | The `/evidence` page degraded honestly (skeleton, never blank — I opened the frame). But one unhandled `QueuePool limit ... reached` inside `GET /api/backtest` (verified by me at `logs/backend.log:175614`) left a tab spinning with no error and no retry — filed **iter-46/ba**. Occurred only under a self-stacked load heavier than any journey's own scenario. |
| AG-10 — host resource ceiling | OK | Every launch banner in the log reads `memory_cap_mb=8192 malloc_arena_max=2` with `host-guard: cpu_list=0-15 blas_threads=8`; `/proc/<pid>/limits` confirms 8589934592 bytes. No cap value changed; no HOST-GUARD block touched. |
| AG-2 / AG-5 / AG-6 | OK | No new user-facing claim, no scoring or forward-return change (backend memory-bounding only, byte-identical outputs required and proven); no evidence-derived claim introduced, so the referee gate is not engaged. |
| Committed budgets (goal Success Criteria) | **MINOR, open** | `GET /api/evidence` 163.3 s idle / >300 s loaded against a ≤3 s budget — **iter-46/av**; first health 200 at ~29 s against ≤5 s — **iter-46/az**; the new warm's two bare `logger.exception` calls — **iter-46/aw**. |

Ledger after this iteration: **64 entries, 20 unresolved, 0 unresolved critical.** Five resolved this
round (iter-44/ak, iter-44/al, iter-45/ao, iter-45/at, iter-43/ag); two new-and-resolved-in-round
(iter-46/ay, iter-46/bb); five new and open (au, av, aw, az, ba). Coherence: **COHERENCE-WARN** — zero
blocking violations, three advisories (two undocumented-in-blueprint additions plus context on the
audit's open findings). No structural veto.

## Next-Step Recommendation

**Re-run all eight journey checks first, before writing any new code.** Today's pictures were taken on
a build that changed twice afterwards, so nobody actually knows what the current app does. Give every
journey its own picture: "Aggregates are precomputed at ingest" (J-05) has none at all and has been
borrowing another journey's file for three rounds.

Then give the round one real job: **make the Evidence page usable again after a data job.** Right now
a single row of new data throws away all seven stored evidence panels, and the next person to open
that page waits about 163 seconds on an idle machine, or more than 300 seconds while a job runs.
Either rebuild those panels right after the job saves its data — before the slow tail starts — or keep
showing the previous ones behind an honest "recomputing" label.

After that, in order: **put a firm limit on the third memory-hungry place on that same page**
(`apps/backend/app/engine/samples.py:145` builds the whole history at once and `:156` sorts it whole),
proving the output is unchanged; and **make adding one old day of history finish** — every day left to
fill sits before dates already stored, which is exactly the case last round's shortcut skipped, so the
app still rebuilds the entire membership history for one day and never completes.

Small and already written down: measure how long the backend takes to answer for the first time on an
idle machine (this round read ~29 s against a promise of 5 s, but under heavy congestion — a clean
number may simply restore J-04 "Non-blocking boot with visible status"); protect the two unguarded log
calls in the new warm-up code (`warmup.py:205`, `:212`); add the snapshot-date filter the auditor
proved safe to `_drawdown_ticker_slice_map`, which today reads 7,994,388 rows to serve 7 claims; give
the database connection pool room so a page cannot be left spinning with no error.

Carried, untouched: iter-29/b + the badge wording after a permanently failed warm-up (eighteen rounds
unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u. iter-43/ag is
now closed. Deferred a twelfth time: iter-33/g, Regime Lab's cold pooled view. Capture-only, never a
round's goal: J-07's `[NEW]` walkthrough (sixteenth round unrecorded) and J-05's acceptance frames.

**One sentence for the owner:** nothing needs your decision — but three facts belong in front of you:
the app no longer goes dark and no longer runs out of memory (the first good news in five rounds),
adding one old day of history still never finishes, and the Evidence page still takes about three
minutes after any data job.
