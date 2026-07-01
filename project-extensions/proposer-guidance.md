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

### 4.1 Pre-registered multi-horizon staging candidate set (goal-mcp-loop iter-10 — anti-data-mining keystone)

Part B Phase 1 opened the certification-engine aperture beyond the 20-day horizon. The exploration
iterates a **FIXED, PRE-REGISTERED** hypothesis set — a reasoned registry, **never** the full
`factor × horizon × decile` cross-product. Each member is a documented h20 screen survivor
re-registered at a **non-20** horizon (a genuine "beyond the 20-day horizon" hypothesis). This registry
is the single source of truth for the set (config-backed in `config.triad.candidates`, consumed VERBATIM
by `app.engine.triad_scan.explore_multi_horizon_staging`, which certifies each through the referee into
the INTERNAL `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` under the online-FDR economy). All
are decile 10, direction positive:

| # | Factor | Horizon | Rationale (economic) | Signal-less? |
|---|--------|---------|----------------------|--------------|
| 1 | `vcp_contraction` | h10 | Tight volatility contractions resolve into expansion; does the h20-proven edge already appear at a ~2-week hold? | yes — cleanest J-07 candidate |
| 2 | `vcp_contraction` | h60 | Does the post-contraction expansion edge persist/strengthen over a quarter? | yes |
| 3 | `rs_spy_3m` | h60 | 3-month RS leadership over a hold matched to the factor's own 3-month lookback (more natural than h20). | yes — the speculative member |
| 4 | `leadership_score` | h60 | The system's strongest signal (hit the p-floor at h20) probed longer — a high-probability ANCHOR that the machinery certifies a real edge end-to-end. | no — score column, already in `proven_signals` |

**iter-10 referee outcome (recorded in the staging ledger — read it, do not recompute):** #1 `vcp_contraction`
h10 **FAILED** out-of-sample (block-bootstrap `p ≈ 0.057` — the h20 edge does NOT appear at a 2-week hold).
#2–#4 **PASSED** at `p ≈ 0.0005`, all clearing even the strict canonical divisor-5 bar (`p < 0.010`).
For **iter-11's J-07 promotion**, prefer a **signal-less** winner (#2 `vcp_contraction` h60 or #3 `rs_spy_3m`
h60) so it backs the factor lab only and never a `/stocks` badge; #4 `leadership_score` is the score-column
fallback. Promotion MUST set `"ledger":"canonical"` explicitly in the `## Evidence Claim` (an omitted key
defaults to staging). **Do NOT re-propose** `vcp_contraction` h10 as a canonical claim — it failed the referee.
As with `ma_stack`/`hv`/`high_proximity` (iter-8), a documented referee failure is a closed hypothesis.

### 4.2 Pre-registered 2-factor combination staging candidate set (goal-mcp-loop iter-12 — anti-data-mining keystone)

Part B Phase 1's deferred **combinations** half opens the certification aperture to 2-factor **composite**
cohorts. As with §4.1, the exploration iterates a **FIXED, PRE-REGISTERED** hypothesis set — a reasoned
registry, **never** the full `factor × pair × horizon` cross-product. This registry is the single source of
truth for the set (config-backed in `config.triad.combination_candidates`, consumed VERBATIM by
`app.engine.triad_scan.explore_combination_staging`, which projects each into a
`{kind:"combination", cohort:"composite", horizon, direction, condition:[leg1, leg2]}` claim and certifies it
through the referee into the INTERNAL `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` under the
online-FDR economy). All are composite cohort, direction positive, **horizon 20** (the J-08 target hold).
Each `condition` leg is `<factor_key>:<side>:<quantile_key>` with `side` matching the factor's catalog
`direction` (top = higher_better, bottom = lower_better):

| # | Condition legs | Horizon | Rationale (economic) | Signal-less? |
|---|----------------|---------|----------------------|--------------|
| 1 | `rs_spy_3m:top:quintile` + `atr_pct:bottom:tertile` | h20 | Momentum leadership that is NOT volatile/extended — identical to the shipped `research.factor_lab.combination.default_conditions` and the J-08 example; both legs individually evidenced (rs_spy_3m PASSED strongly OOS at h60; low-ATR% is the risk-factor low-volatility/quality filter). | yes — signal-less composite, backs the combination lab only |
| 2 | `leadership_score:top:quintile` + `atr_pct:bottom:tertile` | h20 | The composite Leadership score concentrated to its low-volatility members; asks whether the system's strongest signal (p-floor solo) is even cleaner filtered to orderly, low-ATR names. | no — carries the `leadership_score` column |
| 3 | `rs_spy_3m:top:quintile` + `high_proximity:top:tertile` | h20 | Relative-strength leaders that are ALSO near their 52-week high (leaders in position / breakout-ready). | yes — signal-less composite |

**For iter-13's J-08 promotion:** read the recorded staging verdicts (do NOT recompute) and promote the
combination whose **raw block-bootstrap `p_value`** clears the canonical divisor-6 bar (`required_p ≈ 0.00833`)
with margin. The promotion `## Evidence Claim` MUST set `"ledger":"canonical"` explicitly (an omitted key
defaults to staging). If NONE of the three clears the bar with margin, honestly report it — the referee
refusing a thin/weak composite is anti-goal #1/#4 upheld, not a failure to engineer around; J-08 then needs
the human to widen/revise the pre-registered set. `ma_stack` is excluded from every leg (a closed referee
FAIL, iter-8).

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
