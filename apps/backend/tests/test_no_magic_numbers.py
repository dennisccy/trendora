"""No magic numbers in the engine calculation code (anti-goal).

Every scoring weight, threshold, decision cutoff, bucket edge, and indicator period MUST come
from config.yaml — never a literal in calculation code. This test tokenizes the four engine calc
modules and asserts:
  1. No float literal appears (every weight / cutoff in config is a float).
  2. No config-tunable integer (any MA period, RS window, ATR/52w/vol period, bucket edge, or
     regime/sector cutoff) appears as a literal — those must be read from config.
Structural integers (0/1/2/4/100 used for indexing, arithmetic, rounding precision, and the
percent unit) are not tunables and are allowed.
"""
from __future__ import annotations

import re
import tokenize
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1] / "app" / "engine"
CALC_FILES = [
    "indicators.py", "regime.py", "sectors.py", "buckets.py",
    # iter-3 calc modules — every weight/cutoff/period must come from config, never a literal.
    "scoring.py", "themes.py", "setups.py", "labels.py", "normalize.py",
    # iter-6 walk-forward calc — horizons, min_sample, history_years, asof_cadence, default_horizon,
    # and the control-group {seed, top_n, peers_per_sector} ALL come from config; the no-lookahead
    # price accessors (bars_asof / bars_after / close_on) introduce no tunable literal either.
    "forward_testing.py", "prices.py",
]

# The union of every NUMERIC tunable currently in config.yaml (periods, windows, bucket edges,
# regime/sector cutoffs, vix threshold, and the iter-3 decision-rule / theme-score cutoffs).
# None of these may be hard-coded in calc code. (85 = decision_rules.extended.leadership, new in
# iter-3; the other theme_scores/decision_rules integers reuse values already in this set.)
FORBIDDEN_INT_LITERALS = {
    14, 20, 21, 30, 45, 50, 55, 60, 63, 65, 70, 75, 80, 85, 90, 126, 150, 200, 252,
}


def _number_tokens(path: Path) -> list[str]:
    tokens: list[str] = []
    with open(path, "rb") as handle:
        for tok in tokenize.tokenize(handle.readline):
            if tok.type == tokenize.NUMBER:
                tokens.append(tok.string)
    return tokens


def test_engine_calc_code_has_no_magic_numbers():
    offenders: list[str] = []
    for filename in CALC_FILES:
        path = ENGINE_DIR / filename
        for literal in _number_tokens(path):
            lowered = literal.lower()
            if "." in literal or "e" in lowered or "j" in lowered:
                offenders.append(f"{filename}: float/complex literal {literal!r}")
                continue
            if int(literal, 0) in FORBIDDEN_INT_LITERALS:
                offenders.append(f"{filename}: tunable literal {literal!r} (must come from config)")
    assert not offenders, "magic numbers found in engine calc code:\n" + "\n".join(offenders)


# iter-5: the scanner orchestrates the canonical engines + persists snapshots — it must introduce
# NO scoring literal (it recomputes nothing) and NO hard-coded as-of date (those come from
# config.scanner.bootstrap_dates).
SCANNER_FILE = ENGINE_DIR / "scanner.py"
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def test_scanner_has_no_scoring_or_date_literals():
    source = SCANNER_FILE.read_text()
    # no hard-coded as-of date anywhere (incl. comments/strings) — dates live in config.yaml
    iso = _ISO_DATE.search(source)
    assert iso is None, f"scanner.py must not hard-code an ISO date ({iso.group(0)!r}); read config.scanner.bootstrap_dates"

    # no scoring literal: no float/complex, and no config-tunable integer
    offenders: list[str] = []
    for literal in _number_tokens(SCANNER_FILE):
        lowered = literal.lower()
        if "." in literal or "e" in lowered or "j" in lowered:
            offenders.append(f"float/complex literal {literal!r}")
        elif int(literal, 0) in FORBIDDEN_INT_LITERALS:
            offenders.append(f"tunable literal {literal!r}")
    assert not offenders, "scanner.py introduced a scoring literal:\n" + "\n".join(offenders)
