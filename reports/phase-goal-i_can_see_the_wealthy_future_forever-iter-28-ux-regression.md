# Phase goal-i_can_see_the_wealthy_future_forever-iter-28 — UX Regression Review

**Date:** 2026-06-10

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

This iteration adds no new pages, routes, or sidebar entries. All new user-visible capabilities are surfaced through existing pages and the existing top-bar header shell. Discoverability is assessed by navigation path from any page.

### Three-state top-bar readiness badge (Ready / Initializing… n/m / Unavailable)

- **Navigation path:** Present on every page. The badge is mounted in the sticky top-bar header via `layout.tsx` → `HealthBadge` inside the `ReadinessProvider` wrapper. A user sees it on page load without any click.
- **Reachable within 2 clicks:** Yes — it is always visible (0 clicks).
- **Label clarity:** The three states are unambiguous to a non-technical user: "Ready" (green), "Initializing… history 4/11" (amber with monospace progress), "Backend unavailable" (red). The loading placeholder "Checking backend…" is neutral and transient.
- **Visual feedback:** The `warn` variant adds an `animate-pulse` amber dot during the Initializing state, providing motion feedback. The `ok` and `danger` variants provide color feedback.
- **Assessment:** Discoverable. No flags.

### Backtest page warming state ("Warming up — historical evidence still loading n/m")

- **Navigation path:** Sidebar → "Backtest" (1 click from any page). The warming card renders in the main content area while `readiness === "initializing"`.
- **Reachable within 2 clicks:** Yes — 1 click.
- **Label clarity:** "Warming up — historical evidence still loading" is clear. The subtext explicitly tells the user the page will populate automatically without a refresh. It does not present as an error.
- **Visual feedback:** A `Loader2` spinning icon (amber), `border-warn` card border, and `text-warn` heading clearly distinguish this from an error state.
- **Assessment:** Discoverable. No flags.

### Research page warming state (all three labs)

- **Navigation path:** Sidebar → "Research" (1 click). The warming card renders for all three labs (Factor Lab, Combination Lab, Event Study) while `readiness === "initializing"`.
- **Reachable within 2 clicks:** Yes — 1 click.
- **Label clarity:** Same WarmingState component as Backtest — consistent, clear, non-error framing.
- **Visual feedback:** Same spinner + warn styling as Backtest.
- **Assessment:** Discoverable. No flags.

### Auto-populate on readiness flip (Backtest and Research)

- **Navigation path:** No separate navigation required — this is an automatic behavior on the Backtest and Research pages when `readiness` transitions from `initializing` to `ready`. The effect re-runs via the `readiness` dependency in the fetch `useEffect` on both pages.
- **Label clarity:** No separate label — the warming card simply disappears and the full data populates. The behavior is self-evident.
- **Assessment:** No action required — the transition is automatic and requires no user action.

---

## Regression Risk

The following components changed in this iteration are shared with prior features. Regression risk is assessed for each.

### `apps/frontend/components/health-badge.tsx` — changed

- **Prior feature served:** All prior iterations use this component for the binary "Backend OK / Backend unavailable" badge (established since iter-1). It is visible on every page.
- **Change:** The component now imports `useReadiness` from the new `ReadinessProvider` context, replacing the direct `fetchHealth` poll with a shared context read for the readiness pill. The static detail badges (provider, seed date, symbol count) still fetch via `fetchHealth` in a one-time effect.
- **Regression risk:** Low. The component's output for the `ready` state is a visually equivalent green pill ("Ready" vs previous "Backend OK" — minor label change). The prior binary Unavailable state is preserved. All existing consumers read the badge purely visually — no tests or prior features depend on the badge's internal fetch path. The new `data-state` and `data-testid` attributes add browser-QA test anchors without removing prior ones.
- **Prior label change note:** The previous "Backend OK" label has been renamed to "Ready". This is a minor label change for which no prior phase explicitly depends on the exact text. The semantic intent (green = operational) is identical.

### `apps/frontend/app/layout.tsx` — changed

- **Prior feature served:** Layout shell is shared by all pages across all prior iterations. Every sidebar entry, the global `AsOfSwitcher`, and the `HealthBadge` are in this file.
- **Change:** `ReadinessProvider` wrapper was added around `AsOfProvider` and the layout shell. No structural change to the sidebar, header, or navigation.
- **Regression risk:** Low. The `ReadinessProvider` is an additive context wrapper; it does not alter the routing, sidebar links, or layout structure. All prior pages remain at their existing routes. The `Sidebar` component is unchanged.
- **Navigation integrity:** All 10 sidebar routes (Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Watchlist, Methodology, Data Manager) are intact in `sidebar.tsx`. No route was removed or renamed.

### `apps/frontend/app/backtest/page.tsx` — changed

- **Prior feature served:** Backtest page was built in prior iterations to show the forward-test scorecard, regime/sector/theme summary, and return attribution (J-09, J-14, J-19, J-21, J-25, J-26, J-29, J-32 journeys). The global as-of switcher drives the date (J-18).
- **Change:** `useReadiness` is imported and `readiness` is added as a dependency of the main fetch `useEffect`. A `shouldShowWarming(readiness)` gate wraps the content area — when `true`, renders `WarmingState`; when `false`, renders the existing skeleton/error/ok content tree unchanged.
- **Regression risk:** Low. The warming gate is only active when `readiness === "initializing"`. On a warm backend (normal usage), `readiness === "ready"` and the gate is transparent — the full existing content renders. The `readiness` dep in the effect only adds a re-fetch trigger on state transition, which is additive. J-18 is explicitly preserved: `readiness` is not a date state, and the `asOf` dep remains the sole date driver. The comment in the source explicitly documents J-18 preservation.

### `apps/frontend/app/research/page.tsx` — changed

- **Prior feature served:** Research page hosts the Factor Lab, Combination Lab, and Event Study labs (J-25, J-32). The as-of mode toggle (J-32) and the global as-of date (J-18) drive the analysis cutoff.
- **Change:** `useReadiness` imported, `readiness` added as dep to the Factor Lab effect, `shouldShowWarming` gate wraps all three lab sections. Same structure as Backtest.
- **Regression risk:** Low. Gate is transparent on a warm backend. The `asofCutoff` computation (J-32: `mode === "asof" ? asOf : null`) is unchanged. The mode toggle and factor/horizon selectors are unchanged. J-18 preserved per explicit comment.

### `apps/frontend/lib/api.ts` — changed

- **Prior feature served:** All API types and fetchers used across every page since iter-1.
- **Change:** `ReadinessState`, `WarmupProgress` types added; `HealthStatus` extended with `readiness`, `warmup`, `poll_interval_seconds`, `poll_idle_interval_seconds` fields. No existing field removed.
- **Regression risk:** Low. All existing fields on `HealthStatus` and all other types are unchanged. The extensions are purely additive.

---

## UI vs Backend Parity

| Backend Capability | UI Exposure | Assessment |
|---|---|---|
| `GET /api/health` extended with `readiness`, `warmup`, `poll_interval_seconds`, `poll_idle_interval_seconds` | `ReadinessProvider` polls this endpoint; `HealthBadge` renders the three states with live progress; Backtest and Research show the warming gate | Fully surfaced |
| `compute_readiness` → `ready` / `initializing` / `unavailable` states | Three-state badge in top bar on every page | Fully surfaced |
| Warm-up progress `done`/`total` ("history n/m") | Badge "Initializing… history n/m" + WarmingState card "(n/m)" on Backtest and Research | Fully surfaced |
| Fast-boot: server serves latest snapshot within readiness budget before full backfill | User-facing effect is faster page availability; badge shows `ready` once the minimal sync completes; no explicit "fast boot" control exists (correct — this is infrastructure behavior, not a user action) | Correctly surfaced as a behavioral improvement |
| Concurrency-safe `run_scan` IntegrityError guard (scanner.py) | No UI surface — internal robustness fix; no user-facing state changes | Correctly backend-only |
| Non-fatal warm-up: failure logged, server continues serving | The `unavailable` badge state correctly reflects a backend where no snapshot is servable; a warm-up failure that leaves a latest snapshot servable will show `ready`, not an error — matching the honesty requirement | Correctly surfaced |
| Startup `StartupCfg` config tunables (`readiness_budget_seconds`, poll cadences, batch size) | Poll cadences are delivered to the frontend via the health payload and drive `ReadinessProvider` intervals — no raw config surface in UI (intentional) | Correctly backend-only |
| Pre-computed snapshot seed (deferred / out of scope) | Documented as "Not Visible Yet" in user-visible-changes.md | Correctly deferred |
| Faster (memoized) scan engine (deferred / out of scope) | Documented as "Not Visible Yet" in user-visible-changes.md | Correctly deferred |

All backend capabilities that are in scope for this iteration are surfaced in the UI. The deferred items are correctly documented.

---

## Flags

### Hidden Capabilities

None. All new user-facing capabilities are surfaced in the UI through the existing layout shell and existing page content areas.

### Undiscoverable Capabilities

None. The three-state badge is always visible (0 clicks). The warming states on Backtest and Research are reachable in 1 click from any page.

### Potential Regressions

- **`health-badge.tsx` label change — "Backend OK" → "Ready":** The badge label for the green/operational state changed from "Backend OK" (prior iterations) to "Ready". Any browser-QA test that asserts on the exact text "Backend OK" would fail. However, no prior handoff documents a browser-QA capture asserting on this exact string value, and the semantic intent is identical. The risk is low — WARN-level at most, and confined to test assertions rather than product behavior.
- **`layout.tsx` context wrapper addition:** The `ReadinessProvider` now wraps the entire app shell. If any prior page component inadvertently calls `useReadiness()` without being inside the provider, it would throw. However, no prior page uses `useReadiness` — only the three iter-28-modified files (`health-badge.tsx`, `backtest/page.tsx`, `research/page.tsx`) import it. Risk is negligible.

### Visual Consistency

- The new `ReadinessProvider` adds no visible UI — it is a pure context provider with no rendered output.
- The `HealthBadge` continues to use existing `Badge` component variants (`ok`, `warn`, `danger`, `default`, `accent`). The three-state pill reuses the established `animate-pulse` dot pattern from the prior binary badge. No raw HTML or arbitrary Tailwind values are introduced for the badge states.
- The `WarmingState` card on Backtest and Research uses the existing `Card` component, `border-warn` and `text-warn` palette tokens, and a `lucide-react` `Loader2` spinner matching the dense dark analytical style of the rest of the application. The `n/m` progress uses the `num` monospace class consistent with other numeric displays in the UI (stock scores, run dates, seed dates in the badge, etc.).
- The `warming-state.tsx` and `readiness-provider.tsx` components contain no arbitrary pixel/color values — all styling is via design system classes (`bg-surface`, `border-warn`, `text-warn`, `text-text-muted`, etc.).
- The visual style of the new warming card is consistent with the existing error cards on the same pages (the error card on Backtest uses `border-neg bg-surface p-5 text-sm` — the warming card uses the same structure with `border-warn`). This consistent pattern makes the distinction between "error" (red) and "warming" (amber) clear and recognizable.
- No visual inconsistency found.

---

## Recommendation

No action required.

All new capabilities from this iteration are discoverable within 1 click or are always visible. No prior navigation paths were removed or altered. The changes to `layout.tsx`, `backtest/page.tsx`, `research/page.tsx`, `health-badge.tsx`, and `lib/api.ts` are additive and backward-compatible with all prior phase features. Visual consistency is maintained throughout using the existing design system tokens.

The sole minor note — the badge label change from "Backend OK" to "Ready" — is a deliberate UX improvement (clearer language) and does not represent a regression. No existing browser-QA capture is known to assert on the exact prior text.

The one deliverable that remains for this phase is the browser-QA test results file (`-ui-test-results.md`), which does not yet exist. This is expected: browser QA runs after this UX regression review. The UX regression review is based on source and artifact evidence, not on browser-QA outcomes.
