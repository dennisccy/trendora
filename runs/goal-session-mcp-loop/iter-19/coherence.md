# Iteration 19 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-19
**Date:** 2026-07-07
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

Iter-19 is a regression-fix + hardening iteration (no new Evidence Claim, no new pages, no nav
change — confirmed by the iter spec's "Blueprint conformance" field and by the ui-surface-map's
own summary: "New pages/routes: 0", "Navigation changes: no"). Reviewed: bounded diff was absent, so
`git diff 8f1798be0559154fd8e36fc1504b9ec7dbb39b74` (noise-excluded) plus direct reads of the four
new untracked source files it can't show (`app/error.tsx`, `app/global-error.tsx`,
`lib/sector-label.ts`, `lib/sector-label.test.ts`), the excluded-path `--stat` (only `runs/*` harness
churn + the blueprint's own +2-line iter-19 clarification — no lockfile changes), the blueprint, the
iter spec, and `reports/phase-goal-mcp-loop-iter-19-ui-surface-map.md`.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Daily prices / bars (`seed_loader`/`daily_prices` → `GET /api/stocks/{ticker}/bars`) | OK | `apps/backend/app/engine/prices.py:82-169` — the `_BarCache.prefill`/`bars_asof` rewrite (whole-table `.all()` → streamed column-projected `yield_per` into a lightweight `Bar` `NamedTuple`) stays inside the SAME module, same query shape (`ORDER BY symbol, date`), no new endpoint. Proven byte-identical by new tests `test_prefill_returns_bar_records_matching_plain_query_row_level` and `test_lazy_load_returns_bar_records_matching_plain_query_row_level` (`apps/backend/tests/test_bar_cache.py:221-266`), which assert the prefilled/lazy rows equal a plain reference `SELECT * FROM daily_prices` row-for-row. This is an internal loading-mechanism change re-serving the registered value, not a duplicate computation. |
| Three per-stock scores incl. `sector` (`scoring:score_stocks` → `GET /api/stocks`, `GET /api/stocks/{ticker}`) | OK | `apps/backend/app/engine/scoring.py` untouched this iteration (not in the diff) — `sector` stays null for unmapped names, exactly as the spec requires ("do NOT change the backend"). The frontend change is a display-layer re-format only: `lib/api.ts:283` widens the TS type to `string \| null` (a type correction reflecting the field's real nullability, not a new value), and every consumer reads the field through the ONE new shared helper `lib/sector-label.ts` (`sectorLabel`/`compareSectors`) rather than recomputing or re-fetching it — `app/stocks/page.tsx:96,361,412,885`, `app/stocks/[ticker]/page.tsx:182`, `app/scanner-runs/[runId]/page.tsx:212`. Confirmed exhaustive: `grep -rn "StockRow" apps/frontend` shows `StockRow` used in exactly these three page files plus `lib/api.ts`/`lib/sector-label.ts`, and every `.sector` access on a `StockRow` in those three files goes through the shared helper. (`components/return-attribution.tsx:52`'s `row.sector` is a DIFFERENT, pre-existing nullable type — `PerStockRow.sector: string \| null` at `lib/api.ts:798`, already null-guarded by a ternary before this iteration and untouched by this diff — not a `StockRow` consumer, no relation to this fix.) |
| Evidence status / certified-claim (`referee:certify_edge` / `evidence:build_evidence_payload` → `GET /api/evidence`) | OK (untouched) | No referee/ledger/evidence files appear in the diff; the iter spec explicitly declares no Evidence Claim this iteration and the post-decompose gate passed automatically. Both ledgers stay byte-identical. |
| "Unassigned" sector label | Not a new contract value | It is a pure display re-format of the EXISTING registered `sector` field's null state (`lib/sector-label.ts:18-19` `sectorLabel(sector) = sector ?? "Unassigned"`), applied identically everywhere via one shared helper — not a new computed metric, so no Data Contract registration is needed (skill Part A.3: re-labeling for display is not a violation). |

No duplicate computation, no non-canonical source, no unregistered new value found.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/stocks` (Sector sort/filter fix) | OK | Pre-existing canonical home (blueprint nav skeleton: `Stocks /stocks`); no route/shell change. `components/sidebar.tsx` not in the diff. |
| `/stocks/{ticker}`, `/scanner-runs/{runId}` (sector chip/column re-format) | OK | Pre-existing row-reached homes per blueprint; no route/shell change. |
| `app/error.tsx` (route-level error boundary) | OK — not a nav surface | Renders IN PLACE of the page inside the existing root layout's `{children}` slot (confirmed by reading the file: no own `<html>/<body>`, no competing nav) — the sidebar/header from `app/layout.tsx` keep rendering around it. This is Next.js App Router error-boundary infrastructure, not a navigable page, so the ≤2-click reachability rule does not apply to it (nothing to reach — it activates automatically on an uncaught exception). Matches the blueprint's own iter-19 clarification ("route-level Next.js error infrastructure, not nav surfaces"). |
| `app/global-error.tsx` (root error boundary) | OK — sanctioned exception, not a parallel shell | This file DOES render its own bare `<html>/<body>` with no Sidebar/nav — the one case that could look like Part B.4 "parallel shell." Judged not a violation: Part B.4 exists to catch a new *feature* inventing a competing nav/layout for content that belongs in the shared shell. `global-error.tsx` is the opposite — a last-resort fallback that Next.js requires to activate ONLY when the root layout itself throws, i.e., exactly when the shared shell is broken and cannot be depended on. It has no navigational purpose, backs no entity with a home in the IA, and is unreachable by any user action other than a root-layout crash. The blueprint's iter-19 clarification explicitly sanctions this ("no new surfaces... not nav surfaces"). |
| Nav skeleton / sidebar | Unchanged | `components/sidebar.tsx` does not appear in the diff; ui-surface-map confirms "Navigation changes: no". No new pages this iteration (ui-surface-map: "New pages/routes: 0"). |

No hidden feature, no undiscoverable route, no duplicate home, no parallel shell.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The "Unassigned" label is sourced from one shared constant (`UNASSIGNED_SECTOR` in
  `lib/sector-label.ts`) and reads identically on `/stocks` (cell + filter option), `/stocks/{ticker}`,
  and `/scanner-runs/{runId}` — no formatting drift observed, noted here only as a positive
  confirmation, not an issue.
- This iteration's blueprint update was itself additive and correctly scoped: the only change to
  `runs/goal-session-mcp-loop/state/blueprint.md` is the +2-line "iter-19 clarification" paragraph
  appended at the end (confirmed via the excluded-path `--stat`), consistent with "no re-approval
  requested" in the iter spec's Blueprint-conformance field.
