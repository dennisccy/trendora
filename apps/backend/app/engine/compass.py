"""app.engine.compass — the deterministic narrative + candidate-selection trace + manifest assembly
(goal-market-compass iter-2, J-03/J-04, CONTENT block; iter-3, J-05/J-06, the freeze/integrity block;
iter-28, J-07, the `state_band` CONTENT block; iter-36, J-13, the `session_delta.rotation` CONTENT block;
iter-38, J-14, why-not entries carry their TRUE reason instead of a false universal "passed everything").

Five CONTENT producers, one assembler:

  - `build_narrative(...)` — deterministic template sentences (state / direction / breadth /
    focus-count, plus a no-comparison / NA-velocity / retrospective-stamp variant where it applies),
    each carrying `{template_id, text, facts}`. Word maps and thresholds live only in
    `compass.vocabulary.*` / `compass.delta.*` — never a literal here (see test_no_magic_numbers.py).
  - `evaluate_selection(...)` — the transparent candidate-selection rule (J-04) over stored
    `ScannerResult` rows: candidates with reasons/cautions/checklist/what-would-change/invalidation;
    why-not entries for near-miss and cap-excluded non-candidates, each carrying its OWN true `reason`
    (`excluded_by_cap` / `below_selection_floor`, reusing `selection_disposition`'s closed vocabulary)
    and `failed_conditions` (advisory misses carried through for cap-excluded rows too, never silently
    discarded — iter-38, J-14); a cap-excluded entry also carries its leadership `cap_rank` among
    qualifying rows and the configured `cap`. The DISPLAYED `why_not` list reserves
    `why_not_cap_per_reason` slots for EACH reason class (`_select_why_not_display`) so a large
    cap-excluded pool can never crowd out every near-miss name; `why_not_totals` discloses the two
    UNCAPPED per-reason pool counts. Also: a disposition tally that partitions member count minus
    candidate count exactly; an explicit `candidates_empty_reason` when nothing clears the floor.
    iter-3 (J-05/J-06) additionally serializes FULL frozen-context rows for every
    non-candidate member — `comparison_cohort` (the whole non-selected pool, each row carrying a
    closed-vocabulary `selection_disposition`) and `near_threshold_shadow` (the leadership-banded
    subset just below the floor) — reusing the SAME `non_qualifying` / `excluded_by_cap_pairs`
    partitions the disposition tally already computed. No new blended/composite score is introduced
    anywhere (AG-11) — every value shown is one of the three existing per-stock scores/buckets, a
    config word map, or a structural context field already computed by `scoring.score_stocks`.
  - `build_state_band(...)` — iter-28 (J-07): three direction words (regime, stress, breadth), each
    with a signed delta, comparing the current stored run against the immediately preceding one. Reuses
    the SAME `compass.vocabulary.direction_words` map as `build_narrative`'s own direction sentence
    (never a second word map) and the SAME `_flat_band_word` classifier `_direction_word` already used.
    No-prior-run or a missing per-word input renders that word's explicit null/no-comparison state —
    never a fabricated word (mirrors `session_delta`'s and `narrative`'s own no-prior-run handling).
  - `build_rotation(...)` — iter-36 (J-13): `session_delta.rotation.{sector,theme}` — two labelled,
    signed, both-directions (`gaining`/`losing`) sides per group kind, built from the SAME sector/theme
    rank pairs `session_delta.sector_rank_pairs`/`theme_rank_pairs` computes (no second computation),
    each side capped by the NEW `compass.delta.rotation_top_k` and a complete per-kind accounting
    (`shown_count`/`suppressed_count`/`residual_count`/`configured_total`) that discloses an
    above-threshold mover beyond the cap rather than dropping it uncounted (the exact defect this
    iteration fixes). The SAME signed `delta` + a served `direction_word` additionally ride the
    sector/theme-kind entries of `session_delta.changes` (single computation, two placements) — group-
    level only, no stock-kind row anywhere in `rotation` (Non-Goal).
  - `build_manifest_payload(...)` — assembles `session_delta` (now including `rotation`) + `narrative` +
    `selection` + `state_band` into one content document and computes `content_hash` (sha256 over the
    sorted-key JSON of the content block only — unchanged scope/contract from iter-2, including the
    cohorts nested inside `selection`, `state_band` alongside them since iter-28, and `session_delta.
    rotation` since iter-36).

The freeze/integrity block (iter-3, J-05/J-06) — `_freeze_manifest` is the ONE writer behind all three
producer paths:

  - (a) `get_or_create_manifest(..., producer="ingest_finalize")` — the ingest-finalize freeze call site;
    mints version 1, `mode` is data-driven (`at_ingest` iff no bar dated later than the as-of exists at
    generation — `_resolve_mode`), `frozen: true` always.
  - (b) `get_or_create_manifest(...)` (default `producer="on_demand_get"`) — create-once-on-GET for a
    HISTORICAL (non-frontier) as-of with no row yet. The CURRENT frontier's manifest is NEVER minted this
    way (`ManifestNotYetFrozen`) — only (a) or an explicit (c) can mint it (J-05 step 7 / TC-8).
  - (c) `regenerate_manifest(...)` — the confirm-gated regenerate action; mints version N+1 for an
    EXISTING `as_of`. `prospective_eligible` is write-once and version-shopping-proof: only version 1
    minted by `ingest_finalize` can ever be `true` (`_derive_prospective_eligible` is fail-closed on
    every condition independently — mode, producer, version, frozen, the `available_at_utc` fence, and
    complete provenance).

`manifest_row_payload(row)` reconstructs the served document from the row's split storage columns —
a READ, never a recompute (AG-8 column-projection posture: `comparison_cohort_json` /
`near_threshold_shadow_json` / `generation_json` / the three rule-identity config-subset columns are
their OWN columns so a future column-projected read never has to deserialize a block it does not need).
`basis_disclosure(session, row)` is a READ-TIME-ONLY comparison (never a mutation, never a recompute of
the frozen content) between the manifest's recorded `source_run_created_at` and the CURRENT stored run
for that as-of (never the dataset-version stamp alone, which a rebuild can reproduce byte-identically).

Reads ONLY column-projected `ScannerResult` selects for the universe-wide sweep, plus a bounded
`record_json` read for candidates AND (iter-3) every non-candidate member of the ONE run being frozen
(up to ~530 rows today) — never a full-universe sweep across runs (AG-8; TC-30). Never reads
`forward_returns` or any bar dated after the as-of — it reads already-stored, already-computed run rows
only (AG-5).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.config import Config, REPO_ROOT, get_config
from app.engine import engine_identity, evidence, market_phase, readiness
from app.engine.prices import latest_data_date
from app.engine.research import _dataset_version  # single-sourced dataset stamp (J-72) — never duplicated
from app.engine.session_delta import (
    KIND_SECTOR,
    KIND_THEME,
    compute_delta,
    find_previous_run,
    sector_rank_pairs,
    theme_rank_pairs,
)
from app.engine.setups import RISK_OFF_LABEL
from app.engine.snapshot_serving import dashboard_payload
from app.engine.universe_screen import POOL_SURVIVORSHIP_LABEL, read_pool
from app.models import NextSessionManifest, ScannerResult, ScannerRun, ThemeScoreRow

logger = logging.getLogger(__name__)

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


def _flat_band_word(delta: float, flat_band: float, cfg: Config) -> str:
    """Generic up/down/flat classification of a SIGNED delta against a flat-band threshold, via the ONE
    shared `compass.vocabulary.direction_words` map (goal.md, iter-28/J-07: "reuses the SAME ...  map,
    never a second word map"). The caller is responsible for the delta's SIGN meaning "higher is
    healthier" (positive -> "up"/improving) — see `build_state_band`'s stress-band sign note for the one
    band where that requires a deliberate transform before calling this."""
    vocab = cfg.compass.vocabulary.direction_words
    if abs(delta) < flat_band:
        return vocab["flat"]
    return vocab["up" if delta > 0 else "down"]


def _direction_word(current_run: ScannerRun, previous_run: ScannerRun, cfg: Config) -> tuple[str, float]:
    delta = current_run.regime_score - previous_run.regime_score
    return _flat_band_word(delta, cfg.compass.delta.velocity_flat_band, cfg), delta


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
    generation-time signal this narrative's retrospective stamp discloses. iter-3 (J-05/J-06) REUSES
    this exact check as "is this NOT the current frontier run" — the manifest-freeze frontier guard
    (`get_or_create_manifest`) and this narrative stamp ask the SAME question, so they share one
    answer rather than two independently-drifting checks."""
    later = session.exec(select(ScannerRun.id).where(ScannerRun.asof_date > current_run.asof_date)).first()
    return later is not None


def _assert_no_banned_language(sentences: list[dict], cfg: Config) -> None:
    """TC-11 as a runtime guarantee, not only an offline test scan: no rendered sentence may contain a
    committed banned term (imperative trade verbs, forecast terms, causal-attribution phrases — AG-2).
    iter-3 (J-05/J-06, TC-35) reuses this SAME scan over `evaluate_selection`'s candidate reason/caution/
    invalidation/why-not strings (`_scan_selection_language`, below) — these are about to be frozen into
    an immutable exported artifact, so the guard must cover them too, not only narrative sentences."""
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


# --- state_band (iter-28, J-07) -----------------------------------------------------------------

_STATE_BAND_NO_COMPARISON: dict = {"direction_word": None, "delta": None}


def _severity_at(session: Session, as_of: date, cfg: Config) -> Optional[float]:
    """One date's stored/cached severity, via the SAME `market_phase_cached` read `build_narrative`
    already uses for the current run (a warm cache hit for any date that was itself once the frontier —
    never a fresh full-history recompute here). Honest `None` (never fabricated) when phase data is
    unavailable for that date (insufficient trailing history)."""
    payload = market_phase.market_phase_cached(session, as_of, cfg)
    if not payload.get("available"):
        return None
    return payload.get("severity")


def build_state_band(
    session: Session,
    current_run: ScannerRun,
    previous_run: Optional[ScannerRun],
    config: Optional[Config] = None,
) -> dict:
    """The `state_band` CONTENT block (goal-market-compass iter-28, J-07) — three direction words
    (`regime`, `stress`, `breadth`), each with a signed delta, computed ONCE here inside
    `build_manifest_payload` (same producer/scope as `session_delta`/`narrative`), never recomputed at
    read. No-prior-run, OR a missing per-word input, independently renders THAT word's explicit
    null/no-comparison state — never a fabricated word (mirrors `session_delta`'s and `narrative`'s own
    no-prior-run handling).

      - `regime`: reuses `_direction_word` verbatim (current vs previous `regime_score`,
        `compass.delta.velocity_flat_band` — goal.md: "unchanged").
      - `breadth`: current vs previous `breadth_above_50dma`, banded via `compass.delta.
        breadth_min_change_pts` (goal.md's NOTES authorize reusing this existing edge). Higher breadth
        shares regime's polarity (more names above their 50-DMA is more constructive), so the raw delta
        classifies directly — no sign transform.
      - `stress`: current vs previous market-phase `severity` (the "severity velocity" goal.md names),
        banded via the NEW `compass.delta.stress_velocity_flat_band`. `state_band.stress.delta` is the
        LITERAL `current_severity - previous_severity` (unflipped — positive means severity ROSE).
        Severity's polarity is the OPPOSITE of regime_score/breadth: a rising severity is DETERIORATING,
        not improving (the engine's own existing convention: `market_phase._severity_velocity_at`'s
        docstring states "positive = severity worsening"). So the WORD is classified off this delta's
        NEGATION — a falling severity (stress easing) reads "up"/improving, a rising severity reads
        "down"/deteriorating — so the shared direction_words map's plain-English meaning ("improving" /
        "deteriorating") stays truthful for this band too. This sign choice is a deliberate design
        decision (documented in the dev handoff), not a literal-only reading of the delta equation."""
    cfg = config or get_config()
    if previous_run is None:
        return {
            "regime": dict(_STATE_BAND_NO_COMPARISON),
            "stress": dict(_STATE_BAND_NO_COMPARISON),
            "breadth": dict(_STATE_BAND_NO_COMPARISON),
        }

    regime_word, regime_delta = _direction_word(current_run, previous_run, cfg)

    current_severity = _severity_at(session, current_run.asof_date, cfg)
    previous_severity = _severity_at(session, previous_run.asof_date, cfg)
    if current_severity is not None and previous_severity is not None:
        stress_delta = current_severity - previous_severity
        stress_word = _flat_band_word(-stress_delta, cfg.compass.delta.stress_velocity_flat_band, cfg)
    else:
        stress_delta = None
        stress_word = None

    b_cur = current_run.breadth_above_50dma
    b_prev = previous_run.breadth_above_50dma
    if b_cur is not None and b_prev is not None:
        breadth_delta = b_cur - b_prev
        breadth_word = _flat_band_word(breadth_delta, cfg.compass.delta.breadth_min_change_pts, cfg)
    else:
        breadth_delta = None
        breadth_word = None

    return {
        "regime": {"direction_word": regime_word, "delta": regime_delta},
        "stress": {"direction_word": stress_word, "delta": stress_delta},
        "breadth": {"direction_word": breadth_word, "delta": breadth_delta},
    }


# --- rotation (iter-36, J-13) -------------------------------------------------------------------


def _rank_direction_word(delta: int, cfg: Config) -> str:
    """The sector/theme rank-delta -> `direction_word` classifier (goal-market-compass iter-36, J-13) --
    reuses the SAME `_flat_band_word`/`compass.vocabulary.direction_words` map every other direction word
    in this module uses (never a second word map). `flat_band` reuses `compass.delta.rank_move_min`
    itself: every caller here already gated the row to `abs(delta) >= rank_move_min`, so the word is
    never "flat" for a displayed row -- no separate threshold key is needed (AG-15: not a new/retuned
    threshold, just the SAME gate reused as the word classifier's flat-band). Polarity is resolved
    engine-side: a FALLING rank number (`delta < 0`) is an IMPROVING position, so `delta` is NEGATED
    before classifying -- mirrors the `state_band.stress` sign-transform precedent above (a falling
    severity is also "up"/improving)."""
    return _flat_band_word(-delta, cfg.compass.delta.rank_move_min, cfg)


def _rotation_row(entry: dict, cfg: Config) -> dict:
    """One `session_delta.rotation.<kind>.{gaining,losing}` row from a `session_delta.py` sector/theme
    pair entry (already carries a signed `delta`) -- the served shape only (label/from/to/delta/
    direction_word/drill_href); the internal `kind`/`magnitude`/`threshold` fields stay session_delta's
    own concern and are not repeated here."""
    return {
        "label": entry["label"],
        "from": entry["from"],
        "to": entry["to"],
        "delta": entry["delta"],
        "direction_word": _rank_direction_word(entry["delta"], cfg),
        "drill_href": entry["drill_href"],
    }


def _rotation_kind(pairs: list[tuple[dict, float]], cfg: Config, configured_total: int) -> dict:
    """One group kind's (`sector` | `theme`) rotation block: two labelled, both-directions sides plus a
    complete accounting (goal-market-compass iter-36, J-13) -- built from `pairs`, the SAME uncapped
    signed-delta pairs `session_delta.sector_rank_pairs`/`theme_rank_pairs` already computed (no second
    computation), already sorted most-moved-first.

    `gaining` = an IMPROVING position (`delta < 0`, rank number fell); `losing` = a DETERIORATING one
    (`delta > 0`); a pair that clears `rank_move_min` can never have `delta == 0` (the gate requires
    `abs(delta) >= rank_move_min >= 1`), so every above-threshold pair lands in exactly one side.

    Accounting: `shown_count` (rows actually returned, both sides, after the `rotation_top_k` cap) +
    `suppressed_count` (below-`rank_move_min` pairs) + `residual_count` (above-threshold pairs beyond the
    cap on EITHER side -- disclosed, never dropped, unlike the prior defect this iteration fixes) sums to
    exactly `len(pairs)`, which equals `configured_total` whenever both runs score the full configured
    universe (the fixed sector/industry and theme catalogs always do)."""
    threshold = cfg.compass.delta.rank_move_min
    cap = cfg.compass.delta.rotation_top_k
    above = [(entry, magnitude) for entry, magnitude in pairs if magnitude >= threshold]
    suppressed_count = len(pairs) - len(above)
    gaining_all = [entry for entry, _magnitude in above if entry["delta"] < 0]
    losing_all = [entry for entry, _magnitude in above if entry["delta"] > 0]
    gaining = gaining_all[:cap]
    losing = losing_all[:cap]
    residual_count = (len(gaining_all) - len(gaining)) + (len(losing_all) - len(losing))
    return {
        "gaining": [_rotation_row(entry, cfg) for entry in gaining],
        "losing": [_rotation_row(entry, cfg) for entry in losing],
        "shown_count": len(gaining) + len(losing),
        "suppressed_count": suppressed_count,
        "residual_count": residual_count,
        "configured_total": configured_total,
    }


def _rotation_no_prior(configured_total: int) -> dict:
    """One kind's explicit no-prior-run rotation state (TC-9) -- no deltas, no direction words, no
    fabricated rows, consistent with `session_delta`'s own top-level no-prior-run branch. `configured_total`
    is a static config fact (not a comparison result), so it is still reported honestly here."""
    return {
        "gaining": [], "losing": [], "shown_count": 0, "suppressed_count": 0,
        "residual_count": 0, "configured_total": configured_total,
    }


def build_rotation(
    previous_run: Optional[ScannerRun],
    sector_pairs: list[tuple[dict, float]],
    theme_pairs: list[tuple[dict, float]],
    cfg: Config,
) -> dict:
    """The `session_delta.rotation` CONTENT block (goal-market-compass iter-36, J-13) -- two labelled,
    signed, both-directions sides per group kind (`sector`, `theme`), built from the SAME sector/theme
    rank pairs `compute_delta` already computes (`sector_pairs`/`theme_pairs`, passed in by
    `build_manifest_payload` -- no second computation). Group-level only -- no stock-kind row anywhere
    here (Non-Goal, J-13 step 1). `previous_run is None` renders each kind's explicit no-prior-run state
    (TC-9)."""
    sector_total = len(cfg.etfs.sector) + len(cfg.etfs.industry)
    theme_total = len(cfg.themes)
    if previous_run is None:
        return {"sector": _rotation_no_prior(sector_total), "theme": _rotation_no_prior(theme_total)}
    return {
        "sector": _rotation_kind(sector_pairs, cfg, sector_total),
        "theme": _rotation_kind(theme_pairs, cfg, theme_total),
    }


def _attach_rank_direction_words(changes: list[dict], cfg: Config) -> None:
    """TC-6: mutates sector/theme-kind entries of `session_delta.changes` IN PLACE, attaching the SAME
    `direction_word` their rotation-row counterpart carries -- `delta` already rides these entries from
    `session_delta.py`'s `_entry` calls (single computation); this adds ONLY the served word, via the SAME
    `_rank_direction_word` helper `_rotation_row` uses (single computation, two placements, goal.md)."""
    for entry in changes:
        if entry["kind"] in (KIND_SECTOR, KIND_THEME) and "delta" in entry:
            entry["direction_word"] = _rank_direction_word(entry["delta"], cfg)


# --- selection (J-04; iter-3 J-05/J-06 adds comparison_cohort + near_threshold_shadow) --------

_QUALIFIER_CHECKS = ("leadership_min_score", "entry_min_score", "risk_max_score")

# iter-3 (J-05/J-06): the cohort row's frozen context field list — part of `cohort_rule_hash`'s scope
# (goal.md: "the cohort row field list"). Changing this list is itself a cohort-rule-affecting change
# (a new/removed field moves `cohort_rule_hash`), so it is read into that hash's subset dict verbatim
# rather than left as an unhashed implementation detail.
_COHORT_ROW_FIELDS: tuple[str, ...] = (
    "ticker", "leadership_score", "leadership_bucket", "entry_quality_score", "entry_quality_bucket",
    "risk_score", "risk_bucket", "setup_status", "rank_in_run", "sector", "theme_memberships",
    "close", "atr_pct", "distance_from_52w_high", "gap_p95", "worst_20d", "distance_to_invalidation",
    "adv_dollars",
)
# The closed selection_disposition vocabulary (goal.md: partitions the non-selected set exactly under
# the frozen rule — floor, then cap; nothing else excludes). Part of `cohort_rule_hash`'s scope.
_DISPOSITION_BELOW_FLOOR = "below_selection_floor"
_DISPOSITION_EXCLUDED_BY_CAP = "excluded_by_cap"
_DISPOSITION_VOCABULARY: tuple[str, ...] = (_DISPOSITION_BELOW_FLOOR, _DISPOSITION_EXCLUDED_BY_CAP)
# The declared candidate ordering rule (goal.md: "leadership desc, ticker asc") — a fixed descriptive
# string, not a config value; part of `candidate_rule_hash`'s scope so a future re-ordering shows up as
# an identity change even though no config KEY governs it today.
_CANDIDATE_ORDERING_RULE = "leadership desc, ticker asc"


def _record_json_by_ticker(session: Session, run: ScannerRun, tickers: list[str]) -> dict[str, dict]:
    """A targeted, bounded `record_json` read for a specific ticker list SCOPED TO THIS ONE RUN — never a
    full-universe or cross-run sweep (AG-8). Used for both candidates (`len(tickers) <= max_candidates`)
    and, since iter-3 (J-05/J-06), every non-candidate member of the run being frozen (up to ~530 rows
    today, TC-30) — still one bounded per-run query, not a whole-table scan. Deliberately self-contained
    (does not reuse `snapshot_serving.filtered_stock_rows`, which additionally attaches `forward_returns`
    — this producer stays grep-clean of any post-as-of read, TC-29)."""
    if not tickers:
        return {}
    rows = session.exec(
        select(ScannerResult.ticker, ScannerResult.record_json).where(
            ScannerResult.run_id == run.id, ScannerResult.ticker.in_(tickers)
        )
    ).all()
    return {ticker: json.loads(record_json) for ticker, record_json in rows}


def _theme_rank_by_slug(session: Session, run: ScannerRun) -> dict[str, int]:
    """One small, per-run-bounded query (as many rows as configured themes — 11 today) mapping this run's
    theme slug -> its stored rank. Used to attach `theme_memberships`' per-theme rank to each cohort row
    without a per-ticker query (AG-8)."""
    rows = session.exec(
        select(ThemeScoreRow.slug, ThemeScoreRow.rank).where(ThemeScoreRow.run_id == run.id)
    ).all()
    return dict(rows)


def _component_raw(components: list[dict], name: str) -> Optional[float]:
    """The stored RAW value of one named component from a `leadership`/`entry_quality`/`risk` score
    block's `components` array (`scoring._build_score`'s output, already stored verbatim in
    `record_json`) — a READ of an already-computed value, never a new computation. `None` when the
    component is absent or was NA for this row (honestly propagated, never fabricated)."""
    for component in components:
        if component.get("name") == name:
            return component.get("raw")
    return None


def _cohort_row(row: dict, record: Optional[dict], theme_rank_by_slug: dict[str, int]) -> dict:
    """One frozen `comparison_cohort` / `near_threshold_shadow` context row (goal-market-compass iter-3,
    J-05/J-06) — every value is read from the run's ALREADY-STORED `record_json` (the SAME canonical
    per-stock document `_candidate_payload` already reads a slice of), never a new bar/DB read (AG-8, "no
    new data sources"):

      - `close` reuses the invalidation block's `price` field — the as-of last close
        (`scoring._invalidation`'s `price` arg is literally `inv_closes[-1]`, the as-of-date close).
      - `distance_from_52w_high` reuses the Leadership score's stored `high_proximity` component raw
        (`scoring._raw_components`: `dist_high = ind.dist_from_high(...)`, <= 0; already surfaced
        verbatim by the Factor Lab at `leadership.components.high_proximity.raw` — an established
        cross-surface read of this exact stored value, not a new one).
      - `adv_dollars` reuses the Risk score's stored `liquidity` component raw, sign-flipped back
        (`scoring._raw_components` stores `_neg(adv)` there so a HIGHER raw reads as MORE dangerous,
        matching every other Risk component's orientation — this is a re-sign of an already-stored
        number, not a new computation, no bars read).
      - `atr_pct` / `gap_p95` / `worst_20d` / `distance_to_invalidation` all come from the SAME
        `risk_budget` block `_candidate_payload`'s ATR caution already reads a slice of."""
    record = record or {}
    risk_budget = record.get("risk_budget") or {}
    atr = risk_budget.get("atr_pct") or {}
    gap_profile = risk_budget.get("gap_profile") or {}
    leadership_components = (record.get("leadership") or {}).get("components") or []
    risk_components = (record.get("risk") or {}).get("components") or []
    liquidity_raw = _component_raw(risk_components, "liquidity")
    themes = record.get("themes") or []

    return {
        "ticker": row["ticker"],
        "leadership_score": row["leadership_score"],
        "leadership_bucket": row["leadership_bucket"],
        "entry_quality_score": row["entry_quality_score"],
        "entry_quality_bucket": row["entry_quality_bucket"],
        "risk_score": row["risk_score"],
        "risk_bucket": row["risk_bucket"],
        "setup_status": row["setup_status"],
        "rank_in_run": row["rank_in_run"],
        "sector": row["sector"],
        "theme_memberships": [
            {"theme": theme["slug"], "rank": theme_rank_by_slug.get(theme["slug"])} for theme in themes
        ],
        "close": (record.get("invalidation") or {}).get("price"),
        "atr_pct": {"value": atr.get("value"), "percentile": atr.get("percentile")},
        "distance_from_52w_high": _component_raw(leadership_components, "high_proximity"),
        "gap_p95": (gap_profile.get("p95") or {}).get("value"),
        "worst_20d": (risk_budget.get("worst_20d_window") or {}).get("value"),
        "distance_to_invalidation": (risk_budget.get("distance_to_invalidation_pct") or {}).get("value"),
        "adv_dollars": -liquidity_raw if liquidity_raw is not None else None,
    }


def _assert_disposition_predicate(comparison_cohort: list[dict], sel) -> None:
    """goal-market-compass iter-35 (J-12): makes `selection_disposition` truthful BY CONSTRUCTION, not
    merely by the caller's good behavior -- asserts each label's OWN predicate holds for every cohort row
    before `evaluate_selection` ever returns: `below_selection_floor` implies leadership below the floor,
    `excluded_by_cap` implies leadership at or above it. A violation here would mean the partition logic
    above regressed, not that a row is legitimately mislabeled -- this must never fire in production."""
    for row in comparison_cohort:
        disposition = row["selection_disposition"]
        cleared_floor = row["leadership_score"] >= sel.leadership_min_score
        if disposition == _DISPOSITION_BELOW_FLOOR:
            if cleared_floor:
                raise AssertionError(
                    f"{row['ticker']}: selection_disposition=below_selection_floor but leadership_score "
                    f"{row['leadership_score']} >= leadership_min_score {sel.leadership_min_score}"
                )
        elif disposition == _DISPOSITION_EXCLUDED_BY_CAP:
            if not cleared_floor:
                raise AssertionError(
                    f"{row['ticker']}: selection_disposition=excluded_by_cap but leadership_score "
                    f"{row['leadership_score']} < leadership_min_score {sel.leadership_min_score}"
                )


def _scan_selection_language(candidates: list[dict], why_not: list[dict], cfg: Config) -> None:
    """TC-35: extend the SAME runtime banned-language guard `build_narrative` already uses to
    `evaluate_selection`'s candidate reason/caution/invalidation/why-not strings — these are about to be
    frozen into an immutable exported artifact (iter-3), so the guard must cover them before ANY
    candidate is returned, not only narrative sentences (the exact gap `lessons.md` iter-2 flagged)."""
    pseudo_sentences: list[dict] = []
    for candidate in candidates:
        ticker = candidate["ticker"]
        for index, text in enumerate(candidate["reasons"]):
            pseudo_sentences.append({"template_id": f"candidate_reason_{ticker}_{index}", "text": text, "facts": []})
        for index, text in enumerate(candidate["cautions"]):
            pseudo_sentences.append({"template_id": f"candidate_caution_{ticker}_{index}", "text": text, "facts": []})
        pseudo_sentences.append(
            {"template_id": f"candidate_invalidation_{ticker}", "text": candidate["invalidation"], "facts": []}
        )
    for entry in why_not:
        for index, failed in enumerate(entry["failed_conditions"]):
            # `condition` is always one of the fixed `_QUALIFIER_CHECKS` tokens, never free text — scanned
            # anyway so the guard's coverage matches goal.md's literal "why-not strings" wording exactly.
            pseudo_sentences.append(
                {"template_id": f"why_not_{entry['ticker']}_{index}", "text": failed["condition"], "facts": []}
            )
    _assert_no_banned_language(pseudo_sentences, cfg)


def _qualifier_checks(row: dict, cfg: Config) -> list[dict]:
    """goal-market-compass iter-35 (J-12): each check now carries its own `gating` tag -- the SINGLE
    source of truth for which qualifier is the candidacy gate (`leadership_min_score`, per the goal
    file's own declared rule and `config.yaml`'s comment) versus an advisory qualifier
    (`entry_min_score`/`risk_max_score`) that annotates a caution and the eligibility checklist but never
    removes a row from candidacy. Both `evaluate_selection`'s partition and `_candidate_payload`'s
    checklist/reason/caution construction read this ONE tag rather than re-deriving it."""
    sel = cfg.compass.selection
    return [
        {
            "condition": "leadership_min_score",
            "threshold": sel.leadership_min_score,
            "actual": row["leadership_score"],
            "passed": row["leadership_score"] >= sel.leadership_min_score,
            "gating": True,
        },
        {
            "condition": "entry_min_score",
            "threshold": sel.entry_min_score,
            "actual": row["entry_quality_score"],
            "passed": row["entry_quality_score"] >= sel.entry_min_score,
            "gating": False,
        },
        {
            "condition": "risk_max_score",
            "threshold": sel.risk_max_score,
            "actual": row["risk_score"],
            "passed": row["risk_score"] <= sel.risk_max_score,
            "gating": False,
        },
    ]


def _failed_condition_entries(checks: list[dict]) -> list[dict]:
    """goal-market-compass iter-38 (J-14): every check that did NOT pass, carrying its own `gating` tag
    (from `_qualifier_checks`, the single source) alongside the existing threshold/actual/distance shape
    -- so a why-not entry never claims a row passed a qualifier it failed, and a reader can tell a
    gating miss (the candidacy floor) from an advisory one (entry/risk, never removes candidacy). Used
    for BOTH non-qualifying rows (below the floor) and qualifying-but-cap-excluded rows (which can still
    carry a failed ADVISORY check -- the exact case iter-35 left unrecorded, BACKGROUND)."""
    return [
        {
            "condition": check["condition"],
            "threshold": check["threshold"],
            "actual": check["actual"],
            "distance": abs(check["actual"] - check["threshold"]),
            "gating": check["gating"],
        }
        for check in checks
        if not check["passed"]
    ]


def _candidate_payload(row: dict, checks: list[dict], detail: Optional[dict], run: ScannerRun, cfg: Config) -> dict:
    """goal-market-compass iter-35 (J-12): `checks` may now include an ADVISORY qualifier that FAILED
    (leadership_min_score is the only gate -- a candidate is guaranteed to have `checks[0]["passed"]`
    True, but entry_min_score/risk_max_score are never guaranteed). Each check's own `gating` tag (from
    `_qualifier_checks`, the single source) decides whether it contributes a "clears" REASON (passed) or,
    for an advisory miss, a CAUTION citing the threshold and the row's actual stored value -- never a
    reason claiming it clears a qualifier it did not clear."""
    vocab = cfg.compass.vocabulary
    checklist = [
        {
            "condition": check["condition"],
            "threshold": check["threshold"],
            "actual": check["actual"],
            "verdict": "Pass" if check["passed"] else "Miss",
            "gating": check["gating"],
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
    reason_by_condition = {
        "leadership_min_score": (
            f"Leadership score {row['leadership_score']:.1f} clears the {sel.leadership_min_score:.1f} floor "
            f"({vocab.leadership_words[row['leadership_bucket']]})."
        ),
        "entry_min_score": (
            f"Entry Quality score {row['entry_quality_score']:.1f} clears the {sel.entry_min_score:.1f} "
            f"qualifier ({vocab.entry_words[row['entry_quality_bucket']]})."
        ),
        "risk_max_score": (
            f"Risk score {row['risk_score']:.1f} clears the {sel.risk_max_score:.1f} ceiling "
            f"({vocab.risk_words[row['risk_bucket']]})."
        ),
    }
    # Advisory-qualifier-miss caution text (never shown for the leadership gate -- a candidate always
    # clears it). States the threshold and the row's ACTUAL stored value only -- no advice-sounding tail
    # (mirrors the ATR_RISK_BUDGET caution's fact-only posture, TC-34).
    caution_by_condition = {
        "entry_min_score": (
            f"ENTRY_QUALITY_QUALIFIER: Entry Quality score {row['entry_quality_score']:.1f} is below the "
            f"{sel.entry_min_score:.1f} qualifier ({vocab.entry_words[row['entry_quality_bucket']]}) -- "
            "advisory only; Leadership alone determines candidacy."
        ),
        "risk_max_score": (
            f"RISK_QUALIFIER: Risk score {row['risk_score']:.1f} is above the {sel.risk_max_score:.1f} "
            f"ceiling ({vocab.risk_words[row['risk_bucket']]}) -- advisory only; Leadership alone "
            "determines candidacy."
        ),
    }
    reasons = []
    qualifier_cautions = []
    for check in checks:
        if check["passed"]:
            reasons.append(reason_by_condition[check["condition"]])
        elif not check["gating"]:  # a candidate's gating check always passes -- this is always an advisory miss
            qualifier_cautions.append(caution_by_condition[check["condition"]])

    cautions = list(qualifier_cautions)
    invalidation_note = "No stored invalidation note for this row."
    risk_budget = (detail or {}).get("risk_budget") or {}
    atr = risk_budget.get("atr_pct") or {}
    if atr.get("value") is not None:
        pct = atr.get("percentile")
        pct_text = f"p{pct * 100:.0f} of universe" if pct is not None else "percentile NA"
        # TC-34 (iter-3 MINOR finding, iter-2 eval): states the fact only — no advice-sounding tail.
        cautions.append(f"ATR_RISK_BUDGET: ATR is {atr['value']:.2f}% of price ({pct_text}).")
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


def _select_why_not_display(why_not_pool: list[dict], why_not_cap: int, cap_per_reason: int) -> list[dict]:
    """goal-market-compass iter-38 (J-14): reserve up to `cap_per_reason` DISPLAY slots for EACH why-not
    reason class before filling the remaining `why_not_cap` budget from whichever class has leftover
    entries -- without this split, a single leadership-desc sort over the combined pool always favors
    `excluded_by_cap` rows (leadership >= the floor, by construction, outranks every
    `below_selection_floor` row), so the near-miss band stays entirely unlistable whenever the
    cap-excluded pool alone exceeds `why_not_cap` (the exact BACKGROUND defect: 27 cap-excluded vs a cap
    of 20 on the committed 2026-08-12 frontier). `why_not_pool` is already sorted (leadership desc,
    ticker asc, TC-1..TC-3's ordering); config validation (`CompassSelectionCfg._validate`) guarantees
    `2 * cap_per_reason <= why_not_cap` so the two reservations never themselves exceed the total cap."""
    by_reason: dict[str, list[dict]] = {_DISPOSITION_EXCLUDED_BY_CAP: [], _DISPOSITION_BELOW_FLOOR: []}
    for entry in why_not_pool:
        by_reason[entry["reason"]].append(entry)

    selected: list[dict] = []
    leftover: list[dict] = []
    for reason in (_DISPOSITION_EXCLUDED_BY_CAP, _DISPOSITION_BELOW_FLOOR):
        pool = by_reason[reason]
        selected.extend(pool[:cap_per_reason])
        leftover.extend(pool[cap_per_reason:])

    remaining_budget = why_not_cap - len(selected)
    if remaining_budget > 0 and leftover:
        leftover.sort(key=lambda entry: (-entry["row"]["leadership_score"], entry["row"]["ticker"]))
        selected.extend(leftover[:remaining_budget])

    selected.sort(key=lambda entry: (-entry["row"]["leadership_score"], entry["row"]["ticker"]))
    return selected[:why_not_cap]  # defensive: config validation guarantees this never actually trims


def evaluate_selection(session: Session, run: ScannerRun, config: Optional[Config] = None) -> dict:
    """The `selection` CONTENT block (goal-market-compass iter-2, J-04; iter-3, J-05/J-06 adds
    `comparison_cohort` + `near_threshold_shadow`). See the module docstring for the anti-goal posture
    (AG-8 bounded reads, AG-11 no new composite score)."""
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
            ScannerResult.setup_status,
            ScannerResult.rank,
            ScannerResult.sector,
        )
        .where(ScannerResult.run_id == run.id)
        .order_by(ScannerResult.ticker)
    ).all()
    member_count = len(raw_rows)

    qualifying: list[tuple[dict, list[dict]]] = []
    non_qualifying: list[tuple[dict, list[dict]]] = []
    for (
        ticker, l_score, l_bucket, e_score, e_bucket, r_score, r_bucket, setup_status, rank, sector,
    ) in raw_rows:
        row = {
            "ticker": ticker,
            "leadership_score": l_score,
            "leadership_bucket": l_bucket,
            "entry_quality_score": e_score,
            "entry_quality_bucket": e_bucket,
            "risk_score": r_score,
            "risk_bucket": r_bucket,
            "setup_status": setup_status,
            "rank_in_run": rank,
            "sector": sector,
        }
        checks = _qualifier_checks(row, cfg)
        # goal-market-compass iter-35 (J-12): `leadership_min_score` (the sole `gating: True` check) is
        # the ONLY candidacy gate -- `entry_min_score`/`risk_max_score` are advisory and never remove a
        # row from candidacy, matching the goal file's own declared rule and config.yaml's own comment.
        gating_checks = [check for check in checks if check["gating"]]
        assert len(gating_checks) == 1, "expected exactly one gating qualifier check (leadership_min_score)"
        if gating_checks[0]["passed"]:
            qualifying.append((row, checks))
        else:
            non_qualifying.append((row, _failed_condition_entries(checks)))

    qualifying.sort(key=lambda pair: (-pair[0]["leadership_score"], pair[0]["ticker"]))
    candidate_pairs = qualifying[: sel.max_candidates]
    excluded_by_cap_pairs = qualifying[sel.max_candidates :]

    candidate_tickers = [row["ticker"] for row, _checks in candidate_pairs]
    detail_by_ticker = _record_json_by_ticker(session, run, candidate_tickers)
    candidates = [
        _candidate_payload(row, checks, detail_by_ticker.get(row["ticker"]), run, cfg)
        for row, checks in candidate_pairs
    ]

    # goal-market-compass iter-38 (J-14): the why-not pool carries BOTH non-selection reasons, each entry
    # its OWN true evaluation -- a below-floor row's failed_conditions already includes the gating
    # leadership_min_score miss (plus any advisory misses); a cap-excluded row's checks are re-evaluated
    # here (`_failed_condition_entries`, the SAME helper) because a qualifying-but-cap-excluded row can
    # still fail an ADVISORY qualifier (entry_min_score/risk_max_score) -- the exact case the prior code
    # discarded by extending with an unconditional `[]` (BACKGROUND). `cap_rank` is the row's 1-based
    # position in the FULL leadership-sorted `qualifying` list (candidates occupy ranks
    # 1..max_candidates; excluded_by_cap_pairs starts at rank max_candidates + 1) -- reuses the SAME
    # sort `qualifying` was already sorted by, no new ordering computed.
    why_not_pool: list[dict] = [
        {"row": row, "failed_conditions": failed, "reason": _DISPOSITION_BELOW_FLOOR, "cap_rank": None, "cap": None}
        for row, failed in non_qualifying
        if row["leadership_score"] >= sel.why_not_floor
    ]
    why_not_pool.extend(
        {
            "row": row,
            "failed_conditions": _failed_condition_entries(checks),
            "reason": _DISPOSITION_EXCLUDED_BY_CAP,
            "cap_rank": cap_rank,
            "cap": sel.max_candidates,
        }
        for cap_rank, (row, checks) in enumerate(excluded_by_cap_pairs, start=sel.max_candidates + 1)
    )
    # The two UNCAPPED per-reason pool counts (goal.md data-contract addition) -- computed from the SAME
    # partitions the disposition tally above already computed, BEFORE the why_not_cap truncation below
    # (no new query, no full-universe pass).
    why_not_totals = {
        "excluded_by_cap_uncapped": len(excluded_by_cap_pairs),
        "below_floor_in_band_uncapped": sum(
            1 for row, _failed in non_qualifying if row["leadership_score"] >= sel.why_not_floor
        ),
    }
    why_not_pool.sort(key=lambda entry: (-entry["row"]["leadership_score"], entry["row"]["ticker"]))
    why_not = [
        {
            "ticker": entry["row"]["ticker"],
            "failed_conditions": entry["failed_conditions"],
            "reason": entry["reason"],
            "cap_rank": entry["cap_rank"],
            "cap": entry["cap"],
        }
        for entry in _select_why_not_display(why_not_pool, sel.why_not_cap, sel.why_not_cap_per_reason)
    ]

    candidates_empty_reason = None
    if not candidates:
        # goal-market-compass iter-35 (J-12, TC-7): names ONLY the gating rule -- Entry Quality/Risk are
        # advisory qualifiers and are never cited here as though they gated inclusion.
        candidates_empty_reason = (
            f"No stored member cleared the Leadership score floor ({sel.leadership_min_score:.1f}) for "
            "this as-of -- the sole candidacy gate."
        )

    # --- iter-3 (J-05/J-06): comparison cohort (every non-candidate member) + near-threshold shadow.
    # Reuses the SAME non_qualifying / excluded_by_cap_pairs partitions the disposition tally above
    # already computed — exactly the below_selection_floor / excluded_by_cap split (BACKGROUND).
    non_candidate_pairs: list[tuple[dict, str]] = [(row, _DISPOSITION_BELOW_FLOOR) for row, _failed in non_qualifying]
    non_candidate_pairs.extend((row, _DISPOSITION_EXCLUDED_BY_CAP) for row, _checks in excluded_by_cap_pairs)
    non_candidate_pairs.sort(key=lambda pair: (-pair[0]["leadership_score"], pair[0]["ticker"]))

    non_candidate_tickers = [row["ticker"] for row, _disposition in non_candidate_pairs]
    non_candidate_records = _record_json_by_ticker(session, run, non_candidate_tickers)  # TC-30: one bounded per-run read
    theme_rank_by_slug = _theme_rank_by_slug(session, run)

    comparison_cohort = [
        {
            **_cohort_row(row, non_candidate_records.get(row["ticker"]), theme_rank_by_slug),
            "selection_disposition": disposition,
        }
        for row, disposition in non_candidate_pairs
    ]
    # Half-open band [shadow.min_score, leadership_min_score) — a name AT the floor is candidate-eligible,
    # never shadow. A subset of comparison_cohort by construction (built from the SAME ordered pairs, so
    # both stay in lockstep — never independently re-sorted / re-derived).
    near_threshold_shadow = [
        {k: v for k, v in cohort_row.items() if k != "selection_disposition"}
        for cohort_row, (row, _disposition) in zip(comparison_cohort, non_candidate_pairs)
        if sel.shadow.min_score <= row["leadership_score"] < sel.leadership_min_score
    ]

    # goal-market-compass iter-35 (J-12): make `selection_disposition` truthful BY CONSTRUCTION, not
    # merely by convention -- a per-row runtime check (mirrors `_scan_selection_language`'s
    # belt-and-suspenders posture) that each label's own predicate actually holds, on every produced
    # manifest, before it is ever returned.
    _assert_disposition_predicate(comparison_cohort, sel)

    result = {
        "candidates": candidates,
        "why_not": why_not,
        "why_not_totals": why_not_totals,
        "disposition_tally": {
            "below_selection_floor": len(non_qualifying),
            "excluded_by_cap": len(excluded_by_cap_pairs),
        },
        "candidates_empty_reason": candidates_empty_reason,
        "member_count": member_count,
        "comparison_cohort": comparison_cohort,
        "near_threshold_shadow": near_threshold_shadow,
    }
    _scan_selection_language(candidates, why_not, cfg)  # TC-35 — before ANY candidate/why-not is returned
    return result


# --- manifest CONTENT assembly (iter-2, unchanged scope) ----------------------------------------


def build_manifest_payload(
    session: Session,
    current_run: ScannerRun,
    previous_run: Optional[ScannerRun],
    config: Optional[Config] = None,
) -> dict:
    """Assemble the CONTENT blocks + `content_hash` (sha256 hex over the sorted-key JSON of the content
    block only — never re-derived at serve time; see `manifest_row_payload`). `selection` carries
    `comparison_cohort` / `near_threshold_shadow` (iter-3); `state_band` (iter-28, J-07) is a new
    top-level content block alongside `session_delta`/`narrative`/`selection` — additive to
    `content_hash`'s scope, no other code change needed for that.

    iter-36 (J-13): `sector_pairs`/`theme_pairs` are computed ONCE here (when `previous_run` exists) and
    passed into BOTH `compute_delta` (so its own sector/theme classify+cap reuses them, no second query)
    and `build_rotation` (`session_delta.rotation`) — one pair-building DB read per manifest build."""
    cfg = config or get_config()
    sector_pairs = sector_rank_pairs(session, current_run, previous_run, cfg) if previous_run is not None else []
    theme_pairs = theme_rank_pairs(session, current_run, previous_run, cfg) if previous_run is not None else []
    delta = compute_delta(session, current_run, previous_run, cfg, sector_pairs=sector_pairs, theme_pairs=theme_pairs)
    _attach_rank_direction_words(delta["changes"], cfg)
    delta["rotation"] = build_rotation(previous_run, sector_pairs, theme_pairs, cfg)
    selection = evaluate_selection(session, current_run, cfg)
    narrative = build_narrative(session, current_run, previous_run, selection, cfg)
    state_band = build_state_band(session, current_run, previous_run, cfg)
    content = {"session_delta": delta, "narrative": narrative, "selection": selection, "state_band": state_band}
    canonical = json.dumps(content, sort_keys=True, default=str)
    content_hash = hashlib.sha256(canonical.encode()).hexdigest()
    return {**content, "content_hash": content_hash}


# --- freeze/integrity block (iter-3, J-05/J-06) --------------------------------------------------


class ManifestNotYetFrozen(Exception):
    """J-05 step 7 / TC-8: the current frontier's manifest is minted ONLY by the ingest-finalize freeze
    or an explicit regenerate — never by a plain GET. Raised, never silently fabricated; the API layer
    maps this to an honest 404."""

    def __init__(self, as_of: date):
        self.as_of = as_of
        super().__init__(
            f"no next-session manifest exists yet for the current frontier date {as_of} — it is minted "
            "at the next ingest finalize freeze, never by a plain GET"
        )


class ManifestNotFoundError(Exception):
    """The confirm-gated regenerate action requires an EXISTING manifest for `as_of` — it never mints a
    first version (that is the finalize freeze's or create-once-on-GET's job)."""

    def __init__(self, as_of: date):
        self.as_of = as_of
        super().__init__(f"no next-session manifest exists yet for {as_of} — regenerate requires an existing manifest")


def _canonical_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _utc_isoformat(value: datetime) -> str:
    """SQLite reads a stored timestamp back WITHOUT tzinfo even when it was WRITTEN as
    `datetime.now(timezone.utc)` (the SAME gotcha `forward_testing._utc_isoformat` documents and fixes
    for `evidence_generated_at`). Reattaching UTC to an already-naive value (never touching a genuinely
    tz-aware one) keeps this producer's ISO strings byte-stable across a DB round-trip, which the
    manifest-hash / export byte-equality contract (TC-4/TC-9) depends on."""
    return (value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)).isoformat()


def _resolve_mode(session: Session, as_of: date) -> tuple[str, Optional[date]]:
    """TC-18: data-driven, fails toward retrospective. `at_ingest` iff no bar dated later than `as_of`
    exists at generation time — the SAME global frontier (`latest_data_date`) every other as-of resolver
    treats as "Latest". No price data at all also fails toward retrospective (never assumes at_ingest
    without evidence)."""
    frontier = latest_data_date(session)
    if frontier is None or frontier > as_of:
        return "retrospective", frontier
    return "at_ingest", frontier


def _candidate_rule_subset(cfg: Config) -> dict:
    """`candidate_rule_hash`'s scope: ONLY membership/ordering-affecting keys (goal.md) — never the
    why-not display cap, a caution qualifier, or the shadow band (TC-23)."""
    sel = cfg.compass.selection
    return {
        "rule_version": sel.rule_version,
        "leadership_min_score": sel.leadership_min_score,
        "max_candidates": sel.max_candidates,
        "ordering_rule": _CANDIDATE_ORDERING_RULE,
    }


def _cohort_rule_subset(cfg: Config) -> dict:
    """`cohort_rule_hash`'s scope: cohort semantics — `shadow.min_score`, the shared `leadership_min_score`
    band bound (a floor change moves BOTH scientific hashes, TC-23), the disposition-vocabulary version
    (`rule_version` doubles as this — extending the vocabulary is a rule change carried by a bumped
    `rule_version`, never a relabeling of frozen rows), and the cohort row field list."""
    sel = cfg.compass.selection
    return {
        "rule_version": sel.rule_version,
        "shadow_min_score": sel.shadow.min_score,
        "leadership_min_score": sel.leadership_min_score,
        "disposition_vocabulary": list(_DISPOSITION_VOCABULARY),
        "cohort_row_fields": list(_COHORT_ROW_FIELDS),
    }


def _manifest_config_subset(cfg: Config) -> dict:
    """`manifest_config_hash`'s scope: the WHOLE `compass.selection` subtree — qualifiers, why-not display
    keys, everything (TC-23: a why-not/qualifier-only change moves ONLY this hash)."""
    return cfg.compass.selection.model_dump()


def _hash_subset(subset: dict) -> str:
    return _sha256_hex(_canonical_dumps(subset))


def _universe_block(member_count: int, cfg: Config) -> dict:
    """`universe` block: pool hash + the point-in-time resolver gate values (read from config, never
    re-typed) + the member count `evaluate_selection` already computed (no second query) +
    `profile: "core"` (goal.md's companion-universe forward-compat non-goal — a defaulted slot only)."""
    try:
        pool_rows = read_pool()
        pool_hash = _sha256_hex(_canonical_dumps(pool_rows))
    except FileNotFoundError:
        pool_hash = None  # honest gap — never fabricated (mirrors universe_screen.pool_survivorship)
    filters = cfg.universe.filters
    return {
        "pool_hash": pool_hash,
        "resolver_gate": {
            "min_history_bars": cfg.indicators.min_history_bars,
            "max_staleness_days": filters.max_staleness_days,
            "min_price": filters.min_price,
            "adv_window_days": filters.adv_window_days,
            "min_dollar_vol": filters.min_dollar_vol,
        },
        "member_count": member_count,
        "profile": "core",
    }


# TC-27 (AG-16): the frozen non-causal cohort disclosure — verbatim per goal.md's own wording so the
# manifest and the frontend audit-view labels never drift from a second hand-typed copy.
_COHORT_SEMANTICS_TEXT = (
    "The comparison cohort is a frozen non-selected comparison pool, not a matched or causal control "
    "group. The near-threshold shadow cohort is near the LEADERSHIP selection floor specifically, not "
    "necessarily near the final candidate-selection boundary (deterministic ordering, the candidate cap, "
    "and any future gating qualifier also affect final inclusion) — it is never described as \"near-selected\"."
)

# The compass selection rule's own evidence signal name — never registered as a certified claim within
# this goal (AG-15: no outcome-tuned selection may be certified here). The check below is REAL (reads the
# SAME ledger status every other evidence chip reads), not a hardcoded string — an honest future ledger
# change would flip it, even though AG-15/AG-6 mean it never will within this goal.
_COMPASS_SELECTION_SIGNAL = "compass_selection"


def _evidence_caveat(session: Session, cfg: Config) -> str:
    """The manifest's evidence caveat — sourced from the SAME `GET /api/evidence` ledger status
    (`app.engine.evidence.build_evidence_payload`) every other "Proven / Not yet proven" surface in this
    product reads, never a second proven-ness computation (AG-1). No Evidence Claim names the compass
    selection rule itself within this goal (AG-15/AG-6), so this reads "Not yet proven" today — but the
    check is real, not decorative."""
    try:
        payload = evidence.build_evidence_payload(evidence.resolve_ledger_path(), session=session, config=cfg)
        proven = _COMPASS_SELECTION_SIGNAL in (payload.get("proven_signals") or {})
    except Exception as exc:  # noqa: BLE001 — fail-closed: an unreadable ledger is honestly "not yet proven"
        logger.error("compass manifest evidence-caveat read failed (non-fatal, fails closed): %s", exc)
        proven = False
    if proven:
        return "Backed by a certified out-of-sample claim for the compass selection rule (see the Evidence ledger)."
    return "Not yet proven — attention rule, not a certified edge (see the Evidence ledger)."


def _sector_basis_caveat(cfg: Config) -> str:
    """The sector-label basis disclosure — the SAME config prose `app.engine.methodology._sector_basis`
    resolves (a direct config-field read, not a re-typed copy: both read `config.methodology.
    universe_selection.sector_basis` verbatim)."""
    universe_selection = cfg.methodology.universe_selection
    if universe_selection is not None and universe_selection.sector_basis:
        return universe_selection.sector_basis
    return "Sector label basis disclosure is not configured for this build."


def _caveats_block(session: Session, cfg: Config) -> dict:
    return {
        "evidence": _evidence_caveat(session, cfg),
        "survivorship": POOL_SURVIVORSHIP_LABEL,
        "sector_basis": _sector_basis_caveat(cfg),
        "cohort_semantics": _COHORT_SEMANTICS_TEXT,
    }


def _derive_prospective_eligible(
    *,
    mode: str,
    frontier_bar_date: Optional[date],
    based_on_close: date,
    producer: str,
    version: int,
    frozen: bool,
    available_at_utc: Optional[datetime],
    provenance_complete: bool,
    manifest_hash: Optional[str],
) -> bool:
    """TC-20: fail-closed, write-once derivation — true iff EVERY condition holds; any missing/violated
    condition independently forces `false` (never partially trusted, never recomputed at read).
    `manifest_hash` here is a PRESENCE-only signal — production passes a non-None placeholder since the
    real hash is computed moments later in the SAME `_freeze_manifest` call (after which it is always
    non-null); this function's OWN fixture tests (TC-20) pass an explicit `None` to prove that branch in
    isolation."""
    return bool(
        mode == "at_ingest"
        and frontier_bar_date is not None
        and frontier_bar_date == based_on_close
        and producer == "ingest_finalize"
        and version == 1
        and frozen is True
        and available_at_utc is not None
        and provenance_complete
        and manifest_hash is not None
    )


def verify_manifest_hash(document: dict) -> bool:
    """Recompute `manifest_hash` over `document` (any dict carrying a `manifest_hash` key) the SAME
    canonical way `_freeze_manifest` computed it at write time — the hash field itself is excluded from
    what gets hashed, never a second convention. TC-4/TC-22: tamper detection — flipping any byte of a
    copied export (including inside `prospective_eligible` or a provenance field) changes some field's
    value and therefore fails this recomputation."""
    stored = document.get("manifest_hash")
    if not stored:
        return False
    without_hash = {key: value for key, value in document.items() if key != "manifest_hash"}
    return _sha256_hex(_canonical_dumps(without_hash)) == stored


def _write_export(document: dict, cfg: Config) -> Optional[str]:
    """The at-ingest-mode export writer: the SAME canonical bytes used for `manifest_hash` / storage,
    written to `compass.manifest.export_dir` (a `TRENDORA_COMPASS_EXPORT_DIR` env override exists for
    tests — name only, never a value in files). Isolate-and-continue: an I/O failure here is caught and
    logged, NEVER blocks or crashes the caller — `export_path` stays `None` (an honest gap, never a
    half-written file)."""
    export_dir_raw = os.environ.get("TRENDORA_COMPASS_EXPORT_DIR") or cfg.compass.manifest.export_dir
    export_dir = Path(export_dir_raw)
    if not export_dir.is_absolute():
        export_dir = (REPO_ROOT / export_dir).resolve()
    try:
        export_dir.mkdir(parents=True, exist_ok=True)
        path = export_dir / f"{document['as_of']}_v{document['version']}.json"
        payload = _canonical_dumps(document)
        try:
            # AG-12: an already-exported artifact is NEVER rewritten. Exclusive create ("x") so a SECOND
            # writer for the same `(as_of, version)` — a create-once/regenerate race whose INSERT loses,
            # or any process sharing the configured export dir — can never mutate the frozen bytes an
            # existing row's `export_path` already points at.
            with open(path, "x") as handle:
                handle.write(payload)
        except FileExistsError:
            if path.read_text() == payload:
                return str(path)  # byte-identical — idempotent re-export, nothing was mutated
            logger.error(
                "compass manifest export refused for as_of=%s version=%s: %s already exists with "
                "DIFFERENT bytes (AG-12 — a frozen artifact is never rewritten); export_path stays NULL "
                "for this row rather than overwriting the existing artifact",
                document.get("as_of"), document.get("version"), path,
            )
            return None
        return str(path)
    except OSError as exc:
        logger.error(
            "compass manifest export write failed for as_of=%s version=%s (non-fatal — export_path stays "
            "NULL, never a half-written file): %s", document.get("as_of"), document.get("version"), exc,
        )
        return None


def _freeze_manifest(
    session: Session,
    current_run: ScannerRun,
    *,
    version: int,
    producer: str,
    config: Optional[Config] = None,
) -> NextSessionManifest:
    """The ONE writer behind all three producer paths (goal-market-compass iter-3, J-05/J-06). Computes
    the CONTENT block (unchanged iter-2 contract), the freeze/integrity block, assembles ONE canonical
    document, computes `manifest_hash` over the complete document with only `manifest_hash` itself
    excluded, writes the at-ingest-mode export file BEFORE the INSERT (so `export_path` is included in
    the single write — AG-12 forbids any later UPDATE), then INSERTs the immutable row.

    Concurrency-safe: a losing concurrent INSERT for the SAME `(as_of, version)` rolls back and returns
    the already-committed row (mirrors `scanner.persist_run_payload`'s guard — never raises, never
    duplicates, never overwrites; TC-17)."""
    cfg = config or get_config()
    previous_run = find_previous_run(session, current_run)
    content_payload = build_manifest_payload(session, current_run, previous_run, cfg)
    selection = dict(content_payload["selection"])
    comparison_cohort = selection.pop("comparison_cohort")
    near_threshold_shadow = selection.pop("near_threshold_shadow")
    member_count = selection.pop("member_count")  # folded into universe.member_count -- one source, not two
    state_band = content_payload["state_band"]  # iter-28 (J-07) -- its own top-level document key + column

    generated_at = datetime.now(timezone.utc)
    available_at_utc = generated_at + timedelta(seconds=cfg.compass.manifest.availability_margin_seconds)
    mode, frontier_bar_date = _resolve_mode(session, current_run.asof_date)
    frozen = True  # every row THIS writer mints is a permanent record (models.py: "True for every row
    # minted by the iter-3 freeze writer") -- mode/producer/version already distinguish HOW it was minted

    engine_id = engine_identity.compute_engine_identity(cfg)

    preflight_verdict = None
    if mode == "at_ingest":
        # AG-13: the preflight verdict is recorded ONLY here (generation block, at-ingest only) -- never
        # on the market/narrative surface. Isolate-and-continue: a read failure never blocks the freeze.
        try:
            preflight_verdict = readiness.compute_preflight(session, cfg).get("verdict")
        except Exception as exc:  # noqa: BLE001
            logger.error("compass manifest preflight read failed for %s (non-fatal): %s", current_run.asof_date, exc)

    generation = {
        "producer": producer,
        "frontier_bar_date": frontier_bar_date.isoformat() if frontier_bar_date else None,
        "generated_at": generated_at.isoformat(),
        "preflight_verdict": preflight_verdict,
        "engine_identity": engine_id,
        "source_run_created_at": _utc_isoformat(current_run.created_at),
    }

    candidate_rule_config = _candidate_rule_subset(cfg)
    cohort_rule_config = _cohort_rule_subset(cfg)
    manifest_config_subset = _manifest_config_subset(cfg)
    candidate_rule_hash = _hash_subset(candidate_rule_config)
    cohort_rule_hash = _hash_subset(cohort_rule_config)
    manifest_config_hash = _hash_subset(manifest_config_subset)

    dataset = {"stamp": _dataset_version(session)}
    universe = _universe_block(member_count, cfg)
    caveats = _caveats_block(session, cfg)

    provenance_complete = bool(
        engine_id and candidate_rule_hash and cohort_rule_hash and manifest_config_hash
        and dataset["stamp"] and universe["pool_hash"]
    )
    prospective_eligible = _derive_prospective_eligible(
        mode=mode, frontier_bar_date=frontier_bar_date, based_on_close=current_run.asof_date,
        producer=producer, version=version, frozen=frozen, available_at_utc=available_at_utc,
        provenance_complete=provenance_complete, manifest_hash="pending",
    )

    document: dict[str, Any] = {
        "as_of": current_run.asof_date.isoformat(),
        "version": version,
        "mode": mode,
        "frozen": frozen,
        "session_delta": content_payload["session_delta"],
        "narrative": content_payload["narrative"],
        "selection": selection,
        "state_band": state_band,
        "comparison_cohort": comparison_cohort,
        "near_threshold_shadow": near_threshold_shadow,
        "content_hash": content_payload["content_hash"],
        "generation": generation,
        "candidate_rule_hash": candidate_rule_hash,
        "candidate_rule_config": candidate_rule_config,
        "cohort_rule_hash": cohort_rule_hash,
        "cohort_rule_config": cohort_rule_config,
        "manifest_config_hash": manifest_config_hash,
        "manifest_config_subset": manifest_config_subset,
        "dataset": dataset,
        "universe": universe,
        "caveats": caveats,
        "prospective_eligible": prospective_eligible,
        "available_at_utc": available_at_utc.isoformat(),
    }
    manifest_hash = _sha256_hex(_canonical_dumps(document))
    document["manifest_hash"] = manifest_hash

    export_path = None
    if mode == "at_ingest":  # goal.md: `modes: at_ingest only`
        export_path = _write_export(document, cfg)

    row = NextSessionManifest(
        as_of=current_run.asof_date,
        version=version,
        source_run_id=current_run.id,
        session_delta_json=json.dumps(content_payload["session_delta"]),
        narrative_json=json.dumps(content_payload["narrative"]),
        selection_json=json.dumps(selection),
        state_band_json=json.dumps(state_band),
        content_hash=content_payload["content_hash"],
        created_at=generated_at,
        mode=mode,
        frozen=frozen,
        generation_json=json.dumps(generation),
        engine_identity=engine_id,
        candidate_rule_hash=candidate_rule_hash,
        candidate_rule_config_json=json.dumps(candidate_rule_config),
        cohort_rule_hash=cohort_rule_hash,
        cohort_rule_config_json=json.dumps(cohort_rule_config),
        manifest_config_hash=manifest_config_hash,
        manifest_config_subset_json=json.dumps(manifest_config_subset),
        dataset_json=json.dumps(dataset),
        universe_json=json.dumps(universe),
        comparison_cohort_json=json.dumps(comparison_cohort),
        near_threshold_shadow_json=json.dumps(near_threshold_shadow),
        caveats_json=json.dumps(caveats),
        prospective_eligible=prospective_eligible,
        available_at_utc=available_at_utc,
        manifest_hash=manifest_hash,
        export_path=export_path,
    )
    session.add(row)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        existing = session.exec(
            select(NextSessionManifest).where(
                NextSessionManifest.as_of == current_run.asof_date, NextSessionManifest.version == version,
            )
        ).first()
        if existing is not None:
            return existing
        raise
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.exec(
            select(NextSessionManifest).where(
                NextSessionManifest.as_of == current_run.asof_date, NextSessionManifest.version == version,
            )
        ).first()
        if existing is not None:
            return existing
        raise
    session.refresh(row)
    return row


def latest_manifest_for_date(session: Session, as_of: date) -> Optional[NextSessionManifest]:
    """The LATEST stored `NextSessionManifest` version for `as_of`, or `None` if none exists yet — a
    pure read: no run lookup, no write, no self-heal. Factored out of `get_or_create_manifest`'s
    existing-row check (below) so both call sites share the ONE query shape for "does a manifest
    already exist for this date" (single source, no duplicate query shape for the same fact).

    iter-27 (J-06 step 2's last unmet limb): this lets `GET /api/compass` probe for an existing
    manifest BEFORE ever resolving/self-healing a `ScannerRun`, so a frozen manifest whose source run
    has been removed can be served with an honest `basis.status == "unavailable"` instead of the read
    path silently recreating the run first."""
    return session.exec(
        select(NextSessionManifest)
        .where(NextSessionManifest.as_of == as_of)
        .order_by(NextSessionManifest.version.desc())
    ).first()


def get_or_create_manifest(
    session: Session, current_run: ScannerRun, config: Optional[Config] = None, *, producer: str = "on_demand_get",
) -> NextSessionManifest:
    """Serve the LATEST stored manifest version for `current_run.asof_date`, minting version 1 ONCE if
    none exists yet (TC-1: zero producer calls on a warm hit). `producer` defaults to `"on_demand_get"`
    (the `GET /api/compass` call site); the ingest-finalize call site passes `producer="ingest_finalize"`
    explicitly.

    J-05 step 7 / TC-8: for the CURRENT frontier run (no LATER stored run exists) with no manifest yet,
    a non-finalize caller NEVER auto-creates one — raises `ManifestNotYetFrozen`. A HISTORICAL
    (non-frontier) `as_of` still create-once-mints here regardless of caller (mode resolves
    `retrospective` since a later run already exists)."""
    cfg = config or get_config()
    existing = latest_manifest_for_date(session, current_run.asof_date)
    if existing is not None:
        return existing

    if producer != "ingest_finalize" and not _is_retrospective(session, current_run):
        raise ManifestNotYetFrozen(current_run.asof_date)

    return _freeze_manifest(session, current_run, version=1, producer=producer, config=cfg)


def regenerate_manifest(session: Session, as_of: date, config: Optional[Config] = None) -> NextSessionManifest:
    """The confirm-gated regenerate action (path c) — mints version N+1 for an EXISTING `as_of`. Raises
    `ManifestNotFoundError` when no manifest (or no source run) exists for `as_of` — NEVER fabricates a
    first version this way (that is `get_or_create_manifest`'s job). ALWAYS `prospective_eligible: false`
    (via `_derive_prospective_eligible`'s `producer == "ingest_finalize"` / `version == 1` checks — no
    special-casing needed here). Version 1 is never touched — a NEW row only."""
    cfg = config or get_config()
    latest = session.exec(
        select(NextSessionManifest)
        .where(NextSessionManifest.as_of == as_of)
        .order_by(NextSessionManifest.version.desc())
    ).first()
    if latest is None:
        raise ManifestNotFoundError(as_of)
    current_run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == as_of)).first()
    if current_run is None:
        # the source run is gone -- nothing to recompute content from; honest failure, never fabricated
        raise ManifestNotFoundError(as_of)
    return _freeze_manifest(session, current_run, version=latest.version + 1, producer="regenerate", config=cfg)


def list_manifest_versions(session: Session, as_of: date) -> list[NextSessionManifest]:
    """Every stored version for `as_of`, oldest first — read-only, bounded to this one date's rows (a
    handful at most). Backs the manifest strip's "both versions" listing once more than one exists."""
    return list(
        session.exec(
            select(NextSessionManifest).where(NextSessionManifest.as_of == as_of).order_by(NextSessionManifest.version)
        ).all()
    )


def basis_disclosure(session: Session, row: NextSessionManifest) -> dict:
    """Read-time-only comparison (TC-9..TC-19) — NEVER a mutation, NEVER a recompute of the frozen
    content. Compares the manifest's recorded `source_run_created_at` against the CURRENT stored run for
    this `as_of` (never the dataset-version stamp alone, which a rebuild can reproduce byte-identically).
    `{"status": "available"|"unavailable"|"rebuilt"|"unverifiable", "detail": str|None}`.

    Fail-closed fix, part 1 (docs/goal.md J-11 step 11 ruling A4, owner 2026-08-23 — withdraws iter-10's
    "needs no change" reading): the ORIGINAL implementation short-circuited `not row.generation_json`
    straight to `{"status": "available"}`, which FABRICATES "basis intact" for a manifest with no
    recorded basis at all. Four degenerate branches — `generation_json` NULL/empty (TC-9/TC-10),
    malformed JSON (TC-11), and well-formed JSON that is not an object or omits
    `source_run_created_at` (TC-12) — all return the SAME explicit `"unverifiable"` status, never
    `"available"`, never a raised exception.

    Fail-closed fix, part 2 — ruling A4-bis (owner 2026-08-24): part 1 closed the branches above `recorded
    = generation.get("source_run_created_at")`, but left the VALUE of `recorded` unchecked: the original
    code was `if recorded is not None and recorded != current: rebuilt` / `else: available`, so a key
    present with JSON value `null` fell through to `available` (still fail-open), and an empty or
    unparseable string was reported as `rebuilt` — asserting a rebuild that was never established, by raw
    string inequality rather than a real timestamp comparison. `recorded` is now validated BEFORE any
    match/mismatch branch is reached (iter-7's ordering lesson: the fail-closed floor must sit before the
    comparison, never after) — `None`, a non-string, or an empty/whitespace-only string is `unverifiable`
    (no verifiable timestamp at all); a string that fails to parse via `datetime.fromisoformat` is
    `unverifiable` (TC-15, e.g. `"garbage"`); only a value that PARSES is re-canonicalized through the
    SAME `_utc_isoformat` helper the writer used to produce `current` (never a raw string compare) and
    then compared — equal is `available` (TC-17), unequal is `rebuilt` (TC-16). The complete status
    table (docs/goal.md A4-bis):
      absent / `null` / empty / unusable / unparseable  -> `unverifiable`
      valid timestamp != current run's                  -> `rebuilt`
      valid timestamp == current run's                  -> `available`
      no current `ScannerRun` for this as-of             -> `unavailable` (unchanged, TC-18)
    Never report `available` unless an actual recorded timestamp exists AND matches the current run."""
    current_run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == row.as_of)).first()
    if current_run is None:
        return {"status": "unavailable", "detail": "the underlying scanner run for this as-of is no longer stored"}
    if not row.generation_json:
        # NULL or empty string -- no recorded basis to compare. Fail closed: never "available".
        return {"status": "unverifiable", "detail": "no generation basis was recorded for this manifest"}
    try:
        generation = json.loads(row.generation_json)
    except (ValueError, TypeError):
        # malformed (not valid JSON) -- must not raise; fail closed the same as a missing basis.
        return {"status": "unverifiable", "detail": "the recorded generation basis is malformed and cannot be read"}
    if not isinstance(generation, dict) or "source_run_created_at" not in generation:
        # Well-formed JSON, but either not an OBJECT at all (a bare scalar/list -- `"key" in 5` raises
        # TypeError, which would escape this fail-closed guard as a 500 on the served `GET /api/compass`
        # payload) or an object missing the one field this comparison depends on. Both are the same
        # fact: a basis is recorded but cannot be used. Fail closed, never raise (ruling A4: "when
        # `generation_json` is missing, empty, or malformed, or when `source_run_created_at` is absent
        # ... must NEVER report available").
        return {"status": "unverifiable", "detail": "the recorded generation basis omits the source run timestamp"}

    recorded = generation.get("source_run_created_at")
    current = _utc_isoformat(current_run.created_at)

    # A4-bis, validated BEFORE any match/mismatch branch: `null`, a non-string, or an empty/unusable
    # string carries no verifiable timestamp at all -- fail closed, never "available", never "rebuilt"
    # by virtue of a raw string inequality against a value that was never a real timestamp.
    if recorded is None or not isinstance(recorded, str) or not recorded.strip():
        return {
            "status": "unverifiable",
            "detail": "the recorded source run timestamp is null or empty and cannot be verified",
        }
    try:
        recorded_dt = datetime.fromisoformat(recorded)
    except (ValueError, TypeError):
        # present but not parseable as the expected timestamp representation -- fail closed, never
        # "rebuilt" (that would assert a rebuild this value never actually establishes).
        return {
            "status": "unverifiable",
            "detail": "the recorded source run timestamp could not be parsed and cannot be verified",
        }
    # Re-canonicalize the PARSED value through the SAME helper the writer used to produce `current` --
    # never a raw string compare between two independently-formatted timestamps.
    recorded_canonical = _utc_isoformat(recorded_dt)
    if recorded_canonical != current:
        return {"status": "rebuilt", "detail": "the source scanner run was recreated after this manifest was frozen"}
    return {"status": "available", "detail": None}


def manifest_row_payload(row: NextSessionManifest) -> dict:
    """Re-shape a STORED `NextSessionManifest` row into the served `GET /api/compass` dict — a read,
    never a recompute (single source of truth). iter-3 (J-05/J-06): reconstructs the full freeze/
    integrity block from its split storage columns (AG-8 column-projection posture); every datetime is
    re-serialized via `_utc_isoformat` so the reconstructed bytes match what was hashed/exported at write
    time regardless of SQLite's tzinfo-dropping round-trip (TC-4/TC-9 byte-equality)."""
    return {
        "as_of": row.as_of.isoformat(),
        "version": row.version,
        "mode": row.mode,
        "frozen": row.frozen,
        "session_delta": json.loads(row.session_delta_json),
        "narrative": json.loads(row.narrative_json),
        "selection": json.loads(row.selection_json),
        # iter-28 (J-07): NULL for every row minted before this iteration ("pre-state_band era" — never
        # backfilled, AG-12) — an honest None, mirrors every other iter-3+ additive block's None default.
        "state_band": json.loads(row.state_band_json) if row.state_band_json else None,
        "comparison_cohort": json.loads(row.comparison_cohort_json) if row.comparison_cohort_json else [],
        "near_threshold_shadow": json.loads(row.near_threshold_shadow_json) if row.near_threshold_shadow_json else [],
        "content_hash": row.content_hash,
        "generation": json.loads(row.generation_json) if row.generation_json else None,
        "candidate_rule_hash": row.candidate_rule_hash,
        "candidate_rule_config": json.loads(row.candidate_rule_config_json) if row.candidate_rule_config_json else None,
        "cohort_rule_hash": row.cohort_rule_hash,
        "cohort_rule_config": json.loads(row.cohort_rule_config_json) if row.cohort_rule_config_json else None,
        "manifest_config_hash": row.manifest_config_hash,
        "manifest_config_subset": json.loads(row.manifest_config_subset_json) if row.manifest_config_subset_json else None,
        "dataset": json.loads(row.dataset_json) if row.dataset_json else None,
        "universe": json.loads(row.universe_json) if row.universe_json else None,
        "caveats": json.loads(row.caveats_json) if row.caveats_json else None,
        "prospective_eligible": row.prospective_eligible,
        "available_at_utc": _utc_isoformat(row.available_at_utc) if row.available_at_utc else None,
        "manifest_hash": row.manifest_hash,
    }
