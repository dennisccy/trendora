# Iteration diff (bounded)

Files changed: 17. Shown in full: 17.

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 32b8eb3..17941cf 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -285,6 +285,15 @@ class IndicatorsCfg(BaseModel):
     # bars_asof series is never fed whole into a ~252-bar-max indicator. Validated below to be >= every
     # individually-configured window on THIS model; the byte-identity harness is the real authority.
     max_lookback_bars: int
+    # iter-40 (J-24, B-201 risk-budget card): the overnight-gap-profile window (median/p95/worst +
+    # overnight variance share, `indicators:overnight_gap_profile`) — read from the SAME
+    # `max_lookback_bars`-bounded trailing slice `scoring.py` already fetches (no extra bar fetch).
+    gap_window: int
+    # The worst-trailing-N-day-return window (`indicators:worst_20d_window`) — scans the name's FULL
+    # as-of history (NOT the max_lookback_bars-bounded slice; see scoring.py pass-3), so this value is
+    # NOT itself bounded by max_lookback_bars — it is still validated positive below alongside every
+    # other indicator window (No magic numbers).
+    worst_window_days: int
 
     @model_validator(mode="after")
     def _validate(self) -> "IndicatorsCfg":
@@ -307,6 +316,8 @@ class IndicatorsCfg(BaseModel):
             "vol_contraction_recent": self.vol_contraction_recent,
             "vol_contraction_prior": self.vol_contraction_prior,
             "max_lookback_bars": self.max_lookback_bars,
+            "gap_window": self.gap_window,
+            "worst_window_days": self.worst_window_days,
         }
         nonpositive = sorted(k for k, v in scalars.items() if v <= 0)
         if nonpositive:
@@ -315,6 +326,10 @@ class IndicatorsCfg(BaseModel):
         # window must cover every consumer fed by a bars_asof-sliced series on THIS model (a
         # different model's pattern min_history_bars is cross-checked on Config below, mirroring
         # `_pattern_ma_period_is_an_indicator_period`'s "a sub-model cannot see indicators" note).
+        # iter-40: gap_window/worst_window_days folded in alongside hv_window/semivol_window (mirrored
+        # treatment) — even though worst_window_days's consumer reads the FULL as-of history rather
+        # than this bounded slice, keeping every configured indicator window <= max_lookback_bars is a
+        # cheap, harmless general consistency guard.
         max_needed = max(
             max(self.ma_periods),
             max(self.rs_windows.values()) + 1,  # rs_vs needs window + 1 bars
@@ -324,6 +339,8 @@ class IndicatorsCfg(BaseModel):
             self.hv_window + 1,
             self.semivol_window + 1,
             self.vol_contraction_recent + self.vol_contraction_prior + 1,
+            self.gap_window + 1,
+            self.worst_window_days + 1,
         )
         if self.max_lookback_bars < max_needed:
             raise ValueError(
diff --git a/apps/backend/app/engine/indicators.py b/apps/backend/app/engine/indicators.py
index 4e4b9c6..7d98867 100644
--- a/apps/backend/app/engine/indicators.py
+++ b/apps/backend/app/engine/indicators.py
@@ -197,6 +197,19 @@ def vol_contraction(closes: Sequence[float], recent: int, prior: int) -> Optiona
     return _population_stdev(rets[-recent:]) / prior_vol  # the later (recent) block / baseline
 
 
+def _percentile(sorted_values: Sequence[float], pct: float) -> float:
+    """Linear-interpolation percentile (the standard definition) of an ALREADY-ASCENDING-SORTED
+    sequence at `pct` in [0,1]. A single-value sequence returns that value regardless of `pct`."""
+    n = len(sorted_values)
+    if n == 1:
+        return sorted_values[0]
+    rank = pct * (n - 1)
+    lower = int(rank)
+    upper = min(lower + 1, n - 1)
+    frac = rank - lower
+    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * frac
+
+
 def downside_vol(closes: Sequence[float], window: int) -> Optional[float]:
     """Downside / semi-volatility (downside leg ONLY): the trailing downside semideviation of the last
     `window` daily simple returns about MAR=0 — `sqrt(mean(min(r, 0)**2))`. Only NEGATIVE returns
@@ -212,3 +225,82 @@ def downside_vol(closes: Sequence[float], window: int) -> Optional[float]:
     if rets is None:
         return NA
     return sqrt(sum(min(r, 0) ** 2 for r in rets) / len(rets))
+
+
+# --- iter-40 risk-budget family (J-24 / B-201) -----------------------------------------------
+# Two more NA-graceful, config-windowed, bars<=D-only functions, computed once in the scoring/snapshot
+# path and STORED (additively) for the stock-detail risk-budget card + leaderboard columns — like the
+# iter-13 volatility family above, they enter NO weighted score.
+
+def overnight_gap_profile(
+    opens: Sequence[float], closes: Sequence[float], window: int
+) -> Optional[dict]:
+    """The overnight-gap risk profile over the trailing `window` sessions — the risk an invalidation
+    level cannot protect against, since a level only triggers on a gradual decline, not a jump past it.
+
+    Distribution of `|open_i - close_{i-1}| / close_{i-1}` (the overnight gap magnitude) over the
+    window: `median` / `p95` (linear-interpolation percentiles) / `worst` (the max), each expressed as
+    a PERCENT (directly comparable to ATR%/HV). Plus `overnight_variance_share`: the population
+    variance of the SIGNED overnight leg (`open_i/close_{i-1} - 1`) as a PERCENT of the population
+    variance of the SAME window's signed total daily return (`close_i/close_{i-1} - 1`) — how much of
+    the day's realized variance already happened before the open.
+
+    NA (`None`) if fewer than `window`+1 aligned open/close bars are available (insufficient history —
+    never a fabricated value). `overnight_variance_share` alone is NA when the window's total-return
+    variance is exactly zero (an undefined ratio — mirrors `vol_contraction`'s zero-denominator guard)
+    while `median`/`p95`/`worst` still report the real, independently-computable gap distribution."""
+    if window <= 0:
+        raise ValueError(f"overnight_gap_profile window must be positive, got {window}")
+    if len(opens) != len(closes):
+        raise ValueError("overnight_gap_profile requires opens/closes of equal length")
+    if len(closes) < window + 1:
+        return NA
+    o = opens[-(window + 1):]
+    c = closes[-(window + 1):]
+    gaps: list[float] = []
+    overnight_rets: list[float] = []
+    total_rets: list[float] = []
+    for i in range(1, len(c)):
+        prev_close = c[i - 1]
+        if prev_close == 0:
+            return NA
+        overnight_ret = (o[i] - prev_close) / prev_close
+        total_ret = (c[i] - prev_close) / prev_close
+        gaps.append(abs(overnight_ret))
+        overnight_rets.append(overnight_ret)
+        total_rets.append(total_ret)
+
+    sorted_gaps = sorted(gaps)
+    total_variance = _population_stdev(total_rets) ** 2
+    overnight_variance = _population_stdev(overnight_rets) ** 2
+    share = (overnight_variance / total_variance * 100) if total_variance != 0 else NA
+
+    return {
+        "median": _percentile(sorted_gaps, 0.5) * 100,
+        "p95": _percentile(sorted_gaps, 0.95) * 100,
+        "worst": sorted_gaps[-1] * 100,
+        "overnight_variance_share": share,
+    }
+
+
+def worst_20d_window(closes: Sequence[float], window: int) -> Optional[float]:
+    """The most negative trailing `window`-trading-day return ANYWHERE in the given (full as-of)
+    `closes` series — expressed as a PERCENT. Distinct from a forward max-drawdown figure (which
+    measures forward from one as-of date): this scans every trailing `window`-bar return the whole
+    series contains and keeps the worst (most negative) one — the deepest historical drawdown-window
+    depth. NA if fewer than `window`+1 closes (not even one trailing window computable) or a divisor
+    close is zero (an undefined return — never fabricated)."""
+    if window <= 0:
+        raise ValueError(f"worst_20d_window window must be positive, got {window}")
+    n = len(closes)
+    if n < window + 1:
+        return NA
+    worst: Optional[float] = None
+    for i in range(window, n):
+        base = closes[i - window]
+        if base == 0:
+            return NA
+        ret = closes[i] / base - 1
+        if worst is None or ret < worst:
+            worst = ret
+    return worst * 100
diff --git a/apps/backend/app/engine/prices.py b/apps/backend/app/engine/prices.py
index a95b15b..deb2079 100644
--- a/apps/backend/app/engine/prices.py
+++ b/apps/backend/app/engine/prices.py
@@ -529,6 +529,10 @@ def bars_through_latest(session: Session, symbol: str) -> list[DailyPrice]:
 # --- ascending-series extractors (the indicator functions take plain float lists) ----------
 # `bars` may be `DailyPrice` rows (the default, uncached path) or `Bar` records (iter-19: the cache
 # path) — both expose the same `.close/.high/.low/.volume` attributes, so these read structurally.
+def opens(bars: list[DailyPrice] | list[Bar]) -> list[float]:
+    return [b.open for b in bars]
+
+
 def closes(bars: list[DailyPrice] | list[Bar]) -> list[float]:
     return [b.close for b in bars]
 
diff --git a/apps/backend/app/engine/scoring.py b/apps/backend/app/engine/scoring.py
index d5e4e56..65b19e9 100644
--- a/apps/backend/app/engine/scoring.py
+++ b/apps/backend/app/engine/scoring.py
@@ -33,7 +33,7 @@ lookahead). Numeric literals are structural only (0/1/2/4/100); every period/wei
 from __future__ import annotations
 
 from datetime import date as date_cls
-from typing import Optional
+from typing import Callable, Optional
 
 from sqlmodel import Session, select
 
@@ -42,7 +42,7 @@ from app.engine import indicators as ind
 from app.engine.buckets import to_bucket
 from app.engine.normalize import cross_sectional_percentiles
 from app.engine.patterns import detect_flat_base_breakout, detect_pullback_to_rising_dma, detect_vcp
-from app.engine.prices import bars_asof, bars_asof_window, closes, highs, lows, volumes
+from app.engine.prices import bars_asof, bars_asof_window, closes, highs, lows, opens, volumes
 from app.engine.regime import score_regime
 from app.engine.sectors import score_sectors
 from app.engine.universe_resolver import resolve_members
@@ -90,6 +90,30 @@ def _avg_dollar_volume(series: list[float], vols: list[float], period: int) -> O
     return sum(close * volume for close, volume in recent) / period
 
 
+# --- iter-40 (J-24 / B-201) risk-budget card ------------------------------------------------
+# A per-stock "how much can this hurt" bundle, computed ONCE in pass-3 from the SAME as-of bars
+# already in hand (ATR% / downside-vol REUSE the existing pass-1/pass-3 values — no second
+# computation), stored ADDITIVELY on the row (enters NO weighted score — CONTRAST with the
+# `_build_score` components above). Each leaf is `{"value": <float|None>, "percentile": <float|None>}`
+# — `percentile` is filled in AFTER every row is assembled (see `_apply_risk_budget_percentile` below).
+
+def _risk_budget_leaf(value: Optional[float]) -> dict:
+    return {"value": value, "percentile": None}
+
+
+def _apply_risk_budget_percentile(rows: list[dict], leaf: Callable[[dict], dict], negate: bool = False) -> None:
+    """Attach a CROSS-SECTIONAL percentile (over the SAME as-of scan's resolved members — never across
+    time) to the risk-budget leaf `leaf(row)` on every row, mirroring pass-2's
+    `cross_sectional_percentiles` pattern. Oriented so a HIGHER percentile always means MORE risk (the
+    card's "pXX of universe" = riskier-than-XX% framing): `negate=True` for a component where a
+    SMALLER/more-negative raw value is MORE dangerous (`worst_20d_window`, `distance_to_invalidation_pct`)."""
+    orient = _neg if negate else (lambda v: v)
+    present = {row["ticker"]: orient(leaf(row)["value"]) for row in rows if leaf(row)["value"] is not None}
+    percentiles = cross_sectional_percentiles(present)
+    for row in rows:
+        leaf(row)["percentile"] = percentiles.get(row["ticker"])
+
+
 def _raw_components(
     session: Session,
     asof: date_cls,
@@ -385,6 +409,36 @@ def score_stocks(session: Session, asof: date_cls, config: Optional[Config] = No
         )
         downside_vol = ind.downside_vol(inv_closes, icfg.semivol_window)
 
+        # iter-40 (J-24 / B-201): the risk-budget bundle — a per-stock "how much can this hurt" set of
+        # DESCRIPTIVE components, computed ONCE here and stored ADDITIVELY (enters NO weighted score,
+        # like the iter-13 volatility family above). ATR% / downside-vol REUSE the values already
+        # computed above (raws["atr_pct"] from pass-1's `_raw_components`; the `downside_vol` local
+        # just computed) — never a second `ind.atr_pct`/`ind.downside_vol` call. The gap profile reads
+        # the SAME bounded `bars` slice already fetched for `inv_closes` above (no extra bar fetch).
+        gap_profile = ind.overnight_gap_profile(opens(bars), inv_closes, icfg.gap_window)
+        # The worst-20d window is read from the name's FULL as-of history (bars <= asof), NOT the
+        # max_lookback_bars-bounded slice above — a deliberate, logged interpretation (NOTES,
+        # assumptions.md iter-40). When a `bar_cache` context is active (bootstrap/backfill — the
+        # common heavy-traffic path), `bars_asof` slices the already-resident cached series (no new DB
+        # round trip); an uncached ad-hoc as-of date pays a one-time query per ticker, same as any other
+        # never-before-scanned date's first (and only, since runs are immutable) compute.
+        worst_20d = ind.worst_20d_window(closes(bars_asof(session, ticker, asof)), icfg.worst_window_days)
+        # Distance-to-invalidation %, REFRAMED (not recomputed) from the invalidation dict already built
+        # above — reuses the SAME `_pct_from_ma` helper `extension`/`support_nearby` already use, so the
+        # level itself is computed exactly once (by `_invalidation` above).
+        dist_to_invalidation_pct = _pct_from_ma(invalidation["price"], invalidation["level"])
+
+        risk_budget = {
+            "atr_pct": _risk_budget_leaf(raws["atr_pct"]),
+            "downside_vol": _risk_budget_leaf(downside_vol * 100 if downside_vol is not None else None),
+            "gap_profile": {
+                key: _risk_budget_leaf(gap_profile[key] if gap_profile else None)
+                for key in ("median", "p95", "worst", "overnight_variance_share")
+            },
+            "worst_20d_window": _risk_budget_leaf(worst_20d),
+            "distance_to_invalidation_pct": _risk_budget_leaf(dist_to_invalidation_pct),
+        }
+
         rows.append({
             "ticker": ticker,
             "name": ticker,
@@ -402,9 +456,27 @@ def score_stocks(session: Session, asof: date_cls, config: Optional[Config] = No
             "hv": hv,
             "vcp_contraction": vcp_contraction,
             "downside_vol": downside_vol,
+            # iter-40 (J-24 / B-201) — the risk-budget card/leaderboard-column bundle, never a score input.
+            "risk_budget": risk_budget,
             "rank": None,
         })
 
+    # iter-40 (J-24 / B-201) — cross-sectional percentiles for the risk-budget bundle. Unlike pass-2's
+    # component percentiles (computed BEFORE row assembly, since `_build_score` needs them), these are
+    # read from the just-built `rows` (see "Percentile pass" note): every ticker's raw risk-budget
+    # value must be known before any one ticker's peer-rank can be computed. Order-independent of the
+    # rank assignment below. `worst_20d_window` / `distance_to_invalidation_pct` are NEGATED before
+    # ranking (a smaller/more-negative raw value is MORE dangerous) so a HIGHER percentile always means
+    # MORE risk everywhere on the card (the "pXX of universe" framing) — see `_apply_risk_budget_percentile`.
+    _apply_risk_budget_percentile(rows, lambda r: r["risk_budget"]["atr_pct"])
+    _apply_risk_budget_percentile(rows, lambda r: r["risk_budget"]["downside_vol"])
+    _apply_risk_budget_percentile(rows, lambda r: r["risk_budget"]["gap_profile"]["median"])
+    _apply_risk_budget_percentile(rows, lambda r: r["risk_budget"]["gap_profile"]["p95"])
+    _apply_risk_budget_percentile(rows, lambda r: r["risk_budget"]["gap_profile"]["worst"])
+    _apply_risk_budget_percentile(rows, lambda r: r["risk_budget"]["gap_profile"]["overnight_variance_share"])
+    _apply_risk_budget_percentile(rows, lambda r: r["risk_budget"]["worst_20d_window"], negate=True)
+    _apply_risk_budget_percentile(rows, lambda r: r["risk_budget"]["distance_to_invalidation_pct"], negate=True)
+
     # ranked leaderboard: by Leadership descending (tie-break ticker for determinism)
     rows.sort(key=lambda row: (-row["leadership"]["score"], row["ticker"]))
     for index, row in enumerate(rows):
diff --git a/apps/backend/tests/test_api_methodology.py b/apps/backend/tests/test_api_methodology.py
index ba3dc60..d6b1449 100644
--- a/apps/backend/tests/test_api_methodology.py
+++ b/apps/backend/tests/test_api_methodology.py
@@ -56,6 +56,8 @@ GLOSSARY_SPOT_CHECK_TERMS = {
     "breadth > 50-DMA", "DMA", "rank-IC", "universe", "decile", "MAE", "MFE", "expectancy",
     "hit-rate", "dispersion", "walk-forward", "survivorship bias", "horizon", "excess return",
     "composite", "quantile", "ATR%", "pivot", "invalidation",
+    # iter-40 (J-24 / B-201 risk-budget card)
+    "overnight-gap profile", "worst 20-day window", "distance-to-invalidation %",
 }
 
 
diff --git a/apps/backend/tests/test_config.py b/apps/backend/tests/test_config.py
index 405889c..71e3526 100644
--- a/apps/backend/tests/test_config.py
+++ b/apps/backend/tests/test_config.py
@@ -76,6 +76,9 @@ MINIMAL_VALID = {
         # iter-26 (J-16 item F): required window; mirrors config.yaml's real value (>= high_window_52w
         # 252 + margin; >= the patterns block's largest min_history_bars, 90).
         "max_lookback_bars": 320,
+        # iter-40 (J-24 / B-201 risk-budget) required windows (required + validated positive).
+        "gap_window": 20,
+        "worst_window_days": 20,
     },
     "sectors": {
         "weights": {
diff --git a/apps/backend/tests/test_config_engine.py b/apps/backend/tests/test_config_engine.py
index b02abdf..10e1b10 100644
--- a/apps/backend/tests/test_config_engine.py
+++ b/apps/backend/tests/test_config_engine.py
@@ -72,6 +72,9 @@ VALID = {
         # iter-26 (J-16 item F): required window; mirrors config.yaml's real value (>= high_window_52w
         # 252 + margin; >= the patterns block's largest min_history_bars, 90).
         "max_lookback_bars": 320,
+        # iter-40 (J-24 / B-201 risk-budget) required windows (required + validated positive).
+        "gap_window": 20,
+        "worst_window_days": 20,
     },
     "sectors": {
         "weights": {
@@ -329,6 +332,40 @@ def test_indicators_nonpositive_volatility_window_raises(tmp_path):
         load_config(_write(tmp_path, data))
 
 
+# --- iter-40 (J-24 / B-201): risk-budget windows ---------------------------------------------
+def test_real_config_exposes_risk_budget_windows():
+    """The real config.yaml exposes the two typed risk-budget windows, both positive (anti-goal: No
+    magic numbers)."""
+    icfg = load_config().indicators
+    assert icfg.gap_window > 0 and icfg.worst_window_days > 0
+
+
+def test_indicators_nonpositive_gap_window_raises(tmp_path):
+    """A non-positive gap_window fails the boot loudly — never a silent default."""
+    data = copy.deepcopy(VALID)
+    data["indicators"]["gap_window"] = 0
+    with pytest.raises(ConfigError):
+        load_config(_write(tmp_path, data))
+
+
+def test_indicators_nonpositive_worst_window_days_raises(tmp_path):
+    """A non-positive worst_window_days fails the boot loudly — never a silent default."""
+    data = copy.deepcopy(VALID)
+    data["indicators"]["worst_window_days"] = 0
+    with pytest.raises(ConfigError):
+        load_config(_write(tmp_path, data))
+
+
+def test_indicators_max_lookback_bars_must_cover_gap_window(tmp_path):
+    """max_lookback_bars must be >= gap_window + 1 (the byte-identity-window guard, mirroring the
+    hv_window/semivol_window treatment)."""
+    data = copy.deepcopy(VALID)
+    data["indicators"]["max_lookback_bars"] = 5
+    data["indicators"]["gap_window"] = 400  # exceeds the shrunk max_lookback_bars
+    with pytest.raises(ConfigError):
+        load_config(_write(tmp_path, data))
+
+
 def test_real_config_resolves_volatility_factor_sources():
     """The three new volatility factors are catalogued with family `volatility`, `lower_better`, and a
     typed-column source that RESOLVES at boot (load_config would raise ConfigError otherwise). This is
diff --git a/apps/backend/tests/test_indexes.py b/apps/backend/tests/test_indexes.py
index eddfc84..140d8b6 100644
--- a/apps/backend/tests/test_indexes.py
+++ b/apps/backend/tests/test_indexes.py
@@ -69,6 +69,8 @@ _CFG = {
         # iter-26 (J-16 item F): required window; >= this fixture's own max (high_window_52w=20) and
         # >= the patterns block's min_history_bars below (20).
         "max_lookback_bars": 20,
+        # iter-40 (J-24 / B-201 risk-budget) required windows — synthetic small scale.
+        "gap_window": 5, "worst_window_days": 5,
     },
     "sectors": {
         "weights": {"rs_spy_1m": 0.20, "rs_spy_3m": 0.25, "rs_spy_6m": 0.20, "ma_stack": 0.15, "dist_from_high": 0.10, "vol_trend": 0.10},
diff --git a/apps/backend/tests/test_indicators.py b/apps/backend/tests/test_indicators.py
index 4769aa9..5f8de0f 100644
--- a/apps/backend/tests/test_indicators.py
+++ b/apps/backend/tests/test_indicators.py
@@ -186,3 +186,75 @@ def test_downside_vol_na_when_too_short():
 def test_downside_vol_rejects_nonpositive_window():
     with pytest.raises(ValueError):
         ind.downside_vol([100, 90, 81], 0)
+
+
+# --- overnight_gap_profile (J-24 / B-201 risk-budget) ---------------------------------------
+# Fixture derivation (window=4, 5 bars): overnight_ret_i is set to EXACTLY 0.5 * total_ret_i at every
+# step, so Var(overnight) = 0.5^2 * Var(total) exactly regardless of Var(total)'s actual value, making
+# overnight_variance_share = 0.25 (25.0%) an EXACT expected value, not an approximation of an
+# approximation.
+#   day1: total +10.0% (close 100->110),   overnight +5.0% (open 105 from prior close 100)
+#   day2: total  -6.0% (close 110->103.4), overnight -3.0% (open 106.7 from prior close 110)
+#   day3: total  +4.0% (close 103.4->107.536), overnight +2.0% (open 105.468 from prior close 103.4)
+#   day4: total  -8.0% (close 107.536->98.93312), overnight -4.0% (open 103.23456 from prior close 107.536)
+# abs gaps = [5.0, 3.0, 2.0, 4.0] -> sorted [2.0, 3.0, 4.0, 5.0] (percent)
+#   median (linear-interp rank=1.5): 3.0 + (4.0-3.0)*0.5 = 3.5
+#   p95    (linear-interp rank=2.85): 4.0 + (5.0-4.0)*0.85 = 4.85
+#   worst = max = 5.0
+_GAP_CLOSES = [100, 110, 103.4, 107.536, 98.93312]
+_GAP_OPENS = [100, 105, 106.7, 105.468, 103.23456]
+
+
+def test_overnight_gap_profile_exact():
+    profile = ind.overnight_gap_profile(_GAP_OPENS, _GAP_CLOSES, 4)
+    assert profile["median"] == pytest.approx(3.5)
+    assert profile["p95"] == pytest.approx(4.85)
+    assert profile["worst"] == pytest.approx(5.0)
+    assert profile["overnight_variance_share"] == pytest.approx(25.0)
+
+
+def test_overnight_gap_profile_na_when_too_short():
+    # needs window+1 = 5 aligned bars; only 3 given
+    assert ind.overnight_gap_profile([100, 101, 102], [100, 101, 102], 4) is None
+
+
+def test_overnight_gap_profile_rejects_nonpositive_window():
+    with pytest.raises(ValueError):
+        ind.overnight_gap_profile(_GAP_OPENS, _GAP_CLOSES, 0)
+
+
+def test_overnight_gap_profile_rejects_mismatched_lengths():
+    with pytest.raises(ValueError):
+        ind.overnight_gap_profile([100, 101], [100, 101, 102], 1)
+
+
+def test_overnight_gap_profile_share_na_on_zero_total_variance():
+    # closes flat at 100 (every total return is exactly 0 -> undefined variance ratio -> NA), but
+    # opens still vary, so the gap distribution itself stays a real, non-fabricated number.
+    closes = [100, 100, 100, 100, 100]
+    opens = [100, 105, 95, 102, 98]
+    profile = ind.overnight_gap_profile(opens, closes, 4)
+    # abs gaps = [5, 5, 2, 2] -> sorted [2, 2, 5, 5]
+    assert profile["median"] == pytest.approx(3.5)   # 2 + (5-2)*0.5
+    assert profile["p95"] == pytest.approx(5.0)       # 5 + (5-5)*0.85
+    assert profile["worst"] == pytest.approx(5.0)
+    assert profile["overnight_variance_share"] is None
+
+
+# --- worst_20d_window (J-24 / B-201 risk-budget) ---------------------------------------------
+def test_worst_20d_window_exact():
+    # window=3; trailing 3-day returns ending at each valid index:
+    #   idx3: 80/100 - 1  = -20.0%
+    #   idx4: 105/90 - 1  = +16.666...%
+    #   idx5: 70/95  - 1  = -26.315...%   <- most negative (worst)
+    closes = [100, 90, 95, 80, 105, 70]
+    assert ind.worst_20d_window(closes, 3) == pytest.approx((70 / 95 - 1) * 100)
+
+
+def test_worst_20d_window_na_when_too_short():
+    assert ind.worst_20d_window([100, 90, 95], 3) is None  # needs window+1 = 4 closes
+
+
+def test_worst_20d_window_rejects_nonpositive_window():
+    with pytest.raises(ValueError):
+        ind.worst_20d_window([100, 90, 95, 80], 0)
diff --git a/apps/backend/tests/test_scoring.py b/apps/backend/tests/test_scoring.py
index bf4d06f..39a2d53 100644
--- a/apps/backend/tests/test_scoring.py
+++ b/apps/backend/tests/test_scoring.py
@@ -9,12 +9,14 @@ deterministic; and the as-of date bounds the computation (no lookahead).
 """
 from __future__ import annotations
 
+import pytest
 from sqlmodel import Session, select
 
 from app.config import load_config
+from app.engine import indicators as ind
 from app.engine.buckets import to_bucket
 from app.engine.indicators import sma
-from app.engine.prices import bars_asof, closes, latest_data_date
+from app.engine.prices import bars_asof, bars_asof_window, closes, latest_data_date, opens
 from app.engine.scoring import score_stocks
 from app.engine.setups import ALL_STATUSES
 from app.engine.universe_screen import read_pool
@@ -330,6 +332,154 @@ def test_volatility_values_ride_the_row_but_enter_no_score(loaded_engine, monkey
     assert isinstance(nvda["vcp_contraction"], float) and isinstance(nvda["downside_vol"], float)
 
 
+RISK_BUDGET_SCALAR_KEYS = ("atr_pct", "downside_vol", "worst_20d_window", "distance_to_invalidation_pct")
+RISK_BUDGET_GAP_KEYS = ("median", "p95", "worst", "overnight_variance_share")
+
+
+def test_risk_budget_fields_present_with_cross_sectional_percentiles(loaded_engine):
+    """iter-40 (J-24 / B-201): every row carries an additive `risk_budget` block — ATR% / downside vol /
+    the overnight-gap profile (median/p95/worst/overnight-variance-share) / worst-20d window /
+    distance-to-invalidation %, each `{value, percentile}` — computed for a real, ample-history name
+    (NVDA), with percentiles that are genuinely CROSS-SECTIONAL (not a fabricated constant)."""
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        asof = latest_data_date(session)
+        result = score_stocks(session, asof, cfg)
+    rows = result["rows"]
+    nvda = _row(rows, "NVDA")
+    rb = nvda["risk_budget"]
+
+    for key in RISK_BUDGET_SCALAR_KEYS:
+        leaf = rb[key]
+        assert set(leaf) == {"value", "percentile"}
+        assert isinstance(leaf["value"], float)
+        assert leaf["percentile"] is not None and 0 <= leaf["percentile"] <= 1
+
+    assert set(rb["gap_profile"]) == set(RISK_BUDGET_GAP_KEYS)
+    for key in RISK_BUDGET_GAP_KEYS:
+        leaf = rb["gap_profile"][key]
+        assert set(leaf) == {"value", "percentile"}
+        assert isinstance(leaf["value"], float)
+        assert leaf["percentile"] is not None and 0 <= leaf["percentile"] <= 1
+
+    # genuinely cross-sectional: not every peer shares NVDA's percentile (never a fabricated constant).
+    atr_percentiles = {r["ticker"]: r["risk_budget"]["atr_pct"]["percentile"] for r in rows}
+    assert len(set(atr_percentiles.values())) > 1
+
+
+def test_risk_budget_gap_p95_byte_matches_offline_recomputation(loaded_engine):
+    """Correctness (DoD): a spot-checked overnight-gap p95 value byte-matches an INDEPENDENT offline
+    recomputation from the same as-of bars — the served number is never a UI/second-path recompute."""
+    cfg = load_config()
+    icfg = cfg.indicators
+    with Session(loaded_engine) as session:
+        asof = latest_data_date(session)
+        result = score_stocks(session, asof, cfg)
+        nvda_bars = bars_asof_window(session, "NVDA", asof, icfg.max_lookback_bars)
+    expected = ind.overnight_gap_profile(opens(nvda_bars), closes(nvda_bars), icfg.gap_window)
+    assert expected is not None  # NVDA has ample history
+
+    nvda = _row(result["rows"], "NVDA")
+    assert nvda["risk_budget"]["gap_profile"]["p95"]["value"] == pytest.approx(expected["p95"])
+    assert nvda["risk_budget"]["gap_profile"]["median"]["value"] == pytest.approx(expected["median"])
+
+
+def test_risk_budget_worst_20d_byte_matches_offline_recomputation(loaded_engine):
+    """The worst-20d window reads the name's FULL as-of history (not the max_lookback_bars-bounded
+    slice — logged interpretation, assumptions.md iter-40); spot-check against an independent
+    recomputation over the SAME full series."""
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        asof = latest_data_date(session)
+        result = score_stocks(session, asof, cfg)
+        nvda_full_closes = closes(bars_asof(session, "NVDA", asof))
+    expected = ind.worst_20d_window(nvda_full_closes, cfg.indicators.worst_window_days)
+    assert expected is not None
+
+    nvda = _row(result["rows"], "NVDA")
+    assert nvda["risk_budget"]["worst_20d_window"]["value"] == pytest.approx(expected)
+
+
+def test_risk_budget_atr_and_downside_vol_are_reused_not_recomputed(loaded_engine, monkeypatch):
+    """B-201 ★ Do NOT touch / trap guard: ATR% and downside-vol MUST be REUSED from pass-1/pass-3's
+    existing computation for the risk-budget card, never called a second time. Wrap both indicator
+    functions with a call counter and assert each fires exactly once per resolved member."""
+    cfg = load_config()
+    calls = {"atr_pct": 0, "downside_vol": 0}
+    real_atr_pct, real_downside_vol = ind.atr_pct, ind.downside_vol
+
+    def _counting_atr_pct(*a, **k):
+        calls["atr_pct"] += 1
+        return real_atr_pct(*a, **k)
+
+    def _counting_downside_vol(*a, **k):
+        calls["downside_vol"] += 1
+        return real_downside_vol(*a, **k)
+
+    monkeypatch.setattr("app.engine.indicators.atr_pct", _counting_atr_pct)
+    monkeypatch.setattr("app.engine.indicators.downside_vol", _counting_downside_vol)
+    with Session(loaded_engine) as session:
+        asof = latest_data_date(session)
+        result = score_stocks(session, asof, cfg)
+
+    n_members = len(result["members"])
+    assert calls["atr_pct"] == n_members       # once per ticker (pass-1 only) — never a second call
+    assert calls["downside_vol"] == n_members  # once per ticker (pass-3 only) — never a second call
+
+    nvda = _row(result["rows"], "NVDA")
+    risk_atr = next(c for c in nvda["risk"]["components"] if c["name"] == "atr_pct")
+    # the SAME reused raw value — `risk.components[].raw` is rounded to 4dp for the score-breakdown
+    # display (`_build_score`'s `round(raw, 4)`); `risk_budget.atr_pct.value` stores the SAME
+    # unrounded `raws["atr_pct"]` (matching the unrounded convention the iter-13 `downside_vol`/`hv`/
+    # `vcp_contraction` top-level fields already use) — round for an exact, not merely approximate, check.
+    assert round(nvda["risk_budget"]["atr_pct"]["value"], 4) == risk_atr["raw"]
+
+
+def test_risk_budget_values_ride_the_row_but_enter_no_score(loaded_engine, monkeypatch):
+    """CRITICAL keystone (iter-40 / J-24 / B-201 ★ Do NOT touch score weights): the risk-budget
+    components ride on every canonical row for the stock-detail card + leaderboard columns, but enter
+    NO weighted score. Force the two new indicator functions to an absurd constant and assert every
+    row's three scores + A-E buckets + setup status + rank are BYTE-IDENTICAL to baseline — proving the
+    values never feed `_build_score`. Mirrors `test_volatility_values_ride_the_row_but_enter_no_score`."""
+    cfg = load_config()
+    risk_budget_keys = {
+        "atr_pct", "downside_vol", "gap_profile", "worst_20d_window", "distance_to_invalidation_pct",
+    }
+    for weights in (cfg.scores.leadership.weights, cfg.scores.entry_quality.weights, cfg.scores.risk.weights):
+        assert not (risk_budget_keys & set(weights))
+
+    def _snapshot(rows):
+        return {
+            r["ticker"]: (
+                r["leadership"]["score"], r["leadership"]["bucket"],
+                r["entry_quality"]["score"], r["entry_quality"]["bucket"],
+                r["risk"]["score"], r["risk"]["bucket"],
+                r["setup"]["status"], r["rank"],
+            )
+            for r in rows
+        }
+
+    with Session(loaded_engine) as session:
+        asof = latest_data_date(session)
+        baseline_rows = score_stocks(session, asof, cfg)["rows"]
+        baseline = _snapshot(baseline_rows)
+        for r in baseline_rows:
+            assert "risk_budget" in r
+
+        # force the two NEW indicator functions to an absurd constant — must perturb NO score/bucket/setup
+        monkeypatch.setattr(
+            "app.engine.indicators.overnight_gap_profile",
+            lambda *a, **k: {"median": 999.0, "p95": 999.0, "worst": 999.0, "overnight_variance_share": 999.0},
+        )
+        monkeypatch.setattr("app.engine.indicators.worst_20d_window", lambda *a, **k: 999.0)
+        forced_rows = score_stocks(session, asof, cfg)["rows"]
+
+    assert _snapshot(forced_rows) == baseline  # risk-budget additions changed nothing in any score path
+    nvda = _row(forced_rows, "NVDA")
+    assert nvda["risk_budget"]["gap_profile"]["p95"]["value"] == 999.0        # the monkeypatch took effect
+    assert nvda["risk_budget"]["worst_20d_window"]["value"] == 999.0
+
+
 def test_asof_bounds_the_computation_no_lookahead(loaded_engine):
     """The as-of date bounds the data window: scoring at an earlier date echoes that date and
     produces a different ranking than the latest date (it cannot see later bars)."""
diff --git a/apps/backend/tests/test_sectors.py b/apps/backend/tests/test_sectors.py
index 4457836..040d918 100644
--- a/apps/backend/tests/test_sectors.py
+++ b/apps/backend/tests/test_sectors.py
@@ -100,6 +100,8 @@ _SYNTH_CFG = {
         # iter-26 (J-16 item F): required window; >= this fixture's own max (high_window_52w=20) and
         # >= the patterns block's min_history_bars below (20).
         "max_lookback_bars": 20,
+        # iter-40 (J-24 / B-201 risk-budget) required windows — synthetic small scale.
+        "gap_window": 5, "worst_window_days": 5,
     },
     "sectors": {
         "weights": {"rs_spy_1m": 0.20, "rs_spy_3m": 0.25, "rs_spy_6m": 0.20, "ma_stack": 0.15, "dist_from_high": 0.10, "vol_trend": 0.10},
diff --git a/apps/backend/tests/test_themes.py b/apps/backend/tests/test_themes.py
index 664c9f2..9a763e0 100644
--- a/apps/backend/tests/test_themes.py
+++ b/apps/backend/tests/test_themes.py
@@ -106,6 +106,8 @@ _SYNTH_CFG = {
         # iter-26 (J-16 item F): required window; >= this fixture's own max (high_window_52w=20) and
         # >= the patterns block's min_history_bars below (20).
         "max_lookback_bars": 20,
+        # iter-40 (J-24 / B-201 risk-budget) required windows — synthetic small scale.
+        "gap_window": 5, "worst_window_days": 5,
     },
     "sectors": {
         "weights": {"rs_spy_1m": 0.20, "rs_spy_3m": 0.25, "rs_spy_6m": 0.20, "ma_stack": 0.15, "dist_from_high": 0.10, "vol_trend": 0.10},
diff --git a/apps/frontend/app/stocks/[ticker]/page.tsx b/apps/frontend/app/stocks/[ticker]/page.tsx
index 2a9478e..5f6d94b 100644
--- a/apps/frontend/app/stocks/[ticker]/page.tsx
+++ b/apps/frontend/app/stocks/[ticker]/page.tsx
@@ -1,6 +1,6 @@
 "use client";
 
-import { useEffect, useState } from "react";
+import { useEffect, useState, type ReactNode } from "react";
 import Link from "next/link";
 import { useParams } from "next/navigation";
 import { AlertTriangle, ArrowLeft, SearchX } from "lucide-react";
@@ -17,6 +17,7 @@ import { Badge } from "@/components/ui/badge";
 import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
 import { formatIsoDate } from "@/lib/dates";
 import { SCORE_SIGNALS } from "@/lib/evidence";
+import { fmtRiskPercentile, fmtRiskValue, isRiskBudgetNa } from "@/lib/risk-budget";
 import { sectorLabel } from "@/lib/sector-label";
 import { cn } from "@/lib/utils";
 import {
@@ -27,6 +28,7 @@ import {
   type BarsResponse,
   type ProvenSignal,
   type RegimePoint,
+  type RiskBudgetComponent,
   type ScoreBlock,
   type StockDetailResponse,
   type StockRow,
@@ -190,6 +192,11 @@ function StockDetailBody({ data }: { data: StockDetailResponse }) {
       {/* theme membership + concrete invalidation level (server-computed, rendered verbatim) */}
       <ThemeAndInvalidationCard row={row} />
 
+      {/* iter-40 (J-24 / B-201) — the "how much can this hurt" risk-budget card: ATR% / downside vol /
+          overnight-gap profile / worst-20d window / distance-to-invalidation, each re-read verbatim from
+          the served row with its universe-percentile context (never recomputed client-side). */}
+      <RiskBudgetCard row={row} />
+
       {/* detected patterns — each a separate pattern with its own pivot + invalidation level. VCP always
           shows (incl. a not-detected state); the iter-9 patterns show a card only when flagged. */}
       <VcpCard vcp={row.vcp} />
@@ -272,6 +279,89 @@ function ThemeAndInvalidationCard({ row }: { row: StockRow }) {
   );
 }
 
+/** One risk-budget metric tile: a label, the server value(s) (re-displayed verbatim), and — when
+ *  present — the "pXX of universe" percentile chip. NA (no value) renders the warn-coloured "NA" text,
+ *  mirroring `ThemeAndInvalidationCard`'s `naInvalidation` short-history treatment above — never a
+ *  fabricated 0. Purely descriptive: no badge, no proven-language, no position advice (anti-goals #1/#2). */
+function RiskMetricTile({
+  label,
+  component,
+  children,
+}: {
+  label: string;
+  /** The metric that drives the tile's NA state + (when present) its percentile chip. For the
+   *  multi-line gap-profile tile this is the p95 sub-component (the "near-worst case" headline the
+   *  card's percentile chip speaks to — median/worst render as plain supporting lines via `children`). */
+  component: RiskBudgetComponent | null | undefined;
+  /** Custom value content; defaults to `fmtRiskValue(component.value)` when omitted. */
+  children?: ReactNode;
+}) {
+  const na = isRiskBudgetNa(component);
+  const pctLabel = fmtRiskPercentile(component?.percentile);
+  return (
+    <div className="space-y-1 rounded-md border border-border bg-surface-2 p-3">
+      <p className="text-xs uppercase tracking-wide text-text-faint">{label}</p>
+      {na ? (
+        <p className="num text-sm text-warn" title="Insufficient history for this component (NA)">
+          NA — insufficient history
+        </p>
+      ) : (
+        <>
+          <div className="num text-sm text-text">{children ?? fmtRiskValue(component?.value)}</div>
+          {pctLabel ? <p className="text-[11px] text-text-faint">{pctLabel}</p> : null}
+        </>
+      )}
+    </div>
+  );
+}
+
+/** The J-24 / B-201 "how much can this hurt" risk-budget card: ATR% (reused from the Risk score),
+ *  downside volatility (reused), the overnight-gap profile (median/p95/worst + overnight share of
+ *  20-day return variance), the worst historical 20-day window, and distance-to-invalidation % — every
+ *  value + its universe-percentile label read VERBATIM from the served row (single source; the card
+ *  never recomputes a risk-budget number). Absent entirely for a row served before iter-40 (an honest
+ *  omission, not an error — see `StockRow.risk_budget`'s optionality). */
+function RiskBudgetCard({ row }: { row: StockRow }) {
+  const rb = row.risk_budget;
+  if (!rb) return null;
+  return (
+    <Card data-testid="risk-budget-card">
+      <CardHeader>
+        <CardTitle>Risk budget</CardTitle>
+      </CardHeader>
+      <CardContent className="space-y-3">
+        <p className="text-xs text-text-faint">
+          How much plausible damage this name carries — volatility, overnight-gap exposure the
+          invalidation level cannot protect against, the worst historical 20-day window, and distance
+          from where the thesis is wrong. Descriptive only; not a recommendation.
+        </p>
+        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
+          <RiskMetricTile label="ATR %" component={rb.atr_pct} />
+          <RiskMetricTile label="Downside volatility" component={rb.downside_vol} />
+          <RiskMetricTile label="Worst 20-day window" component={rb.worst_20d_window} />
+          <RiskMetricTile label="Distance to invalidation" component={rb.distance_to_invalidation_pct} />
+          {/* Median/worst are ATOMIC with p95 (overnight_gap_profile returns the whole distribution or
+              NA together — only overnight_variance_share can independently drop out), so gating on the
+              p95 component's own NA state (RiskMetricTile's default behavior) safely covers all three. */}
+          <RiskMetricTile label="Overnight gap · p95" component={rb.gap_profile.p95}>
+            <div className="space-y-0.5">
+              <p>p95 {fmtRiskValue(rb.gap_profile.p95.value)}</p>
+              <p className="text-xs text-text-faint">
+                median {fmtRiskValue(rb.gap_profile.median.value)} · worst{" "}
+                {fmtRiskValue(rb.gap_profile.worst.value)}
+              </p>
+            </div>
+          </RiskMetricTile>
+          <RiskMetricTile
+            label="Overnight share of 20d variance"
+            component={rb.gap_profile.overnight_variance_share}
+          />
+        </div>
+      </CardContent>
+    </Card>
+  );
+}
+
 /** The VCP badge that rides ALONGSIDE the setup status (teal accent). Its tooltip carries the
  *  server-built reason + pivot + invalidation note (rendered verbatim — never assembled here). */
 function VcpBadge({ vcp }: { vcp: Vcp }) {
diff --git a/apps/frontend/app/stocks/page.tsx b/apps/frontend/app/stocks/page.tsx
index 5cf0d67..ce29fc2 100644
--- a/apps/frontend/app/stocks/page.tsx
+++ b/apps/frontend/app/stocks/page.tsx
@@ -19,6 +19,7 @@ import { TermInfo } from "@/components/ui/term-info";
 import { formatIsoDate } from "@/lib/dates";
 import { fmtHighProximity, highProximityValue } from "@/lib/high-proximity";
 import { regimeVariant } from "@/lib/regime-variant";
+import { fmtRiskValue } from "@/lib/risk-budget";
 import { SCORE_SIGNALS } from "@/lib/evidence";
 import { compareSectors, sectorLabel } from "@/lib/sector-label";
 import { cn } from "@/lib/utils";
@@ -31,6 +32,7 @@ import {
   type DashboardResponse,
   type MethodologyCatalog,
   type ProvenSignal,
+  type RiskBudgetComponent,
   type StockRow,
   type StocksResponse,
   type ThemeRow,
@@ -70,9 +72,34 @@ const PATTERNS: { key: string; label: string; badge: string; get: (row: StockRow
 /** A base sortable column, plus the dynamic forward-return columns `fwd_<horizon>` (J-75) and the paired
  *  max-drawdown columns `mdd_<horizon>` (J-86). */
 type BaseSortKey = "rank" | "ticker" | "sector" | "leadership" | "entry_quality" | "risk" | "setup";
+/** iter-40 (J-24 / B-201) — the five risk-budget leaderboard columns, config-driven like `PATTERNS`
+ *  above (adding a column is ONE entry here — the header, cell, and comparator all read this list). Each
+ *  `get` re-reads the SAME served `risk_budget` field the Stock Detail risk-budget card shows (never
+ *  recomputed client-side) — `?.` degrades an absent (pre-iter-40) `risk_budget` to the honest NA cell. */
+type RiskBudgetColumnKey = "rb_atr_pct" | "rb_downside_vol" | "rb_gap_p95" | "rb_worst_20d" | "rb_dist_invalidation";
+const RISK_BUDGET_COLUMNS: {
+  key: RiskBudgetColumnKey;
+  label: string;
+  term: string;
+  get: (row: StockRow) => RiskBudgetComponent | null | undefined;
+}[] = [
+  { key: "rb_atr_pct", label: "ATR%", term: "ATR%", get: (r) => r.risk_budget?.atr_pct },
+  {
+    key: "rb_downside_vol", label: "Downside vol", term: "downside volatility (semivol)",
+    get: (r) => r.risk_budget?.downside_vol,
+  },
+  { key: "rb_gap_p95", label: "Gap p95", term: "overnight-gap profile", get: (r) => r.risk_budget?.gap_profile.p95 },
+  { key: "rb_worst_20d", label: "Worst 20d", term: "worst 20-day window", get: (r) => r.risk_budget?.worst_20d_window },
+  {
+    key: "rb_dist_invalidation", label: "Dist. to invalidation", term: "distance-to-invalidation %",
+    get: (r) => r.risk_budget?.distance_to_invalidation_pct,
+  },
+];
+
 // J-106 adds the `high_proximity` column key (handled by an explicit NA-last branch in comparatorFor,
-// NOT routed through SORT_COMPARATORS — that base map has no null handling).
-type SortKey = BaseSortKey | "high_proximity" | `fwd_${number}` | `mdd_${number}`;
+// NOT routed through SORT_COMPARATORS — that base map has no null handling). iter-40 adds the five
+// risk-budget columns the SAME way.
+type SortKey = BaseSortKey | "high_proximity" | RiskBudgetColumnKey | `fwd_${number}` | `mdd_${number}`;
 type SortDir = "asc" | "desc";
 
 /** J-75 — a stock's realized forward return at `horizon` from the served `forward_returns` (NA → null).
@@ -132,6 +159,21 @@ function comparatorFor(key: SortKey, dir: SortDir): (a: StockRow, b: StockRow) =
       return (av - bv) * sign;
     };
   }
+  // iter-40 (J-24 / B-201) — the five risk-budget columns, read verbatim from the SAME served
+  // `risk_budget` field the detail card shows (never recomputed). NA (short history, or a row served
+  // before iter-40) always sorts LAST regardless of direction, exactly like `high_proximity` above.
+  const riskBudgetColumn = RISK_BUDGET_COLUMNS.find((c) => c.key === key);
+  if (riskBudgetColumn) {
+    const sign = dir === "asc" ? 1 : -1;
+    return (a, b) => {
+      const av = riskBudgetColumn.get(a)?.value ?? null;
+      const bv = riskBudgetColumn.get(b)?.value ?? null;
+      if (av === null && bv === null) return 0;
+      if (av === null) return 1;
+      if (bv === null) return -1;
+      return (av - bv) * sign;
+    };
+  }
   const cmp = SORT_COMPARATORS[key as BaseSortKey];
   const sign = dir === "asc" ? 1 : -1;
   return (a, b) => cmp(a, b) * sign;
@@ -661,6 +703,20 @@ function StocksInner() {
                   dir={sortDir}
                   onSort={onSort}
                 />
+                {/* iter-40 (J-24 / B-201) — the five risk-budget columns, re-reading the SAME served
+                    `risk_budget` field the Stock Detail risk-budget card shows (never recomputed),
+                    each client-side sortable (view transform, NA-last). */}
+                {RISK_BUDGET_COLUMNS.map((col) => (
+                  <SortHeader
+                    key={col.key}
+                    col={col.key}
+                    label={col.label}
+                    term={col.term}
+                    activeKey={sortKey}
+                    dir={sortDir}
+                    onSort={onSort}
+                  />
+                ))}
                 <SortHeader
                   col="setup"
                   label="Setup"
@@ -831,6 +887,21 @@ function HighProximityCell({ value }: { value: number | null }) {
   return <span className="num text-text">{fmtHighProximity(value)}</span>;
 }
 
+/** iter-40 (J-24 / B-201) — one risk-budget leaderboard cell: the served value (already a percent
+ *  number — `fmtRiskValue` only appends "%", it never multiplies by 100), read VERBATIM — the SAME
+ *  value the Stock Detail risk-budget card shows (single source; never recomputed). NA (short history,
+ *  or a row served before iter-40) renders a muted "NA" that always sorts last. */
+function RiskBudgetCell({ value }: { value: number | null | undefined }) {
+  if (value === null || value === undefined) {
+    return (
+      <span className="num text-text-muted" title="Insufficient history for this component (NA)">
+        NA
+      </span>
+    );
+  }
+  return <span className="num text-text">{fmtRiskValue(value)}</span>;
+}
+
 /** J-86 — one colour-graded max-drawdown cell: the served realized drawdown (<= 0; NA → "NA" muted), read
  *  verbatim. A real (negative) drawdown reads red via the shared `mddClass` helper. */
 function MaxDrawdownCell({ value }: { value: number | null }) {
@@ -910,6 +981,14 @@ function StockTableRow({
       <td className="px-3 py-2 text-right" data-testid="high-proximity">
         <HighProximityCell value={highProximityValue(row.leadership.components)} />
       </td>
+      {/* iter-40 (J-24 / B-201) — five risk-budget cells, re-reading the SAME served `risk_budget`
+          field the Stock Detail risk-budget card shows (never recomputed); NA-honest (muted "NA") on
+          short history or a row served before iter-40. */}
+      {RISK_BUDGET_COLUMNS.map((col) => (
+        <td key={col.key} className="px-3 py-2 text-right" data-testid={col.key}>
+          <RiskBudgetCell value={col.get(row)?.value} />
+        </td>
+      ))}
       <td className="px-3 py-2">
         <div className="flex flex-wrap items-center gap-1.5">
           <Badge variant={setupVariant(row.setup.status)}>{row.setup.status}</Badge>
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index be50c49..129e326 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -319,6 +319,38 @@ export interface FlatBaseBreakout {
   detail?: Record<string, number | null>; // base_depth_pct, dist_below_pivot_pct, volume_ratio
 }
 
+/** One risk-budget component (iter-40, J-24 / B-201): a stored value + its CROSS-SECTIONAL universe
+ *  percentile in [0,1] (higher percentile = MORE risk by this measure — the card's "pXX of universe"
+ *  framing), both read verbatim from the server — never recomputed client-side. `value`/`percentile`
+ *  null together = NA (insufficient history); `percentile` is never present without `value`. */
+export interface RiskBudgetComponent {
+  value: number | null;
+  percentile: number | null;
+}
+
+/** The overnight-gap risk profile (iter-40, J-24 / B-201): the distribution of overnight moves over the
+ *  gap window (median / p95 / worst), plus the overnight share of the same window's return variance —
+ *  the risk an invalidation level cannot protect against (a gap jumps past it, it does not breach it). */
+export interface GapProfile {
+  median: RiskBudgetComponent;
+  p95: RiskBudgetComponent;
+  worst: RiskBudgetComponent;
+  overnight_variance_share: RiskBudgetComponent;
+}
+
+/** The per-stock "how much can this hurt" risk-budget bundle (iter-40, J-24 / B-201) — computed ONCE by
+ *  `scoring:score_stocks` and served verbatim on the SAME two stock endpoints the rest of `StockRow`
+ *  comes from (no new endpoint, no UI recompute). Descriptive statistics only — no proven-language, no
+ *  position advice (anti-goals #1/#2). Historical scanner rows predating iter-40 carry no `risk_budget`
+ *  key at all (honest absence, never a fabricated NA) — optional on `StockRow` for that reason. */
+export interface RiskBudget {
+  atr_pct: RiskBudgetComponent;
+  downside_vol: RiskBudgetComponent;
+  gap_profile: GapProfile;
+  worst_20d_window: RiskBudgetComponent;
+  distance_to_invalidation_pct: RiskBudgetComponent;
+}
+
 export interface StockRow {
   ticker: string;
   name: string;
@@ -343,6 +375,10 @@ export interface StockRow {
   // Backtest reads (never recomputed). `return` is null (NA) where no stored row exists for that horizon
   // (so at/near the latest date all five are NA — never fabricated). Order maps to config horizons.
   forward_returns: StockForwardReturn[];
+  // iter-40 (J-24 / B-201): the risk-budget card/leaderboard-column bundle. Optional — a scanner row
+  // persisted before iter-40 carries no `risk_budget` key at all (honest absence; only the served
+  // bootstrap + latest snapshots regenerate with it, historical runs stay as they were).
+  risk_budget?: RiskBudget;
 }
 
 /** One forward-return entry: the realized return at `horizon` trading days, or null (NA) when no stored
diff --git a/config.yaml b/config.yaml
index f36d61f..18bd75c 100644
--- a/config.yaml
+++ b/config.yaml
@@ -658,6 +658,14 @@ indicators:
   # 252 + a ~68-bar safety margin. The byte-identity harness (test_scoring_window.py), not this
   # value, is the authority: it must show 0 diffs windowed vs. unwindowed; widen this if it ever doesn't.
   max_lookback_bars: 320
+  # iter-40 (J-24, B-201 risk-budget card): the overnight-gap-profile window (median/p95/worst gap +
+  # overnight share of same-window return variance) -- 20 trading days (~1 trading month), read from
+  # the SAME max_lookback_bars-bounded trailing slice, so "20-day return variance" in the served copy
+  # matches this value exactly (no separate literal).
+  gap_window: 20
+  # The worst-trailing-N-day-return window scanned over each name's FULL as-of history (not bounded by
+  # max_lookback_bars -- see scoring.py pass-3) -- 20 trading days, matching gap_window's span.
+  worst_window_days: 20
 
 # ----------------------------------------------------------------------------------------
 # iter-2 CONSUMED — Sector/industry leadership. Component weights (must cover every component
@@ -1884,6 +1892,22 @@ methodology:
       category: factor_stats
       definition: "Volatility computed from NEGATIVE returns only — the kind of volatility that actually hurts. Used so 'risk' never penalises healthy upside movement."
       where: "Research → Factor Lab volatility family, risk-adjusted ratios."
+    - term: "overnight-gap profile"
+      category: factor_stats
+      definition: "The distribution of overnight moves (|open − prior close| / prior close) over the gap window: the median, p95 (a near-worst case), and worst gap, plus the overnight share of the same window's close-to-close return variance. The risk an invalidation level cannot protect against, since a level only triggers on a gradual decline, never a jump past it."
+      where: "Stocks, Stock Detail risk-budget card."
+      thresholds:
+        - { label: "Gap window", cmp: "=", ref: "indicators.gap_window", unit: " bars" }
+    - term: "worst 20-day window"
+      category: factor_stats
+      definition: "The most negative trailing 20-trading-day return found ANYWHERE in a name's full available as-of history — the deepest historical drawdown-window depth. Distinct from a forward max-drawdown figure, which measures forward from one as-of date."
+      where: "Stock Detail risk-budget card."
+      thresholds:
+        - { label: "Window", cmp: "=", ref: "indicators.worst_window_days", unit: " bars" }
+    - term: "distance-to-invalidation %"
+      category: factor_stats
+      definition: "The percent distance of the latest close above the invalidation level (the same level named in the setup's invalidation note) — how much room exists before the long thesis is technically wrong."
+      where: "Stock Detail risk-budget card."
     - term: "pivot"
       category: factor_stats
       definition: "The breakout trigger price at the top of a base (e.g. the base high in a VCP or flat base) — a buy is referenced TO the pivot, and proximity to it is a pattern condition."
diff --git a/apps/frontend/lib/risk-budget.ts b/apps/frontend/lib/risk-budget.ts
new file mode 100644
index 0000000..53c26b6
--- /dev/null
+++ b/apps/frontend/lib/risk-budget.ts
@@ -0,0 +1,33 @@
+/**
+ * Shared risk-budget formatting helpers (iter-40, J-24 / B-201) — the SINGLE source for rendering a
+ * `RiskBudgetComponent` (value + cross-sectional percentile), used by BOTH the Stock Detail risk-budget
+ * card and the `/stocks` leaderboard risk-budget columns, so the same stock's number reads identically
+ * in both places (single source of truth — never recomputed client-side, never a second formatter).
+ *
+ * Every `RiskBudgetComponent.value` served by the backend is ALREADY a percent number (e.g. `5.23` means
+ * "5.23%") — these helpers only round + append "%"; they never multiply by 100 (unlike
+ * `components/forward-return.tsx`'s `fmtPct`/`fmtMdd`, which format raw FRACTION returns).
+ */
+import type { RiskBudgetComponent } from "@/lib/api";
+
+/** Format an already-percent risk-budget value — "5.23%" (natural sign, never a forced "+"); null/
+ *  undefined (NA — insufficient history) renders "NA". */
+export function fmtRiskValue(value: number | null | undefined): string {
+  if (value === null || value === undefined) return "NA";
+  return `${value.toFixed(2)}%`;
+}
+
+/** Format a risk-budget percentile (a fraction in [0,1], oriented so HIGHER always means MORE risk) as
+ *  the card's "pXX of universe" label; null/undefined renders null so the caller omits the chip
+ *  entirely (never a fabricated "p0"). */
+export function fmtRiskPercentile(percentile: number | null | undefined): string | null {
+  if (percentile === null || percentile === undefined) return null;
+  return `p${Math.round(percentile * 100)} of universe`;
+}
+
+/** True when a risk-budget component carries no value (short-history / insufficient-data NA) — the
+ *  card/leaderboard render an honest "NA", never a fabricated 0. Mirrors the `naInvalidation`
+ *  short-history convention already used on this page. */
+export function isRiskBudgetNa(component: RiskBudgetComponent | null | undefined): boolean {
+  return !component || component.value === null || component.value === undefined;
+}
```
