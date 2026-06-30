/**
 * Unit tests for the inline evidence-badge status resolver (lib/evidence.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/evidence.test.ts
 *
 * The crux (goal.md anti-goal — nothing "Proven" without a PASS-backed ledger entry; fail-safe default):
 *   (a) a signal ABSENT from the served proven map reads "Not yet proven" with NO link;
 *   (b) a null/undefined map (the fetch failed, or the ledger is empty) reads "Not yet proven";
 *   (c) a PRESENT, proven signal reads "Proven" and links to its `/evidence` backing entry;
 *   (d) a present-but-not-`proven` row is still treated as "Not yet proven" (defensive).
 */
import assert from "node:assert";

import {
  NOT_PROVEN_LABEL,
  PROVEN_LABEL,
  SCORE_SIGNALS,
  claimAnchorId,
  claimSurface,
  cohortClaimId,
  cohortEvidenceAnchor,
  evidenceAnchor,
  factorCohortFromClaim,
  formatEvidencePct,
  formatPValue,
  proofFieldsFor,
  regimeLabel,
  resolveCohortEvidence,
  resolveEvidenceStatus,
  type CertifiedClaim,
  type FactorCohort,
  type ProvenSignal,
} from "./evidence.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

function provenRow(signal: string): ProvenSignal {
  return {
    signal,
    claim: { kind: "factor", factor: signal, decile: 10, horizon: 20 },
    register_date: "2024-06-01",
    horizon: 20,
    cohort_n: 42,
    control_n: 40,
    verdict: { status: "PASS", reason: "certified", control_excess: 0.018, holdout_edge: 0.031 },
    proven: true,
    forward_walk: null,
  };
}

// --- (a) absent signal => "Not yet proven", no link (the empty-ledger reality this iteration) ----------
check("a signal absent from the proven map reads 'Not yet proven' with no link", () => {
  const status = resolveEvidenceStatus("leadership_score", {});
  assert.strictEqual(status.proven, false);
  assert.strictEqual(status.label, NOT_PROVEN_LABEL);
  assert.strictEqual(status.label, "Not yet proven");
  assert.strictEqual(status.href, null);
  assert.strictEqual(status.claim, null);
});

// --- (b) null/undefined map (fetch failed / empty ledger) => fail-safe "Not yet proven" ----------------
check("a null or undefined proven map falls back to 'Not yet proven' (fail-safe)", () => {
  for (const map of [null, undefined]) {
    const status = resolveEvidenceStatus("risk_score", map);
    assert.strictEqual(status.proven, false);
    assert.strictEqual(status.label, "Not yet proven");
    assert.strictEqual(status.href, null);
  }
});

// --- (c) present & proven => "Proven" linking to the /evidence backing entry --------------------------
check("a present, proven signal reads 'Proven' and links to its /evidence backing entry", () => {
  const map = { leadership_score: provenRow("leadership_score") };
  const status = resolveEvidenceStatus("leadership_score", map);
  assert.strictEqual(status.proven, true);
  assert.strictEqual(status.label, PROVEN_LABEL);
  assert.strictEqual(status.label, "Proven");
  assert.strictEqual(status.href, "/evidence#signal-leadership_score");
  assert.ok(status.href!.startsWith("/evidence"), "the proven badge must link into /evidence");
  assert.strictEqual(status.claim?.register_date, "2024-06-01");
  assert.strictEqual(status.claim?.verdict.control_excess, 0.018);
});

// --- (d) present but NOT proven => defensively "Not yet proven" ----------------------------------------
check("a present row that is not `proven` is still treated as 'Not yet proven'", () => {
  const row = { ...provenRow("entry_quality_score"), proven: false };
  const status = resolveEvidenceStatus("entry_quality_score", { entry_quality_score: row });
  assert.strictEqual(status.proven, false);
  assert.strictEqual(status.label, "Not yet proven");
  assert.strictEqual(status.href, null);
});

// --- evidenceAnchor is the stable claim→surface linkback target ---------------------------------------
check("evidenceAnchor builds the stable per-signal ledger anchor", () => {
  assert.strictEqual(evidenceAnchor("risk_score"), "/evidence#signal-risk_score");
});

// --- SCORE_SIGNALS — the single shared score→signal map (de-duped in iter-2) ---------------------------
check("SCORE_SIGNALS maps each score to its canonical factor-catalog signal key", () => {
  assert.strictEqual(SCORE_SIGNALS.leadership, "leadership_score");
  assert.strictEqual(SCORE_SIGNALS.entry_quality, "entry_quality_score");
  assert.strictEqual(SCORE_SIGNALS.risk, "risk_score");
});

// ======================================================================================================
// J-02 proof drill-down — `proofFieldsFor` reads the backing claim VERBATIM (the iter-2 PRIMARY contract).
// The values below MIRROR the real certified leadership_score entry the post-decompose gate wrote, so the
// test pins the displayed-numbers-are-correct anti-goal: what the panel shows must equal the served entry.
// ======================================================================================================

/** A proven row mirroring the REAL ledger entry (holdout edge / p-value / control excess / register date /
 *  cohort_n the gate certified for leadership_score), so the proof-field extraction is pinned to reality. */
function provenLeadershipRow(): ProvenSignal {
  return {
    signal: "leadership_score",
    claim: {
      kind: "factor",
      factor: "leadership_score",
      slice_kind: "decile",
      decile: 10,
      horizon: 20,
      direction: "positive",
      signal: "leadership_score",
    },
    register_date: "2026-06-30",
    horizon: 20,
    cohort_n: 12297,
    control_n: 1137,
    verdict: {
      status: "PASS",
      reason: "certified out-of-sample",
      holdout_edge: 0.06359100763913017,
      control_excess: 0.06359100763913017,
      p_value: 0.0004997501249375312,
    },
    proven: true,
    forward_walk: null,
  };
}

// --- (e) proven => the proof fields are read VERBATIM, with the stable claim id + /evidence anchor -------
check("proofFieldsFor reads the backing claim verbatim for a proven signal", () => {
  const fields = proofFieldsFor("leadership_score", { leadership_score: provenLeadershipRow() });
  assert.ok(fields, "a proven signal must yield proof fields");
  assert.strictEqual(fields!.signal, "leadership_score");
  assert.strictEqual(fields!.status, "PASS");
  // every numeric is the referee's value EXACTLY (no recompute, no rounding in the data layer)
  assert.strictEqual(fields!.holdoutEdge, 0.06359100763913017);
  assert.strictEqual(fields!.pValue, 0.0004997501249375312);
  assert.strictEqual(fields!.controlExcess, 0.06359100763913017);
  assert.strictEqual(fields!.cohortN, 12297);
  assert.strictEqual(fields!.registerDate, "2026-06-30");
  // the stable certified-claim id + the backing /evidence anchor a "Proven" badge round-trips to
  assert.strictEqual(fields!.claimId, "leadership_score · registered 2026-06-30");
  assert.strictEqual(fields!.href, "/evidence#signal-leadership_score");
});

// --- (f) FAIL-SAFE: an unproven / absent / null-map signal yields NO proof fields (no empty panel) ------
check("proofFieldsFor returns null for an absent, null-map, or not-`proven` signal (fail-safe)", () => {
  // absent from the map (the Entry Quality / Risk reality this iteration)
  assert.strictEqual(proofFieldsFor("entry_quality_score", { leadership_score: provenLeadershipRow() }), null);
  // null / undefined map (fetch failed / empty ledger)
  assert.strictEqual(proofFieldsFor("leadership_score", null), null);
  assert.strictEqual(proofFieldsFor("leadership_score", undefined), null);
  // present but explicitly not `proven` (defensive — never trust a non-proven row)
  const notProven = { ...provenLeadershipRow(), proven: false };
  assert.strictEqual(proofFieldsFor("leadership_score", { leadership_score: notProven }), null);
});

// --- (g) the display formatters — exact strings (the panel re-formats; it fabricates nothing) -----------
check("formatEvidencePct renders a signed percent (and an em dash for a missing value)", () => {
  assert.strictEqual(formatEvidencePct(0.06359100763913017), "+6.36%"); // the real holdout edge / control excess
  assert.strictEqual(formatEvidencePct(-0.004), "-0.40%");
  assert.strictEqual(formatEvidencePct(0), "+0.00%");
  assert.strictEqual(formatEvidencePct(null), "—");
  assert.strictEqual(formatEvidencePct(undefined), "—");
  assert.strictEqual(formatEvidencePct(Number.NaN), "—");
});

check("formatPValue renders the p-value to 4 significant figures (with a small/missing fallback)", () => {
  assert.strictEqual(formatPValue(0.0004997501249375312), "0.0004998"); // the real certified p-value
  assert.strictEqual(formatPValue(0.05), "0.05");
  assert.strictEqual(formatPValue(0.0000000001), "< 0.0001");
  assert.strictEqual(formatPValue(null), "—");
  assert.strictEqual(formatPValue(undefined), "—");
});

// ======================================================================================================
// J-04 regime-conditioned evidence — the ClaimRow regime label + the honest non-score title/linkback.
// The row below MIRRORS the real 2nd ledger entry the post-decompose gate certified (Breakout-watch ×
// Risk-on event-study, signal: null), so these pin the J-04 display contract AND the J-05 no-regression
// invariant (the leadership score row's title + linkback stay byte-identical).
// ======================================================================================================

/** A certified (PASS) row mirroring the REAL iter-4 2nd ledger entry: the Breakout-watch setup's
 *  event-study cohort sliced to the named `Risk-on` regime. It deliberately carries NO `signal` (it backs
 *  no per-stock score badge — it is regime-conditioned evidence in its own right). */
function eventStudyRegimeRow(): CertifiedClaim {
  return {
    signal: null,
    claim: {
      kind: "event-study",
      subject: "Breakout-watch",
      slice_kind: "regime",
      regime: "Risk-on",
      view: "pooled",
      horizon: 20,
      direction: "positive",
    },
    register_date: "2026-06-30",
    horizon: 20,
    cohort_n: 4720,
    control_n: 414,
    verdict: {
      status: "PASS",
      reason: "certified out-of-sample (Risk-on)",
      holdout_edge: 0.06124590639955655,
      control_excess: 0.06124590639955655,
      p_value: 0.0004997501249375312,
    },
    proven: true,
    forward_walk: null,
  };
}

// --- (h) regime label — read VERBATIM from the cohort's own `regime` selector when present --------------
check("regimeLabel returns the cohort's regime verbatim for a regime-conditioned claim", () => {
  assert.strictEqual(regimeLabel(eventStudyRegimeRow()), "Risk-on");
});

// --- (i) regime label is HIDDEN (null) for a score claim with no regime (leadership must look unchanged) -
check("regimeLabel returns null for a score claim that carries no regime (label hidden)", () => {
  assert.strictEqual(regimeLabel(provenLeadershipRow()), null);
});

// --- (j) a blank / whitespace / absent regime is treated as absent (no empty 'Regime:' chip) -----------
check("regimeLabel treats a blank, whitespace, or absent regime as hidden", () => {
  const blank = eventStudyRegimeRow();
  blank.claim = { ...blank.claim, regime: "   " };
  assert.strictEqual(regimeLabel(blank), null);
  const absent = eventStudyRegimeRow();
  delete (absent.claim as Record<string, unknown>).regime;
  assert.strictEqual(regimeLabel(absent), null);
});

// --- (k) score row title + linkback stay BYTE-IDENTICAL (J-05 must not regress) ------------------------
check("claimSurface keeps the score row's signal-key title + 'Stocks leaderboard' linkback byte-identical", () => {
  const surface = claimSurface(provenLeadershipRow());
  assert.strictEqual(surface.title, "leadership_score"); // the signal key, rendered in the mono `num` style
  assert.strictEqual(surface.titleIsSignalKey, true);
  assert.strictEqual(surface.subtitle, null);
  assert.strictEqual(surface.href, "/stocks");
  assert.strictEqual(surface.label, "Stocks leaderboard"); // "Backs: Stocks leaderboard →" — unchanged
});

// --- (l) signal-less event-study claim → HONEST title + a NON-leaderboard linkback ----------------------
check("claimSurface gives a signal-less event-study claim an honest title + a non-leaderboard linkback", () => {
  const surface = claimSurface(eventStudyRegimeRow());
  // an honest, meaningful title — NEVER the misleading "Unmapped signal"
  assert.strictEqual(surface.title, "Breakout-watch setup");
  assert.notStrictEqual(surface.title, "Unmapped signal");
  assert.strictEqual(surface.titleIsSignalKey, false);
  // framed as historical out-of-sample evidence in the regime (never a buy/return promise)
  assert.strictEqual(surface.subtitle, "Out-of-sample edge in the Risk-on regime");
  // the linkback is honest — its Research event-study lab, NOT the Stocks leaderboard
  assert.strictEqual(surface.href, "/research/event-study");
  assert.strictEqual(surface.label, "Research event-study lab");
  assert.notStrictEqual(surface.label, "Stocks leaderboard");
});

// ======================================================================================================
// J-06 — the read-side COHORT-SELECTOR matcher for a signal-less plain-factor decile cohort (iter-8).
// The rows below MIRROR the real iter-8 ledger entries the post-decompose gate certified: the 4th entry
// (vcp_contraction D10 h20 PASS, holdout/control +0.0333, p 0.01149, signal-less) and the 3rd entry
// (ma_stack D10 h20 FAIL). These pin the J-06 display contract: vcp_contraction's top-decile cohort reads
// "Proven" (a PASS-backed match) and deep-links to its ledger row; every other factor top-decile cohort —
// INCLUDING ma_stack's FAIL row — reads "Not yet proven" with no link (anti-goal #1 upheld).
// ======================================================================================================

/** The queried top-decile cohort for the certified vcp_contraction factor (D10 @ the certified horizon 20). */
const VCP_COHORT: FactorCohort = {
  factor: "vcp_contraction",
  slice_kind: "decile",
  decile: 10,
  horizon: 20,
  direction: "positive",
};

/** A certified (PASS) row mirroring the REAL 4th ledger entry: the vcp_contraction top-decile cohort.
 *  It deliberately carries NO `signal` (a plain-factor cohort — it backs the factor lab + Evidence, never a
 *  per-stock score badge), so it MUST NOT enter the inline `proven_signals` map. */
function vcpContractionRow(): CertifiedClaim {
  return {
    signal: null,
    claim: {
      kind: "factor",
      factor: "vcp_contraction",
      slice_kind: "decile",
      decile: 10,
      horizon: 20,
      direction: "positive",
    },
    register_date: "2026-06-30",
    horizon: 20,
    cohort_n: 12297,
    control_n: 1075,
    verdict: {
      status: "PASS",
      reason: "certified: holdout edge +0.0333 beats the control out-of-sample (p=0.01149 < alpha/4=0.0125)",
      holdout_edge: 0.03330492745744988,
      control_excess: 0.03330492745744988,
      p_value: 0.011494252873563218,
    },
    proven: true,
    forward_walk: null,
  };
}

/** A FAIL row mirroring the REAL 3rd ledger entry: the ma_stack top-decile cohort that did NOT clear the
 *  tightened referee bar. It is audit-listed but `proven: false` — a matched-but-non-PASS cohort that MUST
 *  resolve to "Not yet proven". */
function maStackFailRow(): CertifiedClaim {
  return {
    signal: null,
    claim: {
      kind: "factor",
      factor: "ma_stack",
      slice_kind: "decile",
      decile: 10,
      horizon: 20,
      direction: "positive",
    },
    register_date: "2026-06-30",
    horizon: 20,
    cohort_n: 12297,
    control_n: 1106,
    verdict: {
      status: "FAIL",
      reason: "holdout edge +0.02619 is not significant after multiple-testing deflation (p=0.01949 >= alpha/3=0.01667)",
      holdout_edge: 0.026192275085938167,
      control_excess: 0.026192275085938167,
      p_value: 0.019490254872563718,
    },
    proven: false,
    forward_walk: null,
  };
}

/** The full 4-entry served claim list (leadership PASS, Breakout-watch Risk-on PASS, ma_stack FAIL,
 *  vcp_contraction PASS) — the post-iter-8 ledger the factor-lab badge resolves against. */
function ledgerClaims(): CertifiedClaim[] {
  return [provenLeadershipRow(), eventStudyRegimeRow(), maStackFailRow(), vcpContractionRow()];
}

// --- (m) full-selector match against a PASS entry => "Proven" + the cohort deep-link href ----------------
check("resolveCohortEvidence matches a PASS factor cohort on all selectors => 'Proven' + href", () => {
  const status = resolveCohortEvidence(VCP_COHORT, ledgerClaims());
  assert.strictEqual(status.proven, true);
  assert.strictEqual(status.label, PROVEN_LABEL);
  assert.strictEqual(status.label, "Proven");
  assert.strictEqual(status.href, "/evidence#factor-vcp_contraction-d10-h20");
  assert.ok(status.href!.startsWith("/evidence#"), "the proven cohort badge must deep-link into /evidence");
  // the backing claim row is returned VERBATIM (the displayed-numbers-are-correct contract)
  assert.strictEqual(status.claim?.verdict.holdout_edge, 0.03330492745744988);
  assert.strictEqual(status.claim?.verdict.control_excess, 0.03330492745744988);
  assert.strictEqual(status.claim?.verdict.p_value, 0.011494252873563218);
  assert.strictEqual(status.claim?.register_date, "2026-06-30");
  assert.strictEqual(status.claim?.signal, null); // signal-less — never lights a /stocks score badge
});

// --- (n) a matched-but-non-PASS cohort (the ma_stack FAIL row) => "Not yet proven", no href -------------
check("resolveCohortEvidence treats a matched-but-non-PASS cohort (ma_stack FAIL) as 'Not yet proven'", () => {
  const maCohort: FactorCohort = { ...VCP_COHORT, factor: "ma_stack" };
  const status = resolveCohortEvidence(maCohort, ledgerClaims());
  assert.strictEqual(status.proven, false);
  assert.strictEqual(status.label, NOT_PROVEN_LABEL);
  assert.strictEqual(status.label, "Not yet proven");
  assert.strictEqual(status.href, null);
  assert.strictEqual(status.claim, null);
});

// --- (o) ANY selector mismatch (factor / decile / horizon / direction) => "Not yet proven", no href -----
check("resolveCohortEvidence returns 'Not yet proven' on any selector mismatch", () => {
  for (const mismatch of [
    { ...VCP_COHORT, factor: "rs_spy_3m" }, // unbacked factor
    { ...VCP_COHORT, decile: 9 }, // wrong decile (not the top decile)
    { ...VCP_COHORT, horizon: 60 }, // wrong horizon
    { ...VCP_COHORT, direction: "negative" }, // wrong direction
    { ...VCP_COHORT, slice_kind: "sector" }, // wrong slice kind
  ] as FactorCohort[]) {
    const status = resolveCohortEvidence(mismatch, ledgerClaims());
    assert.strictEqual(status.proven, false, `cohort ${JSON.stringify(mismatch)} must not resolve proven`);
    assert.strictEqual(status.label, "Not yet proven");
    assert.strictEqual(status.href, null);
  }
});

// --- (p) FAIL-SAFE: an empty / null / undefined claim list => "Not yet proven", no href -----------------
check("resolveCohortEvidence falls back to 'Not yet proven' for an empty/null/undefined claim list", () => {
  for (const claims of [[], null, undefined] as (CertifiedClaim[] | null | undefined)[]) {
    const status = resolveCohortEvidence(VCP_COHORT, claims);
    assert.strictEqual(status.proven, false);
    assert.strictEqual(status.label, "Not yet proven");
    assert.strictEqual(status.href, null);
    assert.strictEqual(status.claim, null);
  }
});

// --- (q) the cohort anchor is stable + collision-free (the badge href == the /evidence row id) ----------
check("cohortClaimId / cohortEvidenceAnchor derive a stable, collision-free anchor from the cohort selectors", () => {
  // stable: the SAME cohort yields the SAME id every call
  assert.strictEqual(cohortClaimId(VCP_COHORT), "factor-vcp_contraction-d10-h20");
  assert.strictEqual(cohortClaimId(VCP_COHORT), cohortClaimId({ ...VCP_COHORT }));
  // the anchor is the id under the /evidence hash — so the factor-lab badge href lands on the ledger row id
  assert.strictEqual(cohortEvidenceAnchor(VCP_COHORT), "/evidence#factor-vcp_contraction-d10-h20");
  assert.strictEqual(
    cohortEvidenceAnchor(VCP_COHORT),
    `/evidence#${cohortClaimId(VCP_COHORT)}`,
    "the badge anchor must be the /evidence hash of the cohort id",
  );
  // collision-free: distinct (factor, decile, horizon) tuples yield distinct ids
  const ids = new Set([
    cohortClaimId(VCP_COHORT),
    cohortClaimId({ ...VCP_COHORT, factor: "ma_stack" }),
    cohortClaimId({ ...VCP_COHORT, decile: 9 }),
    cohortClaimId({ ...VCP_COHORT, horizon: 60 }),
  ]);
  assert.strictEqual(ids.size, 4, "distinct cohorts must produce distinct anchors");
});

// --- (r) factorCohortFromClaim extracts the selectors of a factor decile claim (null otherwise) ----------
check("factorCohortFromClaim reads a factor decile cohort's selectors (and null for a non-factor claim)", () => {
  const cohort = factorCohortFromClaim(vcpContractionRow());
  assert.ok(cohort, "a factor decile claim yields a cohort");
  assert.strictEqual(cohort!.factor, "vcp_contraction");
  assert.strictEqual(cohort!.slice_kind, "decile");
  assert.strictEqual(cohort!.decile, 10);
  assert.strictEqual(cohort!.horizon, 20);
  assert.strictEqual(cohort!.direction, "positive");
  // its anchor id round-trips to the SAME string the badge links to (the deep-link lands)
  assert.strictEqual(cohortClaimId(cohort!), "factor-vcp_contraction-d10-h20");
  // an event-study (non-factor) claim is NOT a factor cohort
  assert.strictEqual(factorCohortFromClaim(eventStudyRegimeRow()), null);
});

// --- (q2) a backed SCORE-COLUMN factor cohort resolves "Proven" but deep-links to its `signal-…` row -----
// The factor lab lists the three score columns (leadership/entry-quality/risk) as factor rows too, so a
// certified score-column cohort (leadership_score, the 1st ledger entry — it carries a `signal`) reads
// "Proven" there. Its `/evidence` row keeps the `signal-${signal}` id (J-02/J-05 unchanged), so the badge
// MUST deep-link to `signal-…`, NOT a cohort anchor the row never carries (so the click still lands).
check("resolveCohortEvidence links a backed score-column factor cohort to its `signal-…` ledger row", () => {
  const leadershipCohort: FactorCohort = { ...VCP_COHORT, factor: "leadership_score" };
  const status = resolveCohortEvidence(leadershipCohort, ledgerClaims());
  assert.strictEqual(status.proven, true);
  assert.strictEqual(status.label, "Proven");
  assert.strictEqual(status.href, "/evidence#signal-leadership_score");
  // the vcp_contraction (signal-less) cohort still links to its cohort anchor (the deep-links don't cross)
  assert.strictEqual(
    resolveCohortEvidence(VCP_COHORT, ledgerClaims()).href,
    "/evidence#factor-vcp_contraction-d10-h20",
  );
});

// --- (q3) claimAnchorId is the SINGLE row-id contract the /evidence row + the badge agree on -------------
check("claimAnchorId derives the /evidence row id (signal row, factor cohort row, none for event-study)", () => {
  // a score-column claim keeps its signal anchor (J-02/J-05 deep-links unchanged)
  assert.strictEqual(claimAnchorId(provenLeadershipRow()), "signal-leadership_score");
  // a signal-less plain-factor decile cohort derives its cohort anchor (the badge lands on THIS row)
  assert.strictEqual(claimAnchorId(vcpContractionRow()), "factor-vcp_contraction-d10-h20");
  // the event-study row carries no stable cohort id (unchanged — anchor absent)
  assert.strictEqual(claimAnchorId(eventStudyRegimeRow()), null);
});

// --- (s) claimSurface signal-less FACTOR branch => honest title + 'Research factor lab' linkback ---------
check("claimSurface gives a signal-less factor cohort an honest title + a 'Research factor lab' linkback", () => {
  const surface = claimSurface(vcpContractionRow());
  // an honest, meaningful title derived from the selectors — NEVER the misleading "Unmapped signal"
  assert.strictEqual(surface.title, "vcp_contraction — top decile (D10)");
  assert.notStrictEqual(surface.title, "Unmapped signal");
  assert.strictEqual(surface.titleIsSignalKey, false);
  // framed as historical out-of-sample evidence (never a buy/sell or return promise — anti-goal #2)
  assert.strictEqual(surface.subtitle, "Out-of-sample edge — factor top decile");
  // the linkback is honest — the Research factor lab, NOT the Stocks leaderboard
  assert.strictEqual(surface.href, "/research/factor-lab");
  assert.strictEqual(surface.label, "Research factor lab");
  assert.notStrictEqual(surface.label, "Stocks leaderboard");
});

// --- (t) the score row + event-study row stay BYTE-IDENTICAL after the factor branch is added ------------
check("claimSurface keeps the score + event-study branches byte-identical (J-05 / J-04 no regression)", () => {
  const score = claimSurface(provenLeadershipRow());
  assert.strictEqual(score.title, "leadership_score");
  assert.strictEqual(score.titleIsSignalKey, true);
  assert.strictEqual(score.subtitle, null);
  assert.strictEqual(score.href, "/stocks");
  assert.strictEqual(score.label, "Stocks leaderboard");

  const evt = claimSurface(eventStudyRegimeRow());
  assert.strictEqual(evt.title, "Breakout-watch setup");
  assert.strictEqual(evt.subtitle, "Out-of-sample edge in the Risk-on regime");
  assert.strictEqual(evt.href, "/research/event-study");
  assert.strictEqual(evt.label, "Research event-study lab");
});

console.log(`\n${passed} evidence-badge resolver checks passed.`);
