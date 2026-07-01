# goal-mcp-loop-iter-11 Execution Plan

Surface **J-07**: promote the referee-certified **`vcp_contraction` D10 @ h60** signal-less edge
(pre-scored PASS in iter-10 staging: holdout **+8.91%**, block-bootstrap p **0.00049975** < the
canonical divisor-5 bar 0.010) to a canonical `certified-claims.jsonl` entry and surface it as a
**per-horizon** factor-lab "Proven" badge + a new `/evidence` claim row. The factor lab evolves from
a single-horizon (h20-only) evidence marker to an honest per-horizon view; h60 → "Proven", the
uncertified horizons (h1/h5/h10) → "Not yet proven", h20 → "Proven" (J-06 unchanged).

Aligns exactly with goal.md Must-have journey **J-07** and the evaluator's iter-10 recommendation.
No drift from the goal detected. Builds directly on iter-8's h20 badge (`resolveCohortEvidence`,
`cohortClaimId`, `FactorEvidenceBadge`) and iter-10's staging discovery — most plumbing already
exists; this iteration promotes one winner and renders it per-horizon.

## What to Build

- **(Data precondition — produced by the post-decompose gate BEFORE build, NOT by an agent.)** The
  gate certifies the canonical `## Evidence Claim`
  `{"kind":"factor","factor":"vcp_contraction","slice_kind":"decile","decile":10,"horizon":60,"direction":"positive","ledger":"canonical"}`
  through the referee, appending the **5th** entry to `certified-claims.jsonl`: `status=PASS`,
  `holdout_edge≈+0.08910`, `control_excess≈+0.08910` (beats SPY OOS), `p_value=0.0004997501249375312`,
  `deflation="bonferroni"`, `deflation_divisor=5`, `required_p=0.010`, `horizon=60`, **no `signal` key**.
  A non-PASS verdict BLOCKS the iteration (fail-closed). *This entry is already present on disk
  (uncommitted; HEAD has 4) — the developer builds against the 5-entry ledger and MUST NOT edit or
  reorder it.*
- **Per-horizon factor-lab evidence badges** (`app/research/_labs.tsx`). Replace the single
  `FactorEvidenceBadge` rendered once at `defaultHorizon` (currently lines ~852-858, "Evidence
  (D10 · 20d)" column) with one badge **per horizon** in the served vocabulary `data.horizons`
  (`[1,5,10,20,60]`), each resolving its own status via the EXISTING
  `resolveCohortEvidence({factor: row.key, slice_kind:"decile", decile: topDecile, horizon: h, direction:"positive"}, evidenceClaims)`
  — same matcher, same `GET /api/evidence` payload, no new fetch, no recompute. Result on the
  `vcp_contraction` row: h60 → "Proven" → `/evidence#factor-vcp_contraction-d10-h60`; h1/h5/h10 →
  "Not yet proven" (no href); **h20 → "Proven" → `/evidence#factor-vcp_contraction-d10-h20`
  (unchanged — J-06 must not regress).** Place the per-horizon badges VISIBLE on the surface aligned
  with the existing per-horizon forward-return columns (`groupedHorizonColumns(horizons)`) —
  recommended: a per-column badge or compact per-horizon chip strip. Preserve the "Proven" `<Link>`
  `stopPropagation()` guard so a click deep-links rather than toggling the expand row (iter-5 hazard).
- **`data-horizon` attribute** on `FactorEvidenceBadge` (both proven + not-proven branches), alongside
  the existing `data-testid="factor-evidence-badge"` / `data-proven` / `data-factor`, so each badge is
  independently selectable (`[data-factor="vcp_contraction"][data-horizon="60"]` → `data-proven="true"`;
  `[data-horizon="10"]` → `data-proven="false"`).
- **`claimSurface` subtitle horizon-disambiguation** (`lib/evidence.ts`, display-only). The factor-cohort
  subtitle is currently horizon-agnostic, so the h20 and h60 vcp_contraction `/evidence` rows would share
  wording. Disambiguate the h60 row (e.g. `"Out-of-sample edge — factor top decile · 60-day hold"`) so it
  is self-distinguishing. **Keep the h20 row's rendered text byte-identical to iter-8** (J-06 non-regression)
  — apply the "· N-day hold" suffix to the new h60 row only (see Assumptions). No return/price/buy-sell
  language. This is the ONLY `evidence.ts` change: `resolveCohortEvidence` / `cohortClaimId` /
  `claimAnchorId` / `formatEvidencePct` already support horizon and need NO edit.
- **Frontend tests** (`lib/evidence.test.ts` + a per-horizon `FactorEvidenceBadge` component test).
  MUST update case (o) — it currently pins `{…VCP_COHORT, horizon:60}` as a MISMATCH → "Not yet proven"
  (will break once the h60 claim is live) — and add a positive h60 case (see Key Test Scenarios).
- **Verify `GET /api/evidence`** serves the new entry verbatim in `claims[]` and `proven_signals` stays
  exactly `{leadership_score}` (live check during browser-qa; optionally a TEST-ONLY assertion in
  `apps/backend/tests/test_evidence.py`, mirroring iter-8 — zero `app/**` change). No app engine/router edit.
- **Demo-narrator `[NEW]`-flagged walkthrough** of the h60 row + per-horizon badge (pipeline step; J-07
  "Walkthrough" acceptance) and the **dev handoff** at `docs/handoffs/goal-mcp-loop-iter-11-dev.md`.

## Agents Required
- developer: yes -- frontend per-horizon badge + `data-horizon` + `claimSurface` subtitle disambiguation; update `evidence.test.ts` (fix case (o), add h60) + a per-horizon component test; verify `GET /api/evidence`; dev handoff.
- backend-data: no -- the 5th canonical ledger entry is written by the post-decompose GATE (already on disk), NOT by an agent. No engine/router/referee/ledger/online_fdr/triad_scan/`evidence.py` edit. Only optional touch: a TEST-ONLY payload assertion in `test_evidence.py`.
- frontend-ux: yes -- the core of the iteration (per-horizon badges on `/research/factor-lab`; the additive `/evidence` row renders via the existing `ClaimRow`).

(The pipeline also runs reviewer / QA / **auditor** / browser-qa automatically. The AUDITOR MUST run
this iteration — it ships a NEW canonical "Proven" claim + a new public badge, the exact high-stakes
write that needs the audit, mirroring iter-8. The canonical `browser-qa-agent` lane MUST actually run
and write `reports/phase-goal-mcp-loop-iter-11-ui-test-results.md` — a real badge flip, not a
backend-only SKIP.)

## Frontend Present
Frontend Present: yes

The iteration flips a user-facing badge and adds a visible `/evidence` row. Chrome MCP browser checks
are REQUIRED (canonical browser-qa lane). Free port :3255 and ensure the frontend can reach the backend
before the browser lane binds.

## Files to Create/Modify
- `/home/dennis-chan/Git/trendora/apps/frontend/app/research/_labs.tsx` -- per-horizon `FactorEvidenceBadge` render (loop over `data.horizons`, aligned with the forward-return horizon columns); add `data-horizon={horizon}`. Keep the h20 badge + `stopPropagation` deep-link behavior.
- `/home/dennis-chan/Git/trendora/apps/frontend/lib/evidence.ts` -- `claimSurface` factor-cohort subtitle horizon-disambiguation ONLY (h20 wording preserved). No other function changes.
- `/home/dennis-chan/Git/trendora/apps/frontend/lib/evidence.test.ts` -- update case (o) (drop the h60-mismatch row), add positive h60 "Proven" (href `…-h60`), keep h20 "Proven" + h10 "Not yet proven"; assert `cohortClaimId`/`claimAnchorId` horizon-distinct anchor; `formatEvidencePct(0.08909719710495288) === "+8.91%"`; the h60 `claimSurface` disambiguated subtitle + h20 unchanged.
- `/home/dennis-chan/Git/trendora/apps/frontend/app/research/_labs.test.tsx` (or the developer's existing component-test location) -- per-horizon `FactorEvidenceBadge` renders `data-horizon` + correct `data-proven` per horizon; a matched-but-non-PASS entry (ma_stack FAIL) stays "Not yet proven".
- `/home/dennis-chan/Git/trendora/apps/backend/tests/test_evidence.py` (OPTIONAL, test-only) -- assert the served payload contains the 5th (h60) entry verbatim and `proven_signals == {leadership_score}`. No `app/**` change.
- `/home/dennis-chan/Git/trendora/docs/handoffs/goal-mcp-loop-iter-11-dev.md` -- NEW dev handoff.
- **DO NOT EDIT (editing = regression signal):** `runs/goal-session-mcp-loop/state/certified-claims.jsonl` (the gate wrote entry 5; the 4 prior rows stay byte-identical); any `apps/backend/app/**` (engine / referee / ledger / online_fdr / triad_scan / `evidence.py` / routers); the score branches of `claimSurface` / `resolveEvidenceStatus`; `proven_signals`.

## UI Evolution
- New user-facing capability: audit an out-of-sample-proven factor edge at a **non-20-day horizon** end-to-end — see it "Proven" on the factor lab at h60, click through to its certified-claim row, and see every other horizon honestly marked "Not yet proven".
- New information displayed: a new `/evidence` certified-claim row for `vcp_contraction — top decile (D10)` @ **h60** (PASS, +8.91% holdout, +8.91% vs SPY, registration date, forward-walk "Pending", "Backs: Research factor lab →"); per-horizon "Proven"/"Not yet proven" badges on the factor-lab factor rows.
- New user actions: click the factor-lab h60 "Proven" badge to deep-link to `/evidence#factor-vcp_contraction-d10-h60` (`stopPropagation` guards the row expand toggle).
- UI surface changes: `/research/factor-lab` (single h20 evidence marker → per-horizon evidence badges) and `/evidence` (one additional auto-rendered claim row). No new pages.
- Navigation changes: none.

## Visual Requirements
- Component patterns: reuse the existing quiet `FactorEvidenceBadge` chip ("Proven ✓ / Not yet proven"); render a per-horizon set (per-column badge or compact chip strip) aligned with the existing `groupedHorizonColumns` forward-return columns in `FactorsTable`. Reuse the existing `<Link>` + `stopPropagation` deep-link. The `/evidence` row auto-renders via the existing `ClaimRow` (no new component).
- Layout: extend the existing data-dense factor-lab table; badges aligned under/with the horizon columns. No layout rewrite.
- Key visual effects: match Trendora's minimal, data-dense, evidence-first style — the badge reads as a calm, unmissable "proven / not yet proven" chip, never hype (goal.md Design Direction). Invent no new effects.
- States to handle: empty/failed `fetchEvidence` → every badge "Not yet proven" with no link (fail-safe honesty); an uncertified horizon (h1/h5/h10) → "Not yet proven"; a matched-but-non-PASS entry (ma_stack FAIL) → "Not yet proven".

## Key Test Scenarios
Phase is complete only when all pass; assert EXACT values and cover a failure path.
- **Gate precondition:** the post-decompose gate certified the canonical vcp_contraction D10 h60 claim PASS (Bonferroni divisor 5, required_p=0.010); `certified-claims.jsonl` has 5 entries (else fail-closed, no build).
- **J-07 (browser-qa, canonical lane — REQUIRED):** `/evidence` — the NEW `vcp_contraction` D10 row shows `horizon=60`, PASS, holdout **+8.91%**, control vs SPY **+8.91%**, a registration date, forward-walk "Pending", "Backs: Research factor lab →". `/research/factor-lab` — `[data-factor="vcp_contraction"][data-horizon="60"]` reads "Proven" with href `/evidence#factor-vcp_contraction-d10-h60`; `[data-horizon="1"|"5"|"10"]` read "Not yet proven". **Scroll each asserted badge into the viewport before capture** (iter-3 lesson — the table is wide, the h60 column/expander sits below/right of the fold).
- **J-06 (regression):** `[data-factor="vcp_contraction"][data-horizon="20"]` still reads "Proven" and deep-links to `/evidence#factor-vcp_contraction-d10-h20`; the h20 `/evidence` row unchanged.
- **J-05 (regression):** `/evidence` lists the prior four rows (leadership_score PASS, Breakout-watch PASS, ma_stack FAIL, vcp_contraction h20 PASS) PLUS the new h60 row; each linkback works.
- **J-01/J-02/J-03 (regression):** `/stocks` rows still show Leadership "Proven" and Entry Quality / Risk "Not yet proven"; `proven_signals` byte-identical `{leadership_score}`; NO new inline `/stocks` badge from the signal-less h60 claim.
- **J-04 (regression):** Breakout-watch regime row unchanged.
- **Frontend unit:** `resolveCohortEvidence` — h60 → proven (href `…-h60`); h10 → not proven (no href); h20 → proven (h20 entry). Anchor horizon-distinct. `formatEvidencePct(0.08909719710495288) === "+8.91%"`. `claimSurface` h60 subtitle disambiguated + h20 unchanged. Per-horizon `FactorEvidenceBadge` `data-horizon`/`data-proven`. **Error cases:** uncertified horizon → "Not yet proven"; empty/failed `fetchEvidence` → all badges "Not yet proven", no link; matched-but-non-PASS (ma_stack) never "Proven".
- **Correctness (anti-goal #3):** the displayed h60 edge / p / control byte-match `certified-claims.jsonl` L5 — never a UI recompute.
- **Anti-goals:** no return/price/buy-sell language; determinism + no-lookahead preserved; no secrets. Auditor confirms the signal-less claim never lights a `/stocks` badge and `proven_signals` is unchanged.
- **Deliverables:** demo-narrator `[NEW]`-flagged walkthrough produced (`demo.sh mcp-loop --session-live`); `docs/handoffs/goal-mcp-loop-iter-11-dev.md` written.

## Assumptions
- **h20 `/evidence` row unchanged (J-06):** to honor "keep the h20 row's existing wording behavior intact" while disambiguating h60, the developer preserves the h20 factor-cohort subtitle exactly (iter-8's "Out-of-sample edge — factor top decile") and applies the "· N-day hold" suffix to the h60 row only (gate on horizon ≠ default, or on horizon value). The load-bearing horizon signal remains the `horizon=60` hypothesis chip already rendered.
- **leadership_score reading "Proven" in the factor lab is HONEST** (it has a real PASS canonical entry) — do NOT special-case the matcher to vcp-only. Each "Proven" badge deep-links to its row's REAL `claimAnchorId` (a signal-less factor → its `factor-…-h…` anchor; a score-column factor → its `signal-…` anchor).
- The `[1,5,10,20,60]` horizon vocabulary is sourced from the served `data.horizons` payload field (already threaded into `FactorsTable`) — no hardcoded horizon list, no backend/payload change.

## Out of Scope (excluded — no scope creep)
- **J-08** (multi-factor combination on `/research/factor-combination`) — deferred to iter-12+ per goal.md Part B sequencing.
- Promoting `rs_spy_3m` h60 (implausible +0.21 p-floor edge) or `leadership_score` h60 (config-declared fallback / score column) — only `vcp_contraction` h60 is promoted.
- Any inline `/stocks` badge for the signal-less h60 claim, or any change to `proven_signals` / the per-stock score badges.
- Any backend engine edit (referee / ledger / online_fdr / triad_scan / `evidence.py` / routers); widening the scan or adding candidate hypotheses (discovery completed in iter-10).
- Evidence badges on other research labs (event-study, regime, etc.); a second evidence data path.
