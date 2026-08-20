# Project story so far

Trendora is a research tool for a stock-market investor. This chapter is teaching it to open each evening with a short, honest "Today" briefing instead of a plain dashboard.

## How it has grown

Before this chapter began, Trendora was already a solid research platform — untouched throughout. Early rounds gave every stock a real sector label instead of "Unassigned," then built the daily briefing's heart: a plain-English market read, a "what changed" list, and a "next-session focus" watch-list with plain reasons and honest why-not notes for each candidate.

The next round locked each evening's briefing into a permanent, tamper-evident "Manifest" record listing every near-miss stock and why it missed. After that, the team paused new features for one round to protect the shared computer Trendora runs on, cutting the backend's peak memory by a real 29% — not quite to target, so the owner still needs to weigh in.

Then an accident happened. While rehearsing a data-recovery drill, an earlier round accidentally and permanently deleted two days of stock prices (August 11 and 12) that could not be put back. The team disclosed this openly and built a careful, fenced-off repair tool that works out exactly which prices are missing and refuses, in code, to touch anything outside that exact gap. This round used the tool for real, asking the data supplier (Stooq) for precisely those two days back. The tool did everything right, but Stooq has started blocking automated downloads with a "prove you're human" puzzle, so the download failed cleanly and nothing was restored — and nothing else was damaged either; the team checked the whole database byte-for-byte to make sure. Because those two days are still missing, the "what changed" list and plain-English summary are temporarily unreliable for the newest dates, though the code behind them still works correctly. The plan now is to retry with a second supplier, Yahoo, adding a check that its prices are recorded the same way as the ones already stored.

## What it can do today

The rest of Trendora — the scanner, sector and theme views, backtesting, and methodology reference — works exactly as before. Every stock shows its real sector instead of "Unassigned," and next-session candidate cards explain why each stock was picked and why others were not. The home page also carries a sealed "Manifest" card proving each day's briefing was locked and time-stamped. The plain-English summary and "what changed" list are temporarily unreliable for the newest two dates while the price-data repair is in progress. Still missing: live proof a real close seals a fresh record, the page's final layout, and a dedicated Market page.

_Last updated: 2026-08-20 after iteration 6._
