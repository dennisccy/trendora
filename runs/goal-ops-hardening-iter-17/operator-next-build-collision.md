# Operator note — shared `.next` build collision from two concurrent dev servers (2026-07-24)

**Written by:** the goal-mode operator (pump), against myself. The iter-17 browser-QA agent diagnosed
this precisely rather than just reporting "page broken", and its finding is the reason iter-17's
browser verdict reads FAIL. That deserves a durable record separate from the iteration artifacts.

## What I did wrong

To close the long-standing `not_yet_computed` evidence gap I booted a **second** Next dev server
(the TC-9 throwaway, port 13255, pointed at the throwaway backend on :18255) — launched from the
**same working directory** as the main one (`apps/frontend`). Next's dev server writes its compiled
output to `.next` relative to that cwd, so both processes shared one build directory.

Consequence: `NEXT_PUBLIC_API_URL` is inlined into client chunks at compile time. Whichever server
compiled a route last overwrote the other's chunks on disk. The main app at `:3255` therefore began
serving a client bundle whose health poll called **`http://localhost:18255`** — the throwaway
backend — producing a permanent "Backend unavailable" / "NO-GO" state on a perfectly healthy main
backend. A second manifestation: `/data`'s route chunk went missing entirely (`ChunkLoadError`,
confirmed 404 on the chunk file).

The repo already keeps `.next-iter25`, `.next-alt-qa`, `.next-verify` on disk — prior sessions hit
this and solved it with isolated build directories. I did not look before launching.

## How the browser agent handled it (correctly)

It did not silently work around the failure or fabricate a pass:
- Instrumented `window.fetch` in-page to capture the actual outgoing URL, proving the `:18255` call
  from a `:3255`-loaded page rather than inferring it.
- Confirmed via `git diff` that every file involved (`readiness-provider.tsx`, `health-badge.tsx`,
  `preflight-banner.tsx`, `lib/api.ts`, `app/data/page.tsx`) is untouched this iteration — i.e. an
  environment defect, not a product regression.
- Recorded UT-01 as a genuine **FAIL** in its literal unpatched form, then used a clearly-labelled
  diagnostic redirect to complete the remaining cases, and said so explicitly.
- Named the fix it needed from the operator instead of attempting service control it is not allowed
  to perform.

## The correction

Killed every `next dev` / `next-server` process (the first `pkill` pattern missed the surviving
`next-server` pid 1188846 — it had to be killed by explicit PID), removed `apps/frontend/.next`
entirely, and relaunched the main frontend alone via `scripts/start-frontend.sh`.

Verified after the clean rebuild:
- `grep -rlo 'localhost:18255' apps/frontend/.next` → **no matches** (was matching `app/layout.js`,
  `app/page.js`, `app/backtest/page.js` before).
- `http://127.0.0.1:3255/` → 200, `http://127.0.0.1:3255/backtest` → 200.
- The live `next-server`'s own environment carries the correct `NEXT_PUBLIC_API_URL=http://localhost:8255`.

The throwaway **backend** (:18255) is left running for the record; its frontend is stopped.

## What the evidence is still worth

Both gaps this lane existed to close were genuinely closed, and neither depends on the broken chunks:
- **`not_yet_computed` captured in a browser for the first time** (UT-02/UT-06, against the throwaway
  pair on its own port) — `TC-09-not-yet-computed-state.png`.
- **The corrected "Refreshing" banner copy + the new `evidence_asof` label captured live** (UT-03) —
  `TC-07-refreshing-banner-with-asof.png` — reached via a same-`asof_key` stale-version window, which
  does not require an as-of boundary crossing.

## Lesson for future operator turns

Never run two Next dev servers from the same cwd. If a second instance is needed, give it an isolated
build directory (the repo's existing `.next-alt-qa` / `.next-verify` convention) — e.g. a distinct
`distDir` via config or a separate checkout — and tear it down as soon as its evidence is captured.
Related lesson from earlier this same iteration: `runs/goal-ops-hardening-iter-17/operator-tc9-ag10-correction.md`.
