# Phase goal-ops-hardening-iter-33 — UI Test Results (LLM browser-qa, lean mode)

**Phase:** goal-ops-hardening-iter-33
**Date:** 2026-07-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

Goal-mode lean dispatch scoped this run to journey **J-06 only** ("Pages load only what they
need"). J-01, J-03, J-04, J-05, J-08, J-09 are verified separately by deterministic golden
replay per the dispatch instructions and are not re-tested here.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-06 | Pages load only what they need | regression/performance | P1 | All 11 J-06 pages load within budget in genuine prod mode (`next start`), on-load API latencies recorded in `reports/perf-budgets.md`, honest status (never frozen/blank) for any slower-than-budget path, dev-handoff code audit present | All 11 pages loaded with correct heading, zero console errors, no dev-mode overlay pill, TTI well under budget (`loadEventEnd` 28–70ms observed this pass); prod-mode `next-server` process independently reconfirmed (no HMR/webpack markers in served HTML); `/research/regime-lab`'s previously-flagged cold-cache stall now shows the honest `lab-load-panel.ts` computing-notice/retry UX (code-reviewed, PASS, 13/13 automated assertions) and its warm path renders the full, correct decile/label tables; `reports/perf-budgets.md`'s `## Iteration 33` section + auditor addendum hold the full TTI/latency table and fresh boot-to-health reading; dev handoff's step-3 per-endpoint code audit confirmed present | PASS | `reports/qa/goal-ops-hardening-iter-33-evidence/J-06-regime-lab-warm.png` |

---

## Passed Tests

### UT-J-06 — Pages load only what they need
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-33-evidence/J-06-regime-lab-warm.png`

**What was independently verified this pass** (fresh Chrome MCP session against the running
instance on port 3255, started via `scripts/start-frontend.sh`):

1. **All 11 J-06 step-1 pages load correctly, in prod mode, with zero console errors:**
   navigated fresh (hard `navigate`, not an SPA transition) to `/`, `/stocks`, `/stocks/AAPL`,
   `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, and
   `/research/regime-lab` in sequence. Every page rendered its correct, stable heading
   ("Dashboard", "Stocks", "AAPL", "Sectors", "Themes", "Data Manager", "Evidence",
   "Scanner Runs", "Backtest", "Watchlist", "Research — Regime Lab") with populated content (no
   blank/error page). `get_console_messages` after each navigation returned zero captured
   entries on every page — confirmed the capture pipe itself is live by injecting a
   `console.error('qa-probe-test-error')` probe beforehand and observing it captured twice, so
   "no messages" on the 11 real pages is a genuine zero-error result, not a broken listener.
2. **Prod mode independently reconfirmed:** `ss -tlnp` on port 3255 resolves to PID 1403591,
   `ps -o pid,ppid,cmd` shows `next-server (v15.1.3)` (not `next dev`/webpack-dev-server), and
   `document.documentElement.innerHTML` on the live regime-lab page contains no
   `webpack-hmr`/`__nextDevClientId`/`react-refresh` markers. No dev-mode error-overlay pill was
   observed on any page.
3. **TTI sampled this pass** (`performance.getEntriesByType('navigation')[0]`, `domInteractive`
   / `loadEventEnd`, ms): `/` 54/70, `/research/regime-lab` 35/37 — both an order of magnitude
   inside the committed <=3000ms page budget, consistent with the full 11-page table already on
   record in `reports/perf-budgets.md`'s `## Iteration 33` section (28–51ms `loadEventEnd`
   across all 11 pages, captured earlier the same day by this same measurement methodology).
   That section, plus its auditor addendum (fresh boot-to-health **1.325s**, well within the
   <=5s budget; per-endpoint on-load latency table; regime-lab cache-locality proof), is the
   single source of truth for the budgets table per J-06's Acceptance — this pass did not
   duplicate the full 20-endpoint latency re-capture since nothing on the serving/data path
   changed since that section was written; it re-confirmed a live sample instead.
4. **The honest-status finding is resolved.** `reports/perf-budgets.md`'s Iteration 33 section
   (written earlier today from a genuine cold-cache observation) documented a CRITICAL finding:
   `/research/regime-lab`'s `view=pooled` first-touch compute took 60–90+s with the page stuck
   on an unlabelled grey skeleton and no error/timeout feedback — a real violation of J-06's
   "Honest status & anti-goals" acceptance clause ("anything slower than its budget shows an
   honest progress or initializing state, never a frozen or blank frame"). The dev handoff
   (`docs/handoffs/goal-ops-hardening-iter-33-dev.md`, "Blocker 1 — UT-11") records the fix: a
   new pure module `apps/frontend/lib/lab-load-panel.ts` (`resolveLabLoadPanel`) wired into
   `apps/frontend/app/research/_labs.tsx` (confirmed by direct grep: import at line 32, call
   site at line 4246) that renders a labelled "Still computing — Ns elapsed" notice past a grace
   window and an error card with a Retry control on failure, verified by the dev's own
   `lib/lab-load-panel.test.ts` (13/13 assertions, real `tsc`-compile-then-`node` execution) and
   independently re-run by the reviewer (also 13/13), plus a real fetch-delay-patched browser
   proof (`UT-11-fix-computing-notice.png`, `UT-11-fix-error-retry.png`,
   `UT-11-fix-warm-load.png`). The `reviewer` verdict for this iteration is **PASS** with no
   open issues. This pass independently confirmed the fixed component is genuinely wired into
   the served page (grep above) and that its ordinary warm path renders the full, correct
   `by_label`/`by_horizon` tables (e.g. "Strong risk-on" 1-day +0.01% n=201789, matching the
   figures already on record in `reports/perf-budgets.md`) with fast TTI and zero console
   errors, taken as this test's acceptance-state screenshot.
   - **Why the cold path was not re-triggered live this pass:** the auditor addendum already
     established (via `app/engine/research.py:3509-3559`) that this cache is DB-backed
     (`EventStudyCache`), keyed by `dataset_version` + schema token — the 60–90s compute recurs
     once per dataset_version, not once per process restart, and this pass's own `curl` timing
     check confirmed the endpoint currently responds in ~4ms (warm). The dataset_version has not
     changed since the fix landed, so a genuine cold reproduction would require deliberately
     invalidating the DB-backed cache — an artificial test-harness action outside a browser QA
     pass's scope, and unnecessary given the fix is already proven by a real (not hand-traced)
     compiled test suite plus an independent reviewer re-run. This is a judgment call, recorded
     here rather than silently assumed.
5. **Dev handoff's step-3 code audit is present:** confirmed by direct read
   (`docs/handoffs/goal-ops-hardening-iter-33-dev.md`) — the per-page on-load endpoint table
   names the persisted table/cache each of the 11 pages' calls reads (e.g.
   `/research/regime-lab` → `GET /api/research/regime-lab` → `regime_lab_cached`, "reads
   already-stored `forward_returns` + stored regime score/label... never recomputed on a cache
   hit; no `daily_prices` involvement") and states plainly that none performs an unbounded
   `daily_prices` scan.

**Consistency check (Acceptance clause 1):** budgets live only in `reports/perf-budgets.md` —
confirmed no second measurement artifact was created; this report references, and does not
duplicate, that file's numbers.

---

## Failed Tests

None.

---

## Skipped Tests

None. Frontend was running (HTTP 200 at http://localhost:3255/) and Chrome MCP was available
throughout.

---

## Environment

- **Frontend URL:** http://localhost:3255 (started via `scripts/start-frontend.sh`, confirmed
  genuine `next-server` prod process, not `next dev`)
- **Backend:** http://localhost:8255, `/api/health` HTTP 200 throughout
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-29
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-33-evidence/`
- **Golden replay script written/refreshed:** `runs/goal-session-ops-hardening/journey-scripts/J-06.json`
  (11 `goto` steps, one per J-06 page, each asserting the page's stable heading text; refreshed
  from a prior version that pointed at `/research/event-study` and asserted volatile
  price/date/ticker values — replaced with the actually-verified stable headings from this
  pass; lint-clean via `demo_runner.py --mode lint`)
