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

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db import get_session
from app.engine.market_phase import (
    market_phase_default_payload,
    market_phase_full_cached,
    retrospective_cached,
)
from app.engine.snapshot_serving import resolved_date

router = APIRouter(tags=["market-phase"])


@router.get("/market-phase")
def market_phase(
    as_of: Optional[str] = None,
    retrospective: bool = False,
    full: bool = Query(
        default=False,
        description=(
            "J-97 clamp-optional: when true, ADDITIVELY attach the full-history causal timeline series "
            "`timeline_full` ([{date, phase, p_bear, severity}]) for the Dashboard two-pane cross-view "
            "chart — read VERBATIM from the SAME cached derivation (no recompute, no new endpoint/cache). "
            "Default false serves the bounded card payload byte-identical to today (the `timeline` tail is "
            "unchanged); the full series is a display-only opt-in used only by the J-97 chart."
        ),
    ),
    session: Session = Depends(get_session),
) -> dict:
    """Serve the Market Phase & Severity derivation for the resolved as-of date. `as_of=None` resolves to
    the latest stored date; a provided date is validated by the shared resolver (4xx/503 on an invalid /
    out-of-range date — never a fabricated date). The payload is `market_phase_cached(...)` verbatim
    (byte-identical to a fresh compute; cached behind the dataset-version stamp) — it carries the CAUSAL
    timeline series + dated downtrend episodes + the recovery-turn signal (J-89 / J-90), all read from the
    SAME single causal derivation.

    iter-30 (J-89): the FENCED retrospective (full-sample / analysis-only) sub-view — the SMOOTHED P(bear)
    series + the peak-to-trough true-bear dating — is served ONLY when `retrospective=true`, behind the
    SEPARATE structural `retrospective` field (a sibling cached read under the SAME engine + dataset_version
    stamp). The smoothed probability is lookahead by construction and NEVER feeds any as-of value (the J-49
    fence); the fence is structural — `retrospective_cached` is a different code path that no causal field
    reads. When `retrospective=false` (the default) the heavy backward-smoother is not computed at all."""
    resolved = resolved_date(session, as_of, None)
    # iter-38 (J-97): `full=true` ADDITIVELY attaches the full-history causal `timeline_full` series for the
    # Dashboard two-pane cross-view (the SAME cached derivation — no recompute, no new cache/endpoint). The
    # default (`full=false`) strips that opt-in key so the card payload stays byte-identical to today.
    payload = (
        market_phase_full_cached(session, resolved)
        if full
        else market_phase_default_payload(session, resolved)
    )
    if retrospective:
        payload = {**payload, "retrospective": retrospective_cached(session, resolved)}
    return payload
