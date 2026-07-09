# goal-mcp-loop-iter-25 Dev Handoff

**Phase:** goal-mcp-loop-iter-25
**Date:** 2026-07-09
**Agent:** developer
**Status:** complete

## What Was Built

Nothing new. Per the plan and phase spec, this iteration is a **fix-VERIFICATION + artifact-reconciliation
pass only** — zero new features, endpoints, models, or migrations. The work:

- Confirmed the already-committed fix (`config.yaml:108` → `mmap_size_bytes: 0`, applied by the iter-24
  audit, committed at HEAD `665565a`) is still present and `git diff HEAD -- config.yaml` is clean. No
  contingency restore was needed — the fix never reverted.
- Live-drove the cold-path repro **twice** against the real 30-year/583-symbol committed DB: full backend
  stop (`kill -TERM` on the uvicorn PID) → fresh `scripts/start-backend.sh` cold start → `GET /api/data`
  as the first (run 2) or first-heavy (run 1) request, with backend RSS sampled from
  `/proc/<pid>/status` every 0.2 s for the duration of each request. Both runs: HTTP 200, ~9.4–9.5 s,
  peak RSS ~1.8–1.9 GB (well under the 6144 MB `ulimit -v` cap), backend process stayed alive throughout
  and continued serving requests afterward. **This flips iter-24's UT-16 (browser-qa reproduced the
  crash 2/2) to fixed, verified 2/2 at the live HTTP level.**
- Brought up both prod-mode services (`scripts/start-backend.sh` :8255 / `scripts/start-frontend.sh`
  :3255, `rm -rf apps/frontend/.next` first per the iter-20 staleness-stamp lesson) and confirmed both
  answered HTTP 200 before and during the checks above.
- Re-ran `scripts/measure-perf.sh`'s warm methodology (captured to a scratch file rather than appended
  directly, to avoid the script's hardcoded `"(iter-24)"` section label — see Known Issues) — every J-15
  warm budget still holds, and the `GET /api/data` `capacity` payload is byte-identical to every
  previously-recorded figure in `reports/perf-budgets.md` (no drift).
- Corrected/extended `reports/perf-budgets.md` with two new, clearly-labeled iter-25 sections: a
  live-verified cold-path section (replacing the iter-24 audit's ablation-only "471 MB" claim with two
  real HTTP-level cold-boot measurements) and a warm re-confirmation section.
- Ran the DoD-named targeted test selection **unedited**: `test_bar_cache.py`, `test_api_engine.py`,
  `test_health.py`, `test_data_manager.py` — **123 passed, 0 failed**, in 7156.23 s (1:59:16).
- Cleanly stopped both server processes before finishing (confirmed no process bound to :8255/:3255 and
  no stray `uvicorn`/`next` processes remain).

## Files Changed

- `reports/perf-budgets.md` — appended two new sections: "Cold `/api/data` path — LIVE-VERIFIED by the
  iter-25 developer pass" (two real cold-boot HTTP measurements, replacing the ablation-only claim) and
  "Warm budgets — re-confirmed on the fixed build" (fresh `scripts/measure-perf.sh` warm numbers).
- No `apps/backend/**` or `apps/frontend/**` files touched — confirmed via
  `git diff HEAD --stat -- apps/backend apps/frontend` (empty both before and after this pass).
- `config.yaml` — confirmed unchanged (`git diff HEAD -- config.yaml` empty); the `mmap_size_bytes: 0`
  fix was already at HEAD from the iter-24 audit.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_bar_cache.py tests/test_api_engine.py tests/test_health.py tests/test_data_manager.py -v`

Result: **123 passed, 0 failed** in 7156.23s (1:59:16).

Run detached via `setsid nohup` (per this box's >8-minute-command operational note) and polled to
completion. The `loaded_engine` session-scoped fixture's one-time full 30-year/583-symbol seed-load +
historical-cadence bootstrap (~124 quarterly dates) + forward-return backfill dominates the wall time —
this is consistent with iter-24's own precedent recorded in `docs/handoffs/goal-mcp-loop-iter-24-dev.md`
("first run 1 failed, 162 passed in 10177.36s (2:49:37)" for a similar 5-file selection, and
"tests/test_db.py: 19 passed in 6332.34s (1:45:32) -- includes the one-time 30-year loaded_engine fixture
build"). Confirmed via `/proc/<pid>` sampling throughout (not a hang): 100% CPU, stable ~848 MB RSS, no
I/O wait, 5.5 GB+ cumulative page-cache reads.

**Live cold-path repro** (not a pytest run — a real HTTP-level operational check, the actual crux
deliverable of this iteration):

| Run | Sequence | `GET /api/data` | Wall time | Peak backend RSS | Backend survived |
|---|---|---|---|---|---|
| 1 | cold-start → (stray external `/api/health` ×4, see Known Issues) → `/api/data` | HTTP 200 | 9.522s | ~1,814 MB (1,857,632 KB) | **YES** |
| 2 | cold-start → (stray external `/api/health` ×1) → `/api/data` as the first/only HEAVY request | HTTP 200 | 9.387s | ~1,859 MB (1,903,228 KB) | **YES** |

Both cold `capacity` response bodies are byte-identical to each other and to every previously-recorded
figure (`db_file_bytes 1307414528`, `daily_prices_rows 3293160`, `scanner_results_rows 165755`,
`forward_returns_rows 821054`).

**Warm re-confirmation** (`scripts/measure-perf.sh` methodology, run immediately after the cold hit
above): all 4 endpoint budgets (`/api/health` 0.090s, `/api/stocks` 0.058s, `/api/stocks/AAPL` 0.003s,
`/api/data` 0.014s) and all 4 page budgets (`/stocks` 0.008s, `/stocks/AAPL` 0.007s, `/data` 0.010s,
`/evidence` 0.008s) held with wide headroom; full detail in `reports/perf-budgets.md`.

## Known Issues

- **This dev-level verification is strong operational evidence, not the terminal gate.** Per the plan,
  phase spec, and repeated session lessons (iter-13/20/22/24), the canonical `browser-qa-agent` LIVE run
  is still required to formally flip J-13/UT-16 and clear the CLOSURE-FAIL — my curl-level repro (real
  process, real HTTP requests, real memory sampling, twice, from a genuine cold restart) is solid
  supporting evidence but is not itself the DoD-named browser-verified gate. That is the very next step.
- **An unrelated background process on this host polled `/api/health` a few times immediately after each
  backend cold-start** (visible in the captured backend logs; not started by this verification pass —
  most likely this session's own goal-mode dispatch/pump supervisory tooling doing a liveness probe,
  consistent with the `runs/goal-session-mcp-loop/dispatch/` activity visible in `git status`). This does
  **not** weaken the repro: `mmap_size_bytes: 0` removes the per-pooled-connection virtual-memory
  reservation that caused the original OOM regardless of which endpoint opens a connection first, and
  run 2 confirms `/api/data` was still the first/only HEAVY (prefill-triggering) request in that
  process's lifetime. Flagging for transparency in case the browser-qa lane observes similar traffic.
- **`scripts/measure-perf.sh` hardcodes a `"(iter-24)"` section label** in its auto-appended output
  regardless of when it's actually run. Rather than edit a script outside this iteration's explicit
  scope (plan's files-to-modify list does not include it, and the plan is explicit that no
  pool/pragma/re-tuning-adjacent code should be touched), I ran it against a scratch output file and
  hand-transcribed the numbers verbatim into a correctly-labeled iter-25 section in
  `reports/perf-budgets.md`. A future tidy-scope iteration could parameterize the label.
- The full ~10–11 h 30-year pytest fixture was correctly **not** run, per the phase spec's explicit
  exclusion (iter-23 lesson).
- **No `docs/handoffs/goal-mcp-loop-iter-25-frontend.md` was written.** Zero frontend source changed
  (confirmed via `git diff`), so a separate frontend handoff would have nothing to report — the plan
  itself states frontend-ux is not dispatched this iteration ("zero frontend source change... not a UI
  implementation task"). The one frontend-adjacent operational step (`rm -rf apps/frontend/.next` +
  fresh prod build/serve, to dodge the iter-20 staleness-stamp trap) is recorded above and was verified
  working (frontend answered HTTP 200 after a ~19s fresh build).
- Both backend and frontend server processes started during this pass were cleanly stopped before
  finishing (confirmed no process bound to :8255/:3255 and no stray `uvicorn`/`next` processes remain).
