# Phase goal-mcp-loop-iter-30 — UX Regression Review

**Date:** 2026-07-13

**Verdict:** UX-REGRESSION-PASS

## New Capability Discoverability

| Capability | Navigation path | Clicks from home | Label clarity | Visual feedback |
|---|---|---|---|---|
| Pre-registration registry table (`/research/registry`) | Dashboard → sidebar "Research" → "Governance & process" section → "Pre-registration registry" card | 2 (1 from `/research` itself) | Consistent with the app's existing evidence/certification vocabulary (`/evidence` already trains the user on this language); the card's one-line description spells out the effect in plain terms ("The gate refuses to certify anything that isn't here") | Loading skeleton (8 bars), contained "Backend unavailable" error card, honest "No registrations yet" empty state — all three live-verified |

Both the click count and the rendered content were independently live-verified by browser-qa-agent, not just asserted by the plan: UT-02 clicked the hub card and confirmed the destination URL and all 11 populated rows; UT-10 walked the full path from `/` through the sidebar and confirmed 2 total clicks with an unchanged 11-item sidebar. This is a genuine navigation entry, not a deep link a user would have to already know — no "hidden capability" or "undiscoverable capability" condition applies.

The "Governance & process" section heading and "Pre-registration registry" label are mildly institutional/technical phrasing, but they extend vocabulary the product already established on `/evidence` and `/research` (certification, evidence, "Backs:" links) rather than inventing a new register — not flagged as label confusion.

## Regression Risk

| Shared component touched this iteration | Prior feature(s) it serves | Nature of the touch | Risk |
|---|---|---|---|
| `apps/backend/main.py` (router table) | Every API route in the app, incl. `GET /api/evidence` behind J-01/02/03/05/06/07/08/09/11 | One new import line + one `include_router(registry.router, prefix="/api")` call beside the existing `evidence.router` line — verified via `git diff` to be a pure 2-line addition, zero lines changed or removed | Low — live-verified: UT-09 reloaded `/evidence` post-change and confirmed all 7 FAIL claims render identically with 0 console errors |
| `apps/frontend/lib/api.ts` (shared API client, imported by every data-fetching page) | All existing `fetchXxx` functions (evidence, prices, stocks, themes, sectors, labs, …) | `git diff` shows a clean 13-line addition (one new import, one re-export line, one new `fetchRegistry` function) — no existing line touched | Low — additive-only by inspection; further mitigated by UT-10's full sidebar sweep (all 11 pages load and navigate) |
| `apps/backend/app/config.py` (`EvidenceCfg`) | Every consumer of `EvidenceCfg` (the evidence ledger reader, the FDR economy, the gate) | New `RegistryCfg` class + one new `registry: RegistryCfg` field, default-populated (`enforce: bool = False` default) so any fixture predating this block still loads unchanged; the only removed lines are docstring prose being reworded to mention the new field, no logic removed | Low — `test_config.py`'s full 71 tests (68 pre-existing + 3 new) pass per the dev handoff, confirming no config-schema regression |
| `apps/frontend/app/research/page.tsx` (Research hub) | The 10-lab `RESEARCH_LABS` grid (a pre-existing fixed reading-order contract, `lib/research-labs.ts`, untouched this iteration) | A new, visually separate "Governance & process" section appended below the existing grid; the `RESEARCH_LABS` array itself is imported and rendered exactly as before | Low — UT-08 live-confirmed exactly 10 lab cards in the identical original order, with the new section appearing only afterward in its own block |

No navigation-skeleton file (sidebar/nav/layout/shell) was touched — confirmed by `git diff --stat` against the working tree (no match for `sidebar|nav|layout|shell`), consistent with the plan's explicit "No sidebar/nav-skeleton change" claim.

One gap worth naming honestly: the individual Research lab sub-pages that host J-06/07/08/09 (Factor Lab, Combination lab, etc.) were not individually reloaded with full data assertions in this iteration's browser QA pass — browser QA was explicitly scoped to "J-18 step 1 only" per the phase spec's own Testing Requirements, deferring the full J-01..J-11 replay to the deterministic-replay/evaluator step downstream. Given none of those pages' own source files were touched and the only shared dependencies they have (`lib/api.ts`, `main.py`) changed strictly additively, this is assessed as low residual risk, not a flag — but it is not independently re-verified live by this iteration's own artifacts and is worth the evaluator's deterministic replay confirming it explicitly.

## UI vs Backend Parity

| Backend capability built this iteration | UI exposure |
|---|---|
| Registry data file + `app.engine.registry` loader + `GET /api/research/registry` | Full parity — directly and verbatim rendered by `/research/registry` (confirmed single-source by dev's own test + QA) |
| Gate cross-check in `project-extensions/gates/verify_claim.py` (refuses an unregistered Evidence Claim before `verify_edge` runs) | **Intentionally no UI, by design and permanently** — this is a CLI/governance pre-check inside the automated goal-mode dev pipeline, never invoked by or reachable from the running Trendora web app. `implementation-summary.md`, `user-visible-changes.md`, and `ui-surface-map.md` all state this consistently and explicitly (not as a "not visible yet" placeholder implying future UI is owed), and the phase spec itself splits J-18's steps 2/3 out as fixture-proven, non-browser-testable. Per the agent's own rule this is an acceptable backend-only capability, not a parity gap. |
| `evidence.registry.enforce` config flag | Backend/pipeline-only; no page reads or displays it — same "permanent by design" classification as the gate itself, not a gap. |

No backend capability from this iteration is silently un-surfaced or mislabeled as complete-but-invisible. The single backend-only item is the one the coordinator explicitly flagged as structurally non-UI-able, and every artifact treats it that way rather than glossing over it.

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None.

### Potential Regressions
None. All shared-component touches (`main.py`, `lib/api.ts`, `app/config.py`, the Research hub page) are additive-only by direct diff inspection and have live or automated-test confirmation that the prior features they serve (`/evidence`, the 10-lab grid, config loading) are unaffected. See Regression Risk table for the one honestly-noted residual gap (individual lab sub-pages not individually re-loaded this iteration) — assessed low-risk, not elevated to a flag.

### Visual Consistency
- New page and hub section reuse existing `Card`/`CardContent`/`Badge`/`PageHeading` components; table markup mirrors `app/research/samples/page.tsx` precisely (same border/spacing/typography tokens: `text-sm`, `text-xs uppercase tracking-wide text-text-faint`, `border-border`, `bg-surface`/`bg-surface-2`).
- No arbitrary colors or spacing values found — frontend handoff states every class used is an existing design-system token already used elsewhere in the Research section; QA (UT-04) independently confirmed the Status/backfill badge classes are neutral tokens (`bg-surface-2`, `text-text-muted`, `text-text-faint`), not ad hoc values.
- Status badges are deliberately styled in the neutral/muted variant rather than `/evidence`'s green/red PASS/FAIL treatment — a considered choice (registry status is descriptive process state, not a proven/not-proven signal) that stays inside the design system rather than inventing a new visual language, and directly upholds the anti-goal against presenting unproven values as confident.
- Hover/focus states on the new hub card match the existing lab cards exactly; the governance grid reuses the same responsive breakpoints as the lab grid. No glow/gradient/glassmorphism introduced, consistent with the plan's own "not a marketing surface" requirement and with the calm, data-dense style of every other Research sub-page.
- No visual inconsistency found.

## Recommendation

No action required. Discoverability, regression risk, and UI/backend parity all check out cleanly, with live browser evidence (10/10 QA tests) backing the discoverability and shared-file-regression claims rather than resting on the plan's intent alone.

Non-blocking note for the downstream evaluator: confirm the deterministic replay of J-01/02/03/05/06/07/08/09/11 (the individual lab sub-pages, not just `/evidence` and the hub) as part of the standard required-still-passing sweep, since this iteration's own browser QA was correctly scoped to J-18 only and did not individually re-load those lab pages.
