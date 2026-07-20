# Phase goal-ops-hardening-iter-2 — UX Regression Review

**Date:** 2026-07-20

**Verdict:** UX-REGRESSION-WARN

---

## New Capability Discoverability

This iteration's only new UI element lands on the existing `/data` page, which already has a stable, unchanged sidebar entry ("Data Manager", `Database` icon, confirmed at `apps/frontend/components/sidebar.tsx:44` — unchanged this iteration, verified directly). Every capability below is reachable in **1 click from anywhere in the app** (well within the 2-click budget) and required no new nav entry.

| New capability | Navigation path | Clicks from home | Label clarity | Visual feedback |
|---|---|---|---|---|
| "Refreshed: …" line (which downstream aggregates a completed run's finalize hook kept fresh) | `/data` → Job progress panel (live), Last-run summary card (persisted fallback), Run history table row — all three render the identical line automatically, no user action needed to reveal it | 1 (0 extra — it's already visible on the page you land on) | Plain English, humanized via `.replace(/_/g, " ")` — "market phase", "membership timeline", "research hot keys", never a raw slug (confirmed at `apps/frontend/app/data/page.tsx:2551`; QA UT-08 independently confirmed no underscores render) | Text appears the moment a job reaches a terminal state (UT-02: live + post-reload byte-identical) |
| Instant `/data` coverage load after cold restart (coverage-from-storage) | Same page, same panel — no discrete UI element, an existing panel simply became fast | 1 | N/A (a performance property, not a labeled feature) | Stat tiles populate in <0.1s instead of ~9-10s (UT-04); no loading-state regression observed |
| As-of switcher shows genuine historical numbers, not false zeros | Existing global as-of switcher (unchanged component) | 1 (already global chrome) | Unchanged | UT-05 cross-checked two historical dates against direct API calls — both exact matches |
| Honest empty state + auto-heal for a brand-new/never-ingested DB | Same coverage panel, automatic | 1 | Zero/empty tiles read as `0`/`—`, not an error | UT-06: no crash, no hang; reload after warm-up shows real numbers with no manual action |
| `scripts/start-backend.sh` memory cap + persistent logfile | **None — correctly so.** No UI surface exists or is claimed for this; verifiable only via `/proc/<pid>/limits`/`/proc/<pid>/environ` or reading `logs/backend.log` directly | N/A | N/A | N/A |

No capability from `user-visible-changes.md` lacks a navigation path. The flagship capability (the "Refreshed:" line) is about as discoverable as a passive, read-only UI element can be — it requires zero clicks beyond visiting a page operators already use for every backfill, appears in three places at once (live view, persisted fallback, history row), and uses plain-English category names rather than backend slugs. The memory-cap/logfile item is correctly categorized as ops-only infrastructure with no UI claim anywhere in `user-visible-changes.md` — this is an honest disclosure, not a gap (per the reviewer's own instructions: intentionally backend-only capabilities are acceptable when disclosed as such, and no Must-have journey's acceptance text requires a browser-visible surface for it).

**Design-system / visual consistency:** the new line reuses the exact `text-xs text-text-faint` class already used by the adjacent (iter-1-built) breakdown line — confirmed by direct source read (`apps/frontend/app/data/page.tsx:2545` vs `:2550`). No new badge, color token, or arbitrary value was introduced. No new page or panel was added this iteration at all, which removes the most common source of visual drift (a new surface reinventing established patterns).

---

## Regression Risk

Verified directly against the iteration's actual working-tree diff (`git diff --stat HEAD`), not merely inferred from handoffs:

```
apps/backend/app/api/data.py            |   7 +-
apps/backend/app/engine/data_manager.py | 369 +++++++++++++++++++++++++++++-
apps/backend/app/engine/warmup.py       |  36 +++
apps/backend/app/models.py              |  51 +++++
apps/frontend/app/data/page.tsx         |  32 ++-
apps/frontend/lib/api.ts                |   8 +
```
(plus test files and `incredible_auto_dev/scripts/start-backend.sh`/`reports/perf-budgets.md`)

| Shared component | Prior feature it serves | Origin | This iteration's touch | Risk | Verified how |
|---|---|---|---|---|---|
| `BackfillBreakdown` / `LastRunSummary` / `JobProgressPanel` / `RunHistoryPanel` (`/data`) | iter-1's breakdown counts, zero-work badge, chunk progress, persisted-history fallback | ops-hardening iter-1 | Direct — new optional prop threaded through all 3 call sites, extended not forked | **High inherent risk** (same component) — but **directly reverified live** | Browser QA: UT-03 (persisted-history fallback still renders correctly, Refreshed-line correctly absent for a pre-iteration run), UT-07 (fetch/interrupted rows show neither breakdown nor Refreshed line), UT-J-01/UT-J-03 (iter-1's own J-01/J-03 journeys re-run and PASS) — **all PASS** |
| Sidebar (`sidebar.tsx`), app shell (`layout.tsx`), `HealthBadge`/readiness provider, `PreflightBanner`, `error.tsx`/`global-error.tsx`, `availability-heatmap.tsx` | Global navigation; J-04 readiness signal; board-integrity gating; crash containment (all mcp-loop era) | mcp-loop | **Zero** — none appear in this iteration's diff | None | Confirmed via direct `git diff --stat`: 0 lines changed in any of these files |
| `/`, `/scanner-runs`, `/research/*` route code | Dashboard, Scanner Runs list/detail, Research pages | mcp-loop / earlier ops-hardening iterations | **Zero code change** — only the caches these pages read got warmed proactively instead of on-demand | None (consequential, byte-identical output) | Confirmed via diff (no route files touched) + UT-09 live re-check (Dashboard Market Phase card, Scanner Runs list + detail all render correctly, byte-identical to pre-iteration) |
| Coverage panel + as-of switcher (this iteration's OWN new mechanism) | N/A — new this iteration | ops-hardening iter-2 | A regression was introduced **and fixed within this same iteration's dev pass**: the first version only persisted coverage for the current/latest as-of, so selecting any older ingested date served a false all-zero "nothing here yet" panel instead of that date's real numbers. Code review caught it (AG-3-critical) before this handoff; fixed via per-date persist at ingest + a self-healing read for legacy dates. | **Resolved** — flagged here for the record given its AG-3 severity class, not because it is currently open | UT-05: cross-checked two historical dates (2015-04-01, 2015-01-16) against direct `GET /api/data?as_of=...` calls — both exact matches; "Latest" chip round-trip also confirmed unchanged |
| Coverage panel (same new mechanism) — **`fetch`-triggered false-zero, newly discovered, not yet fixed** | N/A — new this iteration | ops-hardening iter-2 | See Flags → Potential Regressions below. Not caused by touching a *prior*-iteration feature's code, but a self-regression relative to this same panel's own pre-iteration behavior (which always live-computed, so it was never wrong) | **Open, non-blocking** | Reproduced and root-caused live by browser-qa-agent during UT-07; self-heal (backend restart) confirmed |
| `LastRunSummary`'s unconditional `dates_total`-derived line ("0 snapshots · 0 trading days in range" for an interrupted run) | iter-1 audit finding F1 — pre-existing, deliberately deferred | ops-hardening iter-1 (found/deferred by iter-1's own auditor) | **Not touched or worsened this iteration.** iter-2 added the Refreshed-line prop to the same component but did not touch this specific pre-existing line. The new Refreshed line correctly self-suppresses for an interrupted run (no false "Refreshed: …" appears), so iter-2 does not compound F1 — but F1 itself remains open in the exact component iter-2 extended | Low (pre-existing, non-blocking, self-disclosed by iter-1's audit as deferred) | Code read: `_breakdown_computed` gate (`data_manager.py:3351`) correctly nulls `aggregates_refreshed` for `calendar_days == 0` rows; `dates_total` itself is still served unconditionally, per iter-1 audit's F1 |

No shared cross-cutting component (nav/shell/readiness/error-boundary) was touched. The one component with real code overlap (`BackfillBreakdown` and its three call sites) was independently re-exercised live by browser QA across both the new field and every one of iter-1's own prior states, and all passed.

---

## UI vs Backend Parity

`implementation-summary.md` states: **"Backend-Only Items: None. Every backend change in this phase has a corresponding, if minimal, piece of it visible in the UI... or is invisible-by-design infrastructure hardening."** Cross-checked against `user-visible-changes.md` and the ui-surface-map:

| Backend capability | Surfaced in UI? |
|---|---|
| `coverage_snapshot` persisted table (replaces request-path `compute_coverage`) | Yes, indirectly — same coverage panel, same numbers, now instant (UT-04); no dedicated "from storage" indicator, and none was required (no journey's acceptance text asks for one) |
| Ingest finalize hook (coverage/market-phase/membership/research-hotkey warming) | Yes — directly named by the new "Refreshed: …" line |
| `aggregates_refreshed` field, honesty-gated | Yes — same line; confirmed null-suppressed for fetch/expand/interrupted/not-yet-computed rows (UT-03, UT-07) |
| Boot-time `_warm_coverage_snapshot` safety net | Yes, indirectly — the empty-then-filled transition on a brand-new DB (UT-06) |
| `scripts/start-backend.sh` `ulimit -v` + `MALLOC_ARENA_MAX` + persistent logfile | **No UI surface — correctly so.** Verifiable only via process/file inspection (TC-15/16/17), never through the product. This is disclosed plainly in `user-visible-changes.md`'s "Not Visible Yet" section, matches the phase spec's own explicit OUT-OF-SCOPE note ("a visible 'coverage last refreshed at HH:MM' indicator" is explicitly not required), and no Must-have journey's acceptance text needs a browser-visible surface for it |
| `computed_at` timestamp on each snapshot | Not rendered — explicitly out of scope per the phase spec; acceptable, not a gap |

No backend capability was found "complete" but silently missing from the UI where a journey required visibility. The two backend-only items (memory cap, logfile) are legitimately ops/infra concerns with their own DoD-level verification path (process inspection, not browser) — this matches the "intentionally backend-only... acceptable" allowance, since the phase's own goal explicitly frames them as reliability hardening, not a product-facing capability.

---

## Flags

### Hidden Capabilities
None found. The flagship new capability (the "Refreshed: …" line) is exposed in three places on a page operators already visit for every backfill, with zero additional clicks and no new navigation required.

### Undiscoverable Capabilities
None found for capabilities this iteration set out to build. One related note: when the fetch-job coverage-blanking gap below occurs, its **recovery path** (restart the backend, or run an unrelated backfill/rebuild) is itself completely undiscoverable from the UI — nothing on `/data` hints that either action would fix the all-zero panel. This is a consequence of the regression below, not a separate hidden feature.

### Potential Regressions

- **Confirmed, non-blocking: a routine "Fetch EOD prices" job that changes bar/symbol counts silently blanks the Dataset coverage panel to a false all-zero state, indistinguishable from a genuinely-never-ingested database, with no in-UI explanation and no discoverable recovery action.** Discovered and root-caused live by the browser-qa-agent during UT-07 (not hypothetical): `CoverageSnapshot` rows are keyed on `(asof_key, dataset_version)`, and `dataset_version` is a live fingerprint that changes whenever bar/symbol counts change. `fetch`-kind jobs are, correctly per this iteration's own spec, never routed through the ingest finalize hook (only `backfill`/`both`/`rebuild` are) — so a `fetch` that lands even one new bar changes the fingerprint out from under every existing `coverage_snapshot` row, and `GET /api/data` then finds no matching row for any as-of date and serves the same honest-empty payload designed for a brand-new database (Universe/Symbols/Trading days/Snapshot dates/Backfill gaps all `0`). QA confirmed this is not a frontend artifact (direct backend `curl` showed the same zeros) and confirmed the only two recovery paths (backend restart, or an unrelated backfill/rebuild) — neither surfaced or hinted at anywhere in the product. This is a genuine behavioral regression relative to the panel's own **pre-iteration** behavior: before this iteration, every `/data` visit live-computed coverage, so it was *always* correct, just slow; after this iteration, a mainstream, lower-risk, everyday action (a plain fetch) can make it briefly but silently wrong. It does not block this iteration's own DEFINITION OF DONE (no test case in the 21 test-first contracts exercises "fetch, then check coverage," and QA's PASS verdict correctly reflects that), and it self-heals without data loss — hence WARN, not FAIL. QA itself flagged this as "a strong candidate for a follow-up iteration."
- **Resolved, not currently open:** the as-of-switcher false-zero-for-historical-dates bug (see Regression Risk table) was introduced within this same iteration's first pass, caught by code review pre-handoff, fixed, and independently re-verified live (UT-05) with direct API cross-checks on two separate historical dates. No action needed; noted here only because it sits on an AG-3-critical dimension and is exactly the class of thing this report exists to catch.
- **Pre-existing, not caused or worsened by this iteration:** `LastRunSummary` still renders "0 snapshots · 0 trading days in range" for an interrupted latest run (iter-1 audit finding F1, deliberately deferred as out of surgical scope). iter-2 extended the same component (`BackfillBreakdown`, which `LastRunSummary` calls) with the new Refreshed line, and that new line correctly self-suppresses for this case — so iter-2 does not deepen F1, but F1 remains open in a component this iteration touched, and is worth folding into whatever future iteration revisits interrupted-row rendering.
- No regression found in any cross-cutting shared component (sidebar, app shell, readiness badge, preflight banner, error boundaries, heatmap) — zero code overlap, confirmed directly via diff.
- No regression found in `/`, `/scanner-runs`, or `/research/*` — zero code changes to those routes, and UT-09 independently re-confirmed live rendering.

### Visual Consistency
- The new "Refreshed: …" line reuses the exact `text-xs text-text-faint` CSS class already established by iter-1's breakdown line — confirmed by direct source read, not just the handoff's claim. No new color, badge, gradient, or arbitrary/inline value was introduced.
- No new page, panel, or layout structure was added this iteration — the single highest-risk source of visual drift (a new surface improvising its own patterns) does not apply here.
- Category labels are humanized via a simple, consistent `_` → ` ` replacement (e.g., "research_hot_keys" → "research hot keys") — plain English throughout, no raw backend slugs leak to the screen (confirmed by source read and QA's UT-08 explicit scan).

---

## Recommendation

No blocking action required before this iteration closes: the flagship capability (the "Refreshed:" line) is maximally discoverable and visually consistent; no cross-cutting navigation or shared-component regression was found; the one regression introduced within this iteration's own dev pass was already caught and fixed pre-handoff with independent live re-verification.

For a near-term follow-up (does not need to reopen this iteration, matches QA's own suggested scope):
1. Fix or mitigate the fetch-job coverage-blanking gap — either have `fetch` jobs also refresh `coverage_snapshot` opportunistically when they change bar/symbol counts, or make the boot-time warm-up safety net run periodically rather than boot-only. Until fixed, consider a cheap interim UI safeguard: when the coverage panel would render all-zero, distinguish "genuinely no data yet" (safe to show today's honest-empty copy) from "data exists but the stored snapshot is stale/missing" (should show something other than an identical-looking honest-empty state) — today an operator cannot tell these two situations apart on screen.
2. Carry forward iter-1 audit's still-open F1 (`LastRunSummary`'s unconditional "0 trading days in range" for an interrupted run) into whichever future iteration next revisits interrupted-row rendering — iter-2 touched the same component and is a natural place to note this, even though fixing it was correctly out of this iteration's own scope.

Neither item blocks this iteration's DEFINITION OF DONE or any Must-have journey (J-05, J-04, J-01, J-03 all pass with direct live evidence); both are flagged because they are genuinely user-visible and fall squarely within this iteration's own headline feature.
