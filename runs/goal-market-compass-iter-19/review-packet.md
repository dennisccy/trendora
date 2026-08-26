# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

(no changes)

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-market-compass-index.html     |  4 +-
 reports/goal-session-market-compass-retro.md       | 71 ++++++++++---------
 runs/goal-session-market-compass/session.json      |  6 +-
 .../state/assumptions.md                           | 82 ++++++++++++++++++++++
 runs/goal-session-market-compass/state/lessons.md  | 26 +------
 .../state/lessons.md.archive.md                    | 35 +++++++++
 .../state/retro-input.md                           |  4 +-
 runs/goal-session-market-compass/summary.md        |  6 +-
 runs/goal-session-market-compass/telemetry.jsonl   | 21 ++++++
 runs/goal-session-market-compass/trace/.next-step  |  2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |  4 ++
 11 files changed, 193 insertions(+), 68 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
