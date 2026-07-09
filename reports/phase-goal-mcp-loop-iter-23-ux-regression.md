# Phase goal-mcp-loop-iter-23 — UX Regression Review

**Date:** 2026-07-09

**Verdict:** UX-REGRESSION-PASS

---

## Context

This is a **zero-application-diff, verification-only iteration** (independently confirmed by the dev
handoff, the reviewer's `PASS_WITH_NOTES` verdict, `git diff HEAD`/`git status` re-checked directly by me
just now, and `ui-surface-map.md`). The only file this iteration touched anywhere in the repo is a QA
replay-script fixture (`runs/goal-session-mcp-loop/journey-scripts/J-13.json`, `"587 symbols"` →
`"590 symbols"`) — not application code, not a UI surface. Its entire purpose was to re-run the canonical
`browser-qa-agent` and `ux-regression-reviewer` lanes against the build that already contains iter-22's
shipped feature (deep, vendor-labeled index/macro overlays on the Dashboard chart + the `/data`
vendor-disclosure panel) plus the `minBarSpacing: 0.02` fix, because those reports-of-record had gone
stale and blocked closure (iter-22 → `CLOSURE-FAIL`).

Because there is no new capability to evaluate, this review's job is narrower than usual: (1) confirm the
previously-flagged **iter-22 UX-REGRESSION-FAIL** (a hidden capability) is genuinely resolved on fresh
evidence, not just re-labeled; (2) confirm no prior journey regressed; (3) confirm UI/backend parity holds;
(4) confirm the documentation reconciliation the closure verdict asked for actually happened. I independently
opened two of the QA evidence screenshots (`UT-01-result.png`, `UT-03-hover-leftedge.png`,
`UT-12-backend-recovered.png`, `UT-10-legend-overview.png`) rather than relying solely on the QA report's
prose, per this role's "a PASS label is not proof" standard.

---

## New Capability Discoverability

**No new capability shipped this iteration** (`user-visible-changes.md`: "None. No new user-facing
capability shipped in this iteration."). The table below re-assesses the one capability iter-22's
ux-regression review flagged as **HIDDEN (FAIL)**, now that the fix has fresh, live evidence behind it:

| Capability | Path from home | Clicks | Label clarity | Visual feedback | iter-22 verdict | iter-23 verdict |
|---|---|---|---|---|---|---|
| Per-series vendor label on Dashboard chart legend/tooltip | Dashboard `/` → "Regime × phase cross-view" card | 0 | Clear — vendor in parens/`·` suffix directly on the series name | Immediate, faint-gray inline text | Discoverable — PASS | **Reconfirmed — PASS** |
| `/data` "Index & benchmark data provenance" panel | Dashboard `/` → sidebar "Data Manager" → scroll | 1 | Self-explanatory title + hint text | Own loading/error/empty states | Discoverable — PASS | **Reconfirmed — PASS** (QA UT-23 timed this at exactly 1 click) |
| **Deep `^SPX`/`^NDX`/`^DJI`/`^VIX` benchmark history (1996–2026) on the Dashboard chart's DEFAULT view** | Dashboard `/`, same chart, same pane, zero interaction | 0 | N/A — the fix means no label/hint is even needed, the line is simply on-screen | Immediate — line pixels visible at first paint | **HIDDEN — FAIL** (only reachable via ~10 undocumented full-pane drags) | **RESOLVED — PASS** |

The third row is the load-bearing check. I opened `UT-01-result.png` and `UT-03-hover-leftedge.png`
directly: the Dashboard's chart, in its literal just-loaded state (no zoom, pan, or drag applied), already
spans an x-axis from `1996`/`1999` through `2026`, and the orange/purple/teal/green line pixels for
`^NDX`/`^SPX`/`^VIX`/`^DJI` are visibly present across the entire left portion of the plot, well before the
5 ETF lines (SPY/QQQ/IWM/RSP/DIA) begin around 1999–2005. A hover at the chart's far-left edge reads
`1996-02-26` with exactly the four deep/vol series and their vendor suffix (`^SPX · Stooq`, `^NDX · Stooq`,
`^DJI · Stooq`, `^VIX · Yahoo`) — no fabricated ETF values at that date. The bottom legend, always visible
with no interaction, spells out the vendor for all 5 non-ETF lines directly (e.g. "S&P 500 Index (^SPX)
(Stooq)"), so vendor attribution needs no hover at all. This independently corroborates QA's UT-03/UT-04
PASS calls — the fix genuinely eliminated the hidden-capability defect; it is not a relabeled FAIL.

---

## Regression Risk

Per the skill's method: intersect this iteration's changed files (from `ui-surface-map.md`) against
components prior phases relied on.

| Shared component | Prior feature(s) served | This iteration's change | Risk |
|---|---|---|---|
| `runs/goal-session-mcp-loop/journey-scripts/J-13.json` | J-13's own automated golden-replay script (QA tooling, not application code) | One assertion string updated (`587`→`590 symbols`) to match iter-22's already-shipped additive load | **None.** Not read by any UI surface; a test-fixture-only file. |
| `phase-cross-view-chart.tsx`, `index-vendor-panel.tsx`, `availability-heatmap.tsx`, `app/data/page.tsx`, Sidebar/Nav/layout | J-04, J-12, J-13, J-14, and every other journey's navigation | **Zero diff** (`git diff HEAD` touches none of these) | **None — by construction.** No shared UI/navigation component was edited, so no code-level regression vector exists this iteration. |

Since no shared UI component changed, the residual regression question is purely evidentiary: did the
required-still-passing journeys actually get re-driven live, and did they pass? Per
`ui-test-results.md`, all eight did:

- **J-01** (`/stocks` 541/541, zero leaked `^` rows, sort + Evidence nav) — PASS (UT-16)
- **J-03** (leaderboard + detail page "Not yet proven") — PASS (UT-17)
- **J-04** (Dashboard regime card + regime-conditioned evidence link) — PASS (UT-18)
- **J-05** (`/evidence` 7/7 FAIL rows, auditable linkback) — PASS (UT-19)
- **J-10** (`/stocks/NVDA` Full ↔ Recent toggle, exact bar counts, no crash) — PASS (UT-20)
- **J-11** (no stale pre-refresh edge; both ledgers all-FAIL) — PASS (UT-21)
- **J-12** (`/data` 541 == `/stocks` 541/541; DDOG present) — PASS (UT-22)
- **J-13** (dedicated replay — two-group legend, non-amber ramp, violet ring, md5-distinct hover pair) —
  PASS (UT-10). I opened `UT-10-legend-overview.png` directly: the calendar shows a monotonic blue fill
  ramp (not amber) and several cells carry a distinct violet/purple ring border, consistent with the
  claimed "Scored snapshot — indicator" semantics.

**J-13 coverage-gap closure:** iter-22's ux-regression review carried forward a non-blocking flag — J-13
lacked a dedicated live replay with the same rigor as its six peer journeys (last dedicated pixel was
iter-21). This iteration's UT-10 closes that gap with a fully dedicated, evidence-rich replay (exact
legend strings, computed ramp/ring colors, md5-distinct hover screenshots). **Resolved, not carried
forward.**

**Non-blocking tooling note (not a product regression):** the QA report documents that a deterministic
golden-script replay tool (`demo_runner.py --mode verify`) flagged J-01's "Sort by Sector → expect
Unassigned" step as failing on a timing basis, while three independent live manual re-tests via Chrome MCP
(immediately before and after, with the same selector) produced a consistent, correct 423-occurrence count
each time. I have no way to re-run the replay tool myself from this review, but the manual evidence is
concrete (a repeatable DOM count, not a subjective read), and the underlying table is confirmed
unvirtualized (all ~541 rows always mounted), which is consistent with a replay-tool race rather than an
actual sort defect. Flagged for QA-tooling follow-up so future iterations don't have to re-litigate this;
not a basis for a WARN verdict here since the live product behavior itself was independently reproduced
correct multiple times.

---

## UI vs Backend Parity

No new backend capability shipped this iteration (verification-only). Re-confirming the already-shipped
iter-22 parity, now on fresh evidence:

| Backend capability | Surfaced in UI? | Where | Status this iteration |
|---|---|---|---|
| `vendor` field per index series (`GET /api/indexes`) | Yes | Dashboard chart legend + tooltip; `/data` provenance panel | Both readers reconfirmed live (UT-04/UT-05/UT-07) |
| `first` field (honest first-bar date) | Yes | `/data` provenance panel | Reconfirmed live (UT-07/UT-09) |
| Deep `^SPX`/`^NDX`/`^DJI` price history (1996→) | Yes, **now on both intended surfaces** | `/data` panel (always did) **and** the Dashboard chart's default view (previously did not — see Discoverability above) | **Parity gap from iter-22 closed** — both surfaces now expose the data, not just one |
| `^VIX`/`^TNX` overlay lines | Yes | Chart (default view) + `/data` panel | Reconfirmed |
| `test_api_indexes.py`'s newly-surfaced `full=true` + historical-`as_of` `KeyError: '^TNX'` gap | No UI exposure exists or is claimed | N/A | Correctly and transparently disclosed in `user-visible-changes.md`'s "Not Visible Yet" section as a latent backend/test gap, not a shipped defect. No current page issues that specific parameter combination (the `/stocks/{ticker}` toggle doesn't also pass a historical `as_of`) — verified against the dev handoff's own reachability analysis. This is a backend test-quality gap, not a UI/backend parity gap, and it is not hidden from the record. |

Parity is full for everything actually displayed. The one gap iter-22 left open (data loaded but only one
of two intended display surfaces exposed it) is now closed on both sides.

---

## Flags

### Hidden Capabilities
- None. The one capability iter-22 flagged as hidden (deep 1996 chart history, reachable only via ~10
  undocumented drag gestures) is resolved — confirmed via fresh `browser-qa-agent` evidence (UT-03) and
  independently re-confirmed by me opening the actual screenshot pixels, not trusting a PASS label.

### Undiscoverable Capabilities
- None.

### Potential Regressions
- None confirmed. Zero shared UI/navigation components were touched this iteration (the only file changed
  is a QA-tooling fixture). All 8 required-still-passing journeys were live-replayed with PASS verdicts
  against their own golden scripts, not just re-read from test-plan wording.
- Non-blocking tooling note: `demo_runner.py --mode verify`'s single flag on J-01's sort step could not be
  reproduced via 2 additional live manual re-tests — treated as a replay-tool timing nuance per the QA
  report's own diligence, not a product regression. Worth a follow-up look at replay-tool reliability
  against large unvirtualized tables, but not blocking.
- The J-13 dedicated-replay coverage gap carried forward from iter-22's review is now closed (UT-10).

### Visual Consistency
- No new UI code this iteration — nothing new to assess against the design system. Re-confirmed via direct
  screenshot review that the already-shipped J-14 surfaces remain consistent with the established
  dark-theme system: `Card`/`PanelTitle` structure matching sibling panels, semantic Tailwind tokens, a
  10-swatch categorical chart palette with all values pairwise-distinct (per QA's programmatic
  `getComputedStyle` read), and the availability heatmap's blue (non-amber) density ramp + violet snapshot
  ring rendering exactly as specified. This reconfirms iter-22 ux-regression's "no visual-consistency
  issues found" conclusion, now backed by fresh, post-fix live evidence rather than the earlier stale
  pre-fix report.
- No arbitrary hex values or inline styles observed in any of the reviewed screenshots or component source
  (consistent with iter-22's grep-verified finding, which stands since these files are unmodified).

### Documentation Reconciliation (closure verdict Issue #3)
- **RESOLVED.** The iter-22 closure verdict flagged `user-visible-changes.md`'s claim that the deep lines
  render "automatically on page load... no new click or control is required" as falsified-at-the-time by
  QA's pre-fix UT-03 FAIL, and asked for either a regeneration or an explicit reconciliation note. The
  fresh `reports/phase-goal-mcp-loop-iter-23-user-visible-changes.md` **is** that regeneration: it drops the
  disproven "no click required" framing entirely and instead states plainly that users "can already see"
  the deep lines, without over-claiming render mechanics. Independently, the claim is now factually true
  (confirmed above) — post-fix, the deep lines genuinely do render at first paint with zero interaction —
  so the current record is both appropriately hedged and, on the merits, accurate.
- **Minor non-blocking nit:** `reports/phase-goal-mcp-loop-iter-22-user-visible-changes.md` — the original,
  frozen artifact-of-record — still contains the unqualified, pre-fix sentence verbatim at line 11, and
  iter-23's document links to it as "the original full write-up of these capabilities" without an inline
  caveat. A future reader who opens only the iter-22 file (skipping iter-23's) would see an unannotated
  claim that was false when written and only became true after a same-day fix. This is an internal
  engineering-record nuance, not something any actual product user encounters, so it does not affect this
  iteration's verdict — but a one-line "superseded, see iter-23" annotation on that historical file would
  close the loop for future readers/agents.

---

## Recommendation

No blocking action required — this iteration's UI evolution is fully sound: zero product surfaces changed,
the one previously-hidden capability is now genuinely and independently verified fixed, all
required-still-passing journeys re-verified live, and UI/backend parity is complete for everything
actually displayed.

Optional, non-blocking follow-ups (do not gate this iteration):
1. Add a one-line "corrected — see iter-23 evidence" annotation to
   `reports/phase-goal-mcp-loop-iter-22-user-visible-changes.md` line 11, for any future reader who opens
   that specific historical file directly.
2. Look into the `demo_runner.py --mode verify` timing nuance on J-01's "Sort by Sector" step in a future
   QA-tooling pass so it doesn't have to be manually re-litigated with a live cross-check each time it
   fires.
3. Carried from iter-22 (still non-blocking, still out of this iteration's explicit scope): delete the
   orphaned dead-duplicate `index-regime-chart.tsx` / `major-indexes-card.tsx` pair in a future dedicated
   tidy iteration.
