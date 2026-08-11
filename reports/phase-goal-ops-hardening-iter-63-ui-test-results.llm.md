# Phase goal-ops-hardening-iter-63 — UI Test Results

**Phase:** goal-ops-hardening-iter-63
**Date:** 2026-08-11
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests executed by this agent passed (0 failed, 0 skipped by this agent).

Note on scope: per the dispatch instructions, the Required-still-passing journeys (J-01, J-03, J-04,
J-05, J-06, J-08, J-09) were ALREADY re-verified this iteration by deterministic replay against their
stored golden scripts (`runs/goal-session-ops-hardening/journey-scripts/J-*.json`); this agent was
directed NOT to re-test them and NOT to emit rows for them — their rows merge into the final results
automatically from the replay lane. This agent executed only UT-J-07, the iteration's Target journey,
which the test plan itself states cannot be proven quantitatively through a browser-only check (that
proof is the dev/QA live 1 Hz `GET /api/health` poll drill in `reports/perf-budgets.md`); this test is
the fast, deterministic regression check that the browser-visible surfaces stay wired to real,
non-frozen data.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | Heavy aggregates never take the service down (target) | regression | P1 | Readiness badge present with `data-state="ready"`; background-compute-panel renders a real non-fabricated state; last-run-status renders a genuine persisted status; aggregates-refreshed lists the finalize tail's refreshed categories; no freeze/spinner/5xx/blank error | All four elements rendered live, real values: readiness-badge `data-state="ready"` (text "Ready"); background-compute-panel showed a REAL in-flight warm (as-of 2026-07-31, elapsed 52.2s, horizons 0/5, dataset r2960-f6568295) that this pass happened to catch already running, not one triggered by the check; last-run-status="ok"; aggregates-refreshed="Refreshed: latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, availability heatmap, factor lab all, drawdown expectations". No freeze, spinner-forever, or error observed. | PASS | `reports/qa/goal-ops-hardening-iter-63-evidence/UT-J-07-result.png` |

---

## Passed Tests

### UT-J-07 — Heavy aggregates never take the service down (target journey)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-63-evidence/UT-J-07-result.png`

- Navigated to `http://localhost:3255/data`.
- Read the readiness badge element (`[data-testid="readiness-badge"]`) directly via its own
  `data-state` attribute (not a heading/title match, per the golden's own iter-52 lesson): present,
  `data-state="ready"`, visible text "Ready".
- Read the background-compute panel (`[data-testid="background-compute-panel"]`): present, and — rather
  than the idle "No background compute running" state seen in most prior passes — this pass caught a
  REAL in-flight background compute window, honestly disclosing observed elapsed time and
  horizons-done/total with no fabricated finish-time estimate: "as-of 2026-07-31 · elapsed 52.2s ·
  horizons 0/5 · dataset r2960-f6568295".
- Read the `last-run-status` element (`[data-testid="last-run-status"]`): present, text "ok" — a genuine
  persisted status, not blank/undefined/fabricated.
- Read the `aggregates-refreshed` element (`[data-testid="aggregates-refreshed"]`): present, listing 9
  refreshed categories ("latest snapshot, coverage, membership timeline, market phase, forward
  aggregates, research hot keys, availability heatmap, factor lab all, drawdown expectations") — a
  superset of the 4 categories seen in some prior passes, consistent with catching a more complete
  finalize-tail run, not a regression.
- No page freeze, forever-spinner, or 5xx/blank error appeared at any point.
- Golden replay script `runs/goal-session-ops-hardening/journey-scripts/J-07.json` updated (steps
  unchanged — same five assertions this pass verified; an iter-63 `_notes` entry appended per the
  file's own rotation-history convention) and re-linted clean:
  `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-ops-hardening/journey-scripts --journeys J-07` → `J-07 ok`.
- Scope note carried from the test plan: this iteration's fix targets the finalize tail's
  `coverage_membership_timeline_refresh` GIL-hold latency; the quantitative proof (1 Hz `GET
  /api/health` poll for the full duration of a real finalize tail, reconciled against the raw poll log)
  is a dev/QA live drill recorded in `reports/perf-budgets.md`, not reproducible through this
  browser-only check — this test is the fast, deterministic regression proof that the browser-visible
  surfaces stay wired to real, non-frozen data, as designed.

---

## Failed Tests

None.

---

## Skipped Tests

None by this agent. (J-01, J-03, J-04, J-05, J-06, J-08, J-09 were not executed by this agent per the
dispatch instructions — they were already re-verified this iteration via deterministic replay against
their stored golden scripts; their rows merge into the final results automatically and are not
duplicated here.)

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (`/api/health` returned HTTP 200 at test start)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned profile/CDP
  port, headless
- **Test Date:** 2026-08-11
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-63-evidence/`
