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

from sqlalchemy import func
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine.prices import latest_data_date
from app.engine.regime import score_regime
from app.engine.scoring import score_stocks
from app.engine.sectors import score_sectors
from app.engine.setups import summarize_candidates
from app.engine.themes import score_themes
from app.models import DailyPrice, ScannerResult, ScannerRun, SectorScoreRow, ThemeScoreRow


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
                record_json=json.dumps(row),  # the COMPLETE canonical row dict (lossless, incl. patterns)
                # denormalized MIRRORS of each detected pattern's <name>.flagged (the same single
                # detector output) — written once here for the forward-test by_<name> grouping;
                # recomputes nothing (one detector call per run, in score_stocks).
                is_vcp=row["vcp"]["flagged"],
                is_pullback_to_rising_dma=row["pullback_to_rising_dma"]["flagged"],
                is_flat_base_breakout=row["flat_base_breakout"]["flagged"],
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


# --- iter-8 as-of resolution: map ?as_of= to its IMMUTABLE stored snapshot (J-15 + J-13) --------
# The read path serves canonical values from the persisted snapshot for the resolved date instead of
# recomputing per request (anti-goal: No recompute in the read path). Resolution is create-once and
# lookahead-free — both inherited from `run_scan` above (anti-goals: Snapshots immutable / No
# lookahead). The engine raises a SEMANTIC error (no HTTP/status literal here); the API layer maps it.
class AsOfError(Exception):
    """An as-of date could not be resolved to a stored (or creatable) immutable snapshot.

    `kind` is the semantic reason the API layer maps to an explicit HTTP status — so the engine stays
    free of web concerns and of any status-code literal. The resolver NEVER fabricates a snapshot for
    an invalid date (anti-goal: No fabricated data):
      - "no_data"        — no price data exists at all.
      - "unparseable"    — the as-of string is not a valid ISO date.
      - "future"         — the as-of date is after the latest available data date.
      - "before_history" — the as-of date is before the earliest bar (no bar with date <= D).
    """

    def __init__(self, kind: str, detail: str):
        self.kind = kind
        self.detail = detail
        super().__init__(detail)


def _latest_stored_run_date(session: Session) -> Optional[date_cls]:
    """The most recent persisted run's as-of date, or None when no run is stored yet."""
    return session.scalar(select(func.max(ScannerRun.asof_date)))


def resolve_as_of_date(
    session: Session, as_of: Optional[str], config: Optional[Config] = None
) -> date_cls:
    """Resolve an optional ?as_of= string to a concrete, snapshot-resolvable trading date.

    `None` / empty -> the latest STORED run's as-of date (falling back to the latest data date when no
    run is stored yet, so a not-yet-bootstrapped DB still resolves). A provided string is validated
    against the frozen seed WITHOUT fabricating anything, raising `AsOfError` with the matching kind:
    not a valid ISO date -> "unparseable"; after the latest data date -> "future"; before the earliest
    bar (no bar with date <= D) -> "before_history". A valid in-range date is returned unchanged; the
    caller load-or-creates its immutable snapshot exactly once. No price data at all -> "no_data"."""
    latest = latest_data_date(session)
    if latest is None:
        raise AsOfError("no_data", "no price data available")
    if not as_of:
        return _latest_stored_run_date(session) or latest
    try:
        target = date_cls.fromisoformat(as_of)
    except (TypeError, ValueError):
        raise AsOfError("unparseable", f"as_of is not a valid ISO date: {as_of!r}")
    if target > latest:
        raise AsOfError(
            "future", f"as_of {target.isoformat()} is after the latest data date {latest.isoformat()}"
        )
    has_bar_on_or_before = session.scalar(
        select(DailyPrice.id).where(DailyPrice.date <= target).limit(1)
    )
    if has_bar_on_or_before is None:
        raise AsOfError(
            "before_history", f"as_of {target.isoformat()} is before the available price history"
        )
    return target


def resolve_run(
    session: Session, as_of: Optional[str], config: Optional[Config] = None
) -> ScannerRun:
    """Resolve ?as_of= to its IMMUTABLE stored snapshot: return the existing run for the resolved
    date, or create it EXACTLY ONCE via `run_scan` (INSERT-only, bars <= D, idempotent + immutable).
    `as_of=None` resolves to the latest stored run. Raises `AsOfError` for an absent/invalid date —
    never a fabricated snapshot. The read endpoints serve the returned run's STORED rows; the
    canonical engines run only on first creation, never per request for an already-persisted date."""
    cfg = config or get_config()
    target = resolve_as_of_date(session, as_of, cfg)
    return run_scan(session, target, cfg)
