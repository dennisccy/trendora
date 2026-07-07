#!/bin/bash
# iter-18 authoritative full-suite runner: two SEQUENTIAL chunks (non-fixture, then loaded_engine),
# each a single pytest invocation, all stdio to durable logs, machine-parseable SUMMARY lines summed
# into a master ledger + a GRAND TOTAL. Designed to be launched fully detached (setsid/nohup/disown)
# so it survives agent/harness/pipe death — the failure mode that killed dispatches 3-6.
set -u
BE=/home/dennis-chan/Git/trendora/apps/backend
Q=/home/dennis-chan/Git/trendora/reports/qa
RUN=/home/dennis-chan/Git/trendora/scripts/run_suite_chunk.sh
MASTER="$Q/goal-mcp-loop-iter-18-fullsuite-chunked.log"
cd "$BE" || exit 99

NONLE=$(comm -23 <(ls tests/test_*.py | sort) <(grep -rl "loaded_engine" tests/ | grep -v conftest | sort))
LE=$(grep -rl "loaded_engine" tests/ | grep -v conftest | sort)

echo "################ FULL-SUITE ORCHESTRATOR START $(date -u +%FT%TZ) (pid $$) ################" >> "$MASTER"

bash "$RUN" nonfixture    "$Q/goal-mcp-loop-iter-18-chunk-nonfixture.log"    "$MASTER" $NONLE
bash "$RUN" loaded_engine "$Q/goal-mcp-loop-iter-18-chunk-loaded_engine.log" "$MASTER" $LE

# ---- GRAND TOTAL by summing the two chunk logs' per-test outcome lines ----
GT() { grep -hcE "$1" "$Q/goal-mcp-loop-iter-18-chunk-nonfixture.log" "$Q/goal-mcp-loop-iter-18-chunk-loaded_engine.log" 2>/dev/null | awk '{s+=$1} END{print s+0}'; }
P=$(GT " PASSED"); F=$(GT " FAILED"); E=$(GT " ERROR"); S=$(GT " SKIPPED")
{
  echo "==== GRAND TOTAL $(date -u +%FT%TZ) :: passed=${P} failed=${F} error=${E} skipped=${S} (collected 1381) ===="
  echo "################ FULL-SUITE ORCHESTRATOR END $(date -u +%FT%TZ) ################"
} >> "$MASTER"
