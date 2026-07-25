# goal-ops-hardening-iter-23 Dev Handoff

**Phase:** goal-ops-hardening-iter-23
**Date:** 2026-07-25
**Agent:** developer
**Status:** complete

## What Was Built

Nothing product-facing — this is a zero-product-diff, evidence-closeout iteration per the spec's own framing
("close the iter-22 CONFIRM-reject gaps ... with zero product-code changes"). The deliverable is two closed
findings from `runs/goal-session-ops-hardening/iter-22/eval-confirm.md`:

1. **Session-demo evidence gap** — `reports/goal-session-ops-hardening-demo.json` (the file `demo.sh
   ops-hardening --session-live` actually reads, per `demo-phase.sh:78`) had zero steps for J-06/J-07/J-08.
   Appended 5 `[NEW]`-flagged, verified steps (n=8–12) covering all three journeys, additive-only.
2. **Undisclosed J-06 golden-script loosening** — `runs/goal-session-ops-hardening/journey-scripts/J-06.json`'s
   `default_timeout_ms` had been silently bumped 8000→18000 during iter-22's own dispatch. Investigated for a
   legitimate basis (a background-compute-window overlap); found none — reverted to 8000. The two assertion
   value changes from the same edit were independently re-verified against the live app and are both correct
   as iter-22 left them (kept unchanged).

The third eval-confirm.md finding (the `perf-budgets.md` TC-4 self-contradiction) was already fixed by the
operator before this iteration, per the coordinator's instruction — not touched.

## Investigation — J-06.json's undisclosed `default_timeout_ms` edit (TC-6)

**Method:** cross-referenced `logs/backend.log` request timestamps against `forward_aggregate_cache.created_at`
commit rows for every background-compute window (BCW) that ran on 2026-07-25, the same technique used in
iter-21/22.

**Timeline reconstructed (all times UTC unless noted; local = UTC+1):**

- The edit happened inside iter-22's own dispatch window. `eval-confirm.md` (an independent, earlier read)
  places it at **08:41 local**; the file's actual commit (`0df289c6`, bundled with the rest of iter-22's
  changes) landed later at completion, 09:12:12 local.
- The iter-22 regression/QA pass ran 08:16:51–08:44 local (bounded by the replay-lane's evidence screenshots
  at 08:16:51–08:17:00 and the LLM-lane results file `phase-goal-ops-hardening-iter-22-ui-test-results.llm.md`
  written at 08:44).
- A full query of **every** `forward_aggregate_cache` row created on 2026-07-25 (28 rows total, all
  accounted for) shows exactly one BCW overlapping that window: the browser-qa agent's own UT-J-08 trigger for
  `asof=2026-07-20`, with commits at 07:31:59 → 07:32:56 UTC (= **08:31:59 → 08:32:56 local**, horizon 1 through
  horizon 60/ready). No other BCW ran between 07:17 and 07:44 UTC.
- That BCW **closed at 08:32:56 local — 8+ minutes before the 08:41 edit.** J-06's own steps never dispatch a
  BCW themselves (step 9 visits `/backtest` at the *latest* as-of, which per J-08's own guarantee serves from
  storage, not a request-path compute).
- Direct confirmation from `logs/backend.log`: at **07:41:21.653184 UTC and 07:41:21.948696 UTC** (i.e.
  08:41:21 local — the exact minute of the disclosed edit), two `backtest_timing` lines show
  `is_latest=True total_ms=30.64` and `total_ms=44.65` — J-06's own `/backtest` step, responding in 30–45 ms,
  with zero contention of any kind.

**Finding: no legitimate BCW overlap is substantiated.** Per the spec's own instruction ("if no BCW overlap
is substantiated, the honest outcome is reverting to 8000 ms, not inventing a plausible-sounding number"),
`default_timeout_ms` is reverted to **8000** (`runs/goal-session-ops-hardening/journey-scripts/J-06.json`).

## Re-verification of the two changed assertion values (TC-7)

- **`/stocks/AAPL` → `"$304.89"`.** Read live via `GET /api/stocks/AAPL` (backend API, current `asof_date`
  `2026-07-22`): `row.invalidation.level = 304.88740039062503`, rendered verbatim by
  `ThemeAndInvalidationCard` (`apps/frontend/app/stocks/[ticker]/page.tsx:274`) as
  `row.invalidation.note = "Invalid below the 50-DMA at $304.89"`. **Current and correct** — this is the
  50-day-moving-average invalidation level, not a quote price, which is why it moved from iter-11's $302.65 as
  the price history advanced. No change needed.
- **`/research/event-study` step 11 → `"Setup & Pattern event study"`.** Read live via direct HTML fetch of
  `http://localhost:3255/research/event-study`: the page heading renders `"Research — Setup & Pattern event
  study"` (source: `apps/frontend/app/research/_labs.tsx:3681`, `EventStudyLabPage`'s `LabRouteShell title`
  prop) — contains the asserted substring exactly. `"Actionable"` (the pre-iter-22 value) does not appear
  anywhere on the page. **Current and correct.** (The page comment at `_labs.tsx:3677` and
  `event-study/page.tsx:3` note this is now "its own lazy route (J-104)" — the page was restructured with a
  new heading since the script was authored at iter-11, which explains the drift honestly rather than as a
  mystery.)

Both values are kept exactly as iter-22 left them — only the timeout needed reverting.

## Deterministic replay — corrected J-06.json (TC-8)

Ran the official harness (`scripts/automation/lib/demo_runner.py --mode verify`) against the corrected script:

```
python3 scripts/automation/lib/demo_runner.py --mode verify \
  --scripts-dir runs/goal-session-ops-hardening/journey-scripts --journeys J-06 \
  --results reports/phase-goal-ops-hardening-iter-23-regression-replay-results.md \
  --evidence-dir reports/qa/goal-ops-hardening-iter-23-evidence \
  --base-url http://localhost:3255 --phase-id goal-ops-hardening-iter-23 --repo-root <repo>
```

Result: **PASS, 0 failed** (exit 0). Evidence: `reports/qa/goal-ops-hardening-iter-23-evidence/J-06-verify.png`.

The harness itself records no per-step timing, so a separate, disclosed throwaway script
(`runs/goal-ops-hardening-iter-23/j06-replay-timed.py`) re-drove the same 11 steps by importing
demo_runner.py's own `_do_action`/`_check_expect` helpers read-only (no duplication of browser-automation
logic, no edit to the committed file) and timed each one:

| Step | URL | Elapsed | Budget | Verdict |
|---|---|---|---|---|
| 1 | `/` | 1349.33 ms | 8000 ms | PASS |
| 2 | `/stocks` | **2098.60 ms (slowest)** | 8000 ms | PASS |
| 3 | `/stocks/AAPL` | 1783.58 ms | 8000 ms | PASS |
| 4 | `/sectors` | 1071.85 ms | 8000 ms | PASS |
| 5 | `/themes` | 1021.62 ms | 8000 ms | PASS |
| 6 | `/data` | 1273.38 ms | 8000 ms | PASS |
| 7 | `/evidence` | 1096.49 ms | 8000 ms | PASS |
| 8 | `/scanner-runs` | 1573.93 ms | 8000 ms | PASS |
| 9 | `/backtest` | 1359.52 ms | 8000 ms | PASS |
| 10 | `/watchlist` | 1018.42 ms | 8000 ms | PASS |
| 11 | `/research/event-study` | 1007.11 ms | 8000 ms | PASS |

**0 breaches, all 11 steps PASS. Slowest step: step 2 (`/stocks`) at 2098.60 ms — 26% of the 8000 ms budget,
comfortable margin.** Raw CSV: `runs/goal-ops-hardening-iter-23/j06-replay-timed.csv`. This result reinforces
the investigation's conclusion: nothing here was ever close to needing 18000 ms.

## Session-demo manifest — new J-06/J-07/J-08 steps (TC-1, TC-2, TC-3, TC-4, TC-5)

Appended steps `n=8`–`12` to `reports/goal-session-ops-hardening-demo.json`, additive-only:

- **n=8 (J-06, full_tour):** `/stocks/AAPL`, budgets-table-vs-live-loads narrative. `expect: "Leadership"` (a
  data-loaded marker, not the drifting `$304.89` value — deliberately avoids repeating the fragile-assertion
  mistake this iteration is fixing elsewhere).
- **n=9 (J-07, full_tour):** `/backtest`, cites the developer's own reconciled `bcw-measure.csv` figures from
  `reports/perf-budgets.md`'s "Iteration 22" section verbatim — **68.79 s** window, **7.1191 s** max
  `/backtest`, **0.2530 s** max `/api/health`, **58.2 %** VmPeak margin. Confirmed the "28.06 s window"
  phrasing (the browser-qa poller's elapsed time, not the true window, per `eval-confirm.md` finding 2) does
  **not** appear anywhere in the file.
- **n=10, 11, 12 (J-08, full_tour/highlights/highlights):** the version-bump → refreshing → fresh-serve-after
  -warm sequence for `/backtest` (latest) and `/backtest?asof=2026-07-20` (twice), narrated from the verified
  iter-22 evidence (`UT-J-08` row + the exact banner copy in
  `apps/frontend/app/backtest/page.tsx`'s `RefreshingEvidenceBanner`, "Refreshing — showing the last complete
  evidence"). n=11 depicts the refreshing state, n=12 the post-warm fresh-serve state.

**Schema/DoD checks (all passed):**
- `python3 -m json.tool` parses the file as valid strict JSON (TC-4).
- Every step (old and new) retains all required keys (`n`, `title`, `narration`, `point_out`, `journey`,
  `new`, `verified`, `section`, `action`) — verified programmatically, no missing keys.
- Steps 1–7 diffed field-by-field against the committed `HEAD` version: **byte-identical, zero changes**
  (TC-5).
- `"section": "highlights"` count across the whole file: **8** (existing 6 + new n=11, n=12) — at the ≤8 cap.
  n=8, 9, 10 are `full_tour`.
- J-06: 1 new/verified step. J-07: 1 new/verified step, verbatim-cited figures confirmed, "28.06" absent.
  J-08: 3 new/verified steps (≥2 required; one refreshing, one post-warm, plus a baseline scene).

**Extra verification (not strictly required, done anyway per the iter-16 lesson — "verify each sentence
against the code that would have to be true for it"):** a second throwaway script
(`runs/goal-ops-hardening-iter-23/demo-steps-live-check.py`) live-drove all 4 distinct new goto+expect pairs
(n=8, 9/10 shared URL, 11/12 shared URL) against the running app using the same `demo_runner.py` helpers.
**All 5 checks OK** — every new step's `expect` text is genuinely present on the page today, not just
plausible-sounding.

## Files Changed

- `reports/goal-session-ops-hardening-demo.json` -- appended 5 new steps (n=8–12) for J-06/J-07/J-08;
  existing 7 steps byte-unchanged.
- `runs/goal-session-ops-hardening/journey-scripts/J-06.json` -- `default_timeout_ms` reverted 18000→8000; the
  two assertion values re-verified and kept unchanged (both already correct).
- `reports/phase-goal-ops-hardening-iter-23-regression-replay-results.md` -- new, demo_runner.py's own
  verify-mode output for the corrected J-06 replay.
- `reports/qa/goal-ops-hardening-iter-23-evidence/J-06-verify.png` -- new, replay evidence screenshot.
- `runs/goal-ops-hardening-iter-23/j06-replay-timed.py`, `j06-replay-timed.csv` -- new, throwaway per-step
  timing instrument + its output (TC-8 elapsed-time evidence; demo_runner.py itself untouched).
- `runs/goal-ops-hardening-iter-23/demo-steps-live-check.py` -- new, throwaway live-verification of the 4 new
  demo-step goto+expect pairs.
- `docs/handoffs/goal-ops-hardening-iter-23-dev.md` -- this handoff (new).
- `runs/goal-ops-hardening-iter-23/status.json` -- new, `current_step: dev_complete`.
- Nothing under `apps/backend/` or `apps/frontend/`.

## Tests Run

No application test suite applies — zero application source changes this iteration (schema/JSON validation
and replay execution are the test surface here, per the spec's own "Unit/integration: none new" instruction).

```
python3 -m json.tool reports/goal-session-ops-hardening-demo.json      # valid strict JSON
python3 scripts/automation/lib/demo_runner.py --mode verify --journeys J-06 ...   # PASS, 0 failed
python3 runs/goal-ops-hardening-iter-23/j06-replay-timed.py            # 11/11 steps PASS
python3 runs/goal-ops-hardening-iter-23/demo-steps-live-check.py       # 5/5 checks OK
```

Result: all PASS, 0 failed across every check above.

## Pre-handoff verification (developer.md checklist)

- **Service startup works:** the backend was found **not running** at dispatch start (despite the
  coordinator's note that it had "just [been] restarted" — no crash traceback in `logs/backend.log`, just an
  abrupt stop after the last recorded health poll; worth the coordinator's awareness, not a blocker). Restarted
  via `scripts/start-backend.sh` only (per AG-10), polled `/api/health` until `readiness: "ready"` /
  `warmup: 89/89`, confirmed clean. The frontend was already up and healthy throughout (HTTP 200, `next dev`
  process alive) and was never touched — matching iter-22's own precedent of not needing to cycle it. Did not
  perform an additional stop/start/stop/start cycle beyond the one needed restart: this iteration changes zero
  startup code (no `scripts/*.sh` edits), so a redundant cycle would verify nothing new while risking
  disturbing the quiet-BCW conditions the replay measurement needed.
- **External integrations:** N/A — no new adapters/scrapers this iteration.
- **Native dependency binaries:** N/A — no new dependencies; Playwright/Chromium (already installed) is
  exercised successfully by every replay/verification script above.

## Verification (`git status` / `git diff` at completion — TC-9)

```
$ git status --short --porcelain -- apps/backend apps/frontend
(no output)
$ git diff --stat -- apps/backend apps/frontend
(no output)
```

Both empty. Zero files under `apps/backend/` or `apps/frontend/` changed, staged, or left untracked by this
iteration.

## Anti-goal checks

- **AG-3:** the two re-verified J-06 assertion values were checked against the live app's actual current
  output (API read for the price/invalidation figure, direct HTML fetch for the heading) and match exactly —
  see "Re-verification" above.
- **AG-9:** every action this iteration was a plain `GET`/DOM read against the already-running seed-backed app,
  or a local, read-only `sqlite3`/Python DB query (`forward_aggregate_cache` timestamps). No backfill/fetch/
  rebuild job was submitted; no live external network call at any point.
- **AG-10:** the one backend restart needed was launched exclusively via `scripts/start-backend.sh`; host-guard
  caps confirmed live before proceeding (matching the pattern from iter-22's own handoff).

## Known Issues

None of the two agent-tractable eval-confirm.md findings were left open — both are fully closed with cited
evidence (see above). Two items worth the next reader's awareness, neither blocking:

- **Backend was down at dispatch start**, contrary to the coordinator's note. No log evidence of a crash
  (abrupt stop, no traceback) — restarted cleanly via the sanctioned script; flagging in case this recurs.
- **The J-08 "refreshing" demo step (n=11) deliberately does not assert the literal "Refreshing" banner text
  as its `expect` gate.** `asof=2026-07-20`'s background compute completed back in iter-22 (confirmed via the
  DB: `forward_aggregate_cache` rows for that date/version are already complete) and stays resolved until the
  next `dataset_version` bump, so that transient state is not reproducible on demand at an arbitrary future
  `--session-live` playback without a fresh ingest. Rather than embed an assertion likely to silently fail at
  replay time, `expect` uses the robust, always-present `"expanding window"` marker (true in both `ready` and
  `refreshing` states — confirmed live), and the semantic distinction (refreshing vs. fresh-serve) is carried
  in `narration`/`point_out` instead, grounded in the exact verified iter-22 banner copy. This is consistent
  with the demo-narrator's "showcase, not QA — a failed step is a soft note" design and the spec's own framing
  that this iteration's DoD is the JSON artifact's completeness/accuracy, not a witnessed live run.
- Did not investigate **who or what process** made the undisclosed J-06.json edit — only **whether** it was
  technically justified (the spec's actual ask). It was not; reverted.
