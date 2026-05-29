"""One-shot seed ingest — DEV-RUN ONCE, then COMMIT the output. NOT on the boot/request path.

Fetches REAL daily EOD OHLCV for every universe symbol + ETF + ^VIX in config.yaml, computes
split/dividend-adjusted OHLC, and writes a frozen CSV fixture under
`apps/backend/data/seed/prices/`. After committing, the build loop only READS these files (via
SeedProvider) and MUST NOT re-fetch live data — re-fetching would make later walk-forward
evidence irreproducible.

SOURCE NOTE (documented deviation): the plan named Stooq, but Stooq's bulk CSV download is now
gated behind an apikey obtained via captcha. Committing such a key would violate the
"No secrets in source" anti-goal, and a captcha is not reproducible/unattended. We therefore use
the free, NO-KEY Yahoo Finance chart API (query1.finance.yahoo.com/v8/finance/chart). Same hard
guarantees: REAL EOD history, no key, no secret, deterministic + frozen once committed. No bars
are fabricated or hand-edited — symbols that fail to fetch are logged and simply omitted.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/ingest_seed.py
    apps/backend/.venv/bin/python apps/backend/scripts/ingest_seed.py --start 2021-01-01
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
SEED_DIR = BACKEND_DIR / "data" / "seed"
PRICES_DIR = SEED_DIR / "prices"

sys.path.insert(0, str(BACKEND_DIR))
from app.config import load_config  # noqa: E402
from app.data_providers.seed_provider import symbol_to_filename  # noqa: E402

YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) trendora-seed-ingest/1.0"}
ET = ZoneInfo("America/New_York")


def _to_epoch(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def fetch_symbol(client: httpx.Client, symbol: str, start: date, end: date) -> list[dict]:
    """Return adjusted daily OHLCV rows for one symbol, or raise on failure."""
    params = {
        "period1": _to_epoch(start),
        "period2": _to_epoch(end),
        "interval": "1d",
        "events": "div,split",
    }
    resp = client.get(YAHOO_URL.format(symbol=symbol), params=params, headers=HEADERS, timeout=30.0)
    resp.raise_for_status()
    payload = resp.json()
    result = payload["chart"]["result"]
    if not result:
        raise ValueError(f"no chart result for {symbol}")
    res = result[0]
    timestamps = res.get("timestamp") or []
    quote = res["indicators"]["quote"][0]
    adj = (res["indicators"].get("adjclose") or [{}])[0].get("adjclose")

    rows: list[dict] = []
    for i, ts in enumerate(timestamps):
        o, h, low, c, v = (quote["open"][i], quote["high"][i], quote["low"][i],
                           quote["close"][i], quote["volume"][i])
        if None in (o, h, low, c):
            continue  # skip incomplete bars — never interpolate/fabricate
        # split + dividend adjustment factor from Yahoo's adjusted close
        factor = (adj[i] / c) if (adj and adj[i] is not None and c) else 1.0
        d = datetime.fromtimestamp(ts, ET).date()  # exchange-local trading date (deterministic)
        rows.append({
            "date": d.isoformat(),
            "open": round(o * factor, 6),
            "high": round(h * factor, 6),
            "low": round(low * factor, 6),
            "close": round(c * factor, 6),
            "volume": int(v) if v is not None else 0,
        })
    # de-dupe by date (keep last) and sort ascending
    by_date = {r["date"]: r for r in rows}
    return [by_date[d] for d in sorted(by_date)]


def write_csv(symbol: str, rows: list[dict]) -> Path:
    PRICES_DIR.mkdir(parents=True, exist_ok=True)
    path = PRICES_DIR / symbol_to_filename(symbol)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["date", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="One-shot Trendora seed ingest (Yahoo EOD).")
    parser.add_argument("--start", default="2021-01-01", help="ISO start date (default 2021-01-01)")
    parser.add_argument("--end", default=None, help="ISO end date (default: today)")
    parser.add_argument("--sleep", type=float, default=0.3, help="seconds between symbol requests")
    args = parser.parse_args()

    config = load_config()
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end) if args.end else datetime.now(ET).date()

    symbols: list[str] = []
    symbols += list(config.universe.symbols)
    symbols += list(config.etfs.index)
    symbols += list(config.etfs.sector.keys())
    symbols += list(config.etfs.industry)
    symbols += list(config.etfs.volatility)
    seen: set[str] = set()
    symbols = [s for s in symbols if not (s in seen or seen.add(s))]

    print(f"[ingest] {len(symbols)} symbols, window {start} -> {end}, source=Yahoo chart API")
    ok: list[dict] = []
    failed: list[str] = []
    with httpx.Client(follow_redirects=True) as client:
        for i, symbol in enumerate(symbols, 1):
            last_err = None
            for attempt in range(3):
                try:
                    rows = fetch_symbol(client, symbol, start, end)
                    if not rows:
                        raise ValueError("empty series")
                    path = write_csv(symbol, rows)
                    ok.append({"symbol": symbol, "bars": len(rows),
                               "first": rows[0]["date"], "last": rows[-1]["date"]})
                    print(f"[{i:3d}/{len(symbols)}] {symbol:6s} {len(rows):5d} bars "
                          f"{rows[0]['date']}..{rows[-1]['date']} -> {path.name}")
                    break
                except Exception as exc:  # noqa: BLE001 - log + retry, then record failure
                    last_err = exc
                    time.sleep(1.0 + attempt)
            else:
                failed.append(symbol)
                print(f"[{i:3d}/{len(symbols)}] {symbol:6s} FAILED: {last_err}")
            time.sleep(args.sleep)

    meta = {
        "source": "Yahoo Finance chart API (query1.finance.yahoo.com/v8/finance/chart)",
        "note": "REAL split/dividend-adjusted EOD OHLCV; frozen + committed; no key/secret used.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "symbols_ok": len(ok),
        "symbols_failed": len(failed),
        "failed": failed,
        "symbols": ok,
    }
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    (SEED_DIR / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"[ingest] done: {len(ok)} ok, {len(failed)} failed. Wrote {SEED_DIR / 'meta.json'}")
    if failed:
        print(f"[ingest] failed symbols: {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
