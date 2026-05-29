"""Setup classification + candidate counting (app.engine.setups).

`classify_setup` maps the three per-stock scores + the regime label to one of the six configured
setup statuses using `config.decision_rules` cutoffs. The CRITICAL anti-goal under test: a
**Risk-off** regime gates EVERY name to watchlist-only — zero "Actionable" regardless of how
strong the scores are. `summarize_candidates` is the single place candidate counts are derived
(it counts the canonical per-stock statuses).
"""
from __future__ import annotations

from app.config import load_config
from app.engine.setups import (
    ALL_STATUSES,
    RISK_OFF_LABEL,
    classify_setup,
    summarize_candidates,
)

CFG = load_config()  # real decision_rules: actionable L80/E70/R60, extended L85/E50, watch L75, avoid 80


def _scores(leadership, entry_quality, risk):
    return {"leadership": leadership, "entry_quality": entry_quality, "risk": risk}


def test_actionable_when_strong_leader_good_entry_low_risk():
    out = classify_setup(_scores(90, 80, 40), "Risk-on", CFG)
    assert out["status"] == "Actionable"
    assert out["reason"]  # non-empty reason (explainability / J-02)


def test_risk_off_regime_gates_actionable_to_zero():
    """The critical gate: even a perfect setup is watchlist-only when the regime is Risk-off."""
    out = classify_setup(_scores(99, 99, 0), RISK_OFF_LABEL, CFG)
    assert out["status"] == "Risk-off-watchlist"
    assert out["status"] != "Actionable"


def test_risk_off_gate_holds_across_all_score_combinations():
    """No combination of scores produces Actionable while the regime is Risk-off."""
    for leadership in range(0, 101, 20):
        for entry in range(0, 101, 20):
            for risk in range(0, 101, 20):
                out = classify_setup(_scores(leadership, entry, risk), RISK_OFF_LABEL, CFG)
                assert out["status"] == "Risk-off-watchlist"
                assert out["status"] != "Actionable"


def test_avoid_when_risk_exceeds_avoid_cutoff():
    # R=85 >= avoid_risk(80); also fails the Actionable risk gate (<=60)
    out = classify_setup(_scores(90, 80, 85), "Risk-on", CFG)
    assert out["status"] == "Avoid"


def test_extended_strong_leader_poor_entry():
    # L=88 >= extended.leadership(85), E=40 < extended.entry(50)
    out = classify_setup(_scores(88, 40, 45), "Risk-on", CFG)
    assert out["status"] == "Extended"


def test_pullback_watch_leader_at_decent_entry():
    # watch (L=78 >= 75), not Actionable (L<80), entry good (E=75 >= actionable.entry 70)
    out = classify_setup(_scores(78, 75, 45), "Risk-on", CFG)
    assert out["status"] == "Pullback-watch"


def test_breakout_watch_leader_entry_not_ripe():
    # watch (L=78 >= 75), entry weak (E=40 < actionable.entry 70)
    out = classify_setup(_scores(78, 40, 45), "Risk-on", CFG)
    assert out["status"] == "Breakout-watch"


def test_weak_leadership_is_avoid():
    out = classify_setup(_scores(40, 40, 30), "Risk-on", CFG)
    assert out["status"] == "Avoid"


def test_every_status_has_a_nonempty_reason():
    cases = [
        (_scores(90, 80, 40), "Risk-on"),       # Actionable
        (_scores(99, 99, 0), RISK_OFF_LABEL),   # Risk-off-watchlist
        (_scores(90, 80, 85), "Risk-on"),       # Avoid (risk)
        (_scores(88, 40, 45), "Risk-on"),       # Extended
        (_scores(78, 75, 45), "Risk-on"),       # Pullback-watch
        (_scores(78, 40, 45), "Risk-on"),       # Breakout-watch
        (_scores(40, 40, 30), "Risk-on"),       # Avoid (weak)
    ]
    for scores, regime in cases:
        out = classify_setup(scores, regime, CFG)
        assert out["status"] in ALL_STATUSES
        assert isinstance(out["reason"], str) and out["reason"].strip()


def test_summarize_candidates_counts_canonical_statuses():
    rows = [
        {"setup": {"status": "Actionable"}},
        {"setup": {"status": "Actionable"}},
        {"setup": {"status": "Breakout-watch"}},
        {"setup": {"status": "Pullback-watch"}},
        {"setup": {"status": "Avoid"}},
    ]
    counts = summarize_candidates(rows)
    assert counts["Actionable"] == 2
    assert counts["Breakout-watch"] == 1
    assert counts["Pullback-watch"] == 1
    assert counts["Avoid"] == 1
    assert counts["Extended"] == 0
    # every canonical status is present (a number always renders on the dashboard, never missing)
    assert set(counts) == set(ALL_STATUSES)
