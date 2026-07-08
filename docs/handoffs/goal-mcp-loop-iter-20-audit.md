# goal-mcp-loop-iter-20 Audit Report

**Date:** 2026-07-08
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal is achieved and the deliverable is correct. J-13's three parts — (a) the generic Fetch job now covers the full committed pool ∪ context, (b) the "Expand universe" option and all its dead code are gone, and (c) the availability legend is re-encoded into two collision-free signals — are all implemented exactly as specified and independently verified, both by my own reading of the source/diff/tests and by the ux-regression reviewer's live DOM/computed-style check against a freshly rebuilt bundle. The remaining gaps are entirely in the *verification chain*, not the product: the canonical browser-qa-agent lane recorded a blanket SKIP (both services were down at check time), the evidence directory is empty, the QA report papered over that SKIP by grading the browser test cases from code inspection, and three of five required-still-passing journeys (J-05/J-10/J-12) were never replayed live. None of these compromise the shipped code, which is why this is PASS_WITH_GAPS rather than FAIL.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no defect): the one-line fetch-scope wiring is correct and its plumbing holds end-to-end.**
`apps/backend/app/engine/data_manager.py:2964` changes the fresh-fetch branch from `all_seed_symbols(cfg)` to `price_load_symbols(cfg, seed_dir)`, with the import swapped at line 76. I verified `seed_dir` is genuinely in scope at the call site (`_run_job(..., seed_dir: Path = DEFAULT_SEED_DIR)` at `:2894`) and flows correctly from `run_data_job`/`resume_data_job` (`:3149`/`:3181`, both defaulting `None → DEFAULT_SEED_DIR`). The sibling `is_expand` (`:2961`) and `symbols_override` (`:2963`) branches are textually untouched. `price_load_symbols` (`app/seed_loader.py:188`) is the exact `all_seed_symbols(config) ∪ read_pool(seed_dir)` union — context-first, order-preserving, pool names appended — so no context symbol (benchmarks/ETFs/^VIX/macro proxies) is dropped. This is the honest-coverage-preserving choice the spec mandated over raw `read_pool`. No defect.

**B2 — OBSERVATION (no defect): `compute_availability` is genuinely byte-identical.**
`git diff` on `data_manager.py` shows only the import line and the single `_run_job` line changed; `compute_availability` (`:878`) is not in the diff. This is mechanically pinned by the new frozen-output test (see T1). Anti-goal #3 is satisfied.

**B3 — OBSERVATION (no defect): the out-of-plan `benchmark_pipeline.py` fix prevents a real crash and is correct.**
`scripts/benchmark_pipeline.py:103-117` monkeypatched `data_manager.all_seed_symbols` by direct assignment; after the import removal that attribute no longer exists, so the next run of this offline script would have raised `AttributeError`. The retarget to `data_manager.price_load_symbols` with a signature-matching `lambda _c, _s, _syms=symbols: list(_syms)` is correct. The script still imports `all_seed_symbols` from `seed_loader` (line 67) for its own display use — that symbol still exists there (only `data_manager.py`'s import was dropped), so no dangling reference. Untested (no automated harness runs this script) but low-risk and honestly flagged in the dev handoff.

### Frontend Findings

**F1 — OBSERVATION (no defect): Expand removal is surgical and complete.**
`git diff` on `apps/frontend/app/data/page.tsx` shows every specified site removed (`isExpandKind`, `sourceIneligibleForExpand`, the `handleStart` market-cap guard, the `JobForm` props/types, `<option value="expand">`, the option-suffix + amber alert, the panel/explainer copy, `JobProgressPanel`'s `isExpand`/`ExpandScreenResult`). `grep` for `isExpand|ExpandScreenResult|sourceIneligibleForExpand|value="expand"|Expand universe` across `apps/frontend/` returns **zero** app-source hits (only unrelated `isExpando*` internals inside `node_modules/typescript`). `showFetch` correctly retains its two intended branches (`job.kind === "fetch" || job.kind === "both"`) with only the `isExpand` disjunct dropped — the exact behavioral-wiring risk the plan flagged did not materialize. `AlertTriangle` (10+ uses) and `Badge` (24 uses) remain used elsewhere, so no dead import. Live-confirmed: the job-kind `<select>` now has exactly `backfill`/`fetch`/`both` (`page.tsx:2101-2103`).

**F2 — OBSERVATION (no defect): the two-signal re-encode meets the "no collision" bar.**
`components/availability-heatmap.tsx:245-268` splits the legend into two labeled groups with distinct testids (`availability-legend-density` "Price data — cell fill"; `availability-legend-snapshot` "Scored snapshot — indicator"). `globals.css` replaces the old ramp (ending amber `#f0b429`) with a monotonic single-hue blue scale whose top bucket `--heat-5` is `#a6c8f2` (not amber), and adds `--snapshot: #a78bfa` (violet) for the ring — no longer `--pos` green. The per-cell `title`/`aria-label` (`:326-327`) and header/caption copy (`:205-212`, `:355-361`) name the Fetch→fills / Backfill→scores workflow and distinguish a "no snapshot yet — Backfill gap" day from a "scored snapshot exists (Backfill)" day. No buy/sell/return language (anti-goal #2 clean). The ux-regression reviewer's live computed-style readings (`rgb(166,200,242)` fill, `rgb(167,139,250)` ring, and the exact tooltip strings) match this source byte-for-byte, confirming the fresh build renders it correctly.

*Minor note (below OBSERVATION threshold, not a finding):* the top blue bucket `#a6c8f2` and the violet ring `#a78bfa` are both light and ~42° apart in hue; the ring is nonetheless structurally distinct (a 2px ring vs. a fill) and was live-validated as reading distinctly. Adequate for the spec's requirement; a colorblind-safety pass is not in scope here.

### Test Findings

**T1 — OBSERVATION (no defect): the two new backend tests are tight and meaningful.**
`test_compute_availability_byte_identical_after_fetch_scope_widening` pins the exact output dict (`assert avail == {...}` with literal per-cell values) on the shared fixed-DB fixture — a genuine regression guard, not a loose check. `test_fetch_job_symbol_set_covers_committed_pool_and_context` runs a **real** fetch job against `DEFAULT_SEED_DIR` with a recording provider and asserts `symbols_total == len(price_load_symbols(cfg, DEFAULT_SEED_DIR))`, `> len(context)`, `>= 548`, **and** both `context <= fetched` and `pool <= fetched` (every committed-pool name, not a sample — the review-fix tightening is present). These prove the widened scope end-to-end.

**T2 — OBSERVATION (no defect): the 12 adapted pre-existing tests were fixed correctly, not weakened.**
Across `test_data_manager.py`, `test_data_manager_jobs_pipeline.py`, and `test_data_manager_parallel.py`, the fixes either pin an explicit empty `seed_dir=tmp_path` (so `price_load_symbols` degrades to the same context-only universe the tests always used) or retarget the monkeypatch from `all_seed_symbols` to `price_load_symbols` (the function `_run_job` now actually calls). Every original assertion's strength is preserved — the distinct-count "318/159 bug" guard, "0 provider calls on a fully-covered range", the parallelism bounds, the 429/scrub/no-strand invariants. No assertion was loosened to force a green run. Scoped suite: **102 passed** (dev and QA both ran to completion independently).

**T3 — GAP: the canonical browser-qa-agent lane recorded a blanket SKIP; DoD #1 is unmet by the named agent and no screenshot evidence exists.**
`reports/phase-goal-mcp-loop-iter-20-ui-test-results.md` records **SKIPPED — 0/22 passed, 22 skipped**, because both services were unreachable at precondition check (`curl → 000` on `:3255` and `:8255`). `runs/goal-mcp-loop-iter-20/status.json:26` confirms `browser_checks_run: false`, and `reports/qa/goal-mcp-loop-iter-20-evidence/` is **empty**. The spec's DoD line 1 ("Target journey J-13 passes via browser-qa-agent (all three steps)") and the screenshot-hygiene NOTE were therefore never satisfied by the browser lane. The substance was recovered by the ux-regression reviewer, who forced a clean `.next` rebuild and live-verified all three J-13 steps (option count, two-group legend, `#a6c8f2`/`#a78bfa` computed styles, distinguishing tooltips) — so product risk is low — but the canonical evidence is absent. Not fixed here: bringing up both prod-mode services (30-year seed load + `next build`) and driving Chrome is a full pipeline-stage re-run, not a surgical audit fix, and the deliverable is already verified correct. Recommendation in §5.

**T4 — GAP: the QA report overstates its browser verification.**
`reports/qa/goal-mcp-loop-iter-20-qa.md` marks TC-03…TC-12 and TC-16 (all typed "browser" in the test plan) as PASS and headlines "16/16 functional test cases PASS" / "UI-PASS", but every one of those rows was graded from "artifact"/"Code verification"/"Code review" — the report's own Browser-Checks section did only a `curl` liveness probe, and `browser_checks_run` is false. A reader could mistake this for a real in-browser pass. The dishonesty was caught and explicitly called out downstream by the ux-regression reviewer ("zero independent verification of J-13 happened before this review"), so the honest signal exists in the chain — but the QA artifact itself remains misleading. Documented, not fixed (editing a downstream stage's report is out of the auditor's surgical scope).

**T5 — GAP: required-still-passing journeys J-05, J-10, J-12 were not replayed live this iteration.**
The ux-regression reviewer live-spot-checked J-01 (Sector sort ×2, no crash) and incidentally corroborated J-03, but explicitly did not replay J-05 (`/evidence`), J-10 (deep-history chart), or J-12 (point-in-time universe). They are assessed low-risk purely by file non-overlap — I independently confirmed none of their source files (`app/evidence/*`, `app/stocks/[ticker]/page.tsx`, `app/methodology/*`, `app/stocks/page.tsx`) appear in the changed-file set, and the one shared dependency (`compute_availability`, which feeds J-12's universe counts) is byte-identical. Acceptable for a tightly-scoped presentation-only change, but the DoD's deterministic-replay line is only partially exercised.

**O1 — OBSERVATION: `start-frontend.sh` staleness trap (deployment tooling, not product code).**
The ux-regression reviewer found the running instance was serving the **pre-iter-20** bundle because `scripts/start-frontend.sh` only rebuilds when its `.next/.qa-serve-base` backend-URL stamp changes, never on frontend-source freshness — the `.next/` build predated all four iter-20 edits and was served silently. Not a source defect (the code is correct once rebuilt); a real risk that a future iteration grades a stale bundle. Already flagged by ux-regression as a non-blocking follow-up (hash/mtime the frontend source into the stamp, or `rm -rf .next` before any QA/audit browser pass). Carried forward, not this iteration's scope.

---

## 3. Domain Assessment

The core domain logic is correct and honest. The Fetch-scope change is a single, well-reasoned wiring line that reuses the exact union (`price_load_symbols`) `load_prices` has used since iter-18/J-12 — it broadens coverage to the full ~588-name set (162 context ∪ 548 pool, minus overlap) without dropping the benchmark/ETF/^VIX/macro context, avoiding the silent-coverage-regression trap the spec called out. The availability data contract is genuinely preserved: the function is untouched and a frozen-output test enforces it, so J-12's cross-page universe counts cannot drift. The market-cap decision is handled honestly — removing Expand removed the only on-demand cap refresh, and the entire cap-refresh copy went with it; the "Candidate universe" tile reads "static" with no refresh claim (live-confirmed), so no fabricated or stale-implying data. The two-signal re-encode correctly separates the two orthogonal facts (price-data density = fill; scored-snapshot exists = ring) that previously shared green/amber encodings, and the copy states each meaning plainly without any prohibited return/price-target/buy-sell language. This is a clean, minimal, local-first change that surfaces its one ambiguity (a full-but-unscored "Backfill gap" day) explicitly rather than hiding it.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT defect was found in the shipped code. The open items (T3/T4/T5, O1) are verification-chain and tooling gaps whose correct remedy is a browser-qa-agent re-dispatch and a follow-up tooling ticket — neither is a surgical code fix, and the product deliverable is already independently verified correct, so applying "fixes" here would be scope creep.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied (no critical/important code defect). |

---

## 5. Recommended Next Step

**Proceed** — the J-13 deliverable is complete and correct. Before the iteration is considered fully closed against its own DoD, re-dispatch the **browser-qa-agent** lane against a freshly rebuilt frontend (the ux-regression reviewer left, or teed up, both prod-mode services; if they are down, `rm -rf apps/frontend/.next` then `start-backend.sh`/`start-frontend.sh` to dodge the staleness trap in O1). That run should capture the three J-13 screenshots the empty evidence dir is missing (`md5sum` them per the hygiene NOTE) and replay J-05/J-10/J-12 live to close T3/T5 with genuine evidence rather than code inspection. File the O1 `start-frontend.sh` freshness-stamp gap as a non-blocking tooling follow-up. None of this blocks the correctness of what was built; it closes the audit trail the DoD asks for.
