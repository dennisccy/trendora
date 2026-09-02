"""app.engine.session_delta — session-over-session change detection (goal-market-compass iter-2, J-02).

`compute_delta(session, current_run, previous_run, config)` builds the `session_delta` CONTENT block of
the next-session manifest (see docs/phases/goal-market-compass-iter-2.md's Data-contract addition for
the exact served shape): the ordered list of meaningful market -> breadth -> sector -> theme -> stock
changes between `current_run` and the immediately preceding stored run, each gated by its kind's
`compass.delta.*` threshold, plus the suppressed (below-threshold) entries and an explicit no-prior-run
state for the earliest stored run.

Reads ONLY column-projected `ScannerResult` / `SectorScoreRow` / `ThemeScoreRow` selects — never a full
`record_json` sweep (AG-8); `ScannerRun` itself carries no such blob so its typed columns are read
directly. Compares only two ALREADY-STORED, already-computed runs — there is no `forward_returns` or
post-as-of bar for this module to read even by accident (AG-5).

`sector_rank_pairs(session, current_run, previous_run, config)` / `theme_rank_pairs(...)`
(goal-market-compass iter-36, J-13): the full, uncapped, signed-`delta` sector/theme rank-pair
computation `_sector_changes`/`_theme_changes` (feeding `session_delta.changes`, still `top_k`-capped,
unchanged behavior) and `app.engine.compass.build_rotation` (`session_delta.rotation`, independently
`rotation_top_k`-capped, both directions) both build from — one query pair per manifest build, two
capped consumers. Sector/theme-kind `changes[]` entries additionally carry this signed `delta`
(direction-word wording is compass.py's concern — it owns `compass.vocabulary`, this module does not).

`_stock_changes` (goal-market-compass iter-40, J-15): classifies the FULL stock-kind bucket-crossing
list against `stock_score_min_change` BEFORE applying the `max_stock_items` display bound, so every
evaluated crossing lands in exactly one of shown / suppressed / residual; `compute_delta` serves the
partition as `session_delta.stock_accounting = {evaluated_count, shown_count, suppressed_count,
residual_count}` (`evaluated_count == shown_count + suppressed_count + residual_count`) -- mirroring how
J-13 (iter-36) closed the same hole for the sector/theme kinds. `max_stock_items` keeps its existing
value and stays the DISPLAY cap only; new-to-universe members keep their pre-existing unconditional
display priority and stay outside this accounting (they are never subject to the threshold).
"""
from __future__ import annotations

from typing import Optional

from sqlmodel import Session, select

from app.config import Config, get_config
from app.models import ScannerResult, ScannerRun, SectorScoreRow, ThemeScoreRow

KIND_MARKET = "market"
KIND_BREADTH = "breadth"
KIND_SECTOR = "sector"
KIND_THEME = "theme"
KIND_STOCK = "stock"


def find_previous_run(session: Session, current_run: ScannerRun) -> Optional[ScannerRun]:
    """The immediately preceding STORED run by `asof_date` (never by `id` / insertion order — TC-2)."""
    return session.exec(
        select(ScannerRun)
        .where(ScannerRun.asof_date < current_run.asof_date)
        .order_by(ScannerRun.asof_date.desc())
    ).first()


def _drill_href(kind: str, as_of_iso: str, ticker: Optional[str] = None) -> str:
    """The change entry's drill-through link, carrying the current `?asof` (TC-3)."""
    if kind == KIND_STOCK and ticker:
        return f"/stocks/{ticker}?asof={as_of_iso}"
    if kind == KIND_SECTOR:
        return f"/sectors?asof={as_of_iso}"
    if kind == KIND_THEME:
        return f"/themes?asof={as_of_iso}"
    return f"/?asof={as_of_iso}"


def _entry(
    kind: str, label: str, frm, to, magnitude: float, threshold: float, drill_href: str,
    delta: Optional[int] = None,
) -> dict:
    entry = {
        "kind": kind,
        "label": label,
        "from": frm,
        "to": to,
        "magnitude": magnitude,
        "threshold": threshold,
        "drill_href": drill_href,
    }
    # goal-market-compass iter-36 (J-13): a SIGNED rank delta rides sector/theme-kind entries only (never
    # market/breadth/stock) -- additive, so the older entry shape is unchanged for every other kind.
    if delta is not None:
        entry["delta"] = delta
    return entry


def _classify(pairs: list[tuple[dict, float]], threshold: float) -> tuple[list[dict], list[dict]]:
    """Split (entry, magnitude) pairs into (changes, suppressed) by one kind's threshold — a magnitude
    AT OR ABOVE the threshold is a change (TC-3); below it is suppressed (TC-4)."""
    changes: list[dict] = []
    suppressed: list[dict] = []
    for entry, magnitude in pairs:
        if magnitude >= threshold:
            changes.append(entry)
        else:
            suppressed.append({"kind": entry["kind"], "magnitude": magnitude, "threshold": threshold})
    return changes, suppressed


def _market_changes(
    current: ScannerRun, previous: ScannerRun, as_of_iso: str, cfg: Config
) -> tuple[list[dict], list[dict]]:
    threshold = cfg.compass.delta.market_score_min_change
    magnitude = abs(current.regime_score - previous.regime_score)
    entry = _entry(
        KIND_MARKET, "Market regime score", previous.regime_score, current.regime_score,
        magnitude, threshold, _drill_href(KIND_MARKET, as_of_iso),
    )
    return _classify([(entry, magnitude)], threshold)


def _breadth_changes(
    current: ScannerRun, previous: ScannerRun, as_of_iso: str, cfg: Config
) -> tuple[list[dict], list[dict]]:
    threshold = cfg.compass.delta.breadth_min_change_pts
    pairs: list[tuple[dict, float]] = []
    for label, cur_val, prev_val in (
        ("Breadth above 50-DMA", current.breadth_above_50dma, previous.breadth_above_50dma),
        ("Breadth above 200-DMA", current.breadth_above_200dma, previous.breadth_above_200dma),
    ):
        if cur_val is None or prev_val is None:
            continue  # honest NA on either side (insufficient history) — never a fabricated delta
        magnitude = abs(cur_val - prev_val)
        entry = _entry(KIND_BREADTH, label, prev_val, cur_val, magnitude, threshold, _drill_href(KIND_BREADTH, as_of_iso))
        pairs.append((entry, magnitude))
    return _classify(pairs, threshold)


def sector_rank_pairs(
    session: Session, current: ScannerRun, previous: ScannerRun, config: Optional[Config] = None
) -> list[tuple[dict, float]]:
    """ALL comparable sector/industry rank pairs between `current` and `previous` (goal-market-compass
    iter-36, J-13) — BEFORE any `rank_move_min` gate or `top_k`/`rotation_top_k` cap is applied, most-
    moved-first (stable sort — ties keep the deterministic ticker-ordered input). Each entry carries a
    SIGNED `delta` (`cur_rank - prev_rank`; a FALLING rank number is an IMPROVING position) alongside the
    existing `magnitude`/`from`/`to`/`drill_href` shape. This is the ONE pair-building computation both
    `_sector_changes` (feeding the existing `session_delta.changes`/`suppressed`, `top_k`-capped) and
    `app.engine.compass.build_rotation` (`rotation_top_k`-capped, both directions) read — callers that
    already hold these pairs should pass them straight into `compute_delta` so the DB is queried only
    once per manifest build (see `compass.build_manifest_payload`)."""
    cfg = config or get_config()
    threshold = cfg.compass.delta.rank_move_min
    as_of_iso = current.asof_date.isoformat()
    cur_rows = session.exec(
        select(SectorScoreRow.ticker, SectorScoreRow.name, SectorScoreRow.rank)
        .where(SectorScoreRow.run_id == current.id)
        .order_by(SectorScoreRow.ticker)
    ).all()
    prev_by_ticker = {
        ticker: rank
        for ticker, _name, rank in session.exec(
            select(SectorScoreRow.ticker, SectorScoreRow.name, SectorScoreRow.rank)
            .where(SectorScoreRow.run_id == previous.id)
        ).all()
    }
    pairs: list[tuple[dict, float]] = []
    for ticker, name, cur_rank in cur_rows:
        prev_rank = prev_by_ticker.get(ticker)
        if prev_rank is None:
            continue  # the sector/industry ETF universe is fixed (config.etfs.*) — never new-to-universe
        delta = cur_rank - prev_rank
        magnitude = float(abs(delta))
        entry = _entry(
            KIND_SECTOR, name, prev_rank, cur_rank, magnitude, threshold, _drill_href(KIND_SECTOR, as_of_iso),
            delta=delta,
        )
        pairs.append((entry, magnitude))
    # Most-moved first (stable sort — ties keep the deterministic ticker-ordered input); no cap here — the
    # two callers apply their OWN independent cap (top_k vs rotation_top_k).
    pairs.sort(key=lambda pair: pair[1], reverse=True)
    return pairs


def theme_rank_pairs(
    session: Session, current: ScannerRun, previous: ScannerRun, config: Optional[Config] = None
) -> list[tuple[dict, float]]:
    """Theme-kind counterpart of `sector_rank_pairs` (see its docstring for the full contract) — same
    signed-`delta` shape, same "one computation, multiple capped consumers" posture."""
    cfg = config or get_config()
    threshold = cfg.compass.delta.rank_move_min
    as_of_iso = current.asof_date.isoformat()
    cur_rows = session.exec(
        select(ThemeScoreRow.slug, ThemeScoreRow.name, ThemeScoreRow.rank)
        .where(ThemeScoreRow.run_id == current.id)
        .order_by(ThemeScoreRow.slug)
    ).all()
    prev_by_slug = {
        slug: rank
        for slug, _name, rank in session.exec(
            select(ThemeScoreRow.slug, ThemeScoreRow.name, ThemeScoreRow.rank)
            .where(ThemeScoreRow.run_id == previous.id)
        ).all()
    }
    pairs: list[tuple[dict, float]] = []
    for slug, name, cur_rank in cur_rows:
        prev_rank = prev_by_slug.get(slug)
        if prev_rank is None:
            continue  # the theme universe is fixed (config.themes) — never new-to-universe
        delta = cur_rank - prev_rank
        magnitude = float(abs(delta))
        entry = _entry(
            KIND_THEME, name, prev_rank, cur_rank, magnitude, threshold, _drill_href(KIND_THEME, as_of_iso),
            delta=delta,
        )
        pairs.append((entry, magnitude))
    pairs.sort(key=lambda pair: pair[1], reverse=True)
    return pairs


def _sector_changes(pairs: list[tuple[dict, float]], cfg: Config) -> tuple[list[dict], list[dict]]:
    """`session_delta.changes`/`suppressed`'s sector-kind slice — classify + cap at the EXISTING `top_k`
    (unchanged behavior/value). `pairs` is `sector_rank_pairs`'s full output — no second query."""
    changes, suppressed = _classify(pairs, cfg.compass.delta.rank_move_min)
    return changes[: cfg.compass.delta.top_k], suppressed


def _theme_changes(pairs: list[tuple[dict, float]], cfg: Config) -> tuple[list[dict], list[dict]]:
    """Theme-kind counterpart of `_sector_changes` (see its docstring)."""
    changes, suppressed = _classify(pairs, cfg.compass.delta.rank_move_min)
    return changes[: cfg.compass.delta.top_k], suppressed


def _stock_changes(
    session: Session, current: ScannerRun, previous: ScannerRun, as_of_iso: str, cfg: Config
) -> tuple[list[dict], list[dict], dict]:
    """Stock-kind entries are leadership-BUCKET crossings (TC-5) plus new-to-universe members (TC-7,
    reported unconditionally — never as a score change, always prioritized ahead of crossings and
    unconditionally exempt from the threshold, unchanged from before). `changes`/`suppressed` stay
    bounded to `max_stock_items` total DISPLAY entries (new members prioritized) so this producer never
    RANKS OR DISPLAYS the full ~500+ member universe in one pass (AG-8) — but every evaluated bucket
    crossing is still CLASSIFIED (goal-market-compass iter-40, J-15): the third return value,
    `stock_accounting`, accounts for the full `crossing_pairs` list computed below (no second
    materialization, no new query) so a crossing lands in exactly one of shown / suppressed / residual
    (`evaluated_count == shown_count + suppressed_count + residual_count`) — nothing above
    `stock_score_min_change` vanishes uncounted past the display cap the way it did before this change."""
    threshold = cfg.compass.delta.stock_score_min_change
    max_items = cfg.compass.delta.max_stock_items
    cur_rows = session.exec(
        select(ScannerResult.ticker, ScannerResult.leadership_score, ScannerResult.leadership_bucket)
        .where(ScannerResult.run_id == current.id)
        .order_by(ScannerResult.ticker)
    ).all()
    prev_by_ticker = {
        ticker: (score, bucket)
        for ticker, score, bucket in session.exec(
            select(ScannerResult.ticker, ScannerResult.leadership_score, ScannerResult.leadership_bucket)
            .where(ScannerResult.run_id == previous.id)
        ).all()
    }

    new_pairs: list[tuple[dict, float]] = []
    crossing_pairs: list[tuple[dict, float]] = []
    for ticker, cur_score, cur_bucket in cur_rows:
        prev = prev_by_ticker.get(ticker)
        if prev is None:
            entry = _entry(
                KIND_STOCK, f"{ticker} new to universe", "new", cur_bucket,
                cur_score, threshold, _drill_href(KIND_STOCK, as_of_iso, ticker),
            )
            new_pairs.append((entry, cur_score))
            continue
        prev_score, prev_bucket = prev
        if cur_bucket == prev_bucket:
            continue  # only a BUCKET crossing is a "stock" change (TC-5) — a same-bucket score wobble is not
        magnitude = abs(cur_score - prev_score)
        entry = _entry(
            KIND_STOCK, f"{ticker} leadership bucket", prev_bucket, cur_bucket,
            magnitude, threshold, _drill_href(KIND_STOCK, as_of_iso, ticker),
        )
        crossing_pairs.append((entry, magnitude))

    new_pairs.sort(key=lambda pair: pair[1], reverse=True)
    crossing_pairs.sort(key=lambda pair: pair[1], reverse=True)
    bounded_new = new_pairs[:max_items]
    available_slots = max(max_items - len(bounded_new), 0)

    # J-15: classify the FULL crossing_pairs list (unchanged threshold semantics) BEFORE applying the
    # max_stock_items display bound, so every evaluated crossing lands in exactly one bucket. `_classify`
    # preserves the magnitude-desc order already applied above, so `meets_threshold` is still most-moved
    # first -- the display bound then splits it into the shown head and the residual tail.
    meets_threshold, suppressed = _classify(crossing_pairs, threshold)
    shown_crossings = meets_threshold[:available_slots]
    residual_crossings = meets_threshold[available_slots:]

    changes = [entry for entry, _magnitude in bounded_new]
    changes.extend(shown_crossings)

    stock_accounting = {
        "evaluated_count": len(crossing_pairs),
        "shown_count": len(shown_crossings),
        "suppressed_count": len(suppressed),
        "residual_count": len(residual_crossings),
    }
    return changes, suppressed, stock_accounting


def compute_delta(
    session: Session,
    current_run: ScannerRun,
    previous_run: Optional[ScannerRun],
    config: Optional[Config] = None,
    sector_pairs: Optional[list[tuple[dict, float]]] = None,
    theme_pairs: Optional[list[tuple[dict, float]]] = None,
) -> dict:
    """The `session_delta` CONTENT block (goal-market-compass iter-2, J-02). `previous_run` is the
    immediately preceding STORED run (see `find_previous_run`), or `None` for the earliest stored run —
    the explicit no-prior-run state (TC-6): no deltas, no direction words, nothing fabricated.

    `sector_pairs`/`theme_pairs` (goal-market-compass iter-36, J-13): optional PRECOMPUTED
    `sector_rank_pairs`/`theme_rank_pairs` output. A caller that also needs the full pairs (e.g.
    `app.engine.compass.build_manifest_payload`, to build `session_delta.rotation`) computes them once
    and passes them in here so the DB is queried only once per manifest build; omitted, they are computed
    the same way internally (unchanged behavior for every other caller)."""
    cfg = config or get_config()
    if previous_run is None:
        return {"prior_as_of": None, "gap_days": None, "changes": [], "suppressed": [], "suppressed_count": 0}

    as_of_iso = current_run.asof_date.isoformat()
    if sector_pairs is None:
        sector_pairs = sector_rank_pairs(session, current_run, previous_run, cfg)
    if theme_pairs is None:
        theme_pairs = theme_rank_pairs(session, current_run, previous_run, cfg)

    changes: list[dict] = []
    suppressed: list[dict] = []
    for changes_part, suppressed_part in (
        _market_changes(current_run, previous_run, as_of_iso, cfg),
        _breadth_changes(current_run, previous_run, as_of_iso, cfg),
        _sector_changes(sector_pairs, cfg),
        _theme_changes(theme_pairs, cfg),
    ):
        changes.extend(changes_part)
        suppressed.extend(suppressed_part)

    # goal-market-compass iter-40 (J-15): `_stock_changes` also returns the stock-kind accounting object
    # -- computed in the SAME pass over `crossing_pairs` above, no second query, no second materialization.
    stock_changes, stock_suppressed, stock_accounting = _stock_changes(
        session, current_run, previous_run, as_of_iso, cfg
    )
    changes.extend(stock_changes)
    suppressed.extend(stock_suppressed)

    return {
        "prior_as_of": previous_run.asof_date.isoformat(),
        "gap_days": (current_run.asof_date - previous_run.asof_date).days,
        "changes": changes,
        "suppressed": suppressed,
        "suppressed_count": len(suppressed),
        "stock_accounting": stock_accounting,
    }
