# Phase goal-ops-hardening-iter-17 — UI Test Results

**Phase:** goal-ops-hardening-iter-17
**Date:** 2026-07-24
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- Driven mechanically by UT-01 (P1 smoke) failing in its raw/unpatched, real-browser form. Read
     "Critical Environment Finding" below before treating this as a product regression: it is not one —
     this iteration's OWN target functionality (B1 cross-asof_key fallback, evidence_asof, corrected
     copy) is independently verified CORRECT (UT-02/03/04/05/06 all PASS). The FAIL is a session
     infrastructure defect (two concurrently-running `next dev` processes sharing one build directory)
     that currently breaks real browsing of the main pair (:3255), discovered and root-caused this run. -->

**Overall:** 5/7 tests passed, 1 failed, 1 skipped

---

## Critical Environment Finding — read this before the results table

Two things discovered this run affect how every main-pair (`:3255`/`:8255`) row below must be read. Neither
is a code change from this iteration's diff (confirmed against the ui-surface-map's "Backend-Only Changes"
and a direct read of the affected files' git history — `readiness-provider.tsx`, `health-badge.tsx`,
`preflight-banner.tsx`, `lib/api.ts`, `lib/api-base.ts`, and `app/data/page.tsx` are not part of iter-17's
changed set). Both are session/process-provisioning defects.

### Finding 1 (major) — the main frontend's compiled client bundle is cross-wired to the THROWAWAY backend

**Symptom:** `http://localhost:3255/backtest`, navigated fresh (3 separate full navigations, plus a brand-new
tab to rule out single-tab staleness), shows the top-bar readiness badge and the layout-level preflight
banner stuck on **"Backend unavailable"** / **"NO-GO — do not rely on today's board."** indefinitely — a
15-second direct DOM wait (`await_element [data-state="ready"]`) timed out every time. The backtest page's
own evidence/scorecard fetch fails the same way, so the WHOLE page below the nav renders only the two error
cards, nothing else.

**Root cause, confirmed (not inferred):**
1. I instrumented `window.fetch` in-page (a logging wrapper) and observed the app's OWN health poll
   (`ReadinessProvider`'s retry loop, which fires every ~2s) was calling
   `http://localhost:18255/api/health` — the **throwaway** backend's port — from a page loaded at
   `http://localhost:3255`. A plain manual `fetch('http://localhost:8255/api/health')` run in the exact
   same page context succeeded instantly (200, `readiness:"ready"`), 5/5 times, ruling out CORS/network/DNS.
2. `ps`/`/proc/<pid>/cwd` showed the main frontend's `next-server` (pid 1188846, port 3255) and the
   throwaway frontend's `next-server` (pid 1245599, port 13255) run with the **identical** cwd
   (`apps/frontend`) and therefore the same default `.next` build-output directory — confirmed by
   `apps/frontend/.next` having one shared, very-recent mtime. Each process's own **process env** is
   correctly set (`NEXT_PUBLIC_API_URL=http://localhost:8255` for the main pid, `...:18255` for the
   throwaway pid — verified via `/proc/<pid>/environ`), but Next dev-mode writes non-content-hashed client
   chunks to that shared directory, so whichever process last compiled a shared chunk (e.g. `lib/api.ts`'s
   `apiBase()`, bundled into a common chunk both pages use) overwrites the other's — the main server keeps
   serving HTML that references that chunk path, but the BYTES now on disk are the throwaway's.
3. **A diagnostic workaround** (not a fix — no file, config, or service touched) confirms the underlying
   page logic is correct once it can reach the right backend: re-patching `window.fetch` in-page to rewrite
   any `localhost:18255` URL back to `localhost:8255`, then letting the health poll's own existing 2s retry
   loop tick through the patch, flips the badge to **Ready** / the banner to the REAL **DEGRADED** verdict
   (matching a direct `curl` of `:8255/api/health` exactly), and — because `/backtest` refetches on a
   readiness transition (`app/backtest/page.tsx`'s own comment: *"this page refetches only on mount / an
   as-of change / a readiness transition"*) — the whole page (scorecard, leadership, evidence) then renders
   fully and correctly. Screenshots of both states: `UT-01-top.png` (raw, broken) vs.
   `UT-01-top-workaround.png` (patched, correct).

**Related manifestation, same root cause (Finding 1b):** `http://localhost:3255/data` fails even harder —
its own per-route chunk is not merely wrong, it is **absent**. Console showed
`ChunkLoadError: Loading chunk app/data/page failed. (timeout: .../_next/static/chunks/app/data/page.js)`;
`ls apps/frontend/.next/static/chunks/app/data/` on disk is an **empty directory**; a direct `curl` of that
exact chunk URL returns **HTTP 404**. This is not fixable by any in-page workaround (the file genuinely does
not exist) — it blocked UT-03's literal steps 1-6 (see that test's own entry below for the substitute I used).

**Impact:** any real visitor to `http://localhost:3255` right now gets a broken top bar/preflight banner on
every page, and a non-functional `/data` page, regardless of browser or tab.

**What's needed (I did not do this — no service start/stop/restart this session per the operator note):** a
restart of the main and/or throwaway frontend `next dev` process with an **isolated** build-output directory
for at least one of them. The project already has this convention on disk — `apps/frontend/.next-iter25`,
`.next-alt-qa`, and `.next-verify` all exist alongside the default `.next` — so an operator likely needs to
launch one of the two concurrent instances against one of those (or a fresh one) instead of the shared
default, then restart.

### Finding 2 (minor) — throwaway backend's CORS allowlist doesn't include the `127.0.0.1` origin form

The dispatch note's literal `http://127.0.0.1:13255/backtest` is unreachable in a real browser: a `curl`
CORS preflight check confirms `http://localhost:18255` sends `access-control-allow-origin:
http://localhost:13255` for `Origin: http://localhost:13255`, but sends **no** `access-control-allow-origin`
header at all for `Origin: http://127.0.0.1:13255` — browsers treat `localhost` and `127.0.0.1` as distinct
origins, so the throwaway frontend's own health/backtest fetches are CORS-blocked when the page is loaded
via the `127.0.0.1` host form, producing the identical "Backend unavailable" symptom as Finding 1 but for a
different reason. **Substitution used:** I loaded the SAME throwaway pair via
`http://localhost:13255/backtest` instead (confirmed via `curl` to reach the identical frontend process, and
via its own `/api/health` to reach the identical disposable-DB backend) — no patch/workaround needed once
the matching-origin URL was used; UT-02/UT-06 below are clean, unpatched passes.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/backtest` loads without errors (main) | smoke | P1 | Page renders; heading+as-of badge+Survivorship card visible; scorecard/leadership headings above populated tables; no console errors | **Raw/real (as literally specified):** stuck on "Backend unavailable"/NO-GO indefinitely — Environment Finding 1. **Under the diagnostic workaround:** heading, "Ready"/DEGRADED banner, Survivorship card, populated scorecard/leadership all render correctly, no console errors | FAIL | `reports/qa/goal-ops-hardening-iter-17-evidence/UT-01-top.png` (raw), `UT-01-top-workaround.png` (workaround) |
| UT-02 | `not_yet_computed` empty state renders (throwaway) | smoke | P1 | Page renders, no Backend-unavailable card; bottom dashed card w/ flask icon, exact title+description, no "run an ingest", not duplicated; survives refresh | Loaded via `http://localhost:13255/backtest` (Finding 2 — the dispatched `127.0.0.1` form is CORS-blocked); rendered cleanly, **no workaround needed**. Bottom card text matches spec verbatim; F5-equivalent refresh reproduced identical content, zero new console errors. As-of-scan-summary was POPULATED (not "unavailable" as the plan assumed) — the throwaway DB has real snapshot data through 2026-07-01 with only `forward_aggregate_cache` emptied (matches the pump note precisely); the plan itself flags that bullet as "not the focus of this test" | PASS | `reports/qa/goal-ops-hardening-iter-17-evidence/TC-09-not-yet-computed-state.png` |
| UT-03 | Live capture: corrected banner + `evidence_asof` (main) | happy-path | P1 (time-boxed) | Banner text exact match; real calendar date before "generated"; evidence still populated below; screenshot saved to the reserved filename | `/data`'s own page could not be driven via browser (Finding 1b — missing chunk); submitted the IDENTICAL `POST /api/data/jobs {kind:"backfill",start:"2025-05-29",end:"2025-05-29"}` a real "Start" click would issue (fresh gap date, not one of the 5 already-taken dates). `/backtest` (workaround-patched) then rendered the banner with the EXACT expected sentence, "2026-07-22" as a real date before "generated", and fully populated evidence below it | PASS | `reports/qa/goal-ops-hardening-iter-17-evidence/TC-07-refreshing-banner-with-asof.png` |
| UT-04 | Evidence section populated in ready state (main) | regression | P1 | Populated evidence section; either no banner (ready) or a refreshing banner over still-populated numbers — both PASS; only an empty not-yet-computed card is a FAIL | Workaround-patched: confirmed BOTH accepted shapes — plain ready/no-banner (DOM-verified before UT-03's job existed) and refreshing-with-populated-numbers (screenshot, captured mid-UT-03-job) — never the empty card | PASS | `reports/qa/goal-ops-hardening-iter-17-evidence/UT-04-ready-evidence-bottom-refreshing.png` |
| UT-05 | Scorecard/leadership sections unaffected (main) | regression | P1 | Scorecard: one row/horizon, numeric or "—"; Top Sectors/Themes: ranked w/ score+return; Ranked cohort: rank/ticker/setup/leadership/return populated | Workaround-patched: Forward-test scorecard shows 5 horizon rows (1d/5d/10d/20d/60d), each "—"/n=0 (correct NA — latest date has no elapsed forward window); Top Sectors (5) + Top Themes (5) ranked w/ score badges; Ranked cohort shows 10 rows, all columns populated | PASS | `reports/qa/goal-ops-hardening-iter-17-evidence/UT-01-top-workaround.png` (scorecard), extracted DOM text for leadership/ranked-cohort (see below) |
| UT-06 | Empty-state copy reads factually (throwaway) | ux | P2 | States fact + resolution without commanding; discloses no-fabrication; one clean sentence, no duplicated opening clause | Same page load as UT-02 (`localhost:13255`): text confirmed verbatim — no "run an ingest"; explicit "no numbers are fabricated in the meantime"; single clean sentence, title not repeated in the body | PASS | `reports/qa/goal-ops-hardening-iter-17-evidence/TC-09-not-yet-computed-state.png` |
| UT-J-04 | J-04: Non-blocking boot with visible status (regression journey) | regression | P1 (journey) | This iteration's own scope is a non-disruptive steady-state check only (no kill/restart) — health 200/ready; log shows no new crash/restart banner | Fresh `GET /api/health` → 200, `readiness:"ready"`, `db_ok:true`. `logs/backend.log` grew 41568→42382 lines with zero new `launching`/`Shutting down`/`Finished server process` lines (no crash since the last recorded launch, 2026-07-24T01:41:20Z). Full kill/restart replay not performed (binding out-of-scope this iteration, matching iter-14/15/16 precedent). The badge's real-time browser observability is currently compromised by Environment Finding 1 on the raw path; the workaround shows the underlying readiness-computation-and-display logic itself is unaffected and correct | SKIPPED | n/a — see dedicated section below |

---

## Passed Tests

### UT-02 — `not_yet_computed` empty state renders correctly (throwaway)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-17-evidence/TC-09-not-yet-computed-state.png` (full-page)
- Loaded `http://localhost:13255/backtest` (substituted for the dispatched `127.0.0.1:13255` — see
  Environment Finding 2; same throwaway backend/frontend/disposable-DB, confirmed via `curl` to both
  hostnames landing on the same processes).
- Badge showed "Ready", `provider: seed`, `seed 2026-07-01`, `590 symbols`; preflight banner showed the real
  DEGRADED verdict (matches a direct `curl` of `:18255/api/health`) — no patch needed, unlike the main pair.
- Bottom of page: a dashed-bordered card, flask icon, title **"Backtest evidence not yet computed"**, body
  **"No forward-tested evidence exists yet for this date. Backfilling or fetching data that covers it will
  compute this evidence — no numbers are fabricated in the meantime."** — byte-identical to
  `apps/frontend/app/backtest/page.tsx`'s `EmptyState` call site. The phrase "run an ingest" does not appear
  anywhere on the page. The description is one clean sentence pair, not a duplicated opening clause.
- Refreshed (re-navigated to the same URL, F5-equivalent) and re-checked: identical card/title/description
  reappeared; zero new console errors (only the standard React DevTools info line both times).
- Deviation from the plan's assumption (documented, not a failure): the "As-of scan summary" area was
  POPULATED (Market Regime 72.25/100 "Risk-on", Candidate Counts 0/59/0), not "Scan summary unavailable for
  this date" as the test plan assumed for an "empty DB" — because this throwaway copy actually has real
  snapshot data through 2026-07-01 (only `forward_aggregate_cache` is emptied), matching the pump note's own
  more precise description ("a DB copy with `forward_aggregate_cache` emptied — NOT the main app") rather
  than the plan's "schema created, zero rows" phrasing. The plan itself marks that specific bullet "not the
  focus of this test"; the focus bullet (the bottom empty-state card) matches exactly.

### UT-03 — Live capture: corrected "Refreshing" banner + `evidence_asof` label (main)
**Verdict:** PASS (methodology deviation fully disclosed — see below)
**Evidence:** `reports/qa/goal-ops-hardening-iter-17-evidence/TC-07-refreshing-banner-with-asof.png` (full-page)
- **Steps 1-6 (the `/data` form) could not be driven through the browser** — Environment Finding 1b: the
  main frontend's `/data` route chunk is absent from disk (`ChunkLoadError`, confirmed 404 on the exact
  chunk URL). I checked the backend directly for a fresh, unused gap date instead of reading it off the
  (unreachable) form: `curl http://localhost:8255/api/data`'s `coverage.gap_last` = `"2025-05-29"`, not one
  of the five dates the pump flagged as already taken (2025-05-20/21/22, 2025-05-28, 2026-07-21). I then
  issued the IDENTICAL request `apps/frontend/lib/api.ts`'s `startDataJob()` (the function the form's
  "Start" button calls) would send — `POST http://localhost:8255/api/data/jobs` with
  `{"kind":"backfill","start":"2025-05-29","end":"2025-05-29"}` (kind `backfill` = the form's default
  "Backfill snapshots") — confirmed accepted: `{"job_id":"9bcf2469...","status":"running"}`.
- This is a **historical gap-date** backfill (2025-05-29, over a year before the latest snapshotted date),
  which is the SAME pre-existing same-`asof_key` stale-version mechanism UT-03's own "IMPORTANT" note
  describes (bumps the shared dataset-version stamp, momentarily staling the LATEST date's own
  forward-aggregate rows while the prior complete version keeps serving) — not the new cross-`asof_key`
  fallback (confirmed unreachable this session per the Scope note; not claimed here).
- Polled `GET http://localhost:8255/api/backtest` directly and saw `evidence_status` flip to `"refreshing"`
  with `evidence_asof: "2026-07-22"` while the job's own status endpoint still showed `"status":"running"`,
  `aggregates_refreshed: []` — the exact transient window the test wants captured.
- **Steps 7-9 (the `/backtest` capture) WERE performed via real browser observation**, workaround-patched
  per Environment Finding 1 (a fresh navigate + an in-page fetch-redirect patch, since the one-shot
  evidence fetch on this page has no automatic retry — the app's own readiness-transition refetch carried
  the patched call through). Captured `[data-testid="evidence-refreshing"]`'s exact text:

  > "Refreshing — showing the last complete evidence" / "The dataset has changed since this evidence was
  > generated, and the newer version is not complete yet. The forward-tested evidence below is the last
  > complete version — evidence as of 2026-07-22, generated 2026-07-23 21:56:07 — no partial or fabricated
  > figures are shown in the meantime. Reload this page after the next ingest finishes to pick up the new
  > version."

  — word-for-word the expected copy, a real calendar date ("2026-07-22", never an em dash/blank) in the
  "evidence as of ___, generated" position, sitting above a still-fully-populated evidence section (Forward
  return by score bucket, Excess vs SPY/QQQ, by setup type, by market regime, etc. — all with real
  percentages and `n` counts). Saved to the exact reserved filename.
- **What this proves and does not prove** (per the test's own "IMPORTANT" clause): proves the corrected
  banner text and the new `evidence_asof` label render correctly when `refreshing` occurs via the
  pre-existing same-`asof_key` mechanism. Does NOT exercise the NEW iter-17 cross-`asof_key` fallback
  (unreachable this session, confirmed separately by backend unit tests per the qa report).

### UT-04 — Evidence section stays populated in the normal "ready" state (main)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-17-evidence/UT-04-ready-evidence-bottom-refreshing.png`
- Workaround-patched (Environment Finding 1) two separate observations, both explicitly acceptable per this
  test's own Expected Result:
  1. Before UT-03's job existed: DOM query confirmed `evidence-refreshing` testid ABSENT, `"Backtest
     evidence not yet computed"` text ABSENT, and the "Forward-tested evidence" section's tail text showing
     real populated numbers (Snapshots contributing: 1801, Mean stock fwd return (60d): +4.34% (n=744166),
     buckets A-E with distinct percentages, Excess vs SPY +0.61% / vs QQQ -1.26%) — the plain `ready` case.
  2. During UT-03's job (mid-warm): the amber refreshing banner appeared ABOVE the same still-fully-populated
     section — the test's own explicitly-alternative-acceptable case ("that is ALSO a PASS").
  - Neither observation ever showed the empty "not yet computed" card on the main pair.

### UT-05 — Scorecard and leadership sections unaffected by this iteration's backend change (main)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-17-evidence/UT-01-top-workaround.png` + DOM text extraction
- Workaround-patched (Environment Finding 1): "Forward-test scorecard" shows one row per configured horizon
  (1d/5d/10d/20d/60d), each "—　n=0 ⚠" — correct NA (today's date has no elapsed forward window yet), not
  blank, not an error card.
- "Top Sectors" (HACK/CIBR/KRE/KBE/XBI) and "Top Themes" (Cybersecurity/Glp1 Pharma/Ai Data Centre/Software
  Cloud/Megacap Leaders) each show 5 ranked entries with a leadership-bucket score badge and a return figure.
- "Ranked cohort" shows a 10-row table (TRV, WELL, TECH, SNOW, INCY, PM, VTR, GL, PANW, ALL) with rank,
  ticker, setup, leadership badge, and forward-60d-return columns all populated.
- None of these values differ from what a direct `curl` of `/api/backtest`'s `scorecard`/`leadership_returns`
  fields shows — consistent with the ui-surface-map's claim that these sections are untouched this iteration.

### UT-06 — Empty-state copy reads factually and does not presume the user hasn't already acted (throwaway)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-17-evidence/TC-09-not-yet-computed-state.png`
- Same page load as UT-02. Full description text: "No forward-tested evidence exists yet for this date.
  Backfilling or fetching data that covers it will compute this evidence — no numbers are fabricated in the
  meantime." — states what's true now + what resolves it, without an imperative "run an ingest" (audit F2
  fixed); explicitly disclaims fabrication (audit tone requirement met); one clean sentence, title
  ("Backtest evidence not yet computed") not repeated as the body's own opening clause (audit F3 fixed).

---

## Failed Tests

### UT-01 — `/backtest` page loads without errors (main pair, smoke)
**Verdict:** FAIL
**Failure:** In its literally-specified form (navigate, wait for loading to settle, open console — no
workaround), `http://localhost:3255/backtest` shows a red **"Backend unavailable"** readiness badge and a
full-width **"NO-GO — do not rely on today's board."** banner that never clears — confirmed stuck for 15+
seconds via a direct `await_element([data-state="ready"])` wait, and reproduced identically across three
separate full page navigations plus a brand-new browser tab (ruling out single-tab/single-load staleness).
The backtest-specific scorecard/leadership/evidence content never renders either (only the two error cards
show).
**Evidence:** `reports/qa/goal-ops-hardening-iter-17-evidence/UT-01-top.png` (raw failing state)

**Steps taken:**
1. Navigated to `http://localhost:3255/backtest` (repeated 3×, plus once in a brand-new tab).
2. Waited for loading to settle each time (a plain wait, then explicitly a 15-second `await_element` wait
   for the readiness badge to reach `data-state="ready"` — timed out every time).
3. Opened the console (`enable_console_logging` / `get_console_messages`) — zero uncaught errors logged;
   the failure is silent (the app's own error-handling swallows the underlying fetch failure without
   `console.error`, by design — see `lib/api.ts`'s "we never fabricate data" comment).
4. Instrumented `window.fetch` in-page to see what URL the app's own health poll was actually calling:
   `http://localhost:18255/api/health` (the THROWAWAY backend, port 18255) — from a page loaded at
   `http://localhost:3255`. Root-caused to Environment Finding 1 (see above): confirmed via `curl` CORS
   check disproof, via 5/5 successful manual same-context fetches to the correct `:8255` disproving a
   network/CORS cause, and via `/proc/<pid>/cwd` + `.next` mtime showing the two frontend dev-server
   processes share one build-output directory.

**Expected:** Page renders; heading "Backtest" (h1); "Viewing as-of `<date>` (latest)" badge; Survivorship
bias card; Forward-test scorecard + Leadership cohorts headings each above a populated table; no console
error.
**Actual:** Page renders only the nav/chrome plus two persistent "Backend unavailable" error cards (the
top-bar badge/banner, and the backtest-section's own "The backtest scorecard could not load from the API"
card); none of the expected content below that appears; no console error is logged (the failure mode is a
silently-caught fetch to the wrong port, not an exception).
**Note:** under a diagnostic `window.fetch` redirect patch (routing any `:18255` call back to `:8255` — no
file/config/service touched), the SAME page renders fully and correctly (see `UT-01-top-workaround.png` and
the PASS write-ups for UT-04/UT-05 above), demonstrating this is a session build/deployment defect, not a
regression in this iteration's product code.

---

## Skipped Tests

### UT-J-04 — J-04: Non-blocking boot with visible status (goal.md regression journey)
**Verdict:** SKIPPED
**Reason:** This iteration's own phase spec explicitly scopes J-04's re-check to "a non-disruptive
steady-state sanity check (TC-11), never a kill/restart" this session (binding OUT OF SCOPE item, matching
the same choice iter-16 made for the identical scoped check). The full 6-step journey's kill/restart/badge-
transition/log-truncation/interrupted-job steps require restarting or killing the backend, which is blocked
for this agent this session (pump note: "Do NOT kill, restart, or start ANY of the four services").

**What WAS verified non-disruptively (TC-11, matches the phase spec's own designed check for this
iteration):**
- Fresh `GET http://localhost:8255/api/health` → HTTP 200, `{"status":"ok","readiness":"ready","db_ok":true}`.
- `logs/backend.log` grew from 41,568 to 42,382 lines during this session (normal request logging) with
  **zero** new `=== start-backend.sh: launching ===`, `Shutting down`, or `Finished server process` lines —
  no crash/restart banner since the last recorded one (`2026-07-24T01:41:20Z`), satisfying TC-11's exact
  wording.
- This iteration's diff does not touch `main.py`, `app/api/health.py`, `app/engine/readiness.py`, or
  `app/engine/warmup.py` (binding "Do not redo," confirmed via the ui-surface-map's "Backend-Only Changes"
  section) — no new regression risk to J-04's own code this iteration.

**What was NOT verified this session:** the boot-phase-visible-pre-ready badge (step 3), the crash→explicit-
unreachable transition (step 4), the abrupt-log-truncation-on-kill evidence (step 5), and the mid-flight-job
→interrupted-on-restart detection (step 6) — all require a kill/restart, out of scope per the phase spec.

**Additional context surfaced this session (not part of J-04's own verdict, but relevant to how its
Acceptance — "badge... re-reads [readiness] ... never a bare 'Backend unavailable'" — is currently
observable):** Environment Finding 1 above means the badge is CURRENTLY stuck on "Backend unavailable" on
the raw (unpatched) main-pair path, live, right now — for a reason unrelated to J-04's own code (a
cross-wired frontend build, not the readiness computation). Under the same diagnostic workaround used for
UT-01/04/05, the badge correctly reflects the true "Ready" state once it can reach the right backend,
indicating the underlying readiness-computation-and-display logic J-04 cares about is intact; the
defect is in build/deployment plumbing outside J-04's own files.

**Golden replay script:** none written this round — J-04's own acceptance is fundamentally a kill/
restart/log-truncation journey that the `demo_runner.py` schema (goto/click/fill + text-expect) cannot
express, and this session verified only the non-disruptive slice (not a full PASS), so per the agent
instructions' best-effort clause this journey is left to fall back to the LLM lane next time rather than
publish a script that would misrepresent it as fully replayable.

---

## Environment

- **Frontend URL (main pair):** http://localhost:3255 (backend http://localhost:8255)
- **Frontend URL (throwaway pair, substituted host form — see Environment Finding 2):**
  http://localhost:13255 (backend http://localhost:18255)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-24
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-17-evidence/`
- **Services:** not started/stopped/restarted by this agent this session, per the operator note. A single
  small backfill job was submitted (`POST /api/data/jobs`, kind=backfill, 2025-05-29→2025-05-29) directly
  against the main backend as UT-03's substitute trigger — a normal, in-scope, offline (AG-9-compliant)
  application write, not a service-lifecycle action.

## Operator action needed (naming exactly what, per this session's own instructions)

Everything performable within this session's constraints is now done (all 6 test-plan cases + the J-04
regression executed; nothing left that doesn't require a service restart). To restore normal (unpatched)
browsing of the main pair for the NEXT session:
- Restart the main (`:3255`) and/or throwaway (`:13255`) frontend `next dev` process so they no longer share
  one `.next` build-output directory — e.g. point one of them at an already-existing isolated directory
  (`apps/frontend/.next-iter25`, `.next-alt-qa`, or `.next-verify` all already exist on disk) or a fresh one.
  A plain restart of just one process without directory isolation will not fix it durably if both are
  expected to keep running concurrently again later.
- Optionally, add `http://127.0.0.1:13255` to the throwaway backend's CORS allowlist (or standardize on the
  `localhost` host form in future dispatch notes for this pair) — Environment Finding 2, minor.
