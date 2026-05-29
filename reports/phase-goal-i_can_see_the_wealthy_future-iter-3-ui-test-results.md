# Phase goal-i_can_see_the_wealthy_future-iter-3 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future-iter-3
**Date:** 2026-05-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- SKIPPED: Frontend not running. ALL tests skipped. -->

**Overall:** 0/23 tests passed (23 skipped)

---

## Precondition check

Before recording a verdict, the frontend was probed on both candidate ports. The
iter-3 plan warns of `next dev` port drift between 3836 and 3835 that caused two prior
SKIP/PASS flaps, so both were checked. A `curl` connectivity probe is not a browser test.

| Probe | URL | Result | Interpretation |
|-------|-----|--------|----------------|
| Frontend (dispatched port) | http://localhost:3836 | HTTP `000` | No server listening — connection failed |
| Frontend (drift fallback) | http://localhost:3835 | HTTP `000` | No server listening — connection failed |
| Backend health | http://localhost:8835/health | HTTP `404` | Port answered but irrelevant; the frontend is the gate |

**Conclusion:** The frontend is not running on either port, and the dispatch declared
`Frontend available: no`. Per the browser-qa-agent precondition rules, **all 23 browser
test cases are marked SKIPPED** with reason "frontend not running". Chrome MCP / browser
automation was not invoked, and no screenshots were captured.

This report is aligned to the current 23-case UI test plan (UT-01…UT-23); it supersedes
an earlier stale results file that was written against a previous 21-case numbering.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Stock Leaderboard loads | smoke | P1 | Dense dark ranked table renders with 8-column header + as-of badge + visible/total count, no error card | Not executed — frontend not running (HTTP 000 on :3836 and :3835) | SKIP | none |
| UT-02 | Ranked rows: 3 scores + setup + reason | happy-path | P1 | ≥2 rows, ranks 1..n, each row has 3 ScoreBadges (letter+number) + setup badge + reason, ordered by Leadership | Not executed — frontend not running | SKIP | none |
| UT-03 | Sector filter narrows rows | happy-path | P1 | Selecting "Technology" shows only Tech rows; left count drops, total unchanged; scores unchanged (no recompute) | Not executed — frontend not running | SKIP | none |
| UT-04 | Setup filter (populated status) | happy-path | P1 | Selecting "Breakout-watch" shows only that status's rows (or honest empty state) | Not executed — frontend not running | SKIP | none |
| UT-05 | Setup "Actionable" → honest empty state | happy-path | P1 | Only Actionable rows, or "No stocks match these filters"; no fabricated/placeholder rows | Not executed — frontend not running | SKIP | none |
| UT-06 | Combined filters compose + clear restores | happy-path | P2 | Tech+Extended composes (≤ Tech-only count); clearing both restores full total | Not executed — frontend not running | SKIP | none |
| UT-07 | Ticker link → detail | happy-path | P1 | Clicking NVDA navigates to /stocks/NVDA; detail renders 3 score cards | Not executed — frontend not running | SKIP | none |
| UT-08 | Risk badge colour-inverted | ux | P2 | High Risk badge = red/danger, high Leadership badge = green; visibly opposite directions | Not executed — frontend not running | SKIP | none |
| UT-09 | Backend-down error card (/stocks) | error | P2 | Red "Backend unavailable" card; no fabricated rows; no blank crash / Next.js overlay | Not executed — frontend not running | SKIP | none |
| UT-10 | Detail: 3 score cards | happy-path | P1 | Header card (setup+reason) + 3 cards (raw NN.NN/100, A–E badge, caption, components) + back link + iter-4 note | Not executed — frontend not running | SKIP | none |
| UT-11 | Detail scores == leaderboard (J-06) | regression | P1* | All 3 raw numbers + A–E buckets on detail equal leaderboard NVDA values (single source); any mismatch = hard FAIL | Not executed — frontend not running | SKIP | none |
| UT-12 | Detail components ≥3, NA not fabricated | ux | P2 | ≥3 human-labelled components (not raw keys); gap_climax shown as NA, not a fabricated number | Not executed — frontend not running | SKIP | none |
| UT-13 | Unknown ticker graceful card | error | P2 | /stocks/NOTREAL shows "Unknown ticker" card + leaderboard link; no crash; no fabricated cards | Not executed — frontend not running | SKIP | none |
| UT-14 | Back-to-leaderboard link | happy-path | P2 | "Back to leaderboard" navigates to /stocks; full table re-renders | Not executed — frontend not running | SKIP | none |
| UT-15 | Themes load + ranked non-increasing | smoke | P1 | Ranked theme table (8 cols incl. chevron), ≥3 rows, scores non-increasing, breadth + price-confirmed captions | Not executed — frontend not running | SKIP | none |
| UT-16 | Top theme numeric metrics | happy-path | P1 | Top row shows numeric 1m & 3m returns, breadth % (or NA), non-empty trend label | Not executed — frontend not running | SKIP | none |
| UT-17 | Theme row expand/collapse | happy-path | P1 | Row expands to member-ticker chips + ComponentBreakdown (human labels); re-click collapses | Not executed — frontend not running | SKIP | none |
| UT-18 | Themes backend-down error card | error | P2 | Red "Backend unavailable" card; no theme rows / fabricated data; no blank crash | Not executed — frontend not running | SKIP | none |
| UT-19 | Dashboard real Candidate Counts | happy-path | P1 | Candidate Counts card: Actionable/Breakout-watch/Pullback-watch with real numbers (0 OK), not a placeholder | Not executed — frontend not running | SKIP | none |
| UT-20 | Dashboard real Top Themes | happy-path | P1 | Top Themes card lists ≥3 themes (rank+name+trend+ScoreBadge) matching /themes top entries, not a placeholder | Not executed — frontend not running | SKIP | none |
| UT-21 | Dashboard regime/sectors/breadth regression | regression | P1 | Market Regime card, ≥3 Top Sectors with scores, breadth %, data-as-of badge all still render | Not executed — frontend not running | SKIP | none |
| UT-22 | Sector Leaderboard regression (J-04) | regression | P1 | /sectors renders ranked sectors + scores + A–E buckets + labels unchanged from iter-2; breakdown expands | Not executed — frontend not running | SKIP | none |
| UT-23 | New surfaces discoverable from nav | ux | P2 | Nav shows Dashboard/Stocks/Sectors/Themes; Stocks & Themes navigate to full leaderboards (not stubs) | Not executed — frontend not running | SKIP | none |

---

## Passed Tests

None — no tests were executed (frontend not running).

---

## Failed Tests

None — no tests were executed, so no test failed. Per the browser-qa-agent rules, an
unavailable frontend is recorded as SKIPPED, never as FAIL.

---

## Skipped Tests

All 23 test cases (UT-01 … UT-23) were skipped for the **same reason**.

**Verdict:** SKIPPED (all)
**Reason:** frontend not running — HTTP `000` (connection refused / no listener) on
both the dispatched port `http://localhost:3836` and the documented drift-fallback port
`http://localhost:3835`, and the dispatch declared `Frontend available: no`. With no
frontend to drive, Chrome MCP was not invoked and no UI workflow could be exercised.

Affected tests: UT-01, UT-02, UT-03, UT-04, UT-05, UT-06, UT-07, UT-08, UT-09, UT-10,
UT-11, UT-12, UT-13, UT-14, UT-15, UT-16, UT-17, UT-18, UT-19, UT-20, UT-21, UT-22, UT-23.

**Notes on critical / specially-conditioned cases:**
- **UT-11 (P1*, critical — J-06 single source):** the browser-level cross-check that the
  detail page's scores equal the leaderboard's could not be performed without the
  frontend. The equivalent single-source invariant is also asserted at the API level by
  the functional test plan (byte-identical list-vs-detail JSON).
- **UT-22 (P1, critical — J-04 regression):** the browser-level visual regression guard for
  the `labels.py` extraction could not be run; the byte-identical-output invariant is also
  covered at the API/unit level by the functional test plan.
- **UT-09 & UT-18 (backend-down error cards):** these intentionally require the backend to be
  *stopped*, but still need a *running frontend* to render the "Backend unavailable" card —
  so they are skipped for the same frontend-not-running reason.

---

## Environment

- **Frontend URL:** http://localhost:3836 (dispatched; probed — HTTP 000, not running)
- **Frontend URL (drift fallback):** http://localhost:3835 (probed — HTTP 000, not running)
- **Backend URL:** http://localhost:8835 (reachable; `/health` → 404)
- **Browser:** Chrome via MCP — not invoked (no frontend to drive)
- **Test Date:** 2026-05-29
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future-iter-3-evidence/` (empty — no screenshots captured)
