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
    n_blocked = sum(1 for r in rows if r["verdict"] == "BLOCKED")
    total = len(rows)

    overall_line = f"**Overall:** {n_pass}/{total} journeys passed ({n_skip} skipped"
    overall_line += f", {n_blocked} blocked" if n_blocked else ""
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
              ("void_respects_escaped_pipes", t_void_respects_escaped_pipes)]
    for name, fn in checks:
        check(name, fn)

    for f in failures:
        print(f"  FAIL {f}", file=sys.stderr)
    print(f"[merge_ui_test_results self-test] {len(checks) - len(failures)} passed, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
