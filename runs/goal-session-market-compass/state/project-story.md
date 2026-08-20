# Project story so far

Trendora is a research tool for a stock-market investor. This chapter is teaching it to open each evening with a short, honest "Today" briefing instead of a plain dashboard.

## How it has grown

Before this chapter began, Trendora was already a solid research platform, untouched throughout. Early rounds gave every stock a real sector label instead of "Unassigned," then built the daily briefing's heart: a plain-English market read, a "what changed" list, and a "next-session focus" watch-list with plain reasons for each candidate. The next round locked each evening's briefing into a permanent, tamper-evident "Manifest" record. After that, the team spent one round shrinking the backend's memory use by 29% to protect the shared computer Trendora runs on — not quite to target, so the owner still needs to weigh in.

Then an accident happened: rehearsing a data-recovery drill accidentally and permanently deleted two days of stock prices (August 11 and 12). The team disclosed this openly and built a fenced-off repair tool that works out exactly which prices are missing and refuses, in code, to touch anything else. The first live attempt asked the original supplier, Stooq, for the two days back, but Stooq now blocks automated downloads with a "prove you're human" puzzle, so that attempt failed cleanly — nothing restored, nothing else damaged.

This round switched the repair tool to a second supplier, Yahoo, and added a new safety check: before writing anything back, compare a sample of Yahoo's prices against what Trendora already stores, to confirm the two suppliers record prices the same way. Run for real on 88 genuine comparisons, the check found one stock (Chevron) just outside the allowed tolerance and — honoring its own rule never to loosen the bar after a near-miss — refused to write anything, so the two days are still missing. The team's independent reviewer then found and fixed, before it ever touched real data, a flaw in that very check: it would have wrongly said "these match" if it had compared nothing at all. The owner has now redesigned the check to compare how prices move over time rather than their raw level, and the next round builds that redesign and tries again.

## What it can do today

The rest of Trendora — the scanner, sector and theme views, backtesting, and methodology reference — works exactly as before. Every stock shows its real sector instead of "Unassigned," and next-session candidate cards explain why each stock was picked and why others were not. The home page carries a sealed "Manifest" card proving each day's briefing was locked and time-stamped. The plain-English summary and "what changed" list stay temporarily unreliable for the newest two dates while the price-data repair continues. Still missing: live proof a real close seals a fresh record, the page's final layout, and a dedicated Market page.

_Last updated: 2026-08-21 after iteration 7._
