# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

(no changes)

## Excluded-path stat (dependency/lockfile visibility)

 .../dispatch/.pump-alive                           |   4 +-
 runs/goal-session-market-compass/session.json      |   2 +-
 .../state/assumptions.md                           | 205 +++------------------
 .../state/assumptions.md.archive.md                | 180 ++++++++++++++++++
 .../goal-session-market-compass/state/blueprint.md |  10 +
 runs/goal-session-market-compass/state/lessons.md  |  52 +-----
 .../state/lessons.md.archive.md                    |  69 +++++++
 runs/goal-session-market-compass/telemetry.jsonl   |  13 ++
 runs/goal-session-market-compass/trace/.next-step  |   2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |   2 +
 .../state/preflight-verdict-history.jsonl          |   1 +
 11 files changed, 311 insertions(+), 229 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
