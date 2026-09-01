# Iteration State — market-compass

**After iteration:** 35 · **Date:** 2026-09-01 · **Verdict:** CONTINUE

## Journeys

12 passing (J-01..J-12) · 1 failing (J-13) — 13 total. `goal_gate.py journeys` exits 1, `blocking: ["J-13"]`.

## Active blockers

- **J-13 "Leadership rotation"** (owner: dev) — never built; the ONLY thing blocking completion. Three
  defects I measured on `2026-08-12_v8.json` + `compass-leadership-rotation-section.tsx:38`: (a) line 38
  is a client-side `changes.filter(kind in {sector,theme,stock})` over an array with 0 market/breadth
  entries, so it duplicates all 17 What-changed rows; (b) entries carry unsigned `magnitude`, no `delta`,
  no `direction_word`; (c) NO `rotation` key, and sector = 5 shown + 24 suppressed = **29 of 31** ETFs.
- Non-blocking: `test_manifest_invariants.py:933` risk fixture `58.9` vs a `60.0` ceiling makes its
  "fails BOTH qualifiers" comment false (raise above 60.0); the two new `assert` guards at
  `compass.py:462`/`:689` should `raise`; `test_no_magic_numbers.py` red on 3 untouched files.

## Last 2 verdicts

- iter 35: CONTINUE — J-12 built and verified (37→0 mislabeled rows, 502+27+10=539), nothing frozen
  moved, but the goal GREW: J-13 landed 2026-09-01 unbuilt and I proved it fails.
- iter 34: GOAL_ACHIEVED — closed J-09 on two independent memory readings; superseded, because
  `docs/goal.md` gained J-12 and J-13 after that verdict.

## Do not redo

- **J-12 is CLOSED** — do NOT re-open `evaluate_selection`'s gating logic. Leadership is the sole gate;
  entry/risk are advisory. `config.yaml compass.selection.rule_version` is now `"v2"`.
- **Never mutate, relabel, re-hash or delete a stored manifest row or export file** (AG-12/AG-17).
  `2026-08-12` v5/v6/v7 keep their 37 mislabeled rows and `rule_version: "v1"`; the correction lives
  ONLY in v8. Verified byte-identical this round.
- **J-09 stays closed** — do not touch `warmup.py`/`prices.py`; Constraints (a)/(b)/(c) stay landed.
- **No threshold VALUE may change** (80.0 / 70.0 / 60.0) — AG-15; which checks GATE is now settled.
- **Evidence capture is never an iteration goal** — J-04's crop (17th round owed) and the 7 journeys
  owing a `[NEW]` walkthrough (J-02/03/05/06/07/08/12) ride as passengers or a `Depth: evidence` round.
- **Depth for the J-13 round is `full`** (shared `session_delta` producer feeds J-02/J-05/J-06/J-07;
  J-13 must prove What-changed unchanged; real UI for ux-regression). A drop to `lean` must be
  surfaced explicitly and marked unmet (`docs/goal.md:2607-2620`).
