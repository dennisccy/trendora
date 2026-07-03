# goal-mcp-loop-iter-17 — Staged 30-Year Seed Coverage Manifest (Part A2: index & macro context)

**Phase:** goal-mcp-loop-iter-17
**Date:** 2026-07-02
**Written by:** developer
**Staged asset:** `apps/backend/data/seed-stooq-30y/` (read by NOTHING at runtime; `config.provider: seed` untouched)

---

## Swap-complete: **YES**

The staged price-file set is a strict superset of the live seed's (staged ⊇ live), proven by the
committed test `tests/test_seed_staged_30y.py::test_swap_completeness_staged_superset_of_live`
(green over the real staged tree, 2026-07-02). The live seed's 162 price CSVs all have staged
counterparts; the previous gap — exactly `_DXY.csv`, `_TNX.csv`, `_VIX.csv`, `_VXN.csv` — is
closed. **The iter-18 atomic basis swap + sanctioned ledger reset is unblocked.**

---

## 1. Final staged inventory

| Category | Count | Detail |
|---|---|---|
| Equity/ETF series (iter-16, unchanged) | 583 | From Stooq's local bulk US archive (`d_us_txt`), window 1996-01-01 → 2026-07-01, per-name real first bar |
| Index & macro context series (iter-17, NEW) | 7 | `_SPX`, `_NDX`, `_DJI`, `_VIX`, `_TNX`, `_DXY`, `_VXN` |
| **Total staged price CSVs** | **590** | Matches `symbols_ok: 590` in `meta.json` (planned 591, failed 1) |
| Remaining honest absences | 1 | **SATS** — absent from Stooq's US stocks+ETFs bundle; recorded as an honest manifest failure, never fabricated |

Manifest accounting: `symbols_planned` 588 → **591** (+`^SPX`/`^NDX`/`^DJI`), `symbols_ok`
583 → **590** (+7 context), `symbols_failed` 5 → **1** (the four caret failures resolved into
coverage records; SATS remains). Window pins unchanged: `1996-01-01 → 2026-07-01`. The 583
equity records are byte-identical to the iter-16 manifest (verified against `git show HEAD`),
order preserved; the merge was strictly additive.

## 2. Per-series vendor table (goal.md §H disclosure)

| Series | Vendor (in `meta.json`) | Access | Coverage | Bars | Notes |
|---|---|---|---|---|---|
| `_SPX` | `stooq` | local world bundle (`data/d_world_txt/.../indices/^spx.txt`) | 1996-01-02 → 2026-07-01 | 7,674 | Archive reaches 1789 (flat/monthly early rows) — window clip proven by test; last bar == pinned end |
| `_NDX` | `stooq` | local world bundle (`^ndx.txt`) | 1996-01-02 → 2026-07-01 | 7,674 | Same clip + pinned-end proof |
| `_DJI` | `stooq` | local world bundle (`^dji.txt`) | 1996-01-02 → 2026-07-01 | 7,674 | Same clip + pinned-end proof |
| `_VIX` | `yahoo` | **deep single pull, live Yahoo chart API** | 1996-01-02 → 2026-07-01 | 7,675 | See §3 — the DEEP branch succeeded; never spliced |
| `_TNX` | `fred-macro-proxy` | byte-identical copy of `data/seed/prices/_TNX.csv` | 2021-01-04 → 2026-05-28 | 1,357 | The app's deterministic FRED-macro proxy (credit_spread transform); NEVER re-fetched from Yahoo; honestly short |
| `_DXY` | `fred-macro-proxy` | byte-identical copy of live seed | 2021-01-04 → 2026-05-28 | 1,357 | == `macro/dollar_index` (≈105 basis, not ICE ≈89); honestly short |
| `_VXN` | `fred-macro-proxy` | byte-identical copy of live seed | 2021-01-04 → 2026-05-28 | 1,357 | Deterministic flat-OHLC macro transform; honestly short |

The proxies stay coherent with `data/seed/macro/` (the FRED series the app displays). Deepening
them by extending the FRED macro series remains the sanctioned, DEFERRED macro-subsystem
follow-up — it can land later without re-staging equities. A proxy is never presented as a
market index (recorded verbatim in the manifest `note`).

## 3. `_VIX` outcome: **DEEP (Yahoo single pull succeeded)** — no fallback needed

- One single-vendor pull from the free Yahoo chart API (no key, no secret), window-clipped
  client-side to the manifest's pinned window: **7,675 bars, 1996-01-02 → 2026-07-01**.
- **Overlap agreement:** on all 1,357 dates shared with the live seed's `_VIX.csv`
  (2021-01-04 → 2026-05-28), max |staged − live| across OHLC = **0.000000** — the same vendor
  series, extended deep, zero seam. Every live date is covered by the staged series.
- **Continuity:** largest calendar gap = 7 days, ending 2001-09-17 (the 9/11 market closure) —
  a single continuous series; the deep-XOR-fallback test pins this (max gap ≤ 14 days).
- The tool validated the pull (deep first bar ≤ 1996-01-05, last bar ≥ the live copy's
  2026-05-28, strictly ascending, no splice-scale gap) before staging; an unusable pull would
  have taken the sanctioned verbatim-live-copy fallback — that branch is implemented,
  unit-tested, and NOT exercised for the committed asset.
- No follow-up needed (the fallback's "deepen `_VIX` later" follow-up is moot).
- Observation (inherited vendor quirk, not introduced): Yahoo serves a 2026-05-25 (Memorial
  Day) `^VIX` bar; the LIVE seed's `_VIX`/proxies already carry that date, so the staged basis
  is consistent with the live one. `_VIX` therefore has 7,675 bars vs the Stooq indexes' 7,674.

## 4. Validation status (committed tests, all green 2026-07-02)

- `tests/test_seed_staged_30y.py` — **12 passed** over the real staged tree: the prior 7
  (schema/ascending/positive/volumes, depth anchors, NVDA real IPO, post-IPO honesty, split
  continuity, cross-vendor returns agreement, manifest↔disk agreement) + 5 NEW context checks
  (deep/clipped/pinned-end/no-flat-run indexes; proxies byte-identical; `_VIX` deep-XOR-fallback;
  **swap-completeness staged ⊇ live**; manifest vendor/window/accounting agreement).
- `tests/test_ingest_seed.py` — **47 passed** offline (world-bundle indexing, context merge,
  fallback/splice-refusal, redaction failure path, pow cap, CLI guards) + 1 live integration
  test (`test_yahoo_vix_deep_pull_live_or_skip`) **passed against real Yahoo** (re-verified on
  resume, 2026-07-02: one deep-window request returned 63 real rows in 0.12s).

## 5. Reproduction

```bash
cd apps/backend
# world bundle (offline) + proxies (offline) + deep _VIX (Yahoo) merged into the staged manifest:
.venv/bin/python scripts/ingest_seed.py --provider stooq-local --stage-context --out data/seed-stooq-30y
# validate:
.venv/bin/python -m pytest tests/test_seed_staged_30y.py -q
```

Idempotent: re-running reuses the manifest's pinned window (a conflicting `--start`/`--end` is
refused, EXIT_CONFLICT) and appends the mixed-vendor note addendum exactly once. `data/d_world_txt/`
(operator's disk, gitignored under repo-root `/data/`) is required for the world leg; the staged
OUTPUT is what gets committed, same as iter-16's `d_us_txt` handling.

## 6. For iter-18 (forward pointer)

The swap iteration MUST see `test_swap_completeness_staged_superset_of_live` green at its start
(it is, as of this report), then execute the atomic flip + sanctioned ledger reset per the
iter-16 evaluator's roadmap: seed-dir flip, pool-broadened `load_prices`, `resolve_candidate`
staleness gate, DB rebuild, bounded backfill, regeneration of BOTH ledgers, frozen-golden/pin
refresh, survivorship-label span update. The +21.34% J-09 edge faces honest re-certification on
the new basis.
