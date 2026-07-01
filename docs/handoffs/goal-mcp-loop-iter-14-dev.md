# goal-mcp-loop-iter-14 Dev Handoff

**Phase:** goal-mcp-loop-iter-14
**Date:** 2026-07-01
**Agent:** developer
**Status:** complete

## What Was Built

**Nothing — this is a verification-only iteration (INITIAL BUILD with zero feature code).**
Per the iter-13 evaluator's explicit LEAN recommendation, iter-14 is the clean, backend-up
**re-run** that verifies the already-shipped J-08 capability end-to-end: the
`/research/factor-combination` composite **"Proven"** badge for
`rs_spy_3m:top:quintile × high_proximity:top:tertile @ h20` renders "Proven" and deep-links to
its backing 6th `/evidence` combination row, with the committed hash-scroll fix landing that row
in the viewport.

The mechanism under test — the iter-13 audit's hash-scroll `useEffect` in
`apps/frontend/app/evidence/page.tsx` (L57-66) — is already at HEAD. I **verified it live and it
is sufficient**, so the spec's contingency (a minimal additive scroll/anchor correction) was
**NOT triggered**. No app code changed; `certified-claims.jsonl` is byte-identical (6 rows).

## Verification performed (live, backend held up the whole run)

Stack brought up on the canonical QA ports (backend `:8255`, frontend `:3255`) using the same
scripts the browser-qa lane uses (`scripts/start-backend.sh` + `scripts/start-frontend.sh`). The
frontend was served from a **fresh production build** (`next start`) that includes the committed
fix — there was no prior prod build, so a stale bundle could not have been served.

- **Backend payload (curl, before + reachable throughout):** `GET /api/evidence` → 200, exactly
  **6 claims**. Combination row: `kind=combination`,
  `condition=[rs_spy_3m:top:quintile, high_proximity:top:tertile]`, `horizon=20`,
  `proven=true`, `signal=null`, `holdout_edge=0.046931901591708916`,
  `control_excess=0.046931901591708916`, `p_value=0.0009995002498750624`,
  `register_date=2026-07-01`. `proven_signals` keys = `['leadership_score']` only (the signal-less
  combination cannot and does not leak a `/stocks` badge).
- **Default honest-marking (J-03):** on `/research/factor-combination` the config-default leg 2
  (`atr_pct:bottom:tertile`) badge is `data-proven=false`, text **"Not yet proven"**, not a link.
  No "Backend unavailable" pill.
- **Compose the certified selection:** leg 1 kept `rs_spy_3m` top `quintile`; leg 2 set to
  `high_proximity`, side **Top**, quantile `tertile`; horizon 20. Badge flips to
  `data-proven=true`, `data-legs="rs_spy_3m:top:quintile,high_proximity:top:tertile"` (contains
  both factors), text **"Proven"**, and `href="/evidence#combination-high_proximity-rs_spy_3m-h20"`.
- **Deep-link + hash-scroll (the exact iter-13 failure point):** clicking the "Proven" badge (and,
  independently, a cold navigation from `/stocks` → `/evidence#combination-high_proximity-rs_spy_3m-h20`)
  lands on `/evidence` and the page **auto-scrolls** (measured `window.scrollY = 1034`, the page
  maximum; `docHeight 1934 − vh 900`) so the 6th combination `ClaimRow` is **fully in the viewport**
  (`getBoundingClientRect` top=591, bottom=876, vh=900). Without the fix `scrollY` would be 0 and the
  last row off-screen — this is the concrete regression that iter-13 hit and that is now fixed.
- **Byte-match (anti-goal #3), read from the rendered row:** `PASS · holdout edge +4.69%`,
  `CONTROL COMPARISON (VS SPY) +4.69%`, `p=0.0009995 < alpha/6=0.008333` (Bonferroni divisor 6),
  `REGISTRATION DATE 2026-07-01`, `kind=combination`, `ledger=canonical`,
  `Backs: Multi-factor combination lab →`. Full-page capture confirms all 6 rows render with correct
  values (J-05 ledger; J-04 "Regime: Risk-on" row; J-03 FAIL ma_stack honestly marked; J-06 h20 +
  J-07 h60 vcp_contraction rows).
- **`/stocks` regression (J-01 + no leakage):** 0 `combination-evidence-badge` elements on `/stocks`;
  360 inline evidence-status badges present, a Proven/Not-yet-proven mix; no "Backend unavailable" pill.

## Files Changed

- No application, engine, ledger, or config files changed (verification-only).
- `docs/handoffs/goal-mcp-loop-iter-14-dev.md` -- this handoff.
- `runs/goal-mcp-loop-iter-14/status.json` -- pipeline status (`current_step: dev_complete`).
- `runs/goal-mcp-loop-iter-14/dev-verify-*.png` -- three md5-distinct dev-verification captures
  (combination-lab certified selection; `/evidence` full ledger with the 6th combination row;
  `/evidence` top) preserved as reference evidence for the reviewer / browser-qa lane.

## Tests Run

Command: `cd apps/frontend && npx tsx lib/evidence.test.ts`
Result: **37 passed, 0 failed** — the evidence-badge resolver suite (incl.
`resolveCombinationEvidence`, `combinationCohortFromClaim`, `combinationClaimId`,
`combinationEvidenceAnchor`, `claimAnchorId` for combinations). The expectation tests are
**UNEDITED** (byte-identical to HEAD — confirmed via `git status --short`), per the iter-9 lesson.

Backend `GET /api/evidence` live-checked (200, 6 claims) rather than via a pytest run, since no
backend code changed this iteration and the ledger is byte-identical to HEAD.

## Known Issues

- **None blocking.** The committed hash-scroll fix is verified sufficient; the contingency
  read-side correction was not needed and was not applied.
- **Screenshot-tooling note for the browser-qa lane (not a product defect):** in my Chrome-MCP
  session, a *viewport* screenshot of `/evidence` returns a blank dark frame **when the window is
  programmatically scrolled below the fold** (a headless-Chrome compositing/repaint artifact at a
  scroll offset). It is purely a capture artifact — proven by (a) the DOM eval showing the combination
  row fully rendered and in-viewport at `scrollY=1034`, (b) the page rendering perfectly at
  `scrollY=0`, and (c) a **full-page** capture cleanly showing all 6 rows including the scrolled-to
  combination row (`runs/goal-mcp-loop-iter-14/dev-verify-evidence-ledger-6rows.png`). For the
  terminal md5-distinct "scrolled-into-frame" evidence, prefer **full-page** or **element-clip**
  captures over a plain viewport capture, and ground the pass in the DOM assertions + the byte-exact
  ledger + the green unit tests (iter-11 lesson). Do not misread a blank scrolled viewport frame as
  the row failing to land — the row DOES land (DOM-verified).
- **Backend must be held up for the browser-qa run.** I cleaned up my own `:8255`/`:3255` processes
  at the end (both ports FREE afterward; the goal engine was left untouched); the browser-qa lane
  starts its own services via the same scripts.
