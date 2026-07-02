# Phase goal-mcp-loop-iter-16 — Implementation Summary

**Phase:** goal-mcp-loop-iter-16
**Date:** 2026-07-02
**Written by:** developer

---

## Features Implemented

- **A 30-year price-history download tool**: the seed ingest tool can now fetch the full ~30-year
  price history (back to 1996, or each company's real first trading day) for all ~588 needed
  names from the free Stooq data service, into a separate staging folder that the running product
  never touches. It fetches the most important names first (market benchmarks, then the current
  122 tracked stocks, then the rest of the 548-name candidate pool), waits at least one second
  between requests, and can be stopped and resumed at any time without losing progress or
  re-downloading anything.
- **A go/no-go probe**: before any large download, a three-stock test run checks that the data
  service actually works from this machine, that history really reaches back to 1996, and that
  prices are properly adjusted for stock splits. The big download only proceeds if all checks pass.
- **A data-quality inspection suite**: 7 automated checks that will validate the downloaded data
  before it is ever used — correct file format, dates in order, no impossible prices, real company
  listing dates respected (no invented early history for recent IPOs like Coinbase or ARM), no
  price jumps at known stock-split dates, and agreement with the current data where the two
  overlap. These checks activate automatically once the data exists.

## Changed Behavior

- None. Every page, number, badge, and ledger entry in the product is exactly as it was. The
  existing download tool's normal (Yahoo) mode behaves exactly as before.

## Backend-Only Items

- Everything in this phase is tooling/data preparation with no user-facing surface (by design —
  the visible 30-year history arrives in a later phase after the data is staged and swapped in).

## Incomplete Items

- **The 30-year data itself was NOT downloaded — honestly blocked.** The Stooq service refuses
  file downloads from this machine's internet address ("Access denied"), even after the tool
  correctly completes the site's automated browser check, on both of Stooq's domains. This is a
  standing block on this address, not a temporary limit. Nothing was faked or substituted; the
  blocker, with full evidence, is documented in the coverage report and the dev handoff.
- **A decision is needed from the operator** (one of): run the documented two commands from a
  different network (e.g. a home connection) — the tool is ready and resumes safely; or provide a
  sanctioned Stooq access key via the `STOOQ_API_KEY` environment variable; or change the goal's
  chosen data provider. Until one of these happens, the follow-up phase (swapping the product onto
  the 30-year data) cannot start.

## Config and Environment Changes

- `STOOQ_API_KEY` (optional, new) — if the operator obtains a Stooq access key, exporting it in
  the environment lets the download tool use it. It is read from the environment only and is never
  written to any file. Default: unset.
- No configuration file, database, or product setting changed.

## Known Limitations

- The data staging folder (`apps/backend/data/seed-stooq-30y/`) does not exist yet; the
  data-quality checks report themselves as "skipped — data not yet fetched" until it does.
- When the download eventually runs, coverage of a few special series (the VIX index and three
  macro proxies) is unknown until tried; any name Stooq lacks will simply be recorded as missing —
  never invented.
