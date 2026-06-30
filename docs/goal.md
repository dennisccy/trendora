# Project Goal

> This goal drives the **decision-quality improvement loop** for Trendora. The original
> feature-complete product goal (GOAL_ACHIEVED) is archived at [`docs/goal-product.md`](goal-product.md)
> and remains the description of the underlying product. This file evolves Trendora from
> *"ranks the market with explainable scores"* to *"ranks the market AND proves, out-of-sample,
> which of its signals actually work — showing an honest evidence status on everything."*

## Vision

Trendora already produces explainable, regime-aware equity-leadership rankings (three independent
scores — Leadership, Entry Quality, Risk — plus market regime/phase and realized forward-return
evidence). The next evolution makes every signal **provable, not just explainable**: each score,
ranking, and "edge" the user sees carries a visible **evidence status** sourced from an append-only
**evidence ledger** of out-of-sample, control-beating, multiple-testing-corrected claims. Unvalidated
signals are shown as *"not yet proven"* — never as confident numbers. The platform improves itself by
mining its own data for candidate decision-support views and shipping only the ones a statistical
**referee** certifies. This is research-only decision support; it never predicts returns or places orders.

## Target Users

Self-directed, quant-minded swing/position traders who distrust black-box signals and want **hard,
out-of-sample evidence** before risking capital — now served not just explainable scores but provable
ones, with honest "this isn't proven yet" markers when the evidence is thin or fails.

## Success Criteria

- Every user-facing score / ranking / edge carries a **visible, accurate evidence status** ("proven" or
  "not yet proven") sourced from the evidence ledger — never a confident number without a status.
- A user can **audit the proof** behind any "proven" claim: the out-of-sample test, the control
  comparison (vs SPY / QQQ / sector ETF / random same-sector), and the certified-claim id + date.
- Failed or unvalidated signals are **explicitly flagged** as not proven, never shown as confident.
- Each successful iteration ships **at least one referee-certified** decision-support improvement, and
  **zero uncertified edges** reach the UI.
- Displayed numbers are **correct** (match the engine's computation for the same as-of date), not just
  rendered.

## Key Capabilities

1. **Evidence badges + drill-down** on every score/ranking surface — a "Proven / Not yet proven" badge
   inline, expanding to the backing out-of-sample test, controls, and certified-claim id/date.
2. **Evidence ledger surface** — an auditable list of certified claims (hypothesis, out-of-sample
   verdict, control comparison, registration date, forward-walk score-to-date).
3. **Regime-conditioned evidence** — decision-support conditioned on the current regime/phase, showing
   the out-of-sample evidence for *that* regime, labeled with the regime it applies to.
4. **Honest uncertainty / noise marking** — when evidence is thin or a pattern fails out-of-sample, the
   UI says so plainly instead of presenting a confident-looking number.
5. **Self-improving evidence loop** (internal) — each iteration proposes a decision-support improvement
   from the platform's own data and ships only referee-certified ones (enforced by the post-decompose gate).

## Non-Goals

- No return/price prediction, "buy/sell" signals, price targets, or alpha claims. Decision support only.
- No order placement, broker keys, or trade simulation.
- Not a rewrite — the evidence layer is **additive** to the existing surfaces (Dashboard, Stocks,
  Sectors, Themes, Backtest, Research labs, Data, Watchlist).

## Constraints

- Local-first, deterministic, offline against the committed seed; **strict no-lookahead** preserved
  (scoring uses bars ≤ as-of; forward returns use bars > as-of).
- **All "proven" status flows from the evidence ledger** as the single source of truth; the UI never
  computes proven-ness itself.
- A claim becomes "proven" only via the statistical **referee** (sealed holdout + controls +
  multiple-testing correction); the referee and ledger live in the project (read-only MCP "window" +
  `project-extensions/` gate), not in the shared framework.

## Design Direction

- Visual style: minimal, data-dense, evidence-first — consistent with the existing Trendora UI.
- Mood: skeptical, rigorous, honest. Evidence status is calm and unmissable, never hype.
- Reference: existing Trendora surfaces; badges read like a quiet "proven ✓ / not yet proven" chip.

## Product Shape

### Navigation / information architecture
- Existing nav unchanged: Dashboard | Stocks | Sectors | Themes | Backtest | Research | Data | Watchlist.
- **New: Evidence** (the ledger) added to the persistent nav, reachable in ≤2 clicks.
- Evidence badges appear **inline** on existing score surfaces (Stocks leaderboard, Stock detail,
  Sector/Theme leaderboards, research labs) — each badge links to its ledger entry.

### Canonical values (single source of truth)
- **Evidence status** and **certified-claim** for any (signal, as-of) — computed **once** by the referee,
  stored in the evidence ledger, and displayed identically everywhere a badge appears.
- The three scores (Leadership / Entry Quality / Risk), regime score, market phase, and realized
  forward-returns remain single-source from the existing engine (unchanged).

## Must-have user journeys

- **J-01: Every score shows an evidence status**
  - Steps:
    1. Visit `/stocks`
    2. Observe the leaderboard rows
    3. Assert each row's score area shows an evidence badge reading "Proven" or "Not yet proven"
    4. Assert at least one badge is present and none of the displayed scores lack a status
  - Acceptance: no score on the leaderboard is presented without a visible evidence status.

- **J-02: Drill into the proof behind a score**
  - Steps:
    1. From `/stocks`, click a stock to open `/stocks/{ticker}`
    2. Locate a score with a "Proven" badge and expand/click it
    3. Assert the panel shows: the out-of-sample test result, the control comparison
       (vs SPY/QQQ/sector ETF/random), and the certified-claim id + registration date
  - Acceptance: the user can see *why* a score is considered proven — the test, the controls, and the date.

- **J-03: Unproven / noise signals are honestly marked**
  - Steps:
    1. Find a score or edge whose claim has not been certified (or failed out-of-sample)
    2. Assert the UI shows "Not yet proven" (and, where applicable, "did not beat controls out-of-sample")
       rather than a confident-looking number
  - Acceptance: unvalidated or failed signals are visibly flagged and never presented as confident.

- **J-04: Regime-conditioned evidence**
  - Steps:
    1. Visit the Dashboard and note the current market regime/phase
    2. Open a research lab or the Evidence surface for a regime-conditioned claim
    3. Assert the evidence shown is scoped to and labeled with the regime it applies to
  - Acceptance: evidence is regime-scoped and clearly labeled with the regime it holds in.

- **J-05: Audit the evidence ledger**
  - Steps:
    1. Click "Evidence" in the nav
    2. Assert a list of certified claims renders, each with: hypothesis, out-of-sample verdict,
       control comparison, registration date, and forward-walk score-to-date
    3. Click a claim and assert it links back to the surface(s) whose badge it backs
  - Acceptance: the user can audit every "proven" claim the platform relies on, end to end.

<!-- Continuous-improvement auto-journeys: the goal-proposer appends NEW Must-have journeys ONLY
     between the two markers below (see the goal-self-extension skill). The human-authored journeys
     above and the Anti-goals below are never machine-edited. An empty block = nothing auto-proposed yet. -->
<!-- AUTO:journeys -->
<!-- /AUTO:journeys -->

## Anti-goals

- A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
  **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
  values MUST render a "not yet proven" state. *(critical)*
- **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
  claims; never place or simulate orders. *(critical)*
- A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
  for the same as-of date — not merely that the page renders. *(critical)*
- **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
  out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
- **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
  never introduce lookahead anywhere. *(critical)*
- No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the
  post-decompose gate. *(critical)*
- No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## Loop mechanics (for the iteration planner)

When an iteration's purpose is to ship a **data-derived** decision-support view — i.e. it presents a
score / ranking / edge as "proven" — the iteration spec MUST include a machine-readable **Evidence
Claim** so the post-decompose gate can certify the edge through the referee BEFORE any code is built.
Iterations that are pure UX / correctness / navigation work (no new "proven" claim) need NO Evidence
Claim and pass the gate automatically.

Write the claim as a fenced JSON block under a `## Evidence Claim` heading, using the same cohort
selectors the Research labs use (mirrors `/api/research/samples`):

```json
{"kind": "factor", "factor": "<factor-key>", "slice_kind": "decile", "decile": 10, "horizon": 20, "direction": "positive"}
```

- `kind`: `factor` | `event-study` | `regime-setup-pattern` | … (a Research-lab cohort)
- selectors: the cohort slice (factor + `decile`/`regime`, or `subject`/`setup`), exactly as in the labs
- `horizon`: forward-return horizon in trading days; `direction`: `positive` | `negative`

The gate runs the referee — a **sealed out-of-sample holdout** + an **SPY control** + **multiple-testing
deflation** (the bar tightens with every claim ever tested) — and appends the verdict to the
certified-claims ledger at `runs/goal-session-<sid>/state/certified-claims.jsonl`. A non-PASS verdict
(`FAIL` or `INSUFFICIENT`) **blocks** the iteration. So propose only an Evidence Claim you have reason to
believe survives out-of-sample, and prefer **narrow, regime-conditioned** cohorts over broad,
data-mined ones — the referee counts independent holdout *dates*, not correlated same-date names, and
will refuse to certify on a sample too thin to believe.
