# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26
**Date:** 2026-06-17
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- When an Expand-universe job is paused in a resumable state (due to a Yahoo market-cap authentication or rate-limit failure), the operator can click **Resume** on the `/data` Unfinished-imports panel and the job picks up exactly where it left off — without re-downloading price history it already fetched.
- An operator who sees a previously failed Expand-universe job now gets an honest, actionable message in the job card — the Unfinished-imports row shows a Resume control and an explanation that the market-cap provider auth failed, rather than a misleadingly "successful" job that reported zero qualifying companies.

---

## What Changed in the Visible UI

- The **Unfinished-imports panel** on `/data` (Data Manager) now displays an honest, resumable-state job card when an Expand-universe job hits a systemic Yahoo authentication or rate-limit failure. Previously this panel would show nothing unusual (the job appeared complete), or would show a completion with "0 passers, 548 omitted" — indistinguishable from a real empty universe. Now the panel shows the paused/resumable status with the actual backend message.
- The **job message** on the `/data` job card for a resumed or paused Expand job now accurately reflects "market-cap provider auth failed — Resume to retry" (plumbed verbatim from the backend payload). Previously any systemic Yahoo auth rejection produced the same look as every individual company having no market cap.

---

## What Old Behavior Changed

- **Expand-universe job on Yahoo auth/rate-limit failure:** Previously the job completed "successfully" but silently omitted every candidate and wrote a 0-member universe file, making the universe look empty. Now a whole-batch Yahoo authentication or rate-limit failure pauses the job in a **resumable** state (no universe file written), and the Unfinished-imports panel on `/data` offers the Resume affordance with an honest message.
- **Seed manifest protection (J-39):** A corrupt empty-universe record and clobbered price-seed manifest committed by the prior session's bug have been repaired. The committed-seed window safeguard (which protects the 159 committed price symbols — e.g. NVDA `2021-01-04..2026-05-28` — from accidental deletion) is now re-enabled. This behavior change is not directly visible in the UI, but it restores the correctness of the remove-symbol confirmation guard.

---

## Not Visible Yet

- **Real, populated universe (~500 members with actual market caps):** The cookie+crumb authenticated batch market-cap fetch is fully implemented in the backend and proven offline with injected providers. However, a live successful fetch of market caps from Yahoo is provider-rate-limited on this host, so the populated universe (J-22's ≥500-real-members leg) cannot be demonstrated here. When Yahoo is reachable, the Expand job will produce a real member list with actual per-member caps rather than an empty universe.
