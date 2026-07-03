# Iteration 17 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

Iter-17 completed the staged 30-year seed's index/macro context (§H) exactly as specced, with zero runtime change: `_SPX`/`_NDX`/`_DJI` staged deep from Stooq's local world bundle (7,674 bars each, 1996-01-02 → 2026-07-01, 1789-era rows provably clipped), `_VIX` staged deep from a live Yahoo pull (7,675 bars, max |Δ|=0.0 vs the live series on all 1,357 overlap dates — evaluator-reproduced), and `_TNX`/`_DXY`/`_VXN` preserved as byte-identical FRED-macro-proxy copies (`cmp`-verified). The swap-completeness gate (staged 590 ⊇ live 162) is a committed passing test this evaluator re-ran green (12/12). No journey flips by design (enablement, iter-9/10/12/16 lineage); J-14 becomes newly tracked `unknown` with its step-1 data basis delivered into the staged asset. The iter-16 STALLED rationale is fully dissolved — iter-18 (the atomic swap + sanctioned ledger reset) is dispatchable unattended.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing (byte-identity carry) | `git diff HEAD` empty on `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, `data/seed/**`, both ledgers (7+7 rows — evaluator-verified); unedited DoD suites green (64 passed, run independently by reviewer AND QA); last pixel iter-15 `reports/qa/goal-mcp-loop-iter-15-evidence/TC-06-stocks-no-regression.png` |
| J-02 | passing | passing (byte-identity carry) | same channel; last pixel iter-15 `UT-01-initial.png` |
| J-03 | passing | passing (byte-identity carry) | same channel; last pixel iter-15 `UT-01-initial.png` |
| J-04 | passing | passing (byte-identity carry) | same channel; ledger row 2 byte-identical |
| J-05 | passing | passing (byte-identity carry) | same channel; `certified-claims.jsonl` exactly 7 lines, 0-diff (evaluator-verified) |
| J-06 | passing | passing (byte-identity carry) | same channel; ledger row 4 byte-identical |
| J-07 | passing | passing (byte-identity carry) | same channel; ledger row 5 byte-identical |
| J-08 | passing | passing (byte-identity carry) | same channel; ledger row 6 byte-identical |
| J-09 | passing | passing (byte-identity carry) | same channel; ledger row 7 byte-identical (+21.34% yellow flag carried — faces honest re-certification at iter-18) |
| J-10 | unknown | unknown (BLOCKER RESOLVED; staged data basis now exists + swap-complete; surfacing sequenced at/after iter-18) | staged tree 590 CSVs; `test_seed_staged_30y.py` 12/12 (evaluator re-run); `reports/phase-goal-mcp-loop-iter-17-seed-coverage.md` "Swap-complete: YES" |
| J-11 | unknown | unknown (unbuilt by design — the sanctioned ledger reset IS iter-18) | both ledgers byte-identical this iteration (zero referee submissions, deliberate) |
| J-12 | unknown | unknown (unbuilt by design — pool broadening + staleness gate sequenced into iter-18) | — |
| J-13 | unknown | unknown (unbuilt by design — post-swap Data Manager work) | — |
| J-14 | — (new) | unknown (newly tracked; step-1 data basis DELIVERED into the staged asset — deep vendor-disclosed index/macro context; steps 2–3 are post-swap surfacing) | staged `meta.json` vendor records (stooq ×3 / yahoo ×1 / fred-macro-proxy ×3 — evaluator-verified); proxy disclaimer present exactly once; window pins unchanged 1996-01-01 → 2026-07-01 |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No unbacked "proven" presentation | OK | Zero referee submissions, zero ledger writes, zero displayed-number change (empty diff on all display paths) |
| Decision-quality only (no buy/sell/price targets/alpha) | OK | Language scan of the full diff: zero hits |
| Displayed numbers correct | OK | Nothing displayed changed; byte-identity channel |
| No overfit edges | OK | No new edge surfaced; both ledgers byte-identical at 7+7 |
| Determinism + no-lookahead preserved | OK | `apps/backend/app/**` zero-diff; staged tree read by nothing at runtime (`config.provider: seed` unchanged); no fabricated bars (pre-1996 clip verified NONE leaked; proxies byte-identical; VIX single-vendor zero-seam; SATS honestly absent) |
| No uncertified evidence-derived claims shipped | OK | Spec's Evidence Claim section: None; gate passed through automatically |
| No hard-coded credentials | OK | Secret scan of the diff: only a docstring phrase ("No key, no secret") and the PLANTED fake key `ctx-secret-key-9` inside the B1 redaction failure-path test (the test the spec required); `redact_stooq_key` choke point in place (11 refs), failure path test-exercised |

## Next-Step Recommendation

**iter-18 (FULL) — the ATOMIC basis swap + sanctioned ledger reset**, the session's highest-stakes write, now dispatchable unattended (the staged asset exists and is swap-complete; the iter-16 human-only-unblock rationale no longer holds):

1. Verify `test_swap_completeness_staged_superset_of_live` green at start (it is — evaluator re-ran it).
2. Atomically: seed-dir flip, pool-broadened `load_prices`, `resolve_candidate` recency/staleness gate (J-12), DB rebuild, bounded snapshot backfill (coarser deep-history cadence), regeneration of BOTH ledgers from scratch per goal.md "Data-basis change", frozen-golden/seed-pin test refresh (`test_evidence.py`, `test_staging_ledger_routing.py`, `test_seed_integrity.py`, `test_bar_cache.py` comment), survivorship-label span update.
3. Run the bounded, sequential FULL backend suite with real counts in the handoff (retires audit gap B1 where it is genuinely load-bearing — iter-18 changes runtime code).
4. Browser-verify the post-swap surfaces: J-10 (deep history honestly bounded per name), J-11 (no stale edge survives — no old +21.34%/+6.36%/p=0.0004998 value shown unless independently re-certified), and every J-01..J-05 badge honestly reflecting the REGENERATED ledger.
5. **Pre-registered for the iter-18 evaluator:** the sanctioned reset means J-06..J-09's SPECIFIC retired-window edges may honestly fail re-certification — per goal.md ("J-01..J-09 remain valid contracts... but their specific certified edges recompute") that is the system WORKING, not a REGRESSION; judge those journeys against the honest-badge/correct-number contract on the new basis, and let the decomposer spec how J-06..J-09 statuses map post-reset (re-propose through the gate on the new data; a non-reproducing edge correctly reads "Not yet proven").

## Halt Justification

Not applicable — verdict is CONTINUE.
