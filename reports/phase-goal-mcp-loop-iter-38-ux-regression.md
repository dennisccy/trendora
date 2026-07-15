# Phase goal-mcp-loop-iter-38 — UX Regression Review

**Date:** 2026-07-15

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

**New capability: the "Concentration X-ray" section on `/watchlist`** (J-23 / B-204) — pairwise
correlation matrix, deterministic clusters, ENB headline+window, sector/theme/setup concentration bars.

- **Navigation path:** none needed beyond what already exists. `/watchlist` is a pre-existing,
  persistent top-level sidebar item (`apps/frontend/components/sidebar.tsx`, untouched this iteration).
  The X-ray is stacked directly below the existing entries table on that same page — no new route, no
  new nav entry, no sub-menu.
- **Click count:** 1 click from the dashboard (`/` → sidebar "Watchlist" → `/watchlist`). Verified live
  by browser-qa UT-14: clicked "Watchlist" from `/`, landed on `/watchlist`, and "Concentration X-ray"
  text was present immediately with no further navigation. This is inside the 2-click ceiling with room
  to spare.
- **Label clarity:** the section heading is "Concentration X-ray" with an explicit subtitle —
  "Descriptive only — how correlated, clustered, and concentrated your watchlist really is. No
  recommendations." — which is plain language, not developer jargon, and pre-empts the "is this
  advice?" question the anti-goals care about. The one technical term ("effective independent bets") is
  immediately paired with an `InfoTooltip` (accessible name "What is effective independent bets?")
  whose panel text was verified by UT-11 to explain the methodology and the honesty floor in plain
  language.
- **Visual feedback:** the section rides the page's single existing `GET /api/watchlist` fetch/state
  machine (`state.kind`: loading/ok/error in `apps/frontend/app/watchlist/page.tsx`) — the same
  `WatchlistSkeleton` and error card the rest of the page already used cover it; no separate spinner or
  silent-failure risk was introduced. NA cells are visually distinct (dashed border, muted text) rather
  than blank, so a user can tell "not enough data" apart from "nothing to show."

No new user-facing capability from this iteration lacks a navigation path. No new capability requires
more than 1 click. No label confusion found — "Concentration X-ray" accurately describes what renders,
and the copy explicitly disclaims advice language.

---

## Regression Risk

Per the ui-regression-scout method: intersect this iteration's touched files with components prior
Must-have journeys depend on.

| Shared surface | Prior feature it serves | This iteration's touch | Risk |
|---|---|---|---|
| `apps/frontend/app/watchlist/page.tsx` — entries table, Add-ticker form, Remove control | The base watchlist save-list workflow (add/remove/reason, live-enriched columns) | Diff is two insertions around the existing table (`Network` icon import, `CorrelationHeatmap`/`InfoTooltip`/`sectorLabel` imports, and one `<WatchlistXraySection .../>` call appended immediately after the existing `</Card>`). Verified via `git diff`: not a single line inside the pre-existing table/form JSX was touched. | **Low.** Directly regression-tested live: UT-08 (add AAPL → row appears, X-ray recalculates), UT-09 (remove AAPL → reverts byte-for-byte to baseline), UT-10 (all 9 table columns + Remove column unchanged) — all PASS. |
| `apps/backend/app/api/watchlist.py:list_watchlist` | Same base watchlist feature's API contract (`asof_date`, `entries[]`) | Diff confirmed additive-only: `_canonical_rows`/`_enrich` calls are unchanged, only one new `"xray": build_xray_payload(...)` key appended to the returned dict. | **Low.** Byte-identity of `asof_date`/`entries[]` is asserted by the extended `test_api_watchlist.py` and independently confirmed by reading the diff — no existing line of response-building logic was altered. |
| `apps/frontend/app/layout.tsx` → `PreflightBanner` (J-20: "single daily preflight verdict guards every decision surface," whose own acceptance text explicitly names `/watchlist` as one of the surfaces it must render on) | J-20 | `layout.tsx` is **not** in this iteration's diff at all (confirmed via `git status`). The X-ray section is added inside the page component the layout wraps, not the layout itself. | **None.** J-20's banner placement is architecturally independent of this page's body content. |
| `apps/frontend/components/ui/{badge,card,info-tooltip}.tsx`, `apps/frontend/components/empty-state.tsx`, `apps/frontend/lib/sector-label.ts` | Every other page that uses these shared primitives (`/stocks`, `/sectors`, `/themes`, `/evidence`, etc.) | None of these files appear in the diff — the new section only **imports and reuses** them (confirmed via `git status --short` and by reading `page.tsx`'s new imports). `setupVariant()` used by the new setup-concentration bars is literally the same function (defined once, line 47) the existing Setup-column `Badge` already calls — not a duplicate. | **None.** No shared-component source was edited, so no other page consuming these primitives is at risk. |
| `apps/backend/app/config.py` / `config.yaml` | Every config-consuming code path | New `WatchlistCfg`/`WatchlistXrayCfg` classes, wired via `Field(default_factory=...)`, following the same additive pattern as `data_quality`/`chart_bars`/`server` (confirmed by reading the diff). No existing `Config` field changed. | **Low.** A config predating this key still loads unchanged, matching the plan's stated pattern. |

**Conclusion: no potential-regression flags.** The only pages/components this iteration's diff touches
(`watchlist/page.tsx`, `lib/api.ts`, the new `correlation-heatmap.tsx`, plus additive backend/config
files) are either brand-new or touched in a purely additive way that browser-qa independently
regression-tested and confirmed unchanged.

---

## UI vs Backend Parity

`GET /api/watchlist`'s additive `xray` object carries 13 fields. Cross-checked each against the
rendered page (`apps/frontend/app/watchlist/page.tsx` + `components/correlation-heatmap.tsx`):

| Backend field | Surfaced in UI? | Where |
|---|---|---|
| `status` | Yes | Gates `WatchlistXraySection` vs. the "Not enough names yet" `EmptyState` |
| `window_days` | Yes | ENB headline ("over the last N trading days"), `InfoTooltip` body, matrix-cell hover titles |
| `min_overlap_days` | Yes | `InfoTooltip` body ("under {N} days of overlapping history is excluded"), NA-cell hover titles |
| `cluster_threshold` | Yes | Clusters caption ("grouped when their correlation is at or above {N}") |
| `tickers` | Yes | Matrix row/column headers |
| `history_days` | Yes | Every cell's `title` tooltip (self-cell and NA-cell day counts) |
| `correlation_matrix` | Yes | `CorrelationHeatmap` grid (value, color, NA state, tooltip) |
| `clusters` | Yes | Cluster `Badge` chips |
| `effective_number_of_bets` | Yes | ENB headline |
| `enb_member_count` | **No** | Computed and served (`app/engine/watchlist_xray.py`), typed in `lib/api.ts`, but grep confirms zero render sites in `page.tsx` or `correlation-heatmap.tsx` |
| `sector_concentration` | Yes | Sector concentration bars |
| `theme_concentration` | Yes | Theme concentration bars |
| `setup_concentration` | Yes | Shared-setup concentration bar |

12 of 13 served fields are rendered. `enb_member_count` is the one gap — see Flags below. This is
already self-disclosed in `reports/phase-goal-mcp-loop-iter-38-user-visible-changes.md`'s "Not Visible
Yet" section, not hidden by omission.

Also confirmed intentionally NOT built this phase, matching the phase spec's explicit scope boundary
(not a parity gap since no backend work exists for these either): the `/evidence`-side B-104
correlation-audit UI, the J-24 risk-budget card, and the J-25 drawdown/dry-spell panels. `goal.md`'s OUT
OF SCOPE section names all three explicitly, so their absence is a scope decision, not a UI lag behind
a shipped backend capability.

---

## Flags

### Hidden Capabilities
None. The entire new capability (X-ray section) is reachable via the pre-existing `/watchlist` nav item
with zero new navigation required.

### Undiscoverable Capabilities
None. 1-click reach from the dashboard, confirmed live (UT-14).

### Potential Regressions
None found. See the Regression Risk table above — every touched shared surface was either
directly regression-tested live (entries table / add / remove — UT-08/09/10) or confirmed untouched by
diff inspection (layout/PreflightBanner, shared UI primitives, config-consumers).

### Visual Consistency
- **Matches the established style.** The new section reuses, rather than reinvents: the page's existing
  `Card` container pattern, the page's existing `space-y-4` vertical rhythm (the X-ray `Card` is simply
  the next sibling after the entries-table `Card`), the existing `text-pos`/`text-neg`/muted sign-token
  family (already used on this exact page for `price_since_added`, now reused verbatim by
  `correlation-heatmap.tsx`'s `cellTextClass`), and the existing `Badge` variant vocabulary
  (`ok`/`warn`/`danger`/`accent`/`default`). The shared-setup bar's color is not just "the same
  variant name" — it calls the identical `setupVariant()` function the entries table's own Setup column
  already calls (one function, two call sites), which is stronger evidence of consistency than
  independently re-deriving the same mapping would be.
- **No glassmorphism/glow/gradient.** Grepped both new/changed frontend files
  (`watchlist/page.tsx`, `correlation-heatmap.tsx`) for `backdrop-blur`/`shadow-glow`/`animate-glow`/
  `gradient` — zero matches, matching the plan's explicit instruction to keep this page's "dense,
  minimal, data-first look."
- **No arbitrary/new color scale.** Every color class used (`text-pos`, `text-neg`, `text-text-faint`,
  `text-text-muted`, `bg-accent`, `bg-surface`/`bg-surface-2`, `border-border`/`border-dashed`) is a
  pre-existing DESIGN SYSTEM token already in use elsewhere on this same page — no arbitrary hex/rgb
  values or new tokens were introduced.

---

## Recommendation

No action required to ship this iteration. One low-priority, non-blocking note for a future iteration
(not this one — J-23's acceptance criteria in `docs/goal.md` do not require it, and it is already
honestly self-disclosed rather than silently hidden):

- `enb_member_count` (how many watchlist names actually contributed to the ENB figure) is computed and
  served but has no display slot. It is inert today (always equals the visible ticker count on a
  2-name watchlist with no exclusions), but on a larger watchlist where one or more names are excluded
  for short history, a user would see an ENB figure with no visible indication of how many names it was
  actually computed over. Consider surfacing it in a future pass — e.g. appended to the ENB headline
  ("≈ 2.0 effective independent bets across 2 of 2 names") or folded into the `InfoTooltip` body — only
  when a future iteration next touches this section, not as a standalone follow-up.
