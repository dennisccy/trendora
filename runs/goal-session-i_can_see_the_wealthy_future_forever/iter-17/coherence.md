**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-17 (i_can_see_the_wealthy_future_forever)

**Iteration:** 17 — *Forward-test evidence aggregate moves to Backtest, as-of-scoped (expanding window ≤ D); retire System Health*
**Target journeys:** J-09, J-10
**Snapshot SHA audited against:** `e5a22e8095cadb226606b11a7c584998b8c37786`
**Scope of change:** relocation + as-of scoping of an EXISTING canonical value (`compute_forward_aggregates`) from the retired `/system-health` onto `/backtest`. No new Data-Contract value. Nav-skeleton change (System Health retired) — blueprint IA edited + `state/blueprint.reapproval-requested` marker written (confirmed present).

This is a consolidation iteration: it actively *resolves* coherence invariant #12 ("no second home for an existing entity") by moving an aggregate that had its own page onto the page that already serves the per-date scorecard built from the same stored `forward_returns`. No objective violations found.

---

## Step 1 — Data Contract check (the "numbers don't match" gate) — PASS

Registered canonical value (blueprint Data Contract): **Forward-return aggregates** — computed once by `app.engine.forward_testing:compute_forward_aggregates`, served by (after this iter's edit) `GET /api/backtest`.

- **No duplicate computation.** The `as_of` cutoff was added to the SAME function — `compute_forward_aggregates(session, horizon, config=None, *, as_of=None)` (`apps/backend/app/engine/forward_testing.py:547-563`). It is a SINGLE membership filter on the `fr_rows` step (`forward_testing.py:572-582`: `if as_of is not None: fr_stmt = fr_stmt.join(ScannerRun, …).where(ScannerRun.asof_date <= as_of)`); the grouping / excess / control-group / attribution math is untouched, and `as_of=None` adds no clause (byte-identical all-history path). No new `_compute_*`/second aggregation function was introduced. Grep confirms no rival implementation.
- **Canonical source, single serving home.** `apps/backend/app/api/backtest.py:37-41` imports `compute_forward_aggregates` from the canonical module and `backtest.py:66-69` calls it with `as_of=run.asof_date`, riding the single `/api/backtest` payload as `evidence_by_horizon`. The previous serving path is fully retired: `system_health.py` route DELETED, router unregistered (`apps/backend/main.py:26,75 removed`), `fetchSystemHealth`/`SystemHealthResponse` removed from `apps/frontend/lib/api.ts`. Net result = ONE computing module, ONE serving endpoint — the opposite of a second-source split.
- **No non-canonical UI source / no client recompute.** The new `apps/frontend/components/evidence-panels.tsx` is purely presentational: `EvidenceAggregateSection({ evidence, asofDate })` takes the `evidence` object straight from the `/api/backtest` payload (`apps/frontend/app/backtest/page.tsx:181` `backtest.evidence_by_horizon[selected?.horizon]`) and only re-formats (`<Return>`, `fmtPct`, badges). No `fetch`, no arithmetic on returns/excess/buckets. The `EvidenceAggregate` interface (`lib/api.ts`) is the renamed-in-place `SystemHealthResponse` shape — same canonical value, now nested in `BacktestResponse.evidence_by_horizon: Record<number, EvidenceAggregate>`.
- **No new/unregistered value.** Spec and blueprint both state no new value is introduced; confirmed. The J-19 attribution aggregate slice and the J-16/J-28 pattern breakdowns ride the same relocated aggregate (no separate computation). Read-only grouping of persisted `forward_returns` is the established, every-iteration-passing model (invariant #2 permits read-only grouping of stored values; it recomputes no return/score/bucket).

## Step 2 — Information Architecture check — PASS

- **No new route added; a route is removed.** The evidence aggregate homes on the EXISTING `/backtest` page, reachable in **1 click** via the intact sidebar entry (`apps/frontend/components/sidebar.tsx:35` `{ href: "/backtest", label: "Backtest", icon: FlaskConical }`).
- **No duplicate home / no dangling nav.** `/system-health` page deleted (`apps/frontend/app/system-health/page.tsx` removed), its sidebar entry + now-unused `Activity` icon import removed (`sidebar.tsx`). Frontend SOURCE grep for `system-health`/`fetchSystemHealth`/`SystemHealth` is CLEAN (only `.next/` build-cache trace hits, which are stale artifacts). Backend residual references are comments/docstrings + the correct retirement test `test_system_health_route_is_retired_404` (asserts `GET /api/system-health` → 404) — no live import/route/registration.
- **No parallel shell.** The new panel is rendered inside the existing `BacktestResults` component at the very bottom, after the leadership lists (`backtest/page.tsx:209-211`), preserving the J-21 order (scorecard → Return Attribution → leadership lists → evidence). Same established dark-workstation shell.
- **Nav-skeleton change handled per agent rules.** `blueprint.md` IA skeleton + journey-home table + Data Contract rows edited to reflect the retirement/relocation (verified in diff), AND `runs/goal-session-…/state/blueprint.reapproval-requested` is written — so `run-goal.sh` will pause for human confirmation before iter-18's decomposer.

## Step 3 — Subjective observations (advisory only) — none blocking

- **J-18 (principal anti-goal — exactly one date selector) holds.** The aggregate's cutoff is the resolved global as-of (`run.asof_date`, `backtest.py:67`), transmitted as the existing `?as_of=` on the snapshot-served read — the single global date being read, NOT a second state (consistent with MEMORY `j18-asof-on-stocks-fetch-is-correct`). No page-local date picker was added; `EvidenceAggregateSection` reads `asofDate` from the payload, and the horizon control is a view selector over the already-fetched `evidence_by_horizon` (no refetch). The frontend holds no second date state.
- **Consistent labelling.** The section is clearly titled "Forward-tested evidence (expanding window ≤ {asofDate})" and explicitly distinguished from the per-date scorecard ("what *this* date's cohort did") — reduces the "two things that look the same" confusion risk.
- **Housekeeping improves coherence.** `config.yaml:517` comment and `apps/backend/app/api/research.py:13-16` docstring were updated only to drop stale `/api/system-health` references (no scoring literal, no as-of param added to `/api/research/*` — respects OUT OF SCOPE). These reduce drift, not add it.

---

## Summary

No Part A (Data Contract) or Part B (Information Architecture) violation. The iteration removes a duplicate-home risk rather than creating one, keeps a single computing module and a single serving endpoint for the forward-return aggregate, adds no second date state, and correctly records the nav-skeleton retirement in the blueprint with the re-approval marker. Verdict: **COHERENCE-PASS** (no advisory issues rise to WARN).
