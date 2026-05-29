"""label_for — the shared score→label-via-edges helper (Data Contract: app.engine.labels).

A 0-100 score maps to the label of the first edge (descending by `min`) whose `min` the score
reaches; edges are config-validated to cover 0, so a label is always found. Promoted out of
`regime.py` (iter-3 consolidation) so `regime.py`, `sectors.py`, and `themes.py` share ONE
definition instead of importing a private helper. Presentation only — it derives no canonical
value and contains no numeric literal (the edges come from config).
"""
from __future__ import annotations

from app.config import LabelEdge


def label_for(score: float, edges: list[LabelEdge]) -> str:
    """First edge (descending by `min`) whose `min` the score reaches; falls back to the lowest."""
    for edge in edges:
        if score >= edge.min:
            return edge.label
    return edges[-1].label
