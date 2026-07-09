# goal-mcp-loop-iter-25 Audit Report

**Date:** 2026-07-09
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's single purpose — proving the already-committed `mmap_size_bytes: 0` fix eliminates the iter-24 cold `GET /api/data` OOM crash — is genuinely achieved and verified from primary evidence: the fix is present and committed at HEAD (`665565a`, `config.yaml:108`) with `pool_size`/`max_overflow`/`memory_cap_mb` untouched, the working tree carries **zero** source or test diff vs HEAD (I re-confirmed every DoD-protected test file at 0 diff-lines), and the cold-restart crux is proven live by two independent lanes (canonical browser-qa UT-02/UT-03 + the dev's HTTP-level RSS-sampled repro), which I corroborated by opening the actual asserted frame (`UT-02-run1-data-fullpage.png` renders a fully-populated `/data` as the first request after a cold boot — no crash, no blank page). J-13 is restored, J-15's cold-path criterion is met, and anti-goal #8 is upheld. The gaps that keep this from a clean PASS are evidence-hygiene defects confined to the **non-terminal QA lane** (a mis-cited storage-card screenshot — now reconciled — and an over-budget `/api/health` figure marked PASS) plus a genuinely soft same-instant storage-card↔API match; none threaten the phase goal, all are documented, and the terminal lanes are clean.

---

## 2. Findings

### Backend / Config Findings

**B1 — verified (no defect): the fix is real, committed, and correctly scoped.**
`config.yaml:108` reads `mmap_size_bytes: 0` in both the working tree and at HEAD `665565a` (verified via `git show HEAD:config.yaml`). `pool_size: 10` (`config.yaml:119`), `max_overflow: 20` (`:120`), `cache_size: -262144` (`:107`), and `server.memory_cap_mb: 6144` (`:1224`) are all unchanged — no out-of-scope re-tuning. `git diff HEAD -- config.yaml` is empty. The mechanism (disabling the per-pooled-connection virtual-address mmap reservation that, at 1 GB × ~6 live connections, breached the 6144 MB `ulimit -v` before the prefill ran) is sound and matches the root-cause analysis. No defect.

**B2 — verified (no defect): zero source/test drift.** `git diff HEAD --stat -- apps/backend apps/frontend config.yaml` is empty; per-file checks return 0 diff-lines for `test_data_manager.py`, `test_bar_cache.py`, `test_api_engine.py`, `test_health.py`, `data_manager.py`, `app/data/page.tsx`, and `availability-heatmap.tsx`. NOTE: the git snapshot captured at *this audit conversation's* start listed several of these as modified — that snapshot was stale (iter-24 had "parked uncommitted work"; the engine reverted the tree to HEAD before/at iter-25 start). The current, authoritative state is clean, independently matching the dev, reviewer, and ux-regression checks. The DoD's "byte-identity tests remain green unedited" is satisfied (123 passed/0 failed, dev-run + reviewer-verified; not re-run here per the coordinator's instruction and corroborated by the zero-diff proof).

### Frontend Findings

**F1 — verified (no defect): no UI change, error boundary intact.** `apps/frontend` is byte-identical to HEAD. I visually confirmed the two negative/positive states from primary frames: `UT-06-backend-unavailable.png` shows exactly one contained "Backend unavailable" card with the full nav/shell intact (anti-goal #8's "never a blank application-error page" holds), and `UT-04-storage-card.png` / `UT-02-run1-data-fullpage.png` show the fully-populated `/data` surface. No misleading UI.

### Test / Evidence Findings

**T1 — IMPORTANT (fixed): QA-lane TC-02 cited an error-card screenshot as proof of a working storage card.**
`reports/qa/goal-mcp-loop-iter-25-qa.md` TC-02 ("Storage card values match API payload — PASS") cited `TC-02-storage-card.png`, which is byte-for-byte identical (md5 `3fe10a6b962f65a6a2a858fedf8db22b`) to `UT-06-backend-unavailable.png`. I opened the file: it is the *Backend unavailable* red error card, **not** a storage card. This is precisely the rubric §6 ✖ anti-pattern (a PASS whose own screenshot shows an error state) and the iter-11/13/14/15 lesson (mis-cited/reused frames). Severity: I was genuinely between GAP and IMPORTANT and chose the higher per the tie-break rule, because a PASS backed by a contradicting frame is a hard honesty violation — *but it does not compromise the phase goal*, because the **canonical (terminal) lane** independently proves the same claim with valid, md5-distinct evidence (UT-01 `UT-01-result.png`; UT-04 `UT-04-storage-card.png` / `UT-03-run2-data-fullpage.png`, all real card values, visually confirmed). **Fix applied:** corrected the TC-02 citation in `qa.md` to the valid canonical frames and added an explicit auditor reconciliation note documenting the mis-save (the bad file and its md5 are left in place as a documented trail, not overwritten — overwriting evidence would itself be tampering). This matches the ux-regression reviewer's flag and the coordinator's reconciliation request.

**T2 — OBSERVATION (not fixed): QA-lane TC-13 marks an over-budget `/api/health` figure PASS.**
`qa.md` TC-13 records `/api/health` at 0.210 s against a ≤0.1 s budget yet verdicts PASS, rationalized as "cold, not warm." The authoritative warm measurement is `reports/perf-budgets.md:187` (`/api/health` 0.090045 s, `scripts/measure-perf.sh` methodology), which holds the budget with the iter-24 run (0.092 s) agreeing. So the budget genuinely holds warm; the QA-lane figure is an improper-warming artifact. Noted in the reconciliation block I added to `qa.md`. Not fixed beyond that note (the correct value already lives in the terminal perf record; further QA-lane surgery would be scope creep). Reinforces the theme that the non-terminal QA lane is the weak link this iteration.

**T3 — GAP (not fixed): same-instant storage-card↔API byte-match was never rigorously captured.**
The testing requirement "storage-footprint card values match the `GET /api/data` `capacity` payload" was verified softly: the QA lane claimed a byte-match but with the broken screenshot (T1), and the canonical lane's UT-04 compared the *card* to the (stale) spec constants rather than a same-instant `curl … | jq .capacity`, noting the DB had grown (`scanner_results` 165,755→166,213; `forward_returns` 821,054→823,409). The capability demonstrably works — the card is populated *from* the same API response (zero code diff this iteration; `test_data_manager.py` diagnostic query-count test green unedited), and I saw real, correct values rendered — but the exact same-instant diff the plan asked for was not produced. Acceptable for a recovery pass (carry-forward capability, not new code, not a DoD-critical line); documented for a future session.

**T4 — OBSERVATION (not fixed): committed "capacity" figures are not static across the iteration.**
`perf-budgets.md`'s iter-25 sections record `scanner_results_rows 165755` / `forward_returns_rows 821054` as "byte-identical to every prior figure … no drift," but the later canonical lane observed 166,213 / 823,409. `apps/backend/data/trendora.db` is **untracked** local data (`git ls-files --error-unmatch` fails on it), which testing/backfill mutates; each measurement is internally consistent at its own instant and no journey is affected (every UI-vs-API comparison is same-instant). Honest to note; not a defect.

**T5 — note (not a defect): the phase-closure gate is still pending downstream.**
`status.json.current_step = ux_regression_complete`; `next_action` = "Ready for auditor and phase-closure gates." The DoD line "phase-closure-auditor → CLOSURE-PASS on the FIXED build" runs *after* the auditor in the pipeline, so it is legitimately not yet produced. Final DoD closure depends on that gate passing on this same clean build — flagged so the coordinator does not treat this audit as the terminal gate.

---

## 3. Domain Assessment

The core domain claims hold up under scrutiny:

- **Cold-path resilience (the crux, J-13 + J-15 cold criterion):** proven by two independent lanes that both exercise the *real heavy* code path, not an `/api/health` boot substitute — the exact false-positive the iter-13/20/22/24 lessons warn against. Canonical browser-qa UT-02/UT-03 stop the backend, confirm-down via `curl` (code 000), cold-start, poll readiness via a *non-HTTP* `ss -tln` check (preserving true "first request" semantics), then open `/data` first: real content in ~10.2 s / ~10.5 s, backend survived, downstream `/stocks` (541/541) loaded, `/api/health` 200 after. The dev's HTTP-level repro adds RSS sampling (peak ~1.8–1.9 GB, ≈4.3 GB under the 6144 MB cap), 2/2 clean. I confirmed the crux frame directly. This is a genuine recovery, not a claimed one.

- **No false-proven claims (anti-goals on evidence integrity):** browser-qa UT-09/UT-11 extracted `/evidence` raw HTML — 14 "FAIL", **0 "PASS"** — both ledgers all-FAIL, no stale/unbacked edge presented as proven. The Bonferroni divisor stays 8; no Evidence Claim was introduced, matching the spec's "no new proven signal" posture. Consistent with the decision-support-only, no-orders anti-goals.

- **Determinism / no-lookahead / byte-identity:** untouched by construction (zero source diff) and guarded by the unedited byte-identity suites (123/0). The iter-24 regression was a *memory-footprint* config bug, not a correctness/lookahead bug, and the fix is a pure VA-reservation removal that leaves served values byte-identical — confirmed by the `capacity` payloads matching prior figures at each measurement instant.

Local-first, minimal, explicit-failure architecture is preserved: the one negative path (`/data` on an unreachable backend) renders a single contained honest card with NA rather than fabricated values (UT-06, visually confirmed), and the unbounded whole-table ORM load that anti-goal #8 forbids remains fixed (iter-19 streamed prefill, unchanged).

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/qa/goal-mcp-loop-iter-25-qa.md` | Corrected TC-02's mis-cited evidence (`TC-02-storage-card.png`, md5-identical to the `UT-06-backend-unavailable.png` error card) to the valid canonical-lane frames (UT-01/UT-04); verdict left PASS (independently proven by the terminal lane). |
| 2 | Observation | `reports/qa/goal-mcp-loop-iter-25-qa.md` | Added an auditor reconciliation blockquote documenting the T1 mis-save and the T2 `/api/health` over-budget-but-PASS nuance (authoritative warm figure is `perf-budgets.md` 0.090 s). |

No product source, test, or config file was touched (none needed it). The bad screenshot file was deliberately **not** overwritten — its md5 is now a documented trail rather than hidden.

**Post-fix self-verification:** the corrected citation points at evidence I visually confirmed (`UT-04-storage-card.png` shows the real populated card; `TC-02`/`UT-06` are the error card). The diff is limited to the TC-02 Notes cell plus one blockquote — no verdict flipped, no other row or file changed, no error silenced. No dev-handoff claim is invalidated (the handoff cites none of these QA-lane files).

---

## 5. Recommended Next Step

**Proceed to the phase-closure gate on this same clean build.** The phase goal is achieved: the cold-path OOM fix is committed, in place, correctly scoped, and live-verified by the canonical lane; J-13 is restored, J-15's cold criterion met, required-still-passing journeys freshly replayed green, anti-goal #8 upheld, and the artifact reconciliation (perf-budgets correction, honest summaries, non-contradictory `status.json`) is done. The evaluator should expect **CONTINUE** (not GOAL_ACHIEVED) — J-02/J-06/J-07/J-08/J-09 remain sanctioned-partial and J-16 is deliberately unbuilt, exactly as the spec states.

Carry-forward (non-blocking, do not bundle into a recovery pass): the QA lane's evidence hygiene needs tightening (T1/T2 recurred the iter-24 pattern of a QA-lane PASS resting on weak/wrong evidence — trust the canonical + ux-regression content over `status.json`/QA prose); the same-instant storage-card↔API byte-diff (T3) should be captured cleanly in a future `/data`-touching iteration; and the previously-tracked F1 (`/data` no-retry desync) and dead-duplicate chart-component cleanup remain deferred as planned.
