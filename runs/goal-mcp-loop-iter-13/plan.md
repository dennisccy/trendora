# goal-mcp-loop-iter-13 Execution Plan

**Type:** frontend-only surfacing of **J-08** (the LAST Must-have journey). Depth: full.
**Goal alignment:** exactly `docs/goal.md` J-08 — surface the first referee-certified **2-factor
combination** edge (composite cohort) as a "Proven" badge on `/research/factor-combination` + a new
`/evidence` claim row, both reading the SAME `GET /api/evidence` payload. No drift from the goal; no
scope creep detected. Landing this browser-verified with J-01..J-07 non-regressed makes GOAL_ACHIEVED
reachable (the evaluator's call, not this spec's).

**Data precondition — ALREADY DONE by the post-decompose gate (verified on disk, do NOT re-do):**
`runs/goal-session-mcp-loop/state/certified-claims.jsonl` now holds **6 entries**; row 6 is the
promoted combination PASS:
`{"kind":"combination","cohort":"composite","condition":["rs_spy_3m:top:quintile","high_proximity:top:tertile"],"horizon":20,"direction":"positive","ledger":"canonical"}`
→ `status=PASS`, `holdout_edge≈+0.04693` (+4.69%), `control_excess≈+0.04693` (beats SPY OOS),
`p_value=0.0009995002498750624`, `deflation="bonferroni"`, `deflation_divisor=6`,
`required_p≈0.008333`, `register_date=2026-07-01`, **no `signal` key**. The prior 5 rows are
byte-identical. The developer builds against the 6-entry ledger and MUST NOT edit/reorder it. Honest-stop
guard is already satisfied (verdict is PASS). `build_evidence_payload` re-displays row 6 into `claims[]`
verbatim and `_resolve_signal` returns `None` for `kind=combination`, so `GET /api/evidence` already
serves it with `signal:null, proven:true` and it is ABSENT from `proven_signals` (stays `{leadership_score}`).

## What to Build

- **`lib/evidence.ts` — the read-side combination matcher (the core, all PURE/no-React/no-fetch):**
  - `CombinationCohort` type: `{ kind:"combination", cohort:"composite", condition: string[], horizon: number, direction: string }`.
  - `combinationCohortFromClaim(claim)` — sibling of `factorCohortFromClaim`; extracts/validates
    (kind=combination, cohort=composite, `condition` a non-empty `string[]`, numeric `horizon`,
    non-empty `direction`), else `null`.
  - `resolveCombinationEvidence(cohort, claims)` — sibling of `resolveCohortEvidence`; scans served
    `claims[]` for a `proven===true` (PASS) entry matching on `kind=combination` + `cohort=composite` +
    the **`condition` leg-set order-independent** (compare sorted full leg strings — NOT just factor keys) +
    `horizon` + `direction`. Returns `{proven:true, label:"Proven", href:"/evidence#<anchor>", claim}` on
    a PASS match, else `{proven:false, label:"Not yet proven", href:null, claim:null}`. NEVER recomputes
    proven-ness (a matched-but-non-PASS entry stays "Not yet proven"); reads the SAME payload — no new
    fetch path.
  - Combination anchor id (sibling of `cohortClaimId`) — deterministic, order-independent (from the
    **sorted** legs + horizon), collision-free, `combination-`-prefixed (so it is DISTINCT from any
    `factor-…` anchor), e.g. `combination-high_proximity-rs_spy_3m-h20`. The only hard requirement is
    that the badge href and the `/evidence` row `id` come from the SAME function so the deep-link lands.
  - Extend `claimAnchorId(claim)` — return the combination anchor for a combination claim (currently it
    returns `null`, so the `/evidence` row carries no `id` and the badge deep-link cannot land).
  - Extend `claimSurface(claim)` — add a `combination` branch: an honest composite title naming the two
    legs, a historical-evidence subtitle (NEVER a return/buy-sell promise), `href:"/research/factor-combination"`,
    label `Multi-factor combination lab` (replacing the misleading "Unmapped signal" fallback for this claim).
- **`app/research/_labs.tsx` — the composite-cohort "Proven" badge:**
  - Add the served evidence `claims[]` to the combination lab by REUSING the existing `fetchEvidence`
    client (mirror `FactorLabPage`'s pattern at ~lines 194-217) in `CombinationLab` (line 1086) /
    `CombinationLabPage` (line 3557); thread `evidenceClaims` into `CombinationTable` (line 1401).
  - In `CombinationTable`, build the `CombinationCohort` from the ALREADY-computed `conditions`
    (lines 1414-1416, `${factor}:${side}:${quantile}` — the exact byte-format of the served claim's legs)
    + `horizon` (line 1411) + `direction:"positive"` (the composite is the only/positive direction), resolve
    via `resolveCombinationEvidence`, and render an evidence badge on the composite row (line 1466,
    `data-testid="combination-row-composite"`). Give the badge `data-testid` + `data-proven` (+ enough of
    the selected legs/horizon to be independently selectable by browser-qa).
- **`app/evidence/page.tsx` — NO structural change.** The combination `ClaimRow` renders automatically:
  `claimSurface`/`claimAnchorId` (extended above) supply the title/linkback/anchor, and the existing
  `ClaimHypothesis` already renders every selector chip (`condition`, `kind`, `horizon`, `direction`,
  `cohort`, `ledger`) verbatim. Do NOT add a bespoke combination branch here.
- **Frontend tests** (`lib/evidence.test.ts`) — see Key Test Scenarios.
- **Backend — NO app code change.** Optional TEST-ONLY assertion in `apps/backend/tests/test_evidence.py`
  (mirrors iter-8/iter-11): `GET /api/evidence` includes the combination row verbatim with `signal:null,
  proven:true`, and it is ABSENT from `proven_signals` (`{leadership_score}`). Zero `app/**` change.
- **Demo-narrator `[NEW]`-flagged walkthrough** of the combination `/evidence` row + composite badge
  (pipeline step; non-gating) and the **dev handoff** at `docs/handoffs/goal-mcp-loop-iter-13-dev.md`.

## Agents Required
- developer: yes -- this project's single implementer performs all frontend work below (+ optional test-only backend assertion).
- backend-data: no -- the 6th canonical ledger entry was written by the post-decompose GATE (already on disk); NO engine/referee/ledger/online_fdr/triad_scan/`evidence.py`/`api/evidence.py` edit. Only optional touch: a TEST-ONLY payload assertion in `test_evidence.py`.
- frontend-ux: yes -- the core of the iteration (`resolveCombinationEvidence` in `lib/evidence.ts`; the composite "Proven" badge on `/research/factor-combination`; the additive `/evidence` row renders via the existing `ClaimRow`).

(The pipeline also runs reviewer / QA / **auditor** / browser-qa automatically. The AUDITOR MUST run —
this ships a NEW canonical "Proven" claim + a new public badge, the high-stakes write that needs the
audit, mirroring iter-8/iter-11. The canonical `browser-qa-agent` lane MUST actually run and write
`reports/phase-goal-mcp-loop-iter-13-ui-test-results.md` — a real badge flip, not a backend-only SKIP.)

## Frontend Present

Frontend Present: yes

The iteration flips a user-facing badge and adds a visible `/evidence` row. Chrome MCP browser checks are
REQUIRED (canonical browser-qa lane). Free the frontend port and confirm the frontend can reach the
backend BEFORE the browser lane binds (iter-2/iter-4/iter-5); if a verification artifact is missing, read
`runs/goal-session-mcp-loop/engine.log` for where the pipeline actually died (iter-6).

## Files to Create/Modify
- `/home/dennis-chan/Git/trendora/apps/frontend/lib/evidence.ts` -- `CombinationCohort` type; `combinationCohortFromClaim`; `resolveCombinationEvidence`; combination anchor id; extend `claimAnchorId` + `claimSurface` (combination branch). No change to the score/event-study/factor branches.
- `/home/dennis-chan/Git/trendora/apps/frontend/lib/evidence.test.ts` -- add combination coverage (see Key Test Scenarios). Do NOT weaken existing factor/event-study/score cases.
- `/home/dennis-chan/Git/trendora/apps/frontend/app/research/_labs.tsx` -- fetch `fetchEvidence` claims in the combination lab; thread into `CombinationTable`; render the composite-cohort evidence badge with `data-testid`/`data-proven`.
- `/home/dennis-chan/Git/trendora/apps/backend/tests/test_evidence.py` (OPTIONAL, test-only) -- assert the served payload contains the 6th (combination) entry verbatim with `signal:null, proven:true`, and `proven_signals == {leadership_score}`. No `app/**` change.
- `/home/dennis-chan/Git/trendora/docs/handoffs/goal-mcp-loop-iter-13-dev.md` -- NEW dev handoff.
- **DO NOT EDIT (editing = regression signal):** `runs/goal-session-mcp-loop/state/certified-claims.jsonl` (the gate wrote row 6; the prior 5 stay byte-identical); any `apps/backend/app/**` (engine / referee / ledger / online_fdr / triad_scan / `evidence.py` / `api/evidence.py` / routers); the score/event-study/factor branches of `claimSurface`/`resolveEvidenceStatus`/`resolveCohortEvidence`; `proven_signals`; `app/evidence/page.tsx` structure.

## UI Evolution
- New user-facing capability: audit an out-of-sample-proven **multi-factor (composite)** edge end-to-end — see it "Proven" on the Multi-factor combination lab for the certified `rs_spy_3m × high_proximity` selection, click through to its `/evidence` row, and confirm every other combination honestly reads "Not yet proven".
- New information displayed: a 6th `/evidence` certified-claim row for the `rs_spy_3m × high_proximity` composite @ h20 (hypothesis incl. both `condition` legs + horizon + `kind=combination`, PASS verdict, holdout +4.69%, control vs SPY +4.69%, registration date, forward-walk "Pending", "Backs: Multi-factor combination lab →"); a "Proven"/"Not yet proven" badge on the combination lab's composite cohort row.
- New user actions: click the composite "Proven" badge on `/research/factor-combination` to deep-link to its `/evidence` row; compose a different 2-factor combination (or leave the default) and observe the badge honestly read "Not yet proven".
- UI surface changes: `/research/factor-combination` composite row gains an inline evidence badge; `/evidence` gains one combination claim row (auto-rendered). No new page, no new route.
- Navigation changes: none (both routes already registered in the blueprint IA, line 76).

## Visual Requirements
- Component patterns: reuse the existing quiet evidence chip — `Badge` (`accent` for Proven, `default` for Not-yet-proven), `lucide-react` `ShieldCheck`/`Shield`, the `num` mono class, Next.js `<Link>` for the deep-link — mirroring `FactorEvidenceBadge`. The `/evidence` row auto-renders via the existing `ClaimRow` (no new component). Invent no new component.
- Layout: attach the badge inline on the existing composite row of the data-dense `combination-table`; no layout rewrite, no new page.
- Key visual effects: match Trendora's minimal, data-dense, evidence-first style — a calm, unmissable "proven / not yet proven" chip, never hype (goal.md Design Direction). No new effects/colors.
- States to handle: empty/failed `fetchEvidence` → badge reads "Not yet proven" with no link (fail-safe honesty); the DEFAULT combination and any non-certified selection → "Not yet proven"; a matched-but-non-PASS entry → never "Proven"; combination cohorts still render their existing NA/low-sample cells unchanged.

## Key Test Scenarios
Phase is complete only when all pass; assert EXACT values and cover the failure paths.
- **Gate precondition (already met):** `certified-claims.jsonl` has 6 entries; row 6 is the combination PASS (Bonferroni divisor 6, `required_p≈0.008333`, `p_value=0.0009995`). Prior 5 byte-identical.
- **J-08 (browser-qa, canonical lane — REQUIRED):**
  - `/evidence` — the NEW combination row renders (SCROLL into viewport before capture) with hypothesis chips showing the two `condition` legs + `horizon=20` + `kind=combination`, PASS, holdout **+4.69%**, control vs SPY **+4.69%**, a registration date, forward-walk "Pending", and the **"Backs: Multi-factor combination lab →"** linkback (NOT "Unmapped signal").
  - `/research/factor-combination` — compose the certified selection (`rs_spy_3m:top:quintile` + `high_proximity:top:tertile` at horizon **20**): the composite cohort badge reads **"Proven"** and deep-links to the `/evidence` combination row. **The DEFAULT combination is `rs_spy_3m × atr_pct` (a FAILED pair) → it reads "Not yet proven"** — the operator MUST swap leg 2 to `high_proximity:top:tertile` (side top, tertile) at h20 to get "Proven". Assert a different combination (e.g. the default, or h60) reads "Not yet proven".
  - **HARD (iter-3/iter-11):** scroll each asserted badge/row into the viewport before the screenshot; md5-check the captured PNGs are DISTINCT (not one relabeled full-page frame).
- **Regression J-01/J-02/J-03:** `/stocks` + `/stocks/{ticker}` inline score badges unchanged (Leadership "Proven", Entry Quality/Risk "Not yet proven"); `proven_signals` byte-identical `{leadership_score}`; NO new inline `/stocks` badge from the signal-less combination claim.
- **Regression J-04/J-05/J-06/J-07:** `/evidence` still lists the prior 5 rows PLUS the new combination row (6 total); the `/research/factor-lab` per-horizon badges (vcp_contraction h20/h60) unchanged; the Breakout-watch regime row unchanged.
- **Frontend unit (`lib/evidence.test.ts`):** `resolveCombinationEvidence` → "Proven" + correct anchor for the certified cohort with legs in EITHER order (order-independence); "Not yet proven" for a non-matching combination (different legs / different horizon / reversed direction), a matched-but-non-PASS entry, and an empty/null/undefined list. `combinationCohortFromClaim` extracts the certified claim and rejects a factor/event-study/malformed claim. `claimAnchorId` returns the combination anchor (distinct from any `factor-…` anchor); `claimSurface` combination branch → honest title + `/research/factor-combination` linkback + deterministic anchor. No return/price/buy-sell language.
- **Correctness (anti-goal #3):** the displayed combination edge / p / control byte-match `certified-claims.jsonl` row 6 — never a UI recompute.
- **Anti-goals:** signal-less claim lights NO `/stocks` badge; `proven_signals` unchanged; no return/price/buy-sell language; determinism + no-lookahead preserved (no engine change); no secrets. Auditor confirms.
- **Deliverables:** demo-narrator `[NEW]`-flagged walkthrough produced (`demo.sh mcp-loop --session-live`); `docs/handoffs/goal-mcp-loop-iter-13-dev.md` written.

## Assumptions & Landmines
- **Full leg-string match, not factor-key match.** The certified claim's `condition` legs are the full
  `factor:side:quantile` strings (`rs_spy_3m:top:quintile`, `high_proximity:top:tertile`). The matcher
  must compare the full leg-set (order-independent) so a different side/quantile of the same factors does
  NOT false-match. `CombinationTable` already emits legs in this exact byte-format (lines 1414-1416).
- **Default ≠ certified.** The combination lab's config default (`rs_spy_3m × atr_pct:bottom:tertile`) is a
  FAILED anchor pair, so the composite badge is "Not yet proven" on first load. This is CORRECT (honest) —
  browser-qa must actively compose the `high_proximity` pair at h20 to demonstrate "Proven". Do NOT
  special-case the default to read "Proven".
- **Direction is fixed positive.** The composite cohort is the positive (top-quantile blend) direction only;
  the query uses `direction:"positive"` to match row 6. If the payload exposes a direction field, read it;
  otherwise "positive" is the sole composite direction.
- **`leadership_score` still reads honestly across surfaces** — this iteration does not touch the score
  branches; do not regress them.
- **Blueprint conformance — already satisfied.** J-08's IA homes are registered (blueprint.md line 76) and
  the additive iter-13 Data-Contract clarification is already present (line 199): same value, more readers,
  no new module/endpoint, no nav change. Verify present; do NOT re-approve the blueprint.
- **No architecture docs to update.** `docs/architecture/` does not exist; design context lives in
  `docs/trendora-design.md` + per-iteration handoffs.

## Out of Scope (excluded — no scope creep)
- Any change to the referee, `verify_edge`, `online_fdr`, `evidence.py`, `api/evidence.py`, or the existing
  5 canonical ledger rows (only the single new row 6, written by the gate, exists).
- Any `/stocks`, `/stocks/{ticker}`, `/sectors`, `/themes`, or Dashboard inline-badge change; `proven_signals`
  must stay exactly `{leadership_score}`.
- Adding a `signal` key to the combination claim (it is signal-less by design — would wrongly try to light a
  per-stock badge).
- Promoting/exploring any OTHER combination or horizon, quantile spreads (D10−D1), regime conditioning, or
  sector cohorts (deferred per goal.md Part B "later phases").
- Re-proposing any closed FAIL hypothesis (`ma_stack`, `hv`, `high_proximity` single-factor, or the FAILed
  anchor combinations `rs_spy_3m+atr_pct`, `leadership_score+atr_pct`).
- A bespoke combination branch in `app/evidence/page.tsx` (the existing `ClaimRow` + extended
  `claimSurface`/`claimAnchorId` already render it) or a second evidence data path.
