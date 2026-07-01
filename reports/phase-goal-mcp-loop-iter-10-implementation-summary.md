# goal-mcp-loop-iter-10 — Implementation Summary

**Phase:** goal-mcp-loop-iter-10
**Date:** 2026-07-01
**Written by:** developer

---

## Features Implemented

This iteration is **internal research machinery** — it changes nothing a user can see. Its job was to
let Trendora's "referee" (the statistical judge that decides whether a signal is genuinely proven)
look for edges at **more time horizons than just 20 trading days**, and to record what it found in a
private "staging" notebook that the next iteration will act on.

- **Wider horizon search:** the engine's internal scan can now evaluate factor cohorts at forward
  horizons of **1, 5, 10, 20, and 60 trading days** (previously only 20). Nothing new is shown yet —
  this simply opens the field of view.
- **A short, pre-approved list of hypotheses to test:** rather than testing every possible
  combination (which invites false positives), the iteration tests a **fixed, reasoned list of four**
  factor/horizon ideas, each written down with a one-line economic reason. The list lives in config and
  is mirrored into the analyst-guidance document.
- **A "staging" evidence run:** each of the four ideas was put through the full referee and the honest
  verdict (pass / fail / not-enough-data, with its out-of-sample statistics) was saved to an internal
  staging file — **never** to the user-facing evidence ledger.
- **A sustainable "trial budget" was switched on for staging:** the referee's staging notebook now uses
  a smarter statistical accounting method (online false-discovery control) so that finding a real edge
  earns back capacity to test more — keeping a wide search feasible. This is **fenced to staging only**;
  the user-facing "Proven" badge keeps its stricter guarantee unchanged.

### What the referee found (the point of the iteration)

| Idea (top-decile, "goes up") | Horizon | Verdict | Strong enough to promote? |
|------------------------------|---------|---------|---------------------------|
| Volatility-contraction (VCP) | 10 days | **Did not hold up** out-of-sample | No |
| Volatility-contraction (VCP) | 60 days | **Passed** strongly | **Yes** |
| Relative strength vs SPY (3-month) | 60 days | **Passed** strongly | **Yes** |
| Leadership score | 60 days | **Passed** strongly | Yes (but it's an existing "score" signal) |

Three of the four ideas cleared even the strictest bar. The next iteration will take one of the two
"pure" ones (VCP-60 or relative-strength-60) and actually surface it as a "Proven" badge with a longer
horizon — the first evidence Trendora shows beyond the 20-day window.

---

## Changed Behavior

- **Internal triad scan horizons:** the analyst-loop scan (`scan_product_triad`, an internal/MCP tool,
  not a user page) previously evaluated only the 20-day horizon; it now evaluates all five configured
  horizons and applies a steeper multiple-testing haircut proportional to the wider search. No
  user-facing output depends on this scan.
- **Everything users see is unchanged.** The Dashboard, Stocks, Sectors, Themes, Backtest, Research
  labs, Data, Watchlist, and the Evidence ledger all render byte-for-byte identically. The "Proven"
  badges and their proofs are unchanged.

---

## Backend-Only Items

- `explore_multi_horizon_staging` (in `app.engine.triad_scan`) — runs the pre-registered candidate set
  through the referee into the internal staging ledger. Internal machinery; no UI wiring (by design).
- `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` — the internal record of the four verdicts.
  Never served by the API, never displayed. It is the input the next iteration reads.

---

## Incomplete Items

- **Surfacing the discovered edge (journey J-07)** is intentionally deferred to iteration 11. This
  iteration is discovery-only; it deliberately builds no UI and flips no journey to "passing". An
  absent J-07 badge is expected, not a gap.

---

## Config and Environment Changes

- `evidence.fdr.enabled` — turned **on** (`true`). Activates the online false-discovery economy, but
  **only** for the internal staging ledger; the user-facing evidence bar stays strict and unchanged.
- `triad.horizons` — new: `[1, 5, 10, 20, 60]` (the horizons the internal scan evaluates).
- `triad.top_k` — raised `20` → `50`; `triad.screen.haircut_coef` — raised `0.001` → `0.0025` (scale
  the internal scan's multiple-testing haircut to the wider field). These affect only the internal
  proposer scan, not the staged evidence verdicts.
- `triad.candidates` — new: the fixed, pre-registered list of four factor/horizon hypotheses (each with
  an economic rationale).
- No database migration. No new environment variable. No secrets.

---

## Known Limitations

- The staged verdicts are computed against the full daily market database (`trendora.db`, ~1,377 daily
  snapshots) — the same database the user-facing evidence ledger was built against. The lightweight
  quarterly test fixture is too sparse to reproduce these specific numbers, so the staging file is
  committed as a frozen, reproducible artifact (regenerated deterministically from the daily database)
  and validated by a golden test. This mirrors how the existing certified-claims ledger is handled.
- The staging economy (online false-discovery control) is statistically **weaker** than the strict
  family-wise guarantee behind the user-facing "Proven" badge. That is by design and is the reason it
  is fenced to the internal staging ledger and never touches the badge. The next iteration promotes a
  staged winner to the user-facing ledger only through the strict bar.
