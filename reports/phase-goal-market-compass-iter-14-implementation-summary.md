# goal-market-compass-iter-14 — Implementation Summary

**Phase:** goal-market-compass-iter-14
**Date:** 2026-08-24
**Written by:** developer

---

## Features Implemented

This iteration built and ran (read-only, without executing any data-changing regeneration) the safety
checks that the still-unauthorized "Stage D" data-repair step will need before it can ever run.

- **A fresh, honestly-computed identity for the next repair attempt**: recorded exactly what version of
  the code and settings would be used if Stage D ran today, without assuming or forcing any earlier
  attempt's identity onto it.
- **Three automatic tripwires** that will stop a future Stage D run cold, with zero data changes, if the
  code/settings drift mid-attempt — before the first write, before each date, and after each write —
  rather than silently continuing with mismatched data.
- **A pre-flight readiness check**, run live against the real database today: confirmed the 11 affected
  historical dates are still cleanly empty, confirmed the price history and existing decision records are
  completely unchanged since the last verified checkpoint, and confirmed no format/rules the repair
  depends on have drifted. Result: **every check passed.**
- **A set of "what if something goes wrong" tests** proving the safety machinery actually stops things —
  a corrupted record, a missing confirmation flag, or a failed check all correctly block any data-changing
  action and leave no false "all clear" marker behind.
- **A one-name investigation into a known data-scale oddity** (one stock, AVB, has prices stored at a
  different numeric scale than every other stock in the tracked list — a known, already-recorded
  side-effect of a prior data-recovery step). This iteration traced exactly how much that scale
  difference could affect trading decisions if left as-is: essentially none — the stock's admission to
  the tracked universe, its risk category, and its "should I look at this" status are all unaffected. The
  effect is honestly recorded as small but real (it nudges a handful of OTHER stocks' rankings by a
  hair), and the finding says this does not need to be fixed before the repair can proceed.

## Changed Behavior

Nothing user-facing: no page, screen, or API response changed. This iteration adds new safety/diagnostic
tooling only.

One operator-facing change, added during the review fix-up: the maintenance command-line tool that
performed the previous iteration's one authorized data clean-up no longer has a built-in default output
folder. Anyone running it must now state where its record-keeping files should be written; if they leave
that out, it stops immediately and explains why, instead of quietly writing into the real evidence folder.
That tool's actual clean-up job is already finished and is not run again.

## Backend-Only Items

- All new tooling (the identity freeze, the three tripwire checks, the pre-flight check, and the AVB
  investigation) is command-line/engine-level only — there is no UI for any of it, by design (this
  iteration deliberately touches no frontend code at all).

## Incomplete Items

None from this iteration's own scope. The actual data-repair step ("Stage D") remains intentionally
NOT started — that was never part of this iteration's job; it requires a separate, explicit go-ahead
from the project owner.

## Config and Environment Changes

None. No `config.yaml` value, environment variable, or database schema changed.

## Known Limitations

- **Resolved since the first draft of this report.** A checksum quoted by the coordinator (meant to prove
  a set of 24 historical records is unchanged) was first reported as "could not be reproduced." That was
  a mistake in method, not a real disagreement: the number is produced by one specific technical recipe,
  and following that exact recipe reproduces it digit for digit. The records are unchanged, and the
  separate, stronger check — comparing every one of the 28 fields of all 24 records, one by one — also
  found zero differences.
- **Resolved, and the earlier explanation was wrong.** Three evidence files saved by the previous
  iteration were emptied out on disk during this work. The first draft of this report blamed unrelated
  automation. It was in fact caused by one of this iteration's own new automated tests: the test called a
  command-line tool without telling it where to put its (fake, test-only) output, so the tool fell back to
  its built-in default location — which happened to be the real evidence folder — and wrote over the
  files there. The problem was caught in code review. All three files were restored intact from the
  project's git history, the test now writes only into a scratch folder, and the tool itself was changed
  so that it refuses to run at all unless the output folder is stated explicitly. No product data or
  database record was ever at risk; only these three record-keeping files were affected, and they are
  fully recovered.
- One stock's investigation (AVB) confirmed a small, real ripple effect on a handful of OTHER stocks'
  rankings, but did not go the extra step of re-checking whether any of THOSE other stocks' risk category
  changed as a result — the ripple sizes involved are too small to plausibly matter, but this was not
  independently double-checked, in the interest of keeping the investigation appropriately narrow.
