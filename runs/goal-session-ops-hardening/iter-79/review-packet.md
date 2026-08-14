# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/docs/goal.md b/docs/goal.md
index 46a5aa35..760ca648 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -558,3 +558,40 @@ original 2026-07-18 measurement, not re-measured this round)
   - **`scripts/start-frontend.sh` joins `HOST_GUARD_MARKER_FILES`** (the iter-33/i owner item): it
     can trigger a multi-worker `next build` from the QA / demo lanes, so it carries a HOST-GUARD
     block like the other launchers.
+- **Owner amendment — completion rule, harness approvals (added 2026-08-13 by the owner, after the
+  iter-78 STALLED halt):** answering the three questions the evaluator escalated in writing across
+  iterations 75-78. **No journey text and no anti-goal text is modified by this amendment** — it
+  changes when the session is allowed to *conclude*, and grants two named permissions.
+  - **The completion rule is settled: all eight Must-have journeys `passing`/`already_passing` on
+    fresh evidence + zero unresolved *critical* anti-goal violations + `coherence.md` not
+    `COHERENCE-FAIL` ⇒ GOAL_ACHIEVED.** Unresolved **minor** ledger entries in
+    `state/journey-history.json` **no longer block** GOAL_ACHIEVED. Grounds: the ledger is a
+    self-audit backlog that this loop grows faster than it closes (138 → 140 → 146 unresolved
+    across three consecutive all-green rounds, iters 76-78, at 3.5-5.6× the wall-clock budget), so
+    reading `.claude/skills/goal-evaluation-methodology.md` §C.3's "no unresolved anti-goal
+    violations" to include minor entries makes termination unreachable by construction. The
+    evaluator applies §C.3 with "unresolved anti-goal violations" scoped to **critical** severity
+    (that skill's own §B already defines critical narrowly: secrets, unapproved paid dependency,
+    license violation, security backdoor, fabricated data presented as real). Minor entries stay
+    recorded, stay counted, and stay in the ledger as the standing backlog — they are reported at
+    close, not gated on. The fail-closed rule is untouched: **when unsure whether a finding is
+    critical, treat it as critical.** REGRESSION on an unresolved critical violation still fires
+    verbatim.
+  - **`scripts/automation/lib/closure_gate.py` may be edited (APPROVED):** its placeholder scan
+    must not fire on `TODO`/`TBD` appearing inside a **quoted span** — fenced code, inline code, or
+    double quotes (an artifact faithfully *quoting* a tool's own message is evidence, not an
+    unfinished placeholder; the iter-78 instance quoted with double quotes, not backticks —
+    single quotes are excluded so apostrophes cannot swallow prose), and its
+    backend-only claim guard must not fire on a *negated* mention ("no remaining backend-only
+    gap", "no longer backend-only"). Both false positives blocked closure on complete artifacts in
+    iterations 77 and 78. The guards themselves stay — only these two false-positive classes are
+    excluded.
+  - **`scripts/automation/browser-qa-phase.sh` may be edited (APPROVED):** `TARGET_JOURNEYS` must
+    be assigned **before** `replay_lane_partition_and_verify` is called, not after. Assigning it
+    afterwards made iteration 60's target-journey replay routing dead on the full-pipeline path
+    (live only on the lean path), which is why target journeys went unreplayed for several rounds.
+  - **`CHAIN_EVIDENCE_MICRO_PATH=false` for the remainder of this session (owner directive).** With
+    every target journey already `passing`, the SPEED-9 evidence backstop
+    (`run-goal.sh:2513-2537`) demoted every lean spec to `evidence` and skipped the developer
+    entirely — that is how iterations 75 and 76 produced empty diffs against non-empty specs. The
+    backstop stays in the code; it is disabled for this session by environment.
diff --git a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
index 518f0553..aa56b426 100755
--- a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
+++ b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
@@ -269,6 +269,18 @@ if [[ "$PHASE" =~ ^goal-(.+)-iter-[0-9]+$ ]]; then
   replay_lane_paths "$PHASE"
   # shellcheck disable=SC2034
   REQUIRED_JOURNEYS="$(replay_lane_spec_journeys 'Required-still-passing' "$SPEC")"
+  _bqa_targets="$(replay_lane_spec_journeys 'Target journeys:' "$SPEC")"
+  # ops-hardening iter-42: mirror into the shared TARGET_JOURNEYS global name goal-iter-lean.sh
+  # already uses -- replay_lane_merge_results (lib/replay-lane.sh) reads this ONE name from both
+  # callers to thread `--target` into the merger, mirroring REQUIRED_JOURNEYS -> --required exactly.
+  #
+  # ops-hardening iter-79 (owner-approved 2026-08-13): this assignment MUST stay ABOVE
+  # replay_lane_partition_and_verify. It used to sit below, so the partitioner read an EMPTY
+  # TARGET_JOURNEYS and iter-60's target-journey replay routing was dead on this full-pipeline
+  # path (it worked only on the lean path, which sets the name first) -- target journeys went
+  # unreplayed for several rounds.
+  # shellcheck disable=SC2034
+  TARGET_JOURNEYS="$_bqa_targets"
   replay_lane_partition_and_verify "$PHASE"
   if [[ "$_use_replay" == "yes" ]]; then
     _llm_out="$LLM_RESULTS"
@@ -278,12 +290,6 @@ if [[ "$PHASE" =~ ^goal-(.+)-iter-[0-9]+$ ]]; then
   # replay_lane_llm_regression_set narrows itself when it is non-empty, and
   # the post-merge writer below appends the DEFERRED-BUDGET rows. Targets are
   # excluded from deferral — they are dispatched regardless.
-  _bqa_targets="$(replay_lane_spec_journeys 'Target journeys:' "$SPEC")"
-  # ops-hardening iter-42: mirror into the shared TARGET_JOURNEYS global name goal-iter-lean.sh
-  # already uses -- replay_lane_merge_results (lib/replay-lane.sh) reads this ONE name from both
-  # callers to thread `--target` into the merger, mirroring REQUIRED_JOURNEYS -> --required exactly.
-  # shellcheck disable=SC2034
-  TARGET_JOURNEYS="$_bqa_targets"
   REPLAY_DEFERRED_BUDGET="$(replay_lane_deferred_budget_set "$_bqa_targets")"
   if [[ -n "${REPLAY_DEFERRED_BUDGET// /}" ]]; then
     echo "[browser-qa] iter-budget trim (rung 2): deferring no-golden regression journey(s) this iteration: ${REPLAY_DEFERRED_BUDGET% }— targets + replay-FAIL re-confirms are never deferred."
diff --git a/incredible_auto_dev/scripts/automation/lib/closure_gate.py b/incredible_auto_dev/scripts/automation/lib/closure_gate.py
index 3d3c0711..c8983f14 100644
--- a/incredible_auto_dev/scripts/automation/lib/closure_gate.py
+++ b/incredible_auto_dev/scripts/automation/lib/closure_gate.py
@@ -66,6 +66,18 @@ _PLACEHOLDER_RE = re.compile(
     r"\bTODO\b|\bTBD\b|<fill|\bFILL IN\b|\blorem\b|\bxxx+\b", re.IGNORECASE
 )
 
+# Code spans are quoted evidence, not authored prose — a marker inside one is
+# something a tool said, not a placeholder the author left behind (owner
+# amendment 2026-08-13; ops-hardening iter-78 blocked closure on an artifact
+# faithfully quoting Chrome MCP's own "TODO: Console logging not yet
+# implemented" message).
+_INLINE_CODE_RE = re.compile(r"`[^`]*`")
+_CODE_FENCE_RE = re.compile(r"^\s*(?:```|~~~)")
+# Straight and curly double quotes, bounded to one line so an unbalanced quote
+# cannot blank out the rest of the document. Single quotes are deliberately NOT
+# included — apostrophes ("don't") would swallow arbitrary prose.
+_QUOTED_SPAN_RE = re.compile(r"\"[^\"\n]{0,300}\"|“[^”\n]{0,300}”")
+
 # N/A-stub / backend-only claim markers — the same set check_backend_only_claim
 # greps (lib/common.sh) so both layers agree on what a backend-only claim is.
 _BACKEND_CLAIM_RE = re.compile(
@@ -178,16 +190,48 @@ def skip_reason(results_text: str) -> str | None:
 
 
 def placeholder_hits(text: str) -> list[str]:
-    """Placeholder markers on non-comment lines, as 'marker (line N)' strings."""
+    """Placeholder markers on non-comment lines, as 'marker (line N)' strings.
+
+    Markers inside a quoted span — fenced code, inline code, or double quotes —
+    are skipped: quoting a tool's own output is evidence, not an unfinished
+    placeholder. Bare markers in prose still block, which is what the guard
+    exists for.
+    """
     hits: list[str] = []
+    in_fence = False
     for i, line in enumerate(text.splitlines(), 1):
-        if line.strip().startswith("<!--"):
+        if _CODE_FENCE_RE.match(line):
+            in_fence = not in_fence
+            continue
+        if in_fence or line.strip().startswith("<!--"):
             continue
-        for m in _PLACEHOLDER_RE.finditer(line):
+        # Blank out quoted spans, preserving offsets. Code first, so a quote
+        # character inside a code span cannot open a stray quoted span.
+        scanned = _INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)
+        scanned = _QUOTED_SPAN_RE.sub(lambda m: " " * len(m.group(0)), scanned)
+        for m in _PLACEHOLDER_RE.finditer(scanned):
             hits.append(f"{m.group(0)} (line {i})")
     return hits
 
 
+# A negated mention is the opposite of a claim: "no remaining backend-only gap"
+# and "no longer backend-only" both assert the gap is CLOSED. Clause-bounded so
+# "…no new pages; it is backend-only" still reads as a genuine claim.
+_BACKEND_CLAIM_NEGATOR_RE = re.compile(
+    r"\b(?:no|not|never|non|zero)\b[^.;]{0,32}$", re.IGNORECASE
+)
+
+
+def has_backend_only_claim(text: str) -> bool:
+    """True when the text actually claims backend-only, ignoring negated mentions."""
+    for m in _BACKEND_CLAIM_RE.finditer(text):
+        prefix = text[: m.start()].rsplit("\n", 1)[-1]
+        if _BACKEND_CLAIM_NEGATOR_RE.search(prefix):
+            continue
+        return True
+    return False
+
+
 def frontend_files_changed(repo_root: Path, phase: str) -> bool:
     """Port of detect_frontend_changes: status.json changed_files first,
     git diff fallback. Errors conservatively mean 'no frontend change'."""
@@ -460,7 +504,7 @@ def _crossref_frontend(
     # Backend-only claim guard (port of check_backend_only_claim, blocking here
     # because Frontend Present: yes — body.md Step 4).
     uvc = texts.get("user-visible-changes")
-    if uvc is not None and _BACKEND_CLAIM_RE.search(uvc):
+    if uvc is not None and has_backend_only_claim(uvc):
         if frontend_files_changed(repo_root, phase):
             r.blocking.append((
                 "user-visible-changes claims no visible changes but frontend "
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-ops-hardening-index.html      |    4 +-
 reports/goal-session-ops-hardening-retro.md        |   69 +-
 ...e-goal-ops-hardening-iter-78-closure-verdict.md |    7 +-
 runs/goal-session-ops-hardening/.engine.lock/epoch |    2 +-
 runs/goal-session-ops-hardening/.engine.lock/pid   |    2 +-
 runs/goal-session-ops-hardening/engine.pid         |    2 +-
 runs/goal-session-ops-hardening/session.json       |   10 +-
 .../state/assumptions.md                           | 1402 +-------------------
 .../state/assumptions.md.archive.md                | 1371 +++++++++++++++++++
 runs/goal-session-ops-hardening/state/lessons.md   |  426 +-----
 .../state/lessons.md.archive.md                    |  512 +++++++
 .../state/retro-input.md                           |  818 +++++++++++-
 runs/goal-session-ops-hardening/summary.md         |  963 +++++++++++++-
 runs/goal-session-ops-hardening/telemetry.jsonl    |   22 +
 runs/goal-session-ops-hardening/trace/.next-step   |    2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |    3 +
 16 files changed, 3716 insertions(+), 1899 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
