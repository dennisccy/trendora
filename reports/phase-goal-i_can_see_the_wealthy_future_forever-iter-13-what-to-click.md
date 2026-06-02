# Phase goal-i_can_see_the_wealthy_future_forever-iter-13 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-13
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running and reachable (port 8835)
- Database was regenerated this iteration (snapshots carry the new volatility values)
- A seeded **Risk-Off** run is selectable on `/stocks`

---

## Verification Steps

<!-- Maximum 10 steps. Prioritize: 1) the new volatility family works, 2) honest NA, 3) score regression after DB regen. -->

1. Open `http://localhost:3835/research` in your browser
   - **Expect:** Heading "Research — Factor Lab" loads; an amber card "Survivorship bias · universe-relative · descriptive" is visible; a decile table and a "Rank-IC" card render with data. No red "Backend unavailable" card.

2. Click the "Factor" dropdown (top-right, under the "Factor" label) and look at how options are grouped
   - **Expect:** Options sit under family sub-headings (Score, Momentum, Trend, **Volatility**, …) — not a flat list. The "Volatility" group lists exactly four entries: "ATR % (volatility level)", "Historical volatility (HV)", "Volatility contraction (VCP-style)", "Downside volatility (semivol)".

3. Select "Historical volatility (HV)" from the Volatility group
   - **Expect:** The factor header line above the table reads `Factor: Historical volatility (HV) (volatility · lower better)`. The Rank-IC card shows a signed numeric value (≈ `+0.03`) with an `n` chip — not "NA", not blank.

4. Select "Volatility contraction (VCP-style)" from the Volatility group
   - **Expect:** The decile table re-populates with columns "Mean fwd return" AND "Risk-adjusted (downside)", D1–D10 rows, each with a small `n` chip. Header line reads `… (volatility · lower better)`.

5. Select "Downside volatility (semivol)", then scan the "Risk-adjusted (downside)" column and the "Factor effectiveness by market regime" table for an "NA"
   - **Expect:** At least one cell shows the literal text **"NA"** (muted grey) with its `n` still shown beside the row — never "0" or a blank. This proves downside risk is honest (a healthy all-up decile is not penalised).

6. Toggle the global as-of date control, then re-read the decile table and Rank-IC value
   - **Expect:** The Factor-Lab numbers are unchanged before vs after the toggle (the lab is a cross-date aggregate; it must not move with as-of).

7. Navigate to `http://localhost:3835/stocks` and open the seeded **Risk-Off** run
   - **Expect:** **Zero** stocks are marked "Actionable" (the Risk-Off gate survived the DB regen).

8. On `http://localhost:3835/stocks`, find the **NVDA** row and read its three scores; then open `http://localhost:3835/stocks/NVDA` and read them again
   - **Expect:** Identical in both views — Leadership **47.48 / E**, Entry Quality **66.24 / D**, Risk **33.79 / E**. The new volatility values (hv, vcp_contraction, downside_vol) do NOT appear on the detail page.

---

## What "Working Correctly" Looks Like

- The Factor dropdown is grouped, and the "Volatility" group has four selectable measures (previously only ATR %).
- Each volatility measure populates a full decile table (raw + downside-risk-adjusted + n), a numeric Rank-IC with n, and a by-regime split.
- Undefined/low-sample cells read "NA" + n — never a fabricated 0.
- After the DB regen, the Risk-Off Actionable count is 0 and NVDA's three scores match across leaderboard and detail.

## Common Issues

- **Red "Backend unavailable" card on /research**: backend not running — confirm the API on port 8835 (`curl http://localhost:8835/api/research/factor-lab`).
- **Volatility group missing or flat list**: the `<optgroup>` grouping or the config catalog entries didn't load — hard-refresh; check `config.yaml` `research.factor_lab.factors`.
- **NVDA scores differ between views, or Risk-Off shows Actionable > 0**: a regression from the DB regen — this is a hard blocker; flag immediately.
- **A risk-adjusted cell shows "0" instead of "NA"**: fabricated value regression — flag it; downside-undefined must render NA + n.
