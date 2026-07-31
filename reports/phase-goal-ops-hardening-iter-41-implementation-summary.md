# Phase goal-ops-hardening-iter-41 — Implementation Summary

**Phase:** goal-ops-hardening-iter-41
**Date:** 2026-07-31
**Written by:** developer

---

## Features Implemented

This is an ops/tooling-correctness iteration — no new end-user feature. Two things were fixed for the
operators of this development pipeline itself:

- **Verification pipeline repair**: The automated pipeline that re-checks "does the app still work"
  every iteration was silently skipping that check for iterations that only changed backend code (no new
  screen or button). It now still re-checks the app's existing pages when the iteration names journeys
  that must keep passing, even though nothing new was built to look at.
- **Memory-usage bound on a data-loading step**: One internal data-loading routine (`_BarCache.prefill`,
  used when computing dataset coverage/backfills) that streams the whole price-history table into memory
  now uses roughly half the memory to hold the same data, measured on the real database (~1.34 GB before,
  ~0.65 GB after — a 51.5% reduction). No visible change to any page; the same numbers are computed and
  displayed as before.

---

## Changed Behavior

- **Automated re-verification of existing pages**: Previously, a backend-only development iteration
  (nothing visibly changed for a user) skipped ALL automated browser re-checks entirely — it just wrote
  "N/A, nothing to check" and moved on, even for pages that absolutely needed to keep working. Now, if
  the iteration's own worklist names pages/flows that must still work, those get a real automated
  re-check with real evidence (screenshots/results) — not just an assumption they still work.
- **Automated pipeline's health-check URL**: The pipeline's own automated helper (an AI agent that
  drives a browser to re-check the app) was polling the wrong web address to ask "is the backend up?" —
  it was polling a generic path that this specific app never uses, so a perfectly healthy backend could
  get misreported as "down." That's fixed; it now polls the correct address.
- **Checkpoint frequency during a data backfill**: If an operator kills a running data-backfill job at
  exactly the wrong moment, the system now guarantees its "last known progress" record is never more than
  5 days of work stale (previously it could be staler if each day's work finished unusually fast).

---

## Backend-Only Items

- Everything in this iteration is backend/pipeline-only by design — the phase spec itself declares "no
  new UI surface." Nothing here is a "feature with no UI wiring" in the usual sense (that phrase implies
  a user-facing capability was built but not surfaced); this iteration built no user-facing capability at
  all.

---

## Incomplete Items

- **The live "does the system freeze under memory pressure" drill** was re-run once (as the plan
  specified) with a new diagnostic tool armed (a way to get a live snapshot of what every thread in the
  process is doing, without killing the process, if it ever does freeze). The freeze from several
  iterations ago did NOT happen again on this re-run, so the new diagnostic tool was never actually
  triggered — there was nothing to diagnose. The original freeze from iterations ago is still not
  positively explained; this iteration did not (and could not) close that question, only add a tool that
  would help catch it live next time it happens.
- Two owner-level decisions flagged in earlier iterations (how strict the health-check speed requirement
  should be; whether the frontend-start script needs an additional safety limit) remain open — this
  iteration was explicitly told not to touch them.

---

## Config and Environment Changes

- `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1` — new, optional, diagnostic-only environment variable. When set to
  `1` before starting the backend, arms a tool that lets an operator send a special signal to a possibly-frozen
  backend process to get a snapshot of what every part of it is doing, without killing it. Default: unset
  (off) — every normal deployment is unaffected. Never touches the app's normal startup scripts.
- No database migrations, no new config file entries, no new dependencies.

---

## Known Limitations

- The memory-usage improvement (B5) makes ONE specific internal data-loading step use less memory per
  row of data — it does not change the fact that this step still reads the whole price-history table for
  certain operations (full backfills, dataset coverage). That is an existing, intentional design choice
  (some operations genuinely need the full picture); this iteration made that design choice cheaper, not
  different.
- The diagnostic freeze-detection tool added this iteration only helps if a freeze is caught WHILE it is
  happening — it did not (and could not, since no freeze occurred) prove or disprove what caused the
  original freeze several iterations back.
- The pipeline-repair work (fixing which pages get automatically re-checked) turned out to require
  changing three pipeline scripts, not just the one originally planned — the extra two were necessary for
  the fix to actually take effect. This is disclosed in detail in the developer handoff for whoever
  reviews this work next.

---

## Post-Review Fix (attempt 2)

The code review of this iteration returned FAIL on one point, now fixed.

- **What was wrong**: One of the new automated checks written this iteration — the one that proves the
  new freeze-diagnostic tool actually works — was itself broken and had never been run before the work
  was handed over. It was looking for the word "Thread" (capital T) in the diagnostic's output, but the
  diagnostic actually writes "Current thread" (lowercase) when the process being inspected has only one
  thread running, which is exactly the case this check sets up. So the check could never have passed.
- **What was fixed**: The check now recognizes both wordings the diagnostic tool can produce, while still
  refusing to pass if no diagnostic snapshot was written at all. Only that one test file was changed —
  no application code, no pipeline scripts. The freeze-diagnostic tool itself was never faulty; the
  review confirmed the tool works and only the check that inspects it was wrong.
- **Verified**: the corrected check passes three times in a row, and the other test files touched by this
  iteration were re-run and still pass (17, 4, and 2 checks respectively — all green).
- **Worth an operator's attention**: the real problem was not the wording mismatch but that this check
  was shipped without ever being run, while the handover document listed twenty other checks that WERE
  run — which made the omission easy to miss. That is the same class of gap this whole iteration was
  meant to close, so it is recorded plainly here rather than quietly fixed. No automatic safeguard
  against that specific pattern was added (that would have been unrequested extra work); it is flagged
  for whoever decides what the next iteration should cover.
