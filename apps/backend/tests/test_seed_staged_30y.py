"""Validation suite for the STAGED ~30-year Stooq seed (`data/seed-stooq-30y/`) — iter-16 Part A
of the sanctioned data-basis migration. The staged tree is read by NOTHING at runtime; these tests
validate the committed data asset itself:

  * schema identity + structural integrity for EVERY staged CSV (canonical header, strictly
    ascending unique dates, positive prices, non-negative volumes);
  * depth/honesty anchors — long-tenured names reach the first 1996 week; NVDA starts at its REAL
    1999 IPO (not a padded 1996); post-IPO names (COIN/ARM/HOOD) are honestly short and NEVER
    predate their real listing (anti-goal: No fabricated data);
  * split continuity — no ~10x/~4x one-day close seam across NVDA 2024-06-10 / AAPL 2020-08-31
    (the whole span must be one consistent back-adjusted basis);
  * cross-vendor sanity — staged daily returns agree with the committed live (Yahoo) seed over
    the 2021-01 -> 2026-05 overlap (both bases are fully adjusted, so returns must match);
  * manifest agreement — meta.json's per-symbol coverage matches the CSVs on disk exactly.

SKIPS (honestly, with the reason below) while the staged directory is absent: the iter-16 live
probe found Stooq's CSV export endpoint DENIES this environment (`Access denied` ACL behind its
browser-verification front door — evidence in docs/handoffs/goal-mcp-loop-iter-16-dev.md). The
suite activates unchanged the moment the staged asset lands (resume from an unblocked network or
with a sanctioned key).
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
        "staged 30y Stooq seed absent at data/seed-stooq-30y — iter-16 live-probe outcome: the "
        "Stooq CSV export endpoint denies this environment ('Access denied' ACL behind its "
        "browser-verification front door; evidence in docs/handoffs/goal-mcp-loop-iter-16-dev.md). "
        "This suite activates unchanged once the staged asset is fetched from an unblocked "
        "network or with a sanctioned STOOQ_API_KEY."
    ),
)


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
