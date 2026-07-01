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

- **J-07: Multi-horizon certified edge surfaced (the loop sees beyond the 20-day horizon)**
  - Steps:
    1. The iteration carries a machine-readable `## Evidence Claim` for a factor cohort at a
       NON-20 forward-return horizon (1/5/10/60) — e.g.
       `{"kind":"factor","factor":"<key>","slice_kind":"decile","decile":10,"horizon":60,"direction":"positive"}` —
       that the post-decompose gate certifies through the referee BEFORE any code is built
       (a non-PASS verdict blocks the iteration).
    2. Visit `/evidence` and locate the new certified-claim row; assert its horizon is the
       non-20 value and it renders the standard fields (hypothesis incl. horizon, out-of-sample
       verdict, SPY control, registration date, forward-walk score-to-date, "Backs: Research
       factor lab →").
    3. Open `/research/factor-lab` for that factor; assert its cohort at that horizon shows a
       "Proven" badge linking to this ledger entry, while uncertified horizons read "Not yet proven".
  - Acceptance:
    - **Consistency (single source):** the row + factor-lab badge read the canonical
      `GET /api/evidence` payload verbatim; the claim is a NEW entry in the EXISTING
      `certified-claims.jsonl` (no new computing module, no new serving endpoint).
    - **Correctness:** displayed edge / p-value / control byte-match the referee verdict for
      the same as-of — never a UI recompute.
    - **Honest status / anti-goals:** a signal-less factor claim backs ONLY the factor lab,
      never a `/stocks` inline badge (J-01/J-02/J-03 unaffected); "Proven" only with a PASS,
      else "Not yet proven" (anti-goal #1); no return/price/buy-sell language; determinism +
      no-lookahead preserved (scoring ≤ as-of, forward returns > as-of; sealed temporal holdout).
    - **Walkthrough:** a `[NEW]`-flagged demo-narrator walkthrough of the multi-horizon row +
      badge, viewable via `demo.sh mcp-loop --session-live`.

- **J-08: Multi-factor combination certified edge surfaced on the Combination lab + Evidence**
  - Steps:
    1. The iteration carries a `## Evidence Claim` for a curated 2-factor composite cohort drawn
       from the pre-registered combination candidate set — e.g.
       `{"kind":"combination","cohort":"composite","horizon":20,"direction":"positive","condition":["rs_spy_3m:top:quintile","atr_pct:bottom:tertile"]}` —
       certified by the gate BEFORE any code is built (a non-PASS verdict blocks the iteration).
    2. Visit `/evidence`, locate the new combination certified-claim row, and assert the standard
       fields plus a "Backs: Multi-factor combination lab →" linkback.
    3. Open `/research/factor-combination`, reproduce/select that combination, and assert its
       composite cohort shows a "Proven" badge linking to this ledger entry; uncertified
       combinations read "Not yet proven".
  - Acceptance: same Consistency / Correctness / Honest-status / Walkthrough bar as J-07
    (canonical `GET /api/evidence` single source; byte-match; signal-less ⇒ no `/stocks` badge;
    PASS-gated; no return/price/buy-sell; deterministic; `[NEW]` walkthrough). The combination
    MUST come from the pre-registered candidate set — never an ad-hoc data-mined cohort.

<!-- Continuous-improvement auto-journeys: the goal-proposer appends NEW Must-have journeys ONLY
     between the two markers below (see the goal-self-extension skill). The human-authored journeys
     above and the Anti-goals below are never machine-edited. An empty block = nothing auto-proposed yet. -->
<!-- AUTO:journeys -->

- **J-06: vcp_contraction top-decile certified edge surfaced on Evidence + Research factor lab**
  - Steps:
    1. The iteration carries a machine-readable `## Evidence Claim` for the vcp_contraction top-decile cohort —
       `{"kind":"factor","factor":"vcp_contraction","slice_kind":"decile","decile":10,"horizon":20,"direction":"positive"}` —
       so the post-decompose gate certifies it through the referee (sealed out-of-sample holdout + SPY
       control + multiple-testing deflation) BEFORE any code is built; a non-PASS verdict (FAIL/INSUFFICIENT)
       blocks the iteration.
    2. Visit `/evidence` and locate the new vcp_contraction certified-claim row.
    3. Assert it renders the same fields as the existing claim rows: hypothesis, out-of-sample verdict,
       control comparison (vs SPY), registration date, forward-walk score-to-date, and a
       "Backs: Research factor lab →" linkback.
    4. Open the Research factor lab (`/research/factor-lab`) for the vcp_contraction factor and assert its
       top-decile cohort shows an evidence badge reading "Proven" that links to this ledger entry.
  - Acceptance:
    - **Consistency (single source):** the vcp_contraction ledger row and the factor-lab badge read the canonical
      `GET /api/evidence` payload verbatim (the ledger row re-displays `claims[]`; the badge looks up the
      resolved evidence status — it NEVER recomputes proven-ness or re-fetches from a new path). The vcp_contraction
      certified-claim is a NEW entry in the EXISTING `certified-claims.jsonl` ledger already served by
      `GET /api/evidence` — **no new computing module and no new serving endpoint** are introduced (same
      evidence-status contract value, one additional reader), so the Data Contract's single source of truth
      is preserved (no new shared value to register).
    - **Correctness:** the displayed out-of-sample edge, p-value, and control comparison byte-match the
      referee verdict written to `certified-claims.jsonl` for the same as-of — never a recompute in the UI.
    - **Honest status / anti-goals:** like the Breakout-watch setup claim, the vcp_contraction factor claim carries
      NO per-stock `signal`, so it backs ONLY the Research factor lab and never lights or overwrites a
      `/stocks` inline score badge (J-01/J-02/J-03 unaffected). The factor-lab cohort reads "Proven" ONLY
      because a PASS certified-claim backs it; absent a PASS verdict it must read "Not yet proven"
      (anti-goal #1 upheld). No return promise, price target, or buy/sell signal is shown — only the evidence
      status plus the realized hold-out statistic. Determinism + no-lookahead preserved (scoring ≤ as-of,
      forward returns > as-of; the referee uses a sealed temporal holdout).
    - **Walkthrough:** a `[NEW]`-flagged demo-narrator walkthrough of the new vcp_contraction ledger row and the
      factor-lab "Proven" badge is produced (plain-language narration + a real-data screenshot example),
      viewable via `demo.sh mcp-loop --session-live`.

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

> **Sustaining an open-ended search:** the single global Bonferroni bar above is what the
> "Improvement direction (engineering)" section below replaces for *exploration*. Per-iteration
> Evidence Claims default to a separate **staging** ledger under an online-FDR economy; the
> user-facing `/evidence` ledger (`certified-claims.jsonl`) stays strict Bonferroni and receives
> only deliberately promoted winners (`"ledger":"canonical"`). Build that economy BEFORE widening
> the scan, so the wider aperture has a sustainable economy to run in.

## Improvement direction (engineering): open the aperture + sustainable trial economy

The continuous-improvement loop converged because the discovery machinery is structurally narrow,
not because real edges are exhausted. Two coupled upgrades — **build the economy first, then widen
the scan**. (Richer engineering notes were drafted in a planning doc; everything needed is inlined
here.)

**Why it stalled.** (1) The scan enumerates only `factor × horizon-20 × deciles{1,10}` (~22 cells,
SPY control only) in `app/engine/triad_scan.py` `scan_factor_decile_cells`, while the cohort/cert
path already supports horizons 1–60, regime/sector slices, and multi-factor combinations, against a
dense ~1,377-date snapshot. (2) The referee uses one global Bonferroni counter that never resets and
counts failures (`app/engine/referee.py` `certify_edge`; `app/engine/ledger.py` `count_trials`), so
every probe permanently tightens the bar (now `0.05/5 = 0.010`) and a single FAIL is permanent.

**A) Sustainable trial economy (hybrid — build this FIRST).** Add online-FDR (LORD++) as an
*injectable, default-off* deflation policy in the referee, running in a SEPARATE **staging** ledger
where a discovery replenishes testing capacity (so a wide search keeps finding edges). The canonical
`certified-claims.jsonl` served to `/evidence` stays STRICT Bonferroni and receives only deliberately
promoted winners — its "Proven" badge keeps its current family-wise guarantee. FDR is OFF by default
(config); exploration is isolated; the honesty guards (out-of-sample-beats-control gate, block
bootstrap, Thresholdout overfit charge) stay independent of the economy. Seams: new PURE
`app/engine/online_fdr.py` (no RNG/IO, wealth derived from rejection times — zero migration);
`RefereeState.test_level` + `deflation` (default-preserving, so every existing referee test stays
byte-identical); `ledger.rejection_offsets` (derived, no schema change → live ledger `[1,2,4]`);
`verify_edge` threads the economy (stays the ONLY ledger writer); `forward_walk` reproduce-contract
preserved by reconstructing `test_level` from the recorded `required_p`; `EvidenceCfg` typed `FdrCfg`
(defaults reproduce today) + `staging_ledger_path` in `config.yaml`; gate routing in
`project-extensions/gates/verify_claim.py` reads an optional `"ledger"` key per Evidence Claim
(default `"staging"`, explicit `"canonical"` for winners) with `exit 3`-on-non-PASS blocking
unchanged; `run-goal.sh` exports `STAGING_LEDGER_PATH` alongside `LEDGER_PATH`. The 4 existing
canonical entries stay byte-identical (`deflation="bonferroni"`, divisors 1–4 — honest history).

**B) Open the scan aperture (after A). Phase 1:** multi-horizon (config-only:
`config.yaml` triad `horizons: [1,5,10,20,60]`, reuses `compute_factor_lab`) + curated 2-factor
combinations (reuse `compute_factor_combination`; emit the `condition`-string claim form parsed by
`drill_samples`; combination enumerator + selector translation in `triad_scan.py`). Raise
`triad.top_k` (only `ranked[:top_k]` are screened) and the currently-inert `triad.screen.haircut_coef`
so the multiple-testing haircut scales with the wider aperture. A PRE-REGISTERED, config-backed
candidate set — each pair/horizon carrying a one-line economic rationale, mirrored into
`project-extensions/proposer-guidance.md` — is the anti-data-mining keystone: iterate a fixed
hypothesis set, NEVER the full cross-product. Deferred to later phases (NOT this direction):
quantile spreads (D10−D1), regime conditioning (reuse the `regime-phase-factor` kind first), sector
cohorts (event-study sector slice), scoped α-split families.

**Honesty constraint (anti-goal #1 upheld):** FDR controls the false-discovery *rate* and is weaker
than family-wise control — it runs ONLY in staging; the user-facing `/evidence` "Proven" badge stays
Bonferroni-curated. Every verdict records its `deflation` + `required_p` for audit. No unbacked or
overfit edge is ever shown as proven.
