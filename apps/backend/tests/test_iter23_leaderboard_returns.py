"""iter-23 — Themes/Sectors leaderboard forward-return columns (J-81) + Regime × Setup × Pattern
samples validation reconciliation (J-82c).

J-81 is a NEW READ SURFACE of the EXISTING stored `forward_returns` table — each `/api/themes` row and
each `/api/sectors` row ADDITIVELY carries a `forward_returns` list (one entry per
`config.walk_forward.horizons` value), read VERBATIM via the SAME `forward_testing:_leadership_returns`
builder Backtest's Top Themes / Top Sectors already use (theme = equal-weight member basket; sector =
the ETF's OWN stored return). The keystone assertion (J-06 single source) is byte-equality against the
`/api/backtest` leadership_returns projection for the same date + horizon — proving no recompute and no
second query path.

J-82(c) is a serve-side VALIDATION RECONCILIATION on `/research/samples` for the regime-setup-pattern
kind: the drill-down accepts EXACTLY the set of (regime, setup, pattern) combinations
`compute_regime_setup_pattern_study` emits (incl. `pattern = none`), with `total == the row's n` in BOTH
Episodes & Pooled and BOTH All-history & As-of, while a genuinely non-emitted combination still 4xxes.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

import main
from app.config import load_config


def _oldest_run_date(client) -> str:
    return min(r["asof_date"] for r in client.get("/api/runs").json()["runs"])


# ==================================================================================================
# J-81 — Themes leaderboard forward-return columns
# ==================================================================================================
def test_themes_rows_carry_forward_returns_config_driven(loaded_engine):
    """J-81: every /api/themes row carries a `forward_returns` list, one entry per config horizon (no
    hardcoded [1,5,10,20,60] literal), each `{horizon, return}` (return float or null NA)."""
    cfg = load_config()
    horizons = list(cfg.walk_forward.horizons)
    with TestClient(main.app) as client:
        oldest = _oldest_run_date(client)
        payload = client.get("/api/themes", params={"as_of": oldest}).json()
    assert payload["rows"], "expected stored theme rows at the oldest run"
    for row in payload["rows"]:
        assert [fr["horizon"] for fr in row["forward_returns"]] == horizons
        for fr in row["forward_returns"]:
            assert fr["return"] is None or isinstance(fr["return"], (int, float))


def test_sectors_rows_carry_forward_returns_config_driven(loaded_engine):
    """J-81: every /api/sectors row carries a `forward_returns` list, one entry per config horizon."""
    cfg = load_config()
    horizons = list(cfg.walk_forward.horizons)
    with TestClient(main.app) as client:
        oldest = _oldest_run_date(client)
        payload = client.get("/api/sectors", params={"as_of": oldest}).json()
    assert payload["rows"], "expected stored sector rows at the oldest run"
    for row in payload["rows"]:
        assert [fr["horizon"] for fr in row["forward_returns"]] == horizons
        for fr in row["forward_returns"]:
            assert fr["return"] is None or isinstance(fr["return"], (int, float))


def test_themes_forward_returns_match_backtest_leadership(loaded_engine):
    """J-81 / J-06 KEYSTONE: a /api/themes row's forward return at a horizon EQUALS the SAME value
    Backtest's Top Themes (`leadership_returns.themes`) exposes for the same date+horizon — one source
    (the same `_leadership_returns` projection over the same stored `forward_returns`), never a second
    computation."""
    with TestClient(main.app) as client:
        oldest = _oldest_run_date(client)
        themes = client.get("/api/themes", params={"as_of": oldest}).json()
        backtest = client.get("/api/backtest", params={"as_of": oldest}).json()
    # {(slug, horizon): mean_return} from Backtest's leadership_returns.themes
    bt = {}
    for h in backtest["scorecard"]["by_horizon"]:
        for t in h["leadership_returns"]["themes"]:
            bt[(t["slug"], h["horizon"])] = t["mean_return"]
    checked = 0
    for row in themes["rows"]:
        for fr in row["forward_returns"]:
            key = (row["slug"], fr["horizon"])
            assert key in bt, f"theme {key} not present in Backtest leadership_returns"
            assert fr["return"] == bt[key], f"{key}: themes={fr['return']} backtest={bt[key]}"
            checked += 1
    assert checked > 0, "expected at least one (theme, horizon) to compare"


def test_sectors_forward_returns_match_backtest_leadership(loaded_engine):
    """J-81 / J-06 KEYSTONE: a /api/sectors row's forward return at a horizon EQUALS the SAME value
    Backtest's Top Sectors (`leadership_returns.sectors`) exposes for the same date+horizon — the ETF's
    OWN stored return, one source, never a second computation. (Only SECTOR-ETF rows are in the
    leadership_returns.sectors projection; industry-ETF rows render NA honestly and are skipped here.)"""
    with TestClient(main.app) as client:
        oldest = _oldest_run_date(client)
        sectors = client.get("/api/sectors", params={"as_of": oldest}).json()
        backtest = client.get("/api/backtest", params={"as_of": oldest}).json()
    bt = {}
    for h in backtest["scorecard"]["by_horizon"]:
        for s in h["leadership_returns"]["sectors"]:
            bt[(s["sector_etf"], h["horizon"])] = s["mean_return"]
    checked = 0
    for row in sectors["rows"]:
        for fr in row["forward_returns"]:
            key = (row["ticker"], fr["horizon"])
            if key in bt:  # sector ETF -> compare against Backtest's own-return value
                assert fr["return"] == bt[key], f"{key}: sectors={fr['return']} backtest={bt[key]}"
                checked += 1
            else:  # an industry ETF not in the sector projection -> NA honestly, never fabricated
                assert fr["return"] is None
    assert checked > 0, "expected at least one (sector ETF, horizon) to compare"


def test_themes_forward_returns_na_at_latest(loaded_engine):
    """J-81 / No-fabricated-data: at the latest stored run there are no post-D bars for the far horizons,
    so the leaderboard forward-return cells are honestly NA (None) — never a fabricated 0%. At least one
    cell must be NA at latest (the long horizons cannot be realized yet)."""
    with TestClient(main.app) as client:
        themes = client.get("/api/themes").json()  # no as_of -> latest run
    na_count = sum(
        1 for row in themes["rows"] for fr in row["forward_returns"] if fr["return"] is None
    )
    assert na_count > 0, "expected at least one honestly-NA forward return at the latest run"


def test_sectors_forward_returns_na_at_latest(loaded_engine):
    """J-81 / No-fabricated-data: same NA-honesty for /api/sectors at the latest run."""
    with TestClient(main.app) as client:
        sectors = client.get("/api/sectors").json()
    na_count = sum(
        1 for row in sectors["rows"] for fr in row["forward_returns"] if fr["return"] is None
    )
    assert na_count > 0, "expected at least one honestly-NA forward return at the latest run"


def test_themes_forward_returns_equal_weight_member_basket(loaded_engine):
    """J-81: a theme's forward return at a horizon is the EQUAL-WEIGHT mean of its member stocks' stored
    forward returns over ONLY members with a stored return (absent members skipped, never counted as 0).
    Verified directly against the per-stock forward returns served on /api/stocks for the same date."""
    cfg = load_config()
    with TestClient(main.app) as client:
        oldest = _oldest_run_date(client)
        themes = client.get("/api/themes", params={"as_of": oldest}).json()
        stocks = client.get("/api/stocks", params={"as_of": oldest}).json()
    # {(ticker, horizon): return} from the per-stock forward returns
    stock_ret = {}
    for row in stocks["rows"]:
        for fr in row["forward_returns"]:
            stock_ret[(row["ticker"], fr["horizon"])] = fr["return"]
    checked = 0
    for theme in themes["rows"]:
        members = theme["members"]
        for fr in theme["forward_returns"]:
            h = fr["horizon"]
            present = [
                stock_ret[(m, h)] for m in members
                if (m, h) in stock_ret and stock_ret[(m, h)] is not None
            ]
            if not present:
                assert fr["return"] is None  # no member has a stored return -> NA (not 0)
            else:
                expected = sum(present) / len(present)
                assert fr["return"] is not None
                assert abs(fr["return"] - expected) < 1e-9, (
                    f"{theme['slug']} h={h}: got {fr['return']} expected {expected}"
                )
                checked += 1
    assert checked > 0, "expected at least one populated theme basket to verify"


# ==================================================================================================
# J-82(c) — Regime × Setup × Pattern samples validation reconciliation
# ==================================================================================================
def test_rsp_samples_accepts_every_emitted_combination_pooled(loaded_engine):
    """J-82(c) KEYSTONE (Pooled): the /research/samples drill-down accepts EVERY combination the study
    emits (INCLUDING `pattern = none`) without a 4xx, and the drill-down `total` EQUALS the row's
    published `n` — count-coherent by construction (same observation set, same membership rule)."""
    _assert_every_emitted_combination_coherent(view="pooled")


def test_rsp_samples_accepts_every_emitted_combination_episodes(loaded_engine):
    """J-82(c) KEYSTONE (Episodes): same as Pooled but under the first-trigger episode collapse."""
    _assert_every_emitted_combination_coherent(view="episodes")


def _assert_every_emitted_combination_coherent(view: str) -> None:
    with TestClient(main.app) as client:
        study = client.get(
            "/api/research/regime-setup-pattern", params={"horizon": 20, "view": view}
        ).json()
        saw_pattern_none = False
        checked = 0
        for r in study["rows"]:
            params = {
                "kind": "regime-setup-pattern", "horizon": 20, "view": view,
                "regime": r["regime"], "setup": r["setup"], "pattern": r["pattern"],
            }
            resp = client.get("/api/research/samples", params=params)
            assert resp.status_code == 200, (
                f"emitted combination {(r['regime'], r['setup'], r['pattern'])} should not 4xx, "
                f"got {resp.status_code}: {resp.text}"
            )
            s = resp.json()
            assert s["total"] == r["stats"]["n"], (
                f"{view} {(r['regime'], r['setup'], r['pattern'])}: "
                f"study n={r['stats']['n']} samples total={s['total']}"
            )
            if r["pattern"] == study["pattern_none"]:
                saw_pattern_none = True
            checked += 1
        assert checked > 0, "expected at least one emitted combination row"
        # the seed always yields observations with no detected pattern -> a `pattern = none` row exists,
        # and it must NOT 4xx (the J-82(c) reconciliation keystone).
        assert saw_pattern_none, "expected at least one `pattern = none` combination row"


def test_rsp_samples_pattern_none_drilldown_no_4xx(loaded_engine):
    """J-82(c): explicitly exercise a `pattern = none` row's N= chip drill-down end-to-end — it opens
    the exact cohort without a 4xx and is count-coherent. This is the precise defect J-82 fixes."""
    with TestClient(main.app) as client:
        study = client.get(
            "/api/research/regime-setup-pattern", params={"horizon": 20, "view": "pooled"}
        ).json()
        none_rows = [r for r in study["rows"] if r["pattern"] == study["pattern_none"] and r["stats"]["n"] > 0]
        assert none_rows, "expected at least one non-empty `pattern = none` combination"
        r = none_rows[0]
        resp = client.get(
            "/api/research/samples",
            params={
                "kind": "regime-setup-pattern", "horizon": 20, "view": "pooled",
                "regime": r["regime"], "setup": r["setup"], "pattern": study["pattern_none"],
            },
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == r["stats"]["n"]
    # every member row honestly reports pattern = none
    for row in body["rows"]:
        assert row["pattern"] == study["pattern_none"]


def test_rsp_samples_count_coherent_as_of_scoped(loaded_engine):
    """J-82(c): count-coherence (total == n) holds under the As-of (point-in-time) scope too — the same
    single global as-of filter threaded into the SAME observation builder."""
    with TestClient(main.app) as client:
        oldest = _oldest_run_date(client)
        study = client.get(
            "/api/research/regime-setup-pattern",
            params={"horizon": 20, "view": "pooled", "as_of": oldest},
        ).json()
        for r in study["rows"]:
            if r["stats"]["n"] == 0:
                continue
            s = client.get(
                "/api/research/samples",
                params={
                    "kind": "regime-setup-pattern", "horizon": 20, "view": "pooled", "as_of": oldest,
                    "regime": r["regime"], "setup": r["setup"], "pattern": r["pattern"],
                },
            ).json()
            assert s["total"] == r["stats"]["n"], (
                f"as-of {(r['regime'], r['setup'], r['pattern'])}: "
                f"study n={r['stats']['n']} samples total={s['total']}"
            )


def test_rsp_samples_genuinely_invalid_combination_still_4xx(loaded_engine):
    """J-82(c): acceptance is WIDENED to emitted combinations, NOT disabled — a genuinely non-emitted
    (regime, setup, pattern) combination still returns an honest 4xx (never a silent empty 200)."""
    with TestClient(main.app) as client:
        resp = client.get(
            "/api/research/samples",
            params={"kind": "regime-setup-pattern", "horizon": 20,
                    "regime": "Bogus", "setup": "Actionable", "pattern": "vcp"},
        )
    assert resp.status_code == 422, resp.text
