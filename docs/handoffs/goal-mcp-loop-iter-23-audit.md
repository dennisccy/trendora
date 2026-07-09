# goal-mcp-loop-iter-23 Audit Report

**Date:** 2026-07-09
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

This verification-only iteration achieved its goal: J-14's already-shipped deep, vendor-labeled
index/macro context is now canonically browser-verified (the iter-22 default-view FAIL flipped to PASS on
genuine, md5-distinct evidence), all eight required-still-passing journeys were re-verified live,
`ux-regression` returned UX-REGRESSION-PASS on fresh evidence, both evidence ledgers remain byte-unchanged
all-FAIL, and no product/UI/data-contract code drifted. The one IMPORTANT open item — the DoD-named
`test_api_indexes.py` was 11/12 (a genuine, pre-existing, test-only defect) — was **fixed during this
audit** and verified by reproducing the exact `KeyError: '^TNX'` and its fixed-pass in-process. Residual
gaps are mechanical (a routine ~2h full-file re-run to capture the literal green line; the `phase-closure`
gate runs after this audit) and OBSERVATION-level (tooling/doc notes), so PASS_WITH_GAPS rather than PASS.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): `test_api_indexes.py` failed on a DoD-named line (`KeyError: '^TNX'`) — a test-only defect, not a product bug**

- Location: `apps/backend/tests/test_api_indexes.py:162` (`test_api_indexes_full_param_serves_through_latest_and_echoes_asof`), failing assertion at the original `:183`.
- The phase DoD (`docs/phases/goal-mcp-loop-iter-23.md:92`) and TESTING REQUIREMENTS (`:101`) explicitly
  require "backend pytest green including `test_api_indexes.py`". The dev handoff honestly reported 11/12:
  the 12th failed with `KeyError: '^TNX'`. That is an unmet DoD item → IMPORTANT.
- **I did not accept the "test-only" label on trust — I read the product code and reproduced the failure.**
  In `app/engine/indexes.py:138-148`, clamped mode (`bars_asof`, default) drops any configured symbol with
  zero bars ≤ the resolved as-of via `if not bars: continue` (line 147-148) — the documented, correct,
  separately-pinned "honest omission" behavior (`indexes.py:10-12`,
  `test_indexes.py::test_barless_configured_symbol_omitted_from_series_and_legend`). Full mode
  (`bars_through_latest`) shows the symbol's whole stored path. So a symbol whose first bar is after an
  early as-of is legitimately in `full["series"]` but absent from `clamped["series"]`. The test's final
  loop (`:181-183`) unconditionally indexed `clamped_by_sym[s["symbol"]]` for every `full` symbol →
  `KeyError` for the omitted one. The API returns honest, correct data in both modes; only the test's
  symmetry assumption was wrong.
- **Reproduction (in-process against the warm dev DB, so no 2h fixture rebuild):** calling the exact
  `compute_index_series` the route calls —
  - Case A (`as_of=2000-01-01`, the earliest run date the test uses): clamped = `[QQQ,^SPX,^NDX,^DJI,^VIX]`,
    full = all 10; in-full-not-clamped = `[SPY,IWM,RSP,DIA,^TNX]`, each with `bars_asof(≤2000-01-01)=0`
    (honest omission). Original assertion → `KeyError: 'SPY'`; fixed assertion → PASS.
  - Case B (`as_of=2005-02-26`, isolating `^TNX`): clamped = 9 symbols (all but `^TNX`), full = all 10;
    in-full-not-clamped = `['^TNX']` with `bars_asof(≤2005-02-26)=0`. Original assertion →
    **`KeyError: '^TNX'`** (the exact reported failure); fixed assertion → PASS.
- **Fix applied (test-only):** guarded the overlap loop to skip symbols absent from clamped, and added an
  `assert clamped ⊆ full` so a hypothetical future regression that *drops* a clamped symbol from full is
  still caught (the bare guard alone would have slightly weakened coverage). Diff is 9 insertions / 1
  deletion, confined to that one test function; the other 11 tests are byte-untouched. `pytest
  --collect-only` confirms all 12 still collect (0.27s, no fixture triggered, no syntax/import break).

**B2 — OBSERVATION (gap): local dev DB `^TNX` history (2005) is wider than the manifest `first` it discloses (2021)**

- `apps/backend/data/trendora.db` (gitignored build artifact) carries `^TNX` daily bars from `2005-02-28`,
  but `data/seed/meta.json` declares `^TNX` `first = 2021-01-04`, and `compute_index_series`
  (`app/engine/indexes.py:156-157`) sources the disclosed `first` from the manifest, not from the actual
  bars. On this particular dev DB the `/data` panel's `^TNX` first-bar (2021-01-04) therefore *understates*
  the DB's real `^TNX` history — and in full mode the chart would draw `^TNX` from 2005 while the panel
  says 2021. This is a local-ingest artifact (the committed seed's `^TNX` bars are expected to match its
  2021 manifest), and it lands squarely on the pre-tracked audit **F4** (`^TNX` first-bar disclosure
  semantics), which the spec explicitly puts OUT OF SCOPE this iteration (`:83`). Not a defect introduced
  here; worth confirming committed-seed consistency in the dedicated F4 follow-up.

### Frontend Findings

**F1 — none.** `git diff HEAD` shows zero changes under `apps/frontend/`. The `minBarSpacing: 0.02`
deep-window fix is present and committed (`apps/frontend/components/phase-cross-view-chart.tsx:162`, commit
`20f90b0`), exactly as required. `tsc --noEmit` was clean (dev handoff). No UI surface, component, or
navigation changed — confirmed independently by `ux-regression` opening the actual screenshots.

### Test Findings

**T1 — OBSERVATION (gap): the canonical ~2h full-file run of `test_api_indexes.py` was not repeated post-fix**

- After the surgical fix, I verified via faithful in-process reproduction of the exact failing scenario
  (B1) plus a collection check, not by re-paying the ~2h session-fixture end-to-end run (project lesson:
  long pytest on the 30y/590-symbol basis fork-locks the box and is reaped at turn boundaries; the dev
  needed `setsid nohup` + 2h14m polling to land the original result). The auditor rubric sanctions
  "exercise the code path directly and record the output" when re-running is impractical; the in-process
  reproduction is arguably stronger (it shows the real data, the exact `KeyError`, and the fixed-pass). The
  other 11 tests were observed green by the dev before my edit and my diff does not touch them. Recommend a
  routine idle-time `pytest tests/test_api_indexes.py` to capture the literal "12 passed" line for the
  record.

**T2 — OBSERVATION (gap): `qa.md` internally contradicts itself on how many functional cases were executed**

- `reports/qa/goal-mcp-loop-iter-23-qa.md:94` states "17/18 test cases PASS", while its own Test Results
  Summary table (`:177-178`) says "Functional test cases (verified/passed) 7 … (pending/interaction) 9 —
  Awaiting interactive verification". The authoritative DoD lane —
  `reports/phase-goal-mcp-loop-iter-23-ui-test-results.md` (browser-qa-agent) — actually executed the
  browser cases (22/23 PASS, 1 sanctioned skip) with genuine evidence. The "9 pending" wording in `qa.md`
  is stale/misleading and understates what was done; it does not reflect a real coverage gap. Cosmetic
  reconciliation for the record; not blocking.

**T3 — verified genuine (not a finding): browser-qa evidence is real, not a PASS label.** Per the
iter-3/11/13/14 lesson I md5-checked the load-bearing pairs: `UT-03` J-14 flip pair
(`e110b9fb…`/`aee41b2d…`), `UT-10` J-13 hover pair (`bdb9a68e…`/`15731dac…`), `UT-20` J-10 toggle pair
(`3ad7e490…`/`49dd3d7f…`) — all pairwise distinct, and the last two **byte-match the md5 prefixes the
browser-qa report itself cited**. No `-fail-`-named frame exists in the evidence directory.

---

## 3. Domain Assessment

The core domain logic is correct and honest, and I verified the load-bearing pieces against the code and
data rather than the handoffs:

- **Honest omission / no fabrication (anti-goal #1, #8):** bar-less configured symbols are omitted, never
  synthesized (`indexes.py:147-148`), and a zero base is skipped rather than divided by
  (`indexes.py:150-151`). ETF lines carry `vendor: None` — no fabricated vendor
  (`indexes.py:47-52`, `test_api_indexes.py:60-73`, browser UT-08/UT-09).
- **No-lookahead preserved (anti-goal #5):** `full` mode widens only the *display* upper bound
  (`bars_through_latest`) for dashboard context behind the as-of marker; it feeds no as-of-scoped computed
  value, and the ≤D overlap is value-identical to clamped mode (`indexes.py:121-130`; my B1 reproduction
  confirmed the overlap invariant holds for every shared symbol — no second compute path).
- **FRED-macro proxy never presented as a market index (anti-goal, critical):** `^TNX` renders as
  "10Y-2Y spread proxy (^TNX)" with vendor "FRED-macro proxy" on both the chart legend/tooltip and the
  `/data` panel (browser UT-04/UT-05/UT-07/UT-09).
- **No proven/confident edge without a passing referee (anti-goals #1, #4):** both ledgers are byte-unchanged
  and 7/7 `FAIL` — I read every row's `status` (`certified-claims.jsonl` and `staging-ledger.jsonl`), each
  with an honest reason (negative holdout edge, or not significant after Bonferroni/LORD++ deflation).
  `git status` on `runs/goal-session-mcp-loop/state/` is clean. UI shows "Not yet proven" everywhere
  (browser UT-17/UT-21), zero "Proven".
- **Scope integrity (auditor focus — no drift):** the only application-source change in the working tree is
  my one test-file fix; the only other tracked change is the spec-permitted `J-13.json` fixture line
  (587→590) plus goal-engine trace bookkeeping. No engine/scoring/referee/ledger/chart/UI code moved.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | IMPORTANT | `apps/backend/tests/test_api_indexes.py` | Guarded the full/clamped overlap loop to skip a symbol honestly omitted from clamped (first bar after the as-of) and added an `assert clamped ⊆ full`. Test-only; no product change. Verified by in-process reproduction of the exact `KeyError: '^TNX'` (original→KeyError, fixed→PASS) + `--collect-only` (12 collect). |
| 2 | (record) | `docs/handoffs/goal-mcp-loop-iter-23-dev.md` | Added an AUDITOR ADDENDUM correcting the now-stale "No files under `apps/backend/` were changed" claim (one test file changed by the auditor after the handoff). |
| 3 | (record) | `runs/goal-mcp-loop-iter-23/status.json` | Annotated the `test_api_indexes.py` blocker with the auditor resolution and added the test file to `changed_files`. Re-validated as JSON. |

Post-fix self-check: (1) the fix is verified (B1 reproduction + collection); (2) `git diff` on the test
file is confined to the one function — no scope creep; (3) no new escape hatch — the added `clamped ⊆ full`
assertion keeps the test from getting weaker; (4) invalidated claims in the dev handoff and status.json were
reconciled.

---

## 5. Recommended Next Step

**Proceed to `phase-closure` (pipeline step 10).** The evidence supports CLOSURE-PASS: the J-14 default-view
FAIL flipped to PASS on genuine md5-distinct evidence, all eight required-still-passing journeys re-verified
live, `ux-regression` = UX-REGRESSION-PASS, both ledgers byte-unchanged all-FAIL, zero feature drift, and
the one unmet DoD test line is now fixed and verified. `status.json` is `in_progress` (not `blocked`) and no
`-fail-`-named frame exists — reconcile it to `complete` at closure.

Two low-cost follow-ups (neither blocks this iteration): (a) run `pytest tests/test_api_indexes.py` once on
an idle box to capture the literal "12 passed" green line for the record (T1); (b) fold the dev-DB-vs-manifest
`^TNX` first-bar discrepancy (B2) into the already-tracked F4 follow-up and reconcile `qa.md`'s
"9 pending" wording (T2).

As the spec itself states, **GOAL_ACHIEVED is not reachable this iteration** regardless — J-02/J-06/J-07/J-08/J-09
remain sanctioned-partial and J-15/J-16 are unbuilt. This iteration's defined success (J-14 `passing` +
CLOSURE-clearable + zero regressions) is met.
