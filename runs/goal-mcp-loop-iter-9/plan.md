# goal-mcp-loop-iter-9 Execution Plan

> **Gate status: PASS-THROUGH by design — iteration UNBLOCKED.** This spec carries **NO `## Evidence
> Claim` block**, so the post-decompose gate passes through automatically (it only certifies
> claim-bearing specs). This iteration ships **NO new "Proven" claim** and makes **NO write to the
> canonical `certified-claims.jsonl`** — it therefore cannot block on the referee and cannot tighten
> the canonical Bonferroni bar. This is a **backend-infrastructure milestone** (Part A of goal.md's
> engineering direction), scored by the DEFINITION OF DONE below — NOT by a J-07/J-08 status change.
>
> **THE LOAD-BEARING INVARIANT: canonical stays byte-identical.** The 4 existing ledger entries
> (`deflation="bonferroni"`, divisors 1–4; line 3 `ma_stack` is a permanent FAIL — honest history),
> `build_evidence_payload(canonical)` / `GET /api/evidence`, and `proven_signals == {leadership_score}`
> MUST be byte-for-byte unchanged ⇒ J-01..J-06 unperturbed. FDR is `enabled: false` by default.
> **ESCALATION:** if the "injectable, default-off / defaults-reproduce-today" invariant cannot be met
> without altering any of the 4 canonical entries or the default `certify_edge` output, **STOP and flag
> in the handoff** — do NOT modify the canonical entries or the default path. Honest history is
> non-negotiable.

## What to Build

Stand up an **injectable, default-off online-FDR (LORD++) deflation policy** running in a SEPARATE
internal **staging** ledger, so future iterations (J-07 multi-horizon, J-08 combinations) can explore
without permanently tightening the user-facing canonical Bonferroni bar. Nine backend seams, all
default-preserving:

- **NEW `apps/backend/app/engine/online_fdr.py`** — a **PURE** LORD++ online-FDR module (no RNG, no IO).
  Derives the per-trial significance `test_level` an online-FDR economy allocates given the deterministic
  sequence of prior rejection offsets (wealth reconstructed from rejection times — zero migration). Pure
  ⇒ trivially unit-testable + determinism-preserving. Every LORD++ tunable comes from config, no magic
  numbers.
- **`apps/backend/app/engine/referee.py`** — make the multiple-testing deflation an **injectable policy**
  on `RefereeState` (a `deflation` / `test_level` selector) with **DEFAULT = Bonferroni**, so
  `certify_edge` reproduces today's `required_p = alpha_per_test / max(1, n_trials)` **byte-identically**.
  `Verdict` already records `required_p` + `deflation_divisor` + `deflation`; keep recording the policy
  used per verdict. **No behavior change on the default path.**
- **`apps/backend/app/engine/ledger.py`** — add a **DERIVED** `rejection_offsets` accessor (the ordinals
  of PASS entries; on the live canonical ledger `[1, 2, 4]` — lines 1/2/4 PASS, line 3 FAIL). Derived
  only — **no schema change, no rewrite of any existing entry.** Feeds the LORD++ wealth reconstruction.
- **`apps/backend/app/mcp/tools.py`** — `verify_edge` threads the economy: it selects the target ledger
  (canonical vs staging) and the matching deflation policy (canonical ⇒ Bonferroni; staging ⇒ the
  configured economy), reads cumulative state from THAT ledger, and appends THERE. `verify_edge` MUST
  remain the **ONLY** ledger writer (iter-1 lesson — route the one writer to a different file; do NOT add
  a second write path) and MUST stay **READ-ONLY** w.r.t. the snapshot DB (sole write = the ledger append).
- **`apps/backend/app/engine/forward_walk.py`** — preserve the reproduce-contract by reconstructing the
  policy `test_level` from each entry's recorded `required_p`, so a re-score reproduces the original
  verdict byte-for-byte (only newer/matured data may move it). A canonical (Bonferroni) entry already
  reproduces via `n_trials_at_test`; a staging entry reconstructs `test_level = recorded required_p`.
- **`apps/backend/app/config.py`** — extend `EvidenceCfg` with a typed **`FdrCfg`** (defaults reproduce
  today: FDR **off**) and a **`staging_ledger_path`**. A config predating this block (and inline test
  fixtures) must still load + behave identically.
- **`config.yaml`** — add a documented `evidence.staging_ledger_path`
  (`runs/goal-session-mcp-loop/state/staging-ledger.jsonl`) and an `fdr` sub-block (`enabled: false` by
  default + LORD++ tunables), consumed VERBATIM (no magic numbers in code). Default-off ⇒ canonical
  behavior unchanged.
- **`project-extensions/gates/verify_claim.py`** — read an OPTIONAL per-claim `"ledger"` key (default
  `"staging"`, explicit `"canonical"` for promoted winners) and route `verify_edge` to the corresponding
  path (`STAGING_LEDGER_PATH` vs `LEDGER_PATH`). Keep `exit 3`-on-non-PASS blocking and fail-closed-on-
  unset-path UNCHANGED. An **unrecognized `"ledger"` value is fail-closed (block)**, never silently
  certified.
- **`scripts/automation/run-goal.sh`** — export `STAGING_LEDGER_PATH` (pointing at the staging ledger
  under `state/`) alongside the existing `LEDGER_PATH`, at the **same two dispatch sites** that currently
  set `LEDGER_PATH` (≈ lines 1070 and 1401).

## Agents Required
- **developer: yes** — a single backend agent drives the whole iteration with TDD. It is a load-bearing
  refactor of the shared certification engine under a strict byte-identical-defaults invariant.
- **backend-data: yes** — all nine seams above (engine + config + gate + harness) plus their unit /
  integration tests.
- **frontend-ux: no** — **zero frontend change.** The staging ledger + FDR economy are INTERNAL; they are
  never served to an endpoint and never displayed. A user-visible change here would be a **DEFECT**
  (canonical `/evidence` and every "Proven" badge must stay byte-identical).

## Frontend Present

Frontend Present: no

This is a purely internal backend-infrastructure iteration with **zero user-visible impact by design** —
`no` per the spec's "No visible delta by design" and "A user-visible change here would be a DEFECT". No
new surface, no new endpoint, no nav change. J-01..J-06 are re-confirmed by the goal-mode deterministic
golden-script replay over the **unchanged** canonical `/api/evidence` (or, if that replay does not run
for a backend-only iteration, a browser-qa regression pass over J-01..J-06). Judge regression on the
canonical `/api/evidence` byte-match + the unit suite — NEVER on the dead `browser_checks_run` flag
(iter-6 lesson).

## Files to Create/Modify
- `apps/backend/app/engine/online_fdr.py` — **NEW.** PURE LORD++ module: `test_level` from rejection
  offsets; no RNG/IO; tunables injected from `FdrCfg`.
- `apps/backend/app/engine/referee.py` — injectable deflation policy on `RefereeState` (default
  Bonferroni); referee reads the selected `test_level` / falls back to `alpha_per_test/divisor`. Keep the
  `Verdict` audit fields (`required_p`/`deflation_divisor`/`deflation`).
- `apps/backend/app/engine/ledger.py` — add derived `rejection_offsets(path)` (PASS-entry ordinals; skip
  forward-walk records exactly like `count_trials`). No schema change.
- `apps/backend/app/mcp/tools.py` — `verify_edge` routes ledger + policy (canonical vs staging); stays the
  ONLY writer and DB-read-only.
- `apps/backend/app/engine/forward_walk.py` — reconstruct `test_level` from the recorded `required_p` in
  `_rescore` so re-scores stay byte-identical.
- `apps/backend/app/config.py` — `FdrCfg` (default-off) + `staging_ledger_path` on `EvidenceCfg`; typed +
  validated; malformed `fdr` ⇒ loud `ConfigError` or a documented Bonferroni fall-back (never a silent
  weakening).
- `config.yaml` — `evidence.staging_ledger_path` + the documented `fdr` sub-block (`enabled: false`).
- `project-extensions/gates/verify_claim.py` — optional per-claim `"ledger"` routing (default `staging`);
  keep `exit 3` + fail-closed; unrecognized value ⇒ block.
- `scripts/automation/run-goal.sh` — export `STAGING_LEDGER_PATH` at both `LEDGER_PATH` sites (~1070, ~1401).
- **Tests (TDD):** NEW `apps/backend/tests/test_online_fdr.py` (purity + deterministic `test_level` +
  `rejection_offsets` → `[1,2,4]`); NEW routing / cross-contamination integration test driving
  `verify_edge` + the gate both ways (e.g. `tests/test_staging_ledger_routing.py`); extend
  `tests/test_config.py` (FdrCfg defaults + malformed-config error); a canonical frozen-golden regression
  (`GET /api/evidence` + 4 entries byte-identical) in `tests/test_api_evidence.py` / `tests/test_evidence.py`;
  existing `tests/test_referee.py` + `tests/test_forward_walk.py` stay green **unedited**.
- `docs/handoffs/goal-mcp-loop-iter-9-dev.md` — **required** dev handoff (DoD).

Pipeline-produced (not by the developer): `docs/handoffs/goal-mcp-loop-iter-9-audit.md` — the full QA +
auditor pipeline MUST complete the audit stage this iteration (full depth for a load-bearing engine
refactor).

**Do NOT touch:** any `apps/frontend/**`; the 4 canonical `certified-claims.jsonl` entries; the default
`certify_edge` output; `GET /api/evidence`'s shape/payload; the referee's statistical procedure
(holdout/bootstrap/Thresholdout) on the default path.

## Blueprint note (already done — do NOT duplicate)
The additive **iter-9 clarification** note is **already present** in
`runs/goal-session-mcp-loop/state/blueprint.md` (Data Contract section, ~lines 152–170), and
`blueprint.approved` exists. Information Architecture is untouched (no new surface, no nav change), so
**no `blueprint.reapproval-requested` is written and the developer must NOT re-edit the blueprint.**
Canonical proven-ness still flows solely from `verdict.status == PASS` under strict Bonferroni.

## Key Test Scenarios
- **Canonical byte-identical (load-bearing):** `GET /api/evidence` payload + the 4 ledger entries are
  byte-identical against a frozen golden; `proven_signals == {leadership_score}`. ⇒ J-01..J-06 unperturbed.
- **Defaults reproduce today:** every existing `test_referee.py` / ledger / evidence / api-evidence test
  stays green **with no expectation edits**; the default deflation path is Bonferroni and `certify_edge`
  yields the identical `required_p` / `deflation_divisor` / verdict for the existing fixtures.
- **`online_fdr.py` PURE + deterministic:** allocated `test_level` asserted exactly on a known
  rejection-offset sequence (same input ⇒ same output, no RNG/IO); `rejection_offsets` derives `[1, 2, 4]`
  from the live canonical ledger (no entry rewritten).
- **Staging isolated + routed:** a staging-routed `verify_edge` appends to the staging file **only** (NOT
  canonical); a `"ledger":"canonical"` claim appends to `certified-claims.jsonl` under strict Bonferroni
  **only** (cross-contamination test, both directions).
- **`forward_walk` reproduce-contract:** reconstructing `test_level` from a recorded `required_p`
  reproduces the original verdict byte-for-byte.
- **Gate routing + fail-closed:** `verify_claim.py` reads the optional `"ledger"` key (default `staging`),
  routes correctly, keeps `exit 3`-on-non-PASS + fail-closed-on-unset-path, and **fail-closes an
  unrecognized `"ledger"` value** (block / `exit 3`, never certified).
- **Harness:** `run-goal.sh` exports `STAGING_LEDGER_PATH` at both `LEDGER_PATH` dispatch sites; `fdr` is
  `enabled: false` in `config.yaml`.
- **Error cases (rejected, not silently weakened):** `STAGING_LEDGER_PATH` (or `LEDGER_PATH`) unset for a
  claim that needs it ⇒ fail-closed block (never a silent canonical write); malformed `fdr` config ⇒ loud
  `ConfigError` or a documented Bonferroni fall-back (never a silent weakening of the canonical bar).
- **J-01..J-06 regression:** re-confirmed by the goal-mode deterministic golden-script replay (every
  evidence badge byte-identical against the unchanged canonical `/evidence`); else a browser-qa regression
  pass over J-01..J-06. J-07/J-08 do NOT regress (remain unbuilt/unknown — expected).
- **Anti-goals:** secret scan of the diff clean; no return/price/buy-sell/alpha language; determinism +
  no-lookahead preserved; canonical proven-ness unchanged (FDR fenced to staging, weaker than family-wise
  and never touches the canonical badge).

## Scope, Drift & Assumptions
- **Goal alignment: CONFIRMED.** goal.md's engineering direction is explicit — "build the economy first,
  then widen the scan"; Part A is "build this FIRST"; Part B (multi-horizon + combinations = J-07/J-08) is
  "after A". iter-9 builds **Part A only**. Doing J-07/J-08 first would force blind canonical claims
  against a divisor-5 bar, risking a gate FAIL that blocks the iteration AND permanently tightens the bar
  — the exact failure mode the economy prevents.
- **OUT OF SCOPE (exclude — flagged scope guards):** **Part B / opening the scan aperture** (iter-10+):
  multi-horizon scan config (`triad.horizons`), the combination enumerator + selector translation in
  `triad_scan.py`, raising `triad.top_k` / `screen.haircut_coef`, and the pre-registered combination
  candidate set + `proposer-guidance.md` mirror. **J-07 surfacing** (non-20-horizon factor-lab badge /
  `/evidence` row / canonical claim). **J-08 surfacing** (combination-lab badge / row / claim). **Any new
  "Proven" claim** or any write to canonical `certified-claims.jsonl`. **Any Evidence-Claim block** (this
  spec carries none by design). **Any frontend / page / nav change.** The note's deferred ideas (quantile
  spreads, regime conditioning, sector cohorts, scoped α-split families).
- **Assumptions (documented, not asked):**
  - `online_fdr.py` is default-**off** and fenced to staging, so its exact LORD++ numerics never touch
    canonical; the correctness bar is (a) purity/determinism and (b) that the OFF path reproduces
    Bonferroni byte-identically. Exact LORD++ constants (`alpha`, wealth/reward params) come from the
    `config.yaml` `fdr` block — no magic numbers in code.
  - The staging ledger file need not pre-exist: a MISSING ledger is an EMPTY ledger (0 trials, fresh
    budget) per `ledger.py` semantics — the first staging claim starts clean.
  - The injectable policy is added to `RefereeState` as a new field with a default (`deflation="bonferroni"`
    / `test_level=None`), so every existing `RefereeState(...)` construction and every existing referee
    test stays byte-identical.
- **Verification gap = HARD fail (iter-0/2/5/6 lesson):** score regression on the byte-identical
  `/api/evidence` payload + the green unit suite + (where run) the canonical `…-ui-test-results.md` — NEVER
  on the dead `browser_checks_run` flag and NEVER on a secondary QA-lane PASS. Any mid-run harness fix must
  live in the per-step child scripts, not the running parent.
