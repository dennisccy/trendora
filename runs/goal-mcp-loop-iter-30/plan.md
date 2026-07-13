# goal-mcp-loop-iter-30 Execution Plan

## Alignment Check

Target journey **J-18** (`docs/goal.md`) — the pre-registration registry + gate cross-check, backlog
card **B-901**. This directly builds Key Capability 5 ("Self-improving evidence loop") and is the
**governance keystone** nine forthcoming journeys (J-19 graveyard, J-22 referee-audit, every future
Evidence Claim) depend on — no drift from the project goal. It carries **no `## Evidence Claim`**
(confirmed absent from `docs/phases/goal-mcp-loop-iter-30.md`) — pure governance/UX, so the
post-decompose gate passes this iteration's own dispatch through automatically.

The session's `blueprint.md` (Data Contract, line ~110) **already pre-registers the exact contract**
this plan must not deviate from — treat it as binding, not just descriptive:
- **Canonical value:** the pre-registration registry.
- **Computing module:** `app.engine.registry:load_registrations` — the SINGLE append-only read of
  `runs/goal-session-mcp-loop/state/pre-registrations.jsonl` (config `evidence.registry.path`; env
  `TRENDORA_REGISTRY_PATH` override — no second parse path; missing file ⇒ honest empty).
- **Serving endpoint:** `GET /api/research/registry` — the ONE endpoint the page reads; the SAME
  loader is imported directly (non-HTTP) by the gate `verify_claim.py`, and later by B-902's
  graveyard. No second computation, no second endpoint.
- The `blueprint.reapproval-requested` marker file already exists (written by the decomposer) —
  **do not recreate it**; `run-goal.sh` auto-approves it.

**Do NOT touch** (explicit in the spec and `docs/goal.md`'s anti-goals): `app.mcp.tools:verify_edge`,
`app.engine.referee`, `app.engine.ledger`, and both `certified-claims.jsonl` / `staging-ledger.jsonl`
stay byte-identical (divisor stays 8, all-FAIL). Required-still-passing journeys J-01/02/03/05/06/07/
08/09/11 must replay green — they read `GET /api/evidence`, which this iteration never touches.

## What to Build

- New append-only state file `runs/goal-session-mcp-loop/state/pre-registrations.jsonl` (one JSON
  object per line): every hypothesis ever registered/tested, backfilled from history.
- New pure loader module `app.engine.registry`: `resolve_registry_path()` (mirrors
  `app.engine.evidence.resolve_ledger_path()` exactly — env override, else config, resolved against
  `REPO_ROOT`), `load_registrations()`, and `match_registration(claim) -> dict | None` by **EXACT**
  selector-set equality (no fuzzy/superset matching). Missing/empty file ⇒ `[]`, never a crash.
- New read-only endpoint `GET /api/research/registry` serving the loader output verbatim.
- **Gate teeth:** `project-extensions/gates/verify_claim.py` cross-checks every claim against the
  registry (via the same `match_registration`) BEFORE `tools.verify_edge` runs, when
  `evidence.registry.enforce` is `true`. No match ⇒ block (exit 3) before any referee computation —
  no `verify_edge` call, no ledger write. Enforcement OFF ⇒ byte-identical current behavior.
- Config: `evidence.registry.path` + `evidence.registry.enforce` (flip `true` only after the backfill
  is verified complete — sequencing matters, see Critical Implementation Detail). `run-goal.sh` exports
  `TRENDORA_REGISTRY_PATH` alongside `LEDGER_PATH`/`STAGING_LEDGER_PATH` at both dispatch sites.
- New page `/research/registry`: a read-only table of every registration (selectors, rationale,
  registration date, source, status), historical backfills visibly labeled. Discoverable from
  `/research` in ≤2 clicks.
- Backend fixture tests proving: registered-exact-match → proceeds; unregistered → refused before
  `verify_edge`; near-miss (one differing selector) → refused (exact match, not fuzzy); loader ==
  endpoint (single source); missing-file → empty, no crash; enforcement-off → unchanged behavior.
- Dev handoff at `docs/handoffs/goal-mcp-loop-iter-30-dev.md`.

## Assumptions (batched — proceeding, not blocking)

1. **Backfill row count resolves to the exact-match-consistent number, not the spec's literal "≥14."**
   I enumerated both ledgers: `certified-claims.jsonl` (7 rows) + `staging-ledger.jsonl` (7 rows) = 14
   raw entries, but **3 pairs are EXACT selector-set duplicates across the two files** (a staging
   candidate later promoted/re-tested under `"ledger":"canonical"` with the identical cohort
   selectors: `vcp_contraction` decile-10 h60; `rs_spy_3m` decile-10 h60; the
   `rs_spy_3m:top:quintile`+`high_proximity:top:tertile` h20 combination). Since `match_registration`
   must return "the matching row" (**singular**) for an exact selector-set, the registry **cannot**
   hold two rows sharing an identical selector tuple — deduplication by exact selector-set is a
   functional requirement, not optional polish. Result: **11 distinct hypotheses** from the two
   ledgers. Separately, ALL 7 `proposer-guidance.md` §4.1 (4) + §4.2 (3) candidates already coincide
   1:1 with 7 of those 11 ledger rows (none are net-new) — the remaining 4 (`leadership_score` d10 h20,
   the `Breakout-watch`/Risk-on event-study, `ma_stack` d10 h20, `vcp_contraction` d10 h20) are original
   canonical claims that predate the §4.1/§4.2 guidance tables. **Net: 11 backfilled registry rows
   total.** Treat the spec's "≥14" as an approximation the decomposer wrote without deriving the
   cross-ledger overlap — completeness + exact-match correctness (the DoD's own "single-source
   assertion" and "near-miss refused" fixtures) are the real bar, not a literal row count. Record the
   actual count + this reasoning in the dev handoff so review isn't surprised by 11 vs "≥14."
2. **`registered_date` for every backfilled row = the ledger's own `register_date` field
   (`"2026-07-03"`, the sanctioned re-referee date)** — never today's date. Stamping a fresh date on a
   historical backfill would look exactly like the "retroactive registration to launder a mined result"
   trap B-901 explicitly warns about, even though this is an honest backfill; citing the real recorded
   date sidesteps that appearance entirely.
3. **Status vocabulary:** all 11 backfilled rows get `status: "tested"` (each has a recorded FAIL
   verdict) EXCEPT `ma_stack`, which the spec explicitly singles out as `status: "closed"` (permanent —
   matches J-19's forward acceptance text "the ma_stack closed FAIL"). `registered_by: "backfill"` on
   all 11. `source` cites concrete provenance, combining when a row has both a guidance-table origin and
   a ledger origin (e.g. `"proposer-guidance §4.1 #2; certified-claims.jsonl"`).
4. **Endpoint file:** create a small dedicated `app/api/registry.py` (mirrors `app/api/evidence.py`'s
   minimal one-endpoint pattern) rather than appending to `research.py` — this is a governance/process
   surface, architecturally distinct from the ten analytical labs, and three more governance endpoints
   (J-17/J-19/J-22) are coming. Either placement satisfies the spec; this is the recommended default.
5. **Hub discoverability:** add a separate "Governance & process" group directly in
   `app/research/page.tsx`, not an 11th entry in `lib/research-labs.ts`'s `RESEARCH_LABS` array — that
   array's own header comment declares it holds "the ten labs" in a fixed reading order (J-113
   contract); mixing a non-lab governance link into it would blur that contract. This also establishes
   the pattern the 3 forthcoming governance pages (budget/graveyard/referee-audit) will reuse.
6. **Combination `condition` list order is part of the exact match** (`["A","B"]` ≠ `["B","A"]` under
   strict equality) — this is a known, accepted sharp edge, not a bug to normalize away: any
   normalization is itself a step toward "fuzzy matching," the card's named dominant trap. Future
   combination registrations should just reuse the leg order already established in
   `proposer-guidance.md` / `config.triad.combination_candidates`.

## Out of Scope

- J-17 (budget panel), J-19 (graveyard), J-22 (referee-audit), J-20/J-21 (daily-ops), J-23/J-24/J-25
  (risk analytics) — per spec, one risky journey per iteration.
- Any change to `app.mcp.tools:verify_edge`, `app.engine.referee`, `app.engine.ledger`, either ledger
  file, or the canonical Bonferroni divisor.
- Fuzzy/partial selector matching of any kind; UI edit/delete of registry rows; retroactive
  registration of an un-pre-registered result; re-submission of the closed `ma_stack` FAIL.
- Any new proven/confidence language, badge, or number-as-edge anywhere on the new page.
- A workflow engine, approval flow, or mutation UI — a registry + loader + gate check + a read-only
  page, nothing more (B-901's own named dominant failure mode is scope-creep).
- A `## Evidence Claim` — this iteration certifies nothing.

## Agents Required

- backend-data: yes — `app.engine.registry` loader module, the backfilled
  `pre-registrations.jsonl`, `GET /api/research/registry`, the `verify_claim.py` gate cross-check,
  `EvidenceCfg`/`config.yaml` additions, the `run-goal.sh` env export at both dispatch sites, and the
  full fixture test suite (loader, endpoint, gate registered/unregistered/near-miss/enforcement-off).
  Flip `evidence.registry.enforce: true` in `config.yaml` LAST, only after the backfill is verified
  complete against both ledgers + `proposer-guidance.md` §4.1/§4.2.
- frontend-ux: yes — `/research/registry` page (table: selectors, rationale, registration date,
  source, status; backfills labeled; honest loading/empty/error states; no proven-language, no
  badges-as-edges) + the Research-hub governance entry + `lib/registry.ts` types + `api.ts`
  `fetchRegistry`.

Frontend Present: yes

## Files to Create/Modify

Backend:
- `runs/goal-session-mcp-loop/state/pre-registrations.jsonl` — NEW, 11 backfilled rows (see
  Assumptions #1-3). Reproducible construction (a small one-off script reading both ledgers +
  `proposer-guidance.md` is recommended over hand transcription, to avoid a selector typo that would
  silently break `match_registration`'s exact-equality contract).
- `apps/backend/app/engine/registry.py` — NEW. `resolve_registry_path()` (mirror
  `app/engine/evidence.py:47-60` exactly — env var name pattern `TRENDORA_REGISTRY_PATH`),
  `load_registrations()` (mirror `ledger.read_entries` — missing file ⇒ `[]`), `match_registration
  (claim: dict) -> dict | None` (build the claim's selector-set the same way `_CLAIM_SELECTOR_KEYS`
  does in `app/mcp/tools.py:395-399` — `kind` + the present `_CLAIM_SELECTOR_KEYS` subset + `horizon` +
  `direction` — then exact-equality-compare against each row's stored `selectors`).
- `apps/backend/app/api/registry.py` — NEW. `GET /api/research/registry`, thin, mirrors
  `app/api/evidence.py` (no DB session needed; 200 + empty list on missing file, never 500).
- `apps/backend/main.py` — add the `registry` import (`app/main.py`'s import block at `:18-35`) and
  `application.include_router(registry.router, prefix="/api")` beside the `evidence.router` line (`:132`).
- `apps/backend/app/config.py` — add `RegistryCfg(BaseModel)` (fields: `path: str`, `enforce: bool =
  False` — DEFAULT-OFF in code, mirroring `FdrCfg`'s default-preserving pattern so any fixture
  predating this block still loads unchanged) just above `EvidenceCfg` (~line 2103); add `registry:
  RegistryCfg = Field(default_factory=RegistryCfg)` inside `EvidenceCfg` (~line 2121).
- `config.yaml` — add `evidence.registry.path` and `evidence.registry.enforce` as a sibling block to
  the existing `fdr:` sub-block (after line ~1087, same `evidence:` section), documented at the same
  density as the surrounding comments. Set `enforce: true` only as the LAST step, after backfill
  verification.
- `project-extensions/gates/verify_claim.py` — insert a registry cross-check in `main()`'s per-claim
  loop (`:110-129`), before the `tools.verify_edge(...)` call, gated on `get_config().evidence.registry
  .enforce`. No match ⇒ append a result shaped exactly like the existing `route_error` block (`:113-119`
  — `{"claim":..., "ledger":..., "status":"BLOCKED", "reason": <names the registry requirement>}`), set
  `blocked = True`, and `continue` (skip `verify_edge` for that claim). A match, or enforcement off ⇒
  fall through unchanged. Needs a new `from app.config import get_config` and `from app.engine import
  registry as registry_mod` import (the existing `sys.path.insert` at `:35` already makes `app.*`
  importable, exactly as `from app.mcp import tools` already does).
- `scripts/automation/run-goal.sh` — add `TRENDORA_REGISTRY_PATH="$GOAL_SESSION_DIR_LOCAL/state/
  pre-registrations.jsonl"` beside `LEDGER_PATH`/`STAGING_LEDGER_PATH` at BOTH dispatch sites
  (`:1637-1638` and `:2141-2142`).

Backend tests:
- `apps/backend/tests/test_registry.py` — NEW. Loader unit tests: exact match returns the row; a
  near-miss (one differing selector, e.g. `vcp_contraction` decile 10→9, or horizon 20→21) returns
  `None`; missing file ⇒ `[]` no crash; `resolve_registry_path` honors the env override.
- `apps/backend/tests/test_api_registry.py` — NEW. `GET /api/research/registry` — 200 empty on missing
  file; serves backfilled rows verbatim; response equals `load_registrations()` output directly
  (single-source assertion).
- `apps/backend/tests/test_gate_registry_enforcement.py` — NEW (or extend
  `test_staging_ledger_routing.py` if preferred — same file already tests gate routing). Import
  `verify_claim.py` via `importlib.util.spec_from_file_location` exactly as
  `test_staging_ledger_routing.py:194-196` already does. Cases: (a) registered exact-match claim with
  `enforce=true` → `tools.verify_edge` IS called (monkeypatch/spy); (b) unregistered claim → refused,
  `verify_edge` NOT called, target ledger file unchanged, `BLOCKED` result names the registry
  requirement; (c) near-miss claim (one selector differs from a real registry row) → refused, same
  assertions as (b); (d) `enforce=false` → an unregistered claim still proceeds to `verify_edge`
  (byte-identical to pre-iter-30 behavior).
- Extend whichever existing test already covers `EvidenceCfg`/`FdrCfg` validation (check
  `test_config.py` / `test_config_engine.py` first) with `RegistryCfg` coverage rather than duplicating.

Frontend:
- `apps/frontend/lib/registry.ts` — NEW. `PreRegistrationRow` + `RegistryResponse` types, mirroring
  `lib/evidence.ts`'s pattern (types-plus-small-helpers module).
- `apps/frontend/lib/api.ts` — add `fetchRegistry(signal?)` calling `GET /api/research/registry`,
  re-exporting the new types (mirror `fetchEvidence` at `:348-349` and the `export type {...}` block).
- `apps/frontend/app/research/registry/page.tsx` — NEW. Table columns: selectors (rendered readably,
  not raw JSON — reuse whatever cohort-label helper `lib/evidence.ts`/`lib/factor-lab-evidence.ts`
  already has for rendering a claim's cohort, if one fits), rationale, registration date, source,
  status (backfills visibly labeled, e.g. "backfill" pill). Loading skeleton / fetch-error card / empty
  state, mirroring `app/evidence/page.tsx`'s three-state pattern (`:36-103`). Read-only — no
  edit/delete affordance anywhere.
- `apps/frontend/app/research/page.tsx` — add a "Governance & process" section below the existing
  `RESEARCH_LABS` grid, linking to `/research/registry` (through `useAsOfHref`, consistent with every
  other hub link).

## UI Evolution

- New user-facing capability: browse the complete pre-registration registry at `/research/registry` —
  every hypothesis the system has ever registered/tested, with its economic rationale and audit-trail
  date.
- New information displayed: per-hypothesis selectors, rationale, registration date, source, status
  (backfills labeled as such). No numeric edge, no proven/confidence language.
- New user actions: navigate to `/research/registry` via the Research hub and read/scan the table. No
  forms, no mutations — registrations are appended by the gate/tooling only.
- UI surface changes: one new read-only page under the existing Research section + one new
  "Governance & process" group on the `/research` hub. No sidebar/nav-skeleton change.
- Navigation changes: none to the persistent nav; the hub gains one new discoverable card/link.

## Visual Requirements

- Component patterns: `Card`/`CardContent` wrapping a plain `<table>` (precedent:
  `app/research/samples/page.tsx`'s table markup), `PageHeading` for the title/subtitle, `Badge` ONLY
  for the status column in a **neutral/muted** variant — explicitly NOT the accent/danger coloring
  `EvidencePage` uses for PASS/FAIL, since "registered/tested/closed" is descriptive process state, not
  a proven/not-proven signal (conflating the two would violate anti-goal #1's spirit even though it's
  technically a different field).
- Layout: single-column page under the existing app shell (sidebar + main content), same width/spacing
  as other Research sub-pages; a "Back to Research" link matching `samples/page.tsx`'s pattern.
- Key visual effects: none beyond the existing card/border/hover treatment already used across Research
  sub-pages — this is a dense, calm, data-first table, not a marketing surface.
- States to handle: loading skeleton, fetch-error (backend unreachable) card, and an honest empty state
  (registry file absent/empty — should not occur post-backfill, but the endpoint/page must degrade
  gracefully, never crash, per the anti-goal on data-shape resilience).

## Critical Implementation Detail

- **Insertion point discipline in `verify_claim.py`:** the registry check must be a pure pre-check that
  either lets the existing `tools.verify_edge(...)` call proceed completely unchanged, or short-circuits
  before it runs at all. Do not thread any new parameter into `verify_edge`, `certify_edge`, or the
  ledger modules — the "Do NOT touch" boundary is absolute here.
- **`enforce` sequencing is the actual safety mechanism**, not a formality: land the loader + backfill +
  gate code with `config.yaml`'s `evidence.registry.enforce` still `false`, verify the backfill
  (loader row count, each row's selector-set round-trips through `match_registration` against its own
  ledger claim), THEN flip to `true` in the same dev pass. If backfill verification surfaces a gap,
  fix the backfill before flipping — never flip first and patch later.
- **This iteration's own gate run is unaffected either way** — iter-30 carries no `## Evidence Claim`,
  so `verify_claim.py` exits 0 (no-claim passthrough) regardless of the `enforce` value, exactly as
  today.

## Key Test Scenarios

- J-18 step 1 (browser-qa): `/research/registry` renders selectors + rationale + registration date +
  source + status for every backfilled row, backfills visibly labeled; reachable from `/research` in
  ≤2 clicks; honest empty/error states if the backend is unreachable; no proven-language anywhere on
  the page.
- J-18 steps 2 & 3 are gate mechanics, NOT browser-testable (the gate is a CLI script) — fixture-proven
  only: a registered exact-match claim reaches `verify_edge`; an unregistered claim is refused before
  any referee computation with a message naming the registry requirement.
- Near-miss exact-match proof: a claim differing from a real registry row by exactly one selector value
  is refused (proves matching is exact, never fuzzy).
- Single-source proof: `GET /api/research/registry`'s response equals `load_registrations()` called
  directly against the same file.
- Missing/empty registry file: loader returns `[]`, endpoint returns 200 with an empty list, page shows
  an honest empty state — none crash.
- Enforcement-off proof: with `evidence.registry.enforce=false`, an unregistered claim still reaches
  `verify_edge` (byte-identical to pre-iter-30 behavior) — this is the regression guard for every
  *future* iteration that predates its own registry row being backfilled correctly.
- Regression (replay, no browser re-verification needed beyond the standard required-still-passing
  sweep): `GET /api/evidence` and both ledger files are byte-identical before/after; J-01/02/03/05/06/
  07/08/09/11 replay green.
- Before dispatching browser-qa: bring up BOTH prod-mode services fresh (`rm -rf apps/frontend/.next`
  first, per the iter-13/20/22 lesson already carried in the phase spec's Notes) so the registry page
  is actually served, not a stale cached build.
