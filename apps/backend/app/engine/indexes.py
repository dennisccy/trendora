"""Major-indexes normalized-% display series (iter-2 goal mode, J-44 / Capability 37).

`compute_index_series(...)` builds, **server-side**, the normalized-% performance lines for the
config-listed major-index ETFs over a selected range preset, rebased to the range start so every line
starts at ~0% on a shared scale. The frontend only re-formats these numbers — there is NO client-side
return math (anti-goal: The index chart is honest and never data-gated → "the normalized % series MUST
be computed server-side from stored bars").

Anti-goals enforced here:
  - **Honest, never data-gated.** A configured symbol with NO stored bars in the range (e.g. DIA before
    its one-shot fetch) is OMITTED — no synthesized line, no legend entry — and the chart still renders
    from the available series. The journey is never gated on DIA.
  - **No lookahead.** Series are bounded to dates `<= the resolved as-of date` (via `bars_asof`). A
    historical as-of renders no bar dated after the as-of date.
  - **No magic numbers.** The symbol list + display names and the range presets come from
    `config.index_chart` — never a hardcoded list/window in the engine.
  - **No recompute of a canonical score.** This is a PRESENTATION series (a normalized %), not a
    canonical score/return that any other surface reads; it is derived once here for the chart only.

The `?as_of=` resolution is delegated to `app.engine.scanner.resolve_as_of_date` (identical semantics to
every other read endpoint). An unknown range preset raises `UnknownRangeError` (the API maps it to an
explicit 422 — never a silent fallback to a fabricated range).
"""
from __future__ import annotations

import json
from datetime import date as date_cls, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.config import Config, IndexRangePreset, get_config
from app.engine.data_manager import load_seed_meta
from app.engine.prices import bars_asof, bars_through_latest
from app.engine.scanner import resolve_as_of_date
from app.models import DailyPrice, IndexSeriesCache

# iter-22 (J-14) — the honest display label for each committed-seed manifest vendor key (`data/seed/
# meta.json` `symbols[].vendor`). A key with no mapping falls back to the raw key itself (never a crash,
# never a fabricated label) — every currently-committed key is mapped below.
_VENDOR_LABELS: dict[str, str] = {
    "stooq": "Stooq",
    "yahoo": "Yahoo",
    "fred-macro-proxy": "FRED-macro proxy",
}


def _vendor_label(raw: Optional[str]) -> Optional[str]:
    """The honest display label for a `meta.json` vendor key, or `None` when the manifest has no vendor
    record for this symbol (e.g. the SPY/QQQ/IWM/RSP/DIA ETF lines) — never a fabricated vendor."""
    if not raw:
        return None
    return _VENDOR_LABELS.get(raw, raw)


class UnknownRangeError(Exception):
    """The requested range-preset key is not one of the configured `index_chart.range_presets` keys.
    The API maps this to an explicit 422 — the engine never silently falls back to a fabricated range."""

    def __init__(self, key: str, valid: list[str]):
        self.key = key
        self.valid = valid
        super().__init__(f"unknown range preset {key!r}; valid: {valid}")


def _resolve_preset(cfg: Config, range_key: Optional[str]) -> IndexRangePreset:
    """Resolve a range-preset key to its config entry (defaulting to `index_chart.default_range` when
    omitted). An unknown key raises `UnknownRangeError` — never a silent fabricated window."""
    presets = cfg.index_chart.range_presets
    key = range_key if range_key else cfg.index_chart.default_range
    for preset in presets:
        if preset.key == key:
            return preset
    raise UnknownRangeError(key, [p.key for p in presets])


def _range_start(resolved: date_cls, preset: IndexRangePreset) -> Optional[date_cls]:
    """The inclusive lower date bound for the preset: `resolved - preset.days` (a trailing window), or
    `None` for an all-history preset (`days is None`)."""
    if preset.days is None:
        return None
    return resolved - timedelta(days=preset.days)


def compute_index_series(
    session: Session,
    as_of: Optional[str] = None,
    range_key: Optional[str] = None,
    config: Optional[Config] = None,
    full: bool = False,
    seed_dir: Optional[str | Path] = None,
) -> dict:
    """Normalized-% display series for the config-listed index ETFs over the selected range preset.

    Returns a dict::

        {
          "asof_date": "yyyy-MM-dd",       # the resolved as-of date (upper bound of every series)
          "range": {"key": "...", "label": "...", "days": <int|null>, "start": "yyyy-MM-dd"|null},
          "ranges": [{"key": "...", "label": "..."}, ...],   # all presets, for the switcher (from config)
          "series": [                       # one line per CONFIGURED symbol THAT HAS bars in the range
            {"symbol": "SPY", "name": "S&P 500 (SPY)", "vendor": "Stooq"|None, "first": "yyyy-MM-dd",
             "points": [{"date": "yyyy-MM-dd", "pct": <float, rebased to range start>}, ...]},
            ...
          ],
        }

    Each series is rebased to its FIRST bar in the range (`pct = (close/base - 1) * 100`), so the first
    point is exactly 0.0% and all lines share one scale. A configured symbol with no bar in the range is
    omitted entirely (no `series` entry → no legend). Raises `AsOfError` for an invalid as-of and
    `UnknownRangeError` for an unknown range key — never a fabricated row/range.

    iter-22 (J-14) — `vendor` and `first` are ADDITIVE per-series fields sourced from the committed-seed
    manifest (`data_manager.load_seed_meta`, the SAME `meta.json` parse `load_seed_windows` uses — no
    second read path). `vendor` is the honest display label ("Stooq"/"Yahoo"/"FRED-macro proxy") or
    `None` when the manifest has no vendor record for the symbol (e.g. the SPY/QQQ/IWM/RSP/DIA ETF
    lines) — never a fabricated vendor. `first` is the symbol's REAL first bar date from the manifest,
    independent of the selected range/`full` — deliberately NOT `points[0]["date"]`, which is
    range-clamped (e.g. ~3 months ago on a "3M" preset) and would silently misrepresent how far back the
    series' real history goes. `seed_dir` is a test seam (defaults to the committed seed dir).

    `full` (J-49 — clamp-optional, dashboard card only): when `False` (the default — every existing
    consumer, incl. the stock-detail-fed path) bars are read via `bars_asof` (date <= resolved), so NO
    future-dated bar appears — byte-identical to before. When `True` the SERVED upper bound widens to the
    symbol's full stored path (`bars_through_latest`), so post-as-of bars render as DISPLAY-ONLY market
    context behind the dashboard's vertical as-of marker. It is the SAME compute path: same range start
    (lower bound), same rebase base (the first in-range bar), same normalization — only the upper bound
    moves, so the overlapping `<= resolved` portion is value-identical between modes. The response still
    echoes the resolved `asof_date` (the client draws the marker from it). This widened window is
    presentation-only; it feeds no as-of-scoped computed value (anti-goal: Full-history market context
    never looks ahead)."""
    cfg = config or get_config()
    resolved = resolve_as_of_date(session, as_of, cfg)
    preset = _resolve_preset(cfg, range_key)
    start = _range_start(resolved, preset)
    seed_meta = load_seed_meta(seed_dir)

    series: list[dict] = []
    for entry in cfg.index_chart.symbols:
        # full mode serves the whole stored path (display-only context past D); default clamps at <= D.
        bars = (
            bars_through_latest(session, entry.symbol)
            if full
            else bars_asof(session, entry.symbol, resolved)
        )
        if start is not None:
            bars = [bar for bar in bars if bar.date >= start]
        if not bars:
            continue  # honest omission — no synthesized line for a bar-less symbol (e.g. DIA)
        base = bars[0].close
        if base == 0:
            continue  # cannot rebase against a zero base — omit rather than divide-by-zero/fabricate
        points = [
            {"date": bar.date.isoformat(), "pct": round((bar.close / base - 1.0) * 100.0, 4)}
            for bar in bars
        ]
        meta_row = seed_meta.get(entry.symbol) or {}
        first_date = meta_row.get("first")
        series.append({
            "symbol": entry.symbol,
            "name": entry.name,
            "vendor": _vendor_label(meta_row.get("vendor")),
            "first": first_date.isoformat() if first_date else None,
            "points": points,
        })

    return {
        "asof_date": resolved.isoformat(),
        "range": {
            "key": preset.key,
            "label": preset.label,
            "days": preset.days,
            "start": start.isoformat() if start is not None else None,
        },
        "ranges": [{"key": p.key, "label": p.label} for p in cfg.index_chart.range_presets],
        "series": series,
    }


# --------------------------------------------------------------------------------------------------
# Ingest-time serving cache for the SINGLE unparameterized default hot key (ops-hardening iter-13,
# J-06 — aggregation candidate #7): `range_key=cfg.index_chart.default_range`, `full=True`, no explicit
# `as_of`. Every other request combination (a user-selected non-default range, an explicit historical
# as-of) stays on the lazy, uncached `compute_index_series` call above — unchanged.
# --------------------------------------------------------------------------------------------------


def index_series_dataset_version(session: Session, config: Optional[Config] = None) -> str:
    """A NARROW cache stamp for `IndexSeriesCache`, scoped ONLY to the inputs the hot-key series
    actually reads: the configured `index_chart.symbols`' stored bars. Deliberately NOT the broad
    `research._dataset_version` (which folds in the `forward_returns` row count and would invalidate on
    unrelated ingest activity that never touches an index symbol's bars) — mirrors
    `research._membership_dataset_version`'s own narrow-stamp precedent (scope the stamp to only what
    the cache reads).

    A single bounded, indexed read (`max(date)` + `count(*)` filtered to the configured index symbols,
    served by the existing `uq_daily_prices_symbol_date` / `ix_daily_prices_date` indexes) — never a
    whole-`daily_prices`-table scan. Changes whenever a configured index symbol gains, loses, or has a
    bar altered anywhere in its history; unaffected by ingest activity for any OTHER symbol or by a pure
    forward-return insert."""
    cfg = config or get_config()
    symbols = [entry.symbol for entry in cfg.index_chart.symbols]
    if not symbols:
        return "none"
    max_date = session.exec(
        select(func.max(DailyPrice.date)).where(DailyPrice.symbol.in_(symbols))
    ).one()
    if isinstance(max_date, tuple):
        max_date = max_date[0]
    count = session.exec(
        select(func.count()).select_from(DailyPrice).where(DailyPrice.symbol.in_(symbols))
    ).one()
    if isinstance(count, tuple):
        count = count[0]
    date_stamp = max_date.isoformat() if max_date is not None else "none"
    return f"d{date_stamp}-c{count or 0}"


def index_series_cached_with_status(
    session: Session, config: Optional[Config] = None, seed_dir: Optional[str | Path] = None,
) -> tuple[dict, bool]:
    """Serve the hot-key `compute_index_series(as_of=None, range_key=cfg.index_chart.default_range,
    full=True)` payload from `IndexSeriesCache`, returning `(payload, persisted_this_call)`: on a cache
    HIT for the current `(range_key, full, dataset_version)` key, deserialize the stored payload (NO
    recompute), re-derive the CURRENT resolved `as_of` and overwrite the echoed `asof_date` with it (see
    `IndexSeriesCache`'s own docstring — the only as-of-dependent part of this response), and return
    `persisted_this_call=False`; on a MISS or a stale dataset-version stamp, compute ONCE via the
    UNCHANGED `compute_index_series` (the SOLE producer — this function is a pure serving/persistence
    wrapper, never a second derivation), persist it under the current stamp, prune any stale rows for
    this `(range_key, full)` identity, and return `persisted_this_call=True`. The returned payload is
    BYTE-IDENTICAL to `compute_index_series(...)` for the same inputs (No recompute in the read path).

    `persisted_this_call` is the honesty gate the ingest finalize hook's `aggregates_refreshed` reads:
    "index_series" is reported ONLY when this call actually wrote a new row — a cache HIT (nothing new
    to persist) is an honest skip, mirroring the "was skipped" omission every other warm category
    already follows, never a fabricated refresh."""
    cfg = config or get_config()
    range_key = cfg.index_chart.default_range
    version = index_series_dataset_version(session, cfg)

    hit = session.exec(
        select(IndexSeriesCache).where(
            IndexSeriesCache.range_key == range_key,
            IndexSeriesCache.full == True,  # noqa: E712 — SQLAlchemy column comparison, not a bool identity check
            IndexSeriesCache.dataset_version == version,
        )
    ).first()
    if hit is not None:
        resolved = resolve_as_of_date(session, None, cfg)  # re-derived fresh, never trusted from storage
        payload = json.loads(hit.payload_json)
        payload["asof_date"] = resolved.isoformat()
        return payload, False

    # MISS — compute once (the SOLE producer, unchanged) and persist.
    payload = compute_index_series(
        session, as_of=None, range_key=range_key, config=cfg, full=True, seed_dir=seed_dir
    )

    # prune stale rows for THIS (range_key, full) identity (any older dataset_version) so the cache
    # table does not grow unbounded as the dataset matures; the current-version row is then upserted.
    stale = session.exec(
        select(IndexSeriesCache).where(
            IndexSeriesCache.range_key == range_key,
            IndexSeriesCache.full == True,  # noqa: E712
            IndexSeriesCache.dataset_version != version,
        )
    ).all()
    for row in stale:
        session.delete(row)

    session.add(IndexSeriesCache(
        range_key=range_key, full=True, dataset_version=version,
        payload_json=json.dumps(payload), created_at=datetime.now(timezone.utc),
    ))
    try:
        session.commit()
    except Exception:  # a concurrent writer raced us to the same key — the cache is best-effort, not a
        session.rollback()  # source of truth; the freshly computed payload is still byte-identical, so return it
    return payload, True


def index_series_cached(
    session: Session, config: Optional[Config] = None, seed_dir: Optional[str | Path] = None,
) -> dict:
    """The `GET /api/indexes` hot-key route's own entry point: the payload half of
    `index_series_cached_with_status` (drops the `persisted_this_call` flag, which only the ingest
    finalize hook's honesty gate needs)."""
    payload, _persisted = index_series_cached_with_status(session, config, seed_dir)
    return payload
