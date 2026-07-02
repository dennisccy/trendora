# goal-mcp-loop-iter-16 — 30-year Stooq Seed Coverage Manifest

**Phase:** goal-mcp-loop-iter-16 (Part A of the sanctioned data-basis migration)
**Date:** 2026-07-02
**Written by:** developer
**Status: STAGED (583 symbols) — via the operator's LOCAL Stooq bulk archive (2026-07-02).** The
per-symbol network endpoint stayed blocked (§2, historical), so the operator downloaded Stooq's bulk
US archive (`d_us_txt.zip` → `data/d_us_txt/`) and a new OFFLINE provider path
(`--provider stooq-local`, reading the SAME Stooq vendor/adjusted data) staged the seed to
`data/seed-stooq-30y/`. The staged validation suite (`tests/test_seed_staged_30y.py`) is GREEN
(7 passed). The 4 caret index series + `SATS` are recorded absent (§3); the carets come from a
separate Stooq indices bundle the operator is adding. **iter-17's atomic swap + ledger reset is
unblocked.**

---

## 1. Fetch plan (deterministic — computed from the committed config + pool)

The network plan (probe first, then the full prioritized pool) was BLOCKED (§2). The staged run
actually used the OFFLINE local-archive path (same Stooq vendor data) — this is what landed the seed:

```
cd apps/backend
# ACTUALLY RUN (offline, from the operator's extracted d_us_txt bulk archive) — 28s, exit 0:
.venv/bin/python scripts/ingest_seed.py --provider stooq-local \
    --out data/seed-stooq-30y --symbols-set pool --start 1996-01-01 --sleep 0
# (original network plan, blocked by the per-IP export ACL:)
#   .venv/bin/python scripts/ingest_seed.py --provider stooq --probe --out data/seed-stooq-30y --start 1996-01-01
#   .venv/bin/python scripts/ingest_seed.py --provider stooq --out data/seed-stooq-30y --symbols-set pool --start 1996-01-01
```

Pinned window: **1996-01-01 → 2026-07-01** (the most recent completed trading day at run start; the
archive's last bar is 2026-07-01, so the latest data is included).

| Priority tier | Contents | Planned | Fetched | Recorded absent |
|---|---|---:|---:|---|
| 1 — benchmarks/controls | 4 index ETFs (SPY QQQ IWM RSP) + 11 sector ETFs + 20 industry ETFs + ^VIX + DIA (legend) + ^TNX ^VXN ^DXY (macro proxies) | 40 | 36 | 4 (^VIX ^TNX ^VXN ^DXY) |
| 2 — current universe | the 122 `universe.symbols` | 122 | 122 | 0 |
| 3 — remaining pool | 426 remaining `universe_pool.csv` names, alphabetical | 426 | 425 | 1 (SATS — empty archive file) |
| **Total** | pool (548 unique) ∪ all seed symbols | **588** | **583** | **5** |

The candidate pool has no dot-class tickers (e.g. BRK.B) — the existing symbol mapping covers every
planned name (the local provider maps a dot-class share to its hyphenated file, `BRK.B` → `brk-b.us.txt`).
The 4 caret indexes are absent from the `d_us_txt` stocks+ETFs bundle (they ship in a separate Stooq
indices/world archive — §3).

## 2. Probe outcome (the go/no-go, run live 2026-07-01/02)

```
[probe] go/no-go: AAPL, SPY, NVDA full-span 1996-01-01 -> 2026-06-30 via StooqProvider (Stooq free per-symbol CSV (https://stooq.com/q/d/l/, keyless))
[probe] HARD FAILURE fetching AAPL: stooq returned no usable data for 'AAPL': 'Access denied'
[probe] NO-GO — the endpoint is gated/unavailable for this environment. Nothing staged; the exact
        response evidence is embedded in the error above. (A key, if required, is read from
        $STOOQ_API_KEY only.)
exit code 2
```

### Exact gate anatomy (captured evidence)

1. **Front door — automatic JavaScript browser verification.** `stooq.com/q/d/l/` (and `stooq.pl`)
   serve a small HTML page: *"This site requires JavaScript to verify your browser"* plus a script
   that finds a nonce `n` with `sha256(c+n)` starting with 4 hex zeros and POSTs it to `/__verify`
   (a millisecond proof-of-work — no captcha, no credential). The ingest tool completes this
   handshake exactly as specified (`_StooqVerifyClient`); verified live: `POST /__verify → 200`,
   session cookie granted, regular site pages then serve normally (e.g. the AAPL quote page,
   199 KB of real HTML).
2. **Second gate — CSV-export ACL (the actual blocker).** With the verified session, the historical
   CSV export endpoint itself returns `HTTP 200, text/plain, 13 bytes: "Access denied"` — on
   stooq.com AND stooq.pl (`"Odmowa dostępu"`), with or without Referer/page-navigation, with or
   without date params. This is a standing per-IP denial of the export endpoint, NOT a daily-hits
   quota (no limit-page language, denial from the first request). It matches the iter-3 lesson
   recorded in `config.yaml`'s import catalog: stooq "free CSV nominally, but key-gated for this IP".
3. **Bulk database path** (`static.stooq.com/db/…`): `HTTP 401 Basic realm="Restricted"` — the
   captcha/key-gated bulk download from the iter-1 lesson, still closed and still out of bounds.
4. `STOOQ_API_KEY` is **not set** in this environment, and no documented key parameter is known
   for the per-symbol export endpoint.

## 3. Coverage facts — RESOLVED by the staged run (2026-07-02)

- **^VIX and the macro proxies (^TNX/^VXN/^DXY):** ABSENT from Stooq's `d_us_txt` bundle (US
  stocks+ETFs only — no indices tree). Recorded absent, never fabricated. They come from a separate
  Stooq indices/world bundle the operator is adding (indexes carry no split/dividend adjustment, so
  the single-basis rule — an equities concern — does not bind here). Until that bundle is staged,
  iter-17 keeps the existing `_VIX/_TNX/_VXN/_DXY` + `macro/` series.
- **Pool names Stooq lacks entirely:** exactly ONE — `SATS` (an empty archive file in `d_us_txt`).
  Recorded absent; it simply never enters the universe. Every other pool + universe + benchmark name
  staged (583 total).
- **Short-history names:** honest per-name first bars confirmed — NVDA 1999-01-22 (real IPO),
  COIN 2021-04-14, ARM 2023-09-14, HOOD 2021-07-29; long-tenured AAPL/MSFT reach 1996-01-02.
  Split continuity verified (NVDA 2024-06-10, AAPL 2020-08-31: no unadjusted seam) and cross-vendor
  returns agree with the live Yahoo seed over the 2021-2026 overlap (all in `test_seed_staged_30y.py`).

## 4. Rate-cap events

None — the run never got past the first symbol. The graceful-stop machinery (record cap event →
write manifest → non-zero exit → resume skips completed symbols) is unit-proven in
`tests/test_ingest_seed.py` (`test_rate_limit_stops_gracefully_then_resumes`).

## 5. Resume instructions (when access exists)

The tool is fully ready; nothing needs rebuilding. From an environment Stooq's export ACL does not
deny (e.g. a residential connection), or with a sanctioned key exported as `STOOQ_API_KEY`:

1. `cd apps/backend`
2. `.venv/bin/python scripts/ingest_seed.py --provider stooq --probe --out data/seed-stooq-30y --start 1996-01-01`
   — must print GO (depth ≤ 1996-01-05 for AAPL/SPY; no split seam at NVDA 2024-06-10 / AAPL 2020-08-31).
3. `.venv/bin/python scripts/ingest_seed.py --provider stooq --out data/seed-stooq-30y --symbols-set pool --start 1996-01-01`
   — ~588 symbols, ≥1s apart (~20–35 min). On a rate-cap it stops honestly (exit 2) with the
   progress manifest written; **re-run the same command** to resume — completed symbols are
   skipped and the manifest's pinned end is reused (do NOT pass a different `--end`).
4. `.venv/bin/python -m pytest tests/test_seed_staged_30y.py -q` — the staged validation suite
   (schema, depth anchors, post-IPO honesty, split continuity, cross-vendor returns agreement,
   manifest agreement) activates automatically once the staged dir exists and must be green
   before the asset is committed.
5. Update this manifest's tier table + unknowns section from `data/seed-stooq-30y/meta.json`
   (`symbols` / `failures` / `cap_events`).

## 6. Decision RESOLVED (2026-07-02) — staged via the local bulk archive

The operator took a 4th path equivalent to option (a): downloaded Stooq's bulk US archive
(`d_us_txt.zip` → `data/d_us_txt/`) and staged it OFFLINE with the new `--provider stooq-local` path
(same Stooq vendor/adjusted data; no network, no key, no `app/**` boot-path change). The staged asset
is validated (7/7 in `test_seed_staged_30y.py`) and committed. **J-10's data prerequisite is met; the
iter-17 atomic swap + sanctioned ledger reset is unblocked.**

Remaining for iter-17: the 4 caret index series (`^VIX/^TNX/^VXN/^DXY`) come from a separate Stooq
indices bundle the operator is adding — until it is staged, iter-17 preserves the existing
`_VIX/_TNX/_VXN/_DXY` + `macro/` series (index levels are not split/dividend-adjusted, so a mixed
vendor basis for them is acceptable — the single-basis rule is an equities concern).
