# Iteration 28 — Coherence Audit

**Iteration:** goal-market-compass-iter-28
**Date:** 2026-08-31
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `state_band` (regime/stress/breadth direction words + deltas) — NEW row addendum registered in blueprint's iter-28 update | OK | `apps/backend/app/engine/compass.py:268-345` (`build_state_band`, sole producer, called once inside `build_manifest_payload` at `compass.py:719-723`); served verbatim by `GET /api/compass` via `manifest_row_payload` (`compass.py:1310-1312`, unchanged route file `apps/backend/app/api/compass.py`, not touched this diff); frontend reads `compass.state_band.*` verbatim with no client threshold — `apps/frontend/components/compass-state-band-card.tsx:57,84,115,141` (`DirectionBadge` just renders `word ?? "NA"`) |
| Regime label + score | OK (re-read, no recompute) | `compass-state-band-card.tsx:52-58,79-88` reads `dashboard.regime` (same `GET /api/dashboard` payload as before); `apps/frontend/app/market/page.tsx:178-207` (`RegimeGlanceCard`) reads the identical field — two display surfaces of the same canonical value, blueprint's own row for this value explicitly permits multiple readers ("compass reads this value, never recomputes it") |
| Market phase / severity / P(bear) | OK (re-read, no recompute) | `compass-state-band-card.tsx:92-125` reads `phase` from `GET /api/market-phase`; `market/page.tsx:212-266` (`PhaseGlanceCard`) reads the same endpoint — both are the SAME served object, no independent computation |
| Breadth level | OK (re-read, no recompute) | `compass-state-band-card.tsx:130-142` reads `dashboard.breadth.above_50dma_pct`; `market/page.tsx`'s `MoreDetailSection` reads the same `dashboard.breadth` block — single source, `GET /api/dashboard` |
| Severity used inside `build_state_band`'s `stress` band | OK — canonical reader, not a second computation | `compass.py:268-278` (`_severity_at`) calls `market_phase.market_phase_cached(session, as_of, cfg)` — the SAME cache-backed reader `build_narrative` already uses for the current run, just invoked for the previous run's date too; no re-derivation of severity itself |
| `session_delta.changes` ("Leadership rotation" filtered view) | OK — presentational filter only, no new value | `apps/frontend/components/compass-leadership-rotation-section.tsx:38` filters the already-served `compass.session_delta.changes` (existing J-02 Data Contract row, `GET /api/compass`) to `kind ∈ {sector, theme, stock}`; no client-side score/word computation |
| Direction-word vocabulary | OK — one shared map | `compass.py:134-144` (`_flat_band_word`) is the single classifier both `_direction_word` (regime, pre-existing) and `build_state_band`'s stress/breadth bands call — `compass.vocabulary.direction_words` is read once, never duplicated |
| New config threshold `compass.delta.stress_velocity_flat_band` | OK — config-only, no magic number | `config.yaml:1411`, `apps/backend/app/config.py:2570-2589` (typed field + `>= 0` validator) |

No new function was found that independently recomputes any registered value; no new UI surface fetches a registered value from a non-canonical endpoint. `state_band` is a genuinely new value and it IS registered (blueprint `state_band.md` iter-28 update block, matching the iter spec's "Data-contract additions" section field-for-field) — not an unregistered-value WARN.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/` renamed "Dashboard" → "Today" | OK | `apps/frontend/components/sidebar.tsx:34` — `{ href: "/", label: "Today", icon: Compass }`, matches blueprint's target NAV row exactly |
| `/market` (new route) | OK | `sidebar.tsx:35` — `{ href: "/market", label: "Market", icon: LayoutDashboard }`, immediately after Today, 1 click from persistent nav; every other of the 10 remaining entries (`sidebar.tsx:36-46`) is byte-identical in route/order/label to before (`git diff` shows only the two-line insertion) |
| Today page body (state-band card, Leadership rotation section) | OK — subsections of the already-registered Today home, not a new route | Blueprint IA row "J-07 Today page ... whole page, top to bottom" already covers all of `/`'s body; no separate IA row is owed to a subsection |
| `/market` shell | OK — no parallel shell | `apps/frontend/app/layout.tsx` and `apps/frontend/components/asof-provider.tsx` are untouched by this diff (`git diff b74605d -- apps/frontend/app/layout.tsx apps/frontend/components/asof-provider.tsx` is empty) — `/market` renders inside the existing app shell with the existing single `?asof` owner, not a new layout |
| Regime × phase cross-view chart | OK — relocated, not duplicated | Removed from `/` (`apps/frontend/app/page.tsx` diff deletes `DashboardBody`/`PhaseCrossViewCard` usage entirely) and lives only at `/market` (`market/page.tsx:167`); Today carries a single labelled link-out (`compass-state-band-card.tsx:64-71`) to `/market`, not a second copy of the chart |

No hidden feature, no undiscoverable route, no duplicate home, no parallel shell.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **QA/evidence gap outside this gate's scope, noted for the evaluator:** the dev handoff
  (`docs/handoffs/goal-market-compass-iter-28-dev.md`, "Known Issues" #1) states no browser-qa agent ran
  this iteration (dispatched `lean` despite the spec's `Depth: full`), so J-07/J-08's rendered UI was
  never visually verified and `state_band`'s three-word happy path is unobservable live under this
  iteration's authorized safe `as_of` set (every safe date already carries a pre-iter-28 manifest row,
  so `state_band` reads `null` on every live call made). `reports/qa/goal-market-compass-iter-28-evidence/`
  contains only J-01/J-02/J-03/J-04/J-05/J-06/J-10/J-11 screenshots (the regression set), none for J-07/J-08.
  This does not create a Data Contract or IA violation — the code as written is structurally consistent
  with the blueprint — but the goal-evaluator should weigh whether J-07/J-08 can be certified passing
  without browser evidence.
- **Design judgment call, not a coherence issue:** the developer flags (dev handoff, "A deliberate design
  decision" section) that `state_band.stress.direction_word` classifies the NEGATION of
  `state_band.stress.delta` (severity rising = "deteriorating" even though the raw delta is positive) —
  a deliberate AG-3-motivated choice the developer itself flags as possibly diverging from TC-2's most
  literal text. This is a correctness/spec-compliance question for the reviewer/evaluator, not a
  duplicate-source or navigation issue.
- `reports/phase-goal-market-compass-iter-28-ui-surface-map.md` does not exist for this iteration; surfaces
  were derived directly from the diff instead (page.tsx, market/page.tsx, sidebar.tsx, the two new
  components, api.ts).
