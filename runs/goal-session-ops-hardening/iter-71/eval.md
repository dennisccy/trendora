# Iteration 71 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

All eight journeys were checked against a live app again, after the previous round checked
nothing. Seven of them work: the backfill jobs, the long-range request, the page loads, the
stored backtest evidence and the new "background compute running" disclosure all showed real,
correct numbers that I re-checked in the database myself. One journey failed badly. While a
real 20-minute data job ran, the app stopped answering its health check 58 times out of 900,
including one unbroken stretch of 165 seconds with no answer at all, and it returned one
server error to the `/data` page. I found the cause in the app's own log: the database
connection pool ran out (30 connections, 30-second wait, then an error). One thing must be
said next to that: the whole check ran on the development launcher, which does not apply the
connection limit the production launcher applies, and two journeys say in plain words that
they must be measured in production mode and never on the development launcher.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | partial (pending-infra) | passing | `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-01-result.png` + results row UT-J-01 PASS; DB: 19 `scanner_runs` in 2026-05-04..2026-05-29; `data_provider_runs` 456-459 all `provider='seed'` |
| J-03 No per-run range cap | partial (pending-infra) | passing | `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-03-result.png` + results row UT-J-03 PASS (412-day span accepted, "283/283 dates") |
| J-04 Non-blocking boot with visible status | partial (pending-infra) | passing | `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-04-result.png` (banner "GO — today's board is current." on `/data`) + results row UT-J-04 PASS; steps 4-6 carried on evidence durability (boot/crash code unchanged) |
| J-05 Aggregates are precomputed at ingest, never on the fly | partial (pending-infra) | partial | `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-05-result.png` + results row UT-J-05 PASS; DB: `scanner_runs` id 2974 = 2005-07-08, `created_at` 2026-08-12 17:49:56.406, 149 result rows. **Step 4 ("stays responsive throughout") failed on this same job — see J-07** |
| J-06 Pages load only what they need | partial (pending-infra) | passing | `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-06-result.png` + results row UT-J-06 PASS (11 pages); DB: `daily_prices` 1996-01-02 → 2026-08-03 / 591 symbols matches the displayed captions |
| J-07 Heavy aggregates never take the service down | partial (pending-infra) | **failing** | `runs/goal-ops-hardening-iter-71/browser-qa-drill/j07-health-poll.csv` (recomputed by me: 900 polls, 58 non-answers, longest outage 33 polls = 165 s, worst answered 4.659 s) + results row UT-J-07 FAIL + `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-07-fail.png` |
| J-08 Backtest evidence serves from storage only | partial (pending-infra) | passing | `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-08-result.png` (as-of 2026-08-03, real scorecard, no skeleton) + results row UT-J-08 PASS |
| J-09 The backend discloses its own background-compute activity | partial (pending-infra) | passing | `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-09-result.png` + results row UT-J-09 PASS; DB: `forward_aggregate_cache` rows for as-of 2026-07-31 committed 17:56:26 → 18:04:30 |

Deterministic replay lane: 2/8 PASS, 6 FAIL — every one of the six with
`net::ERR_CONNECTION_REFUSED at http://localhost:3255` (the QA frontend was swept away
mid-run). The merged file is authoritative and its dated reconciliation footer overturns
J-04, J-05, J-06, J-08 and J-09 as golden-script false positives. J-07's FAIL in the merged
file is NOT that: it comes from the LLM lane's own 900-poll drill, which I recomputed from
the raw CSV.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unproven presented as proven | OK | Backend-only diff (7 files, zero `apps/frontend/`); no proven-language added. The `/backtest` and Regime-Lab frames I opened both render their honest "Nothing is fabricated" / survivorship-bias disclosures. |
| AG-2 decision-quality only | OK | No return promise, price target, signal or order path in the diff (`readiness.py`, `health.py`, `config.py`, `config.yaml`, 3 test files). |
| AG-3 displayed numbers correct | OK | Re-derived by me in the DB: run 2974 = 2005-07-08 `created_at` 17:49:56.406 (matches the UI's "Scanned 2026-08-12 17:49:56"); run 748 = 2026-05-29 scanned 2026-07-20 (re-serve, not recompute); 19 May runs; 591 symbols; 1996-01-02 → 2026-08-03; 2973 → 2974 snapshot dates across the two frames. |
| AG-4 no overfit edges | OK | No referee, ledger or claim path touched. |
| AG-5 determinism / no lookahead | OK | No scoring or forward-return code in the diff; the new stamp is `time.monotonic()`, explicitly chosen so a clock change cannot manufacture staleness. |
| AG-6 referee gate | OK | No evidence-derived claim introduced this round. |
| AG-7 no hard-coded credentials | OK | `iter-71/scan-report.md`: CLEAN, no secret/dependency/license finding on added lines. |
| AG-8 resilience / no unbounded loads | OK, with one flagged item | No data-basis widening this round, and no new query or whole-table load (coherence.md traced the change as a cache read plus one derived field). One HTTP 500 was served (`GET /api/data`, `QueuePool limit of size 10 overflow 20 reached ... timeout 30.00`). I considered scoring this critical under AG-8 and rejected it: AG-8's trigger is a widened basis and the basis is byte-identical to prior rounds. It is logged minor as iter-71/c and carried by J-07's failing status. What the `/data` page renders during that 500 was never captured — named as next-round work. |
| AG-9 offline-deterministic ingest | OK | All 8 of this round's ingest jobs are `data_provider_runs` ids 453-460, every one `provider='seed'`, `status=ok`. Today's rows group to `[('seed', 29)]` — no other provider. |
| AG-10 host resource ceiling | OK | `git status --porcelain -- config.yaml project-extensions/ scripts/` shows ONLY `config.yaml`, whose entire diff is the one added `max_stale_intervals: 3` line; `memory_cap_mb: 8192` and `malloc_arena_max: 2` untouched. Heavy compute launched via `scripts/dev.sh` — a launcher AG-10 names explicitly — and the log echoes its subshell applying `ulimit -v $((MEMORY_CAP_MB * 1024))`, `MALLOC_ARENA_MAX` and the HOST-GUARD block. No cap removed, weakened or bypassed. |

New minor findings logged this round: iter-71/a (dev-mode stack used for journeys that forbid
it), /b (`dev.sh` omits the production server guards and the persistent logfile), /c (the 500 +
165 s outage), /d (TC-5 missed a second round), /e (a QA citation to a file that does not
contain the cited line), /f (walkthroughs still unrecorded), /g (eleventh over-budget round),
/h (J-06 steps 2-3 not performed). Closed this round: iter-70/a, /b and /d. Ledger: 238 total,
120 unresolved, **0 unresolved critical**.

Coherence: **COHERENCE-PASS** (0 blocking, 2 advisory) — no consolidation pass is mandated.
Review: **PASS**. Scan: **CLEAN**. No `journeys-changed.md`, and I confirmed all eight
`spec_hash` values are unchanged from the prior history, so no goal-edit drift exists.

## Next-Step Recommendation

Run the next round at full depth and give it one job: find out how bad the health-check outage
really is, and fix it.

1. **Repeat the measurement properly.** Start the app with `scripts/start-backend.sh` and
   `scripts/start-frontend.sh`, not `scripts/dev.sh`. The development launcher does not apply
   the limit on how many requests may be in flight at once (production allows 64), and the
   error the app actually returned was "no free database connection after 30 seconds" — which
   is exactly what that limit exists to prevent. Start the health poller at least 2 seconds
   *before* the job, which was asked for last round and missed twice now.
2. **Make the app hold up when two heavy jobs overlap.** The failure needs two things at once:
   the long `factor_lab_all_warm` stage (607 seconds) and a background scorecard computation a
   user triggered by opening `/backtest`. Bounding how many heavy computations may run at once
   is card B-1107, which the owner set aside — so ask the owner, or take the paths that do not
   need him: give the health check its own guaranteed database connection, or size the pool to
   the allowed number of in-flight requests.
3. **Re-check this round's own change for a share of the blame.** When the cached readiness
   value is older than 1.5 seconds, every health request now computes it again itself, one at
   a time behind a single lock, and the code never re-checks whether someone else already
   refreshed it. Under load that can feed on itself. Add the re-check, or serve the slightly
   old value and say how old it is instead of blocking.
4. **Make `scripts/dev.sh` match production** for the request limit, the keep-alive timeout and
   the persistent log file. It already matches on the memory caps. This is launcher work the
   goal already calls in-scope, and it is why the log for this whole round is missing.
5. **Small and written down:** capture what `/data` shows to a person while the backend returns
   that error; record the page timings J-06 asks for; record the walkthroughs (J-05 for the
   13th round, J-07's new steps for the 2nd).
6. **Still waiting on the owner** (nothing below blocks the work above): the 2-second
   health-check promise question, now 23 rounds old and newly urgent; permission to fix the
   one-line ordering bug in `scripts/automation/browser-qa-phase.sh`; and a cost decision — this
   round again ran about 2.9 times over its time budget, the eleventh in a row.

In one sentence: approve a full-depth round that re-measures the outage on the production
launcher and fixes the database-connection exhaustion behind it, and please answer the
2-second health-check question so this last journey can finally be closed or re-scoped.
