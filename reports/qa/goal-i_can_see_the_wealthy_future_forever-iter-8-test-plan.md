# goal-i_can_see_the_wealthy_future_forever-iter-8 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-8
**Date:** 2026-06-02
**Frontend Present:** yes

## Phase Goal

Execute the committed J-22 runbook now that the Yahoo data wall has cleared: replace the curated 122-name universe with a transparent, config-screened ~400–500-name universe built from real committed OHLCV + market cap, so `/methodology` surfaces the real Universe-Selection screen and `/data` shows the grown coverage count — all from real data, nothing fabricated, with the full regression set still green.

## Test Cases

### TC-01 — Universe expanded to ~400–500 real names in config

**Type:** artifact
**Preconditions:** Runbook executed; `config.yaml` regenerated.

**Steps:**
1. Load `config.yaml`: `python -c "import yaml; print(len(yaml.safe_load(open('config.yaml'))['universe']['symbols']))"`.
2. Inspect that members are no longer the curated 122 list.

**Expected outcome:** `universe.symbols` contains ~400–500 entries (not 122).
**Pass criteria:** Count is in [400, 500] band (≥400). Each member also has a `stock_sectors` entry (no orphan symbol). Themes remain non-empty and every theme member is in the universe.

---

### TC-02 — Committed screen-pass record exists and every member passes the screen

**Type:** artifact
**Preconditions:** Screen+ingest step completed.

**Steps:**
1. Confirm `apps/backend/data/seed/universe.json` exists.
2. For each member record, confirm market cap ≥ `min_market_cap` ($2B), dollar-vol ≥ `min_dollar_vol` ($50M), price ≥ `min_price` ($10) — the thresholds in `config.universe.filters`.

**Expected outcome:** `universe.json` present; every recorded member satisfies all three recorded thresholds.
**Pass criteria:** File exists; zero members violate any of the three `universe.filters` thresholds; thresholds in the record match `config.universe.filters` (no re-typed numbers).

---

### TC-03 — New committed seed artifacts present (no fabricated bars)

**Type:** artifact
**Preconditions:** Screen+ingest completed.

**Steps:**
1. Confirm ~380 new per-symbol `apps/backend/data/seed/<SYMBOL>.csv` files exist for the new screened names.
2. Confirm `apps/backend/data/seed/meta.json` is refreshed (date window + symbol count updated to the expanded set).
3. Confirm existing committed CSVs were reused untouched (date window aligned to existing seed, not extended).

**Expected outcome:** New per-symbol OHLCV CSVs + refreshed `meta.json` committed; every CSV holds real fetched bars.
**Pass criteria:** Per-symbol CSV count matches the new-name count in `universe.json`; `meta.json` symbol count ≈ 500; no symbol in `universe.json` lacks a backing CSV; date window unchanged vs prior seed.

---

### TC-04 — `GET /api/methodology` serves the universe_selection section with live-ref thresholds

**Type:** api
**Preconditions:** Backend running on port 8835 with regenerated DB.

**Steps:**
1. `curl -s http://localhost:8835/api/methodology`
2. Inspect the `universe_selection` object.

**Expected outcome:** Section is present (honest gate open) with membership rule, the three thresholds resolved live from `universe.filters` (via `ref`), and `resolved_size` ≈ 500.
**Pass criteria:** HTTP 200; `universe_selection` present and non-null; the three threshold values equal `config.universe.filters` ($2B / $50M / $10) with no re-typed literals; `resolved_size` in [400, 500].

---

### TC-05 — Single source of truth: `/api/data` universe_count == `/api/methodology` resolved_size == config

**Type:** api
**Preconditions:** Backend running on port 8835.

**Steps:**
1. `curl -s http://localhost:8835/api/data` → read `universe_count`.
2. `curl -s http://localhost:8835/api/methodology` → read `universe_selection.resolved_size`.
3. Compare both to `len(config.universe.symbols)`.

**Expected outcome:** All three values are identical (no recompute, no drift).
**Pass criteria:** `universe_count` == `resolved_size` == config symbol count, all ≈ 500. No discrepancy.

---

### TC-06 — Risk-Off seam preserved: both bootstrap dates label Risk-Off with zero Actionable (critical, J-07)

**Type:** api
**Preconditions:** Backend running; seed regenerated over the expanded universe.

**Steps:**
1. Identify the two seeded bootstrap dates in `config.scanner.bootstrap_dates` (originally `2022-10-07`, `2025-04-04`; a config-only swap may have replaced a flipped one).
2. For each, fetch the seeded scanner run and read the regime label + Actionable count.

**Expected outcome:** Each seeded bootstrap run resolves to Risk-Off (or Defensive); when Risk-Off, zero stocks are marked Actionable (watchlist-only).
**Pass criteria:** At least one seeded run is Risk-Off with exactly 0 Actionable; no Risk-Off run shows any Actionable stock; if a date was swapped, the swap is config-only (no code, no fabricated run).

---

### TC-07 — Full pytest suite passes ONCE, including the 3 now-active committed-record tests

**Type:** artifact
**Preconditions:** `apps/backend/data/trendora.db` deleted and regenerated via backend lifespan boot. Run pytest exactly once (boot is ~14 min — never run two concurrently).

**Steps:**
1. Run the full backend pytest suite once, capturing output to `reports/qa/<phase>-test.log`.
2. Verify `test_universe_screen.py`'s 3 previously-skipped committed-record tests (screen-pass / matches-config / market-cap-from-storage) now activate.

**Expected outcome:** Whole suite green; the 3 committed-record tests run (not skipped) and pass.
**Pass criteria:** Exit code 0; 0 failures; the 3 committed-record tests reported as passed (not skipped); `test_seed_integrity` (risk-on AND risk-off stretches), `test_no_magic_numbers`, `test_config`, no-lookahead and snapshot-immutability suites all green.

---

### TC-08 — `/methodology` Universe-Selection card renders real screened values (J-22 primary, browser)

**Type:** browser
**Preconditions:** Frontend on port 3835, backend on 8835; `universe.json` exists.

**Steps:**
1. Assert live URL is `/methodology`; navigate via Chrome MCP.
2. Locate the Universe-Selection card.
3. Read the membership rule, the three thresholds, and the resolved size. Screenshot to `reports/qa/<phase>-evidence/TC-08-methodology-universe-card.png`.

**Expected outcome:** Card is visible (was hidden at 122) showing the membership rule + the three config thresholds ($2B / $50M / $10) + resolved size ~400–500.
**Pass criteria:** Card present and populated; thresholds match `universe.filters`; resolved size in [400, 500]; values are display-formatted API values, not a hand-curated code list.

---

### TC-09 — `/data` Universe coverage metric shows grown count consistent with methodology (J-17 + single source, browser)

**Type:** browser
**Preconditions:** Frontend on port 3835.

**Steps:**
1. Assert live URL is `/data`; navigate via Chrome MCP.
2. Read the Universe coverage metric. Screenshot to `reports/qa/<phase>-evidence/TC-09-data-universe-metric.png`.

**Expected outcome:** Universe metric shows ≈ 500, equal to the `/methodology` resolved size.
**Pass criteria:** Coverage count in [400, 500] and equal to TC-08's resolved size (single source, no drift).

---

### TC-10 — Risk-Off seeded run renders Risk-Off label + 0 Actionable in UI (J-07, browser)

**Type:** browser
**Preconditions:** Frontend on port 3835; seeded Risk-Off bootstrap run available.

**Steps:**
1. Open a seeded Risk-Off bootstrap run via the dashboard/as-of control.
2. Assert live DOM shows the regime label; read the Actionable count. Screenshot to `reports/qa/<phase>-evidence/TC-10-riskoff-zero-actionable.png`.

**Expected outcome:** Regime label is Risk-Off (or Defensive); Actionable count is 0 (watchlist-only).
**Pass criteria:** Label is Risk-Off/Defensive AND Actionable = 0 in the rendered UI.

---

### TC-11 — Dashboard + leaderboard render ranked rows over the wider universe (J-01/J-02, browser)

**Type:** browser
**Preconditions:** Frontend on port 3835.

**Steps:**
1. Navigate to the dashboard and leaderboard surfaces.
2. Confirm ranked rows render without layout break over the ~500-name universe. Screenshot to `reports/qa/<phase>-evidence/TC-11-leaderboard-wide-universe.png`.

**Expected outcome:** Dashboard + leaderboard render ranked rows spanning the expanded universe; layout unchanged.
**Pass criteria:** Both pages render ranked rows (more than 122 names available); no error/empty state; score coherence holds (ordering consistent).

---

### TC-12 — System Health renders with grown forward-test sample size (J-09, browser)

**Type:** browser
**Preconditions:** Frontend on port 3835; seed regenerated.

**Steps:**
1. Navigate to System Health.
2. Read the forward-test sample size `n`. Screenshot to `reports/qa/<phase>-evidence/TC-12-system-health-n.png`.

**Expected outcome:** System Health renders; forward-test `n` is larger than at 122 names.
**Pass criteria:** Page renders without error; `n` strictly greater than the prior (122-universe) sample size; breadth/walk-forward labels remain "universe-relative" / survivorship-biased (honest limitation text intact).

---

### TC-13 — Methodology glossary intact alongside the new card (J-12, browser)

**Type:** browser
**Preconditions:** Frontend on port 3835.

**Steps:**
1. On `/methodology`, confirm the existing setup/pattern glossary still renders below the Universe-Selection card.

**Expected outcome:** Glossary content unchanged; new card sits above it without displacing existing sections.
**Pass criteria:** Glossary present and complete; no regression in existing methodology content; the new card is additive.

---

### TC-14 — J-08 immutability: older runs differ from latest, rows never mutated

**Type:** artifact
**Preconditions:** Seed regenerated (create-once ≤ D snapshots; append-only > D forward returns).

**Steps:**
1. Inspect persisted `scanner_run` rows: confirm an older seeded run's result rows differ from the latest run.
2. Confirm forward returns live in the separate append-only table keyed to the snapshot (not overwriting snapshot rows).

**Expected outcome:** Snapshots immutable; older runs preserved distinct from latest; no row overwrite.
**Pass criteria:** Distinct historical runs present; snapshot result rows unchanged after creation; forward returns are append-only in their own table.

---

### TC-15 — Error path: fetch/threshold failures are logged + omitted, never fabricated

**Type:** artifact
**Preconditions:** Screen+ingest run log available (dev handoff §ingest log).

**Steps:**
1. Inspect the screen run log / dev handoff for candidates that failed to fetch, returned empty/partial series, lacked a market cap, or failed a threshold.
2. Confirm each such candidate is OMITTED from `universe.json` (not present), never assigned synthesized prices/caps.

**Expected outcome:** Every failed candidate is logged with a reason and excluded; no fabricated bars/caps anywhere.
**Pass criteria:** No omitted-and-logged candidate appears in `universe.json`; no synthesized data; if the bulk fetch hard-walled and < ~400 names passed, the dev handoff records an honest halt (STALLED) rather than padding. The `screen_reasons` predicate failure paths are unit-asserted (covered by TC-07).

---

### TC-16 — Dev handoff present and states the data-step outcome plainly

**Type:** artifact
**Preconditions:** Iteration executed.

**Steps:**
1. Confirm `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-8-dev.md` exists.
2. Confirm it states: whether the live fetch succeeded, how many candidates passed vs were omitted (and why), and whether a bootstrap date was swapped.

**Expected outcome:** Handoff present with the three required disclosures.
**Pass criteria:** File exists; fetch outcome, pass/omit counts with reasons, and bootstrap-swap status all stated.

---

## Summary

Total test cases: 16
API tests: 3 (TC-04, TC-05, TC-06)
Browser tests: 6 (TC-08, TC-09, TC-10, TC-11, TC-12, TC-13)
Artifact checks: 7 (TC-01, TC-02, TC-03, TC-07, TC-14, TC-15, TC-16)

**Note (graceful-degradation):** If the probe-gate re-walls at dispatch (persistent Yahoo 429) and the runbook halts honestly (STALLED) before regenerating the universe, TC-01–TC-15 cannot be satisfied by fabrication; the correct outcome is an honest halt recorded in TC-16's handoff — that is a non-regression result, not a QA failure to be papered over.
