#!/bin/bash
# Durable, resumable chunk runner for the iter-18 full-suite completion (reviewer-endorsed
# "chunk by module and sum counts"). Runs ONE pytest invocation over the given targets,
# SEQUENTIALLY and ALONE, writing every per-test outcome (-v) to a durable log that survives
# agent/pipe death, and appending a machine-parseable SUMMARY line to a master ledger so counts
# can be summed even if a later chunk is interrupted.
#
# Usage: run_suite_chunk.sh <chunk_name> <chunk_log> <master_ledger> <pytest targets...>
set -u
NAME="$1"; LOG="$2"; MASTER="$3"; shift 3
cd /home/dennis-chan/Git/trendora/apps/backend || exit 99
START=$(date -u +%s)
{
  echo "==================================================================="
  echo "==== CHUNK ${NAME} START $(date -u +%FT%TZ) ===="
  echo "cmd: pytest $* -v -ra -p no:cacheprovider --durations=25"
  echo "==================================================================="
} >> "$LOG"

PYTHONUNBUFFERED=1 .venv/bin/python -u -m pytest "$@" \
  -v -ra -p no:cacheprovider --durations=25 --basetemp="/home/dennis-chan/.cache/trendora-iter18-${NAME}" >> "$LOG" 2>&1
RC=$?

END=$(date -u +%s)
WALL=$((END - START))
# pytest's terminal summary line, e.g. "= 12 failed, 900 passed, 8 skipped, 2 errors in 4200s ="
SUMLINE=$(grep -E "^(=+ .*(passed|failed|error).* =+|=+ no tests ran)" "$LOG" | tail -1)
{
  echo "==== CHUNK ${NAME} END $(date -u +%FT%TZ) rc=${RC} wall=${WALL}s ===="
  echo "SUMMARY[${NAME}] rc=${RC} wall=${WALL}s :: ${SUMLINE}"
  echo "==================================================================="
} >> "$LOG"
echo "SUMMARY[${NAME}] rc=${RC} wall=${WALL}s :: ${SUMLINE}" >> "$MASTER"
exit $RC
