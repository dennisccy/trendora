# Goal Iteration 41 — Phase-conditional drawdown & dry-spell expectations panel on `/evidence` (J-25)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 41
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-25
- **Required-still-passing journeys:** J-01, J-02, J-04, J-05, J-11, J-10, J-13, J-15, J-16, J-20
- **Evidence Claim:** NONE — J-25 introduces NO proven-language and carries NO `## Evidence Claim` (B-205: "N/A — this card must not introduce proven-language anywhere"). The post-decompose gate passes automatically; the canonical Bonferroni divisor stays 8; both ledgers stay byte-identical (7/7 FAIL, 0 PASS).
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*

## GOAL

On a certified claim's detail on `/evidence`, the user sees an honest, phase-conditional **expectations panel** — historical distributions (median / p90) of max-drawdown depth, underwater duration, time-to-recover, and longest losing streak, split by the causal market phase at entry, each with its sample size `n` (thin phases read "insufficient (n=…)") — so a normal dry spell reads as a known, pre-committed historical fact instead of a surprise.

## BACKGROUND

J-25 (backlog **B-205**) is the LAST unbuilt Must-have; delivering and verifying it makes GOAL_ACHIEVED reachable (after the iter-42 lean closeout). The iter-40 evaluator explicitly recommended **iter-41 = FULL J-25**. Depth is **full** because this is one risky journey that crosses backend+frontend and touches the data model: it adds two append-only stored columns to `ForwardReturn`, a new pure aggregation in `forward_testing.py`, an additive field on `GET /api/evidence`, a new panel on the `/evidence` claim rows, AND a bounded backfill of the new columns over the deep 30-year basis (the anti-goal #8 memory-risk surface). New non-browser tests are required (fixture-exact aggregation, no-lookahead/causal-phase, correctness re-derivation, memory-under-cap). This is exactly one risky element (the stored-field addition + its backfill); everything else is mechanical additive work — it does not bundle a second risky change.

Unlike the five stuck evidence journeys (J-02/J-06/J-07/J-08/J-09, which need a PASS certified edge that does not exist on this basis), **J-25 is outcome-neutral**: the expectations panel is descriptive cohort history and renders for ANY claim regardless of its PASS/FAIL verdict (the ledger is 7/7 FAIL). So J-25 CAN fully pass on the current FAIL ledger — the iter-28 "honest-absence ≠ acceptance" lesson does NOT apply here.

## IN SCOPE

### Backend

- [ ] **Two new append-only stored path columns on `ForwardReturn`** — `underwater_days` (count of the first-`horizon` post-snapshot bars whose close is below the entry high-water mark) and `time_to_recover_days` (bars from the max-drawdown trough until close first returns to the entry level within the horizon; NA if it never recovers in-window). Computed ONCE in the SAME `_insert_run_forward_returns` INSERT pass as `max_drawdown`, from the SAME `post_bars` already in hand (ZERO extra bar reads), sharing the identical no-lookahead NA gate (non-None iff `realized_return` exists; `< horizon` post-bars ⇒ NO row / None, never a fabricated 0). Model docstring mirrors the existing `max_drawdown` (iter-27/J-86) column note. This is the J-86 precedent applied verbatim.
- [ ] **New pure path helpers in `app.engine.forward_testing`** — `underwater_days(post_bars, entry_close, horizon)` and `time_to_recover_days(post_bars, entry_close, horizon)`, forward-side only, same NA gate as `forward_return`/`max_drawdown`. **REUSE the existing `max_drawdown` helper verbatim for DD-depth — do NOT fork or re-derive it** (B-205 ★ Do NOT touch). Fixture-tested against constructed series with known underwater spells / recovery points.
- [ ] **New aggregation `compute_drawdown_expectations(session, claim, cfg)`** in `forward_testing.py` — for ONE claim's cohort, resolve the observation set via the SAME cohort selectors `GET /api/research/samples` uses (factor+decile+horizon OR the combination `condition`-string form — no second cohort resolver), read each observation's STORED `realized_return`, `max_drawdown`, `underwater_days`, `time_to_recover_days` (read verbatim — recompute nothing), join each to its **causal phase at entry** via `app.engine.market_phase:phase_context_by_date` (keyed on the observation's `asof_date`), and emit per-phase distributions {median, p90} of the four measures + `n`. Loss-streak = the longest run of consecutive **negative** cohort forward-returns taken at the **walk-forward cadence** (NOT daily — avoids overlapping-horizon double-count, B-205 trap), stated in a method note. Per-phase distribution cells below `walk_forward.min_sample` render "insufficient (n=…)"; loss-streak cells below `walk_forward.streak_min_n` likewise. Pure read-compose — recomputes NO existing canonical value.
- [ ] **Config additions (no inline literals):** `walk_forward.underwater_horizons` (the forward horizon(s) over which underwater / time-to-recover are measured and reported) and `walk_forward.streak_min_n` (loss-streak honesty floor). Per-phase distribution floor REUSES the existing `walk_forward.min_sample` (30) — no new threshold for those.
- [ ] **Additive `expectations` field per claim on the EXISTING `GET /api/evidence`** — the route/`build_evidence_payload` path threads a DB session + config and attaches `compute_drawdown_expectations` output to each claim row. No new endpoint, no new page. Missing/empty ledger or an unresolvable cohort ⇒ honest empty/NA `expectations` (200, never 500).
- [ ] **Bounded backfill of the two new columns over the served aggregation window** so the deep historical phases (Correction / Bear from 2000 / 2008 / 2020 / 2022) carry enough observations to clear the per-phase floor. Reuse the EXISTING memory-hardened forward-returns backfill/warmup path (per-symbol bounded reads from the resident bar cache; `MALLOC_ARENA_MAX` + `gc.collect()`/`malloc_trim(0)`; deep-history cadence bound). Newly-served snapshots get the columns immediately; historical rows stay honest-NA until this sanctioned backfill runs (iter-40/J-24 precedent). **This is the one risky element — anti-goal #8 guardrails are mandatory (see TESTING).**

### Frontend

- [ ] **Expectations panel inside the `/evidence` `ClaimRow`** (`apps/frontend/app/evidence/page.tsx`) — an additive section per claim card rendering the per-phase table (phase × {max-DD depth, underwater duration, time-to-recover, longest losing streak}, each median/p90 + `n`), reading the `expectations` field verbatim from `GET /api/evidence` (NEVER recomputing in the browser). Thin phases render "insufficient (n=…)". Copy is strictly **historical** — "In {Phase} phases, top-decile entries **historically saw** a median max-DD of … (p90 …), typical underwater time … , losing streaks up to … (n=…)" — with a visible method note (walk-forward-cadence streaks) and the **B-111 survivorship caveat** ("read as an upper bound; free Stooq has no delisted names").
- [ ] **Nullable-field discipline (iter-18/19 lesson):** the new `underwater_days` / `time_to_recover_days` are nullable; type them `number | null` at the `lib/api.ts` contract boundary and route every consumer (format/sort/`.toFixed`) through a guarded NA render — never an unguarded call that can crash the card on `null`.

### New user-facing capability

The user can open any certified claim on `/evidence` and read, per market phase at entry, what following this methodology has historically felt like (drawdown depth, time underwater, time to recover, worst losing streak) with honest sample sizes — expectation-setting history, never a forecast.

### New information displayed

Per-claim, per-phase historical distributions (median / p90 + `n`) of: max-drawdown depth, underwater duration, time-to-recover, and longest losing streak; "insufficient (n=…)" where a phase is below the floor; a walk-forward-cadence method note and the survivorship caveat.

### New user actions

None (read-only descriptive panel; it renders within the existing `/evidence` claim cards — no new controls, forms, or navigation).

### UI surface changes

Additive section inside the existing `/evidence` claim-row cards. No new page, no new route, no nav change.

### Product surface delta

`/evidence` evolves from "the certified-claims ledger" to "the ledger + the honest, phase-conditional drawdown/dry-spell history behind each claim's cohort" — pre-committed drawdown psychology, quantified.

### Blueprint conformance

`/evidence` (the claim-detail cards), under the existing **Evidence [NEW]** nav section — J-05's canonical home, already in the Information Architecture. The panel is additive to J-05's existing surface: no new page, no new route, no nav-skeleton change. (Blueprint IA table updated with a J-25 home row; additive edit, no re-approval required.)

### Data-contract additions

ONE new displayed value — **Phase-conditional drawdown & dry-spell expectations** (per certified-claim cohort). Registered in `blueprint.md`'s Data Contract this iteration:
- **Computed once by:** `app.engine.forward_testing:compute_drawdown_expectations` — a PURE read-compose over STORED `ForwardReturn` values (`realized_return`, `max_drawdown` [reused verbatim, NOT forked], and the new stored `underwater_days`/`time_to_recover_days` computed alongside `max_drawdown` in `_insert_run_forward_returns`), grouped by the causal phase-at-entry from `app.engine.market_phase:phase_context_by_date` (the stored causal timeline), resolving each claim's cohort via the SAME selectors `/api/research/samples` uses. Recomputes no existing canonical value.
- **Served by:** additive `expectations` field per claim on the EXISTING `GET /api/evidence` (the ONE endpoint `/evidence` reads). No new endpoint.

## OUT OF SCOPE

- The **backtest-page** expectations panel and the later **B-1203 Sunday sheet** reader (B-205 lists both as additional surfaces; J-25's binding acceptance is the `/evidence` claim detail ONLY) — deferred.
- Any `## Evidence Claim` / new certified edge / promotion — B-205 forbids proven-language; the divisor stays 8 and both ledgers stay byte-identical.
- **Forking or altering** the `max_drawdown` helper or the causal phase-timeline computation — both are reused verbatim (B-205 ★ Do NOT touch MDD depth; the phase timeline is the single causal source).
- **Reusing `market_phase`'s trailing `time_underwater` severity component** as the forward underwater-duration — it is a DIFFERENT concept (a causal *trailing* phase-classification input, not a forward per-entry duration). Do NOT conflate them.
- Any change to the Leadership / Entry Quality / Risk scores, regime score, or existing forward-return aggregates — the expectations attach additively; those values stay byte-identical.
- Nav-skeleton changes, new routes, new pages, or a full DB re-scoring/rebuild beyond populating the two new `ForwardReturn` columns.
- CVaR/tail measures (B-206), phase-transition cards (B-207), sequence-risk Monte Carlo (B-208) — separate backlog cards, not this journey.

## DEFINITION OF DONE

- [ ] **J-25 passes via browser-qa-agent:** on a certified claim's detail on `/evidence`, an expectations panel renders per-phase (median/p90) distributions of max-DD depth, underwater duration, time-to-recover, and longest losing streak, each labeled with `n`; phases below the floor read "insufficient (n=…)"; wording is historical ("historically saw") with ZERO forecast/promise phrasing (steps 1–3 of J-25).
- [ ] **Correctness (anti-goal #3):** one cell (e.g., Correction-phase median max-DD depth) re-derived offline byte-matches the served value.
- [ ] **Single source:** `compute_drawdown_expectations` is the ONLY module computing the panel; the `/evidence` UI re-reads it verbatim (no client-side recompute); `max_drawdown` is reused, not forked; Leadership/Entry Quality/Risk scores + regime + existing forward-return aggregates are byte-identical (existing `forward_testing`/`scoring` expectation tests are UNEDITED and green — iter-9 proof-of-no-regression).
- [ ] **No-lookahead (anti-goal #5):** phase-at-entry is the causal `phase_context_by_date` label as-of the entry date; underwater/recover use bars > as-of within the first `horizon`; scoring uses bars ≤ as-of; a no-lookahead unit test passes (a future bar cannot change a stored value or a phase label).
- [ ] **Anti-goal #8 (memory/scale):** the new-column backfill runs to completion under the 6144 MB cap on the FULL-universe shape with BOTH VSZ and RSS sampled (iter-26 lesson — RSS-only on a subset does not count); no whole-table ORM load introduced; `/api/evidence` + `/evidence` do not regress the J-15 latency budget (measured, recorded in `reports/perf-budgets.md`).
- [ ] **No proven-language / no advice (anti-goals #1/#2):** the panel carries no "Proven"/"Not yet proven" badge and no buy/sell/trim/reduce/rebalance/target verb; no `## Evidence Claim` in this spec (gate passes automatically; divisor stays 8; both ledgers byte-identical).
- [ ] **Required-still-passing journeys (J-01, J-02, J-04, J-05, J-11, J-10, J-13, J-15, J-16, J-20) remain green** — live-verified this iteration via browser-qa; deterministic golden-replay of the full set is DEFERRED to the iter-42 lean closeout (the known structural FULL-iter replay gap — see NOTES).
- [ ] Unit/integration tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-41-dev.md`.

## TESTING REQUIREMENTS

- **Browser (canonical browser-qa-agent):**
  - **J-25** — open a certified claim on `/evidence`, scroll the expectations panel into frame, assert the per-phase distributions render (median/p90 + n for all four measures), a below-floor phase reads "insufficient (n=…)", and the copy is historical with no forecast/promise phrasing. The panel is **below the fold inside a claim card** — use full-page or element-clip capture and `md5`-check for reused/blank frames (iter-3/11/13/14 lesson).
  - Required-still-passing live re-verification: `/evidence` still renders the 7 claim rows with byte-correct verdict/control/registration fields (J-05), the "Not yet proven" badges (J-01), the no-stale-edge invariant on the 0-PASS ledger (J-11), the regime-labeled claim rows (J-04), the score drill (J-02); plus core smoke: `/stocks/{ticker}` deep history (J-10), `/data` (J-13), the "GO" preflight strip (J-20).
- **Unit/integration:**
  - Pure `underwater_days` / `time_to_recover_days` helpers — fixture series with KNOWN spells/recovery → exact stats; NA on `< horizon` post-bars (never a fabricated 0); same NA gate as `max_drawdown`.
  - `max_drawdown` REUSED not recomputed — call-count or byte-identity assertion that the new columns do not re-derive DD depth.
  - `compute_drawdown_expectations` — fixture cohort with constructed per-phase observations → exact per-phase median/p90/n; a phase below `walk_forward.min_sample` emits "insufficient", not a distribution; loss-streak computed at walk-forward cadence (fixture proving daily overlap does NOT double-count).
  - No-lookahead / causal-phase — phase-at-entry equals the causal `phase_context_by_date` label as-of the entry date; adding a later bar changes no stored value and no phase label.
  - Single-source / no-regression — existing `forward_testing` + `scoring` expectation tests unedited & green; scores/regime/forward-return aggregates byte-identical; `GET /api/evidence` `claims`/`proven_signals` unchanged apart from the additive `expectations` field.
  - Memory — the new-column backfill on the full-universe shape stays under the 6144 MB `ulimit -v` cap, VSZ+RSS sampled (iter-26).
- **Error cases:**
  - Missing/empty ledger ⇒ `GET /api/evidence` still 200 with `claims` + honest empty `expectations`.
  - A cohort that resolves to zero observations, or a phase with no observations ⇒ honest empty/"insufficient" panel, never a 500 or a fabricated cell.
  - A `null` `underwater_days`/`time_to_recover_days` ⇒ guarded NA render, never an unguarded crash of the claim card (iter-18/19).

## NOTES

- **Assumption logged** (`runs/goal-session-mcp-loop/state/assumptions.md`, iter-41): B-205's "pure aggregation helpers" leaves open whether underwater-duration / time-to-recover are stored or computed on-read. We chose **per-observation path stats over the first-`horizon` post-snapshot bars, stored additively on `ForwardReturn` alongside `max_drawdown` (J-86 precedent) and backfilled over the deep window** — because on-read per-observation bar reads on `/api/evidence` would regress the J-15 latency budget, and the deep historical phases need populated coverage to clear the floor. Reversible (additive columns / additive field / additive panel).
- **HARD PRECONDITION (from iter-40 eval):** the coordinator/pump must investigate the **Chrome-MCP DevTools port-binding outage** that made iter-40's canonical browser-qa lane SKIP all 16 tests. If it recurs, J-25's canonical browser evidence degrades the same way — and per the iter-40 lesson, the evaluator should then fall back to the demo-narrator (Playwright) frames + functional-QA frames + the auditor byte-match, not default J-25 to `unknown`.
- **FULL-iter replay gap (systemic, recurred iter-33/36/38/40):** a FULL iteration routes through `run-phase.sh`, which has NO deterministic replay lane, so the "required-still-passing golden replay" DoD line is structurally unsatisfiable here. This iteration live-verifies the required set via browser-qa; the deterministic golden replay of the full set (folding in the never-replayed J-23.json [4th carry], J-24.json, and the new J-25.json) is the **iter-42 lean closeout's** job. Do NOT let a stage paper this over with an unevidenced "replay ran next step" claim (iter-33/36 CLOSURE-FAIL trap).
- **Below-the-fold capture discipline (iter-3/11/13/14):** the panel is inside a claim card below the fold — full-page/element-clip captures only; md5-scan the evidence dir; a header-only or blank frame proves nothing.
- **Backend-shared-value proof (iter-9):** the regression proof for the forward_testing change is byte-identical canonical output + UNEDITED green existing tests — if any existing forward_testing/scoring expectation test must be EDITED to pass, that edit is itself the regression signal.
- **Outcome-neutral (do not misapply iter-28):** the panel renders for any claim regardless of PASS/FAIL; the demo picks any of the 7 FAIL claims. J-25 does NOT require a PASS certified edge, so it is fully passable on the current ledger.
- **Wording is the guardrail (B-205):** "historically saw", never "expect to lose at most" / "you will" / any promise in either direction; carry the B-111 survivorship caveat (upper-bound reading).
