# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

(no changes)

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                           | 91 +++++++++++++++++++++++
 runs/goal-session-ops-hardening/telemetry.jsonl   |  6 ++
 runs/goal-session-ops-hardening/trace/.next-step  |  2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl |  1 +
 4 files changed, 99 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
