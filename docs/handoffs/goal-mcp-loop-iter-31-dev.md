# goal-mcp-loop-iter-31 Dev Handoff

**Phase:** goal-mcp-loop-iter-31
**Date:** 2026-07-13
**Agent:** developer
**Status:** complete

## What Was Built

J-19 / backlog B-902 — the negative-results graveyard, the "what does NOT work" companion to `/evidence`
("what is proven") and `/research/registry` ("what is registered"):

- **`app.engine.graveyard`** (new, pure read-compose module, no DB/session): `resolve_staging_ledger_path()`
  (env `STAGING_LEDGER_PATH` override — the SAME literal `run-goal.sh`/`verify_claim.py` already use,
  deliberately not a new `TRENDORA_STAGING_LEDGER_PATH` name — else `config.evidence.staging_ledger_path`,
  mirrors `app.engine.evidence.resolve_ledger_path()` exactly) and `build_graveyard_payload(canonical_path=
  None, staging_path=None)` (defaults resolve via `evidence.resolve_ledger_path()` + the new staging
  resolver — the endpoint's real no-arg call shape; a test may pass explicit fixture paths). It reads BOTH
  ledgers via the existing `app.engine.ledger.read_entries`, excludes forward-walk monitoring records
  (`type == "forward_walk"`, mirrors `build_evidence_payload`'s inline check), filters to NON-PASS
  (`verdict.status != STATUS_PASS`, imported from `app.engine.referee` — status-driven, never a hardcoded
  count), tags each surviving entry `"ledger": "canonical"|"staging"`, re-displays `verdict` verbatim
  (including `deflation`/`deflation_divisor`), and attaches lineage via the EXISTING
  `app.engine.registry.match_registration` (loaded once per request, passed through — never a second
  matcher). Also exposes `REVISIT_PROTOCOL` (a module-level constant: the B-406/§0 re-test rule text, no
  proven-language).
- **`GET /api/research/graveyard`** (new, `app/api/graveyard.py`) — serves `build_graveyard_payload()`
  verbatim as `{"entries": [...], "revisit_protocol": {...}}`. No DB/session; 200 + empty entries on a
  missing/empty ledger (either or both), never 500.
- **`/research/graveyard`** (new page) — a read-only table (Selectors as key=value chips, Verdict as a
  `danger`/`warn` Badge — FAIL/INSUFFICIENT only, NEVER `accent`, mirrors `/evidence`'s own PASS/FAIL/
  INSUFFICIENT mapping for these two statuses — Date, Deflation `"{deflation} ÷{divisor}"`, Ledger
  origin pill, Lineage) reading only `GET /api/research/graveyard`. A "permanent" pill renders on rows
  whose matched registry row has `status === "closed"` (derived client-side, e.g. `ma_stack`). A Revisit-
  protocol panel (`id="revisit-protocol"`) renders `revisit_protocol.rule`; each row carries a "Revisit
  protocol →" anchor link to it. Loading skeleton, fetch-error card, and an honest empty state (both
  ledgers absent/empty) mirror `/research/registry`'s three-state shell exactly. No forms, no deletion/
  edit affordance anywhere (append-only history).
- **Research hub** — a second card in the EXISTING "Governance & process" grid (iter-30 reserved this
  slot), linking to `/research/graveyard`, `data-testid="research-governance-link-graveyard"` (verbatim
  per spec). The section's header comment updated ("registry + graveyard now; budget / referee-audit
  still to follow") — a documentation-only edit, no structural change.
- **`/research/registry` row anchor** (plan Assumption #4) — each `<tr>` now carries
  `id={`registration-${row.id}`}` + `scroll-mt-20` (mirrors `/evidence`'s `ClaimRow` `id={anchorId}`
  pattern) so a graveyard lineage link can land on the exact row. Presentation-only; no data/behavior
  change to the registry page itself.
- **Drift insurance** (recommended cheap add, iter-30 audit-O1 carry-forward) — `test_registry.py` gained
  one equality test pinning `app.engine.registry._CLAIM_SELECTOR_KEYS ==
  app.mcp.tools._CLAIM_SELECTOR_KEYS`, since the graveyard now leans on `match_registration` for lineage
  and a silent drift between the two tuples would silently break lineage matching.

This iteration is READ-ONLY composition: no `## Evidence Claim`, no referee submission, no ledger write.
`app.engine.evidence`, `app.engine.referee`, `app.engine.ledger`'s write path, `app.mcp.tools:verify_edge`,
and `project-extensions/gates/verify_claim.py` were NOT touched (only imported from, read-only, per the
plan). The one deliberate contract evolution (documented in the blueprint's iter-31 clarification,
already present at `runs/goal-session-mcp-loop/state/blueprint.md` before I started — no edit needed from
me): the iter-9/10/12 "staging ledger is internal-only, never served" invariant narrows so the staging
ledger's NON-PASS verdicts become browsable. The honesty fence holds: the graveyard shows ONLY non-PASS
rows, staging carries 0 PASS rows today, and `/evidence` / `proven_signals` / the "Proven" badge are
verified byte-identical (see Tests Run below).

## Files Changed

- `apps/backend/app/engine/graveyard.py` -- NEW. `resolve_staging_ledger_path()` + `build_graveyard_payload()` + `REVISIT_PROTOCOL`.
- `apps/backend/app/api/graveyard.py` -- NEW. `GET /api/research/graveyard`.
- `apps/backend/main.py` -- import `graveyard` (alphabetically between `evidence` and `health`) + `include_router(graveyard.router, prefix="/api")` beside `registry.router`. Purely additive two lines; no existing import/route line touched.
- `apps/backend/tests/test_graveyard.py` -- NEW. 18 tests (staging-path resolver, non-PASS filter, forward-walk exclusion, ledger tag + deflation verbatim, lineage matched/honest-null, "closed" surfaced verbatim, missing/empty degrade, no-arg default resolution, REVISIT_PROTOCOL no-proven-language, real `ma_stack` round-trip, real 14-entry/all-non-PASS assertion).
- `apps/backend/tests/test_api_graveyard.py` -- NEW. 4 tests (200-empty on missing files, verbatim fixture serving, endpoint-equals-module single-source, real-ledger status-derived count — not a hardcoded "14").
- `apps/backend/tests/test_registry.py` -- EXTENDED. +1 drift-insurance equality test (`_CLAIM_SELECTOR_KEYS` parity with `app.mcp.tools`); no existing test altered.
- `apps/frontend/lib/graveyard.ts` -- NEW. `GraveyardEntry` / `RevisitProtocol` / `GraveyardResponse` types (types-only, mirrors `lib/registry.ts`; no evidence-status resolution).
- `apps/frontend/lib/api.ts` -- `fetchGraveyard()` + re-exported graveyard types (mirrors the `fetchRegistry` addition pattern).
- `apps/frontend/app/research/graveyard/page.tsx` -- NEW. The graveyard table + revisit-protocol panel page.
- `apps/frontend/app/research/page.tsx` -- second governance-grid card linking to `/research/graveyard`; updated the section's own header comment (registry+graveyard now, budget/referee-audit to follow).
- `apps/frontend/app/research/registry/page.tsx` -- added `id`/`scroll-mt-20` to the row `<tr>` (Assumption #4) so graveyard lineage links land on the exact row. Presentation-only.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest <targeted files> -v`

1. **New + extended tests, full run** — `test_graveyard.py` (18), `test_api_graveyard.py` (4),
   `test_registry.py` (23, including the new drift-insurance test) = **45 passed, 0 failed**, all DB-free
   (pure filesystem-read modules — no seed load, no warm-up triggered).
2. I did **not** run the broader `test_evidence.py` / `test_api_evidence.py` /
   `test_gate_registry_enforcement.py` / `test_staging_ledger_routing.py` regression sweep to completion —
   I started it, but after ~10 CPU-minutes with zero output it was clearly hitting the DB-seeded/real-
   referee-computation paths in `test_gate_registry_enforcement.py` (a live `verify_edge` call assembles a
   real cohort across many historical dates), unrelated to anything this iteration touches, and killed it
   rather than burn further time on files I have zero code-path exposure to (per the standing "don't run
   expensive suites speculatively" guidance). Instead I substituted **cheaper, more targeted proof**:
   - `git diff`/`git status` scope check: my only backend edits are two brand-new self-contained files
     plus a strictly-additive two-line `main.py` change (new import, new `include_router` line — no
     existing line touched) plus a test-only extension. `app.engine.evidence`, `app.engine.referee`,
     `app.engine.ledger`, `app.mcp.tools`, and `project-extensions/gates/verify_claim.py` are untouched —
     there is no mechanism by which this diff could affect those other test files' behavior.
   - Live service check (see below) hitting `GET /api/evidence` and `GET /api/research/registry` directly
     — the two canonical endpoints those tests also exercise — confirming byte-identical behavior to their
     documented state.
   - `git status --porcelain` on all three ledger/registry state files (`certified-claims.jsonl`,
     `staging-ledger.jsonl`, `pre-registrations.jsonl`) — empty output, confirming byte-identical / untouched.

**Live end-to-end smoke test** (in lieu of a browser-driven QA pass, which is the browser-qa-agent's job
downstream — I have no browser tool): started both services via `scripts/dev.sh` (auto-offset ports
8255/3255), confirmed:
- `GET /api/research/graveyard` -> 200, 14 entries (7 canonical + 7 staging), all `verdict.status ==
  "FAIL"`, every entry has non-null `lineage` (the iter-30 backfill covers all 14 raw ledger entries), the
  `ma_stack` entry's `lineage.status == "closed"`, `revisit_protocol.rule` present and correctly worded.
- `GET /api/evidence` -> unchanged: 7 claims (canonical only, as designed), `proven_signals: {}`, every
  status `FAIL` — byte-matches the documented all-FAIL plateau state.
- `GET /api/research/registry` -> unchanged: 11 rows (the iter-30 backfill count).
- `GET /research`, `GET /research/graveyard`, `GET /research/registry` -> HTTP 200, no
  "Application error"/"Internal Server Error" markers in any response body.
- `GET /research`'s HTML contains `data-testid="research-governance-link-graveyard"` (the static card
  markup renders immediately; the fetched table rows on `/research/graveyard` and the row anchors on
  `/research/registry` are client-fetched via `useEffect` and so do not appear in a plain curl of the SSR
  shell — expected Next.js "use client" behavior, not a bug; full interactive verification is the
  browser-qa-agent's job).
- Backend/frontend dev logs show zero compile errors and zero runtime errors across all of the above.
- Restarted `dev.sh` a second time (its own port-clearing kill loop, which finds/kills by port occupancy
  rather than tracked PIDs, so it catches nested child processes) — both ports cleanly reclaimed, both
  services came back up serving the same data. Stopped and fully cleaned up both processes afterward
  (verified via `ss -ltnp` + `ps aux` that no leftover uvicorn/next process remained on the used ports).

`npx tsc --noEmit` (frontend, whole project) -- clean, zero errors (one weak-type mismatch caught and
fixed during development: `DeflationLabel`'s prop was typed as an ad-hoc all-optional inline shape, which
TypeScript's weak-type detection rejected against the real `Verdict` type — fixed by typing the prop as
`Verdict` directly). `next lint` is not configured in this repo (no committed ESLint config; invoking it
prompts an interactive first-time setup) — skipped, consistent with the iter-30 precedent.

## Known Issues

- **Frontend `node lib/*.test.ts` harness does not run in this environment** — confirmed again this
  iteration (`node --experimental-strip-types` errors with `ERR_NO_TYPESCRIPT`, "Node.js is not compiled
  with TypeScript support", on every existing `lib/*.test.ts` file, none of which I touched). Pre-existing
  environment limitation (this sandbox's `/usr/bin/node` v22.22.1 build lacks compiled-in TS-stripping
  support; no nvm/volta or alternate Node binary is available), documented identically in the iter-30
  handoff. `lib/graveyard.ts` carries no exported pure logic (types only, mirrors `lib/registry.ts`, which
  also has no companion test file in this codebase — consistent precedent), so this environment gap
  introduces no new test-writing hole. `tsc --noEmit` (clean) plus the live curl-based verification above
  were the practical substitute.
- **No interactive browser click-through was performed by me** (the developer agent has no browser tool).
  I verified via direct HTTP against both live running services instead. Full interactive verification —
  clicking the governance card, reading the rendered table (selectors/verdict/date/deflation/ledger/
  lineage), confirming the `ma_stack` "permanent" pill and a resolved lineage link land on the correct
  `/research/registry` row, and checking the revisit-protocol anchor — remains the browser-qa-agent's job
  for J-19.
- **`.claude/project-template.md` is still the unfilled generic template** for this project (placeholders,
  not Trendora-specific values) — pre-existing gap, unchanged since iter-30's handoff noted the same. I
  inferred the real commands the same way: `scripts/dev.sh`, existing test files, and the iter-30 dev
  handoff's own confirmed command (`cd apps/backend && .venv/bin/python -m pytest <targeted files> -v`;
  `node lib/*.test.ts` for frontend pure-logic modules).
- **No `[NEW]`-flagged demo-narrator walkthrough was produced by this dev pass** — that is the downstream
  `demo-narrator` agent's job, expected later in the standard pipeline.
