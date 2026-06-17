**Verdict:** COHERENCE-PASS

## Coherence Audit — iter-28 (J-86 colour-grading finish)

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration:** 28
**Depth:** lean (frontend-only)
**Snapshot SHA:** 2297b9a4fc6f58845dd1d0170ec3ebf8074da89d

---

### Changed files (from `git diff 2297b9a4fc6f58845dd1d0170ec3ebf8074da89d`)

| File | Role |
|---|---|
| `apps/frontend/components/forward-return.tsx` | Delegate `mddClass` to new shared helper |
| `apps/frontend/lib/mdd-color.ts` | New shared module — magnitude-graded colour map (untracked, not yet committed) |
| `apps/frontend/lib/mdd-color.test.ts` | Unit tests for the above (untracked) |
| `docs/handoffs/goal-...-iter-28-dev.md` | Dev handoff (untracked, non-product artifact) |

No backend file changed. `git diff --stat HEAD -- apps/backend` = 0 lines.

---

### Step 1 — Data Contract check

**Registered canonical value:** "Max-drawdown per (run, symbol, horizon)" — computed once by `forward_testing` INSERT path; served verbatim on `GET /api/stocks`, `GET /api/stocks/{ticker}`, `GET /api/themes`, `GET /api/sectors`, and the Backtest/Research aggregates.

**Findings:**

1. `apps/frontend/lib/mdd-color.ts` — the new `mddColorClass` function receives a pre-served `number | null | undefined` value (the already-fetched `forward_returns.max_drawdown`) and maps it to a Tailwind class. It performs NO computation of a drawdown figure: no arithmetic, no fetch, no `useState`, no `useEffect`. It is a pure presentation formatter — the same category as `fmtMdd` and `returnClass` that were already present. This is explicitly permitted: "a value that is read from its canonical endpoint and merely re-formatted for display is not a violation."

2. All four consumer pages (`/stocks/page.tsx`, `/stocks/[ticker]/page.tsx`, `/themes/page.tsx`, `/sectors/page.tsx`) and `evidence-panels.tsx` continue to call `mddClass` from `@/components/forward-return`, which now delegates to `mddColorClass`. The serving endpoint for the underlying figure is unchanged in every case. No new endpoint was introduced. No alternative computation path exists.

3. No new displayed value was introduced. The same already-registered `max_drawdown` field is now colour-graded rather than flat-red — a re-format, not a new value.

**Data Contract verdict: no violation.**

---

### Step 2 — Information Architecture check

**New pages/routes introduced:** none. The diff contains no new route files, no new `app/` directories, no new sidebar links, no new nav components.

**Surfaces modified in place:** `forward-return.tsx` (shared component), `lib/mdd-color.ts` (new utility module — not a page or route). All four consumer surfaces (`/stocks`, `/stocks/[ticker]`, `/themes`, `/sectors`) already exist and are already registered in the blueprint IA with nav links reachable in ≤2 clicks.

**IA verdict: no violation.**

---

### Step 3 — Advisory observations

None. This is a minimal single-module delegation refactor. The colour scale uses `color-mix(in_srgb, var(--neg) N%, var(--text-muted))` exclusively — no new hex literals, fully consistent with the design-token discipline (anti-goal 10). The single-source-of-truth property is strengthened: the graded colour previously lived inline in `forward-return.tsx`; it now lives in one place (`lib/mdd-color.ts`) referenced by the shared `mddClass` wrapper that all four surfaces already import.

The advisory WARN from iter-27 (three local `MaxDrawdownCell` wrappers using `"NA"` text vs the shared `"—"` em dash) is explicitly deferred in the iter-28 spec and remains a WARN; it is not reproduced here as it was already noted in the prior audit.

---

### Summary

| Rule | Result |
|---|---|
| Part A — Duplicate computation of `max_drawdown` | PASS — no second computation anywhere in the diff |
| Part A — Non-canonical source for `max_drawdown` | PASS — all surfaces fetch from unchanged canonical endpoints |
| Part A — New unregistered value | PASS — no new value introduced |
| Part B — No navigation path for new route | PASS — no new route introduced |
| Part B — Duplicate home | PASS — no new page |
| Part B — Parallel shell | PASS — no new shell |
| Anti-goal 10 (no hardcoded hex) | PASS — `color-mix` over `var(--neg)` / `var(--text-muted)` only |
| Backend-diff empty | PASS — 0 lines |
