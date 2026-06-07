# Phase goal-i_can_see_the_wealthy_future_forever-iter-23 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-23
**Date:** 2026-06-07
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Grow the scored universe by selecting "Expand universe" from the job-kind dropdown on the `/data` Data Manager page and starting the job over a market-cap-capable source (Yahoo, Tiingo, or Finnhub).
- See exactly which candidates from the committed pool passed the screen (passers count) and which were omitted — with the specific reason for each omission (e.g. "market_cap below threshold", "price below $10", "no_market_cap", "fetch_failed") — displayed in the job card's "Universe screen" block once the expand job runs.
- Identify at a glance which import sources cannot run an expand job: when "Expand universe" is selected, Alpha Vantage and Stooq are shown as disabled options with the reason "cannot supply market cap — not selectable for expand" appended directly in the source dropdown.
- Resume a rate-limited expand job from where it stopped, using the same existing amber "Resume" control on the live job card or the "Resumable imports" panel — no new interface needed.
- See the grown universe count reflected immediately in the Coverage panel's "Universe" metric (`universe-count`) after a completed expand, without a page reload.

---

## What Changed in the Visible UI

- The job-kind `<select>` on `/data` now includes a fourth option: "Expand universe" (previously only Backfill snapshots / Fetch EOD prices / Fetch + backfill).
- The panel title hint text on the "Start a fetch / backfill / expand job" card now reads "…and — for a fetch or expand — an import source", reflecting that the source picker appears for expand jobs too.
- The panel footer description text on the job-form card now includes a sentence explaining the Expand job: "Expand screens the committed candidate pool… over a market-cap-capable source and grows the scored universe — every omitted candidate is listed with its reason."
- When "Expand universe" is selected, each source option in the Import source picker is decorated differently: eligible sources show "· available" or "· needs key" (unchanged behavior), while ineligible sources show "· cannot supply market cap — not selectable for expand" and are rendered as disabled `<option>` elements.
- When an ineligible source is selected with "Expand universe" active, a styled amber alert block appears below the source picker explaining why that source cannot be used and suggesting Yahoo as an alternative (`data-testid="expand-ineligible-reason"`).
- The job card now renders a "Universe screen" result block for an expand job, showing a green "X passed" badge and an amber "X omitted" badge (`data-testid="expand-screen-result"`, `data-testid="expand-passers"`, `data-testid="expand-omitted-count"`), with an expandable scrollable list of each omitted candidate and its reason (`data-testid="expand-omitted-list"`).
- The run-history table on `/data` now shows rows with `kind = "expand"` alongside existing fetch/backfill/both rows, and the Summary column includes the expand screen outcome (passers vs omitted).

---

## What Old Behavior Changed

- Import source picker visibility: previously the source picker only appeared when the job kind was "fetch" or "both". It now also appears when "expand" is selected, giving expand jobs the same source-selection affordance.
- Start button disabled condition: previously the Start button was only blocked when dates were missing, a job was running, or the form was busy. It is now also blocked when "Expand universe" is selected and the currently-selected source has `supports_market_cap: false`, showing the ineligible-reason alert instead of allowing a doomed request.
- The Coverage panel "Universe" count: previously this count reflected only the YAML config's 122 names. After a successful expand run that produces passing members, it will now reflect the grown universe from `universe.json` (the single-source merge introduced this iteration). On this machine the count remains 122 because no live expand can complete due to walled data feeds — but the plumbing is live.

---

## Not Visible Yet

- The live universe expansion outcome (a completed expand that actually grows the universe past 122 names) cannot be demonstrated on the current host because all market-cap data feeds (Yahoo, Tiingo, Finnhub) are blocked or rate-limited from this machine. The expand job, eligibility gating, and screen-result display are fully wired; only the live data step is environment-gated. An expand that hits the wall lands in the amber "rate-limited — resumable" state (or shows every candidate omitted with "market_cap_fetch_failed"), which is the honest behavior, not a failure.
