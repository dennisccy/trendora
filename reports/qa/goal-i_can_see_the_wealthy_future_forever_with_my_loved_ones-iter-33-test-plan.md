# Goal Iteration 33 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-33  
**Date:** 2026-06-18  
**Frontend Present:** yes

## Phase Goal

Implement a dynamic point-in-time stock universe that resolves per as-of-date based on price, ADV, and minimum-history thresholds; add per-date coverage diagnostics and a membership timeline view showing universe entries/exits; offer a data-walled backward-history extension flow; and reconcile a stale test guard.

---

## Test Cases

### TC-01 — Consolidation: Stale data-overview guard accepts macro key

**Type:** api  
**Preconditions:** Backend code compiles; test suite is runnable.

**Steps:**
1. Open `apps/backend/tests/test_api_data.py::test_get_data_overview_shape`.
2. Verify the guard at line ~74 now uses a superset comparison (`{…} <= set(payload)`) OR includes `"macro"` in the expected set.
3. Run `pytest apps/backend/tests/test_api_data.py::test_get_data_overview_shape -xvs`.

**Expected outcome:** Test passes with no assertion error.  
**Pass criteria:** Exit code 0; no `AssertionError` on the payload shape comparison.

---

### TC-02 — Per-as-of-date universe resolver: price threshold admits only qualifying names

**Type:** api  
**Preconditions:** The `universe_resolver.py` module exists and is imported into the scoring engine; config has `universe.filters.min_price` set.

**Steps:**
1. Call the resolver for a known as-of date with bars-asof data.
2. Verify each returned symbol has a price ≥ `config.universe.filters.min_price` on or before that date.
3. Verify a name with price < min_price on that date is NOT in the returned set.

**Expected outcome:** Resolver correctly filters by minimum price; no sub-threshold names are admitted.  
**Pass criteria:** All returned names pass the price check; at least one excluded name is confirmed below-threshold in the log/return structure.

---

### TC-03 — Per-as-of-date universe resolver: ADV threshold gates membership

**Type:** api  
**Preconditions:** The resolver is integrated; config has `universe.filters.adv_window_days` and an ADV threshold.

**Steps:**
1. Call the resolver for an as-of date; capture the returned membership set.
2. For a name that WAS admitted, verify its ADV (over the config window) ≥ the threshold.
3. For a name that was NOT admitted, verify either its price or ADV is below threshold (or both).

**Expected outcome:** ADV threshold is applied consistently; no low-ADV names are scored.  
**Pass criteria:** All admitted names meet the ADV threshold; at least one sub-threshold exclusion is documented.

---

### TC-04 — Per-as-of-date universe resolver: minimum-history gate (J-94)

**Type:** api  
**Preconditions:** The resolver reads `indicators.min_history_bars` from config; bars-asof is populated for test data.

**Steps:**
1. Call the resolver for an as-of date.
2. For each returned name, count the trailing bars dated ≤ as-of-date; verify the count ≥ `min_history_bars`.
3. Identify a name that has fewer trailing bars and confirm it is NOT in the returned set.

**Expected outcome:** Names with insufficient history are excluded; the warm-up boundary is enforced.  
**Pass criteria:** All members have ≥ min_history_bars; a sub-threshold name is confirmed excluded with reason "below-history".

---

### TC-05 — Resolver no-lookahead: removing future bars does not change as-of membership

**Type:** api  
**Preconditions:** The resolver is implemented; bars-asof supports tail-truncation testing.

**Steps:**
1. Call the resolver for as-of date D and capture membership set M.
2. Remove all bars dated > D from the data source.
3. Re-call the resolver for the same date D and capture membership set M'.
4. Verify M == M'.

**Expected outcome:** Removing future bars does not alter the resolved membership (tail-invariance).  
**Pass criteria:** M and M' are byte-identical sets.

---

### TC-06 — Universe source repointed: score_stocks iterates resolver membership

**Type:** api  
**Preconditions:** The resolver is integrated into `scoring.py`; a full run completes.

**Steps:**
1. Run a full scan for a known as-of date.
2. Capture the set of tickers in the returned `ScannerResult.`
3. Call the resolver directly for the same as-of date.
4. Verify the set of tickers in `ScannerResult` == the resolver-returned membership.

**Expected outcome:** The scanner scores exactly the resolver's resolved set, no more, no fewer.  
**Pass criteria:** `ScannerResult` tickers ⊆ resolved membership (they may be filtered by regime, but the candidate set is the resolved one).

---

### TC-07 — Forward symbols repointed: per-run membership + benchmarks

**Type:** api  
**Preconditions:** `forward_testing.py` is repointed; forward-returns computation runs.

**Steps:**
1. Run a scan for an as-of date; capture the `ScannerResult` tickers.
2. Compute forward returns; verify the set of forward-tested names includes:
   - All `ScannerResult` tickers (or a subset filtered by regime).
   - Benchmark symbols (SPY, QQQ, sector ETFs) always present.
3. Verify the boundary (entry close on D, exits date > D) is preserved.

**Expected outcome:** Forward returns are computed over the per-run membership ∪ benchmarks, with benchmarks always present.  
**Pass criteria:** Benchmarks appear in every run's forward-returns table; the no-lookahead boundary is byte-identical to the previous implementation (confirmed via byte-equality unit test).

---

### TC-08 — Universe count migration: as-of-dependent resolved size

**Type:** api  
**Preconditions:** `data_manager.py` and `methodology.py` are updated; `GET /api/data` and `GET /api/methodology` endpoints run.

**Steps:**
1. Fetch `GET /api/data?asof=2021-01-04` (early date, before warm-up boundary).
2. Verify `universe_count` == number of names resolved at that as-of-date (expected: small/0).
3. Fetch `GET /api/data?asof=2022-01-01` (after warm-up boundary).
4. Verify `universe_count` == number of names resolved at that date (expected: near full pool).
5. Verify the full-pool candidate count is also served (for comparison).

**Expected outcome:** `universe_count` reflects the as-of-dependent resolved membership, not a global constant.  
**Pass criteria:** Early dates show smaller counts; later dates show full/near-full counts; the candidate-pool count is present in the payload.

---

### TC-09 — Per-date coverage diagnostic: admitted + excluded-by-reason counts

**Type:** api  
**Preconditions:** `compute_coverage` is updated to derive per-date exclusion counts; `GET /api/data` payload includes the diagnostic.

**Steps:**
1. Fetch `GET /api/data?asof=2021-06-01` (warm-up period).
2. Verify the payload includes fields for:
   - `admitted_count` (number of names that passed all filters).
   - `excluded_below_history_count`.
   - `excluded_below_price_count`.
   - `excluded_below_adv_count`.
3. Verify `admitted_count + sum(excluded_*_count) ≈ candidate_pool_size`.

**Expected outcome:** The coverage diagnostic breaks down the exclusions by reason.  
**Pass criteria:** All exclusion reasons are present; the counts sum to the candidate pool (with expected roundoff for thin/no_history).

---

### TC-10 — Membership timeline derivation: per-date size step function

**Type:** api  
**Preconditions:** The timeline derivation is implemented; `GET /api/data` or `GET /api/data/universe-timeline` serves the timeline.

**Steps:**
1. Fetch the membership timeline endpoint for the full date range.
2. Verify it returns an ordered array of {date, resolved_size, entries_count, exits_count, excluded_by_reason_counts}.
3. Verify resolved_size forms a step function (values are stable or change between dates).
4. Verify early dates (2021-01) have resolved_size = 0 or very small; later dates (2022-01+) approach full pool size.

**Expected outcome:** The timeline shows a deterministic step function of universe size over time.  
**Pass criteria:** The size series is monotonic or shows discrete steps (no noise); early dates are small/empty; the function reaches full size ~2022-01.

---

### TC-11 — Membership timeline: entries and exits

**Type:** api  
**Preconditions:** The timeline includes entries/exits per snapshot date.

**Steps:**
1. Fetch the membership timeline.
2. For each date, verify `entries` lists names that appear in that date's snapshot but not in the prior snapshot.
3. For each date, verify `exits` lists names that appeared in prior snapshots but not in that date's snapshot.
4. Verify the timeline is causal: each date's entries/exits are observed only from its own ≤ D snapshot.

**Expected outcome:** Entries and exits are correctly computed and align with the membership step function.  
**Pass criteria:** A name appears in `entries[date]` iff it first appears in the snapshot at that date; exits align with disappearance; no future information is used.

---

### TC-12 — J-95 backward-history control renders with survivorship-bias label

**Type:** browser  
**Preconditions:** Frontend dev server is running; the `/data` page loads.

**Steps:**
1. Navigate to `http://localhost:3000/data`.
2. Scroll to the membership-timeline or coverage section.
3. Look for a "Extend history backward" button or control.
4. Verify the candidate pool or timeline displays a **survivorship-bias label** (text like "current-constituent" or "not point-in-time historical universe").

**Expected outcome:** The backward-history control is present and the survivorship caveat is visible.  
**Pass criteria:** Button/control is clickable; label is readable and mentions survivorship or current-membership.

---

### TC-13 — J-95 backward-history flow: confirm gate + honest blocked state

**Type:** browser  
**Preconditions:** The `/data` page is loaded; the backward-history control is visible.

**Steps:**
1. Click the "Extend history backward" button.
2. Verify a confirm modal appears (reusing J-85 rebuild confirm UI).
3. Click "Confirm" (or equivalent).
4. Observe the fetch attempt; if the data provider is unavailable, verify the UI shows an **explicit blocked/limited-coverage (NA) state** instead of hanging or showing an error.
5. If the provider is available, the flow proceeds to the rebuild.

**Expected outcome:** The control is confirm-gated; unavailable providers surface an honest NA state (non-halting).  
**Pass criteria:** Confirm modal appears; NA state is displayed (not a crash, not a generic error); the UI remains responsive.

---

### TC-14 — J-93 as-of slide: membership changes on /stocks

**Type:** browser  
**Preconditions:** Frontend is running; the as-of date control (global) is visible on the page.

**Steps:**
1. Navigate to `http://localhost:3000/stocks`.
2. Set the as-of date to `2021-01-04` (before warm-up boundary) via the global date control.
3. Observe the stock leaderboard.
4. Verify the universe is empty or very small (< 10 names).
5. Change the as-of date to `2022-01-01` (after warm-up boundary).
6. Observe the stock leaderboard.
7. Verify the universe has grown to near full size (100+ names).

**Expected outcome:** Stepping the as-of date visibly changes the membership on `/stocks`; early dates show honest small/empty universe.  
**Pass criteria:** Leaderboard row count is visibly smaller at 2021-01; larger at 2022-01; no padded/fabricated names at early dates.

---

### TC-15 — J-93 as-of slide: theme/sector membership follows resolver

**Type:** browser  
**Preconditions:** `/themes` and `/sectors` pages are accessible.

**Steps:**
1. Set as-of to `2021-01-04` on the global control.
2. Navigate to `/themes`.
3. Verify theme membership is small or empty (each theme row shows fewer or zero members).
4. Change as-of to `2022-01-01`.
5. Verify theme membership has grown (each theme row shows more members).
6. Repeat for `/sectors` (and `/scanner-runs` if applicable).

**Expected outcome:** All pages reflect the as-of-dependent membership; no page shows a static universe.  
**Pass criteria:** Member counts visibly change with the as-of date; no hardcoded/padded member lists.

---

### TC-16 — J-94 per-date coverage diagnostic: UI displays admitted + excluded counts

**Type:** browser  
**Preconditions:** The `/data` page loads; the coverage panel is visible.

**Steps:**
1. Navigate to `http://localhost:3000/data`.
2. Set the as-of date to a warm-up date (e.g., `2021-06-01`).
3. Look for a "Coverage" or "Diagnostic" panel that displays:
   - Admitted count (names that passed all filters).
   - Excluded count broken down by reason: below-history, below-price, below-ADV.
4. Verify the panel shows plain-language explanations (e.g., "X stocks excluded due to insufficient history").

**Expected outcome:** The diagnostic panel displays the as-of-dependent coverage breakdown.  
**Pass criteria:** All exclusion reasons are shown; counts are readable; the panel updates when the as-of date changes.

---

### TC-17 — J-96 membership timeline renders with step function + entries/exits

**Type:** browser  
**Preconditions:** The `/data` page loads; the membership timeline panel is visible.

**Steps:**
1. Navigate to `http://localhost:3000/data`.
2. Scroll to the membership-timeline section (may be below the fold).
3. Verify the panel displays:
   - A **step-function chart** showing universe size over time (should show 0 or low values before ~2021-10, full size from ~2022-01).
   - An **entries/exits list** showing which names entered/exited on each date.
   - **Excluded-by-reason counts** per date (below-history, below-price, below-ADV).
4. Verify the three **honest labels** are visible:
   - Survivorship-bias caveat (current-constituent).
   - Warm-up boundary explanation.
   - Universe-relative breadth note.

**Expected outcome:** The timeline provides a complete view of universe dynamics; all labels are readable.  
**Pass criteria:** Step function renders (not a blank/missing chart); entries/exits are populated; all three labels are visible and readable.

---

### TC-18 — J-94 empty-universe honest state: no fabrication before warm-up

**Type:** browser  
**Preconditions:** The frontend loads; the as-of control works.

**Steps:**
1. Set the as-of date to `2021-01-04` (definitely before the warm-up boundary).
2. Navigate to `/stocks`.
3. Verify the leaderboard shows **zero rows** or an **explicit "No stocks available"** message.
4. Verify the leaderboard does NOT show padded/fabricated names.
5. Verify `/scanner-runs` for the same date also shows empty or honest minimal results (ETF/regime surfaces may still render from the ETF infrastructure, which is expected).

**Expected outcome:** Early as-of dates show honest empty stock universe; no synthetic data.  
**Pass criteria:** `/stocks` is empty; no error message; the page is responsive (not a loading state).

---

### TC-19 — Required-still-passing: J-06 single source (NVDA leaderboard == detail)

**Type:** browser  
**Preconditions:** Frontend is running; NVDA is in the seed universe at a full-universe as-of date (e.g., 2022-06-01).

**Steps:**
1. Set as-of to `2022-06-01` on the global control.
2. Navigate to `/stocks` and find NVDA in the leaderboard.
3. Note its Leadership Score, Entry Quality Score, Risk Score, and bucket (A–E).
4. Click NVDA to open its detail page.
5. Verify the scores and bucket on the detail page **exactly match** the leaderboard.

**Expected outcome:** Scores are byte-identical across pages (single source of truth).  
**Pass criteria:** All three scores match; the bucket matches; values are not re-computed.

---

### TC-20 — Required-still-passing: J-18 exactly one date selector (no secondary date state)

**Type:** browser  
**Preconditions:** Frontend is loaded; a historical as-of is selected.

**Steps:**
1. Navigate to `/data` (with the new membership-timeline and coverage panels).
2. Use the browser developer tools to search for `<input type="date">` elements.
3. Verify there is **zero such input** on the page.
4. Verify the page reads the single global as-of via `useAsOf()` hook.
5. Repeat for `/stocks`, `/themes`, `/sectors` (and any other affected pages).

**Expected outcome:** No second date state is introduced; the single global as-of is the only date control.  
**Pass criteria:** `<input type="date">` count = 0 on all affected pages; timeline + diagnostic panels read `useAsOf()`.

---

### TC-21 — Required-still-passing: J-07 Risk-Off marks zero Actionable

**Type:** browser  
**Preconditions:** A Risk-Off regime date is known (e.g., 2020-03-16 or later confirmed from seed data).

**Steps:**
1. Set the as-of date to a Risk-Off regime date.
2. Navigate to `/stocks`.
3. Verify the "Regime" label or indicator shows "Risk-Off".
4. Verify the "Actionable" column (or status) shows **zero names** with Actionable status.
5. Verify names may still show "Watchlist" status (allowed in Risk-Off).

**Expected outcome:** Risk-Off regime gates the Actionable status; zero stocks are marked buyable in a Risk-Off regime.  
**Pass criteria:** Regime is Risk-Off; Actionable count = 0; Watchlist entries are present.

---

### TC-22 — Required-still-passing: J-87/J-88 Dashboard panel unchanged

**Type:** browser  
**Preconditions:** Frontend loads; Dashboard page is accessible; a full-universe as-of date is selected (e.g., 2022-06-01).

**Steps:**
1. Set as-of to `2022-06-01` (full universe, risk-on regime).
2. Navigate to `/` (Dashboard).
3. Verify the existing dashboard panels (market regime chart, sector leaders, theme leaders, stock leadership) are present and populated.
4. Verify the layout and styling are unchanged from prior iterations (no visual regressions).

**Expected outcome:** Dashboard is unchanged by the membership-resolver changes.  
**Pass criteria:** All panels render; no visual regressions; the same data as before appears.

---

### TC-23 — Backend test suite GREEN: test_get_data_overview_shape passes

**Type:** artifact  
**Preconditions:** All code changes are merged; the test suite is runnable.

**Steps:**
1. Run `pytest apps/backend/tests/test_api_data.py::test_get_data_overview_shape -xvs`.
2. Capture the output.

**Expected outcome:** Test passes.  
**Pass criteria:** Exit code 0; no `AssertionError`.

---

### TC-24 — Backend test suite GREEN: full pytest suite passes

**Type:** artifact  
**Preconditions:** All code changes are merged; the full backend test suite is runnable.

**Steps:**
1. Run the full backend test suite: `pytest apps/backend/tests/ -x --tb=short 2>&1 | tee /tmp/pytest_full.log`.
2. Monitor for the final summary line (e.g., `845 passed, 0 failed` or similar).
3. Verify exit code = 0.

**Expected outcome:** All tests pass; no failures.  
**Pass criteria:** Exit code 0; final summary shows `0 failed` and non-zero `passed` count.

---

### TC-25 — No-magic-numbers: universe_resolver.py in CALC_FILES

**Type:** artifact  
**Preconditions:** `test_no_magic_numbers.py` is runnable; the new resolver module exists.

**Steps:**
1. Open `apps/backend/tests/test_no_magic_numbers.py`.
2. Verify `universe_resolver.py` is listed in the `CALC_FILES` set.
3. Run `pytest apps/backend/tests/test_no_magic_numbers.py -xvs`.

**Expected outcome:** Test passes; all config-sourced thresholds are verified.  
**Pass criteria:** Exit code 0; no threshold literals found in `universe_resolver.py`.

---

### TC-26 — Anti-goal: no lookahead in resolver (unit test)

**Type:** artifact  
**Preconditions:** A unit test exists for the resolver's tail-invariance property.

**Steps:**
1. Run `pytest apps/backend/tests/test_universe_resolver.py::test_resolver_no_lookahead -xvs` (or equivalent).
2. Verify the test removes bars dated > D and re-runs the resolver, confirming the membership is unchanged.

**Expected outcome:** Test passes; lookahead is ruled out.  
**Pass criteria:** Exit code 0; the test confirms tail-invariance.

---

### TC-27 — Anti-goal: no market-cap fabrication per historical date

**Type:** artifact  
**Preconditions:** Code review / static inspection.

**Steps:**
1. Search `universe_resolver.py` for any reference to market cap or forward-looking valuation.
2. Verify no market-cap threshold is applied in the per-D resolver logic.
3. Verify the spec's dropped-market-cap note is documented in the module docstring or a comment.

**Expected outcome:** Market cap is not applied per historical date; the criterion is documented as dropped.  
**Pass criteria:** No market-cap logic in the resolver; a comment or docstring explains the dropped criterion.

---

### TC-28 — Anti-goal: single source of truth (universe_count migration)

**Type:** artifact  
**Preconditions:** The migration to as-of-dependent `universe_count` is complete.

**Steps:**
1. Search for all occurrences of `len(cfg.universe.symbols)` in the codebase.
2. Verify all occurrences have been replaced with the resolver-based `universe_count` or a direct resolved-set length.
3. Run a unit test that verifies `universe_count == len(resolved_set)` for multiple as-of dates.

**Expected outcome:** Single source of truth is maintained; no hardcoded list lengths remain.  
**Pass criteria:** All previous `cfg.universe.symbols` sites now read the resolved membership; byte-equality tests pass.

---

### TC-29 — Anti-goal: immutability (seed bars un-deletable)

**Type:** artifact  
**Preconditions:** The backward-history clear flow is implemented; `clear_snapshot_set` is called.

**Steps:**
1. Run a test that calls `clear_snapshot_set` for a backward-history rebuild attempt.
2. Verify the function asserts `bars_before == bars_after` (i.e., no bars are deleted).
3. Verify the test passes (the assertion does not fail).

**Expected outcome:** Seed bars are never deleted by the clear step.  
**Pass criteria:** `clear_snapshot_set` asserts `bars_before == bars_after`; the test passes.

---

## Summary

**Total test cases:** 29  
**API tests:** 9 (TC-02 through TC-11)  
**Browser tests:** 10 (TC-12 through TC-15, TC-18 through TC-22)  
**Artifact checks:** 10 (TC-01, TC-23 through TC-29)
