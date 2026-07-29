# Phase goal-ops-hardening-iter-29 — UX Regression Review

**Date:** 2026-07-28

**Verdict:** UX-REGRESSION-FAIL

---

## Summary

The iteration's own intended change — a passive "Unavailable" disclosure note on `/evidence` claim
cards — is cleanly built, fully discoverable, and visually consistent; QA verified it in detail
(UT-05/UT-06, both PASS). However, the mandated regression check of the shared research-engine
surface (TC-9, `/research/factor-lab`) did its job and caught a real, live, 100%-reproducible
backend crash on a normal, 2-click-reachable nav page (UT-07, FAIL). That single finding is enough
to fail this review: a page any user can reach in the ordinary course of navigation currently
crashes on every visit, with the crash produced inside the exact module (`research.py`) this
iteration modified, in a sibling function to the one it fixed.

## New Capability Discoverability

- **Capability:** per-claim "Unavailable — monitored and refreshed as new data arrives." disclosure
  inside the existing `DrawdownExpectationsPanel` on `/evidence` claim cards
  (`apps/frontend/app/evidence/page.tsx`, resolved by
  `resolveDrawdownExpectationsPanelState` in `apps/frontend/lib/evidence.ts`).
- **Navigation path:** none needed — `/evidence` is already 1 click from the home page (confirmed
  by UT-08: "Dashboard → Evidence (1 click) lands on `/evidence`"), and the note renders inline in
  the panel slot the table would otherwise occupy. This is correctly a passive disclosure per the
  plan ("no new button, link, filter, or click path") — there is nothing to discover via navigation
  because there is no new surface, only a new state of an existing one.
  - Confirms my own note: "the button exists somewhere" is not the bar here, and correctly so —
    the spec never intended a button. The bar for a passive disclosure is visibility-in-place, and
    QA confirmed that (UT-05: exactly 1 `evidence-expectations-unavailable` element with the exact
    required copy, other 6 cards unaffected).
- **Label clarity:** "Historical drawdown & dry-spell expectations" (heading, unchanged) +
  "Unavailable — monitored and refreshed as new data arrives." (body) — plain language, no jargon,
  consistent with the existing sibling "Pending — monitored as new data matures" copy already on
  the same card. No label confusion.
- **Visual feedback:** QA (UT-06) confirmed computed-style identity with the pre-existing "Pending"
  note in the same card (`color: rgb(91,102,119)`, `font-weight: 400`, class `text-text-faint`, zero
  icons) — calm, non-alarming, matches the established honest-copy convention exactly.
- **Assessment:** no flags. Fully discoverable, fully consistent.

## Regression Risk

| Shared component | Prior feature | Current-phase change | Risk | Outcome |
|---|---|---|---|---|
| `DrawdownExpectationsPanel` (`apps/frontend/app/evidence/page.tsx`) | J-05 per-claim drawdown expectations (iter-7) | Prop signature changed from `expectations` to the whole `claim`; branches through new resolver | High (central to J-05's rendering, touches all 7 claim cards) | **Verified safe** — QA UT-01–UT-06 confirm all 7 cards render, factor-kind tables byte-intact (UT-03), combination/event-study cards unaffected (UT-04) |
| `_factor_observations` (`apps/backend/app/engine/research.py:197-315`) | Feeds `/evidence`'s expectations panel (J-05) and the Factor Lab's single-horizon path | Accumulator rewritten into bounded per-run-id slices (`_fr_slice_map`) | High (shared read path, multiple pages) | **Verified safe** — TC-1/TC-2/TC-3 unit-proven (chunk-bounded, byte-identical, no-lookahead); developer's own live check of `GET /api/research/factor-lab?factor=leadership_score&horizon=20` returned real data, no crash |
| `_all_factor_observations_by_horizon` (`apps/backend/app/engine/research.py:452-521`) | Factor Lab's all-factors, all-horizons view (J-107→J-109) | **Not touched this iteration** — but exercised by this iteration's own mandated regression sweep (TC-9) of the shared `research.py` module | Critical | **CONFIRMED BROKEN — see below** |

### The confirmed break: `/research/factor-lab`

`apps/frontend/app/research/_labs.tsx:207-216` — `FactorLabPage` unconditionally calls
`fetchFactorLabAll()` on mount, every time, with no user choice that avoids it (the single-horizon
`<select>` was removed at iter-52; "all horizons shown" is now the page's only mode). That function
(`apps/frontend/lib/api.ts:1478-1483`) always requests `GET /api/research/factor-lab?all=true`,
which routes to `compute_factor_lab_all` → `_all_factor_observations_by_horizon`
(`research.py:452-521`). That function builds `fr_by_h: dict[int, dict[tuple[int,str],tuple]]` as
ONE unbounded map across every horizon and every `run_id` in a single pass — the same class of
AG-8 accumulator-unboundedness this iteration fixed in `_factor_observations`'s
`ret_by_run_symbol`, but in a sibling function this iteration's diff never touched (confirmed: the
dev handoff's "Files Changed" list only names `_fr_slice_map`/`_factor_observations`/docstrings in
`research.py`, never the `_all_factor_observations_by_horizon`/`compute_factor_lab_all` block at
lines 444-521 or 2909-2969). The compute is synchronous inside the live request
(`factor_lab_all_cached`, `research.py:2925-2969`, computes on cache MISS in-request, not via a
background warm job), so the crash happens on the user-facing request path, not off to the side.

QA (`reports/phase-goal-ops-hardening-iter-29-ui-test-results.md`, UT-07) reproduced a live
`MemoryError` inside `_all_factor_observations_by_horizon` **three separate times**, "both via
direct API call and via a genuine sidebar click," described in QA's own words as "reproducibly
crashes the backend." The page's only recourse is the app's generic "Backend unavailable"
fallback — no fabricated data, but also no real decile table, no rank-IC, contradicting TC-9's
explicit acceptance clause ("renders its decile table + rank-IC figures with real values... no
console error, no blank/empty table"). Evidence: `reports/qa/goal-ops-hardening-iter-29-evidence/UT-07-backend-unavailable.png`.

Why this belongs in a UX regression review, not just a QA log line:
- **It is not an edge case.** The crash-triggering request fires unconditionally on every page
  mount — there is no factor/horizon combination a user could pick to avoid it, because the page no
  longer offers that choice.
- **The page is not obscure.** UT-08 confirms Factor Lab is reachable in exactly 2 ordinary sidebar
  clicks from the home page (Dashboard → Research → Factor Lab) — well within this review's own
  2-click discoverability bar, which normally would be a compliment; here it means the crash is
  equally easy to reach.
- **It is a shared-component regression by this review's own test.** The ui-surface-map
  (`reports/phase-goal-ops-hardening-iter-29-ui-surface-map.md`, row 4) explicitly lists
  `/research/factor-lab` as an affected surface *because* this iteration modified shared
  `research.py` code, and mandates exactly the check that caught this (TC-9). The skill
  (`ui-regression-scout.md`) calls this pattern out directly: "Find the intersection: components
  that were changed in this phase AND were part of prior features" — `research.py` is that
  intersection, and the mandated check on its neighboring consumer surfaced a real break.
- **The developer's own live verification did not catch it because it exercised a different
  request shape than the real page sends.** The dev handoff's "Live verification" section tested
  `GET /api/research/factor-lab?factor=leadership_score&horizon=20` (the old single-horizon query
  shape, which happens to route through the function actually fixed this iteration) and reported
  success — but the live `FactorLabPage` component never sends that request; it always sends
  `?all=true`, which routes through the untouched, unbounded sibling. The 67-second "no crash"
  result documented in the dev handoff is real but not representative of what a browser actually
  does when a user opens this page.
- **Blast radius beyond Factor Lab is not fully known from the available evidence.** QA's own
  language — "crashes the backend" and a fallback identical to the process-level "Backend
  unavailable" presentation used elsewhere in this codebase for a fully unreachable backend (see
  `components/health-badge.tsx`) — raises, without confirming, the possibility that a `MemoryError`
  this severe destabilizes more than just the one in-flight request. This review does not have
  evidence to state that other journeys were degraded during/after the crash, and does not claim
  that; it flags the ambiguity as a reason for caution, not as a settled fact.

Attribution note, for accuracy: this specific defect is **not** something this iteration's own
code change introduced — `_all_factor_observations_by_horizon` predates iter-29 and was outside its
diff. The plan's own "Explicitly OUT OF SCOPE" list named two sibling risky accumulators
(`_combination_observations`, `_event_study_members`) as known-theoretical, deliberately-deferred
follow-ups — it did not name this one, meaning it was not anticipated. That does not lessen the
user-facing severity today: whether "pre-existing and newly discovered" or "newly introduced," the
product, as currently shippable, has a real nav page that crashes on every visit.

## UI vs Backend Parity

| Backend capability | UI exposure | Assessment |
|---|---|---|
| `_factor_observations`'s bounded/chunked accumulator (Fix 1) | None visible by design — byte-identical output is the entire point | Correctly and explicitly disclosed as intentionally invisible in `user-visible-changes.md`'s "Not Visible Yet" section. No gap. |
| `evidence.py` per-claim isolate-and-continue guard + `expectations_status` field (Fix 2) | New inline "Unavailable" note on the affected claim's card | Fully wired, QA-verified (UT-05/UT-06 PASS). No gap. |

One documentation-accuracy note (non-blocking, informational): `user-visible-changes.md`'s "Not
Visible Yet" section names the two sibling at-risk accumulators it knows about
(`_combination_observations`, `_event_study_members`) but does not mention
`_all_factor_observations_by_horizon` — the sibling that actually turned out to be broken. This
isn't a parity gap in the strict sense (nothing was built-but-hidden), but it means the impact
analysis's own risk map was incomplete going into QA. Worth folding into the next iteration's
risk-scan so this class of surface is checked proactively rather than by incidental discovery.

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None — the new "Unavailable" disclosure is inline, in-place, on an already 1-click-reachable page.

### Potential Regressions

- **[BLOCKING, confirmed not potential] `/research/factor-lab` all-factors view.** Live,
  100%-reproducible `MemoryError` crash on every page visit (QA reproduced 3x). Root cause:
  `_all_factor_observations_by_horizon` (`apps/backend/app/engine/research.py:452-521`), an
  unbounded sibling of the accumulator this iteration fixed, in the same shared module this
  iteration's diff modified. Reachable via ordinary 2-click sidebar navigation
  (Dashboard → Research → Factor Lab); no obscurity protects a real user from hitting it. See
  "Regression Risk" above for the full trace. Evidence:
  `reports/qa/goal-ops-hardening-iter-29-evidence/UT-07-backend-unavailable.png`,
  `reports/phase-goal-ops-hardening-iter-29-ui-test-results.md` (UT-07).
- **[Checked, verified safe] `DrawdownExpectationsPanel` prop-signature refactor** — shared by all 7
  `/evidence` claim cards from J-05 (iter-7). Fully regression-tested by QA, no issues found.
- **[Checked, verified safe] `_factor_observations` itself** (the function actually rewritten) —
  bounded/byte-identical/no-lookahead unit-proven; single-horizon Factor Lab endpoint live-clean.

### Visual Consistency

- The new "Unavailable" note matches the established DESIGN SYSTEM honest-copy convention exactly:
  QA confirmed computed-style identity (`text-text-faint`, same color, same font-weight, no icon) with
  the pre-existing "Pending — monitored as new data matures" note on the same card. No arbitrary
  values, no new tokens, no layout shift (UT-06). This is a clean, low-risk, consistent addition —
  the only issue this review found is unrelated to it.

## Recommendation

1. **Block on the Factor Lab crash before treating this iteration as closed.** A normal,
   2-click-reachable nav page currently fails on every single visit with a live-reproduced
   `MemoryError` originating in the same file this iteration modified. This is not a discoverability
   nit — TC-9's explicit acceptance clause is not met, and QA's own overall verdict is already FAIL
   (13/14) on this exact basis.
2. **Extend this iteration's own fix pattern rather than opening a new investigation.** The fix
   already exists as a template: `_fr_slice_map`'s per-run-id-slice chunking of
   `_factor_observations`'s `ret_by_run_symbol`. `_all_factor_observations_by_horizon`'s `fr_by_h`
   accumulator (`research.py:494-497`) is structurally the same shape (a `(run_id, symbol) →
   (return, drawdown)` map, just keyed per-horizon) and is a strong candidate for the identical
   bounding technique.
3. **If a fix is deferred instead, name it explicitly** the way `_combination_observations` /
   `_event_study_members` were named as known, deliberately-deferred follow-ups — right now this
   defect is unnamed in the spec's OUT OF SCOPE list and was found only incidentally by QA's
   regression sweep. An unnamed, live-reproduced crash on a reachable page is a materially different
   risk posture than a named, theoretical one, and the record should reflect that distinction for
   whoever evaluates GOAL_ACHIEVED next.
4. **No action required** for this iteration's actual intended deliverable (the "Unavailable"
   disclosure on `/evidence`) — discoverability, labeling, visual consistency, and the
   `DrawdownExpectationsPanel` shared-component refactor are all clean per QA's own verified
   evidence.
