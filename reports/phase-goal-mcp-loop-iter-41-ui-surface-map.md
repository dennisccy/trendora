# Phase goal-mcp-loop-iter-41 — UI Surface Map

**Phase:** goal-mcp-loop-iter-41
**Date:** 2026-07-15
**Written by:** ui-impact-analyst

---

Context for the table below: `apps/backend/app/engine/forward_testing.py` gained two pure per-observation
helpers (`underwater_days`, `time_to_recover_days`, computed alongside the existing `max_drawdown` with
zero extra bar reads) and a new aggregation, `compute_drawdown_expectations` — resolving a claim's cohort
via the same selectors `compute_samples` uses, joining each observation to its causal market phase, and
emitting per-phase `{median, p90, n}` cells plus a walk-forward-cadence loss-streak cell. This is served,
**not as a new endpoint**, but as an additive `expectations` field threaded onto every row of the
already-consumed `GET /api/evidence` (`apps/backend/app/api/evidence.py` / `engine/evidence.py`), behind a
new `compute_drawdown_expectations_cached` wrapper added mid-iteration to fix a discovered ~3x latency
regression. The single frontend page that reads `GET /api/evidence` — `/evidence` — renders the field via
one new component, `DrawdownExpectationsPanel`, appended inside every existing claim card. Verified against
the live, freshly-rebuilt database (`GET http://localhost:8255/api/evidence`, all 7 real ledger claims)
while writing this map, so the specific figures cited below are real served values, not hypothetical.

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/evidence` | `DrawdownExpectationsPanel` (`data-testid="evidence-expectations-panel"`), appended inside `ClaimRow`'s `CardContent` | New component | J-25: additive phase-conditional drawdown/dry-spell history per certified claim | Open `/evidence`; on the FIRST claim card (Hypothesis chips read `factor=leadership_score`, `decile=10`, `horizon=20`), scroll past the existing 5-field grid and confirm a "Historical drawdown & dry-spell expectations (20-day hold)" heading plus a 5-row table (`data-testid="evidence-expectations-table"`) appear below it, separated by a top border. |
| `/evidence` | Distribution cells — "Max-DD depth" / "Underwater" / "Time to recover" columns (`DistributionCellView`) | New table content | Displays server-computed median/p90/n per phase, read verbatim — never recomputed client-side | On that same first card's **Expansion** row, confirm "Max-DD depth" reads exactly `-7.70% (p90 -3.72%) n=1264`, "Underwater" reads `20.0d (p90 20.0d) n=1264`, and "Time to recover" reads `0.0d (p90 6.0d) n=769` — note the smaller `n=769` is correct (only 769 of the 1264 observations recovered within the horizon; the rest are honest NA, not zeroed). Max-DD depth byte-matches the independent offline re-derivation recorded in `reports/perf-budgets.md` Item I. |
| `/evidence` | "Longest losing streak" column, honesty-floor state (`LossStreakCellView`) | New state (insufficient) | A below-floor phase must read "insufficient (n=…)", never a fabricated streak length | On the same first card's **Correction** row, confirm "Longest losing streak" reads `insufficient (n=5)` (5 walk-forward cadence dates, below the configured `streak_min_n=10` floor) rather than a number — note the row's other three columns DO show real numbers for Correction (only the streak cell is floor-limited here, since its own `n` counts cadence dates, not raw observations). |
| `/evidence` | Full-row zero-observation state, all 4 measure columns | New state (zero-observation cohort) | A claim/phase combination with zero cohort observations must degrade honestly across every column, never a 500, crash, or fabricated cell | Open the **SECOND** claim card (top badge cluster reads "FAIL" + a "Regime: Risk-on" badge; Hypothesis chips include `kind=event-study`, `subject=Breakout-watch`); confirm its **Correction** row AND its **Bear** row each read `insufficient (n=0)` in all four columns — a realistic case, since a "Risk-on"-only cohort naturally has almost no entries during Bear/Correction phases. |
| `/evidence` | Method note + survivorship caveat text (`data-testid="evidence-expectations-method-note"` / `"evidence-expectations-survivorship"`) | New content | Transparency requirement — the counting method and the survivorship-bias caveat must be visible verbatim on every card, not summarized or omitted | Confirm every one of the 7 claim cards shows, below its table, the sentence starting "Longest losing streak is counted at the walk-forward cadence…" and a second sentence starting "Walk-forward evidence now spans up to ~30 years of history…" and ending "…Read the edge as an upper bound, not a guarantee." — identical wording on all 7 cards. |
| `/evidence` | Phase badges inside the new table (`<Badge variant="default">{phase}</Badge>`) | Changed visual (MINOR, reviewer-flagged) | Diverges from the app's single-source phase-color mapping (`lib/phase.ts`) that every OTHER phase badge in the product uses | Compare a "Bear" badge inside the new table against the phase badge shown on the main dashboard (`/`, market-phase card); confirm the new table's badges are flat neutral gray for every phase (no color differentiation) while the dashboard's phase badge is color-coded by severity — a cosmetic-only gap tracked as MINOR in `reports/reviews/goal-mcp-loop-iter-41-review.md`, not a data error. |
| `/evidence` | `DrawdownExpectationsPanel` absent state (component returns `null`) | New graceful-degradation state | An unresolvable cohort or a session-less API payload must render nothing for the panel section — never an error boundary or empty placeholder box | Not currently reproducible by clicking through the live ledger (all 7 claims resolve non-null `expectations` today). Instead: `curl http://localhost:8255/api/evidence` and confirm none of the 7 claim objects is missing the `expectations` key; separately confirm by reading `apps/frontend/app/evidence/page.tsx` (the `DrawdownExpectationsPanel` function) that it returns `null` before rendering anything whenever `expectations` is falsy. |
| `/evidence` | Existing `<dl>` field grid + verdict `Badge` (regression guard) | Unchanged (required-still-passing J-01/J-05) | The pre-existing fields must not shift, reorder, or change value when the new panel is appended below them | On any claim card, confirm the "Out-of-sample verdict" badge still reads `FAIL` for all 7 cards (0/7 PASS today) and the five existing fields (Hypothesis, Out-of-sample verdict, Control comparison, Registration date, Forward-walk score-to-date) render exactly as before, with the new panel appearing strictly below them — never interleaved into the existing grid. |
| `GET /api/evidence` (API, consumed by `/evidence`) | Response field `claims[].expectations` | Changed response shape (additive field) | Backend change the frontend now consumes; every pre-existing field must stay untouched | Fetch `http://localhost:8255/api/evidence` directly (or inspect the Network tab while on `/evidence`); confirm each of the 7 claim objects carries a non-null `expectations` object with keys `horizon`, `min_sample`, `streak_min_n`, `survivorship_bias`, `method_note`, and a 5-entry `by_phase` array (`Expansion, Pullback, Correction, Bear, Recovery`, in that order), while `signal`, `claim`, `verdict`, `proven`, `register_date`, `forward_walk` are unchanged from before this iteration. |
| `/evidence` (page-level) | Data load timing after a DB rebuild | Changed behavior (performance, cache-cold vs. cache-warm) | New per-request cohort computation is expensive; a cache keeps steady state fast but the first request after any rebuild is slow | Do not trigger a fresh full DB rebuild solely to test the cold path (destructive, multi-minute operation). Instead, confirm the current steady state: reload `/evidence` now and confirm the page's data returns in well under 1 second — consistent with the 6–17 ms warm-cache `/api/evidence` latency recorded in `reports/perf-budgets.md` Item I (vs. the one-time 9.471 s cold-cache measurement recorded there). |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/models.py` — two new nullable `ForwardReturn` columns (`underwater_days`, `time_to_recover_days`) storing raw per-observation path stats — no independent UI surface of their own; only the phase-aggregated median/p90/n reaches the page, never the raw per-row values.
- `apps/backend/app/db.py` — registers the two columns in `_ADDITIVE_COLUMNS` so a live database that is not rebuilt this pass degrades to NULL instead of a 500 — infrastructure/migration plumbing only, no UI surface.
- `apps/backend/app/config.py` + `config.yaml` — `walk_forward.underwater_horizons` / `.streak_min_n` — runtime thresholds that shape what the panel is willing to show; not rendered as UI elements themselves (no settings page exposes them).
- `apps/backend/data/trendora.db` full rebuild (not tracked in git; run twice this iteration) — an operator action that populated the two new columns across the full ~30-year/590-symbol history so the deep historical phases (Correction/Bear 2000/2008/2020/2022) clear the honesty floor; the rebuild itself has no UI — only its downstream effect (real numbers instead of universal NULLs) is visible, and is what the table rows above actually exercise.
- All test files — `test_forward_testing.py`, `test_evidence.py`, `test_db.py`, `test_config.py`, `test_config_engine.py`, `test_indexes.py`, `test_sectors.py`, `test_themes.py`, `apps/frontend/lib/evidence.test.ts` — verification code, no UI surface.
- `reports/perf-budgets.md` — measurement documentation (memory + latency), no UI surface.

---

## Summary

- **Frontend surfaces changed:** 1 (the `/evidence` claim-card panel — one code change, applied identically across all 7 rendered claim cards)
- **New pages/routes:** 0 — additive section on an existing page only, no new route
- **Modified components:** 4 (`ClaimRow` extended + 3 new: `DrawdownExpectationsPanel`, `DistributionCellView`, `LossStreakCellView`), plus supporting non-visual additions in `lib/evidence.ts` (4 new types + 3 new formatters: `insufficientLabel`, `formatDays`, `formatStreak`) and `lib/api.ts` (re-exports only)
- **Navigation changes:** no
- **Backend-only changes:** 6 (models.py, db.py, config.py/config.yaml as one config change, the DB rebuild, the test-file group, perf-budgets.md — `forward_testing.py`'s new aggregation and `api/evidence.py`/`engine/evidence.py` are excluded from this count because their output IS UI-visible, per the table above)
