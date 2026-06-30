# Goal Iteration 2 — First referee-certified claim: light the Leadership "Proven" badge + proof drill-down

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-02, J-05
- **Required-still-passing journeys:** J-01, J-03
- **Anti-goal reminders:**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## GOAL

Ship the session's first referee-certified claim so the Leadership score reads a real, audited **"Proven"** — drillable on `/stocks/{ticker}` to its out-of-sample test + SPY control + claim id/date (J-02) and rendered as a populated, link-backed row on `/evidence` (J-05) — while every uncertified score stays honestly "Not yet proven."

## BACKGROUND

J-01/J-03 are green and `/evidence` exists, but they all read "Not yet proven" because the ledger is empty (iter-1 built the read path against an empty ledger). This is the **first certified iteration**: a narrow `## Evidence Claim` (the top decile of `leadership_score`, the strongest a-priori edge in the factor set) is run through the post-decompose gate's referee **before any code is built** — a PASS appends the first ledger entry and structurally unblocks J-02 (proof drill-down) and J-05 (a populated, link-backed claim row). Full depth is warranted (and was the iter-1 evaluator's recommendation): it ships a new "Proven" data surface gated by the referee plus new drill UI that needs the browser-QA / ux-regression / closure lanes.

**Lesson applied (iter-1 — Applies to: the first certified iter / `verify_edge` / `evidence` / `/evidence`):** a referee PASS does NOT light a badge unless the **canonical signal key is carried on the written claim** — the read side keys `proven_signals` on `claim.get("signal")` (fail-safe), and a signal-less PASS stays "Not yet proven." Critically, the gate's `verify_edge` writes the ledger entry *before* the developer runs, so the signal must already be on the claim the gate writes — not stamped by a not-yet-run writer. This spec puts the canonical `signal` on the Evidence Claim JSON (the assembler ignores non-selector keys; `verify_edge` persists `claim` verbatim), so the gate's own write carries it. The DoD therefore requires browser-verifying that the PASS **actually flips the Leadership badge to "Proven" end-to-end**, not merely that a ledger row exists. (iter-0 lesson — Applies to any iteration: full depth must actually run the browser-QA lane and capture real screenshots; a missing ui-test-results file is a hard fail.)

## IN SCOPE

### Evidence Claim (certified by the post-decompose gate BEFORE build — a non-PASS blocks this iteration)

See the `## Evidence Claim` section below. It is the **top decile (decile 10) of `leadership_score`** at the config default horizon (20), claimed positive vs the same-dates SPY control. `leadership_score` is itself a factor-catalog key that is byte-identical to the UI signal key, so the cohort *is* the Leadership score's top decile — a tautologically honest binding. The JSON carries `"signal": "leadership_score"` so the gate's verbatim ledger write lands the canonical signal on the entry (see Background). First claim ⇒ `n_trials=1`, full alpha budget ⇒ minimal multiple-testing deflation; a full-history decile spans far more than the referee's 5-sealed-holdout-date floor, so INSUFFICIENT is unlikely.

### Backend
- [ ] **No new computation and no new endpoint.** The certified-claims value, its canonical module (`app.engine.evidence:build_evidence_payload`), and its single endpoint (`GET /api/evidence`) already exist and already serve every field the UI needs (`verdict.status`, `verdict.holdout_edge`, `verdict.p_value`, `verdict.control_excess`, `register_date`, `signal`, `proven`, `forward_walk`). The gate's `app.mcp.tools:verify_edge` writes the certified entry; the read path serves it unchanged. Do **not** add a second computing path or a second endpoint for proven-ness (Data Contract row 1 is canonical).
- [ ] **Optional hardening (recommended, non-blocking):** in `app.engine.evidence` (`build_evidence_payload`/`_claim_row`), when a PASS entry's cohort is a score-column factor (`claim.kind == "factor"` and `claim.factor ∈ {leadership_score, entry_quality_score, risk_score}`) but its written `claim` omits `signal`, **derive** `signal = claim.factor`. This is display-routing only (proven-ness still comes 100% from `verdict.status == PASS`), non-spoofable (only the three score columns self-map), and prevents a future claim that forgets the field from silently going dark. It does NOT compute proven-ness and adds no new contract value.

### Frontend
- [ ] **J-02 proof drill-down on `/stocks/{ticker}`** (`apps/frontend/app/stocks/[ticker]/page.tsx`, the `ScoreCard` around the existing `EvidenceStatusBadge` at ~L582–607). When a score is **proven**, add an in-place expandable "proof" disclosure (e.g. a "Why proven?" toggle / panel) that reveals — read **verbatim** from the already-fetched `provenSignals[signal]` row (no new fetch, no recompute):
  - the **out-of-sample test result** — `verdict.status` + `verdict.holdout_edge` + `verdict.p_value` (and `cohort_n`/holdout dates if available);
  - the **control comparison vs SPY** — `verdict.control_excess`, labeled "vs SPY (benchmark control)";
  - the **certified-claim id + registration date** — the stable identifier `signal · registered <register_date>` (matching the `/evidence` anchor `#signal-leadership_score`), plus a link to that backing ledger row.
  When the score is **not** proven, the disclosure is absent/disabled (no empty panel). Additive only — the score number itself is unchanged.
- [ ] **Verify (already coded in iter-1 — exercise, don't rebuild):** `/evidence` `ClaimRow` now renders the populated `leadership_score` claim (Hypothesis chips, Out-of-sample verdict + holdout edge, Control comparison vs SPY, Registration date, Forward-walk score-to-date = "Pending") with its `id="signal-leadership_score"` anchor and the **"Backs: Stocks leaderboard →"** linkback (J-05 steps 2–3).
- [ ] **Verify (already wired):** the `/stocks` leaderboard and stock-detail Leadership badge now read **"Proven"** (accent chip, links to `/evidence#signal-leadership_score`); Entry Quality and Risk badges stay **"Not yet proven"** (no claim backs them).
- [ ] **Optional (coherence WARN cleanup, non-blocking):** extract the duplicated `SCORE_SIGNALS` constant from `apps/frontend/app/stocks/page.tsx` and `apps/frontend/app/stocks/[ticker]/page.tsx` into `apps/frontend/lib/evidence.ts` (one canonical definition).

### New user-facing capability
A user can, for the first time, see a score marked **Proven** and audit *why*: from a stock's detail page they expand the Leadership score's proof to read the out-of-sample test, the SPY control comparison, and the certified-claim id/date — and follow it to the backing row on the Evidence ledger.

### New information displayed
A populated certified-claims row on `/evidence` (the first real claim) and an inline proof panel on stock detail: out-of-sample holdout edge + p-value + status, SPY control excess, and the certified-claim id + registration date — all read verbatim from `GET /api/evidence`.

### New user actions
Expand/collapse the "proof" disclosure on a proven score (stock detail); click the "Proven" badge to jump to its `/evidence` row; click a claim's "Backs: Stocks leaderboard →" link to return to the surface it backs.

### UI surface changes
`/stocks/{ticker}` score cards gain an expandable proof panel for proven scores. `/stocks` leaderboard and `/evidence` change only in state (a real "Proven" badge; a populated claim row) — no new pages, no nav change.

### Product surface delta
The platform crosses from "every signal honestly unproven" to "one signal is referee-certified and fully auditable, the rest still honestly unproven" — the evidence layer's core promise, demonstrated end to end.

### Blueprint conformance
No new surfaces or nav. The J-02 proof panel lives on `/stocks/{ticker}` — already the blueprint's canonical home for "drill into the proof behind a score (badge → proof panel)". `/evidence` is the existing J-05 home. The drill panel is an additional **reader** of the already-registered `GET /api/evidence` payload.

### Data-contract additions
None — no new displayed value. Everything shown is the already-registered "Evidence status + certified-claim" value (Data Contract row 1), read from its single canonical endpoint `GET /api/evidence`. The blueprint's row-1 notes are clarified (additive edit) to record the score-column **factor==signal binding** and the J-02 drill panel as a second reader of the same payload. No new computing module, no second endpoint, no nav-skeleton change ⇒ no re-approval required.

## Evidence Claim

```json
{"kind": "factor", "factor": "leadership_score", "slice_kind": "decile", "decile": 10, "horizon": 20, "direction": "positive", "signal": "leadership_score"}
```

The gate runs this through the referee (sealed temporal holdout + same-dates SPY control + multiple-testing deflation) and appends the verdict to `runs/goal-session-mcp-loop/state/certified-claims.jsonl`. A `FAIL` or `INSUFFICIENT` verdict **blocks** the iteration (see NOTES for the recovery path).

## OUT OF SCOPE

- **J-04 (regime-conditioned evidence)** — deferred to iter-3. A regime slice (`slice_kind: "regime"`) narrows the cohort by date and risks an INSUFFICIENT verdict; do not jeopardize the first PASS. iter-3 adds a regime-conditioned claim once this end-to-end "Proven" path is browser-proven.
- **Proving Entry Quality or Risk** — only `leadership_score` is claimed this iteration; the other two stay honestly "Not yet proven" (do not fabricate a status for them).
- **Multi-control set (QQQ / sector ETF / random same-sector).** The referee currently certifies against the **SPY benchmark control** (`_benchmark_control_observations`); the panel shows that control honestly labeled "vs SPY". Adding more controls would either fabricate uncomputed comparisons (anti-goal: honesty) or change the referee's pass bar — both are a separate controls-enrichment iteration.
- Any change to the three scores' computation, the regime/forward-return engines, or `GET /api/evidence`'s shape.
- A second proven-ness computation or a second evidence endpoint (forbidden — Data Contract row 1 is canonical).

## DEFINITION OF DONE

- [ ] The post-decompose gate returns **PASS** for the Evidence Claim and the first entry is appended to `certified-claims.jsonl`.
- [ ] Target journeys **J-02** and **J-05** pass via browser-qa-agent with real screenshots:
  - J-02: on `/stocks/{ticker}` a Leadership "Proven" badge expands to a panel showing the OOS test result, the SPY control comparison, and the certified-claim id + registration date — values byte-identical to `GET /api/evidence`.
  - J-05: `/evidence` renders the populated `leadership_score` claim row (all five fields) and its "Backs: Stocks leaderboard →" link navigates to `/stocks`; the leaderboard "Proven" badge links back to `/evidence#signal-leadership_score`.
- [ ] **End-to-end badge flip is browser-verified** (per the iter-1 lesson): a real screenshot shows the Leadership badge reading "Proven" on `/stocks` AND stock detail — not merely a ledger row in JSON.
- [ ] Required-still-passing **J-01** and **J-03** remain green: every leaderboard score still shows a status (Leadership now "Proven"; Entry Quality + Risk still "Not yet proven"), and no uncertified signal is shown as confident.
- [ ] No anti-goal violation: nothing uncertified reads "Proven"; displayed numbers match the engine; no return/price/buy-sell/order language; determinism/no-lookahead preserved; no secrets.
- [ ] Unit tests pass; no regression in `/api/stocks`, `/api/evidence`, or the evidence resolver. New/updated tests cover the proof-panel rendering and (if implemented) the read-side signal derivation.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-2-dev.md`.

## TESTING REQUIREMENTS

- **Browser (must verify, by ID):**
  - **J-02** — `/stocks` → click a stock → expand the Leadership proof; assert the OOS test, SPY control, and claim id/date render and match `/api/evidence`.
  - **J-05** — `/evidence`; assert the populated `leadership_score` row (5 fields) + working "Backs:" linkback; assert the leaderboard badge → `/evidence#signal-leadership_score` round-trip.
  - **J-01** (regression) — `/stocks`: every score still shows a status; Leadership "Proven", others "Not yet proven".
  - **J-03** (regression) — Entry Quality + Risk still read "Not yet proven", never a confident number.
- **Unit/integration:**
  - The proof panel reads `provenSignals[signal]` verbatim and shows nothing for an unproven signal (fail-safe).
  - If the read-side derivation is implemented: a PASS entry whose claim cohort is a score-column factor maps to that signal in `proven_signals`; a non-score cohort or non-PASS entry does NOT (assert exact `proven_signals` keys).
  - `build_evidence_payload` against a ledger with the certified leadership entry returns `proven_signals["leadership_score"].proven == true` with the verdict fields intact.
- **Error cases:** an absent/empty/unreadable ledger still yields `{"claims": [], "proven_signals": {}}` (200, never 500) and every badge reads "Not yet proven"; a fetch failure on the stock-detail page leaves badges fail-safe ("Not yet proven", no proof panel).

## NOTES

- **If the gate blocks (FAIL/INSUFFICIENT):** the iteration does not build (by design — anti-goal: no uncertified edge ships). Recovery in iter-3: re-aim the claim — try another economically-sound score-backing cohort (e.g. `rs_spy_3m` decile 10), a different horizon from `[1,5,10,20,60]`, or accept the referee's honest verdict that top-decile Leadership is not OOS-provable on this seed and surface it as such. Do not loosen the referee to force a PASS.
- **Why `signal` lives on the claim JSON, not a writer change:** the post-decompose gate runs `verify_edge` and writes the ledger entry *before* the developer runs, so a writer-stamp added this iteration would miss the gate's own write. The assembler (`assemble_claim_observations`) only consumes `_CLAIM_SELECTOR_KEYS`, so the extra `signal` key is ignored during cohort assembly and persisted verbatim into the entry's `claim` — read back by `_claim_row` via `claim.get("signal")`. The optional read-side derivation is defense-in-depth for future claims.
- **Honesty boundary for J-02 controls:** the panel shows the single SPY benchmark control the referee actually used. The broader control menu named in goal.md (QQQ / sector ETF / random same-sector) is a future controls-enrichment iteration; showing uncomputed controls would violate the displayed-numbers-are-correct anti-goal.
- Sources grounding this spec: `apps/backend/app/mcp/tools.py` (`verify_edge`, `assemble_claim_observations`, `_CLAIM_SELECTOR_KEYS`), `apps/backend/app/engine/evidence.py` (read path), `apps/backend/app/engine/referee.py` (5-holdout-date floor, SPY control), `apps/backend/app/config.py` (factor keys = signal keys; horizons), `apps/frontend/app/evidence/page.tsx` (`ClaimRow` already built), `apps/frontend/app/stocks/[ticker]/page.tsx` (`ScoreCard` + `provenSignals` already fetched).
