"""Live-vs-seed drift monitor (goal-mcp-loop iter-35, J-21 / backlog B-304 — OVERLAP CHECK ONLY).

`app.engine.drift` is a PURE comparator + single writer/reader pair for the drift-report artifact:

  - `build_drift_report` — byte/fixed-precision OHLCV compare (never a loose float tolerance) over the
    last `overlap_days` dates COMMON to a fetch and the committed seed. Fixture matrix: a re-adjusted
    overlap is detected with the exact mismatching dates + `adjustment_seam` classification; a clean
    overlap reports `status == "clean"` with an empty `affected` list; a byte/fixed-precision compare
    catches a real (small-magnitude) seam a loose/tolerant float compare would miss (the named B-304
    trap); only the last `overlap_days` COMMON dates are ever compared (older mismatches outside the
    window are invisible); a symbol absent from the seed entirely is never flagged (honest skip, no
    KeyError).
  - `resolve_drift_report_path` — env override, else config default resolved against REPO_ROOT (mirrors
    `app.engine.evidence.resolve_ledger_path` exactly).
  - `write_drift_report` / `read_drift_report` — a single writer/reader pair; a missing artifact is
    inert (`None`); an unparseable artifact reads back an honest `status == "unreadable"` — NEVER a
    raise.
"""
from __future__ import annotations

import os
from datetime import date

import pytest

from app.config import REPO_ROOT, get_config
from app.data_providers.base import Bar
from app.engine.drift import (
    DRIFT_REPORT_PATH_ENV,
    STATUS_CLEAN,
    STATUS_DRIFT,
    STATUS_UNREADABLE,
    build_drift_report,
    read_drift_report,
    resolve_drift_report_path,
    write_drift_report,
)


def _bar(d: date, *, close: float = 100.0, open_: float = 100.0, high: float = 101.0, low: float = 99.0, volume: float = 1000.0) -> Bar:
    return Bar(date=d, open=open_, high=high, low=low, close=close, volume=volume)


# ==================================================================================================
# build_drift_report — fixture matrix
# ==================================================================================================
def test_clean_overlap_reports_clean_status_and_empty_affected():
    dates = [date(2024, 3, 1), date(2024, 3, 4), date(2024, 3, 5)]
    seed = {"AAA": [_bar(d) for d in dates]}
    fetched = {"AAA": [_bar(d) for d in dates]}  # byte-identical re-fetch
    report = build_drift_report(fetched, seed, overlap_days=5, reference="2024-03-05")
    assert report == {
        "status": STATUS_CLEAN,
        "reference": "2024-03-05",
        "overlap_days": 5,
        "affected": [],
    }


def test_readjusted_overlap_detected_with_exact_symbol_and_dates():
    seed = {
        "AAA": [
            _bar(date(2024, 3, 1), close=100.0),
            _bar(date(2024, 3, 4), close=101.0),
            _bar(date(2024, 3, 5), close=102.0),
        ]
    }
    # the vendor re-adjusted the 3/1 close (a whole-history back-adjustment on a dividend/split) — the
    # OTHER two dates are byte-identical.
    fetched = {
        "AAA": [
            _bar(date(2024, 3, 1), close=95.0),
            _bar(date(2024, 3, 4), close=101.0),
            _bar(date(2024, 3, 5), close=102.0),
        ]
    }
    report = build_drift_report(fetched, seed, overlap_days=5, reference="2024-03-05")
    assert report["status"] == STATUS_DRIFT
    assert report["affected"] == [
        {"symbol": "AAA", "mismatching_dates": ["2024-03-01"], "classification": "adjustment_seam"}
    ]


def test_small_price_delta_is_flagged_never_smoothed_by_a_tolerance_window():
    """The B-304 trap: a 1-cent close delta is exactly the kind of 'surely just rounding' difference a
    loose `abs(a - b) < 0.01` comparator would silently let through. This must FAIL if the comparator is
    ever 'simplified' to a numeric tolerance window instead of exact fixed-precision equality."""
    d = date(2024, 3, 1)
    seed = {"AAA": [_bar(d, close=100.00)]}
    fetched = {"AAA": [_bar(d, close=100.01)]}
    report = build_drift_report(fetched, seed, overlap_days=5, reference="2024-03-01")
    assert report["status"] == STATUS_DRIFT
    assert report["affected"] == [
        {"symbol": "AAA", "mismatching_dates": ["2024-03-01"], "classification": "adjustment_seam"}
    ]


def test_mismatch_in_any_single_ohlcv_field_is_sufficient():
    """A mismatch on ANY of open/high/low/close/volume (not just close) is caught."""
    d = date(2024, 3, 1)
    base = {"open_": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000.0}
    for field in ("open_", "high", "low", "close", "volume"):
        bumped = dict(base)
        bumped[field] = bumped[field] + 5.0
        seed = {"AAA": [_bar(d, **base)]}
        fetched = {"AAA": [_bar(d, **bumped)]}
        report = build_drift_report(fetched, seed, overlap_days=5, reference="2024-03-01")
        assert report["status"] == STATUS_DRIFT, f"field {field} mismatch was not detected"


def test_only_last_overlap_days_common_dates_are_compared():
    """A mismatch OUTSIDE the last `overlap_days` common dates is invisible (bounded window, per the
    iter-24/26 anti-goal-#8 lesson — a bounded per-symbol overlap-window compare, never the whole
    history); a mismatch INSIDE the window is still caught."""
    dates = [date(2024, 3, d) for d in (1, 4, 5, 6, 7)]  # 5 common dates
    seed = {"AAA": [_bar(d, close=100.0 + i) for i, d in enumerate(dates)]}

    # mismatch on the OLDEST date only, outside a 2-day window -> invisible -> clean
    fetched_old_only = {
        "AAA": [
            _bar(dates[0], close=999.0),  # re-adjusted, but outside the window
            *[_bar(d, close=100.0 + i) for i, d in enumerate(dates) if i > 0],
        ]
    }
    report = build_drift_report(fetched_old_only, seed, overlap_days=2, reference="2024-03-07")
    assert report["status"] == STATUS_CLEAN

    # mismatch on the NEWEST date -> inside a 2-day window -> caught
    fetched_recent = {
        "AAA": [
            *[_bar(d, close=100.0 + i) for i, d in enumerate(dates) if i < 4],
            _bar(dates[4], close=999.0),
        ]
    }
    report2 = build_drift_report(fetched_recent, seed, overlap_days=2, reference="2024-03-07")
    assert report2["status"] == STATUS_DRIFT
    assert report2["affected"][0]["mismatching_dates"] == ["2024-03-07"]


def test_symbol_absent_from_seed_is_not_flagged_no_crash():
    """A fetched symbol with NO committed-seed history at all (e.g. a brand-new universe member) has no
    common dates to compare -- an honest skip, never a KeyError or a fabricated mismatch."""
    fetched = {"NEWCO": [_bar(date(2024, 3, 1))]}
    report = build_drift_report(fetched, seed_bars={}, overlap_days=5, reference="2024-03-01")
    assert report == {"status": STATUS_CLEAN, "reference": "2024-03-01", "overlap_days": 5, "affected": []}


def test_multiple_symbols_only_mismatching_ones_are_affected():
    d = date(2024, 3, 1)
    seed = {"AAA": [_bar(d, close=100.0)], "BBB": [_bar(d, close=50.0)], "CCC": [_bar(d, close=10.0)]}
    fetched = {"AAA": [_bar(d, close=100.0)], "BBB": [_bar(d, close=999.0)], "CCC": [_bar(d, close=10.0)]}
    report = build_drift_report(fetched, seed, overlap_days=5, reference="2024-03-01")
    assert report["status"] == STATUS_DRIFT
    assert [a["symbol"] for a in report["affected"]] == ["BBB"]


# ==================================================================================================
# resolve_drift_report_path -- env override / config default (mirrors resolve_ledger_path exactly)
# ==================================================================================================
def test_resolve_drift_report_path_env_override(tmp_path, monkeypatch):
    override = tmp_path / "custom-drift-report.json"
    monkeypatch.setenv(DRIFT_REPORT_PATH_ENV, str(override))
    assert resolve_drift_report_path() == str(override)


def test_resolve_drift_report_path_config_default(monkeypatch):
    monkeypatch.delenv(DRIFT_REPORT_PATH_ENV, raising=False)
    resolved = resolve_drift_report_path()
    configured = get_config().data_quality.drift.report_path
    assert resolved == str(REPO_ROOT / configured)
    assert os.path.isabs(resolved)


# ==================================================================================================
# write_drift_report / read_drift_report -- single writer/reader pair
# ==================================================================================================
def test_write_then_read_round_trips(tmp_path, monkeypatch):
    target = tmp_path / "nested" / "drift-report.json"
    monkeypatch.setenv(DRIFT_REPORT_PATH_ENV, str(target))
    report = {"status": STATUS_DRIFT, "reference": "2024-03-01", "overlap_days": 5,
               "affected": [{"symbol": "AAA", "mismatching_dates": ["2024-03-01"], "classification": "adjustment_seam"}]}
    write_drift_report(report)
    assert target.exists()  # write_drift_report creates the parent directory on first write
    assert read_drift_report() == report


def test_read_missing_artifact_is_inert_none(tmp_path, monkeypatch):
    monkeypatch.setenv(DRIFT_REPORT_PATH_ENV, str(tmp_path / "never-written.json"))
    assert read_drift_report() is None


def test_read_unparseable_artifact_is_honest_never_raises(tmp_path, monkeypatch):
    target = tmp_path / "corrupt-drift-report.json"
    target.write_text("{not valid json")
    monkeypatch.setenv(DRIFT_REPORT_PATH_ENV, str(target))
    report = read_drift_report()  # must not raise
    assert report is not None
    assert report["status"] == STATUS_UNREADABLE


def test_write_overwrites_the_single_artifact_not_append(tmp_path, monkeypatch):
    """The drift artifact is a SINGLE overwritten snapshot (only the latest fetch's status matters for
    readiness) -- NOT an append-only ledger."""
    target = tmp_path / "drift-report.json"
    monkeypatch.setenv(DRIFT_REPORT_PATH_ENV, str(target))
    write_drift_report({"status": STATUS_DRIFT, "reference": "d1", "overlap_days": 5, "affected": []})
    write_drift_report({"status": STATUS_CLEAN, "reference": "d2", "overlap_days": 5, "affected": []})
    assert read_drift_report()["status"] == STATUS_CLEAN
    assert read_drift_report()["reference"] == "d2"
