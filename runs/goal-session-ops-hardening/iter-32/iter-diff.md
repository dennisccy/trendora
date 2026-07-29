# Iteration diff (bounded)

Files changed: 3. Shown in full: 2.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/forward_testing.py` (219 lines not shown)

```diff
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index 24b17456..7ac6f8e1 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -40,6 +40,7 @@ import threading
 from calendar import monthrange
 from collections import defaultdict
 from datetime import date as date_cls, datetime, timedelta, timezone
+from fractions import Fraction
 from statistics import mean, median, stdev
 from typing import Optional, Union
 
@@ -593,6 +594,108 @@ def _mean_or_none(values: list[float]) -> Optional[float]:
     return mean(values) if values else None
 
 
+# --------------------------------------------------------------------------------------------------
+# ops-hardening iter-32 (AG-8, J-07) -- bounded per-group/per-ticker accumulators.
+#
+# `compute_forward_aggregates` used to grow ONE ~9-field dict per (run_id, ticker) observation
+# (`stock_obs`) across the WHOLE horizon-partition (770K-800K live) purely so `_group_means`/`_group_mdd`/
+# `_control_groups`/`_attribution_slices` could each re-derive their own group buckets from it at the very
+# end. `_ExactMeanAcc` below is the one piece that makes eliminating that list possible without changing
+# a single output value: it reproduces `statistics.mean`'s OWN algorithm (group floats by their EXACT
+# `as_integer_ratio()` denominator, sum the per-denominator numerators, convert the final exact Fraction
+# to float once) incrementally, one value at a time. Fraction addition is exact and therefore associative
+# and commutative -- the resulting mean is bit-for-bit identical to `statistics.mean(values)` regardless
+# of what order the values were added in, so a per-group running accumulator can replace a per-group LIST
+# of that group's returns with no behavior change (TC-2), while its own memory footprint is bounded by
+# the number of DISTINCT denominators IEEE-754 doubles can produce (at most a few thousand), never by how
+# many values were added (TC-1) -- unlike a per-group list of bare floats, which would still be a
+# constant-factor win "wearing a bound's clothes" (the iter-31 lesson), this genuinely stops scaling
+# with N.
+# --------------------------------------------------------------------------------------------------
+class _ExactMeanAcc:
+    """Streaming exact mean matching `statistics.mean`'s own exact-Fraction algorithm bit-for-bit,
+    without ever holding the added values themselves."""
+
+    __slots__ = ("_partials", "_count")
+
+    def __init__(self) -> None:
+        self._partials: dict[int, int] = {}
+        self._count = 0
+
+    def add(self, value: float) -> None:
+        numerator, denominator = value.as_integer_ratio()
+        self._partials[denominator] = self._partials.get(denominator, 0) + numerator
+        self._count += 1
+
+    @property
+    def n(self) -> int:
+        return self._count
+
+    def mean(self) -> Optional[float]:
+        if self._count == 0:
+            return None
+        total = sum(Fraction(numerator, denominator) for denominator, numerator in self._partials.items())
+        return float(total / self._count)
+
+
+class _GroupAcc:
+    """One group value's accumulated state: the group's return mean/n (`_group_means`'s `buckets`) paired
+    with its max-drawdown mean over ONLY the members that have a stored drawdown (`_group_mdd`'s NA-
+    intersection rule) -- the bounded, per-group-value replacement for both functions' per-group LISTS."""
+
+    __slots__ = ("returns", "mdds")
+
+    def __init__(self) -> None:
+        self.returns = _ExactMeanAcc()
+        self.mdds = _ExactMeanAcc()
+
+    def add(self, return_value: float, mdd_value: Optional[float]) -> None:
+        self.returns.add(return_value)
+        if mdd_value is not None:
+            self.mdds.add(mdd_value)
+
+
+def _accumulate_group(accs: dict, value, return_value: float, mdd_value: Optional[float]) -> None:
+    """`_group_means`'s own `if value is not None: buckets[value].append(...)` gate, applied to a
+    pre-aggregated `dict[value, _GroupAcc]` instead of a per-value list of raw observations."""
+    if value is not None:
+        accs[value].add(return_value, mdd_value)
+
+
+def _group_means_from_accs(accs: dict, label_key: str, order, pad: bool) -> list[dict]:
+    """`_group_means`'s exact row/order/pad contract (same ordering: `order` first -- padded to n=0/mean
+    None when `pad` and a value is missing -- then any extra observed values in sorted order), sourced
+    from PRE-AGGREGATED `dict[value, _GroupAcc]` state instead of a raw observation list. Byte-identical
+    output to `_group_means(observations, group_attr, label_key, order, pad)` for the same underlying
+    observations, since both ultimately derive `mean_return`/`mean_max_drawdown`/`n` from the SAME
+    per-group return/drawdown multisets (`_ExactMeanAcc.mean()`'s order-independence is what makes this
+    safe, TC-2)."""
+
+    def _row(value, acc: Optional[_GroupAcc]) -> dict:
+        if acc is None:
+            return {label_key: value, "mean_return": None, "mean_max_drawdown": None, "n": 0}
+        return {
+            label_key: value,
+            "mean_return": acc.returns.mean(),
+            "mean_max_drawdown": acc.mdds.mean(),
+            "n": acc.returns.n,
+        }
+
+    rows: list[dict] = []
+    emitted: set = set()
+    for value in order:
+        if value in accs:
+            rows.append(_row(value, accs[value]))
+            emitted.add(value)
+        elif pad:
+            rows.append(_row(value, None))
+            emitted.add(value)
+    for value in sorted(accs):
+        if value not in emitted:
+            rows.append(_row(value, accs[value]))
+    return rows
+
+
 def _group_mdd(observations: list[dict], group_attr: str) -> dict[str, list[float]]:
     """`group value -> [stored max_drawdown over the group's observations that HAVE one]` (iter-27, J-86).
     A group's mean-MDD is the mean over only the observations whose stored `max_drawdown` is non-None
@@ -646,6 +749,44 @@ def _group_means(observations: list[dict], group_attr: str, label_key: str, orde
     return rows
 
 
+def _control_group_run_contribution(
+    run_id: int,
+    run_obs: list[dict],
+    rng: random.Random,
+    cg,
+    etf_by_sector: dict[str, str],
+    ret_by_run_symbol: dict,
+) -> tuple[list[float], list[float], list[float]]:
+    """ONE run's contribution to the three per-run control-group cohorts (top-ranked / random same-sector
+    / sector-ETF) -- the per-run body `_control_groups` below walks in ascending run-id order over its
+    full `stock_obs` list. Factored out (ops-hardening iter-32) so `_ControlGroupBuilder` can drive the
+    IDENTICAL per-run logic, consuming the SAME shared `rng` instance one run at a time as each run's
+    complete observation set becomes available inside `compute_forward_aggregates`'s chunked loop, instead
+    of requiring the whole horizon's `stock_obs` materialized first. `rng` is mutated (advances its
+    stream) -- callers must share ONE instance across every run, in ascending run-id order, for the draw
+    sequence (and therefore every cohort's `mean_return`/`n`) to match `_control_groups`'s own sequence
+    (AG-5, TC-6)."""
+    top_sectors = sorted(
+        {o["sector"] for o in run_obs if o["rank"] is not None and o["rank"] <= cg.top_n and o["sector"]}
+    )
+    by_sector: dict[str, list[dict]] = defaultdict(list)
+    for o in run_obs:
+        if o["sector"]:
+            by_sector[o["sector"]].append(o)
+    top_returns = [o["return"] for o in run_obs if o["rank"] is not None and o["rank"] <= cg.top_n]
+    random_returns: list[float] = []
+    sector_etf_returns: list[float] = []
+    for sector in top_sectors:
+        pool = sorted(by_sector.get(sector, []), key=lambda o: o["ticker"])
+        if pool:
+            sample = rng.sample(pool, min(cg.peers_per_sector, len(pool)))
+            random_returns.extend(o["return"] for o in sample)
+        etf_ret = ret_by_run_symbol.get((run_id, etf_by_sector.get(sector)))
+        if etf_ret is not None:
+            sector_etf_returns.append(etf_ret)
+    return top_returns, random_returns, sector_etf_returns
+
+
 def _control_groups(
     horizon: int,
     stock_obs: list[dict],
@@ -656,7 +797,11 @@ def _control_groups(
     """The control-group cohorts at `horizon` (J-10): the top-ranked cohort vs a random same-sector
     cohort vs SPY / QQQ / sector-ETF — each numeric, labelled, with n. The random same-sector cohort is
     drawn with a deterministic RNG re-seeded from `control_group.seed` (reproducible across calls and
-    restarts), sampling `peers_per_sector` stocks per sector that the top-ranked cohort occupies."""
+    restarts), sampling `peers_per_sector` stocks per sector that the top-ranked cohort occupies. Kept as
+    the full-`stock_obs`-at-once implementation (byte-unchanged behavior; the per-run body lives in
+    `_control_group_run_contribution` above) -- `compute_run_scorecard`'s own small per-run `stock_obs`
+    and the byte-identity reference oracle both call this UNCHANGED signature (TC-7); `compute_forward_
+    aggregates` uses the incremental `_ControlGroupBuilder` counterpart instead (TC-1)."""
     cg = cfg.walk_forward.control_group
     bm = benchmark_symbols(cfg)
     etf_by_sector = _sector_etf_by_name(cfg)
@@ -671,25 +816,12 @@ def _control_groups(
     sector_etf_returns: list[float] = []
     # deterministic iteration order (sorted runs, sorted sectors, sorted pools) so RNG draws reproduce
     for run_id in sorted(obs_by_run):
-        run_obs = obs_by_run[run_id]
-        top_sectors = sorted(
-            {o["sector"] for o in run_obs if o["rank"] is not None and o["rank"] <= cg.top_n and o["sector"]}
+        run_top, run_random, run_sector_etf = _control_group_run_contribution(
+            run_id, obs_by_run[run_id], rng, cg, etf_by_sector, ret_by_run_symbol
         )
-        by_sector: dict[str, list[dict]] = defaultdict(list)
-        for o in run_obs:
-            if o["sector"]:
-                by_sector[o["sector"]].append(o)
-        for o in run_obs:
-            if o["rank"] is not None and o["rank"] <= cg.top_n:
-                top_returns.append(o["return"])
-        for sector in top_sectors:
-            pool = sorted(by_sector.get(sector, []), key=lambda o: o["ticker"])
-            if pool:
-                sample = rng.sample(pool, min(cg.peers_per_sector, len(pool)))
-                random_returns.extend(o["return"] for o in sample)
-            etf_ret = ret_by_run_symbol.get((run_id, etf_by_sector.get(sector)))
-            if etf_ret is not None:
-                sector_etf_returns.append(etf_ret)
+        top_returns.extend(run_top)
+        random_returns.extend(run_random)
+        sector_etf_returns.extend(run_sector_etf)
 
     spy_returns = [ret_by_run_symbol[(r, bm["spy"])] for r in runs_with_fr if (r, bm["spy"]) in ret_by_run_symbol]
     qqq_returns = [ret_by_run_symbol[(r, bm["qqq"])] for r in runs_with_fr if (r, bm["qqq"]) in ret_by_run_symbol]
@@ -706,6 +838,52 @@ def _control_groups(
     ]
 
 
+class _ControlGroupBuilder:
+    """Incremental counterpart to `_control_groups`, for `compute_forward_aggregates`'s chunked loop
+    (ops-hardening iter-32, TC-1/TC-6): the SAME per-run contribution (`_control_group_run_contribution`),
+    fed one run at a time via `consume_run` as each run's COMPLETE observation set becomes available
+    (chunk boundaries never split a run, iter-30), in the SAME ascending run-id order `_control_groups`
+    itself walks -- so the shared `rng`'s draw sequence, and therefore every cohort's `mean_return`/`n`,
+    is identical to calling `_control_groups` on the full `stock_obs` list at once (TC-6), while this
+    builder never holds more than the three running `_ExactMeanAcc` totals (bounded, never one entry per
+    observation)."""
+
+    def __init__(self, cfg: Config) -> None:
+        self._cg = cfg.walk_forward.control_group
+        self._etf_by_sector = _sector_etf_by_name(cfg)
+        self._rng = random.Random(self._cg.seed)  # ONE shared instance, advanced run-by-run
+        self._top_returns = _ExactMeanAcc()
+        self._random_returns = _ExactMeanAcc()
+        self._sector_etf_returns = _ExactMeanAcc()
+
+    def consume_run(self, run_id: int, run_obs: list[dict], bm_returns: dict) -> None:
+        """`run_obs` must be run `run_id`'s COMPLETE observation set (never a partial slice) -- callers
+        rely on chunk boundaries never splitting a run (iter-30) to guarantee this."""
+        top, rand, sector_etf = _control_group_run_contribution(
+            run_id, run_obs, self._rng, self._cg, self._etf_by_sector, bm_returns
+        )
+        for value in top:
+            self._top_returns.add(value)
+        for value in rand:
+            self._random_returns.add(value)
+        for value in sector_etf:
+            self._sector_etf_returns.add(value)
+
+    def finalize(self, bm: dict, runs_with_fr: list[int], bm_returns: dict) -> list[dict]:
+        spy_returns = [bm_returns[(r, bm["spy"])] for r in runs_with_fr if (r, bm["spy"]) in bm_returns]
+        qqq_returns = [bm_returns[(r, bm["qqq"])] for r in runs_with_fr if (r, bm["qqq"]) in bm_returns]
+        return [
+            {"key": "top_ranked", "label": f"Top-ranked cohort (rank ≤ {self._cg.top_n})",
+             "mean_return": self._top_returns.mean(), "n": self._top_returns.n},
+            {"key": "random_same_sector", "label": "Random same-sector peers",
+             "mean_return": self._random_returns.mean(), "n": self._random_returns.n},
+            {"key": "spy", "label": bm["spy"], "mean_return": _mean_or_none(spy_returns), "n": len(spy_returns)},
+            {"key": "qqq", "label": bm["qqq"], "mean_return": _mean_or_none(qqq_returns), "n": len(qqq_returns)},
+            {"key": "sector_etf", "label": "Sector ETF (same sectors)",
+             "mean_return": self._sector_etf_returns.mean(), "n": self._sector_etf_returns.n},
+        ]
+
+
 # --------------------------------------------------------------------------------------------------
 # Return attribution (J-19) — four READ-ONLY slices of the ALREADY-BUILT per-observation stock_obs
 # --------------------------------------------------------------------------------------------------
@@ -721,22 +899,59 @@ def _rank_band_label(rank: Optional[int], rank_bands) -> Optional[str]:
     return None
 
 
-def _per_stock_attribution(stock_obs: list[dict], top_k: int) -> dict:
-    """Per-stock contributors / detractors: each ticker's mean realized return + n + STORED sector over
-    the SAME observations (no recomputed return), the highest `top_k` means as contributors and the
-    lowest `top_k` as detractors (deterministic ticker tie-break). Empty observations -> empty lists."""
-    returns_by_ticker: dict[str, list[float]] = defaultdict(list)
-    sector_by_ticker: dict[str, Optional[str]] = {}
-    for obs in stock_obs:
-        returns_by_ticker[obs["ticker"]].append(obs["return"])
-        sector_by_ticker.setdefault(obs["ticker"], obs.get("sector"))
-    rows = [
-        {"ticker": ticker, "mean_return": mean(rets), "n": len(rets), "sector": sector_by_ticker[ticker]}
-        for ticker, rets in returns_by_ticker.items()
-    ]
-    contributors = sorted(rows, key=lambda r: (-r["mean_return"], r["ticker"]))[:top_k]
-    detractors = sorted(rows, key=lambda r: (r["mean_return"], r["ticker"]))[:top_k]
-    return {"contributors": contributors, "detractors": detractors}
+class _AttributionAccumulator:
+    """Bounded incremental state for `_attribution_slices`'s three group-shaped panels (`per_stock`/
+    `by_sector`/`by_rank_band`) plus the ONE disclosed bare-float exception (`distribution`) -- built one
+    observation at a time via `add`, either from `compute_forward_aggregates`'s chunked loop (never
+    holding the whole horizon's `stock_obs`) or from a small hand-built list via `from_observations`
+    (`compute_run_scorecard`'s own already-small per-run `stock_obs`, and this module's direct-call unit
+    tests). `per_stock`/`by_sector`/`by_rank_band` are bounded by the number of DISTINCT tickers/sectors/
+    rank-bands, never by the observation count (TC-1); `distribution`'s exact median/stdev has no O(1)
+    streaming equivalent, so its bare-`float` return list (never a full observation dict) is the ONE
+    still-O(N) exception the spec discloses.
+
+    `_attribution_slices` below reads this state read-only -- it holds no Session and issues no query,
+    preserving the anti-goal "Attribution is read-only" this module's tests pin structurally."""
+
+    __slots__ = ("_rank_bands", "_per_ticker_returns", "_per_ticker_sector", "by_sector", "by_rank_band", "returns")
+
+    def __init__(self, rank_bands) -> None:
+        self._rank_bands = rank_bands
+        self._per_ticker_returns: dict[str, _ExactMeanAcc] = {}
+        self._per_ticker_sector: dict[str, Optional[str]] = {}
+        self.by_sector: dict[str, _GroupAcc] = defaultdict(_GroupAcc)
+        self.by_rank_band: dict[str, _GroupAcc] = defaultdict(_GroupAcc)
+        self.returns: list[float] = []  # the disclosed bare-float exception (exact median/dispersion)
+
+    @classmethod
+    def from_observations(cls, observations, rank_bands) -> "_AttributionAccumulator":
+        acc = cls(rank_bands)
+        for obs in observations:
+            acc.add(obs)
+        return acc
+
+    def add(self, obs: dict) -> None:
+        ticker, return_value = obs["ticker"], obs["return"]
+        sector, rank, mdd = obs.get("sector"), obs.get("rank"), obs.get("max_drawdown")
+        self.returns.append(return_value)
+        if ticker not in self._per_ticker_returns:
+            self._per_ticker_returns[ticker] = _ExactMeanAcc()
+            self._per_ticker_sector[ticker] = sector  # first occurrence wins (mirrors setdefault)
+        self._per_ticker_returns[ticker].add(return_value)
+        _accumulate_group(self.by_sector, sector, return_value, mdd)
+        _accumulate_group(self.by_rank_band, _rank_band_label(rank, self._rank_bands), return_value, mdd)
+
+    def per_stock(self, top_k: int) -> dict:
+        """`_per_stock_attribution`'s exact contract: each ticker's mean realized return + n + STORED
+        sector, highest `top_k` means as contributors and lowest `top_k` as detractors (deterministic
+        ticker tie-break)."""
+        rows = [
+            {"ticker": ticker, "mean_return": acc.mean(), "n": acc.n, "sector": self._per_ticker_sector[ticker]}
+            for ticker, acc in self._per_ticker_returns.items()
+        ]
+        contributors = sorted(rows, key=lambda r: (-r["mean_return"], r["ticker"]))[:top_k]
+        detractors = sorted(rows, key=lambda r: (r["mean_return"], r["ticker"]))[:top_k]
+        return {"contributors": contributors, "detractors": detractors}
 
 
 def _distribution(returns: list[float]) -> dict:
@@ -756,31 +971,34 @@ def _distribution(returns: list[float]) -> dict:
     }
 
 
-def _attribution_slices(stock_obs: list[dict], cfg: Config) -> dict:
-    """The four READ-ONLY return-attribution slices (J-19), derived ENTIRELY from the ALREADY-BUILT
-    per-observation `stock_obs` (stored realized returns joined to stored `scanner_results`, read
-    verbatim) + config. It recomputes NO return and takes NO Session, so it can issue no second
-    forward_returns / price-bar query — this IS the anti-goal "Attribution is read-only": the slices
-    are pure groupings of the SAME observations the aggregate / scorecard already measured (no second
-    formula, no second data source; consistency with the aggregate mean is unit-asserted).
+def _attribution_slices(acc: _AttributionAccumulator, cfg: Config) -> dict:
+    """The four READ-ONLY return-attribution slices (J-19), derived ENTIRELY from an ALREADY-BUILT
+    `_AttributionAccumulator` (stored realized returns joined to stored `scanner_results`, read verbatim,
+    incrementally accumulated -- never a second query) + config. It recomputes NO return and takes NO
+    Session, so it can issue no second forward_returns / price-bar query — this IS the anti-goal
+    "Attribution is read-only": the slices are pure groupings of the SAME observations the aggregate /
+    scorecard already measured (no second formula, no second data source; consistency with the aggregate
+    mean is unit-asserted).
 
       - per_stock     contributors (highest mean) / detractors (lowest mean), each `top_contributors_k`
       - by_sector     mean realized return + n per STORED sector (config sector-name order; non-padded)
       - by_rank_band  mean realized return + n per config rank band (every band padded to n=0)
       - distribution  mean / median / % positive (hit rate) / dispersion (stdev) of the same returns
-    """
+
+    ops-hardening iter-32: this signature was previously the frozen, test-pinned `(stock_obs: list[dict],
+    cfg)` -- lifted ON PURPOSE so the caller can hand in incrementally-built, bounded state instead of a
+    full per-observation list (the last unbounded accumulator inside `compute_forward_aggregates`, TC-1).
+    `_AttributionAccumulator.from_observations(...)` reconstructs the old convenience for callers that
+    still have (or want) a small, already-materialized observation list (`compute_run_scorecard`'s own
+    per-run `stock_obs`, and this module's direct-call unit tests)."""
     attribution = cfg.walk_forward.attribution
     sector_order = list(cfg.etfs.sector.values())  # config sector NAMES (never a literal sector list)
     band_order = [band.label for band in attribution.rank_bands]
-    banded_obs = [
-        {**obs, "rank_band": _rank_band_label(obs.get("rank"), attribution.rank_bands)}
-        for obs in stock_obs
-    ]
     return {
-        "per_stock": _per_stock_attribution(stock_obs, attribution.top_contributors_k),
-        "by_sector": _group_means(stock_obs, "sector", "sector", sector_order, pad=False),
-        "by_rank_band": _group_means(banded_obs, "rank_band", "rank_band", band_order, pad=True),
-        "distribution": _distribution([obs["return"] for obs in stock_obs]),
+        "per_stock": acc.per_stock(attribution.top_contributors_k),
+        "by_sector": _group_means_from_accs(acc.by_sector, "sector", sector_order, pad=False),
+        "by_rank_band": _group_means_from_accs(acc.by_rank_band, "rank_band", band_order, pad=True),
+        "distribution": _distribution(acc.returns),
     }
 
 
@@ -936,20 +1154,28 @@ def compute_forward_aggregates(
     inspection: neither ever looks up a regular stock ticker in it), then discards the slice map before the
     next chunk — the two named join dicts never again hold the full horizon-partition at once.
 
-    `stock_obs` itself is still assembled to full size by the end of the loop: `_attribution_slices`
-    (below) is a frozen, test-pinned `(stock_obs, cfg)` read-only contract
-    (`test_attribution_is_pure_over_passed_observations_no_new_query`) that several other tests also call
-    directly with hand-built observation lists, so it still needs one materialized list — but it never again
-    CO-EXISTS with a full-size join accumulator, only with the current chunk's small one. `_group_means`,
-    `_group_mdd`, `_control_groups`, `_attribution_slices`, and the VCP/pullback/breakout groupings are all
... [diff_bound] apps/backend/app/engine/forward_testing.py: 219 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_forward_testing.py b/apps/backend/tests/test_forward_testing.py
index 908045ed..e7463c1f 100644
--- a/apps/backend/tests/test_forward_testing.py
+++ b/apps/backend/tests/test_forward_testing.py
@@ -1193,11 +1193,16 @@ def test_attribution_rank_band_with_no_members_is_padded(aggregates_engine):
 
 def test_attribution_empty_observations_are_all_na():
     """Honesty: empty observations -> every slice NA with n=0 (no fabricated 0%). by_rank_band stays
-    padded (every config band present at n=0); by_sector (non-padded) is empty."""
-    from app.engine.forward_testing import _attribution_slices
+    padded (every config band present at n=0); by_sector (non-padded) is empty.
+
+    ops-hardening iter-32: `_attribution_slices`'s frozen `(stock_obs, cfg)` signature was lifted ON
+    PURPOSE (ops-hardening iter-32, TC-3) to `(acc: _AttributionAccumulator, cfg)` — an empty accumulator
+    (zero `.add()` calls) is the new contract's equivalent of the old empty `stock_obs` list."""
+    from app.engine.forward_testing import _AttributionAccumulator, _attribution_slices
 
     cfg = load_config()
-    attr = _attribution_slices([], cfg)
+    acc = _AttributionAccumulator.from_observations([], cfg.walk_forward.attribution.rank_bands)
+    attr = _attribution_slices(acc, cfg)
     assert attr["per_stock"]["contributors"] == [] and attr["per_stock"]["detractors"] == []
     assert attr["distribution"] == {
         "mean_return": None, "median": None, "pct_positive": None, "dispersion": None, "n": 0
@@ -1212,11 +1217,14 @@ def test_attribution_empty_observations_are_all_na():
 def test_attribution_single_observation_dispersion_is_null():
     """A single-observation slice has no defined standard deviation -> dispersion null (no spurious 0
     stdev); mean / median equal the single value and the hit-rate is 1.0."""
-    from app.engine.forward_testing import _attribution_slices
+    from app.engine.forward_testing import _AttributionAccumulator, _attribution_slices
 
-    dist = _attribution_slices(
-        [{"ticker": "AAA", "return": 0.05, "sector": "Technology", "rank": 1}], load_config()
-    )["distribution"]
+    cfg = load_config()
+    acc = _AttributionAccumulator.from_observations(
+        [{"ticker": "AAA", "return": 0.05, "sector": "Technology", "rank": 1}],
+        cfg.walk_forward.attribution.rank_bands,
+    )
+    dist = _attribution_slices(acc, cfg)["distribution"]
     assert dist["n"] == 1
     assert dist["mean_return"] == pytest.approx(0.05) and dist["median"] == pytest.approx(0.05)
     assert dist["pct_positive"] == pytest.approx(1.0)
@@ -1225,18 +1233,26 @@ def test_attribution_single_observation_dispersion_is_null():
 
 def test_attribution_is_pure_over_passed_observations_no_new_query():
     """Read-only / no new query (the critical anti-goal, structural proof): `_attribution_slices` is a
-    pure function of the ALREADY-BUILT `stock_obs` + cfg — it takes NO Session, so it can issue no
-    forward_returns / price-bar query. The same observation list that feeds the aggregate feeds the
-    slices: no second formula, no second data source."""
+    pure function of an ALREADY-BUILT `_AttributionAccumulator` + cfg — it takes NO Session, so it can
+    issue no forward_returns / price-bar query. The same observations that feed the aggregate feed the
+    slices: no second formula, no second data source.
+
+    ops-hardening iter-32: the previously frozen `(stock_obs, cfg)` signature is lifted ON PURPOSE (TC-3)
+    so `compute_forward_aggregates` can hand in incrementally-built, bounded state (TC-1) instead of a
+    full per-observation list — `_AttributionAccumulator.from_observations` reconstructs the old
+    convenience for small, already-materialized lists like this test's."""
     import inspect
 
-    from app.engine.forward_testing import _attribution_slices
+    from app.engine.forward_testing import _AttributionAccumulator, _attribution_slices
 
-    assert set(inspect.signature(_attribution_slices).parameters) == {"stock_obs", "cfg"}
-    attr = _attribution_slices(
-        [{"ticker": "AAA", "return": 0.10, "sector": "Technology", "rank": 1}], load_config()
+    assert set(inspect.signature(_attribution_slices).parameters) == {"acc", "cfg"}
+    cfg = load_config()
+    acc = _AttributionAccumulator.from_observations(
+        [{"ticker": "AAA", "return": 0.10, "sector": "Technology", "rank": 1}],
+        cfg.walk_forward.attribution.rank_bands,
     )
-    assert attr["distribution"]["n"] == 1  # produced from a hand list with no DB access at all
+    attr = _attribution_slices(acc, cfg)
+    assert attr["distribution"]["n"] == 1  # produced from a hand-built accumulator with no DB access at all
 
 
 def test_stored_scores_identical_with_and_without_forward_returns(backfilled_engine):
diff --git a/apps/backend/tests/test_forward_testing_aggregates_streaming.py b/apps/backend/tests/test_forward_testing_aggregates_streaming.py
index 9c02e494..0f086dbd 100644
--- a/apps/backend/tests/test_forward_testing_aggregates_streaming.py
+++ b/apps/backend/tests/test_forward_testing_aggregates_streaming.py
@@ -29,8 +29,11 @@ compare the SAME real `compute_forward_aggregates` against this SAME reference,
 from __future__ import annotations
 
 import sqlite3
+import tracemalloc
+from collections import defaultdict
 from datetime import date, datetime, timedelta, timezone
 from pathlib import Path
+from statistics import mean
 
 import pytest
 from sqlmodel import Session, select
@@ -44,10 +47,14 @@ from app.engine.forward_testing import (
     PULLBACK_LABELS,
     SURVIVORSHIP_BIAS_LABEL,
     VCP_LABELS,
-    _attribution_slices,
+    _accumulate_group,
+    _AttributionAccumulator,
     _control_groups,
+    _distribution,
+    _GroupAcc,
     _group_means,
     _mean_or_none,
+    _rank_band_label,
     benchmark_symbols,
     compute_forward_aggregates,
 )
@@ -57,6 +64,50 @@ from app.models import ForwardReturn, ScannerResult, ScannerRun
 REPO_ROOT = Path(__file__).resolve().parents[3]
 REAL_DB = REPO_ROOT / "apps/backend/data/trendora.db"
 
+
+# --------------------------------------------------------------------------------------------------
+# Pinned PRE-iter-32 attribution implementation (audit iter-32).
+#
+# `_attribution_slices` was restructured this iteration to read an `_AttributionAccumulator` instead of a
+# full `stock_obs` list, and `_per_stock_attribution` was folded into that class. If the reference below
+# simply called the NEW `_attribution_slices` (as the developer's first version did), the byte-identity
+# oracle would compare the new implementation against ITSELF for the `attribution` key -- one of the ten
+# top-level keys TC-2 requires -- and could never detect an attribution behavior change. These two
+# functions are the verbatim pre-iter-32 bodies (`git show HEAD:...forward_testing.py`), so the oracle
+# stays an INDEPENDENT reference for every key. `_group_means`/`_distribution`/`_rank_band_label` are
+# imported from the module because this iteration left them byte-unchanged.
+# --------------------------------------------------------------------------------------------------
+def _reference_per_stock_attribution(stock_obs: list[dict], top_k: int) -> dict:
+    returns_by_ticker: dict[str, list[float]] = defaultdict(list)
+    sector_by_ticker: dict[str, object] = {}
+    for obs in stock_obs:
+        returns_by_ticker[obs["ticker"]].append(obs["return"])
+        sector_by_ticker.setdefault(obs["ticker"], obs.get("sector"))
+    rows = [
+        {"ticker": ticker, "mean_return": mean(rets), "n": len(rets), "sector": sector_by_ticker[ticker]}
+        for ticker, rets in returns_by_ticker.items()
+    ]
+    contributors = sorted(rows, key=lambda r: (-r["mean_return"], r["ticker"]))[:top_k]
+    detractors = sorted(rows, key=lambda r: (r["mean_return"], r["ticker"]))[:top_k]
+    return {"contributors": contributors, "detractors": detractors}
+
+
+def _reference_attribution_slices(stock_obs: list[dict], cfg) -> dict:
+    attribution = cfg.walk_forward.attribution
+    sector_order = list(cfg.etfs.sector.values())
+    band_order = [band.label for band in attribution.rank_bands]
+    banded_obs = [
+        {**obs, "rank_band": _rank_band_label(obs.get("rank"), attribution.rank_bands)}
+        for obs in stock_obs
+    ]
+    return {
+        "per_stock": _reference_per_stock_attribution(stock_obs, attribution.top_contributors_k),
+        "by_sector": _group_means(stock_obs, "sector", "sector", sector_order, pad=False),
+        "by_rank_band": _group_means(banded_obs, "rank_band", "rank_band", band_order, pad=True),
+        "distribution": _distribution([obs["return"] for obs in stock_obs]),
+    }
+
+
 # --------------------------------------------------------------------------------------------------
 # Pinned pre-rewrite reference implementation (the two `.all()` reads this iteration replaces)
 # --------------------------------------------------------------------------------------------------
@@ -167,7 +218,11 @@ def _reference_compute_forward_aggregates(session: Session, horizon: int, config
         "by_flat_base_breakout": by_flat_base_breakout,
         "excess": excess,
         "control_group": _control_groups(horizon, stock_obs, ret_by_run_symbol, runs_with_fr, cfg),
-        "attribution": _attribution_slices(stock_obs, cfg),
+        # ops-hardening iter-32: `_attribution_slices`'s frozen `(stock_obs, cfg)` signature was lifted ON
+        # PURPOSE for the real function's restructuring (TC-3). AUDIT iter-32: this reference calls the
+        # PINNED pre-iter-32 attribution body above rather than the new `_attribution_slices` -- otherwise
+        # this key would be compared against itself and TC-2 would cover only 9 of its 10 keys.
+        "attribution": _reference_attribution_slices(stock_obs, cfg),
     }
 
 
@@ -566,3 +621,111 @@ def test_shipped_forward_agg_run_chunk_binds_against_the_real_committed_seed():
         f"walk_forward.forward_agg_run_chunk={width} against the LIVE seed's {live_run_count} distinct "
         f"runs at horizon={horizon} produces only {n_chunks} chunk(s) — the bound is inert on the real basis"
     )
+
+
+# ====================================================================================================
+# ops-hardening iter-32 (AG-8, J-07) — `stock_obs`, the LAST unbounded accumulator in this function's own
+# family, is gone: `_group_means`/`_group_mdd`/`_control_groups`'s per-group/per-run consumers and
+# `_attribution_slices`'s `per_stock`/`by_sector`/`by_rank_band` are now driven by state built
+# INCREMENTALLY inside the per-chunk loop, bounded by the number of distinct groups/runs/tickers rather
+# than by the observation count. This section proves the bound (TC-1) — a test that fails if the
+# restructuring were reverted to the old full-`stock_obs` design.
+#
+# This test feeds synthetic observations DIRECTLY into the same accumulation primitives
+# `compute_forward_aggregates` uses internally (`_GroupAcc`/`_accumulate_group`/`_AttributionAccumulator`),
+# bypassing the DB/ORM read path entirely -- a dev-pass measurement discovered that going through the real
+# `compute_forward_aggregates(session, ...)` call confounds this iteration's accumulators with `run_rows`
+# (`session.exec(select(ScannerRun)...).all()`, one ORM object per RUN, unchanged since iter-14 and
+# EXPLICITLY documented there as "bounded, small... not one of the named unbounded offenders this
+# iteration fixes" -- verified separately: tripling run count alone roughly triples `run_rows`'s own
+# tracemalloc peak, which would make a whole-function measurement fail for a reason THIS iteration never
+# claimed to fix). Isolating the accumulation step targets exactly what TC-1 asks about; the live
+# full-deep-basis warm (TC-4/TC-5, see the dev handoff) is the end-to-end proof that the real function
+# does not crash at the actual ~800K-observation live scale.
+# ====================================================================================================
+def _accumulate_synthetic_observations(n_obs: int, rank_bands, *, retain_distribution: bool = True):
+    """Feeds `n_obs` synthetic observations through the SAME per-observation accumulation primitives
+    `compute_forward_aggregates` calls inside its per-chunk loop, at a FIXED small cardinality (3 tickers,
+    1 sector, 1 bucket, 1 setup, 2 regimes) -- returns the resulting accumulators (never a per-observation
+    list).
+
+    `retain_distribution=False` drops each observation's realized return immediately after it has been
+    accumulated, so the measured state is EXACTLY the quantity TC-1 names -- "peak size attributable to
+    the by-group/per-stock accumulation paths" -- with the spec's ONE disclosed still-O(N) exception
+    (`_AttributionAccumulator.returns`, the bare-float list the exact median/dispersion needs) excluded by
+    construction. Nothing else reads that list, so clearing it changes no accumulated group/ticker state
+    (audit iter-32)."""
+    bucket_accs: dict = defaultdict(_GroupAcc)
+    setup_accs: dict = defaultdict(_GroupAcc)
+    regime_accs: dict = defaultdict(_GroupAcc)
+    attribution_acc = _AttributionAccumulator(rank_bands)
+    tickers = ("AAA", "BBB", "CCC")
+    for i in range(n_obs):
+        realized, mdd = 0.001 * (i + 1), -0.01
+        obs = {"ticker": tickers[i % 3], "return": realized, "max_drawdown": mdd, "sector": "Technology", "rank": 1}
+        _accumulate_group(bucket_accs, "A", realized, mdd)
+        _accumulate_group(setup_accs, "Actionable", realized, mdd)
+        _accumulate_group(regime_accs, "Risk-on" if i % 2 == 0 else "Risk-off", realized, mdd)
+        attribution_acc.add(obs)
+        if not retain_distribution:
+            attribution_acc.returns.clear()
+    return bucket_accs, setup_accs, regime_accs, attribution_acc
+
+
+def test_accumulator_peak_size_does_not_scale_with_observation_count_at_fixed_cardinality():
+    """TC-1: at a FIXED small group/ticker cardinality (3 tickers, 1 sector, 1 bucket, 1 setup, 2 regimes),
+    quintupling the observation count (40 -> 200) must not come CLOSE to quintupling the tracemalloc-
+    measured peak of the by-group/per-stock accumulation paths -- calibrated against a dev-pass
+    measurement of the OLD full-`stock_obs`-list design under the SAME 5x delta (peak ratio ~5.6x, close
+    to proportional, as expected for a genuine per-observation list): the new design's ratio measures
+    ~2.0-2.8x across several (n_small, n_large) pairs at this delta (the ONE disclosed exception,
+    `_AttributionAccumulator.returns`'s bare-float `distribution` list, does still grow linearly, so the
+    ratio is not 1.0x -- only proportional-to-old growth would be a regression). The 4.0x threshold below
+    sits with margin above the new design's observed range and with margin below the old design's, so this
+    test fails if the restructuring were reverted.
+
+    AUDIT iter-32 -- second assertion added. The first assertion's metric INCLUDES the spec's disclosed
+    still-O(N) `distribution` list, so it is scale-dependent by construction: measured on the SHIPPED
+    (correct) code it is 2.00x at 40->200 but 4.70x at 5,000->25,000 and 4.77x at 20,000->100,000, i.e. it
+    converges on fully-proportional growth as the surviving linear term stops being diluted by fixed
+    overhead. It therefore discriminates against the old design only at the small n it was calibrated at.
+    The second assertion below measures what TC-1 actually names -- the by-group/per-stock accumulation
+    paths alone -- at a 5x delta two orders of magnitude larger, where the shipped design measures 1.29x
+    (25.5 kB -> 27.8 kB; the residual growth is `_ExactMeanAcc`'s DISTINCT-denominator partials, bounded by
+    the exponent range of IEEE-754 doubles, never by n) against ~5.1x for the reverted full-`stock_obs`
+    design. That assertion is scale-robust: it holds at 20,000->100,000 too (1.09x)."""
+    rank_bands = load_config().walk_forward.attribution.rank_bands
+    n_small, n_large = 40, 200
+
+    def _peak(n: int, *, retain_distribution: bool = True) -> int:
+        # warm up (import/dict-resize caches)
+        _accumulate_synthetic_observations(n, rank_bands, retain_distribution=retain_distribution)
+        tracemalloc.start()
+        try:
+            _accumulate_synthetic_observations(n, rank_bands, retain_distribution=retain_distribution)
+            _, peak = tracemalloc.get_traced_memory()
+        finally:
+            tracemalloc.stop()
+        return peak
+
+    peak_small, peak_large = _peak(n_small), _peak(n_large)
+
+    assert peak_large < peak_small * 4.0, (
+        f"peak memory grew from {peak_small} to {peak_large} bytes when observation count went from "
+        f"{n_small} to {n_large} (5x) at a fixed 3-ticker/1-sector/1-bucket/1-setup/2-regime cardinality — "
+        f"the by-group/per-stock accumulation paths must not scale proportionally with observation count "
+        f"(TC-1)"
+    )
+
+    # TC-1 as the spec words it: the by-group/per-stock accumulation paths ALONE (the disclosed bare-float
+    # `distribution` list excluded), at a delta where a per-observation retention would be unmistakable.
+    iso_small, iso_large = 5_000, 25_000
+    iso_peak_small = _peak(iso_small, retain_distribution=False)
+    iso_peak_large = _peak(iso_large, retain_distribution=False)
+
+    assert iso_peak_large < iso_peak_small * 2.0, (
+        f"by-group/per-stock accumulation state grew from {iso_peak_small} to {iso_peak_large} bytes when "
+        f"observation count went from {iso_small} to {iso_large} (5x) at FIXED group/ticker cardinality — "
+        f"these paths must be bounded by the number of DISTINCT groups/tickers, never by the observation "
+        f"count (TC-1; shipped design measures ~1.3x here, the reverted full-`stock_obs` design ~5.1x)"
+    )
```
