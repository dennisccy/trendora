# Goal iter-12 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future-iter-12
**Date:** 2026-05-31
**Written by:** developer

---

## Features Implemented

- **Methodology / Glossary page (`/methodology`)**: A new page that explains, in plain language, what every setup status (Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist) and the VCP price pattern mean — each with the exact thresholds that define it and a worked example. This closes the project's final must-have (J-12).
- **Sidebar "Methodology" link**: A new top-level navigation item (book icon) placed after Watchlist, so the page is discoverable.
- **Inline badge definitions on the Stocks page**: Every setup badge and the VCP badge on `/stocks` now has a small "info" affordance. Hovering, keyboard-focusing, or tapping it reveals the same plain-language definition shown on the Methodology page.
- **Single config-backed catalog**: The page, the tooltips, and the Stocks "Setup" filter all read ONE source — a new `methodology` section in `config.yaml`. Adding an entry there (or tuning a threshold) updates every place at once, with no code change.
- **Always-matching thresholds**: The numbers shown for each status/pattern are not re-typed in the glossary — they are pulled live from the same config values the scanner itself uses, so the glossary can never drift from the engine.

---

## Changed Behavior

- **Stocks page "Setup" filter**: Previously its options were a fixed list hard-coded in the page. Now the options come from the methodology catalog (the same six statuses, now config-sourced). If the catalog cannot be loaded, the filter automatically falls back to the statuses present in the current data, so the leaderboard and all its filters keep working.
- **Stocks page setup / VCP badges**: Previously a setup badge was a plain chip and the VCP badge showed only its per-row reason on hover. Now each also exposes the generic catalog definition via an inline info tooltip. The per-row VCP reason and the per-row "Reason" column are unchanged.

---

## Backend-Only Items

- None. Every backend addition (the `GET /api/methodology` endpoint and the catalog it serves) is surfaced in the UI (the Methodology page, the badge tooltips, and the Setup filter).

---

## Incomplete Items

- None. All spec items are implemented: the page, the inline tooltips, the config-driven catalog, the boot-time threshold validator, the completeness assertion, and the full backend + frontend test coverage. The optional (out-of-scope) Stock-Detail tooltip and any second pattern were intentionally not added.

---

## Config and Environment Changes

- `config.yaml` — new top-level `methodology:` section: an `intro` plus an ordered list of entries (the six setup statuses + the VCP pattern). Each entry carries plain-language copy (meaning + example) and threshold rows that **reference** existing config keys (e.g. `decision_rules.actionable.leadership`, `patterns.vcp.min_contractions`) rather than re-typing numbers. No new environment variables. No database/schema change.

---

## Known Limitations

- The methodology catalog is read-only and explanatory; it does not let a user edit thresholds from the UI (a config-editing UI was explicitly out of scope).
- The inline badge tooltip is a small pop-over rendered inside the Stocks leaderboard table. On the very last visible row it can extend just past the table's scroll area; the same definition is always fully available on the dedicated `/methodology` page, and the tooltip text is present in the DOM as soon as it is opened.
- Browser-level UI verification is normally performed by the dedicated browser-QA step. The new capability is fully covered by backend unit/API tests, a clean production build (the new route compiles and is type-checked), and a live API check of `GET /api/methodology`.
