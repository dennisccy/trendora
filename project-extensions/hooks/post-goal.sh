#!/usr/bin/env bash
# Trendora post-goal HOOK (project policy) — runs when every Must-have journey passes, BEFORE the
# generic goal-proposer agent is dispatched. Its only job is cheap, deterministic data prep: refresh the
# triad scan into a snapshot (`<session>/state/triad-scan.json`) the proposer reads alongside the live
# MCP tools. The continue/halt decision is made by run-goal.sh AFTER the proposer agent runs (from
# `state/proposer-result.json`) — so this hook is pure prep and returns 0 (PROJECT_HOOK no-continue).
#
# Degrades gracefully: any problem (missing venv, un-bootable DB, scan error) is NON-FATAL — it logs and
# exits 0, because the goal-proposer can still call `scan_product_triad` via MCP directly. This hook
# lives in project-extensions/ (outside the framework subtree) and is never pushed upstream.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$HERE/../../apps/backend"
OUT_DIR="${SESSION_DIR:-$HERE/../..}/state"
export TRIAD_OUT="$OUT_DIR/triad-scan.json"

if [[ ! -x "$BACKEND/.venv/bin/python" ]]; then
  echo "[post-goal] backend venv missing — skipping triad snapshot (proposer can use MCP directly)" >&2
  exit 0
fi
mkdir -p "$OUT_DIR" 2>/dev/null || true
cd "$BACKEND" || exit 0
.venv/bin/python - <<'PY' 2>&1 || { echo "[post-goal] triad scan snapshot failed (non-fatal)" >&2; exit 0; }
import json
import os

from sqlmodel import Session

from app.config import get_config
from app.db import get_engine
from app.engine.triad_scan import scan_product_triad

out_path = os.environ["TRIAD_OUT"]
with Session(get_engine()) as session:
    result = scan_product_triad(session, get_config())
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(result, fh, indent=2, default=str)
print(
    f"[post-goal] triad snapshot -> {out_path} "
    f"| cells={result['n_cells']} screened={result['n_screened']} survivors={result['n_survivors']}"
)
PY
exit 0
