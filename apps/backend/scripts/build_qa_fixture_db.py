"""Build a THROWAWAY QA fixture DB (+ a narrowed fixture config) for the iter-26 browser captures of
J-37 (missing-data diagnostic + gap-exact pull) and J-35 (expand). It is a TEST/DEV harness affordance
ONLY — it NEVER mutates the committed `apps/backend/data/seed/` tree and NEVER touches the live host DB
(`apps/backend/data/trendora.db`); everything it writes goes under a temp/throwaway output directory.

What it seeds (so the diagnostic renders ALL THREE categories with the chosen members):
  - SPY        — the full benchmark calendar (a recent N-trading-day window from the committed seed),
                 so the diagnostic's trading calendar + the J-36 coverage table are exact.
  - one healthy member (default ``AMD``) — the full window, so it is FINE (flagged in NO category) and
    the universe is not wholly broken.
  - ``ANET``   — ZERO bars  -> the ``no_history`` category (pull target = the full window).
  - ``DELL``   — a few bars (< ``indicators.min_history_bars``) -> the ``thin`` category.
  - ``MU``     — the full window MINUS a contiguous mid-window hole -> the ``intra_series_gap`` category
                 (a pullable gap; the gap-exact pull fetches EXACTLY ``[first_gap, last_gap]``).

The bars come from the committed seed (REAL committed prices — nothing is fabricated), so the env-gated
offline ``seed`` import source can supply EXACTLY the diagnosed shortfall and a pull/expand runs to
completion offline. A narrowed fixture ``config.yaml`` (the committed config with ``universe.symbols``
restricted to the four chosen members) is written alongside so the diagnostic flags exactly those rows
(not all 122 universe members as no-history).

The QA/browser harness boots the backend with:
    TRENDORA_ENABLE_SEED_IMPORT_SOURCE=1   (expose the offline ``seed`` import source)
    TRENDORA_CONFIG=<out>/config.yaml      (the narrowed fixture universe)
    <database.url pointed at <out>/qa_fixture.db>   (already baked into the fixture config)

Usage:
    .venv/bin/python scripts/build_qa_fixture_db.py [--out DIR] [--window N] [--thin-bars K]
                                                    [--gap-len G] [--healthy SYM]
Prints the three env/path values the harness needs as a final JSON line.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from datetime import date as date_cls
from pathlib import Path

# Make `app` importable when run as a script from apps/backend.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import yaml  # noqa: E402

from app.config import DEFAULT_CONFIG_PATH, load_config  # noqa: E402
from app.data_providers import DEFAULT_SEED_DIR  # noqa: E402
from app.data_providers.seed_provider import symbol_to_filename  # noqa: E402
from app.db import create_db_and_tables, make_engine  # noqa: E402
from app.models import DailyPrice  # noqa: E402
from sqlmodel import Session  # noqa: E402

# The three diagnostic-triggering members + one healthy control. All are real committed-seed symbols
# AND committed-config universe members (verified iter-26) so the offline `seed` source can supply them.
NO_HISTORY_SYMBOL = "ANET"   # zero bars -> no_history
THIN_SYMBOL = "DELL"         # few bars  -> thin (< indicators.min_history_bars)
GAP_SYMBOL = "MU"            # full window minus a mid hole -> intra_series_gap
DEFAULT_HEALTHY_SYMBOL = "AMD"  # full window -> FINE (flagged in no category)
BENCHMARK = "SPY"

# Real-world approximate market caps (USD) for a representative subset of the committed-seed symbols —
# used ONLY by the env-gated offline `seed` import source's J-35 expand (a `market_caps.csv` overlay) so
# the OFFLINE expand has BOTH passers (cap >= the config min_market_cap) AND honest omissions (a symbol
# absent here is omitted `no_market_cap` — never a fabricated cap). These are descriptive screening
# references for a TEST fixture, never displayed canonical values, and the file lives in a THROWAWAY
# overlay dir (never the committed seed tree, never production). One member (`SMCI` here as a low-cap
# example is NOT included) — instead the omissions come naturally from the many pool symbols absent below.
_FIXTURE_MARKET_CAPS_USD: dict[str, float] = {
    "NVDA": 3_300_000_000_000.0,
    "AAPL": 3_400_000_000_000.0,
    "MSFT": 3_100_000_000_000.0,
    "AMZN": 2_300_000_000_000.0,
    "GOOGL": 2_100_000_000_000.0,
    "META": 1_300_000_000_000.0,
    "AVGO": 1_100_000_000_000.0,
    "AMD": 220_000_000_000.0,
    "MU": 120_000_000_000.0,
    "ANET": 110_000_000_000.0,
    "DELL": 95_000_000_000.0,
    "MRVL": 70_000_000_000.0,
    "SMCI": 25_000_000_000.0,
    "VRT": 45_000_000_000.0,
    "CIEN": 11_000_000_000.0,
    "ON": 28_000_000_000.0,
    "TSM": 900_000_000_000.0,
    # an intentionally SUB-threshold (< $2B) member so the expand shows a "market_cap < min" omission too
    "AMSC": 1_200_000_000.0,
}


def _read_seed_bars(symbol: str, seed_dir: Path) -> list[dict]:
    """Read a committed-seed symbol's bars (ascending). Raises if the file is absent — never fabricates."""
    path = seed_dir / "prices" / symbol_to_filename(symbol)
    if not path.exists():
        raise FileNotFoundError(f"committed seed missing for {symbol!r} at {path}")
    with path.open(newline="") as fh:
        rows = [
            {
                "date": date_cls.fromisoformat(r["date"]),
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": float(r["volume"]),
            }
            for r in csv.DictReader(fh)
        ]
    rows.sort(key=lambda r: r["date"])
    return rows


def _add_bars(session: Session, symbol: str, bars: list[dict]) -> int:
    for b in bars:
        session.add(DailyPrice(symbol=symbol, **b))
    return len(bars)


def build_fixture(
    out_dir: Path,
    *,
    window: int = 230,
    thin_bars: int = 40,
    gap_len: int = 10,
    healthy_symbol: str = DEFAULT_HEALTHY_SYMBOL,
    seed_dir: Path = DEFAULT_SEED_DIR,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> dict:
    """Build the throwaway fixture DB + narrowed config under ``out_dir``. Returns a dict of the env/path
    the QA harness needs. NEVER writes inside ``seed_dir`` or the live host DB."""
    out_dir = Path(out_dir).resolve()
    seed_dir = Path(seed_dir).resolve()
    # Guard: refuse to write inside the committed seed tree (anti-goal: never mutate committed seed).
    if out_dir == seed_dir or seed_dir in out_dir.parents:
        raise ValueError(f"refusing to write the fixture inside the committed seed tree: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = out_dir / "qa_fixture.db"
    if db_path.exists():
        db_path.unlink()  # idempotent rebuild

    cfg = load_config(config_path)
    threshold = cfg.indicators.min_history_bars
    if thin_bars <= 0 or thin_bars >= threshold:
        raise ValueError(f"--thin-bars must be in (0, {threshold}); got {thin_bars}")

    # The benchmark window = the LAST `window` SPY trading days from the committed seed (a recent slice).
    # ops-hardening iter-1 (J-03): no job date-range span cap exists anywhere in config any more (removed
    # — was data_manager.max_range_days), so this fixture-builder no longer bounds the window's calendar
    # span against it either; `--window` (a TRADING-day count) is its own reasonable sizing knob.
    spy = _read_seed_bars(BENCHMARK, seed_dir)
    if len(spy) < window:
        raise ValueError(f"committed SPY seed has only {len(spy)} bars; --window {window} too large")
    spy_window = spy[-window:]
    window_dates = [b["date"] for b in spy_window]
    if gap_len <= 0 or gap_len >= window - 2:
        raise ValueError(f"--gap-len must be in (0, {window - 2}); got {gap_len}")

    healthy = _read_seed_bars(healthy_symbol, seed_dir)
    healthy_window = [b for b in healthy if b["date"] in set(window_dates)]
    thin_src = _read_seed_bars(THIN_SYMBOL, seed_dir)
    thin_window = [b for b in thin_src if b["date"] in set(window_dates)][:thin_bars]
    gap_src = _read_seed_bars(GAP_SYMBOL, seed_dir)
    gap_full = [b for b in gap_src if b["date"] in set(window_dates)]
    # punch a contiguous hole in the MIDDLE of the gap member's series
    hole_start = (len(gap_full) - gap_len) // 2
    gap_hole_dates = [b["date"] for b in gap_full[hole_start:hole_start + gap_len]]
    gap_with_hole = [b for b in gap_full if b["date"] not in set(gap_hole_dates)]

    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    counts: dict[str, int] = {}
    with Session(engine) as session:
        counts[BENCHMARK] = _add_bars(session, BENCHMARK, spy_window)
        counts[healthy_symbol] = _add_bars(session, healthy_symbol, healthy_window)
        counts[NO_HISTORY_SYMBOL] = 0  # no rows -> no_history
        counts[THIN_SYMBOL] = _add_bars(session, THIN_SYMBOL, thin_window)
        counts[GAP_SYMBOL] = _add_bars(session, GAP_SYMBOL, gap_with_hole)
        session.commit()

    # The narrowed fixture config: the committed config with universe.symbols restricted to the four
    # chosen members + the database.url pointed at the throwaway fixture DB.
    raw = yaml.safe_load(config_path.read_text())
    members = [NO_HISTORY_SYMBOL, THIN_SYMBOL, GAP_SYMBOL, healthy_symbol]
    member_set = set(members)
    raw.setdefault("universe", {})["symbols"] = members
    raw.setdefault("database", {})["url"] = f"sqlite:///{db_path}"
    # The config validators require (a) every theme member to be in universe.symbols and (b) every theme
    # to be non-empty. Narrow each theme to the chosen members and DROP a theme that becomes empty, so the
    # narrowed universe stays valid. (`stock_sectors` already maps the chosen members — they are original
    # universe members — so no sector-coverage edit is needed.)
    themes = raw.get("themes")
    if isinstance(themes, dict):
        narrowed = {
            slug: [m for m in mem if m in member_set]
            for slug, mem in themes.items()
        }
        raw["themes"] = {slug: mem for slug, mem in narrowed.items() if mem}
        if not raw["themes"]:
            # keep at least one non-empty theme so the config stays valid
            raw["themes"] = {"qa_fixture_theme": members}
    # J-58: `_stock_industries_valid` requires every `stock_industries` KEY to be in universe.symbols.
    # Drop any stock no longer in the narrowed universe; the values are `etfs.industry` tickers (NOT
    # universe members), so leave them as-is. An empty section is fine (it defaults to `{}`).
    stock_industries = raw.get("stock_industries")
    if isinstance(stock_industries, dict):
        raw["stock_industries"] = {
            stock: etfs for stock, etfs in stock_industries.items() if stock in member_set
        }
    fixture_config_path = out_dir / "config.yaml"
    fixture_config_path.write_text(yaml.safe_dump(raw, sort_keys=False))

    # The OFFLINE-expand overlay seed dir (iter-26 J-35): a throwaway dir that re-exposes the committed
    # `prices/` + `universe_pool.csv` as WRITABLE COPIES (never a symlink/mutation of the committed tree)
    # PLUS a `market_caps.csv` so the env-gated `seed` import source can read a REAL committed cap
    # reference for an OFFLINE expand. The expand WRITES its grown universe.json / per-symbol CSVs /
    # meta.json into THIS overlay (a copy) — so the committed seed tree is NEVER mutated. The QA harness
    # sets TRENDORA_SEED_IMPORT_DIR to this dir.
    import shutil
    overlay_dir = out_dir / "seed_overlay"
    if overlay_dir.exists():
        shutil.rmtree(overlay_dir)
    overlay_dir.mkdir(parents=True, exist_ok=True)
    # writable copies (NOT symlinks — the expand writes per-symbol CSVs back into prices/, and a symlink
    # would follow through to the committed seed and corrupt it).
    shutil.copytree(seed_dir / "prices", overlay_dir / "prices")
    pool_src = seed_dir / "universe_pool.csv"
    if pool_src.exists():
        shutil.copyfile(pool_src, overlay_dir / "universe_pool.csv")
    # write the real-cap reference for the pool symbols we know (others omit `no_market_cap` honestly)
    cap_lines = ["symbol,market_cap"]
    for sym, cap in _FIXTURE_MARKET_CAPS_USD.items():
        cap_lines.append(f"{sym},{cap:.0f}")
    (overlay_dir / "market_caps.csv").write_text("\n".join(cap_lines) + "\n")

    result = {
        "db_path": str(db_path),
        "config_path": str(fixture_config_path),
        "database_url": f"sqlite:///{db_path}",
        "universe_members": members,
        "benchmark_window": [window_dates[0].isoformat(), window_dates[-1].isoformat()],
        "bar_counts": counts,
        "gap": {
            "symbol": GAP_SYMBOL,
            "first_gap": gap_hole_dates[0].isoformat(),
            "last_gap": gap_hole_dates[-1].isoformat(),
            "missing_day_count": len(gap_hole_dates),
        },
        "thin": {"symbol": THIN_SYMBOL, "bars_have": counts[THIN_SYMBOL], "bars_needed": threshold},
        "no_history": {"symbol": NO_HISTORY_SYMBOL, "bars_needed": threshold},
        "seed_overlay_dir": str(overlay_dir),
        "env": {
            "TRENDORA_ENABLE_SEED_IMPORT_SOURCE": "1",
            "TRENDORA_CONFIG": str(fixture_config_path),
            "TRENDORA_SEED_IMPORT_DIR": str(overlay_dir),
        },
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a throwaway QA fixture DB for iter-26 captures.")
    parser.add_argument("--out", default=None, help="output dir (default: a fresh temp dir)")
    parser.add_argument("--window", type=int, default=230, help="benchmark trading-day window (default 230)")
    parser.add_argument("--thin-bars", type=int, default=40, help="bars for the thin member (< threshold)")
    parser.add_argument("--gap-len", type=int, default=10, help="mid-series hole length for the gap member")
    parser.add_argument("--healthy", default=DEFAULT_HEALTHY_SYMBOL, help="a healthy (full-window) member")
    args = parser.parse_args()

    out_dir = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="trendora_qa_fixture_"))
    result = build_fixture(
        out_dir,
        window=args.window,
        thin_bars=args.thin_bars,
        gap_len=args.gap_len,
        healthy_symbol=args.healthy,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
