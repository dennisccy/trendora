# Phase goal-ops-hardening-iter-19 — UI Test Plan

**Phase:** goal-ops-hardening-iter-19
**Date:** 2026-07-24
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255

---

## Scope & Environment Notes

Read this before executing any test case below.

- **This is a backend-only iteration with a real, user-facing effect — not a stub.** Zero files under
  `apps/frontend/` changed (`Frontend Present: no`, confirmed by
  `reports/phase-goal-ops-hardening-iter-19-user-visible-changes.md`). The fix removed a per-request
  ~550-lookup waste inside `backfill_run_forward_returns` (`apps/backend/app/engine/forward_testing.py`),
  the function behind both `GET /api/backtest` and MCP `query_backtest`. The ONE page this touches is the
  existing `/backtest` workspace — no new page, button, form, or label exists to test. Every case below is
  either (a) a **regression** check that `/backtest` still looks and computes exactly as it did before this
  iteration (AG-3 byte-identity is a **critical** anti-goal for this cluster), or (b) a **corroboration**
  that it now does so **fast**, which is the entire point of this iteration.
- **Chrome MCP (browser automation, port 9224) is confirmed unreachable this session** (connection refused
  at phase-spec-writing time — see `docs/phases/goal-ops-hardening-iter-19.md`'s NOTES). If you are an
  automated browser-qa agent picking up this plan and the wedge has not cleared, **SKIP the
  browser-driven steps below** and rely instead on the already-recorded evidence in
  `reports/qa/goal-ops-hardening-iter-19-test-plan.md` (TC-1 through TC-10) and
  `reports/perf-budgets.md`'s "Iteration 19" sections — those are the deterministic/curl-based fallback the
  phase's own TESTING REQUIREMENTS names for exactly this situation. **If you are a live human with a real
  browser, the Chrome MCP wedge does not affect you at all — every step below is a normal manual click-path.**
- **Do NOT trigger any backfill/ingest/rebuild job while executing this plan** (AG-10 — this host hard-reset
  twice this session under ingest bursts, 2026-07-20/21). None of the steps below need one. The
  ingest-overlay re-measurement (TC-7, contingent on owner go-ahead) is a separate, already-tracked operator
  task in the functional test plan — it is not reproduced here.
- **Do not start, stop, or restart either service.** Both are already running the final (attempt-3) iter-19
  fix build: `runs/goal-ops-hardening-iter-19/status.json` shows `current_step: qa_complete`, and
  `reports/perf-budgets.md`'s "iter-19 attempt-3" section already measured this exact live backend process.
- **This plan does not repeat the functional test plan's API/unit assertions** (TC-1 through TC-10 in
  `reports/qa/goal-ops-hardening-iter-19-test-plan.md`). It operationalizes the two rows of
  `reports/phase-goal-ops-hardening-iter-19-ui-surface-map.md` into human/browser-executable steps, and
  **cites** the already-recorded measured numbers as ground truth rather than re-deriving them.
- **Types not used this iteration:**
  - **Validation** — no form was added or changed anywhere in the app this iteration; there is nothing new
    to validate.
  - A dedicated new **Error** case (backend error surfaced to the UI) is not included as its own test: the
    phase spec explicitly states the pre-existing invalid-`as_of` 4xx/503 path is "unchanged by this
    iteration... no new TC needed for this already-covered, unchanged path." UT-05 below covers the one
    related, browser-reachable path (an unrecognized `?asof=` deep link) — a **regression** check that the
    pre-existing client-side guard around it still works, not a newly-introduced error surface.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test has exact steps and specific expected results. -->

---

### UT-01 — `/backtest` loads at the default (latest) as-of without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Frontend running at `http://localhost:3255`, backend at `http://localhost:8255` — already running, do
  not start/stop/restart.
- No login exists in this app.

**Steps:**
1. Navigate to `http://localhost:3255/backtest`.
2. Wait for the page to finish loading (any grey pulse/skeleton placeholder disappears).
3. Open the browser's developer console.

**Expected Result:**
- The page renders — no blank screen and no red "Backend unavailable" card.
- An `<h1>` heading reading exactly "Backtest" is visible near the top, with a subtitle sentence beneath it
  beginning "Time-machine to a past scan date and read its forward-test scorecard...".
- A badge reading "Viewing as-of `<date>` (latest)" (small clock icon) is visible directly below the
  heading.
- A "Survivorship bias" card (amber-bordered, shield icon) is visible with a non-empty descriptive sentence
  beneath its title.
- Scrolling down: an "As-of scan summary" heading, a "Market Regime" card (a score formatted to 2 decimals
  followed by "/ 100", plus a colored regime badge), and a "Candidate Counts" card (rows labeled
  "Actionable", "Breakout-watch", "Pullback-watch", each with a number) are all visible.
- Below that, a "Forward-test scorecard" heading is visible. **Because the default view is the LATEST scan
  date — whose 1/5/10/20/60-day forward windows have not happened yet — a dashed-bordered card reading "No
  elapsed forward window for this date yet" is EXPECTED here. This is normal, honest, pre-existing
  behavior, NOT a bug** — it is exactly the condition this iteration's fix makes cheap to serve, not a
  condition it removes. Below that card, a table with one row per configured horizon (e.g. 1d/5d/10d/20d/60d)
  is still visible, showing "—" in every numeric column.
- Further down, a "Return attribution" heading and a "Leadership cohorts" heading are visible, each with
  populated lists ("Top Sectors", "Top Themes", a "Ranked cohort" table) showing real ranks, tickers, and
  score badges — the rightmost "Fwd `<N>`d" return column may show "—" for every row at this default latest
  view (same reason as above).
- At the very bottom, a "Forward-tested evidence (expanding window ≤ `<date>`)" heading is visible with real,
  non-"—" numbers beneath it — this section is a separate all-history aggregate (a different, untouched code
  path) and stays populated regardless of whether the CURRENT date's own window has elapsed.
- No uncaught JavaScript error appears in the browser console.

---

### UT-02 — `/backtest` serves promptly, corroborating the iter-19 fix live (happy-path)

**Type:** happy-path
**Priority:** P1 (the browser-observable speed check below is mandatory; the quantified 6×-concurrency
reproduction is optional/citation-only — see Expected Result)
**Surface:** `/backtest`

**Preconditions:**
- Same running backend/frontend as UT-01.

**Steps:**
1. Navigate to `http://localhost:3255/backtest` (or reload it if already open).
2. Note how quickly the skeleton placeholder is replaced by real content — a stopwatch, or the browser's
   Network tab timing for the `backtest` request, is enough.
3. Reload the page (F5) 3-4 more times in a row, each time noting the same thing.

**Expected Result:**
- Every one of the loads in steps 2-3 finishes in well under a second — no multi-second stall, no spinner
  that hangs. This is a stark, directly observable change from before this iteration: the operator's own
  post-fix measurement recorded a **112 ms mean / 302 ms max** client-observed load time under 6×
  concurrent load (down from a pre-fix **1083 ms mean / ~1.3 s max** on the identical protocol — see
  `reports/perf-budgets.md`, "Iteration 19 — TC-6 ... attempt-3"), so even a single unloaded browser tab
  should feel close to instant.
- **Optional, more rigorous corroboration** (for an operator with terminal access to the backend host — not
  required for this case to PASS, since the authoritative quantified number is already recorded):
  ```
  for i in 1 2 3 4 5 6; do curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' http://localhost:8255/api/backtest & done; wait
  tail -n 30 logs/backend.log | grep backtest_timing | tail -n 6
  ```
  Expect all 6 curl lines to read `200` with `time_total` well under 1.5 s, and each of the 6
  `backtest_timing` log lines to show `backfill_forward_returns_ms=` as a small number (roughly 1-75,
  matching the measured 13.9 ms mean / 73.4 ms max) with `write_taken=False` (this run's forward returns
  are already fully backfilled from the thousands of requests already served today, so no write is
  expected). A result anywhere near the pre-fix 800-900+ ms range, or `write_taken=True` on every line,
  would mean the running backend is NOT actually serving the iter-19 fix build — flag it immediately.

---

### UT-03 — Evidence, scorecard, and leadership content are unchanged between reloads (regression, AG-3)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Same running backend/frontend as UT-01.

**Steps:**
1. Navigate to `http://localhost:3255/backtest`.
2. Note (or screenshot) the numbers in the "Forward-test scorecard" table, the horizon selector's default
   selection, and the first 2-3 rows of the "Ranked cohort" table.
3. Reload the page (F5).
4. Compare the newly-rendered table/lists against your step-2 notes/screenshot.

**Expected Result:**
- Every value is identical between the two loads — same "—"/numeric pattern in the scorecard, same ranks
  and tickers in the same order in the leadership lists, same default horizon selection. Nothing shifts,
  flickers, or momentarily shows different numbers between reloads.
- No red "Backend unavailable" card appears on either load.
- **Optional, more rigorous corroboration** (for an operator with terminal access — closes the still-open
  live-capture item in `reports/phase-goal-ops-hardening-iter-19-user-visible-changes.md`'s "Not Visible
  Yet" section):
  ```
  curl -s http://localhost:8255/api/backtest | python3 -m json.tool > backtest-capture-1.json
  sleep 3
  curl -s http://localhost:8255/api/backtest | python3 -m json.tool > backtest-capture-2.json
  diff backtest-capture-1.json backtest-capture-2.json
  ```
  (write the two files to a writable scratch directory — e.g. the value of `$TMPDIR` if your environment
  sets one for isolated test runs). Expect `diff` to print **nothing** — the two captures are byte-for-byte
  identical, confirming the fix's guard introduced no nondeterminism between back-to-back requests for the
  same as-of. Both captures should contain a non-null `evidence_status`, `evidence_generated_at`,
  `evidence_asof`, and a populated `evidence_by_horizon` entry for every configured horizon. This
  corroborates the unit-tested byte-identity guarantee (functional plan TC-5) against the real running
  process, not only a test fixture (functional plan TC-10).

---

### UT-04 — An old, fully-elapsed as-of date still shows a complete scorecard (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest?asof=2025-05-30`

**Preconditions:**
- Same running backend/frontend as UT-01.
- This relies on `2025-05-30` still being a date this backend's run list recognizes — it was confirmed
  present with fully-backfilled forward returns during this iteration's own diagnostic capture (a
  545-symbol × 5-horizon run, `reports/perf-budgets.md`'s "iter-19 addendum" section, run 1437). **If step 2
  below shows "(latest)" instead of "(historical)"**, the deep link was not recognized — instead, click the
  "‹" chevron button (hover text "Previous available date") next to the as-of control near the top of any
  page 10-15 times, then repeat steps 3-4 against whatever historical date that lands on.

**Steps:**
1. Navigate to `http://localhost:3255/backtest?asof=2025-05-30`.
2. Confirm the badge below the page heading reads "Viewing as-of 2025-05-30 (historical)" (amber, history
   icon) — not "(latest)".
3. Look at the "Forward-test scorecard" table.
4. Look at the row of horizon buttons above the "Return attribution" section, and at the "Leadership
   cohorts" section's "Fwd `<N>`d" column header.

**Expected Result:**
- Step 2 confirms you are genuinely viewing the historical date, not silently redirected to latest.
- Step 3: the dashed "No elapsed forward window for this date yet" card seen in UT-01 does **NOT** appear
  here — every horizon row (1d/5d/10d/20d/60d) shows a real numeric percentage (not "—") in the Cohort
  column, since this date's forward windows have all fully elapsed.
- Step 4: the horizon selector defaults to a small horizon (commonly 1d, not the 60d fallback seen at the
  latest view in UT-01), and every horizon button, once clicked, shows real non-"—" figures in both Return
  Attribution and the three leadership lists.
- No red "Backend unavailable" card, no console error — confirming this iteration's un-elapsed-horizon
  short-circuit (which only changes behavior for runs with `observable_days == 0`, i.e. dates at or near the
  data's own end) left this already-elapsed historical date's code path byte-identical to before.

---

### UT-05 — An unrecognized `?asof=` deep link degrades safely to the latest view (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/backtest?asof=2099-12-31`

**Preconditions:**
- Same running backend/frontend as UT-01.

**Steps:**
1. Navigate to `http://localhost:3255/backtest?asof=2099-12-31` (a date with no scan run).
2. Wait for the page to finish loading.
3. Look at the badge below the heading and at the browser's address bar.

**Expected Result:**
- No error page, blank screen, or "Backend unavailable" card appears.
- The badge reads "Viewing as-of `<today's actual latest date>` (latest)" — the unrecognized date is
  silently discarded, never trusted or displayed as if it were real.
- The address bar's `?asof=2099-12-31` query parameter is removed (the URL settles to the bare
  `http://localhost:3255/backtest`) once the page finishes loading.
- This exercises pre-existing (J-43) client-side validation logic that this iteration did not touch —
  confirms the backend change did not disturb it.

---

### UT-06 — `/backtest` and the historical as-of control remain discoverable (ux)

**Type:** ux
**Priority:** P2
**Surface:** sidebar navigation + as-of switcher (top bar)

**Preconditions:**
- Frontend running at `http://localhost:3255`.

**Steps:**
1. Navigate to `http://localhost:3255` (the dashboard/home page).
2. Look at the left sidebar navigation.
3. Click the "Backtest" link in the sidebar (flask-shaped icon).
4. On the resulting page, click the small calendar button near the top-right of the as-of control (it
   currently reads "Latest").

**Expected Result:**
- Step 2: a "Backtest" label with a flask icon is visible in the sidebar — reaching it from home takes
  exactly 1 click, no login required.
- Step 3: the browser navigates to `http://localhost:3255/backtest` and the "Backtest" `<h1>` heading
  appears.
- Step 4: a calendar popover opens listing selectable historical dates. This is the SAME single global
  as-of switcher used across every other page in the app, not a page-local control.
- Nothing about this iteration's backend fix changed any label, icon, or click path — this case exists only
  to confirm the pre-existing way of reaching and using `/backtest` was not accidentally disturbed by this
  iteration's source changes.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/backtest` loads at default (latest) as-of | smoke | P1 | `/backtest` |
| UT-02 | Serves promptly — the iter-19 fix, live | happy-path | P1 | `/backtest` |
| UT-03 | Evidence/scorecard/leadership unchanged across reloads | regression | P1 | `/backtest` |
| UT-04 | Historical fully-elapsed date unaffected | regression | P1 | `/backtest?asof=2025-05-30` |
| UT-05 | Unrecognized `?asof=` degrades safely | regression | P2 | `/backtest?asof=2099-12-31` |
| UT-06 | `/backtest` + as-of switcher discoverability | ux | P2 | sidebar, top bar |

**P1 tests must all pass for a browser-qa PASS verdict, when a live browser or Chrome MCP session is
available.** Per the confirmed port-9224 wedge this session, the automated browser-qa lane is expected to
SKIP — in that case the functional test plan's TC-1 through TC-10 (unit-tested byte-identity, plus the
already-recorded live TC-6 measurement in `reports/perf-budgets.md`) are the substitute evidence floor for
this iteration's Definition of Done, per the phase spec's own TESTING REQUIREMENTS. A live human operator
with a real browser is unaffected by the wedge and can execute every case above by hand.

**Coverage of phase requirements:**
- The one affected surface (`/backtest` load-time behavior): UT-01, UT-02.
- Byte-identity regression guard (AG-3, critical): UT-03, UT-04.
- Old/historical-date code path unaffected by the new short-circuit: UT-04.
- Pre-existing client-side deep-link guard unaffected: UT-05.
- No regression to discoverability/navigation: UT-06.
- Deliberately NOT covered here (already covered elsewhere, out of ui-test-designer scope): TC-1 through
  TC-5's SQL-inspected zero-write/idempotency unit tests, TC-6/TC-7's quantified concurrency/ingest-overlay
  measurements, TC-8's health poll, and TC-9's deterministic golden replay for the required-still-passing
  J-01/J-03/J-05 journeys — none of those journeys' own pages (`/data`, `/scanner-runs`) are in this
  iteration's UI surface map, so no new browser case for them is manufactured here.
