# Goal Iteration 13 — Per-date availability heatmap (J-61) + as-of calendar popover (J-62)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 13
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-61, J-62
- **Required-still-passing journeys:** J-13, J-18, J-43, J-50, J-42, J-36, J-17, J-37, J-08, J-06, J-15, J-40
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. ... The `?asof` URL query param (J-43) is the **serialization of that single global state** — written by and restored through the one global control — NOT a second date state; no page parses or holds its own. *(extends Single source of truth)*
  - **Coverage & missing-data are descriptive & honest.** The coverage figures, the per-symbol/per-universe-member table, and the insufficient-for-analysis diagnostic MUST be **read-only metadata derived from the stored bars + config** — they MUST NOT recompute or restate any canonical score, return, bucket, or setup. ... *(extends No fabricated data + No recompute in the read path)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. ...
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.

## GOAL

The user can see exactly which dates have data (a per-trading-date availability heatmap on `/data`) and pick the as-of date from a calendar popover that marks only the selectable snapshot dates — both read from the existing single sources, neither introducing a second date state.

## BACKGROUND

J-61 and J-62 are the last two non-data-walled UI Must-haves before the session can close on J-63; the iter-12 evaluator recommended exactly this pair at **full** depth (CONTINUE verdict, depth recommendation `full`). Both are *presentation / read-only upgrades of existing single-source state*: J-61 adds ONE read-only descriptive endpoint deriving per-date `symbols-with-bars` count + `snapshot-exists` from the **same** stored bars + stored runs the existing `data_manager.compute_coverage` reads (over the benchmark/SPY trading calendar at `data_manager.py:115`), rendered as a `/data` heatmap; J-62 swaps the global as-of switcher's flat `<select>`/`<option>` dropdown (`apps/frontend/components/asof-switcher.tsx`) for a calendar popover that renders the **same** `dates` array the `asof-provider` already derives once from `GET /api/runs` `run.asof_date` — no new date source, no new endpoint semantics, no second state. Full depth is warranted because J-61 introduces a new endpoint + new surfaces and J-62 touches the single-source as-of control (the no-second-date-state invariant plus the ux-regression / closure gates apply).

**Lessons applied (from `lessons.md` / project memory — surfaced for dev/reviewer/evaluator):**
- **Additive SQLModel column → `db.py` `_ADDITIVE_COLUMNS`.** Iter-12's QA-FAIL root cause was two new columns not registered in `db.py` `_ADDITIVE_COLUMNS`, 500ing the live persistent DB while fresh-DB tests stayed green. **This iteration should add NO stored column** (J-61 is a read-only derivation over existing tables; J-62 is frontend-only) — but if any stored column is introduced, it MUST be registered in `_ADDITIVE_COLUMNS` with a regression test, and the live DB migrated.
- **New required/typed config field → EVERY inline-config + narrowing site, incl. `scripts/build_qa_fixture_db.py`.** Any new config knob (e.g. heatmap legend buckets / poll knob) must be added to every inline test config dict and any fixture/QA-DB builder; grep the new section key across `apps/backend/tests`, don't trust a fixed list. (Iter-11's QA fixture builder not pruning `stock_industries` was the same class of bug.)
- **iter-5 nested-interactive hazard for new clickable UI.** Heatmap cells and calendar day cells are clickable — keep any inner button/link as a SIBLING of the cell's own click handler, never nested inside a parent `role="button"`/interactive element (the J-57/J-58/J-64 member-link + TermInfo sibling pattern); avoid the React dev-overlay "nested interactive" error.
- **React controlled `select`/inputs need the native setter for Chrome MCP.** If the calendar popover keeps any `<select>` or controlled input that browser-QA drives, the Chrome MCP `select`/value action won't fire React `onChange` on this frontend — use the native-setter + bubbling change event in eval, then assert live DOM.
- **Full pytest is ~46–59 min — hand it to the pump, never block the evaluator on it.** Dev runs targeted modules; the full suite goes to the pump. A subagent cannot finish it (10-min Bash cap + bg job dies on turn-end).
- **md5 evidence hygiene.** Each browser-QA capture must be a distinct, correctly-named file for the surface it claims (iter-12 had a few byte-duplicate / mislabeled crops). The heatmap-hover, sparse-vs-full-day, prefill, and calendar-popover captures must each be genuinely distinct.

## IN SCOPE

### Backend
- [ ] Add ONE read-only descriptive **per-date availability** derivation in `apps/backend/app/engine/data_manager.py` over the **already-stored** bars + runs, keyed to the benchmark (SPY) trading calendar (the same `_trading_days` / `compute_coverage` machinery at `data_manager.py:115/292`): for each calendar trading date, `{ date, symbols_with_bars, total_symbols, snapshot_exists }`. Descriptive metadata only — recompute NO canonical score / return / bucket / setup; never a second derivation of an existing coverage figure (read the same source `compute_coverage` reads).
- [ ] Expose it on ONE new read-only endpoint in the availability family under `GET /api/data/...` (e.g. `GET /api/data/availability`). No new write path. The `/api/data` overview and all existing data endpoints stay byte-unchanged.
- [ ] Honest empty-DB behavior: an empty / bars-less DB returns an empty-but-valid payload (no fabricated cells); a trading day with zero bars is represented as `symbols_with_bars=0`, not omitted-as-if-covered.
- [ ] Any legend bucketing / color thresholds (if computed server-side) come from `config.yaml` — no magic numbers in derivation code. (Pure presentation color mapping MAY live in the frontend; any numeric cutoff that classifies coverage density must be config-backed.)

### Frontend
- [ ] Render the J-61 **availability heatmap** on `/data` (`apps/frontend/app/data/page.tsx` + a new card/component): a trading-day calendar grid colored by `symbols_with_bars`, with a distinct marker on days that also have a snapshot, a legend, and exact figures on hover (date, `symbols_with_bars / total_symbols`, snapshot yes/no). A sparsely-covered day (e.g. 3-of-158) MUST be visually distinct from a fully-covered day; a zero-bar trading day is visibly empty. All dates render `yyyy-MM-dd` via the shared `apps/frontend/lib/dates.ts` formatter (J-42).
- [ ] Clicking a heatmap day (or selecting a range) **prefills the job form's Start/End date inputs** — these are **job parameters, NEVER the global as-of control** (J-18). No write to the as-of state.
- [ ] After a fetch/backfill/removal job completes, the heatmap re-reads (re-fetches the availability endpoint) and shows the new coverage. Renders gracefully on an empty DB.
- [ ] Replace the global as-of switcher presentation in `apps/frontend/components/asof-switcher.tsx` with a **calendar popover** (month grid): available snapshot dates (the existing `dates` array from `asof-provider`) are marked + selectable; other days are disabled; month navigation spans the stored history (reaches the oldest stored month); a **"Latest"** affordance returns to the latest view; keyboard operable (open / navigate months & days / select / dismiss). Textual dates render `yyyy-MM-dd` via the shared formatter (J-42).
- [ ] The calendar holds **NO second date state** — it is a renderer of the one global as-of control: selecting a date calls the existing `setAsOf` from `asof-provider` (unchanged), so the historical badge, `?asof` URL serialization (J-43), and href stamping (J-50) all stay byte-unchanged. An invalid `?asof` on load still degrades to latest (J-43). No dates available → disabled control.

### New user-facing capability
The user can (1) see at a glance, per trading day, how much data exists and whether a snapshot was computed — and click a day to prefill the next fetch/backfill — and (2) pick the as-of date from a calendar that visibly distinguishes selectable snapshot dates from unavailable days.

### New information displayed
A `/data` per-trading-date availability heatmap (symbols-with-bars density + snapshot marker, exact figures on hover, legend). A calendar month grid in the as-of popover marking selectable dates.

### New user actions
Hover a heatmap day (read exact figures); click a heatmap day / drag a range (prefill the job form dates); open the as-of calendar popover, navigate months, pick a selectable date, press "Latest", operate by keyboard.

### UI surface changes
- `/data` (Data Manager): a new availability-heatmap card/panel.
- Top-bar as-of switcher: dropdown → calendar popover (same single state).

### Product surface delta
The Data Manager stops giving the misleading single min→max "Price history" range impression — partial-coverage days are now honestly visible. The as-of control stops being a flat all-dates dropdown and becomes a date-aware calendar that shows exactly what is selectable. Both are presentation upgrades of state the app already owns.

### Blueprint conformance
No new top-level nav section and no new page. J-61 lands on the existing **Data Manager (`/data`)** home; J-62 is the cross-cutting top-bar as-of switcher (no page of its own). Both homes already exist in `blueprint.md` Information Architecture. The blueprint nav skeleton + Data Contract rows were stamped `[TARGET iter-13]` additively (J-61 availability row at the Data Contract; J-62 note on the "Resolved as-of date" row) — no nav-skeleton change, no re-approval required.

### Data-contract additions
- **Per-date availability counts** (per benchmark trading date: `symbols_with_bars` + `snapshot_exists`) — already registered in `blueprint.md` as the J-61 row: computed once as a read-only derivation over stored bars + stored runs by the existing `data_manager` coverage machinery; served by ONE new read-only endpoint in the availability family under `GET /api/data/...`. Descriptive metadata — no canonical value recomputed, never a second derivation. **This iteration stamps it `[TARGET iter-13]`.**
- **No new canonical value for J-62.** The calendar popover renders the SAME `dates` array (`run.asof_date` from `GET /api/runs`) the flat dropdown reads today — registered on the existing "Resolved as-of date" Data Contract row, annotated `[TARGET iter-13]`. No new date source, no new endpoint, no second date state.

## OUT OF SCOPE

- J-63 (event-study first-trigger episode mode) — the next iteration closes the session with it; do NOT build it here.
- Any new stored column or table (J-61 is read-only over existing tables; J-62 is frontend-only). If one becomes unavoidable, register it in `db.py` `_ADDITIVE_COLUMNS` + add a regression test + migrate the live DB (iter-12 lesson) — but prefer not to.
- Changing the as-of state machine, the `?asof` serialization, or the href-stamping (J-43/J-50) — the calendar must drive the EXISTING `setAsOf` only.
- Recomputing or restating any coverage figure, score, return, bucket, or setup in the availability endpoint.
- J-22 / J-23 / J-24 (data-walled, non-halting; honest NA) — no work, no fabrication.
- A date-picker dependency is permitted only if consistent with the stack (Next.js 15 / TS / Tailwind / shadcn) and it holds no internal date state of its own; a hand-rolled grid is equally acceptable. Do not add a heavy calendar library.

## DEFINITION OF DONE

- [ ] J-61 passes via browser-qa-agent: `/data` renders the availability heatmap with a legend; hover shows exact figures (date, symbols-with-bars / total, snapshot yes/no); a sparse day is visually distinct from a full day; clicking a day prefills the job-form date inputs (NOT the as-of control); after a job completes the heatmap re-reads; empty-DB renders gracefully with no fabricated cells.
- [ ] J-62 passes via browser-qa-agent: the as-of switcher opens a calendar popover; selectable snapshot dates are marked + selectable, others disabled; month navigation reaches the oldest stored month; "Latest" returns to latest; keyboard-operable; selecting a historical date re-points the app exactly as today (historical badge + `?asof` serialization + href stamping unchanged); an invalid `?asof` URL degrades to latest.
- [ ] Required-still-passing journeys remain green — especially **J-13/J-18/J-43/J-50** (one date control, `?asof` serialization, href stamping) and **J-36/J-17/J-37** (coverage / data-manager surfaces on `/data`).
- [ ] No anti-goal violation introduced — most critically **Exactly one date selector** (the calendar holds no second date state) and **Coverage & missing-data are descriptive & honest / No recompute in the read path** (the availability endpoint recomputes no canonical value).
- [ ] Unit/integration tests pass; no regressions. Full backend suite handed to the pump (do NOT block the evaluator on the ~46–59-min run); dev runs the targeted new modules + the data-manager / coverage / as-of-related modules locally.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13-dev.md`.
- [ ] All 6 UI visibility artifacts produced; coherence-auditor COHERENCE-PASS; closure CLOSURE-PASS.

## TESTING REQUIREMENTS

- **Browser (named journeys this iteration must verify, by ID):** J-61 (heatmap render + legend + hover figures + sparse-vs-full distinction + click-prefills-job-form + re-read after a job + empty-DB graceful), J-62 (calendar popover open + selectable-vs-disabled days + month nav to oldest month + "Latest" + keyboard operation + historical select re-points app exactly as today + invalid `?asof` → latest). Each capture must be a distinct, correctly-named file for the surface it claims (md5 hygiene).
- **Unit/integration (code paths that must have tests):**
  - The new availability derivation: per-date `symbols_with_bars` + `snapshot_exists` exactly match the stored bars + stored runs over the benchmark trading calendar; the figures are consistent with (never a second derivation of) `compute_coverage`; assert exact counts on a known fixture (a sparse day, a fully-covered day, a zero-bar trading day, a date with a snapshot vs without).
  - Empty/bars-less DB → empty-but-valid payload, no fabricated cells.
  - J-62 has no backend change to test; assert frontend behavior via browser-QA and (if a frontend test harness exists) that the calendar drives `setAsOf` and holds no local date state.
- **Error cases (invalid inputs that must be rejected / handled honestly):** a trading day with zero bars renders as empty/`0`, never as covered; an invalid `?asof` URL degrades to latest (J-43, must stay green); the availability endpoint on an empty DB returns a graceful empty payload (no 500, no fabricated cells); clicking a heatmap day writes ONLY the job-form date inputs, never the global as-of state (assert the as-of state is unchanged after a heatmap click).

## NOTES

- Drives directly from the iter-12 eval Next-Step Recommendation (CONTINUE, depth `full`, target J-61 + J-62 paired). After this iteration the only remaining failing Must-have is **J-63** (event-study episodes-default), which iter-14 should target to close the session.
- The single most load-bearing invariant: **J-62 must drive the existing single global as-of state, not introduce a parallel date state.** The calendar is a presentation of the one control (`setAsOf` in `asof-provider.tsx`); `?asof` (J-43) stays the serialization of that one state; the J-18/J-43/J-50 contracts must read byte-unchanged. The coherence-auditor will hard-fail a second date selector.
- J-61 must read the SAME source `compute_coverage` reads (stored bars + stored runs over the benchmark/SPY calendar) — never a second derivation of an existing coverage figure, and never a canonical-value recompute (anti-goal: Coverage & missing-data are descriptive & honest / No recompute in the read path).
- J-22/J-23/J-24 remain `unknown` blocked-NA (data-walled, non-vetoing) — no work this iteration.
