# Iteration 20 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

Iteration 20 was dispatched as a **stale "finalization / no-code" pass** — but the operator re-scoped `docs/goal.md` (commit `d3e5076`, 2026-06-04 21:14) to add **three new Must-have journeys: J-33, J-34, J-35** (UI data-import: selectable key-aware provider source; chunked, rate-limit-resilient, *resumable* import; Expand-universe from the Data Manager). The goal-decomposer wrote the iter-20 spec **90 seconds later (21:15)** yet ignored those three journeys and declared the session complete on the old 29-journey set. I verified in source that **J-33/34/35 are unbuilt**, and `goal.md` (lines 838–844) explicitly states their UI + catalog + key-detection + chunk/resume/checkpoint + expand-screen machinery is **"buildable and fully testable offline" and "not blanket-blocked"** — only the live-fetch *outcome* is data-gated. Therefore the goal is **not** achieved: three buildable must-have journeys remain. The 29 prior buildable journeys (J-01–J-21, J-25–J-32) remain `passing` (re-verified via real browser QA; zero code change → no regression possible); J-22/J-23/J-24 stay honestly blocked (NA), non-halting.

## Why not GOAL_ACHIEVED

The evaluator rule is explicit: *do not mark GOAL_ACHIEVED if any Must-have journey has status `failing` or `unknown`.* The current `goal.md` lists **J-33 (line 762), J-34 (line 784), J-35 (line 803)** under "Must-have user journeys." Code inspection proves their required capabilities do not exist:

| Journey | Required (goal.md) | Actual code state | Verdict |
|---------|--------------------|-------------------|---------|
| **J-33** Selectable, key-aware provider source | config provider **catalog** (Yahoo/Tiingo/Finnhub/Alpha Vantage/Stooq) w/ env-detected availability + **session-only key paste**; Import-source control on `/data` | `JobCreate` has only `kind: Literal["fetch","backfill","both"]` — **no `source`/`provider` field**; `config.yaml` has only `provider: seed\|stooq` (a 2-value Literal, no catalog, no `needs_key`/`env_var`); `/data/page.tsx` has **no source picker** | **failing (unbuilt)** |
| **J-34** Chunked, rate-limit-resilient, resumable import | chunk x/N progress; config-driven batch/backoff; **durable checkpoint surviving restart**; 429 → backoff → graceful **resumable/paused** state; **Resume** continues from last chunk; per-(symbol,date) idempotency | **no resume route**; no `resumable`/`checkpoint`/`backoff`/429 machinery in `data_manager.py`; no Resume button / chunk-progress in the UI; existing job is single-shot fetch/backfill with simple polling | **failing (unbuilt)** |
| **J-35** Expand-universe from Data Manager | an **Expand-universe job kind** that reads the committed `universe_pool.csv` + the config screen and writes passers | `JOB_KINDS = ("fetch","backfill","both")` — **no `expand` kind**; frontend offers no expand option. `universe_pool.csv` (548 names) exists but has **no UI/API path** to run the screen | **failing (unbuilt)** |

The `/data` screenshot (`UT-J-17-data-coverage.png`) visually confirms it: only "Start a fetch / backfill job" (Start date / End date / Job kind = "Backfill snapshot…") + Run history — no source picker, no Expand kind, no Resume/chunk machinery. The iter-20 **dev handoff's claim** (item 10) that the Data Manager already has "source picker (config catalog + env-detection), chunked rate-limit-resilient import with resumable checkpoints, and expand-universe job" is **inaccurate** — it restates the goal.md *vision* (capability #20), not the implemented code.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01…J-21, J-25…J-32 (29) | passing | **passing** (re-verified, zero-code-change carry) | `reports/qa/…iter-20-evidence/UT-J-*.png` (25 PNGs, 24 distinct sha256) + browser QA 29/29 PASS |
| J-22 | failing (blocked) | **failing** — BLOCKED / NON-HALTING / NON-VETOING (not re-probed) | data-walled per goal.md 99–103, 824–836 |
| J-23 | failing (blocked) | **failing** — BLOCKED / NON-HALTING / NON-VETOING (not re-probed) | data-walled (intraday) |
| J-24 | failing (blocked) | **failing** — BLOCKED / NON-HALTING / NON-VETOING (not re-probed) | depends on J-23 |
| **J-33** | (new — not yet tracked) | **failing (unbuilt)** | code-verified absent (no `source` field; config `provider: seed\|stooq` only) + `UT-J-17-data-coverage.png` |
| **J-34** | (new — not yet tracked) | **failing (unbuilt)** | code-verified absent (no resume/checkpoint/backoff/chunk machinery) |
| **J-35** | (new — not yet tracked) | **failing (unbuilt)** | code-verified absent (`JOB_KINDS` lacks `expand`); `universe_pool.csv` present but no UI/API path |

**Board: 29 passing / 6 failing (J-22/23/24 data-walled non-halting; J-33/34/35 buildable-but-unbuilt).**

## Anti-goal Check

Zero source changed this iteration (`git diff HEAD -- apps/ config.yaml` = 0 lines; coherence-auditor + reviewer + status.json all confirm) — so **no anti-goal could be violated**. The principal invariant (**Exactly one date selector**) held: the Data Manager's import date inputs are job parameters, not the viewing as-of control (browser QA UT-J-18; the single global switcher is the only date control). Coherence: **COHERENCE-PASS**. The one historical minor violation ("exactly one date selector", iter-0 baseline) stays **resolved**.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Exactly one date selector | OK | held; import dates = job params; Research toggle is a mode (J-18/J-32) |
| No recompute in read path | OK | no code change; snapshot-served reads intact |
| Snapshots immutable | OK | no schema/DB change |
| No fabricated data / honest NA | OK | data-walled journeys recorded NA, not fabricated |
| (all others) | OK | zero source diff → none reachable for violation |

## Next-Step Recommendation

**`full` depth, target the J-33 → J-34 → J-35 import chain.** The next decomposer MUST read the **current** `goal.md` (with J-33/34/35) and target them — it must NOT re-issue a "finalization / session-complete" spec (that framing is stale: it predates the loop seeing the re-scope).

Concrete build order (all offline-testable with an **injected provider** stub — a fake that returns bars or raises 429):
1. **J-33 (foundation):** add a **config provider catalog** (`providers:` list with each source's `needs_key` + `env_var`; replace the `seed|stooq` Literal). Add a `source` field to `JobCreate`/the job engine. Build the `/data` **Import-source** control with **env-detected availability** + a **session-only key paste** (held in memory for the run — verifiably **never** written to disk/run-log/DB and never echoed in `/api/data` or run history). Unit-test: catalog-from-config, env-detection, key-never-persisted, provider-failure → explicit error (no fabricated bar).
2. **J-34 (resilience):** chunk the import (config-driven symbol-batch / date-window / max-retries / backoff base+cap / inter-request sleep — no magic numbers); **durable checkpoint** after each chunk (persisted, survives restart); 429 → backoff → graceful **`resumable`/paused** status (distinct from `failed`); a **Resume** action that continues from the next un-fetched chunk with per-(symbol,date) idempotency (no duplicate fetch/row). Unit-test with an injected provider scripted to raise 429 after K symbols; assert checkpoint survives a simulated restart and Resume re-fetches nothing.
3. **J-35 (payoff):** add the **`expand` job kind** that reads the committed `universe_pool.csv` (548 names) + the config screen (`universe.filters`), runs as a chunked/resumable import (per J-34), writes only passers to `universe.json` + per-symbol CSVs + `meta.json`, and records selection-methodology + per-member screen-pass + omitted-with-reason. A provider that cannot supply market cap is **not selectable** for expansion (disabled w/ reason). This is the **operator-facing path that auto-unblocks J-22** once data is reachable.

**Anti-goal watch-items for the build:** (a) **Import keys env-or-session, never persisted** — the new session-key paste is the principal risk; verify it is absent from `/api/data`, run history, and the DB and never echoed. (b) **Exactly one date selector** — the import date inputs are **job parameters**, NOT the global as-of viewing control; do not introduce a second viewing-date state. (c) **No fabricated data** — provider failures surface explicit error/NA; live-fetch is real-data-only. (d) **No magic numbers** — every chunk/backoff/retry constant comes from config. (e) **Universe screen reproducible & honest** — J-35 writes only real screened passers, omits-with-reason, keeps breadth/forward-test labels universe-relative/survivorship-biased.

**Data-gating note (non-halting):** J-33/34/35's *machinery* (catalog, key-detection, chunk/resume/checkpoint, expand-screen logic) is expected to go **green offline** with the injected provider. Only a *successful live fetch* (and thus J-22 fully passing through J-35) is data-gated — when every provider is Yahoo-429 walled it is recorded as honestly blocked / rate-limited (NA) and **MUST NOT** halt the loop, drive STALLED, or veto GOAL_ACHIEVED (goal.md 779–782, 838–844). Do **not** autonomously re-probe J-22/J-23/J-24.

After J-33/34/35 land green offline and nothing regresses, **GOAL_ACHIEVED is reachable** on the buildable set (32/32 buildable journeys), with the live-fetch outcome of J-22/23/24/33/34/35 recorded as honestly blocked (NA) and non-halting.
