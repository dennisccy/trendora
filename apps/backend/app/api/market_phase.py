"""GET /api/market-phase — the CANONICAL read-only endpoint for the Market Phase & Severity layer
(Data Contract: app.engine.market_phase; J-87 + J-88).

For the resolved single global as-of date it serves the STRICTLY CAUSAL derivation VERBATIM: the
discrete phase (Expansion / Pullback / Correction / Bear / Recovery), the 0-100 severity with its named
component breakdown, the cycle legs (drawdown / off-trough), and the forward FILTERED P(bear) with its
disclosed observation vector. It recomputes NO canonical value (regime/breadth read verbatim from the
stored snapshot) and adds NO snapshot column.

The as-of is resolved by the SAME shared snapshot-served resolver every read endpoint uses
(`resolved_date`: unparseable -> 422, future/before-history -> 400, no data -> 503), so the panel
re-points with the single global as-of (`/api/market-phase?as_of=` — NOT a second date state, J-18). The
derivation is computed ONCE per resolved as-of and CACHED behind a `dataset_version` stamp (the SAME
stamp J-72's event-study cache uses, single-sourced), so a repeated read serves the stored aggregate and
the cache refreshes after any dataset change — never a stale figure.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.engine.market_phase import market_phase_cached
from app.engine.snapshot_serving import resolved_date

router = APIRouter(tags=["market-phase"])


@router.get("/market-phase")
def market_phase(as_of: Optional[str] = None, session: Session = Depends(get_session)) -> dict:
    """Serve the Market Phase & Severity derivation for the resolved as-of date. `as_of=None` resolves to
    the latest stored date; a provided date is validated by the shared resolver (4xx/503 on an invalid /
    out-of-range date — never a fabricated date). The payload is `market_phase_cached(...)` verbatim
    (byte-identical to a fresh compute; cached behind the dataset-version stamp)."""
    resolved = resolved_date(session, as_of, None)
    return market_phase_cached(session, resolved)
