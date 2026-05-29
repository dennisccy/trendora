"""Per-stock scoring engine against the REAL committed seed (deterministic).

Asserts the canonical contract: every stock carries three independent 0-100 scores, each with an
A-E bucket (via the single `to_bucket`) and a named component breakdown keyed to `config.scores.*`
with >=3 AVAILABLE components; the deferred `gap_climax` component is NA / available=false and
excluded from the weighted sum (never fabricated); each score is a config-weighted blend (changing
a weight changes the score); the row carries a setup status + non-empty reason; output is
deterministic; and the as-of date bounds the computation (no lookahead).
"""
from __future__ import annotations

from sqlmodel import Session, select

from app.config import load_config
from app.engine.buckets import to_bucket
from app.engine.prices import latest_data_date
from app.engine.scoring import score_stocks
from app.engine.setups import ALL_STATUSES
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
    assert len(rows) == len(cfg.universe.symbols)
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
        assert row["sector"] in set(cfg.etfs.sector.values())


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
