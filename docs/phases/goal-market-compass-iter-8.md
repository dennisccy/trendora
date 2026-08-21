# Goal Iteration 8 — J-10 recovery redesign: precommitted path-agreement + stable multiplicative bridge, per symbol

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 8
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: the redesigned gate's correctness depends on the
  interaction between `j10_recovery.py`'s per-symbol orchestration, `yahoo_provider.py`'s fetch/parse
  layer, and the existing `data_manager` fetch-and-insert engine that will perform this session's
  FIRST live write into `daily_prices` — three modules whose interaction a reviewer+QA pass already
  missed once this session (iter-7's B1 fail-open was caught only by the audit lane, on a scenario
  none of the 9 original tests constructed). This independently satisfies trigger 1 in addition to
  matching the evaluator's own binding-by-default recommendation (`full`) for this iteration.
- **Frontend Present:** no
- **Target journeys:** J-10
- **Required-still-passing journeys:** None this iteration — deliberately. See BACKGROUND: J-01–J-04
  re-verification (browser-QA or deterministic replay) is explicitly deferred to iteration 9,
  UNCONDITIONALLY, regardless of whether this iteration's recovery succeeds.
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local
    provider fixtures — no live external network calls or paid data services without an explicit
    goal.md amendment. *(critical)*
    - **Dated exception (owner, 2026-08-20 — single-use, self-closing, incident response):** the
      bounded recovery fetch defined by J-10 is authorized for exactly two calendar dates,
      2026-08-11 and 2026-08-12, and only for the symbol/row scope proven missing as a consequence
      of the iter-5 drill. It authorizes nothing else: no other date (in particular nothing on or
      after 2026-08-13), no refresh of unaffected historical data, no replacement of valid existing
      rows, no broad backfill, no advancement of the dataset to a newer market-data frontier, no
      change to candidate thresholds or research logic, and no unrelated data repair. The intent is
      state restoration only, not dataset advancement. If the implementation cannot prove a request
      stays inside this scope, it MUST stop rather than broaden the fetch. The exception is
      exhausted the moment J-10's post-recovery verification passes — normal AG-9 then applies
      again automatically, and any later live fetch, including of these same two dates, requires a
      new dated goal.md amendment. The only retry permitted under this exception is a re-run of the
      same bounded, idempotent recovery after a failed or partial attempt, still confined to the
      proven missing set. This is not a standing "recovery fetch allowed" path.
    - **Vendor addendum (owner, 2026-08-20, after iteration 6's Stooq block):** the exception's
      vendor is widened from `stooq` to **`stooq` or `yahoo`**, and to no other provider. It
      additionally covers the **read-only comparison fetch** defined in J-10 step 2a — a small
      overlap window of already-surviving days, held outside the database, used solely to prove the
      adjustment convention matches, never written and never used to repair anything. Every other
      bound is unchanged (the same two dates, the same proven-missing rows, fail-closed, idempotent,
      self-closing on verification). A third vendor requires a new dated amendment.
  - **AG-17 — Repair never rewrites provenance (owner, 2026-08-20):** restoring deleted historical
    data MUST NOT retroactively change research provenance. A manifest that was retrospective or
    ineligible stays that way; `prospective_eligible` is never upgraded merely because historical
    data was later repaired; `available_at_utc`, manifest versions, `content_hash`/`manifest_hash`,
    and prior eligibility classifications remain immutable (AG-12 governs the rows and files
    themselves). Any manifest or artifact produced while the database was known to be damaged —
    everything dated from the iter-5 drill until J-10's post-recovery verification passes — remains
    marked unusable as prospective/out-of-sample evidence; only a separately regenerated artifact,
    minted after verified recovery under the existing create-once and version rules, may carry
    eligibility, and it remains subject to the same version and `prospective_eligible` contract as
    any other artifact. The incident record itself is evidence: the iter-5 drill result, its
    handoff, the reviewer/QA evidence already produced, and the explicit statement that the
    committed seed could not restore these dates MUST NOT be deleted, rewritten, or silently
    superseded. Repairing the database never rewrites historical causality. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file
    are never mutated or deleted by any later ingest, rebuild, data removal, config change, or code
    change; corrections happen only as new version rows; a historical view never substitutes a newer
    manifest. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use
    bars > as-of; the manifest for close D derives only from state stored at or before D; never
    introduce lookahead anywhere. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never
    crash an existing page or exhaust memory — consumers of widened fields are re-validated, the UI
    degrades gracefully (contained error boundary, honest "—"/NA placeholder), and unbounded
    whole-table ORM loads are forbidden (the delta engine reads column-projected selects, never full
    record_json sweeps). *(critical)*

## GOAL

Rebuild J-10's fail-closed adjustment-convention gate to the owner's redesigned per-symbol
contract — precommitted path-agreement plus a stable multiplicative bridge measured and applied on
one series end to end, with persisted per-pair evidence and non-overridable thresholds — then run
the gated recovery for real, honestly restoring whichever proven-missing symbols pass and naming the
rest as not-restored.

## BACKGROUND

The owner rewrote J-10 step 2a in `docs/goal.md` *after* iteration 7's real run produced a
technically-correct-but-uninformative "mismatch" on two oil-dividend names (CVX/XOM, deltas uniform
within-symbol across all 5 window days — the signature of a stale-adjustment offset, not a
convention disagreement). The absolute-level tolerance test is superseded entirely by a two-part
test that is invariant to that kind of uniform offset: (1) **path agreement** — compare the two
series' *shape* (day-over-day returns, or each rebased to 1.0 at the window's earliest date), and
(2) a **stable multiplicative bridge** — the per-symbol ratio of stored-to-fallback value across the
window, passing only if its dispersion is within a precommitted bound; that stability IS the
agreement evidence, and a passing bridge must then be *applied* (never a raw insert) to all four
price fields. Both thresholds must be fixed in code before the comparison runs and never adjusted
afterward. This is now fail-closed **per symbol**, not one aggregate verdict gating the whole 587.

This iteration also closes three findings iteration-state's "Active blockers" names explicitly as
**"close in the same turn"**, all from `docs/handoffs/goal-market-compass-iter-7-audit.md`:
- **B2 (one series, end to end):** iter-7's gate validated Yahoo's `get_adjusted_close` (`adjclose`)
  while the unchanged restore path would have written `get_daily`'s raw `quote.close` —
  quantities the developer's own probe measured ~0.086% apart on AAPL. A bridge calibrated across
  that gap silently encodes it as if it were the bridge factor. **Whichever Yahoo series
  calibrates a symbol's bridge MUST be the exact same series (same method, same field) used to
  fetch that symbol's two recovery-date bars.** This is the single most important constraint this
  iteration must not violate — see NOTES for a possible simplification.
- **B3 (persisted per-pair evidence):** iter-7's 88 comparisons were never written to a file (only
  prose, which didn't even reconcile: 4+4+5+76=89≠88). Every live comparison run MUST serialize its
  full per-pair record (`ConventionCheckPair`-shaped: symbol, date, stored value, fallback value,
  ratio/delta) to a run artifact **before** any verdict is interpreted or acted on. That artifact,
  not prose, is the sole admissible calibration input.
- **B5 (non-overridable thresholds):** `run_gated_recovery` currently exposes
  `convention_tolerance`/`convention_sample_symbols`/`convention_window_dates` as caller-settable
  parameters, so "precommitted" lives in operator discipline, not code. Remove that override
  surface from the production entry point.

**Carry forward, do not regress:** iter-7's B1 fix (the minimum-evidence floor — "agree" requires a
non-empty, fully-covered comparison, evaluated *after* the mismatch branch so a genuine
out-of-tolerance pair is never downgraded) must survive into the per-symbol redesign, in its
per-symbol form. `RECOVERY_SYMBOLS` (587, MNST excluded) and `RECOVERY_SOURCE = "yahoo"` are settled
— read unchanged, never re-derived.

**Why full depth, explicitly (Full trigger 1):** see the metadata block above. This also matches the
iter-7 evaluator's own binding recommendation for this iteration (`full`) — both independently
support the same depth, so no escape-condition analysis is needed beyond stating the trigger.

**Applying prior lessons directly:**
- *iter-7 lesson (minimum-evidence floor + degenerate-input testing):* "a guard is only proven
  fail-closed when a test constructs the degenerate input the guard will actually meet in
  production... all nine [prior] tests seeded a complete fixture." Applied here: the new per-symbol
  tests must include a symbol with zero comparable pairs, a symbol with partial coverage, and a
  symbol that fails only path-agreement (not bridge-dispersion) and vice versa — not just
  fully-populated happy-path fixtures.
- *iter-6 lesson (depth-dispatched vs. spec Depth line):* the evaluator checks
  `runs/goal-session-market-compass/iter-8/depth-dispatched` against this spec's own `Depth: full`
  line before trusting any merged results file. Carried as a DEFINITION OF DONE item again.

**Deliberate scope decision — J-01–J-04 re-verification stays OUT of this iteration, unconditionally,
even if recovery succeeds.** The dispatching coordinator's context permits planning browser-QA for
J-01–J-04 "unless the recovery actually completes and verifies first" — but a goal-mode spec is fixed
before dispatch, and the browser-QA/replay lane is driven mechanically by this spec's
Target/Required-still-passing/TESTING REQUIREMENTS fields; there is no way to make a named journey's
lane conditional on an earlier step's runtime outcome within one spec. Naming J-01/J-04 in
Required-still-passing would trigger deterministic replay against the database regardless of whether
J-10 actually finished restoring it by then — exactly the "QA lane ran against a database whose
damage status was still being determined" failure this session has already hit twice (iter-2,
iter-6). This repeats iter-7's own decomposer reasoning (`assumptions.md` iter-7 entry) for the same
reason; logged again below since it deviates from a literal reading of this iteration's dispatch
context.

**Expect a partial outcome, and that is acceptable.** AG-9's addendum authorizes the comparison
fetch for "a SAMPLE of the proven-missing symbols," while the redesigned gate is fail-closed *per
symbol*. Read together: only symbols actually included in the comparison sample can ever accumulate
enough evidence to pass; every un-sampled symbol is automatically "not restored" for lack of
evidence, not because it failed a test. A live run that restores some but not all of the 587 —
or, honestly, restores none if the sampled symbols don't hold up — is a valid, complete iteration
result, matching this session's established pattern (iter-4 J-09, iter-6, iter-7 all recorded
honest partial/zero outcomes without that being treated as an iteration failure).

**Housekeeping note, likely resolved:** the last two evals flagged "`docs/goal.md` amendment still
uncommitted" as an open item. Current `git status` shows `docs/goal.md` clean (not modified) against
HEAD `f6c31afc` ("owner resource-fit amendments after 2026-08-20 desktop-freeze incident"), and the
goal-slice this spec was written from already contains the full redesigned J-10 step 2a text — so
this item appears resolved. Not re-flagged as open below; the evaluator should confirm.

## IN SCOPE

### Backend
- [ ] `apps/backend/app/engine/j10_recovery.py`: replace the single-tolerance, aggregate-verdict
  `check_adjustment_convention` with the two-part, PER-SYMBOL gate J-10 step 2a now specifies — (a)
  path agreement (series-shape comparison over the overlap window) and (b) a stable multiplicative
  bridge (per-symbol stored/fallback ratio, passing only within a precommitted dispersion bound).
  Both new threshold values are module-level literals, fixed before this iteration's live run and
  never adjusted afterward (same discipline as the superseded `CONVENTION_CHECK_TOLERANCE`). Extend
  this SAME module — do not create a second recovery path.
- [ ] Per-symbol verdict ladder: a symbol passes only if BOTH parts pass; a symbol failing either
  part, or with too few comparable pairs to judge (including zero), is `not restored` and named on
  a "requested but not restored" list with its reason. Carry the iter-7 B1 minimum-evidence floor
  into this per-symbol form, evaluated after the disagreement branch so a genuine mismatch is never
  downgraded to "insufficient evidence" by a coverage gap elsewhere in the batch.
- [ ] Resolve B2 ("one series, end to end"): whichever Yahoo series/method calibrates a symbol's
  bridge MUST be the exact same series/method used to fetch that symbol's two recovery-date bars —
  one code path, no crossover between an adjusted comparison series and a raw insertion series (or
  vice versa). Extend `apps/backend/app/data_providers/yahoo_provider.py` only if a new capability
  is needed to keep the two aligned (see NOTES for a possible simplification that needs no new
  provider method at all).
- [ ] Apply a passing symbol's bridge factor to all four price fields (open/high/low/close) of its
  fetched recovery-date bars before insert — never insert a raw fallback value unchanged; volume is
  never scaled (goal.md is explicit: "volume is not a price and is not scaled").
- [ ] Resolve B3: every live comparison run persists its full per-pair evidence (symbol, date,
  stored value, fallback value, computed ratio/delta) to a run artifact under
  `runs/goal-market-compass-iter-8/`, written BEFORE the run's verdicts are interpreted or acted on.
  This artifact is the sole admissible input to bridge calibration — no number from prose/handoff
  text may be used as calibration evidence.
- [ ] Resolve B5: remove the tolerance/dispersion-bound/sample/window override parameters from the
  production (non-test) recovery entry point — a caller cannot pass a looser threshold with no code
  diff to review. Tests may still inject symbols/window/fake providers for determinism; the
  acceptance THRESHOLDS themselves stay fixed module constants on the real driver path.
- [ ] Cheap, audit-recommended (B6): add a defence-in-depth assertion at the transforming insert
  that every written bar's date falls inside `[RECOVERY_START, RECOVERY_END]` — cheap insurance now
  that this path transforms values before writing, where a bug would be easy to miss.
- [ ] Execute the redesigned, gated recovery for real against `data/trendora.db`: compute path
  agreement + bridge for the comparison sample of still-missing symbols; for each passing symbol,
  fetch and bridge-transform its two recovery-date bars and insert them through the existing
  `data_manager` fetch engine (no second write path); rebuild derived `ScannerRun` snapshots for
  the two dates through the existing, unchanged `run_bounded_recovery_backfill`; record full
  provenance (provider, dates, per-symbol restored vs. not-restored with reasons, timestamps,
  pre/post row counts, resulting frontier) in `data_provider_runs` plus the dev handoff's dated
  section per J-10 step 4. A zero-symbols-passing outcome is a valid, honest result: insert
  nothing and stop for owner review (same discipline iter-6/iter-7 established).
- [ ] Execute J-10 step 5's verification checks (a)–(f) directly — read-only DB queries plus a
  direct `GET /api/compass?as_of=2026-08-12` call against a single, transiently-started backend
  (never the browser-QA pipeline lane) — and record every result in the dev handoff, honestly,
  regardless of outcome. If all pass, record AG-9's exception as exhausted per step 6; if not,
  record the honest stop instead.
- [ ] `apps/backend/tests/test_j10_recovery.py`: restructure the convention-check tests for the
  per-symbol, two-part verdict (constructing genuinely degenerate per-symbol inputs — zero pairs,
  partial coverage, path-agreement-only failure, bridge-only failure — not just complete fixtures),
  add tests for the persisted-evidence artifact and the bridge-application transform, and confirm
  the 27 pre-existing tests still pass (renamed/restructured only where the redesign requires it,
  with the reason documented).
- [ ] Add the missing synthetic-payload unit tests for `_parse_adjusted_close` (and any new parsing
  capability) — chart error, missing result, empty timestamp, absent adjclose/quote block,
  malformed shape, null-cell skip — following the existing
  `test_provider_clients.py::test_yahoo_error_payload_raises` pattern (resolves T2).
- [ ] Dev handoff `docs/handoffs/goal-market-compass-iter-8-dev.md` documents: the two precommitted
  thresholds and their basis (chosen before the live run), the comparison sample, the persisted
  per-pair artifact's location, every symbol's verdict and (if not-restored) reason, the
  fetch/backfill outcome, the full step-4/step-5 checklists, and an explicit statement that a
  successful restoration is not evidence of Yahoo/Stooq interchangeability generally.

### Frontend
None — J-10 has no UI surface (goal.md: "Walkthrough: waived — data-layer repair with no UI surface
change of its own").

### New user-facing capability
None this iteration.

### New information displayed
None this iteration.

### New user actions
None this iteration.

### UI surface changes
None this iteration.

### Product surface delta
None visible to a user in the general case. IF enough symbols restore to support a valid scanner
run for 2026-08-12, `GET /api/compass?as_of=2026-08-12` (an existing endpoint) may stop 400ing — a
pre-existing surface returning to its intended behavior, not a new one. A PARTIAL restoration
(fewer than the ~541-member universe) may leave that endpoint still degraded or still 400ing; record
whichever is actually true rather than assuming success.

### Blueprint conformance
No new surfaces. J-10 has no Information Architecture home (data-layer repair only, "Walkthrough:
waived") and is not listed in `runs/goal-session-market-compass/state/blueprint.md`'s Feature/journey
homes table, consistent with J-09 (also backend-only). No blueprint edit made this iteration —
nothing to register.

### Data-contract additions
None. No new displayed value, endpoint, or computing module. This iteration repairs INPUT rows in
the pre-existing `daily_prices` table (not itself a Data-Contract row — it is the raw input every
listed computing module already reads unchanged) through the single existing
`data_manager.run_data_job`/`create_job`/`validate_job_request` write path, which iter-6's coherence
audit already confirmed has no second implementation anywhere in the codebase
(`grep -rln "run_data_job\b" apps/backend/app` → exactly `data_manager.py` + `j10_recovery.py`). The
new per-pair evidence artifact and per-symbol verdict are internal orchestration state, never served
by any endpoint or displayed to a user (mirrors iter-7's coherence finding on the prior verdict
object) — not a Data Contract row.

## OUT OF SCOPE

- J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09 — no code changes, no re-verification, no
  browser-QA or deterministic-replay lane against any of them this iteration. J-01–J-04's
  browser-lane re-check is explicitly deferred to iteration 9 (see BACKGROUND), UNCONDITIONALLY,
  independent of this iteration's recovery outcome.
- Retrying Stooq, attempting to defeat its bot challenge, or using any third vendor — AG-9's
  exception covers only `stooq` or `yahoo`; a third vendor needs a new dated amendment.
- Re-deriving or re-litigating `RECOVERY_SYMBOLS` (587, MNST still excluded) — settled, "Do not
  redo" work. MNST inclusion stays an open, non-blocking owner question.
- Widening the comparison sample toward all 587 symbols specifically to chase more restored
  coverage AFTER seeing an early result — a precommitted sample size, chosen once before running,
  is fine; iteratively expanding it after seeing which symbols pass/fail is the same
  forced-pass anti-pattern the tolerance-widening prohibition already forbids, applied to sample
  scope instead of a threshold.
- Any `config.yaml` change — the `yahoo` catalog entry already exists (`needs_key: false`, already
  `default_source`); no provider-catalog or tunable edit is needed.
- Any new database column or a second provenance framework — J-10 step 4 forbids one; existing
  `data_provider_runs.provider` plus the dev handoff satisfy the provenance requirement.
- Destructive-drill isolation/sandbox infrastructure — goal.md Constraints record this as a deferred
  defect, explicitly not this cycle's build.
- Deleting, rewriting, or reusing `reports/qa/goal-market-compass-iter-6-evidence/` — quarantined
  under AG-17, left exactly as-is.
- Starting the frontend, or starting more than one backend process at a time. A second goal-mode
  engine may be active on this host, which froze once already from two concurrent backends.
- Any claim, anywhere (code, docstrings, dev handoff), that a successful cross-vendor restoration
  proves Yahoo and Stooq bars are interchangeable — AG-9 step 2a forbids this explicitly.
- Upgrading any `next_session_manifests` row's `prospective_eligible` flag as a consequence of this
  recovery — AG-17 forbids retroactive eligibility upgrades; only a separately regenerated artifact,
  minted after verified recovery, may ever carry eligibility, and that is not this iteration's work.
- Committing recovery work anywhere but the `goal/market-compass` branch (`main` is not touched).

## DEFINITION OF DONE

- [ ] The two-part gate (precommitted path agreement + stable multiplicative bridge) is built in
  `j10_recovery.py`, evaluated PER SYMBOL, with both thresholds fixed as module literals before any
  live run and never adjusted afterward (TC-1 through TC-6)
- [ ] Every live comparison run persists its full per-pair evidence to a run artifact under
  `runs/goal-market-compass-iter-8/` before any verdict is interpreted or acted on (TC-7) —
  resolves B3
- [ ] A passing symbol's bridge factor is applied to all four price fields (open/high/low/close) of
  its fetched recovery-date bars before insert; volume is never scaled; no raw fallback value is
  ever inserted unchanged (TC-8)
- [ ] The series measured for calibration and the series fetched for restoration are the same
  provider method/field, symbol by symbol — no crossover (TC-9) — resolves B2
- [ ] The precommitted tolerance and dispersion bound are not parameters on the production recovery
  entry point — a caller cannot override them (TC-1) — resolves B5
- [ ] The live gated recovery runs for real against `data/trendora.db`; the honest per-symbol
  outcome (zero, partial, or full restoration among the sampled symbols) is recorded, with every
  non-restored symbol named and reasoned on a "requested but not restored" list (TC-10, TC-11,
  TC-12)
- [ ] `RECOVERY_SYMBOLS` (587, MNST excluded) and `RECOVERY_SOURCE` ("yahoo") are read unchanged —
  not re-derived, not re-litigated (TC-14)
- [ ] J-10 step 5's verification (a)–(f) is executed directly by the developer (read-only DB
  queries + a direct `GET /api/compass` call) and recorded in the dev handoff; this does NOT invoke
  the browser-QA or deterministic-replay pipeline lane (TC-13)
- [ ] If step 5 verification passes, AG-9's exception is recorded exhausted per step 6; if it does
  not, the honest stop is recorded instead — never a forced/assumed success
- [ ] AG-17 holds: no `next_session_manifests` row's `prospective_eligible`/version/hash changes as
  a result of this iteration; the incident record (iter-5/6/7 handoffs) stays byte-unchanged
  (TC-15)
- [ ] No wording anywhere (code, comments, docstrings, dev handoff) claims Yahoo/Stooq
  interchangeability or vendor-equivalence
- [ ] `_parse_adjusted_close`/new-parser synthetic-payload tests exist and pass, one per failure
  branch (TC-16) — resolves T2
- [ ] All 27 pre-existing `test_j10_recovery.py` tests (restructured where the per-symbol redesign
  requires, with reasons documented) plus this iteration's new tests pass via the single targeted
  pytest file invocation (never the full suite) (TC-17)
- [ ] No browser-QA or deterministic-replay lane runs against J-01, J-02, J-03, or J-04 this
  iteration, regardless of the recovery's outcome (TC-19)
- [ ] Coherence check confirms no new displayed value/endpoint/route/second write path was
  introduced (TC-18)
- [ ] `reports/qa/goal-market-compass-iter-6-evidence/` remains byte-unchanged
- [ ] `runs/goal-session-market-compass/iter-8/depth-dispatched` reads `full`, matching this spec's
  own `Depth: full` line (the evaluator checks this explicitly per the standing iter-6 lesson)
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-8-dev.md`

## TESTING REQUIREMENTS

- Browser: none. J-10 has no UI surface (walkthrough waived). No browser-QA runs against J-01–J-04
  this iteration — deferred to iteration 9 unconditionally (see BACKGROUND/OUT OF SCOPE).
- Unit/integration: `apps/backend/tests/test_j10_recovery.py` (restructured + new tests, fixture-
  scoped, synthetic data, no live network in the automated suite) run via the targeted single-file
  pytest invocation this project always uses for pipeline agents (never the full suite). The real
  recovery attempt against `data/trendora.db` is executed directly (a small standalone script making
  the same `Session`/`Engine` calls the tests use, mirroring iterations 6–7) — not part of the
  automated pytest suite.
- Error cases: a sampled symbol with zero comparable pairs; a sampled symbol with partial coverage
  (below the minimum-evidence floor); a symbol failing path-agreement only; a symbol failing
  bridge-dispersion only; a provider failure mid-sample; a caller attempting to pass a
  tolerance/dispersion-bound override on the production path (should not exist as a parameter); a
  symbol requested outside `RECOVERY_SYMBOLS` (including MNST, explicitly — existing
  `RecoveryScopeError` guard, regression-tested not rebuilt); a second/idempotent invocation after a
  partial or complete prior attempt re-requesting only what is still missing.

Test-first contract — TC- scenarios (numbered sequentially; each maps to a DEFINITION OF DONE item):

- TC-1: given the redesigned gate's path-agreement tolerance and bridge-dispersion bound, when they
  are defined, then both are module-level literals fixed before this iteration's live comparison
  run — never adjusted afterward — and neither is an argument accepted by the production
  (non-test) recovery entry point.
- TC-2: given a sampled symbol whose per-day stored/fallback ratio across the overlap window has a
  dispersion within the precommitted bridge-dispersion bound AND whose rebased/day-over-day-return
  series matches the stored series within the precommitted path-agreement tolerance, when the
  two-part check evaluates that symbol, then its verdict is "agree" and its recorded bridge factor
  equals the computed stable ratio.
- TC-3: given a sampled symbol whose bridge-ratio dispersion exceeds the precommitted bound, when
  the check evaluates that symbol, then its verdict is "mismatch", it is excluded from the fetch,
  and it is recorded on the "requested but not restored" list with its measured dispersion cited.
- TC-4: given a sampled symbol whose day-over-day-return/rebased-series comparison exceeds the
  precommitted path-agreement tolerance even though its bridge-ratio dispersion is low, when the
  check evaluates that symbol, then its verdict is still "mismatch" — passing only one of the two
  required tests is insufficient.
- TC-5: given a sampled symbol with fewer comparable pairs than the precommitted minimum-evidence
  floor (including zero), when the check evaluates that symbol, then its verdict is "inconclusive"
  — never "agree" — regardless of how well the few available pairs happen to agree.
- TC-6: given one symbol that genuinely fails the mismatch branch and a second symbol in the same
  run with too few comparable pairs, when the batch is evaluated, then the first symbol's verdict
  stays "mismatch" (the minimum-evidence floor is evaluated after, and never downgrades, a genuine
  disagreement) — carrying iter-7's B1 fix forward into the per-symbol form.
- TC-7: given any live comparison run, when the check computes its per-symbol verdicts, then a run
  artifact under `runs/goal-market-compass-iter-8/` records every compared pair's symbol, date,
  stored value, fallback value, and computed ratio/delta, written before any fetch/backfill call
  executes.
- TC-8: given a symbol whose verdict is "agree", when its two recovery-date bars are fetched and
  inserted, then the inserted open/high/low/close values equal that date's fallback-provider values
  multiplied by the symbol's bridge factor (within floating-point tolerance), and the inserted
  volume equals the fallback's raw volume, unscaled.
- TC-9: given a symbol's calibration pairs and its restoration-date fetch, when the code path is
  traced, then both read the identical provider method/field for the close value (no crossover
  between an adjusted-series calibration and a raw-series insert, or vice versa) — resolving B2.
- TC-10: given zero sampled symbols pass the two-part gate on the live run, when the recovery
  driver completes, then zero rows are inserted into `daily_prices`/`scanner_runs` (at most one
  honest `data_provider_runs` attempt record), and the dev handoff states the zero-restored outcome
  plainly.
- TC-11: given at least one symbol passes, when the fetch and backfill complete, then
  `daily_prices` gains rows only for the passing symbols on exactly 2026-08-11/2026-08-12, a
  pre/post row-count diff shows zero changes to any other date or symbol, and `ScannerRun`
  snapshots exist for those two dates, built through the existing backfill path.
- TC-12: given the recovery run completes (any outcome), when the dev handoff's provenance section
  and `data_provider_runs` are read, then both name: provider, dates, per-symbol restored vs.
  requested-but-not-restored with reasons, start/completion timestamps, pre- and post-recovery
  missing-row counts, and the resulting frontier date.
- TC-13: given the recovery outcome (any verdict), when J-10 step 5's checks (a)–(f) are executed
  directly by the developer (DB queries + a `GET /api/compass` call, not the browser-QA pipeline),
  then each of the six results is recorded in the dev handoff honestly, including the actual HTTP
  status returned for `as_of=2026-08-12`.
- TC-14: given `RECOVERY_SYMBOLS` (587, MNST excluded) and `RECOVERY_SOURCE = "yahoo"`, when this
  iteration's tests run, then both remain unchanged from the existing module — no new derivation,
  no other vendor attempted.
- TC-15: given AG-17, when the recovery run completes (any outcome), then no
  `next_session_manifests` row's `prospective_eligible`, version, or hash changes (a read-only
  count/hash check before and after matches), and the iter-5/6/7 incident records remain
  byte-unchanged.
- TC-16: given `_parse_adjusted_close` and any new Yahoo parsing capability, when each is fed a
  synthetic chart-error payload, a missing result, an empty timestamp array, a response with no
  adjclose/quote block, a malformed shape, and a null price cell, then each raises
  `ProviderUnavailableError` (or, for the null cell, silently omits that date) exactly as
  documented — one passing test per branch.
- TC-17: given the 27 pre-existing `test_j10_recovery.py` tests, when the full targeted file runs
  after this iteration's changes, then every one still passes (restructured only where the
  per-symbol redesign requires it, with the reason documented), alongside the new tests from TC-1
  through TC-9.
- TC-18: given this iteration's diff, when the coherence-auditor checks the Data Contract and
  Information Architecture, then it confirms no new displayed value, endpoint, route, or computing
  module was introduced, and `run_data_job` remains the single write path (no second insert path
  added).
- TC-19: given J-01, J-02, J-03, and J-04, when this iteration's pipeline completes, then no
  browser-QA or deterministic-replay evidence file for any of the four exists under this
  iteration's QA evidence directory.

## NOTES

- **Possible simplification for B2 ("one series, end to end"), offered — not mandated:** the
  restoration insert already flows through `data_manager.run_data_job` → `provider.get_daily`
  (raw `quote.close`/open/high/low/volume), unchanged since iter-6. The cleanest way to guarantee
  "the same series measured is the same series inserted" without any new Yahoo parsing method is to
  calibrate the bridge on `get_daily`'s RAW close (not `get_adjusted_close`) against the stored
  (Stooq-adjusted) close over the overlap window, then apply that per-symbol bridge factor to
  `get_daily`'s raw open/high/low/close for the two recovery dates — one existing method used for
  both purposes, trivially satisfying "one series end to end." Whether that raw-close bridge is
  actually STABLE (low dispersion) over the window is an empirical question the live run will
  answer; if it is not stable for a symbol, that symbol simply fails and is not restored — a safe
  outcome either way. This is a suggestion, not a requirement: the developer may instead build a
  parallel "adjusted OHLC" capability on `YahooProvider` (deriving open/high/low from the same
  per-day quote/adjclose ratio already available in one chart-endpoint response) if that is judged
  the more correct basis — but whichever is chosen, the SAME series must feed both the check and
  the insert, and the choice plus its empirical basis should be logged to `assumptions.md` by the
  developer (following the session's established pattern for this kind of technical call).
  Reusing the existing `data_manager.run_data_job` insert path (via a bridge-applying provider
  wrapper passed to `run_bounded_recovery_fetch`'s existing `provider=` injection point, or
  equivalent) is very likely the least invasive way to add the transform without creating a second
  write path — worth considering to keep "single write path" intact.
- **Coverage-sufficiency is an open, honestly-reportable question, not an assumption.** Even a
  successful per-symbol gate pass for, say, 20 of 587 symbols would leave `run_bounded_recovery_
  backfill` building a `ScannerRun` snapshot from a badly under-covered universe (~20 of ~541
  members) for 2026-08-12 — plausibly not enough for J-10 step 5(f)'s "J-01/J-02/J-03 replay clean"
  to actually hold — under-coverage, not a gate defect, would be the cause. Record whatever coverage and
  whatever step-5 result actually obtain; do not infer or assume a passing replay from a partial
  restore.
- **Host safety (unchanged from iteration 7):** invoke the real recovery via a small standalone
  script making direct `Session`/`Engine` calls into `j10_recovery` — no running backend needed for
  the core fetch/backfill work. Start a single backend only transiently, for the one step-5(f)
  `GET /api/compass` call, then stop it immediately. Never run two backends concurrently and never
  start the frontend this iteration — a second goal-mode engine may be active on this host, which
  froze once already from two concurrent backends (memory overcommit + swap-thrash, no OOM kill,
  2026-08-20). The comparison fetch adds live Yahoo calls on top of the restoration fetch itself
  (up to ~2x the symbol count in HTTP calls this iteration) — keep the sample modest rather than
  reaching for all 587 in one shot (see OUT OF SCOPE on sample-widening discipline).
- **Carried, low-priority, not this iteration's to fix:** B4 (a `TypeError` in the mismatch reason
  string when every failing pair has a zero stored close — fails closed already, reporting-only;
  fix opportunistically if the per-symbol restructure naturally touches that code, but do not scope
  time to it otherwise).
- **Still-open, non-blocking owner questions, carried forward untouched (none are this iteration's
  to resolve):** whether 3.44 GB is acceptable for J-09; J-06's "underlying run unavailable"
  wording; the J-01 test-step rewording; whether an empty "next-session focus" on the newest date is
  acceptable; and whether MNST should be included in a future recovery attempt.
- **Coordinator path confirmation:** the dispatching coordinator named both
  `apps/backend/app/engine/j10_recovery.py` and `apps/backend/app/data_providers/yahoo_provider.py`
  — both verified correct by direct read this iteration.
- Escalation flag for the evaluator: a partial or zero-restoration outcome on this live run is an
  honest, acceptable result (same as iterations 6–7) — do not read it as a process failure by
  itself. Only a repeat of the depth-demotion/forbidden-lane pattern, a B2/B3/B5 finding left
  unresolved, or a violation of the interchangeability/provenance/AG-17 constraints should weigh
  toward ESCALATE.

