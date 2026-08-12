# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals. This chapter tracks making the running app itself trustworthy day to day — fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest, added a live status badge, fixed a cluster of low-memory crashes, and returned the team to a fuller review process. Iteration 59 proved the Regime Lab page can no longer crash under memory pressure, and iterations 60-61 brought seven of the product's eight promises to fully passing after fixing a timezone mix-up.

Iteration 62 rehearsed the product's trickiest promise — staying fast to respond during a genuine 15-minute background job — and found cracks in the checking tools themselves; iterations 63-64 fixed those cracks and confirmed the slow-reply pattern was real.

Iteration 65 measured the heavy job four different ways and, honestly, found no single place where the app pauses. Iteration 66 fixed a real double-logging bug in the Data Manager's resumed jobs and built one shared stopwatch every test now uses — which then delivered the worst news yet: about 7 in 100 health checks were briefly slow during one specific calculation step.

Iteration 67 changed tactics: rather than testing that step in isolation again, the team built a small hidden instrument inside the running app to watch a real health request as it actually happens, run during a genuine 18-minute background job plus a no-job control run. It found the app's own request-handling briefly slows during heavy background work, measurably more than when idle — but that only explained about a tenth of the one slow reply seen that round. Most of the delay was still hiding inside the health check's own calculation work.

Iteration 68 aimed the same instrument at exactly that hiding place, adding a third stopwatch inside the health check's own body. For the first time, it named where most of a slow reply goes: about four-fifths of it. The team also finally ran a test file for that same code that had been skipped the round before, and it passed cleanly (17 of 17). The health check still occasionally answers slowly during the app's heaviest background work — ten times out of 1,609 checks this round, the app itself never went down or errored — so the last of the product's eight promises stays partly, not fully, done. But the team can now point at a specific piece of code instead of a vague slowdown, and the next round will pin down exactly which part of that code is slow.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools, always with an honest status message while the backend starts up. Backfills accept any date range with no hidden cap and explain when there's nothing new to fetch. Backtest results and other aggregates load instantly from storage, pages fetch only what they need, and the app discloses when it's crunching numbers in the background. The Data Manager page stays current on its own and no longer double-logs an interrupted, resumed job. The Regime Lab page holds up under heavy load. The app answers its own health check quickly almost all of the time even during its biggest background job, with a rare, brief slow reply now mostly named and being tracked down to its exact source.

_Last updated: 2026-08-12 after iteration 68._
