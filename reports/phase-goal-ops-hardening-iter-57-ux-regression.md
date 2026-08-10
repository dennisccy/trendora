# Phase goal-ops-hardening-iter-57 — UX Regression Review

**Date:** 2026-08-10

**Verdict:** UX-REGRESSION-PASS

---

## Inputs consumed

- `runs/goal-ops-hardening-iter-57/plan.md` (UI Evolution + Visual Requirements sections)
- `docs/phases/goal-ops-hardening-iter-57.md`
- `reports/phase-goal-ops-hardening-iter-57-user-visible-changes.md`
- `reports/phase-goal-ops-hardening-iter-57-ui-surface-map.md`
- `reports/phase-goal-ops-hardening-iter-57-ui-test-results.md` (16/17 PASS, 1 legitimate tooling-SKIP)
- `reports/qa/goal-ops-hardening-iter-57-qa.md` — UI Evolution Audit block (`**Verdict:** UI-PASS`)
- `reports/phase-goal-ops-hardening-iter-57-implementation-summary.md` (incl. its post-audit
  verification-pass addendum)
- `docs/handoffs/goal-ops-hardening-iter-57-dev.md`, `-frontend.md`
- Prior handoffs scan (`docs/handoffs/`) for the four shared components this iteration touches
  (`AvailabilityHeatmap` — iters 1/5/56; `HealthBadge` — iters 0/4/25; `BackfillBreakdown` — iters
  1/2; `sma_series` — `indicators.py`, single caller `stocks.py`)
- Direct source diff read: `apps/frontend/components/availability-heatmap.tsx`,
  `apps/frontend/lib/api.ts`, `apps/backend/app/engine/indicators.py`
- `runs/goal-session-ops-hardening/iter-57/coherence.md` — **not present at review time** (coherence
  step had not written its artifact for this iteration yet); no coherence findings to reconcile
  against, so no "audit contradiction" check was possible for this iteration. This is an evidence
  gap, not a contradiction — noted, not treated as a flag.

---

## New Capability Discoverability

There is exactly one new user-facing capability this iteration: the `/data` availability heatmap's
"Data as of `<served_dataset_version>` — updating" banner, shown only when the backend serves a
stale (mid-ingest) reading instead of the empty sentinel.

- **Navigation path:** none needed — it renders inline on the already-registered `/data` page inside
  the existing `AvailabilityHeatmap` card, 0 clicks from where a user already looks for availability
  data. QA's UI Evolution Audit (`reports/qa/goal-ops-hardening-iter-57-qa.md`) confirms Reachability
  PASS, Visibility PASS, Control PASS (no new actions to verify), and Generic-page-dumping PASS —
  cited, not re-derived.
- **Live confirmation beyond QA's conditional-state note:** QA's own audit block could only confirm
  the code path (no job was mid-flight during that check), but `ui-test-results.md`'s UT-03 closes
  that gap with a real, live-triggered backfill: the banner rendered with the exact text "Data as of
  `r2945-rc2945-b2026-08-03-bc3306390-h200` — updating" above 5,391 real (non-empty) `availability-cell`
  elements — the dev handoff's own "not visually screenshotted this dispatch" caveat was resolved by
  QA as recommended.
- **Label clarity:** the banner's static text ("Data as of `<version>` — updating") accurately
  describes what is happening — no label/behavior mismatch. One minor, pre-existing observation (not
  a regression, not new to this iteration): `served_dataset_version` renders as a raw internal stamp
  (e.g. `r2945-rc2945-b2026-08-03-bc3306390-h200`) rather than a human date — but this exactly mirrors
  the page's existing `coverage-stale-notice` convention ("Coverage as of a prior scan (version
  `{c.stale_dataset_version}}`)"), which already ships the identical opaque-stamp pattern elsewhere on
  the same page. Since this iteration deliberately reused that established pattern rather than
  inventing a new one, it is consistent, not a new defect — flagged here only as a candidate for a
  future iteration's polish, not as a UX regression.
- **New user actions:** none (spec-declared) — verified none exist.

## Regression Risk

| Shared component | Prior-phase feature | This iteration's touch | Risk | Evidence |
|---|---|---|---|---|
| `AvailabilityHeatmap` (`apps/frontend/components/availability-heatmap.tsx`) | Per-date availability calendar, iters 1/5; ingest-time cache serving, iter-56 | New conditional banner block inserted **before** the existing `loading`/`error`/`empty`/`ok` branches (verified via diff: pure JSX insertion, no existing branch logic altered) | Low | UT-01 (normal load, 5,391 cells, no banner) PASS; UT-04 (idle state post-job, banner absent) PASS — both regression-guard cases hold |
| `HealthBadge` / `GET /api/health` (used by every page's header) | Global readiness badge, iters 0/4/25 | Backend-only latency fix (indexed query replacing a per-request `COUNT(DISTINCT symbol)` scan); response shape/values unchanged, no frontend file touched | Low | UT-06: `readiness-badge` still `data-state="ready"` on `/`, `/stocks/AAPL`, `/scanner-runs`; measured 23-47ms (was 160-241ms) |
| Stock Detail chart / `sma_series` (`apps/backend/app/engine/indicators.py`) | Price + MA overlay chart | Bounded the per-call slice window (O(n²)→O(n)); confirmed by direct grep this function has exactly one caller (`apps/backend/app/api/stocks.py`) — not shared with scanner/scoring paths, which call `sma()` directly, so the blast radius is confined to this one endpoint | Low | Byte-identity proven by dedicated regression test (`test_indicators.py`, TC-6) plus live UT-02/UT-07: caption "3189 bars · as of 2026-08-03 · history since 1996-01-02", MA lines render, 3ms measured |
| `BackfillBreakdown` "Refreshed: …" note | Job-history breakdown, iters 1/2 | `persisted_this_call` rollback-honesty fix only changes behavior on a forced-rollback failure path (fault-injected in unit tests, not reachable through normal UI use) | Low | UT-09 confirms the success-path note is unaffected ("Refreshed: latest snapshot, coverage, membership timeline, …" still renders normally); TC-10 fault-injection unit tests pass for both `data_manager.py` and `indexes.py` siblings |
| MCP `list_runs` (`apps/backend/app/mcp/tools.py`) | AI-assistant/agent integration tool, no web-UI caller | Grouped-aggregate rewrite, byte-identical `n_stocks` | None | No frontend surface exists for this tool; UT-10-equivalent byte-identity unit tests pass |

No shared component's existing behavior regressed. Both regression-guard UI states specified in the
plan (idle/matching-stamp unchanged; never-ingested empty state unchanged) were explicitly tested and
passed.

**Forward-looking, not a regression from this iteration:** the implementation summary's own "Known
Limitations" section discloses that `GET /api/regime-history` (also called by the same Stock Detail
page this iteration's chart fix touches) has independently grown slower over time (~1-3s) as the
dataset has grown. This iteration did not touch that call and it was not in scope — noted here only
because it shares a page with a component this review is examining, as a heads-up for a future
iteration, not a finding against this one.

## UI vs Backend Parity

| Backend capability this iteration | User-facing? | Surfaced in UI? |
|---|---|---|
| Availability stale-serving fallback (`stale`/`served_dataset_version`) | Yes | Yes — the new banner |
| `GET /api/health` latency fix | No (invisible speed-only) | N/A — correctly not surfaced as new UI, only as faster existing behavior |
| `bars_through_latest` / `sma_series` latency fix | No (invisible speed-only) | N/A — same |
| `persisted_this_call` rollback-honesty fix (both siblings) | Only in a rare failure path, via the pre-existing "Refreshed: …" text | Yes, via the existing mechanism — no new field/UI added, matching the phase's explicit "no new status value" out-of-scope decision |
| MCP `list_runs` dedup | No — agent/MCP-only tool | Correctly has no web UI; explicitly documented as such in both `user-visible-changes.md` and `ui-surface-map.md` |
| `perf-budgets.md` correction note, `docs/test-infra-tickets.md` | No — developer records | Correctly not surfaced |

Every backend change with genuine user-facing implications is surfaced. Every backend-only change is
correctly left without a UI surface, and the implementation summary explicitly confirms this ("no
backend-only items" that lack either a UI change or a legitimately invisible speed/correctness fix).
No parity gap found.

## Flags

### Hidden Capabilities
- None.

### Undiscoverable Capabilities
- None. The one new capability is inline on the page a user already checks for data status, requires
  zero navigation, and was live-confirmed rendering during a real ingest job (UT-03).

### Potential Regressions
- None confirmed. All four touched shared surfaces (`AvailabilityHeatmap`, `HealthBadge`, Stock Detail
  chart, `BackfillBreakdown`) were regression-tested against their pre-iteration behavior and passed.

### Visual Consistency
- The new banner's className (`border-b border-border bg-surface-2 px-4 py-2 text-xs text-text-muted`)
  is byte-identical to the existing `coverage-stale-notice` element on the same page (verified directly
  in `apps/frontend/app/data/page.tsx:760-761`) — no arbitrary values, no new visual pattern
  introduced; it reads as part of the same established "as-of" convention rather than a new style or
  alarm treatment, matching the plan's Visual Requirements exactly.
- No other new UI surfaces exist this iteration to assess for consistency (the other three affected
  surfaces are behavior-only, not new markup).

## Recommendation

No action required. The single new user-facing capability is discoverable with zero added navigation,
is visually consistent with the page's established pattern, and was live-verified rendering correctly
during a real in-flight job. All shared components touched by backend changes (health, bars/MA chart,
rollback-honesty note) were regression-tested and hold. The two carried-forward, out-of-scope items
noted above (opaque `served_dataset_version` stamp formatting; `/api/regime-history` growing slower)
are pre-existing/adjacent, not introduced by this iteration, and are already logged in the dev/QA
records for a future round — restating them here only for continuity, not as blockers.
