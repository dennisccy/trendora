# Iteration 16 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The precompute-before-serve redesign (J-08) is real and structurally sound: `GET /api/backtest` and the MCP
`query_backtest` tool are now pure readers that *cannot* reach `compute_forward_aggregates`, and the
178.74s blocking cold recompute that STALLED iter-15 is gone (worst read this iteration: 12.655s, a
stored-row read under contention). I recomputed the operator's 68-row live poll CSV myself and it confirms
the state machine end-to-end. But three clauses of J-08 remain open, so it lands `partial` and cannot yet
free J-06/J-07: (1) **audit B1** — the last-good fallback is scoped to a single `asof_key`, so the *common
single-latest-date* ingest serves `not_yet_computed` (empty evidence) rather than the labeled last-good
J-08 step 2 promises; (2) the committed ≤1.5s `/backtest` budget is breached on 11/68 live polls (max
12.655s); (3) the `not_yet_computed` state has **zero** browser evidence and the only browser evidence of
the refreshing banner shows the *false* copy the audit later fixed and never re-rendered. No journey
regressed, no anti-goal was violated, coherence is PASS — and the remaining work is concrete and
agent-owned, so this continues rather than halts.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors requested range | passing | **passing** (replay) | `reports/phase-goal-ops-hardening-iter-16-ui-test-results.md` UT-J-01 PASS; `reports/qa/goal-ops-hardening-iter-16-evidence/J-01-verify.png` (opened — `/data` Ready, seed 2026-07-22, coverage 1996-01-02→2026-07-22) |
| J-03 No per-run range cap | passing | **passing** (replay) | UT-J-03 PASS; `…/J-03-verify.png` (opened — **byte-identical to J-01-verify.png**, md5 `7d8f6681…`; see Gaps) |
| J-04 Non-blocking boot with visible status | passing | **passing — CARRIED, NOT re-verified** | UT-J-04 **SKIPPED** (kill/restart is a blocked service action this session). Basis: iter-14 live end-to-end pass; `main.py` / `app/api/health.py` / `app/engine/readiness.py` / `app/engine/warmup.py` / `scripts/` absent from the diff (audit §T2 `git status`, spec OUT OF SCOPE binds them); non-disruptive `/api/health` 200 `readiness:"ready"` + `logs/backend.log` boot banners. `last_verified_iter` deliberately left at iter-15. |
| J-05 Aggregates precomputed at ingest | passing | **passing** (replay) | UT-J-05 PASS; `…/J-05-verify.png` (opened — Scanner Run "Immutable snapshot — as of 2025-05-15 · Stored exactly as scanned; never recomputed for today") |
| J-06 Pages load only what they need | partial | **partial** | Cold-MISS residual architecturally closed, but step 2 ("assert every measurement is within budget") fails: `reports/perf-budgets.md:2827-2831` — 11/68 polls >1.5s, max 12.655s. Honest-status clause holds: `…/UT-02-refreshing-fullpage.png` (opened — page fully populated, never frozen/blank) |
| J-07 Heavy aggregates never take the service down | partial | **partial** | Step 1's amended "served from storage per J-08" confirmed for the gap-backfill shape (68/68 HTTP 200; 16/16 refreshing polls served the prior complete generation) but **not** for the as-of-advancing shape (audit B1). Steps 2-4 carried from iter-14/15. `…/UT-04-cutover-ready.png` (opened) |
| **J-08 Backtest serves from storage only** | *(new)* | **partial** | Steps 1/3/4 evidenced; step 2 latency-breached + falsified by B1; step 5 **no browser evidence** (UT-03 SKIPPED); walkthrough unproduced. `…/UT-02-refreshing-fullpage.png`, `…/UT-04-cutover-ready.png`, `runs/goal-ops-hardening-iter-16/tc16-backtest-poll.csv` |

### What I verified myself (not inherited)

- **Recomputed the whole TC-16 CSV** (68 rows): 68/68 HTTP 200; exactly **two** generations ever
  (`14:44:52.882242` ×19, `20:57:22.711666` ×49) — never a third, never mixed; all **16** `refreshing`
  polls served the *prior* generation; the flip to the new generation lands on the same row as the flip to
  `ready`. Latency min 0.121 / median 0.304 / max 12.655s; **11/68 over budget**, all inside the 380s
  ingest window (the 7 polls after it: max 0.171s). This matches `perf-budgets.md` exactly, including its
  own flagged operator-median convention error (0.307 vs the true 0.304).
- **Read the resolver source** (`apps/backend/app/engine/forward_testing.py:1163-1242`) rather than trust
  the audit prose: no branch can reach `compute_forward_aggregates`; the completeness read is
  `.where(ForwardAggregateCache.asof_key == asof_key)` with a 4-column projection (AG-8 bounded, TC-18
  confirmed in source); the `not_yet_computed` return is `{}` / `None`, never partial.
- **Confirmed B1 in source, independent of the auditor's probe**: `backtest.py:70` resolves the default
  view to the latest stored run, and `:1209` scopes the lookup to that one `asof_key` — so a new latest
  date has no rows and `complete` is empty → `not_yet_computed`. `data_manager.py:3172` calls that flow
  "the common single-latest-date backfill" in its own comment.
- **Opened UT-02 and read the banner text on screen**: it is the *pre-fix* copy — "A newer dataset version
  **is still being warmed** … **This updates automatically** once the new version finishes warming."
  Both claims are false (audit F1). The corrected copy **is** in the working tree
  (`apps/frontend/app/backtest/page.tsx:270-276`, verified by me) but has never been rendered.
- **Opened UT-04**: the cutover is a real value change, not just an absent banner — `evidence-summary`
  moves 1800 snapshots / n=743634 → **1801 / n=744166**.

## The two calls the audit routed to me

**1. B1 — must the last-good fallback cross as-of boundaries? RULING: YES.** goal.md J-08 step 2 says the
refresh window serves the last complete version *"labeled with that version's served as-of"* — a label that
is meaningless unless the served as-of can differ from the current one. Step 5 reserves
`not_yet_computed` for *"a store where no warm has ever completed for any version (fresh-install shape)"*,
which B1's flow is not: the store is full of complete versions, just not for the newly-advanced key. So
serving the fresh-install signal there is a misuse of an honest state, and in the *most common* ingest
shape the page shows an empty evidence section plus copy telling the user to "run an ingest" they are
already running (audit F2). This is a reading of the goal text, not a product-direction decision, so I make
it rather than defer it — and the fix (widen the fallback to the most recent prior complete `asof_key`,
label the served as-of) is bounded, agent-owned follow-up work, exactly as the auditor scoped it.
I did **not** treat it as a REGRESSION: no journey moved passing→failing, no anti-goal is implicated (it is
a contained honest-shaped `EmptyState`, not a crash, blank error page, or wrong number), and it was
disclosed by the pipeline's own auditor rather than hidden.

**2. Latency — is 11/68 over budget a pass? RULING: NO, it is a documented DoD miss.** J-06 step 2 requires
"assert every measurement is within budget" and the goal's Success Criteria commit to "page loads stay
within committed never-regress budgets". The owner was offered a budget amendment as iter-15 option (3)
and chose option (2) — the redesign — instead, so ≤1.5s still binds unamended. 7/16 `refreshing` and 4/49
post-warm `ready` polls breach it. This is a *14x improvement* on iter-15's 178.74s and a categorically
smaller problem (stored-row read contention, not a synchronous compute) — but scoring it green would
launder a breach the same way iter-12's human-ratified precedent declined to.

## Anti-goal Check

Worked from `runs/goal-session-ops-hardening/iter-16/scan-report.md` (**CLEAN**) + `iter-diff.md`
(12 files: 4 backend app, 5 backend test, 2 frontend, 1 new untracked test).

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language without ledger backing | OK | No score/edge presented as proven. `evidence_status` is a *serving* state, not a proven-ness claim. UT-02/UT-04 show honest "— n=0 ⚠" and "Figures with n<30 ⚠ are low-sample. Nothing is fabricated." |
| AG-2 return promises / orders | OK | No new such copy; banner text is about dataset versions. "Research-only · decision support · no orders" bar intact in every screenshot. |
| AG-3 displayed numbers correct | OK | Byte-identity asserted vs a fresh compute (`test_forward_testing_serving_split.py:125-156`); `compute_forward_aggregates` untouched (diff's first hunk starts after it). UT-04's summary changed consistently with the new version (1801/744166), i.e. a real re-serve. |
| AG-4 overfit edges | OK | No referee/ledger/claim path touched. |
| AG-5 no-lookahead | OK — strengthened | The fallback serves a strictly *older* complete version; the completeness gate makes a partially-newer mix structurally impossible (`forward_testing.py:1216-1220`), and the 68-row CSV shows only 2 generations, never mixed. |
| AG-6 referee gate on evidence claims | OK | Ops/serving-architecture iteration; no evidence-derived claims introduced (goal.md Loop mechanics). |
| AG-7 hard-coded credentials | OK | scan-report CLEAN on added lines; no config/env/manifest file in the diff list. |
| AG-8 data-scale resilience / no unbounded ORM loads | OK | New completeness read is `asof_key`-filtered + column-projected, bounded to ~2 versions' rows (read by me at `forward_testing.py:1205-1210`). All three states return HTTP 200; `not_yet_computed` renders a contained `EmptyState`, never a blank application-error page. |
| AG-9 offline-deterministic ingest | OK | No provider/network/dependency change (scan-report: no dependency findings); `provider: seed` visible in every screenshot; TC-16 ran against the committed seed. |
| AG-10 host resource ceiling | OK | No launch script, host-guard file, or `main.py` touched. TC-16 launched via `scripts/start-backend.sh`, taskset `0-3,8-11`, sampler live, watchdog armed, in-window peak **83 °C < 95 °C** (I confirmed the `hwmon.csv` cross-read at `perf-budgets.md:2813-2823`). All test runs `taskset -c 0-3,8-11`, BLAS/OMP/NUMEXPR=4. Exactly ONE authorized heavy pass. |

**Result: no anti-goal violation introduced or observed this iteration.** All 8 historical records in
`journey-history.json` remain `resolved: true` (0 unresolved).

**Coherence:** `runs/goal-session-ops-hardening/iter-16/coherence.md` = **COHERENCE-PASS** (one producer,
two consumers, no second cache identity, nav byte-unchanged) → no consolidation mandate.

## Gaps and evidence-quality notes

- **UT-03 (`not_yet_computed`) never rendered** — the only J-08 state with zero browser evidence.
- **The corrected refreshing banner is un-screenshotted** — the audit's own honest limitation; the sole
  browser artifact shows the false wording.
- **`J-01-verify.png` and `J-03-verify.png` are byte-identical** (md5 `7d8f6681…`) and both show only the
  `/data` page-top landing frame, not either journey's acceptance state. The replay lane's PASS rests on
  its scripted DOM `expect`s (legitimate, and the raw
  `reports/phase-goal-ops-hardening-iter-16-regression-replay-results.md` agrees with the merged file with
  no reconciliation footer), but two of three replay screenshots are not independently informative.
  Framework note, not a reason to overturn a deterministic PASS. My J-05 spot-check *was* meaningful and
  corroborated its status; neither spot-check contradicted the record, so I did not widen.
- **T1** — the `loaded_engine` fixture pre-warm (`conftest.py:77-81`) is still unrun; the audit narrowed
  the real blast radius from "~29 files" to **2** (`test_api_backtest.py`, `test_mcp_window.py`) and traced
  both bite paths as benign. Residual risk low but `unknown`.
- **B3** — `evidence_generated_at` is serialized naive (`"2026-07-23T20:57:22.711666"`, no `Z`/offset)
  despite the data contract calling it "ISO 8601 UTC". Frontend is accidentally safe (it slices, not
  parses); an MCP client doing `fromisoformat`/`new Date()` gets a local-interpreted value. New field,
  worth fixing while it is young.
- **B2** — `refreshing` is sticky: any `ScannerRun` insert (including a user merely navigating to an
  unsnapshotted as-of date) bumps the global stamp and leaves the latest view labeled `refreshing`
  indefinitely with no self-heal. Values stay correct and honestly labeled.
- Carried, unrelated: `test_db.py::test_create_all_produces_expected_tables` (pre-existing).

## Next-Step Recommendation

**FULL depth** (the fix changes the same serving contract *and* adds a user-visible as-of label). No new
features — close J-08, which is the sole item between J-06/J-07 and `passing`.

1. **AGENT, item 1 — fix B1.** Widen `resolved_forward_aggregate_evidence` so that when the requested
   `asof_key` has no complete version but an earlier one does, it serves that earlier complete version as
   `refreshing`, **labeled with that version's served as-of** (J-08 step 2's own wording), instead of
   falling to `not_yet_computed`. Reserve `not_yet_computed` for the true fresh-install shape (step 5).
   Surface the served as-of in the banner, and re-word the empty state so it never tells a user mid-ingest
   to "run an ingest" (audit F2). Add the as-of-advancing case to
   `test_forward_testing_serving_split.py` — it currently has **zero** unit or live coverage.
2. **AGENT, item 2 — browser evidence for the two unrendered states.** Re-capture the *corrected*
   refreshing banner (services are up), and render `not_yet_computed` on a **disposable copy** of
   `trendora.db` (never the working DB) to close UT-03 / J-08 step 5.
3. **AGENT, item 3 — the latency residual.** Root-cause the 11/68 breaches (max 12.655s) — all inside the
   ingest window, on a *stored-row read*, so this is writer/reader contention, not compute. Check SQLite
   journal mode and the ingest's transaction span; the auditor's B5 (the historical branch reads and
   deserializes every payload twice) is a cheap adjacent win. Record either way in `reports/perf-budgets.md`.
4. **AGENT, non-blocking:** B3 timezone designator on the new `evidence_generated_at` field; B2 sticky
   `refreshing` (decide self-heal vs. document); F3 duplicated empty-state sentence.
5. **OPERATOR (not agent-tractable this session):** a live J-04 replay (kill/restart) — J-04 is carried,
   not re-verified, and **must** be freshly verified before any GOAL_ACHIEVED; and one
   `loaded_engine`-dependent test (`test_api_backtest.py::test_backtest_evidence_by_horizon_shape_and_keys`)
   to close T1. A fresh `demo.sh ops-hardening --session-live` run would newly exercise J-08's own `[NEW]`
   walkthrough steps (the iter-14 walkthrough predates J-08 and cannot cover them).
6. **OWNER, optional:** if the ≤1.5s `/backtest` budget is not meant to govern reads taken *during* a heavy
   ingest, that is a conscious logged amendment in `reports/perf-budgets.md` — never a silent loosening.
   Until then it binds as written and J-06 stays `partial`.

## Halt Justification (if halting)

Not halting. Explicitly rejected:
- **REGRESSION** — no journey moved `passing`/`already_passing` → `failing`, and no critical anti-goal is
  unresolved (all 8 records `resolved: true`; every category checked above came back clean). B1 is a
  real behavioural trade-off this iteration introduced (pre-iter-16 that flow blocked and eventually
  served real evidence; now it serves an empty state fast) but it implicates no anti-goal, causes no
  crash/outage, leaves the page interactive, and was surfaced by the pipeline's own auditor.
- **STALLED** — decisively not iter-15's situation. There, every unblock path was owner-owned; here the
  auditor itself scopes B1's fix as "a follow-up iteration", and items 1-4 above are all agent-owned. Only
  item 5 is human-owned, and it is not the critical path.
- **GOAL_ACHIEVED** — J-06, J-07, J-08 are `partial`; J-04 carries no fresh evidence.
- **ESCALATE** — already full depth; review PASS_WITH_NOTES, QA PASS, browser-qa PASS, audit
  PASS_WITH_GAPS, closure CLOSURE-PASS, coherence COHERENCE-PASS. No fail-open, no journey failing twice.
