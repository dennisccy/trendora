"""Per-stock scoring engine against the REAL committed seed (deterministic).

Asserts the canonical contract: every stock carries three independent 0-100 scores, each with an
A-E bucket (via the single `to_bucket`) and a named component breakdown keyed to `config.scores.*`
with >=3 AVAILABLE components; the deferred `gap_climax` component is NA / available=false and
excluded from the weighted sum (never fabricated); each score is a config-weighted blend (changing
a weight changes the score); the row carries a setup status + non-empty reason; output is
deterministic; and the as-of date bounds the computation (no lookahead).
"""
from __future__ import annotations

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.engine import indicators as ind
from app.engine.buckets import to_bucket
from app.engine.indicators import sma
from app.engine.prices import bars_asof, bars_asof_window, closes, latest_data_date, opens
from app.engine.scoring import score_stocks
from app.engine.setups import ALL_STATUSES
from app.engine.universe_screen import read_pool
from app.engine.themes import theme_name
from app.models import DailyPrice

SCORE_KEYS = ("leadership", "entry_quality", "risk")


def _row(rows, ticker):
    return next(r for r in rows if r["ticker"] == ticker)


def test_each_stock_has_three_bucketed_explainable_scores(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_stocks(session, asof, cfg)

    rows = result["rows"]
    # iter-33 (J-93): one row per POINT-IN-TIME-RESOLVED member (the scored set == result["members"]),
    # a non-empty subset of the static universe at a full-universe date — not the static universe size.
    assert len(rows) == len(result["members"])
    assert 0 < len(rows) <= len(read_pool())  # iter-18: resolved members are a subset of the 548-pool
    assert result["benchmark"] == "SPY"
    assert [r["rank"] for r in rows] == list(range(1, len(rows) + 1))
    # ranked by leadership, non-increasing
    leaderships = [r["leadership"]["score"] for r in rows]
    assert leaderships == sorted(leaderships, reverse=True)

    expected_keys = {
        "leadership": set(cfg.scores.leadership.weights),
        "entry_quality": set(cfg.scores.entry_quality.weights),
        "risk": set(cfg.scores.risk.weights),
    }
    for row in rows:
        for key in SCORE_KEYS:
            block = row[key]
            assert 0 <= block["score"] <= 100
            assert block["bucket"] == to_bucket(block["score"], cfg)   # single bucketing fn
            assert block["bucket"] in {"A", "B", "C", "D", "E"}
            names = {c["name"] for c in block["components"]}
            assert names == expected_keys[key]                          # named + keyed to config
            available = [c for c in block["components"] if c["available"]]
            assert len(available) >= 3                                  # >=3 available (explainability)
        # setup status + reason ride on the same row (single composition path)
        assert row["setup"]["status"] in ALL_STATUSES
        assert isinstance(row["setup"]["reason"], str) and row["setup"]["reason"].strip()
        # iter-18: broadened-pool names have no `cfg.stock_sectors` mapping, so sector is honestly None
        # (never a fabricated sector — pool-sector surfacing is J-13/J-14, out of scope). Config-universe
        # names still carry a valid mapped sector.
        assert row["sector"] is None or row["sector"] in set(cfg.etfs.sector.values())


def test_gap_climax_is_na_and_excluded_never_fabricated(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_stocks(session, asof, cfg)

    nvda = _row(result["rows"], "NVDA")
    risk_components = {c["name"]: c for c in nvda["risk"]["components"]}
    gap = risk_components["gap_climax"]
    assert gap["available"] is False
    assert gap["raw"] is None and gap["percentile"] is None and gap["contribution"] is None
    # AVAILABLE contributions sum to the score itself (gap's weight is excluded from the blend,
    # NOT counted as a 0 contribution) — the renormalize-over-available-weight invariant.
    contributions = [c["contribution"] for c in nvda["risk"]["components"] if c["available"]]
    assert abs(sum(contributions) - nvda["risk"]["score"]) < 0.1


def test_contextual_risk_components_read_canonical_scores(loaded_engine):
    """`regime` and `sector_strength` are normalized directly from the canonical 0-100 scores
    they read (higher danger when weaker) — available and in range, not peer-percentiled."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_stocks(session, asof, cfg)
    nvda = _row(result["rows"], "NVDA")
    risk = {c["name"]: c for c in nvda["risk"]["components"]}
    for name in ("regime", "sector_strength"):
        assert risk[name]["available"] is True
        assert 0 <= risk[name]["percentile"] <= 1   # the [0,1] danger sub-score


def test_score_is_a_config_weighted_blend(loaded_engine):
    """Changing a Leadership weight changes the Leadership score — proving the blend reads config
    weights (not a hard-coded formula)."""
    base = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        base_result = score_stocks(session, asof, base)

        tweaked = load_config()
        tweaked.scores.leadership.weights = {
            "rs_spy_1m": 0.40, "rs_spy_3m": 0.10, "rs_sector": 0.10, "rs_theme": 0.10,
            "ma_stack": 0.10, "high_proximity": 0.10, "up_down_vol": 0.10,
        }
        tweaked_result = score_stocks(session, asof, tweaked)

    base_nvda = _row(base_result["rows"], "NVDA")["leadership"]["score"]
    tweaked_nvda = _row(tweaked_result["rows"], "NVDA")["leadership"]["score"]
    assert base_nvda != tweaked_nvda


def test_score_stocks_is_deterministic(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        first = score_stocks(session, asof, cfg)
        second = score_stocks(session, asof, cfg)
    assert first == second


def test_invalidation_level_is_canonical_sma_and_note_built_server_side(loaded_engine):
    """iter-4: each row carries a structured `invalidation` whose `level` is EXACTLY the canonical
    `sma(closes_asof, config invalidation ma_period)` — the same 50-DMA that ends the /bars chart
    series and feeds the scoring extension/support components (single source). The human note is
    built in the backend (rendered verbatim by the UI), never assembled client-side."""
    cfg = load_config()
    inv_period = cfg.decision_rules.invalidation.ma_period
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_stocks(session, asof, cfg)
        nvda_closes = closes(bars_asof(session, "NVDA", asof))
    expected_level = sma(nvda_closes, inv_period)
    assert expected_level is not None  # NVDA has ample history at the latest date

    nvda = _row(result["rows"], "NVDA")
    inv = nvda["invalidation"]
    assert inv["ma_period"] == inv_period
    assert inv["basis"] == f"{inv_period}-DMA"
    assert inv["level"] == expected_level                 # canonical MA — no second computation
    assert inv["price"] == nvda_closes[-1]                # latest close (as-of)
    assert inv["note"] == f"Invalid below the {inv_period}-DMA at ${expected_level:.2f}"


def test_earliest_date_universe_is_honestly_empty_warmup(loaded_engine):
    """iter-33 (J-93): at the earliest as-of date the POINT-IN-TIME universe is honestly EMPTY — no
    candidate yet has the required >= `min_history_bars` trailing bars (a deterministic warm-up). The
    scored rows are empty (no fabricated members), and `members` is empty — not an error."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        dates = list(session.exec(select(DailyPrice.date).distinct().order_by(DailyPrice.date)).all())
        earliest = score_stocks(session, dates[0], cfg)
    assert earliest["rows"] == []  # warm-up: no member resolves on day one (no fabricated rows)
    assert earliest["members"] == []


def test_invalidation_na_is_honest_never_fabricated_unit():
    """The invalidation level is an honest NA (`level is None` + the honest note, no fabricated price)
    whenever the canonical 50-DMA is unavailable — a UNIT assertion on the single `_invalidation`
    composer. (Post-J-93 a RESOLVED member always has >= 200 bars, so it always has the 50-DMA; the
    honest-NA contract is exercised here directly so it can never silently regress.)"""
    from app.engine.scoring import _invalidation
    cfg = load_config()
    ma_period = cfg.decision_rules.invalidation.ma_period
    inv = _invalidation(f"{ma_period}-DMA", ma_period, None, 123.45)  # level None (short history)
    assert inv["level"] is None
    assert inv["note"] == "Invalidation level NA — insufficient history"
    assert inv["ma_period"] == ma_period


def test_themes_are_the_reverse_of_config_themes(loaded_engine):
    """iter-4: each row carries `themes` = every config theme whose member list contains the ticker,
    in config order, named via the SHARED `theme_name` derivation (no second theme→name mapping)."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_stocks(session, asof, cfg)

    for row in result["rows"]:
        expected = [slug for slug, members in cfg.themes.items() if row["ticker"] in members]
        assert [t["slug"] for t in row["themes"]] == expected            # reverse map, config order
        assert all(t["name"] == theme_name(t["slug"]) for t in row["themes"])  # shared naming
    # NVDA is a member of exactly these themes (multi-theme membership renders multiple chips)
    nvda = _row(result["rows"], "NVDA")
    assert [t["slug"] for t in nvda["themes"]] == ["ai_data_centre", "semiconductors", "megacap_leaders"]


def test_invalidation_and_themes_ride_on_the_shared_row_for_list_and_detail(loaded_engine):
    """Both new fields live on the single `score_stocks` row, so the list and detail paths carry
    them identically (J-06 single source — proven byte-identical at the API layer in test_api_engine)."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        rows = score_stocks(session, asof, cfg)["rows"]
    for row in rows:
        assert set(row["invalidation"]) == {"basis", "ma_period", "level", "price", "note"}
        assert isinstance(row["themes"], list)
        # iter-11: the VCP pattern flag also rides the SAME shared row (list == detail; J-06)
        assert set(row["vcp"]) == {"flagged", "reason", "pivot", "invalidation", "contractions", "detail"}
        # iter-9: the two new detected patterns ride the row the same way (same contract, no contractions)
        for name in ("pullback_to_rising_dma", "flat_base_breakout"):
            assert set(row[name]) == {"flagged", "reason", "pivot", "invalidation", "detail"}


def test_vcp_block_rides_each_row(loaded_engine):
    """iter-11: every row carries a `vcp` block (the detected pattern) ALONGSIDE setup/invalidation, a
    separate flag with the documented shape. A not-flagged row carries NO fabricated pivot/level."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        rows = score_stocks(session, asof, cfg)["rows"]
    for row in rows:
        vcp = row["vcp"]
        assert set(vcp) == {"flagged", "reason", "pivot", "invalidation", "contractions", "detail"}
        assert isinstance(vcp["flagged"], bool)
        assert isinstance(vcp["reason"], str) and vcp["reason"].strip()
        assert set(vcp["invalidation"]) == {"level", "note"}
        if vcp["flagged"]:
            assert vcp["pivot"] is not None
            assert vcp["invalidation"]["level"] is not None
            assert len(vcp["contractions"]) >= cfg.patterns.vcp.min_contractions
        else:
            assert vcp["pivot"] is None and vcp["invalidation"]["level"] is None  # never fabricated


def test_vcp_is_a_pattern_not_a_status(loaded_engine, monkeypatch):
    """Critical anti-goal (VCP is a pattern, not a status): "VCP" is never a setup status, and adding
    the VCP flag changes NO row's setup_status — even when the detector is forced to flag EVERY name."""
    assert "VCP" not in ALL_STATUSES

    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        baseline = {r["ticker"]: r["setup"]["status"] for r in score_stocks(session, asof, cfg)["rows"]}

        forced = {
            "flagged": True, "reason": "forced", "pivot": 1.0,
            "invalidation": {"level": 1.0, "note": "forced"}, "contractions": [9.0, 5.0],
            "detail": {"n_contractions": 2, "volume_ratio": 0.5, "dist_from_pivot_pct": 1.0},
        }
        monkeypatch.setattr("app.engine.scoring.detect_vcp", lambda *a, **k: dict(forced))
        forced_rows = score_stocks(session, asof, cfg)["rows"]

    forced_status = {r["ticker"]: r["setup"]["status"] for r in forced_rows}
    assert forced_status == baseline                       # the VCP flag never altered any setup status
    assert all(r["vcp"]["flagged"] for r in forced_rows)   # the detector really did flag every name
    assert all(r["setup"]["status"] in ALL_STATUSES for r in forced_rows)


def test_new_patterns_are_patterns_not_statuses(loaded_engine, monkeypatch):
    """Critical anti-goal (New patterns are patterns, not statuses): force-flagging EACH new detected
    pattern for EVERY name changes NO row's setup_status — the patterns ride alongside the setup, never
    enter the setup-status enum, and never promote a name. Mirrors the VCP pattern-not-status proof."""
    cfg = load_config()
    forced = {
        "flagged": True, "reason": "forced", "pivot": 1.0,
        "invalidation": {"level": 1.0, "note": "forced"},
        "detail": {},
    }
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        baseline = {r["ticker"]: r["setup"]["status"] for r in score_stocks(session, asof, cfg)["rows"]}

        for name in ("detect_pullback_to_rising_dma", "detect_flat_base_breakout"):
            monkeypatch.setattr(f"app.engine.scoring.{name}", lambda *a, **k: dict(forced))
        forced_rows = score_stocks(session, asof, cfg)["rows"]

    forced_status = {r["ticker"]: r["setup"]["status"] for r in forced_rows}
    assert forced_status == baseline  # neither new pattern altered any setup status
    assert all(r["pullback_to_rising_dma"]["flagged"] for r in forced_rows)  # detectors really flagged
    assert all(r["flat_base_breakout"]["flagged"] for r in forced_rows)
    assert all(r["setup"]["status"] in ALL_STATUSES for r in forced_rows)


def test_volatility_values_ride_the_row_but_enter_no_score(loaded_engine, monkeypatch):
    """CRITICAL keystone (iter-13 / J-30 — the guard protecting J-06 score consistency AND the J-07
    Risk-Off→Actionable gate): the three new volatility-family values (hv / vcp_contraction /
    downside_vol) ride on every canonical row for the read-only Factor Lab, but enter NO weighted score.
    Force the three volatility indicators to an absurd constant and assert every row's three scores +
    A-E buckets + setup status + rank are BYTE-IDENTICAL to baseline — proving the values never feed
    `_build_score`. (Source guard: none of the three keys appears in any `scores.*.weights`.) Mirrors the
    proven `test_vcp_is_a_pattern_not_a_status` invariance proof."""
    cfg = load_config()
    # source-level guard: the volatility keys are absent from every weighted score's component set
    vol_keys = {"hv", "vcp_contraction", "downside_vol"}
    for weights in (cfg.scores.leadership.weights, cfg.scores.entry_quality.weights, cfg.scores.risk.weights):
        assert not (vol_keys & set(weights))

    def _snapshot(rows):
        return {
            r["ticker"]: (
                r["leadership"]["score"], r["leadership"]["bucket"],
                r["entry_quality"]["score"], r["entry_quality"]["bucket"],
                r["risk"]["score"], r["risk"]["bucket"],
                r["setup"]["status"], r["rank"],
            )
            for r in rows
        }

    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        baseline_rows = score_stocks(session, asof, cfg)["rows"]
        baseline = _snapshot(baseline_rows)
        for r in baseline_rows:
            assert vol_keys <= set(r)  # every row carries the three volatility values

        # force the three volatility indicators to an absurd constant — must perturb NO score/bucket/setup
        monkeypatch.setattr("app.engine.indicators.hist_volatility", lambda *a, **k: 999.0)
        monkeypatch.setattr("app.engine.indicators.vol_contraction", lambda *a, **k: 999.0)
        monkeypatch.setattr("app.engine.indicators.downside_vol", lambda *a, **k: 999.0)
        forced_rows = score_stocks(session, asof, cfg)["rows"]

    assert _snapshot(forced_rows) == baseline  # volatility additions changed nothing in any score path
    assert all(r["hv"] == 999.0 for r in forced_rows)             # the monkeypatch really took effect
    assert all(r["vcp_contraction"] == 999.0 for r in forced_rows)
    assert all(r["downside_vol"] == 999.0 for r in forced_rows)
    # baseline values are the REAL computed numbers (NVDA has ample history → all three numeric, not NA)
    nvda = _row(baseline_rows, "NVDA")
    assert isinstance(nvda["hv"], float) and nvda["hv"] != 999.0
    assert isinstance(nvda["vcp_contraction"], float) and isinstance(nvda["downside_vol"], float)


RISK_BUDGET_SCALAR_KEYS = ("atr_pct", "downside_vol", "worst_20d_window", "distance_to_invalidation_pct")
RISK_BUDGET_GAP_KEYS = ("median", "p95", "worst", "overnight_variance_share")


def test_risk_budget_fields_present_with_cross_sectional_percentiles(loaded_engine):
    """iter-40 (J-24 / B-201): every row carries an additive `risk_budget` block — ATR% / downside vol /
    the overnight-gap profile (median/p95/worst/overnight-variance-share) / worst-20d window /
    distance-to-invalidation %, each `{value, percentile}` — computed for a real, ample-history name
    (NVDA), with percentiles that are genuinely CROSS-SECTIONAL (not a fabricated constant)."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_stocks(session, asof, cfg)
    rows = result["rows"]
    nvda = _row(rows, "NVDA")
    rb = nvda["risk_budget"]

    for key in RISK_BUDGET_SCALAR_KEYS:
        leaf = rb[key]
        assert set(leaf) == {"value", "percentile"}
        assert isinstance(leaf["value"], float)
        assert leaf["percentile"] is not None and 0 <= leaf["percentile"] <= 1

    assert set(rb["gap_profile"]) == set(RISK_BUDGET_GAP_KEYS)
    for key in RISK_BUDGET_GAP_KEYS:
        leaf = rb["gap_profile"][key]
        assert set(leaf) == {"value", "percentile"}
        assert isinstance(leaf["value"], float)
        assert leaf["percentile"] is not None and 0 <= leaf["percentile"] <= 1

    # genuinely cross-sectional: not every peer shares NVDA's percentile (never a fabricated constant).
    atr_percentiles = {r["ticker"]: r["risk_budget"]["atr_pct"]["percentile"] for r in rows}
    assert len(set(atr_percentiles.values())) > 1


def test_risk_budget_gap_p95_byte_matches_offline_recomputation(loaded_engine):
    """Correctness (DoD): a spot-checked overnight-gap p95 value byte-matches an INDEPENDENT offline
    recomputation from the same as-of bars — the served number is never a UI/second-path recompute."""
    cfg = load_config()
    icfg = cfg.indicators
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_stocks(session, asof, cfg)
        nvda_bars = bars_asof_window(session, "NVDA", asof, icfg.max_lookback_bars)
    expected = ind.overnight_gap_profile(opens(nvda_bars), closes(nvda_bars), icfg.gap_window)
    assert expected is not None  # NVDA has ample history

    nvda = _row(result["rows"], "NVDA")
    assert nvda["risk_budget"]["gap_profile"]["p95"]["value"] == pytest.approx(expected["p95"])
    assert nvda["risk_budget"]["gap_profile"]["median"]["value"] == pytest.approx(expected["median"])


def test_risk_budget_worst_20d_byte_matches_offline_recomputation(loaded_engine):
    """The worst-20d window reads the name's FULL as-of history (not the max_lookback_bars-bounded
    slice — logged interpretation, assumptions.md iter-40); spot-check against an independent
    recomputation over the SAME full series."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_stocks(session, asof, cfg)
        nvda_full_closes = closes(bars_asof(session, "NVDA", asof))
    expected = ind.worst_20d_window(nvda_full_closes, cfg.indicators.worst_window_days)
    assert expected is not None

    nvda = _row(result["rows"], "NVDA")
    assert nvda["risk_budget"]["worst_20d_window"]["value"] == pytest.approx(expected)


def test_risk_budget_atr_and_downside_vol_are_reused_not_recomputed(loaded_engine, monkeypatch):
    """B-201 ★ Do NOT touch / trap guard: ATR% and downside-vol MUST be REUSED from pass-1/pass-3's
    existing computation for the risk-budget card, never called a second time. Wrap both indicator
    functions with a call counter and assert each fires exactly once per resolved member."""
    cfg = load_config()
    calls = {"atr_pct": 0, "downside_vol": 0}
    real_atr_pct, real_downside_vol = ind.atr_pct, ind.downside_vol

    def _counting_atr_pct(*a, **k):
        calls["atr_pct"] += 1
        return real_atr_pct(*a, **k)

    def _counting_downside_vol(*a, **k):
        calls["downside_vol"] += 1
        return real_downside_vol(*a, **k)

    monkeypatch.setattr("app.engine.indicators.atr_pct", _counting_atr_pct)
    monkeypatch.setattr("app.engine.indicators.downside_vol", _counting_downside_vol)
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_stocks(session, asof, cfg)

    n_members = len(result["members"])
    assert calls["atr_pct"] == n_members       # once per ticker (pass-1 only) — never a second call
    assert calls["downside_vol"] == n_members  # once per ticker (pass-3 only) — never a second call

    nvda = _row(result["rows"], "NVDA")
    risk_atr = next(c for c in nvda["risk"]["components"] if c["name"] == "atr_pct")
    # the SAME reused raw value — `risk.components[].raw` is rounded to 4dp for the score-breakdown
    # display (`_build_score`'s `round(raw, 4)`); `risk_budget.atr_pct.value` stores the SAME
    # unrounded `raws["atr_pct"]` (matching the unrounded convention the iter-13 `downside_vol`/`hv`/
    # `vcp_contraction` top-level fields already use) — round for an exact, not merely approximate, check.
    assert round(nvda["risk_budget"]["atr_pct"]["value"], 4) == risk_atr["raw"]


def test_risk_budget_values_ride_the_row_but_enter_no_score(loaded_engine, monkeypatch):
    """CRITICAL keystone (iter-40 / J-24 / B-201 ★ Do NOT touch score weights): the risk-budget
    components ride on every canonical row for the stock-detail card + leaderboard columns, but enter
    NO weighted score. Force the two new indicator functions to an absurd constant and assert every
    row's three scores + A-E buckets + setup status + rank are BYTE-IDENTICAL to baseline — proving the
    values never feed `_build_score`. Mirrors `test_volatility_values_ride_the_row_but_enter_no_score`."""
    cfg = load_config()
    risk_budget_keys = {
        "atr_pct", "downside_vol", "gap_profile", "worst_20d_window", "distance_to_invalidation_pct",
    }
    for weights in (cfg.scores.leadership.weights, cfg.scores.entry_quality.weights, cfg.scores.risk.weights):
        assert not (risk_budget_keys & set(weights))

    def _snapshot(rows):
        return {
            r["ticker"]: (
                r["leadership"]["score"], r["leadership"]["bucket"],
                r["entry_quality"]["score"], r["entry_quality"]["bucket"],
                r["risk"]["score"], r["risk"]["bucket"],
                r["setup"]["status"], r["rank"],
            )
            for r in rows
        }

    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        baseline_rows = score_stocks(session, asof, cfg)["rows"]
        baseline = _snapshot(baseline_rows)
        for r in baseline_rows:
            assert "risk_budget" in r

        # force the two NEW indicator functions to an absurd constant — must perturb NO score/bucket/setup
        monkeypatch.setattr(
            "app.engine.indicators.overnight_gap_profile",
            lambda *a, **k: {"median": 999.0, "p95": 999.0, "worst": 999.0, "overnight_variance_share": 999.0},
        )
        monkeypatch.setattr("app.engine.indicators.worst_20d_window", lambda *a, **k: 999.0)
        forced_rows = score_stocks(session, asof, cfg)["rows"]

    assert _snapshot(forced_rows) == baseline  # risk-budget additions changed nothing in any score path
    nvda = _row(forced_rows, "NVDA")
    assert nvda["risk_budget"]["gap_profile"]["p95"]["value"] == 999.0        # the monkeypatch took effect
    assert nvda["risk_budget"]["worst_20d_window"]["value"] == 999.0


def test_asof_bounds_the_computation_no_lookahead(loaded_engine):
    """The as-of date bounds the data window: scoring at an earlier date echoes that date and
    produces a different ranking than the latest date (it cannot see later bars)."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        dates = list(session.exec(select(DailyPrice.date).distinct().order_by(DailyPrice.date)).all())
        earlier = dates[len(dates) // 2]
        latest = dates[-1]
        early_result = score_stocks(session, earlier, cfg)
        late_result = score_stocks(session, latest, cfg)

    assert early_result["asof_date"] == earlier.isoformat()
    assert late_result["asof_date"] == latest.isoformat()
    # a different as-of window yields a different canonical result (the as-of bound is wired in)
    assert early_result["rows"] != late_result["rows"]
