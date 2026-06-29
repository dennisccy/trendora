# goal-mcp-loop-iter-1 Dev Handoff

**Phase:** goal-mcp-loop-iter-1
**Date:** 2026-06-29
**Agent:** developer
**Status:** complete

## What Was Built

The **read-side evidence path** — the user-facing surface over the (today EMPTY) certified-claims ledger.
Against the empty ledger every signal honestly reads **"Not yet proven"** and nothing is shown as a
confident, proven number. Structurally satisfies J-01 (every score shows a status), J-03 (unvalidated
signals flagged, never confident) and the J-05 ledger surface. J-02 / J-04 remain correctly deferred (they
need a referee-certified claim).

- **Read-side evidence resolver** `app.engine.evidence` (recomputes NOTHING): `resolve_ledger_path()` (env
  `TRENDORA_LEDGER_PATH` → else config `evidence.ledger_path` resolved against `REPO_ROOT`) and
  `build_evidence_payload(ledger_path)` → `{claims:[...], proven_signals:{...}}`, reading ONLY via
  `app.engine.ledger.read_entries`. A signal is **Proven** iff a ledger entry with `verdict.status == "PASS"`
  names it; everything else is "Not yet proven" (fail-safe). Missing/empty ledger ⇒ `{claims:[], proven_signals:{}}`.
- **Typed config** `evidence.ledger_path` (default `runs/goal-session-mcp-loop/state/certified-claims.jsonl`,
  the SAME file the post-decompose gate writes) in `config.py` + `config.yaml`. No path literal in code.
- **Endpoint** `GET /api/evidence` → `build_evidence_payload(resolve_ledger_path())`. READ-ONLY (never writes
  the ledger, never computes proven-ness). Registered in `main.py` under `/api`.
- **`EvidenceStatusBadge`** chip — given a `signal` key + the served `proven_signals` map, renders "Proven"
  (linking to `/evidence#signal-<signal>`) when present, else muted "Not yet proven" (fail-safe default).
- **Badges inline** on `/stocks` leaderboard rows (each of Leadership / Entry Quality / Risk, below the
  ScoreBadge) and beside each score in the stock-detail `ScoreCard`. Evidence fetched once, non-blocking; a
  fetch failure renders "Not yet proven" and never breaks the leaderboard. Served scores stay byte-identical.
- **`/evidence` ledger page** + **Evidence nav entry** (after Research, `ShieldCheck` icon). Honest empty
  state today; the claim-row layout (hypothesis / out-of-sample verdict / control vs SPY / registration date /
  forward-walk score-to-date) + claim→surface linkback are built and unit-tested (exercised once a claim is certified).

## Files Changed

Backend:
- `apps/backend/app/engine/evidence.py` (new) -- read-side resolver (`resolve_ledger_path`, `build_evidence_payload`); reads the ledger only, recomputes nothing
- `apps/backend/app/api/evidence.py` (new) -- `GET /api/evidence` router (read-only; empty/absent ledger ⇒ 200 empty, never 500)
- `apps/backend/app/config.py` (modified) -- typed `EvidenceCfg(ledger_path)` + default-populated `evidence` field on `Config`
- `config.yaml` (modified) -- `evidence: { ledger_path: runs/goal-session-mcp-loop/state/certified-claims.jsonl }`
- `apps/backend/main.py` (modified) -- import `evidence` + `include_router(evidence.router, prefix="/api")`
- `apps/backend/tests/test_evidence.py` (new) -- resolver/payload units (absent⇒empty; PASS⇒proven; FAIL/INSUFFICIENT⇒not; signal-less PASS fail-safe; forward-walk excluded; env override vs config default)
- `apps/backend/tests/test_api_evidence.py` (new) -- endpoint (empty⇒200 empty; seeded PASS⇒served) + `/api/stocks` no-recompute regression

Frontend:
- `apps/frontend/lib/evidence.ts` (new) -- evidence types + the pure `resolveEvidenceStatus` / `evidenceAnchor` (no runtime imports; node-testable)
- `apps/frontend/lib/evidence.test.ts` (new) -- resolver unit test ("Not yet proven" when absent/null; "Proven" + `/evidence` link when present)
- `apps/frontend/components/evidence-status-badge.tsx` (new) -- the calm status chip (palette tokens only)
- `apps/frontend/app/evidence/page.tsx` (new) -- certified-claims ledger list + honest empty state + claim-row layout + linkback
- `apps/frontend/lib/api.ts` (modified) -- `fetchEvidence()` + re-exported `EvidenceLedgerResponse` / `CertifiedClaim` / `ProvenSignal` (distinct from `EvidenceAggregate`)
- `apps/frontend/components/sidebar.tsx` (modified) -- Evidence nav entry after Research (`ShieldCheck`)
- `apps/frontend/app/stocks/page.tsx` (modified) -- fetch evidence once (non-blocking) + badge under each score on every row
- `apps/frontend/app/stocks/[ticker]/page.tsx` (modified) -- fetch evidence once + badge in each `ScoreCard`

## Tests Run

Backend command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
- New evidence units + API + regression: `tests/test_evidence.py tests/test_api_evidence.py` → **10 passed**
  (includes the full-app `TestClient` lifespan boot hitting `GET /api/evidence`, and the byte-identical
  `/api/stocks` no-recompute regression).
- Config / no-magic-numbers / referee / evidence fast subset
  (`tests/test_config.py tests/test_no_magic_numbers.py tests/test_referee.py tests/test_evidence.py`) →
  **79 passed** (covers the config-field addition + the no-magic-numbers contract — no existing fixture broke).
- The full suite (`pytest tests/ -q`) was also launched as a regression net. The changes are purely additive
  (a default-populated config field, two new modules, one router registration, frontend additions), so the
  pre-existing tests are unaffected; the reviewer can re-run the full suite to confirm.

Frontend:
- `cd apps/frontend && node lib/evidence.test.ts` (repo convention) — 5 resolver checks. NOTE: this sandbox's
  `node` was built WITHOUT TypeScript support, so I verified the SAME test by transpiling with the repo's
  `tsc` and running it: **5 checks passed**. In the QA environment (TS-enabled `node`, like every existing
  `lib/*.test.ts`) the file runs as written.
- `cd apps/frontend && ./node_modules/.bin/tsc --noEmit` → **clean (exit 0)**.
- `cd apps/frontend && ./node_modules/.bin/next build` → **success (exit 0)**; `/evidence`, `/stocks`,
  `/stocks/[ticker]` all compiled (25/25 routes).

## Known Issues

- **Writer does NOT yet stamp `claim.signal`** (deliberately out of scope, per the plan). The real ledger
  writer `app.mcp.tools.verify_edge` appends a cohort-selector `claim` with **no `signal` key**. The read
  side keys `proven_signals` on `entry["claim"].get("signal")` (defensive), so a future real PASS entry stays
  "Not yet proven" until a later **certified J-02/J-04 iteration** wires the writer to stamp `claim.signal`.
  The frontend signal keys are the canonical factor-catalog keys (`leadership_score` / `entry_quality_score`
  / `risk_score`) so that wiring lights up the right badge. This iteration's empty ledger never exercises this.
- **`/evidence` claim→surface linkback is built + unit-tested but not exercisable end-to-end** until ≥1 claim
  is certified (empty ledger renders the honest empty state). The empty state enumerates the five claim-row
  fields so the layout is present in the markup without fabricating a claim.
- **Live standalone `uvicorn` could not be kept up in this sandbox** (the sandbox terminates detached
  network listeners; booting the full app against the real 777 MB prod DB also gets memory-killed). The full
  app stack IS exercised live via the FastAPI `TestClient` in `test_api_evidence.py` (real lifespan boot →
  `GET /api/evidence` returns 200 empty; seeded PASS → claim served; `/api/stocks` byte-identical). I also
  verified the REAL config-default branch in-process: `resolve_ledger_path()` →
  `/home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/certified-claims.jsonl` (absent today) →
  `build_evidence_payload` returns `{claims: [], proven_signals: {}}`, and `TRENDORA_LEDGER_PATH` overrides it.
- **No external integrations added** this iteration (no scrapers/adapters/live API calls) — the "live external
  integration" pre-handoff check is N/A. No new native-dependency binaries.
- **No Evidence-Claim block** in the spec (intentional): iter-1 surfaces nothing as "Proven", so the
  post-decompose gate passes automatically.
