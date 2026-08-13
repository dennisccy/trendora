# goal-ops-hardening-iter-77 — Implementation Summary

**Phase:** goal-ops-hardening-iter-77
**Date:** 2026-08-13
**Written by:** developer (updated after the audit's FAIL verdict and this fix pass)

---

## Features Implemented

- **Staleness disclosure on the readiness badge and preflight banner**: anyone looking at the top-bar
  status badge or the board-status strip can now see how old the status they are reading actually is — a
  short "as of …" note. It appears only when the reading is genuinely stale, and it never shows a number at
  all when the backend cannot be reached (better an absent note than a made-up one). Because the app's
  status refreshes twice a second, the usual case is a fraction of a second, which reads **"as of <1s
  ago"**; longer gaps read "as of 4s ago" and so on.
- **A display bug fixed**: at common window sizes the green "Ready" indicator could be pushed off the
  visible top bar when a background data-processing indicator was also showing. It now wraps onto a second
  line instead of disappearing.
- **A stable test hook on the backtest scorecard**: each per-horizon row of the forward-test scorecard now
  carries a stable identifier so automated checks can point at the real row instead of matching loose text.
  No visible change.

---

## Changed Behavior

- **The app can no longer be silently broken by a routine "check that it still compiles" build.** This is
  the headline change of this fix pass, and the defect it closes is the one that broke this very round.
  Running a plain build command inside the frontend folder used to overwrite the copy of the app that was
  being served at that moment. Two things went wrong when it did: the rebuilt copy did not know which port
  the backend listens on (so every page said "Backend unavailable" even though the backend was perfectly
  healthy), and rewriting files under a running server made the app fall over into a full-page error. Both
  are now refused outright, with a message telling the operator exactly what to run instead (a throwaway
  build folder for verification, or the normal launch script to rebuild what is actually being served).
- **The frontend launch script now checks the app it is about to serve can reach the backend.** On every
  launch it verifies the built copy actually references the backend address it was configured with, and
  rebuilds if it does not. Previously, a copy built for a different backend would be served as "current"
  and every page would show "Backend unavailable" — with nothing anywhere in the logs saying why. If
  another server is already serving that same copy, it warns instead of rebuilding, so it never pulls the
  rug out from under a running server.
- **The frontend launch script coordinates concurrent launches** (from the first pass): if two copies of
  the script run at once against the same build folder, only one builds at a time, so visitors can never be
  served a half-written page.
- **The internal recording tool that captures showcase walkthrough screenshots** waits for the on-screen
  change to actually land before taking the "after" picture, instead of firing on a fixed delay.

---

## Backend-Only Items

None. The staleness value shown in the UI has been computed and served by the backend since an earlier
round (iter-71); this round adds the first screen that shows it to a user. No backend code changed in
either pass of this round.

---

## Incomplete Items

- **A cheap "the demo lane found the whole app broken" alarm** is recommended but not built. During this
  round the automated walkthrough recorded seven consecutive failed steps and a gallery of crash screens
  while every other check reported green — that was the loudest available signal that the product was down,
  and nothing consumed it. Turning it into a hard stop is a change to pipeline policy, so it is written up
  for the owner rather than slipped into a fix.
- **One process finding is left to the review lane**: the round's summary report claimed "no blockers"
  while the merged browser-test artifact it summarises read BLOCKED. That artifact is written by the
  browser-test lane, not by this work; the evidence it needs now exists (all eight user journeys replay
  successfully against the delivered app, with fresh screenshots).

Everything else in this round's plan is complete: the launch-script defect (now with a named, reproduced
cause and four regression tests), the staleness display, the layout fix, the scorecard test hook, the
walkthrough-recorder fix, and all the housekeeping items — including the "golden scripts pending
regeneration" tracking list, which is now empty because all eight journeys were re-confirmed against the
rebuilt app.

---

## Config and Environment Changes

None for operators. No new environment variables, no config-file changes, no database migrations.

Two internal marker files are now written inside the frontend's build folder — one recording which launch
produced the build, one recording which process is currently serving it. They are build artefacts, not
configuration, and are recreated automatically on every launch. Two test-only switches exist
(`TRENDORA_FRONTEND_LOCK_DIR`, `TRENDORA_LAUNCH_BUILD`) and are never set during a normal launch.

**Operator note (worth knowing):** to check the frontend still compiles, run the build against a throwaway
folder — `NEXT_DIST_DIR=.next-verify npx next build` — never a plain `npx next build`, which is now refused
while the live copy exists or is being served. The refusal message repeats this instruction.

---

## Known Limitations

- The "who is serving this build folder" marker records a single server. If two servers are deliberately
  pointed at the same build folder (a configuration only the automated tests use), the second overwrites
  the first's claim.
- The check that the built app references the right backend works by looking for the backend address inside
  the built files, which is how the framework embeds it today. If a future framework change stopped
  embedding it, the launcher would rebuild once per launch — slower, and loudly logged, but never a silent
  breakage.
- The verification the audit could not perform for the previous pass — that the app users see is the app
  the tests measured — is now covered by evidence taken from the delivered tree itself: the app was rebuilt
  through the normal launcher, all eight journeys were replayed against it, and the showcase walkthrough was
  re-recorded end to end with no failures.
