"""goal-market-compass iter-16 -- J-11 "OWNER RULING -- AVB two-row raw-volume correction before Stage D"
tests (Goals 1-4). Fixture-only throughout: file-backed temp sqlite databases (`tmp_path`, never
`apps/backend/data/trendora.db`) for anything that touches a real file path (the isolating hashes and the
manifest row-dump hash open a SEPARATE raw `sqlite3` `mode=ro` connection, which needs an actual file),
plain synthetic dicts for the pure derivation/comparison/mutation-evidence functions. The ONE real,
deliberate live write against the production database is the actual `run_j11_avb_correction.py --confirm`
execution itself (not a pytest test) -- its own true-start/true-end envelopes ARE the mutation-evidence
proof; see `docs/handoffs/goal-market-compass-iter-16-dev.md`.
"""
from __future__ import annotations

from datetime import date

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.engine import j11_avb_correction as corr
from app.engine import j11_avb_diagnostic as diag
from app.models import DailyPrice


@pytest.fixture()
def file_engine(tmp_path):
    """A REAL sqlite FILE-backed engine (never `sqlite://` in-memory, never the live product DB) --
    `capture_isolating_hashes`/`capture_manifest_row_dump_hash` open a separate raw `sqlite3` `mode=ro`
    connection against the file path, which requires an actual file on disk."""
    db_path = tmp_path / "test.db"
    eng = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)
    return eng, db_path


def _mk_price(session, symbol, d, o, h, l, c, v):
    row = DailyPrice(symbol=symbol, date=d, open=o, high=h, low=l, close=c, volume=v)
    session.add(row)
    return row


def _seed_avb_and_other(session):
    _mk_price(session, "AVB", date(2026, 8, 10), 100.0, 101.0, 99.0, 100.5, 2000.0)
    _mk_price(session, "AVB", date(2026, 8, 11), 183.22001534990548, 184.13001191846783, 181.7100027790582, 181.76001476703186, 1549436.0)
    _mk_price(session, "AVB", date(2026, 8, 12), 181.08999902870366, 182.0900043902787, 179.45999604273928, 179.79000697488598, 10350885.0)
    _mk_price(session, "AAPL", date(2026, 8, 11), 50.0, 51.0, 49.0, 50.5, 3000.0)
    session.commit()


# --- Goal 1: the isolating hashes -- byte-identical unless the specific touched scope changes ---------


def test_isolating_hashes_unaffected_by_a_target_date_volume_change(file_engine):
    engine, db_path = file_engine
    with Session(engine) as session:
        _seed_avb_and_other(session)
    before = corr.capture_isolating_hashes(db_path)

    with Session(engine) as session:
        row = session.exec(
            select(DailyPrice).where(DailyPrice.symbol == "AVB").where(DailyPrice.date == date(2026, 8, 11))
        ).one()
        row.volume = 554757.0
        session.add(row)
        session.commit()

    after = corr.capture_isolating_hashes(db_path)
    # OHLC-only excludes volume entirely -- unaffected by a volume-only change on ANY AVB date
    assert after["avb_ohlc_only"]["sha256"] == before["avb_ohlc_only"]["sha256"]
    # excludes the two target dates entirely -- unaffected by a change scoped to one of them
    assert after["avb_other_dates_full_row"]["sha256"] == before["avb_other_dates_full_row"]["sha256"]
    # the non-AVB population is untouched
    assert after["non_avb_full_row"]["sha256"] == before["non_avb_full_row"]["sha256"]


def test_avb_other_dates_hash_moves_if_a_non_target_avb_date_changes(file_engine):
    """Negative control: proves the isolating hashes are genuinely sensitive, not trivially inert."""
    engine, db_path = file_engine
    with Session(engine) as session:
        _seed_avb_and_other(session)
    before = corr.capture_isolating_hashes(db_path)

    with Session(engine) as session:
        row = session.exec(
            select(DailyPrice).where(DailyPrice.symbol == "AVB").where(DailyPrice.date == date(2026, 8, 10))
        ).one()
        row.volume = 999999.0
        session.add(row)
        session.commit()

    after = corr.capture_isolating_hashes(db_path)
    assert after["avb_other_dates_full_row"]["sha256"] != before["avb_other_dates_full_row"]["sha256"]
    assert after["avb_ohlc_only"]["sha256"] == before["avb_ohlc_only"]["sha256"]  # volume-only change


def test_non_avb_hash_moves_if_a_non_avb_row_changes(file_engine):
    engine, db_path = file_engine
    with Session(engine) as session:
        _seed_avb_and_other(session)
    before = corr.capture_isolating_hashes(db_path)

    with Session(engine) as session:
        row = session.exec(select(DailyPrice).where(DailyPrice.symbol == "AAPL")).one()
        row.volume = 1.0
        session.add(row)
        session.commit()

    after = corr.capture_isolating_hashes(db_path)
    assert after["non_avb_full_row"]["sha256"] != before["non_avb_full_row"]["sha256"]
    assert after["avb_ohlc_only"]["sha256"] == before["avb_ohlc_only"]["sha256"]
    assert after["avb_other_dates_full_row"]["sha256"] == before["avb_other_dates_full_row"]["sha256"]


def test_manifest_row_dump_hash_recipe_is_stable_and_order_independent_of_insertion(file_engine):
    engine, db_path = file_engine
    with Session(engine) as session:
        _seed_avb_and_other(session)
    first = corr.capture_manifest_row_dump_hash(db_path)
    second = corr.capture_manifest_row_dump_hash(db_path)
    assert first["sha256"] == second["sha256"]
    assert first["row_count"] == 0  # no manifests seeded in this fixture


# --- Goal 1: capture_true_envelope + fetch_avb_target_rows shape -------------------------------------


def test_capture_true_envelope_reports_seeded_values(file_engine):
    engine, db_path = file_engine
    with Session(engine) as session:
        _seed_avb_and_other(session)

    with Session(engine) as session:
        envelope = corr.capture_true_envelope(session, engine, db_path)

    assert envelope["daily_prices"]["row_count"] == 4
    assert envelope["avb_target_rows"]["2026-08-11"]["volume"] == 1549436.0
    assert envelope["avb_target_rows"]["2026-08-12"]["volume"] == 10350885.0
    assert envelope["avb_target_rows"]["2026-08-11"]["close"] == 181.76001476703186
    assert envelope["scanner_runs_total_count"] == 0
    assert envelope["all_11_incident_dates_zero_scanner_runs"] is True
    assert envelope["isolating_hashes"] is not None
    assert envelope["manifest_row_dump_fingerprint"]["row_count"] == 0


# --- Goal 1: coordinator-capture comparison -- exact mismatch reporting, never silently reconciled ----


_SMALL_COORDINATOR_CAPTURE = {
    "db_mtime": 123, "db_size_bytes": 456, "db_wal_size_bytes": 0,
    "daily_prices_row_count": 4, "scanner_runs_total_count": 0, "scanner_runs_stamped_6261ca17_count": 0,
    "forward_returns_total_count": 0, "forward_returns_measured_into_incident_total": 0,
    "data_provider_runs_count": 0, "manifest_row_count": 0,
    "manifest_ddl_sha256": "expected-ddl-hash",
    "manifest_row_dump_sha256_prefix": "ffffffff", "manifest_row_dump_sha256_suffix": "000000",
    "watchlist_count": 0, "all_11_incident_dates_zero_scanner_runs": True,
    "isolating_hashes": {"avb_ohlc_only": "a", "avb_other_dates_full_row": "b", "non_avb_full_row": "c"},
    "avb_target_rows": {
        "2026-08-11": {"open": 183.22001534990548, "high": 184.13001191846783, "low": 181.7100027790582, "close": 181.76001476703186, "volume": 1549436.0},
        "2026-08-12": {"open": 181.08999902870366, "high": 182.0900043902787, "low": 179.45999604273928, "close": 179.79000697488598, "volume": 10350885.0},
    },
}


def test_compare_true_envelope_reports_every_mismatch_explicitly(file_engine):
    engine, db_path = file_engine
    with Session(engine) as session:
        _seed_avb_and_other(session)
    with Session(engine) as session:
        envelope = corr.capture_true_envelope(session, engine, db_path)

    result = corr.compare_true_envelope_to_coordinator_capture(envelope, _SMALL_COORDINATOR_CAPTURE)
    assert result["any_mismatch"] is True
    # the AVB target rows and counts genuinely match this fixture's seed -- only the hash-shaped fields
    # (which this synthetic target deliberately does not reproduce) should mismatch.
    assert result["comparisons"]["daily_prices_row_count"]["matches"] is True
    assert result["comparisons"]["avb_target_row.2026-08-11"]["matches"] is True
    assert result["comparisons"]["manifest_ddl_sha256"]["matches"] is False
    assert result["comparisons"]["isolating_hash.non_avb_full_row"]["matches"] is False


def test_compare_true_envelope_all_match_when_expectations_equal_a_self_capture(file_engine):
    engine, db_path = file_engine
    with Session(engine) as session:
        _seed_avb_and_other(session)
    with Session(engine) as session:
        envelope = corr.capture_true_envelope(session, engine, db_path)

    self_capture = {
        "db_mtime": int(envelope["db_file"]["mtime"]), "db_size_bytes": envelope["db_file"]["size_bytes"],
        "db_wal_size_bytes": 0,
        "daily_prices_row_count": envelope["daily_prices"]["row_count"],
        "scanner_runs_total_count": envelope["scanner_runs_total_count"],
        "scanner_runs_stamped_6261ca17_count": envelope["scanner_runs_by_identity_group"]["legacy_6261ca17_count"],
        "forward_returns_total_count": envelope["forward_returns_total_count"],
        "forward_returns_measured_into_incident_total": envelope["forward_returns_measured_into_incident_total"],
        "data_provider_runs_count": envelope["data_provider_runs_count"],
        "manifest_row_count": envelope["manifest_row_count"],
        "manifest_ddl_sha256": envelope["manifest_ddl_sha256"],
        "manifest_row_dump_sha256_prefix": envelope["manifest_row_dump_fingerprint"]["sha256"][:8],
        "manifest_row_dump_sha256_suffix": envelope["manifest_row_dump_fingerprint"]["sha256"][-6:],
        "watchlist_count": envelope["watchlist_count"],
        "all_11_incident_dates_zero_scanner_runs": envelope["all_11_incident_dates_zero_scanner_runs"],
        "isolating_hashes": {k: v["sha256"] for k, v in envelope["isolating_hashes"].items()},
        "avb_target_rows": envelope["avb_target_rows"],
    }
    result = corr.compare_true_envelope_to_coordinator_capture(envelope, self_capture)
    assert result["any_mismatch"] is False
    assert all(c["matches"] for c in result["comparisons"].values())


# --- Goal 2: the derivation -- formula, rounding, cross-check, fail-closed paths ----------------------


_BRIDGE_FACTOR = 2.7930001225759193


def _synthetic_provider_evidence(sufficient=True, missing_close=False):
    per_date = {
        "2026-08-11": {"close": 65.07698059082031, "volume": 1549436.0},
        "2026-08-12": {"close": 64.37164306640625, "volume": 10350885.0},
    }
    if missing_close:
        per_date["2026-08-11"]["volume"] = None
    return {"per_date": per_date, "sufficient_evidence": sufficient}


def _synthetic_j10_row():
    return {"symbol": "AVB", "bridge_factor": _BRIDGE_FACTOR}


def _synthetic_stored():
    stored_volume_before = {"2026-08-11": 1549436.0, "2026-08-12": 10350885.0}
    stored_close = {"2026-08-11": 181.76001476703186, "2026-08-12": 179.79000697488598}
    return stored_volume_before, stored_close


def test_derive_avb_volume_correction_verifies_and_matches_expected_values():
    stored_volume_before, stored_close = _synthetic_stored()
    result = corr.derive_avb_volume_correction(
        _synthetic_provider_evidence(), _synthetic_j10_row(), stored_volume_before, stored_close
    )
    assert result["verified"] is True
    assert result["per_date"]["2026-08-11"]["corrected_volume"] == 554757.0
    assert result["per_date"]["2026-08-12"]["corrected_volume"] == 3706010.0
    for key in ("2026-08-11", "2026-08-12"):
        assert result["per_date"][key]["within_tolerance"] is True
        assert abs(result["per_date"][key]["dollar_volume_ratio_after"] - 1.0) < 0.01


def test_derive_avb_volume_correction_fails_closed_when_evidence_insufficient():
    stored_volume_before, stored_close = _synthetic_stored()
    result = corr.derive_avb_volume_correction(
        _synthetic_provider_evidence(sufficient=False), _synthetic_j10_row(), stored_volume_before, stored_close
    )
    assert result["verified"] is False
    assert result["per_date"]["2026-08-11"]["ok"] is False
    assert result["per_date"]["2026-08-12"]["ok"] is False


def test_derive_avb_volume_correction_fails_closed_on_missing_provider_volume():
    stored_volume_before, stored_close = _synthetic_stored()
    result = corr.derive_avb_volume_correction(
        _synthetic_provider_evidence(missing_close=True), _synthetic_j10_row(), stored_volume_before, stored_close
    )
    assert result["verified"] is False
    assert result["per_date"]["2026-08-11"]["ok"] is False
    assert "insufficient" in result["per_date"]["2026-08-11"]["reason"]


def test_derive_avb_volume_correction_fails_closed_when_bridge_factor_missing():
    stored_volume_before, stored_close = _synthetic_stored()
    result = corr.derive_avb_volume_correction(
        _synthetic_provider_evidence(), {"symbol": "AVB", "bridge_factor": None}, stored_volume_before, stored_close
    )
    assert result["verified"] is False


def test_derive_avb_volume_correction_fails_closed_when_cross_check_out_of_tolerance():
    """A stored_close value that does NOT match the bridge relationship at all -- the cross-check must
    reject it rather than proceed."""
    stored_volume_before, _ = _synthetic_stored()
    stored_close_wrong = {"2026-08-11": 1.0, "2026-08-12": 1.0}  # nowhere near provider_close*bridge_factor
    result = corr.derive_avb_volume_correction(
        _synthetic_provider_evidence(), _synthetic_j10_row(), stored_volume_before, stored_close_wrong
    )
    assert result["verified"] is False
    assert result["per_date"]["2026-08-11"]["within_tolerance"] is False


def test_derive_avb_volume_correction_reproduces_the_real_committed_iteration15_evidence():
    """Regression check against the ACTUAL committed iteration-15/iteration-9 evidence files (read-only,
    no DB access) -- confirms the real files remain loadable and reproduce the exact iteration-16
    corrected values this session independently re-derived."""
    provider_evidence = corr.load_provider_fetch_evidence()
    j10_row = diag.load_j10_avb_evidence()
    stored_volume_before = {"2026-08-11": 1549436.0, "2026-08-12": 10350885.0}
    stored_close = {"2026-08-11": 181.76001476703186, "2026-08-12": 179.79000697488598}
    result = corr.derive_avb_volume_correction(provider_evidence, j10_row, stored_volume_before, stored_close)
    assert result["verified"] is True
    assert result["per_date"]["2026-08-11"]["corrected_volume"] == 554757.0
    assert result["per_date"]["2026-08-12"]["corrected_volume"] == 3706010.0


# --- Goal 3: the ONE write, fixture-only -- exact scope proof ------------------------------------------


def test_checkpoint_wal_truncates_after_a_small_write(file_engine):
    """A write far too small to cross SQLite's default auto-checkpoint threshold on its own must still
    land durably in the MAIN db file, with the `-wal` sidecar back at 0 bytes, once `checkpoint_wal` is
    called -- this is the exact gap a live two-cell `daily_prices.volume` UPDATE hit."""
    engine, db_path = file_engine
    with Session(engine) as session:
        _seed_avb_and_other(session)
        session.commit()

    with Session(engine) as session:
        row = session.exec(
            select(DailyPrice).where(DailyPrice.symbol == "AVB").where(DailyPrice.date == date(2026, 8, 11))
        ).one()
        row.volume = 554757.0
        session.add(row)
        session.commit()

    result = corr.checkpoint_wal(engine)
    assert result["busy"] == 0  # single-writer fixture -- nothing should block a full checkpoint

    wal_path = db_path.parent / (db_path.name + "-wal")
    if wal_path.exists():
        assert wal_path.stat().st_size == 0


def test_apply_avb_volume_correction_touches_only_the_two_target_rows_and_only_volume(file_engine):
    engine, db_path = file_engine
    with Session(engine) as session:
        _seed_avb_and_other(session)

    with Session(engine) as session:
        before_rows = {
            (r.symbol, r.date.isoformat()): (r.open, r.high, r.low, r.close, r.volume)
            for r in session.exec(select(DailyPrice)).all()
        }

    with Session(engine) as session:
        written = corr.apply_avb_volume_correction(session, {"2026-08-11": 554757.0, "2026-08-12": 3706010.0})
    assert written == {"2026-08-11": 554757.0, "2026-08-12": 3706010.0}

    with Session(engine) as session:
        after_rows = {
            (r.symbol, r.date.isoformat()): (r.open, r.high, r.low, r.close, r.volume)
            for r in session.exec(select(DailyPrice)).all()
        }

    for key, before in before_rows.items():
        symbol, iso_date = key
        after = after_rows[key]
        if symbol == "AVB" and iso_date in ("2026-08-11", "2026-08-12"):
            assert after[:4] == before[:4]  # OHLC byte-identical
            expected_volume = 554757.0 if iso_date == "2026-08-11" else 3706010.0
            assert after[4] == expected_volume
        else:
            assert after == before  # every other row (OHLCV, all columns) byte-identical


def test_apply_avb_volume_correction_raises_and_writes_nothing_if_target_row_count_wrong(file_engine):
    engine, db_path = file_engine
    with Session(engine) as session:
        _mk_price(session, "AVB", date(2026, 8, 11), 1, 2, 3, 4, 5)  # only ONE of the two target dates
        session.commit()

    with Session(engine) as session:
        with pytest.raises(RuntimeError):
            corr.apply_avb_volume_correction(session, {"2026-08-11": 1.0, "2026-08-12": 2.0})

    with Session(engine) as session:
        rows = session.exec(select(DailyPrice)).all()
    assert len(rows) == 1
    assert rows[0].volume == 5  # untouched


# --- Goal 4: the mutation-evidence comparison builder -- pure, synthetic envelopes ---------------------


def _make_envelope(avb_rows, ohlcv_sum, **overrides):
    base = {
        "avb_target_rows": avb_rows,
        "daily_prices": {
            "row_count": 10, "min_date": "1996-01-02", "max_date": "2026-08-12", "id_sum": 100,
            "ohlcv_sum": ohlcv_sum, "fingerprint": "f",
        },
        "isolating_hashes": {
            "avb_ohlc_only": {"sha256": "h1"}, "avb_other_dates_full_row": {"sha256": "h2"},
            "non_avb_full_row": {"sha256": "h3"},
        },
        "scanner_runs_by_identity_group": {"null_count": 1, "legacy_6261ca17_count": 2, "other_count": 0},
        "forward_returns_total_count": 5,
        "forward_returns_measured_into_incident_total": 3,
        "data_provider_runs_count": 7,
        "manifest_row_count": 24,
        "manifest_ddl_sha256": "ddl",
        "manifest_row_dump_fingerprint": {"sha256": "dump"},
        "watchlist_count": 6,
        "all_11_incident_dates_zero_scanner_runs": True,
        "db_file": {"mtime": 100.0, "size_bytes": 1000, "wal": {"exists": True, "size_bytes": 0}},
    }
    base.update(overrides)
    return base


_DERIVATION = {"per_date": {"2026-08-11": {"corrected_volume": 554757.0}, "2026-08-12": {"corrected_volume": 3706010.0}}}


def _clean_true_start():
    return _make_envelope(
        {
            "2026-08-11": {"open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 1549436.0},
            "2026-08-12": {"open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 10350885.0},
        },
        ohlcv_sum=100000.0,
    )


def _clean_true_end():
    delta = (1549436.0 - 554757.0) + (10350885.0 - 3706010.0)
    return _make_envelope(
        {
            "2026-08-11": {"open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 554757.0},
            "2026-08-12": {"open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 3706010.0},
        },
        ohlcv_sum=100000.0 - delta,
        db_file={"mtime": 200.0, "size_bytes": 1100, "wal": {"exists": True, "size_bytes": 0}},
    )


def test_build_mutation_evidence_all_checks_pass_on_a_clean_correction():
    result = corr.build_mutation_evidence(true_start=_clean_true_start(), true_end=_clean_true_end(), derivation=_DERIVATION)
    assert result["all_checks_pass"] is True
    for name, ok in result["checks"].items():
        assert ok is True, f"{name} unexpectedly False"


def test_build_mutation_evidence_fails_when_ohlc_moved():
    true_end = _clean_true_end()
    true_end["avb_target_rows"]["2026-08-11"]["close"] = 999.0  # OHLC must NEVER move
    result = corr.build_mutation_evidence(true_start=_clean_true_start(), true_end=true_end, derivation=_DERIVATION)
    assert result["checks"]["ohlc_byte_identical_both_dates"] is False
    assert result["all_checks_pass"] is False


def test_build_mutation_evidence_fails_when_a_non_avb_isolating_hash_moved():
    true_end = _clean_true_end()
    true_end["isolating_hashes"]["non_avb_full_row"]["sha256"] = "DIFFERENT"
    result = corr.build_mutation_evidence(true_start=_clean_true_start(), true_end=true_end, derivation=_DERIVATION)
    assert result["checks"]["isolating_hash_unchanged.non_avb_full_row"] is False
    assert result["all_checks_pass"] is False


def test_build_mutation_evidence_fails_when_row_count_changed():
    true_end = _clean_true_end()
    true_end["daily_prices"]["row_count"] = 11
    result = corr.build_mutation_evidence(true_start=_clean_true_start(), true_end=true_end, derivation=_DERIVATION)
    assert result["checks"]["row_count_unchanged"] is False
    assert result["all_checks_pass"] is False


def test_build_mutation_evidence_fails_when_ohlcv_sum_delta_is_wrong():
    true_end = _clean_true_end()
    true_end["daily_prices"]["ohlcv_sum"] = 100000.0  # unchanged -- but volume moved, so this is WRONG
    result = corr.build_mutation_evidence(true_start=_clean_true_start(), true_end=true_end, derivation=_DERIVATION)
    assert result["checks"]["ohlcv_sum_shifted_by_exact_delta"] is False
    assert result["all_checks_pass"] is False


def test_build_mutation_evidence_fails_when_db_file_did_not_move():
    true_end = _clean_true_end()
    true_end["db_file"] = {"mtime": 100.0, "size_bytes": 1000, "wal": {"exists": True, "size_bytes": 0}}
    result = corr.build_mutation_evidence(true_start=_clean_true_start(), true_end=true_end, derivation=_DERIVATION)
    assert result["checks"]["db_file_moved"] is False
    assert result["all_checks_pass"] is False


def test_build_mutation_evidence_fails_when_wal_not_checkpointed():
    true_end = _clean_true_end()
    true_end["db_file"]["wal"] = {"exists": True, "size_bytes": 4096}
    result = corr.build_mutation_evidence(true_start=_clean_true_start(), true_end=true_end, derivation=_DERIVATION)
    assert result["checks"]["wal_checkpointed_to_zero"] is False
    assert result["all_checks_pass"] is False
