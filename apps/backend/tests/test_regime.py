"""Market Regime engine against the REAL committed seed (deterministic).

Asserts the canonical contract: score in [0,100], label is one of the six configured labels,
breadth in [0,100], components present, the label-edge boundary mapping is correct, and the
output is byte-identical across repeated calls (determinism on the frozen seed).
"""
from __future__ import annotations

from sqlmodel import Session

from app.config import load_config
from app.engine.labels import label_for
from app.engine.prices import latest_data_date
from app.engine.regime import score_regime


def test_score_regime_shape_and_ranges(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_regime(session, asof, cfg)

    assert 0 <= result["score"] <= 100
    assert result["label"] in cfg.regime.labels
    assert 0 <= result["breadth_above_50dma"] <= 100
    assert 0 <= result["breadth_above_200dma"] <= 100
    assert result["new_high_low"]["universe_relative"] is True
    assert result["universe_relative"] is True
    assert result["asof_date"] == asof.isoformat()

    # every weighted component is present + named (explainability — no bare score)
    names = {c["name"] for c in result["components"]}
    assert {"index_ma_stack", "breadth_above_50dma", "breadth_above_200dma", "new_high_low", "vix_gate"} <= names


def test_label_edges_boundary_mapping():
    edges = load_config().regime.label_edges  # 80/65/55/45/30/0
    assert label_for(80, edges) == "Strong risk-on"
    assert label_for(79.99, edges) == "Risk-on"
    assert label_for(65, edges) == "Risk-on"
    assert label_for(64, edges) == "Narrow leadership"
    assert label_for(55, edges) == "Narrow leadership"
    assert label_for(45, edges) == "Choppy"
    assert label_for(30, edges) == "Defensive"
    assert label_for(29, edges) == "Risk-off"
    assert label_for(0, edges) == "Risk-off"


def test_score_regime_is_deterministic(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        first = score_regime(session, asof, cfg)
        second = score_regime(session, asof, cfg)
    assert first == second
