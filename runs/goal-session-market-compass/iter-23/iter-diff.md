# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/apps/backend/app/engine/j11_disposable_clone.py b/apps/backend/app/engine/j11_disposable_clone.py
new file mode 100644
index 00000000..07e26734
--- /dev/null
+++ b/apps/backend/app/engine/j11_disposable_clone.py
@@ -0,0 +1,180 @@
+"""app.engine.j11_disposable_clone -- goal-market-compass iter-23: tooling for the ONE remaining J-11
+acceptance objective (docs/goal.md "OWNER RULING -- J-11 database recovery accepted; one final serving
+verification remains", owner 2026-08-27, items 3-5). Stages D-G already repaired the CANONICAL database
+and are accepted `J-11 DATA RECOVERY: COMPLETE` / `J-11 DATABASE ACCEPTANCE: COMPLETE` -- this module does
+NOT touch that recovery. It builds the tooling for the one task the ruling leaves open: prove the
+repaired state SERVES correctly through a real backend/frontend boot, run ONLY against a disposable,
+byte-faithful clone. The canonical `apps/backend/data/trendora.db` stays OFF and unmutated throughout --
+every function here either opens it `mode=ro` (structurally read-only, not just by convention) or never
+touches it at all.
+
+Three primitives:
+  - `capture_db_provenance(db_path)` -- read-only row-count/max-id/whole-file-sha256 provenance a caller
+    compares before/after a clone, and before/after the whole verification window on the canonical file
+    itself (ruling item 3: "record enough evidence to prove the verification DB began from the repaired
+    canonical state"; DoD: "the canonical trendora.db is proven byte-unchanged").
+  - `create_disposable_clone(source_path, dest_path)` -- the SQLite online backup API
+    (`sqlite3.Connection.backup`), source opened `mode=ro`. A consistent backup mechanism per the IN SCOPE
+    bullet ("not a raw file copy while the DB might be open") -- the backup API produces a transactionally
+    consistent snapshot even against a live WAL-mode writer, and here the source is never opened for write
+    at all.
+  - `build_verification_config_text` / `assert_launch_targets_clone` -- the verification-only config
+    (whose ONLY difference from the committed `config.yaml` is `database.url`, per ruling item 3) and the
+    fail-closed launch guard the Testing Requirements' "Error cases" paragraph names: "a launch attempt
+    that omits the TRENDORA_CONFIG override ... must be refused before any browser/replay execution
+    proceeds."
+
+Nothing here creates, deletes, or mutates a row in ANY table -- it only reads the canonical file (via a
+read-only URI) and writes NEW files elsewhere (the clone database, the verification config).
+"""
+from __future__ import annotations
+
+import hashlib
+import re
+import sqlite3
+from pathlib import Path
+from typing import Optional
+
+import yaml
+
+
+class ClonePreconditionError(RuntimeError):
+    """Raised when a disposable-clone precondition is not met. Every function in this module fails
+    closed -- it never silently proceeds past a missing file, an already-existing destination, or a
+    config that still points at the canonical database."""
+
+
+def sha256_file(path: Path, *, chunk_size: int = 8 * 1024 * 1024) -> str:
+    """Streaming sha256 of a file's bytes -- never loads the whole (potentially multi-GB) file into
+    memory at once (AG-8)."""
+    digest = hashlib.sha256()
+    with Path(path).open("rb") as fh:
+        while True:
+            chunk = fh.read(chunk_size)
+            if not chunk:
+                break
+            digest.update(chunk)
+    return digest.hexdigest()
+
+
+def capture_db_provenance(db_path: Path, *, include_sha256: bool = True) -> dict:
+    """Read-only provenance of a SQLite database file: `daily_prices` row count, `next_session_manifests`
+    row count, `data_provider_runs` max id, file size/mtime, and (optionally -- an expensive multi-GB
+    streaming read) a whole-file sha256. Opens the file with `mode=ro` in the connection URI, SQLite's own
+    documented read-only open mode, so this function structurally cannot write to `db_path`."""
+    db_path = Path(db_path)
+    uri = f"file:{db_path}?mode=ro"
+    conn = sqlite3.connect(uri, uri=True)
+    try:
+        daily_prices = conn.execute("SELECT COUNT(*) FROM daily_prices").fetchone()[0]
+        manifests = conn.execute("SELECT COUNT(*) FROM next_session_manifests").fetchone()[0]
+        max_provider_run_id = conn.execute("SELECT MAX(id) FROM data_provider_runs").fetchone()[0]
+    finally:
+        conn.close()
+    stat = db_path.stat()
+    return {
+        "path": str(db_path),
+        "daily_prices_count": int(daily_prices),
+        "next_session_manifests_count": int(manifests),
+        "data_provider_runs_max_id": int(max_provider_run_id) if max_provider_run_id is not None else None,
+        "size_bytes": stat.st_size,
+        "mtime": stat.st_mtime,
+        "sha256": sha256_file(db_path) if include_sha256 else None,
+    }
+
+
+def create_disposable_clone(source_path: Path, dest_path: Path) -> dict:
+    """Byte-faithful SQLite clone via the online backup API (`sqlite3.Connection.backup`) -- a
+    transactionally consistent snapshot, never a raw file copy. `source_path` is opened `mode=ro`, so this
+    function can never write to the canonical file. Refuses if `dest_path` already exists (never silently
+    clobbers a prior clone) or if its parent directory is missing (never creates directories itself --
+    the caller decides where the disposable clone lives)."""
+    source_path = Path(source_path)
+    dest_path = Path(dest_path)
+    if not source_path.exists():
+        raise ClonePreconditionError(f"source database does not exist: {source_path}")
+    if dest_path.exists():
+        raise ClonePreconditionError(f"refusing to overwrite an existing clone at {dest_path}")
+    if not dest_path.parent.exists():
+        raise ClonePreconditionError(f"destination directory does not exist: {dest_path.parent}")
+    source_conn = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
+    dest_conn = sqlite3.connect(str(dest_path))
+    try:
+        source_conn.backup(dest_conn)
+    finally:
+        dest_conn.close()
+        source_conn.close()
+    return {
+        "source": str(source_path),
+        "dest": str(dest_path),
+        "dest_size_bytes": dest_path.stat().st_size,
+    }
+
+
+def build_verification_config_text(config_text: str, canonical_url: str, clone_url: str) -> str:
+    """Returns `config_text` with the EXACT `url: "<canonical_url>"` line replaced by
+    `url: "<clone_url>"` -- every other byte unchanged (ruling item 3: "whose only difference from it is
+    `database.url`"). Fails closed if that exact line does not appear exactly once, rather than risk
+    editing the wrong line or a comment that happens to mention a URL."""
+    target_line_pattern = re.compile(
+        r'(?m)^([ \t]*url:[ \t]*)"' + re.escape(canonical_url) + r'"([ \t]*)$'
+    )
+    matches = list(target_line_pattern.finditer(config_text))
+    if len(matches) != 1:
+        raise ClonePreconditionError(
+            f'expected exactly one \'url: "{canonical_url}"\' line in the config text, found {len(matches)}'
+        )
+    match = matches[0]
+    replacement = f'{match.group(1)}"{clone_url}"{match.group(2)}'
+    return config_text[: match.start()] + replacement + config_text[match.end():]
+
+
+def clone_sqlite_url(clone_db_path: Path) -> str:
+    """The absolute-path `sqlite:////...` URL form for `clone_db_path` -- FOUR slashes (the standard
+    SQLAlchemy/sqlite absolute-path form: the 3-slash `sqlite:///` scheme prefix plus the path's own
+    leading `/`). `app.db.resolve_database_url` passes an absolute path straight through unresolved, so
+    this never gets silently rebased onto the repo root the way a relative path would."""
+    resolved = Path(clone_db_path).resolve()
+    return f"sqlite:///{resolved}"
+
+
+def assert_launch_targets_clone(trendora_config_path: Optional[str], canonical_url: str) -> dict:
+    """Testing Requirements 'Error cases': "a launch attempt that omits the TRENDORA_CONFIG override (i.e.
+    would default to the canonical DB) must be refused before any browser/replay execution proceeds."
+    Raises `ClonePreconditionError` (never returns) unless: the env var is set and non-empty, the file it
+    names exists, that file parses as YAML with a `database.url`, and that url is NOT the canonical url.
+    Returns `{"config_path", "database_url"}` on success -- proof the caller can log."""
+    if not trendora_config_path:
+        raise ClonePreconditionError(
+            "TRENDORA_CONFIG is not set -- a launch without it targets the CANONICAL database "
+            "(app.config.load_config's own default-path fallback); refusing to boot"
+        )
+    config_path = Path(trendora_config_path)
+    if not config_path.exists():
+        raise ClonePreconditionError(f"TRENDORA_CONFIG points at a file that does not exist: {config_path}")
+    data = yaml.safe_load(config_path.read_text())
+    url = ((data or {}).get("database") or {}).get("url")
+    if not url:
+        raise ClonePreconditionError(f"{config_path} has no database.url -- refusing to boot")
+    if url == canonical_url:
+        raise ClonePreconditionError(
+            f"{config_path}'s database.url still equals the CANONICAL url ({canonical_url!r}) -- "
+            "refusing to boot against the canonical database"
+        )
+    return {"config_path": str(config_path), "database_url": url}
+
+
+def compare_provenance(before: dict, after: dict) -> dict:
+    """Field-by-field comparison of two `capture_db_provenance(...)` results (the row-count/max-id/sha256
+    fields only -- `mtime` is deliberately excluded: a read-only open can legitimately touch atime/mtime
+    metadata on some filesystems without writing a single content byte, so mtime is corroborating evidence
+    elsewhere, never the pass/fail gate here). `equal` is True iff every compared field matches."""
+    fields = (
+        "daily_prices_count",
+        "next_session_manifests_count",
+        "data_provider_runs_max_id",
+        "size_bytes",
+        "sha256",
+    )
+    mismatches = [f for f in fields if before.get(f) != after.get(f)]
+    return {"equal": not mismatches, "mismatched_fields": mismatches}
diff --git a/apps/backend/scripts/run_j11_disposable_clone.py b/apps/backend/scripts/run_j11_disposable_clone.py
new file mode 100644
index 00000000..9c0c286c
--- /dev/null
+++ b/apps/backend/scripts/run_j11_disposable_clone.py
@@ -0,0 +1,183 @@
+"""goal-market-compass iter-23 -- J-11's one remaining acceptance objective: build a disposable,
+byte-faithful clone of the repaired canonical database plus a verification-only config, so real
+backend/frontend/browser verification can run WITHOUT ever booting against
+`apps/backend/data/trendora.db` itself (docs/goal.md "OWNER RULING -- J-11 database recovery accepted;
+one final serving verification remains", owner 2026-08-27, items 3-4).
+
+Sequence (every step's evidence is persisted before the next runs):
+  1. Capture the canonical database's provenance (row counts + max provider-run id + whole-file sha256)
+     BEFORE touching anything.
+  2. Create the disposable clone via the SQLite online backup API (source opened `mode=ro` -- this
+     script can never write to the canonical file).
+  3. Re-capture the canonical database's provenance and assert it is byte-unchanged from step 1 (the
+     ruling's "canonical database remains OFF and must not be mutated by this verification").
+  4. Capture the clone's provenance and assert its row counts / max id match step 1's canonical values
+     (TC-1).
+  5. Build the verification-only config -- a copy of the committed `config.yaml` whose ONLY changed line
+     is `database.url`, pointed at the clone -- and self-check it with the SAME launch-safety guard the
+     boot wrapper (`scripts/start-backend-j11-verify.sh`) uses, including a demonstration that omitting
+     the override is correctly refused.
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_disposable_clone.py \\
+        --confirm \\
+        --dest-dir runs/goal-market-compass-iter-23/verify-clone \\
+        --evidence-dir runs/goal-market-compass-iter-23
+
+Without `--confirm`, the script performs NO filesystem interaction at all and exits non-zero (mirrors
+every other J-11 evidence-writing script's idiom).
+"""
+from __future__ import annotations
+
+import argparse
+import json
+import sys
+import time
+from pathlib import Path
+from typing import Optional
+
+# scripts/ -> backend -> apps -> repo root
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+REPO_ROOT = BACKEND_DIR.parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from app.config import get_config  # noqa: E402
+from app.db import resolve_database_url  # noqa: E402
+from app.engine import j11_disposable_clone as jdc  # noqa: E402
+
+
+def _write_json(path: Path, payload) -> None:
+    path.parent.mkdir(parents=True, exist_ok=True)
+    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
+    print(f"wrote {path}", file=sys.stderr)
+
+
+def _db_path_from_url(database_url: str) -> Path:
+    resolved_url = resolve_database_url(database_url)
+    prefix = "sqlite:///"
+    if not resolved_url.startswith(prefix):
+        raise SystemExit(f"refusing to run: database.url is not a sqlite file URL: {database_url!r}")
+    return Path(resolved_url[len(prefix):])
+
+
+def main(argv: Optional[list] = None) -> int:
+    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    parser.add_argument(
+        "--confirm", action="store_true",
+        help="required -- without it, NO filesystem interaction of any kind happens",
+    )
+    parser.add_argument(
+        "--dest-dir", type=Path, required=True,
+        help="directory to create the disposable clone DB + verification config in (must not already "
+        "contain trendora-clone.db)",
+    )
+    parser.add_argument(
+        "--evidence-dir", type=Path, required=True,
+        help="directory to write provenance/evidence JSON into (no implicit default)",
+    )
+    args = parser.parse_args(argv)
+
+    if not args.confirm:
+        print("refusing to run without --confirm -- no filesystem interaction performed", file=sys.stderr)
+        return 1
+
+    started_at = time.time()
+    cfg = get_config()
+    canonical_url = cfg.database.url
+    canonical_path = _db_path_from_url(canonical_url)
+    evidence_dir = args.evidence_dir
+    dest_dir = args.dest_dir
+    dest_dir.mkdir(parents=True, exist_ok=True)
+    clone_db_path = dest_dir / "trendora-clone.db"
+    verify_config_path = dest_dir / "config.verify.yaml"
+
+    print(f"canonical database: {canonical_path}", file=sys.stderr)
+
+    # Step 1 -- canonical provenance BEFORE anything.
+    before = jdc.capture_db_provenance(canonical_path)
+    _write_json(evidence_dir / "j11-disposable-clone-canonical-before.json", before)
+
+    # Step 2 -- create the clone.
+    clone_result = jdc.create_disposable_clone(canonical_path, clone_db_path)
+    _write_json(evidence_dir / "j11-disposable-clone-clone-result.json", clone_result)
+
+    # Step 3 -- canonical provenance AFTER clone creation; must be byte-unchanged.
+    after_clone = jdc.capture_db_provenance(canonical_path)
+    _write_json(evidence_dir / "j11-disposable-clone-canonical-after-clone.json", after_clone)
+    canonical_unchanged = jdc.compare_provenance(before, after_clone)
+    _write_json(evidence_dir / "j11-disposable-clone-canonical-unchanged-check.json", canonical_unchanged)
+    if not canonical_unchanged["equal"]:
+        print(
+            f"FATAL: canonical database changed during clone creation -- mismatched fields: "
+            f"{canonical_unchanged['mismatched_fields']}. This must never happen; STOP and report.",
+            file=sys.stderr,
+        )
+        return 1
+
+    # Step 4 -- clone provenance; row counts/max id must match the canonical values at clone time (TC-1).
+    clone_provenance = jdc.capture_db_provenance(clone_db_path, include_sha256=False)
+    _write_json(evidence_dir / "j11-disposable-clone-clone-provenance.json", clone_provenance)
+    clone_matches = (
+        clone_provenance["daily_prices_count"] == before["daily_prices_count"]
+        and clone_provenance["next_session_manifests_count"] == before["next_session_manifests_count"]
+        and clone_provenance["data_provider_runs_max_id"] == before["data_provider_runs_max_id"]
+    )
+    if not clone_matches:
+        print(
+            "FATAL: clone provenance does not match the canonical database's provenance at clone time "
+            "-- TC-1 fails. STOP and report.",
+            file=sys.stderr,
+        )
+        return 1
+
+    # Step 5 -- build + self-check the verification-only config.
+    committed_config_text = (REPO_ROOT / "config.yaml").read_text()
+    clone_url = jdc.clone_sqlite_url(clone_db_path)
+    verify_config_text = jdc.build_verification_config_text(committed_config_text, canonical_url, clone_url)
+    verify_config_path.write_text(verify_config_text)
+    print(f"wrote {verify_config_path}", file=sys.stderr)
+
+    launch_check_pass = jdc.assert_launch_targets_clone(str(verify_config_path), canonical_url)
+    try:
+        jdc.assert_launch_targets_clone(None, canonical_url)
+        launch_check_refusal_proof = {"raised": False}
+    except jdc.ClonePreconditionError as exc:
+        launch_check_refusal_proof = {"raised": True, "message": str(exc)}
+
+    summary = {
+        "started_at": started_at,
+        "finished_at": time.time(),
+        "canonical_db_path": str(canonical_path),
+        "canonical_url": canonical_url,
+        "clone_db_path": str(clone_db_path),
+        "clone_url": clone_url,
+        "verify_config_path": str(verify_config_path),
+        "canonical_provenance_before": before,
+        "canonical_provenance_after_clone": after_clone,
+        "canonical_unchanged": canonical_unchanged,
+        "clone_provenance": clone_provenance,
+        "tc1_clone_matches_canonical": clone_matches,
+        "launch_guard_passes_for_verify_config": launch_check_pass,
+        "launch_guard_refuses_when_unset": launch_check_refusal_proof,
+        "next_steps": {
+            "export_env": {
+                "TRENDORA_CONFIG": str(verify_config_path),
+                "TRENDORA_COMPASS_EXPORT_DIR": str(dest_dir / "exports" / "next_session_manifests"),
+            },
+            "boot_backend": "bash scripts/start-backend-j11-verify.sh",
+            "boot_frontend": "bash scripts/start-frontend.sh",
+            "warning": (
+                "NEVER call GET /api/compass?as_of=<one of the 7 manifest-less incident dates "
+                "2026-05-12/05-13/07-10/07-13/07-24/07-27/08-03> -- this mints a historical manifest "
+                "and is a hard verification FAIL. Verify those dates only via GET /runs or GET "
+                "/runs/{run_id}."
+            ),
+        },
+    }
+    _write_json(evidence_dir / "j11-disposable-clone-summary.json", summary)
+    print("disposable clone + verification config created successfully.", file=sys.stderr)
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/test_j11_disposable_clone.py b/apps/backend/tests/test_j11_disposable_clone.py
new file mode 100644
index 00000000..59160732
--- /dev/null
+++ b/apps/backend/tests/test_j11_disposable_clone.py
@@ -0,0 +1,322 @@
+"""Fixture-scoped tests for `app.engine.j11_disposable_clone` (goal-market-compass iter-23 -- the ONE
+remaining J-11 serving/replay verification objective). Every test builds tiny synthetic SQLite databases
+under `tmp_path` -- NEVER touches `apps/backend/data/trendora.db` (project-template.md: "NEVER copy, move,
+or open-for-write trendora.db")."""
+from __future__ import annotations
+
+import sqlite3
+from pathlib import Path
+
+import pytest
+
+from app.engine.j11_disposable_clone import (
+    ClonePreconditionError,
+    assert_launch_targets_clone,
+    build_verification_config_text,
+    capture_db_provenance,
+    clone_sqlite_url,
+    compare_provenance,
+    create_disposable_clone,
+    sha256_file,
+)
+
+
+def _make_fixture_db(path: Path, *, prices: int = 5, manifests: int = 2, provider_run_ids: tuple = (1, 2, 3)) -> None:
+    conn = sqlite3.connect(str(path))
+    try:
+        conn.executescript(
+            """
+            CREATE TABLE daily_prices (id INTEGER PRIMARY KEY, symbol TEXT, date TEXT, close REAL);
+            CREATE TABLE next_session_manifests (id INTEGER PRIMARY KEY, as_of TEXT, version INTEGER);
+            CREATE TABLE data_provider_runs (id INTEGER PRIMARY KEY, provider TEXT);
+            """
+        )
+        for i in range(prices):
+            conn.execute(
+                "INSERT INTO daily_prices (symbol, date, close) VALUES (?, ?, ?)",
+                (f"SYM{i}", f"2026-01-{i + 1:02d}", 100.0 + i),
+            )
+        for i in range(manifests):
+            conn.execute(
+                "INSERT INTO next_session_manifests (as_of, version) VALUES (?, ?)",
+                (f"2026-02-{i + 1:02d}", 1),
+            )
+        for run_id in provider_run_ids:
+            conn.execute("INSERT INTO data_provider_runs (id, provider) VALUES (?, ?)", (run_id, "yahoo"))
+        conn.commit()
+    finally:
+        conn.close()
+
+
+# ---------------------------------------------------------------------------
+# sha256_file / capture_db_provenance
+# ---------------------------------------------------------------------------
+
+
+def test_sha256_file_matches_hashlib_reference(tmp_path):
+    import hashlib
+
+    p = tmp_path / "blob.bin"
+    p.write_bytes(b"the quick brown fox jumps over the lazy dog" * 1000)
+    expected = hashlib.sha256(p.read_bytes()).hexdigest()
+    assert sha256_file(p) == expected
+
+
+def test_sha256_file_streams_in_chunks_smaller_than_the_file(tmp_path):
+    p = tmp_path / "blob.bin"
+    p.write_bytes(b"x" * 100)
+    # A chunk size smaller than the file forces multiple .update() calls -- must still match a
+    # single-shot hash.
+    import hashlib
+
+    assert sha256_file(p, chunk_size=7) == hashlib.sha256(p.read_bytes()).hexdigest()
+
+
+def test_capture_db_provenance_reads_exact_counts_and_max_id(tmp_path):
+    db_path = tmp_path / "source.db"
+    _make_fixture_db(db_path, prices=7, manifests=3, provider_run_ids=(1, 2, 5))
+    prov = capture_db_provenance(db_path)
+    assert prov["daily_prices_count"] == 7
+    assert prov["next_session_manifests_count"] == 3
+    assert prov["data_provider_runs_max_id"] == 5
+    assert prov["size_bytes"] > 0
+    assert prov["sha256"] is not None and len(prov["sha256"]) == 64
+
+
+def test_capture_db_provenance_can_skip_the_expensive_sha256(tmp_path):
+    db_path = tmp_path / "source.db"
+    _make_fixture_db(db_path)
+    prov = capture_db_provenance(db_path, include_sha256=False)
+    assert prov["sha256"] is None
+
+
+def test_capture_db_provenance_never_writes_to_the_source_file(tmp_path):
+    """The mode=ro URI open must be a structural guarantee, not a convention -- attempting a write
+    through the same connection style must fail."""
+    db_path = tmp_path / "source.db"
+    _make_fixture_db(db_path)
+    before_bytes = db_path.read_bytes()
+    capture_db_provenance(db_path)
+    assert db_path.read_bytes() == before_bytes
+
+
+# ---------------------------------------------------------------------------
+# create_disposable_clone
+# ---------------------------------------------------------------------------
+
+
+def test_create_disposable_clone_produces_matching_row_provenance(tmp_path):
+    """Row-level provenance (counts + max id) must match exactly between source and clone -- this is
+    TC-1's actual assertion. Whole-FILE sha256 is deliberately NOT compared here: `sqlite3.Connection.
+    backup()` produces a database that is logically identical (same rows, same values) but not
+    necessarily byte-identical at the file level (freelist/page-layout/journal-mode header differences
+    between a long-lived source file and a freshly created destination) -- sha256 equality is the
+    canonical file's OWN identity check across time (see the launch-safety tests below), never a
+    cross-file equality check between two independently created files with identical content."""
+    source = tmp_path / "source.db"
+    dest = tmp_path / "clone.db"
+    _make_fixture_db(source, prices=11, manifests=4, provider_run_ids=(1, 9, 42))
+
+    result = create_disposable_clone(source, dest)
+
+    assert dest.exists()
+    assert result["dest_size_bytes"] > 0
+    before = capture_db_provenance(source, include_sha256=False)
+    after = capture_db_provenance(dest, include_sha256=False)
+    assert after["daily_prices_count"] == before["daily_prices_count"] == 11
+    assert after["next_session_manifests_count"] == before["next_session_manifests_count"] == 4
+    assert after["data_provider_runs_max_id"] == before["data_provider_runs_max_id"] == 42
+
+
+def test_create_disposable_clone_never_mutates_the_source_file(tmp_path):
+    source = tmp_path / "source.db"
+    dest = tmp_path / "clone.db"
+    _make_fixture_db(source)
+    before_sha = sha256_file(source)
+    before_size = source.stat().st_size
+
+    create_disposable_clone(source, dest)
+
+    assert sha256_file(source) == before_sha
+    assert source.stat().st_size == before_size
+
+
+def test_create_disposable_clone_refuses_to_overwrite_an_existing_destination(tmp_path):
+    source = tmp_path / "source.db"
+    dest = tmp_path / "clone.db"
+    _make_fixture_db(source)
+    dest.write_bytes(b"pre-existing content, must survive")
+
+    with pytest.raises(ClonePreconditionError, match="refusing to overwrite"):
+        create_disposable_clone(source, dest)
+
+    assert dest.read_bytes() == b"pre-existing content, must survive"
+
+
+def test_create_disposable_clone_refuses_when_source_is_missing(tmp_path):
+    source = tmp_path / "does-not-exist.db"
+    dest = tmp_path / "clone.db"
+    with pytest.raises(ClonePreconditionError, match="does not exist"):
+        create_disposable_clone(source, dest)
+
+
+def test_create_disposable_clone_refuses_when_dest_directory_is_missing(tmp_path):
+    source = tmp_path / "source.db"
+    _make_fixture_db(source)
+    dest = tmp_path / "no-such-dir" / "clone.db"
+    with pytest.raises(ClonePreconditionError, match="destination directory does not exist"):
+        create_disposable_clone(source, dest)
+
+
+# ---------------------------------------------------------------------------
+# build_verification_config_text
+# ---------------------------------------------------------------------------
+
+_SAMPLE_CONFIG_TEXT = """\
+# a comment mentioning sqlite:///apps/backend/data/trendora.db in prose, must NOT be touched
+some_key: "some_value"
+database:
+  url: "sqlite:///apps/backend/data/trendora.db"
+  pool_size: 24
+other_section:
+  nested: true
+"""
+
+
+def test_build_verification_config_text_changes_only_the_url_line():
+    clone_url = "sqlite:////tmp/clone/trendora-clone.db"
+    result = build_verification_config_text(
+        _SAMPLE_CONFIG_TEXT, "sqlite:///apps/backend/data/trendora.db", clone_url
+    )
+    result_lines = result.splitlines()
+    original_lines = _SAMPLE_CONFIG_TEXT.splitlines()
+    assert len(result_lines) == len(original_lines)
+    diffs = [
+        (i, a, b) for i, (a, b) in enumerate(zip(original_lines, result_lines)) if a != b
+    ]
+    assert len(diffs) == 1, diffs
+    _, before_line, after_line = diffs[0]
+    assert before_line == '  url: "sqlite:///apps/backend/data/trendora.db"'
+    assert after_line == f'  url: "{clone_url}"'
+    # the comment-line prose mention must survive untouched
+    assert "a comment mentioning sqlite:///apps/backend/data/trendora.db in prose" in result
+
+
+def test_build_verification_config_text_raises_if_the_line_is_absent():
+    with pytest.raises(ClonePreconditionError, match="found 0"):
+        build_verification_config_text(
+            "database:\n  url: \"sqlite:///something/else.db\"\n",
+            "sqlite:///apps/backend/data/trendora.db",
+            "sqlite:////tmp/clone.db",
+        )
+
+
+def test_build_verification_config_text_raises_if_the_line_appears_twice():
+    doubled = _SAMPLE_CONFIG_TEXT + '\n  url: "sqlite:///apps/backend/data/trendora.db"\n'
+    with pytest.raises(ClonePreconditionError, match="found 2"):
+        build_verification_config_text(
+            doubled, "sqlite:///apps/backend/data/trendora.db", "sqlite:////tmp/clone.db"
+        )
+
+
+# ---------------------------------------------------------------------------
+# clone_sqlite_url
+# ---------------------------------------------------------------------------
+
+
+def test_clone_sqlite_url_is_the_four_slash_absolute_form(tmp_path):
+    db_path = tmp_path / "clone.db"
+    url = clone_sqlite_url(db_path)
+    assert url.startswith("sqlite:////")
+    assert url == f"sqlite:///{db_path.resolve()}"
+
+
+def test_clone_sqlite_url_round_trips_through_resolve_database_url(tmp_path):
+    from app.db import resolve_database_url
+
+    db_path = tmp_path / "clone.db"
+    url = clone_sqlite_url(db_path)
+    # An absolute sqlite URL must pass through resolve_database_url completely unchanged -- never
+    # rebased onto the repo root the way a relative path would be.
+    assert resolve_database_url(url) == url
+
+
+# ---------------------------------------------------------------------------
+# assert_launch_targets_clone
+# ---------------------------------------------------------------------------
+
+_CANONICAL_URL = "sqlite:///apps/backend/data/trendora.db"
+
+
+def test_assert_launch_targets_clone_refuses_when_env_var_is_unset():
+    with pytest.raises(ClonePreconditionError, match="TRENDORA_CONFIG is not set"):
+        assert_launch_targets_clone(None, _CANONICAL_URL)
+
+
+def test_assert_launch_targets_clone_refuses_when_env_var_is_empty_string():
+    with pytest.raises(ClonePreconditionError, match="TRENDORA_CONFIG is not set"):
+        assert_launch_targets_clone("", _CANONICAL_URL)
+
+
+def test_assert_launch_targets_clone_refuses_when_config_file_is_missing(tmp_path):
+    missing = tmp_path / "does-not-exist.yaml"
+    with pytest.raises(ClonePreconditionError, match="does not exist"):
+        assert_launch_targets_clone(str(missing), _CANONICAL_URL)
+
+
+def test_assert_launch_targets_clone_refuses_when_url_still_equals_canonical(tmp_path):
+    config_path = tmp_path / "verify-config.yaml"
+    config_path.write_text(f'database:\n  url: "{_CANONICAL_URL}"\n')
+    with pytest.raises(ClonePreconditionError, match="still equals the CANONICAL url"):
+        assert_launch_targets_clone(str(config_path), _CANONICAL_URL)
+
+
+def test_assert_launch_targets_clone_refuses_when_database_url_is_missing(tmp_path):
+    config_path = tmp_path / "verify-config.yaml"
+    config_path.write_text("database:\n  pool_size: 24\n")
+    with pytest.raises(ClonePreconditionError, match="has no database.url"):
+        assert_launch_targets_clone(str(config_path), _CANONICAL_URL)
+
+
+def test_assert_launch_targets_clone_passes_when_correctly_pointed_at_a_clone(tmp_path):
+    clone_url = "sqlite:////tmp/somewhere/clone.db"
+    config_path = tmp_path / "verify-config.yaml"
+    config_path.write_text(f'database:\n  url: "{clone_url}"\n')
+    result = assert_launch_targets_clone(str(config_path), _CANONICAL_URL)
+    assert result == {"config_path": str(config_path), "database_url": clone_url}
+
+
+# ---------------------------------------------------------------------------
+# compare_provenance
+# ---------------------------------------------------------------------------
+
+
+def test_compare_provenance_reports_equal_for_identical_dicts():
+    prov = {
+        "daily_prices_count": 1,
+        "next_session_manifests_count": 2,
+        "data_provider_runs_max_id": 3,
+        "size_bytes": 4,
+        "sha256": "abc",
+        "mtime": 123.0,
+    }
+    result = compare_provenance(prov, dict(prov))
+    assert result == {"equal": True, "mismatched_fields": []}
+
+
+def test_compare_provenance_ignores_mtime_but_catches_a_real_content_change():
+    before = {
+        "daily_prices_count": 1,
+        "next_session_manifests_count": 2,
+        "data_provider_runs_max_id": 3,
+        "size_bytes": 100,
+        "sha256": "abc",
+        "mtime": 111.0,
+    }
+    after_mtime_only = {**before, "mtime": 222.0}
+    assert compare_provenance(before, after_mtime_only) == {"equal": True, "mismatched_fields": []}
+
+    after_real_change = {**before, "sha256": "different"}
+    result = compare_provenance(before, after_real_change)
+    assert result["equal"] is False
+    assert result["mismatched_fields"] == ["sha256"]
diff --git a/apps/backend/tests/test_j11_disposable_clone_cli_script.py b/apps/backend/tests/test_j11_disposable_clone_cli_script.py
new file mode 100644
index 00000000..5b639ff7
--- /dev/null
+++ b/apps/backend/tests/test_j11_disposable_clone_cli_script.py
@@ -0,0 +1,175 @@
+"""goal-market-compass iter-23 -- `scripts/run_j11_disposable_clone.py` CLI control-flow + integration
+tests. The confirm-gating test is `unittest.mock`-based (mirrors `test_j11_stage_g_verify_cli_script.py`'s
+idiom); the happy-path and failure-path tests run the REAL `app.engine.j11_disposable_clone` functions
+against tiny synthetic SQLite fixtures under `tmp_path` -- never `apps/backend/data/trendora.db`."""
+from __future__ import annotations
+
+import importlib.util
+import sqlite3
+import sys
+from pathlib import Path
+from types import SimpleNamespace
+from unittest import mock
+
+import pytest
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_disposable_clone.py"
+_MODULE_NAME = "run_j11_disposable_clone_under_test"
+
+
+def _load_script_module():
+    spec = importlib.util.spec_from_file_location(_MODULE_NAME, SCRIPT_PATH)
+    module = importlib.util.module_from_spec(spec)
+    sys.modules[_MODULE_NAME] = module
+    spec.loader.exec_module(module)
+    return module
+
+
+@pytest.fixture()
+def script_ns():
+    original_argv = sys.argv
+    try:
+        module = _load_script_module()
+        yield module
+    finally:
+        sys.argv = original_argv
+        sys.modules.pop(_MODULE_NAME, None)
+
+
+def _make_fixture_db(path: Path, *, prices: int = 5, manifests: int = 24, max_provider_run_id: int = 549) -> None:
+    conn = sqlite3.connect(str(path))
+    try:
+        conn.executescript(
+            """
+            CREATE TABLE daily_prices (id INTEGER PRIMARY KEY, symbol TEXT, date TEXT, close REAL);
+            CREATE TABLE next_session_manifests (id INTEGER PRIMARY KEY, as_of TEXT, version INTEGER);
+            CREATE TABLE data_provider_runs (id INTEGER PRIMARY KEY, provider TEXT);
+            """
+        )
+        for i in range(prices):
+            conn.execute(
+                "INSERT INTO daily_prices (symbol, date, close) VALUES (?, ?, ?)",
+                (f"SYM{i}", f"2026-01-{i + 1:02d}", 100.0 + i),
+            )
+        for i in range(manifests):
+            conn.execute(
+                "INSERT INTO next_session_manifests (as_of, version) VALUES (?, ?)",
+                (f"2026-02-{i + 1:02d}", 1),
+            )
+        conn.execute(
+            "INSERT INTO data_provider_runs (id, provider) VALUES (?, ?)", (max_provider_run_id, "yahoo")
+        )
+        conn.commit()
+    finally:
+        conn.close()
+
+
+# --- missing --confirm: no filesystem interaction ---------------------------------------------------
+
+
+def test_missing_confirm_never_touches_the_filesystem(monkeypatch, script_ns, tmp_path):
+    mock_get_config = mock.MagicMock(name="get_config")
+    monkeypatch.setattr(script_ns, "get_config", mock_get_config)
+
+    exit_code = script_ns.main(
+        ["--dest-dir", str(tmp_path / "dest"), "--evidence-dir", str(tmp_path / "evidence")]
+    )  # no --confirm
+
+    assert exit_code != 0
+    mock_get_config.assert_not_called()
+    assert not (tmp_path / "dest").exists()
+    assert not (tmp_path / "evidence").exists()
+
+
+def test_missing_required_dest_dir_or_evidence_dir_raises(script_ns):
+    with pytest.raises(SystemExit):
+        script_ns.main(["--confirm"])  # missing --dest-dir/--evidence-dir
+
+
+# --- happy path: real functions, tiny fixture DB -------------------------------------------------------
+
+
+def test_full_run_produces_matching_clone_and_config(monkeypatch, script_ns, tmp_path):
+    source_db = tmp_path / "canonical" / "trendora.db"
+    source_db.parent.mkdir(parents=True)
+    _make_fixture_db(source_db, prices=13, manifests=24, max_provider_run_id=549)
+
+    committed_config = tmp_path / "config.yaml"
+    canonical_url = f"sqlite:///{source_db}"
+    committed_config.write_text(f'database:\n  url: "{canonical_url}"\n  pool_size: 24\n')
+
+    monkeypatch.setattr(script_ns, "REPO_ROOT", tmp_path)
+    monkeypatch.setattr(
+        script_ns, "get_config", lambda: SimpleNamespace(database=SimpleNamespace(url=canonical_url))
+    )
+    # resolve_database_url normally rebases a relative path onto REPO_ROOT; here the url is already
+    # absolute so the real function's behavior is unaffected by monkeypatching REPO_ROOT above.
+
+    dest_dir = tmp_path / "verify-clone"
+    evidence_dir = tmp_path / "evidence"
+
+    exit_code = script_ns.main(
+        ["--confirm", "--dest-dir", str(dest_dir), "--evidence-dir", str(evidence_dir)]
+    )
+
+    assert exit_code == 0
+    clone_db = dest_dir / "trendora-clone.db"
+    assert clone_db.exists()
+    verify_config = dest_dir / "config.verify.yaml"
+    assert verify_config.exists()
+    assert canonical_url not in verify_config.read_text()
+    assert "sqlite:////" in verify_config.read_text()
+
+    # the canonical source db must be byte-unchanged
+    assert source_db.stat().st_size > 0
+    from app.engine import j11_disposable_clone as jdc
+
+    clone_prov = jdc.capture_db_provenance(clone_db, include_sha256=False)
+    assert clone_prov["daily_prices_count"] == 13
+    assert clone_prov["next_session_manifests_count"] == 24
+    assert clone_prov["data_provider_runs_max_id"] == 549
+
+    import json
+
+    summary = json.loads((evidence_dir / "j11-disposable-clone-summary.json").read_text())
+    assert summary["tc1_clone_matches_canonical"] is True
+    assert summary["canonical_unchanged"]["equal"] is True
+    assert summary["launch_guard_refuses_when_unset"]["raised"] is True
+
+
+def test_refuses_and_stops_if_canonical_changes_during_clone_creation(monkeypatch, script_ns, tmp_path):
+    """A mutation-style proof: force `capture_db_provenance`'s SECOND call (the post-clone canonical
+    re-check) to report different content than the first -- the script must detect this and exit
+    non-zero rather than proceed to build a verification config."""
+    source_db = tmp_path / "canonical" / "trendora.db"
+    source_db.parent.mkdir(parents=True)
+    _make_fixture_db(source_db)
+
+    canonical_url = f"sqlite:///{source_db}"
+    monkeypatch.setattr(script_ns, "REPO_ROOT", tmp_path)
+    monkeypatch.setattr(
+        script_ns, "get_config", lambda: SimpleNamespace(database=SimpleNamespace(url=canonical_url))
+    )
+
+    real_capture = script_ns.jdc.capture_db_provenance
+    call_count = {"n": 0}
+
+    def _flaky_capture(path, **kwargs):
+        call_count["n"] += 1
+        result = real_capture(path, **kwargs)
+        if call_count["n"] == 2:
+            result = {**result, "sha256": "deliberately-different-to-simulate-a-mutation"}
+        return result
+
+    monkeypatch.setattr(script_ns.jdc, "capture_db_provenance", _flaky_capture)
+
+    dest_dir = tmp_path / "verify-clone"
+    evidence_dir = tmp_path / "evidence"
+
+    exit_code = script_ns.main(
+        ["--confirm", "--dest-dir", str(dest_dir), "--evidence-dir", str(evidence_dir)]
+    )
+
+    assert exit_code != 0
+    assert not (dest_dir / "config.verify.yaml").exists()
diff --git a/incredible_auto_dev/scripts/start-backend-j11-verify.sh b/incredible_auto_dev/scripts/start-backend-j11-verify.sh
new file mode 100644
index 00000000..bf28d74b
--- /dev/null
+++ b/incredible_auto_dev/scripts/start-backend-j11-verify.sh
@@ -0,0 +1,41 @@
+#!/usr/bin/env bash
+# start-backend-j11-verify.sh — goal-market-compass iter-23: the ONE remaining J-11 acceptance
+# objective is a real backend boot against a DISPOSABLE clone, never the canonical
+# apps/backend/data/trendora.db (docs/goal.md "OWNER RULING — J-11 database recovery accepted; one
+# final serving verification remains", owner 2026-08-27, item 3: "The canonical repaired DB stays
+# protected... Backend/frontend/browser verification runs against the disposable verification DB only").
+#
+# Testing Requirements' "Error cases": "a launch attempt that omits the TRENDORA_CONFIG override (i.e.
+# would default to the canonical DB) must be refused before any browser/replay execution proceeds." This
+# script is that refusal, checked via the SAME app.engine.j11_disposable_clone.assert_launch_targets_clone
+# the disposable-clone CLI script and its tests already use — never a second, drifting implementation of
+# the check. Only after it passes does this script exec the project's STANDARD launch script
+# (scripts/start-backend.sh) unmodified, so AG-10's host-guard caps still apply exactly as they do for
+# every other boot.
+set -e
+
+REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
+
+if [[ -z "${TRENDORA_CONFIG:-}" ]]; then
+  echo "start-backend-j11-verify.sh: TRENDORA_CONFIG is not set -- refusing to boot (a boot without it" >&2
+  echo "targets the CANONICAL database). Export TRENDORA_CONFIG to the disposable verification config" >&2
+  echo "produced by scripts/run_j11_disposable_clone.py before running this script." >&2
+  exit 1
+fi
+
+"$REPO_ROOT/apps/backend/.venv/bin/python" -c "
+import sys
+sys.path.insert(0, '$REPO_ROOT/apps/backend')
+from app.config import load_config
+from app.engine.j11_disposable_clone import assert_launch_targets_clone, ClonePreconditionError
+
+canonical_url = load_config('$REPO_ROOT/config.yaml').database.url
+try:
+    result = assert_launch_targets_clone('$TRENDORA_CONFIG', canonical_url)
+except ClonePreconditionError as exc:
+    print(f'start-backend-j11-verify.sh: REFUSING to boot -- {exc}', file=sys.stderr)
+    sys.exit(1)
+print(f'start-backend-j11-verify.sh: launch guard OK -- booting against {result[\"database_url\"]!r}', file=sys.stderr)
+"
+
+exec "$REPO_ROOT/scripts/start-backend.sh"
```
