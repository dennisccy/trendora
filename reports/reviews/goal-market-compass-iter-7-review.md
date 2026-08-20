**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-market-compass-iter-7
date: 2026-08-20
reviewer: reviewer
summary: |
  Swaps RECOVERY_SOURCE to "yahoo" and adds J-10 step 2a's fail-closed adjustment-convention
  gate (check_adjustment_convention + run_gated_recovery) in the same module, plus the
  additive YahooProvider.get_adjusted_close capability (correct adjclose field, not raw
  quote.close). Verified by code read: no path reaches run_bounded_recovery_fetch/backfill on
  any non-"agree" verdict, and any exception escaping the provider call (caught as
  ProviderUnavailableError->inconclusive, or uncaught) propagates out before the fetch/backfill
  lines are ever reached - genuinely structural, not conventional. Real run against live DB
  returned "mismatch" (CVX ~0.865%>0.75% tolerance) and made zero writes; independently
  reconfirmed via direct read-only SQL (daily_prices/data_provider_runs/scanner_runs/
  next_session_manifests all unchanged; MAX(id)=541 same row as iter-6; DB file mtime predates
  the check). 23/23 new+updated tests and 44/44 provider-client regression tests pass (ran both
  myself). No scope creep (git status matches packet exactly), no interchangeability claims
  (grep-verified, only correct disclaimers), iter-6 evidence byte-unchanged (git diff clean),
  depth-dispatched=full, correct branch, tolerance not loosened after a borderline result.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: MINOR
    file: apps/backend/app/data_providers/yahoo_provider.py
    line: 135
    category: tests
    summary: _parse_adjusted_close's own branches (chart error, missing result, empty timestamp, missing adjclose block, malformed shape, null skip) have no synthetic-payload unit test; test_j10_recovery.py's fakes bypass real parsing entirely, leaving only a one-time non-repeatable live probe as evidence this exact logic works
    fix: add get_adjusted_close analogs of test_provider_clients.py's existing test_yahoo_error_payload_raises / test_yahoo_skips_null_price_rows_never_fabricates pattern
standards:
  state_transitions_server_side: pass
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
