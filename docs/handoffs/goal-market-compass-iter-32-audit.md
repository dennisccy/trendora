# goal-market-compass-iter-32 Audit Report

**Date:** 2026-09-01
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal — an honest, durably-evidenced re-measurement of J-09's standing-warm VmPeak — is
genuinely achieved: the raw capture survives on disk, every figure in the dev handoff and in
`perf-budgets.md` Addendum 43 re-derives exactly from that capture, no config/product code moved,
and the honest miss (3,038,684 kB vs the ≤ 2,621,440 kB target) is recorded without widening the
target. Two IMPORTANT defects were found and fixed during this audit: the deterministic replay
lane's results file — the artifact TC-7 requires by name, cited as evidence by the dev handoff, the
review report AND the QA report — **did not exist anywhere on disk**, and the handoff's claim that
"the only live `/api/compass` calls this iteration made were the 6 authorized" was scoped to the
wrong backend instance. The audit re-ran the replay lane (10/10 PASS, rc=0) and corrected the
handoff. Everything else verified clean, including AG-12 (manifest census unchanged, re-derived
directly from the canonical DB) and AG-10 (zero diff in `config.yaml`, `scripts/`, host-guard env).

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): TC-7's replay-results artifact was never written; three reports cite a
file that did not exist**

`run_verify` writes its results file **only** when `--results` is passed
(`scripts/automation/lib/demo_runner.py:2080-2085` — `def _write(...)` is a no-op when
`opts.results` is falsy). The developer's invocation (quoted in the handoff's "Tests Run", ending
in `...`) omitted it. Consequence at audit time:

- `find /home/dennis-chan -name '*market-compass-iter-32-regression*'` → **no hit**;
  `git log --all -- reports/phase-goal-market-compass-iter-32-regression-replay-results.md` → empty;
  `git worktree list` → single worktree. The file simply never existed.
- The dev handoff (item 8, "Results: `reports/phase-goal-market-compass-iter-32-regression-replay-results.md`"),
  the review report (`summary:` "the replay results file shows 10/10 journeys PASS including
  J-02/J-03's first-ever execution") and the QA report (artifact table: "✓ exists | 10/10 journeys
  PASS") all cite it as verified evidence.

This is the DoD item this iteration was specifically chartered to make real (the fourth recurrence
of "a golden rewritten after replay is not coverage"). It mattered more than usual because the
replay lane was the iteration's **only** journey coverage: browser-QA ran but recorded 0/11 with
every row SKIPPED (frontend and backend both unreachable at its dispatch —
`reports/phase-goal-market-compass-iter-32-ui-test-results.md`), the demo lane was SKIPPED
(`...-demo-results.md`), and ux-regression was shed by the SPEED-15 wall-clock trim
(`...-ux-regression.md`).

**Fix applied.** The audit started backend and frontend through the project launch scripts
(`bash scripts/start-backend.sh` / `scripts/start-frontend.sh`, HOST-GUARD blocks intact, no script
edited), waited for `readiness: ready`, and re-ran the identical lane with `--results` set. Result:
`rc=0`, `[demo_runner] verify: 10 journey(s), 0 failed (verdict: PASS)`, 29.4 s wall clock. The
required file now exists with a real per-journey PASS row, and fresh screenshots are under
`reports/qa/goal-market-compass-iter-32-evidence/audit-rerun/` (the developer's originals were NOT
overwritten). `journey-scripts/J-02.json` and `J-03.json` were not edited (mtimes still
`03:35:14.921` / `03:35:18.462`, i.e. unchanged since iter-31's rewrite).

The developer's original run is corroborated rather than taken on faith: its screenshots are
byte-size-identical to the re-run's (e.g. `J-01-verify.png` 103297 = 103297), and the two backend
instances served an identical per-`as_of` `/api/compass` request pattern in `logs/backend.log`
(10 bare, 7×`2025-04-15`, 1×`1996-02-01`, 1×`2026-07-23`, 1×`2026-03-30`, 1×`2026-08-03`,
2×`2026-08-12`, 1×`2026-08-11` in both). The run happened; only the record of it was missing.

**B2 — IMPORTANT (fixed): the handoff's "exactly 6 compass calls this iteration" claim is scoped to
the wrong backend instance**

Dev handoff item 9 states "the only live `/api/compass` calls this iteration made were the 6
authorized before/after byte-identity pairs at the 3 pre-authorized as-of values (confirmed via
`logs/backend.log`'s compass-endpoint histogram: exactly 6 hits)". That histogram is counted from
the launch banner `=== start-backend.sh: launching at 2026-09-01T03:19:17Z ===` forward, and is
correct for that instance (I re-derived it: 940 request lines, **all HTTP 200**, 0 `QueuePool`
lines, `/api/compass` ×6 — bare, `2025-04-15`, `1996-02-01`, twice each). But the replay lane ran
**earlier**, against the instance launched at `2026-09-01T03:14:26Z`, which served **24 compass
GETs across 8 distinct as-of forms**, four of them (`2026-03-30`, `2026-07-23`, `2026-08-03`,
`2026-08-11`) outside the spec's authorized 3-value set. All returned 200.

This is the same failure shape iter-25's Addendum 41 was burned for (a true-but-wrongly-scoped
"no contention was present" claim carried by six evaluators), so it is corrected rather than left.
The safety conclusion it supports is **independently true** and was re-verified from the canonical
DB, not from the handoff: `next_session_manifests` = **28 rows / 18 distinct `as_of` / max id 28**,
max `created_at` `2026-09-01 00:12:07` (predating this iteration's 03:03Z start), and every as-of
the goldens navigate is already among the 18 stored values. `GET /api/compass`
(`apps/backend/app/api/compass.py:58-89`) contains no `session.add` and no `commit` — the mint path
is `POST /compass/regenerate` (`:90`), which nothing this iteration called. AG-12 holds.

**Fix applied:** an attributed "Auditor correction" section appended to
`docs/handoffs/goal-market-compass-iter-32-dev.md` (original text left unedited above it) recording
both B1 and B2 so the evaluator does not carry the two claims forward.

**B3 — GAP: Addendum 43 reports VmPeak only; the same CSV shows the standing-warm resident
footprint is 725,856 kB, not ~3.04 GB**

`runs/goal-market-compass-iter-32/j09-vmpeak-samples.csv` also captures `VmSize_kB` and `VmRSS_kB`.
At the plateau (last sample, `t+396.34s`, `readiness: ready`): **VmSize 1,298,796 kB, VmRSS
725,856 kB**; max VmRSS over the whole window was 2,417,068 kB, reached during boot. VmPeak is a
monotonic high-water mark of virtual address space set during the pool/prefill warm-up
(`readiness` first reads `ready` at `t+25.97s`, VmPeak plateaus at `t+15.94s` — i.e. *before*
readiness), so "the standing-warm floor is a real, stable ~2.97-3.06 GB" describes a boot-transient
peak, not what the process holds while serving.

This is **not** a metric error: `docs/goal.md:549-587` binds J-09's acceptance to
"measured backend VmPeak at standing warm ≤ 2.5 GB" and itself notes "the pool's own connection
warm-up IS the peak", and `server.memory_cap_mb` is a `ulimit -v` (virtual) cap, so VmPeak is the
figure that governs the AG-10 ceiling. Every table cell in Addendum 43 is correctly labelled
"VmPeak". Left as a GAP rather than fixed (fixing would mean editing the developer's addendum for
context the spec never required), but the owner making the now-fired J-09 acceptance decision
should see both numbers: the ceiling-relevant peak is 3,038,684 kB and the serving-time resident is
725,856 kB.

**B4 — GAP: the spec contradicts itself on authorized `as_of` values**

`docs/phases/goal-market-compass-iter-32.md` OUT OF SCOPE forbids "Any live `GET`/`POST
/api/compass*` call outside the exact as-of set `{no param (2026-08-12), "2025-04-15",
"1996-02-01"}`", while TC-7/TC-8 mandate replaying ten goldens whose pages navigate
`/?asof=2026-03-30`, `2026-07-23`, `2026-08-03`, `2026-08-11` and `/stocks?asof=2026-08-12`. The
two clauses cannot both hold. The developer satisfied the DoD clause and breached the scope clause
(B2); harm is nil (all those dates are already manifested; the read path cannot mint). The audit's
own re-run necessarily repeated the same pattern and discloses it. For the decomposer: next spec
should authorize the replay lane's own as-of set explicitly.

**B5 — OBSERVATION: health-endpoint captures were taken but excluded from the TC-5 claim**

`runs/goal-market-compass-iter-32/byte-identity/` holds 18 files, not 12: three `health-*`
before/after pairs in addition to the six compass/dashboard pairs. I ran `cmp` over all nine pairs:
the six compass/dashboard pairs are byte-identical (TC-5 holds, verified independently), and the
three health pairs differ **only** in the `stale_for_s` float (e.g. `0.243…` → `0.446…`), a liveness
timestamp, no Data Contract value. The handoff's TC-5 claim names only compass and dashboard and is
accurate as written; the reviewer disclosed the health delta. Noted only because the file count in
the handoff ("12 raw response captures") understates what is on disk.

**B6 — OBSERVATION: replica burst never exercises `/api/data/availability`**

`_POOL_PRESSURE_ENDPOINTS` has 6 entries against `_POOL_PRESSURE_WORKERS=5` under `worker_id % 6`
assignment, so index 5 is never hit. Inherited from the canonical methodology in
`apps/backend/tests/test_start_backend_script.py`, disclosed by the developer in Known Issues and in
Addendum 43, and correctly left alone — fixing it would break comparability with Addenda 40/41.

### Frontend Findings

None. `Frontend Present: no` is correct: `git diff HEAD --stat` shows the only tracked change this
iteration is `reports/perf-budgets.md` (+144/−0) plus goal-session bookkeeping
(`telemetry.jsonl`, `trace/`). Nothing under `apps/frontend/**` or `apps/backend/app/**` moved, so
no displayed value could move — and the byte-identity spot-check (B5) proves none did.

### Test Findings

**T1 — IMPORTANT (gap, not fixable retroactively): two gates certified an artifact that did not
exist**

The review report claims independent re-verification ("the replay results file shows 10/10 journeys
PASS"), and the QA report's artifact table marks it "✓ exists". Neither could have opened that file
— it was never written (B1). The claim happened to be true, which is exactly what makes it
dangerous: the pipeline's evidence floor
(`.claude/judgment-rubrics.md` §5: "No regressions" requires a replay-verify lane green, §6: a claim
with no citation is `unknown`, not `done`) was satisfied by assertion, not by reading. This is a
process finding for the reviewer/QA lanes, not a product defect; it is recorded here because it is
the mechanism by which B1 reached the auditor undetected.

**T2 — OBSERVATION (verified good): the goldens assert real displayed values, not page loads**

I read `J-02.json` and `J-03.json` (the two executing for the first time since their iter-31
rewrite). Their expects are tight, exact-string assertions on rendered numbers —
`"vs 2026-08-11 (1 day ago)"`, click `"Suppressed moves (36)"` then expect `"0.26 < 5.00"`,
`"Market regime is Risk-on (73.2/100); market phase is Expansion with calm conditions (severity
25.9/100)."`, expect `"73.18"` behind "Show cited facts", plus the earliest-session and
retrospective-stamp strings. `run_verify` treats every `expect` as a hard assertion and returns 5
if any journey fails (`demo_runner.py:2053-2069`). This is genuine AG-3 coverage; the J-03 frontier
assertion also matches the served payload exactly
(`byte-identity/compass-frontier-before.json` → `narrative.sentences[0].text`, version 7,
`mode: at_ingest`).

---

## 3. Domain Assessment

The measurement itself is sound and, unusually for this session, fully reproducible from artifacts:

- **VmPeak (TC-2/TC-3):** re-derived from the CSV — 80 samples, single pid `1724495`, window
  `2026-09-01T03:19:41.786735+00:00 → 03:26:17.728910+00:00`, max `VmPeak_kB` = **3,038,684**,
  first `ready` at `t+25.97s`. Every derived figure in Addendum 43 checks out arithmetically:
  2,967.5 MB (3,038,684/1024 = 2,967.46); +417,244 kB / +15.9 % over the 2,621,440 kB target;
  −400,416 kB / −11.6 % vs iter-4; −26,088 kB / −0.85 % vs iter-25.
- **Concurrent load (TC-4):** `concurrent64-burst-results.jsonl` = 320 records, **all status 200**;
  `replica-burst-results.jsonl` = 482 records, all 200. Server side, the measurement instance's log
  segment shows 940 request lines, all 200, and **zero `QueuePool` lines**. `boot-timeline.txt`
  timestamps line up with the CSV window.
- **Byte identity (TC-5):** verified myself with `cmp` (B5) — 6/6 pairs identical.
- **Append-only budget report (TC-6):** `git diff --stat HEAD -- reports/perf-budgets.md` =
  144 insertions, **0 deletions**; Addendum 43 begins at line 12485, below Addendum 42 (12415);
  40/41/42 byte-unchanged.
- **Config / AG-10 (TC-1):** `git diff -- config.yaml` empty; `cache_size: -65536` (`config.yaml:109`),
  `pool_size: 24` / `max_overflow: 44` (`:126-127`), `limit_concurrency: 64` (`:1374`),
  `memory_cap_mb: 8192` (`:1377`), `malloc_arena_max: 2` (`:1378`) all as declared;
  `git diff HEAD -- scripts/` empty with both HOST-GUARD markers present in
  `start-backend.sh`/`start-frontend.sh`; `project-extensions/host-guard/host-guard.env` untouched.
- **Targeted tests:** re-ran `.venv/bin/python -m pytest tests/test_db.py -q -k pragma` →
  **2 passed, 18 deselected in 0.26s**. Full suite correctly not run.
- **Depth:** `runs/goal-session-market-compass/iter-32/depth-dispatched` = `full`. The spec's
  ninth-demotion worry did not materialise — but note that "full" here delivered review + QA +
  audit only: browser-QA produced zero executed rows (services down), demo and ux-regression were
  skipped. The evaluator should read "full dispatched, partially covered", not "full verified".

The honest-miss handling is the strongest part of the iteration: the target was not widened, no cap
value moved, the contamination (a `tensteps` goal-mode session dispatching throughout the window)
was disclosed proactively in both the handoff and Addendum 43 rather than discovered afterwards,
and the conclusion — that a clean re-measurement lands within 0.85 % of the contaminated iter-25
figure, so the gap will not close by re-measuring again — follows from the evidence.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/phase-goal-market-compass-iter-32-regression-replay-results.md` (new) + `reports/qa/goal-market-compass-iter-32-evidence/audit-rerun/*.png` (new) | Re-ran the deterministic replay lane with `--results` set, producing the TC-7 artifact that was never written. Verification: `python3 scripts/automation/lib/demo_runner.py --mode verify --base-url http://localhost:3255 --backend-health-url http://localhost:8255/api/health --scripts-dir runs/goal-session-market-compass/journey-scripts --journeys J-01,…,J-11 --results … --evidence-dir …/audit-rerun` → `rc=0`, `verify: 10 journey(s), 0 failed (verdict: PASS)`; 10 fresh screenshots written; `next_session_manifests` census identical before and after the run (`(28, 18, 28, '2026-09-01 00:12:07.835199')`). No golden script edited (J-02/J-03 mtimes unchanged). |
| 2 | Important | `docs/handoffs/goal-market-compass-iter-32-dev.md` | Appended an attributed "Auditor correction" section (original text unedited) correcting (a) the citation of a results file that did not exist and (b) item 9's compass-call scope claim. Verification: re-derived the two log segments — instance `03:14:26Z` served 24 compass GETs across 8 as-of forms, instance `03:19:17Z` served exactly 6; DB census unchanged and `GET /api/compass` proven write-free. |

Post-fix state check: `git diff HEAD --stat` still shows `reports/perf-budgets.md` as the only
tracked product/report change (+144/−0); the audit added only untracked files plus the handoff
append. The backend and frontend the audit started were stopped afterwards, leaving the host as
found (both ports return `000`).

---

## 5. Recommended Next Step

Proceed — but hand J-09 to the owner, do not spend another iteration re-measuring. The clean figure
is **3,038,684 kB VmPeak (2,967.5 MB), a 15.9 % miss against the 2.5 GB bar**, with the raw capture
durable at `runs/goal-market-compass-iter-32/j09-vmpeak-samples.csv`. J-09's "stop for owner review"
clause has genuinely fired: the owner's choice is to accept ~2.97-3.06 GB VmPeak as the
standing-warm number (it sits at 63.8 % margin under the `memory_cap_mb` 8192 ceiling, and the
serving-time resident is 725,856 kB — see B3), or to scope the `_BarCache.prefill` re-bound already
parked in `docs/goal.md` Constraints (b)/(c).

Two carries for the next iteration's spec:
1. Bind the replay lane's invocation to `--results <path>` (B1) — the recurring evidence defect in
   this session is now four rounds old and has changed shape from "golden rewritten after replay"
   to "replay with no surviving record". A cheap deterministic guard (the lane's exit path
   asserting the results file exists and is non-empty) would end the family.
2. Fix the spec's own as-of contradiction (B4) by authorizing the goldens' as-of set alongside the
   byte-identity set.

No product code should change for either.
