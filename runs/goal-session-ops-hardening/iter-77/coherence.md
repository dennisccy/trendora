# Iteration 77 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-77
**Date:** 2026-08-13
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `stale_for_s` (Backend readiness / boot phase + preflight verdict row, blueprint.md:436) | OK | Registered iter-71 as computed by `compute_readiness`/`compute_preflight`, served by `GET /api/health`. This iteration's frontend reads it from the SAME single poll: `apps/frontend/components/readiness-provider.tsx:92` (`setStaleForS(data.stale_for_s)`, inside the existing `GET /api/health` fetch, no second fetch added) and formats it with a pure re-formatter, `apps/frontend/lib/staleness-annotation.ts:12` (`formatStaleAnnotation`), consumed by `health-badge.tsx:113` and `preflight-banner.tsx:22`. No new computation, no client-side derivation of a number the server didn't already send (the formatter only rounds/labels), no second endpoint. This is the textbook "re-format is fine" case (skill Part A rule 3) — first UI consumer of an already-registered field. |
| `scorecard.by_horizon[]` (Backend readiness row is separate; this value is covered under the same J-07/J-08 IA row, `GET /api/backtest`) | OK | `apps/frontend/app/backtest/page.tsx:619` adds `data-testid="scorecard-row-${row.horizon}d"` to the existing table row rendering the already-fetched `row` object — a test hook on an already-displayed value, no new fetch, no recomputation. Matches the spec's "Data-contract additions: None new" claim. |

No new displayed value/entity was introduced this iteration (confirmed against the diff: only `stale_for_s` — already registered — gained a UI consumer, and a `data-testid` was added to an already-registered value). No duplicate-computation or non-canonical-source pattern found anywhere in the diff.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Global readiness badge + preflight banner (staleness annotation, layout fix) | OK | Not a nav item per blueprint.md:386-388 ("a global top-bar readiness badge is present on every page (not a nav item)"); confirmed unchanged in `apps/frontend/components/sidebar.tsx` (no diff to that file this iteration) and in `apps/frontend/app/layout.tsx`, where the badge/banner remain mounted in the SAME root shell — only `header`'s `h-14`→`min-h-14 py-2` and the badge row's `flex`→`flex flex-wrap` classes changed (`app/layout.tsx:38,42`). No parallel shell introduced. |
| `/backtest` scorecard rows (testid only) | OK | No visible change, no route change; `/backtest` already has its home in blueprint.md:421 under "Backtest" nav section. |

No new page, route, or nav entry was added this iteration (confirmed: `git diff --stat` shows zero new files under `apps/frontend/app/**` and no diff to `sidebar.tsx`/router config; the only two new files, `apps/frontend/lib/staleness-annotation.ts` and its test, are a non-rendering pure-function module, not a surface). This matches the iter spec's own "Blueprint conformance" and "UI surface changes" fields.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `incredible_auto_dev/scripts/start-frontend.sh` and `incredible_auto_dev/scripts/automation/lib/demo_runner.py` are hardlinked, byte-identical copies of `scripts/start-frontend.sh` / `scripts/automation/lib/demo_runner.py` (confirmed via `stat -c %i`, same inode; `incredible_auto_dev/` is the vendored framework subtree per prior "chore(framework): pull vendored incredible_auto_dev..." commits). This is framework tooling, not a product data value or UI surface, so it is out of this gate's scope — noted only so a future auditor doesn't mistake the two paths in `git diff --stat` for a duplicated implementation.
- `runs/goal-session-ops-hardening/journey-scripts/J-06.json` and `J-08.json` were re-serialized with pretty-printed indentation as a side effect of this iteration's note appends (their J-07 sibling shows the same reformatting). Cosmetic only — the `_notes` content and `steps` arrays are otherwise unchanged/append-only; not a coherence concern.
- No unregistered-but-new value was introduced, so Part A5 does not apply this iteration.

---

## Summary

This iteration is a clean, additive UI-consumer pass over an already-registered Data Contract value (`stale_for_s`, registered iter-71) plus a layout fix and a test-hook addition, exactly as the iter spec's "Blueprint conformance" and "Data-contract additions: None new" fields claimed. The bulk of the diff (`start-frontend.sh`'s build lock, `next.config.mjs`'s build guard, `demo_runner.py`'s settle-for-capture fix) is launch-script/tooling reliability work with no Data Contract or Information Architecture surface at all. No FAIL-class violation found in either Part A or Part B.
