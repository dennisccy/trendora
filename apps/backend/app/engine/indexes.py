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

from datetime import date as date_cls, timedelta
from typing import Optional

from sqlmodel import Session

from app.config import Config, IndexRangePreset, get_config
from app.engine.prices import bars_asof
from app.engine.scanner import resolve_as_of_date


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
) -> dict:
    """Normalized-% display series for the config-listed index ETFs over the selected range preset.

    Returns a dict::

        {
          "asof_date": "yyyy-MM-dd",       # the resolved as-of date (upper bound of every series)
          "range": {"key": "...", "label": "...", "days": <int|null>, "start": "yyyy-MM-dd"|null},
          "ranges": [{"key": "...", "label": "..."}, ...],   # all presets, for the switcher (from config)
          "series": [                       # one line per CONFIGURED symbol THAT HAS bars in the range
            {"symbol": "SPY", "name": "S&P 500 (SPY)",
             "points": [{"date": "yyyy-MM-dd", "pct": <float, rebased to range start>}, ...]},
            ...
          ],
        }

    Each series is rebased to its FIRST bar in the range (`pct = (close/base - 1) * 100`), so the first
    point is exactly 0.0% and all lines share one scale. A configured symbol with no bar in the range is
    omitted entirely (no `series` entry → no legend). Bars are read via `bars_asof` (date <= resolved),
    so no future-dated bar appears. Raises `AsOfError` for an invalid as-of and `UnknownRangeError` for
    an unknown range key — never a fabricated row/range."""
    cfg = config or get_config()
    resolved = resolve_as_of_date(session, as_of, cfg)
    preset = _resolve_preset(cfg, range_key)
    start = _range_start(resolved, preset)

    series: list[dict] = []
    for entry in cfg.index_chart.symbols:
        bars = bars_asof(session, entry.symbol, resolved)
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
        series.append({"symbol": entry.symbol, "name": entry.name, "points": points})

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
