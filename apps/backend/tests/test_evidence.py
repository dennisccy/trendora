"""Read-side evidence resolver units (goal-mcp-loop iter-1).

`app.engine.evidence` is the SINGLE source of displayed proven-ness — it RECOMPUTES NOTHING; it projects
the append-only certified-claims ledger into the read-only `/api/evidence` payload. These tests pin the
fail-safe contract:
  - absent/empty ledger => empty payload (every signal reads "Not yet proven");
  - a `verdict.status == "PASS"` entry that NAMES a signal => that signal is Proven;
  - a `FAIL` / `INSUFFICIENT` entry => the signal stays NOT proven (even when its signal can be derived);
  - a PASS entry WITHOUT an explicit `signal` key: a SCORE-COLUMN factor cohort DERIVES `signal = factor`
    and is surfaced as proven (iter-2 defense-in-depth, non-spoofable); any OTHER signal-less cohort maps
    to no UI signal (fail-safe — no KeyError, stays "Not yet proven");
  - forward-walk MONITORING records are excluded from the claim list (they re-score, they aren't claims);
  - `resolve_ledger_path()` honors the `TRENDORA_LEDGER_PATH` env override, else the config default
    resolved against the repo root.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlmodel import Session, select

import app.engine.forward_testing as forward_testing
import app.engine.market_phase as market_phase
from app.config import REPO_ROOT, load_config
from app.db import create_db_and_tables, make_engine
from app.engine.evidence import (
    LEDGER_PATH_ENV,
    _resolve_signal,
    build_evidence_payload,
    resolve_ledger_path,
)
from app.engine.ledger import append_entry
from app.models import ForwardReturn, ScannerResult, ScannerRun


def _pass_entry(signal: str | None, factor: str = "leadership_score") -> dict:
    """A certified (PASS) ledger entry over the `factor` cohort. When `signal` is given it is stamped on
    the claim verbatim (the iter-2+ gate convention — the Evidence-Claim JSON carries `signal`); when None
    it mirrors a claim that omitted the field, exercising the read-side `_resolve_signal` derivation
    (a score-column `factor` self-maps; any other `factor` stays dark)."""
    claim = {
        "kind": "factor",
        "factor": factor,
        "slice_kind": "decile",
        "decile": 10,
        "horizon": 20,
        "direction": "positive",
    }
    if signal is not None:
        claim["signal"] = signal
    return {
        "claim": claim,
        "register_date": "2024-06-01",
        "horizon": 20,
        "cohort_n": 42,
        "control_n": 40,
        "verdict": {
            "status": "PASS",
            "reason": "certified out-of-sample",
            "holdout_edge": 0.031,
            "control_excess": 0.018,
            "p_value": 0.004,
        },
    }


def _regime_event_study_entry() -> dict:
    """A certified (PASS) ledger entry mirroring the REAL iter-4 2nd ledger entry: the Breakout-watch
    setup's event-study cohort sliced to the named `Risk-on` regime (pooled view, horizon 20). It
    deliberately carries NO `signal` key — it backs no per-stock score badge, it is regime-conditioned
    evidence in its own right (so it must NOT enter `proven_signals` nor overwrite `leadership_score`)."""
    return {
        "claim": {
            "kind": "event-study",
            "subject": "Breakout-watch",
            "slice_kind": "regime",
            "regime": "Risk-on",
            "view": "pooled",
            "horizon": 20,
            "direction": "positive",
        },
        "register_date": "2026-06-30",
        "horizon": 20,
        "cohort_n": 4720,
        "control_n": 414,
        "verdict": {
            "status": "PASS",
            "reason": "certified out-of-sample (Risk-on)",
            "holdout_edge": 0.06124590639955655,
            "control_excess": 0.06124590639955655,
            "p_value": 0.0004997501249375312,
        },
    }


def _verdict_entry(signal: str, status: str) -> dict:
    return {
        "claim": {"kind": "factor", "factor": signal, "signal": signal, "horizon": 20},
        "register_date": "2024-06-01",
        "horizon": 20,
        "cohort_n": 12,
        "control_n": 12,
        "verdict": {"status": status, "reason": f"{status} out-of-sample", "control_excess": -0.004},
    }


def _vcp_contraction_pass_entry() -> dict:
    """The REAL iter-8 4th ledger entry: the `vcp_contraction` top-decile (D10) horizon-20 factor cohort,
    certified PASS by the referee at trial #4 (Bonferroni divisor 4, required_p 0.0125). It deliberately
    carries NO `signal` key — `vcp_contraction` is a plain (volatility-family) factor, NOT a score column,
    so `_resolve_signal` returns None and it backs the Research factor lab + the Evidence ledger ONLY (never
    a `/stocks` inline score badge). Verdict values byte-match `certified-claims.jsonl` line 4."""
    return {
        "claim": {
            "kind": "factor",
            "factor": "vcp_contraction",
            "slice_kind": "decile",
            "decile": 10,
            "horizon": 20,
            "direction": "positive",
        },
        "register_date": "2026-06-30",
        "horizon": 20,
        "cohort_n": 12297,
        "control_n": 1075,
        "verdict": {
            "status": "PASS",
            "reason": "certified: holdout edge +0.0333 beats the control out-of-sample and is significant after multiple-testing deflation (p=0.01149 < alpha/4=0.0125)",
            "holdout_edge": 0.03330492745744988,
            "control_excess": 0.03330492745744988,
            "p_value": 0.011494252873563218,
            "deflation_divisor": 4,
            "required_p": 0.0125,
        },
    }


def _vcp_contraction_h60_pass_entry() -> dict:
    """The REAL iter-11 (J-07) 5th ledger entry: the `vcp_contraction` top-decile (D10) cohort at the NON-20
    forward-return horizon 60, promoted to the canonical ledger (`"ledger":"canonical"`) and certified PASS at
    trial #5 (strict Bonferroni divisor 5, required_p 0.010). Like the h20 row it carries NO `signal` key —
    it backs the Research factor lab + the Evidence ledger ONLY (never a `/stocks` inline score badge). Verdict
    values byte-match `certified-claims.jsonl` line 5 (the displayed-numbers-are-correct anti-goal)."""
    return {
        "claim": {
            "kind": "factor",
            "factor": "vcp_contraction",
            "slice_kind": "decile",
            "decile": 10,
            "horizon": 60,
            "direction": "positive",
            "ledger": "canonical",
        },
        "register_date": "2026-07-01",
        "horizon": 60,
        "cohort_n": 12026,
        "control_n": 1055,
        "verdict": {
            "status": "PASS",
            "reason": "certified: holdout edge +0.0891 beats the control out-of-sample and is significant after multiple-testing deflation (p=0.0004998 < alpha/5=0.01)",
            "holdout_edge": 0.08909719710495288,
            "control_excess": 0.08909719710495288,
            "p_value": 0.0004997501249375312,
            "deflation": "bonferroni",
            "deflation_divisor": 5,
            "required_p": 0.01,
        },
    }


def _ma_stack_fail_entry() -> dict:
    """The REAL iter-8 3rd ledger entry: the `ma_stack` top-decile (D10) horizon-20 factor cohort the
    referee REJECTED (a decent holdout edge but p=0.01949 >= alpha/3=0.01667). A signal-less FAIL row — it
    is audit-listed but `proven == False` and adds no UI signal. Verdict values byte-match
    `certified-claims.jsonl` line 3."""
    return {
        "claim": {
            "kind": "factor",
            "factor": "ma_stack",
            "slice_kind": "decile",
            "decile": 10,
            "horizon": 20,
            "direction": "positive",
        },
        "register_date": "2026-06-30",
        "horizon": 20,
        "cohort_n": 12297,
        "control_n": 1106,
        "verdict": {
            "status": "FAIL",
            "reason": "holdout edge +0.02619 is not significant after multiple-testing deflation (p=0.01949 >= alpha/3=0.01667)",
            "holdout_edge": 0.026192275085938167,
            "control_excess": 0.026192275085938167,
            "p_value": 0.019490254872563718,
            "deflation_divisor": 3,
            "required_p": 0.016666666666666666,
        },
    }


def _combination_pass_entry() -> dict:
    """The REAL iter-13 (J-08) 6th ledger entry: the `rs_spy_3m × high_proximity` composite (multi-factor)
    cohort @ horizon 20, promoted to the canonical ledger (`"ledger":"canonical"`) and certified PASS at
    trial #6 (strict Bonferroni divisor 6, required_p 0.008333). Its `kind` is `combination` (NOT a score
    column) and it carries NO `signal` key, so `_resolve_signal` returns None and it backs the Multi-factor
    combination lab + the Evidence ledger ONLY (never a `/stocks` inline score badge). The `condition` legs
    are the FULL `factor:side:quantile` strings. Verdict values byte-match `certified-claims.jsonl` line 6
    (the displayed-numbers-are-correct anti-goal)."""
    return {
        "claim": {
            "kind": "combination",
            "cohort": "composite",
            "condition": ["rs_spy_3m:top:quintile", "high_proximity:top:tertile"],
            "horizon": 20,
            "direction": "positive",
            "ledger": "canonical",
        },
        "register_date": "2026-07-01",
        "horizon": 20,
        "cohort_n": 23929,
        "control_n": 1102,
        "verdict": {
            "status": "PASS",
            "reason": "certified: holdout edge +0.04693 beats the control out-of-sample and is significant after multiple-testing deflation (p=0.0009995 < alpha/6=0.008333)",
            "holdout_edge": 0.046931901591708916,
            "control_excess": 0.046931901591708916,
            "p_value": 0.0009995002498750624,
            "deflation": "bonferroni",
            "deflation_divisor": 6,
            "required_p": 0.008333333333333333,
        },
    }


def test_build_payload_absent_ledger_is_empty(tmp_path):
    missing = tmp_path / "nope" / "certified-claims.jsonl"
    payload = build_evidence_payload(str(missing))
    assert payload == {"claims": [], "proven_signals": {}}


def test_build_payload_pass_entry_marks_signal_proven(tmp_path):
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry("leadership_score"))
    payload = build_evidence_payload(str(ledger))

    assert list(payload["proven_signals"].keys()) == ["leadership_score"]
    proven = payload["proven_signals"]["leadership_score"]
    assert proven["proven"] is True
    assert proven["signal"] == "leadership_score"
    assert proven["register_date"] == "2024-06-01"
    assert proven["horizon"] == 20
    assert proven["cohort_n"] == 42
    assert proven["control_n"] == 40
    # verdict fields are re-displayed VERBATIM (no recompute) — these are exactly what the J-02 proof panel reads
    assert proven["verdict"]["status"] == "PASS"
    assert proven["verdict"]["control_excess"] == 0.018
    assert proven["verdict"]["holdout_edge"] == 0.031
    assert proven["verdict"]["p_value"] == 0.004
    # forward-walk score-to-date is the layout placeholder (None until a certified iteration monitors it)
    assert proven["forward_walk"] is None
    # hypothesis = the cohort selectors, read verbatim
    assert proven["claim"]["factor"] == "leadership_score"
    assert proven["claim"]["decile"] == 10

    assert len(payload["claims"]) == 1
    assert payload["claims"][0] is not proven or payload["claims"][0] == proven


def test_build_payload_regime_event_study_claim_adds_no_signal(tmp_path):
    # iter-4 (J-04 / J-05 no-regression): the LIVE 2-entry ledger
    # [leadership_score PASS (factor), Breakout-watch × Risk-on PASS (event-study)]. The regime-conditioned
    # event-study claim is shown as its OWN audit row (regime-labeled) but carries NO `signal`, so it must
    # NOT enter `proven_signals` nor overwrite `leadership_score` — the leadership score stays the SOLE
    # proven signal (J-01/J-02/J-03/J-05 must not regress). Every displayed number is read VERBATIM.
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry("leadership_score"))
    append_entry(str(ledger), _regime_event_study_entry())
    payload = build_evidence_payload(str(ledger))

    # proven_signals is keyed ONLY on leadership_score — the regime claim adds NO signal
    assert list(payload["proven_signals"].keys()) == ["leadership_score"]
    assert payload["proven_signals"]["leadership_score"]["proven"] is True
    assert payload["proven_signals"]["leadership_score"]["signal"] == "leadership_score"

    # both claims are audit-listed; the regime row is present, PROVEN, signal-less, and regime-labeled
    assert len(payload["claims"]) == 2
    regime_rows = [row for row in payload["claims"] if row["claim"].get("kind") == "event-study"]
    assert len(regime_rows) == 1
    regime_row = regime_rows[0]
    assert regime_row["proven"] is True
    assert regime_row["signal"] is None
    assert regime_row["claim"]["regime"] == "Risk-on"
    assert regime_row["claim"]["subject"] == "Breakout-watch"
    assert regime_row["claim"]["slice_kind"] == "regime"
    # displayed numbers are re-displayed VERBATIM (the J-04 API-correctness contract)
    assert regime_row["verdict"]["status"] == "PASS"
    assert regime_row["verdict"]["holdout_edge"] == 0.06124590639955655
    assert regime_row["verdict"]["control_excess"] == 0.06124590639955655
    assert regime_row["verdict"]["p_value"] == 0.0004997501249375312
    assert regime_row["register_date"] == "2026-06-30"

    # the resolver maps the event-study regime claim to NO UI signal (it stays off the inline badges)…
    assert _resolve_signal(_regime_event_study_entry()["claim"]) is None
    # …while the leadership score column still self-maps (unchanged)
    assert _resolve_signal(_pass_entry("leadership_score")["claim"]) == "leadership_score"


def test_build_payload_vcp_contraction_factor_cohort_post_certification(tmp_path):
    # iter-8 (J-06): the FULL post-certification 4-entry ledger
    #   [leadership_score PASS (score factor), Breakout-watch × Risk-on PASS (event-study),
    #    ma_stack D10 FAIL (plain factor), vcp_contraction D10 PASS (plain factor)].
    # The vcp_contraction top-decile cohort is a signal-less PLAIN-factor edge: it is audit-listed + proven
    # but carries NO `signal` (`_resolve_signal -> None`), so it backs the Research factor lab + Evidence
    # ONLY and MUST NOT enter `proven_signals` (J-01/J-02/J-03 unaffected — `leadership_score` stays the SOLE
    # proven signal). The rejected ma_stack cohort stays `proven == False`. Every displayed number is read
    # VERBATIM (the J-06 API-correctness / displayed-numbers-are-correct contract).
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry("leadership_score"))
    append_entry(str(ledger), _regime_event_study_entry())
    append_entry(str(ledger), _ma_stack_fail_entry())
    append_entry(str(ledger), _vcp_contraction_pass_entry())
    payload = build_evidence_payload(str(ledger))

    # the vcp_contraction (and ma_stack) plain-factor claims add NO signal — proven_signals stays EXACTLY
    # {leadership_score} (the iter-1 lesson asserted here so a stray `signal` stamp would fail loudly).
    assert list(payload["proven_signals"].keys()) == ["leadership_score"]
    assert payload["proven_signals"]["leadership_score"]["signal"] == "leadership_score"

    # all four originals are audit-listed (no forward-walk record), in ledger order
    assert len(payload["claims"]) == 4
    factor_rows = {
        row["claim"].get("factor"): row
        for row in payload["claims"]
        if row["claim"].get("kind") == "factor"
    }

    # the vcp_contraction row: proven, signal-less, selectors verbatim, verdict bytes verbatim
    vcp = factor_rows["vcp_contraction"]
    assert vcp["proven"] is True
    assert vcp["signal"] is None
    assert vcp["claim"]["slice_kind"] == "decile"
    assert vcp["claim"]["decile"] == 10
    assert vcp["claim"]["horizon"] == 20
    assert vcp["claim"]["direction"] == "positive"
    assert vcp["register_date"] == "2026-06-30"
    assert vcp["verdict"]["status"] == "PASS"
    assert vcp["verdict"]["holdout_edge"] == 0.03330492745744988
    assert vcp["verdict"]["control_excess"] == 0.03330492745744988
    assert vcp["verdict"]["p_value"] == 0.011494252873563218

    # the ma_stack row: audit-listed but NOT proven (a FAIL never reads "Proven"), signal-less
    ma = factor_rows["ma_stack"]
    assert ma["proven"] is False
    assert ma["signal"] is None
    assert ma["verdict"]["status"] == "FAIL"
    assert ma["verdict"]["control_excess"] == 0.026192275085938167

    # the resolver maps the vcp_contraction plain-factor cohort to NO UI signal (it is not a score column)
    assert _resolve_signal(_vcp_contraction_pass_entry()["claim"]) is None
    assert _resolve_signal(_ma_stack_fail_entry()["claim"]) is None


def test_build_payload_vcp_contraction_h60_factor_cohort_post_certification(tmp_path):
    # iter-11 (J-07): the FULL post-promotion 5-entry ledger
    #   [leadership_score PASS (score factor), Breakout-watch × Risk-on PASS (event-study),
    #    ma_stack D10 FAIL (plain factor), vcp_contraction D10 h20 PASS, vcp_contraction D10 h60 PASS].
    # The NEW 5th entry is the same signal-less plain-factor edge as the h20 row but at the NON-20 horizon 60:
    # it is audit-listed + proven, carries NO `signal`, and MUST NOT enter `proven_signals` (leadership_score
    # stays the SOLE proven signal — J-01/J-02/J-03 unaffected). Both vcp_contraction rows are served with
    # their OWN horizon verbatim so the per-horizon factor-lab badge deep-links to the right one. Every
    # displayed number is read VERBATIM (the J-07 correctness / displayed-numbers-are-correct contract).
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry("leadership_score"))
    append_entry(str(ledger), _regime_event_study_entry())
    append_entry(str(ledger), _ma_stack_fail_entry())
    append_entry(str(ledger), _vcp_contraction_pass_entry())
    append_entry(str(ledger), _vcp_contraction_h60_pass_entry())
    payload = build_evidence_payload(str(ledger))

    # proven_signals stays EXACTLY {leadership_score} — the signal-less h60 claim adds NO signal (iter-1 lesson)
    assert list(payload["proven_signals"].keys()) == ["leadership_score"]
    assert payload["proven_signals"]["leadership_score"]["signal"] == "leadership_score"

    # all five originals are audit-listed (no forward-walk record), in ledger order
    assert len(payload["claims"]) == 5

    # the two vcp_contraction rows are served DISTINCTLY by horizon (the per-horizon badge relies on this)
    vcp_rows = [
        row
        for row in payload["claims"]
        if row["claim"].get("kind") == "factor" and row["claim"].get("factor") == "vcp_contraction"
    ]
    assert len(vcp_rows) == 2
    horizons = sorted(row["claim"]["horizon"] for row in vcp_rows)
    assert horizons == [20, 60]

    # the NEW h60 row: proven, signal-less, selectors verbatim, verdict bytes verbatim (byte-match the ledger)
    h60 = next(row for row in vcp_rows if row["claim"]["horizon"] == 60)
    assert h60["proven"] is True
    assert h60["signal"] is None
    assert h60["claim"]["slice_kind"] == "decile"
    assert h60["claim"]["decile"] == 10
    assert h60["claim"]["direction"] == "positive"
    assert h60["register_date"] == "2026-07-01"
    assert h60["cohort_n"] == 12026
    assert h60["control_n"] == 1055
    assert h60["verdict"]["status"] == "PASS"
    assert h60["verdict"]["holdout_edge"] == 0.08909719710495288
    assert h60["verdict"]["control_excess"] == 0.08909719710495288
    assert h60["verdict"]["p_value"] == 0.0004997501249375312
    assert h60["verdict"]["required_p"] == 0.01

    # the h60 plain-factor cohort still maps to NO UI signal (it is not a score column — anti-goal #1)
    assert _resolve_signal(_vcp_contraction_h60_pass_entry()["claim"]) is None


def test_build_payload_combination_composite_cohort_post_promotion(tmp_path):
    # iter-13 (J-08): the FULL post-promotion 6-entry ledger
    #   [leadership_score PASS (score factor), Breakout-watch × Risk-on PASS (event-study),
    #    ma_stack D10 FAIL (plain factor), vcp_contraction D10 h20 PASS, vcp_contraction D10 h60 PASS,
    #    rs_spy_3m × high_proximity composite PASS (combination)].
    # The NEW 6th entry is a signal-less MULTI-FACTOR composite edge (kind=combination): it is audit-listed +
    # proven, carries NO `signal`, and MUST NOT enter `proven_signals` (leadership_score stays the SOLE proven
    # signal — J-01/J-02/J-03 unaffected). It is served with its `condition` legs + horizon verbatim so the
    # combination-lab badge + the /evidence row read the SAME payload. Every displayed number is read VERBATIM
    # (the J-08 correctness / displayed-numbers-are-correct contract — no UI/endpoint recompute).
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry("leadership_score"))
    append_entry(str(ledger), _regime_event_study_entry())
    append_entry(str(ledger), _ma_stack_fail_entry())
    append_entry(str(ledger), _vcp_contraction_pass_entry())
    append_entry(str(ledger), _vcp_contraction_h60_pass_entry())
    append_entry(str(ledger), _combination_pass_entry())
    payload = build_evidence_payload(str(ledger))

    # proven_signals stays EXACTLY {leadership_score} — the signal-less combination claim adds NO signal
    # (the anti-goal #1 / iter-1 lesson asserted here so a stray `signal` stamp would fail loudly).
    assert list(payload["proven_signals"].keys()) == ["leadership_score"]
    assert payload["proven_signals"]["leadership_score"]["signal"] == "leadership_score"

    # all six originals are audit-listed (no forward-walk record), in ledger order
    assert len(payload["claims"]) == 6

    # the NEW combination row: proven, signal-less, selectors + verdict bytes verbatim (byte-match the ledger)
    combo = next(row for row in payload["claims"] if row["claim"].get("kind") == "combination")
    assert combo["proven"] is True
    assert combo["signal"] is None
    assert combo["claim"]["cohort"] == "composite"
    assert combo["claim"]["condition"] == ["rs_spy_3m:top:quintile", "high_proximity:top:tertile"]
    assert combo["claim"]["horizon"] == 20
    assert combo["claim"]["direction"] == "positive"
    assert combo["claim"]["ledger"] == "canonical"
    assert "signal" not in combo["claim"]  # signal-less — never lights a /stocks inline score badge
    assert combo["register_date"] == "2026-07-01"
    assert combo["cohort_n"] == 23929
    assert combo["control_n"] == 1102
    assert combo["verdict"]["status"] == "PASS"
    assert combo["verdict"]["holdout_edge"] == 0.046931901591708916
    assert combo["verdict"]["control_excess"] == 0.046931901591708916
    assert combo["verdict"]["p_value"] == 0.0009995002498750624
    assert combo["verdict"]["required_p"] == 0.008333333333333333
    assert combo["verdict"]["deflation_divisor"] == 6

    # the combination cohort maps to NO UI signal (it is not a score column — anti-goal #1)
    assert _resolve_signal(_combination_pass_entry()["claim"]) is None


def test_build_payload_fail_and_insufficient_not_proven(tmp_path):
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _verdict_entry("entry_quality_score", "FAIL"))
    append_entry(str(ledger), _verdict_entry("risk_score", "INSUFFICIENT"))
    payload = build_evidence_payload(str(ledger))

    # neither a FAIL nor an INSUFFICIENT verdict surfaces a proven signal (fail-safe)
    assert payload["proven_signals"] == {}
    # both rows are still audit-listed on the ledger page, honestly carrying their verdict + proven=False
    assert len(payload["claims"]) == 2
    statuses = {row["verdict"]["status"]: row["proven"] for row in payload["claims"]}
    assert statuses == {"FAIL": False, "INSUFFICIENT": False}


def test_build_payload_pass_score_column_without_signal_derives(tmp_path):
    # iter-2 read-side derivation: a PASS over a SCORE-COLUMN factor cohort that omitted an explicit
    # `signal` still lights its badge — `_resolve_signal` derives `signal = factor` (factor key is
    # byte-identical to the UI signal key). Defense-in-depth so a future claim that forgets the field
    # does not silently go dark.
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry(None, factor="leadership_score"))
    payload = build_evidence_payload(str(ledger))

    assert list(payload["proven_signals"].keys()) == ["leadership_score"]
    proven = payload["proven_signals"]["leadership_score"]
    assert proven["proven"] is True
    assert proven["signal"] == "leadership_score"     # derived, not explicitly stamped
    assert proven["claim"].get("signal") is None      # the underlying claim still carries NO signal key


def test_build_payload_pass_non_score_factor_without_signal_stays_dark(tmp_path):
    # FAIL-SAFE preserved: a signal-less PASS over a NON-score factor cohort (only the three score columns
    # self-map) must NOT KeyError and must NOT light up any UI signal — it stays "Not yet proven".
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry(None, factor="rs_spy_3m"))
    payload = build_evidence_payload(str(ledger))

    assert payload["proven_signals"] == {}            # a non-score cohort never self-maps to a UI signal
    assert len(payload["claims"]) == 1
    row = payload["claims"][0]
    assert row["proven"] is True                      # the verdict IS a PASS (honestly shown on the ledger)
    assert row["signal"] is None                      # but it maps to NO UI signal key (fail-safe)


def test_build_payload_non_pass_score_column_not_proven_even_when_signal_derives(tmp_path):
    # proven-ness flows SOLELY from verdict.status == PASS: a FAIL over a score-column factor cohort whose
    # signal WOULD derive must still NOT surface as a proven signal (derivation is display-routing only).
    ledger = tmp_path / "certified-claims.jsonl"
    fail_entry = _pass_entry(None, factor="leadership_score")
    fail_entry["verdict"]["status"] = "FAIL"
    fail_entry["verdict"]["reason"] = "did not beat the control out-of-sample"
    append_entry(str(ledger), fail_entry)
    payload = build_evidence_payload(str(ledger))

    assert payload["proven_signals"] == {}            # a non-PASS verdict is never proven, derived signal or not
    row = payload["claims"][0]
    assert row["signal"] == "leadership_score"        # the signal still DERIVES (for the audit-listed row)
    assert row["proven"] is False                     # but proven-ness requires a PASS


def test_build_payload_excludes_forward_walk_monitoring_records(tmp_path):
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry("leadership_score"))
    append_entry(str(ledger), {"type": "forward_walk", "claim": {"signal": "leadership_score"},
                               "verdict": {"status": "PASS"}})
    payload = build_evidence_payload(str(ledger))

    # the monitoring re-score is NOT a new claim row (it re-scores an existing claim)
    assert len(payload["claims"]) == 1
    assert payload["claims"][0]["register_date"] == "2024-06-01"
    # the original certified claim still proves its signal
    assert list(payload["proven_signals"].keys()) == ["leadership_score"]


# ==================================================================================================
# additive `expectations` field (iter-41, J-25) — session-provided vs. session-omitted paths
# ==================================================================================================
@pytest.fixture()
def evidence_dd_engine(tmp_path, monkeypatch):
    """A minimal hand-built engine with ONE resolvable leadership_score observation at horizon 20, dated
    into a monkeypatched 'Expansion' phase — just enough for `compute_drawdown_expectations` (fully unit-
    tested on its own in test_forward_testing.py) to return a non-None payload for the SAME
    decile-10/horizon-20 claim shape `_pass_entry` builds above."""
    engine = make_engine(f"sqlite:///{tmp_path / 'evidence_dd.db'}")
    create_db_and_tables(engine)
    d = date(2025, 1, 10)
    with Session(engine) as session:
        run = ScannerRun(
            asof_date=d, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(run)
        session.flush()
        session.add(ScannerResult(
            run_id=run.id, ticker="AAA", name="AAA", sector="Technology",
            leadership_score=90.0, leadership_bucket="A",
            entry_quality_score=50.0, entry_quality_bucket="C",
            risk_score=50.0, risk_bucket="C",
            setup_status="Actionable", rank=1, record_json="{}",
        ))
        session.add(ForwardReturn(
            run_id=run.id, symbol="AAA", horizon=20, asof_date=d, entry_close=100.0,
            measured_date=d + timedelta(days=40), realized_return=0.02,
            max_drawdown=-0.05, underwater_days=3, time_to_recover_days=5,
        ))
        session.commit()

    def _fake_ctx(session=None, as_of=None, config=None):
        return {d.isoformat(): {"phase": "Expansion", "severity": 10.0, "p_bear": 0.05}}

    monkeypatch.setattr(market_phase, "phase_context_by_date", _fake_ctx)
    return engine


def test_build_payload_session_omitted_no_expectations_key(tmp_path):
    """DEFAULT (session=None, EVERY existing call site's shape): a claim row carries NO `expectations`
    key at all — not even `None` — the literal 'absent' the DoD requires, proving the ~13 existing
    positional-only call sites (incl. the frozen-golden test) see a byte-identical row."""
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry("leadership_score"))
    payload = build_evidence_payload(str(ledger))
    assert "expectations" not in payload["claims"][0]


def test_build_payload_session_provided_attaches_expectations(tmp_path, evidence_dd_engine):
    """When a session IS provided (the real `/evidence` route), a resolvable claim's row additively
    carries `expectations` — read straight from `compute_drawdown_expectations`, never a second
    computation, never a client-visible recompute."""
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry("leadership_score"))  # factor=leadership_score, decile=10, h=20
    with Session(evidence_dd_engine) as session:
        payload = build_evidence_payload(str(ledger), session=session, config=load_config())
    row = payload["claims"][0]
    assert "expectations" in row
    assert row["expectations"]["horizon"] == 20
    exp_phase = next(p for p in row["expectations"]["by_phase"] if p["phase"] == "Expansion")
    assert exp_phase["n"] == 1


# ops-hardening iter-49 AUDIT (finding T1) — TC-3's drawdown leg covered the column-projection change
# (`test_research_streaming.py`, `_factor_decile_observations` vs a pinned full-entity reference) but NOT
# the OTHER change shipped in the same iteration: the new, additive `phases` parameter on
# `compute_drawdown_expectations`/`_cached`. The ingest finalize warm loop
# (`data_manager._refresh_ingest_aggregates`) is the ONE caller that threads a pre-computed all-history
# timeline through it, and every `event_study_cache` payload `/api/evidence` later SERVES is written by
# exactly that path — so a divergence between the threaded and the self-computed timeline would silently
# persist wrong drawdown/dry-spell figures behind a "proven" claim (AG-3). Nothing in the suite asserted
# that equivalence; these two proofs pin it at both entry points.
def test_compute_drawdown_expectations_precomputed_phases_is_byte_identical(evidence_dd_engine):
    """The uncached producer returns a byte-identical payload whether the caller threads a pre-computed
    `phase_context_by_date(session, as_of=None, config=cfg)` timeline (the ingest finalize warm loop's
    shape) or lets it self-compute (`phases=None`, every other caller's shape)."""
    cfg = load_config()
    claim = _pass_entry("leadership_score")["claim"]
    with Session(evidence_dd_engine) as session:
        self_computed = forward_testing.compute_drawdown_expectations(session, claim, cfg)
        precomputed = market_phase.phase_context_by_date(session, as_of=None, config=cfg)
        threaded = forward_testing.compute_drawdown_expectations(session, claim, cfg, phases=precomputed)
    assert self_computed is not None, "fixture sanity: this claim must resolve to a real payload"
    assert self_computed["by_phase"], "fixture sanity: the payload must carry real per-phase rows"
    assert json.dumps(threaded, sort_keys=True) == json.dumps(self_computed, sort_keys=True)


def test_drawdown_expectations_cached_persists_same_payload_when_phases_threaded(evidence_dd_engine):
    """The CACHED entry point the ingest warm actually calls persists (and returns) the SAME payload a
    fresh, `phases`-less canonical computation produces — the stored `event_study_cache` row `/api/evidence`
    serves is not a second, divergent computation."""
    cfg = load_config()
    claim = _pass_entry("leadership_score")["claim"]
    with Session(evidence_dd_engine) as session:
        canonical = forward_testing.compute_drawdown_expectations(session, claim, cfg)
        precomputed = market_phase.phase_context_by_date(session, as_of=None, config=cfg)
        # MISS -> computes with the threaded timeline and persists under the current dataset version.
        written = forward_testing.compute_drawdown_expectations_cached(
            session, claim, cfg, phases=precomputed
        )
        # HIT -> re-serves the persisted row (proving what was STORED, not just what was returned).
        served = forward_testing.compute_drawdown_expectations_cached(session, claim, cfg)
    assert canonical is not None, "fixture sanity: this claim must resolve to a real payload"
    assert json.dumps(written, sort_keys=True) == json.dumps(canonical, sort_keys=True)
    assert json.dumps(served, sort_keys=True) == json.dumps(canonical, sort_keys=True)


def test_build_payload_session_provided_unresolvable_claim_no_expectations_key(tmp_path, evidence_dd_engine):
    """A session IS provided but the claim's cohort is unresolvable (an unknown factor) — the row still
    carries NO `expectations` key (graceful, matches the session-omitted case; never a crash, never a
    fabricated panel)."""
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry("leadership_score", factor="does_not_exist_factor"))
    with Session(evidence_dd_engine) as session:
        payload = build_evidence_payload(str(ledger), session=session, config=load_config())
    assert "expectations" not in payload["claims"][0]
    # ops-hardening iter-29 (AG-8) error-case regression: the pre-existing HONEST-None path (an
    # unresolvable cohort, `compute_drawdown_expectations` returning None WITHOUT raising) must stay
    # byte-unchanged by the new per-claim failure guard below — no `expectations_status` field either.
    # This is what proves the new field is ADDITIVE (only on a caught exception), never a replacement of
    # the pre-existing silent-omission behavior.
    assert "expectations_status" not in payload["claims"][0]


# ==================================================================================================
# ops-hardening iter-29 (AG-8) — a per-claim `compute_drawdown_expectations_cached` failure
# (`MemoryError` or otherwise) must never abort the response for the OTHER claims: the failing claim's row
# omits `expectations` and carries the new `expectations_status: "unavailable"` field; every other claim's
# row is byte-unchanged (isolate-and-continue, mirroring the EXISTING per-claim `MemoryError`-then-continue
# convention `data_manager.py`'s drawdown-expectations ingest warm loop already uses near
# `data_manager.py:3361` — TC-4).
# ==================================================================================================
@pytest.fixture()
def evidence_dd_two_claims_engine(tmp_path, monkeypatch):
    """TWO independently resolvable claims in ONE fixture, dedicated (not a mutation of `evidence_dd_engine`
    above, so its own two existing tests stay untouched): AAA (leadership_score, decile 10, horizon 20 —
    byte-identical setup to `evidence_dd_engine`) plus BBB (entry_quality_score, decile 10, horizon 20) in
    the SAME run/date. BBB's high `entry_quality_score` / baseline `leadership_score` (and AAA's inverse)
    mean each name is the SOLE decile-10 member of its OWN factor's single-observation cohort — adding BBB
    does not disturb AAA's leadership_score decile-10 membership (still {AAA} alone, n=1)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'evidence_dd_two.db'}")
    create_db_and_tables(engine)
    d = date(2025, 1, 10)
    with Session(engine) as session:
        run = ScannerRun(
            asof_date=d, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(run)
        session.flush()
        session.add(ScannerResult(
            run_id=run.id, ticker="AAA", name="AAA", sector="Technology",
            leadership_score=90.0, leadership_bucket="A",
            entry_quality_score=50.0, entry_quality_bucket="C",
            risk_score=50.0, risk_bucket="C",
            setup_status="Actionable", rank=1, record_json="{}",
        ))
        session.add(ForwardReturn(
            run_id=run.id, symbol="AAA", horizon=20, asof_date=d, entry_close=100.0,
            measured_date=d + timedelta(days=40), realized_return=0.02,
            max_drawdown=-0.05, underwater_days=3, time_to_recover_days=5,
        ))
        session.add(ScannerResult(
            run_id=run.id, ticker="BBB", name="BBB", sector="Technology",
            leadership_score=50.0, leadership_bucket="C",
            entry_quality_score=90.0, entry_quality_bucket="A",
            risk_score=50.0, risk_bucket="C",
            setup_status="Actionable", rank=2, record_json="{}",
        ))
        session.add(ForwardReturn(
            run_id=run.id, symbol="BBB", horizon=20, asof_date=d, entry_close=100.0,
            measured_date=d + timedelta(days=40), realized_return=0.03,
            max_drawdown=-0.04, underwater_days=2, time_to_recover_days=4,
        ))
        session.commit()

    def _fake_ctx(session=None, as_of=None, config=None):
        return {d.isoformat(): {"phase": "Expansion", "severity": 10.0, "p_bear": 0.05}}

    monkeypatch.setattr(market_phase, "phase_context_by_date", _fake_ctx)
    return engine


def test_build_payload_per_claim_compute_failure_is_isolated(
    tmp_path, evidence_dd_two_claims_engine, monkeypatch
):
    """TC-4: `compute_drawdown_expectations_cached` monkeypatched to raise `MemoryError` for exactly ONE of
    two resolvable claims. The failing claim's row carries `expectations_status: "unavailable"` and no
    `expectations` key; the OTHER claim's row carries its normal `expectations` key, fully unaffected —
    proving one claim's compute failure never blanks the rest of the `/evidence` response."""
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry("leadership_score"))
    append_entry(str(ledger), _pass_entry("entry_quality_score", factor="entry_quality_score"))

    # ops-hardening iter-47: `build_evidence_payload` now calls the SERVING wrapper
    # `compute_drawdown_expectations_cached_with_status` (audit B2, serve-stale-behind-a-label), not the
    # plain cached function directly — the monkeypatch target moves with it.
    real_cached = forward_testing.compute_drawdown_expectations_cached_with_status

    def _flaky_cached(session, claim, config=None):
        if claim.get("factor") == "leadership_score":
            raise MemoryError("synthetic TC-4 failure")
        return real_cached(session, claim, config)

    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached_with_status", _flaky_cached)

    with Session(evidence_dd_two_claims_engine) as session:
        payload = build_evidence_payload(str(ledger), session=session, config=load_config())

    rows = payload["claims"]
    assert len(rows) == 2
    failed_row = next(r for r in rows if r["claim"]["factor"] == "leadership_score")
    ok_row = next(r for r in rows if r["claim"]["factor"] == "entry_quality_score")

    assert failed_row.get("expectations_status") == "unavailable"
    assert "expectations" not in failed_row

    assert "expectations_status" not in ok_row
    assert "expectations" in ok_row
    assert ok_row["expectations"]["horizon"] == 20
    exp_phase = next(p for p in ok_row["expectations"]["by_phase"] if p["phase"] == "Expansion")
    assert exp_phase["n"] == 1


# ==================================================================================================
# ops-hardening iter-47 (audit B2) — the serve-stale-behind-a-label fix: `GET /api/evidence` must survive
# an UNRELATED concurrent ingest (any new forward_returns row bumps every claim's dataset-version stamp)
# without falling onto the multi-minute cold-recompute tail. `build_evidence_payload` now calls
# `compute_drawdown_expectations_cached_with_status`; a claim serving a stale (last-good) generation
# additively carries `expectations_status: "refreshing"` alongside its (real, honest) `expectations` —
# never mixed with the newer generation's fields.
# ==================================================================================================
def test_build_payload_serves_stale_expectations_as_refreshing_after_dataset_change(
    tmp_path, evidence_dd_engine, monkeypatch,
):
    """TC-3: after the dataset changes (an unrelated new forward_returns row lands, exactly like a
    concurrent ingest), the row's `expectations` still renders — the LAST-GOOD pre-change payload,
    byte-identical to what was served before the change — with an ADDITIVE `expectations_status:
    "refreshing"` label. The pre-existing 'ready' shape (no status key at all) is unaffected when there is
    no dataset change."""
    import app.db as db_module
    import app.engine.forward_testing as forward_testing_module

    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry("leadership_score"))
    cfg = load_config()

    with Session(evidence_dd_engine) as session:
        before = build_evidence_payload(str(ledger), session=session, config=cfg)
    before_row = before["claims"][0]
    assert "expectations_status" not in before_row  # the pre-existing 'ready' shape: no status key at all

    # change the dataset: a second, UNRELATED symbol's forward return on the SAME run (mirrors a concurrent
    # ingest landing a new row that has nothing to do with this claim's own cohort membership).
    with Session(evidence_dd_engine) as session:
        run = session.exec(select(ScannerRun)).one()
        session.add(ScannerResult(
            run_id=run.id, ticker="ZZZ", name="ZZZ", sector="Technology",
            leadership_score=10.0, leadership_bucket="C",
            entry_quality_score=50.0, entry_quality_bucket="C",
            risk_score=50.0, risk_bucket="C",
            setup_status="Actionable", rank=2, record_json="{}",
        ))
        session.add(ForwardReturn(
            run_id=run.id, symbol="ZZZ", horizon=20, asof_date=run.asof_date, entry_close=100.0,
            measured_date=run.asof_date + timedelta(days=40), realized_return=-0.01,
            max_drawdown=-0.09, underwater_days=7, time_to_recover_days=None,
        ))
        session.commit()

    prev_engine = db_module._engine
    db_module.set_engine(evidence_dd_engine)
    monkeypatch.setattr(forward_testing_module.threading, "Thread", _NoOpThread)
    # iter-47 AUDIT (T1): `_NoOpThread.start()` never runs `_spawn_drawdown_expectations_rewarm`'s worker
    # body, so its `finally: _REWARM_IN_FLIGHT = False` never fires and the module GLOBAL would stay True
    # for the rest of the pytest process — poisoning the single-flight guard for every later test in the
    # SAME session (proven: with this line absent, running this file before
    # `test_forward_testing.py::test_cached_with_status_dataset_change_serves_stale_refreshing_then_settles_ready`
    # makes that test fail with `assert 'refreshing' == 'ready'`). `monkeypatch.setattr` records the
    # pre-test value and restores it at teardown, so the guard is always left as it was found.
    monkeypatch.setattr(forward_testing_module, "_REWARM_IN_FLIGHT", False)
    try:
        with Session(evidence_dd_engine) as session:
            after = build_evidence_payload(str(ledger), session=session, config=cfg)
    finally:
        db_module.set_engine(prev_engine)

    after_row = after["claims"][0]
    assert after_row.get("expectations_status") == "refreshing"
    assert "expectations" in after_row
    assert after_row["expectations"] == before_row["expectations"], (
        "a refreshing row must serve the LAST-GOOD pre-change generation verbatim — never a mix"
    )


class _NoOpThread:
    """A `threading.Thread` stand-in whose `start()` does NOTHING — this test only needs to prove the
    REQUEST-PATH behavior (immediate stale-serve + label), not the background re-warm's own eventual-
    consistency mechanics (already proven directly in test_forward_testing.py)."""

    def __init__(self, target=None, args=(), kwargs=None, daemon=None, name=None):
        pass

    def start(self):
        pass


def test_resolve_ledger_path_env_override(tmp_path, monkeypatch):
    override = tmp_path / "override-ledger.jsonl"
    monkeypatch.setenv(LEDGER_PATH_ENV, str(override))
    assert resolve_ledger_path() == str(override)


def test_resolve_ledger_path_config_default(monkeypatch):
    monkeypatch.delenv(LEDGER_PATH_ENV, raising=False)
    resolved = resolve_ledger_path()
    # the SAME file the post-decompose gate writes, resolved absolute against the repo root
    assert resolved == str(REPO_ROOT / "runs/goal-session-mcp-loop/state/certified-claims.jsonl")
    assert Path(resolved).is_absolute()


# ==================================================================================================
# iter-18 SANCTIONED REFRESH — the LIVE canonical ledger was REGENERATED from scratch on the 30-year
# basis (goal.md "Data-basis change (sanctioned ledger reset)"): the SAME pre-registered 7-claim family
# replayed in historical order (verbatim selectors, strict Bonferroni divisors 1..7 — including the
# ma_stack re-test), each through verify_edge(ledger="canonical") against the rebuilt DB
# (register_date 2026-07-03). On the deep multi-regime sealed holdout NONE of the retired-window edges
# reproduced — every claim honestly FAILED (several with positive in-sample edges going NEGATIVE
# out-of-sample: exactly the overfit signature the deep basis was expected to expose; goal.md §F). The
# retired verdicts remain auditable via git history. proven_signals is EMPTY: every score/edge surface
# reads "Not yet proven" until a claim independently re-certifies on this basis (anti-goal #1).
# ==================================================================================================
def test_canonical_ledger_frozen_golden(monkeypatch):
    """Pins the REGENERATED canonical ledger byte-for-byte (the one sanctioned refresh): 7 entries,
    verbatim historical selectors in historical order, strict Bonferroni divisors 1..7, register_date
    2026-07-03, ALL verdicts FAIL, and the projected payload proves NOTHING (proven_signals == {}) —
    no retired edge value (+21.34% / +6.36% / +8.91% / +4.69% / +6.12% / p=0.0004998) survives
    anywhere. Any accidental rewrite/reorder — or a resurrected stale PASS — fails loudly."""
    monkeypatch.delenv(LEDGER_PATH_ENV, raising=False)
    from app.engine.ledger import read_entries

    ledger_file = REPO_ROOT / "runs/goal-session-mcp-loop/state/certified-claims.jsonl"
    entries = read_entries(str(ledger_file))

    # exactly the seven replayed entries, in the verbatim historical order, all strict Bonferroni 1..7,
    # all registered on the regeneration run date, all honest FAILs on the 30-year basis.
    assert len(entries) == 7
    assert [e["verdict"]["status"] for e in entries] == ["FAIL"] * 7
    assert [e["verdict"]["deflation_divisor"] for e in entries] == [1, 2, 3, 4, 5, 6, 7]
    assert all(e["verdict"]["deflation"] == "bonferroni" for e in entries)
    assert all(e["register_date"] == "2026-07-03" for e in entries)
    assert [e["claim"].get("factor") for e in entries] == [
        "leadership_score", None, "ma_stack", "vcp_contraction", "vcp_contraction", None, "rs_spy_3m",
    ]
    assert [e["claim"].get("kind") for e in entries] == [
        "factor", "event-study", "factor", "factor", "factor", "combination", "factor",
    ]
    # the verbatim selector shapes carried through the replay (incl. #1's signal stamp and the explicit
    # canonical routing keys claims #5-#7 carried from their historical promotion gates).
    assert entries[0]["claim"]["signal"] == "leadership_score"
    assert entries[1]["claim"]["regime"] == "Risk-on" and entries[1]["claim"]["subject"] == "Breakout-watch"
    assert entries[5]["claim"]["condition"] == ["rs_spy_3m:top:quintile", "high_proximity:top:tertile"]
    assert all(entries[i]["claim"].get("ledger") == "canonical" for i in (4, 5, 6))

    # exact regenerated verdict pins (the displayed-numbers-are-correct anti-goal — every /evidence
    # row byte-matches these): p-values, holdout edges, required_p, and the cohort/control accounting.
    expected = [
        # (p_value, holdout_edge, required_p, cohort_n, control_n)
        (0.5352323838080959, -0.00031360673077383193, 0.05, 15485, 390),
        (0.9460269865067467, -0.006842313773714405, 0.025, 5989, 146),
        (0.2768615692153923, 0.002061821804493209, 0.016666666666666666, 15485, 377),
        (0.95952023988006, -0.0037732016043003124, 0.0125, 15485, 381),
        (0.9995002498750625, -0.016363899205616317, 0.01, 15322, 378),
        (0.4942528735632184, 8.030187730850894e-05, 0.008333333333333333, 30768, 384),
        (0.9045477261369316, -0.014155225763191797, 0.0071428571428571435, 15263, 383),
    ]
    for e, (p, edge, req, cohort_n, control_n) in zip(entries, expected):
        assert e["verdict"]["p_value"] == p
        assert e["verdict"]["holdout_edge"] == edge
        assert e["verdict"]["control_excess"] == edge  # the referee reports the same holdout excess
        assert e["verdict"]["required_p"] == req
        assert e["cohort_n"] == cohort_n
        assert e["control_n"] == control_n
        # the honest referee ran with real power (a FAIL, never an INSUFFICIENT refusal)
        assert e["verdict"]["holdout_dates"] >= 5
        assert e["verdict"]["seed"] == 20240601  # determinism preserved

    # the projected payload: 7 audit-listed rows, NOTHING proven — every badge reads "Not yet proven"
    # (anti-goal #1: no unbacked "Proven"; the reset never resurrects a stale edge).
    payload = build_evidence_payload(str(ledger_file))
    assert len(payload["claims"]) == 7
    assert payload["proven_signals"] == {}
    assert all(row["proven"] is False for row in payload["claims"])
