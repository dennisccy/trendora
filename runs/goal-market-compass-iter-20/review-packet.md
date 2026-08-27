# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

(no changes)

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-market-compass/session.json      |   2 +-
 .../state/assumptions.md                           | 245 +++++----------------
 .../state/assumptions.md.archive.md                | 192 ++++++++++++++++
 runs/goal-session-market-compass/state/lessons.md  |  11 +-
 .../state/lessons.md.archive.md                    |  17 ++
 runs/goal-session-market-compass/telemetry.jsonl   |  23 ++
 runs/goal-session-market-compass/trace/.next-step  |   2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |   3 +
 8 files changed, 297 insertions(+), 198 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
