#!/usr/bin/env bash
# test-frontend-restart-reprobe.sh — ops-hardening iter-42 (B4, TC-9): after a mid-run
# backend/frontend restart, `ensure_services_running` (lib/common.sh) must give the frontend a
# bounded, corruption-aware re-probe (`_wait_for_frontend_ready`) before returning, instead of
# trusting its own internal start-retry budget's verdict alone.
#
# The gap iter-41's own audit found (B4): two restart paths in the regression/replay flow
# (lib/replay-lane.sh's REL-5 replay retry and REL-14 preflight retry) call ONLY
# `ensure_services_running` after a mid-run restart and then immediately retry/probe once, with no
# re-probe of their own — so a frontend that is genuinely still recompiling reads as unreachable and
# the whole regression run goes silently all-SKIP on one premature timeout (iter-40's actual
# incident: 000 at one caller's 90s probe, ready in 0s from a DIFFERENT caller twenty minutes later).
#
# Sources the REAL lib/common.sh and stubs its two frontend-startup callees
# (`_start_service_with_retries`, `_wait_for_frontend_ready`) so the test proves
# `ensure_services_running`'s OWN orchestration logic, not a re-implementation of either callee.
#
# Offline, no model, no real network/process, <1s.
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

[[ -f "$LIB" ]] && bash -n "$LIB" && assert "lib/common.sh exists and parses (bash -n)" pass \
  || { assert "lib/common.sh exists and parses (bash -n)" fail; echo "RESULT: $PASS passed, $((FAIL)) failed"; exit 1; }

# ── 1. Frontend still not ready after ensure_services_running's own budget: a bounded re-probe
#      recovers it. Proves _wait_for_frontend_ready is GENUINELY invoked (the iter-37 "assert the
#      condition was actually live" lesson), not merely present in the source.
out="$(
  (
    set -euo pipefail
    # shellcheck source=/dev/null
    source "$LIB"
    # Simulates the internal start-retry budget expiring with the frontend still not answering
    # (rc=1, the documented "failed" case).
    _start_service_with_retries() { return 1; }
    REPROBE_LOG="$(mktemp)"
    # Simulates the frontend becoming ready DURING the bounded re-probe window — the exact iter-40
    # shape (ready shortly after the restart's own budget gave up).
    _wait_for_frontend_ready() {
      echo "called url=$1 name=$2 max_wait=$3 tag=$4" >> "$REPROBE_LOG"
      return 0
    }
    export QA_FRONTEND_REQUIRED="yes"
    export QA_FRONTEND_URL="http://localhost:19999"
    export QA_FRONTEND_START_CMD="true"
    ensure_services_running
    echo "QA_FRONTEND_UP=$QA_FRONTEND_UP"
    echo "REPROBE_CALLS=$(wc -l < "$REPROBE_LOG")"
    cat "$REPROBE_LOG"
  )
)"
echo "$out" | grep -q '^QA_FRONTEND_UP=yes$' \
  && assert "ensure_services_running: bounded re-probe recovers a still-down frontend (QA_FRONTEND_UP=yes)" pass \
  || { assert "ensure_services_running: bounded re-probe recovers a still-down frontend (QA_FRONTEND_UP=yes)" fail; echo "    got: $out"; }
echo "$out" | grep -q '^REPROBE_CALLS=1$' \
  && assert "ensure_services_running: the re-probe is GENUINELY invoked exactly once (live, not dead code)" pass \
  || { assert "ensure_services_running: the re-probe is GENUINELY invoked exactly once (live, not dead code)" fail; echo "    got: $out"; }
echo "$out" | grep -q 'url=http://localhost:19999 name=frontend max_wait=90' \
  && assert "ensure_services_running: re-probe called with the frontend URL + a bounded (90s) window" pass \
  || { assert "ensure_services_running: re-probe called with the frontend URL + a bounded (90s) window" fail; echo "    got: $out"; }

# ── 2. Frontend genuinely never comes up — the re-probe timeout is HONEST (QA_FRONTEND_UP stays
#      "no"), never silently promoted to "yes".
out2="$(
  (
    set -euo pipefail
    source "$LIB"
    _start_service_with_retries() { return 1; }
    _wait_for_frontend_ready() { return 1; }   # still not ready after the bounded re-probe
    export QA_FRONTEND_REQUIRED="yes"
    export QA_FRONTEND_URL="http://localhost:19999"
    export QA_FRONTEND_START_CMD="true"
    ensure_services_running
    echo "QA_FRONTEND_UP=$QA_FRONTEND_UP"
  )
)"
[[ "$out2" == "QA_FRONTEND_UP=no" ]] \
  && assert "ensure_services_running: a genuinely down frontend stays QA_FRONTEND_UP=no (honest, not a silent promotion)" pass \
  || { assert "ensure_services_running: a genuinely down frontend stays QA_FRONTEND_UP=no (honest, not a silent promotion)" fail; echo "    got: $out2"; }

# ── 3. _start_service_with_retries already returns 0 (ready) — the re-probe is SKIPPED (no
#      redundant wait for the common, already-healthy case).
out3="$(
  (
    set -euo pipefail
    source "$LIB"
    _start_service_with_retries() { return 0; }
    REPROBE_LOG3="$(mktemp)"
    _wait_for_frontend_ready() { echo called >> "$REPROBE_LOG3"; return 0; }
    export QA_FRONTEND_REQUIRED="yes"
    export QA_FRONTEND_URL="http://localhost:19999"
    export QA_FRONTEND_START_CMD="true"
    ensure_services_running
    echo "QA_FRONTEND_UP=$QA_FRONTEND_UP"
    echo "REPROBE_CALLS=$(wc -l < "$REPROBE_LOG3")"
  )
)"
echo "$out3" | grep -q '^QA_FRONTEND_UP=yes$' && echo "$out3" | grep -q '^REPROBE_CALLS=0$' \
  && assert "ensure_services_running: an already-healthy frontend skips the re-probe entirely" pass \
  || { assert "ensure_services_running: an already-healthy frontend skips the re-probe entirely" fail; echo "    got: $out3"; }

# ── 4. QA_FRONTEND_REQUIRED != yes — the frontend block (and the re-probe) never engage at all.
out4="$(
  (
    set -euo pipefail
    source "$LIB"
    _start_service_with_retries() { echo "SHOULD NOT BE CALLED" >&2; return 1; }
    _wait_for_frontend_ready() { echo "SHOULD NOT BE CALLED" >&2; return 1; }
    export QA_FRONTEND_REQUIRED="no"
    export QA_FRONTEND_URL="http://localhost:19999"
    export QA_FRONTEND_START_CMD="true"
    ensure_services_running
    echo "QA_FRONTEND_UP=$QA_FRONTEND_UP"
  )
)"
[[ "$out4" == "QA_FRONTEND_UP=unknown" ]] \
  && assert "ensure_services_running: QA_FRONTEND_REQUIRED=no -> frontend block (and re-probe) never engage" pass \
  || { assert "ensure_services_running: QA_FRONTEND_REQUIRED=no -> frontend block (and re-probe) never engage" fail; echo "    got: $out4"; }

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[[ $FAIL -gt 0 ]] && exit 1
exit 0
