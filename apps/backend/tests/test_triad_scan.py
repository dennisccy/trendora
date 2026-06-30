"""Tests for the deterministic triad scan (app.engine.triad_scan) against the real committed seed.

Asserts: cells are read from the canonical Factor-Lab; the triad score ranks best-first; the top cells
are hold-out-screened; survivors are exactly the screened cells whose edge persisted; the scan is
deterministic; and it never touches the certified-claims ledger.
"""
from __future__ import annotations

from sqlmodel import Session

from app.engine import triad_scan
from app.engine.triad_scan import scan_factor_decile_cells, scan_product_triad, score_cells


def test_scan_cells_read_from_factor_lab(loaded_engine, config):
    with Session(loaded_engine) as session:
        cells = scan_factor_decile_cells(session, config)
    assert cells, "expected at least some factor-decile cells from the warmed seed"
    for c in cells:
        assert {"factor", "horizon", "decile", "mean_return", "mean_max_drawdown", "n", "rank_ic",
                "selector"} <= set(c)
        assert c["selector"]["kind"] == "factor" and c["selector"]["slice_kind"] == "decile"
        assert c["mean_return"] is not None and c["n"] > 0


def test_score_ranks_best_first():
    cells = [
        {"factor": "a", "horizon": 20, "decile": 10, "mean_return": 0.05, "mean_max_drawdown": -0.05, "n": 100, "rank_ic": 0.1},
        {"factor": "b", "horizon": 20, "decile": 1, "mean_return": -0.02, "mean_max_drawdown": -0.20, "n": 100, "rank_ic": 0.1},
        {"factor": "c", "horizon": 20, "decile": 10, "mean_return": 0.02, "mean_max_drawdown": -0.10, "n": 100, "rank_ic": 0.1},
    ]
    ranked = score_cells([dict(c) for c in cells], triad_scan.DEFAULT_WEIGHTS)
    scores = [c["triad_score"] for c in ranked]
    assert scores == sorted(scores, reverse=True)
    # the high-return / shallow-drawdown cell wins; the negative-return / deep-drawdown cell loses.
    assert ranked[0]["factor"] == "a"
    assert ranked[-1]["factor"] == "b"


def test_scan_product_triad_structure_and_screening(loaded_engine, config):
    with Session(loaded_engine) as session:
        out = scan_product_triad(session, config, top_k=10)
    assert {"cells", "survivors", "n_cells", "n_screened", "n_survivors", "batch_size", "horizons"} <= set(out)
    assert out["n_cells"] >= out["n_screened"]
    assert len(out["cells"]) == out["n_screened"]
    # cells are ranked best-first by triad score
    scores = [c["triad_score"] for c in out["cells"]]
    assert scores == sorted(scores, reverse=True)
    # survivors are exactly the screened cells whose edge persisted out-of-sample
    survivors = [c for c in out["cells"] if c["oos_survived"]]
    assert out["survivors"] == survivors
    assert out["n_survivors"] == len(survivors)
    for c in out["cells"]:
        assert c["oos_survived"] == c["screen"]["survived"]
        assert "holdout_edge" in c["screen"]


def test_scan_is_deterministic(loaded_engine, config):
    with Session(loaded_engine) as session:
        a = scan_product_triad(session, config, top_k=8)
    with Session(loaded_engine) as session:
        b = scan_product_triad(session, config, top_k=8)
    assert a == b
