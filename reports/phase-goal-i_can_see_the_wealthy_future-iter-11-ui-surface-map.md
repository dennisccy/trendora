# Phase goal-i_can_see_the_wealthy_future-iter-11 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future-iter-11
**Date:** 2026-05-31
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/stocks` | VCP filter `Select` (All / VCP only / Non-VCP) | New form control | J-16 adds a VCP filter parallel to Sector/Setup | Select "VCP only" and confirm the row count drops to only flagged names (e.g. STX/TSLA/TSM/ORCL); the `n / total` header updates; switch to "Non-VCP" and confirm those rows disappear and all others remain |
| `/stocks` | Teal "VCP" `Badge` in the Setup cell | New element | Surface the VCP flag on flagged rows alongside setup status | Find a flagged row and confirm a teal "VCP" badge appears next to the setup-status badge; hover it and confirm the tooltip shows the reason + `Pivot $<n>` + invalidation note |
| `/stocks` | VCP-aware empty-state | Changed behavior | Honest empty-state when "VCP only" matches nothing | Apply "VCP only" on a date/filter combo with zero flagged names and confirm the message reads "No VCP-flagged name …" (no fabricated rows) |
| `/stocks` | Filter ranking / Sector + Setup filters | Regression guard | VCP filter must not alter existing filters or sort order | With VCP = All, apply a Sector and a Setup filter and confirm rows narrow exactly as before and ranking order is unchanged |
| `/stocks/[ticker]` | `VcpBadge` in header card | New element | Show VCP flag beside setup status on detail | Open a flagged ticker (e.g. STX) and confirm a teal "VCP" badge sits next to the setup status in the header card |
| `/stocks/[ticker]` | `VcpCard` ("VCP — Volatility Contraction Pattern") | New component | Explain the pattern with pivot + invalidation + contractions | Open STX and confirm the card shows the reason, a "Pivot (breakout level)" value (e.g. `$905.39`), an "Invalidation" sentence (e.g. `$816.98`), and contraction-depth chips |
| `/stocks/[ticker]` | `VcpCard` not-flagged state | New element | No fabricated pattern for non-VCP names | Open a non-flagged ticker and confirm the VCP card shows "No VCP pattern detected." with no pivot/invalidation numbers |
| `/stocks/[ticker]` | VCP values vs `/stocks` row | Regression guard (J-06) | Leaderboard and detail must serve the byte-identical stored row | Compare STX's pivot/invalidation shown on `/stocks` tooltip vs `/stocks/STX` card and confirm they are identical |
| `/system-health` | "Forward return: VCP vs non-VCP" `BreakdownPanel` | New component | J-16 forward-test dimension `by_vcp` | Confirm the panel renders two rows (VCP, non-VCP) each with a mean return and sample size `n` (e.g. VCP +3.18% n=27 ⚠, non-VCP +2.01% n=1191); confirm `n` below `min_sample` shows the ⚠ marker and an empty cohort shows the NA em-dash |
| `/system-health` | Existing by-setup / by-regime / by-bucket / control-group panels | Regression guard (J-09/J-10) | New panel must not disturb existing breakdowns | Confirm all pre-existing breakdown panels still render with their values unchanged |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/patterns.py` (NEW `detect_vcp` + ZigZag helpers) — computes the pattern; surfaced only via the `vcp` block on stock rows (no direct UI).
- `apps/backend/app/engine/scoring.py` — composes `row["vcp"]` onto each row; the data it produces is rendered by the UI but the file itself is backend logic.
- `apps/backend/app/models.py` — append-only `ScannerResult.is_vcp` mirror column — storage only, not directly displayed (the forward-test reads it).
- `apps/backend/app/engine/scanner.py` — populates the `is_vcp` mirror in `run_scan` — persistence only.
- `apps/backend/app/engine/forward_testing.py` — adds the `by_vcp` aggregate consumed by `/system-health`.
- `apps/backend/app/config.py` + `config.yaml` — new typed `patterns.vcp` config block (thresholds); affects detection output, no direct UI surface.
- `apps/backend/app/engine/setups.py` — UNCHANGED (asserted; VCP never enters `ALL_STATUSES`).
- `apps/backend/tests/*` — unit/integration tests; no UI surface.
- `apps/frontend/lib/api.ts` — added `Vcp` type + `vcp` on `StockRow`, `ForwardVcpRow` + `by_vcp` on `SystemHealthResponse`; type-layer only (no rendered surface itself, but enables the surfaces above).

---

## Summary

- **Frontend surfaces changed:** 3 routes (`/stocks`, `/stocks/[ticker]`, `/system-health`)
- **New pages/routes:** 0 (all three are existing IA homes — no nav change, no blueprint reapproval)
- **Modified components:** VCP filter `Select` + VCP badge + empty-state on `/stocks`; `VcpBadge` + `VcpCard` on `/stocks/[ticker]`; `by_vcp` `BreakdownPanel` on `/system-health`
- **Navigation changes:** no
- **Backend-only changes:** 9 (new detector + scoring/model/scanner/forward-test/config edits + unchanged setups.py + tests + api.ts type layer)
