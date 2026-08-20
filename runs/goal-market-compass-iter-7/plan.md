# goal-market-compass-iter-7 Execution Plan

## What to Build
- Swap `RECOVERY_SOURCE` in `j10_recovery.py` from the literal `"stooq"` to the literal `"yahoo"` —
  the sole vendor authorized for this retry (goal.md AG-9 vendor addendum: `stooq` or `yahoo`, no
  other provider). Stooq stays permanently excluded from this retry; do not retry it, do not attempt
  to defeat its JS proof-of-work challenge, do not add a third vendor.
- Add J-10 step 2a's fail-closed adjustment-convention check, as a new function in the SAME
  `j10_recovery.py` module (extend, never a second recovery path). For a documented sample of ≥ 15
  `RECOVERY_SYMBOLS` over the 5 most recent already-surviving trading days (≤ 2026-08-10), fetch
  Yahoo's **split/dividend-adjusted** series and compare it against the stored `daily_prices` closes
  for the same (symbol, date) pairs, within a documented tolerance (proposed default 0.75% relative
  on close; the developer may set the final value once from observed empirical deltas, recorded in
  the handoff — never iteratively loosened after a borderline/failing result). Return one of exactly
  three evidenced verdicts: `agree` / `mismatch` / `inconclusive` (a provider error must yield
  `inconclusive`, never a false `agree`). The comparison fetch is read-only/in-memory only — never
  written to any table, never cached beyond the call's lifetime.
  - **Load-bearing technical point:** `YahooProvider.get_daily` currently parses
    `indicators.quote[0].close` — Yahoo's plain/raw close — confirmed by direct read of
    `apps/backend/app/data_providers/yahoo_provider.py:258-261`. `daily_prices.close` is
    split/dividend-adjusted (`models.py:101`). Comparing raw-vs-adjusted will produce false
    "mismatch" verdicts for dividend-paying names. The developer must add a small additive capability
    to fetch/parse Yahoo's `indicators.adjclose[0].adjclose` array (e.g. requesting
    `indicators=quote,adjclose`) and use THAT series for the comparison — not reuse `get_daily`
    unmodified. Getting this field right is the entire point of the gate.
- **Sequence the orchestration so the convention check is a genuine gate, not a formality**: it must
  run and return `agree` strictly BEFORE any call capable of writing to `daily_prices`, `scanner_runs`,
  or `data_provider_runs`. A `mismatch` or `inconclusive` verdict — or any fetch failure — must leave
  every one of those tables byte-unchanged and produce an explicit "stopped" outcome; no silent
  partial writes, no exception that leaves state ambiguous. Concretely: the convention-check call and
  its verdict branch must sit textually and causally before the call into
  `run_bounded_recovery_fetch`, with no code path that reaches the fetch/backfill calls on any verdict
  other than `agree`.
- IF (and only if) the check returns `agree`: run the existing (unchanged) `run_bounded_recovery_fetch`
  with `source="yahoo"` against the real `data/trendora.db`, then the existing (unchanged)
  `run_bounded_recovery_backfill`, restoring 2026-08-11 and 2026-08-12 for all 587
  `RECOVERY_SYMBOLS` (MNST stays excluded — this is prior evidence-based judgment, not this
  iteration's to re-litigate). Record `yahoo` provenance in `data_provider_runs.provider`.
- Execute J-10 step 5's verification checks (a)-(f) directly — read-only DB queries plus two direct
  `GET /api/compass` calls against a single, transiently-started backend — and record every result in
  the dev handoff. This must NOT invoke the QA/browser-QA/deterministic-replay pipeline lane (see
  guardrails below). If all six pass, record AG-9's exception as exhausted (step 6). If the check
  returns `mismatch`/`inconclusive` or the fetch fails, record the honest stop instead — do not
  attempt a third vendor, do not retry Stooq, do not treat a second "zero bars restored" outcome as a
  process failure by itself (the spec's own escalation note: this is an acceptable outcome, same as
  iteration 6).
- Update the two now-stale unit tests in `test_j10_recovery.py` (`test_rejects_wrong_source` must now
  assert `"stooq"` is rejected; `test_recovery_constants_shape` must assert
  `RECOVERY_SOURCE == "yahoo"`), and add new fixture-scoped tests for the convention check's three
  outcomes via an injected fake provider — zero live network calls anywhere in the automated pytest
  suite.
- Write `docs/handoffs/goal-market-compass-iter-7-dev.md`: the convention-check sample (symbols +
  dates), per-pair observed deltas, tolerance used and its basis, the verdict, the fetch/backfill
  outcome either way, the full step-4/step-5 checklists, and an explicit statement that a successful
  restoration is not evidence of Yahoo/Stooq interchangeability generally.

## Explicit guardrails (safety-critical — verify, don't just implement)
- **No lane may verify journeys against the still-possibly-damaged dataset before this iteration's
  own recovery verification passes.** J-01, J-02, J-03, J-04 (and J-05-J-09) get NO code changes, NO
  browser-QA run, NO deterministic-replay run this iteration, regardless of whether the recovery
  succeeds — their re-verification is iteration 8's work. `Frontend Present: no` (below) already keeps
  the QA agent out of the browser-check path; the developer/reviewer/QA must not independently decide
  to "just check" J-01-J-04 against live data as a bonus.
- Never start the frontend and never run two backends concurrently this iteration — a goal-mode run
  already froze this host once via memory overcommit (2026-08-20). Start the backend transiently, only
  for the two step-5(f) `GET /api/compass` calls, then stop it. The real fetch/backfill work goes
  through direct `Session`/`Engine` calls (a small standalone script, same pattern as iteration 6 —
  not a tracked deliverable file).
- Never run the full pytest suite or two pytest processes concurrently. Only
  `apps/backend/tests/test_j10_recovery.py` runs this iteration (targeted, single-file, per
  `.claude/project-template.md`).
- No `config.yaml` change, no new DB column, no second provenance framework — `data_provider_runs`
  plus the dev handoff already satisfy J-10 step 4.
- `reports/qa/goal-market-compass-iter-6-evidence/` is quarantined incident evidence (AG-17) — left
  byte-unchanged, never deleted or reused.
- All work stays on `goal/market-compass`; `main` is not touched. The developer does not commit
  (commits happen at a later pipeline stage, per this project's convention).

## Agents Required
- developer: yes -- implement the vendor swap + fail-closed convention-check gate in
  `apps/backend/app/engine/j10_recovery.py`, the small additive Yahoo `adjclose`-parsing capability in
  `apps/backend/app/data_providers/yahoo_provider.py`, update/extend
  `apps/backend/tests/test_j10_recovery.py`, run the gated recovery against the real `data/trendora.db`
  (via a direct Session/Engine script, not the test suite), execute J-10 step 5 verification directly,
  and write the dev handoff. Pure backend engine + test work — no frontend engineer needed this
  iteration.

## Frontend Present
no

## Files to Create/Modify
- `apps/backend/app/engine/j10_recovery.py` -- change `RECOVERY_SOURCE` `"stooq"` → `"yahoo"`; add the
  fail-closed adjustment-convention-check function (agree/mismatch/inconclusive) in this same module;
  sequence it strictly before any write-capable call; update the module docstring's vendor framing.
- `apps/backend/app/data_providers/yahoo_provider.py` -- add a small additive method/capability to
  fetch and parse Yahoo's `indicators.adjclose[0].adjclose` series (split/dividend-adjusted) for the
  convention-check comparison; do not change `get_daily`'s existing (already-correct-for-its-own-use)
  contract or its callers.
- `apps/backend/tests/test_j10_recovery.py` -- update `test_rejects_wrong_source` (now rejects
  `"stooq"`) and `test_recovery_constants_shape` (`RECOVERY_SOURCE == "yahoo"`); add fixture-scoped
  tests for the convention check's three verdicts using an injected fake provider (no live network).
- `docs/handoffs/goal-market-compass-iter-7-dev.md` (new) -- dev handoff per J-10 steps 4-6, as
  detailed above.
- `runs/goal-session-market-compass/state/assumptions.md` -- append a dated entry only if a genuine
  new judgment call arises (e.g. the final tolerance value's empirical basis); not a hard requirement
  of this iteration's Definition of Done.
- No `config.yaml`, no `app/models.py`/`app/db.py` (no new column), no frontend files, no changes to
  any other `app/engine/*` module.

## Key Test Scenarios
- `RECOVERY_SOURCE == "yahoo"`; `validate_recovery_scope` raises `RecoveryScopeError` for
  `source="stooq"` and raises nothing for `source="yahoo"` on an otherwise in-scope request.
- Convention check, injected fake provider: all sampled pairs within tolerance → `agree`, zero rows
  written to `daily_prices`/`scanner_runs`/`data_provider_runs`. One sampled pair off by more than
  tolerance (e.g. a 2:1 split-away value) → `mismatch`, zero writes, no further network calls made
  after the mismatch. Provider raises `ProviderUnavailableError` mid-comparison → `inconclusive`
  (never a false `agree`), zero writes.
- Fixture-scoped fetch test (2-symbol set: one full survivor + one missing a single date, passing
  convention-check) with `source="yahoo"`: only the missing row is requested/written; the survivor's
  stored values are byte-unchanged.
- Real-DB run, IF the check returns `agree`: `daily_prices` gains rows for all 587 `RECOVERY_SYMBOLS`
  (MNST still absent) on both 2026-08-11 and 2026-08-12; `ScannerRun` rows exist for both dates; the
  new `data_provider_runs` row's `provider` reads `"yahoo"`; `GET /api/compass?as_of=2026-08-12`
  returns HTTP 200 (not 400).
- Pre/post full-table diff (every `scanner_runs.asof_date` and every `daily_prices` (symbol, date))
  shows zero rows changed outside 2026-08-11/2026-08-12 — true whether the outcome is success or an
  honest stop.
- IF the check returns `mismatch`/`inconclusive`, or the fetch itself fails: zero DB rows change
  anywhere, the dev handoff records the honest stop with reasons, and no third vendor is attempted.
- No wording anywhere (code, comments, docstrings, dev handoff) claims Yahoo/Stooq interchangeability
  or vendor-equivalence.
- The 24 pre-existing `next_session_manifests` rows are still 24 after this iteration, `MAX(as_of)` is
  still 2026-08-12, and every row's `content_hash`/`manifest_hash` is unchanged (AG-12 held) —
  independently re-verified, not trusted from the developer's report alone.
- `reports/qa/goal-market-compass-iter-6-evidence/` is byte-unchanged; no browser-QA or
  deterministic-replay evidence file for J-01/J-02/J-03/J-04 exists under this iteration's QA evidence
  directory; `runs/goal-session-market-compass/iter-7/depth-dispatched` reads `full`.
- Targeted test run only: `cd apps/backend && .venv/bin/python -m pytest tests/test_j10_recovery.py -v`
  (never the full suite; never two pytest processes concurrently).
