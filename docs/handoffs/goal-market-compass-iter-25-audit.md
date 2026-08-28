# goal-market-compass-iter-25 Audit Report

**Date:** 2026-08-28
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

Both halves of the iteration really happened: the J-09 re-measurement ran live against the confirmed
canonical database, and the J-01/J-04/J-10 regression replay genuinely executed through the newly fixed
parser (verified from the rendered screenshots, the goldens' exact-value assertions, and the backend log
— not from the handoff's word). But the iteration reached me with two real defects that four upstream
lanes passed over: the parser fix introduced the **mirror image** of the bug it was chartered to remove
(demonstrated on a real committed spec), and `reports/perf-budgets.md` Addendum 41 asserted a **factually
false** causal explanation for its own headline result while understating the load the measurement ran
under by roughly 2×. Both are fixed here. The residual gap is that the headline VmPeak figure itself
(3,064,772 kB) has **no surviving primary artifact** — after two of its neighbouring claims turned out
wrong, that number rests on the measuring agent's report alone.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the parser fix introduced the inverse silent-wrong-parse it was written to eliminate**

`incredible_auto_dev/scripts/automation/lib/replay-lane.sh:86-95` (as delivered) replaced `head -1` with
"first label-matching line that contains a `J-NN` token." That removes iter-24's failure mode but creates
its mirror: an **explicit `none` bullet is now skipped** (it has no `J-NN` token) and an incidental prose
mention of the label phrase *later* in the document supplies the set instead — silently returning a WRONG
NON-EMPTY journey set. `replay_lane_warn_if_zero_parse` cannot catch it, because it only fires on *empty*
parses.

This is not hypothetical. A differential run of the old vs. delivered parser over every spec in
`docs/phases/` produced exactly one wrong answer, on a real committed spec:

- `docs/phases/goal-market-compass-iter-7.md:16` — `- **Required-still-passing journeys:** None this iteration — deliberately.`
- `docs/phases/goal-market-compass-iter-7.md:108` — prose: `...J-10 itself has no UI (walkthrough waived) and Required-still-passing is explicitly empty...`

Delivered parser returns `REQUIRED_JOURNEYS=<J-10 >` for that spec, with no warning. The spec sentence the
parser misreads literally says the set is empty, and goes on to explain that this is deliberate so the
lane has "no in-scope journey to test against the still-possibly-damaged database." A goal-mode iteration
of that shape would replay a journey it explicitly declined to declare, and feed the result to the
goal-evaluator as a required-journey verdict — a false FAIL could trip a spurious REGRESSION halt, a false
PASS records coverage that was never requested. (I was unsure between IMPORTANT and CRITICAL here and took
the lower one only because it adds unrequested verification rather than silently skipping it; the harm
class — the governor lying about what was verified — is the same one iter-24 escalated on.)

**Fix applied** (`lib/replay-lane.sh:86-112`): the label's own markdown bullet, when the spec has one, is
authoritative and is parsed alone; specs with no such bullet fall through to the delivered token-skipping
scan unchanged. The helper this needs, `replay_lane_bullet_line`, already existed — the developer wrote it
but wired it only into the warning path. Post-fix differential over all specs now shows *only* the three
intended repairs (`goal-market-compass-iter-24`, `goal-mcp-loop-iter-26`, `goal-ops-hardening-iter-46`)
and no wrong answers. Verified: `test-replay-lane.sh` **84 passed, 0 failed** (81 + 3 new);
`test-replay-lane-full.sh` **24 passed, 0 failed**; `test-backend-launch-context.sh` **18 passed, 0 failed**;
`bash -n` clean on all four edited shell files. TC-4/TC-5/TC-6 all still pass.

**B2 — IMPORTANT (fixed): Addendum 41's explanation for its own headline improvement is factually false**

`reports/perf-budgets.md` (Addendum 41) attributed the entire 10.9% VmPeak improvement to host quiet:
*"Addendum 40 explicitly recorded a SECOND concurrent goal-mode engine sharing the host throughout that
round; none was present this round."*

`/home/dennis-chan/.cache/iad/host-guard/events.jsonl` contradicts this outright. A second goal-mode
engine was resident across the whole burst window:

```
2026-08-28T10:20:13  engine_start    /home/dennis-chan/Git/tensteps  sid=ten-steps-v1  pid=3510323
2026-08-28T10:20:17  iter_start      tensteps  iter=17  depth=full
2026-08-28T10:20:17  dispatch_start  tensteps  agent=goal-decomposer
2026-08-28T10:38:05  dispatch_end    tensteps  agent=goal-decomposer  rc=0  dur_s=1068
```

The bursts ran 10:24:06–10:30:33 — entirely inside that 1,068-second dispatch. The `aggregate_ok` event at
10:20:17 records `live:5`. Host conditions were therefore *not* materially quieter than Addendum 40's, and
the stated cause cannot hold. This matters because the addendum is the artifact the owner will use to rule
on J-09: it currently invited the reading "the improvement was an artifact of host load, not the product."

**Fix applied:** the explanation paragraph now records the improvement as real but **UNEXPLAINED**, and
explicitly forbids attributing it either to host quiet or to J-10/J-11's database changes without new
evidence. A dated `iter-25 AUDIT CORRECTION` block at the end of Addendum 41 records what was changed and
why, with the event-log citations, so the original claim is not quoted from an older copy.

**B3 — IMPORTANT (fixed): the recorded request counts understate the load the VmPeak was sampled under**

TC-2's recorded figure — "451 + 1,679 = 2,130 total live HTTP requests" — does not match the server. The
measurement session (`logs/backend.log`, `=== start-backend.sh: launching at 2026-08-28T09:22:32Z ===`,
lines 405471-408407) logs **2,614 HTTP requests, every one a 200** — 2,403 excluding 211 `/api/health`
polls — against 2,130 issued of which 39 timed out (≈2,091 served).

The endpoint histogram localises the excess to the *replica* burst (the one that produced the headline
figure): the six endpoints of the 6-endpoint replica mix average **313.8** requests each, while the three
endpoints unique to the 10-endpoint stress mix average **164.3** — implying roughly **900** replica-mix
requests, about double the 451 reported. Consequence: **the primary VmPeak plateau was sampled under
approximately twice the request volume Addendum 41's own Method section documents.** The direction does
not flatter the number, but the Method section does not describe the load the backend actually saw, and
the two stress runs are likewise not load-comparable (iter-4 completed 4,240 requests at identical
parameters; this round completed 1,679 — a ~2.5× throughput drop that the addendum's head-to-head stress
comparison does not acknowledge).

**Fix applied:** TC-2's paragraph now cites the server-side count and flags the client-side total as
unreliable; the correction block carries the histogram derivation and the load-comparability caveat.

**B4 — GAP (fixed wording, defect stands): the 39 stress-burst timeouts were never served**

The handoff and addendum dismissed the 24-worker burst's 39 client-side timeouts on `/api/market-phase` as
"a harness pacing artifact (server ultimately returned 200 for all of them)." Those 39 requests have **no
server-side log line at all** — the deficit is directly visible as `/api/market-phase` logging 133
requests where the comparable stress-only endpoints logged 186 and 174. Nothing the server *answered* was
a non-200, which is what TC-2 actually gates on, but the dismissal as stated is unsupported. Wording
corrected in Addendum 41; the underlying behaviour (a slow endpoint under 24× stress) is out of this
iteration's scope.

**B5 — OBSERVATION (fixed): stress-variant delta arithmetic**

`401,316 / 4,493,232 = 8.93%`, not the recorded `+9.3%`. Secondary figure only. Corrected to `+8.9%`. The
primary figure's `+16.9%` over target and `−10.9%` vs iter-4 both re-check correct, as do the MB
conversions and the 63.5% / 41.7% cap margins.

**B6 — GAP (not fixed): the headline VmPeak figures have no surviving primary artifact**

No sampler log, `/proc` capture, or any other artifact from this run contains a VmPeak reading. The only
files holding `3,064,772` are the four narrative documents that quote each other (`perf-budgets.md`, the
dev handoff, the review, the QA report). Addendum 41 also records **no clock times** — only the date and
relative `t+90s`/`t+105s` offsets — which is why locating the run in `logs/backend.log` required inference
from the launch banner. The spec did not require retaining raw samples, so this is a gap rather than a
defect; but with B2, B3 and B4 all being claims from the same section that durable evidence contradicted,
the uncorroborated number deserves the owner's scepticism. Recommendation recorded in the correction
block: future addenda must record burst start/end in UTC and retain the sampler output.

**What did hold up under attack.** Not everything I probed was wrong, and the corroborated set is
substantial:

- **Canonical targeting — CORROBORATED** by evidence independent of the vanished `/proc/<pid>/fd` check:
  `apps/backend/data/trendora.db` is exactly 8,365,871,104 bytes as claimed; its `-shm` sidecar mtime
  (10:42:36) sits one second after the second backend launch, and `-wal` (10:31:23) inside the measurement
  window; the decoy `data/trendora.db` stub was untouched on 08-28; and no clone DB exists anywhere on
  disk. The measurement really did run against canonical.
- **Byte-identity (TC-3) — FULLY CORROBORATED with primary artifacts.** All eight captured response bodies
  survive; all four md5s re-compute exactly as recorded, byte counts match, `cmp` on each v1/v2 pair is
  identical, `as_of` is `2026-08-10` on all four, and `/api/compass` returns
  `mode: retrospective, version: 1, frozen: true`. The eight fetches are visible in the backend log from
  two distinct client-port families, confirming two genuine independent read rounds.
- **Zero non-200s, zero `QueuePool` — CORROBORATED.** 2,614/2,614 are 200. All 19 `QueuePool` lines in the
  entire append-only log are from 2026-08-04, exactly as the addendum states.
- **Config integrity (AG-10) — CORROBORATED.** `git diff HEAD -- config.yaml` empty; `cache_size: -65536`,
  `pool_size: 24`, `max_overflow: 44`, `memory_cap_mb: 8192`, `malloc_arena_max: 2` all as claimed;
  `project-extensions/host-guard/host-guard.env` clean and untouched for nine days.
- **Append-only discipline — CORROBORATED by hash, not just by diff.** Addenda 39/40 (lines 11947-12235)
  and the entire pre-Addendum-41 file hash identically to HEAD both before and after my own edits;
  `git diff --numstat` on `perf-budgets.md` is still `178 0` — a pure append, one hunk at line 12236.

### Frontend Findings

None. `apps/frontend/**` and `apps/backend/app/**` are byte-unchanged (`git status` confirms), which is
correct for this spec — J-09's walkthrough is waived by its own acceptance text and the parser fix is
automation-only.

### Test Findings

**T1 — IMPORTANT (fixed by verification): the DoD's regression claim was signed off on 2 of 21 relevant suites**

DoD item 9 claims "no regressions in existing `scripts/automation` ... coverage this iteration's changes
touch." 21 of the 48 suites in `incredible_auto_dev/tests/automation/` reference the edited files; the
developer, reviewer and QA all ran only `test-replay-lane.sh` and `test-backend-launch-context.sh`. The
single most relevant suite — `test-replay-lane-full.sh`, which drives `browser-qa-phase.sh`'s replay lane
end-to-end, including the exact `_bqa_targets` path the developer refactored at line 405 — was never run
by any lane. I ran it: **24 passed, 0 failed**, with my B1 fix in place. No regression exists, but the
checkbox was ticked on evidence that did not cover the change.

**T2 — GAP (not fixed): J-01's golden replay asserts far less than the journey claims**

`runs/goal-session-market-compass/journey-scripts/J-01.json` — journey "Sector attribution is honest and
near-complete on new runs" — asserts only that `/stocks?asof=2026-08-12` renders the text "Stock
Leaderboard" and that searching `GRMN` shows "Consumer Discretionary". Neither *honest* nor
*near-complete* is tested: no coverage ratio, no absence-of-fabrication check, one ticker. The iteration's
own GOAL says the parser fix exists so these journeys are "genuinely re-verified... instead of merely
assumed" — for J-01 the replay is a thin proxy for its own claim. Pre-existing (goldens dated 2026-08-20),
outside this spec's scope, so not fixed. **J-04 and J-10 are the opposite and deserve credit**: they pin
exact values (`Strong leader (81.2)`, `REGIME_RISK_OFF`, `$187.89`, `$187.94`) — real AG-3-grade
assertions, and the J-10 screenshot independently shows `$187.94` on the live as-of-2026-08-11 page.

**T3 — OBSERVATION: TC-4 tests a copy of the old bug, not a live code path**

`test-replay-lane.sh` reproduces the pre-fix behaviour with an inline `_pre_fix_spec_journeys` copy. It is
byte-faithful to the removed implementation and honestly labelled as documentation of the bug shape. This
is the right call (both versions cannot coexist), and TC-5 exercises the real function, which is what
gates the behaviour.

**T4 — GAP (not fixed): the zero-parse warning is advisory only**

`replay_lane_warn_if_zero_parse` writes one line to stderr and by design "never affects control flow or
exit status." Nothing records it for the goal-evaluator, and no lane verdict changes. That matches the
spec exactly ("reported as a lane warning, not swallowed"), so it is not a defect — but iter-24's failure
was invisible precisely because nothing *noticed* a passive signal in a long log. Worth an owner decision
later on whether a zero-parse on a declared set should block the lane rather than warn.

---

## 3. Domain Assessment

**The parser.** The delivered fix identified the right defect and the right file (one real file — the
`scripts/` → `incredible_auto_dev/` symlink identity is confirmed by md5, and only one copy was patched,
as instructed). Its weakness was treating "skip token-less lines" as universally safe when it is only safe
*within prose*; the authoritative-bullet concept was already implemented three functions away and simply
not used on the parse path. Post-fix, the function has a clear precedence rule — own bullet wins, else
first token-bearing line — that is correct in both directions, and the differential across every spec in
the repo produces exactly the three intended repairs and nothing else. The load-bearing `set -e` +
`pipefail` guarantee (`set -uo pipefail` really is in force, inherited from `lib/telemetry.sh:21`) is
preserved: I exercised the real call-site pattern against the iter-25, iter-24 and iter-7 specs plus a
malformed-bullet spec under `set -euo pipefail` and every path survives, with the warning firing exactly
where it should.

**The measurement.** The *procedure* was sound and the parts of it that left artifacts are clean — the
byte-identity check in particular is exemplary evidence work, with all eight bodies retained and every
md5 reproducible. The failure was in the *narrative*: three separate claims in Addendum 41 were written
from the client-side harness's own output and asserted as fact without cross-checking the server log or
the host-guard event stream that were sitting on disk the whole time. The one that matters is B2, because
it is not a slip of arithmetic — it is a causal story that would have shaped the owner's ruling on J-09.
The honest-miss discipline itself held perfectly: the target was not widened, the miss is stated plainly
in bold, the worse stress figure was reported rather than omitted, and the owner-only cap values are
byte-unchanged.

**The replay (TC-7).** Genuine, and I verified it rather than accepting the file. The lane ran at
09:44:25-36 UTC, after `replay-lane.sh` was fixed at 09:21 — so the fixed parser really was the one in
play, and it does parse this spec to `REQUIRED_JOURNEYS=<J-01 J-04 J-10>`. The three screenshots are
distinct 1280×800 captures written 3-4 seconds apart, and they render real data (GRMN / Consumer
Discretionary / 591 symbols; AVB at as-of 2026-08-11 with `$187.94` — the exact value J-10's golden
asserts). The browser-qa LLM agent that later reported `SKIPPED` did so honestly and for the right reason
(services already stopped, nothing new to drive), and did not claim credit for the replay.

**Upstream lanes.** Given this is the first independent audit in three iterations, worth stating plainly:
the reviewer and QA both restated `3,064,772 kB` and `451 + 1,679 = 2,130` verbatim without opening
`logs/backend.log`, where both discrepancies are visible; the reviewer recorded `definition_of_done:
complete` and `issues: []` over a parser change that had introduced a new wrong-answer path. QA's other
work was real — it re-ran the three suites and its numbers match mine.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `incredible_auto_dev/scripts/automation/lib/replay-lane.sh` | `replay_lane_spec_journeys`: parse the label's own markdown bullet when one exists (authoritative), else fall through to the delivered token-skipping scan — removes the inverse silent-wrong-parse (B1). Stale doc comment on `replay_lane_bullet_line` updated. |
| 2 | Important | `incredible_auto_dev/tests/automation/test-replay-lane.sh` | 3 regression assertions reproducing `goal-market-compass-iter-7.md`'s shape: explicit `none` bullet beats later prose; sibling bullet still parses; the legitimate empty does not trip the warning. Suite 81 → 84. |
| 3 | Important | `reports/perf-budgets.md` | Addendum 41: replaced the false "no second engine this round" explanation with an explicit UNEXPLAINED finding (B2); corrected TC-2's request counts against the server log and withdrew the unsupported "server returned 200 for all 39 timeouts" claim (B3/B4); `+9.3%` → `+8.9%` (B5); appended a dated `iter-25 AUDIT CORRECTION` block with citations. Addenda 39/40 and the whole pre-Addendum-41 file remain byte-identical (md5-verified); the file is still a pure append vs HEAD. |
| 4 | Important | `docs/handoffs/goal-market-compass-iter-25-dev.md` | Added an `AUDIT CORRECTION` block at the head of the J-09 measurements section so the three invalidated claims are not quoted from the handoff, and noted that no raw VmPeak artifact survives. |

**Post-fix verification (all run after every change was in place):**

- `bash incredible_auto_dev/tests/automation/test-replay-lane.sh` → `RESULT: 84 passed, 0 failed`
- `bash incredible_auto_dev/tests/automation/test-replay-lane-full.sh` → `=== Results: 24 passed, 0 failed ===`
- `bash tests/automation/test-backend-launch-context.sh` → `=== Results: 18 passed, 0 failed ===`
- `bash -n` clean on `replay-lane.sh`, `test-replay-lane.sh`, `goal-iter-lean.sh`, `browser-qa-phase.sh`
- Old-vs-fixed parser differential over all `docs/phases/*.md`: only the three intended repairs remain
- Call-site pattern under `set -euo pipefail` against iter-25 / iter-24 / iter-7 / malformed specs: all survive; warning fires only on the malformed bullet
- `git diff --numstat HEAD -- reports/perf-budgets.md` → `178 0` (pure append); Addenda 39/40 md5 unchanged
- `git status --porcelain -- config.yaml apps/` → empty (no product or config file touched by this audit)

No pytest was run and no service was started by this audit, per the standing host-resource constraints.

---

## 5. Recommended Next Step

**Proceed to the next iteration** — the spec's DEFINITION OF DONE is genuinely met and both defects I
found are fixed and re-verified. Three things should travel forward:

1. **J-09's number goes to the owner with a caveat, not a conclusion.** The honest miss stands
   (3,064,772 kB vs the 2,621,440 kB target, +16.9%), and the 10.9% improvement over iter-4 is real — but
   its cause is now recorded as unknown, and the figure has no surviving raw artifact. This remains the
   open owner question it always was; nothing this iteration produced should be read as evidence that the
   footprint improved *because of* anything the product did.
2. **Retain raw evidence for the next measurement.** Any future perf addendum should record burst
   start/end in UTC and keep the sampler output alongside the response bodies — the byte-identity check
   already does this correctly and is the model to copy. Had the VmPeak sampler done the same, none of
   B2/B3/B6 would have been open questions.
3. **Two carried-forward items for the owner, neither blocking:** whether a declared journey set that
   parses to zero should *block* the lane rather than warn (T4), and J-01's golden replay script, whose
   assertions are much weaker than the journey it certifies (T2) — worth strengthening the next time a
   slice legitimately touches J-01.

Per the spec's own NOTES, the suggested order after this is J-05/J-06 (freeze/integrity pair) then
J-07/J-08 (surface pair). Nothing found here changes that order.
