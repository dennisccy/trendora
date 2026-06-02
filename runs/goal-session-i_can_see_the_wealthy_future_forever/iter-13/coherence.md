**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-13 (J-30: volatility as a first-class Factor-Lab family)

**Session:** i_can_see_the_wealthy_future_forever
**Iteration:** 13
**Snapshot audited:** `git diff f984a93b3bf0760e978383775e73eb12475c4637` (19 files, +420/−13)
**Auditor:** coherence-auditor

This iteration adds three NEW stored volatility-family factor values (`hv`, `vcp_contraction`,
`downside_vol`) computed once in the scoring/snapshot path and read by the existing read-only Factor
Lab, plus a presentational `<optgroup>` grouping of the config-driven factor dropdown. No new page,
route, endpoint, or nav entry. **No objective Data-Contract or Information-Architecture violation
found.**

---

## Step 1 — Data Contract (the "numbers don't match" gate) — PASS

**New value registered, not duplicated.** The three volatility values are a brand-new canonical value
and ARE registered in the blueprint Data Contract this iteration (new "Per-stock volatility factor
values — J-30" row, blueprint.md:174) — so not even an unregistered-value WARN applies.

**Computed exactly once, single producer.**
- `apps/backend/app/engine/scoring.py:351-356` — `hv`/`vcp_contraction`/`downside_vol` are computed in
  `score_stocks` from `inv_closes` (the as-of bars ≤ D already in hand; no extra round-trip, no
  lookahead) and added to the canonical row dict (scoring.py:372-374). This is the ONE producer.
- `apps/backend/app/engine/scanner.py:112-117` — mirrored verbatim onto new `ScannerResult` columns
  inside the existing `run_scan` transaction (no second scan / no recompute).
- `apps/backend/app/models.py:186-188` — three `Optional[float]` columns; append-only, NULL on short
  history (honestly excluded by the lab, never fabricated).

**Served from the canonical source / read verbatim (no new path).**
- They ride the canonical `GET /api/stocks` + `GET /api/stocks/{ticker}` rows (no new endpoint added —
  `git diff --name-status` shows zero new files under `apps/backend/app/api`).
- `apps/backend/app/engine/research.py` change is **docstring-only** (verified: no new
  `run_scan`/`score_stocks`/`detect_*`/`score_regime`/`forward_return` call). `_extract_factor_value`
  reads the typed column via `getattr` exactly as it reads the score columns — the read-only lab seam
  is intact; `compute_factor_lab` recomputes nothing.

**Not a re-derivation of an existing value** (the one place a duplicate could hide):
- `hv` (stdev of daily returns ×100) is mathematically distinct from the existing `atr_pct` (true-range
  ratio) — same `family: volatility`, different measure.
- `vcp_contraction` (continuous recent-vol/prior-vol ratio via the NEW `indicators.vol_contraction`) is
  **not** the `detect_vcp` pattern flag (`is_vcp`, still produced separately by `detect_vcp` and stored
  on its own column) and **not** `entry_quality.contraction` (which the spec verified is `_neg(atr)`,
  perfectly anti-correlated with `atr_pct`, i.e. not an independent contraction value).
- `downside_vol` (pre-snapshot semivol of trailing returns, MAR=0) is explicitly distinct from
  `research.py:_downside_deviation` (downside deviation of FORWARD returns for the risk-adjusted column).
- The three new `indicators.py` functions are pure/DB-free and re-implement no existing canonical value.

**Critical: the new values do NOT enter any of the six canonical scores** (this is the J-06/J-07
"numbers must match everywhere" invariant). Verified statically:
- `scoring.py` — `_build_score` is **unchanged** (not in the diff; the only `_build_score`/`weights`
  string in the scoring diff is inside the new explanatory comment, not code).
- `config.yaml` — **no** `scores.*.weights` change; the only config.yaml additions are 4 new
  `indicators` windows and 3 new `research.factor_lab.factors` catalog entries.
- `config.py` — `FACTOR_TYPED_COLUMNS` is extended with the three names (the Factor-Lab **source
  allowlist**, not a score weight); `IndicatorsCfg` gains 4 validated positive-int windows.
- Therefore no new code path computes Leadership/Entry Quality/Risk, the A–E bucket, setup status,
  candidate counts, the regime label, or the Risk-Off gate. No "numbers don't match" risk is introduced.
  *(The DB-regen + full-pytest score-invariance regression + browser J-06/J-07 re-verify are the
  dynamic proof and belong to QA/evaluator; the static coherence requirement — no divergent computation
  path — holds.)*

No Part-A violation.

## Step 2 — Information Architecture (the "where do I find it / why is it everywhere" gate) — PASS

- **No new page/route/endpoint/nav entry.** `git diff --name-status` shows no new files under
  `apps/frontend/app` or `apps/backend/app/api`. The only frontend change
  (`apps/frontend/app/research/page.tsx`) is a `<optgroup>` grouping of the existing factor `<select>`,
  derived entirely from the payload (`groupByFamily(data.factors)`) with option values unchanged — no
  hard-coded factor/family list, purely presentational.
- **Lives in its approved home.** The volatility family is additive catalog members on the EXISTING,
  approved `/research` Factor Lab — no duplicate home, no parallel shell.
- **No re-approval owed.** No `blueprint.reapproval-requested` marker was written (verified absent from
  `state/`), which is correct: additive members under an already-approved nav home.
- **Blueprint kept in sync.** blueprint.md updated with the iter-13 nav note (line 80), the skeleton
  `/research` annotation (line 67), and the new Data-Contract row (line 174).
- **J-18 preserved.** No new date/as-of control on `/research`; the lab remains a cross-date aggregate.

No Part-B violation.

## Step 3 — Advisory (non-blocking)

- The `<optgroup>` grouping **improves** coherence: it makes the config-driven catalog's `family`
  axis visible and keeps the frontend free of hard-coded factor knowledge — consistent with the
  "backend is the single source; frontend only re-formats" contract.
- Catalog convention note (not a defect): all four volatility factors carry `direction: lower_better`.
  J-30's own goal is to discover *whether* that textbook direction actually holds in this universe;
  `direction` here is only the catalog's display/sort convention applied to a verbatim-read value (not
  a recomputed result), so it does not violate the read-only/single-source contract. Worth nothing more
  than a mention.

---

## Conclusion

A tightly-scoped, blueprint-conformant iteration. The new values follow the same
computed-once-stored-then-read pattern as the existing score columns, sit behind the canonical
`/api/stocks(/…)` rows, are read verbatim by the unchanged read-only lab seam, and are structurally
walled off from every weighted score — so the iteration introduces no divergent computation path and no
scattered/duplicate surface. The two failure modes this gate exists to catch (divergent copies of a
value; scattered/hidden structure) are both absent.

**Verdict: COHERENCE-PASS** — no objective Step-1 or Step-2 violations; only positive/neutral advisory
notes.
