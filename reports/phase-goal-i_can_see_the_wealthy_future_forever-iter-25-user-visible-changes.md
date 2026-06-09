# Phase goal-i_can_see_the_wealthy_future_forever-iter-25 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-25
**Date:** 2026-06-09
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On the `/data` Data Manager page, users can now read a Missing-data diagnostic panel that
  names every universe member that is insufficient for analysis — split into three honest
  categories: no history (zero bars), thin history (bars below the analysis threshold), or
  intra-series gaps (trading days missing inside the member's own date range). Each row shows
  the symbol and its exact shortfall in plain language (e.g. "12 / 200 bars" or "3 missing
  2025-01-15 → 2025-02-03").

- For each fixable diagnostic row (no-history and intra-series-gap members), users can click
  "Pull the missing data" to start a fetch covering exactly that symbol's diagnosed gap — not
  the whole universe or the whole window. A "Pull all missing" button does this for every
  fixable row in sequence. Live job progress surfaces in the existing job card; on completion
  the diagnostic row clears and the coverage table reflects the new bars.

- Users can now see every import that did not finish cleanly — paused (rate-limited), partial
  (some symbols failed), or fully failed — in one unified Unfinished-imports panel on the
  `/data` page. Each row shows a plain-language state explanation, done/remaining/failed
  counts, and chunk progress where applicable.

- For each unfinished import, users can now choose the right action from its row: Resume
  (paused/resumable imports, continues from where it stopped), Retry remaining/failed (partial
  or failed runs, re-fetches only outstanding work), or Remove/Dismiss (drops the actionable
  record from the list; the permanent run-history audit entry remains visible below).

- For a needs-key import source, a Retry or Resume action in the Unfinished-imports panel
  re-prompts the user to paste the session-only API key before re-dispatching — the key is
  held in memory for that request only and never stored anywhere.

---

## What Changed in the Visible UI

- A new "Missing-data diagnostic" panel now appears on the `/data` page directly below the
  Coverage panel. When the diagnostic is empty (every member has enough history and no gaps),
  the panel renders a clean "No missing data" empty-state rather than hiding silently.

- The three diagnostic categories — "No history", "Thin history", and "Intra-series gaps" —
  are each rendered as a labeled section with per-row symbol + exact shortfall. Thin rows
  display the shortfall for transparency but have no Pull button (they are not directly
  pullable). No-history and intra-series-gap rows have a per-row "Pull the missing data"
  button and are included in the "Pull all missing" action.

- The existing "Resumable imports" panel has been replaced by the new "Unfinished-imports"
  panel. The panel now lists all three import states (resumable/paused, partial, failed)
  rather than only paused imports. Each row shows a status badge (amber for paused/partial,
  red for failed), a server-built plain-language state string, and the appropriate action
  buttons (Resume / Retry / Remove-Dismiss). The panel is hidden entirely when there are no
  unfinished imports.

- Each unfinished-imports row now carries a "Dismiss" or "Remove" button regardless of import
  state. Clicking it removes the row from the panel immediately; the run-history audit table
  below the panel remains unchanged.

- New `data-testid` attributes are present on the diagnostic panel (`missing-data-diagnostic`,
  `pull-all-button`, `pull-row-button`, `diagnostic-no-history`, `diagnostic-thin-history`,
  `diagnostic-intra-series-gaps`) and on the unfinished-imports panel (`unfinished-imports`,
  `unfinished-checkpoint`, `unfinished-run`, `unfinished-state`, `retry-button`,
  `dismiss-button`) — these are browser-automation hooks and do not affect visible appearance.

---

## What Old Behavior Changed

- Resumable-imports panel renamed and generalized: previously the panel listed only
  paused/resumable imports and offered only a Resume action. It now lists every unfinished
  import (paused + partial + failed), adds Retry and Remove/Dismiss actions, and is hidden
  when empty rather than showing a blank card.

- Pull/retry date inputs are job parameters, not a viewing-date control: the page's global
  as-of date switcher is unchanged. The new "Pull the missing data" and "Retry" actions submit
  the diagnosed date range as a job parameter — they do not move or duplicate the single
  global date selector.

---

## Not Visible Yet

- None — every backend capability added this iteration (missing-data diagnostic, gap-exact
  pull constructor, unified unfinished-imports list, retry, dismiss, and the new
  `unfinished_imports` + `coverage.diagnostic` API fields) is wired into the `/data` UI and
  is accessible to the user.

- The J-39 Remove-data confirm-preview panel and the J-35 injected-provider expand capability
  were not changed this iteration (no code change); their browser flows are pending re-capture
  by the QA gate on a clean hydrated build.
