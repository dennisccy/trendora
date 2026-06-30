# goal-mcp-loop-iter-5 Dev Handoff

**Phase:** goal-mcp-loop-iter-5
**Date:** 2026-06-30
**Agent:** developer
**Status:** complete

## What Was Built

This is a **verification-integrity + QA-harness fix** iteration, **not** a feature delivery. All five
Must-have journeys' features are already built and referee-certified; the only developer task was the
single allowed code change that lets the canonical browser-qa lane bind the frontend port reliably.

- **Pre-bind port-free preamble in `scripts/start-frontend.sh`** (the symlinked real file is
  `incredible_auto_dev/scripts/start-frontend.sh`). Inserted immediately **before** the final
  `exec npx next start -p "$FRONTEND_PORT"`, it frees `$FRONTEND_PORT` right before binding:
  1. `lsof -ti :$FRONTEND_PORT | kill -9` any owning PIDs,
  2. `fuser -k -9 $FRONTEND_PORT/tcp` (catches child processes `lsof` lists under a different PID),
  3. a **bounded** wait loop (≤ ~5 s: 50 × `sleep 0.1`) that re-kills until `lsof` shows no owner
     **AND** `ss -tlnH sport = :$FRONTEND_PORT` shows no lingering socket.
  The loop **breaks immediately when the port is already free**, so the normal pipeline path is
  unaffected. This mirrors the proven pattern already in `scripts/dev.sh` (lines 22–41), but **scoped to
  `$FRONTEND_PORT` only** — `start-backend.sh` owns the backend port, so this script must not touch it.
- **Placement rationale:** the preamble sits *after* the stamp-guarded `next build` and *immediately
  before* `exec next start`. Freeing the port right before bind (not before the ~18 s build) minimizes
  the window in which a racing process could re-grab the port. The existing build/stamp/start logic is
  **unchanged** — only the preamble was added.

This eliminates the exact iter-4 failure: a stale `next-server` from a prior run held the port, so the
canonical `browser-qa-agent` lane SKIPPED all 11 checks ("frontend not running") or risked serving a
**stale** bundle.

## Files Changed

- `scripts/start-frontend.sh` (real path `incredible_auto_dev/scripts/start-frontend.sh`) — added the
  pre-bind port-free preamble for `$FRONTEND_PORT` immediately before `exec npx next start`. **+26 lines,
  zero deletions.** No other logic touched.

**Zero `apps/` diff** — no product code (backend or frontend) was modified. Confirmed via
`git diff --name-only` (only the harness script + the auto-generated `runs/.../telemetry.jsonl` appear).

## Tests Run

**Backend unit/integration** — `cd apps/backend && .venv/bin/python -m pytest tests/test_evidence.py tests/test_api_evidence.py -q`
Result: **13 passed** (includes `test_build_payload_regime_event_study_claim_adds_no_signal`). No regressions.

**Frontend unit** (Node v22.22.1 has no native TS loader — transpiled with the repo's own `tsc` 5.7.2
`--rewriteRelativeImportExtensions` to ESM, ran the emitted JS, per the iter-4 path):
- `lib/api-base.test.ts` → **11 passed**
- `lib/evidence.test.ts` → **15 passed**
- Total **26 passed**. No regressions. (These cannot be affected by a harness-only change — zero `apps/` diff.)

**Frontend build** — `npx next build` (env `NEXT_PUBLIC_API_URL=http://localhost:8255`): **clean, exit 0**;
all routes compile (`/`, `/stocks`, `/stocks/[ticker]`, `/evidence`, `/sectors`, `/themes`, `/watchlist`).
The current bundle + `.next/.qa-serve-base` stamp (`http://localhost:8255|8255`) are left in place so the
downstream browser-qa lane's `start-frontend.sh` skips the rebuild and goes straight to bind.

**Live harness error-case (the deliverable verification)** — deliberately occupied `$FRONTEND_PORT` (3255)
with a stale `python3 -m http.server` serving an `OLD-STALE-MARKER`, then ran `scripts/start-frontend.sh`:
- The preamble logged `[start-frontend] Freeing port 3255 (held by: <pid>)` and **killed the stale listener**.
- `next start` then **bound successfully** (`✓ Ready in 252ms`).
- Readiness probe returned **HTTP 200**, `GET /stocks` → **200**, and the served body is the **live Next.js
  bundle** with the stale marker **gone** — i.e. the current bundle is served, not the stale one.
- This is the precise iter-4 failure mode, now eliminated.

**Server cleanup:** all test servers (`next start` / `next-server` / the stale `http.server`) were killed;
port 3255 verified **FREE** with no stray processes after the run.

## Known Issues

- **Out of developer scope (downstream pipeline stages, by design):**
  - The **canonical `browser-qa-agent` lane** result (`reports/phase-goal-mcp-loop-iter-5-ui-test-results.md`,
    fresh UT-* screenshots for all five journeys) is produced by the browser-qa-agent stage, not here. My
    change is what *unblocks* that lane; the live error-case test above demonstrates it will now bind.
  - The **post-QA audit handoff** (`docs/handoffs/goal-mcp-loop-iter-5-audit.md`) is the auditor stage's
    DoD item (it stalled at `qa_complete` in iter-3 and iter-4). Not a developer deliverable.
- **No `## Evidence Claim` block** was added — there is no new "proven" claim this iteration (pure
  verification + harness fix), so per `docs/goal.md` Loop mechanics the post-decompose gate passes
  automatically. This is intentional, not an omission.
- **Frontend unit-test runner (environmental, pre-existing — not introduced here):** the `.test.ts` files
  document `node lib/*.test.ts`, but the installed Node (v22.22.1) has no TS loader. They were run via the
  repo's own `tsc` transpile (the reliable iter-3/iter-4 path). The optional `tsx` devDependency was **not**
  added — it is explicitly not required for DoD and an `npm install` risks the local-first/offline constraint.
- **`Frontend Present: yes` with zero UI-code change** is intentional: it is the machine-read line
  `qa-phase.sh` uses to require the Chrome MCP browser lane (the spec is IN SCOPE → Frontend because the
  browser-qa-agent must run against the live frontend). It is **not** a request to write UI code — the
  user-visible product is byte-identical to iter-4.
