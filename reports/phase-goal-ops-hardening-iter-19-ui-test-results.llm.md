# Phase goal-ops-hardening-iter-19 — UI Test Results

**Phase:** goal-ops-hardening-iter-19
**Date:** 2026-07-24
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 6/6 UI-test-plan cases passed (0 skipped, 0 failed). Plus-one regression journey (J-04, required-still-passing) requested by this dispatch: SKIPPED — see reasoning below and in its own section. Required-still-passing J-01/J-03/J-05 were already re-verified by the deterministic golden-replay lane per this run's dispatch note and are not re-tested or re-reported here.

**Note on Chrome MCP status:** the dispatch's PUMP NOTE flagged Chrome MCP as known-wedged this session (based on the iter-18 agent's experience) and instructed a single quick probe before falling back to SKIPPED. The probe (a `navigate` to `/backtest`) succeeded on the first try this run — the tool's own auto-restart kicked in and returned real, correct DOM content (confirmed against a full-page screenshot and the DOM/markdown auto-capture). Chrome MCP worked cleanly for the remainder of this session, so the full browser-driven test plan below was executed live, per the PUMP NOTE's "if it unexpectedly works, do the real regression check" branch.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/backtest` loads at default (latest) as-of | smoke | P1 | Page renders (no blank/red "Backend unavailable"); H1 "Backtest" + subtitle; "Viewing as-of `<date>` (latest)" badge; Survivorship-bias card; As-of scan summary (Market Regime + Candidate Counts); Forward-test scorecard shows the dashed "No elapsed forward window" card + all-"—" table (expected at latest); Return attribution + Leadership cohorts populated with real ranks/tickers; Forward-tested evidence section populated with real (non-"—") numbers; no console error | All elements rendered exactly as expected: H1 "Backtest", subtitle "Time-machine to a past scan date and read its forward-test scorecard…"; badge "Viewing as-of 2026-07-22 (latest)"; Survivorship-bias card present; Market Regime 61.86/100 "Narrow leadership"; Candidate Counts Actionable 0 / Breakout-watch 54 / Pullback-watch 1; dashed "No elapsed forward window for this date yet" card + 1d/5d/10d/20d/60d rows all "—"/n=0; Leadership cohorts (Top Sectors, Top Themes, 10-row Ranked cohort) fully populated with real grades/scores, rightmost Fwd 60d column "—" as expected at latest; Forward-tested evidence section populated with real percentages (e.g. Bucket A +10.72% n=8800, Excess vs SPY +0.60%). No error boundary, no blank screen | PASS | `reports/qa/goal-ops-hardening-iter-19-evidence/UT-01-result-fullpage.png` |
| UT-02 | Serves promptly — the iter-19 fix, live | happy-path | P1 | Every load/reload finishes well under 1 second | Browser Navigation-Timing API measured on 1 initial load + 3 reloads of `/backtest`: `loadEventEnd` = 250ms, 227ms, 242ms — all well under 1s. Supplementary (optional) 6× concurrent `curl` to `GET /api/backtest`: all 6 returned HTTP 200 in 136–231ms; the matching `backtest_timing` log lines all show `backfill_forward_returns_ms` 14.3–21.8ms and `write_taken=False` — consistent with the phase's cited post-fix 112ms mean/302ms max and nowhere near the pre-fix ~1083ms mean | PASS | `reports/qa/goal-ops-hardening-iter-19-evidence/UT-02-UT-03-latest-reload.png` |
| UT-03 | Evidence/scorecard/leadership unchanged across reloads | regression | P1 | Every value identical between reloads; no flicker; no "Backend unavailable" card | Full-DOM auto-captures from two independent `/backtest` reloads (both at latest as-of, captures 711 and 715 in the browser session dir) diffed byte-for-byte identical via `diff`. Separately (optional corroboration), two `curl` captures of `GET /api/backtest` taken 3 seconds apart also diffed byte-for-byte identical: `evidence_status="ready"`, `evidence_generated_at` populated, `evidence_asof="2026-07-22"`, `evidence_by_horizon` populated for horizons 1/5/10/20/60. No "Backend unavailable" card on any load | PASS | `reports/qa/goal-ops-hardening-iter-19-evidence/UT-02-UT-03-latest-reload.png` |
| UT-04 | Historical fully-elapsed date unaffected | regression | P1 | Badge "Viewing as-of 2025-05-30 (historical)"; no dashed "no elapsed window" card; every horizon row shows a real numeric % (not "—"); horizon selector defaults to a small horizon; leadership lists show real Fwd-`<N>`d figures; no "Backend unavailable" card, no console error | All confirmed once content settled: badge read exactly "Viewing as-of 2025-05-30 (historical)"; Forward-test scorecard showed real values for every horizon (1d +1.28% n=29, 5d +3.43%, 10d +3.08%, 20d +10.93%, 60d +19.05%); Return-attribution horizon selector defaulted to "1d" (highlighted); Leadership cohorts' Fwd 1d column showed real non-"—" values (ZS +6.34%, HOOD +2.77%, etc.); no red "Backend unavailable" card appeared at any point. **See "Additional Observation" below the table — the FIRST load of this historical date stalled on an empty skeleton for far longer than UT-02's latest-view budget before rendering; this did not change UT-04's own pass bar (which has no speed criterion) but is flagged as directly relevant to the iteration's overall latency concern** | PASS | `reports/qa/goal-ops-hardening-iter-19-evidence/UT-04-historical-recheck.png` (post-load); `UT-04-historical-wait-check.png` (stalled/skeleton state, see note) |
| UT-05 | Unrecognized `?asof=` degrades safely | regression | P2 | No error/blank/"Backend unavailable"; badge reads latest date; `?asof=` query param removed from the address bar | Navigated to `/backtest?asof=2099-12-31`; page rendered the latest view (21 interactive buttons, matching the latest-view baseline from UT-01); badge read "Viewing as-of 2026-07-22 (latest)"; the as-of control read "Latest"; `window.location.href` (evaluated in-page) confirmed the URL had settled to the bare `http://localhost:3255/backtest` with no query string. No error card | PASS | `reports/qa/goal-ops-hardening-iter-19-evidence/UT-05-unrecognized-asof.png` |
| UT-06 | `/backtest` + as-of switcher discoverability | ux | P2 | "Backtest" + flask-ish icon in sidebar, reachable in 1 click, no login; click navigates to `/backtest` with H1 "Backtest"; clicking the as-of control opens a calendar popover listing selectable historical dates (same global control) | Dashboard (`/`) loaded directly, no login prompt; "Backtest" nav entry with a small icon visible in the sidebar; clicking `a[href="/backtest"]` navigated to `http://localhost:3255/backtest` (confirmed via `window.location.href`) with H1 "Backtest"; clicking `[aria-label="View as-of date"]` opened a calendar popover: month grid for 2026-07, year/month dropdowns, prev/next-month arrows, "1862 selectable dates" label, and a "Latest · 2026-07-22" quick-jump button. This is the same as-of control whose badge form ("Data as-of 2026-07-22") was also seen on the Dashboard page itself | PASS | `reports/qa/goal-ops-hardening-iter-19-evidence/UT-06-asof-popover.png`, `UT-06-dashboard-sidebar.png` |
| UT-J-04 | J-04: Non-blocking boot with visible status (required-still-passing regression, per dispatch) | regression | P1 (journey) | Per `docs/goal.md`'s J-04 steps 1–6: backend restart → `GET /api/health` returns first 200 within 5s; ≤250ms-interval health polls during a second restart show boot-phase/progress reflected in the top-bar badge; killing the backend shows an explicit unreachable/crashed presentation distinct from "initializing"; the persistent backend logfile shows boot entries and, after the kill, ends abruptly with no clean-shutdown line; restarting again shows any job that was mid-flight at the kill in an explicit interrupted/error state | **NOT EXECUTED.** Every acceptance-bearing step (1, 3, 4, 6) requires restarting or forcibly killing the live backend process. This dispatch's own operator note states plainly: "You cannot start/stop services; backend :8255 + frontend :3255 are up" — and, independently, the phase spec and execution plan both carry this exact disruptive kill/restart replay as "operator/owner-gated (ingest-trigger classifier)… carried since iter-15… not this iteration's blocker," with TC-8 (a non-disruptive `GET /api/health` check) as this iteration's explicit substitute. No non-disruptive subset of J-04's own acceptance criteria is browser-observable without an actual restart/kill event occurring, so no partial attempt was made. See the dedicated Skipped section below for the supplementary (non-blocking) context gathered instead | SKIPPED | none (no disruptive action was taken; see Skipped Tests section for the non-blocking `curl`/log context gathered in its place) |

---

## Passed Tests

### UT-01 — `/backtest` loads at the default (latest) as-of without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-19-evidence/UT-01-result-fullpage.png`
- Every element named in the test plan's Expected Result was directly observed on a full-page screenshot and cross-checked against the DOM's auto-captured markdown export: heading, subtitle, latest-as-of badge, survivorship-bias card, market-regime/candidate-count cards, the (expected-at-latest) "No elapsed forward window" dashed card with an all-"—" scorecard table, fully-populated leadership cohorts (Top Sectors/Top Themes/10-row Ranked cohort), and a fully-populated "Forward-tested evidence (expanding window ≤ 2026-07-22)" section with real percentages throughout.
- Console-log capture via this Chrome MCP tool is not yet implemented ("`# TODO: Console logging not yet implemented`" in every `*-console.txt` capture this run) — "no console error" is inferred from the page rendering fully and correctly with no error boundary triggered, not from a direct console read. Flagging this tool limitation for transparency rather than overclaiming direct console verification.

### UT-02 — `/backtest` serves promptly, corroborating the iter-19 fix live
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-19-evidence/UT-02-UT-03-latest-reload.png`
- Used the browser's own Navigation Timing API (`performance.getEntriesByType('navigation')[0]`) rather than a subjective stopwatch, for a harder number: `loadEventEnd` was 250ms (initial load), then 227ms and 242ms on two subsequent reloads — all comfortably under the 1-second bar and consistent with the plan's "should feel close to instant" expectation.
- Also ran the plan's optional 6×-concurrent `curl` reproduction: all 6 requests to `GET /api/backtest` returned HTTP 200 in 136–231ms, and the corresponding `backtest_timing` log lines all showed `backfill_forward_returns_ms` in the 14.3–21.8ms range with `write_taken=False` — matching the phase's cited post-fix numbers (112ms mean/302ms max under load) and far below the documented pre-fix ~1083ms mean / ~1.3s max.

### UT-03 — Evidence, scorecard, and leadership content are unchanged between reloads
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-19-evidence/UT-02-UT-03-latest-reload.png`
- Compared the browser's own full-DOM auto-captures from two independent `/backtest` reloads (both at the latest as-of, several actions apart) with a plain `diff` — byte-for-byte identical, no flicker or transient value observed at any point.
- Also ran the plan's optional double-curl-capture corroboration: `GET /api/backtest` captured twice, 3 seconds apart, `diff`'d to nothing (byte-identical). Both captures carried a populated `evidence_status: "ready"`, `evidence_generated_at`, `evidence_asof: "2026-07-22"`, and `evidence_by_horizon` entries for every configured horizon (1/5/10/20/60).

### UT-04 — An old, fully-elapsed as-of date still shows a complete scorecard
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-19-evidence/UT-04-historical-recheck.png`
- `2025-05-30` was recognized (badge read "…(historical)", not "(latest)"), so no chevron-clicking fallback was needed.
- Once the page finished loading, every element the plan calls for was present and correct: real (non-"—") percentages in all 5 horizon rows of the Forward-test scorecard, a horizon selector defaulting to the small "1d" horizon, and real Fwd-1d figures in all three Leadership-cohort lists. No "Backend unavailable" card appeared.
- **Additional Observation (does not change this test's verdict, but is flagged for the evaluator's attention as directly relevant to this iteration's subject matter):** the FIRST navigation to this historical URL left the page showing three empty skeleton placeholder boxes for well over 10 seconds (an `await_text` wait for "Forward-test scorecard" with a 10-second timeout expired while still empty; see `UT-04-historical-wait-check.png`). Investigating via direct `curl` and the backend log:
  - A direct `curl -s -w '%{time_total}s' 'http://localhost:8255/api/backtest?as_of=2025-05-30'` (this run's first hit for that date) took **9.6 seconds** and returned HTTP 200.
  - The matching `backtest_timing` log lines for that request and two more concurrently in-flight browser-originated requests for the same date show `total_ms` of 9548, 54483, and 54328 — i.e., two of the three concurrent first-touch requests for this date took roughly **54 seconds** each.
  - Critically, in every one of those same log lines, `backfill_forward_returns_ms` stayed small (13.6ms, 12.2ms, 79.9ms) and `write_taken=False` — i.e., the function this iteration's fix actually touches was NOT the source of the delay. The overwhelmingly dominant cost was a separate logged field, `ensure_loop_ms` (9288ms, 54281ms, 54084ms on those same three lines), that this iteration's spec/plan/surface-map do not mention anywhere.
  - Repeating the identical `curl` for the same date immediately afterward returned in 0.13s and then 0.08s — i.e., the cost is a one-time, per-date "cold" cost, not a persistent regression on every request for that date.
  - I am reporting only the measured facts and the literal log field names above, per this agent's "don't speculate about root causes" instruction — I am not asserting what `ensure_loop_ms` is or attributing it to this iteration's diff. Given it is a distinctly-named, separate timing field from `backfill_forward_returns_ms` (which behaved correctly and consistently with this iteration's intended fix throughout, here and in UT-02/03), and given the surface map's own confirmation that `backfill_run_forward_returns` is the only function this iteration touches, this observation reads as a pre-existing characteristic of a different subsystem, not a regression introduced by this iteration's diff. It is still a real, current, reproducible, multi-second-to-roughly-a-minute stall a user would hit on the first view of any historical as-of this backend process hasn't served yet, so I'm surfacing it rather than omitting it.

### UT-05 — An unrecognized `?asof=` deep link degrades safely to the latest view
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-19-evidence/UT-05-unrecognized-asof.png`
- The unrecognized date was silently discarded exactly as designed: the rendered badge and as-of control both showed "latest," and the address bar's query string was removed once the page settled (`window.location.href` evaluated to the bare `/backtest` path, confirmed programmatically, not just visually).

### UT-06 — `/backtest` and the historical as-of control remain discoverable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-19-evidence/UT-06-asof-popover.png`, `UT-06-dashboard-sidebar.png`
- 1-click path from the Dashboard confirmed (no login gate anywhere in the app). The as-of popover opened by clicking `[aria-label="View as-of date"]` is a full calendar picker (month/year dropdowns, "1862 selectable dates", a "Latest · 2026-07-22" quick-jump) — the same shared control referenced elsewhere in the app (e.g. the Dashboard's own "Data as-of 2026-07-22" badge), confirming it is not a page-local control reimplemented for `/backtest`.

---

## Failed Tests

None. No test case failed this run.

---

## Skipped Tests

### UT-J-04 — J-04: Non-blocking boot with visible status (required-still-passing regression journey)
**Verdict:** SKIPPED
**Reason:** J-04's `docs/goal.md` acceptance requires actually restarting the backend (steps 1, 3, 6) and forcibly killing it (step 4) to observe the boot-phase badge, the crash presentation, and the post-restart interrupted-job state. This dispatch's own operator note is explicit: "You cannot start/stop services; backend :8255 + frontend :3255 are up." Independently, both `docs/phases/goal-ops-hardening-iter-19.md` and `runs/goal-ops-hardening-iter-19/plan.md` carry this exact disruptive kill/restart replay as owner/operator-gated ("owed since iter-15," blocked by the AG-10 ingest-trigger safety classifier in prior sessions, "not this iteration's blocker") with TC-8 — a non-disruptive `GET /api/health` poll — named as this iteration's explicit substitute for the Definition of Done. There is no partial, non-disruptive slice of J-04's own numbered steps that is meaningfully browser-observable without an actual restart/kill event, so no attempt (partial or otherwise) was made against the live service.

Supplementary, non-blocking context gathered instead (does **not** constitute a J-04 pass — no restart or kill was performed this run, so none of J-04's own acceptance criteria were exercised):
- `GET /api/health` → HTTP 200, `{"status":"ok", ..., "readiness":"ready"}`.
- The last 3 startup/shutdown pairs visible in `logs/backend.log` are all clean (`Application shutdown complete` immediately followed by a fresh `Application startup complete` / `Uvicorn running`) — i.e., no evidence of an unclean/abrupt truncation in the currently-visible log tail. This is consistent with TC-8's own non-disruptive bar (no new crash banner since the last recorded one) but is unrelated to — and not a substitute for — J-04's own kill/restart-triggered acceptance criteria.
- No golden replay script was written for J-04 this run (best-effort, per this agent's instructions) since the journey was not verified PASS.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` MCP — worked normally this run (the PUMP NOTE's expected wedge did not reproduce; one quick probe succeeded and the full plan was executed live)
- **Test Date:** 2026-07-24
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-19-evidence/`
