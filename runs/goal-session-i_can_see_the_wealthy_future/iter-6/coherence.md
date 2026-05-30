**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-6 (Walk-forward forward-testing + System Health, J-09/J-10)

**Session:** i_can_see_the_wealthy_future · **Iteration:** 6 · **Auditor:** coherence-auditor
**Snapshot compared:** `git diff 9bb03b98116adfca1de1e6d04d3384b84fe62323` + uncommitted/untracked (`git status`)

This iteration implements an **already-registered** Data Contract row (forward-return aggregates) in
its exact named module/function/endpoint/table, reads all canonical groupings from the stored
snapshot verbatim, re-formats a single API payload on the frontend, and places the surface in its
existing IA home. No objective Part A or Part B violation found.

---

## Step 1 — Data Contract check (the "numbers don't match" gate) → PASS

**Registered row implemented exactly as contracted.** Blueprint Data Contract: *Forward-return
aggregates* → computed by `app.engine.forward_testing:compute_forward_aggregates` → served by
`GET /api/system-health`, with the append-only `forward_returns` table. Every name matches:

- Module/function: `compute_forward_aggregates` at `apps/backend/app/engine/forward_testing.py:360`. ✅
- Endpoint: `system_health.py:26` defines `GET /system-health`; `apps/backend/main.py:63` registers it
  with `prefix="/api"` → canonical `GET /api/system-health`. The view returns
  `compute_forward_aggregates(...)` **verbatim** (`system_health.py:47`) — no recompute in the view. ✅
- Table: `ForwardReturn`/`forward_returns`, **separate append-only** table keyed
  `UniqueConstraint(run_id, symbol, horizon)` (`models.py:196`+). INSERT-only; the snapshot is never
  mutated. ✅
- Accessor: `bars_after` (date > d) + `close_on` (latest bar date ≤ d) added to the canonical price
  module `prices.py:44`/`:60` — the strict forward inverse of `bars_asof`. ✅

**No duplicate computation (Part A1).** `compute_forward_aggregates` READS the stored canonical values
verbatim and groups by them — it re-derives **no** score/bucket/setup:
- bucket from `res.leadership_bucket` (`forward_testing.py:396`, "verbatim — no re-bucketing"),
- setup from `res.setup_status` (`:397`), sector `res.sector` (`:398`), rank `res.rank` (`:399`),
- regime label from the stored `scanner_runs.regime_label` (`:383`, `:400`).
No `to_bucket`, `classify_setup`, `score_stocks`, or `score_regime` is imported or called in the
aggregation path. Imports are only `bars_after/bars_asof/close_on/latest_data_date`, `run_scan`,
`ALL_STATUSES` (used solely as a display-ordering vocabulary at `:441`), and the three models. ✅

**No non-canonical source (Part A2).** Frontend `fetchSystemHealth` hits exactly
`/api/system-health?horizon=` (`apps/frontend/lib/api.ts:339`). The page consumes that single payload
and re-formats only: `fmtPct` scales/rounds (`page.tsx:29`), `mean_excess`/`by_bucket`/`by_setup`/
`by_regime`/`control_group` are read straight off `data.*` (`:208`, `:220`–`:236`), and
`bucketVariant(row.bucket)` merely colours the stored bucket label (`:275`). No client-side return,
excess, or bucket math anywhere. ✅

**No unregistered new value (Part A4/A5).** Everything displayed (by-bucket return, excess vs
SPY/QQQ, by-setup, by-regime, control-group cohorts, per-figure `n`, survivorship label) maps to the
one registered forward-return-aggregates row — no new contract row needed, none introduced. The
realized `forward_return` (`forward_testing.py:98`) is that row's implementation math, not a synonym
of any existing canonical score. ✅

**No re-pointing of existing canonical paths.** `git diff` confirms `app/api/{dashboard,stocks,
sectors,themes,runs}.py` and `app/engine/{scoring,buckets,setups,regime}.py` are **untouched** — the
backfill `calls` the idempotent `run_scan` (`forward_testing.py:198`), recomputing nothing. J-01–J-08
read paths are unchanged. The added walk-forward cadence runs surface through the same canonical
`/api/runs` from stored snapshots (more rows from one source — the blueprint's intended immutable
history, not a second source). ✅

## Step 2 — Information Architecture check → PASS

- **Canonical home, no new route.** `/system-health` is the blueprint IA home for J-09/J-10. The page
  graduates an existing EmptyState stub in place — no new route, no `blueprint.reapproval-requested`
  needed (correctly omitted). ✅
- **Reachable in 1 click.** Persistent sidebar carries `{ href: "/system-health", label: "System
  Health" }` (`apps/frontend/components/sidebar.tsx:32`) — top-level, 1 click. ✅
- **No parallel shell.** The page uses the established design system — shared `Card`, `PageHeading`,
  `Badge`/`bucketVariant`, `EmptyState`, `tabular-nums`, warn/pos/neg palette tokens — not a new
  layout. ✅
- **No duplicate home.** No second evidence/health page introduced. ✅

## Step 3 — Subjective observations (advisory only; not blocking)

- `close_on` (`prices.py:60`) is a new accessor, but it is **co-located in the canonical
  `app.engine.prices` module** and explicitly documented as the single-bar form of
  `bars_asof(...)[-1].close` (same `date ≤ d` boundary) — an accessor optimization, not a second code
  path for a contract value. No drift; noted only for transparency.
- `config.yaml` changes `walk_forward.asof_cadence` weekly→quarterly and adds `default_horizon` +
  `control_group.{seed,top_n,peers_per_sector}` (additive, config-sourced — consumed via
  `wf.default_horizon`/`cg.*`, no literal in calc code). Matches the blueprint's additive-keys note.

---

### Conclusion

No Part A (Data Contract) or Part B (Information Architecture) violation. One value, one computing
module, one serving endpoint; stored canonical buckets/setups/sectors/regime read verbatim; a single
payload re-formatted on the frontend; the surface lives in its existing 1-click IA home with no
parallel shell or duplicate home. **COHERENCE-PASS.**
