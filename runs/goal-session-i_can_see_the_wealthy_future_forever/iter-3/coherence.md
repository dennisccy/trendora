**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-3 (J-17 Data Manager)

- **Session:** i_can_see_the_wealthy_future_forever
- **Iteration:** 3 (`goal-i_can_see_the_wealthy_future_forever-iter-3`)
- **Audited diff:** `git diff a7715c6ea341942ff37c8d8a101685237fff619d` + untracked (`api/data.py`, `engine/data_manager.py`, `data_providers/stooq_provider.py`, `app/data/page.tsx`)
- **Auditor:** coherence-auditor

No objective Data-Contract or Information-Architecture violation found. The iteration adds the J-17 Data Manager exactly as the blueprint pre-approved it: a new `/data` page under the existing shell, one additive sidebar entry, and an engine that **orchestrates** the registered canonical paths instead of re-implementing any computed value. No advisory (WARN) items of note.

---

## Step 1 — Data Contract (the "numbers don't match" gate) → PASS

The single biggest coherence risk for this iter (a *second* scan/return code path) is avoided.

- **Backfill reuses the canonical compute paths — no duplicate computation.** `data_manager._do_backfill` calls the registered `scanner.run_scan` (`apps/backend/app/engine/data_manager.py:254`) then `forward_testing.backfill_run_forward_returns` (`:255`). No score/bucket/return math is implemented in `data_manager.py`. The new snapshots + forward returns are the **same canonical values via the same modules** already in the contract (Data Contract rows "Scanner run snapshot" and "Forward-return aggregates") — registered, not re-registered.
- **Coverage is new descriptive metadata, not a re-derivation of any canonical value.** `compute_coverage` (`data_manager.py:73-101`) reports price-range / distinct-symbol-count / snapshot-date set / backfill gaps — read-only over `DailyPrice` + `ScannerRun`. The trading calendar is derived from raw SPY seed bars (`_trading_days`, `:63-70`), not from a score/return. These are registered as **new descriptive values** in the refined J-17 Data Contract row (`blueprint.md`) — no synonym/duplicate of an existing score, bucket, or return.
- **Fetch ingests raw bars, computes nothing.** `_do_fetch` (`:207-240`) persists only NEW `(symbol, date)` `DailyPrice` rows from the live provider; `_existing_dates` (`:195-204`) guarantees committed seed bars are never overwritten. Raw price ingestion is not a canonical computed value.
- **Serving paths are canonical and read-only.** `GET /api/data`, `POST /api/data/jobs`, `GET /api/data/jobs/{job_id}` (`apps/backend/app/api/data.py:45-87`) are thin wrappers over `compute_coverage` / `recent_runs` / `get_job` — the exact endpoints registered in the updated J-17 row.
- **Frontend re-formats only; no client-side recompute and no divergent source.** `lib/api.ts` adds `fetchDataCoverage` → `/api/data`, `startDataJob` → `/api/data/jobs`, `fetchDataJob` → `/api/data/jobs/{id}` (`apps/frontend/lib/api.ts:570-679`); the page renders server values verbatim (`app/data/page.tsx` CoveragePanel/JobProgressPanel/RunHistoryPanel). Critically, the new dates flow through the **single canonical run-list source**: the page calls `refresh()` which re-runs `asof-provider.load()` → `fetchRuns()` → `GET /api/runs` (`components/asof-provider.tsx:47-67`). No parallel run-list fetch was introduced.

## Step 2 — Information Architecture (the "where do I find it" gate) → PASS

- **Navigation path exists (1 click).** One additive entry `{ href: "/data", label: "Data Manager", icon: Database }` added to the persistent sidebar `NAV` (`apps/frontend/components/sidebar.tsx:39`). Reachable from every page in 1 click — well within the ≤2-click rule.
- **Canonical home, no parallel shell.** `/data` is the blueprint-approved home for J-17 (IA nav skeleton + journey-homes table). The page lives in the standard app shell using design-system primitives (`PageHeading`, `Card`, `EmptyState`, `Badge`, `Select`); it invents no layout/nav of its own.
- **No duplicate home.** `/data` is the first and only home for J-17; no existing entity gets a second page.
- **Blueprint updated as instructed, not drifted.** `blueprint.md` flips the J-17 IA + journey-homes + Data-Contract rows from `⛔ NOT BUILT` to `built iter-3` and fills in the real module/endpoint names. This is the spec-mandated refinement of an already-approved home — an additive sidebar entry under the existing skeleton, **no nav-skeleton change, no re-approval**.

## J-18 "exactly one date selector" (critical invariant #5) → PRESERVED

The explicitly-flagged risk for this iter is handled exactly as the spec required:

- The `/data` date inputs (`start`, `end`) are local `useState` job parameters (`app/data/page.tsx:56-57`), **never** bound to `useAsOf`. The page consumes only `refresh` from the global provider (`:54`).
- `refresh()` is additive — it re-fetches the available `dates`/`latest` only and **never changes the user's `asOf` selection** (`asof-provider.tsx:29-32`, `:66-69`). No second viewing date state is created.
- Backend reinforces this: `api/data.py:14-16,36-38` documents the date inputs as job parameters, and the router never touches the as-of read path.

## Step 3 — Subjective / advisory (WARN) → none

- Entity labelling is consistent ("Data Manager" in the sidebar, page heading, and run-history; "Backfill snapshots / Fetch EOD prices / Fetch + backfill" used uniformly).
- Coverage/progress figures use the shared `num` tabular style and the established status→palette mapping (`statusVariant`, `app/data/page.tsx:34-47`).
- All new displayed values are registered in the Data Contract, so there is no "unregistered-but-new value" note to carry forward.
- Config tunables (`data_manager.live_provider/max_range_days/gap_preview/run_history_limit`, `config.yaml`) keep job/display caps out of the orchestration code — consistent with the no-magic-numbers invariant (noted for completeness; not a coherence axis).

---

**Conclusion:** The product stays coherent — one shell, one nav home per feature, and one source of truth for every displayed value. The Data Manager grows the dataset by orchestrating the registered canonical paths (no second computation), serves new descriptive values from their canonical endpoints, and preserves the single global as-of control. **COHERENCE-PASS.**
