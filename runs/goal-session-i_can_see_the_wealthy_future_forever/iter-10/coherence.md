**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-10 (J-25 Factor Lab on `/research`)

- **Session:** i_can_see_the_wealthy_future_forever
- **Iteration:** 10 — Factor Lab (`/research`): decile sort + rank-IC per factor
- **Snapshot SHA:** `1217007cb86aff311a5372547c43619ea174658f`
- **Auditor:** coherence-auditor (objective Part A / Part B rules; subjective = advisory)
- **Surfaces audited:** new engine `app/engine/research.py`, new API `app/api/research.py`, new page `app/frontend/app/research/page.tsx`, modified `sidebar.tsx`, `main.py`, `config.py`, `config.yaml`, `lib/api.ts` (per ui-surface-map + diff).

---

## Part A — Data Contract (the "numbers don't match" gate) → PASS

The new value **Factor-Lab analytics** (decile mean return + downside risk-adjusted + rank-IC, each with `n`) is registered in the blueprint Data Contract (`blueprint.md:162`): computed once by `app.engine.research:compute_factor_lab`, served by the single endpoint `GET /api/research/factor-lab`. The diff conforms.

1. **Read-only / no recompute (invariants #1, #2, #9).** `_factor_observations` (`app/engine/research.py:154-181`) issues only `select(ForwardReturn)` and `select(ScannerResult)` — SELECT-only, no writes. The realized return is read verbatim (`ForwardReturn.realized_return`, line 163); the factor value is read verbatim from the stored row — a typed column via `getattr(res, parsed["column"])` or a `record_json` component `raw` (`_extract_factor_value`, line 134-151). No call to `run_scan` / `score_stocks` / `backfill*` / `forward_return` / `detect_*`; the only `forward_testing` import is the `SURVIVORSHIP_BIAS_LABEL` constant (line 40), not a compute fn. **No duplicate computation of any score/return/bucket/factor.**

2. **Single canonical source.** `GET /api/research/factor-lab` (`app/api/research.py:28-59`) returns `compute_factor_lab(...)` verbatim — the view recomputes nothing. Registered in `main.py:81` (`prefix="/api"`). The client helper `fetchFactorLab` (`lib/api.ts`) is a plain GET; the page re-formats only (`fmtPct`/`fmtRatio`) — **no non-canonical source, no client-side recompute.** No other code path computes deciles/rank-IC (forward_testing.py / scoring.py unchanged in the diff).

3. **New value, not a synonym.** The decile means, rank-IC, and risk-adjusted column are NEW descriptive aggregations over the SAME stored pool `compute_forward_aggregates` uses; the factor *values* keep their canonical home (`scoring` → `scanner_results`/`record_json`) and the realized *returns* keep theirs (`forward_testing` → `forward_returns`). This is a read-only slice exactly like the J-19 attribution row — **registered, so not an "unregistered value" WARN.**

4. **Risk-adjusted is downside-only (invariant #9, anti-goal).** `_risk_adjusted = mean / _downside_deviation` where `_downside_deviation = sqrt(mean(min(r,0)**2))`, MAR=0 (`research.py:69-87`). It does NOT reuse `forward_testing`'s total-stdev helper; NA (None) when `dd == 0` or `n < 2` — never a total-vol number.

5. **No fabrication (invariant #8).** Factor-NULL observations are excluded (line 177); empty/low-sample deciles carry honest `n` + `low_sample` flag (NA in UI, line 255-260); rank-IC `value` is None on `n<2`/zero variance. Config validation (`config.py:_factor_lab_sources_resolve`, line ~853) fails boot loudly if any factor `source` does not resolve to a real stored column or a real component in `scores.<block>.weights` — no silent default.

---

## Part B — Information Architecture (the "where do I find it" gate) → PASS

1. **Navigation path exists (invariant #12).** `apps/frontend/components/sidebar.tsx` adds `{ href: "/research", label: "Research", icon: Microscope }` to the `NAV` array (between System Health and Watchlist). Top-level sidebar link ⇒ **1 click from any page** (≤2). Verified statically in the nav file.

2. **Canonical home, no parallel shell.** `/research` is the blueprint-approved top-level home (skeleton `blueprint.md:67`; approval pause cleared iter-10). The new `app/research/page.tsx` lives under the app-router root layout (the shared sidebar shell) and reuses shared components (`PageHeading`, `Card`, `Select`, `EmptyState`, `forward-return` helpers) — it defines **no** layout/nav of its own. No parallel shell.

3. **No duplicate home.** `/research` is a brand-new entity (the research labs); no existing entity is given a second home.

4. **J-18 — exactly one date selector (invariant #5).** The page imports no `useAsOf`/date context and renders no date/as-of picker; its only state is `factor` + `horizon` (`page.tsx:29-30`). `horizon` is a forward-window analysis parameter sourced from `walk_forward.horizons` (server payload) — identical in kind to System Health, **not** an as-of date control. The single global as-of switcher is untouched. J-18 preserved by construction.

---

## Part C — Advisory (non-blocking)

None material. Notes for the record:

- **Formatting consistency:** the page reuses the shared `fmtPct` / `returnClass` / `SampleSize` from `components/forward-return`, matching System Health and Backtest. The new `fmtRatio` is correctly distinct for unitless ratios (risk-adjusted, rank-IC) — a ratio is not a percent, so this is correct, not drift.
- **Config-driven vocabulary (iter-9 lesson honored):** the factor dropdown and horizon group are built from the server `factors`/`horizons` payload, not a hardcoded frontend list (`page.tsx:121-125`, `152-171`) — a config-only factor needs no frontend edit.
- **Consistency invariant** (pooled factor-lab mean at horizon `h` == `compute_forward_aggregates(h).overall.mean_return`) is the evaluator's/unit-test cross-check, not a coherence rule. Note it is exact only for never-NULL typed columns; component-`raw` factors legitimately yield a subset pool because factor-NULL observations are honestly excluded — that is a read-only slice, not a recomputation, so it is outside the FAIL ruleset.

---

## Conclusion

No objective Data-Contract or Information-Architecture violations. The Factor Lab is a read-only aggregation of already-stored forward returns + factor values, served by its single canonical endpoint, reachable in one click from the sidebar under its approved `/research` home, with no second date control. **COHERENCE-PASS.**
