# goal-ops-hardening-iter-2 Audit Report

**Date:** 2026-07-20
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-05 (coverage + aggregates served from a persisted `coverage_snapshot` table at ingest, never on the
request path) and J-04's remaining acceptance (enforced `ulimit -v`/`MALLOC_ARENA_MAX` + a persistent
`logs/backend.log`) are genuinely implemented and correct for every surface the Must-have journeys
exercise. I verified this by reading the actual source (not the handoffs), running a subset of the new
tests first-hand (4/4 passed), and cross-checking the live browser + perf-budget evidence. Cold `/data`
serves coverage from storage in 0.029–0.086 s (vs a ~9.4 s pre-fix baseline) with zero request-path
whole-table loads on the default path; the launch script's cap/env/logfile are confirmed live via
`/proc/<pid>/{limits,environ}`. The AG-3 as-of-switcher CRITICAL that failed review pass 1 is properly
fixed and re-verified.

Two genuine gaps keep this from a clean PASS, both documented rather than force-fixed: (1) a
**`fetch`-that-lands-bars silently blanks the default `/data` coverage panel to false all-zeros** — an
introduced AG-3-class regression on a path the spec explicitly scoped out, self-healing, and not surgically
fixable without breaking this iteration's own TC-6/TC-9 contracts (B1); and (2) TC-11/TC-12 (health
responsiveness + memory ceiling **during a heavy job**) were never measured (T1). Neither compromises
J-05/J-04's own acceptance, but B1 sits on the AG-3 dimension and should be closed before the goal is
declared achieved.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap; unsure CRITICAL): a `fetch` that lands new bars silently blanks the default `/data` coverage panel to false all-zeros**

`CoverageSnapshot` rows are keyed on `(asof_key, dataset_version)`, where `dataset_version` =
`_membership_dataset_version` — a live fingerprint that embeds bar count / run count / latest date (the
UT-07 capture shows `r772-rc759-b2026-07-17-bc3299789-h200`). A `fetch` that lands even one bar changes
that stamp. `fetch`/`expand` are correctly excluded from the finalize hook — the gate at
`data_manager.py:3759` (`if final_status in ("ok","partial") and (prog.kind in _BACKFILL_KINDS or
prog.kind in _REBUILD_KINDS)`) — so no new `coverage_snapshot` row is written for the new stamp. The
default `/data` visit (`data_overview` passes `as_of=None`, `api/data.py:115-127`) then finds no matching
row and, because the self-heal is deliberately gated `if as_of is not None` (`data_manager.py:1101`, to
preserve the TC-6/TC-9 cold-boot no-whole-table guarantee), falls through to the all-zero sentinel
(`_coverage_not_yet_computed_payload`, `data_manager.py:900`). Result: Universe/Symbols/Trading-days/
Snapshot-dates all render `0` for a fully-ingested DB until the next restart or backfill/rebuild.

- **Evidence:** reproduced and root-caused *live* by the browser-qa-agent during UT-07
  (`reports/phase-goal-ops-hardening-iter-2-ui-test-results.md` §"Additional Finding"; confirmed via direct
  backend `curl`, not a frontend artifact) and independently rated by the ux-regression-reviewer
  (`...-ux-regression.md` §"Potential Regressions").
- **Why it matters:** a real regression *relative to pre-iteration behavior* — before iter-2 `/data`
  always live-computed and was therefore always correct (just slow). It lands on the default landing view
  (the most common surface), shows numbers that do not match the engine (the AG-3 "displayed numbers must
  be correct" spirit), and its only recovery paths (restart, or an unrelated backfill/rebuild) are
  undiscoverable from the UI.
- **Why I did NOT fix it (and why it is a gap, not a FAIL):**
  - The spec **explicitly** scopes it out — "Any change to `fetch`/`expand` kinds' finalize behavior" is
    OUT OF SCOPE, and "no Must-have journey exercises a fetch that lands new bars this cycle." No TC-1..21
    exercises fetch-then-coverage.
  - It is **not surgically fixable within the iteration's own contracts.** Extending the self-heal to the
    `as_of=None` default path re-introduces a request-path whole-table `_compute_coverage_uncached` in the
    cold-boot window — precisely the OOM/hang J-05/TC-6/TC-9 exist to remove (it would trade an IMPORTANT
    gap for a CRITICAL one). Routing `fetch`/`expand` through an ingest-time refresh is the correct fix
    (ingest-time is AG-8-safe) but is exactly the fetch/expand finalize change the spec deferred, and needs
    new "skip when stamp unchanged" gating + tests + a cross-suite re-run.
  - It self-heals (no data loss; stored rows stay byte-identical — a key-space *freshness* miss, not a
    byte-identity, unbounded-load, or network violation, so the DoD's specifically-enumerated checks
    "AG-3 byte-identity / AG-8 no-unbounded-serving-load / AG-9 no-network" all still hold), and both QA
    and the ux-regression-reviewer classified it as a non-blocking follow-up.
  - I was genuinely unsure between IMPORTANT and CRITICAL; per the rubric I name the higher and flag it as
    the top follow-up. It is IMPORTANT for *this* iteration (out-of-scope, self-healing, contract-locked)
    but CRITICAL-class on the product's AG-3 dimension.

**B2 — GAP: stale-stamp `coverage_snapshot` rows accumulate and are never reclaimed**

`_upsert_coverage_snapshot` (`data_manager.py:947-963`) prunes stale rows only for the *same* `asof_key`
being written (`asof_key == k AND dataset_version != dv`). When the global `dataset_version` changes, the
per-date historical rows written under the previous stamp (via `_persist_per_date_coverage_snapshots` or
prior self-heals) are for *other* `asof_key`s and are never pruned — a later explicit-as-of read inserts a
fresh `(asof_key, new_dv)` row and leaves the old one orphaned forever. Correctness is unaffected (reads
always hit the current-stamp row or self-heal), so this is a slow storage/cleanliness leak, not a defect.
A "delete rows whose `dataset_version != current`" sweep belongs with the B1 follow-up. Not worth a
surgical fix this iteration.

**B3 — OBSERVATION: `ulimit -v $((MEMORY_CAP_MB * 1024))` degrades to `ulimit -v 0` on an empty config read**

`incredible_auto_dev/scripts/start-backend.sh:48` derives the cap from `MEMORY_CAP_MB` (the venv-Python
`get_config()` read at `:34-40`). Were that read ever to yield empty, bash arithmetic treats it as `0` →
`ulimit -v 0`, which prevents uvicorn from starting. This is a hard, immediately-visible failure (not
silent), the read is deterministic in this repo, and it never fired live (Item K measured the correct
`6442450944` bytes). Noted for robustness only.

### Frontend Findings

**F1 — OBSERVATION (no defect): the additive `Refreshed:` line is minimal, gated, and reused**

`apps/frontend/app/data/page.tsx` extends the shared `BackfillBreakdown` with one optional
`aggregatesRefreshed?: string[] | null` prop rendering `Refreshed: <prettified, comma-joined>` only when
non-null/non-empty, threaded verbatim through all three existing call sites (`LastRunSummary`,
`JobProgressPanel`, `RunHistoryPanel`); the suppression guard correctly became
`!hasBreakdown && !hasAggregates`; `data-testid="aggregates-refreshed"`; same muted `text-xs text-text-faint`
treatment; `tsc --noEmit` clean. `lib/api.ts` types match the persisted-nullable vs live-optional
convention. No new page/panel/nav/control. Verified live by browser QA UT-02 (live + post-reload
byte-identical) and UT-08 (no underscores, identical style). No scope creep.

### Test Findings

**T1 — GAP: TC-11/TC-12 (health responsiveness + memory ceiling DURING a heavy backfill/rebuild) never measured**

Only the *boot-time* peak was measured (`reports/perf-budgets.md` Item J: VmHWM ~1.78 GB, ~71% margin) and
*normal-operation* health (QA: 5 polls ≤0.15 s). The heavy-job case is unmeasured, and it matters more than
the dev's reasoning acknowledges:
  - The `ulimit -v` cap is now genuinely **enforced** (Item K). Pre-iteration there was no cap, so a large
    transient could not OOM-kill the process; post-iteration it can. An unmeasured heavy-job peak above
    6144 MB would be a *new* crash mode.
  - The "same `_compute_coverage_uncached`, only moved" reasoning does not cover the genuinely **new**
    per-date loop `_persist_per_date_coverage_snapshots` (`data_manager.py:2977`). For a full `rebuild`
    (clears then recreates every snapshot), `prog.new_snapshot_dates` is *every* date (~758 on the live
    DB), so the finalize hook computes coverage for ~757 dates plus market-phase for all of them — work
    scaling with date count. Memory is bounded by the single shared `prefilled_bar_cache`, so a peak
    blow-out is unlikely, but the wall-time addition to a rebuild's finalize is real and unmeasured.
  Mitigating: the finalize hook runs strictly *after* `_do_backfill`'s heavy date-loop and its cache is
  freed (`_release_process_memory`), so peaks are sequential not additive, and it is on the job thread not
  the request path (health is served on the event loop). Low regression risk — but this is one of J-05's
  four DoD acceptance steps and remains a genuine hole. Reviewer (MINOR) and QA both deferred it as a
  QA-measurement task, so GAP, not blocker.

**T2 — OBSERVATION (no defect): new unit/integration tests are tight, and I re-ran a critical subset**

I ran a 4-test critical subset first-hand (TMPDIR set): `test_api_data.py` coverage-from-storage /
honest-sentinel / empty-db + `test_data_manager.py` run-detail-gating / self-heal / per-date-historical —
**4 passed in 0.52 s**. Assertions are tight, not loose: exact set-equality on refreshed categories
(`test_data_manager.py:1052`), full-dict byte-identity for AG-3 (`:1077`, `:1360`, `:1383`), exact
`compute_market_phase` count = 1 then 0 on re-read (`:1099/:1104`), the interrupted-crash gate serving
`null` despite a computed breakdown (`:1197`), fetch-kind `null` despite a fabricated field (`:1203`), and
the AG-3 regression tests discriminate REAL coverage (`symbol_count == 1`) from the false sentinel (`0`).
Zero-prefill contracts are enforced by monkeypatching the prefill path to raise (`test_api_data.py:117-121`).
`test_start_backend_script.py` is a genuine real-process test (spawns the real script on an isolated port,
reads `/proc/<pid>/{limits,environ}`, SIGKILLs, checks the log slice) — not a stub — correctly handling the
zombie-reap and append-log-offset edges the dev honestly disclosed. The J-05 browser walkthrough with a
real backfill (TC-20 pixel-level render of a populated line) was covered live by browser QA UT-02 (PASS).

---

## 3. Domain Assessment

The core domain logic is correct and honest on every path the phase set out to build.

- **Coverage-from-storage read path (J-05 core):** verified `data_overview` passes `resolved_asof = None`
  on the default visit (`api/data.py:115`), so `coverage_from_storage`'s self-heal branch (gated on
  `as_of is not None`, `data_manager.py:1101`) can never fire on the common cold path — TC-6/TC-9
  (zero-prefill, honest sentinel) hold structurally, confirmed by Item J's live 0.029–0.054 s and by the
  monkeypatched unit tests.
- **Finalize-hook honesty:** `_refresh_ingest_aggregates` (`data_manager.py:2998`) reports only categories
  it actually refreshed. The "membership_timeline" claim is not fabricated — `_compute_coverage_body`
  genuinely calls `membership_timeline_cached` (`data_manager.py:889`), so it is warmed as a real side
  effect of the coverage compute; `latest_snapshot`/`market_phase` are appended only when
  `new_snapshot_dates` is non-empty.
- **Interrupted-crash gating (AG-3, TC-13):** the persisted `aggregates_refreshed` is gated on
  `_breakdown_computed and prog.aggregates_refreshed` (`data_manager.py:3375`), the SAME gate `calendar_days`
  uses. I confirmed a `rebuild` reaches `calendar_days > 0` via `_do_backfill` (`:2779`, dispatched at
  `:3698`), so there is no rebuild hole where the hook runs but the field is hidden. Crash-safety is
  structural (the sweep never rewrites the `message` JSON) — no new sweep code, correctly.
- **Ordering fix:** the finalize hook runs *before* `prog.status = final_status` (`data_manager.py:3759-3766`)
  and in its own `Session(eng)` opened after the job session closed — so a live poller never observes
  `status: ok` with an empty `aggregates_refreshed`. The observability window the developer found and
  honestly self-reported is genuinely closed.
- **AG-3 as-of-switcher fix (review pass-1 CRITICAL):** the two layers (per-date persist at ingest +
  explicit-as_of read-path self-heal) are real and correct; browser QA UT-05 cross-checked two historical
  dates against direct API calls (byte-exact), and the two regression tests assert `symbol_count == 1`
  (REAL) vs the `0` sentinel. Properly resolved.
- **AG-8 / AG-9:** the default path reads a stored row or a zero-DB-query sentinel (`read_pool()` file read
  only); the one request-path compute is the bounded, one-time-per-date explicit-historical self-heal,
  never on the default. `test_finalize_hook_makes_no_network_call` asserts zero `socket.connect`.

The one domain wrinkle is B1: the derived-cache key space is not maintained on the `fetch` path, so the
"served from storage" guarantee silently degrades to the honest-empty sentinel after a count-changing
fetch — correct-by-construction for the journeys the spec covers, wrong only on the out-of-scope fetch path.

**Independent test re-run (this audit):** 4 crux tests (coverage-from-storage / honest-sentinel / empty-db /
run-detail-gating / self-heal / per-date-historical) — **4 passed, 47 deselected, 0.52 s**, TMPDIR set.

---

## 4. Fixes Applied During This Audit

None. The one IMPORTANT finding (B1) has no surgical fix that does not either re-introduce the CRITICAL
cold-boot whole-table-compute regression (TC-6/TC-9) or drift into the spec's explicitly-excluded
`fetch`/`expand` finalize behavior (new gating + tests + cross-suite re-verification) — applying either
would trade one finding for a worse one, so B1 is documented for a scoped follow-up rather than
force-fixed. T1 is a QA measurement task, not a code defect. All other findings are GAP/OBSERVATION
(document-only per policy). I verified the implementation rather than rewriting it.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied (rationale above). |

---

## 5. Recommended Next Step

**Proceed** — close this iteration as PASS_WITH_GAPS. J-05 and J-04's remaining acceptance are met with
live evidence, J-01/J-03 regression journeys pass, and the review-pass-1 AG-3 CRITICAL is fixed. The system
is strictly stronger: coverage served from storage ~170–330× faster, the memory cap actually enforced, a
persistent logfile, and honest `aggregates_refreshed` transparency.

Open a dedicated **follow-up iteration** (corroborated by QA's and the ux-regression-reviewer's own
suggested scope — this is not a new demand):

1. **(Top priority — AG-3 dimension)** Close B1. Refresh `coverage_snapshot` for the current stamp at the
   end of *any* ingest kind that changed the bars manifest (ingest-time, so AG-8-safe), gated to skip when
   `_membership_dataset_version` is unchanged (so a zero-work offline fetch pays nothing); or make the
   boot-time warm-up safety net run on a light cadence. Fold in the B2 stale-stamp prune. Do **not** fix B1
   by extending the `as_of=None` self-heal — that path must stay on the zero-query sentinel to preserve the
   cold-boot no-whole-table guarantee this iteration delivered.
2. **(Measurement)** Run one real heavy `rebuild`/multi-day backfill and record TC-11 (`/api/health` ≤1 s
   throughout) and TC-12 (`VmPeak` under the now-enforced 6144 MB cap) into perf-budgets Item J, paying
   attention to the new per-date coverage loop's cost on a full rebuild (~757 per-date computes).

Neither should reopen this iteration; both are genuine, user-relevant follow-ups within the same headline
feature.
