# goal-market-compass-iter-3 — User-Visible Changes

**Phase:** goal-market-compass-iter-3
**Date:** 2026-08-20
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see, on the Dashboard (`/`), a new **"Manifest"** card at the bottom of the compass
  stack (below "Next-session focus") proving that each close's decision brief was frozen, stamped, and
  exported unchanged — not merely computed and displayed.
- Users can now expand an **"Audit table"** disclosure inside the Manifest card to see, for a given
  date, every stock that was NOT selected as a candidate — each row carries its own frozen leadership /
  entry / risk scores plus the specific reason it wasn't picked ("below selection floor" or "excluded
  by cap").
- Users can now see a separate **"near-threshold shadow"** list inside the same audit table — stocks
  that scored just below the selection bar — under its own explicit, always-visible "research-only"
  label, so it can never be mistaken for part of selection.
- Users can now step the as-of date switcher to any historical date and click **"Regenerate manifest"**
  on the Manifest card to mint an explicit, clearly-labeled new version of that date's manifest under
  today's rules, through a confirmation modal that spells out exactly what will and will not change —
  without ever touching or hiding the original version.
- Users can now see a **"Versions"** list on the Manifest card once more than one version exists for a
  date, showing each version's mode, eligibility, and freeze timestamp side by side.
- Users can now see whether a manifest's underlying data is still available, was rebuilt, or has become
  unavailable, via a **"Basis: available / rebuilt / unavailable"** line on the Manifest card.
- Users can now read clean, rounded numbers (e.g. "6.27") in the Summary card's "Show cited facts"
  panel, instead of occasionally seeing a raw floating-point artifact (e.g. "6.2700000000000005").

---

## What Changed in the Visible UI

- The Dashboard (`/`) gained a new **"Manifest"** card — the last card in the compass stack, positioned
  above the existing, unmodified dashboard body (regime/phase/chart/more-detail sections).
- The Manifest card shows: a mode badge ("at ingest" or "retrospective"), a "version N" badge, a
  "frozen"/"not frozen" badge, a "prospective-eligible"/"not prospective-eligible" badge, a "Frozen
  \<timestamp\>" line, four truncated hash chips ("Engine identity", "Candidate rule", "Cohort rule",
  "Manifest config" — each showing a short value ending in "…" with the full value reachable via a hover
  tooltip), a dataset stamp, the universe pool hash + member count + profile, and the basis-disclosure
  line.
- The Summary card's "Show cited facts" disclosure now shows every numeric fact rounded to 2 decimal
  places.
- Candidate cards in "Next-session focus" now show a shorter, fact-only ATR caution sentence (ending
  "... of universe).") with no advice-sounding tail.
- The `/data` page's "Refreshed:" line (shown in the Job progress panel and Run history rows after a
  snapshot job's finalize step) now reads "...**next-session manifest**..." (hyphenated) instead of
  "...next session manifest..." (no hyphen) whenever that job's finalize tail included the manifest
  freeze phase.

---

## What Old Behavior Changed

- **Loading the current/live date's compass before the nightly close has frozen it:** previously,
  simply loading `/` (or calling `GET /api/compass`) for today's date would silently compute and save a
  manifest on the spot. Now, only the real overnight ingest-finalize process — or an explicit
  "Regenerate manifest" click for a HISTORICAL date — is allowed to create a manifest for the live
  frontier; a plain page load before that happens now honestly renders "unavailable" on the affected
  compass cards instead of quietly creating one.
- **The ATR risk caution on candidate cards:** previously ended with an imperative-sounding "— sized
  risk accordingly"; it now states the fact only (e.g. "ATR_RISK_BUDGET: ATR is 3.42% of price (p67 of
  universe).").
- **Summary-card cited numeric facts:** previously could render a raw unrounded float string for some
  values (e.g. a regime-score delta); now every numeric fact is always rounded to 2 decimal places for
  display (the underlying stored/served value is unchanged).

---

## Not Visible Yet

- **The export file itself:** each freeze also writes a byte-identical JSON file to disk for the
  separate Tapeology project to read. The file's path is stored on the manifest's database row but is
  **not** included in the `GET /api/compass` response and is **not** shown anywhere on the page — there
  is no way to tell from the UI whether or where an export file was written for a given date.
- **The manifest's own integrity hashes:** `manifest_hash` (the whole-document tamper-detection hash)
  and `content_hash` (the narrower research-content hash) are both served by `GET /api/compass`, but
  neither is displayed on the Manifest card — only four *other* identity hashes (engine identity,
  candidate rule, cohort rule, manifest config) are shown as chips.
- **`available_at_utc`:** the conservative timestamp fence a future prospective-observation study must
  respect is served in the API response but never shown on the page.
- **`generation.producer` and `generation.frontier_bar_date`:** served, but not directly labeled
  anywhere in the UI — the mode/version badges are the closest visible proxy for "how this manifest was
  produced."
- **The universe's `resolver_gate` detail** (the exact filter values used to build the universe pool) is
  served but not rendered — only the pool hash, member count, and profile ("core") are shown.
- **`generation.preflight_verdict`** is served on the manifest but is *deliberately* never rendered on
  the Manifest card — system-readiness vocabulary (GO/DEGRADED/NO-GO) must never appear next to
  market/manifest content (this is a by-design omission, not a gap).
- **The new `POST /api/compass/regenerate` action endpoint's raw response** carries the same full payload
  `GET /api/compass` does, but is only ever consumed by the Manifest card's own regenerate flow — there
  is no separate "API explorer" surface in this product.
