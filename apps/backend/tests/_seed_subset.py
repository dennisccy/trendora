"""Read-only subset-DB builders for the heavy-fixture pytest files that used to `shutil.copyfile`/
`copy2` the live 7.8 GB `apps/backend/data/trendora.db` (goal-market-compass iter-5, goal.md
Constraint (a) / host resource-fit, owner 2026-08-20 after the desktop-freeze incident):
`test_evidence_drawdown_memory_pressure.py`, `test_samples_memory_pressure.py`, and
`test_start_backend_script.py`'s three copy sites (`spawned_backend_fast_graceful_timeout`,
`spawned_backend_throwaway_db`, `spawned_backend_throwaway_db_fault_injected`).

Every builder here creates a FRESH destination SQLite file via the real `app.db` schema, then
`ATTACH`es the real committed DB **READ-ONLY** (`file:...?mode=ro`) and `INSERT ... SELECT`s only the
rows a given test actually needs. This never does a byte-level file copy (no doubled 7.8 GB disk
usage, no multi-second whole-file I/O) and never opens the real file for writing — the ATTACH is a
SQLite-native, single-connection, streamed copy of just the matching rows.

`test_ingest_finalize_memory_pressure.py` needs no builder here — it already synthesizes its fixture
DB from scratch (fake `MPT#######` tickers) and never touched the real file; it only needed the new
`TRENDORA_MEMORY_PRESSURE` opt-in gate (see that file)."""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_DB = REPO_ROOT / "apps/backend/data/trendora.db"

# Reference/universe tables: small, NOT date-partitioned — copied in full whenever a builder needs a
# functioning universe (the windowed builder; the research-only builder needs none of them, since
# `_factor_observations`/`_factor_samples` read sector/name straight off the copied `scanner_results`
# row, never these lookup tables).
_REFERENCE_TABLES = ("sectors", "industries", "stocks", "etfs", "themes", "theme_members")


def real_db_available() -> bool:
    return REAL_DB.exists()


def _attach_real_db_readonly(conn: sqlite3.Connection) -> None:
    # `mode=ro` — a SQLite read-only open; never takes a write lock, never mutates the real file. The
    # destination connection must be opened with `uri=True` (below) for ATTACH's own filename argument
    # to be URI-interpreted too (SQLite ties that to the connection, not the individual statement).
    conn.execute("ATTACH DATABASE ? AS src", (f"file:{REAL_DB}?mode=ro",))


def _fresh_dest_engine(dest_path: Path):
    """Create `dest_path`'s schema via the real `app.db`/`app.models` metadata (the SAME schema the
    live app expects — additive columns included, since they are already plain model fields), then
    dispose the SQLAlchemy engine so the file has no lingering pooled connection before the raw
    `sqlite3` copy step below opens it directly."""
    from app.db import create_db_and_tables, make_engine

    engine = make_engine(f"sqlite:///{dest_path}")
    create_db_and_tables(engine)
    engine.dispose()


def build_research_subset_db(dest_path: Path, *, horizons: list[int]) -> None:
    """For `test_evidence_drawdown_memory_pressure.py` / `test_samples_memory_pressure.py`: every
    `scanner_runs` and `scanner_results` row (UNCHANGED population for a given horizon — these two
    files' own calibration docstrings measure ~1.2-1.26M horizon-20 observations across essentially
    all stored runs, so keeping both tables whole preserves the exact population the existing
    `TIGHT_CAP_KB`/`STARVED_CAP_KB`/`CONTROL_CAP_KB` constants were calibrated against), but
    `forward_returns` filtered to ONLY `horizons` (both files' claims are horizon=20 today — the other
    4 configured horizons are dropped, a real reduction) and every other table (`daily_prices`, the
    reference/universe tables, every cache table) left absent/empty.

    Consequence, deliberately accepted: `phase_context_by_date` (called inside
    `compute_drawdown_expectations`) finds no `daily_prices` bars for the benchmark/^VIX and honestly
    returns `{}` (`_severity_reading` reads "insufficient history" for every run -> None), so the
    `by_phase` cells in the returned payload are all n=0. Neither test file inspects `by_phase`
    VALUES — both only assert the `RESULT=.../SUBSEQUENT_READ_OK` child-process sentinels — so this
    does not weaken what either test proves."""
    if not horizons:
        raise ValueError("build_research_subset_db requires at least one horizon")
    _fresh_dest_engine(dest_path)
    conn = sqlite3.connect(f"file:{dest_path}", uri=True)
    try:
        _attach_real_db_readonly(conn)
        conn.execute("INSERT INTO main.scanner_runs SELECT * FROM src.scanner_runs")
        conn.execute("INSERT INTO main.scanner_results SELECT * FROM src.scanner_results")
        placeholders = ",".join("?" * len(horizons))
        conn.execute(
            f"INSERT INTO main.forward_returns SELECT * FROM src.forward_returns "
            f"WHERE horizon IN ({placeholders})",
            horizons,
        )
        conn.commit()
    finally:
        conn.execute("DETACH DATABASE src")
        conn.close()


def build_windowed_subset_db(dest_path: Path, *, trading_days: int = 300, price_lookback_pad_days: int = 400) -> date:
    """For `test_start_backend_script.py`'s 3 real-backend-process fixtures (SIGTERM-under-load,
    back-to-back heavy ingest, ingest-finalize fault injection): a REAL, functioning (if
    shorter-history) database a spawned backend can boot against and run a genuine `rebuild`/`backfill`
    over — not a byte-copy of the full 30-year file.

    Windowed to the most recent `trading_days` stored `scanner_runs` dates (default 300, ~14 months):
    every date-partitioned table (`daily_prices`, `scanner_runs`, `scanner_results`, `sector_scores`,
    `theme_scores`, `forward_returns` — ALL configured horizons this time, since these fixtures drive
    the real finalize tail end to end) is filtered to that window; `daily_prices` additionally starts
    `price_lookback_pad_days` calendar days EARLIER than the window so trailing-indicator lookback
    (moving averages, 52w-high, …) has real history at the window's own start instead of an all-NA
    ramp-up. The small reference/universe tables are copied whole (`_REFERENCE_TABLES`). Job-control
    and cache tables (`data_provider_runs`, `import_checkpoints`, every `*_cache` table,
    `next_session_manifests`, `coverage_snapshot`) are left EMPTY — correct for a throwaway DB that is
    about to run its own fresh jobs and warm its own caches, never inherited/stale state.
    `watchlist`/`macro_series` are copied whole (small, non-date-partitioned-in-a-way-that-matters).

    Returns the resolved window-start `asof_date` (the earliest `scanner_runs` date retained) so a
    caller can pick a real, in-window trading day for its own use (e.g. `_pick_unsnapshotted_trading_day`
    already does this itself via the spawned backend's own `/api/runs`, so callers rarely need this).

    None of the three fixtures' own tests hard-assert an exact wall-clock duration tied to full 30-year
    scale (they use generous multi-minute timeouts and runtime-derived dates via
    `_pick_unsnapshotted_trading_day`/`GET /api/runs`) — a smaller window makes a `rebuild`/`backfill`
    complete FASTER, which only adds slack under those timeouts, never breaks them."""
    if not real_db_available():
        raise FileNotFoundError(f"real dev DB not found at {REAL_DB} — nothing to subset")
    _fresh_dest_engine(dest_path)
    conn = sqlite3.connect(f"file:{dest_path}", uri=True)
    try:
        _attach_real_db_readonly(conn)
        (window_start_raw,) = conn.execute(
            "SELECT MIN(asof_date) FROM ("
            "  SELECT asof_date FROM src.scanner_runs ORDER BY asof_date DESC LIMIT ?"
            ")",
            (trading_days,),
        ).fetchone()
        if window_start_raw is None:
            raise RuntimeError("real dev DB has no scanner_runs rows — nothing to window")
        window_start = date.fromisoformat(window_start_raw)
        price_start = (window_start - timedelta(days=price_lookback_pad_days)).isoformat()

        for table in _REFERENCE_TABLES:
            conn.execute(f"INSERT INTO main.{table} SELECT * FROM src.{table}")
        conn.execute("INSERT INTO main.watchlist SELECT * FROM src.watchlist")
        conn.execute("INSERT INTO main.macro_series SELECT * FROM src.macro_series")

        conn.execute(
            "INSERT INTO main.daily_prices SELECT * FROM src.daily_prices WHERE date >= ?", (price_start,)
        )
        conn.execute(
            "INSERT INTO main.scanner_runs SELECT * FROM src.scanner_runs WHERE asof_date >= ?",
            (window_start_raw,),
        )
        run_id_subquery = "SELECT id FROM src.scanner_runs WHERE asof_date >= ?"
        for table in ("scanner_results", "sector_scores", "theme_scores"):
            conn.execute(
                f"INSERT INTO main.{table} SELECT * FROM src.{table} "
                f"WHERE run_id IN ({run_id_subquery})",
                (window_start_raw,),
            )
        conn.execute(
            "INSERT INTO main.forward_returns SELECT * FROM src.forward_returns WHERE asof_date >= ?",
            (window_start_raw,),
        )
        conn.commit()
        return window_start
    finally:
        conn.execute("DETACH DATABASE src")
        conn.close()
