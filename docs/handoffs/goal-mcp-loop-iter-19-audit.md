# goal-mcp-loop-iter-19 Audit Report

**Date:** 2026-07-07
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal is genuinely achieved and strongly evidenced: the iter-18 REGRESSION (the `/stocks`
Sector-sort crash on the ~78%-null-sector 30-year pool) is fixed at its source AND contained by a new
error boundary, and the coupled `/api/data` prefill OOM is fixed by a streamed, column-projected load
with a double-scan guard — both verified by tight unit tests, a live cold-path measurement, and a
browser-QA lane that ran to completion (23/24, one P3 skip). I independently re-derived the byte-identity
safety of the `Bar` substitution, opened the two load-bearing screenshots (the exact crash driver and the
error-containment card), and confirmed the working-tree diff is surgical with no scope drift. The gaps
are all documented and non-blocking (cold-restart OOM measured by the developer's curl rather than
re-reproduced by the browser agent; two seed-heavy backend test files deferred; the F1 chart x-domain
carry item). None compromise the phase goal, so no fixes were required.

---

## 2. Findings

### Backend Findings

**B1 — GAP (observation): cold-*restart* `/api/data` OOM survival was measured by the developer, not re-reproduced by the browser agent.**
The single most novel claim — that a genuine cold-process-restart `/api/data` load survives under the
6144 MB cap — is evidenced by the developer's live measurement against the real 30-year DB (single cold
request 10.5 s / ~1.09 GB, 6-concurrent 18.5 s / ~1.10 GB), recorded in `reports/perf-budgets.md`
(Item-A table). The browser lane's `UT-12` (`reports/phase-goal-mcp-loop-iter-19-ui-test-results.md:122`)
was a **warm** load, because restarting a backend shared with the goal-mode orchestration is outside a
browser agent's remit. The ux-regression review flags this precisely
(`reports/phase-goal-mcp-loop-iter-19-ux-regression.md:54-71`) and asks the auditor to reconcile it.
**Reconciliation:** DoD item 3 ("Backend survives the FULL canonical browser-qa lane … cold `/api/data`
completes under the cap; item-A measurement recorded") is met — the backend survived all 24 browser tests
without OOM, the cold-path measurement is a real request/response with memory sampling (meets the
"API works" evidence floor), and the streaming + column-projection fix is structurally proven to lower
peak memory. The gap is *which agent re-ran a cold restart*, not a missing or unproven deliverable. No fix
warranted; treat the cold-start claim as "mechanism-verified + developer-measured cold + browser-verified
under warm/6-concurrent," not "browser-verified under a genuine cold restart."

**B2 — OBSERVATION: `perf-budgets.md` reports RSS (`VmRSS`/`VmHWM`), but `ulimit -v` caps VSZ.**
`config.yaml:1183`'s `memory_cap_mb: 6144` is a `ulimit -v` (virtual-memory) cap, whereas the Item-A table
samples resident memory (RSS), which is typically smaller than VmSize. So the "~1.09 GB vs 6144 MB" figure
understates the true cap-distance. This is the reviewer's NOTE
(`reports/reviews/goal-mcp-loop-iter-19-review.md:20-23`) and I confirm it. It does **not** weaken the
pass criterion: the no-OOM outcome is *directly observed* (the `ulimit -v` would have killed the process
had VmSize exceeded 6144; it did not, across the dev's cold runs and the full browser lane). Only the
numeric headroom is imprecise. Fixing it (sampling `VmSize`) is a future measurement-pass nicety, not a
correctness issue — out of scope to change here.

**B3 — OBSERVATION: the optional growth-leeway `prefill(symbols=, min_date=)` bounds were not added.**
`apps/backend/app/engine/prices.py:91` is `prefill(self, session, expected_symbols=None)` — the spec's
"(Growth leeway — design in now, cheap; **optional** per §A)" `symbols=`/`min_date=` parameters were not
implemented. This is explicitly optional in IN SCOPE and is **not** a DEFINITION OF DONE item; the spec's
OUT OF SCOPE and NOTES both stress "item A only." Skipping it is correct scope discipline, not a gap in a
required deliverable. Noted only for completeness.

### Frontend Findings

**F1 — GAP (observation): `/stocks/{ticker}` Full-history chart x-axis does not visually extend to the deep first-bar date.**
On `/stocks/NVDA` the caption reads "3025 bars · history since 1999-01-22" but the rendered gridlines only
label ~2019–2026 (`reports/phase-goal-mcp-loop-iter-19-ui-test-results.md:115`, note 1). This is the spec's
own **non-blocking "F1" carry item** ("confirm whether the Full-history chart plots pre-2018 weekly bars …
widen the x-domain if not"), explicitly out of this iteration's DoD. The browser check confirms the
suspicion is real; it is correctly reported as an observation, not a UT-10 failure. Appropriate follow-up
for a later iteration.

**F2 — OBSERVATION: `global-error.tsx` was source-verified, not dynamically triggered.**
`UT-18` is SKIPPED because forcing a root-layout throw requires editing `app/layout.tsx`, outside the
browser agent's "no source edits" rule. I independently read `apps/frontend/app/global-error.tsx`: it
renders its own `<html>/<body>`, imports only `./globals.css` (no Sidebar/AsOfProvider/app components), and
uses the `reset` prop — the correct Next.js last-resort pattern that cannot depend on the tree it replaces.
The per-route boundary `error.tsx` *was* dynamically verified (UT-16/17). This is an acceptable
substitution for a P3, non-gating boundary.

**F3 — OBSERVATION (pre-existing): `return-attribution.tsx` renders a null sector as a blank omission, not "Unassigned".**
`apps/frontend/components/return-attribution.tsx:52` (`row.sector ? <span>…</span> : null`, untouched this
iteration, its field was already `string | null` and already guarded) shows nothing for an unmapped sector,
diverging from the new shared `sectorLabel` "Unassigned" convention used on `/stocks`, `/stocks/{ticker}`,
and `/scanner-runs/{runId}`. Pre-existing and correctly out of iter-19 scope; a terminology inconsistency
worth a future note, not a defect (it does not crash and was already null-guarded). Matches the
ux-regression review's flag (`…-ux-regression.md:120-127`).

### Test Findings

**T1 — GAP: `tests/test_scanner.py` and `tests/test_bars.py` were not run this session.**
Both depend on the expensive real-seed-load fixture (per project memory, the 30-year basis makes the full
suite ~10-11h; these are the slow, `loaded_engine`-class files). The dev handoff discloses this honestly
with a re-run command. **Assessment (low-risk, sound reasoning):** `test_bars.py` exercises
`/api/stocks/{ticker}/bars` via the DEFAULT uncached `bars_asof`/`bars_through_latest` path — which returns
`DailyPrice`, not the rewritten `_BarCache`/`Bar` (I independently confirmed at `api/stocks.py:171` and
`prices.py:308-325`); `test_bars_windowing.py` covers the same endpoint with fast fixtures and passed (9/9).
`test_scanner.py` DOES use the cache, but the exact byte-identity property it would re-confirm is already
gated green by `test_bar_cache.py::test_cached_snapshot_equals_uncached_row_level` and
`::test_bootstrap_snapshots_equal_with_cache` (both run `scanner.run_scan`/`score_stocks` through the cache
and assert row-level equality vs uncached; 12/12 passed under both dev and QA). The specifically-named DoD
gate (`test_bar_cache.py` byte-identical snapshot tests) is green. Documented deferral, not a hidden failure.

---

## 3. Domain Assessment

The core domain logic is correct and well-guarded.

- **Byte-identity of the OOM fix (the correctness gate) — independently confirmed.** The `Bar` NamedTuple
  (`prices.py:31-47`) exposes exactly `.date/.open/.high/.low/.close/.volume`. I grepped every
  bar-consuming module (`scoring.py`, `sectors.py`, `regime.py`, `themes.py`, `forward_testing.py:265`,
  `indexes.py`, `patterns.py` via the extractors) and found **zero** reads of a `DailyPrice`-only attribute
  (`.symbol`/`.id`/`.adjusted`/`.updated_at`) off a bar — every consumer reads bars structurally through
  `closes()/highs()/lows()/volumes()` or `bar.date`. The only `.symbol/.id` hits are on non-bar objects
  (resolver rows, `ForwardReturn` rows, import checkpoints). The chart path (`api/stocks.py:171`) reads
  `bars_through_latest`/uncached `bars_asof`, which return `DailyPrice`, so J-10's byte-identical bars are
  structurally immune to the cache rewrite. This static proof plus the passing row-level snapshot tests
  give high confidence the substitution changed HOW bars load, never WHAT is served.
- **The double-scan diagnosis is real and correctly fixed.** The `_prefilled` guard (`prices.py:89,129-153`)
  makes the whole-table scan run at most once per cache instance; the empty-series `expected_symbols`
  bookkeeping still runs on every call (preserving the iter-37 load-once-per-job invariant for no-bar
  names). The new `test_data_manager_membership_cache.py` test counts `real_scans` (calls where
  `_prefilled` was False) and asserts exactly 1 despite ≥2 nested `prefill()` calls — a tight, direct proof.
- **The single-flight was verified, not rebuilt** — `data_manager.py` is confirmed **unmodified** in the
  working tree, matching the handoff's claim; the pre-existing J-100 concurrency test (3/3) plus the live
  6-concurrent measurement (~1.10 GB, not ~6×) show cross-request cold callers already serialize. No
  redundant locking layer was added (the plan's Risk #3 was heeded).
- **Honest null handling.** The backend still serves `sector: null` for unmapped pool names (never a
  fabricated GICS sector — anti-goal respected); the frontend maps it to the honest "Unassigned" bucket via
  one shared helper (`lib/sector-label.ts`), applied at all four consumer sites in `stocks/page.tsx`
  (comparator L96, filter vocabulary L361, predicate L412, cell L885) plus the two detail pages. `tsc
  --noEmit` is clean, proving the widened `string | null` type flagged and closed every call site.
- **Anti-goals preserved end-to-end** (browser-verified): all-FAIL ledger with zero "Proven" (UT-21:
  1623/1623 "Not yet proven", 7/7 FAIL), byte-identical coverage/bars (UT-10, UT-13), and a clean
  product-wide anti-goal-#2 language sweep (UT-19). Anti-goal #8 (resilience to data-shape/scale change) is
  now genuinely satisfied: no crash on Sector-sort, no OOM on `/api/data`, graceful contained degradation.

**Verdict reconciliation (DoD item requiring the auditor to read the gate verdicts):**
Review = PASS; QA = PASS; Browser-QA (`ui-test-results.md`) = PASS (23/24, UT-18 P3 skipped);
UX-regression = UX-REGRESSION-PASS. The **phase-closure-auditor has not run yet** — it is the final gate
*after* the auditor (core.md DoD steps 7 then 9), so there is no closure verdict to reconcile at this point;
the six UI-visibility artifacts it checks all exist (`implementation-summary`, `user-visible-changes`,
`ui-surface-map`, `ui-test-plan`, `ui-test-results`, `what-to-click` — all present under `reports/`).
The DoD "no 'zero blockers' claim that contradicts a `-fail-`-named frame" reconciliation **holds**: the
evidence dir contains zero `-fail-`-named frames (all 23 are `UT-*-result.png`), so `status.json`'s
`blockers: []` is honest — the exact failure mode iter-18 exhibited (a real crash frame sitting under a
"zero blockers" claim) is absent here. `qa.md`'s browser-test "SKIPPED (frontend not accessible)" rows are
not a contradiction: QA validation ran before the canonical lane and explicitly deferred to it; the
canonical lane subsequently ran and PASSED, which is the authoritative browser evidence.

**Screenshot hygiene (the iter-18/14 recurring lesson) — checked, not trusted.** I md5'd the key frames and
opened the two most load-bearing ones. `UT-02-result.png` genuinely shows the leaderboard sorted by Sector
ascending ("SECTOR ↑", Communication Services→Industrials, 541/541, full nav) — the exact click that
crashed iter-18. `UT-16-result.png` genuinely shows the contained error card with the complete sidebar nav
preserved. All frames are 70 KB–800 KB (far from the ~5855-byte blank-frame signature). The one md5
collision (`UT-03` == `UT-04-06`) is disclosed in the results doc (note 5) and explained (sort state carried
over between captures); those verdicts are additionally backed by full 541-row DOM parsing, not the frame
alone.

---

## 4. Fixes Applied During This Audit

None. Every finding is GAP- or OBSERVATION-level; there were no CRITICAL or IMPORTANT issues. Per the
auditor rules, fixing GAP/OBSERVATION items would be scope creep, so the implementation was left unchanged.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes required |

---

## 5. Recommended Next Step

**Proceed.** The iteration cleanly closes the iter-18 REGRESSION and its coupled OOM defect, restores and
hardens the `/stocks` headline page, and is verified end-to-end with genuine browser evidence and tight,
byte-identity-gated unit tests. Hand off to the phase-closure-auditor (the final gate) to confirm the six
UI-visibility artifacts — all are present and consistent from this review.

Carry these documented, non-blocking items to a future iteration (do not reopen iter-19 for them):
1. Re-run `tests/test_scanner.py tests/test_bars.py` for independent confirmation when a several-minute
   seed-load budget is available (T1 — low-risk; the property is already gated by `test_bar_cache.py`).
2. The F1 Full-history chart x-domain widening (F1) — the spec's own deferred carry item.
3. Add a `VmSize` sample to `perf-budgets.md` for a precise cap-distance figure (B2), and, if pool growth
   is imminent, the optional `prefill(symbols=, min_date=)` bounds (B3).
4. Reconcile the `return-attribution.tsx` blank-vs-"Unassigned" terminology inconsistency (F3).
