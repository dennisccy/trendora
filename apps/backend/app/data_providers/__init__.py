"""Price-provider package + the name->provider factory.

`make_provider(name)` resolves a config provider name to a concrete `PriceProvider`. The default
boot/runtime path constructs `SeedProvider` directly (offline, deterministic); the factory lets the
on-demand Data Manager FETCH path resolve the config-selected LIVE provider
(`config.data_manager.live_provider`, e.g. `stooq`) WITHOUT moving live fetch into the boot path — so
the seed stays the reproducible default. `StooqProvider` is imported lazily so importing this package
(on every app boot) does not pull in the live-only HTTP path unless a fetch actually runs.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError
from app.data_providers.seed_provider import SeedProvider, symbol_to_filename

# app/data_providers/__init__.py -> app -> backend ; the committed seed lives at backend/data/seed.
DEFAULT_SEED_DIR = Path(__file__).resolve().parents[2] / "data" / "seed"

__all__ = [
    "Bar",
    "PriceProvider",
    "ProviderUnavailableError",
    "SeedProvider",
    "symbol_to_filename",
    "make_provider",
    "DEFAULT_SEED_DIR",
]


def make_provider(name: str, *, seed_dir: Optional[Union[str, Path]] = None) -> PriceProvider:
    """Resolve a provider name to a `PriceProvider`. `seed` -> the offline `SeedProvider`
    (committed fixture); `stooq` -> the live `StooqProvider` (real EOD via httpx). An unknown name
    raises `ValueError` — never a silent fallback (the config Literal already constrains the value)."""
    if name == "seed":
        return SeedProvider(seed_dir or DEFAULT_SEED_DIR)
    if name == "stooq":
        from app.data_providers.stooq_provider import StooqProvider  # lazy: only when a fetch runs

        return StooqProvider()
    raise ValueError(f"unknown provider: {name!r}")
