"""Price-provider package + the name->provider factory.

`make_provider(name, *, api_key=...)` resolves a provider name to a concrete `PriceProvider`. The
default boot/runtime path constructs `SeedProvider` directly (offline, deterministic); the factory lets
the on-demand Data Manager FETCH path resolve the job-selected import `source` from the config
`data_manager.providers` catalog (J-33) WITHOUT moving live fetch into the boot path — so the seed stays
the reproducible default. Every live client is imported LAZILY so importing this package (on every app
boot) pulls in no live-only HTTP path unless a fetch actually runs.

Key handling (anti-goal: Import keys are env-or-session, never persisted): a key-aware provider receives
its credential ONLY via the `api_key` argument (the engine resolves it from the environment or the
pasted session key and passes it through here, request-only). A key-aware provider constructed with no
`api_key` RAISES `ProviderUnavailableError` when used — never a silent fallback. `make_provider` itself
reads no environment and stores no key.
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


def make_provider(
    name: str,
    *,
    api_key: Optional[str] = None,
    seed_dir: Optional[Union[str, Path]] = None,
) -> PriceProvider:
    """Resolve a provider `name` (a catalog `id`, or the offline `seed`) to a `PriceProvider`. The
    key-aware live clients (`tiingo`/`finnhub`/`alpha_vantage`) receive `api_key` (request-only, never
    persisted); `seed`/`yahoo`/`stooq` ignore it. Each live client is lazy-imported (only when a fetch
    runs). An unknown name raises `ValueError` — never a silent fallback (the catalog constrains the
    value upstream, and the engine validates a job's `source` against it)."""
    if name == "seed":
        return SeedProvider(seed_dir or DEFAULT_SEED_DIR)
    if name == "yahoo":
        from app.data_providers.yahoo_provider import YahooProvider  # lazy: only when a fetch runs

        return YahooProvider()
    if name == "stooq":
        from app.data_providers.stooq_provider import StooqProvider  # lazy: only when a fetch runs

        return StooqProvider()
    if name == "tiingo":
        from app.data_providers.tiingo_provider import TiingoProvider  # lazy: only when a fetch runs

        return TiingoProvider(api_key=api_key)
    if name == "finnhub":
        from app.data_providers.finnhub_provider import FinnhubProvider  # lazy: only when a fetch runs

        return FinnhubProvider(api_key=api_key)
    if name == "alpha_vantage":
        from app.data_providers.alpha_vantage_provider import AlphaVantageProvider  # lazy: only on fetch

        return AlphaVantageProvider(api_key=api_key)
    raise ValueError(f"unknown provider: {name!r}")
