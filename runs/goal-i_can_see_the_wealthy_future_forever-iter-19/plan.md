# goal-i_can_see_the_wealthy_future_forever-iter-19 Execution Plan

**Target journey:** J-32 — Research point-in-time toggle (All-history ⟷ As-of-date). The **last buildable**
must-have journey. After it lands with nothing regressed, GOAL_ACHIEVED is reachable on the buildable set
(29/32; J-22/J-23/J-24 honestly blocked NA, non-halting — **do NOT re-probe them**).

**Goal alignment:** clean. `docs/goal.md` Product Shape already documents `/research` with "an optional
**'As of date'** mode [that] restricts every figure to snapshots dated ≤ the global as-of date … a mode,
not a second date picker," and the J-32 + "Research lab is read-only" anti-goal prescribe exactly this
read-only FILTER. No scope creep; no drift from the goal.

## What to Build

A point-in-time **mode** on the three `/research` labs that, when active, filters every figure to snapshots
dated ≤ the **existing global as-of date** — reusing the proven iter-17 seam verbatim and introducing **no
second date state** (J-18 is the principal risk).

**Backend** (`research.py` + `api/research.py`)
- Thread a **keyword-only** `as_of: Optional[date] = None` into the three public lab functions, mirroring
  `compute_forward_aggregates(..., *, as_of=None)`:
  - `compute_factor_lab(session, factor_key, horizon, config=None, *, as_of=None)` → into `_factor_observations`
  - `compute_factor_combination(session, conditions, horizon, config=None, *, as_of=None)` → into `_combination_observations`
  - `compute_event_study(session, subject_key, horizon, config=None, *, as_of=None)` → into `_event_study_members`
    **⚠ thread through the per-horizon LOOP** (`research.py:839-845` calls `_event_study_members` once per
    `wf.horizons` **plus** a defensive fallback) — every call must receive `as_of`, not just one.
- In each of the three observation builders, apply the **single membership filter** to the opening
  `fr_rows` query — verbatim from `forward_testing.py:579-583` (all three currently open with the identical
  `select(ForwardReturn).where(ForwardReturn.horizon == horizon)`; `ScannerRun` is already imported):
  ```
  fr_stmt = select(ForwardReturn).where(ForwardReturn.horizon == horizon)
  if as_of is not None:
      fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
          ScannerRun.asof_date <= as_of
      )
  fr_rows = session.exec(fr_stmt).all()
  ```
  Because `runs_with_fr`, `results`, `run_rows`, and `regime_by_run` are all derived from `fr_rows`, this
  one clause scopes the whole pool. Cutoff = canonical `ScannerRun.asof_date` (**not** the denormalized
  `ForwardReturn.asof_date`). `as_of=None` adds **no clause** → all-history **byte-identical**.
- Add an optional `as_of` query param to the three endpoints. **Reuse the established validator** —
  `resolved_date(session, as_of, cfg)` from `snapshot_serving` already maps unparseable→**422**,
  future→**400**, before-history→**400**, no-data→**503** (the same convention as `/api/stocks?as_of=`,
  `/bars?as_of=`). Do **not** hand-roll validation. Pass the resolved `date` into the compute fn; when
  `as_of` is omitted → all-history (default). Keep the existing `latest_data_date is None → 503` guard.
- Payload echoes the **resolved cutoff** as `asof_date` when scoped; **null/absent** in all-history mode
  (consistent with every other read endpoint). No other payload-shape change (`n`/`n_total` drop naturally).
- Update the now-false docstrings (module header + each handler currently assert *"NONE has an as-of/date
  control (J-18)"*) to the J-32 contract: each accepts the **single global as-of** as an optional
  point-in-time scoping cutoff (a mode, not a second date state); default remains all-history.

**Frontend** (`app/research/page.tsx` + `lib/api.ts`)
- Add a single page-level **`"all" | "asof"` segmented toggle** (style like `HorizonSelector`/`SideToggle`
  — a button group, **not** a `<select>`, so browser QA clicks it directly), default **All history**;
  label "All history" ⟷ "As of date". In As-of mode show an inline "As of {asof_date}" context label from
  the global provider.
- `import { useAsOf }`; compute one **resolved cutoff** `const asofCutoff = mode === "asof" ? asOf : null;`
  (`asOf` is already `string | null` — null at latest, so As-of@latest == all-history, matching J-09).
  Thread `asofCutoff` into the page-level FactorLab effect, `<CombinationLab>`, and `<EventStudyLab>`.
- **⚠ Each lab's fetch `useEffect` must depend on `asofCutoff` (the resolved cutoff), NOT raw `asOf`.** This
  is the hinge for J-15 + J-32-step-4: (a) toggling `asof→all` refetches (full sample returns); (b) in
  **All-history mode, moving the global date does NOT refetch** (cutoff stays `null`) — preserving the
  read-path discipline and the genuine cross-date nature of all-history.
- `lib/api.ts`: add an `asof?: string` arg to `fetchFactorLab`/`fetchFactorCombination`/`fetchEventStudy`,
  routed through the existing `withAsOf(...)` so `?as_of=` is appended **only** when a historical cutoff is
  active; add optional `asof_date?: string` to the three response types.
- Update the three stale inline/JSX copies that read "NO as-of/date control (J-18)" / "No date control"
  (page lines ~533-534, ~915-916, ~958-961) to the mode-aware truth.
- Keep the survivorship/universe-relative/descriptive `CaveatBanner` visible in **both** modes (do not gate
  it on mode — it already renders unconditionally).

**Blueprint** (`runs/goal-session-.../state/blueprint.md`)
- Add an iter-19 **"NO skeleton change"** note (additive mode on the EXISTING approved `/research` home) and
  annotate the three lab Data-Contract rows with the optional `as_of` scoping cutoff (a refinement of
  existing values — mirror how iter-17 annotated `compute_forward_aggregates`). **No** new value, no new
  endpoint, **no** `blueprint.reapproval-requested` marker.

## Agents Required
- developer: **yes** — backend (the `as_of` seam across 3 functions + 3 builders + 3 endpoints) and
  frontend (mode toggle + `useAsOf` wiring + `lib/api.ts`); plus the test updates + blueprint annotation.
- backend-data: **yes** (research engine + API)
- frontend-ux: **yes** (`/research` mode toggle + as-of context label)
- reviewer, qa, ui-impact-analyst, ui-test-designer, browser-qa-agent, ux-regression-reviewer,
  coherence-auditor, phase-closure-auditor, auditor: **yes** (full depth — per spec NOTES).

Frontend Present: yes

## Files to Create/Modify
- `apps/backend/app/engine/research.py` — `as_of` kwarg on the 3 public fns; the single membership filter
  in `_factor_observations` / `_combination_observations` / `_event_study_members`; docstrings.
- `apps/backend/app/api/research.py` — optional `as_of` query param on the 3 routes (validate via
  `resolved_date`), echo resolved `asof_date`, pass cutoff to compute; module + handler docstrings.
- `apps/backend/tests/test_research.py` — engine as-of tests for each of the 3 functions (see scenarios).
- `apps/backend/tests/test_api_research.py` — endpoint as-of tests; **UPDATE all three**
  `test_factor_lab_no_date_control_present` / `test_factor_combination_no_date_control_present` /
  `test_event_study_no_date_control_present` **and the module docstring (line 8)** to the new contract.
- `apps/frontend/app/research/page.tsx` — mode toggle, `useAsOf`, `asofCutoff` threaded to all 3 labs.
- `apps/frontend/lib/api.ts` — `asof` arg via `withAsOf` on the 3 fetchers; `asof_date?` on the 3 types.
- `runs/goal-session-i_can_see_the_wealthy_future_forever/state/blueprint.md` — iter-19 note + 3 row annotations.
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-19-dev.md` (+ `-frontend.md`) — handoffs.

## ⚠ Flags (surface to developer / reviewer / evaluator)
1. **THREE contract tests, not one.** The spec names only `test_factor_combination_no_date_control_present`,
   but there are **three** symmetric `*_no_date_control_present` tests (factor-lab, combination, event-study)
   plus the module docstring (line 8). The `as_of` param + `asof_date` echo affects all three endpoints, so
   **all three tests + the docstring must be UPDATED to the new contract** — a deliberate J-32 acceptance
   change (iter-2 lesson: update the invariant to the new truth), **NOT** a regression and **NOT** a silent
   delete. New truth: the default (all-history) payload has `asof_date` null/absent; a `?as_of=D` call scopes
   the pool + echoes the resolved `asof_date`; there is no SECOND date param (only the single global `as_of`).
2. **`?as_of=D` on the research fetch is correct, not a J-18 violation** (MEMORY `j18-asof-on-stocks-fetch-is-correct`).
   It is the single global date *transmitted* on a snapshot-served read, exactly like `/api/stocks?as_of=D`.
   Judge J-18 by: the page holds no second date state / exposes no date control of its own (the as-of value
   comes solely from `useAsOf()`); live, exactly one date `<select>` and it is a descendant of `<header>`,
   not `<main>`. State this in the dev handoff so the reviewer/evaluator do not misread the new `?as_of=`.
3. **`compute_event_study` threads `as_of` through a horizon loop**, not a single call (above).
4. **All-history must be byte-identical** (`as_of=None` adds no clause) — the regression guard test below.

## UI Evolution
- New user-facing capability: switch `/research` between **All history** (default) and **As of date** —
  in As-of mode, setting the global switcher to an earlier day re-points every decile / rank-IC /
  combination-cohort / event-study figure to that point-in-time walk-forward window (smaller n, honest NA).
- New information displayed: a point-in-time view of all `/research` analytics, with reduced `n` and honest
  NA at early dates; the resolved as-of date shown as the mode's inline context label.
- New user actions: one **All history ⟷ As of date** mode toggle at the top of `/research`. **No** new date
  control — the global top-bar switcher supplies the date.
- UI surface changes: `/research` only — one additive mode toggle + an inline "As of {date}" label. The
  three lab sections are otherwise unchanged (they re-point with the mode).
- Navigation changes: **none** (lives on the existing approved `/research` home; no nav-skeleton change).

## Visual Requirements
- Component patterns: reuse the existing `Card` panels + the segmented button-group pattern of
  `HorizonSelector`/`SideToggle` for the mode toggle (`role="group"`, `aria-pressed`, `data-testid`). Keep
  the `CaveatBanner` (warn-bordered Card) in both modes.
- Layout: unchanged page layout; place the mode toggle in the top control row beside the existing selectors.
- Key visual effects: palette tokens only (accent for the active segment, muted for inactive); monospace
  tabular-nums for all numbers; no new colors.
- States to handle: As-of-at-latest == all-history (no surprise empty); early-date thin sample → NA + n
  (never fabricated); loading/error/empty already handled per lab — preserve them under both modes.

## Key Test Scenarios (must pass for the phase to be complete)

**Browser (Chrome MCP) — J-32 end-to-end + J-18** (ensure a clean hydrated build first — MEMORY
`browser-qa-dead-shell-next-cache`: confirm `GET /_next/static/chunks/main-app.js → 200`; do not `npm run
build` against the live dev `.next`):
1. `/research` defaults to **All history**; capture baseline decile/rank-IC + a combination cohort + an
   event-study table with their `n` (distinct sha256 shots + DOM/network assertions — iter-6 lesson).
2. Toggle to **As of date**; set the global switcher to one of the **earliest** dates (bottom of the
   descending list — thin by **date**, not horizon, per iter-11). DOM-assert each lab's figures change and
   `n` **drops**; early-date low-sample cells show NA + n (never a fabricated number). Drive the global
   `<select>` with the native-setter + bubbling change event (MEMORY `react-controlled-select-needs-native-setter`).
3. Toggle back to **All history**; DOM-assert the full-sample figures (larger `n`) return.
4. **J-18 live:** exactly one date `<select>` on the page, a descendant of `<header>` (not `<main>`); in
   As-of mode the research fetch carries the single global `?as_of=` (expected); in All-history mode, moving
   the global date leaves the research figures unchanged with **no** research refetch (network-asserted).

**Backend unit/integration** — mirror the iter-17 as-of tests for **each** of the 3 functions/endpoints:
- `as_of=None` == `as_of=latest` == current all-history (**byte-identical** — the all-history regression guard).
- `as_of=D` (early D) pools **only** snapshots with `ScannerRun.asof_date ≤ D` → strictly smaller
  `n_total`/cell `n`; **no future-run leak** (a run dated > D contributes nothing — assert via fixture or by
  comparing pooled counts across two cutoffs).
- Low-sample / NA at an early cutoff (decile/cohort/regime cells with `n < min_sample` → NA + n).
- Endpoint validation: unparseable `as_of` → **422**; future (> latest) → **400**; valid historical → scoped
  payload echoing resolved `asof_date`; an as-of so early a lab has zero contributing snapshots → honest
  empty/NA (`n=0`), never a fabricated row or a 500.
- Read-only keystone: extend the existing patch-to-raise test so the **scoped** path also recomputes no
  return/factor/regime; forbidden-call grep (`run_scan`/`score_stocks`/`backfill*`/`forward_return`/
  `detect_*`/`score_regime`) still hits only docstrings in `research.py`.
- The three updated `*_no_date_control_present` tests assert the **new** contract (flag #1).

**Suite gate:** backend pytest green (run **once** — ~14-18 min, MEMORY `backend-test-suite-runtime`);
frontend `npm run build` typechecks/builds clean. J-06/J-07 byte-identical (scoring/snapshot path
git-verified untouched — **no DB regen**). J-25/J-26/J-27/J-29/J-30 unchanged in All-history mode and
correctly re-point in As-of mode; J-15 read-path preserved; J-31 synthesis cross-link intact.

## Out of Scope (exclude — per spec)
- No re-probe/build of **J-22/J-23/J-24** (Yahoo-429 data-walled, non-halting; auto-heal via committed runbook).
- **No second date state / no date picker** on `/research` — the toggle is a MODE; the date comes only from
  the global provider (J-18, the principal risk).
- No new page/route/nav/endpoint/config value; no blueprint re-approval.
- No change to `scoring.py`/`scanner.py`/`regime.py`/`patterns.py`/`buckets.py`/`forward_testing.py` storage/
  `snapshot_serving.py`/`asof-provider.tsx`/`stocks/page.tsx`/`backtest/page.tsx`; **no DB regen**.
- Do not touch the `/backtest` per-date scorecard's as-of behavior (J-09/J-14 already deliver it).
- Watch-item (carry, not this iter): stale `data/page.tsx:141` subtitle prose — tidy in a future touch.
