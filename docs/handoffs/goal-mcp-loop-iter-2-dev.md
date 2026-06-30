# goal-mcp-loop-iter-2 Dev Handoff

**Phase:** goal-mcp-loop-iter-2
**Date:** 2026-06-30
**Agent:** developer
**Status:** complete

## What Was Built

This iteration lights the session's **first referee-certified "Proven" badge** end-to-end and adds the
**J-02 proof drill-down**. The post-decompose gate had already certified the Evidence Claim (top decile of
`leadership_score`, horizon 20, vs SPY) and appended the first entry to
`runs/goal-session-mcp-loop/state/certified-claims.jsonl` **before** this build — so the read path already
returns `proven_signals["leadership_score"].proven == true` with zero backend computation changes. The new
work makes that proof **auditable from the UI**.

- **J-02 proof drill-down on `/stocks/{ticker}` (PRIMARY, new code).** A new `ScoreProofPanel` client
  component renders, only when a score is **Proven**, a collapsed-by-default **"Why proven?"** disclosure
  that expands in place to show, read **verbatim** from the already-fetched `proven_signals[signal]` map:
  - the **out-of-sample test** — verdict status (`PASS`), holdout edge (`+6.36%`), p-value (`0.0004998`),
    and the sealed-holdout cohort size (`12,297`);
  - the **control comparison vs SPY** — the cohort's excess over the benchmark control (`+6.36%`), labeled
    "vs SPY (benchmark control)";
  - the **certified-claim id + registration date** — `leadership_score · registered 2026-06-30`, with a
    link to the backing ledger row at `/evidence#signal-leadership_score`.
  When the score is **not** proven the panel renders **nothing** (fail-safe — no empty panel). It is on the
  stock-detail score card only, never on the leaderboard.
- **Shared evidence helpers (`lib/evidence.ts`).** Added the pure, unit-tested `proofFieldsFor()` extractor
  (reads the backing claim verbatim, returns `null` for any unproven signal) plus two display formatters,
  `formatEvidencePct()` and `formatPValue()`. De-duped the `SCORE_SIGNALS` map into this one module (it was
  copied identically in both stocks pages) — clears a known coherence WARN.
- **Backend read-side `signal = factor` derivation (`app.engine.evidence`, optional/recommended hardening).**
  `_resolve_signal()` now derives the UI signal for a PASS entry that omitted an explicit `signal` **only**
  when its cohort is a score-column factor (`leadership_score` / `entry_quality_score` / `risk_score`, whose
  factor key is byte-identical to the UI signal key). This is display-routing only and non-spoofable;
  proven-ness still flows 100% from `verdict.status == "PASS"`. Defense-in-depth so a future score-column
  claim that forgets the field does not silently go dark (directly addresses the iter-1 lesson). No new
  computation, no new value, no new endpoint.

## Files Changed

- `apps/frontend/components/score-proof-panel.tsx` (new) -- the J-02 "Why proven?" disclosure; reads
  `proofFieldsFor` verbatim, renders nothing for an unproven signal.
- `apps/frontend/app/stocks/[ticker]/page.tsx` -- render `ScoreProofPanel` below the `EvidenceStatusBadge`
  in `ScoreCard`; import the shared `SCORE_SIGNALS` (removed the local copy).
- `apps/frontend/app/stocks/page.tsx` -- import the shared `SCORE_SIGNALS` (removed the local copy). No
  behavior change.
- `apps/frontend/lib/evidence.ts` -- added `SCORE_SIGNALS`, `ProofFields`, `proofFieldsFor`,
  `formatEvidencePct`, `formatPValue` (all pure / read-only).
- `apps/frontend/lib/evidence.test.ts` -- extended: proof-field verbatim read + fail-safe (null for an
  unproven signal), exact formatter strings, and the shared `SCORE_SIGNALS` map.
- `apps/backend/app/engine/evidence.py` -- added `_SCORE_COLUMN_FACTORS` + `_resolve_signal`; `_claim_row`
  now resolves `signal` via it. Updated the module docstring.
- `apps/backend/tests/test_evidence.py` -- split the old "signal-less PASS stays dark" test into a
  score-column-derives case and a non-score-stays-dark case, and added a test that a non-PASS score-column
  entry is never proven even though its signal derives. Strengthened the proven-fields assertion (p_value).

## Tests Run

- **Frontend unit (`lib/evidence.test.ts`)** — no JS test runner is installed in this frontend; the repo
  convention is `node lib/<name>.test.ts` (Node type-stripping). This machine's Node build lacks built-in
  TS stripping (`ERR_NO_TYPESCRIPT`) and `tsx` is not installed, so I transpiled with the repo's local
  TypeScript 5.7 and ran the emitted JS:
  ```
  cd apps/frontend
  node_modules/.bin/tsc lib/evidence.ts lib/evidence.test.ts --outDir <tmp> \
    --module nodenext --moduleResolution nodenext --target es2022 \
    --rewriteRelativeImportExtensions --skipLibCheck --strict
  node <tmp>/evidence.test.js
  ```
  Result: **10 passed** (5 pre-existing + 5 new).
- **Frontend typecheck:** `cd apps/frontend && node_modules/.bin/tsc --noEmit -p tsconfig.json` — **clean
  (exit 0)**, both before and after the change.
- **Frontend production build:** `cd apps/frontend && node_modules/.bin/next build` — **succeeded (exit 0)**;
  compiled `/stocks` (7.58 kB), `/stocks/[ticker]` (8.77 kB), and `/evidence` (3.5 kB) without errors.
- **Backend evidence resolver units:** `cd apps/backend && .venv/bin/python -m pytest tests/test_evidence.py -v`
  — **9 passed**.
- **Backend `/api/evidence` route regression:** `.venv/bin/python -m pytest tests/test_api_evidence.py -q`
  — **3 passed** (boots the FastAPI app via TestClient, so app startup with the change is verified).
- **Real-ledger end-to-end read:** `build_evidence_payload(resolve_ledger_path())` over the committed
  `certified-claims.jsonl` returns `proven_signals` keys `["leadership_score"]` with
  `status=PASS, holdout_edge=0.06359100763913017, p_value=0.0004997501249375312,
  control_excess=0.06359100763913017, register_date=2026-06-30, cohort_n=12297`; `entry_quality_score` and
  `risk_score` are **absent** (honestly "Not yet proven").

## Known Issues

- **`/api/stocks` regression check (no regression — proven by isolation, not by running the slow suite).**
  My only backend change is in `app/engine/evidence.py`, whose single real importer is `app/api/evidence.py`
  (the only other reference, in `app/config.py:1900`, is a docstring comment). The stocks route does **not**
  import the evidence module, so `/api/stocks` cannot regress from this change. The full
  `tests/test_api_engine.py` suite boots the entire engine/seed (~2.5 min/run); its result at handoff time
  is recorded below.
- **`next build`** passed cleanly (above), and `tsc --noEmit` is green — the new client component compiles
  for production with no errors or warnings on the affected routes.
- **Frontend test execution is environment-sensitive.** The `node lib/*.test.ts` convention assumes a Node
  built with TypeScript stripping (or `tsx`); neither is present here. The transpile-and-run command above is
  the working invocation on this machine. The QA lane should use it (or a Node ≥22.18 built with Amaro).
- **Honesty boundary on controls (by design).** The proof panel shows the **single SPY benchmark control**
  the referee actually computed, labeled "vs SPY". The broader control menu in goal.md (QQQ / sector ETF /
  random same-sector) is a future controls-enrichment iteration — showing uncomputed controls would violate
  the displayed-numbers-are-correct anti-goal.
- **p-value / edge display formatting.** The panel renders the p-value to 4 significant figures
  (`0.0004998`, matching the referee's own `verdict.reason` formatting) and the edge/control as a signed
  percent (`+6.36%`, matching the `/evidence` claim-row representation). These are re-formats of the exact
  served float — nothing is recomputed.
