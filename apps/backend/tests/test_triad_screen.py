"""Unit tests for the lightweight hold-out screen (app.engine.triad_screen).

Pure function — no DB. Builds synthetic (date, return) observations and asserts that an edge which
PERSISTS out-of-sample survives, a fluke (strong in-sample, collapses in the hold-out) does not, and
thin data is honestly refused. Also checks the batch multiple-testing haircut and determinism.
"""
from __future__ import annotations

import math
from datetime import date, timedelta

from app.engine.triad_screen import required_holdout_edge, screen_holdout

H = 5  # small horizon → small purge window, clean separation on weekly dates


def _weekly_dates(n: int, start=date(2024, 1, 1)) -> list[date]:
    return [start + timedelta(days=7 * i) for i in range(n)]


def _series(dates, cohort_fn, control_fn):
    """Build (cohort_obs, control_obs) as [(date, return)], one obs per date per side."""
    cohort = [(d, cohort_fn(i, d)) for i, d in enumerate(dates)]
    control = [(d, control_fn(i, d)) for i, d in enumerate(dates)]
    return cohort, control


def test_persistent_edge_survives():
    dates = _weekly_dates(40)
    # cohort beats the control by +0.03 on EVERY date (in-sample and hold-out).
    cohort, control = _series(dates, lambda i, d: 0.04, lambda i, d: 0.01)
    res = screen_holdout(cohort, control, H, batch_size=1)
    assert res["survived"] is True
    assert res["holdout_dates"] >= 5 and res["in_sample_dates"] >= 5
    assert res["holdout_edge"] > 0
    assert math.isclose(res["holdout_edge"], 0.03, abs_tol=1e-9)


def test_in_sample_fluke_does_not_survive():
    dates = _weekly_dates(40)
    split_idx = 28  # ~70% in-sample boundary
    # strong +0.03 edge in-sample, then it COLLAPSES to −0.02 in the hold-out window.
    cohort, control = _series(
        dates,
        lambda i, d: 0.04 if i < split_idx else -0.01,
        lambda i, d: 0.01,
    )
    res = screen_holdout(cohort, control, H, batch_size=1)
    assert res["survived"] is False
    assert res["reason"] == "edge-did-not-persist"
    assert res["in_sample_edge"] is not None and res["in_sample_edge"] > 0
    assert res["holdout_edge"] is not None and res["holdout_edge"] <= 0


def test_thin_data_refused():
    dates = _weekly_dates(4)  # far below the 5+5 date minimum
    cohort, control = _series(dates, lambda i, d: 0.04, lambda i, d: 0.01)
    res = screen_holdout(cohort, control, H, batch_size=1)
    assert res["survived"] is False
    assert res["reason"] in ("insufficient-dates", "no-split")


def test_batch_haircut_tightens_the_bar():
    # With a positive haircut coefficient, a larger scan batch demands a higher hold-out edge.
    r1 = required_holdout_edge(1, base_edge_floor=0.0, haircut_coef=0.001)
    r_big = required_holdout_edge(1000, base_edge_floor=0.0, haircut_coef=0.001)
    assert r1 == 0.0
    assert r_big > r1
    assert math.isclose(r_big, 0.001 * math.log(1000), rel_tol=1e-12)

    # A marginal edge that clears the floor at batch=1 but not under a heavy batch haircut.
    dates = _weekly_dates(40)
    cohort, control = _series(dates, lambda i, d: 0.015, lambda i, d: 0.01)  # +0.005 edge
    survives_small = screen_holdout(cohort, control, H, batch_size=1, haircut_coef=0.001)["survived"]
    survives_big = screen_holdout(cohort, control, H, batch_size=100_000, haircut_coef=0.001)["survived"]
    assert survives_small is True
    assert survives_big is False  # 0.001*ln(100000) ≈ 0.0115 > 0.005


def test_determinism():
    dates = _weekly_dates(40)
    cohort, control = _series(dates, lambda i, d: 0.04, lambda i, d: 0.01)
    a = screen_holdout(cohort, control, H, batch_size=7)
    b = screen_holdout(cohort, control, H, batch_size=7)
    assert a == b
