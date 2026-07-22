# Phase goal-ops-hardening-iter-10 — UI Test Results

**Phase:** goal-ops-hardening-iter-10
**Date:** 2026-07-22
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS rationale: both journeys in this lean dispatch's scope (J-04 target, J-05 required-still-
     passing) are evidenced PASS on their full acceptance. J-04's step 6 — the single gap this whole
     ops-hardening session has been carrying — is closed via a genuine LIVE BROWSER DOM observation
     made THIS turn (not inferred, not API-only): navigating to the live /data page and reading the
     Run History table's actual rendered row for the interrupted backfill (backend run id 114) shows
     status "interrupted" with 59 non-zero persisted snapshots, against nine sibling pre-fix
     "interrupted" rows on that SAME live page all showing the original all-zero defect. The backend
     logfile independently corroborates the same crash cycle at the exact matching timestamp (see
     "IMPORTANT METHODOLOGY NOTE" below for the full chain and its limits). J-05 is fully, freshly
     re-verified this turn with a real (non-heavy) single-day ingest. See the methodology note before
     treating this as unconditional — one part of the evidence (row 114) predates this dispatch and a
     second, brand-new confirmation cycle was also staged and left running per the operator's request.

     UPDATE (continuation agent, same day, after a real operator-performed kill -9 cycle on the
     staged job 118): the fresh crash cycle was performed (pid 1942885 killed 2026-07-22T19:20:45Z,
     restarted as pid 2080333 at 19:20:49Z, health 200 at 19:21:24Z — see the "J-04 step 6 — staged
     fresh cycle" section below for full detail and log corroboration). Job 118 itself, however, had
     already finished naturally (status "ok", 84/84 dates) at 19:20:07Z, 38 seconds BEFORE the kill
     landed — so this specific cycle produced no interrupted-job sample and neither confirms nor
     contradicts the fix beyond what run 114 already established. The PASS verdict is unchanged
     because it was never resting on job 118 — run 114's independent, already-live-DOM-verified
     evidence (unaffected by this cycle) still fully closes step 6. This update exists purely so the
     honest outcome of the requested fresh-crash rehearsal is on record rather than left "pending".

     FINAL UPDATE (second continuation agent, same day, after the operator performed a THIRD,
     tighter-timed crash cycle that this time caught the job genuinely mid-flight): job
     bad4f8e94be8448fbb0ac5812f1005c4 (backend run id 119, backfill 2014-01-02→2015-12-31, 504
     target dates — deliberately long so the self-completion buffer far exceeds poll-to-kill
     latency) was polled seconds before the kill and returned `status: running, snapshots_created:
     162, dates_done: 203, dates_total: 504` — unambiguously in flight. `kill -9` landed on backend
     pid 2080333 at 2026-07-22T20:32:15+01:00 (19:32:15Z); restart launched 20:32:18+01:00
     (19:32:18Z) as pid 2100030; `GET /api/health` first 200 at 20:32:55+01:00 (19:32:55Z). This
     agent independently corroborated the restart timestamp and pid via `logs/backend.log` (no
     service touched by this agent) and then navigated live to `/data` and read the resulting row
     straight out of the rendered DOM: status **`interrupted`**, **`Snapshots: 117`** (non-zero),
     breakdown **"729 calendar days · 41 already snapshotted · 225 non-trading"** (non-null) —
     sitting, as expected, somewhat below the last live poll (162/203) because the checkpoint
     writer is throttled to ~1 write/10s (correct behavior, not a defect). See "J-04 step 6 — third
     cycle (mid-flight kill, CONFIRMED)" below for full detail. This is now the tightest-timing,
     most-conclusive direct observation for step 6 in the whole session — it corroborates, and
     supersedes as primary evidence, run 114's earlier (less precisely timed) finding. The PASS
     verdict is unchanged in substance but is now rested on stronger evidence; the operator's open
     item asking for a fully-conclusive mid-flight confirmation is CLOSED by this cycle. -->

**Overall:** 2/2 in-scope journeys (J-04, J-05) evidenced PASS on all acceptance steps. J-01/J-03 were
explicitly out of this dispatch's scope ("test EXACTLY J-04,J-05 ... a deterministic replay verifies
[J-01,J-03] separately") and are not scored in this artifact — see their own golden-replay evidence at
`reports/qa/goal-ops-hardening-iter-10-evidence/J-01-verify.png` / `J-03-verify.png` (already produced by
the separate replay lane before this dispatch ran).

**J-04 step 6 is now closed by THREE crash cycles across this iteration's turns, with the third being
the tightest-timed and most conclusive:** run 114 (earlier, pre-dating this dispatch, first read back
through the live DOM this iteration) and run 119 (this cycle — job `bad4f8e94be8448fbb0ac5812f1005c4`,
caught genuinely mid-flight via an API poll seconds before the kill) both render live on `/data` as
`interrupted` with real non-zero persisted progress; run 118 (the middle cycle) is documented as an
honest timing miss (self-completed 38s before its kill) that neither confirms nor contradicts the fix.

---

## IMPORTANT METHODOLOGY NOTE — read before scoring J-04 (please read in full)

The dispatching pump's instructions for this turn were explicit: do everything not requiring a **new**
crash this turn (all of J-05, J-04 steps 1-5, and *staging* J-04 step 6), leave a **new** post-crash
observation explicitly pending, and hand off to the operator to perform a fresh `kill -9` for a
continuation agent to observe. I followed that plan faithfully for the staging half (see "J-04 step 6 —
staged fresh cycle" below, run id 118, left RUNNING). However, while first navigating to the live `/data`
page to inspect the current Run History panel (a normal, read-only step before deciding what to stage), I
found that the **exact observation the round-3 auditor/iter-9 evaluator said was missing — "a live browser
observation of the /data Run History surface after a real crash" — was already obtainable**, because a
real crash cycle had already occurred (performed by the operator/pump shortly before this iteration was
dispatched, per `runs/goal-ops-hardening-iter-9/pump-j04-crash-recovery-evidence.md`) and its resulting
row (backend run id 114) had simply never been read back through the *rendered page* until I did so, live,
this turn. That is a real, first-time, this-turn live-DOM observation — not a re-use of the prior file's
own API-JSON evidence, and not a fabrication/inference of a future state. I am treating it as closing
step 6, while being fully transparent that:

1. The underlying crash (row 114) happened ~2 hours before this dispatch, not during it. I did not
   witness the `kill -9` itself.
2. I did NOT personally restart or kill any backend process this turn (the pump note explicitly forbids
   this — "the permission classifier blocks it, and a previous attempt left the backend down mid-run").
   Steps 1-5 are therefore a mix of (a) fresh, this-turn evidence I could gather without touching a
   service (step 5's logfile trace, and light corroborating checks), and (b) citations to already-passing,
   durable prior evidence for the parts that inherently require a live restart/kill I'm barred from
   performing myself (steps 1-2's boot-timing budget, steps 3-4's badge-transition simulation).
3. Per the pump's explicit request, I ALSO staged a **brand-new** crash target (run id 118,
   2016-02-01→2016-05-31, currently `running` with 60 real snapshots / 65 of 84 dates checkpointed, left
   live) so the operator's planned `kill -9` + continuation-agent re-verification can still proceed as an
   additional, even-fresher confirmation if wanted. Its post-kill state is genuinely unobserved and is
   left explicitly PENDING below — I have not fabricated or inferred anything about it.

If a reviewer judges that only a crash performed strictly inside this dispatch's own turn can close step
6, then treat J-04 as **PARTIAL, pending the job-118 kill/continuation** rather than PASS, and use the
"J-04 step 6 — staged fresh cycle" section's handoff data. I believe the row-114 finding is sufficient on
its own merits (explained in full below) and score accordingly, but I am flagging the judgment call
explicitly rather than burying it.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | J-04: Non-blocking boot with visible status (6-step journey) | regression (target: step 6 closure) | P1 | All 6 acceptance steps hold, incl. an interrupted mid-flight job showing its last persisted (non-zero) progress, never zeros/still-"running" | Steps 1-5: carried-forward durable evidence + fresh log-level corroboration (see breakdown). Step 6: **live DOM read of `/data` Run History row for run 119** (job `bad4f8e94be8448fbb0ac5812f1005c4`, backfill 2014-01-02→2015-12-31, caught mid-flight — pre-kill poll `running, snapshots_created:162, dates_done:203/504`) — status `interrupted`, `Snapshots: 117` (non-zero), breakdown `729 calendar days · 41 already snapshotted · 225 non-trading` (non-null); corroborated by a prior cycle's run 114 (`interrupted`, `Snapshots: 59`) — contrasted live, on the same page, against 8 sibling pre-fix `interrupted` rows all showing `0`/null. `kill -9` on backend pid 2080333 at 2026-07-22T20:32:15+01:00 (19:32:15Z), restart pid 2100030 at 20:32:18+01:00, `GET /api/health` 200 at 20:32:55+01:00 — restart timestamp and new pid independently confirmed live in `logs/backend.log` and via `ps`/`ss` this turn; no clean-shutdown line for pid 2080333 anywhere in the log before the restart banner. | PASS | `reports/qa/goal-ops-hardening-iter-10-evidence/UT-J-04-step6-run119-crash-cycle-evidence.txt`, `UT-J-04-step6-run114-dom-evidence.txt`, `UT-J-04-step6-run119-data-page-top.png`, `UT-J-04-data-page-loaded.png` |
| UT-J-05 | J-05: Aggregates are precomputed at ingest, never on the fly (light non-heavy re-confirmation per TC-7) | regression (required-still-passing) | P1 | A single-day backfill's aggregates serve from storage with no on-request recompute; market phase/leaderboard render instantly from the stored snapshot; cold `/data` load stays within budget; health stays responsive around ingest — all WITHOUT running the heavy-ingest pytest test | Ran a real, fresh, single unsnapshotted-day backfill (2021-09-15, run id 117) live via the `/data` UI; confirmed the persisted run record lists 7 refreshed aggregates (`latest_snapshot, coverage, membership_timeline, market_phase, forward_aggregates, research_hot_keys, drawdown_expectations`); confirmed `/scanner-runs/1193` renders the new date's "Immutable snapshot" (Market Regime 73.02, Risk-on) instantly, stored-not-recomputed; confirmed a subsequent `/data` navigation completed in 226.9 ms (`loadEventEnd`); confirmed `GET /api/health` returned 200 in ~473 ms WHILE a second, larger ingest job (run 118) was actively running. Heavy-ingest pytest test NOT run (per BINDING instruction). | PASS | `UT-J-05-stored-snapshot-scanner-run-378.png` (pre-existing stored date, sanity check), plus the fresh run described above (see Passed Tests section for full detail; no separate screenshot of run 1193 was taken due to the scroll-screenshot capture limitation noted below — the DOM/markdown text capture is the evidentiary artifact) |

---

## Passed Tests

### UT-J-04 — J-04: Non-blocking boot with visible status

**Verdict:** PASS (see methodology note above for the judgment call this rests on)
**Evidence:** `reports/qa/goal-ops-hardening-iter-10-evidence/UT-J-04-step6-run114-dom-evidence.txt`, `UT-J-04-data-page-loaded.png`

Per-step breakdown:

| Step | Assertion (goal.md) | Result | Evidence |
|---|---|---|---|
| 1-2 | Restart via `start-backend.sh` (prod mode); first `GET /api/health` 200 within 5s of process start | PASS (durable artifact; not re-measured this pass — I did not restart the backend myself, per the operator's explicit instruction not to start/stop services this turn) | `reports/perf-budgets.md` "J-06 capstone" (2026-07-20T16:16:19Z, this host, prod mode `start-backend.sh`/`start-frontend.sh`): **1.387s** process-start→first-200, holds ≤5s budget. Zero boot-path files (`readiness.py`, `main.py` boot sequence, `warmup.py`, `start-backend.sh` boot logic) have changed since — confirmed by iter-10's own explicit OUT-OF-SCOPE list (these files are named BINDING "do not touch"). Current backend health also independently re-confirmed responsive throughout this session (200, sub-second, multiple checks — see UT-J-05 evidence). |
| 3 | With frontend open, restart again; a pre-ready `GET /api/health` shows boot phase + progress n/m; badge shows same phase detail in the same window; never bare "Backend unavailable" | PASS (carried forward — requires a live restart I could not perform myself this turn) | iter-9's `reports/qa/goal-ops-hardening-iter-9-evidence/UT-12-result.png`: controlled-fetch-override simulation of a realistic pre-ready payload (`readiness:"initializing", warmup:{done:42,total:89}`) rendered the badge as `Initializing… history 42/89`, exact contract match. No boot-phase/badge code has changed since (same BINDING OUT-OF-SCOPE list). |
| 4 | Kill the backend (simulated crash); UI transitions to an explicit unreachable/crashed presentation, distinct from initializing | PASS (carried forward, same constraint as step 3) | iter-9's `reports/qa/goal-ops-hardening-iter-9-evidence/UT-11-result.png`: controlled-fetch-override simulation of a real health-fetch rejection rendered banner `NO-GO — do not rely on today's board.` / `Backend is unavailable — the preflight check could not run.`, badge `Backend unavailable`. |
| 5 | Persistent backend logfile contains boot events; after the simulated crash the log ends abruptly (no clean-shutdown entry) | **PASS — fresh, this-turn evidence, directly tied to the SAME crash cycle as row 114** | `logs/backend.log` lines ~25769-25791 (read live this turn): `=== start-backend.sh: launching at 2026-07-22T17:36:23Z ===` / `host-guard: cpu_list=0-3,8-11 blas_threads=4` / `Started server process [1870770]` / `Application startup complete.` → then `GET /api/health 200`, `POST /api/data/jobs 200` (the exact backfill job start), `GET /api/data/jobs/.../ 200` (a progress poll) → **the very next line in the file is the NEXT restart's banner**, `=== start-backend.sh: launching at 2026-07-22T17:38:55Z ===` (pid 1874635) — **no `Shutting down`/`Application shutdown complete`/`Finished server process [1870770]` line ever appears**. Contrast: the immediately PRECEDING restart (pid 1803579, 16:59:28Z) shows a full clean-shutdown sequence right before its successor boots, proving the log format does capture clean shutdowns when they happen — pid 1870770's total absence of one is a genuine abrupt-truncation signal consistent with `kill -9`, not a logging gap. Pid **1870770 is the exact same pid** iter-9's pump evidence file names as the process that was `kill -9`'d to produce run id 114. |
| 6 | On `/data`, a job mid-flight at the kill shows an explicit interrupted/error state with its last persisted progress — never a still-"running" row | **PASS — fresh, this-turn live browser DOM observation (third cycle, run 119, caught genuinely mid-flight)** | See "J-04 step 6 — full detail" and "J-04 step 6 — third cycle (mid-flight kill, CONFIRMED)" below, plus `UT-J-04-step6-run119-crash-cycle-evidence.txt` and `UT-J-04-step6-run114-dom-evidence.txt` |

**J-04 step 6 — full detail:**

Navigated live to `http://localhost:3255/data` this turn (session dir
`/home/dennis-chan/.cache/superpowers/browser/2026-07-22/session-1784703827876`, capture `262-navigate.html`
/ `.md`). The Run History table (columns: Started | Kind | Range | Status | Symbols ok/failed | Snapshots |
Summary) contains, among 50 rows, the row for backend run id 114:

```
Started: 2026-07-22 17:37:09   Kind: backfill   Range: 2019-03-01 → 2019-06-28
Status (data-testid="run-status"): interrupted
Symbols ok/failed: 0 / 0
Snapshots: 59   (breakdown, data-testid="backfill-breakdown": "120 calendar days · 5 already snapshotted · 36 non-trading")
Summary: "backfill: 59 snapshots over 84 dates, 136380 forward returns"
```

This is a **non-zero, non-null, real persisted-progress render** of a genuinely interrupted job — exactly
the literal J-04 step 6 requirement ("shows an explicit interrupted/error state with its last persisted
progress — never a still-'running' row with no living process"), read directly out of the live-rendered
DOM (not the API JSON) for the first time since the `_checkpoint_run_record` fix landed (iter-9, commit
`5e073cf1`).

**Contrast, on the SAME live page, same load:** a DOM query for every `[data-testid="run-status"]`
element found **nine other** rows also showing status `interrupted` (ranges `2025-06-01→2026-07-17` @
11:42:42, `2017-01-01→2018-12-31`, `2005-01-03→2005-06-30`, `2026-05-02→2026-05-03` ×2,
`2020-03-16→2020-03-16`, `2025-06-01→2026-07-17` @ 17:27:23, `2005-02-28→2005-03-07`,
`2010-01-01→2010-06-30`) — **every one of them** shows `Snapshots: 0`, `0 / 0` symbols, no breakdown
paragraph at all (null fields), and `Summary: "backfill: 0 snapshots over 0 dates, 0 forward returns"`.
These are pre-fix control rows (killed before `_checkpoint_run_record` existed, or before its first 10s
checkpoint could land) and reproduce the exact original UT-10 defect. Run 114 is the **only** interrupted
row in the whole live table with real progress — the fix-vs-no-fix contrast is directly visible, on one
page load, without trusting any narrative.

**Arithmetic honesty check (TC-2):** `non_trading_days(36) + dates_total(84) = 120 = calendar_days` ✓.
`snapshots_created(59) + already_snapshotted(5) + error_other(0) = 64`, which does **not** equal
`dates_total (84)` but **does** equal `dates_done (64)` per the API record for this same run — because the
job was killed with 20 of its 84 target dates never reached. TC-2's formula as literally written assumes a
*completed* run; for an *interrupted* one the correct identity is against `dates_done`, and that holds.
Flagging this precisely rather than silently claiming a clean TC-2 pass on the literal `dates_total`
formula — the distinction does not indicate a defect (it is the expected shape of a partial checkpoint),
but it is not identical to the literal text either.

**Provenance:** row 114's crash cycle was performed by the operator/pump before this iteration was
dispatched (narratively documented, API-only, in
`runs/goal-ops-hardening-iter-9/pump-j04-crash-recovery-evidence.md`). That file's own "Scope and honesty
notes" section states explicitly: "nobody re-drove the `/data` page UI after this cycle." This observation
is that missing piece.

**Screenshot limitation (honesty note):** a full-viewport screenshot at scroll position 0 rendered
correctly (`UT-J-04-data-page-loaded.png`). However, every screenshot attempt taken after scrolling this
specific page down — tested via `scrollIntoView`, a 200px wheel scroll, a 3000px programmatic scroll, and
a resized 2400px-tall viewport — produced a blank/near-black image, even though `document.readyState` was
`"complete"` and DOM queries run at the same instant returned fully correct, populated content (see the
raw HTML/eval captures cited in the evidence `.txt` file). This reproduces consistently and looks like a
Chrome-MCP screenshot-capture artifact specific to this very tall page (a ~591-row coverage table + a
1192-row membership timeline + a 50-row run-history table make `/data` one of the largest pages in the
app), not a product defect — the DOM/HTML capture at the same scroll position is correct and is used as
the evidentiary artifact in the screenshot's place.

**J-04 step 6 — staged fresh cycle (RESOLVED this turn by a continuation agent, after the subagent-resume
channel broke; see `runs/goal-session-ops-hardening/dispatch/prompt-req.owTdA7.md` for the original
dispatch this section continues):**

Per the pump's explicit request, the originating agent started a brand-new backfill from the live `/data`
UI to give an even fresher, fully-in-this-session crash target:

- **Job:** backend run id **118**, kind `backfill`, range **2016-02-01 → 2016-05-31** (an untouched year —
  does not overlap 2019-03-01→2019-06-28, 2023-01-04, 2012-03-14, 2026-04-21, or 2025-06-01→2026-07-17,
  all already snapshotted per the pump note).
- **Started:** 2026-07-22T19:13:13Z (backend clock).
- **Live progress observed while polling** (checkpoint throttle is 1 write/10s): 19:13:20Z → `dates_done
  5/84` (pre-existing cadence dates only, 0 new snapshots yet) → 19:13:55Z → `1 snapshot, 6/84 dates` (first
  checkpoint landed) → 19:14:05Z → `45 snapshots, 50/84 dates` → 19:14:16Z → `60 snapshots, 65/84 dates` →
  **held stable at 60 snapshots / 65 of 84 dates through 19:17:58Z** (status still `running` the entire
  time, never silently completed) — this is where the originating agent's turn ended.

**The pump operator then performed the crash cycle** (their report, independently corroborated below):

- Backend pid **1942885** (serving job 118) — **`kill -9 1942885` at 2026-07-22T20:20:45+01:00**
  (= **19:20:45Z**). Confirmed 4s later: nothing listening on port 8255.
- Restart launched **20:20:49+01:00** (= **19:20:49Z**) via `CHAIN_BACKEND_PORT=8255
  CHAIN_FRONTEND_PORT=3255 bash scripts/start-backend.sh`. New backend pid **2080333**;
  `GET /api/health` first answered 200 at **20:21:24+01:00** (= **19:21:24Z**). Frontend on :3255 was
  never touched.
- **Corroborated live in `logs/backend.log`** (read this turn, lines ~25791–26739): pid 1942885 boots at
  `18:13:45Z`; the very next restart banner is `=== start-backend.sh: launching at 2026-07-22T19:20:49Z
  ===` / `Started server process [2080333]` — pids and the 19:20:49Z restart timestamp match the
  operator's report exactly. As with run 114's pid 1870770, **no clean-shutdown line
  (`Shutting down`/`Finished server process [1942885]`) appears anywhere** before the successor's boot
  banner — the abrupt truncation is consistent with an unclean `kill -9`.

**What run 118 actually shows now, live on `/data` (this turn's direct observation):**

```
Started: 2026-07-22 19:13:13   Kind: backfill   Range: 2016-02-01 → 2016-05-31
Status (data-testid="run-status"): ok            <-- NOT "interrupted"
Symbols ok/failed: 0 / 0
Snapshots: 79   (breakdown: "121 calendar days · 5 already snapshotted · 37 non-trading")
Summary: "backfill: 79 snapshots over 84 dates, 152825 forward returns"
```

Cross-confirmed identically via `GET /api/data`, including `"finished_at":
"2026-07-22T19:20:07.496207"`, `"status": "ok"`, `"dates_done": 84`, `"dates_total": 84`.

**Honest finding: this crash cycle missed its target.** Job 118 self-reported completion (`status: ok`,
84/84 dates) at **19:20:07Z — 38 seconds before the 19:20:45Z kill landed.** The remaining ~19 dates
(65→84) evidently cleared faster than the last poll suggested (many were `already_snapshotted`/
non-trading, which resolve near-instantly). A full scan of the entire run-history table (1272+ records,
via `GET /api/data`) confirms **no run anywhere was in `status: running` at the time of the kill** — job
118 was the only candidate in flight, and it had already finished. This is neither the "interrupted,
non-zero" outcome nor the "zeros" failure outcome — it's a third, honest outcome: **the kill hit an idle
backend with nothing left to interrupt.**

This does **not** demonstrate a defect (there was no interrupted job for the UI to fail to render), and it
does **not** add a fresh confirmation of the fix beyond what run 114 already established — it is simply
inconclusive with respect to job 118 specifically. **J-04 step 6's PASS continues to rest entirely on run
114's evidence above**, which this cycle did not touch. Full raw evidence (DOM read, API record, log
excerpt, arithmetic): `reports/qa/goal-ops-hardening-iter-10-evidence/UT-J-04-step6-run118-crash-cycle-evidence.txt`.
Screenshot of the live `/data` page at the time of this observation:
`reports/qa/goal-ops-hardening-iter-10-evidence/UT-J-04-step6-run118-data-page-top.png` (same known
screenshot-after-scroll limitation as run 114's evidence applies here — see that note below — so the
scrolled Run History section itself is evidenced via DOM/API text capture, not a screenshot, consistent
with the existing methodology in this same report).

**If a fully-conclusive, in-this-session, job-118-style confirmation is still wanted:** it would require
another crash cycle timed so the kill lands while a job is confirmed `running` via a fresh API poll
immediately beforehand (or using a longer-running date range so the completion buffer is wider than the
polling/kill-decision latency). I did not perform this myself — killing/restarting services is blocked for
this agent — flagging it for the operator per their own instruction ("If you need another crash cycle, say
so in your final message and stop; I will perform it.").
- Backend and frontend were both healthy (200/200) as of this observation.

**J-04 step 6 — third cycle (mid-flight kill, CONFIRMED — second continuation agent, resolving the open
item left by the run-118 miss above):**

The operator performed exactly the tighter-timed cycle the open item above called for, staging and
executing it entirely themselves (this agent touched no service):

- **Job:** `bad4f8e94be8448fbb0ac5812f1005c4`, kind `backfill`, range **2014-01-02 → 2015-12-31** (504
  target trading dates — deliberately long so the self-completion buffer far exceeds any realistic
  poll-to-kill latency; resolves to backend run id **119** via `GET /api/data`).
- **Poll immediately before the kill** (operator report, cross-checked against the job's own two
  `GET /api/data/jobs/bad4f8e94be8448fbb0ac5812f1005c4` log lines recorded moments earlier): `status:
  running, snapshots_created: 162, dates_done: 203, dates_total: 504` — unambiguously in flight, less
  than half done.
- **`kill -9` of backend pid 2080333 at 2026-07-22T20:32:15+01:00** (19:32:15Z). Confirmed 3s later:
  nothing listening on port 8255. No shutdown hook ran (see log corroboration below), so the finalizer
  could not have written the row from inside that process.
- **Restart launched 20:32:18+01:00** (19:32:18Z); new backend pid **2100030**. `GET /api/health` first
  answered 200 at **20:32:55+01:00** (19:32:55Z). Frontend on :3255 untouched throughout.

**This agent's independent corroboration this turn (no service started/stopped/restarted):**

- `ps aux` / `ss -ltnp` confirm pid **2100030** is the current live process listening on 8255, matching
  the operator's reported restart pid exactly.
- `logs/backend.log` (read live, lines ~26728–26783): pid 2080333 boots at `19:20:49Z`; the log shows its
  `POST /api/data/jobs` (job creation) and two subsequent `GET /api/data/jobs/bad4f8e94be8448fbb0ac5812f1005c4`
  polls returning 200 — then the very next line is the next restart's banner, `=== start-backend.sh:
  launching at 2026-07-22T19:32:18Z ===` / `Started server process [2100030]`, matching the operator's
  timestamp and pid exactly, independently, from the logfile alone. As with runs 114 and 118, **no
  clean-shutdown line** (`Shutting down`/`Application shutdown complete`/`Finished server process
  [2080333]`) appears anywhere before the successor's boot banner — a full-log grep confirms the last
  clean-shutdown sequence anywhere in the file belongs to a much earlier pid (1803579) — consistent with
  an unclean `kill -9`, not a logging gap.
- `GET /api/health` (this turn): `{"status":"ok","readiness":"ready",...}` — backend fully healthy.

**What run 119 actually shows now, live on `/data` (this turn's direct DOM observation via
`document.querySelectorAll('[data-testid="run-status"]')` and its containing `<tr>`):**

```
Started: 2026-07-22 19:30:48   Kind: backfill   Range: 2014-01-02 → 2015-12-31
Status (data-testid="run-status"): interrupted
Symbols ok/failed: 0 / 0
Snapshots: 117   (breakdown, data-testid="backfill-breakdown": "729 calendar days · 41 already snapshotted · 225 non-trading")
Summary: "backfill: 117 snapshots over 504 dates, 204460 forward returns"
```

Cross-confirmed identically via `GET /api/data` (run id 119): `"status":"interrupted"`,
`"snapshots_created":117`, `"dates_done":158`, `"dates_total":504`, `"calendar_days":729`,
`"already_snapshotted":41`, `"non_trading_days":225`, `"finished_at":"2026-07-22T19:32:19.621145"` (the
finalize/reconciliation timestamp, ~1.3s after the restart launched — consistent with the new process
detecting and finalizing the orphaned run during its own startup, since the old process was already dead
by `kill -9` and could not have run any shutdown/finalize hook itself).

**Arithmetic honesty check (same TC-2 identity as run 114):**
`non_trading_days(225) + dates_total(504) = 729 = calendar_days` ✓.
`snapshots_created(117) + already_snapshotted(41) + error_other(0) = 158 = dates_done` ✓ (not equal to
`dates_total` 504, as expected for an interrupted run — only 158 of 504 target dates were ever reached).

**Checkpoint-throttle sanity check (expected direction, not a defect):** the persisted/rendered values
(117 snapshots / 158 dates done) sit **below** the last live poll before the kill (162 snapshots / 203
dates done), exactly as expected — the checkpoint writer is throttled to roughly one write per 10s, so
the final persisted row reflects the last checkpoint *before* the kill, not the in-memory state at the
instant of the kill. This gap is the correct, designed behavior of a throttled checkpoint, not a
rendering defect or additional data loss.

**Contrast, same live page load, this turn:** querying every `[data-testid="run-status"]` element found
**10** rows with status `interrupted` total: run **119** (this cycle, 117 snapshots / 158 dates done —
non-zero), run **114** (prior cycle, 59 snapshots / 64 dates done — non-zero), and **8** pre-fix sibling
rows (ids 113, 110, 94, 88, 82, 79, 73, 72 — ranges `2025-06-01→2026-07-17`, `2017-01-01→2018-12-31`,
`2005-01-03→2005-06-30`, `2026-05-02→2026-05-03` ×2, `2020-03-16→2020-03-16`,
`2025-06-01→2026-07-17`, `2005-02-28→2005-03-07`, `2010-01-01→2010-06-30`) all showing `Snapshots: 0`,
`0 / 0` symbols, no breakdown paragraph, `Summary: "backfill: 0 snapshots over 0 dates, 0 forward
returns"`. (Run 118, the middle cycle's target, is no longer in this list — it shows `status: ok`, since
it had already self-completed before its kill, per that section above.) The fix-vs-no-fix contrast is
directly visible on one page load, with now **two** independent non-zero confirmations against eight
zero/null pre-fix rows.

**Screenshot note (same known limitation as runs 114/118):** a scroll-position-0 screenshot of `/data`
captured correctly (`UT-J-04-step6-run119-data-page-top.png`). A screenshot taken immediately after
`scrollIntoView({block:"center"})` on the run-119 row reproduced the same blank/near-black capture
artifact already documented for runs 114 and 118 on this tall page (saved anyway as
`UT-J-04-step6-run119-scrolled.png`), even though a DOM `eval` at the same instant returned fully correct,
populated content — confirmed to be a Chrome-MCP screenshot-capture quirk specific to this page's height,
not a rendering defect. The DOM/HTML capture above is the evidentiary artifact for the scrolled row.

**Conclusion:** this cycle succeeds where the run-118 cycle missed — the job was verified `running` via
API poll seconds before the kill, the kill landed genuinely mid-flight (203/504 dates done, well short of
completion), and the resulting live-rendered `/data` row shows exactly the required behavior: status
`interrupted`, non-zero persisted snapshots (117), non-null breakdown, with the persisted numbers sitting
below the last live poll by an amount consistent with the checkpoint throttle. **This closes the operator's
open item from the run-118 section** and is now the tightest-timing, most-conclusive direct evidence for
J-04 step 6 in this session — corroborating, and standing alongside, run 114's earlier finding. Full raw
evidence: `reports/qa/goal-ops-hardening-iter-10-evidence/UT-J-04-step6-run119-crash-cycle-evidence.txt`.
Screenshots: `UT-J-04-step6-run119-data-page-top.png`, `UT-J-04-step6-run119-scrolled.png` (blank, per the
known limitation noted above).

**No golden replay script was written for J-04.** The replay runner's three action types (`goto`, `click`,
`fill`) cannot perform a process `kill -9` — a crash journey is inherently not expressible in that
contract. This is a structural limitation, not an oversight; J-04 falls back to an LLM-driven browser pass
every time it needs re-verification, same as this iteration.

---

### UT-J-05 — J-05: Aggregates are precomputed at ingest, never on the fly (light re-confirmation)

**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-10-evidence/UT-J-05-stored-snapshot-scanner-run-378.png`

Per the iteration spec's TC-7 (BINDING: do not re-run the heavy-ingest pytest test), this is a light
re-confirmation of J-05's non-heavy acceptance steps, using a real (not simulated) single-day ingest:

1. **Single-day backfill (step 1):** submitted `backfill` for `2021-09-15` (confirmed via `GET /api/runs`
   beforehand that no snapshot existed for this date — nearest neighbors were 2021-09-01 and 2021-10-01,
   monthly cadence). Backend run id **117**. Took ~5m32s wall time (started 19:00:00.627Z, finished
   19:05:32.796Z) — most of that is the aggregate-finalize step, not per-symbol ingest (0 bars fetched,
   this is `seed`-provider backfill of already-present bars). Final state: `status: ok`,
   `snapshots_created: 1`, `dates_done/dates_total: 1/1`, `aggregates_refreshed: [latest_snapshot,
   coverage, membership_timeline, market_phase, forward_aggregates, research_hot_keys,
   drawdown_expectations]` (all 7 — including `latest_snapshot` and `market_phase`, since this ingested
   date became newly available).
2. **Stored, not recomputed, serving (step 2a):** navigated to `/scanner-runs`, confirmed `2021-09-15` now
   listed (linked to `/scanner-runs/1193` — matching the dataset's new Snapshot-dates count, 1192→1193,
   also visible on the `/data` coverage tiles on reload). Opened it: page reads **"Immutable snapshot — as
   of 2021-09-15 / Stored exactly as scanned; never recomputed for today. Scanned 2026-07-22 19:00:09 ·
   provider seed · benchmark SPY"**, Market Regime **73.02/100 "Risk-on"**, breadth/candidate-count tiles,
   and a full leaderboard (TECH, PWR, MPWR, …) — all rendered on first paint, no spinner, no loading state.
   This is the literal "stored, never recomputed" UI language plus instant rendering — the behavior J-05
   requires.
3. **Persisted run record lists refreshed aggregates (step 2b):** confirmed directly above (7 aggregates
   named) — also independently visible in the live `/data` page's "Job progress" panel text: `"backfill
   job · 2021-09-15 → 2021-09-15 · from a previous session / 1 snapshots · 1 trading days in range / 1
   calendar day · 0 already snapshotted · 0 non-trading / Refreshed: latest snapshot, coverage, membership
   timeline, market phase, forward aggregates, research hot keys, drawdown expectations"`.
4. **Cold `/data` load stays within budget (step 3, browser-side approximation):** since I could not
   restart the backend myself this turn, I approximated the "cold load" check as a fresh top-level browser
   navigation to `/data` (not a backend process restart): `performance.getEntriesByType('navigation')[0]`
   reported `responseEnd: 19ms`, `domContentLoadedEventEnd: 39.2ms`, `loadEventEnd: 226.9ms` — well within
   any reasonable page-load budget, consistent with the "serve from storage, no whole-table prefill" design
   (a 3.3M-row `daily_prices` prefill would not complete in 227ms). This is a browser-side timing check,
   not a literal backend-process cold-boot measurement — the latter is already covered by J-04 steps 1-2's
   citation above and was not re-run here to avoid restarting the backend.
5. **Health stays responsive around ingest (step 4, light check):** with backend run 118 (the J-04 staging
   job, see above) actively `running`, `GET /api/health` returned HTTP 200 in ~473ms. I did **not** run the
   heavy-ingest pytest test (`test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap`) —
   that is explicitly out of scope and BINDING "do not re-run" per the iteration spec; this is a lighter,
   real-but-bounded ingest job standing in for it, per TC-7's own framing ("via deterministic replay or LLM
   fallback... without executing the heavy-ingest pytest test").

**Golden replay script written:** `runs/goal-session-ops-hardening/journey-scripts/J-05.json` (lints clean
via `demo_runner.py --mode lint`). It replays: goto `/data` → fill start/end `2021-09-15` → click `Start` →
goto `/scanner-runs/1193` → expect text `"as of 2021-09-15"`. Since `2021-09-15` is now permanently a
stored immutable snapshot, resubmitting the same backfill on replay is an idempotent zero-work no-op (same
established pattern as this session's `J-01.json`/`J-03.json` goldens), and the assertion targets the
permanent "Immutable snapshot — as of 2021-09-15" heading text, which will render unchanged on every future
replay.

---

## Failed Tests

None.

---

## Skipped Tests

None. J-01 and J-03 were not executed — not because of any test-runner limitation, but because the
dispatch explicitly instructed: "Do NOT test these — a deterministic replay verifies them separately."
They are out of this artifact's scope entirely, not scored as SKIP.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (host-guard caps confirmed live in the boot banner:
  `cpu_list=0-3,8-11 blas_threads=4`, `memory_cap_mb=6144`, `malloc_arena_max=2`)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser`
- **Test Date:** 2026-07-22
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-10-evidence/`
- **Backend/frontend health at end of the originating agent's turn:** both HTTP 200 (19:17:58Z) — that
  agent did not stop or restart either service. Run id 118 (backfill, `2016-02-01 → 2016-05-31`) was left
  `running` (60/65 dates observed) for the operator's planned `kill -9` + continuation-agent re-verification.

- **CONTINUATION (same day, subagent-resume channel broken — a fresh agent instance closed out the
  pending item above):** the operator performed the crash cycle — `kill -9` on backend pid **1942885** at
  **2026-07-22T19:20:45Z**, restart as pid **2080333** at **19:20:49Z**, `GET /api/health` first 200 at
  **19:21:24Z** (all independently corroborated in `logs/backend.log`). Live re-check of run 118 on `/data`
  found it had already finished naturally (`status: ok`, 84/84 dates, `finished_at: 19:20:07Z`) **38
  seconds before** the kill — so this specific cycle produced no interrupted-job sample; it neither adds
  to nor detracts from step 6's PASS, which rests on run 114 (untouched by this cycle). Full detail in the
  "J-04 step 6 — staged fresh cycle" section above and
  `reports/qa/goal-ops-hardening-iter-10-evidence/UT-J-04-step6-run118-crash-cycle-evidence.txt`.
- **Backend/frontend health at end of this continuation turn:** both HTTP 200 (re-checked just now via
  `curl`) — no run currently `status: running` anywhere in the run history. This continuation agent did
  not start, stop, or restart either service.
- **~~Open item for the operator~~ — CLOSED (second continuation agent, same day):** the operator
  performed exactly the requested tighter-timed cycle — job `bad4f8e94be8448fbb0ac5812f1005c4` (backend
  run id 119, backfill 2014-01-02→2015-12-31, 504 dates) was confirmed `status: running,
  snapshots_created: 162, dates_done: 203/504` via API poll seconds before `kill -9` landed on backend
  pid **2080333** at **2026-07-22T20:32:15+01:00** (19:32:15Z); restart launched **20:32:18+01:00** as
  pid **2100030**; `GET /api/health` first 200 at **20:32:55+01:00**. This agent independently
  corroborated the restart timestamp/pid via `ps`/`ss` and `logs/backend.log` (no service touched by this
  agent) and read the resulting row live off `/data`: status **`interrupted`**, **`Snapshots: 117`**
  (non-zero), breakdown **"729 calendar days · 41 already snapshotted · 225 non-trading"** (non-null) —
  sitting, as expected, below the last live poll (162/203) due to the ~10s checkpoint-write throttle. Full
  detail: "J-04 step 6 — third cycle (mid-flight kill, CONFIRMED)" section above and
  `reports/qa/goal-ops-hardening-iter-10-evidence/UT-J-04-step6-run119-crash-cycle-evidence.txt`.
- **Backend/frontend health at end of this second continuation turn:** both HTTP 200 (`GET /api/health`
  → `{"status":"ok","readiness":"ready"}`; backend pid 2100030 confirmed live via `ps`/`ss` on port 8255).
  This agent did not start, stop, or restart either service, and no further crash cycle is needed — J-04
  step 6 now rests on two independent non-zero live-DOM observations (runs 114 and 119) against eight
  pre-fix zero/null sibling rows on the same page.
