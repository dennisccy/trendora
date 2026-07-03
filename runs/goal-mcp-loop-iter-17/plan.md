# goal-mcp-loop-iter-17 Execution Plan

**Phase:** 30-year basis, Part A2 — deep index & macro context staged into the 30y seed (vendor-disclosed, ZERO runtime change).
**Target journey:** J-14 (step 1 delivered into the STAGED basis; stays `unknown` — steps 2–3 are post-swap surfacing). Required-still-passing: J-01, J-02, J-03, J-05, J-09 — proven by byte-identity + unedited green suites, not browser runs.
**Goal alignment:** implements goal.md §H exactly ("complete the seed's index/macro context BEFORE the swap so the swap happens once over one complete seed"); iter-18 = the atomic swap + sanctioned ledger reset. No drift detected. **Evidence Claim: none** — zero referee submissions, both ledgers byte-identical; the post-decompose gate passes automatically.
**Preconditions re-verified against disk today (iter-12/16 lesson):** staged seed EXISTS (583 price CSVs + `meta.json`, window pinned `1996-01-01 → 2026-07-01`, failures = `^VIX/^TNX/^VXN/^DXY/SATS`, zero `_*` context files staged); live-seed carets are exactly `_DXY/_TNX/_VIX/_VXN` (`_VIX` spans 2021-01-04 → 2026-05-28, volume 0); `data/d_world_txt/data/daily/world/indices/` carries `^spx.txt`/`^ndx.txt`/`^dji.txt` and NO `^vix`; `test_seed_staged_30y.py` present; `_solve_stooq_pow` (ingest_seed.py:293) is still uncapped (B2 due now).

## What to Build

- **World-bundle indexing in `apps/backend/scripts/ingest_seed.py`'s `stooq-local` path** (surgical; US-archive `*.us.txt` indexing and all existing behavior intact): when `--archive-dir` points at the extracted world bundle (`data/d_world_txt/`), discover plain `^xxx.txt` files (no `.us` suffix; same `<TICKER>,<PER>,<DATE>,<TIME>,…` bulk row format). Map file stem → caret symbol → staged filename via the app's existing `symbol_to_filename` convention (`app/data_providers/seed_provider.py:18-20`: `'^SPX' → '_SPX.csv'`). Keep both REFUSED guards (missing dir / no recognized files — the current message at :756 assumes `d_us_txt`; extend, don't regress).
- **Stage `_SPX.csv`, `_NDX.csv`, `_DJI.csv`** into `apps/backend/data/seed-stooq-30y/prices/` over the manifest's pinned window (`resolve_stooq_window` reuses the pinned end on resume — do NOT widen or re-pin). CLIP pre-window rows: world `^spx.txt` reaches back to 1789 with flat/monthly early rows — none may leak. Volume rule for index rows: non-negative (0 is legitimate, like live `_VIX`), not positive.
- **Deep `_VIX` from Yahoo** (`^VIX`, start 1996-01-01, clipped to pinned end 2026-07-01) as a SINGLE-vendor single-pull series via a NEW context-merge mode — do NOT route through `run_yahoo_ingest` (:451, writes its own manifest and would CLOBBER the staged stooq `meta.json`): write the one CSV and MERGE its coverage/vendor record into the existing manifest (583 equity records + pinned window untouched). **Sanctioned offline fallback:** if Yahoo is unreachable, copy live `data/seed/prices/_VIX.csv` VERBATIM (byte-identical, honestly short 2021-01-04 → 2026-05-28), record `vendor: yahoo` + the shortfall in manifest and coverage report, surface the narrow follow-up. NEVER merge/splice two pulls; never fabricate a bar.
- **Preserve the three FRED-macro proxies:** copy `_TNX.csv`, `_DXY.csv`, `_VXN.csv` BYTE-IDENTICAL from `data/seed/prices/`. Do NOT re-fetch from Yahoo (§H verbatim: a re-fetch would DESYNC them from the FRED macro the app displays — ICE DXY ≈89 vs ≈105; yield×10). They stay honestly short (→ 2026-05-28); FRED-deepening is a DEFERRED macro-subsystem task.
- **Manifest merge with per-series vendor disclosure:** every context series gets `vendor` — `stooq` (`_SPX/_NDX/_DJI`; vendor unchanged, access local world bundle), `yahoo` (`_VIX`), `fred-macro-proxy` (`_TNX/_DXY/_VXN`) — alongside the existing `{symbol, bars, first, last}` records. The four caret failure entries resolve into coverage records with their REAL (possibly short) spans; `^SPX/^NDX/^DJI` join as new planned+ok; accounting stays consistent (expected: planned 588→591, ok 583→590, failed 5→1 = SATS only); extend `note` to describe the mixed-vendor context + "a proxy is never presented as a market index". Copied/proxy series record their real last bar (2026-05-28) — never pretend pinned-end coverage.
- **Extend the staged validation suite** (`tests/test_seed_staged_30y.py` or sibling, same skip-with-reason pattern): `_SPX/_NDX/_DJI` present + schema-identical + strictly-ascending unique dates + positive prices/non-negative volumes + first bar ≥ 1996-01-01 (clip proven — no pre-window leakage) + last bar == pinned end + no flat-OHLC fabricated-looking run in-window; `_TNX/_DXY/_VXN` byte-identical to live; `_VIX` deep (first bar ≤ 1996-01-05, single continuous series) XOR byte-identical live copy — exactly one state, never a hybrid; **swap-completeness: staged price-file set ⊇ live seed's** (the iter-18 hard gate); manifest agreement (vendor ∈ {stooq, yahoo, fred-macro-proxy} for every context series; first/last/bars match disk; window pins unchanged).
- **Audit carry-forwards, due now:** B2 — cap `_solve_stooq_pow` iterations (bounded loop, honest failure message) + regression test; B1 discipline — any NEW failure-record path routes error/URL text through the `redact_stooq_key` choke-point pattern (:216, :248-252), with the FAILURE path exercised by a test (the Yahoo path carries no key; the discipline applies to whatever error text it persists).
- **Coverage report** `reports/phase-goal-mcp-loop-iter-17-seed-coverage.md`: final staged inventory (583 equities + 7 context = 590 expected), per-series vendor table, `_VIX` outcome (deep vs fallback + follow-up if fallback), remaining honest absences (SATS), and an explicit "swap-complete: yes/no" line with the staged⊇live result.
- **Commit the staged additions** (7 context CSVs + merged `meta.json`). The staged tree remains read by NOTHING at runtime (`config.provider: seed` untouched; `SeedProvider` still reads `data/seed/`).

## Agents Required

- backend-data (developer): yes -- all of the above: world-bundle indexer, context staging (3 offline + 1 Yahoo-or-fallback + 3 byte-copies), manifest merge + vendor disclosure, extended validation suite, B1/B2 carry-forwards, coverage report, commit, dev handoff.
- frontend-ux: no -- zero UI change; every displayed number stays byte-identical.

Frontend Present: no

## Files to Create/Modify

- `apps/backend/scripts/ingest_seed.py` -- world-bundle (`^xxx.txt`) indexing in the stooq-local path; context-merge staging mode (manifest MERGE, never overwrite); `_solve_stooq_pow` iteration cap; redaction on any new persistence path.
- `apps/backend/tests/test_ingest_seed.py` -- new offline unit tests: synthetic `d_world_txt`-layout discovery + caret→`_XXX.csv` mapping + coexistence with `*.us.txt`; pre-1996 clip; manifest merge non-disturbance; pow cap; redaction failure path; window-conflict refusal.
- `apps/backend/tests/test_seed_staged_30y.py` (extend; or sibling module, same skip pattern) -- context validations, proxy byte-identity, `_VIX` deep-XOR-fallback, swap-completeness (staged ⊇ live), manifest/vendor agreement.
- `apps/backend/data/seed-stooq-30y/prices/{_SPX,_NDX,_DJI,_VIX,_TNX,_DXY,_VXN}.csv` (new, committed) + `apps/backend/data/seed-stooq-30y/meta.json` (merged) -- the completed staged asset.
- `reports/phase-goal-mcp-loop-iter-17-seed-coverage.md` (new) -- inventory + vendor table + swap-complete verdict.
- `docs/handoffs/goal-mcp-loop-iter-17-dev.md` (new) -- honest External-Integration section for the Yahoo pull (succeeded or fell back, with evidence).
- Blueprint `runs/goal-session-mcp-loop/state/blueprint.md`: **verify-only, do NOT edit** — the J-14 homes row (line ~82) and the iter-17 clarification (line ~211) are already present from the decompose step.
- MUST NOT change (byte-identical): `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, `runs/goal-session-mcp-loop/state/certified-claims.jsonl`, `runs/goal-session-mcp-loop/state/staging-ledger.jsonl`, `data/seed/**` (live seed is a read-only copy source), and the unedited DoD suites (`test_referee.py`, `test_forward_walk.py`, `test_evidence.py`, `test_staging_ledger_routing.py`, `test_seed_integrity.py`, `test_seed_provider.py`). Zero referee submissions, zero ledger writes, no test pins refreshed.

## UI Evolution

N/A — backend/data-only iteration; no UI surface, action, or navigation change. (Stages 5/6/8 write the sanctioned N/A stubs.)

## Key Test Scenarios

- World-archive indexer offline units: synthetic world tree → `^spx/^ndx/^dji` discovered, mapped to `_SPX/_NDX/_DJI.csv`; `*.us.txt` indexing coexists; missing/wrong `--archive-dir` → REFUSED; no recognized files → REFUSED.
- Window clipping: pre-1996 archive rows (incl. flat/monthly 18xx-era rows) never reach a staged CSV; staged first bar ≥ 1996-01-01; last bar == the manifest's pinned end 2026-07-01; a window conflicting with the pinned manifest → `EXIT_CONFLICT`; staging into a foreign-manifest dir still REFUSED.
- Manifest merge: context records merge WITHOUT disturbing the 583 equity records, pinned window, or provider identity; vendor required for every context series; planned/ok/failed accounting consistent; a context series absent from its source → recorded honestly, never fabricated.
- Proxies byte-identical to live; `_VIX` asserts deep-XOR-fallback (never a hybrid/splice); swap-completeness staged ⊇ live green — the load-bearing iter-18 gate.
- `_solve_stooq_pow` bounded (cap hit → honest failure, no spin); redaction exercised on the FAILURE path (nothing env-sourced persists to any committed artifact).
- ONE live integration test for the Yahoo `_VIX` pull (`@pytest.mark.integration`-style, existing convention) — honest outcome (pass or documented block) drives the deep-vs-fallback branch; Yahoo unreachable → the sanctioned verbatim-copy fallback, never a partial series.
- Non-regression J-01/J-02/J-03/J-05/J-09: `git diff` clean on all protected paths + both ledgers, unedited DoD suites green. No browser checks (`Frontend Present: no`).

## Assumptions & Scope Guards

- `data/d_world_txt/` stays on the operator's disk and is NOT committed (only staged OUTPUT is committed — iter-16's `d_us_txt` precedent). Verified today: `^spx/^ndx/^dji.txt` present, no `^vix` (consistent with §H's "^VIX from Yahoo").
- Pinned window stays `1996-01-01 → 2026-07-01`; later-fetched context series clip to it; copied/proxy series honestly end 2026-05-28.
- The `_VIX` fallback branch still yields a swap-complete staged seed — iter-18 is dispatchable regardless of Yahoo reachability; a Yahoo failure alone is NOT a STALLED condition (spec's evaluator note).
- Expected final inventory: 590 staged price CSVs; SATS remains the only honest absence.
- OUT OF SCOPE (flag any drift): the atomic swap + sanctioned ledger reset and everything downstream (seed-dir flip, `load_prices` broadening, `resolve_candidate` staleness gate, DB rebuild, backfill, ledger regeneration, frozen-golden/pin refresh — all iter-18); ANY change under `apps/backend/app/**`, `apps/frontend/**`, `config.yaml` (incl. adding `_SPX/_NDX/_DJI` to `etfs.index`/`index_chart`); FRED-macro deepening / proxy regeneration; Yahoo gap-fill for any equity (incl. SATS); J-14 steps 2–3 surfacing + `[NEW]` demo; J-10 chart windowing, J-12 membership hardening, J-13 Data Manager changes; re-probing Stooq's network endpoints (standing per-IP ACL — local archives are the sanctioned path).
