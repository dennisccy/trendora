# Phase goal-mcp-loop-iter-31 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-31 (goal mode, journey J-19 / backlog B-902)
**Date:** 2026-07-13
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now browse every hypothesis the system's statistical referee has ever rejected by navigating to `/research` and clicking the new "Negative-results graveyard" card, or by going directly to `/research/graveyard`.
- Users can now see, for each rejected hypothesis, six pieces of information side by side: its exact cohort selectors (as key=value chips), the verdict kind (`FAIL` or `INSUFFICIENT`), the date it was tested, the deflation / multiple-testing-correction context that was applied (e.g. `bonferroni ÷8`), which ledger it came from (`canonical` or `staging`), and — when known — a link tracing it back to its registered hypothesis.
- Users can now identify a permanently closed hypothesis (today: the `ma_stack` moving-average idea) via a "permanent" pill next to its verdict, signaling it must never be silently retried.
- Users can now read the exact "revisit protocol" — the rule governing whether and how a rejected idea may ever be re-tested — in a dedicated panel on the graveyard page, and jump straight to it from a "Revisit protocol →" link on every row.
- Users can now click a graveyard row's Lineage link and land precisely on that hypothesis's own row on `/research/registry` (the page scrolls to and positions the exact row, not just the top of the page).
- Users can now see results from the system's internal/staging exploration track for the first time anywhere in the product — specifically its rejected ideas only. Nothing about which values count as "Proven" changed anywhere else.

---

## What Changed in the Visible UI

- The `/research` hub's existing "Governance & process" grid now shows a second card, "Negative-results graveyard," beside the existing "Pre-registration registry" card. Clicking it navigates to `/research/graveyard`.
- A new page, `/research/graveyard`, was added: a page heading ("Negative-results graveyard" + a one-line description), a six-column table (Selectors / Verdict / Date / Deflation / Ledger / Lineage), and a "Revisit protocol" panel below the table. A "Back to Research" link sits at the top, matching the Registry page's pattern.
- On `/research/graveyard`, verdict badges render in the same red ("FAIL") / amber ("INSUFFICIENT") styling the Evidence page already uses for those two statuses — never the page's green "Proven" styling, since this page shows only rejected ideas.
- `/research/registry`'s table rows are now individually addressable by URL (e.g. `#registration-<id>`). There is no visible difference when browsing the page normally top to bottom; the difference only appears when arriving via such a link (see below).

---

## What Old Behavior Changed

- `/research/registry`: a row reached via a URL fragment (e.g. `/research/registry#registration-REG-003`, as produced by a graveyard Lineage link) now scrolls to and positions that exact row beneath the page header. Previously no such fragment links existed anywhere in the product, so this is a new capability rather than a regression — but it is a change to how the existing registry page responds to navigation, worth re-verifying that normal (non-anchor) browsing of the page is visually unchanged.
- Nothing else changed. The dev handoff records that `/evidence`, `proven_signals`, the "Proven" badge, and `/research/registry`'s own listing were confirmed to return byte-identical data before and after this iteration.

---

## Not Visible Yet

- None. This iteration's one new backend capability — `GET /api/research/graveyard`, backed by the new `app.engine.graveyard` composition module — has a complete, matching UI consumer: the new `/research/graveyard` page is its only consumer and renders everything the endpoint returns (all entries, plus the revisit-protocol text). There is no backend capability from this iteration left unwired to the UI.
