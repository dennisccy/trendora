# Goal Iteration 14 — Event study is overlap-honest (first-trigger episodes by default)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 14
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-63
- **Required-still-passing journeys:** J-29 (event-study lab), J-51 / J-64 / J-65 (samples drill-down count-coherence + new-tab chips), J-25 / J-26 / J-27 / J-30 / J-31 / J-32 (the other `/research` labs read unchanged), J-12 / J-47 (methodology glossary), J-18 (one date control), J-06 (score coherence)
- **Anti-goal reminders (verbatim from docs/goal.md Non-Goals / Constraints):**
  - **No order execution, no auto-trading, no brokerage integration, no capital deployment** — Trendora is decision-support and research only.
  - No machine-learning price prediction.
  - The backend is the **single source of truth**; the frontend only re-formats values from the API and never recomputes a score, return, or bucket.
  - **One config file** (`config.yaml`) holds every tunable … No scoring/threshold literal is hard-coded in calculation code.
  - (Coherence keystone) reads serve persisted-snapshot values; attribution & lab analytics are **read-only** — derived from stored returns/excursions/factor values; no fabricated data (low samples → NA + n, never a synthesized row).
  - (J-18 / invariant 5) **Exactly one date selector** — the global as-of control drives every date-scoped page; the Episodes⇄Pooled toggle is a MODE / cohort parameter, never a second date state.

## GOAL

The Setup & Pattern Lab (`/research`) defaults to a **first-trigger Episodes** view that collapses consecutive same-symbol signal-days of a subject into one observation, with a one-click **Episodes ⇄ Pooled** toggle whose Pooled figures are byte-identical to today's, both modes honestly disclosing n + unique symbols + episode count.

## BACKGROUND

J-63 is the LAST buildable failing Must-have; J-61/J-62 landed CONTINUE in iter-13 (commit 755a622d) and the iter-13 evaluator explicitly recommends targeting J-63 next at **full** depth. Full is warranted because this is a backend research-module change (`apps/backend/app/engine/research.py` + `samples.py` + two API endpoints) with a **hard byte-identity guard** — the Pooled toggle must reproduce the prior event-study figures exactly — plus a count-coherence requirement against the J-64/J-65 `N=` samples drill-downs in BOTH modes; it crosses backend+frontend and gates on the full pytest suite. Source verification (this iteration's plan is grounded in it): the current event study is **pooled-only** — `compute_event_study` / `_event_study_members` (research.py:711, 902) pool every per-signal-day occurrence and there is no `view`/episode concept anywhere in backend or `apps/frontend/app/research/page.tsx`'s `EventStudyLab` (research.py and the frontend confirmed to lack any episode/pooled-mode handling; the existing `mode` state in the page is the unrelated J-32 all/asof analysis-mode). Episode collapse is a pure deterministic grouping of the SAME `_event_study_members` rows — NO new stored column is needed (it avoids the iter-12 `_ADDITIVE_COLUMNS` trap by construction; `ScannerRun.asof_date` already gives the per-run date sequence). After J-63 passes with no regression and a clean coherence audit, the next evaluation is a **GOAL_ACHIEVED candidate** (J-22/J-23/J-24 stay blocked-NA, non-vetoing).

## IN SCOPE

### Backend
- [ ] Add a deterministic **episode-collapse** helper in `apps/backend/app/engine/research.py` that takes the existing `_event_study_members` per-observation rows for a `(subject, horizon)` and groups them: for each `(ticker, subject)`, runs of **consecutive stored snapshot dates** (consecutiveness judged on the ordered `ScannerRun.asof_date` sequence — the global stored run-date order, NOT calendar adjacency) collapse into ONE episode observed at its **first trigger date**, carrying that observation's **stored** `return` / `mae` / `mfe` / `regime` / `sector` verbatim. Pure in-memory grouping of stored rows — recomputes NO return, excursion, factor, regime, sector, or membership. Reuse the `run_rows` the helper already loads to build the `run_id → asof_date` map (it currently discards everything but `regime_label`). **No new stored column, no new table, no `models.py`/`db.py`/`config.py`/`config.yaml` change.**
- [ ] Thread a `view` parameter (`"episodes"` default | `"pooled"`) through `compute_event_study(...)` so EVERY figure respects the mode — per-horizon distribution, hit-rate, expectancy, MAE/MFE, best-exit-horizon, risk-adjusted ratios, by-regime, by-sector all derive from the mode's observation set. `view="pooled"` MUST reproduce the current output **byte-identical** (the episode path is additive; the pooled path stays the existing `_event_study_members` list unchanged).
- [ ] Compute and expose THREE disclosure values on the payload for the selected horizon, present in BOTH modes: `n` (observations in the current mode), `unique_symbols` (distinct tickers in the mode's observation set), `episode_count` (distinct first-trigger episodes for the subject/horizon — identical value in both modes since it counts episodes regardless of which mode is rendered). These are derivations of the SAME observation set — no new endpoint.
- [ ] Add `view` (default `episodes`) to `GET /api/research/event-study` (`apps/backend/app/api/research.py`), validated to the two allowed values (422 on anything else, matching the existing subject/horizon validation pattern); thread it to `compute_event_study`.
- [ ] Extend `_event_study_samples` in `apps/backend/app/engine/samples.py` and `GET /api/research/samples` with the same `view` cohort parameter so the drill-down lists the mode's observations (episode rows in `episodes`, signal-day rows in `pooled`) and its total equals the clicked `N` in BOTH modes. The samples episode rows reuse the SAME episode-collapse helper (one membership rule, one builder family — never a second grouping path).
- [ ] Methodology/glossary (J-47, config-backed): add **Episode** and **Pooled (per-signal-day)** glossary entries to the existing `config.methodology` catalog mechanism so they appear on `/methodology` and as term tooltips — referenced from the same single catalog, never re-described in code.

### Frontend
- [ ] Add an **Episodes ⇄ Pooled** segmented toggle to `EventStudyLab` in `apps/frontend/app/research/page.tsx` (styled like the existing `SideToggle`/`AnalysisModeToggle` segmented groups — clicked directly, not a `<select>`), defaulting to **Episodes**. It sets a local `view` state and threads it into `fetchEventStudy` (extend the signature in `apps/frontend/lib/api.ts`) and into every `N=` chip's samples href.
- [ ] Render the disclosure line beside the figures in BOTH modes: **n** (current mode), **unique symbols**, and **episodes** (read verbatim from the payload; ISO/number formatting only).
- [ ] Carry `view` as a cohort parameter in the event-study `N=` chip serialization (`apps/frontend/lib/samples-link.ts` `EventStudyCohortParams`) so the samples drill-down (opened in a new tab per J-65) reproduces the same mode + cohort; `/research/samples` page reads `view` and renders the mode's observations. The `view` param is a cohort/mode selector ONLY — it MUST NOT touch `?asof`, the asof-provider, or the J-32 analysis-mode state.

### New user-facing capability
The user reads honest, overlap-aware event-study evidence: by default each continuous run of a symbol triggering a subject counts once (Episodes), and one click reveals the raw per-signal-day Pooled figures — with n, unique symbols, and episode count always shown so window overlap is never hidden.

### New information displayed
Episodes-mode forward-return distribution / hit-rate / expectancy / MAE-MFE / risk-adjusted ratios / by-regime / by-sector for each subject; the n + unique-symbols + episode-count disclosure line; Episode and Pooled glossary entries on `/methodology`.

### New user actions
The Episodes ⇄ Pooled toggle on the Setup & Pattern Lab; clicking an `N=` chip in either mode opens the mode-correct samples drill-down in a new tab.

### UI surface changes
`/research` Setup & Pattern Lab gains the toggle + disclosure line (no new page); `/research/samples` honors the `view` cohort param; `/methodology` gains two glossary entries.

### Product surface delta
The event study stops over-counting overlapping signal-days by default, making the displayed evidence more conservative and honest, while preserving the exact prior numbers one toggle away for continuity.

### Blueprint conformance
No new surfaces and no nav-skeleton change. Everything lands on existing homes: the toggle/disclosure on **Research** (`/research`), the drill-down on **Samples** (`/research/samples`, link-reached under Research), the glossary entries on **Methodology** (`/methodology`). Blueprint already updated additively (no re-approval): IA J-63 TARGETs pinned to iter-14; the event-study and methodology Data Contract rows now register `view` (episodes/pooled) + the three disclosure values as derivations of the SAME observation set on the SAME endpoints.

### Data-contract additions
- **Event-study observation set in both modes** (already a registered Data Contract row — this iteration realizes the `[TARGET iter-14]` annotation): the pooled per-signal-day observations AND their deterministic first-trigger episode collapse come from the SAME `_event_study_members` builder (one membership rule; the collapse is a pure stored-data-only grouping). Computed by `research:compute_event_study` (+ episode-collapse helper) and `samples:_event_study_samples`; served by `GET /api/research/event-study` and `GET /api/research/samples` (the SAME endpoints — no new endpoint).
- **Disclosure values** `n` / `unique_symbols` / `episode_count`: derivations of that same observation set, served on the same event-study + samples payloads.
- **No NEW canonical value, no new endpoint, no new stored column.** `view="pooled"` is byte-identical to current output; never introduce a second compute/fetch path for any existing event-study figure — read the registered canonical source (`_event_study_members`).

## OUT OF SCOPE

- Any change to the J-32 all-history⇄as-of analysis-mode, the global as-of state, or `asof-provider.tsx` (the Episodes⇄Pooled toggle is orthogonal — a cohort/mode, not a date control).
- Any change to Factor Lab / Combination Lab compute or their samples cohorts (regression-only; their figures must read unchanged).
- Any new stored column, table, migration, or `config.yaml` numeric tunable (the win/loss `>0` boundary and episode-consecutiveness are structural rules, not magic numbers).
- Recomputing any forward return, MAE/MFE, regime, sector, factor, or membership — the episode path reads stored values verbatim only.
- J-22 / J-23 / J-24 (data-walled, non-halting — record blocked-NA, do not attempt fabrication).

## DEFINITION OF DONE

- [ ] J-63 passes via browser-qa-agent: `/research` Setup & Pattern Lab loads in **Episodes** mode by default with a visible Episodes⇄Pooled toggle and the n + unique-symbols + episodes disclosure; for a persisting subject (e.g. Risk-off-watchlist) pooled n > episode n and the episode-mode `N=` drill-down shows ONE row for a continuous run at its first-trigger date; flipping to Pooled shows figures byte-identical to the current published values; clicking an `N=` chip in each mode opens a new tab whose drill-down total equals the clicked N; `/methodology` explains Episode vs Pooled.
- [ ] Required-still-passing journeys remain green — J-29 (lab still renders all figures), J-51/J-64/J-65 (samples count-coherence + sort/filter + new-tab chips in both modes), J-25/J-26/J-27/J-30/J-31/J-32 (other labs unchanged), J-12/J-47 (glossary), J-18/J-06.
- [ ] No anti-goal violation introduced (one date control held; read-only; no fabricated data; no order path; no magic numbers).
- [ ] Full backend pytest suite passes with no regressions, INCLUDING a new test asserting `view="pooled"` output equals the prior pooled output (byte-identity guard) and a test asserting count-coherence (samples total == event-study `n`) in BOTH modes, plus an episode-collapse correctness test (a constructed consecutive run collapses to one first-trigger row; a gap in the stored run-date sequence splits episodes). Frontend gate is `tsc --noEmit` (ESLint is not installed — per lessons iter-1).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** J-63 (Episodes default + toggle + disclosure + first-trigger drill-down row + Pooled byte-identity + `N=` chip new-tab count-coherence + `/methodology` entries). Regression sweep of J-29, J-51, J-64, J-65, J-32 on `/research` and `/research/samples`.
- **Unit/integration:**
  - Episode-collapse determinism: consecutive stored run-dates for the same `(ticker, subject)` collapse to one first-trigger observation; a break in the stored run-date sequence yields separate episodes; episode rows carry the stored return/MAE/MFE/regime/sector verbatim.
  - **Byte-identity guard:** `compute_event_study(..., view="pooled")` and `GET /api/research/event-study?view=pooled` reproduce the existing (pre-change) output exactly for representative subjects/horizons.
  - Count-coherence in BOTH modes: the `/api/research/samples` drill-down total equals the event-study `n` for the same cohort params + `view`, and lists exactly that mode's rows.
  - Read-only assertion: `compute_event_study` and `_event_study_samples` issue only SELECTs in the new path — no INSERT/UPDATE/session.add/commit/run_scan/score_*/detect_*/forward_* call.
  - Disclosure values: `n` mode-dependent; `unique_symbols`/`episode_count` correct for a constructed multi-run subject.
- **Error cases:** `view` outside `{episodes, pooled}` → 422 on both endpoints; an empty/low-sample cohort → honest NA + n (never a fabricated row) in both modes; a subject with no forward-tested occurrences → honest empty state.

## NOTES

- **Lessons applied (read before coding):**
  - **iter-12 `_ADDITIVE_COLUMNS` trap:** prefer adding NO stored column — this iteration is designed to add none (episode collapse is an in-memory grouping of stored rows). If a column is somehow introduced, it MUST be registered in `apps/backend/app/db.py` `_ADDITIVE_COLUMNS` with a guard test AND a real (non-fresh) DB read exercised, because `create_all` never ALTERs an existing table and the live `apps/backend/data/trendora.db` would silently 500. Do not add one.
  - **iter-11 config-narrowing:** no new validated `config.yaml` section is planned. If glossary entries require a config addition, it is catalog data (not a validated screen), but still grep every config-narrowing site (`tests/`, `apps/backend/scripts/build_qa_fixture_db.py`, `apply_universe_to_config.py`) before declaring done.
  - **Full pytest is long (~46–59 min):** run it to completion in the dev turn foreground OR hand it to the pump as a background run; NEVER block the goal-evaluator on the in-flight suite — gate on the flushed terminal summary line.
  - **Count-coherence Ns drift between boots** (iter-7): assert samples-total == aggregate-n SAME-INSTANT against the live aggregate, never against a hardcoded N from an earlier capture.
  - **iter-5 nested-interactive hazard:** the new toggle and any clickable disclosure/`N=` chip must NOT nest a `<button>` inside another interactive element or around `TermInfo`/`InfoTooltip` (which renders its own `<button>`) — watch for the Next dev-overlay "error" badge in captures.
  - **md5 evidence hygiene** (iters 3/7/10): md5sum the evidence dir FIRST; require one distinct capture per claimed surface; validate filename-vs-content for any shared-byte capture before accepting a PASS.
- **Owed opportunistic check (cheap, if the QA session is already on the dashboard):** the J-44 indexes/regime chart **toggle off → reload → still-off** persistence cycle has been owed since iter-2 (lessons iter-6) — verify it opportunistically and capture it early in the browser session; it is not a gating leg for this iteration.
- **GOAL_ACHIEVED candidacy:** this is the final buildable Must-have. If J-63 lands green, all required-still-passing journeys hold, and coherence passes, flag for the evaluator that the next evaluation is a GOAL_ACHIEVED candidate — J-01..J-21, J-25..J-67 passing/already_passing; J-22/J-23/J-24 blocked-NA (data-walled, non-vetoing, confirmed verbatim by prior evaluators).
