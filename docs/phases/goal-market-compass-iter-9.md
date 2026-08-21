# Goal Iteration 9 — J-10 population-scale recovery: evaluate the remaining 567 symbols under the fixed gate

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 9
- **Mode:** next
- **Depth:** full
- **Depth enforcement:** required
- **Full trigger:** 1 — Structural/cross-cutting: the population-scale pass exercises the interaction
  between the extended recovery driver, `j10_recovery.py`'s per-symbol gate,
  `yahoo_provider.py`'s fetch layer, and `data_manager`'s fetch-and-insert engine at up to ~28x
  iteration 8's tested scale (567 vs. 20 symbols) — an interaction this session's own audit already
  caught a real fail-open in once (iter-7's B1 fail-open, found only by the audit lane). Independently
  matches the evaluator's own binding recommendation (`full`) for this iteration and `docs/goal.md`'s
  standing rule that any J-10 iteration performing recovery DB/network mutation carries full depth as
  a requirement, not a preference. `Depth enforcement: required` is set because
  `runs/goal-session-market-compass/iter-8/budget-breached` exists on disk (content `1`) — without this
  line, the deterministic depth arbiter's cost ladder would treat that marker as a `budget-breach` and
  force this spec's `Depth: full` down to `lean` despite the recommendation, exactly the silent
  demotion this line exists to override (verified against `scripts/automation/lib/common.sh`'s
  `goal_full_depth_required` and `run-goal.sh`'s arbiter precedence).
- **Frontend Present:** no
- **Target journeys:** J-10
- **Required-still-passing journeys:** None this iteration — deliberately. `docs/goal.md`'s
  Loop-mechanics lane gate ("No developer, reviewer, QA, browser-QA, evaluator, coherence, research or
  proposer lane may run against the knowingly damaged database before J-11 Stage G passes") forbids any
  browser-QA/replay verification of J-01–J-08 while the derived layer stays quarantined. Naming any of
  them here would mechanically trigger exactly that forbidden lane through this spec's own
  Required-still-passing field. See BACKGROUND / OUT OF SCOPE.
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local
    provider fixtures — no live external network calls or paid data services without an explicit
    goal.md amendment. *(critical)*
    - **Dated exception (owner, 2026-08-20 — single-use, self-closing, incident response):** the
      bounded recovery fetch defined by **J-10** is authorized for exactly two calendar dates,
      **2026-08-11 and 2026-08-12**, and only for the symbol/row scope proven missing as a consequence
      of the iter-5 drill. It authorizes **nothing else**: no other date (in particular nothing on or
      after 2026-08-13), no refresh of unaffected historical data, no replacement of valid existing
      rows, no broad backfill, no advancement of the dataset to a newer market-data frontier, no
      change to candidate thresholds or research logic, and no unrelated data repair. The intent is
      **state restoration only, not dataset advancement**. If the implementation cannot prove a
      request stays inside this scope, it MUST stop rather than broaden the fetch. The exception is
      **exhausted** the moment J-10's post-recovery verification passes — normal AG-9 then applies
      again automatically, and any later live fetch, **including of these same two dates**, requires a
      new dated goal.md amendment. The only retry permitted under this exception is a re-run of the
      same bounded, idempotent recovery after a failed or partial attempt, still confined to the
      proven missing set. This is not a standing "recovery fetch allowed" path.
    - **Vendor addendum (owner, 2026-08-20, after iteration 6's Stooq block):** the exception's vendor
      is widened from `stooq` to **`stooq` or `yahoo`**, and to no other provider. It additionally
      covers the **read-only comparison fetch** defined in J-10 step 2a — a small overlap window of
      already-surviving days, held outside the database, used solely to prove the adjustment
      convention matches, never written and never used to repair anything. Every other bound is
      unchanged (the same two dates, the same proven-missing rows, fail-closed, idempotent,
      self-closing on verification). A third vendor requires a new dated amendment.
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are
    never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change;
    corrections happen only as new version rows; a historical view never substitutes a newer manifest.
    *(critical)*
  - **AG-17 — Repair never rewrites provenance (owner, 2026-08-20):** restoring deleted historical data
    MUST NOT retroactively change research provenance. A manifest that was retrospective or ineligible
    stays that way; **`prospective_eligible` is never upgraded merely because historical data was later
    repaired**; `available_at_utc`, manifest versions, `content_hash`/`manifest_hash`, and prior
    eligibility classifications remain immutable (AG-12 governs the rows and files themselves). Any
    manifest or artifact produced while the database was known to be damaged — everything dated from
    the iter-5 drill until **J-11 Stage G** passes — **remains marked unusable as prospective/out-of-
    sample evidence**; nothing is retroactively marked prospective merely because raw bars were
    repaired in J-10 or derived snapshots were regenerated in J-11 — historical causality is unchanged
    by either; only a separately regenerated artifact, minted after verified recovery under the
    existing create-once and version rules, may carry eligibility. The incident record itself is
    evidence: the iter-5 drill result, its handoff, the reviewer/QA evidence already produced, and the
    explicit statement that the committed seed could not restore these dates MUST NOT be deleted,
    rewritten, or silently superseded. Repairing the database never rewrites historical causality.
    *(critical)*

## GOAL

Evaluate every one of the 567 still-missing, authorized `RECOVERY_SYMBOLS` through J-10's existing
fixed per-symbol path-agreement + stable-bridge gate — restoring each one that passes (idempotently,
alongside the already-valid 20) and honestly naming each one that does not — while closing the three
still-open audit gaps (mandatory evidence file, provider-mismatch guard, un-gated fetch back door) and
verifying the raw-layer outcome by direct read-only database/provenance checks only, with zero
browser-QA or replay lane execution.

## BACKGROUND

**Target selection follows the priority rubric with no deviation.** Iteration 8's eval recorded zero
regressed journeys and the iter-8 coherence audit is `COHERENCE-PASS` (not FAIL), so neither rule 1
(regressed-first) nor rule 2 (consolidation-before-features) redirects this iteration. J-10 is this
session's sole unblocker (rubric 3): `docs/goal.md`'s explicit sequencing gate forbids starting J-11
before J-10's raw-layer terminal state, and the deferred J-01–J-04 re-verification is itself gated on
that same state. It is not human-blocked (rubric 6) — the owner has already authorized continuation via
the 2b/2c amendment — and exactly one risky journey is targeted, nothing bundled alongside it (rubric
5). Per the coordinator's explicit direction, J-11 is out of scope regardless.

**Why full depth, explicitly (Full trigger 1).** See the metadata block for the full citation. In
short: this iteration exercises the recovery driver's interaction with the per-symbol gate, the Yahoo
fetch layer, and the insert engine at population scale (up to 567 symbols) for the first time — an
interaction this session's own audit lane already caught a real fail-open in once at a much smaller
scale (iter-7's B1, missed by reviewer and QA both). This independently matches the evaluator's own
binding-full recommendation for this iteration and `docs/goal.md`'s standing rule that any J-10
iteration performing recovery DB/network mutation carries full depth as a requirement. `Depth
enforcement: required` is set because iteration 8's `budget-breached` marker is present on disk and
would otherwise force the deterministic depth arbiter's cost ladder to demote this spec to `lean`
regardless of the `Depth: full` line — confirmed by reading `scripts/automation/lib/common.sh`'s
`goal_full_depth_required` and the arbiter precedence in `run-goal.sh` directly. No escape-condition
analysis is needed beyond stating the trigger, since the recommendation and the trigger already agree.

**What "continue from 20/587" means precisely (goal.md J-10 step 2b).** Two different things must not
be conflated. The **methodology-validation sample** — the 20 fixed names in
`CONVENTION_CHECK_SAMPLE_SYMBOLS` — already produced its admissibility verdict in iteration 8 (all 20
`agree`, bridge factor 1.0) and stays **frozen**: never re-run, re-widened, or re-derived as a
validation exercise. What this iteration widens is a different axis: the **recovery population**
(`still_missing_symbols()`, up to 567 names, independently established before any live comparison ran)
now gets evaluated, one symbol at a time, through that same already-proven, byte-unchanged fixed gate —
same thresholds (`PATH_AGREEMENT_TOLERANCE`, `BRIDGE_DISPERSION_BOUND`, `MIN_COMPARABLE_PAIRS_PER_SYMBOL`),
same live window derivation, same verdict ladder. Per the Completion rule, J-10 does not close on any
invented "enough" number — every remaining symbol needs an explicit restored-or-classified-unrestorable
outcome, named by symbol.

**Do not carry iteration 8's stale framing forward.** That spec's BACKGROUND stated "Expect a partial
outcome, and that is acceptable" — the evaluator correctly refused to let that framing close J-10, and
it is not repeated here. This iteration's target is full population coverage. See
`runs/goal-session-market-compass/state/assumptions.md` (iter-9 entry) for the one narrow, honest
exception this spec allows — a named residual only for a genuine external blocker (e.g., a Yahoo outage
on a specific symbol during the run), never an invented threshold.

**Three still-open audit/reviewer gaps ride along (iteration-state's Do-not-redo list: B1/B2/B3/B5/B6
are DONE — do not regress them; these three are not).** (1) `run_gated_recovery`'s `evidence_path`
parameter is currently `Optional` on the production entry point — make it required. (2) Its
`fetch_provider` parameter currently defaults silently to `convention_provider` with nothing refusing a
caller-supplied mismatch — add a guard so a mismatched pair (violating B2's one-series-end-to-end rule)
is refused, not merely discouraged by docstring. (3) `run_bounded_recovery_fetch` is independently
importable and only enforces scope (dates/symbols/source), not that its symbols passed the convention
gate — a caller reaching it directly could insert an untransformed (non-bridge-applied) row; close that
back door. Also: **commit the recovery driver.** Grepping the repository shows no committed caller of
`run_gated_recovery` outside `test_j10_recovery.py` — iteration 8's real 20-symbol run was executed ad
hoc and cannot be reproduced from the repository (its own dev handoff, Known Issue list, said so). This
iteration's much larger population-scale run must be reproducible.

**Verification stays inside the lane gate (coordinator directive; `docs/goal.md` Loop mechanics).** A
deterministic replay/browser lane has now run against the knowingly damaged database twice (iter-6 lean,
iter-8 both lean and — during the very re-run meant to add the missing audit — full), overwriting
AG-17-protected evidence once. Correcting the depth marker did not stop it (iter-8 audit finding P2:
the lane runs at full depth too). This spec therefore names zero Target/Required-still-passing journeys
whose verification would invoke that lane, and J-10's own step-5 verification (raw coverage, no
third-date/symbol touch, no overwrite, frontier unchanged, integrity checks) is executed as direct,
read-only DB and provenance checks — never by starting the backend merely to look, since boot warmup
itself writes (iteration 8's own 2026-05-12 `ScannerRun` side effect). Where a check cannot avoid
starting the backend, step 5a's mutation-reconciliation rule applies: every write it causes must be
detected, classified, and disclosed — never silently waved through as "no out-of-scope writes."

**Applying prior lessons directly.** iter-7's lesson (a fail-closed guard is proven only by a test that
constructs the exact degenerate input it will meet in production) applies to the three gap-closing
tests above: each needs a test exercising the actual missing-`evidence_path`, mismatched-`fetch_provider`,
and ungated-symbol conditions, not a happy-path fixture. iter-8's lesson (a suspiciously clean
cross-source result can be a same-source tautology) applies to this batch's own results narrative: the
stored overlap-window bars are Yahoo's, not Stooq's, so a population-scale run that again returns
bridge factors near 1.0 across hundreds of symbols is still a Yahoo-vs-Yahoo result — safer, but not
cross-vendor validation, and the handoff must say so explicitly rather than implying otherwise. iter-6/
iter-8's forbidden-lane lesson is applied above.

## IN SCOPE

### Backend
- [ ] Extend the J-10 recovery driver so the fixed per-symbol gate runs over the recovery-population
  remainder (`still_missing_symbols()`) as an axis distinct from the frozen 20-name methodology sample,
  which stays byte-unchanged and is never re-run as a validation exercise (goal.md step 2b's binding
  invariant).
- [ ] Commit a reproducible entry point (script or module-level callable) that drives the gate → fetch →
  backfill sequence for the population pass, so this iteration's real run can be re-derived from the
  repository.
- [ ] Make `run_gated_recovery`'s `evidence_path` parameter required (not optional) on the production
  entry point.
- [ ] Add a guard in `run_gated_recovery` that refuses a `fetch_provider` whose source does not match
  `convention_provider`'s source.
- [ ] Close the un-gated back door: production code must not be able to reach
  `run_bounded_recovery_fetch` with recovery-scope symbols that never passed the convention gate's
  bridge transform.
- [ ] Run the population pass end to end: for each `agree` verdict, fetch + bridge-transform + insert
  both recovery-date bars (idempotently skipping the 20 already restored); for each `mismatch`/
  `inconclusive` verdict, write zero rows and record the symbol + reason on the "requested but not
  restored" list.
- [ ] Persist the full per-pair evidence artifact for this batch (mandatory `evidence_path`, e.g. under
  `runs/goal-market-compass-iter-9/`) before any verdict drives a fetch/insert decision.
- [ ] Record provenance in `data_provider_runs` and a dated section of the dev handoff per J-10 step 4
  (dates, provider, restored/not-restored-with-reason, timestamps, pre/post missing-row counts).
- [ ] Verify raw-layer state per J-10 step 5(a)-(f) via direct read-only DB/provenance checks; where a
  check would otherwise require starting the backend, either replace it with a read-only equivalent or
  fully reconcile and disclose every mutation the check itself causes (step 5a).
- [ ] Record in the dev handoff whether AG-9's dated exception is exhausted per step 6 — `true` only at
  the Completion-rule terminal state, never on a partial outcome.
- [ ] Add/extend file-scoped unit tests in `apps/backend/tests/test_j10_recovery.py` (and
  `test_provider_clients.py` if the provider-mismatch guard touches it) covering the three closed gaps
  on synthetic fixtures built from the actual degenerate conditions (missing `evidence_path`, mismatched
  provider, an ungated symbol reaching the fetch function directly), plus the population-pass behavior.

### Frontend
None — J-10 has no UI surface (`docs/goal.md`: Walkthrough waived). No frontend file is in scope.

### New user-facing capability
None this iteration — raw-layer incident recovery only.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None this iteration — the underlying dataset becomes more complete (raw-layer only); no user-visible
surface changes until J-11 regenerates and re-serves the derived state (a later journey, out of scope
here).

### Blueprint conformance
No new surfaces. `runs/goal-session-market-compass/state/blueprint.md` carries no J-10/J-11 row today
(both are raw/derived-layer incident-recovery journeys with no page of their own) and none is added.

### Data-contract additions
None — no new displayed value, endpoint, or computing module. `daily_prices` raw rows are upstream
data, not a blueprint Data-Contract (served-value) entry; nothing already registered in the Data
Contract changes its computing module or serving endpoint.

## OUT OF SCOPE

- **J-11** (incident-bounded clean regeneration) in any form — hard-gated behind J-10's raw-layer
  terminal state. No `ScannerRun`/snapshot clearing or regeneration, no `next_session_manifests` touch,
  no cache invalidation work.
- Re-fetching, overwriting, or reverting the 20 symbols already restored in iteration 8.
- Widening `RECOVERY_SYMBOLS`, `RECOVERY_SOURCE`, `RECOVERY_DATES`, `PATH_AGREEMENT_TOLERANCE`,
  `BRIDGE_DISPERSION_BOUND`, `MIN_COMPARABLE_PAIRS_PER_SYMBOL`, or `CONVENTION_CHECK_SAMPLE_SYMBOLS` —
  all frozen and settled; read unchanged, never re-derived.
- Including MNST in the recovery population — remains deliberately, evidentially excluded pending a
  separate owner decision (non-blocking).
- A third data vendor, under any condition — Yahoo unreachable or failing the convention check on a
  symbol is an honest miss for that symbol, not grounds to try anything else.
- **Any browser-QA-agent execution or deterministic-replay lane, for any journey, this iteration.** The
  standing lane gate stays shut until J-11 Stage G passes; this explicitly includes J-01–J-08. A static
  UI-impact-analyst pass that touches no live app (confirming zero frontend files changed) is not
  forbidden, since it starts nothing and mutates nothing.
- Starting the backend or frontend merely to verify, wherever a read-only DB/provenance check suffices.
- Any mutation, deletion, or "cleanup" of `reports/qa/goal-market-compass-iter-8-evidence/` — the
  quarantined incident evidence is preserved exactly as is.
- Running the full pytest suite — file-scoped test invocations only (`docs/goal.md` Constraints).
- Any change to `main` — all work stays on `goal/market-compass`.
- Resolving the four older non-blocking owner questions (J-09's 3.44 GB figure, J-06's wording, J-01's
  test-step rewording, an empty next-session-focus section) — carried forward, not this iteration's
  work.
- Fixing the pipeline's forbidden-lane recurrence itself — a defect in `scripts/automation/`, outside
  this Trendora-product iteration's surface. This spec plans around it; it does not fix it.

## DEFINITION OF DONE

- [ ] Every `RECOVERY_SYMBOLS` member still missing at the start of this iteration has exactly one
  recorded verdict (`agree`, `mismatch`, or `inconclusive`) — none silently unattempted (TC-1)
- [ ] Every `agree` verdict yields both recovery-date bars inserted, each OHLC field equal to the
  fallback value times that symbol's bridge factor, volume unscaled (TC-2)
- [ ] Every `mismatch`/`inconclusive` verdict yields zero rows for that symbol and a named,
  reason-carrying entry on the "requested but not restored" list (TC-3)
- [ ] The 20 symbols restored in iteration 8 are excluded from this iteration's request; their 40 stored
  rows are byte-identical before and after (TC-4)
- [ ] A request naming a date outside {2026-08-11, 2026-08-12}, a symbol outside `RECOVERY_SYMBOLS`, or
  a source other than `yahoo` is refused before any network call or DB write (TC-5)
- [ ] `run_gated_recovery`'s `evidence_path` is a required parameter on the production entry point (TC-6)
- [ ] `run_gated_recovery` refuses a `fetch_provider`/`convention_provider` source mismatch (TC-7)
- [ ] `run_bounded_recovery_fetch` cannot be reached in production code with an ungated, unbridged
  symbol (TC-8)
- [ ] The recovery driver used for this iteration's real run is committed to the repository and proven
  idempotent on re-run (TC-9)
- [ ] Every DB mutation this iteration's own verification causes is detected, classified (authorized
  recovery write vs. incidental product write), and disclosed in the dev handoff (TC-10)
- [ ] No browser-QA or deterministic-replay lane runs against J-01–J-08 this iteration;
  `runs/goal-session-market-compass/iter-9/depth-dispatched` reads `full`, matching this spec's own
  `Depth: full` + `Depth enforcement: required` lines (TC-11)
- [ ] `data_provider_runs` and the dev handoff's provenance section agree on provider, dates, the
  restored/not-restored-with-reason lists, timestamps, and pre/post missing-row counts (TC-12)
- [ ] The dev handoff's AG-9 exception-exhaustion statement reads `true` only if the Completion-rule
  terminal state is actually reached this iteration, `false`/not-yet-exhausted otherwise (TC-13)
- [ ] All commits stay on `goal/market-compass`; `main` is unchanged (TC-14)
- [ ] File-scoped unit tests (`test_j10_recovery.py`, `test_provider_clients.py`) pass with zero
  regressions, including the new gap-closing tests (TC-15)
- [ ] No anti-goal violation introduced — AG-9 scope stays exactly {2026-08-11, 2026-08-12} ×
  `RECOVERY_SYMBOLS` × `yahoo`; AG-12 and AG-17 hold (zero manifest mutation, zero provenance rewrite)
  (TC-16)
- [ ] `reports/qa/goal-market-compass-iter-8-evidence/` remains byte-unchanged (TC-16)
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-9-dev.md`

## TESTING REQUIREMENTS

- Browser: none. No browser-QA-agent or deterministic-replay lane runs this iteration for any journey —
  J-10 has no UI surface (walkthrough waived) and the standing lane gate forbids any such lane against
  J-01–J-08 while the derived layer stays quarantined pending J-11 Stage G. A static UI-impact-analyst
  pass that starts nothing and mutates nothing is fine.
- Unit/integration: `apps/backend/tests/test_j10_recovery.py` and `apps/backend/tests/test_provider_clients.py`
  (if the provider-mismatch guard touches it), via the targeted single-file pytest invocation this
  project always uses for pipeline agents — never the full suite. The real population-scale recovery
  run against `data/trendora.db` executes via the committed driver directly (mirroring iterations 6-8),
  outside the automated pytest suite.
- Error cases: a symbol with zero comparable pairs; a symbol below the minimum-evidence floor; a symbol
  failing path agreement only; a symbol failing bridge dispersion only; a Yahoo provider failure
  mid-batch (must yield `inconclusive` for that one symbol, never abort the whole batch); a call
  omitting `evidence_path`; a call passing a `fetch_provider` that does not match `convention_provider`'s
  source; a direct call to `run_bounded_recovery_fetch` for a symbol with no passing bridge factor; a
  request naming MNST or any symbol outside `RECOVERY_SYMBOLS`; a second/idempotent invocation after a
  partial or complete prior attempt.

Test-first contract — TC- scenarios (numbered sequentially; each maps to a DEFINITION OF DONE item):

- TC-1: given the live `still_missing_symbols()` set at the start of this iteration, when the
  population pass runs the fixed per-symbol gate over it, then every symbol in that set has exactly one
  recorded verdict (`agree`/`mismatch`/`inconclusive`) in the persisted evidence artifact, with none
  absent.
- TC-2: given a symbol whose verdict is `agree`, when its fetch/backfill executes, then `daily_prices`
  carries exactly one row for that symbol on 2026-08-11 and one on 2026-08-12, each OHLC field equal to
  the fallback provider's value multiplied by that symbol's recorded bridge factor (within
  floating-point tolerance), and volume equal to the fallback's raw volume, unscaled.
- TC-3: given a symbol whose verdict is `mismatch` or `inconclusive`, when the driver completes, then
  zero `daily_prices` rows exist for that symbol on either recovery date, and the symbol appears by name
  with its reason on the "requested but not restored" provenance list.
- TC-4: given the 20 symbols already restored in iteration 8, when the population driver runs, then
  `still_missing_symbols()` excludes all 20 from the request, no network call is made for them, and a
  spot-check of their 40 stored rows shows byte-identical values before and after this iteration.
- TC-5: given a request naming a date outside `{2026-08-11, 2026-08-12}`, a symbol outside the frozen
  `RECOVERY_SYMBOLS`, or a source other than `yahoo`, when it reaches `validate_recovery_scope`, then
  `RecoveryScopeError` is raised and no network call or DB write occurs.
- TC-6: given a call to `run_gated_recovery` that omits `evidence_path`, when the call is attempted,
  then it is refused before any convention check or fetch runs.
- TC-7: given a call to `run_gated_recovery` with a `fetch_provider` whose source does not match
  `convention_provider`'s, when the call is attempted, then it is refused before any fetch occurs; an
  omitted `fetch_provider` (defaulting to `convention_provider`) still proceeds normally.
- TC-8: given a direct call to `run_bounded_recovery_fetch` in the production code path for a symbol
  with no passing bridge factor on record, when the call is attempted, then it is refused — the un-gated
  back door cannot insert an untransformed row for a symbol that never passed the convention gate.
- TC-9: given the recovery driver used for this iteration's real run, when the repository is inspected
  after the iteration, then that exact driver is committed under version control, and re-running it
  against the post-iteration DB state is a verified zero-write no-op.
- TC-10: given this iteration's full sequence of DB writes (convention-check reads, fetch, backfill, and
  any verification step), when the dev handoff's mutation-reconciliation section is checked, then every
  write is classified as either an authorized recovery write or an explicitly named incidental product
  write — no verification claim of "no out-of-scope writes" stands if the application itself produced
  an unrelated persistent row during that verification.
- TC-11: given this iteration's dispatch, when `runs/goal-session-market-compass/iter-9/depth-dispatched`
  is read after the pipeline completes, then it reads `full`, and no browser-QA or deterministic-replay
  evidence file for J-01 through J-08 exists under this iteration's QA evidence directory.
- TC-12: given `data_provider_runs` before and after this iteration, when the new run row(s) are
  inspected, then each records the recovery dates, provider (`yahoo`), start/completion timestamps, the
  pre-recovery missing-row count, and the post-recovery restored-row count, matching the dev handoff's
  dated provenance section on every shared fact.
- TC-13: given the recovery's actual end state after this iteration, when the dev handoff states whether
  AG-9's dated exception is exhausted, then that statement reads `true` only if every `RECOVERY_SYMBOLS`
  member has a final restored-or-classified-unrestorable status, and reads `false`/not-yet-exhausted
  otherwise.
- TC-14: given the repository's branch state, when this iteration's commits are inspected, then all of
  them are on `goal/market-compass` and `main` is unchanged.
- TC-15: given `apps/backend/tests/test_j10_recovery.py` and `test_provider_clients.py`, when run via
  the targeted single-file pytest invocation, then all pre-existing tests still pass alongside the new
  tests from TC-6/TC-7/TC-8, with zero regressions.
- TC-16: given AG-12 and AG-17, when this iteration's recovery run completes (any outcome), then a
  read-only count/hash check of `next_session_manifests` before and after shows no row's
  `prospective_eligible`, version, `content_hash`, or `manifest_hash` changed, and a checksum sweep of
  `reports/qa/goal-market-compass-iter-8-evidence/` before and after shows every file byte-unchanged.

## NOTES

- **Concurrent engine observed at dispatch time (operational safety flag, not a spec requirement).** Two
  `run-goal.sh --session-id market-compass --resume --interactive` processes were running on this host
  when this spec was written (process start times ~12:39 and ~13:49). This matches, and confirms as
  currently live rather than hypothetical, the "a second goal-mode engine may be running on this host"
  risk named in this iteration's dispatch context — the same class of condition behind the 2026-08-20
  freeze (memory overcommit + swap-thrash under concurrent goal-mode load). This iteration performs a
  large, non-reversible live-network write; confirming a single engine instance actually drives the
  fetch/backfill execution is recommended before it starts. Resolving or monitoring this is outside the
  goal-decomposer's own authority — flagged for the executing pipeline/owner.
- **Framework defect not fixed here.** The forbidden-lane recurrence (browser/replay executing against
  the damaged DB at both lean and full depth, iterations 2/6/8) lives in `scripts/automation/`, outside
  this Trendora-product iteration's surface. This spec plans around it (no Target/Required-still-passing
  journey whose verification would invoke that lane) rather than fixing it — flagged again for the
  evaluator/owner per the standing iter-8 blocker.
- **Carried, non-blocking owner questions (unchanged, not part of this iteration):** whether 3.44 GB is
  acceptable for J-09; J-06's "underlying run unavailable" wording; the rewording of J-01's first two
  test steps; whether an empty "next-session focus" is an acceptable honest result; whether MNST should
  ever join the recovery population.
- **Blueprint:** no edit made this iteration. `runs/goal-session-market-compass/state/blueprint.md` adds
  no row — this iteration introduces no displayed value, page, or endpoint, matching the iter-8
  coherence audit's confirmed-true "Data-contract additions: None" finding for this same class of work.
- An `assumptions.md` entry is appended for this iteration's one interpretive call (how strictly "every
  symbol restored or classified" must complete within this single iteration versus honestly naming a
  residual for a genuine external blocker).
