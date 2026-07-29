# Phase goal-ops-hardening-iter-29 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-29
**Date:** 2026-07-27
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On the **Evidence** page (`/evidence`), users can now tell the difference between two situations that
  previously looked identical: a claim whose drawdown/dry-spell history genuinely doesn't apply (panel
  section stays blank, as before) versus a claim whose drawdown/dry-spell history simply failed to compute
  this time (the card now shows a short note: "Unavailable — monitored and refreshed as new data arrives.").
  Before this iteration, both cases rendered nothing, so a real compute failure was indistinguishable from
  "not applicable."
- This is a passive disclosure only — there is no new button, link, filter, or click path. The user does not
  do anything differently; they simply see more honest information on the one affected claim's card, if and
  when that failure occurs.

---

## What Changed in the Visible UI

- The **Evidence** page's per-claim "Historical drawdown & dry-spell expectations" panel (inside each
  claim's card, below the existing hypothesis/verdict/control-comparison/registration-date/forward-walk
  field grid) can now render a **third state** in addition to its two existing ones:
  - Heading: "Historical drawdown & dry-spell expectations"
  - Body text: "Unavailable — monitored and refreshed as new data arrives."
  - Styling: small, faint/muted text (`text-text-faint`) — the same calm, non-alarming treatment already
    used elsewhere on the same card for the "Pending — monitored as new data matures" forward-walk note.
    Never a red, warning, or error-styled treatment.
  - Carries `data-testid="evidence-expectations-unavailable"` in the page markup, for automated checks.
- The two pre-existing states are unchanged in appearance: a full table (deciles-by-phase, underwater,
  time-to-recover, loss-streak figures) when the data resolves successfully, and a blank panel section
  (nothing rendered) when a claim's cohort genuinely has no applicable history.
- No new page, no new navigation entry, no new field visible anywhere else in the product. The change is
  scoped entirely to this one panel on the existing `/evidence` claim cards.

---

## What Old Behavior Changed

- **Evidence page resilience (not a visual change under normal conditions):** previously, if the background
  computation behind even one claim's drawdown-expectations panel ran out of memory, that failure could
  break the entire `/evidence` data request — potentially preventing every claim's card from loading, not
  just the one that failed. Now, a failure on one claim is isolated: every other claim's card still renders
  normally, and only the failing claim shows the new "Unavailable" note. Testers should re-verify that a
  simulated single-claim failure no longer affects the other claims on the page.
- **Underlying computation reliability (no visible difference in normal operation):** the calculation that
  powers both the Evidence page's expectations panel and the separate `/research/factor-lab` page's decile
  table and rank-IC figures was rewritten to use a bounded, fixed-size amount of memory instead of memory
  that grows with the full amount of stored price history. Output values are unchanged (verified
  byte-identical by the developer's tests) — so nothing should look different on either page — but both
  pages are now less likely to fail or slow down as historical data continues to accumulate. Testers should
  confirm both pages still show the same real data they did before, with no crash, blank table, or console
  error.

---

## Not Visible Yet

None. Every backend change made this iteration is either:
- fully wired through to a visible element (the new `expectations_status` field → the "Unavailable" note
  on the Evidence page), or
- a deliberately invisible reliability/memory fix (the bounded computation in `research.py`), whose entire
  point is to produce **byte-identical** output — it is not a hidden feature awaiting UI wiring, it is a
  backend robustness change with no display component of its own.

Two similar-but-separate calculations elsewhere on the Research pages (serving "combination" and
"event-study" claim kinds) carry the same theoretical memory-growth risk but were deliberately **not**
touched this iteration (named follow-up, out of scope) — there is nothing new to observe there because
nothing changed there.
