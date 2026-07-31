#!/usr/bin/env bash
# test-blocked-verdict-grep-sites.sh — ops-hardening iter-41 (A4, TC-9): `BLOCKED` joins
# `verdicts.py::BrowserQAVerdict` (previously PASS/FAIL/SKIPPED only) and every one of
# goal-iter-lean.sh's four `grep -oE 'PASS|FAIL|SKIPPED'` verdict-extraction sites also matches it
# (audit iter-40 finding T3: before this fix, extracting a BLOCKED headline's verdict word silently
# produced an EMPTY string — "fail-safe by accident, not by contract").
#
# Two things proven:
#   1. `BrowserQAVerdict` (verdicts.py) accepts "BLOCKED" as a legal member.
#   2. All four grep sites in goal-iter-lean.sh extract "BLOCKED" correctly from a
#      `**Browser QA Verdict:** BLOCKED` line (not an empty string).
#
# Offline, no model, <1s.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LEAN="$REPO_ROOT/scripts/automation/goal-iter-lean.sh"
VERDICTS_PY="$REPO_ROOT/scripts/automation/lib/verdicts.py"

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

# ── 1. BrowserQAVerdict accepts BLOCKED as a legal enum member ───────────────────────────────
rc=0
out=$(python3 -c "
import sys
sys.path.insert(0, '$(dirname "$VERDICTS_PY")')
from verdicts import BrowserQAVerdict
print(BrowserQAVerdict('BLOCKED').value)
") || rc=$?
[[ $rc -eq 0 && "$out" == "BLOCKED" ]] \
  && assert "BrowserQAVerdict accepts BLOCKED" "pass" \
  || assert "BrowserQAVerdict accepts BLOCKED (rc=$rc, got '$out')" "fail"

# ── 2. Every grep -oE site in goal-iter-lean.sh matches BLOCKED ──────────────────────────────
n_sites=$(grep -c "grep -oE 'PASS|FAIL|SKIPPED" "$LEAN" || true)
n_sites=${n_sites:-0}
[[ "$n_sites" -eq 4 ]] \
  && assert "goal-iter-lean.sh has exactly 4 verdict-extraction grep sites (got $n_sites)" "pass" \
  || assert "goal-iter-lean.sh has exactly 4 verdict-extraction grep sites (got $n_sites, expected 4)" "fail"

n_with_blocked=$(grep -c "grep -oE 'PASS|FAIL|SKIPPED|BLOCKED'" "$LEAN" || true)
n_with_blocked=${n_with_blocked:-0}
[[ "$n_with_blocked" -eq "$n_sites" && "$n_sites" -gt 0 ]] \
  && assert "all $n_sites site(s) include BLOCKED in the pattern" "pass" \
  || assert "all site(s) include BLOCKED in the pattern (got $n_with_blocked of $n_sites)" "fail"

# ── 3. Functional: the pattern actually extracts BLOCKED, not an empty string ────────────────
line='**Browser QA Verdict:** BLOCKED'
extracted="$(echo "$line" | grep -oE 'PASS|FAIL|SKIPPED|BLOCKED' | head -1)"
[[ "$extracted" == "BLOCKED" ]] \
  && assert "the widened pattern extracts BLOCKED (not empty) from a BLOCKED headline" "pass" \
  || assert "the widened pattern extracts BLOCKED (not empty) from a BLOCKED headline (got '$extracted')" "fail"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[[ $FAIL -gt 0 ]] && exit 1
exit 0
