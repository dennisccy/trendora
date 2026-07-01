/**
 * Read-side evidence types + the inline-badge status resolver (goal-mcp-loop iter-1).
 *
 * This module is the SINGLE place the UI decides whether a signal reads "Proven" or "Not yet proven".
 * It is PURE and dependency-free (no React, no fetch) so it is unit-testable under the repo's
 * `node lib/*.test.ts` pattern — the React `EvidenceStatusBadge` and the `/evidence` page consume it.
 *
 * The evidence ledger is the ONLY source of proven-ness (goal.md Constraints + anti-goal): the UI NEVER
 * computes proven-ness itself. A signal is "Proven" ONLY when the served `proven_signals` map (built by the
 * backend from a `verdict.status == "PASS"` ledger entry) names it; any signal ABSENT from that map — or a
 * null/failed/empty map — is "Not yet proven" (the fail-safe default). Against today's empty ledger every
 * signal therefore reads "Not yet proven".
 */

/** The referee's verdict for one claim, re-displayed VERBATIM (never recomputed). Only the fields the
 *  Evidence page reads are typed explicitly; the additive audit fields ride along via the index signature. */
export interface Verdict {
  status: string; // "PASS" | "FAIL" | "INSUFFICIENT"
  reason: string;
  in_sample_edge?: number | null;
  holdout_edge?: number | null; // the out-of-sample edge
  control_excess?: number | null; // the control comparison (cohort − benchmark/SPY)
  p_value?: number | null;
  [key: string]: unknown;
}

/** One certified-claims ledger row, read VERBATIM from `GET /api/evidence`. `claim` is the hypothesis
 *  (the cohort selectors); `proven` is true ONLY for a PASS verdict; `signal` is the UI signal key the
 *  PASS backs (null for a real signal-less writer entry — fail-safe). `forward_walk` is the forward-walk
 *  score-to-date (null until a certified claim is monitored). */
export interface CertifiedClaim {
  signal: string | null;
  claim: Record<string, unknown>;
  register_date: string | null;
  horizon: number | null;
  cohort_n: number | null;
  control_n: number | null;
  verdict: Verdict;
  proven: boolean;
  forward_walk: unknown | null;
}

/** A proven claim row, as stored in the served `proven_signals` map (keyed by signal). Same shape as a
 *  `CertifiedClaim`; the alias documents intent at the badge call sites. */
export type ProvenSignal = CertifiedClaim;

/** The `GET /api/evidence` payload: the full claim list the ledger page renders + the proven-signal map
 *  the inline badge reads. */
export interface EvidenceLedgerResponse {
  claims: CertifiedClaim[];
  proven_signals: Record<string, ProvenSignal>;
}

/** The two honest, calm status labels — never hype (goal.md Design Direction). */
export const PROVEN_LABEL = "Proven";
export const NOT_PROVEN_LABEL = "Not yet proven";

/** The Evidence-page anchor a "Proven" badge links to (claim → surface linkback target). The claim rows
 *  on `/evidence` carry the matching `id`, so the badge jumps straight to the backing entry. */
export function evidenceAnchor(signal: string): string {
  return `/evidence#signal-${signal}`;
}

/** The resolved status for one signal's inline badge. */
export interface EvidenceStatus {
  proven: boolean;
  /** "Proven" | "Not yet proven" — the exact text the badge renders. */
  label: string;
  /** The ledger anchor to link to when proven; null when not yet proven (no link). */
  href: string | null;
  /** The backing claim row when proven; null otherwise. */
  claim: ProvenSignal | null;
}

/**
 * Resolve a signal's evidence status from the served `proven_signals` map. FAIL-SAFE: any signal absent
 * from the map (or a null/undefined map, or a row that is not `proven`) resolves to "Not yet proven" with
 * no link — the UI never fabricates proven-ness. A present, proven row resolves to "Proven" linking to its
 * backing ledger entry.
 */
export function resolveEvidenceStatus(
  signal: string,
  provenSignals: Record<string, ProvenSignal> | null | undefined,
): EvidenceStatus {
  const claim = provenSignals?.[signal] ?? null;
  if (claim && claim.proven) {
    return { proven: true, label: PROVEN_LABEL, href: evidenceAnchor(signal), claim };
  }
  return { proven: false, label: NOT_PROVEN_LABEL, href: null, claim: null };
}

/**
 * The signal key each per-stock score maps to on the evidence ledger — the canonical factor-catalog keys,
 * byte-identical to the UI signal key (e.g. the Leadership score IS `leadership_score`). The SINGLE
 * definition shared by the Stocks leaderboard and the Stock-detail score cards (de-duped in iter-2 — there
 * was one identical copy in each page). A score reads "Proven" ONLY when a PASS-backed ledger entry names
 * its key; everything absent from `proven_signals` is "Not yet proven".
 */
export const SCORE_SIGNALS = {
  leadership: "leadership_score",
  entry_quality: "entry_quality_score",
  risk: "risk_score",
} as const;

// --- proof drill-down (J-02) field extraction + display formatters ------------------------------------
// These are PURE and read-only: they re-display what the referee already certified (read VERBATIM from the
// served `proven_signals` map) and FABRICATE nothing. The Stock-detail "Why proven?" panel renders them;
// the unit tests pin them. Proven-ness still flows 100% from `resolveEvidenceStatus` (a PASS-backed entry).

/** Coerce a served numeric field to a finite number, else null (NA-honest — never a fabricated 0). */
function finiteOrNull(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

/**
 * The proof fields a "Proven" score drills into — read VERBATIM from the backing ledger entry (the
 * out-of-sample test, the SPY control comparison, and the certified-claim id/date). Every numeric field is
 * the referee's value exactly as written; the panel only re-formats it. `null` numerics render "—"
 * (never a fabricated figure).
 */
export interface ProofFields {
  /** The certified-claim's signal key (the stable id component, e.g. "leadership_score"). */
  signal: string;
  /** The out-of-sample verdict status, verbatim (e.g. "PASS"). */
  status: string;
  /** The out-of-sample holdout edge (a fraction), verbatim — null when the entry omits it. */
  holdoutEdge: number | null;
  /** The out-of-sample significance (p-value), verbatim — null when the entry omits it. */
  pValue: number | null;
  /** The control comparison vs SPY (the cohort's excess over the benchmark, a fraction), verbatim. */
  controlExcess: number | null;
  /** The sealed-holdout cohort size, verbatim — null when the entry omits it. */
  cohortN: number | null;
  /** The registration date (ISO), verbatim — null when the entry omits it. */
  registerDate: string | null;
  /** The stable certified-claim id label: `${signal} · registered ${registerDate}`. */
  claimId: string;
  /** The `/evidence` backing-row anchor this proof links to (claim → surface linkback). */
  href: string;
}

/**
 * Build the read-only proof fields for one signal from the served `proven_signals` map, or `null` when the
 * signal is NOT proven (absent / null map / non-`proven` row). FAIL-SAFE: an unproven signal yields `null`
 * so the "Why proven?" disclosure is absent entirely (no empty panel, no fabricated confidence). Reads
 * every field VERBATIM from the backing claim — recomputes nothing.
 */
export function proofFieldsFor(
  signal: string,
  provenSignals: Record<string, ProvenSignal> | null | undefined,
): ProofFields | null {
  const status = resolveEvidenceStatus(signal, provenSignals);
  if (!status.proven || !status.claim || !status.href) {
    return null;
  }
  const claim = status.claim;
  const verdict = claim.verdict ?? { status: "", reason: "" };
  const registerDate = claim.register_date ?? null;
  return {
    signal,
    status: verdict.status ?? "",
    holdoutEdge: finiteOrNull(verdict.holdout_edge),
    pValue: finiteOrNull(verdict.p_value),
    controlExcess: finiteOrNull(verdict.control_excess),
    cohortN: finiteOrNull(claim.cohort_n),
    registerDate,
    claimId: registerDate ? `${signal} · registered ${registerDate}` : signal,
    href: status.href,
  };
}

/**
 * Format a signed fraction as a percent with an explicit sign (e.g. +6.36% / -0.40%). Display-only; the
 * SAME representation the `/evidence` claim row uses for the holdout edge and the SPY control comparison.
 * A null/undefined/non-finite value renders an em dash (never a fabricated 0%).
 */
export function formatEvidencePct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) {
    return "—";
  }
  const pct = value * 100;
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
}

/**
 * Format an out-of-sample p-value for display — 4 significant figures (matching the referee's own
 * `verdict.reason` formatting, e.g. 0.0004998), `< 0.0001` for vanishingly small values, an em dash for a
 * missing value. Display-only; never recomputed.
 */
export function formatPValue(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) {
    return "—";
  }
  if (value <= 0) {
    return "0";
  }
  if (value < 0.0001) {
    return "< 0.0001";
  }
  return Number(value.toPrecision(4)).toString();
}

// --- claim-row presentation (goal-mcp-loop iter-4) — regime label + honest title/linkback --------------
// PURE, read-only helpers the `/evidence` ClaimRow consumes to deliver J-04 (regime-conditioned evidence,
// "clearly labeled with the regime it holds in") WITHOUT regressing J-05 (the leadership score row's title
// + linkback stay byte-identical). They re-display what the served claim already carries — they FABRICATE
// nothing and they NEVER decide proven-ness (that still flows solely from `resolveEvidenceStatus`).

/**
 * The market-regime label a regime-conditioned claim holds in — read VERBATIM from the claim's own cohort
 * selector (`claim.claim.regime`, e.g. "Risk-on"). Returns `null` when the cohort carries no regime (a
 * score claim like the leadership row has none — its label MUST stay hidden so that row looks unchanged),
 * and treats a blank / whitespace-only value as absent (no empty "Regime:" chip).
 */
export function regimeLabel(claim: CertifiedClaim): string | null {
  const regime = claim.claim?.["regime"];
  if (typeof regime === "string" && regime.trim() !== "") {
    return regime;
  }
  return null;
}

/** The Stocks-leaderboard linkback every per-stock score signal backs (the pre-iter-4 surface — unchanged). */
const STOCKS_LEADERBOARD_SURFACE = { href: "/stocks", label: "Stocks leaderboard" } as const;

/** The forward-return horizon whose signal-less factor-cohort subtitle stays BARE ("Out-of-sample edge —
 *  factor top decile") — the iter-8-established default-horizon (20-day) vcp_contraction row whose exact
 *  wording J-06 pins byte-identical. Every OTHER horizon (iter-11's h60) appends a "· N-day hold"
 *  disambiguator so the two vcp_contraction rows on `/evidence` are self-distinguishing. Display-only — the
 *  load-bearing horizon signal is still the served `horizon` selector shown on the row's hypothesis chip. */
const DEFAULT_FACTOR_COHORT_HORIZON = 20;

/** The honest title + linkback for ONE certified-claims row (the read-only `surfaceForSignal` successor). */
export interface ClaimSurface {
  /** The row headline. For a score-column claim this is the signal key VERBATIM (rendered in the mono
   *  `num` style — byte-identical to the pre-iter-4 row); for a signal-less cohort it is a meaningful
   *  subject-framed title (never the misleading "Unmapped signal"). */
  title: string;
  /** True iff `title` is a raw signal key (so the row renders it in the mono `num` style — the unchanged
   *  score-row look). False for a prose title. */
  titleIsSignalKey: boolean;
  /** An honest one-line framing for a signal-less cohort (e.g. "Out-of-sample edge in the Risk-on regime"),
   *  or `null` for a score row (which shows only its signal key, unchanged). Always *historical evidence*
   *  framing — never a buy/sell or return promise (anti-goal #2). */
  subtitle: string | null;
  /** The "Backs: <label> →" linkback target. A score claim backs the Stocks leaderboard (unchanged); a
   *  signal-less event-study cohort backs its Research lab, NOT the leaderboard (honest linkback). */
  href: string;
  /** The linkback label rendered inside "Backs: <label> →". */
  label: string;
}

/**
 * Resolve a claim row's title + linkback honestly (PURE, read-only):
 *   - a MAPPED score signal (`claim.signal` present) → its signal key as the title (mono `num` style) +
 *     the "Stocks leaderboard" linkback — BYTE-IDENTICAL to the pre-iter-4 score row (J-05 must not regress);
 *   - a signal-less EVENT-STUDY cohort with a subject → a meaningful "<subject> setup" title + an honest
 *     "Out-of-sample edge[ in the <regime> regime]" framing + a Research event-study-lab linkback (NOT the
 *     leaderboard — this claim backs no per-stock score);
 *   - any OTHER signal-less cohort → the prior generic "Unmapped signal" + leaderboard fallback (defensive —
 *     no such claim exists today, but never a crash and never a fabricated mapping).
 * Fabricates nothing — every value is read from the served claim.
 */
export function claimSurface(claim: CertifiedClaim): ClaimSurface {
  if (claim.signal) {
    return {
      title: claim.signal,
      titleIsSignalKey: true,
      subtitle: null,
      href: STOCKS_LEADERBOARD_SURFACE.href,
      label: STOCKS_LEADERBOARD_SURFACE.label,
    };
  }
  const cohort = claim.claim ?? {};
  const kind = typeof cohort["kind"] === "string" ? (cohort["kind"] as string) : null;
  const subjectRaw = cohort["subject"];
  const subject =
    typeof subjectRaw === "string" && subjectRaw.trim() !== "" ? subjectRaw : null;
  if (kind === "event-study" && subject) {
    const regime = regimeLabel(claim);
    return {
      title: `${subject} setup`,
      titleIsSignalKey: false,
      subtitle: regime ? `Out-of-sample edge in the ${regime} regime` : "Out-of-sample edge",
      href: "/research/event-study",
      label: "Research event-study lab",
    };
  }
  // A signal-less PLAIN-FACTOR decile cohort (iter-8 — the vcp_contraction top-decile edge). It backs the
  // Research factor lab + this Evidence ledger ONLY (NOT a per-stock score badge — it carries no `signal`),
  // so its title is the factor + top decile read from the selectors (never the misleading "Unmapped
  // signal"), its subtitle is honest *historical evidence* framing (never a buy/return promise — anti-goal
  // #2), and its linkback points at the Research factor lab (NOT the Stocks leaderboard).
  const factorCohort = kind === "factor" ? factorCohortFromClaim(claim) : null;
  if (factorCohort) {
    // iter-11 (J-07): disambiguate the horizon so the h20 and h60 vcp_contraction rows on `/evidence` are
    // self-distinguishing. The default (20-day) row keeps iter-8's EXACT wording (J-06 non-regression); any
    // other horizon appends a "· N-day hold" suffix. This is clarity polish only — proven-ness + the
    // load-bearing horizon selector are unchanged.
    const factorSubtitleBase = "Out-of-sample edge — factor top decile";
    const subtitle =
      factorCohort.horizon === DEFAULT_FACTOR_COHORT_HORIZON
        ? factorSubtitleBase
        : `${factorSubtitleBase} · ${factorCohort.horizon}-day hold`;
    return {
      title: `${factorCohort.factor} — top decile (D${factorCohort.decile})`,
      titleIsSignalKey: false,
      subtitle,
      href: "/research/factor-lab",
      label: "Research factor lab",
    };
  }
  return {
    title: "Unmapped signal",
    titleIsSignalKey: false,
    subtitle: null,
    href: STOCKS_LEADERBOARD_SURFACE.href,
    label: STOCKS_LEADERBOARD_SURFACE.label,
  };
}

// --- read-side cohort-selector matcher (goal-mcp-loop iter-8) — the signal-less successor to
// `resolveEvidenceStatus`. PURE + read-only: it scans the served `claims[]` for a PASS entry whose cohort
// selectors MATCH a queried factor decile cohort, and re-displays the served status VERBATIM. It NEVER
// recomputes proven-ness (a matched-but-non-PASS entry stays "Not yet proven"), reads from the SAME
// `GET /api/evidence` payload (no new fetch path), and fabricates nothing. This is how the Research
// factor lab marks the one certified top-decile cohort "Proven" while every unbacked cohort reads
// "Not yet proven" (anti-goal #1).

/** A factor top-decile cohort's selectors — the SAME slice vocabulary the Research labs + the certified
 *  claim use (`/api/research/samples` / the Evidence-Claim JSON): factor + `slice_kind` ("decile") + the
 *  decile bucket + the forward `horizon` + the `direction`. A signal-less cohort (it backs no per-stock
 *  score). */
export interface FactorCohort {
  factor: string;
  slice_kind: string; // "decile"
  decile: number;
  horizon: number;
  direction: string; // "positive" | "negative"
}

/** Extract a `FactorCohort` from a served claim's selectors, or `null` when the claim is not a factor
 *  decile cohort (e.g. the event-study row) or is missing a required selector. Reads VERBATIM — fabricates
 *  nothing. The score-column factor cohorts (leadership/entry-quality/risk) ARE factor cohorts too, so the
 *  CALLER decides routing (the `/evidence` ClaimRow checks `claim.signal` first — a score row keeps its
 *  `signal-${signal}` anchor; only a signal-less factor cohort uses this cohort anchor). */
export function factorCohortFromClaim(claim: CertifiedClaim): FactorCohort | null {
  const cohort = claim.claim ?? {};
  if (cohort["kind"] !== "factor") {
    return null;
  }
  const factor = cohort["factor"];
  const sliceKind = cohort["slice_kind"];
  const decile = cohort["decile"];
  const horizon = cohort["horizon"];
  const direction = cohort["direction"];
  if (
    typeof factor !== "string" ||
    factor === "" ||
    sliceKind !== "decile" ||
    typeof decile !== "number" ||
    typeof horizon !== "number" ||
    typeof direction !== "string" ||
    direction === ""
  ) {
    return null;
  }
  return { factor, slice_kind: sliceKind, decile, horizon, direction };
}

/** The stable, collision-free anchor id for a factor cohort, derived from its selectors
 *  (e.g. `factor-vcp_contraction-d10-h20`). The `/evidence` factor `ClaimRow` carries this as its row `id`
 *  and the factor-lab "Proven" badge links to the matching `/evidence#…` anchor, so the deep-link lands.
 *  Distinct (factor, decile, horizon) tuples produce distinct ids. */
export function cohortClaimId(cohort: FactorCohort): string {
  return `factor-${cohort.factor}-d${cohort.decile}-h${cohort.horizon}`;
}

/** The `/evidence#…` deep-link a "Proven" factor-cohort badge points at — the `cohortClaimId` under the
 *  Evidence-page hash (the row carrying the matching `id`). */
export function cohortEvidenceAnchor(cohort: FactorCohort): string {
  return `/evidence#${cohortClaimId(cohort)}`;
}

/**
 * The stable `/evidence` row `id` for ONE certified claim — the SINGLE source the `/evidence` ClaimRow and
 * every "Proven" badge agree on, so a deep-link always lands on the backing row:
 *   - a score-column claim (carries a `signal`) keeps its `signal-${signal}` id (J-02/J-05 unchanged);
 *   - a signal-less plain-factor decile cohort (iter-8 — vcp_contraction) derives its `cohortClaimId`;
 *   - any other claim (e.g. the event-study row) has no stable cohort id → `null` (no anchor).
 * Reading the SAME id at the badge and at the row is what guarantees the factor-lab "Proven" badge scrolls
 * to its real ledger entry (a score-column factor like leadership_score links to `signal-…`, NOT a cohort
 * anchor its row never carries).
 */
export function claimAnchorId(claim: CertifiedClaim): string | null {
  if (claim.signal) {
    return `signal-${claim.signal}`;
  }
  const cohort = factorCohortFromClaim(claim);
  return cohort ? cohortClaimId(cohort) : null;
}

/** The resolved status for one factor cohort's evidence badge (mirrors `EvidenceStatus`). */
export interface CohortEvidenceStatus {
  proven: boolean;
  /** "Proven" | "Not yet proven" — the exact text the badge renders. */
  label: string;
  /** The `/evidence#…` cohort anchor when proven; null when not yet proven (no link). */
  href: string | null;
  /** The backing claim row when proven; null otherwise. */
  claim: CertifiedClaim | null;
}

/**
 * Resolve a factor cohort's evidence status from the served `claims[]` (PURE, read-only). It scans for a
 * `proven` (PASS) entry whose cohort selectors MATCH the queried cohort on `factor` + `slice_kind` +
 * `decile` + `horizon` + `direction`, and returns "Proven" linking to its `/evidence` cohort anchor.
 * FAIL-SAFE: no match, a matched-but-NON-PASS entry (e.g. the ma_stack FAIL row), or an empty/null/undefined
 * list → "Not yet proven" with no link. It re-displays `entry.proven` VERBATIM and recomputes nothing —
 * the UI never fabricates proven-ness (goal.md Constraints + anti-goal #1).
 */
export function resolveCohortEvidence(
  cohort: FactorCohort,
  claims: CertifiedClaim[] | null | undefined,
): CohortEvidenceStatus {
  if (Array.isArray(claims)) {
    for (const entry of claims) {
      if (!entry || entry.proven !== true) {
        continue; // only a PASS-backed entry can prove a cohort (matched-but-non-PASS stays unproven)
      }
      const entryCohort = factorCohortFromClaim(entry);
      if (
        entryCohort &&
        entryCohort.factor === cohort.factor &&
        entryCohort.slice_kind === cohort.slice_kind &&
        entryCohort.decile === cohort.decile &&
        entryCohort.horizon === cohort.horizon &&
        entryCohort.direction === cohort.direction
      ) {
        // Link to the matched claim's ACTUAL `/evidence` row id (`claimAnchorId`) so the deep-link lands:
        // a signal-less plain factor (vcp_contraction) → its cohort anchor; a score-column factor whose
        // certified row carries a `signal` (e.g. leadership_score) → that row's `signal-…` anchor (never a
        // cohort anchor its `/evidence` row never has). Falls back to the queried cohort anchor defensively.
        const anchor = claimAnchorId(entry);
        const href = anchor ? `/evidence#${anchor}` : cohortEvidenceAnchor(cohort);
        return { proven: true, label: PROVEN_LABEL, href, claim: entry };
      }
    }
  }
  return { proven: false, label: NOT_PROVEN_LABEL, href: null, claim: null };
}
