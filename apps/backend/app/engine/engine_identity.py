"""app.engine.engine_identity — the deterministic engine-code + config identity stamp (goal-market-compass
iter-3, J-05/J-06).

`compute_engine_identity(config)` hashes:

  - the CONTENT of every file listed in `config.provenance.engine_files` (repo-root-relative paths), and
  - the VALUES of every dotted config path listed in `config.provenance.config_keys`

into ONE sha256 hex digest. A code change to a listed engine file, or a config change under a listed
key, moves this stamp; anything else does not. It is embedded verbatim in every next-session manifest's
`generation.engine_identity` and stamped on newly created `ScannerRun` rows only (via
`app.engine.scanner.persist_run_payload`) — an existing row is never backfilled (a NULL `engine_identity`
on an old row is the honest "pre-stamping era" marker, never retroactively filled in).

A listed file that cannot be read (moved/renamed) records an explicit `None` for that path rather than
silently omitting it or crashing — an honest gap that still changes the digest (so a broken provenance
list is visible in the stamp itself, never masked).

No score/return is read here — this module touches no snapshot table, no bar, and no forward return
(AG-5, AG-9): it hashes source files and already-loaded config values only.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

from app.config import REPO_ROOT, Config, get_config


def _config_value(cfg_dict: dict, dotted_key: str) -> Any:
    """Resolve one dotted config path (e.g. `"compass.selection"`) against the full config dict, walking
    nested mappings only. Returns `None` for a path that does not resolve (never raises) — an absent key
    still changes the digest the same honest way a missing engine file does."""
    node: Any = cfg_dict
    for part in dotted_key.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node


def compute_engine_identity(config: Optional[Config] = None) -> str:
    """The sha256 hex digest over `{"files": {path: content_sha256_or_null}, "config": {dotted_key:
    value}}`, canonically serialized (`sort_keys=True`) so the digest is reproducible from the SAME
    inputs regardless of dict insertion order — the same reproducibility contract
    `app.engine.compass.build_manifest_payload`'s `content_hash` already follows."""
    cfg = config or get_config()
    prov = cfg.provenance

    file_hashes: dict[str, Optional[str]] = {}
    for rel_path in prov.engine_files:
        path = REPO_ROOT / rel_path
        try:
            content = path.read_bytes()
        except OSError:
            file_hashes[rel_path] = None  # honest gap — never silently skipped, never crashes
            continue
        file_hashes[rel_path] = hashlib.sha256(content).hexdigest()

    cfg_dict = cfg.model_dump()
    config_subset = {key: _config_value(cfg_dict, key) for key in prov.config_keys}

    canonical = json.dumps({"files": file_hashes, "config": config_subset}, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()
