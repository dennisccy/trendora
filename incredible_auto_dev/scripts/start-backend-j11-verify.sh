#!/usr/bin/env bash
# start-backend-j11-verify.sh — goal-market-compass iter-23: the ONE remaining J-11 acceptance
# objective is a real backend boot against a DISPOSABLE clone, never the canonical
# apps/backend/data/trendora.db (docs/goal.md "OWNER RULING — J-11 database recovery accepted; one
# final serving verification remains", owner 2026-08-27, item 3: "The canonical repaired DB stays
# protected... Backend/frontend/browser verification runs against the disposable verification DB only").
#
# Testing Requirements' "Error cases": "a launch attempt that omits the TRENDORA_CONFIG override (i.e.
# would default to the canonical DB) must be refused before any browser/replay execution proceeds." This
# script is that refusal, checked via the SAME app.engine.j11_disposable_clone.assert_launch_targets_clone
# the disposable-clone CLI script and its tests already use — never a second, drifting implementation of
# the check. Only after it passes does this script exec the project's STANDARD launch script
# (scripts/start-backend.sh) unmodified, so AG-10's host-guard caps still apply exactly as they do for
# every other boot.
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -z "${TRENDORA_CONFIG:-}" ]]; then
  echo "start-backend-j11-verify.sh: TRENDORA_CONFIG is not set -- refusing to boot (a boot without it" >&2
  echo "targets the CANONICAL database). Export TRENDORA_CONFIG to the disposable verification config" >&2
  echo "produced by scripts/run_j11_disposable_clone.py before running this script." >&2
  exit 1
fi

"$REPO_ROOT/apps/backend/.venv/bin/python" -c "
import sys
sys.path.insert(0, '$REPO_ROOT/apps/backend')
from app.config import load_config
from app.engine.j11_disposable_clone import assert_launch_targets_clone, ClonePreconditionError

canonical_url = load_config('$REPO_ROOT/config.yaml').database.url
try:
    result = assert_launch_targets_clone('$TRENDORA_CONFIG', canonical_url)
except ClonePreconditionError as exc:
    print(f'start-backend-j11-verify.sh: REFUSING to boot -- {exc}', file=sys.stderr)
    sys.exit(1)
print(f'start-backend-j11-verify.sh: launch guard OK -- booting against {result[\"database_url\"]!r}', file=sys.stderr)
"

exec "$REPO_ROOT/scripts/start-backend.sh"
