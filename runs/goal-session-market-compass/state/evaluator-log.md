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

## Iteration 2 — goal-market-compass-iter-2

**Date:** 2026-08-20T09:05:00Z
**Verdict:** ESCALATE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: J-02, J-03, J-04 (all three with `evidence_makeup: true` — walkthrough not recorded)
- Promoted partial → passing: J-01 (screenshot now exists; `evidence_makeup: true` for the walkthrough)
- Newly failing: none
- Regressed: none
- Not re-tested (carried, out of scope): J-05, J-06, J-07, J-08 — all still failing
- Anti-goal violations: none critical. One MINOR wording note (AG-2): the ATR caution ends
  "— sized risk accordingly", which reads as advice; and the automatic banned-word check only
  scans the summary sentences, not the candidate reason and caution lines.

**Reasoning:** This iteration built the heart of the Today page and it works. The home page now
shows a plain-English summary, a "what changed since the previous session" list, and a
"next-session focus" section. I did not take this from the reports. I opened all four pictures
myself. The best proof is inside the pictures: the summary says the market score is 73.24 and the
severity is 25.84, and the older, separate tiles further down the SAME page show 73.24 and 25.84
too — so the new text is quoting the same numbers the rest of the site already served. The same
check passes on the 23 July page (57.9 and 36.6 in the text, 57.87 and 36.61 in the tiles). The
"what changed" card correctly names the previous session and the one-day gap, and the candidate
card for GWW shows why it was chosen, what would change that, and twenty names that were not
chosen with the exact distance each one missed by. The sector work from last iteration is now
picture-backed too, so J-01 is finished apart from its recording. Nothing broke: no journey that
was working stopped working, the structure check passed, and the security scan was clean. So why
ESCALATE and not CONTINUE? Because the engine ran this iteration in the light "lean" mode even
though its own plan asked for the full mode. That means three safety lanes never ran — the
independent auditor (which caught a real hidden-feature bug only one iteration ago), the
visual-regression check, and the walkthrough recorder that four journeys need for their evidence.
On top of that the developer raised a real product question the missing lanes were meant to
settle: on today's date not a single stock passes all three selection rules, so the headline
section is honestly empty.

**Next-step recommendation:** Run the next iteration in FULL mode and build J-05 "Each close
freezes one next-session manifest" together with J-06 "A frozen manifest never changes". These
two lock the daily briefing into a sealed, dated, tamper-evident file that can never change
afterwards, which is the riskiest part of the whole plan and needs the auditor watching. Carry
three small jobs along with it, none of them big enough to deserve their own turn: record the
missing walkthroughs for J-01 to J-04, take one picture of the "Risk-off" warning state, and
reword the ATR caution so it stops sounding like advice. Two things need the owner, not the
robot: please approve rewording J-01's first test step (it currently tells the tester to delete
and rebuild two days of data, which cannot be undone offline) and its second step (it asks the
tester to pick an "Unassigned" filter option that no longer exists now that every stock has a
sector); and please say whether the empty "next-session focus" on the newest date is acceptable
as an honest result, or whether the three cut-off numbers should be revisited — noting that the
rules forbid changing them just because past prices would have looked better.
