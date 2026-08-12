# goal-ops-hardening-iter-72 Audit Report

**Date:** 2026-08-13
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's real goal — `GET /api/health` never stops answering under the concurrent heavy load that
produced iter-71's 165 s / 58-of-900 outage — is genuinely achieved, and I verified it by recounting both
raw poll CSVs myself and by bracketing the drill windows in `logs/backend.log` rather than trusting either
lane's prose: 1,315 browser-lane polls and 1,598 developer-lane polls, **every one HTTP 200, zero
inter-poll gaps over 2 s, zero `QueuePool` timeouts, zero `Exceeded concurrency limit` warnings** in either
drill window. The two root causes are fixed at the right place: the pool sum now genuinely covers uvicorn's
admitted concurrency and is enforced at boot, and the `/api/health` read path no longer touches `_TICK_LOCK`
at all.

Three things keep this off a clean PASS: one DoD deliverable (TC-10's `/data` honest-fallback screenshot)
was never produced yet was recorded as complete by the reviewer and substituted with unit tests by QA; the
developer-lane drill's own summary recorded a 12-of-43 `/api/backtest` failure rate that its perf addendum
omitted (disclosed by this audit, and traced to client-side timeouts, not server rejections); and the round
removes iter-71's never-serve-arbitrarily-stale-readiness bound with no user-visible disclosure and no
watchdog — spec-sanctioned, but the most consequential open limitation this session now carries.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): `config.yaml:1353` still advertised the synchronous fallback this iteration
removed.**
The developer corrected the now-false docstrings in `apps/backend/app/config.py` (`ReadinessCfg`),
`apps/backend/app/api/health.py`, and `readiness.py`, but left `config.yaml`'s own inline comment on
`readiness.max_stale_intervals` reading *"a cache entry older than max_stale_intervals x
refresh_interval_seconds (1.5s) is never served; GET /api/health falls back to a synchronous compute
instead"* — a statement that is now false in exactly the way `config.yaml:118-120`'s *"comfortably covers"*
comment was false, which is the defect this same iteration was chartered to correct one screen earlier in
the same file. A false comment about a removed safety guard is not cosmetic in this codebase's history:
iter-71's live outage was masked for many iterations by precisely that failure mode. I was unsure between
GAP and IMPORTANT and took the higher per the rubric.
*Fix applied:* comment rewritten at `config.yaml:1353` to state the field is currently unconsumed, why the
fallback was removed, and where the rationale lives. No value changed. See §4 for verification.

**B2 — IMPORTANT (fixed): `reports/perf-budgets.md` Addendum 37 omitted the drill's own
`/api/backtest` failure count.**
The addendum reports only `/api/health`, but the same drill's own summary
(`runs/goal-session-ops-hardening/iter-72/j07-drill-summary.json`) records `"backtest_ping_hits": 31,
"backtest_ping_errors": 12` — 12 of 43 `GET /api/backtest` attempts failed during the run the addendum
presents as clean. `.claude/judgment-rubrics.md` §6 requires failures be reported with their output, and
§5's "no regressions" floor requires an explicit list of what was not clean.
*Attribution verified, not assumed:* I bracketed the drill in `logs/backend.log` (lines 299954–301676,
between the `start-backend.sh: launching at 2026-08-12T20:52:52Z` header and the next launch header) and
counted **1,675 access lines, all `200`, zero `503`, zero `Exceeded concurrency limit`**. So the server
never rejected those requests — the 12 failures are client-side timeouts/aborts against a slow
`/api/backtest` under the heavy job. This *confirms* the addendum's "New finding" claim (the uvicorn
concurrency-limit 503 streak did NOT recur under TC-7's spec'd load) while showing TC-8's
"`/backtest` serves with no interruption" is **not** supported by this developer-lane drill — TC-8's real
evidence is the browser lane's live J-08 row.
*Fix applied:* an attributed AUDIT AMENDMENT block added to Addendum 37 carrying both the omitted figure and
the log-verified attribution.

**B3 — IMPORTANT (gap, unresolved): the DoD's TC-10 evidence — a filed screenshot of `/data`'s honest
fallback — does not exist anywhere, yet is recorded as done.**
DoD item 8 and TC-10 require a screenshot of `/data` rendering *"Dataset coverage could not load from the
API…"* under a fault-injected `GET /api/data` failure. I searched every iter-72 artifact
(`reports/qa/goal-ops-hardening-iter-72-evidence/` — 14 PNGs, all journey rows; the merged UI results; the
browser-QA slice; the demo gallery): **no TC-10 row, no such screenshot, no mention of
`TRENDORA_FAULT_INJECT_MEMORY_ERROR` in any QA artifact.** The review report nonetheless records
`definition_of_done: complete`, and the QA report substitutes *"TC-10: … verified by test_api_data.py"* —
a unit test, which is a different evidence class from the browser row + screenshot
`.claude/judgment-rubrics.md` §2.1 requires. Per §2.2 the correct status is `unknown`, not `done`.
*Product risk is low:* the fallback is pre-existing and unchanged (`apps/frontend/app/data/page.tsx:522-532`
renders the exact spec'd message from `state.kind === "error"`), and the backend probe is genuinely tested
(`apps/backend/tests/test_api_data.py`, 2 new tests, re-run by me). *Consequence:* this round shipped a new
**unguarded** fault-injection call into a production request handler
(`apps/backend/app/api/data.py:119`) whose sole justification — enabling that evidence capture — went
unused. *Not fixed here:* capturing it requires arming the env var in the backend process (a restart this
role is barred from performing on the shared QA stack) plus the browser lane; fabricating or paraphrasing
the evidence would violate §6.

**B4 — GAP: the never-serve-arbitrarily-stale-readiness bound is gone, with no user-visible disclosure and
no watchdog.**
`apps/backend/app/engine/readiness.py:645-649` now serves any existing cache entry unconditionally, however
old. That is exactly what the spec ordered, and the honesty mechanism (`stale_for_s`, uncapped) is real —
but the spec also deferred rendering `stale_for_s` on the badge/banner *and* deferred a tick-thread
watchdog. Net effect: if the background tick thread wedges or dies, the global readiness badge shows a
frozen "Ready" indefinitely and **nothing in any UI discloses it**; the disclosure exists only in an API
field no page reads. This reverses the guarantee iter-71 shipped to close iter-70's own named gap ("it can
now be fast and wrong"). Spec-sanctioned, so not a violation — but it is the round's most consequential
known limitation and the strongest argument for promoting the deferred `stale_for_s` surfacing.

**B5 — GAP: the post-lock recheck can silently drop the ingest finalize hook's requested refresh.**
`trigger_readiness_refresh` (`readiness.py:669-677`) exists specifically to run a tick on the ingest job's
OWN session so the cache reflects just-persisted rows. When that call is contended, `readiness.py:584-589`
reuses whatever entry the other thread just published — an entry whose underlying DB reads may have started
*before* the ingest committed — and the requested refresh never happens. `/api/health` can therefore report
pre-ingest readiness until the next periodic tick. Bounded and self-healing: `refresh_interval_seconds` is
`0.5` (`config.yaml:1352`), so the exposure is sub-second. The behavior is precisely what the spec's own
IN SCOPE bullet ordered, so this is a limitation of the spec'd design, not a deviation from it.

**B6 — OBSERVATION: `stale_for_s: 0.0` can understate a reused entry's age by up to
`refresh_interval_seconds`.** On the cold-start-contended path, `readiness.py:589` returns another thread's
entry and `readiness.py:665` stamps it `stale_for_s=0.0`. Bounded by 0.5 s and only reachable before the
first tick has ever published.

**B7 — OBSERVATION: `scripts/dev.sh` now sends the backend's stdout/stderr only to `logs/backend.log`**
(`incredible_auto_dev/scripts/dev.sh:99-103`). This is faithful parity with `scripts/start-backend.sh`
(which uses the identical `>> "$LOG_FILE" 2>&1`) and is what the spec asked for, but the interactive dev
launcher's terminal no longer shows backend/`--reload` output — a real day-to-day change for whoever runs
`dev.sh`; the frontend subshell still prints normally.

**B8 — OBSERVATION: `readiness.max_stale_intervals` is now a dead tunable** — still typed, validated and
boot-checked, consumed by nothing. Deliberate and documented (`apps/backend/app/config.py`, `ReadinessCfg`
docstring); flagged only so it is not mistaken for live behavior (B1 corrected the config-side comment).

**B9 — OBSERVATION: the causal claim is bundled, not isolated.** iter-71's baseline was measured on
`scripts/dev.sh` (no `--limit-concurrency`, no logfile); this round's on `scripts/start-backend.sh` with
the pool resize *and* the serve-stale fix *and* the launcher change all landing together. The drills prove
the target state is healthy; they cannot attribute the recovery to any one of the three. The
assumption-ledger entry (`runs/goal-session-ops-hardening/state/assumptions.md:1258`, iter-72) records the
decision to bundle rather than A/B, so this is a disclosed interpretation call — noted so no later round
cites Addendum 37 as isolating the pool fix.

**B10 — OBSERVATION: `runs/goal-ops-hardening-iter-72/status.json` records `browser_checks_run: false`**
while the browser lane ran and produced 8 result rows plus 14 screenshots. Stale field; harmless here, but
a downstream gate reading it would draw the wrong conclusion.

### Frontend Findings

None. `Frontend Present: no` is accurate — `git diff HEAD` touches zero files under `apps/frontend/`. The
`/data` fallback the round claims to evidence is pre-existing and unchanged
(`apps/frontend/app/data/page.tsx:522-532`); see B3 for the missing evidence artifact.

### Test Findings

**T1 — GAP: J-01's regression golden lost two assertions its own repair note does not disclose.**
`runs/goal-session-ops-hardening/journey-scripts/J-01.json` went from 16 steps to 14. The note discloses
dropping the `19/19 dates` chunk-progress expect and swapping the `zero-work-note` testid lookup for a text
expect. It does **not** disclose (a) the removal of the old step 6 `expect testid: stage-timings`, or (b)
the old step 13 `0/0 dates` → `no new snapshots` swap. I checked (a) against the product rather than
assuming: `data-testid="stage-timings"` still exists and renders
(`apps/frontend/app/data/page.tsx:2467`), so no product regression is being hidden — but the golden is
genuinely weaker and the note under-reports the change (`.claude/judgment-rubrics.md` §2.4). J-01's real
teeth (the exact per-reason breakdown lines) survive in both submissions. Not repaired by me: editing a
golden I cannot re-run through the replay lane would be an unverified fix.

**T2 — GAP: the deterministic replay lane produced zero green rows for 6 of 8 journeys.**
`reports/phase-goal-ops-hardening-iter-72-regression-replay-results.md` records **2/8 PASS**; J-01, J-05,
J-06, J-07, J-08 and J-09 all FAILed and were reconciled to PASS by the LLM lane. Per iter-64's lesson I
checked each "false positive" label against the actual frame rather than trusting it: **J-05's is
substantiated** (a direct sqlite read shows `data_provider_runs` id 469 `ok`, `snapshots_created=1`, and a
real `scanner_runs` row for 2005-07-11 — the runner was reaped, the job completed); **J-01's is
substantiated** (all three submissions re-run live with the exact breakdown strings); **J-06's is
plausible and independently supported** (its 2000 ms badge budget failed while the replay ran concurrently
with this session's own heavy drill, and my own recount of the health CSV shows p99 0.797 s / max 1.652 s —
enough to blow a 2 s end-to-end budget without any product fault). J-07/J-08/J-09's are attributed to the
same session contention with live re-verification afterwards. The DoD's own wording ("deterministic replay
+ LLM fallback") sanctions this, so it is not a renegotiation — but the round leaves **no clean replay
baseline** for the next iteration, which is worth fixing before it becomes structural.

**T3 — no finding: the new unit tests are tight.** TC-3's rewrite asserts `calls == {"readiness": 0,
"preflight": 0}`, `stale_for_s >= threshold + 10.0`, and that the cache entry is left byte-untouched — it
would fail loudly if any fallback returned. TC-4's two tests use an explicit block/release harness (not a
timing barrier) and assert exact compute counts (1 for the reuse case, 2 for the too-old case), so a
sleep-based race would fail, not silently pass. TC-1's four config tests cover the real config with a
`>= 4` margin assertion, the defaults path, the raising path (matched on message), and the `==` boundary.
TC-5/TC-6 spawn `dev.sh` for real and read `/proc/<pid>/cmdline`. The deleted iter-71 test's premise
(a synchronous fallback that can itself fail) is genuinely unreachable now, and its "never raises"
guarantee remains covered by `test_readiness_cache_cold_start_never_raises_on_a_first_tick_failure`
(`apps/backend/tests/test_readiness.py:792`) — verified, not taken on the handoff's word.

---

## 3. Domain Assessment

**The core fix is real and lands in the right place.** `get_readiness_and_preflight`'s hot path
(`readiness.py:643-649`) now returns before touching `_TICK_LOCK` at all — the read path is lock-free, which
is precisely the property iter-71's self-amplifying stall lacked. The only synchronous compute left is the
once-per-process cold start. I traced the lock discipline in `_tick_and_cache` (`readiness.py:579-599`)
line by line: exactly one acquire on both branches (non-blocking success, or non-blocking failure followed
by a blocking acquire), one `finally: release()`, the blocking acquire correctly placed *outside* the
`try` so a failed acquire cannot trigger an unmatched release. No deadlock, no double-release, no re-entrancy
hazard. The "detect contention explicitly rather than compare timestamps" choice is the right one — it is
what preserves the degrade-on-error contract for solo re-ticks, and the existing
`test_readiness_cache_degrades_to_last_known_good_on_tick_failure` still passes because of it.

**The pool fix is substantive, not cosmetic.** `config.yaml:125-126` (24+44=68) is genuinely consumed —
`apps/backend/app/db.py:78-79` passes both into the engine, and iter-71's own error text
(`QueuePool limit of size 10 overflow 20`) proves a real `QueuePool`, not a `NullPool`/`StaticPool` that
would have made the resize inert. The boot invariant at `apps/backend/app/config.py:2778` converts the
arithmetic mismatch into a loud `ConfigError`, which is the durable half of the fix — the numbers can drift
again, the invariant cannot silently drift with them.

**The evidence for the availability claim survives independent recounting**, which is the part I was most
prepared to find wrong. Browser lane: 1,315 rows, all `200`, max elapsed 1.652 s, **zero inter-poll gaps
above 2 s** (recomputed from timestamps, not from the file's own `breach` column), window
22:35:14→22:57:10 UTC fully covering job 474's 22:36:12→22:56:37. Developer lane: 1,598 rows, all `200`,
zero rows with an `error` value, p50/p90/p99/max matching the addendum to three decimals. Server-side, both
windows are clean of `503`s and concurrency warnings. The poller was armed 58 s before job start (closing
iter-71's twice-missed TC-5 gap), and the concurrency was genuine — the J-09 background compute ran
22:37:00–22:41:46 inside the ingest's own 20-minute window.

**Where the domain reasoning is weakest** is not the code but the trade it encodes: the round buys
availability by permanently surrendering the freshness bound, and then defers the one thing that would make
that trade honest to a user (rendering `stale_for_s`). Inside the API the honesty is complete; at the glass
it is not. That is B4, and it should be the next round's first candidate.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `config.yaml:1353` | Rewrote the `max_stale_intervals` inline comment, which still described the synchronous fallback removed by this same iteration, to state the field is currently unconsumed and why. Comment only — no value changed. |
| 2 | Important | `reports/perf-budgets.md` (Addendum 37) | Added an attributed AUDIT AMENDMENT disclosing the drill's own omitted `backtest_ping_errors: 12` of 43, with the log-bracketed attribution (0 server-side non-200 in the window ⇒ client-side timeouts) and an explicit correction of which lane actually carries TC-8's evidence. |

**Post-fix verification (commands run, results cited):**
- `cd apps/backend && .venv/bin/python -m pytest tests/test_config.py -q -p no:randomly` → **75 passed**
  (covers all four TC-1 tests; proves `config.yaml` still parses and the invariant still holds after fix 1).
- `.venv/bin/python -c "from app.config import get_config; …"` → `pool 24 + 44 = 68 >= limit_concurrency 64`;
  `readiness refresh_interval_seconds 0.5 max_stale_intervals 3` — values byte-unchanged by fix 1.
- `cd apps/backend && .venv/bin/python -m pytest tests/test_readiness.py -q -k "cache or tick or stale or recheck" -p no:randomly`
  → **15 passed** (independent re-run of the TC-3/TC-4 and degrade-on-error suite, before and unaffected by
  the fixes).
- `cd apps/backend && .venv/bin/python -m pytest tests/test_config.py -k pool tests/test_api_data.py -k "fault_injection or pool" -p no:randomly`
  → **6 passed**.
- Self-diff re-read (`git diff -- config.yaml`): my change adds exactly one comment line beyond the
  developer's four pool lines; nothing else. `reports/perf-budgets.md` is insert-only.
- **TC-12 re-checked after my edits, from both git roots:** `git status --porcelain -- config.yaml
  project-extensions/ scripts/` → ` M config.yaml` at the repo root and ` M incredible_auto_dev/scripts/dev.sh`
  at the symlink target's root — unchanged from before this audit. `git diff HEAD -- config.yaml | grep -E
  "memory_cap_mb|malloc_arena_max|HOST-GUARD"` → **empty**; `project-extensions/host-guard/` → **clean**.
  No AG-10 cap value or HOST-GUARD block was touched by the iteration or by this audit.

No handoff claim was invalidated by either fix (both are corrections to records the handoff itself pointed
at, not to behavior it described).

---

## 5. DEFINITION OF DONE — verification ledger

| # | DoD item | Status | Basis |
|---|---|---|---|
| 1 | Pool sum ≥ `limit_concurrency`, unit-tested | **MET** (full trace) | `config.yaml:125-126` = 68 ≥ 64; boot validator `apps/backend/app/config.py:2778`; consumed at `apps/backend/app/db.py:78-79`; 4 tests re-run by me (75/75 in `test_config.py`) |
| 2 | J-07 passes via browser-qa on `start-backend.sh`+`start-frontend.sh` | **MET** (full trace) | Raw CSV recounted by me: 1,315 rows / all 200 / 0 gaps > 2 s; server log window clean of 503s & concurrency warnings; launcher confirmed by cmdline in `…-ui-test-results.md` row UT-J-07 and by the absence of any `dev.sh` boot header after 21:45:56Z |
| 3 | J-05 returns to `passing` | **MET** | UT-J-05 row; step 3 (cold restart) carried per the spec's own "steps 1-3 carried" clause; step 4 re-verified live against the same drill |
| 4 | Required-still-passing J-01/03/04/06/08/09 green | **MET, with T2** | Merged results 8/8; deterministic lane 2/8 with six documented LLM-lane overrides (see T2) |
| 5 | No anti-goal violation; scoped git status | **MET** (full trace) | Verified from both git roots after my own edits — see §4 |
| 6 | Unit/integration tests pass; iter-71 test rewritten | **MET** (full trace) | Rewrite present and tight (T3); re-run by me — 15 + 75 + 6 passed; deleted test's guarantee still covered at `test_readiness.py:792` |
| 7 | `logs/backend.log` gets a `dev.sh` boot line; uvicorn carries the 3 flags | **MET** (full trace) | Three real `=== dev.sh: launching at … ===` headers in `logs/backend.log` (lines 302071, 302113, 302176) from this round's spawns; `test_dev_script_wires_server_ops_flags_and_persistent_logfile` reads `/proc/<pid>/cmdline` for all three flags and asserts the frontend subshell carries none |
| 8 | TC-10 `/data` fallback screenshot filed | **NOT MET** | No such artifact exists anywhere — see B3 |
| 9 | `perf-budgets.md` dated addendum vs iter-71's figures + J-06 carry item | **MET**, amended | Addendum 37 (launcher named, full distribution, J-06 carry item recorded); completeness corrected by fix 2 |
| 10 | Dev handoff written | **MET** | `docs/handoffs/goal-ops-hardening-iter-72-dev.md` |

---

## 6. Recommended Next Step

Proceed to the next iteration — the availability regression that drove the ESCALATE is genuinely closed and
independently re-verified. Carry these four items forward, in priority order:

1. **Render `stale_for_s` (B4).** It is now the only thing standing between an unbounded stale readiness
   payload and a user reading a frozen "Ready" badge. It was deferred as "this cycle's first UI change";
   after this round it is the honest completion of this round's own trade, and it is a standalone,
   review-friendly change.
2. **Capture TC-10's screenshot (B3)** in the next `Frontend Present: yes` round — the mechanism is already
   built, tested, and shipped into the request path; only the evidence is missing. If it is not captured
   next round, remove the unguarded probe from `apps/backend/app/api/data.py:119` rather than leave an
   unused fault hook in a production handler.
3. **Restore a clean deterministic replay baseline (T2/T1)** — six overridden FAILs in one round is the
   point at which the replay lane stops being a gate. Re-run the goldens against a quiet host, and
   disclose every golden edit in the note that accompanies it.
4. **Ask the owner about B-1107 again, with the new evidence.** The addendum's un-spec'd-load 503 streak,
   now confirmed by this audit as absent under the spec'd load but real above it, plus the 12-of-43
   client-side `/api/backtest` failures during a single heavy job, are two independent arguments for
   bounding concurrent heavy computes. This round's fixes were deliberately chosen to not require that
   decision; the next availability failure probably will.
