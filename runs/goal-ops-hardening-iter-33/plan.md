# goal-ops-hardening-iter-33 Execution Plan

**Goal alignment:** closes the launcher-mode blocker two consecutive evaluators (iter-31, iter-32) named
first in their next-step recommendation, then performs J-06's real-browser TTI + on-load-latency sweep
that bug has blocked all session. No new page/score/claim; the Vision's "each page loads only the data it
needs... measured against committed budgets" success criterion is what this closes. No drift from
`docs/goal.md`: the fix target (`scripts/start-frontend.sh`) is already named "prod mode" in the goal's own
J-06 step-1 text, so fixing the script (not amending the wording) is the goal-faithful choice, per the
spec's own NOTES. A small orthogonal framework fix (`merge_ui_test_results.py`'s `_ROW_RE`) rides along —
low-risk, mechanical, touches no product code.

## What to Build

- **Rewrite `scripts/start-frontend.sh`** (real file: `incredible_auto_dev/scripts/start-frontend.sh` —
  `scripts/` is a symlink) to genuinely serve production mode:
  - Preserve BYTE-FOR-BYTE the existing port-detection block (`CHAIN_FRONTEND_PORT` / deterministic
    sha1-offset fallback) and the `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_API_PORT` export logic — only the
    final `exec` line and what precedes it changes.
  - **Staleness check, not just "does `.next` exist":** confirmed by direct inspection this session that
    the checked-out `apps/frontend/.next` (accumulated from this whole session's `next dev` runs) has NO
    `BUILD_ID`, no `routes-manifest.json`, no `prerender-manifest.json` — it is a dev-mode cache, not a
    production build. `next start` errors immediately against it ("Could not find a production build").
    So "stale or missing" must mean: `.next/BUILD_ID` (or another prod-build-only marker file) is ABSENT,
    OR it is older than the newest mtime among `apps/frontend`'s tracked source files (excluding
    `node_modules`/`.next`) and `package.json`/`package-lock.json` — never a bare directory-existence
    check, which would wrongly treat today's dev-mode `.next` as current.
  - When stale/missing: run `next build` (respecting the existing `NEXT_DIST_DIR` env override already
    wired into `apps/frontend/next.config.js` — a verification build can target a scratch dir instead of
    clobbering `.next`, useful for the smoke tests below). On a NON-ZERO exit, print the build's own error
    output and exit non-zero — never fall back to `next dev`, never serve the stale `.next`.
  - When current: skip the rebuild, `exec npx next start -p "$FRONTEND_PORT"` directly.
  - If the production build surfaces an error dev mode tolerated (Next 15 prod builds run stricter
    type-checking than the dev server), fix ONLY what's needed in `apps/frontend` to make the build pass —
    no page's rendered content or behavior changes otherwise. ESLint is already `ignoreDuringBuilds: true`
    (`next.config.js`), so only real TypeScript/build errors are in play.
- **Verify (do not edit) `scripts/dev.sh`'s frontend subshell** stays `next dev`, untouched — this fix is
  scoped to `start-frontend.sh` only. Confirm via `git diff` that `scripts/dev.sh` and
  `scripts/start-backend.sh`'s HOST-GUARD blocks are byte-unchanged (TC-9) — this iteration's only risky
  change is the launcher's build mode, not anything host-guard-adjacent, and the frontend build step must
  NOT be wrapped in host-guard CPU/memory caps (explicitly out of scope — the frontend has always been
  host-guard-exempt).
- **Correct `scripts/measure-perf.sh`'s header comment** (`incredible_auto_dev/scripts/measure-perf.sh:11-14`)
  — documentation only. It currently says this script "refuses to measure against a `next dev` frontend (no
  reliable way to detect that from here, so it just documents the requirement...)". That caveat is now
  moot (the frontend genuinely is prod mode); reword to state the launcher now guarantees prod mode rather
  than describing an undetectable risk. No change to the timing/measurement code itself.
- **New smoke test, `apps/backend/tests/test_start_frontend_script.py`** (new file — mirror
  `test_start_backend_script.py`'s real-subprocess-on-an-isolated-port pattern; TESTING REQUIREMENTS
  explicitly asks for this): TC-1 (stale/missing build -> `next build` runs, then a `next start` process —
  verify via the owning PID's `/proc/<pid>/cmdline`, not just `ps aux` text, mirroring
  `test_start_backend_script.py::_owning_pid`'s "resolve via the listening socket" discipline since `next`
  can fork a further worker) is bound to the configured port; TC-2 (an already-current build skips the
  rebuild — assert `next build` did NOT re-run, e.g. `.next/BUILD_ID`'s mtime unchanged, or a measurably
  fast startup vs. TC-1's); TC-3 (a deliberately broken source file -> script exits non-zero, prints the
  build's own error, and leaves NO `next dev`/stale-`.next` process running).
  - **Design hint (verify before relying on it):** use `NEXT_DIST_DIR` (already wired in
    `next.config.js`) to point each test invocation's build/start at a scratch directory, so these tests
    never clobber or depend on the real checked-out `.next`. TC-3's "deliberately broken source" needs a
    temporary file change in `apps/frontend` (Next's prod build type-checks the whole project); add it
    inside a `try`/`finally` (or a `tmp_path`-copied `apps/frontend` tree, if that proves cleaner) so the
    real tree is NEVER left broken even if an assertion fails mid-test. A full `next build` is genuinely
    slow (tens of seconds) — an accepted cost for a real-process launcher proof, consistent with this
    project's existing slow real-engine test convention.
- **Widen `_ROW_RE` in `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py`** (line ~30:
  `re.compile(r"^\|\s*(UT-[^|]+?)\s*\|(.*)\|\s*$")`) to match BOTH `UT-` and `TC-` prefixed row ids (e.g.
  `(?:UT|TC)-`), so a `TC-`-prefixed headline FAIL from either merge input survives into the merged
  output — never silently downgraded to PASS because one file's rows failed the id-prefix regex and
  `compute_overall` fell back to a file-level verdict that happened to read differently. This module has
  no separate pytest file — its own `_self_test()` (invoked via `python3 merge_ui_test_results.py
  self-test`) is the test surface; add a new `check()` case there (mirroring `t_bold_verdicts`/
  `t_annotated_verdicts`'s style) proving a `TC-`-prefixed FAIL row survives a merge — RED against the
  unfixed regex, GREEN after.
- **J-06 measurement (TC-4/TC-5/TC-6):** the real-browser 11-page TTI + on-load-API-latency sweep, plus a
  fresh boot-to-health reading, against the now-fixed prod-mode frontend + a warm backend on the
  committed-seed DB. This is a genuine Chrome-driven measurement (iter-28's lesson: "measure the actual
  thing, not a proxy" — a curl timing is NOT a browser TTI), so it belongs to the browser-qa-agent pass
  that `Frontend Present: yes` triggers, not a developer-authored script. The developer's own
  responsibility here is narrower: get the launcher genuinely serving prod mode and verified bootable
  (a quick manual `curl`/health-check pass is enough pre-handoff confirmation — leave the formal dated
  sweep for QA), and write the code-level on-load audit below.
- **J-06 step-3 code-level audit → dev handoff:** for every on-load endpoint the 11 pages
  (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`,
  `/backtest`, `/watchlist`, one `/research` lab) call, name the persisted table/cache it reads (existing
  Data Contract rows — Regime score/market phase/forward-returns, Index series, Coverage payload, Job
  history, Membership timeline/research hot-key) and state plainly that none performs an unbounded
  `daily_prices` scan or recomputes an already-ingest-warmed aggregate (TC-6). This is a documentation/
  verification task grounded in reading the actual route handlers, not new code.
- **Golden-script hygiene (conditional — only if the launcher change requires it):** after the fix, do a
  local dry-run replay of the 8 golden journey-scripts
  (`runs/goal-session-ops-hardening/journey-scripts/J-0{1,3,4,5,6,7,8,9}.json`) against the prod-mode
  frontend before handoff. If — and only if — an assertion breaks purely because dev-vs-prod markup
  differs (dev-overlay pill removal, a CSS-module class-name difference), repair that ONE assertion to
  check stable content (a heading/label, per the iter-28 lesson) and document the specific diff that
  motivated it in the dev handoff. Any break that looks like a real behavior difference is a finding for
  the evaluator, not something to quietly patch — stop and disclose it instead.
- Write dev handoff at `docs/handoffs/goal-ops-hardening-iter-33-dev.md` (files changed, exact test
  commands/counts, the staleness-check design actually shipped, the `NEXT_DIST_DIR` scratch-build
  mechanism used by the smoke tests, the J-06 step-3 audit table, any golden-script repairs with their
  motivating diffs, and confirmation that `scripts/dev.sh` / `scripts/start-backend.sh`'s HOST-GUARD
  blocks are untouched).

## Agents Required

- backend-data: yes -- `apps/backend/tests/test_start_frontend_script.py` (new Python smoke-test file,
  same venv/httpx/pytest machinery as `test_start_backend_script.py`) and
  `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py`'s `_ROW_RE` widen + its
  `_self_test()` extension (Python framework tooling, no backend engine/app code touched — DoD explicitly
  states "no backend code path changes").
- frontend-ux: yes -- `scripts/start-frontend.sh`'s rewrite (build-if-stale + `next start`),
  `scripts/measure-perf.sh`'s header-comment correction, any minimal `apps/frontend` source fix a stricter
  prod build surfaces, and the conditional golden-script markup-only repairs.

Frontend Present: yes

## Files to Create/Modify

- `incredible_auto_dev/scripts/start-frontend.sh` -- rewrite: build-if-stale (byte-unchanged port/env
  logic) then `exec npx next start`; non-zero exit with the build's own error on a genuine build failure,
  never a `next dev`/stale-`.next` fallback.
- `incredible_auto_dev/scripts/measure-perf.sh` -- header-comment correction only (lines ~11-14), no
  timing/measurement code change.
- `apps/backend/tests/test_start_frontend_script.py` -- new file: TC-1/TC-2/TC-3 real-subprocess smoke
  tests for the rewritten launcher.
- `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` -- widen `_ROW_RE` to accept both
  `UT-` and `TC-` prefixes; extend `_self_test()` with a new RED-before/GREEN-after case proving a
  `TC-`-prefixed FAIL row survives a merge.
- `reports/perf-budgets.md` -- new dated "## Iteration 33" section (appended by the browser-qa-agent's
  real-browser sweep, per the pipeline's `Frontend Present: yes` gate — not authored by the developer
  directly, though the developer's handoff should reference it once QA has run).
- `docs/handoffs/goal-ops-hardening-iter-33-dev.md` -- new dev handoff (create), including the J-06
  step-3 on-load endpoint -> persisted-table/cache audit table.
- Possibly (conditional, only if the prod build or the golden-script replay surfaces a real diff):
  one or more `apps/frontend/**/*.tsx` files (minimal build-error fix only) and one or more
  `runs/goal-session-ops-hardening/journey-scripts/J-0*.json` assertions (markup-only repair, with the
  motivating diff documented).
- Do NOT touch: `scripts/dev.sh`, `scripts/start-backend.sh`'s HOST-GUARD blocks (TC-9 verifies
  byte-unchanged via `git diff`), `project-extensions/host-guard/host-guard.env`, any backend engine file
  under `apps/backend/app/engine/` (`compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched`, `stock_obs`'s bounded design — all binding "Do not
  redo" from iter-32).

## Frontend Present

yes

## UI Evolution

- New user-facing capability: none — this is a defect fix to the frontend's serving mode for automated
  evidence capture/measurement, not a new user-visible capability.
- New information displayed: none.
- New user actions: none.
- UI surface changes: none — no new component/page. Existing pages now render without the Next.js
  dev-mode error-overlay pill (the one visible-but-incidental difference, and only if it was ever showing).
- Navigation changes: none.

## Visual Requirements

N/A -- no new component, layout, or visual-effect work this iteration. If a prod-build type error forces a
minimal `apps/frontend` source fix, it must not change any page's rendered content or behavior beyond
making the build pass.

## Key Test Scenarios

Restating the spec's test-first contract as the acceptance bar:

- TC-1: `.next` missing or older than sources/`package.json`/lockfile -> `start-frontend.sh` runs
  `next build` before `next start`; the owning process on `FRONTEND_PORT` is `next start`, not `next dev`.
- TC-2: an existing, current `.next` build -> the script skips the rebuild and execs `next start` directly.
- TC-3: a deliberately broken `apps/frontend` source file -> the script exits non-zero, prints the build's
  own error output, and leaves no `next dev`/stale-`.next` process running.
- TC-4: warm backend (committed-seed DB) + fixed prod-mode frontend -> real-browser TTI + on-load API
  latencies recorded for all 11 J-06 step-1 pages, plus a fresh <=5s boot-to-health reading, appended as a
  new dated section in `reports/perf-budgets.md` (browser-qa-agent, post-dev).
- TC-5: any reading over its committed budget is recorded as an honest WARN with a one-line stated cause,
  never omitted from the table.
- TC-6: dev handoff lists every on-load endpoint the 11 pages call, names the persisted table/cache each
  reads, and states plainly none performs an unbounded `daily_prices` scan or recomputes an
  already-ingest-warmed aggregate.
- TC-7: zero error-level browser console entries on any of the 11 pages after load (no dev-overlay pill).
- TC-8: required-still-passing journeys J-01, J-03, J-04, J-05, J-08, J-09 all replay PASS against the
  prod-mode frontend, no assertion regression from their `last_passing_iter=32` baseline.
- TC-9: `git diff` shows `scripts/dev.sh` and `scripts/start-backend.sh`'s HOST-GUARD blocks byte-unchanged.
- TC-10: a QA input file with `TC-`-prefixed ids and a headline FAIL -> `merge_ui_test_results.py`'s merged
  output still shows that FAIL, not a laundered PASS (RED-before/GREEN-after self-test case).
- TC-11: `scripts/measure-perf.sh`'s header text no longer states the unresolved "no reliable way to
  detect [next dev]" caveat as an open limitation.

Error cases (explicit in spec's Testing Requirements): a `next build` failure must surface its own error
and exit non-zero, never silently fall back to `next dev` or serve a stale `.next` build; a merged QA
report whose ONLY input file uses `TC-` ids and reports a headline FAIL must show that FAIL in the merged
output, never a laundered PASS.

## Out of Scope (flagged per spec, do not implement this iteration)

- J-07's two remaining steps (health-poll latency recording through a live warm; the induced-memory-
  pressure abort drill) and its demo `[NEW]` walkthrough — deliberately deferred to iteration 34 (rule 5:
  one risky/heavy-compute change per iteration; this iteration's one risky change is the launcher's build
  mode).
- `run_rows` (`forward_testing.py:1195`) -- recorded WATCH ITEM (iter-32/f), untouched.
- The stray `GET /research/factor-lab?all=true` 404 -- binding "Do not redo," not re-investigated.
- `warmup.py:194` and `prices.py:141` -- carried, unresolved AG-8 findings, unrelated to this iteration's
  surface, not touched.
- `J-07.json`'s literal `n=8869` assertion -- deferred to iteration 34 (that journey's own golden script).
- `test_no_magic_numbers.py` red on `indicators.py`/`forward_testing.py`; UT-04's fresh-install DB fixture;
  `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches -- all carried, unrelated.
- Amending `docs/goal.md` to accept dev-mode TTI numbers -- rejected per the spec's own reasoning (see
  `assumptions.md` iter-33): the goal's own step-1 text already calls this script "prod mode."
- Applying host-guard CPU/memory caps to the frontend build step, or adding `start-frontend.sh` to
  `HOST_GUARD_MARKER_FILES` -- out of scope; the frontend has always been host-guard-exempt.
- Any change to `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched`, or `stock_obs`'s bounded accumulation shape -- binding
  "Do not redo" (iter-32).

## Testing Notes (host constraint)

- The new `next build` invocations inside `test_start_frontend_script.py` are genuinely slow real-process
  tests (tens of seconds each) -- an accepted cost, same category as this project's existing slow
  real-engine tests. Do not run them concurrently with any other heavy pytest/ingest process on this host
  (AG-10 host-guard convention) -- run them in the same single combined invocation as any other new/changed
  backend selectors this iteration, launched via `setsid nohup` + in-turn polling per this session's
  established subagent-background-process discipline (prior background-pytest-reaped-at-turn-end lesson).
- Do not run the full pytest suite (project convention -- the 30-year `loaded_engine` basis makes it
  ~10-11h; this iteration's backend-adjacent changes are narrow enough that targeted selectors suffice).
- The frontend build/start smoke tests must never leave a stray `next build`/`next start` process running
  on a shared port after a failure -- mirror `test_start_backend_script.py`'s `finally`-block SIGKILL +
  reap discipline exactly.
