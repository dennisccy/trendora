"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, BookOpen } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  fetchMethodology,
  type MethodologyCatalog,
  type MethodologyEntry,
  type MethodologyThresholdRow,
} from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: MethodologyCatalog }
  | { kind: "error" };

/** Setup vs Pattern chip — pure presentation (a palette-token switch, not per-entry copy). */
function kindVariant(kind: MethodologyEntry["kind"]): "accent" | "default" {
  return kind === "pattern" ? "accent" : "default";
}
function kindLabel(kind: MethodologyEntry["kind"]): string {
  return kind === "pattern" ? "Pattern" : "Setup";
}

export default function MethodologyPage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchMethodology(controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  const entries = state.kind === "ok" ? state.data.entries : [];

  return (
    <div className="space-y-4">
      <PageHeading
        title="Methodology"
        subtitle="What every setup status and the VCP pattern mean — with the exact config thresholds that define each (read live from config, so they always match the scanner) and a worked example."
      />

      {state.kind === "ok" && state.data.intro ? (
        <Card className="p-4 text-sm text-text-muted">{state.data.intro}</Card>
      ) : null}

      {state.kind === "loading" ? <MethodologySkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The methodology glossary could not load from the API. No definitions are shown rather
              than fabricated copy. Confirm the backend is running and retry.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" && entries.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="No methodology entries"
          description="The backend returned an empty catalog. Add entries to the methodology section of config.yaml."
        />
      ) : null}

      {state.kind === "ok" && entries.length > 0 ? (
        <div className="space-y-3">
          {entries.map((entry) => (
            <EntryCard key={entry.key} entry={entry} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function EntryCard({ entry }: { entry: MethodologyEntry }) {
  return (
    <Card className="space-y-3 p-4" data-entry-key={entry.key}>
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-base font-semibold text-text">{entry.name}</h2>
        <Badge variant={kindVariant(entry.kind)}>{kindLabel(entry.kind)}</Badge>
      </div>
      <p className="text-sm text-text-muted">{entry.meaning}</p>

      {entry.thresholds.length > 0 ? (
        <div className="space-y-1.5">
          <p className="text-xs uppercase tracking-wide text-text-faint">Thresholds</p>
          <ul className="space-y-1">
            {entry.thresholds.map((row, index) => (
              <ThresholdRow key={index} row={row} />
            ))}
          </ul>
        </div>
      ) : null}

      <p className="text-xs text-text-muted">
        <span className="text-text-faint">Example: </span>
        {entry.example}
      </p>
    </Card>
  );
}

function ThresholdRow({ row }: { row: MethodologyThresholdRow }) {
  if (row.text != null) {
    return (
      <li className="text-xs text-text-muted">
        <span className="text-text">{row.label}</span>
        <span className="text-text-faint"> — {row.text}</span>
      </li>
    );
  }
  return (
    <li className="flex items-center gap-2 text-xs text-text-muted">
      <span className="w-44 shrink-0 text-text">{row.label}</span>
      <span className="num text-text-faint">{row.cmp}</span>
      <span className="num text-text">
        {row.value}
        {row.unit ?? ""}
      </span>
    </li>
  );
}

function MethodologySkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i} className="space-y-3 p-4">
          <div className="h-5 w-40 animate-pulse rounded bg-surface-2" />
          <div className="h-4 w-full animate-pulse rounded bg-surface-2" />
          <div className="h-4 w-3/4 animate-pulse rounded bg-surface-2" />
        </Card>
      ))}
    </div>
  );
}
