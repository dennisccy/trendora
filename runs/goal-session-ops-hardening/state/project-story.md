# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals. This chapter tracks making the running app itself trustworthy day to day — fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest, added a live status badge, fixed a cluster of low-memory crashes, and returned the team to a fuller review process. Iteration 59 proved the Regime Lab page can no longer crash under memory pressure, and iterations 60-61 brought seven of the product's eight promises to fully passing after fixing a timezone mix-up. Iteration 62 ran the project's first real rehearsal of its trickiest promise — staying fast to respond during a genuine 15-minute background job — and found cracks in the checking tools themselves; iteration 63 fixed one of those cracks but slow replies still rose for an unexplained reason; iteration 64 fixed the test's own practice-date problem and confirmed the slow-reply pattern was real.

Iteration 65 measured the heavy job four different ways and, honestly, found no single place where the app pauses. Iteration 66 profiled a different step, again found nothing to bound, but fixed a real double-logging bug (a resumed data-import job used to log itself twice; now it logs once) and built one shared stopwatch every test now uses — which then delivered the worst news yet: about 7 in 100 health checks were briefly slow during one specific calculation step.

Iteration 67 changed tactics: rather than testing that step in isolation again, the team built a small hidden instrument inside the running app to watch a real health request as it actually happens, and ran it during a genuine 18-minute background job plus a no-job control run. The instrument found something real — the app's own request-handling briefly slows during heavy background work, measurably more than when idle — but that only explains about a tenth of the one slow reply seen this round. Most of the delay is still hiding somewhere the instrument doesn't reach, inside the health check's own calculation work, which the team is aiming at next. Seven of the product's eight promises pass fully; the eighth — staying fast to respond during heavy background work — stays partly done, closer to understood but not yet closed.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools, always with an honest status message while the backend starts up. Backfills accept any date range with no hidden cap and explain when there's nothing new to fetch. Backtest results load instantly from storage, pages fetch only what they need, and the app discloses when it's crunching numbers in the background. The Data Manager page stays current on its own and no longer double-logs an interrupted, resumed job. The Regime Lab page holds up under heavy load. The app almost always answers its own health check quickly even during its biggest background job, with only a rare, brief slow reply still being tracked down.

_Last updated: 2026-08-12 after iteration 67._
