# goal-i_can_see_the_wealthy_future-iter-11 QA Report

**Verdict:** PASS

**Phase:** goal-i_can_see_the_wealthy_future-iter-11
**Date:** 2026-05-31
**Agent:** qa (MODE 2 — validation)
**Frontend Present:** yes (Chrome MCP browser checks executed)

---

## Summary

J-16 — the VCP (Volatility Contraction Pattern) detector — is shipped and faithful. A config-driven
`detect_vcp` rides each immutable snapshot row **alongside** (never replacing) the setup status,
surfaced as a filter + explained badge on `/stocks`, an identical badge + card on `/stocks/[ticker]`,
and a VCP-vs-non-VCP forward-return breakdown on `/system-health`. All 17 functional test cases pass:
118 targeted backend tests green (0 failures), frontend build clean, and all 5 browser flows verified
live with distinct evidence. Every critical anti-goal (pattern-not-status, no-recompute single-source,
immutability/no-lookahead, no magic numbers, honest NA) is upheld.

### Backend health-path note (non-blocking environment issue)

The QA runner reported the backend "did NOT become healthy" because it probed `GET /health` (404). The
canonical health endpoint for this project is `GET /api/health` (per `.claude/project-template.md`),
which returned **200 OK** repeatedly in the same log. The backend was healthy; the runner used the
wrong probe path. The runner had then shut the backend (and frontend) down, so QA restarted both
cleanly on 8835/3835 and ran the full validation. This is a runner configuration mismatch, **not an
implementation defect**, and does not affect the verdict. (Recommend the runner probe `/api/health`.)

---

## Step 1 — Required artifacts

| Artifact | Status |
|----------|--------|
| `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-11-dev.md` | ✅ present |
| `reports/reviews/goal-i_can_see_the_wealthy_future-iter-11-review.md` | ✅ **PASS** |
| `runs/goal-i_can_see_the_wealthy_future-iter-11/status.json` | ✅ present (`review_passed`) |
| `apps/backend/app/engine/patterns.py` (`detect_vcp`) | ✅ present |
| `apps/backend/tests/test_patterns.py` | ✅ present |
| `reports/qa/goal-i_can_see_the_wealthy_future-iter-11-test-plan.md` | ✅ present (executed) |

---

## Step 2 — Backend tests (exact output)

Full suite (`pytest tests/ -v`) takes ~29 min (walk-forward lifespan fixtures); per the test plan
(TC-10) the **targeted set** was run instead. Log: `reports/qa/goal-i_can_see_the_wealthy_future-iter-11-test.log`

Command:
```
cd apps/backend && .venv/bin/python -m pytest tests/test_patterns.py tests/test_scoring.py \
  tests/test_scanner.py tests/test_forward_testing.py tests/test_api_engine.py \
  tests/test_api_system_health.py tests/test_no_magic_numbers.py tests/test_config.py \
  tests/test_config_engine.py -q
```
Result (verbatim tail):
```
........................................................................ [ 61%]
..............................................                           [100%]
118 passed in 677.54s (0:11:17)
```
**118 passed, 0 failed.** (The dev handoff additionally records the full suite at 234 passed / 0 failed.)

---

## Step 3 — Frontend build/typecheck (TC-11)

```
cd apps/frontend && npm run build
```
✅ Exit 0. `✓ Generating static pages (11/11)`. New `vcp`/`by_vcp` types compiled, no type errors.

---

## Step 3.5 — Functional test plan results

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | Implementation present | artifact | All files/handoff/grep present | `detect_vcp` in patterns.py; 50 vcp hits in apps/; handoff present | **PASS** | status.json at `review_passed` (qa step in progress — expected) |
| TC-02 | Config `patterns.vcp` block | artifact | All 10 keys, sane values | All 10 keys present + `min_contraction_pct` (config-driven ZigZag, not a magic number); `shrink_ratio=0.9∈(0,1]`, all `*_pct>0`, windows>0 | **PASS** | |
| TC-03 | Config typed validation | unit | valid loads, invalid raises ConfigError | covered green in targeted run (test_config*.py) | **PASS** | part of 118 passed |
| TC-04 | `detect_vcp` behavior | unit | pos/neg/NA paths | test_patterns.py green | **PASS** | part of 118 passed |
| TC-05 | No magic numbers incl patterns.py | unit | patterns.py held to contract | test_no_magic_numbers.py green | **PASS** | part of 118 passed |
| TC-06 | VCP is a pattern, NOT a status | unit | not in ALL_STATUSES; no promotion | test_scoring.py green; live: 4 flagged rows are Extended/Avoid — **none Actionable** | **PASS** | anti-goal upheld |
| TC-07 | Single-source / no-recompute keystone | unit | reads serve stored when detector patched to raise | test_api_engine.py green | **PASS** | part of 118 passed |
| TC-08 | Faithful mirror + immutability + no-lookahead | unit | mirror==record; invariants green | test_scanner.py green; live DB mirror check `is_vcp==record_json.vcp.flagged` ✅ | **PASS** | |
| TC-09 | `by_vcp` forward dimension | unit | two cohorts + empty NA + verbatim | test_forward_testing.py green | **PASS** | part of 118 passed |
| TC-10 | Targeted backend suite (regression) | unit | zero failures | **118 passed, 0 failed** | **PASS** | |
| TC-11 | Frontend build/typecheck | build | exit 0, no type errors | clean, 11/11 routes | **PASS** | |
| TC-12 | DB rebuild reproduces VCP | artifact | is_vcp column populated, mix | Fresh DB: column present; per-snapshot flagged = 0–10; latest (2026-05-28) = 4; 31 total | **PASS** | populated from frozen seed, no manual ALTER |
| TC-13 | `/stocks` VCP filter narrows | browser | VCP only→flagged only; All restores | "VCP only" → 4/122 (STX,TSLA,TSM,ORCL); "Non-VCP" → 118/122 (no flagged); 4+118=122 | **PASS** | `TC-13-leaderboard-filtered.png` |
| TC-14 | `/stocks` badge reason+pivot+invalidation | browser | tooltip carries all three | All 4 badges' `title` = reason + `Pivot $X` + invalidation note | **PASS** | verified verbatim via DOM `title` attr |
| TC-15 | Detail badge identical to leaderboard | browser | values match; unflagged honest | STX detail pivot $905.39 / inval $816.98 == stored; MU → "No VCP pattern detected" (no fabricated pivot) | **PASS** | `TC-15-detail-badge.png` |
| TC-16 | System Health VCP-vs-non-VCP | browser | 2 cohorts + n + ⚠ + survivorship | "Forward return: VCP vs non-VCP" → VCP +3.18% n=27 ⚠ / non-VCP +2.01% n=1191; survivorship label present | **PASS** | `TC-16-system-health-by-vcp.png` |
| TC-17 | Regression: existing surfaces intact | browser | filters/panels/as-of unchanged | Setup="Extended"→11/122 all Extended; SH by-bucket/setup/regime/control panels present; as-of switcher (11 dates) re-points to 2022-10-07 | **PASS** | |

**17 / 17 test cases passed.**

---

## Step 4 — Chrome MCP browser checks

Executed live against `http://localhost:3835` (QA-restarted dev server) → backend `http://localhost:8835`.

- **/stocks**: 122 rows; 4 selects (as-of, sector, setup, **VCP**). VCP filter pure client re-display on
  the server-computed `row.vcp.flagged` — ranking unchanged. 4 VCP badges each carry the server-built
  reason + pivot + invalidation tooltip.
- **/stocks/STX** (flagged): pivot $905.39 + invalidation $816.98 byte-identical to the leaderboard row.
- **/stocks/MU** (unflagged): "No VCP pattern detected" — honest empty, no fabricated pivot.
- **/system-health**: VCP-vs-non-VCP `BreakdownPanel` with both cohorts, sample sizes, low-sample ⚠ on
  n=27, survivorship-bias caveat present.

Evidence (md5-distinct), saved under `reports/qa/goal-i_can_see_the_wealthy_future-iter-11-evidence/`:
```
701b94b...  TC-13-leaderboard-filtered.png
c809edc...  TC-15-detail-badge.png
3b1a4d8...  TC-16-system-health-by-vcp.png
```
Corroborated by the developer's 4 distinct PNGs in
`reports/evidence/goal-i_can_see_the_wealthy_future-iter-11/` (01-leaderboard, 02-detail-STX,
03-system-health, 04-detail-ORCL).

> Note: an initial `npm run build` (TC-11) overwrote the running `next dev` server's `.next`
> directory, causing transient empty renders + a crash mid-session. QA restarted the frontend cleanly
> and all flows then rendered correctly. This is a test-sequencing artifact, not a product defect.

---

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the new capability?** Yes — a VCP filter + explained badge on the
   leaderboard, a dedicated VCP card on stock detail, and a VCP-vs-non-VCP forward-return panel on
   System Health.
2. **Can the user see, understand, and control it?** Yes — filterable (VCP only / Non-VCP / All),
   explained (reason + pivot + invalidation in tooltip and detail card), evidenced (forward-return
   edge with honest sample size).
3. **Still relying on old generic pages?** No — added to the correct existing IA homes; spec mandated
   no new nav route this iter.
4. **Technically complete but under-exposed?** No — the capability is visible and controllable on all
   three intended surfaces.

**Verdict:** UI-PASS

---

## Blockers

None.

---

## Anti-goal verification (explicit)

- **VCP is a pattern, not a status** — `"VCP" ∉ ALL_STATUSES`; all 4 flagged rows resolve to
  Extended/Avoid, zero Actionable (TC-06).
- **No recompute / single source** — keystone test serves stored values with the detector patched to
  raise; UI tooltip rendered verbatim from `row.vcp` (TC-07).
- **Immutable + no-lookahead + faithful mirror** — `is_vcp == record_json.vcp.flagged` confirmed on
  live DB; named invariant tests green (TC-08).
- **No magic numbers** — `patterns.py` in CALC_FILES; all thresholds from `config.patterns.vcp` (TC-05).
- **Honest NA / no fabrication** — unflagged detail shows "No VCP pattern detected"; empty cohort → NA;
  low sample flagged ⚠ (TC-04/09/15/16).

---

## Services

QA-started backend (8835) and frontend (3835) were both stopped (by port) after validation.
