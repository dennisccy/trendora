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
/*
 * iter-18 NOTE (sanctioned data-basis reset): the fixtures below are SELF-CONTAINED SYNTHETIC
 * payloads exercising resolver BEHAVIOR (PASS -> Proven, FAIL -> honest dark, linkbacks, formats).
 * Values that historically mirrored live certified-claims ledger lines mirror the RETIRED basis;
 * the live ledger was regenerated 2026-07-03 on the 30-year basis and currently holds ZERO PASS
 * rows (every score/edge surface honestly reads "Not yet proven"). The backend frozen golden
 * (tests/test_evidence.py::test_canonical_ledger_frozen_golden) pins the live file byte-for-byte.
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
  combinationClaimId,
  combinationCohortFromClaim,
  combinationEvidenceAnchor,
  evidenceAnchor,
  factorCohortFromClaim,
  formatDays,
  formatEvidencePct,
  formatPValue,
  formatStreak,
  insufficientLabel,
  proofFieldsFor,
  regimeLabel,
  resolveCohortEvidence,
  resolveCombinationEvidence,
  resolveDrawdownExpectationsPanelState,
  resolveEvidenceStatus,
  type CertifiedClaim,
  type CombinationCohort,
  type DrawdownExpectations,
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
// SYNTHETIC retired-basis mirror (see the iter-18 NOTE at the top of this file): the values below MIRROR
// the RETIRED pre-swap ledger's certified leadership_score entry — the regenerated 30-year ledger holds no
// PASS row. The self-contained payload still pins the extraction contract: what the panel shows must equal
// the served entry.
// ======================================================================================================

/** A proven row mirroring the RETIRED-basis ledger entry (holdout edge / p-value / control excess /
 *  register date / cohort_n the pre-swap gate certified for leadership_score) — synthetic post-reset; the
 *  proof-field extraction contract it pins is basis-independent. */
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
  assert.strictEqual(formatEvidencePct(0.06359100763913017), "+6.36%"); // a realistic holdout edge / control excess (retired-basis value; see iter-18 NOTE)
  assert.strictEqual(formatEvidencePct(0.08909719710495288), "+8.91%"); // iter-11 J-07 — the real vcp h60 holdout edge / SPY control
  assert.strictEqual(formatEvidencePct(-0.004), "-0.40%");
  assert.strictEqual(formatEvidencePct(0), "+0.00%");
  assert.strictEqual(formatEvidencePct(null), "—");
  assert.strictEqual(formatEvidencePct(undefined), "—");
  assert.strictEqual(formatEvidencePct(Number.NaN), "—");
});

check("formatPValue renders the p-value to 4 significant figures (with a small/missing fallback)", () => {
  assert.strictEqual(formatPValue(0.0004997501249375312), "0.0004998"); // a realistic certified p-value (retired-basis value; see iter-18 NOTE)
  assert.strictEqual(formatPValue(0.05), "0.05");
  assert.strictEqual(formatPValue(0.0000000001), "< 0.0001");
  assert.strictEqual(formatPValue(null), "—");
  assert.strictEqual(formatPValue(undefined), "—");
});

// ======================================================================================================
// J-04 regime-conditioned evidence — the ClaimRow regime label + the honest non-score title/linkback.
// The row below MIRRORS the RETIRED 2nd ledger entry the pre-swap post-decompose gate certified
// (Breakout-watch × Risk-on event-study, signal: null) — synthetic post-reset (iter-18 NOTE at top). It
// still pins the J-04 display contract AND the J-05 no-regression invariant (the leadership score row's
// title + linkback stay byte-identical).
// ======================================================================================================

/** A certified (PASS) row mirroring the RETIRED iter-4 2nd ledger entry (synthetic post-reset): the Breakout-watch setup's
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
// The rows below MIRROR the RETIRED iter-8 ledger entries the pre-swap gate certified (synthetic
// post-reset — iter-18 NOTE at top): the 4th entry
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

/** A certified (PASS) row mirroring the RETIRED 4th ledger entry (synthetic post-reset): the vcp_contraction top-decile cohort.
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

/** A FAIL row mirroring the RETIRED 3rd ledger entry (synthetic post-reset): the ma_stack top-decile cohort that did NOT clear the
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

/** A certified (PASS) row mirroring the RETIRED iter-11 5th ledger entry (synthetic post-reset): the
 *  vcp_contraction top-decile cohort at the NON-20 forward-return horizon 60, promoted to the canonical
 *  ledger (`"ledger":"canonical"`). Like the h20 row it is signal-less (backs the factor lab + Evidence
 *  ONLY). Verdict values byte-matched the RETIRED `certified-claims.jsonl` line 5 (pre-swap basis). */
function vcpContractionH60Row(): CertifiedClaim {
  return {
    signal: null,
    claim: {
      kind: "factor",
      factor: "vcp_contraction",
      slice_kind: "decile",
      decile: 10,
      horizon: 60,
      direction: "positive",
      ledger: "canonical",
    },
    register_date: "2026-07-01",
    horizon: 60,
    cohort_n: 12026,
    control_n: 1055,
    verdict: {
      status: "PASS",
      reason: "certified: holdout edge +0.0891 beats the control out-of-sample and is significant after multiple-testing deflation (p=0.0004998 < alpha/5=0.01)",
      holdout_edge: 0.08909719710495288,
      control_excess: 0.08909719710495288,
      p_value: 0.0004997501249375312,
    },
    proven: true,
    forward_walk: null,
  };
}

/** The full post-iter-11 5-entry served claim list (leadership PASS, Breakout-watch Risk-on PASS, ma_stack
 *  FAIL, vcp_contraction h20 PASS, vcp_contraction h60 PASS) — the ledger the per-horizon factor-lab badges
 *  resolve against. */
function ledgerClaims(): CertifiedClaim[] {
  return [
    provenLeadershipRow(),
    eventStudyRegimeRow(),
    maStackFailRow(),
    vcpContractionRow(),
    vcpContractionH60Row(),
  ];
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

// --- (m2) iter-11 J-07 — the vcp_contraction h60 cohort matches the NEW 5th entry => "Proven" + …-h60 href -
// This is the first surfaced edge beyond the 20-day window: the SAME matcher, the SAME served payload, one
// more PASS-backed entry. The h60 badge deep-links to its OWN horizon-distinct row and the h20 badge is
// unperturbed (the two vcp_contraction rows never cross) — J-06 stays green.
check("resolveCohortEvidence matches the vcp_contraction h60 cohort => 'Proven' + a horizon-distinct href", () => {
  const cohortH60: FactorCohort = { ...VCP_COHORT, horizon: 60 };
  const status = resolveCohortEvidence(cohortH60, ledgerClaims());
  assert.strictEqual(status.proven, true);
  assert.strictEqual(status.label, "Proven");
  assert.strictEqual(status.href, "/evidence#factor-vcp_contraction-d10-h60");
  // the displayed h60 edge / control / p are read VERBATIM (byte-match the served fixture payload — the
  // anti-goal #3 display==served contract; values mirror the RETIRED basis, see iter-18 NOTE at top)
  assert.strictEqual(status.claim?.verdict.holdout_edge, 0.08909719710495288);
  assert.strictEqual(status.claim?.verdict.control_excess, 0.08909719710495288);
  assert.strictEqual(status.claim?.verdict.p_value, 0.0004997501249375312);
  assert.strictEqual(status.claim?.register_date, "2026-07-01");
  assert.strictEqual(status.claim?.signal, null); // signal-less — never lights a /stocks score badge
  // the h20 cohort still resolves to its OWN distinct row — the two vcp_contraction rows don't cross (J-06)
  const h20 = resolveCohortEvidence(VCP_COHORT, ledgerClaims());
  assert.strictEqual(h20.href, "/evidence#factor-vcp_contraction-d10-h20");
  assert.notStrictEqual(h20.href, status.href);
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
// Resolved against the FULL current 7-entry ledger (`ledgerClaims7()`, defined in the J-09 section below).
// iter-15 reconcile: `rs_spy_3m` is now a BACKED factor (certified at h60 — ledger row 7), so its former
// "unbacked factor" line becomes the stronger no-cross-horizon-leak negative: the SAME now-backed factor
// queried at an UNCERTIFIED horizon (h20) must still read "Not yet proven" — proven-ness never leaks h60 → h20
// (anti-goal #1). The dedicated h60 "Proven" proof lives in check (ee) below.
check("resolveCohortEvidence returns 'Not yet proven' on any selector mismatch", () => {
  for (const mismatch of [
    { ...VCP_COHORT, factor: "rs_spy_3m" }, // rs_spy_3m backed ONLY at h60 — this h20 query is an uncertified horizon (no leak)
    { ...VCP_COHORT, decile: 9 }, // wrong decile (not the top decile)
    { ...VCP_COHORT, horizon: 5 }, // uncertified horizon (only h20 + h60 are backed for vcp_contraction)
    { ...VCP_COHORT, direction: "negative" }, // wrong direction
    { ...VCP_COHORT, slice_kind: "sector" }, // wrong slice kind
  ] as FactorCohort[]) {
    const status = resolveCohortEvidence(mismatch, ledgerClaims7());
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

// --- (s2) iter-11 J-07 — the h60 factor-cohort subtitle is horizon-DISAMBIGUATED; h20 stays byte-identical -
// The two vcp_contraction rows on `/evidence` share a title, so the h60 row's subtitle gains a "· 60-day
// hold" suffix to self-distinguish. The h20 row's wording MUST stay EXACTLY iter-8's (J-06 non-regression).
check("claimSurface disambiguates the h60 factor-cohort subtitle while keeping the h20 wording byte-identical", () => {
  const h60 = claimSurface(vcpContractionH60Row());
  assert.strictEqual(h60.title, "vcp_contraction — top decile (D10)"); // title is horizon-agnostic (the row id carries the horizon)
  assert.strictEqual(h60.titleIsSignalKey, false);
  assert.strictEqual(h60.subtitle, "Out-of-sample edge — factor top decile · 60-day hold");
  assert.strictEqual(h60.href, "/research/factor-lab");
  assert.strictEqual(h60.label, "Research factor lab");
  // still historical out-of-sample framing — never a buy/sell or return promise (anti-goal #2)
  assert.ok(!/buy|sell|return|target|price/i.test(h60.subtitle), "no return/price/buy-sell language");
  // the pre-existing h20 vcp_contraction row is byte-identical to iter-8 (J-06 must not regress)
  assert.strictEqual(claimSurface(vcpContractionRow()).subtitle, "Out-of-sample edge — factor top decile");
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

// ======================================================================================================
// J-08 (iter-13) — the read-side COMBINATION-cohort matcher for a signal-less multi-factor composite cohort.
// The row below MIRRORS the RETIRED 6th ledger entry the pre-swap gate certified (synthetic post-reset —
// iter-18 NOTE at top): the
// `rs_spy_3m × high_proximity` composite cohort @ h20 (PASS, holdout/control +0.04693, p 0.0009995,
// signal-less, promoted to canonical). These pin the J-08 display contract: the certified composite reads
// "Proven" (a PASS-backed leg-set match, order-independent) and deep-links to its ledger row; every other
// combination — different legs, a different quantile of the SAME factors, a different horizon, the reversed
// direction, or a matched-but-non-PASS entry — reads "Not yet proven" with no link (anti-goal #1 upheld).
// ======================================================================================================

/** The queried composite cohort for the certified combination (legs in the ledger's stored order). */
const COMBINATION_COHORT: CombinationCohort = {
  kind: "combination",
  cohort: "composite",
  condition: ["rs_spy_3m:top:quintile", "high_proximity:top:tertile"],
  horizon: 20,
  direction: "positive",
};

/** A certified (PASS) row mirroring the RETIRED 6th ledger entry (synthetic post-reset): the
 *  `rs_spy_3m × high_proximity` composite cohort @ h20, promoted to the canonical ledger
 *  (`"ledger":"canonical"`). It deliberately carries NO `signal` (a combination cohort — it backs the
 *  combination lab + Evidence ONLY, never a per-stock score badge), so it MUST NOT enter the inline
 *  `proven_signals` map. Verdict values byte-matched the RETIRED `certified-claims.jsonl` line 6
 *  (pre-swap basis). */
function combinationRow(): CertifiedClaim {
  return {
    signal: null,
    claim: {
      kind: "combination",
      cohort: "composite",
      condition: ["rs_spy_3m:top:quintile", "high_proximity:top:tertile"],
      horizon: 20,
      direction: "positive",
      ledger: "canonical",
    },
    register_date: "2026-07-01",
    horizon: 20,
    cohort_n: 23929,
    control_n: 1102,
    verdict: {
      status: "PASS",
      reason:
        "certified: holdout edge +0.04693 beats the control out-of-sample and is significant after multiple-testing deflation (p=0.0009995 < alpha/6=0.008333)",
      holdout_edge: 0.046931901591708916,
      control_excess: 0.046931901591708916,
      p_value: 0.0009995002498750624,
    },
    proven: true,
    forward_walk: null,
  };
}

/** The full post-iter-13 6-entry served claim list (the 5 prior rows PLUS the combination PASS) — the ledger
 *  the composite-cohort badge resolves against. */
function ledgerClaims6(): CertifiedClaim[] {
  return [...ledgerClaims(), combinationRow()];
}

// --- (u) full leg-set match (order-independent) against a PASS entry => "Proven" + the combination href ---
check("resolveCombinationEvidence matches the certified composite cohort (either leg order) => 'Proven' + href", () => {
  const status = resolveCombinationEvidence(COMBINATION_COHORT, ledgerClaims6());
  assert.strictEqual(status.proven, true);
  assert.strictEqual(status.label, PROVEN_LABEL);
  assert.strictEqual(status.label, "Proven");
  assert.strictEqual(status.href, "/evidence#combination-high_proximity-rs_spy_3m-h20");
  assert.ok(status.href!.startsWith("/evidence#"), "the proven composite badge must deep-link into /evidence");
  // the backing claim row is returned VERBATIM (the displayed-numbers-are-correct contract, anti-goal #3)
  assert.strictEqual(status.claim?.verdict.holdout_edge, 0.046931901591708916);
  assert.strictEqual(status.claim?.verdict.control_excess, 0.046931901591708916);
  assert.strictEqual(status.claim?.verdict.p_value, 0.0009995002498750624);
  assert.strictEqual(status.claim?.register_date, "2026-07-01");
  assert.strictEqual(status.claim?.signal, null); // signal-less — never lights a /stocks score badge
  // ORDER-INDEPENDENT: querying with the legs reversed resolves to the SAME proven row + href
  const reversed: CombinationCohort = {
    ...COMBINATION_COHORT,
    condition: ["high_proximity:top:tertile", "rs_spy_3m:top:quintile"],
  };
  const reversedStatus = resolveCombinationEvidence(reversed, ledgerClaims6());
  assert.strictEqual(reversedStatus.proven, true);
  assert.strictEqual(reversedStatus.href, status.href);
});

// --- (v) FULL-leg match, NOT factor-key match: a different side/quantile of the SAME factors must NOT match -
check("resolveCombinationEvidence matches the full leg-set, not just the factor keys", () => {
  // same two factors, but leg 2 is a DIFFERENT side/quantile than the certified `high_proximity:top:tertile`
  const sameFactorsDifferentLegs: CombinationCohort = {
    ...COMBINATION_COHORT,
    condition: ["rs_spy_3m:top:quintile", "high_proximity:bottom:tertile"],
  };
  const status = resolveCombinationEvidence(sameFactorsDifferentLegs, ledgerClaims6());
  assert.strictEqual(status.proven, false, "a different side/quantile of the same factors must not false-match");
  assert.strictEqual(status.label, "Not yet proven");
  assert.strictEqual(status.href, null);
});

// --- (w) any mismatch (legs / horizon / direction) => "Not yet proven", no href -------------------------
check("resolveCombinationEvidence returns 'Not yet proven' on any leg/horizon/direction mismatch", () => {
  for (const mismatch of [
    { ...COMBINATION_COHORT, condition: ["rs_spy_3m:top:quintile", "atr_pct:bottom:tertile"] }, // the FAILED default pair
    { ...COMBINATION_COHORT, condition: ["rs_spy_3m:top:quintile"] }, // only one leg
    { ...COMBINATION_COHORT, horizon: 60 }, // uncertified horizon
    { ...COMBINATION_COHORT, direction: "negative" }, // reversed direction
  ] as CombinationCohort[]) {
    const status = resolveCombinationEvidence(mismatch, ledgerClaims6());
    assert.strictEqual(status.proven, false, `cohort ${JSON.stringify(mismatch.condition)}@${mismatch.horizon}/${mismatch.direction} must not resolve proven`);
    assert.strictEqual(status.label, "Not yet proven");
    assert.strictEqual(status.href, null);
    assert.strictEqual(status.claim, null);
  }
});

// --- (x) a matched-but-non-PASS combination entry => "Not yet proven" (proven-ness flows only from PASS) --
check("resolveCombinationEvidence treats a matched-but-non-PASS combination as 'Not yet proven'", () => {
  const failRow = combinationRow();
  failRow.proven = false;
  failRow.verdict = { ...failRow.verdict, status: "FAIL" };
  const status = resolveCombinationEvidence(COMBINATION_COHORT, [failRow]);
  assert.strictEqual(status.proven, false);
  assert.strictEqual(status.label, NOT_PROVEN_LABEL);
  assert.strictEqual(status.href, null);
  assert.strictEqual(status.claim, null);
});

// --- (y) FAIL-SAFE: an empty / null / undefined claim list => "Not yet proven", no href -----------------
check("resolveCombinationEvidence falls back to 'Not yet proven' for an empty/null/undefined claim list", () => {
  for (const claims of [[], null, undefined] as (CertifiedClaim[] | null | undefined)[]) {
    const status = resolveCombinationEvidence(COMBINATION_COHORT, claims);
    assert.strictEqual(status.proven, false);
    assert.strictEqual(status.label, "Not yet proven");
    assert.strictEqual(status.href, null);
    assert.strictEqual(status.claim, null);
  }
});

// --- (z) combinationCohortFromClaim extracts the certified claim; rejects non-combination / malformed -----
check("combinationCohortFromClaim reads a composite combination cohort (null for a non-combination/malformed claim)", () => {
  const cohort = combinationCohortFromClaim(combinationRow());
  assert.ok(cohort, "a composite combination claim yields a cohort");
  assert.strictEqual(cohort!.kind, "combination");
  assert.strictEqual(cohort!.cohort, "composite");
  assert.deepStrictEqual(cohort!.condition, ["rs_spy_3m:top:quintile", "high_proximity:top:tertile"]);
  assert.strictEqual(cohort!.horizon, 20);
  assert.strictEqual(cohort!.direction, "positive");
  // a factor / event-study claim is NOT a combination cohort
  assert.strictEqual(combinationCohortFromClaim(vcpContractionRow()), null);
  assert.strictEqual(combinationCohortFromClaim(eventStudyRegimeRow()), null);
  // malformed combination claims are rejected (empty condition, non-array condition, missing horizon)
  const emptyCondition = combinationRow();
  emptyCondition.claim = { ...emptyCondition.claim, condition: [] };
  assert.strictEqual(combinationCohortFromClaim(emptyCondition), null);
  const nonArrayCondition = combinationRow();
  nonArrayCondition.claim = { ...nonArrayCondition.claim, condition: "rs_spy_3m:top:quintile" };
  assert.strictEqual(combinationCohortFromClaim(nonArrayCondition), null);
  const noHorizon = combinationRow();
  delete (noHorizon.claim as Record<string, unknown>).horizon;
  assert.strictEqual(combinationCohortFromClaim(noHorizon), null);
});

// --- (aa) the combination anchor is stable, order-independent, and DISTINCT from any factor anchor --------
check("combinationClaimId / combinationEvidenceAnchor derive a stable, order-independent, factor-distinct anchor", () => {
  assert.strictEqual(combinationClaimId(COMBINATION_COHORT), "combination-high_proximity-rs_spy_3m-h20");
  // order-independent: reversing the legs yields the SAME id
  const reversed: CombinationCohort = {
    ...COMBINATION_COHORT,
    condition: ["high_proximity:top:tertile", "rs_spy_3m:top:quintile"],
  };
  assert.strictEqual(combinationClaimId(reversed), combinationClaimId(COMBINATION_COHORT));
  // the anchor is the id under the /evidence hash — the badge href lands on the ledger row id
  assert.strictEqual(combinationEvidenceAnchor(COMBINATION_COHORT), "/evidence#combination-high_proximity-rs_spy_3m-h20");
  assert.strictEqual(
    combinationEvidenceAnchor(COMBINATION_COHORT),
    `/evidence#${combinationClaimId(COMBINATION_COHORT)}`,
  );
  // DISTINCT from any factor anchor (the `combination-` prefix guarantees no cross-collision)
  assert.ok(combinationClaimId(COMBINATION_COHORT).startsWith("combination-"));
  assert.notStrictEqual(combinationClaimId(COMBINATION_COHORT), cohortClaimId(VCP_COHORT));
});

// --- (bb) claimAnchorId derives the combination row id (distinct from factor + signal anchors) ------------
check("claimAnchorId returns the combination anchor for a combination claim (distinct from factor/signal)", () => {
  assert.strictEqual(claimAnchorId(combinationRow()), "combination-high_proximity-rs_spy_3m-h20");
  // the prior contracts are unchanged: score row keeps its signal anchor, factor cohort keeps its factor id
  assert.strictEqual(claimAnchorId(provenLeadershipRow()), "signal-leadership_score");
  assert.strictEqual(claimAnchorId(vcpContractionRow()), "factor-vcp_contraction-d10-h20");
  // the combination anchor is distinct from BOTH
  const combo = claimAnchorId(combinationRow());
  assert.notStrictEqual(combo, claimAnchorId(provenLeadershipRow()));
  assert.notStrictEqual(combo, claimAnchorId(vcpContractionRow()));
});

// --- (cc) claimSurface combination branch => honest composite title + combination-lab linkback -----------
check("claimSurface gives a signal-less combination claim an honest title + a 'Multi-factor combination lab' linkback", () => {
  const surface = claimSurface(combinationRow());
  // an honest title naming the two factors — NEVER the misleading "Unmapped signal"
  assert.strictEqual(surface.title, "rs_spy_3m × high_proximity — composite");
  assert.notStrictEqual(surface.title, "Unmapped signal");
  assert.strictEqual(surface.titleIsSignalKey, false);
  // framed as historical out-of-sample evidence (never a buy/sell or return promise — anti-goal #2)
  assert.strictEqual(surface.subtitle, "Out-of-sample edge — multi-factor composite");
  assert.ok(!/buy|sell|return|target|price/i.test(surface.subtitle!), "no return/price/buy-sell language");
  // the linkback is honest — the Multi-factor combination lab, NOT the Stocks leaderboard
  assert.strictEqual(surface.href, "/research/factor-combination");
  assert.strictEqual(surface.label, "Multi-factor combination lab");
  assert.notStrictEqual(surface.label, "Stocks leaderboard");
});

// --- (dd) the combination claim adds NO /stocks signal + does not perturb the prior branches -------------
check("the combination claim is signal-less and leaves the score/factor/event-study branches byte-identical", () => {
  // signal-less: it must NOT resolve any inline /stocks score badge (proven_signals is unaffected — J-01..J-03)
  assert.strictEqual(resolveEvidenceStatus("leadership_score", {}).proven, false);
  // the prior claimSurface branches are byte-identical with the combination row present in the ledger
  const score = claimSurface(provenLeadershipRow());
  assert.strictEqual(score.title, "leadership_score");
  assert.strictEqual(score.href, "/stocks");
  const factor = claimSurface(vcpContractionRow());
  assert.strictEqual(factor.title, "vcp_contraction — top decile (D10)");
  assert.strictEqual(factor.href, "/research/factor-lab");
  const evt = claimSurface(eventStudyRegimeRow());
  assert.strictEqual(evt.title, "Breakout-watch setup");
  assert.strictEqual(evt.href, "/research/event-study");
  // the certified factor cohorts still resolve to their OWN rows (the combination row never cross-matches)
  assert.strictEqual(resolveCohortEvidence(VCP_COHORT, ledgerClaims6()).href, "/evidence#factor-vcp_contraction-d10-h20");
});

// ======================================================================================================
// J-09 (iter-15) — the per-horizon COHORT matcher lights a SECOND factor's NON-20 certified horizon.
// The row below MIRRORS the RETIRED 7th ledger entry the pre-swap gate certified (synthetic post-reset —
// iter-18 NOTE at top): the signal-less
// `rs_spy_3m` top-decile cohort @ h60, promoted to the canonical ledger (`"ledger":"canonical"`, strict
// Bonferroni divisor 7). It pins the J-09 display contract: `rs_spy_3m`'s h60 cohort reads "Proven" (a
// PASS-backed per-horizon match) deep-linking to its OWN row, while its h1/h5/h10/h20 cohorts stay
// "Not yet proven" (no cross-horizon leak) — and `rs_spy_3m` ∉ the three score columns, so it carries NO
// `signal` and NEVER enters `proven_signals` (J-01/J-02/J-03 unaffected). SAME general matcher, SAME served
// payload, one more PASS-backed entry — no factor-specific branch (iter-8 lesson).
// ======================================================================================================

/** A certified (PASS) row mirroring the RETIRED iter-15 7th ledger entry (synthetic post-reset): the
 *  rs_spy_3m top-decile cohort at the NON-20 forward-return horizon 60, promoted to the canonical ledger
 *  (`"ledger":"canonical"`). Like the vcp_contraction factor rows it is signal-less (rs_spy_3m ∉ the three
 *  score columns — it backs the factor lab + Evidence ONLY, never a `/stocks` inline badge). Verdict values
 *  byte-matched the RETIRED `certified-claims.jsonl` line 7 (pre-swap basis): holdout/control +0.2134,
 *  p 0.0004998, divisor 7. */
function rsSpy3mH60Row(): CertifiedClaim {
  return {
    signal: null,
    claim: {
      kind: "factor",
      factor: "rs_spy_3m",
      slice_kind: "decile",
      decile: 10,
      horizon: 60,
      direction: "positive",
      ledger: "canonical",
    },
    register_date: "2026-07-01",
    horizon: 60,
    cohort_n: 12026,
    control_n: 1101,
    verdict: {
      status: "PASS",
      reason:
        "certified: holdout edge +0.2134 beats the control out-of-sample and is significant after multiple-testing deflation (p=0.0004998 < alpha/7=0.007143)",
      holdout_edge: 0.21344270202534893,
      control_excess: 0.21344270202534893,
      p_value: 0.0004997501249375312,
    },
    proven: true,
    forward_walk: null,
  };
}

/** The full post-iter-15 7-entry served claim list (the 6 prior rows PLUS the rs_spy_3m h60 factor PASS,
 *  ledger row 7) — the current full ledger the per-horizon factor-lab badges resolve against. */
function ledgerClaims7(): CertifiedClaim[] {
  return [...ledgerClaims6(), rsSpy3mH60Row()];
}

// --- (ee) iter-15 J-09 — the rs_spy_3m h60 cohort matches the NEW 7th entry => 'Proven' + …-h60 href ------
// A SECOND factor surfaced beyond the 20-day window: the SAME general matcher, the SAME served payload, one
// more PASS-backed entry. The h60 badge deep-links to its OWN horizon-distinct row; every uncertified horizon
// of rs_spy_3m (h1/h5/h10/h20) stays "Not yet proven"; and the vcp_contraction h60 badge is unperturbed (the
// two h60 factor rows never cross) — J-06/J-07 stay green.
check("resolveCohortEvidence matches the rs_spy_3m h60 cohort => 'Proven' + a horizon-distinct href", () => {
  const rsSpyH60: FactorCohort = {
    factor: "rs_spy_3m",
    slice_kind: "decile",
    decile: 10,
    horizon: 60,
    direction: "positive",
  };
  const status = resolveCohortEvidence(rsSpyH60, ledgerClaims7());
  assert.strictEqual(status.proven, true);
  assert.strictEqual(status.label, PROVEN_LABEL);
  assert.strictEqual(status.label, "Proven");
  assert.strictEqual(status.href, "/evidence#factor-rs_spy_3m-d10-h60");
  assert.ok(status.href!.startsWith("/evidence#"), "the proven cohort badge must deep-link into /evidence");
  // the displayed h60 edge / SPY control / p are read VERBATIM (byte-match the served fixture payload,
  // which mirrors the RETIRED certified-claims.jsonl row 7 — the anti-goal #3 display==served contract)
  assert.strictEqual(status.claim?.verdict.holdout_edge, 0.21344270202534893);
  assert.strictEqual(status.claim?.verdict.control_excess, 0.21344270202534893);
  assert.strictEqual(status.claim?.verdict.p_value, 0.0004997501249375312);
  assert.strictEqual(status.claim?.register_date, "2026-07-01");
  assert.strictEqual(status.claim?.signal, null); // signal-less — never lights a /stocks score badge
  // every UNCERTIFIED horizon of the SAME factor stays "Not yet proven" (no cross-horizon leak — anti-goal #1)
  for (const h of [1, 5, 10, 20]) {
    const uncertified = resolveCohortEvidence({ ...rsSpyH60, horizon: h }, ledgerClaims7());
    assert.strictEqual(uncertified.proven, false, `rs_spy_3m h${h} must read Not yet proven`);
    assert.strictEqual(uncertified.label, "Not yet proven");
    assert.strictEqual(uncertified.href, null);
    assert.strictEqual(uncertified.claim, null);
  }
  // the vcp_contraction h60 badge is unperturbed — the two h60 factor rows resolve to DISTINCT rows (J-07)
  const vcpH60 = resolveCohortEvidence({ ...VCP_COHORT, horizon: 60 }, ledgerClaims7());
  assert.strictEqual(vcpH60.href, "/evidence#factor-vcp_contraction-d10-h60");
  assert.notStrictEqual(vcpH60.href, status.href);
});

// --- (ff) iter-15 J-09 — the rs_spy_3m h60 `/evidence` ROW renders through the EXISTING signal-less factor
// branch: an honest factor title, the horizon-disambiguated subtitle, the "Backs: Research factor lab →"
// linkback, and the `factor-rs_spy_3m-d10-h60` anchor — so the badge href and the row id agree (deep-link lands).
check("claimSurface + claimAnchorId render the rs_spy_3m h60 /evidence row honestly (factor-lab linkback + anchor)", () => {
  const row = rsSpy3mH60Row();
  const surface = claimSurface(row);
  // an honest factor title derived from the selectors — NEVER the misleading "Unmapped signal"
  assert.strictEqual(surface.title, "rs_spy_3m — top decile (D10)");
  assert.notStrictEqual(surface.title, "Unmapped signal");
  assert.strictEqual(surface.titleIsSignalKey, false);
  // horizon-disambiguated (NON-20) subtitle, still historical out-of-sample framing (never buy/sell — anti-goal #2)
  assert.strictEqual(surface.subtitle, "Out-of-sample edge — factor top decile · 60-day hold");
  assert.ok(!/buy|sell|return|target|price/i.test(surface.subtitle!), "no return/price/buy-sell language");
  // the linkback is honest — the Research factor lab, NOT the Stocks leaderboard
  assert.strictEqual(surface.href, "/research/factor-lab");
  assert.strictEqual(surface.label, "Research factor lab");
  assert.notStrictEqual(surface.label, "Stocks leaderboard");
  // the row id the badge deep-links to (badge href === row id ⇒ the click lands on THIS row)
  assert.strictEqual(claimAnchorId(row), "factor-rs_spy_3m-d10-h60");
  assert.strictEqual(`/evidence#${claimAnchorId(row)}`, "/evidence#factor-rs_spy_3m-d10-h60");
  // signal-less: it adds NO inline /stocks score badge (proven_signals stays unaffected — J-01/J-02/J-03)
  assert.strictEqual(row.signal, null);
  assert.strictEqual(resolveEvidenceStatus("leadership_score", {}).proven, false);
});

// --- drawdown & dry-spell expectations formatters (goal-mcp-loop iter-41, J-25) -------------------------
check("insufficientLabel renders the exact honest-floor copy", () => {
  assert.strictEqual(insufficientLabel(0), "insufficient (n=0)");
  assert.strictEqual(insufficientLabel(7), "insufficient (n=7)");
});

check("formatDays renders one decimal + 'd', and an em dash for null/undefined/non-finite", () => {
  assert.strictEqual(formatDays(5), "5.0d");
  assert.strictEqual(formatDays(7.4), "7.4d");
  assert.strictEqual(formatDays(0), "0.0d");
  assert.strictEqual(formatDays(null), "—");
  assert.strictEqual(formatDays(undefined), "—");
  assert.strictEqual(formatDays(Number.NaN), "—");
});

check("formatStreak renders a rounded integer, and an em dash for null/undefined/non-finite", () => {
  assert.strictEqual(formatStreak(2), "2");
  assert.strictEqual(formatStreak(0), "0");
  assert.strictEqual(formatStreak(3.0), "3");
  assert.strictEqual(formatStreak(null), "—");
  assert.strictEqual(formatStreak(undefined), "—");
});

// --- drawdown-expectations panel state resolver (ops-hardening iter-29, AG-8 residual-failure disclosure,
// TC-5) — the pure decision function `DrawdownExpectationsPanel` (app/evidence/page.tsx) branches on. Three
// states: the pre-existing "present" (a table renders) and "absent" (no expectations, no status field —
// renders nothing, unchanged honest-None cohort-unresolvable case) plus the NEW "unavailable" (a per-claim
// compute failure this request — an inline note, no table). Mirrors the extracted-decision-function pattern
// `lib/background-compute-panel-branch.ts` established (iter-24/25, J-09).
const SAMPLE_EXPECTATIONS: DrawdownExpectations = {
  horizon: 20,
  min_sample: 5,
  streak_min_n: 3,
  survivorship_bias: "Current-membership seed; survivorship bias not corrected for.",
  method_note: "Median/p90 by market phase at entry.",
  by_phase: [],
};

check("resolveDrawdownExpectationsPanelState: expectations present => 'present', carrying it verbatim", () => {
  const claim: CertifiedClaim = { ...provenRow("leadership_score"), expectations: SAMPLE_EXPECTATIONS };
  const state = resolveDrawdownExpectationsPanelState(claim);
  assert.strictEqual(state.kind, "present");
  if (state.kind === "present") {
    assert.strictEqual(state.expectations, SAMPLE_EXPECTATIONS); // read verbatim, never recomputed
  }
});

check("resolveDrawdownExpectationsPanelState: expectations_status='unavailable' => 'unavailable' (TC-5)", () => {
  const claim: CertifiedClaim = { ...provenRow("leadership_score"), expectations_status: "unavailable" };
  const state = resolveDrawdownExpectationsPanelState(claim);
  assert.strictEqual(state.kind, "unavailable");
});

check(
  "resolveDrawdownExpectationsPanelState: no expectations + no status field => 'absent' (pre-existing " +
    "honest-None case, unchanged, TC-5)",
  () => {
    const claim: CertifiedClaim = provenRow("leadership_score"); // no expectations, no expectations_status
    const state = resolveDrawdownExpectationsPanelState(claim);
    assert.strictEqual(state.kind, "absent");
  },
);

check(
  "resolveDrawdownExpectationsPanelState: 'unavailable' is DISTINCT from the pre-existing absent case (TC-5)",
  () => {
    const unavailable = resolveDrawdownExpectationsPanelState({
      ...provenRow("leadership_score"),
      expectations_status: "unavailable",
    });
    const absent = resolveDrawdownExpectationsPanelState(provenRow("leadership_score"));
    assert.notStrictEqual(unavailable.kind, absent.kind);
    assert.strictEqual(unavailable.kind, "unavailable");
    assert.strictEqual(absent.kind, "absent");
  },
);

// --- ops-hardening iter-47 (audit B2, TC-3): a FOURTH state — "refreshing" — a resolved, REAL last-good
// prior-generation `expectations` payload served while a newer generation (an unrelated ingest bumped the
// shared dataset-version stamp) computes in the background. Distinct from BOTH "present" (current
// generation, no status field) and "unavailable" (no expectations at all).
check(
  "resolveDrawdownExpectationsPanelState: expectations + expectations_status='refreshing' => 'refreshing', " +
    "carrying the served (last-good) payload verbatim (TC-3)",
  () => {
    const claim: CertifiedClaim = {
      ...provenRow("leadership_score"),
      expectations: SAMPLE_EXPECTATIONS,
      expectations_status: "refreshing",
    };
    const state = resolveDrawdownExpectationsPanelState(claim);
    assert.strictEqual(state.kind, "refreshing");
    if (state.kind === "refreshing") {
      assert.strictEqual(state.expectations, SAMPLE_EXPECTATIONS); // read verbatim, never recomputed
    }
  },
);

check(
  "resolveDrawdownExpectationsPanelState: 'refreshing' is DISTINCT from 'present' and from 'unavailable' (TC-3)",
  () => {
    const refreshing = resolveDrawdownExpectationsPanelState({
      ...provenRow("leadership_score"),
      expectations: SAMPLE_EXPECTATIONS,
      expectations_status: "refreshing",
    });
    const present = resolveDrawdownExpectationsPanelState({
      ...provenRow("leadership_score"),
      expectations: SAMPLE_EXPECTATIONS,
    });
    const unavailable = resolveDrawdownExpectationsPanelState({
      ...provenRow("leadership_score"),
      expectations_status: "unavailable",
    });
    assert.strictEqual(refreshing.kind, "refreshing");
    assert.strictEqual(present.kind, "present");
    assert.strictEqual(unavailable.kind, "unavailable");
    assert.notStrictEqual(refreshing.kind, present.kind);
    assert.notStrictEqual(refreshing.kind, unavailable.kind);
  },
);

check(
  "resolveDrawdownExpectationsPanelState: no expectations but expectations_status='refreshing' (an " +
    "impossible-in-practice payload shape) resolves to 'absent', never 'refreshing' without a payload to " +
    "show — the resolver checks `claim.expectations` FIRST",
  () => {
    const claim: CertifiedClaim = {
      ...provenRow("leadership_score"),
      expectations_status: "refreshing",
    };
    const state = resolveDrawdownExpectationsPanelState(claim);
    assert.strictEqual(state.kind, "absent");
  },
);

console.log(`\n${passed} evidence-badge resolver checks passed.`);
