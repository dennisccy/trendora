# Goal Iteration 40 — Per-stock "how much can this hurt" risk-budget card (J-24 / B-201)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 40
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-24
- **Required-still-passing journeys:** J-01, J-02, J-03, J-05, J-10, J-12, J-13, J-20
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*

## GOAL

On every stock's detail page (and as columns on the leaderboard), show an honest, descriptive **risk-budget card** — ATR%, downside volatility, overnight-gap profile (median / p95 / worst), the worst historical 20-day window, and distance-to-invalidation — each with a cross-sectional universe-percentile context label, sourced once from the stored snapshot record.

## BACKGROUND

The 23 built Must-haves are green; the only remaining unbuilt journeys are J-24 (this iteration) and J-25 (iter-41), after which GOAL_ACHIEVED becomes reachable. The iter-39 CONTINUE evaluation recommended **iter-40 = FULL J-24** (backlog **B-201**), the owner's post-iter-28-plateau pull of a NO-SPEND risk-analytics card that carries **no Evidence Claim**. Depth is **full** because this iteration (1) crosses backend + frontend, (2) changes the snapshot data shape (new stored risk components + their cross-sectional percentiles), (3) needs new unit/fixture tests beyond browser smoke (pure gap-stats / worst-window functions with exact-value asserts + a byte-match spot check + methodology-catalog completeness), and (4) the prior evaluator recommended full — any one triggers full; all four hold. B-201 is the binding detailed spec (its What / How / Config surface / ★ Canonical value / ★ Do NOT touch / Traps were read before planning). Applicable lessons carried in: the **iter-24/26/27 anti-goal #8 OOM lesson** (bounded per-symbol as-of reads only; never a whole-table load; never a full-universe 30-year rebuild) and the **iter-18/19 nullable-field lesson** (NA over fabrication for thin history; contained degradation, never a blank crash). B-201's dominant failure mode is **UI-recompute** — the card and columns re-read stored fields, never recompute gap stats in the browser.

## IN SCOPE

### Backend
- [ ] Add PURE functions to `app/engine/indicators.py`: (a) an **overnight-gap profile** over the as-of bars (distribution of `|open − prior close| / prior close`: median, p95, worst; plus the overnight share of 20-day return variance), and (b) a **worst-20d-window** (the most negative trailing 20-trading-day return) over the name's available as-of history. Both read only bars ≤ as-of (no-lookahead), return `None` on insufficient history, and take their windows from config. Reuse the EXISTING `indicators:atr_pct` and `indicators:downside_vol` for ATR% and downside volatility (no second computation).
- [ ] In `scoring.py` pass-3 (the iter-13 J-30 stored-factor block, ~`scoring.py:380-404`), compute the new risk components ONCE from the same as-of bars already in hand, and **reframe distance-to-invalidation as a %** derived from the EXISTING canonical `invalidation` level + price (no recompute of the level). Compute each component's **cross-sectional universe percentile** across the members scored in the SAME as-of scan pass (the existing cross-sectional-normalization pattern), and store all values + percentiles as additive fields on the stored row dict (persisted losslessly in `record_json` by `scanner.py:147`). These components enter **NO weighted score** (like the iter-13 J-30 volatility factors) — Leadership / Entry Quality / Risk stay byte-identical.
- [ ] Add config: `indicators.gap_window`, `indicators.worst_window_days: 20` (typed + validated in `IndicatorsCfg`, no inline literals; keep `max_lookback_bars` ≥ any new lookback these introduce).
- [ ] Add `config.methodology` catalog entries documenting each new component's formula + window (the single source `/methodology` reads via `app.engine.methodology:build_catalog`).
- [ ] Ensure the **served snapshots regenerate with the new fields**: because `run_scan` is idempotent + immutable (it returns an existing run WITHOUT recomputing) and `trendora.db` is built at boot from the seed, the served runs (bootstrap dates + latest) must be recomputed by the new code — clear the served snapshot runs / rebuild the DB from seed so bootstrap recomputes them. **Bounded to bootstrap + latest only** — do NOT run a full-universe 30-year backfill (the iter-24/26/27 OOM path); historical scanner rows stay honestly NA for the new fields (sanctioned by B-201).

### Frontend
- [ ] Add a **Risk-budget card** to `apps/frontend/app/stocks/[ticker]/page.tsx` (a new `Card`, placed near the existing Risk score / `ThemeAndInvalidationCard`), rendering the new server fields verbatim: ATR%, downside volatility, overnight-gap profile (median / p95 / worst), worst historical 20-day window, distance-to-invalidation %, each with its universe-percentile context label (e.g., "gap risk: p87 of universe"). Short-history components render **NA with the reason**, never a fabricated 0.
- [ ] Add the corresponding **risk-budget columns** to the `/stocks` leaderboard (`apps/frontend/app/stocks/page.tsx`), reading the SAME served fields (no client recomputation).
- [ ] Extend the `StockRow` type in `apps/frontend/lib/api.ts` with the new fields (nullable — NA is honest).

### New user-facing capability
On any stock detail page the user can now see, at a glance, the plausible downside of a name — its volatility, its overnight-gap exposure (the risk an invalidation level cannot protect against), its worst historical 20-day drawdown, and how far price is from where the thesis is wrong — each contextualized against the whole universe.

### New information displayed
ATR%, downside volatility, overnight-gap median / p95 / worst (+ overnight share of 20-day variance), worst historical 20-day window, distance-to-invalidation %, and a universe-percentile label per component. Same values appear as leaderboard columns.

### New user actions
None — descriptive read-only card. No inputs, no buttons, no advice controls.

### UI surface changes
A new Risk-budget card section on the EXISTING `/stocks/{ticker}` detail page + new columns on the EXISTING `/stocks` leaderboard. No new page, no nav change.

### Product surface delta
Trendora gains its capital-preservation half: entry-quality scoring is complemented by an honest "how much can this hurt" panel, sourced single-source from the snapshot and honestly NA where history is thin.

### Blueprint conformance
No new surfaces. The risk-budget card is an additive section on the EXISTING `/stocks/{ticker}` Stock Detail page (row-reached under the **Stocks** nav section) and additive columns on the EXISTING `/stocks` leaderboard — both already in the `blueprint.md` Information Architecture homes table. No nav-skeleton change; no `blueprint.reapproval-requested`. A J-24 feature-home row is added to the IA table (additive edit).

### Data-contract additions
ONE new value — **Per-stock risk-budget components** (ATR%, downside volatility, overnight-gap profile median/p95/worst + overnight variance share, worst historical 20-day window, distance-to-invalidation %), each with a cross-sectional universe-percentile label.
- **Computed once by:** `scoring:score_stocks` at snapshot time — new PURE `app.engine.indicators` gap-stats + worst-window functions (ATR% / downside-vol REUSE existing `indicators:atr_pct` / `indicators:downside_vol`; distance-to-% REUSES the existing canonical `invalidation` level — no second computation); universe percentiles computed cross-sectionally across members in the SAME as-of scan pass; stored as additive fields on the snapshot row (`record_json`, iter-13 J-30 precedent).
- **Served by:** additive fields on the EXISTING `GET /api/stocks/{ticker}` (card) + `GET /api/stocks` (leaderboard columns) — both re-read the SAME stored fields. **No new endpoint, no UI recompute.**
Registered in `blueprint.md` this iteration (Data Contract row + iter-40 clarification). Never introduces a second way to compute or fetch a value already in the contract (invalidation level is read from its existing canonical source).

## OUT OF SCOPE

- Feeding the new risk components into ANY weighted score — Leadership / Entry Quality / Risk stay byte-identical (B-201 ★ Do NOT touch score weights; that is a separate pre-registered decision).
- New `ScannerResult` DB columns / schema migration — store additive fields in `record_json` (both endpoints already read it); J-24 requires no sort/filter on the new fields.
- Any full-universe 30-year historical backfill of the new fields — historical scanner rows stay honestly NA (B-201 sanctions "NA for historical rows until a sanctioned backfill"); only the served snapshots (bootstrap + latest) regenerate. This avoids the iter-24/26/27 anti-goal #8 OOM path.
- Any new endpoint (additive fields on the existing stock endpoints only).
- B-203 position-risk arithmetic calculator (account size × risk fraction) — a separate BOUNDARY card needing owner amendment.
- B-202 invalidation-style evidence study — a separate card/journey.
- Any `## Evidence Claim`, proven-language, "Proven / Not yet proven" badge, or position advice ("buy / sell / trim / reduce / rebalance") on the risk components — descriptive statistics only.

## DEFINITION OF DONE

- [ ] **J-24 passes via browser-qa-agent:** `/stocks/{ticker}` for a liquid name shows the risk-budget card with ATR%, downside volatility, overnight-gap profile (median / p95 / worst), worst historical 20-day window, and distance-to-invalidation — each with a universe-percentile context label.
- [ ] A short-history name (e.g., a recent IPO like ARM) renders NA + the reason for components lacking sufficient history (browser-verified).
- [ ] `/methodology` documents each new component's formula and window (browser-verified AND `tests/test_api_methodology.py` catalog completeness green).
- [ ] The `/stocks` leaderboard shows the risk-budget columns re-reading the SAME stored fields — a spot-checked leaderboard value equals the same value on that name's detail card (single source, no UI recompute).
- [ ] **Correctness:** one spot-checked overnight-gap value (e.g., p95) byte-matches an offline recomputation from the engine for the same as-of (unit test asserting the exact value).
- [ ] The three per-stock scores (Leadership / Entry Quality / Risk) remain byte-identical (new components enter no weighted score).
- [ ] No proven-language, no badge, and no position advice anywhere on the card (anti-goals #1 / #2).
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-05, J-10, J-12, J-13, J-20 remain green.
- [ ] No anti-goal violation introduced (no lookahead — bars ≤ as-of; no whole-table ORM load / no full-universe rebuild — anti-goal #8; determinism preserved).
- [ ] Unit tests pass; new pure-function fixture tests (gap-stats, worst-window) assert exact values incl. the NA / short-history path; snapshot payload-shape tests updated (additive); no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-40-dev.md`.

## TESTING REQUIREMENTS

- **Browser (full-iter lane):** J-24 on `/stocks/{ticker}` (liquid name — full card with percentile labels), a short-history name (NA + reason), `/methodology` (new component docs), and a `/stocks` leaderboard-column ↔ detail-card single-source spot check. Regression: J-01, J-02, J-03 (evidence badges + scores byte-identical on `/stocks` and detail), J-10 (deep price chart on the touched detail page), J-05 (evidence ledger), J-12 (`/methodology` untouched claims), J-13 (`/data`), J-20 (cross-cutting preflight banner on the touched pages).
- **Unit/integration:** new `indicators` gap-stats + worst-window pure functions (exact-value fixtures + insufficient-history → `None`); `scoring.py` stored-row additive fields present with cross-sectional percentiles; the byte-match gap-value spot check; a test asserting Leadership/Entry Quality/Risk are byte-identical with the new components present; `test_api_methodology.py` catalog completeness for the new entries; snapshot payload-shape tests updated.
- **Error cases:** short-history / insufficient-bars name → NA with reason (never fabricated 0); a name with a null invalidation level → distance-to-invalidation renders NA (never a divide-by-zero / crash); the served snapshot for the default as-of carries real values after a clean DB build.

## NOTES

- **No Evidence Claim (deliberate).** J-24 carries none per goal.md + B-201 (descriptive risk statistics, not a "Proven" edge). Do NOT add a `## Evidence Claim` block — the post-decompose gate passes automatically; both ledgers stay byte-identical (7/7 FAIL); the canonical Bonferroni divisor stays **8**. Never re-submit a closed FAIL.
- **Operational risk #1 — served-snapshot regeneration.** `run_scan` is immutable (returns an existing run without recomputing) and `trendora.db` is built at boot, so browser-QA will see NA everywhere unless the served snapshots are recomputed by the new code. Regenerate the served runs (bootstrap dates + latest) on a clean DB build — bounded, fast — and verify `/api/stocks/{ticker}` carries the new fields with real values before the browser lane runs. Do NOT trigger a full-universe 30-year backfill (anti-goal #8, iter-24/26/27 OOM).
- **Interpretation logged.** "Worst-20d window in the name's history" is read as the name's FULL available as-of history (bars ≤ as-of, from the per-symbol series already in the scan's bar cache — bounded, no new DB load), not a max_lookback-windowed recent span. Recorded in `runs/goal-session-mcp-loop/state/assumptions.md` (iter-40; reversible: yes).
- **Systemic replay-lane flag (carried from iter-39, recurred iter-33/36/38).** A FULL iteration routes through `run-phase.sh`, which has no deterministic-replay lane, so iter-40 will re-create the required-still-passing replay gap. It must either run the closure one-liner replay inline OR be followed by a lean verify pass (as iter-34/37/39 were) — expect iter-41 planning to fold this in. Durable framework fix still owed to the maintainer: add the replay lane to the full path.
- **Non-blocking residual to fold into the next lean replay:** the J-23.json golden (linted iter-38, LLM-walked iter-39) has still not run through `demo_runner --mode verify` — run it through the deterministic lane on the next lean pass.
- After J-24 (iter-40) and J-25 (iter-41), all 25 Must-haves would be passing and GOAL_ACHIEVED becomes reachable.
