# Iteration State — market-compass

**After iteration:** 27 · **Date:** 2026-08-28 · **Verdict:** CONTINUE

## Journeys

6 passing (J-01 J-04 J-05 J-06 J-10 J-11) · 3 partial (J-02 J-03 J-09) · 2 failing (J-07 J-08) — 11 total

## Active blockers

- **None dev-blocking.** J-06 closed; J-07 "The Today page answers the ten-second read" is next, then
  J-08 — ordinary work authorised by owner ruling item 5.
- **Process (put it in the next plan):** the browser-QA lane exceeded this iteration's "read-only and
  additive-free" live constraint and permanently minted `next_session_manifests` row id 26
  (`as_of=2019-03-01`). Benign, but the plan must list the ONLY dates that lane may visit live, and
  row-count claims must be re-derived after it finishes. **True count is 26, not 25.**
- **J-06 residuals, not blocking:** "unavailable" is proven at route level on a fixture DB, never through a
  real `remove_data()`; removing a FRONTIER manifest's price range makes it unreadable (400 `future`, B3).
- Non-blocking owner questions: J-09 2.99 GB · J-06 wording · J-01 test steps · empty focus · MNST.

## Last 2 verdicts

- iter 27: CONTINUE — J-06 promoted; route now serves an existing manifest before any self-heal, so
  "Basis: unavailable" is honestly reachable (97 tests pass; HEAD-vs-worktree flip confirmed by evaluator).
- iter 26: ESCALATE — J-05 promoted; J-06's remaining gap sat in the shared serving path and needed the
  independent auditor that the lean demotion had removed.

## Do not redo

- **J-06 is done** — route reorder (`app/api/compass.py` fast path + `latest_manifest_for_date`), flipped
  route-level test, restore/warm-path tests, and the auditor's TC-5/TC-9 tests all landed; 97 pass.
- **J-11 is CLOSED** (owner ruling item 1) and **J-05 is done** (iter-26 live evidence; step 2 fixture-only,
  permanently unprovable here — assumptions.md). Only walkthroughs are owed.
- **Do NOT run the live remove+backfill drill** for J-05 step 1 / J-06 steps 1-3: "the last two trading
  days" still resolves to 2026-08-11/12, the incident pair; AG-9 exception exhausted. Fixtures cover it.
- **Do NOT delete manifest row id 26** (2019-03-01) or any manifest row — AG-12 forbids it; the record was
  corrected in the dev handoff instead.
- **Launcher fix verified** (iter-24); canonical DB boot is sanctioned work; the iter-23 clone
  (`runs/goal-market-compass-iter-23/verify-clone/`, 7.8 GB) may now be deleted.
- Passenger tasks only, never an iteration goal: J-04's screenshot re-take (9th owed), J-05/J-06 walkthroughs.
