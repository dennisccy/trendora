#!/bin/bash
# iter-18 fix-dispatch-9 VERIFICATION — the reviewer-sanctioned "one loaded_engine re-run" of the fixes.
#
# Sequential + ALONE (memory note: never run two heavy pytest jobs concurrently on this host). It WAITS
# for the durable finisher's GRAND TOTAL sentinel (so it never overlaps the review-CRITICAL full-suite
# run), then runs the 6 previously-failing loaded_engine tests + the issue-3 pool-loader test in ONE
# invocation. Ordered so a loaded_engine test warms the 30y session fixture FIRST — the RSS-cap test
# (test_concurrent_coverage...) then sees the ru_maxrss lifetime peak the re-based 8192 cap accommodates,
# reproducing the exact full-suite condition that failed. Detached (setsid/nohup) so it self-completes.
set -u
BE=/home/dennis-chan/Git/trendora/apps/backend
Q=/home/dennis-chan/Git/trendora/reports/qa
MASTER="$Q/goal-mcp-loop-iter-18-fullsuite-chunked.log"
VLOG="$Q/goal-mcp-loop-iter-18-fixverify.log"
cd "$BE" || exit 99

echo "################ FIX-VERIFY START $(date -u +%FT%TZ) (pid $$) ################" >> "$VLOG"
echo "==== waiting for the finisher GRAND TOTAL before starting (run ALONE) $(date -u +%FT%TZ) ====" >> "$VLOG"
while ! grep -qE "^==== GRAND TOTAL" "$MASTER" 2>/dev/null; do sleep 60; done
# extra safety: ensure the finisher's nonfixture pytest is truly gone before we spawn ours
while pgrep -f "trendora-iter18-nonfixture-rerun" >/dev/null 2>&1; do sleep 30; done
echo "==== GRAND TOTAL observed + finisher pytest gone; starting fix-verify ALONE $(date -u +%FT%TZ) ====" >> "$VLOG"

START=$(date -u +%s)
PYTHONUNBUFFERED=1 .venv/bin/python -u -m pytest \
  tests/test_market_phase.py::test_2022_bear_reproduction \
  tests/test_scoring.py::test_each_stock_has_three_bucketed_explainable_scores \
  tests/test_api_research.py::test_phase_severity_lab_as_of_scopes_pool_and_echoes_cutoff \
  tests/test_api_research.py::test_regime_phase_factor_as_of_scopes_and_echoes \
  tests/test_api_research.py::test_factor_combination_as_of_scopes_pool_and_echoes_resolved_cutoff \
  tests/test_data_manager_concurrency_load.py::test_concurrent_coverage_single_flight_byte_identical_and_bounded \
  tests/test_seed_loader_pool.py \
  -v -ra -p no:cacheprovider \
  --basetemp="/home/dennis-chan/.cache/trendora-iter18-fixverify" >> "$VLOG" 2>&1
RC=$?
END=$(date -u +%s); WALL=$((END - START))
SUM=$(grep -E "^(=+ .*(passed|failed|error).* =+|=+ no tests ran)" "$VLOG" | tail -1)
echo "SUMMARY[fixverify] rc=${RC} wall=${WALL}s :: ${SUM}" >> "$VLOG"
echo "################ FIX-VERIFY END $(date -u +%FT%TZ) rc=${RC} ################" >> "$VLOG"
