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
from app.engine.indicators import sma
from app.engine.prices import bars_asof, closes, latest_data_date
from app.engine.scoring import score_stocks
from app.engine.setups import ALL_STATUSES
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


def test_invalidation_na_on_short_history_is_honest_never_fabricated(loaded_engine):
    """At the earliest as-of date no stock has `ma_period` bars yet, so the invalidation level is
    NA: `level is None` with an honest note and no fabricated price-derived number."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        dates = list(session.exec(select(DailyPrice.date).distinct().order_by(DailyPrice.date)).all())
        earliest = score_stocks(session, dates[0], cfg)

    na_rows = [r for r in earliest["rows"] if r["invalidation"]["level"] is None]
    assert na_rows  # nobody has a full 50-bar window on day one
    for row in na_rows:
        assert row["invalidation"]["note"] == "Invalidation level NA — insufficient history"
        assert row["invalidation"]["ma_period"] == cfg.decision_rules.invalidation.ma_period


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
