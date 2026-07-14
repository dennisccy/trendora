# Phase goal-mcp-loop-iter-32 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-32 (certification-budget accounting panel + J-19 close-out)
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255` (this run's offset port — substitute your actual running port if different)
- Backend running and reachable (no login is required anywhere in this product)
- No setup/seed data needed — the live ledgers already hold real trial history (7 canonical + 7 staging trials, 11 registry rows, 7 all-FAIL evidence claims) that this iteration did not touch

---

## Steps

1. Open `http://localhost:3255/research` in your browser
   - **Expect:** The Research hub loads; scrolling down, a "Governance & process" section shows 3 cards, the third one titled "Certification-budget accounting" (wallet icon)

2. Click the "Certification-budget accounting" card
   - **Expect:** Browser navigates to `http://localhost:3255/research/budget`; the heading "Certification-budget accounting" appears with a "Back to Research" link above it

3. Wait a couple of seconds, then read all four cards on the page
   - **Expect:** Four cards show: **"7"** (Total trials to date), **"0.00625"** (Current canonical required p), **"0.9"** (Thresholdout budget remaining), **"0.0003926"** (Staging LORD++ next-trial level) — each with a small trend-line graphic underneath. Nowhere on the page does the word "Proven" or "Not yet proven" appear as a status badge.

4. Navigate to `http://localhost:3255/research/graveyard`
   - **Expect:** The Negative-results graveyard table loads with data rows

5. Click any row's Lineage link (an id followed by "→", in the rightmost "Lineage" column — skip any row that instead says "No registration lineage")
   - **Expect:** The browser navigates to `.../research/registry#registration-<id>` **and the page automatically scrolls down** so the matching row is already visible — you should NOT have to scroll manually to find it. This is the trickiest check this round: an earlier version of this page landed at the very top with no scroll.

6. Navigate to `http://localhost:3255/evidence`
   - **Expect:** 7 claim cards appear; every visible verdict badge reads **"FAIL"** (none read "PASS")

7. Navigate to `http://localhost:3255/stocks`
   - **Expect:** The leaderboard loads with stock rows; each row shows **"Not yet proven"** badges next to its 3 scores (Leadership, Entry quality, Risk)

---

## What "Working Correctly" Looks Like

- The budget panel's four cards show plain numbers and formulas (a trial count, `0.05 ÷ 8`, a remaining budget, a staging level) with small trend lines underneath — never a "Proven"/"Not yet proven" badge anywhere on that page
- Clicking a graveyard row's Lineage link visibly jumps you partway down the registry page, landing right on the matching row — not stuck at the top

## Common Issues

- **Blank page / error screen on `/research/budget`**: check the backend is running (`curl http://localhost:8255/api/health` should return `"readiness":"ready"`). If the backend is genuinely down, you should see a contained red "Backend unavailable" card instead of a blank page — a truly blank or crashed page (not that red card) is itself a bug.
- **Lineage link doesn't scroll**: if clicking a graveyard row's Lineage link lands you at the very top of `/research/registry` with no auto-scroll, that is exactly the regression this round is re-verifying is fixed — flag it immediately.
- **Numbers look different from this guide**: the ledger legitimately grows over time as new trials get certified. If the four budget numbers are internally consistent (e.g. "Current canonical required p" = `0.05 ÷` the trial number named in its own subtext), that's fine — only flag it if the math doesn't add up, or a card is blank/stuck loading.
