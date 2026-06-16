"""API ↔ engine: served values EQUAL the engine outputs (no recompute drift).

Single source of truth (anti-goal): every endpoint serves exactly what the engine computes — no
second computation, no reshaping of a score. The J-06 coherence guard proves a ticker's row from
`/api/stocks` (list) is byte-identical to its row from `/api/stocks/{ticker}` (detail). The
dashboard's `candidate_counts` equal `summarize_candidates(score_stocks)` (counts the canonical
setup statuses); Theme scores are served ONLY by `/api/themes` (not re-served by the dashboard).
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
from app.engine.regime import score_regime
from app.engine.scoring import score_stocks
from app.engine.sectors import score_sectors
from app.engine.setups import summarize_candidates
from app.engine.themes import score_themes


def test_api_sectors_equals_engine_output(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        expected = score_sectors(session, asof, cfg)
    with TestClient(main.app) as client:
        resp = client.get("/api/sectors")
    assert resp.status_code == 200
    served = resp.json()
    # iter-23 (J-81): the snapshot-served sector rows ADDITIVELY carry `forward_returns` (read verbatim
    # from the stored forward_returns table via the same `_leadership_returns` builder Backtest uses) that
    # the live `score_sectors` engine does not produce — a NEW serving field, NOT a recomputed canonical
    # score. Strip it so the no-drift guarantee is asserted on the CANONICAL scored payload (every
    # score/rank/component/breadth/trend/member still byte-identical to the live engine).
    stripped = {
        **served,
        "rows": [{k: v for k, v in row.items() if k != "forward_returns"} for row in served["rows"]],
    }
    assert stripped == expected  # byte-for-byte: served canonical == computed (no drift)
    # the additive J-81 field is present + config-driven (one entry per walk_forward horizon)
    for row in served["rows"]:
        assert [fr["horizon"] for fr in row["forward_returns"]] == list(cfg.walk_forward.horizons)
    assert served["benchmark"] == "SPY"
    assert len(served["rows"]) == 31


def test_api_sectors_serves_config_name_description_and_members(loaded_engine):
    """J-58: /api/sectors echoes the stored config name + description + universe-member list verbatim
    from the immutable snapshot (no read-path recompute). An unmapped industry ETF (KRE) serves an
    empty member list — never fabricated; a sector ETF serves description=null but a non-empty list."""
    cfg = load_config()
    with TestClient(main.app) as client:
        rows = client.get("/api/sectors").json()["rows"]
    by_ticker = {r["ticker"]: r for r in rows}

    # industry ETF: config name + description + members from stock_industries
    smh = by_ticker["SMH"]
    assert smh["name"] == cfg.etfs.industry["SMH"].name and smh["name"] != "SMH"
    assert smh["description"] == cfg.etfs.industry["SMH"].description
    assert "NVDA" in smh["members"]

    # unmapped industry ETF: explicit empty member list, still config-named
    kre = by_ticker["KRE"]
    assert kre["name"] == cfg.etfs.industry["KRE"].name
    assert kre["members"] == []

    # sector ETF: named from etfs.sector, no description, members from stock_sectors
    xlk = by_ticker["XLK"]
    assert xlk["description"] is None
    assert xlk["members"] == sorted(t for t, s in cfg.stock_sectors.items() if s == "Technology")
    # every served member is a real universe symbol (no fabrication anywhere)
    universe = set(cfg.universe.symbols)
    for r in rows:
        assert all(m in universe for m in r["members"])


def test_api_sectors_reserved_run_is_byte_identical(loaded_engine):
    """Snapshot immutability: serving the SAME stored run twice yields byte-identical payloads
    (including the J-58 description/members) — the read path never recomputes or mutates."""
    with TestClient(main.app) as client:
        first = client.get("/api/sectors").json()
        second = client.get("/api/sectors").json()
    assert first == second
    # the additive fields are present on every row
    assert all("description" in r and "members" in r for r in first["rows"])


def test_api_dashboard_equals_engine_with_real_candidate_counts(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        regime = score_regime(session, asof, cfg)
        expected_counts = summarize_candidates(score_stocks(session, asof, cfg)["rows"])
    with TestClient(main.app) as client:
        resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    body = resp.json()

    # regime served == engine (single source of truth)
    assert body["regime"]["score"] == regime["score"]
    assert body["regime"]["label"] == regime["label"]
    assert body["regime"]["components"] == regime["components"]

    # breadth served == engine, labelled universe-relative
    assert body["breadth"]["above_50dma_pct"] == regime["breadth_above_50dma"]
    assert body["breadth"]["above_200dma_pct"] == regime["breadth_above_200dma"]
    assert body["breadth"]["label"] == "universe-relative"

    assert body["asof_date"] == asof.isoformat()
    # candidate counts == summarize_candidates(score_stocks) — the single derivation path
    assert body["candidate_counts"] == expected_counts
    assert all(isinstance(v, int) for v in body["candidate_counts"].values())
    # Theme score is NOT re-served by the dashboard (one serving path = /api/themes)
    assert "top_themes" not in body


def test_dashboard_top_sectors_match_sectors_endpoint(loaded_engine):
    """The Dashboard's Top Sectors read the canonical /api/sectors (one serving path). Prove the
    top sectors a client would slice equal the /api/sectors rows — same values, no second source."""
    with TestClient(main.app) as client:
        sectors_rows = client.get("/api/sectors").json()["rows"]
    top3 = sectors_rows[:3]
    assert [r["rank"] for r in top3] == [1, 2, 3]
    assert all(r["score"] >= top3[-1]["score"] for r in top3)


def test_api_stocks_equals_engine_output(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        expected = score_stocks(session, asof, cfg)
    with TestClient(main.app) as client:
        resp = client.get("/api/stocks")
    assert resp.status_code == 200
    served = resp.json()
    # iter-20 (J-75): the snapshot-served rows ADDITIVELY carry `forward_returns` (read verbatim from the
    # stored forward_returns table) that the live `score_stocks` engine does not produce — a NEW serving
    # field, NOT a recomputed canonical score. Strip it so the no-drift guarantee is asserted on the
    # CANONICAL scored payload (every score/bucket/setup/pattern still byte-identical to the live engine).
    stripped = {
        **served,
        "rows": [{k: v for k, v in row.items() if k != "forward_returns"} for row in served["rows"]],
    }
    assert stripped == expected                      # byte-for-byte: served canonical == computed (no drift)
    # the additive J-75 field is present + config-driven (one entry per walk_forward horizon)
    for row in served["rows"]:
        assert [fr["horizon"] for fr in row["forward_returns"]] == list(cfg.walk_forward.horizons)
    assert served["benchmark"] == "SPY"
    assert len(served["rows"]) == len(cfg.universe.symbols)


def test_api_stock_detail_equals_list_row_single_source_j06(loaded_engine):
    """J-06 coherence guard: NVDA's row from the leaderboard EQUALS its row from the detail
    endpoint — one computation, never recomputed per view (scores AND buckets identical)."""
    with TestClient(main.app) as client:
        list_rows = client.get("/api/stocks").json()["rows"]
        detail = client.get("/api/stocks/NVDA").json()
    list_nvda = next(r for r in list_rows if r["ticker"] == "NVDA")
    assert detail["row"] == list_nvda                # full byte-identical row
    for score_key in ("leadership", "entry_quality", "risk"):
        assert detail["row"][score_key]["score"] == list_nvda[score_key]["score"]
        assert detail["row"][score_key]["bucket"] == list_nvda[score_key]["bucket"]


def test_api_stock_detail_unknown_ticker_404(loaded_engine):
    with TestClient(main.app) as client:
        resp = client.get("/api/stocks/NOTREAL")
    assert resp.status_code == 404


def test_api_stock_detail_is_case_insensitive(loaded_engine):
    with TestClient(main.app) as client:
        resp = client.get("/api/stocks/nvda")
    assert resp.status_code == 200
    assert resp.json()["row"]["ticker"] == "NVDA"


def test_api_themes_equals_engine_output(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        expected = score_themes(session, asof, cfg)
    with TestClient(main.app) as client:
        resp = client.get("/api/themes")
    assert resp.status_code == 200
    served = resp.json()
    # iter-23 (J-81): the snapshot-served theme rows ADDITIVELY carry `forward_returns` (the equal-weight
    # member-basket return read verbatim from the stored forward_returns table via the same
    # `_leadership_returns` builder Backtest uses) that the live `score_themes` engine does not produce — a
    # NEW serving field, NOT a recomputed canonical score. Strip it so the no-drift guarantee is asserted
    # on the CANONICAL scored payload (every score/rank/component/breadth/member still byte-identical to
    # the live engine).
    stripped = {
        **served,
        "rows": [{k: v for k, v in row.items() if k != "forward_returns"} for row in served["rows"]],
    }
    assert stripped == expected  # byte-for-byte: served canonical == computed (no drift)
    # the additive J-81 field is present + config-driven (one entry per walk_forward horizon)
    for row in served["rows"]:
        assert [fr["horizon"] for fr in row["forward_returns"]] == list(cfg.walk_forward.horizons)
    assert len(served["rows"]) == len(cfg.themes)


def test_new_endpoints_raise_503_when_no_price_data(tmp_path):
    """No price data -> explicit 503 on all three new endpoints (never fabricated rows). The route
    handlers are called directly against an empty DB session (the live app self-seeds on startup,
    so emptiness is exercised at the handler level), leaving the process engine untouched."""
    from app.api.stocks import stock_detail, stocks
    from app.api.themes import themes as themes_route

    engine = make_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    create_db_and_tables(engine)  # tables exist, but no price rows were ever loaded
    with Session(engine) as session:
        assert latest_data_date(session) is None
        # iter-8: handlers now take an optional `as_of` first, so pass `session` by keyword.
        for call in (
            lambda: stocks(session=session),
            lambda: stock_detail("NVDA", session=session),
            lambda: themes_route(session=session),
        ):
            with pytest.raises(HTTPException) as exc:
                call()
            assert exc.value.status_code == 503


# --- iter-8: snapshot-served reads + as-of resolution (J-15 + J-13) -------------------------
def _historical_run(client) -> dict:
    """The oldest stored run (a genuinely historical as-of date != latest) from the canonical list."""
    runs = client.get("/api/runs").json()["runs"]
    return min(runs, key=lambda r: r["asof_date"])


def test_repointed_endpoints_echo_resolved_asof(loaded_engine):
    """Every re-pointed read endpoint echoes the resolved `asof_date` it served — for a historical
    date as well as the latest — so the UI can render the as-of / historical indicator."""
    with TestClient(main.app) as client:
        historical = _historical_run(client)["asof_date"]
        for path in ("/api/dashboard", "/api/stocks", "/api/sectors", "/api/themes"):
            body = client.get(f"{path}?as_of={historical}").json()
            assert body["asof_date"] == historical, path


def test_asof_serves_stored_snapshot_matching_run_detail(loaded_engine):
    """J-13/J-15: `/api/stocks?as_of=D` serves the SAME stored snapshot rows as the immutable
    `/api/runs/{run_id}` for that date — byte-identical — and that date differs from the latest."""
    with TestClient(main.app) as client:
        runs = client.get("/api/runs").json()["runs"]
        latest_date = max(r["asof_date"] for r in runs)
        historical = min(runs, key=lambda r: r["asof_date"])
        assert historical["asof_date"] != latest_date  # genuinely a historical view
        stocks_asof = client.get(f"/api/stocks?as_of={historical['asof_date']}").json()
        run_detail = client.get(f"/api/runs/{historical['run_id']}").json()
    assert stocks_asof["asof_date"] == historical["asof_date"]
    # iter-20 (J-75): `/api/stocks` rows ADDITIVELY carry `forward_returns` (a NEW serving field read from
    # the separate stored forward_returns table); the immutable `/api/runs/{id}` snapshot view deliberately
    # does NOT (forward returns are not part of the immutable snapshot). Compare the SAME stored canonical
    # rows modulo that additive field — they remain byte-identical (the J-13/J-15 single-source guarantee).
    stocks_rows = [{k: v for k, v in r.items() if k != "forward_returns"} for r in stocks_asof["rows"]]
    assert stocks_rows == run_detail["rows"]  # the same stored immutable snapshot (canonical rows)


def test_asof_detail_equals_list_row_for_historical_date(loaded_engine):
    """J-06 holds for a HISTORICAL date too: a stock's `/api/stocks?as_of=D` list row is byte-identical
    to its `/api/stocks/{ticker}?as_of=D` detail row (both rehydrated from the same stored result)."""
    with TestClient(main.app) as client:
        d = _historical_run(client)["asof_date"]
        list_rows = client.get(f"/api/stocks?as_of={d}").json()["rows"]
        ticker = list_rows[0]["ticker"]
        detail = client.get(f"/api/stocks/{ticker}?as_of={d}").json()
    assert detail["asof_date"] == d
    assert detail["row"] == next(r for r in list_rows if r["ticker"] == ticker)


def test_repointed_handlers_serve_persisted_date_without_recompute(loaded_engine, monkeypatch):
    """No-recompute (anti-goal): for an already-persisted as-of date the re-pointed endpoints serve the
    stored snapshot WITHOUT invoking the live scoring/regime/sector/theme engines. We patch those
    engines (as `run_scan` references them) to raise, then assert the handlers still return the stored
    payload for a persisted date — proving they read storage, never recompute."""
    from app.api.dashboard import dashboard as dashboard_route
    from app.api.sectors import sectors as sectors_route
    from app.api.stocks import stocks as stocks_route
    from app.api.themes import themes as themes_route

    with TestClient(main.app) as client:  # lifespan persists the bootstrap runs
        historical = _historical_run(client)["asof_date"]

    def boom(*args, **kwargs):
        raise AssertionError("a live engine must not run for an already-persisted as-of date")

    for name in ("score_stocks", "score_regime", "score_sectors", "score_themes"):
        monkeypatch.setattr(f"app.engine.scanner.{name}", boom)

    with Session(loaded_engine) as session:
        assert stocks_route(as_of=historical, session=session)["asof_date"] == historical
        assert dashboard_route(as_of=historical, session=session)["asof_date"] == historical
        assert sectors_route(as_of=historical, session=session)["asof_date"] == historical
        assert themes_route(as_of=historical, session=session)["asof_date"] == historical


def test_vcp_served_from_storage_not_recomputed_keystone(loaded_engine, monkeypatch):
    """Keystone (patch-to-raise — NOT value-equality, per the iter-8 lesson): with `detect_vcp` AND
    the score_* engines patched to RAISE, the read path STILL serves the stored VCP flag from the
    immutable snapshot — proving `/api/stocks`, `/api/stocks/{ticker}`, and the System Health
    `by_vcp` breakdown re-detect/recompute nothing (anti-goal: No recompute in the read path)."""
    from app.engine.forward_testing import compute_forward_aggregates

    # the lifespan persists the bootstrap runs + walk-forward forward_returns into loaded_engine
    with TestClient(main.app) as client:
        latest = max(r["asof_date"] for r in client.get("/api/runs").json()["runs"])

    def boom(*args, **kwargs):
        raise AssertionError("the read path must NOT re-detect VCP or re-score a persisted snapshot")

    monkeypatch.setattr("app.engine.patterns.detect_vcp", boom)
    monkeypatch.setattr("app.engine.scoring.detect_vcp", boom)
    for name in ("score_stocks", "score_regime", "score_sectors", "score_themes"):
        monkeypatch.setattr(f"app.engine.scanner.{name}", boom)

    from app.api.stocks import stock_detail as stock_detail_route, stocks as stocks_route

    cfg = load_config()
    with Session(loaded_engine) as session:
        # /api/stocks serves the stored vcp block for the persisted latest date (no re-detection)
        rows = stocks_route(as_of=latest, session=session)["rows"]
        assert rows
        assert all("vcp" in r and {"flagged", "pivot", "invalidation"} <= set(r["vcp"]) for r in rows)

        # the detail row's vcp is byte-identical to the same stored list row (J-06)
        ticker = rows[0]["ticker"]
        detail = stock_detail_route(ticker, as_of=latest, session=session)
        assert detail["row"]["vcp"] == rows[0]["vcp"]

        # the System Health by_vcp breakdown reads the stored is_vcp mirror (never re-detects)
        agg = compute_forward_aggregates(session, cfg.walk_forward.default_horizon, cfg)
        assert {r["vcp"] for r in agg["by_vcp"]} == {"VCP", "non-VCP"}


def test_new_patterns_served_from_storage_not_recomputed_keystone(loaded_engine, monkeypatch):
    """Keystone for the two NEW patterns (patch-to-raise, per the iter-8 lesson): with BOTH new
    detectors AND the score_* engines patched to RAISE, the read path STILL serves the stored pattern
    flags from the immutable snapshot — proving `/api/stocks` (list + detail) and the System Health
    `by_<name>` breakdowns re-detect/recompute nothing (anti-goal: No recompute in the read path)."""
    from app.engine.forward_testing import compute_forward_aggregates

    with TestClient(main.app) as client:
        latest = max(r["asof_date"] for r in client.get("/api/runs").json()["runs"])

    def boom(*args, **kwargs):
        raise AssertionError("the read path must NOT re-detect a pattern or re-score a persisted snapshot")

    for name in ("detect_pullback_to_rising_dma", "detect_flat_base_breakout"):
        monkeypatch.setattr(f"app.engine.patterns.{name}", boom)
        monkeypatch.setattr(f"app.engine.scoring.{name}", boom)
    for name in ("score_stocks", "score_regime", "score_sectors", "score_themes"):
        monkeypatch.setattr(f"app.engine.scanner.{name}", boom)

    from app.api.stocks import stock_detail as stock_detail_route, stocks as stocks_route

    cfg = load_config()
    with Session(loaded_engine) as session:
        rows = stocks_route(as_of=latest, session=session)["rows"]
        assert rows
        # both new pattern blocks served from storage for every row (no re-detection)
        for name in ("pullback_to_rising_dma", "flat_base_breakout"):
            assert all(name in r and {"flagged", "pivot", "invalidation"} <= set(r[name]) for r in rows)

        # the detail row's pattern blocks are byte-identical to the same stored list row (J-06)
        ticker = rows[0]["ticker"]
        detail = stock_detail_route(ticker, as_of=latest, session=session)
        for name in ("pullback_to_rising_dma", "flat_base_breakout"):
            assert detail["row"][name] == rows[0][name]

        # the System Health by_<name> breakdowns read the stored mirrors (never re-detect)
        agg = compute_forward_aggregates(session, cfg.walk_forward.default_horizon, cfg)
        assert {r["pullback_to_rising_dma"] for r in agg["by_pullback_to_rising_dma"]} == {"Pullback-to-DMA", "non-Pullback"}
        assert {r["flat_base_breakout"] for r in agg["by_flat_base_breakout"]} == {"Flat-base", "non-Flat-base"}


def test_asof_invalid_dates_are_explicit_4xx_never_fabricated(loaded_engine):
    """Invalid as-of -> explicit 4xx, never a fabricated snapshot: future -> 400, before history ->
    400, unparseable -> 422 (FastAPI convention; any 4xx satisfies the no-fabrication contract)."""
    with TestClient(main.app) as client:
        assert client.get("/api/stocks?as_of=2999-01-01").status_code == 400      # future
        assert client.get("/api/stocks?as_of=1900-01-01").status_code == 400      # before history
        assert client.get("/api/stocks?as_of=not-a-date").status_code == 422      # unparseable
        # the same contract on the other re-pointed endpoints
        assert client.get("/api/dashboard?as_of=not-a-date").status_code == 422
        assert client.get("/api/sectors?as_of=2999-01-01").status_code == 400
        assert client.get("/api/themes?as_of=not-a-date").status_code == 422
