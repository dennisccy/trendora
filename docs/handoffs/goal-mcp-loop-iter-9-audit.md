# goal-mcp-loop-iter-9 Audit Report

**Date:** 2026-07-01
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

iter-9 delivers exactly Part A of goal.md's engineering direction — an injectable, default-off online-FDR
(LORD++) staging economy — with the load-bearing invariant intact: the canonical `certified-claims.jsonl`
is byte-identical (git-confirmed unmodified since iter-8), the default deflation path is strict Bonferroni,
and the honesty fence (canonical is ALWAYS Bonferroni even with FDR enabled) is enforced in both
`verify_edge` and config and proven by a DB integration test. I independently re-ran the load-bearing test
set (111 tests green across `online_fdr` / `referee` / `forward_walk` / `config` / `evidence` / the staging
routing suite incl. the two DB tests), re-derived the frozen numerics, and re-ran the gate's own regex over
the spec — all confirm the dev/review/QA claims rather than merely restating them. No critical or important
gaps; no fixes required.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (verified): Canonical byte-identical invariant holds three independent ways.**
`runs/goal-session-mcp-loop/state/certified-claims.jsonl` (`ledger.py`) is unmodified — `git status`/`git
diff HEAD` show no working-tree change and the file was last touched at the iter-8 commit. The 4 entries are
PASS/PASS/FAIL/PASS, divisors 1–4, all `deflation="bonferroni"`. Independently, `ledger.rejection_offsets()`
on the live file returns `[1, 2, 4]` and `count_trials()` returns `4` (derived, nothing rewritten). The
`test_evidence.py` golden byte-matches lines 3–4 (`required_p`, `deflation_divisor`, reason strings) and
asserts `proven_signals` keys == `["leadership_score"]` across four scenarios. DoD #1 met.

**B2 — OBSERVATION (verified): Defaults reproduce today, proven by unedited tests.**
`referee.py` makes deflation an injectable `RefereeState.deflation`/`test_level` policy with `test_level is
None` ⇒ `required_p = alpha_per_test / n_trials` and the exact `alpha/{divisor}=…` reason bar. Decisive
evidence: `git diff HEAD` for `tests/test_referee.py` and `tests/test_forward_walk.py` is EMPTY — they were
not edited — and both pass green (part of the 100-test run). An unedited suite passing is the strongest
possible proof the default path is byte-identical. DoD #2 met.

**B3 — OBSERVATION (verified): `online_fdr.py` is pure and deterministic; numerics are frozen and exact.**
`grep` finds no `random`/`np.random`/`time`/`datetime`/`now`/`uuid`/`os.urandom` in the module; a 3-run
runtime check yields one unique value. `test_level(1, [])` == `0.010937254144361815` and `test_level(5,
[1,2,4])` == `0.027669279357088947` reproduced exactly; the ζ(1.6) normalizer == `2.285765665680135`
(matches the true Riemann zeta to 1e-12). The `lru_cache` on `_gamma_normalizer` is pure memoization of a
deterministic map (key = `(exponent, n_terms)`), not a determinism risk. DoD #3 met.

**B4 — OBSERVATION (verified): Staging is isolated and routed; the honesty fence holds under FDR-enabled.**
`verify_edge` (`tools.py`) computes `use_fdr = ledger == LEDGER_STAGING and fdr_cfg.enabled`, so canonical
NEVER runs FDR regardless of config. The two DB integration tests pass (138s): a staging-routed claim writes
staging only (canonical file stays absent), and with `fdr.enabled=True` the staging claim is judged at the
LORD++ level while the canonical claim is still `deflation="bonferroni"`, `required_p == 0.05/1`. `verify_edge`
remains the sole certification writer (the only other `append_entry` caller, `forward_walk.py`, writes
`type=forward_walk` monitoring rows that `count_trials`/`alpha_spent`/`rejection_offsets` all exclude — an
iter-1-era arrangement, not a new write path). DoD #4 met.

**B5 — OBSERVATION (verified): No staging leak to any endpoint.**
`engine/evidence.py` `resolve_ledger_path()` reads `config.evidence.ledger_path` (canonical) only, and
`build_evidence_payload` reads the passed canonical path. `grep` finds zero references to
`staging_ledger_path`/`STAGING_LEDGER_PATH` in `evidence.py`, routers, or the API layer — the staging ledger
is genuinely internal and never served, so `GET /api/evidence` and every "Proven" badge stay byte-identical
(anti-goal #1/#4 honesty constraint upheld).

**B6 — OBSERVATION (verified): Config is default-off, validated, and fail-loud.**
`config.py` `FdrCfg` defaults `enabled=False` and validates `alpha∈(0,1)`, `w0_fraction∈[0,1]`,
`gamma_exponent>1`, `gamma_terms>=1`; `load_config` wraps a Pydantic `ValidationError` into `ConfigError`
(line 2271–2272). `config.yaml` restates `evidence.staging_ledger_path` + the `fdr` block (`enabled: false`,
tunables matching the FdrCfg defaults). `test_config.py` adds four real tests (real-config default-off,
omitted-block backward-compat, tunable validation, malformed-block→`ConfigError`). Minor note: `FdrCfg` uses
`extra="allow"` (codebase-wide convention), so a MISSPELLED sub-key (e.g. `alpah`) is silently accepted as an
extra field and the real tunable keeps its safe default — never a *weaker* value, and confined to staging.
Not a defect; noted for completeness.

### Frontend Findings

**F1 — N/A: No frontend surface exists or should exist this iteration.**
`Frontend Present: no`. Zero `apps/frontend/**` changes; a user-visible change would have been a defect. The
"no visible delta by design" requirement is satisfied precisely because canonical `/api/evidence` is
byte-identical (B1/B5).

### Test Findings

**T1 — OBSERVATION (verified): Tests are tight, not loose.**
Assertions pin exact frozen levels (`abs=1e-15`), byte-for-byte verdict reproduction
(`fdr_rescore[0]["verdict"] == fdr.to_dict()` for both Bonferroni and LORD++ policies), exact policy names,
and the gate's fail-closed routing (unrecognized value AND unset path). The `test_injected_test_level_...`
case flips PASS↔FAIL on the same data/seed purely by the injected bar — proving the policy is the only moved
variable. Independently re-ran: 100 passed (online_fdr+referee+forward_walk+config+evidence), 9 passed (non-DB
routing), 2 passed (DB honesty-fence).

**T2 — OBSERVATION (documented, unrelated): One pre-existing timing flake in an untouched module.**
The full-suite run (per handoff) reports `1285 passed, 1 failed`: `test_data_manager_jobs_pipeline.py::
test_backfill_speedup_factor_in_backend_stages_payload`, a wall-clock speedup assertion against a 1e-6
tolerance that passes in isolation. `data_manager` is absent from `changed_files` and from the iter-9 diff,
so this is not an iter-9 regression. It is a flaky assertion in unrelated code — a standing known limitation,
not a blocker for this backend-infrastructure iteration.

**T3 — OBSERVATION (verified): Gate pass-through confirmed with the gate's own regex.**
The spec contains the string "## Evidence Claim" only mid-line in prose (lines 44, 117), never as an
`^## Evidence Claim` heading. Running the gate's exact `_CLAIM_SECTION`/`_JSON_FENCE` regexes over the spec
yields 0 sections and 0 claims ⇒ `exit 0` pass-through. iter-9 ships no Evidence-Claim block by design, so it
cannot tighten the canonical Bonferroni bar. DoD #9 met.

---

## 3. Domain Assessment

The domain logic is correct and honest. The core design insight — Bonferroni tightens permanently so a
sustained search eventually cannot certify anything, whereas LORD++ replenishes alpha-wealth from prior
rejection times — is implemented faithfully: `α_t = W₀·γ_t + (α−W₀)·γ_{t−τ₁} + α·Σ_{j≥2} γ_{t−τⱼ}` with the
normalized polynomial spending sequence `γ_j = j^{-p}/ζ(p)`. Wealth is reconstructed purely from rejection
ordinals (zero migration, no stored budget), which is exactly what makes the module pure and the forward-walk
reproduce-contract tractable (a staging entry pins `test_level` to its recorded `required_p`; re-deriving from
the now-larger ledger would move the bar). The statistical-honesty posture is preserved end-to-end: FDR
controls the false-discovery *rate* and is weaker than family-wise control, so it is fenced to staging and
default-off, and the user-facing "Proven" badge keeps its strict Bonferroni guarantee. The `deflation_divisor`
field records the trial ordinal in FDR mode (not a literal divisor), but the verdict is unambiguously labeled
`deflation="lord++"` and `required_p` carries the true bar, and this only ever lives in the staging file — a
harmless audit-trail nuance, not a correctness issue. Determinism and no-lookahead are untouched (the referee's
sealed-holdout / purge-embargo procedure was not modified on the default path).

---

## 4. Fixes Applied During This Audit

None. Every DEFINITION OF DONE item and load-bearing invariant verified true on first inspection; no critical
or important issue found, so no source change was warranted. (OBSERVATION-level notes above are documentation,
not defects.)

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes required |

---

## 5. Recommended Next Step

**Proceed.** iter-9's Part A (sustainable trial economy) is complete, correct, and safely fenced. The staging
ledger + LORD++ economy are ready for iter-10 to open the scan aperture (Part B): explore non-20 horizons in
staging and promote one winner to canonical (with an explicit `"ledger":"canonical"` key) to surface J-07,
then a pre-registered 2-factor combination for J-08. One reminder for those authors, already documented in the
spec (lines 44/117): a claim intended for the user-facing badge MUST set `"ledger":"canonical"` explicitly —
the gate default is now `staging` (the conservative direction: a forgotten key means "not shown as proven",
never "wrongly proven"). Separately, the standing `data_manager` timing flake (T2) is worth a tolerance widen
in a future untouched-module cleanup, but it does not gate this iteration.
