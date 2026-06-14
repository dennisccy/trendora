**Verdict:** COHERENCE-PASS

## Iteration 16 — Availability heatmap readability + keyboard as-of stepping

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration index:** 16
**Snapshot SHA:** 1fd6f3c5a3cbf82616dd5252b6db4deda120a6c9
**Files changed:** `apps/frontend/components/availability-heatmap.tsx`, `apps/frontend/components/asof-calendar.tsx`, `runs/.../telemetry.jsonl`

---

## Step 1 — Data Contract check

**Registered values touched this iteration:**

### J-70 — Per-date availability counts (`GET /api/data/availability`)

Blueprint contract: "Per-date availability counts" — computed once by `data_manager`, served by `GET /api/data/availability`; frontend re-formats only.

Diff evidence:
- `availability-heatmap.tsx`: the only change to the data-consumption path is `.slice().reverse()` on the result of `toMonthBands(state.data.cells)` (line 144 post-diff), reversing the order of month bands for descending display. Each band's internal day order is unchanged. No new fetch, no new computation, no new endpoint.
- `BUCKET_TEXT_CLASS` (new constant, lines 62–68) maps `DensityBucket` to design-token CSS classes (`text-text` / `text-bg`) — a presentation re-styling of an already-displayed cell element. The density bucket itself is read verbatim from the served `data-bucket` value; nothing is recomputed.
- The two-up grid (`md:grid-cols-2`, line 259 post-diff) is a layout change to the wrapper `<div>`, not a change to the data consumption path.
- All test-id and data attributes (`data-testid="availability-cell"`, `data-bucket`, `data-date`, `data-symbols`, `data-total`, `data-snapshot`, `data-testid="availability-month"`) are preserved verbatim.

**Result: no violation.** Pure re-render of the same canonical payload.

### J-71 — Resolved as-of date + available dates (ONE global state)

Blueprint contract: "Resolved as-of date + available dates" — `setAsOf` is the single global setter; the calendar popover is a renderer of that state, never a second state owner.

Diff evidence:
- `asof-calendar.tsx`: `stepAsOf(dir)` (lines 118–131 post-diff) reads `sortedAsc` and `asOf` from props (already passed in by the parent; no new endpoint call), computes an index, and calls `onSelect(isLatest ? null : landing)`. The parent wires `onSelect` directly to `setAsOf` (unchanged). This is the SAME code path as clicking a day button.
- `useState` usage in the component remains exactly one call: `const [view, setView]` (the month-view cursor). No new date state introduced. `asof-provider.tsx` is not touched.
- The `onKeyDown` handler on the dialog element (`ArrowLeft`/`ArrowRight`, lines 141–146 post-diff) is local to the component's JSX. No `window.addEventListener` or `document.addEventListener` call is present anywhere in the diff.
- The popover stays open on Arrow steps (no `onClose()` call inside `stepAsOf`); only `Escape` / day-click / outside-click close it, exactly as before.

**Result: no violation.** J-18 single-global-as-of invariant preserved; no second date state; no global listener.

**No new displayed value introduced. No duplicate computation. No non-canonical source.**

---

## Step 2 — Information Architecture check

**New pages/routes introduced:** none.

Both J-70 and J-71 modify existing components on existing surfaces:
- `/data` (Data Manager) — `availability-heatmap.tsx` is already a sub-panel of the Data Manager page, which is directly reachable from the sidebar (one click). Blueprint IA: "Data Manager `/data`" — confirmed.
- Cross-cutting as-of calendar popover — `asof-calendar.tsx` is rendered by the top-bar switcher, already reachable from every page (zero clicks beyond the top bar). Blueprint IA: "cross-cutting J-71 entry" — confirmed.

No new navigation link required. No duplicate home. No parallel shell.

**Result: no violation.**

---

## Step 3 — Subjective observations (advisory)

- **Design tokens confirmed valid:** `text-text` (maps to `var(--text)`, `tailwind.config.ts:25`) and `text-bg` (maps to `var(--bg)`, line 18) are registered design tokens, not hardcoded hex. Coherence invariant 10 satisfied.
- No formatting inconsistency introduced. The `formatIsoDate` shared formatter (`lib/dates.ts`) is used wherever dates are displayed in `asof-calendar.tsx` (unchanged).
- No label drift: the "Latest" label and its `null` semantics are preserved end-to-end in `stepAsOf` (newest date → `onSelect(null)` → same "Latest" display path as before).

**No advisory warnings.**

---

## Summary

| Check | Result | Notes |
|---|---|---|
| Data Contract — Per-date availability counts | PASS | `.reverse()` + layout tokens; canonical endpoint unchanged |
| Data Contract — Resolved as-of date | PASS | `stepAsOf` calls existing `onSelect`→`setAsOf`; no new state |
| IA — new pages/routes | PASS | None introduced |
| IA — navigation path | PASS | Both surfaces already reachable (1 click / top-bar) |
| IA — duplicate home | PASS | None |
| Invariant 10 — no hardcoded hex | PASS | `text-text`/`text-bg` are valid design tokens |
| J-18 — single global date control | PASS | No second date state; no global listener |

**Verdict: COHERENCE-PASS** — no objective violations; no advisory warnings.
