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

from pathlib import Path

from app.config import REPO_ROOT
from app.engine.evidence import (
    LEDGER_PATH_ENV,
    _resolve_signal,
    build_evidence_payload,
    resolve_ledger_path,
)
from app.engine.ledger import append_entry


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
# iter-9 LOAD-BEARING INVARIANT — the LIVE canonical ledger is byte-identical (honest history intact),
# so `GET /api/evidence` proven-ness is unperturbed after the injectable-economy refactor.
# ==================================================================================================
def test_canonical_ledger_frozen_golden(monkeypatch):
    """The canonical `certified-claims.jsonl` entries are the immutable honest history the whole evidence
    layer reads. The original four (lines 1/2/4 PASS, line 3 `ma_stack` FAIL — strict Bonferroni divisors
    1..4) stay byte-identical, iter-11 (J-07) appended the FIFTH (the vcp_contraction top-decile edge at the
    NON-20 horizon 60 — PASS, strict Bonferroni divisor 5, required_p 0.010), and iter-13 (J-08) appends the
    SIXTH: the `rs_spy_3m × high_proximity` composite (multi-factor) edge @ h20, promoted to canonical (PASS,
    strict Bonferroni divisor 6, required_p 0.008333). All six are strict Bonferroni and `proven_signals`
    stays exactly `{leadership_score}` (both the h60 and the combination claims are signal-less — they MUST
    NOT enter it). This pins the canonical golden so any accidental rewrite/reorder of the prior rows — or a
    stray `signal` on the combination row — fails loudly."""
    monkeypatch.delenv(LEDGER_PATH_ENV, raising=False)
    from app.engine.ledger import read_entries

    ledger_file = REPO_ROOT / "runs/goal-session-mcp-loop/state/certified-claims.jsonl"
    entries = read_entries(str(ledger_file))

    # exactly the six honest-history entries, all strict Bonferroni with divisors 1..6 (the combination
    # promotion tightened the user-facing bar 5→6 — permanent, honest history).
    assert len(entries) == 6
    assert [e["verdict"]["status"] for e in entries] == ["PASS", "PASS", "FAIL", "PASS", "PASS", "PASS"]
    assert [e["verdict"]["deflation_divisor"] for e in entries] == [1, 2, 3, 4, 5, 6]
    assert all(e["verdict"]["deflation"] == "bonferroni" for e in entries)
    # the 6th row is a `combination` (no `factor` selector → None); the prior five are unchanged
    assert [e["claim"].get("factor") for e in entries] == [
        "leadership_score", None, "ma_stack", "vcp_contraction", "vcp_contraction", None,
    ]
    assert [e["claim"].get("kind") for e in entries] == [
        "factor", "event-study", "factor", "factor", "factor", "combination",
    ]

    # the 5th (iter-11 J-07) entry: the vcp_contraction top-decile edge at the NON-20 horizon 60 — PASS,
    # signal-less, verdict bytes FROZEN (the displayed h60 edge/p/control byte-match anti-goal #3).
    h60 = entries[4]
    assert h60["claim"]["horizon"] == 60
    assert h60["claim"]["decile"] == 10
    assert "signal" not in h60["claim"]  # signal-less — never lights a /stocks inline score badge
    assert h60["verdict"]["status"] == "PASS"
    assert h60["verdict"]["required_p"] == 0.01
    assert h60["verdict"]["holdout_edge"] == 0.08909719710495288
    assert h60["verdict"]["control_excess"] == 0.08909719710495288
    assert h60["verdict"]["p_value"] == 0.0004997501249375312

    # the 6th (iter-13 J-08) entry: the rs_spy_3m × high_proximity composite edge @ h20 — PASS, signal-less,
    # verdict bytes FROZEN (the displayed combination edge/p/control byte-match anti-goal #3).
    combo = entries[5]
    assert combo["claim"]["kind"] == "combination"
    assert combo["claim"]["cohort"] == "composite"
    assert combo["claim"]["condition"] == ["rs_spy_3m:top:quintile", "high_proximity:top:tertile"]
    assert combo["claim"]["horizon"] == 20
    assert combo["claim"]["direction"] == "positive"
    assert combo["claim"]["ledger"] == "canonical"
    assert "signal" not in combo["claim"]  # signal-less — never lights a /stocks inline score badge
    assert combo["verdict"]["status"] == "PASS"
    assert combo["verdict"]["required_p"] == 0.008333333333333333
    assert combo["verdict"]["holdout_edge"] == 0.046931901591708916
    assert combo["verdict"]["control_excess"] == 0.046931901591708916
    assert combo["verdict"]["p_value"] == 0.0009995002498750624

    # the projected payload: 6 claim rows, and the ONLY inline-badge signal is STILL leadership_score
    # (the signal-less h60 + combination claims MUST NOT enter proven_signals — J-01/J-02/J-03 unaffected).
    payload = build_evidence_payload(str(ledger_file))
    assert len(payload["claims"]) == 6
    assert set(payload["proven_signals"].keys()) == {"leadership_score"}
    proven = payload["proven_signals"]["leadership_score"]
    assert proven["proven"] is True
    assert proven["claim"]["decile"] == 10 and proven["claim"]["horizon"] == 20
