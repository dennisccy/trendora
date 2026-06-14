# Goal Iteration 15 — Data Manager hardening: multi-month backfill 'committed'-session fix + range-scoped accident-proof removal

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 15
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-68, J-69
- **Required-still-passing journeys:** J-39 (seed-safe / cascade-consistent removal), J-41 (create-once / idempotent / concurrency-safe snapshots), J-53 (parallel multi-date backfill + per-stage timings), J-66 (honest fine-grained progress), J-67 (transactionally-sound parallel backfill — failure isolation, byte-identical outputs), J-17 (grow dataset by date / range), J-61 (per-date availability heatmap reads `GET /api/data/availability`), J-42 (ISO dates everywhere), J-08 (immutable scanner-run history), J-13/J-18 (single global as-of state — heatmap/remove dates are job parameters, never a second date control)
- **Anti-goal reminders:**
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. *(critical)*
  - **On-demand snapshots stay immutable & lookahead-free.** Creating a snapshot for a newly selected date is create-once: an existing snapshot MUST be read, never overwritten. *(critical)*
  - **Range backfill stays immutable & lookahead-free.** Snapshots created for a fetched or backfilled date range are create-once: an existing snapshot MUST be read, never overwritten.
  - **Coverage & missing-data are descriptive & honest.** Coverage figures and the per-symbol/per-universe-member table MUST be read-only metadata derived from stored bars + config — never recompute/restate a canonical score/return/bucket/setup. The removal impact counts are likewise descriptive, single-sourced from the real backend computation, never fabricated.
  - **No magic numbers.** Every threshold/edge/concurrency knob comes from `config.yaml` — no such literal in calculation code.
  - **Exactly one date selector.** The global as-of control drives every date-scoped page; import/remove dates are job/action parameters, never a second date state. *(critical)*

## GOAL

Make the Data Manager safe for the real reproduction it currently fails: a multi-month (and full-history) backfill/`both` job completes without the `This session is in 'committed' state` crash, and removing imported data is a deliberate, range-scoped, accident-proof flow (no symbols field, both dates mandatory, a counts-only confirm with a persistently visible Confirm button).

## BACKGROUND

The prior session reached GOAL_ACHIEVED at iter-14; `docs/goal.md` (commit `aefc120`) appends four new offline-buildable Must-haves J-68..J-71. This iteration takes the two that touch the backend Data Manager engine (`apps/backend/app/engine/data_manager.py`) and share the `/data` home, so they ride one full-pipeline cycle and one pytest gate:

- **J-68** hardens J-67. The evaluator marked J-67 passing in iter-12 on the offline parallel-vs-sequential equality + failure-isolation tests, but goal.md states the fix "did not hold for this orchestration path" — the live multi-month Data Manager job still crashes with the committed-session error. Root cause is confirmed in source: `_do_backfill`'s per-date `_persist` calls `scanner.persist_run_payload` (commits the session at `scanner.py:205`) then `forward_testing.backfill_run_forward_returns` (commits again at `forward_testing.py:289`) on the SHARED orchestrating `session`; the failure-isolation handler `_persist_isolated` then calls `session.rollback()` on a date failure. After an inner `commit()` has run, a later `rollback()`/further SQL on that same already-committed session is exactly the invalid `'committed'`-state path. The iter-12 tests passed because they did not drive the real `_do_backfill` orchestration over a multi-month range with the failure-isolation branch on a session that had already committed prior dates.

- **J-69** amends J-39. Removal currently exposes a free-text **symbols** input, the date fields are **optional**, and the confirm modal renders a per-symbol committed-seed list (and removable-symbols list) that can push the Confirm button off-screen. goal.md now wants removal scoped **purely by date range over all symbols**, with **both dates mandatory** (guarding against accidental delete-everything), and a **counts-only** confirm with a **persistently visible** Confirm button.

J-70 (heatmap readability/layout) and J-71 (as-of calendar keyboard stepping) are pure frontend polish and are deferred to iter-16 (lean) to keep this iteration tight.

**Lessons applied (from `lessons.md` / project memory):**
- iter-11 / iter-12: a full-depth backend iteration's pytest suite (~46–55 min) MUST be handed to the pump as a background (`nohup`) run; NEVER block the goal-evaluator on it. Gate the evaluator on the flushed terminal summary line.
- iter-12: a new column on an existing table must be registered in `db.py` `_ADDITIVE_COLUMNS`. **This iteration adds NO new stored column** (J-68 is a transaction-boundary fix, not a schema change; J-69 reuses the existing `POST /api/data/remove` contract) — so the trap does not apply, and reviewers should confirm `models.py`/`db.py` are untouched.
- iter-2: a dev-turn background pytest run does not survive the turn ending — run to completion in-foreground within the dev turn or explicitly hand to the pump.
- iter-3/iter-7/iter-10: browser-QA evidence has repeatedly degraded to byte-identical / blank / mislabeled captures — md5sum the evidence dir FIRST, one capture per claimed surface, and corroborate the J-68 backfill outcome against persistent backend state (`data_provider_runs`, `scanner_runs`) rather than trusting a job-card screenshot alone.
- iter-5: do not nest interactive elements (the Remove panel and modal must keep a single click target per control).

## IN SCOPE

### Backend
- [ ] **J-68 — fix the 'committed'-session crash at the source in `_do_backfill` orchestration (`apps/backend/app/engine/data_manager.py`).** No `Session` may be left in a committed/invalid state mid-orchestration. In particular the per-date persist MUST NOT `rollback()` a session whose two internal commits (`scanner.persist_run_payload` + `forward_testing.backfill_run_forward_returns`) have already committed. Choose ONE sound mechanism (developer's discretion, but it must keep SQLite writes serialized + transactional and outputs byte-identical to the sequential engine):
  - a fresh session per date for the write/persist step (orchestrator owns the per-date transaction boundary, so a failure rolls back only that date's own session), OR
  - per-worker write sessions with a single serialized writer, OR
  - orchestrator-owned explicit transaction boundaries that never call `rollback()` on a session the inner helpers have already committed.
  The fix must preserve: per-date failure isolation (a forced-failed date is recorded `failed` with its error while the other dates still complete), create-once idempotency (J-41 — re-running the same range fills only what is missing, no UNIQUE crash, nothing overwritten), honest `partial` terminal state when a date fails (J-66 progress honest throughout), and byte-identical canonical outputs vs the sequential path.
- [ ] **J-68 — committed regression test that reproduces the ACTUAL job-orchestration path.** Add a test that drives the same `_do_backfill` orchestration the UI `backfill`/`both` job uses (not a hand-rolled stand-in) over a multi-month range end-to-end, OFFLINE, including the failure-isolation branch — explicitly closing the gap that let J-67 pass while the live job crashed. Assert: (1) the multi-month range completes without the committed-session error; (2) a forced single-date failure is isolated (that date `failed` with its error, the others complete, terminal `partial`); (3) a re-run of the same range creates 0 new snapshots and raises no UNIQUE error (create-once); (4) outputs byte-identical to the sequential (`backfill_workers == 1`) engine.
- [ ] **J-69 — range-only removal scope semantics (`apps/backend/app/engine/data_manager.py` + `apps/backend/app/api/data.py`).** The destructive flow is scoped purely by `{start, end}` over ALL symbols (no `symbols`). Both `start` and `end` are REQUIRED for the destructive `POST /api/data/remove` (and its preview) when invoked from this flow; an empty or single-ended date scope is rejected explicitly with an honest 4xx `detail` (reuse/extend `_validate_remove_scope` — keep the existing empty/inverted/unknown-symbol guards). The committed-seed protection and the seed-safe refusal/`reason` (J-39) are UNCHANGED — only user-added bars in the range are deleted; dependent snapshots/forward-returns cascade as today. The impact counts (removable bar count, affected-symbol count, cascade snapshot count) remain single-sourced from the real backend computation — never fabricated. (The `RemoveScope` model's `symbols` field may remain in the schema for the internal pull-missing path, but the J-69 destructive UI flow MUST send `{start, end}` with no `symbols`.)

### Frontend
- [ ] **J-69 — Remove panel (`apps/frontend/app/data/page.tsx`, `RemoveDataPanel`).** Remove the **symbols** text input entirely from the panel. Keep the two ISO date inputs (`From`/`To`) but make BOTH **mandatory**: the `Preview removal` / `Remove` button stays disabled until both are non-empty AND valid `yyyy-MM-dd` (extend the existing `IsoDateInput` validity gating; drop the `optional` flag on both). `buildScope()` sends `{start, end}` only (no `symbols`). Dates render via the shared `lib/dates.ts` formatter (J-42).
- [ ] **J-69 — confirm modal (`RemoveConfirmModal`).** Render **counts only**: removable (user-added) bar count, affected-symbol count (`removable_symbol_count`), cascade-removed snapshot count, with the date range restated. Do NOT render the long `removable_symbols` list nor the per-symbol `not_removable_by_symbol` list in this confirm (a summary protected-seed bar count is acceptable; the long enumerated lists that push the button off-screen must go). The **Confirm** button must be persistently visible without scrolling for a large range (e.g. keep the counts block compact / cap modal body height with the action row outside the scroll region). The refused (wholly-seed) path and its explicit reason are unchanged.
- [ ] **J-69 — post-Confirm refresh.** After Confirm, coverage AND the per-date availability heatmap refresh to reflect the removal (the existing `onRemoved` already calls `refresh()` + `loadAvailability()` — keep it).

### New user-facing capability
A multi-month (and full-history) backfill or fetch+backfill job started from the Data Manager now runs to completion instead of crashing partway with a database session error. Removing imported data is now a deliberate, range-scoped action: there is no symbols field, both dates are required, and the confirm dialog shows a compact impact summary with the Confirm button always visible.

### New information displayed
No new canonical value. The confirm modal now shows an **affected-symbol count** prominently (already served as `removable_symbol_count` — re-displayed, not newly computed). All figures remain the existing read-only descriptive removal-preview metadata.

### New user actions
- Remove imported data by entering a From and To date (both required) — no symbol entry.
- Confirm a range-scoped removal from a counts-only dialog with an always-visible Confirm button.
- (Behaviorally) start a multi-month/full-history backfill that now completes rather than crashing.

### UI surface changes
- `/data` Remove-imported-data panel: the symbols input is gone; both date fields are mandatory.
- `/data` Confirm-data-removal modal: counts-only body, persistently visible Confirm button.

### Product surface delta
The Data Manager becomes trustworthy for the two operations a real operator runs at scale: a long-range backfill that completes, and a destructive removal that cannot be triggered accidentally and whose confirm you can always reach.

### Blueprint conformance
Both journeys live under the existing **Data Manager → `/data`** Information-Architecture home (no new page, no new route, no nav-skeleton change). J-68 is a backend orchestration fix (no UI surface beyond the existing job card). J-69 modifies the existing Remove panel + confirm modal on `/data`.

### Data-contract additions
None. J-68 is a transaction-boundary fix to the existing **Import job control** canonical row (`data_manager:*` → `POST /api/data/jobs*`, `GET /api/data`) — no new value, no new endpoint, no new stored column; canonical scan/forward-return outputs stay byte-identical. J-69 reuses the existing **seed-safe remove preview+cascade** contract (`data_manager:remove_data`/`preview` → `POST /api/data/remove(/preview)`) — the removal impact counts are already-registered descriptive metadata, re-scoped to range-only; the affected-symbol count is the existing `removable_symbol_count`. No second computation or second endpoint is introduced for any displayed value. Blueprint Data-Contract rows for "Import job control" and "Backend readiness" are amended in place (additive notes), not duplicated.

## OUT OF SCOPE

- J-70 (availability-heatmap readability/contrast/two-up layout/descending months) — deferred to iter-16.
- J-71 (as-of calendar keyboard ArrowLeft/ArrowRight stepping) — deferred to iter-16.
- Any new stored column, model, or migration (J-68 is a transaction-boundary fix; J-69 reuses the existing remove contract).
- Any change to the canonical scan / forward-return / scoring math (outputs MUST stay byte-identical).
- Any change to the symbol-scoped pull-missing path (J-37) that internally still uses `RemoveScope.symbols` semantics elsewhere — only the J-69 destructive UI flow is re-scoped to range-only.
- J-22/J-23/J-24 (data-walled, non-vetoing) — no work; they stay blocked-NA.

## DEFINITION OF DONE

- [ ] Target journeys J-68, J-69 pass per their goal.md acceptance (J-68 verified primarily by the offline regression test that drives the real `_do_backfill` orchestration over a multi-month range incl. the failure-isolation branch, corroborated against persistent `scanner_runs`/`data_provider_runs` state; J-69 verified via browser-qa on `/data` + a backend test that the destructive endpoint rejects a single-ended/empty date scope and accepts range-only).
- [ ] Required-still-passing journeys remain green — especially J-39, J-41, J-53, J-66, J-67 (run the scanner / forward-returns / immutability / no-lookahead / parallel-vs-sequential-equality suites; outputs identical) and J-61 (heatmap still reads `GET /api/data/availability` and refreshes after removal).
- [ ] No anti-goal violation introduced (no fabricated data, snapshots immutable, no lookahead, single date selector, no magic numbers, descriptive-only coverage/impact counts).
- [ ] No new stored column / model / migration; `models.py` and `db.py` `_ADDITIVE_COLUMNS` confirmed untouched.
- [ ] Full backend pytest suite green (handed to the pump as a `nohup` background run; gate on the flushed summary line — do NOT block the evaluator on it). Budget ~50–60 min.
- [ ] `tsc --noEmit` clean for the frontend (ESLint is not installed — do not add an `npm run lint` DoD line per the iter-1 lesson).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15-dev.md`.

## TESTING REQUIREMENTS

- **Browser (Chrome MCP):**
  - **J-69** on `/data`: the Remove panel has NO symbols input; the Remove/Preview button is disabled until BOTH From and To are valid ISO dates (capture disabled-with-one-date and enabled-with-both); the confirm modal renders counts only (removable bar count, affected-symbol count, cascade snapshot count, restated range) with the Confirm button visible without scrolling; after Confirm, coverage + the availability heatmap reflect the removal. (Use the **preview** endpoint or a safe small user-added range — never the destructive endpoint on committed-seed symbols; per project memory NVDA carries unrestorable user-added bars, so do NOT remove a real symbol's bars in QA.)
  - md5sum the evidence dir first; one capture per claimed surface; no recycled/mislabeled images.
- **Unit/integration (pytest):**
  - **J-68:** a test driving the real `_do_backfill` orchestration (the same path `start_data_job` `backfill`/`both` uses) over a multi-month range, OFFLINE, asserting: completes without the committed-session error; forced single-date failure is isolated (that date `failed` + error, others complete, terminal `partial`); re-run creates 0 new snapshots and no UNIQUE error (create-once); outputs byte-identical to the `backfill_workers == 1` sequential run.
  - **J-69:** `POST /api/data/remove` (and `/preview`) rejects a single-ended date scope (`start` without `end`, or `end` without `start`) and an empty scope with an honest 4xx; accepts a valid range-only `{start, end}` (no `symbols`); committed-seed protection + seed-safe refusal/`reason` unchanged; impact counts match the real computation.
  - Re-run the J-53/J-67 parallel-vs-sequential equality suite + the J-41 create-once/idempotency/concurrency tests + the immutability + no-lookahead suites — green, outputs identical.
- **Error cases:** single-ended date range on removal → rejected 4xx; empty removal scope → rejected 4xx; a forced per-date backfill failure → isolated `failed` + honest `partial` (never a silent partial, never a fabricated snapshot for the failed date, never a committed-session crash).

## NOTES

- **Root cause is identified (do not re-discover from scratch):** `scanner.persist_run_payload` commits at `scanner.py:205` and `forward_testing.backfill_run_forward_returns` commits at `forward_testing.py:289`, both on the shared orchestrating `session` inside `_do_backfill._persist`; `_persist_isolated` then calls `session.rollback()` on a later date's failure → the `'committed'`-state crash on multi-month ranges. Fix the transaction ownership at the source per the IN SCOPE mechanism options.
- **Why full depth:** backend transaction/session-model change in the highest-risk Data Manager orchestration path + a destructive-removal contract change; both demand the full 11-step pipeline and the full pytest gate. (The prior evaluator's standing recommendation for a resumed-in-place extension was also `full`.)
- **Operational (pump):** hand the full suite to the pump via `nohup bash -c '...' &` (project memory: harness kills long `run_in_background` wrappers after ~3h; the detached engine survives but a plain bg loop dies). Never make the goal-evaluator wait on the in-flight suite — answer the dispatch on the flushed summary line.
- **Coherence:** last iteration was COHERENCE-PASS, so no consolidation pass is owed. Keep this iteration coherence-clean: no second compute/endpoint for any displayed value, no second date state (remove dates are action parameters), descriptive-only impact counts.
- **Carried opportunistic debt (non-blocking):** the J-44 dashboard toggle off→reload→still-off cycle has been owed since iter-2 on provably untouched code; if a browser session is already open on `/`, grab one belt-and-braces capture, but it does not gate this iteration.
- Next iteration (iter-16, lean): J-70 (heatmap day-number contrast across buckets 0–5, descending month order, two-up-per-row layout) + J-71 (as-of calendar `onKeyDown` ArrowLeft/ArrowRight stepping among snapshot dates, bounded, driving the single global as-of, no global window listener) — both pure frontend on `availability-heatmap.tsx` / `asof-calendar.tsx`.
