# Phase goal-mcp-loop-iter-24 — Closure Verdict

**Phase:** goal-mcp-loop-iter-24
**Date:** 2026-07-09
**Written by:** phase-closure-auditor

---

**Verdict:** CLOSURE-FAIL

---

## Standard Pipeline Gate Checks

| Artifact | Status | Verdict |
|----------|--------|---------|
| Review report (`reports/reviews/goal-mcp-loop-iter-24-review.md`) | exists | PASS_WITH_NOTES (acceptable) |
| QA report (`reports/qa/goal-mcp-loop-iter-24-qa.md`) | exists | PASS **— but stale/contradicted, see below** |
| Audit report (`docs/handoffs/goal-mcp-loop-iter-24-audit.md`) | exists | PASS_WITH_GAPS **— but its own text says the phase is not yet shippable** |

Each verdict string is individually within the nominally acceptable set. This closure gate nonetheless
fails the phase because reading the *content* of the downstream UI-chain artifacts (not just the verdict
line) reveals that the QA PASS and the audit's PASS_WITH_GAPS were both overtaken by a later, more
rigorous, and more authoritative finding — a reproduced critical crash — that has not been closed out at
the browser/journey level the Definition of Done actually requires.

---

## UI Visibility Artifact Checks

| Artifact | Exists | Non-Empty | Non-Vague | Status |
|----------|--------|-----------|-----------|--------|
| implementation-summary.md | yes | yes | yes | OK, but **stale relative to now-known facts** (see Blocking Issue 2) |
| user-visible-changes.md | yes | yes | yes | OK, but **stale relative to now-known facts** (see Blocking Issue 2) |
| ui-surface-map.md | yes | yes | yes | OK |
| ui-test-plan.md | yes | yes | yes | OK — 16 detailed UT-xx cases with concrete steps/expected results |
| ui-test-results.md | yes | yes | yes | OK as an artifact, but **verdict is FAIL, not PASS** (see Blocking Issue 1) |
| what-to-click.md | yes | yes | yes | OK — 9 numbered steps with specific expected outcomes |

All six required artifacts exist, are substantive, and are non-vague on their own terms. The blocking
problem is not artifact *absence* — it is that the artifacts, read together with their timestamps, show an
unresolved FAIL that the pipeline moved past without a closing re-verification.

---

## Cross-Reference Checks

- [x] user-visible-changes lists ≥1 specific capability — yes: the "Storage footprint" card on `/data`.
- [x] ui-surface-map has specific route/component entries — yes: `/data` `StorageCapacityPanel`,
      `/stocks/{ticker}`, `/watchlist`, global `HealthBadge`, etc., each with file:line citations.
- [x] ui-test-plan has specific steps with exact actions and expected results — yes, 16 cases (UT-01…UT-16).
- [x] ui-test-results shows execution evidence — yes: 14/16 executed with screenshots/curl cross-checks,
      2 SKIPPED with documented reasons (UT-04 needs an isolated empty-DB instance; UT-12's warm-up window
      was too fast to observe on this host, 3/3 restarts).
- [x] what-to-click has ≥3 numbered steps with exact expected outcomes — yes, 9 steps.
- [ ] **implementation-summary claims are consistent with ui-test-results evidence — FAILS.** This is the
      blocking check. See below.

---

## Blocking Issues

1. **The canonical browser-qa verdict is FAIL, not PASS, and has never been re-run after the fix.**
   `reports/phase-goal-mcp-loop-iter-24-ui-test-results.md` (written by browser-qa-agent, mtime 07-09
   08:48) states, at the top: `**Browser QA Verdict:** FAIL`. It reproduced, 2 of 2 independent fresh
   restarts, a backend crash (`MemoryError` in `cursor.fetchmany()`/`json.dumps()`, and on the second
   attempt a fatal Rust/PyO3 panic that kills the whole uvicorn process) on the very first `/data` load
   after boot — the exact cold-path scenario the phase spec's own DoD requires ("a cold `/api/data` still
   completes ≤ 60 s without OOM"). This fails UT-16 (P2) and, because the crash prevents the page from
   ever rendering, cascades to fail UT-06 (**P1** — "P1 tests must all pass for browser QA verdict to be
   PASS" per the test plan's own summary) and the recovery-continuation half of UT-05.
   `reports/phase-goal-mcp-loop-iter-24-ux-regression.md` (mtime 09:04) independently confirms this and
   returns its own hard verdict, **UX-REGRESSION-FAIL**, stating verbatim: *"Do not close this iteration on
   the current evidence"* and listing "re-run the canonical browser-qa lane... before considering J-13 or
   J-15 passing" as an explicit, numbered, unmet precondition.

   `docs/handoffs/goal-mcp-loop-iter-24-audit.md` (mtime 09:20, i.e. written *after* both of the above) did
   root-cause this correctly — item B's `mmap_size_bytes: 1073741824` (1 GB per-connection SQLite read-mmap
   window) × the new `pool_size=10`/`max_overflow=20` connection pool exhausted the `server.memory_cap_mb:
   6144` `ulimit -v` cap before the cold bar-prefill could even run — and fixed it at the source
   (`config.yaml:108`, `apps/backend/app/config.py:1687`, `apps/backend/tests/test_db.py:328` all now show
   `mmap_size_bytes: 0`, confirmed by direct grep of the working tree). But the audit's own re-verification
   was a **Python ablation script** (`coldpath_repro.py`) exercising the cold-path function directly under a
   simulated `RLIMIT_AS`, not a live browser session — and the audit says so itself, explicitly, in its own
   "Recommended Next Step" section: *"the one remaining gap is that the canonical browser-qa J-15 lane must
   be re-run on a fresh restart to convert my engineering-level re-verification into the journey-level
   browser evidence the DoD asks for"* and *"Once that lane is green, this iteration is shippable."*

   No such re-run exists. `reports/qa/goal-mcp-loop-iter-24-evidence/` contains no screenshot or log newer
   than 08:46 (the original crash-log excerpt); `reports/phase-goal-mcp-loop-iter-24-ui-test-results.md`
   itself is unchanged since 08:48. The DoD's own two relevant checkboxes are therefore **not** satisfied on
   present evidence:
   - *"Target journey J-15 passes via browser-qa-agent (canonical lane, live, non-empty md5-distinct
     evidence dir)"* — the only browser-qa-agent run on record for this phase is FAIL.
   - *"Required-still-passing journeys J-01, J-03, J-04, J-05, J-10, J-12, J-13, J-14 remain green (live
     replay)"* — J-13 (Data Manager coverage + availability legend) was confirmed broken by this exact
     crash (`ux-regression.md`'s Regression Risk table, row 1: "CRITICAL — confirmed, not potential"); its
     restoration has not been re-confirmed via live browser replay since the fix, only via the audit's
     out-of-browser script.

   **Remediation:** Dispatch browser-qa-agent again (or re-run the equivalent live check) against a fresh
   `start-backend.sh`/`start-frontend.sh` boot, specifically repeating the UT-16 → UT-06 → UT-05 sequence
   (stop backend, cold-start, immediately load `/data` at least twice) to confirm the mmap fix holds at the
   browser/journey level, then update `reports/phase-goal-mcp-loop-iter-24-ui-test-results.md` (and
   `reports/phase-goal-mcp-loop-iter-24-ux-regression.md`'s verdict) to reflect a genuine PASS before
   re-submitting for closure. `runs/goal-mcp-loop-iter-24/status.json` (`qa_verdict: PASS`,
   `current_step: audit_passed`, `next_action: none`, `updated_at` 08:21) also needs to be regenerated — its
   `updated_at` predates the browser-qa FAIL (08:48), the ux-regression FAIL (09:04), and the audit itself
   (09:20), so it does not reflect any of what actually happened afterward and cannot be relied on as a
   completion signal.

2. **Two required UI artifacts were never corrected after the critical bug was found, unlike the dev
   handoff.** `reports/phase-goal-mcp-loop-iter-24-implementation-summary.md` (mtime 07:27, i.e. written
   ~2 hours before the browser-qa FAIL and the audit) states under "Incomplete Items": *"None from this
   iteration's scope. Everything specified for items B, C, D, G, H, and K ... was implemented, tested, and
   verified live against running services."* `reports/phase-goal-mcp-loop-iter-24-user-visible-changes.md`
   (mtime 07:51, same generation) contains no mention of any crash risk either. Neither file mentions the
   mmap/OOM crash, its fix, or the outstanding browser re-verification, even though
   `docs/handoffs/goal-mcp-loop-iter-24-dev.md` — written by the same pipeline, for the same phase — was
   specifically retrofitted with a prominent "AUDIT CORRECTION" banner at the top once the bug surfaced.
   Left as-is, an operator or future agent reading only `implementation-summary.md` (one of this project's
   own designated "read first" artifacts for exactly this kind of review) would have no way to learn that
   this iteration crashed the backend on cold boot 2/2 times and that the fix is unverified at the browser
   level. This is the "implementation-summary claims are consistent with ui-test-results evidence" check
   failing outright — the two documents describe different realities.

   **Remediation:** After the browser-qa re-run in Issue 1 is green, add a short correction note to both
   `implementation-summary.md` and `user-visible-changes.md` (mirroring the dev handoff's banner) recording
   the crash, root cause, fix, and re-verification — so the artifact set is internally consistent for
   anyone reading it later without also reading the audit report.

---

## Non-Blocking Notes

- The review report's single MINOR issue (missing executable bit on `scripts/measure-perf.sh`) was fixed
  during QA and is not a closure blocker.
- The reviewer's NOTE on the unlocked readiness memo (`readiness.py:65`) is correctly classified as benign
  by both the reviewer and the audit (T2) — redundant recompute at worst, never a wrong value. Not blocking.
- F1 (pre-existing `/data` no-retry desync between the page body and the independently-polling readiness
  badge) is correctly scoped by the audit as pre-existing and out of this iteration's spec — not a new
  regression to block on, but it is what turns the (now-fixed) crash's aftermath into a confusing stuck
  state for a real user; worth a dedicated follow-up card as both the audit and ux-regression report already
  recommend.
- T1 (`measure-perf.sh`'s bounded-backfill timing landing on 0 cadence-eligible dates on an already-warm
  backend) is an honest, accurately-labeled result, not a defect — not blocking.
- Items C/D/G/H/K's domain correctness (byte-identity, index hygiene, capacity snapshot, additive payload
  field) is independently well-evidenced across the dev handoff, reviewer, QA, browser-qa's PASS-ing tests
  (UT-02/07/08/09/10/11/13/14), and the audit's own source-level re-verification. None of that is in
  question — the sole blocker is the unresolved crash/re-verification gap above.
