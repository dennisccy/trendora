"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, ArrowDown, ArrowUp, ArrowUpDown, Search, TrendingUp } from "lucide-react";

import { useAsOf, useAsOfHref } from "@/components/asof-provider";
import { EmptyState } from "@/components/empty-state";
import { EvidenceStatusBadge } from "@/components/evidence-status-badge";
import { fmtMdd, fmtPct, mddClass, returnClass } from "@/components/forward-return";
import { PageHeading } from "@/components/page-heading";
import { ScoreBadge } from "@/components/score-badge";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { InfoTooltip } from "@/components/ui/info-tooltip";
import { TermInfo } from "@/components/ui/term-info";
import { formatIsoDate } from "@/lib/dates";
import { fmtHighProximity, highProximityValue } from "@/lib/high-proximity";
import { regimeVariant } from "@/lib/regime-variant";
import { SCORE_SIGNALS } from "@/lib/evidence";
import { cn } from "@/lib/utils";
import {
  fetchDashboard,
  fetchEvidence,
  fetchMethodology,
  fetchStocks,
  fetchThemes,
  type DashboardResponse,
  type MethodologyCatalog,
  type ProvenSignal,
  type StockRow,
  type StocksResponse,
  type ThemeRow,
  type ThemesResponse,
} from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: StocksResponse }
  | { kind: "error" };

const ALL = "__all__";

/** A detected price pattern's read-only flag shape — every pattern (VCP + the iter-9 additions) shares
 *  this contract, so the leaderboard filters/renders them uniformly (no per-pattern branching). */
type PatternFlag = {
  flagged: boolean;
  reason: string;
  pivot: number | null;
  invalidation: { level: number | null; note: string };
};

/** The detected patterns shown on the leaderboard, in display order. Each maps the canonical config key
 *  (matches the /methodology catalog `key`) to its row field + a short badge label. Adding a pattern is
 *  ONE entry here — the badge, the filter, and the tooltip all read this list (config-driven UI). */
const PATTERNS: { key: string; label: string; badge: string; get: (row: StockRow) => PatternFlag }[] = [
  { key: "vcp", label: "VCP", badge: "VCP", get: (r) => r.vcp },
  { key: "pullback_to_rising_dma", label: "Pullback to rising DMA", badge: "Pullback", get: (r) => r.pullback_to_rising_dma },
  { key: "flat_base_breakout", label: "Flat-base breakout", badge: "Flat base", get: (r) => r.flat_base_breakout },
];

/** J-48 — the sortable leaderboard columns. Each entry maps a column to a comparator over the SERVED
 *  row value (never recomputed). `rank` is the default / stored-scanner order (clicking `#` restores it).
 *  Score columns sort by the stored 0–100 number (the A–E bucket rides along, unchanged); `setup` sorts
 *  alphabetically on the served status string; `ticker`/`sector` sort lexicographically. This is a pure
 *  VIEW transform — it only re-orders the already-served rows; it changes/recomputes no displayed value. */
/** A base sortable column, plus the dynamic forward-return columns `fwd_<horizon>` (J-75) and the paired
 *  max-drawdown columns `mdd_<horizon>` (J-86). */
type BaseSortKey = "rank" | "ticker" | "sector" | "leadership" | "entry_quality" | "risk" | "setup";
// J-106 adds the `high_proximity` column key (handled by an explicit NA-last branch in comparatorFor,
// NOT routed through SORT_COMPARATORS — that base map has no null handling).
type SortKey = BaseSortKey | "high_proximity" | `fwd_${number}` | `mdd_${number}`;
type SortDir = "asc" | "desc";

/** J-75 — a stock's realized forward return at `horizon` from the served `forward_returns` (NA → null).
 *  Read verbatim; never recomputed. */
function fwdReturnAt(row: StockRow, horizon: number): number | null {
  return row.forward_returns.find((fr) => fr.horizon === horizon)?.return ?? null;
}

/** J-86 — a stock's realized max-drawdown at `horizon` from the served `forward_returns` (NA → null).
 *  Read verbatim; never recomputed (<= 0 where present). */
function fwdMddAt(row: StockRow, horizon: number): number | null {
  return row.forward_returns.find((fr) => fr.horizon === horizon)?.max_drawdown ?? null;
}

/** The base per-column comparators (ascending). Ties are broken by stored rank in the stable-sort memo. */
const SORT_COMPARATORS: Record<BaseSortKey, (a: StockRow, b: StockRow) => number> = {
  rank: (a, b) => a.rank - b.rank,
  ticker: (a, b) => a.ticker.localeCompare(b.ticker),
  sector: (a, b) => a.sector.localeCompare(b.sector),
  leadership: (a, b) => a.leadership.score - b.leadership.score,
  entry_quality: (a, b) => a.entry_quality.score - b.entry_quality.score,
  risk: (a, b) => a.risk.score - b.risk.score,
  setup: (a, b) => a.setup.status.localeCompare(b.setup.status),
};

/** Resolve a sort key to its comparator — a base column, or a `fwd_<horizon>` forward-return column
 *  (J-75/J-48 view transform). A null (NA) forward return always sorts LAST (so NA never poses as a
 *  top/bottom value); the stable memo then tie-breaks by stored rank. Pure re-order of served values. */
function comparatorFor(key: SortKey, dir: SortDir): (a: StockRow, b: StockRow) => number {
  if (key.startsWith("fwd_") || key.startsWith("mdd_")) {
    const horizon = Number(key.slice(4));
    const valueAt = key.startsWith("mdd_") ? fwdMddAt : fwdReturnAt; // J-86 MDD column shares the view-transform
    const sign = dir === "asc" ? 1 : -1;
    return (a, b) => {
      const av = valueAt(a, horizon);
      const bv = valueAt(b, horizon);
      if (av === null && bv === null) return 0;
      if (av === null) return 1; // NA last regardless of direction
      if (bv === null) return -1;
      return (av - bv) * sign;
    };
  }
  // J-106 — the "Proximity to 52w high" column sorts on the stored `high_proximity` value (a percent
  // <= 0; 0 at a fresh high), read verbatim from the SAME served component the detail breakdown shows
  // (single source; never recomputed). NA (short history) always sorts LAST regardless of direction; the
  // stable memo then tie-breaks by stored rank. Kept OUT of SORT_COMPARATORS, which has no null handling.
  if (key === "high_proximity") {
    const sign = dir === "asc" ? 1 : -1;
    return (a, b) => {
      const av = highProximityValue(a.leadership.components);
      const bv = highProximityValue(b.leadership.components);
      if (av === null && bv === null) return 0;
      if (av === null) return 1; // NA last regardless of direction
      if (bv === null) return -1;
      return (av - bv) * sign;
    };
  }
  const cmp = SORT_COMPARATORS[key as BaseSortKey];
  const sign = dir === "asc" ? 1 : -1;
  return (a, b) => cmp(a, b) * sign;
}

/** The default sort: the scanner's stored rank, ascending (`#` column) — the initial state and what a
 *  click on the `#` header restores. */
const DEFAULT_SORT: { key: SortKey; dir: SortDir } = { key: "rank", dir: "asc" };

/** Decode the URL `pattern` query param into the leaderboard's internal filter value (J-31 deep-link).
 *  Strictly validated against the PATTERNS registry: `<key>__only` / `<key>__none` for a KNOWN key,
 *  else the `__all__` sentinel — an absent or unrecognized param never crashes and fabricates no filter
 *  (it harmlessly falls back to "all"). The encoding is the leaderboard's existing one verbatim; this is
 *  the ONLY place a URL param maps to filter state — no date/as_of param is ever read here (J-18). */
function parsePatternParam(raw: string | null): string {
  if (!raw) return ALL;
  const [key, mode] = raw.split("__");
  const known = PATTERNS.some((p) => p.key === key);
  if (known && (mode === "only" || mode === "none")) return `${key}__${mode}`;
  return ALL;
}

/** J-56 — resolve a theme slug to its shared display name from the derived vocabulary (the SAME label
 *  the detail/themes page show — never renamed client-side). Falls back to the slug if absent. */
function themeNameForSlug(options: { slug: string; name: string }[], slug: string): string {
  return options.find((t) => t.slug === slug)?.name ?? slug;
}

/** A pattern badge tooltip: the server-built reason + pivot + invalidation note, rendered verbatim
 *  (never assembled client-side — single source of truth). */
function patternTitle(flag: PatternFlag): string {
  return [flag.reason, flag.pivot != null ? `Pivot $${flag.pivot.toFixed(2)}.` : null, flag.invalidation.note]
    .filter(Boolean)
    .join(" ");
}

function setupVariant(status: string): "ok" | "warn" | "danger" | "accent" | "default" {
  switch (status) {
    case "Actionable":
      return "ok";
    case "Breakout-watch":
    case "Pullback-watch":
      return "accent";
    case "Extended":
    case "Risk-off-watchlist":
      return "warn";
    case "Avoid":
      return "danger";
    default:
      return "default";
  }
}

/** Thin wrapper providing the Suspense boundary that `useSearchParams()` requires in the Next 15 App
 *  Router (a production-build requirement). All hooks live in StocksInner, inside the boundary. */
export default function StocksPage() {
  return (
    <Suspense fallback={<StocksSkeleton />}>
      <StocksInner />
    </Suspense>
  );
}

function StocksInner() {
  const { asOf } = useAsOf();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [state, setState] = useState<State>({ kind: "loading" });
  // Filters init ONCE from the URL (lazy initializers — read on mount only). `sector`/`setup` are taken
  // verbatim (an unmatched value harmlessly renders the existing honest empty-state); `pattern` is
  // strictly validated against the PATTERNS registry. These three filter params are the ONLY URL state —
  // the as-of date stays in the global asof-provider (useAsOf), never a query param (J-18).
  const [sector, setSector] = useState<string>(() => searchParams.get("sector") ?? ALL);
  const [setup, setSetup] = useState<string>(() => searchParams.get("setup") ?? ALL);
  const [pattern, setPattern] = useState<string>(() => parsePatternParam(searchParams.get("pattern")));
  // J-56 — the theme filter, init-once from `?theme=`. Like `sector`, the vocabulary is data-derived
  // (from the served rows' themes), so the raw slug is held verbatim; an unrecognized value never
  // crashes and fabricates no filter — the `visible` memo treats an out-of-vocabulary slug as inactive
  // (mirrors parsePatternParam's graceful "fall back to all" handling). Never a date param (J-18).
  const [theme, setTheme] = useState<string>(() => searchParams.get("theme") ?? ALL);
  // J-55 — the type-to-filter symbol search, init-once from `?q=`. A pure client-side view transform
  // (case-insensitive substring on ticker AND company name); no submit, no refetch (the [asOf]-keyed
  // fetch is untouched). Serialized as `?q=` like the other filter params, omitted when empty, never a
  // date (J-18). The trimmed/lowercased query is derived in the `visible` memo below.
  const [query, setQuery] = useState<string>(() => searchParams.get("q") ?? "");
  const [catalog, setCatalog] = useState<MethodologyCatalog | null>(null);
  // J-80 — the as-of date's market regime (from /api/dashboard) and theme ranking (from /api/themes),
  // re-displayed in the header. BOTH are read-only re-displays of canonical served values — the SAME
  // endpoints the Dashboard (J-06) and Themes pages read — never recomputed/re-ranked client-side. They
  // are keyed to [asOf] like the leaderboard fetch so changing the global as-of re-points all three.
  // Fetched NON-blocking: a failure renders an honest empty state and never breaks the leaderboard.
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [themes, setThemes] = useState<ThemesResponse | null>(null);
  // goal-mcp-loop iter-1 — the served proven-signal map (from /api/evidence). Default `{}` is the
  // FAIL-SAFE: until/unless evidence loads, every score badge reads "Not yet proven". The UI never
  // computes proven-ness — it only re-displays this served map. Against today's empty ledger this stays
  // `{}`, so every badge honestly reads "Not yet proven".
  const [provenSignals, setProvenSignals] = useState<Record<string, ProvenSignal>>({});
  // J-48: client-side sort state — PURE view transform. Initial state is the scanner's stored rank
  // (the `#` column ascending), so the leaderboard opens in the canonical stored order. Sort state is
  // deliberately NOT serialized to the URL (out of scope) — it is local view ergonomics only.
  const [sortKey, setSortKey] = useState<SortKey>(DEFAULT_SORT.key);
  const [sortDir, setSortDir] = useState<SortDir>(DEFAULT_SORT.dir);
  // J-50/J-54: the one shared helper builds every in-app href carrying the global as-of date while
  // historical (clean at latest) — used by the leaderboard row → detail links below.
  const asofHref = useAsOfHref();

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchStocks(asOf ?? undefined, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [asOf]);

  // J-80 — fetch the as-of date's regime (/api/dashboard) and theme ranking (/api/themes), keyed to the
  // SAME [asOf] as the leaderboard so all three re-point together. Non-blocking and independent: each
  // failure clears only its own header section (honest empty state), never the leaderboard. These are the
  // SAME canonical endpoints the Dashboard / Themes pages read — a pure re-display, no recompute/re-rank.
  useEffect(() => {
    const controller = new AbortController();
    setDashboard(null);
    setThemes(null);
    fetchDashboard(asOf ?? undefined, controller.signal)
      .then((data) => setDashboard(data))
      .catch(() => {
        if (!controller.signal.aborted) setDashboard(null);
      });
    fetchThemes(asOf ?? undefined, controller.signal)
      .then((data) => setThemes(data))
      .catch(() => {
        if (!controller.signal.aborted) setThemes(null);
      });
    return () => controller.abort();
  }, [asOf]);

  // The config-backed Setup & Pattern catalog (iter-12) — fetched independently of the as-of date
  // (config is global) and NON-blocking: a failure must NOT break the leaderboard or its filters
  // (graceful degradation protects J-02 and warm load J-15). It drives the badge definition tooltips
  // and the Setup-filter vocabulary below.
  useEffect(() => {
    const controller = new AbortController();
    fetchMethodology(controller.signal)
      .then((data) => setCatalog(data))
      .catch(() => {
        if (!controller.signal.aborted) setCatalog(null);
      });
    return () => controller.abort();
  }, []);

  // goal-mcp-loop iter-1 — fetch the certified-claims evidence ONCE (config-global, not as-of keyed; the
  // endpoint takes no params this iteration), NON-blocking: a failure leaves `provenSignals` at `{}` so
  // every badge falls back to "Not yet proven" and the leaderboard is never broken. The evidence ledger is
  // the single source of proven-ness — this only re-displays the served map (no client-side computation).
  useEffect(() => {
    const controller = new AbortController();
    fetchEvidence(controller.signal)
      .then((data) => setProvenSignals(data.proven_signals ?? {}))
      .catch(() => {
        if (!controller.signal.aborted) setProvenSignals({});
      });
    return () => controller.abort();
  }, []);

  // Reflect filter changes OUT to the URL so the view is shareable / back-navigable — WITHOUT a server
  // refetch (the fetchStocks effect above stays keyed to [asOf] only; J-15 warm load unchanged). State is
  // initialized from the URL once above and never driven FROM searchParams, so there is no state↔URL loop.
  // The mount run is skipped so only real filter changes are written; `__all__` values are omitted for
  // clean URLs. NO date/as_of param is ever written here (J-18 — the as-of stays in the global provider).
  const didReflectMount = useRef(false);
  useEffect(() => {
    if (!didReflectMount.current) {
      didReflectMount.current = true;
      return;
    }
    const params = new URLSearchParams();
    if (sector !== ALL) params.set("sector", sector);
    if (setup !== ALL) params.set("setup", setup);
    if (pattern !== ALL) params.set("pattern", pattern);
    if (theme !== ALL) params.set("theme", theme);
    // J-55: the search query serializes as `?q=` (trimmed) — omitted when empty for a clean URL, and
    // reflected on change exactly like the other filter params. Never a date/as_of param (J-18).
    const trimmedQuery = query.trim();
    if (trimmedQuery) params.set("q", trimmedQuery);
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  }, [sector, setup, pattern, theme, query, pathname, router]);

  const rows = state.kind === "ok" ? state.data.rows : [];

  // status -> catalog meaning (the SAME generic definition the /methodology page shows). The badge
  // tooltip renders this, NOT the per-row reason (which stays unchanged in the Reason column).
  const setupMeaning = useMemo(() => {
    const map = new Map<string, string>();
    catalog?.entries
      .filter((entry) => entry.kind === "setup")
      .forEach((entry) => map.set(entry.key, entry.meaning));
    return map;
  }, [catalog]);
  // pattern key -> catalog meaning (the SAME generic definition the /methodology page shows), for every
  // detected pattern. Keyed by config `key` so a new pattern's tooltip appears with no per-pattern code.
  const patternMeaning = useMemo(() => {
    const map = new Map<string, string>();
    catalog?.entries
      .filter((entry) => entry.kind === "pattern")
      .forEach((entry) => map.set(entry.key, entry.meaning));
    return map;
  }, [catalog]);
  // Setup-filter vocabulary: the catalog's setup entries in catalog order; graceful fallback to the
  // statuses present in the data if the catalog fetch failed (a catalog hiccup must NOT break J-02).
  const setupOptions = useMemo(() => {
    const fromCatalog = catalog?.entries
      .filter((entry) => entry.kind === "setup")
      .map((entry) => entry.key);
    if (fromCatalog && fromCatalog.length > 0) return fromCatalog;
    return Array.from(new Set(rows.map((row) => row.setup.status)));
  }, [catalog, rows]);

  // sectors present in the data, for the Sector filter (re-display of server rows only)
  const sectors = useMemo(
    () => Array.from(new Set(rows.map((r) => r.sector))).sort(),
    [rows],
  );

  // J-56 — the Theme filter vocabulary: every theme that appears in the served rows' membership chips,
  // in config order (the order the rows' `themes` arrays already carry — no client re-ordering). Keyed
  // by slug (the canonical id) with the shared display name (the SAME label the detail/themes page show
  // — never renamed client-side). A pure re-display of the served `row.themes` — no fetch, no recompute.
  const themeOptions = useMemo(() => {
    const seen = new Map<string, string>(); // slug -> name, first occurrence wins (config order)
    for (const row of rows) {
      for (const chip of row.themes) {
        if (!seen.has(chip.slug)) seen.set(chip.slug, chip.name);
      }
    }
    return Array.from(seen, ([slug, name]) => ({ slug, name }));
  }, [rows]);

  // J-56 graceful degradation: an `?theme=` slug not present in the served vocabulary is treated as
  // INACTIVE (fabricates no filter — mirrors parsePatternParam falling back to "all"), so an unknown
  // value never crashes and never hides every row behind a phantom filter. The select itself only ever
  // offers in-vocabulary slugs, so this only matters for a hand-typed/stale deep-link.
  const themeActive = theme !== ALL && themeOptions.some((t) => t.slug === theme);

  // J-80 — the served theme ranking, read VERBATIM from /api/themes (the SAME `rank`/`score` the Themes
  // leaderboard uses, in the SAME descending order). `rankedThemes` (rank ascending) drives the header
  // Top-Themes strip; `themeRank` (slug → served rank) drives the `#n` badges on the row theme chips and
  // the theme-filter options. NO client re-ranking — the served `rank` is surfaced as-is.
  const rankedThemes = useMemo(
    () => (themes ? [...themes.rows].sort((a, b) => a.rank - b.rank) : []),
    [themes],
  );
  const themeRank = useMemo(() => {
    const map = new Map<string, number>();
    for (const t of themes?.rows ?? []) map.set(t.slug, t.rank);
    return map;
  }, [themes]);

  // client-side FILTER only — never re-sorts or recomputes a score/flag (single source of truth). The
  // pattern filter narrows on the SERVER-computed `row.<name>.flagged` (pure re-display, no detection).
  // The `pattern` value is `__all__`, or `<key>__only` / `<key>__none` for a specific detected pattern.
  // J-55 search (case-insensitive substring on ticker OR company name) and J-56 theme filter (membership
  // contains the selected slug) compose here as additional narrowing predicates over the SAME served
  // rows — pure view transforms, no second compute path. The trimmed/lowercased query is derived once.
  const visible = useMemo(() => {
    const [patternKey, patternMode] = pattern === ALL ? [null, null] : pattern.split("__");
    const patternEntry = patternKey ? PATTERNS.find((p) => p.key === patternKey) : null;
    const q = query.trim().toLowerCase();
    return rows.filter((r) => {
      if (sector !== ALL && r.sector !== sector) return false;
      if (setup !== ALL && r.setup.status !== setup) return false;
      if (patternEntry) {
        const flagged = patternEntry.get(r).flagged;
        if (patternMode === "only" ? !flagged : flagged) return false;
      }
      // J-56 theme filter: keep only rows whose served membership contains the selected slug. An
      // out-of-vocabulary slug is inactive (themeActive guard), so it narrows nothing (no phantom filter).
      if (themeActive && !r.themes.some((t) => t.slug === theme)) return false;
      // J-55 symbol search: case-insensitive substring on the served ticker AND company name.
      if (q && !r.ticker.toLowerCase().includes(q) && !r.name.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [rows, sector, setup, pattern, theme, themeActive, query]);

  // client-side SORT only — a PURE, STABLE view transform layered ON TOP of the filter memo above
  // (filter THEN sort compose). It re-orders the already-served, already-filtered rows; it NEVER
  // recomputes, re-ranks, or re-formats a single served value — the rank `#`, the six scores, the A–E
  // buckets, the setup status, and the pattern flags all read exactly as the API served them (single
  // source of truth → J-06/J-16). Stability: rows are tagged with their pre-sort index and ties fall
  // back to it, so equal-key rows keep their incoming (stored-rank) order — and the default `rank`-asc
  // sort reproduces the stored scanner order exactly. There is no second fetch and no second endpoint.
  const sorted = useMemo(() => {
    const cmp = comparatorFor(sortKey, sortDir); // already applies the direction sign (J-75 NA-last)
    return visible
      .map((row, index) => ({ row, index }))
      .sort((a, b) => {
        const primary = cmp(a.row, b.row);
        // Stable tie-break: preserve the incoming order (which for the unsorted default IS stored rank).
        return primary !== 0 ? primary : a.index - b.index;
      })
      .map((entry) => entry.row);
  }, [visible, sortKey, sortDir]);

  // J-75 — the forward-return column horizons, derived from the SERVED rows (config-driven; no hardcoded
  // [1,5,10,20,60] in the UI). Read from the first row's `forward_returns` order.
  const fwdHorizons = useMemo<number[]>(
    () => (rows.length > 0 ? rows[0].forward_returns.map((fr) => fr.horizon) : []),
    [rows],
  );

  // Toggle/select sort on a header click: a NEW column adopts that column's natural lead direction
  // (text columns ascend A→Z; the `#`/rank and score columns also start ascending); clicking the
  // ACTIVE column toggles asc⇄desc. Clicking `#` always restores the default stored-rank ascending
  // order (J-48 acceptance: the `#` header restores the scanner's stored rank on demand).
  const onSort = (key: SortKey) => {
    if (key === "rank") {
      setSortKey(DEFAULT_SORT.key);
      setSortDir(DEFAULT_SORT.dir);
      return;
    }
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      // J-75: forward-return columns lead descending (best return first); other columns ascend.
      setSortDir(key.startsWith("fwd_") ? "desc" : "asc");
    }
  };

  // a plain-language label for the active pattern filter, used only in the honest empty-state copy.
  const patternFilterLabel = useMemo(() => {
    if (pattern === ALL) return null;
    const [key, mode] = pattern.split("__");
    const entry = PATTERNS.find((p) => p.key === key);
    if (!entry) return null;
    return mode === "only" ? `${entry.label}-flagged` : `non-${entry.label}`;
  }, [pattern]);

  return (
    <div className="space-y-4">
      <PageHeading
        title="Stocks"
        subtitle="Stock Leaderboard — ranked by Leadership, with independent Entry Quality and Risk (danger) scores, a setup status and a reason"
      />

      {/* J-80 — the as-of date's market regime + ranked Top-Themes strip. A pure re-display of the
          canonical /api/dashboard regime and /api/themes ranking (identical to the Dashboard/Themes for
          this date) — never recomputed. Hidden while the leaderboard itself errored (the regime/theme
          context has no meaning without the leaderboard). */}
      {state.kind !== "error" ? (
        <RegimeThemeHeader dashboard={dashboard} rankedThemes={rankedThemes} asofHref={asofHref} />
      ) : null}

      {state.kind === "ok" && rows.length > 0 ? (
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant="default" className="num">
            as of {formatIsoDate(state.data.asof_date)}
          </Badge>
          {/* J-55 — the type-to-filter symbol search. No submit affordance and no Enter handler: the
              `value`/`onChange` binding narrows the view per keystroke. `type="search"` gives the native
              clear "x". It re-displays/narrows the already-served rows only — it never refetches (the
              [asOf]-keyed fetch above is untouched). */}
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-faint"
              aria-hidden
            />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search ticker or name…"
              aria-label="Search by ticker or company name"
              data-testid="stocks-search"
              className="h-9 w-56 rounded-md border border-border bg-surface-2 pl-8 pr-3 text-sm text-text placeholder:text-text-faint transition-colors hover:border-border-strong focus-visible:border-accent focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
            />
          </div>
          <label className="flex items-center gap-2 text-xs text-text-muted">
            Sector
            <Select value={sector} onChange={(e) => setSector(e.target.value)} aria-label="Filter by sector">
              <option value={ALL}>All sectors</option>
              {sectors.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex items-center gap-2 text-xs text-text-muted">
            Setup
            <Select value={setup} onChange={(e) => setSetup(e.target.value)} aria-label="Filter by setup status">
              <option value={ALL}>All setups</option>
              {setupOptions.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex items-center gap-2 text-xs text-text-muted">
            Pattern
            <Select value={pattern} onChange={(e) => setPattern(e.target.value)} aria-label="Filter by detected pattern">
              <option value={ALL}>All patterns</option>
              {PATTERNS.map((p) => (
                <optgroup key={p.key} label={p.label}>
                  <option value={`${p.key}__only`}>{p.label} only</option>
                  <option value={`${p.key}__none`}>Not {p.label}</option>
                </optgroup>
              ))}
            </Select>
          </label>
          {/* J-56 — the Theme filter. Its vocabulary is the served rows' themes in config order (like the
              Sector filter derives from rows). Keeps exactly the rows whose membership contains the slug. */}
          <label className="flex items-center gap-2 text-xs text-text-muted">
            Theme
            <Select value={theme} onChange={(e) => setTheme(e.target.value)} aria-label="Filter by theme">
              <option value={ALL}>All themes</option>
              {themeOptions.map((t) => {
                // J-80 — prefix the served `#n` rank (from /api/themes) when known; the option value/order
                // (J-56 config order) is unchanged — only the visible label gains the rank badge.
                const rank = themeRank.get(t.slug);
                return (
                  <option key={t.slug} value={t.slug}>
                    {rank != null ? `#${rank} · ${t.name}` : t.name}
                  </option>
                );
              })}
            </Select>
          </label>
          <span className="num text-xs text-text-faint" data-testid="visible-count">
            {visible.length} / {rows.length}
          </span>
        </div>
      ) : null}

      {state.kind === "loading" ? <StocksSkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The Stock Leaderboard could not load from the API. No rankings are shown rather than
              fabricated values. Confirm the backend is running and retry.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" && rows.length === 0 ? (
        <EmptyState
          icon={TrendingUp}
          title="No ranked stocks at this date"
          description={
            "The point-in-time universe is honestly EMPTY at this as-of — no candidate yet has the required " +
            "history, price, and liquidity from bars on or before this date (a warm-up date; the universe " +
            "fills out as history accrues). No rows are fabricated. Step the global as-of forward to a later " +
            "date, or see Data Manager → Universe resolution for the per-date admitted/excluded breakdown."
          }
        />
      ) : null}

      {state.kind === "ok" && rows.length > 0 && visible.length === 0 ? (
        <EmptyState
          icon={query.trim() ? Search : TrendingUp}
          title={query.trim() ? "No stocks match" : "No stocks match these filters"}
          description={`${
            patternFilterLabel ? `No ${patternFilterLabel} name` : "No stock"
          } is currently ${setup !== ALL ? `“${setup}”` : "shown"}${
            sector !== ALL ? ` in ${sector}` : ""
          }${themeActive ? ` in the ${themeNameForSlug(themeOptions, theme)} theme` : ""}${
            query.trim() ? ` matching “${query.trim()}”` : ""
          }. No rows are fabricated to fill the view — clear a filter or the search to see more.`}
        />
      ) : null}

      {state.kind === "ok" && visible.length > 0 ? (
        <Card className="overflow-x-auto p-0">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
                <SortHeader col="rank" label="#" activeKey={sortKey} dir={sortDir} onSort={onSort} />
                <SortHeader col="ticker" label="Ticker" activeKey={sortKey} dir={sortDir} onSort={onSort} />
                <SortHeader col="sector" label="Sector" activeKey={sortKey} dir={sortDir} onSort={onSort} />
                <SortHeader
                  col="leadership"
                  label="Leadership"
                  term="Leadership Score"
                  activeKey={sortKey}
                  dir={sortDir}
                  onSort={onSort}
                />
                <SortHeader
                  col="entry_quality"
                  label="Entry Quality"
                  term="Entry Quality Score"
                  activeKey={sortKey}
                  dir={sortDir}
                  onSort={onSort}
                />
                <SortHeader
                  col="risk"
                  label="Risk"
                  term="Risk Score"
                  activeKey={sortKey}
                  dir={sortDir}
                  onSort={onSort}
                />
                {/* J-106 — "Proximity to 52w high", directly after Risk. A re-display of the stored
                    leadership `high_proximity` value (the SAME value the detail Leadership breakdown
                    shows; never recomputed), client-side sortable (NA-last). The header carries the
                    config-backed glossary tooltip via TermInfo (`52-week high proximity`). */}
                <SortHeader
                  col="high_proximity"
                  label="Proximity to 52w high"
                  term="52-week high proximity"
                  activeKey={sortKey}
                  dir={sortDir}
                  onSort={onSort}
                />
                <SortHeader
                  col="setup"
                  label="Setup"
                  term="setup status"
                  activeKey={sortKey}
                  dir={sortDir}
                  onSort={onSort}
                />
                {/* J-75 — five realized forward-return columns (1/5/10/20/60-day from config horizons),
                    each client-side sortable (view transform, NA-last). The horizons are server-driven
                    (from the row payload), so no hardcoded horizon list lives in the UI. */}
                {fwdHorizons.map((h) => (
                  <SortHeader
                    key={`fwd_${h}`}
                    col={`fwd_${h}` as SortKey}
                    label={`${h}d`}
                    term="forward return"
                    activeKey={sortKey}
                    dir={sortDir}
                    onSort={onSort}
                  />
                ))}
                {/* J-86 — five PAIRED max-drawdown columns (1/5/10/20/60-day), to the RIGHT of the forward
                    returns, each client-side sortable (view transform, NA-last). MDD is <= 0, read verbatim
                    from the stored forward_returns. Server-driven horizons (no hardcoded list). */}
                {fwdHorizons.map((h) => (
                  <SortHeader
                    key={`mdd_${h}`}
                    col={`mdd_${h}` as SortKey}
                    label={`${h}d MDD`}
                    term="max drawdown"
                    activeKey={sortKey}
                    dir={sortDir}
                    onSort={onSort}
                  />
                ))}
                {/* J-56 — the Theme column. Non-sortable (a re-display of the served membership chips),
                    so a plain header (no SortHeader): membership is a set, not an orderable scalar. */}
                <th className="px-3 py-2 font-medium">
                  <TermInfo term="Theme Score">Themes</TermInfo>
                </th>
                <th className="px-3 py-2 font-medium">
                  <TermInfo term="reason summary">Reason</TermInfo>
                </th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((row) => (
                <StockTableRow
                  key={row.ticker}
                  row={row}
                  href={asofHref(`/stocks/${row.ticker}`)}
                  setupMeaning={setupMeaning.get(row.setup.status)}
                  patternMeaning={patternMeaning}
                  fwdHorizons={fwdHorizons}
                  themeRank={themeRank}
                  provenSignals={provenSignals}
                />
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
    </div>
  );
}

/** J-80 — how many ranked themes the header Top-Themes strip shows (mirrors the Dashboard's Top Themes
 *  slice of 5). The `#n` rank badges on the row chips / theme filter still use the FULL served ranking. */
const TOP_THEMES_STRIP_LIMIT = 5;

/** J-80 — the Stocks header band: the as-of date's market-regime label + 0–100 score (re-displayed from
 *  /api/dashboard, identical to the Dashboard for this date — J-06) and a ranked Top-Themes strip
 *  (re-displayed from /api/themes in the SAME descending order the Themes page uses). Pure re-display of
 *  served canonical values — nothing recomputed or re-ranked here. Each section shows an honest empty
 *  state when its data is absent (a date with no ranked themes never fabricates a #1 theme). */
function RegimeThemeHeader({
  dashboard,
  rankedThemes,
  asofHref,
}: {
  dashboard: DashboardResponse | null;
  /** The served themes, rank ascending (the SAME `rank`/`score` /api/themes serves). */
  rankedThemes: ThemeRow[];
  /** The J-50 href builder — stamps `?asof=D` onto the `/themes` link while historical. */
  asofHref: (path: string) => string;
}) {
  const regime = dashboard?.regime ?? null;
  const topThemes = rankedThemes.slice(0, TOP_THEMES_STRIP_LIMIT);
  return (
    <Card className="flex flex-wrap items-center gap-x-6 gap-y-3 p-4" data-testid="stocks-regime-theme-header">
      {/* Market regime — label + 0–100 score, the SAME stored value the Dashboard shows (J-06). */}
      <div className="flex items-center gap-2" data-testid="stocks-regime">
        <span className="text-xs uppercase tracking-wide text-text-faint">
          <TermInfo term="market regime">Market regime</TermInfo>
        </span>
        {regime ? (
          <>
            <Badge variant={regimeVariant(regime.label)}>{regime.label}</Badge>
            <span className="num text-sm font-semibold text-text" data-testid="stocks-regime-score">
              {regime.score.toFixed(2)}
            </span>
          </>
        ) : (
          <span className="text-xs text-text-muted" data-testid="stocks-regime-empty">
            No regime for this date
          </span>
        )}
      </div>

      {/* Ranked Top-Themes strip — descending Theme Score (1 · …, 2 · …); each links to /themes. */}
      <div className="flex flex-wrap items-center gap-2" data-testid="stocks-top-themes">
        <span className="text-xs uppercase tracking-wide text-text-faint">
          <TermInfo term="Theme Score">Top themes</TermInfo>
        </span>
        {topThemes.length > 0 ? (
          topThemes.map((t) => (
            <Link
              key={t.slug}
              href={asofHref("/themes")}
              data-testid="stocks-top-theme"
              className={cn(
                "inline-flex items-center gap-1.5 rounded-md border border-border bg-surface-2 px-2 py-0.5 text-xs text-text-muted",
                "transition-colors hover:border-border-strong hover:text-text",
                "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
              )}
            >
              <span className="num text-text-faint">{t.rank}</span>
              <span className="text-text-faint">·</span>
              <span className="whitespace-nowrap text-text">{t.name}</span>
            </Link>
          ))
        ) : (
          <span className="text-xs text-text-muted" data-testid="stocks-top-themes-empty">
            No ranked themes for this date
          </span>
        )}
      </div>
    </Card>
  );
}

/** J-75 — one colour-graded forward-return cell: the served realized return (NA → "NA" muted), read
 *  verbatim. Positive green / negative red via the shared palette helper (same as the evidence tables). */
function ForwardReturnCell({ value }: { value: number | null }) {
  if (value === null || value === undefined) {
    return (
      <span className="num text-text-muted" title="No realized forward return at this horizon yet (NA)">
        NA
      </span>
    );
  }
  return <span className={cn("num font-semibold", returnClass(value))}>{fmtPct(value)}</span>;
}

/** J-106 — the "Proximity to 52w high" cell: the stored leadership `high_proximity` value (a percent
 *  <= 0; 0 at a fresh high), read VERBATIM via the shared helper — the SAME value the detail Leadership
 *  breakdown shows (single source; never recomputed). NA (short history) renders a muted "NA" that sorts
 *  last; a real value reads in the default numeric style (right-aligned `num`), matching the other cells. */
function HighProximityCell({ value }: { value: number | null }) {
  if (value === null || value === undefined) {
    return (
      <span className="num text-text-muted" title="No 52-week-high proximity yet (NA — short history)">
        NA
      </span>
    );
  }
  return <span className="num text-text">{fmtHighProximity(value)}</span>;
}

/** J-86 — one colour-graded max-drawdown cell: the served realized drawdown (<= 0; NA → "NA" muted), read
 *  verbatim. A real (negative) drawdown reads red via the shared `mddClass` helper. */
function MaxDrawdownCell({ value }: { value: number | null }) {
  if (value === null || value === undefined) {
    return (
      <span className="num text-text-muted" title="No realized max drawdown at this horizon yet (NA)">
        NA
      </span>
    );
  }
  return <span className={cn("num font-semibold", mddClass(value))}>{fmtMdd(value)}</span>;
}

function StockTableRow({
  row,
  href,
  setupMeaning,
  patternMeaning,
  fwdHorizons,
  themeRank,
  provenSignals,
}: {
  row: StockRow;
  /** The detail href, pre-built by the J-50 helper so it already carries `?asof=D` while historical. */
  href: string;
  setupMeaning?: string;
  patternMeaning: Map<string, string>;
  /** J-75 — the server-driven forward-return column horizons (config order), rendered as five cells. */
  fwdHorizons: number[];
  /** J-80 — served theme `rank` by slug (from /api/themes), for the `#n` chip badge. */
  themeRank: Map<string, number>;
  /** goal-mcp-loop iter-1 — the served proven-signal map; drives each score's evidence-status badge. */
  provenSignals: Record<string, ProvenSignal>;
}) {
  return (
    <tr className="border-b border-border transition-colors hover:bg-surface-2">
      <td className="num px-3 py-2 text-text-faint">{row.rank}</td>
      <td className="px-3 py-2">
        {/* J-54: the leaderboard ticker opens the stock detail in a NEW tab (the only in-app link that
            does — every other link stays same-window). The `href` is the J-50 helper's output, so the
            new tab lands on `/stocks/[ticker]?asof=D` while historical (clean at latest). `rel` carries
            `noopener noreferrer` for new-tab safety. */}
        <Link
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="num font-semibold text-accent hover:underline focus-visible:underline focus-visible:outline-none"
        >
          {row.ticker}
        </Link>
      </td>
      <td className="px-3 py-2 text-xs text-text-muted">{row.sector}</td>
      {/* goal-mcp-loop iter-1 — each score now carries an inline evidence-status badge BELOW it (purely
          additive; the ScoreBadge value is unchanged). Against the empty ledger every badge reads
          "Not yet proven". */}
      <td className="px-3 py-2">
        <div className="flex flex-col items-start gap-1">
          <ScoreBadge bucket={row.leadership.bucket} score={row.leadership.score} />
          <EvidenceStatusBadge signal={SCORE_SIGNALS.leadership} provenSignals={provenSignals} />
        </div>
      </td>
      <td className="px-3 py-2">
        <div className="flex flex-col items-start gap-1">
          <ScoreBadge bucket={row.entry_quality.bucket} score={row.entry_quality.score} />
          <EvidenceStatusBadge signal={SCORE_SIGNALS.entry_quality} provenSignals={provenSignals} />
        </div>
      </td>
      <td className="px-3 py-2">
        <div className="flex flex-col items-start gap-1">
          <ScoreBadge bucket={row.risk.bucket} score={row.risk.score} invert />
          <EvidenceStatusBadge signal={SCORE_SIGNALS.risk} provenSignals={provenSignals} />
        </div>
      </td>
      {/* J-106 — proximity-to-52w-high cell, directly after Risk. Re-displays the stored leadership
          `high_proximity` value verbatim (the SAME value the detail Leadership breakdown shows; never
          recomputed); NA-honest (muted "NA") on short history. */}
      <td className="px-3 py-2 text-right" data-testid="high-proximity">
        <HighProximityCell value={highProximityValue(row.leadership.components)} />
      </td>
      <td className="px-3 py-2">
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant={setupVariant(row.setup.status)}>{row.setup.status}</Badge>
          {setupMeaning ? (
            <InfoTooltip label={`Definition of ${row.setup.status}`} content={setupMeaning} />
          ) : null}
          {PATTERNS.filter((p) => p.get(row).flagged).map((p) => {
            const meaning = patternMeaning.get(p.key);
            return (
              <span key={p.key} className="inline-flex items-center gap-1">
                <Badge variant="accent" className="cursor-help" title={patternTitle(p.get(row))}>
                  {p.badge}
                </Badge>
                {meaning ? (
                  <InfoTooltip label={`Definition of the ${p.label} pattern`} content={meaning} />
                ) : null}
              </span>
            );
          })}
        </div>
      </td>
      {/* J-75 — five realized forward-return cells (config horizons, colour-graded, NA where no stored
          row). Read verbatim from the served row — never recomputed. */}
      {fwdHorizons.map((h) => (
        <td key={`fwd_${h}`} className="px-3 py-2 text-right" data-testid={`fwd-${h}`}>
          <ForwardReturnCell value={fwdReturnAt(row, h)} />
        </td>
      ))}
      {/* J-86 — five PAIRED max-drawdown cells (to the right of the forward returns), colour-graded on the
          negative scale (<= 0), NA where the return is NA. Read verbatim — never recomputed. */}
      {fwdHorizons.map((h) => (
        <td key={`mdd_${h}`} className="px-3 py-2 text-right" data-testid={`mdd-${h}`}>
          <MaxDrawdownCell value={fwdMddAt(row, h)} />
        </td>
      ))}
      <td className="px-3 py-2">
        <ThemeChips themes={row.themes} themeRank={themeRank} />
      </td>
      <td className="max-w-xs px-3 py-2 text-xs text-text-muted">
        <span className="line-clamp-2" title={row.setup.reason}>
          {row.setup.reason}
        </span>
      </td>
    </tr>
  );
}

/** J-56 — the Theme cell: re-displays the row's already-served `themes` chips VERBATIM (the same
 *  config-derived membership the Stock Detail page shows — J-06; nothing fetched or recomputed per row).
 *  A row in many themes shows the first `THEME_PREVIEW_LIMIT` chips plus a `+n` overflow whose full
 *  membership is readable IN PLACE via the `title` tooltip — a plain non-interactive <span>, NOT a nested
 *  interactive element inside any control (iter-5 nested-button lesson). Empty membership renders a dash. */
const THEME_PREVIEW_LIMIT = 3;

function ThemeChips({
  themes,
  themeRank,
}: {
  themes: StockRow["themes"];
  /** J-80 — served theme `rank` by slug (from /api/themes); a chip with a known rank gets a `#n` badge. */
  themeRank: Map<string, number>;
}) {
  if (themes.length === 0) {
    return <span className="text-xs text-text-faint">—</span>;
  }
  const shown = themes.slice(0, THEME_PREVIEW_LIMIT);
  const overflow = themes.slice(THEME_PREVIEW_LIMIT);
  return (
    <div className="flex flex-wrap items-center gap-1" data-testid="theme-chips">
      {shown.map((chip) => {
        const rank = themeRank.get(chip.slug);
        return (
          <Badge key={chip.slug} variant="default" className="whitespace-nowrap text-[11px]">
            {/* J-80 — the served `#n` rank badge (omitted when the theme has no served rank — never a
                fabricated rank). The chip name is unchanged (J-56). */}
            {rank != null ? (
              <span className="num text-text-faint" data-testid="theme-chip-rank">
                #{rank}
              </span>
            ) : null}
            {chip.name}
          </Badge>
        );
      })}
      {overflow.length > 0 ? (
        // The `+n` overflow: a plain <span> (NOT a button/link — no nested interactive element), the full
        // remaining membership readable in place via the native `title` tooltip (iter-5-safe affordance).
        <span
          className="num cursor-help text-[11px] text-text-faint"
          title={`Also in: ${overflow.map((c) => c.name).join(", ")}`}
          data-testid="theme-overflow"
        >
          +{overflow.length}
        </span>
      ) : null}
    </div>
  );
}

/** J-48 — a sortable column header. Renders a button (keyboard + click accessible) that sorts by `col`
 *  and shows the sort indicator ONLY on the active column, so exactly one indicator is visible at a time
 *  across the whole header row. Inactive columns show a faint neutral up/down glyph as the affordance.
 *  `label` is the visible header text; an optional `term` renders a definition info affordance BESIDE
 *  the sort button (a sibling, never nested inside it — valid DOM, iter-6 nested-button fix). */
function SortHeader({
  col,
  label,
  term,
  activeKey,
  dir,
  onSort,
}: {
  col: SortKey;
  /** The visible column label (also the sort button's accessible name). */
  label: string;
  /** Optional glossary term — renders a definition info affordance BESIDE the sort button (NOT inside
   *  it, so the info `<button>` is never nested in the sort `<button>` — valid DOM; iter-6 fix). */
  term?: string;
  activeKey: SortKey;
  dir: SortDir;
  onSort: (key: SortKey) => void;
}) {
  const active = activeKey === col;
  const ariaSort: "ascending" | "descending" | "none" = active
    ? dir === "asc"
      ? "ascending"
      : "descending"
    : "none";
  return (
    <th className="px-3 py-2 font-medium" aria-sort={ariaSort}>
      {/* The sort control and the term-definition affordance are SIBLINGS — the info trigger lives
          outside the sort <button> so no interactive element is nested in another (valid DOM), and
          clicking the info icon never triggers a sort (the icon also stops propagation defensively). */}
      <span className="inline-flex items-center gap-1">
        <button
          type="button"
          onClick={() => onSort(col)}
          aria-label={`Sort by ${label}${active ? (dir === "asc" ? ", ascending" : ", descending") : ""}`}
          className="group inline-flex items-center gap-1 rounded-sm uppercase tracking-wide transition-colors hover:text-text focus-visible:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
        >
          <span className={cn(active && "text-text")}>{label}</span>
          {active ? (
            dir === "asc" ? (
              <ArrowUp className="h-3 w-3 text-accent" aria-hidden data-testid="sort-indicator" />
            ) : (
              <ArrowDown className="h-3 w-3 text-accent" aria-hidden data-testid="sort-indicator" />
            )
          ) : (
            <ArrowUpDown
              className="h-3 w-3 text-text-faint/40 opacity-0 transition-opacity group-hover:opacity-100"
              aria-hidden
            />
          )}
        </button>
        {term ? <TermInfo term={term} /> : null}
      </span>
    </th>
  );
}

function StocksSkeleton() {
  return (
    <Card className="space-y-2 p-4">
      {Array.from({ length: 10 }).map((_, i) => (
        <div key={i} className="h-8 w-full animate-pulse rounded bg-surface-2" />
      ))}
    </Card>
  );
}
