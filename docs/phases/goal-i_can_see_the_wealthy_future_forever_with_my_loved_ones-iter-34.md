# Goal Iteration 34 — Live re-verification + closure repair of the dynamic point-in-time universe cluster (J-93/J-94/J-95/J-96)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 34
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-93, J-94, J-95, J-96
- **Required-still-passing journeys:** J-06, J-18, J-07, J-87, J-88, J-89, J-90, J-91, J-92, J-08, J-36, J-37, J-39, J-85
- **Anti-goal reminders** (verbatim from `docs/goal.md`):
  - No lookahead. A score, ranking, regime label, forward-return, drawdown, or membership decision for as-of date D MUST use only data dated on or before D. Removing bars dated after D MUST NOT change any value computed at D.
  - Single source of truth. Every value that appears in more than one place is computed in exactly ONE module and served by exactly ONE endpoint; the frontend re-formats, never recomputes.
  - Snapshots are immutable; the committed price seed is never deleted. A rebuild clears then create-once recomputes the snapshot layer wholesale — never an in-place UPDATE — and never touches the committed daily-price seed.
  - No magic numbers. Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - No fabricated data. An honestly-empty or honestly-small result (warm-up, excluded-by-reason) is shown as such — never padded, never NA-filled into a fake score.
  - Exactly one date control (CRITICAL). There is ONE global as-of date selector and no second/page-local date state.
  - Honest limitations surfaced. Survivorship, warm-up, and universe-relative caveats are stated plainly; data-walled legs are labelled blocked-NA, never faked.
  - No secrets in source. No provider/index-feed key is ever persisted, logged, echoed, or committed.

## GOAL

Produce genuine differential LIVE browser evidence that the already-built dynamic point-in-time universe cluster works in the rendered UI (the `/stocks` membership slides with the global as-of; the `/data` coverage diagnostic, membership timeline, and backward-history control render with their honesty labels), write the missing `ui-test-results.md` closure artifact, and confirm the full backend suite flushes `0 failed` — so J-93/J-94/J-96 can flip `partial → passing`.

## BACKGROUND

The iter-33 FULL iteration BUILT the dynamic-universe cluster correctly: the keystone `universe_resolver.py` is no-magic-number + no-lookahead (14 fast tests GREEN), review/QA/audit all PASS, and coherence is COHERENCE-PASS. It was NOT a GOAL_ACHIEVED candidate for evidence/closure reasons only — the phase-closure-auditor returned CLOSURE-FAIL because `ui-test-results.md` was never written, the J-93 as-of-slide screenshots were byte-identical (md5 ae9c2e38, both showing Latest/122), the J-94/J-96 `/data` capture was an empty loading skeleton, and the full suite GREEN line was never flushed. Per the strict rule (no Must-have marked `passing` without positive evidence of the rendered end state), J-93/J-94/J-95/J-96 sit at `partial`. The iter-33 evaluator prescribed exactly this iteration: a LEAN live re-verification + closure repair with **no backend code rework**. Depth is `lean` because the backend is byte-correct and the only work is a browser-QA pass plus a small frontend render fold-in; coherence is COHERENCE-PASS (no consolidation mandated) and the prior verdict was CONTINUE (not ESCALATE).

Applicable lessons (surfaced for dev/QA/evaluator):
- **iter-33 lesson** — a QA "PASS" can be hollow: a differential journey (membership slides with as-of) REQUIRES TWO byte-DISTINCT frames, and a feature-render journey requires the rendered pixels, not a loading skeleton. md5sum the evidence dir FIRST and open every cited frame. A `/stocks` frame showing 122/122 while the resolver's own stated behaviour is a smaller resolved latest is a red flag the capture predates/bypasses the new code path.
- **iter-18 lesson (7×-recurring)** — `/data` panels (coverage diagnostic, membership timeline) sit BELOW the fold; naive captures land on a blank dark frame or the per-symbol coverage TABLE. Scroll the target panel explicitly into the viewport and capture full-viewport; reject empty-skeleton / wrong-surface frames. DOM/computed-CSS extraction substitutes for a degraded screenshot ONLY when it carries render-only signal.
- **iter-17 / iter-25 / iter-30 lesson** — confirm `:3835` (frontend) + `:8835` (backend) + `:9222` (Chrome DevTools) are all reachable BEFORE scoring; a Chrome ECONNREFUSED hard-SKIP leaves the targets stuck `unknown`/`partial`. Hydration/render journeys need a live runtime, never source review alone.
- **iter-11 / iter-29 lesson** — never block the evaluator on the in-flight full pytest suite; launch it nohup-async to the pump and gate the GOAL_ACHIEVED candidacy on the FLUSHED `0 failed, EXIT 0` line.
- **iter-27 / iter-28b lesson** — resolve sortable / control buttons by `aria-label`, never visible `text()` (nested-span labels make `text()` match nothing → selector false-negative).

## IN SCOPE

### Backend
- [ ] NONE. The backend (engine `universe_resolver.py`, `data_manager` coverage/diagnostic/timeline derivations, `forward_symbols_for_run`, `methodology._universe_selection`) is built and byte-correct as of iter-33 — do NOT modify it. The dev step is effectively a no-op on `apps/backend/app/`. Confirm with `git diff --stat HEAD -- apps/backend/app` that no backend source changes (the only acceptable backend touch is none).

### Frontend (optional, single-file render fold-in — closes the iter-33 coherence Part-C WARN)
- [ ] Widen the `UniverseSelection` TypeScript interface in `apps/frontend/lib/api.ts` (currently `{ membership_rule, thresholds, resolved_size }` at ~line 945) to additionally declare the three fields the backend `methodology._universe_selection` already returns: `candidate_pool_size: number`, `per_date_rule: string`, `per_date_min_history_bars: number`.
- [ ] Render the per-date rule prose on `apps/frontend/app/methodology/page.tsx` Universe Selection section (display `per_date_rule`, with `candidate_pool_size` as the full-pool denominator and `per_date_min_history_bars` as the min-history bar count). Re-format only — read the values verbatim from the existing `GET /api/methodology` payload; introduce NO new value, NO new computation, NO new endpoint, NO new date state. Match the existing methodology section styling (no raw `<div>` soup, design-system tokens only).

This fold-in is OPTIONAL and frontend-only; if it risks delaying the live re-verification (the primary objective), it may be deferred — but it is cheap (one interface + one render block reading already-served fields) and resolves a standing coherence WARN.

### New user-facing capability
No NEW capability is delivered this iteration — the dynamic-universe capability already shipped in iter-33. This iteration makes that capability VISIBLE/verified in the live UI and (via the optional fold-in) surfaces the already-served per-date rule prose on `/methodology`.

### New information displayed
Only the optional fold-in: the `/methodology` Universe Selection section now shows the per-date screen rule prose (`per_date_rule`), the full candidate-pool denominator (`candidate_pool_size`), and the min-history bar count (`per_date_min_history_bars`) — all read verbatim from `GET /api/methodology`.

### New user actions
None.

### UI surface changes
Optional fold-in only: the `/methodology` Universe Selection section gains the rendered per-date rule prose. No new pages, panels, routes, or nav entries.

### Product surface delta
The product experience is unchanged by this iteration except that the per-date universe screen rule (already computed by the backend) becomes readable on `/methodology` instead of being silently dropped by the frontend. The cluster's behaviour itself is verified-as-working, not changed.

### Blueprint conformance
No new surfaces. The optional fold-in renders on the EXISTING Methodology home (`/methodology`, blueprint Information Architecture line 290). The three per-date display fields are registered in the Data Contract row for "Universe membership + selection screen" (blueprint line 335) as additive display fields served by the existing canonical `GET /api/methodology`.

### Data-contract additions
The three methodology display fields (`per_date_rule`, `candidate_pool_size`, `per_date_min_history_bars`) are registered in `blueprint.md` (Data Contract row 335 + Methodology IA row 290) as additive — each is produced by the SINGLE canonical module `methodology._universe_selection` and served by the SINGLE existing endpoint `GET /api/methodology`; the frontend re-formats only. No second computation, no second endpoint, no duplicate of any registered value. No other new displayed value.

## OUT OF SCOPE

- ANY backend source change in `apps/backend/app/` (the backend is correct; touching it would re-open the full pipeline and risk regression). Test-file edits are also out of scope — the iter-33 suite reconciliation (the `macro` shape guard, open_item `iter32-stale-data-overview-shape`) was applied in iter-33; this iteration only CONFIRMS the suite flushes `0 failed`, it does not edit tests.
- Building any NEW feature or journey beyond J-93..J-96 verification + the methodology render fold-in.
- The J-95 real backward-history fetch and the true point-in-time index-constituent feed — these are data-walled and stay honestly `blocked-NA` / non-vetoing (only the confirm-gated control + survivorship label render is in scope to verify).
- J-22 / J-23 / J-24 — data-walled, non-vetoing, unchanged.

## DEFINITION OF DONE

- [ ] `reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-34-ui-test-results.md` is WRITTEN by browser-qa-agent (the artifact whose absence drove the iter-33 CLOSURE-FAIL) with genuine live evidence.
- [ ] **J-93** verified by TWO byte-DISTINCT live frames: stepping the single global as-of from an EARLY date (before the ~2021-10 warm-up boundary → `/stocks` honestly empty/small, never padded) to a FULL date (~2022-01 → full resolved membership). md5sum the evidence dir FIRST; the two frames MUST differ in row count. Reconcile the resolved-latest count against the resolver's stated behaviour (do not accept a stale 122/122 if the running resolver filters to fewer).
- [ ] **J-94** verified live: the `/data` per-date coverage diagnostic panel rendered (admitted count + excluded-by-reason counts: below-history / below-price / below-ADV) — scrolled into the viewport, real numbers visible, NOT an empty skeleton.
- [ ] **J-96** verified live: the `/data` membership-timeline panel rendered (per-date resolved-size step function + entries/exits + excluded-by-reason counts) with the THREE honesty labels visible (candidate-pool survivorship caveat, warm-up boundary, universe-relative breadth caveat).
- [ ] **J-95** verified live: the confirm-gated backward-history extension control + survivorship-bias label render (the real-fetch leg stays honest `blocked-NA`).
- [ ] Required-still-passing journeys remain green via LIVE smoke: J-06 (NVDA leaderboard == detail at a full-universe date), J-18 (0 `<input type=date>`, no second date state, CRITICAL), J-07 (Risk-Off date → zero Actionable, CRITICAL), J-87/J-88 Dashboard Market-Phase panel unchanged at a full-universe date; J-89/J-90/J-91/J-92 and J-08/J-36/J-37/J-39/J-85 carried (consumed-layer / coverage / immutability byte-unchanged).
- [ ] If the optional fold-in is included: `/methodology` Universe Selection section renders the per-date rule prose; `tsc --noEmit` exits 0; coherence stays COHERENCE-PASS (Part-C WARN resolved).
- [ ] No anti-goal violation introduced (CRITICAL: exactly one date selector; no lookahead; snapshots immutable / seed undeletable; single source).
- [ ] The FULL backend pytest suite flushes `0 failed, EXIT 0` — launched nohup-async to the pump, NOT blocking the evaluator. (Backend source is byte-unchanged, so the iter-33-reconciled suite is the standing gate; confirm the flushed line.)
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-34-dev.md` stating explicitly that the backend diff is empty and listing the (optional) frontend files touched.

## TESTING REQUIREMENTS

- **Browser (primary gate this iteration):**
  - J-93 — two byte-distinct `/stocks` frames across the early→full as-of step (md5sum-verified distinct; row counts differ; early date honestly empty/small).
  - J-94 — `/data` coverage-diagnostic panel scrolled into viewport with rendered admitted + excluded-by-reason counts.
  - J-96 — `/data` membership-timeline panel scrolled into viewport with rendered step function + entries/exits + the three honesty labels.
  - J-95 — confirm-gated backward-history control + survivorship label rendered (real fetch stays blocked-NA).
  - Required-still-passing live smoke: J-06, J-18 (CRITICAL), J-07 (CRITICAL), J-87, J-88.
  - If the fold-in is included: `/methodology` Universe Selection per-date prose rendered.
  - Evidence hygiene (mandatory): md5sum the evidence dir FIRST; capture per-surface (one capture per claimed surface); scroll below-the-fold `/data` panels explicitly into the viewport; resolve any control button by `aria-label`, never visible `text()`; VIEW the pixels of every cited frame.
- **Unit/integration:** No NEW backend tests (backend unchanged). Confirm the FULL backend pytest suite flushes `0 failed, EXIT 0` (nohup-async via the pump; gate on the flushed terminal line, never the in-flight stream). If the fold-in is included, `tsc --noEmit` must exit 0 (the frontend has no unit-test harness beyond the type check).
- **Error cases:** Verify the EARLY-date `/stocks` honestly renders empty/small membership (no fabricated/padded rows) — the warm-up boundary case. Confirm an invalid/unknown `?asof` still degrades to latest with no fabricated date (J-43/J-83 invariant, incidental).

## NOTES

- This iteration directly executes the iter-33 evaluator's next-step recommendation: a LEAN live re-verification + closure repair, NO backend rework.
- Environment precondition: bring up backend `:8835` + frontend `:3835` + Chrome DevTools `:9222` and confirm all three are reachable BEFORE running browser-QA (the iter-33 env was down; iter-17/25/30 precedent — a hard-SKIP leaves targets stuck `partial`/`unknown`). Per `MEMORY.md`, the backend needs `CORS_ORIGINS` including `:3835`, and never use broad `pkill` — manage dev servers by port on this multi-project machine.
- Do NOT trigger any destructive `/data` action during QA. Per `MEMORY.md`, a `kind:"rebuild"` is ~11h and clears the snapshot layer; the J-85/J-95 confirm-gated rebuild/backward-history controls are guard-protected and the browser-QA must verify the CONTROL RENDERS only — it must NOT execute a live rebuild. Likewise the destructive `POST /api/data/remove` on a real symbol must not be exercised (use the preview/render-only path).
- If browser-QA actually runs live and passes, do not let a conservative QA-report "defer" downgrade the journeys (iter-26 precedent — read `ui-test-results.md` directly).
- After the three targets close green on LIVE differential evidence, `ui-test-results.md` exists (closure passes), the suite flushes `0 failed`, with zero regression and COHERENCE-PASS — every buildable Must-have is passing and the next evaluation is a GOAL_ACHIEVED candidate. J-22/J-23/J-24 + J-95's real-fetch / constituent-feed legs stay honestly `blocked-NA` (non-vetoing per `docs/goal.md`).
- Blueprint already updated (additive): the three methodology per-date display fields registered in the Data Contract (row 335) + Methodology IA (row 290). No nav-skeleton change → no re-approval requested.
