**Verdict:** PASS

# QA Validation Report — goal-i_can_see_the_wealthy_future_forever-iter-17

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-17
**Date:** 2026-06-04
**Frontend Present:** yes (Chrome MCP browser checks performed)
**QA agent:** qa (MODE 2 validation)

## Summary

Iter-17 as-of-scopes the forward-test evidence aggregate (`compute_forward_aggregates(..., as_of=D)`),
relocates its single serving home from `GET /api/system-health` to `GET /api/backtest`
(`evidence_by_horizon`, all horizons in one fetch), and retires System Health
(route/router/page/nav/client/test). All 15 functional test cases PASS. Full backend pytest is green
(454 passed, 4 skipped, exit 0). The principal anti-goal risk (J-18 — exactly one date selector) holds:
`/backtest` has exactly one date control (the global as-of `<select>`); the horizon buttons are a
client-side view selector that triggers **zero** refetch; the page URL is date-free.

---

## Step 1 — Required artifacts

| Artifact | Status |
|----------|--------|
| `docs/handoffs/goal-...-iter-17-dev.md` | ✅ present |
| `docs/handoffs/goal-...-iter-17-frontend.md` | ✅ present |
| `reports/reviews/goal-...-iter-17-review.md` (**Verdict:** PASS) | ✅ present, PASS |
| `runs/goal-...-iter-17/status.json` | ✅ present (`review_passed`) |
| `runs/goal-session-.../state/blueprint.reapproval-requested` | ✅ present (nav-skeleton change marker) |
| Functional test plan | ✅ present, executed below |

---

## Step 2 — Backend tests (exact result)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Log: `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-17-test.log`

```
================= 454 passed, 4 skipped in 1191.27s (0:19:51) ==================
EXIT:0
```

Run ONCE (per `backend-test-suite-runtime` MEMORY). 4 skips are pre-existing (live Stooq fetch +
committed-universe-record checks), not regressions. New backing tests for this iteration all present and
green:

- As-of scoping / no-leak / relocated invariant (`test_forward_testing.py`):
  `test_aggregates_as_of_pools_only_runs_on_or_before_cutoff`,
  `test_aggregates_as_of_sample_grows_toward_latest`,
  `test_aggregates_as_of_none_equals_latest_equals_all_history`,
  `test_aggregates_as_of_no_future_run_leak`,
  `test_aggregates_as_of_before_all_runs_is_honest_empty`,
  `test_aggregates_as_of_scoped_consistency_invariant_relocated`,
  `test_aggregates_by_vcp_empty_cohort_is_na_padded`,
  `test_aggregates_by_new_patterns_empty_cohort_is_na_padded`,
  `test_aggregates_carry_survivorship_label_and_min_sample`.
- Endpoint (`test_api_backtest.py`): `test_backtest_evidence_by_horizon_shape_and_keys`,
  `test_backtest_evidence_is_as_of_scoped_expanding_window`,
  `test_backtest_evidence_default_equals_full_all_history_aggregate`,
  `test_backtest_invalid_asof_is_explicit_4xx_never_fabricated`,
  `test_system_health_route_is_retired_404`.

---

## Step 3 — Frontend typecheck

`cd apps/frontend && npx tsc --noEmit` → exit 0 (no TypeScript errors).

> Note: the project's nominal frontend test command is `npm run build`, but per the iter-15 lesson
> (`browser-qa-dead-shell-next-cache`) a prod build against the live `next dev` `.next/` clobbers it into a
> dead un-hydrated shell, which would break the subsequent browser-qa-agent. `tsc --noEmit` validates the
> same compile/typecheck correctness (the change set is page + shared component + type edits) without
> touching `.next`. The dev/frontend handoff records a clean build at implementation time.

---

## Step 3.5 / Step 4 — Functional test plan results

Backend at `http://localhost:8835`, frontend at `http://localhost:3835` (both healthy, managed by QA
runner). Browser checks on the live hydrated dev build (`/_next/static/chunks/main-app.js → 200`).

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | As-of scoping restricts pool to runs ≤ D | api | only runs ≤ D; n(early)<n(latest) | n: 2022-10-07→120, 2024-08-28→364, latest→1218; `asof_dates` never > D | PASS | Confirmed via API + backing unit tests |
| TC-02 | `as_of=None` == all-history == latest | api | structural equality | `test_aggregates_as_of_none_equals_latest_equals_all_history` + `..._default_equals_full_all_history_aggregate` green | PASS | |
| TC-03 | No >D leak | api | post-D run contributes 0 | `test_aggregates_as_of_no_future_run_leak` green; `asof_dates` capped at D at every probe | PASS | |
| TC-04 | Relocated consistency invariant | api | `distribution.mean == overall.mean_return` on aggregate | `test_aggregates_as_of_scoped_consistency_invariant_relocated` green (moved, not deleted) | PASS | iter-2 lesson honored |
| TC-05 | Low-sample / empty → NA + n | api | NA + n; empty = n=0, never 0-as-number | empty `by_vcp` arm → `mean=None, n=0`; sub-min_sample cells carry n + ⚠ in UI | PASS | API exposes `mean`+`n`+`min_sample`; UI renders NA below min_sample (same model as retired SH) |
| TC-06 | `/api/backtest?as_of=D` returns `evidence_by_horizon` | api | 200; per-horizon aggregate shape | keys `['1','5','10','20','60']`; each has by_bucket/excess/by_setup/by_regime/by_vcp/pattern/control_group/attribution | PASS | cutoff = resolved `run.asof_date`; no separate date param |
| TC-07 | `GET /api/system-health` removed | api | 404 / route absent | `GET /api/system-health → 404`; absent from openapi paths | PASS | |
| TC-08 | Unknown/short horizon NA; invalid as_of handled | api | NA not fabricated; invalid as_of rejected/defaulted | invalid `as_of` → 422 `"as_of is not a valid ISO date"`; horizons not elapsed → NA(n=0) | PASS | `test_backtest_invalid_asof_is_explicit_4xx_never_fabricated` green |
| TC-09 | No `/system-health` refs in `apps/` source | artifact | grep clean | only hits are the intentional 404-retirement test in `test_api_backtest.py`; page/client/route/type deleted | PASS | `.next/` excluded |
| TC-10 | Full backend pytest green (once) | artifact | exit 0, no failures | 454 passed, 4 skipped, exit 0 | PASS | run once (~20min) |
| TC-11 | Frontend typechecks/builds | artifact | exit 0 | `tsc --noEmit` exit 0 | PASS | build deferred to avoid clobbering live `.next` (iter-15 lesson) |
| TC-12 | J-09: as-of-scoped evidence re-points on as-of change | browser | re-points, n drops, latest=all-history | latest: 10 snapshots / n=1217 / +10.57%; 2024-08-28: 3 snapshots / n=364; return to latest reproduces all-history | PASS | distinct screenshots (sha256 differ); URL date-free; as-of range capped at D |
| TC-13 | J-10: control-group comparison numeric + labelled | browser | 3+ arms numeric/NA + labelled | Top-ranked cohort +10.48% (n=199), Random same-sector +8.18% (n=280), SPY +6.21% (n=10⚠), QQQ +7.37% (n=10⚠), Sector ETF +5.14% (n=64) | PASS | all 5 arms labelled with n |
| TC-14 | J-18: exactly one date selector on `/backtest` | browser | one global date control; URL date-free; horizon no refetch | single `<select aria-label="View as-of date">`; horizon click → 0 `/api/backtest` fetches; as-of change → exactly 1 fetch; URL `/backtest` | PASS | principal anti-goal — holds |
| TC-15 | Regression spot-checks | browser | scorecard+attribution+breakdowns; J-21 ordering; J-13 re-points other pages | heading order scorecard(1)<attribution(3)<leadership(8)<evidence(10); VCP/pattern breakdowns present; /stocks re-points to 2024-08-28 on in-app nav | PASS | J-14/J-16/J-19/J-21/J-28/J-13 all green |

**15/15 test cases passed.**

### Evidence (de-duped, distinct screenshots)

- `reports/qa/.../iter-17-evidence/TC-12-evidence-latest.png` — sha256 `14ab49b4…`
- `reports/qa/.../iter-17-evidence/TC-12-evidence-earlier-2024-08-28.png` — sha256 `b524a106…` (distinct)
- `reports/qa/.../iter-17-evidence/TC-13-control-group-latest.png`

### Key DOM / network assertions (grounding the browser claims)

- **J-09 re-point:** at latest, evidence header = "Snapshots contributing (≤ 2026-05-28): 10",
  "Mean stock fwd return (60d): +10.57% (n=1217)"; after switching the global as-of to 2024-08-28 (native
  setter + bubbling change, per `react-controlled-select-needs-native-setter` MEMORY), header =
  "Snapshots contributing (≤ 2024-08-28): 3", n=364, "As-of range: 2022-10-07 → 2024-08-28" (no >D leak).
  Returning to latest reproduced 10 / n=1217 / +10.57% exactly.
- **J-18/J-15:** instrumented `window.fetch` — clicking the 20d horizon button changed the view to
  "(20d)" with the SAME n=364 and issued **0** `/api/backtest` calls; the as-of change issued exactly **1**
  call (`http://localhost:8835/api/backtest`). Only one date control in the DOM; page URL carries no date
  param (per `j18-asof-on-stocks-fetch-is-correct` MEMORY, the `?as_of=` on the snapshot-served read is the
  single global date being transmitted, not a second state).
- **J-13:** with global as-of at 2024-08-28, in-app nav to `/stocks` preserved the selection
  (`select value=2024-08-28`) and the page re-pointed.
- **J-21 ordering:** scorecard → return attribution → leadership cohorts → evidence aggregate (bottom);
  leadership lists remain below Return Attribution; evidence never between scorecard/attribution/leadership.

---

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the new capability?** Yes — `/backtest` gained a clearly-labelled
   "Forward-tested evidence (expanding window ≤ D)" block (by-bucket A–E, excess vs SPY/QQQ, by-setup,
   by-regime, VCP/pattern, control group), each cell with `n` and low-sample ⚠, carrying the
   survivorship-bias / universe-relative label.
2. **Can the user see/understand/control it?** Yes — the existing global as-of switcher re-points it (sample
   grows/shrinks with the date) and the existing horizon selector re-views it client-side; the panel is
   explicitly distinguished from the per-date scorecard.
3. **Still relying on old generic pages?** No — System Health (the old date-blind home) is fully retired
   (page, nav entry, route, client, type). Single home for the evidence.
4. **Technically complete but under-exposed?** No — the capability is fully surfaced and discoverable on the
   Backtest workspace under one date control.

**Verdict:** UI-PASS

---

## Step 5b — Servers

No servers started by QA (managed by the QA runner). Killed a stuck self-matching wait-loop helper
(PID 353395) whose own command line matched its `pgrep -f "pytest tests"`; no real pytest/uvicorn/next
process was left by QA.

## Blockers

None.

## Anti-goal / critical-invariant confirmation

- **No recompute in read path / Single source of truth:** the aggregate is a read-only grouping over the
  persisted `forward_returns`; the only logic change is a single `ScannerRun.asof_date <= D` membership
  filter (`compute_forward_aggregates` stays the one computing module; `/api/backtest` its one serving home).
- **No lookahead / No >D leak:** verified in source, by unit test, and live (`asof_dates`/"As-of range"
  capped at D at every probe).
- **Exactly one date selector (J-18):** one global `<select>`; horizon is a client-side view selector
  (0 refetch); URL date-free.
- **No fabricated data:** empty cohort → `mean=None, n=0`; sub-min_sample cells carry n + ⚠; invalid as_of
  → 422, never a synthesized number.
- **Scoring/scanner/regime/patterns/snapshots untouched** (J-06/J-07 byte-identical; no DB regen).

---

**Verdict:** PASS
