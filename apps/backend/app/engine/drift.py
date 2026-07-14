"""Live-vs-seed drift monitor (goal-mcp-loop iter-35, J-21 / backlog B-304 — OVERLAP CHECK ONLY).

When the live provider fetches new bars, the vendor may have silently RE-ADJUSTED already-committed
history (Stooq back-adjusts a symbol's WHOLE history on every dividend/split). Because the price DB is
INSERT-new-only (`data_manager._existing_dates` skips any date already stored), a re-adjusted value for an
already-covered date is silently DISCARDED — the DB keeps the OLD value forever, and nobody is told the
live feed disagrees with what was validated. This module is the detector: it byte/fixed-precision compares
the bars a fetch just returned against the **committed seed CSVs** (`data/seed/prices/{symbol}.csv` — the
validated history) for the last `overlap_days` dates common to both, and reports any mismatch as an
"adjustment seam". It NEVER mutates, reconciles, or re-fetches the fetched data (B-304 "Do NOT touch the
fetched data" — reconciliation is an owner decision, possibly a future re-basis); it only REPORTS.

Comparator discipline (the named B-304 trap): the compare is FIXED-PRECISION (6 decimal places, matching
the deepest precision the committed seed carries) and EXACT — never a tolerance window (`abs(a - b) <
eps`). A tolerant comparator would silently pass a genuine small-magnitude re-adjustment; see
`test_drift.py::test_small_price_delta_is_flagged_never_smoothed_by_a_tolerance_window`.

The artifact is a SINGLE overwritten JSON object (not an append-only ledger — only the most recent fetch's
drift status matters for the daily preflight verdict), written ONCE by the fetch pipeline's post-fetch
validation stage (`app.engine.data_manager._run_job`) and re-read VERBATIM by both
`app.engine.readiness.compute_preflight` (the `drift` preflight component) and the additive `drift` field
on `GET /api/data` (`app.api.data.data_overview`) — the single-source Data Contract. A missing artifact
(no fetch has run yet) is honestly inert; an unparseable one reads back an honest `status ==
"unreadable"` — `read_drift_report` NEVER raises.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from app.config import REPO_ROOT, get_config
from app.data_providers.base import Bar

# The environment-variable NAME (the NAME only — never a path VALUE literal in code) the runtime
# drift-report path may be overridden with. Mirrors `app.engine.evidence.LEDGER_PATH_ENV`.
DRIFT_REPORT_PATH_ENV = "TRENDORA_DRIFT_REPORT_PATH"

STATUS_CLEAN = "clean"
STATUS_DRIFT = "drift"
# The artifact file exists but could not be parsed as the expected JSON object — an honest degraded
# read (never silently treated as "clean", never a raise). Distinct from a MISSING artifact (`None`
# from `read_drift_report`), which means "no fetch has run yet" and is genuinely inert.
STATUS_UNREADABLE = "unreadable"

_OHLCV_FIELDS = ("open", "high", "low", "close", "volume")
# Fixed decimal places for the byte/fixed-precision comparator — matches the deepest precision the
# committed seed CSVs carry (e.g. `0.241539`). No magic number at the call site; named here once.
_COMPARE_PRECISION = 6


def resolve_drift_report_path() -> str:
    """The drift-report artifact path: the `TRENDORA_DRIFT_REPORT_PATH` env override if set, else
    `config.data_quality.drift.report_path` resolved against `REPO_ROOT` when relative. Mirrors
    `app.engine.evidence.resolve_ledger_path()` exactly, so the browser-qa/gate lanes and the fetch
    pipeline always resolve the SAME artifact. No path literal lives here — the default lives in config
    (anti-goal: No magic numbers)."""
    override = os.environ.get(DRIFT_REPORT_PATH_ENV)
    if override:
        return override
    configured = Path(get_config().data_quality.drift.report_path)
    if not configured.is_absolute():
        configured = REPO_ROOT / configured
    return str(configured)


def _fixed(value: float) -> str:
    """Fixed-precision string form of one OHLCV field value — the byte/fixed-precision comparator unit.
    Two values that format to different strings here ARE a mismatch, however small the numeric delta
    (never a tolerance window — the B-304 trap)."""
    return f"{float(value):.{_COMPARE_PRECISION}f}"


def _bars_mismatch(fetched: Bar, seed: Bar) -> bool:
    """True iff ANY OHLCV field differs at fixed precision between the two bars for the SAME date."""
    return any(_fixed(getattr(fetched, field)) != _fixed(getattr(seed, field)) for field in _OHLCV_FIELDS)


def build_drift_report(
    fetched_bars: dict[str, list[Bar]],
    seed_bars: dict[str, list[Bar]],
    *,
    overlap_days: int,
    reference: str,
) -> dict:
    """The SINGLE overlap comparator (PURE — recomputes/mutates nothing, touches no filesystem/DB).

    For each symbol present in `fetched_bars`, take the last `overlap_days` dates COMMON to
    `fetched_bars[symbol]` and `seed_bars[symbol]` (bounded — never the whole history, per the
    iter-24/26 anti-goal-#8 lesson), and byte/fixed-precision compare OHLCV on each. A symbol with no
    seed history at all (e.g. a brand-new universe member) has zero common dates and is honestly never
    flagged — no KeyError, no fabricated mismatch.

    Returns `{status: "clean"|"drift", reference, overlap_days, affected: [{symbol, mismatching_dates,
    classification: "adjustment_seam"}, ...]}`, `affected` sorted by symbol. `reference` is passed
    through verbatim — the caller supplies a DETERMINISTIC anchor (a job/fetch parameter, never
    `date.today()` — anti-goal #5)."""
    affected: list[dict] = []
    for symbol in sorted(fetched_bars):
        fetched_by_date = {bar.date: bar for bar in (fetched_bars.get(symbol) or [])}
        seed_by_date = {bar.date: bar for bar in (seed_bars.get(symbol) or [])}
        common_dates = sorted(set(fetched_by_date) & set(seed_by_date))
        window = common_dates[-overlap_days:] if overlap_days > 0 else []
        mismatching = [d for d in window if _bars_mismatch(fetched_by_date[d], seed_by_date[d])]
        if mismatching:
            affected.append({
                "symbol": symbol,
                "mismatching_dates": [d.isoformat() for d in mismatching],
                "classification": "adjustment_seam",
            })
    return {
        "status": STATUS_DRIFT if affected else STATUS_CLEAN,
        "reference": reference,
        "overlap_days": overlap_days,
        "affected": affected,
    }


def write_drift_report(report: dict) -> None:
    """Persist the SINGLE drift-report artifact (OVERWRITE, not append — only the latest fetch's status
    matters for the preflight verdict). Creates the parent directory on first write. Written via a
    temp-file-then-rename so a reader never observes a partially-written file."""
    path = resolve_drift_report_path()
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, sort_keys=True, default=str)
    os.replace(tmp_path, path)


def read_drift_report() -> Optional[dict]:
    """The SINGLE reader both `compute_preflight` and `GET /api/data` call — no second parse path.

    - Missing artifact (no fetch has run yet) -> `None`, the honest inert case (every caller treats
      `None` as "ok" / "no report to show", distinct from a confirmed `status == "clean"`).
    - Unparseable artifact -> an honest `{"status": "unreadable", ...}` dict — NEVER a raise, and never
      silently treated as clean (a corrupt artifact is worth surfacing, not hiding)."""
    path = resolve_drift_report_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        data = None
    if not isinstance(data, dict) or "status" not in data:
        return {"status": STATUS_UNREADABLE, "reference": None, "overlap_days": None, "affected": []}
    return data
