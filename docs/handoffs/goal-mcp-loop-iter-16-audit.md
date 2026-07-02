# goal-mcp-loop-iter-16 Audit Report

**Date:** 2026-07-02
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal — land provider-routed, resumable, honestly-failing staged-ingest tooling plus a
staged-data validation suite with ZERO runtime change — was genuinely achieved on the spec's
explicitly sanctioned probe-hard-failure branch. Every load-bearing claim was independently
re-verified during this audit (test counts re-run, tier counts recomputed, byte-identity
re-diffed, the live Stooq probe re-executed and reproducing the exact documented `Access denied`
ACL, and the skipping validation suite proven to pass on a good synthetic tree and catch five
planted violations). One IMPORTANT defect was found and fixed during the audit: a set
`STOOQ_API_KEY` would have been persisted into the committed staging manifest (and printed) on
any HTTP-status failure — booby-trapping the coverage manifest's own sanctioned unblock path.
The remaining gaps (the staged 30-year asset does not exist; human decision required) are the
spec's sanctioned honest-partial outcome, documented everywhere, with J-10..J-13 correctly held
`unknown`.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): `STOOQ_API_KEY` was persisted into the committed staging manifest on HTTP-status failures**
`_StooqVerifyClient` carries the env key as a client-level query param
(`apps/backend/scripts/ingest_seed.py:290-292`), and httpx `HTTPStatusError` messages embed the
FULL request URL including that param. `StooqProvider.get_daily` wraps the message verbatim
(`apps/backend/app/data_providers/stooq_provider.py:71-74`), and the ingest recorded it via
`record_cap`/`record_absent` into `meta.json` `cap_events[].detail` / `failures[].detail` — a
file the spec instructs to COMMIT — and printed it to console (which flows into handoffs).
**Empirically confirmed** with a MockTransport 401: the key appeared verbatim in `meta.json`.
This directly violates the spec's "read `STOOQ_API_KEY` from the environment only (never
persisted, never committed)", the critical anti-goal, and the coverage manifest §6(b)'s promise
to the operator ("never committed; the tool already carries it request-only") — i.e. the exact
sanctioned resume scenario would have leaked the sanctioned key.
**Fix applied:** `redact_stooq_key()` (`scripts/ingest_seed.py:197-208`) strips the env-key value
and any `apikey=<...>` query value; applied at the persistence choke points
(`record_absent`/`record_cap`, lines 228-235) and the three provider-error print sites
(lines 517-518, 529-530, 586). Regression test added
(`tests/test_ingest_seed.py:261-283`, `test_key_redacted_from_manifest_and_output_on_failure`)
asserting the key never reaches `meta.json` or stdout while the redacted evidence
(`apikey=***`) is kept. Leak re-check after fix: key absent from manifest and output.

**B2 — GAP (documented, not fixed): unbounded proof-of-work loop on a hostile/changed challenge page**
`_solve_stooq_pow` (`scripts/ingest_seed.py:275-280`) iterates until the served difficulty is
met with no iteration cap; the difficulty is attacker/vendor-controlled
(`_STOOQ_CHALLENGE_RE`, line 272). Observed live difficulty is 4 (~0.03 s), but a changed page
serving d=8+ would spin the CPU for hours before any fetch. Mitigation: this is a manually-run
dev tool (Ctrl+C works; `run_stooq_ingest` even converts KeyboardInterrupt into a resumable
stop, line 548-552). Non-blocking; recommend a difficulty/iteration cap whenever this script is
next touched.

**B3 — OBSERVATION: the front-door handshake client is a scope judgment call — honestly surfaced, and it strengthened the evidence**
The spec authorized routing via the existing `StooqProvider` + optional env key; it did not
anticipate `_StooqVerifyClient` (`scripts/ingest_seed.py:283-308`) solving Stooq's JS
browser-verification proof-of-work. Assessment: the challenge is served to every visitor, is
neither a captcha nor a credential, and the endpoint's actual authorization decision behind it
is honored unchanged — verified live during this audit: the probe reproduces `Access denied`
(the post-handshake ACL body; without the handshake the body would be the challenge HTML), and
the tool stops honestly with exit 2, staging nothing. Without the handshake the blocker
diagnosis would have been ambiguous ("requires JavaScript" vs the real export ACL). The dev
handoff discloses the mechanism and offers a removal path; the final call belongs to the human
operator, as the handoff itself states. No anti-goal violated; no evasion of the access decision.

**B4 — OBSERVATION: `make_provider("stooq")` letter-vs-spirit deviation is sound**
DoD item 1 says "via `make_provider`"; the script constructs
`StooqProvider(client=_StooqVerifyClient(...))` directly (`scripts/ingest_seed.py:312-320`).
Verified: `make_provider("stooq")` is literally `StooqProvider()` with no client parameter
(`app/data_providers/__init__.py:66-69`), so the literal factory could not carry the injected
client without an `app/**` change the spec forbade. Same provider class, endpoint, `.us`
mapping, and real-data-only contract — the spirit (reuse the existing provider layer) is fully
met and the deviation is documented in `make_stooq_provider`'s docstring.

**B5 — OBSERVATION: probe stages CSVs before its final header check**
`run_probe` writes the three CSVs, then validates the staged header
(`scripts/ingest_seed.py:627-634`); on that structurally-impossible failure (DictWriter always
emits `CSV_FIELDS`) files would remain despite the NO-GO wording, with no manifest — a state the
next run self-heals (no manifest → re-fetch). Unreachable in practice; no action.

**B6 — OBSERVATION: resume-skip semantics verified correct**
The skip condition (manifest-ok + CSV exists, `scripts/ingest_seed.py:494-500`) does not
re-check "reaches the pinned end" per-file — and that is the *correct* design: the pinned window
is enforced by `resolve_stooq_window` (lines 169-211, conflicting windows refused), so every
ok-recorded symbol was fetched over the same shared bound; a naive `last == end` check would
re-fetch delisted names forever. Also confirmed: `most_recent_completed_trading_day`
(lines 147-153) is weekday-only — already disclosed in the handoff's Known Issues; harmless
since the pinned end only bounds the shared window.

### Frontend Findings

None — `Frontend Present: no`. Verified byte-identical: `apps/frontend/**`,
`apps/backend/app/**`, `config.yaml`, and BOTH evidence ledgers (`git diff` empty on all
protected paths, re-checked after audit fixes). The blueprint diff is exactly the additive
J-10..J-13 homes rows + the iter-16 internal-asset clarification the spec prescribes
(`runs/goal-session-mcp-loop/state/blueprint.md:78-81, 208`) — decomposer-authored, no
nav-skeleton change.

### Test Findings

**T1 — OBSERVATION (verified): claimed counts all reproduce**
Re-run during audit: `test_ingest_seed.py` 21 passed (20 dev + 1 audit-added);
`test_seed_staged_30y.py` 7 skipped with the stated probe-blocked reason; the five DoD suites
UNEDITED (`git diff` empty) → 44 passed + 1 skipped (the pre-existing live-integration stooq
test, honestly skipping under the same documented gate); `test_staging_ledger_routing.py`
UNEDITED → 19 passed. Pool plan recomputed against the committed config: tier1=40 (index ETFs
lead: SPY/QQQ/IWM/RSP), tier2=122, tier3=426, total 588; default set 158; pool CSV 548 — every
number in the handoff/coverage manifest is exact.

**T2 — OBSERVATION (verified): the skipping validation suite is genuinely load-bearing, not skip-theater**
The handoff's executability claim was only asserted, so this audit proved it independently
against synthetic staged trees (module-global override; the repo's real
`data/seed-stooq-30y` path was never created): all 7 validations PASS on a good tree, and each
planted violation is caught precisely — fabricated NVDA 1996 depth
(`tests/test_seed_staged_30y.py:122-126`), an unadjusted AAPL 4:1 seam (-74.15% flagged,
lines 142-153), manifest bar-count drift (lines 191-217), a pre-listing COIN row
(lines 129-139), and a +10% cross-vendor basis drift (lines 156-188). The suite will genuinely
gate the staged asset the moment it lands.

**T3 — IMPORTANT (fixed, part of B1): the "never persisted" assertion had a coverage hole**
`test_env_key_client_injection_never_persisted` (`tests/test_ingest_seed.py:241-257`) asserted
key *construction* (request-only param) but never exercised the failure-*persistence* path — the
one place the key actually escaped. The audit-added regression test (lines 261-283) closes the
hole.

**T4 — OBSERVATION: dev-handoff arithmetic slip corrected**
The handoff's DoD-suite total read "64 passed" (the reviewer's MINOR finding: the +20 delta was
`test_ingest_seed.py` double-counted). No dev retry ran (PASS_WITH_NOTES), so the prescribed
one-line correction was never applied; this audit applied it
(`docs/handoffs/goal-mcp-loop-iter-16-dev.md:162-164`, now "44 passed, 1 skipped" with
attribution). QA's numbers were already correct.

---

## 3. Domain Assessment

The core domain logic of this iteration is data-honesty machinery, and it is correct:

- **No fabrication anywhere.** Atomic CSV writes (tmp+rename, `scripts/ingest_seed.py:362-373`)
  make a partial row impossible; empty series and `N/D` bodies are recorded absences that never
  produce a file; the provider's real-data-only contract (`ProviderUnavailableError` on any
  failure) is preserved unchanged. Verified nothing was staged: `data/` holds only `seed/` and
  the DB; the audit's own probe re-run staged nothing on NO-GO.
- **The honest-blocked outcome is real, not narrative.** The live probe re-executed during this
  audit reproduced the handoff's evidence exactly: handshake completes, then the CSV export
  endpoint answers `Access denied` from the first request → NO-GO, exit 2. This matches the
  iter-3 lesson recorded in `config.yaml` and satisfies External Integration Testing
  (anti-pattern #15) the right way — a real-system check with the blocker documented, never
  papered over.
- **Failure taxonomy and resume semantics are sound** (per-symbol absence vs whole-run gate;
  manifest rewritten after every symbol; pinned-window reuse with conflicting windows refused;
  the clobber guard refusing a non-stooq `--out`). The Yahoo default path was diffed against
  `git show HEAD:` line-by-line: same symbol construction, retry loop, meta shape, prints —
  unregressed (and pinned by `test_yahoo_path_unregressed_writes_live_layout`).
- **Ledger discipline held:** zero referee submissions, both ledgers byte-identical, no test
  pins refreshed — so J-01/J-02/J-05/J-09 (and J-03/04/06/07/08) non-regression follows from
  the zero-app-diff argument the spec prescribes, with all unedited suites green.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/scripts/ingest_seed.py` | Added `redact_stooq_key()` (lines 197-208) and applied it at the manifest persistence choke points (`record_absent`/`record_cap`, lines 228-235) and the three provider-error print sites (lines 517-518, 529-530, 586) so a set `STOOQ_API_KEY` can never be persisted into the committed `meta.json` or printed (empirically confirmed leaking before the fix, clean after). |
| 2 | Important | `apps/backend/tests/test_ingest_seed.py` | Added `test_key_redacted_from_manifest_and_output_on_failure` (lines 261-283) + `httpx` import — regression-pins the redaction (key absent from manifest and stdout; redacted `apikey=***` evidence retained). Suite now 21 passed. |
| 3 | Minor | `docs/handoffs/goal-mcp-loop-iter-16-dev.md` | Applied the reviewer-prescribed arithmetic correction: DoD-suite total "64 passed" → "44 passed, 1 skipped" (verified by audit re-run), with attribution. |

Post-fix verification: `test_ingest_seed.py` + `test_seed_staged_30y.py` +
`test_stooq_provider.py` → 29 passed, 8 skipped; DoD suites 44 passed + 1 skipped;
`test_staging_ledger_routing.py` 19 passed; protected paths still byte-identical.

---

## 5. Recommended Next Step

Proceed to close this iteration as the spec's sanctioned honest-partial outcome (evaluator
guidance in the spec: CONTINUE with the escalation surfaced, no journey flips; J-10..J-13 stay
`unknown`). **iter-17 (atomic swap + sanctioned ledger reset) must NOT be scheduled until the
human operator resolves the blocker** via one of the coverage manifest §6 options: (a) run the
probe + pool fetch from a network Stooq's export ACL accepts, (b) provide a sanctioned
`STOOQ_API_KEY` via the environment (now safe against persistence thanks to fix #1), or
(c) amend `docs/goal.md`'s provider choice. When the fetch eventually runs, the staged suite
activates automatically and must be green before the asset is committed. Minor follow-up for
whenever the script is next touched: cap `_solve_stooq_pow` iterations (B2).
