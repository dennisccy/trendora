# goal-mcp-loop-iter-4 Execution Plan

> **Gate status: ALREADY PASSED — iteration UNBLOCKED.** The post-decompose gate has certified the
> Evidence Claim: `runs/goal-session-mcp-loop/state/certified-claims.jsonl` holds the 2nd entry
> (`event-study` · subject **Breakout-watch** · `slice_kind: regime` · **regime "Risk-on"** · view
> **pooled** · horizon **20**, `status: PASS`, holdout edge **+0.06125 (+6.12%)** vs the same-dates SPY
> control, p **0.0004998** < required_p **0.025**, **107** holdout / **277** in-sample dates,
> `register_date` **2026-06-30**, `deflation_divisor 2`). This is a **frontend-surfacing + one backend
> confirming-test** iteration. **Zero backend app-source diff; zero engine/referee/endpoint diff.** Do NOT
> re-run or loosen the referee.

## What to Build
- **Regime label on regime-conditioned claim rows** (`/evidence` `ClaimRow`): when a claim's cohort carries
  a non-empty `claim.claim.regime` (equivalently `slice_kind === "regime"`), render a calm, prominent
  **"Regime: Risk-on"** badge in the row header (read **verbatim** from the payload). Hide it entirely when
  absent — the leadership (score) row has no `regime` and must look **unchanged**. This is J-04's "clearly
  labeled with the regime it holds in."
- **Honest title + linkback for the non-score (setup) claim** (same `ClaimRow`): the regime claim has
  `signal: null`, which today renders "Unmapped signal" + a misleading "Backs: Stocks leaderboard →". For
  this `event-study` claim, show a meaningful title (the subject — *"Breakout-watch setup"* — framed as an
  *out-of-sample edge in the Risk-on regime*) and an honest linkback to the **Dashboard regime context /
  Research event-study lab**, NOT the Stocks leaderboard. The leadership (score) row's `signal` text, title,
  and **"Backs: Stocks leaderboard →"** stay **byte-identical** (J-05 must not regress).
- **Dashboard → Evidence affordance** (`RegimeGlanceCard` in `app/page.tsx`): add a discoverable link
  **"See evidence proven in this regime →"** that navigates to `/evidence`. Additive; the regime
  number/label (Risk-on, 76.05) is unchanged.
- **Backend confirming unit test (NO app-source change):** assert `build_evidence_payload` over the live
  2-entry ledger `[leadership_score PASS (factor), Breakout-watch Risk-on PASS (event-study)]` returns
  `proven_signals` keyed **only** on `leadership_score`, and `claims[]` includes the regime row
  (`claim.regime == "Risk-on"`, `proven == true`, `signal == null`); `_resolve_signal` returns `None` for
  the event-study regime claim. This guards the anti-regression invariant (the regime claim adds no signal,
  does not overwrite `leadership_score`).
- **Frontend unit tests** for the new pure helpers (regime-label present/absent; non-score honest
  title/linkback; score-row title/linkback unchanged).

## Agents Required
- **developer: yes** — single agent does both lanes below (frontend bulk + the one backend test), TDD.
- **backend-data: yes (TEST-ONLY)** — add the `build_evidence_payload` 2-entry-ledger assertion to
  `apps/backend/tests/test_evidence.py` and keep the backend pytest suite green. **NO `apps/backend/app/**`
  change** — no new computation, no new endpoint, no engine/referee/resolver edit (Data Contract row 1 is
  canonical; `/api/evidence` already serves the entry verbatim).
- **frontend-ux: yes** — `ClaimRow` regime label + honest non-score title/linkback, the Dashboard regime
  affordance, and the `lib/evidence.ts` pure helpers + `lib/evidence.test.ts` cases.

## Frontend Present

Frontend Present: yes

## Files to Create/Modify
- `apps/frontend/lib/evidence.ts` — add two **pure, testable** helpers: (1) a regime-label extractor that
  returns `claim.claim.regime` when present/non-empty else `null`; (2) a claim title + linkback resolver
  that, for a `signal: null` event-study/regime claim, yields an honest title + a non-"Stocks leaderboard"
  linkback, while returning the **existing** score-row title + "Backs: Stocks leaderboard →" **byte-identical**.
  (Placement assumption — see Scope notes: pure logic lives here because `page.tsx` is not unit-tested.)
- `apps/frontend/lib/evidence.test.ts` — add cases: regime label present → "Risk-on"; absent/blank → hidden;
  non-score claim → honest title + non-leaderboard linkback; score claim → title + linkback unchanged.
- `apps/frontend/app/evidence/page.tsx` — `ClaimRow`: render the "Regime: <label>" badge in the header when
  present; route the `signal: null` claim through the new honest title/linkback; leadership row untouched.
- `apps/frontend/app/page.tsx` — `RegimeGlanceCard`: add the "See evidence proven in this regime →" link to
  `/evidence` (additive footer affordance).
- `apps/backend/tests/test_evidence.py` — add the 2-entry-ledger confirming test (matches existing
  `_pass_entry` / `tmp_path` conventions).
- `docs/handoffs/goal-mcp-loop-iter-4-dev.md` — **required** dev handoff (DoD).
- **NONE under `apps/backend/app/**`** and no change to the three scores, the regime/forward-return engine,
  the referee, or `GET /api/evidence`'s shape.

Pipeline-produced (not by the developer): `docs/handoffs/goal-mcp-loop-iter-4-audit.md` — the audit stage
MUST run to completion this iteration (iter-3 process gap: the audit stopped at `qa_complete`).

## UI Evolution
- **New user-facing capability:** for the first time the user sees decision-support evidence **conditioned
  on and labeled with a market regime** — the Breakout-watch setup's certified out-of-sample edge that holds
  specifically in the current **Risk-on** regime, reached from the Dashboard regime panel.
- **New information displayed:** a 2nd `/evidence` claim row **labeled "Regime: Risk-on"** showing the OOS
  holdout edge (**+6.12%** vs SPY), the control comparison, the post-deflation significance, and the
  registration date — all **verbatim** from `GET /api/evidence`.
- **New user actions:** from the Dashboard regime card, click **"See evidence proven in this regime →"** to
  jump to `/evidence` and read the regime-labeled claim row.
- **UI surface changes:** `/evidence` `ClaimRow` gains a regime label + an honest title/linkback for the
  non-score claim; the Dashboard `RegimeGlanceCard` gains the Evidence affordance link. **No new pages.**
- **Navigation changes:** none — the **Evidence** nav entry already exists (`sidebar.tsx:41`). No blueprint
  re-approval required.

## Visual Requirements
- **Component patterns (reuse, no new component):** `Badge` (calm `accent`/`default` token) for the
  **"Regime: Risk-on"** header label; existing `Card`/`CardContent` row layout; the existing `Link` style
  (`text-accent hover:underline focus-visible:ring-1`) for both the Dashboard affordance and the honest
  non-score linkback.
- **Layout:** unchanged — Evidence ledger as a vertical `Card` list; the regime label sits in the row header
  beside the verdict badge; the Dashboard affordance sits within `RegimeGlanceCard` (below the component
  disclosure). No layout restructuring.
- **Key visual effects:** none new — keep the minimal, data-dense, **evidence-first, skeptical/calm**
  treatment. The regime label is calm and unmissable, never hype; the claim is framed as *historical,
  regime-conditioned out-of-sample evidence*, never "buy these now."
- **States to handle:** regime label **hidden** when `claim.regime` is absent/blank (no empty "Regime:"
  chip, score rows unchanged); the regime row renders **below the fold** under the leadership row —
  browser-QA MUST **scroll it into the viewport before capture** (iter-3 lesson); empty/absent/unreadable
  ledger still yields `{"claims": [], "proven_signals": {}}` (200, never 500) and every badge reads "Not yet
  proven".

## Key Test Scenarios
- **Gate (re-confirm, do not re-run):** `certified-claims.jsonl` has the 2nd entry with `status: PASS` for
  the Breakout-watch · Risk-on · pooled · h20 cohort. A non-PASS would block — but it is already PASS.
- **J-04 (browser, target):** Dashboard regime panel shows **Risk-on (76.05)** + the "See evidence proven in
  this regime →" affordance → follow to `/evidence` → the Breakout-watch row is **labeled "Regime:
  Risk-on"** and its displayed holdout edge **+6.12%** / control / **register date 2026-06-30** are
  **byte-identical** to `GET /api/evidence` (API-correctness). **Scroll the row into frame before the shot.**
- **J-05 (browser regression):** the leadership row's 5 fields + **"Backs: Stocks leaderboard →"** still
  render and round-trip; the new regime row does not break the list.
- **J-01 / J-03 (browser regression):** `/stocks` — every score shows a status; **Leadership "Proven"**,
  **Entry Quality + Risk "Not yet proven"**.
- **J-02 (browser regression):** `/stocks/{ticker}` — the Leadership proof drill-down still shows the OOS
  test, SPY control, and claim id/date.
- **Frontend unit (`node lib/evidence.test.ts`):** regime label present → "Risk-on", absent/blank → hidden;
  non-score (`signal: null`) → honest title + a **non-"Stocks leaderboard"** linkback; the score row's title
  + linkback **unchanged**.
- **Backend unit (`pytest tests/test_evidence.py`):** 2-entry ledger → `proven_signals` keys ==
  `["leadership_score"]`; `claims[]` contains the regime row (`regime == "Risk-on"`, `proven == true`,
  `signal == null`); `_resolve_signal` → `None` for the event-study claim. Error case: absent/empty ledger →
  `{"claims": [], "proven_signals": {}}` (already covered — keep green).
- **Invariants (must not regress):** no anti-goal language (no return/price/buy-sell/alpha) on the regime
  row; nothing uncertified reads "Proven"; `proven_signals.leadership_score` unchanged (unit-asserted); zero
  engine diff (determinism / no-lookahead untouched); secret scan clean.

## Scope, Drift & Assumptions
- **Goal alignment: confirmed.** Delivers `docs/goal.md` Key Capability 3 (regime-conditioned evidence) and
  closes **J-04**, the sole remaining Must-have. On a passing browser run, **all five journeys (J-01…J-05)
  are green** → the goal-evaluator can assess **GOAL_ACHIEVED**.
- **OUT OF SCOPE (exclude — flagged scope guards):** lighting an inline regime badge on a per-stock score
  surface or stamping this claim with a `signal`; proving Entry Quality / Risk or a 2nd/broader regime
  claim; multi-control enrichment (QQQ / sector ETF / random same-sector — the row shows the **SPY** control
  honestly); any change to the three scores, the regime/forward-return engine, the referee, or
  `/api/evidence`'s shape; a 2nd proven-ness computation or a 2nd endpoint; a regime filter/query UI on
  `/evidence` (optional polish only — a simple Dashboard→`/evidence` link + the prominent label suffices).
- **Design assumption (documented, not asked):** the new regime-label + non-score title/linkback logic is
  added as **pure helpers in `lib/evidence.ts`** (matching the repo's `node lib/*.test.ts` unit pattern,
  since `page.tsx` is not unit-tested) and the score-row output is kept byte-identical. If the developer
  instead keeps `surfaceForSignal` inline in `page.tsx`, the new branch logic must still be exercised by a
  pure unit test in `lib/evidence.test.ts`.
- **Optional, low-value carry (not required for DoD):** iter-3 reviewer suggested adding `tsx` as a frontend
  devDependency so `node lib/*.test.ts` runs without the `ERR_NO_TYPESCRIPT` workaround. The existing tests
  already run under Node's native TS type-stripping — add `tsx` **only if** `node lib/evidence.test.ts`
  actually fails here, and route the install through the supply-chain security gate.
- **Verification gap = HARD fail (iter-0/iter-2 lesson):** `browser_checks_run=false` or an all-SKIP
  `ui-test-results.md` leaves **J-04 unknown (never passing)** regardless of a QA PASS. The iter-3 `next
  start` bring-up is in place; confirm the frontend reaches the backend (populated ~120-row leaderboard,
  `/api/evidence` returns `proven_signals.leadership_score.proven == true`) **before** scoring.
- **Process gap (iter-3):** the audit stage stopped at `qa_complete`; this full run MUST produce
  `docs/handoffs/goal-mcp-loop-iter-4-audit.md`.
