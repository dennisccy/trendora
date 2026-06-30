# goal-mcp-loop-iter-4 Dev Handoff

**Phase:** goal-mcp-loop-iter-4
**Date:** 2026-06-30
**Agent:** developer
**Status:** complete

## What Was Built

A **frontend-surfacing + one backend confirming-test** iteration that delivers **J-04
(regime-conditioned evidence)** — the sole remaining Must-have journey. The Evidence Claim was
already certified by the post-decompose gate (the 2nd `certified-claims.jsonl` entry: Breakout-watch ×
**Risk-on** event-study, `status: PASS`, holdout edge **+6.12%** vs SPY, p 0.0004998). This iteration
makes that certified edge **discoverable and honestly labeled** in the UI. **Zero `apps/backend/app/**`
diff; zero engine / referee / endpoint diff.**

- **Regime label on regime-conditioned claim rows** (`/evidence` `ClaimRow`): a calm, prominent
  **"Regime: Risk-on"** badge in the row header, read **verbatim** from the claim's own `claim.regime`
  selector. Hidden entirely when the cohort carries no regime — so the leadership (score) row looks
  unchanged. (J-04's "clearly labeled with the regime it holds in.")
- **Honest title + linkback for the non-score (setup) claim** (same `ClaimRow`): the signal-less
  event-study claim now renders a meaningful title **"Breakout-watch setup"** + an anti-hype framing line
  **"Out-of-sample edge in the Risk-on regime"** + an honest linkback **"Backs: Research event-study lab →"**
  (`/research/event-study`) — replacing the old misleading "Unmapped signal" + "Backs: Stocks leaderboard →".
- **Dashboard → Evidence affordance** (`RegimeGlanceCard` in `app/page.tsx`): a discoverable link
  **"See evidence proven in this regime →"** → `/evidence`. Additive; the regime number/label
  (Risk-on, 76.05) is unchanged.
- **Two pure, testable helpers** in `apps/frontend/lib/evidence.ts`: `regimeLabel(claim)` (the verbatim
  regime selector, blank/absent → `null`) and `claimSurface(claim)` (the title + linkback resolver — a
  score signal keeps its **byte-identical** signal-key title + "Stocks leaderboard" linkback; a signal-less
  event-study cohort gets the honest subject-framed title + Research-lab linkback). The `/evidence`
  `surfaceForSignal` inline helper was superseded by `claimSurface` and removed.
- **Backend confirming unit test (TEST-ONLY)**: `build_evidence_payload` over the live 2-entry ledger
  returns `proven_signals` keyed **only** on `leadership_score`, and `claims[]` includes the regime row
  (`claim.regime == "Risk-on"`, `proven == true`, `signal == null`); `_resolve_signal` → `None` for the
  event-study claim. Guards the anti-regression invariant: the regime claim adds **no** signal and never
  overwrites `leadership_score`.

The leadership (score) row's `signal` text, title, and **"Backs: Stocks leaderboard →"** linkback are
**byte-identical** to before (J-05 must not regress) — confirmed in a real browser (see below).

## Files Changed

- `apps/frontend/lib/evidence.ts` — added the pure `regimeLabel()` + `claimSurface()` helpers (and the
  `ClaimSurface` interface). Read-only re-display; fabricates nothing; never decides proven-ness.
- `apps/frontend/lib/evidence.test.ts` — added 5 cases: regime label present/absent/blank; score-row
  title+linkback byte-identical; signal-less event-study → honest title + non-leaderboard linkback.
- `apps/frontend/app/evidence/page.tsx` — `ClaimRow` now uses `claimSurface` + `regimeLabel`; renders the
  "Regime: <label>" badge + the honest title/subtitle for the non-score claim; removed `surfaceForSignal`.
- `apps/frontend/app/page.tsx` — `RegimeGlanceCard` gains the "See evidence proven in this regime →"
  affordance to `/evidence` (added `next/link` import).
- `apps/backend/tests/test_evidence.py` — added the 2-entry-ledger confirming test + the
  `_regime_event_study_entry()` builder; imported `_resolve_signal`. **No `apps/backend/app/**` change.**

## Tests Run

**Backend** — `cd apps/backend && .venv/bin/python -m pytest tests/test_evidence.py -v`
Result: **10 passed** (the new `test_build_payload_regime_event_study_claim_adds_no_signal` included).
Also `pytest tests/test_api_evidence.py -q` (the `/api/evidence` endpoint-shape + empty-ledger-200
regression) — **3 passed** (~150 s; app spins up the seed DB).

**Frontend unit** (Node v22.22.1 has no native TS loader — transpiled with the repo's own `tsc` 5.7.2
`--rewriteRelativeImportExtensions` to ESM and ran the emitted JS; see Known Issues):
- `lib/evidence.test.ts` → **15 passed** (10 prior + 5 new).
- `lib/api-base.test.ts` → **11 passed** (regression, unchanged).

**Type-check / build:** `tsc --noEmit` → **clean**; `next build` → **clean** (`/`, `/evidence`,
`/research/event-study` all compile).

**Live browser verification (Chrome MCP, frontend :3255 → backend :8255):**
- **Pre-flight:** `/api/health` → 200 `readiness: ready`; `/api/evidence` → **2 claims**,
  `proven_signals` keys `["leadership_score"]` (proven `true`); regime row: `kind=event-study`,
  `signal=null`, `regime=Risk-on`, `subject=Breakout-watch`, `holdout_edge 0.06124590639955655`,
  `register_date 2026-06-30`.
- **J-04:** Dashboard shows **"Market Regime Risk-on 76.05"** + the **"See evidence proven in this
  regime →"** affordance (href `/evidence`). On `/evidence`, the 2nd row renders **"Breakout-watch
  setup"**, the **"Regime: Risk-on"** badge, **"Out-of-sample edge in the Risk-on regime"**,
  **"Backs: Research event-study lab →"**, **+6.12%** holdout / **+6.12%** vs SPY / **2026-06-30** —
  **byte-identical to `GET /api/evidence`**.
- **J-05 (no regression):** the leadership row still reads **"leadership_score"** / **"PASS"** /
  **+6.36%** / **"Backs: Stocks leaderboard →"** with **no** regime badge — unchanged.

## Pre-handoff verification

- **Service startup:** `scripts/start-backend.sh` (:8255) + `scripts/start-frontend.sh` (:8255-baked
  `next start`, :3255) both started cleanly (frontend "Ready in 251 ms", no errors). All routes 200.
  Both QA servers were **killed** afterward; ports 8255/3255 are **free**.
- **External integrations:** none added this iteration (no adapters/scrapers/external APIs). The only
  live "integration" is frontend→backend `/api/evidence`, verified above end-to-end.
- **Native deps:** none added.

## Known Issues

- **Frontend unit-test runner (environmental, pre-existing — not introduced here):** the `.test.ts`
  files document `node lib/evidence.test.ts`, but the installed Node (v22.22.1) has no TypeScript loader
  (`ERR_UNKNOWN_FILE_EXTENSION` for `.ts`). I ran them by transpiling with the project's own `tsc` 5.7.2
  (`--rewriteRelativeImportExtensions`) and executing the emitted ESM — all 26 frontend checks pass. I did
  **not** add the optional `tsx` devDependency (the iter-3 carry): it requires an `npm install` that risks
  the local-first/offline constraint and is explicitly "not required for DoD"; the `tsc`-transpile path is
  reliable in this environment. If a future online iteration wants the documented `node lib/*.test.ts`
  command to work directly, add `tsx` through the supply-chain security gate.
- **Stale-process port conflict (operational, resolved):** a leftover `next-server` from a prior session
  was already holding :3255 and served an **old** bundle, so my first `next start` hit `EADDRINUSE` and the
  page showed pre-iter-4 output. `start-frontend.sh` does **not** free the port before binding (unlike
  `dev.sh`). I killed the stale holder (`fuser -k 3255/tcp`) and restarted; the new bundle then served and
  J-04 verified. **Note for QA:** if the browser lane ever shows stale UI, confirm no orphan `next-server`
  owns the frontend port before scoring.
- **`next build` clears the QA serve stamp.** A manual `next build` rewrites `.next` and drops
  `.next/.qa-serve-base`. I rebuilt with the correct baked base (`NEXT_PUBLIC_API_URL=http://localhost:8255`,
  port `8255`) and **restored the stamp** (`http://localhost:8255|8255`), so the browser-QA lane takes the
  fast `next start` path (no in-window rebuild). If any later step rebuilds, `start-frontend.sh` self-heals
  with one bounded (~18 s) rebuild.
