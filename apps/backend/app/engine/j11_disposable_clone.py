"""app.engine.j11_disposable_clone -- goal-market-compass iter-23: tooling for the ONE remaining J-11
acceptance objective (docs/goal.md "OWNER RULING -- J-11 database recovery accepted; one final serving
verification remains", owner 2026-08-27, items 3-5). Stages D-G already repaired the CANONICAL database
and are accepted `J-11 DATA RECOVERY: COMPLETE` / `J-11 DATABASE ACCEPTANCE: COMPLETE` -- this module does
NOT touch that recovery. It builds the tooling for the one task the ruling leaves open: prove the
repaired state SERVES correctly through a real backend/frontend boot, run ONLY against a disposable,
byte-faithful clone. The canonical `apps/backend/data/trendora.db` stays OFF and unmutated throughout --
every function here either opens it `mode=ro` (structurally read-only, not just by convention) or never
touches it at all.

Three primitives:
  - `capture_db_provenance(db_path)` -- read-only row-count/max-id/whole-file-sha256 provenance a caller
    compares before/after a clone, and before/after the whole verification window on the canonical file
    itself (ruling item 3: "record enough evidence to prove the verification DB began from the repaired
    canonical state"; DoD: "the canonical trendora.db is proven byte-unchanged").
  - `create_disposable_clone(source_path, dest_path)` -- the SQLite online backup API
    (`sqlite3.Connection.backup`), source opened `mode=ro`. A consistent backup mechanism per the IN SCOPE
    bullet ("not a raw file copy while the DB might be open") -- the backup API produces a transactionally
    consistent snapshot even against a live WAL-mode writer, and here the source is never opened for write
    at all.
  - `build_verification_config_text` / `assert_launch_targets_clone` -- the verification-only config
    (whose ONLY difference from the committed `config.yaml` is `database.url`, per ruling item 3) and the
    fail-closed launch guard the Testing Requirements' "Error cases" paragraph names: "a launch attempt
    that omits the TRENDORA_CONFIG override ... must be refused before any browser/replay execution
    proceeds."

Nothing here creates, deletes, or mutates a row in ANY table -- it only reads the canonical file (via a
read-only URI) and writes NEW files elsewhere (the clone database, the verification config).
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path
from typing import Optional

import yaml


class ClonePreconditionError(RuntimeError):
    """Raised when a disposable-clone precondition is not met. Every function in this module fails
    closed -- it never silently proceeds past a missing file, an already-existing destination, or a
    config that still points at the canonical database."""


def sha256_file(path: Path, *, chunk_size: int = 8 * 1024 * 1024) -> str:
    """Streaming sha256 of a file's bytes -- never loads the whole (potentially multi-GB) file into
    memory at once (AG-8)."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def capture_db_provenance(db_path: Path, *, include_sha256: bool = True) -> dict:
    """Read-only provenance of a SQLite database file: `daily_prices` row count, `next_session_manifests`
    row count, `data_provider_runs` max id, file size/mtime, and (optionally -- an expensive multi-GB
    streaming read) a whole-file sha256. Opens the file with `mode=ro` in the connection URI, SQLite's own
    documented read-only open mode, so this function structurally cannot write to `db_path`."""
    db_path = Path(db_path)
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        daily_prices = conn.execute("SELECT COUNT(*) FROM daily_prices").fetchone()[0]
        manifests = conn.execute("SELECT COUNT(*) FROM next_session_manifests").fetchone()[0]
        max_provider_run_id = conn.execute("SELECT MAX(id) FROM data_provider_runs").fetchone()[0]
    finally:
        conn.close()
    stat = db_path.stat()
    return {
        "path": str(db_path),
        "daily_prices_count": int(daily_prices),
        "next_session_manifests_count": int(manifests),
        "data_provider_runs_max_id": int(max_provider_run_id) if max_provider_run_id is not None else None,
        "size_bytes": stat.st_size,
        "mtime": stat.st_mtime,
        "sha256": sha256_file(db_path) if include_sha256 else None,
    }


def create_disposable_clone(source_path: Path, dest_path: Path) -> dict:
    """Byte-faithful SQLite clone via the online backup API (`sqlite3.Connection.backup`) -- a
    transactionally consistent snapshot, never a raw file copy. `source_path` is opened `mode=ro`, so this
    function can never write to the canonical file. Refuses if `dest_path` already exists (never silently
    clobbers a prior clone) or if its parent directory is missing (never creates directories itself --
    the caller decides where the disposable clone lives)."""
    source_path = Path(source_path)
    dest_path = Path(dest_path)
    if not source_path.exists():
        raise ClonePreconditionError(f"source database does not exist: {source_path}")
    if dest_path.exists():
        raise ClonePreconditionError(f"refusing to overwrite an existing clone at {dest_path}")
    if not dest_path.parent.exists():
        raise ClonePreconditionError(f"destination directory does not exist: {dest_path.parent}")
    source_conn = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
    dest_conn = sqlite3.connect(str(dest_path))
    try:
        source_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        source_conn.close()
    return {
        "source": str(source_path),
        "dest": str(dest_path),
        "dest_size_bytes": dest_path.stat().st_size,
    }


def build_verification_config_text(config_text: str, canonical_url: str, clone_url: str) -> str:
    """Returns `config_text` with the EXACT `url: "<canonical_url>"` line replaced by
    `url: "<clone_url>"` -- every other byte unchanged (ruling item 3: "whose only difference from it is
    `database.url`"). Fails closed if that exact line does not appear exactly once, rather than risk
    editing the wrong line or a comment that happens to mention a URL."""
    target_line_pattern = re.compile(
        r'(?m)^([ \t]*url:[ \t]*)"' + re.escape(canonical_url) + r'"([ \t]*)$'
    )
    matches = list(target_line_pattern.finditer(config_text))
    if len(matches) != 1:
        raise ClonePreconditionError(
            f'expected exactly one \'url: "{canonical_url}"\' line in the config text, found {len(matches)}'
        )
    match = matches[0]
    replacement = f'{match.group(1)}"{clone_url}"{match.group(2)}'
    return config_text[: match.start()] + replacement + config_text[match.end():]


def clone_sqlite_url(clone_db_path: Path) -> str:
    """The absolute-path `sqlite:////...` URL form for `clone_db_path` -- FOUR slashes (the standard
    SQLAlchemy/sqlite absolute-path form: the 3-slash `sqlite:///` scheme prefix plus the path's own
    leading `/`). `app.db.resolve_database_url` passes an absolute path straight through unresolved, so
    this never gets silently rebased onto the repo root the way a relative path would."""
    resolved = Path(clone_db_path).resolve()
    return f"sqlite:///{resolved}"


def assert_launch_targets_clone(trendora_config_path: Optional[str], canonical_url: str) -> dict:
    """Testing Requirements 'Error cases': "a launch attempt that omits the TRENDORA_CONFIG override (i.e.
    would default to the canonical DB) must be refused before any browser/replay execution proceeds."
    Raises `ClonePreconditionError` (never returns) unless: the env var is set and non-empty, the file it
    names exists, that file parses as YAML with a `database.url`, and that url is NOT the canonical url.
    Returns `{"config_path", "database_url"}` on success -- proof the caller can log."""
    if not trendora_config_path:
        raise ClonePreconditionError(
            "TRENDORA_CONFIG is not set -- a launch without it targets the CANONICAL database "
            "(app.config.load_config's own default-path fallback); refusing to boot"
        )
    config_path = Path(trendora_config_path)
    if not config_path.exists():
        raise ClonePreconditionError(f"TRENDORA_CONFIG points at a file that does not exist: {config_path}")
    data = yaml.safe_load(config_path.read_text())
    url = ((data or {}).get("database") or {}).get("url")
    if not url:
        raise ClonePreconditionError(f"{config_path} has no database.url -- refusing to boot")
    if url == canonical_url:
        raise ClonePreconditionError(
            f"{config_path}'s database.url still equals the CANONICAL url ({canonical_url!r}) -- "
            "refusing to boot against the canonical database"
        )
    return {"config_path": str(config_path), "database_url": url}


def compare_provenance(before: dict, after: dict) -> dict:
    """Field-by-field comparison of two `capture_db_provenance(...)` results (the row-count/max-id/sha256
    fields only -- `mtime` is deliberately excluded: a read-only open can legitimately touch atime/mtime
    metadata on some filesystems without writing a single content byte, so mtime is corroborating evidence
    elsewhere, never the pass/fail gate here). `equal` is True iff every compared field matches."""
    fields = (
        "daily_prices_count",
        "next_session_manifests_count",
        "data_provider_runs_max_id",
        "size_bytes",
        "sha256",
    )
    mismatches = [f for f in fields if before.get(f) != after.get(f)]
    return {"equal": not mismatches, "mismatched_fields": mismatches}
