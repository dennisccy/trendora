**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

# Iteration 5 Evaluation

## Summary

All three targets (J-48 sortable leaderboard, J-50 href-embedded `?asof`, J-54 new-tab tickers)
landed and pass with verified evidence, and all seven required-still-passing journeys held — the
evaluator independently confirmed the frontend-only diff (8 files, 216+/26-, zero `apps/backend/`),
the pure view-transform sort comparators, and the single `useAsOfHref()` author of every `?asof`
href. One minor defect was found that QA missed: the new `SortHeader` wraps `TermInfo` (whose
`InfoTooltip` trigger is a `<button>`) inside its own `<button>` — invalid nested-button DOM that
matches the new "1 error" Next dev-overlay badge visible on the iter-5 `/stocks` captures (absent in
iter-2 captures), and clicking a header's info icon bubbles into a sort. Extension journeys
J-49/J-51/J-52/J-53 remain unbuilt, so the goal is not yet achieved.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-48 (target) | failing (new must-have) | **passing** | reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-evidence/UT-J-48-restore-rank.png (+ leadership-asc, filter-sort-compose, initial) |
| J-50 (target) | failing (new must-have) | **passing** | UT-J-50-historical-hrefs.png (historical banner + dated rows) + UT-J-50-fresh-tab-asof.png (fresh tab landed historical); DOM href assertions for all 10 sidebar + row links |
| J-54 (target) | failing (new must-have) | **passing** | UT-J-54-newtab-detail.png (new tab on dated MRVL detail); DOM eval: `target="_blank"`, `rel="noopener noreferrer"`, href `?asof=2026-06-05` historical / clean at latest |
| J-02 (required) | passing | passing (re-verified WITH sort active; empty-state compose) | UT-J-02-sort-filter-compose.png |
| J-05 (required) | already_passing | passing (re-verified) | UT-J-05-nvda-detail.png |
| J-06 (required) | passing | passing (NVDA 43.14/54.05/35.80 identical both views — same stored values API-verified in iter-3) | UT-J-06-nvda-coherence.png |
| J-13 (required) | passing | passing (DOM-asserted; see note below) | UT-J-13-asof-switcher.png |
| J-16 (required) | already_passing | passing (re-verified with sort active; honest empty-state + glossary entry) | UT-J-16-vcp-methodology.png |
| J-18 (required) | passing | passing (1 select on /backtest = the global switcher) | UT-J-18-backtest-one-date.png |
| J-43 (required) | passing | passing (reload kept `?asof`; `9999-99-99` degraded clean, no crash) | UT-J-43-invalid-asof-degrades.png |
| J-49 | unrecorded (new must-have) | **failing** (not built — deferred by spec) | n/a |
| J-51 | unrecorded (new must-have) | **failing** (not built — deferred by spec) | n/a |
| J-52 | unrecorded (new must-have) | **failing** (not built — deferred by spec) | n/a |
| J-53 | unrecorded (new must-have) | **failing** (not built — deferred by spec) | n/a |
| J-22/J-23/J-24 | unknown (blocked-NA) | unknown — data-walled, non-vetoing per goal.md; the one-shot best-effort fetch is deferred to the J-53 iteration per the spec's OUT OF SCOPE record | n/a |
| All other journeys | passing / already_passing | unknown this iter → statuses carried over (untouched surfaces; frontend-only diff, coherence PASS) | prior iters |

### Evidence verification notes (skeptical checks performed)

- **md5 spot-check:** three byte-identical groups found. (a) UT-J-05 == UT-J-06 — both the NVDA
  detail; acceptable, J-06's leaderboard half is DOM-extracted and the values match iter-3's
  live-API-verified stored values exactly. (b) UT-J-50-historical-hrefs == UT-J-54-ticker-new-tab —
  same `/stocks` historical view; acceptable, both tests assert href/target attributes only readable
  via DOM. (c) UT-J-13 == UT-J-43 == UT-J-48-initial — the capture shows the **latest** view (no
  historical banner), so it evidences J-48's default order and J-43's post-degrade end state but NOT
  J-13's historical leg; that leg is independently corroborated by the distinct
  UT-J-50-historical-hrefs.png + UT-J-50-fresh-tab-asof.png ("Viewing as-of 2026-06-05 (historical)"
  visible) captured the same session, so J-13 stands.
- **Code audit:** `SORT_COMPARATORS` read only served fields (`rank`, `.score`, `.status`); the sort
  memo is stable (pre-sort-index tie-break) and layered on the filter memo; `useAsOfHref()` reads only
  the one global `asOf`/`isHistorical` context and is the sole `?asof` author across all 8 files; the
  ticker `<Link>` carries `target="_blank" rel="noopener noreferrer"`. No new endpoint, no second
  fetch, no second date state.
- Backend/frontend were down at evaluation time (000 on :8835/:3835; not restarted per project
  memory), so the live API J-06 cross-read was replaced by the iter-3 stored-value match.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Leaderboard sorting is a view transform (no recompute/re-rank/second path) | OK | Comparators read served values; default = stored rank; restore verified (MRVL A94.30/E23.35/E59.43 identical pre/post-sort); no new endpoint |
| `?asof` is a serialization, not a second date state | OK | One helper exported from `asof-provider.tsx`; provider state semantics untouched; invalid param degrades to latest (verified live) |
| Single source of truth (scores never recomputed) | OK | Frontend-only diff; J-06 values identical across views |
| Exactly one date selector | OK | 1 select on /backtest; `/data` inputs untouched |
| No secrets / no backend change asserted | OK | `git diff --name-only -- apps/backend/` empty (evaluator-verified); no credentials in diff |

**Minor defect (not an anti-goal violation):** nested `<button>` — `SortHeader`'s sort button wraps
`TermInfo` → `InfoTooltip`'s own `<button>` on the Leadership / Entry Quality / Risk / Setup headers
(`apps/frontend/app/stocks/page.tsx` SortHeader + `components/ui/info-tooltip.tsx:62`). Invalid HTML
(React DOM-nesting error → the new "1 error" dev-overlay badge on every iter-5 `/stocks` capture,
absent in iter-2 captures), and the inner onClick does not stopPropagation, so opening a header's
definition tooltip also triggers a sort. Functionally all journey legs still pass; fix in the next
iteration.

## Coherence

`runs/goal-session-.../iter-5/coherence.md` = **COHERENCE-PASS** (0 violations; no new routes; the
sort indicator is data-free UI chrome; blueprint tag flip is bookkeeping only). No veto.

## Next-Step Recommendation

Iter-6 at **lean** depth, per the decomposer's batch plan: target **J-49** (dashboard Major-indexes &
regime card renders the **full stored history** regardless of the global as-of, with a vertical as-of
marker when historical; clamp-optional serving on the existing `GET /api/indexes` +
`GET /api/regime-history` endpoints — same stored values, no second path; **J-45 stock-detail bands
stay clamped, explicitly NOT amended**). Required-still-passing should include J-44, J-45, J-20, J-13.
Because the clamp-optional serving touches `apps/backend/` read endpoints, the full backend pytest
suite becomes a gate (~35–46 min — hand to the pump, never two concurrently). **Bundle the
nested-button fix**: render the header info affordance outside the sort `<button>` (sibling, not
child) or use a non-button trigger, and have browser-QA confirm the `/stocks` dev-overlay error badge
is gone and that clicking the info icon no longer changes the sort. Then iter-7 → J-51+J-52 (samples
endpoint family + `/research/samples`), iter-8 → J-53 at **full** depth + the deferred one-shot
J-22/J-23/J-24 + DIA best-effort fetch.
