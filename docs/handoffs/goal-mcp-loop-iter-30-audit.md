# goal-mcp-loop-iter-30 Audit Report

**Date:** 2026-07-13
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

The pre-registration registry (J-18 / B-901) is fully and correctly delivered: a read-only `/research/registry` page discoverable in one click, a single-source loader, and a fail-closed gate pre-check that refuses any unregistered Evidence Claim *before* `verify_edge` runs. The three highest-stakes invariants all hold under independent verification from git and the live ledgers — both ledger files, `referee.py`, `ledger.py`, and `tools.py` are byte-untouched vs HEAD; the canonical Bonferroni divisor stays 8; no `## Evidence Claim` was introduced; and the backfill's row count (11) is the mathematically correct dedup of the 14 raw ledger entries, not a fabrication. No critical or important gaps remain; no fixes were required.

---

## 2. Findings

### Backend Findings

**B1 — VERIFIED (no issue): Ledger/referee/tools byte-untouched; divisor stays 8.**
`git status --short` against `runs/goal-session-mcp-loop/state/certified-claims.jsonl`, `staging-ledger.jsonl`, `apps/backend/app/engine/referee.py`, `app/engine/ledger.py`, and `app/mcp/tools.py` returns empty (all unmodified vs HEAD `5d8715e`). Both ledgers are git-tracked (`git ls-files` confirms), so byte-identity is meaningful. The canonical ledger holds exactly 7 entries → the next trial faces Bonferroni divisor 8; the `config.yaml` diff is purely the additive `evidence.registry` block (no divisor/deflation change). Invariant upheld.

**B2 — VERIFIED (no issue): Gate is a fail-closed pre-check before `verify_edge`.**
`project-extensions/gates/verify_claim.py:143-149` runs `if get_config().evidence.registry.enforce and registry_mod.match_registration(claim) is None:` → appends a `BLOCKED` result, sets `blocked=True`, and `continue`s, *before* the `tools.verify_edge(...)` call at `:150-153`. No new parameter threads into `verify_edge`/`certify_edge`/ledger modules — it is a pure short-circuit. `main()` returns `3 if blocked else 0` (`:167`), so a refusal is exit 3, never a silent pass. A missing registry file with `enforce=true` refuses every claim (fail-closed, test-proven). The iteration's own gate run is unaffected: with no `## Evidence Claim`, `extract_claims` returns `[]` and the gate exits 0 at `:126-127` before the registry check is ever reached.

**B3 — VERIFIED (no issue): `registered_date` is the real 2026-07-03, not a laundered "today".**
All 11 rows in `runs/goal-session-mcp-loop/state/pre-registrations.jsonl` carry `"registered_date": "2026-07-03"` (the ledgers' own `register_date`), never today's date (2026-07-13). `test_registry.py:242` asserts this on every committed row. This sidesteps the "retroactive registration to launder a mined result" trap B-901 names — the audit trail cites the honest recorded date.

**B4 — VERIFIED (no issue): `enforce: true`, correctly sequenced and default-off in code.**
`RegistryCfg.enforce` defaults to `False` in `app/config.py` (mirrors `FdrCfg.enabled=False`), so any fixture predating the block loads byte-identically. `config.yaml:1103` flips it to `true` with a comment documenting the sequencing (backfill verified complete first). The gate's enforcement-off path is proven byte-identical to pre-iter-30 by `test_enforcement_off_unregistered_claim_still_proceeds`.

**B5 — VERIFIED (no issue): `_CLAIM_SELECTOR_KEYS` mirrors `tools.py` byte-for-byte.**
`app/engine/registry.py:80-84` is a character-identical copy of `app/mcp/tools.py:395-399` (independently diffed). Kept a local literal so the module stays engine-free/pure, consistent with the existing `ledger._PASS_STATUS`-mirrors-`referee.STATUS_PASS` precedent. See O1 for the future-drift note.

### Frontend Findings

**F1 — VERIFIED (no issue): Single-source, read-only, no proven-language.**
`app/research/registry/page.tsx` reads ONLY `fetchRegistry` → `GET /api/research/registry` (`lib/api.ts`), which serves `load_registrations()` verbatim as `{"registrations": [...]}` (`app/api/registry.py:32`) — the same file+loader the gate uses. Three honest states (loading skeleton / "Backend unavailable" error card / empty state) plus the table. Status renders in the neutral `Badge default` variant (not the accent/danger PASS/FAIL coloring), backfills carry a "backfill" pill. A grep sweep found "proven"/"certify" only in documentation comments and one governance-descriptive subtitle ("the gate refuses to certify any Evidence Claim that does not match a row here") — no registry row is presented as proven/confident. Anti-goal #1 upheld.

**F2 — VERIFIED (no issue): Discoverable in 1 click; `RESEARCH_LABS` untouched.**
`app/research/page.tsx:78-105` adds a separate "Governance & process" section with one card linking to `/research/registry` via `useAsOfHref`; the `RESEARCH_LABS` array (the J-113 ten-lab reading-order contract) is left completely unmodified. No existing lab/route added, removed, or renamed.

### Test Findings

**T1 — VERIFIED (no issue): Gate fixtures assert the load-bearing contract with tight assertions.**
`test_gate_registry_enforcement.py` proves, via a `verify_edge` spy stub (DB-free): registered exact-match → `len(calls)==1` (referee reached); unregistered → `calls==[]` (never called) **and** target ledger `read_bytes()==before` (no write) **and** `rc==3` **and** the BLOCKED reason names "registry"+"register"; near-miss (decile 10→9) → `calls==[]`, `rc==3`; enforce-off → proceeds; missing file → refuses all. Assertions are exact, not loose. I re-ran the suite independently: **30 passed in 0.74s** (`tests/test_registry.py tests/test_api_registry.py tests/test_gate_registry_enforcement.py`), plus **3 passed** for the `RegistryCfg` config tests.

**T2 — VERIFIED (no issue): Backfill completeness proven against real data, not a hand-count.**
`test_registry.py:256-273` iterates BOTH live ledgers and asserts every claim round-trips to a backfilled row via the real `match_registration`; `:225-253` asserts exactly 11 rows, unique ids, unique selector-sets (the dedup requirement), `registered_by=="backfill"`, exact date, status ∈ {tested, closed}, and exactly one `ma_stack` row marked `closed`.

---

## 3. Domain Assessment

The core domain logic is correct and the row-count question — the coordinator's flagged risk — resolves cleanly in favor of the implementation.

**The 11-vs-"≥14" count is right, and no rows were fabricated.** I traced every ledger entry to a backfill row independently of the handoff:
- Canonical ledger (7 entries) → backfill rows {1, 2, 3, 4, 6, 7, 11}.
- Staging ledger (7 entries) → backfill rows {5, 6, 7, 8, 9, 10, 11}.
- Union = all 11 rows; the intersection {6, 7, 11} are the 3 hypotheses that appear in *both* ledgers with an identical selector-set (`vcp_contraction` d10 h60; `rs_spy_3m` d10 h60; `rs_spy_3m`×`high_proximity` h20 — each a staging candidate later promoted/re-tested under `ledger:canonical`). 14 raw − 3 cross-ledger duplicates = 11 distinct hypotheses.

This dedup is a **functional requirement, not a shortcut**: `match_registration` must resolve an exact selector-set to *one* row, so the registry cannot hold two rows sharing an identical selector tuple. The 7 proposer-guidance §4.1/§4.2 candidates coincide 1:1 with rows 5-11 (verified against `project-extensions/proposer-guidance.md:67-98`), so they add nothing net-new. The spec's "≥14" was the decomposer's uncomputed estimate; the dev flagged the deviation explicitly, the reviewer independently recomputed it, and this audit confirms it a third way against the live ledgers. Collapsing a staging→canonical promotion into one hypothesis row (with a combined `source`) is the correct modeling of a registry-of-hypotheses. This is exactly the honesty the framework rewards (judgment-rubric §6): the dev shipped the correct 11 rather than fabricating 3 phantom rows to hit a literal number.

**Governance mechanism is sound.** The registry is the single source both the human-facing page and the machine gate read through the same loader, so they can never disagree. The gate makes pre-registration *binding* (a machine checks it) rather than conventional, and does so fail-closed. Scope is disciplined per B-901's named dominant failure mode: a registry + loader + gate check + read-only page — no mutation UI, no approval workflow, no quota accounting.

---

## 4. Fixes Applied During This Audit

None. No critical or important issues were found; the implementation required no correction.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied |

---

## 5. Recommended Next Step

**Proceed.** J-18 / B-901 is complete and correct; the governance keystone is in place for the downstream journeys that depend on it (J-19 graveyard reads this registry's lineage; every future Evidence Claim now passes through the gate). Two informational observations below are for the record only — neither warrants a fix in this iteration (fixing them would be scope creep).

- **O1 (observation, maintainability — considered GAP, no current impact):** `registry.py`'s `_CLAIM_SELECTOR_KEYS` is a hand-synced copy of `tools.py`'s constant, enforced only by a code comment ("update both together") and manual review — there is no test asserting `registry._CLAIM_SELECTOR_KEYS == tools._CLAIM_SELECTOR_KEYS`. They are byte-identical today (verified), so there is zero current defect. The round-trip tests use `registry.claim_selectors` on both sides, so they would not necessarily catch a future one-sided divergence if `tools.py` later adds a selector key. A one-line equality regression test would be cheap insurance for a future iteration. Not fixed: the spec did not require it and there is no observable impact today.
- **O2 (observation, report precision):** The QA report's TC-12 states no "evidence"/"certified" keywords appear on the page, but the page subtitle does contain "certify any Evidence Claim" in accurate governance-describing context. The substantive conclusion (no registry row presented as proven) is correct; only the keyword-scan wording was imprecise. No product impact.
