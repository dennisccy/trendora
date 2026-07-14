# goal-mcp-loop-iter-33 — Implementation Summary

**Phase:** goal-mcp-loop-iter-33
**Date:** 2026-07-14
**Written by:** developer

---

## Features Implemented

- **Daily preflight verdict banner**: every page in the product (Dashboard, Stocks, a stock's detail
  page, Watchlist, Evidence, Research, and every other page) now shows one small strip near the top
  telling the user, at a glance, whether today's board is safe to rely on. On a healthy day it reads a
  quiet "GO — today's board is current." When something is wrong, it becomes an unmissable colored banner
  that names the concrete problem in plain English — for example, "Latest data is 6 trading days old,
  exceeding the configured maximum." A serious problem (e.g. the underlying data files cannot be found or
  read) shows in red with the exact wording "do not rely on today's board," so it can never be missed or
  mistaken for a minor warning.
- **One shared answer, everywhere**: the verdict is computed once, in one place, and every page simply
  displays that same answer — there is no risk of one page saying "fine" while another quietly disagrees.
- **A record of when things changed**: whenever the verdict actually changes (for example, from "all
  good" to "something's wrong"), that change is written to a small log file, so there is a paper trail of
  when trust in the board went up or down. Routine checks that find nothing new do not clutter this log.

## Changed Behavior

- **`GET /api/health` (the backend's status check used by every page)**: previously reported only whether
  the backend was up and how "warmed up" its data was. It now ALSO reports the new overall verdict
  (GO/DEGRADED/NO-GO) and the reasons behind it, in the same response. Nothing that was there before was
  removed or changed — this is a pure addition.
- **Every page's layout**: gained one new, thin status strip near the top of the screen. On a healthy day
  it is easy to miss (by design); when something needs attention it becomes hard to miss (also by design).

## Backend-Only Items

None — the new verdict is both computed on the backend and immediately visible on every page.

## Incomplete Items

None from this iteration's scope. Three future enrichments named in the underlying spec (an anomaly
detector, a "did live data quietly drift from what we validated" monitor, and a "time machine" replay
check) were explicitly out of scope for this iteration and are left as clearly labeled hooks for a future
iteration to plug into the same banner — they do not need to be built for today's verdict to be honest and
useful with the inputs that already exist (is the backend serving data, is that data current, are the
underlying record-keeping files intact).

## Config and Environment Changes

- `config.yaml` — new `readiness:` section:
  - `freshness_max_age_days` (default `5`) — how many trading days old the latest data may be before it
    counts as stale. Because the product currently runs against a fixed, offline snapshot rather than a
    live daily feed, this normally always reads "0 days old" and stays green — the setting exists for
    when live daily updates are wired in, and as a deliberate testing lever (see below).
  - `severity` — which of the three checks (is the backend serving data / is the data fresh / are the
    record-keeping files intact) count as a "serious" problem (shown in red, "do not rely on today's
    board") versus a "caution" problem (shown in amber). This is an operator-tunable setting, not a code
    change, so the threshold for "how worried should we be" can be adjusted without a new release.
  - `verdict_history_path` — where the change-log file above is written.
- No new required environment variables for normal operation. Two optional environment-variable
  overrides were added for testing/automation purposes only (mirroring how similar settings already work
  elsewhere in the product): one to point the change-log at an alternate file, and the existing
  general-purpose config-file override can be used to test the "something's wrong" banner states without
  touching the real, committed data.

## Known Limitations

- The "how stale is the data" check is measured against the data's own most recent date, not the
  calendar's "today" — this is intentional (the product runs deterministically against a fixed,
  committed dataset, so there is no meaningful "real time" to compare against yet), and it is documented
  plainly in the code so a future engineer wiring in live daily updates has a clear, marked spot to
  connect a real clock-based comparison.
- Three enrichments named in the design spec (see "Incomplete Items" above) are intentionally not part of
  this iteration; the banner already gives an honest, useful answer without them and is built so adding
  each one later is a small, additive change rather than a rework.
- This developer's own testing used the fast local dev startup script rather than the slower
  production-style startup; the pipeline's next, more thorough browser-based check (using the
  production-style startup) still needs to run before this feature is considered fully signed off — a
  normal, expected next step, not a gap in what was built.
