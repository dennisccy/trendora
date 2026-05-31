# goal-i_can_see_the_wealthy_future-iter-12 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-12
**Date:** 2026-05-31
**Frontend Present:** yes

## Phase Goal

Deliver J-12 (the final Must-have): a config-backed Methodology / Glossary catalog of all six setup statuses + the VCP pattern, surfaced both at `/methodology` and as inline tooltips on `/stocks` setup/VCP badges — generated from a single config catalog (no hard-coded copy, thresholds resolved live so they always match config) — while keeping the other 15 journeys green for a legitimate 16/16 GOAL_ACHIEVED.

## Test Cases

### TC-01 — `GET /api/methodology` returns the catalog (shape)

**Type:** api
**Preconditions:** Backend running (TestClient or live `http://localhost:8835`); no seeded DB needed (reads config only).

**Steps:**
1. `curl -s -o /tmp/m.json -w "%{http_code}" http://localhost:8835/api/methodology`
2. Inspect JSON: top-level `intro?` + `entries[]`; each entry has `key, kind, name, meaning, thresholds[], example`; each threshold row has either (`label` + `value`/`cmp`/`unit?`) or (`label` + `text`).

**Expected outcome:** 200 with a well-formed catalog payload matching `build_catalog` output.
**Pass criteria:** HTTP 200; `entries` length ≥ 7; every entry has all required keys; every threshold row has exactly one of `value`(ref-resolved) or `text`.

---

### TC-02 — Catalog completeness: all six statuses + VCP pattern present

**Type:** api
**Preconditions:** TC-01 payload available.

**Steps:**
1. Collect `kind:"setup"` entry names; confirm Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist.
2. Collect `kind:"pattern"` entries; confirm VCP present.
3. Confirm `"VCP"` does NOT appear as a `kind:"setup"` entry.

**Expected outcome:** Every `setups.ALL_STATUSES` status appears as a setup entry; `vcp` appears as a pattern entry; VCP is never a setup status.
**Pass criteria:** 6 setup entries matching ALL_STATUSES + 1 VCP pattern entry; VCP absent from setup entries. (Anti-goal: VCP is a pattern, not a status.)

---

### TC-03 — Matching-config keystone: displayed values equal live config

**Type:** api
**Preconditions:** TC-01 payload; access to real `config.yaml` values.

**Steps:**
1. For each threshold row with a `ref`, resolve the live config value (e.g. `decision_rules.actionable.leadership`=80, `entry`=70, `risk`=60; VCP `patterns.vcp.*`).
2. Compare each rendered `value` to the resolved live config value.

**Expected outcome:** Every displayed threshold value equals the value its `ref` resolves to in config.
**Pass criteria:** Zero mismatches between displayed `value` and resolved config value (no hard-coded copy, no drift).

---

### TC-04 — Config-driven: extra catalog entry renders with no code change

**Type:** artifact
**Preconditions:** `test_methodology.py` exists; alternate config fixture with ONE extra entry referencing existing config keys.

**Steps:**
1. Load the alternate config; call `build_catalog` / hit `GET /api/methodology`.
2. Confirm the extra entry appears in output with NO change to Python/TS source.

**Expected outcome:** The new entry surfaces purely from config.
**Pass criteria:** A unit test exists and passes asserting the config-only extra entry is present in the catalog without code edits.

---

### TC-05 — Honest-failure: unresolvable `ref` raises ConfigError at boot

**Type:** artifact
**Preconditions:** `test_config*.py` exists.

**Steps:**
1. Load a config whose methodology entry has an unresolvable threshold `ref`.
2. Observe boot/validation behavior.

**Expected outcome:** Boot fails loudly with `ConfigError` (never a silent/placeholder threshold).
**Pass criteria:** A test exists and passes asserting `ConfigError` is raised on an unresolvable `ref`.

---

### TC-06 — No magic numbers: `methodology.py` in CALC_FILES

**Type:** artifact
**Preconditions:** Backend test suite available.

**Steps:**
1. Confirm `methodology.py` is added to `CALC_FILES` in `test_no_magic_numbers.py`.
2. Run `test_engine_calc_code_has_no_magic_numbers`.

**Expected outcome:** `methodology.py` is scanned and contains no threshold literal (all numbers resolved from config).
**Pass criteria:** Test passes with `methodology.py` in `CALC_FILES`.

---

### TC-07 — MINIMAL_VALID config still loads with methodology section

**Type:** artifact
**Preconditions:** `test_config.py` exists.

**Steps:**
1. Confirm `MINIMAL_VALID` includes a minimal valid `methodology` section.
2. Run config tests that load `MINIMAL_VALID`.

**Expected outcome:** From-scratch config fixture loads cleanly.
**Pass criteria:** `MINIMAL_VALID` (with minimal `methodology`) validates and loads; test passes.

---

### TC-08 — Full backend test suite passes

**Type:** artifact
**Preconditions:** All backend deps installed.

**Steps:**
1. Run the full backend pytest suite (per project-template test command).
2. Capture pass/fail counts.

**Expected outcome:** All tests pass including new `test_methodology.py` cases.
**Pass criteria:** 0 failures, 0 errors; new methodology/config/api tests all pass.

---

### TC-09 — Empty-diff non-regression of canonical engine/model/router files

**Type:** artifact
**Preconditions:** Git available.

**Steps:**
1. `git diff --stat` against the iteration base for `models.py`, `scanner.py`, `scoring.py`, `setups.py`, `patterns.py`, `forward_testing.py`, and the existing routers.

**Expected outcome:** These pre-existing files are byte-unchanged.
**Pass criteria:** Empty diff for all listed files (J-01–J-11/J-13–J-16 cannot structurally regress); backend `order`/`broker`/secret greps stay empty.

---

### TC-10 — `/methodology` page renders the full catalog

**Type:** browser
**Preconditions:** Backend up (`CORS_ORIGINS=http://localhost:3835`); frontend built (`NEXT_PUBLIC_API_URL=http://localhost:8835`) and serving.

**Steps:**
1. Navigate to `/methodology`.
2. Verify all six setup statuses + VCP each render: name, kind chip (Setup/Pattern), plain-language meaning, compact thresholds list (`label cmp value unit` or verbatim `text`), worked example.
3. Spot-check Actionable (Leadership ≥ 80, Entry ≥ 70, Risk ≤ 60) and VCP (its `patterns.vcp.*` thresholds + meaning + example).
4. Capture a distinct PNG to `reports/qa/<phase>-evidence/` and `md5sum` it.

**Expected outcome:** Dense-dark glossary page lists every entry from the fetched catalog with config-matching thresholds.
**Pass criteria:** 7 entries visible with all parts; spot-checked thresholds match config; page contains no hard-coded entry list (data comes from `/api/methodology`).

---

### TC-11 — `/stocks` setup-badge inline tooltip shows catalog meaning

**Type:** browser
**Preconditions:** Frontend serving with data.

**Steps:**
1. Navigate to `/stocks`.
2. Hover AND keyboard-focus AND click/tap a setup badge.
3. Read the revealed inline definition; confirm it matches the `/methodology` meaning for that `row.setup.status`.
4. Confirm tooltip is dismissible. Capture a distinct PNG (md5-distinct from TC-10) to the evidence dir.

**Expected outcome:** The setup badge reveals the catalog `meaning` inline via hover/focus/tap.
**Pass criteria:** Definition appears via click/tap (not title-only), is dismissible, and equals the `/methodology` meaning for that status.

---

### TC-12 — `/stocks` VCP badge exposes catalog VCP meaning (J-16 step 4)

**Type:** browser
**Preconditions:** `/stocks` has at least one VCP-flagged row.

**Steps:**
1. On `/stocks`, locate a VCP badge; hover/focus/tap it.
2. Confirm the per-row reason is still present AND the catalog VCP `meaning` is reachable inline.

**Expected outcome:** VCP badge keeps its existing per-row reason and additionally exposes the catalog VCP definition.
**Pass criteria:** Both the per-row reason and the catalog VCP `meaning` are reachable from the VCP badge inline.

---

### TC-13 — `/stocks` Setup filter sourced from catalog + graceful degradation (J-02)

**Type:** browser
**Preconditions:** Frontend serving.

**Steps:**
1. On `/stocks`, open the Setup filter; confirm options are the six catalog `kind:setup` statuses in catalog order (hard-coded `SETUP_STATUSES` removed).
2. Select a setup; confirm rows narrow correctly.
3. Simulate catalog-fetch failure (backend down for the catalog call); confirm the leaderboard + Sector/Setup/VCP filters still work using statuses present in the data.

**Expected outcome:** Filter vocabulary is catalog-driven; a catalog hiccup does not break J-02.
**Pass criteria:** Filter options come from the catalog; selecting narrows rows; on catalog failure the page degrades gracefully (leaderboard + filters still functional).

---

### TC-14 — Sidebar gains "Methodology" nav after Watchlist

**Type:** browser
**Preconditions:** Frontend serving.

**Steps:**
1. Inspect the sidebar nav order.
2. Click "Methodology"; confirm it routes to `/methodology`.

**Expected outcome:** New nav item with BookOpen icon, placed after Watchlist, navigates to the glossary.
**Pass criteria:** "Methodology" present after Watchlist; clicking lands on `/methodology`.

---

### TC-15 — Backend-unavailable error state on `/methodology`

**Type:** browser
**Preconditions:** Backend stopped (or `/api/methodology` returns non-200).

**Steps:**
1. Navigate to `/methodology` with the backend down.
2. Observe the page state.

**Expected outcome:** Explicit "Backend unavailable" error (never fabricated copy).
**Pass criteria:** Page shows the explicit error/empty state; no synthesized threshold or placeholder copy rendered. (Anti-goal: no fabricated data.)

---

### TC-16 — Frontend build clean, route count 11 → 12

**Type:** artifact
**Preconditions:** Frontend deps installed.

**Steps:**
1. Run `npm run build` in `apps/frontend`.
2. Confirm typecheck + compile succeed and the new `/methodology` route appears.

**Expected outcome:** Clean build; app route count increases from 11 to 12.
**Pass criteria:** Build succeeds with no type/compile errors; `/methodology` listed among routes (12 total).

---

### TC-17 — 16-journey regression sweep renders canonical values

**Type:** browser
**Preconditions:** Backend + frontend serving with seeded data.

**Steps:**
1. Visit `/`, `/stocks`, `/themes`, `/sectors`, `/scanner-runs` (+ a Risk-off run → 0 Actionable, J-07), `/system-health` (by-bucket/setup/regime/excess/control-group + by_vcp), `/backtest`, `/watchlist`.
2. Exercise the global as-of switcher (J-13).
3. Confirm each surface renders its canonical values unchanged; capture distinct md5-distinct PNGs per surface.

**Expected outcome:** All 15 other journeys remain green alongside J-12.
**Pass criteria:** Every listed surface renders correctly; Risk-off → 0 Actionable; as-of switching works; no regression observed.

---

## Summary

Total test cases: 17
API tests: 3 — TC-01, TC-02, TC-03
Browser tests: 7 — TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-17
Artifact checks: 7 — TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-16
