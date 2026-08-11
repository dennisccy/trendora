#!/usr/bin/env bash
# test-replay-lane.sh — unit tests for scripts/automation/lib/replay-lane.sh,
# the ONE shared implementation of the deterministic regression-replay lane
# (P2 fix: the lane must exist at BOTH goal-mode depths — goal-iter-lean.sh and
# the FULL pipeline's browser-qa-phase.sh both source this lib; no copy-paste).
#
# Sources the real lib in a sandbox with a stub demo_runner.py (lint + verify
# knobs via STUB_* env) and the REAL merge_ui_test_results.py. Each scenario
# runs in a fresh `set -euo pipefail` subshell — the same shell discipline the
# production callers run under, so the load-bearing `|| true` guards are
# actually exercised (see the journey-less-spec death in test-goal-parallel-bqa
# scenario I).
#
# Covered:
#   1. replay_lane_spec_journeys: Target/Required parse; journey-less line
#      ("Required-still-passing journeys: none — ...") survives set -e+pipefail.
#   2. replay_lane_paths: SID derivation + all lane path globals + mkdir.
#   3. Partition: golden on file → R_REPLAY; missing → R_LLM; lint-invalid →
#      quarantined (*.json.invalid) + R_LLM.
#      3b (ops-hardening iter-60): TARGET_JOURNEYS entries join the SAME partition —
#      an on-file golden joins R_REPLAY and is ACTUALLY REPLAYED (the iter-59
#      lane-coverage gap: a target journey's golden used to sit unexecuted every
#      run); a lint-invalid one is quarantined but NOT routed to R_LLM (a
#      different semantic set — the iteration's own target-journey QA dispatch
#      already covers it); a missing one is left untouched (same fallback); a
#      journey in BOTH sets is never double-entered; TARGET_JOURNEYS being
#      entirely unset (the common case, and every pre-iter-60 scenario below)
#      must not crash the lane under set -u.
#   4. Verify rc=0 → _use_replay=yes, REPLAY_FAILED empty, results file has the
#      UT-J row.
#   5. Verify rc=5 (journey FAIL) → REPLAY_FAILED extracted for LLM re-confirm.
#   6. Verify rc=6 TWICE (persistent browser-infra, REL-5): ONE retry after a
#      service re-check, then the lane records SKIPPED-INFRA (raw artifact
#      verdict line + footer, REPLAY_SKIPPED_INFRA=yes, greppable log lines)
#      and falls back: _use_replay=no, R_REPLAY cleared (ALL regression
#      journeys ride the LLM lane).
#   7. CHAIN_REGRESSION_REPLAY=false escape hatch → verify never invoked.
#   8. Stale-artifact hygiene: a prior run's REGRESSION_RESULTS/LLM_RESULTS are
#      removed at partition entry (a lane that does not run this iteration must
#      not leave last run's files masquerading as current output).
#   9. replay_lane_llm_regression_set: replay on → REPLAY_FAILED+R_LLM (deduped);
#      hatch off → the whole REQUIRED set.
#  10. Merge: replay FAIL overturned by LLM PASS → merged PASS + dated
#      reconciliation footer appended to the RAW replay artifact (companion 1:
#      no stale FAIL survives the iteration); un-overturned FAIL → no footer.
#      10b (ops-hardening iter-42): TARGET_JOURNEYS threads into --target the
#      same way REQUIRED_JOURNEYS threads into --required — a missing target
#      journey forces BLOCKED; unset TARGET_JOURNEYS stays byte-identical.
#  11. Merge crash → lane-file cp fallback (LLM file preferred).
#  12. REL-5 flake discipline: infra-then-success → the retry rescues the lane
#      (normal PASS path, no SKIPPED-INFRA); infra-then-FAIL → the retry's rc=5
#      feeds REPLAY_FAILED unchanged; a clean rc=5 is NEVER retried
#      (invocation-count-proven, zero service re-checks); a non-6 failure
#      (rc=3) keeps the old no-retry generic fallback; SKIPPED-INFRA journeys
#      still feed replay_lane_llm_regression_set (whole REQUIRED set).
#  13. SPEED-15 rung 2: replay_lane_deferred_budget_set defers R_LLM only when
#      trim is active AND replay engaged; the narrowed LLM set keeps replay-FAIL
#      re-confirms; replay_lane_write_deferred_rows appends DEFERRED-BUDGET rows
#      the achievement gate (real goal_gate.py) treats as blocking; empty
#      deferred set → both are no-ops.
#
# No API calls; runs in a couple of seconds.
#
# shellcheck disable=SC1090,SC1091,SC2015,SC2034,SC2329
# (SC1090/91: the lib path is computed per-sandbox; SC2034: FRONTEND_* et al are
# consumed by the sourced lib; SC2329: cleanup runs via trap; SC2015: assert's
# pass arm always returns 0, so the `&& pass || fail` idiom is safe here.)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PASS=0
FAIL=0
assert() {
  if [[ "$2" == "pass" ]]; then echo "  PASS  $1"; PASS=$((PASS + 1)); else echo "  FAIL  $1"; FAIL=$((FAIL + 1)); fi
}

WORK="$(mktemp -d)"
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

ITER="goal-rltest-iter-2"

# ── Sandbox: engine scripts + stub demo_runner ──────────────────────────────
SBX="$WORK/proj"
mkdir -p "$SBX"
cp -r "$ENGINE_ROOT/scripts" "$SBX/"
mkdir -p "$SBX/docs/phases" "$SBX/reports"

LIB="$SBX/scripts/automation/lib/replay-lane.sh"

# Stub demo_runner.py: lint says ok unless STUB_LINT_INVALID names the journey;
# verify writes production-shaped rows per STUB_REPLAY_VERDICT and exits
# STUB_REPLAY_RC (default: 0 for PASS, 5 for FAIL — the real runner's contract),
# stamping STUB_VERIFY_STAMP so tests can prove it did / did not run.
cat > "$SBX/scripts/automation/lib/demo_runner.py" <<'PYEOF'
#!/usr/bin/env python3
import os, sys

def arg(name, default=""):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default

mode = arg("--mode", "record")
journeys = [j for j in arg("--journeys").replace(",", " ").split() if j]

if mode == "lint":
    bad = os.environ.get("STUB_LINT_INVALID", "").split()
    for j in journeys:
        if j in bad:
            print(f"{j} invalid: step 1 has no action")
        else:
            print(f"{j} ok")
    sys.exit(0)

if mode == "verify":
    stamp = os.environ.get("STUB_VERIFY_STAMP", "")
    if stamp:
        with open(stamp, "w") as f:
            f.write(" ".join(journeys))
    # REL-5 knobs: a per-invocation rc sequence driven by a counter file, so
    # retry semantics (exactly-once, rescue, never-on-5) are provable.
    attempt = 1
    cf = os.environ.get("STUB_REPLAY_COUNT_FILE", "")
    if cf:
        try:
            attempt = int(open(cf).read().strip() or "0") + 1
        except Exception:
            attempt = 1
        with open(cf, "w") as f:
            f.write(str(attempt))
    verdict = os.environ.get("STUB_REPLAY_VERDICT", "PASS")
    fail_set = os.environ.get("STUB_REPLAY_FAIL_SET", "").split()
    rc = os.environ.get("STUB_REPLAY_RC", "")
    seq = os.environ.get("STUB_REPLAY_RC_SEQ", "").split()
    if seq:
        rc = seq[min(attempt, len(seq)) - 1]
    results = arg("--results")
    if results and rc == "6":
        # Mirror the real runner: a browser-infra crash still writes the
        # results file (SKIP rows naming the infra failure) before exiting 6.
        rows = "\n".join(
            f"| UT-{j} | replay {j} | regression | P1 | replays clean | browser infrastructure failure: stub crash | SKIP | none |"
            for j in journeys)
        with open(results, "w") as f:
            f.write("**Browser QA Verdict:** SKIPPED\n\n"
                    "## Results Table\n"
                    "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
                    "|---|---|---|---|---|---|---|---|\n" + rows + "\n")
    if results and rc != "6":
        def v_for(j):
            if fail_set:
                return "FAIL" if j in fail_set else "PASS"
            return verdict
        rows = "\n".join(
            f"| UT-{j} | replay {j} | regression | P1 | replays clean | stub {v_for(j).lower()} | {v_for(j)} | none |"
            for j in journeys)
        any_fail = any(v_for(j) == "FAIL" for j in journeys)
        with open(results, "w") as f:
            f.write("**Browser QA Verdict:** " + ("FAIL" if any_fail else "PASS") + "\n\n"
                    "## Results Table\n"
                    "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
                    "|---|---|---|---|---|---|---|---|\n" + rows + "\n")
        if not rc:
            sys.exit(5 if any_fail else 0)
    if rc:
        sys.exit(int(rc))
    sys.exit(5 if verdict == "FAIL" else 0)
PYEOF

# Run a lane scenario in a fresh production-discipline subshell. Env knobs are
# passed via the caller's environment. Prints the outcome globals on one line.
# $1 = REQUIRED_JOURNEYS value, $2 = optional TARGET_JOURNEYS value (ops-hardening
# iter-60 — defaults to unset, exactly like every pre-iter-60 scenario below, so
# the lib must survive TARGET_JOURNEYS never being assigned at all under set -u).
run_partition() {  # $1 = REQUIRED_JOURNEYS value, $2 = optional TARGET_JOURNEYS value
  (
    set -euo pipefail
    # shellcheck source=/dev/null
    source "$LIB"
    REPO_ROOT="$SBX"
    REQUIRED_JOURNEYS="$1"
    if [[ -n "${2:-}" ]]; then
      TARGET_JOURNEYS="$2"
    fi
    FRONTEND_AVAILABLE="${FRONTEND_AVAILABLE_OVERRIDE:-yes}"
    FRONTEND_URL="http://localhost:9"
    # REL-5: the retry path re-checks services when the function exists (in
    # production common.sh provides it; this stamping stub proves call counts —
    # scenarios without STUB_SVC_STAMP also prove the lib survives its absence).
    if [[ -n "${STUB_SVC_STAMP:-}" ]]; then
      ensure_services_running() { echo recheck >> "$STUB_SVC_STAMP"; }
    fi
    replay_lane_paths "$ITER"
    if [[ -n "${RUN_PARTITION_LOG:-}" ]]; then
      replay_lane_partition_and_verify "$ITER" > "$RUN_PARTITION_LOG" 2>&1
    else
      replay_lane_partition_and_verify "$ITER" >/dev/null
    fi
    printf 'R_REPLAY=<%s>|R_LLM=<%s>|use=<%s>|failed=<%s>\n' \
      "${R_REPLAY:-}" "${R_LLM:-}" "${_use_replay:-}" "${REPLAY_FAILED:-}"
    if [[ -n "${REPLAY_SKIPPED_INFRA:-}" ]]; then
      printf 'skipinfra=<%s>\n' "$REPLAY_SKIPPED_INFRA"
    fi
    if [[ -n "${REPLAY_MASS_FAIL:-}" ]]; then
      printf 'massfail=<%s>|canaries=<%s>\n' "$REPLAY_MASS_FAIL" "${REPLAY_CANARIES:-}"
    fi
  )
}

reset_goldens() {
  rm -rf "$SBX/runs" "$SBX/reports"
  mkdir -p "$SBX/reports"
}

golden() {  # $1 = journey id
  mkdir -p "$SBX/runs/goal-session-rltest/journey-scripts"
  echo '{"journey":"'"$1"'","steps":[]}' > "$SBX/runs/goal-session-rltest/journey-scripts/$1.json"
}

echo "=== test-replay-lane.sh ==="

# ── 0. Lib exists and parses ─────────────────────────────────────────────────
if [[ -f "$LIB" ]] && bash -n "$LIB" 2>/dev/null; then
  assert "lib exists and parses (bash -n)" pass
else
  assert "lib exists and parses (bash -n)" fail
  echo "  (scripts/automation/lib/replay-lane.sh missing — nothing else can pass)"
  echo ""
  echo "RESULT: $PASS passed, $((FAIL + 1)) failed"
  exit 1
fi

# ── 1. Spec journey parsing ──────────────────────────────────────────────────
SPEC="$SBX/docs/phases/$ITER.md"
cat > "$SPEC" <<'EOF'
# Goal Iteration 2

- **Target journeys:** J-01, J-03
- **Required-still-passing journeys:** J-02, J-04
EOF

out="$( (set -euo pipefail; source "$LIB"; replay_lane_spec_journeys 'Target journeys:' "$SPEC") )"
[[ "$out" == "J-01 J-03 " ]] && assert "spec_journeys: Target parse" pass || { assert "spec_journeys: Target parse (got '<$out>')" fail; }

out="$( (set -euo pipefail; source "$LIB"; replay_lane_spec_journeys 'Required-still-passing' "$SPEC") )"
[[ "$out" == "J-02 J-04 " ]] && assert "spec_journeys: Required parse" pass || { assert "spec_journeys: Required parse (got '<$out>')" fail; }

cat > "$SPEC.baseline" <<'EOF'
- **Required-still-passing journeys:** none — baseline establishes the initial state
EOF
rc=0
out="$( (set -euo pipefail; source "$LIB"; replay_lane_spec_journeys 'Required-still-passing' "$SPEC.baseline"; echo "SURVIVED") )" || rc=$?
[[ "$rc" -eq 0 && "$out" == *SURVIVED* ]] && assert "spec_journeys: journey-less line survives set -e + pipefail" pass \
  || assert "spec_journeys: journey-less line survives set -e + pipefail (rc=$rc)" fail

# ── 2. Lane paths ────────────────────────────────────────────────────────────
out="$( (
  set -euo pipefail
  source "$LIB"
  REPO_ROOT="$SBX"
  replay_lane_paths "$ITER"
  printf '%s|%s|%s|%s|%s\n' "$SID" "$JOURNEY_SCRIPTS_DIR" "$REGRESSION_RESULTS" "$LLM_RESULTS" "$EVIDENCE_DIR"
) )"
want="rltest|$SBX/runs/goal-session-rltest/journey-scripts|$SBX/reports/phase-$ITER-regression-replay-results.md|$SBX/reports/phase-$ITER-ui-test-results.llm.md|$SBX/reports/qa/$ITER-evidence"
[[ "$out" == "$want" ]] && assert "paths: SID + lane path globals" pass || { assert "paths: SID + lane path globals" fail; echo "    got:  $out"; echo "    want: $want"; }
[[ -d "$SBX/runs/goal-session-rltest/journey-scripts" ]] && assert "paths: journey-scripts dir created" pass || assert "paths: journey-scripts dir created" fail

# ── 3. Partition: golden / missing / lint-invalid ────────────────────────────
reset_goldens
golden "J-01"
golden "J-03"
out="$(STUB_LINT_INVALID="J-03" STUB_VERIFY_STAMP="$WORK/stamp3" run_partition "J-01 J-02 J-03 ")"
[[ "$out" == "R_REPLAY=<J-01 >|R_LLM=<J-02 J-03 >|use=<yes>|failed=<>" ]] \
  && assert "partition: golden→replay, missing→LLM, lint-invalid→LLM" pass \
  || { assert "partition: golden→replay, missing→LLM, lint-invalid→LLM" fail; echo "    got: $out"; }
[[ -f "$SBX/runs/goal-session-rltest/journey-scripts/J-03.json.invalid" && ! -f "$SBX/runs/goal-session-rltest/journey-scripts/J-03.json" ]] \
  && assert "partition: invalid golden quarantined (.json.invalid)" pass \
  || assert "partition: invalid golden quarantined (.json.invalid)" fail

# ── 3b. Partition: TARGET_JOURNEYS with an on-file golden joins R_REPLAY too (ops-hardening
#       iter-60, TC-1 — the lane-coverage gap: J-05/J-07 passed LIVE but never got replayed because
#       this loop previously scanned ONLY REQUIRED_JOURNEYS). J-01 is BOTH required and target (must
#       not double-enter); J-05 is target-only with a valid golden (must join R_REPLAY and be
#       ACTUALLY REPLAYED); J-07 is target-only with a lint-invalid golden (quarantined, not R_LLM —
#       a different set with a different semantic, see the fix's own comment); J-09 is target-only
#       with NO golden at all (must stay untouched — the "existing fallback path" the error-case
#       test below relies on, not this lane's R_LLM). ─────────────────────────────────────────────
reset_goldens
golden "J-01"
golden "J-05"
golden "J-07"
out="$(STUB_LINT_INVALID="J-07" STUB_VERIFY_STAMP="$WORK/stamp3b" run_partition "J-01 " "J-01 J-05 J-07 J-09")"
[[ "$out" == "R_REPLAY=<J-01 J-05 >|R_LLM=<>|use=<yes>|failed=<>" ]] \
  && assert "partition: TARGET-only journey with an on-file golden joins R_REPLAY (TC-1)" pass \
  || { assert "partition: TARGET-only journey with an on-file golden joins R_REPLAY (TC-1)" fail; echo "    got: $out"; }
[[ -f "$SBX/runs/goal-session-rltest/journey-scripts/J-07.json.invalid" && ! -f "$SBX/runs/goal-session-rltest/journey-scripts/J-07.json" ]] \
  && assert "partition: lint-invalid TARGET-only golden is still quarantined" pass \
  || assert "partition: lint-invalid TARGET-only golden is still quarantined" fail
[[ ! -f "$SBX/runs/goal-session-rltest/journey-scripts/J-09.json" && ! -f "$SBX/runs/goal-session-rltest/journey-scripts/J-09.json.invalid" ]] \
  && assert "partition: TARGET-only journey with no golden is left untouched (existing fallback path, not R_LLM)" pass \
  || assert "partition: TARGET-only journey with no golden is left untouched" fail
[[ "$(cat "$WORK/stamp3b" 2>/dev/null)" == "J-01 J-05" ]] \
  && assert "partition: demo_runner actually invoked WITH the target journey (ACTUALLY REPLAYED, TC-1)" pass \
  || assert "partition: demo_runner actually invoked WITH the target journey (got '$(cat "$WORK/stamp3b" 2>/dev/null)')" fail
grep -q '^| UT-J-05 ' "$SBX/reports/phase-$ITER-regression-replay-results.md" \
  && assert "partition: J-05 produced a REAL row in the raw replay results file (TC-1)" pass \
  || assert "partition: J-05 produced a REAL row in the raw replay results file (TC-1)" fail

# ── 3c. Partition: TARGET_JOURNEYS never assigned at all does not crash the lane (set -u safety —
#       most callers/scenarios, including every one above, never set it). ──────────────────────────
out="$(STUB_VERIFY_STAMP="$WORK/stamp3c" run_partition "J-01 ")"
[[ "$out" == "R_REPLAY=<J-01 >|R_LLM=<>|use=<yes>|failed=<>" ]] \
  && assert "partition: TARGET_JOURNEYS unset entirely does not crash the lane (set -u safety)" pass \
  || { assert "partition: TARGET_JOURNEYS unset entirely does not crash the lane (set -u safety)" fail; echo "    got: $out"; }

# ── 3d. Partition: a journey listed as BOTH required and target is never double-entered ─────────
reset_goldens
golden "J-01"
out="$(STUB_VERIFY_STAMP="$WORK/stamp3d" run_partition "J-01 " "J-01 ")"
[[ "$out" == "R_REPLAY=<J-01 >|R_LLM=<>|use=<yes>|failed=<>" ]] \
  && assert "partition: a journey in BOTH required and target sets is not double-entered" pass \
  || { assert "partition: a journey in BOTH required and target sets is not double-entered" fail; echo "    got: $out"; }

# ── 4. Verify rc=0 (all pass) ────────────────────────────────────────────────
[[ -f "$SBX/reports/phase-$ITER-regression-replay-results.md" ]] \
  && grep -q '^| UT-J-01 ' "$SBX/reports/phase-$ITER-regression-replay-results.md" \
  && assert "verify rc=0: regression results file written with UT-J row" pass \
  || assert "verify rc=0: regression results file written with UT-J row" fail
[[ "$(cat "$WORK/stamp3" 2>/dev/null)" == "J-01" ]] \
  && assert "verify rc=0: runner invoked with exactly the replay set" pass \
  || assert "verify rc=0: runner invoked with exactly the replay set" fail

# ── 5. Verify rc=5: FAIL rows → REPLAY_FAILED ───────────────────────────────
reset_goldens
golden "J-01"
out="$(STUB_REPLAY_VERDICT=FAIL run_partition "J-01 J-02 ")"
[[ "$out" == "R_REPLAY=<J-01 >|R_LLM=<J-02 >|use=<yes>|failed=<J-01 >" ]] \
  && assert "verify rc=5: REPLAY_FAILED extracted for LLM re-confirm" pass \
  || { assert "verify rc=5: REPLAY_FAILED extracted for LLM re-confirm" fail; echo "    got: $out"; }

# ── 6. Verify rc=6 twice (REL-5): one retry + re-check → SKIPPED-INFRA ──────
reset_goldens
golden "J-01"
rm -f "$WORK/count6"; : > "$WORK/svc6"
out="$(STUB_REPLAY_RC_SEQ='6 6' STUB_REPLAY_COUNT_FILE="$WORK/count6" \
       STUB_SVC_STAMP="$WORK/svc6" RUN_PARTITION_LOG="$WORK/lane6.log" \
       run_partition "J-01 J-02 ")"
want="R_REPLAY=<>|R_LLM=<J-02 >|use=<no>|failed=<>
skipinfra=<yes>"
[[ "$out" == "$want" ]] \
  && assert "verify rc=6 twice: fallback + REPLAY_SKIPPED_INFRA=yes" pass \
  || { assert "verify rc=6 twice: fallback + REPLAY_SKIPPED_INFRA=yes" fail; echo "    got: $out"; }
[[ "$(cat "$WORK/count6" 2>/dev/null)" == "2" ]] \
  && assert "verify rc=6 twice: exactly ONE retry (2 verify invocations)" pass \
  || assert "verify rc=6 twice: exactly ONE retry (got $(cat "$WORK/count6" 2>/dev/null) invocations)" fail
[[ "$(grep -c recheck "$WORK/svc6" 2>/dev/null)" == "1" ]] \
  && assert "verify rc=6 twice: exactly one ensure_services_running re-check" pass \
  || assert "verify rc=6 twice: exactly one ensure_services_running re-check (got $(grep -c recheck "$WORK/svc6" 2>/dev/null))" fail
grep -q "browser-infra failure (rc=6) — re-checking services and retrying the replay once" "$WORK/lane6.log" \
  && assert "verify rc=6 twice: greppable retry log line" pass \
  || assert "verify rc=6 twice: greppable retry log line" fail
grep -q "SKIPPED-INFRA — browser-infra failure persisted after one retry" "$WORK/lane6.log" \
  && assert "verify rc=6 twice: greppable SKIPPED-INFRA verdict log line" pass \
  || assert "verify rc=6 twice: greppable SKIPPED-INFRA verdict log line" fail
REG6="$SBX/reports/phase-$ITER-regression-replay-results.md"
grep -q '^\*\*Browser QA Verdict:\*\* SKIPPED-INFRA$' "$REG6" \
  && assert "verify rc=6 twice: raw artifact verdict line is exactly SKIPPED-INFRA" pass \
  || { assert "verify rc=6 twice: raw artifact verdict line is exactly SKIPPED-INFRA" fail; head -3 "$REG6" 2>/dev/null | sed 's/^/        /'; }
grep -q 'routed to the LLM lane' "$REG6" \
  && assert "verify rc=6 twice: raw artifact footer explains the routing" pass \
  || assert "verify rc=6 twice: raw artifact footer explains the routing" fail

# ── 6b. Verify rc=7 (ops-hardening iter-39, TC-5): backend-unreachable BLOCKED,
#        distinct from rc=6 (browser-infra) — falls back to the LLM lane on the
#        FIRST attempt, no retry, distinct log line naming it "BLOCKED" not
#        "browser-infra" or a real regression.
reset_goldens
golden "J-01"
out="$(STUB_REPLAY_RC=7 RUN_PARTITION_LOG="$WORK/lane7.log" run_partition "J-01 J-02 ")"
want="R_REPLAY=<>|R_LLM=<J-02 >|use=<no>|failed=<>"
[[ "$out" == "$want" ]] \
  && assert "verify rc=7: falls back to LLM lane for ALL regression journeys" pass \
  || { assert "verify rc=7: falls back to LLM lane for ALL regression journeys" fail; echo "    got: $out"; }
grep -q "backend unreachable before any journey ran (rc=7, BLOCKED" "$WORK/lane7.log" \
  && assert "verify rc=7: greppable BLOCKED-distinct log line" pass \
  || assert "verify rc=7: greppable BLOCKED-distinct log line" fail

# ── 7. Escape hatch ──────────────────────────────────────────────────────────
reset_goldens
golden "J-01"
rm -f "$WORK/stamp7"
out="$(CHAIN_REGRESSION_REPLAY=false STUB_VERIFY_STAMP="$WORK/stamp7" run_partition "J-01 ")"
[[ "$out" == "R_REPLAY=<J-01 >|R_LLM=<>|use=<no>|failed=<>" && ! -f "$WORK/stamp7" ]] \
  && assert "hatch: CHAIN_REGRESSION_REPLAY=false — verify never invoked" pass \
  || { assert "hatch: CHAIN_REGRESSION_REPLAY=false — verify never invoked" fail; echo "    got: $out"; }

# ── 8. Stale-artifact hygiene at partition entry ─────────────────────────────
reset_goldens
echo "stale replay" > "$SBX/reports/phase-$ITER-regression-replay-results.md"
echo "stale llm"    > "$SBX/reports/phase-$ITER-ui-test-results.llm.md"
out="$(run_partition "J-02 ")"   # no goldens → verify never runs → files must STILL be gone
if [[ ! -f "$SBX/reports/phase-$ITER-regression-replay-results.md" && ! -f "$SBX/reports/phase-$ITER-ui-test-results.llm.md" ]]; then
  assert "hygiene: stale lane artifacts removed at partition entry" pass
else
  assert "hygiene: stale lane artifacts removed at partition entry" fail
fi

# ── 9. LLM regression set ────────────────────────────────────────────────────
out="$( (
  set -euo pipefail
  source "$LIB"
  _use_replay=yes REPLAY_FAILED="J-05 " R_LLM="J-02 J-05 " REQUIRED_JOURNEYS="J-01 J-02 J-05 "
  replay_lane_llm_regression_set
) )"
[[ "$out" == "J-02 J-05 " ]] && assert "llm_regression_set: replay on → REPLAY_FAILED+R_LLM deduped" pass \
  || { assert "llm_regression_set: replay on → REPLAY_FAILED+R_LLM deduped" fail; echo "    got: <$out>"; }

out="$( (
  set -euo pipefail
  source "$LIB"
  _use_replay=no REPLAY_FAILED="" R_LLM="" REQUIRED_JOURNEYS="J-01 J-02 "
  replay_lane_llm_regression_set
) )"
[[ "$out" == "J-01 J-02 " ]] && assert "llm_regression_set: hatch off → whole REQUIRED set" pass \
  || { assert "llm_regression_set: hatch off → whole REQUIRED set" fail; echo "    got: <$out>"; }

# ── 10. Merge + reconciliation footer (companion 1) ──────────────────────────
merge_case() {  # $1 = llm rows file content;  seeds replay file with J-06 PASS + J-07 FAIL
  reset_goldens
  REG="$SBX/reports/phase-$ITER-regression-replay-results.md"
  LLM="$SBX/reports/phase-$ITER-ui-test-results.llm.md"
  MERGED="$SBX/reports/phase-$ITER-ui-test-results.md"
  rm -f "$MERGED"
  cat > "$REG" <<'EOF'
**Browser QA Verdict:** FAIL

## Results Table
| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---|---|---|---|---|---|---|---|
| UT-J-06 | view dashboard | regression | P1 | e | ok | PASS | none |
| UT-J-07 | filter table | regression | P1 | e | step 3 failed | FAIL | none |
EOF
  printf '%s\n' "$1" > "$LLM"
  (
    set -euo pipefail
    source "$LIB"
    REPO_ROOT="$SBX"
    replay_lane_paths "$ITER"
    _use_replay=yes
    replay_lane_merge_results "$MERGED" "$LLM"
  )
}

merge_case '**Browser QA Verdict:** PASS

## Results Table
| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---|---|---|---|---|---|---|---|
| UT-J-07 | filter table | regression | P1 | e | re-confirmed by LLM | PASS | none |'
grep -q '^\*\*Browser QA Verdict:\*\* PASS' "$SBX/reports/phase-$ITER-ui-test-results.md" \
  && grep -E '^\| UT-J-07 ' "$SBX/reports/phase-$ITER-ui-test-results.md" | grep -qF '| PASS |' \
  && assert "merge: LLM re-confirm overrides replay FAIL (merged PASS)" pass \
  || assert "merge: LLM re-confirm overrides replay FAIL (merged PASS)" fail
grep -q 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md" \
  && grep -q 'J-07' <(grep 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md") \
  && assert "merge: reconciliation footer names the overturned journey (companion 1)" pass \
  || assert "merge: reconciliation footer names the overturned journey (companion 1)" fail

# ops-hardening iter-39 (TC-7, audit finding iter-38/T1): reproduces the EXACT bug — a raw
# replay FAIL overturned to an ANNOTATED verdict cell (not a bare "PASS"/"SKIP") must still be
# named in the footer. The old exact-string `grep -F '| PASS |'` missed both J-05-style
# (FAIL -> "PASS (steps ... verified)") and J-04-style (FAIL -> "SKIPPED (partial ...)") flips
# in iter-38, silently under-reporting the footer by omitting both.
merge_case '**Browser QA Verdict:** PASS

## Results Table
| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---|---|---|---|---|---|---|---|
| UT-J-07 | filter table | regression | P1 | e | steps 1,2,4 verified live; step 3 not executed | PASS (steps 1,2,4 verified live; step 3 not executed, see UT-J-04) | none |'
grep -q 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md" \
  && grep -q 'J-07' <(grep 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md") \
  && assert "merge: reconciliation footer names an ANNOTATED PASS overturn (J-05-style, TC-7)" pass \
  || assert "merge: reconciliation footer names an ANNOTATED PASS overturn (J-05-style, TC-7)" fail
# ops-hardening iter-39 FIX PASS (audit finding B6): a flip to PASS — and ONLY a flip to PASS — may
# be described as a live re-confirmation / false positive.
grep 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md" | grep -q 'J-07 -> PASS' \
  && grep 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md" | grep -q 'false positive' \
  && assert "merge: footer wording for a PASS flip claims re-confirmation (B6)" pass \
  || assert "merge: footer wording for a PASS flip claims re-confirmation (B6)" fail

merge_case '**Browser QA Verdict:** SKIPPED

## Results Table
| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---|---|---|---|---|---|---|---|
| UT-J-07 | filter table | regression | P1 | e | not executed live, judged unsafe to restart | SKIPPED (partial — see Actual) | none |'
grep -q 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md" \
  && grep -q 'J-07' <(grep 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md") \
  && assert "merge: reconciliation footer names a FAIL->SKIPPED overturn (J-04-style, TC-7)" pass \
  || assert "merge: reconciliation footer names a FAIL->SKIPPED overturn (J-04-style, TC-7)" fail
# ops-hardening iter-39 FIX PASS (audit finding B6): the SAME flip must NOT be described as a
# re-confirmation / disproven FAIL — SKIP means the journey was never re-verified. This is the
# assertion the fixed wording exists for; the pre-fix fixed sentence fails it.
grep 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md" | grep -q 'NOT re-verified' \
  && ! grep 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md" | grep -q 'false positive' \
  && assert "merge: footer wording for a SKIP flip does NOT claim re-confirmation (B6)" pass \
  || assert "merge: footer wording for a SKIP flip does NOT claim re-confirmation (B6)" fail

merge_case '**Browser QA Verdict:** PASS

## Results Table
| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---|---|---|---|---|---|---|---|
| UT-J-20 | new feature | smoke | P1 | e | ok | PASS | none |'
grep -q '^\*\*Browser QA Verdict:\*\* FAIL' "$SBX/reports/phase-$ITER-ui-test-results.md" \
  && assert "merge: un-overturned replay FAIL survives (merged FAIL)" pass \
  || assert "merge: un-overturned replay FAIL survives (merged FAIL)" fail
grep -q 'Reconciliation' "$SBX/reports/phase-$ITER-regression-replay-results.md" \
  && assert "merge: no footer when nothing was overturned" fail \
  || assert "merge: no footer when nothing was overturned" pass

# ── 10b. Merge: TARGET_JOURNEYS threads into --target (ops-hardening iter-42) ─
# A target journey (this iteration's OWN Target journeys: line) with zero rows
# forces the merged headline to BLOCKED, exactly like REQUIRED_JOURNEYS does
# for a required-still-passing journey (section 10) -- proves TARGET_JOURNEYS
# genuinely reaches merge_ui_test_results.py's --target flag through
# replay_lane_merge_results (the bash wiring), not just that merge()'s own
# Python self-test covers the guard in isolation.
reset_goldens
REG="$SBX/reports/phase-$ITER-regression-replay-results.md"
LLM="$SBX/reports/phase-$ITER-ui-test-results.llm.md"
MERGED="$SBX/reports/phase-$ITER-ui-test-results.md"
rm -f "$MERGED"
cat > "$REG" <<'EOF'
**Browser QA Verdict:** PASS

## Results Table
| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---|---|---|---|---|---|---|---|
| UT-J-06 | view dashboard | regression | P1 | e | ok | PASS | none |
EOF
cat > "$LLM" <<'EOF'
**Browser QA Verdict:** PASS

## Results Table
| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---|---|---|---|---|---|---|---|
EOF
(
  set -euo pipefail
  source "$LIB"
  REPO_ROOT="$SBX"
  replay_lane_paths "$ITER"
  _use_replay=yes
  TARGET_JOURNEYS="J-05 "   # this iteration's own target -- has ZERO rows in either lane above
  replay_lane_merge_results "$MERGED" "$LLM"
)
grep -q '^\*\*Browser QA Verdict:\*\* BLOCKED' "$MERGED" \
  && assert "merge: TARGET_JOURNEYS threads into --target -- missing target forces BLOCKED" pass \
  || assert "merge: TARGET_JOURNEYS threads into --target -- missing target forces BLOCKED" fail
grep -q '## Missing Target Journeys' "$MERGED" && grep -q 'UT-J-05' "$MERGED" \
  && assert "merge: Missing Target Journeys section names J-05" pass \
  || assert "merge: Missing Target Journeys section names J-05" fail

# TARGET_JOURNEYS unset (plain phase mode / no Target journeys line) → unchanged clean PASS, so
# every caller stays byte-identical until its own bash wiring sets TARGET_JOURNEYS.
rm -f "$MERGED"
(
  set -euo pipefail
  source "$LIB"
  REPO_ROOT="$SBX"
  replay_lane_paths "$ITER"
  _use_replay=yes
  replay_lane_merge_results "$MERGED" "$LLM"
)
grep -q '^\*\*Browser QA Verdict:\*\* PASS' "$MERGED" \
  && assert "merge: TARGET_JOURNEYS unset -> unchanged clean PASS" pass \
  || assert "merge: TARGET_JOURNEYS unset -> unchanged clean PASS" fail

# ── 11. Merge crash → lane-file fallback ─────────────────────────────────────
reset_goldens
REG="$SBX/reports/phase-$ITER-regression-replay-results.md"
LLM="$SBX/reports/phase-$ITER-ui-test-results.llm.md"
MERGED="$SBX/reports/phase-$ITER-ui-test-results.md"
echo "replay rows" > "$REG"
echo "llm rows" > "$LLM"
rm -f "$MERGED"
(
  set -euo pipefail
  source "$LIB"
  REPO_ROOT="$SBX"
  replay_lane_paths "$ITER"
  MERGE_RESULTS="$SBX/nonexistent-merge.py"   # force the merge to crash
  _use_replay=yes
  replay_lane_merge_results "$MERGED" "$LLM" 2>/dev/null
)
[[ "$(cat "$MERGED" 2>/dev/null)" == "llm rows" ]] \
  && assert "merge crash: falls back to copying the LLM lane file" pass \
  || assert "merge crash: falls back to copying the LLM lane file" fail

# ── 12. REL-5 flake discipline: rescue / infra-then-FAIL / never-retry-5 / non-6 ──
# 12a. infra-then-success: the retry rescues the lane — normal PASS path,
# no SKIPPED-INFRA state, raw artifact is the retry's own output.
reset_goldens
golden "J-01"
rm -f "$WORK/count12a"; : > "$WORK/svc12a"
out="$(STUB_REPLAY_RC_SEQ='6 0' STUB_REPLAY_COUNT_FILE="$WORK/count12a" \
       STUB_SVC_STAMP="$WORK/svc12a" RUN_PARTITION_LOG="$WORK/lane12a.log" \
       run_partition "J-01 J-02 ")"
[[ "$out" == "R_REPLAY=<J-01 >|R_LLM=<J-02 >|use=<yes>|failed=<>" && "$(cat "$WORK/count12a" 2>/dev/null)" == "2" ]] \
  && assert "12a rescue: retry turns an infra blip into a normal PASS lane" pass \
  || { assert "12a rescue: retry turns an infra blip into a normal PASS lane" fail; echo "    got: $out ($(cat "$WORK/count12a" 2>/dev/null) invocations)"; }
grep -q '^\*\*Browser QA Verdict:\*\* PASS' "$SBX/reports/phase-$ITER-regression-replay-results.md" \
  && assert "12a rescue: raw artifact is the retry's normal output (no SKIPPED-INFRA)" pass \
  || assert "12a rescue: raw artifact is the retry's normal output (no SKIPPED-INFRA)" fail

# 12b. infra-then-FAIL: the retry's rc=5 takes the normal REPLAY_FAILED path
# (first-observation assertion FAILs are re-confirmed by the LLM lane as today).
reset_goldens
golden "J-01"
rm -f "$WORK/count12b"
out="$(STUB_REPLAY_VERDICT=FAIL STUB_REPLAY_RC_SEQ='6 5' STUB_REPLAY_COUNT_FILE="$WORK/count12b" \
       RUN_PARTITION_LOG="$WORK/lane12b.log" run_partition "J-01 J-02 ")"
[[ "$out" == "R_REPLAY=<J-01 >|R_LLM=<J-02 >|use=<yes>|failed=<J-01 >" && "$(cat "$WORK/count12b" 2>/dev/null)" == "2" ]] \
  && assert "12b infra-then-FAIL: retry's assertion FAIL feeds REPLAY_FAILED unchanged" pass \
  || { assert "12b infra-then-FAIL: retry's assertion FAIL feeds REPLAY_FAILED unchanged" fail; echo "    got: $out ($(cat "$WORK/count12b" 2>/dev/null) invocations)"; }

# 12c. A clean assertion failure (rc=5) is NEVER retried. Discriminating
# sequence: a (forbidden) retry would hit rc=0 and flip the outcome.
reset_goldens
golden "J-01"
rm -f "$WORK/count12c"; : > "$WORK/svc12c"
out="$(STUB_REPLAY_VERDICT=FAIL STUB_REPLAY_RC_SEQ='5 0' STUB_REPLAY_COUNT_FILE="$WORK/count12c" \
       STUB_SVC_STAMP="$WORK/svc12c" run_partition "J-01 J-02 ")"
[[ "$out" == "R_REPLAY=<J-01 >|R_LLM=<J-02 >|use=<yes>|failed=<J-01 >" && "$(cat "$WORK/count12c" 2>/dev/null)" == "1" ]] \
  && assert "12c: assertion failure (rc=5) NEVER retried — 1 invocation, FAIL propagates as today" pass \
  || { assert "12c: assertion failure (rc=5) NEVER retried" fail; echo "    got: $out ($(cat "$WORK/count12c" 2>/dev/null) invocations)"; }
[[ ! -s "$WORK/svc12c" ]] \
  && assert "12c: zero service re-checks on an assertion failure" pass \
  || assert "12c: zero service re-checks on an assertion failure" fail

# 12d. A non-6 lane failure (rc=3, playwright missing) keeps the old no-retry
# generic fallback — no retry, no re-check, no SKIPPED-INFRA state.
reset_goldens
golden "J-01"
rm -f "$WORK/count12d"; : > "$WORK/svc12d"
out="$(STUB_REPLAY_RC_SEQ='3' STUB_REPLAY_COUNT_FILE="$WORK/count12d" \
       STUB_SVC_STAMP="$WORK/svc12d" RUN_PARTITION_LOG="$WORK/lane12d.log" \
       run_partition "J-01 J-02 ")"
[[ "$out" == "R_REPLAY=<>|R_LLM=<J-02 >|use=<no>|failed=<>" && "$(cat "$WORK/count12d" 2>/dev/null)" == "1" && ! -s "$WORK/svc12d" ]] \
  && assert "12d: non-6 failure (rc=3) keeps the old generic fallback — no retry, no state" pass \
  || { assert "12d: non-6 failure (rc=3) keeps the old generic fallback — no retry, no state" fail; echo "    got: $out ($(cat "$WORK/count12d" 2>/dev/null) invocations)"; }
grep -q "Replay lane failed (rc=3) — falling back to the LLM lane" "$WORK/lane12d.log" \
  && assert "12d: generic fallback warn text unchanged" pass \
  || assert "12d: generic fallback warn text unchanged" fail

# 12e. Reader decision (recorded in REL-5): SKIPPED-INFRA journeys still feed
# the LLM lane — the regression set after a double-6 is the WHOLE required set.
out="$( (
  set -euo pipefail
  source "$LIB"
  _use_replay=no REPLAY_FAILED="" R_LLM="J-02 " REQUIRED_JOURNEYS="J-01 J-02 " REPLAY_SKIPPED_INFRA=yes
  replay_lane_llm_regression_set
) )"
[[ "$out" == "J-01 J-02 " ]] && assert "12e: SKIPPED-INFRA → whole REQUIRED set feeds the LLM lane" pass \
  || { assert "12e: SKIPPED-INFRA → whole REQUIRED set feeds the LLM lane" fail; echo "    got: <$out>"; }

# ── 14. SPEED-22 mass-false-FAIL detection (lean-armed only) ─────────────────
# 14a. 3 of 4 replay journeys FAIL (majority, >2) with the canary capability
# armed → breaker arms, canaries = 2 lowest-ID FAILs.
reset_goldens
golden "J-01"; golden "J-02"; golden "J-03"; golden "J-04"
out="$(REPLAY_LANE_CANARY_CAPABLE=1 STUB_REPLAY_FAIL_SET="J-02 J-03 J-04" \
       run_partition "J-01 J-02 J-03 J-04 ")"
echo "$out" | grep -q 'massfail=<yes>|canaries=<J-02 J-03 >' \
  && assert "14a: 3/4 majority FAIL arms the breaker with the 2 lowest-ID canaries" pass \
  || { assert "14a: 3/4 majority FAIL arms the breaker with the 2 lowest-ID canaries" fail; echo "    got: $out"; }

# 14b. Same failure shape WITHOUT the capability flag (full pipeline) → no arm.
reset_goldens
golden "J-01"; golden "J-02"; golden "J-03"; golden "J-04"
out="$(STUB_REPLAY_FAIL_SET="J-02 J-03 J-04" run_partition "J-01 J-02 J-03 J-04 ")"
echo "$out" | grep -q 'massfail=' \
  && { assert "14b: full pipeline (no capability flag) never arms the breaker" fail; echo "    got: $out"; } \
  || assert "14b: full pipeline (no capability flag) never arms the breaker" pass

# 14c. Boundary: 2 FAILs (not >2) and a 3/6 non-majority never arm.
reset_goldens
golden "J-01"; golden "J-02"; golden "J-03"; golden "J-04"
out="$(REPLAY_LANE_CANARY_CAPABLE=1 STUB_REPLAY_FAIL_SET="J-03 J-04" \
       run_partition "J-01 J-02 J-03 J-04 ")"
echo "$out" | grep -q 'massfail=' \
  && { assert "14c: 2 FAILs (not >2) do not arm" fail; echo "    got: $out"; } \
  || assert "14c: 2 FAILs (not >2) do not arm" pass
reset_goldens
golden "J-01"; golden "J-02"; golden "J-03"; golden "J-04"; golden "J-05"; golden "J-06"
out="$(REPLAY_LANE_CANARY_CAPABLE=1 STUB_REPLAY_FAIL_SET="J-04 J-05 J-06" \
       run_partition "J-01 J-02 J-03 J-04 J-05 J-06 ")"
echo "$out" | grep -q 'massfail=' \
  && { assert "14c: 3/6 (exactly half) does not arm" fail; echo "    got: $out"; } \
  || assert "14c: 3/6 (exactly half) does not arm" pass

# 14d. Knob off → no arm even at 3/4.
reset_goldens
golden "J-01"; golden "J-02"; golden "J-03"; golden "J-04"
out="$(REPLAY_LANE_CANARY_CAPABLE=1 CHAIN_REPLAY_MASS_FAIL_BREAKER=false \
       STUB_REPLAY_FAIL_SET="J-02 J-03 J-04" run_partition "J-01 J-02 J-03 J-04 ")"
echo "$out" | grep -q 'massfail=' \
  && { assert "14d: CHAIN_REPLAY_MASS_FAIL_BREAKER=false disables detection" fail; echo "    got: $out"; } \
  || assert "14d: CHAIN_REPLAY_MASS_FAIL_BREAKER=false disables detection" pass

# ── 15. SPEED-22 canary verdict + void ───────────────────────────────────────
seed_mass_fail_files() {
  REG="$SBX/reports/phase-$ITER-regression-replay-results.md"
  CAN="$SBX/reports/phase-$ITER-ui-test-results.canary.md"
  cat > "$REG" <<'EOF'
**Browser QA Verdict:** FAIL

## Results Table
| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---|---|---|---|---|---|---|---|
| UT-J-02 | browse | regression | P1 | e | step 2 failed | FAIL | none |
| UT-J-03 | export | regression | P1 | e | step 1 failed | FAIL | none |
| UT-J-04 | filter | regression | P1 | e | step 4 failed | FAIL | none |
EOF
  cat > "$CAN" <<'EOF'
**Browser QA Verdict:** PASS

## Results Table
| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---|---|---|---|---|---|---|---|
| UT-J-02 | browse | regression | P1 | e | re-checked green | PASS | none |
| UT-J-03 | export | regression | P1 | e | re-checked green | PASS | none |
EOF
}

reset_goldens
seed_mass_fail_files
out="$( (
  set -euo pipefail
  source "$LIB"
  REPO_ROOT="$SBX"
  replay_lane_paths "$ITER"
  if replay_lane_canaries_all_pass "$CANARY_RESULTS" "J-02 J-03 "; then echo ALLPASS; else echo NOTPASS; fi
  REPLAY_FAILED="J-02 J-03 J-04 "
  REPLAY_CANARIES="J-02 J-03 "
  replay_lane_void_mass_fail "$ITER" >/dev/null 2>&1
  printf 'failed_after=<%s>\n' "${REPLAY_FAILED:-}"
) )"
echo "$out" | grep -q 'ALLPASS' \
  && assert "15: canaries_all_pass sees both green canary rows" pass \
  || { assert "15: canaries_all_pass sees both green canary rows" fail; echo "    got: $out"; }
echo "$out" | grep -q 'failed_after=<>' \
  && assert "15: void clears REPLAY_FAILED (no further re-confirms)" pass \
  || { assert "15: void clears REPLAY_FAILED" fail; echo "    got: $out"; }
REG="$SBX/reports/phase-$ITER-regression-replay-results.md"
[[ "$(grep -c '| SKIP |' "$REG")" == "3" ]] && ! grep -qF '| FAIL |' "$REG" \
  && assert "15: void rewrote every FAIL row to SKIP" pass \
  || assert "15: void rewrote every FAIL row to SKIP" fail
grep -q '_VOIDED (' "$REG" && grep -q 'voided: suspected selector' "$REG" \
  && assert "15: dated loud footer + voided note present" pass \
  || assert "15: dated loud footer + voided note present" fail
grep -q '^\*\*Browser QA Verdict:\*\* SKIPPED' "$REG" \
  && assert "15: raw-artifact headline recomputed from surviving rows" pass \
  || { assert "15: raw-artifact headline recomputed from surviving rows" fail; head -1 "$REG" | sed 's/^/        /'; }
[[ "$(cat "$SBX/runs/goal-session-rltest/state/goldens-regen-pending" 2>/dev/null | tr '\n' ' ')" == "J-02 J-03 J-04 " ]] \
  && assert "15: voided journeys queued for golden regeneration" pass \
  || assert "15: voided journeys queued for golden regeneration (got '$(cat "$SBX/runs/goal-session-rltest/state/goldens-regen-pending" 2>/dev/null | tr '\n' ' ')')" fail

# Conservative negatives: a FAIL canary row / a missing file never clear.
seed_mass_fail_files
sed -i 's/| UT-J-03 | export | regression | P1 | e | re-checked green | PASS |/| UT-J-03 | export | regression | P1 | e | really broken | FAIL |/' "$CAN"
out="$( (
  set -euo pipefail
  source "$LIB"
  REPO_ROOT="$SBX"
  replay_lane_paths "$ITER"
  if replay_lane_canaries_all_pass "$CANARY_RESULTS" "J-02 J-03 "; then echo ALLPASS; else echo NOTPASS; fi
) )"
[[ "$out" == "NOTPASS" ]] \
  && assert "15: a genuinely failing canary blocks the void (conservative)" pass \
  || assert "15: a genuinely failing canary blocks the void (conservative)" fail
out="$( (
  set -euo pipefail
  source "$LIB"
  REPO_ROOT="$SBX"
  replay_lane_paths "$ITER"
  rm -f "$CANARY_RESULTS"
  if replay_lane_canaries_all_pass "$CANARY_RESULTS" "J-02 "; then echo ALLPASS; else echo NOTPASS; fi
) )"
[[ "$out" == "NOTPASS" ]] \
  && assert "15: a missing canary file blocks the void (conservative)" pass \
  || assert "15: a missing canary file blocks the void (conservative)" fail

# ── 16. SPEED-22 canary file rides the merge as a middle input ───────────────
reset_goldens
seed_mass_fail_files
LLM="$SBX/reports/phase-$ITER-ui-test-results.llm.md"
MERGED="$SBX/reports/phase-$ITER-ui-test-results.md"
printf '%s\n' '**Browser QA Verdict:** PASS

## Results Table
| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---|---|---|---|---|---|---|---|
| UT-J-20 | target | smoke | P1 | e | ok | PASS | none |' > "$LLM"
rm -f "$MERGED"
(
  set -euo pipefail
  source "$LIB"
  REPO_ROOT="$SBX"
  replay_lane_paths "$ITER"
  _use_replay=yes
  replay_lane_merge_results "$MERGED" "$LLM"
)
grep -E '^\| UT-J-02 ' "$MERGED" | grep -qF '| PASS |' \
  && grep -E '^\| UT-J-03 ' "$MERGED" | grep -qF '| PASS |' \
  && assert "16: canary PASS rows override the replay FAILs in the merge (middle input)" pass \
  || assert "16: canary PASS rows override the replay FAILs in the merge (middle input)" fail
grep -E '^\| UT-J-04 ' "$MERGED" | grep -qF '| FAIL |' \
  && assert "16: an un-canaried FAIL still survives the merge (LLM lane must re-confirm it)" pass \
  || assert "16: an un-canaried FAIL still survives the merge" fail

# ── 13. SPEED-15 rung 2: budget-deferred regression narrowing ────────────────
# 13a. trim active + replay engaged + no-golden journeys → deferred set = R_LLM.
out="$( (
  set -euo pipefail
  source "$LIB"
  iter_budget_trim_active() { return 0; }   # stub: budget math is test-iter-budget's job
  _use_replay=yes R_LLM="J-04 J-02 " REPLAY_FAILED="J-05 " REQUIRED_JOURNEYS="J-02 J-04 J-05 "
  replay_lane_deferred_budget_set
) )"
[[ "$out" == "J-02 J-04 " ]] && assert "13a: trim+replay → deferred set is exactly R_LLM (sorted)" pass \
  || { assert "13a: trim+replay → deferred set is exactly R_LLM (sorted)" fail; echo "    got: <$out>"; }

# 13b. trim inactive → empty deferred set.
out="$( (
  set -euo pipefail
  source "$LIB"
  iter_budget_trim_active() { return 1; }
  _use_replay=yes R_LLM="J-02 " REPLAY_FAILED="" REQUIRED_JOURNEYS="J-02 "
  replay_lane_deferred_budget_set
) )"
[[ -z "${out// /}" ]] && assert "13b: trim inactive → nothing deferred" pass \
  || { assert "13b: trim inactive → nothing deferred" fail; echo "    got: <$out>"; }

# 13c. replay off → nothing deferred even when trim is active (the whole
# REQUIRED set must keep its LLM verifier).
out="$( (
  set -euo pipefail
  source "$LIB"
  iter_budget_trim_active() { return 0; }
  _use_replay=no R_LLM="J-02 " REPLAY_FAILED="" REQUIRED_JOURNEYS="J-02 "
  replay_lane_deferred_budget_set
) )"
[[ -z "${out// /}" ]] && assert "13c: replay off → nothing deferred (whole set keeps a verifier)" pass \
  || { assert "13c: replay off → nothing deferred" fail; echo "    got: <$out>"; }

# 13c2. Target-overlap exclusion: a journey that is BOTH a target and a
# no-golden required journey is dispatched anyway — it must never be deferred
# (a DEFERRED-BUDGET row beside its real PASS row would contradict the record).
out="$( (
  set -euo pipefail
  source "$LIB"
  iter_budget_trim_active() { return 0; }
  _use_replay=yes R_LLM="J-02 J-04 " REPLAY_FAILED="" REQUIRED_JOURNEYS="J-02 J-04 "
  replay_lane_deferred_budget_set "J-04 J-09 "
) )"
[[ "$out" == "J-02 " ]] && assert "13c2: target-overlapping journey excluded from deferral" pass \
  || { assert "13c2: target-overlapping journey excluded from deferral" fail; echo "    got: <$out>"; }

# 13d. Armed deferred set narrows the LLM set to the replay-FAIL re-confirms.
out="$( (
  set -euo pipefail
  source "$LIB"
  _use_replay=yes REPLAY_FAILED="J-05 " R_LLM="J-02 J-04 " REQUIRED_JOURNEYS="J-02 J-04 J-05 "
  REPLAY_DEFERRED_BUDGET="J-02 J-04 "
  replay_lane_llm_regression_set
) )"
[[ "$out" == "J-05 " ]] && assert "13d: narrowed LLM set keeps ONLY replay-FAIL re-confirms" pass \
  || { assert "13d: narrowed LLM set keeps ONLY replay-FAIL re-confirms" fail; echo "    got: <$out>"; }

# 13e. Deferred rows: appended to the merged file, DEFERRED-BUDGET verdict cell,
# and the REAL achievement gate treats the file as blocking.
MERGED13="$SBX/reports/phase-$ITER-ui-test-results.md"
cat > "$MERGED13" <<'EOF'
**Browser QA Verdict:** PASS

## Results Table
| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---|---|---|---|---|---|---|---|
| UT-J-01 | target | smoke | P1 | e | ok | PASS | none |
EOF
(
  set -euo pipefail
  source "$LIB"
  REPO_ROOT="$SBX"
  replay_lane_paths "$ITER"
  REPLAY_DEFERRED_BUDGET="J-02 J-04 "
  replay_lane_write_deferred_rows "$MERGED13" >/dev/null
)
[[ "$(grep -c 'DEFERRED-BUDGET' "$MERGED13")" -ge 2 ]] \
  && grep -q '^| UT-J-02 ' "$MERGED13" && grep -q '^| UT-J-04 ' "$MERGED13" \
  && assert "13e: DEFERRED-BUDGET rows appended for each deferred journey" pass \
  || assert "13e: DEFERRED-BUDGET rows appended for each deferred journey" fail
if python3 "$ENGINE_ROOT/scripts/automation/lib/goal_gate.py" results "$MERGED13" >/dev/null 2>&1; then
  assert "13e: real achievement gate BLOCKS on the deferred rows (rc 1)" fail
else
  assert "13e: real achievement gate BLOCKS on the deferred rows (rc 1)" pass
fi
grep -q '^\*\*Browser QA Verdict:\*\* PASS' "$MERGED13" \
  && assert "13e: headline verdict enum untouched (stays PASS/FAIL/SKIPPED)" pass \
  || assert "13e: headline verdict enum untouched (stays PASS/FAIL/SKIPPED)" fail

# 13f. Empty deferred set → writer is a byte-level no-op.
cat > "$MERGED13" <<'EOF'
**Browser QA Verdict:** PASS
| UT-J-01 | target | smoke | P1 | e | ok | PASS | none |
EOF
_before13="$(cat "$MERGED13")"
(
  set -euo pipefail
  source "$LIB"
  REPO_ROOT="$SBX"
  replay_lane_paths "$ITER"
  REPLAY_DEFERRED_BUDGET=""
  replay_lane_write_deferred_rows "$MERGED13" >/dev/null
)
[[ "$(cat "$MERGED13")" == "$_before13" ]] \
  && assert "13f: empty deferred set → writer no-op" pass \
  || assert "13f: empty deferred set → writer no-op" fail

echo ""
echo "RESULT: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]] || exit 1
exit 0
