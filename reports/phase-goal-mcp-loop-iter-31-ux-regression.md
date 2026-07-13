# Phase goal-mcp-loop-iter-31 — UX Regression Review

**Date:** 2026-07-13

**Verdict:** UX-REGRESSION-WARN

---

## New Capability Discoverability

| Capability | Nav path | Clicks from home | Label clarity | Feedback |
|---|---|---|---|---|
| `/research/graveyard` page (browse every rejected hypothesis) | Dashboard → "Research" sidebar item → "Negative-results graveyard" card in the existing `data-testid="research-governance"` grid | 2 (QA-confirmed via `UT-14`: sidebar unchanged, 11 items, Research 7th; card click lands on `/research/graveyard`) | Clear — card title "Negative-results graveyard," description "Every hypothesis the referee has rejected... Nobody retries a dead idea blindly." Plain language, no internal jargon ("non-PASS" does not appear in the card copy per `UT-14`) | Standard loading skeleton → populated table; verified in-browser |
| "permanent" marking on a closed hypothesis (`ma_stack`) | Inline pill next to the Verdict badge on the graveyard row itself — no separate navigation required | 2 (same as above, then visible in-row) | Clear — "permanent" text, muted/neutral styling, unique to the one closed row (`UT-06`) | Visible immediately on page load, no interaction needed |
| Revisit-protocol rule (when a dead idea may be re-tested) | "Revisit protocol →" link on every graveyard row, anchors to a `Card` panel (`id="revisit-protocol"`) on the same page | 2 (same as graveyard) + 0 extra clicks to reach the rule text (it's already on-page; the link only assists scrolling) | Clear | Confirmed working: `UT-08` shows the anchor click moves `window.scrollY` to the panel and the panel is in-viewport |
| Lineage link (rejected hypothesis → its registered entry) | "Lineage" column link on each graveyard row | 3 to actually **land on the correct row** (2 to reach the graveyard, 1 more click on the link) — but see Flags below: the 3rd click does not deliver its "land on the exact row" promise | Clear — link text is the registration id + "→" | **Broken for the scroll-assist part** — see `### Broken Capabilities` below |
| Staging-ledger rejections (internal exploration track) now visible | Same graveyard table; a "Ledger" column pill (`canonical`/`staging`) distinguishes origin per row | 2 | Clear — plain "staging"/"canonical" pill text | Confirmed 7/7 split rendered (`UT-02`) |

All five new capabilities named in `user-visible-changes.md` have a working navigation path reachable in ≤2 clicks, matching the phase spec's own discoverability requirement ("reachable from `/research` governance grid in ≤2 clicks"). No capability from this iteration is hidden or requires developer knowledge to find — this was independently confirmed by `browser-qa-agent` (`UT-02`, `UT-14`), not just asserted by the dev handoff.

---

## Regression Risk

Per the skill's method: intersect this iteration's `ui-surface-map.md` file list against prior-phase handoffs. Only one prior phase's shared surfaces are touched by iter-31 — iter-30 (J-18, the pre-registration registry). Grep across `docs/handoffs/*.md` confirms no other mcp-loop iteration touched `research/page.tsx`, `research/registry/page.tsx`, or the sidebar/nav files since iter-30/iter-31 (sidebar was last touched at iter-1/19/21, none of which iter-31 touches).

| Shared component | Prior feature it serves | Current phase's change | Risk | Evidence it still works |
|---|---|---|---|---|
| `apps/frontend/app/research/page.tsx` | iter-30: the 10-card research-labs grid (long-standing) + the "Governance & process" section's first card ("Pre-registration registry") | Additive: a second card in the *same, already-reserved* grid slot + a comment-only string update | **Low** | `UT-12` (regression test): all 10 lab-grid titles/order unchanged; exactly 2 governance cards in order, both descriptions verbatim-matched, including the pre-existing registry card's description |
| `apps/frontend/app/research/registry/page.tsx` | iter-30: J-18's registry table (11 rows, 5 columns) | Presentation-only: `id={`registration-${row.id}`}` + `scroll-mt-20` added to each `<tr>` | **Low for the page's own journey; see Flags for the new cross-page interaction it enables** | `UT-13` (regression test): plain (non-anchor) browsing shows the same 11 rows/5 columns as before; a **direct hard-navigation** to `/research/registry#registration-<id>` correctly scrolls to the target row, proving the anchor mechanism itself is sound |
| `apps/backend/main.py` (router registration) | Every existing endpoint's reachability (evidence, registry, etc.) | Additive 2-line change: new import + `include_router(graveyard.router, ...)`, no existing line touched | **Low** | `UT-13`: `/evidence` still serves 7 FAIL cards, byte-identical to pre-iteration expectations; dev handoff's live smoke test confirms `/api/evidence`, `/api/research/registry` unchanged |
| `apps/frontend/lib/api.ts` | Every page that fetches data (`fetchEvidence`, `fetchRegistry`, etc.) | Additive: new `fetchGraveyard()` + re-exported types, no existing export altered | **Low** | `tsc --noEmit` clean project-wide (would catch a broken existing import); `/evidence` and `/research/registry` both confirmed unchanged live |
| Shared component library (`Badge`, `Card`, `CardContent`, `PageHeading`) | Every page in the product | **Not touched** — only consumed/imported by the new page | **None** | Confirmed by absence from both dev and frontend handoffs' "Files Changed" lists and the ui-surface-map's file classification table |

No prior-phase user journey shows evidence of regression. The two touched shared surfaces (hub grid, registry page) were both explicitly regression-tested by browser QA with PASS results, not just asserted by the developer.

---

## UI vs Backend Parity

| Backend capability (from `app.engine.graveyard.build_graveyard_payload`) | UI exposure |
|---|---|
| Non-PASS ledger entries (canonical + staging), status-filtered | Rendered — all 14 rows, `UT-02` |
| Origin ledger tag (`canonical`/`staging`) | Rendered — Ledger column pill, `UT-02` |
| `verdict.deflation` / `deflation_divisor` (verbatim) | Rendered — Deflation column, `UT-05` |
| Registration lineage (`registry.match_registration`) | Rendered — Lineage column link/honest-null text |
| "closed" status → "permanent" marking | Rendered — permanent pill, `UT-06` |
| `REVISIT_PROTOCOL` constant | Rendered — Revisit-protocol panel, `UT-08` |
| `cohort_n` / `control_n` (present in the `GraveyardEntry` type per the frontend handoff, part of the raw ledger entry shape) | **Not surfaced as a dedicated column** — but the phase spec's own "New information displayed" list only names selectors/verdict/date/deflation/ledger/lineage; these two fields are not in that list, and the sibling `/evidence` page does not surface them as standalone fields either. This is consistent precedent, not a gap introduced by this iteration. |

`user-visible-changes.md`'s "Not Visible Yet" section claims "None" — this iteration's one new backend capability (`GET /api/research/graveyard`) has a complete UI consumer. Independent cross-check against `ui-surface-map.md` and the QA results confirms this claim holds: every field the spec requires to be displayed is displayed. No backend-complete-but-UI-absent gap found.

---

## Flags

### Hidden Capabilities
None. All new capabilities have a navigation path, confirmed live by browser QA.

### Undiscoverable Capabilities
None. Everything is reachable in ≤2 clicks with plain-language labels, confirmed live by browser QA (`UT-14`).

### Broken Capabilities
- **Lineage link's "scroll to exact row" promise does not fire on the actual user click path.** `user-visible-changes.md` states as a delivered capability: *"Users can now click a graveyard row's Lineage link and land precisely on that hypothesis's own row on `/research/registry` (the page scrolls to and positions the exact row, not just the top of the page)."* Browser QA (`UT-07`, P1 happy-path) proved this false for the real interaction: clicking the link navigates to the correct URL (including the correct `#registration-<id>` fragment) and the target row genuinely exists in the DOM, but `window.scrollY` stays at `0` — no scroll occurs. Root cause, confirmed by direct source inspection: `apps/frontend/app/research/graveyard/page.tsx:230` renders the Lineage link as a Next.js `<Link href={asofHref(...#registration-<id>)}>` — a client-side (SPA) route transition. Browsers only auto-scroll to a URL fragment on a full/hard page load; Next.js App Router does not reliably replicate that behavior on client-side navigation to a different route. QA's own control test proves this precisely: typing the identical URL directly into the address bar (hard navigation) **does** scroll correctly to the row (`UT-13`), isolating the defect to the SPA-link code path, not the anchor mechanism (`id`/`scroll-mt-20` on `apps/frontend/app/research/registry/page.tsx:133`) itself, which works.
  - **Why this is WARN, not FAIL, under this agent's rubric:** the capability is not hidden (the link is visible, correctly labeled, on every row) and not inaccessible (the click does land the user on the correct page, with the correct heading, and the target row's content is on that page). With today's live data (11 registry rows on a standard viewport), the destination table is small enough that a user lands within sight of, or one small scroll from, the row they wanted — this is a rough edge, not a wall. It is also not a regression of a *prior* journey: J-18's own registry-browsing journey is unaffected (`UT-13` plain-browsing regression check passed), and the anchor mechanism J-19 added to that page works correctly on its own.
  - **Why this should not be dismissed as trivial:** it is an explicit, P1-tested, spec-named new user action ("click a row's lineage link through to its registry row" — phase spec TESTING REQUIREMENTS) that does not do what the product now claims it does. As the registry grows past what fits in one viewport (already flagged by QA: rows 9–11 today, more as more hypotheses are registered), this stops being cosmetic and starts being a real "search the page yourself" tax on exactly the workflow (tracing a dead idea back to its registration) this iteration exists to support.
  - **Recommendation:** the developer/reviewer should add an effect that scrolls the target element into view after a client-side route change lands on a URL with a hash (e.g., a `useEffect` keyed on the route + hash calling `document.getElementById(...)?.scrollIntoView()`), consistent with how `/evidence`'s existing `ClaimRow` anchor pattern is described as behaving. This is a source-code fix outside this review's scope to apply — flagging only.

### Potential Regressions
None found. The two shared surfaces this iteration touches (`research/page.tsx` hub grid, `research/registry/page.tsx` table) were both explicitly re-verified by browser QA with PASS results (`UT-12`, `UT-13`), not left to inference.

### Visual Consistency
- New page (`/research/graveyard`) matches the established Research-section style: `Card`/`CardContent` + plain `<table>`, `PageHeading`, the same `text-sm` / `text-xs uppercase tracking-wide text-text-faint` header tokens, `border-border`, `bg-surface`/`bg-surface-2` — all pre-existing design-system tokens, no arbitrary values introduced (confirmed by the dev handoff's Design System Compliance section and independently by QA's live DOM class inspection in `UT-04`).
- Verdict badges correctly use the `danger` (FAIL, red) / `warn` (INSUFFICIENT, amber) variants and explicitly avoid the `accent` ("Proven," green) variant `/evidence` reserves for PASS — QA confirmed this via actual class-attribute inspection (`border-neg ... text-neg`, not `accent`), not just by reading the source. This is the single most safety-critical visual rule in this product (the anti-goal against presenting unproven/rejected values as proven) and it held.
- No new visual effects (glow/gradient/glassmorphism) were introduced; the page stays "dense, calm, data-first," consistent with every other Research sub-page and explicitly consistent with iter-30's identical registry-page style statement.
- No arbitrary/one-off values found in either handoff's file list or QA's DOM inspection.

---

## Recommendation

1. **Fix the Lineage-link scroll behavior** (`apps/frontend/app/research/graveyard/page.tsx`'s `LineageLink` → `apps/frontend/app/research/registry/page.tsx`'s row anchors) so a client-side navigation to a hash URL scrolls to the target element, not just a hard/full navigation. This is the one concrete gap between what `user-visible-changes.md` claims ships and what a real click delivers. Low urgency today (11 registry rows, mostly in-viewport already) but will compound as the registry grows — worth fixing before or alongside the next iteration that touches either page, not necessarily blocking this one.
2. No other action required — discoverability, prior-journey regression risk, and UI/backend parity are all clean, each backed by independent browser-QA verification rather than developer self-report alone.
