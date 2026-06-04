# Phase goal-i_can_see_the_wealthy_future_forever-iter-17 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-17
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend reachable (the Backtest page reads `/api/backtest`)
- Seed data loaded so the top-bar "View as-of date" dropdown lists more than one date
- No login required

---

## Verification Steps

<!-- Each step has an exact action and exact expected outcome. -->

1. Open `http://localhost:3835/backtest` in your browser
   - **Expect:** The "Backtest" page loads (no red "Backend unavailable" card). After the loading skeleton clears, scrolling to the very bottom reveals a section headed **"Forward-tested evidence (expanding window ≤ &lt;a date&gt;)"**.
   - **Broken looks like:** the bottom of the page ends at the "Ranked cohort" table with no evidence section, or shows a red error card.

2. In that bottom section, read the summary line and the panels below it
   - **Expect:** A line reading "Snapshots contributing (≤ &lt;date&gt;): &lt;number&gt;" … "Mean stock fwd return (&lt;N&gt;d): &lt;pct&gt; (n=&lt;number&gt;)", followed by panels "Forward return by score bucket" (rows A–E), "Excess vs benchmarks" (Excess vs SPY / Excess vs QQQ), by setup type, by market regime, VCP vs non-VCP, pullback, flat-base, and a "Control-group comparison" table.
   - **Broken looks like:** any cell shows `null`, `NaN`, or `undefined`.

3. Note the "Snapshots contributing" number, then at the top bar open the **"View as-of date"** dropdown and select an **earlier date** (any option below "Latest · …")
   - **Expect:** The top-bar badge turns amber: "Viewing as-of &lt;D&gt; (historical)". After the brief reload, the evidence heading now reads "… (expanding window ≤ &lt;the earlier D&gt;)" and the "Snapshots contributing" count and "(n=…)" are **smaller** than before.
   - **Broken looks like:** the count/n stays identical to the Latest view (evidence not re-scoping to the date).

4. Re-open the **"View as-of date"** dropdown and select the first option **"Latest · &lt;date&gt;"**
   - **Expect:** The badge returns to a quiet "Latest"; the "Snapshots contributing" count and "(n=…)" return to the original (larger) all-history values from step 3.

5. Open browser DevTools → **Network** tab, filter for "backtest", clear the log. Then find the **"Horizon"** button group (in the Return Attribution header) and click a different button (e.g. "20d")
   - **Expect:** Every evidence panel's numbers change (the summary now says "Mean stock fwd return (20d): …", the control-group hint says "At 20 days: …"), and **NO new `/api/backtest` request appears** in the Network log — the switch is instant and client-side.
   - **Broken looks like:** a new `/api/backtest` network request fires, or the panels don't change.

6. Look at the browser **address bar** after steps 3–5
   - **Expect:** The URL stays `http://localhost:3835/backtest` with **no** `?as_of=…` or date/horizon query parameter. There is no second date dropdown inside the evidence section — only the single top-bar switcher controls the date.

7. Look at the **left sidebar**
   - **Expect:** 10 items — Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Watchlist, Methodology, Data Manager. There is **no "System Health"** link.

8. Type `http://localhost:3835/system-health` directly into the address bar and press Enter
   - **Expect:** A 404 "This page could not be found" page. The evidence now lives only on Backtest.

9. (Optional) On `/backtest`, scroll the whole page and confirm section order: As-of scan summary → Forward-test scorecard → Return attribution → Leadership cohorts (Top Sectors / Top Themes / Ranked cohort) → Forward-tested evidence (last)
   - **Expect:** Exactly one "Return attribution" heading; the new evidence section is the **last** block, below the leadership lists.

---

## What "Working Correctly" Looks Like

- The bottom of `/backtest` shows a clearly-labelled "Forward-tested evidence (expanding window ≤ &lt;date&gt;)" section with a shrinking sample `n` as you move the global date earlier.
- Switching the Horizon buttons re-renders all evidence numbers instantly with **zero** new network calls.
- The sidebar has no "System Health", and `/system-health` is a 404.
- Empty/low-sample cells show "—" or an "⚠" flag — never a fabricated number.

## Common Issues

- **No evidence section at the bottom of /backtest**: confirm the backend is running (`curl http://localhost:8000/api/backtest`); a red "Backend unavailable" card means the API didn't respond.
- **Count/n doesn't shrink when picking an earlier date**: the React `<select>` may not have fired its change — pick the date again from the dropdown and wait for the loading skeleton to flash before re-reading.
- **Empty-state card "No forward-tested evidence for this window yet"**: this is expected when you pick the earliest date and/or the 60d horizon — it is the honest empty state, not a bug.
- **Horizon click triggers a network request**: that is a failure of the no-refetch requirement (J-15) — flag it.
