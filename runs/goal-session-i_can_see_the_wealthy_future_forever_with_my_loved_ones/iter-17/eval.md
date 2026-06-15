# Iteration 17 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

Iter-17 delivered the two lowest-risk frontend polishes of the J-72..J-78 extension — J-74 (multi-hue
availability-heatmap scale + legend + per-bucket legible day numbers) and J-76 (stock-detail price-chart
per-bar hover box). Both diffs are source-verified correct against the spec, coherence is COHERENCE-PASS,
review is PASS, `tsc --noEmit` is clean, backend diff is empty, and no anti-goal is violated. **However,
browser-QA was SKIPPED entirely (0/9 tests; Chrome MCP / DevTools port 9222 unavailable) — there is zero
live screenshot evidence for either target journey.** Per the strict rule (no journey may be marked
passing without positive evidence, and GOAL_ACHIEVED requires every Must-have passing), J-74 and J-76
stay `unknown` and the iteration cannot be declared done. This is an environment failure, not a code
failure — the next iteration only needs to bring up Chrome + re-run browser-QA on these two surfaces.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-74 (target) | new | unknown (code in place, source-verified; no live browser proof) | none — browser-QA SKIPPED |
| J-76 (target) | new | unknown (code in place, source-verified; no live browser proof) | none — browser-QA SKIPPED |
| J-61 (req. passing) | passing | passing (carried; source-verified preserved; not live re-verified) | iter-16 UT-J-70-heatmap-viewport.png |
| J-70 (req. passing) | passing | passing (carried; source-verified preserved; not live re-verified) | iter-16 UT-J-70-heatmap-viewport.png |
| J-20 (req. passing) | passing | passing (carried; hover box pointer-events-none, marker unobscured) | iter-6 UT-J-49-nvda-chart-clamped-bands.png |
| J-45 (req. passing) | passing | passing (carried; regime-band draw path unchanged) | iter-6 UT-J-49-nvda-chart-clamped-bands.png |
| J-42 (req. passing) | passing | passing (carried; hover-box date uses shared formatIsoDate) | iter-16 UT-J-70-heatmap-viewport.png |
| J-05 (req. passing) | passing | passing (carried; no read-path/score change) | iter-9 UT-J-05-J-06-nvda-detail.png |
| J-06 (req. passing) | passing | passing (carried; single-source-of-truth held; coherence PASS) | iter-9 UT-J-05-J-06-nvda-detail.png |
| J-18 (critical invariant) | passing | passing (asof-provider/switcher/calendar untouched; heatmap click → job form only) | iter-16 UT-J-71-cross-month-step.png |

All other journeys (J-01..J-71) carried forward unchanged — none in scope, none touched (frontend-only,
backend diff empty). J-22/J-23/J-24 remain honest blocked-NA (data-walled, non-vetoing per goal.md).

No journey newly passing, no journey newly failing, no journey regressed.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No fabricated data | OK | Heatmap re-styles the same `GET /api/data/availability` payload; hover box reads already-served bars/MA, renders absent MA as "NA" (never fabricated). |
| No recompute in the read path | OK | Backend diff empty; both surfaces re-display served payloads. The hover-box % change is a display derivation of two served closes (pre-registered acceptable presentation math, not a stored canonical value). Coherence Data-Contract PASS. |
| No magic numbers | OK | Heat hues defined ONCE in globals.css CSS vars, registered as Tailwind `heat`/`heat-text` tokens; cells reference `bg-heat-N`/`text-heat-text-N` — no per-cell hex (coherence invariant 10 PASS). |
| No lookahead | OK | Forward (`is_forward`) bar in the hover box is labelled "after as-of (display only)"; visualization-only, feeds no score/bucket/setup/pattern/factor. |
| Exactly one date selector | OK | asof-provider.tsx / asof-switcher.tsx / asof-calendar.tsx untouched (diff-confirmed); heatmap cell-click calls onPrefillRange into the JOB FORM only (never setAsOf); hover box holds no date state. Critical invariant held. |
| Coverage/missing-data descriptive & honest | OK | Heatmap is read-only metadata over stored bars; a thin day renders as a distinct lower-bucket hue, an empty day as the lowest (slate), never filled. |

No anti-goal violations introduced. `anti_goal_violations` array remains empty.

## Next-Step Recommendation

**Re-run browser-QA for J-74 and J-76 on a live frontend** — this is the only blocker to closing this
scope. Bring up the backend (:8835) + frontend (:3835) and Chrome with DevTools on :9222, then capture:
- J-74: `/data` heatmap full-viewport showing the multi-hue scale + legend + snapshot ring; hover shows
  exact figures; a cell click prefills the job-form Start/End and the as-of indicator stays "Latest"
  (URL stays `/data`). Buckets 0–3 are acceptably source-verified per the iter-16 lesson (seed gives
  only full-coverage days); buckets 4–5 + legend need the live capture.
- J-76: `/stocks/NVDA` — move the crosshair, capture the hover box (date `yyyy-MM-dd` + OHLCV + % change
  + MA values); set a historical as-of D so a forward region exists, capture the box labelling a
  forward bar "after as-of (display only)"; move off-chart and confirm the box disappears.
- Also smoke the required-still-passing set live (J-61/J-70/J-20/J-45/J-42/J-05/J-06).

The code itself needs no rework (source review + tsc + build all clean). Depth stays **lean** — this is a
re-verification pass over two isolated frontend surfaces; no backend, no new tests. md5sum the evidence
dir first; one capture per claimed surface; full-viewport for any close-up.

After J-74/J-76 close green, recommended next per the iter-17 spec: J-78 (one-line `config.yaml`
default-range change, line 305) bundled with J-73 (synchronous `?asof` URL hydration — touches
asof-provider.tsx, the J-18/J-43/J-50 invariant core, so handle with care), then the backend cluster
J-72 / J-75 / J-77 at full depth.

## Halt Justification

Not halting. CONTINUE — progress is blocked only by an unavailable browser-QA environment (Chrome MCP /
DevTools :9222 down), not by any code defect, regression, or anti-goal violation. The next step is
clearly actionable (re-run browser-QA live), so this is neither STALLED nor REGRESSION. GOAL_ACHIEVED is
withheld because the two target Must-haves (J-74, J-76) lack the mandatory live browser evidence and must
remain `unknown`.
