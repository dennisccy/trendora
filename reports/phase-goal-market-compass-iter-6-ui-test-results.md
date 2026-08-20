# UI Test Results (merged)

**Date:** 2026-08-20
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** BLOCKED

**Overall:** 2/5 journeys passed (3 skipped, 2 required-unverified, 1 target-unverified)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-6-evidence/J-01-verify.png |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | journey | P1 | Not evaluated — lane gated by goal contract | Not executed. `docs/goal.md` (Loop mechanics, owner insert #2) forbids browser-QA from running against the knowingly damaged database before J-10's post-recovery verification passes; that verification did not complete this iteration. J-02's Acceptance depends on session-over-session data for exactly the deleted 2026-08-11/2026-08-12 window. | SKIP | none — no browser opened this run |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | journey | P1 | Not evaluated — lane gated by goal contract | Not executed. Same lane gate as UT-J-02. J-03's summary sentences are generated from the same manifest/session-delta substrate that depends on the deleted 2026-08-11/2026-08-12 price data. | SKIP | none — no browser opened this run |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-6-evidence/J-04-verify.png |
| UT-J-10 | Bounded recovery of the two trading days the iter-5 drill deleted | journey | P1 | Not evaluated — recovery incomplete this iteration | Not executed. J-10 is itself the recovery/verification journey; its Acceptance requires the frontier to reach 2026-08-12 and `GET /api/compass?as_of=2026-08-12` to serve before "J-01/J-02/J-03 replay clean" can even be checked. This iteration's authorized Stooq fetch (AG-9's dated exception) was blocked vendor-side — all 587 requests returned 404 behind a JavaScript proof-of-work challenge — so the frontier is still 2026-08-10 and `GET /api/compass?as_of=2026-08-12` still returns 400. J-10's own Walkthrough requirement is separately waived in goal.md ("data-layer repair with no UI surface change of its own") — it was never a UI-testable journey. | SKIP | none — no browser opened this run |

## Missing Required Journeys

_Required-still-passing journeys named in the iteration spec that were NOT verified this iteration — either no lane (deterministic replay or LLM browser-qa) produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-40 lesson: this is exactly how required journeys shipped with zero evidence while every gate reported clean)._

- `UT-J-02` — only a SKIP row for J-02: named but never executed
- `UT-J-03` — only a SKIP row for J-03: named but never executed

## Missing Target Journeys

_Target journeys named in the iteration spec's `Target journeys:` line — the journeys THIS iteration exists to verify — that were NOT verified this iteration, either no lane produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-41 audit finding B2 / iter-42 fix: promoting a journey to an iteration's own target silently removed its verification — iter-41 itself shipped a clean PASS 6/6 headline while its two target journeys had zero rows anywhere)._

- `UT-J-10` — only a SKIP row for J-10: named but never executed

## Skipped Tests

### UT-J-02 — "What changed" reports meaningful session-over-session deltas with honest empties

**Verdict:** SKIPPED
**Reason:** Not executed. `docs/goal.md` (Loop mechanics, owner insert #2) forbids browser-QA from running against the knowingly damaged database before J-10's post-recovery verification passes; that verification did not complete this iteration. J-02's Acceptance depends on session-over-session data for exactly the deleted 2026-08-11/2026-08-12 window.

### UT-J-03 — The plain-English summary is deterministic, cited, and never invents a cause

**Verdict:** SKIPPED
**Reason:** Not executed. Same lane gate as UT-J-02. J-03's summary sentences are generated from the same manifest/session-delta substrate that depends on the deleted 2026-08-11/2026-08-12 price data.

### UT-J-10 — Bounded recovery of the two trading days the iter-5 drill deleted

**Verdict:** SKIPPED
**Reason:** Not executed. J-10 is itself the recovery/verification journey; its Acceptance requires the frontier to reach 2026-08-12 and `GET /api/compass?as_of=2026-08-12` to serve before "J-01/J-02/J-03 replay clean" can even be checked. This iteration's authorized Stooq fetch (AG-9's dated exception) was blocked vendor-side — all 587 requests returned 404 behind a JavaScript proof-of-work challenge — so the frontier is still 2026-08-10 and `GET /api/compass?as_of=2026-08-12` still returns 400. J-10's own Walkthrough requirement is separately waived in goal.md ("data-layer repair with no UI surface change of its own") — it was never a UI-testable journey.

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-20

