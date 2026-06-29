"""Trendora MCP "window" — a READ-ONLY Model Context Protocol surface over the live computed evidence.

This package is a thin, transport-free-at-the-core window onto the SAME data Trendora's read API
serves (regime, per-stock/sector/theme scores, market phase, backtest scorecard, factor-lab /
event-study / samples). It exists so an MCP client (e.g. Claude) can READ and VERIFY the platform's
own outputs — output PARITY with the HTTP API is the whole point.

Layout:
  - ``tools``  — plain ``(session, params) -> dict`` functions that REUSE the exact engine/serving
                 functions the FastAPI routers call, so every value is byte-identical to the matching
                 ``GET /api`` endpoint. No transport, fully unit-testable.
  - ``server`` — a ``FastMCP`` stdio server ("trendora-window") whose ``@mcp.tool()`` handlers open a
                 short-lived DB session on the app's process engine and delegate to ``tools``.

READ-ONLY w.r.t. the snapshot DB by construction: nothing here exposes watchlist writes, data-manager
jobs, or any snapshot mutation. The one exception is the referee ``verify_edge``, which is read-only
against the snapshot DB and writes ONLY the append-only certified-claims ledger (a file).
"""
