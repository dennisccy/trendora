# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/README.md b/README.md
index 548dd00a..c771e3fb 100644
--- a/README.md
+++ b/README.md
@@ -9,7 +9,7 @@ Current capabilities:
 
 - **Daily dashboard**: The Dashboard opens with a compact at-a-glance summary row — **Market Regime** (stored label + 0–100 score) and **Market Phase & Severity** (phase badge + 0–100 severity + filtered bear-probability chip) — as the very first elements on the page, before any chart. Each compact figure has an inline collapsible "component breakdown" that lists the named drivers behind its score so it is never a bare number. Below the summary a single **Regime × phase cross-view** chart shows the market path under two lenses simultaneously in two stacked panes that share one time axis and synchronize zoom and scroll: the top pane shows the major index lines with market-regime colour bands; the bottom pane shows the same index lines with market-phase colour bands, a 0–100 severity line, and a zero-centered **severity-velocity** line — positive values mean market stress is worsening, negative values mean it is easing, with a dashed zero reference so the direction is instantly readable; the earliest few dates show "NA" honestly before enough history exists to measure a slope. The index lines shown in both panes now include three deep equity-index benchmarks — the S&P 500, Nasdaq 100, and Dow Jones Industrial Average — that reach back to 1996, well before the original ETF lines' own starting points (roughly 1999–2005), plus a CBOE Volatility Index (VIX) line and an explicitly-labeled "10Y-2Y spread proxy" Treasury macro-indicator line (named as a proxy so it is never mistaken for the real yield-curve series), for up to ten lines shown at once in ten visually distinct colours; the chart opens already showing this full multi-decade span by default, with no extra click, zoom, or pan needed, and loads quickly from a pre-computed store rather than being recalculated from the full multi-decade price history on every visit. Both the legend and the hover tooltip name which data vendor — Stooq, Yahoo, or FRED-macro proxy — supplied each line wherever one is on record; lines with no recorded vendor show no label rather than a guessed one. The phase colour bands in the bottom pane always span the full stored history regardless of which historical as-of date you have selected — picking an older date moves only the vertical marker, so you see the full context at a glance. Hovering over any date on the cross-view chart shows a tooltip with the market-regime label and its 0–100 score, the phase label, the 0–100 severity, the severity-velocity value, and the P(bear) probability — all for that exact date. Supporting cards — breadth metrics, candidate counts, top sectors, top themes, and the full Market Phase & Severity detail — sit in a collapsed **"More detail"** section below the cross-view chart; nothing was removed, only repositioned for a faster first paint. The cross-view card itself has a persisted hide toggle. A **Market Phase & Severity** detail card shows the phase label (Expansion, Pullback, Correction, Bear, or Recovery) coloured green/amber/red, the 0–100 severity score with a named per-driver breakdown (drawdown depth, time underwater, market regime, breadth below 200-day average, and VIX stress — each showing its value and point contribution), the 0–1 bear-market probability, and a **phase-history timeline** as a colour-coded step-function chart with a dashed as-of marker. A **dated causal downtrend episode list** records exactly when each historical downtrend began and whether it is still open or has closed at the selected date. A **recovery-turn signal line** tells you whether the selected date is a causal recovery/turn signal with a plain-language reason. A fenced **Retrospective (full-sample / analysis-only)** sub-panel (hidden by default) provides after-the-fact peak-to-trough "true bear" dating and the smoothed bear-probability series, clearly labelled as hindsight analysis. When a date has insufficient price history any affected card honestly says "not enough history".
 - **Stock leaderboard**: the page header shows the **current market-regime label and score** for the selected date alongside a **ranked strip of the top five themes** (each labelled with its rank badge and linking directly to the Themes page) so you can read market context at a glance without navigating away. Below that, a ranked table with three independent, explainable scores per stock — Leadership, Entry Quality, and Risk — each displayed as an A–E bucket plus a 0–100 value. A **Proximity to 52w high** column sits directly to the right of Risk and shows the percentage distance of each stock's last close below its 52-week high (`0.00%` means the stock is at a fresh high); "NA" is shown in muted text — and always sorted last — for stocks with insufficient price history. The column is sortable by clicking its header (click again to reverse) and carries an inline info icon with its glossary definition, consistent with every other numeric column. The table is filterable by sector, setup status, and detected chart patterns including VCP. Type in the search box to instantly narrow the list to any ticker or company name — the count stays honest and composes with all other filters. A Themes column shows each stock's theme memberships directly in the table with **#n rank badges**; a Theme dropdown filters the list to stocks belonging to a particular theme and also shows rank badges. Click any column header to sort by that column (click again to reverse) — including the Sector column, which now sorts correctly in both directions for every stock, even the majority of the widened universe that has no sector on file; click the rank column to restore the scanner's original order; clicking the info icon next to a column header opens the definition tooltip without triggering a sort. Stocks with no mapped sector show "Unassigned" instead of a blank cell, and the Sector filter dropdown offers a matching "Unassigned" option to isolate exactly that group. All filters and sort compose: the view always shows filtered, searched results in the chosen order. The table shows **five realized forward-return columns (1d / 5d / 10d / 20d / 60d)** — colour-graded green/red — read directly from stored data; cells near the latest date show "NA" honestly when post-date bars are insufficient; all five columns are sortable with NA values always sorted last. Five paired **max-drawdown columns (1d MDD / 5d MDD / 10d MDD / 20d MDD / 60d MDD)** appear to the right, colour-graded by drawdown magnitude — a shallow loss shows faint red while a deep loss shows saturated red, with "NA" rendered in muted text — all sortable with NA values always at the bottom. Clicking a ticker opens the stock detail in a new tab so the leaderboard — filters, search, sort, scroll position, and selected date — stays exactly as you left it. At early dates before enough price history has accumulated the leaderboard shows an honest warm-up empty state with an explanation pointing to the Data Manager diagnostic rather than fabricated rows.
-- **Evidence tracking**: Every Leadership, Entry Quality, and Risk score on the Stocks leaderboard and on each stock detail page shows an evidence-status chip — "Not yet proven" (muted) or "Proven" (linked) — immediately below the score badge, so a reader always knows at a glance whether hard, out-of-sample statistical evidence currently backs each score. An **Evidence** page, reachable in one click from the left navigation sidebar (ShieldCheck icon, after Research), lists every claim the platform has tested; each row shows its hypothesis, out-of-sample verdict, control comparison versus SPY, registration date, and forward-walk score-to-date. Opening any certified claim's card also reveals a **Historical drawdown & dry-spell expectations** panel, broken out by the market phase the position was entered in (Expansion, Pullback, Correction, Bear, Recovery, always in that order): a typical (median) and worst-case (90th-percentile) drawdown depth, typical days spent underwater, typical time to recover, and the longest streak of consecutive losing periods — each figure carrying its own honest sample size, with any phase that has too few historical examples reading "insufficient (n=…)" instead of a guessed number, plus a plain-language method note and a survivorship-bias caveat below the table; this panel appears on every certified claim regardless of whether that claim itself passed or failed its own out-of-sample test, since it is descriptive cohort history rather than a promise about the future. These panels are pre-computed the moment new data finishes ingesting, so they load instantly the very first time anyone opens the Evidence page after an update — nobody has to be the first visitor to trigger a slow, on-the-spot calculation. When a claim is certified, a **"Why proven?"** disclosure toggle appears below the affected score's badge on its stock detail page; opening it reveals an auditable proof panel with the out-of-sample test result, the SPY benchmark control, and a direct link to the matching Evidence ledger row — supporting a full round trip from the Stocks leaderboard through a stock's proof panel to the Evidence ledger and back. On the Research factor lab, every factor row shows a compact strip of five **"Evidence (D10 · per horizon)"** chips — one per tested holding period (1d, 5d, 10d, 20d, 60d) — each resolved independently to "Proven" (with a direct deep-link to the ledger entry) or "Not yet proven" (no link); a factor that was tested and rejected (such as ma_stack) shows "Not yet proven" at every horizon — a failed test never looks confident. The **Dashboard Market Regime card** links directly to the Evidence page so a reader can jump from the current regime straight to whatever is certified in it. Following the platform's move to a deeper, up-to-30-year price history, every one of the platform's seven previously-certified claims was honestly re-examined from scratch on the new data, and none currently hold up out-of-sample — every score, setup, and factor cohort across the product therefore currently reads "Not yet proven" rather than displaying a number that no longer holds. This is the evidence system working as designed: an edge that only held on shorter history is retired rather than left on display, and a fetch failure degrades the same safe way — never fabricating evidence.
+- **Evidence tracking**: Every Leadership, Entry Quality, and Risk score on the Stocks leaderboard and on each stock detail page shows an evidence-status chip — "Not yet proven" (muted) or "Proven" (linked) — immediately below the score badge, so a reader always knows at a glance whether hard, out-of-sample statistical evidence currently backs each score. An **Evidence** page, reachable in one click from the left navigation sidebar (ShieldCheck icon, after Research), lists every claim the platform has tested; each row shows its hypothesis, out-of-sample verdict, control comparison versus SPY, registration date, and forward-walk score-to-date. Opening any certified claim's card also reveals a **Historical drawdown & dry-spell expectations** panel, broken out by the market phase the position was entered in (Expansion, Pullback, Correction, Bear, Recovery, always in that order): a typical (median) and worst-case (90th-percentile) drawdown depth, typical days spent underwater, typical time to recover, and the longest streak of consecutive losing periods — each figure carrying its own honest sample size, with any phase that has too few historical examples reading "insufficient (n=…)" instead of a guessed number, plus a plain-language method note and a survivorship-bias caveat below the table; this panel appears on every certified claim regardless of whether that claim itself passed or failed its own out-of-sample test, since it is descriptive cohort history rather than a promise about the future. If a panel's computation temporarily fails, it shows a calm "Unavailable — monitored and refreshed as new data arrives." note instead of breaking the Evidence page entirely. These panels are pre-computed the moment new data finishes ingesting, so they load instantly the very first time anyone opens the Evidence page after an update — nobody has to be the first visitor to trigger a slow, on-the-spot calculation. When a claim is certified, a **"Why proven?"** disclosure toggle appears below the affected score's badge on its stock detail page; opening it reveals an auditable proof panel with the out-of-sample test result, the SPY benchmark control, and a direct link to the matching Evidence ledger row — supporting a full round trip from the Stocks leaderboard through a stock's proof panel to the Evidence ledger and back. On the Research factor lab, every factor row shows a compact strip of five **"Evidence (D10 · per horizon)"** chips — one per tested holding period (1d, 5d, 10d, 20d, 60d) — each resolved independently to "Proven" (with a direct deep-link to the ledger entry) or "Not yet proven" (no link); a factor that was tested and rejected (such as ma_stack) shows "Not yet proven" at every horizon — a failed test never looks confident. The **Dashboard Market Regime card** links directly to the Evidence page so a reader can jump from the current regime straight to whatever is certified in it. Following the platform's move to a deeper, up-to-30-year price history, every one of the platform's seven previously-certified claims was honestly re-examined from scratch on the new data, and none currently hold up out-of-sample — every score, setup, and factor cohort across the product therefore currently reads "Not yet proven" rather than displaying a number that no longer holds. This is the evidence system working as designed: an edge that only held on shorter history is retired rather than left on display, and a fetch failure degrades the same safe way — never fabricating evidence.
 - **Point-in-time stock universe**: the set of stocks the scanner scores is recomputed for the date you are viewing, drawn from a broadened candidate pool of roughly 548 names — a name only qualifies once it has enough price history, a sufficient share price, adequate trading liquidity, and a price feed that hasn't gone stale (stopped updating for more than 10 calendar days), all measured from data on or before that date. Before enough history has accumulated for a given date the leaderboard is honestly empty (0 rows); the universe grows as more names clear the history bar across the platform's now up-to-30-year price history. The universe count on Data Manager changes in real time as you step the global date switcher — and the count shown on the coverage diagnostic always agrees with the count served on the leaderboard. All leaderboard pages (Stocks, Themes, Sectors), Backtest evidence, and Research surfaces reflect only the names that qualify at the viewed date. The Data Manager membership timeline renders a true step-function curve: the SIZE column varies by date, and the Entries and Exits columns are populated with real membership changes rather than dashes.
 - **Stock detail**: full price + moving-average + volume chart (extending through the latest seed date with an as-of marker for historical views) with **optional market-regime bands** in the background (toggle default-on, persists) and a **chart-range toggle** — Recent (a bounded ~5-year trailing window, the default) or Full history (the stock's entire real history back to its actual first trading day, as early as 1996 for the longest-tenured names) — with a header caption disclosing the exact bar count, the as-of date, and the stock's first available date; Full-history view is honestly thinned to weekly bars beyond a set age so it stays responsive, and a recently-listed stock's short real history is shown as-is, never padded with invented earlier prices. A **Realized forward returns** panel above the chart shows the five horizon returns (1d / 5d / 10d / 20d / 60d) colour-graded for the resolved as-of date, each accompanied by its paired **max-drawdown figure** (the worst peak-to-trough decline within that window) colour-graded by loss magnitude to match the leaderboard exactly; per-score component breakdowns (the Leadership breakdown shows the actual distance-below-52w-high percentage — e.g., `-0.53%` — matching the leaderboard column for that stock), theme membership, setup status, plain-language reason, and a concrete invalidation level. A **crosshair hover detail box** tracks the cursor over the price chart and displays the exact date, open, high, low, close, volume, percentage change, and each moving-average value for the bar under the cursor — bars that fall after the selected as-of date are clearly labelled as display-only; the box disappears when the cursor leaves the chart.
 - **Risk budget**: every stock detail page shows a **Risk budget card**, sitting directly below the "Theme & invalidation" card and above the pattern cards (VCP, etc.), captioned "Descriptive only; not a recommendation" — no buy/sell/trim wording. It answers "how much can this hurt" with ATR%, downside-only volatility, an overnight-gap profile (the near-worst p95 gap as the headline figure, with median and worst gap shown as supporting detail) plus the overnight share of 20-day return variance, the single worst historical 20-trading-day window in the stock's whole price history, and the exact distance to its invalidation level — every number carries a **"pXX of universe" percentile chip** showing how that figure ranks against the rest of the scanned universe. The same five headline numbers — ATR%, Downside vol, Gap p95, Worst 20d, and Dist. to invalidation — appear as sortable, right-aligned columns on the `/stocks` leaderboard (inserted between the existing "High proximity" and "Setup" columns), each carrying the same inline info-icon definition used by every other column and reading the identical stored figures as the detail card so the leaderboard and the detail page can never disagree. A stock with too little trading history honestly shows "NA — insufficient history" on the affected tiles or cells instead of a fabricated number, and the Methodology glossary documents all three new metrics — overnight-gap profile, worst 20-day window, and distance-to-invalidation % — including the exact 20-trading-day window each is computed over.
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 0f390020..6e73c5a1 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -743,7 +743,17 @@ class WalkForwardCfg(BaseModel):
       - `streak_min_n` — the loss-streak honesty floor: a phase's longest-losing-streak cell needs at least
         this many WALK-FORWARD-CADENCE dates (not raw per-observation n, which `min_sample` already floors)
         before it is shown as a real value rather than "insufficient (n=…)". Distinct from `min_sample`
-        because cadence dates are far fewer than per-observation rows."""
+        because cadence dates are far fewer than per-observation rows.
+
+    ops-hardening iter-30 (AG-8, J-07) ADDITIVE key, consumed by `app.engine.forward_testing.compute_
+    forward_aggregates`:
+      - `forward_agg_run_chunk` — the RUN-COUNT width of `compute_forward_aggregates`'s own join-accumulator
+        chunk (its OWN dedicated knob — never `research.read_batch_size`, a ROWS knob for `yield_per`, and
+        never `research.factor_join_run_chunk`, a DIFFERENT function's own run-chunk knob; iter-29's binding
+        lesson on unit/ownership mismatch is exactly the failure mode this separate key avoids). Peak live
+        accumulator = this x symbols-per-run (~417 on the live basis), so it must stay well below the live
+        distinct-run count per horizon (1,813-1,872 today) to bind at all. Defaulted so a config predating it
+        (and the inline test fixtures) still loads unchanged; boot-validated `>= 1`."""
 
     model_config = ConfigDict(extra="allow")
     history_years: int
@@ -755,6 +765,7 @@ class WalkForwardCfg(BaseModel):
     attribution: AttributionCfg
     underwater_horizons: list[int] = Field(min_length=1)
     streak_min_n: int
+    forward_agg_run_chunk: int = 100
 
     @model_validator(mode="after")
     def _validate(self) -> "WalkForwardCfg":
@@ -773,6 +784,8 @@ class WalkForwardCfg(BaseModel):
             raise ValueError("walk_forward.underwater_horizons must all be positive")
         if self.streak_min_n <= 0:
             raise ValueError("walk_forward.streak_min_n must be positive")
+        if self.forward_agg_run_chunk < 1:
+            raise ValueError("walk_forward.forward_agg_run_chunk must be >= 1")
         return self
 
 
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index 3b5a8e4a..24b17456 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -854,6 +854,43 @@ def _leadership_returns(
     return {"sectors": sectors, "themes": themes, "cohort": cohort}
 
 
+def _forward_agg_runs_with_fr(session: Session, horizon: int, as_of: Optional[date_cls]) -> list[int]:
+    """iter-30 (AG-8): the sorted DISTINCT `forward_returns.run_id`s carrying a return at `horizon`
+    (optionally `as_of`-scoped) — `compute_forward_aggregates`'s chunk axis, mirroring
+    `research._runs_with_fr`'s established DISTINCT-projected discovery pattern (bounded by RUN count,
+    never by the (run_id, symbol) PAIR count the old single-pass accumulator materialized). Semantically
+    IDENTICAL to the prior `{fr_run_id for fr_run_id, ... in session.exec(fr_stmt)...}` set build: a
+    `SELECT DISTINCT run_id` returns exactly the same run-id set a full iteration would collect, so
+    `runs_with_fr` is byte-identical to before — only how it is discovered changed (no return/max_drawdown
+    value is read at this step)."""
+    stmt = select(ForwardReturn.run_id).where(ForwardReturn.horizon == horizon)
+    if as_of is not None:
+        stmt = stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(ScannerRun.asof_date <= as_of)
+    return sorted(session.exec(stmt.distinct()).all())
+
+
+def _forward_agg_slice_map(
+    session: Session, horizon: int, slice_run_ids: list[int], batch: int,
+) -> dict[tuple[int, str], tuple[float, Optional[float]]]:
+    """iter-30 (AG-8): the `(run_id, symbol) -> (realized_return, max_drawdown)` join map for ONE bounded
+    SLICE of run ids — `compute_forward_aggregates`'s chunk-scoped join accumulator, mirroring
+    `research._fr_slice_map` exactly (merged into ONE dict of tuples rather than two parallel dicts, half
+    the dict-entry count). Column-projected + `yield_per`-streamed like the pre-chunk single-pass read; the
+    only difference is the added `run_id.in_(slice_run_ids)` scope, which bounds this dict's LIVE size to
+    (len(slice_run_ids) x symbols-per-run) instead of the full horizon-partition's distinct (run_id, symbol)
+    pair count (770K-803K measured live per horizon, iter-29's audit — the SAME join-accumulator shape iter-29
+    fixed one function over in `research.py`, now confirmed live in THIS function's own `forward_testing.py:965`
+    frame per the iter-29 evaluator's browser-QA finding). The caller discards this dict before the next
+    chunk — it never again holds the full horizon-partition at once."""
+    fr_stmt = select(
+        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return, ForwardReturn.max_drawdown,
+    ).where(ForwardReturn.horizon == horizon, ForwardReturn.run_id.in_(slice_run_ids))
+    slice_map: dict[tuple[int, str], tuple[float, Optional[float]]] = {}
+    for run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
+        slice_map[(run_id, symbol)] = (realized_return, max_drawdown)
+    return slice_map
+
+
 def compute_forward_aggregates(
     session: Session,
     horizon: int,
@@ -872,25 +909,47 @@ def compute_forward_aggregates(
     `as_of` (iter-17, J-09/J-10) optionally scopes the pool to an EXPANDING WALK-FORWARD WINDOW: when
     set, ONLY snapshots with `ScannerRun.asof_date <= as_of` contribute, so a run dated > D leaks nothing
     into the as-of-D evidence (the No-lookahead / No-recompute / Single-source criticals). It is a SINGLE
-    membership filter on the `fr_stmt` step, so it equally bounds `runs_with_fr`, the `ScannerResult` scan,
-    `run_rows`, and the SPY/QQQ benchmark lists (all derived from it) — the grouping / excess /
-    control-group / attribution math is untouched. `as_of=None` keeps the all-history behaviour
+    membership filter on `_forward_agg_runs_with_fr`, so it equally bounds `runs_with_fr`, every chunk's
+    `ScannerResult` scan, `run_rows`, and the SPY/QQQ benchmark lists (all derived from it) — the grouping /
+    excess / control-group / attribution math is untouched. `as_of=None` keeps the all-history behaviour
     BYTE-IDENTICAL (== the latest-date case, since no run is dated after the latest). The cutoff is the
     resolved global as-of date transmitted on the snapshot-served read — never a second date state (J-18).
 
-    iter-14 (J-07, AG-8 REGRESSION recovery): the `ForwardReturn` and `ScannerResult` reads below are
+    iter-14 (J-07, AG-8 REGRESSION recovery): the `ForwardReturn` and `ScannerResult` reads are
     column-projected and `yield_per`-streamed (mirroring `_streamed_existing_keys` in this same module and
     `research._event_study_members`/`_subject_matching_result_rows`'s established precedent for these exact
-    two tables) instead of each being materialized as a whole-partition `.all()` of full ORM objects. Both
-    tables had grown ~9x since this was first written (`scanner_results` 611,689 rows, `forward_returns`
-    3,098,302 rows at the ops-hardening iter-14 measurement) and the unbounded pattern was the confirmed
-    root cause of a session-long critical AG-8 defect (a silent per-request `MemoryError` in iter-11/12,
-    escalating to a ~12-minute full-backend wedge under concurrent load in iter-13). Only the fields
-    actually read below are ever selected — no second formula, no schema change, no signature/return-shape
-    change; byte-identical to the prior whole-row materialization for the same inputs (proven by a
-    fixture-backed equality test), because the SAME filter produces the SAME row set and every downstream
-    step (dict/set construction, `_group_means`, `_control_groups`, `_attribution_slices`) is unaffected by
-    how those rows were fetched."""
+    two tables) instead of each being materialized as a whole-partition `.all()` of full ORM objects.
+
+    iter-30 (AG-8, J-07 finding): streaming the two SOURCE queries was not enough on its own — the JOIN
+    ACCUMULATOR (the old `ret_by_run_symbol`/`mdd_by_run_symbol` dicts) still held every distinct
+    (run_id, symbol) pair of the FULL horizon-partition at once (770K-803K measured live, iter-29's audit —
+    the SAME shape iter-29 fixed one function over in `research.py`'s `_fr_slice_map`, confirmed live in
+    THIS function via the ops-hardening iter-29 evaluator's browser-QA `MemoryError` finding at
+    `forward_testing.py:965`). `runs_with_fr` is now discovered up front via `_forward_agg_runs_with_fr`
+    (a lightweight DISTINCT-projected query, bounded by run count, never by pair count) and walked in
+    bounded SLICES of `walk_forward.forward_agg_run_chunk` run ids (its OWN dedicated RUN-count knob — never
+    `research.read_batch_size`, a ROWS knob, or `research.factor_join_run_chunk`, a different function's own
+    knob; iter-29's binding unit/ownership lesson). Each slice builds its own `_forward_agg_slice_map`
+    (bounded to len(slice) x symbols-per-run), uses it to build ONLY that slice's contribution to
+    `stock_obs` PLUS extract the tiny benchmark-symbol subset (`bm_returns`, SPY/QQQ/sector-ETF returns
+    only — the ONLY symbols `_control_groups`/the excess calc below ever look up in this map, confirmed by
+    inspection: neither ever looks up a regular stock ticker in it), then discards the slice map before the
+    next chunk — the two named join dicts never again hold the full horizon-partition at once.
+
+    `stock_obs` itself is still assembled to full size by the end of the loop: `_attribution_slices`
+    (below) is a frozen, test-pinned `(stock_obs, cfg)` read-only contract
+    (`test_attribution_is_pure_over_passed_observations_no_new_query`) that several other tests also call
+    directly with hand-built observation lists, so it still needs one materialized list — but it never again
+    CO-EXISTS with a full-size join accumulator, only with the current chunk's small one. `_group_means`,
+    `_group_mdd`, `_control_groups`, `_attribution_slices`, and the VCP/pullback/breakout groupings are all
+    UNCHANGED (same signatures, same bodies) — this fix is confined to HOW the containers they consume are
+    assembled. Byte-identical to the prior whole-partition accumulation for the same inputs (proven by a
+    fixture-backed equality test): the chunks partition `runs_with_fr` into non-overlapping, exhaustive
+    ranges, so the UNION of every chunk's `stock_obs` contribution and `bm_returns` entries exactly equals
+    what the old single-pass accumulation produced (mean/median/stdev are order-independent — CPython's
+    `statistics` module sums via exact `Fraction` arithmetic — and `_control_groups`' RNG draws are
+    order-independent too: its per-sector sample pool is re-sorted by ticker before every `rng.sample`
+    call, so it depends only on ascending run-id processing order, never on `stock_obs`'s own list order)."""
     cfg = config or get_config()
     wf = cfg.walk_forward
     bm = benchmark_symbols(cfg)
@@ -898,38 +957,14 @@ def compute_forward_aggregates(
     # `_streamed_existing_keys`/`research.py`'s heavy read-path builders already use (no second batch-size
     # config value).
     batch = cfg.research.read_batch_size
+    # iter-30's OWN dedicated RUN-count chunk width (never `research.read_batch_size`/`factor_join_run_chunk`
+    # — iter-29's binding unit/ownership lesson).
+    run_chunk = wf.forward_agg_run_chunk
 
-    # The SINGLE as-of membership filter (iter-17): restrict the pool to runs dated <= D by joining each
-    # forward return to its run's canonical `asof_date`. `as_of=None` adds NO clause -> the query (and
-    # thus every derived set) is byte-identical to the all-history path. The cutoff is read from
-    # `ScannerRun.asof_date` (the canonical snapshot date) — not the denormalized `ForwardReturn.asof_date`
-    # — so it is exactly the "snapshots dated <= D" membership the expanding walk-forward window requires.
-    #
-    # iter-14: column-projected to the 4 fields actually read (run_id, symbol, realized_return,
-    # max_drawdown) and consumed via `yield_per(batch)` — bounded memory on the horizon-partition scan.
-    # `ret_by_run_symbol`/`mdd_by_run_symbol`/`runs_with_fr_set` are built incrementally per streamed row;
-    # dict/set construction is order-independent, so this is byte-identical to the prior two full-row
-    # dict comprehensions + sorted-set-of-attribute pattern.
-    fr_stmt = select(
-        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return, ForwardReturn.max_drawdown,
-    ).where(ForwardReturn.horizon == horizon)
-    if as_of is not None:
-        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
-            ScannerRun.asof_date <= as_of
-        )
-    ret_by_run_symbol: dict[tuple[int, str], float] = {}
-    # iter-27 (J-86): the stored max_drawdown for each (run, symbol) at this horizon, read VERBATIM — so
-    # the aggregate mean-MDD is a read-only grouping of the SAME stored values (no recomputed drawdown).
-    mdd_by_run_symbol: dict[tuple[int, str], Optional[float]] = {}
-    runs_with_fr_set: set[int] = set()
-    for fr_run_id, fr_symbol, fr_realized_return, fr_max_drawdown in session.exec(fr_stmt).yield_per(batch):
-        ret_by_run_symbol[(fr_run_id, fr_symbol)] = fr_realized_return
-        mdd_by_run_symbol[(fr_run_id, fr_symbol)] = fr_max_drawdown
-        runs_with_fr_set.add(fr_run_id)
-    runs_with_fr = sorted(runs_with_fr_set)
+    runs_with_fr = _forward_agg_runs_with_fr(session, horizon, as_of)
 
     # NOTE: `run_rows` stays a materialized `.all()` (unchanged, iter-14 scope) — one `ScannerRun` per
-    # cadence date (bounded, small; ~180+ total on the current deep basis), not one of the two named
+    # cadence date (bounded, small; ~180+ total on the current deep basis), not one of the named
     # unbounded offenders this iteration fixes.
     run_rows = (
         session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
@@ -937,31 +972,40 @@ def compute_forward_aggregates(
     )
     regime_by_run = {run.id: run.regime_label for run in run_rows}
 
+    # The ONLY symbols `_control_groups`/the excess calc below ever look up in `bm_returns` — SPY, QQQ, and
+    # every sector ETF (confirmed by inspection of both consumers). `bm_returns` therefore stays bounded to
+    # (n_runs x n_benchmarks) — ~1,800 x ~13 = ~23K entries on the live basis — regardless of chunk width,
+    # never the full horizon-partition.
+    benchmark_symbol_set = {bm["spy"], bm["qqq"], *bm["sector_etfs"]}
+    bm_returns: dict[tuple[int, str], float] = {}
+
     # Per-stock observations: each stored result joined to its stored realized return at this horizon.
     # The bucket / setup / sector / rank / regime are READ from the snapshot — never recomputed here.
-    #
-    # iter-14: column-projected to the 8 fields actually read below and consumed via `yield_per(batch)` —
-    # bounded memory on the `ScannerResult` scan (the largest table, `record_json` blobs excluded from the
-    # projection entirely). Ordered by `ScannerResult.id` — mirroring `research._subject_matching_result_
-    # rows`'s established precedent for this exact table/concern — so the streamed scan reproduces the
-    # SAME row order the prior un-ordered `.all()` naturally returned (SQLite's default rowid-ascending
-    # scan for a simple single-table `WHERE run_id IN (...)` query), keeping `stock_obs`'s content AND
-    # order byte-identical. `stock_obs` is built directly in the loop with the SAME `if realized is None:
-    # continue` NA gate as before.
     stock_obs: list[dict] = []
-    if runs_with_fr:
+    for start in range(0, len(runs_with_fr), run_chunk):
+        slice_run_ids = runs_with_fr[start:start + run_chunk]
+        slice_map = _forward_agg_slice_map(session, horizon, slice_run_ids, batch)
+        for (slice_run_id, slice_symbol), (slice_return, _slice_mdd) in slice_map.items():
+            if slice_symbol in benchmark_symbol_set:
+                bm_returns[(slice_run_id, slice_symbol)] = slice_return
+
+        # iter-14: column-projected to the 8 fields actually read below and consumed via `yield_per(batch)`
+        # (the largest table, `record_json` blobs excluded from the projection entirely). Ordered by
+        # `ScannerResult.id` within this slice. `stock_obs` is built with the SAME `if fr is None: continue`
+        # NA gate as before.
         res_stmt = select(
             ScannerResult.run_id, ScannerResult.ticker, ScannerResult.leadership_bucket,
             ScannerResult.setup_status, ScannerResult.sector, ScannerResult.rank,
             ScannerResult.is_vcp, ScannerResult.is_pullback_to_rising_dma, ScannerResult.is_flat_base_breakout,
-        ).where(ScannerResult.run_id.in_(runs_with_fr)).order_by(ScannerResult.id)
+        ).where(ScannerResult.run_id.in_(slice_run_ids)).order_by(ScannerResult.id)
         for (
             res_run_id, ticker, leadership_bucket, setup_status, sector, rank,
             is_vcp, is_pullback_to_rising_dma, is_flat_base_breakout,
         ) in session.exec(res_stmt).yield_per(batch):
-            realized = ret_by_run_symbol.get((res_run_id, ticker))
-            if realized is None:
+            fr = slice_map.get((res_run_id, ticker))
+            if fr is None:
                 continue  # this stock has no realized return at this horizon in this run (n=0 contribution)
+            realized, max_drawdown = fr
             stock_obs.append({
                 "run_id": res_run_id,
                 "ticker": ticker,
@@ -969,7 +1013,7 @@ def compute_forward_aggregates(
                 # iter-27 (J-86): the stored max_drawdown for this observation (read verbatim) — paired to
                 # the return so the aggregate mean-MDD groups exactly the same observation set as the mean
                 # return.
-                "max_drawdown": mdd_by_run_symbol.get((res_run_id, ticker)),
+                "max_drawdown": max_drawdown,
                 "bucket": leadership_bucket,   # stored canonical A-E (verbatim — no re-bucketing)
                 "setup": setup_status,         # stored canonical setup status (verbatim)
                 "sector": sector,
@@ -980,6 +1024,8 @@ def compute_forward_aggregates(
                 "is_pullback_to_rising_dma": is_pullback_to_rising_dma,
                 "is_flat_base_breakout": is_flat_base_breakout,
             })
+        # `slice_map` is rebound (not accumulated into) on the next iteration — this slice's dict is
+        # eligible for GC before the next chunk's query even starts (the bounded-memory guarantee, TC-1).
 
     stock_returns = [o["return"] for o in stock_obs]
     overall_mean = _mean_or_none(stock_returns)
@@ -987,8 +1033,8 @@ def compute_forward_aggregates(
     # NA discipline the return aggregate uses) — read-only over the SAME stored values, recomputes nothing.
     overall_mdds = [o["max_drawdown"] for o in stock_obs if o["max_drawdown"] is not None]
     overall_mean_mdd = _mean_or_none(overall_mdds)
-    spy_returns = [ret_by_run_symbol[(r, bm["spy"])] for r in runs_with_fr if (r, bm["spy"]) in ret_by_run_symbol]
-    qqq_returns = [ret_by_run_symbol[(r, bm["qqq"])] for r in runs_with_fr if (r, bm["qqq"]) in ret_by_run_symbol]
+    spy_returns = [bm_returns[(r, bm["spy"])] for r in runs_with_fr if (r, bm["spy"]) in bm_returns]
+    qqq_returns = [bm_returns[(r, bm["qqq"])] for r in runs_with_fr if (r, bm["qqq"]) in bm_returns]
     spy_mean = _mean_or_none(spy_returns)
     qqq_mean = _mean_or_none(qqq_returns)
 
@@ -1053,7 +1099,10 @@ def compute_forward_aggregates(
         "by_pullback_to_rising_dma": by_pullback_to_rising_dma,
         "by_flat_base_breakout": by_flat_base_breakout,
         "excess": excess,
-        "control_group": _control_groups(horizon, stock_obs, ret_by_run_symbol, runs_with_fr, cfg),
+        # iter-30: `bm_returns` is the bounded, benchmark-symbol-only subset of the old full `ret_by_run_
+        # symbol` — `_control_groups` only ever looks up SPY/QQQ/sector-ETF keys in it (confirmed above),
+        # so this is byte-identical to passing the old unbounded dict.
+        "control_group": _control_groups(horizon, stock_obs, bm_returns, runs_with_fr, cfg),
         # J-19: the four read-only attribution slices for this horizon, derived from the SAME stock_obs
         # (no recomputed return). distribution.mean_return == overall.mean_return (asserted in tests).
         "attribution": _attribution_slices(stock_obs, cfg),
diff --git a/apps/backend/tests/test_forward_testing_aggregates_streaming.py b/apps/backend/tests/test_forward_testing_aggregates_streaming.py
index 6e3745b0..9c02e494 100644
--- a/apps/backend/tests/test_forward_testing_aggregates_streaming.py
+++ b/apps/backend/tests/test_forward_testing_aggregates_streaming.py
@@ -14,14 +14,28 @@ rewritten function still uses. Any divergence between the real function's output
 therefore only come from the two rewritten read steps, never from a second aggregation formula — this is
 the "capture the original's output ... or keep a reference implementation in the test" fixture-backed
 equality proof the iter-14 plan calls for (TC-1/TC-2).
+
+ops-hardening iter-30 (AG-8, J-07) ADDITIVE section (bottom of this file): streaming the two source
+queries was not enough on its own — the JOIN ACCUMULATOR built from those streamed rows
+(`ret_by_run_symbol`/`mdd_by_run_symbol`, exactly what `_reference_compute_forward_aggregates` above still
+builds via one un-sliced `.all()`) still held every distinct (run_id, symbol) pair of the FULL
+horizon-partition at once (770K-803K measured live per horizon) — the confirmed live `MemoryError` site
+this iteration bounds via `_forward_agg_slice_map` + `walk_forward.forward_agg_run_chunk`-sized run
+slices. Because `_reference_compute_forward_aggregates` never chunks, it doubles as the byte-identity
+oracle for the run-chunking dimension too (reused, not re-pinned a second time) — the new tests below
+compare the SAME real `compute_forward_aggregates` against this SAME reference, just varying
+`forward_agg_run_chunk` instead of `research.read_batch_size`.
 """
 from __future__ import annotations
 
-from datetime import date, datetime, timezone
+import sqlite3
+from datetime import date, datetime, timedelta, timezone
+from pathlib import Path
 
 import pytest
 from sqlmodel import Session, select
 
+import app.engine.forward_testing as forward_testing_module
 from app.config import load_config
 from app.db import create_db_and_tables, make_engine
 from app.engine.forward_testing import (
@@ -40,6 +54,9 @@ from app.engine.forward_testing import (
 from app.engine.setups import ALL_STATUSES
 from app.models import ForwardReturn, ScannerResult, ScannerRun
 
+REPO_ROOT = Path(__file__).resolve().parents[3]
+REAL_DB = REPO_ROOT / "apps/backend/data/trendora.db"
+
 # --------------------------------------------------------------------------------------------------
 # Pinned pre-rewrite reference implementation (the two `.all()` reads this iteration replaces)
 # --------------------------------------------------------------------------------------------------
@@ -301,3 +318,251 @@ def test_compute_forward_aggregates_zero_fr_run_excluded_from_runs_with_fr(multi
         reference_payload = _reference_compute_forward_aggregates(session, 20, cfg, as_of=None)
     assert "2025-06-15" not in new_payload["asof_dates"]
     assert new_payload == reference_payload
+
+
+# ====================================================================================================
+# ops-hardening iter-30 (AG-8, J-07) — `compute_forward_aggregates`'s OWN join-accumulator chunking.
+#
+# iter-14 above bounded the two SOURCE queries (streamed `.all()` -> `yield_per`); iter-30 bounds the
+# CONTAINER those streamed rows land in (`ret_by_run_symbol`/`mdd_by_run_symbol`, still built as one
+# un-sliced accumulator by `_reference_compute_forward_aggregates` above), which iter-29's audit found
+# still held every distinct (run_id, symbol) pair of the FULL horizon-partition at once — the confirmed
+# live `MemoryError` site (`forward_testing.py:965`). `_forward_agg_slice_map` + `walk_forward.
+# forward_agg_run_chunk` (its OWN dedicated RUN-count knob — never `research.read_batch_size`, a ROWS
+# knob, or `research.factor_join_run_chunk`, a different function's own knob) replace it with bounded,
+# per-run-id-slice accumulation. `_reference_compute_forward_aggregates` never chunks by run, so it is
+# reused (not re-pinned) as the byte-identity oracle for this dimension too.
+# ====================================================================================================
+def _cfg_run_chunk(run_chunk: int):
+    """The real config with `walk_forward.forward_agg_run_chunk` overridden (chunk-width probe) — mirrors
+    the row-batch `cfg.model_copy(update={"research": ...})` override pattern used above, for this
+    iteration's own dedicated run-count knob."""
+    cfg = load_config()
+    wf = cfg.walk_forward.model_copy(update={"forward_agg_run_chunk": run_chunk})
+    return cfg.model_copy(update={"walk_forward": wf})
+
+
+def test_forward_agg_run_chunk_accumulator_is_bounded(multi_run_engine, monkeypatch):
+    """TC-1: `compute_forward_aggregates`'s join accumulator (`_forward_agg_slice_map`'s return value,
+    observed via monkeypatch) never holds more entries than ONE bounded chunk at any point — never one
+    entry per distinct (run_id, symbol) pair across the whole 4-run (excluding the zero-FR 5th run)
+    fixture (8 stocks + 4 benchmarks = 12 symbols/run)."""
+    cfg = _cfg_run_chunk(1)  # 4 runs at width 1 -> 4 slices, one run id each
+    observed_sizes: list[int] = []
+    real_slice_map = forward_testing_module._forward_agg_slice_map
+
+    def _wrapped(session, horizon, slice_run_ids, batch):
+        result = real_slice_map(session, horizon, slice_run_ids, batch)
+        observed_sizes.append(len(result))
+        return result
+
+    monkeypatch.setattr(forward_testing_module, "_forward_agg_slice_map", _wrapped)
+    with Session(multi_run_engine) as session:
+        agg = compute_forward_aggregates(session, 20, cfg)
+
+    total_pairs = 4 * (len(_STOCKS) + len(_BENCHMARKS))  # 4 runs x 12 symbols = 48, if ever unbounded
+    assert agg["n_runs"] == 4, "sanity: the zero-FR 5th run must stay excluded"
+    assert len(observed_sizes) == 4, f"expected 4 chunks (4 run ids at width 1), got {len(observed_sizes)}"
+    assert max(observed_sizes) == len(_STOCKS) + len(_BENCHMARKS), (
+        f"a single run's own slice must hold exactly its own symbol count, got {observed_sizes}"
+    )
+    assert max(observed_sizes) < total_pairs, (
+        "the live accumulator must never hold the WHOLE fixture's pairs at once"
+    )
+
+
+@pytest.mark.parametrize("run_chunk", [1, 2, 4, 100])
+@pytest.mark.parametrize("as_of", [None, HISTORICAL_AS_OF])
+def test_compute_forward_aggregates_chunked_equals_reference_across_run_chunk_widths(
+    multi_run_engine, run_chunk, as_of
+):
+    """TC-2: for EVERY configured horizon, the chunked `compute_forward_aggregates` stays byte-identical
+    to the pinned (never-chunks-by-run) reference at run-chunk widths that produce 1 chunk (100, >= the
+    4-run fixture), an even split (2), and maximum fragmentation (1, one run per chunk) — with and
+    without `as_of`."""
+    cfg = _cfg_run_chunk(run_chunk)
+    with Session(multi_run_engine) as session:
+        for horizon in HORIZONS:
+            new_payload = compute_forward_aggregates(session, horizon, cfg, as_of=as_of)
+            reference_payload = _reference_compute_forward_aggregates(session, horizon, cfg, as_of=as_of)
+            assert new_payload == reference_payload, (
+                f"chunked != reference at run_chunk={run_chunk} horizon={horizon} as_of={as_of}"
+            )
+
+
+def test_forward_agg_run_chunk_boundary_never_splits_a_run(multi_run_engine):
+    """Error case: a chunk boundary adjacent to (or isolating) every run must not double-count or drop
+    that run's contribution — proved directly (not just via the full-dict equality above) by pinning a
+    specific by-regime count/mean at maximum fragmentation (run_chunk=1) against the SAME figures at zero
+    fragmentation (run_chunk=100, one chunk): r0/r3 are Risk-off, r1/r2 are Risk-on (2 runs each), so
+    Risk-on's `n` must be exactly 2 runs' worth of stock observations at both widths, never doubled or
+    dropped by isolating each run into its own chunk."""
+    horizon = 20
+    with Session(multi_run_engine) as session:
+        fragmented = compute_forward_aggregates(session, horizon, _cfg_run_chunk(1))
+        single_chunk = compute_forward_aggregates(session, horizon, _cfg_run_chunk(100))
+    frag_regime = {r["regime"]: r for r in fragmented["by_regime"]}
+    single_regime = {r["regime"]: r for r in single_chunk["by_regime"]}
+    for label in ("Risk-on", "Risk-off"):
+        assert frag_regime[label]["n"] == single_regime[label]["n"] == 2 * len(_STOCKS)
+        assert frag_regime[label]["mean_return"] == pytest.approx(single_regime[label]["mean_return"])
+
+
+@pytest.fixture()
+def sparse_chunk_engine(tmp_path):
+    """A run (r_sparse) that DOES carry a forward return (so it legitimately enters `runs_with_fr` and its
+    chunk IS processed) but whose OWN scored ticker has NO matching forward return at all — an
+    ALL-EXCLUDED chunk (zero qualifying `stock_obs` rows) when isolated at `forward_agg_run_chunk=1`, the
+    error case a run-chunked merge must survive without crashing or fabricating a value."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'sparse_chunk.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        run = ScannerRun(
+            asof_date=date(2025, 8, 1), created_at=_utc(), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(run)
+        session.flush()
+        # scored, but NEVER given a ForwardReturn at any horizon -> always excluded, never fabricated
+        session.add(ScannerResult(
+            run_id=run.id, ticker="NOFR", name="NOFR", sector="Technology",
+            leadership_score=50.0, leadership_bucket="A", entry_quality_score=0.0, entry_quality_bucket="E",
+            risk_score=0.0, risk_bucket="E", setup_status="Actionable", rank=1, record_json="{}",
+        ))
+        # the ONLY forward return this run carries is a benchmark's -> the run legitimately enters
+        # runs_with_fr / the SPY benchmark list, even though its own chunk yields zero stock_obs rows.
+        session.add(ForwardReturn(
+            run_id=run.id, symbol="SPY", horizon=20, asof_date=date(2025, 8, 1),
+            entry_close=100.0, measured_date=date(2025, 9, 1), realized_return=0.07, max_drawdown=-0.03,
+        ))
+        session.commit()
+    return engine
+
+
+def test_forward_agg_all_excluded_chunk_does_not_crash_the_merge(sparse_chunk_engine):
+    """Error case: an all-excluded chunk (zero qualifying `stock_obs` observations) must not crash the
+    merge, and must never fabricate a value for the excluded ticker — it simply contributes nothing, while
+    the run still legitimately counts via its own benchmark return."""
+    cfg = _cfg_run_chunk(1)  # isolates the sparse run into its own (all-excluded) chunk
+    with Session(sparse_chunk_engine) as session:
+        agg = compute_forward_aggregates(session, 20, cfg)
+    assert agg["n_runs"] == 1, "the run still legitimately enters runs_with_fr via its SPY return"
+    assert agg["overall"]["n"] == 0, "NOFR has no forward return anywhere -> zero stock observations"
+    assert agg["excess"]["vs_spy"]["benchmark_n"] == 1
+    assert agg["excess"]["vs_spy"]["benchmark_mean"] == pytest.approx(0.07)
+    tickers = {
+        row["ticker"]
+        for row in agg["attribution"]["per_stock"]["contributors"] + agg["attribution"]["per_stock"]["detractors"]
+    }
+    assert "NOFR" not in tickers
+
+
+# ----------------------------------------------------------------------------------------------------
+# TC-3 — the SHIPPED `walk_forward.forward_agg_run_chunk` must actually chunk on the live basis
+# (iter-29's binding lesson: a knob that degenerates to one chunk on the real basis binds nothing).
+# ----------------------------------------------------------------------------------------------------
+# The live basis measured during the iter-30 audit (direct read of the committed `trendora.db`,
+# 2026-07-29): 1,813-1,872 distinct scanner runs per horizon. A run-chunk width at/above the run count
+# degenerates to a single chunk, so the shipped width must stay well below it with room for years of
+# further daily-cadence growth; 500 is the loosest ceiling that still forces real chunking on today's
+# basis (>=3 chunks) and would have caught a shipped value re-using `research.read_batch_size` (2000).
+_MAX_MEANINGFUL_RUN_CHUNK = 500
+
+
+def test_shipped_forward_agg_run_chunk_actually_binds_on_the_live_basis():
+    """The SHIPPED `walk_forward.forward_agg_run_chunk` must be small enough to produce real chunking
+    against a multi-year daily-cadence basis — the regression guard for iter-29's binding lesson (a width
+    reused from another function's own knob, or otherwise too close to the live run count, means one
+    chunk and zero peak reduction, while every unit proof still passes because it typically overrides the
+    knob to a small fixture-sized value)."""
+    width = load_config().walk_forward.forward_agg_run_chunk
+    assert 1 <= width <= _MAX_MEANINGFUL_RUN_CHUNK, (
+        f"walk_forward.forward_agg_run_chunk={width} cannot bound the join accumulator on the live basis "
+        f"(1,813-1,872 distinct runs/horizon): it must be <= {_MAX_MEANINGFUL_RUN_CHUNK}"
+    )
+
+
+def test_forward_aggregates_chunks_at_the_shipped_config(tmp_path, monkeypatch):
+    """The accumulator is chunk-bounded under the SHIPPED config — no override. Builds a fixture with
+    (shipped width + 3) runs so real chunking is REQUIRED, then asserts `compute_forward_aggregates` made
+    >= 2 slice reads and no single slice ever held the whole fixture's (run_id, symbol) pairs."""
+    cfg = load_config()  # the REAL config.yaml — deliberately NOT overridden
+    width = cfg.walk_forward.forward_agg_run_chunk
+    horizon = cfg.walk_forward.horizons[0]
+    n_runs, tickers = width + 3, ("AA", "BB")
+    engine = make_engine(f"sqlite:///{tmp_path / 'shipped_chunk.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        for i in range(n_runs):
+            run = ScannerRun(
+                asof_date=date(2025, 1, 1) + timedelta(days=i), created_at=_utc(),
+                provider="seed", benchmark="SPY", regime_score=50.0, regime_label="Risk-on",
+                regime_components_json="[]", new_high_low_json="{}", candidate_counts_json="{}",
+            )
+            session.add(run)
+            session.flush()
+            for j, base in enumerate(tickers):
+                ticker = f"{base}{i}"
+                session.add(ScannerResult(
+                    run_id=run.id, ticker=ticker, name=ticker, sector="Technology",
+                    leadership_score=50.0, leadership_bucket="A", entry_quality_score=0.0,
+                    entry_quality_bucket="E", risk_score=0.0, risk_bucket="E",
+                    setup_status="Actionable", rank=j + 1, record_json="{}",
+                ))
+                session.add(ForwardReturn(
+                    run_id=run.id, symbol=ticker, horizon=horizon, asof_date=run.asof_date,
+                    entry_close=100.0, measured_date=date(2025, 12, 31),
+                    realized_return=0.01 * (i + 1) + 0.001 * j, max_drawdown=-0.02,
+                ))
+        session.commit()
+
+    observed_sizes: list[int] = []
+    real_slice_map = forward_testing_module._forward_agg_slice_map
+
+    def _wrapped(session, h, slice_run_ids, batch):
+        result = real_slice_map(session, h, slice_run_ids, batch)
+        observed_sizes.append(len(result))
+        return result
+
+    monkeypatch.setattr(forward_testing_module, "_forward_agg_slice_map", _wrapped)
+    with Session(engine) as session:
+        agg = compute_forward_aggregates(session, horizon, cfg)
+
+    total_pairs = n_runs * len(tickers)
+    assert agg["overall"]["n"] == total_pairs, "sanity: every fixture pair must surface as an observation"
+    assert len(observed_sizes) >= 2, (
+        f"the SHIPPED config produced {len(observed_sizes)} chunk(s) over {n_runs} runs — the accumulator "
+        f"bound is inert at the real configuration (width={width})"
+    )
+    assert max(observed_sizes) <= width * len(tickers), "a slice exceeded its configured run-chunk width"
+    assert max(observed_sizes) < total_pairs, (
+        "the live accumulator must never hold the WHOLE fixture's pairs at once under the shipped config"
+    )
+
+
+def test_shipped_forward_agg_run_chunk_binds_against_the_real_committed_seed():
+    """TC-3 (literal): against the LIVE committed seed DB's ACTUAL distinct-run count for a representative
+    horizon (never a fixture-sized width) — read-only, no ORM/engine machinery, a single indexed
+    COUNT(DISTINCT run_id) query — the shipped chunk width produces more than one chunk. Skips when the
+    committed seed DB is absent (matches `test_start_backend_script.py`'s established `REAL_DB`
+    convention)."""
+    if not REAL_DB.exists():
+        pytest.skip(f"real committed seed DB not found at {REAL_DB} — nothing to measure against")
+    cfg = load_config()
+    width = cfg.walk_forward.forward_agg_run_chunk
+    horizon = cfg.walk_forward.default_horizon
+    conn = sqlite3.connect(f"file:{REAL_DB}?mode=ro", uri=True)
+    try:
+        cur = conn.execute(
+            "SELECT COUNT(DISTINCT run_id) FROM forward_returns WHERE horizon = ?", (horizon,)
+        )
+        (live_run_count,) = cur.fetchone()
+    finally:
+        conn.close()
+    assert live_run_count > 0, "sanity: the committed seed must carry forward returns at the default horizon"
+    n_chunks = (live_run_count + width - 1) // width
+    assert n_chunks > 1, (
+        f"walk_forward.forward_agg_run_chunk={width} against the LIVE seed's {live_run_count} distinct "
+        f"runs at horizon={horizon} produces only {n_chunks} chunk(s) — the bound is inert on the real basis"
+    )
diff --git a/config.yaml b/config.yaml
index 40125bd7..26ba6f96 100644
--- a/config.yaml
+++ b/config.yaml
@@ -799,6 +799,14 @@ walk_forward:
   # smaller floor).
   underwater_horizons: [1, 5, 10, 20, 60]
   streak_min_n: 10
+  # ops-hardening iter-30 (AG-8, J-07) — the RUN-COUNT width of compute_forward_aggregates's OWN
+  # join-accumulator chunk (forward_testing.py). A DIFFERENT knob from research.read_batch_size (a ROWS
+  # count for yield_per) and research.factor_join_run_chunk (a different function's own run-chunk knob) —
+  # iter-29's binding lesson: reusing another function's knob as a run width can produce exactly one
+  # chunk and 0% peak reduction on the live basis. Peak live accumulator = this x symbols-per-run (~417
+  # measured), so 100 runs/chunk holds ~42K pairs instead of the full ~770K-803K per horizon (1,813-1,872
+  # distinct runs/horizon measured live, 2026-07-29). Must stay well below the live run count. Boot-validated >= 1.
+  forward_agg_run_chunk: 100
 
 # ----------------------------------------------------------------------------------------
 # iter-18 (J-10 performance) — GET /api/stocks/{ticker}/bars presentation bounding on the deep
```
