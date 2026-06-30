# goal-mcp-loop-iter-5 Execution Plan

> **Iteration type:** verification-integrity + QA-harness fix. NOT a feature delivery.
> All five Must-have journeys' features are already built and referee-certified. The sole
> blockers to GOAL_ACHIEVED (named by the iter-4 evaluator) are process/harness, not product:
> (1) the **canonical** `browser-qa-agent` lane SKIPPED all 11 checks because a stale `next-server`
> held the frontend port (`scripts/start-frontend.sh` lacks the pre-bind port-free that `dev.sh` has),
> and (2) the post-QA **audit handoff is missing** (the audit stage stalled at `qa_complete` in iter-3
> and iter-4). This iteration fixes both.

## What to Build

- **One code change only — harden the QA frontend bring-up.** In `scripts/start-frontend.sh`, insert a
  **pre-bind port-free block** immediately before the final `exec npx next start -p "$FRONTEND_PORT"`
  (currently line 55). Mirror the proven pattern in `scripts/dev.sh` (lines 23–41) but **scoped to
  `$FRONTEND_PORT` only** (this script binds only the frontend; the backend is owned by
  `start-backend.sh`): `lsof -ti :$FRONTEND_PORT | kill -9`, then `fuser -k -9 $FRONTEND_PORT/tcp`,
  then a **bounded** wait loop (≤ ~5s; dev.sh uses 50 × `sleep 0.1`) that re-kills until `lsof` shows
  no owner **AND** `ss -tlnH sport = :$FRONTEND_PORT` shows no lingering socket. The loop exits
  immediately when the port is already free, so the normal path is unaffected.
- **Leave the existing stamp-guarded `next build` / `next start` logic unchanged** — only ADD the
  preamble. **Zero `apps/` diff.**
- **Re-confirm all five Must-have journeys end-to-end through the canonical `browser-qa-agent` lane**
  (the only lane that counts for GOAL_ACHIEVED), capturing fresh **UT-*** screenshots into
  `reports/phase-goal-mcp-loop-iter-5-ui-test-results.md`. Flip **J-04 `partial` → `passing`**;
  re-confirm J-01/J-02/J-03/J-05 with **fresh canonical pixels** (not carried, not via the parallel
  TC-* lane).
- **Produce the post-QA audit handoff** `docs/handoffs/goal-mcp-loop-iter-5-audit.md` (PASS or
  PASS_WITH_GAPS) — a hard DoD item that the audit stage failed to write in iter-3 and iter-4.

## Agents Required

- developer: yes — implement the single `scripts/start-frontend.sh` port-free preamble. **No `apps/`
  product code.** Write the dev handoff. Do **NOT** add an `## Evidence Claim` block (no new proven claim).
- backend-data: no — zero `apps/backend/**` diff (no engine / referee / ledger / endpoint change).
- frontend-ux: no — zero `apps/frontend/**` product-code diff. Existing surfaces are **re-verified, not
  modified**.
- auditor (full pipeline): yes — MUST complete this time and write the audit handoff (see process flag below).

## Frontend Present

Frontend Present: yes

> **Why `yes` despite zero UI-code change:** this is the machine-read line `qa-phase.sh` uses to require
> the Chrome MCP browser lane. The browser-qa-agent running against the **live** frontend and rendering
> all five journeys *is this iteration's deliverable* (spec IN SCOPE → Frontend). Do not read this as a
> request to write UI code — there is intentionally **zero product-surface delta** vs iter-4.

## Files to Create/Modify

- `scripts/start-frontend.sh` — MODIFY (the ONE allowed code change): add the pre-bind port-free
  preamble for `$FRONTEND_PORT` immediately before the final `exec npx next start`. Existing
  build/stamp/start logic untouched.
- `docs/handoffs/goal-mcp-loop-iter-5-dev.md` — CREATE: dev handoff (what changed, harness error-case
  result, tests run, known issues).
- `docs/handoffs/goal-mcp-loop-iter-5-audit.md` — CREATE: post-QA audit handoff with PASS /
  PASS_WITH_GAPS verdict (hard DoD item; stalled in iter-3 + iter-4).
- `reports/phase-goal-mcp-loop-iter-5-ui-test-results.md` — CREATE (browser-qa-agent canonical lane):
  fresh UT-* screenshots, all five journeys, `browser_checks_run=true`, NOT all-SKIP.
- **Do NOT touch** anything under `apps/backend/**` or `apps/frontend/**`.

## UI Evolution (verification-only — no product surface delta)

- New user-facing capability: **None.** No new product capability this iteration.
- New information displayed: **None.** Every value re-verified reads from its already-registered
  canonical source (`GET /api/evidence`, `/api/stocks`, `/api/stocks/{ticker}`, `/api/dashboard`).
- New user actions: **None.**
- UI surface changes: **None.** `/stocks`, `/stocks/{ticker}`, `/evidence`, Dashboard regime card +
  affordance are re-verified, not changed.
- Navigation changes: **None.** Evidence nav entry already exists; no nav-skeleton change, so no
  `blueprint.reapproval-requested`.

> The "evolution" this iteration delivers is **verification integrity**: journeys that were `unknown`/
> `partial` because the canonical lane SKIPPED now carry fresh canonical proof. The user-visible product
> is byte-identical to iter-4.

## Visual Requirements (re-verify existing patterns — build nothing new)

- Component patterns: re-verify only — `Badge` (Proven / Not yet proven; "Regime: Risk-on"), `Card`/
  `CardContent` claim rows, existing link style for the Dashboard affordance + linkbacks. No new
  component or effect.
- Layout: unchanged — existing `/stocks` leaderboard, `/stocks/{ticker}` detail with expandable proof
  panel, `/evidence` claims list, Dashboard regime glance card.
- Key visual effects: none added; confirm the established calm/skeptical evidence-first treatment renders.
- States to handle (verify, not build): non-empty leaderboard (frontend↔backend reachable);
  "Not yet proven" rendered for Entry Quality + Risk; below-the-fold elements (J-02 proof panel, J-04
  2nd `/evidence` row) **scrolled into the viewport before capture** (iter-3 lesson).

## Key Test Scenarios

**Pre-flight reachability gate (BEFORE scoring any journey — iter-2 lesson):** `GET /api/evidence`
returns the **2 claims** (`proven_signals` keys == `["leadership_score"]`, proven `true`; 2nd row
`kind=event-study`, `signal=null`, `regime=Risk-on`, `subject=Breakout-watch`) **and** `/stocks` renders
**non-empty**. An empty leaderboard / empty frame is the "frontend can't reach backend" tell → HARD
verification gap, NOT a pass.

Canonical `browser-qa-agent` lane (→ `reports/phase-goal-mcp-loop-iter-5-ui-test-results.md`, UT-*):

- **J-01 — `/stocks`:** each leaderboard row's score area shows an evidence badge; Leadership reads
  **"Proven"**, Entry Quality + Risk read **"Not yet proven"**; ≥1 badge present and no score lacks a status.
- **J-02 — `/stocks/{ticker}`:** open a detail, locate a "Proven" badge, expand the proof panel,
  **scroll it into the viewport before capturing**; assert the out-of-sample test, control comparison
  (vs SPY/QQQ/sector ETF/random), and certified-claim id + registration date.
- **J-03 — `/stocks` (or detail):** Entry Quality + Risk render **"Not yet proven"** (not a confident
  number); the signal-less Breakout-watch regime claim lights **no** inline per-stock score badge.
- **J-04 — Dashboard → `/evidence`:** Dashboard shows **Risk-on 76.05/100** + the **"See evidence proven
  in this regime →"** affordance; follow it; **scroll the 2nd row ("Breakout-watch setup", "Regime:
  Risk-on") into frame before capturing**; values **byte-match `GET /api/evidence` line 2** (holdout
  **+6.12%**, p=0.0004998 < alpha/2=0.025, control **+6.12%** vs SPY, registered **2026-06-30**).
- **J-05 — `/evidence`:** both rows render (leadership_score + Breakout-watch); click a claim and verify
  the **linkback round-trip** (leadership "Backs: Stocks leaderboard →" → `/stocks` and back); the new
  regime row did not break the list.
- **Harness error case:** with a stale process deliberately holding `$FRONTEND_PORT`,
  `scripts/start-frontend.sh` frees it, binds successfully, and the readiness probe returns 2xx serving
  the **current** bundle (not the stale one) — the precise iter-4 failure the fix must eliminate.
- **Unit/integration (must stay green, unchanged — harness-only change):** backend
  `apps/backend/tests/test_evidence.py` (incl. `test_build_payload_regime_event_study_claim_adds_no_signal`)
  + `test_api_evidence.py`; frontend `lib/evidence.test.ts`, `lib/api-base.test.ts`.

**Definition-of-Done anchors:** start-frontend.sh frees the port pre-bind; canonical lane RUNS
(`browser_checks_run=true`, not all-SKIP) with fresh UT-* for all five; J-01–J-05 PASS via the canonical
lane (J-04 partial→passing); required-still-passing J-01/J-02/J-03/J-05 green; no anti-goal violation
(zero `apps/` diff; displayed numbers byte-match the API; Entry Quality + Risk still "Not yet proven";
regime claim lights no inline score badge; no buy/sell/return-promise language; secret scan clean);
unit tests green; **audit handoff written**; dev handoff written.

## Anti-goal guardrails (carry into dev / QA / audit)

- Displayed numbers are correct **only** if they byte-match the engine for the same as-of date — judge
  against **live `GET /api/evidence`** (source of truth), not against any number transcribed in this plan.
- "Proven" requires a PASS certified-claim that **names** the signal — `proven_signals` stays keyed only
  on `leadership_score`; Entry Quality + Risk MUST remain "Not yet proven".
- Determinism / no-lookahead preserved trivially (zero `apps/` diff — every served number is byte-identical).
- No new "proven" claim / no `## Evidence Claim` → post-decompose gate auto-passes. Do not propose an edge.
- No secrets in source.

## Process flag (ESCALATION)

The audit stage stalled at `qa_complete` in **both** iter-3 and iter-4. The full pipeline MUST reach and
complete the auditor this iteration and write `docs/handoffs/goal-mcp-loop-iter-5-audit.md` — it is a DoD
item, not optional. On a clean full run (canonical lane renders all five fresh + audit handoff exists),
the iter-4 evaluator's own assessment is that **all five journeys go green and GOAL_ACHIEVED is reachable.**

## Two browser lanes — do not confuse (iter-4 lesson)

There are TWO browser lanes and they can disagree: the **canonical** `browser-qa-agent` (UT-*,
`reports/phase-*-ui-test-results.md`) vs the QA agent's own Chrome MCP run (TC-*, `reports/qa/*-qa.md`).
**Only the canonical lane counts** for the terminal GOAL_ACHIEVED gate — it must RUN (not SKIP) and render
all five. An all-SKIP `ui-test-results.md` or `browser_checks_run=false` is a HARD verification gap
(journeys stay `unknown`/`partial`, never `passing`).

## Assumptions (documented, not blocking)

- `Frontend Present: yes` is intentional with zero UI-code change — it gates the browser lane (spec
  IN SCOPE → Frontend). Written as the literal inline line so `detect_frontend_in_plan` parses it.
- The port-free preamble frees **only** `$FRONTEND_PORT` (defined at script line 27) — not the backend
  port — and is placed immediately before the final `exec npx next start`; existing build/stamp logic
  is untouched.
- Number correctness is verified by byte-match against the live API; the anchor values cited here
  (Risk-on 76.05; J-04 +6.12% / p=0.0004998 / vs SPY / 2026-06-30; leadership +6.36%) come from
  `runs/goal-session-mcp-loop/state/certified-claims.jsonl` and are confirmatory references only.

## Goal alignment / scope check

This iteration **advances toward GOAL_ACHIEVED** by closing the verification-integrity gap that the
iter-4 evaluator named as the sole blocker — it does not drift from `docs/goal.md`. **No scope creep:**
no new feature, no new page, no nav/IA change, no new displayed value, no new Evidence Claim, no
`apps/` diff. Out-of-scope items explicitly excluded: adding the optional `tsx` devDependency (not
required for DoD; risks the offline/local-first constraint); any product-code patch (if the browser lane
reveals a genuine **product** defect rather than a harness/capture issue, **stop and flag it** — do not
silently patch UI here).
