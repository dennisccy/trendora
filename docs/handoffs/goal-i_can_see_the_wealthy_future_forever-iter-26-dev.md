# goal-i_can_see_the_wealthy_future_forever-iter-26 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-26
**Date:** 2026-06-09
**Agent:** developer
**Status:** complete

## What Was Built

The single goal of this iteration was to make the four already-built Data-Manager journeys (J-37 missing-data
diagnostic + gap-exact pull, J-38 unified Unfinished-imports, J-39 seed-safe Remove, J-35 expand-universe)
**demonstrable end-to-end offline** so the browser-qa-agent can capture their defining multi-step flows, plus
fix one small J-38 Resume-without-key UX gap. No production user-facing capability is added.

- **Env-gated offline `seed` import source (the capture enabler).** A new `seed` entry appears in the
  `GET /api/data` `sources` catalog and is accepted by the job-source validator **only when the env flag
  `TRENDORA_ENABLE_SEED_IMPORT_SOURCE` is set** (off by default, absent from the committed `config.yaml`
  catalog, never in production). It is no-key, market-cap-capable, always-available, and serves the **real
  committed seed bars** through the **existing** J-34 chunked engine + the **existing** `screen_reasons`
  predicate — no second fetch path, no second screen rule, no fabricated data. This lets the browser drive a
  real J-37 pull and a real J-35 expand to completion with no live network.
- **Offline market-cap reference for the `seed` expand.** `SeedProvider.get_market_cap` now reads an OPTIONAL
  committed `market_caps.csv` from its seed dir (returns the real listed value, or `None` for an absent
  symbol — an honest `no_market_cap` omission, never a fabricated cap). The production seed dir has no such
  file, so the default provider's behavior is unchanged.
- **Overlay seed dir for the offline expand (committed-seed-safe).** A `seed`-source **expand** now writes its
  grown `universe.json` / per-symbol CSVs / `meta.json` to a **throwaway overlay dir**
  (`TRENDORA_SEED_IMPORT_DIR`) instead of the committed `data/seed/` tree — so an offline J-35 capture can
  never mutate the committed seed. For any real provider the behavior is unchanged (writes to the committed
  seed as before).
- **QA fixture-DB builder** (`apps/backend/scripts/build_qa_fixture_db.py`). Builds a throwaway fixture DB +
  a narrowed fixture config + a writable seed overlay (with `market_caps.csv`) so the diagnostic renders all
  three categories (no-history `ANET`, thin `DELL`, intra-series-gap `MU`) and the `seed` source can supply
  the missing bars for a real pull/expand. It NEVER mutates the committed seed tree (refuses to, and copies
  rather than symlinks).
- **J-38 Resume-without-key UX fix (the iter-25 UT-11 FAIL).** A needs-key Resume submitted without a key now
  shows a **visible inline `role="alert"` error** (an actionable, source-specific prompt when no key was
  entered) and the unfinished-imports row **stays** — `onResumed`/overview reload runs on SUCCESS only, so a
  failed resume never silently drops the row. Added a `data-testid="resume-error"` for deterministic capture.

## Files Changed

- `apps/backend/app/engine/data_manager.py` -- env-gated `seed` entry in `compute_provider_availability`;
  seed-aware source-validator gate (`_provider_entry_with_seed`); `seed_import_source_enabled` /
  `seed_import_overlay_dir` helpers; route a `seed`-source expand's artifact write to the overlay (never the
  committed seed) in `start_data_job`.
- `apps/backend/app/data_providers/seed_provider.py` -- `SeedProvider.get_market_cap` reads an optional
  committed `market_caps.csv` (real data only; honest `None` when absent).
- `apps/backend/app/data_providers/__init__.py` -- `make_provider("seed")` honors `TRENDORA_SEED_IMPORT_DIR`
  overlay env dir (test/dev only); committed default when unset.
- `apps/backend/scripts/build_qa_fixture_db.py` (new) -- the throwaway QA fixture-DB + overlay builder.
- `apps/backend/tests/test_data_manager.py` -- seed-source present-only-when-flagged / absent-otherwise;
  seed job validates through the existing gate; gap-exact + idempotent seed pull; offline expand
  passers+omitted; **expand writes to overlay not committed seed** (corruption regression); fixture builder
  writes only to temp.
- `apps/backend/tests/test_api_data.py` -- `seed` source surfaced in `GET /api/data` under the flag; `seed`
  job dispatch via `POST /api/data/jobs` without a key.
- `apps/backend/tests/test_seed_provider.py` -- `get_market_cap` None-without-reference / reads-committed.
- `apps/backend/tests/test_provider_clients.py` -- `make_provider("seed")` honors the overlay env dir.
- `apps/frontend/app/data/page.tsx` -- J-38 `ResumeControl`: clearer inline `role="alert"` error +
  `data-testid="resume-error"`; defensive comment-gate that a failed resume never reloads-away the row.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: full suite run in progress at handoff time; all NEW tests pass (40 targeted seed/fixture/expand/
provider tests green) and the committed seed tree is byte-identical (verified). Frontend `npx tsc --noEmit`
is clean. See "Known Issues" for the full-suite confirmation note.

The new tests assert exact values: the `seed` entry shape (no-key, cap-capable, available, no key value);
absent-without-flag; the gap-exact pull fills exactly the diagnosed `(symbol, [start,end])` and re-runs with
zero duplicates; the offline expand yields 1 passer + the three honest omission reasons; and a seed expand
leaves the committed-seed sha unchanged while writing the grown `universe.json` to the overlay.

## Known Issues

- **Live-provider paths were NOT exercised (data-walled, non-halting).** Per `docs/goal.md` lines 989–1012 and
  the iter spec, the *live* outcomes of J-35 expand / J-37 pull / J-38 retry over a real walled provider
  (Yahoo-429 / key-gated) are recorded honestly as NA / non-halting. All four target flows are captured
  against the **deterministic offline `seed` source + the throwaway fixture DB** — never a live network.
- **Corruption guard added after a near-miss.** An early offline-expand experiment (before the overlay fix)
  truncated several committed seed CSVs because a `seed`-source expand wrote per-symbol CSVs into the
  committed `data/seed/` tree. This is now fixed (the seed-expand artifact write is routed to the throwaway
  overlay), the committed seed was restored from HEAD, and a regression test
  (`test_seed_source_expand_writes_to_overlay_not_committed_seed`) guards it. **The committed seed tree is
  clean** (`git status apps/backend/data/seed/` empty).
- **QA harness setup (operator note).** To capture J-37/J-35 offline: run
  `apps/backend/scripts/build_qa_fixture_db.py --out <tmp>`, then boot the backend with the three env values
  the script prints (`TRENDORA_ENABLE_SEED_IMPORT_SOURCE=1`, `TRENDORA_CONFIG=<tmp>/config.yaml`,
  `TRENDORA_SEED_IMPORT_DIR=<tmp>/seed_overlay`). The fixture's universe is narrowed to ANET/DELL/MU/AMD so the
  diagnostic shows exactly the three categories. The DB url is baked into the fixture config.
- **J-39 destructive capture** must run against the **fixture** (never a live real symbol); the live host
  capture uses the non-destructive **preview** endpoint (MEMORY `j39-live-host-has-user-added-nvda-bars`).
- **No service-startup smoke run was performed by dev** (no backend/frontend processes were started, to avoid
  port conflicts on this shared machine and to respect the kill-by-port rule). `npx tsc --noEmit` confirms the
  frontend change type-checks; the env-fix gate (rm `.next`, restart `next dev`) is QA's responsibility before
  driving the UI.
