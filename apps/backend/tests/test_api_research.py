"""GET /api/research/factor-lab — the Factor Lab endpoint (iter-10, J-25).

The shared `loaded_engine` has the walk-forward snapshots + their forward_returns persisted (the
lifespan backfill), so the default factor-lab payload carries real observations. These prove: the
payload carries the config-driven factor catalog + a D1…D10 decile table (mean_return + downside
risk-adjusted + n) + rank-IC + the honest labels; the catalog matches config (config-driven, not
hard-coded); changing factor / horizon re-points the table; unknown factor / bad horizon are 422; no
price data is 503; and (J-18) the payload exposes NO as-of/date control (a cross-date aggregate).
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlmodel import Session

import main
from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.prices import latest_data_date


def test_factor_lab_default_payload(loaded_engine):
    """J-25 at the API level: the default payload (first catalog factor + default horizon) carries the
    decile table, the rank-IC, the config-driven catalog, and the honest labels — each decile with n."""
    cfg = load_config()
    fl = cfg.research.factor_lab
    with TestClient(main.app) as client:
        resp = client.get("/api/research/factor-lab")
    assert resp.status_code == 200
    data = resp.json()

    # default factor = first catalog factor; default horizon = config default_horizon
    assert data["factor"]["key"] == fl.factors[0].key
    assert data["horizon"] == cfg.walk_forward.default_horizon
    assert data["min_sample"] == cfg.walk_forward.min_sample

    # the catalog is config-driven (the dropdown vocabulary) — exact match, in order
    assert [c["key"] for c in data["factors"]] == [f.key for f in fl.factors]
    assert {"key", "label", "family", "direction", "source"} == set(data["factors"][0])

    # decile table: exactly `deciles` rows, each carrying mean_return + risk_adjusted + n
    assert len(data["deciles"]) == fl.deciles
    assert [d["decile"] for d in data["deciles"]] == list(range(1, fl.deciles + 1))
    for d in data["deciles"]:
        assert {"decile", "factor_min", "factor_max", "mean_return", "risk_adjusted", "n", "low_sample"} <= set(d)
    # the leadership_score factor never NULLs -> the seed yields >=1 observation
    assert data["n_total"] >= 1
    assert sum(d["n"] for d in data["deciles"]) == data["n_total"]

    # rank-IC + honest labels
    assert {"value", "n"} == set(data["rank_ic"])
    assert "survivorship" in data["survivorship_bias"].lower()
    assert "not a predictive model" in data["descriptive_caveat"].lower()


def test_factor_lab_no_date_control_present(loaded_engine):
    """J-18: the Factor Lab is a cross-date aggregate — its payload exposes NO as-of/date field (no
    second date state); selectors are factor + horizon only."""
    with TestClient(main.app) as client:
        data = client.get("/api/research/factor-lab").json()
    assert not any(k in data for k in ("asof_date", "as_of", "asof_dates", "date", "is_latest"))


def test_factor_lab_changing_factor_and_horizon_changes_payload(loaded_engine):
    """Changing the factor re-points the decile factor ranges; changing the horizon re-points the decile
    returns — server values, never a client recompute (assert the payload actually changes)."""
    with TestClient(main.app) as client:
        lead = client.get("/api/research/factor-lab", params={"factor": "leadership_score", "horizon": 20}).json()
        risk = client.get("/api/research/factor-lab", params={"factor": "risk_score", "horizon": 20}).json()
        lead_h60 = client.get("/api/research/factor-lab", params={"factor": "leadership_score", "horizon": 60}).json()

    assert lead["factor"]["key"] == "leadership_score" and risk["factor"]["key"] == "risk_score"
    # different factors -> different factor partitions (the decile bounds differ)
    lead_bounds = [(d["factor_min"], d["factor_max"]) for d in lead["deciles"]]
    risk_bounds = [(d["factor_min"], d["factor_max"]) for d in risk["deciles"]]
    assert lead_bounds != risk_bounds
    # different horizons -> different realized returns (the decile means differ)
    assert lead["horizon"] == 20 and lead_h60["horizon"] == 60
    lead_means = [d["mean_return"] for d in lead["deciles"]]
    lead_h60_means = [d["mean_return"] for d in lead_h60["deciles"]]
    assert lead_means != lead_h60_means


def test_factor_lab_unknown_factor_422(loaded_engine):
    """An unknown factor is rejected (422) — no fabricated factor."""
    with TestClient(main.app) as client:
        resp = client.get("/api/research/factor-lab", params={"factor": "not_a_factor"})
    assert resp.status_code == 422


def test_factor_lab_invalid_horizon_422(loaded_engine):
    """An out-of-range horizon is rejected (422) — no fabricated horizon."""
    with TestClient(main.app) as client:
        resp = client.get("/api/research/factor-lab", params={"horizon": 7})
    assert resp.status_code == 422


def test_factor_lab_503_when_no_price_data(tmp_path):
    """No price data -> explicit 503 (never a fabricated evidence row). The handler is called directly
    against an empty DB session, leaving the process engine untouched."""
    from app.api.research import factor_lab

    engine = make_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        assert latest_data_date(session) is None
        with pytest.raises(HTTPException) as exc:
            factor_lab(factor=None, horizon=None, session=session)
        assert exc.value.status_code == 503


# ==================================================================================================
# GET /api/research/factor-combination — multi-factor combination cohorts (iter-12, J-26)
# ==================================================================================================
def test_factor_combination_default_payload(loaded_engine):
    """J-26 at the API level: the default payload (config default_conditions + default horizon) carries
    the unconditional baseline + one single per condition + the combined-AND cohort, each with the full
    stat shape; the factor catalog + quantile vocabulary are config-driven; the cohort algebra holds."""
    cfg = load_config()
    comb = cfg.research.factor_lab.combination
    with TestClient(main.app) as client:
        resp = client.get("/api/research/factor-combination")
    assert resp.status_code == 200
    data = resp.json()

    # defaults resolved from config (no condition param -> config.default_conditions; default horizon)
    assert data["horizon"] == cfg.walk_forward.default_horizon
    assert data["min_sample"] == cfg.walk_forward.min_sample
    assert [c["factor"]["key"] for c in data["conditions"]] == [d.factor for d in comb.default_conditions]
    assert [c["side"] for c in data["conditions"]] == [d.side for d in comb.default_conditions]

    # config-driven vocabularies (the dropdowns) + condition limits
    assert [q["key"] for q in data["quantiles"]] == [q.key for q in comb.quantiles]
    assert [f["key"] for f in data["factors"]] == [f.key for f in cfg.research.factor_lab.factors]
    assert data["min_conditions"] == comb.min_conditions and data["max_conditions"] == comb.max_conditions

    # every cohort carries the full stat shape
    cohorts = [data["baseline"], data["combined"], *data["singles"]]
    for cohort in cohorts:
        assert {"n", "mean_return", "median_return", "hit_rate", "risk_adjusted", "low_sample"} <= set(cohort["stats"])
    assert len(data["singles"]) == len(comb.default_conditions)

    # algebra: baseline == pool; each single ⊆ pool; combined ⊆ each single
    assert data["baseline"]["stats"]["n"] == data["pool_n"]
    assert all(s["stats"]["n"] <= data["pool_n"] for s in data["singles"])
    assert data["combined"]["stats"]["n"] <= min(s["stats"]["n"] for s in data["singles"])

    # honest labels carried verbatim
    assert "survivorship" in data["survivorship_bias"].lower()
    assert "not a predictive model" in data["descriptive_caveat"].lower()


def test_factor_combination_no_date_control_present(loaded_engine):
    """J-18: the combination cohort is a cross-date aggregate — its payload exposes NO as-of/date field
    (no second date state); the only inputs are conditions + the shared horizon."""
    with TestClient(main.app) as client:
        data = client.get("/api/research/factor-combination").json()
    assert not any(k in data for k in ("asof_date", "as_of", "asof_dates", "date", "is_latest"))


def test_factor_combination_explicit_conditions_repoint(loaded_engine):
    """Passing explicit conditions re-points the cohorts; adding a 3rd condition adds a 3rd single row and
    keeps combined ≤ each single ≤ pool (server values, never a client recompute)."""
    with TestClient(main.app) as client:
        two = client.get(
            "/api/research/factor-combination",
            params=[("condition", "leadership_score:top:quintile"), ("condition", "atr_pct:bottom:tertile")],
        ).json()
        three = client.get(
            "/api/research/factor-combination",
            params=[
                ("condition", "leadership_score:top:quintile"),
                ("condition", "atr_pct:bottom:tertile"),
                ("condition", "entry_quality_score:top:half"),
            ],
        ).json()
    assert len(two["singles"]) == 2 and len(three["singles"]) == 3
    assert [c["factor"]["key"] for c in three["conditions"]] == [
        "leadership_score", "atr_pct", "entry_quality_score",
    ]
    for data in (two, three):
        assert all(s["stats"]["n"] <= data["pool_n"] for s in data["singles"])
        assert data["combined"]["stats"]["n"] <= min(s["stats"]["n"] for s in data["singles"])


def test_factor_combination_horizon_repoints(loaded_engine):
    """Changing the shared horizon re-points the cohort returns — server values (assert the payload's
    horizon changes and at least one cohort mean differs across horizons)."""
    with TestClient(main.app) as client:
        h20 = client.get("/api/research/factor-combination", params={"horizon": 20}).json()
        h60 = client.get("/api/research/factor-combination", params={"horizon": 60}).json()
    assert h20["horizon"] == 20 and h60["horizon"] == 60
    assert h20["baseline"]["stats"]["mean_return"] != h60["baseline"]["stats"]["mean_return"]


def test_factor_combination_unknown_factor_422(loaded_engine):
    with TestClient(main.app) as client:
        resp = client.get(
            "/api/research/factor-combination",
            params=[("condition", "not_a_factor:top:quintile"), ("condition", "atr_pct:bottom:tertile")],
        )
    assert resp.status_code == 422


def test_factor_combination_unknown_side_422(loaded_engine):
    with TestClient(main.app) as client:
        resp = client.get(
            "/api/research/factor-combination",
            params=[("condition", "leadership_score:sideways:quintile"), ("condition", "atr_pct:bottom:tertile")],
        )
    assert resp.status_code == 422


def test_factor_combination_unknown_quantile_422(loaded_engine):
    with TestClient(main.app) as client:
        resp = client.get(
            "/api/research/factor-combination",
            params=[("condition", "leadership_score:top:decile"), ("condition", "atr_pct:bottom:tertile")],
        )
    assert resp.status_code == 422


def test_factor_combination_malformed_condition_422(loaded_engine):
    """A condition not shaped '<factor>:<side>:<quantile>' is rejected (422) — never silently parsed."""
    with TestClient(main.app) as client:
        resp = client.get(
            "/api/research/factor-combination",
            params=[("condition", "leadership_score:top"), ("condition", "atr_pct:bottom:tertile")],
        )
    assert resp.status_code == 422


def test_factor_combination_too_few_conditions_422(loaded_engine):
    """A condition count below min_conditions is rejected (422) — no fabricated cohort."""
    with TestClient(main.app) as client:
        resp = client.get(
            "/api/research/factor-combination", params=[("condition", "leadership_score:top:quintile")]
        )
    assert resp.status_code == 422


def test_factor_combination_too_many_conditions_422(loaded_engine):
    """A condition count above max_conditions is rejected (422) — no fabricated cohort."""
    with TestClient(main.app) as client:
        resp = client.get(
            "/api/research/factor-combination",
            params=[
                ("condition", "leadership_score:top:quintile"),
                ("condition", "atr_pct:bottom:tertile"),
                ("condition", "entry_quality_score:top:half"),
                ("condition", "risk_score:bottom:quartile"),
            ],
        )
    assert resp.status_code == 422


def test_factor_combination_invalid_horizon_422(loaded_engine):
    """An out-of-range horizon is rejected (422) — no fabricated horizon."""
    with TestClient(main.app) as client:
        resp = client.get("/api/research/factor-combination", params={"horizon": 7})
    assert resp.status_code == 422


def test_factor_combination_503_when_no_price_data(tmp_path):
    """No price data -> explicit 503 (never a fabricated cohort). The handler is called directly against
    an empty DB session, leaving the process engine untouched."""
    from app.api.research import factor_combination

    engine = make_engine(f"sqlite:///{tmp_path / 'empty_comb.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        assert latest_data_date(session) is None
        with pytest.raises(HTTPException) as exc:
            factor_combination(condition=None, horizon=None, session=session)
        assert exc.value.status_code == 503
