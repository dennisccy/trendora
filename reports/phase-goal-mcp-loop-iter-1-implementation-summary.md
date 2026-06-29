# goal-mcp-loop-iter-1 — Implementation Summary

**Phase:** goal-mcp-loop-iter-1
**Date:** 2026-06-29
**Written by:** developer

---

## Features Implemented

- **Evidence status on every score**: Each stock score on the Stocks leaderboard (Leadership, Entry Quality,
  Risk) and on a stock's detail page now shows a small "Proven / Not yet proven" chip right next to it. It
  tells the user, at a glance, whether hard out-of-sample evidence backs that score.
- **Evidence ledger page**: A new "Evidence" page (reachable from the left navigation in one click) lists the
  platform's certified claims. Today the list is empty, so it shows an honest "No certified claims yet"
  message and explains exactly what each future certified claim will show.
- **Honest "Not yet proven" everywhere**: Because no claim has been certified yet, every score honestly reads
  "Not yet proven." Nothing is presented as a confident, proven number — which is the whole point of this
  evolution of the product.
- **Evidence data endpoint**: A new read-only `/api/evidence` endpoint serves the certified-claims ledger to
  the screens above. It only reads and re-displays what the statistical referee has certified; it never
  computes proven-ness itself and never changes any score.

---

## Changed Behavior

- **Stocks leaderboard & stock detail**: Previously each score showed only its A–E bucket and 0–100 value.
  Now each score ADDITIONALLY shows an evidence-status chip beside it. The scores themselves are unchanged
  (byte-for-byte identical to before) — the chip is purely additional information.
- **Left navigation**: A new "Evidence" item now appears (after "Research"). No other navigation changed.

---

## Backend-Only Items

- None. Every backend addition this iteration (`/api/evidence`) is wired to the UI (the badges and the
  Evidence page).

---

## Incomplete Items (deferred by design)

- **"Proof drill-down" (journey J-02) and "regime-conditioned evidence" (journey J-04)**: Both require at
  least one referee-certified claim to exist. The ledger is empty this iteration, so these are intentionally
  deferred to a later iteration that proposes and certifies a claim. The screens that will host them (the
  badge link target and the Evidence claim rows) are already built and tested.
- **"Proven" badge linking to its backing claim, and claim rows linking back to their surface**: Built and
  unit-tested, but only visible once a claim is certified (today everything is "Not yet proven").
- **Badges on Sectors / Themes / Research labs**: Out of scope this iteration (scoped tightly to the Stocks
  surfaces + the Evidence page); a later iteration can extend the same badge across more surfaces.

---

## Config and Environment Changes

- `config.yaml` → new `evidence.ledger_path` setting — points at the certified-claims ledger file
  (`runs/goal-session-mcp-loop/state/certified-claims.jsonl`), the SAME file the platform's certification
  gate writes to. Default is set; no action needed by operators.
- `TRENDORA_LEDGER_PATH` (optional environment variable) — if set, overrides the ledger file location at
  runtime. Normally unset; the config default is correct out of the box.
- No database migration and no schema change.

---

## Known Limitations

- The evidence ledger is **empty today**, so by design every score reads "Not yet proven" and the Evidence
  page shows its empty state. This is the correct, honest behavior for this iteration — not a bug.
- The certification writer does not yet tag a certified claim with which on-screen score it backs. That
  wiring (so a future certified claim actually flips a specific badge to "Proven") is deliberately deferred to
  the later certified iteration. Until then, even a hypothetical certified claim would safely stay
  "Not yet proven" on the badges (fail-safe).
- A fetch failure of the evidence data degrades safely: badges fall back to "Not yet proven" and the rest of
  the page is unaffected — the platform never fabricates a "Proven."
