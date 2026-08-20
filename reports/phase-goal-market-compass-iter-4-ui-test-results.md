# UI Test Results (merged)

**Date:** 2026-08-20
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** BLOCKED

**Overall:** 4/5 journeys passed (1 skipped, 1 target-unverified)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | Unassigned share ≤5% of resolved members at latest as-of (was ~78%); two spot-checked names show identical sector across leaderboard/detail/API; `/methodology` discloses the two-source basis + current-only limitation; a symbol absent from both maps serves `sector: null` / "Unassigned", never fabricated | Verified live: `GET /api/stocks` at latest as-of (2026-08-12, 539 rows) returns **0 rows with `sector: null` (0.0% Unassigned)** — the frontend's "Filter by sector" `<select>` has no "Unassigned" option at all because zero rows currently qualify (stronger than the ≤5% bar, not a missing control). NVDA (`config.stock_sectors`-mapped → "Technology") and GRMN (pool-CSV-fallback, not in `config.stock_sectors` → "Consumer Discretionary") match identically across the leaderboard Sector cell, the stock detail header badge, and `GET /api/stocks`. `/methodology` → "Stock sector labels" discloses the exact two-source basis and current-only limitation, citing B-114. Step 1 (Remove+backfill on `/data`) was deliberately NOT re-executed live — see Passed Tests notes. Step 5's null-symbol case could not be exercised live (0/539 active members are currently null) — methodology text documents the guarantee; not re-verified via a live click path. | PASS | `reports/qa/goal-market-compass-iter-4-evidence/UT-J-01-result.png` |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-4-evidence/J-02-verify.png |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-4-evidence/J-03-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-4-evidence/J-04-verify.png |
| UT-J-09 | The backend fits the host — standing memory halves with zero behavior change | non-UI | P1 | Measured backend VmPeak at standing warm ≤ 2.5 GB (2,621,440 kB) | Not browser-observable — deliberately backend-only, no UI surface (goal.md: "Walkthrough: waived"). Documentary evidence only (cited below): VmPeak measured **3,439,100 kB**, a real 28.9% reduction from the 4,837,420 kB baseline, but **+817,660 kB (31.2%) OVER** the ≤2.5 GB target — **target MISSED**. Disclosed honestly per spec (appended dated, cap values untouched) rather than hidden or forced to pass. | SKIPPED | none (no UI surface) |

## Missing Target Journeys

_Target journeys named in the iteration spec's `Target journeys:` line — the journeys THIS iteration exists to verify — that were NOT verified this iteration, either no lane produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-41 audit finding B2 / iter-42 fix: promoting a journey to an iteration's own target silently removed its verification — iter-41 itself shipped a clean PASS 6/6 headline while its two target journeys had zero rows anywhere)._

- `UT-J-09` — only a SKIP row for J-09: named but never executed

## Skipped Tests

### UT-J-09 — The backend fits the host — standing memory halves with zero behavior change

**Verdict:** SKIPPED
**Reason:** Not browser-observable — deliberately backend-only, no UI surface (goal.md: "Walkthrough: waived"). Documentary evidence only (cited below): VmPeak measured **3,439,100 kB**, a real 28.9% reduction from the 4,837,420 kB baseline, but **+817,660 kB (31.2%) OVER** the ≤2.5 GB target — **target MISSED**. Disclosed honestly per spec (appended dated, cap values untouched) rather than hidden or forced to pass.

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-20

