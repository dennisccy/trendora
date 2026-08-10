# Phase goal-ops-hardening-iter-57 — UI Test Results

**Phase:** goal-ops-hardening-iter-57
**Date:** 2026-08-10
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 15/16 tests passed (1 skipped, 0 failed)

---

## Re-run context — the prior FAIL was a deployment artifact, now fixed and re-verified

My first pass on this iteration recorded **FAIL** because the running frontend build's
`NEXT_PUBLIC_API_URL` was baked at port 8257 while the live backend served on 8255 (a stale
`.next` build left over from an earlier port assignment). The coordinator rebuilt the frontend
against the correct port and confirmed it independently. I re-verified the fix myself before
re-running anything:

- `grep -rho 'localhost:82[0-9][0-9]' apps/frontend/.next/static/chunks/` → `1  localhost:8255`
  (previously showed `8257`).
- `curl http://localhost:8255/api/health` → `200`, healthy payload, `readiness: "ready"`.
- `curl http://localhost:3255/` → `200`.
- Live in the browser: `/data`, `/stocks/AAPL`, `/`, `/backtest`, `/scanner-runs` all render real
  data (591 symbols, real charts, real job history) instead of the "Backend unavailable" banner
  seen in the first pass.

With the real backend reachable, I re-executed every UT-XX test case and every regression
journey (J-01/J-03/J-04/J-05/J-08/J-09) live end-to-end — including two real backfill jobs (one
zero-work re-run over already-snapshotted ranges, one genuine ~18-minute compute over a
previously-unsnapshotted historical day) — rather than relying on the earlier blocked state.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/data` loads without errors | smoke | P1 | Heading + `availability-heatmap` card render, no console errors | "Data Manager" heading renders; `availability-heatmap` card present with 5,391 real `availability-cell` elements, no stale-notice, no empty state | PASS | `reports/qa/goal-ops-hardening-iter-57-evidence/UT-01-result.png` |
| UT-02 | `/stocks/AAPL` loads without errors | smoke | P1 | "AAPL" + `chart-window-caption` with real text | Full page renders: "AAPL" heading, scores (Leadership 55.03, Entry Quality 44.20, Risk 35.41), `chart-window-caption` = "3189 bars · as of 2026-08-03 · history since 1996-01-02 · older bars weekly-sampled" | PASS | `reports/qa/goal-ops-hardening-iter-57-evidence/UT-02-result.png` |
| UT-03 | Stale "updating" banner appears during a job | happy-path | P1 | Start a job, reload, see `availability-stale-notice` | Started a real backfill (2010-11-10, shared with J-05 to avoid a second heavy job — see note below); a fresh tab load of `/data` mid-job showed `availability-stale-notice` = "Data as of r2945-rc2945-b2026-08-03-bc3306390-h200 — updating" directly above the calendar grid, with 5,391 real `availability-cell` elements still rendered (no empty state) | PASS | `reports/qa/goal-ops-hardening-iter-57-evidence/UT-03-result.png` |
| UT-04 | Idle heatmap unchanged (no banner) | regression | P1 | Normal colored calendar grid, no stale notice | After the backfill job completed and no job was running, `/data` showed 5,391 `availability-cell` elements, `availability-stale-notice` absent (`false`), "Job running" text absent | PASS | `reports/qa/goal-ops-hardening-iter-57-evidence/UT-04-result.png` |
| UT-05 | Availability error state unaffected | error | P2 | Blocking `**/api/data/availability**` shows `availability-error` with specific text | Not executable: `mcp__plugin_superpowers-chrome_chrome__use_browser`'s action set (navigate/click/type/extract/screenshot/eval/select/attr/await_element/await_text/tab mgmt/hover/scroll/keyboard/viewport/cookies/console) has no request-blocking or route-interception primitive, so the test's DevTools-blocking precondition cannot be set up with this tool | SKIP | none |
| UT-06 | Readiness badge answers within budget | regression/perf | P1 | `data-state="ready"`, "Ready" text, `GET /api/health` well under 100ms on 3 pages | Checked `/`, `/stocks/AAPL`, `/scanner-runs`: `readiness-badge` reads `data-state="ready"` on all three. Real browser-observed `/api/health` durations via `performance.getEntriesByType('resource')`: 28ms, 24ms, 47ms, 38ms, 34ms, 23ms — all well under the 100ms budget | PASS | `reports/qa/goal-ops-hardening-iter-57-evidence/UT-06-result.png` |
| UT-07 | Stock chart answers within budget | regression/perf | P1 | `chart-window-caption` real text, MA lines render, bars request well under 1.5s | `GET /api/stocks/AAPL/bars?through=latest` measured 3ms (browser `performance` API); caption "3189 bars · as of 2026-08-03 · history since 1996-01-02 · older bars weekly-sampled"; 20/50/150/200-DMA legend entries render | PASS | `reports/qa/goal-ops-hardening-iter-57-evidence/UT-07-result.png` |
| UT-08 | Banner discoverable, calm styling | ux | P2 | Compare stale banner styling to `coverage-stale-notice` | Live `availability-stale-notice` className: `"border-b border-border bg-surface-2 px-4 py-2 text-xs text-text-muted"`. Source-verified `coverage-stale-notice` (`apps/frontend/app/data/page.tsx:760-761`) uses the **byte-identical** className string. No red/amber/alarm coloring, no error icon on either; text is factual ("Data as of `<version>` — updating") and sits directly above the calendar grid without overlapping cells | PASS | `reports/qa/goal-ops-hardening-iter-57-evidence/UT-08-result.png` |
| UT-09 | "Refreshed" note unaffected on success | regression | P2 | Job history row shows `aggregates-refreshed` text | Multiple `aggregates-refreshed` rows present in job history, e.g. "Refreshed: latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, factor lab all, drawdown expectations" | PASS | `reports/qa/goal-ops-hardening-iter-57-evidence/UT-09-result.png` |
| UT-10 | Rollback honesty fix (unit test) | regression | P3 | Both rollback tests pass, assert `persisted_this_call is False` | `pytest tests/test_data_manager.py tests/test_indexes.py -k rollback -v` → **2 passed** (re-ran twice, 0.44s / 0.59s) | PASS | none (backend-only) |
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | Full backfill/zero-work/persistence journey completes on `/data` | Live-replayed the golden exactly: May range → "19/19 dates", `stage-timings` present, "28 calendar days · 19 already snapshotted · 9 non-trading", `zero-work-note` present; weekend-only range → "0/0 dates", "2 calendar days · 0 already snapshotted · 2 non-trading", job-status "no new snapshots" (visually distinct from success); reload → both runs persist ("Run history" + both breakdown strings still present); `/scanner-runs/748` → "as of 2026-05-29" | PASS | `reports/qa/goal-ops-hardening-iter-57-evidence/J-01-verify.png` |
| UT-J-03 | No per-run range cap | regression | P1 | >370-day backfill accepted, chunk-executes | Submitted 2025-06-01 → 2026-07-17 (412 calendar days). No "range too large"/cap rejection. Result: "283/283 dates", `stage-timings` present, "412 calendar days · 283 already snapshotted · 129 non-trading", progress showed "chunk 5/5" (chunked execution confirmed) | PASS | `reports/qa/goal-ops-hardening-iter-57-evidence/J-03-verify.png` |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | Golden's own documented scope: steady-state regression guard only (the restart/crash/interrupted-job behavior was already proven live in iter-53 per this golden's `_notes`; killing the backend mid-replay is explicitly out of scope for a browser-driven golden and for this agent's standing "never restart the app" rule) | `/` → `readiness-badge[data-state="ready"]` found; `preflight-banner` testid present; `/data` → `last-run-status` testid present (persisted `data_provider_runs`-backed field, no live job needed) | PASS | `reports/qa/goal-ops-hardening-iter-57-evidence/J-04-verify.png` |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | Backfill one unsnapshotted day, confirm storage-served aggregates | Verified 2010-11-10 had 0 `scanner_runs` rows immediately before running. Started backfill; `job-status`="running" confirmed live (not accepted-then-never-run); polled to real completion (~18 minutes, matching this golden's documented 11-19 min range) → `stage-timings` present, `backfill-breakdown`="1 calendar day · 0 already snapshotted · 0 non-trading", "1/1 dates" and "1 snapshots" in body, `aggregates-refreshed`="Refreshed: latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, availability heatmap, factor lab all, drawdown expectations"; `/scanner-runs` → clicked through to run 2946 → "Immutable snapshot — as of 2010-11-10" header, "Entry Quality" column renders (stored leaderboard, not the empty state) | PASS | `reports/qa/goal-ops-hardening-iter-57-evidence/J-05-verify.png` |
| UT-J-08 | Backtest serves from storage only | regression | P1 | `/backtest` serves last-good/refreshing/fresh states within budget | `/backtest` loads real data: `evidence-aggregate` and `evidence-summary` testids present, "Snapshots contributing (≤ 2026-08-03): 2884" text present. Bonus live confirmation of the refreshing-indicator behavior: while viewing a historical as-of whose evidence was mid-compute, the page showed "Refreshing — showing the last complete evidence... evidence as of 2026-07-22, generated 2026-07-31 13:12:40" instead of a blank/partial state | PASS | `reports/qa/goal-ops-hardening-iter-57-evidence/J-08-verify.png` |
| UT-J-09 | Discloses in-flight background-compute activity | regression | P1 | Badge + `/data` panel show background-compute disclosure during a triggered BCW | Clicking `/backtest`'s "Previous available date" back to 2026-07-30 then 2026-07-29 (dates not yet cached under the live dataset version) triggered two real, simultaneous background-compute windows. Badge showed "Ready" + "background compute running (2)". `/data`'s `background-compute-panel` showed both `background-compute-active-row`s live — "as-of 2026-07-30 · elapsed 1m 33s · horizons 3/5 · dataset r2945-f6545585" and "as-of 2026-07-29 · elapsed 36.9s · horizons 0/5" — plus the exact text "Since the last backend restart — this history is process-lifetime only, never persisted." After completion, `GET /api/health.background_compute.recent_outcomes` showed both windows with real measured durations (144486ms, 119919ms) and the `/data` panel correctly flipped to `background-compute-idle`="No background compute running." | PASS | `reports/qa/goal-ops-hardening-iter-57-evidence/J-09-verify.png` |

---

## Passed Tests (highlights — full detail in the table above)

### UT-01, UT-02 — smoke
Both core pages render completely with real backend-served data now that the port mismatch is fixed. No blocked/error states.

### UT-03 / UT-08 — combined evidence, one job
To respect AG-10 (avoid stacking heavy computes), I combined UT-03's stale-banner trigger with
UT-J-05's real backfill (2010-11-10) instead of running a second heavy job — starting a real
backfill and creating a genuinely new snapshot is what actually exercises the finalize-tail
"updating" window; a same-day "Fetch" job (tried first) completed in ~4s, too fast to reliably
catch mid-flight. A second browser tab loaded `/data` fresh while the backfill was in flight and
observed the stale notice with real cells still rendering. UT-08's styling comparison used one
live element (`availability-stale-notice`'s className) plus a source-code check
(`apps/frontend/app/data/page.tsx:760-761`) proving `coverage-stale-notice` uses the byte-identical
className — a valid substitute for a simultaneous live comparison since `coverage-stale-notice`
was not itself stale at observation time.

### UT-J-01, UT-J-03 — zero-work journeys
Both ranges were already fully snapshotted from earlier sessions, so both replayed as fast,
honest zero-work confirmations exactly matching their golden scripts' recorded expectations —
no new heavy computation triggered.

### UT-J-05 — the one real heavy job this pass
2010-11-10 was confirmed to have 0 `scanner_runs` rows before starting (per the golden's own
rotation discipline). I started the backfill, confirmed it was genuinely live (`job-status`:
"running"), then polled the database directly (`data_provider_runs.status`) every 20s in a
single bounded Bash call rather than leaving anything detached, until it finished naturally at
~18 minutes — consistent with this golden's documented 11-19 min range. All of its assertions
matched exactly.

### UT-J-08, UT-J-09 — background-compute disclosure
Walking `/backtest`'s "Previous available date" control back past the two dates already cached
under the live dataset version (`r2945-f6545585`) reliably produced two concurrent, real
background-compute windows, which both the badge and the `/data` panel disclosed honestly and
in real time, then correctly resolved to a last-outcome/idle state after completion.

---

## Skipped Tests

### UT-05 — Availability heatmap error state is unaffected
**Verdict:** SKIPPED
**Reason:** The `mcp__plugin_superpowers-chrome_chrome__use_browser` tool's action set has no
request-blocking / network-interception primitive (confirmed via its `action="help"` enum), so
the test's precondition — "add a DevTools request-blocking rule for
`**/api/data/availability**`" — cannot be set up with this tool. This is a tool-capability gap,
unrelated to app behavior; nothing about this iteration's code is implicated.

---

## Golden Replay Scripts

All six regression journeys (J-01, J-03, J-04, J-05, J-08, J-09) were live-replayed against
their **existing** golden scripts in `runs/goal-session-ops-hardening/journey-scripts/`, step for
step, and every one passed exactly as written — no edits were needed. The earlier stored
replay-lane FAILs for these six were fully explained by the (now-fixed) port mismatch, not by
stale goldens, so nothing needed repair. Per the coordinator's explicit instruction, `J-06.json`
was not touched (its paired budget-gate/sabotage-proven tripwire is out of scope for this pass
and is not one of the six journeys I was asked to re-verify).

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (pinned profile/CDP port)
- **Test Date:** 2026-08-10
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-57-evidence/`
- **Note:** `performance.getEntriesByType('resource')` (read via `eval`) was used for real
  browser-observed endpoint timings since this Chrome MCP tool exposes no dedicated Network-tab
  action; console-log capture is listed as "not yet implemented" by the tool itself, so UT-01/
  UT-02's "no console errors" sub-criterion could not be independently verified this pass (page
  rendering and DOM content were fully verified by other means).
