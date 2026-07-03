# goal-mcp-loop-iter-17 Audit Report

**Date:** 2026-07-03
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal — a swap-complete, vendor-disclosed, honestly-sourced staged 30-year seed with ZERO runtime change — is genuinely achieved and was verified in this audit against disk and code, not handoffs: all 7 context CSVs verified on disk with the exact claimed spans and bar counts, proxies byte-identical via `cmp`, staged ⊇ live confirmed by direct set-diff (162 live ⊆ 590 staged), the manifest merge proven strictly additive against `git show HEAD` (583 equity records byte-equal, window pins unchanged, accounting 591/590/1), protected paths and both ledgers zero-diff, and both iteration-critical suites re-run green by this audit (47 + 12 passed). One documented gap keeps this from a clean PASS: the DoD's "full backend suite counts in the handoff" item was satisfied by an honest, documented deferral rather than real full-suite counts — no pipeline stage ran the full 74-file suite (8 files were run, twice, independently). The gap is verification-breadth documentation, not correctness: this audit proved the untargeted suites have no code or data path touched by the diff.

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap): Full-suite counts absent from the dev handoff; no stage ran the full backend suite**
`docs/handoffs/goal-mcp-loop-iter-17-dev.md:149` says "Full backend suite … deferred to the reviewer stage"; the spec's DoD (`docs/phases/goal-mcp-loop-iter-17.md:121`, REMAINING item at `:62`) required the placeholder replaced "with the real full-suite command + counts". The placeholder text itself is gone (grep-verified: no `PLACEHOLDER` in any committed artifact), and the deferral is honest — but the reviewer and QA each ran only 8 of the ~74 test files (`test_ingest_seed.py`, `test_seed_staged_30y.py`, and the 6 DoD suites = 124 tests), so real full-suite counts never landed anywhere.
Why this is a GAP and not IMPORTANT: the regression-proving purpose of the full run is mechanically covered. This audit verified by grep that (a) the changed script `scripts/ingest_seed.py` is imported by NO test other than `tests/test_ingest_seed.py` (the `conftest.py` hit is a docstring only, and conftest is byte-unmodified), (b) the staged tree `data/seed-stooq-30y/` is read only by the two touched test files and the script itself, and (c) `apps/backend/app/**`, `config.yaml`, `data/seed/**`, and both ledgers are byte-identical to HEAD — so the ~66 unrun suites have no mechanism to regress from this diff. Every suite with a plausible connection ran green twice independently (reviewer + QA), and this audit re-ran the two iteration-critical suites green a third time.
Not fixed at audit time, deliberately: producing real full-suite counts would require the monolithic run that killed this iteration's first dispatch and that the operator has directed must not be run from this execution context; fabricating counts is prohibited. Recommendation: iter-18 (which DOES change runtime code) must run the bounded sequential full suite as part of its own DoD, where it is genuinely load-bearing.

**B2 — OBSERVATION: resume-preservation guard slightly exceeds the literal spec bullet list**
`apps/backend/scripts/ingest_seed.py:584` (`planned = max(...)`, plus note/source preservation on resume in `run_stooq_ingest`) changes the existing resume path's behavior so a later, narrower maintenance run cannot shrink `symbols_planned` or erase the iter-17 vendor addendum. Not an itemized spec deliverable, but it directly protects this iteration's committed manifest, is byte-equivalent for real resume flows, and is pinned by `tests/test_ingest_seed.py:1043` (`test_regular_resume_preserves_merged_manifest_provenance`). Justified; no action.

**B3 — OBSERVATION: the staged-tree VIX XOR test cannot structurally detect a hypothetical same-vendor splice**
`tests/test_seed_staged_30y.py:290` proves deep-XOR-verbatim plus continuity (max gap ≤ 14 days, coverage never lost, clipped to the pinned end); a same-vendor splice with small gaps would be invisible to it. Acceptable because the code path makes a splice unreachable: `run_context_merge` (`scripts/ingest_seed.py:817`) stages the WHOLE validated pull or takes the WHOLE verbatim fallback (`_vix_pull_shortfall`, `:779` — a pull failing any check is discarded in full), writes atomically, and the discard behavior is pinned offline by `test_context_merge_shallow_or_stale_pull_falls_back_never_splices` (`tests/test_ingest_seed.py:953`). The committed `_VIX` was additionally verified by the reviewer as byte-value-identical to the live series on all 1,357 overlap dates. No action.

### Frontend Findings

None — `Frontend Present: no`. Zero diff under `apps/frontend/**` (git-verified). The sanctioned N/A stubs for stages 5/6/8 exist (`reports/phase-goal-mcp-loop-iter-17-{ui-surface-map,ui-test-plan,ui-test-results,user-visible-changes,what-to-click}.md`).

### Test Findings

**T1 — OBSERVATION (positive): assertions are tight and failure paths are genuinely exercised**
The staged validation suite pins exact values, not ranges: exact accounting (`symbols_planned == 591`, `ok == 590 == len(symbols)`, `failed == ["SATS"]`), exact vendor map for all 7 context series with per-record disk agreement on bars/first/last (`tests/test_seed_staged_30y.py:332`), byte-equality for proxies, pinned-window equality, equity records proven vendor-free (AAPL check), and the load-bearing superset gate (`:320`). The offline suite exercises FAILURE paths, not just construction: B1 redaction plants a real env key inside a failing pull's URL and asserts the key never persists while `apikey=***` evidence does (`tests/test_ingest_seed.py:1068`); the B2 pow cap asserts both the regression (real difficulty still solves) and the honest capped failure classified as a resumable "gate" (`:1152`, `scripts/ingest_seed.py:314`); refusal guards assert nothing is written (missing/foreign manifest `:980`, window conflict `:1007`, worldless archive `:1109`); pre-1996 clip is proven against a fixture that reaches 1789 (`:776`). The live Yahoo integration test ran green against the real endpoint (dev + reviewer, evidence in the handoff) — anti-pattern #15 satisfied.

---

## 3. Domain Assessment

The core domain risk of this iteration is data integrity of the future basis, and it holds up under direct inspection:

- **No fabrication, no leakage:** `_SPX`/`_NDX`/`_DJI` first bars are 1996-01-02 (the 1789/1938/1896-era archive rows provably clipped — parser-level window filter at `app/data_providers/local_stooq_archive.py:103-106`, fixture-proven), last bars exactly the pinned end 2026-07-01, 7,674 daily bars each (not a monthly relic), no flat-OHLC run > 2 bars. The all-CSV structural sweep (canonical header, strictly ascending unique dates, strictly positive OHLC, volume ≥ 0 — the correct non-negative index rule) covers all 590 files.
- **Honest vendor mix, disclosed at the source of truth:** the merged `meta.json` records `stooq` ×3 / `yahoo` ×1 / `fred-macro-proxy` ×3 with real (possibly short) spans — the proxies honestly record 2026-05-28, never a pretended pinned-end; the note carries the verbatim "a proxy is never presented as a market index" exactly once (idempotency test-pinned). The §H prohibition is honored in code: proxies are byte-copies (`cmp`-verified), never re-fetched from Yahoo.
- **Zero runtime change is real, not asserted:** `git diff` is empty on `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, `data/seed/**`, and both evidence ledgers; the staged tree is read by nothing at runtime; the world-bundle support lives in a script-local subclass (`scripts/ingest_seed.py:370`), keeping the app boot path untouched. Architecture stays local-first and minimal — no new dependencies, no new endpoints, no new module.
- **The iter-18 gate is genuinely load-bearing:** `test_swap_completeness_staged_superset_of_live` asserts the live set is non-empty and staged ⊇ live by filename set-diff — this audit reproduced the same result independently of the test.
- **Anti-goals intact:** zero ledger writes, zero referee submissions, no claim presented as proven, no lookahead surface touched.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | None. No CRITICAL or IMPORTANT issues found; the single GAP (B1) is documented above with the reason it is not auditor-fixable. |

---

## 5. Recommended Next Step

Proceed to **iter-18: the atomic basis swap + sanctioned ledger reset** (depth FULL, dispatchable unattended — the iter-16 STALLED rationale no longer holds). Iter-18 must: (1) verify `test_swap_completeness_staged_superset_of_live` is green at its start; (2) carry the ledger reset atomically with the seed-dir flip per goal.md "Data-basis change"; (3) include the bounded, sequential FULL backend suite run with real counts in its handoff — that iteration changes runtime code, so the full run is load-bearing there and also retires gap B1's documentation debt; (4) expect the +21.34% J-09 edge to face honest re-certification on the new basis.
