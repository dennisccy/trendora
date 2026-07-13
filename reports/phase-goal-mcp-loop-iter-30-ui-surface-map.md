# Phase goal-mcp-loop-iter-30 — UI Surface Map

**Phase:** goal-mcp-loop-iter-30
**Date:** 2026-07-13
**Written by:** ui-impact-analyst

---

## Context

16 files changed (per the dev handoff's "Files Changed"). Classified:

| File | Category | UI Impact |
|------|----------|-----------|
| `apps/frontend/app/research/registry/page.tsx` (NEW) | frontend-direct | Direct — the new page itself |
| `apps/frontend/app/research/page.tsx` | frontend-direct | Direct — new hub section |
| `apps/frontend/lib/api.ts` | frontend-direct | Direct — `fetchRegistry()`, the page's only data source |
| `apps/frontend/lib/registry.ts` (NEW) | frontend-direct | Direct — types consumed by the page |
| `apps/backend/app/api/registry.py` (NEW) | backend-api | Indirect — consumed by the new page (confirmed: `fetchRegistry` in `lib/api.ts` calls `GET /api/research/registry`) |
| `apps/backend/app/engine/registry.py` (NEW) | backend-internal | None directly — feeds the API endpoint above, not itself reachable |
| `apps/backend/main.py` | backend-internal | None directly — router registration plumbing; shared-file regression risk only |
| `apps/backend/app/config.py` | config | None directly — new `RegistryCfg` field |
| `config.yaml` | config | None directly — `evidence.registry.{path,enforce}`; `enforce:true` activates a backend-only gate |
| `project-extensions/gates/verify_claim.py` | backend-internal | **None, ever** — a CLI gate script in the automated dev pipeline, not part of the running web app |
| `scripts/automation/run-goal.sh` (framework infra) | config | None — env-var plumbing for the pipeline, not the product |
| `runs/goal-session-mcp-loop/state/pre-registrations.jsonl` (NEW) | backend-internal (data) | Indirect — its 11 rows are exactly what the new page's table renders, verbatim |
| `apps/backend/tests/test_registry.py` (NEW) | backend-internal (test) | None |
| `apps/backend/tests/test_api_registry.py` (NEW) | backend-internal (test) | None |
| `apps/backend/tests/test_gate_registry_enforcement.py` (NEW) | backend-internal (test) | None |
| `apps/backend/tests/test_config.py` | backend-internal (test) | None |

Net: this is a **full-stack** change — one new page + one new endpoint it directly consumes + one modified
existing page (the hub) — bundled with a **backend-only governance mechanism** (the gate cross-check) that
has no UI surface by design, now or in any planned future iteration (it is a pre-check inside a CLI script,
never reachable from a browser). The nine required-still-passing journeys (J-01/02/03/05/06/07/08/09/11)
all read `GET /api/evidence`, which no file in this iteration touches; the one shared-file regression risk
worth a live check is `main.py`'s new router import/registration.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research/registry` | `RegistryPage` — populated table view (`apps/frontend/app/research/registry/page.tsx`) | New page | J-18/B-901: users can now browse every registered/tested hypothesis with its economic rationale and audit-trail date | Navigate to `/research/registry` (directly, or via the hub card). Confirm the table renders exactly 11 rows, and that every row shows non-empty Selectors chips, non-empty Rationale text, a formatted Registered date, a non-empty Source string, and a Status badge — none blank or "—". |
| `/research/registry` | `SelectorChips` — the Selectors column | New component | Selectors must render readably (key=value chips), not raw JSON, per the plan's Visual Requirements | On the row with id `factor-vcp_contraction-d10-h60`, confirm the Selectors cell shows separate chips reading `kind=factor`, `factor=vcp_contraction`, `decile=10`, `horizon=60`, `direction=positive` (5 chips, no raw `{...}` JSON text visible). On the row with id `combination-atr_pct-rs_spy_3m-h20`, confirm the `condition` chip shows `condition=rs_spy_3m:top:quintile+atr_pct:bottom:tertile` (two array legs joined with `+`, not shown as separate array brackets). |
| `/research/registry` | `StatusBadge` — Status column + "backfill" pill | New component / anti-goal check | Anti-goal #1 (critical): a value must never render as proven/confident without a passing certified-claim; registry status is process state, not proven-ness, and must be visually distinguishable from `/evidence`'s PASS/FAIL badges | For all 11 rows, confirm the Status badge text reads only "tested" or "closed" — never "Proven", "Not yet proven", or any confidence wording — and renders in a neutral gray/muted badge style (not the green/red styling `/evidence`'s PASS/FAIL badges use). Confirm every row additionally shows a separate small "backfill" pill immediately beside its status badge (all 11 rows have `registered_by: backfill`). |
| `/research` | New "Governance & process" section + "Pre-registration registry" card | Added navigation | Makes `/research/registry` discoverable per the J-18 DoD ("reachable from `/research` in ≤2 clicks") | Open `/research`. Scroll below the existing 10-card lab grid and confirm a "Governance & process" heading appears with exactly one card, titled "Pre-registration registry", containing a book icon and the description text ending "...The gate refuses to certify anything that isn't here." Click the card and confirm the browser navigates to `/research/registry`. |
| `/research` | Existing `RESEARCH_LABS` grid (10 lab cards) | Regression check (must NOT have changed) | `lib/research-labs.ts`'s array is a fixed reading-order contract (J-113); the plan explicitly required it stay untouched | On `/research`, count the cards in the main lab grid (above the new Governance section) and confirm there are still exactly 10, in the same order/labels as before this iteration (no lab added, removed, or renamed). |
| `/research/registry` | Fetch-error card (`Card` "Backend unavailable") | New state / error handling | Anti-goal (critical): resilience to data-shape/service failure — page must degrade gracefully, never crash blank | Stop the backend process. Load `/research/registry` directly. Confirm a single contained card renders reading "Backend unavailable" and "The pre-registration registry could not load from the API. Confirm the backend is running and reload." — not a blank white page or an unhandled application error. Confirm the page's own header/title still renders above the error card. |
| `/research/registry` | Empty state (`RegistryEmptyState`, `data-testid="registry-empty"`) | New state / data-shape resilience | DoD: "Missing/empty registry file: loader returns `[]`, endpoint returns 200 with an empty list, page shows an honest empty state — none crash" | With the backend running, temporarily rename `runs/goal-session-mcp-loop/state/pre-registrations.jsonl` (or point `TRENDORA_REGISTRY_PATH` at a nonexistent path) and restart the backend. Load `/research/registry` and confirm a card reads "No registrations yet" with the explanatory paragraph about what will appear once something is registered — not an error card, not a crash. Restore the file and restart the backend afterward. |
| `/research/registry` | Loading skeleton (`RegistrySkeleton`) | New state | Honest loading state before the fetch resolves | Open browser devtools, throttle the network to "Slow 3G" (or similar), then load `/research/registry`. Confirm 8 pulsing placeholder bars render inside a card immediately, and are fully replaced by the real table once the fetch completes (no flash of an empty table, no skeleton left stuck after data loads). |
| `/evidence` | Certified-claims ledger list (unchanged source file) | Regression check | Required-still-passing journeys read `GET /api/evidence`; `apps/backend/main.py` (shared app-wiring file) was edited this iteration to register the new registry router | Open `/evidence`. Confirm it still lists the same 7 certified claims, each with its hypothesis, out-of-sample verdict, and registration date unchanged from before this iteration (per the dev handoff's smoke test: `proven_signals: {}`, matching the frozen golden). Confirms the new router import/registration in `main.py` did not break app startup or the existing evidence surface. |

<!-- Change Type key: "New page"/"New component"/"Added navigation"/"New state" = genuinely new UI surface
     shipped this iteration. "Regression check" = the surface's own source is unchanged, but a shared file
     it depends on (main.py's router table, or the RESEARCH_LABS reading-order contract) was touched or is
     adjacent to what was touched, so it must be re-confirmed live rather than assumed unaffected. -->

---

## Backend-Only Changes (No UI Impact)

- `project-extensions/gates/verify_claim.py` — the pre-registration cross-check inserted before
  `tools.verify_edge(...)`. This is a CLI script invoked by the automated goal-mode pipeline between
  iterations to certify a proposed Evidence Claim — it is never invoked by, or reachable from, the running
  Trendora web application. No UI surface exists for it today, and none is planned; a blocked claim's only
  observable trace is that later iteration's own dev/review handoff text, not anything in the product UI.
- `apps/backend/app/engine/registry.py` — the pure loader (`resolve_registry_path`, `load_registrations`,
  `claim_selectors`, `match_registration`). Not itself an HTTP-reachable surface; it is imported directly by
  both `app/api/registry.py` (the endpoint the new page reads) and `verify_claim.py` (the gate). No
  independent UI impact beyond the endpoint it feeds, which is already covered in the surface table above.
- `apps/backend/main.py` — one new import line and one `include_router(registry.router, prefix="/api")`
  call beside the existing `evidence.router` line. Plumbing only; its only UI-relevant effect is making
  `GET /api/research/registry` reachable at all, which is exercised by the surface-table rows above.
- `apps/backend/app/config.py` — new `RegistryCfg(BaseModel)` (`path: str`, `enforce: bool = False`) and
  the `EvidenceCfg.registry` field. Read only at process start / by the gate script; no page or API
  response surfaces this schema to a browser.
- `config.yaml` — new `evidence.registry.{path,enforce}` block (`enforce: true`, flipped only after
  backfill verification). Configures the backend-only gate above; no UI reads this value.
- `scripts/automation/run-goal.sh` (real path `incredible_auto_dev/scripts/automation/run-goal.sh`) —
  exports `TRENDORA_REGISTRY_PATH` alongside `LEDGER_PATH`/`STAGING_LEDGER_PATH` at both dispatch sites.
  Pipeline/process-launch plumbing, not part of the product; invisible to any browser.
- `runs/goal-session-mcp-loop/state/pre-registrations.jsonl` — the new 11-row backfilled data file itself.
  Not a UI surface (it's a data file on disk), but note it is the exact content rendered verbatim by the
  `/research/registry` table above — any future edit to this file changes what that page shows.
- `apps/backend/tests/test_registry.py`, `test_api_registry.py`, `test_gate_registry_enforcement.py`,
  `test_config.py` — test files; no UI surface by definition.

---

## Summary

- **Frontend surfaces changed:** 2 (`/research/registry` new page, `/research` hub page updated)
- **New pages/routes:** 1 (`/research/registry`)
- **Modified components:** 2 (`app/research/page.tsx` — new Governance section; `lib/api.ts` — new
  `fetchRegistry()` supporting the new page); plus 4 new page-local sub-components inside the new page
  itself (`SelectorChips`, `StatusBadge`, `RegistryTable`, `RegistrySkeleton`/`RegistryEmptyState`)
- **Navigation changes:** yes — one new discoverable card on the `/research` hub (no sidebar/persistent-nav
  change)
- **Backend-only changes:** 11 files (`registry.py` loader, `main.py` wiring, `config.py`, `config.yaml`,
  `verify_claim.py` gate, `run-goal.sh`, the backfill data file, + 4 test files)
