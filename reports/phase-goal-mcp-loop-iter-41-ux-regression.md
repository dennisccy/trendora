# Phase goal-mcp-loop-iter-41 — UX Regression Review

**Date:** 2026-07-16

**Verdict:** UX-REGRESSION-PASS

## New Capability Discoverability

**New capability:** "Historical drawdown & dry-spell expectations" panel, appended inside every certified-claim card on `/evidence` (J-25 / B-205).

- **Navigation path:** `/evidence` is an existing top-level sidebar nav item (`Evidence [NEW]`, added iter-1, unchanged this iteration) — 1 click from anywhere via the persistent sidebar. The new panel is additive content *inside* the existing claim cards on that same page, so reaching it costs 0 additional clicks beyond scrolling within the card. Total cost: 1 click + scroll, comfortably inside the ≤2-click bar. No new route, no new page, no nav-skeleton change — confirmed against `runs/goal-session-mcp-loop/state/blueprint.md`'s IA table (J-25 row: "additive panel, no new page/route") and the frontend diff (only `app/evidence/page.tsx`, `lib/evidence.ts`, `lib/api.ts`, `lib/evidence.test.ts` touched — `components/sidebar.tsx` untouched).
- **Label clarity:** heading reads "Historical drawdown & dry-spell expectations ({N}-day hold)" with an explicit subtitle ("descriptive history only, never a forecast or a promise"). Unambiguous, and consistent with the app's existing technical-but-descriptive register (ATR%, p90, downside-vol, etc. already appear elsewhere without simplification). Browser QA (UT-02) independently byte-matched this heading and confirmed the one "forecast" substring hit on the page is the panel's own anti-promise disclaimer, not a promise.
- **Visual feedback on use:** not applicable — the spec explicitly scopes this as a read-only, controls-free panel (anti-goals #1/#2: no buy/sell/trim verbs, no actions to take). Correctly built with zero interactive affordances, so there is nothing to give feedback on.
- **Independently verified, not just claimed:** browser-qa (UT-01 through UT-04, UT-13) confirmed live — panel present on 7/7 cards, real byte-matched Expansion-row figures, a below-floor "insufficient (n=5)" streak cell alongside real sibling cells, a full zero-observation row degrading honestly to "insufficient (n=0)" across all four measures, and the method-note/survivorship-caveat text visible without any interaction (no accordion/tooltip gating).

**Conclusion:** fully discoverable. No hidden or undiscoverable capability.

## Regression Risk

Per the skill's shared-component method, I intersected this iteration's touched frontend surfaces (`ui-surface-map.md`) against prior-phase feature ownership (blueprint IA table + `docs/handoffs/`), then verified the actual diff rather than trusting the handoff narrative alone.

| Shared surface | Prior feature(s) served | Change this iteration | Verification | Risk |
|---|---|---|---|---|
| `ClaimRow` / `apps/frontend/app/evidence/page.tsx` | J-04 (regime-labeled claim rows), J-05 (canonical `/evidence` ledger audit — J-05's home page), J-11 (30-year re-certified ledger, same surface) | One appended line, `<DrawdownExpectationsPanel expectations={claim.expectations} />`, inserted after the closing `</dl>` and before `</CardContent>` | `git diff 3768228 -- apps/frontend/app/evidence/page.tsx` shows the existing 5-field grid, verdict badge, and regime badge markup completely untouched — not reordered, not restyled. QA UT-06 independently re-verified all 5 field labels + FAIL badges byte-identical across all 7 cards, panel always strictly below the grid (never interleaved). QA UT-07 independently re-verified the J-04 regime badge. | **Low** (directly confirmed via diff + independent re-test, not inferred) |
| `CertifiedClaim` type / `lib/evidence.ts`, re-exports in `lib/api.ts` | Any surface importing these types | New `expectations?: DrawdownExpectations \| null` field added; nothing renamed/retyped/removed | `git diff` confirms purely additive interface + additive re-exports (+9 lines in `api.ts`, all new type re-exports) | **Low** |
| `build_evidence_payload` / `engine/evidence.py` | ~13 pre-existing non-route call sites (`test_evidence.py` incl. the frozen-golden `test_canonical_ledger_frozen_golden`) | `session`/`config` added as optional keyword-only params, default `None` → `expectations` omitted entirely, byte-identical to pre-iteration output | Reviewer independently re-ran all ~13 call sites; confirmed unedited + green (`reports/reviews/goal-mcp-loop-iter-41-review.md`) | **Low** |
| `EventStudyCache` table (J-72) | 8+ existing Research-lab aggregations (factor-lab, event-study, regime-lab, phase-severity-lab, combination view, recovery-turn edge, downtrend-opportunity, all-factors view — `engine/research.py`) | New `compute_drawdown_expectations_cached` writes/reads this shared table | Source-inspected directly (not just the handoff's claim): the new code reserves its own `view` sentinel (`_DD_EXPECTATIONS_VIEW = "drawdown_expectations"`), and every one of the 8+ existing consumers *and* the new one scope all queries/writes by `(subject, view, asof_key, dataset_version, horizon)` — the new `view` value cannot collide with any existing row. None of these Research-lab journeys (J-06–J-09) are in this iteration's required-still-passing set, so this check would not otherwise have been caught by this iteration's own test scope. | **Low** (verified in source) |
| `/evidence` cold-load latency (not a shared component, but a behavior change worth naming under this section's brief) | All `/evidence` visitors | First request after any full DB rebuild now takes ~9.5s (previously near-instant); every subsequent request is a few ms (cached) | Disclosed transparently in `user-visible-changes.md` and `reports/perf-budgets.md` Item I; independently measured by both dev (9.471s cold / 6-17ms warm) and QA (UT-01: ~5ms warm, two consecutive curls). Trigger is an operator-run DB rebuild, not normal user traffic. | **Low**, disclosed and mitigated (cache), not hidden |

**Overall regression risk: LOW.** Every touched shared surface was verified with direct evidence (diff inspection, independent QA re-test, or source inspection) rather than accepted on the strength of the "additive" framing in the handoffs alone. Journey-history (`journey-history.json`) shows J-01/J-02/J-04/J-05/J-10/J-11/J-13/J-15/J-16/J-20 were all `passing` prior to this iteration, consistent with these being genuine prior-working journeys, not previously-broken ones being newly excused.

## UI vs Backend Parity

- Every backend capability built this iteration — the two new stored `ForwardReturn` columns, `compute_drawdown_expectations` / `compute_drawdown_expectations_cached`, and the additive `expectations` field on `GET /api/evidence` — is reached by the new `/evidence` panel. Cross-referenced `ui-surface-map.md`'s "Backend-Only Changes" list: every item there (`models.py` columns, `db.py` `_ADDITIVE_COLUMNS` registration, `config.py`/`config.yaml` thresholds, the DB rebuild operation, the test-file group, `perf-budgets.md`) is infrastructure/enabling plumbing, not an independent user-facing capability left stranded without a UI.
- `walk_forward.underwater_horizons` is configured as `[1, 5, 10, 20, 60]` (per the dev handoff), which covers every horizon the product currently serves — no certified claim is silently excluded from the panel today.
- `user-visible-changes.md`'s own "Not Visible Yet" section states "None" — cross-checked against the implementation summary and found consistent; no gap.

**No UI vs backend parity gap found.**

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None.

### Potential Regressions
None confirmed. See the Regression Risk table above — all touched shared surfaces (component, types, backend seam, shared cache table, latency behavior) were independently verified additive-only or disclosed/mitigated.

### Visual Consistency
- **Phase-badge color gap (MINOR, already triaged).** The new per-phase `Badge` elements inside the expectations table (`Expansion`/`Pullback`/`Correction`/`Bear`/`Recovery`) all use the flat `variant="default"` — identical neutral-gray styling regardless of phase — instead of routing through `apps/frontend/lib/phase.ts`'s `phasePosture` mapping, which is the app's single shared phase→color source specifically built so "the same served phase label maps to the same color on every surface" (its own docstring). That module is already imported by the dashboard's "Market Phase & Severity" card (`app/page.tsx`) and `market-phase-card.tsx`. The new table is a third rendering surface for phase labels that does not participate in this shared mapping — a user reading "Bear" in the new table sees plain gray, while "Bear" on the dashboard reads stress-red.
  - Severity: cosmetic only. Phase-name text stays fully legible; no figures are affected; no journey is blocked.
  - Already caught and triaged twice before reaching this review: the code reviewer flagged it (`reports/reviews/goal-mcp-loop-iter-41-review.md`, MINOR, with the exact fix — route through `lib/phase.ts`'s `phasePosture`, mirroring `market-phase-card.tsx`), and browser-qa independently re-confirmed the gap is exactly as documented and no worse (UT-14, CSS class-string inspection, not just a visual read). This was a deliberate developer tradeoff (avoiding a "loud" accent treatment for five repeated per-row labels in a dense table), not an oversight — but it still measurably diverges from the DESIGN SYSTEM's established single-source-of-truth pattern for this specific data point, which is exactly the kind of drift this review is scoped to catch.
- **No other visual-consistency issues found.** The rest of the panel reuses existing primitives verbatim: `Card`/`CardContent`/`Field`/`dl` layout patterns already on this page, `fmtMdd` imported directly from `components/forward-return.tsx` (the same formatter Backtest/stock-detail MDD figures use), and the same muted `text-text-faint` treatment other caveat text already uses elsewhere in the app — confirmed via diff inspection, not just the handoff's self-description.

## Recommendation

No blocking action required — J-25 ships clean on discoverability, regression safety, and UI/backend parity. One pre-existing, already-triaged, non-blocking follow-up carried forward from the code reviewer: route the expectations-panel's phase `Badge` through `lib/phase.ts`'s `phasePosture` (mirroring `market-phase-card.tsx`/`app/page.tsx`) so phase-label coloring reads consistently across all three surfaces that now render market-phase labels. Low priority; does not need to block this iteration's closure.
