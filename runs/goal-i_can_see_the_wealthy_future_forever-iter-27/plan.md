# goal-i_can_see_the_wealthy_future_forever-iter-27 Execution Plan

> **Capture-only iteration.** The build is DONE and committed at HEAD `77d0816`
> (`git diff --stat HEAD -- apps/ config.yaml` is empty). The ONLY missing work is
> wiring the browser-QA harness to the throwaway fixture DB + the env-gated offline
> `seed` import source so the four target flows are *reachable* and can be captured.
> This has failed identically across iters 23/24/25/26 for one reason: the dedicated
> browser-qa-agent ran against the LIVE host with the seed env flags unset, so no
> insufficient member, no resumable checkpoint, and no `seed` source existed. **Fix
> the harness wiring, not the code.**

## What to Build
- **No new code is expected.** Convert J-37, J-38, J-39, J-35 from `partial` to `passing` by
  capturing each defining multi-step flow end-to-end against the fixture DB.
- **Harness wiring (the actual deliverable):** build the fixture DB, boot the backend with the
  three printed env values, clear the `.next` dead-shell, then drive the four flows in the browser.
- **Conditional, minimal fix only:** apply a backend/frontend fix ONLY if a capture surfaces a
  genuine defect (gap-pull scope wider than diagnosed shortfall; Resume not continuing from
  `next_chunk_index`; a new error string leaking a key; a failed Resume silently dropping the row;
  a result panel not rendering passers/omitted/grown-count). Any fix goes on the existing canonical
  path (J-34 engine / `screen_reasons` / redacted-URL+scrub / existing `/data` `page.tsx` components)
  with a regression test — never a second fetch/screen/compute path, no new date state, no new
  page/route/nav/endpoint/Data-Contract value.

## Agents Required
- backend-data: yes -- harness wiring ONLY (run `build_qa_fixture_db.py`, boot backend with its
  three printed env values). Write production source ONLY if a capture exposes a real defect, on the
  canonical path, with a regression test. Write the dev handoff with the exact recipe.
- frontend-ux: no (conditional) -- no production frontend change expected; the J-38 ResumeControl
  `resume-error` alert fix is already at HEAD. Touch `/data` `page.tsx` ONLY if a capture exposes a
  real UX defect on a target flow.

## Frontend Present
yes

## Files to Create/Modify
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-27-dev.md` -- **(must create)** the
  exact fixture-build + env-export + clean-boot recipe so QA wires to the fixture, not the live host.
- `runs/goal-i_can_see_the_wealthy_future_forever-iter-27/status.json` -- iteration status (PHASE-namespace path).
- *(conditional, only if a capture finds a defect)* `apps/backend/app/engine/data_manager.py` OR
  `apps/frontend/app/data/page.tsx` -- minimal canonical-path fix + a regression test in the
  matching `apps/backend/tests/test_*.py`. **Expected: none of these change.**

## Harness Recipe (backend-data MUST document this verbatim in the handoff; QA MUST follow it)
1. **Stop strays BY PORT only** — backend :8835 region, frontend :3835 region. NEVER broad
   `pkill -f "next dev"` / `"uvicorn"` (shared machine — MEMORY `dev-server-cleanup-by-port`).
2. `rm -rf apps/frontend/.next` (clears the prod-build dead shell — MEMORY `browser-qa-dead-shell-next-cache`).
3. `cd apps/backend && .venv/bin/python scripts/build_qa_fixture_db.py` — it prints a final JSON line
   whose `env` block carries `TRENDORA_ENABLE_SEED_IMPORT_SOURCE=1`, `TRENDORA_CONFIG=<out>/config.yaml`,
   `TRENDORA_SEED_IMPORT_DIR=<out>/seed_overlay`. The fixture narrows the universe to ANET/DELL/MU/AMD
   so the diagnostic renders all three categories (no-history ANET, thin DELL, intra-series-gap MU) and
   seeds a `market_caps.csv` so a `seed` expand can screen. It NEVER mutates the committed seed tree.
4. **Export those three env values and (re)start the backend with them.**
5. Restart `next dev`; confirm `_next/static/chunks/main-app.js` returns 200 AND the "Checking backend…"
   health badge has cleared BEFORE any UI capture. A dead-shell/down-server result is SKIPPED
   (environmental) → **re-wire**, do not accept the partials.
6. Before driving any expand/pull, **assert the `seed` source is present in the import picker** — its
   absence means the env flag did not reach the running backend (re-wire).

## UI Evolution
- New user-facing capability: **None new.** This converts already-built capabilities from `partial`
  to `passing` by demonstrating them end-to-end on the existing `/data` (Data Manager) page.
- New information displayed: **None new** — exercises already-registered values against fixture data
  (J-37 three-category diagnostic with exact shortfalls; J-38 Unfinished-imports + Resume-success
  state; J-39 confirm-preview removable-vs-protected-seed breakdown; J-35 expand passers / omitted-
  with-reason / grown universe count).
- New user actions: **None new** — exercised: "Pull the missing data" / "Pull all missing" (J-37);
  Resume / Retry / Remove-Dismiss (J-38); Remove-data Preview → confirm (J-39, confirm on fixture
  only); select the `seed` source → start Expand (J-35).
- UI surface changes: **None** — all four flows live on the EXISTING `/data` page (Coverage panel +
  Missing-data diagnostic, Unfinished-imports panel, Remove-data form, Import source picker + expand).
- Navigation changes: **none** (no nav-skeleton change; no `blueprint.reapproval-requested` marker —
  confirmed absent).

## Visual Requirements
- Component patterns: existing `/data` components only (Coverage table, Missing-data diagnostic rows
  with per-row "Pull the missing data", Unfinished-imports list with Resume/Retry/Remove, Remove-data
  confirm-preview, Import source picker + expand controls). Add no new components.
- Layout: unchanged — the existing `/data` page under the persistent sidebar.
- Key visual effects: none new; preserve the existing dense dark analytical treatment.
- States to handle (must render honestly, never fabricated): J-38 needs-key Resume-without-key →
  backend 400 → visible inline `role="alert" data-testid="resume-error"`, **row retained**; wholly-
  seed Remove scope → **refused with an explicit reason**; provider failure on pull/expand → explicit
  error / rate-limited state, **no fabricated bar**.

## Key Test Scenarios (Definition of Done — all four must capture green, nothing may regress)
- **J-37:** against the fixture, the three diagnostic categories render with exact shortfalls; a
  gap-exact pull over the `seed` source runs to completion with the job's `symbols + [start,end]`
  == the diagnosed gap (NOT the whole universe/window) → the row clears and J-36 coverage updates.
- **J-38:** a SEEDED resumable `seed`-source checkpoint is Resumed SUCCESSFULLY, continuing from
  `next_chunk_index` (**distinct before/after sha** screenshots) AND the UT-11 fix is shown
  (needs-key Resume-without-key → 400 → visible inline `resume-error` alert → row stays).
- **J-39:** the Remove-data confirm-preview enumerates removable user-added bars + range + protected
  committed-seed breakdown + dependent cascade (**PREVIEW path on the live host**); a wholly-seed
  scope is refused with an explicit reason; the destructive confirm + whole-row cascade (no in-place
  overwrite) is demonstrated **ONLY against the throwaway fixture DB**, NEVER on a real live symbol
  (MEMORY `j39-live-host-has-user-added-nvda-bars`).
- **J-35:** a `seed`-source Expand runs end-to-end → passers + omitted-with-reason list → grown
  universe count, with `/methodology` resolved size matching `/api/data` `universe_count`.
- **Required-still-passing (must stay green):**
  - **J-18** (flagged watch risk): DOM `querySelectorAll('select, input[type=date]')` shows exactly
    ONE global as-of `<select>` per page — the seed source / expand / pull / resume controls add ZERO
    new date state; job/action date inputs are job parameters, not a second date control.
  - **J-33** (key-leak scrub): grep the **job-status response** `GET /api/data/jobs/{id}` `errors[]`
    AND the job card AND run history on every new pull/retry/resume/expand error string — sentinel +
    `?token=`/`?apikey=` absent (real-httpx assertion; MEMORY `httpx-error-leaks-url-query-key`).
  - **J-17, J-34, J-36, J-08** (Dismiss/Remove drops only job-control; audit + immutable rows
    preserved), **J-06 / J-07 / J-15** (scoring/snapshot path git-untouched, no DB regen, byte-identical).
- **Regression suite:** existing 610-green pytest stays green — run pytest **ONCE** (full suite ~14 min,
  never two concurrent invocations — MEMORY `backend-test-suite-runtime`). Add a regression test ONLY
  if a capture surfaces a genuine defect.
- **Evidence hygiene:** all screenshots **sha256-deduped** — NO blank/dark or byte-identical
  before/after frames (the iter-25/26 blemish must not recur); every before/after claim rests on
  distinct hydrated shots + a DOM/network assertion.

## Out of Scope / Scope-Creep Guards (excluded)
- Any production code change to the scoring/scanner/regime/patterns/buckets/forward_testing/research/
  snapshot_serving engines or the `/stocks`·`/backtest`·`/research` pages or the as-of provider/sidebar
  (a `git status` over these MUST stay EMPTY → no DB regen).
- Re-probing **J-22 / J-23 / J-24** (externally Yahoo-429 data-walled; NON-HALTING / NON-VETOING per
  goal.md 994–1012). Do NOT autonomously retry a live bulk/intraday/market-cap fetch. The seed-source
  captures are OFFLINE and are NOT a live re-probe.
- Any NEW page, route, nav entry, endpoint, or Data-Contract value.
- Committing the `seed` source into the production `config.yaml` catalog, or enabling it by default —
  it stays env-gated and OFF in production.
- Running the destructive J-39 confirm against any real live symbol — destructive confirm + cascade is
  proven ONLY against the throwaway fixture DB; the live host uses the non-destructive PREVIEW path only.
