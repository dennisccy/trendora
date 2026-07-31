#!/usr/bin/env bash
# test-health-url-resolution.sh — ops-hardening iter-41 (A1, TC-2): the backend health-check URL
# surfaced to the browser-qa / QA LLM dispatch must resolve to this project's actual `/api/health`
# path (Trendora namespaces every route under `/api` — `apps/backend/main.py` mounts
# `health.router` with `prefix="/api"`), never the framework's generic bare `/health` default,
# which 404s on a live, healthy backend and gets misread as "down" (iter-40's root cause #1).
#
# Two things proven:
#   1. `lib/common.sh::resolve_backend_health_url` itself — no override -> `/api/health`; an
#      explicit `CHAIN_BACKEND_HEALTH_URL` always wins (unchanged override contract).
#   2. Regression guard: none of the five `*-phase.sh` callers this iteration fixed still carry
#      the OLD inline `.../health}"` default — the exact drift that let `demo_runner.py`'s iter-39
#      fix diverge from the shell scripts in the first place (each script duplicating its own
#      inline default instead of sharing one helper).
#
# Offline, no model, <1s.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LIB="$REPO_ROOT/scripts/automation/lib/common.sh"

PASS=0
FAIL=0
assert() {
  local label="$1" result="$2"
  if [[ "$result" == "pass" ]]; then
    echo "  PASS  $label"; PASS=$((PASS+1))
  else
    echo "  FAIL  $label"; FAIL=$((FAIL+1))
  fi
}

# ── 1. No override -> the project-specific `/api/health` default ─────────────────────────────
rc=0
out=$(bash -c '
  set -euo pipefail
  unset CHAIN_BACKEND_HEALTH_URL
  source "'"$LIB"'"
  resolve_backend_health_url 8123') || rc=$?
[[ $rc -eq 0 && "$out" == "http://localhost:8123/api/health" ]] \
  && assert "default resolves to /api/health (got '$out')" "pass" \
  || assert "default resolves to /api/health (got '$out', rc=$rc)" "fail"

# ── 2. An explicit CHAIN_BACKEND_HEALTH_URL override always wins ─────────────────────────────
rc=0
out=$(bash -c '
  set -euo pipefail
  export CHAIN_BACKEND_HEALTH_URL="http://example.test/custom-health"
  source "'"$LIB"'"
  resolve_backend_health_url 8123') || rc=$?
[[ $rc -eq 0 && "$out" == "http://example.test/custom-health" ]] \
  && assert "explicit CHAIN_BACKEND_HEALTH_URL overrides the default" "pass" \
  || assert "explicit CHAIN_BACKEND_HEALTH_URL overrides the default (got '$out')" "fail"

# ── 3. Regression guard: none of the five fixed callers still carry the OLD inline default ───
OLD_PATTERN='CHAIN_BACKEND_HEALTH_URL:-http://localhost:\${?[A-Za-z_]*}?/health'
for f in browser-qa-phase.sh goal-iter-lean.sh qa-phase.sh demo-phase.sh run-phase.sh; do
  path="$REPO_ROOT/scripts/automation/$f"
  if grep -Eq "$OLD_PATTERN" "$path" 2>/dev/null; then
    assert "$f: no longer carries the old inline /health default" "fail"
  else
    assert "$f: no longer carries the old inline /health default" "pass"
  fi
  if grep -q 'resolve_backend_health_url' "$path" 2>/dev/null; then
    assert "$f: calls the shared resolve_backend_health_url helper" "pass"
  else
    assert "$f: calls the shared resolve_backend_health_url helper" "fail"
  fi
done

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[[ $FAIL -gt 0 ]] && exit 1
exit 0
