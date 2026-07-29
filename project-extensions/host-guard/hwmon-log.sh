#!/usr/bin/env bash
# hwmon-log.sh — forwarder. The sampler implementation moved into the framework
# (scripts/automation/host-guard/hwmon-log.sh) so every project shares one copy;
# this shim keeps existing paths and runbooks working (README, systemd units,
# muscle memory). Same CLI: {run|start|stop|status|watch}.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
exec env HOST_GUARD_ROOT="${HOST_GUARD_ROOT:-$ROOT}" \
  bash "$ROOT/scripts/automation/host-guard/hwmon-log.sh" "$@"
