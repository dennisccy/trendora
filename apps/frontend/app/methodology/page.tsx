"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, BookOpen, Filter, Search } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  fetchMethodology,
  type GlossaryTerm,
  type MethodologyCatalog,
  type MethodologyEntry,
  type MethodologyGlossary,
  type MethodologyThresholdRow,
  type UniverseSelection,
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
        subtitle="What every setup status and detected price pattern mean — with the exact config thresholds that define each (read live from config, so they always match the scanner) and a worked example."
      />

      {state.kind === "ok" && state.data.intro ? (
        <Card className="p-4 text-sm text-text-muted">{state.data.intro}</Card>
      ) : null}

      {state.kind === "ok" && state.data.universe_selection ? (
        <UniverseSelectionCard selection={state.data.universe_selection} />
      ) : null}

      {state.kind === "ok" && state.data.sector_basis ? (
        <SectorBasisCard sectorBasis={state.data.sector_basis} />
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

      {state.kind === "ok" && state.data.glossary ? (
        <GlossarySection glossary={state.data.glossary} />
      ) : null}
    </div>
  );
}

/** The J-47 terminology Glossary section — the categorized, client-side-searchable ≥100-term list read
 *  from the SAME served catalog (single source of truth; the inline tooltips read these very entries).
 *  Search filters live on term + definition; an empty match shows an honest empty state. */
function GlossarySection({ glossary }: { glossary: MethodologyGlossary }) {
  const [query, setQuery] = useState("");

  const normalized = query.trim().toLowerCase();
  const totalTerms = useMemo(
    () => glossary.categories.reduce((sum, category) => sum + category.terms.length, 0),
    [glossary],
  );

  // Live client-side filter on term + definition (e.g. "IC" narrows to rank-IC). Categories with no
  // matching terms are dropped so the result reads cleanly; catalog order is preserved.
  const filtered = useMemo(() => {
    if (!normalized) return glossary.categories;
    return glossary.categories
      .map((category) => ({
        ...category,
        terms: category.terms.filter(
          (term) =>
            term.term.toLowerCase().includes(normalized) ||
            term.definition.toLowerCase().includes(normalized),
        ),
      }))
      .filter((category) => category.terms.length > 0);
  }, [glossary, normalized]);

  const matchCount = filtered.reduce((sum, category) => sum + category.terms.length, 0);

  return (
    <section className="space-y-3" data-testid="glossary-section">
      <div className="flex flex-wrap items-center gap-2 pt-2">
        <BookOpen className="h-4 w-4 text-accent" aria-hidden />
        <h2 className="text-base font-semibold text-text">Glossary</h2>
        <span className="text-xs text-text-faint">
          {totalTerms} terms across {glossary.categories.length} categories — every word the UI uses,
          from this one config-backed catalog.
        </span>
      </div>

      <div className="relative max-w-md">
        <Search
          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint"
          aria-hidden
        />
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search terms and definitions…"
          aria-label="Search the glossary"
          data-testid="glossary-search"
          className="w-full rounded-md border border-border bg-surface py-2 pl-9 pr-3 text-sm text-text placeholder:text-text-faint transition-colors focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        />
      </div>

      {normalized ? (
        <p className="text-xs text-text-faint" data-testid="glossary-match-count">
          {matchCount} match{matchCount === 1 ? "" : "es"} for{" "}
          <span className="text-text">&ldquo;{query.trim()}&rdquo;</span>
        </p>
      ) : null}

      {matchCount === 0 ? (
        <EmptyState
          icon={Search}
          title="No matching terms"
          description="No glossary term or definition matches your search. Clear the box or try a different word."
        />
      ) : (
        <div className="space-y-4">
          {filtered.map((category) => (
            <Card key={category.key} className="space-y-3 p-4" data-category-key={category.key}>
              <h3 className="text-sm font-semibold uppercase tracking-wide text-accent">
                {category.label}
              </h3>
              <ul className="space-y-2">
                {category.terms.map((term) => (
                  <GlossaryRow key={term.term} term={term} />
                ))}
              </ul>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}

/** One glossary term row — the literal UI term, its plain-language definition, an optional where-note,
 *  and any resolved threshold references. Pure presentation of the served entry (no recompute). */
function GlossaryRow({ term }: { term: GlossaryTerm }) {
  return (
    <li className="border-b border-border pb-2 last:border-b-0 last:pb-0" data-term={term.term}>
      <div className="flex flex-wrap items-baseline gap-2">
        <span className="font-medium text-text">{term.term}</span>
        {term.kind ? (
          <Badge variant={term.kind === "pattern" ? "accent" : "default"}>
            {term.kind === "pattern" ? "Pattern" : "Setup"}
          </Badge>
        ) : null}
      </div>
      <p className="text-sm text-text-muted">{term.definition}</p>
      {term.where ? (
        <p className="text-xs text-text-faint">
          <span className="uppercase tracking-wide">Where: </span>
          {term.where}
        </p>
      ) : null}
      {term.thresholds && term.thresholds.length > 0 ? (
        <ul className="mt-1 space-y-0.5">
          {term.thresholds.map((row, index) => (
            <ThresholdRow key={index} row={row} />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

/** Compact currency for the screen thresholds — display formatting of the API value ONLY (e.g.
 *  2_000_000_000 -> "$2B", 50_000_000 -> "$50M", 10 -> "$10"). The number is never recomputed. */
function fmtMoney(value: number): string {
  if (value >= 1e9) return `$${Number((value / 1e9).toFixed(1)).toString()}B`;
  if (value >= 1e6) return `$${Number((value / 1e6).toFixed(1)).toString()}M`;
  if (value >= 1e3) return `$${Number((value / 1e3).toFixed(1)).toString()}K`;
  return `$${value}`;
}

/** The Universe Selection section (J-22 / J-93) — the membership rule + the three config screen
 *  thresholds (read live from config) + the resolved universe size, plus the J-93 per-as-of-date
 *  membership rule (the `per_date_rule` prose, the `candidate_pool_size` full-pool denominator, and the
 *  `per_date_min_history_bars` warm-up bar count). Mirrors the EntryCard config-backed pattern; no
 *  hard-coded copy or numbers — every value is read verbatim from the GET /api/methodology payload.
 *  (The J-01 sector-basis disclosure is its own `SectorBasisCard` — this card is gated off until the
 *  committed screen record exists, and that disclosure must stay readable regardless.) */
function UniverseSelectionCard({ selection }: { selection: UniverseSelection }) {
  return (
    <Card className="space-y-3 p-4" data-testid="universe-selection">
      <div className="flex flex-wrap items-center gap-2">
        <Filter className="h-4 w-4 text-accent" aria-hidden />
        <h2 className="text-base font-semibold text-text">Universe Selection</h2>
        <Badge variant="accent">Screen</Badge>
        <span className="ml-auto text-xs text-text-faint">
          Resolved universe:{" "}
          <span className="num text-text" data-testid="universe-size">
            {selection.resolved_size}
          </span>{" "}
          names
        </span>
      </div>
      <p className="text-sm text-text-muted">{selection.membership_rule}</p>

      <div className="space-y-1.5">
        <p className="text-xs uppercase tracking-wide text-text-faint">Screen thresholds</p>
        <ul className="space-y-1">
          {selection.thresholds.map((row, index) => (
            <li key={index} className="flex items-center gap-2 text-xs text-text-muted">
              <span className="w-64 shrink-0 text-text">{row.label}</span>
              <span className="num text-text-faint">{row.cmp}</span>
              <span className="num text-text">
                {row.unit === "$" && row.value != null ? fmtMoney(row.value) : `${row.value ?? ""}${row.unit ?? ""}`}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="space-y-1.5 border-t border-border pt-3" data-testid="universe-per-date-rule">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-xs uppercase tracking-wide text-text-faint">Per-date membership rule</p>
          <Badge variant="default">As-of</Badge>
        </div>
        <p className="text-sm text-text-muted">{selection.per_date_rule}</p>
        <p className="text-xs text-text-faint">
          Candidate pool:{" "}
          <span className="num text-text" data-testid="universe-candidate-pool-size">
            {selection.candidate_pool_size}
          </span>{" "}
          names · Minimum history:{" "}
          <span className="num text-text" data-testid="universe-per-date-min-history-bars">
            {selection.per_date_min_history_bars}
          </span>{" "}
          trailing bars
        </p>
      </div>
    </Card>
  );
}

/** The J-01 (goal-market-compass iter-1) two-source stock-sector-label disclosure: curated
 *  `config.stock_sectors` first, the committed `universe_pool.csv` fallback second, plus the
 *  current-only limitation. Rendered as its OWN card, NOT inside UniverseSelectionCard, because that
 *  card is suppressed by the backend's J-22 honest-universe gate until the committed screen record
 *  exists — this disclosure makes no screen claim and stays readable either way. Config prose shown
 *  verbatim; the frontend never resolves or derives a sector. */
function SectorBasisCard({ sectorBasis }: { sectorBasis: string }) {
  return (
    <Card className="space-y-1.5 p-4" data-testid="universe-sector-basis">
      <div className="flex flex-wrap items-center gap-2">
        <Filter className="h-4 w-4 text-accent" aria-hidden />
        <h2 className="text-base font-semibold text-text">Stock sector labels</h2>
        <Badge variant="default">Data basis</Badge>
      </div>
      <p className="text-sm text-text-muted">{sectorBasis}</p>
    </Card>
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
