# Phase goal-mcp-loop-iter-33 — UI Test Results

**Phase:** goal-mcp-loop-iter-33 (J-20 — Daily Preflight Verdict, backlog B-301)
**Date:** 2026-07-14
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 20/20 tests passed (0 skipped)

All 12 P1 tests pass. All 5 P2 tests pass. All 3 P3 tests pass. The single new capability (a
layout-level `PreflightBanner` reading the additive `preflight` field on `GET /api/health`) is
byte-verbatim identical across every required decision surface in all three verdict states (GO,
DEGRADED, NO-GO), the NO-GO banner contains the exact mandated phrase, reasons are specific and
config-driven, the verdict is single-source and updates live, and no existing surface (readiness
badge, leaderboard evidence badges, evidence ledger, nav) regressed.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Dashboard loads with GO banner | smoke | P1 | "Dashboard" heading + thin green "GO — today's board is current." strip below header, no reasons, no crash | Exact match. `data-testid="preflight-banner"` `data-verdict="GO"` confirmed via DOM. | PASS | `reports/qa/goal-mcp-loop-iter-33-evidence/UT-01-dashboard-go.png` |
| UT-02 | `/stocks` loads with GO banner | smoke | P1 | "Stocks" heading, identical GO strip above leaderboard, table loads beneath | Exact match. Leaderboard rows (INTC, GL, TENB, MRVL, …) with scores render fully beneath strip. | PASS | `reports/qa/goal-mcp-loop-iter-33-evidence/UT-02-stocks-go.png` |
| UT-03 | Stock detail loads with GO banner | smoke | P1 | "NVDA" heading, identical GO strip, scores/evidence badges/chart render without overlap | Exact match. Leadership 34.24 / Entry Quality 52.54 / Risk 34.64, "Not yet proven" badges, price chart all render cleanly below strip. | PASS | `reports/qa/goal-mcp-loop-iter-33-evidence/UT-03-stock-detail-go.png` |
| UT-04 | `/watchlist` loads with GO banner | smoke | P1 | "Watchlist" heading, identical GO strip, table/empty-state fully visible | Exact match. Watchlist table (MSFT, ABBV rows) fully visible beneath strip. | PASS | `reports/qa/goal-mcp-loop-iter-33-evidence/UT-04-watchlist-go.png` |
| UT-05 | `/evidence` loads with GO banner | smoke | P1 | "Evidence" heading, identical GO strip, ledger table fully visible | Exact match. Certified-claims ledger (FAIL rows: leadership_score, Breakout-watch setup, ma_stack, vcp_contraction, …) fully visible beneath strip. | PASS | `reports/qa/goal-mcp-loop-iter-33-evidence/UT-05-evidence-go.png` |
| UT-06 | GO banner identical on all 5 required surfaces | happy-path | P1 | Same exact text/color/position on all 5 pages | Confirmed via direct screenshot comparison (UT-01–05) plus `data-verdict` DOM attr checks on each page — all identical, byte-verbatim "GO — today's board is current." | PASS | UT-01 through UT-05 screenshots (above) |
| UT-07 | `/research` + sub-page inherit banner | happy-path | P2 | Identical GO strip on `/research` and `/research/factor-lab` | Confirmed on both — same position, text, color above the Research lab-card grid and above the Factor Lab table. | PASS | `reports/qa/goal-mcp-loop-iter-33-evidence/UT-07-research-go.png`, `UT-07-research-factor-lab-go.png` |
| UT-08 | Remaining nav pages show banner, no collision on `/data` | happy-path | P2 | GO strip on Sectors/Themes/Backtest/Methodology/Scanner Runs; no overlap with `/data`'s own content | `data-verdict="GO"` confirmed via DOM attr on all 5 pages (no crash/blank). On `/data`, GO strip renders cleanly above the page's own content area with no overlap — see note. | PASS | `reports/qa/goal-mcp-loop-iter-33-evidence/UT-08-data-go.png` |
| UT-09 | Existing readiness badge unchanged | regression | P1 | "Ready" pill + "provider: seed" + "seed 2026-07-01" + "590 symbols" badges unchanged by the new banner | Confirmed identical across GO and DEGRADED screenshots; correctly shows "Backend unavailable" (pre-existing `HealthBadge` behavior, not part of this phase) when backend was down. Text/color/position unaffected by the new banner in every case. | PASS | UT-01, UT-17, UT-12 screenshots |
| UT-10 | Evidence badges/leaderboard unaffected (J-01/J-02) | regression | P1 | Leaderboard "Not yet proven" badges and ledger "FAIL" rows fully visible, not hidden by the new strip | Confirmed in UT-02/UT-05 (GO) and again in UT-13/UT-14 (DEGRADED/NO-GO) screenshots — content never clipped or hidden. | PASS | UT-02, UT-05, UT-13, UT-14 screenshots |
| UT-11 | Content fully visible beneath banner on quiet and loud days | regression | P2 | No content cut off/hidden in either state; content simply starts lower under the taller loud banner | Confirmed by direct comparison: UT-01 (GO, dashboard) vs UT-17 (DEGRADED, dashboard) and UT-03 (GO, NVDA) vs UT-13 stock-detail (DEGRADED, NVDA) — all page content fully visible in both, shifted down under the loud banner as expected, never overlapped. | PASS | UT-01/UT-17, UT-03/UT-13-stock-detail screenshot pairs |
| UT-12 | Backend down → honest NO-GO fallback, no blank page | error | P1 | Red banner "NO-GO — do not rely on today's board." + reason "Backend is unavailable — the preflight check could not run."; no blank/crash; recovers to GO after restart | Confirmed twice: (1) organically, when the backend process was found already down at test start (see Environment Notes); (2) in a controlled stop/restart cycle. Both times: exact headline + exact reason, page never blank, sidebar/header chrome intact. Restarted backend — still-open tab auto-recovered to GO with zero refresh. | PASS | `UT-12-dashboard-backend-down.png`, `UT-12-dashboard-restored-go.png` |
| UT-13 | Induced DEGRADED shows amber banner + reason (DoD Step 2) | error | P1 | Amber banner "DEGRADED — treat today's board with caution." + reason naming exact stale-days/threshold, identical on all 5 surfaces | Confirmed on `/`, `/stocks`, `/stocks/NVDA`, `/watchlist`, `/evidence` — all show identical headline + reason "Latest data (2026-07-01) is 0 trading day(s) old, exceeding the configured maximum of -1 day(s)." Date matches "seed 2026-07-01" badge. Restored config afterward; all 5 surfaces confirmed back to GO. | PASS | `UT-17-dashboard-live-degraded.png`, `UT-13-stocks-degraded.png`, `UT-13-stock-detail-degraded.png`, `UT-13-watchlist-degraded.png`, `UT-13-evidence-degraded.png` |
| UT-14 | Induced NO-GO shows exact mandated phrase (DoD Step 2, critical) | error | P1 | Red banner containing exact phrase "do not rely on today's board" + integrity reason, identical on all 5 surfaces | Confirmed on all 5 required surfaces — headline "NO-GO — do not rely on today's board." (exact phrase present) + reason "Integrity check failed: evidence ledger missing (…/does-not-exist-ledger.jsonl)." (contains "Integrity check failed" and "missing"). Restored `TRENDORA_LEDGER_PATH` afterward; all 5 surfaces confirmed back to GO; real ledger file untouched throughout. | PASS | `UT-14-dashboard-nogo.png`, `UT-14-stocks-nogo.png`, `UT-14-stock-detail-nogo.png`, `UT-14-watchlist-nogo.png`, `UT-14-evidence-nogo.png` |
| UT-15 | First load never fabricates GO | validation | P1 | Neutral "Checking board status…" placeholder before first check resolves, never a premature GO | PASS via direct source verification (see note below) — the Chrome MCP tool exposes no network-throttle/CDP-conditions action, so the millisecond-scale transient window could not be captured as a live screenshot. `readiness-provider.tsx` shows `loading` initializes `true` and `preflight` initializes `null`, and `setLoading(false)` fires only inside the `finally` of the first `/api/health` fetch attempt — so `PreflightBanner`'s `if (loading)` branch (rendering exactly "Checking board status…", no color, no verdict) is structurally guaranteed on first paint. Corroborated live: across ~20 navigations this session (including the organic backend-down case) the verdict always matched actual backend state with zero observed stale/fabricated flashes. | PASS | Source: `apps/frontend/components/preflight-banner.tsx` L22-33, `apps/frontend/components/readiness-provider.tsx` L43-44,74-76 |
| UT-16 | DEGRADED/NO-GO reasons specific, not generic | validation | P2 | Reason names the specific problem, understandable by a non-technical reader | Confirmed: "Latest data (2026-07-01) is 0 trading day(s) old, exceeding the configured maximum of -1 day(s)." names exact date and exact threshold — not a generic "Something went wrong." | PASS | `UT-13-evidence-degraded.png` |
| UT-17 | Verdict updates live without refresh | happy-path | P2 | Banner auto-switches GO→DEGRADED within 30s with zero refresh | Confirmed: dashboard tab left open on GO; backend restarted with the DEGRADED override; `data-verdict` attr read "DEGRADED" ~17-20s later on the SAME unrefreshed tab. Bonus: the reverse (NO-GO→GO) was also observed live during the UT-12 restore step. | PASS | `UT-17-dashboard-live-degraded.png` |
| UT-18 | Banner self-explanatory, no click needed | ux | P3 | Meaning clear from text alone; no clickable affordance | Confirmed via DOM/CSS inspection: element is a `<div role="status">`, `cursor: auto` (not `pointer`), `onclick === null` — reads as status text, not an interactive control. | PASS | eval output (see transcript); `UT-01-dashboard-go.png` |
| UT-19 | Exactly one banner, single-source | ux | P3 | Exactly 1 `[data-testid="preflight-banner"]`; no duplicate `/api/health` request | Confirmed on `/` and `/stocks`: `document.querySelectorAll(...).length === 1` both times. `/api/health` request count observed over 10s windows: 1 on `/`, 0 on `/stocks` (idle-cadence timing) — never more than 1, confirming no second/duplicate fetch from the banner. | PASS | eval output (see transcript) |
| UT-20 | No new nav item added | ux | P3 | Sidebar shows the same 11 pre-existing items, no new entry | Confirmed via DOM query: exactly 11 `<nav>` links — Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Evidence, Watchlist, Methodology, Data Manager. No "Preflight"/"Status" entry added. | PASS | eval output (see transcript); all screenshots |

---

## Passed Tests

All 20 test cases passed. See the Results Table above for per-test evidence and detail — the notes
below cover only what needed more explanation than fits in the table.

### UT-15 — First load never fabricates GO
**Verdict:** PASS (source-verified, not screenshot-verified)
**Evidence:** `apps/frontend/components/readiness-provider.tsx` L21-44, L50-86; `apps/frontend/components/preflight-banner.tsx` L19-34

This Chrome MCP tool's action set (checked via its own `help` action) has no network-throttle or
CDP-network-conditions action, and a plain hard-refresh on localhost resolves the health fetch
faster than any of my tool round-trips could reliably screenshot mid-flight — so I could not force
and visually catch the transient "Checking board status…" window the way a human with real
DevTools throttling could. Rather than guess or claim a screenshot I don't have, I read the exact
shipped source currently running in the prod build:

- `ReadinessProvider` initializes `const [loading, setLoading] = useState(true)` and
  `const [preflight, setPreflight] = useState<PreflightStatus | null>(null)` (readiness-provider.tsx
  L43-44).
- `setLoading(false)` is called only inside the `finally` block of the first `tick()` invocation
  (L74-76), i.e. only after the first `/api/health` fetch attempt resolves one way or another.
- `PreflightBanner` checks `if (loading)` FIRST (preflight-banner.tsx L22), before any verdict
  branch, rendering only the neutral "Checking board status…" text with no color/verdict.

Given React's render model, the component's first-ever paint after mount is therefore structurally
guaranteed to hit the loading branch — it is not merely "usually" the case, it cannot do otherwise.
This is reported as PASS with the evidence basis stated plainly so the reader can weigh it
appropriately; it is not a live-screenshot PASS like the other 19 tests.

### UT-08 — `/data` skeleton-loading observation (non-blocking)
`/data`'s own coverage/gap panels were still showing skeleton placeholders (dark loading bars)
several seconds after navigation, while the backend log confirmed `GET /api/data/availability` had
already returned `200 OK`. This appears to be pre-existing `/data`-page behavior unrelated to the
preflight banner (the banner rendered instantly and correctly; only `/data`'s own async panels were
slow to resolve client-side) — not a regression this phase introduced, and not something UT-08 asks
me to test. Noted for transparency; does not affect the UT-08 verdict, which only concerns
banner/content collision (confirmed absent).

---

## Failed Tests

None. 20/20 tests passed.

---

## Skipped Tests

None.

---

## Environment Notes

- **Organic backend outage at test start.** Before I touched anything, `/stocks/NVDA` was found
  already showing the app's honest NO-GO/"Backend unavailable" fallback — the backend process
  (PID 3498957) had exited cleanly (`Shutting down` / `Application shutdown complete` in its log,
  no traceback) between the QA dispatch wrapper's boot and my first few navigations, for reasons
  outside this test session (this is a shared multi-project dev box; `browser-qa-phase.sh`'s
  pre-retry service-revival hook only fires between separate `claude -p` invocations, not
  continuously, so it did not auto-heal this mid-session). I restarted it myself via
  `scripts/start-backend.sh` (matching the running process's own invocation) and confirmed it came
  back healthy before continuing. This organic occurrence became the first piece of evidence for
  UT-12, which I then reproduced a second time in a fully controlled stop/restart cycle for clean,
  intentional before/after evidence.
- **Config overrides used for UT-13/UT-14 (per the dev handoff's documented, sanctioned levers).**
  DEGRADED: backend restarted with `TRENDORA_CONFIG` pointed at a copy of `config.yaml` with
  `readiness.freshness_max_age_days: -1` (copy at
  `/tmp/iad.goal-mcp-loop-iter-33.2778307/qa-config-overrides/config-degraded.yaml`; the committed
  `config.yaml` was never modified). NO-GO: backend restarted with `TRENDORA_LEDGER_PATH` pointed at
  a nonexistent path; no real ledger/registry file was deleted or modified — confirmed by `/evidence`
  showing its normal FAIL-ledger content again immediately once the override was removed. Both
  overrides were reverted and the backend restarted clean before finishing; final `/api/health`
  confirms `preflight.verdict: "GO"` with all three components `ok: true`.
- **Minor cosmetic observation (out of scope, not reproduced).** One screenshot
  (`UT-14-dashboard-nogo.png`, first capture) showed a small clipped tooltip-like text fragment
  at the very top edge of the viewport, above the readiness badges. It did not recur on any other
  capture (including the immediately following `/stocks` NO-GO screenshot), does not overlap the
  preflight banner, and is not something any UT-XX test case asserts on — most likely a stale
  `:hover` artifact from mouse-position carryover between rapid consecutive navigations in the
  automation harness rather than a product defect. Noted for transparency only.
- Backend log (`fanout-backend-8255*.log`) was checked for errors/tracebacks across the entire
  session — none found, across every restart and override.
- **Golden replay script written.** `runs/goal-session-mcp-loop/journey-scripts/J-20.json` (5 steps,
  one `goto` + exact-text `expect` per required surface). Linted clean
  (`demo_runner.py --mode lint`) and live-verified against the running app
  (`demo_runner.py --mode verify --journeys J-20` → `1 journey(s), 0 failed (verdict: PASS)`).

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-14
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-33-evidence/`
