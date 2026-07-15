# goal-mcp-loop-iter-38 Audit Report

**Date:** 2026-07-15
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-23 (watchlist concentration X-ray / B-204) is genuinely achieved: the pairwise correlation
matrix, deterministic clusters, effective-number-of-bets headline+window, and sector/theme/setup
concentration are computed engine-side by one canonical ENB/correlation helper, served as an
additive `xray` field on `GET /api/watchlist`, and re-read verbatim by the page — verified
end-to-end by browser-qa with screenshots (UT-01..UT-11/14/15 PASS) and confirmed correct by code
tracing plus my own re-run of the 24 fast backend tests. The implementation is provably additive
(diffs confirm no shared-logic edit), ledgers are byte-identical, and no proven/advice language or
anti-goal violation is present. The verdict is PASS_WITH_GAPS (not clean PASS) for one open DoD
line — the deterministic golden-replay of the required-still-passing set (J-01/02/03/05/10/13/20)
was not executed this iteration (services torn down; smoke-200 + diff-intersection only) — which is
the recurring systemic framework gap the spec itself flags and explicitly permits closing via an
immediately-following lean verify pass.

---

## 2. Findings

No CRITICAL or IMPORTANT findings. Nothing was fixed — every item below is GAP or OBSERVATION, and
fixing those would be scope creep (the shipped behavior is correct and degrades honestly).

### Backend Findings

**B1 — GAP (gap): config validator misses the `min_overlap_days == corr_window_days` unreachable-floor case**
`apps/backend/app/config.py:2352` rejects only `min_overlap_days > corr_window_days`. Because a
member's return series is one shorter than its bar window (`_returns` yields `len(bars)-1`;
`watchlist_xray.py:52`), the maximum reachable own-history is `corr_window_days-1`, so
`min_overlap_days == corr_window_days` is *also* an unreachable floor — every member would render
NA forever. The validator's own docstring ("an unreachable floor is a config error", line 2337-2338)
intends to reject exactly this. The shipped default (60/126) is unaffected, and a misconfiguration
degrades *honestly* (ENB → NA, no crash, no fabrication), so this is not a shipped defect. The
reviewer already flagged it as MINOR with the one-char fix (`>` → `>=`). Not fixed here: the shipped
config is correct and the failure mode is honest, so changing a boot-validation boundary that the
shipped config never hits is scope creep.

**B2 — OBSERVATION (observation): ENB eligibility is over-conservative for a sufficient-history zero-variance member**
`apps/backend/app/engine/watchlist_xray.py:201` computes `enb_eligible` as sufficient tickers whose
correlation against *every other* sufficient ticker is defined. A flat-price name with ≥
`min_overlap_days` of (all-zero) returns is `sufficient` but its every pairwise correlation is
`None` (zero variance), so it knocks *itself and every other name* out of `enb_eligible`, collapsing
ENB to `None`. This is unreachable for real equity data (no stock holds an identical close for 60+
consecutive trading days) and for the committed seed, and it degrades honestly (ENB renders "NA",
never a fabricated number, never a crash). Documented, not fixed.

**B3 — OBSERVATION (observation): pairwise alignment is positional, which equals date-alignment only for gap-free same-calendar series**
`app.engine.concentration._pair_correlation` (`concentration.py:34-48`) aligns two return series on
their trailing `min(len)` *positions*. For contiguous bars on one trading calendar (all US equities
in this seed) position == date, so the docstring's "a real date alignment" holds and the live
spot-check (MSFT×ABBV) matched an offline computation to 10+ digits (dev handoff). If two members
ever had *divergent internal bar gaps*, positional alignment could pair mismatched dates and present
a subtly wrong correlation as correct (anti-goal #3). Not a defect for this product's single-calendar
seed; a latent edge for irregular/sparse data the spec did not require solving. Documented only.

**B4 — OBSERVATION (observation): canonical rows are fetched twice per `GET /api/watchlist`**
`list_watchlist` calls `_canonical_rows` for entry enrichment (`watchlist.py:115`) and then
`build_xray_payload` independently calls `resolved_run` + `filtered_stock_rows` for the same tickers
(`watchlist_xray.py:210-211`). Two indexed fetches for the same small ticker set — micro-perf only,
no observable impact at watchlist scale. Documented only.

### Frontend Findings

**F1 — OBSERVATION (observation): `enb_member_count` is served and typed but not rendered**
Computed (`watchlist_xray.py:223`) and typed (`lib/api.ts:1115`) but has no render site in
`page.tsx`/`correlation-heatmap.tsx`. Inert on a 2-name list (always equals the visible ticker
count); on a larger list with short-history exclusions a user would see an ENB with no visible
member count. Already self-disclosed in `...-user-visible-changes.md` ("Not Visible Yet") and noted
by ux-regression as a future-pass item — not hidden by omission, and J-23's acceptance does not
require it. Documented only.

### Test Findings

**T1 — GAP (gap): the 4 new `test_api_watchlist.py` tests rest on a single (reviewer) full-file run**
`apps/backend/tests/test_api_watchlist.py:187-245` adds four additive-`xray` tests. The dev deferred
the full-file run (slow `loaded_engine` 30y fixture reaped mid-setup) and QA collected it only
partially; only the reviewer claims a completed run (~60 min, 13 passed). Mitigation is strong: I
re-ran the two fast files myself (`test_concentration.py` + `test_watchlist_xray.py` → 24/24 passed
in 1.41s), and the same four behaviors (additive shape, `status:"ok"`, no-language, determinism)
were independently confirmed by the dev's live production-seed E2E and by browser-qa UT-08/09.
Adequate, but the formal full-file pytest confirmation is single-sourced. Documented.

**T2 — OBSERVATION (observation): no combined 3-ticker composer test for "2 correlated + 1 independent"**
The B-204 fixture (ENB≈2, exact 1.8) is proven at the helper level
(`test_concentration.py::test_b204_fixture_two_correlated_one_independent_series`) and the composer's
2-name cluster merge/split + ENB is proven separately in `test_watchlist_xray.py`; no single composer
test asserts clusters *and* ENB together over the 3-ticker fixture. Reviewer's optional NOTE.
Documented only.

---

## 3. Domain Assessment

The core domain logic is correct and honest.

- **ENB `(Σλ)²/Σλ²`** (`concentration.py:60-79`) via `numpy.linalg.eigvalsh`. Numerically robust:
  for a unit-diagonal correlation matrix `Σλ = trace = N` and `Σλ² = ‖A‖²_F`, so the value stays in
  `[1, N]` regardless of PSD-ness — no NaN/instability. Verified against hand-derived exacts
  (identity→N, all-ones→1, 2×0-corr→2, `[[1,1,0],[1,1,0],[0,0,1]]`→1.8) and the closed-form 2-asset
  case `2/(1+ρ²)`: ρ=−0.114 → 1.9743, matching the dev's live value to 10+ digits. Single-name→1.0,
  empty→None handled directly.
- **`correlation_matrix`** returns honest `None` for undefined/zero-variance/too-short pairs
  (`_pair_correlation`), never a fabricated 0.0. The individual `min_overlap_days` floor guarantees
  ≥ floor pairwise overlap for any two sufficient members (both are trailing windows ending at the
  same as-of), so the honesty floor is sound.
- **Clustering** (`_connected_components`) is deterministic connected components with
  positive-correlation-only edges — the correct semantics for a *concentration* view (names moving
  together; a strong negative correlation is diversifying, not concentrating) — with sorted,
  byte-identical output.
- **Determinism / no-lookahead**: the X-ray is anchored to `latest_data_date` (`watchlist.py:107`),
  never wall-clock; every read is the bounded per-symbol `bars_asof_window` (bars ≤ as-of); the
  determinism test and a live repeat-call check pass. Anti-goals #5 and #8 hold.
- **Nullable-sector** (iter-18/19 lesson): grouped as a real bucket (`_sector_concentration`), never
  dropped, never crashed; null→"Unassigned" display is delegated to the existing `sectorLabel()`
  helper (single source). Verified by test + browser UT-05.
- **Single canonical helper**: grep confirms exactly one `def effective_number_of_bets` /
  `def correlation_matrix` in production code — the B-204 single-source trap is respected.
- **Scope**: strictly additive — no `/evidence` change, no `models.py` schema change, no ML
  clustering, no advice/position concept. The diff touches only the planned files.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issue was found; all findings are GAP/OBSERVATION, which the auditor
documents rather than fixes (fixing them is scope creep, and the shipped behavior is correct and
degrades honestly).

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes required |

---

## 5. Recommended Next Step

Proceed toward closing iteration 38. Before the session marks the required-still-passing set green,
the **immediately-following lean verify pass MUST run the deterministic golden-replay for
J-01/02/03/05/10/13/20** (scripts exist under `runs/goal-session-mcp-loop/journey-scripts/`) — this
is the single open DoD line (T1/§1) and the exact item iter-33 and iter-36 CLOSURE-FAILed on. My
diff-intersection analysis shows those seven journeys have *no plausible regression path* from this
iteration (config change is additive + default-populated; `watchlist.py` GET is additive with
`asof_date`/`entries[]` byte-identical; no shared engine/UI source was edited), so the replay is
expected to be a clean green — but it must be executed, not inferred. Recommended follow-ups for a
future iteration (non-blocking): tighten the `WatchlistXrayCfg` validator to `>=` (B1) and surface
`enb_member_count` in the ENB headline when this section is next touched (F1). The durable framework
fix — adding a deterministic-replay lane to the full `run-phase.sh`/`run-goal.sh` path — remains
owed to the framework maintainer, not to this iteration.
