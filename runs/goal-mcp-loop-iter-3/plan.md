# goal-mcp-loop-iter-3 Execution Plan

> **Verification-only iteration.** The evidence read-path is already shipped, reviewed,
> unit-tested, coherence-clean, and data-verified. The deliverable is a GREEN, evidence-backed
> **browser** lane — not new code. The expected app-source diff is **zero**; any fix is confined
> to QA bring-up scripts and must be justified in the handoff.

## What to Build
- Make the goal-mode browser-QA lane actually **run** this iteration: the QA frontend
  (`http://localhost:3255`) must reach the QA backend (`http://localhost:8255`) so `/stocks`,
  `/stocks/{ticker}`, and `/evidence` render with live data — never "Checking backend…", an empty
  leaderboard, or "Backend unavailable".
- **Diagnose the iter-2 bring-up failure** (all 18 UI tests SKIPPED, reason "frontend not running at
  http://localhost:3255", `browser_checks_run: false`, and **no** `browser-qa-agent` telemetry record).
  iter-2 used port **3255 with NO port drift**, so the gate (`_wait_for_frontend_ready`, 120s budget)
  failed because the frontend root URL never returned 2xx/3xx in budget — i.e. the frontend process
  died / cold `next dev` compile overran the budget, and/or the backend was unstable. This is an
  **operational bring-up failure, not a code regression** (iter-2 `next build`, `tsc`, backend +
  frontend units, and the `/api/evidence` curl were all green).
- **Apply the MINIMAL bring-up fix** so both services come up and stay mutually reachable through the
  test window. A **zero app-source-diff** outcome is expected and acceptable.
- **Browser-prove J-02 and J-05** (target journeys) and **re-confirm J-01 and J-03 with FRESH captures**
  (their evidence is stale since iter-1; iter-2's lane skipped). Displayed numbers must be
  **byte-identical to `GET /api/evidence`** (anti-goal #3: correctness, not mere rendering).
- Produce an auditable trail: `status.json browser_checks_run: true`, a real `browser-qa-agent`
  `agent_invocation` telemetry record, a non-SKIPPED `ui-test-results.md`, and ≥1 **real** screenshot
  per target journey (iter-0 lesson: no record / all-SKIP = nothing verified).

## Agents Required
- **developer: yes** — diagnose the bring-up defect, apply the minimal fix in QA bring-up scripts only,
  demonstrate both services boot and are mutually reachable (curl pre-flight), re-run the unit suites,
  and write the handoff. Must NOT touch app feature code.
- backend-data: **no** — no `apps/backend/app/**` change. The evidence read-path
  (`engine/evidence.py`, `api/evidence.py`, `api/health.py`, `engine/ledger.py`, `engine/referee.py`)
  is frozen and already serves correct values.
- frontend-ux: **no** — no `apps/frontend/**` change. `lib/api-base.ts:resolveApiBase` already returns
  the configured base verbatim for a localhost page (rule 3), so the localhost QA path needs no code change.
- (pipeline-driven, **full** depth) **browser-qa-agent: MUST run (not skip)** — proves J-01/J-02/J-03/J-05
  with real screenshots. `Frontend Present: yes` forces the browser lane.

## Frontend Present

Frontend Present: yes

## Files to Create/Modify
- `scripts/start-frontend.sh` — **candidate fix.** If cold `next dev` compile (or process death) is the
  proven cause, serve deterministically from a **pre-built** `.next` via `next start` so the readiness
  probe gets a fast 2xx. **Pitfall:** do NOT run `next build` *inside* the readiness window — pre-build
  first, then `next start` only. Else: no change.
- `scripts/start-backend.sh` — **candidate fix.** If uvicorn is OOM-killed under the 777 MB seed DB
  (the `ulimit -v` memory cap from `config.server.memory_cap_mb`), relax/raise `CHAIN_SERVER_MEMORY_CAP_MB`
  for the QA run so `/api/health` reaches 200 and stays up. Else: no change.
- `scripts/automation/goal-iter-lean.sh` — **only if** diagnosis proves a harness-level ordering/port
  defect (this lane lacks the base-port reconciliation that `browser-qa-phase.sh` has, and it deems the
  backend "up" on *any* HTTP status, not a 200/ready). See Scope & Drift note — prefer the narrowest fix;
  this is framework code with cross-project blast radius.
- `docs/handoffs/goal-mcp-loop-iter-3-dev.md` — **required.** State the diagnosed bring-up root cause and
  the exact fix, or explicitly "no code change needed — verification-only".
- **NONE** under `apps/backend/app/**` or `apps/frontend/**` — app feature code is frozen.

Pipeline-produced (not by the developer): `runs/goal-mcp-loop-iter-3/status.json`
(`browser_checks_run: true`), `reports/phase-goal-mcp-loop-iter-3-ui-test-results.md` (non-SKIPPED),
`reports/qa/goal-mcp-loop-iter-3-evidence/` (≥1 real screenshot per target journey),
`runs/goal-session-mcp-loop/telemetry.jsonl` (a `browser-qa-agent` record).

## UI Evolution
- New user-facing capability: **none new.** An already-built capability becomes **observably true in the
  browser** — the user can see the Leadership "Proven" badge, drill into its proof, and audit the backing
  claim on `/evidence`.
- New information displayed: **none new.** The proof panel and populated `/evidence` row already exist in
  code; this iteration proves they render with values byte-identical to `/api/evidence`.
- New user actions: **none new.**
- UI surface changes: **none new** — `/stocks`, `/stocks/{ticker}`, `/evidence` are unchanged. Verification,
  not surface work.
- Navigation changes: **none** (the Evidence nav entry already exists). No blueprint re-approval needed.

## Visual Requirements
- Component patterns (reused, unchanged): `EvidenceStatusBadge` (inline "Proven" / "Not yet proven" chip on
  leaderboard rows + stock-detail score cards), `ScoreProofPanel` ("Why proven?" drill-down on `/stocks/{ticker}`),
  and the `/evidence` ledger page. No new components.
- Layout: existing Trendora surfaces (Stocks leaderboard table, stock-detail score cards, Evidence ledger
  list) — no layout change.
- Key visual effects: none new — keep the existing minimal, data-dense, evidence-first treatment.
- States to handle (the crux of this iteration): the bring-up must NOT mistake a non-ready state for a pass.
  **"Checking backend…", an empty leaderboard, "No regime for this date", and "Backend unavailable" are
  HARD-FAIL bring-up states, never passes.** The honest health badge (J-40) must still render correctly
  when the backend is down — never a fabricated "Ready". A pass requires the **Ready** badge, a populated
  (~120-row) leaderboard at the default as-of, and the proven/unproven chips reading correctly.

## Pre-flight Gate (must pass BEFORE the browser-qa-agent runs)
1. `curl http://localhost:8255/api/health` → **200**.
2. `curl http://localhost:8255/api/evidence` → `proven_signals.leadership_score.proven == true`.
3. `http://localhost:3255/stocks` (default/latest view, no `?as_of=`) renders **≥1** leaderboard row
   (iter-1 rendered ~120 rows at the seed frontier **2026-05-28** — use that default view).
Only when all three hold may browser tests dispatch. A failure here is a FAIL of the bring-up gate.

## Key Test Scenarios
Reuse the iter-2 UI test plan (UT-01..UT-18 already enumerate these flows). All numeric checks compare to
a live `GET /api/evidence` — the values below are the known-good reference, not a substitute for the
byte-identical comparison.
- **J-02 (target):** `/stocks` → click a stock → expand "Why proven?" on the **Leadership** card → panel
  shows OOS **PASS**, holdout edge **+6.36%**, **p ≈ 0.0005**, cohort **n = 12297**, the "vs SPY (benchmark
  control)" excess, and the claim id + **"registered 2026-06-30"** — byte-identical to `/api/evidence`.
- **J-05 (target):** `/evidence` renders the populated `leadership_score` row with all five fields
  (hypothesis, OOS verdict, SPY control, registration date, forward-walk score-to-date); the
  "Backs: Stocks leaderboard →" linkback round-trips; and the leaderboard "Proven" badge links to
  `/evidence#signal-leadership_score`.
- **J-01 (re-confirm, FRESH capture):** every `/stocks` row shows an evidence status; **Leadership reads
  "Proven"**; no displayed score lacks a status.
- **J-03 (re-confirm, FRESH capture):** **Entry Quality** and **Risk** read **"Not yet proven"** (muted) on
  `/stocks` and stock detail, with **no** "Why proven?" toggle on those two cards.
- **Invariants to NOT regress:** empty/absent ledger → 200 with `{"claims": [], "proven_signals": {}}`
  (never 500); backend-down → honest health badge ("Backend unavailable…"), never a faked "Ready".
- **Unit suites green:** backend `pytest` (incl. `tests/test_evidence.py`); frontend `lib/evidence.test.ts`
  + `lib/api-base.test.ts`. No regression; no anti-goal language (no return/price/buy-sell/alpha) on any
  proof surface; secret scan clean; determinism / no-lookahead untouched.

## Diagnostic Order (for the developer)
1. **Reproduce the harness path:** start `scripts/start-backend.sh` then `scripts/start-frontend.sh` (the
   commands the lane invokes via `ensure_services_running`); confirm whether the frontend port 3255 ever
   serves and whether `/api/health` on 8255 returns 200 and stays up.
2. **Frontend reachability:** does `next dev` finish its initial compile and keep the port alive within the
   120s gate, or does the process die (sandbox terminates detached listeners; memory pressure)? If `next dev`
   is the proven flake source, switch to a pre-built `next start` (see Files note).
3. **Backend stability:** is uvicorn OOM-killed under the 777 MB seed DB / `ulimit -v` cap? If so, relax
   `CHAIN_SERVER_MEMORY_CAP_MB` for the QA run so health reaches and holds 200.
4. **Readiness ordering:** the lane deems the backend "up" on any HTTP status (listening ≠ ready). Confirm
   `/api/health` is 200 (not `initializing`) before the browser loads `/stocks`, else the leaderboard is empty.
Apply the **smallest** change that makes the pre-flight gate pass, and document the proven root cause.

## Scope, Drift & Assumptions
- **Goal alignment: confirmed.** This iteration advances `docs/goal.md` success criteria (visible, accurate
  evidence status; auditable proof; correct displayed numbers) by browser-proving the certified
  `leadership_score`. It correctly **adds no `## Evidence Claim`** (no new "proven" signal — the
  post-decompose gate passes automatically) and correctly **defers J-04** (no regime-scoped certified claim
  exists yet). No drift from the goal.
- **Hard guardrails:** do NOT modify the evidence feature code (backend or frontend). Do NOT add evidence
  badges to `/sectors`, `/themes`, or research labs. Do NOT add a new Evidence Claim or any new "proven"
  signal. Do NOT touch the scoring / regime / forward-return / research engines (determinism + no-lookahead).
  Any diff outside the QA bring-up scripts is out-of-scope and must be justified in the handoff.
- **Scope nuance (flagged):** the spec scopes the fix to "project QA start scripts only," but the strongest
  *systemic* gap the investigation surfaced is in the harness lane `scripts/automation/goal-iter-lean.sh`
  (which `scripts/` symlinks into the framework). The spec's hard boundary is "no app feature-code change";
  honor that absolutely. Touch `goal-iter-lean.sh` only if the start-script fixes cannot make the gate pass,
  prefer the narrowest change, and document the blast radius.
- **Key risk / assumption:** the sandbox has previously OOM-killed uvicorn and terminated detached listeners
  (iter-1 ran via TestClient). This iteration assumes both live services **can** be kept up and mutually
  reachable in this environment (iter-1 rendered 120 browser rows once, proving it is possible, just flaky).
  If, after the bring-up fixes, the services genuinely cannot stay up to serve a real browser, that is a
  blocking environment finding for the handoff — an all-SKIP result still counts as a FAIL, never a pass.
