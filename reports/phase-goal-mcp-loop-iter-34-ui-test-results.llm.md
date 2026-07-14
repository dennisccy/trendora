# Phase goal-mcp-loop-iter-34 — UI Test Results (LLM lane)

**Phase:** goal-mcp-loop-iter-34
**Date:** 2026-07-14
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

**Scope note (lean mode):** Per dispatch, this LLM lane tests EXACTLY the one Target
journey, **J-20**. All 17 Required-still-passing journeys (J-01–J-14, J-17–J-19) are
verified separately by the deterministic golden-script replay lane
(`demo_runner.py --mode verify`) against `runs/goal-session-mcp-loop/journey-scripts/*.json`
— confirmed already executed on disk (`reports/qa/goal-mcp-loop-iter-34-evidence/J-01-verify.png`
… `J-19-verify.png`, timestamped 12:40–12:42 today, before this LLM lane ran). This file is
the LLM-lane input to the merge step that produces the final
`reports/phase-goal-mcp-loop-iter-34-ui-test-results.md`, per the iteration spec.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-20 | A single daily preflight verdict guards every decision surface | smoke | P1 | GO banner ("GO — today's board is current.") renders identically on dashboard/`/stocks`/stock-detail/`/watchlist`/`/evidence`, sourced from one `/api/health` payload; DEGRADED/NO-GO states (carried from byte-identical iter-33 code) render loud banners with concrete reasons, NO-GO containing "do not rely on today's board" | All 5 required surfaces confirmed live via Chrome MCP: identical `data-verdict="GO"` banner, text byte-matches `"GO — today's board is current."`, matches live `GET /api/health` (`preflight.verdict:"GO"`, `reasons:[]`) verbatim. Single-source confirmed live (exactly 1 `[data-testid="preflight-banner"]` element; DOM verdict === fresh API fetch verdict). DEGRADED/NO-GO not re-induced live this session (blocked by a tool-permission boundary — see Notes) but carried on `git diff HEAD` byte-identity for `readiness.py`, `config.yaml`, and all of `apps/frontend` against iter-33's commit (4561da1), which live-verified DEGRADED + NO-GO (incl. the exact mandated phrase) on all 5 surfaces just prior, same day. | PASS | `reports/qa/goal-mcp-loop-iter-34-evidence/J-20-00-stocks-go.png`, `J-20-01-dashboard-go.png`, `J-20-02-stock-detail-go.png`, `J-20-03-watchlist-go.png`, `J-20-04-evidence-go.png` |

---

## Passed Tests

### UT-J-20 — A single daily preflight verdict guards every decision surface
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-34-evidence/J-20-{00-stocks,01-dashboard,02-stock-detail,03-watchlist,04-evidence}-go.png`

**Step 1 (healthy state — live-verified this session):**
- Navigated to `/`, `/stocks`, `/stocks/NVDA`, `/watchlist`, `/evidence` in the current
  live browser (Chrome MCP, backend already running healthy at the time of dispatch —
  `GET /api/health` → `preflight.verdict:"GO"`, all three components
  (`servability`/`freshness`/`integrity`) `ok:true`).
- On every one of the 5 pages, `document.querySelector('[data-testid="preflight-banner"]')`
  returned `data-verdict="GO"` and `textContent === "GO — today's board is current."` —
  byte-identical across all 5 surfaces, no reasons bulleted (GO's `reasons: []`).
- Page content beneath the banner rendered normally on every surface with no overlap
  (leaderboard rows on `/stocks`, scores/chart on `/stocks/NVDA`, watchlist rows on
  `/watchlist`, the certified-claims ledger on `/evidence`).

**Step 3 (single source — live-verified this session):**
- On `/`, ran a combined DOM+fetch check: exactly **1** element matched
  `[data-testid="preflight-banner"]` (`bannerCount: 1`); its `data-verdict` attribute
  (`"GO"`) matched a **fresh, same-request** `fetch('http://localhost:8255/api/health')`
  call's `preflight.verdict` (`"GO"`) — `singleSourceMatch: true`. The pre-existing,
  unrelated `[data-testid="readiness-badge"]` pill still reads `"Ready"`, confirming no
  regression to that separate element (J-01/J-02 surfaces unaffected).
- This directly confirms goal.md's J-20 Step 3 ("the verdict and reasons come from one
  endpoint; no page computes its own") on the live running app.

**Step 2 (induced DEGRADED/NO-GO — carried from iter-33, not re-driven live this session):**
See "Notes — DEGRADED/NO-GO evidence basis" below for the full rationale. Summary: the
Chrome MCP session cannot re-induce these states this run because doing so requires
restarting the shared backend process (PID 3674946), which was denied by the tool
permission system as "a running shared service it did not create this session." The
underlying code is confirmed **byte-identical** to iter-33's own commit (`git diff HEAD`
empty on `apps/backend/app/engine/readiness.py`, `config.yaml`, and all of
`apps/frontend`), and iter-33's browser-qa-agent already live-verified, same day
(screenshots timestamped 10:50–10:53 today), on all 5 required surfaces:
- DEGRADED: amber banner **"DEGRADED — treat today's board with caution."** + reason
  naming the exact stale-days/threshold — `reports/qa/goal-mcp-loop-iter-33-evidence/UT-13-{stocks,stock-detail,watchlist,evidence}-degraded.png` (+ `UT-17-dashboard-live-degraded.png` for the dashboard).
- NO-GO: red banner containing the exact mandated phrase **"do not rely on today's
  board"** + an integrity reason — `reports/qa/goal-mcp-loop-iter-33-evidence/UT-14-{dashboard,stocks,stock-detail,watchlist,evidence}-nogo.png`.
- Both states were induced via the documented sanctioned levers (`TRENDORA_CONFIG` →
  `readiness.freshness_max_age_days: -1` for DEGRADED; `TRENDORA_LEDGER_PATH` → a
  nonexistent path for NO-GO), with the real `config.yaml` and ledger files never
  touched, and the backend restored to clean GO before that session finished.

**This iteration's own Definition of Done line for J-20** ("Target journey J-20
re-confirmed `passing` via browser-qa on the final tree: the GO preflight banner renders
and content is not obscured; no regression of the cross-cutting chrome") is satisfied in
full by the live evidence above.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Notes — DEGRADED/NO-GO evidence basis (permission boundary, not a product defect)

This session's Chrome MCP browser was pointed at the already-running, shared dev stack
(backend PID 3674946 on :8255, frontend on :3255) that was up and healthy (HTTP 200,
`preflight.verdict:"GO"`) at dispatch time. Reproducing goal.md J-20 Step 2 live requires
restarting the backend with an env override (`TRENDORA_CONFIG` or `TRENDORA_LEDGER_PATH`)
— the same "sanctioned lever" iter-33 used. Attempting that restart
(`kill -TERM 3674946`) this session was **denied by the Claude Code auto-mode permission
classifier**: *"kills backend process PID 3674946, a running shared service it did not
create this session... not authorized by the browser-QA task."* No workaround (alternate
kill path, a second backend/frontend instance, etc.) was attempted, per instructions to
respect tool-permission boundaries rather than route around them.

Given that boundary, this report relies on byte-identity + carried same-day evidence
rather than a fresh live screenshot for the DEGRADED/NO-GO portion specifically — a
narrower, explicitly-labeled version of the same "carry forward when `git diff HEAD` is
empty" methodology this whole lean iteration is built on for the other 17 journeys. The
facts supporting this:
- `git diff --stat HEAD -- apps/backend/app/engine/readiness.py config.yaml apps/frontend`
  is empty (confirmed this session).
- `git log -1` on `preflight-banner.tsx` / `readiness-provider.tsx` / `readiness.py` all
  point to commit `4561da1` ("iter 33 — CONTINUE"), i.e. the exact code iter-33's
  browser-qa-agent screenshotted for DEGRADED/NO-GO.
- Those screenshots exist on disk, dated **today** (10:50–10:53), roughly two hours
  before this session — not stale, historical evidence.
- This iteration's own Definition of Done line for J-20 is itself scoped to the GO-state
  + no-regression re-confirmation (quoted above), which is fully live-verified.

Flagging this plainly for the goal-evaluator to weigh, per instructions not to invent
results: **the GO-state and single-source portions of J-20 are fresh, live,
Chrome-MCP-verified this session; the DEGRADED/NO-GO portion is carried, not
re-driven, this session,** for the tool-permission reason above.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-14
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-34-evidence/`
- **Golden replay script:** `runs/goal-session-mcp-loop/journey-scripts/J-20.json` —
  rewritten this session (content unchanged from what already existed — still lints
  clean: `demo_runner.py --mode lint` → `J-20 ok`) covering the deterministic,
  replayable GO-state contract across all 5 required surfaces. DEGRADED/NO-GO are not
  representable in the replay script format (no `goto`/`click`/`fill` action can restart
  a backend process), consistent with how the script was originally scoped in iter-33.
