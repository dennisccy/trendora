# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32
**Date:** 2026-06-18
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now view a **Downtrend Opportunity study** on the Research page (`/research`) by scrolling below the Recovery-Turn Edge lab, which shows three side-by-side ranked tables: "Held up best", "Fell hardest" (evidence only), and "Recovery-turn edge by phase" — all drawn from the same forward-return evidence already stored.
- Users can now **condition the forward-return tables on a specific market state** by selecting from the "Condition on" dropdown in the Downtrend Opportunity section (choices: Phase, Severity band, P(bear) band). The tables update to show only observations whose snapshot date fell in that market state.
- Users can now **switch the study view between Episodes and Pooled counting** using the Episodes/Pooled toggle in the Downtrend Opportunity section.
- Users can now **toggle between All-history and As-of-date scoping** for the Downtrend Opportunity study by using the page-level analysis-mode toggle (the same single global date control used by all other Research labs — no new date picker is added).
- Users can now **sort any column** in the three angle tables by clicking the column header (view-only re-sort; data is not re-fetched).
- Users can now **drill into the exact underlying observations** for any row by clicking the `N=` chip, which opens the samples in a new browser tab with a count matching the published table row.
- Users can now **see the macro feed catalog** on the Data Manager page (`/data`) in a new "Macro feed" panel, which lists the FRED provider status (live key detected or not), the four configured macro series (FRED id, publication lag, OHLCV proxy, committed-seed observation count), and whether each wiring leg (severity / regime / study) is on or off.

---

## What Changed in the Visible UI

- The `/research` page gained a new **Downtrend Opportunity Lab** section appended below the existing Recovery-Turn Edge lab. It contains a "Condition on" dimension selector, an Episodes/Pooled toggle, three ranked sortable tables, per-row `N=` chips linking to samples, a survivorship-bias caveat banner, and a macro publication-lag limitation label.
- The **"Fell hardest" angle table** carries a "Research evidence only" label and has no order or trade-execution affordance anywhere in or near the table.
- The `/research/samples` page gained a new **cohort header description** for the downtrend-opportunity kind, so the drill-down page shows a descriptive label identifying which conditioning dimension and cohort the samples belong to.
- The `/data` page (Data Manager) gained a new **Macro feed panel** after the existing missing-data diagnostic. It shows the macro provider (`fred`), env-var detection status (name only — never a key value), per-leg enable flags, and a per-series availability table. When all legs are off (the default) it shows an explicit "default figures are unchanged" note.
- A **macro publication-lag limitation label** appears in the Downtrend Opportunity lab. It discloses that macro inputs are optional and off by default, and that any macro value used for a date must have been published on or before that date — a walled or uncommitted series shows NA, never a fabricated value.

---

## What Old Behavior Changed

- No existing figures, tables, or panels changed. The Downtrend Opportunity study is purely additive — existing event-study, regime-setup-pattern, and recovery-turn-edge figures on `/research` are byte-identical to before. The Dashboard market-phase panel is unchanged. The Risk-Off gate is unchanged.

---

## Not Visible Yet

- **Live FRED macro fetch**: The FRED macro provider exists in the backend and the Data Manager shows its catalog, but there is no UI button or import flow to trigger a live macro pull this iteration. Setting `FRED_API_KEY` in the environment wires the provider, but the actual fetch must be run outside the app UI. Until then, the Data Manager macro panel shows the committed offline seed counts and marks the live key as "not set (NA)" if the env var is absent.
- **Macro-conditioned figures**: All three macro wiring legs (severity, regime-switching, study conditioning) ship config-default-OFF, so no live served figure is currently influenced by macro data. The publication-lag label is shown pre-emptively even though the macro path is inactive by default.
