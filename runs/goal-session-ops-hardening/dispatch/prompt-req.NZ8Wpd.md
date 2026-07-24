You are the coherence-auditor agent for goal-mode coherence enforcement.

Session ID: ops-hardening
Iteration index: 17
Iter name: goal-ops-hardening-iter-17

Blueprint (the contract): /home/dennis-chan/Git/trendora/runs/goal-session-ops-hardening/state/blueprint.md
Iter spec: /home/dennis-chan/Git/trendora/docs/phases/goal-ops-hardening-iter-17.md
Agent instructions: .claude/agents/coherence-auditor.md  <-- read this first
Methodology: .claude/skills/coherence-audit.md
(CLAUDE.md is already in your system prompt — do not Read it again.)

This iteration's changes — read in this order (judge-sanctioned context trim:
lower the context fed to you, never your effort):
1. Bounded diff (read FIRST if it exists): /home/dennis-chan/Git/trendora/runs/goal-session-ops-hardening/iter-17/iter-diff.md — hunks capped, noise excluded, truncations are NAMED in its header so you can git-diff just those files.
2. For anything it truncates — or if the file is absent —
Run: git diff c998936c86a1c12af905660a71f2a70109f0ccc5 -- . ':(exclude)*package-lock.json' ':(exclude)*yarn.lock' ':(exclude)*pnpm-lock.yaml' ':(exclude)*poetry.lock' ':(exclude)*uv.lock' ':(exclude)*Cargo.lock' ':(exclude)*.min.js' ':(exclude)*.min.css' ':(exclude)*.map' ':(exclude)runs/*' ':(exclude)reports/*' ':(exclude)docs/handoffs/*' ':(exclude)*.png' ':(exclude)*.jpg' ':(exclude)*.jpeg' ':(exclude)*.gif' ':(exclude)*.svg' ':(exclude)*.ico' ':(exclude)*.pdf' ':(exclude)*.woff' ':(exclude)*.woff2' ':(exclude)*.ttf'
  (this is the diff to review — lockfile/minified/binary/harness-artifact noise is pre-excluded)
Then run: git diff c998936c86a1c12af905660a71f2a70109f0ccc5 --stat -- '*package-lock.json' '*yarn.lock' '*pnpm-lock.yaml' '*poetry.lock' '*uv.lock' '*Cargo.lock' '*.min.js' '*.min.css' '*.map' 'runs/*' 'reports/*' 'docs/handoffs/*' '*.png' '*.jpg' '*.jpeg' '*.gif' '*.svg' '*.ico' '*.pdf' '*.woff' '*.woff2' '*.ttf'
  (stat of ONLY the excluded paths: if it lists dependency lockfiles, note WHICH changed and review the matching package.json/pyproject edit in the main diff; runs/ and reports/ churn is harness bookkeeping, outside review scope)
(Also `git status` for uncommitted changes. If the snapshot SHA is empty, diff against HEAD~1.)
UI surface map (read if it exists): reports/phase-goal-ops-hardening-iter-17-ui-surface-map.md

Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.

Write your verdict to: /home/dennis-chan/Git/trendora/runs/goal-session-ops-hardening/iter-17/coherence.md
The verdict line MUST appear first and start exactly with:
**Verdict:** COHERENCE-PASS
  or **Verdict:** COHERENCE-WARN
  or **Verdict:** COHERENCE-FAIL

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-b612f488.372082" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-b612f488.372082" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-b612f488.372082"