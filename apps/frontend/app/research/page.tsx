"use client";

import Link from "next/link";
import {
  ArrowRight,
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
import { cn } from "@/lib/utils";

/** One lab the Research hub links to: its route, title, one-line description, and an icon. */
interface LabLink {
  href: string;
  title: string;
  description: string;
  icon: typeof Microscope;
}

/** The Research labs, in reading order. Each lives on its own lazy-loaded route (J-104) so navigating to
 *  one fires at most ONE heavy fetch — the hub itself fires none. Every lab is reachable + deep-linkable. */
const LABS: LabLink[] = [
  {
    href: "/research/factor-lab",
    title: "Factor Lab",
    description:
      "Does a factor actually sort future returns? Decile means + a downside risk-adjusted column + the rank-IC.",
    icon: LineChart,
  },
  {
    href: "/research/factor-combination",
    title: "Multi-factor combination",
    description:
      "Does combining factor conditions beat either alone? The composite rank-blend cohort vs the baseline and each single factor.",
    icon: GitCompareArrows,
  },
  {
    href: "/research/event-study",
    title: "Setup & Pattern event study",
    description:
      "What forward-return distribution has each setup or detected pattern historically shown? Per-horizon stats + by-regime / by-sector slices.",
    icon: Microscope,
  },
  {
    href: "/research/regime-setup-pattern",
    title: "Regime × Setup × Pattern",
    description:
      "Which (regime, setup, pattern) combinations have had the strongest forward-return edge? A ranked, filterable table.",
    icon: Layers,
  },
  {
    href: "/research/recovery-turn-edge",
    title: "Recovery-Turn Edge",
    description:
      "When the market causally turns up out of a downtrend, what forward-return edge has entering at those dates shown?",
    icon: TrendingUp,
  },
  {
    href: "/research/downtrend-opportunity",
    title: "Downtrend Opportunity",
    description:
      "Conditioned on the causal downtrend state, which cohorts held up best and which fell hardest. Evidence only — never an order.",
    icon: TrendingDown,
  },
  {
    href: "/research/severity-velocity",
    title: "Severity-velocity × Regime",
    description:
      "Does rising or falling stress under a given regime predict the market's next move? A regime-family × velocity-sign forward-return matrix.",
    icon: Waves,
  },
  {
    href: "/research/regime-lab",
    title: "Regime Lab",
    description:
      "How have stocks' forward returns and downside risk differed across market regimes? Paired return + max-drawdown by regime label and by regime-score decile, all horizons.",
    icon: Gauge,
  },
  {
    href: "/research/phase-severity-lab",
    title: "Market Phase & Severity Lab",
    description:
      "How have stocks' forward returns and downside risk differed across the market phase and stress severity? Paired return + max-drawdown by market-phase label and by severity-score decile, all horizons.",
    icon: Thermometer,
  },
  {
    href: "/research/regime-phase-factor",
    title: "Regime × Phase × Factor",
    description:
      "For a chosen factor, how do forward returns and downside risk differ across the three-way regime-score × severity-score × factor decile interaction? A ranked, filterable, paginated combination table, all horizons.",
    icon: Boxes,
  },
];

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
        {LABS.map(({ href, title, description, icon: Icon }) => (
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
        ))}
      </div>
    </div>
  );
}
