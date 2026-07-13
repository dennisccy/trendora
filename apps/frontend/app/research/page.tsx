"use client";

import Link from "next/link";
import {
  Archive,
  ArrowRight,
  BookMarked,
  Boxes,
  Gauge,
  GitCompareArrows,
  Layers,
  LineChart,
  Microscope,
  Thermometer,
  TrendingDown,
  TrendingUp,
  Waves,
} from "lucide-react";

import { useAsOfHref } from "@/components/asof-provider";
import { PageHeading } from "@/components/page-heading";
import { Card } from "@/components/ui/card";
import { RESEARCH_LABS, type ResearchLabIcon } from "@/lib/research-labs";
import { cn } from "@/lib/utils";

/** Resolve a lab's icon key (the pure ordered source in `lib/research-labs.ts` stores a string so it stays
 *  dependency-free + unit-assertable) to its lucide component. */
const LAB_ICONS: Record<ResearchLabIcon, typeof Microscope> = {
  LineChart,
  Gauge,
  Thermometer,
  Boxes,
  Layers,
  Waves,
  GitCompareArrows,
  Microscope,
  TrendingUp,
  TrendingDown,
};

/** /research — the Research hub (J-104). A list of the labs, each linking to its own lazy-loaded route so
 *  only one heavy computation runs per page (the hub fires none). Every lab is reachable + deep-linkable;
 *  the existing N= samples drill-downs keep working from the relocated labs. */
export default function ResearchHubPage() {
  // J-50: every nav href carries the global as-of date while historical (clean at the latest date), so a
  // lab opens scoped to the same point-in-time the operator was browsing.
  const asofHref = useAsOfHref();
  return (
    <div className="space-y-4">
      <PageHeading
        title="Research"
        subtitle="Read-only labs over the stored forward-tested evidence. Each lab loads on its own page (fast, one heavy fetch at a time). Descriptive evidence, never a forecast or an order."
      />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3" data-testid="research-hub">
        {RESEARCH_LABS.map(({ href, title, description, icon }) => {
          const Icon = LAB_ICONS[icon];
          return (
          <Link
            key={href}
            href={asofHref(href)}
            data-testid={`research-lab-link-${href.split("/").pop()}`}
            className={cn(
              "group flex flex-col gap-2 rounded-lg border border-border bg-surface p-4 transition-colors",
              "hover:border-accent hover:bg-surface-2",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
            )}
          >
            <div className="flex items-center gap-2">
              <Icon className="h-5 w-5 text-accent" aria-hidden />
              <h2 className="text-base font-semibold text-text">{title}</h2>
              <ArrowRight className="ml-auto h-4 w-4 text-text-faint transition-transform group-hover:translate-x-0.5 group-hover:text-accent" aria-hidden />
            </div>
            <p className="text-sm text-text-muted">{description}</p>
          </Link>
          );
        })}
      </div>

      {/* goal-mcp-loop iter-30 (J-18) / iter-31 (J-19) — Governance & process: registry + graveyard now,
          budget / referee-audit still to follow. Kept a SEPARATE section, not an 11th RESEARCH_LABS
          entry — that array's reading order is a J-113 contract over the ten analytical labs; a
          governance/process link is architecturally distinct, not a lab. */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-text-faint">Governance &amp; process</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3" data-testid="research-governance">
          <Link
            href={asofHref("/research/registry")}
            data-testid="research-governance-link-registry"
            className={cn(
              "group flex flex-col gap-2 rounded-lg border border-border bg-surface p-4 transition-colors",
              "hover:border-accent hover:bg-surface-2",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
            )}
          >
            <div className="flex items-center gap-2">
              <BookMarked className="h-5 w-5 text-accent" aria-hidden />
              <h3 className="text-base font-semibold text-text">Pre-registration registry</h3>
              <ArrowRight className="ml-auto h-4 w-4 text-text-faint transition-transform group-hover:translate-x-0.5 group-hover:text-accent" aria-hidden />
            </div>
            <p className="text-sm text-text-muted">
              Every hypothesis the system has ever registered or tested — selectors, rationale,
              registration date, and source. The gate refuses to certify anything that isn&apos;t here.
            </p>
          </Link>

          {/* goal-mcp-loop iter-31 (J-19) — the negative-results graveyard: every referee-rejected
              hypothesis across both ledgers, so nobody re-derives a dead idea from scratch. */}
          <Link
            href={asofHref("/research/graveyard")}
            data-testid="research-governance-link-graveyard"
            className={cn(
              "group flex flex-col gap-2 rounded-lg border border-border bg-surface p-4 transition-colors",
              "hover:border-accent hover:bg-surface-2",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
            )}
          >
            <div className="flex items-center gap-2">
              <Archive className="h-5 w-5 text-accent" aria-hidden />
              <h3 className="text-base font-semibold text-text">Negative-results graveyard</h3>
              <ArrowRight className="ml-auto h-4 w-4 text-text-faint transition-transform group-hover:translate-x-0.5 group-hover:text-accent" aria-hidden />
            </div>
            <p className="text-sm text-text-muted">
              Every hypothesis the referee has rejected, across the canonical and staging ledgers — its
              verdict, deflation context, and registration lineage. Nobody retries a dead idea blindly.
            </p>
          </Link>
        </div>
      </div>
    </div>
  );
}
