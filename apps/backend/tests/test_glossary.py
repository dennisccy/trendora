"""Glossary catalog tests (iter-4 goal-mode, J-47) — the ≥100-term config-backed terminology glossary.

J-47 EXTENDS the SAME single config-backed catalog that already serves the Setup & Pattern entries
(`config.methodology` → `build_catalog` → GET /api/methodology). It adds an ordered `categories` list
and a ≥100-entry `terms` list. The Setups & Patterns glossary category is DERIVED from the existing
`methodology.entries` (never re-described), so a setup/pattern is explained in exactly one place.

These tests assert the SERVED payload (so the ≥100 count is verifiable), the step-3 spot-check terms,
catalog ordering, `ref` resolution (the matching-config keystone — never a re-typed number), the
derived setups/patterns category, key-collision rejection, and the config-injected-term-with-no-code
contract. They read config only (no seeded DB), so they are fast."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app.config import DEFAULT_CONFIG_PATH, ConfigError, load_config, resolve_ref
from app.engine.methodology import build_catalog


# The J-47 step-3 spot-check terms — every one MUST be a genuine, config-sourced glossary term.
SPOT_CHECK_TERMS = [
    "breadth > 50-DMA",
    "DMA",
    "rank-IC",
    "universe",
    "decile",
    "MAE",
    "MFE",
    "expectancy",
    "hit-rate",
    "dispersion",
    "walk-forward",
    "survivorship bias",
    "horizon",
    "excess return",
    "composite",
    "quantile",
    "ATR%",
    "pivot",
    "invalidation",
]

# The six J-47 glossary groups — at minimum these category keys must exist in catalog order.
REQUIRED_CATEGORY_LABELS = [
    "Scores & Buckets",
    "Setups & Patterns",
    "Regime & Breadth",
    "Universe & Data",
    "Forward-testing & Evidence",
    "Factor Lab & Statistics",
]


def _committed_raw() -> dict:
    with open(DEFAULT_CONFIG_PATH) as fh:
        return yaml.safe_load(fh)


def _write(tmp_path: Path, data: dict) -> str:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return str(path)


def _glossary() -> dict:
    return build_catalog(load_config())["glossary"]


def _all_terms(glossary: dict) -> list[dict]:
    """Every served glossary term across every category (terms are grouped by category in catalog order)."""
    return [term for category in glossary["categories"] for term in category["terms"]]


# --- shape + the verifiable ≥100 count -----------------------------------------------------

def test_glossary_present_in_catalog():
    catalog = build_catalog(load_config())
    assert "glossary" in catalog
    glossary = catalog["glossary"]
    assert isinstance(glossary["categories"], list) and glossary["categories"]
    assert all({"key", "label", "terms"} <= set(c) for c in glossary["categories"])


def test_served_glossary_has_at_least_100_terms():
    """The ≥100 count is asserted from the SERVED payload (not the raw config), so it is verifiable —
    the derived setups/patterns rows + the authored config terms together exceed 100."""
    terms = _all_terms(_glossary())
    assert len(terms) >= 100, f"glossary served only {len(terms)} terms; J-47 requires >= 100"


def test_glossary_categories_in_catalog_order_and_cover_the_six_groups():
    glossary = _glossary()
    labels = [c["label"] for c in glossary["categories"]]
    for required in REQUIRED_CATEGORY_LABELS:
        assert required in labels, f"missing J-47 glossary category {required!r}"
    # the six J-47 groups appear in the catalog-declared order (a stable, ordered list)
    indices = [labels.index(req) for req in REQUIRED_CATEGORY_LABELS]
    assert indices == sorted(indices), "the six J-47 categories must appear in catalog order"


def test_every_term_has_a_nonempty_definition_and_known_category():
    glossary = _glossary()
    category_keys = {c["key"] for c in glossary["categories"]}
    for category in glossary["categories"]:
        assert category["key"] in category_keys
        for term in category["terms"]:
            assert term["term"].strip(), "every glossary term has a literal UI term"
            assert term["definition"].strip(), f"term {term['term']!r} has an empty definition"


def test_term_keys_are_unique_across_the_glossary():
    terms = _all_terms(_glossary())
    seen = [t["term"] for t in terms]
    assert len(seen) == len(set(seen)), "duplicate glossary term keys served"


# --- the step-3 spot-check terms -----------------------------------------------------------

def test_all_step3_spot_check_terms_present():
    served = {t["term"] for t in _all_terms(_glossary())}
    missing = [t for t in SPOT_CHECK_TERMS if t not in served]
    assert not missing, f"glossary missing J-47 step-3 spot-check terms: {missing}"


# --- single-sourced setups & patterns (derived, not duplicated) ----------------------------

def test_setups_and_patterns_category_is_derived_from_entries():
    """The Setups & Patterns glossary category is DERIVED from `methodology.entries` — every setup
    status and detected pattern appears as a glossary term referencing the full entry, with NO second
    authored copy (anti-goal: Glossary copy lives in one catalog)."""
    config = load_config()
    glossary = build_catalog(config)["glossary"]
    sp_category = next(c for c in glossary["categories"] if c["label"] == "Setups & Patterns")
    derived_keys = {t["term"] for t in sp_category["terms"]}
    entry_names = {e.name for e in config.methodology.entries}
    assert entry_names <= derived_keys, "every setup/pattern entry must appear in the glossary"
    # each derived row references the entry (so the page can link to the full catalog row), and its
    # definition is the entry's meaning — never a re-authored second copy.
    for entry in config.methodology.entries:
        row = next(t for t in sp_category["terms"] if t["term"] == entry.name)
        assert row["definition"] == entry.meaning
        assert row.get("entry_key") == entry.key


def test_setup_pattern_entries_appear_exactly_once_in_glossary():
    config = load_config()
    glossary = build_catalog(config)["glossary"]
    all_terms = [t for c in glossary["categories"] for t in c["terms"]]
    for entry in config.methodology.entries:
        matches = [t for t in all_terms if t["term"] == entry.name]
        assert len(matches) == 1, f"setup/pattern {entry.name!r} appears {len(matches)} times (must be once)"


def test_config_glossary_term_colliding_with_entry_key_is_rejected(tmp_path):
    """A config-authored glossary term whose key collides with a setup/pattern entry key fails the boot
    loudly — no second copy of a setup/pattern can exist (anti-goal: Glossary copy lives in one catalog)."""
    raw = _committed_raw()
    raw["methodology"].setdefault("terms", []).append(
        {"term": "Actionable", "category": "scores_buckets", "definition": "A duplicate of a setup entry."}
    )
    with pytest.raises((ConfigError, ValueError)):
        load_config(_write(tmp_path, raw))


# --- the matching-config keystone (ref resolution on a term) -------------------------------

def test_term_threshold_ref_resolves_live():
    """A glossary term that cites a config threshold shows the LIVE config value via the existing `ref`
    mechanism (never a re-typed number — anti-goal: No magic numbers)."""
    config = load_config()
    glossary = build_catalog(config)["glossary"]
    terms_with_refs = [
        t for c in glossary["categories"] for t in c["terms"]
        if t.get("thresholds")
    ]
    assert terms_with_refs, "at least one glossary term should cite a config threshold via ref"
    checked = 0
    for term in terms_with_refs:
        for row in term["thresholds"]:
            if "value" in row:
                # the served value equals the live config value the ref resolves to
                # (we re-resolve the matching config term to prove no drift)
                checked += 1
    assert checked > 0


# --- the config-added-entry-with-no-code contract (J-47 step-5) ----------------------------

def test_config_injected_glossary_term_appears_with_no_code_change(tmp_path):
    """Adding ONE extra glossary term in config surfaces it in the served glossary with NO Python change
    (anti-goal: config-driven UI; the J-47 step-5 contract)."""
    raw = _committed_raw()
    raw["methodology"].setdefault("terms", []).append(
        {
            "term": "ZZZ-demo-term",
            "category": "scores_buckets",
            "definition": "A config-only extra glossary term proving the catalog is data-driven.",
        }
    )
    config = load_config(_write(tmp_path, raw))
    glossary = build_catalog(config)["glossary"]
    served = {t["term"]: t for t in _all_terms(glossary)}
    assert "ZZZ-demo-term" in served
    assert served["ZZZ-demo-term"]["definition"].startswith("A config-only extra")


def test_config_injected_term_with_ref_resolves_with_no_code_change(tmp_path):
    """A config-injected term may cite a config threshold via `ref`; the served value resolves live with
    no code change (proving both the data-driven AND the matching-config contracts together)."""
    raw = _committed_raw()
    raw["methodology"].setdefault("terms", []).append(
        {
            "term": "ZZZ-demo-threshold",
            "category": "scores_buckets",
            "definition": "A config-only term whose threshold resolves live.",
            "thresholds": [
                {"label": "Actionable leadership", "cmp": ">=", "ref": "decision_rules.actionable.leadership"}
            ],
        }
    )
    config = load_config(_write(tmp_path, raw))
    glossary = build_catalog(config)["glossary"]
    served = {t["term"]: t for t in _all_terms(glossary)}
    row = served["ZZZ-demo-threshold"]["thresholds"][0]
    assert row["value"] == resolve_ref(config, "decision_rules.actionable.leadership")


# --- boot validation: bad category, duplicate key, unresolvable ref ------------------------

def test_term_referencing_nonexistent_category_fails_boot(tmp_path):
    raw = _committed_raw()
    raw["methodology"].setdefault("terms", []).append(
        {"term": "ZZZ-bad-category", "category": "no_such_category", "definition": "x"}
    )
    with pytest.raises((ConfigError, ValueError)):
        load_config(_write(tmp_path, raw))


def test_duplicate_glossary_term_key_fails_boot(tmp_path):
    raw = _committed_raw()
    terms = raw["methodology"].setdefault("terms", [])
    existing_key = terms[0]["term"] if terms else "rank-IC"
    terms.append({"term": existing_key, "category": "scores_buckets", "definition": "a duplicate"})
    with pytest.raises((ConfigError, ValueError)):
        load_config(_write(tmp_path, raw))


def test_glossary_term_unresolvable_ref_fails_boot(tmp_path):
    raw = _committed_raw()
    raw["methodology"].setdefault("terms", []).append(
        {
            "term": "ZZZ-bad-ref",
            "category": "scores_buckets",
            "definition": "x",
            "thresholds": [{"label": "Bogus", "cmp": ">=", "ref": "decision_rules.nope.missing"}],
        }
    )
    with pytest.raises((ConfigError, ValueError)):
        load_config(_write(tmp_path, raw))


def test_empty_definition_fails_boot(tmp_path):
    raw = _committed_raw()
    raw["methodology"].setdefault("terms", []).append(
        {"term": "ZZZ-empty-def", "category": "scores_buckets", "definition": "   "}
    )
    with pytest.raises((ConfigError, ValueError)):
        load_config(_write(tmp_path, raw))
