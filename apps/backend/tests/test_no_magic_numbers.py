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

import tokenize
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1] / "app" / "engine"
CALC_FILES = ["indicators.py", "regime.py", "sectors.py", "buckets.py"]

# The union of every NUMERIC tunable currently in config.yaml (periods, windows, bucket edges,
# regime + sector cutoffs, vix threshold). None of these may be hard-coded in calc code.
FORBIDDEN_INT_LITERALS = {
    14, 20, 21, 30, 45, 50, 55, 60, 63, 65, 70, 75, 80, 90, 126, 150, 200, 252,
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
