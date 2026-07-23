# Phase goal-ops-hardening-iter-12 — UX Regression Review

**Date:** 2026-07-23

**Verdict:** UX-REGRESSION-WARN

---

## New Capability Discoverability

None to assess. `plan.md`'s "UI Evolution" section, the phase spec's "New user-facing capability" bullet
("None new"), and `reports/phase-goal-ops-hardening-iter-12-user-visible-changes.md` all agree: zero new
user-facing capability, zero new information displayed, zero new user action, zero navigation change this
iteration. `git status`/`git diff --stat -- apps/backend apps/frontend` (re-confirmed independently here)
both return empty. `Frontend Present: yes` was set for one documented reason only — to force the goal-mode
harness's browser-qa lane to run G2's three-load `/api/indexes` control measurement and the
J-01/J-03/J-04/J-05 required-still-passing replay, not because new UI shipped. There is nothing to flag as
hidden or undiscoverable this iteration.

## Regression Risk

| Shared surface touched this iteration | Prior feature it serves | This iteration's change | Risk |
|---|---|---|---|
| `/data` — Coverage/`/api/indexes` panel (`apps/frontend/app/data/page.tsx`) | J-06's performance-budget commitment on the Data Manager page | **No code change** — three fresh-navigation, cache-disabled real-browser measurements only (G2) | **None (re-verification only).** But the measurement itself surfaces a real, confirmed finding — see Flags below. |
| `/data` — `JobForm`/`JobProgressPanel`/`UnfinishedImportsPanel` | J-01 (zero-work explanation), J-03 (no range cap), J-04 (interrupted-job state) | **No code change** — re-verification via a fresh >370-day backfill (UT-06/UT-07), reload persistence check (UT-08), and a live read of pre-existing interrupted rows 124/119/114 | **None.** All three re-confirmed PASS with fresh evidence this turn; no behavior drift detected. |
| `/scanner-runs`, `/scanner-runs/[runId]`, `/` (`MarketPhaseCard`) | J-01 step 4 / J-05 step 2(a) — precomputed leaderboard/phase, no on-read compute | **No code change** — re-verified via live DB cross-check (UT-10: DOM vs. `scanner_results` row, exact match) and Resource-Timing (UT-11: `/api/market-phase` 39.7ms, no stall) | **None.** |
| `HealthBadge` / `PreflightBanner` (global) | J-04 steps 2–4 — boot-phase detail and NO-GO presentation | **No code change**, and **not freshly exercised this turn** — UT-12/UT-13 SKIPPED (no operator-performed restart/crash was available this session); carried forward on the grounds that `health-badge.tsx`/`preflight-banner.tsx`/`health.py`/`readiness.py`/`main.py`/`warmup.py` are all confirmed `git diff`-empty since a commit that pre-dates even iter-9's own accepted verification | **Low, but a live coverage gap, not a confirmed pass.** Steps 3–4 of J-04 rest on "code unchanged since it last passed," which is a sound but weaker form of evidence than the fresh DOM/log proof steps 5–6 got this turn. This gap is carried forward unchanged from iter-9/iter-11 (same operator-action constraint), not newly introduced. |
| `apps/backend/app/engine/forward_testing.py:826` (`compute_forward_aggregates`) | AG-8's already-tracked unbounded-load MemoryError (feeds `/data`'s coverage/job-history rendering indirectly) | **Named, not modified** (`git diff` empty) — the TC-4 audit-correction addendum documents the MISS/compute-path site; the `data_provider_runs` 120/121/122 read reconfirms it fired 3-for-3 on the sampled rows, once cascading into a `GET /api/data` HTTP 500 (historical, pre-dating this dispatch) | **Carried-forward critical risk, unchanged by this iteration.** This iteration's OWN triggering of the same code path (during UT-06/07 and J-01 step 5's live backfills) produced two MORE MemoryErrors, but both were caught internally with zero HTTP 500s reaching a client (UT-15, informational PASS) — so no regression in THIS session's user-facing behavior, but the underlying crash-risk code is untouched and still live. |

**Golden-script replay note (informational, not a product regression):** the deterministic replay lane
(`reports/phase-goal-ops-hardening-iter-12-regression-replay-results.md`) recorded FAIL for J-01/J-03/J-05
("`step 02 could not perform fill: Locator.wait_for` timeout"), then its own footnote states these were
"overturned by the LLM lane's re-confirmation this iteration (golden-script false positive)." The LLM
browser-qa lane's fresh, independently-gathered evidence (DB cross-checks, DOM assertions, screenshots) for
the same three journeys is credible and consistent with prior iterations' findings, so this is treated as a
harness-timing flake, not a real regression — but it is a second, low-severity instance (after iter-9's
merge-summary/raw-file mismatch) of this pipeline's automated evidence needing a human/LLM tiebreaker before
being trusted at face value.

## UI vs Backend Parity

- No new backend capability shipped this iteration (confirmed via `implementation-summary.md`'s "Files
  Changed" list: `reports/perf-budgets.md` transcription/addenda, dev handoff, implementation summary,
  `status.json` — none are `apps/backend/` or `apps/frontend/` source). Nothing new to surface in the UI;
  no parity gap on the "capability shipped but hidden" axis.
- **AG-8 is disclosed honestly, not concealed as resolved.** The dev handoff, implementation summary, and
  `user-visible-changes.md` all explicitly state the `forward_aggregates_cached` → `compute_forward_aggregates`
  MemoryError remains unresolved and reconfirm it as a live, reproducible 3-for-3 failure this iteration's own
  `data_provider_runs` read uncovered — not silently dropped, not claimed fixed. This is the correct parity
  posture for a critical, explicitly out-of-scope, owner-decision item.
- **A real, now-confirmed user-facing performance gap exists and is correctly disclosed, not hidden.**
  G2's three independent, cache-disabled, idle-cross-checked real-browser readings of `GET
  /api/indexes?full=true` on `/data` (2257.7ms / 2148.2ms / 2138.7ms — UT-02/03/04) all exceed the committed
  ≤1.5s budget by 43%–51%, under host conditions confirmed idle via both `logs/backend.log` (no concurrent
  ingest) and `logs/hwmon/hwmon.csv` (load1 1.48–1.83, mem_avail 18.2–18.8GB). This is the exact finding the
  pump note calls out as material: it rules out iter-11's "ambient contention" explanation for this specific
  endpoint. The gap is transparently recorded in `reports/perf-budgets.md` (a project-internal artifact) but
  there is **no user-facing signal on the `/data` page itself** that this specific panel is running
  chronically over its performance budget — a user just experiences a ~2.1–2.3s wait for the Coverage panel
  on every page load, indistinguishable from "normal" to them. Plan.md correctly scopes only re-confirming
  the pre-existing "honest still-loading, never frozen" state (not building anything new), and that state was
  reconfirmed live (panel populated correctly all three times, no blank/frozen frame) — so this is not a
  broken experience, but it is an unaddressed, now-doubly-confirmed slow one.

## Flags

### Hidden Capabilities
- None. No new capability shipped this iteration.

### Undiscoverable Capabilities
- None. No new capability shipped this iteration.

### Potential Regressions
- **None caused by this iteration** — zero `apps/backend`/`apps/frontend` files changed, confirmed by both
  the dev handoff and independent `git diff --stat` inspection here. All re-verification rows above passed
  with fresh evidence except J-04 steps 3–4 (HealthBadge/PreflightBanner live-crash behavior), which remain
  a **carried-forward, not newly-introduced, coverage gap**: SKIPPED again this session (UT-12/UT-13) because
  no operator-performed backend restart/crash was available, resting instead on a code-diff-empty argument
  that has now held unbroken since at least iter-9. This is low risk given the code's stability record, but
  it is evidence-by-absence, not evidence-by-observation, and should not be mistaken for a fresh live pass.
- **AG-8's `forward_aggregates_cached` → `compute_forward_aggregates` unbounded-load MemoryError remains
  live and reproducible** (3-for-3 on this iteration's own `data_provider_runs` 120/121/122 read, one
  instance cascading to a `GET /api/data` HTTP 500). Explicitly out of this iteration's scope per the phase
  spec (named, not fixed) — correctly so — but it is a standing critical risk to any user who triggers a
  cache-miss ingest (a new-trading-date backfill), and this iteration's own QA pass reproduced it twice more
  (UT-15), even though both instances were caught before reaching a client this time.

### Visual Consistency
- Not applicable — zero frontend files changed this iteration (confirmed via the dev handoff's "Files
  Changed" list and `ui-surface-map.md`'s "Frontend surfaces changed: 0"). No new component patterns, no
  arbitrary values introduced; all 7 re-verification rows in the UI surface map are pre-existing surfaces
  exercised as-is, and browser-qa's own screenshots (where not blocked by the documented page-height/blank-
  screenshot limitation) show styling consistent with prior iterations (e.g. `border-pos`/`text-pos` vs.
  `border-border`/`text-muted` badge distinction, re-confirmed in UT-J-01 step 8).

## Recommendation

1. **No action required on this iteration's own scope** — the transcription (G1), the three-load control
   measurement (G2), and the TC-4 audit correction were exactly what this iteration set out to do, and each
   is complete, honestly disclosed, and correctly does not touch any UI code.
2. **Backlog item (not this iteration's scope):** `GET /api/indexes?full=true` on `/data` is now confirmed
   — by three independent, idle-cross-checked readings, not a single ambiguous sample — to run 43%–51% over
   its committed ≤1.5s budget. Since users get no in-page signal that this specific panel is chronically
   slow (only a longer, otherwise-honest loading wait), recommend either raising the committed budget to
   match reality or scoping a fix to the endpoint/query, as a future iteration's explicit target.
3. **Recommend closing the J-04 steps 3–4 (HealthBadge/PreflightBanner) live-verification gap** the next time
   an operator-performed restart/crash is available in-session — the code-diff-empty argument is sound but
   has now substituted for a live pass across at least iterations 9 through 12.
4. **No new action on AG-8** beyond what the spec already calls for — it remains the correct, explicitly
   named, critical owner decision blocking `GOAL_ACHIEVED`; this review adds no new information beyond
   reconfirming (via this iteration's own evidence) that it is not a one-off.
5. **Minor, informational:** the merged `reports/phase-goal-ops-hardening-iter-12-ui-test-results.md`
   header states "16/20 journeys passed (3 skipped)" while its own results table contains 17 PASS rows (a
   1-off undercount) and the raw `...ui-test-results.llm.md` correctly states "17/20 ... 0 failed." This is
   the same class of `merge_ui_test_results.py` header-arithmetic issue already flagged as an out-of-scope
   framework-maintainer item in prior iterations (score from the raw file, per this session's own standing
   instruction) — noted for completeness, not a new defect and not blocking.
