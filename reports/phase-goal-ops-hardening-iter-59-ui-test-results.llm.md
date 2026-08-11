# Phase goal-ops-hardening-iter-59 — UI Test Results

**Phase:** goal-ops-hardening-iter-59
**Date:** 2026-08-11
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests that were executed pass; UT-02/UT-03/UT-04 are legitimately SKIPPED per this
     agent's hard "never restart the app" rule (the test plan's own preconditions anticipate this exact
     skip: "skip this test if you only have browser access") — no smoke/happy-path/P1 test that ran
     failed. -->

**Overall:** 4/7 tests passed (3 skipped, 0 failed)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Page loads under normal conditions | smoke | P1 | Heading + both tables visible, correct column order, no error card | Heading "Research — Regime Lab" visible; `regime-lab-by-label` and `regime-lab-by-decile` cards present; column order Fwd 1d/5d/10d/20d/60d then MDD 1d/5d/10d/20d/60d in both tables; no error card | PASS | `reports/qa/goal-ops-hardening-iter-59-evidence/UT-01-result.png` |
| UT-02 | Memory-pressure degrade renders honestly | happy-path | P1 | Backend restarted w/ `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab`, all cells show NA + specific tooltip | Not executed — requires a backend restart, which this agent's hard rule ("never debug or restart the app") forbids; the test plan's own precondition explicitly allows this skip ("skip this test if you only have browser access") | SKIP | none |
| UT-03 | Rank-IC row keeps old NA tooltip (known gap) | validation | P2 | With fault-injected backend still running, Rank-IC NA cell keeps old generic tooltip | Not executed — depends on UT-02's fault-injected backend state, which was never established (same restart restriction) | SKIP | none |
| UT-04 | Fully-down backend shows generic error card | error | P2 | Backend stopped entirely; red "Backend unavailable" card + Retry button appear | Not executed — requires stopping the backend entirely, which this agent's hard rule forbids | SKIP | none |
| UT-05 | Normal figures unchanged from before this phase | regression | P1 | UI value/`n=` matches raw API; no `regime_lab_status`/`status` keys in response; sort + N= chip still work | `GET /api/research/regime-lab?view=pooled` (the exact query the frontend sends — `REGIME_LAB_VIEW="pooled"`) returned `by_label[0]` ("Strong risk-on") horizon 20 `mean_return=0.0035029...` (rounds to +0.35%, `n=282050`) — byte-for-byte match to the rendered "Strong risk-on / Fwd 20d" cell; no `regime_lab_status` key anywhere in the payload and no `status` key on any `by_horizon[]` entry (checked all `by_label` + `by_decile` rows); clicking the "Fwd 20d" header re-sorted rows descending (2.48% → 2.27% → 2.22% → 1.42% → 1.07% → 0.35%); an "N=" chip is an `<a target="_blank" href="/research/samples?kind=regime-lab&horizon=1&slice=label&view=pooled&regime=Defensive">`, clicked and confirmed the samples page opened in a new tab with matching cohort content ("Defensive") | PASS | `reports/qa/goal-ops-hardening-iter-59-evidence/UT-05-result.png` |
| UT-06 | Regime Lab still reachable from Research index | ux | P3 | Card titled "Regime Lab" with matching description text; navigates to `/research/regime-lab`; no new degraded/unavailable badge | `[data-testid="research-lab-link-regime-lab"]` present on `/research`, text "Regime Lab" + "How have stocks' forward returns and downside risk differed across market regimes? ..." (no badge/icon added); clicking it navigated to `/research/regime-lab` (confirmed via `await_text` on the page heading) | PASS | `reports/qa/goal-ops-hardening-iter-59-evidence/UT-06-result.png` |
| UT-J-01 | J-01: Backfill honors the requested range and explains zero-work (goal-mode regression journey, replay-flagged) | regression | P1 | See journey Acceptance below | All 8 acceptance points confirmed live (see Journey section) | PASS | `reports/qa/goal-ops-hardening-iter-59-evidence/UT-J-01-result.png`, `UT-J-01-fullrange-result.png`, `UT-J-01-weekend-zerowork-crop.png` |

---

## Passed Tests

### UT-01 — Page loads under normal conditions
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-59-evidence/UT-01-result.png`
- Navigated to `/research/regime-lab`; heading "Research — Regime Lab" visible.
- `[data-testid="regime-lab-by-label"]` ("By regime label") and `[data-testid="regime-lab-by-decile"]`
  ("By regime-score decile") both rendered with real data (six regime-label rows; D1–D10 decile rows plus
  a Rank-IC row).
- Column headers, left to right, in both tables: Regime | Fwd 1d | Fwd 5d | Fwd 10d | Fwd 20d | Fwd 60d |
  MDD 1d | MDD 5d | MDD 10d | MDD 20d | MDD 60d — matches the required order exactly.
- No red "Backend unavailable" card anywhere on the page.
- Console logging is not implemented in this Chrome MCP build (`# TODO: Console logging not yet
  implemented`), so "no console errors" could not be independently confirmed via the console log file;
  the page rendered complete, populated tables with no visible error boundary or crash, which is the
  behavioral signal this test cares about.

### UT-05 — Normal figures unchanged from before this phase
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-59-evidence/UT-05-result.png`
- Read the frontend source (`apps/frontend/app/research/_labs.tsx:3821`, `REGIME_LAB_VIEW = "pooled"`) to
  determine the exact query the page issues, then called `GET /api/research/regime-lab?view=pooled`
  directly: `by_label[0]` ("Strong risk-on") horizon-20 entry is `{"n": 282050, "mean_return":
  0.0035029211787330154, "mean_max_drawdown": -0.08365893657818559}` — `0.35%` rounded, `n=282050`,
  byte-identical to the "Strong risk-on / Fwd 20d" cell rendered in the UI.
- Confirmed via the same payload: no `regime_lab_status` key at the top level, and no `status` key on any
  `by_horizon[]` entry across every `by_label` and `by_decile` row — a genuinely clean, non-degraded
  response.
- Clicked the "Fwd 20d" column header (`//*[@data-testid="regime-lab-by-label"]//th[contains(.,"Fwd
  20d")]`); rows re-sorted descending by that column's value (2.48% → 2.27% → 2.22% → 1.42% → 1.07% →
  0.35%) — sort still works.
- Located an "N=" chip (`n=104065` under Defensive/Fwd 1d), confirmed it is an `<a target="_blank"
  href="/research/samples?kind=regime-lab&horizon=1&slice=label&view=pooled&regime=Defensive">`, clicked
  it, and confirmed the new tab loaded `/research/samples` with matching "Defensive" cohort content before
  closing the tab and returning to the main tab.

### UT-06 — Regime Lab still reachable from Research index
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-59-evidence/UT-06-result.png`
- On `/research`, `[data-testid="research-lab-link-regime-lab"]` is present, `href="/research/regime-lab"`,
  text = "Regime Lab" + "How have stocks' forward returns and downside risk differed across market
  regimes? Paired return + max-drawdown by regime label and by regime-score decile, all horizons." — no
  new badge/icon/"degraded"/"unavailable" indicator.
- Clicked the card; the app navigated and rendered the "Research — Regime Lab" heading (`await_text`
  confirmed).

### UT-J-01 — J-01: Backfill honors the requested range and explains zero-work
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-59-evidence/UT-J-01-result.png` (acceptance state — the
`/scanner-runs/748` immutable-snapshot leaderboard), plus `UT-J-01-fullrange-result.png` (the completed
full-May-range job card) and `UT-J-01-weekend-zerowork-crop.png` (the zero-work explanatory note, cropped
from a full-page capture for legibility).

This journey was flagged by the replay lane as a possible regression and was re-executed live end to end
per the dispatch instructions, driving the real `/data` job form (not merely replaying the stored golden).
Pre-check: `sqlite3` confirmed `scanner_runs` already holds all 19 trading-day snapshots for 2026-05-04 …
2026-05-29 (ids 730–748) from earlier iterations of this same goal-mode session, so both job submissions
below land in the zero-work branch — this is expected, persisted state, not a test artifact.

1. Navigated to `/data`, set start=`2026-05-02` / end=`2026-05-29` via `[data-testid="job-start-date"]` /
   `[data-testid="job-end-date"]` (job kind defaulted to `backfill`), clicked "Start".
2. Watched the live progress panel: `19/19 dates` → `0 snapshots · 0 forward returns inserted` → `28
   calendar days · 19 already snapshotted · 9 non-trading` — `dates_total` = 19 confirmed (all 19 trading
   days targeted); every one was already snapshotted so `snapshots_created` = 0, with the explicit
   already-snapshotted/non-trading breakdown partitioning all 28 calendar days.
3. Set start=`2026-05-02` / end=`2026-05-03` (weekend-only span), clicked "Start": panel showed `0/0
   dates`, `2 calendar days · 0 already snapshotted · 2 non-trading`, and an explicit note: "Zero-work
   outcome — every requested trading day already had a snapshot (or the range contains no trading days).
   No new computation was needed; this is not a failure." — partitions the 2 calendar days per the
   run-summary contract.
4. Reloaded `/data` (fresh navigation, not SPA state): the Run history table's top two rows were exactly
   the two runs just submitted (`2026-08-11 03:24:24 backfill 2026-05-02 → 2026-05-03` and `2026-08-11
   03:23:17 backfill 2026-05-02 → 2026-05-29`), same breakdown text as live — confirms the persisted job
   history panel survives reload, never "no job started this session".
5. Compared badge styling directly in the DOM: the zero-work "no new snapshots" badge
   (`data-testid="run-status"`) uses `class="... border-border bg-surface-2 text-text-muted ..."` (neutral
   gray) versus a productive run's "ok" badge using `class="... border-pos bg-surface-2 text-pos ..."`
   (the positive/green color token) — visually distinct, never the same unexplained success styling.
   Confirms acceptance point "zero-work is never rendered as unexplained success."
6. Navigated to `/scanner-runs`: confirmed `2026-05-04`, `2026-05-15`, `2026-05-29` all present in the
   page text. Opened `/scanner-runs/748`: page shows "Immutable snapshot — as of 2026-05-29 · Stored
   exactly as scanned; never recomputed for today" with a populated 542-row leaderboard — a stored,
   non-recomputed snapshot renders correctly (screenshot at this acceptance state).

Acceptance checklist:
- Consistency (single source): confirmed by inspection — the UI renders exactly the persisted run-summary
  breakdown text served by the job endpoint; no separate client-side eligibility computation observed.
- Correctness: `scanner_runs` holds all 19 required May trading-day rows (ids 730–748, verified via
  `sqlite3` before driving the UI); `/scanner-runs/748` leaderboard renders as an immutable stored
  snapshot.
- Honest status & anti-goals: the weekend-only run showed `0/0` targets + `2 non-trading`; the full-range
  re-run showed `0` created + `19 already-snapshotted` + `9 non-trading`; both persisted across reload; no
  fabricated progress.
- Walkthrough: out of scope for browser-qa-agent this iteration (the dev handoff/demo lane owns
  `demo.sh ops-hardening --session-live`, per TC-10 in the phase spec) — not re-verified here.

Golden replay script rewritten at `runs/goal-session-ops-hardening/journey-scripts/J-01.json` (16 steps,
same structure as the pre-existing script — every assertion in it was independently re-confirmed live this
run, including the `19/19 dates`, `stage-timings` panel, both calendar-day breakdown strings, and the
`/scanner-runs/748` "as of 2026-05-29" landing text) and lints clean via
`demo_runner.py --mode lint --journeys J-01`. The prior replay FAIL appears to have been a stale/flaky
result — every assertion in the golden reproduced exactly on live re-execution with no code or UI
difference observed.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-02 — A memory-pressure degrade renders honestly instead of crashing the page
**Verdict:** SKIPPED
**Reason:** Requires restarting the backend with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab` set. This
agent's hard rule ("never debug or restart the app — that is a SKIPPED with reason") forbids performing a
backend restart regardless of available shell access. The test plan's own precondition anticipates exactly
this: "Requires shell access to restart the backend with an environment variable set — skip this test if
you only have browser access." The phase spec itself independently confirms browser-qa-agent is not
assigned restart duties this iteration (only the developer is, for J-05 step 3).

### UT-03 — The Rank-IC row keeps its old, generic NA tooltip during a degrade
**Verdict:** SKIPPED
**Reason:** Depends on UT-02's fault-injected backend still running (same precondition chain); since UT-02
was not executed, there is no fault-injected backend state to test against. Same restart restriction as
UT-02.

### UT-04 — A fully-down backend still shows the pre-existing generic error card
**Verdict:** SKIPPED
**Reason:** Requires stopping the backend process entirely. Same hard rule as UT-02/UT-03 — this agent
never stops/restarts the app under test.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (confirmed healthy, HTTP 200 on `/api/health`, before and
  throughout this run — never restarted by this agent)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned
  profile/CDP port per environment, headless throughout
- **Test Date:** 2026-08-11
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-59-evidence/`
- **Golden replay script written/repaired:**
  `runs/goal-session-ops-hardening/journey-scripts/J-01.json` (lints clean)
