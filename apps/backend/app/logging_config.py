"""Root-logger configuration for the Trendora backend (ops-hardening iter-39).

Before this module existed, the app never called `logging.basicConfig` / added any handler
anywhere (confirmed live, iter-38: a direct read of `apps/backend/main.py` showed only bare
`logging.getLogger(...)` calls, no handler/level setup anywhere in the app). Every `trendora.*`
logger (created via `logging.getLogger("trendora.xxx")`) therefore had no handler anywhere in
its propagation chain up to the root logger, so Python's global `logging.lastResort` fallback
(a `StreamHandler(sys.stderr)` PINNED to WARNING — see the stdlib `logging` module) was the ONLY
thing ever writing those records anywhere. That is why routine `.info()` liveness lines were
silently dropped: an `.info`-level version of the J-07 finalize-tail `cache_ctx` liveness line
(`data_manager.py`, `_refresh_ingest_aggregates`) never once appeared in `logs/backend.log`
across a full drilled job, forcing it to masquerade as `.warning` instead (iter-38 workaround).

`configure_app_logging()` attaches one `StreamHandler` to the ROOT logger at INFO level.
`scripts/start-backend.sh` already redirects the launched process's stdout+stderr into
`logs/backend.log` (`>> "$LOG_FILE" 2>&1`), so this module decides ONLY the level/handler —
never a destination file path — and every `trendora.*` `.info()`+ call now reaches that same
persistent logfile with no further wiring. Idempotent (a second call is a no-op) so importing
this module more than once, or under pytest's own logging setup, never doubles output or
clobbers a caller's own root-logger configuration.

CORRECTION (iter-39 audit, B1): the paragraph above overstated "no handler anywhere" — it was
established by reading `main.py` alone. TWO modules DO attach a handler to their own logger and
have since iter-18: `app/api/backtest.py` (`trendora.backtest`) and `app/mcp/tools.py`
(`trendora.mcp_backtest`), each deliberately keeping `propagate = True` so `caplog`-based tests
still observe their records. Those loggers were therefore never affected by the `lastResort`
gap — and once a root handler exists, their records reach BOTH handlers, so every
`backtest_timing` / `query_backtest_timing` line was written to `logs/backend.log` TWICE
(confirmed live in this repo's own log: one bare copy from the module handler, one formatted
copy from the root handler, same millisecond). `_already_handled_by_own_logger` below suppresses
the root handler's duplicate copy, so a logger that carries its own handler keeps exactly its
pre-existing single line (bare format, unchanged for every existing consumer/grep of it) while
every other `trendora.*` logger gains the INFO-level output this module was added to provide."""
from __future__ import annotations

import logging

_CONFIGURED = False


def _already_handled_by_own_logger(record: logging.LogRecord) -> bool:
    """True when `record` was already emitted by a handler attached to its own logger (or to an
    ancestor below the root) — in which case this module's root handler must NOT emit a second
    copy. Walks the propagation chain the same way `logging.Logger.callHandlers` does, stopping
    before the root logger itself."""
    logger = logging.getLogger(record.name)
    while logger is not None and logger.parent is not None:  # stop before the root logger
        if logger.handlers:
            return True
        if not logger.propagate:
            return False
        logger = logger.parent
    return False


def configure_app_logging(level: int = logging.INFO) -> None:
    """Idempotently attach a root-logger `StreamHandler` at `level` so every `trendora.*`
    logger's calls at `level`+ reach the process's stderr (and therefore `logs/backend.log`
    under the launch scripts) instead of being silently dropped by Python's WARNING-only
    `logging.lastResort` fallback. Safe to call more than once (e.g. re-imported under a test
    runner) — only the FIRST call has any effect."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    root = logging.getLogger()
    # widen the root logger's own level only if it would otherwise filter OUT this handler's
    # level (a root at the default WARNING would swallow INFO records before they ever reach
    # the handler below) — never narrow it past what a caller may have already configured.
    if root.level == logging.NOTSET or root.level > level:
        root.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    # iter-39 audit (B1): never double-write a record a logger's OWN handler already emitted
    # (`trendora.backtest`, `trendora.mcp_backtest` — see the module docstring's CORRECTION).
    handler.addFilter(lambda record: not _already_handled_by_own_logger(record))
    root.addHandler(handler)
    _CONFIGURED = True
