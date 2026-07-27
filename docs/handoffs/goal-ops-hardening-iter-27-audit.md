# goal-ops-hardening-iter-27 Audit Report

**Date:** 2026-07-27
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

Both ESCALATE-flagged anti-goal findings are genuinely closed in code, with tight tests and live
corroboration I re-derived myself rather than accepting from the handoffs. The AG-8 fix, however,
shipped with a newly-introduced fabricated-count defect that neither review nor QA caught — the
tolerated rollback destroyed more rows than its bookkeeping undid, so `rows_inserted` (a number that
reaches the user on `/data`) could report 2 while persisting 0. I reproduced it, fixed it, and added a
regression test; the combined suite now reports 201 passed. The remaining gaps are evidence gaps, not
code gaps: the browser-QA agent was killed by a quota before producing any row for J-05/J-07/J-08 — the
exact three journeys this iteration targets — so the DoD's first bullet is unmet, and TC-2's specified
full-page capture of the race does not exist.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the tolerated rollback fabricated `rows_inserted` and left `existing` claiming destroyed rows**

`apps/backend/app/engine/forward_testing.py:427` (as shipped: `pending_keys = []` reset inside the loop,
after `close_on`) and `:478-490` (the `except IntegrityError` handler).

The new guard called `session.rollback()`, which is **transaction-wide**. `_insert_run_forward_returns`
never commits — its callers do (`_backfill:557`, `backfill_run_forward_returns:1721`) — so every row
staged by an *earlier* symbol of the same call had been autoflushed-but-not-committed and was destroyed
by that rollback too. The handler nonetheless undid only the *current* symbol's `pending_keys`, because
the shipped code reset that list on every successful `close_on`. Result: `existing` retained keys whose
rows no longer existed, and the returned `inserted` counted rows that had been thrown away.

The dev's own TC-3 test (`test_iter27_insert_run_forward_returns_tolerates_mid_loop_autoflush_collision`)
cannot catch this because it stages the collision on the **first** symbol, where there is nothing earlier
to lose. I probed the case it does not cover — four symbols, concurrent row staged on the third:

```
PROBE: inserted_returned=2
PROBE: existing_set=[(1, 'AAA', 1), (1, 'BBB', 1)]
PROBE: rows_actually_in_db=['CCC']          # CCC is the staged concurrent writer's row
PROBE: rows_this_call_contributed=[] (count=0)
```

This is a fabricated number reaching the UI, not just an internal counter: `backfill_run_forward_returns`'s
`rows_inserted` flows through `data_manager.py:2978` (`prog.forward_returns_inserted += ...`) to
`data_manager.py:3627` and is rendered at `apps/frontend/app/data/page.tsx:2785` as
`"{job.forward_returns_inserted} forward returns inserted"`. It also contradicted the shipped docstring's
own claim ("so `existing`/the returned count stay truthful, never a fabricated insert count") and the dev
handoff's identical claim — which is why I graded it IMPORTANT rather than GAP: the affirmative honesty
guarantee was false, in a project whose *No fabricated data* / AG-3 anti-goals are critical.

**Fix applied.** `pending_keys` became `staged_keys`, accumulating every key staged since function entry
(the correct scope, since the rollback's blast radius is "since the last commit" and this function never
commits); the per-symbol reset was deleted; the handler now discards all of them. Behavior on the happy
path is unchanged. Proof: new regression test
`test_iter27_audit_returned_count_is_truthful_when_collision_follows_earlier_flushed_symbols`
(`apps/backend/tests/test_forward_testing_concurrency.py:800`) asserts the returned count equals the rows
actually persisted and that `existing` retains no destroyed key. Command and result cited in §4.

**B2 — GAP (not fixed): `_backfill`'s cross-call residual survives B1's fix**

`apps/backend/app/engine/forward_testing.py:545-557`. `_backfill` calls `_insert_run_forward_returns`
once per `ScannerRun` inside ONE transaction, sharing one `existing` set and committing only at `:557`.
A tolerated rollback during run K therefore also destroys runs 1..K-1's staged rows — which belong to
*earlier calls*, outside the fixed function's knowledge. `_backfill`'s accumulated `rows_inserted`
(surfaced via `warmup.py:195`) still over-reports for those runs, and `existing` still retains their
destroyed keys for the rest of that pass.

Not fixed deliberately: a correct fix needs either SAVEPOINT-scoped rollback (`begin_nested()`, whose
pysqlite semantics are a known trap and would be a risky change to introduce in an audit) or per-run
commits inside the boot warm-up (a transaction-granularity change with unmeasured cost over 1868 runs).
Both are redesigns, not surgical fixes. Mitigations that make this a GAP rather than IMPORTANT: it
self-heals on the next backfill (`existing` is rebuilt from the DB by `_streamed_existing_keys:504`), and
the **user-visible** `/data` job counter uses the per-run `backfill_run_forward_returns` path
(`data_manager.py:2965`), which B1's fix makes truthful. Recommend a scoped follow-up iteration.

**B3 — OBSERVATION: the colliding symbol itself is skipped, not retried**

`forward_testing.py:478-493`. The collision surfaces during symbol N's `close_on` autoflush, and the
handler's `continue` is at the symbol level — so symbol N is never processed by this call. The dev's own
TC-3 test asserts exactly this (`assert "BBB" not in by_symbol`). Benign for the target scenario (the
winning concurrent writer commits the whole run atomically at `_commit_forward_returns_concurrency_safe`,
so N's row exists) and covered by the module's idempotent-retry contract. Recording it because the spec's
TC-3 wording ("the loop continues processing the remaining symbols/horizons") reads slightly stronger
than what is implemented.

**B4 — OBSERVATION: the stale-coverage lookup assumes "different version" means "older"**

`apps/backend/app/engine/data_manager.py:1165-1177`. The fallback selects by `asof_key` alone ordered by
`computed_at DESC` and labels whatever it finds `"stale"` with `stale_dataset_version`. Since
`_membership_dataset_version` composes `max(scanner_runs.id)` and `count(scanner_runs)`, a stamp can in
principle move *backwards* (rows deleted), in which case a row under a non-current-but-not-older stamp
would still be described as "a prior scan". The served figures remain real and labelled, so this is
cosmetic. Verified the positive claims: `CoverageSnapshot.asof_key` is `Field(index=True)`
(`app/models.py:755`) so the "bounded, INDEXED lookup" claim holds, `.limit(1)` bounds it, and every
`_tag_coverage_status` caller passes a freshly-constructed dict (`json.loads` / a fresh compute /
`_coverage_not_yet_computed_payload`), so the in-place mutation cannot corrupt shared state.

**B5 — GAP (carried, out of this iteration's scope): unhandled `MemoryError` on `GET /api/evidence`, and 12–24 minute historical `/backtest` latencies, both inside this iteration's own QA window**

`logs/backend.log:81850` and `:81932` — two `Exception in ASGI application` entries after this window's
boot marker at `:81466` (`launching at 2026-07-26T20:17:21Z`), both `MemoryError` raised through
`app/api/evidence.py:34 → forward_testing.compute_drawdown_expectations_cached:2115 →
compute_drawdown_expectations:1979`. Neither function is touched by this diff; this is the known
memory-pressure class, not the IntegrityError this iteration closes. It is nonetheless a live, unhandled
exception on a user-facing endpoint occurring during the pipeline's own run, and the QA report explicitly
(and wrongly) denies it — see T1.

In the same window, `backtest_timing` records historical requests at `:81685-81686` (738.8s / 741.1s),
`:81766-81767` (1057.9s / 1061.4s) and `:82013`/`:82016` (1442.4s / 1443.8s — **24 minutes**), with
`resolved_run_ms` accounting for ~99% of each. `resolved_run` is untouched by this diff and the owner
budget decision on cold historical `/backtest` load is explicitly OUT OF SCOPE per the spec — but the
magnitude is 60–100× the "16–23s measured iter-26" figure that decision was framed around, and far
outside the bounded ~30s window the owner amendment contemplates. No artifact in this iteration records
it. Flagging for the evaluator's own scoring; not fixed here.

### Frontend Findings

**F1 — No defects found.** `apps/frontend/app/data/page.tsx:759-767` renders the stale notice only on
`coverage_status === "stale"`, with `data-testid="coverage-stale-notice"`, using this file's existing
muted-note tokens (`border-border` / `bg-surface-2` / `text-text-muted`) rather than the `text-warn`
alarm treatment — matching the spec's "routine, expected state, not an error" requirement. The
`not_yet_computed` and `current` renderings are untouched. `apps/frontend/lib/api.ts:2338-2348` types all
three fields. I read the dev's live capture rather than trusting the description:
`runs/goal-ops-hardening-iter-27/coverage-stale-label-only.png` renders the spec's exact text verbatim,
and the cropped top of `coverage-stale-panel.png` shows that label sitting above **real** figures —
PRICE HISTORY `1996-01-02 → 2026-07-22`, UNIVERSE 540, SYMBOLS 591, TRADING DAYS 5383, SNAPSHOT DATES
1868 — i.e. the exact all-zero sentinel the AG-3 finding was about is gone. TC-5/TC-6 are substantively
demonstrated (by developer self-verification; see T2 on independence).

### Test Findings

**T1 — IMPORTANT (documented, not fixable in code): the QA report rests on two claims that the evidence contradicts**

`reports/qa/goal-ops-hardening-iter-27-qa.md:61` states "No ASGI exceptions generated during request
window (pre-existing exception count in backend.log is unchanged)". The count is **not** unchanged: it
went from 13 to 15 during the pipeline's own boot window (B5). The same report's `:137` summary and
sign-off inherit that error.

Separately, QA's TC-01 re-run did not reproduce the race it claims to have exercised. QA used
`as_of=2011-03-10` (`logs/backend.log:81477`, `:81479`) — the very date the developer's own 19:59
reproduction had already created a run for. Both QA requests logged `write_taken=False` with
`resolved_run_ms=1.16` and `13.47` (`:81476`, `:81478`): the create-once run and its forward returns
already existed, so no forward-returns write race was possible. QA's TC-01 PASS is therefore vacuous as
corroboration of the fix.

This is a report-accuracy defect, not a product defect, so there is nothing in source to fix; I have
recorded the correction here (the later, authoritative artifact) rather than rewriting another agent's
report. Note that the *fix itself* is still well-corroborated — see T4.

The dev handoff carried a third, smaller inaccuracy — "exactly 1 occurrence in the whole 81,450-line
file" — when the file holds 12 further such entries from earlier boots (lines 11888, 11988, 13057,
13202, 13283, 16123, 26150, 26931, 27355, 27497, 27602, 27661). The reviewer repeated it. The
*per-window* claim it was supporting is correct and I re-verified it. I corrected the handoff in place.

**T2 — IMPORTANT (not fixable here): the DoD's browser-QA verification of J-05/J-07/J-08 does not exist**

`reports/phase-goal-ops-hardening-iter-27-ui-test-results.md` has zero rows for J-05, J-07 or J-08 — the
three journeys this iteration exists to fix, and the subject of DoD bullet 1. The browser-QA agent was
killed mid-run by an account usage limit; the file contains only the deterministic replay lane. I checked
whether usable evidence survived anyway and it largely did not:

- `reports/qa/.../evidence/UT-01-data-page-top.png` (21:34:15) shows `/data` still in its **loading
  skeleton** — "Checking backend…", "Checking board status…", grey placeholder blocks. It evidences
  nothing about the coverage panel.
- `reports/qa/.../evidence/UT-05-backtest-latest-fullpage.png` (21:34:54) is a genuine full-page
  `/backtest` capture showing a fully-rendered, non-blank evidence page — but of the **latest** view
  (`Viewing as-of 2026-07-22 (latest)`), not the never-scanned historical date TC-2 specifies. It is
  partial, not the specified artifact.

So TC-2 ("a full-page capture of the concurrent-race page state") has **no** evidence, and TC-6's browser
evidence is the developer's own screenshot, not an independent pass. Stated plainly rather than inferred
either way: this is an unrun check, not a failed one.

**T3 — GAP: the J-06 golden replay FAIL is a brittle shared-state assertion, not an iter-27 regression (investigated independently; live re-confirmation not possible)**

`runs/goal-session-ops-hardening/journey-scripts/J-06.json` step 1 asserts the literal text `"DEGRADED"`
on `/` — an incidental capture of the `PreflightBanner` verdict at recording time, unrelated to J-06's
actual subject ("Pages load only what they need"; steps 2-6 assert page-specific content). That verdict
comes from `compute_preflight`'s drift component (`app/engine/readiness.py:400-406`), which reads a
single **session-unscoped** artifact via `resolve_drift_report_path()` (`app/engine/drift.py:53-66`,
default from `config.yaml`'s `data_quality.drift.report_path`).

I checked the artifact rather than accepting the ux-reviewer's account:
`runs/goal-session-mcp-loop/state/drift-report.json` is `{"status": "drift", 584 affected}` at HEAD and
`{"status": "clean", 0 affected}` in the working tree, mtime `2026-07-26 21:23:42` — **8 minutes before**
the replay screenshots (21:31:36–21:32:01). A clean drift artifact yields GO, so the banner could not have
read DEGRADED at replay time. Corroborated visually in two independent captures that both read
"GO — today's board is current.": `UT-05-backtest-latest-fullpage.png` (21:34) and the dev's
`coverage-stale-panel.png` (21:01).

Attribution: iter-27's diff touches none of `readiness.py`, `drift.py` or `preflight-banner.tsx`. The
only writer of that artifact in product code is `data_manager._check_drift` (`:2682`), reached from the
post-fetch stage of a fetch/both job (`:3987-3991`); the readiness/drift tests all monkeypatch
`TRENDORA_DRIFT_REPORT_PATH` to a tmp dir, so pytest is not the polluter. Note the replay lane is
self-defeating here: **J-01's own golden script starts a Data Manager job** (steps 2-4) before J-06 runs,
so the suite can rewrite the artifact that a later step asserts against.

I did not start the services to re-poll `/api/health` live — the 30-year backend boot for a single banner
string is not a justified spend against this host's declared ceiling (AG-10), and the two independent
screenshots already settle what the banner read. Conclusion: not a product regression from this diff;
a brittle, cross-session-shared golden assertion. Recommend scoping `readiness.drift.report_path` per
goal-mode session and dropping the incidental "DEGRADED" expectation from J-06 step 1.

**T4 — OBSERVATION (favourable): the AG-8 fix has better live corroboration than any report claims**

Independently of the dev's own reproduction, three *genuine* never-scanned-date concurrent races ran
during the QA window and all four requests returned HTTP 200 with no IntegrityError:
`:81685`/`:81686` (`write_taken=True` / `False`) and `:82013`/`:82016` (`write_taken=True` / `False`, the
`as_of=2015-09-09` pair). A `write_taken` True/False split is the signature of exactly the create-once
race this iteration targets. Combined with the developer's own 19:59 pair (`resolved_run_ms=80588` /
`80819`, `write_taken=True`/`False`, both 200, and zero `Exception in ASGI application` between the boot
marker at `:81392` and `:81466` — I re-derived this from the raw line numbers), TC-1 is solidly met.

**T5 — GAP: TC-7's default-view case is asserted only on the explicit-as-of path**

No test asserts `coverage_status == "not_yet_computed"` for the **default** (`as_of=None`) view against a
DB with zero `CoverageSnapshot` rows. `test_data_manager.py:2534` covers the explicit dataless as-of, and
`test_api_data.py::test_get_data_overview_zero_coverage_rows_serves_honest_sentinel_never_500` covers the
default view's payload shape but not the new field. Both reach the same `return` statement
(`data_manager.py:1178`), so risk is low.

**T6 — Test quality otherwise good.** The four pre-existing byte-equality assertions were not weakened:
each now asserts the new field's exact value *and* compares the stripped remainder to an independently
computed payload (`test_data_manager.py:2299-2303`, `:2501-2502`, `:2525-2526`; `test_api_data.py:124-130`).
TC-5's new test is a faithful reproduction of the root cause — it asserts the stamp actually advanced
(`v2 != v1`), that the resolved as-of is unchanged, that the current-stamp row genuinely does not exist,
and then the exact served values. TC-4's narrow-catch test is a monkeypatch rather than a second real
constraint, which is a reasonable determinism trade-off and is honestly labelled as such.

---

## 3. Domain Assessment

The two diagnoses in the spec were correct and I confirmed both against the code rather than the
narrative. Fix 1 addresses the right control-flow point: SQLAlchemy's autoflush genuinely makes the
*next* symbol's `close_on` read the site of the duplicate-key failure, which is why the pre-existing
`_commit_forward_returns_concurrency_safe` guard at the final commit could never have caught it, and why
the iter-26 traceback pointed at `_insert_run_forward_returns:390`. The narrowness requirement was met
honestly — `_is_forward_return_duplicate_key_collision` matches the DBAPI's own constrained-column
message, so a NOT NULL or foreign-key violation still propagates, and the guard is genuinely not a
blanket `except IntegrityError`. Where the implementation fell short was not the diagnosis but the
transaction semantics of its remedy (B1) — a classic case of a guard whose blast radius is wider than its
bookkeeping.

Fix 2 is the better of the two. It correctly refuses the tempting request-path recompute (which would
have reintroduced the whole-table prefill the Coverage payload redesign eliminated), keeps a single
computing module and endpoint, adds three purely additive fields, and — importantly — does not persist
those fields back into `coverage_snapshot.payload_json`, so the stored row stays byte-identical to a
fresh compute and the existing equality invariants survive. Serving real prior-scan figures under an
honest label is strictly more truthful than the all-zero sentinel it replaces, and the assumption is
logged and reversible.

Freeze discipline held: `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
`ensure_historical_forward_aggregates_dispatched` and J-08's serving split are untouched, `api/data.py`
correctly needed no change, and everything the spec listed OUT OF SCOPE (audit finding B2, B-1107, the
serving-split monkeypatches, the OWNER BUDGET AMENDMENT sections, the demo JSON) is unmodified.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/forward_testing.py` | `_insert_run_forward_returns`: `pending_keys` → `staged_keys`, accumulating every key staged since entry instead of resetting per symbol; the tolerated-collision handler now discards all of them from `existing` and from `inserted`. Fixes the fabricated `rows_inserted` / stale `existing` after a transaction-wide rollback (B1). Docstring corrected — it had asserted the very guarantee that was false. |
| 2 | Important | `apps/backend/tests/test_forward_testing_concurrency.py` | New regression test `test_iter27_audit_returned_count_is_truthful_when_collision_follows_earlier_flushed_symbols` — stages the concurrent row on the **third** of four symbols so earlier rows are already autoflushed when the rollback fires; asserts returned count == rows actually persisted, and that `existing` retains no destroyed key. Fails on the pre-fix code (returned 2, persisted 0), passes after. |
| 3 | — | `docs/handoffs/goal-ops-hardening-iter-27-dev.md` | Corrected two claims the audit invalidated: the "undo that symbol's bookkeeping … never a fabricated insert count" description (now describes the fixed behaviour and records B1), and the false "exactly 1 occurrence in the whole 81,450-line file" ASGI-exception count. |

**Verification of the fixes (single combined invocation, per the host constraint — no full suite, no
concurrent pytest):**

```
cd apps/backend && .venv/bin/python -m pytest \
  tests/test_forward_testing_concurrency.py tests/test_data_manager.py tests/test_api_data.py -q
201 passed in 298.70s (0:04:58)
```

201 = the 200 the developer, reviewer and QA each measured, plus my new regression test. Zero failures,
zero regressions in any touched file; no pytest process left running afterwards. This also serves as the
audit's independent re-verification of TC-11.

**Other DoD items re-verified independently rather than accepted:**

- **TC-10** — `reports/perf-budgets.md:3817` now reads `2026-07-26T18:14:25Z`, matching the table header
  at `:3825`. Ground truth: the boot marker `=== start-backend.sh: launching at 2026-07-26T18:11:43Z ===`
  at `logs/backend.log:80603`, ~2.7 min before the reading. Exactly one line changed in that section.
- **TC-12** — `coverage_status`, `stale_dataset_version`, `stale_computed_at` appear verbatim in
  `runs/goal-session-ops-hardening/state/blueprint.md:276` and `:339`, matching the served JSON. No
  renamed, dropped or extra field. The reviewer's NOTE stands: those rows still carry the decomposer's
  "TARGETED this iteration, not yet built" tag — documentation staleness only, no code impact.
- **TC-1** — re-derived from raw log line numbers (see T4), not from the handoff.

---

## 5. Recommended Next Step

Proceed, but do not let the evidence gap close silently. Specifically:

1. **Re-run browser-QA for J-05, J-07 and J-08** before this iteration is scored as fully verified. That
   is DoD bullet 1 and it did not run; the developer's evidence is concrete and I confirmed it visually,
   but it is self-verification. TC-2 in particular needs its specified artifact: a full-page capture of
   `/backtest` during a *never-scanned historical* concurrent race, not the latest view.
2. **Fix the J-06 golden assertion, not the product.** Drop the incidental `"DEGRADED"` expectation from
   step 1 and scope `readiness.drift.report_path` per goal-mode session, so one session's data job cannot
   flip another's golden assertion — and so J-01's own job step cannot invalidate J-06 later in the same
   replay. Until then this FAIL will recur and read as a regression every iteration.
3. **Open a scoped follow-up for B2** (`_backfill`'s cross-call rollback residual). It needs a SAVEPOINT
   or per-run-commit redesign with its own measurement, not a patch bundled into an unrelated iteration —
   the same "never bundle two risky concurrency changes" rule this spec applied to audit finding B2.
4. **Surface B5 to the owner** alongside the already-open cold-`/backtest` budget decision: this
   iteration's own logs contain 12–24 minute historical request latencies and two unhandled `MemoryError`s
   on `/api/evidence`. Both are outside this diff, but the open budget question was framed around 16–23s
   and the newer evidence is two orders of magnitude worse.
