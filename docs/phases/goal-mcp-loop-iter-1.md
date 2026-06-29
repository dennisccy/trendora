# Goal Iteration 1 — Read-side evidence path: status badges + ledger page (empty ledger ⇒ "Not yet proven")

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 1
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-01, J-03, J-05
- **Required-still-passing journeys:** none (baseline — J-01..J-05 are all `unknown`; no journey is passing yet)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## GOAL

Every score on `/stocks` and on stock-detail carries a visible, honest evidence status, and a new nav-reachable **Evidence** ledger page renders the certified-claims ledger — so against today's empty ledger every signal honestly reads **"Not yet proven"** and nothing is presented as a confident, proven number.

## BACKGROUND

Iter-0 (baseline) returned **ESCALATE**: the lean pipeline's browser-QA lane never executed (no `ui-test-results` file, empty evidence dir, no `browser-qa-agent` telemetry record), so J-01..J-05 are all `unknown` rather than empirically verified. ESCALATE mandates **full** depth this iteration, which guarantees the full browser-QA lane runs and captures real evidence — directly closing the iter-0 lesson (do not infer pass/fail from a static dev scan; confirm `browser-qa-agent` actually ran). The referee, append-only ledger, MCP "window", and post-decompose gate already exist (`app.engine.referee`, `app.engine.ledger`, `app.mcp.tools:verify_edge`, `project-extensions/gates/`); what is MISSING is the **read-side** user-facing surface. This iteration builds exactly that — a read-only `GET /api/evidence` over the ledger, an inline "Proven / Not yet proven" status badge, and the `/evidence` page — which structurally satisfies **J-01** (every score shows a status), **J-03** (unvalidated signals flagged, never confident), and the **J-05** ledger surface. **J-02** (drill into a *Proven* score) and **J-04** (regime-conditioned *Proven* evidence) require a referee-certified claim and are deferred to a later certified iteration.

## IN SCOPE

### Backend
- [ ] New module `apps/backend/app/engine/evidence.py` — the **read-side** evidence resolver (single source of truth for displayed proven-ness; recomputes NOTHING):
  - `resolve_ledger_path()` → returns the certified-claims ledger path: env `TRENDORA_LEDGER_PATH` if set, else the config `evidence.ledger_path` resolved against the repo root. This MUST resolve to the SAME file the post-decompose gate writes (`runs/goal-session-mcp-loop/state/certified-claims.jsonl`, set by `run-goal.sh`).
  - `build_evidence_payload(ledger_path)` → reads entries via `app.engine.ledger.read_entries(ledger_path)` ONLY (a missing file is an empty ledger) and returns `{ "claims": [...], "proven_signals": { <signal_key>: {...} } }`. A ledger entry contributes a **Proven** signal ONLY when its `verdict.status == "PASS"`; it maps to `proven_signals[entry["claim"]["signal"]]` (carrying claim id, register date, out-of-sample verdict summary, control comparison, forward-walk score-to-date — read verbatim from the entry). Any signal NOT present in `proven_signals` is, by definition, "Not yet proven" (fail-safe default). Absent/empty ledger ⇒ `{ "claims": [], "proven_signals": {} }`.
- [ ] Config: add a typed `evidence.ledger_path` key to `apps/backend/app/config.py` + a value in `config.yaml` (default `runs/goal-session-mcp-loop/state/certified-claims.jsonl`, resolved relative to `REPO_ROOT`). No path literal lives in the endpoint or resolver (project rule: No magic numbers).
- [ ] New router `apps/backend/app/api/evidence.py` — `GET /api/evidence` → `build_evidence_payload(resolve_ledger_path())`. READ-ONLY: it never writes the ledger and never computes proven-ness. Register it in `apps/backend/main.py` (`application.include_router(evidence.router, prefix="/api")`).
- [ ] Treat `app.engine.referee`, `app.engine.ledger` (append/read), `app.mcp.tools`, and `project-extensions/gates/` as READ-ONLY dependencies — consume them; do not modify them.

### Frontend
- [ ] New component `apps/frontend/components/evidence-status-badge.tsx` — a calm, unmissable status chip (palette tokens only; NOT to be confused with the existing `evidence-panels.tsx`, which is the Backtest forward-tested aggregate). Given a `signal` key and the served `proven_signals` map, it renders **"Proven"** (linking to the backing entry on `/evidence`) when `proven_signals[signal]` is present, else **"Not yet proven"** (muted). Fail-safe default is "Not yet proven".
- [ ] `apps/frontend/lib/api.ts` — add `fetchEvidence()` and distinct types `EvidenceLedgerResponse` / `CertifiedClaim` / `ProvenSignal` (do NOT reuse the existing `EvidenceAggregate`, which is the Backtest forward-evidence type).
- [ ] `apps/frontend/app/stocks/page.tsx` — fetch evidence once (non-blocking, keyed like the existing header fetches) and render an `EvidenceStatusBadge` in each score area (Leadership / Entry Quality / Risk) on every leaderboard row. A fetch failure renders "Not yet proven" honestly and never breaks the leaderboard.
- [ ] `apps/frontend/app/stocks/[ticker]/page.tsx` — render the status badge beside each of the three scores (this is the J-02/J-03 drill home; the "Proven" drill panel itself is deferred).
- [ ] New page `apps/frontend/app/evidence/page.tsx` — the certified-claims ledger list. Each claim row shows: the hypothesis (claim cohort selectors), the out-of-sample verdict, the control comparison (vs SPY), the registration date, and the forward-walk score-to-date — read verbatim from `/api/evidence`. Honest empty state when zero claims ("No certified claims yet — every signal currently reads Not yet proven"). Each claim links back to the surface(s) whose badge it backs (linkback wiring built + unit-tested; exercised once a claim is certified).
- [ ] `apps/frontend/components/sidebar.tsx` — add `{ href: "/evidence", label: "Evidence", icon: <ShieldCheck-style lucide icon> }` after the Research entry. This IMPLEMENTS the already-approved blueprint Information Architecture (the IA skeleton already lists `Evidence [NEW] /evidence`), so it is conformance, not a nav-skeleton change.

### New user-facing capability
Every score the user sees on `/stocks` and stock-detail now carries a visible evidence status, and a new **Evidence** ledger page is reachable from the persistent nav in ≤2 clicks. Against today's empty ledger, every status honestly reads "Not yet proven" — establishing the evidence-first frame end to end.

### New information displayed
The "Proven / Not yet proven" status chip on each score; the Evidence ledger page (an honest empty-state today, with the claim row layout — hypothesis, out-of-sample verdict, control comparison, registration date, forward-walk score-to-date — ready for the first certified claim).

### New user actions
Click "Evidence" in the nav to open the ledger; click a "Proven" badge to jump to its backing ledger entry (when a claim exists); claim rows link back to the surfaces they back.

### UI surface changes
`/stocks` leaderboard rows and the stock-detail score areas gain an inline status chip; a new `/evidence` page; a new Evidence nav entry.

### Product surface delta
The product shifts from "explainable scores" to "explainable AND honestly-statused scores": with zero certified claims, the honest, uniform state is "Not yet proven" — never a confident-looking proven number — which is exactly the skeptical, evidence-first posture the goal demands.

### Blueprint conformance
All pages live under the already-approved Information Architecture: the inline badges sit on `/stocks` (Stocks) and `/stocks/{ticker}` (Stocks → Stock Detail, row-reached); the ledger lives on `/evidence` under the sanctioned **Evidence [NEW]** nav section the blueprint IA already lists. No new home is invented and no nav-skeleton change is made beyond implementing that already-approved Evidence section (so no `blueprint.reapproval-requested` is needed).

### Data-contract additions
No NEW contract value — the "Evidence status + certified-claim" value is already registered (Data Contract row 1). This iteration builds its **read side**: the resolver `app.engine.evidence` over `app.engine.ledger:read_entries`, served by the single endpoint `GET /api/evidence`; a signal is "Proven" ONLY when a PASS certified-claim entry names it, else "Not yet proven". No second computation or second endpoint is introduced for any existing contract value — the three served scores stay byte-identical and the badge only attaches additively. The blueprint row is updated in place (additive) to register these concrete read-side names.

## OUT OF SCOPE

- **J-02** (drill into a *Proven* score) and **J-04** (regime-conditioned *Proven* evidence) — both require at least one referee-certified claim; deferred to a later iteration that proposes a referee-certifiable claim and earns a PASS at the post-decompose gate.
- Any evidence-claim proposal / referee certification THIS iteration — iter-1 surfaces nothing as "Proven", so it carries NO Evidence-Claim block and passes the gate automatically.
- Status badges on `/sectors`, `/themes`, and the Research labs — a later iteration extends the badge cross-surface (the blueprint allows it; iter-1 scopes to the Stocks surfaces + the Evidence page to stay tight).
- Modifying the referee, the ledger writer (`append_entry`), the MCP window, or the post-decompose gate — all already built and consumed read-only.
- Modifying shared framework scripts (`scripts/` is a symlink to `incredible_auto_dev/scripts/`) — the read-side ledger path is config/env-driven so `start-backend.sh` needs no change.
- Changing any existing score / regime / forward-return computation — badges are purely additive; served scores remain byte-identical.

## DEFINITION OF DONE

- [ ] Target journeys J-01, J-03, J-05 verified via `browser-qa-agent`, with `reports/phase-goal-mcp-loop-iter-1-ui-test-results.md` and screenshots actually produced (the iter-0 gap — no results file, empty evidence dir, no browser-qa telemetry — MUST NOT recur).
- [ ] Against the empty/absent ledger, every score on `/stocks` and stock-detail renders a visible "Not yet proven" status; NO score is shown without a status; nothing reads "Proven".
- [ ] The Evidence page is reachable from the persistent nav in ≤2 clicks and renders the ledger (honest empty state today).
- [ ] No anti-goal violation introduced (especially: nothing presented as proven without a PASS certified-claim; the three served scores stay byte-identical — no recompute in the read path).
- [ ] Unit + API tests pass; `/api/stocks` payload is unchanged (no regression in `stocks_payload`).
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-1-dev.md`.

## TESTING REQUIREMENTS

- **Browser (named journeys this iteration must verify):**
  - **J-01** — visit `/stocks`; assert every leaderboard row's score area shows an evidence badge ("Proven" or "Not yet proven"); assert at least one badge is present and no displayed score lacks a status.
  - **J-03** — assert the badges read "Not yet proven" (never a confident "Proven" number) against the empty ledger, on both `/stocks` and a stock-detail page.
  - **J-05** — click "Evidence" in the nav (≤2 clicks); assert the ledger page renders; assert the honest empty state shows when there are zero claims, and the claim-row layout (hypothesis, out-of-sample verdict, control comparison, registration date, forward-walk score-to-date) plus claim→surface linkback are present in the markup.
- **Unit/integration:**
  - `app/engine/evidence.py`: (a) absent ledger ⇒ `{claims: [], proven_signals: {}}`; (b) a synthetic `verdict.status == "PASS"` entry naming a signal ⇒ that signal appears in `proven_signals`; (c) a `FAIL` / `INSUFFICIENT` entry ⇒ the signal is NOT in `proven_signals` (stays "Not yet proven"); (d) `resolve_ledger_path()` honors the `TRENDORA_LEDGER_PATH` env override and otherwise the config `evidence.ledger_path` default.
  - `GET /api/evidence`: empty ledger ⇒ 200 with empty `claims` + `proven_signals`; a seeded ledger fixture ⇒ the PASS claim appears in both `claims` and `proven_signals`.
  - Frontend: `EvidenceStatusBadge` renders "Not yet proven" when the signal is absent from the proven map and "Proven" (with the `/evidence` link) when present.
  - Regression: `stocks_payload` / `GET /api/stocks` serves byte-identical scores (the badge attaches additively; no recompute).
- **Error cases:**
  - An absent ledger file ⇒ `GET /api/evidence` returns 200 with an empty payload (never 500).
  - A ledger entry with a missing or non-PASS verdict ⇒ never surfaced as "Proven" (fail-safe).
  - A frontend evidence-fetch failure ⇒ badges fall back to "Not yet proven" and the leaderboard is unaffected.

## NOTES

- **Full depth is mandated by the iter-0 ESCALATE.** The full 11-step pipeline guarantees the `browser-qa-agent` lane runs; the goal-evaluator MUST confirm a `browser-qa-agent` telemetry record + a non-empty evidence dir before scoring any journey (iter-0 lesson — a missing `ui-test-results` file must drive escalation, not a guessed verdict).
- **No Evidence-Claim block on purpose.** Per `docs/goal.md` loop mechanics, only an iteration that surfaces a signal AS "Proven" needs a machine-readable evidence-claim for the referee. Iter-1 surfaces nothing as proven (empty ledger ⇒ all "Not yet proven"), so it is pure read-side / navigation work and passes the post-decompose gate automatically. J-02 and J-04 are the iterations that will carry a referee-certifiable claim.
- **Single source of truth (goal.md Constraints + anti-goal).** The evidence ledger is the ONLY source of proven-ness. `GET /api/evidence` re-displays verdict fields verbatim and the UI never computes proven-ness; the resolver reads the SAME file the post-decompose gate writes, so displayed evidence is consistent with what the referee certified.
- **J-05 boundary.** Against the empty ledger the page renders an honest empty state; the claim→surface linkback is built and unit-tested but cannot be exercised end-to-end until ≥1 claim is certified. The evaluator may record the claim-linkback sub-step as pending that certified iteration while still crediting the ledger surface (page + nav + empty state) this iteration.
- **Do not edit `scripts/` (a symlink to the shared framework).** The config-default `evidence.ledger_path` already points at the gate's ledger file, so the backend reads the right ledger with no framework-script change; `TRENDORA_LEDGER_PATH` remains available as a forward-looking override.
