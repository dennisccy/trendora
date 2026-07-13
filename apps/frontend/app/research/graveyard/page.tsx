"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, Archive, ArrowLeft } from "lucide-react";

import { useAsOfHref } from "@/components/asof-provider";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { fetchGraveyard, type GraveyardEntry, type GraveyardResponse, type RevisitProtocol } from "@/lib/api";
import type { Verdict } from "@/lib/evidence";
import type { PreRegistrationRow } from "@/lib/registry";
import { formatIsoDate } from "@/lib/dates";
import { cn } from "@/lib/utils";

/**
 * /research/graveyard — the negative-results graveyard (goal-mcp-loop iter-31, J-19 / backlog B-902).
 *
 * A read-only table of every hypothesis the referee has REJECTED (`FAIL` / `INSUFFICIENT`) across BOTH
 * the canonical and staging certified-claims ledgers, joined to its registration lineage — so nobody (a
 * future model, or the owner in month 9) re-derives a dead idea from scratch. Reads ONLY
 * `GET /api/research/graveyard`; no forms, no mutations, no deletion path anywhere (append-only history).
 *
 * NO proven-language anywhere on this page: the Verdict column shows `FAIL`/`INSUFFICIENT` in the
 * NEUTRAL-negative `danger`/`warn` Badge variants (mirrors the Evidence page's own PASS/FAIL/INSUFFICIENT
 * mapping for these two statuses), NEVER the `accent` variant the Evidence page reserves exclusively for
 * a PASS/"Proven" row — since this page shows only non-PASS rows, `accent` never appears here. The single
 * source of "Proven" stays `/evidence`; this page never resolves or displays evidence status.
 */
export default function GraveyardPage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchGraveyard(controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  const entries = state.kind === "ok" ? state.data.entries : [];
  const revisitProtocol = state.kind === "ok" ? state.data.revisit_protocol : null;

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <BackToResearch />
        <PageHeading
          title="Negative-results graveyard"
          subtitle="Every hypothesis the statistical referee has rejected — out-of-sample FAIL or INSUFFICIENT, across both the canonical and internal staging ledgers — with its selectors, verdict, and registration lineage. Descriptive history only; nothing here is a proven/not-proven signal."
        />
      </div>

      {state.kind === "loading" ? <GraveyardSkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The graveyard could not load from the API. Confirm the backend is running and reload.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" && entries.length === 0 ? <GraveyardEmptyState /> : null}

      {state.kind === "ok" && entries.length > 0 ? (
        <>
          <GraveyardTable entries={entries} />
          {revisitProtocol ? <RevisitProtocolPanel protocol={revisitProtocol} /> : null}
        </>
      ) : null}
    </div>
  );
}

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: GraveyardResponse }
  | { kind: "error" };

/** A same-window link back to the Research hub (mirrors `research/registry/page.tsx`'s pattern exactly). */
function BackToResearch() {
  const asofHref = useAsOfHref();
  return (
    <Link
      href={asofHref("/research")}
      className="inline-flex items-center gap-1 text-xs font-medium text-text-muted hover:text-accent focus-visible:text-accent focus-visible:outline-none"
    >
      <ArrowLeft className="h-3.5 w-3.5" aria-hidden /> Back to Research
    </Link>
  );
}

/** The honest empty state — both ledgers absent/empty. Should not occur today (both real ledgers carry
 *  7 non-PASS rows each), but the page must degrade gracefully rather than crash (anti-goal: resilience
 *  to data-shape change). */
function GraveyardEmptyState() {
  return (
    <Card data-testid="graveyard-empty">
      <CardContent className="space-y-3 p-6">
        <div className="flex items-center gap-2">
          <Archive className="h-5 w-5 text-text-faint" aria-hidden />
          <h2 className="text-sm font-semibold text-text">No rejected hypotheses yet</h2>
        </div>
        <p className="max-w-2xl text-sm text-text-muted">
          Nothing has been referee-rejected yet on either ledger. Once a hypothesis fails, or is ruled
          insufficient, out-of-sample, it appears here with its selectors, verdict, and registration
          lineage.
        </p>
      </CardContent>
    </Card>
  );
}

function GraveyardTable({ entries }: { entries: GraveyardEntry[] }) {
  return (
    <Card className="p-0">
      <div className="overflow-x-auto">
        <table data-testid="graveyard-table" className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              <th className="px-4 py-2 font-medium">Selectors</th>
              <th className="px-4 py-2 font-medium">Verdict</th>
              <th className="px-4 py-2 font-medium">Date</th>
              <th className="px-4 py-2 font-medium">Deflation</th>
              <th className="px-4 py-2 font-medium">Ledger</th>
              <th className="px-4 py-2 font-medium">Lineage</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry, index) => (
              <GraveyardRow key={`${entry.ledger}-${index}`} entry={entry} />
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

/** The verdict-kind variant — NEUTRAL-negative only (`danger` for FAIL, `warn` for INSUFFICIENT), mirrors
 *  the Evidence page's own `verdictVariant` mapping for these two statuses exactly. NEVER `accent`: this
 *  page shows only non-PASS rows, so a "Proven"-style badge must never appear here. */
function verdictKindVariant(status: string): "danger" | "warn" | "default" {
  if (status === "FAIL") return "danger";
  if (status === "INSUFFICIENT") return "warn";
  return "default";
}

function GraveyardRow({ entry }: { entry: GraveyardEntry }) {
  const isPermanent = entry.lineage?.status === "closed";
  const verdict = entry.verdict ?? { status: "", reason: "" };
  return (
    <tr data-testid="graveyard-row" className="border-b border-border align-top last:border-b-0">
      <td className="px-4 py-3">
        <SelectorChips selectors={entry.claim} />
      </td>
      <td className="px-4 py-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant={verdictKindVariant(verdict.status)} data-testid="graveyard-verdict">
            {verdict.status || "—"}
          </Badge>
          {isPermanent ? (
            <Badge variant="default" className="text-text-faint" data-testid="graveyard-permanent">
              permanent
            </Badge>
          ) : null}
        </div>
        {verdict.reason ? <p className="mt-1 max-w-xs text-xs text-text-faint">{verdict.reason}</p> : null}
        <a
          href="#revisit-protocol"
          className="mt-1 inline-block text-[11px] text-text-faint hover:text-accent hover:underline focus-visible:text-accent focus-visible:outline-none"
          data-testid="graveyard-row-revisit-link"
        >
          Revisit protocol →
        </a>
      </td>
      <td className="num whitespace-nowrap px-4 py-3 text-text">{formatIsoDate(entry.register_date)}</td>
      <td className="num whitespace-nowrap px-4 py-3 text-text-muted" data-testid="graveyard-deflation">
        <DeflationLabel verdict={verdict} />
      </td>
      <td className="px-4 py-3">
        <Badge variant="default" data-testid="graveyard-ledger">
          {entry.ledger}
        </Badge>
      </td>
      <td className="px-4 py-3">
        <LineageLink lineage={entry.lineage} />
      </td>
    </tr>
  );
}

/** `{deflation} ÷{deflation_divisor}` (e.g. `bonferroni ÷8`), or just the raw policy name when no divisor
 *  is present (e.g. the staging online-FDR economy's `lord++`) — re-displays the referee's OWN recorded
 *  deflation context verbatim, never recomputed. */
function DeflationLabel({ verdict }: { verdict: Verdict }) {
  const deflation = typeof verdict.deflation === "string" ? verdict.deflation : null;
  if (!deflation) return <span className="text-text-faint">—</span>;
  const divisor = verdict.deflation_divisor;
  const hasDivisor = typeof divisor === "number";
  return (
    <span>
      {deflation}
      {hasDivisor ? ` ÷${divisor}` : ""}
    </span>
  );
}

/** A row's registration lineage: a link to its exact `/research/registry` row when matched, or an honest
 *  "no lineage" text when the selector-set matches no registration (never a fabricated link). */
function LineageLink({ lineage }: { lineage: PreRegistrationRow | null }) {
  const asofHref = useAsOfHref();
  if (!lineage) {
    return (
      <span className="text-xs text-text-faint" data-testid="graveyard-lineage-none">
        No registration lineage
      </span>
    );
  }
  return (
    <Link
      href={asofHref(`/research/registry#registration-${lineage.id}`)}
      className="text-xs text-accent hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
      data-testid="graveyard-lineage-link"
    >
      {lineage.id} →
    </Link>
  );
}

/** Render a claim's selectors verbatim as compact key=value chips (mirrors the Registry page's
 *  `SelectorChips` presentation) — read-only, re-formats nothing, no numeric edge. */
function SelectorChips({ selectors }: { selectors: Record<string, unknown> }) {
  const entries = Object.entries(selectors ?? {});
  if (entries.length === 0) {
    return <span className="text-text-muted">—</span>;
  }
  return (
    <div className="flex max-w-xs flex-wrap gap-1">
      {entries.map(([key, value]) => (
        <Badge key={key} variant="default" className="num whitespace-nowrap text-[11px]">
          {key}={Array.isArray(value) ? value.join("+") : String(value)}
        </Badge>
      ))}
    </div>
  );
}

/** The revisit-protocol panel — the single served rule every row's "Revisit protocol →" link anchors to. */
function RevisitProtocolPanel({ protocol }: { protocol: RevisitProtocol }) {
  return (
    <Card id="revisit-protocol" className="scroll-mt-20" data-testid="graveyard-revisit-protocol">
      <CardContent className="space-y-2 p-5">
        <h2 className="text-sm font-semibold text-text">Revisit protocol</h2>
        <p className="text-sm text-text-muted">{protocol.rule}</p>
      </CardContent>
    </Card>
  );
}

function GraveyardSkeleton() {
  return (
    <Card className="space-y-2 p-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className={cn("h-7 w-full animate-pulse rounded bg-surface-2")} />
      ))}
    </Card>
  );
}
