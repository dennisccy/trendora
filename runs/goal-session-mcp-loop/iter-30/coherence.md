# Iteration 30 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-30
**Date:** 2026-07-13
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| **Pre-registration registry** (NEW this iteration — J-18/B-901) | OK | Single loader `apps/backend/app/engine/registry.py:57` (`load_registrations`) + `:104` (`match_registration`). Single endpoint `apps/backend/app/api/registry.py:27-32` (`GET /research/registry`) imports and serves the loader verbatim, no recompute. The gate's cross-check, `project-extensions/gates/verify_claim.py:47` (import `app.engine import registry as registry_mod`) and `:140` (`registry_mod.match_registration(claim)`), goes through the identical module/function — confirmed by `apps/backend/tests/test_api_registry.py:58-66` (`test_registry_endpoint_equals_loader_output_directly`) and `apps/backend/tests/test_gate_registry_enforcement.py` (gate reads the same `REGISTRY_PATH_ENV`-resolved file via `registry_mod`). No second parse path found anywhere in the diff. |
| **Evidence status / certified-claim** (existing canonical value the gate change sits beside) | OK — untouched | `git diff <snapshot> --stat -- apps/backend/app/engine/referee.py apps/backend/app/engine/ledger.py apps/backend/app/mcp/tools.py apps/backend/app/engine/evidence.py runs/goal-session-mcp-loop/state/certified-claims.jsonl runs/goal-session-mcp-loop/state/staging-ledger.jsonl` returns empty — zero byte changed in any of the six. `apps/backend/app/config.py`'s only touch to `EvidenceCfg` is the new additive `registry: RegistryCfg` field (default `enforce=False`); `ledger_path`/`staging_ledger_path`/`fdr` untouched. The gate's registry pre-check (`verify_claim.py:140-148`) sits strictly BEFORE `tools.verify_edge` and short-circuits on no-match without calling it — proven by `test_gate_registry_enforcement.py::test_unregistered_claim_is_refused_before_verify_edge` (asserts `verify_edge` never called + target ledger file byte-identical). |
| Three per-stock scores, regime score, sector/theme scores, forward-return evidence, research-lab cohorts, index vendor label, DB capacity snapshot (all other registered rows) | OK — untouched | None of these modules/endpoints appear anywhere in the diff (`apps/backend/app/engine/scoring.py`, `regime.py`, `sectors.py`, `themes.py`, `forward_testing.py`, `research.py`, `indexes.py`, `data_manager.py` are all absent from both the tracked-file diff and the untracked-file list). |

No duplicate computation, no non-canonical source, no unregistered-but-new value (the registry value was pre-registered in `blueprint.md`'s Data Contract by this iteration's own decomposer edit, confirmed present at `runs/goal-session-mcp-loop/state/blueprint.md` lines 110 and the iter-30 clarification paragraph at the file's end).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/research/registry` (new page) | OK | `apps/frontend/components/sidebar.tsx:38` — persistent top-level `Research` link (`/research`), unchanged. `apps/frontend/app/research/page.tsx` (diff) adds a "Governance & process" section with one card (`data-testid="research-governance-link-registry"`) linking to `asofHref("/research/registry")`. Total reachability: sidebar → `/research` (1 click) → registry card (2nd click) = 2 clicks, identical hub-reached pattern to all 10 existing labs (`RESEARCH_LABS`, `lib/research-labs.ts`, confirmed untouched by this diff — no lab added/removed/renamed, no reading-order contract broken). No new `layout.tsx` under `apps/frontend/app/research/registry/` (directory listing confirmed) — the page inherits the shared shell, not a parallel shell. Not a duplicate home: no other page in the IA represents "pre-registration registry"; the closest existing concept, `/evidence` (certified-claims ledger), is a distinct, already-registered entity the new page's own text explicitly disclaims overlap with ("no proven-language ... the single source of Proven stays /evidence"). |

No blocking violations.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. The gate change (`project-extensions/gates/verify_claim.py`) has no UI surface by design (a CLI pre-check in the automated pipeline, never reachable from the running app) — this is correctly not treated as a missing nav path, per the coordinator note and the `ui-surface-map`'s own classification. `runs/goal-session-mcp-loop/state/blueprint.reapproval-requested` was filed as required by the iter-29 pre-commitment for a new `/research/*` sub-route grouping, content matches the iteration spec's stated intent.
