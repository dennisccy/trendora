# Phase goal-mcp-loop-iter-32 — UX Regression Review

**Date:** 2026-07-14

**Verdict:** UX-REGRESSION-PASS

---

## Summary

This iteration ships one new read-only surface (`/research/budget`, J-17 / backlog B-903) plus a
third card in the existing Research "Governance & process" grid, and re-verifies (with no code
change) J-19's graveyard→registry lineage-scroll fix. Every claim in `user-visible-changes.md` and
`ui-surface-map.md` was independently checked against the actual source diff (`git diff HEAD`) and
the browser-qa evidence, not taken on faith. All changes to shared components (`app/research/page.tsx`,
`lib/api.ts`, `main.py`) are strictly additive — new lines appended, zero existing lines touched — so
regression risk to the iter-30/31 registry and graveyard journeys is low, and the browser-qa results
confirm those journeys still pass. No hidden or undiscoverable capability was found.

---

## New Capability Discoverability

| Capability | Nav path | Clicks from home | Label clarity | Visual feedback |
|---|---|---|---|---|
| J-17 — Certification-budget accounting panel (`/research/budget`) | Sidebar "Research" (`components/sidebar.tsx:38`, pre-existing, unmodified this iteration) → `/research` → "Certification-budget accounting" card in the `data-testid="research-governance"` grid → `/research/budget` | 2 (verified both in the source diff and independently in `ui-test-results.md` UT-04: sidebar click → `/research`, card click → `/research/budget`) | Clear: "Certification-budget accounting" + a one-line description ("Total trials, the current canonical bar, the Thresholdout budget remaining, and the staging LORD++ wealth — each over time…") sits directly on the card. The vocabulary (Bonferroni, LORD++, Thresholdout) is domain-specific, but it matches the established voice of the two sibling cards ("Pre-registration registry", "Negative-results graveyard") already shipped in iter-30/31 — not a new drop in clarity for this product's evidence-first quant audience. | Loading skeleton (`budget-skeleton`, 4 pulsing placeholders) → populated 4-card grid (`budget-grid`) with sparklines; a distinct red-bordered "Backend unavailable" card on API failure. All three states independently confirmed rendering in `ui-test-results.md` (UT-01, UT-09, UT-10). |
| J-19 — graveyard→registry lineage scroll (re-verification only, no code change this iteration) | `/research/graveyard` → click a row's "Lineage →" link → lands on `/research/registry#registration-<id>` with the target row scrolled into view | N/A (existing journey, not new this iteration) | N/A | Confirmed via UT-11: `window.scrollY = 154` (>0) and the target row's bounding rect sits just below the sticky header — the described fix, not the described "broken" (scrollY=0) behavior. |

Both are reachable well within the 2-click bar and neither required developer knowledge to find —
the card is a first-class grid entry on the Research hub, not a URL-only or query-param-gated route.

---

## Regression Risk

| Shared component | Prior feature(s) it serves | This iteration's change | Verified risk |
|---|---|---|---|
| `apps/frontend/app/research/page.tsx` | iter-30 registry card, iter-31 graveyard card (both live in the `research-governance` grid this file renders) | `git diff HEAD` shows a single new `<Link>` block appended after the graveyard card, plus a `Wallet` import and a comment-only header update. The two existing `<Link>` blocks (registry, graveyard) are byte-identical to their pre-iteration state — not touched. | **Low.** Purely additive; confirmed at the diff level, not just via the dev handoff's description. Browser QA UT-02 independently confirms the DOM still shows exactly `research-governance-link-registry`, `-graveyard`, `-budget` in that order. |
| `apps/frontend/lib/api.ts` | Every prior fetch helper (`fetchEvidence`, `fetchRegistry`, `fetchGraveyard`, etc.) | `git diff HEAD` shows one new import, one new type re-export line, and one new `fetchBudget()` function appended after `fetchGraveyard`. No existing function body or export was edited. | **Low.** Additive-only; independently confirmed via diff. |
| `apps/backend/main.py` | Router wiring for every prior `/api/*` surface | `git diff HEAD` shows one new import (`budget`, alphabetically placed) and one new `include_router(budget.router, prefix="/api")` line, appended after the existing `graveyard.router` line. No existing route line touched. | **Low.** Additive-only; independently confirmed via diff. |
| `apps/frontend/app/research/registry/page.tsx` | J-19's lineage-scroll `useEffect` fix (added iter-31), J-18's registry table (added iter-30) | **Not touched this iteration** — absent from `git status --short` and from both dev/frontend handoffs' "Files Changed" lists. | **Low / re-verified.** This is the file the iter-31/22/20/13 "partial-trap" lesson warns about: a fix here is only credited once a *canonical* browser-qa-agent run confirms it against the current build, not an auditor self-check. That re-run happened this iteration (UT-11, UT-12) with concrete before/after evidence (scrollY, bounding-rect values), which is the DoD-named lane, not a substitute. |

No route, sidebar entry, or auth/permission middleware was touched this iteration (confirmed: the
only frontend files in `git status` are `app/research/page.tsx`, `lib/api.ts`, plus the wholly new
`app/research/budget/` directory and `lib/budget.ts`). The persistent sidebar's "Research" entry
(`components/sidebar.tsx:38`) is unmodified, so every pre-existing route reachable through it remains
reachable exactly as before.

**Required-still-passing journeys** (J-18, J-05, J-11, J-01, J-06, J-08, J-09 per the phase spec) —
`ui-test-results.md` reports live re-verification for J-18 (UT-12: 5 columns, 11 rows, `ma_stack`
"closed"), J-05/06/08/09 (UT-13: 7 evidence claim rows, all FAIL, byte-matched to the ledger), and
J-01 (UT-14: 541-row leaderboard, 3 "Not yet proven" badges per row, no crash). J-11 has no browser
test entry in this iteration's results table; nothing in the diff touches any surface J-11 would
plausibly depend on, so this is a scope gap in the QA report rather than a UI-side regression signal —
noted for completeness, not something this review can independently confirm or deny without a
browser session of its own.

---

## UI vs Backend Parity

The new backend module (`apps/backend/app/engine/budget_accounting.py`, read directly) returns:

- `canonical`: `n_trials_to_date`, `n_trials_next`, `alpha_per_test`, `required_p`,
  `alpha_budget_total`, `alpha_spent`, `alpha_budget_remaining`, `spend_over_time[]` (each point:
  `trial`, `register_date`, `status`, `required_p`, `deflation_divisor`, `alpha_charged`)
- `staging`: `n_trials_to_date`, `n_trials_next`, `next_level`, `spend_over_time[]` (each point:
  `trial`, `register_date`, `status`, `required_p`)

Cross-checked field-by-field against `apps/frontend/app/research/budget/page.tsx` (read directly):

| Backend field | Surfaced in UI? | Where |
|---|---|---|
| `canonical.n_trials_to_date` | Yes | "Total trials to date" headline |
| `canonical.n_trials_next` | Yes | Trials-card subtext + required-p formula denominator |
| `canonical.alpha_per_test` | Yes | Required-p formula numerator |
| `canonical.required_p` | Yes | "Current canonical required p" headline |
| `canonical.alpha_budget_total` / `.alpha_spent` / `.alpha_budget_remaining` | Yes | "Thresholdout budget remaining" headline + subtext |
| `canonical.spend_over_time[].trial` | Yes | Trials-card sparkline |
| `canonical.spend_over_time[].required_p` | Yes | Required-p-card sparkline |
| `canonical.spend_over_time[].alpha_charged` | Yes | Thresholdout-card sparkline (spend-event view) |
| `staging.next_level` | Yes | "Staging LORD++ next-trial level" headline |
| `staging.n_trials_next` | Yes | Staging-card subtext |
| `staging.spend_over_time[].required_p` | Yes | Staging-card sparkline |
| `canonical.spend_over_time[].deflation_divisor`, `.register_date`, `.status`; `staging.n_trials_to_date` | **Not individually rendered** | See note below |

**Note on the unrendered sub-fields:** these are not separate capabilities left dark — they are
minor fields of the one capability ("spend-over-time trend per figure") that the spec explicitly
scoped as "a compact per-metric mini-trend... not a primary interactive chart" (plan, Visual
Requirements). `deflation_divisor` is redundant with the trials sparkline's own ordinal for the
canonical series; `staging.n_trials_to_date` is one arithmetic step from the already-shown
`n_trials_next`. This is a reasonable minimalism choice consistent with the anti-badge, descriptive-
only framing (no verdict/status display keeps the page from reading as a second evidence table), not
an omission a user would notice as missing functionality. Not flagged as a gap.

`user-visible-changes.md`'s "Not Visible Yet: None" claim holds up under this direct
field-by-field check — every headline figure the backend computes has a UI consumer, and the one new
endpoint (`GET /api/research/budget`) has exactly one consumer (`fetchBudget` → `/research/budget`),
confirmed via the frontend handoff's grep and consistent with what `git status` shows changed.

---

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None.

### Potential Regressions
None found. All three shared-component touches (`app/research/page.tsx`, `lib/api.ts`, `main.py`)
are strictly additive at the diff level (verified directly, not inferred from the handoffs), and the
one file central to a prior journey's fix (`registry/page.tsx`, J-19) was not touched and was
independently re-verified live by the canonical browser-qa lane this iteration (UT-11), closing out
the iter-31/22/20/13 "partial-trap" risk rather than leaving it open.

### Visual Consistency
- The new `/research/budget` page reuses `PageHeading` + `Card`/`CardContent` and the exact
  `border-neg bg-surface p-5 text-sm text-neg` error-card pattern used identically on
  `/research/graveyard`, `/research/registry`, `/evidence`, `/backtest`, `/watchlist`,
  `/stocks/[ticker]`, `/themes`, and the app's own global `error.tsx`/`global-error.tsx` — a
  DESIGN SYSTEM token, not an arbitrary value (confirmed via a repo-wide grep, not just the one page).
- The new governance card copies the existing registry/graveyard card markup verbatim (same
  `border-border bg-surface`, `hover:border-accent hover:bg-surface-2`,
  `focus-visible:ring-1 focus-visible:ring-accent` classes) and uses a distinct icon (`Wallet`,
  vs. `BookMarked` for registry and `Archive` for graveyard) — no icon collision, each visually and
  semantically distinct.
- No glassmorphism/glow/gradient introduced anywhere on the new page or card, consistent with this
  product's stated "skeptical, rigorous, honest," data-dense Research-section mood and with the
  plan's explicit Visual Requirements.
- The sparkline SVG uses only `text-accent`/`currentColor` — no arbitrary hex/rgba color introduced.
- No arbitrary spacing/typography values found in the new page; every class traces to an existing
  token already in use on sibling Research pages.

---

## Recommendation

No action required. This iteration's UI evolution is proportionate to its backend capability: one
new capability shipped, one new discoverable entry point added, zero regressions introduced to
shared navigation/data-fetching/routing surfaces, and the one previously-open re-verification debt
(J-19) was closed by the correct lane (canonical browser-qa-agent, not a self-check) with concrete
evidence. The only observation of note — a few `spend_over_time` sub-fields (`deflation_divisor`,
`register_date`, `status`, `staging.n_trials_to_date`) are computed but not individually rendered —
is a deliberate, spec-consistent minimalism choice, not a gap; flagged here for the record only, not
as something the next iteration owes.
