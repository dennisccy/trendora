# Phase goal-ops-hardening-iter-30 — What to Click

**Status:** N/A — Backend-only phase. No UI verification steps.

This iteration bounds RAM accumulators inside `compute_forward_aggregates` (a backend engine function) and adds a backend config knob. It does not add, remove, or change any page, route, button, form, or displayed value. The existing `/backtest` and `/research/factor-lab` pages are asserted byte-identical to their pre-iteration behavior by this iteration's own tests.

If you want to sanity-check that nothing broke, open `/research/factor-lab` and `/backtest` in a browser and confirm they load and render numbers as before — but this is a regression spot-check of pre-existing pages (covered by the functional test plan's TC-05), not a verification of new work from this iteration.
