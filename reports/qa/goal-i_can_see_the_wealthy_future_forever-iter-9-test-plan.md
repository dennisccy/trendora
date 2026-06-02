# goal-i_can_see_the_wealthy_future_forever-iter-9 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-9
**Date:** 2026-06-02
**Frontend Present:** yes

## Phase Goal

Add ≥2 new config-driven detected price patterns beyond VCP (`pullback_to_rising_dma`, `flat_base_breakout`) that ride alongside the setup status exactly like VCP — independently filterable on the Stock Leaderboard, auto-documented on the Methodology/Glossary page from the config-backed catalog, and surfaced as pattern-vs-non-pattern forward-return breakdowns (with sample size `n` / honest NA) on System Health — without altering any of the six canonical scores, the A–E bucket, the setup-status enum, the regime engine, or the watchlist.

## Test Cases

### TC-01 — New pattern detectors flag a constructed positive series with correct pivot + invalidation
**Type:** api (unit — `tests/test_patterns.py`)
**Preconditions:** Backend importable; `config.patterns.{pullback_to_rising_dma,flat_base_breakout}` present.

**Steps:**
1. Construct an as-of price/volume series matching each pattern's shape (rising-DMA pullback; flat-base-breakout-ready).
2. Call `detect_pullback_to_rising_dma(...)` and `detect_flat_base_breakout(...)` with the pattern's config block.
3. Construct a wrong-shape series; call each detector.

**Expected outcome:** Positive series → `flagged=True` with a concrete `pivot` and `invalidation.level`/`note`; wrong-shape → `flagged=False`. Return dict shape matches `detect_vcp` (`{flagged, reason, pivot, invalidation:{level,note}, ...}`).
**Pass criteria:** Both detectors flag the positive case with non-null pivot+invalidation and do NOT flag the wrong-shape case; dict keys identical to the VCP contract.

---

### TC-02 — Insufficient history → honest NA, no fabricated level
**Type:** api (unit — `tests/test_patterns.py`)
**Preconditions:** Detectors present.

**Steps:**
1. Pass each detector a series shorter than its `min_history_bars`.

**Expected outcome:** `flagged=False` with an honest reason; NO fabricated `pivot` or `invalidation.level`.
**Pass criteria:** `flagged is False`, reason references insufficient history, pivot/invalidation level are null/absent (not synthesized).

---

### TC-03 — Detection is config-driven (threshold change flips the flag) and deterministic
**Type:** api (unit — `tests/test_patterns.py`)
**Preconditions:** Detectors present.

**Steps:**
1. Run a borderline series with the committed thresholds; record `flagged`.
2. Tighten/loosen one threshold in the passed config block; re-run.
3. Run the same input twice unchanged.

**Expected outcome:** The flag flips when the threshold changes; identical input yields identical output.
**Pass criteria:** Flag value differs between step 1 and step 2; step 3 outputs are byte-identical (deterministic).

---

### TC-04 — Pattern-not-status: forcing a new pattern flag changes NO setup status
**Type:** api (unit — `tests/test_scoring.py`)
**Preconditions:** Scoring engine importable.

**Steps:**
1. Score a stock row; record its `setup`.
2. Force-flag `pullback_to_rising_dma` (then `flat_base_breakout`) on the same input; re-score.
3. Inspect `row["setup"]` and `row["vcp"]`.

**Expected outcome:** `setup` is unchanged; new flags ride under `row["<name>"]`; `row["vcp"]` byte-identical.
**Pass criteria:** No setup-status value changes; neither new pattern writes to `setup`; `row["vcp"]` unchanged.

---

### TC-05 — Immutable mirror: `is_<name>` equals stored `record_json["<name>"]["flagged"]`
**Type:** api (unit — `tests/test_scanner.py`)
**Preconditions:** Scanner writes `ScannerResult` rows with new mirror columns.

**Steps:**
1. Run a scan; for every stored `ScannerResult`, compare `is_pullback_to_rising_dma` / `is_flat_base_breakout` against `json.loads(record_json)["<name>"]["flagged"]`.

**Expected outcome:** Mirror column equals the lossless JSON flag for every row.
**Pass criteria:** Equality holds for 100% of stored results, both patterns.

---

### TC-06 — Forward-test `by_<name>` groups by stored mirror; empty cohort NA-padded
**Type:** api (unit — `tests/test_forward_testing.py`)
**Preconditions:** `compute_forward_aggregates` extended.

**Steps:**
1. Compute aggregates over observations with known mirror values.
2. Inspect `by_pullback_to_rising_dma` and `by_flat_base_breakout`.
3. Construct an empty cohort case.

**Expected outcome:** Each breakdown groups observations exactly by the stored mirror (verbatim, no re-detect); both `True` and `False` rows always emitted; empty/sub-min-sample cohort shows `n` with `mean=None` (NA).
**Pass criteria:** Grouping matches stored mirror; both rows present; empty cohort → `n=0`, `mean=None`; cohort `n < walk_forward.min_sample` (30) → NA.

---

### TC-07 — System Health API exposes both `by_<name>` breakdowns
**Type:** api (`tests/test_api_system_health.py` + live curl)
**Preconditions:** Backend running on :8000 (live check), DB regenerated.

**Steps:**
1. `curl -s http://localhost:8000/api/system-health | jq '.aggregates | keys'` (adjust path to actual payload shape).

**Expected outcome:** Payload contains `by_pullback_to_rising_dma` and `by_flat_base_breakout` alongside `by_vcp`, each with `n` per cohort.
**Pass criteria:** HTTP 200; both keys present; each contains True/False cohorts with `n` and mean-or-NA.

---

### TC-08 — Read path never re-detects (keystone): patch detector to raise, reads still serve
**Type:** api (integration — `tests/test_api_engine.py`)
**Preconditions:** API + persisted snapshot.

**Steps:**
1. Monkeypatch `detect_pullback_to_rising_dma` (then `detect_flat_base_breakout`) to raise.
2. Call `/api/stocks` (list), `/api/stocks/{ticker}` (detail), and `/api/system-health`.

**Expected outcome:** All three endpoints return 200 serving the persisted stored values; the patched detector is never invoked on the read path.
**Pass criteria:** No exception propagates; `by_<name>` and pattern flags served from the snapshot; HTTP 200 on all reads.

---

### TC-09 — No magic numbers: no detection literal outside config
**Type:** api (unit — `tests/test_no_magic_numbers.py`)
**Preconditions:** Guard test extended with new-pattern threshold sentinels.

**Steps:**
1. Run `test_no_magic_numbers.py`; it tokenizes `patterns.py` and asserts every new-pattern threshold resolves from `cfg.patterns.<name>.*`.

**Expected outcome:** No detector-threshold literal exists outside `config.yaml`; only structural literals (indexing/rounding/percent-unit) remain.
**Pass criteria:** Test passes; each threshold traced to `config.patterns.<name>`.

---

### TC-10 — Catalog completeness + invalid-config boot failures
**Type:** api (unit / boot)
**Preconditions:** `build_catalog` guard present; Pydantic validators added.

**Steps:**
1. Confirm `build_catalog` passes with both new `kind:"pattern"` entries present.
2. Remove a catalog entry for a `config.patterns` key → expect boot failure.
3. Set `ma_period` not in `indicators.ma_periods` (and a ratio/percent out of range) → expect validation failure.

**Expected outcome:** Boot fails loudly (`ConfigError`/validation error) when a catalog entry is missing or a config value is invalid; passes when both entries present and values valid.
**Pass criteria:** Guard fires on missing entry; validators raise on invalid value; no silent default.

---

### TC-11 — Full backend suite passes after DB regeneration (offline/deterministic)
**Type:** api (full pytest, run ONCE)
**Preconditions:** `apps/backend/data/trendora.db` deleted and rebooted from the committed seed (no Yahoo/live fetch).

**Steps:**
1. Delete the DB, reboot to recompute every immutable snapshot with new pattern flags.
2. Run the full backend pytest suite once (~14 min; do not run two invocations concurrently).

**Expected outcome:** All backend tests pass; Risk-Off bootstrap dates still label Risk-Off; all J-01…J-21 values unchanged (scores/setups/regime untouched).
**Pass criteria:** Exit code 0; Risk-Off dates intact; J-07/J-08 hold post-regen.

---

### TC-12 — Frontend typechecks/builds
**Type:** artifact (`npm run build`)
**Preconditions:** `api.ts` types + pages updated.

**Steps:**
1. Run `npm run build` in `apps/frontend`.

**Expected outcome:** Build succeeds; types for new pattern interfaces + `StockRow` + aggregates compile.
**Pass criteria:** Build exits 0 with no type errors.

---

### TC-13 — Leaderboard: filter by `pullback_to_rising_dma` shows only flagged rows + badge/reason/invalidation
**Type:** browser (Chrome MCP)
**Preconditions:** Frontend on :3000, backend on :8000.

**Steps:**
1. Navigate to `/stocks`. Capture unfiltered DOM (row count).
2. Select the `pullback_to_rising_dma` pattern filter. Assert live DOM immediately, then capture.
3. Inspect a flagged row's badge tooltip (reason + concrete invalidation level, verbatim from server).
4. Reset filter to "all".

**Expected outcome:** Filtered view shows only rows where `row.pullback_to_rising_dma.flagged` (or an honest empty-state); each flagged row shows the badge with server `reason` + invalidation; "all" restores the full list.
**Pass criteria:** Filtered row count ≤ unfiltered and matches flagged set (DOM assertion, not just screenshot); badge shows verbatim reason + invalidation; distinct before/after screenshots (de-dup by sha256); pure client-side re-display (no recompute).

---

### TC-14 — Leaderboard: filter by `flat_base_breakout` shows only flagged rows + badge/reason/invalidation
**Type:** browser (Chrome MCP)
**Preconditions:** As TC-13.

**Steps:** Same as TC-13 for the `flat_base_breakout` filter.

**Expected outcome / Pass criteria:** Same criteria as TC-13 for `flat_base_breakout`; badge + reason + invalidation verbatim; filtered set matches `row.flat_base_breakout.flagged` (DOM assertion); honest empty-state if none flagged.

---

### TC-15 — Stock detail shows the same pattern badge/invalidation
**Type:** browser (Chrome MCP)
**Preconditions:** A flagged ticker known from TC-13/14.

**Steps:**
1. From a flagged row, open `/stocks/[ticker]`.
2. Inspect the pattern badge and invalidation.

**Expected outcome:** Detail page shows the same pattern badge + reason + invalidation level as the leaderboard (single source of truth).
**Pass criteria:** Badge present with identical server-built reason/invalidation; no recompute.

---

### TC-16 — Methodology: both new pattern cards auto-render from the catalog
**Type:** browser (Chrome MCP)
**Preconditions:** Frontend running; catalog has both `kind:"pattern"` entries.

**Steps:**
1. Navigate to `/methodology`.
2. Locate the `pullback_to_rising_dma` and `flat_base_breakout` cards.

**Expected outcome:** Both cards render with plain-language meaning, config thresholds (from `ref:` paths, not re-typed), and a worked example — auto-rendered from the config-backed catalog (no hard-coded per-pattern frontend copy).
**Pass criteria:** Both cards present with meaning + thresholds + example; thresholds match `config.patterns.<name>` values.

---

### TC-17 — System Health: both `by_<name>` breakdown panels render with `n` + honest NA
**Type:** browser (Chrome MCP)
**Preconditions:** Frontend running; DB regenerated.

**Steps:**
1. Navigate to `/system-health`.
2. Locate the `by_pullback_to_rising_dma` and `by_flat_base_breakout` panels alongside `by_vcp`.

**Expected outcome:** Each panel shows pattern-cohort vs non-pattern-cohort mean forward return, each with `n`; cohorts below `walk_forward.min_sample` (30) show NA with `n` (never a fabricated number).
**Pass criteria:** Both panels present; numbers + `n` shown; sub-min-sample cohorts show NA (not synthesized values).

---

### TC-18 — Regression J-16: VCP filter/badge/glossary/`by_vcp` intact
**Type:** browser (Chrome MCP)
**Preconditions:** Frontend running.

**Steps:**
1. `/stocks` filter by VCP → flagged rows + badge unchanged.
2. `/methodology` → VCP card unchanged.
3. `/system-health` → `by_vcp` panel unchanged.

**Expected outcome:** VCP behavior identical to pre-iteration.
**Pass criteria:** VCP filter, badge, glossary card, and `by_vcp` breakdown all function as before; `row["vcp"]` unchanged.

---

### TC-19 — Regression J-12: glossary shows 6 setups + 3 patterns
**Type:** browser (Chrome MCP)
**Preconditions:** Frontend running.

**Steps:**
1. Navigate to `/methodology`; count setup-status entries and pattern entries.

**Expected outcome:** All 6 setup statuses render and all 3 patterns (VCP + 2 new) render — from the single config-backed catalog.
**Pass criteria:** 6 setup entries + 3 pattern entries present.

---

### TC-20 — Regression J-02 (sector + Actionable filter) and J-07 (Risk-Off → Actionable = 0)
**Type:** browser (Chrome MCP)
**Preconditions:** Frontend running; a Risk-Off as-of date available.

**Steps:**
1. `/stocks` apply sector filter and Actionable filter — confirm they still work.
2. Select/confirm a Risk-Off run; verify zero stocks marked "Actionable".

**Expected outcome:** Sector + Actionable filters work; on Risk-Off the Actionable count is exactly 0 (watchlist-only). New patterns never promote a name to Actionable.
**Pass criteria:** Filters functional; Risk-Off Actionable count = 0.

---

## Summary

Total test cases: 20
- API tests (unit/integration/curl): 11 (TC-01 … TC-11)
- Browser tests: 8 (TC-13 … TC-20)
- Artifact checks: 1 (TC-12)

Coverage maps to DEFINITION OF DONE: J-28 end-to-end (TC-13–17), ≥2 config-driven patterns (TC-01, TC-03, TC-09), pattern-not-status (TC-04, TC-20), no-lookahead/single-source/immutable mirror (TC-05, TC-08), honest NA/n (TC-02, TC-06, TC-17), required-still-passing regression J-02/J-07/J-12/J-16 (TC-18–20), config/catalog boot guards (TC-10), and the build/test gates (TC-11, TC-12).
