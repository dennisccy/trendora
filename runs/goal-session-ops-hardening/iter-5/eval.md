# Iteration 5 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The iteration's substantive deliverable — the `ForwardAggregateCache` fix for the confirmed
`GET /api/backtest` violation (34.77s → 0.138s, ~252×, byte-identical, verified across review/QA/audit
lanes) — is genuinely correct and shippable. But the target journey J-06 does NOT pass: TC-02 shows the
Dashboard's `/api/indexes?full=true` at 1.68–2.19s in a real browser (3/3 trials) against its ≤1.5s
committed budget — a browser HTTP/1.1 connection-queuing gap curl-based measurement (0.79–0.95s) never
surfaced. QA=FAIL, closure=CLOSURE-FAIL, ux-regression=UX-REGRESSION-FAIL, audit=PASS_WITH_GAPS all
converge and the audit explicitly says "do not close J-06 as passing this iteration." No journey
genuinely regressed and no anti-goal was violated, so this is a CONTINUE toward a fresh iteration that
resolves the Dashboard budget and restores clean regression evidence.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | `reports/qa/goal-ops-hardening-iter-5-evidence/J-01-verify.png` — replay steps 1-5 PASS (incl. the "2 non-trading" zero-work explanation = J-01's actual acceptance); step-6 proxy ("2026-05-15" on `/scanner-runs`) missed but adjudicated a **stale golden-script assertion**, not a regression (audit T1 DB query: the 2026-05-15 run exists; runs-display path untouched in the diff; screenshot shows a healthy 750-row run table headed by 2026-07-17…07-10) |
| J-03 | passing | passing | `reports/qa/goal-ops-hardening-iter-5-evidence/J-03-verify.png` — deterministic replay PASS; spot-check shows `/data` coverage rendering (1996-01-02→2026-07-17, universe 540) |
| J-04 | passing | unknown | Not replayed this cycle (coverage gap — only J-01/J-03 ran). No failing evidence; shared `_refresh_ingest_aggregates` was modified additively. Carry prior passing; re-verify next iter |
| J-05 | passing | unknown | Not replayed this cycle (same coverage gap). Audit notes the ingest-time warm *reinforces* J-05's "precomputed at ingest" claim; still no fresh replay. Carry prior passing; re-verify next iter |
| J-06 | failing | failing | `reports/qa/goal-ops-hardening-iter-5-evidence/TC-02-dashboard.png` — `/api/indexes?full=true` 1678/2185/2054ms > 1.5s budget, 3/3 browser trials (backend curl in-budget; browser 6-conn/origin queuing). TC-10 backtest fix confirmed working (115–275ms) but J-06 requires ALL 11 pages within budget |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 / AG-4 / AG-6 (proven-language, referee) | OK | J-06 carries no Evidence Claims; pure perf work, no proven-language introduced |
| AG-2 (no buy/sell / orders) | OK | none observed |
| AG-3 (displayed numbers correct) | OK | Cache serves byte-identical values to `compute_forward_aggregates` (unit test + audit live spot-check on 176,447-obs DB); honest cold-miss sentinel; UT-01-fail.png shows an honest "Backend unavailable — no figures shown rather than fabricated" contained card |
| AG-5 (no-lookahead / determinism) | OK | Cache keyed on `(horizon, asof_key, dataset_version)`; computation unchanged, no lookahead added |
| AG-7 (no hardcoded secrets) | OK | scan-report CLEAN; no config/env file in the 9-file diff |
| AG-8 (data-scale resilience) | OK | Fix REMOVES a 5×~1.7M-row per-request scan (strengthens AG-8); `/api/indexes` is a config-fixed small index set, not an unbounded scan; over-budget panel degrades to an honest `animate-pulse` skeleton, never blank |
| AG-9 (offline-deterministic ingest) | OK | Pure DB-read cache; `test_finalize_hook_makes_no_network_call` passed; no new dependency/manifest entry |

Coherence: **COHERENCE-PASS** (no new producer/endpoint; blueprint Data Contract row amended in place).
scan-report: **CLEAN**. No unresolved anti-goal violation; the 3 prior (iter-1/iter-2 AG-3) remain resolved.

## Next-Step Recommendation

Full-depth fresh iteration (audit §5 concurs), two scoped items:
1. **Resolve the Dashboard `/api/indexes?full=true` browser-concurrency budget (audit B1).** Choose a real
   latency fix (HTTP/2 on the uvicorn launcher OR coalesce the Dashboard's 10-13 near-simultaneous on-load
   calls) OR a documented browser-realistic budget re-commit in `reports/perf-budgets.md` — and fold
   `/api/data/availability` (same class, ~2.9–3.0s in-browser) into the same decision. Then re-run QA's
   full plan incl. TC-16 to a clean J-06 pass.
2. **Restore clean regression evidence (audit T1/T2).** Fix J-01's `/scanner-runs` step-6 proxy to be
   robust to the now-750-row run history (or re-point it at data the submitted backfill actually produces),
   re-run J-01, and run the skipped **J-04/J-05** golden scripts (both depend on the modified
   `_refresh_ingest_aggregates`) — moving them out of `unknown`.
- Before merging THIS iteration's backend code, run `pytest tests/test_api_backtest.py tests/test_mcp_window.py -v`
  to completion (reviewer/audit T3 — the `loaded_engine` fixture suite was not run this cycle).
- **Closure-gate (for the eventual GOAL_ACHIEVED):** produce BOTH J-05's and J-06's `[NEW]`
  `demo.sh ops-hardening --session-live` walkthroughs, or have the human accept their deferral.

## Halt Justification (if halting)

N/A — not halting. Not GOAL_ACHIEVED (J-06 failing; J-04/J-05 unknown). Not REGRESSION (J-01's replay miss
is a proven-stale proxy assertion, not a product regression — data intact, code path untouched, actual
acceptance steps 1-5 passed; no anti-goal violated). Not STALLED (all blockers are dev/agent-owned and
tractable — no credentials/network/paid service). Not ESCALATE (already full depth; review=PASS_WITH_NOTES,
so no fail-open; J-06 is a first-attempt target, not a 2+-iter repeat failure).
