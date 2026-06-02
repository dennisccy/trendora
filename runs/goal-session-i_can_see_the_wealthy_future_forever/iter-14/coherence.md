**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-14 (J-29 Setup & Pattern Lab / event study + stored MAE/MFE excursion path)

- **Session:** i_can_see_the_wealthy_future_forever
- **Iteration:** 14
- **Snapshot SHA audited:** `1467e8f42279cdf79b833f1f253b737c4a5e92fa` (`git diff` against it; uncommitted working tree)
- **Surfaces:** `/research` gains a third lab section (Setup & Pattern Lab); backend adds 2 new Data-Contract values. No new page/route/nav entry.

No objective Step-1 (Data Contract) or Step-2 (Information Architecture) violation found. Both new values are registered in the blueprint, computed once in a single canonical place, and read verbatim everywhere else. Clean pass.

---

## Step 1 — Data Contract check (the "numbers don't match" gate)

Two NEW values are registered (blueprint.md lines 179 & 181) and the code conforms to both:

**1. Per-(run, symbol, horizon) MAE/MFE excursions — single producer, single storage.**
- Computed exactly once by the pure helper `forward_excursions(...)` (`forward_testing.py:123-145`) inside the SINGLE forward-return INSERT path `_insert_run_forward_returns` (`forward_testing.py:251-264`), reusing the SAME `post_bars`/`entry_close`/`horizon` already in hand (no extra query, no second formula). MAE = `min(low_i)/entry_close − 1`, MFE = `max(high_i)/entry_close − 1` over the first `horizon` post-bars (date > D).
- Shares `forward_return`'s exact NA gate (None when entry missing/zero or `< horizon` post-bars) → a row exists iff `realized_return` does; never a fabricated/truncated excursion.
- Stored append-only on `ForwardReturn.mae`/`.mfe` (`models.py:276-279`, `Optional[float]` default `None`) — the separate forward table; no `scanner_runs`/`scanner_results`/`*_scores` row is UPDATEd (append-only/immutable preserved).
- **No standalone endpoint** — surfaced only through the event study. Confirmed: research.py exposes exactly 3 routes (`factor-lab:43`, `factor-combination:77`, `event-study:159`); no MAE/MFE route exists. ✓

**2. Setup & Pattern event-study analytics — single canonical computer + endpoint, read-only.**
- Computed once by `compute_event_study(...)` (`research.py:644-...`), served verbatim by the SINGLE canonical `GET /api/research/event-study` (`api/research.py:159-193`, returns the engine result verbatim). No other path computes the event study. ✓
- **Read-only (the keystone):** `_event_study_members` (`research.py:548-...`) issues ONLY `select(ForwardReturn)`, `select(ScannerResult)`, `select(ScannerRun)` and reads `realized_return`/`mae`/`mfe`/`regime_label`/`sector`/`setup_status`/`is_<pattern>` VERBATIM. It calls NO `run_scan`/`score_stocks`/`backfill*`/`forward_return`/`forward_excursions`/`detect_*`/`score_regime`. All downstream math is pure stats. ✓
- **Reuses canonical helpers — no duplicate computation:** `_distribution`/`_mean_or_none` imported from `forward_testing` (`research.py:41-45`); `_risk_adjusted`/`_downside_deviation`/`RESEARCH_CAVEAT` are the pre-existing research.py definitions (`research.py:52, 75, 84`) — the diff redefines none of them (verified: no new `def _risk_adjusted`/`_downside_deviation`/`RESEARCH_CAVEAT =` lines added). Risk-adjusted is downside-only everywhere (`return_per_downside_dev` = mean/downside-dev; `return_per_mae` = mean/mean-|MAE|); no total-volatility ratio introduced. ✓
- **Not a duplicate of an existing value.** Realized returns keep their home (`forward_testing`→`forward_returns`, served by `/api/system-health` + `/api/backtest`); MAE/MFE keep theirs (value #1); setup/pattern flags keep theirs (`scoring`/`scanner`). The event study registers only the NEW descriptive aggregation over them — the same read-only-slice pattern as J-19 attribution / J-25–J-27 lab values.
- **Consistency invariant is read-only, not a recompute.** The spec/blueprint bind the event-study pooled mean to `compute_forward_aggregates(h)`'s `by_setup`/`by_<pattern>` cohort mean. This is an equality over the SAME stored observations (both `mean()` the same stored `realized_return` rows) — not a second computation. The pattern-subject pool uses the stored `is_<key>` mirror flag, the identical grouping `forward_testing`'s `by_<pattern>` uses. ✓
- **Config-driven vocabulary (No magic numbers).** `subject_catalog` (`research.py:514-...`) derives subjects from `setups.ALL_STATUSES` + `config.patterns` keys, labels from `config.methodology.entries` — no hard-coded subject list; `min_sample`/`horizons`/`default_horizon` reused from `walk_forward`. `test_no_magic_numbers.py` scan extended for the additions (`forward_testing.py`/`research.py` already in `CALC_FILES`). ✓

Both new values appear in the Data Contract (no "unregistered value" advisory). No new function recomputes a registered canonical value; no UI surface fetches a registered value from a non-canonical source.

## Step 2 — Information Architecture check

- **Additive section on the existing approved home.** Only `apps/frontend/app/research/page.tsx` is modified (+419/−1); no new `page.tsx`/route directory was created (`git status` shows just the one modified route file). `EventStudyLab` is rendered as a sibling below the existing Factor Lab + Combination Lab (`page.tsx:27`), reusing the page's shared `horizon` prop. ✓
- **Reachable in ≤2 clicks.** `/research` is a top-level persistent-sidebar entry (`components/sidebar.tsx:38` → `{ href: "/research", label: "Research" }`, approved iter-10). The new section is on that page → 1 click. ✓
- **No duplicate home / no parallel shell.** No second page for an entity that already has a home; the section reuses the established lab shell, `CaveatBanner`, `HorizonSelector`, and palette tokens. ✓
- **J-18 preserved (exactly one date selector).** `fetchEventStudy` (`lib/api.ts:97-106`) hits `/api/research/event-study` with only `subject`/`horizon` params — no `as_of`. The endpoint takes no date param. The page introduces no new date/as-of state (the sole `as_of` mention in the page diff is a comment disclaiming one); the section adds only a subject selector + the shared horizon. Client renders payload verbatim — no client-side return/excursion recompute. ✓

## Step 3 — Subjective observations (advisory only)

None material. The blueprint was updated consistently with the iteration spec's "Data-contract additions" (nav note iter-14 at line 82, J-29 journey-home row at line 114, the two Data-Contract rows at 179/181, and invariant #9 extended to name the event study + stored MAE/MFE) — additive, no contradiction with prior rows. Labels and NA + n formatting follow the existing lab conventions; no formatting drift observed.

---

## Decision

- Step 1: **PASS** — both new values computed once in their canonical place; event study is SELECT-only and reuses canonical helpers; no duplicate computation, no non-canonical source, no unregistered value.
- Step 2: **PASS** — additive section on the existing 1-click `/research` home; no new nav/route/parallel-shell/duplicate-home; J-18 second-date-state guard intact.

**Verdict: COHERENCE-PASS** — no objective violations; no advisory notes requiring next-iteration tidy.
