"""Permanent validation suite for the LIVE ~30-year Stooq seed basis (`data/seed/`).

History: iter-16 staged the 548-pool equities span offline (`data/seed-stooq-30y/`), iter-17
completed its index/macro context, and iter-18 executed the ATOMIC basis swap — the staged prices
tree became `data/seed/prices/` verbatim and the staging directory was retired (read by nothing).
This suite RETARGETS the staged-tree validation to the live seed as the permanent basis validation
(the two-tree comparison tests — cross-vendor return agreement, proxy byte-identity vs live, the
VIX XOR state, and the swap-completeness gate — did their job pre-swap and are retired with the
staging twin; their pre-swap green runs are in git history).

Validates the committed data asset itself:
  * schema identity + structural integrity for EVERY seed CSV (canonical header, strictly
    ascending unique dates, positive prices, non-negative volumes);
  * depth/honesty anchors — long-tenured names reach the first 1996 week; NVDA starts at its REAL
    1999 IPO (not a padded 1996); post-IPO names (COIN/ARM/HOOD) are honestly short and NEVER
    predate their real listing; nothing leaks before the pinned window start (No fabricated data);
  * split continuity — no ~10x/~4x one-day close seam across NVDA 2024-06-10 / AAPL 2020-08-31
    (the whole span is one consistent back-adjusted basis);
  * manifest agreement — meta.json's per-symbol coverage matches the CSVs on disk exactly, with
    the iter-18 basis-swap provenance record present;
  * index/macro context (goal.md §H): _SPX/_NDX/_DJI deep + daily + window-clipped with no
    fabricated-looking flat runs; _TNX/_DXY/_VXN are the app's deterministic FRED-macro PROXIES,
    coherent with `data/seed/macro/` (never a market-index splice); per-series vendor disclosure.
"""
from __future__ import annotations

import csv
import json
from datetime import date, timedelta
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
SEED_DIR = BACKEND_DIR / "data" / "seed"
SEED_PRICES = SEED_DIR / "prices"
MACRO_DIR = SEED_DIR / "macro"

CSV_HEADER = ["date", "open", "high", "low", "close", "volume"]

# Depth / honesty anchors (spec-pinned facts about the real market, not tunables)
DEPTH_ANCHOR = date(1996, 1, 5)          # AAPL + MSFT traded through 1996: first bar <= this
NVDA_IPO_YEAR = 1999                      # NVDA listed 1999-01-22 — a 1996 first bar = fabrication
POST_IPO_LISTINGS = {                     # first bar in [listing, listing + tolerance], never BEFORE
    "COIN": date(2021, 4, 14),
    "ARM": date(2023, 9, 14),
    "HOOD": date(2021, 7, 29),
}
POST_IPO_TOLERANCE_DAYS = 14              # small allowance for a vendor's first covered session
SPLIT_DAYS = {"NVDA": date(2024, 6, 10), "AAPL": date(2020, 8, 31)}
MAX_SPLIT_DAY_MOVE = 0.25                 # far above a real daily move, far below a split seam

# iter-17/18 context expectations (goal.md §H; spec-pinned facts about the committed basis)
PINNED_WINDOW = {"start": "1996-01-01", "end": "2026-07-01"}
WORLD_INDEX_FILES = ("_SPX", "_NDX", "_DJI")       # vendor stooq (world indices bundle)
PROXY_FILES = ("_TNX", "_DXY", "_VXN")             # vendor fred-macro-proxy (macro-coherent series)
CONTEXT_VENDORS = {
    "^SPX": "stooq", "^NDX": "stooq", "^DJI": "stooq",
    "^VIX": "yahoo",
    "^TNX": "fred-macro-proxy", "^DXY": "fred-macro-proxy", "^VXN": "fred-macro-proxy",
}
EXPECTED_PLANNED = 591                             # 588 (pool ∪ context) + ^SPX/^NDX/^DJI
EXPECTED_OK = 590                                  # 583 equities + 7 context series
EXPECTED_FAILED = ["SATS"]                         # the one remaining honest absence
MIN_DEEP_INDEX_BARS = 7000                         # ~252 trading days x 30.5y ≈ 7690 (not monthly)
MAX_FLAT_OHLC_RUN = 2                              # >=3 consecutive flat-OHLC bars looks fabricated
TNX_CREDIT_SPREAD_SCALE = 5.0                      # the deterministic _TNX = credit_spread x 5 proxy
PROXY_VALUE_ABS_TOL = 1e-9                         # float-parse tolerance for exact decimal values


def _read_series(path: Path) -> tuple[list[date], list[float]]:
    dates: list[date] = []
    closes: list[float] = []
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            dates.append(date.fromisoformat(row["date"]))
            closes.append(float(row["close"]))
    return dates, closes


def _first_bar_date(path: Path) -> date:
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        first = next(reader)
        return date.fromisoformat(first["date"])


def _read_rows(path: Path) -> list[dict]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _read_macro(series_id: str) -> dict[str, float]:
    out: dict[str, float] = {}
    with (MACRO_DIR / f"{series_id}.csv").open(newline="") as fh:
        for row in csv.DictReader(fh):
            out[row["date"]] = float(row["value"])
    return out


def test_seed_csvs_schema_ascending_positive_volumes():
    """One streaming pass over EVERY seed CSV: canonical header; >=1 row; strictly ascending
    unique dates; strictly positive OHLC; non-negative integer volumes; no pre-window leakage."""
    files = sorted(SEED_PRICES.glob("*.csv"))
    assert len(files) == EXPECTED_OK, f"expected {EXPECTED_OK} committed price CSVs, found {len(files)}"
    window_start = date.fromisoformat(PINNED_WINDOW["start"])
    for path in files:
        with path.open(newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            assert header == CSV_HEADER, f"{path.name}: header {header}"
            prev: date | None = None
            rows = 0
            for row in reader:
                rows += 1
                d = date.fromisoformat(row[0])
                if prev is None:
                    assert d >= window_start, f"{path.name}: pre-window leakage — first bar {d}"
                else:
                    assert d > prev, f"{path.name}: dates not strictly ascending at {d}"
                prev = d
                o, h, low, c = (float(row[1]), float(row[2]), float(row[3]), float(row[4]))
                assert min(o, h, low, c) > 0, f"{path.name}: non-positive price on {d}"
                assert int(row[5]) >= 0, f"{path.name}: negative volume on {d}"
            assert rows >= 1, f"{path.name}: empty series (must be omitted, not committed empty)"


def test_depth_anchor_long_tenured_names():
    """AAPL and MSFT traded through 1996 — the full-depth basis must reach the first 1996
    trading week for both."""
    for symbol in ("AAPL", "MSFT"):
        path = SEED_PRICES / f"{symbol}.csv"
        assert path.exists(), f"{symbol} missing from the seed"
        first = _first_bar_date(path)
        assert first <= DEPTH_ANCHOR, f"{symbol} first bar {first} shallower than {DEPTH_ANCHOR}"


def test_nvda_first_bar_is_real_1999_ipo():
    """NVDA listed 1999-01-22. A first bar in 1996 would be FABRICATED depth; a first bar after
    1999 would be missing real history. Honest = first bar inside 1999."""
    first = _first_bar_date(SEED_PRICES / "NVDA.csv")
    assert first.year == NVDA_IPO_YEAR, f"NVDA first bar {first} is not its real 1999 IPO"


def test_post_ipo_names_honestly_short():
    """COIN/ARM/HOOD carry ONLY their real short history: the first bar never PRECEDES the
    real listing date (no fabricated early rows) and starts within a small tolerance after it."""
    for symbol, listing in POST_IPO_LISTINGS.items():
        path = SEED_PRICES / f"{symbol}.csv"
        assert path.exists(), f"{symbol} missing from the seed"
        first = _first_bar_date(path)
        assert first >= listing, f"{symbol} first bar {first} PRECEDES its {listing} listing"
        assert first <= listing + timedelta(days=POST_IPO_TOLERANCE_DAYS), (
            f"{symbol} first bar {first} too far after its {listing} listing"
        )


def test_split_continuity_across_known_splits():
    """The basis must be back-adjusted end-to-end: the NVDA 2024-06-10 (10:1) and AAPL
    2020-08-31 (4:1) split days must show a NORMAL 1-day close move, not a ~-90%/-75% seam."""
    for symbol, split_day in SPLIT_DAYS.items():
        dates, closes = _read_series(SEED_PRICES / f"{symbol}.csv")
        assert split_day in dates, f"{symbol}: split day {split_day} absent from the series"
        i = dates.index(split_day)
        assert i > 0, f"{symbol}: no bar before the split day"
        move = closes[i] / closes[i - 1] - 1.0
        assert abs(move) < MAX_SPLIT_DAY_MOVE, (
            f"{symbol}: {move:+.2%} one-day close move across {split_day} — unadjusted seam"
        )


def test_manifest_agreement_with_disk():
    """meta.json is the basis manifest AND coverage record: every `symbols` entry matches its
    CSV's real first/last/bars exactly; every seed CSV has an entry; recorded-absent symbols
    have NO CSV (honestly omitted, never padded); the iter-18 basis-swap provenance is recorded."""
    meta = json.loads((SEED_DIR / "meta.json").read_text())
    assert meta["provider"] == "stooq"
    assert meta["window"] == PINNED_WINDOW, "the pinned window changed — the basis must not re-pin"
    # iter-18: the sanctioned-swap provenance record (the retired basis stays auditable via git)
    assert meta["basis_swap"]["iteration"] == "goal-mcp-loop-iter-18"
    assert "sanctioned" in meta["basis_swap"]["note"]

    on_disk = {p.stem for p in SEED_PRICES.glob("*.csv")}
    listed = {e["symbol"].replace("^", "_").upper() for e in meta["symbols"]}
    assert listed == on_disk, (
        f"manifest/disk mismatch: only-in-manifest={sorted(listed - on_disk)} "
        f"only-on-disk={sorted(on_disk - listed)}"
    )

    for entry in meta["symbols"]:
        filename = entry["symbol"].replace("^", "_").upper() + ".csv"
        dates, _ = _read_series(SEED_PRICES / filename)
        assert entry["bars"] == len(dates), f"{entry['symbol']}: bars {entry['bars']} != {len(dates)}"
        assert entry["first"] == dates[0].isoformat(), f"{entry['symbol']}: first mismatch"
        assert entry["last"] == dates[-1].isoformat(), f"{entry['symbol']}: last mismatch"

    for failure in meta.get("failures", []):
        filename = failure["symbol"].replace("^", "_").upper() + ".csv"
        assert not (SEED_PRICES / filename).exists(), (
            f"{failure['symbol']} recorded absent but has a committed CSV"
        )


# ---------------------------------------------------------------------------
# index & macro context (goal.md §H) — deep world indexes + macro-coherent proxies
# ---------------------------------------------------------------------------

def test_context_indexes_deep_window_clipped_pinned_end_no_flat_runs():
    """_SPX/_NDX/_DJI are DEEP world-bundle series over the pinned window: first bar inside the
    first 1996 trading week (clip proven — the archive's 1789/1938/1896 flat/monthly rows never
    leak), last bar == the manifest's pinned end (a real trading day), daily density (not a
    monthly-cadence relic), and no fabricated-looking flat-OHLC run inside the window."""
    meta = json.loads((SEED_DIR / "meta.json").read_text())
    pinned_end = date.fromisoformat(meta["window"]["end"])
    for name in WORLD_INDEX_FILES:
        path = SEED_PRICES / f"{name}.csv"
        assert path.exists(), f"{name}.csv missing from the seed context"
        rows = _read_rows(path)
        first = date.fromisoformat(rows[0]["date"])
        last = date.fromisoformat(rows[-1]["date"])
        assert first >= date.fromisoformat(PINNED_WINDOW["start"]), (
            f"{name}: pre-window leakage — first bar {first}"
        )
        assert first <= DEPTH_ANCHOR, f"{name}: not deep — first bar {first}"
        assert last == pinned_end == date.fromisoformat(PINNED_WINDOW["end"]), (
            f"{name}: last bar {last} != the manifest's pinned end {pinned_end}"
        )
        assert len(rows) >= MIN_DEEP_INDEX_BARS, (
            f"{name}: only {len(rows)} bars over the 30y window — not a daily series"
        )
        flat_run = longest = 0
        for r in rows:
            flat = r["open"] == r["high"] == r["low"] == r["close"]
            flat_run = flat_run + 1 if flat else 0
            longest = max(longest, flat_run)
        assert longest <= MAX_FLAT_OHLC_RUN, (
            f"{name}: {longest} consecutive flat-OHLC bars in-window — fabricated-looking run"
        )


def test_fred_macro_proxies_coherent_with_seed_macro():
    """_TNX/_DXY/_VXN are the app's deterministic FRED-macro PROXIES — flat-OHLC series that stay
    coherent with `data/seed/macro/` (goal.md §H: a market-index re-fetch would DESYNC them from
    the FRED macro the app displays and silently change their meaning):
      * every proxy bar is flat OHLC (open == high == low == close) with volume 0 — a value series
        riding daily_prices, never a fabricated market-price series;
      * _DXY equals `macro/dollar_index` EXACTLY on every proxy date;
      * _TNX equals `macro/credit_spread` × 5 EXACTLY on every proxy date (the committed transform)."""
    for name in PROXY_FILES:
        rows = _read_rows(SEED_PRICES / f"{name}.csv")
        assert rows, f"{name}: empty proxy series"
        for r in rows:
            assert r["open"] == r["high"] == r["low"] == r["close"], (
                f"{name}: non-flat OHLC on {r['date']} — a proxy is a value series, not market bars"
            )
            assert float(r["volume"]) == 0, f"{name}: nonzero volume on {r['date']}"

    dollar = _read_macro("dollar_index")
    for r in _read_rows(SEED_PRICES / "_DXY.csv"):
        assert r["date"] in dollar, f"_DXY: {r['date']} has no macro/dollar_index source row"
        assert abs(float(r["close"]) - dollar[r["date"]]) <= PROXY_VALUE_ABS_TOL, (
            f"_DXY {r['date']}: {r['close']} != dollar_index {dollar[r['date']]}"
        )

    credit = _read_macro("credit_spread")
    for r in _read_rows(SEED_PRICES / "_TNX.csv"):
        assert r["date"] in credit, f"_TNX: {r['date']} has no macro/credit_spread source row"
        expected = credit[r["date"]] * TNX_CREDIT_SPREAD_SCALE
        assert abs(float(r["close"]) - expected) <= PROXY_VALUE_ABS_TOL, (
            f"_TNX {r['date']}: {r['close']} != credit_spread x {TNX_CREDIT_SPREAD_SCALE} = {expected}"
        )


def test_manifest_context_vendors_window_pins_and_accounting():
    """Per-series vendor disclosure (goal.md §H): every context series records its vendor
    (stooq / yahoo / fred-macro-proxy) with coverage matching disk; equity records stay untouched
    (vendor = the manifest-level provider tag); the pinned window is unchanged; the
    planned/ok/failed accounting is consistent with SATS the only remaining honest absence."""
    meta = json.loads((SEED_DIR / "meta.json").read_text())
    assert meta["provider"] == "stooq"
    assert meta["window"] == PINNED_WINDOW

    by_symbol = {e["symbol"]: e for e in meta["symbols"]}
    for symbol, vendor in CONTEXT_VENDORS.items():
        entry = by_symbol.get(symbol)
        assert entry is not None, f"{symbol}: no manifest coverage record"
        assert entry.get("vendor") == vendor, (
            f"{symbol}: vendor {entry.get('vendor')!r} != required {vendor!r}"
        )
        rows = _read_rows(SEED_PRICES / (symbol.replace("^", "_").upper() + ".csv"))
        assert entry["bars"] == len(rows), f"{symbol}: manifest bars != disk"
        assert entry["first"] == rows[0]["date"], f"{symbol}: manifest first != disk"
        assert entry["last"] == rows[-1]["date"], f"{symbol}: manifest last != disk"
    assert "vendor" not in by_symbol["AAPL"], "equity records must stay untouched by the merge"
    assert "never presented as a market index" in meta["note"]

    assert meta["failed"] == EXPECTED_FAILED
    assert meta["symbols_planned"] == EXPECTED_PLANNED
    assert meta["symbols_ok"] == EXPECTED_OK == len(meta["symbols"])
    assert meta["symbols_failed"] == len(EXPECTED_FAILED) == len(meta["failures"])
    assert len(list(SEED_PRICES.glob("*.csv"))) == EXPECTED_OK


def test_staging_directory_retired():
    """iter-18: the atomic swap RETIRED the staging tree — `data/seed-stooq-30y/` must not exist
    (the basis lives at `data/seed/`; nothing may quietly resurrect a second price tree)."""
    assert not (BACKEND_DIR / "data" / "seed-stooq-30y").exists(), (
        "data/seed-stooq-30y still exists — the staging tree was retired by the iter-18 swap"
    )
