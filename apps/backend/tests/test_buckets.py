"""The single A-E bucketing function — correct letter at each config edge.

`to_bucket` is the ONLY place A-E is derived (Data Contract). Edges come from config
(buckets: A/B/C/D lower bounds; E is everything below D) — never hard-coded.
"""
from __future__ import annotations

from app.config import load_config
from app.engine.buckets import to_bucket


def test_to_bucket_at_each_config_edge():
    cfg = load_config()  # real edges: A=90, B=80, C=70, D=60
    a, b, c, d = cfg.buckets.A, cfg.buckets.B, cfg.buckets.C, cfg.buckets.D

    # exactly on each lower edge -> that bucket
    assert to_bucket(a, cfg) == "A"
    assert to_bucket(b, cfg) == "B"
    assert to_bucket(c, cfg) == "C"
    assert to_bucket(d, cfg) == "D"

    # just below each edge -> the next lower bucket
    assert to_bucket(a - 1, cfg) == "B"
    assert to_bucket(b - 1, cfg) == "C"
    assert to_bucket(c - 1, cfg) == "D"
    assert to_bucket(d - 1, cfg) == "E"  # E is everything below D


def test_to_bucket_extremes():
    cfg = load_config()
    assert to_bucket(100, cfg) == "A"
    assert to_bucket(95.5, cfg) == "A"
    assert to_bucket(0, cfg) == "E"


def test_to_bucket_honors_custom_edges():
    cfg = load_config()
    # mutate a copy of the buckets edges to prove the fn reads config, not literals
    cfg.buckets.A = 50
    cfg.buckets.B = 40
    cfg.buckets.C = 30
    cfg.buckets.D = 20
    assert to_bucket(50, cfg) == "A"
    assert to_bucket(45, cfg) == "B"
    assert to_bucket(19, cfg) == "E"
