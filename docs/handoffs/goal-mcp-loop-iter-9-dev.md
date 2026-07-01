# goal-mcp-loop-iter-9 Dev Handoff

**Phase:** goal-mcp-loop-iter-9
**Date:** 2026-07-01
**Agent:** developer
**Status:** complete

## What Was Built

Part A of goal.md's engineering direction — the **sustainable trial economy**: an injectable,
**default-off** online-FDR (LORD++) deflation policy that runs in a SEPARATE internal **staging** ledger,
so future iterations (J-07 multi-horizon, J-08 combinations) can explore edges without permanently
tightening the user-facing canonical Bonferroni bar. **Zero user-visible change by design** — canonical
`/evidence` and every "Proven" badge stay byte-identical.

Nine backend seams, every one default-preserving:

- **NEW `app/engine/online_fdr.py`** — a PURE LORD++ module (no RNG, no IO). `test_level(t, rejection_offsets, …)`
  allocates the per-trial significance level from the deterministic sequence of prior rejection ordinals
  (alpha-wealth reconstructed from rejection times — zero migration). The spending sequence is the
  normalized polynomial `γ_j = j^-p / ζ(p)`; the ζ normalizer is computed deterministically via an
  Euler–Maclaurin tail (accurate to ~1e-12, matches true ζ(1.6)=2.285765665680). Every tunable is injected.
- **`app/engine/referee.py`** — the multiple-testing deflation is now an INJECTABLE policy on `RefereeState`
  (new `deflation` / `test_level` fields, DEFAULT = Bonferroni). When `test_level is None` (the default) the
  referee reproduces `required_p = alpha_per_test / n_trials` **byte-identically** (including the exact
  reason-string bar `alpha/{divisor}=…`); a staging economy supplies the level directly.
- **`app/engine/ledger.py`** — new DERIVED `rejection_offsets(path)` (the PASS-entry ordinals; `[1, 2, 4]`
  on the live canonical ledger). No schema change, no entry rewritten. Feeds the LORD++ wealth reconstruction.
- **`app/mcp/tools.py`** — `verify_edge` now takes a `ledger` selector and threads the economy: canonical ⇒
  ALWAYS Bonferroni (the honesty fence); staging ⇒ the configured online-FDR economy WHEN `fdr.enabled`,
  else Bonferroni. It reads cumulative state from THAT ledger and appends THERE — still the SINGLE ledger
  writer, still READ-ONLY w.r.t. the snapshot DB.
- **`app/engine/forward_walk.py`** — `_rescore` reconstructs the policy `test_level` from each entry's
  recorded `required_p` (Bonferroni entries re-derive `alpha/divisor` from the ordinal, unchanged; staging
  entries pin the recorded level), so a re-score reproduces the original verdict byte-for-byte.
- **`app/config.py`** — new typed `FdrCfg` (default-off) + `staging_ledger_path` on `EvidenceCfg`, both
  default-populated (a config predating the block loads unchanged); malformed `fdr` ⇒ loud `ConfigError`.
- **`config.yaml`** — documented `evidence.staging_ledger_path` + an `fdr` sub-block (`enabled: false` +
  LORD++ tunables), consumed verbatim (no magic numbers in code).
- **`project-extensions/gates/verify_claim.py`** — reads an OPTIONAL per-claim `"ledger"` key (default
  `staging`, explicit `canonical`) and routes to `STAGING_LEDGER_PATH` vs `LEDGER_PATH`. Keeps `exit 3`-on-
  non-PASS + fail-closed-on-unset-path, and now **fail-closes an unrecognized `ledger` value** (never
  silently certified).
- **`scripts/automation/run-goal.sh`** — exports `STAGING_LEDGER_PATH` alongside `LEDGER_PATH` at both
  dispatch sites (the post-decompose gate and the post-goal hook).

## Files Changed

- `apps/backend/app/engine/online_fdr.py` — **NEW.** PURE LORD++ test-level allocator (ζ normalizer + wealth-from-rejection-times).
- `apps/backend/app/engine/referee.py` — injectable deflation policy on `RefereeState` (default Bonferroni, byte-identical).
- `apps/backend/app/engine/ledger.py` — derived `rejection_offsets(path)` accessor (no schema change).
- `apps/backend/app/mcp/tools.py` — `verify_edge` threads the economy + `ledger` routing; still the only writer.
- `apps/backend/app/engine/forward_walk.py` — reconstruct `test_level` from recorded `required_p` (both policies reproduce).
- `apps/backend/app/config.py` — `FdrCfg` (default-off) + `staging_ledger_path` on `EvidenceCfg`.
- `config.yaml` — `evidence.staging_ledger_path` + the documented default-off `fdr` sub-block.
- `project-extensions/gates/verify_claim.py` — per-claim `ledger` routing + fail-closed on unrecognized/unset.
- `scripts/automation/run-goal.sh` — export `STAGING_LEDGER_PATH` at both `LEDGER_PATH` sites (via the `incredible_auto_dev/` real path behind the `scripts` symlink).
- `apps/backend/tests/test_online_fdr.py` — **NEW.** PURE LORD++ tests (frozen values, determinism, ζ, validation).
- `apps/backend/tests/test_staging_ledger_routing.py` — **NEW.** routing/isolation/policy/forward-walk/gate + DB integration.
- `apps/backend/tests/test_config.py` — FdrCfg defaults + validation + malformed-config error + real-config check.
- `apps/backend/tests/test_evidence.py` — canonical frozen-golden (4 entries byte-identical, `proven_signals == {leadership_score}`).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`

- Affected-module runs (all green):
  - `test_online_fdr.py` + `test_referee.py` + `test_forward_walk.py` + `test_evidence.py` — **36 passed** (referee/forward_walk **unedited**, proving defaults reproduce today).
  - `test_config.py` + `test_staging_ledger_routing.py` (non-DB) — **73 passed**.
  - `test_staging_ledger_routing.py` (DB) + `test_api_evidence.py` + `test_mcp_window.py` — **27 passed** (151s DB boot).
- **Full suite: `1285 passed, 4 skipped, 1 failed` (2164s).** The single failure —
  `test_data_manager_jobs_pipeline.py::test_backfill_speedup_factor_in_backend_stages_payload` — is an
  **unrelated, pre-existing wall-clock TIMING flake** (it re-derives a parallel-backfill speedup from real
  elapsed seconds against a 1e-6 tolerance: `abs(0.363 − 0.3629) = 1e-4`, drift caused by CPU contention
  from the concurrent 36-min run). `data_manager` is **untouched by this iteration**, and the test
  **passes cleanly in isolation** (`1 passed in 4.75s`). Not an iter-9 regression.

Key assertions pinned:
- **Canonical byte-identical:** the 4 live ledger entries (statuses PASS/PASS/FAIL/PASS, divisors 1..4, all
  `deflation="bonferroni"`) are unchanged and `proven_signals == {leadership_score}`.
- **Defaults reproduce today:** `test_referee.py` / `test_forward_walk.py` stay green **unedited**.
- **`online_fdr` PURE + deterministic:** exact frozen `test_level` on `[1,2,4]`; ζ matches the true value.
- **`rejection_offsets` derives `[1,2,4]`** from the live canonical ledger (no entry rewritten).
- **Staging isolated + routed:** a staging `verify_edge` writes staging only; canonical writes canonical
  under Bonferroni; the honesty fence holds (canonical stays Bonferroni EVEN with FDR enabled).
- **forward_walk reproduce-contract:** both Bonferroni and FDR entries reproduce byte-for-byte.
- **Gate:** routes per-claim (default staging), fail-closes an unrecognized ledger value + an unset path.

## Known Issues

- **None functional.** The economy is fenced to staging and `enabled: false` by default, so canonical
  behavior is byte-identical and no "Proven" claim, canonical write, or Evidence-Claim block ships this
  iteration (the post-decompose gate passes through by design).
- The staging ledger file (`runs/goal-session-mcp-loop/state/staging-ledger.jsonl`) does not yet exist —
  intentional: a MISSING ledger is an EMPTY ledger, so the first staging claim (iter-10+) starts from a
  clean budget. No pre-seeding is required.
- The MCP `verify_edge` server tool keeps its historical signature (defaults to canonical/Bonferroni) — the
  new `ledger` routing is exercised through the gate, not the MCP tool surface (deliberately unchanged).
- No frontend / service-start changes this iteration (backend-infrastructure only) — service startup and
  external integrations are unaffected; the pre-handoff service/integration/binary checks are N/A here.
