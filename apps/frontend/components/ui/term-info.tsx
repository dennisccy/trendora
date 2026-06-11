"use client";

import type { ReactNode } from "react";

import { InfoTooltip } from "@/components/ui/info-tooltip";
import { useGlossaryTerm } from "@/lib/glossary";
import type { MethodologyThresholdRow } from "@/lib/api";

/**
 * Inline term help (iter-4 goal-mode, J-47). A thin wrapper around the existing `InfoTooltip` that looks
 * the term up in the SHARED config-backed glossary (`useGlossaryTerm`) and renders its definition — the
 * SAME entry the /methodology Glossary page shows (single source of truth; no hardcoded copy).
 *
 * Degrades gracefully: a term key absent from the catalog (or a not-yet-loaded / failed fetch) renders
 * the bare children with NO marker — never a crash, never a hardcoded fallback definition.
 *
 *   <TermInfo term="rank-IC">Rank-IC</TermInfo>   // header label + an info marker reading the catalog
 *   <TermInfo term="MAE" />                        // marker only (e.g. next to an existing label)
 */
export function TermInfo({
  term,
  children,
  className,
}: {
  term: string;
  children?: ReactNode;
  className?: string;
}) {
  const entry = useGlossaryTerm(term);

  // Missing term / catalog not ready → render children alone with no marker (graceful degradation).
  if (!entry) return <>{children ?? null}</>;

  const content = (
    <div className="space-y-1.5">
      <p className="font-medium text-text">{entry.term}</p>
      <p className="text-text-muted">{entry.definition}</p>
      {entry.where ? (
        <p className="text-text-faint">
          <span className="uppercase tracking-wide">Where: </span>
          {entry.where}
        </p>
      ) : null}
      {entry.thresholds && entry.thresholds.length > 0 ? (
        <ul className="space-y-0.5 border-t border-border pt-1.5">
          {entry.thresholds.map((row, index) => (
            <ThresholdLine key={index} row={row} />
          ))}
        </ul>
      ) : null}
    </div>
  );

  if (children == null) {
    return <InfoTooltip label={`Definition of ${entry.term}`} content={content} className={className} />;
  }

  return (
    <span className={className}>
      <span className="inline-flex items-center gap-1">
        {children}
        <InfoTooltip label={`Definition of ${entry.term}`} content={content} />
      </span>
    </span>
  );
}

/** One threshold row inside a term tooltip — a config-resolved numeric row or a prose `text` rule. The
 *  value is whatever the backend resolved (never re-typed here). */
function ThresholdLine({ row }: { row: MethodologyThresholdRow }) {
  if (row.text != null) {
    return (
      <li className="text-text-muted">
        <span className="text-text">{row.label}</span>
        <span className="text-text-faint"> — {row.text}</span>
      </li>
    );
  }
  return (
    <li className="flex items-center gap-1.5 text-text-muted">
      <span className="text-text">{row.label}</span>
      <span className="num text-text-faint">{row.cmp}</span>
      <span className="num text-text">
        {row.value}
        {row.unit ?? ""}
      </span>
    </li>
  );
}
