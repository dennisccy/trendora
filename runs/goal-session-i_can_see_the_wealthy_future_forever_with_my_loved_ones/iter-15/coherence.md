# Iteration 15 — Coherence Audit

**Iteration:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15
**Date:** 2026-06-14
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration targets J-68 (multi-month backfill `'committed'`-session fix) and J-69 (range-only
accident-proof removal). Both are declared as carrying no new Data Contract value or endpoint. The
diff confirms this.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Import job control (backfill path) — `data_manager:*` → `POST /api/data/jobs*` | OK | `apps/backend/app/engine/data_manager.py` — `_do_backfill` now opens a per-date write session via `with Session(eng) as wsession`; no new computation, no new endpoint, canonical scan/forward-return outputs byte-identical by design (comment-documented and spec-required). The shared orchestrating `session` is used read-only in this stage. |
| Seed-safe remove preview+cascade — `data_manager:remove_data`/`preview_removal` → `POST /api/data/remove(/preview)` | OK | `apps/backend/app/api/data.py` lines 282–312: SAME two endpoints (`/remove/preview` and `/remove`) now pass `require_range=True`; no new endpoint, no new computation. Impact counts (`removable_bar_count`, `removable_symbol_count`, `cascade.snapshot_count`) remain single-sourced from `_build_removal_plan`; the frontend re-displays `removable_symbol_count` prominently as "affected symbols" — this is a re-format of an already-registered value (not a new computation). |
| Displayed date format (J-42) — `apps/frontend/lib/dates.ts` | OK | `apps/frontend/app/data/page.tsx`: the `fmtDate` calls on the range display in `RemoveConfirmModal` continue to use the shared `fmtDate` formatter (unchanged); no per-component format literal introduced. |
| Per-date availability counts (J-61) — `GET /api/data/availability` | OK | The J-69 post-confirm refresh calls the existing `loadAvailability()` (via the existing `onRemoved` callback, confirmed in diff at line ~2009 `onRemoved()`). No new derivation. |
| All other registered values | OK | No other registered canonical value is touched by this diff. |

No new displayed value is introduced. The affected-symbol count prominently displayed in the new
counts-only `RemoveConfirmModal` is the existing `removable_symbol_count` field already returned by
`preview_removal` — it is re-formatted for emphasis (moved from a subordinate text line to a large
numeral), not re-computed or re-fetched from a different source. This is a re-format, not a new
computation or non-canonical source: no violation.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/data` — `RemoveDataPanel` modification | OK | Existing route; `apps/frontend/components/sidebar.tsx:40` confirms `{ href: "/data", label: "Data Manager" }` — one click from the sidebar. No new route introduced. |
| `/data` — `RemoveConfirmModal` modification | OK | In-page modal on the same `/data` route — no new route. |
| J-68 backfill fix | OK | Backend-only change; no new UI surface. |

No new page, no new route, no nav-skeleton change. Both J-68 and J-69 land entirely on the existing
`/data` home as planned in the iteration spec and the blueprint IA row for Data Manager.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The new counts-only `RemoveConfirmModal` removes the long `not_removable_by_symbol` enumerated
  list. The "committed seed" summary bar-count (`not_removable_bar_count`) is still shown, but the
  per-symbol breakdown is gone. This is the intended J-69 behaviour (counts-only to keep the Confirm
  button always visible) and is not a coherence issue — the data is never fabricated and the
  canonical source is unchanged.
- The `_cleanup_orphan_run` helper in `apps/backend/app/engine/data_manager.py` (line ~1602) issues
  `delete()` statements for `ScannerRun` and its child rows on a failed per-date session. This is a
  best-effort compensating cleanup of a half-written snapshot on the SAME per-date write session (not
  the shared one), consistent with the immutability invariant: a snapshot that never fully committed
  is not a valid snapshot and leaving it would be an inconsistency. The immutability invariant
  (coherence invariant 3) applies to fully-written committed snapshots; cleaning up a partially-
  written orphan is correct by that rule and is not a violation.
