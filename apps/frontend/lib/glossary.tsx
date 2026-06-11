"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  fetchMethodology,
  type GlossaryTerm,
  type MethodologyCatalog,
} from "@/lib/api";

/**
 * Shared glossary state (iter-4 goal-mode, J-47). ONE fetch of the config-backed catalog
 * (`GET /api/methodology`), mounted in the app shell so every page's inline term tooltips AND the
 * /methodology Glossary page read the SAME served entries (single source of truth — no component
 * hardcodes a definition or term list).
 *
 * It holds the full `MethodologyCatalog` plus a `term -> GlossaryTerm` lookup keyed by the LITERAL UI
 * string. A term key missing from the catalog (or a failed fetch) degrades gracefully: `lookup()`
 * returns `undefined` and the inline `<TermInfo>` renders no marker — never a crash, never a
 * hardcoded fallback definition (anti-goal: Glossary copy lives in one catalog).
 */
export interface GlossaryContextValue {
  /** The full served catalog, or null before load / on failure. */
  catalog: MethodologyCatalog | null;
  /** Look up a term by its literal UI string; undefined if absent (degrade gracefully). */
  lookup: (term: string) => GlossaryTerm | undefined;
  /** True once the catalog fetch resolved or failed (callers may show a marker only when ready). */
  ready: boolean;
}

const GlossaryContext = createContext<GlossaryContextValue | null>(null);

export function GlossaryProvider({ children }: { children: React.ReactNode }) {
  const [catalog, setCatalog] = useState<MethodologyCatalog | null>(null);
  const [ready, setReady] = useState(false);

  // Fetch once (config is global, independent of the as-of date). A failure must NOT break any page —
  // the lookup just returns undefined and inline markers disappear (graceful degradation).
  useEffect(() => {
    const controller = new AbortController();
    fetchMethodology(controller.signal)
      .then((data) => {
        setCatalog(data);
        setReady(true);
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setCatalog(null);
          setReady(true);
        }
      });
    return () => controller.abort();
  }, []);

  // term (literal UI string) -> GlossaryTerm, across every category. Built once per catalog.
  const byTerm = useMemo(() => {
    const map = new Map<string, GlossaryTerm>();
    catalog?.glossary?.categories.forEach((category) => {
      category.terms.forEach((term) => {
        if (!map.has(term.term)) map.set(term.term, term);
      });
    });
    return map;
  }, [catalog]);

  const value = useMemo<GlossaryContextValue>(
    () => ({ catalog, lookup: (term: string) => byTerm.get(term), ready }),
    [catalog, byTerm, ready],
  );

  return <GlossaryContext.Provider value={value}>{children}</GlossaryContext.Provider>;
}

/** Read the shared glossary state. Must be used within `<GlossaryProvider>` (mounted in the app shell). */
export function useGlossary(): GlossaryContextValue {
  const ctx = useContext(GlossaryContext);
  if (!ctx) throw new Error("useGlossary must be used within <GlossaryProvider>");
  return ctx;
}

/** Convenience hook: the GlossaryTerm for a literal UI string, or undefined if absent / not yet loaded. */
export function useGlossaryTerm(term: string): GlossaryTerm | undefined {
  return useGlossary().lookup(term);
}
