# goal-mcp-loop-iter-12 — Implementation Summary

**Phase:** goal-mcp-loop-iter-12
**Date:** 2026-07-01
**Written by:** developer

---

## Features Implemented

<!-- Plain language, for operators — what it does, not how. -->

- **Combination-edge exploration (internal only)**: Trendora's statistical "referee" can now test
  **two-factor combinations** of stock characteristics — not just single factors. This iteration ran a
  small, fixed, hand-picked list of three sensible combinations through the referee and recorded the honest
  results in an INTERNAL scratchpad ledger. Nothing about this is visible to a user yet.
- **A curated shortlist of three combinations was registered** (so the search stays disciplined and never
  "data-mines" thousands of random pairings):
  1. Strong-momentum leaders that are also calm/low-volatility.
  2. Top overall-leadership names that are also calm/low-volatility.
  3. Strong-momentum leaders that are also near their 52-week high (breakout-ready).
- **The referee gave an honest verdict on each.** The two "obvious" calm-plus-momentum combinations did NOT
  hold up out-of-sample at the 20-day horizon (their extra "calm" filter actually hurt the result), so they
  were recorded as **not proven**. The third — strong-momentum leaders near their 52-week high — **did hold
  up strongly out-of-sample**, comfortably passing even the strict user-facing bar. That gives the next
  iteration a real, evidence-backed winner to display.

---

## Changed Behavior

<!-- Existing functionality that now works differently. -->

- **None visible to users.** Every existing page, number, and evidence badge behaves exactly as before. The
  user-facing "proven" evidence list is byte-for-byte unchanged. This iteration only added internal search
  machinery and an internal record of what it found.

---

## Backend-Only Items

<!-- Implemented in backend, not wired to any UI. -->

- `app.engine.triad_scan.explore_combination_staging` — runs the three registered combinations through the
  referee and records each verdict in the internal staging ledger. No UI, no API endpoint — internal only.
- The internal staging ledger (`runs/goal-session-mcp-loop/state/staging-ledger.jsonl`) grew from 4 to 7
  recorded entries. This file is never served to any page and is never shown to a user.
- The recorded winner (strong-momentum leaders near their 52-week high) is the intended basis for the NEXT
  iteration to promote and finally show on the Combination lab + Evidence pages (the "J-08" journey).

---

## Incomplete Items

<!-- Partially implemented or deliberately deferred. -->

- **Showing the combination edge to users (journey J-08)** is deliberately deferred to the next iteration.
  This iteration only builds the evidence and records it internally; it does not display anything. This
  mirrors the proven two-step pattern used before (discover internally first, then surface next iteration) so
  a weak result can never be accidentally published.

---

## Config and Environment Changes

<!-- New settings / config file changes. -->

- `config.yaml` — added a new `triad.combination_candidates` section holding the three registered
  combinations (each with the two factors, the 20-day horizon, and a one-line plain-English rationale). No
  environment variables, no database migration, no new services.
- `project-extensions/proposer-guidance.md` — added a section (§4.2) documenting the same three combinations
  and their rationale, so the fixed shortlist has a single, auditable source of truth.

---

## Known Limitations

<!-- Honest constraints. -->

- **Two of the three combinations were "not proven."** This is by design and is a sign the system is being
  honest, not a bug — the referee refuses to bless a pattern that does not survive out-of-sample. Only the
  one genuinely strong combination passed.
- **The internal record can only be regenerated with the full daily database** (the large committed dataset
  the live app uses), not with the small, fast test dataset. On the small test dataset the referee correctly
  reports "not enough data" for every combination. Because of this, the internal record is verified by a
  frozen "golden" test rather than recomputed on the fly — the same approach already used for the user-facing
  evidence list.
- **No user-visible change and no new page or endpoint this iteration.** If you open the app you will see no
  difference; the value of this iteration is the recorded evidence that unlocks the next one.
