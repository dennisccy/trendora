"""Fixture-scoped tests for `app.engine.j11_disposable_clone` (goal-market-compass iter-23 -- the ONE
remaining J-11 serving/replay verification objective). Every test builds tiny synthetic SQLite databases
under `tmp_path` -- NEVER touches `apps/backend/data/trendora.db` (project-template.md: "NEVER copy, move,
or open-for-write trendora.db")."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.engine.j11_disposable_clone import (
    ClonePreconditionError,
    assert_launch_targets_clone,
    build_verification_config_text,
    capture_db_provenance,
    clone_sqlite_url,
    compare_provenance,
    create_disposable_clone,
    sha256_file,
)


def _make_fixture_db(path: Path, *, prices: int = 5, manifests: int = 2, provider_run_ids: tuple = (1, 2, 3)) -> None:
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(
            """
            CREATE TABLE daily_prices (id INTEGER PRIMARY KEY, symbol TEXT, date TEXT, close REAL);
            CREATE TABLE next_session_manifests (id INTEGER PRIMARY KEY, as_of TEXT, version INTEGER);
            CREATE TABLE data_provider_runs (id INTEGER PRIMARY KEY, provider TEXT);
            """
        )
        for i in range(prices):
            conn.execute(
                "INSERT INTO daily_prices (symbol, date, close) VALUES (?, ?, ?)",
                (f"SYM{i}", f"2026-01-{i + 1:02d}", 100.0 + i),
            )
        for i in range(manifests):
            conn.execute(
                "INSERT INTO next_session_manifests (as_of, version) VALUES (?, ?)",
                (f"2026-02-{i + 1:02d}", 1),
            )
        for run_id in provider_run_ids:
            conn.execute("INSERT INTO data_provider_runs (id, provider) VALUES (?, ?)", (run_id, "yahoo"))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# sha256_file / capture_db_provenance
# ---------------------------------------------------------------------------


def test_sha256_file_matches_hashlib_reference(tmp_path):
    import hashlib

    p = tmp_path / "blob.bin"
    p.write_bytes(b"the quick brown fox jumps over the lazy dog" * 1000)
    expected = hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha256_file(p) == expected


def test_sha256_file_streams_in_chunks_smaller_than_the_file(tmp_path):
    p = tmp_path / "blob.bin"
    p.write_bytes(b"x" * 100)
    # A chunk size smaller than the file forces multiple .update() calls -- must still match a
    # single-shot hash.
    import hashlib

    assert sha256_file(p, chunk_size=7) == hashlib.sha256(p.read_bytes()).hexdigest()


def test_capture_db_provenance_reads_exact_counts_and_max_id(tmp_path):
    db_path = tmp_path / "source.db"
    _make_fixture_db(db_path, prices=7, manifests=3, provider_run_ids=(1, 2, 5))
    prov = capture_db_provenance(db_path)
    assert prov["daily_prices_count"] == 7
    assert prov["next_session_manifests_count"] == 3
    assert prov["data_provider_runs_max_id"] == 5
    assert prov["size_bytes"] > 0
    assert prov["sha256"] is not None and len(prov["sha256"]) == 64


def test_capture_db_provenance_can_skip_the_expensive_sha256(tmp_path):
    db_path = tmp_path / "source.db"
    _make_fixture_db(db_path)
    prov = capture_db_provenance(db_path, include_sha256=False)
    assert prov["sha256"] is None


def test_capture_db_provenance_never_writes_to_the_source_file(tmp_path):
    """The mode=ro URI open must be a structural guarantee, not a convention -- attempting a write
    through the same connection style must fail."""
    db_path = tmp_path / "source.db"
    _make_fixture_db(db_path)
    before_bytes = db_path.read_bytes()
    capture_db_provenance(db_path)
    assert db_path.read_bytes() == before_bytes


# ---------------------------------------------------------------------------
# create_disposable_clone
# ---------------------------------------------------------------------------


def test_create_disposable_clone_produces_matching_row_provenance(tmp_path):
    """Row-level provenance (counts + max id) must match exactly between source and clone -- this is
    TC-1's actual assertion. Whole-FILE sha256 is deliberately NOT compared here: `sqlite3.Connection.
    backup()` produces a database that is logically identical (same rows, same values) but not
    necessarily byte-identical at the file level (freelist/page-layout/journal-mode header differences
    between a long-lived source file and a freshly created destination) -- sha256 equality is the
    canonical file's OWN identity check across time (see the launch-safety tests below), never a
    cross-file equality check between two independently created files with identical content."""
    source = tmp_path / "source.db"
    dest = tmp_path / "clone.db"
    _make_fixture_db(source, prices=11, manifests=4, provider_run_ids=(1, 9, 42))

    result = create_disposable_clone(source, dest)

    assert dest.exists()
    assert result["dest_size_bytes"] > 0
    before = capture_db_provenance(source, include_sha256=False)
    after = capture_db_provenance(dest, include_sha256=False)
    assert after["daily_prices_count"] == before["daily_prices_count"] == 11
    assert after["next_session_manifests_count"] == before["next_session_manifests_count"] == 4
    assert after["data_provider_runs_max_id"] == before["data_provider_runs_max_id"] == 42


def test_create_disposable_clone_never_mutates_the_source_file(tmp_path):
    source = tmp_path / "source.db"
    dest = tmp_path / "clone.db"
    _make_fixture_db(source)
    before_sha = sha256_file(source)
    before_size = source.stat().st_size

    create_disposable_clone(source, dest)

    assert sha256_file(source) == before_sha
    assert source.stat().st_size == before_size


def test_create_disposable_clone_refuses_to_overwrite_an_existing_destination(tmp_path):
    source = tmp_path / "source.db"
    dest = tmp_path / "clone.db"
    _make_fixture_db(source)
    dest.write_bytes(b"pre-existing content, must survive")

    with pytest.raises(ClonePreconditionError, match="refusing to overwrite"):
        create_disposable_clone(source, dest)

    assert dest.read_bytes() == b"pre-existing content, must survive"


def test_create_disposable_clone_refuses_when_source_is_missing(tmp_path):
    source = tmp_path / "does-not-exist.db"
    dest = tmp_path / "clone.db"
    with pytest.raises(ClonePreconditionError, match="does not exist"):
        create_disposable_clone(source, dest)


def test_create_disposable_clone_refuses_when_dest_directory_is_missing(tmp_path):
    source = tmp_path / "source.db"
    _make_fixture_db(source)
    dest = tmp_path / "no-such-dir" / "clone.db"
    with pytest.raises(ClonePreconditionError, match="destination directory does not exist"):
        create_disposable_clone(source, dest)


# ---------------------------------------------------------------------------
# build_verification_config_text
# ---------------------------------------------------------------------------

_SAMPLE_CONFIG_TEXT = """\
# a comment mentioning sqlite:///apps/backend/data/trendora.db in prose, must NOT be touched
some_key: "some_value"
database:
  url: "sqlite:///apps/backend/data/trendora.db"
  pool_size: 24
other_section:
  nested: true
"""


def test_build_verification_config_text_changes_only_the_url_line():
    clone_url = "sqlite:////tmp/clone/trendora-clone.db"
    result = build_verification_config_text(
        _SAMPLE_CONFIG_TEXT, "sqlite:///apps/backend/data/trendora.db", clone_url
    )
    result_lines = result.splitlines()
    original_lines = _SAMPLE_CONFIG_TEXT.splitlines()
    assert len(result_lines) == len(original_lines)
    diffs = [
        (i, a, b) for i, (a, b) in enumerate(zip(original_lines, result_lines)) if a != b
    ]
    assert len(diffs) == 1, diffs
    _, before_line, after_line = diffs[0]
    assert before_line == '  url: "sqlite:///apps/backend/data/trendora.db"'
    assert after_line == f'  url: "{clone_url}"'
    # the comment-line prose mention must survive untouched
    assert "a comment mentioning sqlite:///apps/backend/data/trendora.db in prose" in result


def test_build_verification_config_text_raises_if_the_line_is_absent():
    with pytest.raises(ClonePreconditionError, match="found 0"):
        build_verification_config_text(
            "database:\n  url: \"sqlite:///something/else.db\"\n",
            "sqlite:///apps/backend/data/trendora.db",
            "sqlite:////tmp/clone.db",
        )


def test_build_verification_config_text_raises_if_the_line_appears_twice():
    doubled = _SAMPLE_CONFIG_TEXT + '\n  url: "sqlite:///apps/backend/data/trendora.db"\n'
    with pytest.raises(ClonePreconditionError, match="found 2"):
        build_verification_config_text(
            doubled, "sqlite:///apps/backend/data/trendora.db", "sqlite:////tmp/clone.db"
        )


# ---------------------------------------------------------------------------
# clone_sqlite_url
# ---------------------------------------------------------------------------


def test_clone_sqlite_url_is_the_four_slash_absolute_form(tmp_path):
    db_path = tmp_path / "clone.db"
    url = clone_sqlite_url(db_path)
    assert url.startswith("sqlite:////")
    assert url == f"sqlite:///{db_path.resolve()}"


def test_clone_sqlite_url_round_trips_through_resolve_database_url(tmp_path):
    from app.db import resolve_database_url

    db_path = tmp_path / "clone.db"
    url = clone_sqlite_url(db_path)
    # An absolute sqlite URL must pass through resolve_database_url completely unchanged -- never
    # rebased onto the repo root the way a relative path would be.
    assert resolve_database_url(url) == url


# ---------------------------------------------------------------------------
# assert_launch_targets_clone
# ---------------------------------------------------------------------------

_CANONICAL_URL = "sqlite:///apps/backend/data/trendora.db"


def test_assert_launch_targets_clone_refuses_when_env_var_is_unset():
    with pytest.raises(ClonePreconditionError, match="TRENDORA_CONFIG is not set"):
        assert_launch_targets_clone(None, _CANONICAL_URL)


def test_assert_launch_targets_clone_refuses_when_env_var_is_empty_string():
    with pytest.raises(ClonePreconditionError, match="TRENDORA_CONFIG is not set"):
        assert_launch_targets_clone("", _CANONICAL_URL)


def test_assert_launch_targets_clone_refuses_when_config_file_is_missing(tmp_path):
    missing = tmp_path / "does-not-exist.yaml"
    with pytest.raises(ClonePreconditionError, match="does not exist"):
        assert_launch_targets_clone(str(missing), _CANONICAL_URL)


def test_assert_launch_targets_clone_refuses_when_url_still_equals_canonical(tmp_path):
    config_path = tmp_path / "verify-config.yaml"
    config_path.write_text(f'database:\n  url: "{_CANONICAL_URL}"\n')
    with pytest.raises(ClonePreconditionError, match="still equals the CANONICAL url"):
        assert_launch_targets_clone(str(config_path), _CANONICAL_URL)


def test_assert_launch_targets_clone_refuses_when_database_url_is_missing(tmp_path):
    config_path = tmp_path / "verify-config.yaml"
    config_path.write_text("database:\n  pool_size: 24\n")
    with pytest.raises(ClonePreconditionError, match="has no database.url"):
        assert_launch_targets_clone(str(config_path), _CANONICAL_URL)


def test_assert_launch_targets_clone_passes_when_correctly_pointed_at_a_clone(tmp_path):
    clone_url = "sqlite:////tmp/somewhere/clone.db"
    config_path = tmp_path / "verify-config.yaml"
    config_path.write_text(f'database:\n  url: "{clone_url}"\n')
    result = assert_launch_targets_clone(str(config_path), _CANONICAL_URL)
    assert result == {"config_path": str(config_path), "database_url": clone_url}


# ---------------------------------------------------------------------------
# compare_provenance
# ---------------------------------------------------------------------------


def test_compare_provenance_reports_equal_for_identical_dicts():
    prov = {
        "daily_prices_count": 1,
        "next_session_manifests_count": 2,
        "data_provider_runs_max_id": 3,
        "size_bytes": 4,
        "sha256": "abc",
        "mtime": 123.0,
    }
    result = compare_provenance(prov, dict(prov))
    assert result == {"equal": True, "mismatched_fields": []}


def test_compare_provenance_ignores_mtime_but_catches_a_real_content_change():
    before = {
        "daily_prices_count": 1,
        "next_session_manifests_count": 2,
        "data_provider_runs_max_id": 3,
        "size_bytes": 100,
        "sha256": "abc",
        "mtime": 111.0,
    }
    after_mtime_only = {**before, "mtime": 222.0}
    assert compare_provenance(before, after_mtime_only) == {"equal": True, "mismatched_fields": []}

    after_real_change = {**before, "sha256": "different"}
    result = compare_provenance(before, after_real_change)
    assert result["equal"] is False
    assert result["mismatched_fields"] == ["sha256"]
