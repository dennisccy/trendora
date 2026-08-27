# Iteration State — market-compass

**After iteration:** 20 · **Date:** 2026-08-27 · **Verdict:** CONTINUE

## Journeys

3 passing (J-01 J-04 J-10) · 6 partial (J-02 J-03 J-05 J-06 J-09 J-11) · 2 failing (J-07 J-08) — 11 total. Iter-20 ran
under maintenance isolation (browser QA + replay forbidden by contract): ALL statuses carried, none re-verified, none promotable. J-04 keeps `evidence_makeup: true` (capture defect only).

## Active blockers

- **Live write paths reachable from any page request (human-deferred, `docs/goal.md` ruling item 5).** `scanner.py:338-348`
  creates a day-record for any `?as_of=` with NO quarantine check (zero boundary refs in that file — verified);
  `compass.py:1041-1060` mints a saved briefing for any non-newest date, and 7 of the 11 incident dates have none while
  2026-08-12 is now the frontier. KEEP BACKEND + FRONTEND + BROWSER QA OFF through Stage G; do NOT patch these.
- **Normal Market Compass work (J-01..J-09, esp. J-07/J-08) blocked until Stage G passes** (item 12).
- Binding launch conditions for D→G (item 13): `CHAIN_MAINTENANCE_ISOLATION=true` + `CHAIN_REQUIRE_FULL_DEPTH=true`.
  Depth MUST be `full`; `lean` is not equivalent.

## Last 2 verdicts

- iter 20: CONTINUE — J-11 Stage E executed live and cleanly (+16,592 forward returns on the 11 rebuilt runs; nothing
  outside `forward_returns` moved). Stage F is already authorized by ruling item 8, so no human action gates the next step.
- iter 19: CONTINUE — J-11 Stage D executed live and cleanly (11 runs, ids 3148-3158, one frozen identity).

## Do not redo

- **Stage D — DONE, verified live.** Runs 3148-3158 on the 11 `INCIDENT_DATES`, created 2026-08-26
  10:52:55.552946-10:53:02.010362, all stamped `53d2ffd1…`. Re-verify read-only; never re-run.
- **Stage E — DONE, verified live (iter-20).** `forward_returns` 6,797,728 → 6,814,320, ids 6,844,114-6,860,705, per-run
  2771/2769/2216/2215/1659/1658/1103/1103/549/549/0; idempotent — never "resume from the next unfinished run".
  Evidence: `runs/goal-market-compass-iter-20/j11-stage-e-execute-*.json`.
- **Population (b) = 0 is CORRECT, not a missing repair** — retained-run holes are structurally impossible
  (`data_manager.py:1967-2011` + `:2173-2177` delete an affected run's rows whole), so step 5's "holes exist on retained
  runs" is a mistaken premise; Stage G accepts zero without weakening its gate.
- **Boundary + live pre-boot guard — ACTIVE/ARMED, verified.** `j11-incident-recovery`, `active=1`, exactly the 11 dates,
  unchanged since 2026-08-25. Never re-arm, re-create or deactivate before Stage G.
- **Carry into the Stage G spec (audit B1/B2/B5):** preflight must compare `created_at` AND assert one run per incident
  date; needs a content-level instrument for `scanner_results`/`sector_scores`/`theme_scores`/`data_provider_runs`/`watchlist`; must record why 16,566 deleted became 16,592 restored (+26).
