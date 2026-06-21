# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-42 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-42
**Date:** 2026-06-20
**Written by:** developer

---

## Features Implemented

- **The backend stays responsive under concurrent load (J-100)**: When several people (or several
  automated UI tests) open the Data page at the same time, the backend no longer freezes the whole
  machine. The expensive "coverage" calculation is now computed **once** and shared, instead of being
  re-run separately for every simultaneous visitor. In a test, 12 simultaneous requests triggered exactly
  **1** heavy calculation instead of 12.
- **Memory stays bounded**: The data the backend loads to build the coverage numbers is now held as a
  single shared copy regardless of how many people are looking at once — so a busy moment can't balloon
  memory and swap-thrash the server.
- **The server is started with safety limits**: The backend start script now caps how many requests can be
  handled at once, sets request timeouts, and puts a hard ceiling on how much memory the backend process
  may use. If something ever goes wrong, only that one process is stopped — the rest of the machine keeps
  running.

There is **no visible change** on any page. Every number on the Data page, the Stocks page, and the
Dashboard is exactly the same as before — this iteration only removes an intermittent freeze.

---

## Changed Behavior

- **Data page under simultaneous use**: Previously, multiple people opening the Data page at once each
  triggered a separate heavy calculation, which could exhaust the backend's connection pool and
  intermittently freeze the whole machine. Now those simultaneous visitors share one calculation, so the
  page stays responsive and the freeze is gone. The displayed numbers are unchanged.
- **Internal cache refresh timing**: The Data page's "membership timeline" results are cached. Previously
  that cache was thrown away every time the background warm-up recorded a routine forward-return value —
  causing needless recalculation. Now the cache is only refreshed when something that actually affects the
  numbers changes (a new snapshot, added or removed price history). This is invisible to users; it just
  removes wasted work.

---

## Backend-Only Items

- The single-flight coverage cache, the narrow membership cache stamp, the shared bar cache, and the start
  script limits are all internal plumbing. None of them add any page, button, or displayed value — by
  design (this iteration is explicitly "no new UI").

---

## Incomplete Items

- **Live re-verification of the Data page and Dashboard** is left to the QA step. Because there is
  genuinely no frontend change, automated browser QA may auto-skip; the rendered pages must still be
  re-checked live to prove the numbers are unchanged. If the framework skips it, a short live re-verify
  follows in the next iteration.
- **The full backend test suite** (~3.5 hours on this large dataset) is handed to the automation "pump" to
  run in the background; its final green result is the gate. Local verification used the fast, targeted
  test groups plus the new concurrency load test, all of which passed.

---

## Config and Environment Changes

- **New `server:` section in `config.yaml`** — the single source of the backend's resource limits:
  - `limit_concurrency` — max simultaneous backend connections (default: `64`)
  - `timeout_keep_alive_seconds` — idle connection timeout (default: `65`)
  - `graceful_timeout_seconds` — shutdown grace period (default: `120`)
  - `memory_cap_mb` — hard per-process memory ceiling in MB (default: `6144`)
- **Optional environment overrides** for an operator-tuned run (each wins over the config default):
  `CHAIN_SERVER_LIMIT_CONCURRENCY`, `CHAIN_SERVER_KEEP_ALIVE`, `CHAIN_SERVER_GRACEFUL_TIMEOUT`,
  `CHAIN_SERVER_MEMORY_CAP_MB`.
- **No database migration** — no new table or column was added (the existing membership-timeline cache
  table is reused).

---

## Known Limitations

- **`/api/data` must be loaded once, never probed concurrently during normal QA.** The new behavior makes
  simultaneous loads safe, but the safe way to verify the page in QA is still to open it a single time and
  wait ~30 seconds for it to finish loading. The new concurrency load test is the only place simultaneous
  requests are deliberately fired.
- **The memory cap (`ulimit -v`) can only lower a limit, not raise it.** If the host already enforces a
  stricter memory cap, that stricter cap stays in effect and the start script keeps going rather than
  failing. On this host the 6144 MB cap applied cleanly.
- **A live backend start was not performed during development** to avoid kicking off the heavy multi-hour
  warm-up on the shared machine. The start-script change was verified with a non-serving dry run (the
  limits are read correctly and the memory cap applies). The QA step performs the live page check.
