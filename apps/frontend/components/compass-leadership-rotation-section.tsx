"use client";

import { AlertTriangle } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CompassResponse, CompassRotationKind, CompassRotationRow } from "@/lib/api";

type RotationGroupKind = "sector" | "theme";
type RotationSideKey = "gaining" | "losing";

const KIND_LABEL: Record<RotationGroupKind, string> = {
  sector: "Sector",
  theme: "Theme",
};

const SIDE_LABEL: Record<RotationSideKey, string> = {
  gaining: "Gaining",
  losing: "Losing",
};

const EMPTY_SIDE_TEXT: Record<RotationGroupKind, Record<RotationSideKey, string>> = {
  sector: {
    gaining: "No sector gained ground beyond the threshold this session.",
    losing: "No sector lost ground beyond the threshold this session.",
  },
  theme: {
    gaining: "No theme gained ground beyond the threshold this session.",
    losing: "No theme lost ground beyond the threshold this session.",
  },
};

function RotationRow({ row }: { row: CompassRotationRow }) {
  return (
    <li className="flex items-start justify-between gap-3 text-sm">
      <Link href={row.drill_href} className="text-text hover:underline">
        {row.label}
      </Link>
      <span className="num shrink-0 text-xs text-text-muted">
        {row.from} &rarr; {row.to} ({row.delta > 0 ? "+" : ""}
        {row.delta}) &middot; {row.direction_word}
      </span>
    </li>
  );
}

function RotationSide({ kind, side, rows }: { kind: RotationGroupKind; side: RotationSideKey; rows: CompassRotationRow[] }) {
  return (
    <div className="space-y-1.5" data-testid={`compass-leadership-rotation-${kind}-${side}`}>
      <Badge variant="default">{SIDE_LABEL[side]}</Badge>
      {rows.length === 0 ? (
        <p className="text-xs text-text-muted" data-testid={`compass-leadership-rotation-${kind}-${side}-empty`}>
          {EMPTY_SIDE_TEXT[kind][side]}
        </p>
      ) : (
        <ul className="space-y-1.5" data-testid={`compass-leadership-rotation-${kind}-${side}-list`}>
          {rows.map((row) => (
            <RotationRow key={row.label} row={row} />
          ))}
        </ul>
      )}
    </div>
  );
}

function RotationKindBlock({ kind, block }: { kind: RotationGroupKind; block: CompassRotationKind }) {
  return (
    <div className="space-y-2" data-testid={`compass-leadership-rotation-${kind}`}>
      <h4 className="text-sm font-medium text-text">{KIND_LABEL[kind]} rotation</h4>
      <div className="grid gap-3 md:grid-cols-2">
        <RotationSide kind={kind} side="gaining" rows={block.gaining} />
        <RotationSide kind={kind} side="losing" rows={block.losing} />
      </div>
      <p className="text-xs text-text-faint" data-testid={`compass-leadership-rotation-${kind}-accounting`}>
        {block.shown_count} of {block.configured_total} shown &middot; {block.suppressed_count} below threshold
        &middot; {block.residual_count} beyond the display cap.
      </p>
    </div>
  );
}

/** J-13 (goal-market-compass iter-36): the Leadership rotation section — renders the SERVED
 *  `session_delta.rotation.{sector,theme}` block directly (two labelled, signed, both-directions sides
 *  per group kind, most-moved-first, each with its own honest empty state), replacing the prior
 *  client-side `session_delta.changes.filter(kind ∈ {sector, theme, stock})` slice that duplicated the
 *  What-changed card above it verbatim. This component selects no word, computes no sign, and applies no
 *  threshold — every value (label, from/to, signed delta, direction_word, drill_href, and the
 *  shown/suppressed/residual/configured_total accounting) is a served field, re-formatted only. No
 *  stock-kind row exists anywhere in `session_delta.rotation` (group-level only; stock leadership-bucket
 *  crossings stay in the What-changed card only).
 *
 *  Three distinct honest states, never a crash (AG-8): (1) `prior_as_of === null` — the earliest stored
 *  session, nothing to compare against; (2) `rotation` absent — a stored manifest row minted before this
 *  section existed, served verbatim and never backfilled (AG-12), so the block is reported as
 *  not-recorded rather than recomputed; (3) a served block whose side arrays may individually be empty,
 *  each rendering its own empty-state string. */
export function CompassLeadershipRotationSection({ compass }: { compass: CompassResponse | null }) {
  if (compass === null) {
    return (
      <Card
        className="flex items-center gap-3 border-neg bg-surface p-4 text-sm text-neg"
        data-testid="compass-leadership-rotation-unavailable"
      >
        <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
        Leadership rotation is unavailable — backend not reachable.
      </Card>
    );
  }

  const { session_delta } = compass;
  const noPriorRun = session_delta.prior_as_of === null;
  // Third state, distinct from both no-prior-run and an empty side: a stored manifest row minted BEFORE
  // iter-36 has a non-null `prior_as_of` but no `rotation` key at all (never backfilled — AG-12). Read
  // it once here so the render below can never dereference an absent block (AG-8: degrade honestly, do
  // not crash the page on as-of navigation).
  const rotation = session_delta.rotation ?? null;

  return (
    <Card data-testid="compass-leadership-rotation-section">
      <CardHeader>
        <CardTitle>Leadership rotation</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {noPriorRun ? (
          <p className="text-sm text-text-muted" data-testid="compass-leadership-rotation-no-prior">
            This is the earliest stored session — there is no prior session to compare rotation against.
          </p>
        ) : rotation === null ? (
          <p className="text-sm text-text-muted" data-testid="compass-leadership-rotation-not-recorded">
            Rotation detail was not recorded for this session — its stored manifest predates this section,
            and a frozen manifest is never rewritten, so nothing is shown here rather than recomputed. The
            What changed card above still lists this session&rsquo;s moves.
          </p>
        ) : (
          <>
            <RotationKindBlock kind="sector" block={rotation.sector} />
            <RotationKindBlock kind="theme" block={rotation.theme} />
          </>
        )}
      </CardContent>
    </Card>
  );
}
