# Goal Iteration 7 — J-10 recovery retry: swap to Yahoo, add the fail-closed adjustment-convention gate

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 7
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — Prior verdict was ESCALATE (iteration 6); per agent instructions this is
  mandatory, no exceptions, regardless of blast radius. (Trigger 1 does NOT independently apply:
  this iteration's blast radius is one module + its test file — no new DB column, no config.yaml
  edit, no cross-cutting refactor; see NOTES.)
- **Frontend Present:** no
- **Target journeys:** J-10
- **Required-still-passing journeys:** None this iteration — deliberately. See BACKGROUND for why
  J-01/J-02/J-03/J-04 re-verification (browser-QA or deterministic replay) is explicitly deferred
  to iteration 8, regardless of whether this iteration's recovery succeeds.
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
      vendor is widened from `stooq` to `stooq` or `yahoo`, and to no other provider. It
      additionally covers the read-only comparison fetch defined in J-10 step 2a — a small overlap
      window of already-surviving days, held outside the database, used solely to prove the
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

Retry J-10's bounded two-day recovery against the newly authorized `yahoo` vendor, gated behind a
new fail-closed adjustment-convention check (goal.md step 2a) that must positively prove Yahoo's
and Stooq's price series agree before a single byte is written — so the retry either honestly
restores 2026-08-11/2026-08-12 with correct provenance, or honestly stops with zero side effects,
exactly like iteration 6's Stooq attempt did.

## BACKGROUND

Iteration 6 built the recovery mechanism as specified (fail-closed scope guard, idempotent, 15/15
tests, zero side effects on the failed Stooq attempt — independently verified by the reviewer,
coherence-auditor, and evaluator) but the authorized vendor is gone: Stooq now serves a SHA-256
proof-of-work JS challenge, so all 587 requests 404'd. The owner responded the same day by amending
`docs/goal.md`: AG-9's exception now also authorizes `yahoo` (and a read-only comparison fetch),
and J-10 gained step 2a, a new fail-closed gate requiring proof that Yahoo's adjustment convention
matches Stooq's BEFORE any write. This iteration is the retry, scoped to **J-10 alone** per explicit
direction — no other journey is touched.

**Why full depth, explicitly:** the iter-6 evaluator returned ESCALATE not because the recovery
failed (an honest vendor-side block, zero damage) but because the engine silently dispatched a
`Depth: full` spec as `lean` — the SECOND such silent demotion this session (iter-2 was the first).
The lean dispatch auto-enabled a parallel browser-QA replay that then ran against the still-damaged
database in direct violation of goal.md's Loop-mechanics gate, producing FAIL rows that had to be
quarantined (`reports/qa/goal-market-compass-iter-6-evidence/INVALID-damaged-database.md`). Per
agent instructions, a prior ESCALATE makes full depth mandatory this iteration with no exceptions
(Full trigger 3) — independent of this change's actual (narrow) blast radius.

**Applying prior lessons directly:**
- *iter-6 lesson (vendor pinning):* "Pin a recovery journey's vendor as a single named constant...
  so a vendor swap is a one-line change" — this iteration swaps `RECOVERY_SOURCE` from `"stooq"` to
  `"yahoo"` as a literal constant change, not a set of allowed vendors; Stooq stays permanently
  excluded from this retry (do not retry it, do not defeat its challenge, do not try a third
  vendor).
- *iter-6 lesson (lane gate not engine-enforced):* "check `iter-<N>/depth-dispatched` against the
  spec's `**Depth:**` line FIRST, and treat quarantined evidence as unusable in both directions" —
  this iteration's own design defends against a repeat by giving the browser-QA/replay pipeline
  **nothing to run**: J-10 itself has no UI (walkthrough waived) and Required-still-passing is
  explicitly empty, so even if a parallel-QA mechanism fired despite full dispatch, it has no
  in-scope journey to test against the still-possibly-damaged database this iteration.
- *iter-4 lesson (don't invent unverified numeric targets):* applied here by proposing an explicit,
  evidence-checkable convention-check tolerance (see TESTING REQUIREMENTS) rather than an
  unstated/implicit one, and by requiring the developer to record actual observed deltas honestly
  rather than tune the tolerance to force a pass (mirrors J-09's "never widen the target to pass").

**Deliberate scope decision — J-01/J-02/J-03/J-04 re-verification is NOT part of this iteration,
even if recovery succeeds.** The prior evaluator's next-step recommendation suggested bundling the
browser-lane re-check of J-01–J-04 into this same full-depth run once the days are back. This spec
deviates from that suggestion on purpose: this session has now hit the "QA lane ran against a
database whose damage status was still being determined" failure mode twice (iter-2, iter-6).
Bundling a second risky element (browser-QA timing conditional on this iteration's own live-fetch
outcome) onto an already-risky live cross-vendor write is exactly what the "never bundle two risky
journeys" rule warns against — a joint failure would be undiagnosable, and the downside of one extra
iteration's delay is far smaller than the downside of a third occurrence of this exact incident
class. J-10's own step 5(f) check ("J-01/J-02/J-03 replay clean") is still performed THIS iteration,
but directly by the developer via read-only DB queries and two direct `GET /api/compass` calls —
never via the QA/browser-QA pipeline lane (see TESTING REQUIREMENTS and the assumption log).

**A path correction to the dispatching coordinator's note:** `yahoo_provider.py` lives at
`apps/backend/app/data_providers/yahoo_provider.py` (verified by direct file listing), not under
`app/engine/`. It already implements `PriceProvider.get_daily` against Yahoo's public chart JSON
endpoint (no API key; already the catalog `default_source` in `config.yaml`, `needs_key: false`) and
is proven working from this environment as recently as 2026-08-14 (`data_provider_runs` ids 527-533).

## IN SCOPE

### Backend
- [ ] `apps/backend/app/engine/j10_recovery.py`: change `RECOVERY_SOURCE` from `"stooq"` to
  `"yahoo"` — the sole authorized vendor for this retry (Stooq stays excluded; a third vendor is out
  of scope). Update the module docstring's vendor framing accordingly.
- [ ] `apps/backend/app/engine/j10_recovery.py`: add J-10 step 2a's fail-closed
  adjustment-convention check as a new function in this SAME module (extend, do not create a second
  recovery path). It must, for a deterministic documented sample of RECOVERY_SYMBOLS and a small
  window of already-surviving trading days ≤ 2026-08-10, fetch Yahoo's data for those exact
  (symbol, date) pairs, compare it against the stored `daily_prices` rows for the same pairs, hold
  everything in memory only (never DB-written, never cached beyond the call's own lifetime), and
  return one of three definitive, evidenced verdicts: agree / mismatch / inconclusive. See NOTES for
  a load-bearing technical finding about which Yahoo price field this comparison must use.
- [ ] Sequence the orchestration so the convention check runs, and must return "agree", strictly
  BEFORE any call capable of writing to `daily_prices`/`scanner_runs`/`data_provider_runs` — a
  mismatch or inconclusive result must leave every one of those tables byte-unchanged and produce an
  explicit "stopped" outcome the caller can act on (no silent partial writes, no exception that
  leaves state ambiguous).
- [ ] Execute the recovery against the real `data/trendora.db`: run the convention check; if it
  passes, run the existing `run_bounded_recovery_fetch` (now using `source="yahoo"`, which needs no
  API key per the config catalog) then the existing, unchanged `run_bounded_recovery_backfill`;
  record provenance in `data_provider_runs` (the `provider` column reads `"yahoo"`) plus the dev
  handoff's dated provenance section per J-10 step 4 — do NOT add a new DB column or provenance
  framework (J-10 step 4 forbids it; `daily_prices` has no per-row vendor column today, and none is
  needed — the recovery's exact date/symbol bound plus the single `data_provider_runs` record already
  fully establishes which rows came from Yahoo).
- [ ] Run J-10 step 5's verification checks (a)–(f) directly (read-only DB queries + two direct
  `GET /api/compass` calls for the two recovery dates) and record every result in the dev handoff. If
  and only if all pass, record AG-9's exception as exhausted per step 6. If the convention check or
  the fetch fails, record the honest stop instead — do not attempt a third vendor, do not retry
  Stooq.
- [ ] `apps/backend/tests/test_j10_recovery.py`: update `test_rejects_wrong_source` (now asserts a
  wrong vendor — e.g. `"stooq"`, no longer authorized for this retry — is rejected) and
  `test_recovery_constants_shape` (`RECOVERY_SOURCE == "yahoo"`). Add new fixture-scoped tests for
  the convention check's three outcomes (agree / mismatch / inconclusive) using an injected fake
  provider — no live network anywhere in the automated test suite, matching this file's own existing
  "fixture-scoped, synthetic-data only" framing.
- [ ] Dev handoff `docs/handoffs/goal-market-compass-iter-7-dev.md` documents: the convention-check
  sample (symbols + dates), the per-pair observed deltas, the tolerance used and its basis, the
  verdict, the fetch/backfill outcome either way, the full step-4/step-5 checklists, and an explicit
  statement (mirroring AG-9 step 2a) that a successful restoration is not evidence of Yahoo/Stooq
  interchangeability generally.

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
None visible to a user. If recovery succeeds, `GET /api/compass?as_of=2026-08-12` (already an
existing endpoint) stops 400ing and starts serving again — a pre-existing surface returning to its
intended behavior, not a new one.

### Blueprint conformance
No new surfaces. Confirmed by direct comparison against
`runs/goal-session-market-compass/state/blueprint.md`: J-10's write path
(`data_manager.validate_job_request` / `create_job` / `run_data_job`, the same trio the existing
`POST /api/data/jobs` launcher uses) and the new convention-check function are both internal to
`app.engine.j10_recovery`, touch no route file, and serve no new value to any page. No blueprint edit
made this iteration (nothing to register).

### Data-contract additions
None. No new displayed value, endpoint, or computing module. `data_provider_runs.provider` and
`daily_prices` are pre-existing canonical storage, written only through the single existing
`data_manager.run_data_job`/`create_job`/`validate_job_request` path that iter-6's coherence audit
already confirmed has no second implementation anywhere in the codebase
(`grep -rln "run_data_job\b" apps/backend/app` → exactly `data_manager.py` + `j10_recovery.py`).

## OUT OF SCOPE

- J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09 — no code changes, no re-verification, no
  browser-QA or deterministic-replay lane against any of them this iteration. J-01–J-04's browser-lane
  re-check is explicitly deferred to iteration 8 (see BACKGROUND), independent of this iteration's
  outcome.
- Retrying Stooq, attempting to defeat its bot challenge, or using any third vendor — AG-9's
  exception covers only `stooq` or `yahoo`; a third vendor needs a new dated amendment.
- Including MNST in `RECOVERY_SYMBOLS` — it stays excluded (587 symbols, unchanged). This is still an
  open, non-blocking owner question (iteration state); re-deriving or re-litigating the missing set
  is "Do not redo" work per iteration state, and MNST's exclusion is part of that already-derived set.
- Any `config.yaml` change — the `yahoo` catalog entry already exists (`needs_key: false`, already
  `default_source`); no provider-catalog or tunable edit is needed for this retry.
- Any new database column or a second provenance framework — J-10 step 4 explicitly forbids
  introducing one; existing `data_provider_runs.provider` plus the dev handoff satisfy the
  provenance requirement.
- Destructive-drill isolation/sandbox infrastructure — goal.md Constraints record this as a deferred
  defect, explicitly not this cycle's build.
- Deleting, rewriting, or reusing `reports/qa/goal-market-compass-iter-6-evidence/` — quarantined
  under AG-17, left exactly as-is.
- Starting the frontend, or starting more than one backend process at a time. A second goal-mode
  engine may be active on this host, which froze once already from two concurrent backends (see
  NOTES).
- Any claim, anywhere (code comments, docstrings, dev handoff), that a successful cross-vendor
  restoration proves Yahoo and Stooq bars are interchangeable — AG-9 step 2a forbids this explicitly.
- Committing recovery work anywhere but the `goal/market-compass` branch (`main` is not touched).

## DEFINITION OF DONE

- [ ] `RECOVERY_SOURCE` reads `"yahoo"`; `validate_recovery_scope` rejects `source="stooq"` and
  accepts `source="yahoo"` for an otherwise in-scope request (unit tests pass)
- [ ] The adjustment-convention check runs against the real (non-fixture) database and produces one
  of three definitive, evidenced verdicts (agree / mismatch / inconclusive), with every sampled
  pair's observed delta recorded in the dev handoff
- [ ] The convention-check's comparison fetch is provably read-only/in-memory: zero
  `daily_prices`/`scanner_runs`/`data_provider_runs`/any-other-table rows are written by it, in every
  outcome
- [ ] IF the check returns "agree": the bounded fetch restores 2026-08-11 and 2026-08-12 for all 587
  `RECOVERY_SYMBOLS` (MNST still excluded), every restored row's run carries `yahoo` provenance in
  `data_provider_runs.provider`, and every surviving row elsewhere is byte-unchanged
  (pre/post full-table diff outside the two dates)
- [ ] IF the fetch succeeds: `run_bounded_recovery_backfill` rebuilds `ScannerRun` snapshots for
  exactly 2026-08-11 and 2026-08-12 and no other date
- [ ] IF the check returns "mismatch" or "inconclusive", OR the fetch itself fails: zero DB rows
  change anywhere, the dev handoff records the honest stop with reasons, and no third vendor is
  attempted
- [ ] J-10 step 5's verification (a)–(f) is executed directly by the developer (read-only DB queries
  + two direct `GET /api/compass` calls) and recorded in the dev handoff; this does NOT invoke the
  browser-QA or deterministic-replay pipeline lane
- [ ] No wording in code, comments, docstrings, or the dev handoff claims Yahoo/Stooq
  interchangeability or vendor-equivalence
- [ ] Unit tests pass, including new fixture-scoped tests covering the convention check's three
  outcomes via an injected fake provider (zero live network calls in the automated test suite)
- [ ] Reviewer, coherence-auditor, and evaluator all run this iteration (full depth); AG-9, AG-12,
  and AG-17 are each independently confirmed held via first-hand read-only checks, not trusted from
  the developer's report alone
- [ ] `runs/goal-session-market-compass/iter-7/depth-dispatched` reads `full`, matching this spec's
  own `Depth: full` line (the evaluator checks this explicitly per the standing lesson)
- [ ] No browser-QA or deterministic-replay lane runs against J-01, J-02, J-03, or J-04 this
  iteration, regardless of the recovery's outcome
- [ ] `reports/qa/goal-market-compass-iter-6-evidence/` is byte-unchanged (not deleted, not rewritten)
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-7-dev.md`

## TESTING REQUIREMENTS

- Browser: none. J-10 has no UI surface (walkthrough waived). No browser-QA runs against J-01–J-04
  this iteration — deferred to iteration 8 (see BACKGROUND/OUT OF SCOPE).
- Unit/integration: `apps/backend/tests/test_j10_recovery.py` (updated + new convention-check
  tests, fixture-scoped, synthetic data, no live network) run via the targeted single-file pytest
  invocation this project always uses for pipeline agents (never the full suite). The real recovery
  attempt against `data/trendora.db` is executed directly (a small standalone script making the same
  `Session`/`Engine` calls the tests use, per NOTES) — not part of the automated pytest suite, mirroring
  how iteration 6 already operated.
- Error cases: wrong vendor rejected pre-network; out-of-window date rejected; out-of-set symbol
  rejected (including MNST, explicitly); empty symbol list rejected; convention-check mismatch
  yields zero writes; convention-check provider failure (inconclusive) yields zero writes; a
  second/idempotent invocation after a partial or complete prior attempt re-requests only what is
  still missing and never re-fetches a fully-covered symbol.

Test-first contract — TC- scenarios (numbered sequentially; each maps to a DEFINITION OF DONE item):

- TC-1: given `j10_recovery.py`'s `RECOVERY_SOURCE` constant, when `test_recovery_constants_shape`
  runs, then it asserts `RECOVERY_SOURCE == "yahoo"`.
- TC-2: given `validate_recovery_scope` called with `source="stooq"` and an otherwise fully in-scope
  date/symbol request, when invoked, then it raises `RecoveryScopeError` matching "source must be".
- TC-3: given `validate_recovery_scope` called with `source="yahoo"` and a fully in-scope
  date/symbol request, when invoked, then it raises nothing.
- TC-4: given a deterministic, documented sample of at least 15 `RECOVERY_SYMBOLS` tickers and a
  comparison window of the 5 most recent trading days already present in `daily_prices` on or before
  2026-08-10, when the convention-check function runs with an injected fake provider whose returned
  values equal the stored `daily_prices` closes for every sampled pair within the stated tolerance
  (proposed default: 0.75% relative on close price — see NOTES), then it returns an "agree" verdict
  and zero rows are written to `daily_prices`, `scanner_runs`, or `data_provider_runs`.
- TC-5: given the same setup, when the injected fake provider returns, for at least one sampled
  pair, a value inconsistent with the stored close by more than the stated tolerance (e.g. a 2:1
  split-away value), then the function returns a "mismatch" verdict, and the orchestration makes
  zero writes and no further network calls.
- TC-6: given the same setup, when the injected fake provider raises `ProviderUnavailableError`
  during the comparison fetch, then the function returns an "inconclusive" verdict (never a false
  "agree"), and the orchestration makes zero writes.
- TC-7: given a synthetic fixture DB with `RECOVERY_SYMBOLS` monkeypatched to a small 2-symbol set
  (one full survivor, one missing a single date — mirroring this file's existing
  `test_fetch_restores_only_the_missing_rows_and_never_touches_survivors` pattern) and a passing
  convention-check result, when `run_bounded_recovery_fetch` runs with `source="yahoo"` and a
  recording fake provider, then only the missing row is requested and written, and the survivor
  row's stored values are byte-unchanged.
- TC-8: given the real `data/trendora.db` and an "agree" convention-check verdict, when the bounded
  fetch and `run_bounded_recovery_backfill` complete, then `daily_prices` holds rows for all 587
  `RECOVERY_SYMBOLS` (MNST still absent) on both 2026-08-11 and 2026-08-12, and `ScannerRun` rows
  exist with `asof_date` 2026-08-11 and 2026-08-12.
- TC-9: given the same successful run, when the new `data_provider_runs` row is queried, then its
  `provider` column reads `"yahoo"` (never `"stooq"`, never blended or relabeled).
- TC-10: given the same successful run, when `GET /api/compass?as_of=2026-08-12` is called directly
  against a single, transiently-started backend, then it returns HTTP 200 (not 400).
- TC-11: given a pre-recovery snapshot of every `scanner_runs.asof_date` and every `daily_prices`
  (symbol, date) row taken before this iteration's fetch, when diffed against the post-recovery
  state (success or honest stop), then zero rows outside 2026-08-11/2026-08-12 changed.
- TC-12: given the dev handoff and every new code comment/docstring, when grepped for
  interchangeability/equivalence framing ("interchangeable", "equivalent", "proves... same as
  stooq" or similar), then no such claim appears — only a statement that the two dates were restored
  (or not) under a stated, evidenced tolerance.
- TC-13: given the convention check returns "mismatch" or "inconclusive" on the real (non-fixture)
  run, when the developer records the outcome, then the dev handoff states the honest stop, the
  same pre/post diff as TC-11 shows zero changed rows, and no third vendor is attempted.
- TC-14: given this iteration's full diff, when the coherence-auditor checks the Data Contract and
  Information Architecture, then it confirms no new displayed value, endpoint, route, or computing
  module was introduced.
- TC-15: given `reports/qa/goal-market-compass-iter-6-evidence/`, when this iteration's file listing
  is diffed against the pre-iteration state, then the directory is byte-unchanged.
- TC-16: given this spec's `Depth: full` line, when the engine dispatches the iteration, then
  `runs/goal-session-market-compass/iter-7/depth-dispatched` reads `full`; the evaluator checks this
  explicitly before trusting any merged QA results file.
- TC-17: given J-01, J-02, J-03, and J-04, when this iteration's pipeline completes, then no
  browser-QA or deterministic-replay evidence file for any of the four exists under this iteration's
  QA evidence directory (their re-verification is iteration 8's work, not this iteration's).
- TC-18: given the 24 `next_session_manifests` rows present before this iteration, when queried
  after this iteration completes (success or honest stop), then the row count is still 24,
  `MAX(as_of)` is still 2026-08-12, and every row's `content_hash`/`manifest_hash` is unchanged
  (AG-12 held, independently re-verified — not trusted from the developer's claim alone).
- TC-19: given this iteration's completion, when checked, then
  `docs/handoffs/goal-market-compass-iter-7-dev.md` exists and cites evidence for every one of J-10
  step 5's checks (a)–(f).

## NOTES

- **Load-bearing technical finding (verified by direct code read, not assumed):** the existing
  `YahooProvider.get_daily` (`apps/backend/app/data_providers/yahoo_provider.py`) parses
  `indicators.quote[0].close` from Yahoo's chart JSON — Yahoo's plain/raw close series, NOT its
  `indicators.adjclose[0].adjclose` series. `apps/backend/app/models.py:101` documents
  `DailyPrice.close` as "split/dividend-adjusted (the committed seed is pre-adjusted)" and
  `stooq_provider.py`'s own docstring makes the same claim for Stooq. If the convention check
  compares Yahoo's plain `close` against the stored split/dividend-adjusted `daily_prices.close`, it
  will very likely produce a false "mismatch" for any dividend-paying name in the sample — not
  because the vendors disagree, but because the check would be comparing two different fields. The
  developer must fetch/compare Yahoo's dividend-and-split-adjusted series (`adjclose`) for this
  check — likely a small additive capability on `YahooProvider` (e.g. requesting
  `indicators=quote,adjclose` and parsing the adjclose array) rather than reusing `get_daily`
  unmodified. This is exactly the kind of silent mismatch J-10 step 2a exists to catch — get the
  comparison field right or the gate is not testing what the goal requires.
- **Tolerance is a proposed default, not a verified fact.** 0.75% relative difference on close price,
  required for every sampled pair, is this spec's starting point — chosen to be tight enough to
  catch a genuine convention mismatch (a full split ratio is tens of percent; even a modest
  dividend-adjustment drift is usually well above this band) while tolerating ordinary cross-vendor
  rounding noise. If the developer's actual observed deltas suggest a different band is the honest
  evidence-based choice, they may set it once, document the empirical basis (min/max/mean observed
  delta from a preliminary read) in the dev handoff, and use that as the final tolerance — but must
  NOT iteratively loosen it after seeing a borderline or failing result just to force a pass (the
  same discipline J-09 already established: record the honest measured outcome, never move the
  target to make it pass).
- **Why the tolerance and sample/window bounds are inline literals, not new `config.yaml` keys** —
  extending the same reasoning iter-6's own coherence-auditor accepted without objection for
  `RECOVERY_DATES`/`RECOVERY_SYMBOLS`: this whole check exists only to gate one single-use,
  self-closing AG-9 exception (goal.md: "not a standing... path"); promoting its tuning literal to a
  standing, operator-tunable `config.yaml` key would misrepresent a one-time incident check as a
  reusable feature. Logged to the assumption ledger since it is a genuine ambiguity (goal.md doesn't
  say where this literal belongs), same as the iter-6 precedent.
- **Host safety:** invoke the real recovery via a small standalone script making direct
  `Session`/`Engine` calls into `j10_recovery` (the same pattern the test suite already uses) —
  this needs no running backend or frontend at all for the core fetch/backfill work. Start a single
  backend only transiently, for the two step-5(f) `GET /api/compass` calls, then stop it
  immediately. Never run two backends concurrently and never start the frontend this iteration — a
  second goal-mode engine may be active on this host, which froze once already from two concurrent
  backends (memory overcommit + swap-thrash, no OOM kill, 2026-08-20).
- **Still-open, non-blocking owner questions, carried forward untouched (none are this iteration's
  to resolve):** whether 3.44 GB is acceptable for J-09; J-06's "underlying run unavailable" wording;
  the J-01 test-step rewording; whether an empty "next-session focus" on the newest date is
  acceptable; and whether MNST should be included in a future recovery attempt.
- **Coordinator path note:** the dispatching coordinator's message named
  `apps/backend/app/engine/yahoo_provider.py`; the actual, verified location is
  `apps/backend/app/data_providers/yahoo_provider.py` (see BACKGROUND).
- Escalation flag for the evaluator: if `yahoo` also proves unreachable or fails the convention
  check, that is an honest, acceptable outcome for this iteration (same as iteration 6's Stooq
  result) — do not read a second consecutive "zero bars restored" outcome as a process failure by
  itself; only a repeat of the depth-demotion/forbidden-lane pattern, or a violation of the
  interchangeability/provenance constraints, should trigger ESCALATE again.
