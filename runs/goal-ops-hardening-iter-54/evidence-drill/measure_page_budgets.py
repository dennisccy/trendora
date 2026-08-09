"""TC-16 (ops-hardening iter-54, J-06) -- per-page time-to-interactive + on-load API latency, warm
backend in prod mode, for every nav-listed page.

Adapted from the iter-52 audit-fix pass's `measure_j06_tti.py` (single-page) -- generalized to loop over
ALL 11 nav-listed pages named by the iter-54 spec's TC-16:
  /  /stocks  /stocks/AAPL  /sectors  /themes  /data  /evidence  /scanner-runs  /backtest  /watchlist
  one /research lab (regime-lab, matching the existing J-06.json golden's own choice)

Plus the market-phase retrospective sub-view (see the dev handoff for why this is NOT a standalone
`/research/market-phase-retrospective` ROUTE -- no such page exists in the frontend; the retrospective is
a toggle sub-view inside `market-phase-card.tsx`, rendered only on `/` -- so it is measured as a follow-up
interaction on `/` rather than a 12th page navigation).

For each page: navigation-timing marks (domInteractive / domContentLoadedEventEnd / loadEventEnd), the
wall-clock to the page's own anchor text becoming visible ("content_visible_ms" -- the honest TTI figure
for a client-rendered page), whole-page `networkidle_ms`, and every on-load API request's own resource
timing.

Usage: measure_page_budgets.py <frontend_url> <out_json>
"""
import json
import sys
import time

from playwright.sync_api import sync_playwright

FRONTEND = sys.argv[1].rstrip("/")
OUT = sys.argv[2]

PAGES = [
    {"path": "/", "anchor": "Dashboard"},
    {"path": "/stocks", "anchor": "Stocks"},
    {"path": "/stocks/AAPL", "anchor": "AAPL"},
    {"path": "/sectors", "anchor": "Sectors"},
    {"path": "/themes", "anchor": "Themes"},
    {"path": "/data", "anchor": "Data Manager"},
    {"path": "/evidence", "anchor": "Evidence"},
    {"path": "/scanner-runs", "anchor": "Scanner Runs"},
    {"path": "/backtest", "anchor": "Backtest"},
    {"path": "/watchlist", "anchor": "Watchlist"},
    {"path": "/research/regime-lab", "anchor": "Research — Regime Lab"},
]


def measure_page(browser, spec, warm_first=False):
    if warm_first:
        # exclude a dev-server / first-compile artefact from the measured run (mirrors measure_j06_tti.py)
        wctx = browser.new_context()
        wp = wctx.new_page()
        wp.goto(f"{FRONTEND}{spec['path']}", wait_until="networkidle", timeout=180_000)
        wctx.close()

    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    api_calls = []

    def on_response(resp, _calls=api_calls):
        if "/api/" in resp.url:
            _calls.append({"url": resp.url, "status": resp.status})

    page.on("response", on_response)

    t0 = time.monotonic()
    page.goto(f"{FRONTEND}{spec['path']}", wait_until="domcontentloaded", timeout=120_000)
    page.get_by_text(spec["anchor"]).first.wait_for(state="visible", timeout=120_000)
    content_visible_ms = (time.monotonic() - t0) * 1000.0

    try:
        page.wait_for_load_state("networkidle", timeout=60_000)
    except Exception:
        pass  # a page with an open poll (e.g. the readiness badge) may never go fully idle -- best-effort
    networkidle_ms = (time.monotonic() - t0) * 1000.0

    nav = page.evaluate(
        "() => { const n = performance.getEntriesByType('navigation')[0]; return n ? {"
        "domInteractive: n.domInteractive, domContentLoadedEventEnd: n.domContentLoadedEventEnd,"
        "loadEventEnd: n.loadEventEnd, duration: n.duration} : null; }"
    )
    api_timing = page.evaluate(
        "() => performance.getEntriesByType('resource')"
        ".filter(r => r.name.includes('/api/'))"
        ".map(r => ({name: r.name, duration: r.duration, startTime: r.startTime}))"
    )
    result = {
        "path": spec["path"],
        "nav_timing_ms": nav,
        "content_visible_ms": round(content_visible_ms, 1),
        "networkidle_ms": round(networkidle_ms, 1),
        "api_requests": api_calls,
        "api_resource_timing_ms": api_timing,
    }
    print(f"[page-budgets] {spec['path']}: content_visible={content_visible_ms:.1f}ms "
          f"networkidle={networkidle_ms:.1f}ms api_calls={len(api_calls)}", flush=True)
    return ctx, page, result


results = []
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)

    for i, spec in enumerate(PAGES):
        ctx, page, result = measure_page(browser, spec, warm_first=(i == 0))
        if i == 0:
            page.screenshot(path=OUT.replace(".json", f"-{spec['path'].strip('/').replace('/', '_') or 'home'}.png"))
        ctx.close()
        results.append(result)

    # ---- retrospective sub-view (see module docstring: no standalone route exists) ----
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    api_calls = []
    page.on("response", lambda resp, _c=api_calls: _c.append({"url": resp.url, "status": resp.status})
            if "/api/market-phase" in resp.url else None)
    page.goto(f"{FRONTEND}/", wait_until="domcontentloaded", timeout=120_000)
    page.get_by_text("Dashboard").first.wait_for(state="visible", timeout=120_000)
    try:
        page.wait_for_load_state("networkidle", timeout=60_000)
    except Exception:
        pass
    # iter-54 fix: the dashboard now nests the full market-phase card (and its retrospective toggle)
    # behind a "More detail" accordion (a layout change since this script was authored in iter-52) --
    # expand it first, a no-op if the accordion is already open / the toggle is already visible.
    try:
        more_detail = page.get_by_text("Market Phase detail", exact=False).first
        if more_detail.is_visible(timeout=5_000):
            more_detail.click(timeout=5_000)
    except Exception:
        pass
    toggle = page.get_by_text("Show retrospective", exact=False).first
    t0 = time.monotonic()
    toggle_found = False
    try:
        toggle.wait_for(state="visible", timeout=15_000)
        toggle_found = True
        toggle.click(timeout=10_000)
        page.wait_for_load_state("networkidle", timeout=30_000)
    except Exception as exc:
        print(f"[page-budgets] retrospective toggle not reachable/clickable: {exc!r}", flush=True)
    retro_ms = (time.monotonic() - t0) * 1000.0
    retro_api_timing = page.evaluate(
        "() => performance.getEntriesByType('resource')"
        ".filter(r => r.name.includes('/api/market-phase'))"
        ".map(r => ({name: r.name, duration: r.duration, startTime: r.startTime}))"
    )
    results.append({
        "path": "/ (retrospective toggle -- NO standalone /research/market-phase-retrospective route "
                "exists; see dev handoff)",
        "toggle_found": toggle_found,
        "toggle_to_networkidle_ms": round(retro_ms, 1) if toggle_found else None,
        "api_requests": api_calls,
        "api_resource_timing_ms": retro_api_timing,
    })
    print(f"[page-budgets] retrospective toggle: found={toggle_found} "
          f"toggle_to_networkidle={retro_ms:.1f}ms api_calls={len(api_calls)}", flush=True)
    ctx.close()

    browser.close()

with open(OUT, "w") as fh:
    json.dump({"frontend": FRONTEND, "pages": results}, fh, indent=2)
print(f"[page-budgets] wrote {OUT}", flush=True)
