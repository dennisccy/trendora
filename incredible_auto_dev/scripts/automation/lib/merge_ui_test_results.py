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
  merge_ui_test_results.py self-test
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
_ROW_RE = re.compile(r"^\|\s*(UT-[^|]+?)\s*\|(.*)\|\s*$")


def _norm_verdict_cell(c: str) -> str:
    """Strip markdown emphasis/backticks so `**FAIL**`, `_PASS_`, `` `SKIP` ``
    normalize to the bare verdict word before matching."""
    return c.strip().strip("*_`~").strip().upper()
# Column order in the template (after the leading Test ID cell).
_C_NAME, _C_ACTUAL, _C_EVIDENCE = 0, 4, 6


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
            if cu in ("PASS", "FAIL", "SKIP", "SKIPPED"):
                verdict = "SKIP" if cu == "SKIPPED" else cu
                break
        if not verdict:
            # Fallback for ANNOTATED verdict cells ("PASS (with caveat)",
            # "FAIL (see note)") — scan in REVERSE so the verdict column (right of
            # the free-prose Actual column) wins over any prose that happens to
            # start with a verdict word. \b keeps "FAILED ..." prose non-matching.
            for c in reversed(cells):
                mv = re.match(r"(PASS|FAIL|SKIPPED|SKIP)\b", _norm_verdict_cell(c))
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


def compute_overall(rows: "list[dict]", file_verdicts: "list[str] | None" = None) -> str:
    """Overall verdict. Surviving rows are authoritative; only when NO rows could
    be parsed do we fall back to the input files' headline verdicts."""
    verdicts = [r["verdict"] for r in rows if r["verdict"]]
    if verdicts:
        if "FAIL" in verdicts:
            return "FAIL"
        if "PASS" in verdicts:
            return "PASS"
        return "SKIPPED"
    file_verdicts = file_verdicts or []
    if "FAIL" in file_verdicts:
        return "FAIL"
    if "PASS" in file_verdicts:
        return "PASS"
    return "SKIPPED"


def _cell(row: dict, i: int) -> str:
    cells = row["cells"]
    return cells[i] if i < len(cells) else ""


def merge(texts: "list[str]") -> str:
    """Merge in order; later inputs win per Test ID. Returns the merged markdown
    with a single authoritative headline verdict and detail rebuilt from the
    surviving rows (no verbatim per-lane embedding → exactly one verdict line)."""
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
    n_pass = sum(1 for r in rows if r["verdict"] == "PASS")
    n_skip = sum(1 for r in rows if r["verdict"] == "SKIP")
    total = len(rows)

    out = ["# UI Test Results (merged)", "",
           f"**Date:** {_today()}",
           "**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)",
           "", "---", "",
           f"**Browser QA Verdict:** {overall}", "",
           f"**Overall:** {n_pass}/{total} journeys passed ({n_skip} skipped)",
           "", "---", "", "## Results Table", "",
           "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |",
           "|---------|------|------|----------|----------|--------|---------|----------|"]
    for r in rows:
        out.append(r["raw"])
    out.append("")

    failed = [r for r in rows if r["verdict"] == "FAIL"]
    skipped = [r for r in rows if r["verdict"] == "SKIP"]
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
    out += ["## Environment", "",
            "- **Browser:** Chromium (LLM browser-qa + deterministic replay)",
            f"- **Test Date:** {_today()}", ""]
    return "\n".join(out) + "\n"


def main(argv: "list[str]") -> int:
    if argv and argv[0] in ("self-test", "--self-test"):
        return _self_test()
    if len(argv) < 2:
        sys.stderr.write("usage: merge_ui_test_results.py <out.md> <in1.md> [<in2.md> ...]\n")
        return 2
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
    out_path.write_text(merge(texts), encoding="utf-8")
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

    checks = [("parse_rows", t_parse),
              ("later_wins_override", t_later_wins),
              ("real_fail_survives", t_real_fail_survives),
              ("skipped_only", t_skipped_only),
              ("bold_verdicts", t_bold_verdicts),
              ("annotated_verdicts", t_annotated_verdicts)]
    for name, fn in checks:
        check(name, fn)

    for f in failures:
        print(f"  FAIL {f}", file=sys.stderr)
    print(f"[merge_ui_test_results self-test] {len(checks) - len(failures)} passed, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
