# goal-mcp-loop-iter-22 Audit Report

**Date:** 2026-07-08
**Auditor:** Hard audit pass — skeptical, evidence-based (re-audit after the prior FAIL + dev fix pass)

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal — surfacing the deep, vendor-labeled `^SPX`/`^NDX`/`^DJI` (to 1996) + `^VIX`/`^TNX`
context on the live Dashboard chart and disclosing per-series vendor on `/data` — is genuinely
achieved. I independently verified the whole chain: the backend emits correct additive `vendor`/`first`
fields sourced from the single `meta.json` parse (never `points[0]`), the existing lines' `points` math
is byte-identical, the 3 deep symbols are loaded in the live DB from `1996-01-02` (590 distinct symbols,
7,674 bars each), the scoring universe is structurally isolated from `index_chart.symbols` (no leak),
and the prior audit's CRITICAL F1 defect (deep 1996 history hidden by the `lightweight-charts`
bar-spacing floor) is fixed and empirically confirmed. Remaining items are documented GAPs/OBSERVATIONs
— none compromises the goal: J-13 was not dedicatedly live-replayed (its availability-heatmap denominator
honestly moved 587→590), `^TNX`'s disclosed "First bar" conservatively understates its DB history, and
the canonical browser-QA report-of-record still carries the stale pre-fix FAIL.

---

## 2. Findings

### Backend Findings

**B1 — verified-correct (no action): additive `vendor`/`first` are sourced honestly; existing math untouched**
`apps/backend/app/engine/indexes.py:135,153,156-164`. `compute_index_series` reads
`load_seed_meta(seed_dir)` once, and the existing `points` line (`:153`,
`round((bar.close / base - 1.0) * 100.0, 4)`) is character-for-character unchanged in the diff — the only
delta to each entry is the additive `vendor`/`first` keys. `vendor` maps via `_vendor_label`
(`:40-52`, stooq/yahoo/fred-macro-proxy → Stooq/Yahoo/FRED-macro proxy; `None` when absent — no fabricated
vendor). `first` is taken from `meta_row.get("first")` (the manifest), **not** `points[0]["date"]`. DoD
byte-identity of SPY/QQQ/IWM/RSP/DIA is therefore structurally guaranteed and pinned by the unchanged
hand-computed tests plus `test_full_mode_default_is_byte_identical_clamped` (`tests/test_indexes.py:406`).

**B2 — verified-correct (no action): single `meta.json` parse, honest degrade**
`apps/backend/app/engine/data_manager.py:959-1012`. `load_seed_meta` (new, `:991`) and the pre-existing
`load_seed_windows` (`:974`) both build from ONE `_read_seed_meta_rows` helper (`:959`) — there is still
exactly one `json.loads(meta.json)` call site. An absent/unreadable manifest yields `{}` (→ `vendor:None`,
`first:None`), proven by `test_missing_seed_meta_yields_null_vendor_and_first` (`tests/test_indexes.py:589`).
`load_seed_windows`' signature/return are unchanged, so its J-39 caller and test were untouched.

**B3 — verified-correct (no action): no index-symbol leak into the scored universe**
`config.yaml` adds the 5 carets to `index_chart.symbols` only; `etfs.index` remains `[SPY,QQQ,IWM,RSP]`
(no carets). The scored universe reads `universe.symbols`/`etfs.index`, never `index_chart.symbols`
(`grep` confirms `index_chart.symbols` is consumed only by `seed_loader.all_seed_symbols:62` for the LOAD
scope and by `indexes.py` for the CHART — the DIA precedent). Live DB confirms leaderboard/universe stayed
541 (QA UT-14/UT-16 DOM-scanned all 541 rows, zero carets).

**B4 — verified-correct (no action): targeted idempotent loader is additive-only**
`apps/backend/scripts/load_missing_index_symbols.py:62-87`. Per-symbol `COUNT(*)` pre-check skips
already-loaded symbols (idempotent), reads the same committed `SeedProvider` fixture `load_prices` uses,
honestly skips a symbol with no committed CSV (`ProviderUnavailableError → continue`), inserts only into
`daily_prices`, and commits only if something loaded. Independently re-verified in the live DB: 590
distinct symbols; `^SPX`/`^NDX`/`^DJI` = 7,674 rows each, `first=1996-01-02` — byte-matching `meta.json`
and DoD's `^SPX first = 1996-01-02`.

**B5 — GAP: adding the 3 symbols honestly shifts the `/data` availability-heatmap denominator (587→590), not re-verified**
`apps/backend/app/engine/data_manager.py:905` — `compute_availability.total_symbols` is a live
`COUNT(DISTINCT DailyPrice.symbol)`, and per-date `symbols_with_bars` (`:915`) counts distinct symbols per
day. Loading `^SPX`/`^NDX`/`^DJI` moved this denominator 587→590 and ticks the 1996–2026 per-date counts up
by 3. This is the **intended, honest** consequence of the iteration (the heatmap is designed to reflect
actual stored coverage), not a break — UT-02 confirms the panel renders populated without crashing. But
J-13 (a required-still-passing journey whose home is this exact surface) was **not dedicatedly
live-replayed** (ux-regression flagged the same coverage gap). If J-13's golden pins the pre-587 count, it
is a stale assertion to refresh (the iter-21 "intended additive change" lesson the spec itself cites), not
a regression. Component `availability-heatmap.tsx` is content-identical to HEAD (`git diff` empty), so code
risk is low; only the exact-count re-validation is missing.

### Frontend Findings

**F1 — verified-fixed (prior CRITICAL): deep 1996 history is now the default view on the LIVE chart**
`apps/frontend/components/phase-cross-view-chart.tsx:162` adds `minBarSpacing: 0.02` to the `timeScale`
(the `fitContent()` at `:326` is unchanged). The analysis is sound: `lightweight-charts` 5.2.0's default
0.5 px/bar floor forces `fitContent()` to clamp at the most-recent ~2,084 of ~7,674 bars in a ~1,042 px
pane (exactly the pre-fix `2018-02-09→2026` window UT-03 measured); at 0.02 px/bar the full window needs
only ~154 px, so nothing clamps. **Empirically confirmed** by comparing evidence: the pre-fix
`UT-03-fail-fullpage.png` shows the x-axis starting `2018-02-09` with every line already at +148%…+994%,
while the post-fix `TC-01-chart-area.png` (17:30, after the fix) shows the lines starting near **0%** at
the far-left edge — which can only occur if the view begins at the 1996 rebase base (each series is
rebased to its first in-range bar). This matches the dev's live check (left-edge hover → `1996-03-25`) and
QA's TC-01 re-run PASS. DoD (a) is met on the actual rendered surface.

**F2 — verified-fixed (prior MINOR): `IndexSeries.first` is nullable**
`apps/frontend/lib/api.ts:471` — `first: string | null` (and `vendor: string | null`, `:470`), matching
the backend contract (`first:null` for a symbol with no manifest row). Additive/optional, so no typed
consumer breaks; `tsc --noEmit` clean. `index-vendor-panel.tsx:100` passes it through `formatIsoDate`,
which the type system confirms accepts `null` (renders "—").

**F3 — verified-correct (no action): vendor labels, palette, and `/data` panel are honest and byte-exact**
Legend/tooltip render `vendor` only when present (`phase-cross-view-chart.tsx:450,369`); the 5 ETF lines
carry no tag (UT-04/UT-05/UT-08 DOM-verified byte-exact across all three vendor categories). The palette
was extended 5→10 (`:45-48` + 4 additive `globals.css` tokens; `git diff` shows 0 deletions, no existing
token changed) and all 10 swatches are distinct (UT-06 RGB extraction). The `/data` panel
(`index-vendor-panel.tsx`) lists all 10 series with honest `—`/vendor + first-bar date and its own
loading/error/empty states (UT-07 byte-exact; UT-10 whole-backend-down honest). `^TNX` reads as
"10Y-2Y spread proxy (^TNX)" / "FRED-macro proxy" — never as a market index (anti-goal held).

**F4 — GAP: `^TNX`'s disclosed "First bar" (2021-01-04) understates its charted history (~2005)**
The `/data` "First bar" column shows `^TNX = 2021-01-04` (read from `meta.json` per spec), but the live DB
holds `^TNX` bars back to `2005-02-28` (independently confirmed: 1,363 rows, first `2005-02-28`), so the
chart's `^TNX` line renders ~16 years further left than its disclosed "First bar." This is a cross-surface
inconsistency the spec did not anticipate, but it is **spec-compliant** (DoD explicitly requires `first` to
byte-match `meta.json`), **conservative** (it understates, never overstates, available history),
**confined** to one honestly-labeled macro proxy, and **documented** (dev handoff Known Issues). It is a
pre-existing DB data-state artifact (stale pre-2021 `^TNX` bars from before the 30-year swap); the spec
forbids re-fetching/trimming `^TNX` (goal.md §H), so no in-scope fix exists. Documented, not fixed.

### Test Findings

**T1 — verified-strong (no action): the `first`-from-manifest footgun is directly guarded**
`tests/test_indexes.py:536` inserts bars starting `2026-01-01` while the manifest says `first=2005-02-25`/
`1999-03-10`, then asserts the emitted `first` equals the MANIFEST date — a tight test that would fail if
`first` were ever sourced from `points[0]`. Vendor mapping (`:563`) and null-degrade (`:589`) are equally
tight. This is exactly the plan's Risk #5.

**T2 — OBSERVATION: the API-level byte-identity test did not finish; unit-level coverage is sufficient**
`tests/test_api_indexes.py`'s new additive-field test needs the expensive session-scoped `loaded_engine`
fixture (full 30-year/590-symbol bootstrap) and did not complete in-window (a known, pre-existing suite
cost, not introduced here). Byte-identity is nonetheless covered at the unit level (B1) and by the live
`curl /api/indexes` check (QA TC-04). No correctness gap — only a slower test that should be confirmed
green when the fixture finishes.

**T3 — OBSERVATION: the canonical browser-QA report-of-record still reads FAIL (stale, pre-fix)**
`reports/phase-goal-mcp-loop-iter-22-ui-test-results.md` header still says `FAIL` (UT-03, pre-fix) and was
not regenerated after the F1 fix; the post-fix PASS lives in `reports/qa/goal-mcp-loop-iter-22-qa.md`
(TC-01) + `TC-01-chart-area.png`. The substance is fine (I verified the fix), but the FAIL-of-record and
the PASS re-run should be reconciled so a downstream gate does not read the stale FAIL.

---

## 3. Domain Assessment

The core domain logic is honest and correct. This is a pure surfacing/disclosure iteration (no evidence
claim, no referee gate), and it respects the product's skeptical posture throughout: vendors are
conditionally rendered (null → nothing, never a fabricated source), the `first` date is sourced from the
authoritative committed manifest and tested against the exact "don't use the range-clamped point" footgun,
the FRED-macro proxy is honestly named at both the display-name and vendor-badge level, and the deep
indices are structurally barred from the scored universe (presentation-only, the established DIA pattern).
The byte-identity constraint on existing lines is met by construction, not just by assertion. The F1 fix is
the right kind of fix — a minimal, well-reasoned library-config change at the single rendering choke point,
not a rewrite — and it demonstrably turns the invisible-by-default deep history into the default view. The
only honesty wrinkle (F4) is confined to one proxy line, points in the conservative direction, and is a
consequence of following the spec's own `first`-from-manifest mandate against a pre-existing stale-DB
artifact the spec forbids touching.

---

## 4. Fixes Applied During This Audit

None. Every finding is GAP or OBSERVATION level; the two prior blocking findings (F1 CRITICAL, F2 MINOR)
were already fixed by the dev pass and are re-verified here. Fixing B5/F4/T2/T3 would be scope creep or is
explicitly out of scope (F4's only "fix" — re-fetching/trimming `^TNX` — is forbidden by goal.md §H).

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No code changes applied during this audit. |

---

## 5. Recommended Next Step

**Proceed.** The phase goal is achieved and independently verified. Before/alongside the next iteration,
close these documented gaps (none blocking):

1. Capture a dedicated **J-13 live replay** (availability legend fill-vs-snapshot distinction, hover
   tooltip, the Fetch pool) and, if its golden pins the availability denominator, refresh it 587→590 as an
   intended additive change (B5).
2. **Reconcile the canonical browser-QA report** so `ui-test-results.md` reflects the post-fix PASS rather
   than the stale UT-03 FAIL (T3), and confirm `test_api_indexes.py` finished green (T2).
3. Consider a future clarification of `^TNX`'s "First bar" semantics (e.g., label it as the manifest
   window, or reconcile the stale pre-2021 DB bars) so the `/data` disclosure and the chart line agree
   (F4) — low priority, conservative direction, one proxy line.
