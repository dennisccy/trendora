**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-1 (J-18: Backtest reads the single global as-of switcher)

- **Session:** i_can_see_the_wealthy_future_forever
- **Iteration:** 1 — lean, frontend-only consolidation
- **Snapshot SHA:** `d831c5506a11c50b27badf80153809faad2da7a8` (matches `iter-1/snapshot-sha`)
- **Diff audited:** `git diff d831c550…` + `git diff HEAD` (uncommitted). One source file changed:
  `apps/frontend/app/backtest/page.tsx` (38 +/82 −). Other diffs are session bookkeeping
  (telemetry/trace/session.json) — no source impact.
- **UI surface map:** absent (lean iteration) — surfaces derived from the diff + source.

This iteration's whole purpose **is** a coherence consolidation: it realizes the blueprint's
prescribed fix for invariant #5 / J-18 (delete the Backtest page-local date picker, drive the page
from the single global `useAsOf()` switcher). It strengthens single-source-of-truth rather than
risking drift. No objective Part A or Part B violation found.

## Part A — Data Contract (PASS — no violation; divergence removed)

- **No new computation of any registered value.** The diff adds no function/service/endpoint. It only
  removes code. No new displayed value (spec: "New information displayed: None").
- **Relevant contract value — "Snapshot-served reads + resolved as-of date / available dates"**
  (canonical: `app.engine.snapshot_serving` + as-of resolution in `scanner`; available dates from
  `GET /api/runs`; resolved `asof_date` echoed by every read endpoint).
  - **Before:** `app/backtest/page.tsx` held a **second, independent** date source — its own
    `fetchRuns()` call plus `dates`/`latest`/`ready`/`selected` state (the exact invariant-#5 / J-18
    violation this gate exists to catch).
  - **After:** the page reads `asOf` from the shared global `useAsOf()` provider
    (`app/backtest/page.tsx:6,54,62,78`). That provider is the **same** canonical one `/stocks`
    consumes (`components/asof-provider.tsx`, which calls the canonical `GET /api/runs` once,
    centrally — verified at `asof-provider.tsx:5,41`). The page's divergent date source is **deleted**,
    not duplicated → consolidation onto the canonical source.
  - The "Viewing as-of {date} (historical|latest)" badge is **re-format-only** of the canonical
    echoed value: `state.backtest.asof_date` / `!state.backtest.is_latest`
    (`page.tsx:82-83`), falling back to the global `asOf`/`globalIsHistorical` before load. No
    client-side recomputation of a date. Re-format of a canonically-served value is explicitly allowed.
- **Result:** no duplicate computation, no non-canonical source, no unregistered new value.

## Part B — Information Architecture (PASS — no violation)

- **No new page/route/feature.** `/backtest` stays at its existing canonical home under the unchanged
  nav skeleton. Spec confirms: "No sidebar/nav change," "No blueprint change."
- **No parallel shell:** the change *removes* a page-local control and consumes the existing app-shell
  global switcher (mounted in `app/layout.tsx`) — the opposite of inventing a parallel nav.
- **No duplicate home / reachability change:** Backtest's reachability is untouched.

## Part C — Advisory (none blocking)

- The page-level "Viewing as-of …" badge now co-exists with the global top-bar indicator. This is
  **intended** (spec: the badge is "a display indicator, not a control"; both read the same resolved
  date) — not a duplicate control and not label/format drift. No advisory note warranted.

## Invariant #5 verification (the core gate check this iteration)

Confirmed against source, not just the browser-QA summary (per the iter-0 lesson cited in the spec):

- (a) **No date `<Select>` / picker remains:** `grep` of `app/backtest/page.tsx` for
  `Select|fetchRuns|BacktestDatePicker|aria-label` → none. The `BacktestDatePicker` component
  definition and the `Select`/`fetchRuns` imports are deleted.
- (b) **Imports & uses `useAsOf`, effect keyed on `[asOf]`:** `page.tsx:6` import, `:54` hook call,
  `:78` `}, [asOf]);`. All five fetches (`fetchBacktest`/`fetchDashboard`/`fetchSectors`/
  `fetchThemes`/`fetchStocks`) are driven from `asof = asOf ?? undefined` (`page.tsx:62,64,67-70`).
- (c) **No independent date state:** the only remaining `useState` is the page's loading/ok/error
  `state` (`page.tsx:55`) — not a date. `selected`/`latest`/`dates`/`ready` are gone.

→ Invariant #5 ("Exactly one date selector") is now **satisfied**; the frontend holds no second,
independent date state. This clears the session's only live (critical-family) anti-goal violation and
enables the evaluator to mark the date-selector `anti_goal_violations` entry `resolved: true`.

## Bottom line

No objective Data-Contract or Information-Architecture violation. The iteration is a clean,
single-file consolidation that eliminates a divergent date source and aligns Backtest with the
blueprint's canonical global as-of control. **COHERENCE-PASS.**
