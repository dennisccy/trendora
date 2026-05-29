# Goal Iteration 0 — UI Test Results (Baseline)

**Phase:** goal-i_can_see_the_wealthy_future-iter-0
**Date:** 2026-05-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- SKIPPED: Frontend not running. ALL journeys skipped. -->

**Overall:** 0/11 journeys passed (11 skipped)

This is the **iteration-0 baseline** of a confirmed **greenfield** repository. No application
has been built yet, so there is no running frontend or backend to test. Per the
browser-qa-agent precondition rules, all journeys are recorded as **SKIPPED (frontend not
running)** rather than FAIL — the absence of an app is the expected baseline state, not a
defect. This gives the goal-evaluator a clean per-journey starting line (every Must-have
journey NOT-YET-IMPLEMENTED) against which future iterations are measured.

---

## Precondition Check

| Probe | Command | Result | Conclusion |
|-------|---------|--------|------------|
| Frontend | `curl http://localhost:3835` | HTTP 000, curl exit 7 (connection refused) | Frontend NOT running |
| Backend | `curl http://localhost:8835` | HTTP 000, curl exit 7 (connection refused) | Backend NOT running |
| App tree | `ls apps/` | No such file or directory | No `apps/backend` / `apps/frontend` — greenfield |
| Config | `ls config.yaml` | No such file or directory | No root `config.yaml` — greenfield |

Evidence: `reports/qa/goal-i_can_see_the_wealthy_future-iter-0-evidence/precondition-check.txt`

No screenshots were captured for any journey: there is no running application to render a
page, so an end-state screenshot is not obtainable. The precondition-check text file is the
evidence for every row below.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Daily dashboard at a glance (`/`) | journey | P1 | Regime label+score, candidate counts, top sectors/themes, breadth, last-scan timestamp render | No frontend serving `/`; app not built (greenfield) | SKIP | precondition-check.txt |
| UT-J-02 | Stock Leaderboard with working filters (`/stocks`) | journey | P1 | Ranked rows with 3 bucketed scores + setup + reason; sector & "Actionable" filters narrow rows | No frontend serving `/stocks`; app not built | SKIP | precondition-check.txt |
| UT-J-03 | Theme Leaderboard (`/themes`) | journey | P1 | ≥3 themes ranked by Theme Score; top theme shows members, 1m/3m returns, breadth, trend | No frontend serving `/themes`; app not built | SKIP | precondition-check.txt |
| UT-J-04 | Sector / industry Leaderboard (`/sectors`) | journey | P1 | ETFs ranked by Sector Score; RS-vs-SPY, dist-from-52w-high, trend per row; SPY as 0% ref | No frontend serving `/sectors`; app not built | SKIP | precondition-check.txt |
| UT-J-05 | Stock Detail with explainable scores (`/stocks/[ticker]`) | journey | P1 | Price+MA+volume chart; 3 scores each with bucket+value+≥3 components; theme/setup/reason/invalidation | No frontend serving `/stocks/NVDA`; app not built | SKIP | precondition-check.txt |
| UT-J-06 | Score consistency across pages (coherence) | journey | P1 | NVDA's 3 scores + buckets identical on `/stocks` and `/stocks/NVDA` | Neither page exists; app not built | SKIP | precondition-check.txt |
| UT-J-07 | Risk-Off regime suppresses Actionable (`/scanner-runs`) | journey | P1 | Risk-Off/Defensive run shows zero "Actionable" stocks (watchlist-only) | No frontend serving `/scanner-runs`; app not built | SKIP | precondition-check.txt |
| UT-J-08 | Immutable scanner-run history (`/scanner-runs`) | journey | P1 | ≥2 dated runs; older run's rankings stored-as-of and differ from latest | No frontend serving `/scanner-runs`; app not built | SKIP | precondition-check.txt |
| UT-J-09 | System Health forward-tested evidence (`/system-health`) | journey | P1 | By-bucket (A–E) forward returns, excess vs SPY/QQQ, by-setup & by-regime breakdowns, sample n | No frontend serving `/system-health`; app not built | SKIP | precondition-check.txt |
| UT-J-10 | Control-group honesty: selection vs sector beta (`/system-health`) | journey | P1 | Top-ranked cohort vs random same-sector cohort vs SPY/QQQ/sector-ETF returns, labelled, for a horizon | No frontend serving `/system-health`; app not built | SKIP | precondition-check.txt |
| UT-J-11 | Watchlist with persistence (`/watchlist`) | journey | P1 | Add ANET; shows date/reason/score/setup/price-since/invalidation; persists across backend restart | No frontend serving `/watchlist`; no backend to persist; app not built | SKIP | precondition-check.txt |

---

## Passed Tests

None. (Baseline iteration — no application exists to exercise any journey.)

---

## Failed Tests

None. The absence of a running application is recorded as SKIPPED (precondition not met),
not FAIL, per browser-qa-agent rules. The not-yet-implemented status of each journey is the
expected greenfield baseline and is for the goal-evaluator to record.

---

## Skipped Tests

All 11 target journeys were skipped for the same reason. Target journeys (from the iter spec
Goal Mode Metadata): J-01 … J-11. Required-still-passing journeys: none (baseline — nothing
is passing yet).

### UT-J-01 — Daily dashboard at a glance
**Verdict:** SKIPPED
**Reason:** frontend not running (greenfield — `/` route does not exist; no `apps/frontend`).

### UT-J-02 — Stock Leaderboard with working filters
**Verdict:** SKIPPED
**Reason:** frontend not running (greenfield — `/stocks` route does not exist).

### UT-J-03 — Theme Leaderboard
**Verdict:** SKIPPED
**Reason:** frontend not running (greenfield — `/themes` route does not exist).

### UT-J-04 — Sector / industry Leaderboard
**Verdict:** SKIPPED
**Reason:** frontend not running (greenfield — `/sectors` route does not exist).

### UT-J-05 — Stock Detail with explainable scores
**Verdict:** SKIPPED
**Reason:** frontend not running (greenfield — `/stocks/[ticker]` route does not exist).

### UT-J-06 — Score consistency across pages (coherence)
**Verdict:** SKIPPED
**Reason:** frontend not running (greenfield — neither `/stocks` nor `/stocks/[ticker]` exists).

### UT-J-07 — Risk-Off regime suppresses Actionable
**Verdict:** SKIPPED
**Reason:** frontend not running (greenfield — `/scanner-runs` route and seeded runs do not exist).

### UT-J-08 — Immutable scanner-run history
**Verdict:** SKIPPED
**Reason:** frontend not running (greenfield — `/scanner-runs` route and seeded runs do not exist).

### UT-J-09 — System Health forward-tested evidence
**Verdict:** SKIPPED
**Reason:** frontend not running (greenfield — `/system-health` route and walk-forward data do not exist).

### UT-J-10 — Control-group honesty (selection vs sector beta)
**Verdict:** SKIPPED
**Reason:** frontend not running (greenfield — `/system-health` control-group view does not exist).

### UT-J-11 — Watchlist with persistence
**Verdict:** SKIPPED
**Reason:** frontend not running (greenfield — `/watchlist` route and persistence backend do not exist).

---

## Environment

- **Frontend URL:** http://localhost:3835 (not running — connection refused)
- **Backend URL:** http://localhost:8835 (not running — connection refused)
- **Repository state:** greenfield — no `apps/` directory, no root `config.yaml`
- **Browser:** Chrome via MCP — not invoked (precondition not met)
- **Test Date:** 2026-05-29
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future-iter-0-evidence/`
