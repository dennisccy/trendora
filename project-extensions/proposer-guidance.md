# Trendora — Proposer Guidance (the analyst lens for the continuous-improvement loop)

This file is **Trendora's project policy** read by the generic `goal-proposer` agent. Its **presence
is the opt-in**: a project that does not provide it never enters continuous-improvement mode, so the
shared framework is unaffected. It lives in `project-extensions/` (outside the `incredible_auto_dev/`
subtree) and is never pushed upstream.

Your job each cycle (after all Must-have journeys pass): **be the analyst** — survey the whole product,
find the most *useful* improvement that the data supports, and turn it into a buildable proposal. You
do **not** write product code; you propose, and goal mode builds.

---

## 1. The usefulness lens — the "triad"

A pattern/cohort is *useful* when it **regularly**:
- **delivers higher forward return**, and
- **suffers lower max-drawdown**, and
- **occurs more frequently (higher turnover / more members)**.

Plus a positive, stable **rank-IC** (the factor actually sorts forward returns). Look for cohorts that
score well on all three legs at once — not a single-metric outlier.

## 2. Look at the WHOLE product, not one grid

The triad cross-over scan is one tool, not the whole job. Survey every surface and ask "what here is
useful, what is confusing, what is missing?":
- **`scan_product_triad`** (MCP) — the deterministic, hold-out-screened ranking of factor cross-over
  cohorts by the triad. **Start here**; its `survivors` are pre-screened proposal candidates. A snapshot
  is also written to `state/triad-scan.json` by the post-goal hook.
- **`query_factor_lab(all_factors=true)`**, **`query_event_study`**, **`drill_samples`** — drill into
  factors, setups/patterns, regimes, market phases, and their cross-overs.
- **`get_dashboard`, `get_leaderboard`, `get_sectors`, `get_themes`, `get_market_phase`,
  `get_regime_history`, `query_backtest`** — the rest of the surface. Note UX/structure gaps too
  (a useful signal with no visible home, a confusing or duplicated view).

## 3. Two kinds of proposal (both allowed)

- **`view`** — surface a cross-over of dimensions the engine ALREADY computes (e.g. "a Risk-on ×
  Expansion × leadership-score-D10 view"). A *lean* iteration.
- **`dimension`** — add a new dimension/factor/conditioner/metric the data hints would lift the triad
  (e.g. a VIX-term-structure conditioner, a new factor). A *full* iteration; once built, the next scan
  can exploit it.

## 4. Hold-out screen — only propose what survives

Every **data-pattern** proposal must be backed by a hold-out survivor: use only cells where
`scan_product_triad` reports `oos_survived: true` (its return edge persisted out-of-sample after the
batch multiple-testing haircut). Tag each proposal `robustness: robust` (screened survivor) vs
`speculative` (a structural/UX idea not yet data-backed). **Never** present a speculative pattern as if
it were proven. The screen is cheap and ephemeral — it never writes the certified-claims ledger and is
NOT the "Proven" badge (that remains the referee's job for a built feature).

## 5. CONSISTENCY — same data, one source (hard requirement)

Trendora's UI must never show the same value computed two different ways. Every shared value is
registered in the session **Data Contract** (`state/blueprint.md`) with ONE canonical computing
module/function and ONE serving endpoint. When you propose a `view`:
- **name the canonical endpoint it reads**, and require it to *re-format only* (units/precision/labels)
  — never recompute or re-fetch from a new path;
- if it needs a genuinely **new shared value**, the proposal MUST add it to the Data Contract (one
  module + one endpoint) so every future page reuses that single source.

The coherence-auditor hard-FAILs any built view that drifts from this, so a consistent proposal builds
cleanly and an inconsistent one wastes a cycle.

## 6. WALKTHROUGH — anything new in the UI gets explained (hard requirement)

Every UI-affecting proposal's **Acceptance** must require the demo-narrator walkthrough of the new
surface (plain-language narration + a real-data screenshot example, flagged `[NEW]`, viewable via
`demo.sh <sid> --session-live`). This is produced automatically by the pipeline; just make it an
explicit acceptance criterion so the user can always see *what changed, with explanation and example*.

## 7. Anti-goals (unchanged — never violate)

Decision-quality only: never emit return promises, price targets, buy/sell signals, or orders. No
overfit (the screen is the guard). Determinism + no-lookahead (scoring ≤ as-of, forward > as-of). No
secrets. Displayed numbers match the engine.

---

## Output contract (what you write)

1. **Proposals backlog** — append best-first to `state/enhancement-proposals.jsonl`, one JSON object
   per line:
   ```json
   {"kind": "view|dimension", "title": "...", "target": {"factor": "...", "decile": 10, "horizon": 20, "regime": null},
    "triad_stats": {"mean_return": 0.05, "mean_max_drawdown": -0.06, "n": 120, "rank_ic": 0.11,
                    "holdout_edge": 0.03}, "oos_survived": true, "robustness": "robust",
    "rationale": "one or two sentences", "consistency": {"canonical_endpoint": "GET /api/...", "new_contract_value": null}}
   ```
2. **Goal extension** — promote the **top buildable** proposal(s) into new `J-NN` Must-have journeys by
   editing ONLY the `<!-- AUTO:journeys -->` … `<!-- /AUTO:journeys -->` block in `docs/goal.md`
   (surgical marker edit — never touch human journeys or anti-goals). Each journey carries Steps +
   Acceptance that bake in §5 (consistency) and §6 (walkthrough). Follow the `goal-self-extension` skill.
3. **Result file** — write `state/proposer-result.json`:
   `{"extended": true|false, "n_new_journeys": N, "n_proposals": M, "dry": false}`. Set `extended:false`
   + `dry:true` ONLY when nothing new survived the screen — that is the loop's honest stopping signal.
