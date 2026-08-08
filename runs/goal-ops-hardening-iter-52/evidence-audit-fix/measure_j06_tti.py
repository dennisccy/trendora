"""TC-7 / J-06 step 2 — the Factor Lab page's REAL-BROWSER load measurement.

The number `reports/perf-budgets.md` has owed for two rounds (iter-52 audit B2): the Factor Lab page's
real-browser time-to-interactive AND the on-load `GET /api/research/factor-lab?all=true` latency,
measured against the SHIPPED tree with the cache warmed by a real ingest.

Records, per run:
  * the three navigation-timing marks the browser lane reports (domInteractive,
    domContentLoadedEventEnd, loadEventEnd — all relative to navigationStart);
  * `content_visible_ms` — wall clock from `page.goto()` to the Factor Lab's own heading being visible,
    which is the honest "interactive" figure for a client-rendered page (the three marks above only
    describe the empty shell Next.js ships);
  * every `/api/research/factor-lab*` request the page fired, with its own response timing.

Usage: measure_j06_tti.py <frontend_url> <out_json> [runs]
"""
import json
import sys
import time

from playwright.sync_api import sync_playwright

FRONTEND = sys.argv[1].rstrip("/")
OUT = sys.argv[2]
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 3

results = []
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)

    # One throwaway navigation FIRST: `next dev` compiles a route on its first visit, which is a
    # dev-server artefact, not the page's load time. Measuring it would overstate the figure by seconds.
    warm = browser.new_context()
    wp = warm.new_page()
    wp.goto(f"{FRONTEND}/research/factor-lab", wait_until="networkidle", timeout=180_000)
    warm.close()
    print("[j06] route warm-up navigation done (next dev route compile excluded)", flush=True)

    for i in range(RUNS):
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        api_calls = []

        def on_response(resp, _calls=api_calls):
            if "/api/research/factor-lab" in resp.url:
                _calls.append({"url": resp.url, "status": resp.status})

        page.on("response", on_response)

        t0 = time.monotonic()
        page.goto(f"{FRONTEND}/research/factor-lab", wait_until="domcontentloaded", timeout=120_000)
        page.get_by_text("Research — Factor Lab").first.wait_for(state="visible", timeout=120_000)
        content_visible_ms = (time.monotonic() - t0) * 1000.0

        # the page's own heavy fetch has to have LANDED before this is a fair "loaded" figure
        page.wait_for_load_state("networkidle", timeout=120_000)
        networkidle_ms = (time.monotonic() - t0) * 1000.0

        nav = page.evaluate(
            "() => { const n = performance.getEntriesByType('navigation')[0]; return n ? {"
            "domInteractive: n.domInteractive, domContentLoadedEventEnd: n.domContentLoadedEventEnd,"
            "loadEventEnd: n.loadEventEnd, responseEnd: n.responseEnd, duration: n.duration} : null; }"
        )
        api_timing = page.evaluate(
            "() => performance.getEntriesByType('resource')"
            ".filter(r => r.name.includes('/api/research/factor-lab'))"
            ".map(r => ({name: r.name, duration: r.duration, startTime: r.startTime}))"
        )
        rows = page.evaluate("() => document.querySelectorAll('table tbody tr').length")

        results.append({
            "run": i,
            "nav_timing_ms": nav,
            "content_visible_ms": round(content_visible_ms, 1),
            "networkidle_ms": round(networkidle_ms, 1),
            "api_requests": api_calls,
            "api_resource_timing_ms": api_timing,
            "table_rows_rendered": rows,
        })
        print(f"[j06] run {i}: content_visible={content_visible_ms:.1f}ms "
              f"networkidle={networkidle_ms:.1f}ms nav={nav} api={api_timing} rows={rows}", flush=True)
        if i == 0:
            page.screenshot(path=OUT.replace(".json", ".png"), full_page=False)
        ctx.close()
    browser.close()

with open(OUT, "w") as fh:
    json.dump({"frontend": FRONTEND, "runs": results}, fh, indent=2)
print(f"[j06] wrote {OUT}", flush=True)
