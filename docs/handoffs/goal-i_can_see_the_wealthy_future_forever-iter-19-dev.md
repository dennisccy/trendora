# goal-i_can_see_the_wealthy_future_forever-iter-19 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-19
**Date:** 2026-06-04
**Agent:** developer
**Status:** complete

## What Was Built

J-32 — the **Research point-in-time toggle** (All-history ⟷ As-of-date), the last buildable must-have
journey. A read-only point-in-time FILTER on the three `/research` labs, driven entirely by the existing
single global as-of switcher — **no second date state** (J-18 is the principal anti-goal risk).

**Backend (read-only `as_of` scoping seam — the iter-17 `compute_forward_aggregates` template, verbatim):**
- Threaded a **keyword-only** `as_of: Optional[date] = None` into the three public lab functions
  (`compute_factor_lab`, `compute_factor_combination`, `compute_event_study`) and their three SELECT-only
  observation builders (`_factor_observations`, `_combination_observations`, `_event_study_members`).
- In each builder, applied the **single membership filter** to the opening `ForwardReturn` query — identical
  to `forward_testing.py:579-583`:
  ```python
  fr_stmt = select(ForwardReturn).where(ForwardReturn.horizon == horizon)
  if as_of is not None:
      fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
          ScannerRun.asof_date <= as_of
      )
  fr_rows = session.exec(fr_stmt).all()
  ```
  Because `runs_with_fr`, `results`, `run_rows`, and the regime map all derive from `fr_rows`, this one clause
  scopes the whole pool. The cutoff reads the **canonical** `ScannerRun.asof_date` (not the denormalized
  `ForwardReturn.asof_date`). `as_of=None` adds **no** clause ⇒ byte-identical all-history.
- `compute_event_study` threads `as_of` through its **per-horizon loop** (and the defensive direct-call
  fallback) so every horizon row + the by-regime/by-sector slices reflect the same point-in-time window.
- Each compute function echoes the resolved cutoff as `asof_date` (ISO string when scoped, `null` in
  all-history mode).
- Added an optional `as_of` query param to the three endpoints in `api/research.py`, validated by the
  **shared** snapshot-served resolver `resolved_date(session, as_of, cfg)` (unparseable → 422, future → 400,
  before-history → 400 — never hand-rolled), then passed the resolved `date` into the compute fn. Omitted/empty
  ⇒ all-history. Kept the existing `latest_data_date is None → 503` guard.
- Updated the module + handler docstrings (which previously asserted "NONE has an as-of/date control") to the
  J-32 contract: each accepts the single global as-of as an optional scoping cutoff (a mode, not a second
  date state).

**Frontend (`/research` page — a MODE toggle, no date control):**
- Added a single page-level **All history ⟷ As of date** segmented button toggle (`AnalysisModeToggle`,
  styled like `HorizonSelector`/`SideToggle`, clicked directly — not a `<select>`), defaulting to All history.
- `import { useAsOf }`; one resolved cutoff `const asofCutoff = mode === "asof" ? asOf : null;` threaded into
  the page-level Factor-Lab effect, `<CombinationLab>`, and `<EventStudyLab>`.
- **Each lab's fetch `useEffect` depends on `asofCutoff` (the resolved cutoff), NOT raw `asOf`** — so toggling
  asof→all refetches (full sample returns), while in All-history mode moving the global date does **not**
  refetch the labs (cutoff stays `null`) → J-15 read-path discipline preserved.
- `lib/api.ts`: added an `asof?: string` arg to `fetchFactorLab`/`fetchFactorCombination`/`fetchEventStudy`,
  routed through the existing `withAsOf(...)` (so `?as_of=` is appended only when a historical cutoff is
  active); added optional `asof_date?: string | null` to the three response types.
- Added an inline `ModeContext` line that shows the resolved as-of date as the mode's context label.
- Updated the three stale "NO as-of/date control (J-18)" inline/JSX copies to the mode-aware truth.
- The survivorship/universe-relative/descriptive `CaveatBanner` still renders in **both** modes (not gated).

## Files Changed

- `apps/backend/app/engine/research.py` — keyword-only `as_of` on the 3 public fns + the single membership
  filter in the 3 observation builders; `asof_date` echo; docstrings.
- `apps/backend/app/api/research.py` — optional `as_of` query param on the 3 routes (validated via the shared
  `resolved_date`); module + handler docstrings.
- `apps/backend/tests/test_research.py` — new J-32 as-of engine tests (none==latest==all-history byte-identical;
  early cutoff scopes pool + no future-run leak; early-date low-sample NA; zero-snapshot honest-empty;
  combination + event-study scoping through the horizon loop); extended the 3 read-only keystone tests with a
  scoped call.
- `apps/backend/tests/test_api_research.py` — **updated** the 3 `*_no_date_control_present` tests + the module
  docstring to the new contract (deliberate J-32 acceptance change, iter-2 lesson — not a regression, not a
  delete); added as-of scoping/echo + 422-unparseable + 400-future tests for all three endpoints.
- `apps/frontend/app/research/page.tsx` — `AnalysisModeToggle` + `ModeContext`, `useAsOf`, `asofCutoff`
  threaded to all 3 labs (effects keyed on the resolved cutoff); stale J-18 copies updated.
- `apps/frontend/lib/api.ts` — `asof` arg via `withAsOf` on the 3 fetchers; `asof_date?` on the 3 types.

`runs/goal-session-.../state/blueprint.md` was already annotated for iter-19 by the decomposer (the iter-19
"NO skeleton change" note + the three lab Data-Contract rows annotated with the optional `as_of` cutoff). The
implementation matches that annotation exactly; **no** `blueprint.reapproval-requested` marker is written.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **476 passed, 4 skipped** in 1200.85s (~20 min). The 4 skips are the live-network `integration`
tests (skipped offline — expected). **No failures, no regressions.**

Targeted verification (also green):
- `pytest tests/test_research.py -k "as_of or read_only"` → **9 passed**
- `pytest tests/test_api_research.py` → **36 passed** (294.95s — each TestClient lifespan runs the
  walk-forward backfill)

Frontend: `cd apps/frontend && npm run build` → **compiled successfully, types valid, 13/13 pages generated**
(`/research` builds clean).

## J-18 note for the reviewer / evaluator (read this before judging the new `?as_of=`)

Sending `?as_of=D` on the research fetch **in As-of mode is correct and expected** — it is the single global
date being *transmitted* on a snapshot-served read, exactly like `/api/stocks?as_of=D` (MEMORY
`j18-asof-on-stocks-fetch-is-correct`). It is **NOT** a J-18 violation. Judge J-18 by:
- **Source:** `/research` holds no second date `useState` and exposes no date picker of its own; the as-of
  value is sourced solely from `useAsOf()`. The mode toggle is a mode (`"all" | "asof"`), not a date control.
- **Live:** exactly one date `<select>` on the page, a descendant of `<header>` (the global switcher), not
  `<main>`.

Consequently the three `test_*_no_date_control_present` tests were **intentionally updated** (not deleted) to
the new contract: the default payload's `asof_date` is `null`; a `?as_of=D` call scopes the pool + echoes the
resolved `asof_date`; there is no SECOND date field (`asof_dates`/`date`/`is_latest` absent).

## Known Issues

- The **full backend suite is green** — 476 passed, 4 skipped (offline `integration` tests) in ~20 min. No
  regressions. The scoring/snapshot/forward_testing path is git-verified untouched (no DB regen), so J-06/J-07
  stay byte-identical.
- A production `.next` exists from the typecheck `npm run build`; browser QA must start a fresh `next dev`
  (the `start-frontend.sh` default, which regenerates `.next`) — do **not** run `npm run build` against a live
  dev server (MEMORY `browser-qa-dead-shell-next-cache`).

## Suggested Next Phase

J-32 was the last buildable must-have journey. With it landed and nothing regressed, **GOAL_ACHIEVED is
reachable on the buildable set** (29/32; J-22 / J-23 / J-24 remain honestly blocked NA, non-halting — do **not**
autonomously re-probe the Yahoo-429 data-walled three). The goal-evaluator should verify J-32 + the
required-still-passing set (J-18, J-15, J-25–J-31, J-06/J-07) and, if all green, declare the goal achieved on
the buildable set.
