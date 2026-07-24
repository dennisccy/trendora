# goal-ops-hardening-iter-20 — Implementation Summary

**Phase:** goal-ops-hardening-iter-20
**Date:** 2026-07-24
**Written by:** developer

---

## Features Implemented

- **Viewing an old, never-before-viewed date on the Backtest page no longer freezes the page for up to
  nearly a minute.** The Backtest page lets you "time-travel" to any historical date and see how that
  day's picks actually performed afterward. The very first time anyone looks at a date that has never been
  looked at before, the server has to calculate that date's numbers — and until now, it did that
  calculation while making the browser wait, sometimes for as long as 54 seconds, with nothing on screen
  to explain why. This iteration moves that calculation to run quietly in the background instead: the page
  now comes back almost instantly and shows an honest "still working on it" message, then shows the real
  numbers as soon as they're ready (typically on the next reload). Nothing about the numbers themselves
  changes — they are calculated exactly the same way as before, just at a different moment.
- **The message shown while that background calculation finishes now tells the truth about why it's
  happening.** Previously this page had a "refreshing" message that only ever explained one situation
  correctly ("new data just came in"). It's now smart enough to also explain the NEW situation this
  iteration introduces ("you're the first person to look at this specific old date, so it's calculating
  now") — so the wording you see always matches what's actually going on, instead of sometimes describing
  the wrong reason.
- **Nothing new to look at otherwise.** No new page, no new button, no new information was added — this
  iteration only makes an existing, already-working feature respond honestly and quickly instead of
  silently freezing.

---

## Changed Behavior

- **Viewing an old Backtest date for the first time**: previously, the server calculation happened WHILE
  you waited for the page, which is why it could take up to about a minute with no explanation on screen.
  Now the page comes back almost immediately with a calm "this is being calculated" message, and the real
  numbers appear the next time you look at that date (the calculation itself takes the same amount of time
  as before — it just no longer blocks your browser while it happens).
- **The default (today's) view of the Backtest page is completely unaffected** — it never had this
  problem and still works exactly as it did before.
- **Two internal automated checks (not visible to a user) were updated** to match this new "calculate in
  the background" behavior instead of the old "calculate immediately" behavior; a third check in a
  separate, very slow-to-run test file was updated the same way but could not be executed this session (see
  Incomplete Items).

---

## Backend-Only Items

None — the one visible change (the corrected "still calculating" message on the Backtest page) is already
wired up and live in the interface; there is no backend-only capability left unconnected this iteration.

---

## Incomplete Items

- **One of the updated automated checks was not run this session.** It lives in a test file that, to set
  itself up, needs to load roughly 30 years of the project's full historical data — a one-time setup step
  that takes about 80 minutes on this machine. The phase's own instructions explicitly say not to run that
  setup just for a small check like this one. The edit itself was made carefully, following the exact same
  pattern used in two very similar checks that WERE run (and passed, both before and after the fix, proving
  the change is real and not accidental). **Recommend the quality-review stage runs this one file**, with a
  longer time allowance, to close out this last piece of proof.
- **A live, in-browser confirmation was not captured this session.** Confirming the "still calculating"
  message actually looks right when a person visits the page in a real browser is normally done later, by
  a separate quality-check stage — this session could not start or stop the running services itself, so
  that live check is still owed (this is a routine handoff, not a new problem).
- **Two previously-known, owner-approval-only checks remain on hold**, exactly as they have been for
  several iterations in a row: (1) re-measuring page speed while a real data update is running at the same
  time, and (2) deliberately killing and restarting the server mid-job to prove progress isn't lost. Both
  need the project owner's explicit go-ahead before they can run (a hardware-safety rule this project
  follows), and neither was this iteration's job to unblock.

---

## Config and Environment Changes

None — no new settings, environment variables, or database changes.

---

## Known Limitations

- A pre-existing, unrelated hazard in an older part of the system (from a previous iteration, already on
  record, not touched here) was seen again while building one of this iteration's checks: if a LOT of
  people looked at the exact same never-before-viewed date at the exact same instant, there's a narrow
  window where the server could log an internal error instead of quietly recovering. This iteration did not
  introduce it and did not fix it — fixing it properly is a bigger job that was explicitly called out as
  "for a future iteration" back when it was first noticed. This session's test-building work was adjusted
  to avoid tripping over it, so it didn't block anything here.
- The "still calculating" message shown for a historical date and the one shown for the everyday/latest
  date use slightly different wording (the historical one now correctly avoids mentioning "the next data
  update," since none is actually involved) — this is the intended fix, not a limitation, but is noted here
  since it's a small, deliberate wording difference an observant user might notice between the two.
