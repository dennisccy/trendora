# goal-mcp-loop-iter-32 Audit Report

**Date:** 2026-07-14
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal is genuinely achieved: the certification-budget accounting panel (J-17 / B-903) is a
pure read-compose surface that re-reads the exact `ledger` / `online_fdr` / `referee` seams
`app.mcp.tools:verify_edge` uses — I traced the single-source claim to the source and it holds, not
merely because the tests pass but because the derivations are byte-identical to `verify_edge`'s own
(`tools.py:509-528`). J-19 flips partial→passing on concrete canonical browser-qa evidence
(`UT-11`: scrollY=154, target row rect top=79.5), the real ledgers are byte-identical, and no
proven-language leaks onto the panel. The gaps are all GAP/OBSERVATION-level: the spec-listed
required-still-passing journey **J-11 was not independently re-verified this iteration** (nil risk —
the diff is purely additive and the ledger has zero PASS edges, so J-11's invariant is trivially
upheld — but it is a real coverage gap the ux-regression reviewer already flagged), plus two latent
single-source/formatting observations. **No CRITICAL or IMPORTANT issue was found; no fixes were
required.**

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (observation): staging `next_level` calls `online_fdr.test_level` unconditionally, not mirroring `verify_edge`'s `use_fdr` gate**
`budget_accounting._staging_section` (`apps/backend/app/engine/budget_accounting.py:116-123`) always
calls `online_fdr.test_level(...)`. `verify_edge` gates the identical call on
`use_fdr = ledger == LEDGER_STAGING and fdr_cfg.enabled` (`tools.py:519-534`) and falls back to
strict Bonferroni when `evidence.fdr.enabled` is false. Today `config.yaml:1083` sets
`fdr.enabled: true`, so `verify_edge` *does* take the LORD++ branch for a staging claim and the panel
matches the referee exactly (confirmed by `test_staging_single_source_against_live_ledger`, which
derives the expected level through the same seam and asserts equality). The mismatch is latent —
it would only surface if `fdr.enabled` were toggled off, which this iteration does not touch and the
spec itself specified the unconditional call shape (IN SCOPE / Data-contract additions). Matches the
reviewer's NOTE. Not fixed: fixing it would diverge from the spec's own stated call shape and is
out of scope. Worth mirroring the gate in a future iteration only if `fdr.enabled` ever becomes
toggleable at runtime.

**B2 — OBSERVATION (observation): `count_trials` counts a non-dict ledger line but `_spend_over_time` skips it**
`ledger.count_trials` treats a non-dict entry as a real trial (`_is_forward_walk` returns False for a
non-dict, so `not _is_forward_walk` counts it — `ledger.py:63-68`), whereas
`budget_accounting._spend_over_time` skips any non-dict entry (`budget_accounting.py:72`). If a ledger
line were a bare JSON scalar/array, `len(spend_over_time) != count_trials` (the DoD/`test_spend_over_
time_length_equals_count_trials_*` invariant). This is unreachable through the real write path —
`ledger.append_entry` only ever serializes dict contexts (`tools.py:555`) — so every committed ledger
line is a dict and the invariant holds on all real and fixture ledgers. `count_trials` is pre-existing
and untouched this iteration. Noted for completeness only; not a fix (not reachable, not this
iteration's code).

### Frontend Findings

**F1 — OBSERVATION (observation): staging `next_level` rendered through `formatPValue`, which floors at "< 0.0001"**
The staging card renders `formatPValue(staging.next_level)` (`budget/page.tsx:126`); `formatPValue`
returns the string `"< 0.0001"` for any positive value below 1e-4 (`lib/evidence.ts:190-200`). Today
`next_level ≈ 0.0003926` is above the floor and displays precisely (verified in `UT-05`), and the
canonical `required_p` (0.00625) is far above it. If the staging economy ever depletes its next-trial
level below 1e-4, the card would show `"< 0.0001"` rather than the exact figure. This is honest
(not a recompute, not a wrong number — the same truncation `/evidence` uses for p-values) and
consistent with the panel's descriptive-accounting framing, so it is not a byte-match violation in
any realistic near-term state. Noted, not fixed.

**F2 — GAP (gap): the required-p / staging headline figures are format-transformed, not raw-string byte-identical**
`required_p`/`next_level` are displayed via `formatPValue` and `alpha_*` via a local `formatAlpha`
(`budget/page.tsx:92-96, 112-128`). The DoD's "displayed figures byte-match the payload" is satisfied
in the value sense (each figure reads the *served* field — no UI-recompute; the required-p headline
uses `canonical.required_p`, and the "= 0.05 ÷ 8" subtext is built from served `alpha_per_test` /
`n_trials_next`, never a hardcoded literal — `page.tsx:112-114`), and the browser-qa cross-checked
each rendered value against the live payload (`UT-05`, byte-verified). The transformation is display
formatting only, exactly what the test plan's TC-09 pass criteria allow ("formatted consistently").
Recorded as a GAP only to be explicit that "byte-match" here means value-equivalence after a pure,
non-recomputing formatter, not literal string identity. No action needed.

### Test Findings

**T1 — GAP (gap): required-still-passing journey J-11 has no test entry this iteration**
The spec lists J-11 ("Every displayed 'Proven' edge is re-certified on the new 30-year data — no
stale edge survives") among the required-still-passing journeys (spec DEFINITION OF DONE line 90;
TESTING REQUIREMENTS), but neither the QA test plan (TC-11…TC-14 cover J-18/J-05/J-01/J-06/J-08/J-09)
nor the browser-qa results (`UT-12`…`UT-14`) exercise J-11 by replay or browser. The ux-regression
reviewer independently flagged this (`...-ux-regression.md:49-56`). Risk is genuinely nil: (a) the
diff is purely additive and touches no surface J-11 depends on (no edit to `referee.py` / `ledger.py`
/ `online_fdr.py` / `forward_walk` / `evidence`, only read-only imports), and (b) the current ledger
is 0-PASS / 7-FAIL, so there are no "Proven" edges to go stale — `UT-13`/`UT-14` confirm 0 "Proven"
badges anywhere — making J-11's invariant trivially satisfied. Not fixed: a J-11 re-verification needs
a browser session (unavailable to this agent) and would be disproportionate to the nil risk. This is
the sole reason the verdict is PASS_WITH_GAPS rather than PASS.

**T2 — OBSERVATION (observation): two real-ledger tests hardcode the "7 trials / all-FAIL" plateau snapshot**
`test_real_ledger_spend_over_time_all_fail_today_matches_plateau_note`
(`test_budget_accounting.py:99-105`) asserts `len == 7` and `status == "FAIL"` for both series. This
is a snapshot assertion tied to the frozen plateau state; it is acceptable because this iteration
guarantees the ledgers are byte-identical (a new claim is out of scope), and the sibling single-source
tests are status-derived (`count_trials(...)`, not a bare `7`). It will need updating when a future
claim is appended. Noted, not a defect.

---

## 3. Domain Assessment

The core domain logic is correct and, more importantly, **single-sourced** — the load-bearing
acceptance for B-903 (whose named failure mode is "UI-recompute"):

- **Canonical bar.** `required_p = DEFAULT_ALPHA_PER_TEST / n_trials_next` with
  `n_trials_next = count_trials(canonical) + 1` (`budget_accounting.py:94-101`) reproduces
  `verify_edge`'s `n_trials = prior_trials + 1` → referee `required_p = alpha_per_test / max(1,
  n_trials)` (`tools.py:509-512`, `referee.py:47`). Because `n_trials_next ≥ 1` always, `max(1, ·)` is
  a no-op — no divergence. The constant is imported, never a literal (verified: the only `0.05` in the
  module is in docstrings). Today: `0.05 / 8 = 0.00625`, matching the live panel and `UT-05`.
- **Thresholdout remaining.** `DEFAULT_ALPHA_BUDGET - alpha_spent(canonical)` (`budget_accounting.py:104`)
  is byte-identical to `verify_edge`'s `remaining` at `tools.py:510-511`. Today: `1.0 - 0.1 = 0.9`
  (two 0.05 charges in the real ledger), matching `UT-05`.
- **Staging LORD++ level.** `online_fdr.test_level(n_trials_next, rejection_offsets(staging), <config
  tunables>)` (`budget_accounting.py:116-123`) is the identical call `verify_edge` makes
  (`tools.py:521-528`) — same ordinal, same rejection-offset history, config-sourced tunables only.
  The single-source test derives the expected value through the same seam and asserts exact equality.
- **Spend-over-time.** History is *read*, never recomputed: each point re-emits the entry's own
  recorded `verdict.required_p` / `deflation_divisor` / `alpha_charged` verbatim
  (`budget_accounting.py:61-86`), with the same forward-walk exclusion the ledger aggregates use. The
  only computed figures are the two forward next-trial bars, via the shared functions above. `UT-06`
  confirms 7 non-null plotted points per series (so the staging verdicts do record `required_p`), and
  `UT-08` confirms the Thresholdout sparkline's two discrete spend events match the payload's
  `alpha_charged = [0,0,0,0,0.05,0,0.05]` exactly.
- **Resilience.** Missing/empty ledgers degrade to an honest zero/empty snapshot with no special-casing
  (`test_missing_ledgers_degrade_...`, `test_empty_ledger_files_...`), the endpoint returns 200 not 500
  (`test_api_budget.py:26-37`), and the all-FAIL path depletes the staging level monotonically with no
  replenishment (`test_all_fail_ledger_...`, strict `later < earlier`). The module is pure filesystem
  I/O over small append-only JSONL — no ORM, no whole-table load (anti-goal on data-scale upheld).

Test quality is high: assertions are tight and hand-computed (`required_p == 0.05/4`, `0.05/5`;
`charges == [0.0, 0.05]`; `alpha_spent == 0.05`), the fixture-spend uses a throwaway `tmp_path` ledger
and a dedicated test asserts the real ledgers are byte-identical before/after
(`test_fixture_spend_never_writes_the_real_ledgers`), and the endpoint↔module equality test
(`test_budget_endpoint_equals_build_budget_payload_directly`) closes the UI-recompute gap end-to-end.
I re-ran the 20 backend tests independently: **20 passed in 0.32s**. Git confirms the three real
ledgers are byte-identical (no `git status` entry). The canonical browser-qa + ux-regression lanes
genuinely ran against the final prod build (real backend stop/restart for the error-card tests, golden
replay scripts written for J-17/J-19, an honest self-disclosed md5 scan of the evidence dir) — not a
fail-open. The one shared screenshot (`UT-03/05/06/07`) is a legitimate single page state asserted
four different ways, each independently DOM/text-verified and transparently disclosed.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT finding was identified; every finding is GAP- or OBSERVATION-level and
fixing any of them would be scope creep (B1/F1/F2 are spec-conformant display/derivation choices; B2/T2
are unreachable/acceptable; T1 needs a browser session and carries nil risk). Per the auditor rules,
GAPs and OBSERVATIONs are documented, not fixed.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied |

---

## 5. Recommended Next Step

**Proceed.** J-17 lands `passing` and J-19 flips `partial → passing` on genuine canonical browser-qa
evidence; the single-source acceptance is verified at the code level; the real ledgers, divisor (8),
and proven-badge surface are all untouched. The one gap worth carrying forward is a **one-line
addition to a future test/replay pass**: re-verify **J-11** (via golden replay against the current
0-PASS ledger, cheaper than a browser session) so the required-still-passing set is fully closed
rather than 6-of-7 — its risk is nil this iteration but it should not silently accumulate. Per the
iter-31 evaluator, the best next risky target remains **J-20** (daily preflight verdict, B-301) or
**J-22** (certifier-audit, B-102, the fourth governance surface); the fdr-gate mirroring in B1 is only
worth doing if `evidence.fdr.enabled` ever becomes a runtime toggle.
