# Iteration Summary — goal-market-compass-iter-28

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-31
**Iteration:** 28

## In plain words

**What you can do now:** See honest, mostly-complete sector labels for stocks; see why each next-session candidate was picked and why others weren't; browse the two recovered trading days with corrected numbers; trust that the incident-repair work behind those numbers has been checked live; trust that each evening's saved briefing exactly matches what's on screen and never changes once saved; see the app honestly report when an old briefing's underlying data has gone missing instead of quietly rebuilding it; and now also visit a brand-new "Market" page — reached from the sidebar — that carries every card the old dashboard had, including honest historical views of past dates.

**What changed this time:** The homepage was rebuilt into a page called "Today": it now reads top-to-bottom as a short evening briefing (market state, summary, what changed, leadership rotation, next-session focus, manifest strip), and the entire old dashboard moved, unchanged, to a new "Market" page one click away in the sidebar. Today also gained three new small badges meant to say whether the market is improving or getting worse — but they read "NA" on every date the product can currently show, because that information only gets written into brand-new saved briefings and every saved briefing so far was made before this feature existed.

**What's next:** The team plans to trigger one new saved evening briefing so the Today page's new market-direction badges finally show real words instead of "NA," and will re-run this work with a full independent check present, since the last several rounds ran a lighter check than planned.

## Headline

Today and Market pages shipped and work, but the new market-direction words show "NA" everywhere

## Direction

**Signal:** improving
**Why:** J-08 (Market page relocation) moved from failing to passing this iteration, verified live against two screenshots and a historical date. J-07 (Today page) moved from failing to partial — six of seven steps verified live, with the seventh (direction words) blocked only by the fact that no saved briefing yet carries the new field, a closable one-step gap rather than a dead end. No journey regressed and the anti-goal ledger is unchanged at 9 total, 0 unresolved.

**Trend (last 3 iters):**
- Newly passing this iter: J-08
- Newly passing in last 3 iters total: J-06 (iter-27), J-08 (iter-28)
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 1 minor (iter-27 — unauthorized as-of call minted a benign extra manifest row; resolved, no enumerated anti-goal breached)
- Iters with no journey state change: 1 of last 3 (iter-26)

**Latest evaluator reasoning:** The two pages asked for were built and they work. `/` is now a "Today" page with the six sections in the right order, and the whole old dashboard moved to a new `/market` page with nothing dropped. I checked the pictures myself and the numbers on screen match the stored numbers. But the one NEW thing this round invented — three little words that say whether the market is improving or getting worse — shows "NA" on every date the product can serve.

## What was done

- Product changes: apps/backend/app/config.py, apps/backend/app/db.py, apps/backend/app/engine/compass.py, apps/backend/app/models.py, config.yaml, docs/handoffs/trendora-next-session-manifest-v1.schema.json, apps/frontend/app/page.tsx, apps/frontend/app/market/page.tsx, apps/frontend/components/compass-state-band-card.tsx, apps/frontend/components/compass-leadership-rotation-section.tsx, apps/frontend/components/sidebar.tsx, apps/frontend/lib/api.ts
- Added `build_state_band`, a new backend producer computing three direction words (regime/stress/breadth) once at manifest-freeze time, wired into the manifest content, an additive `state_band_json` column, and the schema.
- Relocated the entire legacy dashboard (`DashboardBody` and all its cards) verbatim to a new `/market` route; `/` no longer fetches `/api/sectors`/`/api/themes` on load.
- Reordered `/`'s body into six sections (state band, summary, what-changed, leadership rotation, next-session focus, manifest strip) and renamed the sidebar entry "Dashboard" → "Today", adding a new "Market" entry after it.
- Ran targeted backend tests (54 passed in test_compass.py + test_api_compass.py; reviewer independently re-ran 179 more across related files) and a frontend `next build` verification.
- Verified 10 target/regression journeys pass browser QA (8 deterministic replay + 2 LLM browser-qa, 0 skipped).

## What's left

- Journey J-07 (The Today page answers the ten-second read) partial — direction-word badges render "NA" on all 26 stored briefings; closes with one authorized live request that mints a fresh briefing carrying the real words.
- Journey J-02 (What changed since the previous session) partial — replay golden passes but the limbs that hold it partial haven't been re-examined since iter-6.
- Journey J-03 (Plain-English summary with cited facts) partial — same as J-02, limbs not re-examined since iter-6.
- Journey J-09 (Backend fits the host) partial — memory footprint still ~3.06 GB vs a ~2.5 GB target (+16.9%), open owner question.
- No QA agent or independent auditor ran this iteration — the spec required full depth but a lean dispatch ran instead, the seventh such demotion this session, leaving no independent checker present when the protected briefings table's schema was permanently altered.
- TC-14's perf-budget addendum for the two rebuilt pages still needs a real browser-timing pass.
- `goal_gate.py`'s duplicate-journey-heading defect remains unfixed (standing framework note; must close before any GOAL_ACHIEVED certification).

## Next step

FINISH J-07 by making the three direction words actually appear: the page and its numbers are already right, only the words are missing because every saved briefing predates them. Make ONE authorized live request for a date with no saved briefing yet, so a fresh briefing freezes with the words inside, then photograph the page showing real words instead of "NA" — this permanently adds one new row to the protected briefings table, so the plan must name the exact date in advance and no other. RUN IT AT FULL DEPTH: this iteration was planned full and dispatched lean for the seventh time this session, leaving no independent auditor present when the protected table's schema changed; only the owner can add `Depth enforcement: required` to make full depth binding.

## Assumptions made

- iter-29 · goal-decomposer — Ambiguity: which date to use for the one authorized live-mint request that will make J-07's state_band words observable; goal.md doesn't name one. We chose: 2026-08-03 (has a real stored run plus a genuine prior run, carries zero manifest rows today, sits outside the incident window and the AG-9 dated-exception dates, and is well before the data frontier). Reversible: yes for the date choice itself; no for the row once minted (create-once + AG-12).
- iter-28 · goal-evaluator — Ambiguity: whether the live `ALTER TABLE ... ADD COLUMN state_band_json` on the protected `next_session_manifests` table counts as prohibited AG-18 schema drift or ordinary authorized additive work. We chose: read it as authorized and open no ledger entry — every AG-18 protection holds, and the column is appended non-destructively via the codebase's long-standing additive-column mechanism. Reversible: no for the column itself (permanent in practice); yes for the policy going forward.
- iter-28 · goal-evaluator — Ambiguity: J-08 step 4 asks for "version-1 stamps" at the frontier date, but that date's real version 1 is a legacy pre-freeze row and only versions 2-6 exist. We chose: read "version-1" as shorthand for "that date's own frozen at-ingest manifest" and promote J-08 to passing. Reversible: yes — no mutation; a literal reading would hold J-08 at partial permanently, since version 1 can never be re-minted.
- iter-28 · goal-evaluator — Ambiguity: whether J-07 step 3 is satisfied when the served direction-word field and its on-screen display honestly agree on "nothing to show" (both null/NA) — the same kind of evidence that closed J-05/J-06. We chose: hold J-07 at partial, not passing — unlike J-05/J-06 this gap is producible with one ordinary live request, not permanently unprovable. Reversible: yes — if the owner rules an honest NA on both sides satisfies step 3, J-07 becomes passing immediately.
- iter-28 · goal-decomposer — Ambiguity: whether the new `state_band` direction words should be frozen inside the immutable manifest content (like `session_delta`) or computed fresh on every read. We chose: compute and freeze it inside `build_manifest_payload`, the same single producer as `session_delta`/`narrative`, never recomputed at read. Reversible: yes — an implementation-placement call; could move to a read-time helper later with no data migration.
- iter-28 · goal-decomposer — Ambiguity: goal.md names "leadership rotation" as one of J-07's six sections but gives it no independent computation spec. We chose: treat it as a display-only filtered re-presentation of the already-served `session_delta.changes` array, not a new computed value. Reversible: yes — a scoping call with no schema impact; a future iteration could add a distinct computation without touching what shipped.
- iter-27 · goal-evaluator — Ambiguity: J-06 step 2 promises a frozen manifest is "never a 404," but removing a FRONTIER manifest's price range moves the data frontier behind its own as-of, so the route legitimately 400s instead of serving it (audit finding B3). We chose: record it as an honest residual and promote J-06 anyway, since the behavior is pre-existing, narrowed by seed-safety, and unreachable without a destructive act the safety scoping already forbids. Reversible: yes — no mutation; if the owner rules a frozen manifest must stay readable regardless, J-06 returns to partial for a bounded follow-up fix.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-28.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-28-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-market-compass-iter-28-review.md |
| Browser QA | PASS | reports/phase-goal-market-compass-iter-28-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-market-compass/iter-28/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
