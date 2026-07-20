# Iteration 2 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-05 (ingest-time aggregate maintenance served from a new persisted `coverage_snapshot` table) and
J-04's remaining acceptance (enforced `ulimit -v`/`MALLOC_ARENA_MAX` + persistent `logs/backend.log`)
are genuinely delivered: cold `/data` serves coverage from storage in 0.029–0.086 s (vs a ~9.4 s
pre-fix baseline) with zero request-path whole-table loads on the default path, verified across the
browser lane, a real-process launch-script test suite, live `/proc` reads, and an independent audit
code-trace + test re-run. The review-pass-1 CRITICAL (as-of switcher serving false-zero coverage,
AG-3) was fixed intra-iteration and re-verified byte-exact. Goal is not achieved — J-05 step 4
(health/memory during a *heavy* job) was never measured live, J-06 is untouched (out of scope), and
an out-of-scope `fetch`-path coverage-freshness gap (audit B1) must be closed before any GOAL_ACHIEVED.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | browser-qa UT-J-01 PASS; `reports/qa/goal-ops-hardening-iter-2-evidence/J-01-zero-work-vs-success.png` (productive 2025-05-27→29 `dates_total=3`/3 created vs zero-work re-run "no new snapshots"/3 already-snapshotted, breakdowns add up, persisted) |
| J-03 | passing | passing | browser-qa UT-J-03 PASS; `.../J-03-large-range-accepted.png` (412-cal-day request accepted, no cap, `dates_total=283`; `max_range_days` removed from config.yaml) |
| J-04 | partial | passing | TC-15/16/17 real-process `test_start_backend_script.py` (ulimit=6144 MB, `MALLOC_ARENA_MAX=2`, `logs/backend.log` boot events + SIGKILL abrupt-end); QA live `/proc/<pid>/{limits,environ}`; `.../UT-06-empty-state.png` (phase-aware "Initializing… history 51/89" badge); `.../UT-04-result.png` (fast cold restart, no prefill) |
| J-05 | failing | partial | Steps 1/2a/2b/3 verified: `.../UT-02-live.png` (Refreshed: latest snapshot, coverage, membership timeline, market phase, research hot keys, live+persisted), UT-09 (scanner-runs lists 2025-05-30 + leaderboard), `.../UT-04-result.png` (cold-restart from storage), TC-04 unit (market-phase computed once at ingest, 0 on re-read). **Gap: step 4 (health responsiveness + VmPeak during a HEAVY job, TC-11/TC-12) never measured live** — audit T1, review MINOR |
| J-06 | failing | failing | Out of scope this iteration (measurement capstone, deferred per goal.md build order); no J-06 work — carries iter-0 status |

Status changes verified by opening evidence: J-04 (partial→passing), J-05 (failing→partial). Stable
spot-checks J-01, J-03 both corroborated their recorded passing status (no contradiction → no widen).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (no unbacked proven/confident language) | OK | No edge/proven claims added; Refreshed line names aggregates only. Loop-mechanics: J-01…J-06 carry no Evidence Claims. |
| AG-2 (decision-quality only) | OK | No order/price-target/buy-sell code in diff. |
| AG-3 (displayed numbers correct) | OK for journeys; 1 open dimension gap | As-of-switcher CRITICAL (review pass-1) FIXED + re-verified (UT-05 byte-exact) → resolved. **B1**: a `fetch` that lands bars blanks the DEFAULT `/data` coverage to false all-zeros until restart/backfill — out-of-scope path, breaks no Must-have journey, self-heals, disclosed; recorded unresolved, top next-step (see below). |
| AG-4 (no overfit edges) | OK | No proven-pattern claims. |
| AG-5 (determinism / no-lookahead) | OK | Aggregates re-served from storage byte-identical (TC-8), never re-derived; no lookahead. |
| AG-6 (no evidence-claims without referee) | OK | No evidence-derived claims this iteration. |
| AG-7 (no hard-coded credentials) | OK | scan-report.md CLEAN — no secret findings on added lines. |
| AG-8 (no unbounded whole-table serving loads) | OK (improved) | Default `/data` now serves from storage; monkeypatched tests raise if prefill fires on request path. Self-heal is bounded one-time-per-legacy-date on EXPLICIT as_of only (coherence advisory, not default path). |
| AG-9 (offline-deterministic ingest, no network) | OK | `test_finalize_hook_makes_no_network_call` (zero `socket.connect`); scan-report no new deps. |

Coherence: **COHERENCE-WARN** (advisory only — does not block GOAL_ACHIEVED). One advisory: the
explicit-as_of self-heal computes live on the request path for a narrow gated historical-legacy-date
case, slightly overshooting the blueprint's unqualified "never a live compute on this serving path" —
same canonical module/function/endpoint, so no duplicate-source risk; recommended blueprint wording
tightening next iteration. scan-report.md: CLEAN.

## Next-Step Recommendation

Full-depth iteration targeting, in priority order:
1. **Close audit B1 (AG-3 dimension, #1).** Refresh `coverage_snapshot` for the current stamp at the
   end of ANY count-changing ingest kind (ingest-time → AG-8-safe), gated to skip when
   `_membership_dataset_version` is unchanged so a zero-work offline fetch pays nothing; fold in the
   B2 stale-stamp prune. Do NOT fix by extending the `as_of=None` self-heal — that path must stay on
   the zero-query sentinel to preserve this iteration's cold-boot no-whole-table guarantee.
2. **Close J-05 step 4 (measurement, T1).** Run one real heavy `rebuild`/multi-day backfill and record
   TC-11 (`/api/health` ≤1 s throughout) + TC-12 (`VmPeak` under the now-enforced 6144 MB cap) into
   `reports/perf-budgets.md` Item J — watch the new per-date coverage loop's cost on a full rebuild
   (~757 per-date computes). This promotes J-05 partial→passing.
3. **J-06 capstone** — the cross-page time-to-interactive + on-load-latency budget pass over all pages,
   recorded in `reports/perf-budgets.md`, folding in this iteration's preliminary cold-`/api/data`
   number. J-06 is the last failing Must-have journey.

## Halt Justification (if halting)

Not halting — CONTINUE. Explicitly considered and rejected REGRESSION: (a) no prior-passing journey
failed — J-01/J-03 both re-verified passing (UT-J-01/UT-J-03 PASS); (b) the as-of-switcher AG-3
CRITICAL was fixed intra-iteration and re-verified (resolved); (c) B1 touches the AG-3 dimension but
breaks no Must-have journey (AG-3 is journey-scoped; no J-01/J-03/J-04/J-05 exercises
fetch-lands-bars→default-coverage), self-heals with no data loss and no byte-identity/AG-8/AG-9
violation, and is a disclosed, reasoned scoping tradeoff (the naive fix re-introduces the worse
cold-boot whole-table CRITICAL J-05 exists to remove) with a fix unanimously endorsed by
audit+QA+ux-regression — the most skeptical reviewer (audit, PASS_WITH_GAPS) explicitly recommended
"Proceed." The loop must continue regardless (J-06 unbuilt), and B1 is a queued follow-up, not a
human-adjudication-required halt. STALLED rejected: clear productive next work exists, no human-owned
blocker. GOAL_ACHIEVED rejected: J-05 partial, J-06 failing.
