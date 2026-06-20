# Goal Iteration 39 — Fix J-97 stale-cache schema-versioning + live-verify J-97/J-98

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 39
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-97, J-98
- **Required-still-passing journeys:** J-18, J-07, J-06, J-44, J-49, J-87, J-88, J-13, J-43, J-01, J-89, J-90
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. Chart visualization MAY render bars dated > D strictly as a labelled forward/after-as-of display; this display path MUST NOT feed any score, bucket, setup status, pattern flag, factor value, or ranking. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation. *(critical)*
  - **Chart pane-zoom / range-sync is a view transform, not a date control.** Synchronizing the visible date range across the Dashboard's stacked chart panes changes only the displayed window; it MUST NOT introduce a second date state, write the global as-of, or feed any as-of-scoped computed value — the single global as-of switcher stays the only date control, and the full-history context past the as-of stays display-only behind the as-of marker. *(extends Exactly one date selector + Full-history market context never looks ahead — J-97)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.

## GOAL

The Dashboard's two-pane market cross-view renders a fully-populated bottom pane (phase-colored bands + 0–100 severity line + filtered P(bear) line + as-of marker) at the live current as-of, and the at-a-glance restructure renders and expands correctly — both proven on live browser evidence.

## BACKGROUND

iter-38 built J-97 (the `?full=true` market-phase serialization + the two-pane synced cross-view chart) and J-98 (the Dashboard at-a-glance restructure) with coherence COHERENCE-PASS and review PASS, but the evaluator independently confirmed J-97 FAILS live: `GET /api/market-phase?full=true` at the current as-of (`2026-06-16`) returns **no `timeline_full` key**, so the bottom pane is empty. Root cause (eval + source, `market_phase.py:788-840`): `market_phase_cached` keys the `MarketPhaseCache` row on `(asof_key, dataset_version)` only, and `_dataset_version` tracks DATA changes (backfill/removal), NOT the payload SCHEMA — so every pre-iter-38 cache row (including the live current as-of, written under the unchanged stamp `r1370-f3078889`) is served verbatim without the field that iter-38 added, and `market_phase_full_cached` (a pass-through) returns it field-less. J-98's restructure was held PARTIAL only because it embeds the broken J-97 chart AND the iter-38 evidence dir was empty (Chrome MCP timed out — zero screenshots). This is a single, tractable, cross-cutting cache-correctness defect plus a missing live-evidence pass — `full` depth, matching the prior depth and the evaluator's explicit recommendation.

**Lesson applied (iter-38, append-only lessons):** *"An additive field added to a CACHED payload is INVISIBLE at every already-cached key until the cache is invalidated — and the existing cache key may not invalidate on a SCHEMA change … When adding any additive field to a cached payload, bump a payload-SCHEMA-version component of the cache key (not just the data-version stamp) or prune rows lacking the new field, and unit-test the additive field against an already-populated cache row, not a fresh compute."* The unit test for this fix MUST probe an already-populated cache row written under the OLD schema (or the live current-as-of cache HIT), NOT a fresh-compute date — iter-38's QA TC-01 "1056 points" passed precisely because it hit a fresh-compute cache MISS at a different as-of (`2025-12-31`), which masked the bug.

**Lesson applied (iter-36):** a backend read-path fix whose purpose is to restore a PAGE RENDER is AUTO-SKIPPED by browser-QA when the metadata reads "Frontend Present: no" — so this spec sets `Frontend Present: yes` to force the live browser-QA step in the SAME iteration and capture the evidence J-97/J-98 need to flip to passing.

## IN SCOPE

### Backend
- [ ] Fix the `MarketPhaseCache` schema-versioning defect so `GET /api/market-phase?full=true` serves `timeline_full` at the live current as-of (a cache HIT), not only at fresh-compute dates. Preferred (survivor-proof for future additive fields): incorporate a **payload-schema-version token** into the cache key. Because `market_phase_cache` is a STANDALONE `create_all`-managed table that ALSO exists in the live persistent DB, do this WITHOUT a raw new column unless that column is registered in `db.py` `_ADDITIVE_COLUMNS` AND the `test_db.py` expected-tables/column guards — the lower-risk route is to fold a `SCHEMA_VERSION` constant into the existing `dataset_version` string composite (e.g. `f"{version}|s{SCHEMA_VERSION}"`) so every pre-iter-38 row keyed to the bare stamp is a guaranteed MISS and is recomputed once, OR to one-time prune rows whose `payload_json` lacks `timeline_full`. Choose the route that keeps `?full=false` (card) and the J-89 retrospective payload byte-identical.
- [ ] Apply the SAME schema-version key fix to the FENCED retrospective cache path (`market_phase.py:1103-1146`) — it shares the SAME `MarketPhaseCache` table + the SAME `_dataset_version` stamp, so it carries the identical schema-staleness risk for any additive field it serves; assert its served payload stays byte-identical post-fix (the smoothed/true-bear fence is unchanged).
- [ ] Assert via a committed unit test (probing an ALREADY-POPULATED old-schema cache row, not a fresh compute): `?full=true` at a cached as-of now serves a `timeline_full` that is byte-identical to `compute_market_phase(...)["timeline_full"]` (strictly causal per point, no-lookahead intact), and `?full=false` (card) stays byte-identical to its pre-fix payload. The `timeline_full` series is read VERBATIM from the existing `_timeline_series` — no new derivation, no second computation, no client-side severity/phase/P(bear) math.

### Frontend
- [ ] No new component or value is expected — the J-97 chart (`phase-cross-view-chart.tsx`, `phase-cross-view-card.tsx`, `phase-band-primitive.ts`, `lib/phase.ts`) and the J-98 restructure (`app/page.tsx`) already exist from iter-38. Only touch the frontend if the live verification exposes a genuine render defect downstream of the now-correct payload (e.g. a field path the chart reads). If the payload fix alone makes the bottom pane render, the frontend diff is empty — keep it that way (surgical).

### New user-facing capability
The Dashboard cross-view bottom pane is populated for any as-of with causal phase history: a reader sees the same index path under both the regime lens (top pane) and the phase/severity lens (bottom pane), with synchronized zoom across both panes.

### New information displayed
The full-history phase-colored bands + 0–100 severity line + filtered P(bear) line on the bottom pane at the live current as-of (previously empty). No NEW canonical value — the series is the already-served `timeline_full`.

### New user actions
None new (synchronized zoom/pan on the shared time scale already exists from iter-38; the J-98 More-detail expand/collapse already exists).

### UI surface changes
Dashboard `/` — the two-pane cross-view chart's bottom pane goes from empty to populated; the J-98 at-a-glance summary + collapsed More-detail section render and expand. No new page, no new route, no nav change.

### Product surface delta
The Dashboard's headline cross-view becomes actually usable (the bottom pane was rendering empty), completing the J-97/J-98 at-a-glance experience.

### Blueprint conformance
No new surfaces and no new values. J-97's `timeline_full` is already registered in the Data Contract (`blueprint.md:391`) with its single canonical computing module (`market_phase` engine `_timeline_series` / `compute_market_phase` `timeline_full`, read verbatim) and single serving endpoint (`GET /api/market-phase?full=true`, served from the SAME `dataset_version` cache). J-97/J-98 land on the existing Dashboard `/` IA home (`blueprint.md:329`). This iteration is a correctness fix to the already-registered cache, not a new registration — **no blueprint edit required, no nav-skeleton change, no reapproval request.**

### Data-contract additions
None. The fix serves the already-registered `timeline_full` from its single canonical module + endpoint. Do NOT introduce a second computation, a second endpoint, or a second cache for it — read the registered canonical source.

## OUT OF SCOPE

- Any change to `compute_market_phase`'s phase/severity/P(bear)/episode/recovery math — the engine output is correct; only the cache key/serialization is defective.
- Any snapshot rebuild, scanner/scoring/regime change, or new stored column (the card `?full=false` payload and all canonical values stay byte-identical).
- J-99 (membership-timeline pagination/filter) and J-100 (bounded-resource backend) — they follow in later iterations only after J-97/J-98 close green.
- The descoped `/api/data` coverage warm-cost optimization (a separate, non-blocking concern carried since iter-37) — not touched here.
- The non-blocking coherence WARN from iter-38 (`phaseBadgeVariant`/`phaseVariant` presentational badge-variant duplication) — optional cheap fold-in only if trivially touched, never required.

## DEFINITION OF DONE

- [ ] Target journeys J-97, J-98 pass via browser-qa-agent on LIVE rendered evidence (not API/source-only).
- [ ] `GET /api/market-phase?full=true` at the live current as-of returns `timeline_full` (cache HIT), byte-identical to a fresh `compute_market_phase(...)["timeline_full"]`.
- [ ] `GET /api/market-phase?full=false` (card) and the J-89 retrospective payload stay byte-identical to their pre-fix output (J-87/J-88/J-89 unchanged).
- [ ] Required-still-passing journeys remain green (CRITICAL: J-18 exactly-one-date-selector, J-07 Risk-Off→0 Actionable).
- [ ] No anti-goal violation introduced.
- [ ] Unit tests pass; the FULL backend pytest suite flushes `0 failed, EXIT 0` (handed to the pump nohup-async; gate on the FLUSHED line, never the in-flight stream).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39-dev.md`.

## TESTING REQUIREMENTS

- **Browser (LIVE, target journeys):**
  - **J-97** — bottom pane renders phase-colored bands + the 0–100 severity line + the filtered P(bear) line over the same normalized index lines + the as-of marker, at the LIVE current as-of (the cache-HIT case that failed in iter-38). Capture the synchronized zoom as **two byte-DISTINCT before/after frames** (UT-10 was skipped in iter-38). Capture an early-as-of (no causal phase history) honest-empty bottom pane — never a fabricated severity/phase/probability.
  - **J-98** — first-paint compact at-a-glance summary (Market Regime label+score; Market Phase & Severity label+0–100 severity+band+filtered P(bear)), each with its named component breakdown reachable (no bare number); the More-detail expand (UT-12); an as-of change updating BOTH compact figures (UT-18).
- **Browser (required-still-passing live smoke):** J-18 (0 native `input[type=date]`; the synced zoom adds no date state — CRITICAL), J-07 (Risk-Off → 0 Actionable — CRITICAL), J-06 (compact figures == served values; pane-1 series == the card series for the overlap window — single source), J-44/J-49 (top pane = unchanged index lines + stored-regime bands + as-of marker), J-87/J-88 (card phase/severity/P(bear) unchanged), J-13/J-43 (as-of switch drives both panes), J-89/J-90 (timeline + retrospective fence + recovery-turn unchanged).
- **Unit/integration:** the cache-correctness test MUST probe an ALREADY-POPULATED old-schema cache row (or the live current-as-of cache HIT), asserting `?full=true` now carries `timeline_full` byte-identical to `compute_market_phase`'s, and `?full=false` + retrospective payloads byte-identical pre/post fix. If the fix adds any new model column, it MUST be registered in `db.py` `_ADDITIVE_COLUMNS` and the `test_db.py` expected-tables/column guards in the SAME iteration (iter-12/iter-20 lessons — these guards surface only in the full suite).
- **Error cases:** an as-of with no causal phase history serves an honest-empty `timeline_full` (empty list), not a fabricated series; an invalid `?full` value is handled per the existing endpoint contract.

## NOTES

- **Evidence hygiene (iter-18/33/36/38 lessons):** the iter-38 evidence dir was EMPTY (Chrome MCP CDP timeout). Bring up backend `:8835` (WAIT for `GET /api/health` "ready"), frontend `:3835`, Chrome `:9222`; fall back to Playwright if Chrome MCP is unreachable (iter-34 precedent). `md5sum` the evidence dir FIRST and REJECT any blank/skeleton/byte-identical frame as evidence — a differential leg (synced zoom) REQUIRES two byte-DISTINCT frames; a render leg requires the rendered pixels, not a loading skeleton. The bottom pane sits below the fold — scroll it into the viewport and VIEW the pixels.
- **Cache-correctness check must hit a HIT, not a MISS (iter-38 lesson):** verify `timeline_full` against the LIVE current as-of (a cache HIT under the live `dataset_version`), NOT a fresh-compute date — a fresh-compute date masks the staleness bug exactly as iter-38's QA did.
- **Suite gate (iter-11/29/37 lessons):** never block the goal-evaluator on the in-flight full suite; run it `nohup`-async via the pump and gate GOAL_ACHIEVED candidacy on the flushed `0 failed, EXIT 0` line. Re-run any single `test_warmup.py` / `test_data_manager_jobs_pipeline.py` F in isolation before attributing it to this iteration (known contention/slow-boot flakes, not regressions).
- **CRITICAL invariants by construction:** the synced-zoom is a visible-range view transform, never a second date control — confirm grep shows no new date `useState`/`setAsOf`/window-keydown in the chart/card/page files and live `/` has 0 native `input[type=date]` (J-18). The additive backend diff must touch no scoring/regime/scanner/gate path (J-07/J-44/J-49/J-87/J-88).
- **Not a GOAL_ACHIEVED candidate yet:** J-99 and J-100 remain unbuilt buildable Must-haves (iter-22 lesson — queued-but-unbuilt journeys are `unknown` Must-haves with no positive evidence and block done). After J-97/J-98 close green on live evidence with COHERENCE-PASS and a GREEN suite, build J-99 (lean) then J-100 (full); only then is the next evaluation a GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing per goal.md:105-108).
