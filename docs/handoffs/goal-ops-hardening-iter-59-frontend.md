# goal-ops-hardening-iter-59 Frontend Handoff

**Phase:** goal-ops-hardening-iter-59
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete

## What Was Built

- **`/research/regime-lab` now renders an honest, contained "temporarily unavailable" state for any
  forward-return horizon that the backend could not compute under memory pressure**, instead of a blank
  cell or a fabricated value. This ships CONDITIONAL on the backend's own profiling pass finding the
  partial-degrade signal genuinely needed — it was (see the dev handoff: the iter-58 live incident
  already supplied a real reproduction of a horizon failing to complete under concurrent memory
  pressure).
- The change extends the SAME NA-cell convention already used ~8x elsewhere in `_labs.tsx`
  (`na = cell.low_sample || cell.n === 0 || value === null` -> a muted `"—"`/`"NA"` span with an
  explanatory `title` tooltip) rather than introducing a new visual treatment. `regimeCellIsNa` now
  also treats `cell.status === "unavailable"` as NA. A new small helper, `regimeNaTitle(cell, min,
  emptyLabel)`, centralizes which tooltip copy a cell gets, so a degraded cell reads
  **"Temporarily unavailable — degraded under memory pressure"** — distinct wording from the existing
  "Low sample — n below the N minimum" and "No observations" / "No stored drawdown — NA" reasons, per
  AG's standing "never hype, never reassurance language" rule.
- `RegimeReturnCell` and `RegimeMddCell` (the two cell components `RegimeLabByLabelTable` and
  `RegimeLabDecileTable` both render) were updated to check `cell.status === "unavailable"` first, ahead
  of the existing `low_sample`/`n === 0`/`value === null` checks — same component, same table structure,
  no new column, no new row shape.

## Files Changed

- `apps/frontend/app/research/_labs.tsx` -- `regimeCellIsNa` extended; new `regimeNaTitle` helper;
  `RegimeReturnCell`/`RegimeMddCell` updated to use it.
- `apps/frontend/lib/api.ts` -- `RegimeLabHorizonCell.status?: "unavailable"` and
  `RegimeLabResponse.regime_lab_status?: "unavailable"` added as additive, optional fields to the
  existing TypeScript interfaces — no existing field's shape or meaning changed.

## Tests Run

- `npx tsc --noEmit` (from `apps/frontend/`) — clean, zero errors.
- No new frontend unit test file was added for `regimeCellIsNa`/`regimeNaTitle` specifically. These two
  functions are pure and small (a boolean predicate and a 3-branch string switch), and the codebase's
  established convention for testing this class of logic (see `lib/factor-lab-evidence.ts`,
  `lib/availability-empty-state.ts`) is to extract it into a standalone `lib/*.ts` module with a
  co-located `.test.ts`. Given this iteration's one risky product-code action is the backend memory
  bound (rule 5 discipline), a refactor extracting these two functions out of the already-large
  `_labs.tsx` was deliberately not undertaken alongside it. Correctness was instead verified by: (a) a
  clean `tsc --noEmit` pass, (b) direct code read confirming the new branch is a strict prepend to the
  existing, already-tested-in-production NA logic (a degraded cell has `n === 0`, so even the OLD
  predicate would already have rendered it as NA — the new code only changes the TOOLTIP WORDING for
  that case, not whether it renders as NA), and (c) the browser-QA lane's downstream TC-11 visual check.
  Flagged here rather than silently skipped.

## Known Issues

- `RegimeLabRankIcRow` (the `rank_ic_by_horizon` row shape in `apps/frontend/lib/api.ts`) was NOT given
  a matching `status?: "unavailable"` field, even though the backend payload does carry one on a
  degraded horizon's rank-IC entry. This is not a correctness bug — a degraded rank-IC entry has
  `rank_ic: {value: null, n: 0}`, and the existing rendering already treats `value === null` as NA (a
  correct, non-fabricated "—"). The only gap is that this ONE cell type does not get the more specific
  "temporarily unavailable" tooltip wording the by-label/by-decile cells now get; it falls back to
  whatever generic NA copy the rank-IC cell already used. The plan's own scope named only
  `by_label[].by_horizon[]` and `by_decile[].by_horizon[]` for the tooltip-distinctness requirement, so
  this was left as a disclosed, intentional scope boundary rather than fixed — a candidate for a future
  iteration if the rank-IC row's own NA wording is ever revisited.
- This iteration deliberately did not touch the Regime Lab's broader UI/feature backlog (iter-33/g,
  carried) — only the conditional degrade-marker rendering described above.

---

## Fix Notes (attempt 3 — audit FAIL) — no frontend code changed; the rendering was VERIFIED VISUALLY for the first time

**No `.tsx` / `.ts` file was touched in this pass.** The audit's frontend findings are F1 (the degrade
rendering had never been seen rendered) and F2 (a degraded cell is distinguishable from an empty cohort
only on hover). F2 needs a code change, which TC-7 / DoD item 7 forbid after the browser/replay lane has
run — it is filed for iteration 60. F1 needed evidence, not code, and that is what this pass produced.

### F1 is closed: TC-11 has visual evidence, with a control arm

The bullet above that pointed at "the browser-QA lane's downstream TC-11 visual check" as verification (c)
did not survive the audit — that check never ran. UT-02 and UT-03 both SKIPPED, because arming
`TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab` requires a backend restart and the browser-QA agent's hard
rule forbids restarting the app. So the tooltip, the NA placeholder and the containment of the degraded
column were resting on a code read and a `tsc` pass alone. The audit's own recommendation was that the
developer pre-arm a fault-injected backend, since the lane structurally cannot.

Done: `runs/goal-ops-hardening-iter-59/evidence-drill/capture_degrade_ui.py` restarts the backend through
`scripts/start-backend.sh` with the fault armed (AG-10 caps intact), drives a real browser to
`/research/regime-lab` in `ANALYSIS MODE = As of date` under an as-of whose cache key is a guaranteed MISS
(so the page's OWN request enters `compute_regime_lab` and really degrades), reads the cell text and
tooltip back out of the live DOM, screenshots it, then repeats the whole thing DISARMED as a control and
leaves the process disarmed. Raw result: `pass2/tc11-degrade-ui.json`.

| | Fault ARMED | Fault DISARMED (control, same page, same as-of `2010-11-05`) |
|---|---|---|
| API `regime_lab_status` | `unavailable` | absent |
| API degraded `by_horizon` cells | 80 | 0 |
| Cells rendering the degrade tooltip | **160** (paired Fwd + MDD columns of 80 horizon cells) | **0** |
| Cell text / `title`, read from the live DOM | `NA` / **"Temporarily unavailable — degraded under memory pressure"** | n/a |
| `regime-lab-by-label` / `regime-lab-by-decile` tables present | yes / yes | yes / yes |
| Error-boundary or application-error text anywhere on the page | **none** | none |
| Rendered figures | every cell `NA` + an `n=0` chip | real values (Risk-on FWD 20D **+0.91%**, n=17440) |

Frames, all four **opened and read** rather than hashed (TC-10's binding rule), in
`reports/qa/goal-ops-hardening-iter-59-dev-evidence/`: `TC-11-degrade-rendered.png`,
`TC-11-degrade-rendered-by-label-table.png`, `TC-11-control-clean.png`,
`TC-11-control-clean-by-label-table.png`.

The control arm is the part that makes this evidence rather than a picture: a screenshot of NA cells on its
own cannot distinguish "the degrade renders honestly" from "this as-of has no data anyway". The same page
with the same as-of renders real figures when the fault is disarmed, so the NA state is caused by the
injected pressure.

**TC-11 as written is MET** — the affected horizons render a contained, honest placeholder inside the
normal table structure, never a blank crash page, never a fabricated number.

### F2 is CONFIRMED by the same frame — and left unfixed on purpose

The degraded table is visually identical to an empty cohort: the same muted `NA`, and the `n=0` drill-down
chip is still offered for a cohort that was never computed. Only the `title` tooltip separates
"Temporarily unavailable — degraded under memory pressure" from "No observations", so keyboard, touch and
screenshot review cannot tell them apart. The audit reasoned this from the source; the frame now shows it.
Not fixed here (a code change after the lane is forbidden) — filed for iteration 60, together with the
`RegimeLabRankIcRow` `status?` gap already disclosed above, which is the same class.
