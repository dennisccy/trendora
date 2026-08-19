# Goal Session market-compass — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-08-19T22:30:56Z

**Verdict:** CONTINUE
**Lesson:** The engine reported "product diff this iteration: non-empty" at a zero-code-change
baseline — the diff was the owner's three `docs/goal.md` authoring commits (b01f90e4, 4c676a73,
21e97a44), not iteration output, because `iter-0/snapshot-sha` was empty and the scanner fell
back to `HEAD~1`. Always confirm attribution with `git diff <base>..HEAD --name-only` before
treating a non-empty diff as work the iteration performed.
**Applies to:** any baseline (iter-0) evaluation, and any iteration whose `snapshot-sha` file is
empty or whose scan-report scope reads "changes since HEAD~1".

## iter-0 — 2026-08-19T22:30:56Z (evidence quality)

**Verdict:** CONTINUE
**Lesson:** Four journeys (J-02, J-03, J-04, J-07) were evidenced by one byte-identical
above-the-fold capture of `/` (md5 `9dfcc1cf…`), which shows the legacy Dashboard but cannot by
itself prove the six missing compass sections; the absence claims only held up because the
results file recorded `document.body.innerText` sweeps and the code check confirmed no compass
module exists. Absence-of-feature claims need a text sweep or a code citation, not just a
screenshot of a page that lacks the feature.
**Applies to:** any iteration scoring journeys as failing because a section/page is missing,
especially baselines where several journeys share one page.
