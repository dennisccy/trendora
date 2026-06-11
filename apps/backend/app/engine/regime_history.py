"""Regime-history read path (iter-2 goal mode, J-44 + J-45 / Capability 37).

Returns the per-date market-regime series — `date -> {label, score}` — read **verbatim** from the
immutable `scanner_runs` rows, bounded to dates `<= the resolved as-of date`. This is the SINGLE shared
source both regime-band surfaces consume: the dashboard "Major indexes & regime" card (J-44) and the
regime bands behind the stock-detail price chart (J-45). Because both surfaces read this one series, the
SAME date shows the SAME stored label + score (and therefore the same color) on every surface (J-06
coherence applied to the regime).

Anti-goals enforced here:
  - **Regime overlays read stored regime only.** Every `label`/`score` is the stored value from the
    immutable run row (`ScannerRun.regime_label` / `regime_score`) — NOTHING is recomputed. There is no
    call into `app.engine.regime` here; the regime engine ran once per run at scan time and this module
    only READS its persisted output.
  - **No recompute in the read path / Single source of truth.** This is a pure storage read.
  - **No lookahead.** Rows dated AFTER the resolved as-of date are never returned — bands must not render
    past the resolved as-of date.

The as-of resolution is delegated to `app.engine.scanner.resolve_as_of_date` so this series uses the
EXACT same `?as_of=` semantics as every other read endpoint (latest stored when omitted; raises the
semantic `AsOfError` the API layer maps to a 4xx/503 for an invalid date — never a fabricated row).
"""
from __future__ import annotations

from datetime import date as date_cls
from typing import Optional

from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine.scanner import resolve_as_of_date
from app.models import ScannerRun


def get_regime_history(
    session: Session, as_of: Optional[str] = None, config: Optional[Config] = None
) -> dict:
    """The stored per-date market-regime series, bounded to dates `<= the resolved as-of date`.

    Returns a dict::

        {
          "asof_date": "yyyy-MM-dd",          # the resolved as-of date (the series' upper bound)
          "points": [                          # ascending by date; only dates <= asof_date
            {"date": "yyyy-MM-dd", "label": "<stored label>", "score": <stored float>},
            ...
          ],
        }

    Every point's `label` + `score` is the verbatim stored value from the immutable `ScannerRun` for
    that date (read once at scan time, never recomputed). No row dated after the resolved as-of date is
    ever returned (no-lookahead). An as-of predating all runs yields an honest empty `points` list (no
    crash, no fabricated rows). Raises `AsOfError` (mapped to an HTTP 4xx/503 by the API layer) for an
    unparseable / future / before-history as-of — never a fabricated date."""
    cfg = config or get_config()
    resolved = resolve_as_of_date(session, as_of, cfg)
    rows = session.exec(
        select(ScannerRun)
        .where(ScannerRun.asof_date <= resolved)
        .order_by(ScannerRun.asof_date)
    ).all()
    points = [
        {
            "date": run.asof_date.isoformat(),
            "label": run.regime_label,
            "score": run.regime_score,
        }
        for run in rows
    ]
    return {"asof_date": resolved.isoformat(), "points": points}
