# Phase goal-mcp-loop-iter-20 — UX Regression Review

**Date:** 2026-07-08

**Verdict:** UX-REGRESSION-WARN

---

## Headline finding (read this first)

Browser QA (`reports/phase-goal-mcp-loop-iter-20-ui-test-results.md`) recorded a blanket **SKIP**
(22/22) because neither service was reachable (`curl` → `000` on both `:3255` and `:8255`). That
means **zero independent verification of J-13 happened before this review** — every claim in
`user-visible-changes.md` / `ui-surface-map.md` was, until now, only a static reading of the diff.

Because this iteration's entire content is visual/UX (colors, legend, copy, one removed dropdown
option), a "the code looks right" read is not the same as "a user looking at the running app sees
it." I therefore brought both services up myself (`scripts/start-backend.sh` /
`scripts/start-frontend.sh`, the project's own canonical QA bring-up path) and drove the real
DOM with Chrome. **On the first attempt, the running app was serving the OLD, pre-iter-20 UI**:
the job-kind dropdown still had 4 options including "Expand universe", and
`[data-testid="availability-legend-density"]` / `-snapshot"` did not exist in the DOM at all.

Root cause (confirmed, not a source defect): `scripts/start-frontend.sh` only rebuilds when
`.next/BUILD_ID` is absent or its `.next/.qa-serve-base` stamp (baked backend URL+port) doesn't
match — it has **no check against frontend source freshness**. The `.next/` directory on disk was
built **2026-07-07 12:43:24**; all four iter-20 frontend edits (`page.tsx` 16:14, `heatmap.tsx`
16:37, `tailwind.config.ts` 16:11, `globals.css` **2026-07-08 00:40**) postdate that build. Since
the backend port is deterministic (sha1 of the repo path) and hadn't changed, the stamp matched
and the script served the stale bundle unconditionally, with no warning.

I forced a clean rebuild (`rm -rf apps/frontend/.next` + re-run `start-frontend.sh`, which then
printed "No usable production build ... building" and ran `next build` to completion, 0 type
errors) and re-verified against the fresh bundle. Every J-13 DoD/UI claim then checked out exactly
— see **Live verification performed** below. The application code is correct; the deployment
staleness trap is what's actually being flagged. **Both services are still running right now**,
already on the fresh, correct build, so a re-dispatched browser-qa-agent can pick this up
immediately without re-hitting the trap (see Recommendation).

---

## Live verification performed (this review, after forcing a clean rebuild)

| Check | Result |
|---|---|
| Job-kind `<select>` options | Exactly `["Backfill snapshots", "Fetch EOD prices", "Fetch + backfill"]` — no "Expand universe" |
| `availability-legend-density` / `-snapshot` | Both present; text "Price data — cell fill" / "Scored snapshot — indicator" render |
| Full-density cell computed `background-color` | `rgb(166, 200, 242)` = `#a6c8f2` (spec'd blue, not the old amber `#f0b429`) |
| Snapshot-ring cell computed ring color | `rgb(167, 139, 250)` = `#a78bfa` (spec'd violet, not the old green `#34d399`) |
| Hover readout on a ringed cell | `"2026-07-01 · 583/587 symbols · snapshot yes"`, the "snapshot yes" span computed `color: rgb(167, 139, 250)` |
| Tooltip, full-fill + no-ring cell (2026-05-04, 587/587) | `"...no snapshot yet — Backfill gap"` |
| Tooltip, ringed cell (2026-07-01, 583/587) | `"...scored snapshot exists (Backfill)"` |
| `expand-ineligible-reason` alert | Absent from the DOM |
| Panel title | `"Start a fetch / backfill job"` (no "expand") |
| Explainer copy | `"...covering the full committed symbol pool."` — zero occurrences of "Expand" |
| Backend `symbol_count` (`/api/health`) | 587 (matches the reports' "~588"; not a discrepancy) |
| J-01 regression spot-check (`/stocks`, Sector sort ×2) | Rows re-sorted correctly by sector, nav intact, no application-error text in `document.body`, "Not yet proven" visible on inspected rows (incidental J-03 corroboration) |

I did not personally replay J-05/J-10/J-12 live, or start a real Fetch/Backfill job to completion
(heavier functional checks that belong to a full browser-qa-agent pass, not a UX spot-check) — see
Regression Risk for why those are still assessed low-risk from the file-level blast radius.

---

## New Capability Discoverability

J-13 is explicitly scoped as **no new page, no new nav, no new user action** — goal.md states "no
new user-facing capability beyond clarity." Assessed against that bar:

- **Widened Fetch scope (~548-pool ∪ context, ~587 symbols)** — surfaced automatically through the
  *existing, unmodified* "X of Y symbols" counter and progress bar (`page.tsx:2446,2451`, confirmed
  untouched in the diff). No new control was needed and none was added; a user clicking the same
  "Fetch EOD prices" button they already knew simply sees a bigger denominator. Discoverability:
  **N/A by design — correctly automatic**, not hidden.
- **Two-group legend + re-tooltips** — lives on the same existing "Per-date availability" card, same
  position on `/data`. Anyone who could find the heatmap before can find it now. Discoverability:
  **1 click from Dashboard** (sidebar → Data Manager, live-confirmed), same as before iter-20.
- **"Expand universe" removal** — this is a removal, not a capability to discover; confirmed absent
  from the live DOM post-rebuild.

No new navigation entry was required and none is missing.

## Regression Risk

| Shared surface touched | Prior feature | Risk | Assessment |
|---|---|---|---|
| `app/data/page.tsx` (Expand removal, ~14 sites) | J-37 "Pull the missing data" gap-pull panel, Rebuild panel, plain Fetch/Backfill/Both controls | Low | Confirmed via source: the removed `isExpandKind`/`sourceIneligibleForExpand`/`isExpand`/`ExpandScreenResult`/`expand-ineligible-reason` identifiers have **zero remaining references** anywhere in `page.tsx` or `availability-heatmap.tsx` (grep, 0 hits). `showFetch = job.kind === "fetch" \|\| job.kind === "both"` retains exactly its two intended branches. The J-37 panel (`"Pull the missing data"`, lines ~1562-1804) and `RebuildPanel` (~line 732+) sit in untouched regions of the file. Live-confirmed: dropdown shows exactly 3 correct options. |
| `app/globals.css` / `tailwind.config.ts` (`--heat-*`, new `--snapshot`) | Any other page using these design tokens | Low | These are global token files, but `grep -rl "heat-[0-9]\|ring-snapshot\|text-snapshot"` across the whole frontend returns **only** `tailwind.config.ts` (the registration) and `availability-heatmap.tsx` (the sole consumer) — no other component references these tokens, so the color change cannot ripple elsewhere. The diff also shows `--pos`/`--neg`/`--warn` (used on `/stocks` for gain/loss coloring, and elsewhere) are **byte-unchanged**. |
| `data_manager.py` `_run_job` fresh-fetch branch | The generic Fetch/Backfill/Both job path itself; `is_expand` branch; J-37 `symbols_override` (gap-pull) branch | Low | The diff is a single `if/elif/else` structure with only the final `else` line's RHS changed (`all_seed_symbols(cfg)` → `price_load_symbols(cfg, seed_dir)`); the `is_expand` and `symbols_override` branches are textually untouched. Reviewer (`reports/reviews/goal-mcp-loop-iter-20-review.md`, PASS) independently re-verified this wiring; I independently re-confirmed the diff shape myself. |
| Sidebar / layout / router | Every page's navigation | None | `sidebar.tsx` and `layout.tsx` are not in the changed-file list (confirmed via `git status`/`git diff --stat` — only `page.tsx`, `availability-heatmap.tsx`, `globals.css`, `tailwind.config.ts` under `apps/frontend/`). Live-confirmed: sidebar still lists all 11 routes including Data Manager. |
| Required-still-passing journeys J-01/J-03/J-05/J-10/J-12 | iter-19's Sector-sort crash fix (J-01), honest "Not yet proven" (J-03), `/evidence` (J-05), deep-history chart (J-10), broad universe consistency (J-12) | Low | None of their files (`app/stocks/page.tsx`, `app/stocks/[ticker]/page.tsx`, `app/evidence/*`, `app/methodology/*`, `lib/sector-label.ts`) appear in iter-20's changed-file list. J-01 live-spot-checked in this review (sorted correctly twice, no crash, nav intact); J-03 incidentally corroborated (all inspected rows read "Not yet proven"). J-05/J-10/J-12 assessed low-risk by file non-overlap only, not independently re-run live by this review. |
| Market-cap on-demand refresh (Expand's only caller of `get_market_caps`) | The "Expand universe" job itself | **Intentional removal, not a bug** | This *is* a real loss of a previously-reachable user action, but it is the phase's explicit, spec-directed, honestly-worded choice (see UI vs Backend Parity below) — not an accidental regression. Flagged for the record, not as a defect. |

## UI vs Backend Parity

| Backend capability | UI exposure | Assessment |
|---|---|---|
| Fetch job now targets `price_load_symbols` (548-pool ∪ context) | Automatic — existing "X of Y symbols" counter/progress bar shows the larger total with no new control | Fully surfaced, live-confirmed (`symbol_count: 587` from `/api/health`, matches heatmap's `total_symbols`) |
| `compute_availability` / `GET /api/data/availability` | Unchanged endpoint, re-encoded presentation only | Byte-identical output is a backend-test-enforced invariant per the plan; not something I can verify from the UI side, but the two-group legend correctly re-labels the same fields (`symbols_with_bars`/`total_symbols`/`snapshot_exists`) — confirmed via the live tooltip text quoting exact figures. |
| `kind:"expand"` job + `get_market_caps` | **Not exposed anywhere in the UI** — deliberately. `scripts/screen_universe.py` remains the only (offline, non-UI) trigger. | Acceptable per this phase's explicit scope: goal.md directs removing the Expand UI option and requires "no `/data` copy implies caps are still on-demand-refreshable." Verified live: the "Candidate universe" tile definition reads *"The **static** screened candidate universe..."* — the word "static" is present, no on-demand/refresh claim exists anywhere I found in the page copy. This is the correct, honestly-executed version of an intentional backend-only-from-now-on capability, explicitly disclosed in `user-visible-changes.md`'s "Not Visible Yet" section. Not a parity gap to fix. |

## Flags

### Hidden Capabilities

- **The entire J-13 deliverable was inaccessible on the one running instance of the product until
  this review forced a rebuild.** Not a code defect — `git diff`/grep confirm the source is
  complete and correct — but a deployment-freshness gap in `scripts/start-frontend.sh` (see
  Headline finding). Anyone opening `http://localhost:3255/data` before my intervention today would
  have seen the pre-iter-20 UI (Expand still in the dropdown, single-hue-less rainbow legend, green
  ring) with no indication anything was stale. This is now resolved on the currently-running
  instance (fresh build confirmed at time of writing), but the underlying script gap is still there
  for the next iteration. See Recommendation.

### Undiscoverable Capabilities

- None. No new capability requires a new navigation path this iteration (by design), and the one
  automatic behavior change (wider Fetch scope) is correctly surfaced through existing, unmodified
  UI with no discovery burden on the user.

### Potential Regressions

- None found with functional impact. See Regression Risk table above — all touched shared surfaces
  (design tokens, `page.tsx`'s other job controls, the generic-fetch branch's sibling branches,
  navigation) were checked and are isolated or independently confirmed live. The one real
  behavioral loss (market-cap on-demand refresh) is an intentional, honestly-documented removal
  directed by the phase spec, not an accidental regression.
- **Verification-chain regression, not a product regression:** browser-qa-agent recorded a blanket
  SKIP this iteration (both services down at check time), so none of J-13's DoD browser criteria
  nor the J-01/J-03/J-05/J-10/J-12 replay had been independently exercised by anyone before this
  review. I closed most of that gap myself (see Live verification performed), but J-05/J-10/J-12
  remain un-replayed live this iteration.

### Visual Consistency

- **Consistent with the DESIGN SYSTEM.** Every color used is a CSS custom property defined once in
  `globals.css` and registered in `tailwind.config.ts` (`--heat-0..5`, `--heat-text-0..5`,
  `--snapshot`) — confirmed zero inline hex in either changed component, matching the project's
  stated "the ONLY place raw hex values live" convention (`globals.css`'s own header comment).
- The new blue density ramp (`#39516f → #3d6ba4 → #4d86cb → #669bdb → #83b0e7 → #a6c8f2`) has
  roughly even luminance spacing between adjacent steps (~22-26 of 255 per step, by a quick
  0.299R+0.587G+0.114B check) — a legitimate monotonic ramp, not just "not amber." The reviewer
  independently re-verified the developer's more rigorous OKLCH-ΔL/WCAG-contrast numbers
  (`reports/reviews/goal-mcp-loop-iter-20-review.md`: "2.21:1 and 6.6:1 contrast and monotonic +0.06
  min OKLab ΔL... check out"). This directly addresses the plan's stated risk of reintroducing the
  prior J-74 near-identical-buckets defect.
- The new `--snapshot` violet (`#a78bfa`) shares no hue family with the blue ramp, nor with `--pos`
  (green), `--neg` (red), or `--warn` (amber) — confirmed both by reading the hex values and by
  live computed-style checks on real rendered cells.
- Dark-theme-only styling is preserved throughout (no light-mode branch exists anywhere in this
  app, per iter-19's handoff; nothing in iter-20 introduces one).
- No new component type was introduced; the existing `Card` is reused, matching every other card on
  `/data` and consistent with prior-phase pages.

## Recommendation

1. **Re-dispatch browser-qa-agent now.** Both services are already up on a fresh, correct build as
   of this review (backend `uvicorn` pid 2051912 on `:8255`; frontend `next-server` pid 2054194 on
   `:3255`, rebuilt from current source at ~2026-07-08 with `0` type errors). A real QA pass can run
   immediately without re-hitting the staleness trap, closing the DoD's still-open "Target journey
   J-13 passes via browser-qa-agent" line item with genuine evidence instead of a blanket SKIP, and
   can additionally replay J-05/J-10/J-12 live (not personally re-verified by this review).
2. **File a process/tooling follow-up (non-blocking for this iteration):** `scripts/start-frontend.sh`'s
   staleness check (`.next/.qa-serve-base`) only compares the baked backend URL/port, never frontend
   source freshness. A `.next/` build that predates a later frontend edit is served as-is, silently.
   This iteration was saved from grading the wrong bundle only because *both* services happened to
   be fully down when browser-qa-agent checked (a full SKIP rather than a false PASS/FAIL on stale
   UI) — a partial state (e.g., frontend left running from an earlier session, backend restarted)
   would not be caught. Suggest hashing/mtime-stamping the frontend source tree into the staleness
   stamp, or unconditionally `rm -rf .next` before any QA/audit browser pass.
3. **No changes needed to the J-13 UI/UX implementation itself.** Every DoD-relevant visual and
   behavioral criterion (option count, two-group legend, color values, hover/tooltip copy, honest
   static-caps wording, `tsc --noEmit` cleanliness) checked out exactly against spec once served
   from a fresh build, both by static source audit and by live DOM/computed-style verification.

---

*Services left running for continuity: backend `uvicorn` (pid 2051912, `:8255`, logs at
`/tmp/claude-1000/-home-dennis-chan-Git-trendora/bda69735-cbd2-4764-b108-a73ea25bd966/scratchpad/backend.log`);
frontend `next start` (pid 2054194, `:3255`, fresh-build log at
`/tmp/claude-1000/-home-dennis-chan-Git-trendora/bda69735-cbd2-4764-b108-a73ea25bd966/scratchpad/frontend-rebuild.log`).*
