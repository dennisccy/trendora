# goal-mcp-loop-iter-8 Execution Plan

> **Gate status: ALREADY PASSED — iteration UNBLOCKED.** The post-decompose gate has certified the
> Evidence Claim. `runs/goal-session-mcp-loop/state/certified-claims.jsonl` now holds the **4th** entry:
> `kind:factor` · `factor:vcp_contraction` · `slice_kind:decile` · `decile:10` · `horizon:20` ·
> `direction:positive`, **`status: PASS`**, holdout edge **+0.03330 (+3.33%)** vs the same-dates SPY
> control, **p 0.011494** < required_p **0.0125** (Bonferroni divisor **4**), control_excess +0.03330,
> register_date **2026-06-30**. The claim JSON carries **NO `signal` key** (signal-less plain-factor
> cohort). The ledger also holds the **ma_stack D10 FAIL** (3rd entry, `status: FAIL`, p 0.01949 ≥
> 0.01667). This is a **frontend-surfacing + one backend confirming-test** iteration. **Zero
> `apps/backend/app/**` diff; zero engine / referee / `/api/evidence`-shape diff.** Do NOT re-run or
> loosen the referee; do NOT substitute another factor; do NOT stamp a `signal` on this claim.

## What to Build
- **Read-side cohort-selector matcher** in `lib/evidence.ts` — a PURE `resolveCohortEvidence(cohort, claims)`
  (the signal-less successor to `resolveEvidenceStatus`). Scan the served `claims[]` for a `proven` (PASS)
  entry whose `claim` cohort selectors MATCH the queried cohort on `factor` + `slice_kind` + `decile` +
  `horizon` + `direction`; return `{ proven, label, href, claim }`. Reads `entry.proven` /
  `verdict.status === "PASS"` **verbatim** — never recomputes. Fail-safe: no match, a matched-but-non-PASS
  entry (e.g. the ma_stack FAIL row), or an empty/failed list → `{ proven:false, label:"Not yet proven",
  href:null }`.
- **Deterministic cohort anchor** in `lib/evidence.ts` — pure `cohortClaimId(cohort)` /
  `cohortEvidenceAnchor(cohort)` deriving a stable, collision-free `/evidence#…` anchor from a factor
  cohort's selectors (e.g. `#factor-vcp_contraction-d10-h20`).
- **`claimSurface` factor branch** in `lib/evidence.ts` — add a `kind === "factor"` branch for a
  signal-less factor cohort: honest title (e.g. `"vcp_contraction — top decile (D10)"` from the selectors,
  NOT "Unmapped signal"), honest *historical evidence* subtitle (e.g. `"Out-of-sample edge — factor top
  decile"` — never buy/sell or a return promise), and a **"Backs: Research factor lab →"** linkback to
  `/research/factor-lab`. KEEP the score-signal branch and the event-study branch **byte-identical**.
- **`/evidence` `ClaimRow` cohort anchor** — set the row `id` to `cohortClaimId(cohort)` for a signal-less
  factor claim so the factor-lab "Proven" badge can deep-link to its backing row; KEEP `signal-${signal}`
  for score rows (J-02/J-05 deep-links unchanged). The vcp_contraction row renders the same five fields as
  existing rows + the "Backs: Research factor lab →" linkback (already wired through `claimSurface`).
- **Evidence badge on the factor-lab top-decile rows** — in `_labs.tsx` `FactorLabPage`/`FactorsTable`,
  fetch the canonical payload via the EXISTING `fetchEvidence()` client (reuse — no new fetch path) and, for
  each factor's top-decile (D10) cohort at the certified horizon (20), render an `EvidenceStatusBadge`-style
  chip resolved via `resolveCohortEvidence`: **vcp_contraction → "Proven"** (link via
  `cohortEvidenceAnchor`); every unbacked factor (including ma_stack's FAIL) → **"Not yet proven"** (no
  link). The badge re-displays the served status — it computes nothing.
- **Unit tests** for all new pure helpers (front + back) — see Key Test Scenarios.

## Agents Required
- **developer: yes** — single agent drives both lanes (frontend bulk + the one backend test), TDD.
- **backend-data: yes (TEST-ONLY)** — add a `build_evidence_payload` post-certification assertion to
  `apps/backend/tests/test_evidence.py` over the 4-entry ledger `[leadership_score PASS, Breakout-watch
  Risk-on PASS, ma_stack D10 FAIL, vcp_contraction D10 PASS]`. **NO `apps/backend/app/**` change** — no new
  computation, no new endpoint, no engine/referee/resolver edit (`_resolve_signal` already returns `None`
  for non-score factors; `/api/evidence` already serves the entry verbatim).
- **frontend-ux: yes** — the `lib/evidence.ts` pure helpers + `lib/evidence.test.ts` cases, the `/evidence`
  `ClaimRow` cohort anchor, and the factor-lab evidence badge in `_labs.tsx`.

## Frontend Present

Frontend Present: yes

## Files to Create/Modify
- `apps/frontend/lib/evidence.ts` — add `resolveCohortEvidence`, `cohortClaimId`/`cohortEvidenceAnchor`, and
  the `claimSurface` `kind:"factor"` branch (+ a `Cohort`-style selector type if helpful). PURE, read-only;
  fabricates nothing; never decides proven-ness beyond reading `proven`/`PASS` verbatim. KEEP the existing
  `resolveEvidenceStatus`, score branch, and event-study branch byte-identical.
- `apps/frontend/lib/evidence.test.ts` — add cases for `resolveCohortEvidence` (full-selector match → Proven
  + href; selector mismatch / matched-but-non-PASS / empty → Not yet proven, no href), the `claimSurface`
  factor branch (honest title + "Research factor lab" linkback; score + event-study branches unchanged), and
  `cohortClaimId`/`cohortEvidenceAnchor` stability/collision-free.
- `apps/frontend/app/evidence/page.tsx` — `ClaimRow`: derive the row `id` from `cohortClaimId(cohort)` for a
  signal-less factor claim; keep `signal-${signal}` for score rows and `undefined` for the event-study row.
  The factor row's title/subtitle/linkback flow through the new `claimSurface` branch (no other change).
- `apps/frontend/app/research/_labs.tsx` — `FactorLabPage`: add a fail-safe `fetchEvidence()` call (reuse
  the existing client); thread the resolved `claims[]` into `FactorsTable`/`FactorRows`; render the
  top-decile (D10 @ h20) evidence badge per factor row. **See the nested-interactive hazard below.**
- `apps/backend/tests/test_evidence.py` — add the 4-entry post-certification test (new signal-less
  vcp_contraction factor-PASS builder + a ma_stack FAIL builder; reuse existing `_pass_entry`/`tmp_path`
  conventions). Assert `proven_signals == {leadership_score}`; the vcp_contraction row `proven:true`,
  `signal:null`, selectors verbatim; the ma_stack row `proven:false`; `_resolve_signal(vcp_contraction) →
  None`; and the served verdict fields (holdout edge, p-value, control excess, register date) byte-match the
  ledger line.
- `docs/handoffs/goal-mcp-loop-iter-8-dev.md` — **required** dev handoff (DoD).
- **NONE under `apps/backend/app/**`**; no change to the three scores, the regime/forward-return/factor-lab
  engines, the referee, or `GET /api/evidence`'s shape. `app/research/factor-lab/page.tsx` is a thin
  re-export of `FactorLabPage` — likely **no change** (the work lives in `_labs.tsx`).

Pipeline-produced (not by the developer): `docs/handoffs/goal-mcp-loop-iter-8-audit.md` — the full pipeline
MUST complete the audit stage this iteration.

### Implementation hazard (read before touching `_labs.tsx`)
The factor summary `<tr>` (`FactorRows`) is a `role="button"` click-to-expand control that DELIBERATELY
carries **no nested interactive element** — the iter-5 nested-interactive hazard; that is exactly why the
decile `N=` `SampleLink` drill-downs live in the SEPARATE expanded panel, not the summary row. The "Proven"
badge is a `<Link>` (interactive) and J-06 requires it ON the top-decile summary row. To avoid the hazard,
the developer MUST keep the link from also toggling the row: render the badge in its own summary-row cell
and have the "Proven" link call `e.stopPropagation()` (and stop key events), so a click deep-links rather
than expanding. The "Not yet proven" badges are non-interactive (no link) and are safe. Only the single
vcp_contraction "Proven" link needs this guard.

## UI Evolution
- **New user-facing capability:** for the first time the user sees a **plain-factor (non-score) edge** marked
  "Proven" on the Research factor lab — the vcp_contraction top-decile cohort's certified out-of-sample edge
  — and can click straight through to its auditable ledger entry on `/evidence`.
- **New information displayed:** a 4th `/evidence` claim row for the vcp_contraction top-decile cohort
  (hypothesis chips, OOS verdict ≈ **+3.33%** / p ≈ **0.01149**, control vs SPY, register date, forward-walk
  score-to-date, "Backs: Research factor lab →"); and on `/research/factor-lab`, a "Proven"/"Not yet proven"
  evidence badge on each factor's top-decile cohort (vcp_contraction reads "Proven").
- **New user actions:** on `/research/factor-lab`, click the vcp_contraction top-decile "Proven" badge to
  jump to its backing entry on `/evidence`; on `/evidence`, follow the vcp_contraction row's "Backs: Research
  factor lab →" linkback back to the lab.
- **UI surface changes:** `/research/factor-lab` top-decile rows gain an evidence badge; `/evidence`
  `ClaimRow` gains a factor-cohort honest title/subtitle/linkback and a cohort-derived anchor. **No new
  pages.**
- **Navigation changes:** none — **Research** (with the Factor Lab card → `/research/factor-lab`) and
  **Evidence** already exist in the sidebar; both reachable in ≤2 clicks. Additive edits only, no
  nav-skeleton change ⇒ **no blueprint re-approval required**.

## Visual Requirements
- **Component patterns (reuse, no new component):** the existing `Badge` token (accent for "Proven", muted
  `default` + faint text for "Not yet proven") with the `ShieldCheck`/`Shield` lucide icons — mirror
  `components/evidence-status-badge.tsx`. Existing `Card`/`table` layout for the factor lab; existing
  `Link` style (`text-accent hover:underline focus-visible:ring-1`) for the badge link + the `/evidence`
  linkback.
- **Layout:** unchanged. The badge sits in a dedicated cell on each factor's top-decile summary row in the
  all-factors table; the `/evidence` factor row uses the existing vertical `Card` list. No restructuring.
- **Key visual effects:** none new — keep the minimal, data-dense, **evidence-first, skeptical/calm**
  treatment. The vcp_contraction edge is framed as *historical, out-of-sample evidence* ("beat SPY
  out-of-sample over the sealed holdout"), never "buy this now"; the badge is calm and unmissable, never
  hype.
- **States to handle:** evidence fetch loading/error/empty → every factor-lab top-decile badge reads "Not
  yet proven", no link (fail-safe; never 500, never a fabricated "Proven"); a matched-but-non-PASS cohort
  (ma_stack FAIL) → "Not yet proven", no href; the vcp_contraction `/evidence` row + the factor-lab "Proven"
  badge render **below the fold** — browser-QA MUST **scroll each target into the viewport before capture**
  (iter-3 lesson).

## Key Test Scenarios
- **Gate (re-confirm, do NOT re-run):** `certified-claims.jsonl` line 4 is `status: PASS` for the
  vcp_contraction D10 h20 cohort with no `signal` key. A non-PASS would block — but it is already PASS.
- **J-06 (browser, target):** `/research/factor-lab` — the **vcp_contraction** top-decile cohort shows a
  **"Proven"** badge (scrolled into frame); clicking it deep-links to the vcp_contraction row on
  `/evidence`. At least one OTHER factor top-decile row reads **"Not yet proven"**. `/evidence` — the
  vcp_contraction row renders the five fields + **"Backs: Research factor lab →"**, and its displayed
  holdout edge **+3.33%** / control vs SPY / register date **2026-06-30** **byte-match** `GET /api/evidence`
  (API-correctness).
- **J-01 / J-03 (browser regression):** `/stocks` — every score shows a status; **Leadership "Proven"**,
  **Entry Quality + Risk "Not yet proven"**; **no vcp_contraction-induced inline score badge** appears.
- **J-02 (browser regression):** `/stocks/{ticker}` — the Leadership proof drill-down still shows the OOS
  test, SPY control, and claim id/date.
- **J-04 (browser regression):** `/` → `/evidence` — the Breakout-watch row is still labeled **"Regime:
  Risk-on"** with its event-study linkback.
- **J-05 (browser regression):** `/evidence` — the leadership row (5 fields) + **"Backs: Stocks leaderboard
  →"** still render and round-trip; the new vcp_contraction row does not break the list.
- **Frontend unit (`node lib/evidence.test.ts`):** `resolveCohortEvidence` full-selector match → `{proven:
  true, label:"Proven", href}`; any selector mismatch / matched-but-non-PASS (ma_stack FAIL) / empty →
  `{proven:false, label:"Not yet proven", href:null}`. `claimSurface` signal-less `kind:"factor"` → honest
  factor title + "Research factor lab" linkback; score row + event-study row byte-identical.
  `cohortClaimId`/`cohortEvidenceAnchor` stable + collision-free; `ClaimRow` uses it for a factor claim and
  keeps `signal-${signal}` for score rows.
- **Backend unit (`pytest tests/test_evidence.py`):** 4-entry ledger → `proven_signals` keys ==
  `["leadership_score"]`; `claims[]` includes the vcp_contraction factor row (`proven:true`, `signal:null`,
  selectors verbatim) and the ma_stack row (`proven:false`); `_resolve_signal(vcp_contraction claim) →
  None`; served verdict fields byte-match the ledger line. Error case: absent/empty/unreadable ledger →
  `{"claims": [], "proven_signals": {}}` (200, never 500) — keep green.
- **Invariants (must not regress):** no anti-goal language (no return/price/buy-sell/alpha) on the
  vcp_contraction row; nothing uncertified reads "Proven" (ma_stack reads "Not yet proven"); zero engine
  diff (determinism / no-lookahead untouched); `proven_signals` stays exactly `{leadership_score}`
  (unit-asserted); secret scan clean.
- **Demo (non-gating):** a `[NEW]`-flagged demo-narrator walkthrough of the vcp_contraction ledger row + the
  factor-lab "Proven" badge (plain-language narration + a real-data screenshot), viewable via
  `demo.sh mcp-loop --session-live`.

## Scope, Drift & Assumptions
- **Goal alignment: confirmed.** Delivers `docs/goal.md` Key Capability 1 (evidence badges extended to the
  factor lab) and closes **J-06**, the sole outstanding (auto-proposed) Must-have. On a passing browser run,
  all six journeys (J-01…J-06) are green and the `<!-- AUTO:journeys -->` block carries no further unbuilt
  scope → the goal-evaluator can re-assess **GOAL_ACHIEVED**.
- **OUT OF SCOPE (exclude — flagged scope guards):** stamping a `signal` on the vcp_contraction claim or
  lighting any inline `/stocks` score badge (it backs the factor lab + Evidence only); re-proposing or
  certifying ma_stack / hv / high_proximity (they FAIL the bar — ma_stack is already a FAIL ledger entry);
  badging the full D1…D9 decile grid, the regime/sector/theme labs, or any non-vcp_contraction surface
  (only the factor-lab top-decile D10 summary rows get a badge); proving a 2nd/broader factor or another
  proposer-backlog cohort; any change to the three scores, the engines, the referee, or `/api/evidence`'s
  shape; a 2nd proven-ness computation or a 2nd endpoint; multi-control enrichment (QQQ / sector ETF /
  random — the row shows the **SPY** control honestly labeled).
- **Design assumption (documented, not asked):** all new logic (`resolveCohortEvidence`, the cohort-anchor
  helpers, the `claimSurface` factor branch) lives as **pure helpers in `lib/evidence.ts`** (the repo's
  `node lib/*.test.ts` unit pattern, since `page.tsx`/`_labs.tsx` are not unit-tested), and the score +
  event-study outputs stay byte-identical. The badge in `_labs.tsx` consumes those helpers.
- **Gate authority (do NOT substitute on FAIL):** the gate is deterministic given the cumulative
  `RefereeState` (trial #4 ⇒ divisor 4, required_p 0.0125) and the committed seed; the human replay returned
  PASS. The ledger already shows PASS. If the gate ever returns FAIL/INSUFFICIENT, do NOT loosen the referee
  and do NOT swap in another factor — **halt and surface to the operator**.
- **Verification gap = HARD fail (iter-0/2/5/6 lesson):** judge the journeys on the canonical
  `…-ui-test-results.md` + `engine.log`, NEVER on the dead `browser_checks_run` flag and NEVER on a
  parallel/secondary QA-lane PASS. `start-frontend.sh` must free the frontend port before binding (iter-4
  stale-`next-server` hazard); confirm the frontend reaches the backend (populated factor-lab data,
  `/api/evidence` returns the 4 entries with `vcp_contraction proven == true`) **before** scoring. Any
  mid-run harness fix must live in the per-step child scripts, not the running parent.
