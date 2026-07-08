# Iteration 20 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-20
**Date:** 2026-07-08
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Per-date availability (`symbols_with_bars` / `total_symbols` / `snapshot_exists`) | OK | Still computed solely by `data_manager.compute_availability` and served solely by `GET /api/data/availability` (backend `app/api/data.py` untouched this diff). `apps/frontend/components/availability-heatmap.tsx:15,703-740` re-presents the SAME payload (legend split, color tokens, copy) — no new fetch added. Confirmed single frontend call site: `apps/frontend/lib/api.ts:2405` (`fetchAvailability` → `getJSON("/api/data/availability", …)`); no second call site exists in source (grep across `apps/frontend/**/*.{ts,tsx}` excluding build output). New backend regression test `apps/backend/tests/test_data_manager.py:104-129` (`test_compute_availability_byte_identical_after_fetch_scope_widening`) pins the exact byte-identical output, directly enforcing the "re-format only" rule going forward. |
| Generic Fetch job target symbol set (internal job wiring, not a Data-Contract-registered displayed value) | OK | `apps/backend/app/engine/data_manager.py:2964` repoints `_run_job`'s generic-fetch branch from `all_seed_symbols(cfg)` to `price_load_symbols(cfg, seed_dir)` (import at `:76`, replacing the old `all_seed_symbols` import). This is **not** a new computation: `price_load_symbols` is the pre-existing `seed_loader.py` union helper the blueprint's iter-18 clarification already documents as what `load_prices` uses (`all_seed_symbols ∪ read_pool`). The iteration consolidates a second call site onto the SAME existing canonical helper rather than adding a divergent one — the opposite of the "numbers don't match" failure mode. `benchmark_pipeline.py` and the five backend test files mirror the same rename for their monkeypatch targets/expectations only. |
| Evidence status / certified-claim (ledger) | OK — untouched | `git diff <snapshot-sha>` and `git status` show zero changes to `certified-claims.jsonl` or `staging-ledger.jsonl`. Matches the iter spec's explicit "Out of Scope: any `## Evidence Claim` / referee submission / ledger write" and "Data-contract additions: None." |
| New displayed value check | OK — none introduced | ui-surface-map and the diff agree: 0 new computed/displayed values. The two legend group labels and the re-worded tooltips are copy over the existing three fields above, not new data. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/data` (Data Manager) — Fetch-scope wiring + availability-legend re-encode | OK | No new route; blueprint already registers `/data` as J-13's canonical home (feature-homes table, J-13 row). `apps/frontend/components/sidebar.tsx` is untouched by this diff and still contains `{ href: "/data", label: "Data Manager", icon: Database }` at line 44 — 1 click from the top-level persistent nav. |
| "Expand universe" job option removal | OK — clean deletion, no orphaned/duplicate surface | `apps/frontend/app/data/page.tsx`: the `<option value="expand">`, `isExpandKind`, `sourceIneligibleForExpand`, the market-cap-ineligibility alert block, and the entire `ExpandScreenResult` component are deleted (diff hunks at `:432-438`, `:448-453`, `:2065-2069`, `:2135-2187`, `:2470-2536` old-numbering). Post-change grep of `page.tsx` for "expand" (case-insensitive) returns exactly one hit — `:769`, "newly-expanded members" in the unrelated Rebuild-snapshots hint text — confirming no dangling reference and no parallel shell left behind. |
| New pages/routes this iteration | OK — zero | ui-surface-map's own summary states "New pages/routes: 0 … Navigation changes: no," consistent with the diff (`sidebar.tsx`, router config unchanged). |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `README.md`'s AUTO:capabilities block was also updated this diff to describe two capabilities (the Sector-column sort fix / "Unassigned" bucket, and the contained `error.tsx`/`global-error.tsx` recovery) that the blueprint's iter-19 clarification attributes to iter-19, not this iteration's J-13 scope. Reads as documentation catch-up rather than a defect — it does not touch the IA or the Data Contract, so it is not a coherence violation, just noted for the record.
- The blueprint's new iter-20 clarification paragraph (`runs/goal-session-mcp-loop/state/blueprint.md`, +2 lines) was checked in isolation (`git diff <snapshot-sha> -- runs/goal-session-mcp-loop/state/blueprint.md`) and accurately matches the diff: no new computing module, no new endpoint, no nav-skeleton change, all three sub-claims (Fetch scope / legend / Expand removal) verified against the actual code above.
