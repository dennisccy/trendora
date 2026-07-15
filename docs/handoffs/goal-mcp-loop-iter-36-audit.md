# goal-mcp-loop-iter-36 Audit Report

**Date:** 2026-07-15
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-22 (backlog B-102) — the 4th and final Research "Governance & process" surface — is genuinely delivered: an isolated, deterministic referee-calibration harness (`app.engine.referee_audit`), a config block, `GET /api/research/referee-audit`, and the `/research/referee-audit` page (6 states) with a 4th governance nav card. The **dominant failure mode is controlled**: I independently confirmed `git diff HEAD` on `certified-claims.jsonl` / `staging-ledger.jsonl` / `pre-registrations.jsonl` is byte-identical, and the isolation holds *by construction* (`certify_edge` is pure — no I/O, no ledger write, no budget mutation — and the harness writes only a caller-supplied throwaway path and never imports the real ledger resolvers). No CRITICAL or IMPORTANT defect survived verification. Three GAPs and two OBSERVATIONS are documented below — most notably that the persisted report artifact is left git-untracked while its four sibling governance artifacts are committed, and that the tripwire fires on a tautological factor no out-of-sample test can catch (a spec-sanctioned, honestly-disclosed outcome whose panel prose slightly overstates the risk).

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap): the report artifact is git-untracked while every sibling governance artifact is committed**
`runs/goal-session-mcp-loop/state/referee-audit-report.json` is untracked (`git status` → `??`), yet the exact artifact the dev claims to mirror — `runs/goal-session-mcp-loop/state/drift-report.json` (iter-35) — **is committed**, as are all three real ledgers and every other `.json`/`.jsonl` in that state dir. The panel reads this artifact verbatim; on a fresh checkout (or after the working tree is cleaned) the file is absent, so the page renders the honest **empty state** ("No audit run yet") instead of the real 200-trial calibration until someone re-runs `python -m app.engine.referee_audit`. This does not fail any DoD item (browser-qa saw the real artifact in *this* working tree) and it degrades honestly, so it is not CRITICAL/IMPORTANT — but the phase's claimed "product surface delta" (the certifier's calibration is now disclosed) does not survive a clean checkout. **Recommendation for the release/showcase step:** `git add` the report artifact alongside its committed siblings if the calibration is meant to persist. Not fixed here — committing a runtime data file is a release decision, and the dev explicitly declared it "not source, git-untracked."

**B2 — GAP (gap): contaminated assembler materializes all horizon-5 forward returns; the cohort-date bound is applied in Python, not SQL**
`_default_contaminated_assembler` (`referee_audit.py:413-438`) runs `select(...).where(ForwardReturn.horizon == horizon)` then `session.exec(stmt).all()`, and only *afterwards* skips dates not in `cohort_dates` (`referee_audit.py:423`). So the SQL loads the entire horizon-5 slice of `forward_returns` (dev handoff cites ~597K rows across horizons; the kept split here is cohort_n 11 354 + control_n 103 510). The dev handoff and blueprint both claim "NO unbounded whole-table ORM load," which is slightly overstated: it is a horizon-sliced full materialization with the date bound in Python. **Why this is only a GAP, not the CRITICAL anti-goal #8 it appears to touch:** the anti-goal's harm model is "crash an existing page / exhaust a *service's* memory," and I confirmed by grep that `run_referee_audit` and the assemblers are reachable **only** from `_main()` (the offline CLI) — never from the endpoint (which calls only `read_referee_audit_report()`) or any page. It runs once, offline, bounded to one horizon, at a modest row count. No serving process or page can trigger it. Pushing `ScannerRun.asof_date.in_(cohort_dates)` into the SQL `WHERE` would make it strictly bounded; left as a note, not fixed (offline/once, not a regression risk, an optimization the spec did not require).

### Frontend Findings

**F1 — GAP (gap): the tripwire's interpretive prose overstates an unavoidable limitation**
The real offline run certified the lookahead-contaminated factor **PASS** (p=0.0005), so `contaminated_caught=false` and the red `TripwireCard` renders (`page.tsx:227-254`), stating: *"the certification harness may be leaking signal it should not — treat every certified claim from this basis with suspicion."* The contaminated factor is constructed as *selection on the outcome* — cohort = the top decile of stocks ranked by their own realized forward return each date (`referee_audit.py:427-437`). This is a tautology present identically in-sample and in the holdout, so **no temporal-holdout test can reject it** — the referee is not "leaking," it is meeting a fundamental limit of out-of-sample testing against circular labeling. The dev disclosed this honestly (dev handoff Known Issue #2). This is **not misleading UI in the state-mismatch sense** — the displayed numbers all match the engine (verdict PASS, p=0.0005, cohort/control counts), and the DoD explicitly accepts "the panel renders a prominent red tripwire failure state" as a passing branch — so it is spec-sanctioned and cannot fail the phase. But the *conclusion* the prose draws ("treat every certified claim with suspicion") is stronger than the finding warrants, since no real certified claim is constructed circularly. **Owner call (not fixed — refining it contradicts the spec's explicit "expected: rejected" label and design):** either construct the contaminated factor as a *true temporal-boundary leak* the referee's purge/embargo can actually catch, or soften the prose to name the real (unavoidable) limitation rather than implying a harness defect.

### Test Findings

**T1 — OBSERVATION (observation): three of the four non-tripwire frontend states were not live-browser-verified**
The frontend handoff admits (and QA's TC-13/TC-14 notes confirm) that the honest-empty, unreadable, calm-caught, and backend-down states were **not** exercised in a live browser — only the tripwire (real-data) state was. Coverage for the other states is API-layer unit tests (`test_api_referee_audit.py` proves missing→`null`, corrupt→`unreadable`, FAIL-fixture→caught) plus `tsc` type-checking plus "mirrors a proven sibling pattern." Low risk (the branches are simple conditional renders), but the DoD's Testing Requirements list all four states as browser targets, so this is a real coverage gap. Not fixed — live fixture exercise is browser-qa's lane.

**T2 — OBSERVATION (observation): dev handoff still miscounts the test file**
Dev handoff line 74 says "41 tests" for `test_referee_audit.py`; the actual count is **34** (`grep -c '^def test_'` = 34; + 5 in the API file = 39, matching the run). The reviewer flagged this (MINOR) and QA claimed it was corrected, but the "41" at line 74 remains. Immaterial to behavior; noted for handoff honesty.

---

## 3. Domain Assessment

The core domain logic is sound and, in its isolation discipline, genuinely careful.

**Isolation (the dominant failure mode) is correct by construction, not just by observation.** `certify_edge` (`referee.py:327-486`) is a pure function: it reads a frozen `RefereeState`, draws from a seeded RNG, and returns a `Verdict` — it performs no ledger write and no budget mutation. `run_referee_audit` calls it directly (never `verify_edge`, the writer), always with a fresh `RefereeState(n_trials=1, alpha_budget_remaining=DEFAULT_ALPHA_BUDGET)`, and appends verdicts only to the caller-supplied throwaway `ledger_path`, which it deletes-and-recreates each call so it never accumulates. The module contains no reference to `evidence.resolve_ledger_path` or `graveyard.resolve_staging_ledger_path` — there is *no code path* to the real files. The test `test_run_referee_audit_writes_only_the_throwaway_ledger_never_the_real_files` reads all three real files before/after and asserts byte-identity; I independently re-confirmed the same via `git diff HEAD`.

**The calibration measurement is honest.** 16/200 null trials false-passed (rate 0.08, Wilson 95% CI [0.04984, 0.12599]); the configured α=0.05 sits (just) inside that CI's lower edge, so the empirical rate is statistically consistent with α — the certifier is calibrated within sampling noise, and the panel discloses the rate + CI vs α exactly. The choice of the Wilson interval over Wald is well-justified (Wald degenerates to [0,0] at zero successes) and hand-verified in a tight 1e-12 test. Each null trial correctly uses `required_p = alpha/1` with `deflation_divisor == 1` (asserted per-entry), so the rate is genuinely comparable to the α the panel shows it against — not silently Bonferroni-deflated by an accumulating count.

**Determinism is real and tightly tested.** Same seed → exact dict equality (`assert report_a == report_b`), and the contaminated FAIL/PASS tests use zero-variance flat observations so the referee verdict is analytically seed-invariant rather than RNG-fragile. The whole harness is DB-free when assemblers are injected; the two DB-backed assembler tests use a tiny in-memory SQLite fixture, never the 30-year seed (39 tests run in 0.72s — the DoD's "fast seeded CI test in seconds" is met).

**No proven-language, correct badge discipline.** The page maps even a contaminated PASS to the `danger` badge variant, never `accent` (`page.tsx:149-153`), upholding anti-goal #1 — a PASS on the perfect-crime factor is alarming, not proof. The only "Proven" strings on the page are comments enforcing the prohibition.

The one substantive domain reservation is F1: the contaminated construction tests circular labeling (selection on the outcome), which the referee's temporal-holdout machinery is structurally unable to catch, so the tripwire is a permanent-red state whose prose reads as a harness indictment. It is honest about *what happened* (a PASS on a tautology) but stronger than warranted about *what it means*.

---

## 4. Fixes Applied During This Audit

None. Every finding is GAP- or OBSERVATION-level. Per the auditor mandate, GAPs and OBSERVATIONS are documented, not fixed:
- B1 (committing a runtime data artifact) is a release action beyond surgical scope and contradicts the dev's explicit design choice;
- B2 is an offline-only, non-serving efficiency note the spec did not require solving;
- F1 would require contradicting the spec's explicit "expected: rejected" contaminated-factor design — an owner decision;
- T1/T2 are for the browser-qa and reviewer lanes.

No CRITICAL or IMPORTANT issue was found, so no surgical fix was warranted.

---

## 5. Recommended Next Step

**Proceed.** J-22 achieves its goal: the governance cluster is complete (registry + graveyard + budget + referee-audit, 4/4), and the certifier now has an isolated, deterministic, byte-identity-proven calibration surface. Before/at the showcase-commit step, address **B1** — `git add` the `referee-audit-report.json` artifact next to its committed siblings so the panel shows real calibration on a clean checkout rather than the empty state. Route **F1** (refine the contaminated construction to a catchable temporal leak, or soften the tripwire prose) and **B2** (push the date bound into SQL) to the sanctioned B-204 referee-settings-sweep follow-on that "shares this harness." The next iteration can proceed to the risk-analytics cluster (J-23/J-24/J-25) per the one-risky-journey-per-iter rule.
