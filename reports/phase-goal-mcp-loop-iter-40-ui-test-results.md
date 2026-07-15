# Phase goal-mcp-loop-iter-40 — UI Test Results

**Phase:** goal-mcp-loop-iter-40
**Date:** 2026-07-15
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 0/16 tests passed (16 skipped)

---

## Precondition check

- **Frontend reachability:** PASS — `curl -s -o /dev/null -w "%{http_code}" http://localhost:3255` returned `200`.
- **Backend reachability / readiness:** PASS — `GET http://localhost:8255/api/data` returned coverage data (590 symbols, `universe_asof: 2026-07-01`, 90 snapshot dates).
- **`risk_budget` field precondition (per pump note):** PASS — `GET http://localhost:8255/api/stocks/AAPL` returns a populated `row.risk_budget` object with all 5 components and real, non-null values:
  - `atr_pct.value = 2.835492026826355` (→ "2.84%")
  - `downside_vol.value = 1.1520879762825937` (→ "1.15%")
  - `worst_20d_window.value = -67.03280719770166` (→ "-67.03%")
  - `distance_to_invalidation_pct.value = 0.5829698456096744` (→ "0.58%")
  - `gap_profile.{median,p95,worst,overnight_variance_share}` all populated with percentiles
  - These byte-match the UI test plan's documented "last verified" baseline values exactly (UT-02), confirming the backend/data half of this iteration's precondition holds in this environment.
- **Chrome MCP availability:** **FAIL — tool unavailable.** See diagnostic detail below. Per browser-qa-agent.md: "If Chrome MCP is not available: write all tests as SKIPPED with reason 'Chrome MCP not available'" and "SKIPPED: Frontend not running or Chrome MCP unavailable. ALL tests skipped." Because no test step in this plan can be satisfied by an API-only check (they require DOM rendering, scroll behavior, sort interaction, tooltip/popup behavior, console-error absence, and visual layout — none of which `curl` can verify), all 16 UT-XX cases are recorded as SKIPPED rather than PASS/FAIL. No result in this report should be read as a claim about actual UI behavior.

### Chrome MCP diagnostic detail

`mcp__plugin_superpowers-chrome_chrome__use_browser` was invoked 6 times across this run, every one failing with:

```
Error: Failed to auto-start Chrome: Chrome did not become ready on port 9222 within 15000ms
```

Steps taken to isolate the cause (all via read-only inspection, the tool's own recovery actions, and cleanup of processes this session itself spawned — no source files touched, no other session's processes touched):

1. `action: "navigate"` → timeout error.
2. `action: "restart_chrome"` → same timeout error.
3. Process inspection (`ps aux | grep chrome`) confirmed a Chrome process WAS launched matching the expected flags (`--remote-debugging-port=9222 --user-data-dir=.../browser-profiles/superpowers-chrome`), and it held the profile's `SingletonLock`, i.e. it was genuinely the process spawned by the tool call — not a stale/foreign process.
4. `ss -ltn` showed **no listener on port 9222** at any point, including after the process had been alive for 74+ seconds (well past the tool's internal 15s window).
5. `action: "kill_chrome"` → same timeout error (the tool itself could not cleanly recover on its own).
6. Cross-checked two other, pre-existing Chrome instances unrelated to this session (profiles `yahoo-iter8-qa-retry2` on port 9223, running 20+ min; `superpowers-chrome-3` on port 9224, running 8+ hours) — **neither had its debug port listening either**, despite both processes being alive and using real CPU. This pointed toward a systemic issue rather than a one-off race.
7. Ruled out resource starvation: `uptime` showed load average 1.68 (multi-core box), `free -h` showed 16Gi available memory — not under pressure.
8. Ruled out profile corruption: `action: "set_profile"` → a brand-new, never-before-used profile name (`goal-mcp-loop-iter-40-qa`), then `action: "navigate"` with an explicit extended `timeout: 30000` → identical failure. `ps` confirmed a fresh Chrome process launched under the new profile dir; `ss -ltn` again showed no port 9222 listener.
9. Manually terminated (`kill -TERM`) the two partially-started Chrome processes this session had accumulated, confirmed a fully clean process table (`ps aux | grep chrome` showed no stray `--remote-debugging-port=9222` process), waited, then retried `action: "navigate"` once more from a clean state → **identical timeout failure**, with the newly spawned process again never binding port 9222. Terminated this final stray process too, leaving no orphaned processes behind.

All 6 tool-level attempts plus OS-level process/port/profile isolation, including a full clean-slate retry, converge on the same conclusion: Chrome's DevTools TCP listener does not come up for this session, independent of profile identity, retry count, or process-table cleanliness.

**Important nuance:** the evidence directory already contained one screenshot (`TC-01-risk-budget-card-liquid.png`) timestamped ~19:27, roughly 17 minutes before this session's first attempt (~19:44) — meaning an earlier agent in this same pipeline run (the functional `qa` agent, TC-XX track) DID successfully drive Chrome MCP earlier in this same iteration. This suggests the failure is more likely a session-specific or time-window-specific regression (e.g. something in the shared Chrome/MCP host state changed between ~19:27 and ~19:44) than a permanently-broken environment — worth flagging to the coordinator/pump for investigation — but it does not change the outcome for this run: this session's 6 independent attempts, spanning a full cleanup-and-retry cycle, all failed identically. This is an infrastructure condition outside this agent's mandate to fix (browser-qa-agent must not edit source files or remediate environment/tooling issues) and is reported here as-is.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Stock Detail loads with Risk budget card present | smoke | P1 | "Risk budget" card visible below Themes/Invalidation card on `/stocks/AAPL`, no error banner | Not executed — Chrome MCP unavailable | SKIP | none |
| UT-02 | Risk budget card: all 6 metrics + percentile chips | happy-path | P1 | All 6 tiles show real % values + "pXX of universe" chips | Not executed — Chrome MCP unavailable (backend precondition independently confirmed via curl, see above) | SKIP | none |
| UT-03 | Leaderboard: 5 new risk-budget columns with real values | happy-path | P1 | 5 new columns between "Proximity to 52w high" and "Setup", AAPL row shows real values | Not executed — Chrome MCP unavailable | SKIP | none |
| UT-04 | Leaderboard value == detail card value (single source) | happy-path | P1 | ATR% / Worst 20d identical between leaderboard cell and detail tile | Not executed — Chrome MCP unavailable | SKIP | none |
| UT-05 | Risk-budget columns sortable, NA sorts last | ux | P2 | Sort ascending/descending re-orders rows; NA rows always at bottom | Not executed — Chrome MCP unavailable | SKIP | none |
| UT-06 | Column header info icon shows glossary definition | ux | P2 | Info icon popup shows "overnight-gap profile" definition + WHERE + threshold | Not executed — Chrome MCP unavailable | SKIP | none |
| UT-07 | Methodology glossary: 3 new terms, searchable | happy-path | P1 | Searching each new term returns exactly one matching glossary card | Not executed — Chrome MCP unavailable | SKIP | none |
| UT-08 | Methodology glossary counts stay additive-only | ux | P3 | "... terms across 6 categories ..." (category count unchanged) | Not executed — Chrome MCP unavailable | SKIP | none |
| UT-09 | Short-history stock shows NA + reason | validation | P2 | Amber "NA — insufficient history" on a short-history tile, or documented not-reproducible | Not executed — Chrome MCP unavailable (also independently flagged by the test plan as likely not reproducible in this seed universe) | SKIP | none |
| UT-10 | Historical as-of date: no card, NA columns, no crash | error | P2 | Risk budget card absent at historical as-of date; leaderboard columns show NA; no crash | Not executed — Chrome MCP unavailable | SKIP | none |
| UT-11 | No proven/edge/position-advice language on the card | ux | P1 | No "proven/buy/sell/trim/reduce/rebalance/edge" text or badge inside the card | Not executed — Chrome MCP unavailable | SKIP | none |
| UT-12 | Regression: scores + evidence badges unchanged (J-01/02/03) | regression | P1 | Leadership/Entry Quality/Risk scores + "Not yet proven" badges identical leaderboard vs detail | Not executed — Chrome MCP unavailable | SKIP | none |
| UT-13 | Regression: deep price chart still renders (J-10) | regression | P2 | Price chart renders below new card; "Full history" and regime toggle work | Not executed — Chrome MCP unavailable | SKIP | none |
| UT-14 | Regression: evidence status badges still work (J-05) | regression | P2 | "Not yet proven" badges + tooltip render; `/evidence` loads normally | Not executed — Chrome MCP unavailable | SKIP | none |
| UT-15 | Regression: preflight banner still shows GO (J-20) | regression | P1 | Green "GO — today's board is current." strip on both `/stocks` and `/stocks/AAPL` | Not executed — Chrome MCP unavailable | SKIP | none |
| UT-16 | Regression: Data Manager page unaffected (J-13) | regression | P3 | `/data` loads normally, heading "Data Manager", no risk-budget content | Not executed — Chrome MCP unavailable | SKIP | none |

---

## Passed Tests

None — no test could be executed against a real browser this run.

---

## Failed Tests

None — per browser-qa-agent.md rules, browser-automation unavailability is recorded as SKIPPED, not FAIL, since no test actually ran to observe a failure.

---

## Skipped Tests

All 16 test cases (UT-01 through UT-16) are SKIPPED for the same reason:

**Reason:** Chrome MCP unavailable — `mcp__plugin_superpowers-chrome_chrome__use_browser` could not start a working Chrome DevTools session in this environment. Six tool-level attempts (navigate ×4, restart_chrome, kill_chrome), across two profiles (the default `superpowers-chrome` profile and a freshly created `goal-mcp-loop-iter-40-qa` profile) and including a full process-table cleanup + clean-slate retry, all failed identically with `Chrome did not become ready on port 9222 within 15000ms`. OS-level inspection (`ps`, `ss -ltn`) confirmed the underlying Chrome process does launch each time but never binds its remote-debugging TCP port, a pattern also observed on two other, unrelated pre-existing Chrome instances in this environment (ports 9223, 9224). An earlier agent in this same pipeline run (the functional `qa` agent) did successfully drive Chrome MCP about 17 minutes before this session's first attempt, so this looks more like a session/time-window-specific regression than a permanently broken environment — but it held across every attempt made in this session. Full diagnostic trail is in "Chrome MCP diagnostic detail" above. This is an environment/infrastructure condition outside this agent's remit to fix.

Note: the backend precondition this iteration depends on (`row.risk_budget` populated with real values on `/api/stocks/AAPL`) was independently verified via direct API check and holds — see "Precondition check" above. Only the browser-rendering verification itself could not be performed.

### UT-01 — Stock Detail loads with Risk budget card present
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above)

### UT-02 — Risk budget card: all 6 metrics + percentile chips
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above)

### UT-03 — Leaderboard: 5 new risk-budget columns with real values
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above)

### UT-04 — Leaderboard value == detail card value (single source)
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above)

### UT-05 — Risk-budget columns sortable, NA sorts last
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above)

### UT-06 — Column header info icon shows glossary definition
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above)

### UT-07 — Methodology glossary: 3 new terms, searchable
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above)

### UT-08 — Methodology glossary counts stay additive-only
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above)

### UT-09 — Short-history stock shows NA + reason
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above). Note: the test plan already flags this case as likely "not reproducible with current seed data" even under a working browser (shortest-history ticker `Q` still has ~170 bars), so this would likely have been a documented non-failure outcome regardless.

### UT-10 — Historical as-of date: no card, NA columns, no crash
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above)

### UT-11 — No proven/edge/position-advice language on the card
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above)

### UT-12 — Regression: scores + evidence badges unchanged (J-01/02/03)
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above)

### UT-13 — Regression: deep price chart still renders (J-10)
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above)

### UT-14 — Regression: evidence status badges still work (J-05)
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above)

### UT-15 — Regression: preflight banner still shows GO (J-20)
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above)

### UT-16 — Regression: Data Manager page unaffected (J-13)
**Verdict:** SKIPPED
**Reason:** Chrome MCP unavailable (see diagnostic detail above)

---

## Environment

- **Frontend URL:** http://localhost:3255 (confirmed reachable, HTTP 200)
- **Backend URL:** http://localhost:8255 (confirmed reachable and ready; `row.risk_budget` confirmed populated on `/api/stocks/AAPL`)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`) — **unavailable this run**; DevTools port never bound despite multiple retries and a fresh-profile isolation test (see diagnostics above)
- **Test Date:** 2026-07-15
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-40-evidence/` — no UT-XX screenshots captured this run (no browser session was available). Note: the directory already contained one pre-existing file, `TC-01-risk-budget-card-liquid.png` (timestamped before this run started), which belongs to the earlier functional-QA agent's TC-XX pass, not to this browser-qa-agent's UT-XX pass — it is unrelated to the SKIPPED verdict above and was not produced or inspected by this run.

No golden replay script was written to `runs/goal-session-mcp-loop/journey-scripts/J-24.json` this run, since no journey was verified PASS (golden scripts are only written immediately after a journey passes, per browser-qa-agent.md).
