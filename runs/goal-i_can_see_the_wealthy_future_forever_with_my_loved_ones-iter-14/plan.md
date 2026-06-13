# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14 Execution Plan

Phase goal: **J-63 — Event study is overlap-honest (first-trigger Episodes by default).** The Setup &
Pattern Lab (`/research`) defaults to a first-trigger **Episodes** view that collapses consecutive
same-symbol signal-days of a subject into one observation, with a one-click **Episodes ⇄ Pooled**
toggle whose Pooled figures are byte-identical to today's. Both modes disclose n + unique symbols +
episode count. This is the LAST buildable failing Must-have; passing it green (with no regression +
clean coherence) makes the next evaluation a GOAL_ACHIEVED candidate.

## What to Build

- **Episode-collapse helper** (backend, `research.py`): pure in-memory deterministic grouping of the
  existing `_event_study_members` rows. For each `(ticker, subject)`, runs of **consecutive stored
  snapshot dates** (consecutiveness judged on the ordered `ScannerRun.asof_date` sequence — the global
  stored run-date order, NOT calendar adjacency) collapse into ONE episode observed at its **first
  trigger date**, carrying that observation's stored `return`/`mae`/`mfe`/`regime`/`sector` verbatim.
  Recomputes nothing. Reuse the `run_rows` the helper already loads (currently discards all but
  `regime_label`) to build the `run_id → asof_date` map and the global ordered run-date index.
- **`view` parameter** (`"episodes"` default | `"pooled"`) threaded through `compute_event_study(...)`
  so EVERY figure (per-horizon distribution, hit-rate, expectancy, MAE/MFE, best-exit-horizon,
  risk-adjusted ratios, by-regime, by-sector) derives from the mode's observation set. `view="pooled"`
  MUST reproduce current output **byte-identical** (pooled path stays the existing member list; episode
  path is purely additive).
- **Three disclosure values** on the payload for the selected horizon, present in BOTH modes:
  `n` (observations in current mode), `unique_symbols` (distinct tickers in the mode's set),
  `episode_count` (distinct first-trigger episodes — identical in both modes since it counts episodes
  regardless of which mode renders).
- **API `view` param** on `GET /api/research/event-study` (`api/research.py`), validated to the two
  allowed values (422 on anything else — same pattern as the existing subject/horizon validation),
  threaded to `compute_event_study`.
- **Samples cohort `view`** — extend `_event_study_samples` (`samples.py`) and `GET
  /api/research/samples` with the same `view` cohort parameter; the drill-down lists the mode's
  observations (episode rows in `episodes`, signal-day rows in `pooled`) and its total equals the
  clicked `N` in BOTH modes. Samples episode rows reuse the SAME episode-collapse helper (one
  membership rule, one builder family — never a second grouping path).
- **Glossary entries** (config catalog): add **Episode** and **Pooled (per-signal-day)** terms to
  `config.yaml` `methodology.terms` (category `forward_evidence`) so they appear on `/methodology` and
  as term tooltips — pure catalog data, referenced from the single catalog, never re-described in code.
- **Frontend Episodes ⇄ Pooled toggle** in `EventStudyLab` (`apps/frontend/app/research/page.tsx`),
  styled like the existing `SideToggle`/`AnalysisModeToggle` segmented groups (clicked directly, not a
  `<select>`), defaulting to **Episodes**. Local `view` state threads into `fetchEventStudy` and into
  every `N=` chip's samples href.
- **Disclosure line** beside the figures in BOTH modes: **n** (current mode), **unique symbols**,
  **episodes** (read verbatim from the payload; ISO/number formatting only).
- **Cohort serialization** — carry `view` in the event-study `N=` chip serialization
  (`apps/frontend/lib/samples-link.ts` `EventStudyCohortParams`) so the samples drill-down (new tab per
  J-65) reproduces the same mode + cohort; `/research/samples` reads `view`. The `view` param is a
  cohort/mode selector ONLY — it MUST NOT touch `?asof`, the asof-provider, or the J-32 analysis-mode
  state.

## Agents Required

- backend-data: **yes** — episode-collapse helper + `view` threading in `research.py`/`samples.py`, two
  API endpoint params with 422 validation, disclosure values, config glossary entries, and the full
  test battery (byte-identity guard, episode-collapse determinism, count-coherence both modes, read-only
  assertion, disclosure-value correctness).
- frontend-ux: **yes** — Episodes⇄Pooled segmented toggle, disclosure line, `view` threaded into
  `fetchEventStudy` (extend `lib/api.ts`) and `N=` chip hrefs + `EventStudyCohortParams`, `/research/samples`
  reads `view`. `tsc --noEmit` is the frontend gate (ESLint not installed — lessons iter-1).
- developer: yes -- implements both backend and frontend per the IN SCOPE list; TDD on the backend
  battery; foreground-runs targeted modules and hands the full pytest suite (~46–59 min) to the pump.

## Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/engine/research.py` -- add episode-collapse helper; thread `view` through
  `compute_event_study` + the per-horizon/by-regime/by-sector path; add `n`/`unique_symbols`/
  `episode_count` to the payload. Pooled path stays byte-identical.
- `apps/backend/app/api/research.py` -- add `view` (default `episodes`) query param to
  `GET /api/research/event-study`, validate to `{episodes, pooled}` (422 otherwise), thread to engine.
- `apps/backend/app/engine/samples.py` -- add `view` cohort param to `_event_study_samples` (and
  `compute_samples` event-study branch); reuse the episode-collapse helper for episode rows.
- `apps/backend/app/api/research.py` (samples route, or wherever `GET /api/research/samples` lives) --
  accept + validate + thread `view` for the event-study kind.
- `config.yaml` -- add **Episode** and **Pooled (per-signal-day)** entries under `methodology.terms`
  (category `forward_evidence`). NO new validated section, NO numeric tunable, NO threshold ref needed.
- `apps/backend/tests/test_research*.py` / `test_api_research*.py` / `test_samples*.py` -- new tests:
  byte-identity guard, episode-collapse determinism (consecutive collapse + gap-split), count-coherence
  both modes, read-only SELECT-only assertion, disclosure-value correctness, 422 on bad `view`.
- `apps/frontend/app/research/page.tsx` -- Episodes⇄Pooled toggle in `EventStudyLab`, local `view`
  state, disclosure line (n / unique symbols / episodes), thread `view` into fetch + `N=` hrefs.
- `apps/frontend/lib/api.ts` -- extend `fetchEventStudy` signature with `view`; add the three disclosure
  fields to `EventStudyResponse`.
- `apps/frontend/lib/samples-link.ts` -- add `view` to `EventStudyCohortParams` + its serialization.
- `apps/frontend/app/research/samples/page.tsx` (or the samples reader) -- read `view` from the URL and
  thread it to the samples fetch; render the mode's observations.

## UI Evolution

- New user-facing capability: the user reads **overlap-honest** event-study evidence — by default each
  continuous run of a symbol triggering a subject counts ONCE (Episodes); one click reveals the raw
  per-signal-day Pooled figures. n, unique symbols, and episode count are always shown so window overlap
  is never hidden.
- New information displayed: Episodes-mode forward-return distribution / hit-rate / expectancy /
  MAE-MFE / risk-adjusted ratios / by-regime / by-sector per subject; the n + unique-symbols +
  episode-count disclosure line; Episode and Pooled glossary entries on `/methodology`.
- New user actions: the Episodes ⇄ Pooled toggle on the Setup & Pattern Lab; clicking an `N=` chip in
  either mode opens the mode-correct samples drill-down in a new tab.
- UI surface changes: `/research` Setup & Pattern Lab gains the toggle + disclosure line (no new page);
  `/research/samples` honors the `view` cohort param; `/methodology` gains two glossary entries.
- Navigation changes: none. No new surfaces, no nav-skeleton change. Everything lands on existing homes
  (Research / Samples / Methodology). Blueprint already updated additively (no re-approval per spec).

## Visual Requirements

- Component patterns: reuse the existing segmented-group pattern (`SideToggle` /
  `AnalysisModeToggle` in `page.tsx`) for the new Episodes⇄Pooled toggle — a button group with an active
  pill, NOT a `<select>`. The disclosure line reuses the lab's existing muted-text / faint-label
  treatment. Reuse `Card` / `PanelTitle` already wrapping the lab.
- Layout: in place inside the existing `EventStudyLab` card — toggle near the subject selector / mode
  context, disclosure line beside the figures. No new page or panel.
- Key visual effects: match the existing lab (dense, dark, monospace/tabular numbers, active-pill on the
  segmented toggle). No new effects.
- States to handle: loading (existing skeleton), empty / low-sample (honest NA + n, never a fabricated
  row — in BOTH modes), error (existing "Backend unavailable" banner). The toggle and any clickable
  `N=` chip / disclosure value MUST NOT nest a `<button>` inside another interactive element or around
  `TermInfo`/`InfoTooltip` (lessons iter-5 nested-interactive hazard).

## Key Test Scenarios

- **J-63 browser:** `/research` Setup & Pattern Lab loads in **Episodes** mode by default with a visible
  Episodes⇄Pooled toggle and the n + unique-symbols + episodes disclosure; for a persisting subject
  (e.g. Risk-off-watchlist) pooled n > episode n and the episode-mode `N=` drill-down shows ONE row for
  a continuous run at its first-trigger date; flipping to Pooled shows figures **byte-identical** to the
  current published values; clicking an `N=` chip in each mode opens a new tab whose drill-down total
  equals the clicked N; `/methodology` explains Episode vs Pooled.
- **Byte-identity guard (unit):** `compute_event_study(..., view="pooled")` and
  `GET /api/research/event-study?view=pooled` reproduce the existing pre-change output exactly for
  representative subjects/horizons.
- **Episode-collapse determinism (unit):** consecutive stored run-dates for the same `(ticker, subject)`
  collapse to ONE first-trigger observation; a break in the stored run-date sequence yields separate
  episodes; episode rows carry stored return/MAE/MFE/regime/sector verbatim.
- **Count-coherence both modes (unit):** `/api/research/samples` total equals the event-study `n` for
  the same cohort params + `view`, and lists exactly that mode's rows. (Assert SAME-INSTANT against the
  live aggregate — never a hardcoded N from an earlier capture; lessons iter-7.)
- **Read-only (unit):** `compute_event_study` and `_event_study_samples` issue ONLY SELECTs in the new
  path — no INSERT/UPDATE/session.add/commit/run_scan/score_*/detect_*/forward_* call.
- **Disclosure values (unit):** `n` mode-dependent; `unique_symbols`/`episode_count` correct for a
  constructed multi-run subject.
- **Error cases:** `view` outside `{episodes, pooled}` → 422 on BOTH endpoints; empty/low-sample cohort
  → honest NA + n (never a fabricated row) in both modes.
- **Regression sweep (must stay green):** J-29 (lab renders all figures), J-51/J-64/J-65 (samples
  count-coherence + sort/filter + new-tab chips in both modes), J-25/J-26/J-27/J-30/J-31/J-32 (other
  labs unchanged), J-12/J-47 (glossary), J-18 (one date control), J-06 (score coherence).
- **Gates:** full backend pytest passes with no regressions (run to completion / hand to pump — never
  block the evaluator on the in-flight suite; gate on the flushed terminal summary line). Frontend gate
  is `tsc --noEmit`.

## Risks / Open Questions

- **Byte-identity is the hard guard.** The pooled path must be the *unchanged* existing
  `_event_study_members` list. Implement `view` so the pooled branch routes through exactly the prior
  code path (additive episode branch only) — do not refactor the pooled computation. The dedicated
  byte-identity test is the safety net; write it FIRST (capture pre-change output as the fixture).
- **Consecutiveness is on the stored run-date sequence, NOT calendar dates.** Episodes split on a gap in
  the ordered `ScannerRun.asof_date` index (a subject NOT triggered on an intervening stored run-date
  breaks the run), not on calendar adjacency. The `run_id → asof_date` map plus the global ordered
  run-date list must both come from the `run_rows` the helper already loads. Document this in the
  helper's docstring.
- **No new stored column / table / migration / config numeric tunable.** Designed to add NONE (episode
  collapse is in-memory grouping of stored rows) — this avoids the iter-12 `_ADDITIVE_COLUMNS` 500 trap
  by construction. The win/loss `>0` boundary and episode-consecutiveness are STRUCTURAL rules, not
  magic numbers. If a column is somehow introduced it MUST be registered in `db.py` `_ADDITIVE_COLUMNS`
  with a guard test — but do not add one.
- **Glossary config addition is catalog data, not a validated screen.** Still grep every
  config-narrowing site before declaring done (`apps/backend/tests/`,
  `apps/backend/scripts/build_qa_fixture_db.py`, `apply_universe_to_config.py`) — lessons iter-11. The
  new `forward_evidence` terms need no `ref`/threshold (plain `{term, category, definition, where}`),
  so `_methodology_refs_resolve` is unaffected; verify the >=100-term count and unique-key validators
  still pass.
- **`view` orthogonality (anti-goal).** The Episodes⇄Pooled toggle is a cohort/MODE selector — it MUST
  NOT touch `?asof`, `asof-provider.tsx`, the global as-of state, or the J-32 all/asof analysis-mode
  `mode` state (which is the unrelated existing `useState<"all"|"asof">` in the page). Keep them as
  fully independent local states.
- **One date control held (J-18).** No second date state may be introduced. The new toggle is a mode,
  never a date.
- **Full pytest is long (~46–59 min)** — single instance only, never two concurrent (lessons). The dev
  turn runs targeted research/samples/api modules in the foreground and hands the full suite to the
  pump; the goal-evaluator gates on the flushed summary, not the in-flight run.
- **md5 evidence hygiene (iters 3/7/10):** require one distinct capture per claimed surface; md5sum the
  evidence dir first; validate filename-vs-content for any shared-byte capture before accepting a PASS.
- **Owed opportunistic check (non-gating):** if the QA session is already on the dashboard, verify the
  J-44 indexes/regime chart toggle-off → reload → still-off persistence cycle and capture it early — it
  is NOT a gating leg for this iteration.
- **GOAL_ACHIEVED candidacy:** this is the final buildable Must-have. If J-63 lands green, all
  required-still-passing journeys hold, and coherence passes, flag for the evaluator that the next
  evaluation is a GOAL_ACHIEVED candidate (J-01..J-21, J-25..J-67 passing/already_passing; J-22/J-23/J-24
  blocked-NA — data-walled, non-vetoing, confirmed verbatim by prior evaluators).
- **Scope check:** all IN SCOPE items align with goal.md Capability 29 + the J-63 canonical-value row.
  No scope creep detected — Factor/Combination Lab compute, the J-32 analysis-mode, the global as-of
  state, and any new stored column/table/migration are explicitly OUT OF SCOPE and excluded.

## Assumptions (recorded, not blocking)

- Episode/Pooled glossary entries go under the existing `forward_evidence` category in
  `config.yaml` `methodology.terms` as plain authored terms (no threshold `ref`). If a different
  category better fits the catalog's authoring convention, dev may choose it — the requirement is only
  that both terms render on `/methodology` and as tooltips from the single catalog.
- The `episode_count` value is identical in both modes (it counts first-trigger episodes regardless of
  which mode renders), per the spec — implemented as one derivation surfaced on both payloads.
- The samples route is `GET /api/research/samples` served by `compute_samples` (event-study branch);
  `view` is threaded there the same way `subject_key`/`horizon`/`slice_kind` already are.
