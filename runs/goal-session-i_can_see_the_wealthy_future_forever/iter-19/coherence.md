**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-19 (J-32: Research point-in-time toggle, All-history ⟷ As-of-date)

- **Session:** i_can_see_the_wealthy_future_forever
- **Iteration:** 19 — target **J-32** (the last buildable journey)
- **Snapshot SHA audited:** `d735c27882e519d9d690b9c7c5f6eedb0e7b7afc`
- **Diff scope:** `engine/research.py`, `api/research.py`, 2 backend test files, `app/research/page.tsx`, `lib/api.ts`, `blueprint.md` (+ framework trace/telemetry). All in-scope; **none** of the out-of-scope files (`scoring.py`/`scanner.py`/`regime.py`/`patterns.py`/`buckets.py`/`forward_testing.py` storage/`snapshot_serving.py`/`asof-provider.tsx`/`stocks/page.tsx`/`backtest/page.tsx`) was touched → J-06/J-07 structurally byte-identical, no DB regen.

No objective Part A (Data Contract) or Part B (Information Architecture) violation found. The iteration is a clean, mechanical refinement of three EXISTING Data-Contract values that reuses the proven iter-17 as-of seam verbatim.

---

## Part A — Data Contract check (the "numbers don't match" gate): PASS

**No new value, no new endpoint, no second computation.** The three lab values keep their single canonical homes — `compute_factor_lab` / `compute_factor_combination` / `compute_event_study`, each served by its existing endpoint `GET /api/research/{factor-lab,factor-combination,event-study}`. The endpoint list is exactly the 3 pre-existing routes (`api/research.py:53,97,187`); no route added.

1. **`as_of` is a pure read-only membership FILTER, not a recompute.** All three observation builders gain the identical, SELECT-only clause (`engine/research.py:178-182`, `366-371`, `682-687`):
   ```
   fr_stmt = select(ForwardReturn).where(ForwardReturn.horizon == horizon)
   if as_of is not None:
       fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
           ScannerRun.asof_date <= as_of)
   ```
   This is the `forward_testing.compute_forward_aggregates` seam verbatim. The cutoff reads the **canonical** `ScannerRun.asof_date` (not the denormalized `ForwardReturn.asof_date`). Because `runs_with_fr`/`results`/`run_rows`/regime map all derive from `fr_rows`, the one clause scopes the whole pool. Upholds invariants #2 (no recompute in read path), #4 (no lookahead — no run dated > D contributes), #9 (lab analytics read-only).

2. **`as_of=None` is byte-identical all-history.** The `if as_of is not None:` guard adds no clause in the default path; the opening query is unchanged from the prior all-history form. The all-history regression guard is preserved.

3. **No forbidden recompute introduced.** Grep of `engine/research.py` for actual calls to `run_scan`/`score_stocks`/`backfill*`/`forward_return*`/`detect_*`/`score_regime`/`forward_excursions` → **0 calls**; the tokens appear only in docstrings describing what the module does NOT do (`:12,499,880`). The as-of mode only chooses WHICH stored observations are pooled.

4. **API uses the canonical date resolver, not a hand-rolled one.** Each endpoint resolves the cutoff via the SHARED `snapshot_serving.resolved_date(session, as_of, cfg)` (`api/research.py:89,182,226`) — the same resolver as `/api/stocks?as_of=` / `/bars?as_of=` (422 unparseable / 400 future-or-before-history). Consistent date-resolution path, no divergent validation.

5. **New `asof_date` payload field is a context echo, not a new canonical value.** Each payload echoes `as_of.isoformat() if as_of else None` (`engine/research.py:334,601,894`; types `lib/api.ts:747,853,959`). This is the same "resolved `asof_date` echoed by every re-pointed read endpoint" pattern already registered for snapshot-serving in the Data Contract — a re-display label, not a computed/duplicated value. No A4/A5 violation: nothing conceptually duplicates an existing value, and no genuinely-new displayed value goes unregistered.

The blueprint's three lab Data-Contract rows were annotated (not duplicated) with the optional `as_of` cutoff (`blueprint.md:183,185,191`), and invariant #5 updated to cover the Research toggle (`:201`) — matching how iter-17 annotated `compute_forward_aggregates`.

## Part B — Information Architecture check (the "where do I find it" gate): PASS

- **No new page/route/nav entry.** The two new components (`AnalysisModeToggle`, `ModeContext`) and the three re-pointing labs all live on the EXISTING `/research` page (ui-surface-map: 0 new pages/routes, no navigation change). `/research` remains the single canonical home for the labs.
- **No parallel shell / no duplicate home.** Components are added inside the existing `ResearchPage` layout under the established sidebar shell; no second "results" home for any entity.
- **No re-approval needed and none claimed.** `state/blueprint.reapproval-requested` is correctly **absent** (no nav-skeleton change), matching the spec and the iter-19 blueprint note (`:90`).

## J-18 — Exactly one date selector (coherence invariant #5; the principal anti-goal risk): PASS

- **No second date state on `/research`.** Page `useState` calls are `factor`, `horizon`, the new **`mode: "all" | "asof"`** (a mode string — holds no date), and view-state; child labs add only `conditions`/`subject`/`data`/`status`. There is **no date `useState`, no `<input type="date">`, no `DatePicker`, no new date `<select>`** (the only `<select>` on the page is the pre-existing config-driven subject selector).
- **The date flows solely from the global provider.** `const { asOf } = useAsOf();` then `const asofCutoff = mode === "asof" ? asOf : null;` (`page.tsx:51,60`). The mode toggle is a `role="group"` button group, not a date control.
- **The `?as_of=` transmitted is the single global date, not a rival control.** It is appended via the **pre-existing** shared `withAsOf` helper (`lib/api.ts:21` — not added this iteration), the same path `/api/stocks?as_of=` uses. Per the updated invariant #5 and MEMORY `j18-asof-on-stocks-fetch-is-correct`, this is the single global date being transmitted on a snapshot-served read — explicitly NOT a J-18 violation.
- **J-15 read-path discipline preserved.** Fetch effects depend on the resolved `asofCutoff`, not raw `asOf`, so All-history mode (cutoff `null`) does not refetch the labs when the global date moves (`page.tsx:71,659,1054`).

## Part C — Advisory (WARN-only): none material

- Terminology ("All history" / "As of date" / "Pooling every snapshot" / "only snapshots dated ≤ D") is consistent with the app's existing as-of language ("viewing as-of D (historical)").
- The survivorship/descriptive `CaveatBanner` is unchanged and rendered in both modes (not gated on mode) — honest-limitations discipline intact.
- The spec's carried watch-item (`app/frontend/app/data/page.tsx:141` stale "grow the System Health evidence" subtitle) is **not** touched by this iteration and is out of scope — not introduced here, so not even an advisory note against iter-19.

---

## Conclusion

All changes are additive refinements of three existing Data-Contract values on their existing canonical endpoints, behind a read-only as-of FILTER (the iter-17 seam, `as_of=None` ⇒ byte-identical), surfaced by an additive MODE toggle on the existing `/research` home. No duplicate computation, no non-canonical source, no new/duplicate home, no parallel shell, and — critically — **no second date control** (J-18 / invariant #5 held). The blueprint is annotated consistently and no re-approval marker is (or should be) present.

**Verdict: COHERENCE-PASS** — no objective violations; no blocking issues for the goal-evaluator.
