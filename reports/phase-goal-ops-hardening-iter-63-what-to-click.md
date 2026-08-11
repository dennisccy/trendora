# Phase goal-ops-hardening-iter-63 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-63
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Backend running in prod mode (`scripts/start-backend.sh`) and frontend at `http://localhost:3255`
- No login required
- This iteration is backend-only (a scheduling-only latency fix inside the ingest finalize tail, plus
  test-infrastructure repairs) — there is no new capability to click. This guide instead spot-checks the
  7 required-still-passing journeys (J-01, J-03, J-04, J-05, J-06, J-08, J-09) plus J-07, the one target
  journey this iteration's fix addresses, using the fastest observable proxy for each — never the full
  15–40 minute live ingest jobs those journeys' own definitive proof requires.

---

## Verification Steps

1. Open `http://localhost:3255/` in your browser
   - **Expect:** Dashboard loads; the readiness badge (top bar) reads "Ready", no error page (J-04)

2. Navigate to `http://localhost:3255/data`
   - **Expect:** "Data Manager" heading; a "Run history" panel lists prior runs; a "Last run" status
     shows a real value (e.g. "no new snapshots") — not blank (J-04/J-05 read-path)

3. In the job form, type "2026-05-02" into "Start date" and "2026-05-03" into "End date" (a fast
   weekend-only span), then click "Start"
   - **Expect:** Within a few seconds the job reports "0/0 dates" and "2 calendar days · 0 already
     snapshotted · 2 non-trading", shown in a neutral gray/muted zero-work note — NOT a green success
     badge (J-01 fast path)

4. Navigate to `http://localhost:3255/scanner-runs`
   - **Expect:** A table with multiple rows, each showing a past as-of date — confirms prior heavy
     backfills/aggregates persisted (J-03/J-05 read-path)

5. Click any row's date
   - **Expect:** Page shows "Immutable snapshot — as of <date>" and a leaderboard table with an "ENTRY
     QUALITY" column populated with rows — confirms stored aggregates render, no recompute delay (J-05)

6. Navigate to `http://localhost:3255/backtest`
   - **Expect:** "Backtest" heading; the text "Snapshots contributing" appears immediately, no spinner
     stuck loading (J-08)

7. Click the "Previous available date" button
   - **Expect:** The page updates immediately (no freeze) and shows the text "(historical)" (J-09)

8. Navigate back to `http://localhost:3255/data`
   - **Expect:** A "background compute" panel is visible and contains the text "process-lifetime only,
     never persisted"; the "Last run" status and the aggregates-refreshed list (e.g. "Refreshed: forward
     aggregates, research hot keys, factor lab all, drawdown expectations") both still show real values,
     not blank — confirms the service stayed healthy through this iteration's finalize-tail fix (J-07/J-09)

9. Quickly click through `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/evidence`, and
   `/research/regime-lab` in the nav
   - **Expect:** Each page's own heading ("Stocks", "AAPL", "Sectors", "Themes", "Evidence", "Research —
     Regime Lab") appears within 2-3 seconds, no blank page and no error boundary (J-06)

10. Confirm nothing above showed a crash screen, a permanently blank page, or a frozen spinner
    - **Expect:** All 9 checks above passed cleanly — this is the full regression sweep this
      backend-only iteration requires

---

## What "Working Correctly" Looks Like

- Every page you visit shows real content within a few seconds — never a blank white screen or a spinner
  that never resolves
- The zero-work backfill in step 3 explains itself in neutral/gray styling, never claiming false success
- The background-compute panel in step 8 always shows a real, non-fabricated state (even "No background
  compute running" counts as real — that's an honest idle state, not a missing panel)

## Common Issues

- **Blank page / error screen anywhere**: the backend may not be running in prod mode — check
  `curl http://localhost:8255/api/health` (or the configured backend port) responds
- **Step 3's backfill never finishes / job form stuck on "Job running…"**: this iteration's fix targets
  exactly this phase (`coverage_membership_timeline_refresh`) — if the job visibly hangs rather than
  completing within well under a minute for this tiny weekend-only span, that is the regression this
  iteration exists to prevent; escalate rather than waiting it out
- **J-05's own full live-ingest proof is NOT covered by this 5-minute guide** — it is a genuine
  15–40 minute job; see `reports/phase-goal-ops-hardening-iter-63-ui-test-plan.md`'s UT-J-05 for the full
  procedure if a deeper check is needed
