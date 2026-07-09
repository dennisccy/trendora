# goal-mcp-loop-iter-24 Audit Report

**Date:** 2026-07-09
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

Iteration 24 delivers goal.md's fast-platform mechanical backend pass (items B/C/D/G/H), the item-K
capacity snapshot + `measure-perf.sh` harness, and the `/data` storage card — all byte-identity-clean and
within budget. But it also shipped a **CRITICAL regression the QA PASS missed**: item B's new 1 GB SQLite
`mmap_size` × the new 10+20 connection pool exhausted the `ulimit -v` cap and crashed the first cold
`/api/data` load after every restart (browser-qa UT-16, 2/2) — a direct anti-goal-#8 violation that also
broke required-still-passing J-13 and could take the whole backend down on any deploy. **I root-caused it
(controlled ablation the browser-qa pass had not done), fixed it at the source (`mmap_size_bytes: 0`), and
re-verified the exact cold path end-to-end under the real 6144 MB cap (crash → 471 MB peak, completes).**
The goal is now achieved and the system is materially stronger than before the audit; the one remaining gap
is that the canonical browser-qa J-15 lane must be re-run on a fresh restart to convert my engineering-level
re-verification into the journey-level browser evidence the DoD asks for.

---

## 2. Findings

### Backend Findings

**B1 — CRITICAL (fixed): item B's `mmap_size=1 GB` × the connection pool exhausts the `ulimit -v` cap → cold `/api/data` crashes on every restart.**

The single most important finding. Item B added, per-connection via the `connect` event hook
(`apps/backend/app/db.py:62` — `PRAGMA mmap_size={pragmas.mmap_size_bytes}`), a **1 GB read-mmap window**
(`config.yaml:108`, `mmap_size_bytes: 1073741824`) and sized the pool to `pool_size=10 + max_overflow=20`
(up to 30 connections; `apps/backend/app/db.py:78-79`, `config.yaml:113-114`). A non-zero SQLite
`mmap_size` reserves that many bytes of **virtual address space per connection**. The backend runs under a
`ulimit -v` (RLIMIT_AS) cap of `server.memory_cap_mb = 6144` MB (`incredible_auto_dev/scripts/start-backend.sh:54-55`,
`config.yaml:1218`) — a cap iter-19 sized ONLY against the Python-heap bar prefill (~0.4–0.5 GB retained),
with no accounting for any mmap window. The two collide on the cold `/api/data` path
(`api/data.py:119` → `data_manager.compute_coverage` → `_compute_coverage_uncached` (`data_manager.py:801`)
→ `prices.py:276` `prefilled_bar_cache` → `prices.py:141` `prefill`'s streamed 3.27M-row fetch).

Verification (browser-qa had NOT toggled mmap; I did — the controlled ablation):
- `browser-qa UT-16` reproduced the crash 2/2 on fresh restarts: `MemoryError` in `cursor.fetchmany()`,
  then a fatal PyO3 panic that killed the process; `/proc` showed `VmSize` pinned at exactly 6144 MB while
  `VmRSS` was only ~2.9 GB — the fingerprint of **virtual-address-space** (not physical) exhaustion.
- My `mmap_probe.py` (raw sqlite3, real 1.3 GB DB, no ulimit → cannot crash): at `mmap_size=1 GB` each
  connection adds ~1026 MB VmSize; **6 connections = 6154 MB, already past the 6144 MB cap** before any
  prefill. At `mmap_size=0`: 6 connections add ~12 MB total.
- My `coldpath_repro.py` (the REAL `_compute_coverage_uncached` cold path under `RLIMIT_AS=6144 MB`,
  modelling 5 live pooled connections): **mmap=1 GB → `MemoryError` at exactly 6144 MB VmSize (reproduces
  UT-16); mmap=0 → 471 MB peak, returns the full 19-key coverage payload.** Same run, mmap the only variable.

Fix applied (surgical, root-cause):
- `config.yaml:108` — `mmap_size_bytes: 0` (mmap disabled; SQLite's own default) with an explanatory comment.
- `apps/backend/app/config.py:1682` — `DatabasePragmasCfg.mmap_size_bytes` default `1073741824 → 0` + a
  docstring note stating `mmap_size_bytes × (pool_size + max_overflow)` must stay under the `ulimit -v` cap.
- `apps/backend/tests/test_db.py:325` — the item-B test hard-coded `assert mmap_size == 1073741824` (it
  encoded the dangerous value); changed to `assert mmap_size == 0` with a rationale comment.

Every other item-B pragma (WAL, synchronous=NORMAL, busy_timeout, the 256 MB page cache, temp_store=MEMORY)
is retained — the 256 MB cache is demand-resident, not a virtual reservation, so it carries no per-connection
address-space hazard, and the warm latencies (all 10–100× under budget) are unaffected. The change is
byte-identity-safe: mmap vs pread is purely how pages are read, never what rows are returned.

**B2 — IMPORTANT (fixed): `reports/perf-budgets.md`'s "cold path re-verified, no OOM" claim was false.**

The committed budgets table is the never-regress contract future iterations must re-assert, so a false entry
poisons every later baseline. The iter-24 "Reading the numbers" paragraph
(`reports/perf-budgets.md`) claimed the cold `/api/data` path "was re-verified this iteration … items C/G/H's
query-plan changes did not reintroduce the OOM" — but its cited evidence was a `/api/health` (readiness)
boot, a DIFFERENT code path, and the warm `GET /api/data` 0.0149 s figure is a cache hit, not a cold-boot
number. The actual cold path crashed (B1). This is exactly why the defect passed dev verification and
reached browser-qa before being caught (UX-regression review, "Claimed-vs-actual gap"). Corrected in place:
the paragraph now records the real crash, the confirmed root cause, the fix, and the ablation
re-verification (mmap=0 → 471 MB, OK).

### Frontend Findings

**F1 — GAP (documented, not fixed — pre-existing, P3): `/data`'s `loadOverview` has no retry, so after a backend hiccup the page body and the readiness badge desync.**

`apps/frontend/app/data/page.tsx`'s `loadOverview` fires once on mount with no polling/retry, while the
top-bar `HealthBadge` polls independently. After a crash-and-restart the badge recovers to green "Ready"
while the `/data` body stays stuck on the stale red "Backend unavailable" card until a manual reload
(browser-qa UT-05 recovery-continuation). This is a **pre-existing** design gap that iter-24 did not
introduce — it was merely exposed by the (now-fixed) B1 crash. Out of iter-24's scope (no `/data` retry
affordance was in the spec); worth a dedicated follow-up card (matches the UX reviewer's non-blocking P3
recommendation). Not fixed here — fixing it would be scope creep, and the crash that made it visible is gone.

### Test Findings

**T1 — OBSERVATION: `measure-perf.sh`'s bounded-backfill timing lands on 0 cadence-eligible dates.**

The harness picks a range from `coverage.gaps_preview` (not cadence-filtered), so on an already-warm backend
it resolves to an honest 0-date, 0.23 s no-op (dev Known Issue, accurately labelled). The DoD only requires
"one bounded K-date backfill timing via the jobs API," which it delivers with an honest result. Deferred.

**T2 — OBSERVATION: the readiness cadence-date memo has no lock (reviewer NOTE).**

`apps/backend/app/engine/readiness.py:69` `_cached_warmup_dates` is a module-level single-entry memo mutated
without a lock. Benign: the list rebind is atomic and the derivation is deterministic, so the worst case is a
redundant recompute, never a wrong value. Add a lock only if this is ever tightened. Not fixed (OBSERVATION).

---

## 3. Domain Assessment

The other in-scope items are correctly and honestly implemented — I verified each in source, not just from
the handoff:

- **Item C (index hygiene):** the two redundant `Index(...)` declarations are gone from
  `apps/backend/app/models.py` (only explanatory comments remain at :84/:88/:366); the drop/add runs in a
  guarded, idempotent post-boot step (`db.py:168-182` `_ensure_index_hygiene`, mirroring
  `_ensure_additive_columns`). `EXPLAIN QUERY PLAN` coverage exists (test_db.py) and browser-qa UT-07/UT-08
  confirm coverage/detail values are stable. Dropping a redundant index changes only the plan, never a
  result. Correct.
- **Item D (ticker-filtered fetch):** `filtered_stock_rows` (`snapshot_serving.py:214`) queries
  `ScannerResult` by `run_id` + case-insensitive `ticker IN (…)` instead of deserializing all rows; used by
  `stock_detail_payload` (`:251`) and `watchlist._canonical_rows` (`watchlist.py:62`). Byte-identity proven
  by the existing `test_api_engine.py`/`test_api_watchlist.py` suites passing UNEDITED and by browser-qa
  UT-08 (AAPL detail == leaderboard) and UT-10 (watchlist == leaderboard). Correct.
- **Item G (cheap readiness probe):** `readiness.py:69` memoizes the cadence-date derivation; the per-date
  existence loop is replaced by ONE grouped `select(ScannerRun.asof_date).where(asof_date.in_(cadence_dates))`
  (`:130`). Reported figures unchanged; browser-qa UT-11 confirms the badge + the ≤0.1 s `/api/health` budget
  (0.090–0.104 s). Correct.
- **Item H (N+1 fix):** `_missing_data_diagnostic` (`data_manager.py:249-252`) now issues ONE bulk
  `select(DailyPrice.symbol, DailyPrice.date).where(DailyPrice.symbol.in_(universe))` — bounded to the
  ~122-member universe (no unbounded whole-table scan, anti-goal-#8-safe) — grouped in Python; the gap-diff
  logic is unchanged (byte-identical). My cold-path repro exercised this path (`diagnostic` key present in the
  returned payload) and it completed cleanly. Correct.
- **Item K (capacity):** `compute_capacity` (`data_manager.py:952`) is pure DB introspection — file size via
  `session.get_bind().url.database` + `Path.stat`, three `select(func.count())` row counts, honest all-zero on
  a cold/empty/unresolvable-path DB, recomputes no canonical value — served as an ADDITIVE `capacity` key on
  the existing `GET /api/data` (`api/data.py:140`). Browser-qa UT-01/UT-02/UT-14 confirm the card renders the
  four values (1.22 GB / 3,293,160 / 165,755 / 821,054), human-formatted, each with a plain-language
  definition. Correct.

The core domain discipline the goal cares about — determinism, no-lookahead, byte-identity of every optimized
path, no fabricated numbers — is intact. The regression was purely an **operational resource-budget** miss
(virtual-address-space accounting), not a correctness or evidence-integrity failure; no displayed number
changed, and no ledger/evidence work was touched (correct — this iteration carried no `## Evidence Claim`).

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `config.yaml:108` | `mmap_size_bytes: 1073741824 → 0` (disable the per-connection 1 GB mmap window that exhausted the `ulimit -v` cap) + rationale comment |
| 2 | Critical | `apps/backend/app/config.py:1682` | `DatabasePragmasCfg.mmap_size_bytes` default `1073741824 → 0` + docstring note on the `mmap × pool ≤ cap` invariant |
| 3 | Critical | `apps/backend/tests/test_db.py:325` | test assertion `mmap_size == 1073741824 → == 0` (it had encoded the dangerous value) + rationale comment |
| 4 | Important | `reports/perf-budgets.md` | replaced the false "cold path re-verified, no OOM" prose with the real crash + confirmed root cause + fix + ablation re-verification |
| 5 | — | `docs/handoffs/goal-mcp-loop-iter-24-dev.md` | added an AUDIT CORRECTION banner flagging the two invalidated dev-handoff claims (item B mmap value; the cold-path "no OOM" live-verification) |

Post-fix verification (all run this audit):
- Shipped-config cold path (reads `config.yaml`, no override) under real `RLIMIT_AS=6144 MB`:
  **RESULT: OK — 471 MB peak, full 19-key coverage payload** (before the fix: `MemoryError` at 6144 MB).
- `pytest tests/test_db.py::{test_sqlite_pragmas_applied_on_connect, ...are_config_sourced..., test_pool_size_is_config_sourced, test_is_sqlite_url_detection}` → **4 passed in 0.27s** (confirms the edited assertion passes and the config still loads/applies pragmas correctly after the default change).
- `git diff` re-read: my edits touch ONLY the mmap value/default/test + the perf-budgets prose + the handoff banner — no unrelated code changed. The fix introduces no new escape hatch and silences no error (mmap=0 is SQLite's documented default; WAL + all other pragmas retained; byte-identity preserved).

I did NOT run the full ~10 h 30-year pytest suite or the `loaded_engine`-gated tests (per the phase spec's
own slow-test guidance and the operator memory); the cold-path repro exercises the real prefill directly and
is the decisive evidence.

---

## 5. Recommended Next Step

**Re-run the canonical browser-qa J-15 lane on a fresh restart, then close.** The critical crash is fixed at
the root and re-verified end-to-end at the engine level, so J-13 is unblocked and the anti-goal-#8 violation
is resolved. The one outstanding DoD item is the journey-level browser evidence: bring up both prod services
(`rm -rf apps/frontend/.next`; `start-backend.sh`/`start-frontend.sh`), then load `/data` as the FIRST
request after a fresh restart at least twice (the exact UT-16/UT-06/UT-05 repro path) and confirm the page
renders the coverage + storage + missing-data panels within budget with no crash — converting UT-16/UT-06's
FAIL and UT-05's recovery-continuation to PASS. Once that lane is green, this iteration is shippable. Defer
to follow-up cards: F1 (the `/data` no-retry desync, P3) and T1 (a cadence-aware backfill-timing range in
`measure-perf.sh`). J-16 / item F remain correctly out of scope.
