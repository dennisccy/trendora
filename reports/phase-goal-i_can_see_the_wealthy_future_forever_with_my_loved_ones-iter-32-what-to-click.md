# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running and seed data loaded (the Research page should show existing labs with data, not a permanent spinner)
- No FRED_API_KEY environment variable set (the default state — macro is off by default)

---

## Verification Steps

1. Navigate to `http://localhost:3835/research` and scroll to the bottom of the page
   - **Expect:** Below the "Recovery-Turn Edge" lab, a new "Downtrend Opportunity" section is visible with three table panels: "Held up best", "Fell hardest", and "Recovery-turn edge by phase". If you see only a loading spinner after 15 seconds, the backend may still be warming up — refresh once and wait.

2. In the "Downtrend Opportunity" section, click the "Condition on" dropdown and select "Severity band"
   - **Expect:** All three tables immediately update their row labels to show severity-band cohort names (e.g., "Mild", "Moderate", "Severe"). The global as-of date in the page header does NOT change. No page reload occurs.

3. Locate the "Fell hardest" table panel and read the label near its header
   - **Expect:** A label reading "Research evidence only" (or similar) is visible near the "Fell hardest" table heading. There are NO Buy, Sell, Short, or Trade buttons anywhere in or adjacent to this table.

4. In the "Held up best" table, find any row with an `N=` chip (e.g., "N=12") and click it (use Ctrl+click or middle-click to open in a new tab)
   - **Expect:** A new browser tab opens at `http://localhost:3835/research/samples` with a URL containing `kind=downtrend_opportunity`. The samples page shows a cohort description header (e.g., "Downtrend opportunity — Severity band: Severe") and the total observation count on that page matches the number that was in the chip. If the count does not match, this is a count-coherence failure.

5. Navigate to `http://localhost:3835/data` and scroll past the missing-data diagnostic until the "Macro feed" panel is visible
   - **Expect:** A "Macro feed" panel appears with a table listing at least four macro series rows. The env-var detection column shows the name "FRED_API_KEY" with a status of "not set (NA)" or "not detected" — the panel must NOT display any actual API key string. Three per-leg enable flags (severity / regime switching / study) all read "off". A note states that "default figures are unchanged" while all legs are off.

6. Navigate back to `http://localhost:3835/research` and scroll to the existing "Recovery-Turn Edge" lab (above the Downtrend Opportunity section)
   - **Expect:** The standalone Recovery-Turn Edge lab still shows data identical to what it showed before this iteration. The "Recovery-turn edge by phase" panel inside the Downtrend Opportunity section shows the same rows for the same horizon. If the standalone lab is empty or shows different values, this is a regression.

7. Navigate to `http://localhost:3835/` (the Dashboard) and locate the Market-Phase panel
   - **Expect:** The Market-Phase panel shows a regime label and severity score as before. No new date picker, macro-conditioned score indicator, or second date control appears. The date displayed matches the global as-of.

---

## What "Working Correctly" Looks Like

- On `/research`: the "Downtrend Opportunity" section appears below Recovery-Turn Edge with three side-by-side ranked tables; the "Condition on" dropdown changes all three tables; `N=` chips open count-coherent samples; the "Fell hardest" table carries an "evidence only" label; survivorship-bias and macro publication-lag notices are both visible in the section.
- On `/data`: the "Macro feed" panel lists four series rows; the FRED env-var detection shows "not set (NA)" with no key value visible; all three wiring legs show "off".

## Common Issues

- **Downtrend Opportunity section not visible**: Scroll past ALL existing labs — it is appended at the very bottom of the Research page. If the section is genuinely absent after scrolling, the frontend component was not deployed.
- **N= count mismatch on samples page**: This is a count-coherence failure. Note the chip value and the samples page total and report them as evidence.
- **Macro feed panel not visible on /data**: Scroll below the missing-data diagnostic. If absent, the frontend Data Manager component was not updated.
- **Backend unavailable / spinner forever**: Check that the backend process is running on port 8835. Run `curl http://localhost:8835/health` to confirm.
