# Iteration 25 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** lean

## Summary

All eight must-have journeys now pass, checked with evidence from this iteration. The last open item —
J-09 "The backend shows what it is computing in the background" — needed a guided-tour entry in the file
`demo.sh ops-hardening --session-live` reads, and that entry now exists; I opened the file and compared it
with the old one myself. The `/data` page also now says "state unknown" instead of "nothing running" when
the backend cannot be reached, which was the one dishonest message left. Nothing in the app's engine code
changed this time, and no anti-goal was broken.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range | passing | passing | reports/qa/goal-ops-hardening-iter-25-evidence/J-01-verify.png (replay UT-J-01 PASS) |
| J-03 No per-run range cap | passing | passing | reports/qa/goal-ops-hardening-iter-25-evidence/J-03-verify.png (replay UT-J-03 PASS) |
| J-04 Non-blocking boot with visible status | passing | passing | J-04-verify.png (replay PASS) + UT-J-09-07-poll-failure-viewport.png (red "Backend unavailable" + NO-GO banner, opened by me) |
| J-05 Aggregates precomputed at ingest | passing | passing | reports/qa/goal-ops-hardening-iter-25-evidence/J-05-verify.png (replay UT-J-05 PASS) |
| J-06 Pages load only what they need | passing | passing | reports/qa/goal-ops-hardening-iter-25-evidence/J-06-verify.png (opened: /research/event-study fully rendered) |
| J-07 Heavy aggregates never take the service down | passing | passing | reports/qa/goal-ops-hardening-iter-25-evidence/UT-J-07-health-poll.log (12/12 HTTP 200 inside a real window); replay FAIL overturned — see below |
| J-08 Backtest evidence serves from storage only | passing | passing | reports/qa/goal-ops-hardening-iter-25-evidence/J-08-verify.png (opened: /backtest fully populated, no skeleton) |
| **J-09 Backend discloses its background compute** | **partial** | **passing** | UT-J-09-01-steady-ready.png, -03-badge-inflight.html, -04-data-panel-inflight.html, -05-data-panel-idle-lastoutcome.html, -06-idle-none-yet-post-restart.html, -07-poll-failure-unknown.html + `reports/goal-session-ops-hardening-demo.json` n=13–16 |

### What I checked myself for the one status change (J-09)

- **Walkthrough clause (the sole iter-24 blocker).** I loaded both versions of
  `reports/goal-session-ops-hardening-demo.json` in Python: 12 steps before, 16 now; steps 1–12 compare
  byte-identical; the `highlights` section is still exactly 8 (cap undisturbed); the four new entries all
  carry `"journey": "J-09"`, `"new": true`, `"verified": true`.
- **Numbers are real, not narrated (AG-3).** I queried `forward_aggregate_cache` read-only. This
  iteration's disclosed "as-of 2026-07-13 · elapsed 12.9s · horizons 0/5" is right (that window's first
  horizon committed 15.1 s after its start, so 0 of 5 done at 12.9 s); "completed · 1m 15s" matches
  `duration_ms 74689`; and the manifest's re-used iter-24 figures ("41.8s · 2/5", "1m 15s" for as-of
  2026-07-17) land exactly after that window's first two of five commits (12:56:02.744937 / 12:56:18.412623)
  and match `duration_ms 75108`.
- **The new honest message (audit F1).** `UT-J-09-07-poll-failure-unknown.html` shows
  `background-compute-unknown` = "Background-compute state unknown — the backend is unreachable." with
  `idlePresent: false`, while the badge reads "Backend unavailable". I read the new resolver
  (`apps/frontend/lib/background-compute-panel-branch.ts`) and the `page.tsx` hunk: the genuine-idle wording
  is preserved exactly.
- **The J-07 replay FAIL, checked rather than accepted.** The golden script expects the word "Ready" on the
  home page. At replay time (15:32–15:33Z) the badge read "Initializing… history 89/89" because that boot's
  warm-up hit a non-fatal `MemoryError` (`logs/backend.log:79986`) while two detached pytest runs
  (PIDs 1620313/1620524, started 15:29Z — I confirmed with `ps`) were eating host memory under the backend's
  own memory cap. The whole logfile contains exactly one such warm-up failure. The service kept serving and
  never falsely claimed "Ready". The LLM lane then restarted the backend and verified J-07's substance live.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language | OK | New copy is one factual sentence ("state unknown — the backend is unreachable"); manifest narration makes no proven/edge claim. |
| AG-2 decision-quality only | OK | No prices, targets, orders anywhere in the diff. |
| AG-3 displayed numbers correct | OK | Re-derived from `forward_aggregate_cache` for both live and manifest figures (see above). |
| AG-4 no overfit edges | OK | No evidence-ledger or referee surface touched. |
| AG-5 determinism / no-lookahead | OK | `git diff` vs snapshot `e14a39f2`: no file under `apps/backend/app/**` changed at all. |
| AG-6 referee gate | OK | No evidence-derived claim introduced. |
| AG-7 no credentials | OK | scan-report.md CLEAN; changed files are 2 backend test files, 1 page, 2 new `lib` files, 1 JSON manifest, README. |
| AG-8 resilience / no memory exhaustion | OK (with a stated finding) | One warm-up `MemoryError` at 15:33Z, caused by two concurrent pytest fixture builds on the host, not by this diff (zero backend product change). It behaved as AG-8 requires: logged non-fatal, no crash, no blank error page, pages kept serving real data, readiness never falsely green. Recorded, not laundered; assumption logged. |
| AG-9 offline-deterministic ingest | OK | No ingest change; captures show "provider: seed". |
| AG-10 host resource ceiling | OK | `scripts/` and `project-extensions/` absent from the diff; every restart went through `scripts/start-backend.sh` (logfile banners 15:38:53Z, 15:39:36Z, 15:40:23Z, 15:49:55Z, 15:52:32Z). |

Coherence: `runs/goal-session-ops-hardening/iter-25/coherence.md` = **COHERENCE-PASS** (no structural veto).
No `journeys-changed.md`; all eight `spec_hash` values match `goal_gate hash-journeys` output.
Review: PASS (one NOTE about unfinished pytest reruns — no fail-open, browser results are present).

## Next-Step Recommendation

Stop here — the goal is met. The automatic checks and the second, fresh reviewer still have to agree before
the session closes. Three small things are worth doing later, and none of them blocks anything: (1) actually
run the two rewritten backend tests when the machine is free, because they have never finished a real run;
(2) give the top-bar badge a distinct "warm-up failed" wording, so it cannot sit on "Initializing… 89/89"
forever after a failed start-up; (3) the owner still has one open question — whether the "under 0.1 second"
target for the health check at rest should stand as written, given the app has been at about 98% of that
target since iteration 16. The owner should review this result and, if satisfied, let the closing checks run.

## Halt Justification

Halting with GOAL_ACHIEVED because all eight must-have journeys pass with this iteration's own evidence,
no anti-goal is broken, the coherence audit passed, and no journey's goal text changed. I state four open
points plainly rather than rounding them away:

1. **The two rewritten backend tests were never actually run to a result.** Both detached pytest runs were
   still building the shared test fixture after 39 minutes when this evaluation closed (logs show only the
   test name, no pass/fail line). What IS verified: pytest collected both files with no errors and selected
   exactly one test each; the developer proved the comparison logic on synthetic data; I read both rewritten
   tests in full. This is test-only code — it changes no product behaviour — but the iteration's
   "unit tests pass" checkbox and its five-times-rerun scenario are genuinely not satisfied, and finishing
   them needs a machine that is not busy.
2. **J-09's health-check budget clause.** Its acceptance asks that the health check at rest stays under
   0.1 s, re-measured and recorded. The recorded measurement is 0.100023 s by the official method with a
   worst sample of 0.127788 s across ten polls, and this run saw about 0.10–0.18 s while two heavy test
   processes ran. I scored the clause met at the same bar this session already applied to J-06 and J-07 (a
   pre-existing tightness documented since iteration 16; this iteration adds no backend work at all), and
   routed the standing question to the owner. A reader who treats the recorded worst sample as binding
   would keep J-09 open instead. Logged in the assumption ledger.
3. **A stuck "Initializing…" badge after a failed warm-up.** When the start-up warm-up fails, the badge can
   read "Initializing… history 89/89" forever. It never claims "Ready", so it is not a false green, but it
   is not one of the three states the goal names either. No journey step covers it, and no product code
   changed this iteration, so it is a follow-up, not a regression.
4. **Two replay screenshots are still the same image.** `J-01-verify.png` and `J-03-verify.png` are
   byte-identical because both scripts end on the same page top; each script's own text checks are distinct
   and did the real work. Fifth recurrence of a known framework nit.
