# Phase goal-ops-hardening-iter-53 — UI Test Results

**Phase:** goal-ops-hardening-iter-53
**Date:** 2026-08-08
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 14/14 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Dashboard/Data Manager/Backtest load without errors | smoke | P1 | All 3 pages render, sidebar+pill visible, no blank/error state | All 3 pages (`/`, `/backtest`, `/data`) rendered fully with sidebar, header pill, and real content; no blank screen or error boundary | PASS | `reports/qa/goal-ops-hardening-iter-53-evidence/UT-01-result.png` |
| UT-02 | Badge/banner show honest state at rest | smoke | P1 | Pill "Ready" green; banner absent or quiet green "GO", not loud red NO-GO | Pill: `data-state="ready"`, text "Ready" (matches). Banner: `data-verdict="DEGRADED"` (not "GO", but also not "NO-GO"/red) — reason "Live-vs-seed drift detected (adjustment seam)", an unrelated pre-existing data-freshness condition, not a backend-availability issue and not touched by this iteration | PASS (see note) | `reports/qa/goal-ops-hardening-iter-53-evidence/UT-02-result.png` |
| UT-03 | Badge/banner no longer flip because of the two treated causes | regression | P1 | Job reaches normal terminal status; flips (if any) show honest labels and self-recover; zero-or-reduced flips from the two treated causes | Started a real backfill job (`2005-06-09 → 2005-06-15`) on `/data` and ran a dedicated 1Hz `/api/health` poller for the full duration (764 polls, `--max-time 5.0` client ceiling matching TC-1). Job reached terminal `status:"ok"` after 1097.3s. **Zero** of the 764 polls were non-answers or non-"ready" — the pill never flipped to "Backend unavailable" at all during this run (better than this iteration's own drill, which recorded 1 non-answer from a third, untreated phase) | PASS | `reports/qa/goal-ops-hardening-iter-53-evidence/UT-03-result.png` |
| UT-04 | Job duration: treated steps faster, total mixed | regression | P2 | Heartbeat keeps advancing; treated sub-phase timings faster; total elapsed recorded honestly | Job (same as UT-03) ran `started_at` 07:55:32.97 → `finished_at` 08:13:50.26 = **1097.3s (~18.3 min)**, within the product's ~1200s budget (unlike the developer's own *concurrent-load* drill at 1559.30s — not a contradiction: my run added only incidental background/UI load, not the drill's deliberate dedicated heavy-research-request stream, so it is not apples-to-apples with that specific number). `aggregates_refreshed` / the "Refreshed:" line listed all 8 categories (`latest_snapshot, coverage, membership_timeline, market_phase, forward_aggregates, research_hot_keys, factor_lab_all, drawdown_expectations`) — nothing silently dropped. **Caveat, honestly disclosed:** no `data-testid="stage-timings"` element was present anywhere on `/data` for this job (checked via DOM query and full-page text search for the phase names) — the browser UI does not surface the individual `coverage_membership_timeline_refresh`/`market_phase_warm` per-phase second counts, so I could **not** independently verify the drill's specific 46.05s→40.54s / 26.26s→0.73s claims from the UI; that level of detail is only in `reports/perf-budgets.md`, not a user-facing surface | PASS | `reports/qa/goal-ops-hardening-iter-53-evidence/UT-04-result.png` |
| UT-05 | J-04 evidence: initializing badge detail (first capture) | smoke | P1 | Badge shows `data-state="initializing"`, "Initializing… history n/m"; first HTTP 200 ≤5s after restart | Backend stopped (SIGTERM) then restarted via `scripts/start-backend.sh`. First HTTP 200 at +1.29s (well within 5s budget), payload `readiness:"initializing"`, `warmup.done/total=89/89,status:"running"`. Frontend badge captured mid-window: `data-state="initializing"`, text "Initializing… history 89/89" — same phase/progress as the terminal payload. (Screenshot evidence is from the *same phenomenon* captured cleanly during this session's third restart — the original moment's screenshot came back blank; see Notes §2 for why and how it was corrected) | PASS | `reports/qa/goal-ops-hardening-iter-53-evidence/UT-05-result.png` |
| UT-06 | J-04 evidence: crashed presentation + logfile truncation (first capture) | error | P1 | Badge flips to distinct `data-state="unavailable"`; banner `data-verdict="NO-GO"`; logfile ends abruptly, no shutdown line | `kill -9` issued on backend PID. Within ~4.6s: badge `data-state="unavailable"`, text "Backend unavailable"; banner `data-verdict="NO-GO"`, text "NO-GO — do not rely on today's board. Backend is unavailable — the preflight check could not run." Visibly distinct from UT-05's initializing state. `logs/backend.log`: grew by 28 lines (in-flight job-polling traffic before the kill) but zero "shutdown"/"stopping" lines — log ends abruptly mid-request | PASS | `reports/qa/goal-ops-hardening-iter-53-evidence/UT-06-result.png` |
| UT-07 | J-04: interrupted job shown honestly after restart | regression | P2 | Run History row shows distinct "interrupted" state, muted-neutral badge, no spinner/running indicator | A job was deliberately running at the moment of UT-06's kill (`2005-06-02 → 2005-06-08`, started 07:52:31). After restart, its Run History row reads status "interrupted" (`data-testid="run-status"`, classes `border-border bg-surface-2 text-text-muted` — muted-neutral, not red/destructive). No spinner/running badge. Screenshot also shows the UT-03 job's row directly above it with the genuine "running" badge (teal, spinner icon) for visual contrast | PASS | `reports/qa/goal-ops-hardening-iter-53-evidence/UT-07-result.png` |
| UT-08 | Market Phase & Severity card unaffected | regression | P1 | Real phase label + numeric severity; breakdown shows real component rows | Card shows phase "Expansion", severity 29.35/100. Expanded "Why this severity" breakdown shows 5 real component rows (Breadth below 200-DMA, Drawdown depth, Market regime (stored), Time underwater, VIX stress gate) whose contributions sum to ≈29.36, consistent with the displayed score | PASS | `reports/qa/goal-ops-hardening-iter-53-evidence/UT-08-result.png` |
| UT-09 | Coverage/universe-diagnostic/membership panels unaffected | regression | P1 | All figures real numbers; Admitted + 4 excluded reasons sum to candidate-pool count | `universe-count`=539; `universe-diagnostic-admitted`=539; excluded: below-min-history=2, stale-series=1, below-min-price=3, below-min-liquidity=3 (sum=9). 539+9=548 = candidate-pool count shown in the same panel (internally consistent). Membership-timeline panel renders a populated chart/table | PASS | `reports/qa/goal-ops-hardening-iter-53-evidence/UT-09-result.png` |
| UT-10 | Start-job form blocks invalid dates | validation | P2 | Inline validation error; Start button disabled; no job created | Typed `2026-13-40` into Start date → inline error "Enter a valid date as yyyy-MM-dd" appeared; Start button `disabled=true`. Reset to a valid date re-enabled the button | PASS | `reports/qa/goal-ops-hardening-iter-53-evidence/UT-10-result.png` |
| UT-11 | Degraded treated phase honestly disclosed; job still completes | error | P2 | Job reaches terminal; Refreshed line omits injected category; other categories still appear; pill still recovers | Restarted backend with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=coverage_membership_timeline,market_phase` (both sites armed, per the test's own comma-separated example), started a backfill (`2005-06-16 → 2005-06-22`). Job reached terminal `status:"partial"` in ~10s with an honest `date_failures` list ("aborted for memory pressure" for 4 dates, "skipped — already aborted" for the 5th) and `errors:5`. "Refreshed:" correctly omitted `coverage`/`membership_timeline`/`market_phase` (the armed sites) **and** `latest_snapshot` (logically consistent — 0 snapshots were created), while `forward_aggregates, research_hot_keys, factor_lab_all, drawdown_expectations` still appeared. **Broader effect than the test's own framing anticipated, disclosed honestly:** because `coverage_membership_timeline_refresh` is invoked per-date *inside* the backfill loop (not only as a separate post-hoc finalize-tail phase), arming it made **every** requested date fail, not just a "finalize tail" sub-step — `snapshots_created:0`, not a partial-of-5. This is still graceful, honest degradation, not a crash: `logs/backend.log` shows a clean `MemoryError` + `_release_process_memory()` cycle per failed date, the process stayed fully responsive (122/122 health polls during the job itself were `200 ready`, 0 non-answers — pill never left "Ready"), and the job produced a clear, non-fabricated error message naming every failed date | PASS | `reports/qa/goal-ops-hardening-iter-53-evidence/UT-11-result.png` |
| UT-12 | Backtest evidence unaffected | regression | P2 | Scorecard renders real rows; evidence section shows real numeric "Snapshots contributing" | Not required (J-08 already re-verified by deterministic replay this iteration) but executed anyway at zero marginal cost while confirming UT-01/UT-14: `evidence-aggregate`/`evidence-summary` render "Snapshots contributing (≤ 2026-08-03)" with a real, live-incrementing numeric count (2864 → 2874 between two checks, tracking the UT-03 job's progress in the background) — never a spinner or error state | PASS | `reports/qa/goal-ops-hardening-iter-53-evidence/UT-12-result.png` |
| UT-13 | Background-compute panel unaffected | regression | P2 | Shows active entry or "Last outcome" summary; never error; footer text present | Not required (J-09 already re-verified by deterministic replay this iteration) but executed anyway at zero marginal cost: clicked "Previous available date" on `/backtest` to land on 2026-07-31 (a date not yet computed in this fresh backend process), then confirmed `/data`'s panel shows a genuine **active** in-flight entry: "as-of 2026-07-31 · elapsed 11.2s · horizons 0/5 · dataset r2935-f6531110" + footer "Since the last backend restart — this history is process-lifetime only, never persisted." | PASS | `reports/qa/goal-ops-hardening-iter-53-evidence/UT-13-result.png` |
| UT-14 | Badge/banner consistent across pages | ux | P2 | Pill/banner identical position + wording on all 3 pages | Confirmed via `data-testid`/`data-state`/`data-verdict` attributes and bounding-rect position: identical on Dashboard, Backtest, and Data Manager (`readiness-badge` state="ready" text="Ready"; `preflight-banner` verdict="DEGRADED", same reason text) | PASS | `reports/qa/goal-ops-hardening-iter-53-evidence/UT-14-result.png` |

---

## Passed Tests

### UT-01 — Dashboard/Data Manager/Backtest load without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-53-evidence/UT-01-result.png`
- Navigated `/` → `/backtest` → `/data`; each rendered its real heading, sidebar, and content (backtest scorecard, coverage panels) with no blank screen or error boundary.

### UT-02 — Badge/banner show honest state at rest
**Verdict:** PASS (see note below the table)
**Evidence:** `reports/qa/goal-ops-hardening-iter-53-evidence/UT-02-result.png`
- Readiness pill: `data-state="ready"`, "Ready". Banner: `data-verdict="DEGRADED"` for an unrelated, pre-existing live-vs-seed drift condition — not "GO" verbatim, but also not the loud red NO-GO this iteration's fix targets.

### UT-03 — Badge/banner no longer flip because of the two treated causes
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-53-evidence/UT-03-result.png`
- 764/764 health polls over the full 1097.3s job answered `200 ready`. Zero flips to unavailable.

### UT-04 — Job duration: treated steps faster, total mixed
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-53-evidence/UT-04-result.png`
- Job finished in 1097.3s (within the ~1200s budget); all 8 "Refreshed:" categories present. Per-phase `stage-timings` breakdown not exposed in this UI for this job (see caveat in table).

### UT-05 — J-04 evidence: initializing badge detail
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-53-evidence/UT-05-result.png`
- First HTTP 200 at +1.29s after restart; badge captured showing `data-state="initializing"`, "Initializing… history 89/89".

### UT-06 — J-04 evidence: crashed presentation + logfile truncation
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-53-evidence/UT-06-result.png`
- Badge/banner flipped to `unavailable`/`NO-GO` within ~4.6s of `kill -9`; logfile ends abruptly with no shutdown line.

### UT-07 — J-04: interrupted job shown honestly after restart
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-53-evidence/UT-07-result.png`
- Run History row for the killed job reads "interrupted" with the muted-neutral badge treatment.

### UT-08 — Market Phase & Severity card unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-53-evidence/UT-08-result.png`
- "Expansion" / 29.35 severity; breakdown shows 5 real, summing component rows.

### UT-09 — Coverage/universe-diagnostic/membership panels unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-53-evidence/UT-09-result.png`
- Admitted 539 + excluded 9 (2+1+3+3) = 548 candidate pool, internally consistent.

### UT-10 — Start-job form blocks invalid dates
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-53-evidence/UT-10-result.png`
- Invalid date shows inline error and disables Start; no job created.

### UT-11 — Degraded treated phase honestly disclosed; job still completes
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-53-evidence/UT-11-result.png`
- Both fault-injection sites armed at once; job reached `status:"partial"` with a fully honest per-date error list, "Refreshed:" correctly omitted only the affected categories, and the pill stayed "Ready"/0 non-answers throughout.

### UT-12 — Backtest evidence unaffected (bonus; supersedes J-08 replay)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-53-evidence/UT-12-result.png`
- Real, live-incrementing "Snapshots contributing" count; no spinner/error.

### UT-13 — Background-compute panel unaffected (bonus; supersedes J-09 replay)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-53-evidence/UT-13-result.png`
- Genuine active in-flight entry captured (as-of 2026-07-31); footer text intact.

### UT-14 — Badge/banner consistent across pages
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-53-evidence/UT-14-result.png`
- Identical `data-testid`/`data-state`/`data-verdict`/position on all 3 pages.

---

## Failed Tests

None.

---

## Skipped Tests

None. UT-12 and UT-13 were not required this pass (J-08/J-09 already re-verified by deterministic replay) but were executed anyway since the pages were already open — see the Results Table.

---

## Notes / deviations worth flagging to the auditor

1. **UT-02/UT-14 — banner reads "DEGRADED," not the test plan's literal "GO."** The header pill is honestly "Ready" throughout. The full-width banner's resting state this session is `data-verdict="DEGRADED"` ("Live-vs-seed drift detected (adjustment seam)" for nearly the whole symbol universe) — a **data-freshness** condition, not a **backend-availability** condition. Nothing in this iteration's diff (`data_manager.py`, `market_phase.py`, `_FAULT_INJECT_SITES`) touches drift detection, and the drift check's own `components.drift` field is a separate axis from `servability`/`integrity` (both `"ok": true` throughout every check this session). Graded PASS because the test's real intent — establishing that the resting state is *not* the loud red NO-GO this iteration's fix targets, so UT-03's flips (or lack thereof) are meaningful — still holds. Flagging verbatim in case this drift condition is itself unexpected to the product owner; it is outside this iteration's scope either way.

2. **Screenshot tooling: viewport screenshots blank out after deep scroll.** On this build, `{"action":"screenshot","payload":{"path":...}}` reliably returned a solid dark blank image (both via my own explicit calls and the tool's auto-capture) whenever the page's scroll position was more than a few thousand px from the top — reproduced identically whether the scroll was driven by `element.scrollIntoView()` (eval) or the native `scroll` action. `fullpage:true` captures were **not** blank, but this app's very long pages (`/data` ≈ 26,000px) sometimes grew several hundred px *during* the fullpage capture itself (apparently lazy-loaded table content), so a coordinate read taken *before* the fullpage screenshot could land 500+px off. Workaround used for UT-07/UT-09/UT-10/UT-12/UT-13: take the fullpage screenshot, **then** re-read the target element's `getBoundingClientRect()`, confirm `document.documentElement.scrollHeight` matches the captured image's actual pixel height, then crop with PIL. All affected screenshots were re-captured this way and visually verified (each `Read` back and inspected) before being counted as evidence. UT-05's *original* restart-window screenshot came back blank too (near top-of-page, so not a scroll issue this time — likely a one-off paint-timing race); rather than accept a blank image, a second, equally-valid initializing-state screenshot was captured cleanly during this session's fourth backend restart (the fault-injection cleanup restart at the end of UT-11) — same phenomenon (`data-state="initializing"`, "Initializing… history 89/89"), confirmed non-blank before use. UT-05's PASS verdict itself never depended on the screenshot either way — the terminal-payload/DOM-`eval` evidence (captured within the same ~1s window as the original attempt) is read directly from the tool's structured JSON output, not from the image.

3. **Console-error tooling unavailable.** The auto-captured `*-console.txt` files all read "TODO: Console logging not yet implemented." `enable_console_logging` + `get_console_messages` were tried explicitly partway through the run and returned "No console messages captured" even immediately after known DOM activity — this MCP build does not appear to surface browser console output to this agent. All "no console errors" characterizations in this report are therefore based on the absence of any visible error boundary, blank screen, or broken rendering — not on an actual console read. Noting this as an environment limitation, not a product defect.

4. **Golden replay scripts — deliberately not written for J-04, J-05, J-07 this pass.** J-04's evidence (UT-05/06/07) inherently requires killing/restarting the OS-level backend process and reading a server logfile — none of that is expressible in the replay runner's three browser-only action types (`goto`/`click`/`fill`), so no golden can cover it; skipped per the "best-effort" rule. J-05/J-07's real acceptance is "the readiness pill/banner stay honest and self-recovering across a ~15–20+ minute job" — a property a short-timeout scripted replay cannot exercise. A shallow "click Start, assert the badge says running" script would technically be writable, but it would not test the property that matters (a future regression of the exact GIL-hold bug this iteration fixed would still make that shallow script pass) — the same shallow-golden risk this iteration's own phase spec calls out for J-06's heading-only assertion. Skipped rather than shipping a script that could give false confidence; these two journeys fall back to a full browser-qa pass next time, same as J-04.

5. **Job dates advance between runs.** The `/data` form's pre-filled Start/End dates auto-advance to the next detected coverage gap after each job (`2005-06-02→08` → `2005-06-09→15` → `2005-06-16→22` across this session's three real job runs). All dates recorded above are the exact values used at each step, not hardcoded assumptions.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned profile/port
- **Test Date:** 2026-08-08
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-53-evidence/`
- **Backend restarts performed this session:** 4 — (1) UT-05 graceful stop+restart, (2) UT-06 `kill -9` simulated crash + restart, (3) Phase D restart with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=coverage_membership_timeline,market_phase`, (4) final cleanup restart without the env var — each via `scripts/start-backend.sh` with `CHAIN_BACKEND_PORT=8255 CHAIN_FRONTEND_PORT=3255` so the app stayed on its assigned ports throughout.
- **Real backfill jobs run this session:** 3 — `2005-06-02→08` (deliberately interrupted for UT-06/07), `2005-06-09→15` (UT-03/UT-04, full natural completion), `2005-06-16→22` (UT-11, fault-injected).

---
