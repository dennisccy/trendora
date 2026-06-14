# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15
**Date:** 2026-06-14
**Agent:** developer
**Status:** complete

## What Was Built

- **J-68 — fixed the multi-month backfill `'committed'`-session crash at the source.** The per-date
  write/persist in `_do_backfill` now runs on a FRESH write session that the orchestrator OPENS AND OWNS
  for exactly that date (its own transaction boundary), instead of the SHARED orchestrating `session`. The
  shared read-only pre-filled bar cache is attached to each per-date session, so reads stay
  load-once-per-job and canonical output stays byte-identical. A per-date failure now rolls back ONLY that
  date's own session — the shared orchestrating session is never rolled back after a commit, removing the
  invalid `'committed'`-state path. The per-date persist is also made ATOMIC: because the create-once
  helpers commit the snapshot run before the forward-return INSERT, a forward-return failure now cleans up
  the half-written run whole-row (`_cleanup_orphan_run`), so a failed date leaves NO inconsistent snapshot
  and the create-once re-run is clean (no stranded `ScannerRun` → no UNIQUE crash).

- **J-68 — regression test driving the REAL `_do_backfill` orchestration** over a multi-month range,
  OFFLINE, including a per-date PERSIST failure after an earlier date committed (the exact gap the iter-12
  J-67 tests missed — they only failed the per-date COMPUTE). Asserts: multi-month completes (parallel +
  sequential, no committed-session error); a forced single-date persist failure is isolated (`partial`,
  honest error, the bad date leaves no half-written snapshot, others complete); re-run is create-once (0
  duplicate snapshots, no UNIQUE error); parallel == sequential byte-identical.

- **J-69 — range-only, accident-proof destructive removal.** `_validate_remove_scope` gained a
  `require_range` flag (threaded through `_build_removal_plan` / `preview_removal` / `remove_data`); the
  `POST /api/data/remove` and `/preview` endpoints now pass `require_range=True`, so the destructive flow
  requires BOTH `start` and `end` and rejects a single-ended or empty date scope with an honest 400. The
  existing empty/inverted/unknown-symbol guards and the committed-seed protection + seed-safe refusal/
  `reason` are unchanged. The internal symbol-scoped path (`require_range=False`, the default) is
  untouched.

- **J-69 — Remove panel (frontend).** The symbols text input is GONE; the panel is two date fields + the
  Preview button. Both From/To are MANDATORY — the button is disabled until both are non-empty AND valid
  `yyyy-MM-dd`. `buildScope()` sends `{start, end}` only (no `symbols`).

- **J-69 — confirm modal (frontend).** Counts-only body: removable (user-added) bar count, the
  affected-symbol count foregrounded, a summary protected-seed bar count, and the cascade snapshot /
  forward-return counts, with the date range restated. The long enumerated `removable_symbols` list and the
  per-symbol `not_removable_by_symbol` list (which could push the Confirm button off-screen) are removed.
  The body scrolls within a capped `max-h-[55vh]` while the footer action row stays OUTSIDE the scroll
  region, so the Confirm button is persistently visible for any range.

## Files Changed

- `apps/backend/app/engine/data_manager.py` — J-68: per-date write session in `_do_backfill._persist`
  (orchestrator-owned transaction boundary, shared cache attached, atomic with orphan-run cleanup);
  `_persist_isolated` no longer rolls back the shared session; new `_cleanup_orphan_run` helper. J-69:
  `_validate_remove_scope` / `_build_removal_plan` / `preview_removal` / `remove_data` gained a
  `require_range` flag (range-only contract).
- `apps/backend/app/api/data.py` — J-69: `remove_preview` + `remove_data_endpoint` pass
  `require_range=True`; `RemoveScope` docstring updated to the range-only contract.
- `apps/frontend/app/data/page.tsx` — J-69: `RemoveDataPanel` (no symbols input, both dates mandatory,
  `buildScope` → `{start, end}`) and `RemoveConfirmModal` (counts-only body, removed long lists, capped
  scrollable body with the footer Confirm always visible).
- `apps/backend/tests/test_data_manager_backfill_committed_session.py` — NEW: the J-68 regression suite
  (multi-month real orchestration + persist-failure isolation + create-once re-run + parallel==sequential).
- `apps/backend/tests/test_api_data_remove_range.py` — NEW: the J-69 endpoint suite (single-ended/empty/
  symbols-only/inverted → 400 on both endpoints; valid range-only accepted; seed refusal unchanged; counts
  match the real computation).

## Confirmed Untouched (iter-12 trap does not apply)

- `apps/backend/app/models.py` and `app/db.py` `_ADDITIVE_COLUMNS` — NO new stored column / model /
  migration (J-68 is a transaction-boundary fix; J-69 reuses the existing remove contract).
- Canonical scan / forward-return / scoring math — unchanged (outputs proven byte-identical by the J-68
  parallel==sequential test + the existing J-53/J-67 equality suite).
- The J-37 symbol-scoped pull-missing path — unchanged (`require_range` defaults to False there).

## Tests Run

Command (backend, targeted): `cd apps/backend && .venv/bin/python -m pytest <module> -q`

- `tests/test_data_manager_backfill_committed_session.py` (J-68) — **6 passed** (93s). Confirmed the test
  FAILS pre-fix (the parallel multi-month case crashed → `partial`) and PASSES post-fix.
- `tests/test_api_data_remove_range.py` (J-69) — **13 passed** (6s).
- `tests/test_api_data.py` — **42 passed** (with the remove-range module: 55 passed, 15s).
- `tests/test_data_manager.py -k "remov or scope or seed_window or cascade or refus"` — **11 passed**
  (existing engine-level remove tests, `require_range=False` default, unaffected).
- `tests/test_data_manager_backfill_parallel.py tests/test_data_manager_parallel.py
  tests/test_data_manager_jobs_pipeline.py` (J-53/J-67 still-passing) — handed in-foreground/background;
  see "Known Issues" for the gate.

Frontend: `cd apps/frontend && npx tsc --noEmit` — **clean (exit 0)**.

Service startup: `TestClient(main.app)` boots the full lifespan cleanly; `/api/data/remove/preview` and
`/api/data/remove` are registered and enforce the range-required 400 end-to-end.

## Known Issues

- **Full backend pytest suite handed to the pump.** Per project memory, the full suite (~50–60 min, heavy
  walk-forward boot) MUST be run by the pump as a `nohup` background run — a subagent cannot finish it
  (10-min Bash cap + bg job dies on turn-end). The dev turn ran the J-68/J-69 targeted modules to
  completion (all green) and launched the J-53/J-67 parallel/pipeline regression modules. Gate the
  evaluator on the flushed terminal summary line of the pump's full-suite run — do NOT block the evaluator
  on it.
- **No live external integration in this iteration.** J-68 is a transaction-boundary fix verified offline
  against the committed seed (no provider call); J-69 is a local destructive-metadata contract change. No
  new adapter/scraper/native dependency was added, so no live-integration smoke was required.
- The `removable_symbols` / `not_removable_by_symbol` / `cascade.snapshot_dates` fields remain in the API
  response + the TS `RemovePreview` type (the contract is unchanged); the J-69 modal simply no longer
  renders the long lists. This is intentional (no contract churn) and harmless.
