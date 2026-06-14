"""J-69 — range-only, accident-proof destructive removal (the `POST /api/data/remove(/preview)` contract).

The destructive Remove-data UI flow on `/data` is now scoped PURELY by a `[start, end]` date range over
ALL symbols, with BOTH dates MANDATORY (guarding against an accidental delete-everything). These tests
prove the HTTP contract the endpoints enforce via `require_range=True`:

  - a single-ended date scope (start without end, or end without start) is rejected with an honest 400;
  - an empty scope (no symbols, no dates) is rejected with an honest 400;
  - a valid range-only `{start, end}` (no symbols) is ACCEPTED (no range-required error) — and the
    committed-seed protection + seed-safe refusal/`reason` (J-39) and the impact counts (single-sourced
    from the real backend computation) are UNCHANGED;
  - the same range-required guard applies to BOTH the preview and the destructive remove endpoints.

The engine-level symbol-scoped path (`require_range=False`) is unaffected — it is exercised in
`test_data_manager.py`; here we test the ENDPOINTS (which always require a range).
"""
from __future__ import annotations

import datetime as _dt
import json
from datetime import date
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

import app.db as db_module
from app.api.data import RemoveScope, remove_data_endpoint, remove_preview
from app.db import create_db_and_tables, make_engine
from app.engine import data_manager
from app.models import DailyPrice


def _bar_count(engine) -> int:
    with Session(engine) as session:
        return int(session.scalar(select(func.count(DailyPrice.id))) or 0)


def _write_seed_meta(seed_dir: Path, windows: dict[str, tuple[str, str, int]]) -> None:
    """Write a minimal committed-seed manifest (`meta.json`) — the seed-vs-user-added boundary J-39 reads."""
    seed_dir.mkdir(parents=True, exist_ok=True)
    symbols = [{"symbol": s, "first": f, "last": l, "bars": b} for s, (f, l, b) in windows.items()]
    meta = {"source": "test seed", "symbols_ok": len(symbols), "symbols_failed": 0, "symbols": symbols}
    (seed_dir / "meta.json").write_text(json.dumps(meta) + "\n")


@pytest.fixture()
def remove_api_engine(tmp_path, monkeypatch):
    """An isolated engine with SPY+AAA bars D1..D13 where D1..D10 are committed seed and D11..D13 are
    user-added (beyond the seed `last`). The committed-seed manifest is pointed at a temp dir so the real
    committed seed is never touched. Set as the process engine for the duration of the test."""
    seed_dir = tmp_path / "seed"
    _write_seed_meta(seed_dir, {"SPY": ("2024-01-01", "2024-01-10", 10), "AAA": ("2024-01-01", "2024-01-10", 10)})
    # the endpoints call preview_removal/remove_data with no seed_dir → DEFAULT_SEED_DIR; point that at temp.
    monkeypatch.setattr(data_manager, "DEFAULT_SEED_DIR", seed_dir)

    prev = db_module._engine
    engine = make_engine(f"sqlite:///{tmp_path / 'remove_api.db'}")
    create_db_and_tables(engine)
    days = [date(2024, 1, d) for d in range(1, 14)]  # D1..D13
    with Session(engine) as session:
        for sym in ("SPY", "AAA"):
            for d in days:
                session.add(DailyPrice(symbol=sym, date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
    db_module.set_engine(engine)
    yield engine, seed_dir, days
    db_module.set_engine(prev)


# ==================================================================================================
# single-ended / empty date scope → honest 400 (the accident-proof guard), on BOTH endpoints
# ==================================================================================================
@pytest.mark.parametrize("endpoint", [remove_preview, remove_data_endpoint])
def test_start_without_end_is_400(remove_api_engine, endpoint):
    """A scope with `start` but no `end` is rejected with 400 (both dates mandatory) — never an accidental
    open-ended wipe. Applies to BOTH the preview and the destructive remove endpoint."""
    engine, _seed, days = remove_api_engine
    with Session(engine) as session:
        with pytest.raises(HTTPException) as exc:
            endpoint(RemoveScope(start=days[10], end=None), session=session)
    assert exc.value.status_code == 400
    assert "both" in exc.value.detail.lower() and "end" in exc.value.detail.lower()


@pytest.mark.parametrize("endpoint", [remove_preview, remove_data_endpoint])
def test_end_without_start_is_400(remove_api_engine, endpoint):
    """A scope with `end` but no `start` is rejected with 400 (both dates mandatory)."""
    engine, _seed, days = remove_api_engine
    with Session(engine) as session:
        with pytest.raises(HTTPException) as exc:
            endpoint(RemoveScope(start=None, end=days[12]), session=session)
    assert exc.value.status_code == 400
    assert "both" in exc.value.detail.lower() and "start" in exc.value.detail.lower()


@pytest.mark.parametrize("endpoint", [remove_preview, remove_data_endpoint])
def test_empty_scope_is_400(remove_api_engine, endpoint):
    """An empty scope (no symbols, no dates) is rejected with 400 — never an accidental delete-everything.
    The range-required guard fires first (both dates mandatory)."""
    engine, _seed, _days = remove_api_engine
    with Session(engine) as session:
        with pytest.raises(HTTPException) as exc:
            endpoint(RemoveScope(), session=session)
    assert exc.value.status_code == 400


@pytest.mark.parametrize("endpoint", [remove_preview, remove_data_endpoint])
def test_symbols_only_no_range_is_400(remove_api_engine, endpoint):
    """The destructive UI flow is RANGE-ONLY: a symbols-only scope (no dates) is rejected with 400 even
    though the named symbol has stored bars — the endpoints require BOTH dates (the `symbols` field is
    kept in the schema for the internal path, not this destructive flow)."""
    engine, _seed, _days = remove_api_engine
    with Session(engine) as session:
        with pytest.raises(HTTPException) as exc:
            endpoint(RemoveScope(symbols=["AAA"]), session=session)
    assert exc.value.status_code == 400


@pytest.mark.parametrize("endpoint", [remove_preview, remove_data_endpoint])
def test_inverted_range_is_400(remove_api_engine, endpoint):
    """An inverted range (start > end) is still rejected with 400 (the J-39 guard is unchanged)."""
    engine, _seed, days = remove_api_engine
    with Session(engine) as session:
        with pytest.raises(HTTPException) as exc:
            endpoint(RemoveScope(start=days[12], end=days[10]), session=session)
    assert exc.value.status_code == 400
    assert "on or before" in exc.value.detail.lower()


# ==================================================================================================
# a valid range-only {start, end} (no symbols) is ACCEPTED — J-39 semantics unchanged
# ==================================================================================================
def test_preview_valid_range_only_accepted(remove_api_engine):
    """A valid range-only `{start, end}` (no symbols) is ACCEPTED by the preview (no range-required error)
    and returns the J-39 impact counts single-sourced from the real backend computation: the removable
    user-added bars over D11..D13 (SPY+AAA = 6 bars, 2 symbols), nothing committed-seed in scope, not
    refused. The preview DELETES NOTHING."""
    engine, _seed, days = remove_api_engine
    before = _bar_count(engine)
    with Session(engine) as session:
        prev = remove_preview(RemoveScope(start=days[10], end=days[12]), session=session)
    # range D11..D13 is wholly user-added (beyond the seed last D10) → 6 removable bars, 2 symbols.
    assert prev["removable_bar_count"] == 6
    assert prev["removable_symbol_count"] == 2  # SPY + AAA — the affected-symbol count the modal foregrounds
    assert prev["removable_first"] == days[10].isoformat()
    assert prev["removable_last"] == days[12].isoformat()
    assert prev["not_removable_bar_count"] == 0
    assert prev["refused"] is False
    # the preview deleted nothing.
    assert _bar_count(engine) == before == 26


def test_preview_wholly_seed_range_refused_unchanged(remove_api_engine):
    """A valid range that is wholly committed seed (D1..D5) is ACCEPTED by the range guard but REFUSED by
    the seed-safe logic (`refused=True` + explicit reason) — the J-39 seed-safe refusal is unchanged. A
    200 the UI renders to disable the confirm, not a 400."""
    engine, _seed, days = remove_api_engine
    with Session(engine) as session:
        prev = remove_preview(RemoveScope(start=days[0], end=days[4]), session=session)
    assert prev["removable_bar_count"] == 0
    assert prev["refused"] is True
    assert "committed seed" in prev["reason"].lower()
    assert prev["not_removable_bar_count"] == 10  # SPY & AAA on D1..D5


def test_remove_valid_range_only_executes_and_counts_match(remove_api_engine):
    """The destructive remove ACCEPTS a valid range-only `{start, end}` (no symbols), deletes ONLY the
    user-added bars (D11..D13), and reports a done-count that MATCHES the preview's removable count (the
    impact counts are single-sourced from the same real backend computation, never fabricated)."""
    engine, _seed, days = remove_api_engine
    with Session(engine) as session:
        prev = remove_preview(RemoveScope(start=days[10], end=days[12]), session=session)
    with Session(engine) as session:
        result = remove_data_endpoint(RemoveScope(start=days[10], end=days[12]), session=session)
    # the destructive done-count equals the preview's removable count — one computation, two reads.
    assert result["removed_bar_count"] == prev["removable_bar_count"] == 6
    assert result["removable_symbol_count"] == prev["removable_symbol_count"] == 2
    # only the user-added bars are gone; the committed seed (D1..D10 × 2 symbols = 20 bars) is untouched.
    assert _bar_count(engine) == 20  # 26 - 6 user-added = 20 committed-seed bars survive
