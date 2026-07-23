# Phase goal-ops-hardening-iter-16 — UX Regression Review

**Date:** 2026-07-23

**Verdict:** UX-REGRESSION-WARN

Non-blocking. All new capabilities are properly exposed and no regression was found anywhere this
iteration touched. The WARN is for one real, verified, minor gap (unlinked internal jargon in the
`not_yet_computed` empty-state copy, compounded by that same state never having been observed live in a
browser this session) — not for anything hidden, broken, or regressed. See Flags/Recommendation.

---

## New Capability Discoverability

This iteration's ONLY user-visible change is a 3-way status disclosure (`ready` / `refreshing` /
`not_yet_computed`) added to the EXISTING "Forward-tested evidence" section at the bottom of the EXISTING
`/backtest` page. No new page, route, nav entry, button, or control was added (confirmed: `git diff --stat`
against `apps/frontend/components/sidebar.tsx` and every other frontend file outside
`apps/frontend/app/backtest/page.tsx` / `apps/frontend/lib/api.ts` shows zero changes).

| Capability | Navigation path | Clicks from home | Label clarity | Visual feedback |
|---|---|---|---|---|
| `ready` disclosure (i.e., no banner — unchanged) | Sidebar "Backtest" (`apps/frontend/components/sidebar.tsx:37`, pre-existing, unmodified) → `/backtest`, evidence section at the bottom | 1 click | N/A — unchanged from before this iteration (regression guard, TC-12) | Confirmed live: `UT-01`/`UT-05`, no banner/empty-state text anywhere |
| `refreshing` disclosure (`RefreshingEvidenceBanner`, `data-testid="evidence-refreshing"`) | Same 1-click path; renders automatically, no extra click/toggle needed | 1 click | Clear: "Refreshing — showing the last complete evidence" plus a formatted generation timestamp, in plain language (verified live, `UT-09`: no jargon, no cache-key/function names) | Confirmed live: amber/warn `Card` + spinning `Loader2`, positioned directly above the still-fully-populated evidence section (`UT-02`), page stays interactive while it shows (`UT-09`) |
| `not_yet_computed` disclosure (reused `EmptyState`) | Same 1-click path; renders in place of the evidence section automatically | 1 click | Understandable core message ("Backtest evidence not yet computed") but the call-to-action clause names an action with no in-app label match — see Flags | **Not yet observed live** — proven only by 10/10 unit tests in `test_forward_testing_serving_split.py` (`UT-03` SKIPPED, justified: this DB is fully warmed, reaching this state non-destructively would require deleting `ForwardAggregateCache` rows) |

All three states are reachable in exactly **1 click** from the home/dashboard page (`/`) via the persistent
"Backtest" sidebar entry (unchanged this iteration) — well inside the "≤2 clicks" bar, and in fact the
disclosure itself requires **zero additional clicks**: it is not gated behind a tab, toggle, or button: it
renders automatically as part of the page's existing content the moment `/backtest` loads. This matches
the phase spec's own framing ("New user actions: none — a read-only status disclosure only") and is a
textbook case of a new capability piggy-backing cleanly on an already-discoverable surface rather than
requiring any new navigation.

**Visual Design System compliance** (independently verified by reading source, not just trusting the dev/
frontend handoffs' self-report):
- `RefreshingEvidenceBanner` (`apps/frontend/app/backtest/page.tsx`, new) uses
  `className="flex items-start gap-3 border-warn bg-surface p-4 text-sm"` — **byte-identical** to the
  existing `SurvivorshipBanner` component's own `Card` className on the same page (`page.tsx:167`), plus
  `text-warn` on its heading/icon and `text-text-muted` on its body copy, exactly mirroring
  `SurvivorshipBanner`'s existing convention. `--warn` resolves to a real design-system CSS variable
  (`apps/frontend/tailwind.config.ts:24`, `warn: "var(--warn)"`), not an arbitrary hex value.
- The `not_yet_computed` state reuses the project's existing `EmptyState` component
  (`apps/frontend/components/empty-state.tsx`) via its standard `icon`/`title`/`description` props — the
  SAME component and prop shape already used elsewhere on this same page (`ScorecardSection`'s own
  no-data state, `page.tsx:521`). No new empty-state visual pattern was invented.
- Confirms the goal.md Design Direction ("Evidence status is calm and unmissable, never hype... status/
  health/job surfaces read like the existing preflight banner — calm, factual") was followed, not just
  cited: `UT-09` independently confirmed the banner's amber (not red/danger) tone and plain-language copy
  live in a browser.

Conclusion: discoverability and visual consistency are both excellent for this iteration's new capability.
No "hidden capability," "undiscoverable capability," or "visual inconsistency" flag applies to the
`ready`/`refreshing` states. One minor, concrete "label confusion" issue applies to the `not_yet_computed`
state's copy — see Flags.

---

## Regression Risk

Per the `ui-regression-scout` skill's method: prior-phase features whose components this iteration's
`ui-surface-map.md` touches. This iteration's diff footprint is unusually narrow (confirmed directly via
`git diff`, not only by reading the handoffs), which sharply limits the actual regression surface versus
what the file list alone might suggest.

| Shared component | Prior feature it serves | This iteration's change to it | Regression risk |
|---|---|---|---|
| `_refresh_ingest_aggregates`'s per-horizon warm loop, `data_manager.py:3230` | **J-05 — "Aggregates are precomputed at ingest, never on the fly"** (built iter-2 of this session; hardened iter-3/4/7/8) — the exact finalize hook every backfill/fetch job in **J-01** ("Backfill honors the requested range") and **J-03** ("No per-run range cap") triggers on completion | One-line call-site rename only: `forward_testing.forward_aggregates_cached(...)` → `forward_testing.forward_aggregates_ingest_cached(...)` (`git diff` confirms this is the ONLY functional line changed in this file; the surrounding loop, `MemoryError` isolation, and trigger are byte-identical before/after) | **High-risk component, verified low residual risk.** This is the single most consequential shared code in the whole diff — three Must-have journeys' ingest path funnels through it. It was independently confirmed safe by three separate evidentiary layers this iteration: (1) 24/24 targeted unit tests green including the `MemoryError`-isolation tests for this exact loop; (2) golden-script regression replay of J-01/J-03/J-05 all PASS (`UT-J-01`/`UT-J-03`/`UT-J-05`); (3) a REAL, live, production-scale ingest job during the TC-16 operator pass (`reports/perf-budgets.md`) completed `status="ok"` with `aggregates_refreshed` including `forward_aggregates`, confirmed by direct `logs/backend.log` cross-read. |
| `GET /api/backtest` response shape / `BacktestResponse` TS interface | **J-07 — "Heavy aggregates never take the service down"** (iter-14/15) and **J-06** (this endpoint's own ≤1.5s budget) | Strictly additive: 2 new fields (`evidence_status`, `evidence_generated_at`) appended to the interface (`apps/frontend/lib/api.ts` diff: `+10/-0` lines, zero removed/renamed fields); `evidence_by_horizon`'s pre-existing shape is unchanged in the `ready`/`refreshing` states (only becomes `{}` in the new `not_yet_computed` state, which — per a direct grep — is the ONLY frontend consumer of `BacktestResponse` in the entire codebase, i.e. no other page/component could be broken by this addition) | **Low.** Byte-identity proven (TC-9); browser QA `UT-05`/`UT-10` independently confirm the `ready` path's sub-panels and API shape are unchanged. |
| MCP `query_backtest` tool | Existing AI-agent/MCP consumer surface (non-browser; pre-existing pattern, not new to this iteration) | Mirrors the same 2 new fields | **Low** — no browser page depends on this tool; this is an established non-UI channel in this codebase (multiple prior iterations' MCP tools follow the same "mirrors the endpoint, no dedicated page" convention). |
| Sidebar navigation (`apps/frontend/components/sidebar.tsx`) | Every page's reachability, including all of J-01 through J-08's homes | **None** — confirmed via `git diff --stat`: zero changes to this file this iteration | **None.** |
| Boot/readiness/health (`main.py`, `app/api/health.py`, `app/engine/readiness.py`, `app/engine/warmup.py`) and launch scripts (`scripts/start-backend.sh`, `scripts/dev.sh`) | **J-04 — "Non-blocking boot with visible status"**; the global readiness badge (every page); AG-10's host-guard caps | **None** — confirmed via `git diff --stat`: zero changes to any of these 6 files this iteration (independently verified, not only cited from the phase spec's "OUT OF SCOPE"/"Do not redo" list) | **None.** (J-04 itself was correctly SKIPPED in browser QA rather than falsely asserted PASS, since verifying it requires a restart+kill this session's operational constraints blocked — but the SKIP carries no regression risk precisely because this code is untouched.) |
| `/backtest`'s OTHER sections: `SurvivorshipBanner`, `WarmingState`, `AsOfScanSummary`, `ScorecardSection`, `ReturnAttributionSection`, the 3 leadership lists | Various pre-existing journeys/capabilities on this same page (predates this session — code comments reference `J-09/J-10/J-16/J-28`, i.e. an earlier goal session) | **None** — the `page.tsx` diff (`git diff`) shows the touched block starts exactly at the `{evidence ? (...) : null}` line and ends before `AsOfScanSummary`; every other function in the file is untouched in the diff | **None.** Independently confirmed live: `UT-06` shows the Survivorship card, Market Regime, Candidate Counts, Scorecard, Return Attribution, and all three leadership cohort lists rendering identically to the `ready`-state capture while the evidence section below shows `refreshing` — no leakage, no skeleton, no error. |
| Historical (`?as_of=`) time-machine viewing | The pre-existing time-machine capability (goal.md Non-Goals explicitly protects this from being "rewritten") | **None** — explicitly out of scope this iteration; confirmed unchanged both by a unit test (TC-13) and live browser observation (`UT-07`) | **None from this iteration.** Worth flagging for awareness, not as a regression: `UT-07`'s live measurement found a historical date's FIRST view now takes **≈83 seconds** (2026-07-14, clean measurement) — well beyond the test plan's expectation of "a few seconds." This is NOT caused by this iteration (the lazy create-once-and-cache code path is byte-unchanged, confirmed by the diff) and is explicitly called out in the phase's own BACKGROUND section as a natural consequence of the growing deep basis, not a new defect — but it is a real, user-facing latency the product has not addressed, and it sits right next to this iteration's OWN performance-honesty work. Recommend a future iteration/decomposer pass pick this up explicitly (it is currently only visible in the browser-qa transcript, not in any user-facing changelog). |

**Summary:** every component this iteration touches was independently verified (via `git diff`, not only
by reading self-reported handoffs) to be either (a) a narrowly-scoped, verified-safe change, or (b)
completely untouched. No potential regression rises above "verified low risk" for any prior journey.

---

## UI vs Backend Parity

| Backend capability (this iteration) | Surfaced in UI? | Where |
|---|---|---|
| `evidence_status` on `GET /api/backtest` (`ready`/`refreshing`/`not_yet_computed`) | **Yes** | `/backtest` evidence section — all 3 states render distinctly (2 of 3 confirmed live: `UT-01/02/04/05/09/10`; 1 of 3, `not_yet_computed`, confirmed only at the unit-test layer, `UT-03` SKIPPED — see Flags) |
| `evidence_generated_at` on the same endpoint | **Yes** | Printed inline in the `refreshing` banner (confirmed live, `UT-02`/`UT-10`: byte-identical to the pre-backfill value); implicitly represented by the `ready` state's unchanged, already-current data |
| Same 2 fields on MCP `query_backtest` | **No browser surface — by design, not a gap.** MCP tools in this codebase are consumed by AI-agent/Model-Context-Protocol clients, not the Next.js frontend; there is no page for any MCP tool anywhere in this app (an established, pre-existing pattern, not something iter-16 introduced). Appropriately documented as "Not Visible Yet" in `user-visible-changes.md` rather than omitted. |
| Completeness/cutover pruning logic, single-flight-guard-survives-the-split, `asof_key`-filtered completeness query (TC-4/5/17/18) | **No UI surface, and none is warranted.** These are internal correctness guarantees a user experiences only THROUGH the `evidence_status` label being correct — there is no separate "cutover" concept a user needs to see. Not a parity gap. |
| The 4 sibling ingest-time caches (event-study, market-phase, drawdown-expectations, index-series) | **Intentionally out of scope this iteration** — they keep their pre-existing lazy-warm-and-self-heal behavior with no equivalent status disclosure. This is explicitly logged in both the phase spec's OUT OF SCOPE section and `user-visible-changes.md`'s "Not Visible Yet," so it is a disclosed, deliberate scoping decision, not a silent gap. Noted below under Visual Consistency as a cross-page asymmetry worth a future look, not a defect of this iteration. |

Parity verdict: complete for the one browser-facing surface this iteration targets. The MCP-only and
"other 4 caches" non-surfacing are both intentional and honestly disclosed, matching the "acceptable if
disclosed" carve-out in this reviewer's own instructions.

---

## Flags

### Hidden Capabilities
None. All three `evidence_status` states render inline, automatically, on the already-1-click-reachable
`/backtest` page — none require a separate control, toggle, or undocumented route.

### Undiscoverable Capabilities
None requiring >2 clicks or obscure navigation. (See the one related, but distinct, "label confusion"
item below — that is about copy clarity once the state IS showing, not about finding the feature.)

### Potential Regressions
None found. See the Regression Risk table above for the full component-by-component verification
(including the one genuinely high-risk shared component, the ingest finalize-warm call site, which was
verified safe by three independent evidence layers this iteration).

### Label Confusion
- **`not_yet_computed` empty-state copy uses "ingest" — a term that appears NOWHERE else as user-facing
  copy in this entire frontend.** The new string (`apps/frontend/app/backtest/page.tsx:239`): *"Backtest
  evidence not yet computed — run an ingest to populate the forward-tested evidence for this date."*
  Verified by direct grep across `apps/frontend/app` and `apps/frontend/components` for JSX string
  literals containing "ingest" (case-insensitive): **this is the only hit in the whole frontend.** The
  page this message implicitly points a user to, `/data` ("Data Manager" in the sidebar), never uses the
  word "ingest" in its own visible copy either — its actual job-kind labels are "Backfill snapshots" /
  "Fetch EOD prices" / "Fetch + backfill" (`apps/frontend/app/data/page.tsx:2303-2305`). A non-technical
  user reading "run an ingest" has no in-app label to match it to, and the message does not name the
  target page ("Data Manager") or point to it with a link. This is a genuine, if minor, gap in the sense
  the reviewer's own rubric asks about ("Is its label clear to a non-technical user?") — not a broken or
  hidden feature, just internal jargon leaking into the one piece of user-facing copy this iteration adds
  that names an action rather than only a status. (Note: the phase spec explicitly scopes OUT adding any
  new button/link here — "New user actions: none" — so a literal fix would need a small copy edit, e.g.
  "run a Backfill or Fetch job on the Data Manager page," not a new control.)
- This is compounded (not independently, but worth naming together) by the fact that **this exact state
  has never been observed rendering in a live browser this iteration** — `UT-03` was SKIPPED (justified:
  the working DB has complete evidence for every `asof_key`, and manufacturing this state would require
  destructively deleting cache rows, correctly avoided). The state is proven correct at the unit-test layer
  (10/10 in `test_forward_testing_serving_split.py`) and the component itself (`EmptyState`) is a simple,
  static, already-elsewhere-used piece of markup with no dynamic layout risk — so this is a low-severity
  verification gap, not a functional concern — but it means the exact wording above has not been eyeballed
  for line-wrapping/emphasis/legibility in situ, only read in source.

### Visual Consistency
- The new `RefreshingEvidenceBanner` and the reused `EmptyState` call both match the established
  DESIGN SYSTEM and this page's own prior conventions exactly (see "New Capability Discoverability" above
  for the byte-level comparison against `SurvivorshipBanner` and `ScorecardSection`'s own `EmptyState`
  call). No arbitrary hex/pixel values were introduced; no new spacing/typography scale was invented.
- Minor, non-blocking cross-page asymmetry worth tracking (not a defect of this iteration, and explicitly
  out of scope for it): `/backtest` now has a distinctly more informative "is this data fresh?" disclosure
  than the four sibling ingest-time-cached views (Event Study, Market Phase, `/evidence`'s drawdown-
  expectations panel, the dashboard/Data Manager index-series chart), which still silently show whatever
  is cached with no status label. A user who learns to trust `/backtest`'s honest labeling may reasonably
  expect the same elsewhere. This is fully disclosed already in `user-visible-changes.md`'s "Not Visible
  Yet" section and the phase spec's OUT OF SCOPE list, so it is not a hidden gap — just flagged here per
  this reviewer's own remit to note product-surface asymmetry.

---

## Recommendation

No blocking action required — this iteration may proceed/close on its own technical merits (that
judgment belongs to the evaluator/auditor, not this review). Two small, non-blocking follow-ups worth
picking up, either as a fast-follow inside this iteration if still open, or as a queued item:

1. **Reword the `not_yet_computed` empty-state's call-to-action** to name the actual in-app affordance
   instead of the internal term "ingest" — e.g. "...run a Backfill or Fetch job on the Data Manager page
   to populate the forward-tested evidence for this date." A copy-only change (no new control needed, per
   the spec's own "no new buttons/forms" constraint).
2. **Get one live-browser look at the `not_yet_computed` state** before or shortly after this closes — e.g.
   the next time a throwaway/fresh-seed backend is available, or via a deliberately-scoped, reviewer-
   approved destructive test against a disposable DB copy (never the live working DB). Low urgency: the
   component is simple, already proven elsewhere, and unit-tested 10/10, but it is the one state in this
   iteration's entire deliverable with zero live-rendering evidence.

Non-blocking awareness item (pre-existing, not this iteration's regression, not this iteration's scope):
the historical as-of first-view compute now measures ≈83s live (`UT-07`), well past the "a few seconds"
the test plan assumed — worth a future decomposer look given the deep basis will keep growing, but
explicitly confirmed unrelated to and unchanged by this iteration's diff.
