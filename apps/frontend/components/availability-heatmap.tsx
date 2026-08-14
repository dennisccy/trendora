"use client";

import { useCallback, useMemo, useState } from "react";
import { CalendarDays, Loader2 } from "lucide-react";

import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/empty-state";
import { shouldShowAvailabilityEmptyState } from "@/lib/availability-empty-state";
import { toMonthBands } from "@/lib/availability-month-bands";
import { cn } from "@/lib/utils";
import { formatIsoDate } from "@/lib/dates";
import type { AvailabilityCell, AvailabilityResponse } from "@/lib/api";

/**
 * J-61 — the per-trading-date availability heatmap on `/data`.
 *
 * READ-ONLY presentation of the `GET /api/data/availability` payload (one cell per benchmark trading
 * day), encoding TWO DELIBERATELY SEPARATE signals that must never look alike while meaning different
 * things:
 *   - cell FILL = price-data completeness (`symbols_with_bars` density) — filled by the Fetch job — on
 *     a J-13 (iter-20) MONOTONIC SINGLE-HUE blue scale (dark → bright across the six buckets, each step
 *     validated distinct). This reverses the prior J-74 multi-hue ramp, whose "full" bucket was amber
 *     (this page's warning colour) and collided with the green bucket beside it.
 *   - ring INDICATOR = whether an immutable scored snapshot exists — produced by the Backfill job — in a
 *     dedicated violet `--snapshot` token outside the fill scale's hue family (and no longer `--pos`
 *     green, which collided with the old green bucket).
 * A day can be fully-filled but ringless (a Backfill gap) or ringed on a partial-fill day — the two
 * signals vary independently. A two-group legend + the header/caption copy name the Fetch→fills /
 * Backfill→scores mapping explicitly; hover/focus a cell for exact figures (date, symbols-with-bars /
 * total, snapshot yes/no) via `title`/`aria-label` and the readout panel. A SPARSE day (e.g. 3-of-158) is
 * visually distinct from a FULL day. The day-number stays legible in EVERY bucket (a per-bucket
 * text-contrast token, J-70). All dates render `yyyy-MM-dd` via the shared `formatIsoDate` (J-42).
 *
 * The colour scale + the per-bucket day-number text-contrast classes are defined ONCE here from the
 * design-token system (the `heat-*` / `heat-text-*` / `snapshot` Tailwind tokens registered in
 * tailwind.config.ts, backed by globals.css CSS vars) — NO hardcoded hex lives in an individual cell
 * (anti-goal: No magic numbers / coherence invariant 10). This is a presentation-only re-style of the
 * SAME payload: no new fetch, no recompute, all J-61/J-70 data-* attributes and behaviours preserved.
 *
 * Clicking a day, or shift-clicking a second day to select a range, calls `onPrefillRange(start, end)`
 * — the page wires that into the JOB FORM's Start/End inputs. These are JOB PARAMETERS, NEVER the global
 * as-of viewing control (J-18): this component never touches `setAsOf`. The density→color mapping is pure
 * frontend presentation (no numeric classification is sent to or computed by the backend; no config knob).
 *
 * iter-5 nested-interactive guard: each day is a single `<button>` (the click target); the snapshot
 * marker and the hover tooltip are non-interactive `<span>`s INSIDE it — no nested interactive element.
 *
 * ops-hardening iter-57 (J-06 closure): the payload now carries `stale`/`served_dataset_version` (see
 * `AvailabilityResponse` in `lib/api.ts`). `stale: true` means the backend served the MOST RECENT
 * persisted reading rather than the current in-flight one (an ingest is mid-flight; the payload's real
 * cells are shown, exactly as before) — this component now renders a calm stale notice above the grid
 * in that case (mirrors the Coverage panel's existing `coverage-stale-notice` treatment, same tone, same
 * tokens, and — iter-58 — the SAME wording pattern: "as of a prior scan (version …) — refreshes on the
 * next data job"). `stale: false` with non-empty cells renders unchanged.
 *
 * ops-hardening iter-58 (audit B2 + B5 fixes): the backend now only reports `stale: true` when a job is
 * GENUINELY in flight (`app.engine.data_manager.availability_from_storage`), so this notice can no
 * longer persist indefinitely with nothing running. Separately (B5), the empty-state gate below no
 * longer reads `cells.length === 0` alone — it reads the extracted, unit-tested
 * `shouldShowAvailabilityEmptyState` (`lib/availability-empty-state.ts`), which also requires `!stale`.
 * A persisted row that happens to be BOTH stale and empty (a narrow precondition) now falls through to
 * the stale banner above with no grid below it, rather than the "No availability yet" empty state —
 * that message stays reserved strictly for a DB where no row has ever been persisted.
 *
 * Calendar layout: the grid's slot list comes from `toMonthBands` (`lib/availability-month-bands.ts`),
 * extracted here so it is unit-testable under `node` (same convention as
 * `shouldShowAvailabilityEmptyState` above). It walks every calendar day of each month, so a non-trading
 * day (weekend or market holiday, absent from the payload by construction) occupies an EMPTY grid
 * position and every real cell stays under its own weekday column. The previous inline version offset
 * only the 1st of the month and then packed the cells consecutively, which drifted each day one column
 * left per skipped date and made the heatmap look as though it charted weekends and holidays — see that
 * module's header for the measured before/after. Purely positional: the cells, the payload, and every
 * behaviour below are unchanged, and a blank carries no `data-testid`, so the
 * `[data-testid="availability-cell"]` set is exactly the payload's trading days as before.
 */

type DensityBucket = 0 | 1 | 2 | 3 | 4 | 5;

/** Map a day's coverage fraction (symbols_with_bars / total_symbols) to a 6-step density bucket. Pure
 *  presentation — a frontend-only sequential ramp; no magic number reaches the backend derivation. A
 *  zero-coverage day is bucket 0 (visibly empty); a fully-covered day is bucket 5. */
function densityBucket(withBars: number, total: number): DensityBucket {
  if (total <= 0 || withBars <= 0) return 0;
  const frac = withBars / total;
  if (frac >= 1) return 5;
  if (frac >= 0.75) return 4;
  if (frac >= 0.5) return 3;
  if (frac >= 0.25) return 2;
  return 1;
}

/** J-13 (iter-20) — the MONOTONIC SINGLE-HUE (blue) density scale (low → full), defined ONCE from the
 *  design-token system: each `bg-heat-N` is the SAME hue at increasing lightness, registered in
 *  tailwind.config.ts (CSS vars in globals.css) — NO per-cell hex. The top ("full") bucket is
 *  deliberately NOT amber (this page's warning colour). The six steps are validated distinct (monotone
 *  lightness, a minimum lightness gap between neighbours, the darkest step still readable on the
 *  surface), so a sparse 3-of-158 day still reads as an obviously different shade from a full day — not
 *  just "not amber." Each bucket carries a matching-hue border. */
const BUCKET_CLASS: Record<DensityBucket, string> = {
  0: "bg-heat-0 border border-border",
  1: "bg-heat-1 border border-heat-1",
  2: "bg-heat-2 border border-heat-2",
  3: "bg-heat-3 border border-heat-3",
  4: "bg-heat-4 border border-heat-4",
  5: "bg-heat-5 border border-heat-5",
};

/** J-70/J-74 — per-bucket day-number text token (design tokens only — NO hardcoded hex). The two darkest
 *  buckets (0–1) take near-white `text-heat-text-N` (== `--text`); the four brighter buckets (2–5, same
 *  blue hue at increasing lightness — J-13/iter-20) take the dark base (== `--bg`) so the number reads
 *  with strong contrast on every fill — including the dark-on-dark empty/low-density case. Defined ONCE
 *  here. */
const BUCKET_TEXT_CLASS: Record<DensityBucket, string> = {
  0: "text-heat-text-0",
  1: "text-heat-text-1",
  2: "text-heat-text-2",
  3: "text-heat-text-3",
  4: "text-heat-text-4",
  5: "text-heat-text-5",
};

/** The legend rows — each maps a density bucket's COLOUR to its coverage level (the figures themselves
 *  are on hover; this is the colour→level key J-74 adds). */
const LEGEND: { bucket: DensityBucket; label: string }[] = [
  { bucket: 0, label: "none" },
  { bucket: 1, label: "<25%" },
  { bucket: 2, label: "25–50%" },
  { bucket: 3, label: "50–75%" },
  { bucket: 4, label: "75–<100%" },
  { bucket: 5, label: "full" },
];

const WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"] as const;

export function AvailabilityHeatmap({
  state,
  selectedStart,
  selectedEnd,
  onPrefillRange,
}: {
  state:
    | { kind: "loading" }
    | { kind: "error" }
    | { kind: "ok"; data: AvailabilityResponse };
  /** The current job-form Start/End (so the heatmap highlights the prefilled selection). */
  selectedStart?: string;
  selectedEnd?: string;
  /** Prefill the JOB FORM's Start/End from a clicked day (start == end) or a shift-click range. NEVER the
   *  global as-of control. */
  onPrefillRange: (start: string, end: string) => void;
}) {
  // Hover tooltip: the cell currently hovered/focused (exact figures shown for it). Non-interactive.
  const [hovered, setHovered] = useState<AvailabilityCell | null>(null);
  // Shift-click range anchor: the first day of an in-progress range selection.
  const [anchor, setAnchor] = useState<string | null>(null);

  // Month bands DESCENDING (newest month first, top→bottom) so the most recent history is visible without
  // scrolling. Each month's INTERNAL day order stays ascending (a calendar reads left→right, top→bottom).
  const bands = useMemo(
    () =>
      state.kind === "ok" ? toMonthBands(state.data.cells).slice().reverse() : [],
    [state],
  );

  const handleDayClick = useCallback(
    (cell: AvailabilityCell, shiftKey: boolean) => {
      if (shiftKey && anchor) {
        // Complete a range: order the two endpoints ascending and prefill [start, end].
        const [start, end] = anchor <= cell.date ? [anchor, cell.date] : [cell.date, anchor];
        onPrefillRange(start, end);
        setAnchor(null);
      } else {
        // A plain click selects a single day (start == end) and arms it as a range anchor.
        setAnchor(cell.date);
        onPrefillRange(cell.date, cell.date);
      }
    },
    [anchor, onPrefillRange],
  );

  const inSelectedRange = useCallback(
    (iso: string) => {
      if (!selectedStart || !selectedEnd) return false;
      const lo = selectedStart <= selectedEnd ? selectedStart : selectedEnd;
      const hi = selectedStart <= selectedEnd ? selectedEnd : selectedStart;
      return iso >= lo && iso <= hi;
    },
    [selectedStart, selectedEnd],
  );

  return (
    <Card className="p-0" data-testid="availability-heatmap">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <CalendarDays className="h-4 w-4 text-text-faint" aria-hidden />
          <h2 className="text-sm font-semibold text-text">Per-date availability</h2>
        </div>
        <p className="mt-0.5 text-xs text-text-faint">
          Two separate signals per trading day: the cell fill is how many symbols have price data
          (filled by Fetch), and the ring is whether a scored snapshot exists (produced by Backfill). A
          day can have one without the other — that is exactly a Backfill gap. Descriptive metadata read
          from the dataset, not a recomputed score. Click a day to prefill the job dates below;
          shift-click a second day for a range. (These are job parameters — they never change the global
          as-of date.)
        </p>
      </div>

      {state.kind === "ok" && state.data.stale ? (
        <p
          className="border-b border-border bg-surface-2 px-4 py-2 text-xs text-text-muted"
          data-testid="availability-stale-notice"
        >
          Data as of a prior scan (version {state.data.served_dataset_version}) — refreshes on the next data job
        </p>
      ) : null}

      {state.kind === "loading" ? (
        <div className="flex items-center gap-2 p-6 text-sm text-text-muted" data-testid="availability-loading">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          Loading availability…
        </div>
      ) : null}

      {state.kind === "error" ? (
        <div className="p-4">
          <p className="text-sm text-text-muted" data-testid="availability-error">
            Availability could not load from the API. No cells are shown rather than fabricated values.
          </p>
        </div>
      ) : null}

      {state.kind === "ok" && shouldShowAvailabilityEmptyState(state.data) ? (
        <div className="p-4">
          <EmptyState
            icon={CalendarDays}
            title="No availability yet"
            description="There are no stored trading days to chart. Fetch real EOD prices to populate the dataset, then the per-date availability appears here."
          />
        </div>
      ) : null}

      {state.kind === "ok" && state.data.cells.length > 0 ? (
        <div className="space-y-4 p-4">
          {/* Legend (TWO labeled, unmistakably separate groups — J-13/iter-20) + hovered-day figures */}
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="flex flex-col gap-1.5" data-testid="availability-legend">
              <div className="flex flex-wrap items-center gap-2" data-testid="availability-legend-density">
                <span className="text-[10px] font-semibold uppercase tracking-wide text-text-faint">
                  Price data — cell fill
                </span>
                <div className="flex items-center gap-1">
                  {LEGEND.map(({ bucket, label }) => (
                    <span key={bucket} className="flex items-center gap-1" title={label}>
                      <span className={cn("h-3 w-3 rounded-sm", BUCKET_CLASS[bucket])} aria-hidden />
                      <span className="text-[10px] text-text-faint">{label}</span>
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-2" data-testid="availability-legend-snapshot">
                <span className="text-[10px] font-semibold uppercase tracking-wide text-text-faint">
                  Scored snapshot — indicator
                </span>
                <span className="flex items-center gap-1 text-[10px] text-text-faint">
                  <span className="relative inline-flex h-3 w-3 items-center justify-center" aria-hidden>
                    <span className="h-3 w-3 rounded-sm bg-heat-3 ring-2 ring-snapshot ring-offset-0" />
                  </span>
                  a scored snapshot exists for that day
                </span>
              </div>
            </div>

            {/* The exact figures for the hovered/focused day — read verbatim from the cell, no recompute. */}
            <div className="num text-xs text-text-muted" aria-live="polite" data-testid="availability-hover-readout">
              {hovered ? (
                <span>
                  <span className="text-text">{formatIsoDate(hovered.date)}</span>
                  {" · "}
                  <span className="text-text">
                    {hovered.symbols_with_bars}/{hovered.total_symbols}
                  </span>{" "}
                  symbols ·{" "}
                  {hovered.snapshot_exists ? (
                    <span className="text-snapshot">snapshot yes</span>
                  ) : (
                    <span className="text-text-faint">snapshot no</span>
                  )}
                </span>
              ) : (
                <span className="text-text-faint">Hover or focus a day for exact figures</span>
              )}
            </div>
          </div>

          {/* Month-banded calendar grid (weeks as rows, Monday-first). Two month bands per row on a normal
              viewport (collapsing to one column on narrow screens) so more history is visible without
              excessive scrolling. Scrolls within the card on a tall history; never truncates a covered day. */}
          <div className="grid max-h-[28rem] grid-cols-1 gap-x-5 gap-y-5 overflow-auto pr-1 md:grid-cols-2">
            {bands.map((band) => (
              <div key={band.key} data-testid="availability-month" data-month={band.label}>
                <div className="mb-1 num text-xs font-medium text-text-muted">{band.label}</div>
                <div className="grid grid-cols-7 gap-1">
                  {WEEKDAYS.map((w) => (
                    <div key={w} className="text-center text-[10px] text-text-faint">
                      {w}
                    </div>
                  ))}
                  {band.slots.map((slot, slotIndex) => {
                    // A non-trading day (weekend / holiday) or a leading offset: an empty grid position,
                    // which is what holds every real day under its own weekday column.
                    if (slot.kind === "blank") {
                      return <span key={`blank-${slotIndex}`} aria-hidden />;
                    }
                    const { cell } = slot;
                    const bucket = densityBucket(cell.symbols_with_bars, cell.total_symbols);
                    const selected = inSelectedRange(cell.date);
                    const isAnchor = anchor === cell.date;
                    return (
                      <button
                        key={cell.date}
                        type="button"
                        data-testid="availability-cell"
                        data-date={cell.date}
                        data-bucket={bucket}
                        data-symbols={cell.symbols_with_bars}
                        data-total={cell.total_symbols}
                        data-snapshot={cell.snapshot_exists ? "yes" : "no"}
                        data-selected={selected ? "yes" : "no"}
                        aria-pressed={selected}
                        aria-label={`${cell.date}: ${cell.symbols_with_bars} of ${cell.total_symbols} symbols have price data from Fetch; ${cell.snapshot_exists ? "a scored snapshot exists from Backfill" : "no scored snapshot yet — a Backfill gap"}`}
                        title={`${cell.date} · ${cell.symbols_with_bars}/${cell.total_symbols} symbols have price data (Fetch) · ${cell.snapshot_exists ? "scored snapshot exists (Backfill)" : "no snapshot yet — Backfill gap"}`}
                        onMouseEnter={() => setHovered(cell)}
                        onMouseLeave={() => setHovered((h) => (h?.date === cell.date ? null : h))}
                        onFocus={() => setHovered(cell)}
                        onBlur={() => setHovered((h) => (h?.date === cell.date ? null : h))}
                        onClick={(e) => handleDayClick(cell, e.shiftKey)}
                        className={cn(
                          "relative flex h-7 items-center justify-center rounded-sm text-[10px] font-medium tabular-nums transition",
                          BUCKET_CLASS[bucket],
                          BUCKET_TEXT_CLASS[bucket],
                          "hover:brightness-110 hover:ring-1 hover:ring-accent",
                          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                          (selected || isAnchor) && "ring-2 ring-accent ring-offset-1 ring-offset-surface",
                          // the snapshot ring marker — a dedicated violet token, distinct from the accent
                          // selection ring AND from every heat-* density hue (J-13/iter-20)
                          cell.snapshot_exists && !selected && !isAnchor && "ring-2 ring-snapshot",
                        )}
                      >
                        {/* the day-of-month number — non-interactive text inside the single button */}
                        <span aria-hidden>{slot.day}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          <p className="border-t border-border pt-2 text-[11px] text-text-faint">
            Cell fill = symbols with a bar on that day ÷ total stored symbols ({state.data.total_symbols}),
            filled by Fetch — one hue from dark (none) to bright (full; see the legend above). The ring =
            an immutable scored snapshot exists for that day, produced by Backfill, in a distinct colour
            never used by the fill. A trading day with no non-benchmark bars is shown honestly (the lowest
            level), never omitted as if covered. Only trading days have cells — weekends and market
            holidays are left empty, so every day sits under its own weekday column.
          </p>
        </div>
      ) : null}
    </Card>
  );
}
