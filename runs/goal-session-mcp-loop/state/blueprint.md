# App Blueprint — mcp-loop (Trendora · decision-quality evidence layer)

<!--
Coherence contract for the whole app. Drafted by the goal-decomposer at baseline; auto-approved by
default (pass --require-blueprint-approval to review/edit first); enforced by the coherence-auditor
every iteration.

WHAT THIS SESSION IS. It continues the same Trendora codebase a prior session built to GOAL_ACHIEVED
(explainable, regime-aware equity-leadership rankings: Leadership / Entry Quality / Risk scores, market
regime/phase, realized forward-return evidence, Research labs, Backtest, Data Manager). This session's
`docs/goal.md` evolves it from "explainable" to "PROVABLE": every user-facing score/ranking/edge gains a
visible EVIDENCE STATUS ("Proven" / "Not yet proven") sourced from an append-only certified-claims
LEDGER, with a referee that certifies edges out-of-sample before they may ship. FIVE new Must-haves
J-01..J-05 (plus auto-proposed J-06). The evidence layer is ADDITIVE — it never rewrites the existing
scoring/regime/research engines, only attaches a status + drill-down to what they already serve.

BASELINE FILE-SCAN (what already exists vs. what J-01..J-05 still need):
  EXISTS — the referee + ledger PLUMBING (not yet surfaced):
    • app.engine.referee  (PURE: sealed temporal holdout + block-bootstrap p + Bonferroni/Thresholdout
      multiple-testing deflation; certify_edge)
    • app.engine.ledger   (append-only certified-claims JSONL: append_entry / read_entries)
    • app.mcp.tools:verify_edge + app.mcp.server  (the read-only "window"; verify_edge is the ONLY writer,
      and writes ONLY the ledger)
    • project-extensions/gates/{post-decompose.sh,verify_claim.py}  (post-decompose gate: certifies any
      iteration's "## Evidence Claim" through the referee BEFORE code is built; non-PASS blocks)
  MISSING — the user-facing evidence SURFACE (this is what J-01..J-05 build):
    • no certified-claims ledger file yet (runs/goal-session-mcp-loop/state/certified-claims.jsonl absent
      ⇒ EMPTY ledger ⇒ every signal must currently render "Not yet proven")
    • no read-side evidence-status resolver / GET /api/evidence endpoint  [iter-1: building]
    • no "Proven / Not yet proven" badge component, none inline on any score surface  [iter-1: building]
    • no /evidence ledger page, not in the sidebar nav  [iter-1: building]
  ⇒ Expect J-01..J-05 to FAIL at baseline; iter-0 only records the starting line.

Rows tagged [built] carry REAL verified names; [TARGET] rows are the convention iter-1+ builds to —
rename here if you prefer. KEEP THIS FILE ~one screen; reviewable in ~3 minutes.
-->

## Information Architecture

**Layout shell:** left sidebar nav (`components/sidebar.tsx`) + main content; a persistent top bar with
the single global as-of switcher / calendar popover. The evidence layer adds ONE nav section and INLINE
badges on existing surfaces — no shell rewrite.

**Navigation skeleton** (the persistent sidebar — every feature lives under one of these):

```
Trendora
├── Dashboard            /                 market regime/phase, major indexes, candidate counts
├── Stocks               /stocks           leaderboard (Leadership/Entry/Risk) → Stock Detail /stocks/{ticker}
├── Themes               /themes
├── Sectors              /sectors
├── Scanner Runs         /scanner-runs     → Run Detail /scanner-runs/{runId}
├── Backtest             /backtest         walk-forward forward-tested evidence aggregate
├── Research             /research         labs (factor, event-study, regime, …) → Samples /research/samples
├── Evidence  [NEW]      /evidence         the certified-claims ledger (J-05 home)
├── Watchlist            /watchlist
├── Methodology          /methodology
└── Data Manager         /data
```

`[NEW] Evidence` is the only new top-level nav section this session (sanctioned by goal.md Product Shape:
"New: Evidence (the ledger) added to the persistent nav, reachable in ≤2 clicks"). Proposed slot: after
Research (its proof companion). Stock Detail, Run Detail, Research labs and Samples stay row/link-reached.

**Feature / journey homes** (each reachable in ≤2 clicks from the nav):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 every score shows an evidence status (inline badge) | `/stocks` (leaderboard rows) | Stocks |
| J-02 drill into the proof behind a score | `/stocks/{ticker}` (badge → proof panel) | Stocks → Stock Detail (row-reached) |
| J-03 unproven / noise signals honestly marked | cross-cutting badge state on `/stocks`, `/stocks/{ticker}`, `/sectors`, `/themes`, research labs | Stocks / Sectors / Themes / Research |
| J-04 regime-conditioned evidence | `/` (current regime + Evidence affordance) + regime-labeled claim row on `/evidence` | Dashboard + Evidence/Research |
| J-05 audit the evidence ledger | `/evidence` (claims list; each links back to the surface it backs) | Evidence [NEW] |
| J-06 vcp_contraction top-decile certified factor edge | `/research/factor-lab` (vcp_contraction top-decile "Proven" badge → its ledger row) + vcp_contraction claim row on `/evidence` | Research (lab, link-reached) + Evidence |
| J-07 multi-horizon (NON-20) certified factor edge | `/research/factor-lab` (the factor's non-20-horizon cohort "Proven" badge → its ledger row) + non-20-horizon claim row on `/evidence` | Research (lab, link-reached) + Evidence |
| J-08 multi-factor combination certified edge | `/research/factor-combination` (the composite cohort "Proven" badge → its ledger row) + combination claim row on `/evidence` | Research (lab, link-reached) + Evidence |
| J-09 rs_spy_3m top-decile 60-day-horizon certified factor edge | `/research/factor-lab` (the rs_spy_3m h60 cohort "Proven" badge → its ledger row) + rs_spy_3m h60 claim row on `/evidence` | Research (lab, link-reached) + Evidence |
| J-10 deep ~30-year honestly-bounded price history | `/stocks/{ticker}` (price chart / history window) + `/backtest` (as-of window) | Stocks → Stock Detail (row-reached) + Backtest |
| J-11 every "Proven" edge re-certified on the 30-year basis (sanctioned ledger reset) | `/evidence` (the regenerated ledger) | Evidence [NEW] |
| J-12 broad point-in-time dynamic universe (entries at real IPO, clean exits) | `/methodology` (Universe Selection + membership timeline) + `/stocks` (membership counts) | Methodology + Stocks |
| J-13 Data Manager reflects the 548 pool + unambiguous availability legend | `/data` | Data Manager |
| J-14 deep, vendor-labeled index/macro context on the 30y basis (benchmarks + coherent macro proxies) | `/` (Dashboard — major-indexes & regime card) + `/data` (vendor/macro disclosure) | Dashboard + Data Manager |

Evidence badges are INLINE chips on existing score surfaces (not new pages); each badge links to its
backing ledger entry on `/evidence`. No existing journey's home moves. J-07/J-08 reuse the EXISTING
`/research/factor-lab` and `/research/factor-combination` routes (both already present) + the EXISTING
`/evidence` ledger — no new page, no nav-skeleton change.

## Data Contract

Every value that appears in the UI and must read the same everywhere is registered with ONE canonical
computing source and ONE serving endpoint. No page recomputes or re-fetches these elsewhere; the UI only
re-formats what the canonical endpoint returns. **The evidence ledger is the SINGLE SOURCE OF TRUTH for
proven-ness — the UI never computes proven-ness itself** (goal.md Constraints).

| Value / entity | Computed once by (single module/function) | Served by (single endpoint) | Status / notes |
|---|---|---|---|
| **Evidence status + certified-claim** for any (signal, as-of) — "Proven" / "Not yet proven" + backing test, controls, claim id + registration date | referee `app.engine.referee:certify_edge` (WRITES verdicts) via `app.mcp.tools:verify_edge`; read-side resolver `app.engine.evidence:build_evidence_payload` over `app.engine.ledger:read_entries(certified-claims.jsonl)` | `GET /api/evidence` → `{claims:[…], proven_signals:{<signal>:…}}` (the SINGLE endpoint; the UI re-displays it verbatim) | **[building iter-1]** ledger file = `runs/goal-session-mcp-loop/state/certified-claims.jsonl`, resolved by `evidence.resolve_ledger_path()` from config `evidence.ledger_path` (env `TRENDORA_LEDGER_PATH` overrides) — the SAME file the post-decompose gate writes. MISSING ledger ⇒ EMPTY ⇒ every signal "Not yet proven". A signal is "Proven" ONLY when a PASS certified-claim entry NAMES it (`claim.signal`); absent ⇒ "Not yet proven" (fail-safe). The `EvidenceStatusBadge` (NOT `evidence-panels.tsx`, which is the Backtest aggregate) LOOKS UP `proven_signals` — it never computes status. |
| Three per-stock scores: Leadership / Entry Quality / Risk (+ components) | `scoring:score_stocks` | `GET /api/stocks`, `GET /api/stocks/{ticker}` | **[built — UNCHANGED]** evidence badge attaches additively; served scores byte-identical. |
| Market regime score (0–100) + label + market phase | `regime:score_regime` | `GET /api/dashboard`, `GET /api/runs/{runId}` | **[built — UNCHANGED]** the regime J-04 evidence is conditioned on, never recomputed. |
| Sector / industry score (+RS-vs-SPY, dist-52w, trend) | `sectors:score_sector` | `GET /api/sectors` | **[built — UNCHANGED]** badge attaches additively. |
| Theme score | `themes:score_themes` | `GET /api/themes` | **[built — UNCHANGED]** badge attaches additively. |
| Realized forward-return evidence (by bucket/setup/regime; aggregates) | `forward_testing:compute_forward_aggregates` / `compute_run_scorecard` | `GET /api/backtest`, `GET /api/research/samples` | **[built — UNCHANGED]** the realized-return evidence the referee's edges are tested over. |
| Research-lab cohorts (factor / event-study / regime-setup-pattern / …) | `research:compute_*` (factor_lab, event_study, regime_setup_pattern, …) | `GET /api/research/*`, `GET /api/research/samples` | **[built — UNCHANGED]** an Evidence Claim's cohort selectors mirror `/api/research/samples`. |

The full prior-session Data Contract (every regime/score/forward-return/job row) still holds verbatim and
is NOT reproduced here; the rows above are those the evidence layer reads or attaches a badge to. The ONLY
new contract value this session introduces is the first row (evidence status / certified-claim).

**iter-2 clarification (additive — same value, no new module/endpoint):** for a **score-column factor
cohort** the canonical `signal` IS the factor key itself — `leadership_score` / `entry_quality_score` /
`risk_score` are byte-identical factor-catalog keys AND UI signal keys (`config.FACTOR_TYPED_COLUMNS`), so a
certified top-decile claim on a score tautologically backs that score's badge. The `signal` is carried on
the WRITTEN claim (set on the iteration's `## Evidence Claim` JSON, which `verify_edge` persists verbatim
since `signal` is not a `_CLAIM_SELECTOR_KEYS` selector and is ignored by cohort assembly; optionally also
derived read-side for score-column cohorts as defense-in-depth). Proven-ness still flows ONLY from the
referee's `verdict.status == PASS`; the factor→signal map is display-routing, not a second computation. The
**J-02 proof drill panel** on `/stocks/{ticker}` is an additional READER of the same `GET /api/evidence`
payload (verdict/control/register_date fields, verbatim) — no new computing module, no second endpoint, no
recompute.

**iter-4 clarification (additive — same value, no new module/endpoint):** the certified-claims value now
also includes **regime-conditioned event-study claims** — a named-regime cohort slice (`kind=event-study`,
`slice_kind=regime`, `regime=<label>`, e.g. the Breakout-watch setup in the `Risk-on` regime). Such a claim
**carries NO `signal`** (it backs no inline per-stock score badge; `app.engine.evidence:_resolve_signal`
returns `None` for a non-score cohort), so it appears ONLY as a CLAIM ROW in `claims[]` and never enters
`proven_signals` — it cannot light or overwrite a score badge (J-01/J-02/J-03 are unaffected). The
`/evidence` `ClaimRow` is an additional READER that re-displays the entry's own `claim.regime` selector as a
**"Regime: <label>" display label** (J-04 "labeled with the regime it holds in") and renders an honest
title/linkback for a signal-less setup claim — re-display only, no new computing module, no second endpoint,
no recompute. The Dashboard regime panel adds a discoverable LINK to `/evidence` (navigation affordance — it
serves no new value). Proven-ness still flows ONLY from `verdict.status == PASS`.

**iter-8 clarification (additive — same value, no new module/endpoint):** the certified-claims value now
also includes **signal-less plain-factor decile cohort claims** — a NON-score factor sliced to a decile
(`kind=factor`, `factor=<non-score factor>`, `slice_kind=decile`, `decile=<n>`, here the `vcp_contraction`
top decile D10 at horizon 20, J-06). (The originally-proposed `ma_stack` D10 cohort was REJECTED by the
post-decompose referee — holdout +0.0262, p=0.0195 ≥ α/4=0.0125 — and is recorded as a FAIL ledger entry
that permanently tightens the Bonferroni bar; the human operator replaced it in `docs/goal.md` with
`vcp_contraction` D10 h20, the one backlog cohort that certifies at the current bar — verified holdout
+0.0333, p=0.01149 < α/4=0.0125. Do NOT re-propose ma_stack/hv/high_proximity — each failed submission
permanently raises the bar.) Like the regime event-study claim, such a claim **carries NO `signal`**
(`vcp_contraction` ∉ the three score columns ⇒ `app.engine.evidence:_resolve_signal` returns `None`): it
appears ONLY as a CLAIM ROW in `claims[]` and never enters `proven_signals` — it cannot light or overwrite a
`/stocks` inline score badge (J-01/J-02/J-03 unaffected; `proven_signals` stays `{leadership_score}`). The
**Research factor lab** (`/research/factor-lab`) becomes an additional READER of the SAME `GET /api/evidence`
payload (via the existing `lib/api.ts:fetchEvidence` client — NO new fetch path): its top-decile rows resolve
a "Proven"/"Not yet proven" status by MATCHING the served `claims[]` on cohort selectors
(`factor`+`slice_kind`+`decile`+`horizon`+`direction`) — a pure read-side cohort matcher in `lib/evidence.ts`
(the signal-less successor to `resolveEvidenceStatus`), NEVER a recompute of proven-ness (which still flows
solely from `verdict.status == PASS`) and NEVER a second endpoint. The `/evidence` `ClaimRow` gains (a) an
honest factor-cohort title + "Backs: Research factor lab →" linkback (the `claimSurface` `factor` branch,
replacing the misleading "Unmapped signal" fallback) and (b) a deterministic cohort-derived anchor so the
factor-lab badge can deep-link to its row. Re-display + display-routing only — no new computing module, no
second endpoint, no nav-skeleton change.

**iter-9 clarification (additive — INTERNAL certification machinery; no displayed value, no new endpoint, no
nav change):** the certification ENGINE behind the single evidence-status contract value gains a sustainable
**trial economy** so future iterations can explore J-07 (multi-horizon) and J-08 (combination) edges without
permanently tightening the user-facing canonical Bonferroni bar (`app.engine.ledger:count_trials`; now at
divisor 4, the next canonical claim would face divisor 5). The deflation becomes an **injectable policy** on
`RefereeState` with the DEFAULT = Bonferroni (so `certify_edge` reproduces every existing verdict
byte-identically), plus a NEW PURE `app.engine.online_fdr` (LORD++; no RNG/IO; `test_level` derived from prior
rejection times — `app.engine.ledger:rejection_offsets`, derived `[1,2,4]` from the live canonical PASS
ordinals, no schema change). A SEPARATE internal **staging ledger**
(`runs/goal-session-mcp-loop/state/staging-ledger.jsonl`, config `evidence.staging_ledger_path`, harness
`STAGING_LEDGER_PATH`) holds exploration probes under the online-FDR economy. Crucially this introduces **NO
new displayed value and NO new serving endpoint**: the staging ledger is internal-only — never read by any
page, never served, never displayed. The user-facing canonical `certified-claims.jsonl` + `GET /api/evidence`
+ `proven_signals` stay byte-identical, and FDR is `enabled: false` by default — so the "Proven" badge keeps
its strict family-wise (Bonferroni) guarantee (honesty constraint, anti-goal #1/#4: FDR is weaker than
family-wise control and is FENCED to staging). `verify_edge` stays the ONLY ledger writer (it merely routes to
canonical vs staging); the gate (`verify_claim.py`) reads an optional per-claim `"ledger"` key (default
`"staging"`, explicit `"canonical"` for promoted winners) and keeps `exit 3`-on-non-PASS blocking. No new
computing module for any DISPLAYED value, no second endpoint, no nav-skeleton change.

**iter-10 clarification (additive — INTERNAL discovery machinery; no displayed value, no new endpoint, no
nav change):** Part B Phase 1 opens the certification engine's scan APERTURE beyond the 20-day horizon so
future iterations can surface J-07 (multi-horizon) / J-08 (combination) edges. This iter adds
`config.triad.horizons: [1,5,10,20,60]` (reusing `compute_factor_lab` and the already-present
`walk_forward.horizons`) + raises `triad.top_k` / the inert `triad.screen.haircut_coef`, so
`app.engine.triad_scan:{scan_factor_decile_cells,scan_product_triad}` enumerate one cell per
`(factor, horizon, decile)` across all horizons (the scan stays READ-ONLY — it never writes any ledger).
A FIXED, PRE-REGISTERED candidate set of multi-horizon single-factor hypotheses (config-backed + mirrored
into `project-extensions/proposer-guidance.md`, each with an economic rationale — the anti-data-mining
keystone; NEVER the full cross-product) is then run through the referee into the INTERNAL **staging** ledger
via `app.mcp.tools:verify_edge(ledger="staging")` under the online-FDR (LORD++) economy (`evidence.fdr.enabled`
activated). Crucially this introduces **NO new displayed value and NO new serving endpoint**: the staging
ledger stays internal-only (never served by `GET /api/evidence`, never displayed — as documented in the
iter-9 clarification), so no `/evidence` row, no factor-lab badge, and no `/stocks` badge change this iter.
The user-facing canonical `certified-claims.jsonl` + `GET /api/evidence` + `proven_signals` (`{leadership_score}`)
stay BYTE-IDENTICAL: the honesty fence `use_fdr = (ledger == STAGING and evidence.fdr.enabled)` keeps
canonical certification strict family-wise Bonferroni even with FDR on (anti-goal #1/#4 — FDR is weaker than
family-wise control and is FENCED to staging; it lights NO badge). `verify_edge` stays the ONLY ledger
writer (routing to the staging file). No new computing module for any DISPLAYED value, no second endpoint,
no nav-skeleton change. (iter-11 will PROMOTE the staging winner with block-bootstrap `p_value < 0.010` to
canonical via an explicit `"ledger":"canonical"` `## Evidence Claim` and surface J-07 as an additional READER
of the SAME `GET /api/evidence` payload — same evidence-status contract value, one more reader, still no new
module/endpoint.)

**iter-11 clarification (additive — same value, one more reader; no new module/endpoint, no nav change):** the first NON-20-horizon canonical claim lands — `vcp_contraction` D10 @ **horizon 60** (J-07), promoted from the iter-10 staging winner via an explicit `"ledger":"canonical"` `## Evidence Claim` (block-bootstrap p=0.00049975 < the canonical Bonferroni divisor-5 bar required_p=0.010; holdout +8.91% beats SPY OOS). It is a NEW ENTRY in the EXISTING `certified-claims.jsonl` (now 5 canonical entries; the next canonical claim faces divisor 6) served by the EXISTING `GET /api/evidence` — no new computing module, no new serving endpoint. Like the h20 vcp_contraction and the event-study rows it **carries NO `signal`** (`vcp_contraction` ∉ the three score columns), so it appears ONLY as a `claims[]` row + the factor-lab badge and NEVER enters `proven_signals` (stays `{leadership_score}`) — it cannot light a `/stocks` inline score badge (J-01/J-02/J-03 unaffected). The Research **factor lab** badge becomes a PER-HORIZON reader of the SAME payload: `resolveCohortEvidence` is now resolved for each horizon in `[1,5,10,20,60]` (previously only `default_horizon`=20), so `vcp_contraction` reads "Proven" at h20 (L4) AND h60 (L5) and "Not yet proven" at h1/h5/h10 — one more reader position of the same contract value, not a second computation or endpoint. `cohortClaimId` already keys anchors by horizon (`factor-vcp_contraction-d10-h60` distinct from `…-h20`) so each badge deep-links to its own row. No nav-skeleton change (J-07 reuses the EXISTING `/research/factor-lab` + `/evidence`, both already in the IA). Proven-ness still flows ONLY from `verdict.status == PASS`.

**iter-12 clarification (additive — INTERNAL discovery machinery; no displayed value, no new endpoint, no nav change):** completing the deferred "combinations" half of Part B Phase 1, the certification engine's scan aperture now also covers **2-factor combination composites** so iter-13 can surface J-08. A FIXED, PRE-REGISTERED set of three 2-factor combination hypotheses (a NEW `config.triad.combination_candidates` block, mirrored into `project-extensions/proposer-guidance.md` §4.2, each pair carrying an economic rationale — the anti-data-mining keystone; NEVER the full `factor × pair × horizon` cross-product) is run through the referee into the INTERNAL **staging** ledger via a new combination explorer in `app.engine.triad_scan` (sibling to `explore_multi_horizon_staging`) calling `app.mcp.tools:verify_edge(ledger="staging")` under the online-FDR (LORD++) economy. The referee cert path is REUSED UNCHANGED — `assemble_claim_observations`→`drill_samples` already assemble a `kind:combination` composite cohort via the `condition`/`cohort` selectors already in `_CLAIM_SELECTOR_KEYS`; `verify_edge`'s cert logic is not modified. Crucially this introduces **NO new displayed value and NO new serving endpoint**: the staging ledger stays internal-only (never served by `GET /api/evidence`, never displayed — as documented in the iter-9/iter-10 clarifications), so no `/evidence` row, no combination-lab badge, and no `/stocks` badge change this iter. The user-facing canonical `certified-claims.jsonl` (five entries) + `GET /api/evidence` + `proven_signals` (`{leadership_score}`) stay BYTE-IDENTICAL: the honesty fence `use_fdr = (ledger == LEDGER_STAGING and evidence.fdr.enabled)` keeps canonical certification strict family-wise Bonferroni (anti-goal #1/#4 — FDR is weaker than family-wise control and is FENCED to staging; it lights NO badge). `verify_edge` stays the ONLY ledger writer (routing to the staging file), with the fail-closed guard that refuses the canonical ledger path extended to the combination explorer. No new computing module for any DISPLAYED value, no second endpoint, no nav-skeleton change. (iter-13 will PROMOTE the staging combination winner whose recorded block-bootstrap `p_value` clears the canonical Bonferroni divisor-6 bar `required_p ≈ 0.00833` with margin to canonical via an explicit `"ledger":"canonical"` `## Evidence Claim`, and surface J-08 on `/research/factor-combination` + `/evidence` as additional READERS of the SAME `GET /api/evidence` payload — same evidence-status contract value, more readers, still no new module/endpoint.)

**iter-13 clarification (additive — same value, more readers; no new module/endpoint, no nav change):** the first **2-factor combination** canonical claim lands — the `rs_spy_3m:top:quintile` × `high_proximity:top:tertile` **composite** cohort @ **horizon 20** (J-08), promoted from the iter-12 staging winner (`staging-ledger.jsonl` #7) via an explicit `"ledger":"canonical"` `## Evidence Claim` (recorded block-bootstrap `p_value`=0.0009995 < the canonical Bonferroni divisor-6 bar `required_p`≈0.00833; holdout +4.69% beats SPY OOS). It is a NEW ENTRY in the EXISTING `certified-claims.jsonl` (now 6 canonical entries; the next canonical claim would face divisor 7) served by the EXISTING `GET /api/evidence` — no new computing module, no new serving endpoint. Like the vcp_contraction factor rows and the event-study row it **carries NO `signal`** (`kind=combination` ⇒ `app.engine.evidence:_resolve_signal` returns `None`; only the three score-column factors self-map), so it appears ONLY as a `claims[]` row + the combination-lab composite badge and NEVER enters `proven_signals` (stays `{leadership_score}`) — it cannot light a `/stocks` inline score badge (J-01/J-02/J-03 unaffected). The Research **Multi-factor combination lab** (`/research/factor-combination`, composite cohort) becomes an additional READER of the SAME payload via a NEW PURE read-side matcher `resolveCombinationEvidence` (the combination sibling of `resolveCohortEvidence`) matching the served `claims[]` on `kind=combination` + `cohort=composite` + the `condition` leg-set (order-independent) + `horizon` + `direction` — never a recompute of proven-ness (still solely `verdict.status==PASS`) and never a second endpoint; the composite cohort reads "Proven" ONLY for the certified selection and "Not yet proven" for every other combination (anti-goal #1). The `/evidence` `ClaimRow` gains (a) a `claimSurface` **combination** branch — an honest composite title + "Backs: Multi-factor combination lab →" linkback (replacing the "Unmapped signal" fallback) — and (b) a deterministic leg-set-derived combination anchor (via `claimAnchorId`) so the lab badge deep-links to its row. Re-display + display-routing only — no new computing module, no second endpoint, no nav-skeleton change (J-08 reuses the EXISTING `/research/factor-combination` + `/evidence`, both already in the IA). This is the LAST Must-have journey — GOAL_ACHIEVED becomes reachable once J-08 is browser-verified with J-01..J-07 non-regressed.

**iter-15 clarification (additive — same value, one more reader; no new module/endpoint, no nav change):** the second NON-20-horizon single-factor canonical claim lands — `rs_spy_3m` D10 @ **horizon 60** (J-09), promoted from the pre-registered §4.1 #3 multi-horizon staging winner (`staging-ledger.jsonl` row 3) via an explicit `"ledger":"canonical"` `## Evidence Claim` (recorded block-bootstrap `p_value`=0.00049975 < the canonical Bonferroni divisor-7 bar `required_p`≈0.007143; holdout +0.2134 beats SPY OOS — an implausibly large edge the iter-10 auditor flagged, scrutinized here by the coherence-auditor + phase auditor and governed by the honest-stop guard). It is a NEW ENTRY in the EXISTING `certified-claims.jsonl` (now 7 canonical entries; the next canonical claim would face divisor 8) served by the EXISTING `GET /api/evidence` — no new computing module, no new serving endpoint. Like the `vcp_contraction` factor rows and the event-study row it **carries NO `signal`** (`rs_spy_3m` ∉ the three score columns — it is a `leadership.components.rs_spy_3m.raw` factor, so `app.engine.evidence:_resolve_signal` returns `None`), so it appears ONLY as a `claims[]` row + the factor-lab badge and NEVER enters `proven_signals` (stays `{leadership_score}`) — it cannot light a `/stocks` inline score badge (J-01/J-02/J-03 unaffected). The Research **factor lab** (`/research/factor-lab`, already listing `rs_spy_3m` per `config.yaml` factor_lab.factors) reuses the EXISTING per-horizon reader UNCHANGED: `resolveCohortEvidence` (already resolved for each horizon in `[1,5,10,20,60]` since iter-11) now matches the served `claims[]` for `rs_spy_3m` at h60 → "Proven" (deep-link anchor `factor-rs_spy_3m-d10-h60` via `cohortClaimId`) and "Not yet proven" at h1/h5/h10/h20 — one more reader position of the same contract value, never a recompute (proven-ness still solely `verdict.status==PASS`) and never a second endpoint. No new frontend computing module, no `/evidence` ClaimRow branch change (the `factor` branch + "Backs: Research factor lab →" linkback already exist), no nav-skeleton change (J-09 reuses the EXISTING `/research/factor-lab` + `/evidence`, both already in the IA). This is a post-GOAL_ACHIEVED continuous-improvement journey; proven-ness still flows ONLY from the referee's PASS.

**iter-16 clarification (additive — INTERNAL data-prep asset; no displayed value, no new endpoint, no nav change):** in service of the NEW human-authored J-10..J-13 (30-year Stooq history over the broadened 548-name point-in-time pool), iter-16 STAGES the replacement price seed as a committed, validated data asset at `apps/backend/data/seed-stooq-30y/` (`prices/*.csv` + `meta.json`, fetched via the EXISTING keyless `StooqProvider` per-symbol CSV endpoint through `make_provider("stooq")`, using a new `--provider/--out/--symbols-set` interface on `apps/backend/scripts/ingest_seed.py`; probe-first, resumable, honest-stop on rate-cap — never fabricated/padded/spliced). The staged directory is read by NOTHING at runtime: `config.provider` stays `seed`, `SeedProvider` still reads `data/seed/`, `seed_loader.load_prices` unchanged, BOTH evidence ledgers byte-identical (zero referee submissions), `GET /api/evidence` + every displayed number unchanged. This is Part A of the SANCTIONED data-basis migration (goal.md "Data-basis change (sanctioned ledger reset)"): iter-17 will atomically swap the basis, broaden `load_prices` to the pool, add the `resolve_candidate` staleness gate, rebuild the DB, RESET + regenerate both ledgers on the new data (every pre-refresh certified claim treated as invalidated), and refresh the frozen-golden tests. No new computing module, no second endpoint, no nav-skeleton change (J-10..J-13 all live under EXISTING IA homes — see the homes table).

**iter-17 clarification (additive — INTERNAL data-prep asset completion; no displayed value, no new endpoint, no nav change):** in service of the human-authored **J-14** (deep, vendor-disclosed index/macro context) and sequenced by goal.md §H ("complete the seed's index/macro context BEFORE the swap so the swap happens once over one complete seed"), iter-17 COMPLETES the staged 30-year seed at `apps/backend/data/seed-stooq-30y/`: `_SPX`/`_NDX`/`_DJI` staged deep (1996→pinned end 2026-07-01, window-clipped) from Stooq's LOCAL world bundle (`data/d_world_txt`; vendor `stooq` — same vendor, local access), `_VIX` deep from Yahoo (vendor `yahoo`; sanctioned offline fallback = byte-identical live copy, honestly short 2021→2026-05), and the deterministic FRED-macro proxies `_TNX`/`_DXY`/`_VXN` copied byte-identical (vendor `fred-macro-proxy` — NEVER re-fetched from Yahoo, staying coherent with `data/seed/macro/`; a proxy is never presented as a market index). Each context series' vendor is recorded per-series in the staged `meta.json` — the future single source for the J-14 vendor label, to be REGISTERED as a Data Contract value only at the post-swap iteration that first DISPLAYS it. The staged tree remains read by NOTHING at runtime: `config.provider` stays `seed`, `SeedProvider` still reads `data/seed/`, BOTH evidence ledgers byte-identical (zero referee submissions), `GET /api/evidence` + every displayed number unchanged. A new swap-completeness validation (staged price-file set ⊇ live seed's) becomes the hard gate the iter-18 atomic swap + SANCTIONED ledger reset must see green before flipping the basis (per the iter-16 clarification). No new computing module, no second endpoint, no nav-skeleton change (J-14's homes are the EXISTING Dashboard `/` + `/data` — see the homes table).

**iter-18 clarification (the SANCTIONED data-basis swap + ledger reset — same values, same modules, same endpoints; content REGENERATED; no new displayed value, no new endpoint, no nav change):** executing goal.md's one sanctioned reset ("Data-basis change (sanctioned ledger reset)"), the committed price basis under `data/seed/` becomes the staged 30-year / 548-pool set (590 price CSVs, window 1996-01-01 → 2026-07-01; `data/seed/macro/` + `universe_pool.csv` preserved; per-series vendor records carried in `meta.json`, still undisplayed — the J-14 vendor label registers only when first surfaced). Every registered Data Contract value keeps its SAME computing module and SAME serving endpoint; only CONTENT regenerates on the new basis: (1) **evidence status / certified-claim** — `certify_edge` via `verify_edge` (still the ONLY writer) → `certified-claims.jsonl` → `GET /api/evidence`, with BOTH ledgers regenerated from scratch by replaying the SAME pre-registered 7-claim canonical family in historical order (verbatim selectors, divisors 1..7 preserved — including the ma_stack FAIL re-test) plus the two pre-registered staging explorers under the fenced LORD++ economy; no retired edge value may render unless its claim independently re-certifies (a non-reproducing claim honestly reads "Not yet proven"/FAIL); the two frozen-golden suites refresh to the regenerated verdicts (the one sanctioned refresh). (2) **daily prices / bars** — same `seed_loader`/`daily_prices` value and same `GET /api/stocks/{ticker}/bars` endpoint; `load_prices` broadens to `read_pool ∪ all_seed_symbols`, and `/bars` gains presentation-bounding range/downsample params + pool-broadened ticker validation on the SAME endpoint (bounded default window, explicit full-history opt-in — J-10 performance; never a second endpoint, never a client-side recompute). (3) **membership** — same `resolve_members`/`resolve_candidate` module and `/methodology` serving path; `resolve_candidate` gains the config-driven recency/staleness gate (one NEW exclusion reason; closes the `rs_vs` misalignment for names whose data ends mid-history — J-12). `walk_forward.history_years` 2→~30 deepens the `/backtest` window (same module/endpoint); `SURVIVORSHIP_BIAS_LABEL` names the ~30-year span. Proven-ness still flows ONLY from `verdict.status == PASS` on the REGENERATED rows. No new computing module for any displayed value, no second endpoint, no nav-skeleton change (J-10/J-11/J-12 live at their already-registered homes).

<!-- LOOP RULE for the decomposer: an iteration that surfaces any signal AS "Proven" MUST carry a
machine-readable `## Evidence Claim` JSON block (cohort selectors mirroring /api/research/samples) so the
post-decompose gate certifies it through the referee BEFORE build; a non-PASS verdict (FAIL/INSUFFICIENT)
blocks the iteration. Pure UX / correctness / navigation iterations (no new "proven" claim) need none. -->
