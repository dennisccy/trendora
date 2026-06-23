# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48
**Date:** 2026-06-22
**Agent:** developer
**Status:** complete

## What Was Built
Completed the iter-47 J-105 streaming fix. iter-47 streamed the seven `select(ForwardReturn)…all()` reads but
left the **sibling `select(ScannerResult)…all()` reads** in the same two builders unstreamed — each
materializing ~609K ORM rows. Because **Factor Lab is UNCACHED** (it recomputes the observation set every
request), J-25 still HTTP-500'd with a `MemoryError` at `research.py:216` on the live 3.47 GB DB;
`_combination_observations` (line 421) was a latent cold-miss OOM masked only by the EventStudyCache hit.

This iteration streams both ScannerResult-side reads with `.yield_per(cfg.research.read_batch_size)` over the
**full ScannerResult ORM row** (NOT a narrow column projection — `_extract_factor_value` reads `record_json`
for component factors), keeping every served figure byte-identical. The Factor Lab now serves HTTP 200 with
real figures on the full live dataset, restoring J-25 and closing J-104/J-105.

- `_factor_observations` (research.py:~216) — the unstreamed `select(ScannerResult).where(run_id.in_(runs_with_fr)).all()`
  is now `.yield_per(batch)`-streamed over the full ORM row.
- `_combination_observations` (research.py:~421) — same `.yield_per(batch)` streaming over the full ORM row.
- **Ordering is `(run_id, id)`, NOT a bare `id`.** See "Important ordering decision" below — this is both the
  byte-identical prior order AND the disk-safe order.
- Byte-identity tests added to `tests/test_research_streaming.py`.

### Important ordering decision (deviation from the literal spec wording, with stronger justification)
The spec/plan said "add `.order_by(ScannerResult.id)`". During live verification this introduced a NEW failure:
a bare `ORDER BY id` forces `USE TEMP B-TREE FOR ORDER BY` over ~598K rows (confirmed via `EXPLAIN QUERY PLAN`),
which spills a temp file to a disk that is currently at **93 % full (4.3 GB free)** → the very first probe
returned `500 sqlite3.OperationalError: database or disk is full` (a NEW environmental fault, not the old
MemoryError).

Investigation showed the prior implicit `.all()` order on the `run_id IN (…)` filter is **`(run_id, id)`**, not
global `id` order — SQLite walks the `ix_scanner_results_run_id` index, so rows already arrive grouped by run_id
then id. Verified on the live DB: `SELECT id … WHERE run_id IN (…)` (no order_by) == `… ORDER BY run_id, id`
exactly. So the **byte-identical** prior order is `(run_id, id)`, and ordering by `(run_id, id)` **rides that same
index → NO temp-B-tree sort → NO disk spill** (`EXPLAIN QUERY PLAN` shows only `SEARCH … USING INDEX
ix_scanner_results_run_id`, no `USE TEMP B-TREE`). I therefore used `.order_by(ScannerResult.run_id,
ScannerResult.id)` in both builders. After the change, the same default `GET /api/research/factor-lab` request
that 500'd serves **200**. This is strictly better than the literal `id`-only order: same byte-identity, no disk
fault. Live decile/rank-IC figures are identical between the two order variants (the column-factor n_total,
rank_ic, and D1/D10 means matched exactly), confirming byte-identity is preserved.

## Files Changed
- `apps/backend/app/engine/research.py` — `_factor_observations` and `_combination_observations`: stream the
  ScannerResult side with `.yield_per(batch)` over the full ORM row + `.order_by(run_id, id)`; `record_json`
  preserved; reuse the existing `cfg.research.read_batch_size` (no new config key, no magic number).
- `apps/backend/tests/test_research_streaming.py` — added a component-bearing fixture (`component_engine`,
  `record_json` carries real `leadership.components.rs_spy_3m.raw` + `risk.components.atr_pct.raw` blocks) and
  byte-identity / chunk-independence proofs for both ScannerResult-side builders: streamed-vs-eager-`.all()`
  reference, batch=1 vs huge, a COLUMN factor (`leadership_score`) AND a COMPONENT factor (`rs_spy_3m`, reads
  `record_json`), as-of / all-history, the full `compute_factor_lab` / `compute_factor_combination` payloads,
  and a zero-N cohort.

## ScannerResult / ScannerRun `.all()` audit (required by spec)
Grepped every `.all()` and every `select(ScannerResult)` / `select(ScannerRun)` in research.py. Status after fix:

| Site (line ~) | Builder | Read | Verdict |
|---|---|---|---|
| 216 → fixed | `_factor_observations` | `select(ScannerResult).where(run_id.in_(runs_with_fr))` | **NOW STREAMED** `.yield_per(batch)` + `.order_by(run_id, id)` (the live OOM site — uncached) |
| 421 → fixed | `_combination_observations` | `select(ScannerResult).where(run_id.in_(runs_with_fr))` | **NOW STREAMED** `.yield_per(batch)` + `.order_by(run_id, id)` (latent cold-miss OOM) |
| ~215 | `_factor_observations` | `select(ScannerRun).where(id.in_(runs_with_fr))` | bounded to `runs_with_fr` (the FR-bearing runs, ~hundreds), NOT the full table — left as-is per spec |
| 1533 | `_regime_setup_pattern_observations` | `select(ScannerResult.<cols>).where(run_id.in_(runs_with_fr)).order_by(id)` | already column-projected + `yield_per`-streamed (iter-47) |
| 1771 | `_recovery_turn_observation_set` | `select(ScannerResult).where(run_id.in_(runs_with_fr)).order_by(id)).all()` | run-id-bounded to SIGNAL dates only (a small subset) AND cache-served (`recovery_turn_edge_cached`) — left as-is |
| 2378 | `_severity_velocity` builder | `select(ScannerRun).where(id.in_(runs_with_fr))` | bounded to `runs_with_fr`, not the full table — left as-is |
| 833 / 986 / 2044 | misc | column-projected `select(<cols>)` reads | bounded / projected — left as-is |

No other unbounded full-table `select(ScannerResult)…all()` / `select(ScannerRun)…all()` remains in research.py.
None of the audit-only sites OOM'd or disk-spilled under the live streamed standard (all five heavy labs served
HTTP 200 — see live verification).

## Live verification (fresh, warmed, single-fetch :8835 backend on the full 3.47 GB DB)
Backend restarted to load the fix; waited for health `readiness:ready`, `warmup:ok`, `symbol_count:585`. One
heavy fetch at a time, full suite NOT running concurrently.

- **J-25 factor-lab, COLUMN factor** (`?factor=leadership_score&horizon=20`): **HTTP 200 in 58–121 s**,
  `n_total=598271`, `rank_ic=0.006685`, all 10 deciles real (D1 mean 0.008236 n=59827 … D10 mean 0.014749
  n=59828). No `MemoryError` / `disk is full` at research.py:216.
- **J-25 factor-lab, COMPONENT factor** (`?factor=rs_spy_3m&horizon=20`, reads `record_json`): **HTTP 200 in
  57 s**, `n_total=598271`, `rank_ic=-0.012422`, all 10 deciles non-null — proves `record_json` is preserved
  through streaming (the byte-identity caveat).
- **Default `GET /api/research/factor-lab` (no params):** **200** (this is the exact request that returned
  `500 disk is full` under the bare `ORDER BY id` before the `(run_id, id)` ordering fix).
- **J-26 factor-combination** (`?horizon=20`): **HTTP 200**, `pool_n=598271`, `baseline.stats.n=598271`
  mean=0.008761, `singles[rs_spy_3m].stats.n=119660` mean=0.010936 — cold-miss-safe (component factor read OK).
- **J-104 the other three heavy labs** (event-study, regime-setup-pattern, downtrend-opportunity): all **HTTP
  200** → all five heavy labs serve 200 on the live dataset.
- **Backend log scan across ALL probes:** `0` occurrences of `MemoryError` / `disk is full`; no `500` on any
  research endpoint after the fix. Backend RSS stayed ~733 MB during the heavy compute (bounded — no OOM).

## Tests Run
Command (targeted, run by developer): `cd apps/backend && .venv/bin/python -m pytest tests/test_research_streaming.py tests/test_research.py tests/test_samples.py tests/test_iter20_research_cluster.py tests/test_no_magic_numbers.py -q`
Result: all green (streaming 29 passed; research+samples 137 passed; iter20 16 passed; no-magic-numbers 2 passed).

TDD red proof: temporarily replacing the full-ORM stream with a narrow projection that DROPS `record_json`
made the component-factor byte-identity tests FAIL (`streamed != eager .all() reference (rs_spy_3m, …)`), then
pass again on restore — confirming the test genuinely guards the `record_json`-preservation caveat.

Full backend suite: launched **nohup-async AFTER** the live probes (per spec — never run the full suite
concurrently with the heavy-lab probes; never block the evaluator on the in-flight suite). Log:
`/tmp/iter48_full_suite.log` (looks for `SUITE_EXIT=0` and `0 failed`). The pump confirms the flushed-green gate.

## Known Issues
- **Host disk is at ~93 % (4.3 GB free).** The `(run_id, id)` ordering means the streamed read no longer needs a
  temp-sort file, so the factor-lab no longer depends on free disk. But the host is tight on space generally;
  unrelated heavy operations (e.g. a J-85 rebuild — out of scope, ~11 h, destructive) could still hit disk
  limits. Not a blocker for J-25/J-104/J-105.
- **Factor Lab cold compute is ~50–120 s** over ~598K rows (it is intentionally UNCACHED — out of scope to add a
  cache here; the fix is memory/disk-safety, not caching). Browser-QA must allow ~50–120 s for the first
  factor-lab fetch and fetch one heavy lab at a time.
- No frontend source change (spec: `apps/frontend` diff empty; `Frontend Present: yes` only forces the
  browser-QA live render-capture). The fix is purely a memory/disk-safety property of two backend read paths.
