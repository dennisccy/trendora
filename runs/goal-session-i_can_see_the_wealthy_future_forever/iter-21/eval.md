**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

# Iteration 21 Evaluation

## Summary

J-33 (selectable, key-aware import provider source) was **built** and its catalog / availability / source-threading / session-key-field / explicit-error / J-17 / J-18 machinery all work (browser QA 12/13, full backend suite 502 passed / 4 skipped). **But QA and browser QA both returned FAIL on a verified breach of the iteration's PRINCIPAL anti-goal:** a pasted **session-only API key is echoed back** in `GET /api/data/jobs/{id}` (`errors[]`) and rendered in the `/data` job card. I confirmed the root cause and its containment in source. The leak is **contained and non-durable** (the key is reflected only to the same user's own transient in-memory job-status; nothing is persisted — DB / run-history / logs / committed files / `GET /api/data` all clean), so it is a **minor-severity, non-halting** violation → **CONTINUE** (not a REGRESSION-class critical), but it is a **hard blocker**: J-33 is recorded **partial** (not passing) and this unresolved violation vetoes any future GOAL_ACHIEVED until fixed.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| **J-33** | failing (unbuilt) | **partial** | Built; 12/13 browser tests PASS, **1 FAIL (UT-08 P1, principal anti-goal)** — key echoed in `GET /api/data/jobs/{id}` + job card. `UT-08-FAIL-key-leak-in-job-card-errors.png`; QA FAIL (TC-05/07/11) |
| J-17 (req-still-passing) | passing | **passing** (re-verified) | `…-iter-21-ui-test-results.md#UT-10` — backfill ran end-to-end (status ok, 5 snapshots/5 dates, 3200 fwd returns); source-selectable change preserved J-17 |
| J-18 (req-still-passing) | passing | **passing** (re-verified) | `#UT-13` — exactly ONE date `<select>` app-wide; new source/key controls add no date state; coherence Step 3 PASS |
| J-01–J-16, J-19–J-21, J-25–J-32 (carried) | passing | **passing** (carried) | iter-21 diff touches only the provider package + `/data` + config — zero change to scoring/scanner/regime/patterns/buckets/forward_testing/research/snapshot_serving or the /stocks·/backtest·/research pages; no DB regen; full suite 502 green → cannot regress |
| J-22, J-23, J-24 (data-walled) | failing | **failing** (NON-HALTING/NON-VETOING) | Honestly blocked (NA) per re-scoped goal.md; not re-probed (spec forbids). J-22 auto-unblocks via the J-35 path |
| J-34, J-35 | failing | **failing** (out of scope; iter-22 / iter-23) | Explicitly deferred by the iter-21 spec; diff git-confirms no resume/expand machinery added |

**Board: 29 passing (J-01–J-21, J-25–J-32) / 1 partial (J-33) / 5 failing (J-22/23/24 data-walled + J-34/35 unbuilt-next).**

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| **Import keys are env-or-session, never persisted (never echoed back in any response)** — PRINCIPAL | **🔴 VIOLATED (minor / non-halting / unresolved)** | Pasted key echoed in `GET /api/data/jobs/{id}` `errors[]` + job card. Root cause `_http.py:42` wrapping `str(httpx.HTTPStatusError)` (key in URL query: tiingo:46/finnhub:53/alpha_vantage:51). **Contained**: not persisted (DB/run-history/log/committed/`GET /api/data`/FE-storage all clean — `_persist_run` writes only counts + summary). Blocks J-33; vetoes GOAL_ACHIEVED until fixed. |
| Exactly one date selector | OK (held — was THE watch risk) | UT-13: exactly 1 date `<select>`; new source/key controls add no date state; coherence Step 3 PASS |
| No fabricated data / Live fetch is real-data-only | OK | Walled fetch → explicit `failed`/`partial`, **0 bars fabricated** (live tiingo bars=0, yahoo bars=0); every client raises `ProviderUnavailableError`, never a placeholder bar |
| No secrets in source | OK | No hardcoded key/token; provider keys read from env-var NAME (config) or the session paste; `compute_provider_availability` emits the env-var name + boolean only |
| No magic numbers | OK | Provider catalog + job limits in `config.yaml`; `data_providers/` I/O timeout is excluded from the calc no-magic-numbers contract (mirrors `stooq`) |
| Single source of truth / No recompute in read path | OK | Coherence PASS — `compute_provider_availability` is the only producer, `GET /api/data` the only serving path; no canonical value recomputed; FE renders `data.sources` verbatim |
| Snapshots immutable / No-lookahead / Risk-Off gates Actionable | OK | No DB regen — scoring/snapshot/forward paths git-untouched |

Coherence: **COHERENCE-PASS** (no structural veto).

## Next-Step Recommendation

**iter-22 — full depth — FIX-FIRST consolidation, then J-34.** The key-leak fix is mandatory and gates both J-33→passing and J-34 (J-34's chunked import threads the same source/key and surfaces *richer* per-chunk errors → it will inherit the same leak unless `_http.py` is sanitized first).

1. **Fix the leak (gates J-33 passing).** In `data_providers/_http.py`, build the error message from a redacted URL + status (`exc.request.url.copy_with(query=None)` + `response.status_code`) instead of raw `str(exc)`; and/or send provider keys via an `Authorization`/token **header** rather than a URL query param where supported; and/or scrub the resolved key value out of any error string. Treat job error strings as untrusted-for-secrets before they enter `JobProgress.errors`/responses.
2. **Close the test blind spot.** Add a unit/integration test driving a **real** `httpx.HTTPStatusError` (key in URL) through `get_daily` → `JobProgress.errors` → `to_dict()` and asserting the sentinel key is **absent** from `errors[]` and `GET /api/data/jobs/{id}`. The existing `test_pasted_api_key_never_persisted` uses a *mocked* provider raising a sanitized error — that is exactly why the 502-green suite missed this.
3. **Re-run browser QA UT-08** to confirm the job card no longer renders the key.
4. **Then build J-34** (chunked / durable-checkpoint / resumable / 429→backoff→Resume) on the now-safe source foundation, full depth, with an injected provider scripted to raise 429 after K symbols (no live network call). Sequence J-35 (Expand-universe, auto-unblocks J-22) at iter-23.
5. **Fold in the non-blocking nits** while touching `/data`: Finding #2 (backfill header shows defaulted `yahoo` instead of omitting the source segment — don't default `source` for non-fetch kinds, or suppress the header segment); substitute the dev handoff's `__PYTEST_RESULT__` placeholder; align the blueprint name (`ProviderCatalogCfg` → `ProviderCatalogEntry`); revert the `tsconfig.json` cosmetic churn.

**Strategic:** after J-33 is fixed (passing) and J-34/J-35 land green offline, GOAL_ACHIEVED is reachable on the buildable set (32/32 buildable), with J-22/23/24 + the live-fetch *outcome* recorded honestly as NA / non-halting. Do NOT autonomously re-probe J-22/J-23/J-24.

## Halt Justification (if halting)

Not halting. **CONTINUE** — clear, tractable, autonomous next work (fix the contained key-leak + close the test gap, then J-34/J-35). This is **not REGRESSION**: no previously-passing journey regressed (the 29 carried journeys' paths are git-untouched, no DB regen, full suite 502 green), and the anti-goal violation is minor/contained/non-durable (same-user transient reflection, nothing persisted/external/committed) rather than a critical committed-secret/backdoor class that warrants a human-review halt. It is **not STALLED** (the fix and the remaining journeys are well-specified and offline-buildable) and **not ESCALATE** (already full depth). It is **not GOAL_ACHIEVED** (J-33 partial + J-34/35 unbuilt + an unresolved anti-goal violation).
