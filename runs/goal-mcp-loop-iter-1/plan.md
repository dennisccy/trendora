# goal-mcp-loop-iter-1 Execution Plan

Read-side evidence path: a `GET /api/evidence` over the certified-claims ledger, an inline
"Proven / Not yet proven" status badge on every score, and a nav-reachable `/evidence` ledger page.
Against today's EMPTY ledger every signal must honestly read **"Not yet proven"**. Structurally
satisfies J-01 (every score shows a status), J-03 (unvalidated signals flagged, never confident),
and the J-05 ledger surface. J-02 / J-04 are correctly deferred (they need a referee-certified claim).

## What to Build

- **Read-side evidence resolver** `app.engine.evidence` (recomputes NOTHING): `resolve_ledger_path()`
  (env `TRENDORA_LEDGER_PATH` → else config `evidence.ledger_path` resolved against `REPO_ROOT`) and
  `build_evidence_payload(ledger_path)` → `{claims:[...], proven_signals:{...}}`, reading ONLY via
  `app.engine.ledger.read_entries`. A signal is **Proven** iff a ledger entry with `verdict.status == "PASS"`
  names it; everything else is "Not yet proven" (fail-safe). Missing/empty ledger ⇒ `{claims:[], proven_signals:{}}`.
- **Typed config** `evidence.ledger_path` (default `runs/goal-session-mcp-loop/state/certified-claims.jsonl`)
  in `config.py` + `config.yaml` — the SAME file the post-decompose gate writes. No path literal in code.
- **Endpoint** `GET /api/evidence` → `build_evidence_payload(resolve_ledger_path())`. READ-ONLY (never writes
  the ledger, never computes proven-ness). Registered in `main.py` under the `/api` prefix.
- **`EvidenceStatusBadge`** chip — given a `signal` key + the served `proven_signals` map, renders "Proven"
  (linking to `/evidence`) when present, else muted "Not yet proven" (fail-safe default).
- **Badges inline** on `/stocks` leaderboard rows (each of Leadership / Entry Quality / Risk) and beside each
  score on `/stocks/{ticker}`. Evidence fetched once, non-blocking; a fetch failure renders "Not yet proven"
  and never breaks the leaderboard. Served scores stay **byte-identical** (badge is purely additive).
- **`/evidence` ledger page** + **Evidence nav entry** (after Research, ShieldCheck-style lucide icon). Honest
  empty state today ("No certified claims yet — every signal currently reads Not yet proven"); claim-row layout
  (hypothesis / out-of-sample verdict / control comparison vs SPY / registration date / forward-walk
  score-to-date) and claim→surface linkback built + unit-tested, exercised once a claim is certified.

## Agents Required

- developer: yes -- implements all backend (resolver, config, endpoint, registration, unit/API/regression
  tests) and all frontend (badge, api client + types, `/stocks` + `/stocks/{ticker}` wiring, `/evidence` page,
  sidebar nav, frontend badge test) work. This is a single coherent read-side slice; no separate agents needed.

## Frontend Present

yes

## Files to Create/Modify

Backend — create:
- `apps/backend/app/engine/evidence.py` -- read-side resolver (`resolve_ledger_path`, `build_evidence_payload`)
- `apps/backend/app/api/evidence.py` -- `GET /api/evidence` router (read-only)
- `apps/backend/tests/test_evidence.py` -- resolver/payload units: absent ⇒ empty; PASS entry ⇒ proven; FAIL/INSUFFICIENT ⇒ not proven; env override vs config default
- `apps/backend/tests/test_api_evidence.py` -- endpoint: empty ledger ⇒ 200 empty payload (never 500); seeded PASS fixture ⇒ claim in `claims` + `proven_signals`

Backend — modify:
- `apps/backend/app/config.py` -- add typed `EvidenceCfg(ledger_path: str)` + `evidence` field on the top-level `Config` (reuse existing `REPO_ROOT`; No-magic-numbers rule)
- `config.yaml` -- add `evidence:` block with `ledger_path: runs/goal-session-mcp-loop/state/certified-claims.jsonl`
- `apps/backend/main.py` -- import `evidence` into the `app.api` tuple + `application.include_router(evidence.router, prefix="/api")`
- existing `/api/stocks` test (e.g. `apps/backend/tests/test_api_stocks*.py`) -- add/extend a regression assertion that `stocks_payload` / `GET /api/stocks` is unchanged (scores byte-identical)

Frontend — create:
- `apps/frontend/components/evidence-status-badge.tsx` -- the calm status chip (palette tokens only; NOT `evidence-panels.tsx`)
- `apps/frontend/app/evidence/page.tsx` -- certified-claims ledger list + honest empty state
- frontend badge test (match the repo's existing test runner/location) -- "Not yet proven" when absent; "Proven" + `/evidence` link when present

Frontend — modify:
- `apps/frontend/lib/api.ts` -- add `fetchEvidence()` + new types `EvidenceLedgerResponse` / `CertifiedClaim` / `ProvenSignal` (do NOT reuse the existing `EvidenceAggregate`, which is the Backtest forward-evidence type)
- `apps/frontend/app/stocks/page.tsx` -- fetch evidence once (non-blocking, keyed like header fetches); render a badge in each score area on every row
- `apps/frontend/app/stocks/[ticker]/page.tsx` -- render the badge beside each score in `ScoreCard`
- `apps/frontend/components/sidebar.tsx` -- add `{ href: "/evidence", label: "Evidence", icon: <ShieldCheck> }` after the Research entry

## UI Evolution

- New user-facing capability: every score on `/stocks` and stock-detail now carries a visible, honest
  evidence status; a new Evidence ledger page is reachable from the persistent nav in ≤2 clicks.
- New information displayed: the "Proven / Not yet proven" status chip on each score; the Evidence ledger
  page (honest empty state today, with the claim-row layout ready for the first certified claim).
- New user actions: click "Evidence" in the nav to open the ledger; click a "Proven" badge to jump to its
  backing ledger entry (once a claim exists); claim rows link back to the surfaces they back.
- UI surface changes: `/stocks` rows and stock-detail score areas gain an inline status chip; new `/evidence`
  page; new Evidence nav entry.
- Navigation changes: ONE new sidebar entry — "Evidence" `/evidence`, inserted after Research (this implements
  the already-approved blueprint IA's `Evidence [NEW]` section; conformance, not a nav-skeleton change).

## Visual Requirements

- Component patterns: reuse the local `components/ui/Badge` for the chip and `Card` for the `/evidence` claim
  rows. Evidence icon = a ShieldCheck-style lucide icon (matches `sidebar.tsx`'s `LucideIcon` pattern).
  `/evidence` follows the existing page-header (title + subtitle) layout used by `/stocks/{ticker}`.
- Layout: unchanged shell (left sidebar + main content). `/evidence` = a vertical list of Card claim rows with
  an honest empty state; badges sit inline beside the existing `ScoreBadge` (do not displace it).
- Key visual effects: calm, muted, evidence-first per goal.md Design Direction — "Not yet proven" uses a muted
  token (`text-muted`/`border`), "Proven" a quiet calm accent (`accent`) with a link. Palette tokens ONLY; no
  invented hex, no hype green/glow (goal.md: "calm and unmissable, never hype").
- States to handle: loading (badges default to "Not yet proven" while evidence loads — never block the
  leaderboard); empty (every badge "Not yet proven"; `/evidence` shows the honest no-claims empty state);
  error (evidence-fetch failure ⇒ badges fall back to "Not yet proven", leaderboard unaffected — never 500/crash).

## Key Test Scenarios

- **J-01 (browser):** `/stocks` — every leaderboard row's score area shows an evidence badge; at least one badge
  present; no displayed score lacks a status.
- **J-03 (browser):** badges read "Not yet proven" (never "Proven") against the empty ledger, on both `/stocks`
  and a stock-detail page.
- **J-05 (browser):** click "Evidence" in the nav (≤2 clicks); the ledger page renders the honest empty state;
  the claim-row layout (hypothesis / out-of-sample verdict / control vs SPY / registration date / forward-walk
  score-to-date) + claim→surface linkback are present in the markup.
- **Backend units:** absent ledger ⇒ `{claims:[], proven_signals:{}}`; synthetic `verdict.status=="PASS"` entry
  naming a signal ⇒ that signal in `proven_signals`; FAIL/INSUFFICIENT ⇒ NOT in `proven_signals`;
  `resolve_ledger_path()` honors `TRENDORA_LEDGER_PATH` then the config default.
- **API:** empty ledger ⇒ 200 with empty `claims`+`proven_signals` (never 500); seeded PASS fixture ⇒ claim in both.
- **Regression:** `GET /api/stocks` payload unchanged (scores byte-identical — no recompute in the read path).
- **Frontend:** `EvidenceStatusBadge` renders "Not yet proven" when the signal is absent and "Proven" (with the
  `/evidence` link) when present.
- **Evidence gate:** verify this iteration carries NO `## Evidence Claim` block (nothing surfaced as "Proven"),
  so the post-decompose gate passes automatically.
- **Anti-iter-0:** confirm the `browser-qa-agent` actually runs and produces
  `reports/phase-goal-mcp-loop-iter-1-ui-test-results.md` + screenshots (a non-empty evidence dir). A missing
  results file MUST drive escalation, not a guessed verdict.

## Assumptions & Risks (flagged)

- **Ledger entry schema vs. `claim.signal` keying (read defensively).** The real ledger writer
  `app.mcp.tools.verify_edge` appends `{claim, register_date, horizon, cohort_n, control_n, verdict}`, where
  `claim` is the cohort-selector dict (kind/factor/decile/horizon/…) and carries **no `signal` key**. The spec's
  `proven_signals[entry["claim"]["signal"]]` mapping is therefore a read-side convention iter-1 *establishes*;
  it is never exercised against real data this iteration (the ledger is EMPTY) and is covered only by synthetic
  fixtures that include a `signal`. Requirement: the resolver MUST read `entry["claim"].get("signal")`
  defensively so a real signal-less PASS entry never KeyErrors and stays "Not yet proven" (preserves the
  fail-safe anti-goal). Wiring the WRITER to stamp `claim.signal` (so a future certified edge actually maps to a
  UI signal key) is **deferred to the certified J-02/J-04 iteration** per the spec OUT OF SCOPE — the developer
  must note this writer-side gap in the handoff.
- **Read-only dependencies.** `app.engine.referee`, `app.engine.ledger` (append/read), `app.mcp.tools`, and
  `project-extensions/gates/` are consumed READ-ONLY — do not modify. Do not edit `scripts/` (a symlink to the
  shared framework); the config-default path makes `start-backend.sh` need no change.
- **Goal alignment: PASS.** The spec advances J-01/J-03/J-05, keeps the evidence ledger the single source of
  proven-ness, respects every critical anti-goal (no recompute, nothing "Proven" without a PASS entry, no
  return/price/order claims, determinism/no-lookahead untouched, no hardcoded secrets), and is purely additive.
  No drift detected.
- **Out of scope (excluded):** badges on `/sectors` / `/themes` / research labs; any J-02 proof drill panel or
  J-04 regime-conditioned evidence; any Evidence-Claim proposal / referee certification this iteration;
  modifying the referee, ledger writer, MCP window, the post-decompose gate, or framework scripts.
