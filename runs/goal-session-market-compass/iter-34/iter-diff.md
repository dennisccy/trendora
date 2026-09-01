# Iteration diff (bounded)

Files changed: 1. Shown in full: 0.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` (17 lines not shown)

```diff
diff --git a/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py b/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
index c489d598..14c53619 100644
--- a/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
+++ b/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
@@ -46,6 +46,30 @@ _VERDICT_RE = re.compile(r"\*\*Browser QA Verdict:\*\*\s*[*_`~\s]*([A-Z_]+)")
 # file-level-verdict path and risking a laundered PASS over a real headline FAIL.
 _ROW_RE = re.compile(r"^\|\s*((?:UT|TC)-[^|]+?)\s*\|(.*)\|\s*$")
 
+# market-compass iter-34 (goal-mode harness fix, TC-7/TC-8): a journey's `docs/goal.md`
+# Acceptance block naming the LITERAL marker `**Walkthrough:** waived` has no UI check to
+# fail closed on -- forcing BLOCKED merely because it has no browser row (or only a SKIP
+# row) mistakes "nothing to check" for "not verified". `_JOURNEY_BLOCK_RE` slices goal.md
+# into one span per top-level journey (`- **J-NN ...` through the next such header, the
+# next markdown heading, or EOF) so the waived set is read from the goal text itself, never
+# guessed from a journey-ID pattern -- see `parse_waived_journeys_from_text`.
+_JOURNEY_BLOCK_RE = re.compile(r"^-\s+\*\*(J-\d+)\b.*?(?=^-\s+\*\*J-\d+\b|^#|\Z)", re.MULTILINE | re.DOTALL)
+_WALKTHROUGH_WAIVED_MARKER = "**Walkthrough:** waived"
+
+# market-compass iter-34 AUDIT fix (finding B1) — see `_has_cited_evidence`. Words that mean
+# "nothing was recorded here"; matched against the evidence cell's HEAD (not the whole cell), so
+# `none (long explanation ...)` is recognised as the placeholder it is.
+_PLACEHOLDER_EVIDENCE = (
+    "", "none", "n/a", "na", "-", "--", "—", "tbd", "todo", "pending",
+    "not applicable", "no evidence", "n/a.", "not captured",
+)
+# An artifact-shaped reference: a `dir/file` path, or a bare filename with a known evidence
+# extension. Deliberately narrow — prose alone must not read as a citation.
+_CITATION_SHAPE_RE = re.compile(
+    r"[\w.\-]+/[\w./#\-]+|[\w.\-]+\.(?:md|csv|png|jpg|jsonl?|txt|log|html?)\b",
+    re.IGNORECASE,
+)
+
 
 def _norm_verdict_cell(c: str) -> str:
     """Strip markdown emphasis/backticks so `**FAIL**`, `_PASS_`, `` `SKIP` ``
@@ -55,6 +79,61 @@ def _norm_verdict_cell(c: str) -> str:
 _C_NAME, _C_ACTUAL, _C_EVIDENCE = 0, 4, 6
 
 
+def parse_waived_journeys_from_text(goal_text: str) -> "set[str]":
+    """Bare journey IDs (`{'J-09', ...}`) whose `docs/goal.md` block carries the literal
+    marker `**Walkthrough:** waived` -- the ONLY signal this module trusts (never a
+    journey-ID pattern or a hardcoded list), so the exemption below is provably tied to
+    goal.md's own text and cannot silently widen to an unmarked journey."""
+    waived: "set[str]" = set()
+    for m in _JOURNEY_BLOCK_RE.finditer(goal_text):
+        if _WALKTHROUGH_WAIVED_MARKER in m.group(0):
+            waived.add(m.group(1))
+    return waived
+
+
+def _default_waived_journeys() -> "set[str]":
+    """Best-effort `parse_waived_journeys_from_text` over the repo's own `docs/goal.md`,
+    resolved relative to this file (`lib/ -> automation/ -> scripts/ -> incredible_auto_dev/
+    -> repo root`) so every existing caller (replay-lane.sh's unchanged CLI invocation
+    included) picks up the exemption with zero new wiring. Fails SAFE: a missing/unreadable
+    goal.md yields an empty set, i.e. byte-identical to pre-iter-34 behavior -- this can only
+    ever REMOVE a spurious BLOCKED, never introduce a new one (see `merge`'s docstring)."""
+    try:
+        repo_root = Path(__file__).resolve().parents[4]
+        text = (repo_root / "docs" / "goal.md").read_text(encoding="utf-8")
+    except (OSError, IndexError):
+        return set()
+    return parse_waived_journeys_from_text(text)
+
+
+def _has_cited_evidence(row: dict) -> bool:
+    """True if `row`'s Evidence cell names something concrete. The walkthrough-waived exemption
+    below requires this: a SKIP row for a UI-less journey must still point at SOMETHING (an
+    addendum anchor, a CSV/PNG path, a report file) to count as "verified through cited non-UI
+    evidence" rather than "not executed" -- an empty/placeholder Evidence cell still blocks
+    exactly as before.
+
+    market-compass iter-34 AUDIT fix (finding B1): the original form compared the WHOLE stripped
+    cell against the placeholder tuple, so a placeholder with any prose after it slipped through.
+    That is not hypothetical -- this very iteration's browser-qa lane wrote the cell
+    `none (evidence-based journey -- no UI acceptance state to screenshot, per this journey's own
+    docs/goal.md "Walkthrough: waived" marker ...)`, which cites nothing yet passed the old check
+    (and would even satisfy a naive "contains a path" test, via the incidental `docs/goal.md`
+    mention). Two conjuncts now, both of which that cell fails:
+      1. the cell's HEAD (text before the first `(`/`[`/`;`/`,`) must not be a placeholder word, and
+      2. the cell must contain at least one artifact-shaped reference (a `dir/file` path or a
+         known evidence file extension).
+    Both are fail-CLOSED: an evidence cell that cannot be recognised as a citation keeps the
+    journey blocking, which is the safe direction for a verification exemption."""
+    c = _cell(row, _C_EVIDENCE).strip().strip("`").strip()
+    if not c:
+        return False
+    head = re.split(r"[(\[;,]", c, maxsplit=1)[0].strip().strip("`").strip().rstrip(".").lower()
+    if head in _PLACEHOLDER_EVIDENCE:
+        return False
+    return bool(_CITATION_SHAPE_RE.search(c))
+
+
 def _today() -> str:
     return datetime.date.today().isoformat()
 
@@ -173,7 +252,11 @@ def missing_required_journeys(rows: "list[dict]", required_journeys: "list[str]
     return missing
 
 
-def skipped_required_journeys(rows: "list[dict]", required_journeys: "list[str] | None") -> "list[str]":
+def skipped_required_journeys(
+    rows: "list[dict]",
+    required_journeys: "list[str] | None",
+    waived: "set[str] | None" = None,
+) -> "list[str]":
     """Which of `required_journeys` have a row whose ONLY recorded outcome is `SKIP` — the journey
     was named, a row exists, and it says "not executed." The companion to
     `missing_required_journeys` above: iter-40's actual artifact
@@ -185,15 +268,25 @@ def skipped_required_journeys(rows: "list[dict]", required_journeys: "list[str]
     requires ("fresh, NON-`SKIP` mechanical verification"). Only a literal `SKIP` counts: a
     `DEFERRED-BUDGET` row (SPEED-15 rung 2, an explicit "keeps prior status" record) parses to an
     empty verdict and is deliberately NOT treated as a skip here — `goal_gate.py`'s
-    `_DEFERRED_CELL_RE` already blocks achievement on those."""
+    `_DEFERRED_CELL_RE` already blocks achievement on those.
+
+    market-compass iter-34: a journey in `waived` (its `docs/goal.md` Acceptance carries the
+    literal `**Walkthrough:** waived` marker — see `parse_waived_journeys_from_text`) whose SKIP
+    row ALSO carries cited evidence (`_has_cited_evidence`) is not counted here — it was verified
+    through the cited non-UI evidence instead of a browser walkthrough. A waived journey whose
+    SKIP row has no real citation (an empty/placeholder Evidence cell) still counts as skipped —
+    the exemption is evidence-gated, never a blanket pass for the marker alone."""
     if not required_journeys:
         return []
+    waived = waived or set()
     by_id = {r["test_id"]: r for r in rows}
     skipped = []
     for jid in required_journeys:
         tid = jid if jid.startswith("UT-") else f"UT-{jid}"
         row = by_id.get(tid)
         if row is not None and row["verdict"] == "SKIP":
+            if jid in waived and _has_cited_evidence(row):
+                continue
             skipped.append(jid)
     return skipped
 
@@ -220,19 +313,27 @@ def missing_target_journeys(rows: "list[dict]", target_journeys: "list[str] | No
     return missing
 
 
-def skipped_target_journeys(rows: "list[dict]", target_journeys: "list[str] | None") -> "list[str]":
+def skipped_target_journeys(
+    rows: "list[dict]",
+    target_journeys: "list[str] | None",
+    waived: "set[str] | None" = None,
+) -> "list[str]":
     """Which of `target_journeys` have a row whose ONLY recorded outcome is `SKIP` — the sibling of
     `skipped_required_journeys` above, for `Target journeys:` (see `missing_target_journeys`'s
     docstring for the full rationale). Only a literal `SKIP` counts (not `DEFERRED-BUDGET`), matching
-    `skipped_required_journeys`'s own contract exactly."""
+    `skipped_required_journeys`'s own contract exactly, INCLUDING the market-compass iter-34
+    walkthrough-waived-plus-cited-evidence exemption (see that function's docstring)."""
     if not target_journeys:
         return []
+    waived = waived or set()
     by_id = {r["test_id"]: r for r in rows}
     skipped = []
     for jid in target_journeys:
         tid = jid if jid.startswith("UT-") else f"UT-{jid}"
         row = by_id.get(tid)
         if row is not None and row["verdict"] == "SKIP":
+            if jid in waived and _has_cited_evidence(row):
+                continue
             skipped.append(jid)
     return skipped
 
@@ -241,6 +342,7 @@ def merge(
     texts: "list[str]",
     required_journeys: "list[str] | None" = None,
     target_journeys: "list[str] | None" = None,
+    waived_journeys: "set[str] | None" = None,
 ) -> str:
     """Merge in order; later inputs win per Test ID. Returns the merged markdown
     with a single authoritative headline verdict and detail rebuilt from the
@@ -274,7 +376,18 @@ def merge(
     (the binding iter-41 lesson: "promoting a journey to an iteration's target silently REMOVES its
     verification"). Same additive semantics as `required_journeys`: a missing/all-SKIP target
     journey forces `BLOCKED` on top of (never replacing) the required-journey guard, and a headline
-    already FAIL/BLOCKED is left alone."""
+    already FAIL/BLOCKED is left alone.
+
+    `waived_journeys` (market-compass iter-34 — goal-mode harness fix, TC-7/TC-8): bare IDs whose
+    `docs/goal.md` Acceptance carries the literal `**Walkthrough:** waived` marker (read by
+    `main()` via `_default_waived_journeys`/`parse_waived_journeys_from_text` — never a
+    journey-ID pattern). Threaded into `skipped_required_journeys`/`skipped_target_journeys`
+    ONLY: a waived journey's SKIP row that also carries cited evidence
+    (`_has_cited_evidence`) is treated as verified through that evidence instead of "not
+    executed" and does not force BLOCKED; a waived journey that is MISSING entirely, or whose
+    SKIP row has no real citation, still forces BLOCKED exactly as before — the exemption can
+    only ever REMOVE a spurious BLOCKED for a marked, evidenced journey, never widen past that
+    (TC-8b: an unmarked journey's missing/SKIP-only row is unaffected)."""
     by_id: "dict[str, dict]" = {}
     order: "list[str]" = []
     file_verdicts: "list[str]" = []
@@ -287,10 +400,11 @@ def merge(
             by_id[tid] = row  # later wins
     rows = [by_id[t] for t in order]
     overall = compute_overall(rows, file_verdicts)
+    waived_journeys = waived_journeys or set()
     missing_required = missing_required_journeys(rows, required_journeys)
-    skipped_required = skipped_required_journeys(rows, required_journeys)
+    skipped_required = skipped_required_journeys(rows, required_journeys, waived_journeys)
     missing_target = missing_target_journeys(rows, target_journeys)
-    skipped_target = skipped_target_journeys(rows, target_journeys)
+    skipped_target = skipped_target_journeys(rows, target_journeys, waived_journeys)
     if (missing_required or skipped_required or missing_target or skipped_target) and overall in ("PASS", "SKIPPED"):
         overall = "BLOCKED"
     n_pass = sum(1 for r in rows if r["verdict"] == "PASS")
@@ -479,8 +593,13 @@ def main(argv: "list[str]") -> int:
     # ops-hardening iter-42: a sibling `--target J-05,J-07,...` flag, same parsing shape, for the
     # iteration spec's `Target journeys:` line (see `merge`'s docstring). Absent => no change in
     # behavior, same as `--required`.
+    # market-compass iter-34: an optional `--waived J-09,...` override for tests/manual runs; when
+    # ABSENT (every existing caller, replay-lane.sh included — zero new bash wiring needed) the
+    # waived set is read automatically from the repo's own docs/goal.md
+    # (`_default_waived_journeys`), so the exemption applies with no CLI change required anywhere.
     required: list[str] = []
     target: list[str] = []
+    waived_arg: "list[str] | None" = None
     rest: list[str] = []
     i = 0
     while i < len(argv):
@@ -501,15 +620,24 @@ def main(argv: "list[str]") -> int:
             target = [j for j in a.split("=", 1)[1].replace(",", " ").split() if j]
             i += 1
             continue
+        if a == "--waived" and i + 1 < len(argv):
+            waived_arg = [j for j in argv[i + 1].replace(",", " ").split() if j]
+            i += 2
+            continue
+        if a.startswith("--waived="):
+            waived_arg = [j for j in a.split("=", 1)[1].replace(",", " ").split() if j]
+            i += 1
+            continue
         rest.append(a)
         i += 1
     argv = rest
     if len(argv) < 2:
         sys.stderr.write(
             "usage: merge_ui_test_results.py [--required J-01,J-03,...] [--target J-05,J-07,...] "
-            "<out.md> <in1.md> [<in2.md> ...]\n"
+            "[--waived J-09,...] <out.md> <in1.md> [<in2.md> ...]\n"
         )
         return 2
+    waived = set(waived_arg) if waived_arg is not None else _default_waived_journeys()
     out_path = Path(argv[0])
     texts: list[str] = []
     for p in argv[1:]:
@@ -520,7 +648,10 @@ def main(argv: "list[str]") -> int:
         sys.stderr.write("[merge_ui_test_results] no readable input files\n")
         return 2
     out_path.parent.mkdir(parents=True, exist_ok=True)
-    out_path.write_text(merge(texts, required_journeys=required, target_journeys=target), encoding="utf-8")
+    out_path.write_text(
+        merge(texts, required_journeys=required, target_journeys=target, waived_journeys=waived),
+        encoding="utf-8",
+    )
     print(f"[merge_ui_test_results] merged {len(texts)} file(s) → {out_path}")
     return 0
 
@@ -930,6 +1061,138 @@ def _self_test() -> int:
             assert file_top_verdict(merged2) == "BLOCKED", file_top_verdict(merged2)
             assert "## Missing Target Journeys" in merged2 and "## Missing Required Journeys" not in merged2
 
+    # ==============================================================================================
+    # market-compass iter-34 (goal-mode harness fix, TC-7/TC-8) — a target/required journey whose
+    # docs/goal.md Acceptance carries the literal `**Walkthrough:** waived` marker can be recorded
+    # verified through a cited non-UI evidence row instead of being forced to BLOCKED for having no
+    # browser row / only a SKIP row — STRICTLY scoped to journeys named in `waived_journeys`, and
+    # ONLY when the row actually cites something (not a bare "none"/empty Evidence cell).
+    # ==============================================================================================
+    def t_parse_waived_journeys_from_text():
+        goal_text = (
+            "## Must-have user journeys\n"
+            "- **J-01: Ordinary UI journey**\n"
+            "  - Acceptance:\n"
+            "    - **Walkthrough:** demo required.\n"
+            "- **J-09: Backend-only journey (owner, 2026-08-20)**\n"
+            "  - Acceptance:\n"
+            "    - **Walkthrough:** waived — deliberately backend-only.\n"
+            "- **J-10: Another marked journey**\n"
+            "  - Acceptance:\n"
+            "    - **Walkthrough:** waived — raw-layer repair.\n"
+            "## Anti-goals\n"
+            "- **AG-1:** unrelated section, must not be scanned as a journey.\n"
+        )
+        waived = parse_waived_journeys_from_text(goal_text)
+        assert waived == {"J-09", "J-10"}, waived
+
+    def t_has_cited_evidence():
+        cited = {"cells": ["", "", "", "", "", "", "reports/perf-budgets.md#addendum-45"]}
+        none_cell = {"cells": ["", "", "", "", "", "", "none"]}
+        empty_cell = {"cells": ["", "", "", "", "", "", ""]}
+        short_cells = {"cells": ["a"]}
+        assert _has_cited_evidence(cited) is True
+        assert _has_cited_evidence(none_cell) is False
+        assert _has_cited_evidence(empty_cell) is False
+        assert _has_cited_evidence(short_cells) is False
+
+    def t_waived_target_with_cited_evidence_is_non_blocked():
+        # TC-8a: a synthetic walkthrough-waived TARGET journey with a cited-evidence SKIP row must
+        # merge to a non-BLOCKED headline — the row exists, it was never a UI check to fail, and it
+        # names real evidence instead of "none".
+        waived_row = (
+            "**Browser QA Verdict:** SKIPPED\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-09 | Backend fits the host | smoke | P1 | N/A — waived | verified via "
+            "Addendum 45 | SKIP | reports/perf-budgets.md#addendum-45 |\n")
+        md = merge([waived_row], target_journeys=["J-09"], waived_journeys={"J-09"})
+        assert file_top_verdict(md) != "BLOCKED", file_top_verdict(md)
+        assert "## Missing Target Journeys" not in md
+        assert verdict_for(md, "UT-J-09") == "SKIP", verdict_for(md, "UT-J-09")
+
+    def t_waived_journey_without_evidence_still_blocks():
+        # A waived journey's SKIP row with NO real citation (Evidence == "none") is NOT exempted —
+        # the marker alone is never enough; a real citation is required.
+        no_evidence_row = (
+            "**Browser QA Verdict:** SKIPPED\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-09 | Backend fits the host | smoke | P1 | N/A — waived | no UI to check | "
+            "SKIP | none |\n")
+        md = merge([no_evidence_row], target_journeys=["J-09"], waived_journeys={"J-09"})
+        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
+        assert "## Missing Target Journeys" in md and "only a SKIP row for J-09" in md
+
+    def t_placeholder_prose_evidence_still_blocks():
+        # market-compass iter-34 AUDIT regression (finding B1): a waived journey's SKIP row whose
+        # Evidence cell is a PLACEHOLDER followed by prose cites nothing and must still block. The
+        # cell below is verbatim the one this iteration's own browser-qa lane wrote into
+        # reports/phase-goal-market-compass-iter-34-ui-test-results.llm.md — it defeated the
+        # original whole-cell equality check, and it also contains an incidental `docs/goal.md`
+        # path, so the head-placeholder conjunct (not the citation-shape one) is what rejects it.
+        real_world_cell = (
+            'none (evidence-based journey — no UI acceptance state to screenshot, per this '
+            'journey\'s own `docs/goal.md` "Walkthrough: waived" marker and the test plan\'s own '
+            'framing)')
+        assert _has_cited_evidence({"cells": ["", "", "", "", "", "", real_world_cell]}) is False
+        # …and prose with no artifact reference at all is likewise not a citation.
+        assert _has_cited_evidence({"cells": ["", "", "", "", "", "", "verified by measurement"]}) is False
+        # A real citation still counts, in every shape this repo actually writes.
+        for good in ("reports/perf-budgets.md#addendum-45",
+                     "`reports/perf-budgets.md` Addendum 45; `runs/x/j09-samples.csv`",
+                     "reports/qa/evidence/J-01-verify.png"):
+            assert _has_cited_evidence({"cells": ["", "", "", "", "", "", good]}) is True, good
+        row = (
+            "**Browser QA Verdict:** SKIPPED\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            f"| UT-J-09 | Backend fits the host | smoke | P1 | N/A — waived | no UI to check | "
+            f"SKIP | {real_world_cell} |\n")
+        md = merge([row], target_journeys=["J-09"], waived_journeys={"J-09"})
+        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
+
+    def t_unwaived_target_missing_or_skip_still_blocks():
+        # TC-8b: a target/required journey WITHOUT the goal.md marker (not in waived_journeys),
+        # missing or SKIP-only, must still force BLOCKED exactly as before this fix — the exemption
+        # must never generalize into a "no browser row" loophole for an unmarked journey.
+        md_missing = merge([clean_pair], target_journeys=["J-01", "J-05"], waived_journeys={"J-09"})
+        assert file_top_verdict(md_missing) == "BLOCKED", file_top_verdict(md_missing)
+        assert "## Missing Target Journeys" in md_missing and "UT-J-05" in md_missing
+
+        skip_row_unwaived = (
+            "**Browser QA Verdict:** SKIPPED\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-05 | Unwaived journey | regression | P1 | e | cites something real | SKIP | "
+            "reports/some-report.md |\n")
+        md_skip = merge([skip_row_unwaived], target_journeys=["J-05"], waived_journeys={"J-09"})
+        assert file_top_verdict(md_skip) == "BLOCKED", file_top_verdict(md_skip)
+        assert "only a SKIP row for J-05" in md_skip
+
+    def t_waived_exemption_applies_to_required_too():
+        # The same exemption, mirrored for Required-still-passing journeys (a waived journey can be
+        # BOTH required-still-passing in a later iteration and this iteration's own target).
+        waived_row = (
+            "**Browser QA Verdict:** SKIPPED\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-09 | Backend fits the host | smoke | P1 | N/A — waived | verified via "
+            "Addendum 45 | SKIP | reports/perf-budgets.md#addendum-45 |\n")
+        md = merge([waived_row], required_journeys=["J-09"], waived_journeys={"J-09"})
+        assert file_top_verdict(md) != "BLOCKED", file_top_verdict(md)
+        assert "## Missing Required Journeys" not in md
+
+    def t_no_waived_journeys_arg_unchanged():
+        # Default (no waived_journeys kwarg) is BYTE-IDENTICAL to passing an empty set — no
+        # regression on every pre-iter-34 call shape.
+        assert merge([clean_pair], target_journeys=["J-01"]) == merge(
+            [clean_pair], target_journeys=["J-01"], waived_journeys=None
+        )
+        assert merge([clean_pair], target_journeys=["J-01"], waived_journeys=set()) == merge(
+            [clean_pair], target_journeys=["J-01"]
+        )
+
     # Self-counting list (local form) rather than a hardcoded total — upstream's void
     # tests and the local verdict-normalization tests both live here, so a literal
     # count goes stale on the next pull.
... [diff_bound] incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py: 17 more diff lines omitted — Read the file for full detail
```
