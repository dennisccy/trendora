# goal-mcp-loop-iter-1 Frontend Handoff

**Phase:** goal-mcp-loop-iter-1
**Date:** 2026-06-29
**Agent:** developer
**Status:** complete

## What Was Built (UI)

Every score the user sees on **`/stocks`** and **stock-detail** now carries a visible, honest **evidence
status**, and a new nav-reachable **Evidence** ledger page renders the certified-claims ledger. Against
today's empty ledger every status reads **"Not yet proven"** — establishing the evidence-first frame end to
end without presenting any confident, proven number.

- **`EvidenceStatusBadge`** (`components/evidence-status-badge.tsx`) — a calm, unmissable status chip built
  on the local `Badge`:
  - "Not yet proven" → muted `default` variant + `Shield` icon (fail-safe default; non-interactive).
  - "Proven" → quiet `accent` variant + `ShieldCheck` icon, wrapped in a `Link` to `/evidence#signal-<key>`
    with hover/focus/active states (`hover:bg-surface active:bg-bg`, `focus-visible:ring-accent`).
  - Palette tokens ONLY (no invented hex, no hype green/glow). Carries `data-testid="evidence-badge"` +
    `data-proven` for browser QA.
- **Stocks leaderboard** (`app/stocks/page.tsx`) — fetches `/api/evidence` ONCE on mount (non-blocking,
  config-global), defaulting `provenSignals` to `{}` (fail-safe). A badge renders BELOW each of the three
  ScoreBadges (Leadership / Entry Quality / Risk) on every row. A fetch failure leaves all badges
  "Not yet proven"; the leaderboard is never broken.
- **Stock detail** (`app/stocks/[ticker]/page.tsx`) — same one-shot non-blocking fetch in `StockDetailBody`;
  a badge renders inside each of the three `ScoreCard`s, below the numeric score.
- **`/evidence` page** (`app/evidence/page.tsx`) — page header + loading skeleton + "Backend unavailable"
  error state + honest empty state ("No certified claims yet — every signal currently reads Not yet proven")
  that enumerates the five claim-row fields (Hypothesis / Out-of-sample verdict / Control comparison (vs SPY)
  / Registration date / Forward-walk score-to-date). The real `ClaimRow` renders each served claim verbatim
  with an `id="signal-<key>"` anchor and a "Backs: Stocks leaderboard →" linkback.
- **Sidebar** (`components/sidebar.tsx`) — one new entry, **Evidence** `/evidence` (`ShieldCheck`), inserted
  after Research — reachable in ≤2 clicks, implementing the already-approved blueprint IA's Evidence section.
- **API client** (`lib/api.ts`) — `fetchEvidence()` + the distinct types `EvidenceLedgerResponse` /
  `CertifiedClaim` / `ProvenSignal` (re-exported from `lib/evidence.ts`; NOT the Backtest `EvidenceAggregate`).
- **Pure logic** (`lib/evidence.ts`) — the badge's proven/not-proven decision (`resolveEvidenceStatus`,
  `evidenceAnchor`, label constants) lives in a dependency-free module so it is `node`-unit-testable and the
  UI never computes proven-ness in a component.

## States Handled

- **Loading:** leaderboard/detail badges default to "Not yet proven" while evidence loads (never block the
  page); `/evidence` shows a skeleton.
- **Empty:** every badge "Not yet proven"; `/evidence` shows the honest no-claims empty state.
- **Error:** an evidence-fetch failure ⇒ badges fall back to "Not yet proven" and the leaderboard/detail are
  unaffected (never a crash/500); `/evidence` renders a styled "Backend unavailable" alert.

## Design System Conformance

- Reused `components/ui/Badge` (chip) and `components/ui/Card` (claim rows), `PageHeading`, `lucide` icons
  (`ShieldCheck` / `Shield`) — consistent with prior surfaces.
- Color/spacing/typography use ONLY existing tokens (`text-text-muted`, `text-text-faint`, `border`,
  `accent`, `bg-surface-2`, etc.). The badge is additive — it never displaces the existing `ScoreBadge`.
- Calm, evidence-first per goal.md Design Direction — "Not yet proven" is muted; "Proven" is a quiet accent
  with a link. No new visual effects invented.

## Tests Run (frontend)

- `node lib/evidence.test.ts` (repo convention) — 5 resolver checks. This sandbox's `node` lacks native TS
  support, so I verified the identical test via the repo's `tsc` transpile+run: **5 passed**. Runs as written
  in the QA env (TS-enabled `node`, like every existing `lib/*.test.ts`).
- `./node_modules/.bin/tsc --noEmit` → **clean (exit 0)**.
- `./node_modules/.bin/next build` → **success (exit 0)**; `/evidence` (3.5 kB), `/stocks` (9.56 kB),
  `/stocks/[ticker]` (7.5 kB) compiled; 25/25 routes generated.

## Known Issues

- Against the empty ledger the "Proven" code paths (badge link + claim rows + linkback) are present and
  unit-tested but not visible until ≥1 claim is certified (J-02/J-04). The `/evidence` empty state
  intentionally enumerates the claim-row fields so the layout is verifiable in the markup today.
- The frontend signal keys (`leadership_score` / `entry_quality_score` / `risk_score`) are the canonical
  factor-catalog keys; they will light up once the ledger writer stamps `claim.signal` in a later certified
  iteration (backend-side, out of scope here).
