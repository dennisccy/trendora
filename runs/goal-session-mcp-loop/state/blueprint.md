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

<!-- LOOP RULE for the decomposer: an iteration that surfaces any signal AS "Proven" MUST carry a
machine-readable `## Evidence Claim` JSON block (cohort selectors mirroring /api/research/samples) so the
post-decompose gate certifies it through the referee BEFORE build; a non-PASS verdict (FAIL/INSUFFICIENT)
blocks the iteration. Pure UX / correctness / navigation iterations (no new "proven" claim) need none. -->
