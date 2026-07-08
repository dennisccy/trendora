# goal-mcp-loop-iter-20 Execution Plan

Target journey: **J-13** (Data Manager coherence with the 548 pool + unambiguous availability
legend). Depth: full. No `## Evidence Claim` — pure UX/correctness/navigation change; the
post-decompose gate passes automatically. Verified directly against the current codebase (not
just the spec) — line references below were re-checked and are accurate as of this writing.

## What to Build

- Point the generic Fetch job's fresh-fetch symbol-set branch at the full committed 548-pool ∪
  context union (`price_load_symbols`), not just the ~122-162 context set (`all_seed_symbols`) —
  J-13 step 1. Byte-identical `compute_availability` output; no other job-kind branch touched.
- Remove the "Expand universe" job-kind option and all its now-dead supporting frontend code from
  `/data`, leaving fetch / backfill / both / gap-pull / rebuild untouched and working.
- Conscious, honestly-worded choice on market caps: accept committed/static caps now that Expand
  (their only on-demand refresh) is gone from the UI; no copy may imply caps are still
  on-demand-refreshable. No new refresh path — that is explicitly out of scope.
- Re-encode the per-date availability heatmap's legend so "price-data completeness" (cell fill)
  and "scored-snapshot exists" (indicator) read as two unmistakably separate, non-colliding
  signals: two labeled legend groups, a re-designed density color ramp (top bucket no longer
  amber), a non-green snapshot indicator, and clarified caption/tooltip/header copy naming the
  Fetch→fills / Backfill→scores workflow.
- **No action needed on `blueprint.md`** — the additive iter-20 clarification paragraph the spec
  calls for is already recorded (confirmed present at
  `runs/goal-session-mcp-loop/state/blueprint.md` line 217, written by the decomposer). Do not
  duplicate it.

## Agents Required

- backend-data: yes -- the one-line fetch-scope wiring in `data_manager._run_job` plus the import
  it needs, AND (important, see Risks) fixing the existing tests that hardcode the old symbol
  count/universe as the fetch job's expectation.
- frontend-ux: yes -- remove the Expand option + ~10 dead-code sites in `app/data/page.tsx`;
  re-encode `components/availability-heatmap.tsx`'s legend/colors/copy; adjust `globals.css`
  (+ `tailwind.config.ts` only if a new token name is introduced).

Frontend Present: yes

## Files to Create/Modify

Backend:
- `apps/backend/app/engine/data_manager.py` -- in `_run_job`'s fresh-fetch branch (the `else:` at
  line 2960, `symbols = all_seed_symbols(cfg)`) → `symbols = price_load_symbols(cfg, seed_dir)`.
  Add `price_load_symbols` to the existing `from app.seed_loader import all_seed_symbols` line
  (line 76 — currently imports only `all_seed_symbols`). Do NOT touch the `is_expand` branch
  (lines 2955-2956, already `read_pool(seed_dir)`) or the `symbols_override` branch (2957-2958).
- `apps/backend/tests/test_data_manager.py` -- fix `test_fetch_forced_failure_writes_no_bars_or_snapshots`
  (line 477: `assert summary["symbols_total"] == len(all_seed_symbols(cfg))` on a plain `"fetch"`
  job — will fail post-change) and double-check `test_chunked_fetch_pauses_resumable_then_resumes_idempotently`
  (line 1020: builds `chunk0` from `all_seed_symbols(cfg)[:batch]` — likely still valid since
  `price_load_symbols` is context-prefixed and `batch` ≪ context length, but verify).
- `apps/backend/tests/test_data_manager_jobs_pipeline.py` -- fix `test_symbols_counter_distinct_across_multi_window_plan`
  (lines 225/231: `n_symbols = len(all_seed_symbols(cfg))` asserted as the fetch job's total) and
  `test_covered_range_rerun_zero_provider_calls` / `test_partially_covered_window_still_fetches`
  (lines 313, 354: pre-store bars only for `all_seed_symbols(cfg)` and assert the range is
  "fully/partially covered" against that universe).
- New backend test coverage (extend `test_data_manager.py` or `test_seed_loader_pool.py`) --
  asserts the generic Fetch job's symbol set ⊇ the committed 548 pool (count + membership) AND
  retains every context symbol, per the DoD; plus a `compute_availability` byte-identical-output
  assertion (fixed small DB, same fields/values before vs after) for anti-goal #3.

Frontend:
- `apps/frontend/app/data/page.tsx` (3321 lines) -- remove: `isExpandKind` (:240) and its use in
  `isFetchKind` (:242), `sourceIneligibleForExpand` (:246), the `handleStart` guard (:386-391),
  the `<option value="expand">` (:2122), the `JobForm` `isExpandKind`/`sourceIneligibleForExpand`
  props+types+disabled-wiring (:493-494, :2047-2048, :2068-2069, :2087), the source-eligibility
  suffix + amber alert (:2137, :2179-2189), the panel title's "/ expand job" (:2091) and the
  Expand sentence in the form-copy paragraph (:2213-2219), the `isExpand` flag (:2396) — keep
  `showFetch = job.kind === "fetch" || job.kind === "both"` (drop only the `isExpand` disjunct at
  :2399, not the whole line), the `{isExpand ? <ExpandScreenResult/> : null}` call (:2515), and
  the `ExpandScreenResult` function (:2541 onward, to its closing brace). Leave fetch / backfill /
  both / gap-pull / rebuild controls untouched. Run `npx tsc --noEmit` after — zero dangling refs.
- `apps/frontend/components/availability-heatmap.tsx` (344 lines) -- split the single legend row
  (:232-249) into two labeled groups ("Price data — cell fill" / "Scored snapshot — indicator");
  update the header blurb (:196-201), the per-cell `title`/`aria-label` (:306-307), and the
  caption (:334-339) to name the Fetch→fills / Backfill→scores workflow; the snapshot ring class
  (:321, currently `ring-2 ring-pos`) needs a new non-green token.
- `apps/frontend/app/globals.css` -- `--heat-0..5` (currently slate→blue→cyan→teal-green→green→amber,
  lines 25-30) become a monotonic single-hue ramp whose top bucket is not amber; `--heat-text-0..5`
  (lines 33-38) re-checked for contrast against the new fills; a token for the snapshot indicator
  that is not green and doesn't collide with any new density-bucket hue (new var or a repurposed
  existing one, e.g. `--warn`/`--accent` if not already overloaded with a conflicting meaning on
  this page).
- `apps/frontend/tailwind.config.ts` -- only if a new token NAME is introduced beyond the existing
  registered `heat-0..5`/`heat-text-0..5` families (lines 29-42 already map these from CSS vars —
  a same-named token needs only a new hex in `globals.css`, no config change).
- `docs/handoffs/goal-mcp-loop-iter-20-dev.md` -- dev handoff (required by DoD).

## UI Evolution

- New user-facing capability: none added; the "Expand universe" job kind is REMOVED from the
  picker. The heatmap's legend/colors/copy become clearer for the same underlying data.
- New information displayed: none — the same `symbols_with_bars` / `total_symbols` /
  `snapshot_exists` values, re-encoded for clarity; caption/tooltip copy is new text over old data.
- New user actions: none added; one action REMOVED (Expand). Fetch / backfill / both / gap-pull /
  rebuild unchanged.
- UI surface changes: `/data` only — job-kind picker loses one option (and its eligibility
  alert); availability heatmap legend/ramp/indicator/caption/tooltip re-encoded. No new page.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `Card`/`Select`/`Badge` components already on `/data`;
  the legend re-encode stays inside the existing `AvailabilityHeatmap` card, restructuring its
  legend `<div>` into two labeled sub-groups — no new component type.
- Layout: unchanged — same card position, same page structure, no new panel.
- Key visual effects: none new; this is a color-token + copy + option-removal change, not a new
  visual treatment. Follow the existing dark analytical-workstation palette — `globals.css` CSS
  vars are the only place hex lives (project convention, stated in the file's own header comment);
  no inline hex in components.
- States to handle: no new loading/empty/error states; the heatmap's existing loading/error/empty
  states (:204-227) are unaffected and must keep working unmodified after the legend/color edit.
- Color-design note: goal.md explicitly directs a "monotonic single-hue scale" for the density
  ramp — this reverses the PRIOR iteration's J-74 multi-hue rework, whose own docstring explains
  it replaced "the old single-hue teal-opacity ramp where buckets 1–3 were near-identical." That
  is a real prior defect this change must not reintroduce: pick one hue but vary
  lightness/saturation enough across all 6 steps that they stay clearly distinguishable, not just
  "not amber." The snapshot ring must also read as unambiguous against every one of the new fills,
  not merely "non-green in isolation." If unsure how to keep 6 single-hue steps perceptually
  distinct, consult the `dataviz` skill's sequential-palette method before picking hex values.

## Testing Strategy

**Unit/integration (backend)**
- New/updated coverage: the Fetch job's target symbol set is a superset of the committed 548 pool
  (count + membership) and still includes every context symbol — reuse
  `test_seed_loader_pool.py`'s pattern (temp `seed_dir` + its `_write_pool` helper) for a fast,
  controlled assertion, plus one check against the real committed seed for actual pool size.
- A `compute_availability` byte-identical-output test (fixed small DB, same fields/values before
  vs after the wiring change) — enforces anti-goal #3 mechanically, not just by inspection.
- Fix the tests identified above that hardcode `all_seed_symbols(cfg)` as the fetch job's expected
  symbol universe. None of them pass an explicit `seed_dir` to `run_data_job` (confirmed: its
  signature defaults `seed_dir` to the real committed `DEFAULT_SEED_DIR` when omitted), so
  post-change they will silently start exercising the real ~588-name pool inside what were meant
  to be small, fast, controlled unit tests unless fixed. Prefer passing an explicit temp `seed_dir`
  (empty/small pool) to keep them fast/deterministic, and update their expected-count math to
  `price_load_symbols(cfg, seed_dir)`.
- Run: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py
  tests/test_data_manager_jobs_pipeline.py tests/test_seed_loader_pool.py -v`. Do NOT run the
  full suite (project convention: the full pytest run is ~10-11h on the 30-year basis and
  fork-locks the box — reviewer/QA scope this down to the touched files, same as iter-19).

**Unit (frontend)**
- This project has NO component/DOM test framework installed (checked `package.json` — no
  jest/RTL/vitest; only plain `node lib/*.test.ts` pure-function tests, and even that convention
  currently fails in-sandbox per the iter-19 handoff's noted Node/TS-stripping gap, worked around
  there via a local tsc-compile-then-node step). Do NOT introduce a new test framework for this
  presentation-only iteration — that would be scope creep.
- Instead: (a) `npx tsc --noEmit` must be clean after the Expand removal; (b) if the legend/token
  logic is factored into a small pure function or constant (e.g., "do the two legend-group token
  sets overlap," "is the snapshot token distinct from every bucket token"), it can follow the
  existing `lib/*.test.ts` convention; (c) actual rendered-DOM verification (two-group legend,
  non-amber top bucket, non-green snapshot indicator, hover distinguishing a no-snapshot day from
  a snapshot day) is carried by the browser lane below, not a new unit-test framework.

**Browser (canonical browser-qa-agent lane — Frontend Present: yes triggers Chrome MCP checks)**
- J-13 on `/data`: (1) job-kind picker has no "Expand universe" option; fetch/backfill still start
  without error. (2) legend shows two labeled groups; computed style confirms the top density
  bucket is not the old amber hex and the snapshot indicator is not green. (3) hover a date with
  bars-but-no-snapshot vs a date with a snapshot — tooltip/legend difference is obvious and names
  the Fetch→fills / Backfill→scores workflow.
- Regression replay (required-still-passing): J-01 (`/stocks` Sector sort — the iter-18 crash
  driver, highest-value smoke), J-03 (honest "Not yet proven"), J-05 (`/evidence` ledger renders),
  J-10 (`/stocks/{ticker}` deep-history chart), J-12 (broad point-in-time universe on
  `/methodology` + `/stocks`).
- Keep BOTH services in prod mode for the whole run (`start-backend.sh`/`start-frontend.sh`,
  never `dev.sh`) — confirm the backend stays up (the iter-19 `/api/data` OOM fix should hold).
- Screenshot hygiene (recurring lesson, restated in this iteration's spec): scroll the legend and
  both hovered cells into frame before capture; prefer full-page or element-clip captures (a
  scrolled-viewport capture has previously yielded ~5855-byte blank frames); `md5sum` evidence
  PNGs so one reused capture is not relabeled across the three J-13 assertions.

## Risks and Mitigations

- **Existing backend tests hardcode the OLD (context-only) symbol count/universe as the fetch
  job's expectation, and will break the moment the fresh-fetch branch is repointed at
  `price_load_symbols`.** Confirmed by direct inspection (see Files to Modify above) —
  `test_fetch_forced_failure_writes_no_bars_or_snapshots` and
  `test_symbols_counter_distinct_across_multi_window_plan` assert an exact `symbols_total` equal
  to `len(all_seed_symbols(cfg))` on a plain `"fetch"` job; the two "covered range" tests pre-store
  bars only for that same smaller universe. Mitigation: fix these in the SAME commit as the wiring
  change — do not let this surface as a surprise reviewer/QA finding. This is the single biggest
  time-sink risk in an otherwise small change; flagging it now should save a full retry cycle.
- **Reversing the J-74 multi-hue ramp back to a single hue risks recreating the exact defect J-74
  was built to fix** (near-identical neighboring buckets). This is goal.md's explicit, deliberate
  direction, not spec drift — but the developer must verify perceptual distinctness across all 6
  steps before calling it done, not just confirm "no longer amber."
- **Dense removal surface in one 3300-line file with ~14 distinct sites** — a missed reference
  fails `tsc --noEmit` (self-catching), but a missed behavioral wire-up would not (e.g., if
  `showFetch`'s whole line were deleted instead of just its `isExpand` disjunct, fetch/both would
  silently stop showing their progress bar). Mitigation: re-verify `showFetch` and `JobForm`'s
  `disabled` expression still read correctly with only the `isExpand`-specific parts removed.
- **Market-cap honesty framing** — removing Expand also removes the only on-demand market-cap
  refresh path; the spec requires a conscious, honestly-worded choice (accept static/committed
  caps), not silent removal. Mitigation: grep `/data` copy for any remaining claim that caps are
  still on-demand-refreshable and correct it; do not build a new refresh path (explicitly deferred).
- **Byte-identical availability data is a hard constraint (anti-goal #3, explicit DoD line)** —
  `compute_availability` and `GET /api/data/availability` must not change. Mitigation: a git diff
  on those two functions should show zero changes; the new backend byte-identical test is the
  enforcement mechanism, not just a visual check.
- **Scope-creep guard**: do not rip out the backend `kind:"expand"` handling, `get_market_caps`,
  or `scripts/screen_universe.py` (kept as the offline escape hatch per spec); do not touch
  `compute_availability`'s semantics or the `/stocks`/`/methodology` universe surfaces; do not fold
  a fresh market-cap action into this iteration; do not attempt J-14 (index/macro context) or
  J-15/J-16 (fast-platform perf budgets) — those are separate, already-sequenced later iterations.

## Key Test Scenarios

- A generic Fetch job's `symbols_total` counts ⊇ 548 committed-pool names, retains every context
  symbol, and the covered-range / multi-window / resume mechanics keep working at the new scale.
- `compute_availability`'s `symbols_with_bars` / `total_symbols` / `snapshot_exists` output is
  byte-identical before vs after the wiring change.
- `/data`'s job-kind `<select>` has exactly 3 options (backfill / fetch / both) — no "expand";
  starting a fetch or backfill from the form still works end-to-end.
- The availability legend DOM shows two labeled groups; the top density bucket's computed
  background color is not the old amber hex, and the snapshot indicator's computed color is not
  green and is distinct from every density bucket's own color.
- Hovering a "bars-but-no-snapshot" day vs a "has-snapshot" day produces a visibly and textually
  distinguishable tooltip/legend state that names the Fetch→fills / Backfill→scores workflow.
- J-01 / J-03 / J-05 / J-10 / J-12 all still pass (regression replay, deterministic).
- `tsc --noEmit` is clean; no `isExpandKind` / `sourceIneligibleForExpand` / `ExpandScreenResult` /
  `isExpand` symbol remains anywhere in `page.tsx`.
