# Iteration 24 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

The new journey J-09 "The backend discloses its own background-compute activity" is genuinely built and
works. I saw the top bar say "background compute running (1)" next to a green "Ready" pill, I read the new
Data Manager panel's own page text in three states, and I checked the numbers it showed against the
database myself: the panel's "1m 15s" is the real, measured length of a real compute, correct to about two
thousandths of a second. All seven older journeys were re-checked this iteration and all seven still pass.

I am still not calling the whole goal done. J-09's own written acceptance list ends with a walkthrough item:
the guided tour that a person can play with `demo.sh ops-hardening --session-live` must include the new
steps. That tour file was never touched this iteration and contains no J-09 steps at all. This is the same
missing item that made the second reviewer reject "goal achieved" back at iteration 22, so I am treating it
the same way now. Two smaller honesty items are also open (see below).

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range | passing | passing | reports/phase-goal-ops-hardening-iter-24-regression-replay-results.md (UT-J-01 PASS) · reports/qa/goal-ops-hardening-iter-24-evidence/J-01-verify.png |
| J-03 No per-run range cap | passing | passing | UT-J-03 PASS (replay) · reports/qa/goal-ops-hardening-iter-24-evidence/J-03-verify.png |
| J-04 Non-blocking boot with visible status | passing | passing | UT-J-04 PASS (replay) · reports/qa/goal-ops-hardening-iter-24-evidence/UT-07-backend-unavailable.png, UT-10-initializing-state.png (evaluator opened both) |
| J-05 Aggregates precomputed at ingest | passing | passing | UT-J-05 PASS (replay) · reports/qa/goal-ops-hardening-iter-24-evidence/J-05-verify.png (evaluator opened: immutable 2025-05-15 snapshot) |
| J-06 Pages load only what they need | passing | passing | UT-J-06 PASS (replay) · reports/qa/goal-ops-hardening-iter-24-evidence/J-06-verify.png |
| J-07 Heavy aggregates never take the service down | passing | passing | reports/phase-goal-ops-hardening-iter-24-ui-test-results.md UT-J-07 (20/20 HTTP 200 inside a real window) · evaluator DB cross-check of the 2026-07-16 window |
| J-08 Backtest evidence serves from storage only | passing | passing | UT-J-08 PASS (replay) · reports/qa/goal-ops-hardening-iter-24-evidence/J-08-verify.png, UT-02-badge-active.png |
| **J-09 Backend discloses its background-compute activity** | (new) | **partial** | reports/qa/goal-ops-hardening-iter-24-evidence/UT-02-badge-active.png (evaluator opened) · DOM captures 013-eval.html / 015-eval.html / 040-navigate.html (evaluator read verbatim) · evaluator SQLite cross-check of `forward_aggregate_cache` |

### What is verified for J-09, and what is not

Verified (I checked each myself, not from the summaries):

- Step 3 — badge: `UT-02-badge-active.png` shows "background compute running (1)" beside "Ready"; the
  historical Backtest page behind it is fully drawn, never a blank frame.
- Step 4 — panel while running: `013-eval.html` contains "as-of 2026-07-17 | elapsed 41.8s | horizons 2/5 |
  dataset r1865-f3954530".
- Step 5 — panel after it finishes: `015-eval.html` contains "No background compute running." and
  "Last outcome | completed | as-of 2026-07-17 | 1m 15s".
- Step 6 — honesty about scope: all three captures carry "Since the last backend restart — this history is
  process-lifetime only, never persisted."; after a real restart the panel correctly says "Last outcome:
  none yet." (`040-navigate.html`).
- AG-3 — the numbers are real: the five stored rows for that compute were written at 12:56:02.744937 …
  12:57:03.884239 UTC; the reported end time is 1.68 ms after the last one; the reported length 75108 ms
  matches its own start time exactly; and "2 of 5 done at 41.8 s" lands exactly after the first two rows.

Not met, and the reason this journey is `partial`:

1. **Walkthrough item missing.** `reports/goal-session-ops-hardening-demo.json` (the file the live
   walkthrough actually plays, established at iteration 23) is unchanged from iteration 23 and holds 12
   steps, none of them for J-09. The iteration plan never listed this item, so nobody built it, and nothing
   in the loop creates it automatically.
2. **The panel claims "nothing is running" when it does not know.** When a health check fails, the app sets
   the value to "unknown" (`apps/frontend/components/readiness-provider.tsx:87`) and the panel prints the
   normal idle sentence (`apps/frontend/app/data/page.tsx:3593,3603`). Small window, but it is a stated fact
   the app has not observed (audit F1).
3. **The speed check is not clean.** J-09 asks that the health check stay at or under 0.1 s at rest. The
   developer's own run recorded a worst sample of 0.127788 s (average 0.103597 s); QA's separate run on the
   same build recorded a worst sample of 0.094604 s. I did not count this against J-06/J-07: the new field
   adds no database work at all (the auditor ran the code to confirm, and I read the code path), and this
   endpoint has sat at about 98% of its allowance since iteration 16. It stays an open question for the
   owner (audit B5).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 no unproven "proven" claims | OK | New wording is "Background compute", "background compute running (1)", "completed", "No background compute running…". No proven/confidence language; I read the panel text verbatim in three DOM captures. |
| AG-2 decision-quality only | OK | No returns, targets, signals or orders anywhere in the 12-file diff (health, config, forward_testing, readiness, 4 test files, badge, provider, api types, data page, config.yaml). |
| AG-3 displayed numbers correct | OK | Re-derived by me from `forward_aggregate_cache`: end time within 1.68 ms of the last stored row, duration exact, horizon counter matches the commit times. |
| AG-4 no overfit edges | OK | No pattern or edge surfaced; this is an operations status field. |
| AG-5 determinism / no lookahead | OK | `compute_forward_aggregates` and `resolved_forward_aggregate_evidence` byte-unchanged (coherence.md row 3; my own read of the diff shows only a set→dict swap in the in-flight registry). |
| AG-6 evidence claims need the referee | OK | No evidence-derived claim added; instrumentation only. |
| AG-7 no hard-coded credentials | OK | scan-report.md CLEAN; the one new config key is an integer. Audit B1 notes a raw error string is served on the local health endpoint — the auditor checked no credential is reachable (local SQLite file URL); recorded as a limitation, not a violation. |
| AG-8 resilience / honest degradation | OK | The new read touches no database (auditor executed it; I read the code). I opened UT-07-backend-unavailable.png: with the backend stopped the app shows "Backend unavailable" and "Nothing is fabricated", never a blank error page. The stored outcome list is capped by config (5). |
| AG-9 offline-deterministic ingest | OK | No provider or network change; every capture I opened shows "provider: seed". |
| AG-10 host resource ceiling | OK | `scripts/` and `project-extensions/` have zero changes (`git status` confirms); the backend was started through `scripts/start-backend.sh` in both the developer and browser-QA runs. |

Coherence audit: **COHERENCE-PASS** (`runs/goal-session-ops-hardening/iter-24/coherence.md`) — one producer,
one endpoint, no new route, no client-side re-derivation. No structural veto.
No `journeys-changed.md`; all seven prior `spec_hash` values still match `goal_gate hash-journeys` exactly.

## Next-Step Recommendation

One short iteration, lean depth, no new features. Do these three things:

1. Add the J-09 steps to `reports/goal-session-ops-hardening-demo.json` — the same job iteration 23 did for
   J-06, J-07 and J-08: `[NEW]`-flagged, accurate, and checked against live behaviour. This is the item that
   blocks "goal achieved".
2. Give the Data Manager panel a separate sentence for "backend unreachable — background-compute state
   unknown", so it stops saying "nothing is running" when it cannot tell (audit F1).
3. Fix the two new tests that compare two separate reads of live state (audit T1) before anyone runs the
   whole test file, so they cannot produce a false alarm later.

Owner items, none of them blocking this iteration: decide whether the at-rest 0.1 s health-check target
should stand as written, given two runs on the same build disagreed (0.128 s worst vs 0.095 s worst);
and backlog card B-1107 (a cap on how many background computes may run at once) stays optional. One item
needs a planner, not a quick patch: a failed thread start would leave the badge saying "running (1)"
forever (audit B2), and fixing it means unfreezing a function this iteration was told not to touch.

In one sentence: approve one more short pass that writes the missing guided-tour steps for the new status
panel and fixes its "unknown" wording, and the goal should be ready to close.
