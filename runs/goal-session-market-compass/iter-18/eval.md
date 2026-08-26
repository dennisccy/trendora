# Iteration 18 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

## Summary

The one job the owner allowed was done, and it worked. Trendora's real database now carries the small
safety record that marks the eleven damaged days, and I checked myself — by opening the database in
read-only mode and running the app's own start-up check — that all eleven days are now refused and that
five ordinary days are still allowed. Nothing else in the database moved. But the protection covers
start-up only. I found, and no other lane reported, that anyone can still make the app write one of those
days by asking a page for that date (a web address ending `?as_of=2026-08-12`). The plan stops here by the
owner's own written instruction, and every way forward is a decision only the owner can make.

## Pipeline Health

Coherence audit (`runs/goal-session-market-compass/iter-18/coherence.md`): **COHERENCE-PASS** — no
blocking violation, no Data Contract row touched, no frontend file changed (I re-confirmed the second
and third independently). No veto on this verdict. Deterministic diff scan: **CLEAN**. Review:
**PASS_WITH_NOTES** (one MINOR, one NOTE). QA: **PASS** (UI Evolution Audit correctly SKIPPED — backend
only, `Frontend Present: no`). Audit: **PASS_WITH_GAPS** (B1 and T1 IMPORTANT, both fixed inside the
audit; B2/B3/B4/E1 gaps; B5/T2/T3/E2/E3 observations). No fail-open signal: no lane failed and was
passed over. Depth dispatched was `full`, matching the spec — the silent full-to-lean demotion seen in
iterations 2, 6 and 8 did not recur, for the tenth iteration running.

## Journey Results This Iteration

Browser testing and the automatic replay lane were **forbidden by contract** this iteration (maintenance
isolation). `reports/phase-goal-market-compass-iter-18-ui-test-results.md` records `Browser QA Verdict:
SKIPPED` with a Reason naming maintenance isolation, and
`runs/goal-session-market-compass/iter-18/maintenance-isolation-refusals` logs the engine refusing the
browser-QA dispatch at `2026-08-26T00:20:05Z`. So every journey keeps its prior recorded status; none was
re-verified, and none could be promoted.

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels are honest | passing | passing (carried, not re-verified) | spot-check: `reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png` — GRMN shows a real stored sector label; consistent |
| J-02 What changed since last session | partial | partial (carried, not re-verified) | maintenance isolation — no lane ran |
| J-03 Plain-English summary | partial | partial (carried, not re-verified) | maintenance isolation — no lane ran |
| J-04 Candidates explain why / why-not | passing | passing (carried, not re-verified) | spot-check: `reports/qa/goal-market-compass-iter-4-evidence/J-04-verify.png` — page renders correctly but shows the Dashboard summary, not a candidate's why/why-not; weak citation, does not contradict |
| J-05 Close freezes one manifest | partial | partial (carried, not re-verified) | maintenance isolation — no lane ran |
| J-06 A frozen manifest never changes | partial | partial (carried, not re-verified) | maintenance isolation — no lane ran |
| J-07 Today page ten-second read | failing | failing (carried, not re-verified) | Loop-mechanics gate keeps this lane shut until J-11 Stage G |
| J-08 Market page moves over intact | failing | failing (carried, not re-verified) | Loop-mechanics gate keeps this lane shut until J-11 Stage G |
| J-09 Backend fits the host | partial | partial (carried, not re-verified) | maintenance isolation — no lane ran |
| J-10 Bounded recovery of two days | passing | passing (carried, not re-verified) | spot-check, evaluator's own read-only query: 585 `daily_prices` rows on each of 2026-08-11 and 2026-08-12; AVB's corrected volumes 554757 / 3706010 intact |
| J-11 Incident-bounded regeneration | partial | **partial — advanced** (target) | `runs/goal-market-compass-iter-18/j11-iter18-live-preboot-guard-verification.json`; `…/j11-iter18-full-table-sweep-diff.json`; evaluator's own read-only re-derivation (below) |

### J-11 — what I verified myself, not from a report

- The live database (`apps/backend/data/trendora.db`, opened `mode=ro`) holds a `maintenance_boundaries`
  table whose 7 columns match `app.models.MaintenanceBoundary.__table__` exactly in name, type,
  nullability and primary key, plus the `ix_maintenance_boundaries_name` unique index.
- Exactly **1** row: `j11-incident-recovery`, `active=1`, whose date list parses to exactly the eleven
  values in `app.engine.j11_maintenance.INCIDENT_DATES`.
- Running the **real production entry point**
  `j11_preboot_guard.evaluate_boundary_for_date_fail_closed` against that live file:
  all eleven dates return `blocked=True, ambiguous=False`; five control dates (2026-05-11, 2026-07-09,
  2026-07-23, 2026-08-06, 2026-08-13) return `blocked=False`. The check can answer "no", so it is a real
  gate and not a constant.
- Both newly guarded call sites read directly: `apps/backend/app/engine/warmup.py:361` and
  `apps/backend/app/engine/forward_testing.py:551` both call that same shared wrapper before `run_scan`.
- Nothing else moved: table count 24 -> 25; file size byte-identical at 8,365,871,104 bytes
  (`freelist_count` 24,417 explains the reuse); `daily_prices` 3,310,374; `scanner_runs` 3,117;
  `next_session_manifests` 24; `max(daily_prices.date)` 2026-08-12; **zero** `scanner_runs` on every one
  of the eleven dates — which is also the plainest proof the forbidden rebuild was not quietly started.
- Tests re-run by me: `test_j11_preboot_guard.py`, `test_j11_preboot_guard_cli_scripts.py`,
  `test_j11_maintenance.py` -> **82 passed**, matching the auditor's post-fix figure.
- `spec_hash` re-stamped to `3fff95f1…` (was `8cf4ace6…`): the owner's ruling changed J-11's goal text.
  No `journeys-changed.md` fired because J-11 is `partial`, not `passing`; I re-verified against the
  current text anyway. All ten other journeys' hashes are byte-identical to the recorded ones.

### Open exposure found by this evaluator and by no other lane

The quarantine covers **start-up paths only**. `apps/backend/app/engine/scanner.py:348` (`resolve_run`),
reached from every read endpoint's `?as_of=` parameter via `app/engine/snapshot_serving.py:42`, still
calls `run_scan` with **no boundary check** — so a single request such as `GET /api/compass?as_of=2026-08-12`
would permanently create a canonical result on a quarantined day. This is the same class as the auditor's
B4 (`data_manager.py:3754`) but a far wider surface: the auditor's call-graph enumeration named
`data_manager` as the only user/API-triggered writer, while `grep -rn "run_scan(" app/` returns six call
sites. It is **not** a defect of this iteration — the owner's requirement 7 scoped the work to
boot-initiated paths — but it is the live exposure now, because the owner's own boot condition has been
met. Ordinary page visits are safe: with the eleven days empty, the app's "latest" falls back to
2026-07-23 (my own query), which is not quarantined.

### Second-order consequence, confirmed by reading the code (not by booting)

`ensure_latest_snapshot` returns `None` for a blocked latest date (`warmup.py:113-120`) and
`main.py:113` starts the background warm-up only `if latest is not None`. So while this boundary is armed,
a boot runs **no** background warm-up at all and the health badge reads "still starting up" rather than
"ready". Safe and expected — but the two call sites guarded this iteration are therefore unreachable on
boot today, and anyone reopening browser testing must not read the different badge, or the 2026-07-23
"latest", as a regression.

## Anti-goal Check

Worked from `runs/goal-session-market-compass/iter-18/scan-report.md` (**CLEAN**) plus
`iter-diff.md`, and re-checked by my own greps, code reading and read-only database queries.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials (AG-7) | OK | No credential-shaped literal in any new or changed file; grep over the 4 engine files and all 4 `run_j11_*` scripts returned nothing. Scan report CLEAN. |
| Paid / external SaaS | OK | No dependency manifest changed anywhere in the 67-path changed-file set; scan report reports no dependency findings. |
| License changes | OK | No LICENSE or license field appears in the changed-file set; scan report CLEAN. |
| Fabricated / substituted data | OK | The only live writes are one empty table and one control row, both verified. No research value was written; `daily_prices`, `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`, `forward_returns`, `next_session_manifests` and `data_provider_runs` all hold their prior counts on my own query. |
| AG-1 / AG-4 / AG-6 (proven-language, overfit, referee) | OK | No score, claim or narrative surface exists in this diff; no Evidence Claim is touched. |
| AG-8 (data-shape / scale resilience) | OK | The new sweep uses SQL aggregates (`COUNT/MIN/MAX/SUM(rowid)`) per table, never a full ORM hydration; the only `.all()` is over `sqlite_master` (25 rows). The new guard call sites reuse the already bounded, column-projected, `LIMIT`-ed statement. |
| AG-9 (offline-deterministic ingest) | OK | Zero network imports or URLs in the new and changed modules; no provider fetch anywhere in the evidence trail. |
| AG-10 (host resource ceiling) | OK | No launch script or `host-guard.env` touched; the full test suite was never run and no two pytest processes ran concurrently. |
| AG-11 (no new composite number) | OK | No candidate-facing number added; no scoring file in the changed set. |
| AG-12 (manifest immutability) | OK | `next_session_manifests` still holds 24 rows on my own read-only query; no `NextSessionManifest` reference in any changed module. |
| AG-13 / AG-14 / AG-15 / AG-16 | OK | No readiness/regime vocabulary, no Tapeology import, no selection rule or cohort touched; none of the implicated files appears in the diff. |
| AG-17 (repair never rewrites provenance) | OK (judgment recorded) | Riders 6b/6c corrected two iteration-17 artifacts. Neither is iter-5 drill evidence; 6c is purely additive, and 6b's replacement text names itself as an iter-18 correction and quotes the wording it repudiates — so nothing is silently superseded. Reasoning logged in `assumptions.md`. |
| AG-18 (authorized migration preserves everything) | OK | The create used `MaintenanceBoundary.__table__.create(..., checkfirst=True)`, never `create_db_and_tables()` or `metadata.create_all()`; exactly one table appeared and every pre-existing table is unchanged. |

**Ledger: 7 total, 0 unresolved. No new violation, none critical.**

## Next-Step Recommendation

**One safety decision first, then the big decision.**

**The safety decision.** The owner's rule was "do not start the app until the safety catch is on". The
catch is now on, so someone may reasonably think it is safe to start Trendora again. It is safer than it
was, but not yet safe: asking any page for one of the eleven damaged dates still writes that day
permanently, and nothing stops it. Pick one — (a) keep the "do not start the app" rule in force for one
more iteration, until the page-request path is protected too; or (b) authorize a small change that makes
those page requests refuse instead of writing, which also means deciding what the page should show
instead. I recommend (a): it costs nothing, while (b) edits the read pages, and those cannot be tested
while browser testing is switched off — and their untouched state is the only reason J-01 "Sector labels
are honest", J-04 "Candidates explain why and why-not" and J-10 "Bounded recovery of the two deleted
days" are still counted as passing.

**The big decision, unchanged and still the owner's alone.** Whether to authorize the rebuild of the
eleven damaged days (J-11 "Incident-bounded regeneration", Stage D). The owner's own written rule ends
this step with "stop for owner review even if everything succeeded", and the rebuild needs a separate,
fresh, written instruction. Until that happens nothing else in the plan can move, because the goal file
keeps every normal lane shut until the repair's final stage passes — which is why J-07 "The Today page
answers the ten-second read" and J-08 "Market page moves over intact" have not been worked on since
iteration 1.

**Four small jobs**, none of which can change either decision: decide deliberately what the health badge
should say while a quarantine is on (today it counts a skipped day as done; the obvious fix would leave it
saying "still starting up" forever, so this is a product choice, not a bug fix); consider protecting the
Data Manager write path the same way; annotate — rather than rewrite — iteration 17's quality report,
which still lists the wrong eleven dates; and note that the "nothing else changed" evidence is a
row-identity check, not a true content hash, so it could not detect an in-place edit that kept the same
size (I corroborated it with my own row counts, file size and spot values and found nothing wrong).
**One mechanical item:** this iteration's eleven changed backend files, two of them brand new, are still
uncommitted at the time of scoring — confirm they reach version control.

**What should happen next:** the owner reads the safety decision above, says whether to keep the app
switched off for now, and then decides whether to authorize the rebuild of the eleven damaged days; the
engine cannot do anything useful until one of those two answers arrives.

## Halt Justification

Halting as **STALLED** because every way past the current blocker is an action only the owner can take.

1. **The owner's own instruction ends here.** `docs/goal.md:1738-1743` says: *"Even if all three are
   established, STOP. Actual Stage D execution requires a separate later explicit owner authorization."*
   All three were established this iteration. Continuing would let the engine plan the one step the owner
   reserved.
2. **Everything else is shut until a later stage.** `docs/goal.md:2087-2090` says no developer, reviewer,
   QA, browser-QA, evaluator, coherence, research or proposer lane may run against the damaged database
   before J-11 Stage G passes. Stage G is downstream of the rebuild, so no other journey can be worked on.
3. **The unblock options, all owner-owned:** (a) authorize the rebuild of the eleven days and `--resume`;
   (b) authorize the small change that makes page requests for a quarantined day refuse instead of write,
   accepting that it edits the read pages and cannot be verified while browser testing is off;
   (c) reword or re-scope the plan in `docs/goal.md`; (d) leave the app switched off and pause.
4. **Why not CONTINUE.** The three engineering items that exist — the health-badge counter, the Data
   Manager write path, and the page-request write path I found — are all decisions about how the product
   should behave, and the last one edits the very files whose untouched state is the sole basis for three
   journeys still counting as passing. None is safe to do blind while browser testing is forbidden.
5. **Why not REGRESSION.** Nothing that worked stopped working, no journey was tested so none could fail,
   no stored research value moved, and the anti-goal ledger gained no entry.
6. **Halting is the safer direction.** A stopped engine starts no backend and issues no page request, so
   the one remaining exposure cannot fire while the session is halted.
