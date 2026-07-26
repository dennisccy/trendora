# Phase goal-ops-hardening-iter-24 — UX Regression Review

**Date:** 2026-07-26

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

**Capability 1 — global "background compute running (N)" badge**
- Navigation path: **0 clicks.** `HealthBadge` is rendered once in `apps/frontend/app/layout.tsx:44` (root layout), so the conditional `data-testid="background-compute-indicator"` child appears on every page the instant `backgroundCompute.active.length > 0`, with no click required.
- Label: "background compute running (N)" — clear and literal; correctly scoped to this feature's stated audience (operators diagnosing dispatch timing), not consumer-facing marketing copy.
- Visual feedback: confirmed present as a sibling `Badge` (`variant="accent"`, pulsing dot) next to the existing readiness pill in browser QA UT-02/UT-10, and confirmed absent (no DOM element) when `active` is empty (UT-01, UT-07). Never hides or replaces the pill.
- Verdict: **fully discoverable**, zero clicks, unambiguous label.

**Capability 2 — `BackgroundComputePanel` on `/data`**
- Navigation path: **1 click** — Dashboard (`/`) → "Data Manager" sidebar link → `/data`. Verified directly by browser-qa-agent (UT-11: `window.location.pathname === "/data"`, single click of `a[href="/data"]`). Well within the 2-click bar.
- Placement confirmed in code: `apps/frontend/app/data/page.tsx:614` — `<BackgroundComputePanel />` sits immediately after `<RunHistoryPanel .../>` (line 610), matching the plan's required layout and the existing Card/PanelTitle convention used by `JobProgressPanel`/`RunHistoryPanel` (no new component primitive).
- Label: panel heading is exactly "Background compute" (`<h2>`), and the hint text (verbatim, quoted in UT-11) explains the trigger condition ("a /backtest request... when a historical as-of's evidence is not yet ready") in plain language, understandable without backend jargon (the "MCP query_backtest" aside is a minor technical mention but not load-bearing for comprehension).
- States all verified via DOM extraction (screenshots blank below-the-fold due to the documented host tooling limitation, not a product defect): idle-never-run (UT-04), active window with live-incrementing `horizons_done`/elapsed (UT-03), completed outcome with duration matching the API to the millisecond (UT-05, AG-3 satisfied), and the always-visible process-lifetime disclosure sentence in every state (UT-08).
- Verdict: **fully discoverable**, 1 click, clear label and honest copy.

**Label confusion:** none found. "background compute running (N)" and "Background compute" consistently name the same concept across badge and panel; no mismatch with spec terminology (goal.md / plan.md both use "background compute").

**Visual consistency:** No new component primitives introduced — `Card`/`PanelTitle`/`Badge` reused verbatim (confirmed in `apps/frontend/app/data/page.tsx` and `health-badge.tsx`). The active-window badge reuses the SAME `variant="accent"` + `animate-pulse` dot convention already used by `HealthBadge`'s own `awaiting_snapshot`/`initializing` states (per the frontend handoff's "Visual conformance" section) — no arbitrary colors or new effects. Panel sits in the existing vertical panel stack with no new grid/layout structure. This is consistent with the DESIGN SYSTEM and prior-phase visual style.

## Regression Risk

| Shared component | Prior feature(s) served | Current change | Risk |
|---|---|---|---|
| `health-badge.tsx` / `readiness-provider.tsx` | J-04 (non-blocking boot with visible status) — every page's readiness pill; also read by warmup/preflight consumers | Adds one new conditional sibling element and one new context field (`backgroundCompute`); no existing field/behavior altered | **Low.** J-04 replayed PASS this iteration (deterministic replay, `UT-J-04`). Browser QA UT-10 separately confirmed pill wording/color unchanged across Ready/Initializing/Unavailable states, badge always a distinct sibling `<div>`, never nested or overlapping. |
| `app/data/page.tsx` (`RunHistoryPanel`, `JobProgressPanel`) | J-01 (backfill honors requested range), J-03 (no per-run range cap) — both surface through `/data`'s job/run panels | New panel appended after `RunHistoryPanel`; neither panel's code was modified | **Low.** J-01 and J-03 both replayed PASS this iteration (`UT-J-01`, `UT-J-03`). Browser QA UT-09 independently confirmed every pre-existing `/data` heading is present, in the original order, with "Background compute" the only new (and last) entry. |
| `/api/health` response shape | J-05 (aggregates precomputed at ingest), J-06 (pages load only what they need), J-08 (backtest evidence served from storage only) — none of these directly depend on `/api/health`'s shape, but all are required-still-passing this iteration | One additive top-level field (`background_compute`); zero change to `readiness`/`warmup`/`preflight` keys | **Low.** All three replayed PASS (`UT-J-05`, `UT-J-06`, `UT-J-08`). |
| `app.engine.forward_testing` dispatch registry (`_HIST_DISPATCH_INFLIGHT` set→dict) | J-07 (heavy aggregates never take the service down) — depends on the SAME single-flight guard | Registry becomes a dict with added bookkeeping fields; keying/dispatch-decision logic unchanged (dev handoff states pre-existing iter-19/iter-20 concurrency tests re-run unchanged and pass) | **Low-to-medium in theory (data-structure change to the same guard J-07 relies on), mitigated in practice.** Browser QA UT-J-07 exercised a real background-compute window and polled `/api/health` 20/20 times at HTTP 200 with no frozen window; dev handoff confirms the pre-existing set→dict-affecting unit tests (`-k "iter20 or iter19"`) still pass. |

No prior-phase user journey shows a regression this iteration. One non-regression **observation** surfaced by browser QA (UT-07): when the backend is fully unreachable, `/data` uses a single shared all-or-nothing loading gate, so every panel — including the pre-existing Coverage/Storage/Drift panels, not just the new `BackgroundComputePanel` — disappears together rather than degrading independently. QA correctly attributes this to pre-existing page architecture that predates this iteration (every panel affected equally), not something introduced by this phase's diff. Not counted as a regression here for that reason, but flagged for visibility since it does affect how gracefully the new panel (and its neighbors) degrade under a total backend outage.

## UI vs Backend Parity

| Backend capability (this iteration) | UI exposure |
|---|---|
| `started_at`/`horizons_done`/`horizons_total` registry bookkeeping | Surfaced via `background-compute-active-row` (as-of, elapsed, "horizons X/Y") — confirmed live-incrementing in UT-03 |
| Bounded `recent_outcomes` ring (`background_compute_history_size`) | Surfaced via `background-compute-last-outcome` (most-recent entry only; full ring length is a backend cap, not separately surfaced — matches the plan, which only requires showing "the most recent completed/failed outcome," not the whole ring) |
| `get_background_compute_status()` / `GET /api/health` `background_compute` field | Consumed by `ReadinessProvider` from the existing poll, no second fetch — confirmed in `readiness-provider.tsx` and by QA (badge/panel both track the same live values) |
| `startup.background_compute_history_size` config | Intentionally **not** surfaced in the UI — this is a backend boot-time config value (analogous to other `StartupCfg` fields), not a runtime setting a user edits in-app. `user-visible-changes.md` explicitly discloses this decision rather than silently omitting it. This is an acceptable backend-only gap, not a stranded capability. |

`user-visible-changes.md`'s "Not Visible Yet: None" claim holds up against the actual diff — every field the backend now computes (`active[]`, `recent_outcomes[]` and their sub-fields) has a corresponding rendered element, cross-verified byte-for-byte against `GET /api/health` in QA's UT-03/UT-05/UT-06.

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None.

### Potential Regressions
None confirmed. See "Regression Risk" table above — all touched shared components (`health-badge.tsx`, `readiness-provider.tsx`, `/data`'s panel stack, the dispatch registry backing J-07) had their dependent journeys re-verified passing this iteration (deterministic replay for J-01/J-03/J-04/J-05/J-06/J-08, browser QA smoke for J-07).

### Visual Consistency
No issues. New surfaces reuse existing `Card`/`PanelTitle`/`Badge` primitives and the existing `accent`+pulse-dot convention already established by `HealthBadge`'s other states; no arbitrary values, no new layout/grid, no new nav entry — matches the plan's explicit "no new component primitives" requirement and prior-phase styling.

## Recommendation

No action required for this iteration. One item worth a future (non-blocking) backlog note, unrelated to J-09's own scope: `/data`'s all-or-nothing loading gate means a total backend outage hides every panel at once rather than degrading each independently — this predates iter-24 and was not introduced by it, so it is not a gate on this phase's verdict, but it is worth a backlog card if per-panel graceful degradation on `/data` is ever prioritized.
