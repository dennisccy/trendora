"""Canonical computing engine — the SINGLE source of truth for every canonical value.

Each canonical value (Market Regime, Sector score, A-E bucket, and — in later iterations —
Theme/Leadership/Entry/Risk scores) is computed in EXACTLY ONE module here and served from
exactly one endpoint (anti-goal: Single source of truth). The API and frontend only
re-format these outputs; they never recompute a score, bucket, or return.

Module map (matches the blueprint Data Contract verbatim):
  prices.py      — bars_asof: the no-lookahead boundary (date <= d) all math reads through.
  indicators.py  — pure, DB-free, deterministic indicator math (periods from config).
  buckets.py     — to_bucket: the ONLY place A-E is derived (config edges).
  regime.py      — score_regime: the Market Regime canonical value (-> /api/dashboard).
  sectors.py     — score_sectors: the Sector/industry leadership canonical value (-> /api/sectors).
"""
