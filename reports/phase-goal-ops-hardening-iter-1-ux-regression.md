# Phase goal-ops-hardening-iter-1 — UX Regression Review

**Date:** 2026-07-19

**Verdict:** UX-REGRESSION-WARN

---

## New Capability Discoverability

All new capabilities land on the existing `/data` page, which already has a stable, unchanged sidebar entry ("Data Manager", `Database` icon, `apps/frontend/components/sidebar.tsx:44`). The sidebar is persistent global chrome, so every capability below is reachable in **1 click from anywhere in the app**, including the home page (`/`) — well within the 2-click budget, and no new nav entry was needed or added.

| New capability | Navigation path | Clicks from home | Label clarity | Visual feedback |
|---|---|---|---|---|
| Explicit-range backfill actually executes (cadence bypass) | `/data` → existing job form (unchanged: kind selector, start/end inputs, Start button) | 1 | Form unchanged, no new label to assess | Green "ok" badge + snapshot count (UT-02 historical row, UT-04 live) |
| >370-day backfill accepted, no size rejection | Same form, same page | 1 | N/A (absence of an error) | Job accepted, switches to running view (UT-12) |
| Chunk N/M progress badge on backfill | Job progress panel, automatic once a job spans >1 date-window | 1 | "chunk N/M" — same wording already used for fetch jobs, no new term introduced | `chunk-progress` badge advances live (UT-12/UT-13: "chunk 0/6" → "chunk 1/6") |
| Zero-work distinct badge + explanatory note | Job progress panel + Run history table, automatic when `snapshots_created===0` | 1 | "no new snapshots" badge + plain-English note box, zero raw field names anywhere on the page (UT-16 explicit scan: 0 matches for `dates_total`/`snapshots_created`/etc.) | Grey/neutral badge, visually distinct from green "ok" (confirmed via class names in UT-03/UT-04) |
| Persisted-history fallback on reload / fresh session | Job progress panel, automatic on page load when `runs.length>0` and no session job | 1 | Includes an explicit "from a previous session" qualifier (UT-06) so it can't be mistaken for a just-finished job | `LastRunSummary` renders status/message/breakdown; empty-session literal text never appears once history exists (UT-05: 0 matches across multiple reloads) |
| Breakdown counts (calendar/non-trading/already-snapshotted/error) | Inline text in both Job progress panel and Run history rows | 1 | Plain-English inline line, e.g. "28 calendar days · 0 already snapshotted · 9 non-trading"; absent entirely (not a fabricated "0 calendar days") for fetch/seed-load rows (UT-10) | Text renders next to existing snapshot count, no new column/layout |
| `/scanner-runs` gains new dates (consequential) | Own stable sidebar entry ("Scanner Runs") | 1 | Unchanged page/labels | New rows render with populated regime badge + stock table (UT-11), not empty/error |

No capability from `user-visible-changes.md` lacks a navigation path, and none requires more than the single click already needed to reach `/data` (or `/scanner-runs`) from the sidebar. The job submission form itself is explicitly unchanged (confirmed in both the plan and the dev/frontend handoffs), so no new user action needed a new entry point.

**Design system / visual consistency:** the new zero-work state reuses the existing `Badge` component and the existing neutral/grey `default` variant already established for `interrupted` (no new badge component, no new color token) — confirmed in the frontend handoff's "Visual/Design Compliance" section and consistent with this page's established pattern from prior iterations (iter-20's design-system-compliance approach on this same page, iter-33's token-reuse approach for the cross-cutting `PreflightBanner`). No arbitrary/inline hex values were introduced. No visual-inconsistency flag warranted on styling grounds.

---

## Regression Risk

Working-tree diff for this iteration (`git diff --stat`, 19 files) touches exactly: `apps/backend/app/engine/data_manager.py`, `config.py`, `api/data.py`, `build_qa_fixture_db.py`, 9 backend test files, `config.yaml`, and on the frontend only `apps/frontend/app/data/page.tsx` + `apps/frontend/lib/api.ts`. This was used to verify shared-component overlap directly rather than by inference.

| Shared component | Prior feature it serves | Origin | This iteration's touch | Risk | Verified how |
|---|---|---|---|---|---|
| `data_manager.py` / `data_provider_runs` table / `JobProgressPanel` / `RunHistoryPanel` (`/data`) | J-04's fast boot, phase-aware initializing badge, distinct crash presentation, interrupted-job-after-restart state (built across early mcp-loop iterations; last touched for unrelated Expand-removal/heatmap work in mcp-loop iter-20) | mcp-loop (pre-ops-hardening) | Direct, substantial (214 lines in `data_manager.py`; both panels restructured in `page.tsx`) | **High inherent risk** (same file/table/page) — but **directly reverified live**, not just inferred | Browser QA: UT-14 (interrupted badge, reproduced twice, survives a 3rd restart), UT-15 (all 4 readiness-badge boot states), UT-J-04 (full 6-step goal-mode journey) — **all PASS** |
| Sidebar (`sidebar.tsx`), app shell (`layout.tsx`), `HealthBadge`/`readiness-provider.tsx`, `PreflightBanner` (mcp-loop iter-33's cross-cutting board-integrity banner, mounted on every route incl. `/data`) | Global navigation; J-04's readiness signal; board-integrity gating (J-2x cluster) | mcp-loop iter-1 (nav), iter-33 (PreflightBanner) | **Zero** — none of these files appear in this iteration's diff | None | Confirmed via `git diff --stat`: 0 lines changed in any of these files |
| `error.tsx` / `global-error.tsx` (crash containment), `availability-heatmap.tsx` (legend/colors) | mcp-loop iter-19 (sector-null crash fix + error boundaries), iter-20 (heatmap legend rework) | mcp-loop | Zero — not in this iteration's diff | None | Confirmed via `git diff --stat` |
| `/scanner-runs` page code itself | Scanner Run detail view (regime badge, stock table), mcp-loop iter-19 (sector-null handling) | mcp-loop | Zero code change — only new underlying data (new snapshot dates) flows through it | None (consequential, not a code regression) | UT-11: new dates render correctly with populated regime badge + stock table, not empty/error |

No shared-component regression was found. The one component with legitimate, substantial code overlap (`data_manager.py`/`data_provider_runs`/the two `/data` panels) was the exact one the plan and phase spec flagged in advance as "required-still-passing, not a build target" — and it was independently re-verified live by the browser-qa-agent rather than assumed safe by inspection alone.

---

## UI vs Backend Parity

`implementation-summary.md` states plainly: **"Backend-Only Items: None. Every backend change in this phase has a corresponding visible change on the `/data` page."** Cross-checked against `user-visible-changes.md` and the ui-surface-map — this holds:

| Backend capability | Surfaced in UI? |
|---|---|
| Cadence bypass for explicit `backfill`/`both` | Yes — productive "ok" vs zero-work outcome difference is the entire visible signal |
| `max_range_days` removal | Yes — form now accepts a 412-day span without rejection |
| Date-window chunking | Yes — `chunk N/M` badge, previously fetch-only |
| `dates_total` redefinition + 4 new breakdown fields | Yes — inline breakdown text on both panels |
| Persisted run history on fresh load | Yes — `LastRunSummary` component |
| `rebuild`'s unchanged cadence-filtered target selection | N/A by design — no user journey exercises `rebuild`; explicitly out of scope this iteration |

No backend capability was found "complete" but left undescribed in the UI. The `rebuild`-kind breakdown-invariant limitation is self-disclosed (dev handoff, reviewer NOTE) and does not affect any journey this iteration targets — acceptable per the phase's explicit "rebuild unchanged" scoping, not a parity gap.

---

## Flags

### Hidden Capabilities
None found.

### Undiscoverable Capabilities
None found.

### Potential Regressions
- **None confirmed.** All shared-component risk was either (a) zero code overlap — nav, shell, readiness badge, preflight banner, error boundaries, heatmap legend, all confirmed untouched via `git diff --stat` — or (b) real code overlap (`data_manager.py`/`data_provider_runs`/`JobProgressPanel`/`RunHistoryPanel`) that was directly re-exercised live by browser QA (UT-14, UT-15, UT-J-04) and passed.
- **New-feature-meets-old-state inconsistency (not a regression of the prior feature's own behavior, but worth flagging here since it sits exactly at that intersection):** an interrupted `backfill`/`both`/`rebuild` run (the prior, unchanged `interrupted` status path) persists `calendar_days`/`non_trading_days`/`already_snapshotted` as literal `0` instead of `null` once combined with this iteration's new `BackfillBreakdown` display — so an interrupted 517-day job's Run History row reads "0 calendar days · 0 already snapshotted · 0 non-trading," visually indistinguishable from a genuine 0-day request. This directly contradicts this same iteration's own anti-fabrication contract (`BackfillBreakdown`'s doc comment: "never a fabricated '0'"; UT-10's explicit test of that principle for fetch/seed-load rows) and the "these numbers are guaranteed to add up correctly" claim in `implementation-summary.md`. Reproduced twice live by the browser-qa-agent (UT-14's "Additional observation"); does not fail any written test assertion (badge text/color/visibility are all correct), so it did not block QA, but it is a genuine, user-visible honesty gap in the new capability.

### Visual Consistency
- New states (zero-work badge, breakdown line, chunk badge, `LastRunSummary`) all reuse existing `Badge` variants and established color tokens — no new component, no arbitrary hex, consistent with this page's prior-iteration design-compliance pattern. No styling inconsistency found.
- The one substantive consistency gap is functional/data-integrity rather than stylistic (see above): the breakdown line's numbers can misrepresent an interrupted job's actual scope.
- **Related, lower-severity edge case** (reviewer finding, not yet independently browser-observed): `error_other` is derived from a capped 20-item failure-sample list (`len(prog.date_failures)`) rather than an unconditional counter, so a real run with >20 date failures would silently under-report `error_other` on screen. No current journey/test triggers >20 failures, so this has not yet been seen live, but it is the same root pattern as the interrupted-zero-fill issue above (an internal counter's edge case leaking into the "honest breakdown" UI promise) and is worth fixing alongside it.

---

## Recommendation

No blocking action required before this iteration closes: J-01 and J-03 both pass with direct, live browser evidence; J-04's required-still-passing sub-behaviors were independently re-verified live (not just inferred from code-overlap) and pass; no capability is hidden, undiscoverable, or mislabeled; no navigation or design-system regression was found.

For a near-term follow-up (does not need to reopen this iteration):
1. Change the interrupted/orphan-sweep path in `_do_backfill` to leave `calendar_days`/`non_trading_days`/`already_snapshotted`/`error_other` as `null` (matching the fetch/seed-load convention already correct elsewhere) instead of zero-filling them, so `BackfillBreakdown`'s existing "suppress when null" rendering naturally hides the line for an interrupted run instead of showing a fabricated "0 calendar days."
2. Pair that with the reviewer's own suggested fix — an unconditional error-failure counter (mirroring `omitted_total`) instead of `len(prog.date_failures)` — since both stem from the same root pattern and both affect the same on-screen breakdown line.

Neither item blocks this iteration's DEFINITION OF DONE or any Must-have journey; both are flagged here because they are user-visible and directly relevant to the anti-fabrication principle this same iteration otherwise successfully implements.
