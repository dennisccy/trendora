"""GET /api/methodology — the config-backed Setup & Pattern catalog (iter-12, J-12).

Returns `build_catalog(get_config())` verbatim: the single source for the /methodology page, the
/stocks setup/VCP badge tooltips, AND the /stocks setup-filter vocabulary (anti-goal: Setup & pattern
vocabulary is config-driven in the UI too). It re-formats config only — it recomputes NO
score/return/bucket and needs NO DB/session (it reads config, not a snapshot).
"""
from __future__ import annotations

from fastapi import APIRouter

from app.config import get_config
from app.engine.methodology import build_catalog

router = APIRouter(tags=["methodology"])


@router.get("/methodology")
def methodology() -> dict:
    """The Setup & Pattern glossary catalog (config-backed, read-only; no DB)."""
    return build_catalog(get_config())
