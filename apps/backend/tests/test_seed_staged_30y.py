"""Validation suite for the STAGED ~30-year Stooq seed (`data/seed-stooq-30y/`) — iter-16 Part A
(equities) + iter-17 Part A2 (index & macro context) of the sanctioned data-basis migration. The
staged tree is read by NOTHING at runtime; these tests validate the committed data asset itself:

  * schema identity + structural integrity for EVERY staged CSV (canonical header, strictly
    ascending unique dates, positive prices, non-negative volumes);
  * depth/honesty anchors — long-tenured names reach the first 1996 week; NVDA starts at its REAL
    1999 IPO (not a padded 1996); post-IPO names (COIN/ARM/HOOD) are honestly short and NEVER
    predate their real listing (anti-goal: No fabricated data);
  * split continuity — no ~10x/~4x one-day close seam across NVDA 2024-06-10 / AAPL 2020-08-31
    (the whole span must be one consistent back-adjusted basis);
  * cross-vendor sanity — staged daily returns agree with the committed live (Yahoo) seed over
    the 2021-01 -> 2026-05 overlap (both bases are fully adjusted, so returns must match);
  * manifest agreement — meta.json's per-symbol coverage matches the CSVs on disk exactly;
  * iter-17 context (goal.md §H): _SPX/_NDX/_DJI deep from Stooq's world bundle (window-clipped,
    last bar == the pinned end, no fabricated-looking flat runs); _TNX/_DXY/_VXN byte-identical
    FRED-macro-proxy copies of the live seed (NEVER a Yahoo re-fetch); _VIX either the deep Yahoo
    single pull XOR the sanctioned verbatim live copy (never a hybrid/splice); per-series vendor
    disclosure in the manifest; and SWAP-COMPLETENESS (staged price-file set ⊇ the live seed's)
    — the load-bearing gate for the iter-18 atomic basis swap.

SKIPS (honestly, with the reason below) only while the staged directory is absent — the staged
asset is a COMMITTED tree, so absence means a partial checkout/clean, not a data condition.
"""
from __future__ import annotations

import csv
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
STAGED_DIR = BACKEND_DIR / "data" / "seed-stooq-30y"
STAGED_PRICES = STAGED_DIR / "prices"
LIVE_SEED_PRICES = BACKEND_DIR / "data" / "seed" / "prices"

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

# Cross-vendor agreement bounds (documented allowances for vendor rounding — a violated bound is
# an honest basis problem to surface, not to tolerate):
RETURN_MEDIAN_ABS_DIFF = 1e-3             # typical day: returns effectively identical
RETURN_OUTLIER_ABS_DIFF = 0.005           # a day differing by >0.5% is a vendor discrepancy…
RETURN_OUTLIER_MAX_FRACTION = 0.02        # …allowed only for a rare few sessions
RETURN_MAX_ABS_DIFF = 0.10                # any unadjusted split seam (~0.75-0.9) fails loudly
TOTAL_RETURN_RATIO_TOL = 0.02             # cumulative overlap return within 2% (catches a
                                          # dividend-unadjusted basis: SPY ~7%, AAPL ~3% drift)

pytestmark = pytest.mark.skipif(
    not (STAGED_PRICES.is_dir() and (STAGED_DIR / "meta.json").exists()),
    reason=(
        "staged 30y Stooq seed absent at data/seed-stooq-30y — it is a COMMITTED asset (staged "
        "iter-16 from the local bulk archive, context-completed iter-17), so absence means a "
        "partial checkout/clean, not a data condition. The suite validates the committed tree."
    ),
)

# iter-17 context expectations (goal.md §H; spec-pinned facts about the committed staged asset)
PINNED_WINDOW = {"start": "1996-01-01", "end": "2026-07-01"}
WORLD_INDEX_FILES = ("_SPX", "_NDX", "_DJI")       # vendor stooq (world indices bundle)
PROXY_FILES = ("_TNX", "_DXY", "_VXN")             # vendor fred-macro-proxy (live-seed copies)
CONTEXT_VENDORS = {
    "^SPX": "stooq", "^NDX": "stooq", "^DJI": "stooq",
    "^VIX": "yahoo",
    "^TNX": "fred-macro-proxy", "^DXY": "fred-macro-proxy", "^VXN": "fred-macro-proxy",
}
EXPECTED_PLANNED = 591                             # 588 (iter-16) + ^SPX/^NDX/^DJI
EXPECTED_OK = 590                                  # 583 equities + 7 context series
EXPECTED_FAILED = ["SATS"]                         # the one remaining honest absence
MIN_DEEP_INDEX_BARS = 7000                         # ~252 trading days x 30.5y ≈ 7690 (not monthly)
MAX_VIX_GAP_DAYS = 14                              # no US-market closure exceeds this (9/11: 7d)
MAX_FLAT_OHLC_RUN = 2                              # >=3 consecutive flat-OHLC bars looks fabricated
LIVE_VIX_LAST = date(2026, 5, 28)                  # the live copy's last bar (fallback coverage)


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


def test_staged_csvs_schema_ascending_positive_volumes():
    """One streaming pass over EVERY staged CSV: canonical header; >=1 row; strictly ascending
    unique dates; strictly positive OHLC; non-negative integer volumes."""
    files = sorted(STAGED_PRICES.glob("*.csv"))
    assert files, "staged prices dir exists but holds no CSVs"
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
                if prev is not None:
                    assert d > prev, f"{path.name}: dates not strictly ascending at {d}"
                prev = d
                o, h, low, c = (float(row[1]), float(row[2]), float(row[3]), float(row[4]))
                assert min(o, h, low, c) > 0, f"{path.name}: non-positive price on {d}"
                assert int(row[5]) >= 0, f"{path.name}: negative volume on {d}"
            assert rows >= 1, f"{path.name}: empty series (must be omitted, not staged empty)"


def test_depth_anchor_long_tenured_names():
    """AAPL and MSFT traded through 1996 — a full-depth staged feed must reach the first 1996
    trading week for both."""
    for symbol in ("AAPL", "MSFT"):
        path = STAGED_PRICES / f"{symbol}.csv"
        assert path.exists(), f"{symbol} missing from the staged seed"
        first = _first_bar_date(path)
        assert first <= DEPTH_ANCHOR, f"{symbol} first bar {first} shallower than {DEPTH_ANCHOR}"


def test_nvda_first_bar_is_real_1999_ipo():
    """NVDA listed 1999-01-22. A first bar in 1996 would be FABRICATED depth; a first bar after
    1999 would be missing real history. Honest = first bar inside 1999."""
    first = _first_bar_date(STAGED_PRICES / "NVDA.csv")
    assert first.year == NVDA_IPO_YEAR, f"NVDA first bar {first} is not its real 1999 IPO"


def test_post_ipo_names_honestly_short():
    """COIN/ARM/HOOD carry ONLY their real short history: the first staged bar never PRECEDES the
    real listing date (no fabricated early rows) and starts within a small tolerance after it."""
    for symbol, listing in POST_IPO_LISTINGS.items():
        path = STAGED_PRICES / f"{symbol}.csv"
        assert path.exists(), f"{symbol} missing from the staged seed"
        first = _first_bar_date(path)
        assert first >= listing, f"{symbol} first bar {first} PRECEDES its {listing} listing"
        assert first <= listing + timedelta(days=POST_IPO_TOLERANCE_DAYS), (
            f"{symbol} first bar {first} too far after its {listing} listing"
        )


def test_split_continuity_across_known_splits():
    """The staged basis must be back-adjusted end-to-end: the NVDA 2024-06-10 (10:1) and AAPL
    2020-08-31 (4:1) split days must show a NORMAL 1-day close move, not a ~-90%/-75% seam."""
    for symbol, split_day in SPLIT_DAYS.items():
        dates, closes = _read_series(STAGED_PRICES / f"{symbol}.csv")
        assert split_day in dates, f"{symbol}: split day {split_day} absent from staged series"
        i = dates.index(split_day)
        assert i > 0, f"{symbol}: no bar before the split day"
        move = closes[i] / closes[i - 1] - 1.0
        assert abs(move) < MAX_SPLIT_DAY_MOVE, (
            f"{symbol}: {move:+.2%} one-day close move across {split_day} — unadjusted seam"
        )


def test_cross_vendor_returns_agree_with_live_seed():
    """Both the staged (Stooq) and live (Yahoo) bases are fully split/dividend back-adjusted, so
    DAILY RETURNS on common dates must agree. Bounds are documented vendor-rounding allowances —
    a systematic violation (e.g. a dividend-unadjusted basis) must FAIL here, not be absorbed."""
    for symbol in ("AAPL", "NVDA", "SPY"):
        staged_dates, staged_closes = _read_series(STAGED_PRICES / f"{symbol}.csv")
        live_dates, live_closes = _read_series(LIVE_SEED_PRICES / f"{symbol}.csv")
        staged = dict(zip(staged_dates, staged_closes))
        live = dict(zip(live_dates, live_closes))
        common = sorted(set(staged) & set(live))
        assert len(common) > 1000, f"{symbol}: only {len(common)} overlapping dates"

        diffs: list[float] = []
        for prev_d, d in zip(common, common[1:]):
            r_staged = staged[d] / staged[prev_d] - 1.0
            r_live = live[d] / live[prev_d] - 1.0
            diffs.append(abs(r_staged - r_live))
        diffs.sort()
        median = diffs[len(diffs) // 2]
        outliers = sum(1 for x in diffs if x > RETURN_OUTLIER_ABS_DIFF)
        assert median < RETURN_MEDIAN_ABS_DIFF, f"{symbol}: median |Δreturn| {median:.5f}"
        assert outliers / len(diffs) < RETURN_OUTLIER_MAX_FRACTION, (
            f"{symbol}: {outliers}/{len(diffs)} days differ by >{RETURN_OUTLIER_ABS_DIFF:.3f}"
        )
        assert diffs[-1] < RETURN_MAX_ABS_DIFF, f"{symbol}: max |Δreturn| {diffs[-1]:.4f} (seam?)"

        total_staged = staged[common[-1]] / staged[common[0]]
        total_live = live[common[-1]] / live[common[0]]
        ratio = total_staged / total_live - 1.0
        assert abs(ratio) < TOTAL_RETURN_RATIO_TOL, (
            f"{symbol}: cumulative overlap return drifts {ratio:+.2%} vs the live seed — "
            f"suggests a different adjustment basis (e.g. dividends)"
        )


def test_manifest_agreement_with_disk():
    """meta.json is the staging manifest AND coverage record: every `symbols` entry matches its
    CSV's real first/last/bars exactly; every staged CSV has an entry; recorded-absent symbols
    have NO CSV (honestly omitted, never padded)."""
    meta = json.loads((STAGED_DIR / "meta.json").read_text())
    assert meta["provider"] == "stooq"
    assert meta["window"]["start"] and meta["window"]["end"]  # the pinned window is recorded

    on_disk = {p.stem for p in STAGED_PRICES.glob("*.csv")}
    listed = {e["symbol"].replace("^", "_").upper() for e in meta["symbols"]}
    assert listed == on_disk, (
        f"manifest/disk mismatch: only-in-manifest={sorted(listed - on_disk)} "
        f"only-on-disk={sorted(on_disk - listed)}"
    )

    for entry in meta["symbols"]:
        filename = entry["symbol"].replace("^", "_").upper() + ".csv"
        dates, _ = _read_series(STAGED_PRICES / filename)
        assert entry["bars"] == len(dates), f"{entry['symbol']}: bars {entry['bars']} != {len(dates)}"
        assert entry["first"] == dates[0].isoformat(), f"{entry['symbol']}: first mismatch"
        assert entry["last"] == dates[-1].isoformat(), f"{entry['symbol']}: last mismatch"

    for failure in meta.get("failures", []):
        filename = failure["symbol"].replace("^", "_").upper() + ".csv"
        assert not (STAGED_PRICES / filename).exists(), (
            f"{failure['symbol']} recorded absent but has a staged CSV"
        )


# ---------------------------------------------------------------------------
# iter-17: index & macro context (goal.md §H) + the iter-18 swap gate
# ---------------------------------------------------------------------------

def _read_rows(path: Path) -> list[dict]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def test_context_indexes_deep_window_clipped_pinned_end_no_flat_runs():
    """_SPX/_NDX/_DJI are staged DEEP from the world bundle over the pinned window: first bar
    inside the first 1996 trading week (clip proven — the archive's 1789/1938/1896 flat/monthly
    rows never leak), last bar == the manifest's pinned end (a real trading day), daily density
    (not a monthly-cadence relic), and no fabricated-looking flat-OHLC run inside the window."""
    meta = json.loads((STAGED_DIR / "meta.json").read_text())
    pinned_end = date.fromisoformat(meta["window"]["end"])
    for name in WORLD_INDEX_FILES:
        path = STAGED_PRICES / f"{name}.csv"
        assert path.exists(), f"{name}.csv missing from the staged context"
        rows = _read_rows(path)
        first = date.fromisoformat(rows[0]["date"])
        last = date.fromisoformat(rows[-1]["date"])
        assert first >= date.fromisoformat(PINNED_WINDOW["start"]), (
            f"{name}: pre-window leakage — first staged bar {first}"
        )
        assert first <= DEPTH_ANCHOR, f"{name}: not deep — first staged bar {first}"
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


def test_fred_macro_proxies_byte_identical_to_live():
    """_TNX/_DXY/_VXN are the app's deterministic FRED-macro PROXIES: byte-identical copies of
    the live seed's series (goal.md §H — a Yahoo re-fetch would DESYNC them from the FRED macro
    the app displays and silently change their meaning)."""
    for name in PROXY_FILES:
        staged = (STAGED_PRICES / f"{name}.csv").read_bytes()
        live = (LIVE_SEED_PRICES / f"{name}.csv").read_bytes()
        assert staged == live, f"{name}.csv: staged proxy diverges from the live seed's copy"


def test_vix_deep_xor_verbatim_fallback_never_spliced():
    """_VIX is in EXACTLY ONE of the two sanctioned states: the deep single-pull Yahoo series
    (first bar <= 1996-01-05, one continuous series, clipped to the pinned end, never losing
    coverage vs the live copy) XOR the verbatim byte-identical live copy (the sanctioned
    fallback) — never a hybrid/splice of the two."""
    staged_path = STAGED_PRICES / "_VIX.csv"
    live_path = LIVE_SEED_PRICES / "_VIX.csv"
    assert staged_path.exists(), "_VIX.csv missing from the staged context"
    identical = staged_path.read_bytes() == live_path.read_bytes()

    dates, closes = _read_series(staged_path)
    deep = dates[0] <= DEPTH_ANCHOR
    assert deep != identical, (
        f"_VIX must be deep XOR the verbatim live copy — got deep={deep}, "
        f"byte-identical={identical} (a hybrid/shallow state is a splice or a partial pull)"
    )
    if deep:
        max_gap = max((b - a).days for a, b in zip(dates, dates[1:]))
        assert max_gap <= MAX_VIX_GAP_DAYS, (
            f"_VIX: {max_gap}-day gap — not a single continuous series (splice seam?)"
        )
        assert dates[-1] >= LIVE_VIX_LAST, (
            f"_VIX: deep pull ends {dates[-1]}, LOSING coverage vs the live copy ({LIVE_VIX_LAST})"
        )
        assert dates[-1] <= date.fromisoformat(PINNED_WINDOW["end"]), (
            f"_VIX: last bar {dates[-1]} exceeds the pinned end"
        )
        assert all(c > 0 for c in closes)


def test_swap_completeness_staged_superset_of_live():
    """THE iter-18 gate: every price CSV in the live seed has a staged counterpart (staged set ⊇
    live set), so the atomic basis swap can flip the seed dir once, over one complete seed."""
    live = {p.name for p in LIVE_SEED_PRICES.glob("*.csv")}
    staged = {p.name for p in STAGED_PRICES.glob("*.csv")}
    assert live, "live seed prices dir is empty — cannot prove swap-completeness"
    missing = sorted(live - staged)
    assert not missing, (
        f"swap-INCOMPLETE: the staged seed lacks live series {missing} — iter-18 must not swap"
    )


def test_manifest_context_vendors_window_pins_and_accounting():
    """Per-series vendor disclosure (goal.md §H): every context series records its vendor
    (stooq / yahoo / fred-macro-proxy) with coverage matching disk; equity records stay untouched
    (vendor = the manifest-level provider tag); the pinned window is unchanged; the
    planned/ok/failed accounting is consistent with SATS the only remaining honest absence."""
    meta = json.loads((STAGED_DIR / "meta.json").read_text())
    assert meta["provider"] == "stooq"
    assert meta["window"] == PINNED_WINDOW, "the pinned window changed — staging must not re-pin"

    by_symbol = {e["symbol"]: e for e in meta["symbols"]}
    for symbol, vendor in CONTEXT_VENDORS.items():
        entry = by_symbol.get(symbol)
        assert entry is not None, f"{symbol}: no manifest coverage record"
        assert entry.get("vendor") == vendor, (
            f"{symbol}: vendor {entry.get('vendor')!r} != required {vendor!r}"
        )
        rows = _read_rows(STAGED_PRICES / (symbol.replace("^", "_").upper() + ".csv"))
        assert entry["bars"] == len(rows), f"{symbol}: manifest bars != disk"
        assert entry["first"] == rows[0]["date"], f"{symbol}: manifest first != disk"
        assert entry["last"] == rows[-1]["date"], f"{symbol}: manifest last != disk"
    assert "vendor" not in by_symbol["AAPL"], "equity records must stay untouched by the merge"
    assert "never presented as a market index" in meta["note"]

    assert meta["failed"] == EXPECTED_FAILED
    assert meta["symbols_planned"] == EXPECTED_PLANNED
    assert meta["symbols_ok"] == EXPECTED_OK == len(meta["symbols"])
    assert meta["symbols_failed"] == len(EXPECTED_FAILED) == len(meta["failures"])
    assert len(list(STAGED_PRICES.glob("*.csv"))) == EXPECTED_OK
