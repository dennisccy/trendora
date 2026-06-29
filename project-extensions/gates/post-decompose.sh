#!/usr/bin/env bash
# Trendora post-decompose gate (project policy). Invoked by run-goal.sh's generic
# gate hook (framework mechanism M2) with SPEC_PATH / LEDGER_PATH / GATE_VERDICT_PATH
# in the environment. It certifies — via the referee — any evidence-derived claim the
# iteration spec proposes, BEFORE the iteration is built.
#
#   exit 0  = no evidence claim, or every claim certified (PASS)  -> build
#   exit 3  = a claim was NOT certified (FAIL / INSUFFICIENT)      -> block
#
# Plain iterations (no "## Evidence Claim" block) pass instantly and are never blocked
# by gate-infrastructure problems; only claim-bearing specs reach the referee.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEC="${SPEC_PATH:-}"

# Fast pass-through: nothing to certify unless the spec proposes an evidence claim.
if [[ -z "$SPEC" || ! -f "$SPEC" ]] || ! grep -qE '^##[[:space:]]+Evidence Claim' "$SPEC"; then
  exit 0
fi

BACKEND="$HERE/../../apps/backend"
if [[ ! -x "$BACKEND/.venv/bin/python" ]]; then
  echo "[gate] spec proposes an evidence claim but the backend venv is missing — cannot certify; BLOCKING." >&2
  exit 3
fi
cd "$BACKEND" || { echo "[gate] cannot enter backend dir — BLOCKING." >&2; exit 3; }
exec .venv/bin/python "$HERE/verify_claim.py"
