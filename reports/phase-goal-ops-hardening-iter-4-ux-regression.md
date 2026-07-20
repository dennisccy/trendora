# Phase goal-ops-hardening-iter-4 — UX Regression Review

**Date:** 2026-07-20

**Verdict:** UX-REGRESSION-WARN

---

## New Capability Discoverability

This iteration ships **no new capability** — both changes (B3, F1) are honesty/correctness fixes to an
already-shipped, always-visible surface: the global `HealthBadge` (top bar, every page, mounted once in
`app/layout.tsx`) and the `/data` job-progress heartbeat. Discoverability is therefore assessed as "does the
fixed behavior surface at the same zero-click ambient location the existing three states already use,"
not "can a user find a new button."

- **New `awaiting_snapshot` badge state ("Snapshot pending — …").** Verified directly against
  `apps/frontend/components/health-badge.tsx`: the new state is a 4th `else if` branch in the exact same
  `if/else if` chain that already renders `loading`/`ready`/`initializing`, in the exact same top-bar slot.
  Navigation path: **0 clicks** — it is ambient status, identical in reach to the pre-existing three states.
  No regression: the `loading`/`ready`/`initializing` branches are byte-identical to before; the final
  `else` (still `unavailable`) is unconditional, preserving the "never-scanned DB always shows unavailable"
  guarantee.
- **Recovery-pointer text ("Run a backfill or rebuild on Data Manager…").** Verified against
  `apps/frontend/components/sidebar.tsx`: "Data Manager" (`/data`) is a permanent, always-rendered sidebar
  entry, reachable in **1 click** from any page. The text is plain, non-linked prose (by design, per the
  frontend handoff — no new interactive element), but the destination it names is already a persistent
  1-click nav item every operator already uses for J-01/J-03/J-05. This satisfies the skill's "1 click =
  discoverable" bar.
- **Label clarity.** "Snapshot pending" reads as calm, plain-language, and is immediately followed by a full
  sentence naming the benchmark symbol, the pending date, and the concrete recovery action. No label
  confusion against the spec's own internal name (`awaiting_snapshot` ≈ "pending").
- **Heartbeat fix (F1).** No new surface — it corrects an existing, already-visible "updated Ns ago" line on
  `/data`'s Job progress panel, reached via the same 1-click Data Manager nav entry.

No hidden or undiscoverable capability found.

---

## Regression Risk

Assessed per the skill's method: intersect this iteration's touched files against every prior ops-hardening
iteration's shipped feature, using the actual `docs/handoffs/goal-ops-hardening-iter-{0..3}-*.md` files (this
session's own history) plus direct reads of the current source.

| Shared component | Prior feature it serves | This iteration's change | Risk | Evidence |
|---|---|---|---|---|
| `app/engine/readiness.py::compute_readiness` | J-04 (non-blocking boot, crash detection) — the app's single "is the backend OK" signal every page depends on | Servability check **rewritten** (whole-table `latest_data_date` → benchmark-scoped query); new state + `detail` field added | **High** (central logic rewrite on a global signal) | Regression guard (`latest_run is None` → unconditional `unavailable`) explicitly preserved and re-tested (`test_awaiting_snapshot_never_masks_true_unavailability`); browser-verified live (UT-05: never-scanned DB still shows true `unavailable`; UT-06: backend down still shows true `unavailable`). Risk realized-but-mitigated. |
| `apps/frontend/components/health-badge.tsx` | J-04 (badge is J-04's canonical UI home) | New 4th branch inserted between `initializing` and the final `else` | **Medium** (global, every-page component) | Direct read confirms the 3 pre-existing branches are unmodified; the change is purely additive. UT-J-04's full 6-step regression (fast-boot, initializing detail, crash presentation, logfile, interrupted-job resume) passed. |
| `app/engine/data_manager.py::_refresh_ingest_aggregates` / `_persist_per_date_coverage_snapshots` | J-05 (iter-2/iter-3's aggregates-at-ingest feature); indirectly J-01/J-03 (any backfill job uses `JobProgress`) | Added `prog.tick()` calls only — no change to what is computed, only when the heartbeat timestamp advances | **Medium** (dependency of, not central logic to, the prior feature) | Notably, this required **two attempts within this iteration** — attempt-1 ticked the market-phase loop but missed the per-date coverage loop (the review caught this as a CRITICAL finding and it was fixed in attempt-2, with a TDD red/green proof). The pipeline's own gate worked as designed; the shipped state has both loops covered. UT-07 (real ~953s rebuild) confirms the heartbeat advances through the full finalize tail live. |
| `apps/frontend/components/preflight-banner.tsx` | J-04 (GO/DEGRADED/NO-GO verdict strip, every page) | **Not touched** — confirmed by direct read: it consumes only `preflight.verdict`/`preflight.reasons`, with zero dependency on the new `awaiting_snapshot` literal | **Low** | `compute_preflight`'s servability sub-component non-breach for the new state is unit-tested (`test_preflight_servability_ok_for_awaiting_snapshot_state`) and separately confirmed live (TC-5). See Flags below for one nuance found while verifying this. |
| `apps/frontend/components/readiness-provider.tsx` | J-04 (shared context every readiness consumer reads) | **Not touched** per plan — but `health-badge.tsx`'s own internal detail-fetch `useEffect` dependency changed from mount-once (`[]`) to state-transition-triggered (`[state]`), a deliberate, disclosed, contained deviation | **Low** | Confined entirely inside `health-badge.tsx`; the shared provider itself has zero diff. Re-fetches only on infrequent state transitions, not on every poll tick. |
| `apps/frontend/app/data/page.tsx` (`JobProgressPanel`, `BackfillBreakdown`, `LastRunSummary`) | J-01/J-03 (iter-1's backfill breakdown/chunking); J-05 (iter-2's `aggregates_refreshed` line) | **Not touched this iteration** (confirmed: iter-4's dev/frontend handoffs list only `api.ts` + `health-badge.tsx` as frontend touch points) | **Low** | UT-09 (multi-day backfill) and UT-J-01/UT-J-03 (deterministic replay) all passed unedited. |

No component was found where a prior feature's actual behavior regressed. The two "High"/"Medium" risk
items are real risk (global, shared, load-bearing code), but every one is backed by both a targeted unit
regression test AND a passing live browser replay — not evidence-by-assertion alone.

---

## UI vs Backend Parity

Cross-checked `docs/handoffs/goal-ops-hardening-iter-4-dev.md` / `-frontend.md` (what was built) against
`reports/phase-goal-ops-hardening-iter-4-user-visible-changes.md` (what users can see), and independently
verified by reading the shipped component:

| Backend capability | UI exposure | Verified how |
|---|---|---|
| `compute_readiness`'s new `awaiting_snapshot` state | `HealthBadge`'s new 4th branch | Direct read of `health-badge.tsx`: `state === "awaiting_snapshot"` branch exists and renders |
| `compute_readiness`'s new `detail` field → `health.py`'s `readiness_detail` response key | Rendered inline after an em-dash in the pill | Direct read: `const recoveryDetail = detail.kind === "ok" ? detail.data.readiness_detail : null;` then rendered |
| `_refresh_ingest_aggregates`/`_persist_per_date_coverage_snapshots`'s new `tick()` calls | `/data`'s existing "updated Ns ago" heartbeat line, now accurate | UT-07 live-measured: heartbeat advances through the full ~953s finalize tail |

No orphaned backend-only field found. `user-visible-changes.md`'s own "Not Visible Yet: None" claim holds up
under independent code review.

**One disclosed, non-blocking residual gap** (already honestly surfaced in `user-visible-changes.md` and the
dev handoff, not newly discovered by this review): two single, one-time steps inside the finalize tail — the
current-stamp coverage recompute and the one-time bar-cache preload — still do not individually call
`tick()`. The developer's own reasoning (each is a single ~1–2s step, far under the stale-heartbeat threshold)
is sound and the live UT-07 measurement shows no stalled-heartbeat artifact in practice. Acceptable as
shipped; worth a footnote for whoever next touches this code path, not a blocking gap today.

---

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None.

### Potential Regressions
None confirmed. See Regression Risk table above — every touched shared component has a passing live
regression test specific to the prior feature it serves.

### Visual Consistency

- **New state's color reuse creates a same-color adjacency the other three states don't have.** Verified
  against `apps/frontend/components/ui/badge.tsx`: the new `awaiting_snapshot` pill uses `variant="accent"`
  (`border-accent bg-surface-2 text-accent`). But `HealthBadge` *already* renders a `provider: {name}` badge
  in that exact same `variant="accent"` immediately after the pill, in **every** state where health detail
  has loaded (not new to this iteration). In the `ready`/`initializing`/`unavailable` states, the pill's own
  color (green/amber/red) is visually distinct from the always-teal "provider" badge next to it. In the new
  `awaiting_snapshot` state, the pill and the adjacent "provider" badge are now the **same** teal/accent
  color — the one state, of the four, where color alone no longer separates "this is the status" from "this
  is just metadata." Position and text length still make the pill identifiable (it renders first, and carries
  a long explanatory sentence the provider badge does not), so this is a minor/cosmetic finding, not a
  functional one — but it does cut against the dev handoff's own stated intent that the new state read as
  "visually... distinct." No new color token was introduced (confirmed against `globals.css`: `--accent:
  #4fd1c5` pre-exists), so this is a reuse-adjacency nit, not a token violation.
- **No new page was added**, so cross-page style-consistency (the other half of this check) is trivially
  satisfied — the changed component is the same file rendering in the same slot on every page, not a new
  surface that could drift from established patterns.
- Dot-treatment (static vs. `animate-pulse`) is correctly differentiated from `initializing`'s pulsing dot, a
  deliberate and well-reasoned choice (calm-but-persistent vs. self-resolving), confirmed by direct code read.

### Evidence-artifact gap (found while verifying, reported for completeness)
`reports/phase-goal-ops-hardening-iter-4-ui-test-results.md`'s results table references **"(see Notes for
the one caveat)"** three times (rows UT-03, UT-04, UT-07), but the file, read in full, contains no `## Notes`
section at all — it ends at `## Environment`. This is exactly the class of QA-artifact-completeness gap
iter-3's own audit (T1) flagged as a recurring risk ("QA report overstated a clean pass and buried a real
browser FAIL"). I independently chased the most consequential dangling reference (UT-03's caveat) by opening
`reports/qa/goal-ops-hardening-iter-4-evidence/UT-03-awaiting-snapshot-badge.png` directly: it shows the
preflight banner in a loud **"DEGRADED — treat today's board with caution"** state (a "Live-vs-seed drift
detected (adjustment seam)" reason, listing a large number of symbols), not the calm "GO" banner TC-5's
narrative implies. Tracing this through the source (`apps/backend/app/engine/readiness.py:390`,
`apps/backend/app/engine/drift.py`, `apps/backend/tests/test_drift.py` — all headed "goal-mcp-loop iter-35,
J-21 / backlog B-304, OVERLAP CHECK ONLY") confirms this drift-detection reason is a **pre-existing, wholly
unrelated mechanism from a much earlier session**, untouched by this iteration, and orthogonal to the
servability component B3 actually fixes — `compute_preflight` aggregates multiple independent components, so
an unrelated drift finding can hold the overall verdict at `DEGRADED` while the servability sub-component
stays `ok` (exactly what TC-5 actually requires: not forced to NO-GO/DEGRADED **by this condition alone**).
I am confident this is not a B3/awaiting_snapshot regression. But the report itself does not say any of this
— a reader who takes the missing "Notes" pointer at face value has no way to reach that conclusion without
independently re-deriving it, as this review just did. Recommend the merge script that produces
`ui-test-results.md` be checked for why its Notes section is being dropped.

---

## Recommendation

No blocking action required — ship as-is. Two non-blocking follow-ups worth a look, neither urgent:

1. Consider giving the `awaiting_snapshot` pill a treatment that doesn't share its exact color with the
   adjacent "provider" badge (e.g., keep `accent` for the pill but move "provider" to `variant="default"`,
   or vice versa) so the new state's "visually distinct" goal holds even at a glance, not just on close
   reading. One-line change in `health-badge.tsx`; not spec-mandated (the spec left the exact accent choice
   to the developer).
2. Investigate why `reports/phase-goal-ops-hardening-iter-4-ui-test-results.md`'s merge step drops the
   `## Notes` section its own table cells reference — this is a reporting-pipeline gap, not a product defect,
   but it directly undercuts this session's own standing lesson (iter-3, T1) to "read the raw
   `ui-test-results.md` verdict directly" — that instruction only works if the raw file is complete.

Neither item blocks GOAL_ACHIEVED consideration for J-05; both are quality-of-evidence and polish items.
