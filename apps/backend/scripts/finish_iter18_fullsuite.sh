#!/bin/bash
# iter-18 full-suite FINISHER (fix dispatch 2026-07-06) — SEQUENTIAL, spec-compliant.
#
# Context: the original run_iter18_fullsuite.sh orchestrator DIED, leaving the loaded_engine chunk
# running (orphaned -> systemd, durable) but the nonfixture chunk killed mid-`warm_engine` at
# test_iter27 (a slow 30y fixture setup misread as a hang), and no GRAND TOTAL ever computed.
#
# The iter-18 spec (DEFINITION OF DONE / escalation) requires the suite run "sequentially and alone
# ... do NOT run it concurrently with anything else on this host." So this finisher, launched fully
# detached (setsid/nohup) so it self-completes even if the launching agent dies:
#   1. WAITS for the already-running loaded_engine chunk to finish (its wrapper writes the real
#      "SUMMARY[loaded_engine] rc=..." line to the master ledger) so nonfixture runs ALONE,
#   2. archives any polluted nonfixture partial log (dead attempts would multi-count),
#   3. runs the nonfixture chunk CLEAN to completion, ALONE (heavy warm-up modules are SLOW, not hung),
#   4. computes GRAND TOTAL from the two clean chunk logs + an END sentinel.
#
# NOTE the wait grep matches the REAL summary line "SUMMARY[loaded_engine] rc=" at column 0; the
# progress prose below deliberately never prints that literal string (an earlier version self-matched).
set -u
BE=/home/dennis-chan/Git/trendora/apps/backend
Q=/home/dennis-chan/Git/trendora/reports/qa
MASTER="$Q/goal-mcp-loop-iter-18-fullsuite-chunked.log"
NF_LOG="$Q/goal-mcp-loop-iter-18-chunk-nonfixture.log"
LE_LOG="$Q/goal-mcp-loop-iter-18-chunk-loaded_engine.log"
LE_DONE_RE='^SUMMARY\[loaded_engine\] rc='
cd "$BE" || exit 99

NONLE=$(comm -23 <(ls tests/test_*.py | sort) <(grep -rl "loaded_engine" tests/ | grep -v conftest | sort))

echo "################ FULL-SUITE FINISHER START $(date -u +%FT%TZ) (pid $$) ################" >> "$MASTER"

# 1. WAIT for the running loaded_engine chunk to finish (run ALONE — spec: not concurrent).
echo "==== FINISHER polling master for the loaded_engine completion line before starting nonfixture $(date -u +%FT%TZ) ====" >> "$MASTER"
while ! grep -qE "$LE_DONE_RE" "$MASTER" 2>/dev/null; do sleep 60; done
echo "==== FINISHER saw loaded_engine complete; starting nonfixture ALONE $(date -u +%FT%TZ) ====" >> "$MASTER"

# 2. archive any polluted partial (preserve for audit; reviewer's line-484 hang reference lives here)
if [ -f "$NF_LOG" ]; then
  mv "$NF_LOG" "${NF_LOG%.log}.dead-partials-$(date -u +%Y%m%dT%H%M%SZ).log"
fi

# 3. nonfixture chunk, CLEAN log, to completion, ALONE
START=$(date -u +%s)
{
  echo "==================================================================="
  echo "==== CHUNK nonfixture START $(date -u +%FT%TZ) (finisher clean re-run, alone) ===="
  echo "cmd: pytest <50 NONLE modules> -v -ra -p no:cacheprovider --durations=25"
  echo "==================================================================="
} >> "$NF_LOG"
PYTHONUNBUFFERED=1 .venv/bin/python -u -m pytest $NONLE \
  -v -ra -p no:cacheprovider --durations=25 \
  --basetemp="/home/dennis-chan/.cache/trendora-iter18-nonfixture-rerun" >> "$NF_LOG" 2>&1
RC=$?
END=$(date -u +%s); WALL=$((END - START))
SUMLINE=$(grep -E "^(=+ .*(passed|failed|error).* =+|=+ no tests ran)" "$NF_LOG" | tail -1)
{
  echo "==== CHUNK nonfixture END $(date -u +%FT%TZ) rc=${RC} wall=${WALL}s ===="
  echo "SUMMARY[nonfixture] rc=${RC} wall=${WALL}s :: ${SUMLINE}"
  echo "==================================================================="
} >> "$NF_LOG"
echo "SUMMARY[nonfixture] rc=${RC} wall=${WALL}s :: ${SUMLINE}" >> "$MASTER"

# 4. GRAND TOTAL by summing per-test outcome lines across the two CLEAN chunk logs
GT() { grep -hcE "$1" "$NF_LOG" "$LE_LOG" 2>/dev/null | awk '{s+=$1} END{print s+0}'; }
P=$(GT " PASSED"); F=$(GT " FAILED"); E=$(GT " ERROR"); S=$(GT " SKIPPED")
{
  echo "==== GRAND TOTAL $(date -u +%FT%TZ) :: passed=${P} failed=${F} error=${E} skipped=${S} (collected 1381) ===="
  echo "################ FULL-SUITE FINISHER END $(date -u +%FT%TZ) ################"
} >> "$MASTER"
