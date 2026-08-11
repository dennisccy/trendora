# Iteration State — ops-hardening

**After iteration:** 62 · **Date:** 2026-08-11 · **Verdict:** ESCALATE

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-08 J-09) · 1 partial (J-07) — 8 total. J-08 carried unverified (outside iter-62's required set); J-05 + J-07 keep `evidence_makeup` (walkthrough never recorded).

## Active blockers

- **J-05's golden will FAIL next round (dev, urgent).** `runs/goal-session-ops-hardening/journey-scripts/J-05.json`
  backfills 2010-11-17 and asserts "0 already snapshotted", but iter-62's own replay created that day
  (`scanner_runs` id=2958). Rotate the date; also repoint steps 13-15, which still assert 2010-11-16.
- **Replay lane races the pre-QA restart (dev).** It started 1 min after boot (`logs/backend.log`
  banner 13:24:00Z) and reported false FAILs on J-01/J-04. Make it wait for `data-state="ready"`.
- **J-07's last gap has TWO paths now.** (a) OWNER, 14th round: does the ≤2s `/api/health` ceiling apply
  to a 15-23 min job or only the ~30s window it was written for? (b) DEV: make the 55.20s
  `coverage_membership_timeline_refresh` finalize phase yield — iter-61's single 2.849s poll was inside it.
- **OWNER-gated:** `scripts/automation/browser-qa-phase.sh` line 286-before-272 fix (build-system file),
  plus a cost decision — the replay lane now runs a real 15-minute ingest job every round.

## Last 2 verdicts

- iter 62: ESCALATE — no journey moved; a lean round surfaced three verification-substrate defects no
  lane reported (restart race, self-consuming golden, unsanctioned 15-min replay cost).
- iter 61: CONTINUE — J-05 promoted partial→passing after its only blocker (iter-60/a) proved to be a
  UTC-vs-local clock misreading.

## Do not redo

- `/api/health`'s `last_run_date` is FIXED and verified (`apps/backend/app/api/health.py`, serves
  2026-08-03 = `max(scanner_runs.asof_date)`); TC-1/TC-2 in `apps/backend/tests/test_health.py`.
- `/data`'s ambient refresh no longer wipes good data on a transient failure
  (`apps/frontend/lib/data-overview-refresh.ts` + `app/data/page.tsx`'s two `.catch` sites); test passes
  via `npx tsx`, NOT `node`.
- iter-60/a (stale `/data` coverage counts) is VOID — a clock misreading, not a defect. Do not re-open.
- Target-journey replay routing works on the LEAN path (7 replay rows this round, J-05 + J-07 included);
  it is still dead on the FULL path.
- J-05's product behaviour is machine-verified live (run id=412, 15m04s, 1 snapshot). Do not re-plan it.
- Report-writing defects (headline vs raw file) are lessons, not product code — no fix iteration.
