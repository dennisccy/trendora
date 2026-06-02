"""GET /api/methodology — the config-backed Setup & Pattern catalog (iter-12, J-12).

Returns `build_catalog(get_config())`: the single source for the /methodology page, the
/stocks setup/VCP badge tooltips, AND the /stocks setup-filter vocabulary (anti-goal: Setup & pattern
vocabulary is config-driven in the UI too). It re-formats config only — it recomputes NO
score/return/bucket and needs NO DB/session (it reads config, not a snapshot).

Honest universe gate (J-22): the catalog's `universe_selection` section asserts the universe is a
REPRODUCIBLE SCREEN RESULT (S&P 500 ∪ Nasdaq-100 ∪ prior, filtered by `universe.filters` over real
committed EOD data). That claim is only true once the offline screen has actually run and committed its
record (`data/seed/universe.json`). Until then the universe is the prior curated list, so we MUST NOT
present it as a screen — that would be a hand-curated list masquerading as a screen (anti-goal:
*Universe screen is reproducible & honest*). So the section is served ONLY when the committed screen
record exists; it reappears automatically, with the real screened members, the moment the screen runs.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.config import get_config
from app.engine.methodology import build_catalog
from app.seed_loader import DEFAULT_SEED_DIR, load_universe_screen_record

router = APIRouter(tags=["methodology"])


@router.get("/methodology")
def methodology() -> dict:
    """The Setup & Pattern glossary catalog (config-backed, read-only; no DB).

    Suppresses the `universe_selection` section until the committed screen record exists, so the
    served universe is never claimed to be a screen result before the screen has run (see module note).
    """
    catalog = build_catalog(get_config())
    if not load_universe_screen_record(DEFAULT_SEED_DIR):
        catalog.pop("universe_selection", None)
    return catalog
