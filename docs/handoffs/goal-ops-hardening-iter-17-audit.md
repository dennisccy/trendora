# goal-ops-hardening-iter-17 Audit Report

**Date:** 2026-07-24
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The load-bearing fix is real and correct: `resolved_forward_aggregate_evidence` now crosses `asof_key`
boundaries with a strictly-older filter (AG-5 safe), reserves `not_yet_computed` for the true
fresh-install shape, and both serving endpoints emit the new `evidence_asof` identically — verified by
reading the diff, re-running the 15 unit tests myself (15 passed, 2.17 s), and reading the live
`:8255` response (`evidence_status: "ready"`, `evidence_asof: "2026-07-22"`, `evidence_generated_at:
"2026-07-24T02:11:25.114967+00:00"` — B3's UTC designator is live). One IMPORTANT frontend defect the
review and QA both missed was found and fixed during this audit: in the *only* state this iteration
introduces (cross-`asof_key` `refreshing`), the evidence section's own copy asserted a window
("expanding window ≤ D", "every snapshot dated on or before D", "Snapshots contributing (≤ D): n")
labeled with the page's requested as-of while the served numbers came from an OLDER one — directly
contradicting the new banner two lines above it. Two DEFINITION OF DONE bullets remain genuinely
unmet and honestly disclosed: TC-8 (no live exercise of the cross-boundary fallback — the DB has no
future trading day, independently re-verified) and TC-10 (no fresh, directly-comparable latency
measurement recorded). Neither is a code defect; both are the evaluator's to weigh.

---

## 2. Findings

### Backend Findings

**B1 — GAP (documented, not fixed): the widened fallback materialises every older row's `payload_json`,
unbounded**
`apps/backend/app/engine/forward_testing.py:1286-1292` selects `asof_key, horizon, dataset_version,
payload_json, created_at` for **every** row with `asof_key < requested` and materialises it with
`.all()`, even though at most ONE `(asof_key, dataset_version)` group's payloads are ever served
(`:1305-1310`). The payload column is the heavy one and is not needed for the selection step at all.
Measured read-only on the live DB right now: `forward_aggregate_cache` = 25 rows / 5 `asof_key`s /
818,595 payload bytes (avg 32.7 KB, max 33.1 KB per row), so the current worst case is ~650 KB per
fallback request — trivial. Growth is +5 rows (~164 KB) per distinct as-of that is either ingested as
the latest (`data_manager.py:3230`, one key per job, not per date) or viewed historically on
`/backtest`/`query_backtest` (`api/backtest.py:105`, `mcp/tools.py:222`), so ~1,000 distinct as-of
views would push ~165 MB through a single request under this host's 6 GB `ulimit -v`. This table does
**not** scale with the deep price basis, so the docstring's AG-8 reasoning is defensible and I am
**not** calling it an AG-8 violation today — but the fix is cheap and belongs in a later iteration:
project the four metadata columns in the wide scan, then read payloads for the winning
`(asof_key, dataset_version)` only. Related, already noted by the reviewer: no index on `asof_key`
(the only indexes are the PK, the unique triple, and `ix_forward_aggregate_cache_horizon`).

**B2 — OBSERVATION: the `"all"` sentinel is excluded from the fallback by ASCII ordering, not by a
guard**
`forward_aggregates_ingest_cached` writes `asof_key = as_of.isoformat() if as_of is not None else
"all"` (`forward_testing.py:1083`). The fallback filter is a string comparison
(`asof_key < '<ISO date>'`), and `'a'` (0x61) sorts above every digit, so an `"all"` row can never be
selected or mixed into a served payload. Safe today (all three live call sites pass a concrete date;
the live table holds only ISO keys), but the safety is incidental. Worth one defensive line if an
all-history warm is ever added.

**B3 — OBSERVATION: the B5 gate adds one extra resolver pass on the COLD historical path**
`api/backtest.py:103` / `mcp/tools.py:220` now resolve first and only then run the ensure-loop. On an
already-warm historical date this saves five redundant cache-hit reads+`json.loads` (the claimed win,
real). On a *cold* historical date the resolver now runs the widened older-key scan **before** the
ensure loop — work the pre-iter-17 code never did. Output is byte-identical (handoff claim holds);
the added cold-path cost is simply not mentioned in the handoff or in `reports/perf-budgets.md`'s B5
write-up. Negligible at current table size (see B1).

### Frontend Findings

**F1 — IMPORTANT (fixed): the evidence section's window label contradicted the new banner in the exact
state this iteration ships**
Pre-fix, `apps/frontend/app/backtest/page.tsx:249` passed `asofDate={backtest.asof_date}` into
`EvidenceAggregateSection`, whose copy makes three factual claims bound to that prop
(`apps/frontend/components/evidence-panels.tsx:237` "Forward-tested evidence (expanding window ≤ …)",
`:241` "every snapshot dated on or before …", `:263` "Snapshots contributing (≤ …): n"). Until this
iteration those claims were always true, because the served evidence was always for the requested
as-of (`ready`, or a prior *version* of the same date). The new cross-`asof_key` fallback breaks that
invariant: the served aggregate's window ends at the OLDER `evidence_asof`, so all three sentences —
including the `n_runs` count they attach — assert a date the payload does not cover, two lines below a
banner that says otherwise. This is precisely the failure mode the phase's own Visual Requirements
warned about ("verify every new sentence against the code that would have to make it true").
Reproduced in a real browser by rewriting only the client's own `/api/backtest` response (no backend,
DB or service touched):

| | banner | section header | "Snapshots contributing" |
|---|---|---|---|
| pre-fix code | *(pre-iter-17 banner: no as-of)* | `≤ 2026-07-22` | `≤ 2026-07-22` |
| iteration code, pre-audit-fix | `evidence as of 2026-07-21` | `≤ 2026-07-22` ✗ | `≤ 2026-07-22` ✗ |
| after this audit's fix | `evidence as of 2026-07-21` | `≤ 2026-07-21` ✓ | `≤ 2026-07-21` ✓ |

Fixed at the single call site (`page.tsx:258-261`): `asofDate={backtest.evidence_asof ??
backtest.asof_date}`. Provably a no-op in every other state — `evidence_asof` is `_serve(...,
asof_key)` where `asof_key == run.asof_date.isoformat()`, the same value `card["asof_date"]` carries
(`forward_testing.py:1434`) — confirmed live: the `ready` page still renders `≤ 2026-07-22`, no
banner, zero console errors. Screenshots: `reports/qa/goal-ops-hardening-iter-17-evidence/
AUDIT-A1-crossboundary-refreshing-after-fix.png` and `…/AUDIT-A1-ready-state-unchanged.png`.

**F2 — OBSERVATION: `formatIsoDate(null)` would render an em-dash inside the banner sentence**
`formatIsoDate` returns the EMPTY placeholder for `null` (`lib/dates.ts:75-80`), so a `refreshing`
response with a null `evidence_asof` would read "evidence as of —, generated …". The backend never
produces that combination (`refreshing` always carries a served key), so this is inert.

### Test Findings

**T1 — GAP: the shipped TC-2 test does not exercise the fixture the spec's TC-2 names**
The spec's TC-2 reads: "given the same fixture as TC-1 … the returned JSON includes
`evidence_asof: "2025-01-10"`" — i.e. the *cross-boundary* value asserted at the endpoint level. The
shipped `test_backtest_route_and_mcp_tool_serve_evidence_asof_identically`
(`tests/test_forward_testing_serving_split.py`) instead uses the warm `endpoint_engine` fixture and
asserts the `ready` value (`evidence_asof == asof`). The DoD's substantive claim ("served identically
by both endpoints") *is* verified, and the endpoint wiring is a one-key passthrough shared with the
ready path, so the defect risk is low — but no test anywhere carries an older `evidence_asof` value
through `backtest()` / `query_backtest()`. Combined with TC-8 being unreachable (P1), the
cross-boundary value's *only* evidence is resolver-level.

**T2 — OBSERVATION: TC-5's SQL assertion is loose, but its outcome assertion is not**
`assert not any(">" in stmt …)` is a substring scan over whole statements — it would false-positive on
an unrelated `>` and would miss a lookahead expressed without `>` (a `BETWEEN`, or Python-side
filtering). The test's real proof is its outcome assertion: a fully complete *future* key
(2025-06-01) is seeded, and `evidence_asof` must still resolve to the older key — if the future rows
were read and admitted, they would win the `max()` tie-break. That part is tight.

### Iteration-level Findings

**P1 — GAP: the load-bearing fallback has no live exercise (TC-8), and DoD bullet 4 is not met for it**
Independently re-verified read-only against the committed DB: `MAX(daily_prices.date)` =
`MAX(scanner_runs.asof_date)` = `2026-07-22`, so no ingest can advance `asof_key` without fabricating
price data. The operator's substitute (`?as_of=2026-07-17`) provably healed through the historical
create-once carve-out rather than exercising B1. The browser lane's UT-03 *did* capture the banner
live with `evidence as of 2026-07-22` — but that is the SAME-key `refreshing` sub-case (a gap-date
backfill bumps the global stamp without advancing the identity), so it proves TC-7's banner wiring,
not B1's boundary crossing. B1 therefore rests on 5 unit tests plus (new, from this audit) a
client-side render of the cross-boundary payload. The DoD wording offers an explicit
document-and-defer escape only for TC-9, not for TC-8; the gap is honestly recorded in
`reports/perf-budgets.md`, `status.json` and both handoffs. Evaluator's call.

**P2 — GAP: TC-10's fresh, directly-comparable measurement was not produced; that DoD bullet is not met**
The reasoning (no code in this diff touches the write pattern the iter-16 baseline measured) is sound
and matches the spec's own NOTES clause about not forcing a fix that isn't there — but the DoD bullet
asks for a recorded measurement, and `reports/perf-budgets.md` carries a PENDING placeholder instead.
The root-cause investigation itself is honest work: thermal and single-long-transaction causes are
ruled out with direct evidence, and the blocking limitation is verifiable — I re-ran the claim myself,
`logs/backend.log` has **0** lines matching `^\d{4}-\d{2}-\d{2}` and **0** matching `^\[`, so no
request can be aligned to a wall-clock second. The two surviving mechanisms are genuinely
indistinguishable with current telemetry.

**P3 — OBSERVATION (stale blockers — both now resolved, verified this pass): AG-10 and the browser-QA
FAIL**
(a) `status.json` still lists the uncapped `:18255` throwaway backend as needing operator action. It no
longer applies: the listener on `:18255` is now pid 1245537 (`Max address space 6442450944`, affinity
`0-3,8-11`, `MALLOC_ARENA_MAX=2`, `TRENDORA_CONFIG=/tmp/trendora-tc9-config.yaml`), and the main
backend pid 1414921 carries the same posture. The operator's own AG-10 lapse and its correction are
recorded in `runs/goal-ops-hardening-iter-17/operator-tc9-ag10-correction.md`; no launch script was
modified this iteration (`git status` shows `scripts/` untouched), so there is no code-level AG-10
regression — it was a process-launch lapse, disclosed and corrected.
(b) The merged browser-QA verdict is FAIL on UT-01, attributed to two `next dev` servers sharing one
`.next` directory (`NEXT_PUBLIC_API_URL` is compile-time-inlined). I did not take that on trust:
`grep -rlo 'localhost:18255' apps/frontend/.next` now returns nothing, the app chunks reference
`localhost:8255`, only one trendora `next-server` is running (the other is a different project on
:3301), and `/`, `/backtest`, `/data` all return 200 — plus my own headless load of `/backtest`
rendered the full page with zero console errors. The FAIL does not reproduce and none of the implicated
files (`readiness-provider.tsx`, `health-badge.tsx`, `preflight-banner.tsx`, `app/data/page.tsx`) are in
this iteration's changed set. Environmental, corrected.
(c) The QA report (02:22) predates the browser lane (03:47) and states "Browser test result: PASS";
read it as superseded by `reports/phase-goal-ops-hardening-iter-17-ui-test-results.md`.

---

## 3. Domain Assessment

The core domain logic is sound and the read/compute separation this arc has been building is preserved.

**Correctness of the fallback.** The search is two-staged exactly as specified: a cheap single-identity
completeness read first (unchanged from iter-16, TC-18 still green), and only on total absence a
strictly-older widened search. Grouping by the `(asof_key, dataset_version)` PAIR rather than by
version alone is the right call and the docstring's reasoning is correct — the version stamp is a
global fingerprint, so two different dates can share one stamp and version-only grouping could blend
horizons across dates. The tie-break (`max(complete_by_key)` on ISO strings, then newest `created_at`
within that key) yields the closest older date and never a mixed payload; TC-4 asserts exactly that
with two genuinely different cohorts so a leak would change the numbers, not just the label.

**No-lookahead (AG-5).** The filter is `ForwardAggregateCache.asof_key < asof_key` — a real SQL
`<`, on the *resolved* run date, never `<=` or `>=`. Serving an older as-of's aggregate does not
introduce lookahead (its own window is narrower, not wider). TC-5's future-dated complete key would
win the tie-break if it were ever admitted, and it is not.

**Zero-compute-on-request (J-08).** The resolver still has no compute branch; the latest view calls it
exactly once and nothing else. The B5 re-ordering is the only structural change to the request path
and it is gated on `!= "ready"` — not on `== "not_yet_computed"`, which would have been the natural
mistake and would have short-circuited a cold historical date into serving an unrelated older date's
evidence. The developer identified that trap explicitly and wrote the regression guard for it
(`test_historical_asof_still_computes_once_even_when_older_fallback_evidence_exists`); I traced all
four historical-branch states (own-ready / own-stale-version / own-empty-with-older-complete /
own-empty-with-nothing) and each lands correctly.

**Honesty of the contract.** `not_yet_computed` is now correctly reserved for "no `asof_key` at or
before the request has ever had a complete version", and its live proof is the strongest evidence this
iteration produced: on a disposable DB with `forward_aggregate_cache` at 0 rows, four consecutive
`/api/backtest` requests left the table at 0 rows (re-confirmed read-only against the file itself, so
it holds independently of which process served it). The one place the honesty was incomplete was the
UI copy under the banner (F1), now fixed. `evidence_asof`'s Data Contract registration is present in
`blueprint.md` (lines 207-218 and the appended Notes cell at line 291), tagged `[TARGET, iter-17
building]` for the evaluator to clear.

**Where the evidence is thinner than the artifacts imply.** Every claim about the cross-boundary path
is unit-level or (now) client-render-level. The spec's own lesson for this iteration was "make sure the
live test exercises the identity-advancing shape, not only the convenient one" — that lesson could not
be honored on this data, and the iteration says so plainly rather than substituting a gap date and
calling it a pass. That honesty is the right behavior; it just leaves the DoD bullet open.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/frontend/app/backtest/page.tsx:258-261` | `EvidenceAggregateSection` is now labeled with the served evidence's own as-of (`backtest.evidence_asof ?? backtest.asof_date`) instead of the page's requested as-of, so its three window sentences and its `n_runs` count stay true when the iter-17 fallback crosses an as-of boundary. Comment added recording why. No other file touched. |

**Verification of fix #1 (all re-run after the fix was in place):**
- `cd apps/frontend && npx tsc --noEmit -p tsconfig.json` → **0 errors** (exit 0).
- Live cross-boundary render (Playwright, client-side rewrite of only the `/api/backtest` response —
  no service, backend or DB touched): banner `evidence as of 2026-07-21`; section header
  `Forward-tested evidence (expanding window ≤ 2026-07-21)`; body `every snapshot dated on or before
  2026-07-21`; summary `Snapshots contributing (≤ 2026-07-21): 1802`; `console_errors: []`.
  Screenshot: `reports/qa/goal-ops-hardening-iter-17-evidence/AUDIT-A1-crossboundary-refreshing-after-fix.png`.
- Live `ready`-state regression re-check (unmodified response): header `≤ 2026-07-22`, summary
  `≤ 2026-07-22`, refreshing banner count `0`, `console_errors: []` — identical to pre-fix behavior.
  Screenshot: `…/AUDIT-A1-ready-state-unchanged.png`.
- Pre-fix control captured by temporarily stashing the file: in the same simulated state the section
  rendered `≤ 2026-07-22` (from `asof_date`) — the contradiction is demonstrated, not asserted. Stash
  popped; `git diff --stat` on the file confirms only the iteration's changes plus this one.
- Backend untouched by this audit; I re-ran the iteration's own suite anyway to confirm nothing drifted:
  `taskset -c 0-3,8-11 … pytest tests/test_forward_testing_serving_split.py -q` → **15 passed** (2.17 s).
- `docs/handoffs/goal-ops-hardening-iter-17-frontend.md` gained an auditor addendum recording this change.

Not fixed (deliberately, per severity policy): B1, B2, B3, T1, T2, P1, P2 — GAP/OBSERVATION level.

---

## 5. Recommended Next Step

Proceed to the goal-evaluator with the two open DoD bullets stated plainly rather than smoothed over:

1. **TC-8 is unmet and unmeetable on this data.** The evaluator should decide whether resolver-level
   unit tests plus the audit's client-side render are a sufficient evidence floor for B1, or whether
   J-07/J-08 stay `partial` until a real as-of advance occurs (which needs new price data — an
   owner-owned data-cycle action, not an agent-fixable one).
2. **TC-10 is unmet by decision, not by accident.** The reasoning is sound; if the evaluator wants the
   bullet closed rather than carried, the one-pass operator protocol is already written verbatim in
   the dev handoff. The higher-value follow-up is the instrumentation the investigation asks for (a
   response-timing log line), without which the next pass will repeat the same correlation-only
   analysis.

Two carry-forward items for a future iteration, both cheap and neither blocking: project the metadata
columns in the widened fallback query before reading payloads (B1), and add one endpoint-level test
that carries an *older* `evidence_asof` through `backtest()` / `query_backtest()` (T1). Nothing found
in this audit requires reopening the compute-vs-serve split, `compute_forward_aggregates`, or the
cutover pruning logic.
