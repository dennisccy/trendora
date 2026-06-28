/**
 * J-113 — the single ordered source for the /research hub cards (reading order).
 *
 * Kept a PURE data module (icons referenced by string key, NOT imported lucide components) so the order is
 * unit-assertable under the node TS-strip convention (`node lib/research-labs.test.ts`). The hub page
 * (`app/research/page.tsx`) imports `RESEARCH_LABS`, resolves each `icon` key to a lucide component, and
 * maps over the list — so the reading order lives here, in one place.
 *
 * Reading order (J-113): the regime / phase / factor analysis themes the operator most often opens lead,
 * then the multi-dimensional combination labs, then the event-study / recovery / downtrend labs. No lab is
 * added, removed, or renamed — all ten stay reachable + deep-linkable; every route is unchanged.
 */

/** The lucide icon name a lab card shows (resolved to a component by the hub — kept a string so this
 *  ordered source stays a pure, dependency-free module). */
export type ResearchLabIcon =
  | "LineChart"
  | "Gauge"
  | "Thermometer"
  | "Boxes"
  | "Layers"
  | "Waves"
  | "GitCompareArrows"
  | "Microscope"
  | "TrendingUp"
  | "TrendingDown";

/** One lab the Research hub links to: its route, title, one-line description, and its icon key. */
export interface ResearchLab {
  href: string;
  title: string;
  description: string;
  icon: ResearchLabIcon;
}

/** The Research labs in reading order (J-113). Each lives on its own lazy-loaded route (J-104) so
 *  navigating to one fires at most ONE heavy fetch — the hub itself fires none. Every lab is reachable +
 *  deep-linkable; the `?asof` href-stamping (J-50) and per-lab lazy-load (J-104) are unchanged. */
export const RESEARCH_LABS: ResearchLab[] = [
  {
    href: "/research/factor-lab",
    title: "Factor Lab",
    description:
      "Does a factor actually sort future returns? Decile means + a downside risk-adjusted column + the rank-IC.",
    icon: "LineChart",
  },
  {
    href: "/research/regime-lab",
    title: "Regime Lab",
    description:
      "How have stocks' forward returns and downside risk differed across market regimes? Paired return + max-drawdown by regime label and by regime-score decile, all horizons.",
    icon: "Gauge",
  },
  {
    href: "/research/phase-severity-lab",
    title: "Market Phase & Severity Lab",
    description:
      "How have stocks' forward returns and downside risk differed across the market phase and stress severity? Paired return + max-drawdown by market-phase label and by severity-score decile, all horizons.",
    icon: "Thermometer",
  },
  {
    href: "/research/regime-phase-factor",
    title: "Regime × Phase × Factor",
    description:
      "For a chosen factor, how do forward returns and downside risk differ across the three-way regime-score × severity-score × factor decile interaction? A ranked, filterable, paginated combination table, all horizons.",
    icon: "Boxes",
  },
  {
    href: "/research/regime-setup-pattern",
    title: "Regime × Setup × Pattern",
    description:
      "Which (regime, setup, pattern) combinations have had the strongest forward-return edge? A ranked, filterable table.",
    icon: "Layers",
  },
  {
    href: "/research/severity-velocity",
    title: "Severity-velocity × Regime",
    description:
      "Does rising or falling stress under a given regime predict the market's next move? A regime-family × velocity-sign forward-return matrix.",
    icon: "Waves",
  },
  {
    href: "/research/factor-combination",
    title: "Multi-factor combination",
    description:
      "Does combining factor conditions beat either alone? The composite rank-blend cohort vs the baseline and each single factor.",
    icon: "GitCompareArrows",
  },
  {
    href: "/research/event-study",
    title: "Setup & Pattern event study",
    description:
      "What forward-return distribution has each setup or detected pattern historically shown? Per-horizon stats + by-regime / by-sector slices.",
    icon: "Microscope",
  },
  {
    href: "/research/recovery-turn-edge",
    title: "Recovery-Turn Edge",
    description:
      "When the market causally turns up out of a downtrend, what forward-return edge has entering at those dates shown?",
    icon: "TrendingUp",
  },
  {
    href: "/research/downtrend-opportunity",
    title: "Downtrend Opportunity",
    description:
      "Conditioned on the causal downtrend state, which cohorts held up best and which fell hardest. Evidence only — never an order.",
    icon: "TrendingDown",
  },
];
