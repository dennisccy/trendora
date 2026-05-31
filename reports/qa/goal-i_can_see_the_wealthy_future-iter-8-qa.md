# goal-i_can_see_the_wealthy_future-iter-8 QA Report

**Verdict:** PASS

**Phase:** goal-i_can_see_the_wealthy_future-iter-8
**Date:** 2026-05-31
**Agent:** qa (MODE 2 — validation)
**Frontend Present:** yes

## Summary

Snapshot-served reads (J-15) + global as-of date switcher (J-13) validated end-to-end.
The five primary read endpoints (`/api/dashboard`, `/api/stocks`, `/api/stocks/{ticker}`,
`/api/sectors`, `/api/themes`) now serve canonical values from the persisted immutable
snapshot for a resolved as-of date, echo the resolved `asof_date`, reject bad dates with an
explicit 4xx, and never recompute per request. The frontend top-bar switcher time-travels every
primary page with a clear "Viewing as-of D (historical)" indicator and restores the latest view.
**Full backend suite: 196 passed / 0 failed (exit 0).** All 13 functional test cases PASS.

**13/13 test cases passed.**

## Service / Environment Note

The QA runner reported the backend "did NOT become healthy after retries." Root cause: the
runner probed `GET /health`, but Trendora's health route is `GET /api/health` (per
`.claude/project-template.md` and `app/api/health.py`). The 404s were path mismatches, not a
real outage; the backend then exited. Per the phase spec NOTES (a 7-iteration standing harness
gap), I booted services directly for validation:

- Backend: `uvicorn main:app --port 8835` with `CORS_ORIGINS=http://localhost:3835,http://localhost:3000`.
  Became healthy in 1s; `GET /api/health` → 200 `{"status":"ok","db_ok":true,"provider":"seed",...}`.
- Frontend: `npx next dev -p 3835` with `NEXT_PUBLIC_API_URL=http://localhost:8835`. (The
  runner-managed dev frontend died mid-test; restarted with the correct API URL.)
- Both services were killed by port after testing (verified down: :8835 → 000, :3835 → 000).

No CORS errors observed in the browser console during testing (iter-7 root cause guarded).

## Artifact Verification

| Artifact | Status |
|----------|--------|
| `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-8-dev.md` | EXISTS |
| `reports/reviews/goal-i_can_see_the_wealthy_future-iter-8-review.md` (PASS_WITH_NOTES) | EXISTS |
| `runs/goal-i_can_see_the_wealthy_future-iter-8/status.json` | EXISTS |
| `reports/qa/goal-i_can_see_the_wealthy_future-iter-8-test-plan.md` | EXISTS (executed) |

## Backend Test Results (TC-10)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Log: `reports/qa/goal-i_can_see_the_wealthy_future-iter-8-test.log`

```
======================= 196 passed in 928.58s (0:15:28) ========================
```

- **196 passed, 0 failed, 0 errors** (exit code 0). Baseline was 179+ at iter-7 → ≥179 satisfied.
- Critical guard tests (verbatim from log):
  - `test_asof_resolver.py::test_resolve_run_create_once_then_immutable PASSED` (TC-07)
  - `test_scanner.py::test_run_scan_idempotent_and_immutable PASSED` (TC-07)
  - `test_asof_resolver.py::test_resolve_run_on_demand_has_no_lookahead PASSED` (TC-08)
  - `test_bars.py::test_bars_ascending_all_dates_le_asof_no_lookahead PASSED` (TC-08)
  - `test_scanner.py::test_run_scan_no_lookahead PASSED` (TC-08)
  - `test_api_engine.py::test_repointed_handlers_serve_persisted_date_without_recompute PASSED` (TC-09)
  - `test_scanner.py::test_risk_off_run_has_zero_actionable PASSED` (J-07)
  - `test_scanner.py::test_latest_run_faithful_to_live_computation PASSED` (iter-5 faithful-equality holds)

Note (matches reviewer NOTE): the new resolver suite `tests/test_asof_resolver.py` contains
**10** tests (all passed), not the 12 stated in the dev handoff. Harmless count discrepancy; no
code impact.

## Frontend Test Results

`npm run build` not re-run here (review confirmed it compiles + typechecks 10 routes, 0 errors;
dev handoff confirms the same). Frontend behaviour validated live via Chrome MCP below.

## Functional Test Plan Results

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | Default resolution serves latest + echoes asof_date | api | All four 200; `asof_date`=latest; stocks rows non-empty | `/stocks`,`/dashboard`,`/sectors`,`/themes` all 200; `asof_date=2026-05-28` on all; 122 rows | **PASS** | Latest run echoed on every endpoint |
| TC-02 | As-of re-points to past stored date | api | `asof_date==D_OLD`; ≥1 canonical value differs from latest | All four echo `2025-04-04`; dashboard regime latest=Risk-on 74.32 vs D_OLD=Risk-off 6.3 | **PASS** | Genuine re-point, not latest fallback |
| TC-03 | Invalid as-of → explicit 4xx, no fabrication | api | future→4xx, unparseable→4xx, before-history→4xx; no new run | future→400, unparseable→422, before-history→400; runs count 11→11 unchanged | **PASS** | No fabricated snapshot |
| TC-04 | List↔detail coherence (J-06, byte-identical) | api | NVDA 3 scores+buckets identical list vs detail at latest AND D_OLD | leadership/entry_quality/risk byte-identical (JSON-equal) at both dates; setup identical | **PASS** | Same stored row both views |
| TC-05 | Watchlist coherence with latest stocks row (J-11) | api | Watchlist current values == `/api/stocks` latest | ANET leadership 46.61/entry 57.69/risk 39.62 + buckets + setup all equal `/api/stocks` | **PASS** | Single stored source |
| TC-06 | Bars honors as_of with no lookahead | api | max bar ≤ D; MA bounded; bad dates 4xx | `as_of=2025-04-04`: 1069 bars, max date 2025-04-04; MA arrays parallel to bars (bounded by D); future→400, unparseable→422 | **PASS** | No future-dated bar |
| TC-07 | Create-once / immutability | artifact | Named tests assert INSERT-once + no UPDATE/no duplicate on 2nd view | `test_resolve_run_create_once_then_immutable` + `test_run_scan_idempotent_and_immutable` PASSED | **PASS** | |
| TC-08 | No-lookahead on on-demand creation | artifact | as-of-D snapshot uses only bars ≤ D | `test_resolve_run_on_demand_has_no_lookahead` + `test_run_scan_no_lookahead` + bars guard PASSED | **PASS** | Covers on-demand path |
| TC-09 | No-recompute (serve storage, not live engine) | artifact | Patches engines to raise → endpoints still 200 from storage | `test_repointed_handlers_serve_persisted_date_without_recompute` PASSED | **PASS** | Live engines not invoked for persisted date |
| TC-10 | Full backend suite green | artifact | Exit 0; 0 failures; ≥179 tests | 196 passed in 928s, 0 failed, exit 0 | **PASS** | No regressions |
| TC-11 | J-15: snapshot-served reads render fast & coherent | browser | Rows render all pages; warm load <~1.5s; list scores==detail | `/stocks` renders (NVDA found); `/`, `/themes`, `/sectors` render; warm `/api/stocks` 40–100ms, dashboard/themes/sectors ~20ms; NVDA list==detail byte-identical (TC-04) | **PASS** | Far under 1.5s budget |
| TC-12 | J-13: global switcher time-travels every page | browser | ≥2 pages reflect D_OLD; "(historical)" indicator; back-to-latest restores; distinct md5 evidence | Selecting 2025-04-04 → dashboard regime flips Risk-on→Risk-off; indicator "Viewing as-of 2025-04-04 (historical)"; client-side nav to /stocks keeps date (top3 KTOS/NOC/PLTR vs latest MU/ARM/MRVL); reset to Latest clears indicator + reverts to MU/ARM/MRVL | **PASS** | 4 distinct evidence PNGs; restore PNG pixel-identical to latest (proof of clean restore) |
| TC-13 | Regression smoke (J-01/J-02/J-06/J-07) | browser | Panels render; filter changes rows; NVDA list==detail; Risk-off run zero Actionable | J-01 dashboard Risk-on panels render; J-02 Technology filter 122→58 rows (all Technology); J-06 byte-identical (TC-04); J-07 both Risk-off runs (2025-04-04, 2022-10-07) Actionable=0 | **PASS** | All existing journeys intact |

**13/13 test cases passed.**

## Browser Checks (Chrome MCP)

Frontend reachable at `http://localhost:3835`; backend `http://localhost:8835` with CORS for the
frontend origin. No CORS / connectivity errors in console.

- **As-of switcher present** in the top-bar header (`<select>`) with options sourced from
  `GET /api/runs`: Latest · 2026-05-28, 2026-02-27, 2025-11-28, 2025-08-28, 2025-05-28,
  2025-04-04, 2025-02-28, 2024-11-27, 2024-08-28, 2024-05-28, 2022-10-07. Default = Latest.
- **Time-travel proven:** selecting 2025-04-04 flipped the dashboard regime Risk-on→Risk-off and
  surfaced the amber "Viewing as-of 2025-04-04 (historical)" indicator; the historical `/stocks`
  leaderboard (KTOS/NOC/PLTR — defense) differs from latest (MU/ARM/MRVL — semis).
- **Cross-page persistence:** client-side nav (clicking the Stocks nav link) preserved the
  selected date and indicator (J-13 step 3). NB: a *full* browser reload returns to Latest
  (documented client-context limitation; reviewer NOTE — acceptable).
- **Restore:** resetting to Latest cleared the indicator and reverted the leaderboard; the
  restored-latest screenshot is pixel-identical (same md5) to the latest screenshot.

### Evidence (distinct per-journey PNGs)

`reports/qa/goal-i_can_see_the_wealthy_future-iter-8-evidence/`

| File | md5 | Purpose |
|------|-----|---------|
| TC-11-J15-stocks-latest.png | f353ee… | J-15 latest snapshot-served leaderboard |
| TC-12-J13-dashboard-latest.png | 021270… | J-13 baseline (latest, Risk-on) |
| TC-12-J13-dashboard-historical-2025-04-04.png | bfa89c… | J-13 historical dashboard + indicator (Risk-off) |
| TC-12-J13-stocks-historical-2025-04-04.png | fb1552… | J-13 historical stocks (date persisted across nav) |
| TC-12-J13-stocks-restored-latest.png | f353ee… | J-13 back-to-latest restore (= latest, proves clean reset) |

4 distinct hashes; the restored-latest PNG intentionally matches the latest stocks PNG (evidence
the restore returned exactly to the latest view). J-13 distinct-evidence requirement satisfied:
historical view on 2 pages (dashboard + stocks) + indicator + restore.

## UI Evolution Audit

**Verdict:** UI-PASS

1. **Did the UI evolve to reflect the new capability?** Yes — a new global top-bar as-of date
   switcher + a "Viewing as-of D (historical)" indicator now appear across the as-of-aware pages.
2. **Can the user see, understand, and control the new capability?** Yes — the switcher lists the
   available snapshot dates, selecting one visibly re-points every primary page, the amber
   historical badge labels the state honestly, and reset-to-latest restores the live view.
3. **Still relying on old generic pages?** No — the existing Dashboard/Stocks/Themes/Sectors/Stock
   Detail pages were re-pointed in place (additive top-bar control, no new route, no sidebar change),
   matching the blueprint's no-reapproval intent.
4. **Technically complete but product-wise underexposed?** No — the time-travel capability is fully
   surfaced and operable from the everyday pages.

## Blockers

None.

## Notes

- Verdict driven by: 196/196 backend tests green (0 regressions), all 6 API tests + 4 artifact tests
  + 3 browser tests PASS, and the criticals (no-recompute, on-demand immutability, no-lookahead,
  Risk-Off-gates-Actionable, single-source list==detail==watchlist) re-proven.
- Reviewer NOTEs are non-blocking: (a) resolver suite is 10 tests not 12 (confirmed 10, all pass);
  (b) as-of is client context (full reload → Latest); (c) `/bars` validates as_of before unknown-ticker
  — any 4xx satisfies the no-fabrication contract.
- Harness gap persists at runner scope (wrong `/health` path; runner-managed frontend died mid-run) —
  product code is correct; services were booted/reconciled per the phase spec NOTES and torn down by port.
