# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

(no changes)

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-ops-hardening-index.html      |   4 +-
 reports/goal-session-ops-hardening-retro.md        | 121 +++-------
 reports/perf-budgets.md                            | 252 +++++++++++++++++++++
 runs/goal-session-ops-hardening/.engine.lock/epoch |   2 +-
 runs/goal-session-ops-hardening/.engine.lock/pid   |   2 +-
 runs/goal-session-ops-hardening/engine.pid         |   2 +-
 runs/goal-session-ops-hardening/session.json       |  10 +-
 runs/goal-session-ops-hardening/state/blueprint.md |   4 +-
 .../state/retro-input.md                           |  90 ++++----
 runs/goal-session-ops-hardening/summary.md         |  61 +++--
 runs/goal-session-ops-hardening/telemetry.jsonl    |  22 ++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   3 +
 13 files changed, 411 insertions(+), 164 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
