# Goal Iteration 11 — Surface J-07: promote vcp_contraction D10 @ h60 to canonical, per-horizon factor-lab "Proven" badge

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 11
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-06, J-05, J-01, J-02, J-03, J-04
- **Anti-goal reminders:**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## GOAL

A user opening `/research/factor-lab` sees the `vcp_contraction` top-decile cohort marked **"Proven" at the 60-day horizon** (deep-linking to a new certified-claim row on `/evidence`), while its uncertified horizons (1/5/10-day) honestly read **"Not yet proven"** — the loop's first surfaced edge beyond the 20-day window.

## BACKGROUND

iter-10 delivered J-07's discovery prerequisite: it opened the multi-horizon aperture and ran the pre-registered candidate set through the referee into the INTERNAL staging ledger, producing three canonical-bar-clearing winners. This iteration promotes exactly one of them — the **signal-less `vcp_contraction` D10 @ h60** winner (block-bootstrap p = 0.0004997501249375312 < the canonical divisor-5 bar 0.010; modest, credible holdout edge +8.91%) — to the canonical `certified-claims.jsonl` via an explicit `"ledger":"canonical"` Evidence Claim, then surfaces it on `/evidence` + a **per-horizon** factor-lab badge. Depth is **full** because it ships a NEW referee-gated canonical "Proven" claim (permanently tightens the user-facing Bonferroni bar to divisor 6) plus a new public-surface badge — the exact high-stakes write that needs the auditor (mirrors the iter-8 J-06 pattern that went full + browser-verified). The evaluator's iter-10 recommendation drives this scope verbatim.

**Why vcp_contraction h60 and not the alternatives (iter-10 lesson — surfaced here):** all three staging PASSes sit at the block-bootstrap p-FLOOR (0.00049975), so p cannot rank them — the `holdout_edge` magnitude is the tiebreaker. `rs_spy_3m` h60's +0.2134 edge is implausibly large (auditor flagged it as a p-floor PASS to scrutinize) and `leadership_score` h60 is the config-declared FALLBACK (a score-column factor). The modest, credible **signal-less** `vcp_contraction` +0.089 is the correct promotion.

**Applied lessons (episodic memory — see NOTES for full text):** iter-9b/iter-10 mechanical traps (the claim MUST set `"ledger":"canonical"` explicitly, and promote only a candidate whose raw p already clears required_p=0.010 — both satisfied); iter-8 (`resolveCohortEvidence` lights EVERY certified cohort it matches — leadership_score h20 reading "Proven" is HONEST, do not special-case; assert the badge deep-links to the row's REAL `claimAnchorId`); iter-3 (a below-the-fold/expander screenshot proves nothing unless the element is scrolled into frame); iter-1 (this claim is intentionally signal-less — it must NOT enter `proven_signals` or light a `/stocks` badge).

## IN SCOPE

### Backend / data (no developer engine code — produced by the post-decompose gate)
- [ ] The post-decompose gate certifies the `## Evidence Claim` below (`"ledger":"canonical"`) through the referee BEFORE any code is built, appending a 5th entry to `runs/goal-session-mcp-loop/state/certified-claims.jsonl`. Expected canonical verdict (edge / p / control are data properties reproduced from staging; deflation fields are the canonical Bonferroni re-run): `status=PASS`, `holdout_edge≈+0.08910` (+8.91%), `control_excess≈+0.08910` (beats SPY OOS), `p_value=0.0004997501249375312`, `deflation="bonferroni"`, `deflation_divisor=5`, `required_p=0.010`, `cohort_n=12026`, `control_n=1055`, `horizon=60`, NO `signal` key. A non-PASS verdict BLOCKS the iteration (fail-closed).
- [ ] Verify `GET /api/evidence` serves the new entry verbatim in `claims[]` and that `proven_signals` stays exactly `{leadership_score}` (the signal-less claim MUST NOT enter it). No change to `app.engine.evidence`, any router, referee, ledger, or triad_scan — the existing endpoint reads the ledger the gate wrote.

### Frontend
- [ ] Render the factor-lab top-decile evidence badge **per horizon** (each horizon in the served vocabulary `[1,5,10,20,60]`) instead of only at `defaultHorizon`. Each horizon `h` resolves its own status via the EXISTING `resolveCohortEvidence({factor: row.key, slice_kind:"decile", decile: topDecile, horizon: h, direction:"positive"}, evidenceClaims)` — the SAME matcher reading the SAME `GET /api/evidence` payload (no new fetch path, no recompute). Result on the `vcp_contraction` row: h60 → "Proven" deep-linking to `/evidence#factor-vcp_contraction-d10-h60`; h1/h5/h10 → "Not yet proven"; **h20 → "Proven" (unchanged — J-06 must not regress)**.
- [ ] Extend `FactorEvidenceBadge` to carry `data-horizon={horizon}` alongside the existing `data-testid="factor-evidence-badge"` / `data-proven` / `data-factor`, so each per-horizon badge is independently selectable by browser-qa (e.g. `[data-factor="vcp_contraction"][data-horizon="60"]` → `data-proven="true"`; `[data-horizon="10"]` → `data-proven="false"`). Placement: the per-horizon badges must be VISIBLE on the factor-lab surface aligned with the forward-return horizon columns (developer's choice of a compact per-horizon chip strip vs. per-column badge). If any badge is rendered inside the click-to-expand decile grid, browser-qa MUST open it and scroll it into the viewport before capture (iter-3 lesson).
- [ ] (Small, display-only) In `lib/evidence.ts` `claimSurface`, disambiguate the signal-less factor-cohort subtitle by the horizon (e.g. `"Out-of-sample edge — factor top decile · 60-day hold"`) so the new h60 `/evidence` row is self-distinguishing from the existing h20 vcp_contraction row. The load-bearing horizon signal is already the `horizon=60` hypothesis chip; this is clarity polish. Keep the h20 row's existing wording behavior intact.

### New user-facing capability
The user can audit an out-of-sample-proven factor edge at a **non-20-day horizon** end-to-end: see it "Proven" on the factor lab at h60, click through to its certified-claim row, and see every other horizon honestly marked "Not yet proven".

### New information displayed
A new `/evidence` certified-claim row for `vcp_contraction — top decile (D10)` at horizon 60 (PASS, +8.91% holdout, +8.91% vs SPY, registration date, forward-walk pending, "Backs: Research factor lab →"), and per-horizon "Proven"/"Not yet proven" evidence badges on the factor-lab factor rows.

### New user actions
Click the factor-lab h60 "Proven" badge to deep-link to its backing `/evidence` row (`stopPropagation` guards the row's expand toggle, as the existing badge does).

### UI surface changes
`/research/factor-lab` (per-horizon evidence badges) and `/evidence` (one additional auto-rendered claim row). No new pages, no nav change.

### Product surface delta
The factor lab evolves from a single-horizon (h20) evidence marker to an honest per-horizon evidence view; the Evidence ledger gains its first non-20-horizon certified claim.

### Blueprint conformance
J-07's canonical home is already registered in `blueprint.md` Information Architecture: `/research/factor-lab` (non-20-horizon cohort "Proven" badge → its ledger row) + the non-20-horizon claim row on `/evidence`. Both routes already exist; no new page, no nav-skeleton change. An additive iter-11 clarification is appended to the blueprint Data Contract (no new value row, no reapproval).

### Data-contract additions
**None.** The h60 claim is a NEW ENTRY in the EXISTING `certified-claims.jsonl` (the already-registered "Evidence status + certified-claim" contract value), served by the EXISTING `GET /api/evidence`, read by the EXISTING `resolveCohortEvidence` matcher — one more reader position (the factor-lab badge, now per-horizon), NOT a new computing module or serving endpoint. Do NOT introduce a second evidence path.

## OUT OF SCOPE

- **J-08** (multi-factor combination on `/research/factor-combination`) — deferred to iter-12+ per goal.md Part B sequencing.
- Promoting `rs_spy_3m` h60 (implausible +0.21 p-floor edge) or `leadership_score` h60 (the config-declared FALLBACK / score-column factor) — only `vcp_contraction` h60 is promoted this iteration.
- Any inline `/stocks` badge for the signal-less h60 claim, or any change to `proven_signals` / the per-stock score badges (`{leadership_score}` stays) — the signal-less claim backs the factor lab ONLY (anti-goal #1 honesty; J-01/J-02/J-03 unaffected).
- Any backend engine edit (referee / ledger / online_fdr / triad_scan / `evidence.py` / routers) — the promotion is entirely via the gate + the Evidence Claim.
- Widening the scan or adding new candidate hypotheses (discovery already completed in iter-10).
- Evidence badges on other research labs (event-study, regime, etc.).

## DEFINITION OF DONE

- [ ] The post-decompose gate certifies the canonical vcp_contraction D10 h60 Evidence Claim **PASS** (Bonferroni divisor 5, required_p=0.010) before build; `certified-claims.jsonl` gains the 5th entry.
- [ ] Target journey **J-07 passes via browser-qa-agent** (canonical lane, `reports/phase-goal-mcp-loop-iter-11-ui-test-results.md`): the `/evidence` h60 row renders all standard fields with the horizon visible; the factor-lab `vcp_contraction` h60 top-decile badge reads "Proven" and deep-links to `/evidence#factor-vcp_contraction-d10-h60`; h1/h5/h10 read "Not yet proven".
- [ ] Required-still-passing journeys remain green: **J-06** (vcp_contraction h20 badge still "Proven"; the h20 `/evidence` row unchanged), **J-05** (all prior 4 claim rows render unchanged; new row is additive), **J-01/J-02/J-03** (`proven_signals` stays `{leadership_score}`; no `/stocks` inline badge for the h60 claim; score badges unchanged), **J-04** (Breakout-watch regime row unchanged).
- [ ] No anti-goal violation introduced (all seven); the displayed h60 edge/p/control byte-match `certified-claims.jsonl` L5; no return/price/buy-sell language; determinism + no-lookahead preserved; no secrets.
- [ ] Unit tests pass; no regressions.
- [ ] Demo-narrator `[NEW]`-flagged walkthrough of the h60 row + per-horizon badge produced (J-07 "Walkthrough" acceptance), viewable via `demo.sh mcp-loop --session-live`.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-11-dev.md`.

## TESTING REQUIREMENTS

- **Browser (canonical browser-qa-agent lane — REQUIRED, Frontend Present: yes):**
  - **J-07** — `/evidence`: locate the NEW `vcp_contraction` D10 row whose hypothesis shows `horizon=60`; assert PASS, holdout edge +8.91%, control vs SPY +8.91%, a registration date, forward-walk "Pending", and "Backs: Research factor lab →". `/research/factor-lab`: assert the `vcp_contraction` row's h60 top-decile badge (`[data-factor="vcp_contraction"][data-horizon="60"]`) reads "Proven" and its href is `/evidence#factor-vcp_contraction-d10-h60`; assert h1/h5/h10 badges read "Not yet proven". Scroll each asserted badge into the viewport before capture (iter-3 lesson).
  - **J-06 (regression)** — the `vcp_contraction` h20 badge (`[data-horizon="20"]`) still reads "Proven" and deep-links to `/evidence#factor-vcp_contraction-d10-h20`.
  - **J-05 (regression)** — `/evidence` still lists the prior four rows (leadership_score PASS, Breakout-watch PASS, ma_stack FAIL, vcp_contraction h20 PASS) plus the new h60 row; each linkback works.
  - **J-01/J-03 (regression)** — `/stocks` leaderboard rows still show Leadership "Proven" and Entry Quality / Risk "Not yet proven"; no new inline badge from the signal-less h60 claim.
- **Unit / integration (frontend `apps/frontend/lib/evidence.test.ts` + component tests):**
  - `resolveCohortEvidence` for `{vcp_contraction, decile:10, horizon:60, positive}` against a served payload containing the h60 PASS → proven, href `/evidence#factor-vcp_contraction-d10-h60`; for `horizon:10` → not proven, no href; for `horizon:20` → proven (h20 entry). `cohortClaimId`/`claimAnchorId` produce the horizon-distinct `factor-vcp_contraction-d10-h60` anchor.
  - `formatEvidencePct(0.08909719710495288)` → `"+8.91%"`; `claimSurface` horizon-disambiguated subtitle for the h60 factor cohort.
  - Per-horizon `FactorEvidenceBadge` renders `data-horizon` and the correct `data-proven` per horizon; a matched-but-non-PASS entry (ma_stack FAIL) stays "Not yet proven".
- **Error cases:** an uncertified horizon (h1/h5/h10) resolves "Not yet proven" (never a fabricated "Proven"); an empty/failed `fetchEvidence` leaves every badge "Not yet proven" with no link; a matched-but-non-PASS ledger entry never lights "Proven".

## Evidence Claim

```json
{"kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10, "horizon": 60, "direction": "positive", "ledger": "canonical"}
```

The gate routes `"ledger":"canonical"` to `certified-claims.jsonl` (strict Bonferroni). This claim is intentionally **signal-less** (no `signal` key) so it backs the Research factor lab ONLY and never lights or overwrites a `/stocks` inline score badge (anti-goal #1; J-01/J-02/J-03 unaffected). A non-PASS verdict BLOCKS the iteration.

## NOTES

- **iter-9b / iter-10 mechanical traps (both satisfied here):** (1) the gate defaults an omitted `"ledger"` key to `staging` — a badge-bound winner that forgets `"ledger":"canonical"` is silently re-certified into staging and NEVER surfaces on `/evidence` or the factor lab (no gate error). The Evidence Claim above sets it explicitly. (2) A canonical PASS permanently appends to `certified-claims.jsonl` and tightens the user-facing Bonferroni divisor (5→6) forever, so only a candidate whose recorded raw p already clears required_p=0.010 may be promoted — vcp_contraction h60's p=0.00049975 clears it with large margin (the iter-8 ma_stack bar-tightening disaster is the counter-example: never promote a marginal candidate).
- **iter-8 lesson (allow, don't suppress):** the per-horizon `resolveCohortEvidence` will also light `leadership_score` at h20 as "Proven" if it appears as a factor row — this is HONEST (it has a genuine PASS canonical entry, L1) and correct (anti-goal #1 only bans UNBACKED "Proven"). Do NOT special-case the matcher to vcp-only. Assert each "Proven" badge deep-links to its row's REAL `claimAnchorId` (a signal-less factor → its `factor-…-h…` cohort anchor; a score-column factor like leadership_score → its `signal-leadership_score` anchor, which its `/evidence` row actually carries).
- **iter-3 lesson:** a factor-lab table is wide and the h60 column / any expander sits below or to the right of the fold — a screenshot named for the h60 badge proves nothing unless that badge was scrolled into the viewport first. Corroborate with the independent same-value `/evidence` row render + a confirmed in-component deep-link.
- **Browser-lane operational reminders (iter-2/4/5/6):** this iteration REQUIRES the canonical `browser-qa-agent` lane to actually run and write `reports/phase-goal-mcp-loop-iter-11-ui-test-results.md` (a real badge flip, not a backend-only SKIP). Ensure the frontend can reach the backend and free port :3255 before the browser lane binds; if a verification artifact is missing, read `engine.log` for where the pipeline died (do not trust the dead `browser_checks_run` flag or QA-parallel-lane screenshots as the canonical evidence).
- **Non-regression proof for the untouched surfaces:** `proven_signals` must stay byte-identical `{leadership_score}` and the four prior canonical rows must be unchanged — the h60 claim is purely additive. The frontend evidence unit suite (`evidence.test.ts`) should stay green with only additive edits.
- **Forward pointer:** iter-12+ promotes a PRE-REGISTERED 2-factor combination → J-08 on `/research/factor-combination` + `/evidence`; it will face Bonferroni divisor 6 (required_p=0.00833) after this iteration's canonical write. GOAL_ACHIEVED becomes reachable once both J-07 (this iter) and J-08 land browser-verified.
