# goal-mcp-loop-iter-2 Execution Plan

First referee-certified claim: light the Leadership **"Proven"** badge and add the J-02 proof drill-down.

## Context (read before building)

- **The post-decompose gate already PASSED.** `runs/goal-session-mcp-loop/state/certified-claims.jsonl`
  holds ONE entry: `claim.signal == "leadership_score"`, `verdict.status == "PASS"`,
  `holdout_edge = 0.06359`, `p_value = 0.0004998`, `control_excess = 0.06359`,
  `register_date = "2026-06-30"`, `cohort_n = 12297`, `control_n = 1137`, `horizon = 20`. DoD item
  "gate returns PASS + first entry appended" is **already satisfied** — do NOT re-run the gate.
- The iter-1 lesson is **already handled**: the gate wrote `signal` verbatim onto the claim, and the read
  path keys `proven_signals` on `claim.get("signal")`. So `build_evidence_payload` now returns
  `proven_signals["leadership_score"].proven == true` with **zero backend changes**, and the Leadership
  badge flips to "Proven" end-to-end on `/stocks`, stock-detail, and `/evidence`.
- iter-1 already built the full read path (`GET /api/evidence`, `EvidenceStatusBadge`, `/evidence`
  `ClaimRow` with the 5 fields + `id="signal-leadership_score"` anchor + linkback, inline badges on
  `/stocks` and stock-detail). These now render the populated claim — **exercise + verify, do not rebuild.**
- Alignment: advances goal.md J-02 + J-05 and ships the loop's first certified edge (the core promise).
  No drift, no scope creep detected in the spec.

## What to Build

- **PRIMARY (only new code): J-02 proof drill-down on `/stocks/{ticker}`.** In the stock-detail `ScoreCard`
  (around the `EvidenceStatusBadge` at `[ticker]/page.tsx` ~L607), when a score is **proven**, add an
  in-place expandable "Why proven?" disclosure that reads **verbatim** from `provenSignals[signal]`
  (already fetched — no new fetch, no recompute):
  - **Out-of-sample test**: `verdict.status` + `verdict.holdout_edge` + `verdict.p_value` (+ `cohort_n` /
    holdout dates if present).
  - **Control comparison vs SPY**: `verdict.control_excess`, labeled "vs SPY (benchmark control)".
  - **Certified-claim id + registration date**: `leadership_score · registered 2026-06-30`, linking to
    `/evidence#signal-leadership_score`.
  - When **not** proven: the disclosure is absent/disabled (no empty panel). Additive only — the score
    number is unchanged. Render ONLY on stock-detail, NOT inside `EvidenceStatusBadge` (the badge is also on
    the leaderboard; the panel must not leak there).
- **Exercise + verify (already coded iter-1):** `/evidence` `ClaimRow` now renders the populated
  `leadership_score` row (5 fields) with linkback; `/stocks` + stock-detail Leadership badge now read
  "Proven"; Entry Quality + Risk stay "Not yet proven".
- **OPTIONAL, recommended, non-blocking — read-side signal derivation** in `app.engine.evidence`
  (`_claim_row`/`build_evidence_payload`): when a PASS entry's cohort is a score-column factor
  (`claim.kind == "factor"` and `claim.factor ∈ {leadership_score, entry_quality_score, risk_score}`) but
  `signal` is omitted, derive `signal = claim.factor`. Display-routing only; proven-ness still flows 100%
  from `verdict.status == PASS`; non-spoofable (only the 3 score columns self-map). NOT required this iter
  (the gate already wrote `signal`) — defense-in-depth for future claims.
- **OPTIONAL, non-blocking — de-dup `SCORE_SIGNALS`** (identical in `app/stocks/page.tsx:40` and
  `app/stocks/[ticker]/page.tsx:36`) into `apps/frontend/lib/evidence.ts` (clears a coherence WARN).

## Agents Required

- developer: yes -- build the J-02 proof disclosure on stock-detail (frontend); exercise the already-built
  `/evidence` row + "Proven" badges; optionally add the read-side `signal=factor` derivation (backend) and
  extract `SCORE_SIGNALS` into `lib/evidence.ts`. Add unit tests + write the dev handoff.

## Frontend Present
yes

## Files to Create/Modify

- `apps/frontend/app/stocks/[ticker]/page.tsx` -- add the expandable proof disclosure to `ScoreCard` for
  proven scores (PRIMARY).
- `apps/frontend/components/score-proof-panel.tsx` (new, recommended) -- small client disclosure component
  reading a `ProvenSignal` verbatim; keeps `ScoreCard` thin and the panel reusable/testable. (Inline in
  `ScoreCard` is acceptable if preferred — but keep it off the leaderboard.)
- `apps/frontend/lib/evidence.ts` -- (optional) host the shared `SCORE_SIGNALS` map + any pure proof-field
  display helper so it is `node`-unit-testable (repo `lib/*.test.ts` convention).
- `apps/frontend/lib/evidence.test.ts` -- update/extend: proof-field derivation + fail-safe (nothing for an
  unproven signal).
- `apps/frontend/app/stocks/page.tsx` -- (optional) import `SCORE_SIGNALS` from `lib/evidence.ts` (de-dup).
- `apps/backend/app/engine/evidence.py` -- (optional, recommended) read-side `signal = claim.factor`
  derivation for score-column PASS cohorts. MUST NOT compute proven-ness, add a value, or add an endpoint.
- `apps/backend/tests/test_evidence.py` -- assert `build_evidence_payload` against the populated ledger →
  `proven_signals["leadership_score"].proven == true` with verdict fields intact; (if derivation added)
  assert exact `proven_signals` keys for score-column PASS vs non-score / non-PASS.
- `docs/handoffs/goal-mcp-loop-iter-2-dev.md` -- dev handoff.

## UI Evolution

- New user-facing capability: the platform's **first "Proven" score** — a user opens a stock's detail,
  sees the Leadership score marked "Proven", and expands it to audit *why* (OOS test + SPY control +
  claim id/date), then follows it to the backing Evidence ledger row.
- New information displayed: inline proof panel on stock-detail (holdout edge + p-value + PASS status, SPY
  control excess labeled "vs SPY", claim id + registration date); the populated `leadership_score` claim
  row on `/evidence`.
- New user actions: expand/collapse the "Why proven?" disclosure on a proven score; click the "Proven"
  badge → `/evidence#signal-leadership_score`; click "Backs: Stocks leaderboard →" to return.
- UI surface changes: `/stocks/{ticker}` score cards gain an expandable proof panel for proven scores;
  `/stocks` + `/evidence` change in **state only** (a real "Proven" badge; a populated claim row) — no new
  pages.
- Navigation changes: none (the Evidence nav entry was added in iter-1).

## Visual Requirements

- Component patterns: reuse `Card`/`CardContent`, `Badge` (status + control chips), and the `dt`/`dd`
  `Field` layout the `/evidence` `ClaimRow` already uses, for visual consistency; a plain disclosure
  button/toggle for expand/collapse.
- Layout: the disclosure sits **inside** the existing `ScoreCard`, below the `EvidenceStatusBadge`,
  expanding in-place (no modal/dialog). Stock detail keeps its existing 3-column score grid.
- Key visual effects: calm, evidence-first per goal.md — the accent "Proven" chip, muted body text for
  proof fields, no hype/glow. Palette tokens ONLY (`text-text-muted`, `text-text-faint`, `border`,
  `accent`, `bg-surface-2`); a smooth expand transition consistent with existing components.
- States to handle: **proven** → collapsed-by-default panel, expandable; **not proven** → no disclosure
  (absent/disabled, never an empty panel); **loading / fetch-failure** → fail-safe "Not yet proven", no
  panel (page never breaks).

## Key Test Scenarios

- **J-02 (browser, must verify by ID):** `/stocks` → click a stock → the Leadership badge reads "Proven";
  expand the proof → OOS test (status PASS, holdout edge ≈ +6.36%, p ≈ 0.0005), SPY control (≈ +6.36%
  labeled "vs SPY"), claim id `leadership_score · registered 2026-06-30` + link to
  `/evidence#signal-leadership_score`. Displayed numbers **byte-identical** to `GET /api/evidence`.
- **End-to-end badge flip (browser, real screenshot):** Leadership reads "Proven" on `/stocks` AND
  stock-detail — not merely a ledger row in JSON (per the iter-1 lesson).
- **J-05 (browser):** `/evidence` renders the populated `leadership_score` row (all 5 fields); "Backs:
  Stocks leaderboard →" navigates to `/stocks`; the leaderboard "Proven" badge round-trips to
  `/evidence#signal-leadership_score`.
- **J-01 regression:** every leaderboard score still shows a status — Leadership now "Proven", Entry
  Quality + Risk still "Not yet proven".
- **J-03 regression:** Entry Quality + Risk still read "Not yet proven", never a confident number.
- **Unit:** proof panel reads `provenSignals[signal]` verbatim and shows nothing for an unproven signal
  (fail-safe); `build_evidence_payload` over the populated ledger → `proven_signals["leadership_score"].
  proven == true`; absent/empty/unreadable ledger → `{claims:[], proven_signals:{}}` (200, never 500).
- **Unit (if read-side derivation added):** a PASS score-column factor cohort maps to that signal; a
  non-score cohort or non-PASS entry does NOT (assert exact `proven_signals` keys).

## Out of Scope (exclude — from spec; do not let scope creep in)

- J-04 regime-conditioned evidence (deferred to iter-3 — a regime slice risks an INSUFFICIENT verdict;
  don't jeopardize the first PASS).
- Proving Entry Quality or Risk — only `leadership_score` is claimed; the other two stay honestly
  "Not yet proven" (do NOT fabricate a status).
- Multi-control set (QQQ / sector ETF / random same-sector) — the referee certified vs the **SPY**
  benchmark only; show that single control honestly labeled "vs SPY". Adding uncomputed controls violates
  the displayed-numbers-are-correct anti-goal.
- Any second proven-ness computation or second evidence endpoint (forbidden — Data Contract row 1 is
  canonical); any change to the three scores, the regime/forward engines, or `GET /api/evidence`'s shape.
