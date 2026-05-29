"""cross_sectional_percentiles — shared peer-ranking normalization for the per-entity scorers.

Leadership is inherently *relative*, so the stock and theme engines rank each component
CROSS-SECTIONALLY (a value's percentile among its peers) before the config-weighted blend —
the same proven approach `sectors.py` uses. This helper is the single definition shared by
`scoring.py` and `themes.py` (sectors.py keeps its own copy to avoid touching J-04 math).

Highest raw -> 1.0, lowest -> 0.0; a single value -> 1.0. Ties are broken by key so the output
is deterministic on the frozen seed. Only structural literals (0/1) — no tunable.
"""
from __future__ import annotations


def cross_sectional_percentiles(values_by_key: dict[str, float]) -> dict[str, float]:
    """Percentile in [0,1] of each key's value among the supplied peers (highest raw -> 1.0)."""
    ordered = sorted(values_by_key.items(), key=lambda kv: (kv[1], kv[0]))
    count = len(ordered)
    result: dict[str, float] = {}
    for index, (key, _) in enumerate(ordered):
        result[key] = (index / (count - 1)) if count > 1 else 1
    return result
