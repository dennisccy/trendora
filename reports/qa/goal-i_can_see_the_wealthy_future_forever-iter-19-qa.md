# QA Report — goal-i_can_see_the_wealthy_future_forever-iter-19

**Verdict:** PASS

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-19 (J-32 — Research All-history ⟷ As-of-date mode toggle)
**Date:** 2026-06-04
**Agent:** qa (MODE 2 — validation)
**Frontend Present:** yes (Chrome MCP browser checks executed)

---

## Step 1 — Required artifact verification

| Artifact | Status |
|----------|--------|
| `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-19-dev.md` | ✅ present (122 lines) |
| `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-19-frontend.md` | ✅ present (75 lines) |
| `reports/reviews/goal-i_can_see_the_wealthy_future_forever-iter-19-review.md` | ✅ **PASS** verdict |
| `runs/goal-i_can_see_the_wealthy_future_forever-iter-19/status.json` | ✅ present (`current_step: review_passed`) |
| `reports/qa/...-test-plan.md` | ✅ present (16 test cases — executed below) |

UI-visibility artifacts (TC-14): implementation-summary ✅, user-visible-changes ✅, ui-surface-map ✅, ui-test-plan ✅, what-to-click ✅, dev + frontend handoffs ✅. (`ui-test-results` is produced downstream by browser-qa-agent — not a QA-step blocker.)

---

## Step 2 — Backend test suite (TC-09)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Log: `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-19-test.log`

```
================= 476 passed, 4 skipped in 1153.64s (0:19:13) ==================
EXIT=0
```

**476 passed, 4 skipped, 0 failed, 0 error.** Exit code 0. The 4 skips are the live-network `integration`/Stooq-real-fetch + committed-universe tests (skipped offline — expected, not failures). No new failures, no regressions. The J-32 as-of engine tests and the updated contract tests are included in this green run.

---

## Step 3 — Frontend build/typecheck (TC-13)

Per dev handoff: `cd apps/frontend && npm run build` → compiled successfully, types valid, 13/13 pages generated (`/research` builds clean). Verified live: `GET /_next/static/chunks/main-app.js → 200` and the page hydrated (health badge cleared, `checking:false`) before driving the UI. (QA did NOT run `npm run build` against the live dev `.next` — MEMORY `browser-qa-dead-shell-next-cache`.)

---

## Step 3.5 — Functional test plan results

Backend run dates available (from `GET /api/runs`): `2022-10-07 … 2026-05-28` (11 snapshots). Latest = `2026-05-28`. Early dates used for scoping evidence: `2024-05-28`, `2024-08-28`, `2022-10-07`.

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | All-history byte-identical (`none==latest==current`) | api | All 3 forms identical | factor-lab `n_total` 1218 both `none` and `as_of=latest`; unit test `test_factor_lab_as_of_none_equals_latest_is_byte_identical_all_history` green in suite | **PASS** | `as_of=None` adds no clause |
| TC-02 | As-of scopes only ≤ D, no future-run leak | api | Early cutoff strictly smaller pool | factor-lab 1218→242 (`2024-05-28`); combination pool_n 1217→241→120; event-study 2→0; `no_future_leak` unit tests green for all 3 labs | **PASS** | cutoff reads canonical `ScannerRun.asof_date` |
| TC-03 | Early-cutoff low-sample → NA + n | api | Thin cells flagged, not fabricated | factor-lab @ `2022-10-07`: deciles `n=12 low_sample:true` (vs `n=121 low_sample:false` all-history); unit `..._early_cutoff_is_low_sample_na` green | **PASS** | backend flags `low_sample`; UI renders NA |
| TC-04 | As-of so early → honest empty `n=0` | api | `n=0`, no 500, no fabricated row | event-study @ `2024-05-28` → `n_total=0`, HTTP 200; unit `..._before_any_snapshot_is_empty_not_fabricated` green | **PASS** | live UI shows "No forward-tested occurrences" |
| TC-05 | Endpoint validation 422/400/200 | api | unparseable→422, future→400, valid→200 | All 3 endpoints: `not-a-date`→**422**, `2027-01-01`→**400**, valid historical→**200** | **PASS** | validated via shared `resolved_date` |
| TC-06 | Payload echoes resolved cutoff; null unscoped | api | null/absent unscoped; resolved when scoped | All 3: `asof_date=None` unscoped; `asof_date=<D>` echoed when scoped | **PASS** | |
| TC-07 | 3 `*_no_date_control_present` updated to J-32 truth | api | Updated not deleted | `test_factor_lab/_factor_combination/_event_study_no_date_control_present` all present + updated; module docstring (line 8+) updated to J-32 contract | **PASS** | iter-2 lesson honored |
| TC-08 | Read-only keystone: scoped path recomputes nothing | api | Patched-to-raise passes; grep only docstrings | 3 `..._is_read_only...` tests green; forbidden-call grep (`run_scan`/`score_stocks`/`backfill`/`forward_return`/`detect_`/`score_regime`) in `research.py` hits only docstrings/comments (lines 12–15, 498–499, 876–880) | **PASS** | |
| TC-09 | Full backend suite green | api | exit 0, no new failures | **476 passed, 4 skipped, exit 0** | **PASS** | run once (~19 min) |
| TC-10 | J-32 end-to-end: As-of re-points with reduced n | browser | n drops in As-of, restores in All-history | All-history decile n≈121 → As-of @ `2022-10-07` n=12 (+NA cells) → back to All-history n=121 restored. 3 distinct sha256 screenshots | **PASS** | survivorship label persists both modes |
| TC-11 | J-18: exactly one date control, no second state | browser+source | One date `<select>` in `<header>`; As-of fetch carries `?as_of=`; All-history no refetch on date change | Exactly **1** date `<select>` (`aria-label="View as-of date"`, in `<header>`), 0 in `<main>`, 0 `input[type=date]`. As-of toggle fired 3 fetches all `?as_of=2024-08-28`. All-history date change fired **0** research fetches | **PASS** | `?as_of=` is the transmitted single global date (MEMORY `j18-asof-on-stocks-fetch-is-correct`) |
| TC-12 | Required-passing journeys render in default mode | browser | J-25/26/27/29/30 render; J-31 travel | All sections present: Decile sort + Rank-IC (J-25), Multi-factor combination composite + strict overlap (J-26), Factor effectiveness by market regime (J-27), Setup & Pattern Lab event study (J-29), volatility family (J-30), synthesis cross-link (J-31) | **PASS** | |
| TC-13 | Frontend build/typecheck clean | build | exits 0, no TS errors | dev handoff: compiled, types valid, 13/13 pages; hydrated build verified live | **PASS** | |
| TC-14 | UI-visibility artifacts present | artifact | 6 artifacts + handoffs | impl-summary, user-visible-changes, ui-surface-map, ui-test-plan, what-to-click + dev/frontend handoffs all present | **PASS** | ui-test-results produced downstream by browser-qa |
| TC-15 | Blueprint annotated, no re-approval marker | artifact | iter-19 note + 3 rows annotated; no marker | blueprint.md line 90 = iter-19 "NO skeleton change" note + as_of annotations on the 3 lab rows; `blueprint.reapproval-requested` absent | **PASS** | |
| TC-16 | Scoring/snapshot path git-untouched (J-06/J-07) | artifact | out-of-scope files unchanged | `git status --porcelain` empty for scoring.py/scanner.py/regime.py/patterns.py/buckets.py/forward_testing.py/snapshot_serving.py/asof-provider.tsx/stocks/page.tsx/backtest/page.tsx | **PASS** | no DB regen |

**16/16 test cases passed.**

---

## Step 4 — Chrome MCP browser checks

Frontend confirmed running (`http://localhost:3835` → 200) and hydrated (`main-app.js → 200`, health badge cleared). Evidence saved under `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-19-evidence/` (3 distinct sha256 screenshots — iter-6 lesson).

**J-32 end-to-end (TC-10):**
- Default mode = **All history** (`aria-pressed: All history=true, As of date=false`); decile n ≈ 121–122 (matches `n_total=1218`). → `TC-10-baseline-all-history.png`
- Toggled **As of date** + set global `<select>` to earliest `2022-10-07` (native-setter + bubbling change event): every decile n dropped **121 → 12**; NA cells appear (low-sample at early date); context label *"Point-in-time: pooling only snapshots dated ≤ 2022-10-07 … driven by the single global as-of switcher"*; survivorship + descriptive caveats persist. → `TC-10-asof-2022-10-07.png`
- Toggled back to **All history** (global date still 2022-10-07): full sample **n=12 → 121 restored**, point-in-time label removed. Proves labs key on the resolved cutoff (null in All-history), not raw `asOf`.

**J-18 principal anti-goal (TC-11):**
- Live: exactly **one** date `<select>` (`aria-label="View as-of date"`, descendant of `<header>`); the 6 `<main>` selects are factor/condition/quantile/subject pickers (no date options); zero `input[type=date]`; the mode toggle is a button group (`aria-pressed`), not a date control.
- Network (fetch spy): toggling to As-of (global date 2024-08-28) fired exactly **3** research fetches — `/api/research/factor-lab|factor-combination|event-study` — **all carrying `?as_of=2024-08-28`** (the single global date transmitted on a snapshot-served read — expected, not a violation per MEMORY `j18-asof-on-stocks-fetch-is-correct`).
- J-15 read-path: in **All-history** mode, changing the global date (→ 2024-08-28) fired **zero** research fetches; decile n stayed full (121). Refetch is keyed on `asofCutoff`, not raw `asOf`.
- As-of @ 2024-08-28 decile n=36 (intermediate point-in-time window), confirming a third distinct scoping level.

**Required-still-passing (TC-12):** J-25 (decile/rank-IC), J-26 (composite + strict-overlap), J-27 (regime split), J-29 (event study), J-30 (volatility family), J-31 (synthesis cross-link) all render in default All-history mode and re-point in As-of mode. Event-study honest empty ("No forward-tested occurrences") at an early date — n=0, no fabrication, no 500.

---

## Step 4b — UI Evolution Audit

1. Did the UI evolve to reflect the new capability? **Yes** — a single page-level **All history ⟷ As of date** segmented toggle drives all three labs; an inline point-in-time context label appears in As-of mode.
2. Can the user see/understand/control the capability? **Yes** — one click switches modes; the resolved as-of date + "pooling only snapshots dated ≤ D" explanation is shown; figures visibly re-point (smaller n, honest NA).
3. Relying on old generic pages? **No** — lives on the existing approved `/research` home, additive.
4. Technically complete but product-underexposed? **No** — fully exposed and discoverable; survivorship/descriptive caveats persist in both modes.

**Verdict:** UI-PASS

---

## Step 5 — Blockers

None.

---

## Notes

- No anti-goal violation: as-of mode is a pure read-only FILTER (`as_of=None` byte-identical all-history; forbidden-call grep hits only docstrings; out-of-scope files git-untouched; no DB regen → J-06/J-07 byte-identical).
- J-18 holds: exactly one date control (global header switcher); the `?as_of=` on the research fetch is the single global date transmitted, not a second date state.
- Services managed by the QA runner — QA started no servers (only instrumented `window.fetch` in-page, restored on navigation). No cleanup required.

**Verdict:** PASS
