# goal-mcp-loop-iter-33 Audit Report

**Date:** 2026-07-14
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-20 / backlog B-301 is genuinely achieved: a single `compute_preflight` composer (worst-severity
composition over servability / freshness / DB-ledger-integrity, config-driven severity map, honest
degradation) is served additively on `GET /api/health` and rendered by one layout-level `PreflightBanner`
mounted once in `app/layout.tsx`, reading only the existing `ReadinessProvider` poll — no per-page
recompute. Browser-QA (`ui-test-results.md`, 20/20) pixel-verified the identical GO / DEGRADED / NO-GO
banner across all five required surfaces, the exact mandated phrase "do not rely on today's board", live
GO→DEGRADED update, single-source, and no nav/regression. The one DoD item the pipeline never formally
ran — the backend correctness matrix — I independently verified by exercising the real `compute_preflight`
against a lightweight servable engine (all 8 rows + config-wiring + error cases pass). Remaining gaps are
all GAP/OBSERVATION-level test-hygiene and efficiency items, none compromising the phase goal.

---

## 2. Findings

### Backend Findings

**B1 — GAP (documented, not fixed): verdict-history test isolation — no autouse redirect fixture**
`record_verdict_transition` fires unconditionally on every `/api/health` request (`app/api/health.py:64`),
writing to the config-default path `runs/goal-session-mcp-loop/state/preflight-verdict-history.jsonl`
(`config.yaml:1256`). No autouse fixture in `apps/backend/tests/conftest.py` redirects
`READINESS_VERDICT_HISTORY_PATH`, so the four other suites that hit the endpoint (`test_warmup.py`,
`test_cors_dev_lan.py`, `test_data_manager_concurrency_load.py`, and the two pre-existing `test_health.py`
tests) append to that default file during ordinary runs. Correction to the reviewer's framing: `git
ls-files` / `git check-ignore` confirm the file is **untracked** (`??`), not git-tracked — so this is
test-run noise into an untracked operational log (currently 7 dev/QA entries), not corruption of a
committed artifact. Severity GAP, not CRITICAL. Per the auditor rules GAP-level issues are documented, not
fixed. Recommended fix for the next housekeeping pass: an autouse `conftest.py` fixture pointing
`READINESS_VERDICT_HISTORY_PATH` at a session tmp path (exactly the reviewer's suggestion).

**B2 — GAP (documented, not fixed): `compute_preflight` re-invokes `compute_readiness`**
`compute_preflight` calls `compute_readiness(session, config=cfg)` at `readiness.py:238`, but `health.py`
already computed it once at `health.py:50`; so each ~2 s poll runs `compute_readiness` twice. This mildly
contradicts the "no second computation" prose in the docstrings. It is **not** an anti-goal #8 violation:
the expensive SPY-cadence derivation is memoized (`_cached_warmup_dates`, cache-hit in steady state) and
the only repeated query is the bounded, column-projected `ScannerRun.asof_date IN (cadence_dates)`
existence check (`readiness.py:146`) — no whole-table `.all()` row load is added. Deterministic and
harmless; efficiency only. Recommended (optional) fix: thread the already-computed readiness dict through
as an optional parameter.

**B3 — OBSERVATION: freshness axis is structurally always-0-days by design**
`compute_preflight` hardcodes `age_days = 0` (`readiness.py:275`) because the freshness reference *is* the
latest available bar. Consequently the freshness component can only breach when `freshness_max_age_days < 0`
(the sanctioned test lever) or when there is no price data at all — it cannot detect real staleness of a
loaded seed. This is exactly the deterministic-reference reading the spec's NOTES chose (offline frozen
seed, no wall-clock — anti-goal #5) and B-301's "ship with whatever inputs exist" directive; real staleness
signals are the deferred B-113/B-304/B-103 monitors. Correct within scope; noted so the next reader knows
the freshness axis is presently a config/no-data detector, not a live-age signal.

### Frontend Findings

**F1 — OBSERVATION: banner is well-typed and single-source; no material issue**
`lib/api.ts:147` types `preflight: PreflightStatus` (required, non-nullable) and `health.py:94` always
returns the field (including the exception fallback at `health.py:68`), so `preflight-banner.tsx`'s
`preflight === null` / verdict branches cannot hit an `undefined.verdict`. GO uses the quiet
`border-pos/40 bg-pos/5 text-pos` strip; DEGRADED/NO-GO the loud `--warn`/`--neg` banners; NO-GO carries the
exact phrase verbatim (`preflight-banner.tsx:77`); loading and failed-poll both render honest non-GO states.
No buttons/forms (anti-goal #2). Clean.

### Test Findings

**T1 — GAP (substantive risk closed by the auditor): 18-of-25 backend tests never formally run in-pipeline**
Dev, review, and QA all disclose that the 18 `loaded_engine`-dependent tests in `test_readiness.py` /
`test_health.py` (the correctness matrix, config-wiring, single-source, `compute_readiness` byte-identity,
error cases, health additive-shape) were never confirmed through pytest — the 30-year shared fixture runs
30–60 min and each attempt timed out. The tests themselves are **well-designed**: `test_preflight_fixture_
matrix` (`test_readiness.py:91`) drives all 8 `{servability, freshness, integrity}` combinations with tight
exact-value assertions on verdict, per-component `ok`, and reasons content — not a smoke check.
**Auditor mitigation:** I exercised the real `compute_preflight` production function against a lightweight
*servable* engine (one `DailyPrice` + one `ScannerRun` ⇒ `state != unavailable`) substituted for
`loaded_engine` — the only property those rows need from it. All 8 matrix rows, the severity-map wiring
test, the `compute_readiness` shape-unchanged check, and the DB-unreachable + unparseable-ledger error
cases reproduced the exact expected verdicts (evidence in §4). The 8 non-`loaded_engine` tests were also run
through pytest directly (`8 passed in 0.33s`). The substantive correctness risk is therefore closed; only
the canonical in-pipeline pytest confirmation of those 18 remains outstanding as a formality (recommend the
replay/CI lane background it per the dev's own action note).

**T2 — OBSERVATION: QA report TC-29 prose overclaims the freshness calendar usage**
`goal-mcp-loop-iter-33-qa.md` TC-29 states `compute_preflight` "uses ... the SPY trading-day calendar" for
freshness. It does not — age is hardcoded 0 against the latest-data reference (see B3). The behavior is
correct per the chosen deterministic reading; only the QA prose is imprecise. No code impact.

---

## 3. Domain Assessment

The core domain logic is correct and faithful to B-301's single-source discipline:

- **Composition:** `_apply` records every component's `{ok, severity, detail}` and escalates `verdict` to
  the worst breached component's *configured* severity via `_VERDICT_RANK` — GO only when nothing breaches.
  Verified across all 8 input combinations: single breaches map to their configured severity
  (servability/integrity → NO-GO, freshness → DEGRADED), and multi-breaches take the worst. Config-wiring
  test confirms the same freshness breach flips DEGRADED↔NO-GO purely by re-pointing the severity map — no
  hardcoded verdict logic.
- **Single source:** `compute_preflight` is the sole producer (one call site, `health.py:60`), served only
  on the existing `/api/health`; the banner reads only `useReadiness()`. Browser UT-19 confirmed exactly one
  banner element and no duplicate fetch. `compute_readiness`'s `state`/`warmup` contract is untouched
  (byte-identity check passed; J-40 not regressed).
- **Honest degradation (anti-goal #8):** DB-unreachable → NO-GO with all three components breached and no
  raise; missing/unparseable ledger → NO-GO with the specific reason; the `health.py` wrapper degrades a
  `compute_preflight` failure to an honest NO-GO rather than blanking the payload. No whole-table ORM load is
  introduced on the health path (only indexed max, a bounded `IN` existence query, and tiny JSONL reads).
- **Anti-goals #1/#2/#5:** banner carries only operational trust language (no proven / buy-sell wording);
  freshness is deterministic (no `date.today()`).

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issues were found; all findings are GAP/OBSERVATION-level, which the auditor
protocol documents rather than fixes (fixing them would be scope creep). The audit made **zero** repo
changes (`git status` after the audit shows only the pre-existing dev/iteration files; all verification ran
in the isolated `TMPDIR`, and `READINESS_VERDICT_HISTORY_PATH` was redirected so the repo history log stayed
at its 7 pre-audit lines).

**Verification evidence produced during this audit (exercising the real production code path):**

| Check | Command / method | Result |
|---|---|---|
| Fast readiness tests | `pytest test_readiness.py -k "cfg or record_verdict or resolve_verdict or no_price_data"` | `8 passed in 0.33s` |
| Correctness matrix (all 8 rows) | direct `compute_preflight` calls, lightweight servable engine sub'd for `loaded_engine` | all 8 verdicts exact-match (GO / NO-GO×6 / DEGRADED) |
| Config-wiring | freshness breach under `severity.freshness` = degraded vs no-go | DEGRADED vs NO-GO, as expected |
| `compute_readiness` shape | direct call | `{state, warmup{done,total,status,message}}` unchanged |
| Error: DB unreachable | monkeypatched `latest_data_date` to raise | honest NO-GO, no raise, `as_of`/`reference` None |
| Error: unparseable ledger | bad JSON line in canonical ledger | NO-GO with "unparseable" detail |

---

## 5. Recommended Next Step

**Proceed to the next journey (J-21 / backlog B-304, live-vs-seed drift monitor).** The phase goal is met:
the single canonical preflight verdict is live, single-source, honestly degrading, and pixel-verified on
every decision surface, and the correctness bar is now auditor-verified. J-21 slots cleanly into the
`_apply(...)` seam `compute_preflight` leaves open, per B-301's "enrich the same verdict" design.

Carry the three GAP items into a housekeeping slice on the next iteration (none block closure):
1. **B1** — add the `conftest.py` autouse `READINESS_VERDICT_HISTORY_PATH` redirect so suite runs stop
   appending to the untracked repo history log.
2. **T1** — background the canonical `pytest tests/test_readiness.py tests/test_health.py -v` run to convert
   the auditor-verified assertions into an in-pipeline PASS on the record.
3. **B2** — thread the already-computed readiness dict into `compute_preflight` to drop the redundant
   second `compute_readiness` call on the poll path.
