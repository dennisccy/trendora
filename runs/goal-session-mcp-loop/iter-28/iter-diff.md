# Iteration diff (bounded)

Files changed: 21. Shown in full: 21.

```diff
diff --git a/incredible_auto_dev/.claude/agents/goal-evaluator.md b/incredible_auto_dev/.claude/agents/goal-evaluator.md
index aee0353..b4c28e9 100644
--- a/incredible_auto_dev/.claude/agents/goal-evaluator.md
+++ b/incredible_auto_dev/.claude/agents/goal-evaluator.md
@@ -4,8 +4,8 @@ description: Goal-mode iteration evaluator. Reads iteration outputs (handoffs, b
 model: claude-opus-4-8
 tools: [Read, Glob, Grep, Bash, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.4.0
-last_updated: 2026-07-07
+version: 1.4.1
+last_updated: 2026-07-11
 ---
 
 # Goal Evaluator Agent
@@ -55,7 +55,7 @@ Also read this iteration's `coherence.md` and note its verdict. A `COHERENCE-FAI
 
 ### 2. Check anti-goals
 
-Follow methodology section B: answer every category explicitly (yes/no + citation), working from `iter-<N>/scan-report.md` (deterministic secret/dependency/license scan of the FULL diff) plus `iter-<N>/iter-diff.md` (bounded diff). Fallback when those files are absent: `git diff <snapshot>..HEAD --stat` first, then read only the implicated hunks — never ingest a full raw diff.
+Follow methodology section B: answer every category explicitly (yes/no + citation), working from `iter-<N>/scan-report.md` (deterministic secret/dependency/license scan of the product diff — tracked + untracked, harness bookkeeping path-excluded) plus `iter-<N>/iter-diff.md` (bounded diff). Fallback when those files are absent: `git diff <snapshot>..HEAD --stat` first, then read only the implicated hunks — never ingest a full raw diff.
 - Determine if any anti-goal was violated by this iteration
 - Classify violation severity: critical (committed credentials, unapproved paid-SaaS dependency, license violation, security backdoor, fabricated/substituted data) vs minor (e.g., inefficient pattern that's easy to fix); when unsure, treat as critical and say you were unsure
 
diff --git a/incredible_auto_dev/.claude/anti-patterns.md b/incredible_auto_dev/.claude/anti-patterns.md
index 0081f35..d733b10 100644
--- a/incredible_auto_dev/.claude/anti-patterns.md
+++ b/incredible_auto_dev/.claude/anti-patterns.md
@@ -305,3 +305,13 @@ This is especially bad for AI-agent scripts: the wrapped `claude` keeps consumin
 **Example (good):** `tmp_log=$(mktemp "${TMPDIR:-/tmp}/claude-quota-XXXXXX.log")`; on failure `_quota_preserve_failure_log "$tmp_log" claude-failure` moves it under `runs/<phase>/trace/`.
 
 **Detection:** `ls /tmp/pytest-of-$(id -un)` showing many numbered dirs, or `/tmp` littered with `claude-quota-*.log` / `<role>-<port>.log` files older than a day. During a healthy run there should be exactly ONE `/tmp/iad.*` dir per live pipeline job, and it disappears when the run exits.
+
+---
+
+## 22. A scanner that reads the pipeline's own output flags itself forever
+
+**Pattern:** The goal-mode secret scan built its input as `git diff <snapshot>` plus EVERY untracked file — no path exclusion. Goal mode commits only after evaluation, so the harness's own generated artifacts (`runs/<sid>/iter-N/scan-report.md` — the scanner's previous output, which lists the matched token excerpts — plus `iter-diff.md`, `runs/<sid>/trace/`, `reports/**`, handoffs) were untracked at scan time and got scanned. Each build re-detected the tokens quoted in the previous build's report; agents then *explained* the false positive in prose, planting more copies in evaluator logs, summaries, and specs.
+
+**Why it fails:** Self-referential and monotonically growing — the finding count compounds every iteration (observed 1 → 3 → rising in tapeology session `yahoo_fetch`) and permanently blocks the GOAL_ACHIEVED gate on a product whose real diff is clean. Two iterations spent "fixing" it made it worse: every explanation or allowlist edit that quotes the token is new scan input. A second-order effect: the two per-iteration artifact builds (lean-path early build vs. the pre-evaluator rebuild) scanned different snapshots of the accumulating bookkeeping, so consumers reported CLEAN while the canonical report said CRITICAL. A third: bookkeeping could exhaust the untracked-file cap (200), silently hiding product files from the scan entirely.
+
+**Prevention:** Verifiers scan the PRODUCT, never the pipeline's bookkeeping. `goal_gate_build_diff_artifacts` applies `CHAIN_SCAN_BOOKKEEPING_EXCLUDES` (default `runs reports docs/handoffs docs/phases`, mirroring `CHAIN_STEP_HASH_EXCLUDES`) as a `:(exclude)` pathspec on BOTH the tracked diff and the untracked enumeration; the scan-report footer records the active scope. Do NOT fix this class of bug with value-based allowlists ("this token is a known fake") — that blinds the detector to the same token in real source and breaks the case-05 judgment fixture, which plants a fake credential in product code precisely to prove detection. The distinction is path-based (generated output vs. source), never value-based. Any file a pipeline stage GENERATES that can quote findings (reports, traces, logs, specs, handoffs) must be excluded from every scanner/verifier input, and fixture secrets inside scanner code itself must be assembled at runtime (keyword and value split) so the scanner's own diff can never trip it — both enforced by self-tests (`scan_diff.py self-test` self-scan guard; `goal-gates.sh --self-test` cases 11/12).
diff --git a/incredible_auto_dev/.claude/letter-to-future-sessions.md b/incredible_auto_dev/.claude/letter-to-future-sessions.md
index fb12dd1..b7375dc 100644
--- a/incredible_auto_dev/.claude/letter-to-future-sessions.md
+++ b/incredible_auto_dev/.claude/letter-to-future-sessions.md
@@ -100,3 +100,4 @@ framework requirements. Other projects can ignore this section.
 - First post-cutover session should watch: `gate-report.md` appearing on any GOAL_ACHIEVED,
   `analyze_telemetry.py <session>/telemetry.jsonl` per-model rows, and whether sonnet-5
   fix-retries escalate correctly (look for `[escalation]` lines in the engine log).
+- 2026-07-11: model cutovers now have a runnable checklist — [`docs/model-cutover-playbook.md`](../docs/model-cutover-playbook.md) (EVO-4); future cutovers follow it and append their dated notes here (its step 9).
diff --git a/incredible_auto_dev/.claude/maintenance-protocol.md b/incredible_auto_dev/.claude/maintenance-protocol.md
index 764de8f..49318e4 100644
--- a/incredible_auto_dev/.claude/maintenance-protocol.md
+++ b/incredible_auto_dev/.claude/maintenance-protocol.md
@@ -78,6 +78,7 @@ resync, update the table in `.claude/model-orchestration.md` in the same commit,
 preflight (`claude -p --model <id> 'reply OK'` per id). Never re-pin a per-agent
 `model_override` in `agent.yaml` except as a deliberate temporary exception with a comment
 saying why and when to remove it.
+The full ordered checklist — spend gates, per-step evidence, rollback — is `docs/model-cutover-playbook.md` (EVO-4); follow it for every cutover.
 
 ## 7. After every pipeline-behavior change
 
diff --git a/incredible_auto_dev/.claude/model-orchestration.md b/incredible_auto_dev/.claude/model-orchestration.md
index 3849299..071ee8b 100644
--- a/incredible_auto_dev/.claude/model-orchestration.md
+++ b/incredible_auto_dev/.claude/model-orchestration.md
@@ -124,6 +124,7 @@ An agent's claim about its own work is a hypothesis, not evidence.
 | `CHAIN_GOAL_CONFIRM` | default `true`; the two-key GOAL_ACHIEVED confirm pass | `lib/goal-gates.sh` |
 | `CHAIN_SCAN_STRICT_DEPS` | `true` → new paid-SaaS dependencies become CRITICAL (block certification); default warn | `lib/scan_diff.py` |
 | `CHAIN_SCAN_DEP_ALLOWLIST` | package names (space/comma) never classified as paid-SaaS | `lib/scan_diff.py` |
+| `CHAIN_SCAN_BOOKKEEPING_EXCLUDES` | space-separated path prefixes excluded from the gate's scanned diff (default `runs reports docs/handoffs docs/phases` — the harness's own generated output; the scanner reads product changes only) | `lib/goal-gates.sh` |
 | `CHAIN_DISABLE_EFFORT_OVERRIDE` | `true` → everyone back to `--effort max` | `lib/quota-retry.sh` |
 | `CHAIN_STEP_CHECKPOINTS` | default `true`; step-level resume markers — a stall/quota kill never redoes a completed developer/reviewer/browser-qa step | `lib/checkpoint.sh` |
 | `CHAIN_AGENT_TIMEOUTS` | default `true`; per-agent runtime caps (~2.5-3× measured typicals) instead of one flat 7200s | `lib/quota-retry.sh` |
diff --git a/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md b/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
index 82e1d7d..9ef02da 100644
--- a/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
+++ b/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
@@ -8,8 +8,9 @@ your overall impression of the iteration.
 ## A. Evidence walk (do this before forming ANY opinion)
 
 1. **Deterministic reports first.** Read, if present in `runs/goal-session-<sid>/iter-<N>/`:
-   - `scan-report.md` — deterministic secret/dependency/license scan of the FULL iteration
-     diff. Findings here are facts; you do not need to re-derive them.
+   - `scan-report.md` — deterministic secret/dependency/license scan of the product
+     iteration diff (tracked + untracked; harness bookkeeping path-excluded). Findings here
+     are facts; you do not need to re-derive them.
    - `iter-diff.md` — the bounded diff (complete file list + stats; hunks may be capped, and
      the header lists exactly what was excluded/truncated).
    - `journeys-changed.md` — goal-edit drift note, present only when a recorded-passing
diff --git a/incredible_auto_dev/agents/goal-evaluator/agent.yaml b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
index de5c4a3..bbb9246 100644
--- a/incredible_auto_dev/agents/goal-evaluator/agent.yaml
+++ b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
@@ -10,6 +10,6 @@ tools_allowed:
 - Grep
 - Bash
 - Write
-version: 1.4.0
-last_updated: '2026-07-07'
+version: 1.4.1
+last_updated: '2026-07-11'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-evaluator/body.md b/incredible_auto_dev/agents/goal-evaluator/body.md
index 5a5e6da..3fb44a7 100644
--- a/incredible_auto_dev/agents/goal-evaluator/body.md
+++ b/incredible_auto_dev/agents/goal-evaluator/body.md
@@ -46,7 +46,7 @@ Also read this iteration's `coherence.md` and note its verdict. A `COHERENCE-FAI
 
 ### 2. Check anti-goals
 
-Follow methodology section B: answer every category explicitly (yes/no + citation), working from `iter-<N>/scan-report.md` (deterministic secret/dependency/license scan of the FULL diff) plus `iter-<N>/iter-diff.md` (bounded diff). Fallback when those files are absent: `git diff <snapshot>..HEAD --stat` first, then read only the implicated hunks — never ingest a full raw diff.
+Follow methodology section B: answer every category explicitly (yes/no + citation), working from `iter-<N>/scan-report.md` (deterministic secret/dependency/license scan of the product diff — tracked + untracked, harness bookkeeping path-excluded) plus `iter-<N>/iter-diff.md` (bounded diff). Fallback when those files are absent: `git diff <snapshot>..HEAD --stat` first, then read only the implicated hunks — never ingest a full raw diff.
 - Determine if any anti-goal was violated by this iteration
 - Classify violation severity: critical (committed credentials, unapproved paid-SaaS dependency, license violation, security backdoor, fabricated/substituted data) vs minor (e.g., inefficient pattern that's easy to fix); when unsure, treat as critical and say you were unsure
 
diff --git a/incredible_auto_dev/benchmarks/experiments.md b/incredible_auto_dev/benchmarks/experiments.md
index 52f646c..a74cb4c 100644
--- a/incredible_auto_dev/benchmarks/experiments.md
+++ b/incredible_auto_dev/benchmarks/experiments.md
@@ -50,3 +50,43 @@ Entry format contract (grep-able; pinned by
   catch this: its stub engines echo the env var without validating it against the
   real quota-retry contract. Any rerun is a fresh PRE/POST pair under fresh user
   approval (G9) — this entry stays as the record of the aborted attempt.
+
+---
+
+## PRE bench-20260710-2117 · 2026-07-10T21:17:11Z
+- framework-sha: c48f25047126a52ccec88f9b2347403280b1c22b (dirty: false)
+- fixture: todo-app · max-iter 2
+- hypothesis: Baseline @ c48f25047126: chain reaches GOAL_ACHIEVED with 3/3 journeys within --max-iter 2 on the todo-app fixture
+- metrics + prediction (mechanical --predict): final_status==GOAL_ACHIEVED;journeys_passing_after>=3
+
+## POST bench-20260710-2117 · 2026-07-10T22:42:06Z
+- results: benchmarks/results/20260710-224206-c48f25047126.json
+- headline: status=BUDGET_EXHAUSTED last_verdict=CONTINUE journeys=0/3 iters=2 engine_exit=0 wall=5095s cost=$10.885761
+- predicate: final_status==GOAL_ACHIEVED → false (final_status='BUDGET_EXHAUSTED')
+- predicate: journeys_passing_after>=3 → false (journeys_passing_after=0)
+- verdict-vs-prediction: REFUTED
+- assessment 2026-07-10: GENUINE CHAIN RESULT, not infra — environment healthy (zero
+  quota pauses, engine exit 0, Chrome MCP + playwright preflight-verified, friction
+  counters all zero). The chain BUILT all three journeys (reviewer PASS,
+  COHERENCE-PASS, scan CLEAN, 15/15 pytest) but its browser-QA lane produced zero
+  journey evidence in BOTH iterations, so the evaluator honestly held J-01..J-03 at
+  `unknown` (0/3 passing). Root causes per evaluator-log + trace/0014-qa.log in the
+  kept scratch: (1) the generic `scripts/start-backend.sh` template copied with the
+  framework subrepo set (uvicorn / apps-backend layout) shadowed the fixture
+  project-template's `.venv/bin/python app.py`, so nothing served on 127.0.0.1:5177
+  (README Known Limitation 1 made concrete); (2) a headless write-permission prompt
+  blocked the QA report and the retro-analyst report from persisting. Both are
+  framework gaps this baseline exists to expose; fixing them should move journeys
+  0→3 in a future compare. REFUTED stands as the recorded baseline. Kept scratch:
+  ~/.cache/chain-bench-tmp/bench-bench-20260710-2117.EMAuTK
+- note 2026-07-10: main was REBASED (by the repo owner, outside this protocol) between
+  this run's completion and the close-out commit — a judgment-fixture amendment
+  (tests/judgment/goal-evaluator/case-05-secret-committed, 4 files) was inserted deep
+  in history and everything re-picked. The measured shas b172cea005aa (aborted
+  attempt) and c48f25047126 (recorded baseline) are therefore no longer reachable
+  from main; both are pinned by local tags bench-20260710-2110-framework-sha /
+  bench-20260710-2117-framework-sha so gc never prunes them. Substantively nothing
+  changes: `git diff c48f25047126 1814e24 -- .claude scripts config templates
+  CLAUDE.md benchmarks` is EMPTY (the rebased equivalent of the measured commit
+  differs only in tests/judgment/**, which the benchmark scratch never copies) — the
+  measured tree is byte-identically reproducible from the new main.
diff --git a/incredible_auto_dev/benchmarks/results/20260710-224206-c48f25047126.json b/incredible_auto_dev/benchmarks/results/20260710-224206-c48f25047126.json
new file mode 100644
index 0000000..48a0d1a
--- /dev/null
+++ b/incredible_auto_dev/benchmarks/results/20260710-224206-c48f25047126.json
@@ -0,0 +1,201 @@
+{
+  "meta": {
+    "date_utc": "2026-07-10T21:17:11Z",
+    "framework_sha": "c48f25047126a52ccec88f9b2347403280b1c22b",
+    "framework_dirty": false,
+    "fixture": "todo-app",
+    "session_id": "bench-20260710-2117",
+    "max_iter": 2,
+    "hypothesis": "Baseline @ c48f25047126: chain reaches GOAL_ACHIEVED with 3/3 journeys within --max-iter 2 on the todo-app fixture",
+    "predict": [
+      "final_status==GOAL_ACHIEVED",
+      "journeys_passing_after>=3"
+    ],
+    "chain_env": {
+      "CHAIN_AGENT_BACKEND": "claude",
+      "CHAIN_BENCH_MAX_ITER": "2",
+      "CHAIN_BENCH_SESSION_ID": "bench-20260710-2117"
+    },
+    "model_tiers_sha256": "1d096808ad8eb0b5fcc863b8c71403dced292d24c4e8021d940abda52e298896"
+  },
+  "outcome": {
+    "engine_exit_code": 0,
+    "final_status": "BUDGET_EXHAUSTED",
+    "last_verdict": "CONTINUE",
+    "iterations_used": 2,
+    "journeys_passing_after": 0,
+    "journeys_total": 3,
+    "attempt1_review_fails": 0,
+    "malformed_verdicts": 0,
+    "wall_seconds": 5095
+  },
+  "economics": {
+    "agents": {
+      "bench-20260710-2117": {
+        "sources": [
+          "/home/dennis-chan/.cache/chain-bench-tmp/bench-bench-20260710-2117.EMAuTK/scratch/runs/goal-session-bench-20260710-2117/telemetry.jsonl"
+        ],
+        "total": {
+          "invocations": 12,
+          "errors": 0,
+          "gen_ai.usage.input_tokens": 106538,
+          "gen_ai.usage.output_tokens": 153627,
+          "gen_ai.usage.cache_read_input_tokens": 6596945,
+          "gen_ai.usage.cache_creation_input_tokens": 625374,
+          "gen_ai.usage.total_cost_usd": 10.885761,
+          "duration_ms": 2039676,
+          "duration_api_ms": 1997216,
+          "num_turns": 191,
+          "cache_hit_ratio": 0.9841
+        },
+        "by_agent": {
+          "goal-decomposer": {
+            "invocations": 2,
+            "errors": 0,
+            "gen_ai.usage.input_tokens": 18775,
+            "gen_ai.usage.output_tokens": 40904,
+            "gen_ai.usage.cache_read_input_tokens": 703724,
+            "gen_ai.usage.cache_creation_input_tokens": 99633,
+            "gen_ai.usage.total_cost_usd": 2.464667,
+            "duration_ms": 585836,
+            "duration_api_ms": 582082,
+            "num_turns": 28,
+            "cache_hit_ratio": 0.974
+          },
+          "developer": {
+            "invocations": 1,
+            "errors": 0,
+            "gen_ai.usage.input_tokens": 10348,
+            "gen_ai.usage.output_tokens": 12056,
+            "gen_ai.usage.cache_read_input_tokens": 1666554,
+            "gen_ai.usage.cache_creation_input_tokens": 91169,
+            "gen_ai.usage.total_cost_usd": 1.258864,
+            "duration_ms": 172338,
+            "duration_api_ms": 147502,
+            "num_turns": 32,
+            "cache_hit_ratio": 0.9938
+          },
+          "reviewer": {
+            "invocations": 1,
+            "errors": 0,
+            "gen_ai.usage.input_tokens": 10022,
+            "gen_ai.usage.output_tokens": 5352,
+            "gen_ai.usage.cache_read_input_tokens": 359482,
+            "gen_ai.usage.cache_creation_input_tokens": 36502,
+            "gen_ai.usage.total_cost_usd": 0.437203,
+            "duration_ms": 64139,
+            "duration_api_ms": 61431,
+            "num_turns": 13,
+            "cache_hit_ratio": 0.9729
+          },
+          "goal-evaluator": {
+            "invocations": 2,
+            "errors": 0,
+            "gen_ai.usage.input_tokens": 18934,
+            "gen_ai.usage.output_tokens": 59864,
+            "gen_ai.usage.cache_read_input_tokens": 1616011,
+            "gen_ai.usage.cache_creation_input_tokens": 176222,
+            "gen_ai.usage.total_cost_usd": 4.161496,
+            "duration_ms": 806230,
+            "duration_api_ms": 802708,
+            "num_turns": 38,
+            "cache_hit_ratio": 0.9884
+          },
+          "iteration-summarizer": {
+            "invocations": 2,
+            "errors": 0,
+            "gen_ai.usage.input_tokens": 18912,
+            "gen_ai.usage.output_tokens": 15712,
+            "gen_ai.usage.cache_read_input_tokens": 989911,
+            "gen_ai.usage.cache_creation_input_tokens": 90717,
+            "gen_ai.usage.total_cost_usd": 1.133691,
+            "duration_ms": 168055,
+            "duration_api_ms": 164899,
+            "num_turns": 32,
+            "cache_hit_ratio": 0.9813
+          },
+          "readme-maintainer": {
+            "invocations": 2,
+            "errors": 0,
+            "gen_ai.usage.input_tokens": 18610,
+            "gen_ai.usage.output_tokens": 5558,
+            "gen_ai.usage.cache_read_input_tokens": 474533,
+            "gen_ai.usage.cache_creation_input_tokens": 55228,
+            "gen_ai.usage.total_cost_usd": 0.612928,
+            "duration_ms": 77006,
+            "duration_api_ms": 73830,
+            "num_turns": 19,
+            "cache_hit_ratio": 0.9623
+          },
+          "coherence-auditor": {
+            "invocations": 1,
+            "errors": 0,
+            "gen_ai.usage.input_tokens": 10913,
+            "gen_ai.usage.output_tokens": 12507,
+            "gen_ai.usage.cache_read_input_tokens": 711475,
+            "gen_ai.usage.cache_creation_input_tokens": 53850,
+            "gen_ai.usage.total_cost_usd": 0.756887,
+            "duration_ms": 142330,
+            "duration_api_ms": 141139,
+            "num_turns": 25,
+            "cache_hit_ratio": 0.9849
+          },
+          "retro-analyst": {
+            "invocations": 1,
+            "errors": 0,
+            "gen_ai.usage.input_tokens": 24,
+            "gen_ai.usage.output_tokens": 1674,
+            "gen_ai.usage.cache_read_input_tokens": 75255,
+            "gen_ai.usage.cache_creation_input_tokens": 22053,
+            "gen_ai.usage.total_cost_usd": 0.060026,
+            "duration_ms": 23742,
+            "duration_api_ms": 23625,
+            "num_turns": 4,
+            "cache_hit_ratio": 0.9997
+          }
+        },
+        "by_model": {
+          "claude-opus-4-8": {
+            "invocations": 4,
+            "errors": 0,
+            "gen_ai.usage.input_tokens": 37709,
+            "gen_ai.usage.output_tokens": 100768,
+            "gen_ai.usage.cache_read_input_tokens": 2319735,
+            "gen_ai.usage.cache_creation_input_tokens": 275855,
+            "gen_ai.usage.total_cost_usd": 6.626163,
+            "duration_ms": 1392066,
+            "duration_api_ms": 1384790,
+            "num_turns": 66,
+            "cache_hit_ratio": 0.984
+          },
+          "claude-sonnet-5": {
+            "invocations": 7,
+            "errors": 0,
+            "gen_ai.usage.input_tokens": 68805,
+            "gen_ai.usage.output_tokens": 51185,
+            "gen_ai.usage.cache_read_input_tokens": 4201955,
+            "gen_ai.usage.cache_creation_input_tokens": 327466,
+            "gen_ai.usage.total_cost_usd": 4.199572,
+            "duration_ms": 623868,
+            "duration_api_ms": 588801,
+            "num_turns": 121,
+            "cache_hit_ratio": 0.9839
+          },
+          "claude-haiku-4-5": {
+            "invocations": 1,
+            "errors": 0,
+            "gen_ai.usage.input_tokens": 24,
+            "gen_ai.usage.output_tokens": 1674,
+            "gen_ai.usage.cache_read_input_tokens": 75255,
+            "gen_ai.usage.cache_creation_input_tokens": 22053,
+            "gen_ai.usage.total_cost_usd": 0.060026,
+            "duration_ms": 23742,
+            "duration_api_ms": 23625,
+            "num_turns": 4,
+            "cache_hit_ratio": 0.9997
+          }
+        }
+      }
+    }
+  }
+}
diff --git a/incredible_auto_dev/docs/improvement-roadmap.md b/incredible_auto_dev/docs/improvement-roadmap.md
index 7855701..ab6a921 100644
--- a/incredible_auto_dev/docs/improvement-roadmap.md
+++ b/incredible_auto_dev/docs/improvement-roadmap.md
@@ -281,7 +281,7 @@ the system measures itself, and how it survives the next model change.
   catalog count in CLAUDE.md ("19 agents"), flag it — CLAUDE.md is ask-first class.
 
 ### EVO-3 · Automated benchmark harness
-- **Priority:** P0 · **Effort:** L (3 slices) · **Risk:** MED · **Status:** IN-PROGRESS
+- **Priority:** P0 · **Effort:** L (3 slices) · **Risk:** MED · **Status:** DONE
   *(slice (a) — fixture project — implemented 2026-07-10:
   `benchmarks/fixtures/todo-app/` is a runnable but deliberately BARE Flask +
   vanilla-JS + pytest scaffold — shell page + `/health` on fixed port 5177, storage
@@ -362,7 +362,45 @@ the system measures itself, and how it survives the next model change.
   AGENT-RUNNABLE exactly as the chain finds it — venv bootstrap per the fixture
   project-template, pytest 3/3, app boot with `/health` 200 on port 5177,
   goal_lint exit 0 inside scratch. No runner defects found; no edits needed.)*
-- **Problem:** "did my framework change help or hurt?" currently has no answer a weaker
+  *(slice (c) — compare tool + FIRST REAL BASELINE — implemented 2026-07-10 by
+  that same certifying session: `scripts/automation/lib/benchmark_compare.py`
+  (delta table over wall / est. cost / tokens in+out / journeys passing /
+  attempt-1 review FAILs / malformed verdicts / final status+verdict; REGRESS
+  if wall or cost +>25% or journeys-passing dropped; any of those three verdict
+  inputs missing or literal "unknown (...)" → INCOMPARABLE → verdict UNKNOWN,
+  never a guessed number — regress-worthy comparable signals survive as a note;
+  exit 0 OK / 3 REGRESS / 4 UNKNOWN / 2 usage; `--self-test` registered in
+  run-evals §2, suite 96/96).
+  Baseline attempt 1 (bench-20260710-2110 @ b172cea005aa) ABORTED in 2s with
+  zero agent spend: slice (b) exported the invalid `CHAIN_AGENT_BACKEND=headless`
+  (quota-retry accepts interactive|claude|codex; headless dispatch = `claude`) —
+  a defect the offline suite structurally cannot catch (stub engines echo the
+  env var unvalidated; only a real engine validates it). Runner+test fixed
+  (commit c48f250); aborted attempt kept as a record: results JSON committed,
+  ledger PRE/POST retained with an appended dated correction line (append-only).
+  Attempt 2 = THE RECORDED BASELINE (fresh G9 approval, fresh PRE entry):
+  bench-20260710-2117 @ c48f25047126 · hypothesis "chain reaches GOAL_ACHIEVED
+  with 3/3 journeys within --max-iter 2 on the todo-app fixture" →
+  **verdict-vs-prediction: REFUTED** (mechanical; both predicates false) ·
+  final_status=BUDGET_EXHAUSTED · last_verdict=CONTINUE · journeys 0/3 (all
+  honestly `unknown` — zero browser evidence) · iterations 2 (verify-only
+  baseline + one full-depth build) · wall 5095s (~85 min) · est. cost $10.89
+  (106.5k in / 153.6k out tokens, 12 invocations; goal-evaluator $4.16 +
+  goal-decomposer $2.46 dominate) · results
+  `benchmarks/results/20260710-224206-c48f25047126.json`. GENUINE CHAIN
+  RESULT, not infra (environment healthy; friction counters zero): the chain
+  built all three journeys to reviewer-PASS / COHERENCE-PASS / 15-of-15-pytest
+  quality, but its browser-QA lane produced ZERO evidence in both iterations —
+  (a) the generic `scripts/start-backend.sh` template in the subrepo set
+  (uvicorn, apps/backend layout) shadowed the fixture project-template's
+  `.venv/bin/python app.py`, so nothing served on 5177 (README Known
+  Limitation 1 made concrete); (b) a headless write-permission prompt blocked
+  the QA report and the retro-analyst report from persisting. Both are
+  framework gaps the baseline exists to expose — prime §16-promotion
+  candidates; fixing them should move journeys 0→3 in the next compare.
+  Compare sanity: baseline-vs-baseline → all deltas 0, verdict OK, exit 0.
+  Standing usage rule: §9 "When to benchmark". EVO-3 complete; body archiving
+  left to a future tidy pass (REL-1 precedent).)*
   maintainer can trust. The per-session tripwire compares within a session; nothing
   compares across framework versions.
 - **Current state:** no `benchmarks/` dir. Headless engine is scriptable
@@ -410,7 +448,19 @@ the system measures itself, and how it survives the next model change.
   NEVER wire this into CI.
 
 ### EVO-4 · Model-cutover playbook
-- **Priority:** P0 · **Effort:** S · **Risk:** LOW · **Status:** TODO
+- **Priority:** P0 · **Effort:** S · **Risk:** LOW · **Status:** DONE
+  *(implemented 2026-07-11: `docs/model-cutover-playbook.md` — all 9 steps as exact
+  command(s) · expected evidence · failure/abort path, every command verified against
+  the scripts' own headers; three unmissable user checkpoints (step 2 tier-change
+  approval, step 6 judgment-fixture G9 gate, step 7 per-run benchmark G9 gate) with a
+  spend-class label on every step (step 1 preflight = cents but still tell the user;
+  step 6 = the runner's printed estimate; step 7 ≈ $11 + ~1.5h wall per run at baseline
+  scale); rollback section mirrors steps 2-6 around a single-commit revert; cross-links
+  landed both ways — one line in the letter's deployment section and one in
+  maintenance-protocol §6, playbook links out to §9 "When to benchmark",
+  run-judgment-evals.sh and REL-1's fixtures. Verify grep hits all three files; evals
+  96/96. S item — implementer flips DONE (G8 fresh-session certification is M/L-only);
+  body archiving left to a future tidy pass (REL-1 precedent).)*
 - **Problem:** the Fable→Opus/Sonnet cutover was done once, by a strong model, with the
   procedure living in its head and partially in the letter. The next cutover will be
   done by a weaker model.
@@ -426,7 +476,13 @@ the system measures itself, and how it survives the next model change.
   6. Run REL-1 judgment fixtures: `./scripts/automation/run-judgment-evals.sh
      --yes-spend` (G9: user-approved spend; the runner prints the estimate and
      refuses without the flag).
-  7. Run EVO-3 benchmark before/after (mark "pending EVO-3" until it ships).
+  7. Run the EVO-3 benchmark before AND after the flip (§9 "When to benchmark"):
+     `./scripts/automation/run-benchmark.sh --hypothesis '<prediction>'
+     [--predict '<key OP value>']... --yes-spend` on the pre-cutover sha, again
+     on the post-cutover sha, then `python3
+     scripts/automation/lib/benchmark_compare.py benchmarks/results/<pre>.json
+     benchmarks/results/<post>.json` — REGRESS (exit 3) → do not proceed with
+     the cutover without a human decision.
   8. First-session watchlist: `gate-report.md` appears on any GOAL_ACHIEVED;
      `[escalation]` lines in the engine log; per-model rows in
      `analyze_telemetry.py <session>/telemetry.jsonl`.
@@ -482,6 +538,25 @@ evaluator ~17m, decomposer ~8m — typicals from the timeout table comments,
 `scripts/automation/lib/agent_permissions.py:88-110`). Rule for ALL items here: EVO-3
 benchmark (or a real session's telemetry) before AND after (G8).
 
+**When to benchmark (standing rule — the EVO-3 harness):**
+- BEFORE and AFTER any SPEED-*/TOKEN-* experiment in this section, and during
+  EVO-4 model cutovers (playbook step 7). Same fixture, same `--max-iter`.
+- Run (G9 — user-approved spend per run; order-of-dollars, ~1.5-5h wall):
+  `./scripts/automation/run-benchmark.sh --hypothesis '<one-line prediction>'
+  [--predict '<key OP value>']... --yes-spend`. The runner refuses without the
+  hypothesis (G8) or on a dirty tree — commit first; the PRE entry in
+  `benchmarks/experiments.md` (append-only ledger) is written BEFORE the engine
+  launches and the POST entry grades `--predict` predicates mechanically
+  (CONFIRMED/REFUTED/MIXED). Predicate keys = scalar keys of the results JSON's
+  meta+outcome blocks (e.g. `final_status`, `journeys_passing_after`).
+- Compare: `python3 scripts/automation/lib/benchmark_compare.py <old>.json
+  <new>.json` → delta table + verdict OK / REGRESS / UNKNOWN (exit 0/3/4);
+  REGRESS = wall or cost +>25% or journeys-passing dropped; incomparable
+  verdict inputs → UNKNOWN, never a guess.
+- Afterwards commit the new results JSON + ledger entries; whatever completed
+  IS the measurement — a rerun for a prettier number needs fresh approval and
+  a fresh PRE entry.
+
 ### SPEED-1 · Refactor browser-qa into a function (no behavior change)
 - **Priority:** P1 · **Effort:** S · **Risk:** LOW · **Status:** TODO
 - **Problem:** the browser-qa section of the lean executor is a ~290-line inline block;
@@ -1048,14 +1123,19 @@ territory).
 - **Problem:** `scan_diff.py` catches common credential shapes only (letter explicitly:
   "regex-grade… not exotic secrets").
 - **Current state:** per-iteration diff scan via `goal_gate_build_diff_artifacts`
-  (`lib/goal-gates.sh`) → `iter-<N>/scan-report.md`; CRITICAL blocks GOAL_ACHIEVED
-  (`goal-gates.sh:79-146`).
+  (`lib/goal-gates.sh:57`) → `iter-<N>/scan-report.md`; CRITICAL blocks GOAL_ACHIEVED
+  (`goal_gate_achievement`, `goal-gates.sh:107`). The scanned diff is the PRODUCT diff:
+  harness bookkeeping is path-excluded via `CHAIN_SCAN_BOOKKEEPING_EXCLUDES` (SEC-5).
 - **Change spec:** new `scripts/automation/lib/security_scan.sh`: if `gitleaks` (or
   `trufflehog`) is on PATH — run it in diff mode per iteration (append findings to
   `scan-report.md` with the same CRITICAL semantics) and full-tree on GOAL_ACHIEVED
   before the two-key confirm; if absent — one WARN line ("gitleaks not installed —
-  regex scan only") and proceed. Eval fixture: planted fake secret detected in a
-  fixture diff (skip cleanly when tool absent so CI stays green).
+  regex scan only") and proceed. Diff mode MUST consume the same bookkeeping-excluded
+  diff `goal_gate_build_diff_artifacts` builds (SEC-5) — feeding gitleaks the raw
+  tracked+untracked tree reintroduces the self-scan recursion (anti-pattern #22); the
+  full-tree pass on GOAL_ACHIEVED must likewise skip `runs/ reports/ docs/handoffs/
+  docs/phases/`. Eval fixture: planted fake secret detected in a fixture diff (skip
+  cleanly when tool absent so CI stays green).
 - **DoD:** with gitleaks installed, planted secret → CRITICAL → gate demotion; without,
   behavior unchanged + warning; evals green both ways.
 - **Verify:** `bash -n scripts/automation/lib/security_scan.sh &&
@@ -1119,6 +1199,32 @@ territory).
 - **Files:** `.github/workflows/evals.yml` (or new `security.yml`), docs.
 - **Rollback:** delete the job.
 
+### SEC-5 · Scan-input hygiene: the gate scans the product diff, never harness bookkeeping
+- **Priority:** P1 · **Effort:** S · **Risk:** LOW · **Status:** DONE
+  *(implemented 2026-07-11 from the tapeology `yahoo_fetch` handoff
+  (`upstream-scanner-recursion-fix.md`): `goal_gate_build_diff_artifacts`
+  (`lib/goal-gates.sh:57`) folded EVERY untracked file into the scanned diff with no
+  path exclusion, so the harness's own `runs/`+`reports/` artifacts — including the
+  scanner's previous `scan-report.md`, which quotes matched tokens — were re-scanned
+  each build: self-referential CRITICAL findings compounding 1 → 3 → … and blocking
+  GOAL_ACHIEVED on a clean product. Fix: `CHAIN_SCAN_BOOKKEEPING_EXCLUDES`
+  (default `runs reports docs/handoffs docs/phases`, knob table in
+  `.claude/model-orchestration.md`) applied as `:(exclude)` pathspec to BOTH the
+  tracked diff and the untracked enumeration; untracked files now diffed by relative
+  path (proper `a/… b/…` headers — the old absolute-path+sed combo mangled them to
+  `bpath`, which also defeated `diff_bound.py`'s excludes); provenance footer on
+  `scan-report.md`; empty/crashed scan-report now reads as WARN, not PASS;
+  `scan_diff.py` self-test fixtures assembled at runtime (keyword+value split) with a
+  self-scan structural guard. Deliberately PATH-based, never value-allowlisting —
+  `case-05-secret-committed` still proves a fake credential in product source stays
+  CRITICAL. Regression: `goal-gates.sh --self-test` cases 11/12 (git-backed:
+  bookkeeping quoting a credential scans CLEAN untracked AND tracked; the same
+  credential in product source stays CRITICAL). Residual accepted blind spot: a secret
+  pasted ONLY into a handoff/report/spec is no longer scanned per-iteration — SEC-1's
+  full-tree pass on GOAL_ACHIEVED is the designated cover; until then that text is
+  agent-generated prose, the same class as the traces that caused the recursion.
+  Anti-pattern #22.)*
+
 ---
 
 ## 12. P1 — Product quality gates (the chain's OUTPUT, not the chain)
@@ -1401,6 +1507,94 @@ but appreciated.
 - **Why staged:** caps appear respected today; this is hygiene, not a win. Best
   absorbed into SAFE-2's session rather than run standalone.
 
+### CAND-SVC-BOOT · start-backend template shadows the project's real start command (staged — do not start)
+- **Proposed:** P1 · Effort S (benchmark-local fix) or M (general boot-path fallback) ·
+  Risk LOW (fixture/runner side) to MED (touching the engine's service boot).
+- **Source:** EVO-3 first real baseline (bench-20260710-2117 @ c48f25047126) — README
+  Known Limitation 1 ("QA expects `CHAIN_START_BACKEND_CMD` or `scripts/start-backend.sh`",
+  `README.md:464`) made concrete. Staged 2026-07-11.
+- **Problem:** the deterministic service-boot lane never consults the project's documented
+  start command. Resolution order today (`goal-iter-lean.sh:333-340`; `qa-phase.sh:73-78`
+  same pattern): `CHAIN_START_BACKEND_CMD` env → else `bash scripts/start-backend.sh` if
+  the file exists → else nothing. The generic framework template
+  (`scripts/start-backend.sh:26-34`: `cd apps/backend` + uvicorn, port 8000+hash-offset at
+  `:12-16`) ships in the subrepo set the benchmark assembly copies wholesale
+  (`run-benchmark.sh:208-222`); the fixture has no `scripts/` dir of its own, so the
+  FastAPI-flavored template lands uncontested and shadows the fixture project-template's
+  documented command (`.venv/bin/python app.py` serving 127.0.0.1:5177 —
+  `benchmarks/fixtures/todo-app/.claude/project-template.md:102-106`). The health probe is
+  blind the same way: default `http://localhost:8000/health` (`goal-iter-lean.sh:342-344`;
+  hash-offset resolved it to :8763 in the run) — the fixture's 5177 appears nowhere.
+- **Evidence:** `benchmarks/results/20260710-224206-c48f25047126.json` — journeys 0/3
+  while the chain built all three to reviewer-PASS / COHERENCE-PASS / 15-of-15-pytest
+  quality; ledger POST assessment under `## POST bench-20260710-2117`
+  (`benchmarks/experiments.md`). Kept scratch: the iter-1 backend service log is the single
+  line `cd: .../scratch/apps/backend: No such file or directory`
+  (`runs/goal-bench-20260710-2117-iter-1/service-logs/qa-backend-8763.log`);
+  `trace/0014-qa.log` shows the QA agent correctly diagnosing the mismatch and attempting
+  to rewrite start-backend.sh itself — blocked by CAND-HEADLESS-PERMS, so the two gaps
+  compound.
+- **Sketch (root-cause hypotheses, not a design):** (a) benchmark-local: the fixture ships
+  its own `scripts/start-backend.sh` (the overlay already lets fixture files win
+  collisions, and maintenance-protocol §3.4 blesses localizing exactly this file
+  per-deployment), and/or `run-benchmark.sh` exports `CHAIN_START_BACKEND_CMD` /
+  `CHAIN_BACKEND_PORT` / `CHAIN_BACKEND_HEALTH_URL` derived from the fixture's template;
+  (b) general (retires Known Limitation 1 for every adopter): a middle resolution tier that
+  reads the project-template's `SERVICE START COMMANDS` section before falling back to the
+  generic script — needs a parse contract + eval fixture (G3) and care around
+  `ensure_services_running` (`lib/common.sh:770`, `_start_service_with_retries` `:582`).
+- **Why staged / verify idea:** engine boot-path changes are MED risk and the human should
+  pick (a), (b), or both (EVO-1 promotion). Verify per §9 "When to benchmark": rerun the
+  benchmark with `--predict 'journeys_passing_after>=3'` — the fix should move journeys
+  0→3 and `benchmark_compare.py` renders the delta against the recorded baseline (exactly
+  the compare the baseline + tool exist for).
+
+### CAND-HEADLESS-PERMS · headless write-permission prompt silently voids QA + retro reports (staged — do not start)
+- **Proposed:** P1 · Effort S (runner-side guard + loud tripwire) · Risk LOW-MED (the
+  trust-flag variant writes user-global `~/.claude.json` — ask-first class).
+- **Source:** same EVO-3 baseline (bench-20260710-2117). Staged 2026-07-11.
+- **Problem:** headless dispatches carry no permission flags beyond the per-agent deny
+  overlay (`--disallowedTools` + budget, `lib/quota-retry.sh:603-643`) — write access
+  relies entirely on the allow list in `.claude/settings.json`. Claude Code honors that
+  list only in a TRUSTED workspace: trust is keyed by absolute path in `~/.claude.json`
+  (`projects[<path>].hasTrustDialogAccepted`), a benchmark scratch is a fresh mktemp path
+  every run — never trusted — and no headless run can answer the trust/permission prompt.
+  NOT a missing-file problem: the scratch carried BOTH `settings.json` and the gitignored
+  `settings.local.json`, byte-identical to the repo's (`run-benchmark.sh:218` `cp -a`
+  copies gitignored files too), and every agent trace opens with "Ignoring 122
+  permissions.allow entries … this workspace has not been trusted".
+- **Evidence:** kept-scratch traces (`runs/goal-session-bench-20260710-2117/trace/` in
+  `~/.cache/chain-bench-tmp/bench-bench-20260710-2117.EMAuTK/scratch`): `0014-qa.log` —
+  trust banner at line 1, tail: "I can't write the QA report due to permission
+  restrictions" — the QA verdict exists ONLY in stdout, no artifact (`reports/qa/` empty);
+  `0028-retro-analyst.log` — ends "am writing the report to the output path now", yet no
+  `reports/goal-session-*-retro.md` exists while the engine-shell-written
+  `state/retro-input.md` does (shell writes unaffected; agent Write blocked).
+  `~/.claude.json`: `hasTrustDialogAccepted` is `false` for the scratch path and `true`
+  for this repo → PRODUCTION headless runs in an already-trusted checkout are NOT
+  affected on this machine; every benchmark scratch is, and so is the first headless run
+  on any never-trusted adopter path. Friction counters were all zero — nothing surfaced
+  the missing evidence; the damage mode is SILENT. Open point for promotion: denials were
+  not uniform — iteration-summarizer/reviewer wrote `reports/` files in the SAME untrusted
+  workspace (trace `0026` wrote two) while both blocked dispatches were light-tier (qa,
+  retro-analyst); pin the mechanism with a controlled probe (stub dispatch in an untrusted
+  scratch, observe which tool calls deny) before designing the fix.
+- **Sketch (root-cause hypotheses, not a design):** (a) runner-side guard — cheapest,
+  no global state: after the first dispatch, grep its trace for the "Ignoring N
+  permissions.allow entries" banner and ABORT the run loudly (a voided run still costs
+  ~$11); (b) runner pre-trusts the scratch path (write
+  `projects[<scratch>].hasTrustDialogAccepted: true` into `~/.claude.json` before launch,
+  remove after) — touches user-global config, needs explicit human sign-off; (c) the
+  tripwire wanted REGARDLESS of (a)/(b): any qa/browser-qa/retro dispatch that returns
+  without its expected report file on disk → LOUD `[missing-evidence]` banner + telemetry
+  event, never a silent `unknown` (the silent-missing-evidence failure mode is the damage
+  here).
+- **Why staged / verify idea:** which layer to fix (runner vs engine vs both) and any
+  `~/.claude.json` write are human decisions (G1/EVO-1). Verify: post-fix benchmark rerun
+  shows the QA report + retro report present in scratch and the trust banner absent from
+  every trace; the tripwire is unit-testable offline with a stub dispatch that writes no
+  report.
+
 ---
 
 ## 17. Absorbed-from-README ledger (traceability)
diff --git a/incredible_auto_dev/docs/model-cutover-playbook.md b/incredible_auto_dev/docs/model-cutover-playbook.md
new file mode 100644
index 0000000..392e31d
--- /dev/null
+++ b/incredible_auto_dev/docs/model-cutover-playbook.md
@@ -0,0 +1,242 @@
+# Model-Cutover Playbook (EVO-4)
+
+This file: `docs/model-cutover-playbook.md` — cross-linked from
+`.claude/letter-to-future-sessions.md` (deployment section) and
+`.claude/maintenance-protocol.md` §6.
+
+The strict ordered checklist for changing which Claude models this framework runs on.
+Written 2026-07-11 for a maintainer session that does NOT have this repo's history in
+its head: every step states its exact commands, the evidence that proves it worked, and
+what failure means. Follow the steps IN ORDER. Do not improvise between them.
+
+Run this from an **interactive session with the user reachable** — three steps below
+are hard user checkpoints and cannot be answered by an unattended run.
+
+---
+
+## When to run this playbook
+
+- Anthropic **ships or retires a model** that any tier in `config/model-tiers.yaml`
+  uses or should use (roadmap EVO-1, source #6).
+- A listed model id **starts erroring** on dispatch — the letter's "The model table
+  rots" tripwire (`.claude/letter-to-future-sessions.md`). That symptom means run this
+  playbook NOW.
+- **Before retiring a tier**, and before ANY edit to `config/model-tiers.yaml` for any
+  reason — that file is ask-the-user-first class (`.claude/maintenance-protocol.md` §1).
+
+## Before you start
+
+Required reading (short): `.claude/maintenance-protocol.md` §3 + §6 ·
+`.claude/model-orchestration.md` §1 (the table you will update) ·
+`docs/improvement-roadmap.md` §3 ground rules G1/G8/G9 and §9 "When to benchmark".
+
+Preconditions: clean `git status`; `./scripts/automation/run-evals.sh` green before you
+change anything; you know the candidate model id(s) exactly (typos here waste a
+checkpoint).
+
+### The three user checkpoints (unmissable)
+
+| Where | What the user must approve | Class |
+|---|---|---|
+| Step 2 | The tier change itself (old id → new id, per tier) | Ask-first (G1; model spend) |
+| Step 6 | Judgment-fixture run — the runner prints its own cost estimate | G9 spend gate |
+| Step 7 | EACH benchmark run — ~$11 and ~1.5h+ wall per run at baseline scale | G9 spend gate (per run) |
+
+Steps 1, 3, 4, 5, 8, 9 spend nothing beyond step 1's preflight cents (still tell the
+user about those — no silent spend, however small).
+
+---
+
+## The checklist
+
+### Step 1 — Preflight every candidate id  *(spend: cents — tell the user anyway)*
+
+```bash
+claude -p --model <candidate-id> 'reply OK'     # once per candidate id
+```
+
+- **Expected evidence:** each call returns a completion (any sane "OK"-ish reply) and
+  exits 0.
+- **Failure means:** the id is wrong or not available to this account. **Abort path:**
+  STOP — never write an unverified id into `config/model-tiers.yaml`. Re-check the id
+  with the user; a deprecation announcement is not evidence an id works here.
+
+### Step 2 — USER CHECKPOINT 1: get approval, then flip `config/model-tiers.yaml`
+
+Present to the user: which tier(s) change, old id → new id, and why (release /
+retirement / cost). Only after an explicit yes:
+
+```bash
+$EDITOR config/model-tiers.yaml     # edit tiers.<tier>.claude — nothing else
+```
+
+- **Expected evidence:** `git diff config/model-tiers.yaml` shows ONLY the intended
+  id line(s).
+- **Rules:** this file is the ONE source of model ids. Never "cut over" by adding a
+  per-agent `model_override` in `agents/*/agent.yaml` — that pin is only for commented
+  temporary exceptions, and the evals fail on uncommented ones. Do not change any
+  agent's `model_tier:` here either — moving an agent BETWEEN tiers is a separate
+  spend-class experiment (see roadmap TOKEN-2), not a cutover.
+- **Note (claude-only deployment):** the `codex:` column can stay untouched unless you
+  are actually maintaining the Codex path (letter: `.codex/` is stale by choice; run
+  `sync-cli-assets.py --cli codex` before any Codex use).
+
+### Step 3 — Resync mirrors + drift check
+
+```bash
+python3 scripts/automation/sync-cli-assets.py --cli claude
+python3 scripts/automation/sync-cli-assets.py --cli claude --check   # exit 0 = in sync
+grep -h "^model:" .claude/agents/*.md | sort | uniq -c               # tier census
+```
+
+- **Expected evidence:** `--check` exits 0; the census shows ONLY the new id(s), with
+  per-tier counts summing to the full agent catalog (no line with an old id remains).
+- **Failure means:** mirrors drifted or the render didn't pick up the yaml. **Abort
+  path:** do not proceed with stale mirrors — that is the §3 resync invariant breaking;
+  re-run the sync and investigate before anything else.
+
+### Step 4 — Update the table in `.claude/model-orchestration.md` (same commit)
+
+Edit §1: the tier→model table rows AND the `claude -p --model …` example line, so the
+doc a dispatcher reads matches the yaml the runtime resolves.
+
+```bash
+grep -n '<old-id>' .claude/model-orchestration.md    # expect: no hits
+grep -rn '<old-id>' config/ agents/ .claude/agents/ scripts/ templates/   # expect: no hits
+```
+
+- **Expected evidence:** both greps come back empty. Historical records (`benchmarks/
+  experiments.md`, `benchmarks/results/*.json`, roadmap archive, the letter's old
+  deployment notes) legitimately keep old ids — they are history; NEVER rewrite them.
+- **Commit boundary (protocol §6):** yaml + regenerated mirrors + this table land in
+  ONE commit — but run step 5 first, then commit.
+
+### Step 5 — Offline evals green, then commit steps 2–4
+
+```bash
+./scripts/automation/run-evals.sh    # expect: "Summary: N pass, 0 fail"
+git add config/model-tiers.yaml .claude/agents/ .claude/model-orchestration.md   # + .codex/ only if you synced codex too
+git commit -m "chore(models): cutover <tier>=<new-id> (tiers + mirrors + orchestration table)"
+```
+
+- **Expected evidence:** 0 fail; one commit containing the yaml, the rendered mirrors,
+  and the orchestration table together.
+- **Failure means:** a fixture caught real drift (often an uncommented `model_override`
+  or a half-rendered mirror). **Abort path:** fix before committing; never commit a red
+  suite (G3).
+
+### Step 6 — USER CHECKPOINT 2 (G9): judgment fixtures (REL-1)
+
+The eval suite checks parsers, not judgment. This step checks that the NEW judge
+models still emit the right verdict classes on the frozen golden cases in
+`tests/judgment/` (goal-evaluator, reviewer, auditor).
+
+```bash
+./scripts/automation/run-judgment-evals.sh          # prints plan + cost estimate, then refuses (exit 2)
+# show the printed estimate to the user; only after an explicit yes:
+./scripts/automation/run-judgment-evals.sh --yes-spend
+# targeted re-run of a single judge/case if needed:
+./scripts/automation/run-judgment-evals.sh --yes-spend --judge reviewer
+```
+
+- **Expected evidence:** the pass/fail table shows every case's verdict class correct
+  (13 cases as of 2026-07: 5 evaluator, 4 reviewer, 4 auditor); exit 0.
+- **Failure means:** the new model regresses on judgment — the single biggest cutover
+  risk (silent judge regression mis-certifies whole sessions). **Abort path:** do NOT
+  proceed to step 7. Either roll back (section below) or the user explicitly accepts
+  the regression in writing. Never edit a fixture or tune a prompt "to make it pass".
+
+### Step 7 — USER CHECKPOINT 3 (G9 per run): benchmark before AND after, then compare
+
+Standing rule: roadmap §9 "When to benchmark". Each run costs real tokens
+(baseline scale: ~$11, ~85 min wall; budget up to hours) and needs its own user
+approval + its own PRE ledger entry — the runner enforces both refusals.
+
+**Before-measurement:** the pre-cutover number can be an EXISTING results JSON whose
+framework state matches pre-cutover main (as of writing:
+`benchmarks/results/20260710-224206-c48f25047126.json`, the recorded baseline). If no
+comparable pre-cutover result exists, run the benchmark ONCE **before** step 2's flip
+— the runner stamps whatever sha the tree is on, and a dirty tree is refused.
+
+```bash
+# after the cutover commit (tree clean), with fresh user approval:
+./scripts/automation/run-benchmark.sh \
+  --hypothesis 'Post-cutover <tier>=<new-id>: journeys and cost hold vs baseline' \
+  --predict 'journeys_passing_after>=<pre-run value>' \
+  --yes-spend
+# <pre-run value> = the "journeys_passing_after" number in the pre JSON's "outcome" block
+# then:
+python3 scripts/automation/lib/benchmark_compare.py \
+  benchmarks/results/<pre>.json benchmarks/results/<post>.json
+git add benchmarks/ && git commit -m "docs(bench): post-cutover benchmark run + ledger"
+```
+
+- **Expected evidence:** runner exits 0 with a results JSON + POST ledger entry;
+  compare prints the delta table with verdict **OK** (exit 0).
+- **Failure means:** compare exit 3 = **REGRESS** (wall or cost +>25%, or
+  journeys-passing dropped) → do NOT proceed with the cutover without an explicit
+  human decision; rollback is the default. Compare exit 4 = **UNKNOWN** (verdict
+  inputs incomparable — the tool never guesses) → treat the same way: no proceed
+  without the user. Whatever completed IS the measurement — a rerun for a prettier
+  number needs fresh approval and a fresh PRE entry (§9).
+
+### Step 8 — First-session watchlist  *(spend: none — observe the next real session)*
+
+On the first real goal session after the cutover, check three things:
+
+```bash
+ls runs/goal-<sid>-iter-*/gate-report.md          # must appear on any GOAL_ACHIEVED
+grep '\[escalation\]' runs/goal-session-<sid>/engine.log   # fix-retries name the NEW strong id
+python3 scripts/automation/lib/analyze_telemetry.py runs/goal-session-<sid>/telemetry.jsonl
+```
+
+- **Expected evidence:** gate-report.md present for any GOAL_ACHIEVED (its absence is
+  the letter's "a gate got disabled" degradation sign, cutover or not); `[escalation]`
+  lines cite the new strong-tier id; the telemetry per-model rows show ONLY new ids,
+  with per-agent wall in the same order as §9's typicals and per-agent cost in the same
+  order as the recorded baseline's `by_agent` numbers (`benchmarks/results/`).
+- **Failure means:** routing didn't actually cut over (check
+  `CHAIN_DISABLE_MODEL_ROUTING` / stale mirrors) or the new model's economics are off →
+  bring the numbers to the user; rollback stays on the table.
+
+### Step 9 — Append a dated note to the letter's deployment section
+
+One dated line in `.claude/letter-to-future-sessions.md` (deployment section): what
+flipped, the commit sha, fixture/benchmark outcome, anything the next session should
+watch. This is the provenance trail the next cutover session will look for first.
+
+---
+
+## Rollback (the mirror of steps 2–6)
+
+Triggers: step 6 fixture failure, step 7 REGRESS/UNKNOWN, step 8 watchlist red — or
+the user says so. Rollback is cheap BECAUSE steps 2–4 landed as one commit.
+
+1. Tell the user you are rolling back and why (it restores the previously-approved
+   state, so no new spend approval is needed for the flip itself).
+2. `git revert <cutover-commit>` — or hand-restore the old ids in
+   `config/model-tiers.yaml` if the revert won't apply cleanly.
+3. Resync + check: `python3 scripts/automation/sync-cli-assets.py --cli claude` then
+   `--cli claude --check` (exit 0); the step-3 census grep must show the OLD ids again.
+4. Confirm `.claude/model-orchestration.md` §1 matches the yaml again (the revert
+   normally covers it — verify with the step-4 greps against the reverted-away id).
+5. `./scripts/automation/run-evals.sh` green.
+6. Re-run the judgment fixtures (G9: estimate + user yes) to prove the restored judges
+   still hit their golden verdicts: `./scripts/automation/run-judgment-evals.sh --yes-spend`.
+7. Append a dated rollback note to the letter's deployment section (what was reverted,
+   why, evidence). Never delete the failed attempt's ledger/results entries —
+   `benchmarks/experiments.md` is append-only history.
+
+---
+
+## Cross-references
+
+- Roadmap §9 "When to benchmark" — the standing benchmark rule this playbook's step 7
+  instantiates (`docs/improvement-roadmap.md`).
+- REL-1 judgment fixtures — cases in `tests/judgment/`, runner
+  `scripts/automation/run-judgment-evals.sh` (its header documents every flag).
+- `.claude/maintenance-protocol.md` §6 — the one-commit rule this playbook expands.
+- `.claude/model-orchestration.md` §1 — the table step 4 updates; its "verify, never
+  trust from memory" preflight is step 1.
+- `.claude/letter-to-future-sessions.md` — "The model table rots" (the tripwire that
+  triggers this playbook) and the deployment section (steps 9 / R7 write there).
diff --git a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
index f4dc8b9..f4123c8 100755
--- a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
+++ b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
@@ -277,9 +277,11 @@ if [[ "${CHAIN_LEAN_PARALLEL_COHERENCE:-true}" == "true" && -n "$ITER_DIR" \
     rm -f "$_COH_RC_FILE"
     # Coherence-scoped bounded diff (judge context trim): the source tree is
     # final once review settles, so build iter-diff.md NOW for the auditor to
-    # read first. The evaluator's own scan/iter-diff artifacts are still built
-    # at their original post-browser-qa point in run-goal.sh (overwriting this
-    # file), so the evaluator's inputs are byte-identical to before.
+    # read first. run-goal.sh rebuilds the scan/iter-diff artifacts at its
+    # original post-browser-qa point (overwriting these files); both builds
+    # exclude harness bookkeeping (CHAIN_SCAN_BOOKKEEPING_EXCLUDES), so the
+    # rebuild converges with this one instead of drifting CLEAN→CRITICAL as
+    # runs/ and reports/ artifacts accumulate mid-iteration.
     if declare -F goal_gate_build_diff_artifacts >/dev/null 2>&1 || source "$SCRIPT_DIR/lib/goal-gates.sh" 2>/dev/null; then
       goal_gate_build_diff_artifacts "$ITER_DIR" "$(cat "$ITER_DIR/snapshot-sha" 2>/dev/null || echo "")" "$REPO_ROOT" 2>/dev/null || true
     fi
diff --git a/incredible_auto_dev/scripts/automation/lib/common.sh b/incredible_auto_dev/scripts/automation/lib/common.sh
index 222a436..305743c 100644
--- a/incredible_auto_dev/scripts/automation/lib/common.sh
+++ b/incredible_auto_dev/scripts/automation/lib/common.sh
@@ -365,8 +365,10 @@ ensure_phase_ports() {
 # (push-per-iter makes runs/** tracked in consumer repos, so telemetry/report
 # churn otherwise lands in every `git diff HEAD` the reviewer runs). These trim
 # reviewer CONTEXT only — the deterministic scan_diff.py secrets/deps scan
-# (lib/goal-gates.sh) always runs on the FULL diff, package.json stays in the
-# main diff, and the hint's second command keeps dependency-file awareness.
+# (lib/goal-gates.sh) runs on the full PRODUCT diff (its own bookkeeping
+# excludes are CHAIN_SCAN_BOOKKEEPING_EXCLUDES in goal-gates.sh — the scanner
+# must never read the harness's own generated output), package.json stays in
+# the main diff, and the hint's second command keeps dependency-file awareness.
 REVIEW_DIFF_EXCLUDE_PATTERNS=(
   '*package-lock.json' '*yarn.lock' '*pnpm-lock.yaml' '*poetry.lock' '*uv.lock' '*Cargo.lock'
   '*.min.js' '*.min.css' '*.map'
diff --git a/incredible_auto_dev/scripts/automation/lib/diff_bound.py b/incredible_auto_dev/scripts/automation/lib/diff_bound.py
index d1fc852..2ceb3eb 100644
--- a/incredible_auto_dev/scripts/automation/lib/diff_bound.py
+++ b/incredible_auto_dev/scripts/automation/lib/diff_bound.py
@@ -6,8 +6,10 @@ megabytes on data-heavy iterations (seed CSVs, lockfiles), degrading exactly
 the judgment the loop depends on. This filter produces `iter-diff.md`: the
 COMPLETE file list is always preserved; excluded/oversized content is
 summarized with an honest header (no silent caps); agents Read the real file
-when detail matters. The secret scanner (scan_diff.py) runs on the FULL diff
-separately — bounding never applies to gate-critical inputs.
+when detail matters. The secret scanner (scan_diff.py) runs separately on the
+same unbounded builder input (the product diff — goal-gates.sh path-excludes
+harness bookkeeping from both) — bounding never applies to gate-critical
+inputs.
 
 CLI:
     git diff <sha> | python3 diff_bound.py [--max-file-lines N] [--max-total-lines N]
diff --git a/incredible_auto_dev/scripts/automation/lib/goal-gates.sh b/incredible_auto_dev/scripts/automation/lib/goal-gates.sh
index d562432..02e0dca 100644
--- a/incredible_auto_dev/scripts/automation/lib/goal-gates.sh
+++ b/incredible_auto_dev/scripts/automation/lib/goal-gates.sh
@@ -26,8 +26,10 @@
 #       the verdict to REGRESSION
 #
 #   goal_gate_build_diff_artifacts   writes iter-diff.md (bounded diff view)
-#       and scan-report.md (secret/dependency/license scan of the FULL diff,
-#       tracked + untracked) for the evaluator to consume. Best-effort.
+#       and scan-report.md (secret/dependency/license scan of the product diff,
+#       tracked + untracked, harness bookkeeping path-excluded via
+#       CHAIN_SCAN_BOOKKEEPING_EXCLUDES) for the evaluator to consume.
+#       Best-effort.
 #
 # Escape hatch: CHAIN_GOAL_GATES=false disables gating (filter echoes the
 # verdict through unchanged). Re-enable it in the same session — a silently
@@ -37,6 +39,15 @@
 
 _GOAL_GATES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
 
+# Harness bookkeeping namespaces NEVER fed to the secret scanner: the gate must
+# scan product changes, not the pipeline's own generated output (scan-report /
+# iter-diff / trace / summaries quote findings → self-referential CRITICAL
+# recursion; see .claude/anti-patterns.md). Same set as CHAIN_STEP_HASH_EXCLUDES
+# (lib/checkpoint.sh). Space-separated, env-overridable; note ':=' re-applies
+# the default when the var is exported EMPTY (a single space means "no
+# exclusions").
+: "${CHAIN_SCAN_BOOKKEEPING_EXCLUDES:=runs reports docs/handoffs docs/phases}"
+
 goal_gates_enabled() {
   [[ "${CHAIN_GOAL_GATES:-true}" == "true" ]]
 }
@@ -47,26 +58,42 @@ goal_gate_build_diff_artifacts() {
   local iter_dir="$1" snapshot_sha="$2" repo_root="$3"
   local full_diff
   full_diff="$(mktemp)" || return 0
+  # One exclusion pathspec for BOTH layers (tracked diff + untracked
+  # enumeration): the scanner must never read the harness's own output.
+  local _ex _uf _count=0
+  local _scan_pathspec=(".")
+  for _ex in $CHAIN_SCAN_BOOKKEEPING_EXCLUDES; do
+    _scan_pathspec+=(":(exclude)$_ex")
+  done
   {
     if [[ -n "$snapshot_sha" ]]; then
-      git -C "$repo_root" diff "$snapshot_sha" 2>/dev/null || true
+      git -C "$repo_root" diff "$snapshot_sha" -- "${_scan_pathspec[@]}" 2>/dev/null || true
     else
-      git -C "$repo_root" diff HEAD~1 2>/dev/null || git -C "$repo_root" diff HEAD 2>/dev/null || true
+      git -C "$repo_root" diff HEAD~1 -- "${_scan_pathspec[@]}" 2>/dev/null || \
+        git -C "$repo_root" diff HEAD -- "${_scan_pathspec[@]}" 2>/dev/null || true
     fi
     # Untracked files are the iteration's new files (work is committed only at
-    # the push step, AFTER evaluation) — the scanner must see them too.
-    local _uf _count=0
+    # the push step, AFTER evaluation) — the scanner must see them too. With
+    # bookkeeping excluded, the cap counts PRODUCT files only (bookkeeping used
+    # to be able to exhaust it and silently hide product files from the scan).
+    # Relative path on purpose: --no-index with an absolute path renders
+    # headers as a/home/... which the old sed mangled to 'bpath' — relative
+    # paths give proper a/... b/... headers for scan_diff/diff_bound to parse.
     while IFS= read -r _uf; do
       [[ -z "$_uf" ]] && continue
       _count=$((_count + 1))
       [[ $_count -gt 200 ]] && break
-      git -C "$repo_root" diff --no-index -- /dev/null "$repo_root/$_uf" 2>/dev/null | \
-        sed "s|$repo_root/||g" || true
-    done < <(git -C "$repo_root" ls-files --others --exclude-standard 2>/dev/null)
+      git -C "$repo_root" diff --no-index -- /dev/null "$_uf" 2>/dev/null || true
+    done < <(git -C "$repo_root" ls-files --others --exclude-standard -- "${_scan_pathspec[@]}" 2>/dev/null)
   } > "$full_diff" 2>/dev/null || true
 
   python3 "$_GOAL_GATES_DIR/scan_diff.py" scan --diff-file "$full_diff" \
     > "$iter_dir/scan-report.md" 2>/dev/null || true
+  # Provenance footer (must never contain a literal result-line marker): which
+  # inputs produced this report, so CLEAN/CRITICAL disagreements are debuggable.
+  printf '\n_Scan scope: changes since %s; %s untracked file(s) scanned (cap 200); bookkeeping excluded: %s_\n' \
+    "${snapshot_sha:-HEAD~1}" "$(( _count > 200 ? 200 : _count ))" "$CHAIN_SCAN_BOOKKEEPING_EXCLUDES" \
+    >> "$iter_dir/scan-report.md" 2>/dev/null || true
   python3 "$_GOAL_GATES_DIR/diff_bound.py" < "$full_diff" \
     > "$iter_dir/iter-diff.md" 2>/dev/null || true
   rm -f "$full_diff" 2>/dev/null || true
@@ -122,7 +149,11 @@ goal_gate_achievement() {
   fi
 
   # 4. Diff scan: no CRITICAL findings (secrets / paid-SaaS deps / etc.).
-  if [[ -f "$iter_dir/scan-report.md" ]]; then
+  #    A report with no result line means the scanner crashed (the build
+  #    redirect fails open to an empty file) — treat it like a missing report,
+  #    never as a pass.
+  if [[ -f "$iter_dir/scan-report.md" ]] \
+     && grep -q '^\*\*Result:\*\*' "$iter_dir/scan-report.md" 2>/dev/null; then
     if grep -q '^\*\*Result:\*\* CRITICAL' "$iter_dir/scan-report.md" 2>/dev/null; then
       lines+=("- FAIL scan: critical findings in $iter_dir/scan-report.md")
       failures=$((failures + 1))
@@ -130,7 +161,7 @@ goal_gate_achievement() {
       lines+=("- PASS scan: no critical findings ($iter_dir/scan-report.md)")
     fi
   else
-    lines+=("- WARN scan: no scan-report.md (diff artifacts were not built)")
+    lines+=("- WARN scan: scan-report.md missing or without a result line (diff artifacts were not built)")
   fi
 
   # 5. No passing→failing regressions vs the pre-iteration snapshot.
@@ -391,6 +422,18 @@ _goal_gates_self_test() {
   v="$(goal_gate_filter_verdict GOAL_ACHIEVED "$d/iter-3" "$EVALF" "$HIST_PASS" "$COH" true "$RES" "$d/session" "$d/goal.md" 2>/dev/null)"
   [[ "$v" == "CONTINUE" ]] && echo "  PASS goal-gates: critical scan finding blocks certification" || { echo "  FAIL goal-gates: scan block (got '$v')"; fails=1; }
 
+  # 9b. Empty scan-report (scanner crash fails open to an empty file) must
+  #     read as the WARN/missing branch, never as a PASS.
+  : > "$d/iter-3/scan-report.md"
+  v="$(goal_gate_filter_verdict GOAL_ACHIEVED "$d/iter-3" "$EVALF" "$HIST_PASS" "$COH" true "$RES" "$d/session" "$d/goal.md" 2>/dev/null)"
+  if [[ "$v" == "GOAL_ACHIEVED" ]] && grep -q -- '- WARN scan:' "$d/iter-3/gate-report.md" \
+     && ! grep -q -- '- PASS scan:' "$d/iter-3/gate-report.md"; then
+    echo "  PASS goal-gates: empty scan-report reads as WARN, not PASS"
+  else
+    echo "  FAIL goal-gates: empty scan-report handling (got '$v')"; fails=1
+  fi
+  printf '# scan\n\n**Result:** CLEAN — nothing.\n' > "$d/iter-3/scan-report.md"
+
   # 10. Goal-edit drift (NEED-9): the note is built by the REAL writer
   #     (hash-journeys) from a stale-hash history. A flagged journey whose
   #     spec_hash was never re-recorded blocks certification; re-recording
@@ -417,6 +460,55 @@ _goal_gates_self_test() {
   v="$(goal_gate_filter_verdict GOAL_ACHIEVED "$d/iter-3" "$EVALF" "$HIST_STALE" "$COH" true "$RES" "$d/session" "$d/goal.md" 2>/dev/null)"
   [[ "$v" == "GOAL_ACHIEVED" ]] && echo "  PASS goal-gates: no drift note → stale hash alone never blocks" || { echo "  FAIL goal-gates: drift absent-note (got '$v')"; fails=1; }
 
+  # 11. build_diff_artifacts scans the PRODUCT diff only (recursion guard):
+  #     bookkeeping quoting a credential — the harness's own prior scan
+  #     output, summaries, handoffs — must not trip the scanner, untracked OR
+  #     tracked, while the same credential in product source must. The output
+  #     iter dir lives OUTSIDE the fixture repo so the just-written report is
+  #     not itself untracked in the scanned tree. Fake key is string-split so
+  #     THIS file never contains a pattern-matching literal (see case 12).
+  CHAIN_SCAN_BOOKKEEPING_EXCLUDES="runs reports docs/handoffs docs/phases"
+  local _fk="AKIA""IOSFODNN7EXAMPLE"
+  local G="$d/case11-repo" ITER11="$d/iter-11" _git11=(git -C "$d/case11-repo" -c user.email=t@t -c user.name=t -c commit.gpgsign=false)
+  mkdir -p "$ITER11"
+  git -c init.defaultBranch=main init -q "$G"
+  "${_git11[@]}" commit -q --allow-empty -m base
+  local SNAP11; SNAP11="$("${_git11[@]}" rev-parse HEAD)"
+  mkdir -p "$G/runs/s1/iter-1" "$G/reports" "$G/docs/handoffs" "$G/apps"
+  printf 'prior finding: aws-access-key %s\n' "$_fk" > "$G/runs/s1/iter-1/scan-report.md"
+  printf 'iteration summary quoting %s\n' "$_fk" > "$G/reports/summary.md"
+  printf 'dev handoff quoting %s\n' "$_fk" > "$G/docs/handoffs/x-dev.md"
+  printf 'def ok():\n    return 1\n' > "$G/apps/app.py"
+  goal_gate_build_diff_artifacts "$ITER11" "$SNAP11" "$G"
+  grep -q '^\*\*Result:\*\* CLEAN' "$ITER11/scan-report.md" \
+    && echo "  PASS goal-gates: untracked bookkeeping quoting a credential scans CLEAN" \
+    || { echo "  FAIL goal-gates: bookkeeping exclusion, untracked ($ITER11/scan-report.md)"; fails=1; }
+  printf 'KEY = "%s"\n' "$_fk" > "$G/apps/config.py"
+  goal_gate_build_diff_artifacts "$ITER11" "$SNAP11" "$G"
+  if grep -q '^\*\*Result:\*\* CRITICAL' "$ITER11/scan-report.md" \
+     && grep -q 'apps/config.py' "$ITER11/scan-report.md"; then
+    echo "  PASS goal-gates: credential in product source still CRITICAL, path cited"
+  else
+    echo "  FAIL goal-gates: product-source detection ($ITER11/scan-report.md)"; fails=1
+  fi
+  rm -f "$G/apps/config.py"
+  "${_git11[@]}" add reports/summary.md
+  "${_git11[@]}" commit -q -m bookkeeping
+  printf 'edited summary still quoting %s\n' "$_fk" > "$G/reports/summary.md"
+  goal_gate_build_diff_artifacts "$ITER11" "$SNAP11" "$G"
+  grep -q '^\*\*Result:\*\* CLEAN' "$ITER11/scan-report.md" \
+    && echo "  PASS goal-gates: tracked bookkeeping edit quoting a credential scans CLEAN" \
+    || { echo "  FAIL goal-gates: bookkeeping exclusion, tracked ($ITER11/scan-report.md)"; fails=1; }
+
+  # 12. Structural guard: this library's own source must never contain a
+  #     secret-shaped literal (exit 3 = critical finding in scan_diff.py).
+  local _rc12=0
+  git diff --no-index -- /dev/null "$_GOAL_GATES_DIR/goal-gates.sh" 2>/dev/null | \
+    python3 "$_GOAL_GATES_DIR/scan_diff.py" scan >/dev/null 2>&1 || _rc12=$?
+  [[ "$_rc12" -ne 3 ]] \
+    && echo "  PASS goal-gates: goal-gates.sh source is free of secret-shaped literals" \
+    || { echo "  FAIL goal-gates: goal-gates.sh contains a scanner-tripping literal"; fails=1; }
+
   unset -f claude_with_quota_retry
   rm -rf "$d"
   if [[ $fails -eq 0 ]]; then echo "goal-gates self-test: OK"; else echo "goal-gates self-test: FAILED"; fi
diff --git a/incredible_auto_dev/scripts/automation/lib/scan_diff.py b/incredible_auto_dev/scripts/automation/lib/scan_diff.py
index 7830ab7..c7d3685 100644
--- a/incredible_auto_dev/scripts/automation/lib/scan_diff.py
+++ b/incredible_auto_dev/scripts/automation/lib/scan_diff.py
@@ -5,8 +5,11 @@ diff (stdlib regex only; no external tools, no model tokens).
 Anti-goal detection used to be 100% the goal-evaluator reading a raw diff —
 silent-failure-prone as models get weaker and diffs get bigger. This scanner
 gives the loop (lib/goal-gates.sh) and the evaluator (iter-N/scan-report.md) a
-mechanical first pass over the FULL diff, including the parts the bounded
-diff view excludes (secrets hide in data/config paths).
+mechanical first pass over the caller-provided diff. goal-gates.sh feeds it
+the product diff (tracked + untracked, harness bookkeeping path-excluded via
+CHAIN_SCAN_BOOKKEEPING_EXCLUDES — the scanner must never read the pipeline's
+own generated reports), including the data/config paths the bounded diff view
+truncates (secrets hide there).
 
 Scans ADDED lines ('+' prefix) only. Severities:
   critical — private keys, cloud/API credentials (always blocking)
@@ -169,8 +172,9 @@ def render_markdown(findings: list[Finding]) -> str:
     for f in findings:
         out.append(f"- **{f.severity.upper()}** `{f.rule}` in `{f.file}`: {f.excerpt}")
     out.append("")
-    out.append("_Generated by lib/scan_diff.py over the FULL iteration diff "
-               "(including paths the bounded view excludes)._")
+    out.append("_Generated by lib/scan_diff.py over the caller-provided diff "
+               "(goal-gates.sh feeds product changes only — harness "
+               "bookkeeping is path-excluded)._")
     return "\n".join(out) + "\n"
 
 
@@ -204,12 +208,21 @@ def _self_test() -> int:
 """
     assert scan(clean_diff) == []
 
-    secret_diff = """diff --git a/config/settings.py b/config/settings.py
-+++ b/config/settings.py
-+AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
-+password = "hunter2hunter2"
-+test_password = "example-not-real"
-"""
+    # Fixture tokens are assembled at runtime — keyword AND value split — so
+    # this file's own diff never contains a line matching its own patterns
+    # (editing the scanner must not trip the scanner; enforced by the
+    # self-scan guard at the end of this test).
+    fake_aws = "AKIA" + "IOSFODNN7EXAMPLE"
+    key_name = "pass" + "word"
+    pw = "hunter2" * 2
+    placeholder_val = "example" + "-not-real"
+    secret_diff = (
+        "diff --git a/config/settings.py b/config/settings.py\n"
+        "+++ b/config/settings.py\n"
+        f'+AWS_KEY = "{fake_aws}"\n'
+        f'+{key_name} = "{pw}"\n'
+        f'+test_{key_name} = "{placeholder_val}"\n'
+    )
     f = scan(secret_diff)
     rules = {x.rule for x in f}
     assert "aws-access-key" in rules
@@ -265,16 +278,32 @@ diff --git a/apps/frontend/package.json b/apps/frontend/package.json
     assert any(x.rule == "license-change" for x in f)
 
     # Removed lines are never findings.
-    removed = """diff --git a/a.py b/a.py
-+++ b/a.py
--password = "hunter2hunter2"
-"""
+    removed = (
+        "diff --git a/a.py b/a.py\n"
+        "+++ b/a.py\n"
+        f'-{key_name} = "{pw}"\n'
+    )
     assert scan(removed) == []
 
     # Markdown render includes the verdict word the evaluator keys on.
     assert "CLEAN" in render_markdown([])
     assert "CRITICAL" in render_markdown([Finding("critical", "x", "f", "e")])
 
+    # Structural guard: this file's own source, scanned as fully-added lines,
+    # must never yield a critical finding — otherwise any edit to the scanner
+    # trips the scanner on its own diff (the failure mode that once fed the
+    # goal-gate recursion). Keep fixture secrets keyword/value-split.
+    with open(__file__, encoding="utf-8") as fh:
+        own_lines = fh.read().splitlines()
+    own_diff = (
+        "diff --git a/scan_diff.py b/scan_diff.py\n"
+        "+++ b/scan_diff.py\n"
+        + "\n".join("+" + line for line in own_lines) + "\n"
+    )
+    own_criticals = [x for x in scan(own_diff) if x.severity == "critical"]
+    assert not own_criticals, \
+        f"scan_diff.py's own source trips its scanner: {own_criticals}"
+
     print("self-test passed")
     return 0
 
diff --git a/incredible_auto_dev/scripts/automation/run-goal.sh b/incredible_auto_dev/scripts/automation/run-goal.sh
index ac8c683..f2ab364 100755
--- a/incredible_auto_dev/scripts/automation/run-goal.sh
+++ b/incredible_auto_dev/scripts/automation/run-goal.sh
@@ -1836,7 +1836,7 @@ Agent instructions: .claude/agents/goal-evaluator.md  <-- read this first
 (CLAUDE.md is already in your system prompt — do not Read it again.)
 
 Iteration artifacts (read what exists):
-  Deterministic diff scan (FULL diff — secrets/deps/license): $ITER_DIR/scan-report.md
+  Deterministic diff scan (product diff; harness bookkeeping excluded — secrets/deps/license): $ITER_DIR/scan-report.md
   Bounded diff view (complete file list; hunks capped, header lists omissions): $ITER_DIR/iter-diff.md
   Dev handoff: docs/handoffs/${ITER_NAME}-dev.md
   Review report: reports/reviews/${ITER_NAME}-review.md
diff --git a/incredible_auto_dev/scripts/automation/run-judgment-evals.sh b/incredible_auto_dev/scripts/automation/run-judgment-evals.sh
index be998af..c1c8bb2 100755
--- a/incredible_auto_dev/scripts/automation/run-judgment-evals.sh
+++ b/incredible_auto_dev/scripts/automation/run-judgment-evals.sh
@@ -253,7 +253,7 @@ Agent instructions: .claude/agents/goal-evaluator.md  <-- read this first
 (CLAUDE.md is already in your system prompt — do not Read it again.)
 
 Iteration artifacts (read what exists):
-  Deterministic diff scan (FULL diff — secrets/deps/license): $ITER_DIR/scan-report.md
+  Deterministic diff scan (product diff; harness bookkeeping excluded — secrets/deps/license): $ITER_DIR/scan-report.md
   Bounded diff view (complete file list; hunks capped, header lists omissions): $ITER_DIR/iter-diff.md
   Dev handoff: docs/handoffs/${ITER_NAME}-dev.md
   Review report: reports/reviews/${ITER_NAME}-review.md
diff --git a/incredible_auto_dev/skills/goal-evaluation-methodology.md b/incredible_auto_dev/skills/goal-evaluation-methodology.md
index 82e1d7d..9ef02da 100644
--- a/incredible_auto_dev/skills/goal-evaluation-methodology.md
+++ b/incredible_auto_dev/skills/goal-evaluation-methodology.md
@@ -8,8 +8,9 @@ your overall impression of the iteration.
 ## A. Evidence walk (do this before forming ANY opinion)
 
 1. **Deterministic reports first.** Read, if present in `runs/goal-session-<sid>/iter-<N>/`:
-   - `scan-report.md` — deterministic secret/dependency/license scan of the FULL iteration
-     diff. Findings here are facts; you do not need to re-derive them.
+   - `scan-report.md` — deterministic secret/dependency/license scan of the product
+     iteration diff (tracked + untracked; harness bookkeeping path-excluded). Findings here
+     are facts; you do not need to re-derive them.
    - `iter-diff.md` — the bounded diff (complete file list + stats; hunks may be capped, and
      the header lists exactly what was excluded/truncated).
    - `journeys-changed.md` — goal-edit drift note, present only when a recorded-passing
diff --git a/incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/runs/goal-session-fixt05/iter-2/scan-report.md b/incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/runs/goal-session-fixt05/iter-2/scan-report.md
index 12812cb..7d51fdd 100644
--- a/incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/runs/goal-session-fixt05/iter-2/scan-report.md
+++ b/incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/tree/runs/goal-session-fixt05/iter-2/scan-report.md
@@ -6,4 +6,4 @@
 - **CRITICAL** `secret-assignment` in `backup.py`: AWS_SECRET_ACCESS_KEY = "w7PlqCd0RXmuKZq1t8vGeYb3s6hJnA2fLcE9xTi"
 - **WARN** `new-dependency` in `requirements.txt`: new dependency: boto3
 
-_Generated by lib/scan_diff.py over the FULL iteration diff (including paths the bounded view excludes)._
+_Generated by lib/scan_diff.py over the caller-provided diff (goal-gates.sh feeds product changes only — harness bookkeeping is path-excluded)._
```
