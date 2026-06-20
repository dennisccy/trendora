# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39 Execution Plan

Surgical cache-correctness fix + the live browser-evidence pass that iter-38 missed.
J-97 (two-pane synced cross-view) and J-98 (Dashboard at-a-glance restructure) were
already BUILT in iter-38 (coherence PASS, review PASS) but J-97 FAILS live: the
bottom pane is empty because `GET /api/market-phase?full=true` at the live current
as-of (a cache HIT) serves a payload with NO `timeline_full` key. This iteration
fixes that and proves J-97/J-98 on live rendered pixels.

## What to Build
- Backend cache-key fix: incorporate a payload-SCHEMA-version token into the
  `MarketPhaseCache` key so every pre-iter-38 row (keyed to the bare `dataset_version`
  stamp `r1370-f3078889`, written WITHOUT `timeline_full`) becomes a guaranteed MISS
  and is recomputed once WITH the additive `timeline_full` field. Preferred route
  (per spec): fold a module-level `SCHEMA_VERSION` constant into the existing
  `dataset_version` string composite at the cache call sites
  (e.g. `f"{version}|s{SCHEMA_VERSION}"`) — NO new DB column (avoids the `db.py`
  `_ADDITIVE_COLUMNS` + `test_db.py` guard registration risk on the live persistent DB).
- Apply the SAME schema-version key fix to the FENCED retrospective cache path
  (`retrospective_cached`, market_phase.py ~1103-1146) — it shares the SAME
  `MarketPhaseCache` table + SAME `_dataset_version` stamp and carries the identical
  schema-staleness risk. Its served payload must stay byte-identical (smoothed/true-bear
  fence unchanged).
- Committed unit test that probes an ALREADY-POPULATED old-schema cache row (or the
  live current-as-of cache HIT), NOT a fresh-compute date: assert `?full=true` now
  serves `timeline_full` byte-identical to `compute_market_phase(...)["timeline_full"]`,
  and `?full=false` (card) + the J-89 retrospective payload stay byte-identical to
  their pre-fix output. (iter-38's QA passed only because it hit a fresh-compute MISS
  at `2025-12-31`, masking the bug — the new test must hit a HIT, not a MISS.)
- Live browser verification of J-97 + J-98 with real captured evidence (the iter-38
  evidence dir was EMPTY — Chrome MCP CDP timeout). NO frontend code change expected;
  the J-97 chart and J-98 restructure already exist. Touch frontend ONLY if live
  verify exposes a genuine render defect downstream of the now-correct payload.

## Agents Required
- developer: yes -- backend-only cache-key fix (SCHEMA_VERSION token folded into both
  `market_phase_cached` and `retrospective_cached` keys) + the cache-HIT unit test.
  Frontend diff should be EMPTY unless live verify exposes a real field-path defect.
- backend-data: yes -- the entire functional change is the backend cache-correctness fix.
- frontend-ux: no -- J-97 chart + J-98 restructure already shipped iter-38; keep the
  frontend diff surgical (ideally empty).

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/engine/market_phase.py` -- add a module-level `SCHEMA_VERSION`
  constant; fold it into the cache key string in BOTH `market_phase_cached` (~788-835)
  and `retrospective_cached` (~1103-1146). Payloads unchanged — only the cache KEY string
  changes so stale old-schema rows MISS and recompute once.
- `apps/backend/tests/test_market_phase.py` -- new cache-HIT test (probe an
  already-populated OLD-schema row / live current-as-of HIT): `?full=true` now carries
  `timeline_full` byte-identical to engine; `?full=false` + retrospective byte-identical
  pre/post fix. Strictly causal per point (no-lookahead intact).
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39-dev.md`
  -- dev handoff (required by Definition of Done).
- (Frontend: NO change expected. Only if live verify exposes a real defect would
  `apps/frontend/components/phase-cross-view-chart.tsx` / `phase-cross-view-card.tsx`
  be touched — keep surgical.)

## UI Evolution
- New user-facing capability: the Dashboard `/` cross-view bottom pane goes from EMPTY
  to POPULATED at the live current as-of — a reader sees the same index path under the
  regime lens (top pane) AND the phase/severity lens (bottom pane) with synchronized
  zoom across both panes.
- New information displayed: full-history phase-colored bands + 0–100 severity line +
  filtered P(bear) line on the bottom pane at the live current as-of (previously empty).
  No NEW canonical value — the series is the already-registered, already-served
  `timeline_full`.
- New user actions: none new (synced zoom/pan and the J-98 More-detail expand/collapse
  already exist from iter-38).
- UI surface changes: Dashboard `/` only — bottom cross-view pane empty→populated; the
  J-98 at-a-glance compact summary + collapsed More-detail section render and expand.
- Navigation changes: none. No new page, no new route, Dashboard stays the single home.

## Visual Requirements
- Component patterns: existing `phase-cross-view-card.tsx` host card + `phase-cross-view-chart.tsx`
  two-pane `lightweight-charts` chart; J-98 compact at-a-glance figures with `<details>`
  component-breakdown disclosures (no bare numbers). No new components.
- Layout: Dashboard at-a-glance — compact Market Regime figure + compact Market Phase &
  Severity figure → Major-indexes card → J-97 two-pane cross-view chart → collapsed
  "More detail" section (breadth, Candidate Counts, Top Sectors, Top Themes, full
  MarketPhaseCard). Unchanged from iter-38 layout.
- Key visual effects: the bottom pane's config-colored phase bands (token-driven
  `lib/phase.ts` mapping), 0–100 severity line, filtered P(bear) line, and the as-of
  marker primitive — all on the SAME shared time scale as pane 0.
- States to handle: loading (skeleton, REJECTED as evidence), honest-empty (an early
  as-of with no causal phase history → empty bottom pane, NEVER a fabricated
  severity/phase/probability), error. The bottom pane sits below the fold — must be
  scrolled into the viewport for capture.

## Risks/Unknowns
- **Cache-key route choice:** spec's preferred route is folding `SCHEMA_VERSION` into the
  `dataset_version` string composite (NO new column) — chosen here to avoid the live
  persistent-DB column-registration risk (`db.py` `_ADDITIVE_COLUMNS` + `test_db.py`
  guards, iter-12/iter-20 lessons). If dev instead adds a column, it MUST be registered
  in both in the SAME iteration.
- **Byte-identity invariant:** `?full=false` (card) and the J-89 retrospective payload
  MUST stay byte-identical pre/post fix. Only the cache KEY string changes; the persisted
  payload and the `market_phase_default_payload` strip behavior are untouched. The test
  must assert this directly.
- **Evidence hygiene (iter-18/33/36/38 lessons):** iter-38 evidence dir was EMPTY (Chrome
  MCP CDP timeout). Bring up backend `:8835` (WAIT for `/api/health` "ready"), frontend
  `:3835`, Chrome `:9222`; fall back to Playwright if Chrome MCP unreachable (iter-34
  precedent). `md5sum` evidence FIRST; REJECT any blank/skeleton/byte-identical frame.
  The synced-zoom leg REQUIRES two byte-DISTINCT before/after frames (UT-10 was skipped
  iter-38). Scroll the below-the-fold bottom pane into the viewport before capture.
- **Cache verify must hit a HIT (iter-38 lesson):** verify `timeline_full` at the LIVE
  current as-of (a cache HIT under the live `dataset_version`), NOT a fresh-compute date
  — a fresh-compute date masks the staleness bug exactly as iter-38's QA did.
- **Perf / `/api/data` hazard (MEMORY):** `/api/data` is ~10s warm and a known
  pool-exhaustion risk — NEVER fire concurrent `/api/data` probes during live QA. The
  market-phase fix does NOT touch `/api/data`. A one-time recompute on first `?full=true`
  HIT-miss after the fix is expected and bounded (single market-phase compute, not a scan).
- **Suite gate (iter-11/29/37 lessons):** run the FULL backend pytest suite (~34 min)
  `nohup`-async via the pump; gate GOAL_ACHIEVED candidacy on the FLUSHED `0 failed, EXIT 0`
  line, NEVER block the goal-evaluator on the in-flight stream. Re-run any
  `test_warmup.py` / `test_data_manager_jobs_pipeline.py` F in isolation before
  attributing it (known slow-boot/contention flakes, not regressions).
- **Not a GOAL_ACHIEVED candidate yet:** J-99 + J-100 remain unbuilt buildable Must-haves
  — they follow in later iterations. This iteration only closes J-97/J-98 + suite green.
- **Out of scope (do NOT touch):** `compute_market_phase` phase/severity/P(bear)/episode/
  recovery math; any snapshot rebuild / scanner / scoring / regime change / new stored
  column; J-99 / J-100; the descoped `/api/data` coverage warm-cost optimization; the
  non-blocking iter-38 `phaseBadgeVariant`/`phaseVariant` coherence WARN (optional cheap
  fold-in only if trivially touched, never required).

## Acceptance Criteria mapping
- **J-97 passes live (DoD #1, #2):** the cache-key `SCHEMA_VERSION` fix → `?full=true` at
  the live current as-of (cache HIT) serves `timeline_full` byte-identical to a fresh
  `compute_market_phase(...)["timeline_full"]` → bottom pane renders phase bands + 0–100
  severity line + filtered P(bear) line + as-of marker. Proven on live browser pixels,
  plus two byte-DISTINCT synced-zoom frames and an early-as-of honest-empty pane.
- **J-98 passes live (DoD #1):** first-paint compact at-a-glance summary (Market Regime
  label+score; Market Phase & Severity label+severity+band+filtered P(bear)) each with
  reachable named component breakdown (no bare number); More-detail expand (UT-12); an
  as-of change updating BOTH compact figures (UT-18) — now renders correctly because the
  embedded J-97 chart is populated.
- **Card + retrospective byte-identical (DoD #3):** the cache-HIT unit test asserts
  `?full=false` and the J-89 retrospective payload are byte-identical pre/post fix →
  J-87/J-88/J-89 unchanged.
- **Required-still-passing green (DoD #4):** backend diff touches NO scoring/regime/
  scanner/gate path → J-07 (Risk-Off→0 Actionable, CRITICAL) and J-44/J-49/J-87/J-88
  unchanged; no new date `useState`/`setAsOf`/window-keydown in chart/card/page + live
  `/` has 0 native `input[type=date]` → J-18 (exactly-one-date-selector, CRITICAL);
  J-06 single-source (compact figures == served values; pane-1 series == card series for
  the overlap window); J-13/J-43 (as-of switch drives both panes); J-89/J-90 unchanged.
- **No anti-goal violation (DoD #5):** `timeline_full` read VERBATIM from the existing
  `_timeline_series` — no second computation, no client severity/phase/P(bear) math
  (single source of truth + no recompute in read path); strictly causal per point
  (no lookahead); honest-empty on no-history (no fabricated data); no snapshot mutation
  (only the cache KEY string changes, payloads immutable); synced zoom is a visible-range
  view transform, never a second date control.
- **Suite green + handoff (DoD #6, #7):** full backend pytest flushes `0 failed, EXIT 0`
  (nohup-async via pump); dev handoff written at
  `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39-dev.md`.

## Key Test Scenarios
- **Cache-HIT unit test (the crux):** probe an already-populated OLD-schema cache row (or
  live current-as-of HIT) → `?full=true` now carries `timeline_full` byte-identical to
  `compute_market_phase(...)["timeline_full"]`; `?full=false` (card) + J-89 retrospective
  payloads byte-identical pre/post fix. MUST hit a HIT, not a fresh-compute MISS.
- **Live J-97:** bottom pane renders phase bands + 0–100 severity + filtered P(bear) +
  as-of marker over the same normalized index lines at the LIVE current as-of (the
  iter-38 failure case). Two byte-DISTINCT synced-zoom frames. Early-as-of honest-empty
  bottom pane (no fabricated series).
- **Live J-98:** first-paint compact at-a-glance (regime + phase/severity, each with
  reachable breakdown); More-detail expand; as-of change updates BOTH compact figures.
- **Required-still-passing live smoke:** J-18 (0 native `input[type=date]`, CRITICAL),
  J-07 (Risk-Off→0 Actionable, CRITICAL), J-06 (single source), J-44/J-49 (top pane
  unchanged), J-87/J-88 (card unchanged), J-13/J-43 (as-of drives both panes),
  J-89/J-90 (timeline + retrospective fence + recovery-turn unchanged).
- **Error/empty cases:** an as-of with no causal phase history serves an honest-empty
  `timeline_full` (empty list), not a fabricated series; an invalid `?full` value handled
  per the existing endpoint contract.
- **Suite gate:** FULL backend pytest flushes `0 failed, EXIT 0` (nohup-async, gate on
  the flushed line, never the in-flight stream).
