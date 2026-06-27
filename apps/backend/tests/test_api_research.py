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
# GET /api/research/factor-lab?all=true — the all-factors aggregate view (iter-50, J-107)
# ==================================================================================================
def test_factor_lab_all_payload_is_one_row_per_catalog_factor(loaded_engine):
    """J-107 → J-109 at the API level: `?all=true` returns a `factors_table` with exactly one entry per
    config catalog factor (in order), each carrying family + rank-IC (value + n) + the downside
    risk-adjusted figure (at the default horizon) + a `by_horizon` block with one decile table per config
    horizon (each decile pairing mean_return + mean_max_drawdown); the top-level block echoes the
    config-driven horizons / decile count / min_sample + the honest labels and carries NO single `horizon`.
    No single `factor` is resolved (the table shows every factor at every horizon)."""
    cfg = load_config()
    fl = cfg.research.factor_lab
    horizons = list(cfg.walk_forward.horizons)
    with TestClient(main.app) as client:
        resp = client.get("/api/research/factor-lab", params={"all": "true"})
    assert resp.status_code == 200
    data = resp.json()
    assert [e["key"] for e in data["factors_table"]] == [f.key for f in fl.factors]
    assert "horizon" not in data  # the all-horizons view has no single served horizon (J-109)
    assert data["horizons"] == horizons
    assert data["default_horizon"] == cfg.walk_forward.default_horizon
    assert data["deciles_count"] == fl.deciles
    assert data["min_sample"] == cfg.walk_forward.min_sample
    assert data["asof_date"] is None
    assert "survivorship" in data["survivorship_bias"].lower()
    for e in data["factors_table"]:
        assert {"key", "label", "family", "direction", "n_total", "rank_ic", "risk_adjusted", "by_horizon"} == set(e)
        assert {"value", "n"} == set(e["rank_ic"])
        assert [b["horizon"] for b in e["by_horizon"]] == horizons
        for b in e["by_horizon"]:
            assert {"horizon", "n_total", "deciles"} == set(b)
            assert len(b["deciles"]) == fl.deciles
            for d in b["deciles"]:
                assert "mean_max_drawdown" in d  # J-109 paired drawdown column


def test_factor_lab_all_is_byte_identical_to_single_factor_view(loaded_engine):
    """Single source of truth (J-25/J-06): each all-factors entry's per-horizon deciles are byte-identical to
    the SINGLE-factor `?factor=&horizon=` view for the same factor/horizon, and its default-horizon rank-IC /
    risk-adjusted match the single-factor default view — proving the all-horizons view re-presents the
    canonical compute_factor_lab outputs (one computation path), not a second derivation."""
    import json

    cfg = load_config()
    horizons = list(cfg.walk_forward.horizons)
    default_h = cfg.walk_forward.default_horizon
    with TestClient(main.app) as client:
        allp = client.get("/api/research/factor-lab", params={"all": "true"}).json()
        table = {e["key"]: e for e in allp["factors_table"]}
        for f in cfg.research.factor_lab.factors:
            entry = table[f.key]
            by_h = {b["horizon"]: b for b in entry["by_horizon"]}
            for h in horizons:
                single = client.get(
                    "/api/research/factor-lab", params={"factor": f.key, "horizon": h}
                ).json()
                assert json.dumps(by_h[h]["deciles"], sort_keys=True) == json.dumps(
                    single["deciles"], sort_keys=True
                ), f"deciles drift {f.key}@{h}"
            single_dh = client.get(
                "/api/research/factor-lab", params={"factor": f.key, "horizon": default_h}
            ).json()
            assert json.dumps(entry["rank_ic"], sort_keys=True) == json.dumps(
                single_dh["rank_ic"], sort_keys=True
            )
            assert entry["risk_adjusted"] == single_dh["deciles"][-1]["risk_adjusted"]


def test_factor_lab_all_as_of_scopes_pool_and_echoes_cutoff(loaded_engine):
    """J-32: `?all=true&as_of=D` scopes every factor's pool to snapshots dated <= D (strictly fewer
    observations than all-history) and echoes the resolved cutoff — the single global as-of, a mode not a
    second date state (J-18)."""
    with TestClient(main.app) as client:
        oldest = _oldest_research_date(client)
        all_history = client.get("/api/research/factor-lab", params={"all": "true"}).json()
        scoped = client.get("/api/research/factor-lab", params={"all": "true", "as_of": oldest}).json()
    assert all_history["asof_date"] is None
    assert scoped["asof_date"] == oldest
    lead_all = next(e for e in all_history["factors_table"] if e["key"] == "leadership_score")["n_total"]
    lead_scoped = next(e for e in scoped["factors_table"] if e["key"] == "leadership_score")["n_total"]
    assert 0 < lead_scoped < lead_all  # the oldest cutoff pools strictly fewer, not empty


def test_factor_lab_all_invalid_horizon_422(loaded_engine):
    """An out-of-range horizon is rejected (422) on the all-factors path too — no fabricated horizon."""
    with TestClient(main.app) as client:
        assert client.get("/api/research/factor-lab", params={"all": "true", "horizon": 7}).status_code == 422


# ==================================================================================================
# GET /api/research/regime-lab — the Regime Lab all-horizons view (iter-53, J-110)
# ==================================================================================================
def test_regime_lab_payload_shape_and_config_driven_buckets(loaded_engine):
    """J-110 at the API level: the payload carries a `by_label` table (one row per config regime label, in
    order), a `by_decile` table (D1..D`deciles`), and a `rank_ic_by_horizon` block, each row carrying a
    `by_horizon` list with paired (mean_return, mean_max_drawdown) per config horizon + n. It echoes the
    config-driven horizons / decile count / min_sample / regime-label vocabulary + the honest labels and
    carries NO single `horizon` (all horizons at once)."""
    cfg = load_config()
    fl = cfg.research.factor_lab
    horizons = list(cfg.walk_forward.horizons)
    with TestClient(main.app) as client:
        resp = client.get("/api/research/regime-lab")
    assert resp.status_code == 200
    data = resp.json()
    assert "horizon" not in data  # the all-horizons view has no single served horizon
    assert data["view"] == "episodes"  # the default overlap-honesty view
    assert data["horizons"] == horizons
    assert data["default_horizon"] == cfg.walk_forward.default_horizon
    assert data["deciles_count"] == fl.deciles
    assert data["min_sample"] == cfg.walk_forward.min_sample
    assert data["regime_labels"] == list(cfg.regime.labels)
    assert data["asof_date"] is None
    assert "survivorship" in data["survivorship_bias"].lower()
    assert [r["regime"] for r in data["by_label"]] == list(cfg.regime.labels)
    assert [r["decile"] for r in data["by_decile"]] == list(range(1, fl.deciles + 1))
    assert [r["horizon"] for r in data["rank_ic_by_horizon"]] == horizons
    for r in data["by_label"]:
        assert [b["horizon"] for b in r["by_horizon"]] == horizons
        for b in r["by_horizon"]:
            assert {"horizon", "n", "low_sample", "mean_return", "mean_max_drawdown"} == set(b)
    for r in data["by_decile"]:
        for b in r["by_horizon"]:
            assert {"horizon", "n", "low_sample", "mean_return", "mean_max_drawdown",
                    "score_min", "score_max"} == set(b)


def test_regime_lab_no_date_control_present(loaded_engine):
    """The Regime-Lab payload exposes no second/page-local date control — the only date state is the single
    global as-of echoed as `asof_date` (J-18). The default (omitted) call is all-history."""
    with TestClient(main.app) as client:
        data = client.get("/api/research/regime-lab").json()
    assert data["asof_date"] is None
    # no nested 'date'/'asof' selector field beyond the single echoed cutoff.
    assert "horizon" not in data


def test_regime_lab_pooled_view_differs_and_is_byte_identical_to_engine(loaded_engine):
    """`?view=pooled` serves the per-signal-day pool (a DIFFERENT, larger observation set than the default
    episodes collapse) and is byte-identical to the engine's `regime_lab_cached(view='pooled')` — the API
    serves the canonical aggregate verbatim, never recomputed."""
    import json as _json

    from app.engine.research import regime_lab_cached

    cfg = load_config()
    with TestClient(main.app) as client:
        episodes = client.get("/api/research/regime-lab", params={"view": "episodes"}).json()
        pooled = client.get("/api/research/regime-lab", params={"view": "pooled"}).json()
    assert episodes["view"] == "episodes" and pooled["view"] == "pooled"
    # pooled keeps strictly more observations than the first-trigger episode collapse at the default horizon.
    dh = cfg.walk_forward.default_horizon

    def _total(payload):
        return sum(
            b["n"] for r in payload["by_label"] for b in r["by_horizon"] if b["horizon"] == dh
        )

    assert _total(pooled) > _total(episodes) > 0
    with Session(loaded_engine) as session:
        engine_pooled = regime_lab_cached(session, cfg, view="pooled")
    assert _json.dumps(pooled, sort_keys=True) == _json.dumps(engine_pooled, sort_keys=True)


def test_regime_lab_as_of_scopes_pool_and_echoes_cutoff(loaded_engine):
    """J-32: `?as_of=D` scopes the observation set to snapshots dated <= D (strictly fewer observations than
    all-history) and echoes the resolved cutoff — the single global as-of, a mode not a second date state."""
    cfg = load_config()
    dh = cfg.walk_forward.default_horizon

    def _total(payload):
        return sum(b["n"] for r in payload["by_label"] for b in r["by_horizon"] if b["horizon"] == dh)

    with TestClient(main.app) as client:
        oldest = _oldest_research_date(client)
        all_history = client.get("/api/research/regime-lab").json()
        scoped = client.get("/api/research/regime-lab", params={"as_of": oldest}).json()
    assert all_history["asof_date"] is None
    assert scoped["asof_date"] == oldest
    assert 0 < _total(scoped) < _total(all_history)  # the oldest cutoff pools strictly fewer, not empty


def test_regime_lab_invalid_view_422(loaded_engine):
    """An unknown view is rejected (422) — no fabricated view (mirrors the event-study handler)."""
    with TestClient(main.app) as client:
        assert client.get("/api/research/regime-lab", params={"view": "nope"}).status_code == 422


def test_regime_lab_samples_count_coherent_over_http(loaded_engine):
    """J-51/J-65 over HTTP: a Regime-Lab `N=` chip's samples drill-down `total` equals the published bucket n
    for both a regime LABEL and a regime-score DECILE, in the SAME view — and every displayable bucket
    resolves (200), never a 4xx."""
    cfg = load_config()
    dh = cfg.walk_forward.default_horizon
    with TestClient(main.app) as client:
        data = client.get("/api/research/regime-lab", params={"view": "pooled"}).json()
        # a populated label bucket at the default horizon.
        label_row = next(
            r for r in data["by_label"]
            if next(b for b in r["by_horizon"] if b["horizon"] == dh)["n"] > 0
        )
        label_n = next(b for b in label_row["by_horizon"] if b["horizon"] == dh)["n"]
        s = client.get("/api/research/samples", params={
            "kind": "regime-lab", "slice": "label", "regime": label_row["regime"],
            "horizon": dh, "view": "pooled",
        })
        assert s.status_code == 200
        assert s.json()["total"] == label_n

        # a populated decile bucket at the default horizon.
        decile_row = next(
            r for r in data["by_decile"]
            if next(b for b in r["by_horizon"] if b["horizon"] == dh)["n"] > 0
        )
        decile_n = next(b for b in decile_row["by_horizon"] if b["horizon"] == dh)["n"]
        s2 = client.get("/api/research/samples", params={
            "kind": "regime-lab", "slice": "decile", "decile": decile_row["decile"],
            "horizon": dh, "view": "pooled",
        })
        assert s2.status_code == 200
        assert s2.json()["total"] == decile_n


def test_regime_lab_samples_invalid_selectors_4xx(loaded_engine):
    """An unknown regime label / out-of-range decile / unknown view on the regime-lab samples kind is an
    explicit 4xx (never a silent empty 200)."""
    with TestClient(main.app) as client:
        assert client.get("/api/research/samples", params={
            "kind": "regime-lab", "slice": "label", "regime": "Not-a-regime", "horizon": 20,
        }).status_code == 422
        assert client.get("/api/research/samples", params={
            "kind": "regime-lab", "slice": "decile", "decile": 0, "horizon": 20,
        }).status_code == 422
        assert client.get("/api/research/samples", params={
            "kind": "regime-lab", "slice": "label", "regime": "Risk-on", "horizon": 20, "view": "nope",
        }).status_code == 422


# ==================================================================================================
# GET /api/research/phase-severity-lab — the Market Phase & Severity Lab all-horizons view (iter-54, J-111)
# ==================================================================================================
def test_phase_severity_lab_payload_shape_and_config_driven_buckets(loaded_engine):
    """J-111 at the API level: the payload carries a `by_label` table (one row per config market-phase label,
    in order), a `by_decile` table (D1..D`deciles`), and a `rank_ic_by_horizon` block, each row carrying a
    `by_horizon` list with paired (mean_return, mean_max_drawdown) per config horizon + n. It echoes the
    config-driven horizons / decile count / min_sample / phase-label vocabulary + the honest labels and
    carries NO single `horizon` (all horizons at once)."""
    cfg = load_config()
    fl = cfg.research.factor_lab
    horizons = list(cfg.walk_forward.horizons)
    with TestClient(main.app) as client:
        resp = client.get("/api/research/phase-severity-lab")
    assert resp.status_code == 200
    data = resp.json()
    assert "horizon" not in data  # the all-horizons view has no single served horizon
    assert data["view"] == "episodes"  # the default overlap-honesty view
    assert data["horizons"] == horizons
    assert data["default_horizon"] == cfg.walk_forward.default_horizon
    assert data["deciles_count"] == fl.deciles
    assert data["min_sample"] == cfg.walk_forward.min_sample
    assert data["phase_labels"] == list(cfg.market_phase.labels)
    assert data["asof_date"] is None
    assert "survivorship" in data["survivorship_bias"].lower()
    assert [r["phase"] for r in data["by_label"]] == list(cfg.market_phase.labels)
    assert [r["decile"] for r in data["by_decile"]] == list(range(1, fl.deciles + 1))
    assert [r["horizon"] for r in data["rank_ic_by_horizon"]] == horizons
    for r in data["by_label"]:
        assert [b["horizon"] for b in r["by_horizon"]] == horizons
        for b in r["by_horizon"]:
            assert {"horizon", "n", "low_sample", "mean_return", "mean_max_drawdown"} == set(b)
    for r in data["by_decile"]:
        for b in r["by_horizon"]:
            assert {"horizon", "n", "low_sample", "mean_return", "mean_max_drawdown",
                    "score_min", "score_max"} == set(b)


def test_phase_severity_lab_no_date_control_present(loaded_engine):
    """The Phase & Severity-Lab payload exposes no second/page-local date control — the only date state is the
    single global as-of echoed as `asof_date` (J-18). The default (omitted) call is all-history."""
    with TestClient(main.app) as client:
        data = client.get("/api/research/phase-severity-lab").json()
    assert data["asof_date"] is None
    assert "horizon" not in data


def test_phase_severity_lab_pooled_view_differs_and_is_byte_identical_to_engine(loaded_engine):
    """`?view=pooled` serves the per-signal-day pool (a DIFFERENT, larger observation set than the default
    episodes collapse) and is byte-identical to the engine's `phase_severity_lab_cached(view='pooled')` — the
    API serves the canonical aggregate verbatim, never recomputed."""
    import json as _json

    from app.engine.research import phase_severity_lab_cached

    cfg = load_config()
    with TestClient(main.app) as client:
        episodes = client.get("/api/research/phase-severity-lab", params={"view": "episodes"}).json()
        pooled = client.get("/api/research/phase-severity-lab", params={"view": "pooled"}).json()
    assert episodes["view"] == "episodes" and pooled["view"] == "pooled"
    dh = cfg.walk_forward.default_horizon

    def _total(payload):
        return sum(b["n"] for r in payload["by_label"] for b in r["by_horizon"] if b["horizon"] == dh)

    assert _total(pooled) > _total(episodes) > 0
    with Session(loaded_engine) as session:
        engine_pooled = phase_severity_lab_cached(session, cfg, view="pooled")
    assert _json.dumps(pooled, sort_keys=True) == _json.dumps(engine_pooled, sort_keys=True)


def test_phase_severity_lab_as_of_scopes_pool_and_echoes_cutoff(loaded_engine):
    """J-32: `?as_of=D` scopes the observation set to snapshots dated <= D (strictly fewer observations than
    all-history) and echoes the resolved cutoff — the single global as-of, a mode not a second date state."""
    cfg = load_config()
    dh = cfg.walk_forward.default_horizon

    def _total(payload):
        return sum(b["n"] for r in payload["by_label"] for b in r["by_horizon"] if b["horizon"] == dh)

    with TestClient(main.app) as client:
        oldest = _oldest_research_date(client)
        all_history = client.get("/api/research/phase-severity-lab").json()
        scoped = client.get("/api/research/phase-severity-lab", params={"as_of": oldest}).json()
    assert all_history["asof_date"] is None
    assert scoped["asof_date"] == oldest
    assert 0 < _total(scoped) < _total(all_history)  # the oldest cutoff pools strictly fewer, not empty


def test_phase_severity_lab_invalid_view_422(loaded_engine):
    """An unknown view is rejected (422) — no fabricated view (mirrors the regime-lab handler)."""
    with TestClient(main.app) as client:
        assert client.get("/api/research/phase-severity-lab", params={"view": "nope"}).status_code == 422


def test_phase_severity_lab_samples_count_coherent_over_http(loaded_engine):
    """J-51/J-65 over HTTP: a Phase & Severity-Lab `N=` chip's samples drill-down `total` equals the published
    bucket n for both a market-phase LABEL and a severity-score DECILE, in the SAME view — and every
    displayable bucket resolves (200), never a 4xx."""
    cfg = load_config()
    dh = cfg.walk_forward.default_horizon
    with TestClient(main.app) as client:
        data = client.get("/api/research/phase-severity-lab", params={"view": "pooled"}).json()
        # a populated label bucket at the default horizon.
        label_row = next(
            r for r in data["by_label"]
            if next(b for b in r["by_horizon"] if b["horizon"] == dh)["n"] > 0
        )
        label_n = next(b for b in label_row["by_horizon"] if b["horizon"] == dh)["n"]
        s = client.get("/api/research/samples", params={
            "kind": "phase-severity-lab", "slice": "label", "phase": label_row["phase"],
            "horizon": dh, "view": "pooled",
        })
        assert s.status_code == 200
        assert s.json()["total"] == label_n

        # a populated decile bucket at the default horizon.
        decile_row = next(
            r for r in data["by_decile"]
            if next(b for b in r["by_horizon"] if b["horizon"] == dh)["n"] > 0
        )
        decile_n = next(b for b in decile_row["by_horizon"] if b["horizon"] == dh)["n"]
        s2 = client.get("/api/research/samples", params={
            "kind": "phase-severity-lab", "slice": "decile", "decile": decile_row["decile"],
            "horizon": dh, "view": "pooled",
        })
        assert s2.status_code == 200
        assert s2.json()["total"] == decile_n


def test_phase_severity_lab_samples_invalid_selectors_4xx(loaded_engine):
    """An unknown phase label / out-of-range decile / unknown view on the phase-severity-lab samples kind is an
    explicit 4xx (never a silent empty 200)."""
    with TestClient(main.app) as client:
        assert client.get("/api/research/samples", params={
            "kind": "phase-severity-lab", "slice": "label", "phase": "Not-a-phase", "horizon": 20,
        }).status_code == 422
        assert client.get("/api/research/samples", params={
            "kind": "phase-severity-lab", "slice": "decile", "decile": 0, "horizon": 20,
        }).status_code == 422
        assert client.get("/api/research/samples", params={
            "kind": "phase-severity-lab", "slice": "label", "phase": "Expansion", "horizon": 20, "view": "nope",
        }).status_code == 422


# ==================================================================================================
# GET /api/research/regime-phase-factor — the Regime × Phase × Factor 3-way decile study (iter-55, J-112)
# ==================================================================================================
def test_regime_phase_factor_payload_shape_and_config_driven(loaded_engine):
    """J-112 at the API level: the payload carries a ranked `rows` table of `(regime_decile, severity_decile,
    factor_decile)` combinations, each with a `by_horizon` list of paired (mean_return, mean_max_drawdown) + n
    per config horizon, plus the config-driven factor catalog + selected factor + page_size + honest labels, and
    carries NO single `horizon` (all horizons at once)."""
    cfg = load_config()
    fl = cfg.research.factor_lab
    horizons = list(cfg.walk_forward.horizons)
    with TestClient(main.app) as client:
        resp = client.get("/api/research/regime-phase-factor")
    assert resp.status_code == 200
    data = resp.json()
    assert "horizon" not in data  # the all-horizons view has no single served horizon
    assert data["view"] == "episodes"  # the default overlap-honesty view
    assert data["horizons"] == horizons
    assert data["default_horizon"] == cfg.walk_forward.default_horizon
    assert data["deciles_count"] == fl.deciles
    assert data["min_sample"] == cfg.walk_forward.min_sample
    assert data["page_size"] == cfg.research.regime_phase_factor_page_size
    assert data["factor"]["key"] == fl.factors[0].key  # defaults to the first catalog factor
    assert [f["key"] for f in data["factors"]] == [f.key for f in fl.factors]
    assert data["asof_date"] is None
    assert "survivorship" in data["survivorship_bias"].lower()
    assert data["rows"], "no combination rows on the real seed"
    for r in data["rows"]:
        assert set(r) == {"regime_decile", "severity_decile", "factor_decile", "by_horizon"}
        for k in ("regime_decile", "severity_decile", "factor_decile"):
            assert 1 <= r[k] <= fl.deciles
        assert [b["horizon"] for b in r["by_horizon"]] == horizons
        for b in r["by_horizon"]:
            assert {"horizon", "n", "low_sample", "mean_return", "mean_max_drawdown"} == set(b)


def test_regime_phase_factor_factor_switch_changes_table(loaded_engine):
    """Changing the `factor` param re-partitions the factor-decile dimension and serves a DISTINCT table (the
    `factor` selector really drives the study)."""
    cfg = load_config()
    keys = [f.key for f in cfg.research.factor_lab.factors]
    with TestClient(main.app) as client:
        a = client.get("/api/research/regime-phase-factor", params={"factor": keys[0]}).json()
        b = client.get("/api/research/regime-phase-factor", params={"factor": keys[1]}).json()
    assert a["factor"]["key"] == keys[0] and b["factor"]["key"] == keys[1]
    import json as _json
    assert _json.dumps(a["rows"], sort_keys=True) != _json.dumps(b["rows"], sort_keys=True)


def test_regime_phase_factor_pooled_byte_identical_to_engine(loaded_engine):
    """`?view=pooled` is byte-identical to the engine's `regime_phase_factor_cached(view='pooled')` — the API
    serves the canonical aggregate verbatim, never recomputed."""
    import json as _json

    from app.engine.research import regime_phase_factor_cached

    cfg = load_config()
    factor = cfg.research.factor_lab.factors[0].key
    with TestClient(main.app) as client:
        pooled = client.get(
            "/api/research/regime-phase-factor", params={"factor": factor, "view": "pooled"}
        ).json()
    with Session(loaded_engine) as session:
        engine_pooled = regime_phase_factor_cached(session, cfg, factor=factor, view="pooled")
    assert _json.dumps(pooled, sort_keys=True) == _json.dumps(engine_pooled, sort_keys=True)


def test_regime_phase_factor_as_of_scopes_and_echoes(loaded_engine):
    """J-32: `?as_of=D` scopes the observation set to snapshots dated <= D (strictly fewer total observations
    than all-history) and echoes the resolved cutoff — a mode, not a second date state."""
    cfg = load_config()
    dh = cfg.walk_forward.default_horizon

    def _total(payload):
        return sum(b["n"] for r in payload["rows"] for b in r["by_horizon"] if b["horizon"] == dh)

    with TestClient(main.app) as client:
        oldest = _oldest_research_date(client)
        all_history = client.get("/api/research/regime-phase-factor", params={"view": "pooled"}).json()
        scoped = client.get(
            "/api/research/regime-phase-factor", params={"view": "pooled", "as_of": oldest}
        ).json()
    assert all_history["asof_date"] is None
    assert scoped["asof_date"] == oldest
    assert 0 < _total(scoped) < _total(all_history)  # the oldest cutoff pools strictly fewer, not empty


def test_regime_phase_factor_invalid_factor_and_view_422(loaded_engine):
    """An unknown factor or unknown view is rejected (422) — no fabricated input (mirrors the sibling handlers)."""
    with TestClient(main.app) as client:
        assert client.get(
            "/api/research/regime-phase-factor", params={"factor": "not_a_factor"}
        ).status_code == 422
        assert client.get(
            "/api/research/regime-phase-factor", params={"view": "nope"}
        ).status_code == 422


def test_regime_phase_factor_samples_count_coherent_over_http(loaded_engine):
    """J-51/J-65 over HTTP: a Regime × Phase × Factor `N=` chip's samples drill-down `total` equals the
    published combination n for the exact triple+horizon, in the SAME pinned-pooled view — and the chip
    resolves (200), never a 4xx."""
    cfg = load_config()
    dh = cfg.walk_forward.default_horizon
    factor = cfg.research.factor_lab.factors[0].key
    with TestClient(main.app) as client:
        data = client.get(
            "/api/research/regime-phase-factor", params={"factor": factor, "view": "pooled"}
        ).json()
        # a populated combination at the default horizon.
        row = next(
            r for r in data["rows"]
            if next(b for b in r["by_horizon"] if b["horizon"] == dh)["n"] > 0
        )
        n = next(b for b in row["by_horizon"] if b["horizon"] == dh)["n"]
        s = client.get("/api/research/samples", params={
            "kind": "regime-phase-factor", "factor": factor,
            "regime_decile": row["regime_decile"], "severity_decile": row["severity_decile"],
            "factor_decile": row["factor_decile"], "horizon": dh, "view": "pooled",
        })
        assert s.status_code == 200
        assert s.json()["total"] == n


def test_regime_phase_factor_samples_invalid_selectors_4xx(loaded_engine):
    """An unknown factor / out-of-range decile / unknown view on the regime-phase-factor samples kind is an
    explicit 4xx (never a silent empty 200)."""
    factor = load_config().research.factor_lab.factors[0].key
    with TestClient(main.app) as client:
        assert client.get("/api/research/samples", params={
            "kind": "regime-phase-factor", "factor": "not_a_factor",
            "regime_decile": 1, "severity_decile": 1, "factor_decile": 1, "horizon": 20, "view": "pooled",
        }).status_code == 422
        assert client.get("/api/research/samples", params={
            "kind": "regime-phase-factor", "factor": factor,
            "regime_decile": 0, "severity_decile": 1, "factor_decile": 1, "horizon": 20, "view": "pooled",
        }).status_code == 422
        assert client.get("/api/research/samples", params={
            "kind": "regime-phase-factor", "factor": factor,
            "regime_decile": 1, "severity_decile": 1, "factor_decile": 1, "horizon": 20, "view": "nope",
        }).status_code == 422


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


# ==================================================================================================
# GET /api/research/samples — the J-51 / J-52 drill-down (count-coherence at the API level)
# ==================================================================================================
def test_samples_factor_total_coherence(loaded_engine):
    """J-51 at the API level: the samples `total` for a factor's `n_total` chip EQUALS the published
    factor-lab `n_total`; each row carries ticker, snapshot date, the stored factor value, and the
    realized forward return."""
    with TestClient(main.app) as client:
        agg = client.get("/api/research/factor-lab", params={"factor": "leadership_score", "horizon": 20}).json()
        s = client.get(
            "/api/research/samples",
            params={"kind": "factor", "factor": "leadership_score", "horizon": 20, "slice": "total"},
        ).json()
    assert s["total"] == agg["n_total"]
    assert len(s["rows"]) == agg["n_total"]
    row = s["rows"][0]
    assert set(row) >= {"ticker", "snapshot_date", "values", "forward_return"}
    assert row["values"][0]["key"] == "leadership_score"
    # honest labels ride the payload (survivorship + descriptive)
    assert "survivorship" in s["survivorship_bias"].lower()


def test_samples_factor_every_decile_coherence(loaded_engine):
    """For EVERY published decile chip the samples total equals that decile's `n` — and the deciles'
    member counts sum to `n_total` (no double-count, no drop)."""
    with TestClient(main.app) as client:
        agg = client.get("/api/research/factor-lab", params={"factor": "leadership_score", "horizon": 20}).json()
        running = 0
        for d in agg["deciles"]:
            s = client.get(
                "/api/research/samples",
                params={"kind": "factor", "factor": "leadership_score", "horizon": 20,
                        "slice": "decile", "decile": d["decile"]},
            ).json()
            assert s["total"] == d["n"], f"decile {d['decile']}"
            running += s["total"]
    assert running == agg["n_total"]


def test_samples_factor_by_regime_coherence(loaded_engine):
    """Each by-regime chip's samples total equals that regime's published `n`."""
    with TestClient(main.app) as client:
        agg = client.get("/api/research/factor-lab", params={"factor": "leadership_score", "horizon": 20}).json()
        for r in agg["by_regime"]:
            s = client.get(
                "/api/research/samples",
                params={"kind": "factor", "factor": "leadership_score", "horizon": 20,
                        "slice": "regime", "regime": r["regime"]},
            ).json()
            assert s["total"] == r["n"], f"regime {r['regime']}"


def test_samples_combination_coherence_all_cohorts(loaded_engine):
    """Every combination chip (baseline / each single / composite / strict-overlap) has a samples total
    equal to the aggregate's published n — under the config default conditions."""
    with TestClient(main.app) as client:
        agg = client.get("/api/research/factor-combination", params={"horizon": 20}).json()
        conds = [f"{c['factor']['key']}:{c['side']}:{c['quantile']['key']}" for c in agg["conditions"]]
        base = client.get(
            "/api/research/samples",
            params=[("kind", "combination"), ("horizon", "20"), ("cohort", "baseline"),
                    *[("condition", c) for c in conds]],
        ).json()
        assert base["total"] == agg["pool_n"]
        for idx, single in enumerate(agg["singles"]):
            s = client.get(
                "/api/research/samples",
                params=[("kind", "combination"), ("horizon", "20"), ("cohort", "single"),
                        ("single_index", str(idx)), *[("condition", c) for c in conds]],
            ).json()
            assert s["total"] == single["stats"]["n"], f"single {idx}"
        comp = client.get(
            "/api/research/samples",
            params=[("kind", "combination"), ("horizon", "20"), ("cohort", "composite"),
                    *[("condition", c) for c in conds]],
        ).json()
        assert comp["total"] == agg["composite"]["stats"]["n"]
        strict = client.get(
            "/api/research/samples",
            params=[("kind", "combination"), ("horizon", "20"), ("cohort", "strict_overlap"),
                    *[("condition", c) for c in conds]],
        ).json()
        assert strict["total"] == agg["strict_overlap"]["stats"]["n"]


def test_samples_event_study_coherence(loaded_engine):
    """The pooled event-study chip's samples total equals `compute_event_study.n_total` for a subject."""
    with TestClient(main.app) as client:
        agg = client.get("/api/research/event-study", params={"subject": "vcp", "horizon": 20}).json()
        s = client.get(
            "/api/research/samples",
            params={"kind": "event-study", "subject": "vcp", "horizon": 20, "slice": "pooled"},
        ).json()
    assert s["total"] == agg["n_total"]
    assert all(r["values"][0]["key"] == "vcp" for r in s["rows"])


def test_samples_as_of_scopes_and_echoes(loaded_engine):
    """J-32 at the API level: a `?as_of=D` scopes the samples pool to snapshots dated <= D and echoes the
    resolved `asof_date`; the total matches the as-of-scoped factor-lab n_total (strictly fewer than
    all-history, not empty)."""
    with TestClient(main.app) as client:
        oldest = _oldest_research_date(client)
        all_s = client.get(
            "/api/research/samples",
            params={"kind": "factor", "factor": "leadership_score", "horizon": 20, "slice": "total"},
        ).json()
        scoped_agg = client.get(
            "/api/research/factor-lab",
            params={"factor": "leadership_score", "horizon": 20, "as_of": oldest},
        ).json()
        scoped = client.get(
            "/api/research/samples",
            params={"kind": "factor", "factor": "leadership_score", "horizon": 20,
                    "slice": "total", "as_of": oldest},
        ).json()
    assert all_s["asof_date"] is None
    assert scoped["asof_date"] == oldest
    assert scoped["total"] == scoped_agg["n_total"]
    assert 0 < scoped["total"] < all_s["total"]
    assert all(r["snapshot_date"] <= oldest for r in scoped["rows"])


def test_samples_invalid_selectors_are_4xx(loaded_engine):
    """Invalid cohort selectors are explicit 4xx (never a silent empty 200, which is reserved for a valid
    n=0): unknown kind / factor / subject, out-of-range decile, bad horizon, malformed condition."""
    with TestClient(main.app) as client:
        assert client.get("/api/research/samples", params={"kind": "nope"}).status_code == 422
        assert client.get(
            "/api/research/samples",
            params={"kind": "factor", "factor": "not_a_factor", "slice": "total"},
        ).status_code == 422
        assert client.get(
            "/api/research/samples",
            params={"kind": "factor", "factor": "leadership_score", "slice": "decile", "decile": 999},
        ).status_code == 422
        assert client.get(
            "/api/research/samples",
            params={"kind": "event-study", "subject": "not_a_subject", "slice": "pooled"},
        ).status_code == 422
        assert client.get(
            "/api/research/samples",
            params={"kind": "factor", "factor": "leadership_score", "horizon": 7, "slice": "total"},
        ).status_code == 422
        assert client.get(
            "/api/research/samples",
            params=[("kind", "combination"), ("condition", "leadership_score:top")],
        ).status_code == 422


def test_samples_strict_overlap_zero_is_empty_200(loaded_engine):
    """A VALID n=0 cohort (opposing extremes of the SAME factor → empty strict overlap) is an empty 200
    (rows == [], total == 0) — never a fabricated row, and explicitly NOT a 4xx (4xx is for invalid
    selectors). Coherence holds: the published strict-overlap n is also 0."""
    cfg = load_config()
    q = cfg.research.factor_lab.combination.quantiles[0].key
    conds = [f"leadership_score:top:{q}", f"leadership_score:bottom:{q}"]
    with TestClient(main.app) as client:
        agg = client.get(
            "/api/research/factor-combination",
            params=[("horizon", "20"), *[("condition", c) for c in conds]],
        ).json()
        resp = client.get(
            "/api/research/samples",
            params=[("kind", "combination"), ("horizon", "20"), ("cohort", "strict_overlap"),
                    *[("condition", c) for c in conds]],
        )
    assert agg["strict_overlap"]["stats"]["n"] == 0
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0 and data["rows"] == []


def test_samples_503_when_no_price_data(tmp_path):
    """No price data -> explicit 503 (never a fabricated drill-down). The handler is called directly
    against an empty DB session, leaving the process engine untouched."""
    from app.api.research import research_samples

    engine = make_engine(f"sqlite:///{tmp_path / 'empty_samples.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        assert latest_data_date(session) is None
        with pytest.raises(HTTPException) as exc:
            research_samples(kind="factor", session=session)
        assert exc.value.status_code == 503


# ==================================================================================================
# J-63 — Event-study overlap-honesty (Episodes default ⇄ Pooled) at the API level: default-episodes,
# the three disclosure values, byte-identity of the pooled view, count-coherence in BOTH modes, 422 on
# a bad `view` on BOTH endpoints.
# ==================================================================================================
def test_event_study_default_view_is_episodes_with_disclosure_values(loaded_engine):
    """The event-study default `view` is `episodes`, and BOTH the episodes and pooled payloads carry the
    three disclosure values (`n`, `unique_symbols`, `episode_count`). `episode_count` is IDENTICAL in both
    views (it counts first-trigger episodes regardless of which view renders); `n` is mode-dependent and
    episodes `n` <= pooled `n` (the overlap-honest collapse never inflates)."""
    with TestClient(main.app) as client:
        default = client.get("/api/research/event-study", params={"subject": "vcp", "horizon": 20}).json()
        episodes = client.get(
            "/api/research/event-study",
            params={"subject": "vcp", "horizon": 20, "view": "episodes"},
        ).json()
        pooled = client.get(
            "/api/research/event-study",
            params={"subject": "vcp", "horizon": 20, "view": "pooled"},
        ).json()
    assert default["view"] == "episodes" and default == episodes  # default IS episodes
    for data in (episodes, pooled):
        assert {"n", "unique_symbols", "episode_count"} <= set(data)
        assert data["n"] == data["n_total"]
    assert episodes["episode_count"] == pooled["episode_count"]   # view-independent
    assert episodes["n"] <= pooled["n"]                            # episodes never inflates
    assert episodes["n"] == episodes["episode_count"]             # episodes n == episode count
    assert pooled["unique_symbols"] <= pooled["n"]


def test_event_study_pooled_view_byte_identical_to_prior_published(loaded_engine):
    """BYTE-IDENTITY at the API (the hard J-63 guard): `?view=pooled` reproduces the PRE-J-63 published
    figures exactly for the PRE-EXISTING payload keys. The reference is the same payload with the additive
    J-63 keys removed (`view`/`n`/`unique_symbols`/`episode_count`) — proving the pooled branch routes
    through the unchanged computation (the only delta is additive keys)."""
    additive = {"view", "n", "unique_symbols", "episode_count"}
    with TestClient(main.app) as client:
        pooled = client.get(
            "/api/research/event-study",
            params={"subject": "vcp", "horizon": 20, "view": "pooled"},
        ).json()
    pooled_prior = {k: v for k, v in pooled.items() if k not in additive}
    # every pre-existing key+value is preserved (the by-horizon / by-regime / by-sector aggregates etc.)
    assert "by_horizon" in pooled_prior and "by_regime" in pooled_prior and "by_sector" in pooled_prior
    assert pooled_prior["n_total"] == pooled["n"]  # the pooled n_total is unchanged from before


def test_event_study_unknown_view_422(loaded_engine):
    """An unknown `view` is rejected (422) on the event-study endpoint — same pattern as subject/horizon."""
    with TestClient(main.app) as client:
        resp = client.get("/api/research/event-study", params={"subject": "vcp", "view": "weekly"})
    assert resp.status_code == 422


def test_samples_event_study_count_coherence_both_views(loaded_engine):
    """Count-coherence in BOTH modes at the API (J-63 + J-51): the samples pooled total equals the
    event-study `n` for the SAME subject+horizon under each `view` — asserted SAME-INSTANT against the live
    aggregate (never a hardcoded N)."""
    with TestClient(main.app) as client:
        for view in ("episodes", "pooled"):
            agg = client.get(
                "/api/research/event-study",
                params={"subject": "vcp", "horizon": 20, "view": view},
            ).json()
            s = client.get(
                "/api/research/samples",
                params={"kind": "event-study", "subject": "vcp", "horizon": 20,
                        "slice": "pooled", "view": view},
            ).json()
            assert s["total"] == agg["n"]          # count-coherence in this mode
            assert s["cohort"]["view"] == view


def test_samples_event_study_default_view_is_episodes(loaded_engine):
    """The samples drill-down defaults to episodes (matching the aggregate default) for the event-study
    kind, so a no-`view` drill-down total equals the episodes-view event-study n."""
    with TestClient(main.app) as client:
        agg = client.get(
            "/api/research/event-study",
            params={"subject": "vcp", "horizon": 20, "view": "episodes"},
        ).json()
        s = client.get(
            "/api/research/samples",
            params={"kind": "event-study", "subject": "vcp", "horizon": 20, "slice": "pooled"},
        ).json()
    assert s["cohort"]["view"] == "episodes" and s["total"] == agg["n"]


def test_samples_unknown_view_422(loaded_engine):
    """An unknown event-study `view` is rejected (422) on the samples endpoint too (both endpoints validate
    `view` to {episodes, pooled})."""
    with TestClient(main.app) as client:
        resp = client.get(
            "/api/research/samples",
            params={"kind": "event-study", "subject": "vcp", "horizon": 20,
                    "slice": "pooled", "view": "nonsense"},
        )
    assert resp.status_code == 422


# ==================================================================================================
# iter-20 J-72 — the event-study endpoint serves the cached aggregate (byte-identical to a fresh compute)
# ==================================================================================================
def test_event_study_endpoint_byte_identical_across_repeated_reads(loaded_engine):
    """J-72: the cached endpoint serves a byte-identical payload on repeated reads (a cache HIT after the
    first MISS) — same figures, never recomputed differently per request."""
    with TestClient(main.app) as client:
        first = client.get(
            "/api/research/event-study", params={"subject": "vcp", "horizon": 20, "view": "episodes"}
        ).json()
        second = client.get(
            "/api/research/event-study", params={"subject": "vcp", "horizon": 20, "view": "episodes"}
        ).json()
    import json as _json
    assert _json.dumps(first, sort_keys=True) == _json.dumps(second, sort_keys=True)


def test_event_study_endpoint_matches_direct_compute(loaded_engine):
    """J-72: the endpoint payload equals a direct `compute_event_study` (the cache is a pure performance
    layer — byte-identical figures, the No-recompute-in-the-read-path contract)."""
    import json as _json

    from app.engine.research import compute_event_study
    cfg = load_config()
    with TestClient(main.app) as client:
        served = client.get(
            "/api/research/event-study", params={"subject": "vcp", "horizon": 20, "view": "pooled"}
        ).json()
    with Session(loaded_engine) as session:
        direct = compute_event_study(session, "vcp", 20, cfg, view="pooled")
    assert _json.dumps(served, sort_keys=True) == _json.dumps(direct, sort_keys=True)


# ==================================================================================================
# iter-20 J-75 — five per-stock forward returns served on /api/stocks + detail (identical, config-driven)
# ==================================================================================================
def test_stocks_carry_five_forward_returns_config_driven(loaded_engine):
    """J-75: every /api/stocks row carries a `forward_returns` list, one entry per config horizon (no
    hardcoded list), each `{horizon, return}` (return float or null NA)."""
    cfg = load_config()
    horizons = list(cfg.walk_forward.horizons)
    # pick a historical run with post-D bars so at least some horizons are populated.
    with TestClient(main.app) as client:
        oldest = _oldest_research_date(client)
        payload = client.get("/api/stocks", params={"as_of": oldest}).json()
    assert payload["rows"], "expected stored stock rows at the oldest run"
    for row in payload["rows"]:
        assert [fr["horizon"] for fr in row["forward_returns"]] == horizons
        for fr in row["forward_returns"]:
            assert fr["return"] is None or isinstance(fr["return"], (int, float))


def test_stocks_leaderboard_equals_detail_forward_returns(loaded_engine):
    """J-75 / J-06: the leaderboard list row and the detail row carry IDENTICAL forward returns for the
    same ticker/date/horizon (single source — the same stored rows, one serving path)."""
    with TestClient(main.app) as client:
        oldest = _oldest_research_date(client)
        payload = client.get("/api/stocks", params={"as_of": oldest}).json()
        row = payload["rows"][0]
        detail = client.get(f"/api/stocks/{row['ticker']}", params={"as_of": oldest}).json()
    assert detail["row"]["forward_returns"] == row["forward_returns"]


def test_stocks_forward_returns_match_backtest_stored(loaded_engine):
    """J-75 / J-21: a /api/stocks row's forward return at a horizon equals the SAME stored
    `forward_returns` value Backtest reads (one source — never a second computation)."""
    with TestClient(main.app) as client:
        oldest = _oldest_research_date(client)
        stocks = client.get("/api/stocks", params={"as_of": oldest}).json()
        backtest = client.get("/api/backtest", params={"as_of": oldest}).json()
    # build {(ticker, horizon): return} from the backtest leadership cohort + from the stocks rows.
    bt = {}
    for h in backtest["scorecard"]["by_horizon"]:
        for c in h["leadership_returns"]["cohort"]:
            bt[(c["ticker"], h["horizon"])] = c["mean_return"]
    checked = 0
    for row in stocks["rows"]:
        for fr in row["forward_returns"]:
            key = (row["ticker"], fr["horizon"])
            if key in bt:
                assert fr["return"] == bt[key], f"{key}: stocks={fr['return']} backtest={bt[key]}"
                checked += 1
    assert checked > 0, "expected at least one overlapping (ticker, horizon) to compare"


# ==================================================================================================
# iter-20 J-77 — the new regime-setup-pattern endpoint + count-coherence with /research/samples
# ==================================================================================================
def test_regime_setup_pattern_endpoint_default_payload(loaded_engine):
    """J-77: the new endpoint returns a ranked combinations table with config-backed vocabularies + the
    survivorship label + per-row stats; default horizon resolves; rows ranked by the risk-adjusted figure."""
    cfg = load_config()
    with TestClient(main.app) as client:
        payload = client.get("/api/research/regime-setup-pattern").json()
    assert payload["horizon"] == cfg.walk_forward.default_horizon
    assert payload["regime_labels"] == list(cfg.regime.labels)
    assert "survivorship_bias" in payload
    assert isinstance(payload["rows"], list)
    for r in payload["rows"]:
        assert {"regime", "setup", "pattern", "stats"} <= set(r)
        assert {"n", "mean", "median", "pct_positive", "expectancy",
                "return_per_downside_dev", "return_per_mae", "low_sample"} <= set(r["stats"])


def test_regime_setup_pattern_unknown_horizon_422(loaded_engine):
    with TestClient(main.app) as client:
        resp = client.get("/api/research/regime-setup-pattern", params={"horizon": 999})
    assert resp.status_code == 422


def test_regime_setup_pattern_unknown_view_422(loaded_engine):
    with TestClient(main.app) as client:
        resp = client.get("/api/research/regime-setup-pattern", params={"view": "nonsense"})
    assert resp.status_code == 422


def test_regime_setup_pattern_count_coherence_same_instant(loaded_engine):
    """J-77 keystone (SAME-INSTANT): for EVERY non-empty combination row, the published `n` EQUALS the
    /research/samples drill-down `total` for that exact (regime, setup, pattern) cohort, asserted at the
    SAME instant against the live aggregate (Ns drift between boots as warm-up matures) in BOTH views."""
    for view in ("pooled", "episodes"):
        with TestClient(main.app) as client:
            study = client.get(
                "/api/research/regime-setup-pattern", params={"horizon": 20, "view": view}
            ).json()
            for r in study["rows"]:
                if r["stats"]["n"] == 0:
                    continue
                s = client.get(
                    "/api/research/samples",
                    params={
                        "kind": "regime-setup-pattern", "horizon": 20, "view": view,
                        "regime": r["regime"], "setup": r["setup"], "pattern": r["pattern"],
                    },
                ).json()
                assert s["total"] == r["stats"]["n"], (
                    f"{view} {(r['regime'], r['setup'], r['pattern'])}: "
                    f"study n={r['stats']['n']} samples total={s['total']}"
                )


def test_samples_regime_setup_pattern_invalid_selector_422(loaded_engine):
    """J-77: an unknown (regime, setup, pattern) cohort selector on /research/samples is an explicit 4xx
    (never a silent empty 200)."""
    with TestClient(main.app) as client:
        resp = client.get(
            "/api/research/samples",
            params={"kind": "regime-setup-pattern", "horizon": 20,
                    "regime": "Bogus", "setup": "Actionable", "pattern": "vcp"},
        )
    assert resp.status_code == 422


# ==================================================================================================
# iter-45 (J-103) — the Severity-velocity × Regime forward-return study endpoint + its samples drill-down
# (against the real seed). Proves the matrix renders, the verdict caveat is carried verbatim, the
# count-coherence keystone holds (each cell's published N == its samples drill-down total), and the
# selectors validate (422 on a bad horizon / family / sign).
# ==================================================================================================
def test_severity_velocity_endpoint_default_payload(loaded_engine):
    """J-103 at the API level: the default payload carries the regime-family × velocity-sign matrix (mean /
    win-rate / N per cell), the config-driven family + sign vocabularies, and the honest verdict caveat."""
    cfg = load_config()
    sv = cfg.research.severity_velocity
    with TestClient(main.app) as client:
        resp = client.get("/api/research/severity-velocity")
    assert resp.status_code == 200
    data = resp.json()
    assert data["horizon"] == cfg.walk_forward.default_horizon
    assert data["asof_date"] is None  # default = all-history
    assert data["benchmark"] == cfg.etfs.index[0]
    # the config-driven vocabularies are echoed (the frontend matrix headers + chips build from these)
    assert [f["key"] for f in data["regime_families"]] == [f.key for f in sv.regime_families]
    assert [s["key"] for s in data["velocity_signs"]] == [s.key for s in sv.velocity_signs]
    # the matrix is one row per family, one cell per sign — every cell present (honest NA at n=0)
    assert len(data["matrix"]) == len(sv.regime_families)
    for row in data["matrix"]:
        assert len(row["cells"]) == len(sv.velocity_signs)
        for cell in row["cells"]:
            assert {"n", "low_sample", "mean_return", "win_rate"} == set(cell["stats"])
    # the verdict caveat is carried VERBATIM (the hypothesis is NOT supported on the bull-dominated seed)
    assert "bounce, not continuation" in data["verdict_caveat"]
    assert "NOT supported" in data["verdict_caveat"]


def test_severity_velocity_endpoint_byte_identical_repeated_reads(loaded_engine):
    """J-72/J-103: the cached endpoint serves a byte-identical payload on repeated reads (a HIT after the
    first MISS) — same figures, never recomputed differently per request."""
    import json as _json
    with TestClient(main.app) as client:
        first = client.get("/api/research/severity-velocity").json()
        second = client.get("/api/research/severity-velocity").json()
    assert _json.dumps(first, sort_keys=True) == _json.dumps(second, sort_keys=True)


def test_severity_velocity_endpoint_bad_horizon_422(loaded_engine):
    """An unknown horizon is an explicit 422 (never a fabricated window) — mirroring the sibling handlers."""
    with TestClient(main.app) as client:
        assert client.get("/api/research/severity-velocity?horizon=999").status_code == 422


def test_severity_velocity_samples_count_coherence(loaded_engine):
    """COUNT-COHERENCE (J-51/J-103): each matrix cell's published N equals its samples drill-down total —
    every displayable cell resolves without a 4xx (the J-82 lesson)."""
    with TestClient(main.app) as client:
        study = client.get("/api/research/severity-velocity", params={"horizon": 20}).json()
        for row in study["matrix"]:
            for cell in row["cells"]:
                s = client.get(
                    "/api/research/samples",
                    params={
                        "kind": "severity-velocity", "horizon": 20,
                        "family": row["family"], "velocity_sign": cell["velocity_sign"],
                    },
                ).json()
                assert s["total"] == cell["stats"]["n"], (
                    f"({row['family']}, {cell['velocity_sign']}): "
                    f"study n={cell['stats']['n']} samples total={s['total']}"
                )


def test_severity_velocity_samples_invalid_selector_422(loaded_engine):
    """J-103: an unknown family/sign cohort selector on /research/samples is an explicit 4xx (never a
    silent empty 200, which is reserved for a VALID n=0 cell)."""
    with TestClient(main.app) as client:
        assert client.get(
            "/api/research/samples",
            params={"kind": "severity-velocity", "horizon": 20,
                    "family": "bogus", "velocity_sign": "rising"},
        ).status_code == 422
        assert client.get(
            "/api/research/samples",
            params={"kind": "severity-velocity", "horizon": 20,
                    "family": "risk_off", "velocity_sign": "sideways"},
        ).status_code == 422
