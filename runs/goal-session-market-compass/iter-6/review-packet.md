# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

(no changes)

## Excluded-path stat (dependency/lockfile visibility)

 .../goal-session-market-compass/.engine.lock/epoch |   2 +-
 runs/goal-session-market-compass/.engine.lock/pid  |   2 +-
 runs/goal-session-market-compass/engine.pid        |   2 +-
 .../state/assumptions.md                           | 126 +++++++++++++++++----
 runs/goal-session-market-compass/telemetry.jsonl   |  15 +++
 runs/goal-session-market-compass/trace/.next-step  |   2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |   2 +
 .../state/drift-report.json                        |   2 +-
 8 files changed, 124 insertions(+), 29 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
