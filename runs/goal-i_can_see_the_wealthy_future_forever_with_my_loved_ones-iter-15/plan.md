# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15 Execution Plan

Two journeys, one full-pipeline cycle, one pytest gate. Both live under the existing
**Data Manager → `/data`** IA home — no new page, route, nav, endpoint, stored column, model, or
migration. J-68 is a transaction-boundary fix in `_do_backfill`; J-69 re-scopes the existing Remove
panel + confirm modal to range-only. Canonical scan / forward-return outputs MUST stay byte-identical.

## What to Build
- **J-68 (backend) — fix the `'committed'`-session crash at the source in `_do_backfill`.** Root cause
  is already confirmed: `_persist` runs two inner commits on the SHARED orchestrating `session`
  (`scanner.persist_run_payload` commits at `scanner.py:205`, then
  `forward_testing.backfill_run_forward_returns` commits at `forward_testing.py:289`); on a later
  date's failure `_persist_isolated` calls `session.rollback()` on that already-committed session →
  the invalid-state crash on multi-month ranges. Re-own the per-date write transaction so no rollback
  ever fires on an already-committed session. Pick ONE sound mechanism (developer's discretion):
  a fresh write session per date (orchestrator owns the per-date boundary — simplest, recommended),
  per-worker write sessions with a single serialized writer, OR orchestrator-owned explicit boundaries
  that never `rollback()` a session the inner helpers committed. Writes stay serialized + transactional;
  the shared read-only `prefilled_bar_cache` for the compute fan-out is preserved.
- **J-68 (backend) — regression test driving the REAL `_do_backfill` orchestration** (the path
  `start_data_job` `backfill`/`both` uses, not a hand-rolled stand-in) over a multi-month range,
  OFFLINE, including the failure-isolation branch. This is the test that closes the gap that let J-67
  pass while the live job crashed. Run it for BOTH `backfill_workers == 1` (sequential) and the parallel
  pool, asserting byte-identical canonical outputs between them.
- **J-69 (backend) — range-only destructive removal scope.** Extend `_validate_remove_scope` so the
  destructive `POST /api/data/remove` (and its `/preview`) requires BOTH `start` and `end` and rejects a
  single-ended or empty date scope with an honest 4xx `detail`. Keep the existing empty/inverted/unknown
  guards and the committed-seed protection + seed-safe refusal/`reason` unchanged. (Leave
  `RemoveScope.symbols` in the schema for the internal pull-missing path — the J-69 UI flow simply sends
  `{start, end}` with no `symbols`. Do not break the symbol-scoped pull-missing path.)
- **J-69 (frontend) — Remove panel:** delete the symbols text input entirely; make both From/To
  mandatory (Preview/Remove button disabled until both are non-empty AND valid `yyyy-MM-dd`); `buildScope()`
  sends `{start, end}` only.
- **J-69 (frontend) — confirm modal:** counts-only body (removable bar count, affected-symbol count =
  `removable_symbol_count`, cascade snapshot count, restated range); remove the long `removable_symbols`
  list and the enumerated `not_removable_by_symbol` list (a summary protected-seed bar count is fine);
  ensure the Confirm button is always visible without scrolling (cap modal body height / make body scroll,
  keep the action footer outside the scroll region — the footer is already a separate `border-t` bar).

## Agents Required
- developer: yes — backend-data: J-68 transaction fix + regression test, J-69 `_validate_remove_scope`
  range-required validation + endpoint test; frontend-ux: J-69 Remove panel + confirm modal changes.

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` — J-68: re-own per-date write transaction in `_do_backfill`
  / `_persist` / `_persist_isolated` (no rollback on an already-committed session); J-69: extend
  `_validate_remove_scope` to require both `start` and `end` for the destructive/preview range flow.
- `apps/backend/app/api/data.py` — J-69: ensure the 4xx mapping for a single-ended/empty range scope is
  honest (`detail` carries the reason). No schema change beyond keeping `RemoveScope.symbols` for the
  internal path.
- `apps/frontend/app/data/page.tsx` — J-69: `RemoveDataPanel` (drop symbols input, both dates mandatory,
  drop `optional` on both `IsoDateInput`s, `buildScope` → `{start, end}` only) and `RemoveConfirmModal`
  (counts-only body, remove long lists, persistently visible Confirm).
- `apps/backend/tests/...` — J-68 regression test (real `_do_backfill` multi-month, failure isolation,
  create-once re-run, parallel==sequential byte-identical); J-69 endpoint test (single-ended/empty range
  rejected 4xx; range-only `{start, end}` accepted; seed protection + refusal unchanged; impact counts
  match the real computation). Place in the existing data-manager / data-api test modules.
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15-dev.md` — dev handoff.

**Confirm untouched (iter-12 trap does not apply):** `apps/backend/app/models.py` and `db.py`
`_ADDITIVE_COLUMNS` — this iteration adds NO new stored column. Do NOT change canonical scan /
forward-return / scoring math. Do NOT change the J-37 symbol-scoped pull-missing path.

## UI Evolution
- New user-facing capability: a multi-month / full-history backfill (or `both`) job started from `/data`
  now runs to completion instead of crashing with the `'committed'`-session DB error; removing imported
  data is a deliberate, range-scoped, accident-proof flow.
- New information displayed: no new canonical value. The confirm modal now foregrounds the
  affected-symbol count (already served as `removable_symbol_count` — re-displayed, not newly computed).
- New user actions: remove imported data by entering a From and To date (both required, no symbol entry);
  confirm a range-scoped removal from a counts-only dialog with an always-visible Confirm button.
- UI surface changes: `/data` Remove panel loses the symbols input and makes both dates mandatory;
  `/data` confirm modal becomes counts-only with a persistently visible Confirm button.
- Navigation changes: none.

## Visual Requirements
- Component patterns: reuse existing `Card`, `PanelTitle`, `IsoDateInput`, and the existing in-page modal
  (fixed overlay + `Card` with a `border-t` footer action row) — no new primitives. shadcn/dark
  analytical-workstation aesthetic, monospace/tabular numerics.
- Layout: Remove panel keeps the inline `flex-wrap items-end gap-3` row, now with two date fields + the
  Preview button only. Modal keeps header / body / footer; cap the body (e.g. `max-h` + `overflow-y-auto`)
  so the existing footer action row stays visible for any range.
- Key visual effects: keep the existing `border-neg` danger styling, `backdrop-blur` overlay, spinner on
  in-flight; no new effects.
- States to handle: button disabled until both dates valid (capture disabled-with-one-date AND
  enabled-with-both); counts-only confirm; refused (wholly-seed) path + reason unchanged; post-Confirm
  done banner + coverage/heatmap refresh (`onRemoved` already calls `refresh()` + `loadAvailability()` —
  keep it); preview/remove error states; empty/invalid date error.

## Key Test Scenarios
- **J-68 pytest (primary):** the real `_do_backfill` orchestration over a multi-month range completes
  with NO `'committed'`-state error; a forced single-date failure is isolated (that date `failed` with
  its error, others complete, terminal `partial`); a re-run of the same range creates 0 new snapshots and
  raises no UNIQUE error (create-once / J-41); outputs byte-identical to the `backfill_workers == 1`
  sequential run. Corroborate against persistent `scanner_runs` / `data_provider_runs` state, not a
  job-card screenshot alone.
- **J-69 pytest:** `POST /api/data/remove` and `/preview` reject a single-ended date scope (`start`
  without `end`, or `end` without `start`) and an empty scope with an honest 4xx; accept a valid
  range-only `{start, end}` (no `symbols`); committed-seed protection + seed-safe refusal/`reason`
  unchanged; impact counts equal the real computation.
- **J-69 browser (Chrome MCP, `/data`):** Remove panel has NO symbols input; Preview/Remove disabled with
  one date, enabled with both valid ISO dates; confirm modal shows counts only (removable bar count,
  affected-symbol count, cascade snapshot count, restated range) with the Confirm button visible without
  scrolling; after Confirm, coverage + availability heatmap reflect the removal. **md5sum the evidence dir
  first; one capture per claimed surface; no recycled/mislabeled images. Use the preview endpoint or a
  safe small user-added range — NEVER the destructive endpoint on committed-seed symbols (project memory:
  NVDA carries unrestorable user-added bars; do NOT remove a real symbol's bars in QA).**
- **Required-still-passing:** J-39, J-41, J-53, J-66, J-67 (scanner / forward-returns / immutability /
  no-lookahead / parallel-vs-sequential-equality suites — outputs identical) and J-61 (heatmap still reads
  `GET /api/data/availability` and refreshes after removal). J-08, J-13/J-18, J-42 unaffected.

## Operational notes
- Full backend pytest suite (~50–60 min) MUST be handed to the pump as a `nohup` background run; NEVER
  block the goal-evaluator on it — gate on the flushed terminal summary line (project memory: never make
  the pump wait for the suite before answering a CLAIMED dispatch). The dev turn runs the J-68/J-69
  targeted modules to completion in-foreground; the full suite goes to the pump.
- `tsc --noEmit` clean for the frontend. Do NOT add an `npm run lint` DoD line (ESLint not installed).
- Coherence: keep clean — no second compute/endpoint for any displayed value; remove dates stay action
  parameters (not a second date state); impact counts stay descriptive, single-sourced from the real
  backend computation.

## Scope / drift check
- No scope creep. J-70 (heatmap readability) and J-71 (as-of calendar keyboard stepping) are correctly
  deferred to iter-16 (lean) and excluded here.
- J-22 / J-23 / J-24 stay blocked-NA (data-walled, non-vetoing) — no work.
- The plan aligns with `docs/goal.md` (Capability 20 Data Manager reliability + seed-safe curation,
  anti-goals on immutability / no-lookahead / single date selector / no magic numbers / descriptive-only
  impact counts). No contradiction with the project goal.
