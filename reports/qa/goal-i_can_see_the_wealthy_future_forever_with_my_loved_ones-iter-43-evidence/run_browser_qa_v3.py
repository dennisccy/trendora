#!/usr/bin/env python3
"""
v3: Inspect dashboard deeply - check what's actually rendered.
Focus on J-89, J-90, J-97 and get full page DOM content.
"""

import json
import time
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

EVIDENCE_DIR = Path("/home/dennisccy/Git/trendora/reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-43-evidence")
FRONTEND_URL = "http://localhost:3835"
BACKEND_URL = "http://localhost:8835"

def ss(page, name, full=False):
    path = str(EVIDENCE_DIR / f"{name}.png")
    page.screenshot(path=path, full_page=full)
    print(f"  [screenshot] {name}.png")
    return path

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 1200})
        page = ctx.new_page()
        page.set_default_timeout(90000)

        print("\n=== ITER-43 DEEP DASHBOARD INSPECTION ===\n")

        # Load dashboard fresh
        page.goto(f"{FRONTEND_URL}/", wait_until="domcontentloaded", timeout=60000)
        print("  Initial load done. Waiting 20s for full hydration...")
        time.sleep(20)

        body = page.inner_text("body")
        print(f"  body len after 20s: {len(body)}")
        print(f"  body full:\n{'-'*60}\n{body}\n{'-'*60}")

        # Get all element types rendered
        all_elements = page.evaluate("""() => {
            const tags = {};
            document.querySelectorAll('*').forEach(el => {
                tags[el.tagName] = (tags[el.tagName] || 0) + 1;
            });
            return tags;
        }""")
        print(f"\n  Element counts (interesting): " + str({k:v for k,v in all_elements.items() if k in ['CANVAS', 'SVG', 'DIV', 'SECTION', 'ARTICLE', 'CHART']}))

        # Get canvas elements
        canvases = page.eval_on_selector_all('canvas', 'els => els.map(e => ({id: e.id, class: e.className, width: e.width, height: e.height}))')
        print(f"  Canvas elements: {canvases}")

        # Get SVG elements
        svgs = page.eval_on_selector_all('svg', 'els => els.length')
        print(f"  SVG count: {svgs}")

        # Check for chart container divs
        chart_divs = page.eval_on_selector_all('[class*="chart"], [class*="Chart"], [id*="chart"]', 'els => els.map(e => ({tag: e.tagName, id: e.id, class: e.className[:50] if e.className else ""}))')
        print(f"  Chart-related divs: {chart_divs[:5]}")

        # Get div with class containing "chart"
        chart_check = page.evaluate("""() => {
            const divs = Array.from(document.querySelectorAll('div'));
            const chartDivs = divs.filter(d => d.className && (d.className.includes('chart') || d.className.includes('Chart')));
            return chartDivs.slice(0, 5).map(d => ({class: d.className.slice(0, 80), children: d.children.length}));
        }""")
        print(f"  Chart divs: {chart_check}")

        # Get phase/recovery related content
        phase_check = page.evaluate("""() => {
            const allText = document.body.innerText;
            const markers = ['Phase', 'phase', 'Timeline', 'timeline', 'Episode', 'episode',
                           'Recovery', 'recovery', 'Turn', 'Severity', 'severity',
                           'P(bear)', 'Bear Prob', 'probability', 'Regime', 'Score',
                           'Expansion', 'Pullback', 'Bear', 'Correction'];
            const found = markers.filter(m => allText.includes(m));
            return {found, textLen: allText.length, textSample: allText.slice(0, 1000)};
        }""")
        print(f"  Phase markers found: {phase_check['found']}")
        print(f"  Text len: {phase_check['textLen']}")

        # Check for any error states
        error_check = page.evaluate("""() => {
            const errEls = document.querySelectorAll('[class*="error"], [class*="Error"], [data-error]');
            return Array.from(errEls).slice(0, 5).map(e => e.innerText.slice(0, 100));
        }""")
        print(f"  Error elements: {error_check}")

        # Check API responses via network - what did /api/market-phase return?
        # Directly test the API
        import urllib.request
        try:
            resp = urllib.request.urlopen(f"{BACKEND_URL}/api/market-phase", timeout=30)
            mp_data = json.loads(resp.read())
            print(f"\n  /api/market-phase keys: {list(mp_data.keys()) if isinstance(mp_data, dict) else type(mp_data)}")
            if isinstance(mp_data, dict):
                print(f"  phase: {mp_data.get('phase')}")
                print(f"  severity: {mp_data.get('severity')}")
                print(f"  p_bear: {mp_data.get('p_bear')}")
                print(f"  timeline keys: {list(mp_data.get('timeline', {}).keys()) if isinstance(mp_data.get('timeline'), dict) else 'N/A'}")
                print(f"  episodes: {mp_data.get('episodes', 'N/A')}")
                print(f"  recovery_signal: {mp_data.get('recovery_signal', 'N/A')}")
                # Save for reference
                with open(str(EVIDENCE_DIR / "api-market-phase.json"), "w") as f:
                    json.dump(mp_data, f, indent=2, default=str)
        except Exception as e:
            print(f"  /api/market-phase error: {e}")

        # Take full page screenshot
        ss(page, "UT-dashboard-deep-full", full=True)
        ss(page, "UT-dashboard-deep-viewport")

        # Scroll and capture different sections
        for scroll_y in [300, 600, 900, 1200]:
            page.evaluate(f"window.scrollTo(0, {scroll_y})")
            time.sleep(1)
            ss(page, f"UT-dashboard-scroll-{scroll_y}")

        # Check if there are hidden/collapsed sections that need clicking
        # J-98 says "More detail" is collapsed
        more_detail_btn = page.query_selector('text=More detail')
        if not more_detail_btn:
            more_detail_btn = page.query_selector('[class*="more"], button:has-text("More"), button:has-text("Expand")')
        if more_detail_btn:
            print("\n  Found 'More detail' button - clicking to expand...")
            more_detail_btn.click()
            time.sleep(2)
            body_after = page.inner_text("body")
            print(f"  body after expand: {len(body_after)}")
            ss(page, "UT-dashboard-expanded")
            has_more_after = any(x in body_after for x in ["Sectors", "Themes", "Breadth", "Candidates"])
            print(f"  Has additional content after expand: {has_more_after}")
        else:
            print("\n  No 'More detail' button found via selector")

        browser.close()
        print("\n=== Deep inspection complete ===")

if __name__ == "__main__":
    run()
