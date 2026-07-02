"""LocalStooqArchiveProvider — read Stooq's BULK US daily archive (`d_us_txt`) from local disk.

iter-16 unblock: Stooq's per-symbol CSV export endpoint is IP-blocked ("Access denied"), but the
operator downloaded Stooq's bulk US stocks+ETFs archive (`data/d_us_txt/`, from `d_us_txt.zip`) and
extracted it locally. This provider reads that SAME vendor/adjusted data offline so
`scripts/ingest_seed.py --provider stooq-local` can stage the 30-year seed with no network at all.

Contract (identical to every `PriceProvider`): return REAL bars sorted ascending, or RAISE
`ProviderUnavailableError` on a genuinely corrupt/unparseable file — it NEVER fabricates a bar. A
symbol that cannot be in this stocks+ETFs bundle (a caret index like `^VIX`, or a name Stooq doesn't
carry) or a file with no rows in the window returns `[]` — an honest "no data" that the ingest loop
records as an absence and CONTINUES. It deliberately does NOT raise for a missing/empty symbol: a
raised "no file" would be classified as a rate-cap GATE by `classify_stooq_failure` and abort the
whole staged run (and `^VIX` is an early tier-1 name). A raise is reserved for a genuinely corrupt row
in a PRESENT file (message contains "unparseable" → the ingest records it absent and continues,
matching `StooqProvider`).

This provider is imported ONLY by the dev-run ingest script; it is never referenced by
`make_provider` and never imported on the app boot/request path, so runtime behaviour is unchanged.

Bulk `.us.txt` format (DIFFERENT from the per-symbol network CSV parsed by `StooqProvider`)::

    <TICKER>,<PER>,<DATE>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>,<OPENINT>
    AAPL.US,D,19840907,000000,0.0991725,0.10039,0.0979751,0.0991725,99242379,0

`DATE` is `YYYYMMDD` (no dashes); `VOL` can be fractional (Stooq back-adjusts volume too); OHLC are
fully split+dividend back-adjusted. Files are named `<sym>.us.txt` (lowercase; a dot-class share uses
a hyphen, e.g. `brk-b.us.txt`) and sharded under `data/daily/us/<market {stocks,etfs}>/[shard]/`.
"""
from __future__ import annotations

import csv
from datetime import date as date_cls, datetime
from pathlib import Path
from typing import Optional

from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError

_ARCHIVE_SUFFIX = ".us.txt"


class LocalStooqArchiveProvider(PriceProvider):
    """Serve `get_daily` bars from a locally-extracted Stooq bulk US archive (`d_us_txt`)."""

    def __init__(self, archive_dir: Path | str):
        self.archive_dir = Path(archive_dir)
        # One directory walk builds a base-stem -> file index. The bulk tree has verified 0 duplicate
        # base stems across its shards, so the mapping is an unambiguous 1:1 (setdefault keeps the
        # first seen if a future bundle ever collided, rather than silently overwriting).
        self._index: dict[str, Path] = {}
        if self.archive_dir.is_dir():
            for path in self.archive_dir.rglob("*" + _ARCHIVE_SUFFIX):
                self._index.setdefault(path.name[: -len(_ARCHIVE_SUFFIX)].lower(), path)

    @property
    def indexed_count(self) -> int:
        return len(self._index)

    @staticmethod
    def _stem_for(symbol: str) -> Optional[str]:
        """Map an internal ticker to a bulk-archive file stem, or `None` if it cannot be in this
        US stocks+ETFs bundle (a caret index such as `^VIX`)."""
        s = symbol.strip().lower()
        if not s or s.startswith("^"):
            return None
        return s.replace(".", "-")  # dot-class shares are hyphenated on disk (BRK.B -> brk-b)

    def get_daily(
        self,
        symbol: str,
        start: Optional[date_cls] = None,
        end: Optional[date_cls] = None,
    ) -> list[Bar]:
        stem = self._stem_for(symbol)
        if stem is None:
            return []  # caret index — not in this bundle; honest absence, never fabricate
        path = self._index.get(stem)
        if path is None:
            return []  # name absent from the archive — honest absence
        try:
            return self._parse(path, start, end)
        except (ValueError, KeyError, IndexError) as exc:  # corrupt row — surface, never fabricate
            raise ProviderUnavailableError(
                f"local stooq archive response unparseable for {symbol!r} ({path.name}): {exc}"
            ) from exc

    @staticmethod
    def _parse(
        path: Path,
        start: Optional[date_cls],
        end: Optional[date_cls],
    ) -> list[Bar]:
        bars: list[Bar] = []
        with path.open(newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader, None)  # skip the "<TICKER>,<PER>,..." header (None if empty file)
            if header is None:
                return []
            for row in reader:
                if not row or not row[0] or row[0].startswith("<"):
                    continue  # blank line or a stray repeated header
                d = datetime.strptime(row[2], "%Y%m%d").date()
                if start is not None and d < start:
                    continue
                if end is not None and d > end:
                    continue
                bars.append(
                    Bar(
                        date=d,
                        open=float(row[4]),
                        high=float(row[5]),
                        low=float(row[6]),
                        close=float(row[7]),
                        volume=float(row[8]),
                    )
                )
        bars.sort(key=lambda b: b.date)  # defensive; the bulk archive is already ascending
        return bars
