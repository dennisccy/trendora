# Phase goal-ops-hardening-iter-19 — UX Regression Review

**Date:** 2026-07-24

**Verdict:** UX-REGRESSION-PASS

---

**Note on scope:** `Frontend Present: no` for this iteration, which would normally warrant the short
backend-only stub response. Per this dispatch's PUMP NOTE, the fuller discoverability/regression/parity
checks were run anyway — this iteration is a genuine, measured latency fix to an existing page, and a
distinct pre-existing UX finding (below) needed to be weighed, not silently dropped. The verdict below is
substantiated, not a boilerplate pass.

---

## New Capability Discoverability

None introduced this iteration — confirmed by the phase spec ("New user-facing capability: None directly
new," "New user actions: None," "UI surface changes: None"), the plan, and the user-visible-changes report,
and corroborated by `git status --short` / `git diff --stat`: zero files under `apps/frontend/` appear in
this iteration's changeset (only `apps/backend/app/api/backtest.py`, `apps/backend/app/engine/
forward_testing.py`, `apps/backend/app/mcp/tools.py`, two backend test files, and `reports/perf-budgets.md`).

- **Existing `/backtest` discoverability — unchanged, live-reconfirmed.** I independently checked
  `apps/frontend/components/sidebar.tsx:37` and found the entry unchanged: `{ href: "/backtest", label:
  "Backtest", icon: FlaskConical }` — 1 click from the dashboard, no login gate. I also live-curled the
  running services just now: `GET /api/health` → HTTP 200 in 92ms; `GET http://localhost:3255/backtest` →
  HTTP 200; `GET http://localhost:3255/` → HTTP 200. This matches browser-QA's own UT-06 finding
  (1-click sidebar path, no login, confirmed via `window.location.href` after navigation).
- **The one new backend-only artifact — the `write_taken` field** appended to the `backtest_timing` /
  `query_backtest_timing` structured log lines — is correctly operator/log-only. Confirmed by direct diff
  read of both `apps/backend/app/api/backtest.py` and `apps/backend/app/mcp/tools.py`: the only changes are
  (1) capturing `backfill_run_forward_returns`'s already-computed return value into a local
  (`backfill_result`), (2) deriving `write_taken = backfill_result["rows_inserted"] > 0`, and (3) appending
  one field to the internal timing-log call. The `return {**card, ...}` block — the actual served response
  — is byte-identical in both files; no navigation/discoverability requirement applies to a log-only field.

## Regression Risk

Per the ui-regression-scout skill's method (intersect this phase's changed components against prior-phase
handoff components):

| Shared surface | Prior feature it serves | Touched by this diff? | Risk |
|---|---|---|---|
| `Sidebar` / nav / router | All prior-phase pages, incl. `/backtest`'s own 1-click entry (iter-1 onward) | No (0 frontend files in diff) | None |
| `apps/frontend/app/backtest/page.tsx` (`BacktestResults`, `ScorecardSection`, `RefreshingEvidenceBanner`, `EmptyState` reuse) | iter-16 (`evidence_status`/`evidence_generated_at` disclosure), iter-17 (`evidence_asof` on the banner) | No (0 frontend files in diff) | None — file untouched |
| `GET /api/backtest` response shape (`evidence_status`, `evidence_generated_at`, `evidence_asof`, `evidence_by_horizon`, scorecard fields) | Same iter-16/17 UI features above, which render these fields directly | Internals of the producing function changed; **response shape did not** | Low, and closed out by direct evidence (below) |
| MCP `query_backtest` | No browser page of its own (backend/assistant-only) | Same internal change, same guarantee | Low, same evidence |

- **Zero frontend files touched** — the intersection between this phase's `ui-surface-map.md` and any prior
  handoff's "Files Changed" (iter-16-frontend.md, iter-17-frontend.md: `apps/frontend/app/backtest/page.tsx`,
  `apps/frontend/lib/api.ts`) is empty. There is no shared-component code-edit regression surface for this
  diff to have introduced.
- **Response-shape risk is low and directly checked, not assumed.** I read the actual diffs myself: in both
  `backtest.py` and `mcp/tools.py` the only lines added are the `backfill_result` capture and the appended
  log field — the dict returned to callers (and therefore to `page.tsx`'s `fetchBacktest`/`BacktestResults`)
  is untouched. This is consistent with TC-5 (unit-level byte-identity, every horizon, with/without `as_of`),
  the reviewer's independent rerun (37 scoped tests, 0 failures), and browser-QA's UT-03 (two independent
  full-DOM captures of `/backtest`, diffed byte-for-byte identical) and UT-04 (a fully-elapsed historical
  date still renders every horizon's real values). I additionally tailed `logs/backend.log` live just now and
  confirmed current requests show `write_taken=False` with small `backfill_forward_returns_ms` (2–20ms),
  consistent with the shipped fix actually running in the live process.
- **Required-still-passing journeys:** J-01, J-03, J-05 all replayed PASS via the deterministic golden replay
  (`reports/phase-goal-ops-hardening-iter-19-regression-replay-results.md`, 3/3, 0 skipped). J-04's
  disruptive kill/restart replay was SKIPPED by browser-QA — every acceptance-bearing step needs a live
  backend restart/kill that neither the dispatched agents nor I have permission to perform this session; this
  is the same owner-gated carry-forward documented since iter-15/16/17/18 (TC-8's non-disruptive `GET
  /api/health` substitute is what this iteration actually owes, and the operator/dev handoff both treat it as
  such), not a new gap this diff introduced.

**Conclusion: no potential regression is attributable to this iteration's diff.**

## UI vs Backend Parity

- **Backend capability shipped:** a request-path zero-write guard inside `backfill_run_forward_returns`,
  landed as a global "skip un-elapsed horizons before the per-symbol loop" short-circuit (the developer's
  attempt 3, after two earlier attempts — a redundant-save removal and a column-projected read — were tried
  and live-measured insufficient; reviewer verdict PASS, TC-6 mean 13.9ms/max 73.4ms, independently
  re-checked by the reviewer against `logs/backend.log`).
- **UI exposure:** correctly none. Nothing new is computed or displayed — the served payload is explicitly
  proven byte-identical (TC-5, TC-10, UT-02/03/04). This is a case where "backend change, no UI surfacing"
  is the intended and correct outcome, not a parity gap: there is no new value for any component to render,
  and the phase spec is explicit about this ("New information displayed: None").
- **The `write_taken` log field is correctly kept server-side-only** — a diagnostic for operators reading
  `logs/backend.log`, never part of the response dict (confirmed by diff read). Appropriate scoping.
- **One documentation nuance, not a UI gap:** the phase spec sketched two candidate guard shapes
  ("skip-commit-when-zero" vs. "a pre-check"); what actually shipped (per the dev handoff and reviewer
  summary) is a broader un-elapsed-horizon short-circuit found only after those two were tried and measured
  insufficient. This is a legitimate, well-evidenced pivot documented in the dev handoff and confirmed by the
  reviewer — noting it here only so the parity record isn't read as claiming the originally-sketched
  mechanism is what shipped. It has no UI-facing consequence.

## Flags

### Hidden Capabilities
None. No new user-facing capability was introduced this iteration.

### Undiscoverable Capabilities
None. `/backtest`'s existing 1-click sidebar path is unchanged and was live-reconfirmed both by browser-QA
(UT-06) and by my own direct read of `sidebar.tsx` plus a live curl of the running frontend/backend.

### Potential Regressions
None attributable to this iteration's diff. Zero frontend files were touched; the response payload every
prior-phase `/backtest` UI feature (iter-16's evidence-status banner, iter-17's `evidenceAsof` disclosure)
depends on is proven byte-identical by both unit-level and live evidence; required-still-passing journeys
J-01/J-03/J-05 replay green; J-04's skip is the same owner-gated carry-forward as the last four iterations,
not new.

### Visual Consistency
Not applicable — no frontend file changed, so there is no new page or component to compare against the
DESIGN SYSTEM or prior visual style. `/backtest`'s rendered output is QA-confirmed identical to its
pre-iteration state (UT-03: two independent full-DOM captures diffed byte-for-byte identical).

### Advisory: Pre-Existing UX Concern (Explicitly NOT This Iteration's Regression)

- **Cold first-view stall on a historical `/backtest` date.** Browser-QA (UT-04) found that the FIRST
  navigation to a not-yet-served historical as-of (`2025-05-30`) left the page on empty skeleton
  placeholders for **9.6s–54s** before rendering (three concurrent first-touch requests logged `total_ms` of
  9548/54483/54328). QA traced the cost to a distinctly-named log field, `ensure_loop_ms` (9288/54281/54084ms
  on those same lines) — a separate subsystem from this iteration's own `backfill_forward_returns_ms`, which
  stayed small (12–80ms, `write_taken=False`) on every one of those same requests. Repeat loads of the same
  date dropped to 0.08–0.13s, confirming a one-time per-date cold cost.
- This is correctly **not** attributed to iter-19's diff by browser-QA, the dev handoff, or the dispatch's own
  PUMP NOTE — it predates this change, sits in a different code path (`ensure_loop_ms`, not
  `backfill_run_forward_returns`), and this iteration's own "OUT OF SCOPE" list already excludes J-06's other
  page-load budgets. I am relaying measured evidence already gathered elsewhere, not re-diagnosing root
  cause.
- From a pure UX-regression lens, however, this is a real, user-observable gap on the SAME page this
  iteration is meant to be hardening: a 10–54 second wait with no loading indicator, spinner, or progress
  message anywhere in the QA evidence — just static empty skeleton boxes, giving a user no way to
  distinguish "loading" from "stuck." It does not change this iteration's own verdict, but flagging it here
  so it is not implicitly closed alongside iter-19's J-06/J-07/J-08 evidence when neither this diff nor this
  iteration's test coverage touches it.

## Recommendation

No action required on this iteration's own deliverable: it introduces no new UI surface, breaks no
discoverability path, and touches zero shared frontend components. The byte-identity/regression evidence is
consistent across every source checked — developer (TC-5), reviewer (independent rerun, PASS), browser-QA
(UT-02/03/04/05/06), and my own live spot-check (backend health 200/92ms, `/backtest` and `/` both 200,
`sidebar.tsx`'s "Backtest" entry unchanged, live `backtest_timing` log lines showing `write_taken=False` with
small `backfill_forward_returns_ms`).

One follow-up worth carrying forward, not blocking this iteration: register the historical-first-view
`ensure_loop_ms` stall (9.6–54s, no loading affordance) as its own tracked item, distinct from J-06/J-07/J-08's
`backfill_run_forward_returns` fix, so it doesn't quietly ride along as "solved" once this iteration's target
journeys are evaluated.
