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
        # J-01 (goal-market-compass iter-1): a SIBLING top-level section, deliberately NOT nested inside
        # `universe_selection` — that section is suppressed by the J-22 honest-universe gate until the
        # offline screen record exists, and the sector basis must stay readable regardless (see
        # `_sector_basis`). Same producer, same endpoint, one home — never recomputed elsewhere.
        payload["sector_basis"] = _sector_basis(config)
    if catalog.compass_selection is not None:
        # J-04 (goal-market-compass iter-2): same sibling-key reasoning as `sector_basis` above — this
        # disclosure makes no universe-screen claim, so the J-22 gate must not hide it either.
        payload["compass_selection"] = _compass_selection(config)
    if catalog.categories:
        payload["glossary"] = _glossary(config)
    return payload


def _sector_basis(config: Config) -> str:
    """The two-source stock-sector-label disclosure (J-01, goal-market-compass iter-1): the curated
    `config.stock_sectors` mapping first, the committed `universe_pool.csv` sector column second, plus
    the current-only limitation (no point-in-time sector history; B-114 stays open). Plain config prose
    resolved live, exactly like `membership_rule` — never re-typed in the engine or the frontend.

    Served as its OWN top-level key rather than inside `universe_selection` because that section is
    suppressed by the J-22 honest-universe gate (`app.api.methodology`) until `data/seed/universe.json`
    exists. That gate suppresses the claim *the universe is a reproducible screen result*; this prose
    makes no such claim — it describes how a descriptive sector LABEL is resolved from two sources that
    both exist today (the curated config map and the committed candidate-pool CSV) — so gating it would
    hide an honest disclosure for an unrelated reason."""
    return config.methodology.universe_selection.sector_basis


def _compass_selection(config: Config) -> dict:
    """The J-04 (goal-market-compass iter-2) "Next-session focus" disclosure: the selection-rule prose
    + its live `compass.selection.*` thresholds, resolved via the SAME `ref` mechanism as
    `_universe_selection` (matching-config keystone — never re-typed). Served as its own top-level
    sibling key for the same reason `_sector_basis` is a sibling (see its docstring)."""
    basis = config.methodology.compass_selection
    return {
        "text": basis.text,
        "thresholds": [_threshold_row(threshold, config) for threshold in basis.thresholds],
    }


# The category key the Setups & Patterns glossary rows are DERIVED into (J-47). The category itself is
# declared in `config.methodology.categories` with this key; build_catalog fills its `terms` from the
# existing `methodology.entries` so a setup/pattern is explained in exactly one place (never re-described).
SETUPS_PATTERNS_CATEGORY_KEY = "setups_patterns"


def _glossary(config: Config) -> dict:
    """Assemble the J-47 terminology glossary from `config.methodology.categories` + `.terms`, grouped by
    category in catalog (declared) order. The Setups & Patterns category's terms are DERIVED from
    `methodology.entries` (each entry projected as a glossary row referencing the full entry — single
    source of truth; never a re-authored second copy). Every authored term's threshold `ref` is resolved
    LIVE (the matching-config keystone — never a re-typed number)."""
    catalog = config.methodology

    # authored terms bucketed by their category key (catalog order preserved within a category)
    authored: dict[str, list[dict]] = {}
    for term in catalog.terms:
        row: dict = {
            "term": term.term,
            "category": term.category,
            "definition": term.definition,
        }
        if term.where is not None:
            row["where"] = term.where
        if term.thresholds:
            row["thresholds"] = [_threshold_row(threshold, config) for threshold in term.thresholds]
        authored.setdefault(term.category, []).append(row)

    # the Setups & Patterns rows, derived from the existing entries (single-sourced — references the entry)
    derived_setups_patterns = [
        {
            "term": entry.name,
            "category": SETUPS_PATTERNS_CATEGORY_KEY,
            "definition": entry.meaning,
            "entry_key": entry.key,  # links the glossary row to the full /methodology catalog entry
            "kind": entry.kind,
        }
        for entry in catalog.entries
    ]

    categories = []
    for category in catalog.categories:
        terms = list(authored.get(category.key, []))
        if category.key == SETUPS_PATTERNS_CATEGORY_KEY:
            # derived rows lead the category; any authored terms in this category would have been rejected
            # at boot if they collided with an entry, so here they can only be non-colliding extras.
            terms = derived_setups_patterns + terms
        categories.append({"key": category.key, "label": category.label, "terms": terms})

    return {"categories": categories}


def _universe_selection(config: Config) -> dict:
    """The Universe Selection section (J-22 / J-93): the membership-rule prose + the screen thresholds
    resolved LIVE from config (never re-typed — the matching-config keystone). The universe is now a
    TWO-LAYER screen, both documented here from config refs (no magic number):

      (1) the CANDIDATE-POOL screen — the index-membership union gated by market-cap / ADV / price
          (`universe.filters.*`) — which builds `config.universe.symbols` (the offline `expand` screen);
      (2) the PER-AS-OF-DATE membership resolver (J-93) — that pool screened, FROM BARS <= D ONLY, on
          price + ADV + >= `indicators.min_history_bars` trailing bars (the market-cap criterion is
          DROPPED per-date — a current-only scalar has no point-in-time series; applying it per
          historical date would be lookahead/fabrication).

    `resolved_size` is the CANDIDATE-UNIVERSE size (`len(config.universe.symbols)` — the rule's static
    pool, NOT date-scoped, since methodology describes the rule, not a snapshot); `candidate_pool_size`
    is the same read for clarity. The as-of-DEPENDENT resolved member count (members-resolved-at-D) is
    served on `GET /api/data` (`universe_count` / `universe_diagnostic`) — pointed to via `per_date_note`.
    The API/frontend reads this verbatim; neither recomputes membership.

    NOTE (J-01): the two-source sector-basis disclosure is deliberately NOT part of this section — it is
    served as the sibling top-level `sector_basis` key by `build_catalog`, because this whole section is
    suppressed by the J-22 honest-universe gate until the offline screen record exists, and the sector
    basis makes no screen claim (see `_sector_basis` below)."""
    section = config.methodology.universe_selection
    candidate_size = len(config.universe.symbols)
    return {
        "membership_rule": section.membership_rule,
        "thresholds": [_threshold_row(threshold, config) for threshold in section.thresholds],
        # the candidate-universe (static pool) size — read once, here and on /api/data
        # (`candidate_universe_count`), so the two surfaces never drift (single source, no recompute).
        "resolved_size": candidate_size,
        "candidate_pool_size": candidate_size,
        # J-93: the per-date rule + where its as-of-dependent resolved count is served (the market-cap
        # criterion is dropped per-date — documented, never silently asserted at a historical date).
        "per_date_rule": (
            f"As of any date D the scored membership is this candidate pool screened — from bars dated "
            f"on or before D only — on at least {config.indicators.min_history_bars} trailing bars of "
            f"history (the warm-up gate), data recency (a name whose last bar is more than "
            f"{config.universe.filters.max_staleness_days} calendar days before D is excluded as a stale "
            f"series — a name whose data ends mid-history exits membership cleanly and never feeds a "
            f"misaligned relative-strength window), price ≥ the minimum share price, and average daily "
            f"dollar volume ≥ the minimum. The market-cap filter screens the candidate pool, not the "
            f"per-date membership (market cap has no point-in-time series). The resolved count for a "
            f"date is shown on Data Manager (universe_count)."
        ),
        # iter-18 (J-12): the staleness threshold surfaced beside the min-history gate (config read).
        "per_date_max_staleness_days": config.universe.filters.max_staleness_days,
        "per_date_min_history_bars": config.indicators.min_history_bars,
    }
