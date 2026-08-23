# goal-market-compass-iter-9 Execution Plan

## What to Build
- Extend the J-10 recovery driver (`apps/backend/app/engine/j10_recovery.py`) so the fixed
  per-symbol path-agreement + stable-bridge gate (`check_adjustment_convention_per_symbol` /
  `run_gated_recovery`) runs over the **recovery-population remainder** —
  `still_missing_symbols()`, up to 567 names — as an axis fully distinct from the frozen
  20-name `CONVENTION_CHECK_SAMPLE_SYMBOLS` methodology sample, which stays byte-unchanged and
  is never re-run as a validation exercise (goal.md step 2b's binding invariant). Do not touch
  `RECOVERY_SYMBOLS`, `RECOVERY_DATES`, `RECOVERY_SOURCE`, `PATH_AGREEMENT_TOLERANCE`,
  `BRIDGE_DISPERSION_BOUND`, `MIN_COMPARABLE_PAIRS_PER_SYMBOL`, or
  `CONVENTION_CHECK_SAMPLE_SYMBOLS` — all frozen, read-only.
- Close the three still-open audit gaps on the production entry points:
  1. `run_gated_recovery`'s `evidence_path: Optional[Path] = None` parameter becomes a
     **required** `Path` — no code path may call it without persisting the per-pair artifact
     first.
  2. Add a guard inside `run_gated_recovery` that refuses (raises `RecoveryScopeError` or
     equivalent) when a caller-supplied `fetch_provider`'s source does not match
     `convention_provider`'s source — closing B2's one-series-end-to-end rule at the call
     boundary, not just by docstring. An omitted `fetch_provider` (defaults to
     `convention_provider`) must keep working exactly as today. `PriceProvider` has no
     built-in `source`/name field today (`apps/backend/app/data_providers/base.py`) — the
     developer must add a minimal, non-invasive way to compare provider identity (e.g. a
     `source` attribute on `YahooProvider`/`StooqProvider`, or a type-based check) without
     widening the provider abstraction beyond what this guard needs.
  3. Close the un-gated back door: `run_bounded_recovery_fetch` is independently importable
     and today enforces only scope (dates/symbols/source), not that its symbols passed the
     convention gate. Production code must not be able to reach it with a recovery-scope
     symbol that never passed the bridge transform (an ungated symbol must be refused, not
     silently insertable via a direct call bypassing `run_gated_recovery`).
- Commit a **reproducible entry point** (script or module-level callable, e.g. under
  `apps/backend/scripts/` or as a `if __name__ == "__main__"` block wired to
  `run_gated_recovery`) that drives gate → fetch → backfill for the population pass. Today no
  committed caller of `run_gated_recovery` exists outside `test_j10_recovery.py` — iteration 8's
  real 20-symbol run was ad hoc and irreproducible; this iteration's much larger run must not
  repeat that.
- Run the population pass end to end against the live `apps/backend/data/trendora.db`, mirroring
  iterations 6-8 (outside the pytest suite, via the committed driver): for each symbol in
  `still_missing_symbols()` (the live remainder, excluding the 20 already restored) get exactly
  one verdict (`agree` / `mismatch` / `inconclusive`); `agree` → fetch + bridge-transform +
  idempotent insert of both recovery-date bars; `mismatch`/`inconclusive` → zero rows, symbol +
  reason recorded on the "requested but not restored" list. Persist the full per-pair evidence
  artifact (mandatory `evidence_path`, under `runs/goal-market-compass-iter-9/`, mirroring
  `runs/goal-market-compass-iter-8/j10-convention-evidence.json`) **before** any verdict drives a
  fetch/insert decision.
- Record provenance in `data_provider_runs` (existing convention, no new framework) and a dated
  section of the dev handoff: dates, provider (`yahoo`), restored/not-restored-with-reason lists,
  timestamps, pre/post missing-row counts.
- Verify the raw-layer outcome via **direct read-only DB/provenance checks only** — J-10 step
  5(a)-(f): expected coverage restored for both dates; no other date touched; no survivor
  overwritten; frontier unchanged at 2026-08-12; integrity checks pass; the destructive condition
  is gone. Where a check would otherwise require starting the backend, either find a read-only
  equivalent or fully reconcile and disclose every mutation the check itself causes (step 5a —
  iteration 8's own precedent: backend boot warmup incidentally created a 2026-05-12 `ScannerRun`
  during verification and it had to be classified, not hidden).
- Record in the dev handoff whether AG-9's dated exception is exhausted (step 6) — `true` only if
  every `RECOVERY_SYMBOLS` member reaches a final restored-or-classified-unrestorable state this
  iteration; otherwise `false`/not-yet-exhausted, with the exact named residual and per-symbol
  reason if any genuine external blocker (e.g., a Yahoo outage on a specific symbol) prevents full
  completion — never an invented partial-completion threshold.
- Add/extend file-scoped unit tests in `apps/backend/tests/test_j10_recovery.py` (and
  `apps/backend/tests/test_provider_clients.py` only if the provider-mismatch guard touches
  provider construction) covering the three closed gaps on synthetic fixtures built from the
  actual degenerate conditions named in TC-6/TC-7/TC-8 (missing `evidence_path`, mismatched
  `fetch_provider`/`convention_provider` source, a direct ungated call to
  `run_bounded_recovery_fetch`), plus population-pass behavior (idempotent skip of the 20 already
  restored, per-symbol independence, zero-write on mismatch/inconclusive).
- Write the dev handoff at `docs/handoffs/goal-market-compass-iter-9-dev.md` with a dated
  provenance section, the mutation-reconciliation table (every DB write this iteration's own
  verification caused, classified authorized-recovery vs. incidental-product), and an explicit
  statement that any population-scale near-1.0 bridge-factor result is still a Yahoo-vs-Yahoo
  comparison (per iter-8's audit correction C1), never cross-vendor validation evidence.

## Out of scope (do not build)
- J-11 (clean derived-state regeneration) in any form — no `ScannerRun`/snapshot clearing, no
  `next_session_manifests` touch, no cache invalidation.
- Re-fetching, overwriting, or reverting the 20 symbols iteration 8 already restored.
- Widening any frozen constant (`RECOVERY_SYMBOLS`, `RECOVERY_SOURCE`,
  `CONVENTION_CHECK_SAMPLE_SYMBOLS`, thresholds) or including MNST.
- A third data vendor under any condition.
- Starting the backend or frontend for anything a read-only DB/provenance check can answer.
- Any browser-QA-agent execution or deterministic-replay lane, for any journey (J-01-J-08
  included) — the standing lane gate stays shut until J-11 Stage G. This is enforced by this
  session's `Maintenance isolation: required` marker; no pipeline step in this iteration should
  boot shared services, run demo.sh, or dispatch browser-qa-agent.
- Any mutation of `reports/qa/goal-market-compass-iter-8-evidence/` — byte-preserved.
- Full pytest suite — targeted `test_j10_recovery.py` / `test_provider_clients.py` only.
- Any change to `main` — stays on `goal/market-compass`.

## Agents Required
- backend-data: yes -- extend `j10_recovery.py`'s gating/guard logic, add the committed driver
  entry point, run the real population-scale recovery against `data/trendora.db`, add/extend
  file-scoped tests, write provenance + the dev handoff.
- frontend-ux: no -- J-10 has no UI surface (walkthrough waived per goal.md); no frontend file is
  in scope this iteration.

## Frontend Present
no

## Maintenance Isolation
required -- this is a raw-layer maintenance iteration (see phase spec metadata:
`Maintenance isolation: required`). Full reviewer/QA/audit scrutiny still applies, but backend
boot, frontend boot, browser QA, deterministic replay, and demo generation are forbidden until
J-11 Stage G. All verification in this iteration must be direct, read-only DB/provenance checks
(sqlite queries, file hashes, provenance table reads) — never a running service. If any check
genuinely cannot avoid starting the backend, every write that boot causes must be detected,
classified, and disclosed per step 5a — never waved through as "no out-of-scope writes."

## Files to Create/Modify
- `apps/backend/app/engine/j10_recovery.py` -- population-pass extension over
  `still_missing_symbols()`; `evidence_path` made required on `run_gated_recovery`; add the
  `fetch_provider`/`convention_provider` source-mismatch guard; close the `run_bounded_recovery_fetch`
  un-gated back door.
- `apps/backend/app/data_providers/base.py` and/or `yahoo_provider.py`/`stooq_provider.py` --
  only if a minimal provider-identity field (e.g. `source`) is needed to implement the mismatch
  guard; keep this addition small and non-invasive.
- A new committed driver entry point (script or module-level `main`, e.g.
  `apps/backend/scripts/run_j10_population_recovery.py` or equivalent) -- reproducible caller of
  `run_gated_recovery` for the population pass; must be idempotent on re-run.
- `apps/backend/tests/test_j10_recovery.py` -- new tests for the three gap closures (TC-6/TC-7/TC-8)
  and population-pass behavior (idempotent skip of restored 20, per-symbol independence,
  zero-write on non-agree verdicts).
- `apps/backend/tests/test_provider_clients.py` -- only if the mismatch guard touches provider
  construction/identity.
- `runs/goal-market-compass-iter-9/j10-population-evidence.json` (or similar name under this
  iteration's runs dir) -- mandatory persisted per-pair evidence artifact for the population batch.
- `docs/handoffs/goal-market-compass-iter-9-dev.md` -- dev handoff: provenance section, mutation
  reconciliation, AG-9 exhaustion statement, restored/not-restored-with-reason lists.

## UI Evolution
N/A -- no frontend surface this iteration (Frontend Present: no).

## Visual Requirements
N/A -- no frontend surface this iteration (Frontend Present: no).

## Key Test Scenarios
- TC-1: every symbol in the live `still_missing_symbols()` set at iteration start ends with
  exactly one recorded verdict in the persisted evidence artifact — none silently unattempted.
- TC-2: every `agree` verdict produces exactly one row per recovery date for that symbol, each
  OHLC field equal to the fallback value times the recorded bridge factor, volume unscaled.
- TC-3: every `mismatch`/`inconclusive` verdict produces zero rows for that symbol and a named,
  reasoned entry on the "requested but not restored" list.
- TC-4: the 20 symbols iteration 8 already restored are excluded from this iteration's request
  (no network call for them); their 40 stored rows are byte-identical before and after.
- TC-5: a request naming a date outside {2026-08-11, 2026-08-12}, a symbol outside
  `RECOVERY_SYMBOLS`, or a source other than `yahoo` is refused by `validate_recovery_scope`
  before any network call or DB write.
- TC-6: a call to `run_gated_recovery` omitting `evidence_path` is refused before any convention
  check or fetch runs (constructed as an actual missing-parameter test, not a happy-path fixture).
- TC-7: a call to `run_gated_recovery` with a `fetch_provider` whose source mismatches
  `convention_provider`'s is refused before any fetch; an omitted `fetch_provider` still proceeds
  normally (regression guard).
- TC-8: a direct call to `run_bounded_recovery_fetch` for a symbol with no passing bridge factor
  on record is refused — the back door cannot insert an untransformed row.
- TC-9: the committed recovery driver, re-run against the post-iteration DB state, is a verified
  zero-write no-op.
- TC-10: every DB write this iteration's own verification causes (including any incidental
  `ScannerRun`/derived-row creation from unavoidable backend boot) is classified as authorized
  recovery write vs. incidental product write and disclosed — never silently claimed
  side-effect-free.
- TC-11: `runs/goal-session-market-compass/iter-9/depth-dispatched` reads `full`; no browser-QA
  or deterministic-replay evidence file for J-01-J-08 exists under this iteration's QA evidence
  directory.
- TC-12: `data_provider_runs` and the dev handoff's provenance section agree on provider, dates,
  restored/not-restored-with-reason lists, timestamps, and pre/post missing-row counts.
- TC-13: the dev handoff's AG-9 exception-exhaustion statement reads `true` only if every
  `RECOVERY_SYMBOLS` member reaches a final restored-or-unrestorable status this iteration, else
  `false`.
- TC-14: all commits stay on `goal/market-compass`; `main` unchanged.
- TC-15: `test_j10_recovery.py` and `test_provider_clients.py` (targeted, single-file pytest
  invocation) pass with zero regressions, including the new gap-closing tests.
- TC-16: a read-only count/hash check of `next_session_manifests` before/after shows no row's
  `prospective_eligible`, version, `content_hash`, or `manifest_hash` changed; a checksum sweep of
  `reports/qa/goal-market-compass-iter-8-evidence/` shows every file byte-unchanged.

## Notes for downstream agents
- A second `run-goal.sh --session-id market-compass --resume` process may be running concurrently
  on this host (flagged in the phase spec NOTES as an operational-safety concern, not a spec
  requirement) — this iteration performs a large, non-reversible live-network write; confirm a
  single engine instance drives the actual fetch/backfill before it starts, if practical.
- Do not read `.claude/architecture/*.md` (framework reference only, not project state) — already
  excluded from this plan's inputs per orchestrator instructions.
- iter-8's audit correction (C1) is binding context: a near-1.0 bridge factor across the
  population batch is a **Yahoo-vs-Yahoo** result (the stored overlap-window bars are Yahoo's, not
  Stooq's) — safer, but not cross-vendor validation. State this explicitly in the handoff rather
  than implying otherwise (iter-8's lesson, cited in the phase spec BACKGROUND).
