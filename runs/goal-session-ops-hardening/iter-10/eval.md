# Iteration 10 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The one gap this session has carried since iter-9 — J-04 step 6, "an interrupted mid-flight job shows its last
persisted progress on the rendered `/data` page" — is closed. A third crash cycle caught a 504-date backfill
genuinely mid-flight (`kill -9` of backend pid 2080333 at 19:32:15Z, restart 19:32:18Z as pid 2100030), and the
resulting row renders `interrupted` with `Snapshots: 117` and a full non-null breakdown, against eight pre-fix
sibling rows showing zeros on the same page load. I re-derived the decisive facts myself from sqlite and
`logs/backend.log` rather than accepting the lane's or the operator's account. J-04 moves partial→passing;
J-01/J-03/J-05 re-verify green; J-06 remains `partial` and is now the only non-passing Must-have, so this is not
GOAL_ACHIEVED. Product diff this iteration is `README.md` only; coherence PASS; review PASS.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing (replay re-verified) | `reports/phase-goal-ops-hardening-iter-10-regression-replay-results.md` UT-J-01 PASS; `reports/qa/goal-ops-hardening-iter-10-evidence/J-01-verify.png`; evaluator DB check: `data_provider_runs` id 115 = seed / ok / 0 snapshots over 0 dates (zero-work weekend span) |
| J-03 | passing | passing (replay re-verified) | Same replay artifact, UT-J-03 PASS; `J-03-verify.png`; evaluator DB check: id 116 = 412-day span accepted, `dates_done 283/283`, status ok — no range cap |
| J-04 | partial | **passing** | `reports/phase-goal-ops-hardening-iter-10-ui-test-results.llm.md` UT-J-04 PASS (steps 1-6 table); `reports/qa/goal-ops-hardening-iter-10-evidence/UT-J-04-step6-run119-crash-cycle-evidence.txt`; `UT-J-04-step6-run119-data-page-top.png`; evaluator DB check: id 119 `interrupted` 117/158/504, `calendar_days 729`, `non_trading 225`, `already_snapshotted 41`; `logs/backend.log:26780-26783` restart banner with no clean-shutdown line for pid 2080333 |
| J-05 | passing | passing (light non-heavy re-confirmation) | Same `.llm.md` UT-J-05 PASS; `UT-J-05-stored-snapshot-scanner-run-378.png` (opened — "Immutable snapshot … Stored exactly as scanned; never recomputed for today"); evaluator DB check: run 117 refreshed all 7 aggregate categories, `scanner_runs` id 1193 = 2021-09-15, regime 73.02 "Risk-on" — byte-matching what the lane read off the rendered page |
| J-06 | partial | partial (unchanged, not tested — out of scope) | `last_verified_iter` deliberately left at iter-7; iter-10 spec OUT OF SCOPE section |

### Why J-04's step 6 is accepted (the skeptical trace)

1. **The kill was genuinely mid-flight, provable without the operator's report.** Run 119 targeted 504 dates and
   is persisted at `dates_done 158` — 346 dates short. A completed run would read `ok`, 504/504.
2. **The old process wrote nothing on the way out.** `finished_at` 19:32:19.621 lands 1.3 s *after* the successor's
   `=== start-backend.sh: launching at 2026-07-22T19:32:18Z ===` banner, so the new process's orphan sweep
   finalized the row. A full-file grep finds no `Shutting down` / `Application shutdown complete` /
   `Finished server process [2080333]` before that banner, while pid 1803579 earlier in the same file does show the
   complete clean-shutdown sequence — the format records clean shutdowns, so the absence is signal. This also
   re-confirms step 5 on a second, independent cycle.
3. **The observation is of the rendered surface, not the API.** The captured cell text
   "729 calendar days · 41 already snapshotted · 225 non-trading" is composed client-side in
   `apps/frontend/app/data/page.tsx:2564-2573` (`parts.join(" · ")` inside `data-testid="backfill-breakdown"`;
   status badge at `page.tsx:3503`) and appears nowhere in the API payload — this is exactly the discriminator the
   round-3 auditor and the iter-9 evaluator demanded when they barred an API-only pass.
4. **The contrast is real, not narrated.** Pre-fix control rows 110 and 113, read straight from sqlite, are
   `interrupted` with `snapshots_created 0` and every breakdown field `null`.
5. **Honest gaps stated, not buried.** The scrolled screenshot is genuinely blank (I opened it) — a reproducible
   Chrome-MCP capture artifact on this very tall page; the DOM capture stands in its place. The lane's own
   middle cycle (run 118) is disclosed as a timing miss (job self-completed 38 s before the kill; DB confirms
   `status ok`, 84/84) and contributes nothing either way. Steps 1-4 are carried from iter-9 across an iteration
   whose product diff is `README.md` only, and the ≤5 s boot budget has not been re-measured since iter-9 changed
   `scripts/start-backend.sh` — both recorded as caveats in journey-history and in assumptions.md, both scheduled.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (proven-language backed by ledger) | OK | Zero source diff; `README.md` prose adds no proven/confidence claim (read the full diff — it documents the interrupted-row checkpoint and host-guard parity) |
| AG-2 (decision-quality only) | OK | No return promises, targets, signals, or order paths anywhere in the diff |
| AG-3 (displayed numbers correct) | OK | Personally cross-checked: rendered `117 / 729 / 41 / 225 / interrupted` == `data_provider_runs` id 119; rendered regime `73.02 Risk-on` == `scanner_runs` id 1193 |
| AG-4 (no overfit edges) | OK | No referee/claim/evidence path touched; no evidence claims registered this iteration |
| AG-5 (determinism / no lookahead) | OK | No scoring or forward-return code touched (empty product diff) |
| AG-6 (referee verdict for evidence claims) | OK | `verify_only_pass.evidence_claim_registered: false` in status.json; no claims to gate |
| AG-7 (no hard-coded credentials) | OK | `iter-10/scan-report.md`: CLEAN — no secret, dependency, or license findings; diff is one prose file |
| AG-8 (data-scale resilience) | **Carried, unresolved (critical)** | No NEW violation: a 504-date backfill plus three kill/restart cycles ran with no memory failure, backend healthy after each restart. The iter-9 entry — on-load `GET /api/backtest` → `forward_aggregates_cached` MemoryError — was not re-tested and stays `resolved: false`. It hard-blocks GOAL_ACHIEVED; per iter-8/iter-9 precedent a carried, human-known, spec-declared deferral does not re-fire the REGRESSION halt |
| AG-9 (offline-deterministic ingest) | OK | Every run this iteration is `provider: seed` in the DB (ids 115-119); no new dependency or network path in the diff |
| AG-10 (host resource ceiling) | **Partially — new minor entry** | Launcher side verified live by me: `logs/backend.log:26782` `host-guard: cpu_list=0-3,8-11 blas_threads=4` on the 19:32:18Z restart. Gap: the developer session ran targeted pytest **directly**, unconfined across all cores (its own disclosure, dev handoff:74-87), Tctl 84-89 °C; my `logs/hwmon/hwmon.csv` check finds 1,331 samples ≥88 °C between 2026-07-21T21:28Z and 2026-07-22T19:33Z, peak **91.0 °C** vs the 95 °C watchdog — no trip, no host reset, sampler live. Recorded MINOR (nothing stripped or weakened; pytest is not literally launchable via `start-backend.sh`) with a fix in the next-step list |
| License changes | OK | No LICENSE or license-field diff (single-file diff) |
| Fabricated/substituted data | OK | Journey evidence traced to persisted rows I queried myself; the lane volunteered its own failed cycle (run 118) rather than hiding it |

Coherence: `iter-10/coherence.md` = **COHERENCE-PASS** (zero new modules/endpoints/values; the one Data-Contract
row touched got a documentation-only blueprint amendment naming an already-shipped mechanism). No consolidation
mandate. `journeys-changed.md` absent and all five `spec_hash` values match the current `docs/goal.md` — no
goal-edit drift. Pipeline health: review = PASS, browser-qa = PASS (raw `.llm.md` read directly, per the standing
merge-script caveat) — no fail-open.

## Next-Step Recommendation

Full depth, session-closeout aimed at **J-06 — the only non-passing Must-have left**:

1. **Measurement re-sweep (agent-owned).** Re-run the 11-page real-browser TTI + on-load latency sweep and
   `bash scripts/measure-perf.sh --boot`, recording both in `reports/perf-budgets.md`. The `--boot` run also
   discharges J-04's carried WARN: the ≤5 s start→first-200 budget was last measured 2026-07-20T16:16Z (1.387 s),
   before iter-9 added the host-guard block to `scripts/start-backend.sh`.
2. **Walkthroughs (agent-owned).** Produce the `[NEW]`-flagged `demo.sh ops-hardening --session-live` walkthroughs
   for J-05 and J-06 — J-06's own Acceptance names one — or obtain an explicit human deferral. Outstanding since
   iter-4.
3. **OWNER DECISIONS — do not let an agent invent these.** (a) Scope or formally defer the on-load
   `/api/backtest` → `forward_aggregates_cached` MemoryError; it is the unresolved critical AG-8 entry and a hard
   GOAL_ACHIEVED blocker. (b) `HOST_GUARD_REQUIRE_MARKERS`.
4. **AG-10 hygiene.** Confine agent-run pytest with the host-guard `taskset`/BLAS env, or amend AG-10 to state how
   test-suite bursts are to be confined — the current text names them but the launch scripts cannot carry them.
5. **Bookkeeping before any gate.** `runs/goal-ops-hardening-iter-10/status.json` still reads
   `current_step: dev_complete`, `browser_checks_run: false` although the browser lane ran and passed across three
   dispatches; QA/audit/closure lanes have not run since iter-9 (lean depth). Note also that backend pid 2100030
   has since shut down cleanly (`logs/backend.log` tail) — the services need restarting before the next lane.

Carried framework items, unchanged: `merge_ui_test_results.py` drops emphasised `**FAIL**` cells (benign this
iteration — everything PASSed); the `Frontend Present: no` browser-qa-skip misrouting; the pre-existing
`tests/test_db.py::test_create_all_produces_expected_tables` failure.

## Halt Justification (if halting)

Not halting. GOAL_ACHIEVED is blocked (J-06 `partial`; unresolved critical AG-8 dimension). REGRESSION does not
fire (no journey moved passing→failing; the AG-8 entry is a carried, already-acknowledged deferral, not one this
iteration introduced or worsened). STALLED does not fire: J-06's remaining work — the perf re-sweep, the boot
re-measure, and the `--session-live` walkthroughs — is fully agent-owned; only the scope call on the deferred
`/api/backtest` MemoryError is the owner's, and it is not the sole path forward.
