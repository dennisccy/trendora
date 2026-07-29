# Phase goal-ops-hardening-iter-32 — UI Test Results

**Phase:** goal-ops-hardening-iter-32
**Date:** 2026-07-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- This iteration is backend-only per reports/phase-goal-ops-hardening-iter-32-ui-test-plan.md
     ("Status: N/A — Backend-only phase. No UI tests required.") and the functional test plan
     (reports/qa/goal-ops-hardening-iter-32-test-plan.md, "Browser tests: 0 (Frontend Present: no)").
     The dev/QA report already executed and PASSED the live full-deep-basis warm (TC-4/TC-5, J-07
     steps 1-3) twice via direct process/API measurement, with exact evidence recorded in
     docs/handoffs/goal-ops-hardening-iter-32-dev.md and reports/perf-budgets.md's new "Iteration 32"
     section. This agent did NOT re-trigger a third full 5-horizon warm (AG-10 hardware-protection:
     heavy compute bursts have caused two prior hardware resets on this host, and the dev/QA evidence
     is already exhaustive and independently re-checkable read-only). Instead this agent independently
     verified, via real Chrome MCP browser interaction against the live app, the ONE actual UI surface
     this iteration's fix underlies (`/backtest`, the page `compute_forward_aggregates` serves) — the
     part of J-07's contract that a live-process/log check alone cannot confirm (does a real user's
     browser actually render the restructured accumulators' output correctly, with zero console
     errors) — plus independently re-derived TC-4's zero-MemoryError claim and TC-5's perf-budgets.md
     entry by reading the artifacts directly rather than trusting the dev/QA report's prose. -->

**Overall:** 1/1 journeys passed (0 skipped)

Required-still-passing journeys J-01, J-03, J-04, J-05, J-08, J-09 were already re-verified by
deterministic golden replay before this run
(`reports/phase-goal-ops-hardening-iter-32-regression-replay-results.md`, 6/6 PASS) — per the
dispatch instructions those are not re-tested or re-emitted here. This run covers exactly this
iteration's target journey, J-07.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | Heavy aggregates never take the service down | smoke | P1 | `/backtest` (the page served by the restructured `compute_forward_aggregates`) renders real by-group/control-group figures with zero console errors and zero backend crash; the dev/QA's independently-recorded live full-deep-basis warm shows zero `MemoryError` and a `VmPeak` margin recorded in `reports/perf-budgets.md` | Live Chrome MCP navigation to `/backtest` rendered the full page including the "Forward-tested evidence" section's `by_bucket`/`by_setup`/`by_regime`/`by_vcp`/`excess`/`control_group` tables with real, non-NA numbers (e.g. Bucket A `+10.68% n=8869`, Excess vs SPY `+0.60% n=749441`, Top-ranked cohort `+6.77% n=36316` vs Random same-sector peers `+6.27% n=22178`) — exactly the outputs the iteration's restructured accumulators produce; browser console showed zero errors (only the standard React-DevTools info line); 6/6 fresh `GET /api/health` polls at 1 Hz returned HTTP 200 during this check. Independently re-derived (read-only, no new compute triggered): `tail -n +133277 logs/backend.log \| grep -c MemoryError` = 0 from this session's own boot banner forward; `reports/perf-budgets.md`'s "Iteration 32" section exists with the recorded live-warm measurement (VmPeak 2,691,600 kB flat across both trials, margin 3,515.5 MB / 57.2% headroom under the 6144 MB cap, 77/77 health polls HTTP 200 across two independent trial dates) | PASS | `reports/qa/goal-ops-hardening-iter-32-evidence/J-07-backtest-forward-aggregates.png` |

---

## Passed Tests

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-32-evidence/J-07-backtest-forward-aggregates.png` (md5 `002926b8161a5f9bef927f23b54308d6` — confirmed fresh and distinct from every other evidence PNG in this iteration's directory and from the recurring byte-identical `eff8f9ad…` capture that has affected J-03/J-04/J-07 in prior iterations)

This iteration's fix (`stock_obs`, the last unbounded accumulator in `compute_forward_aggregates`) has
no new UI surface (`ui-surface-map.md`: "No UI surfaces affected"), so J-07's four acceptance steps this
iteration split across two verification channels, per the execution plan's own note ("QA should run
these as live-process/API-level checks... this matches iter-30/31 precedent"):

1. **Steps 1–3 (full warm, 1 Hz health poll, VmPeak margin)** were already executed live, TWICE, by the
   developer directly against the real ~4.97 GB committed-seed DB (`docs/handoffs/goal-ops-hardening-iter-32-dev.md`
   "Live verification" section) and independently confirmed by the `qa` agent
   (`reports/qa/goal-ops-hardening-iter-32-qa.md`, TC-04/TC-05 rows, both PASS). This agent re-derived
   those claims read-only rather than re-running a third multi-minute 5-horizon warm (AG-10 hardware
   protection — this host has taken two instant hardware resets under prior all-core heavy-compute
   bursts, and a third repeat of an already-exhaustively-documented measurement adds no new evidence):
   - `grep -c MemoryError` over `logs/backend.log` from THIS currently-running process's own boot banner
     (`logs/backend.log:133277`, "Application startup complete.") forward = **0**.
   - `reports/perf-budgets.md` contains a new, populated "## Iteration 32 — live full-deep-basis
     forward-aggregate warm (J-07 step 3, `stock_obs` bound), 2026-07-29 (developer)" section recording
     two independent trials (`2026-07-20`, `2026-07-17`), `VmPeak` flat at 2,691,600 kB across the entire
     measurement window, margin 3,599,856 kB (≈3,515.5 MB, 57.2% headroom) under the 6144 MB
     `server.memory_cap_mb` cap, and 77/77 `GET /api/health` polls returning HTTP 200 throughout both
     trials.
2. **This agent's own live browser check (the part only Chrome MCP can confirm — does the restructured
   accumulator's output actually reach a real user's screen intact):**
   - Navigated to `http://localhost:3255/backtest` (the one page `compute_forward_aggregates` serves).
   - Extracted full page text: the "Forward-tested evidence (expanding window ≤ 2026-07-22)" section
     rendered every `compute_forward_aggregates` output this iteration restructured, with real numbers —
     "Forward return by score bucket" (Bucket A `+10.68% n=8869` through Bucket E `+4.13% n=483441`),
     "Excess vs benchmarks" (`+0.60% n=749441` vs SPY, `-1.28% n=749441` vs QQQ), "Forward return by
     setup type", "by market regime", "VCP vs non-VCP", "Pullback-to-rising-DMA vs not", "Flat-base
     breakout vs not", and "Control-group comparison" (Top-ranked cohort `+6.77% n=36316`, Random
     same-sector peers `+6.27% n=22178`, SPY/QQQ/Sector ETF rows) — none blank, none an error string, no
     partial render.
   - `enable_console_logging` + fresh reload: zero console errors (only the standard "Download the React
     DevTools..." info line).
   - Took a fresh top-of-page screenshot confirming a clean render (heading "Backtest", survivorship-bias
     disclosure banner, market regime 61.86/100, candidate counts, "As-of scan summary" — no error
     banner, no blank page, no Next.js overlay).
   - Ran 6 fresh `GET /api/health` polls at 1 Hz immediately after: 6/6 HTTP 200, `readiness: "ready"`,
     `background_compute.active: []` (idle, consistent with not having triggered a new warm).

**Note on screenshot capture:** attempts to capture a screenshot at a scrolled-down position on this page
consistently returned a blank/near-empty PNG (~9 KB, solid background color) via this session's Chrome MCP
tool, while the identical scroll position's `extract` (DOM text) call correctly returned the full real
content every time and a scroll-position-0 screenshot correctly rendered every time (~197 KB, full visual
content). This reads as a screenshot-capture timing/compositor quirk specific to this tool immediately
after a JS-driven scroll on this page (a real user scrolling with a mouse wheel sees the content render
normally — this was not reproduced as a user-visible defect, only as an automated-capture artifact), not a
product bug — flagging transparently rather than passing off a mismatched screenshot as evidence. The
saved evidence PNG is the confirmed-good scroll-position-0 capture; the deeper "Forward-tested evidence"
section's real values are evidenced by the `extract` text quoted above instead of a matching screenshot.

**Acceptance assessed against J-07's four literal steps:**
- Consistency (single canonical producer) — met: `compute_forward_aggregates` unchanged as the sole
  producer per dev handoff; not re-derived here (code-level claim, not a browser-QA action).
- Correctness (byte-identical payload) — met: covered by the 46-test byte-identity oracle (TC-02, dev/QA
  reports); this agent's live `/backtest` render is consistent with, not a substitute for, that proof.
- Honest status & anti-goals (AG-8) — met: zero unbounded materialization observed live (zero
  MemoryError re-derived above); the page's own "No elapsed forward window for this date yet" /
  "Nothing is fabricated" copy on the per-date scorecard (today's `as_of` `2026-07-22` has no elapsed
  forward window yet) is itself the honest-NA disclosure AG-1/AG-8 require, correctly shown rather than
  fabricated.
- Step 4 (induced memory-pressure abort) — explicitly OUT OF SCOPE this iteration per the phase spec; not
  asserted or attempted by this agent, consistent with the spec.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Golden replay scripts written this run

- `runs/goal-session-ops-hardening/journey-scripts/J-07.json` — REWRITTEN to reflect this iteration's
  actual verified scope. The prior script (from iter-29's drawdown-expectations scope: `/evidence`
  `-7.48%`, `/data` "drawdown expectations") tested a different sub-feature than the one this iteration's
  fix touches. The new script asserts two real post-load values from `/backtest` — the page
  `compute_forward_aggregates` (this iteration's target) actually serves: (1) the "Forward-tested
  evidence" section heading itself renders (proof the section isn't suppressed/erroring), and (2) the
  literal computed figure `n=8869` (Bucket A's real sample size from the restructured `_GroupAcc`/
  `_group_means_from_accs` accumulation path — a value that only exists if the by-group accumulation
  produced correct, non-empty output). Linted (`demo_runner.py --mode lint`) and replayed end-to-end
  (`demo_runner.py --mode verify --base-url http://localhost:3255`) — **PASS**
  (`[demo_runner] verify: 1 journey(s), 0 failed (verdict: PASS)`).

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-29
- **Backend process:** boot banner `logs/backend.log:133277` ("Application startup complete."); zero
  `MemoryError` lines from that line forward at the time of this check
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-32-evidence/`
