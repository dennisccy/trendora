# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 4. Shown in full: 4.

```diff
diff --git a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
index 2d37ac45..9ebf99a3 100755
--- a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
+++ b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
@@ -305,6 +305,14 @@ if [[ "$PHASE" =~ ^goal-(.+)-iter-[0-9]+$ ]]; then
   # shellcheck disable=SC2034
   REQUIRED_JOURNEYS="$(replay_lane_spec_journeys 'Required-still-passing' "$SPEC")"
   _bqa_targets="$(replay_lane_spec_journeys 'Target journeys:' "$SPEC")"
+  # iter-25: a declared, non-empty journey bullet that still parses to zero
+  # J-NN tokens must never look like the ordinary "nothing to replay" case —
+  # see replay_lane_warn_if_zero_parse's own doc comment (iter-24 regression).
+  # (The identical 'Target journeys:' re-parse at this file's ~line 400 reuses
+  # $_bqa_targets rather than re-invoking the parser, so it is covered by this
+  # same check — no separate warn call needed there.)
+  replay_lane_warn_if_zero_parse 'Required-still-passing' "$SPEC" "$REQUIRED_JOURNEYS" "browser-qa-phase.sh REQUIRED_JOURNEYS"
+  replay_lane_warn_if_zero_parse 'Target journeys:' "$SPEC" "$_bqa_targets" "browser-qa-phase.sh _bqa_targets"
   # ops-hardening iter-42: mirror into the shared TARGET_JOURNEYS global name goal-iter-lean.sh
   # already uses -- replay_lane_merge_results (lib/replay-lane.sh) reads this ONE name from both
   # callers to thread `--target` into the merger, mirroring REQUIRED_JOURNEYS -> --required exactly.
@@ -397,7 +405,11 @@ bqa_browser_confine
 _bqa_infra_blocked="no"
 _bqa_tok_set=""
 if [[ "$GOAL_REPLAY_ACTIVE" == "yes" ]]; then
-  _bqa_tok_set="$(replay_lane_spec_journeys 'Target journeys:' "$SPEC") ${_llm_regr_set:-}"
+  # iter-25: reuse the identical 'Target journeys:' parse already computed (and
+  # zero-parse-checked) above as $_bqa_targets — GOAL_REPLAY_ACTIVE=="yes" here
+  # only when that assignment already ran, so this is never re-invoking the
+  # parser against a different SPEC state.
+  _bqa_tok_set="$_bqa_targets ${_llm_regr_set:-}"
   _bqa_tok_set="$(echo "$_bqa_tok_set" | tr ' ' '\n' | grep -E '^J-[0-9]+$' | sort -u | tr '\n' ' ' || true)"
   _bqa_tok_set="${_bqa_tok_set% }"
 fi
diff --git a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
index a332b2d3..f0854713 100755
--- a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
+++ b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
@@ -210,12 +210,18 @@ trap 'cleanup_iter_servers; chain_tmp_cleanup' EXIT
 # behavior change); knob=replay forks it right after the developer step.
 
 # Journey sets come from the spec (needed by the fork guard below AND by the
-# resume-skip check and the lanes inside the section). First match wins; the
-# journey-less-line pipefail guard is load-bearing and lives in
+# resume-skip check and the lanes inside the section). The line-selection
+# guarantee (skip label-matching lines with zero J-NN tokens; the
+# journey-less-line pipefail guard) is load-bearing and lives in
 # replay_lane_spec_journeys — see lib/replay-lane.sh (both 20260710/20260712
 # benchmark iter-0s died on exactly that parse before the guard existed).
 TARGET_JOURNEYS="$(replay_lane_spec_journeys 'Target journeys:' "$SPEC")"
 REQUIRED_JOURNEYS="$(replay_lane_spec_journeys 'Required-still-passing' "$SPEC")"
+# iter-25: a declared, non-empty journey bullet that still parses to zero
+# J-NN tokens must never look like the ordinary "nothing to replay" case —
+# see replay_lane_warn_if_zero_parse's own doc comment (iter-24 regression).
+replay_lane_warn_if_zero_parse 'Target journeys:' "$SPEC" "$TARGET_JOURNEYS" "goal-iter-lean.sh TARGET_JOURNEYS"
+replay_lane_warn_if_zero_parse 'Required-still-passing' "$SPEC" "$REQUIRED_JOURNEYS" "goal-iter-lean.sh REQUIRED_JOURNEYS"
 # SPEED-22: only the lean executor has a canary dispatch slot, so only it may
 # arm the mass-false-FAIL breaker inside the shared replay lane (the full
 # pipeline stays byte-identical). Exported so the SPEED-2/3 forks inherit it.
diff --git a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
index 8f4a5388..d59cb281 100644
--- a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
+++ b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
@@ -65,15 +65,69 @@ _replay_lane_log()  { echo "[${REPLAY_LANE_TAG:-replay-lane}] $*"; }
 _replay_lane_warn() { echo "[${REPLAY_LANE_TAG:-replay-lane}] $*" >&2; }
 
 # Journey IDs from a spec line, e.g. `replay_lane_spec_journeys 'Target journeys:' "$SPEC"`
-# → "J-01 J-03 ". First matching line wins. The `|| true` is load-bearing: a
-# journey-less line ("Required-still-passing journeys: none — ...", every
-# iteration-0 baseline spec) makes the inner grep exit 1, and every caller runs
-# under set -e PLUS pipefail (inherited from sourcing lib/telemetry.sh) —
-# without the guard the bare assignment kills the calling script SILENTLY
-# (both 20260710/20260712 benchmark iter-0s died exactly there). Empty is a
-# legitimate parse result; it must never be an exit.
+# → "J-01 J-03 ". Selects the first label-matching line that ACTUALLY CONTAINS
+# one or more J-NN tokens — NOT merely the first label-matching line (iter-24
+# regression: a prose sentence mentioning the label phrase, e.g. "...see
+# Required-still-passing and TESTING REQUIREMENTS below", sat one line before
+# the real "**Required-still-passing journeys:** J-01, J-04, J-10" bullet;
+# `head -1` on the old implementation took the prose line, found zero J-NN
+# tokens in it, and silently returned empty — J-01/J-04/J-10 went unverified
+# for an entire iteration with only a benign "replay: no" logged, no error).
+# Lines with zero J-NN tokens are skipped in favor of the next matching line.
+# Journey-less matches ("Required-still-passing journeys: none — ...", every
+# iteration-0 baseline spec) are a legitimate, common empty result — it must
+# never be an exit. The loop body only ever runs `grep -oE` after a `grep -q`
+# on the SAME line has already proven a match exists, so that extraction can
+# never itself fail; the trailing `return 0` keeps the function's own exit
+# status 0 even when no line qualifies, preserving the old `|| true` guarantee
+# under callers' `set -e` + `pipefail` (inherited from sourcing lib/telemetry.sh
+# — both 20260710/20260712 benchmark iter-0s died when this guarantee was
+# missing).
 replay_lane_spec_journeys() {
-  grep -iE "$1" "$2" 2>/dev/null | head -1 | grep -oE 'J-[0-9]+' | sort -u | tr '\n' ' ' || true
+  local _rl_line
+  while IFS= read -r _rl_line; do
+    if grep -qE 'J-[0-9]+' <<<"$_rl_line"; then
+      grep -oE 'J-[0-9]+' <<<"$_rl_line" | sort -u | tr '\n' ' '
+      return 0
+    fi
+  done < <(grep -iE "$1" "$2" 2>/dev/null)
+  return 0
+}
+
+# replay_lane_bullet_line — the FIRST line that looks like this label's OWN
+# markdown bullet (`- **<label ...>:**...`), as opposed to an incidental prose
+# mention of the label phrase elsewhere in the spec. Used only by the
+# zero-parse warning below; replay_lane_spec_journeys's own line selection
+# above is unchanged (first line containing a J-NN token, per its contract).
+# The `|| true` is load-bearing exactly like replay_lane_spec_journeys's own
+# (see its doc comment): a label with no bullet at all in the spec (this
+# function's own legitimate "nothing to warn about" case) makes grep exit 1,
+# and this is assigned via command substitution at its call site — without the
+# guard, that bare assignment would kill the caller SILENTLY under set -e +
+# pipefail.
+replay_lane_bullet_line() {
+  grep -iE '^[[:space:]]*-[[:space:]]*\*\*[^*]*'"$1" "$2" 2>/dev/null | head -1 || true
+}
+
+# replay_lane_warn_if_zero_parse — call right after replay_lane_spec_journeys
+# with its result, to distinguish a legitimate empty parse (no bullet for this
+# label, or an explicit "none"/"n/a" bullet) from a real defect: a declared,
+# non-empty bullet that still yielded zero J-NN tokens (malformed IDs, or a
+# label whose real bullet the line-selection above still could not find).
+# Emits one WARNING line via _replay_lane_warn — visibly distinct from the
+# ordinary "replay: no" no-work summary a caller may log afterward — and never
+# affects control flow or exit status. $1=label $2=spec $3=parsed result
+# $4=optional context string (which caller/variable, for the log line).
+replay_lane_warn_if_zero_parse() {
+  local _label="$1" _spec="$2" _parsed="$3" _context="${4:-}" _bullet
+  [[ -n "${_parsed// /}" ]] && return 0
+  _bullet="$(replay_lane_bullet_line "$_label" "$_spec")"
+  [[ -z "$_bullet" ]] && return 0
+  if grep -qiE '\*\*[[:space:]]*(none|n/a)\b' <<<"$_bullet"; then
+    return 0
+  fi
+  _replay_lane_warn "WARNING: spec declares a non-empty '$_label' journey bullet but it parsed to ZERO J-NN tokens${_context:+ ($_context)} — line: $_bullet"
+  return 0
 }
 
 # Lane path derivations for iteration/phase name $1 (goal-<sid>-iter-<N>).
diff --git a/incredible_auto_dev/tests/automation/test-replay-lane.sh b/incredible_auto_dev/tests/automation/test-replay-lane.sh
index 762df77c..f9912ca7 100644
--- a/incredible_auto_dev/tests/automation/test-replay-lane.sh
+++ b/incredible_auto_dev/tests/automation/test-replay-lane.sh
@@ -265,6 +265,76 @@ out="$( (set -euo pipefail; source "$LIB"; replay_lane_spec_journeys 'Required-s
 [[ "$rc" -eq 0 && "$out" == *SURVIVED* ]] && assert "spec_journeys: journey-less line survives set -e + pipefail" pass \
   || assert "spec_journeys: journey-less line survives set -e + pipefail (rc=$rc)" fail
 
+# ── 1b. iter-24 regression (TC-4/TC-5): a prose sentence mentioning the label
+#       phrase sits ONE LINE BEFORE the real bullet — reproduces
+#       docs/phases/goal-market-compass-iter-24.md:18-23 verbatim in shape. The
+#       old `head -1`-then-extract implementation took the prose line
+#       unconditionally and found zero J-NN tokens in it, silently returning
+#       empty (TC-4, exercised here via an inline copy of that OLD logic —
+#       documentation of the bug shape, not a live code path). The FIXED
+#       lib function (TC-5) must skip the token-less prose line and source the
+#       real bullet instead. ───────────────────────────────────────────────
+SPEC_ITER24="$SBX/docs/phases/iter24-repro.md"
+cat > "$SPEC_ITER24" <<'EOF'
+- **Target journeys:** none — this iteration is an owner-authorized fix
+  with zero journey-visible product change. Regression coverage substitutes
+  for a target-journey browser-qa pass; see Required-still-passing and TESTING
+  REQUIREMENTS below.
+- **Required-still-passing journeys:** J-01, J-04, J-10 (the entire currently-passing set)
+EOF
+
+# TC-4: pre-fix logic (copied inline — the sourced lib is already fixed; this
+# proves the bug shape the fix addresses, not a live regression surface).
+_pre_fix_spec_journeys() {
+  grep -iE "$1" "$2" 2>/dev/null | head -1 | grep -oE 'J-[0-9]+' | sort -u | tr '\n' ' ' || true
+}
+out="$(_pre_fix_spec_journeys 'Required-still-passing' "$SPEC_ITER24")"
+[[ -z "${out// /}" ]] && assert "spec_journeys (TC-4, pre-fix repro): prose-before-bullet returns EMPTY" pass \
+  || assert "spec_journeys (TC-4, pre-fix repro): prose-before-bullet returns EMPTY (got '<$out>')" fail
+
+# TC-5: the FIXED lib function on the identical fixture must find the real bullet.
+out="$( (set -euo pipefail; source "$LIB"; replay_lane_spec_journeys 'Required-still-passing' "$SPEC_ITER24") )"
+[[ "$out" == "J-01 J-04 J-10 " ]] && assert "spec_journeys (TC-5, fixed): skips token-less prose, sources real bullet" pass \
+  || assert "spec_journeys (TC-5, fixed): skips token-less prose, sources real bullet (got '<$out>')" fail
+
+# ── 1c. TC-6: a declared, non-"none" bullet that parses to ZERO J-NN tokens
+#       (malformed IDs) must emit an explicit WARNING via
+#       replay_lane_warn_if_zero_parse — visibly distinct from the ordinary
+#       "replay: no" no-work summary a caller logs afterward. ──────────────
+SPEC_MALFORMED="$SBX/docs/phases/malformed-repro.md"
+cat > "$SPEC_MALFORMED" <<'EOF'
+- **Required-still-passing journeys:** JX-01, JX-04 (malformed ids, not real J-NN tokens)
+EOF
+out="$( (set -euo pipefail; source "$LIB"; replay_lane_spec_journeys 'Required-still-passing' "$SPEC_MALFORMED") )"
+[[ -z "${out// /}" ]] && assert "spec_journeys: malformed-id bullet still parses to EMPTY (TC-6 precondition)" pass \
+  || assert "spec_journeys: malformed-id bullet still parses to EMPTY (TC-6 precondition) (got '<$out>')" fail
+
+warn_out="$( (set -euo pipefail; source "$LIB"
+  parsed="$(replay_lane_spec_journeys 'Required-still-passing' "$SPEC_MALFORMED")"
+  replay_lane_warn_if_zero_parse 'Required-still-passing' "$SPEC_MALFORMED" "$parsed" "test") 2>&1 )"
+echo "$warn_out" | grep -qi "WARNING" && echo "$warn_out" | grep -q "JX-01" \
+  && assert "warn_if_zero_parse (TC-6): non-empty malformed bullet emits explicit WARNING" pass \
+  || { assert "warn_if_zero_parse (TC-6): non-empty malformed bullet emits explicit WARNING" fail; echo "    got: $warn_out"; }
+
+# ── 1d. The zero-parse warning must NOT false-positive on the two legitimate
+#       empty cases: an explicit "none" bullet, and a label with no bullet at
+#       all in the spec. ────────────────────────────────────────────────────
+warn_out="$( (set -euo pipefail; source "$LIB"
+  parsed="$(replay_lane_spec_journeys 'Target journeys:' "$SPEC_ITER24")"
+  replay_lane_warn_if_zero_parse 'Target journeys:' "$SPEC_ITER24" "$parsed" "test") 2>&1 )"
+[[ -z "$warn_out" ]] && assert "warn_if_zero_parse: explicit 'none' bullet does NOT warn" pass \
+  || { assert "warn_if_zero_parse: explicit 'none' bullet does NOT warn" fail; echo "    got: $warn_out"; }
+
+SPEC_NOBULLET="$SBX/docs/phases/nobullet-repro.md"
+cat > "$SPEC_NOBULLET" <<'EOF'
+- **Required-still-passing journeys:** J-02, J-04
+EOF
+warn_out="$( (set -euo pipefail; source "$LIB"
+  parsed="$(replay_lane_spec_journeys 'Target journeys:' "$SPEC_NOBULLET")"
+  replay_lane_warn_if_zero_parse 'Target journeys:' "$SPEC_NOBULLET" "$parsed" "test") 2>&1 )"
+[[ -z "$warn_out" ]] && assert "warn_if_zero_parse: label absent entirely does NOT warn" pass \
+  || { assert "warn_if_zero_parse: label absent entirely does NOT warn" fail; echo "    got: $warn_out"; }
+
 # ── 2. Lane paths ────────────────────────────────────────────────────────────
 out="$( (
   set -euo pipefail
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-market-compass-index.html     |   11 +-
 reports/perf-budgets.md                            |  132 ++
 .../verify-clone/config.verify.yaml                | 2141 --------------------
 .../goal-session-market-compass/.engine.lock/epoch |    2 +-
 runs/goal-session-market-compass/.engine.lock/pid  |    2 +-
 runs/goal-session-market-compass/engine.pid        |    2 +-
 runs/goal-session-market-compass/session.json      |    6 +-
 .../state/assumptions.md                           |  105 -
 .../state/assumptions.md.archive.md                |  108 +
 runs/goal-session-market-compass/state/lessons.md  |   15 +-
 .../state/lessons.md.archive.md                    |   20 +
 runs/goal-session-market-compass/summary.md        |   55 +-
 runs/goal-session-market-compass/telemetry.jsonl   |   20 +
 runs/goal-session-market-compass/trace/.next-step  |    2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |    2 +
 15 files changed, 335 insertions(+), 2288 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
