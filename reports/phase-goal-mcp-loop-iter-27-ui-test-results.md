# Phase goal-mcp-loop-iter-27 — UI Test Results

**Phase:** goal-mcp-loop-iter-27
**Date:** 2026-07-11 / 2026-07-12 (session crossed midnight UTC)
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke/happy-path P1 tests pass; UT-02 (the centerpiece) passed decisively — three
     consecutive full-universe rebuilds (exceeding the required two) all reached status:"ok" with no
     backend downtime, no MemoryError, no wedge. This supersedes an earlier FAIL verdict recorded in
     this same report file from a prior QA pass (pre-fix): that pass observed a live backend crash on
     this exact job path; this pass, run against the fix (MALLOC_ARENA_MAX=2 + gc.collect()/malloc_trim
     after each backfill), observed the opposite — full survival across 3 consecutive runs. UT-01/
     UT-13/UT-14 are SKIPPED, not FAILED — the backend process is coordinator-managed this run and the
     auto-mode permission classifier denied my attempt to stop/restart it (verified no side effect
     occurred). This is an execution-environment constraint, not a product defect: every test that did
     not require stopping the backend was fully driven live, including UT-02. -->

**Overall:** 11/12 executed tests passed (3 skipped: UT-01, UT-13, UT-14)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Cold-start-first `/data` survives ×2 | smoke | P1 | Backend stopped/restarted twice, `/data` survives as first request both times | Could not execute — no permission to stop the coordinator-managed backend process (kill denied by auto-mode classifier) | SKIP | none |
| UT-02 | Full-universe rebuild survives TWICE in a row (CENTERPIECE) | happy-path | P1 | Both runs reach `ok` 322/322, backend stays reachable throughout, `/api/health`+`/stocks` healthy after | Ran **three** consecutive full-universe rebuilds (exceeding the required two); all three reached `status:"ok"`, `322/322 dates`; backend health/stocks/data endpoints stayed 200 throughout and after | PASS | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-02-run1-initial.png`, `UT-02-run1-confirm-modal-2.png`, `UT-02-run1-started.png`, `UT-02-run1-ok.png`, `UT-02-run2-ok.png`, `UT-02-post-both-runs-stocks.png` |
| UT-03 | Job progress honest, monotonic, never "done early" | validation | P1 | Counter never backward, badge never "ok" before total reached | Confirmed across all 3 runs via direct job-status polling (10-20s cadence): counter climbed monotonically (e.g. run 2: 0→1→2→3→4→4→32→100→155→199→237→272→307→322), `status` stayed `"running"` the entire time counter < total, flipped to `"ok"` only at the same poll where `dates_done == dates_total` | PASS | Same as UT-02 (evidence gathered during the same live runs; see polling logs quoted in this report's Passed Tests section) |
| UT-04 | Rebuild confirm modal can be cancelled | validation | P2 | Modal closes, no job starts, button re-enabled | Clicked Rebuild → modal appeared → clicked Cancel → modal closed; Job progress panel read "No job has been started this session"; rebuild button `disabled=false` | PASS | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-04-cancel-result.png` |
| UT-05 | Rebuild/Start buttons disabled while a job runs | validation | P2 | Both controls disabled + helper text while running; re-enabled after | While running: rebuild button `disabled=true`, Start button read "Job running…" `disabled=true`, helper text "A job is already running — wait for it to finish before rebuilding." visible. After completion: rebuild button `disabled=false`, Start button read "Start" `disabled=false` | PASS | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-05-running-disabled.png`, `UT-05-reenabled.png` |
| UT-06 | Dashboard Market Regime card correct + evidence link | regression | P1 | Non-empty regime badge/score, populated component breakdown, evidence link works | Badge "Risk-on", score "72.25 / 100"; breakdown expanded to 5 populated components (Index MA stack, Breadth>50DMA, Breadth>200DMA, Net new highs, VIX gate) all with numeric detail+contribution; "See evidence proven in this regime →" navigated to `/evidence`; Market Phase & Severity card also rendered normally ("Expansion", "29.95/100") | PASS | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-06-dashboard.png`, `UT-06-regime-breakdown.png` |
| UT-07 | Leaderboard rows show evidence badges | regression | P1 | Every row has a badge, ≥3 populated rows | 541/541 rows rendered; 1,623 "Not yet proven" badge instances found in DOM (541 rows × 3 score columns) — every row, every score, has a badge | PASS | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-02-post-both-runs-stocks.png` |
| UT-08 | Unproven score clearly marked | regression | P1 | Muted styling, not a link, correct tooltip | DOM inspection of badges: `<div>` (not `<a>`, `isLink:false`, no `href`), class includes `text-text-faint bg-surface-2 border-border` (muted, not accent), `title="Not yet proven — no certified out-of-sample evidence backs this signal yet (see the Evidence ledger)."` — exact match | PASS | Same as UT-07 |
| UT-09 | Evidence ledger honest empty state | regression | P1 | Page shows honest ledger, no fabrication, no error card | Page rendered correctly (no "Backend unavailable", no blank page). Ledger has ~8 registered claims, all `FAIL`, each showing all 5 fields (Hypothesis tags, Out-of-sample verdict, Control comparison vs SPY, Registration date, Forward-walk score-to-date). See note below — the literal text "No certified claims yet" is NOT present, but this was confirmed (via source read of `apps/frontend/app/evidence/page.tsx`) to be the app's own correct, intentional behavior: that empty-state string is gated on `claims.length === 0`, not on "0 passing claims", and the ledger currently has 8 non-empty (all-FAIL) claims, so the card-list branch is the code's own intended render — not a regression | PASS (see note) | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-09-evidence-empty-state.png` |
| UT-10 | Full-history toggle shows deep history | regression | P1 | Chart spans real range, no jump, scores stay populated | API-confirmed `bars` span 1996-01-02 → 2026-07-01 (3,185 bars, older bars weekly-sampled — matches the app's disclosed data-seed boundary, not a fabrication); chart line continuous with no discontinuous jump; all 3 score cards populated: Leadership E 55.78/100, Entry Quality D 69.70/100, Risk E 33.12/100, each tagged "Not yet proven" | PASS | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-10-aapl-initial.png`, `UT-10-aapl-full-history.png`, `UT-10-aapl-top.png` |
| UT-11 | Membership timeline honest entries/exits | regression | P1 | Step-function chart, honest per-date attribution, no error | "Resolved universe size" step chart rendered (max 542, 2005-02-25→2026-07-01); paginated table (Page 1 of 33, 322 dates) shows real per-date entries, e.g. `2026-06-22 → 540 · exits: −1 ERIE`, `2026-06-17 → 541 · exits: −1 PSKY` — specific, honestly-attributed, not smoothed/fabricated; no error card | PASS | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-11-membership-timeline-fullpage.png` |
| UT-12 | Core pages meet perf budgets | regression | P2 | Pages/APIs within `reports/perf-budgets.md` budgets | Warm HTTP timings (this session, backend warm after 3 rebuilds): `/stocks` 0.01s, `/stocks/AAPL` 0.01s, `/data` 0.01s, `/evidence` 0.01s (all ≤3s budget); `/api/health` 0.09s, `/api/stocks` 0.09s, `/api/stocks/AAPL` 0.00s, `/api/data` 0.03s (all within 0.1s/1.5s/0.3s/1.5s budgets). Cross-checked against `reports/perf-budgets.md`'s own iter-27 entry, which additionally re-confirms the memory-hardening fix did not regress load times | PASS | curl timings quoted above; no separate screenshot needed |
| UT-13 | Backend-down: one contained card | error | P1 | Contained "Backend unavailable" card, nav intact | Could not execute — requires stopping the backend; same permission denial as UT-01 | SKIP | none |
| UT-14 | Backend recovery after restart | regression | P2 | Page recovers after backend restart | Could not execute — depends on UT-13's backend-down precondition | SKIP | none |
| UT-15 | Data Manager discoverable, labels unchanged | ux | P3 | 1-click nav, unchanged panel titles | Sidebar shows all 11 expected entries unchanged; clicking "Data Manager" navigated to `/data` in exactly one click; all 6 named panels present and correctly titled ("Dataset coverage", "Storage footprint", "Rebuild snapshots for current universe", "Dynamic-universe membership timeline", "Start a fetch / backfill job", "Job progress") | PASS | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-15-data-manager-nav.png` |

---

## Passed Tests

### UT-02 — CENTERPIECE: Full-universe rebuild survives TWICE in a row (and a bonus third time)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-27-evidence/UT-02-run1-initial.png`, `UT-02-run1-confirm-modal-2.png`, `UT-02-run1-started.png`, `UT-02-run1-ok.png`, `UT-02-run2-ok.png`, `UT-02-post-both-runs-stocks.png`

This is the decisive test for the whole iteration. Drove the exact scenario that previously crashed the
backend (audit finding B1 — a second consecutive full-universe rebuild in the same long-lived process, and
the same scenario a prior QA pass of this exact phase — recorded earlier in this report file's history —
observed crash live):

- **Run 1**: clicked "Rebuild snapshots for current universe" → confirmed the "Confirm snapshot rebuild"
  modal (verbatim text matched: "This clears the entire snapshot set and recomputes a snapshot + forward
  returns for EVERY covered trading day... (541 members)") → job started (`running`, `snapshots 0/322
  dates`) → polled `GET /api/data/jobs/{id}` every 10-20s: `done=2→3→4→97→193→265→322`, monotonic, never
  backward → reached `status:"ok"`, `dates_done=322/322`, message "rebuild: 322 snapshots over 322 dates,
  597044 forward returns", elapsed 2m22s. Backend `/api/health` returned 200 at every poll.
- **Run 2 (immediately after, same session, no restart)** — the scenario that previously crashed: clicked
  Rebuild again → confirmed → job started fresh (`cleared 322 snapshot(s); rebuilding all covered dates`)
  → polled every 10s through the full run, paying particular attention to the deep-history tail: `done=0→
  1→2→3→4→4→32→100→155→199→237→272→307→322`, `health=200` at every single poll including the final dates
  (2026-06-10, 2026-07-01 — the most recent/deepest-trailing-window dates, exactly where the crash this
  iteration exists to fix previously occurred) → reached `status:"ok"`, `322/322`, "597044 forward returns",
  elapsed 2m25s.
- Post-both-runs verification: `GET http://localhost:8255/api/health` → `{"status":"ok","db_ok":true,...}`;
  navigated to `/stocks` → leaderboard rendered with 541/541 populated rows (Market Regime "Risk-on 72.25"
  visible in the header), proving the whole backend PROCESS survived, not just that individual requests
  happened to succeed.
- **Bonus run 3** (triggered organically while setting up UT-05's "job running" precondition): also reached
  `status:"ok"`, `322/322`, elapsed 2m28s — a third consecutive success, further than the plan required.

No crash, no wedge, no `MemoryError`, no backend downtime at any point across all three runs. This directly
confirms `reports/perf-budgets.md`'s own iter-27 entry (VmPeak 5,147,876 KB both runs — no growth — vs. the
pre-fix run 2 pinning at the 6,291,456 KB ceiling and crashing).

### UT-03 — Job progress honest, monotonic, never "done early"
**Verdict:** PASS
**Evidence:** same live polling as UT-02 (see above)

Across all three runs, the `dates_done` counter never decreased and `status` never read `"ok"` while
`dates_done < dates_total` — it flipped to `"ok"` in the exact same poll where the counter first reached
322/322. The `current_activity` field ("scanning YYYY-MM-DD (N/322)") and `last_progress_at` timestamp
updated on every poll — no stale/frozen heartbeat observed.

### UT-04 — Rebuild confirm modal can be cancelled
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-27-evidence/UT-04-cancel-result.png`
- Clicked Rebuild → modal appeared → clicked Cancel → modal closed immediately; Job progress panel read "No
  job has been started this session" (fresh page load, session-scoped); rebuild button confirmed
  `disabled=false` via DOM inspection.

### UT-05 — Rebuild/Start buttons disabled while a job runs
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-27-evidence/UT-05-running-disabled.png`, `UT-05-reenabled.png`
- While running: rebuild button `disabled=true`; Start button text "Job running…", `disabled=true`; helper
  text "A job is already running — wait for it to finish before rebuilding." visible.
- After the job reached `ok`: rebuild button `disabled=false`; Start button reverted to "Start",
  `disabled=false`.

### UT-06 — Dashboard Market Regime card correct + evidence link
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-27-evidence/UT-06-dashboard.png`, `UT-06-regime-breakdown.png`
- Badge "Risk-on", score "72.25 / 100" (not blank/NaN). Expanded "Why this regime — component breakdown":
  Index MA stack 1.00/35.00, Breadth>50-DMA 0.55/13.73, Breadth>200-DMA 0.63/15.78, Net new highs
  0.52/7.75, VIX gate "VIX 16.59 < 20 (×1)" 0.00 — all populated, none blank/undefined.
- "See evidence proven in this regime →" clicked and confirmed `window.location.href ===
  "http://localhost:3255/evidence"`.
- Adjacent "Market Phase & Severity" card rendered normally: "Expansion", "29.95/100 severity", no error
  state.

### UT-07 — Leaderboard rows show evidence badges
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-27-evidence/UT-02-post-both-runs-stocks.png`
- `/stocks` rendered 541/541 populated rows. DOM query found 1,623 elements with exact text "Not yet
  proven" (541 rows × 3 scores/row) — every row's every score has a badge, none missing.

### UT-08 — Unproven score clearly marked, never shown as confident
**Verdict:** PASS
**Evidence:** same as UT-07
- Sampled badge DOM nodes: tag `DIV` (not `A`), `isLink:false`, no `href` — confirmed not clickable.
  `className` includes `text-text-faint`, `bg-surface-2`, `border-border` — muted styling, no accent color.
  `title` attribute reads exactly "Not yet proven — no certified out-of-sample evidence backs this signal
  yet (see the Evidence ledger)." Raw score numbers remain fully visible beside each badge.

### UT-09 — Evidence ledger honest state
**Verdict:** PASS (see note)
**Evidence:** `reports/qa/goal-mcp-loop-iter-27-evidence/UT-09-evidence-empty-state.png`

**Note on discrepancy from the literal test-plan text:** The test plan expected an empty-state card headed
"No certified claims yet." What actually renders is a list of ~8 individual claim cards (leadership_score,
Breakout-watch setup, ma_stack — top decile, vcp_contraction — top decile, etc.), each explicitly badged
`FAIL` with its hypothesis tags, out-of-sample verdict + explanation, control comparison vs SPY, registration
date, and forward-walk score-to-date ("Pending — monitored as new data matures"). Neither "No certified
claims yet" nor "every signal currently reads Not yet proven" appears anywhere in `document.body.innerText`.
I read `apps/frontend/app/evidence/page.tsx` to determine whether this is a regression: the empty-state
component is gated strictly on `claims.length === 0` (not on "0 passing claims") — with ~8 registered
(all-FAIL) claims, `claims.length > 0`, so the code's own logic correctly renders the card list, not the
empty-state placeholder. This is pre-existing, unchanged, intentional behavior, not a defect introduced or
missed this iteration. Critically, the safety-relevant assertions all hold: no card reads "Proven", no
"Backend unavailable" card, no blank page, and the intro subtitle itself states the honesty contract ("A
signal reads 'Proven' ONLY when a referee-certified, out-of-sample, control-beating claim backs it;
everything else honestly reads 'Not yet proven.'"). I am marking this PASS on the substance (anti-goal
compliance, no fabrication, no error state) while flagging the test-plan's specific expected string as
inaccurate for the current data state (8 non-empty all-FAIL claims, not 0 claims) — this looks like the
ui-test-designer described the true-empty case without checking the live ledger's actual claim count.

### UT-10 — Full-history toggle shows deep history without fabrication
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-27-evidence/UT-10-aapl-initial.png`, `UT-10-aapl-full-history.png`, `UT-10-aapl-top.png`
- Clicked "Full history"; `GET /api/stocks/AAPL/bars?range=full` confirmed via direct API check: 3,185 bars
  from `1996-01-02` to `2026-07-01` (older bars weekly-sampled, per the label) — this matches the app's own
  disclosed data-seed boundary ("Price history 1996-01-02 → 2026-07-01" shown on `/data`), not a fabricated
  extension and not a truncated recent-only window.
- Chart line rendered continuously with no discontinuous jump (early-era prices near $0 on the linear scale
  is expected given AAPL's split-adjusted 1996 price of ~$0.24, not a rendering defect).
- All three score cards remained populated and unaffected by the toggle: Leadership E 55.78/100, Entry
  Quality D 69.70/100, Risk E 33.12/100 — each also correctly tagged "Not yet proven".

### UT-11 — Membership timeline honest entries/exits
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-27-evidence/UT-11-membership-timeline-fullpage.png`

Note: viewport-scoped `screenshot` calls returned blank/black images specifically at this panel's scroll
depth (a tool-side capture glitch, confirmed via `elementFromPoint`/DOM inspection that real, correctly laid
out content was present the whole time — table cells, filter chips, and an SVG chart all resolved with real
text/geometry). A `fullpage:true` capture bypassed the glitch and shows the panel correctly. Panel confirmed:
"Resolved universe size" step chart (max 542, 2005-02-25 → 2026-07-01, green step-line trending from small
early values up to 541); paginated table (322 dates, 33 pages of 10) with real per-date entries, e.g.
`2026-06-22 → size 540, exits −1 ERIE`, `2026-06-17 → size 541, exits −1 PSKY` — specific ticker-level,
date-attributed exits, not smoothed or fabricated. No console error, no "Backend unavailable" card.

### UT-12 — Core pages meet performance budgets
**Verdict:** PASS
**Evidence:** curl timings below; cross-checked against `reports/perf-budgets.md`

Warm HTTP response timings measured directly against the live backend/frontend (warm after three
consecutive full-universe rebuilds in this same session):

| Page | Wall time | Budget |
|---|---|---|
| `/stocks` | 0.01s | ≤3s |
| `/stocks/AAPL` | 0.01s | ≤3s |
| `/data` | 0.01s | ≤3s |
| `/evidence` | 0.01s | ≤3s |

| API | Wall time | Budget |
|---|---|---|
| `/api/health` | 0.09s | ≤0.1s |
| `/api/stocks` | 0.09s | ≤1.5s |
| `/api/stocks/AAPL` | 0.00s | ≤0.3s |
| `/api/data` | 0.03s | ≤1.5s |

All within budget with wide margin. `reports/perf-budgets.md`'s own iter-27 section independently confirms
the memory-hardening change did not regress timing (cold `/api/data` repro: 30-31s per cycle, well under the
130s+30s allowance).

### UT-15 — Data Manager discoverable, labels unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-27-evidence/UT-15-data-manager-nav.png`
- Sidebar: `["Dashboard","Stocks","Themes","Sectors","Scanner Runs","Backtest","Research","Evidence",
  "Watchlist","Methodology","Data Manager"]` — exact match, no new/removed/renamed entry.
- Clicked "Data Manager" from `/` → landed on `/data` in one click (confirmed via `window.location.href`).
- All 6 named panels present with unchanged titles: "Dataset coverage", "Storage footprint", "Rebuild
  snapshots for current universe", "Dynamic-universe membership timeline", "Start a fetch / backfill job",
  "Job progress".

---

## Failed Tests

None.

---

## Skipped Tests

### UT-01 — Cold-start-first: `/data` survives as the very first request after a backend restart
**Verdict:** SKIPPED
**Reason:** This test requires stopping and restarting the backend process twice. I attempted `kill -TERM`
on the backend PID (1785415) and the command was denied by the Claude Code auto-mode permission classifier
before any side effect occurred (verified: `/api/health` still returned 200 and the PID was unchanged
immediately after the denial). This matches the coordinator's own note that the backend is coordinator-
managed this run and "you likely won't have permission to restart it." I did not attempt any further
workaround, per the denial's explicit instruction not to circumvent it. This is an execution-environment
permission constraint, not a product defect — a re-run with an operator who has backend-lifecycle
permission is needed to execute this specific test.

### UT-13 — Backend-down: ONE contained "Backend unavailable" card
**Verdict:** SKIPPED
**Reason:** Same as UT-01 — requires stopping the backend process, which I do not have permission to do in
this session.

### UT-14 — Backend recovery after restart
**Verdict:** SKIPPED
**Reason:** Depends on UT-13's precondition (backend stopped, "Backend unavailable" card showing). Since
UT-13 could not be executed, this test's starting state does not exist. Same underlying permission
constraint as UT-01/UT-13.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (confirmed `MALLOC_ARENA_MAX=2` present in the live process
  environment, PID 1785415, throughout this session)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-11 (session ran into 2026-07-12 UTC late in the run)
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-27-evidence/`
- **Dataset:** full 322-date × 590-symbol / 541-member-universe seed (3,293,160 price-bar rows), the real
  crashing shape this iteration's fix targets — not a toy/subset dataset.
- **Note on UT-02's scope:** exceeded the test plan's minimum requirement — ran 3 consecutive full-universe
  rebuilds instead of the required 2, all reaching `status:"ok"` with no backend downtime, no `MemoryError`,
  and no VSZ/RSS-driven wedge at any point.
