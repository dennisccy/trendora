"""Setup & Pattern catalog assembler (iter-12, J-12) — Data Contract: app.engine.methodology.

`build_catalog(config)` assembles the served Methodology / Glossary payload from the single
config-backed `config.methodology` catalog. For each entry it resolves every threshold `ref` to its
LIVE value in the canonical config block it points at (so the displayed number ALWAYS matches the
engine — the matching-config keystone; never re-typed) and passes `text` rows through verbatim. It
asserts completeness — every canonical setup status (`app.engine.setups.ALL_STATUSES`) has a
`kind:"setup"` entry and every detected pattern (`config.patterns`) has a `kind:"pattern"` entry —
so the glossary can never silently drop a status/pattern.

It computes/stores NO score (it reads config, not the scoring engine) and contains NO threshold
literal (anti-goal: No magic numbers — every number is resolved from config). The SAME catalog feeds
the /methodology page, the /stocks badge tooltips, and the /stocks setup-filter vocabulary
(anti-goal: Setup & pattern vocabulary is config-driven in the UI too).
"""
from __future__ import annotations

from app.config import Config, MethodologyThreshold, resolve_ref
from app.engine.setups import ALL_STATUSES


def _threshold_row(threshold: MethodologyThreshold, config: Config) -> dict:
    """One served threshold row: a `text` rule verbatim, or a `ref` resolved to its LIVE config value
    (with the comparator/unit attached). Never re-types a number (matching-config keystone)."""
    if threshold.text is not None:
        return {"label": threshold.label, "text": threshold.text}
    row: dict = {"label": threshold.label}
    if threshold.cmp is not None:
        row["cmp"] = threshold.cmp
    row["value"] = resolve_ref(config, threshold.ref)
    if threshold.unit is not None:
        row["unit"] = threshold.unit
    return row


def build_catalog(config: Config) -> dict:
    """Assemble the served catalog from `config.methodology`, resolving each threshold `ref` to its
    live config value. Returns `{intro?, entries:[{key, kind, name, meaning, thresholds, example}]}`.
    Raises `ValueError` if a canonical setup status or detected pattern is undocumented (completeness —
    the glossary can never silently drop one)."""
    catalog = config.methodology
    entries = [
        {
            "key": entry.key,
            "kind": entry.kind,
            "name": entry.name,
            "meaning": entry.meaning,
            "thresholds": [_threshold_row(threshold, config) for threshold in entry.thresholds],
            "example": entry.example,
        }
        for entry in catalog.entries
    ]

    documented_setups = {entry.key for entry in catalog.entries if entry.kind == "setup"}
    documented_patterns = {entry.key for entry in catalog.entries if entry.kind == "pattern"}
    missing_setups = set(ALL_STATUSES) - documented_setups
    missing_patterns = set(config.patterns.model_dump()) - documented_patterns
    if missing_setups or missing_patterns:
        raise ValueError(
            "methodology catalog is incomplete — undocumented "
            f"setup statuses: {sorted(missing_setups)}; patterns: {sorted(missing_patterns)}"
        )

    payload: dict = {"entries": entries}
    if catalog.intro is not None:
        payload["intro"] = catalog.intro
    if catalog.universe_selection is not None:
        payload["universe_selection"] = _universe_selection(config)
    return payload


def _universe_selection(config: Config) -> dict:
    """The Universe Selection section (J-22): the membership-rule prose, the three screen thresholds
    resolved LIVE from `universe.filters` (never re-typed — the matching-config keystone), and the
    resolved member count read from the ONE canonical `config.universe.symbols` (a read, not a literal —
    no magic number). The API/frontend reads this verbatim; neither recomputes membership."""
    section = config.methodology.universe_selection
    return {
        "membership_rule": section.membership_rule,
        "thresholds": [_threshold_row(threshold, config) for threshold in section.thresholds],
        # the resolved universe is `config.universe.symbols` (the committed screen result) — read once,
        # here and on /api/data, so the two surfaces never drift (single source, no recompute).
        "resolved_size": len(config.universe.symbols),
    }
