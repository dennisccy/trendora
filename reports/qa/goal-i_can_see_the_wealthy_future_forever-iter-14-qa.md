**Verdict:** PASS

# goal-i_can_see_the_wealthy_future_forever-iter-14 QA Report

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-14
**Date:** 2026-06-02
**Agent:** qa (MODE 2 — QA Validation)
**Frontend Present:** yes
**Target journey:** J-29 — Setup & Pattern Lab (event study) on `/research` + stored MAE/MFE excursion path

---

## Step 1 — Required artifact verification

| Artifact | Status |
|----------|--------|
| `docs/handoffs/goal-…-iter-14-dev.md` | ✅ present |
| `docs/handoffs/goal-…-iter-14-frontend.md` | ✅ present |
| `reports/reviews/goal-…-iter-14-review.md` (verdict **PASS**) | ✅ present, PASS |
| `runs/goal-…-iter-14/plan.md` | ✅ present |
| `reports/qa/goal-…-iter-14-test-plan.md` | ✅ present (18 TCs, executed below) |
| `runs/goal-…-iter-14/status.json` | ✅ present (updated to complete at Step 6) |

All required artifacts present; review verdict is PASS.

---

## Step 2 — Backend test suite (canonical full run)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Log: `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-14-test.log`

```
........................................................................ [ 15%]
........................................................................ [ 31%]
........................................................................ [ 47%]
........................................................................ [ 63%]
........................................................................ [ 78%]
........................................................................ [ 94%]
........s...........sss..                                                [100%]
453 passed, 4 skipped in 1265.06s (0:21:05)
EXIT=0
```

**453 passed, 4 skipped, exit 0.** The 4 skips are the offline-skipped `integration`-marked live-network
tests (Data Manager live fetch), unchanged by this iteration and unrelated to iter-14 — every iter-14 test
(forward_testing excursions, research event-study, api/research endpoint, no-magic-numbers) ran and passed.
Run was executed ONCE against the regenerated DB (per the iter-13 playbook / backend-suite-runtime memory).
No failure digest needed (exit 0).

## Step 3 — Frontend build (typecheck)

Command: `cd apps/frontend && npm run build` → **exit 0**. `/research` route built (9.21 kB); all routes
compiled and typechecked, including the new `EventStudyLab` / `fetchEventStudy` / `EventStudyResponse`.

---

## Step 3.5 — Functional test plan results

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | MAE/MFE no-lookahead | unit | first `horizon` bars only; unchanged when later bars removed | `forward_excursions` slices `bars_after_list[:horizon]` (source L141); test green in suite | PASS | source-verified + suite |
| TC-02 | MAE/MFE NA gate | unit | None + no row when entry missing/zero or `< horizon` bars | exact `forward_return` gate (source L137-140); suite green | PASS | shared gate confirmed |
| TC-03 | Excursion immutability/idempotency | unit | warm backfill inserts 0 rows, UPDATEs no snapshot | suite green; dev: 6739 rows, 0 band violations | PASS | append-only INSERT |
| TC-04 | MFE ≥ realized ≥ MAE band | unit | band holds for all assertable rows | suite green; dev: 0 band violations across 6739 rows | PASS | |
| TC-05 | Event-study read-only keystone | unit | SELECT-only; patched scoring math never invoked | suite green; source: 0 forbidden call sites in `compute_event_study` | PASS | patch-to-raise + source |
| TC-06 | Consistency invariant (pooled mean == aggregates cohort mean) | unit | equal for setup (`by_setup`) and VCP (`by_vcp`) | suite green; dev live-verified | PASS | bound to `compute_forward_aggregates` |
| TC-07 | Downside-only risk-adjusted + honest NA | unit | return/downside-dev + return/MAE; NA on no-downside/mean\|MAE\|==0/n<2 | suite green; live: both ratios present, NA where defined | PASS | no total-vol metric |
| TC-08 | Unknown subject → ValueError; Σ regime n == pooled n | unit | ValueError; every regime label; Σn == pooled | suite green; live: Σ regime n=99 == n_total=99 | PASS | |
| TC-09 | Endpoint default / 422 / 503 / payload shape | api | 200 / 422 / 422 / 503; full payload | live: 200 default, 422 bogus subject, 422 horizon=99999; payload has subjects/by_horizon/by_regime/by_sector/caveats; 503 covered by unit test | PASS | 503 via unit (live DB has data) |
| TC-10 | No magic numbers scan extended | artifact | no new literal threshold | `test_no_magic_numbers.py` green in suite | PASS | |
| TC-11 | Full backend suite green after regen | suite | exit 0, 0 failures | 453 passed, 4 skipped, exit 0 | PASS | |
| TC-12 | Frontend build typechecks | artifact | exit 0 | exit 0; `/research` 9.21 kB | PASS | |
| TC-13 | J-29 SETUP subject full event study | browser | distribution+expectancy+MAE/MFE+both downside ratios+n; best-exit highlighted; caveat | Breakout-watch (n=99): all 10 columns render per horizon; 60d "best exit" highlighted; survivorship+descriptive caveats visible | PASS | `TC-13-setup-event-study.png` |
| TC-14 | J-29 PATTERN subject + by-regime/sector NA + re-point | browser | pattern renders; ≥1 NA+n; distinct sha | pullback_to_rising_dma (n=163) renders full numbers; by-regime (empty regimes NA+n=0) + by-sector (low-sample NA+n) panels; VCP (n=27) honest NA; subjects re-point distinctly | PASS | `TC-14-pattern-event-study.png` |
| TC-15 | J-18 as-of toggle byte-identical, zero as_of | browser | section byte-identical; 0 `as_of` requests | toggled global as-of latest→2025-05-28 (factor lab re-pointed, proving toggle took effect); event-study section byte-identical; 0 event-study requests carry `as_of` | PASS | `TC-15-j18-asof-byteidentical.png`; API: as_of param ignored (sha equal) |
| TC-16 | J-07 Risk-Off → Actionable=0 after regen | browser | 0 Actionable both Risk-off runs | run 1 & run 2 (Risk-off): 122 rows, 0 Actionable each | PASS | `TC-16-scanner-runs.png` |
| TC-17 | J-06 NVDA list↔detail byte-identical | browser | every score/bucket/setup matches | leadership/entry_quality/risk (incl. components+bucket), setup, sector, rank all byte-identical list↔detail | PASS | `TC-17-nvda-leaderboard.png` |
| TC-18 | Required surfaces still green (J-09/J-14/J-25–27/J-30) | browser | render unchanged; factor lab re-points | System Health (by-bucket/setup/regime/vcp), Backtest scorecard render error-free; Factor Lab re-points on factor change | PASS | `TC-18-system-health.png` |

**18 / 18 test cases passed.**

---

## Step 4 — Chrome MCP browser checks

Frontend reachable at `http://localhost:3835` (HTTP 200); backend `http://localhost:8835/api/health` (HTTP 200).
Browser checks executed via Chrome MCP (this `qa` agent only — access serialized; evidence de-duped by sha256).

Evidence (all 6 screenshots distinct by sha256) under
`reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-14-evidence/`:
- `TC-13-setup-event-study.png` — Breakout-watch full per-horizon table + caveats
- `TC-14-pattern-event-study.png` — pullback_to_rising_dma + by-regime/by-sector NA panels
- `TC-15-j18-asof-byteidentical.png` — event study after as-of toggle (byte-identical)
- `TC-16-scanner-runs.png` — scanner runs (Risk-off runs present)
- `TC-17-nvda-leaderboard.png` — stocks leaderboard
- `TC-18-system-health.png` — System Health aggregates

**Key live findings:**
- Event-study endpoint payload keys: `subject`, `subjects` (9-entry config-driven catalog: 6 setups + 3 patterns,
  grouped by `kind`), `horizon`, `horizons` `[1,5,10,20,60]`, `default_horizon` 20, `min_sample` 30,
  `by_horizon`, `by_regime`, `by_sector`, `best_exit_horizon`, `n_total`, `survivorship_bias`, `descriptive_caveat`.
- Breakout-watch (n=99): every horizon row carries mean/median/%positive/dispersion/expectancy(==mean)/mean-MAE/
  mean-MFE/return-per-downside-dev/return-per-MAE/n; best-exit 60d highlighted.
- by-regime emits every one of the 6 config regime labels (empty regimes → NA + n=0); **Σ per-regime n = 99 = n_total** (conservation holds).
- by-sector present-only, honest NA + n on low-sample sectors.
- **J-18:** the event-study section is byte-identical across a real global as-of toggle (the toggle demonstrably
  changed the Factor Lab), and **zero** event-study fetches carry an `as_of` param (DOM + `performance` resource assertion). API confirms: `?as_of=…` yields byte-identical (sha-equal) response.
- **J-07:** both seeded Risk-off runs (run 1, run 2) carry 0 Actionable after the DB regen.
- **J-06:** NVDA canonical six scores + bucket + setup + sector + rank byte-identical between `/api/stocks` list and `/api/stocks/NVDA` detail.

**Source-level seam verification (anti-goal criticals):**
- No forbidden engine file touched (`scoring.py`/`scanner.py`/`patterns.py`/`regime.py`/`buckets.py` — none in diff).
- `compute_event_study` has 0 forbidden call sites (no `run_scan`/`score_stocks`/`forward_return`/`forward_excursions`/`detect_*`/`score_regime`/`backfill`) — read-only keystone holds (also proven by the patch-to-raise unit test).
- `forward_excursions` uses `bars_after_list[:horizon]` with the exact `forward_return` NA gate → no-lookahead + honest NA in source.

---

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the phase's new capability?** Yes — `/research` gains a third lab section
   (**Setup & Pattern Lab — event study**) below the Factor Lab + Combination Lab, with a subject selector,
   per-horizon distribution/exit-horizon table, by-regime and by-sector panels, and caveat banner.
2. **Can the user see, understand, and control the new capability?** Yes — a grouped (Setups vs Patterns)
   subject selector + the shared horizon selector drive a fully labelled table; low-sample cells show honest
   NA + n; best-exit-horizon is highlighted; survivorship + descriptive caveats are visible.
3. **Still relying on old generic pages for new functionality?** No — the new analytic has its own dedicated
   section and endpoint; MAE/MFE are surfaced through it (not bolted onto existing pages).
4. **Technically complete but product-wise underexposed?** No — the capability is discoverable on the approved
   `/research` home and renders real, stored, lookahead-free evidence with honest NA.

**Verdict:** UI-PASS

---

## Blockers

None.

## Notes

- DB was regenerated from the committed seed for this iteration; both criticals (J-07, J-06) re-verified green
  after regen. Snapshots regenerate byte-identical (scoring path untouched, forward-side only).
- The default subject (Actionable, first catalog subject per spec) renders honest NA + n=2 (genuinely rare
  setup < min_sample=30) — correct low-sample behavior, not a bug; data-rich subjects (Breakout-watch, Avoid,
  pullback_to_rising_dma) show full numbers.
- Services are runner-managed; no servers were started by this agent (nothing to kill). Browser session is
  Chrome-MCP-managed.
</content>
</invoke>
