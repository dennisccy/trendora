# Iteration 40 — Coherence Audit

**Iteration:** goal-market-compass-iter-40
**Date:** 2026-09-02
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `session_delta.stock_accounting` (new field on the registered "Next-session manifest — CONTENT block" row) | OK | Computed in `apps/backend/app/engine/session_delta.py:280-295` (`_stock_changes`) and `apps/backend/app/engine/session_delta.py:329-350` (`compute_delta`) — the SAME registered canonical function that owns `session_delta`; no second query, no second materialization of `crossing_pairs` (reuses the list already built for `changes`/`suppressed`). Served on the SAME registered endpoint `GET /api/compass` (no changes to `apps/backend/app/engine/compass.py` or `apps/backend/app/api/*` in this diff — confirmed via `git diff --stat`, zero hits). Blueprint iter-40 update (`runs/goal-session-market-compass/state/blueprint.md:422-454`) pre-registers this exact field against this exact producer/endpoint, so it is not an unregistered value either. |
| `apps/frontend/lib/api.ts` `SessionDeltaStockAccounting` / `SessionDelta.stock_accounting?` | OK | Pure TS type declaration (`apps/frontend/lib/api.ts:355-374`), optional, matching AG-12 (field absent on manifests frozen before this ships). No new fetch, no new endpoint. |
| `apps/frontend/lib/stock-accounting-summary.ts` (`stockResidualDisclosureText`, `stockShownCapDisclosureText`) | OK — re-format, not recompute | Both functions only turn the already-computed `evaluated_count/shown_count/suppressed_count/residual_count` integers into display strings (pluralization + a static template); they perform no classification/threshold logic of their own (`apps/frontend/lib/stock-accounting-summary.ts:28-48`). This is display formatting of a canonically-sourced value, which the audit skill explicitly treats as non-violating. |
| `WhyNotFailedCondition.gating` (already-registered iter-38 field) | OK | `apps/frontend/components/compass-focus-section.tsx:136-149` (`gatingSuffix`) only changes how an already-served, already-registered field is rendered (2-state truthiness → 3-state honest label). No new value, no new producer, no new endpoint. Single call site confirmed (`compass-focus-section.tsx:166`). |
| `config.yaml` `compass.delta.max_stock_items` | OK | Comment-only change (`config.yaml:1422`); value unchanged at `10` — confirmed by `apps/backend/tests/test_session_delta.py:187` asserting the live value is still `10`. No threshold retuned (AG-15 honored). |

No new endpoint was added (`POST /api/compass/regenerate` and `GET /api/compass` are the only two compass routes touched by history; neither `apps/backend/app/engine/compass.py` nor `apps/backend/app/api/*` appears in this iteration's diff at all). No duplicate/second computation of `session_delta`, `selection.*`, or `session_delta.rotation` was found — `_sector_changes`/`_theme_changes`/`evaluate_selection` are untouched by this diff, consistent with the iteration's own "Do not redo" scope.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/` — What-changed card stock-accounting disclosure (residual + shown-cap lines) | OK | No new route/page/component tree — added inline to the existing `apps/frontend/components/compass-whatchanged-card.tsx` (lines 36-43, 79-85, 102-112), which is the card already registered under the Today (`/`) home in the blueprint's Feature/journey homes table (J-02 row). `apps/frontend/components/sidebar.tsx` (NAV array, lines 36-49) is unchanged in this diff and already lists exactly the 12-entry skeleton the blueprint's Navigation skeleton section specifies, in the same order — no drift. |
| `/` — Next-session focus section `gating` label fix | OK | Same existing `apps/frontend/components/compass-focus-section.tsx`, the component already registered under the Today (`/`) home (J-04 row) — a render-logic fix inside it, not a new surface. |

No new page, route, or nav entry was introduced this iteration; `git diff --stat` against the snapshot SHA shows zero touches to `apps/frontend/app/`, `apps/frontend/components/sidebar.tsx`, or any router/layout file, matching the iteration spec's own "Blueprint conformance" claim (no IA change, no new nav entry).

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None of substance. The two new disclosure strings ("N more stock moves held back by the display cap" / "Showing the top N stock moves") introduce a slightly different phrasing convention from the existing "Suppressed moves (N)" `Disclosure` summary pattern (plain `<p>` text vs. an expandable `Disclosure`), but this is a deliberate, tested distinction per TC-4 ("visibly different text from the suppressed line") rather than accidental drift — not flagged as an issue.
