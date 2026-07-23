# goal-ops-hardening-iter-16 Audit Report

**Date:** 2026-07-23
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-08's core architectural claim holds under direct inspection, not just under the handoff's description:
`compute_forward_aggregates` has exactly one remaining caller (`forward_aggregates_ingest_cached`), the
`is_latest` request path reaches only the read-only resolver, and the completeness/cutover contract makes
a mixed-`dataset_version` response structurally impossible — all three verified in source and re-proven by
the 10 targeted tests plus the operator's 68-row live pass. One **IMPORTANT** user-facing honesty defect
survived review/QA/browser-QA/ux-regression and was found and **fixed** in this audit: the new refreshing
banner asserted that a warm was in flight and promised an automatic update, and neither claim is true.
Three documented gaps remain (the `not_yet_computed` fallback on an as-of-advancing ingest, a sticky
`refreshing` state with no self-heal, and the ≤1.5 s budget breached on 11/68 live polls) — all disclosed,
none silent, none compromising the phase goal.

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap): the default view falls to `not_yet_computed`, not `refreshing`, whenever an ingest advances the latest as-of date**

`resolved_forward_aggregate_evidence` resolves all three states strictly within one `asof_key`
(`apps/backend/app/engine/forward_testing.py:1202`, `1216-1242`), and the default `/backtest` view resolves
its as-of to `max(ScannerRun.asof_date)` (`apps/backend/app/api/backtest.py:74` →
`app/engine/scanner.py:295-297`, `315`). So the moment an ingest commits a snapshot for a NEW latest date —
`data_manager.py:3173` calls this "the common single-latest-date backfill" — the default view switches to
an `asof_key` that has never had a cache row, and serves `not_yet_computed` (empty state) for the whole
warm window instead of the previous date's last-good evidence.

Verified, not inferred. A throwaway probe on a small fixture (written, run host-guard-confined, then
deleted) exercised `app.api.backtest.backtest(as_of=None, ...)` before and after committing a new
later-dated `ScannerRun`:

```
BEFORE new snapshot: asof=2025-01-10 status='ready' horizons=[1, 5, 10, 20, 60]
DURING warm (new latest committed, aggregates not yet warmed):
                     asof=2025-01-13 status='not_yet_computed' gen=None horizons=[]
```

The operator's TC-16 pass could not have caught this: it backfilled `2025-05-22`, a historical gap date
(`reports/perf-budgets.md:2739`), and browser-QA UT-02 backfilled `2025-05-20` — both bump the stamp while
leaving the latest as-of at `2026-07-22`, which is exactly the `refreshing` case. The as-of-advancing case
has zero live or unit coverage.

Not fixed, and deliberately so. This is **spec-conformant**: the iteration spec defines `not_yet_computed`
as "no complete version has ever existed for this `asof_key`" (IN SCOPE bullet 2) and TC-6 encodes the same
per-`asof_key` scoping. Widening the fallback to serve a prior as-of's evidence would change J-08's
contract and is an owner/evaluator design call, not a surgical audit fix. **I weighed IMPORTANT and landed
on GAP** because no specified behavior fails — but the evaluator should weigh it explicitly, because
goal.md J-08 step 2 promises the last-good fallback *"labeled with that version's served as-of"* on a
version bump, and in this flow no last-good is served at all. Step 5 frames `not_yet_computed` as the
"fresh-install shape", which this is not.

**B2 — GAP (gap): `refreshing` is sticky — any stamp bump not followed by an ingest warm leaves the latest view labeled `refreshing` indefinitely**

`_dataset_version` is `f"r{max(ScannerRun.id)}-f{count(ForwardReturn)}"`
(`apps/backend/app/engine/research.py:1532-1547`). Any new `ScannerRun` row bumps it — including the
create-once snapshot a user triggers merely by navigating to an as-of date that has no snapshot yet
(`resolve_run` → `run_scan`, `app/engine/scanner.py:334-344`), and including forward-return inserts from
`backfill_run_forward_returns` (`backtest.py:73`). Pre-iter-16 the request path absorbed such a bump with a
cold recompute (slow, but self-healing). Post-iter-16 the request path cannot compute at all, so the latest
view reports `refreshing` until the next ingest's finalize warm re-stamps it.

Verified by probe (same method as B1) — note it does **not** self-heal on a subsequent request:

```
BEFORE: stamp=r1-f5 asof=2025-06-10 status='ready'
AFTER : stamp=r2-f5 asof=2025-06-10 status='refreshing'   # only change: one older-dated ScannerRun added
AGAIN : status='refreshing'   # second request — self-heals = False
        evidence values identical to the pre-bump ready payload = True
```

Read-only inspection of the live DB confirms this is not theoretical: `forward_aggregate_cache` holds
`asof_key='2026-07-10'` at stamp `r1860-f3941380` while the current stamp is `r1861-f3944105` — i.e. the
browser-QA session's own historical navigation bumped the stamp mid-run (`r1860` → `r1861`). The latest key
`2026-07-22` happens to sit at the current stamp right now (`ready`), because the ingest warm at 21:56:07
came after that bump.

The **served values remain correct and honestly labeled** with their own generation timestamp, so this is a
disclosure-quality gap, not a correctness one — but it is the reason F1 below mattered.

**B3 — OBSERVATION: `evidence_generated_at` carries no timezone designator despite being contracted as "ISO 8601 UTC datetime"**

Written as `datetime.now(timezone.utc)` (`forward_testing.py:1147`) but read back naive from SQLite and
serialized as `generated_at.isoformat()` (`forward_testing.py:1228`), producing
`"2026-07-23T20:57:22.711666"` — no `Z`, no offset (confirmed in the live poll CSV
`runs/goal-ops-hardening-iter-16/tc16-backtest-poll.csv` and in QA's own capture). The spec's Data-contract
and `apps/frontend/lib/api.ts:1095` both document it as UTC. The frontend is accidentally safe because
`formatIsoDateTime` slices rather than parses (`apps/frontend/lib/dates.ts:88-94`), but an MCP client doing
`datetime.fromisoformat(...)`/`new Date(...)` gets a local-interpreted value. Left alone: every timestamp
this codebase serves follows the same naive-UTC convention, so changing it here would be a cross-cutting
change, not a surgical one.

**B4 — OBSERVATION: the served horizon set is taken from the stored rows, not the configured list**

`complete` accepts any version whose row set is a **superset** of the configured horizons
(`forward_testing.py:1216-1220`) and `_serve` then emits every stored horizon (`:1224`). The old code
emitted exactly `cfg.walk_forward.horizons`. Since `_dataset_version` is data-derived, shrinking
`walk_forward.horizons` in config would not bump the stamp, and the now-unconfigured horizon's stale row
would still be served. No impact today (config is static); noted so a future horizon-config change does not
surprise anyone.

**B5 — OBSERVATION: the historical branch reads and deserializes each horizon payload twice**

`backtest.py:80-87` (and `tools.py:208-215`) calls `forward_aggregates_ingest_cached` per horizon — each a
cache HIT that `json.loads`es its payload and discards it — and then re-reads and re-parses the same rows
through the resolver. Correct, just redundant; irrelevant next to the pre-existing ≈83 s first-view compute
on that path.

**B6 — OBSERVATION (confirms the reviewer's NOTE, `review.md:31`): the cutover completeness check has no cross-horizon lock, but the failure mode is bounded**

Two writers committing the 4th and 5th horizon of the same version concurrently can each read "incomplete"
(`forward_testing.py:1126-1134`) and both skip the prune. I traced the consequence: the resolver then finds
the current version **complete** and serves `ready` correctly — only the superseded rows leak, and the next
version that completes deletes them all in one shot (`:1136-1143`, filtered by `asof_key` alone). Serving is
never wrong; growth is self-healing. Agreed with the reviewer that this needs no change while the trigger is
one sequential per-job horizon loop.

### Frontend Findings

**F1 — IMPORTANT (fixed): the refreshing banner asserted two things that are false**

`apps/frontend/app/backtest/page.tsx` (pre-fix, lines 267-272) rendered:

> "A newer dataset version **is still being warmed**. The forward-tested evidence below is the last
> complete version, generated `<ts>`. **This updates automatically once the new version finishes
> warming** — no partial or fabricated figures are shown in the meantime."

Both bolded claims are wrong:

1. *"is still being warmed"* — `refreshing` only means the current stamp differs from the served complete
   version's stamp (`forward_testing.py:1232-1240`). B2 proves this state stands with **no warm running at
   all**, indefinitely. The banner asserts a system state the backend never checked.
2. *"updates automatically"* — `BacktestPage`'s only fetch effect depends on `[asOf, readiness]`
   (`page.tsx:73-92`); there is no interval or refetch. `readiness` is the plain string from
   `useReadiness()` (`apps/frontend/components/readiness-provider.tsx:57`, `60`), which stays `"ready"`
   across every poll, so the dep never changes and the effect never re-runs. This is false **in every
   case**, not just the B2 edge case — browser QA's own UT-04 needed a page *reload* to see the new
   version.

The spec required "a calm, **factual** banner" (IN SCOPE / Frontend). A spinning banner that promises an
update that will never arrive is the "misleading UI" failure mode this audit exists to catch, and it is the
one claim in the iteration nobody verified: review, QA, browser-QA (UT-02/UT-09) and ux-regression all
checked tone, tokens, position and heading — none checked whether the sentences were true.

**Fix applied** (copy only; heading, tone, `data-testid="evidence-refreshing"`, Card/`Loader2` treatment and
position all unchanged, so UT-02/UT-09's structural evidence still stands):

> "The dataset has changed since this evidence was generated, and the newer version is not complete yet.
> The forward-tested evidence below is the last complete version, generated `<ts>` — no partial or
> fabricated figures are shown in the meantime. Reload this page after the next ingest finishes to pick up
> the new version."

Every clause is backed by the resolver's own state: the stamp differs, the current version is not in
`complete`, the served set is one complete version, and a reload is genuinely what re-fetches.

**F2 — GAP (gap): the `not_yet_computed` call-to-action is wrong in B1's flow and uses a term absent from the rest of the UI**

`page.tsx:239` reads "…**run an ingest** to populate the forward-tested evidence for this date." In B1's
scenario the user has just run (or is running) exactly that, so the instruction is actively misleading; and
ux-regression separately verified by grep that "ingest" appears nowhere else as user-facing copy, while
`/data`'s own labels are "Backfill snapshots" / "Fetch EOD prices"
(`reports/phase-goal-ops-hardening-iter-16-ux-regression.md`, Label Confusion). Not fixed: the spec
prescribes this wording verbatim, ux-regression already filed the reword as a non-blocking follow-up, and
the underlying B1 behaviour — not the copy — is the thing worth an owner decision.

**F3 — OBSERVATION: the empty state repeats itself** — `title` is "Backtest evidence not yet computed" and
`description` opens with the same sentence again (`page.tsx:238-239`).

### Test Findings

**T1 — GAP (gap): the `loaded_engine` pre-warm is still unverified live, but its blast radius is smaller than the handoff claims**

`apps/backend/tests/conftest.py:77-81` now warms the latest run's `ForwardAggregateCache` inside the
session-scoped fixture. Neither dev, reviewer nor QA ran a single `loaded_engine`-dependent test (the ~80 min
fixture is out of scope this session), so this stands unproven — carried as the one entry in
`status.json.blockers` and as the review's only MINOR.

I did narrow the risk rather than restate it. The dev handoff says the change "affects ~29 test files" and
names `test_api_engine.py`/`test_api_research.py` as at-risk; a grep shows only **two** files outside the
new one actually read `evidence_by_horizon` — `test_api_backtest.py` (9 refs) and `test_mcp_window.py`
(2 refs) — and neither `test_api_engine.py` nor `test_api_research.py` references it at all. I also traced
the two ways the fixture could still bite and found both benign: (a) `_dataset_version` reads only the
passed session (`research.py:1540-1546`), so calling the warm before `db_module.set_engine(engine)` is safe;
(b) if a test mutates the DB and bumps the stamp, the resolver degrades to `refreshing` and still serves the
same complete row set, so content assertions hold — only a hypothetical `evidence_status == "ready"`
assertion would break, and none exists. Residual risk: low, but still `unknown`, not `verified`. The one
confirming run (`test_api_backtest.py::test_backtest_evidence_by_horizon_shape_and_keys`) remains the right
next step.

**T2 — GAP (gap): two DoD-relevant verifications were skipped, both honestly**

`not_yet_computed` has **zero** live-browser evidence (UT-03 SKIPPED — reaching it would require deleting
cache rows from the working DB), and UT-J-04 (required-still-passing journey J-04) was not replayed
(requires kill/restart, blocked this session). So DoD item "J-01/J-03/J-04/J-05 remain green via
deterministic replay (TC-15)" is met for three of four journeys; J-04 is `unknown`, mitigated only by the
fact that its files are untouched (`git status` confirms no change to `main.py`, `app/api/health.py`,
`app/engine/readiness.py`, `app/engine/warmup.py`, or `scripts/`). Both skips are labelled SKIPPED in the
merged results rather than asserted PASS — the correct call.

**T3 — OBSERVATION: no route-level `refreshing` test.** `refreshing` is proven at the resolver level
(`test_forward_testing_serving_split.py:159-209`, a tight test that asserts every horizon's payload is
byte-equal to V1's stored JSON and that the timestamp is V1's own max `created_at`), and both request entry
points are proven for `ready`/`not_yet_computed` with a monkeypatch-to-raise guard — but no test drives
`app.api.backtest.backtest` in the `refreshing` state. Low value to add: the route is a pure pass-through of
the resolver's three keys.

---

## 3. Domain Assessment

The core logic is correct and, unusually for a redesign of this size, correct for the right reasons.

**The compute-vs-serve split is real, not nominal.** `resolved_forward_aggregate_evidence`
(`forward_testing.py:1163-1242`) contains no branch that can reach `compute_forward_aggregates` — no MISS
path, no lock, no timeout fallback. That is a structural guarantee, not a policy one, and the tests prove it
the right way: they monkeypatch `forward_aggregates_ingest_cached` **to raise** at both request entry points
(`test_forward_testing_serving_split.py:310-405`) rather than merely counting calls, so a future refactor
that reintroduces a compute path fails loudly. `data_manager.py:3230` remains the ingest warm's only call
site with its `MemoryError` isolation byte-unchanged.

**The completeness/cutover contract is the right shape for the bug it closes.** Grouping rows by
`dataset_version` and requiring the full configured-horizon set before a version is eligible
(`:1212-1220`) makes a mixed response impossible by construction rather than by discipline — and the live
DB still contains the exact corruption that motivated it (`asof_key='2026-07-17'` split 4 rows at
`r1193-f2522006` / 1 row at `r1272-f2674831`), which the new resolver correctly refuses to serve as a
mixed payload and which the historical carve-out will clean on first view. The prune is `asof_key`-filtered
in both directions (`:1128-1140`), so completing one identity never touches another's rows, and the
completeness read is a single `asof_key`-filtered SELECT (`:1205-1210`) — TC-18's claim verified in source,
not just by its test's SQL-capture assertion.

**Honesty of the serving states is genuine at the API layer.** All three states return HTTP 200,
`not_yet_computed` returns `{}` rather than a partially-populated map, and the operator's 68-row live pass
independently confirms the state machine end-to-end: exactly two distinct generations across 68 polls, the
16 `refreshing` polls all serving the *prior* generation, and the flip to the new generation landing on the
same row as the flip to `ready` (`reports/perf-budgets.md:2751-2766`). That is a stronger proof than any
unit test could give, and the write-up's independent recomputation — including flagging the operator's own
median convention error rather than silently adopting it — is exactly the standard this session should hold.

**Where the domain model is thinner than the journey text.** J-08's mental model is "one dataset version
supersedes another for the same view". The implementation's identity is `(asof_key, dataset_version)`, and
the *as-of itself* can move (B1) or the stamp can move without any producer running (B2). Both follow
directly from `_dataset_version` being a global row-count fingerprint while the cache warm targets exactly
one key. Neither breaks a stated acceptance criterion, and neither produces a wrong number — but together
they are why the UI copy had to stop asserting *why* the state exists (F1) and stick to *what* it is.

**Anti-goals.** AG-3: byte-identity holds by construction (`json.loads` of the same stored payload the
producer wrote) and is asserted against a fresh compute in `test_forward_testing_serving_split.py:125-156`;
`compute_forward_aggregates` is untouched (the diff's first hunk starts after its closing brace). AG-5: the
fallback serves a strictly *older* complete version, never a partially newer one — the cutover guarantees
it. AG-8: the new read is `asof_key`-filtered and bounded to ~2 versions' rows per identity. AG-10: no
launch script, no `main.py`, no host-guard file touched (`git status`). AG-7/AG-9: nothing added.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/frontend/app/backtest/page.tsx:267-273` | Replaced the refreshing banner's two false claims ("a newer dataset version **is still being warmed**", "this **updates automatically**") with statements the resolver can actually back, plus an accurate "reload after the next ingest" instruction. Heading, tone, `data-testid`, icon, Card treatment and position unchanged. |
| 2 | Important | `apps/frontend/app/backtest/page.tsx:253-258` | Updated the component's own comment to record the two invariants the copy must not violate (never assert a warm is in flight; never promise an auto-update — no poll exists), so the constraint survives the next edit. |
| 3 | — | `docs/handoffs/goal-ops-hardening-iter-16-frontend.md` | Added an "Audit correction" section superseding the handoff's description of the banner body, per the post-fix rule to correct invalidated claims. |

**Post-fix verification.**

- `cd apps/frontend && taskset -c 0-3,8-11 npx tsc --noEmit -p tsconfig.json` → **exit 0, 0 errors**.
- `grep -rn "still being warmed\|updates automatically" apps/frontend/app apps/frontend/components` →
  **no hits** (both claims gone from the whole frontend).
- Backend unaffected, re-confirmed green anyway:
  `taskset -c 0-3,8-11 OMP/OPENBLAS/MKL/NUMEXPR=4 .venv/bin/python -m pytest tests/test_forward_testing_serving_split.py -q`
  → **10 passed in 1.59s**.
- Diff re-read: the change touches only the comment block and the one `<p>` body. No behavioural code, no
  new dependency, no scope creep.
- **Honest limitation:** this wording has **not** been re-rendered in a browser. The Trendora backend and
  frontend were not listening on `:8255`/`:3255` at audit time (`curl` → connection refused; no matching
  process; I did not start or stop anything, per the standing constraint), and browser-QA's UT-02 screenshot
  still shows the old text. The next live pass should re-capture the banner — a one-line check.

No other fix was applied. B1/B2/F2/T1/T2 are GAP-level and fixing them would either contradict the spec's own
state definitions (B1), require a design decision the owner owns (B2), or spend the blocked ~80 min fixture
(T1) — all scope creep for an audit.

---

## 5. Recommended Next Step

**Proceed to the evaluator**, with three items placed in front of it rather than left in the artifacts:

1. **B1 is the item the evaluator must actually rule on.** Whether goal.md J-08 can be scored `passing` —
   and with it J-06/J-07, which are held solely on this residual — depends on whether "the last COMPLETE
   stored version is served during a refresh" is required to hold when the ingest *advances the as-of*, not
   only when it backfills a gap. The live TC-16 and browser-QA evidence both cover only the gap-backfill
   case. If the answer is "yes, it must hold", the fix is a follow-up iteration that lets the fallback cross
   as-of boundaries (with the served as-of labeled, exactly as J-08 step 2's wording already implies) — not
   a patch to this one.
2. **The latency clause is a documented DoD miss, not a pass.** The spec's DoD says the `/backtest` budget
   "is met in all three serving states (TC-3, TC-6, TC-16)"; TC-16 measured 11/68 polls over ≤1.5 s (max
   12.655 s), all inside the ~380 s ingest window, versus 0.13-0.17 s outside it and versus iter-15's
   178.74 s cold MISS. That is a ~14x improvement and a WARN, and `reports/perf-budgets.md:2834` correctly
   declines to self-score it. It should be scored, not inherited.
3. **Two cheap closures worth requesting from the operator before this session's next heavy pass:** one
   `loaded_engine`-dependent test (`test_api_backtest.py::test_backtest_evidence_by_horizon_shape_and_keys`)
   to close T1 with a live result, and one browser look at the corrected refreshing banner plus the
   never-yet-rendered `not_yet_computed` state (T2) — the latter on a disposable DB copy, never the working
   one.

No blocking work remains in this iteration's own scope.
