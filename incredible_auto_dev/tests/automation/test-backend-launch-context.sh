#!/usr/bin/env bash
# test-backend-launch-context.sh — iter-24 fix: goal-iter-lean.sh must make every backend-launch
# call site (initial boot, SPEED-2/3 forked boot, REL-5 restart-after-failure, REL-14 preflight
# retry, the quota-retry pre-hook) preserve the SAME CHAIN_START_BACKEND_CMD/TRENDORA_CONFIG
# override an iteration established, never independently re-derive the bare
# `bash scripts/start-backend.sh` default once an override is in force, and fail closed BEFORE any
# backend process spawns when the expected override is missing/mismatched.
#
# Root cause reproduced here (goal.md OWNER RULING item 3; iter-23 eval "The violation,
# precisely"): `goal-iter-lean.sh:256-257` (pre-fix) resolved BACKEND_START_CMD from
# CHAIN_START_BACKEND_CMD INDEPENDENTLY inside run_browser_qa_boot_and_replay every time that
# function ran, with no cross-check against what an earlier launch point in the same run had
# already established. A disposable-clone override active for one part of iteration 23 never
# reached the routine J-01/J-04 regression re-test in the SAME run, which silently fell back to the
# bare default and booted the protected canonical database.
#
# The fix (lib/common.sh): goal_iter_lock_backend_launch_context resolves the launch command ONCE
# per run and locks it into GOAL_ITER_BACKEND_LAUNCH_CMD; ensure_services_running -- the single
# chokepoint every self-boot path (initial boot, REL-5, REL-14, the quota-retry pre-hook) already
# funnels through -- refuses (fail closed, before _start_service_with_retries ever runs) when a
# call's QA_BACKEND_START_CMD has drifted from that locked value.
#
# Per iter-22b's lesson, this test exercises the REAL lib/common.sh code (sourced, not
# reimplemented) and stubs only its callee `_start_service_with_retries` (the function that would
# actually spawn a process and open a log file) as a SPY -- same technique
# tests/automation/test-frontend-restart-reprobe.sh already uses to prove
# ensure_services_running's OWN orchestration logic. The stub start commands used below
# (`echo ...`) never touch a real port, process, or file -- and never reference
# apps/backend/data/trendora.db -- so this test cannot boot or write to the canonical database
# (TC-9; the NOTES section of docs/phases/goal-market-compass-iter-24.md explicitly permits an
# inert stub command for a pure launch-context unit test).
#
# Offline, no model, no real network/process/service, <1s.
#
# To reproduce iteration 23's defect against the PRE-fix tree (TC-5) and confirm this same test
# passes against the fixed tree (TC-6), see the dev handoff
# (docs/handoffs/goal-market-compass-iter-24-dev.md) for the exact `git stash` / restore commands
# and their outputs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CM="$REPO_ROOT/scripts/automation/lib/common.sh"
GIL="$REPO_ROOT/scripts/automation/goal-iter-lean.sh"

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

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

[[ -f "$CM" ]] && bash -n "$CM" && assert "lib/common.sh exists and parses (bash -n)" pass \
  || { assert "lib/common.sh exists and parses (bash -n)" fail; echo "RESULT: $PASS passed, $((FAIL)) failed"; exit 1; }
[[ -f "$GIL" ]] && bash -n "$GIL" && assert "goal-iter-lean.sh exists and parses (bash -n)" pass \
  || { assert "goal-iter-lean.sh exists and parses (bash -n)" fail; echo "RESULT: $PASS passed, $((FAIL)) failed"; exit 1; }

OVERRIDE_CMD="echo stub-disposable-clone-backend"
BARE_DEFAULT_CMD="bash $REPO_ROOT/scripts/start-backend.sh"

# ── A. TC-1/TC-3: an override locked at run start is reused BYTE-IDENTICAL by a later launch
#      point (simulating REL-5's restart-after-failure / REL-14's preflight retry, both of which
#      call only ensure_services_running -- see lib/replay-lane.sh) -- never silently swapped for
#      the bare default.
outA="$(
  (
    set -euo pipefail
    # shellcheck source=/dev/null
    source "$CM"
    ITER_DIR="$WORK/iterA"
    export CHAIN_START_BACKEND_CMD="$OVERRIDE_CMD"
    goal_iter_lock_backend_launch_context "$ITER_DIR"
    SPY_LOG="$(mktemp)"
    _start_service_with_retries() { echo "cmd=$3" >> "$SPY_LOG"; return 0; }
    export QA_BACKEND_HEALTH_URL="http://localhost:19999/api/health"
    export QA_BACKEND_LOG=/dev/null
    # Launch point 1: initial boot (mirrors run_browser_qa_boot_and_replay's own assignment,
    # post-fix: read the locked value, never re-derive).
    export QA_BACKEND_START_CMD="$GOAL_ITER_BACKEND_LAUNCH_CMD"
    ensure_services_running
    echo "RC1=$?"; echo "UP1=$QA_BACKEND_UP"
    # Launch point 2: a later restart/retry in the SAME run. A caller reusing the locked value
    # (the fixed goal-iter-lean.sh's only pattern now) resolves to the identical string.
    export QA_BACKEND_START_CMD="$GOAL_ITER_BACKEND_LAUNCH_CMD"
    ensure_services_running
    echo "RC2=$?"; echo "UP2=$QA_BACKEND_UP"
    echo "SPY_CALLS=$(wc -l < "$SPY_LOG")"
    cat "$SPY_LOG"
  )
)" || true
echo "$outA" | grep -q '^UP1=yes$' && echo "$outA" | grep -q '^UP2=yes$' \
  && assert "TC-1/TC-3: locked override honored on both the initial boot and a later restart" pass \
  || { assert "TC-1/TC-3: locked override honored on both the initial boot and a later restart" fail; echo "    got: $outA"; }
echo "$outA" | grep -q '^SPY_CALLS=2$' \
  && assert "TC-1/TC-3: exactly 2 backend starts attempted (both launch points actually ran)" pass \
  || { assert "TC-1/TC-3: exactly 2 backend starts attempted (both launch points actually ran)" fail; echo "    got: $outA"; }
_calls="$(echo "$outA" | grep '^cmd=' | sort -u | wc -l)"
[[ "$_calls" -eq 1 ]] \
  && assert "TC-3: the first and later launch commands are byte-identical (zero mismatch)" pass \
  || { assert "TC-3: the first and later launch commands are byte-identical (zero mismatch)" fail; echo "    got: $outA"; }
echo "$outA" | grep -qF "cmd=$OVERRIDE_CMD" \
  && assert "TC-1: the honored command is the override, not the bare default" pass \
  || { assert "TC-1: the honored command is the override, not the bare default" fail; echo "    got: $outA"; }

# ── B. TC-4 (missing): an override is locked, but a launch point's QA_BACKEND_START_CMD comes in
#      EMPTY (a call site that lost the override entirely) -- must fail closed, and the callee that
#      would spawn a process must never be invoked.
outB="$(
  (
    set -euo pipefail
    source "$CM"
    ITER_DIR="$WORK/iterB"
    export CHAIN_START_BACKEND_CMD="$OVERRIDE_CMD"
    goal_iter_lock_backend_launch_context "$ITER_DIR"
    SPY_LOG="$(mktemp)"
    _start_service_with_retries() { echo "cmd=$3" >> "$SPY_LOG"; return 0; }
    export QA_BACKEND_HEALTH_URL="http://localhost:19999/api/health"
    export QA_BACKEND_LOG=/dev/null
    export QA_BACKEND_START_CMD=""   # simulates a call site that lost the override
    _rc=0
    ensure_services_running || _rc=$?
    echo "RC=$_rc"; echo "UP=$QA_BACKEND_UP"; echo "TAIL=$QA_BACKEND_LOG_TAIL"
    echo "SPY_CALLS=$(wc -l < "$SPY_LOG")"
  )
)" || true
echo "$outB" | grep -q '^RC=1$' \
  && assert "TC-4: a missing-but-expected override fails closed (non-zero return)" pass \
  || { assert "TC-4: a missing-but-expected override fails closed (non-zero return)" fail; echo "    got: $outB"; }
echo "$outB" | grep -q '^UP=no$' \
  && assert "TC-4: QA_BACKEND_UP=no (not a silent success)" pass \
  || { assert "TC-4: QA_BACKEND_UP=no (not a silent success)" fail; echo "    got: $outB"; }
echo "$outB" | grep -q '^TAIL=refused:' \
  && assert "TC-4: an explicit 'refused' error is recorded before any boot attempt" pass \
  || { assert "TC-4: an explicit 'refused' error is recorded before any boot attempt" fail; echo "    got: $outB"; }
echo "$outB" | grep -q '^SPY_CALLS=0$' \
  && assert "TC-4: no backend process is spawned for the refused attempt" pass \
  || { assert "TC-4: no backend process is spawned for the refused attempt" fail; echo "    got: $outB"; }

# ── C. TC-5/TC-6 reproduction: an override is locked, but a launch point's QA_BACKEND_START_CMD
#      resolves to the BARE DEFAULT instead (the exact iteration-23 shape -- a call site silently
#      fell back). Pre-fix: no guard exists, so the callee that would spawn the backend process IS
#      invoked with the wrong (bare-default) command -- this assertion FAILS against the reverted
#      diff, proving it reproduces the defect (TC-5), and PASSES against the fix (TC-6).
outC="$(
  (
    set -euo pipefail
    source "$CM"
    ITER_DIR="$WORK/iterC"
    export CHAIN_START_BACKEND_CMD="$OVERRIDE_CMD"
    goal_iter_lock_backend_launch_context "$ITER_DIR"
    SPY_LOG="$(mktemp)"
    _start_service_with_retries() { echo "cmd=$3" >> "$SPY_LOG"; return 0; }
    export QA_BACKEND_HEALTH_URL="http://localhost:19999/api/health"
    export QA_BACKEND_LOG=/dev/null
    export QA_BACKEND_START_CMD="$BARE_DEFAULT_CMD"   # simulates the pre-fix independent re-derivation
    _rc=0
    ensure_services_running || _rc=$?
    echo "RC=$_rc"; echo "UP=$QA_BACKEND_UP"
    echo "SPY_CALLS=$(wc -l < "$SPY_LOG")"
    cat "$SPY_LOG"
  )
)" || true
echo "$outC" | grep -q '^SPY_CALLS=0$' \
  && assert "TC-5/TC-6: a launch point that drifted to the bare default is refused, never started" pass \
  || { assert "TC-5/TC-6: a launch point that drifted to the bare default is refused, never started" fail; echo "    got: $outC"; }
echo "$outC" | grep -q '^RC=1$' && echo "$outC" | grep -q '^UP=no$' \
  && assert "TC-5/TC-6: the drift is a hard fail-closed refusal, not a soft skip" pass \
  || { assert "TC-5/TC-6: the drift is a hard fail-closed refusal, not a soft skip" fail; echo "    got: $outC"; }

# ── D. TC-7: the ordinary no-override case is completely unaffected -- when CHAIN_START_BACKEND_CMD
#      is unset, the locked value IS the bare default, and every call site using it succeeds exactly
#      as before this fix.
outD="$(
  (
    set -euo pipefail
    source "$CM"
    ITER_DIR="$WORK/iterD"
    unset CHAIN_START_BACKEND_CMD 2>/dev/null || true
    goal_iter_lock_backend_launch_context "$ITER_DIR"
    SPY_LOG="$(mktemp)"
    _start_service_with_retries() { echo "cmd=$3" >> "$SPY_LOG"; return 0; }
    export QA_BACKEND_HEALTH_URL="http://localhost:19999/api/health"
    export QA_BACKEND_LOG=/dev/null
    export QA_BACKEND_START_CMD="$GOAL_ITER_BACKEND_LAUNCH_CMD"
    _rc=0
    ensure_services_running || _rc=$?
    echo "RC=$_rc"; echo "UP=$QA_BACKEND_UP"
    echo "LOCKED=$GOAL_ITER_BACKEND_LAUNCH_CMD"
  )
)" || true
echo "$outD" | grep -q '^RC=0$' && echo "$outD" | grep -q '^UP=yes$' \
  && assert "TC-7: the unset-override (ordinary) path is unaffected -- no spurious refusal" pass \
  || { assert "TC-7: the unset-override (ordinary) path is unaffected -- no spurious refusal" fail; echo "    got: $outD"; }
echo "$outD" | grep -qF "LOCKED=$BARE_DEFAULT_CMD" \
  && assert "TC-7: with no override, the locked value is the plain scripts/start-backend.sh default" pass \
  || { assert "TC-7: with no override, the locked value is the plain scripts/start-backend.sh default" fail; echo "    got: $outD"; }

# ── E. A caller that never locks a context (every script besides goal-iter-lean.sh) sees no
#      behavior change -- the guard is a complete no-op when GOAL_ITER_BACKEND_LAUNCH_CMD is unset.
outE="$(
  (
    set -euo pipefail
    source "$CM"
    unset GOAL_ITER_BACKEND_LAUNCH_CMD 2>/dev/null || true
    SPY_LOG="$(mktemp)"
    _start_service_with_retries() { echo "cmd=$3" >> "$SPY_LOG"; return 0; }
    export QA_BACKEND_HEALTH_URL="http://localhost:19999/api/health"
    export QA_BACKEND_LOG=/dev/null
    export QA_BACKEND_START_CMD="$BARE_DEFAULT_CMD"
    _rc=0
    ensure_services_running || _rc=$?
    echo "RC=$_rc"; echo "UP=$QA_BACKEND_UP"
    echo "SPY_CALLS=$(wc -l < "$SPY_LOG")"
  )
)" || true
echo "$outE" | grep -q '^RC=0$' && echo "$outE" | grep -q '^UP=yes$' && echo "$outE" | grep -q '^SPY_CALLS=1$' \
  && assert "no-lock callers (qa-phase.sh, browser-qa-phase.sh, demo-phase.sh, ...) are unaffected" pass \
  || { assert "no-lock callers (qa-phase.sh, browser-qa-phase.sh, demo-phase.sh, ...) are unaffected" fail; echo "    got: $outE"; }

# ── F. Structural: goal-iter-lean.sh locks the context ONCE, before either the SPEED-2 or SPEED-3
#      fork spawn points, and run_browser_qa_boot_and_replay no longer independently re-derives
#      BACKEND_START_CMD from CHAIN_START_BACKEND_CMD (the exact pattern that caused iteration 23's
#      defect) -- it must read the locked value instead.
_lock_line="$(grep -n '^goal_iter_lock_backend_launch_context "\$ITER_DIR"$' "$GIL" | head -1 | cut -d: -f1)"
_fork_line="$(grep -n '^_BQA_PID=""$' "$GIL" | head -1 | cut -d: -f1)"
[[ -n "$_lock_line" && -n "$_fork_line" && "$_lock_line" -lt "$_fork_line" ]] \
  && assert "goal-iter-lean.sh: launch context is locked before the SPEED-2/3 fork spawn points" pass \
  || { assert "goal-iter-lean.sh: launch context is locked before the SPEED-2/3 fork spawn points" fail; echo "    lock@$_lock_line fork@$_fork_line"; }
_fn_body="$(sed -n '/^run_browser_qa_boot_and_replay() {/,/^}$/p' "$GIL")"
# Assignment form only ("BACKEND_START_CMD=...CHAIN_START_BACKEND_CMD...") -- a comment merely
# naming the old pattern (to explain why it was removed) must not false-positive this check.
if echo "$_fn_body" | grep -qE '^\s*BACKEND_START_CMD="\$\{CHAIN_START_BACKEND_CMD'; then
  assert "run_browser_qa_boot_and_replay no longer re-derives from CHAIN_START_BACKEND_CMD" fail
else
  assert "run_browser_qa_boot_and_replay no longer re-derives from CHAIN_START_BACKEND_CMD" pass
fi
echo "$_fn_body" | grep -q 'BACKEND_START_CMD="\${GOAL_ITER_BACKEND_LAUNCH_CMD:-}"' \
  && assert "run_browser_qa_boot_and_replay reads the locked GOAL_ITER_BACKEND_LAUNCH_CMD" pass \
  || { assert "run_browser_qa_boot_and_replay reads the locked GOAL_ITER_BACKEND_LAUNCH_CMD" fail; }

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[[ $FAIL -gt 0 ]] && exit 1
exit 0
