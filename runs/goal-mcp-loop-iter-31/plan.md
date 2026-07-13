# goal-mcp-loop-iter-31 Execution Plan

## Alignment Check

Target journey **J-19** (`docs/goal.md`) — the negative-results graveyard, backlog card **B-902**.
This builds Key Capability 5 ("Self-improving evidence loop") and directly extends the governance
cluster J-18 (iter-30, the pre-registration registry) started: it reads J-18's `registry.match_
registration` verbatim to attach lineage, and consolidates "what is proven" (`/evidence`), "what is
registered" (`/research/registry`), and now "what does NOT work" (`/research/graveyard`) — no drift
from the project goal. It carries **no `## Evidence Claim`** (confirmed absent from `docs/phases/
goal-mcp-loop-iter-31.md`) — pure read-compose/UX, so the post-decompose gate passes this iteration's
own dispatch through automatically.

**Do NOT touch** (explicit in the spec's OUT OF SCOPE and `docs/goal.md`'s anti-goals): `app.mcp.
tools:verify_edge`, `app.engine.referee`, `app.engine.evidence` (import from it read-only, never edit
it), `app.engine.ledger`'s write path, `project-extensions/gates/verify_claim.py` (J-19, unlike J-18,
never touches the gate — READ-ONLY composition), and all three state files (`certified-claims.jsonl`,
`staging-ledger.jsonl`, `pre-registrations.jsonl`) stay byte-identical. The canonical Bonferroni
divisor stays 8. Required-still-passing journeys **J-01, J-03, J-04, J-05, J-06, J-08, J-09, J-11,
J-18** must replay green — none of them read anything this iteration adds.

One deliberate contract note (already logged in the spec + `docs/goal.md`'s Loop-mechanics section):
this iteration **narrows** the iter-9/10/12 "staging ledger is internal-only, never served" invariant
— the staging ledger's NON-PASS verdicts become browsable (the graveyard's whole purpose). The
honesty fence stays intact: staging carries 0 PASS rows, and `/evidence` / `proven_signals` / the
"Proven" badge stay byte-identical and untouched by this change.

## What to Build

- New PURE read-compose module `app.engine.graveyard`: `build_graveyard_payload()` reads BOTH ledgers
  (canonical via the existing `app.engine.evidence.resolve_ledger_path()`; staging via a new local
  resolver honoring the `STAGING_LEDGER_PATH` env the harness already exports, else `config.evidence.
  staging_ledger_path`), excludes forward-walk records, filters to non-PASS (`FAIL`/`INSUFFICIENT`),
  tags each entry with its origin ledger, re-displays `verdict.deflation`/`deflation_divisor` verbatim,
  and attaches lineage via `app.engine.registry.match_registration` (reused, never reimplemented).
  Missing/empty ledger(s) ⇒ empty graveyard, never a crash.
- A module-level `REVISIT_PROTOCOL` constant (the B-406/§0 rule text) served alongside the entries —
  single source, no proven-language.
- New endpoint `GET /api/research/graveyard` (new `app/api/graveyard.py`) serving the composition
  verbatim: `{"entries": [...], "revisit_protocol": {...}}`. 200-with-empty on a missing ledger, never
  500.
- New page `/research/graveyard` mirroring `/research/registry`'s shell: a table of Selectors /
  Verdict (FAIL/INSUFFICIENT, neutral-negative styling) / Date / Deflation / Ledger (canonical/
  staging) / Lineage, a "permanent" marker on closed rows (e.g. `ma_stack`), and a Revisit-protocol
  panel each row links/anchors to.
- `lib/graveyard.ts` types + `fetchGraveyard` in `lib/api.ts`.
- A second card in the EXISTING `/research` "Governance & process" grid (iter-30 already reserved this
  slot in a comment), `data-testid="research-governance-link-graveyard"`.
- Backend fixture tests: non-PASS filter, lineage attachment (matched + honest-null), forward-walk
  exclusion, ledger-origin + deflation tags verbatim, "permanent" from a closed registry row,
  missing/empty ledger ⇒ empty (no crash), endpoint verbatim + 200-on-empty.
- Dev handoff at `docs/handoffs/goal-mcp-loop-iter-31-dev.md`.

## Assumptions (batched — proceeding, not blocking)

1. **Staging-ledger path resolver lives INSIDE the new `app.engine.graveyard` module, not in `app.
   engine.evidence`.** The spec says "mirror the canonical resolver" but `evidence.py` is explicitly
   protected ("NO change to ... any existing computing module" is a literal OUT OF SCOPE line). A new
   local function (env `STAGING_LEDGER_PATH` override — the SAME literal name `run-goal.sh` already
   exports and `verify_claim.py` already reads, deliberately NOT a new `TRENDORA_STAGING_LEDGER_PATH`
   name, since the harness never sets one — else `config.evidence.staging_ledger_path` resolved
   against `REPO_ROOT`) keeps `evidence.py` untouched while satisfying "config-resolved... honor the
   env... no new path literal." `app.engine.graveyard` imports `resolve_ledger_path` from `evidence.py`
   read-only for the canonical side (importing is not "changing" the module).
2. **Endpoint file:** a new dedicated `app/api/graveyard.py` (mirrors `app/api/registry.py`'s minimal
   one-endpoint pattern), not appended to `research.py` — consistent with the iter-30 precedent
   (Assumption #4 there) and the two more governance endpoints (J-17, J-22) still to come.
3. **"Permanent" marking is derived client-side from `lineage.status === "closed"`** (mirrors how the
   registry page already derives its own "backfill" pill from `registered_by === "backfill"`) rather
   than adding a new backend boolean field — the matched registry row's `status` is already re-served
   verbatim, so no new computed semantic is needed on the backend.
4. **Registry-row deep link:** "a row's lineage link resolves to its registry row" (Testing
   Requirements) needs an actual anchor, and `/research/registry`'s `<tr>` currently carries no `id`
   (only a React `key`). Adding `id={`registration-${row.id}`}` + `scroll-mt-20` to that `<tr>`
   (mirrors `/evidence`'s `ClaimRow` `id={anchorId}` pattern exactly) is a small, additive,
   presentation-only change — not a change to a computing module or serving endpoint, so it does not
   violate the "no change to any existing... serving endpoint" boundary. The graveyard's Lineage link
   then points at `/research/registry#registration-<id>`; an honest-null lineage row renders plain text
   (no link).
5. **Verdict badge variant:** reuse the existing `Badge` `danger` variant for FAIL and `warn` for
   INSUFFICIENT (mirrors `/evidence`'s own `verdictVariant` mapping for these two statuses exactly) —
   NEVER `accent`, which `/evidence` reserves exclusively for PASS/"Proven". Since the graveyard shows
   only non-PASS rows this never collides in practice, but it is the explicit guardrail the spec names.
6. **Drift-insurance equality test** (`app.engine.registry._CLAIM_SELECTOR_KEYS == app.mcp.tools.
   _CLAIM_SELECTOR_KEYS`) is added to `test_registry.py` (extend) — the natural home, since it pins a
   constant `app.engine.registry` owns, not something graveyard-specific.
7. **No `config.py` / `config.yaml` changes at all.** `evidence.staging_ledger_path` already exists
   (iter-9); the registry loader already exists (iter-30). This iteration is pure composition + one new
   local resolver + one new endpoint + one new page — no new config surface.

## Out of Scope

- J-17 (budget panel), J-20–J-25 — deferred (one risky new surface per iteration; rubric rule 5).
- Any change to `app.mcp.tools:verify_edge`, `app.engine.referee`, `app.engine.evidence`, `app.engine.
  ledger`'s write path, or `project-extensions/gates/verify_claim.py` — J-19, unlike J-18, is
  READ-ONLY and never touches the gate.
- `## Evidence Claim` / any referee submission / any ledger write — `certified-claims.jsonl`,
  `staging-ledger.jsonl`, `pre-registrations.jsonl` stay byte-identical.
- Any deletion or edit affordance for a graveyard entry (append-only; no such UI anywhere).
- Reviving / re-testing / re-submitting the closed `ma_stack` FAIL or any other closed hypothesis.
- Any new canonical value, new top-level nav section, or change to an existing computing module or
  serving endpoint (the one narrow, presentation-only exception is Assumption #4's row-anchor `id`).

## Agents Required

- backend-data: yes — `app.engine.graveyard` (composition module + local staging resolver +
  `REVISIT_PROTOCOL` constant), `app/api/graveyard.py`, `main.py` router wiring, and the fixture test
  suite (`test_graveyard.py`, `test_api_graveyard.py`, `test_registry.py` extension).
- frontend-ux: yes — `/research/graveyard` page (table + revisit-protocol panel; honest loading/empty/
  error states; neutral-negative verdict badges, never accent), `lib/graveyard.ts`, `api.ts`
  `fetchGraveyard`, the `/research` governance-grid card, and the `/research/registry` row-anchor
  addition (Assumption #4).

Frontend Present: yes

## Files to Create/Modify

Backend:
- `apps/backend/app/engine/graveyard.py` — NEW. `build_graveyard_payload()`: reads canonical via
  `ledger.read_entries(evidence.resolve_ledger_path())` and staging via `ledger.read_entries(<local
  resolver>)`; excludes `entry.get("type") == FORWARD_WALK_TYPE` (import `FORWARD_WALK_TYPE` from
  `app.engine.ledger`, mirror `build_evidence_payload`'s exact inline check — not the private
  `_is_forward_walk`); filters to `entry["verdict"]["status"] != STATUS_PASS` (import `STATUS_PASS`
  from `app.engine.referee`, mirror `evidence.py`'s import pattern); tags `"ledger": "canonical"|
  "staging"`; attaches `"lineage": registry.match_registration(entry["claim"])` (`None` when
  unmatched); re-displays `verdict` verbatim (including `deflation`/`deflation_divisor`). Also exposes
  `REVISIT_PROTOCOL` (module-level dict/constant, the B-406/§0 rule text).
- `apps/backend/app/api/graveyard.py` — NEW. `GET /api/research/graveyard` → `{"entries": [...],
  "revisit_protocol": {...}}` verbatim (mirror `app/api/registry.py`'s minimal shape; no DB session;
  200 + empty list on missing/empty ledgers, never 500).
- `apps/backend/main.py` — add `graveyard` to the `from app.api import (...)` block (`:18-35`,
  alphabetically between `evidence` and `health`) and `application.include_router(graveyard.router,
  prefix="/api")` beside `registry.router` (`:133-135`), with a one-line iter-31/J-19 comment matching
  the existing comment style.

Backend tests:
- `apps/backend/tests/test_graveyard.py` — NEW. `build_graveyard_payload` over fixture ledgers
  (canonical + staging): non-PASS filter (a PASS fixture entry is excluded); lineage attachment via a
  real `match_registration` call (matched row + honest `None` for an unregistered selector-set);
  forward-walk exclusion; ledger-origin tag + `deflation`/`deflation_divisor` re-displayed verbatim;
  "closed" status surfaced verbatim on a matched row (e.g. a `ma_stack`-shaped fixture); missing/empty
  ledger file(s) ⇒ empty payload, no crash. At least one test round-trips a REAL committed ledger line
  (e.g. `ma_stack` from `certified-claims.jsonl`) end-to-end through the payload (anti-goal #3 proof).
- `apps/backend/tests/test_api_graveyard.py` — NEW (mirror `test_api_registry.py` exactly): 200-empty
  on missing files; serves a fixture entry verbatim; endpoint response equals `build_graveyard_payload
  ()` called directly against the same (real, committed) files — single-source assertion; asserts 14
  entries (7+7) against the real committed ledgers today (status-derived, not hardcoded — the test
  computes the expected count from the raw files, not a literal "14").
- `apps/backend/tests/test_registry.py` — EXTEND with one equality test: `app.engine.registry.
  _CLAIM_SELECTOR_KEYS == app.mcp.tools._CLAIM_SELECTOR_KEYS` (drift insurance for the matcher the
  graveyard leans on — recommended cheap add named in the spec).

Frontend:
- `apps/frontend/lib/graveyard.ts` — NEW. `GraveyardEntry` (ledger, claim, register_date, horizon,
  cohort_n, control_n, verdict, lineage) + `RevisitProtocol` + `GraveyardResponse` types, mirroring
  `lib/registry.ts`'s types-only pattern. No proven-language, no evidence-status resolution.
- `apps/frontend/lib/api.ts` — add `fetchGraveyard(signal?)` calling `GET /api/research/graveyard`,
  re-exporting the new types (mirror `fetchRegistry` at `:361-362`).
- `apps/frontend/app/research/graveyard/page.tsx` — NEW. Table columns: Selectors (key=value chips,
  mirror registry's `SelectorChips`), Verdict (`danger`/`warn` Badge — never `accent`), Date,
  Deflation (`{deflation} ÷{deflation_divisor}` or the raw string, e.g. `lord++`), Ledger
  (canonical/staging pill), Lineage (link to `/research/registry#registration-<id>` when matched,
  honest "No registration lineage" text when not — Assumption #4). A "permanent" marker on rows whose
  `lineage.status === "closed"`. A Revisit-protocol panel (anchored, e.g. `id="revisit-protocol"`)
  rendering `revisit_protocol.rule`; each row links/anchors to it. Loading skeleton / backend-
  unavailable card / honest empty state / `Back to Research` / `PageHeading`, mirroring `/research/
  registry/page.tsx`'s three-state shell exactly.
- `apps/frontend/app/research/page.tsx` — add a second card to the EXISTING `data-testid="research-
  governance"` grid, linking to `/research/graveyard`, `data-testid="research-governance-link-
  graveyard"` (per spec, verbatim).
- `apps/frontend/app/research/registry/page.tsx` — add `id={`registration-${row.id}`}` +
  `scroll-mt-20` to the row `<tr>` (Assumption #4) so a graveyard lineage link can land on the exact
  row. Presentation-only; no data/behavior change.

## UI Evolution

- New user-facing capability: browse every dead hypothesis (all non-PASS referee verdicts across both
  ledgers) at `/research/graveyard`, with selectors, verdict kind, date, deflation context, origin
  ledger, and registration lineage — plus the revisit-protocol rule governing re-tests.
- New information displayed: the staging ledger's non-PASS verdicts become visible for the first time
  (previously internal-only); each entry's lineage (or an honest "unregistered" state); the `ma_stack`
  closed/permanent marking; the revisit-protocol rule text.
- New user actions: navigate Research → Graveyard; click a row's lineage link through to its registry
  row; click/anchor through to the revisit-protocol rule.
- UI surface changes: new `/research/graveyard` page; a second card on the existing `/research`
  Governance & process grid; a new row anchor on `/research/registry` (no visible change there beyond
  making its rows individually linkable).
- Navigation changes: none to the persistent nav — reachable from `/research` in ≤2 clicks, same
  pattern as `/research/registry`.

## Visual Requirements

- Component patterns: `Card`/`CardContent` + a plain `<table>` (precedent: `registry/page.tsx`),
  `PageHeading`, `Badge` — `default`/neutral for the Ledger origin pill and any process-state text,
  `danger`/`warn` for the Verdict column (never `accent`).
- Layout: single-column page under the existing app shell, same width/spacing as other Research
  sub-pages; `Back to Research` link matching `registry/page.tsx`'s pattern; a distinct Revisit-
  protocol panel (a `Card`) below or beside the table.
- Key visual effects: none beyond the existing card/border/hover treatment already used across
  Research sub-pages — dense, calm, data-first, not a marketing surface.
- States to handle: loading skeleton, fetch-error (backend unreachable) card, and an honest empty
  state (both ledgers absent/empty) — mirror `registry/page.tsx`'s three-state pattern exactly; none
  crash.

## Critical Implementation Detail

- **Reuse, never reimplement, matching:** the graveyard's lineage MUST call `app.engine.registry.
  match_registration` directly — a second selector-matching implementation is the exact failure mode
  the spec calls out (registry page, gate, and graveyard could disagree).
- **Forward-walk exclusion and the PASS filter must be status-driven**, not a hardcoded count: today
  all 14 raw entries (7+7) are non-PASS, so the graveyard currently shows all of them, but the filter
  is `verdict.status != PASS`, not "show everything" — a future PASS row must disappear from the
  graveyard automatically.
- **This iteration's own gate run is unaffected:** iter-31 carries no `## Evidence Claim`, so `verify_
  claim.py` exits 0 (no-claim passthrough) regardless — and this iteration never edits that file
  anyway (unlike iter-30).
- **Before dispatching browser-qa:** `rm -rf apps/frontend/.next` and confirm BOTH prod services are
  reachable fresh (iter-13/20/22 lesson, restated in the spec's own Notes) — never accept a stale
  cached build or an empty evidence dir as "ready to ship."

## Key Test Scenarios

- J-19 (browser-qa): `/research/graveyard` renders all 14 non-PASS rows (7 canonical + 7 staging)
  with selectors + verdict kind + date + lineage; the `ma_stack` row shows its "permanent" marking
  in-frame; a row's lineage link resolves to its `/research/registry` row; the revisit-protocol rule
  is visible and row-linked; reachable from `/research` governance grid in ≤2 clicks; honest empty/
  backend-down state (contained card, nav intact). Full-page or element-clip captures, md5-distinct.
- Correctness round-trip (anti-goal #3): at least one graveyard entry's displayed selectors + verdict
  + date byte-match its row read directly from `certified-claims.jsonl` / `staging-ledger.jsonl`.
- Single-source proof: `GET /api/research/graveyard`'s response equals `build_graveyard_payload()`
  called directly against the same real files.
- Honest-null lineage: a ledger entry whose selectors match no registry row renders "no registration
  lineage" — no crash, no fabricated link (exercise via a fixture, since every REAL entry today is
  registered).
- Missing/empty ledger file(s): payload/endpoint/page all degrade to empty, never 500 / never crash.
- A PASS entry (fixture-only, none exist today) is excluded from the graveyard.
- Regression (replay, no browser re-verification beyond the standard required-still-passing sweep):
  `certified-claims.jsonl` + `staging-ledger.jsonl` + `pre-registrations.jsonl` byte-identical before/
  after; `GET /api/evidence` + `proven_signals` unchanged; canonical Bonferroni divisor stays 8;
  J-01/03/04/05/06/08/09/11/18 replay green.
