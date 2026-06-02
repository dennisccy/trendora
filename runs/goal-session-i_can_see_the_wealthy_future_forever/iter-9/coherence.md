**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-9 (J-28: more detected patterns beyond VCP)

- **Session:** i_can_see_the_wealthy_future_forever
- **Iteration:** 9 (`goal-i_can_see_the_wealthy_future_forever-iter-9`)
- **Snapshot audited:** `git diff be3530d7ba27f271794b1028a5139159617d4257` (+ working tree)
- **Auditor:** coherence-auditor
- **Result:** No objective Data-Contract or Information-Architecture violations. One trivial, intentional advisory note (below).

This iteration adds two config-driven detected price patterns (`pullback_to_rising_dma`, `flat_base_breakout`) that ride the existing VCP seams, and front-loads the `/research` nav re-approval as a planning action (no `/research` code built). The implementation mirrors the VCP contract precisely.

---

## Part A — Data Contract (the "numbers don't match" gate) → PASS

Both new values are **registered in the Data Contract this iteration** (`blueprint.md:140-141`) with one computing module and the canonical serving endpoints. The build matches the registration exactly.

| Check | Finding | Evidence |
|---|---|---|
| **Computed once (no duplicate computation)** | Each flag is produced by exactly one detector, called once at the single VCP composition site over the same as-of bars (≤ D). No second implementation anywhere. | `scoring.py:332-339` calls `detect_pullback_to_rising_dma(...)` / `detect_flat_base_breakout(...)` beside `detect_vcp`; detectors defined once in `patterns.py:222-421`. |
| **Canonical source only (no non-canonical fetch / client recompute)** | Flags served on `/api/stocks` + `/api/stocks/{ticker}` via `StockRow`; forward cohorts on `/api/system-health` via `by_<name>`. Frontend re-displays server values; never recomputes `flagged`. | `lib/api.ts:190-230,492-494`; `/stocks` filter narrows on server `row.<name>.flagged` (`stocks/page.tsx:143-156`); `/system-health` reads `data.by_<name>` (`system-health/page.tsx:204-214`). |
| **Forward breakdown reads stored mirror verbatim (never re-detect)** | `by_pullback_to_rising_dma` / `by_flat_base_breakout` group on the persisted `is_<name>` boolean via the existing generic `_group_means(..., [True, False], pad=True)` — same path as `by_vcp`. Both cohorts padded; each carries `n`. | `forward_testing.py:557-559` reads `res.is_<name>`; `forward_testing.py:598-609,624-625` build the breakdowns. |
| **Mirror written once (immutable snapshot)** | New indexed boolean columns written once in the single `ScannerResult(...)` from `row["<name>"]["flagged"]` — same design as `is_vcp`; append-only column additions, no row UPDATE. | `models.py:172-173`; `scanner.py:108-113`. |
| **Re-format only (not a violation)** | Badges/tooltips/cards/panels re-format the server `reason`/`pivot`/`invalidation` verbatim; glossary thresholds resolve live from config via `ref:` paths (no retyped numbers). | `stocks/page.tsx` `patternTitle`; `stocks/[ticker]/page.tsx` `PatternCard`; `config.yaml` catalog rows all `ref: patterns.<name>.*`. |
| **New value vs existing concept** | Both are genuinely new **detected-pattern flags**, not synonyms or re-derivations of any registered score/return/bucket. Pattern-not-status (invariant #6) holds: detectors are pure and never touch `setup`; `score_stocks` attaches them as separate row keys. | `patterns.py` detectors return a flag dict only; `scoring.py:356-357` attach `row["pullback_to_rising_dma"]` / `row["flat_base_breakout"]` alongside (not into) `setup`. |

No duplicate computation, no non-canonical source, no unregistered value. **Part A: no violations.**

## Part B — Information Architecture (the "where do I find it / why is it everywhere" gate) → PASS

| Check | Finding |
|---|---|
| **New routes/pages** | None. The four touched surfaces — `/stocks`, `/stocks/[ticker]`, `/methodology`, `/system-health` — are all existing sidebar homes already in the blueprint IA. (ui-surface-map confirms: 0 new pages/routes, navigation changes: no.) |
| **Reachability** | Unchanged; all four homes are ≤2 clicks from the persistent sidebar as before. |
| **Duplicate home** | None. The new patterns extend the existing VCP homes (leaderboard filter, detail badges/cards, glossary, System Health breakdown) — no second page for any entity. |
| **Parallel shell** | None. `sidebar.tsx` / layout unchanged this iteration (confirmed not in the diff). |
| **`/research` skeleton entry** | Added to the blueprint nav-skeleton as **`⛔ PLANNED iter-10+`** only (`blueprint.md:67`). It is **not** wired into the live sidebar and there is **no `/research` route, page, or endpoint** anywhere in `apps/` (verified: no `research` dir under `apps/frontend/app/`, no `research.py` under the backend api). The front-loaded `blueprint.reapproval-requested` marker is written to pause iter-10's pre-decomposer. This is a planning/approval action — correctly avoiding a live nav link to an unbuilt 404. |

**Part B: no violations.** (Correctly, the `/research` planning entry is documentation-only — wiring a live sidebar link to an unbuilt route would itself have been an IA violation, and it was avoided.)

## Part C — Advisory (non-blocking)

- **Minor per-surface label variation for the same pattern** (intentional, not drift): the badge label is short (`Pullback`, `Flat base`), the System Health cohort label is medium (`Pullback-to-DMA`, `Flat-base`), and the glossary/detail name is descriptive (`Pullback to a rising DMA`, `Flat-base breakout`). All are clearly the same entity and the abbreviations fit each surface's space; this matches the existing VCP precedent (`VCP` badge vs `VCP`/`non-VCP` cohort). No action required — noted only for awareness.

---

## Conclusion

The iteration is exemplary on coherence: it reuses the VCP single-source seam end to end (one detector → composed once in `score_stocks` → mirrored once in `scanner.py` → read verbatim by the generic `_group_means` and the frontend), registers both new values in the Data Contract, keeps detected-patterns-are-not-statuses intact, adds no new surfaces, and treats the `/research` nav addition as a pure front-loaded approval with zero `/research` code. No objective Data-Contract or Information-Architecture rule is violated.

**Verdict: COHERENCE-PASS** — does not block GOAL_ACHIEVED.
