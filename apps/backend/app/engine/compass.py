"""app.engine.compass — the deterministic narrative + candidate-selection trace + manifest assembly
(goal-market-compass iter-2, J-03/J-04, CONTENT block only).

Three producers, one assembler:

  - `build_narrative(...)` — deterministic template sentences (state / direction / breadth /
    focus-count, plus a no-comparison / NA-velocity / retrospective-stamp variant where it applies),
    each carrying `{template_id, text, facts}`. Word maps and thresholds live only in
    `compass.vocabulary.*` / `compass.delta.*` — never a literal here (see test_no_magic_numbers.py).
  - `evaluate_selection(...)` — the transparent candidate-selection rule (J-04) over stored
    `ScannerResult` rows: candidates with reasons/cautions/checklist/what-would-change/invalidation;
    why-not entries for near-miss and cap-excluded non-candidates; a disposition tally that partitions
    member count minus candidate count exactly; an explicit `candidates_empty_reason` when nothing
    clears the floor. No new blended/composite score is introduced anywhere (AG-11) — every value shown
    is one of the three existing per-stock scores/buckets plus a config word map.
  - `build_manifest_payload(...)` — assembles `session_delta` + `narrative` + `selection` into one
    content document and computes `content_hash` (sha256 over the sorted-key JSON of the content block
    only).

`get_or_create_manifest` / `manifest_row_payload` are the storage half: compute once per `as_of`
(create-once), persist immutably (AG-12 — never updated or deleted), serve from storage on every later
hit (TC-1 — zero producer calls on a warm read).

Reads ONLY column-projected `ScannerResult` selects for the universe-wide sweep, plus a SMALL, bounded
`record_json` read for the (<= `max_candidates`) actual candidates only — never a full-universe
`record_json` sweep (AG-8). Never reads `forward_returns` or any bar dated after the as-of — it reads
already-stored, already-computed run rows only (AG-5).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine import market_phase
from app.engine.session_delta import compute_delta, find_previous_run
from app.engine.setups import RISK_OFF_LABEL
from app.engine.snapshot_serving import dashboard_payload
from app.models import NextSessionManifest, ScannerResult, ScannerRun

# --- narrative -------------------------------------------------------------------------------

_DIRECTION_TEMPLATE = "direction"
_DIRECTION_NO_PRIOR_RUN_TEMPLATE = "direction_no_prior_run"
_DIRECTION_NA_VELOCITY_TEMPLATE = "direction_na_velocity"


def _pbear_word(p_bear: Optional[float], cfg: Config) -> Optional[str]:
    """The filtered P(bear) -> narrative state word, via the highest `compass.delta.pbear_bands` edge
    whose `min` the value clears (ascending-min band, same convention as `market_phase.phase_edges`)."""
    if p_bear is None:
        return None
    word: Optional[str] = None
    for band in cfg.compass.delta.pbear_bands:
        if p_bear >= band.min:
            word = band.label
    return word


def _state_sentence(dashboard: dict, phase_payload: dict, cfg: Config) -> dict:
    regime_label = dashboard["regime"]["label"]
    regime_score = dashboard["regime"]["score"]
    facts = [
        {"name": "regime_label", "value": regime_label},
        {"name": "regime_score", "value": regime_score},
    ]
    if phase_payload.get("available"):
        severity = phase_payload.get("severity")
        phase_label = phase_payload.get("phase")
        level_word = _pbear_word(phase_payload.get("p_bear"), cfg)
        facts.append({"name": "market_phase", "value": phase_label})
        facts.append({"name": "severity", "value": severity})
        if level_word is not None and severity is not None:
            text = (
                f"Market regime is {regime_label} ({regime_score:.1f}/100); market phase is "
                f"{phase_label} with {level_word} conditions (severity {severity:.1f}/100)."
            )
        else:
            text = f"Market regime is {regime_label} ({regime_score:.1f}/100); market phase is {phase_label}."
    else:
        text = (
            f"Market regime is {regime_label} ({regime_score:.1f}/100); market phase is not yet "
            "available for this session (insufficient trailing history)."
        )
    return {"template_id": "state", "text": text, "facts": facts}


def _direction_word(current_run: ScannerRun, previous_run: ScannerRun, cfg: Config) -> tuple[str, float]:
    delta = current_run.regime_score - previous_run.regime_score
    if abs(delta) < cfg.compass.delta.velocity_flat_band:
        return cfg.compass.vocabulary.direction_words["flat"], delta
    return cfg.compass.vocabulary.direction_words["up" if delta > 0 else "down"], delta


def _direction_sentence(
    current_run: ScannerRun, previous_run: Optional[ScannerRun], phase_payload: dict, cfg: Config
) -> dict:
    if previous_run is None:
        return {
            "template_id": _DIRECTION_NO_PRIOR_RUN_TEMPLATE,
            "text": "This is the earliest stored session — no prior-session comparison is available.",
            "facts": [],
        }
    if not phase_payload.get("available"):
        return {
            "template_id": _DIRECTION_NA_VELOCITY_TEMPLATE,
            "text": "Not enough trailing history yet to read a session-over-session direction.",
            "facts": [],
        }
    word, delta = _direction_word(current_run, previous_run, cfg)
    return {
        "template_id": _DIRECTION_TEMPLATE,
        "text": f"Conditions are {word} since the prior session ({delta:+.1f} regime-score points).",
        "facts": [
            {"name": "regime_score_delta", "value": delta},
            {"name": "direction_word", "value": word},
        ],
    }


def _breadth_sentence(current_run: ScannerRun, cfg: Config) -> dict:
    b50 = current_run.breadth_above_50dma
    b200 = current_run.breadth_above_200dma
    facts = [
        {"name": "breadth_above_50dma", "value": b50},
        {"name": "breadth_above_200dma", "value": b200},
    ]
    if b50 is None and b200 is None:
        text = "Breadth data is not available for this session."
    else:
        parts = []
        if b50 is not None:
            parts.append(f"{b50:.1f}% of the universe above its 50-day average")
        if b200 is not None:
            parts.append(f"{b200:.1f}% above its 200-day average")
        text = f"Universe breadth: {', '.join(parts)}."
    return {"template_id": "breadth", "text": text, "facts": facts}


def _focus_count_sentence(selection: dict, cfg: Config) -> dict:
    count = len(selection["candidates"])
    if count == 0:
        reason = selection.get("candidates_empty_reason") or "no member cleared the selection rule"
        text = f"No names are worth monitoring next session ({reason})"
    else:
        plural = "s" if count != 1 else ""
        text = f"{count} name{plural} worth monitoring next session."
    return {"template_id": "focus_count", "text": text, "facts": [{"name": "candidate_count", "value": count}]}


def _retrospective_sentence() -> dict:
    return {
        "template_id": "retrospective_stamp",
        "text": (
            "This is a retrospective view, reconstructed under the CURRENT selection rule and config — "
            "not necessarily what would have rendered live on this date."
        ),
        "facts": [],
    }


def _is_retrospective(session: Session, current_run: ScannerRun) -> bool:
    """True when a LATER stored run already exists at the moment this manifest is generated — the
    generation-time signal this narrative's retrospective stamp discloses. (Distinct from, and simpler
    than, the future `mode`/`generation.*` freeze fields — J-05/J-06, OUT OF SCOPE this iteration.)"""
    later = session.exec(select(ScannerRun.id).where(ScannerRun.asof_date > current_run.asof_date)).first()
    return later is not None


def _assert_no_banned_language(sentences: list[dict], cfg: Config) -> None:
    """TC-11 as a runtime guarantee, not only an offline test scan: no rendered sentence may contain a
    committed banned term (imperative trade verbs, forecast terms, causal-attribution phrases — AG-2)."""
    banned = cfg.compass.vocabulary.banned_terms
    for sentence in sentences:
        lowered = sentence["text"].lower()
        hits = [term for term in banned if term.lower() in lowered]
        if hits:
            raise ValueError(f"narrative sentence {sentence['template_id']!r} contains banned language: {hits}")


def build_narrative(
    session: Session,
    current_run: ScannerRun,
    previous_run: Optional[ScannerRun],
    selection: dict,
    config: Optional[Config] = None,
) -> dict:
    """The `narrative` CONTENT block (goal-market-compass iter-2, J-03). Every sentence is a
    deterministic template over stored values — no free text, no LLM, no fabricated cause."""
    cfg = config or get_config()
    dashboard = dashboard_payload(current_run)
    phase_payload = market_phase.market_phase_cached(session, current_run.asof_date, cfg)

    sentences = [
        _state_sentence(dashboard, phase_payload, cfg),
        _direction_sentence(current_run, previous_run, phase_payload, cfg),
        _breadth_sentence(current_run, cfg),
        _focus_count_sentence(selection, cfg),
    ]
    if _is_retrospective(session, current_run):
        sentences.append(_retrospective_sentence())

    _assert_no_banned_language(sentences, cfg)
    return {"sentences": sentences}


# --- selection (J-04) -------------------------------------------------------------------------

_QUALIFIER_CHECKS = ("leadership_min_score", "entry_min_score", "risk_max_score")


def _record_json_by_ticker(session: Session, run: ScannerRun, tickers: list[str]) -> dict[str, dict]:
    """A targeted, bounded `record_json` read for the actual candidates only (`len(tickers) <=
    max_candidates`) — never a full-universe sweep (AG-8). Deliberately self-contained (does not reuse
    `snapshot_serving.filtered_stock_rows`, which additionally attaches `forward_returns` — this producer
    stays grep-clean of any post-as-of read, TC-23)."""
    if not tickers:
        return {}
    rows = session.exec(
        select(ScannerResult.ticker, ScannerResult.record_json).where(
            ScannerResult.run_id == run.id, ScannerResult.ticker.in_(tickers)
        )
    ).all()
    return {ticker: json.loads(record_json) for ticker, record_json in rows}


def _qualifier_checks(row: dict, cfg: Config) -> list[dict]:
    sel = cfg.compass.selection
    return [
        {
            "condition": "leadership_min_score",
            "threshold": sel.leadership_min_score,
            "actual": row["leadership_score"],
            "passed": row["leadership_score"] >= sel.leadership_min_score,
        },
        {
            "condition": "entry_min_score",
            "threshold": sel.entry_min_score,
            "actual": row["entry_quality_score"],
            "passed": row["entry_quality_score"] >= sel.entry_min_score,
        },
        {
            "condition": "risk_max_score",
            "threshold": sel.risk_max_score,
            "actual": row["risk_score"],
            "passed": row["risk_score"] <= sel.risk_max_score,
        },
    ]


def _candidate_payload(row: dict, checks: list[dict], detail: Optional[dict], run: ScannerRun, cfg: Config) -> dict:
    vocab = cfg.compass.vocabulary
    checklist = [
        {
            "condition": check["condition"],
            "threshold": check["threshold"],
            "actual": check["actual"],
            "verdict": "Pass" if check["passed"] else "Miss",
        }
        for check in checks
    ]
    what_would_change = [
        {
            "condition": check["condition"],
            "threshold": check["threshold"],
            "actual": check["actual"],
            "met": check["passed"],
        }
        for check in checks
    ]
    sel = cfg.compass.selection
    reasons = [
        f"Leadership score {row['leadership_score']:.1f} clears the {sel.leadership_min_score:.1f} floor "
        f"({vocab.leadership_words[row['leadership_bucket']]}).",
        f"Entry Quality score {row['entry_quality_score']:.1f} clears the {sel.entry_min_score:.1f} "
        f"qualifier ({vocab.entry_words[row['entry_quality_bucket']]}).",
        f"Risk score {row['risk_score']:.1f} clears the {sel.risk_max_score:.1f} ceiling "
        f"({vocab.risk_words[row['risk_bucket']]}).",
    ]

    cautions = []
    invalidation_note = "No stored invalidation note for this row."
    risk_budget = (detail or {}).get("risk_budget") or {}
    atr = risk_budget.get("atr_pct") or {}
    if atr.get("value") is not None:
        pct = atr.get("percentile")
        pct_text = f"p{pct * 100:.0f} of universe" if pct is not None else "percentile NA"
        cautions.append(
            f"ATR_RISK_BUDGET: ATR is {atr['value']:.2f}% of price ({pct_text}) — sized risk accordingly."
        )
    else:
        cautions.append("ATR_RISK_BUDGET: risk-budget data not available for this row — reported NA, never fabricated.")
    inv = (detail or {}).get("invalidation") or {}
    if inv.get("note"):
        invalidation_note = inv["note"]
    if run.regime_label == RISK_OFF_LABEL:
        cautions.append(
            "REGIME_RISK_OFF: the market regime is Risk-off as of this date — every candidate here is "
            "context, not a signal to act."
        )

    return {
        "ticker": row["ticker"],
        "leadership_word": vocab.leadership_words[row["leadership_bucket"]],
        "leadership_score": row["leadership_score"],
        "entry_word": vocab.entry_words[row["entry_quality_bucket"]],
        "entry_quality_score": row["entry_quality_score"],
        "risk_word": vocab.risk_words[row["risk_bucket"]],
        "risk_score": row["risk_score"],
        "reasons": reasons,
        "cautions": cautions,
        "checklist": checklist,
        "what_would_change": what_would_change,
        "invalidation": invalidation_note,
    }


def evaluate_selection(session: Session, run: ScannerRun, config: Optional[Config] = None) -> dict:
    """The `selection` CONTENT block (goal-market-compass iter-2, J-04). See the module docstring for
    the anti-goal posture (AG-8 bounded reads, AG-11 no new composite score)."""
    cfg = config or get_config()
    sel = cfg.compass.selection

    raw_rows = session.exec(
        select(
            ScannerResult.ticker,
            ScannerResult.leadership_score,
            ScannerResult.leadership_bucket,
            ScannerResult.entry_quality_score,
            ScannerResult.entry_quality_bucket,
            ScannerResult.risk_score,
            ScannerResult.risk_bucket,
        )
        .where(ScannerResult.run_id == run.id)
        .order_by(ScannerResult.ticker)
    ).all()
    member_count = len(raw_rows)

    qualifying: list[tuple[dict, list[dict]]] = []
    non_qualifying: list[tuple[dict, list[dict]]] = []
    for ticker, l_score, l_bucket, e_score, e_bucket, r_score, r_bucket in raw_rows:
        row = {
            "ticker": ticker,
            "leadership_score": l_score,
            "leadership_bucket": l_bucket,
            "entry_quality_score": e_score,
            "entry_quality_bucket": e_bucket,
            "risk_score": r_score,
            "risk_bucket": r_bucket,
        }
        checks = _qualifier_checks(row, cfg)
        if all(check["passed"] for check in checks):
            qualifying.append((row, checks))
        else:
            failed = [
                {
                    "condition": check["condition"],
                    "threshold": check["threshold"],
                    "actual": check["actual"],
                    "distance": abs(check["actual"] - check["threshold"]),
                }
                for check in checks
                if not check["passed"]
            ]
            non_qualifying.append((row, failed))

    qualifying.sort(key=lambda pair: (-pair[0]["leadership_score"], pair[0]["ticker"]))
    candidate_pairs = qualifying[: sel.max_candidates]
    excluded_by_cap_pairs = qualifying[sel.max_candidates :]

    candidate_tickers = [row["ticker"] for row, _checks in candidate_pairs]
    detail_by_ticker = _record_json_by_ticker(session, run, candidate_tickers)
    candidates = [
        _candidate_payload(row, checks, detail_by_ticker.get(row["ticker"]), run, cfg)
        for row, checks in candidate_pairs
    ]

    why_not_pool: list[tuple[dict, list[dict]]] = [
        (row, failed) for row, failed in non_qualifying if row["leadership_score"] >= sel.why_not_floor
    ]
    why_not_pool.extend((row, []) for row, _checks in excluded_by_cap_pairs)  # passed everything, cut by cap
    why_not_pool.sort(key=lambda pair: (-pair[0]["leadership_score"], pair[0]["ticker"]))
    why_not = [
        {"ticker": row["ticker"], "failed_conditions": failed}
        for row, failed in why_not_pool[: sel.why_not_cap]
    ]

    candidates_empty_reason = None
    if not candidates:
        candidates_empty_reason = (
            f"No stored member cleared the selection rule (Leadership >= {sel.leadership_min_score:.1f}, "
            f"Entry Quality >= {sel.entry_min_score:.1f}, Risk <= {sel.risk_max_score:.1f}) for this as-of."
        )

    return {
        "candidates": candidates,
        "why_not": why_not,
        "disposition_tally": {
            "below_selection_floor": len(non_qualifying),
            "excluded_by_cap": len(excluded_by_cap_pairs),
        },
        "candidates_empty_reason": candidates_empty_reason,
    }


# --- manifest assembly + storage ----------------------------------------------------------------


def build_manifest_payload(
    session: Session,
    current_run: ScannerRun,
    previous_run: Optional[ScannerRun],
    config: Optional[Config] = None,
) -> dict:
    """Assemble the three CONTENT blocks + `content_hash` (sha256 hex over the sorted-key JSON of the
    content block only — never re-derived at serve time; see `manifest_row_payload`)."""
    cfg = config or get_config()
    delta = compute_delta(session, current_run, previous_run, cfg)
    selection = evaluate_selection(session, current_run, cfg)
    narrative = build_narrative(session, current_run, previous_run, selection, cfg)
    content = {"session_delta": delta, "narrative": narrative, "selection": selection}
    canonical = json.dumps(content, sort_keys=True, default=str)
    content_hash = hashlib.sha256(canonical.encode()).hexdigest()
    return {**content, "content_hash": content_hash}


def get_or_create_manifest(
    session: Session, current_run: ScannerRun, config: Optional[Config] = None
) -> NextSessionManifest:
    """Serve the stored manifest row for `current_run.asof_date`, computing + persisting it ONCE if
    absent (create-once-on-GET / finalize-hook write path — TC-1: zero producer calls on a warm hit).
    Concurrency-safe the SAME way `scanner.persist_run_payload` is: a losing concurrent INSERT rolls
    back and returns the already-committed row (never raises, never duplicates, never overwrites —
    AG-12: a stored row is never mutated or deleted by any later call)."""
    existing = session.exec(
        select(NextSessionManifest).where(NextSessionManifest.as_of == current_run.asof_date)
    ).first()
    if existing is not None:
        return existing

    cfg = config or get_config()
    previous_run = find_previous_run(session, current_run)
    payload = build_manifest_payload(session, current_run, previous_run, cfg)

    row = NextSessionManifest(
        as_of=current_run.asof_date,
        source_run_id=current_run.id,
        session_delta_json=json.dumps(payload["session_delta"]),
        narrative_json=json.dumps(payload["narrative"]),
        selection_json=json.dumps(payload["selection"]),
        content_hash=payload["content_hash"],
        created_at=datetime.now(timezone.utc),
    )
    session.add(row)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        existing = session.exec(
            select(NextSessionManifest).where(NextSessionManifest.as_of == current_run.asof_date)
        ).first()
        if existing is not None:
            return existing
        raise
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.exec(
            select(NextSessionManifest).where(NextSessionManifest.as_of == current_run.asof_date)
        ).first()
        if existing is not None:
            return existing
        raise
    session.refresh(row)
    return row


def manifest_row_payload(row: NextSessionManifest) -> dict:
    """Re-shape a STORED `NextSessionManifest` row into the served `GET /api/compass` dict — a read,
    never a recompute (single source of truth)."""
    return {
        "as_of": row.as_of.isoformat(),
        "session_delta": json.loads(row.session_delta_json),
        "narrative": json.loads(row.narrative_json),
        "selection": json.loads(row.selection_json),
        "content_hash": row.content_hash,
    }
