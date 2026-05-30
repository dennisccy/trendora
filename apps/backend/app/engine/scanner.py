"""Scanner snapshots — the persistence spine (Data Contract: app.engine.scanner).

`run_scan(session, asof, cfg)` calls the EXISTING canonical engine functions ONCE for `asof`
(`score_regime`, `score_sectors`, `score_themes`, `score_stocks`, `setups.summarize_candidates`)
and persists ONE complete immutable snapshot (a `ScannerRun` plus its `ScannerResult` /
`SectorScoreRow` / `ThemeScoreRow` children) in a single transaction. It RECOMPUTES NOTHING — every
stored value is a faithful copy of a canonical engine output (single source of truth). The run
summary (regime, breadth, net new-high/low, candidate counts) is READ from `score_regime`'s output
and `summarize_candidates`, never recomputed from a second formula (the iter-2 coherence lesson).

Idempotent + immutable (anti-goal: Snapshots are immutable): if a run already exists for `asof_date`
it is returned unchanged — never a second run for that date, never an UPDATE/overwrite of an existing
row or its children. The gitignored DB is ephemeral; on a fresh DB the idempotent bootstrap
deterministically re-creates identical runs from the frozen seed (reproducibility, not mutation).

No lookahead (anti-goal): the canonical engines read every bar through `bars_asof` (date <= asof),
so a run dated D is computed only from information available on D.

`bootstrap_runs(session_or_engine, cfg)` ensures a persisted run for every
`cfg.scanner.bootstrap_dates` date PLUS the latest data date (added programmatically). It reads ONLY
the committed frozen seed (via the engines' `bars_asof`) — it never fetches live data.

Forward returns (iter-6) will land in a SEPARATE append-only table keyed to the snapshot
(run_id, stock, horizon); the snapshot itself is never mutated.
"""
from __future__ import annotations

import json
from datetime import date as date_cls, datetime, timezone
from typing import Optional, Union

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine.prices import latest_data_date
from app.engine.regime import score_regime
from app.engine.scoring import score_stocks
from app.engine.sectors import score_sectors
from app.engine.setups import summarize_candidates
from app.engine.themes import score_themes
from app.models import ScannerResult, ScannerRun, SectorScoreRow, ThemeScoreRow


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_run_for_date(session: Session, asof: date_cls) -> Optional[ScannerRun]:
    """The persisted run for an as-of date, or None. One run per date (asof_date is unique)."""
    return session.scalar(select(ScannerRun).where(ScannerRun.asof_date == asof))


def run_scan(session: Session, asof: date_cls, config: Optional[Config] = None) -> ScannerRun:
    """Persist (or return the existing) immutable snapshot for `asof`. Calls the canonical engines
    once; stores faithful copies. Idempotent + immutable — a second call for the same date never
    creates a duplicate and never mutates the stored rows."""
    cfg = config or get_config()

    existing = get_run_for_date(session, asof)
    if existing is not None:
        return existing  # immutable: never re-create or overwrite an existing run

    # Canonical engines — each called ONCE for `asof`. No scoring math is reimplemented here.
    regime = score_regime(session, asof, cfg)
    sector_result = score_sectors(session, asof, cfg)
    theme_result = score_themes(session, asof, cfg)
    stock_result = score_stocks(session, asof, cfg)
    # candidate counts: READ from the SINGLE canonical derivation (counts the per-stock setup
    # statuses) — never recomputed from a second formula here.
    candidate_counts = summarize_candidates(stock_result["rows"])

    run = ScannerRun(
        asof_date=asof,
        created_at=_utcnow(),
        provider=cfg.provider,
        benchmark=stock_result["benchmark"],
        regime_score=regime["score"],
        regime_label=regime["label"],
        regime_components_json=json.dumps(regime["components"]),
        breadth_above_50dma=regime["breadth_above_50dma"],
        breadth_above_200dma=regime["breadth_above_200dma"],
        new_high_low_json=json.dumps(regime["new_high_low"]),
        candidate_counts_json=json.dumps(candidate_counts),
    )
    session.add(run)
    session.flush()  # assign run.id for the child foreign keys

    for row in stock_result["rows"]:
        session.add(
            ScannerResult(
                run_id=run.id,
                ticker=row["ticker"],
                name=row["name"],
                sector=row["sector"],
                leadership_score=row["leadership"]["score"],
                leadership_bucket=row["leadership"]["bucket"],
                entry_quality_score=row["entry_quality"]["score"],
                entry_quality_bucket=row["entry_quality"]["bucket"],
                risk_score=row["risk"]["score"],
                risk_bucket=row["risk"]["bucket"],
                setup_status=row["setup"]["status"],
                rank=row["rank"],
                record_json=json.dumps(row),  # the COMPLETE canonical row dict (lossless)
            )
        )

    for row in sector_result["rows"]:
        session.add(
            SectorScoreRow(
                run_id=run.id,
                ticker=row["ticker"],
                kind=row["kind"],
                name=row["name"],
                score=row["score"],
                bucket=row["bucket"],
                rs_vs_spy=row["rs_vs_spy"],
                dist_from_52w_high_pct=row["dist_from_52w_high_pct"],
                trend_label=row["trend_label"],
                components_json=json.dumps(row["components"]),
                rank=row["rank"],
            )
        )

    for row in theme_result["rows"]:
        session.add(
            ThemeScoreRow(
                run_id=run.id,
                slug=row["slug"],
                name=row["name"],
                score=row["score"],
                bucket=row["bucket"],
                members_json=json.dumps(row["members"]),
                return_1m=row["return_1m"],
                return_3m=row["return_3m"],
                breadth_pct=row["breadth_pct"],
                breadth_label=row["breadth_label"],
                trend_label=row["trend_label"],
                components_json=json.dumps(row["components"]),
                rank=row["rank"],
            )
        )

    session.commit()
    return run


def _bootstrap(session: Session, cfg: Config) -> list[ScannerRun]:
    """Ensure a persisted run for every configured bootstrap date PLUS the latest data date."""
    latest = latest_data_date(session)
    if latest is None:
        return []  # no price data — nothing to bootstrap (the API surfaces 503 elsewhere)

    # configured historical dates + the latest data date (appended in code, not a config literal),
    # de-duplicated and order-preserving.
    asof_dates: list[date_cls] = []
    for candidate in [*cfg.scanner.bootstrap_dates, latest]:
        if candidate not in asof_dates:
            asof_dates.append(candidate)

    return [run_scan(session, asof, cfg) for asof in asof_dates]


def bootstrap_runs(
    session_or_engine: Union[Session, Engine], config: Optional[Config] = None
) -> list[ScannerRun]:
    """Idempotently persist a snapshot for every configured bootstrap date + the latest data date.
    Accepts a `Session` (used by tests) or an `Engine` (used by the app lifespan). Reads ONLY the
    committed frozen seed — never fetches live data."""
    cfg = config or get_config()
    if isinstance(session_or_engine, Session):
        return _bootstrap(session_or_engine, cfg)
    with Session(session_or_engine) as session:
        return _bootstrap(session, cfg)
