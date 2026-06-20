# Goal Iteration 40 — Live re-verification of the Dashboard two-pane cross-view (J-97) + at-a-glance restructure (J-98)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 40
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-97, J-98
- **Required-still-passing journeys:** J-18, J-07, J-06, J-44, J-49, J-87, J-88, J-89, J-90, J-13, J-43, J-01
- **Anti-goal reminders:**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. Chart **visualization** MAY render bars dated > D strictly as a labelled forward/after-as-of display; this display path MUST NOT feed any score, bucket, setup status, pattern flag, factor value, or ranking. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(extends Single source of truth)*
  - **Chart pane-zoom / range-sync is a view transform, not a date control.** Synchronizing the visible date range across the Dashboard's stacked chart panes changes only the **displayed window**; it MUST NOT introduce a second date state, write the global as-of, or feed any as-of-scoped computed value — the single global as-of switcher stays the only date control, and the full-history context past the as-of stays display-only behind the as-of marker. *(extends Exactly one date selector + Full-history market context never looks ahead — J-97)*
  - **No fabricated data.** On a data-provider failure (or an as-of with no causal phase history) the system MUST surface an explicit honest-empty / unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation. *(critical)*

## GOAL

On a live, hydrated Dashboard, capture rendered evidence that the two-pane synced indexes/phase-severity cross-view chart (J-97) populates its bottom pane and that the at-a-glance restructure (J-98) shows the compact regime + phase/severity summary first — flipping J-97 from `failing` to `passing` and J-98 from `partial` to `passing`.

## BACKGROUND

This is the established lean live-re-verification pass the iter-39 evaluator prescribed (the iter-30→31 / iter-33→34 / iter-36→37 pattern, a third repeat). The iter-39 FULL pass already FIXED the iter-38 J-97 stale-cache defect at the backend: a `SCHEMA_VERSION = "s1"` payload-schema token is folded into the `MarketPhaseCache` key via `_cache_version()` (`market_phase.py:797-804`), applied to both `market_phase_cached` and `retrospective_cached`, so every pre-iter-38 bare-stamp row (missing `timeline_full`) becomes a guaranteed MISS recomputed once WITH the field — every served value byte-identical, proven by 16 green cache-HIT-probing unit tests; coherence COHERENCE-PASS; review PASS. The ONLY reason J-97/J-98 did not flip to passing is that browser-QA was SKIPPED entirely (Chrome MCP CDP WebSocket timeout, no Playwright fallback, ZERO screenshots) — so there is NO live rendered proof. Per the strict standing rule (a UI journey is not marked passing without positive LIVE render evidence — iter-17/25/30/36/39), the journeys cannot flip on inference. The frontend (`phase-cross-view-chart.tsx`, `phase-cross-view-card.tsx`, `phase-band-primitive.ts`) and the backend cache fix are already in place; this iteration captures the missing live evidence and needs **no code rework** on the happy path.

## IN SCOPE

### Backend
- [ ] No backend code change is expected. The iter-39 `SCHEMA_VERSION`/`_cache_version` cache fix is already committed (`market_phase.py`). CONTINGENCY ONLY: if a live probe of `GET /api/market-phase?full=true` at the **live current as-of** (a cache HIT, NOT a fresh-compute date) still returns a payload WITHOUT a populated `timeline_full`, prune/clear the stale pre-iter-38 `MarketPhaseCache` rows lacking the field (or bump the `SCHEMA_VERSION` token) so the live HIT recomputes with `timeline_full`, then assert `?full=true` and `?full=false` (the card's bounded tail) both serve byte-identical to a fresh `compute_market_phase`. Do NOT touch any scoring/regime/scanner/snapshot path; do NOT re-trigger the J-85 `kind:rebuild` (~11h destructive — the data is correct).

### Frontend (if applicable)
- [ ] No frontend code change is expected (`phase-cross-view-chart.tsx` / `phase-cross-view-card.tsx` / `phase-band-primitive.ts` are byte-unchanged from iter-38). The `Frontend Present: yes` flag is set ONLY to force the browser-QA render-evidence step (iter-36/iter-39 lesson: a backend-only restore-a-render iter is auto-SKIPPED on a "Frontend Present: no" flag even when live evidence is the acceptance criterion).

### New user-facing capability
None new — this iteration verifies, on live rendered evidence, the capability already built in iter-38/iter-39: a two-pane synced Dashboard cross-view chart whose bottom pane overlays phase-colored bands + a 0–100 severity line + the filtered P(bear) line on the same normalized index lines, and a compact at-a-glance Dashboard summary above it.

### New information displayed
None new. The bottom pane re-formats the SAME single served market-phase series (`timeline_full`) the J-87/J-88/J-89 card already reads; the at-a-glance summary re-displays the SAME regime (from `/api/dashboard`) + phase/severity/P(bear) (from `/api/market-phase`) canonical values.

### New user actions
None new. Verify the already-built synced zoom/pan (a visible-range view transform, never a second date control) and the J-98 "More detail" expand/collapse.

### UI surface changes
None new — the Dashboard `/` layout already changed in iter-38 (at-a-glance summary first, then the two-pane cross-view chart, then the collapsed "More detail" section). This iteration captures it rendered.

### Product surface delta
No structural delta. The Dashboard's verified end state is recorded: first paint shows the compact summary + the cross-view chart; the bottom pane is populated (not empty); breadth / Top Sectors / Candidate Counts / Top Themes are reachable in the collapsed "More detail" section.

### Blueprint conformance
No new surfaces. J-97 and J-98 both live on the EXISTING **Dashboard `/`** Information-Architecture home (blueprint.md:329, IA section). No nav-skeleton change, no new page, no duplicate home — so no blueprint re-approval is required.

### Data-contract additions
None. `timeline_full` is already registered in the Data Contract (blueprint.md:391) with its single canonical computing module (`market_phase` engine `_timeline_series` / `compute_market_phase`) and single serving endpoint (`GET /api/market-phase?full=true`). The bottom pane reads that registered canonical source verbatim; no second computation or endpoint is introduced. The regime figure reads `/api/dashboard`, the phase/severity/P(bear) figures read `/api/market-phase` — both pre-registered. No edits to blueprint.md are needed.

## OUT OF SCOPE

- Any backend code rework on the happy path (the cache fix is correct and byte-identity proven; the pruning fallback fires ONLY if the live HIT still lacks `timeline_full`).
- J-99 (membership-timeline pagination/filter) and J-100 (bounded-resource backend) — they are the next two buildable Must-haves but are sequenced AFTER J-97/J-98 close green on live evidence (iter-39 recommendation). Do NOT begin them this iteration.
- Any change to a scoring/regime/scanner/snapshot/gate path, the as-of contract, or the Market-Phase card's bounded disclosure tail.
- Re-triggering the J-85 `kind:rebuild` (~11h, destructive — the snapshot data is correct).
- J-22 / J-23 / J-24 (data-walled, non-vetoing per goal.md:105-108).

## DEFINITION OF DONE

- [ ] Target journey J-97 passes via browser-qa-agent on LIVE rendered (non-skeleton) evidence: the bottom pane at the live current as-of shows phase-colored bands + a 0–100 severity line + the filtered P(bear) line + the as-of marker; the synced zoom captured as TWO byte-DISTINCT before/after frames; an early-as-of (no causal phase history) renders an honest-EMPTY bottom pane (never a fabricated severity/phase/probability).
- [ ] Target journey J-98 passes via browser-qa-agent on LIVE rendered evidence: first paint shows the compact Market Regime figure (label + 0–100 score) + the compact Market Phase & Severity figure (phase label + 0–100 severity + severity-band label + filtered P(bear)), each with its named component breakdown reachable (no bare number); the "More detail" section expands to reveal breadth + Top Sectors + Candidate Counts + Top Themes; an as-of change updates BOTH compact figures.
- [ ] Required-still-passing journeys remain green on a LIVE smoke (J-18, J-07, J-06, J-44, J-49, J-87, J-88, J-89, J-90, J-13, J-43, J-01).
- [ ] No anti-goal violation introduced (verify by diff inspection: no new date `useState` / `setAsOf` / window-keydown from the chart; no client-side severity/phase/P(bear) math; no scoring/regime/scanner/gate path touched).
- [ ] Unit tests pass; no regressions. If the contingency pruning fires, the full backend suite must flush `0 failed, EXIT 0` (nohup-async via the pump; never block the evaluator on the in-flight suite — iter-11/29/37). On the happy no-code path the iter-39 green-suite gate stands for the byte-unchanged backend.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-40-dev.md`.

## TESTING REQUIREMENTS

- **Browser (PLAN THE PLAYWRIGHT FALLBACK UP FRONT):**
  - J-97 — bottom pane populated at the live current as-of (bands + 0–100 severity + filtered P(bear) + as-of marker); the synced zoom as TWO byte-DISTINCT frames (UT-04/UT-10, skipped every iteration so far — capture them this time); an early-as-of honest-empty bottom pane.
  - J-98 — first-paint compact at-a-glance summary (Market Regime label+score; Market Phase & Severity label+0–100 severity+band+filtered P(bear)); each score's named component breakdown reachable; the "More detail" expand (UT-12); an as-of change updating BOTH compact figures (UT-18).
  - Required-still-passing live smoke: J-18 (0 native `input[type=date]`, CRITICAL), J-07 (Risk-Off → 0 Actionable, CRITICAL), J-06 (compact figures == served; pane-1 series == card series for the overlap window), J-44/J-49 (top pane unchanged + as-of marker), J-87/J-88 (card phase/severity/P(bear) unchanged), J-89/J-90 (timeline + retrospective fence + recovery-turn unchanged), J-13/J-43/J-01.
- **Unit/integration:** No new tests on the happy path. CONTINGENCY ONLY: if pruning fires, add/keep a test that probes an ALREADY-POPULATED old-schema cache row (a real cache HIT, NOT a fresh compute) and asserts the served `timeline_full` is byte-identical to a fresh `compute_market_phase`, AND that `?full=false` (the card) stays byte-identical (protecting J-87/J-88/J-89).
- **Error cases:** An as-of with no causal phase history MUST yield an honest-empty bottom pane (empty `timeline_full` list), never a fabricated severity/phase/probability. An invalid `?asof` URL date still degrades to latest (J-43, unchanged).

## NOTES

- **CRITICAL ENV/EVIDENCE GUIDANCE (lesson iter-39, iter-36, iter-30, iter-17):** the Chrome MCP CDP WebSocket timeout has now emptied the evidence dir TWICE (iter-38 AND iter-39); only iter-34 and iter-37 escaped it, via the Playwright fallback. The browser-qa step MUST plan the Playwright fallback UP FRONT, not after Chrome MCP times out, or the render evidence is lost again and J-97/J-98 cannot flip despite a correct fix. Bring up backend `:8835` (WAIT for `GET /api/health` "ready" — the warm-up precomputes the phase cache; the first `?full=true` per previously-cached as-of pays one bounded recompute by design), frontend `:3835`, Chrome `:9222`.
- **Evidence hygiene (lessons iter-7/10/15/18/33):** `md5sum` the evidence dir FIRST and REJECT any blank/skeleton/byte-identical frame. A differential leg (the synced zoom; an as-of change updating both figures) REQUIRES two byte-DISTINCT frames. Scroll any below-the-fold panel into the viewport and VIEW the pixels; resolve controls by `aria-label`, not visible `text()`.
- **Cache-correctness probe (lesson iter-38):** confirm `GET /api/market-phase?full=true` serves a populated `timeline_full` at the LIVE CURRENT as-of (a cache HIT under the live `dataset_version|s1` stamp), NOT a fresh-compute date — the iter-38 "TC-01 1056 points" was a fresh compute at a different as-of that MASKED the stale-cache bug.
- **Single-source reconciliation (J-06):** the bottom pane's phase/severity/P(bear) series MUST equal the Market-Phase card's values for the overlapping window, and the compact J-98 figures MUST equal the served `/api/dashboard` + `/api/market-phase` values — no client-side recompute.
- **/api/data hygiene (MEMORY / iter-35/37):** the /data page hydrates on a SINGLE patient load; never fire concurrent `/api/data` probes (pool exhaustion). This iteration's surfaces are Dashboard `/` + `/api/market-phase`, not `/api/data`, so /data load is not on the critical path here — but keep the single-load discipline if any required-still-passing smoke touches /data.
- **Suite gate:** on the happy no-code path, the iter-39 green-suite gate stands for the byte-unchanged backend; this is NOT a GOAL_ACHIEVED candidate (J-99/J-100 remain unbuilt buildable Must-haves — iter-22 lesson). Only after J-97..J-100 all pass with a flushed-GREEN full suite + COHERENCE-PASS is the next evaluation a GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing per goal.md:105-108).
- **Next steps after this iteration:** J-99 (lean, frontend-only view transform — pagination/filter over the served `membership_timeline.points`), then J-100 (full, backend perf/stability hardening + a concurrency load test).
- This spec is a planning document. No code is written by the decomposer. No blueprint edits were required (J-97/J-98 and `timeline_full` are already registered; no new value or page).
