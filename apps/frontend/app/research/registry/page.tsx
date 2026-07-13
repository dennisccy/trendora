"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ArrowLeft, BookMarked } from "lucide-react";

import { useAsOfHref } from "@/components/asof-provider";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { fetchRegistry, type PreRegistrationRow, type RegistryResponse } from "@/lib/api";
import { formatIsoDate } from "@/lib/dates";
import { cn } from "@/lib/utils";

/**
 * /research/registry — the pre-registration registry (goal-mcp-loop iter-30, J-18 / backlog B-901).
 *
 * A read-only table of every hypothesis ever registered/tested (selectors, rationale, registration date,
 * source, status), reading ONLY `GET /api/research/registry` — the SAME file + loader the post-decompose
 * gate cross-checks an incoming Evidence Claim against. No forms, no mutations: registrations are
 * appended by the gate/tooling only, never edited here.
 *
 * NO proven-language anywhere on this page: `status` ("registered" / "tested" / "closed") is a
 * descriptive PROCESS state, never a "Proven"/"Not yet proven" signal — a "tested" row may have FAILED
 * out-of-sample (every row here currently did). Rendered in the Badge `default` (neutral/muted) variant
 * deliberately, NOT the accent/danger coloring the Evidence page uses for PASS/FAIL, so this column is
 * never mistaken for an evidence-status badge. The single source of "Proven" stays `/evidence`.
 */
export default function RegistryPage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchRegistry(controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  // Scroll to a `#registration-<id>` deep-link target once the rows have rendered. The browser's native
  // scroll-to-fragment fires only on a full/hard page load; on a client-side (SPA) navigation into this
  // route — e.g. clicking a graveyard row's Lineage link (goal-mcp-loop iter-31, J-19) — the target row
  // is fetched AFTER the route commits, so the fragment resolves to nothing and no scroll happens. This
  // effect runs after the rows mount (`state.kind === "ok"`) and brings the anchored row into view; the
  // row's `scroll-mt-20` positions it just below the sticky header. No hash ⇒ no-op (plain browsing is
  // unchanged). rAF defers one frame so layout is settled before scrolling.
  useEffect(() => {
    if (state.kind !== "ok") return;
    const hash = window.location.hash;
    if (!hash) return;
    const raf = requestAnimationFrame(() => {
      const target = document.getElementById(hash.slice(1));
      if (target) target.scrollIntoView({ block: "start" });
    });
    return () => cancelAnimationFrame(raf);
  }, [state.kind]);

  const rows = state.kind === "ok" ? state.data.registrations : [];

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <BackToResearch />
        <PageHeading
          title="Pre-registration registry"
          subtitle="Every hypothesis the system has ever registered or tested — its selectors, economic rationale, and audit-trail date. The post-decompose gate refuses to certify any Evidence Claim that does not match a row here, exactly, before any referee computation runs."
        />
      </div>

      {state.kind === "loading" ? <RegistrySkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The pre-registration registry could not load from the API. Confirm the backend is running
              and reload.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" && rows.length === 0 ? <RegistryEmptyState /> : null}

      {state.kind === "ok" && rows.length > 0 ? <RegistryTable rows={rows} /> : null}
    </div>
  );
}

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: RegistryResponse }
  | { kind: "error" };

/** A same-window link back to the Research hub (mirrors `research/samples/page.tsx`'s pattern exactly). */
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

/** The honest empty state — should not occur post-backfill, but the page must degrade gracefully rather
 *  than crash if the registry file is ever absent/empty (anti-goal: resilience to data-shape change). */
function RegistryEmptyState() {
  return (
    <Card data-testid="registry-empty">
      <CardContent className="space-y-3 p-6">
        <div className="flex items-center gap-2">
          <BookMarked className="h-5 w-5 text-text-faint" aria-hidden />
          <h2 className="text-sm font-semibold text-text">No registrations yet</h2>
        </div>
        <p className="max-w-2xl text-sm text-text-muted">
          Nothing is registered yet. Once a hypothesis is registered, it appears here with its selectors,
          rationale, registration date, and source — and only a matching registration lets an Evidence
          Claim reach the referee.
        </p>
      </CardContent>
    </Card>
  );
}

function RegistryTable({ rows }: { rows: PreRegistrationRow[] }) {
  return (
    <Card className="p-0">
      <div className="overflow-x-auto">
        <table data-testid="registry-table" className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              <th className="px-4 py-2 font-medium">Selectors</th>
              <th className="px-4 py-2 font-medium">Rationale</th>
              <th className="px-4 py-2 font-medium">Registered</th>
              <th className="px-4 py-2 font-medium">Source</th>
              <th className="px-4 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.id}
                id={`registration-${row.id}`}
                data-testid="registry-row"
                className="scroll-mt-20 border-b border-border align-top last:border-b-0"
              >
                <td className="px-4 py-3">
                  <SelectorChips selectors={row.selectors} />
                </td>
                <td className="max-w-md px-4 py-3 text-text-muted">{row.rationale}</td>
                <td className="num whitespace-nowrap px-4 py-3 text-text">{formatIsoDate(row.registered_date)}</td>
                <td className="max-w-xs px-4 py-3 text-xs text-text-faint">{row.source}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={row.status} registeredBy={row.registered_by} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

/** Render a registration's selectors verbatim as compact key=value chips (mirrors the Evidence page's
 *  `ClaimHypothesis` presentation) — read-only, re-formats nothing, no numeric edge. */
function SelectorChips({ selectors }: { selectors: Record<string, unknown> }) {
  const entries = Object.entries(selectors);
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

/** The status column — a descriptive PROCESS state (never proven-language), deliberately rendered in the
 *  NEUTRAL `default` badge variant (not the accent/danger PASS/FAIL coloring the Evidence page uses), so
 *  a "tested" row is never mistaken for a proven-ness signal. Backfilled rows are visibly labeled. */
function StatusBadge({ status, registeredBy }: { status: string; registeredBy: string }) {
  const isBackfill = registeredBy === "backfill";
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <Badge variant="default" data-testid="registry-status">
        {status}
      </Badge>
      {isBackfill ? (
        <Badge variant="default" className="text-text-faint" data-testid="registry-backfill-label">
          backfill
        </Badge>
      ) : null}
    </div>
  );
}

function RegistrySkeleton() {
  return (
    <Card className="space-y-2 p-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className={cn("h-7 w-full animate-pulse rounded bg-surface-2")} />
      ))}
    </Card>
  );
}
