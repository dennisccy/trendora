## Iteration 0 — goal-market-compass-iter-0

**Date:** 2026-08-19T22:30:56Z
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: none
- Newly failing: J-02, J-03, J-04, J-05, J-06, J-07, J-08 (first measurement — baseline, not a break)
- Newly partial: J-01 (first measurement)
- Regressed: none
- Anti-goal violations: none

**Reasoning:** This was a baseline check with no code changes, so nothing could break and nothing
could be fixed. The browser run measured all eight journeys against the running app and found the
Today compass simply does not exist yet: the `/api/compass` address returns "not found", the
`/market` page shows a 404, and the home page is still the old Dashboard. I checked the code
myself and confirmed the same thing, so I am not relying on the reports alone. J-01 "Sector
labels are honest and nearly complete" is the one journey that is partly there — the labels that
do exist are consistent everywhere and unknown names honestly say "Unassigned" — but 78 stocks in
every 100 are still unlabelled, against a target of 5. The only files changed since the last
release are documents, so no anti-goal could have been broken.

**Next-step recommendation:** Build J-01 "Sector labels are honest and nearly complete" next:
fill the missing sector labels from the pool spreadsheet, explain the two-source basis on the
Methodology page, keep unknown names as "Unassigned", and prove the stock scores did not move.
Run that iteration at full depth, because it is the first change the owner will see on screen.

## Iteration 1 — goal-market-compass-iter-1

**Date:** 2026-08-20T05:03:59Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: none
- Newly failing: none
- Regressed: none
- Still partial (advanced, capture gap): J-01 — behavior verified, screenshots/walkthrough missing (`evidence_makeup: true`)
- Re-tested, unchanged (not a regression): J-08 (/market still 404, explicitly out of scope)
- Anti-goal violations: none (scan-report CLEAN; AG-1..AG-16 each answered in eval.md)

**Reasoning:** The sector work really landed. On the fresh run dated 2026-08-12 every one of the 539
stocks now shows a real sector and none say "Unassigned", down from about 78 in every 100, and the
Methodology page now explains that labels come from the curated list first and the candidate-pool
file second and describe today only. I did not take this from the reports: I read the running app
myself and got 0 of 539 blank, DELL as "Technology" and GRMN as "Consumer Discretionary", and I
opened the screenshot that shows the new Methodology card. So why is J-01 not finished? Only the
picture evidence. The browser test lane ran against a stale copy of the app and its first step
deleted two days of data it could not put back, so it never reached the stock list; the walkthrough
recorder also produced nothing because of a file-reading error. Under our rule that a journey cannot
be called passing without a screenshot of the thing it claims, J-01 stays part-done. The reviewer
passed with notes, the auditor found the disclosure was shipped hidden and fixed it during the audit,
and the coherence check passed, so nothing is structurally wrong.

**Next-step recommendation:** Build the next three journeys together — J-02 "What changed since the
previous session", J-03 "Plain-English summary with cited facts" and J-04 "Each next-session
candidate explains why and why-not" — at full depth, because they share one producer and put new
cards on the home page for the first time. Carry J-01's missing screenshots and its walkthrough
along as a side task, not as an iteration of its own. One thing needs the owner: J-01's written test
steps tell the tester to delete and rebuild the last two trading days, which in this setup destroys
data that cannot be rebuilt offline — please approve rewording that step before J-01 is re-tested.
