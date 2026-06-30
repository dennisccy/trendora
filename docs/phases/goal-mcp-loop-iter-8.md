# Goal Iteration 8 — Surface the vcp_contraction top-decile certified edge on the Research factor lab + Evidence ledger (J-06)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 8
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05
- **Anti-goal reminders:**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## GOAL

Certify the **vcp_contraction top-decile (D10) horizon-20** out-of-sample forward-return edge through the referee gate, then surface it honestly as a new claim row on `/evidence` and as a "Proven" evidence badge on the Research factor lab's vcp_contraction top-decile cohort — both reading the canonical `GET /api/evidence` verbatim — so the newly-promoted Must-have journey J-06 passes.

## BACKGROUND

J-01..J-05 are all green and the prior verdict was GOAL_ACHIEVED; the continuous-improvement proposer then extended `docs/goal.md` with **J-06**, the only outstanding journey. The proposer first aimed J-06 at the `ma_stack` D10 edge, but the post-decompose referee **REJECTED** it (holdout +0.0262, p=0.0195 ≥ α/4=0.0125 — a decent edge but too high a p under the tightened bar); that rejection is now a permanent **FAIL** ledger entry that raises the Bonferroni divisor. The human operator replayed the referee against the ledger and replaced J-06 in `docs/goal.md` with the **only** backlog cohort that certifies at the current bar — **vcp_contraction** D10 h20 (verified PASS, holdout **+0.0333**, p=**0.01149** < α/4=**0.0125**). Like the iter-4 Breakout-watch claim, `vcp_contraction` is **not a score column**, so the claim is **signal-less**: it backs the Research factor lab and the Evidence ledger ONLY, never a `/stocks` inline score badge. This is depth **full** because it adds a new public-surface badge (factor lab), introduces a new read-side cohort-selector matcher in the shared evidence library that J-01..J-05 all depend on, modifies the shared `/evidence` ClaimRow, and ships a referee-gated Evidence Claim — exactly the cross-surface, shared-contract footprint that warrants the full 11-step pipeline (iter-4, the structural twin, also ran full).

**Lessons applied (from `state/lessons.md`):**
- **iter-1 (Applies to: any iter proposing a `## Evidence Claim` / touching the evidence resolver / `/evidence` / a badge):** proven-ness is keyed on `claim.signal`, and `_resolve_signal` self-maps ONLY the three *score-column* factors. `vcp_contraction` is a plain (volatility-family) factor, so the claim **deliberately carries NO `signal` key** — `_resolve_signal(claim) → None`. It MUST appear only as a `claims[]` row and MUST NOT enter `proven_signals`. Keep `proven_signals == {leadership_score}` after this iteration — assert it in a unit test. Do NOT stamp a `signal` on this claim; doing so would falsely light a `/stocks` score badge and regress J-01/J-02/J-03.
- **iter-3 (Applies to: any iter that browser-verifies a below-the-fold disclosure):** the vcp_contraction claim row is a lower row on `/evidence` (below leadership + Breakout-watch, likely below the fold) and the factor-lab "Proven" badge sits on the vcp_contraction row inside a wide table. The browser-qa-agent MUST scroll each target into the viewport before capturing — a page-top frame is a visual-evidence gap.
- **iter-4/iter-5 (Applies to: the GOAL_ACHIEVED gate + browser-qa harness):** a parallel/secondary QA-lane PASS does NOT substitute for the **canonical browser-qa-agent lane**; `start-frontend.sh` must free the frontend port before binding; confirm the frontend reaches the backend (populated leaderboard / factor-lab data) before scoring; read `engine.log` to locate where any missing artifact actually died.
- **iter-6 (Applies to: verdict gating):** `browser_checks_run` is a DEAD status flag — judge on the canonical `...-ui-test-results.md` + `engine.log`, never on that flag. Any mid-run harness fix must live in the per-step child scripts, not the running parent.

## IN SCOPE

### Evidence Claim (certified by the post-decompose gate BEFORE build — a non-PASS verdict BLOCKS this iteration)

See the `## Evidence Claim` section below: the `vcp_contraction` factor cohort, top decile (D10), horizon 20, claimed positive vs the same-dates SPY control. The JSON intentionally OMITS `signal` (this claim backs no inline per-stock score — it is a plain-factor cohort edge surfaced on the Research factor lab). The human operator pre-verified PASS by replaying the referee against the current ledger (holdout +0.0333, p=0.01149 < α/4=0.0125); the post-decompose gate is the authority and a `FAIL`/`INSUFFICIENT` verdict halts the iteration (see NOTES for handling).

### Backend
- [ ] **No new computation and no new endpoint.** The certified entry the gate appends to `certified-claims.jsonl` is served by the **existing** `app.engine.evidence:build_evidence_payload` → `GET /api/evidence`, which already returns each entry's `claim` cohort selectors (`kind`, `factor`, `slice_kind`, `decile`, `horizon`, `direction`) verbatim, the verdict, and the registration date. Do NOT add a second proven-ness computation or a second endpoint (Data Contract row 1 is canonical).
- [ ] Add a unit test (`apps/backend/tests/test_evidence.py`) asserting that `build_evidence_payload` over the post-certification ledger `[leadership_score PASS, Breakout-watch Risk-on PASS, ma_stack D10 FAIL, vcp_contraction D10 PASS]` returns `proven_signals` keyed **only** on `leadership_score` (the vcp_contraction claim adds NO signal — `_resolve_signal(vcp_contraction claim) → None`) and `claims[]` now includes the vcp_contraction factor row with `proven == true`, `signal == null`, and its cohort selectors verbatim. Assert the FAIL ma_stack entry remains `proven == false` and adds no signal. Assert the served verdict fields (holdout edge, p-value, control excess, registration date) byte-match the ledger line.

### Frontend
- [ ] **Read-side cohort-selector matcher** (`apps/frontend/lib/evidence.ts`) — the signal-less successor to `resolveEvidenceStatus`. A PURE, dependency-free function (e.g. `resolveCohortEvidence(cohort, claims)`) that scans the served `claims[]` for a `proven` (PASS) entry whose `claim` cohort selectors MATCH the queried cohort on `factor` + `slice_kind` + `decile` + `horizon` + `direction`, and returns `{ proven, label ("Proven"|"Not yet proven"), href, claim }`. It NEVER recomputes proven-ness (reads `entry.proven` / `verdict.status == PASS` verbatim) and reads from the SAME `GET /api/evidence` payload — no new fetch path. Fail-safe: no match (or empty/failed claims, or a matched but non-PASS entry like the FAIL ma_stack row) → "Not yet proven", `href: null`.
- [ ] **Deterministic cohort anchor** (`apps/frontend/lib/evidence.ts` + `apps/frontend/app/evidence/page.tsx`). Add a pure `cohortClaimId(cohort)` / `cohortEvidenceAnchor(cohort)` helper that derives a stable `/evidence#…` anchor from a factor cohort's selectors (e.g. `#factor-vcp_contraction-d10-h20`). In `ClaimRow`, set the row `id` to that cohort anchor for a signal-less factor claim (KEEP the existing `signal-${signal}` anchor for score rows — J-02/J-05 deep-links unchanged) so the factor-lab "Proven" badge can deep-link to its backing row.
- [ ] **Honest factor-cohort title + linkback** (`apps/frontend/lib/evidence.ts` `claimSurface`, consumed by `/evidence` `ClaimRow`). Add a `kind === "factor"` branch for a signal-less factor cohort: a meaningful title (e.g. `"vcp_contraction — top decile (D10)"` derived from the cohort selectors, NOT the misleading "Unmapped signal"), an honest *historical evidence* subtitle (e.g. `"Out-of-sample edge — factor top decile"` — never a buy/sell or return promise), and a **"Backs: Research factor lab →"** linkback to `/research/factor-lab` (NOT the Stocks leaderboard). KEEP the score-signal branch (leadership row title + "Stocks leaderboard" linkback) and the event-study branch (J-04/J-05) **byte-identical**.
- [ ] **Evidence badge on the factor-lab top-decile rows** (`apps/frontend/app/research/_labs.tsx` `FactorLabPage` / its top-decile summary row, `apps/frontend/app/research/factor-lab/page.tsx`). Fetch the canonical evidence payload via the **existing** `fetchEvidence()` client (`lib/api.ts` — reuse it, do NOT add a new fetch). For each factor's top-decile (D10) cohort at the certified horizon (20), render an `EvidenceStatusBadge`-style chip resolved via `resolveCohortEvidence`: **vcp_contraction → "Proven"** (linking to its ledger row via `cohortEvidenceAnchor`), every unbacked factor → **"Not yet proven"** (anti-goal #1 — never a confident-looking unbacked cohort; no link). The badge re-displays the served status — it computes nothing.

### New user-facing capability
For the first time the user can see a **plain-factor** (non-score) edge marked "Proven" on the Research factor lab — the vcp_contraction top-decile cohort's certified out-of-sample edge — and click straight through to its auditable ledger entry on `/evidence`.

### New information displayed
A new certified-claims row on `/evidence` for the vcp_contraction top-decile cohort (hypothesis chips, out-of-sample verdict ≈ +3.33% / p ≈ 0.01149, control vs SPY, registration date, forward-walk score-to-date, "Backs: Research factor lab →"); and on `/research/factor-lab`, a "Proven"/"Not yet proven" evidence badge on each factor's top-decile cohort (vcp_contraction reads "Proven").

### New user actions
On `/research/factor-lab`, click the vcp_contraction top-decile "Proven" badge to jump to its backing entry on `/evidence`; on `/evidence`, follow the vcp_contraction row's "Backs: Research factor lab →" linkback back to the lab.

### UI surface changes
`/research/factor-lab` factor-lab top-decile rows gain an evidence status badge; `/evidence` `ClaimRow` gains a factor-cohort honest title/subtitle/linkback and a cohort-derived anchor. **No new pages, no nav change.**

### Product surface delta
The evidence layer crosses from "proven scores + one regime-conditioned setup edge" to **proven research-lab factor cohorts** — the Research factor lab now distinguishes the one factor decile that survived the referee from the many that have not (including ma_stack, which honestly reads "Not yet proven" after its FAIL), delivering goal.md Key Capability 1 (evidence badges on every score/ranking surface, now extended to the factor lab) for the J-06 cohort.

### Blueprint conformance
No new surfaces or nav. J-06's home is the **Research factor lab** (`/research/factor-lab`, already under the existing **Research** nav section as a row/link-reached lab) plus the existing **Evidence** ledger (`/evidence`). The factor-lab badge and the `/evidence` factor ClaimRow are additional **readers** of the already-registered `GET /api/evidence` payload. The blueprint's J-06 IA row and "iter-8 clarification" have been corrected from the rejected `ma_stack` to `vcp_contraction` (Data Contract row 1 now also covers signal-less plain-factor decile cohort claims read via a cohort-selector matcher) — **additive edits only, no nav-skeleton change ⇒ no re-approval required**.

### Data-contract additions
**None.** No new displayed value. The vcp_contraction claim is another entry in the **same** certified-claims ledger (Data Contract row 1: "Evidence status + certified-claim"), computed once by the referee and served by the single canonical `GET /api/evidence`; the factor-lab badge and the `/evidence` factor row are additional readers that MATCH the served `claims[]` on cohort selectors and re-display the verdict verbatim. No new computing module, no second endpoint, no recompute, no nav-skeleton change.

## Evidence Claim

```json
{"kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10, "horizon": 20, "direction": "positive"}
```

The post-decompose gate runs this through the referee (sealed temporal holdout + same-dates SPY control + multiple-testing deflation) and appends the verdict to `runs/goal-session-mcp-loop/state/certified-claims.jsonl`. The ledger currently holds **3** entries (leadership_score PASS, Breakout-watch Risk-on PASS, **ma_stack D10 FAIL**); vcp_contraction is **trial #4 ⇒ Bonferroni divisor 4, required_p ≈ 0.05/4 = 0.0125**. The human operator's referee replay against this exact ledger returned PASS (holdout edge +0.0333, p=0.01149 < 0.0125). The JSON intentionally OMITS `signal` (this claim backs no inline per-stock score — `_resolve_signal → None`). A `FAIL`/`INSUFFICIENT` verdict **blocks** the iteration; never loosen the referee to force a PASS, and never substitute another factor (the human has already established vcp_contraction is the only backlog cohort that certifies at this bar).

## OUT OF SCOPE

- **Stamping a `signal` on the vcp_contraction claim / lighting an inline `/stocks` score badge.** This claim backs no per-stock score; it must NOT enter `proven_signals` nor light/overwrite the leadership "Proven" badge. J-06 is satisfied on the factor lab + Evidence surfaces only.
- **Re-proposing or certifying `ma_stack`, `hv`, or `high_proximity`.** They FAIL the referee and each failed submission permanently raises the Bonferroni bar (ma_stack is already a FAIL ledger entry). Only vcp_contraction is in scope.
- **Badging the full D1…D9 decile grid cells, the regime/sector/theme labs, or any non-vcp_contraction surface.** Only the factor-lab top-decile (D10) summary rows get an evidence badge this iteration (vcp_contraction "Proven", others "Not yet proven").
- **Proving Entry Quality or Risk, a second/broader factor, or any other proposer backlog cohort.**
- **Any change to the three scores, the regime/forward-return/factor-lab engines, the referee, or `GET /api/evidence`'s shape**; a second proven-ness computation or a second evidence endpoint (forbidden — Data Contract row 1 is canonical).
- **Multi-control enrichment (QQQ / sector ETF / random same-sector).** The referee certifies against the SPY benchmark control; the row shows that control honestly labeled "vs SPY".

## DEFINITION OF DONE

- [ ] The post-decompose gate returns **PASS** for the Evidence Claim and the vcp_contraction entry is appended to `certified-claims.jsonl` (4th ledger entry).
- [ ] **J-06 passes via browser-qa-agent** with real screenshots: (a) `/evidence` renders the new vcp_contraction claim row with the same fields as the existing rows (hypothesis, out-of-sample verdict, control vs SPY, registration date, forward-walk score-to-date) and a "Backs: Research factor lab →" linkback, scrolled into the viewport before capture; (b) `/research/factor-lab` shows the vcp_contraction top-decile cohort with a "Proven" badge that links to the ledger entry. Displayed out-of-sample edge / p-value / control comparison **byte-match** `GET /api/evidence` (and the certified-claims.jsonl line) for the same as-of.
- [ ] **Required-still-passing J-01/J-02/J-03/J-04/J-05 remain green:** leadership reads "Proven" on `/stocks` + stock detail, Entry Quality + Risk still "Not yet proven" (J-01/J-03); the leadership proof drill-down still shows its OOS test/SPY control/claim id+date (J-02); the Breakout-watch row stays "Regime: Risk-on" with its event-study linkback (J-04); the leadership `/evidence` row + "Backs: Stocks leaderboard →" linkback are unchanged and round-trip (J-05). A unit assertion confirms `proven_signals` stays exactly `{leadership_score}` after the vcp_contraction claim is added.
- [ ] **No anti-goal violation:** the vcp_contraction cohort is shown as out-of-sample *evidence* (holdout edge / control / significance), never a buy/sell or return promise; nothing uncertified reads "Proven" (every unbacked factor-lab top-decile — including the FAIL'd ma_stack — reads "Not yet proven"); displayed numbers match `GET /api/evidence`; determinism/no-lookahead untouched (zero engine diff); no secrets.
- [ ] **Unit tests pass; no regression** in `/api/evidence` shape or the evidence library. New/updated tests cover: `resolveCohortEvidence` (match on full selectors → "Proven" + href; selector mismatch / non-PASS / empty → "Not yet proven", no href); the `claimSurface` factor branch (honest title + "Research factor lab" linkback) with the score + event-study branches unchanged; `cohortClaimId`/`cohortEvidenceAnchor` stability; and the backend `build_evidence_payload` post-certification assertion above.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-8-dev.md`.
- [ ] **Post-QA audit handoff produced** at `docs/handoffs/goal-mcp-loop-iter-8-audit.md` (full pipeline must complete the audit stage).
- [ ] A `[NEW]`-flagged demo-narrator walkthrough of the vcp_contraction ledger row + the factor-lab "Proven" badge is produced (plain-language narration + a real-data screenshot), viewable via `demo.sh mcp-loop --session-live`.

## TESTING REQUIREMENTS

- **Browser (must verify, by ID):**
  - **J-06** — `/research/factor-lab`: assert the vcp_contraction top-decile cohort shows a "Proven" badge (scrolled into frame) and clicking it deep-links to the vcp_contraction row on `/evidence`. `/evidence`: assert the vcp_contraction claim row renders the five fields + "Backs: Research factor lab →", and its holdout edge / control vs SPY / register date match `GET /api/evidence` (API-correctness check). Assert at least one OTHER factor top-decile row reads "Not yet proven".
  - **J-01 / J-03** (regression) — `/stocks`: every score still shows a status; Leadership "Proven", Entry Quality + Risk "Not yet proven"; no vcp_contraction-induced inline badge appears.
  - **J-02** (regression) — `/stocks/{ticker}`: the Leadership proof drill-down still shows the OOS test, SPY control, and claim id/date.
  - **J-04** (regression) — `/` → `/evidence`: the Breakout-watch row is still labeled "Regime: Risk-on" with its event-study linkback.
  - **J-05** (regression) — `/evidence`: the leadership row (5 fields) + "Backs: Stocks leaderboard →" still render and round-trip; the new vcp_contraction row does not break the list.
- **Unit/integration:**
  - `resolveCohortEvidence`: a cohort matching a PASS `claims[]` entry on `factor`+`slice_kind`+`decile`+`horizon`+`direction` → `{proven:true, label:"Proven", href}`; any selector mismatch, a matched-but-non-PASS entry (e.g. the FAIL ma_stack row), or an empty/failed list → `{proven:false, label:"Not yet proven", href:null}`.
  - `claimSurface`: a signal-less `kind:"factor"` cohort → honest factor title + "Research factor lab" linkback (`/research/factor-lab`); the score-signal row and the event-study row are byte-identical to today.
  - `cohortClaimId`/`cohortEvidenceAnchor` produce a stable, collision-free anchor; `ClaimRow` uses it for a signal-less factor claim and keeps `signal-${signal}` for score rows.
  - Backend `build_evidence_payload` over the post-certification ledger: `proven_signals == {leadership_score}`; `claims[]` includes the vcp_contraction factor row (`proven:true`, `signal:null`, selectors verbatim) and the ma_stack row (`proven:false`); `_resolve_signal(vcp_contraction claim) → None`.
- **Error cases:** an absent/empty/unreadable ledger still yields `{"claims": [], "proven_signals": {}}` (200, never 500) and every factor-lab top-decile badge reads "Not yet proven", no link; a factor with no matching PASS claim (including ma_stack's FAIL row) renders "Not yet proven" (no crash, no fabricated href).

## NOTES

- **Why signal-less is correct here (iter-1 lesson, central):** `vcp_contraction` ∉ `_SCORE_COLUMN_FACTORS` (`{leadership_score, entry_quality_score, risk_score}`), so `_resolve_signal` returns `None` and the claim cannot enter `proven_signals` — it backs the factor lab via the new cohort-selector matcher, not a `/stocks` score badge. This is exactly the iter-4 pattern (Breakout-watch event-study claim → Research event-study lab) generalized to a plain-factor decile cohort. Do NOT add a `signal` to the Evidence Claim JSON.
- **Gate is the authority; do NOT substitute on FAIL.** The referee is deterministic given the gate's exact cumulative `RefereeState` (this is trial #4 ⇒ divisor 4, required_p ≈ 0.0125) and seed against the committed seed data; the human operator's replay against this exact ledger returned PASS (holdout +0.0333, p=0.01149 < 0.0125). If the gate ever returns FAIL/INSUFFICIENT (it should not), do NOT loosen the referee and do NOT swap in another factor — ma_stack/hv/high_proximity all fail this bar and the human has already established vcp_contraction is the only certifying cohort. Halt and surface to the operator instead.
- **Anti-goal #2 framing.** Present the vcp_contraction edge as *historical, out-of-sample evidence* ("this factor's top decile beat SPY out-of-sample over the sealed holdout dates"), never as "buy these now." Keep the existing "Research-only · decision support · no orders" posture.
- **On completion:** with J-06 passing and J-01..J-05 still green, all six Must-have journeys are green and the `<!-- AUTO:journeys -->` block carries no further unbuilt scope — the goal-evaluator can re-assess GOAL_ACHIEVED.
- Sources grounding this spec: `apps/backend/app/engine/evidence.py` (`_resolve_signal` → None for non-score factor cohorts, `_SCORE_COLUMN_FACTORS`, `build_evidence_payload`); `apps/backend/app/config.py` (`FACTOR_TYPED_COLUMNS` — vcp_contraction is in the volatility-family columns, NOT a score column); `apps/frontend/lib/evidence.ts` (`resolveEvidenceStatus`, `claimSurface` with its score + event-study branches + "Unmapped signal" fallback, `evidenceAnchor`, `regimeLabel`); `apps/frontend/app/evidence/page.tsx` (`ClaimRow`, anchor `id`, `claimSurface` consumer); `apps/frontend/app/research/_labs.tsx` + `app/research/factor-lab/page.tsx` (the top-decile summary row); `apps/frontend/lib/api.ts` (`fetchEvidence` — the existing canonical evidence client to reuse); `apps/frontend/components/evidence-status-badge.tsx` (the badge pattern); `runs/goal-session-mcp-loop/state/certified-claims.jsonl` (the 2 existing PASS entries + the ma_stack FAIL; vcp_contraction is the 4th).
