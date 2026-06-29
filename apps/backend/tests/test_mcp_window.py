"""Tests for the read-only MCP "window" tool layer (app.mcp).

The contract under test is OUTPUT PARITY: every `app.mcp.tools` function must return the SAME data the
matching `GET /api` read endpoint returns, because the tools reuse the exact engine / serving functions
the routers call. So for `get_dashboard` and `get_leaderboard` we assert the tool output EQUALS BOTH
(a) the engine/serving path the router invokes AND (b) the live HTTP endpoint (via TestClient), against
the committed seed. The remaining tools get non-empty structural-parity checks plus a clean-import check
and a read-only-surface guard. Everything is offline / deterministic (the `loaded_engine` fixture warms
the committed seed once).
"""
from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlmodel import Session

import main
from app.engine import ledger as ledger_mod
from app.engine.snapshot_serving import (
    dashboard_payload,
    resolved_run,
    sectors_payload,
    stock_detail_payload,
    stocks_payload,
    themes_payload,
)
from app.mcp import tools


def _json(obj):
    """Normalize a Python dict through JSON so a tool dict and a parsed HTTP response compare fairly
    (e.g. any tuple -> list), exactly as the endpoint's JSON serialization would render it."""
    return json.loads(json.dumps(obj))


# ==================================================================================================
# Parity: get_dashboard == engine path == GET /api/dashboard
# ==================================================================================================
def test_get_dashboard_equals_endpoint_and_engine(loaded_engine):
    with Session(loaded_engine) as session:
        tool_out = tools.get_dashboard(session)
        engine_out = dashboard_payload(resolved_run(session, None))
    assert tool_out == engine_out  # reuses the SAME serving function the router calls

    with TestClient(main.app) as client:
        http_out = client.get("/api/dashboard").json()
    assert _json(tool_out) == http_out  # byte-identical to the live HTTP endpoint

    # structural sanity
    assert set(tool_out) >= {"regime", "breadth", "asof_date", "candidate_counts"}
    assert tool_out["regime"]["label"]
    assert isinstance(tool_out["regime"]["score"], (int, float))


# ==================================================================================================
# Parity: get_leaderboard == engine path == GET /api/stocks  (+ honest post-filters)
# ==================================================================================================
def test_get_leaderboard_equals_endpoint_and_engine(loaded_engine):
    with Session(loaded_engine) as session:
        tool_out = tools.get_leaderboard(session)
        engine_out = stocks_payload(session, resolved_run(session, None))
    assert tool_out == engine_out  # no filters -> the SAME serving payload the router returns

    with TestClient(main.app) as client:
        http_out = client.get("/api/stocks").json()
    assert _json(tool_out) == http_out  # byte-identical to the live HTTP endpoint

    assert tool_out["rows"]
    assert all("ticker" in r and "leadership" in r and "forward_returns" in r for r in tool_out["rows"])


def test_get_leaderboard_filters_are_honest_subsets(loaded_engine):
    with Session(loaded_engine) as session:
        full = tools.get_leaderboard(session)
        rows = full["rows"]
        assert rows

        # ticker filter — exact, case-insensitive
        a_ticker = rows[0]["ticker"]
        by_ticker = tools.get_leaderboard(session, ticker=a_ticker.lower())
        assert [r["ticker"] for r in by_ticker["rows"]] == [a_ticker]

        # sector filter — same stored sector, never grows the set
        a_sector = next((r["sector"] for r in rows if r.get("sector")), None)
        assert a_sector is not None
        by_sector = tools.get_leaderboard(session, sector=a_sector)
        assert by_sector["rows"]
        assert all(r["sector"] == a_sector for r in by_sector["rows"])
        assert len(by_sector["rows"]) <= len(rows)

        # theme filter — by slug
        a_theme = next((r["themes"][0]["slug"] for r in rows if r.get("themes")), None)
        if a_theme is not None:
            by_theme = tools.get_leaderboard(session, theme=a_theme)
            assert by_theme["rows"]
            assert all(any(t["slug"] == a_theme for t in r["themes"]) for r in by_theme["rows"])

        # pattern filter — only rows with that detected pattern flagged
        by_vcp = tools.get_leaderboard(session, pattern="vcp")
        assert all(r["vcp"]["flagged"] is True for r in by_vcp["rows"])
        assert len(by_vcp["rows"]) <= len(rows)

        # every filtered row is a member of the unfiltered set (a pure post-filter; nothing fabricated)
        full_tickers = {r["ticker"] for r in rows}
        for subset in (by_ticker, by_sector, by_vcp):
            assert {r["ticker"] for r in subset["rows"]} <= full_tickers


# ==================================================================================================
# get_stock_evidence == /api/stocks/{ticker} serving path
# ==================================================================================================
def test_get_stock_evidence_equals_detail_payload(loaded_engine):
    with Session(loaded_engine) as session:
        run = resolved_run(session, None)
        ticker = stocks_payload(session, run)["rows"][0]["ticker"]
        tool_out = tools.get_stock_evidence(session, ticker)
        engine_out = stock_detail_payload(session, run, ticker)
    assert tool_out == engine_out
    assert tool_out["row"]["ticker"] == ticker
    assert "asof_date" in tool_out and "benchmark" in tool_out


# ==================================================================================================
# get_sectors / get_themes
# ==================================================================================================
def test_get_sectors_and_themes_match_serving_path(loaded_engine):
    with Session(loaded_engine) as session:
        sectors_tool = tools.get_sectors(session)
        themes_tool = tools.get_themes(session)
        run = resolved_run(session, None)
        assert sectors_tool == sectors_payload(session, run)
        assert themes_tool == themes_payload(session, run)

    assert sectors_tool["rows"] and all(
        {"ticker", "score", "bucket", "forward_returns"} <= set(r) for r in sectors_tool["rows"]
    )
    assert themes_tool["rows"] and all(
        {"slug", "score", "bucket", "members"} <= set(r) for r in themes_tool["rows"]
    )


# ==================================================================================================
# get_market_phase (+ retrospective / full opt-ins)
# ==================================================================================================
def test_get_market_phase_structural(loaded_engine):
    with Session(loaded_engine) as session:
        mp = tools.get_market_phase(session)
        mp_retro = tools.get_market_phase(session, retrospective=True)
        mp_full = tools.get_market_phase(session, full=True)

    assert {"asof_date", "phase", "severity", "p_bear", "timeline", "episodes"} <= set(mp)
    assert isinstance(mp["timeline"], list)
    # default card payload does NOT carry the opt-in keys; the opt-ins add them additively
    assert "retrospective" not in mp
    assert "retrospective" in mp_retro
    assert "timeline_full" not in mp
    assert "timeline_full" in mp_full


# ==================================================================================================
# query_backtest
# ==================================================================================================
def test_query_backtest_structural(loaded_engine):
    with Session(loaded_engine) as session:
        bt = tools.query_backtest(session)
    assert {"asof_date", "scorecard", "horizons", "min_sample", "is_latest", "evidence_by_horizon"} <= set(bt)
    assert bt["is_latest"] is True  # default resolves to the latest stored run
    assert isinstance(bt["scorecard"]["by_horizon"], list) and bt["scorecard"]["by_horizon"]
    # evidence aggregate present for every configured horizon
    assert all(h in bt["evidence_by_horizon"] for h in bt["horizons"])


# ==================================================================================================
# Research: query_factor_lab (single + all-factors), query_event_study, drill_samples
# ==================================================================================================
def test_query_factor_lab_structural(loaded_engine):
    with Session(loaded_engine) as session:
        fl = tools.query_factor_lab(session)
        fl_all = tools.query_factor_lab(session, all_factors=True)

    assert {"factor", "horizon", "deciles", "rank_ic", "by_regime", "n_total"} <= set(fl)
    assert isinstance(fl["deciles"], list) and fl["deciles"]
    assert "key" in fl["factor"]
    # all-factors aggregate serves the per-factor table
    assert "factors_table" in fl_all and fl_all["factors_table"]


def test_query_event_study_structural(loaded_engine):
    with Session(loaded_engine) as session:
        es = tools.query_event_study(session)
    assert {"subject", "horizon", "view", "by_horizon", "by_regime", "by_sector", "n_total"} <= set(es)
    assert es["view"] == "episodes"  # default view


def test_drill_samples_factor_structural(loaded_engine):
    # The `factor` kind requires an explicit factor selector — like the real /api/research/samples
    # endpoint, the tool does NOT default it (the samples drill-down always receives the cohort's
    # selectors from the caller). Use the SAME default factor the factor-lab view resolves to, with the
    # "total" slice, so the drill-down reproduces that view's whole pool.
    with Session(loaded_engine) as session:
        fl = tools.query_factor_lab(session)            # default = first catalog factor at default_horizon
        factor_key = fl["factor"]["key"]
        smp = tools.drill_samples(session, kind="factor", factor=factor_key, slice_kind="total")
    assert {"kind", "horizon", "cohort", "total", "rows"} <= set(smp)
    assert smp["kind"] == "factor"
    assert smp["total"] == len(smp["rows"])
    # count-coherence keystone: the "total" drill-down total EQUALS the published factor-lab n_total.
    assert smp["total"] == fl["n_total"]


# ==================================================================================================
# verify_edge (the referee) — certifies a real factor cohort + appends exactly one ledger entry.
# (DB boot is slow, so this is the single integration test; the referee's statistics are proved
# exhaustively + offline in tests/test_referee.py.)
# ==================================================================================================
def test_verify_edge_certifies_a_real_factor_cohort(loaded_engine, tmp_path):
    ledger_path = str(tmp_path / "certified_claims.jsonl")
    with Session(loaded_engine) as session:
        fl = tools.query_factor_lab(session)  # default = first catalog factor at default_horizon
        factor_key = fl["factor"]["key"]
        horizon = fl["horizon"]
        claim = {"kind": "factor", "horizon": horizon, "factor": factor_key, "slice_kind": "total"}
        out = tools.verify_edge(session, claim, ledger_path, register_date="2026-06-29")

    verdict = out["verdict"]
    # well-formed verdict: a valid status + the full stats contract.
    assert verdict["status"] in {"PASS", "FAIL", "INSUFFICIENT"}
    assert {
        "in_sample_edge", "holdout_edge", "control_excess", "p_value",
        "effective_n", "n_trials_at_test", "alpha_charged",
    } <= set(verdict)
    assert out["register_date"] == "2026-06-29"
    assert out["cohort_n"] > 0  # the factor "total" cohort is non-empty
    assert verdict["n_trials_at_test"] == 1  # first claim against a fresh ledger

    # appends EXACTLY one ledger entry (the only write — the snapshot DB is untouched).
    entries = ledger_mod.read_entries(ledger_path)
    assert len(entries) == 1
    assert entries[0]["claim"] == claim
    assert entries[0]["register_date"] == "2026-06-29"
    assert entries[0]["verdict"]["status"] == verdict["status"]
    assert ledger_mod.count_trials(ledger_path) == 1

    # a SECOND claim against the same ledger advances the cumulative trial count (deflation memory).
    with Session(loaded_engine) as session:
        out2 = tools.verify_edge(session, claim, ledger_path, register_date="2026-06-30")
    assert out2["verdict"]["n_trials_at_test"] == 2
    assert ledger_mod.count_trials(ledger_path) == 2


# ==================================================================================================
# Additional read-only mirrors: regime-history, indexes, methodology, runs (+ detail)
# ==================================================================================================
def test_additional_readonly_mirrors(loaded_engine):
    with Session(loaded_engine) as session:
        rh = tools.get_regime_history(session)
        idx = tools.get_indexes(session)
        meth = tools.get_methodology()
        runs = tools.list_runs(session)
        run_id = runs["runs"][0]["run_id"]
        detail = tools.get_run(session, run_id)

    assert {"asof_date", "points"} <= set(rh) and isinstance(rh["points"], list)
    assert {"asof_date", "series", "ranges"} <= set(idx) and idx["series"]
    assert isinstance(meth, dict) and meth  # config-backed catalog
    assert runs["runs"] and {"run_id", "asof_date", "regime", "n_stocks"} <= set(runs["runs"][0])
    assert detail["run_id"] == run_id and detail["rows"]


# ==================================================================================================
# The MCP server module imports cleanly, and the exposed tool surface is READ-ONLY.
# ==================================================================================================
def test_server_imports_and_surface_is_read_only():
    import app.mcp.server as server  # must import without touching the DB

    assert server.mcp.name == "trendora-window"

    # The FastMCP tool registry — every registered tool is a read of computed evidence; nothing mutating.
    tool_names = {t.name for t in server.mcp._tool_manager.list_tools()}
    assert tool_names, "expected registered MCP tools"

    expected_reads = {
        "get_dashboard", "get_leaderboard", "get_stock_evidence", "get_sectors", "get_themes",
        "get_market_phase", "query_backtest", "query_factor_lab", "query_event_study",
        "drill_samples", "get_regime_history", "get_indexes", "get_methodology", "list_runs", "get_run",
    }
    assert expected_reads <= tool_names

    # The referee `verify_edge` is the SINGLE exception to the read-only surface: it writes ONLY the
    # append-only certified-claims ledger (a file) and is READ-ONLY w.r.t. the snapshot DB — so it is
    # explicitly carved out below. It must be registered.
    assert "verify_edge" in tool_names

    # READ-ONLY-w.r.t.-the-snapshot-DB guard: no watchlist write, no data-manager job, nothing whose
    # name implies a snapshot mutation. `verify_edge` (the ledger-only writer) is the one allowed
    # exception; every OTHER tool must be a pure read of computed evidence.
    forbidden_substrings = ("watchlist", "write", "create", "update", "delete",
                            "import", "job", "ingest", "mutate", "set_", "add_", "remove", "dismiss")
    for name in tool_names:
        if name == "verify_edge":
            continue  # the certifier — writes only the append-only ledger, never the snapshot DB
        lowered = name.lower()
        assert not any(bad in lowered for bad in forbidden_substrings), f"non-read-only tool exposed: {name}"
