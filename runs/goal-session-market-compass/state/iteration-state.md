# Iteration State — market-compass

**After iteration:** 25 · **Date:** 2026-08-28 · **Verdict:** CONTINUE

## Journeys

4 passing (J-01 J-04 J-10 J-11) · 5 partial (J-02 J-03 J-05 J-06 J-09) · 2 failing (J-07 J-08) — 11 total

## Active blockers

- none blocking. One OPEN OWNER QUESTION, non-blocking (ruling item 6): is ~2.99 GB acceptable for J-09?
  Measured 3,064,772 kB vs the 2,621,440 kB target — an honest miss, and the figure is UNCORROBORATED (no
  raw sample survives; 3 neighbouring claims disproved in-audit). Addendum 41 + its correction block.
- Depth risk (owner-owned): 5 times this session a `Depth: full` plan was auto-demoted to lean on cost.
  Only the owner may add `Depth enforcement: required` — planner and evaluator may not self-grant it.
  `CHAIN_REQUIRE_FULL_DEPTH` / `CHAIN_MAINTENANCE_ISOLATION` stay OFF.

## Last 2 verdicts

- iter 25: CONTINUE — full depth ran as specified; the replay lane genuinely re-tested J-01/J-04/J-10
  (3/3 PASS, screenshots opened); J-09 re-measured and honestly missed; the auditor fixed a mirror-image
  parser defect 4 lanes passed over; the sanctioned canonical boot moved no manifest/day-record/price.
- iter 24: ESCALATE — the launcher fix landed and was verified, but the iteration's own regression
  re-test silently never ran and no lane reported it.

## Do not redo

- **J-11 is CLOSED** (owner ruling item 1). Do not reopen its recovery or serving verification.
- **The launcher-context fix is landed and verified** (iter-24; `test-backend-launch-context.sh` 18/18,
  green again this iteration with the clone absent). Owner ruling item 3 is spent.
- **The replay-lane parser defect is fixed AND audit-hardened** — `lib/replay-lane.sh:86-112` treats the
  label's own bullet as authoritative. Verified independently: iter-25/iter-24 specs parse to
  `J-01 J-04 J-10`, iter-7's "none" bullet parses to empty; `test-replay-lane.sh` 84/84. Do not re-patch.
- **The iter-23 disposable clone is deleted** (~7.8 GB freed, owner ruling item 4). **J-09's one
  authorized config edit landed at iter-4** (`cache_size -65536`) — never touch
  `pool_size`/`max_overflow`/`memory_cap_mb`/host-guard values, and never widen the 2.5 GB target.
- **Normal product work is authorized** (owner ruling item 5) — a read-only canonical boot needs no
  further permission and item 6 forbids stalling for recomputable cache residue. Next: J-05 + J-06
  (freeze/integrity pair), then J-07/J-08. Passengers only: J-04's candidate-card re-capture; J-01's
  weak golden script.
