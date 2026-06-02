"""Methodology catalog tests (iter-12, J-12) — the config-backed Setup & Pattern glossary.

`build_catalog(config)` assembles the served glossary from `config.methodology`: it resolves each
threshold `ref` to its LIVE config value (the matching-config keystone — the displayed number always
equals the config value the engine reads, never re-typed), passes `text` rows verbatim, and asserts
the catalog documents EVERY canonical setup status (`app.engine.setups.ALL_STATUSES`) and EVERY
detected pattern (`config.patterns`). It computes/stores no score and needs NO seeded DB (config only,
so these tests are fast)."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app.config import DEFAULT_CONFIG_PATH, ConfigError, load_config, resolve_ref
from app.engine.methodology import build_catalog
from app.engine.setups import ALL_STATUSES


def _committed_raw() -> dict:
    """The committed config.yaml as a plain mapping (includes the iter-12 methodology section)."""
    with open(DEFAULT_CONFIG_PATH) as fh:
        return yaml.safe_load(fh)


def _write(tmp_path: Path, data: dict) -> str:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return str(path)


def test_committed_catalog_shape_and_intro():
    catalog = build_catalog(load_config())
    assert isinstance(catalog["entries"], list) and catalog["entries"]
    assert catalog.get("intro")
    entry = catalog["entries"][0]
    assert set(entry) >= {"key", "kind", "name", "meaning", "thresholds", "example"}
    assert entry["kind"] in {"setup", "pattern"}


def test_catalog_documents_every_status_and_pattern():
    """Completeness: every ALL_STATUSES status is a kind:setup entry and every config.patterns
    pattern is a kind:pattern entry (the glossary can never silently drop a status/pattern)."""
    config = load_config()
    catalog = build_catalog(config)
    setup_keys = {e["key"] for e in catalog["entries"] if e["kind"] == "setup"}
    pattern_keys = {e["key"] for e in catalog["entries"] if e["kind"] == "pattern"}
    assert setup_keys == set(ALL_STATUSES)
    assert pattern_keys == set(config.patterns.model_dump())
    assert "vcp" in pattern_keys


def test_vcp_is_a_pattern_not_a_status():
    """VCP is documented as a PATTERN, never as a 7th setup status (anti-goal: VCP is a pattern)."""
    catalog = build_catalog(load_config())
    setup_keys = {e["key"] for e in catalog["entries"] if e["kind"] == "setup"}
    assert "VCP" not in ALL_STATUSES
    assert "vcp" not in ALL_STATUSES
    assert "VCP" not in setup_keys and "vcp" not in setup_keys
    vcp = next(e for e in catalog["entries"] if e["key"] == "vcp")
    assert vcp["kind"] == "pattern"


def test_matching_config_keystone():
    """Every displayed threshold value equals the LIVE config value its `ref` resolves to (no
    hard-coded copy, no drift); every `text` row passes through verbatim."""
    config = load_config()
    catalog = build_catalog(config)
    checked = 0
    for entry in config.methodology.entries:
        served = next(e for e in catalog["entries"] if e["key"] == entry.key)
        for threshold, row in zip(entry.thresholds, served["thresholds"]):
            if threshold.ref is not None:
                assert row["value"] == resolve_ref(config, threshold.ref)
                assert "text" not in row
                checked += 1
            else:
                assert row["text"] == threshold.text
                assert "value" not in row
    assert checked > 0  # the catalog actually exercises live config refs


def test_actionable_thresholds_match_decision_rules():
    """Spot-check: the Actionable entry's numbers are exactly the decision_rules cutoffs."""
    config = load_config()
    catalog = build_catalog(config)
    actionable = next(e for e in catalog["entries"] if e["key"] == "Actionable")
    by_label = {r["label"]: r for r in actionable["thresholds"]}
    assert by_label["Leadership"]["value"] == config.decision_rules.actionable.leadership
    assert by_label["Entry Quality"]["value"] == config.decision_rules.actionable.entry
    assert by_label["Risk (danger)"]["value"] == config.decision_rules.actionable.risk


def test_vcp_thresholds_match_patterns_config():
    """Spot-check: the VCP entry's numbers are exactly the patterns.vcp tunables."""
    config = load_config()
    catalog = build_catalog(config)
    vcp = next(e for e in catalog["entries"] if e["key"] == "vcp")
    by_label = {r["label"]: r for r in vcp["thresholds"]}
    assert by_label["Min contractions"]["value"] == config.patterns.vcp.min_contractions
    assert by_label["Max base depth"]["value"] == config.patterns.vcp.max_base_depth_pct
    assert by_label["Volume dry-up"]["value"] == config.patterns.vcp.volume_dryup_ratio


def test_new_pattern_thresholds_match_patterns_config():
    """iter-9 spot-check: each new pattern entry's numbers are exactly its `patterns.<name>` tunables —
    resolved live from config (the matching-config keystone), never re-typed in the catalog copy."""
    config = load_config()
    catalog = build_catalog(config)

    pb = next(e for e in catalog["entries"] if e["key"] == "pullback_to_rising_dma")
    pb_by_label = {r["label"]: r for r in pb["thresholds"]}
    assert pb["kind"] == "pattern"
    assert pb_by_label["Moving-average basis"]["value"] == config.patterns.pullback_to_rising_dma.ma_period
    assert pb_by_label["Min DMA slope"]["value"] == config.patterns.pullback_to_rising_dma.min_dma_slope_pct
    assert pb_by_label["Max pullback depth"]["value"] == config.patterns.pullback_to_rising_dma.max_pullback_depth_pct

    fb = next(e for e in catalog["entries"] if e["key"] == "flat_base_breakout")
    fb_by_label = {r["label"]: r for r in fb["thresholds"]}
    assert fb["kind"] == "pattern"
    assert fb_by_label["Base window"]["value"] == config.patterns.flat_base_breakout.base_window
    assert fb_by_label["Max base depth"]["value"] == config.patterns.flat_base_breakout.max_base_depth_pct
    assert fb_by_label["Min breakout volume"]["value"] == config.patterns.flat_base_breakout.min_breakout_volume_ratio


def test_incomplete_pattern_catalog_raises(tmp_path):
    """Dropping a detected pattern's catalog entry → build_catalog raises (pattern completeness — adding
    a config.patterns key without its kind:pattern entry must fail the boot loudly)."""
    raw = _committed_raw()
    raw["methodology"]["entries"] = [
        e for e in raw["methodology"]["entries"] if e.get("key") != "flat_base_breakout"
    ]
    config = load_config(_write(tmp_path, raw))  # the loader still validates; completeness is build_catalog's job
    with pytest.raises(ValueError):
        build_catalog(config)


# --- iter-7: Universe Selection section (J-22) ----------------------------------------------

def test_universe_selection_section_present_and_resolves():
    """The catalog carries a Universe Selection section: the membership-rule prose, the three screen
    thresholds resolved LIVE from `universe.filters`, and the resolved size read from the ONE canonical
    universe (a read, not a literal). No hard-coded copy/number."""
    config = load_config()
    catalog = build_catalog(config)
    us = catalog["universe_selection"]
    assert isinstance(us["membership_rule"], str) and us["membership_rule"].strip()
    assert us["resolved_size"] == len(config.universe.symbols)
    # the three thresholds resolve to the SAME numbers the offline screen reads (matching-config keystone)
    by_label = {r["label"]: r for r in us["thresholds"]}
    assert by_label["Minimum market cap"]["value"] == config.universe.filters.min_market_cap
    assert by_label["Minimum average daily dollar volume"]["value"] == config.universe.filters.min_dollar_vol
    assert by_label["Minimum share price"]["value"] == config.universe.filters.min_price
    # every threshold is a resolved numeric row (a value), never re-typed prose
    assert all("value" in r for r in us["thresholds"])


def test_universe_selection_thresholds_are_live_refs(tmp_path):
    """Changing `universe.filters` in config moves the displayed Universe Selection numbers with no code
    change (the numbers are `ref`s, never hard-coded copy — anti-goal: No magic numbers)."""
    raw = _committed_raw()
    raw["universe"]["filters"]["min_price"] = 25  # a different, distinctive value
    config = load_config(_write(tmp_path, raw))
    us = build_catalog(config)["universe_selection"]
    by_label = {r["label"]: r for r in us["thresholds"]}
    assert by_label["Minimum share price"]["value"] == 25


def test_universe_selection_is_not_a_setup_or_pattern_entry():
    """The Universe Selection section is SEPARATE from the setup/pattern catalog — it must not appear as
    a glossary entry (which would break the completeness assertion / setup-filter vocabulary)."""
    catalog = build_catalog(load_config())
    keys = {e["key"] for e in catalog["entries"]}
    assert "universe_selection" not in keys
    assert all(e["kind"] in {"setup", "pattern"} for e in catalog["entries"])


def test_config_only_extra_entry_renders_with_no_code_change(tmp_path):
    """Adding ONE extra catalog entry in config (referencing existing keys) surfaces it via
    build_catalog with NO Python change (anti-goal: config-driven UI)."""
    raw = _committed_raw()
    raw["methodology"]["entries"].append(
        {
            "key": "ZZZ-demo",
            "kind": "setup",
            "name": "Demo Extra",
            "meaning": "A config-only extra entry proving the catalog is data-driven.",
            "example": "Added in config.yaml, rendered with no code change.",
            "thresholds": [
                {"label": "Leadership", "cmp": ">=", "ref": "decision_rules.actionable.leadership"},
            ],
        }
    )
    config = load_config(_write(tmp_path, raw))
    catalog = build_catalog(config)
    extra = next(e for e in catalog["entries"] if e["key"] == "ZZZ-demo")
    assert extra["name"] == "Demo Extra"
    assert extra["thresholds"][0]["value"] == config.decision_rules.actionable.leadership


def test_incomplete_catalog_raises(tmp_path):
    """Dropping a canonical setup status from the catalog → build_catalog raises (completeness)."""
    raw = _committed_raw()
    raw["methodology"]["entries"] = [
        e for e in raw["methodology"]["entries"] if e.get("key") != "Extended"
    ]
    config = load_config(_write(tmp_path, raw))
    with pytest.raises(ValueError):
        build_catalog(config)


def test_unresolvable_ref_raises_config_error(tmp_path):
    """A threshold whose ref points at a non-existent config path fails the boot loudly (anti-goal:
    No fabricated data — never a silent/placeholder threshold)."""
    raw = _committed_raw()
    raw["methodology"]["entries"][0]["thresholds"][0] = {
        "label": "Bogus",
        "cmp": ">=",
        "ref": "decision_rules.nope.missing",
    }
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, raw))
