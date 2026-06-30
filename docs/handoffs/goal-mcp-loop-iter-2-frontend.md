# goal-mcp-loop-iter-2 Frontend Handoff

**Phase:** goal-mcp-loop-iter-2
**Date:** 2026-06-30
**Agent:** developer
**Status:** complete

## What Was Built (UI)

- **"Why proven?" proof drill-down on the Stock-detail score card (J-02).** A new client component,
  `ScoreProofPanel`, sits below the inline `EvidenceStatusBadge` inside each `ScoreCard` on
  `/stocks/{ticker}`. For the **Leadership** score (now Proven) it shows a calm, collapsed-by-default
  disclosure with a "Why proven?" toggle. Expanding it reveals three fields, all read **verbatim** from the
  already-fetched `proven_signals` map (no new fetch, no recompute):
  - **Out-of-sample test** — a `PASS` chip, `holdout edge +6.36%`, `p = 0.0004998`, and a sealed-holdout
    cohort line (`12,297 observations`).
  - **Control comparison** — `+6.36%` labeled `vs SPY (benchmark control)`.
  - **Certified claim** — `leadership_score · registered 2026-06-30`, with a `View backing evidence row →`
    link to `/evidence#signal-leadership_score`.
  For **Entry Quality** and **Risk** (not proven) the panel renders **nothing** — there is no empty panel and
  no toggle. The score number itself is unchanged (purely additive).
- **State-only changes on existing surfaces (already coded in iter-1, now populated):** the `/stocks`
  leaderboard and the stock-detail Leadership badge now read **"Proven"** (accent chip linking to
  `/evidence#signal-leadership_score`); the `/evidence` ledger renders the populated `leadership_score`
  claim row (Hypothesis, Out-of-sample verdict + holdout edge, Control comparison vs SPY, Registration date,
  Forward-walk = "Pending") with its `id="signal-leadership_score"` anchor and the
  "Backs: Stocks leaderboard →" linkback. These were verified, not rebuilt.

## Files Changed

- `apps/frontend/components/score-proof-panel.tsx` (new) -- the J-02 disclosure component.
- `apps/frontend/app/stocks/[ticker]/page.tsx` -- renders `ScoreProofPanel` in `ScoreCard`; uses shared
  `SCORE_SIGNALS`.
- `apps/frontend/app/stocks/page.tsx` -- uses shared `SCORE_SIGNALS` (de-dup; no behavior change).
- `apps/frontend/lib/evidence.ts` -- shared `SCORE_SIGNALS` + `proofFieldsFor` + `formatEvidencePct` +
  `formatPValue`.
- `apps/frontend/lib/evidence.test.ts` -- new unit coverage for the above.

## Design / Visual Notes

- Reuses existing primitives only: `Badge` (accent status chip), the `dt`/`dd` field layout pattern from the
  `/evidence` `ClaimRow`, and lucide `ShieldCheck` / `ChevronDown`. Palette tokens only (`border`,
  `bg-surface-2`, `text-text`, `text-text-muted`, `text-text-faint`, `accent`) — no arbitrary colors, no
  glow/hype (evidence-first, per goal.md).
- The disclosure expands **in place** (no modal), with a smooth 200ms chevron rotation. The toggle has hover
  and `focus-visible` ring states and an `aria-expanded` attribute.
- States handled: **proven** → collapsed panel, expandable; **not proven / loading / fetch-failure** → no
  panel at all (the page never breaks; the badge stays "Not yet proven" fail-safe).

## Test Hooks (for browser QA)

- `data-testid="score-proof"` (panel root), `score-proof-toggle` (the "Why proven?" button),
  `score-proof-body` (expanded content), `proof-holdout-edge`, `proof-p-value`, `proof-control-excess`,
  `proof-claim-id`, `proof-evidence-link`.
- Existing badge hook `data-testid="evidence-badge"` with `data-proven="true|false"` distinguishes
  Proven vs Not-yet-proven on both `/stocks` and stock detail.

## Verification

- Frontend unit tests: 10 passed (transpile-and-run; see dev handoff for the exact command).
- `tsc --noEmit`: clean. `next build`: succeeded — `/stocks/[ticker]`, `/stocks`, `/evidence` all compiled.

## Known Limitations

- The proof panel intentionally shows only the **SPY** benchmark control (the one the referee computed),
  honestly labeled — additional controls are a future iteration.
- Numeric display is re-formatted from the exact served float (edge/control as signed percent; p-value to
  4 significant figures) — nothing is recomputed client-side.
