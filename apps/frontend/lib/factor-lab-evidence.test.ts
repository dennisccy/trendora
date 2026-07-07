/**
 * Unit tests for the per-horizon factor-lab evidence badges (lib/factor-lab-evidence.ts) — J-07.
 *
 * No test framework is installed in this frontend; these run under the repo's TS type-strip convention:
 *   npx tsx lib/factor-lab-evidence.test.ts
 *
 * The J-07 crux (the Factor Lab's single-horizon evidence marker becomes an honest PER-HORIZON view):
 *   - the served horizon vocabulary yields exactly ONE badge per horizon, IN ORDER, carrying its horizon;
 *   - vcp_contraction reads "Proven" at h20 AND h60 (two PASS-backed canonical entries), each deep-linking to
 *     its OWN horizon-distinct /evidence row; its uncertified horizons (1/5/10) read "Not yet proven", no link;
 *   - a matched-but-non-PASS factor (ma_stack FAIL) never reads "Proven" at ANY horizon (anti-goal #1);
 *   - a backed SCORE-COLUMN factor (leadership_score) reads "Proven" at its certified horizon and deep-links
 *     to its `signal-…` row (honest — NOT special-cased to vcp only);
 *   - an empty / failed evidence fetch leaves EVERY horizon "Not yet proven" with no link (fail-safe honesty).
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

import { factorHorizonBadges } from "./factor-lab-evidence.ts";
import { NOT_PROVEN_LABEL, PROVEN_LABEL, type CertifiedClaim } from "./evidence.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

/** The served horizon vocabulary + top decile the factor lab threads in from `data.horizons` /
 *  `data.deciles_count` (config-driven — never hardcoded in the component). */
const HORIZONS = [1, 5, 10, 20, 60];
const TOP_DECILE = 10;

/** The RETIRED 1st ledger entry (synthetic post-reset — iter-18 NOTE at top): the leadership_score
 *  score-column cohort (PASS, carries a `signal`). */
function leadershipRow(): CertifiedClaim {
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

/** The RETIRED 3rd ledger entry (synthetic post-reset): ma_stack top-decile h20 that the referee REJECTED
 *  (a signal-less FAIL row). */
function maStackFailRow(): CertifiedClaim {
  return {
    signal: null,
    claim: { kind: "factor", factor: "ma_stack", slice_kind: "decile", decile: 10, horizon: 20, direction: "positive" },
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

/** The RETIRED 4th ledger entry (synthetic post-reset): the vcp_contraction top-decile h20 cohort (PASS,
 *  signal-less). */
function vcpH20Row(): CertifiedClaim {
  return {
    signal: null,
    claim: { kind: "factor", factor: "vcp_contraction", slice_kind: "decile", decile: 10, horizon: 20, direction: "positive" },
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

/** The RETIRED 5th ledger entry (iter-11, synthetic post-reset): the vcp_contraction top-decile @ h60
 *  canonical PASS (signal-less). Verdict values byte-matched the RETIRED `certified-claims.jsonl` line 5
 *  (pre-swap basis) — the resolver contract they pin is basis-independent. */
function vcpH60Row(): CertifiedClaim {
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

/** The full post-iter-11 5-entry served claim list (leadership PASS, event-study elided here — irrelevant to
 *  factor cohorts, ma_stack FAIL, vcp h20 PASS, vcp h60 PASS) the per-horizon badges resolve against. */
function ledgerClaims(): CertifiedClaim[] {
  return [leadershipRow(), maStackFailRow(), vcpH20Row(), vcpH60Row()];
}

/** Find the single badge for horizon `h` in a descriptor list. */
function at(badges: ReturnType<typeof factorHorizonBadges>, h: number) {
  const b = badges.find((x) => x.horizon === h);
  assert.ok(b, `a badge for horizon ${h} must exist`);
  return b!;
}

// --- (a) exactly one badge per served horizon, in order, each carrying its horizon + factor + top decile ---
check("factorHorizonBadges emits one badge per horizon, in the served order", () => {
  const badges = factorHorizonBadges("vcp_contraction", TOP_DECILE, HORIZONS, ledgerClaims());
  assert.strictEqual(badges.length, HORIZONS.length);
  assert.deepStrictEqual(badges.map((b) => b.horizon), [1, 5, 10, 20, 60]);
  badges.forEach((b) => {
    assert.strictEqual(b.factor, "vcp_contraction");
    assert.strictEqual(b.topDecile, 10);
  });
});

// --- (b) vcp_contraction: h60 + h20 "Proven" with horizon-distinct deep-links; h1/h5/h10 "Not yet proven" ---
check("vcp_contraction reads 'Proven' at h60 and h20 with horizon-distinct hrefs; h1/h5/h10 'Not yet proven'", () => {
  const badges = factorHorizonBadges("vcp_contraction", TOP_DECILE, HORIZONS, ledgerClaims());

  const h60 = at(badges, 60);
  assert.strictEqual(h60.proven, true);
  assert.strictEqual(h60.label, PROVEN_LABEL);
  assert.strictEqual(h60.label, "Proven");
  assert.strictEqual(h60.href, "/evidence#factor-vcp_contraction-d10-h60");
  // the displayed h60 edge / control / p are read VERBATIM (byte-match the served fixture payload — the
  // anti-goal #3 display==served contract; values mirror the RETIRED basis, see iter-18 NOTE at top)
  assert.strictEqual(h60.claim?.verdict.holdout_edge, 0.08909719710495288);
  assert.strictEqual(h60.claim?.verdict.control_excess, 0.08909719710495288);
  assert.strictEqual(h60.claim?.verdict.p_value, 0.0004997501249375312);
  assert.strictEqual(h60.claim?.register_date, "2026-07-01");
  assert.strictEqual(h60.claim?.signal, null); // signal-less — never lights a /stocks score badge

  const h20 = at(badges, 20);
  assert.strictEqual(h20.proven, true);
  assert.strictEqual(h20.href, "/evidence#factor-vcp_contraction-d10-h20"); // J-06 unchanged
  assert.notStrictEqual(h20.href, h60.href); // the two vcp rows deep-link to distinct anchors

  for (const h of [1, 5, 10]) {
    const b = at(badges, h);
    assert.strictEqual(b.proven, false, `h${h} must be Not yet proven`);
    assert.strictEqual(b.label, NOT_PROVEN_LABEL);
    assert.strictEqual(b.label, "Not yet proven");
    assert.strictEqual(b.href, null);
    assert.strictEqual(b.claim, null);
  }
});

// --- (c) a matched-but-non-PASS factor (ma_stack FAIL) never reads "Proven" at ANY horizon ----------------
check("a matched-but-non-PASS factor (ma_stack FAIL) stays 'Not yet proven' at every horizon", () => {
  const badges = factorHorizonBadges("ma_stack", TOP_DECILE, HORIZONS, ledgerClaims());
  badges.forEach((b) => {
    assert.strictEqual(b.proven, false, `ma_stack h${b.horizon} must not be Proven`);
    assert.strictEqual(b.label, "Not yet proven");
    assert.strictEqual(b.href, null);
  });
});

// --- (d) a backed SCORE-COLUMN factor (leadership_score) is HONESTLY "Proven" at its horizon --------------
check("leadership_score reads 'Proven' at its h20 and deep-links to its signal-… row (honest, not special-cased)", () => {
  const badges = factorHorizonBadges("leadership_score", TOP_DECILE, HORIZONS, ledgerClaims());
  const h20 = at(badges, 20);
  assert.strictEqual(h20.proven, true);
  assert.strictEqual(h20.href, "/evidence#signal-leadership_score"); // its real /evidence row id (not a cohort anchor)
  for (const h of [1, 5, 10, 60]) {
    assert.strictEqual(at(badges, h).proven, false, `leadership_score h${h} must be Not yet proven`);
  }
});

// --- (e) FAIL-SAFE: an empty / null / undefined claim list => every horizon "Not yet proven", no link ------
check("an empty / null / undefined claim list leaves every horizon 'Not yet proven' with no link (fail-safe)", () => {
  for (const claims of [[], null, undefined] as (CertifiedClaim[] | null | undefined)[]) {
    const badges = factorHorizonBadges("vcp_contraction", TOP_DECILE, HORIZONS, claims);
    assert.strictEqual(badges.length, HORIZONS.length);
    badges.forEach((b) => {
      assert.strictEqual(b.proven, false);
      assert.strictEqual(b.label, "Not yet proven");
      assert.strictEqual(b.href, null);
      assert.strictEqual(b.claim, null);
    });
  }
});

console.log(`\nfactor-lab-evidence: ${passed} checks passed`);
