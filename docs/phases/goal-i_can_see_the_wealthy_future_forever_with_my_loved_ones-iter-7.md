# Goal Iteration 7 — Research samples drill-down (J-51) + sample-row → dated stock detail (J-52)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 7
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-51, J-52
- **Required-still-passing journeys:** J-25, J-26, J-29, J-32, J-47, J-50, J-54
- **Anti-goal reminders:**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request.
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Honest limitations surfaced.** Breadth and new-high/new-low metrics computed from the seed universe MUST be labelled "universe-relative" (not full-market internals), and walk-forward evidence MUST be labelled as carrying survivorship bias (current-membership universe) so results are never overstated.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*

## GOAL

Every research sample count (`N=…`) on `/research` becomes a link to a new read-only `/research/samples` drill-down whose observation total equals the published N, and each sample row's ticker opens the dated stock detail (`/stocks/[ticker]?asof=<row snapshot date>`) in a new tab.

## BACKGROUND

J-51 and J-52 are two of the three remaining failing journeys (the other, J-53, is earmarked for an iter-8 full pass per the iter-6 evaluator recommendation). The iter-6 evaluator explicitly recommended this exact lean scope: the samples endpoint is a SELECT-only exposure of observation sets the lab aggregates ALREADY assemble — `research:_factor_observations`, `_combination_observations`, `_event_study_members` (apps/backend/app/engine/research.py, lines ~168/357/674) — so structural risk is low despite touching both backend and frontend (the same shape as the lean iters 5–6). The blueprint pre-registers (human-approved) both the `/research/samples` IA home (link-reached under Research) and the Data Contract row served by `GET /api/research/samples`; tags flipped to "[TARGET — iter-7 in flight]" this iteration. **Count coherence is the contract: the drill-down total MUST equal the published N chip that was clicked — same membership filter, same observation set, never a second membership rule.**

Lessons that directly apply (see NOTES for the full list): the iter-5 nested-button defect was fixed in iter-6 *specifically to clear the way for this iteration's samples-table headers* — any clickable affordance in a header must be a SIBLING of `TermInfo`/`InfoTooltip`, never nested; the frontend gate is `tsc --noEmit` (ESLint is not installed); a backend touch means the full pytest suite (~35–46 min) is the gate — run it to completion in the dev-turn foreground or hand it to the pump, never two concurrently.

## IN SCOPE

### Backend
- [ ] New read-only endpoint `GET /api/research/samples` in `apps/backend/app/api/research.py`, parameterized to fully reproduce one published cohort: analysis kind (factor-lab | factor-combination | event-study), factor(s)/subject, horizon, decile/cohort identifier, optional regime, optional sector, and the all-history vs as-of scope (J-32 `as_of` semantics — the same scoping the aggregates use, never a second date state).
- [ ] The endpoint assembles its rows by calling the SAME existing observation builders the aggregates are computed from — `research:_factor_observations` / `_combination_observations` / `_event_study_members` — and, for a per-decile cohort, reuses the SAME `_deciles` ordering/quantile assignment (and the same per-regime subset logic) the aggregate used. SELECT-only: it recomputes NO factor value, NO return, NO regime, NO membership rule.
- [ ] Response: one row per observation — ticker, snapshot (as-of) date, the qualifying stored value(s) (the factor value; for a combination cohort each referenced factor's stored value; for an event study the matched setup/pattern), and the stored realized forward return at the stated horizon — plus a `total` count and an echo of the resolved cohort parameters. Serve the complete observation list (no pagination — pool sizes are bounded by the stored seed; see OUT OF SCOPE).
- [ ] Count-coherence unit tests: for each analysis kind and slice family (factor n_total / per-decile n / rank-IC n / by-regime n; combination baseline / single-condition / composite / strict-overlap n; event-study per-horizon / by-regime / by-sector / pooled n_total), assert the samples endpoint total EQUALS the n the corresponding aggregate endpoint publishes under identical params — including the `as_of`-scoped mode and the n=0 strict-overlap case (empty list + total 0, never a fabricated row).
- [ ] Value-identity unit test: row values equal the stored per-observation inputs (same `ForwardReturn` / stored factor / `ScannerResult` fields the aggregate consumed).
- [ ] Invalid cohort params (unknown kind/factor/subject/horizon/decile out of range) → explicit 4xx error, never a silent empty 200 (an empty 200 is reserved for a VALID n=0 cohort).

### Frontend
- [ ] `/research` (`apps/frontend/app/research/page.tsx`): every published sample-size figure becomes a link to `/research/samples?…` carrying the full cohort params — Factor Lab (`n_total`, per-decile n, rank-IC n, by-regime n), Combination Lab (baseline / single-condition / composite / strict-overlap cohort n), Event Study (per-horizon n, by-regime n, by-sector n, pooled `n_total`). Chips reached while in as-of mode carry the as-of scope.
- [ ] New page `apps/frontend/app/research/samples/page.tsx` — deep-linkable and reload-safe (params fully reproduce the cohort): a cohort-description header, the survivorship-bias label, and a samples table (ticker, snapshot date, qualifying stored value(s), realized forward return at the stated horizon) whose displayed total equals the published N. n=0 renders an explicit honest empty state. Dates render via the shared `formatIsoDate` (J-42).
- [ ] Table column headers read the SAME J-47 glossary catalog via `TermInfo` — and any clickable header affordance is a SIBLING of the info trigger, never nested (iter-5 lesson).
- [ ] J-52: each row's ticker links to `/stocks/[ticker]?asof=<that row's snapshot date>` with `target="_blank"` + `rel="noopener"` — the asof param is the ROW's snapshot date (not the page's global as-of); the new tab restores that date through the one global control per J-43. All other links on the page stay same-window and keep the standard J-50 `asofHref` mechanics.
- [ ] `tsc --noEmit` clean; no Next dev-overlay error badge.

### New user-facing capability
A skeptical user can audit any research sample count: click any `N=` figure on `/research` and see the exact stored observations behind it — and jump from any observation to that date's full stock-detail snapshot in a new tab.

### New information displayed
Per-observation evidence rows (ticker, snapshot date, qualifying stored factor/indicator value(s) or matched setup/pattern, realized forward return at the stated horizon), the cohort definition that produced them, and the cohort total (== the published N).

### New user actions
Click any `N=` chip on `/research` (all three labs) → samples drill-down; click a sample row's ticker → dated stock detail in a new tab.

### UI surface changes
`/research`: N= figures become links (no other change). New link-reached page `/research/samples` under the Research home.

### Product surface delta
The evidence chain closes end-to-end: aggregate → exact member observations → the dated snapshot each observation came from. No published number is unauditable anymore.

### Blueprint conformance
`/research/samples` lives under the existing **Research** home as already registered in `blueprint.md` (link-reached from the `N=` chips, not a top-nav tab). No nav-skeleton change; no reapproval needed.

### Data-contract additions
None new — the "Research samples drill-down" row is ALREADY registered in `blueprint.md` (human-approved this resume): computed read-only by `research:_factor_observations` / `_combination_observations` / `_event_study_members`, served by `GET /api/research/samples`. Tags flipped to "[TARGET — iter-7 in flight]". Do NOT introduce a second membership rule, a second observation builder, or any client-side recomputation of a factor/return/regime — the coherence-auditor hard-fails on exactly that (invariant 13).

## OUT OF SCOPE

- J-53 (parallel multi-date backfill + per-stage timings) — iter-8, full depth, per the evaluator plan.
- The one-shot J-22/J-23/J-24 + DIA data fetch — bundled with iter-8.
- Pagination/virtualization of the samples table — serve and render the complete list; add virtualization only if a real cohort demonstrably breaks rendering, and then page-size MUST come from config (no magic numbers) with every inline test config dict updated.
- Any new config key (none is expected for a SELECT-only exposure). If one proves genuinely necessary, it must live in `config.yaml` AND be added to every inline test config dict (grep the new section key across apps/backend/tests — the count grows over time, now five files).
- Any change to the aggregate computations (`compute_factor_lab` / `compute_factor_combination` / `compute_event_study`) beyond, at most, extracting a shared read-only helper so the samples endpoint and the aggregate provably use one membership/slicing path.
- New CSV/export, sorting, or filtering controls on the samples table.

## DEFINITION OF DONE

- [ ] J-51 and J-52 pass via browser-qa-agent (acceptance criteria as written in docs/goal.md, including count coherence, n=0 honest empty state, survivorship label, glossary headers, as-of mode, and the row-date `?asof` new-tab behavior)
- [ ] Required-still-passing journeys remain green: J-25, J-26, J-29 (the N= aggregate sources), J-32 (as-of mode), J-47 (tooltips), J-50, J-54 (href/new-tab mechanics)
- [ ] No anti-goal violation introduced (especially: no recompute in the read path, no second membership rule, no second date state)
- [ ] Count-coherence + value-identity unit tests pass; FULL backend pytest suite green (run to completion — foreground in the dev turn or handed to the pump; never two concurrently); `tsc --noEmit` clean
- [ ] Blueprint Data Contract row's count-coherence promise holds: drill-down total == published N for every linked chip kind
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7-dev.md`

## TESTING REQUIREMENTS

- Browser (J-51): on `/research`, chips in all three labs render as links; click a Factor Lab decile `N` → `/research/samples` opens parameterized to that cohort; displayed total equals the clicked chip's N (assert the exact number); reload the samples URL → same cohort (deep-link-safe); click an `N=0` cohort (strict-overlap) → explicit empty state, no fabricated row; survivorship-bias label visible; column headers carry TermInfo tooltips reading the glossary; with the Research as-of mode active, the chip link carries the scope and the samples total matches the as-of-scoped n; no dev-overlay error badge anywhere.
- Browser (J-52): click a samples-row ticker → NEW tab at `/stocks/[ticker]?asof=<row snapshot date>` showing the historical indicator and that date's stored scores/buckets/setup (J-06/J-43); the originating samples tab's params/scroll untouched. Spot-check one row's displayed factor value + forward return against the stock-detail/backtest stored values.
- Browser (regression): `/research` aggregates themselves unchanged (J-25/J-26/J-29 figures identical pre/post — chips are a presentation change); J-50 hrefs and J-54 leaderboard new-tab behavior unchanged. Opportunistic: re-exercise the J-44 toggle off→reload→still-off cycle (left partially verified in iter-6 due to a mid-session backend death).
- Unit/integration: count-coherence for every chip kind incl. per-regime and per-decile slices and the as_of mode; value-identity vs stored rows; n=0 honest empty; decile assignment reproduces `_deciles` exactly (same ordering, same quantile edges).
- Error cases: unknown kind/factor/subject, out-of-range decile, bad horizon → explicit 4xx (not empty 200); invalid `asof` on the J-52 deep link degrades safely to latest per existing J-43 behavior (no new code needed — verify only if cheap).

## NOTES

- **Depth rationale:** lean, per the iter-6 evaluator's explicit recommendation and the iter-5/iter-6 precedent (backend-touching lean iterations with the full pytest suite as the gate). The endpoint adds no schema, no job, no engine math — a read-only exposure.
- **Lessons applied (verbatim from lessons.md / project memory):**
  - iter-5/iter-6: samples-table headers use TermInfo/InfoTooltip — keep any clickable header affordance a SIBLING of the info trigger, never nested; QA must check the Next dev-overlay error badge.
  - iter-1: ESLint is NOT installed in apps/frontend — `tsc --noEmit` is the frontend gate, never `npm run lint`.
  - iter-2 + memory: full backend pytest is ~35–46 min (691 tests) — run to completion in the dev-turn foreground OR hand to the pump; never two concurrently; a subagent cannot finish it (10-min Bash cap).
  - iter-3/iter-6: md5-check QA PNGs against blank/duplicate degradation; capture fragile legs EARLY before any mid-session backend death; an evidence filename can mislead — verify content.
  - Memory: Chrome MCP `select` doesn't fire React onChange on this frontend — drive controlled selects via native setter + bubbled change event, then assert live DOM (relevant for switching factor/horizon/regime on `/research` during QA).
  - Memory: use the running backend on :8835; never self-restart it mid-QA; kill stray dev servers by port only.
- **Count-coherence is the veto line:** the coherence-auditor's invariant 13 hard-fails if the drill-down total can diverge from the published N (a second membership rule) or if any row value is recomputed rather than read. Prefer extracting/reusing the exact aggregate code path over re-deriving "equivalent" filters.
- **J-32 scoping note:** the samples page's as-of restriction derives from the single global as-of state (the `?asof` serialization) plus a scope/mode param mirroring the Research page's mode — it is a mode, never a second date picker (J-18 holds).
- Iter-8 plan (for continuity, not this iteration): full depth — J-53 parallel multi-date backfill + per-stage timings, bundled with the one-shot best-effort J-22/J-23/J-24 + DIA fetch.
