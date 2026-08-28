# Iteration State — market-compass

**After iteration:** 26 · **Date:** 2026-08-28 · **Verdict:** ESCALATE

## Journeys

5 passing (J-01 J-04 J-05 J-10 J-11) · 4 partial (J-02 J-03 J-06 J-09) · 2 failing (J-07 J-08) — 11 total

## Active blockers

- **J-06 last unmet limb (dev-owned, next target):** the live route can never disclose that a frozen
  manifest's source run is gone. `apps/backend/app/api/compass.py:59` calls `resolved_run()` before
  `basis_disclosure()`, and `run_scan`'s self-heal recreates the missing `ScannerRun` first — so a request
  only ever sees `available`/`rebuilt` and has recomputed, which J-06 step 2 forbids; the same machinery
  can mint permanent rows from a plain page view. (iter-3 audit B2, re-verified iter-26.)
- **Depth demotion (human-owned):** spec asked `Depth: full`, engine dispatched `lean` — 6th time this
  session. Only the owner may add `Depth enforcement: required`; `CHAIN_REQUIRE_FULL_DEPTH` /
  `CHAIN_MAINTENANCE_ISOLATION` stay OFF.
- Non-blocking owner questions: J-09 2.99 GB · J-06 wording · J-01 test steps · empty focus · MNST.

## Last 2 verdicts

- iter 26: ESCALATE — J-05 promoted to passing on live+route-fixture evidence; J-06's remaining gap sits in
  the shared serving path (`resolved_run`) and needs the auditor that the lean demotion removed.
- iter 25: CONTINUE — replay lane repaired and ran 3/3; J-09 re-measured as an honest, uncorroborated miss.

## Do not redo

- **J-11 is CLOSED** (owner ruling 2026-08-27 item 1). Never reopen recovery or serving verification.
- **Do NOT run the live remove+backfill drill** for J-05 step 1 / J-06 steps 1-3: "the last two trading
  days" still resolves to 2026-08-11/12, the incident pair, AG-9 exception exhausted. Fixtures cover it.
- **J-05 is done** — export byte-equality, strip figures, disposition partition and `engine_identity`
  stamping re-derived live at iter-26; step 2's flagship state is fixture-only and permanently unprovable
  here (assumptions.md). Only the walkthrough is owed.
- **Launcher fix landed and verified** (iter-24). The canonical DB boot is sanctioned ordinary work
  (owner item 5); do not re-arm maintenance isolation.
- **TC-15 AST scanner fixed** (`test_manifest_invariants.py`); the four orphaned export files were
  investigated and must NOT be deleted (TC-10 finding: leftover test-fixture artifacts).
- Passenger tasks only, never an iteration goal: J-04's screenshot re-take (8th owed), J-05/J-06
  walkthrough recordings.
