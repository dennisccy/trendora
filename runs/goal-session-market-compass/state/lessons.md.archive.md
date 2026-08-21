# lessons.md — archive

Entries moved out of `lessons.md` by scripts/automation/lib/condense.sh (maintenance protocol §4).
Append-only: nothing here is ever deleted or rewritten.

<!-- condense.sh 2026-08-21T11:39:28Z: moved 5 entries (keep-iters=5) -->

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

## iter-1 — 2026-08-20T05:04:26Z

**Verdict:** CONTINUE
**Lesson:** Browser QA tested a STALE backend: the dev/audit code was on disk but the running
uvicorn process (:8255) predated it, so UT-07/UT-J-01 reported `sector_basis` "absent from
`GET /api/methodology`" when the same call returns it correctly once the process is restarted
(verified by the evaluator post-run). A whole P1 journey step was scored "not observable" against a
process, not against the product.
**Applies to:** any iteration whose deliverable is a new API field or new served payload key —
restart backend + frontend after the dev/audit steps and BEFORE browser-qa, and treat "key absent
from the API" as an environment hypothesis until the process start time is checked.

## iter-1 — 2026-08-20T05:04:26Z

**Verdict:** CONTINUE
**Lesson:** A test that `pytest.skip()`s in the only environment that exists is not coverage. TC-5's
API test guarded itself on the same `data/seed/universe.json` gate that was hiding the feature, so a
green "22 passed, 1 skipped" run concealed an undelivered, user-invisible deliverable
(`apps/backend/app/engine/methodology.py` emitted `sector_basis` inside the section the J-22 gate
pops). The audit caught it only by fetching the live endpoint.
**Applies to:** any iteration adding content behind an existing feature gate — assert the new value
at the layer the spec words its acceptance against (the served response), and never let the
acceptance test skip on the gate it is meant to prove independence from.

## iter-1 — 2026-08-20T05:04:26Z

**Verdict:** CONTINUE
**Lesson:** J-01's own written precondition ("Remove the last two trading days, then backfill the
same range") is destructive in this environment: 2026-08-13/14 were user-added bars with no
committed seed beneath them (`seed_latest_date` = 2026-08-12), so the Remove permanently destroyed
1,174 bars / 18 snapshots / 30,439 forward returns and the offline bars-only Backfill correctly
refused to fabricate them back. The fresh run the journey needed appeared anyway — the backend's own
boot created run 3081 for 2026-08-12 from seed bars.
**Applies to:** any journey step that instructs a data Remove — check `seed_latest_date` covers the
range first, and prefer the backend's own boot/persist path over a destructive remove+rebuild cycle
to obtain a fresh run.

