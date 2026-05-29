"""Setup classification — the canonical Setup status (Data Contract: app.engine.setups).

`classify_setup(scores, regime_label, config)` maps a stock's three independent scores
(Leadership / Entry Quality / Risk) plus the **regime label** to one of the six configured
setup statuses, using the cutoffs in `config.decision_rules` (anti-goal: No magic numbers —
every cutoff comes from config). The status rides on each per-stock row produced by
`scoring.score_stocks`, so there is one composition path and every view agrees.

CRITICAL gate (anti-goal: Risk-Off must gate Actionable): when the regime label is **Risk-off**,
EVERY name is gated to "Risk-off-watchlist" — zero "Actionable" — regardless of how strong the
scores are. This is unit-tested exhaustively.

Risk score direction: Risk is *danger* (higher = MORE dangerous). Actionable therefore requires
Risk **at or below** the actionable cutoff; the avoid cutoff is an upper danger bound.
`summarize_candidates` is the SINGLE place candidate counts are derived — it counts the canonical
per-stock setup statuses (iter-5's scanner must read these, never recompute them).
"""
from __future__ import annotations

from app.config import Config

# Matches the lowest label in `config.regime.labels` — the regime under which no name is taken.
RISK_OFF_LABEL = "Risk-off"

# The six configured setup statuses (the canonical vocabulary; summarize_candidates always
# reports a count for each so a number always renders on the dashboard).
ACTIONABLE = "Actionable"
BREAKOUT_WATCH = "Breakout-watch"
PULLBACK_WATCH = "Pullback-watch"
EXTENDED = "Extended"
AVOID = "Avoid"
RISK_OFF_WATCHLIST = "Risk-off-watchlist"
ALL_STATUSES = [ACTIONABLE, BREAKOUT_WATCH, PULLBACK_WATCH, EXTENDED, AVOID, RISK_OFF_WATCHLIST]

# Plain-language reason per status (explainability — never a bare status). The reason is
# enriched with the stock's top contributing component by `scoring.score_stocks`.
_REASONS = {
    ACTIONABLE: "Strong leader at a constructive entry with contained risk.",
    RISK_OFF_WATCHLIST: "Risk-off regime gates every name to watchlist-only — no Actionable setups while the market is risk-off.",
    EXTENDED: "Strong leader but the entry is extended — wait for a pullback rather than chasing.",
    PULLBACK_WATCH: "Leader near a buyable area — watching for a lower-risk pullback entry.",
    BREAKOUT_WATCH: "Leader not yet at a clean entry — watching for a breakout.",
}
_AVOID_RISK_REASON = "Risk outweighs the setup — avoid."
_AVOID_WEAK_REASON = "Leadership is too weak for a setup — avoid."


def classify_setup(scores: dict, regime_label: str, config: Config) -> dict:
    """Classify one stock's setup. `scores` carries numeric `leadership`/`entry_quality`/`risk`
    (0-100). Returns `{status, reason}`. Risk-off regime ⇒ "Risk-off-watchlist" (the gate)."""
    rules = config.decision_rules
    leadership = scores["leadership"]
    entry = scores["entry_quality"]
    risk = scores["risk"]

    # CRITICAL gate first: nothing is Actionable in a Risk-off regime.
    if regime_label == RISK_OFF_LABEL:
        return {"status": RISK_OFF_WATCHLIST, "reason": _REASONS[RISK_OFF_WATCHLIST]}

    actionable = rules.actionable
    if leadership >= actionable.leadership and entry >= actionable.entry and risk <= actionable.risk:
        return {"status": ACTIONABLE, "reason": _REASONS[ACTIONABLE]}
    if risk >= rules.avoid_risk:
        return {"status": AVOID, "reason": _AVOID_RISK_REASON}
    if leadership >= rules.extended.leadership and entry < rules.extended.entry:
        return {"status": EXTENDED, "reason": _REASONS[EXTENDED]}
    if leadership >= rules.watch.leadership:
        status = PULLBACK_WATCH if entry >= actionable.entry else BREAKOUT_WATCH
        return {"status": status, "reason": _REASONS[status]}
    return {"status": AVOID, "reason": _AVOID_WEAK_REASON}


def summarize_candidates(stock_rows: list[dict]) -> dict:
    """Count the canonical per-stock setup statuses — the SINGLE source of the dashboard's
    candidate counts. Every status is present (0 when none) so a number always renders."""
    counts = {status: 0 for status in ALL_STATUSES}
    for row in stock_rows:
        status = (row.get("setup") or {}).get("status")
        if status in counts:
            counts[status] += 1
    return counts
