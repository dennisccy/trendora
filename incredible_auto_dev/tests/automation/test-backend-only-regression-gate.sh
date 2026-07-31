#!/usr/bin/env bash
# test-backend-only-regression-gate.sh — ops-hardening iter-41 (A1 companion fix, TC-1/TC-4):
# a backend-only (`Frontend Present: no`) goal-mode iteration that names required-still-passing
# journeys must still run UI test design (Step 5) and browser QA (Step 6) for those journeys'
# regression re-verification — a bare N/A stub (the old unconditional behavior) left every one of
# them completely unverified while every gate reported clean (iter-40's ESCALATE root cause: the
# ui-test-designer agent's own "Backend-only phase handling" fix was unreachable because these
# shell-level gates returned before the agent was ever dispatched).
#
# Two things proven:
#   1. `lib/common.sh::phase_spec_has_required_regression` itself — a spec naming at least one
#      "Required-still-passing journeys:" J-ID -> true; a spec with none/absent -> false.
#   2. Regression guard: run-phase.sh's Step 5/6 gates and the two standalone phase scripts
#      (ui-test-design-phase.sh, browser-qa-phase.sh) all consult the helper before falling back
#      to the backend-only N/A-stub path.
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

T=$(TMPDIR=/tmp mktemp -d)
trap 'rm -rf "$T"' EXIT

# ── 1. A spec naming required-still-passing journeys -> true ─────────────────────────────────
cat > "$T/with-journeys.md" <<'EOF'
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 41
- **Frontend Present:** no
- **Target journeys:** J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09
EOF
rc=0
bash -c 'set -euo pipefail; source "'"$LIB"'"; phase_spec_has_required_regression "'"$T"'/with-journeys.md"' || rc=$?
[[ $rc -eq 0 ]] \
  && assert "spec naming 6 required-still-passing journeys -> true" "pass" \
  || assert "spec naming 6 required-still-passing journeys -> true (rc=$rc)" "fail"

# ── 2. A spec with "none" on that line -> false ───────────────────────────────────────────────
cat > "$T/none.md" <<'EOF'
- **Frontend Present:** no
- **Required-still-passing journeys:** none — first iteration, nothing to regress yet
EOF
rc=0
bash -c 'set -euo pipefail; source "'"$LIB"'"; phase_spec_has_required_regression "'"$T"'/none.md"' || rc=$?
[[ $rc -ne 0 ]] \
  && assert "spec with 'none' on the required-regression line -> false" "pass" \
  || assert "spec with 'none' on the required-regression line -> false (rc=$rc)" "fail"

# ── 3. A spec with no such line at all (plain phase mode) -> false ───────────────────────────
cat > "$T/plain.md" <<'EOF'
# phase-3 — Add watchlist export
Some ordinary phase-mode spec with no goal-mode metadata block at all.
EOF
rc=0
bash -c 'set -euo pipefail; source "'"$LIB"'"; phase_spec_has_required_regression "'"$T"'/plain.md"' || rc=$?
[[ $rc -ne 0 ]] \
  && assert "plain phase-mode spec (no goal-mode metadata) -> false" "pass" \
  || assert "plain phase-mode spec (no goal-mode metadata) -> false (rc=$rc)" "fail"

# ── 4. Regression guard: the three call sites reference the helper ───────────────────────────
declare -A CALLERS=(
  ["run-phase.sh"]=2
  ["ui-test-design-phase.sh"]=1
  ["browser-qa-phase.sh"]=1
)
for f in "${!CALLERS[@]}"; do
  path="$REPO_ROOT/scripts/automation/$f"
  n=$(grep -c 'phase_spec_has_required_regression' "$path" 2>/dev/null || true)
  n=${n:-0}
  if [[ "$n" -ge "${CALLERS[$f]}" ]]; then
    assert "$f: consults phase_spec_has_required_regression ($n call site(s))" "pass"
  else
    assert "$f: consults phase_spec_has_required_regression (expected >= ${CALLERS[$f]}, got $n)" "fail"
  fi
done

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[[ $FAIL -gt 0 ]] && exit 1
exit 0
