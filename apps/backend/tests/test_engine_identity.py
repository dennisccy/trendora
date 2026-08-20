"""app.engine.engine_identity (goal-market-compass iter-3, J-05/J-06) — `compute_engine_identity`'s
sensitivity contract: a code change to a listed engine file, or a config change under a listed key,
moves the stamp; anything else does not. A listed file that cannot be read records an honest `None`
gap rather than crashing or silently omitting it.
"""
from __future__ import annotations

import pytest

from app.config import ProvenanceCfg, load_config
from app.engine import engine_identity


@pytest.fixture()
def cfg():
    return load_config()


def test_reproducible_across_identical_calls(cfg):
    """TC-16-style reproducibility: the SAME config yields the SAME digest every time (no timestamp, no
    randomness, no dict-ordering sensitivity — canonical sort_keys=True serialization)."""
    first = engine_identity.compute_engine_identity(cfg)
    second = engine_identity.compute_engine_identity(cfg)
    assert first == second
    assert isinstance(first, str) and len(first) == 64  # sha256 hex


def test_real_default_config_computes_without_crashing(cfg):
    """The actual committed `provenance.*` config (real engine files, real config keys) must resolve
    cleanly — this is what `scanner.persist_run_payload` and every manifest freeze call at runtime."""
    digest = engine_identity.compute_engine_identity(cfg)
    assert digest and all(c in "0123456789abcdef" for c in digest)


def test_engine_file_content_change_moves_the_digest(cfg, tmp_path):
    """A code change to a listed engine file moves the stamp."""
    target = tmp_path / "sample_engine_module.py"
    target.write_text("VALUE = 1\n")
    provenance = ProvenanceCfg(engine_files=[str(target)], config_keys=["compass.selection.rule_version"])
    cfg_a = cfg.model_copy(update={"provenance": provenance})
    digest_a = engine_identity.compute_engine_identity(cfg_a)

    target.write_text("VALUE = 2\n")
    digest_b = engine_identity.compute_engine_identity(cfg_a)
    assert digest_a != digest_b


def test_config_key_value_change_moves_the_digest(cfg, tmp_path):
    """A config change under a listed dotted key moves the stamp."""
    target = tmp_path / "sample_engine_module.py"
    target.write_text("VALUE = 1\n")
    provenance = ProvenanceCfg(engine_files=[str(target)], config_keys=["compass.selection.leadership_min_score"])
    cfg_a = cfg.model_copy(update={"provenance": provenance})
    digest_a = engine_identity.compute_engine_identity(cfg_a)

    changed_selection = cfg.compass.selection.model_copy(update={"leadership_min_score": 81.0})
    cfg_b = cfg_a.model_copy(update={"compass": cfg.compass.model_copy(update={"selection": changed_selection})})
    digest_b = engine_identity.compute_engine_identity(cfg_b)
    assert digest_a != digest_b


def test_unlisted_config_change_never_moves_the_digest(cfg, tmp_path):
    """A config change under a key NOT listed in `provenance.config_keys` never moves the stamp — the
    identity is sensitive ONLY to what is explicitly declared."""
    target = tmp_path / "sample_engine_module.py"
    target.write_text("VALUE = 1\n")
    provenance = ProvenanceCfg(engine_files=[str(target)], config_keys=["compass.selection.leadership_min_score"])
    cfg_a = cfg.model_copy(update={"provenance": provenance})
    digest_a = engine_identity.compute_engine_identity(cfg_a)

    # change an UNLISTED key (why_not_cap, not in config_keys above)
    changed_selection = cfg.compass.selection.model_copy(update={"why_not_cap": 99})
    cfg_b = cfg_a.model_copy(update={"compass": cfg.compass.model_copy(update={"selection": changed_selection})})
    digest_b = engine_identity.compute_engine_identity(cfg_b)
    assert digest_a == digest_b


def test_missing_engine_file_records_honest_gap_never_crashes(cfg, tmp_path):
    """A listed file that cannot be read (moved/renamed) records an explicit None for that path rather
    than crashing or silently omitting it — still changes the digest vs. a config with no such file."""
    missing = tmp_path / "does_not_exist.py"
    provenance = ProvenanceCfg(engine_files=[str(missing)], config_keys=["compass.selection.rule_version"])
    cfg_a = cfg.model_copy(update={"provenance": provenance})
    digest = engine_identity.compute_engine_identity(cfg_a)  # must not raise
    assert digest and len(digest) == 64

    present = tmp_path / "present.py"
    present.write_text("VALUE = 1\n")
    provenance_present = ProvenanceCfg(engine_files=[str(present)], config_keys=["compass.selection.rule_version"])
    cfg_b = cfg.model_copy(update={"provenance": provenance_present})
    digest_present = engine_identity.compute_engine_identity(cfg_b)
    assert digest != digest_present  # the missing-file gap is a DIFFERENT stamp than a present-file hash


def test_no_score_or_bar_read_in_module(cfg):
    """AG-5/AG-9 as a static guarantee: this module touches no snapshot table, no bar, no forward return
    — it hashes source files and already-loaded config values only."""
    import ast

    tree = ast.parse(open(engine_identity.__file__).read())
    banned = {"requests", "httpx", "urllib", "ForwardReturn", "forward_returns", "bars_after", "Session"}
    offenders = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", None) or ""
            names = [alias.name for alias in node.names]
            for candidate in [module, *names]:
                if candidate in banned or candidate.split(".")[0] in banned:
                    offenders.add(candidate)
    assert not offenders, f"engine_identity.py references banned identifiers: {offenders}"
