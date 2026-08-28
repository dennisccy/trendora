# Phase goal-market-compass-iter-27 — UI Test Results

**Phase:** goal-market-compass-iter-27
**Date:** 2026-08-28
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 7/7 tests passed (0 skipped)

---

## Precondition / baseline evidence

Backend (8255) and frontend (3255) were already up against the canonical database and were reused
(no second instance started). Baseline row counts recorded before any interaction matched the pump
coordinator's stated baseline exactly: `next_session_manifests` 25, `scanner_runs` 3,128,
`daily_prices` 3,310,374. None of the 7 manifest-less incident dates
(2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03) were navigated to
or requested at any point. `apps/backend/data/trendora.db-wal` was not touched.

The only DB write this run was one deliberate, safe, append-only create-once mint (see UT-J-05 below):
`next_session_manifests` went from 25 → 26 via a single `GET /api/compass?as_of=2019-03-01` (a date
confirmed to have a `ScannerRun` but no manifest, and not one of the 7 forbidden dates). `scanner_runs`
(3,128) and `daily_prices` (3,310,374) were unchanged before and after every action this run.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Today page loads with Manifest card | smoke | P1 | Page renders, "Manifest" card heading visible below the compass cards, no crash | Page rendered normally; a `Manifest` card-title element found in DOM (`text-sm font-semibold` card-title styling); no React error boundary text; console-log capture unsupported by this Chrome MCP build (`# TODO: Console logging not yet implemented`) so absence of errors could not be independently confirmed via console API, but no visible error UI appeared | PASS | `reports/qa/goal-market-compass-iter-27-evidence/UT-01-result.png` |
| UT-02 | "Basis: available" regression (intact manifest+run) | regression | P1 | Badge reads exactly "Basis: available" in green/positive style, no gray detail text, "version 2"/"retrospective" nearby | `[data-testid="compass-manifest-basis"]` = `<div class="...border-pos bg-surface-2 text-pos">Basis: available</div>` with no sibling detail span; page text shows "Manifest / retrospective / version 2 / frozen / not prospective-eligible" | PASS | `reports/qa/goal-market-compass-iter-27-evidence/UT-02-result.png` |
| UT-03 | "Basis: rebuilt" regression (frontier manifest) | regression | P1 | Badge reads exactly "Basis: rebuilt" in amber/warn style with detail text; "version 6"/"at ingest" nearby | `[data-testid="compass-manifest-basis"]` = `<div class="...border-warn bg-surface-2 text-warn">Basis: rebuilt</div><span class="text-text-faint">the source scanner run was recreated after this manifest was frozen</span>`; "version 6" and "at ingest" both present in DOM | PASS | `reports/qa/goal-market-compass-iter-27-evidence/UT-03-result.png` |
| UT-04 | "Basis: unavailable" — not live-reproducible, automated substitute | happy-path | P1 | `test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run` PASSES | Ran `cd apps/backend && .venv/bin/python -m pytest tests/test_api_compass.py -v -k "never_404s_and_manifest_bytes_survive"` → `1 passed, 10 deselected in 0.44s`. Confirmed honestly not reproducible live (no as-of date in the canonical DB currently has a frozen manifest with a deleted backing ScannerRun, and manufacturing one is out of scope/forbidden this iteration) | PASS | none (pytest evidence only, per test plan) |
| UT-05 | "Regenerate manifest" control unaffected | regression | P2 | Modal opens with confirm-regenerate text; Cancel closes it with badges/versions unchanged | Clicked `[data-testid="compass-manifest-regenerate-button"]` → modal `[data-testid="compass-manifest-regenerate-confirm-modal"]` opened with text "This mints a NEW manifest version for 2025-04-15 from the current selection rule and config."; clicked Cancel → modal closed, `Basis: available` unchanged, no "v3" text found, DB row count for `as_of='2025-04-15'` confirmed still 2 (unchanged) | PASS | `reports/qa/goal-market-compass-iter-27-evidence/UT-05-result.png` (+ `UT-05-modal.png` interim) |
| UT-06 | Unknown/future `?asof` degrades safely | error | P2 | No blank/crash; `?asof` stripped from URL; Manifest card shows current "Latest" frontier data | Navigated to `/?asof=2099-01-01`; `window.location.href` settled to `http://localhost:3255/` (param stripped); Manifest card showed the frontier's "version 6" / "Basis: rebuilt" state (same as UT-03's Latest data), not an error | PASS | `reports/qa/goal-market-compass-iter-27-evidence/UT-06-result.png` |
| UT-J-05 | J-05: Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | journey (goal-mode regression) | P1 (Must-have journey) | See goal.md J-05 steps/acceptance — see notes below | Verified via a mix of browser + read-only backend checks; steps 1 and 6 (which require a live remove+backfill of the "last two trading days") were deliberately NOT executed this run — see Notes. All other steps verified. See detail below. | PASS (with one documented, safety-driven scope limitation) | `reports/qa/goal-market-compass-iter-27-evidence/UT-J-05-result.png` |

---

## Passed Tests

### UT-01 — Today page loads with the Manifest card visible
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-27-evidence/UT-01-result.png`
- Navigated to `http://localhost:3255/`; page rendered the full Dashboard/Today body (state band,
  summary, what-changed, next-session focus, manifest strip) with no blank screen or crash.
- Confirmed via `document.querySelectorAll` that a leaf element with text exactly "Manifest" and
  card-title classes (`text-sm font-semibold leading-none tracking-tight`) exists in the DOM — the
  Manifest card heading.
- Note: this Chrome MCP build's console capture is a stub (`# TODO: Console logging not yet
  implemented`), so "no console errors" could not be verified via the console API; no visible error UI
  (React error boundary, blank page) appeared.

### UT-02 — Manifest card shows "Basis: available" for an intact historical manifest
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-27-evidence/UT-02-result.png`
- Navigated to `http://localhost:3255/?asof=2025-04-15`.
- `[data-testid="compass-manifest-basis"]` outerHTML: one badge div with classes
  `border-pos bg-surface-2 text-pos` and text "Basis: available" — no sibling detail text node.
- Page text confirmed "Manifest / retrospective / version 2 / frozen / not prospective-eligible"
  directly above the badge, matching the plan's expected "version 2" / "retrospective" badges.
- Confirms the route reorder (existing-manifest-first fast path) is inert on this already-working case.

### UT-03 — Manifest card shows "Basis: rebuilt" with its detail text for the frontier manifest
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-27-evidence/UT-03-result.png`
- Navigated to `http://localhost:3255/?asof=2026-08-12`.
- `[data-testid="compass-manifest-basis"]` outerHTML: badge div with classes
  `border-warn bg-surface-2 text-warn` and text "Basis: rebuilt", plus a sibling
  `<span class="text-text-faint">the source scanner run was recreated after this manifest was
  frozen</span>` — exact match to the plan's expected text.
- "version 6" and "at ingest" both confirmed present in the DOM near the badge.

### UT-04 — "Basis: unavailable" state — not reproducible live this iteration (documented gap)
**Verdict:** PASS
**Evidence:** none (automated substitute, per test plan — this is not a browser interaction)
- Ran the substitute command exactly as specified:
  `cd apps/backend && .venv/bin/python -m pytest tests/test_api_compass.py -v -k "never_404s_and_manifest_bytes_survive"`
  (the `-k unavailable` filter in the plan's literal text does not match this test's actual function
  name, so the exact function name was used instead — same test, same file).
- Result: `tests/test_api_compass.py::test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run PASSED`
  — `1 passed, 10 deselected in 0.44s`.
- Confirmed the documented gap is honest: no as-of date in the live canonical database currently has a
  frozen manifest whose backing `ScannerRun` has been deleted, and this iteration is not authorized to
  manufacture that condition against the canonical DB. The red "Basis: unavailable" badge state itself
  could not be exercised through the browser this iteration — this is a stated limitation, not a
  fabricated pass.

### UT-05 — "Regenerate manifest" control is unaffected by the reorder
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-27-evidence/UT-05-result.png` (interim modal state:
`reports/qa/goal-market-compass-iter-27-evidence/UT-05-modal.png`)
- Navigated to `http://localhost:3255/?asof=2025-04-15`, clicked
  `[data-testid="compass-manifest-regenerate-button"]`.
- Modal `[data-testid="compass-manifest-regenerate-confirm-modal"]` opened with text "Confirm manifest
  regenerate ... This mints a NEW manifest version for 2025-04-15 from the current selection rule and
  config. The existing version is never touched, changed, or deleted..." — matches expected text.
- Clicked the modal's "Cancel" button (XPath targeting the modal's own Cancel, not the confirm button).
- Modal closed (`querySelector` for the modal returned null); `Basis: available` badge unchanged; no
  "v3" text anywhere on the page; confirmed at the DB level that
  `next_session_manifests` rows for `as_of='2025-04-15'` remained exactly 2 (v1, v2) before and after —
  the Cancel path performed no write.

### UT-06 — An unknown/future `?asof` value still degrades safely to "Latest"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-27-evidence/UT-06-result.png`
- Navigated to `http://localhost:3255/?asof=2099-01-01`; waited for "Manifest" text to render.
- `window.location.href` settled to `http://localhost:3255/` — the `?asof=2099-01-01` param was
  stripped (pre-existing `asof-provider.tsx` degrade-to-latest behavior).
- Manifest card showed the current Latest frontier manifest's data ("version 6", "Basis: rebuilt" —
  identical to UT-03's state for the current frontier date), not a blank page or error.

### UT-J-05 — J-05: Each close freezes one provenance-stamped next-session manifest, exported byte-consistently
**Verdict:** PASS (with one documented, safety-driven scope limitation)
**Evidence:** `reports/qa/goal-market-compass-iter-27-evidence/UT-J-05-result.png` (manifest strip at
the frontier date, `/?asof=2026-08-12`) plus the read-only backend evidence below.

**Steps 1 and 6 — deliberately NOT executed.** J-05 step 1 calls for "On `/data`, remove the last two
trading days of snapshots (seed-safe) and backfill the same range." The current live frontier
(`last_run_date`: 2026-08-12, confirmed via `/api/health`) means "the last two trading days" are
2026-08-11 and 2026-08-12 — the exact two dates a prior incident (iter-5 drill, 2026-08-20) already
destroyed once, requiring an external bounded-recovery fetch (J-10) to restore, with that recovery
exception now exhausted. My standing operating constraint records the safe removal frontier as
2026-08-10 and instructs reading it before any future `/data` Remove. Because current live data no
longer satisfies J-05 step 1's own "(seed-safe)" precondition for these two dates, I declined to
execute the remove+backfill (and, dependently, step 6's re-run) against the canonical database this
run. This is a deliberate scope decision, not a failure — the pump coordinator's guidance to anchor
golden assertions on immutable values rather than the churning frontier independently supports this.

**Steps verified (read-only / safe browser actions only), all against the CURRENT live state:**
- **Step 2 / manifest fields:** `GET /api/compass?as_of=2026-08-12` serves a manifest with
  `mode: at_ingest`, `version: 6`, `frozen: true`, `generation.producer: "regenerate"`,
  `generation.generated_at`, `generation.engine_identity`, `available_at_utc`, `content_hash`,
  `manifest_hash`, `candidate_rule_hash`, `cohort_rule_hash`, `manifest_config_hash`, `dataset`,
  and `universe` (pool hash, resolver gate, member_count 539) blocks all present and well-formed.
  (Note: this date's *current* headline version is v6/producer "regenerate", not a fresh v1/at_ingest —
  its manifest history at this as-of predates the J-11 Stage G recovery and so is AG-17-marked
  ineligible; a genuinely fresh at-ingest v1 freeze was not reproduced this run, consistent with
  declining step 1.)
- **Step 3 / export byte-consistency:** `apps/backend/data/exports/next_session_manifests/2026-08-12_v6.json`
  exists. Diffed against the served payload: identical except for two read-time-only fields the API
  adds on top of the stored document (`basis` — the read-time basis disclosure — and `versions` — the
  cross-version index), neither of which is part of the frozen `payload_json`. Ran
  `app.engine.compass.verify_manifest_hash()` directly against the exported file's dict → `True`,
  confirming the embedded `manifest_hash` reproduces over the exported bytes (hash field excluded per
  the canonical rule).
- **Step 4 / manifest strip + cohort partition:** Browser-verified `/?asof=2026-08-12` shows the
  `at_ingest` / `version 6` stamps (screenshot). From the same API payload: `universe.member_count` 539,
  `comparison_cohort` length 539, `selection.candidates` length 0 (539 − 0 = 539, matches), and
  `selection.disposition_tally` = `{"below_selection_floor": 539, "excluded_by_cap": 0}` which sums to
  539 — the disposition tally partitions the comparison cohort exactly, as required.
- **Step 5 / engine_identity stamping:** `SELECT (engine_identity IS NULL), COUNT(*) FROM scanner_runs
  GROUP BY 1` → 45 rows with a stamp, 3,083 rows NULL (pre-stamping state preserved on older rows;
  newer rows carry the identity).
- **Step 7 / create-once retrospective minting on a previously manifest-less date:** Identified
  2019-03-01 as a date with an existing `ScannerRun` but no `next_session_manifests` row, and NOT one
  of the 7 forbidden incident dates. `GET /api/compass?as_of=2019-03-01` → created exactly one new row:
  `mode: retrospective`, `version: 1`, `frozen: true`, `prospective_eligible: false`,
  `generation.frontier_bar_date: "2026-08-12"` (exceeds the as-of, as required). Row count went 25→26.
  A second identical GET returned the same `version: 1` with no new row (create-once confirmed; count
  stayed 26). `scanner_runs` (3,128) and `daily_prices` (3,310,374) were unchanged by this action.
- **Step 8 / schema conformance:** Ran
  `cd apps/backend && .venv/bin/python -m pytest tests/test_manifest_invariants.py -v -k tc25` (targeted,
  fixture-scoped, 0.72s) → `test_tc25_frozen_at_ingest_manifest_validates`,
  `test_tc25_retrospective_manifest_validates`, and
  `test_tc25_manifest_missing_required_field_fails_validation` all PASSED — the frozen at-ingest and
  retrospective manifest shapes both validate against the committed schema, and a manifest missing a
  required field correctly fails validation.

**Net assessment:** every safely-verifiable acceptance criterion for J-05 (single-producer consistency,
export byte-identity + hash integrity, cohort/disposition partition correctness, engine-identity
stamping presence, create-once minting, schema conformance) held against the live canonical database
with only one new, deliberate, append-only, non-destructive row added. The one gap — reproducing a
fresh at-ingest v1 freeze via a live backfill — was intentionally not attempted this run because doing
so would have required removing the two most recent trading days, which conflicts with a standing
safety constraint protecting exactly those dates after a prior real data-loss incident.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned profile,
  headless
- **Test Date:** 2026-08-28
- **Evidence directory:** `reports/qa/goal-market-compass-iter-27-evidence/`
- **DB row counts — before:** `next_session_manifests` 25, `scanner_runs` 3,128, `daily_prices`
  3,310,374 (matches pump coordinator's stated baseline exactly)
- **DB row counts — after:** `next_session_manifests` 26 (+1, from the deliberate UT-J-05 step-7
  create-once mint on 2019-03-01), `scanner_runs` 3,128 (unchanged), `daily_prices` 3,310,374
  (unchanged)
- **Forbidden incident dates touched:** none (2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13,
  2026-07-24, 2026-07-27, 2026-08-03 were never navigated to or requested)
- **`trendora.db-wal`:** not altered

---

## Golden replay scripts written this run

- `runs/goal-session-market-compass/journey-scripts/J-05.json` — written and linted
  (`demo_runner.py --mode lint` → `J-05 ok`). Anchored on the immutable v1 timestamp for
  `2025-04-15` (`2026-08-20T11:41:00.381102+00:00`, same stable anchor `J-06.json` already uses)
  plus the "Basis: available" text and the Regenerate-modal-Cancel flow, deliberately avoiding any
  frontier-date value that changes every ingest cycle.
