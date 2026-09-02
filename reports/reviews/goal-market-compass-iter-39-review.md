**Verdict:** PASS

```yaml
phase: goal-market-compass-iter-39
date: 2026-09-02
reviewer: reviewer
summary: |
  Root-cause AG-8 fix: why_not_totals/reason/cap_rank/cap made optional in api.ts, with a new
  pure whyNotSummary() helper (why-not-summary.ts) guarding the "Not priority" disclosure string
  in compass-focus-section.tsx, exactly matching the spec's required degraded/full-count strings.
  Backend untouched (confirmed correct per spec). Journey scripts J-04..J-07 independently
  verified byte-exact to ab3cca63 (git diff empty). Independently re-ran: new fixture test
  (6/6 pass, exact-string asserts), tsc --noEmit (clean), backend why_not fixtures (2/2 pass).
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues: []
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
