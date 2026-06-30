# goal-mcp-loop-iter-2 — Implementation Summary

**Phase:** goal-mcp-loop-iter-2
**Date:** 2026-06-30
**Written by:** developer

---

## Features Implemented

- **First "Proven" score, end to end.** The Leadership score is now the platform's first signal backed by a
  statistically certified claim. On the Stocks leaderboard and on a stock's detail page, the Leadership
  score now shows a green **"Proven"** badge instead of "Not yet proven". Entry Quality and Risk still
  honestly read "Not yet proven" — nothing was fabricated for them.
- **"Why proven?" proof drill-down (the headline new capability).** On any stock's detail page
  (`/stocks/{ticker}`), the Proven Leadership score now has a small **"Why proven?"** toggle. Opening it
  reveals — in plain, auditable terms — *why* the score is considered proven:
  - the **out-of-sample test** (it passed; the measured out-of-sample edge of about **+6.36%**, with a
    significance value of **0.0004998**, over a sealed sample of **12,297** observations);
  - the **control comparison** (it beat the **SPY** benchmark by about **+6.36%**);
  - the **certified-claim id and date** (`leadership_score · registered 2026-06-30`), with a link to the
    full record on the Evidence page.
- **Round-trip between the score and its evidence.** Clicking the "Proven" badge jumps to the matching row
  on the **Evidence** ledger; the Evidence row links back to the Stocks leaderboard. A user can now walk
  from a score, to its proof, to the ledger entry, and back.

---

## Changed Behavior

- **Leadership badge:** Previously read "Not yet proven" everywhere (the evidence ledger was empty). Now
  reads **"Proven"** on the Stocks leaderboard and stock-detail, because the referee certified the claim and
  wrote the first ledger entry.
- **Stock-detail score cards:** Previously showed only the score and its status badge. Now a Proven score
  additionally offers an expandable proof panel. Unproven scores are visually unchanged (no panel).
- **Evidence page:** Previously showed an honest "no certified claims yet" empty state. Now shows one
  populated, certified claim row (Leadership). This row was already built last iteration; it simply has real
  data to display now.

---

## Backend-Only Items

- None. Every backend value shown was already served by the existing `GET /api/evidence` endpoint; this
  iteration added no new endpoint and no new computation. (A small internal hardening was added to how the
  read path maps a certified claim to a score — see "Config and Environment Changes" — but it surfaces no
  new data.)

---

## Incomplete Items

- **Regime-conditioned evidence (journey J-04)** is intentionally **deferred to the next iteration**. It was
  declared out of scope here to avoid jeopardizing this first certification (a narrower, regime-scoped claim
  risks failing the referee's minimum-sample bar). Everything else in the spec's Definition of Done is done.

---

## Config and Environment Changes

- **None for operators.** No new environment variables, no config files, no database migrations, no new
  endpoints. The certified-claims ledger location is unchanged
  (`runs/goal-session-mcp-loop/state/certified-claims.jsonl`, already written by the build pipeline's gate).
- Internal note (no operator action): the evidence read path now self-maps a certified score-column claim to
  its badge even if the written record omits the explicit signal key. This only affects which badge a
  *certified* claim lights — it never makes anything "Proven" that the referee did not certify.

---

## Known Limitations

- The proof panel shows the **single SPY control** the referee actually computed (honestly labeled
  "vs SPY"). The broader control set mentioned in the product vision (QQQ / sector ETF / random same-sector)
  is a deliberate future step — showing controls that were not computed would violate the project's honesty
  rule.
- Displayed numbers are re-formatted for readability (the edge and control as a signed percentage, the
  significance value to four figures) but are taken directly from what the engine certified — they are not
  recomputed in the browser.
- The frontend has no installed JavaScript test runner; its unit tests are run by transpiling with the
  bundled TypeScript compiler and executing the result (documented in the dev handoff). This is a
  tooling/environment note, not a product limitation.
