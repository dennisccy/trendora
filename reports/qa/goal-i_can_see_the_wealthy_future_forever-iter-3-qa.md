**Verdict:** PASS

# QA Validation Report — goal-i_can_see_the_wealthy_future_forever-iter-3

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-3 (J-17 — Data Manager)
**Date:** 2026-06-01
**Agent:** qa (MODE 2 — validation)
**Frontend Present:** yes (services validated on backend `:8835`, frontend `:3835`)

---

## Step 1 — Required artifacts

| Artifact | Status |
|----------|--------|
| `docs/handoffs/...-iter-3-dev.md` | ✅ present (states live-Stooq fetch tested against real endpoint → apikey-gated → skipped honestly) |
| `docs/handoffs/...-iter-3-frontend.md` | ✅ present |
| `reports/reviews/...-iter-3-review.md` | ✅ present, **PASS_WITH_NOTES** (2 non-blocking NOTEs) |
| `runs/...-iter-3/status.json` | ✅ present (`current_step: review_passed`) |
| `reports/qa/...-iter-3-test-plan.md` | ✅ present (19 cases, executed below) |

Review verdict is PASS_WITH_NOTES — proceeding. The two NOTEs (near-instant-job refresh edge; a stooq test that asserts via non-CSV 200 rather than a ≥400 status) are non-blocking and do not affect the DoD.

---

## Step 2/3 — Backend + Frontend test suites

**Backend** (`cd apps/backend && .venv/bin/python -m pytest tests/ -v`), full log: `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-3-test.log`:

```
================= 294 passed, 1 skipped in 1011.36s (0:16:51) ==================
PYTEST_EXIT=0
```

- **0 failures, 0 errors.** 294 passed ≥ iter-2 baseline (266). The single skip is the
  `@pytest.mark.integration` live-Stooq fetch (`test_stooq_real_fetch_single_symbol_or_skip`) — documented:
  Stooq's free CSV endpoint is now apikey-gated, the provider correctly treats the non-CSV body as
  `ProviderUnavailableError` (fabricates nothing), so the test skips honestly rather than silently passing.
- All new-module tests green: `test_data_manager.py` (10), `test_api_data.py` (7), `test_stooq_provider.py`
  (8 + 1 skip), `test_config.py` data_manager validation (3).

**Frontend** — per dev handoff `npm run build` compiled clean (13 routes incl. `/data`); independently
confirmed at runtime: `/data`, `/stocks`, `/`, `/scanner-runs`, `/system-health` all render and respond 200.

---

## Step 3.5 — Functional Test Plan results

API tests run against `:8835`; browser tests via Chrome MCP at `:3835`. Evidence screenshots in
`reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-3-evidence/`.

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | Coverage endpoint reports true metadata | api | symbol_count 158, price 2021-01-04→2026-05-28, gaps non-empty, history present | `symbol_count=158`, `price_start=2021-01-04`, `price_end=2026-05-28`, `gap_count=1345`+`gaps_preview` list, `runs` present | **PASS** | Field names are descriptive (`gap_count`/`gaps_preview` rather than `gaps`); all required data present |
| TC-02 | Coverage correctness on fixture | artifact | `test_compute_coverage_*` present+passing | `test_compute_coverage_exact`, `_gap_preview_capped_by_config`, `_empty_db_is_all_none` PASSED | **PASS** | |
| TC-03 | Start backfill returns job_id immediately | api | `{job_id}`, non-blocking | HTTP 200 `{"job_id":"2042…","status":"running"}` returned promptly | **PASS** | |
| TC-04 | Job polling: progress → final summary | api | advancing counts → terminal summary | Browser flow caught `running · snapshots 2/5`; API final `status:ok, dates_done 5/5, snapshots_created 5, forward_returns_inserted 3200` | **PASS** | Fast backfill; in-progress 2/5 captured in browser TC-16 (screenshot) |
| TC-05 | Invalid ranges rejected 4xx | api | each rejected, no job | start>end→**400**; missing range→**422**; malformed date→**422**; unknown job→**404** | **PASS** | Explicit error bodies on all |
| TC-06 | Backfill grows n deterministically | artifact | test present+passing | `test_backfill_grows_n_and_adds_runs` PASSED | **PASS** | Corroborated live: System Health n 1793→2368 |
| TC-07 | Backfill lookahead-free | artifact | snapshot==run_scan(D), ≤D scoring, >D returns | `test_backfill_is_lookahead_free_and_reuses_canonical` PASSED | **PASS** | |
| TC-08 | Create-once / immutable | artifact | re-backfill no-op; append-only | `test_backfill_create_once_immutable`, `test_dataprovider_run_is_append_only_per_job` PASSED | **PASS** | Live re-run of same range → `snapshots_created:0`, count stayed 16 |
| TC-09 | No second scan/return path | artifact | only canonical calls; no new math | `data_manager.py:254-255` calls `scanner.run_scan` + `forward_testing.backfill_run_forward_returns`; no `score`/`compute_forward` defs | **PASS** | Reuse contract honored |
| TC-10 | Forced fetch failure: explicit error, zero fabrication | artifact | test present+passing | `test_fetch_forced_failure_writes_no_bars_or_snapshots`, `test_network_failure_raises_provider_unavailable_no_bars` PASSED | **PASS** | Also verified live (TC-17) |
| TC-11 | Live Stooq integration (skip allowed) | artifact | marked test exists; handoff honest | `@pytest.mark.integration test_stooq_real_fetch_single_symbol_or_skip` present, SKIPPED; handoff documents apikey-gate outcome | **PASS** | No silent pass |
| TC-12 | Config-driven / no magic numbers | artifact | tunables from config; magic-number test green | `cfg.data_manager.{max_range_days,gap_preview,live_provider,run_history_limit}` read; config validation tests + full suite green | **PASS** | |
| TC-13 | `/data` date inputs ≠ second as-of state | artifact | local job params; no useAsOf/setAsOf binding | `app/data/page.tsx` uses only `refresh` from `useAsOf`; dates are local `useState`; never calls `setAsOf` | **PASS** | Page text explicitly states inputs don't change global as-of |
| TC-14 | Sidebar nav + additive refresh() | artifact | nav entry; non-disruptive refresh | `sidebar.tsx:39 { href:"/data", label:"Data Manager", icon: Database }`; `asof-provider.tsx:32,66 refresh()` re-fetches runs, never touches `asOf`/`latest` | **PASS** | |
| TC-15 | Backend suite passes (no regressions) | artifact | exit 0, ≥266 pass, 0 fail | **294 passed, 1 skipped, 0 failed**, exit 0 | **PASS** | |
| TC-16 | J-17 full multi-step flow | browser | coverage→start→progress→summary→new date selectable (no reload)→n grew | All 6 steps verified (see below) | **PASS** | Primary journey |
| TC-17 | Forced provider failure in UI | browser | explicit error, failed counts, no fake success | UI progress panel: `failed · 0/158 ok, 158 failed, 0 new bars · 20 errors (no data fabricated)`; snapshot_count + price_end unchanged | **PASS** | Real Stooq apikey gate drove the failure |
| TC-18 | Regression: J-07/08/09/13/14 | browser | all remain green | J-13/J-14/J-08/J-07/J-09 all verified (see below) | **PASS** | |
| TC-19 | Default boot path unchanged | artifact | lifespan untouched; only router add | `main.py` lifespan still `bootstrap_runs`+`backfill_forward_returns`; `data.router` added line 79 (additive, last) | **PASS** | No live fetch in boot |

**19/19 test cases passed.**

---

## Step 4 — Chrome MCP browser checks

Frontend reachable (`:3835` → 200). Full J-17 acceptance flow exercised end-to-end (not a single load).

### TC-16 — J-17 primary flow (evidence: TC-16-1…5)
1. **Coverage panel** rendered: price history `2021-01-04 → 2026-05-28`, Symbols `158`, Trading days `1356`,
   Snapshot dates `16`, Backfill gaps `1340`, gap range shown. Run history table populated.
2. **Started a backfill job** `2021-02-01 → 2021-02-05` (kind=backfill) via the form's Start button — a
   range of gap dates absent from the switcher (confirmed pre-job: switcher had 15 options, no 2021-02).
3. **Live progress advanced**: captured `running · snapshots 2/5 dates · 2 snapshots · 1280 forward returns`.
4. **Final summary**: `ok · backfill: 5 snapshots over 5 dates, 3200 forward returns · 5/5 dates`; new run
   row appeared in run history.
5. **New dates selectable WITHOUT a hard reload**: the global switcher gained the 5 `2021-02-0x` dates
   (15→20 options) via `refresh()`. Selecting `2021-02-05` resolved on `/stocks` (122 rows, date shown) and
   on `/` (Dashboard: `Data as-of 2021-02-05`, regime computed, Actionable=1).
6. **System Health n grew**: pre-job `n=1793, n_runs=15` → post-job `n=2368, n_runs=20`; UI shows
   `Snapshots contributing: 20 · Mean stock fwd return +2.86% (n=2368)`; the 5 new dates appear in
   `asof_dates`.

### TC-17 — Forced provider failure (evidence: TC-17-…)
Started a **fetch** job (`2026-05-29`) through the UI. The live Stooq provider is apikey-gated in this
environment, so the real provider failed. UI progress panel showed honest, explicit failure:
`fetched 0/158 (… failed) · 0 new price bars · 20 errors (no data fabricated)` then terminal
`failed · 0/158 symbols ok, 158 failed, 0 new bars`. Backend confirmed **zero fabrication**: snapshot_count
unchanged (31), `price_end` still `2026-05-28`, `bars_fetched=0`; run persisted with `status=failed`. No
fake success anywhere.

### TC-18 — Regression set (evidence: TC-18-…)
- **J-13** (switcher drives view): selecting `2021-02-05` changed Dashboard to `Data as-of 2021-02-05` with
  recomputed regime/Actionable; selection persisted across in-app nav (system-health → /stocks held the
  date). ✅
- **J-14** (per-date scorecard): backfilled `2021-02-05` yields a valid Dashboard scorecard (regime
  components, breadth, top sectors) and 122 stock rows on `/stocks`. ✅
- **J-08** (immutable runs in run list): `/scanner-runs` now lists 21 runs including all backfilled
  2021-01/2021-02 dates. ✅
- **J-07** (Risk-Off → zero Actionable): backfilled Risk-Off dates `2022-06-16` and `2022-09-30` both report
  `candidate_counts.Actionable = 0` (all 122 → Risk-off-watchlist), vs the risk-on `2021-02-05` showing
  Actionable=1. The regime gate holds for backfilled snapshots (via the reused canonical scanner path). ✅
- **J-09** (aggregate coherence): `/system-health` aggregate stays coherent with the grown sample — overall
  mean + per-bucket means each carry their own `n`, low-sample figures labelled, survivorship-bias caveat
  present. ✅

Evidence files: `TC-16-1-coverage-and-form.png`, `TC-16-2-progress-running.png`, `TC-16-3-summary-ok.png`,
`TC-16-4-backfilled-date-stocks.png`, `TC-16-5-system-health-n-grew.png`,
`TC-18-J13-dashboard-backfilled-date.png`, `TC-18-scanner-runs-new-immutable.png`,
`TC-17-fetch-failure-progress.png`, `TC-17-fetch-failure-final.png`.

---

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the new capability?** Yes — a new `/data` page with a Coverage panel, a
   Job form (date/range + kind), a live-progress panel, and a run-history table; plus a `Data Manager`
   sidebar entry.
2. **Can the user see, understand, and control the new capability?** Yes — they read coverage/gaps, start a
   fetch/backfill job, watch live progress, read a final ok/failed summary, and immediately find new as-of
   dates in the global switcher with System Health evidence grown.
3. **Still relying on old generic pages?** No — `/data` is the dedicated, blueprint-approved home; the
   switcher/System Health surfaces (existing pages) correctly reflect the newly created dates/evidence.
4. **Technically complete but under-exposed?** No — the full flow is discoverable and user-operable;
   provider failures are surfaced explicitly (never a fake success).

**Verdict:** UI-PASS

---

## Anti-goal / coherence verification

- **Real-data-only fetch** — Stooq failure surfaced explicitly; zero fabricated bars/snapshots (TC-10, TC-17). ✅
- **Range backfill immutable & lookahead-free** — re-run no-op, append-only, ≤D / >D split (TC-07, TC-08). ✅
- **No second computation path** — orchestrates `scanner.run_scan` + `forward_testing.backfill_run_forward_returns`; no new score/return math (TC-09). ✅
- **Exactly one date selector** — `/data` date inputs are local job params, never bound to `useAsOf` (TC-13). ✅
- **Default boot unchanged** — lifespan untouched; router include is the only `main.py` change (TC-19). ✅
- **No magic numbers** — all job limits read from `config.data_manager.*` (TC-12). ✅

---

## Blockers

None.

## Notes (non-blocking)

- Review NOTE re: near-instant-job refresh edge — not triggered by the real (multi-second) backfill flow;
  the J-17 DoD path always polls and refreshes. Observed working in TC-16 (new dates appeared without reload).
- During testing the runtime/QA DB accumulated extra backfilled snapshots (2021-01, 2021-02, 2022 dates) and
  two failed-fetch run rows — expected, append-only, and the DB is gitignored + bootstrapped on boot.
- Live Stooq fetch is unavailable in this environment (apikey gate); the no-fabrication contract is proven by
  both the offline forced-failure unit test and the real endpoint's behavior (TC-11, TC-17).

## Services

Backend `:8835` and frontend `:3835` are managed by the QA runner — not started or stopped by this agent.

---

**Verdict:** PASS
