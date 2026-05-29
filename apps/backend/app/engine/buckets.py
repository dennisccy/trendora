"""to_bucket — the SINGLE place an A-E bucket is derived (Data Contract: app.engine.buckets).

The A-E letter is derived EXACTLY ONCE here from a 0-100 score using the lower-bound edges in
`config.buckets` (A/B/C/D; E is everything below D). No other module — and never the API or
frontend — re-derives a bucket (anti-goal: Single source of truth). The edges live in config
(anti-goal: No magic numbers); this module contains no numeric edge literal.
"""
from __future__ import annotations

from typing import Optional

from app.config import Config, get_config


def to_bucket(score: float, config: Optional[Config] = None) -> str:
    """Map a 0-100 `score` to its A-E bucket using config edges. E is everything below D."""
    edges = (config or get_config()).buckets
    if score >= edges.A:
        return "A"
    if score >= edges.B:
        return "B"
    if score >= edges.C:
        return "C"
    if score >= edges.D:
        return "D"
    return "E"
