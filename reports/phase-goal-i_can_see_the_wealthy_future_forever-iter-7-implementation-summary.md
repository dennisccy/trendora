# Goal Iteration 7 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-7
**Date:** 2026-06-02
**Written by:** developer

> **J-22 — Transparent, rule-based, expanded universe (~500 names).** The goal was to replace the
> hand-curated 122-name stock universe with a transparent, reproducible, config-recorded **screen**
> over a documented candidate pool of real US index memberships, surfaced in the UI.

---

## ⛔ Status at a glance: BLOCKED on an external data provider (capability NOT delivered)

**Plain-language bottom line:** Iteration 7 could **not** be completed because the one external thing it
depends on — fetching real daily price history (and market cap) for ~300 new company names from a free,
no-key data source — is **unavailable from this machine right now**. Every free source we can reach is
either rate-limiting us or now requires a paid/captcha key. We deliberately did **not** invent fake prices
to force the feature through (that is a hard project rule). So:

- The **stock universe is still the prior 122 names** — it was **not** expanded to ~500.
- The new **"Universe Selection" screen card does NOT appear** in the app yet (by design — see below).
- All the **plumbing** to do the expansion is built, tested, and committed; it just needs the data feed
  to come back so the one-shot build step can run.

This is an **environmental stall**, not a coding bug. It needs the data feed (or an equivalent free source)
to recover before the feature can finish. Recommended next step: **escalate / wait for provider recovery**,
then run the short finish runbook below — **do not** simply re-run the build blindly; it will keep failing
until the feed recovers.

> **Re-confirmed in fix cycle 3 (2026-06-02):** a fresh single-shot probe still returned **HTTP 429** on both
> Yahoo hosts and the market-cap (crumb) endpoint, so the blocker is unchanged. No code change was needed or
> made this cycle (the review's only actionable item is to escalate); the infrastructure tests remain green
> (38 passed, 3 skipped). No data was fabricated.

---

## What actually shipped this iteration

- **The full universe-screen toolchain (built + tested, but inert until the data feed returns):**
  - A documented, reproducible **candidate pool** is committed — `apps/backend/data/seed/universe_pool.csv`
    (548 names: the real S&P 500 + Nasdaq-100 index members, pulled from Wikipedia, plus Trendora's prior
    names). This is a transparent index listing, not a hand-picked code list. *(This step succeeded —
    Wikipedia is reachable.)*
  - A one-shot **screen + ingest** script (`screen_universe.py --screen`) that would fetch real price
    history + market cap for each candidate, apply the three config filters (min market cap / min average
    daily dollar-volume / min price), keep only the passers, and **log + omit** anything that fails or
    can't be fetched — never fabricating. *(Built + unit-tested; could not run — no reachable price feed.)*
  - A config-rewrite script (`apply_universe_to_config.py`) that turns the screen result into the new
    `config.yaml` universe. *(Built + validated on a config copy.)*
- **An honest "no fake screen" safeguard (NEW this fix cycle):** the app will only show the "Universe
  Selection — Screen" card once a **real screen has actually run**. Until then the card stays hidden, so
  the product never claims the current 122 names came from a screen when they did not. The moment the real
  screen runs, the card appears automatically with the real numbers. *(Built + tested + active now.)*
- **Supporting wiring (built + tested, dormant until the screen runs):** stored reference market cap on
  each stock (read from the committed screen record), and a "Universe size" figure on the Data page that
  reads the same single source the methodology card uses.

---

## Changed Behavior (what an operator/user would actually notice today)

- **Stock universe size: unchanged — still 122 names.** The intended growth to ~500 did **not** happen
  (the screen could not run). Every leaderboard / score / forward-test therefore still runs over the same
  122 names as before iteration 7.
- **`/methodology`:** unchanged for users today — the new "Universe Selection" card is intentionally
  hidden until a real screen runs (so nothing false is shown). The existing setup/pattern glossary is
  unaffected.
- **`/data`:** shows a "Universe" figure of 122 (the real current universe size). Honest, just not grown.
- Breadth / new-high-low remain **universe-relative**; walk-forward evidence remains
  **survivorship-biased** — honest-limitation labels unchanged.

---

## Backend-Only Items

- `Stock.market_cap` — populated read-only from the committed screen record when it exists; currently
  empty/NA because the screen has not run. Not surfaced per-stock in the UI this iteration regardless.
- `GET /api/data` `universe_count` — the resolved universe size (currently 122), the same value the
  methodology card uses once it is shown.

---

## Incomplete Items (honest)

- **The seed expansion itself — NOT done.** `config.universe.symbols` is still 122 (target ~400–500);
  `data/seed/universe.json` and the new price CSVs were not produced; the 3 integration tests that verify
  the real expansion remain skipped (they assert once the committed screen record exists). **Blocked on
  the data provider — see Known Limitations.**
- **Risk-Off bootstrap-date re-verification (J-07/J-08)** — deferred; it can only be done after the
  universe is expanded (it depends on the new universe's breadth). It is step 3 of the finish runbook.
- **J-22 browser acceptance** — cannot pass yet (the grown universe + the screen card are not present).
  The card is hidden *honestly* rather than showing a fake screen.

---

## Config and Environment Changes

- `config.yaml` → `methodology.universe_selection` — **new section** (membership-rule prose + the three
  screen thresholds as live references to `universe.filters`; no hard-coded numbers). It is served to the
  UI **only after** a real screen runs (see the honest gate above).
- `config.yaml` → `universe.symbols`, `stock_sectors`, `themes` — **unchanged this run** (still the prior
  122); they are regenerated from the screen result by `apply_universe_to_config.py` once the screen runs.
- No new environment variables. **No committed secret / API key** — the intended price + market-cap
  endpoints are key-free; nothing secret is stored.

---

## Known Limitations

- **The one external dependency is unavailable from this environment (root cause of the stall).** The
  expansion needs a one-shot, dev-time fetch of real daily price history (for reference price + average
  dollar-volume) and a real market cap for ~300 new names. On 2026-06-02 the developer re-probed every
  free, no-key source and **none can supply the needed price history**:
  - **Yahoo** (the proven source from iteration 1) returns **HTTP 429 "Too Many Requests"** persistently,
    on **both** of its hosts — an IP-level rate-limit on this machine's network egress.
  - **Stooq's** free price CSV now requires a **captcha-obtained API key**.
  - **nasdaq.com** is bot-gated / returns empty.
  - **SEC EDGAR** *is* reachable (company list + shares-outstanding) but provides **no daily price
    history**, so it cannot fill the gap — and a real market cap still needs a real price.
  - **Wikipedia** *is* reachable — which is why the candidate pool built successfully.
  - Because the project's **No-fabricated-data** rule forbids inventing prices to force a green result,
    the universe was **not** expanded. This is the honest outcome.
- **Finish runbook — run when a real, no-key price source is reachable again** (the build loop afterwards
  only reads the committed result; nothing fetches live data at runtime):
  1. `apps/backend/.venv/bin/python apps/backend/scripts/screen_universe.py --screen --end <trading-date>`
     → fetches the real data, applies the screen, writes `universe.json` + the new price CSVs + `meta.json`.
  2. `apps/backend/.venv/bin/python apps/backend/scripts/apply_universe_to_config.py`
     → rewrites `config.yaml` (universe + sectors + pruned themes) from the screen result.
  3. Re-verify the two **Risk-Off bootstrap dates** (`2022-10-07` and `2025-04-04`) still label Risk-off
     under the bigger universe; if one flipped, swap it for a real Risk-off date in config (config only).
  4. Delete `apps/backend/data/trendora.db`, restart the backend (it regenerates the snapshots + forward
     returns over the new universe), then run the full backend test suite **once**.
  5. Commit the new seed files + `config.yaml`. The "Universe Selection" card then appears automatically.
- **Mixed-epoch seed (by design):** the screen reuses the existing committed price files (S&P benchmark,
  ETFs, prior names) and fetches only the **new** names — preserving the proven existing history and
  minimizing network exposure. Each file is internally adjusted and the engine compares within-symbol
  returns, so mixing reused and freshly-fetched series is sound.
