# Iteration 45 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

J-103 (Severity-velocity × Regime forward-return study) and J-104 (research-labs route-split + caching/query-bound) are genuinely BUILT and CORRECT: J-103 renders live with real figures, the verbatim honest verdict, count-coherent N= drill-down, and a config-backed matrix; J-104's hub/route-split + lazy-load + byte-identical caching are proven by isolated tests. The browser-QA FAIL (19/25) is NOT a code regression — all four P1 failures are explained: UT-09 is a selector false-negative (QA curled the WRONG param `?asof=` instead of the endpoint's `?as_of=`; the engine's as-of filter is proven by `test_as_of_filter_shrinks_pool_no_recompute` passing), and UT-03/UT-04 (+ the UT-24/UT-25 skips) are a SATURATED/hung live backend (PID 72189, still consuming ~25% CPU at evaluation time from the earlier event-study hammering), not iter-45 code — `test_research.py`+`test_samples.py` (event-study, downtrend, recovery, samples count-coherence) pass 108/108 in isolation. This is NOT GOAL_ACHIEVED only because the standing flushed-GREEN full-suite gate is unmet (the suite hung at 98% with the documented warm-up/contention `EEEE FF E` tail) and a clean live re-render is owed — the established iter-30→31 / iter-36→37 / iter-42→43 lean-reverify pattern.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-103 Severity-velocity × Regime study | failing | passing | reports/qa/.../iter-45-evidence/UT-02-result.png (3×3 matrix), UT-07-result.png (N=241 drill-down == chip), UT-05-5d.png (horizon switch n=241→n=247), UT-06 (verdict + 4 caveats verbatim), UT-18-result.png (samples cohort); test_severity_velocity.py 15/15 incl. as_of-filter + cache byte-identity |
| J-104 Research-labs reliability + route split | failing | passing | reports/qa/.../iter-45-evidence/UT-01-result.png (7-card hub, 0 research calls), UT-23 (all 7 routes HTTP 200), UT-19 (one heavy fetch fires), UT-15/16 (sidebar highlight); test_research.py+test_samples.py 108/108 isolation (byte-identity + bounded scan) |
| J-29 Setup & Pattern event study | passing | passing (carried; NOT regressed) | test_research.py event-study legs PASS in isolation; UT-04 500 was hung-backend contention (UT-04-fail.png shows honest "Backend unavailable" no-fabrication state), not code |
| J-32 Research as-of/all-history toggle | passing | passing (carried) | severity-velocity As-of mode UI toggles (UT-09); as_of engine filter proven by test_severity_velocity.py |
| J-63 Event-study Episodes/Pooled view | passing | passing (carried) | test_research.py episodes/pooled legs PASS in isolation |
| J-65 N= chip → samples new tab | passing | passing (carried) | UT-07-result.png severity-velocity N= chip opens /research/samples (new tab) total==N; test_samples.py count-coherence PASS |
| J-91 Downtrend-opportunity study | passing | passing (carried) | UT-12-result.png route loads; test_research.py downtrend count-coherence + as-of-bound legs PASS in isolation |
| J-72 Derived-once cache performance contract | passing | passing (carried) | TC-12 cache byte-identity (md5 65e63c9c repeats); test_severity_velocity.py factor-combination + regime-setup-pattern cached-byte-identical PASS |
| J-77 Regime × Setup × Pattern study | passing | passing (carried) | UT-10-result.png route loads; test_research.py rsp legs PASS in isolation |
| J-101 Dashboard cross-view consolidation | passing | passing (carried; not re-rendered — backend-research-only diff) | no apps/dashboard diff this iter; byte-unchanged |
| J-102 Severity-velocity line + tooltip | passing | passing (carried; not re-rendered) | severity_velocity engine read verbatim by J-103; market_phase.py adds only a public accessor |
| J-97 Two-pane synced cross-view | passing | passing (carried) | byte-unchanged dashboard surface |
| J-98 At-a-glance restructure | passing | passing (carried) | byte-unchanged dashboard surface |
| J-18 One date control (CRITICAL) | passing | passing | TC-15 / QA: 0 `input[type=date]`; severity-velocity page reads useResearchControls (no new date state) |
| J-07 Risk-Off → 0 Actionable (CRITICAL) | passing | passing | no scoring/regime/scanner/gate code touched (research-labs-only diff); backend /api/runs invariant intact |
| J-22 / J-23 / J-24 | unknown (blocked-NA) | unknown (blocked-NA) | data-walled, NON-VETOING per goal.md:105-108 |

UT-09 (severity-velocity as-of) is recorded as a browser-QA FALSE-NEGATIVE, not a journey failure: the QA curled `?asof=2022-12-31` (no underscore) against an endpoint declaring `as_of: Optional[str] = Query(...)`. FastAPI ignored the unrecognized `asof` param → `as_of=None` → correct all-history response with `asof_date: null`. The real frontend (`fetchSeverityVelocity` → `withAsOf` → `as_of=`) sends the correct param; `test_severity_velocity.py::test_as_of_filter_shrinks_pool_no_recompute` PASSES, proving the filter narrows the pool.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Single source of truth (J-06) | OK | severity_velocity read verbatim from `market_phase.severity_velocity_by_date`; forward_returns read verbatim from `ForwardReturn`; no recompute (COHERENCE-PASS Part A) |
| No recompute in the read path | OK | J-103 is a pure GROUPING; J-104a wraps existing compute fns in a cache (byte-identical); J-104b bounds a query — no new computation path |
| Snapshots immutable | OK | no scanner_runs/scanner_results/*_scores mutation; reuses existing EventStudyCache table |
| No lookahead | OK | forward returns from bars > D by construction; as_of filters ScannerRun.asof_date <= D; test_observation_set_excludes_warmup_head + as_of-filter tests PASS |
| Exactly one date selector (J-18) | OK | 0 native date inputs (TC-15); severity-velocity As-of toggle is a MODE, not a second date state |
| No fabricated data | OK | zero-N cells → honest NA (UT-17); failed fetches → honest "Backend unavailable", no fabricated figures (UT-03/UT-04 frames) |
| No order/execution path (critical) | OK | grep of diff: no BUY/SELL/order/broker/execute; "Research-only · no orders" header intact |
| Every feature navigable; no second home | OK | all 7 labs reachable ≤2 clicks via /research hub + sidebar startsWith highlight (COHERENCE-PASS Part B) |
| Honest limitations surfaced | OK | verdict states "NOT supported" + "bounce, not continuation" + survivorship + bull-dominated + underpowered-for-crashes (UT-06) |
| No magic numbers / no new table | OK | EventStudyCache reused (no new table=True); dev's test_no_magic_numbers + test_db PASS (handoff); config-backed family/sign vocabularies |
| No committed secrets / paid-SaaS | OK | diff scan clean (no api_key/secret/token/stripe/openai) |

No new anti-goal violation. The lone ever-recorded violation (iter-20, minor magic-number) stays resolved since iter-21.

## Next-Step Recommendation

iter-46 LEAN live re-verification + flushed-suite confirmation (NO code rework — J-103/J-104 are correct, byte-identity + as-of filter proven by isolated tests). This is the iter-36→37 / iter-42→43 pattern, fifth repeat.
1. FIRST restart the hung live backend cleanly (kill PID 72189; bring up :8835 and WAIT for `GET /api/health` "ready" so warm-up finishes) — the iter-45 browser-QA ran against a saturated backend, which is the sole cause of UT-03/UT-04/UT-24/UT-25.
2. PLAN the Playwright fallback up front (Chrome MCP CDP has emptied/contended the dir on iters 38/39/40/42/45); md5sum the dir FIRST; NEVER concurrently probe heavy /research/* endpoints (one heavy fetch at a time — the J-104 invariant; MEMORY pool-exhaustion).
3. Re-capture the relocated labs on a QUIET backend with figures+N= chips actually rendered (not the "Backend unavailable" banner): J-29 event-study (UT-04 re-do), J-25/J-26 factor-lab (UT-03 re-do), J-77 regime-setup-pattern, J-91 downtrend, recovery-turn-edge; assert each relocated lab's figures are byte-identical to pre-split + its N= drill-down still works (J-51/J-65 count-coherence).
4. Re-verify J-103's As-of mode in the BROWSER by toggling "As of date" at ?asof=2022-12-31 and confirming the rendered N values DECREASE (do NOT re-curl `?asof=`; the correct param is `?as_of=`, which the frontend sends automatically) — close the UT-09 false-negative with positive rendered evidence.
5. Required-still-passing live smoke: J-18 (0 native date inputs, CRITICAL), J-07 (Risk-Off → 0 Actionable, CRITICAL), J-101/J-102/J-97/J-98 (Dashboard cross-view + severity-velocity line/tooltip unchanged).
6. Suite gate: confirm the FLUSHED full-suite `0 failed, EXIT 0` from the pump's nohup-async re-run on the now-quiet host BEFORE any GOAL_ACHIEVED candidacy — re-run any isolated test_warmup.py / test_watchlist_persistence.py E/F (the documented slow-boot/warm-up contention flake) before attributing it. The iter-45 `.sssEEEEFFE.` tail is in those warm-up/watchlist modules, NOT in the touched research code (test_research+test_samples 108/108, test_severity_velocity 15/15 pass in isolation).

After the relocated labs + J-103 As-of re-render green on a quiet backend AND the full suite flushes 0-failed, the next evaluation is a sound GOAL_ACHIEVED candidate: every buildable Must-have (J-01..J-21, J-25..J-104) positive-evidenced; J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per goal.md:105-108). Do NOT re-trigger the J-85 kind:rebuild (~11h destructive; data is correct).
