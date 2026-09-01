#!/usr/bin/env python3
"""merge_ui_test_results.py — merge several ui-test-results.md files into one.

Goal mode's lean browser-QA runs in two lanes (see goal-iter-lean.sh):
  - the LLM browser-qa-agent verifies the NEW/changed (Target) journeys, and
  - the deterministic replay runner (demo_runner.py --mode verify) re-verifies the
    already-passing regression set from stored golden scripts.

Each lane writes a ui-test-results.md (same template). This merges them into the
single `reports/phase-<iter>-ui-test-results.md` the goal-evaluator reads, so that
contract is unchanged. Inputs are merged in order with LATER-WINS by Test ID, so a
journey the LLM re-confirmed overrides a replay verdict for the same journey (the
caller passes the replay file first, the authoritative LLM file last).

The merged `**Browser QA Verdict:**` is recomputed from the SURVIVING rows (after
later-wins), NOT from the input files' own headline verdicts — otherwise a replay
FAIL that the LLM later re-confirmed as PASS would wrongly keep the file at FAIL.

Usage:
  merge_ui_test_results.py <out.md> <in1.md> [<in2.md> ...]
  merge_ui_test_results.py void <results.md> <J-XX> [<J-YY> ...]
  merge_ui_test_results.py self-test

The `void` subcommand (SPEED-22 mass-false-FAIL breaker) rewrites the listed
journeys' FAIL rows to SKIP with a "voided" note, recomputes the headline
verdict from the surviving rows, and appends a dated loud footer — used when
2 green canary re-checks prove a majority-FAIL replay run was selector/
environment drift rather than real regressions.
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

# Tolerate markdown emphasis around the verdict word (`**FAIL**`) — agents write it
# both ways, and a bold cell/headline must never parse as "no verdict" (that once
# laundered a raw FAIL into a merged PASS at the achievement gate; ops-hardening
# iters 9/12).
_VERDICT_RE = re.compile(r"\*\*Browser QA Verdict:\*\*\s*[*_`~\s]*([A-Z_]+)")
# A results-table data row: | UT-xx | name | type | prio | expected | actual | VERDICT | evidence |
# ops-hardening iter-33: also match `TC-`-prefixed ids — four consecutive evaluators flagged that a
# QA input file whose rows are ALL `TC-`-prefixed (e.g. a smoke-test report for a launcher/tooling
# fix) previously failed to parse as rows at all, silently falling back to `compute_overall`'s
# file-level-verdict path and risking a laundered PASS over a real headline FAIL.
_ROW_RE = re.compile(r"^\|\s*((?:UT|TC)-[^|]+?)\s*\|(.*)\|\s*$")

# market-compass iter-34 (goal-mode harness fix, TC-7/TC-8): a journey's `docs/goal.md`
# Acceptance block naming the LITERAL marker `**Walkthrough:** waived` has no UI check to
# fail closed on -- forcing BLOCKED merely because it has no browser row (or only a SKIP
# row) mistakes "nothing to check" for "not verified". `_JOURNEY_BLOCK_RE` slices goal.md
# into one span per top-level journey (`- **J-NN ...` through the next such header, the
# next markdown heading, or EOF) so the waived set is read from the goal text itself, never
# guessed from a journey-ID pattern -- see `parse_waived_journeys_from_text`.
_JOURNEY_BLOCK_RE = re.compile(r"^-\s+\*\*(J-\d+)\b.*?(?=^-\s+\*\*J-\d+\b|^#|\Z)", re.MULTILINE | re.DOTALL)
_WALKTHROUGH_WAIVED_MARKER = "**Walkthrough:** waived"

# market-compass iter-34 AUDIT fix (finding B1) — see `_has_cited_evidence`. Words that mean
# "nothing was recorded here"; matched against the evidence cell's HEAD (not the whole cell), so
# `none (long explanation ...)` is recognised as the placeholder it is.
_PLACEHOLDER_EVIDENCE = (
    "", "none", "n/a", "na", "-", "--", "—", "tbd", "todo", "pending",
    "not applicable", "no evidence", "n/a.", "not captured",
)
# An artifact-shaped reference: a `dir/file` path, or a bare filename with a known evidence
# extension. Deliberately narrow — prose alone must not read as a citation.
_CITATION_SHAPE_RE = re.compile(
    r"[\w.\-]+/[\w./#\-]+|[\w.\-]+\.(?:md|csv|png|jpg|jsonl?|txt|log|html?)\b",
    re.IGNORECASE,
)


def _norm_verdict_cell(c: str) -> str:
    """Strip markdown emphasis/backticks so `**FAIL**`, `_PASS_`, `` `SKIP` ``
    normalize to the bare verdict word before matching."""
    return c.strip().strip("*_`~").strip().upper()
# Column order in the template (after the leading Test ID cell).
_C_NAME, _C_ACTUAL, _C_EVIDENCE = 0, 4, 6


def parse_waived_journeys_from_text(goal_text: str) -> "set[str]":
    """Bare journey IDs (`{'J-09', ...}`) whose `docs/goal.md` block carries the literal
    marker `**Walkthrough:** waived` -- the ONLY signal this module trusts (never a
    journey-ID pattern or a hardcoded list), so the exemption below is provably tied to
    goal.md's own text and cannot silently widen to an unmarked journey."""
    waived: "set[str]" = set()
    for m in _JOURNEY_BLOCK_RE.finditer(goal_text):
        if _WALKTHROUGH_WAIVED_MARKER in m.group(0):
            waived.add(m.group(1))
    return waived


def _default_waived_journeys() -> "set[str]":
    """Best-effort `parse_waived_journeys_from_text` over the repo's own `docs/goal.md`,
    resolved relative to this file (`lib/ -> automation/ -> scripts/ -> incredible_auto_dev/
    -> repo root`) so every existing caller (replay-lane.sh's unchanged CLI invocation
    included) picks up the exemption with zero new wiring. Fails SAFE: a missing/unreadable
    goal.md yields an empty set, i.e. byte-identical to pre-iter-34 behavior -- this can only
    ever REMOVE a spurious BLOCKED, never introduce a new one (see `merge`'s docstring)."""
    try:
        repo_root = Path(__file__).resolve().parents[4]
        text = (repo_root / "docs" / "goal.md").read_text(encoding="utf-8")
    except (OSError, IndexError):
        return set()
    return parse_waived_journeys_from_text(text)


def _has_cited_evidence(row: dict) -> bool:
    """True if `row`'s Evidence cell names something concrete. The walkthrough-waived exemption
    below requires this: a SKIP row for a UI-less journey must still point at SOMETHING (an
    addendum anchor, a CSV/PNG path, a report file) to count as "verified through cited non-UI
    evidence" rather than "not executed" -- an empty/placeholder Evidence cell still blocks
    exactly as before.

    market-compass iter-34 AUDIT fix (finding B1): the original form compared the WHOLE stripped
    cell against the placeholder tuple, so a placeholder with any prose after it slipped through.
    That is not hypothetical -- this very iteration's browser-qa lane wrote the cell
    `none (evidence-based journey -- no UI acceptance state to screenshot, per this journey's own
    docs/goal.md "Walkthrough: waived" marker ...)`, which cites nothing yet passed the old check
    (and would even satisfy a naive "contains a path" test, via the incidental `docs/goal.md`
    mention). Two conjuncts now, both of which that cell fails:
      1. the cell's HEAD (text before the first `(`/`[`/`;`/`,`) must not be a placeholder word, and
      2. the cell must contain at least one artifact-shaped reference (a `dir/file` path or a
         known evidence file extension).
    Both are fail-CLOSED: an evidence cell that cannot be recognised as a citation keeps the
    journey blocking, which is the safe direction for a verification exemption."""
    c = _cell(row, _C_EVIDENCE).strip().strip("`").strip()
    if not c:
        return False
    head = re.split(r"[(\[;,]", c, maxsplit=1)[0].strip().strip("`").strip().rstrip(".").lower()
    if head in _PLACEHOLDER_EVIDENCE:
        return False
    return bool(_CITATION_SHAPE_RE.search(c))


def _today() -> str:
    return datetime.date.today().isoformat()


def parse_rows(text: str) -> "list[dict]":
    """Extract results-table data rows. Returns dicts with test_id + cells +
    verdict (the cell that is one of PASS/FAIL/SKIP/SKIPPED)."""
    rows: list[dict] = []
    for line in text.splitlines():
        m = _ROW_RE.match(line.strip())
        if not m:
            continue
        test_id = m.group(1).strip()
        cells = [c.strip() for c in m.group(2).split("|")]
        # Skip a markdown header-separator row that happened to start with a dash run.
        if cells and all(set(c) <= {"-", ":"} for c in cells if c):
            continue
        verdict = ""
        for c in cells:
            cu = _norm_verdict_cell(c)
            # ops-hardening iter-40: BLOCKED joins the recognized verdict words, mirroring
            # demo_runner.py's already-shipped class (a journey never checked — e.g. the backend was
            # unreachable — distinct from FAIL, where it WAS checked and did not hold). Previously an
            # unrecognized BLOCKED cell fell all the way through to the empty-verdict default below,
            # silently dropping the row from `compute_overall`'s reckoning.
            if cu in ("PASS", "FAIL", "SKIP", "SKIPPED", "BLOCKED"):
                verdict = "SKIP" if cu == "SKIPPED" else cu
                break
        if not verdict:
            # Fallback for ANNOTATED verdict cells ("PASS (with caveat)",
            # "FAIL (see note)") — scan in REVERSE so the verdict column (right of
            # the free-prose Actual column) wins over any prose that happens to
            # start with a verdict word. \b keeps "FAILED ..." prose non-matching.
            for c in reversed(cells):
                mv = re.match(r"(PASS|FAIL|SKIPPED|SKIP|BLOCKED)\b", _norm_verdict_cell(c))
                if mv:
                    cu = mv.group(1)
                    verdict = "SKIP" if cu == "SKIPPED" else cu
                    break
        rows.append({"test_id": test_id, "cells": cells, "verdict": verdict,
                     "raw": "| " + test_id + " |" + m.group(2) + "|"})
    return rows


def file_top_verdict(text: str) -> str:
    m = _VERDICT_RE.search(text)
    return m.group(1) if m else ""


def verdict_for(text: str, test_id: str) -> str:
    """The single row's normalized verdict for `test_id` in `text` (`""` if not found) — the
    SAME PASS/FAIL/SKIP normalization `parse_rows` already uses, so it tolerates bold cells
    (`**FAIL**`) and ANNOTATED cells ("PASS (steps 1,2,4 verified live; step 3 not executed, see
    UT-J-04)", "SKIPPED (partial — see Actual)").

    ops-hardening iter-39 (TC-7): exists so a bash caller (replay-lane.sh's reconciliation
    footer) never has to re-implement that matching as a raw `grep -F '| PASS |'` — which is
    exactly what silently missed BOTH J-05 (FAIL -> PASS-with-caveat) and J-04 (FAIL -> SKIPPED-
    with-caveat) in iter-38: neither annotated cell contains the bare substring `| PASS |` or
    `| SKIP |` an exact-string grep requires, so the footer under-reported by omitting both."""
    for row in parse_rows(text):
        if row["test_id"] == test_id:
            return row["verdict"]
    return ""


def compute_overall(rows: "list[dict]", file_verdicts: "list[str] | None" = None) -> str:
    """Overall verdict. Surviving rows are authoritative; only when NO rows could
    be parsed do we fall back to the input files' headline verdicts.

    Priority FAIL > BLOCKED > PASS > SKIP/SKIPPED — ops-hardening iter-40, mirroring
    demo_runner.py's already-shipped `compute_regression_verdict` (BLOCKED is a DISTINCT class from
    FAIL: it means a journey's own assertions were never checked at all — e.g. the backend was
    unreachable — not that they were checked and failed; goal_gate.py already blocks achievement on
    any BLOCKED cell regardless of this headline, so this fixes the LLM-readable summary only). Before
    this fix an all-BLOCKED merged run fell through both branches below to the SKIPPED default,
    because BLOCKED matched neither "FAIL" nor "PASS" in either list — never a bare `PASS`."""
    verdicts = [r["verdict"] for r in rows if r["verdict"]]
    if verdicts:
        if "FAIL" in verdicts:
            return "FAIL"
        if "BLOCKED" in verdicts:
            return "BLOCKED"
        if "PASS" in verdicts:
            return "PASS"
        return "SKIPPED"
    file_verdicts = file_verdicts or []
    if "FAIL" in file_verdicts:
        return "FAIL"
    if "BLOCKED" in file_verdicts:
        return "BLOCKED"
    if "PASS" in file_verdicts:
        return "PASS"
    return "SKIPPED"


def _cell(row: dict, i: int) -> str:
    cells = row["cells"]
    return cells[i] if i < len(cells) else ""


def missing_required_journeys(rows: "list[dict]", required_journeys: "list[str] | None") -> "list[str]":
    """Which of `required_journeys` (bare IDs like `J-01`) have ZERO executed test cases in `rows`
    — i.e. no row at all, not even a BLOCKED/SKIP one. Distinct from BLOCKED (a row exists,
    recording that the journey's assertions were never checked) and from SKIP (a row exists,
    recording why it was skipped): "missing" means no lane produced ANY row for this required
    journey, so nothing about it was even recorded, let alone checked."""
    if not required_journeys:
        return []
    present_ids = {r["test_id"] for r in rows}
    missing = []
    for jid in required_journeys:
        tid = jid if jid.startswith("UT-") else f"UT-{jid}"
        if tid not in present_ids:
            missing.append(jid)
    return missing


def skipped_required_journeys(
    rows: "list[dict]",
    required_journeys: "list[str] | None",
    waived: "set[str] | None" = None,
) -> "list[str]":
    """Which of `required_journeys` have a row whose ONLY recorded outcome is `SKIP` — the journey
    was named, a row exists, and it says "not executed." The companion to
    `missing_required_journeys` above: iter-40's actual artifact
    (`reports/phase-goal-ops-hardening-iter-40-ui-test-results.md`) has a row for EVERY required
    journey, all of them `SKIP` ("Not executed — dispatch instructions state frontend is not
    available"), so the missing-row check alone still merged it into a clean `SKIPPED` headline —
    exactly the outcome iter-41's DoD ("an all-SKIP/zero-executed regression run can no longer merge
    into a clean SKIPPED/PASS headline") forbids, and exactly the shape the spec's own wording
    requires ("fresh, NON-`SKIP` mechanical verification"). Only a literal `SKIP` counts: a
    `DEFERRED-BUDGET` row (SPEED-15 rung 2, an explicit "keeps prior status" record) parses to an
    empty verdict and is deliberately NOT treated as a skip here — `goal_gate.py`'s
    `_DEFERRED_CELL_RE` already blocks achievement on those.

    market-compass iter-34: a journey in `waived` (its `docs/goal.md` Acceptance carries the
    literal `**Walkthrough:** waived` marker — see `parse_waived_journeys_from_text`) whose SKIP
    row ALSO carries cited evidence (`_has_cited_evidence`) is not counted here — it was verified
    through the cited non-UI evidence instead of a browser walkthrough. A waived journey whose
    SKIP row has no real citation (an empty/placeholder Evidence cell) still counts as skipped —
    the exemption is evidence-gated, never a blanket pass for the marker alone."""
    if not required_journeys:
        return []
    waived = waived or set()
    by_id = {r["test_id"]: r for r in rows}
    skipped = []
    for jid in required_journeys:
        tid = jid if jid.startswith("UT-") else f"UT-{jid}"
        row = by_id.get(tid)
        if row is not None and row["verdict"] == "SKIP":
            if jid in waived and _has_cited_evidence(row):
                continue
            skipped.append(jid)
    return skipped


def missing_target_journeys(rows: "list[dict]", target_journeys: "list[str] | None") -> "list[str]":
    """Which of `target_journeys` (bare IDs like `J-05`) have ZERO executed test cases in `rows` —
    the sibling of `missing_required_journeys` above, for the iteration spec's `Target journeys:`
    line instead of `Required-still-passing journeys:`. ops-hardening iter-41 audit finding B2 /
    iter-42 fix: promoting a journey to a phase/iteration's OWN target silently REMOVED its
    verification, because every gate in the chain (this one included, before this function existed)
    keyed off `Required-still-passing journeys:` only — an iteration whose stated purpose was
    re-verifying J-05/J-07 could ship a merged clean headline with zero rows for either. Kept as a
    separate function body (not a shared helper with `missing_required_journeys`) deliberately: this
    is correctness-critical merge-gate code, and the two guards must be independently readable and
    independently safe to touch without risking the other's already-hardened behavior."""
    if not target_journeys:
        return []
    present_ids = {r["test_id"] for r in rows}
    missing = []
    for jid in target_journeys:
        tid = jid if jid.startswith("UT-") else f"UT-{jid}"
        if tid not in present_ids:
            missing.append(jid)
    return missing


def skipped_target_journeys(
    rows: "list[dict]",
    target_journeys: "list[str] | None",
    waived: "set[str] | None" = None,
) -> "list[str]":
    """Which of `target_journeys` have a row whose ONLY recorded outcome is `SKIP` — the sibling of
    `skipped_required_journeys` above, for `Target journeys:` (see `missing_target_journeys`'s
    docstring for the full rationale). Only a literal `SKIP` counts (not `DEFERRED-BUDGET`), matching
    `skipped_required_journeys`'s own contract exactly, INCLUDING the market-compass iter-34
    walkthrough-waived-plus-cited-evidence exemption (see that function's docstring)."""
    if not target_journeys:
        return []
    waived = waived or set()
    by_id = {r["test_id"]: r for r in rows}
    skipped = []
    for jid in target_journeys:
        tid = jid if jid.startswith("UT-") else f"UT-{jid}"
        row = by_id.get(tid)
        if row is not None and row["verdict"] == "SKIP":
            if jid in waived and _has_cited_evidence(row):
                continue
            skipped.append(jid)
    return skipped


def merge(
    texts: "list[str]",
    required_journeys: "list[str] | None" = None,
    target_journeys: "list[str] | None" = None,
    waived_journeys: "set[str] | None" = None,
) -> str:
    """Merge in order; later inputs win per Test ID. Returns the merged markdown
    with a single authoritative headline verdict and detail rebuilt from the
    surviving rows (no verbatim per-lane embedding → exactly one verdict line).

    `required_journeys` (ops-hardening iter-41, A3 — TC-3): the iteration spec's own
    "Required-still-passing journeys:" list (bare IDs, e.g. `["J-01", "J-03"]`). iter-40 shipped
    ALL seven required-still-passing journeys with ZERO executed test cases while every gate
    (including this merger) reported a clean headline, because a journey with NO row at all was
    invisible to `compute_overall` — it only ever reasons about rows that exist. When at least one
    required journey has zero executed test cases (see `missing_required_journeys` above) AND the
    rows-derived headline would otherwise be a CLEAN "PASS" or "SKIPPED", the headline is forced to
    "BLOCKED" instead — reusing the existing BLOCKED semantics ("never checked at all") rather than
    inventing a second gate; `goal_gate.py` already blocks achievement on any BLOCKED verdict. A
    headline that was already FAIL or BLOCKED is left alone (already non-clean; the gap is still
    surfaced in the new "Missing Required Journeys" section below, but doesn't need to change an
    already-blocking headline).

    iter-41 audit (B1 fix): the same forcing applies to a required journey whose row exists but
    reads `SKIP` (`skipped_required_journeys` above). The zero-row check alone did NOT close
    iter-40's own failure mode — that run's merged file carries a `SKIP` row for all seven required
    journeys, so it still merged to a clean `SKIPPED` headline under the first implementation of
    this guard (reproduced directly against the committed iter-40 artifact). Both shapes mean the
    same thing to a reader of the headline — "this journey was not verified this iteration" — so
    both force `BLOCKED`.

    `target_journeys` (ops-hardening iter-42 — the sibling gap iter-41's own audit found, B2): the
    iteration spec's `Target journeys:` list. `required_journeys` above guards journeys that must
    STAY passing; `target_journeys` guards the journeys THIS iteration exists to verify — the exact
    ones iter-41 itself shipped with zero rows while its merged headline read a clean `PASS 6/6`
    (the binding iter-41 lesson: "promoting a journey to an iteration's target silently REMOVES its
    verification"). Same additive semantics as `required_journeys`: a missing/all-SKIP target
    journey forces `BLOCKED` on top of (never replacing) the required-journey guard, and a headline
    already FAIL/BLOCKED is left alone.

    `waived_journeys` (market-compass iter-34 — goal-mode harness fix, TC-7/TC-8): bare IDs whose
    `docs/goal.md` Acceptance carries the literal `**Walkthrough:** waived` marker (read by
    `main()` via `_default_waived_journeys`/`parse_waived_journeys_from_text` — never a
    journey-ID pattern). Threaded into `skipped_required_journeys`/`skipped_target_journeys`
    ONLY: a waived journey's SKIP row that also carries cited evidence
    (`_has_cited_evidence`) is treated as verified through that evidence instead of "not
    executed" and does not force BLOCKED; a waived journey that is MISSING entirely, or whose
    SKIP row has no real citation, still forces BLOCKED exactly as before — the exemption can
    only ever REMOVE a spurious BLOCKED for a marked, evidenced journey, never widen past that
    (TC-8b: an unmarked journey's missing/SKIP-only row is unaffected)."""
    by_id: "dict[str, dict]" = {}
    order: "list[str]" = []
    file_verdicts: "list[str]" = []
    for text in texts:
        file_verdicts.append(file_top_verdict(text))
        for row in parse_rows(text):
            tid = row["test_id"]
            if tid not in by_id:
                order.append(tid)
            by_id[tid] = row  # later wins
    rows = [by_id[t] for t in order]
    overall = compute_overall(rows, file_verdicts)
    waived_journeys = waived_journeys or set()
    missing_required = missing_required_journeys(rows, required_journeys)
    skipped_required = skipped_required_journeys(rows, required_journeys, waived_journeys)
    missing_target = missing_target_journeys(rows, target_journeys)
    skipped_target = skipped_target_journeys(rows, target_journeys, waived_journeys)
    if (missing_required or skipped_required or missing_target or skipped_target) and overall in ("PASS", "SKIPPED"):
        overall = "BLOCKED"
    n_pass = sum(1 for r in rows if r["verdict"] == "PASS")
    n_skip = sum(1 for r in rows if r["verdict"] == "SKIP")
    n_blocked = sum(1 for r in rows if r["verdict"] == "BLOCKED")
    total = len(rows)

    overall_line = f"**Overall:** {n_pass}/{total} journeys passed ({n_skip} skipped"
    overall_line += f", {n_blocked} blocked" if n_blocked else ""
    overall_line += f", {len(missing_required)} required-missing" if missing_required else ""
    overall_line += f", {len(skipped_required)} required-unverified" if skipped_required else ""
    overall_line += f", {len(missing_target)} target-missing" if missing_target else ""
    overall_line += f", {len(skipped_target)} target-unverified" if skipped_target else ""
    overall_line += ")"
    out = ["# UI Test Results (merged)", "",
           f"**Date:** {_today()}",
           "**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)",
           "", "---", "",
           f"**Browser QA Verdict:** {overall}", "",
           overall_line,
           "", "---", "", "## Results Table", "",
           "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |",
           "|---------|------|------|----------|----------|--------|---------|----------|"]
    for r in rows:
        out.append(r["raw"])
    out.append("")

    failed = [r for r in rows if r["verdict"] == "FAIL"]
    skipped = [r for r in rows if r["verdict"] == "SKIP"]
    blocked = [r for r in rows if r["verdict"] == "BLOCKED"]
    if missing_required or skipped_required:
        out += ["## Missing Required Journeys", "",
                "_Required-still-passing journeys named in the iteration spec that were NOT "
                "verified this iteration — either no lane (deterministic replay or LLM browser-qa) "
                "produced a row for them at all, or the only row they have reads SKIP (not "
                "executed). Never a clean PASS/SKIPPED headline while any of these are present "
                "(ops-hardening iter-40 lesson: this is exactly how required journeys shipped with "
                "zero evidence while every gate reported clean)._", ""]
        for jid in missing_required:
            out.append(f"- `UT-{jid}` — no test case executed for {jid} by any lane")
        for jid in skipped_required:
            out.append(f"- `UT-{jid}` — only a SKIP row for {jid}: named but never executed")
        out.append("")
    if missing_target or skipped_target:
        out += ["## Missing Target Journeys", "",
                "_Target journeys named in the iteration spec's `Target journeys:` line — the "
                "journeys THIS iteration exists to verify — that were NOT verified this iteration, "
                "either no lane produced a row for them at all, or the only row they have reads "
                "SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are "
                "present (ops-hardening iter-41 audit finding B2 / iter-42 fix: promoting a journey "
                "to an iteration's own target silently removed its verification — iter-41 itself "
                "shipped a clean PASS 6/6 headline while its two target journeys had zero rows "
                "anywhere)._", ""]
        for jid in missing_target:
            out.append(f"- `UT-{jid}` — no test case executed for {jid} by any lane")
        for jid in skipped_target:
            out.append(f"- `UT-{jid}` — only a SKIP row for {jid}: named but never executed")
        out.append("")
    if failed:
        out += ["## Failed Tests", ""]
        for r in failed:
            out += [f"### {r['test_id']} — {_cell(r, _C_NAME)}", "",
                    "**Verdict:** FAIL",
                    f"**Failure:** {_cell(r, _C_ACTUAL)}",
                    f"**Evidence:** `{_cell(r, _C_EVIDENCE) or 'none'}`", ""]
    if skipped:
        out += ["## Skipped Tests", ""]
        for r in skipped:
            out += [f"### {r['test_id']} — {_cell(r, _C_NAME)}", "",
                    "**Verdict:** SKIPPED",
                    f"**Reason:** {_cell(r, _C_ACTUAL)}", ""]
    if blocked:
        out += ["## Blocked Tests", "",
                "_Not a journey failure — its own assertions were never checked (e.g. the backend was "
                "unreachable). Distinct from FAIL: FAIL means the journey's own assertions did not "
                "hold; BLOCKED means they were never checked._", ""]
        for r in blocked:
            out += [f"### {r['test_id']} — {_cell(r, _C_NAME)}", "",
                    "**Verdict:** BLOCKED",
                    f"**Reason:** {_cell(r, _C_ACTUAL)}", ""]
    out += ["## Environment", "",
            "- **Browser:** Chromium (LLM browser-qa + deterministic replay)",
            f"- **Test Date:** {_today()}", ""]
    return "\n".join(out) + "\n"


_VOID_NOTE = ("voided: suspected selector/environment drift — mass replay FAIL "
              "overturned by green canary re-checks")


def void_text(text: str, journeys: "list[str]") -> "tuple[str, list[str]]":
    """Pure transform for the `void` subcommand: rewrite the listed journeys'
    FAIL rows to SKIP + the voided note, recompute the headline from the
    surviving rows, append a dated footer. Returns (new_text, voided_ids)."""
    want = {f"UT-{j}" for j in journeys} | set(journeys)
    voided: list[str] = []
    out_lines: list[str] = []
    for line in text.splitlines():
        m = _ROW_RE.match(line.strip())
        if m:
            tid = m.group(1).strip()
            # Split on UNESCAPED pipes only — the replay renderer escapes '|'
            # inside cells as '\|'; a bare split would shift every later cell.
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", m.group(2))]
            is_sep = cells and all(set(c) <= {"-", ":"} for c in cells if c)
            if tid in want and not is_sep and any(c.upper() == "FAIL" for c in cells):
                new_cells = []
                for idx, c in enumerate(cells):
                    if c.upper() == "FAIL":
                        new_cells.append("SKIP")
                    elif idx == _C_ACTUAL:
                        new_cells.append(_VOID_NOTE)
                    else:
                        new_cells.append(c)
                out_lines.append("| " + tid + " | " + " | ".join(new_cells) + " |")
                voided.append(tid)
                continue
        out_lines.append(line)
    if not voided:
        return text, []
    new_text = "\n".join(out_lines)
    rows = parse_rows(new_text)
    overall = compute_overall(rows)
    new_text = _VERDICT_RE.sub(f"**Browser QA Verdict:** {overall}", new_text, count=1)
    ids = " ".join(sorted({t.replace('UT-', '', 1) for t in voided}))
    new_text += (
        f"\n\n---\n\n_VOIDED ({_today()}): the FAIL rows for {ids} above were VOIDED "
        "(SPEED-22 mass-false-FAIL breaker) — a majority of the replay set failed at "
        "once and the canary journeys re-checked GREEN via the LLM lane, so the "
        "failures are suspected golden-script/selector drift, not product "
        "regressions. These journeys keep their prior recorded status; their golden "
        "scripts are queued for regeneration (state/goldens-regen-pending) and are "
        "re-derived from the next verified demo recording._\n"
    )
    return new_text, sorted({t.replace("UT-", "", 1) for t in voided})


def cmd_void(path: str, journeys: "list[str]") -> int:
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        sys.stderr.write(f"[merge_ui_test_results] void: unreadable {path}: {exc}\n")
        return 2
    new_text, voided = void_text(text, journeys)
    if not voided:
        print("[merge_ui_test_results] void: no matching FAIL rows — file unchanged")
        return 0
    p.write_text(new_text, encoding="utf-8")
    print(f"[merge_ui_test_results] voided FAIL rows for: {' '.join(voided)}")
    return 0


def cmd_verdict_of(path: str, test_id: str) -> int:
    """Print `test_id`'s normalized verdict word in `path` (empty line if the file is unreadable
    or the row is not found) — a stable, tested CLI surface for a bash caller that needs the
    SAME annotation-tolerant parsing `parse_rows` already uses (see `verdict_for`'s docstring)."""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        print("")
        return 0
    print(verdict_for(text, test_id))
    return 0


def main(argv: "list[str]") -> int:
    if argv and argv[0] in ("self-test", "--self-test"):
        return _self_test()
    if argv and argv[0] == "void":
        if len(argv) < 3:
            sys.stderr.write("usage: merge_ui_test_results.py void <results.md> <J-XX> [...]\n")
            return 2
        return cmd_void(argv[1], argv[2:])
    if argv and argv[0] == "verdict-of":
        if len(argv) < 3:
            sys.stderr.write("usage: merge_ui_test_results.py verdict-of <results.md> <test-id>\n")
            return 2
        return cmd_verdict_of(argv[1], argv[2])
    # ops-hardening iter-41 (A3): an optional `--required J-01,J-03,...` flag (space- or
    # comma-separated; may appear anywhere in argv) names this iteration's required-still-passing
    # journeys, so `merge` can detect any with ZERO executed test cases. Absent (the pre-iter-41
    # call shape every existing caller still uses until its bash wiring passes this) => no change
    # in behavior, matching every pre-existing test in this file's self-test suite.
    # ops-hardening iter-42: a sibling `--target J-05,J-07,...` flag, same parsing shape, for the
    # iteration spec's `Target journeys:` line (see `merge`'s docstring). Absent => no change in
    # behavior, same as `--required`.
    # market-compass iter-34: an optional `--waived J-09,...` override for tests/manual runs; when
    # ABSENT (every existing caller, replay-lane.sh included — zero new bash wiring needed) the
    # waived set is read automatically from the repo's own docs/goal.md
    # (`_default_waived_journeys`), so the exemption applies with no CLI change required anywhere.
    required: list[str] = []
    target: list[str] = []
    waived_arg: "list[str] | None" = None
    rest: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--required" and i + 1 < len(argv):
            required = [j for j in argv[i + 1].replace(",", " ").split() if j]
            i += 2
            continue
        if a.startswith("--required="):
            required = [j for j in a.split("=", 1)[1].replace(",", " ").split() if j]
            i += 1
            continue
        if a == "--target" and i + 1 < len(argv):
            target = [j for j in argv[i + 1].replace(",", " ").split() if j]
            i += 2
            continue
        if a.startswith("--target="):
            target = [j for j in a.split("=", 1)[1].replace(",", " ").split() if j]
            i += 1
            continue
        if a == "--waived" and i + 1 < len(argv):
            waived_arg = [j for j in argv[i + 1].replace(",", " ").split() if j]
            i += 2
            continue
        if a.startswith("--waived="):
            waived_arg = [j for j in a.split("=", 1)[1].replace(",", " ").split() if j]
            i += 1
            continue
        rest.append(a)
        i += 1
    argv = rest
    if len(argv) < 2:
        sys.stderr.write(
            "usage: merge_ui_test_results.py [--required J-01,J-03,...] [--target J-05,J-07,...] "
            "[--waived J-09,...] <out.md> <in1.md> [<in2.md> ...]\n"
        )
        return 2
    waived = set(waived_arg) if waived_arg is not None else _default_waived_journeys()
    out_path = Path(argv[0])
    texts: list[str] = []
    for p in argv[1:]:
        fp = Path(p)
        if fp.exists():
            texts.append(fp.read_text(encoding="utf-8"))
    if not texts:
        sys.stderr.write("[merge_ui_test_results] no readable input files\n")
        return 2
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        merge(texts, required_journeys=required, target_journeys=target, waived_journeys=waived),
        encoding="utf-8",
    )
    print(f"[merge_ui_test_results] merged {len(texts)} file(s) → {out_path}")
    return 0


# ── self-test (no filesystem) ────────────────────────────────────────────────

def _self_test() -> int:
    failures: list[str] = []

    def check(name, fn):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{name}: {exc!r}")

    replay = (
        "**Browser QA Verdict:** FAIL\n\n## Results Table\n"
        "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| UT-J-06 | View dashboard | regression | P1 | e | ok | PASS | a.png |\n"
        "| UT-J-07 | Filter table | regression | P1 | e | step 3 failed | FAIL | b.png |\n")
    llm = (
        "**Browser QA Verdict:** PASS\n\n## Results Table\n"
        "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| UT-J-20 | New feature | smoke | P1 | e | ok | PASS | c.png |\n"
        "| UT-J-07 | Filter table | smoke | P1 | e | works on recheck | PASS | d.png |\n")

    def t_parse():
        rows = parse_rows(replay)
        assert [r["test_id"] for r in rows] == ["UT-J-06", "UT-J-07"], rows
        assert rows[1]["verdict"] == "FAIL", rows[1]
        # the header-separator row must not be mistaken for data
        assert all(r["test_id"].startswith("UT-") for r in rows), rows

    def t_later_wins():
        # replay says J-07 FAIL, LLM re-confirm says PASS → LLM (later) wins → overall PASS.
        md = merge([replay, llm])
        rows = parse_rows(md)
        ids = {r["test_id"]: r["verdict"] for r in rows}
        assert ids == {"UT-J-06": "PASS", "UT-J-07": "PASS", "UT-J-20": "PASS"}, ids
        # the merged headline (the ONLY verdict line) must be PASS, not FAIL
        assert file_top_verdict(md) == "PASS", file_top_verdict(md)
        assert md.count("**Browser QA Verdict:**") == 1, "exactly one headline verdict"

    def t_real_fail_survives():
        # replay FAIL with no later override → overall FAIL.
        md = merge([replay])
        assert file_top_verdict(md) == "FAIL", file_top_verdict(md)
        assert "## Failed Tests" in md and "UT-J-07" in md

    def t_skipped_only():
        skip = ("**Browser QA Verdict:** SKIPPED\n## Results Table\n"
                "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
                "|---|---|---|---|---|---|---|---|\n"
                "| UT-J-09 | Export | regression | P1 | e | no script | SKIP | none |\n")
        md = merge([skip])
        assert file_top_verdict(md) == "SKIPPED", file_top_verdict(md)
        assert "## Skipped Tests" in md

    def t_bold_verdicts():
        # Markdown-bold verdict cells/headlines must parse, not vanish (the vanish
        # path let compute_overall() see only the PASS rows and return PASS over a
        # real FAIL — observed live in ops-hardening iters 9/12).
        bold = (
            "**Browser QA Verdict:** **FAIL**\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-01 | Happy path | smoke | P1 | e | ok | **PASS** | a.png |\n"
            "| UT-J-02 | Crash case | regression | P1 | e | zeros shown | **FAIL** | b.png |\n"
            "| UT-J-03 | Needs op | regression | P2 | e | no operator | `SKIPPED` | none |\n")
        rows = parse_rows(bold)
        assert [r["verdict"] for r in rows] == ["PASS", "FAIL", "SKIP"], rows
        assert file_top_verdict(bold) == "FAIL", file_top_verdict(bold)
        md = merge([bold])
        assert file_top_verdict(md) == "FAIL", file_top_verdict(md)

    def t_verdict_for_tolerates_annotated_cells():
        # ops-hardening iter-39 (TC-7): verdict_for must resolve the SAME normalized verdict for
        # an annotated cell that parse_rows already tolerates — reproduces the exact iter-38 rows
        # that a naive `grep -F '| PASS |'` missed (J-05: FAIL -> PASS-with-caveat; a FAIL ->
        # SKIPPED-with-caveat case mirroring J-04).
        annotated = (
            "**Browser QA Verdict:** PASS\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-05 | Aggregates precomputed | regression | P1 | e | steps 1,2,4 verified | "
            "PASS (steps 1,2,4 verified live; step 3 not executed, see UT-J-04) | a.png |\n"
            "| UT-J-04 | Non-blocking boot | regression | P1 | e | not executed live | "
            "SKIPPED (partial — see Actual) | b.png |\n"
            "| UT-J-02 | Still broken | regression | P1 | e | step 2 failed | FAIL | c.png |\n")
        assert verdict_for(annotated, "UT-J-05") == "PASS", verdict_for(annotated, "UT-J-05")
        assert verdict_for(annotated, "UT-J-04") == "SKIP", verdict_for(annotated, "UT-J-04")
        assert verdict_for(annotated, "UT-J-02") == "FAIL", verdict_for(annotated, "UT-J-02")
        assert verdict_for(annotated, "UT-J-99") == "", verdict_for(annotated, "UT-J-99")

    def t_annotated_verdicts():
        # "PASS (with caveat)" / "FAIL (see note)" must parse as their verdict; prose
        # in the Actual column that merely STARTS with a verdict word must lose to the
        # real verdict column (reverse scan), and "failed ..." prose must never match.
        ann = (
            "**Browser QA Verdict:** FAIL\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-A-01 | Caveated ok | ux | P2 | e | banner amber | PASS (with noted caveat) | a.png |\n"
            "| UT-A-02 | Caveated bad | reg | P1 | e | FAIL: zeros persisted after crash | FAIL (see note) | b.png |\n"
            "| UT-A-03 | Prose only | reg | P1 | e | step 3 failed early | **PASS** | c.png |\n")
        rows = parse_rows(ann)
        assert [r["verdict"] for r in rows] == ["PASS", "FAIL", "PASS"], rows

    def t_tc_prefixed_fail_survives():
        # ops-hardening iter-33 (TC-10) — a QA input file whose ONLY rows use `TC-`-prefixed ids (e.g. a
        # launcher/tooling smoke-test report, as opposed to the usual `UT-` journey ids) and a headline
        # FAIL must have that FAIL survive the merge, not get silently laundered into a PASS/SKIPPED
        # because `_ROW_RE` failed to parse any row and `compute_overall` fell back to the file's own
        # headline verdict. RED against the pre-iter-33 `UT-`-only regex (every row here is unparsed,
        # `parse_rows` returns []); GREEN after the `(?:UT|TC)-` widen.
        tc_only = (
            "**Browser QA Verdict:** FAIL\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| TC-1 | Stale build rebuilds | smoke | P1 | e | build ran, next start bound to port | PASS | a.png |\n"
            "| TC-3 | Broken source fails clean | smoke | P1 | e | stale next dev process left running | FAIL | b.png |\n")
        rows = parse_rows(tc_only)
        assert [r["test_id"] for r in rows] == ["TC-1", "TC-3"], rows
        assert rows[1]["verdict"] == "FAIL", rows[1]
        md = merge([tc_only])
        assert file_top_verdict(md) == "FAIL", (
            f"expected the TC-3 FAIL to survive the merge, got headline {file_top_verdict(md)!r}"
        )
        assert "## Failed Tests" in md and "TC-3" in md

    mass = (
        "**Browser QA Verdict:** FAIL\n\n## Results Table\n"
        "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| UT-J-01 | login | regression | P1 | e | ok | PASS | a.png |\n"
        "| UT-J-02 | browse | regression | P1 | e | step 2 failed | FAIL | b.png |\n"
        "| UT-J-03 | export | regression | P1 | e | step 1 failed | FAIL | c.png |\n"
        "| UT-J-04 | filter | regression | P1 | e | step 4 failed | FAIL | d.png |\n")

    def t_void_rewrites_and_recomputes():
        # Void ALL the FAILs → SKIP rows with the note, headline flips to PASS
        # (the surviving PASS row wins), dated footer appended exactly once.
        new, voided = void_text(mass, ["J-02", "J-03", "J-04"])
        assert voided == ["J-02", "J-03", "J-04"], voided
        rows = {r["test_id"]: r["verdict"] for r in parse_rows(new)}
        assert rows == {"UT-J-01": "PASS", "UT-J-02": "SKIP", "UT-J-03": "SKIP", "UT-J-04": "SKIP"}, rows
        assert file_top_verdict(new) == "PASS", file_top_verdict(new)
        assert new.count("_VOIDED (") == 1 and "voided: suspected selector" in new
        assert new.count("**Browser QA Verdict:**") == 1

    def t_void_keeps_unlisted_fail():
        # An un-listed FAIL survives and keeps the headline at FAIL.
        new, voided = void_text(mass, ["J-02"])
        assert voided == ["J-02"], voided
        rows = {r["test_id"]: r["verdict"] for r in parse_rows(new)}
        assert rows["UT-J-03"] == "FAIL" and rows["UT-J-02"] == "SKIP", rows
        assert file_top_verdict(new) == "FAIL", file_top_verdict(new)

    def t_void_no_match_is_noop():
        new, voided = void_text(mass, ["J-99"])
        assert voided == [] and new == mass

    def t_blocked_all_headlines_blocked():
        # TC-6 (iter-40) — two input files whose surviving rows are ALL BLOCKED merge to a BLOCKED
        # headline, never PASS (falls through both `verdicts`/`file_verdicts` "PASS" checks) or
        # SKIPPED (the pre-fix default when nothing else matched).
        f1 = (
            "**Browser QA Verdict:** BLOCKED\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-01 | Backfill honors range | regression | P1 | e | backend unreachable | BLOCKED | none |\n")
        f2 = (
            "**Browser QA Verdict:** BLOCKED\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-03 | No per-run range cap | regression | P1 | e | backend unreachable | BLOCKED | none |\n")
        rows = parse_rows(f1)
        assert rows[0]["verdict"] == "BLOCKED", rows
        md = merge([f1, f2])
        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
        assert "## Blocked Tests" in md and "UT-J-01" in md and "UT-J-03" in md
        assert "## Failed Tests" not in md and "## Skipped Tests" not in md

    def t_fail_still_wins_over_blocked():
        # TC-7 (iter-40) — a merged set with at least one FAIL and at least one BLOCKED headlines FAIL
        # (FAIL still wins), mirroring demo_runner.py's compute_regression_verdict ordering.
        mixed = (
            "**Browser QA Verdict:** FAIL\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-05 | Aggregates precomputed | regression | P1 | e | zeros shown | FAIL | a.png |\n"
            "| UT-J-06 | Pages load lazily | regression | P1 | e | backend unreachable | BLOCKED | none |\n")
        md = merge([mixed])
        assert file_top_verdict(md) == "FAIL", file_top_verdict(md)
        assert "## Failed Tests" in md and "## Blocked Tests" in md
        # and directly against compute_overall, independent of any markdown rendering:
        assert compute_overall([{"verdict": "FAIL"}, {"verdict": "BLOCKED"}]) == "FAIL"
        assert compute_overall([{"verdict": "BLOCKED"}, {"verdict": "PASS"}]) == "BLOCKED"
        assert compute_overall([{"verdict": "BLOCKED"}, {"verdict": "SKIP"}]) == "BLOCKED"

    def t_void_respects_escaped_pipes():
        # The replay renderer escapes '|' in cells; void must not split on it.
        esc = (
            "**Browser QA Verdict:** FAIL\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-07 | Filter \\| sort table | regression | P1 | e | step 2 failed | FAIL | b.png |\n")
        new, voided = void_text(esc, ["J-07"])
        assert voided == ["J-07"], voided
        row = [l for l in new.splitlines() if l.startswith("| UT-J-07")][0]
        # verdict flipped, the note landed in the Actual cell, the escaped
        # pipe survived, and the column count is unchanged
        assert "| SKIP |" in row and _VOID_NOTE in row and "\\|" in row, row
        assert len(re.split(r"(?<!\\)\|", row)) == len(re.split(r"(?<!\\)\|",
            "| UT-J-07 | Filter \\| sort table | regression | P1 | e | step 2 failed | FAIL | b.png |")), row

    # ==============================================================================================
    # ops-hardening iter-41 (A3, TC-3) — a required-still-passing journey with ZERO executed test
    # cases must never merge into a clean PASS/SKIPPED headline.
    # ==============================================================================================
    clean_pair = (
        "**Browser QA Verdict:** PASS\n\n## Results Table\n"
        "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| UT-J-01 | Backfill honors range | regression | P1 | e | ok | PASS | a.png |\n")

    def t_missing_required_journey_blocks_clean_pass():
        # iter-40's own failure mode reproduced: J-03 is required-still-passing but NO lane ever
        # produced a row for it (unlike BLOCKED, where a row exists recording "never checked") --
        # the merge must not headline a clean PASS while that gap is invisible.
        md = merge([clean_pair], required_journeys=["J-01", "J-03"])
        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
        assert "## Missing Required Journeys" in md and "UT-J-03" in md
        # the journey that DID execute keeps its own row/verdict untouched.
        assert verdict_for(md, "UT-J-01") == "PASS", verdict_for(md, "UT-J-01")

    def t_missing_required_journey_blocks_clean_skipped():
        skip_only = (
            "**Browser QA Verdict:** SKIPPED\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-09 | Export | regression | P1 | e | no script | SKIP | none |\n")
        md = merge([skip_only], required_journeys=["J-01"])
        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
        assert "## Missing Required Journeys" in md and "UT-J-01" in md

    def t_all_skip_required_journeys_block_clean_skipped():
        # iter-41 audit (B1): iter-40's ACTUAL artifact shape — a row EXISTS for every required
        # journey, and every one of them reads SKIP ("not executed"). The zero-row check alone
        # left this merging into a clean SKIPPED headline, which is precisely the DoD line
        # "an all-SKIP/zero-executed regression run can no longer merge into a clean
        # SKIPPED/PASS headline".
        all_skip = (
            "**Browser QA Verdict:** SKIPPED\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-01 | Backfill honors range | regression | P1 | e | Not executed — frontend down | SKIP | none |\n"
            "| UT-J-03 | No per-run range cap | regression | P1 | e | Not executed — frontend down | SKIP | none |\n")
        md = merge([all_skip], required_journeys=["J-01", "J-03"])
        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
        assert "## Missing Required Journeys" in md
        assert "only a SKIP row for J-01" in md and "only a SKIP row for J-03" in md

    def t_mixed_skip_and_pass_blocks_only_on_the_skip():
        # A required journey that really was executed keeps its PASS; the one that only has a
        # SKIP row still forces the headline off clean.
        mixed = (
            "**Browser QA Verdict:** PASS\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-01 | Backfill honors range | regression | P1 | e | ok | PASS | a.png |\n"
            "| UT-J-03 | No per-run range cap | regression | P1 | e | Not executed | SKIP | none |\n")
        md = merge([mixed], required_journeys=["J-01", "J-03"])
        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
        assert verdict_for(md, "UT-J-01") == "PASS", verdict_for(md, "UT-J-01")
        assert "only a SKIP row for J-03" in md
        # a NON-required journey's SKIP row must NOT trip the guard
        md2 = merge([mixed], required_journeys=["J-01"])
        assert file_top_verdict(md2) == "PASS", file_top_verdict(md2)
        assert "## Missing Required Journeys" not in md2

    def t_all_required_present_stays_clean():
        # No missing required journey -> headline and rendering are UNCHANGED (no regression on the
        # common case, and no "Missing Required Journeys" section when there is nothing missing).
        md = merge([clean_pair], required_journeys=["J-01"])
        assert file_top_verdict(md) == "PASS", file_top_verdict(md)
        assert "## Missing Required Journeys" not in md

    def t_no_required_journeys_arg_unchanged():
        # The default (no `required_journeys` argument at all) is BYTE-IDENTICAL to before this
        # iteration -- every pre-existing caller of merge() until its bash wiring passes `--required`.
        assert merge([clean_pair]) == merge([clean_pair], required_journeys=None)
        assert merge([clean_pair], required_journeys=[]) == merge([clean_pair])

    def t_missing_required_never_downgrades_fail_or_blocked():
        # A real FAIL (or an existing BLOCKED) elsewhere must stay exactly that -- the missing-
        # required check only ever prevents a CLEAN PASS/SKIPPED, never overrides a worse verdict.
        fail_pair = (
            "**Browser QA Verdict:** FAIL\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-01 | Backfill honors range | regression | P1 | e | step 2 failed | FAIL | a.png |\n")
        md = merge([fail_pair], required_journeys=["J-01", "J-99"])
        assert file_top_verdict(md) == "FAIL", file_top_verdict(md)
        assert "## Missing Required Journeys" in md and "UT-J-99" in md

    def t_missing_required_via_cli_required_flag():
        # main()'s `--required` parsing (anywhere in argv, comma- or space-separated) reaches merge()
        # exactly like the direct kwarg above -- the bash wiring in lib/replay-lane.sh depends on this.
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            out = f"{td}/out.md"
            in1 = f"{td}/in1.md"
            Path(in1).write_text(clean_pair, encoding="utf-8")
            rc = main(["--required", "J-01,J-03", out, in1])
            assert rc == 0, rc
            merged = Path(out).read_text(encoding="utf-8")
            assert file_top_verdict(merged) == "BLOCKED", file_top_verdict(merged)
            assert "UT-J-03" in merged

    # ==============================================================================================
    # ops-hardening iter-42 — a TARGET journey (the iteration's own `Target journeys:` line) with
    # ZERO executed test cases must never merge into a clean PASS/SKIPPED headline either — the
    # sibling gap iter-41's own audit caught: iter-41 shipped a clean PASS 6/6 headline while its
    # two target journeys (J-05, J-07) had zero rows anywhere, because nothing in the chain keyed
    # off `Target journeys:` at all.
    # ==============================================================================================
    def t_missing_target_journey_blocks_clean_pass():
        md = merge([clean_pair], target_journeys=["J-01", "J-05"])
        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
        assert "## Missing Target Journeys" in md and "UT-J-05" in md
        assert verdict_for(md, "UT-J-01") == "PASS", verdict_for(md, "UT-J-01")

    def t_all_skip_target_journeys_block_clean_skipped():
        all_skip = (
            "**Browser QA Verdict:** SKIPPED\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-05 | Aggregates precomputed at ingest | regression | P1 | e | frontend down | SKIP | none |\n"
            "| UT-J-07 | Heavy aggregates never take the service down | regression | P1 | e | frontend down | SKIP | none |\n")
        md = merge([all_skip], target_journeys=["J-05", "J-07"])
        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
        assert "## Missing Target Journeys" in md
        assert "only a SKIP row for J-05" in md and "only a SKIP row for J-07" in md

    def t_target_and_required_guards_both_apply_independently():
        # A required journey is fully verified (PASS) but the iteration's OWN target journey has
        # zero rows -- the target guard alone must still force BLOCKED, with its own section, even
        # though the required-journey guard has nothing to report.
        md = merge([clean_pair], required_journeys=["J-01"], target_journeys=["J-05"])
        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
        assert "## Missing Target Journeys" in md and "UT-J-05" in md
        assert "## Missing Required Journeys" not in md  # nothing missing on the required side
        # and the reverse: a satisfied target alongside a missing required journey.
        target_pair = (
            "**Browser QA Verdict:** PASS\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-05 | Aggregates precomputed | regression | P1 | e | ok | PASS | a.png |\n")
        md2 = merge([target_pair], required_journeys=["J-01"], target_journeys=["J-05"])
        assert file_top_verdict(md2) == "BLOCKED", file_top_verdict(md2)
        assert "## Missing Required Journeys" in md2 and "UT-J-01" in md2
        assert "## Missing Target Journeys" not in md2

    def t_all_target_present_stays_clean():
        md = merge([clean_pair], target_journeys=["J-01"])
        assert file_top_verdict(md) == "PASS", file_top_verdict(md)
        assert "## Missing Target Journeys" not in md

    def t_no_target_journeys_arg_unchanged():
        assert merge([clean_pair]) == merge([clean_pair], target_journeys=None)
        assert merge([clean_pair], target_journeys=[]) == merge([clean_pair])
        # and with a required_journeys arg present but no target_journeys arg at all, still
        # byte-identical to the pre-iter-42 two-arg call shape.
        assert merge([clean_pair], required_journeys=["J-01"]) == merge(
            [clean_pair], required_journeys=["J-01"], target_journeys=None
        )

    def t_missing_target_never_downgrades_fail_or_blocked():
        fail_pair = (
            "**Browser QA Verdict:** FAIL\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-01 | Backfill honors range | regression | P1 | e | step 2 failed | FAIL | a.png |\n")
        md = merge([fail_pair], target_journeys=["J-01", "J-05"])
        assert file_top_verdict(md) == "FAIL", file_top_verdict(md)
        assert "## Missing Target Journeys" in md and "UT-J-05" in md

    def t_missing_target_via_cli_target_flag():
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            out = f"{td}/out.md"
            in1 = f"{td}/in1.md"
            Path(in1).write_text(clean_pair, encoding="utf-8")
            rc = main(["--target", "J-01,J-05", out, in1])
            assert rc == 0, rc
            merged = Path(out).read_text(encoding="utf-8")
            assert file_top_verdict(merged) == "BLOCKED", file_top_verdict(merged)
            assert "UT-J-05" in merged
            # --required and --target may both be given at once (a real iteration passes both).
            out2 = f"{td}/out2.md"
            rc2 = main(["--required", "J-01", "--target", "J-05", out2, in1])
            assert rc2 == 0, rc2
            merged2 = Path(out2).read_text(encoding="utf-8")
            assert file_top_verdict(merged2) == "BLOCKED", file_top_verdict(merged2)
            assert "## Missing Target Journeys" in merged2 and "## Missing Required Journeys" not in merged2

    # ==============================================================================================
    # market-compass iter-34 (goal-mode harness fix, TC-7/TC-8) — a target/required journey whose
    # docs/goal.md Acceptance carries the literal `**Walkthrough:** waived` marker can be recorded
    # verified through a cited non-UI evidence row instead of being forced to BLOCKED for having no
    # browser row / only a SKIP row — STRICTLY scoped to journeys named in `waived_journeys`, and
    # ONLY when the row actually cites something (not a bare "none"/empty Evidence cell).
    # ==============================================================================================
    def t_parse_waived_journeys_from_text():
        goal_text = (
            "## Must-have user journeys\n"
            "- **J-01: Ordinary UI journey**\n"
            "  - Acceptance:\n"
            "    - **Walkthrough:** demo required.\n"
            "- **J-09: Backend-only journey (owner, 2026-08-20)**\n"
            "  - Acceptance:\n"
            "    - **Walkthrough:** waived — deliberately backend-only.\n"
            "- **J-10: Another marked journey**\n"
            "  - Acceptance:\n"
            "    - **Walkthrough:** waived — raw-layer repair.\n"
            "## Anti-goals\n"
            "- **AG-1:** unrelated section, must not be scanned as a journey.\n"
        )
        waived = parse_waived_journeys_from_text(goal_text)
        assert waived == {"J-09", "J-10"}, waived

    def t_has_cited_evidence():
        cited = {"cells": ["", "", "", "", "", "", "reports/perf-budgets.md#addendum-45"]}
        none_cell = {"cells": ["", "", "", "", "", "", "none"]}
        empty_cell = {"cells": ["", "", "", "", "", "", ""]}
        short_cells = {"cells": ["a"]}
        assert _has_cited_evidence(cited) is True
        assert _has_cited_evidence(none_cell) is False
        assert _has_cited_evidence(empty_cell) is False
        assert _has_cited_evidence(short_cells) is False

    def t_waived_target_with_cited_evidence_is_non_blocked():
        # TC-8a: a synthetic walkthrough-waived TARGET journey with a cited-evidence SKIP row must
        # merge to a non-BLOCKED headline — the row exists, it was never a UI check to fail, and it
        # names real evidence instead of "none".
        waived_row = (
            "**Browser QA Verdict:** SKIPPED\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-09 | Backend fits the host | smoke | P1 | N/A — waived | verified via "
            "Addendum 45 | SKIP | reports/perf-budgets.md#addendum-45 |\n")
        md = merge([waived_row], target_journeys=["J-09"], waived_journeys={"J-09"})
        assert file_top_verdict(md) != "BLOCKED", file_top_verdict(md)
        assert "## Missing Target Journeys" not in md
        assert verdict_for(md, "UT-J-09") == "SKIP", verdict_for(md, "UT-J-09")

    def t_waived_journey_without_evidence_still_blocks():
        # A waived journey's SKIP row with NO real citation (Evidence == "none") is NOT exempted —
        # the marker alone is never enough; a real citation is required.
        no_evidence_row = (
            "**Browser QA Verdict:** SKIPPED\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-09 | Backend fits the host | smoke | P1 | N/A — waived | no UI to check | "
            "SKIP | none |\n")
        md = merge([no_evidence_row], target_journeys=["J-09"], waived_journeys={"J-09"})
        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
        assert "## Missing Target Journeys" in md and "only a SKIP row for J-09" in md

    def t_placeholder_prose_evidence_still_blocks():
        # market-compass iter-34 AUDIT regression (finding B1): a waived journey's SKIP row whose
        # Evidence cell is a PLACEHOLDER followed by prose cites nothing and must still block. The
        # cell below is verbatim the one this iteration's own browser-qa lane wrote into
        # reports/phase-goal-market-compass-iter-34-ui-test-results.llm.md — it defeated the
        # original whole-cell equality check, and it also contains an incidental `docs/goal.md`
        # path, so the head-placeholder conjunct (not the citation-shape one) is what rejects it.
        real_world_cell = (
            'none (evidence-based journey — no UI acceptance state to screenshot, per this '
            'journey\'s own `docs/goal.md` "Walkthrough: waived" marker and the test plan\'s own '
            'framing)')
        assert _has_cited_evidence({"cells": ["", "", "", "", "", "", real_world_cell]}) is False
        # …and prose with no artifact reference at all is likewise not a citation.
        assert _has_cited_evidence({"cells": ["", "", "", "", "", "", "verified by measurement"]}) is False
        # A real citation still counts, in every shape this repo actually writes.
        for good in ("reports/perf-budgets.md#addendum-45",
                     "`reports/perf-budgets.md` Addendum 45; `runs/x/j09-samples.csv`",
                     "reports/qa/evidence/J-01-verify.png"):
            assert _has_cited_evidence({"cells": ["", "", "", "", "", "", good]}) is True, good
        row = (
            "**Browser QA Verdict:** SKIPPED\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            f"| UT-J-09 | Backend fits the host | smoke | P1 | N/A — waived | no UI to check | "
            f"SKIP | {real_world_cell} |\n")
        md = merge([row], target_journeys=["J-09"], waived_journeys={"J-09"})
        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)

    def t_unwaived_target_missing_or_skip_still_blocks():
        # TC-8b: a target/required journey WITHOUT the goal.md marker (not in waived_journeys),
        # missing or SKIP-only, must still force BLOCKED exactly as before this fix — the exemption
        # must never generalize into a "no browser row" loophole for an unmarked journey.
        md_missing = merge([clean_pair], target_journeys=["J-01", "J-05"], waived_journeys={"J-09"})
        assert file_top_verdict(md_missing) == "BLOCKED", file_top_verdict(md_missing)
        assert "## Missing Target Journeys" in md_missing and "UT-J-05" in md_missing

        skip_row_unwaived = (
            "**Browser QA Verdict:** SKIPPED\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-05 | Unwaived journey | regression | P1 | e | cites something real | SKIP | "
            "reports/some-report.md |\n")
        md_skip = merge([skip_row_unwaived], target_journeys=["J-05"], waived_journeys={"J-09"})
        assert file_top_verdict(md_skip) == "BLOCKED", file_top_verdict(md_skip)
        assert "only a SKIP row for J-05" in md_skip

    def t_waived_exemption_applies_to_required_too():
        # The same exemption, mirrored for Required-still-passing journeys (a waived journey can be
        # BOTH required-still-passing in a later iteration and this iteration's own target).
        waived_row = (
            "**Browser QA Verdict:** SKIPPED\n\n## Results Table\n"
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| UT-J-09 | Backend fits the host | smoke | P1 | N/A — waived | verified via "
            "Addendum 45 | SKIP | reports/perf-budgets.md#addendum-45 |\n")
        md = merge([waived_row], required_journeys=["J-09"], waived_journeys={"J-09"})
        assert file_top_verdict(md) != "BLOCKED", file_top_verdict(md)
        assert "## Missing Required Journeys" not in md

    def t_no_waived_journeys_arg_unchanged():
        # Default (no waived_journeys kwarg) is BYTE-IDENTICAL to passing an empty set — no
        # regression on every pre-iter-34 call shape.
        assert merge([clean_pair], target_journeys=["J-01"]) == merge(
            [clean_pair], target_journeys=["J-01"], waived_journeys=None
        )
        assert merge([clean_pair], target_journeys=["J-01"], waived_journeys=set()) == merge(
            [clean_pair], target_journeys=["J-01"]
        )

    # Self-counting list (local form) rather than a hardcoded total — upstream's void
    # tests and the local verdict-normalization tests both live here, so a literal
    # count goes stale on the next pull.
    checks = [("parse_rows", t_parse),
              ("later_wins_override", t_later_wins),
              ("real_fail_survives", t_real_fail_survives),
              ("skipped_only", t_skipped_only),
              ("bold_verdicts", t_bold_verdicts),
              ("annotated_verdicts", t_annotated_verdicts),
              ("verdict_for_tolerates_annotated_cells", t_verdict_for_tolerates_annotated_cells),
              ("tc_prefixed_fail_survives", t_tc_prefixed_fail_survives),
              ("blocked_all_headlines_blocked", t_blocked_all_headlines_blocked),
              ("fail_still_wins_over_blocked", t_fail_still_wins_over_blocked),
              ("void_rewrites_and_recomputes", t_void_rewrites_and_recomputes),
              ("void_keeps_unlisted_fail", t_void_keeps_unlisted_fail),
              ("void_no_match_is_noop", t_void_no_match_is_noop),
              ("void_respects_escaped_pipes", t_void_respects_escaped_pipes),
              ("missing_required_journey_blocks_clean_pass", t_missing_required_journey_blocks_clean_pass),
              ("missing_required_journey_blocks_clean_skipped", t_missing_required_journey_blocks_clean_skipped),
              ("all_skip_required_journeys_block_clean_skipped", t_all_skip_required_journeys_block_clean_skipped),
              ("mixed_skip_and_pass_blocks_only_on_the_skip", t_mixed_skip_and_pass_blocks_only_on_the_skip),
              ("all_required_present_stays_clean", t_all_required_present_stays_clean),
              ("no_required_journeys_arg_unchanged", t_no_required_journeys_arg_unchanged),
              ("missing_required_never_downgrades_fail_or_blocked", t_missing_required_never_downgrades_fail_or_blocked),
              ("missing_required_via_cli_required_flag", t_missing_required_via_cli_required_flag),
              ("missing_target_journey_blocks_clean_pass", t_missing_target_journey_blocks_clean_pass),
              ("all_skip_target_journeys_block_clean_skipped", t_all_skip_target_journeys_block_clean_skipped),
              ("target_and_required_guards_both_apply_independently", t_target_and_required_guards_both_apply_independently),
              ("all_target_present_stays_clean", t_all_target_present_stays_clean),
              ("no_target_journeys_arg_unchanged", t_no_target_journeys_arg_unchanged),
              ("missing_target_never_downgrades_fail_or_blocked", t_missing_target_never_downgrades_fail_or_blocked),
              ("missing_target_via_cli_target_flag", t_missing_target_via_cli_target_flag),
              ("parse_waived_journeys_from_text", t_parse_waived_journeys_from_text),
              ("has_cited_evidence", t_has_cited_evidence),
              ("waived_target_with_cited_evidence_is_non_blocked", t_waived_target_with_cited_evidence_is_non_blocked),
              ("waived_journey_without_evidence_still_blocks", t_waived_journey_without_evidence_still_blocks),
              ("placeholder_prose_evidence_still_blocks", t_placeholder_prose_evidence_still_blocks),
              ("unwaived_target_missing_or_skip_still_blocks", t_unwaived_target_missing_or_skip_still_blocks),
              ("waived_exemption_applies_to_required_too", t_waived_exemption_applies_to_required_too),
              ("no_waived_journeys_arg_unchanged", t_no_waived_journeys_arg_unchanged)]
    for name, fn in checks:
        check(name, fn)

    for f in failures:
        print(f"  FAIL {f}", file=sys.stderr)
    print(f"[merge_ui_test_results self-test] {len(checks) - len(failures)} passed, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
