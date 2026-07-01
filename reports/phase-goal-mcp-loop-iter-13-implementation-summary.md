# goal-mcp-loop-iter-13 — Implementation Summary

**Phase:** goal-mcp-loop-iter-13
**Date:** 2026-07-01
**Written by:** developer

---

## Features Implemented

- **"Proven" evidence badge on a multi-factor combination**: On the Research → Multi-factor combination lab
  (`/research/factor-combination`), the Combined (composite) cohort row now shows an honest evidence chip.
  It reads **"Proven"** only for one specific, pre-registered pairing — relative-strength leaders (vs SPY, 3
  months) that are ALSO near their 52-week high — at the 20-day horizon, because that pairing survived the
  statistical referee out-of-sample. Every other combination the user composes reads **"Not yet proven"**.
- **New certified-claim row on the Evidence ledger**: The Evidence page (`/evidence`) now lists a 6th
  certified claim for that combination. It shows the hypothesis (both conditions + the 20-day horizon), the
  out-of-sample verdict (passed), the realized edge over the sealed hold-out (**+4.69%**), the comparison
  versus SPY (**+4.69%** better out-of-sample), the registration date, the forward-walk status ("Pending"),
  and a link back to the Multi-factor combination lab it backs.
- **Click-through between the two surfaces**: The "Proven" badge on the combination lab deep-links straight
  to its backing row on the Evidence ledger, so a user can audit exactly why it is considered proven.

Both surfaces read the SAME single source of truth (the `GET /api/evidence` feed); nothing is recomputed in
the page.

---

## Changed Behavior

- **Evidence ledger (`/evidence`)**: Previously listed 5 certified claims. Now lists 6 — the new one is the
  combination edge. The prior 5 rows are unchanged.
- **Multi-factor combination lab (`/research/factor-combination`)**: Previously purely descriptive (cohort
  statistics only). Now the composite cohort row also carries an evidence status. The statistics themselves
  are unchanged.

---

## Backend-Only Items

- None. Everything added this phase is visible in the UI. No new backend endpoint or module was created — the
  new combination claim is simply one more entry in the existing certified-claims ledger, served by the
  existing Evidence feed.

---

## Incomplete Items

- None deferred from this phase's scope. The single target journey (J-08) is implemented end-to-end
  (data → feed → both UI surfaces) and unit/live-verified. The on-screen badge-flip screenshots are produced
  by the separate browser-QA step that runs after this one.

---

## Config and Environment Changes

- None. No new environment variables, config settings, or migrations. The combination's economic rationale
  was already pre-registered in the existing candidate configuration; no config was edited this phase.

---

## Known Limitations

- **Reaching the "Proven" state takes one deliberate action.** On first load the combination lab shows its
  configured default pairing (relative strength + low volatility), which did NOT pass the referee, so it
  honestly reads "Not yet proven". To see "Proven", the user must compose the certified pairing (relative
  strength + proximity to 52-week high) at the 20-day horizon. This is intentional honesty, not a bug.
- **The combination edge never appears on individual stocks.** It is a research-lab / ledger fact only; it
  deliberately does NOT light up any per-stock score badge on the Stocks pages (those remain exactly as
  before — only the Leadership score reads "Proven" there).
- **This is decision-support evidence, not a recommendation.** The badge reports a historical, out-of-sample
  statistic; it makes no return promise, price target, or buy/sell call.
