# Phase goal-market-compass-iter-13 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-13 (J-11 Stage C — owner-authorized bounded destructive clear)
**Time required:** N/A — no browser verification exists for this iteration
**Written by:** ui-test-designer

**Status:** No UI verification steps this iteration. Backend-only, maintenance-isolated,
destructive-database iteration with zero application-service boot and zero frontend files
touched (`Frontend Present: no`; TC-16 confirms no file under `apps/frontend/` appears in the
diff).

---

## Why there is nothing to click

This iteration's sole `Target journeys:` entry, **J-11 — Stage C only**, is a bounded backend
`DELETE` against four incident dates' derived rows in the live database (`scanner_runs`,
`scanner_results`, `sector_scores`, `theme_scores`, `forward_returns`), executed once via a
`--confirm`-gated CLI script under maintenance isolation (ruling A5/A13, reaffirmed by C10 — no
backend boot, no frontend boot, no browser, no second server). `docs/goal.md`'s own J-11 entry
states its Walkthrough acceptance item is **"waived — maintenance repair of the derived layer
with no UI surface of its own"**, replaced instead by pre/post inventory, mutation
reconciliation, cache-invalidation proof, and manifest-immutability evidence — none of it
renderable UI state.

This is not a new gap this iteration introduced: this project already applied the identical
exclusion to J-11 itself in `reports/phase-goal-market-compass-iter-11-what-to-click.md`, and to
J-10 in the iter-7 equivalent report.

The phase spec's `Required-still-passing journeys:` line adds that none of the carried journeys
(J-01 through J-10) have "their surfaces or Data-Contract values ... touched by this iteration" —
so there is also no regression-risk UI journey to re-check this iteration.

## If you want to confirm this iteration's actual result (no browser needed)

The evidence lives entirely in the filesystem, not in a running app (which stays off this
iteration):

- `runs/goal-market-compass-iter-13/j11-stage-c-complete.json` — completion marker:
  `"j11_stage_c_complete": true`, `"verdict": {"passed": true, "reason": "all_checks_passed"}`
- `docs/handoffs/goal-market-compass-iter-13-dev.md` — closes with the literal lines
  `## J-11 STAGE C COMPLETE: YES` and `## J-11 STAGE D AUTHORIZED: NO`
- `runs/goal-market-compass-iter-13/j11-stage-c-mutation-accounting.json` — `scanner_runs`: 3,121
  before → 4 deleted → 3,117 after; `all_checks_pass: true`; non-incident population's ID-set
  fingerprint unchanged; `next_session_manifests` 24 rows unchanged; `daily_prices` 3,310,374 rows
  unchanged

This is deliberately **not** phrased as a numbered "Verification Steps" list with exact URLs and
clicks — there is no URL or click involved in checking it, and dressing a file-read as a browser
step would misrepresent what maintenance isolation actually allows this iteration to show.

## When a real "What to Click" guide becomes possible again

Not before J-11 Stage D/E/F/G run and application-service boot is re-authorized (ruling C10:
"successful Stage C is **not** implicit authorization for Stage D ... The owner inspects Stage C
mutation accounting first"). Until then, note for whoever next boots the app: the 11 incident
dates — including the 4 this iteration deleted — now serve zero `scanner_runs` and zero derived
children, so any UI surface asked for one of those as-of dates (e.g. `/?asof=2026-08-11`) will hit
a missing-run path until Stage D regenerates them. That is the intended, owner-authorized
mid-repair state this iteration deliberately left behind — **not** a bug, and not a reason to fail
a future click-through of those dates before Stage D has run.
