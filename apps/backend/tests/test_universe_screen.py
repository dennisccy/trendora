"""Universe screen + single-source/consistency tests (iter-7, J-22).

Two layers:
  * PURE screen predicate (`scripts.screen_universe.screen_reasons`) — the three-threshold screen logic
    that resolves membership at build time. Tested with synthetic candidates: a passer passes; a
    candidate below ANY threshold (price / dollar-volume / market-cap), or with no market cap, is
    EXCLUDED with a reason (the failure path — anti-goal: No fabricated data — never silently kept).
  * SINGLE SOURCE / consistency over the REAL committed seed: the resolved universe size is ONE value,
    read identically by `/api/data` (universe_count), `/api/methodology` (universe_selection.resolved_size),
    and `len(config.universe.symbols)` — no drift, no recompute. When the committed screen record
    (`data/seed/universe.json`) is present, every member's stored reference values pass the screen and the
    stored `Stock.market_cap` equals the committed record (read from storage, never recomputed).
"""
from __future__ import annotations

import csv
import json

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.engine.data_manager import compute_coverage
from app.engine.methodology import build_catalog
from app.engine.universe_screen import pool_sector_map, read_pool, resolve_pool_sector
from app.models import Stock
from app.seed_loader import DEFAULT_SEED_DIR, load_universe_screen_record
from scripts.screen_universe import screen_reasons

_FILTERS = dict(min_price=10.0, min_dollar_vol=50_000_000.0, min_market_cap=2_000_000_000.0)


# --- PURE screen predicate (build-time membership logic) ------------------------------------------
def test_screen_passes_a_qualified_candidate():
    assert screen_reasons(150.0, 9.0e8, 3.0e12, **_FILTERS) == []


def test_screen_excludes_below_min_price():
    reasons = screen_reasons(2.0, 9.0e8, 3.0e9, **_FILTERS)
    assert reasons and any("price" in r for r in reasons)


def test_screen_excludes_below_min_dollar_vol():
    reasons = screen_reasons(50.0, 1.0e6, 3.0e9, **_FILTERS)
    assert reasons and any("adv" in r for r in reasons)


def test_screen_excludes_below_min_market_cap():
    reasons = screen_reasons(50.0, 9.0e8, 1.0e9, **_FILTERS)
    assert reasons and any("market_cap" in r for r in reasons)


def test_screen_excludes_missing_market_cap():
    """A candidate whose market cap could not be fetched is omitted (never fabricated)."""
    assert "no_market_cap" in screen_reasons(50.0, 9.0e8, None, **_FILTERS)


def test_screen_reads_only_passed_thresholds():
    """The same candidate flips pass→fail purely from the config thresholds (the screen reads only
    `universe.filters` — no membership literal baked into the predicate)."""
    assert screen_reasons(12.0, 6.0e7, 3.0e9, **_FILTERS) == []
    strict = dict(min_price=15.0, min_dollar_vol=50_000_000.0, min_market_cap=2_000_000_000.0)
    assert screen_reasons(12.0, 6.0e7, 3.0e9, **strict)  # now excluded by the higher min_price


# --- SINGLE SOURCE / consistency over the committed config + seed --------------------------------
def test_universe_size_is_one_value_across_methodology_and_data(loaded_engine, config):
    """iter-33 (J-93): the universe is now POINT-IN-TIME. The STATIC candidate-universe size is read
    identically by /api/methodology (resolved_size) and /api/data (candidate_universe_count) ==
    len(config.universe.symbols) — one source, no drift. The DYNAMIC `universe_count` is the members
    RESOLVED at the as-of (a subset of the candidate universe — names that clear the per-date price/ADV/
    min-history gate), which by construction is <= the candidate count and matches the latest snapshot's
    scored set."""
    candidate = len(config.universe.symbols)
    methodology_size = build_catalog(config)["universe_selection"]["resolved_size"]
    with Session(loaded_engine) as session:
        coverage = compute_coverage(session, config)
        # the dynamic count == the members in the LATEST snapshot's scored set (single source — the
        # persisted ScannerResult rows ARE the membership the resolver admits at that date).
        from app.engine.scanner import _latest_stored_run_date
        from app.models import ScannerRun, ScannerResult
        from sqlmodel import select as _select, func as _func
        latest = _latest_stored_run_date(session)
        latest_run_id = session.scalar(_select(ScannerRun.id).where(ScannerRun.asof_date == latest))
        scored_n = session.scalar(
            _select(_func.count()).select_from(ScannerResult).where(ScannerResult.run_id == latest_run_id)
        )
    # methodology + the static coverage count are the candidate-universe (no drift).
    assert methodology_size == candidate == coverage["candidate_universe_count"]
    # the dynamic universe_count is the as-of-resolved membership == the latest snapshot's scored rows.
    assert coverage["universe_count"] == scored_n
    # iter-18: the dynamic membership resolves from the broadened 548-name pool (read_pool), so it is a
    # subset of the POOL — no longer bounded by the legacy static candidate universe (config.universe.symbols).
    assert 0 < coverage["universe_count"] <= len(read_pool())  # a non-empty subset at a fully-warm date
    # universe_count is the screened universe, NOT the distinct priced-symbol count (which includes ETFs)
    assert coverage["symbol_count"] >= candidate


def test_committed_universe_members_all_pass_screen():
    """Every committed universe member passes all three config thresholds against its stored reference
    values (the recorded screen-pass record is internally consistent — no member sneaked in below a
    threshold). Skips only if the expanded seed record has not been built yet."""
    record_path = DEFAULT_SEED_DIR / "universe.json"
    if not record_path.exists():
        pytest.skip("universe.json (committed screen record) not present yet — run screen_universe.py")
    data = json.loads(record_path.read_text())
    filters = load_config().universe.filters
    members = data["members"]
    assert members, "committed universe record has no members"
    offenders = []
    for member in members:
        reasons = screen_reasons(
            member["reference_close"], member["adv_dollar"], member["market_cap"],
            min_price=filters.min_price, min_dollar_vol=filters.min_dollar_vol,
            min_market_cap=filters.min_market_cap,
        )
        if reasons:
            offenders.append((member["symbol"], reasons))
    assert not offenders, f"committed members that fail the screen: {offenders[:10]}"


def test_committed_record_matches_config_universe():
    """The committed screen record's members ARE the config universe (the build wrote both from the one
    resolved set — no drift between the seed record and config.universe.symbols)."""
    record_path = DEFAULT_SEED_DIR / "universe.json"
    if not record_path.exists():
        pytest.skip("universe.json not present yet")
    data = json.loads(record_path.read_text())
    record_symbols = {m["symbol"] for m in data["members"]}
    assert record_symbols == set(load_config().universe.symbols)


def test_stock_market_cap_read_from_committed_record(loaded_engine):
    """`Stock.market_cap` is populated from the committed screen record (read from storage, never
    recomputed in the API/view). Skips only until the record is built."""
    caps = load_universe_screen_record(DEFAULT_SEED_DIR)
    if not caps:
        pytest.skip("no committed market caps yet (universe.json absent)")
    with Session(loaded_engine) as session:
        sample = list(caps.items())[:25]
        for ticker, expected_cap in sample:
            stock = session.scalar(select(Stock).where(Stock.ticker == ticker))
            assert stock is not None, f"{ticker} missing from stocks table"
            assert stock.market_cap == expected_cap, (
                f"{ticker} stored market_cap {stock.market_cap} != committed record {expected_cap}"
            )


# --- J-01 (goal-market-compass iter-1): the pool-CSV sector fallback ------------------------------
# `resolve_pool_sector` (one raw name -> a validated sector or None) and `pool_sector_map` (the whole
# pool, ticker -> resolved sector) are the SINGLE normalization seam `scoring.score_stocks` reads
# AFTER the curated `config.stock_sectors` map (curated always wins — see test_scoring.py's
# byte-identity fixture for proof the fallback never touches a score/bucket/setup_status).

def _write_pool_csv(tmp_path, rows: list[dict]):
    """A synthetic `universe_pool.csv` under `tmp_path`, in the same shape `read_pool` parses
    (header `symbol,sector,source`; comment lines stripped by `read_pool` itself, not needed here)."""
    path = tmp_path / "universe_pool.csv"
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["symbol", "sector", "source"])
        writer.writeheader()
        writer.writerows(rows)
    return tmp_path


def test_resolve_pool_sector_identity_when_no_alias_configured():
    """TC-6: with no alias entry for a raw pool sector name, the resolved value equals the raw value
    unchanged — today's REAL behavior (the pool's 11 sector names already equal `etfs.sector`'s 11
    names verbatim, so `universe.pool_sector_aliases` stays a legitimate empty/no-op map)."""
    valid = set(load_config().etfs.sector.values())
    assert "Technology" in valid
    assert resolve_pool_sector("Technology", aliases={}, valid_sectors=valid) == "Technology"


def test_resolve_pool_sector_applies_a_configured_alias():
    """A configured alias DOES substitute (proving the normalization seam works even though today's
    real config leaves it empty) — the ALIASED name still has to pass the valid-sectors check."""
    assert (
        resolve_pool_sector("Tech", aliases={"Tech": "Technology"}, valid_sectors={"Technology"})
        == "Technology"
    )


def test_resolve_pool_sector_unresolvable_name_degrades_to_none():
    """TC-7 (AG-8 resilience): a pool sector name (after alias normalization) that is not a member of
    `etfs.sector`'s valid set degrades to None — never raises, never serves an unrecognized string."""
    assert resolve_pool_sector("Not A Real Sector", aliases={}, valid_sectors={"Technology"}) is None
    # an alias that itself points at an invalid name degrades the same way (never a stray string)
    assert (
        resolve_pool_sector("Tech", aliases={"Tech": "Not Real Either"}, valid_sectors={"Technology"})
        is None
    )


def test_resolve_pool_sector_missing_or_blank_raw_value_is_none():
    """TC-3 (unit half): a missing/blank raw sector value is honestly None, never fabricated."""
    assert resolve_pool_sector(None, aliases={}, valid_sectors={"Technology"}) is None
    assert resolve_pool_sector("", aliases={}, valid_sectors={"Technology"}) is None


def test_pool_sector_map_covers_the_real_committed_pool_with_identity_aliases():
    """TC-6 (map-level, real data): with the REAL config's default-empty `pool_sector_aliases`, every
    one of the committed pool's 548 rows resolves — the map is a straight, un-aliased read of
    `universe_pool.csv`'s `sector` column (the pool's 11 sector names already equal `etfs.sector`'s 11
    verbatim)."""
    cfg = load_config()
    assert cfg.universe.pool_sector_aliases == {}  # today's committed config: a genuine no-op default
    mapping = pool_sector_map(aliases=cfg.universe.pool_sector_aliases, valid_sectors=cfg.etfs.sector.values())
    pool = read_pool()
    assert len(pool) == 548
    assert len(mapping) == len(pool)
    by_symbol = {row["symbol"]: row["sector"] for row in pool}
    for symbol, sector in mapping.items():
        assert sector == by_symbol[symbol]  # identity — no alias substitution applied (TC-6)


def test_pool_sector_map_degrades_unresolvable_row_gracefully(tmp_path):
    """TC-7: a synthetic pool with one row whose sector is outside the valid set is simply absent from
    the resolved map (never raises, never a stray/unrecognized string) — a normal row alongside it
    still resolves fine (AG-8: the bad row doesn't take down the whole map)."""
    seed_dir = _write_pool_csv(
        tmp_path,
        [
            {"symbol": "ZZZFAKE", "sector": "Not A Real Sector", "source": "test"},
            {"symbol": "ZZZOK", "sector": "Technology", "source": "test"},
            {"symbol": "ZZZBLANK", "sector": "", "source": "test"},
        ],
    )
    mapping = pool_sector_map(aliases={}, valid_sectors={"Technology"}, seed_dir=seed_dir)
    assert mapping == {"ZZZOK": "Technology"}
    assert "ZZZFAKE" not in mapping
    assert "ZZZBLANK" not in mapping


def test_pool_sector_map_ticker_outside_the_pool_is_simply_absent(tmp_path):
    """TC-3 (map-level): a ticker not present in the pool at all is not a key in the map — the
    caller's `.get(ticker)` then honestly returns None (never fabricated)."""
    seed_dir = _write_pool_csv(tmp_path, [{"symbol": "ZZZOK", "sector": "Technology", "source": "test"}])
    mapping = pool_sector_map(aliases={}, valid_sectors={"Technology"}, seed_dir=seed_dir)
    assert mapping.get("SOME_UNKNOWN_TICKER") is None


def test_pool_sector_map_missing_pool_file_degrades_to_empty_map(tmp_path):
    """A not-yet-built pool file degrades to an empty map (never a crash) — the same honest-empty
    contract `read_pool`'s other callers already tolerate for a missing `universe_pool.csv`."""
    assert pool_sector_map(aliases={}, valid_sectors={"Technology"}, seed_dir=tmp_path) == {}
