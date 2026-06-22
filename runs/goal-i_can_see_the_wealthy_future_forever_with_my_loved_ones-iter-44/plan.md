# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44 Execution Plan

Cohesive Dashboard cross-view cluster **J-101 + J-102**. Full depth: backend (new served
`severity_velocity` field + cache SCHEMA bump + new typed config window) and frontend (chart
re-format, tooltip enrichment, full-history band clamp, duplicate-card removal). In-place resume
after the iter-43 GOAL_ACHIEVED — goal.md queued J-101..J-104 as buildable Must-haves with no
journey-history entry, so the goal is NOT achieved (iter-22 lesson). J-103/J-104 are next iter (iter-45).

## What to Build
- **Backend — config:** Add a typed, load-validated lookback key `severity_velocity_window` (default 5)
  to the EXISTING `config.market_phase` block (`MarketPhaseCfg` in `apps/backend/app/config.py`, near
  line 1099). Validate strictly positive at load (boot fails loudly on non-positive). Add it to
  `config/config.yaml` AND every inline test config dict / config-narrowing script (grep first — count grows).
- **Backend — severity_velocity:** In `market_phase.py` `_timeline_series` (line ~380), ADDITIVELY compute
  a per-date `severity_velocity` = the deterministic config-windowed slope of the served 0-100 `severity`
  over the prior `severity_velocity_window` snapshots; sign positive = worsening; STRICTLY causal (severity
  at dates ≤ each date only); NA at the warm-up head where the window is unavailable; never smoothed with
  future data. Add it to each point of `timeline_full` and the bounded `timeline` tail, read VERBATIM from
  the SAME single derived series (no second computation).
- **Backend — cache schema bump:** Bump `SCHEMA_VERSION` `"s1"` → `"s2"` at `market_phase.py:797` so
  `_cache_version` (line ~800) refreshes EVERY `MarketPhaseCache` row to the new shape; a stale pre-iter-44
  row missing `severity_velocity` must never be served. Mirror to the retrospective cache path if it shares
  the schema risk.
- **Frontend — J-101(a):** REMOVE the standalone `<MajorIndexesCard />` (page.tsx line 158) + its import
  (line 8). The J-97 `<PhaseCrossViewCard />` pane 0 already IS that chart. Dashboard renders exactly one
  market chart.
- **Frontend — J-101(b):** Ensure the bottom phase pane's bands span the FULL stored history at any as-of
  (phase-band primitive clip stays `null`; `timeline_full` fetched UNFILTERED by the global as-of, mirroring
  the top regime pane via `/api/regime-history?full=true`). Selected as-of renders ONLY as the marker;
  post-D history is display-only and feeds no as-of-scoped value. Honest-empty timeline → honest-empty pane.
- **Frontend — J-102(chart):** REMOVE the plotted filtered-P(bear) line (the `PBEAR_SCALE_ID` overlay
  series, lines ~206-213) and draw a ZERO-CENTERED `severity_velocity` line on that retired overlay scale
  slot (with a 0 reference) so the index % lines stay undistorted.
- **Frontend — J-102(tooltip):** In `CrossTooltipBox` (lines ~288-330), ADD the stored market-regime
  label + 0-100 score for the hovered date (read VERBATIM from the already-fetched `/api/regime-history`
  points) and the served `severity_velocity`, while RETAINING the existing date, index %, phase, severity,
  and P(bear) rows (only the plotted P(bear) line is removed; its tooltip value stays).

## Agents Required
- developer: yes -- both backend (config key + `severity_velocity` derivation + SCHEMA_VERSION bump + unit
  tests) and frontend (remove `MajorIndexesCard`, full-history band clamp, swap P(bear) line → severity-
  velocity line, enrich tooltip). The frontend RE-FORMATS only: it computes no velocity/regime/probability.

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/config.py` -- add validated `severity_velocity_window` (default 5) to `MarketPhaseCfg`
- `apps/backend/app/engine/market_phase.py` -- additive `severity_velocity` in `_timeline_series`; bump `SCHEMA_VERSION` s1→s2
- `config/config.yaml` -- add `market_phase.severity_velocity_window: 5`
- `apps/frontend/app/page.tsx` -- remove `<MajorIndexesCard />` + its import
- `apps/frontend/components/phase-cross-view-chart.tsx` -- full-history band clamp; remove P(bear) line, draw zero-centered severity-velocity line; enrich `CrossTooltipBox` with regime label/score + velocity
- `apps/frontend/components/phase-cross-view-card.tsx` -- fetch `timeline_full` unfiltered by as-of if needed (verify wiring)
- inline test config dicts under `apps/backend/tests/` + scripts under `apps/backend/scripts/` -- add the new required config key (grep `severity_velocity_window` to find all; do NOT trust a fixed list)
- `apps/backend/tests/test_market_phase.py` (+ a focused fast no-boot test module) -- unit tests below
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-dev.md` -- dev handoff

## UI Evolution
- New user-facing capability: the Dashboard market view is de-cluttered to a single chart, its phase
  context reads consistently across full history at any as-of, and a severity-velocity line shows at a
  glance whether market stress is worsening or easing, with regime status legible on hover.
- New information displayed: a per-date zero-centered severity-velocity value (line + tooltip row;
  positive = worsening) on the cross-view phase pane, and the stored market-regime label + 0-100 score in
  the cross-view hover tooltip.
- New user actions: none new — hover/zoom/pan on the existing single synced two-pane chart. No new control,
  no new date state.
- UI surface changes: Dashboard `/` — the duplicate Major-indexes & regime card removed; the phase pane
  plots a severity-velocity line instead of the P(bear) line, with full-history bands and an enriched tooltip.
- Navigation changes: none. Both journeys land on the existing Dashboard `/` home; no new surface, no nav-
  skeleton change. Additive blueprint edits only (no reapproval filed).

## Visual Requirements
- Component patterns: reuse the EXISTING `PhaseCrossViewCard` / cross-view chart and tooltip primitives;
  no new component library elements. Match the established Dashboard card style.
- Layout: unchanged Dashboard grid; net result is one fewer card (duplicate removed), single market chart.
- Key visual effects: severity-velocity drawn as a zero-centered line on the retired P(bear) overlay scale
  with a visible 0 reference; keep the existing two-pane synced shared-axis behavior; phase bands the full
  history width. Tooltip rows match existing typography/swatch style.
- States to handle: loading (existing skeleton), honest-empty phase pane at an early as-of (no fabricated
  band), NA velocity at the warm-up head (rendered honestly, never a fabricated slope).

## Key Test Scenarios
- **J-101 (browser, live, Playwright fallback PLANNED UP FRONT; md5sum evidence dir first):** Dashboard
  renders exactly ONE market chart — the standalone Major-indexes & regime card is absent. Capture the
  phase pane bands spanning FULL history at a HISTORICAL as-of (bands do not truncate at the marker) AND the
  honest-empty phase pane at an early as-of (no fabricated band) — TWO byte-DISTINCT frames.
- **J-102 (browser, live):** the phase pane plots a zero-centered severity-velocity line (no plotted P(bear)
  line); the hover tooltip shows regime label + 0-100 score + severity-velocity AND still retains phase,
  severity, and P(bear) rows. Capture the tooltip-visible frame.
- **Unit — derivation:** `severity_velocity` equals the deterministic config-windowed slope on a known
  severity series; sign convention positive = worsening; NA at the warm-up head where the window is unavailable.
- **Unit — no-lookahead tail-invariance:** removing bars dated > D does not change `severity_velocity` at
  any date ≤ D (mirror the existing forward_return / filtered-P(bear) tail-invariance tests).
- **Unit — cache-schema correctness (iter-38/39 keystone):** SEED a genuine OLD-schema `s1` `MarketPhaseCache`
  row with `severity_velocity` STRIPPED (a real cache HIT, not a fresh compute), then assert the served
  `timeline_full` `severity_velocity` is byte-identical to a fresh `compute_market_phase` — proving s1→s2
  forces the recompute. Probe the LIVE current as-of (a HIT), not a fresh-compute date.
- **Unit — byte-identity of everything else:** `phase` / `severity` / `p_bear` / the J-89 episodes +
  retrospective fence / the J-90 recovery signal stay byte-identical to pre-change (purely additive field).
- **Unit — config validation + magic numbers:** a non-positive `severity_velocity_window` fails boot
  loudly; `test_no_magic_numbers` stays green (lookback is config-sourced).
- **Required-still-passing live smoke:** J-97 (two synced panes, shared axis), J-98 (at-a-glance still
  shows P(bear), expand works), J-87/J-88 (Market-Phase card P(bear) unchanged), J-44/J-49 (indexes/regime
  full-history bands), J-06 (figures == served), J-18 (0 native `input[type=date]` on `/`), J-07 (Risk-Off
  → 0 Actionable — API invariant).
- **Suite gate:** full backend pytest flushes `0 failed, EXIT 0` (nohup-async via the pump; never block the
  evaluator on the in-flight suite). On this 1369-run host verify the anti-goal-critical legs (no-lookahead
  tail-invariance, determinism, config-validation, `test_no_magic_numbers`, cache-schema) via FAST no-boot
  tests and hand the full suite to the pump (iter-29 lesson).

## Notes / Assumptions / Guardrails
- **Additive-guard traps (iter-20/23/32):** if any `set(payload) == {...}` exact-shape guard covers
  `/api/market-phase`, update it to accept the additive `severity_velocity` key IN THIS ITER. No new
  `table=True` model and no new column on an existing table (so no `test_db.py` / `_ADDITIVE_COLUMNS`
  changes) — `severity_velocity` is an in-memory additive field on a derived/cached payload.
- **DO NOT** change any canonical score, regime label/score, the filtered/smoothed P(bear) values, the
  J-89 episode/retrospective fence, the J-90 recovery signal, or the Risk-Off→Actionable gate. The
  Market-Phase CARD and the J-98 at-a-glance keep showing P(bear) unchanged.
- **OUT OF SCOPE (excluded):** J-103 (`/research/severity-velocity` study) and J-104 (research-labs
  caching / query-bounding / lazy-load + page-split) — next iteration; do NOT touch `/research`,
  `research.py`, the research routes, or the nav skeleton. No new endpoint, no new snapshot column, no
  snapshot rebuild, no `kind:rebuild` (~11h, destructive).
- **Render evidence (iter-38/39/40/42/43 lesson):** Chrome MCP CDP has repeatedly emptied the evidence
  dir; browser-qa MUST plan the Playwright fallback UP FRONT, md5sum the evidence dir FIRST, and reject any
  blank/skeleton/byte-identical frame — the differential legs (full-history bands vs as-of marker; severity-
  velocity line replacing P(bear)) REQUIRE byte-distinct frames.
- **Alignment:** the spec is consistent with `docs/goal.md` (J-101/J-102 verbatim, lines 2343-2359; the
  J-101..J-104 non-data-dependent note, lines 2379-2387) and violates no anti-goal. No scope drift detected.
- **Service cleanup:** kill dev servers BY PORT (8835 backend, 3835 frontend) — never a broad
  `pkill -f "uvicorn"` / `pkill -f "next dev"` on this multi-project machine.
