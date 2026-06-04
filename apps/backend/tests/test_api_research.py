"""GET /api/research/factor-lab — the Factor Lab endpoint (iter-10, J-25).

The shared `loaded_engine` has the walk-forward snapshots + their forward_returns persisted (the
lifespan backfill), so the default factor-lab payload carries real observations. These prove: the
payload carries the config-driven factor catalog + a D1…D10 decile table (mean_return + downside
risk-adjusted + n) + rank-IC + the honest labels; the catalog matches config (config-driven, not
hard-coded); changing factor / horizon re-points the table; unknown factor / bad horizon are 422; no
price data is 503.

iter-19 (J-32) adds the point-in-time **as-of mode**: each endpoint accepts the SINGLE global `as_of`
as an OPTIONAL scoping cutoff (a mode, not a second date state — MEMORY j18-asof-on-stocks-fetch-is-
correct). The default (omitted) call is all-history and echoes `asof_date: null`; a `?as_of=D` call
scopes the pool to snapshots dated <= D and echoes the resolved `asof_date`. `?as_of=` validation
reuses the shared snapshot-served resolver (unparseable -> 422, future -> 400). The three
`test_*_no_date_control_present` tests are UPDATED to this new contract (iter-2 lesson — the `?as_of=`
is the single global date transmitted on a snapshot-served read, NOT a second/page-local date control).
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


def _oldest_research_date(client) -> str:
    """The earliest stored immutable run date (the canonical run list, descending) — the as-of cutoff
    that scopes a research lab to its earliest point-in-time window (an expanding-window subset)."""
    return min(r["asof_date"] for r in client.get("/api/runs").json()["runs"])


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
    """J-18 (iter-19 UPDATED contract — iter-2 lesson, not a regression): the Factor Lab accepts the
    SINGLE global `as_of` as an OPTIONAL point-in-time scoping cutoff (a mode, not a second date state).
    The default (all-history) payload echoes `asof_date: null`; a `?as_of=D` call echoes the resolved
    cutoff. There is NO second, independent date field (no `asof_dates`/`date`/`is_latest`) — the only
    date is the single global as-of transmitted on the read (MEMORY j18-asof-on-stocks-fetch-is-correct)."""
    with TestClient(main.app) as client:
        default = client.get("/api/research/factor-lab").json()
        oldest = _oldest_research_date(client)
        scoped = client.get(f"/api/research/factor-lab?as_of={oldest}").json()
    # all-history default: the echo is present but null (not scoped) — NOT a second date STATE
    assert default["asof_date"] is None
    # scoped: the resolved single global as-of is echoed (expected, correct — NOT a J-18 violation)
    assert scoped["asof_date"] == oldest
    # no SECOND independent date field beyond the single global as-of echo (no page-local/2nd date state)
    for data in (default, scoped):
        assert not any(k in data for k in ("asof_dates", "date", "is_latest"))


def test_factor_lab_as_of_scopes_pool_and_echoes_resolved_cutoff(loaded_engine):
    """J-32 at the API level: a historical `?as_of=D` scopes the factor-lab pool to snapshots dated <= D
    (the expanding-window discipline — strictly fewer observations than all-history) and echoes the
    resolved `asof_date`; the default (omitted) call is all-history with `asof_date` null."""
    with TestClient(main.app) as client:
        oldest = _oldest_research_date(client)
        all_history = client.get("/api/research/factor-lab").json()
        scoped = client.get(f"/api/research/factor-lab?as_of={oldest}").json()
    assert all_history["asof_date"] is None
    assert scoped["asof_date"] == oldest
    assert 0 < scoped["n_total"] < all_history["n_total"]  # oldest cutoff pools strictly fewer, not empty


def test_factor_lab_as_of_unparseable_422(loaded_engine):
    """An unparseable `?as_of=` is rejected 422 (reusing the shared snapshot-served validator) — never a
    fabricated window."""
    with TestClient(main.app) as client:
        assert client.get("/api/research/factor-lab?as_of=not-a-date").status_code == 422


def test_factor_lab_as_of_future_400(loaded_engine):
    """A future `?as_of=` (after the latest data date) is rejected 400 — never a fabricated forward window."""
    with TestClient(main.app) as client:
        assert client.get("/api/research/factor-lab?as_of=2999-01-01").status_code == 400


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
    """J-26 at the API level: the default payload (config default_conditions + default horizon) carries the
    unconditional baseline + one single per condition + the HEADLINE composite rank-blend cohort + the
    SECONDARY strict-overlap cohort, each with the full stat shape; the factor catalog + quantile vocabulary
    are config-driven; the cohort algebra holds; AND (the iter-18 headline) the composite cohort is non-empty
    and CLEARS min_sample on the real seed — no longer perpetually 0/NA."""
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

    # config-driven vocabularies (the dropdowns) + condition limits (max raised to the catalog count, 11)
    assert [q["key"] for q in data["quantiles"]] == [q.key for q in comb.quantiles]
    assert [f["key"] for f in data["factors"]] == [f.key for f in cfg.research.factor_lab.factors]
    assert data["min_conditions"] == comb.min_conditions and data["max_conditions"] == comb.max_conditions
    assert data["max_conditions"] == len(cfg.research.factor_lab.factors)  # up to ALL catalog factors

    # the composite quantile + weighting are echoed from config (transparent, config-driven labels)
    assert data["composite_quantile"]["key"] == comb.composite.quantile
    assert data["weighting"]["scheme"] == comb.composite.weighting.scheme

    # every cohort carries the full stat shape
    cohorts = [data["baseline"], data["composite"], data["strict_overlap"], *data["singles"]]
    for cohort in cohorts:
        assert {"n", "mean_return", "median_return", "hit_rate", "risk_adjusted", "low_sample"} <= set(cohort["stats"])
    assert len(data["singles"]) == len(comb.default_conditions)

    # algebra: baseline == pool; each single ⊆ pool; composite ⊆ pool; strict_overlap ⊆ each single
    assert data["baseline"]["stats"]["n"] == data["pool_n"]
    assert all(s["stats"]["n"] <= data["pool_n"] for s in data["singles"])
    assert data["composite"]["stats"]["n"] <= data["pool_n"]
    assert data["strict_overlap"]["stats"]["n"] <= min(s["stats"]["n"] for s in data["singles"])

    # THE HEADLINE BAR-RAISE: the composite cohort is non-empty AND clears min_sample (populated stats)
    assert data["composite"]["stats"]["n"] > 0
    assert data["composite"]["stats"]["n"] >= data["min_sample"]
    assert data["composite"]["stats"]["low_sample"] is False
    assert data["composite"]["stats"]["mean_return"] is not None

    # honest labels carried verbatim
    assert "survivorship" in data["survivorship_bias"].lower()
    assert "not a predictive model" in data["descriptive_caveat"].lower()


def test_factor_combination_no_date_control_present(loaded_engine):
    """J-18 (iter-19 UPDATED contract — iter-2 lesson, not a regression): the combination cohort accepts
    the SINGLE global `as_of` as an OPTIONAL point-in-time scoping cutoff (a mode, not a second date
    state). The default (all-history) payload echoes `asof_date: null`; a `?as_of=D` call echoes the
    resolved cutoff. There is NO second, independent date field — the only inputs are conditions + the
    shared horizon + the single global as-of transmitted on the read."""
    with TestClient(main.app) as client:
        default = client.get("/api/research/factor-combination").json()
        oldest = _oldest_research_date(client)
        scoped = client.get(f"/api/research/factor-combination?as_of={oldest}").json()
    assert default["asof_date"] is None
    assert scoped["asof_date"] == oldest
    for data in (default, scoped):
        assert not any(k in data for k in ("asof_dates", "date", "is_latest"))


def test_factor_combination_as_of_scopes_pool_and_echoes_resolved_cutoff(loaded_engine):
    """J-32 at the API level: a historical `?as_of=D` scopes the combination pool to snapshots dated <= D
    (a non-increasing expanding-window subset — pool_n never grows toward the cutoff) and echoes the
    resolved `asof_date`; the default call is all-history with `asof_date` null. (The exact strict n-drop +
    no-future-leak is proven on a controlled fixture in test_research.py.)"""
    with TestClient(main.app) as client:
        oldest = _oldest_research_date(client)
        all_history = client.get("/api/research/factor-combination").json()
        scoped = client.get(f"/api/research/factor-combination?as_of={oldest}").json()
    assert all_history["asof_date"] is None
    assert scoped["asof_date"] == oldest
    assert 0 < scoped["pool_n"] <= all_history["pool_n"]  # expanding window: oldest cutoff is a subset


def test_factor_combination_as_of_unparseable_422(loaded_engine):
    """An unparseable `?as_of=` is rejected 422 (shared validator) — never a fabricated window."""
    with TestClient(main.app) as client:
        assert client.get("/api/research/factor-combination?as_of=not-a-date").status_code == 422


def test_factor_combination_as_of_future_400(loaded_engine):
    """A future `?as_of=` (after the latest data date) is rejected 400 — never a fabricated forward window."""
    with TestClient(main.app) as client:
        assert client.get("/api/research/factor-combination?as_of=2999-01-01").status_code == 400


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
        assert data["strict_overlap"]["stats"]["n"] <= min(s["stats"]["n"] for s in data["singles"])
        assert data["composite"]["stats"]["n"] <= data["pool_n"]  # composite ⊆ baseline


def test_factor_combination_scales_to_all_factors(loaded_engine):
    """The iter-18 'scales to all factors' requirement: a selection of ALL catalog factors (up to the
    raised max_conditions) is accepted (200) and the composite cohort is still NON-EMPTY — combining every
    factor no longer collapses the headline cohort to 0/NA (it stays the top config-quantile of the blend)."""
    cfg = load_config()
    all_factors = [f.key for f in cfg.research.factor_lab.factors]
    assert len(all_factors) == cfg.research.factor_lab.combination.max_conditions  # the cap == catalog count
    with TestClient(main.app) as client:
        resp = client.get(
            "/api/research/factor-combination",
            params=[("condition", f"{f}:top:quintile") for f in all_factors],
        )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["singles"]) == len(all_factors)
    assert data["composite"]["stats"]["n"] > 0           # composite stays non-empty across ALL factors
    assert data["composite"]["stats"]["n"] <= data["pool_n"]


def test_factor_combination_empty_strict_overlap_while_composite_populated(loaded_engine):
    """The headline improvement captured in ONE response: a selection whose strict AND-intersection is
    EMPTY (the opposing extremes of the SAME factor — membership-driven NA per the iter-11 lesson, not
    horizon) still returns a POPULATED composite cohort. strict_overlap = NA (n=0, mean None) while the
    composite is non-empty with a numeric mean — proving the composite is the real, sample-sufficient
    Combined cohort the strict intersection could not be."""
    with TestClient(main.app) as client:
        data = client.get(
            "/api/research/factor-combination",
            params=[
                ("condition", "leadership_score:top:quintile"),
                ("condition", "leadership_score:bottom:quintile"),
            ],
        ).json()
    # SECONDARY strict overlap: the empty AND-intersection -> honest NA + n=0
    assert data["strict_overlap"]["stats"]["n"] == 0
    assert data["strict_overlap"]["stats"]["mean_return"] is None
    # HEADLINE composite: populated where the strict overlap is empty
    assert data["composite"]["stats"]["n"] > 0
    assert data["composite"]["stats"]["mean_return"] is not None


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
    """A condition count above max_conditions (now 11 = the catalog factor count) is rejected (422) — no
    fabricated cohort. 12 conditions (all 11 catalog factors + one repeat) exceed the raised cap."""
    all_factors = [
        "leadership_score", "entry_quality_score", "risk_score", "rs_spy_3m", "ma_stack",
        "high_proximity", "up_down_vol", "atr_pct", "hv", "vcp_contraction", "downside_vol",
    ]
    twelve = all_factors + ["leadership_score"]  # 12 conditions > max_conditions 11
    with TestClient(main.app) as client:
        resp = client.get(
            "/api/research/factor-combination",
            params=[("condition", f"{f}:top:quintile") for f in twelve],
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


# ==================================================================================================
# GET /api/research/event-study — Setup & Pattern event study (iter-14, J-29)
# ==================================================================================================
def test_event_study_default_payload(loaded_engine):
    """J-29 at the API level: the default payload (first catalog subject = first setup + default horizon)
    carries the resolved subject, the config-driven subjects catalog (setups + patterns), one per-horizon
    row per configured horizon (full shape), the by-regime + by-sector slices, and the honest labels."""
    from app.engine.research import subject_catalog

    cfg = load_config()
    subjects = subject_catalog(cfg)
    with TestClient(main.app) as client:
        resp = client.get("/api/research/event-study")
    assert resp.status_code == 200
    data = resp.json()

    # default subject = first catalog subject (the first setup); default horizon = config default_horizon
    assert data["subject"]["key"] == subjects[0]["key"]
    assert data["horizon"] == cfg.walk_forward.default_horizon
    assert data["min_sample"] == cfg.walk_forward.min_sample

    # the subjects catalog is config-driven (the dropdown vocabulary) — exact match, in order
    assert [s["key"] for s in data["subjects"]] == [s["key"] for s in subjects]
    assert {"key", "label", "kind"} == set(data["subjects"][0])

    # one per-horizon row per configured horizon, each carrying the full event-study shape
    assert [r["horizon"] for r in data["by_horizon"]] == list(cfg.walk_forward.horizons)
    for r in data["by_horizon"]:
        assert {
            "horizon", "n", "low_sample", "mean_return", "median", "pct_positive", "dispersion",
            "expectancy", "mean_mae", "mean_mfe", "return_per_downside_dev", "return_per_mae",
        } <= set(r)
        assert {"win_rate", "avg_win", "avg_loss", "expectancy"} <= set(r["expectancy"])

    # by-regime: one row per configured regime label, in order; by-sector: present-only rows
    assert [r["regime"] for r in data["by_regime"]] == cfg.regime.labels
    for r in data["by_regime"]:
        assert {"regime", "n", "low_sample", "mean_return", "hit_rate", "risk_adjusted"} <= set(r)
    for r in data["by_sector"]:
        assert {"sector", "n", "low_sample", "mean_return", "risk_adjusted"} <= set(r)

    # best-exit-horizon is a configured horizon or NA; honest labels carried verbatim
    assert data["best_exit_horizon"] is None or data["best_exit_horizon"] in cfg.walk_forward.horizons
    assert "survivorship" in data["survivorship_bias"].lower()
    assert "not a predictive model" in data["descriptive_caveat"].lower()


def test_event_study_no_date_control_present(loaded_engine):
    """J-18 (iter-19 UPDATED contract — iter-2 lesson, not a regression): the event study accepts the
    SINGLE global `as_of` as an OPTIONAL point-in-time scoping cutoff (a mode, not a second date state).
    The default (all-history) payload echoes `asof_date: null`; a `?as_of=D` call echoes the resolved
    cutoff. There is NO second, independent date field — the only inputs are subject + the shared horizon
    + the single global as-of transmitted on the read."""
    with TestClient(main.app) as client:
        default = client.get("/api/research/event-study").json()
        oldest = _oldest_research_date(client)
        scoped = client.get(f"/api/research/event-study?as_of={oldest}").json()
    assert default["asof_date"] is None
    assert scoped["asof_date"] == oldest
    for data in (default, scoped):
        assert not any(k in data for k in ("asof_dates", "date", "is_latest"))


def test_event_study_as_of_scopes_pool_and_echoes_resolved_cutoff(loaded_engine):
    """J-32 at the API level: a historical `?as_of=D` scopes the event-study pool to snapshots dated <= D
    (a non-increasing expanding-window subset — n_total never grows toward the cutoff) and echoes the
    resolved `asof_date`; the default call is all-history with `asof_date` null. (The exact strict n-drop +
    no-future-leak through the horizon loop is proven on a controlled fixture in test_research.py.)"""
    with TestClient(main.app) as client:
        oldest = _oldest_research_date(client)
        all_history = client.get("/api/research/event-study?subject=vcp").json()
        scoped = client.get(f"/api/research/event-study?subject=vcp&as_of={oldest}").json()
    assert all_history["asof_date"] is None
    assert scoped["asof_date"] == oldest
    assert scoped["n_total"] <= all_history["n_total"]  # expanding window: oldest cutoff is a subset


def test_event_study_as_of_unparseable_422(loaded_engine):
    """An unparseable `?as_of=` is rejected 422 (shared validator) — never a fabricated window."""
    with TestClient(main.app) as client:
        assert client.get("/api/research/event-study?as_of=not-a-date").status_code == 422


def test_event_study_as_of_future_400(loaded_engine):
    """A future `?as_of=` (after the latest data date) is rejected 400 — never a fabricated forward window."""
    with TestClient(main.app) as client:
        assert client.get("/api/research/event-study?as_of=2999-01-01").status_code == 400


def test_event_study_changing_subject_repoints(loaded_engine):
    """Changing the subject re-points the analysis to a different stored cohort (server values, never a
    client recompute): a setup subject and a pattern subject resolve distinctly and their pooled by_horizon
    means differ (distinct populations)."""
    with TestClient(main.app) as client:
        actionable = client.get("/api/research/event-study", params={"subject": "Actionable"}).json()
        vcp = client.get("/api/research/event-study", params={"subject": "vcp"}).json()
    assert actionable["subject"]["key"] == "Actionable" and actionable["subject"]["kind"] == "setup"
    assert vcp["subject"]["key"] == "vcp" and vcp["subject"]["kind"] == "pattern"
    # distinct populations -> the per-horizon mean curves differ (a real re-point, not a relabel)
    a_means = [r["mean_return"] for r in actionable["by_horizon"]]
    v_means = [r["mean_return"] for r in vcp["by_horizon"]]
    assert a_means != v_means


def test_event_study_changing_horizon_repoints(loaded_engine):
    """Changing the shared horizon re-points the selected-horizon by-regime/by-sector slices — server
    values (assert the payload's horizon changes)."""
    with TestClient(main.app) as client:
        h20 = client.get("/api/research/event-study", params={"subject": "vcp", "horizon": 20}).json()
        h60 = client.get("/api/research/event-study", params={"subject": "vcp", "horizon": 60}).json()
    assert h20["horizon"] == 20 and h60["horizon"] == 60


def test_event_study_unknown_subject_422(loaded_engine):
    """An unknown subject is rejected (422) — no fabricated subject."""
    with TestClient(main.app) as client:
        resp = client.get("/api/research/event-study", params={"subject": "not_a_subject"})
    assert resp.status_code == 422


def test_event_study_invalid_horizon_422(loaded_engine):
    """An out-of-range horizon is rejected (422) — no fabricated horizon."""
    with TestClient(main.app) as client:
        resp = client.get("/api/research/event-study", params={"horizon": 7})
    assert resp.status_code == 422


def test_event_study_503_when_no_price_data(tmp_path):
    """No price data -> explicit 503 (never a fabricated event study). The handler is called directly
    against an empty DB session, leaving the process engine untouched."""
    from app.api.research import event_study

    engine = make_engine(f"sqlite:///{tmp_path / 'empty_es.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        assert latest_data_date(session) is None
        with pytest.raises(HTTPException) as exc:
            event_study(subject=None, horizon=None, session=session)
        assert exc.value.status_code == 503
