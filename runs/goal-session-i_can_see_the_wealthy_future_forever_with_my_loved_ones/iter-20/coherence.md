**Verdict:** COHERENCE-PASS

## Iteration 20 — Coherence Audit

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration index:** 20
**Iter name:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20
**Target journeys:** J-72 (event-study perf/cache), J-75 (per-stock forward returns), J-77 (Regime × Setup × Pattern study)
**Snapshot SHA:** deef381a95aca1357f9af2f5d094b07d1a5026fc

---

## Step 1 — Data Contract check

### J-75 — Per-stock forward returns (new read surface of existing stored data)

**Blueprint registration:** The Data Contract pre-registers J-75 as "Per-stock forward returns (per symbol × horizon: 1/5/10/20/60d) … computed ONCE by `forward_testing` (the stored append-only `forward_returns` table) … now ADDITIONALLY served (read VERBATIM, never recomputed) on `GET /api/stocks` + `GET /api/stocks/{ticker}` rows. NO new computation, NO new endpoint."

**Audit result:** Confirmed compliant.

- `apps/backend/app/engine/snapshot_serving.py` — the new `_forward_returns_by_symbol` function issues a single `SELECT ForwardReturn WHERE run_id == run.id` read. No return value is computed: it reads `fr.realized_return` verbatim from the stored `forward_returns` table (lines 55–73). No new computation path.
- The horizons come from `cfg.walk_forward.horizons` (line 98) — no hardcoded `[1, 5, 10, 20, 60]` literal in serving code. The frontend (`apps/frontend/app/stocks/page.tsx` line 344–345) also derives `fwdHorizons` from the served `rows[0].forward_returns` order, not a hardcoded list.
- The leaderboard (`GET /api/stocks`) and detail (`GET /api/stocks/{ticker}`) both call `stored_stock_rows(session, run, config)`, which reads from the same `_forward_returns_by_symbol` lookup. Both surfaces serve the identical stored value (J-06 single-source coherence satisfied).
- NA where no stored row — confirmed (`horizon_map.get(h)` returns `None` for missing rows, `snapshot_serving.py` line 83).
- The frontend cells in `/stocks` (`ForwardReturnCell`) and `/stocks/[ticker]` (`ForwardReturnPanel`) re-format only; neither recomputes a return.
- The canonical computation in `forward_testing.py` (functions `forward_return`, `_insert_run_forward_returns`, `backfill_run_forward_returns`) is unchanged — no duplicate computation.

**Verdict:** No violation. PASS.

### J-72 — Event-study perf/cache (figures byte-identical)

**Blueprint registration:** "a PERSISTED/CACHED derived aggregate (prefer a standalone create_all-managed cache table keyed by subject+view+resolved-as-of+a dataset-version stamp) … the cache REFRESHES after dataset changes … EVERY figure stays BYTE-IDENTICAL."

**Audit result:** Confirmed compliant.

- `apps/backend/app/models.py` introduces `EventStudyCache` as a standalone `SQLModel, table=True` table (lines 370–419). The blueprint explicitly sanctions a standalone create_all-managed cache table to avoid the `_ADDITIVE_COLUMNS` trap. No existing table gains a new column.
- The API endpoint `GET /api/research/event-study` now calls `event_study_cached(...)` (`apps/backend/app/api/research.py` line 258) rather than `compute_event_study(...)` directly. `event_study_cached` is in `apps/backend/app/engine/research.py` (line 1244). It reads from the cache on a hit, or calls `compute_event_study` and writes the result. The endpoint shape and the payload values are unchanged (figures byte-identical by design).
- The dataset-version stamp is derived from stored state (max run id + forward-return row count, `research.py` line ~1224), changing on any backfill/removal — no stale reads possible.
- `compute_event_study` itself is NOT exposed to the API directly any more (it was replaced by `event_study_cached` in the API import list — `apps/backend/app/api/research.py` lines 39–42). No second serving path.
- No duplication of `compute_event_study` logic: the cache stores the serialized result of the same function call and serves it verbatim.

**Verdict:** No violation. PASS.

### J-77 — Regime × Setup × Pattern study (new endpoint + new Data Contract value)

**Blueprint registration:** "Regime × Setup × Pattern combination study … computed by `research:compute_regime_setup_pattern_study` over `_event_study_members` enriched with stored regime/setup/pattern; served by the NEW read-only `GET /api/research/regime-setup-pattern`; sampled by the EXISTING `GET /api/research/samples` (new cohort selector). Existing event-study figures (J-29/J-63) byte-identical; count-coherent with the published N."

**Audit result:** Confirmed compliant.

- A new endpoint `GET /api/research/regime-setup-pattern` is registered in `apps/backend/app/api/research.py` (line 263). This is pre-registered in the blueprint as a NEW canonical endpoint for this new value — not a duplicate of any existing value.
- `compute_regime_setup_pattern_study` in `research.py` (line 1440) is a pure grouping of `_regime_setup_pattern_observations` (line 1328). It reads `fr.realized_return`, `fr.mae`, `fr.mfe` from stored `ForwardReturn` rows verbatim — no return recomputed. It reads `run.regime_label`, `res.setup_status`, and `is_<pattern>` flags verbatim from stored `ScannerRun`/`ScannerResult` rows — no regime/setup/pattern recomputed.
- The enrichment of `_event_study_members` to carry `setup_status` and `patterns` (dict of stored `is_<pattern>` booleans) is additive. Existing consumers of `_event_study_members` that did not use these new keys (the existing J-29/J-63 event-study code paths) are unaffected — their figures remain byte-identical.
- The `N=` chip drill-down reuses `GET /api/research/samples` with a new `kind=regime-setup-pattern` cohort selector (`apps/backend/app/engine/samples.py` lines 343–454 and `apps/backend/app/api/research.py` lines 325+). The SAME `_regime_setup_pattern_observations` builder is called in both the study aggregation and the samples drill-down (count-coherence keystone confirmed by the single shared function).
- No new value is being recomputed that already has a canonical source. The risk-adjusted figures (return/downside-dev, return/MAE) in the study use `_downside_deviation` (the SAME helper the factor lab uses, `research.py` line 84) — these are derivation stats over already-stored returns, not a new canonical value.
- Vocabularies (regime labels, setup statuses, pattern keys) come from `cfg.regime.labels`, `ALL_STATUSES`, and `pattern_keys(cfg)` (which reads `cfg.patterns.model_dump()`) — no hardcoded lists.
- `min_sample` threshold reuses `wf.min_sample` (line 1460 + line 1483) — no new magic number.

**Verdict:** No violation. PASS.

### Cross-check: no existing contract value recomputed or served from a new path

Grepped the diff for any new function computing regime scores, stock scores, buckets, setup statuses, or forward returns outside their canonical modules:
- No new `def score_*`, `def compute_forward_return`, `def detect_*`, `def score_regime`, or equivalent found in the diff.
- `apps/backend/app/engine/research.py` explicitly states (module docstring lines 15–16): "It recomputes no factor and no return."
- `apps/backend/app/engine/snapshot_serving.py` `_forward_returns_by_symbol` reads only; no computation.

**Verdict:** No Part A violation found.

---

## Step 2 — Information Architecture check

**New features in this iteration:**
1. Five forward-return columns on `/stocks` (leaderboard) — a new column group on an existing page.
2. "Realized forward returns" panel on `/stocks/[ticker]` (Stock Detail) — a new component on an existing page.
3. `RegimeSetupPatternLab` section on `/research` — a new study section on an existing page.
4. `regime-setup-pattern` cohort selector on `/research/samples` — new routing to an existing page.

**Navigation reachability (static analysis):**

- `/stocks` — linked in `apps/frontend/components/sidebar.tsx`. The forward-return columns are additive fields on the existing leaderboard; no new route, no new nav entry needed.
- `/stocks/[ticker]` — row-reached from `/stocks` (1 click from the sidebar link to `/stocks`, then 1 row click = 2 clicks). The Forward Return Panel is a new component within that same page; no new route.
- `/research` — linked in `apps/frontend/components/sidebar.tsx` (line 37: `{ href: "/research", label: "Research", icon: Microscope }`). The `RegimeSetupPatternLab` section is placed directly on this page (line 162 of `apps/frontend/app/research/page.tsx`). Reachable in 1 click.
- `/research/samples` — already link-reached under Research (the existing J-51/J-64/J-65 mechanism, unchanged). The new cohort selector is additive — the page URL and routing are unchanged.

**No new top-level nav section** — confirmed by the UI surface map and the diff (sidebar.tsx unchanged in this diff; the J-77 section is added as a sub-section within `/research`).

**No duplicate home** — the Regime × Setup × Pattern study lives exclusively on `/research`, which is its blueprint-registered canonical home. The samples drill-down is an extension of the existing `/research/samples` (link-reached), not a second home.

**No parallel shell** — all new components render within the existing `/research` and `/stocks` page shell. No new layout or nav hierarchy introduced.

**Verdict:** No Part B violation found.

---

## Step 3 — Subjective observations (advisory only)

**WARN (advisory):** The blueprint's IA nav skeleton still marks J-75, J-72, and J-77 as `[TARGET iter-20]` rather than `[built iter-20]`. The blueprint was updated to add the iter-20 description text in the header comment and in the IA nav entries (changing `[TARGET]` to `[TARGET iter-20]`), but the text still says "[TARGET iter-20]" rather than marking them built. This is a labelling note only — the blueprint's Data Contract rows correctly describe what was built and the `[TARGET]` label has always been updated to `[built iterN]` retroactively after the evaluator confirms. Not a coherence violation; recorded so the next blueprint update marks them `[built iter-20]`.

**WARN (advisory):** `compute_event_study` is still exported from `research.py` and used directly in the new `event_study_cached` wrapper (which calls it on cache miss). The API imports `event_study_cached` (not `compute_event_study`) so there is only one serving path for the endpoint. This is correct architecture, but future agents should be aware that `compute_event_study` remains callable directly (for tests and direct invocations). Not a violation.

---

## Summary table

| Rule | Checked | Result |
|------|---------|--------|
| Part A1 — duplicate computation of any contract value | All registered values | PASS |
| Part A2 — non-canonical source for forward returns | `/stocks` + `/stocks/[ticker]` UI surfaces | PASS |
| Part A3 — re-format only is fine | All display transforms confirmed re-format-only | PASS |
| Part A4 — new value duplicates existing concept | J-77 RSP study is genuinely new; J-72 is perf-only (same value) | PASS |
| Part A5 — new value unregistered | J-77 and J-75 pre-registered in blueprint; J-72 cache is a perf property | PASS |
| Part B1 — no navigation path | All new surfaces reachable via existing nav | PASS |
| Part B2 — reachability ≤ 2 clicks | `/research` 1 click; `/stocks` 1 click; row-reached surfaces unchanged | PASS |
| Part B3 — duplicate home | None found | PASS |
| Part B4 — parallel shell | None found | PASS |
