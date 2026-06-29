"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  Database,
  FlaskConical,
  Grid2x2,
  History,
  Layers,
  LayoutDashboard,
  Microscope,
  ShieldCheck,
  Star,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

import { useAsOfHref } from "@/components/asof-provider";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

// The approved Information Architecture (blueprint). Stock Detail and Run Detail are
// intentionally NOT here — they are reached from a leaderboard / run row.
const NAV: NavItem[] = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/stocks", label: "Stocks", icon: TrendingUp },
  { href: "/themes", label: "Themes", icon: Layers },
  { href: "/sectors", label: "Sectors", icon: Grid2x2 },
  { href: "/scanner-runs", label: "Scanner Runs", icon: History },
  { href: "/backtest", label: "Backtest", icon: FlaskConical },
  { href: "/research", label: "Research", icon: Microscope },
  // goal-mcp-loop iter-1 — the certified-claims ledger (the already-approved blueprint IA's Evidence
  // section). Reachable in ≤2 clicks; every score's badge links here.
  { href: "/evidence", label: "Evidence", icon: ShieldCheck },
  { href: "/watchlist", label: "Watchlist", icon: Star },
  { href: "/methodology", label: "Methodology", icon: BookOpen },
  { href: "/data", label: "Data Manager", icon: Database },
];

export function Sidebar() {
  const pathname = usePathname();
  // J-50: every nav href carries the global as-of date while historical (clean at latest) via the one
  // shared helper — so middle-click / new-tab on a sidebar entry lands on the same dated view. The
  // `isActive` check still keys on the route (the base path), never the query, so the active highlight
  // is unaffected by the `?asof` serialization.
  const asofHref = useAsOfHref();
  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-border bg-surface">
      <div className="flex h-14 items-center gap-2 border-b border-border px-5">
        <span className="h-2.5 w-2.5 rounded-full bg-accent" aria-hidden />
        <span className="text-base font-semibold tracking-tight text-text">Trendora</span>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-3">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={asofHref(href)}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                "text-text-muted hover:bg-surface-2 hover:text-text",
                "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
                active && "bg-surface-2 font-medium text-text",
              )}
            >
              <Icon className="h-4 w-4 shrink-0" aria-hidden />
              <span>{label}</span>
              {active ? <span className="ml-auto h-1.5 w-1.5 rounded-full bg-accent" aria-hidden /> : null}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-border p-3 text-xs text-text-faint">
        Offline seed spine · v0.1
      </div>
    </aside>
  );
}
