#!/usr/bin/env bash
# Launch the read-only Trendora "window" MCP server (stdio transport).
#
# Self-locating: works regardless of the CLI's launch cwd. The backend config
# resolves the SQLite path relative to the repo root (not cwd), so running from
# apps/backend — as the server's own tests do — connects to the same seed DB the
# FastAPI app serves.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE/../../apps/backend"
exec .venv/bin/python -m app.mcp.server
