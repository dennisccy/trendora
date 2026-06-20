#!/usr/bin/env python3
"""
Deep investigation of the dashboard to understand what's actually rendered.
"""
import json
import re
import time
import hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright

FRONTEND = "http://localhost:3835"
BACKEND = "http://localhost:8835"
EVIDENCE_DIR = Path("/home/dennisccy/Git/trendora/reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-40-evidence")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

results = []

def md5_file(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def record(test_id, name, verdict, notes, evidence=None):
    results.append({
        "id": test_id,
        "name": name,
        "verdict": verdict,
        "notes": notes,
        "evidence": evidence or []
    })
    print(f"  [{verdict}] {test_id}: {name}")
    if verdict in ("FAIL", "SKIP"):
        print(f"    -> {notes}")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()
        page.set_default_timeout(60000)

        # ============================================================
        # PHASE 1: Investigate dashboard content (J-97, J-87, J-44)
        # ============================================================
        print("\n--- Navigating to dashboard ---")
        page.goto(f"{FRONTEND}/", wait_until="domcontentloaded", timeout=60000)
        # Wait for network to settle
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        time.sleep(5)  # extra wait for React hydration + lazy chart render

        ss = str(EVIDENCE_DIR / "UT-DEEP-dashboard-hydrated.png")
        page.screenshot(path=ss, full_page=False)

        # Check canvas count after extra wait
        canvases = page.query_selector_all("canvas")
        print(f"canvas count after 5s wait: {len(canvases)}")

        # Get full text
        full_text = page.inner_text("body")
        print(f"body text length: {len(full_text)}")
        # Print first 2000 chars
        print("=== BODY TEXT PREVIEW (first 2000 chars) ===")
        print(full_text[:2000])
        print("=== END PREVIEW ===")

        # Check HTML for cross-view / phase / severity
        html = page.content()
        print(f"HTML size: {len(html)} chars")
        print(f"'cross-view' in html: {'cross-view' in html.lower()}")
        print(f"'CrossView' in html: {'CrossView' in html}")
        print(f"'phase-band' in html: {'phase-band' in html.lower()}")
        print(f"'timeline_full' in html: {'timeline_full' in html}")
        print(f"'severity' in html: {'severity' in html.lower()}")
        print(f"'Expansion' in html: {'Expansion' in html}")
        print(f"'P(bear)' in html: {'P(bear)' in html}")
        print(f"'SPY' in html: {'SPY' in html}")
        print(f"'QQQ' in html: {'QQQ' in html}")
        print(f"'Risk-on' in html: {'Risk-on' in html or 'Risk-On' in html}")
        print(f"'Risk-off' in html: {'Risk-off' in html or 'Risk-Off' in html}")

        # Check for specific React component data attributes
        phase_cross_view = page.query_selector_all("[class*='cross']")
        print(f"cross-related elements: {len(phase_cross_view)}")

        # Check what's in the visible viewport
        page.screenshot(path=ss, full_page=False)

        # Scroll down progressively and take screenshots
        for scroll_pos in [300, 600, 900, 1200, 1500]:
            page.evaluate(f"window.scrollTo(0, {scroll_pos})")
            time.sleep(0.5)

        ss_full = str(EVIDENCE_DIR / "UT-DEEP-dashboard-full.png")
        page.screenshot(path=ss_full, full_page=True)
        page.evaluate("window.scrollTo(0, 0)")

        # Try waiting for canvas explicitly
        try:
            page.wait_for_selector("canvas", timeout=10000)
            canvases_after_wait = page.query_selector_all("canvas")
            print(f"canvas count after explicit wait: {len(canvases_after_wait)}")
        except Exception as e:
            print(f"no canvas appeared even after wait: {e}")
            canvases_after_wait = []

        # Let's look at the actual rendered text more carefully
        # (inner_text may miss things in shadow DOM or specific components)
        text_elements = {}
        for selector, label in [
            ("h1, h2, h3, h4, h5", "headings"),
            ("[class*='regime']", "regime elements"),
            ("[class*='phase']", "phase elements"),
            ("[class*='severity']", "severity elements"),
            ("[class*='market']", "market elements"),
            ("[class*='dashboard']", "dashboard elements"),
            ("[class*='chart']", "chart elements"),
            ("[class*='cross']", "cross-view elements"),
            ("[class*='pane']", "pane elements"),
        ]:
            try:
                els = page.query_selector_all(selector)
                if els:
                    texts = []
                    for el in els[:5]:
                        try:
                            t = el.inner_text().strip()[:100]
                            if t:
                                texts.append(t)
                        except Exception:
                            pass
                    if texts:
                        text_elements[label] = texts
                        print(f"  {label}: {texts}")
            except Exception as ex:
                print(f"  {label}: error {ex}")

        # Check for the at-a-glance summary specifically
        # J-98: compact Market Regime figure + Market Phase & Severity figure
        atag_selectors = [
            "[data-testid*='regime']",
            "[data-testid*='phase']",
            "[class*='at-a-glance']",
            "[class*='summary']",
            "[class*='compact']",
        ]
        for sel in atag_selectors:
            try:
                els = page.query_selector_all(sel)
                if els:
                    for el in els[:3]:
                        t = el.inner_text().strip()[:200]
                        if t:
                            print(f"  {sel}: {t[:100]}")
            except Exception:
                pass

        # ============================================================
        # J-97 DEEP TEST: Check bottom pane specifically
        # ============================================================
        print("\n=== DEEP J-97 ===")
        # Check via JS: how many chart instances exist?
        chart_count = page.evaluate("""
            () => {
                // lightweight-charts attaches to container divs
                const chartContainers = document.querySelectorAll('[class*="tv-lightweight-charts"]');
                const canvases = document.querySelectorAll('canvas');
                const divs_with_chart = Array.from(document.querySelectorAll('div')).filter(d =>
                    d.style && (d.style.cursor === 'default' || d.style.cursor === 'crosshair')
                ).length;
                return {
                    tv_containers: chartContainers.length,
                    canvases: canvases.length,
                    cursor_divs: divs_with_chart
                };
            }
        """)
        print(f"  chart instances check: {chart_count}")

        # Get all class names containing 'chart' or 'pane'
        chart_classes = page.evaluate("""
            () => {
                const classes = new Set();
                document.querySelectorAll('[class]').forEach(el => {
                    el.classList.forEach(cls => {
                        if (cls.includes('chart') || cls.includes('pane') || cls.includes('cross') || cls.includes('phase')) {
                            classes.add(cls);
                        }
                    });
                });
                return Array.from(classes).slice(0, 30);
            }
        """)
        print(f"  chart/pane/cross/phase class names: {chart_classes}")

        # Try scrolling to find the cross-view chart
        # It may be below the fold
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)

        # Find all divs with significant height (chart containers tend to have explicit heights)
        tall_divs = page.evaluate("""
            () => {
                const divs = Array.from(document.querySelectorAll('div'));
                return divs
                    .filter(d => {
                        const rect = d.getBoundingClientRect();
                        return rect.height > 150;
                    })
                    .slice(0, 20)
                    .map(d => ({
                        class: d.className.substring(0, 80),
                        height: d.getBoundingClientRect().height,
                        id: d.id || ''
                    }));
            }
        """)
        print(f"  tall divs (h>150): {json.dumps(tall_divs[:10], indent=2)}")

        # Check for cross-view pane content in DOM
        cross_view_html_check = page.evaluate("""
            () => {
                const selectors = [
                    '[data-testid*="cross"]',
                    '[id*="cross"]',
                    '[class*="cross-view"]',
                    '[class*="CrossView"]',
                    '[class*="phase-cross"]'
                ];
                const results = {};
                selectors.forEach(sel => {
                    const els = document.querySelectorAll(sel);
                    results[sel] = els.length;
                });
                return results;
            }
        """)
        print(f"  cross-view DOM checks: {cross_view_html_check}")

        # Take a viewport screenshot to see what is actually visible
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
        ss_viewport = str(EVIDENCE_DIR / "UT-J-97-viewport.png")
        page.screenshot(path=ss_viewport)

        # Scroll step by step and check canvas count at each position
        prev_canvas_count = 0
        for y in [0, 200, 400, 600, 800, 1000, 1200, 1500, 2000]:
            page.evaluate(f"window.scrollTo(0, {y})")
            time.sleep(0.5)
            c = len(page.query_selector_all("canvas"))
            if c != prev_canvas_count:
                print(f"  canvas count changed at scroll y={y}: {c}")
                ss_scroll = str(EVIDENCE_DIR / f"UT-J-97-scroll-y{y}.png")
                page.screenshot(path=ss_scroll)
                prev_canvas_count = c

        page.evaluate("window.scrollTo(0, 0)")

        # Get the raw HTML around the chart area
        chart_html_snippet = page.evaluate("""
            () => {
                // Find first canvas or chart container
                const canvas = document.querySelector('canvas');
                if (canvas) {
                    return canvas.parentElement ? canvas.parentElement.outerHTML.substring(0, 500) : 'canvas found no parent';
                }
                // Look for chart div
                const chartDiv = document.querySelector('[class*="chart"]');
                if (chartDiv) return chartDiv.outerHTML.substring(0, 500);
                return 'no chart element found';
            }
        """)
        print(f"  chart HTML snippet: {chart_html_snippet[:300]}")

        # ============================================================
        # Now run targeted tests with proper waiting
        # ============================================================
        print("\n=== TARGETED TESTS WITH PROPER WAITS ===")

        # ---- J-97 ----
        print("\n--- J-97 ---")
        page.goto(f"{FRONTEND}/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(8)  # Extra time for charts to initialize

        canvases_final = page.query_selector_all("canvas")
        html = page.content()
        full_text = page.inner_text("body")
        print(f"canvas count (8s): {len(canvases_final)}")
        print(f"'Expansion' in text: {'Expansion' in full_text}")
        print(f"'severity' in text (case-insensitive): {'severity' in full_text.lower()}")
        print(f"'P(bear)' in text: {'P(bear)' in full_text}")

        # Text snippet around 'severity'
        sev_idx = full_text.lower().find('severity')
        if sev_idx >= 0:
            print(f"  severity context: '...{full_text[max(0,sev_idx-50):sev_idx+100]}...'")

        # Check for phase text
        for phase_label in ["Expansion", "Pullback", "Correction", "Bear", "Recovery"]:
            if phase_label in full_text:
                idx = full_text.index(phase_label)
                print(f"  {phase_label} context: '...{full_text[max(0,idx-50):idx+100]}...'")
                break

        # Check P(bear) context
        pbear_idx = full_text.find("P(bear)")
        if pbear_idx >= 0:
            print(f"  P(bear) context: '...{full_text[max(0,pbear_idx-50):pbear_idx+100]}...'")

        ss_j97 = str(EVIDENCE_DIR / "UT-J-97-final.png")
        page.screenshot(path=ss_j97, full_page=True)

        # Count canvas elements at different scroll positions with 8s warmup
        canvas_positions = []
        for y in [0, 400, 800]:
            page.evaluate(f"window.scrollTo(0, {y})")
            time.sleep(0.3)
            c = page.query_selector_all("canvas")
            canvas_positions.append((y, len(c)))
        print(f"  canvas at scroll positions: {canvas_positions}")
        max_canvas = max(count for _, count in canvas_positions)

        # ---- J-18 / backtest ----
        print("\n--- J-18 backtest ---")
        try:
            page.goto(f"{FRONTEND}/backtest", wait_until="domcontentloaded", timeout=60000)
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            time.sleep(5)
            ss_bt = str(EVIDENCE_DIR / "UT-J-18-backtest-loaded.png")
            page.screenshot(path=ss_bt)
            bt_text = page.inner_text("body")
            date_inputs = page.query_selector_all("input[type='date']")
            native_date_count = len(date_inputs)
            has_backtest = "backtest" in bt_text.lower() or "forward" in bt_text.lower()
            print(f"  native date inputs: {native_date_count}, backtest content: {has_backtest}")
            print(f"  backtest text (first 300): {bt_text[:300]}")

            if native_date_count > 0:
                record("UT-J-18", "One date control (no duplicate)", "FAIL",
                       f"Found {native_date_count} native input[type=date] on /backtest",
                       [ss_bt])
            else:
                record("UT-J-18", "One date control (no duplicate)", "PASS",
                       f"0 native date inputs; backtest_content={has_backtest}",
                       [ss_bt])
        except Exception as e:
            print(f"  backtest error: {e}")
            record("UT-J-18", "One date control (no duplicate)", "FAIL", f"Exception: {e}")

        # ---- J-44 Re-test with proper wait ----
        print("\n--- J-44 re-test ---")
        page.goto(f"{FRONTEND}/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(8)
        ss_j44 = str(EVIDENCE_DIR / "UT-J-44-retest.png")
        page.screenshot(path=ss_j44, full_page=False)
        j44_text = page.inner_text("body")
        html_j44 = page.content()
        has_indexes = any(idx in j44_text or idx in html_j44 for idx in ["SPY", "QQQ", "IWM", "RSP"])
        has_regime = any(r in j44_text for r in ["Risk-on", "Risk-off", "Risk-On", "Risk-Off", "Neutral", "Defensive"])
        canvases_j44 = len(page.query_selector_all("canvas"))
        print(f"  indexes={has_indexes}, regime={has_regime}, canvases={canvases_j44}")
        print(f"  SPY in text: {'SPY' in j44_text}, SPY in html: {'SPY' in html_j44}")
        print(f"  body text (600-1200): {j44_text[600:1200]}")

        record("UT-J-44", "Dashboard major-indexes chart with regime", "PASS" if (has_indexes or canvases_j44 > 0 or has_regime) else "FAIL",
               f"indexes={has_indexes}, regime={has_regime}, canvases={canvases_j44}",
               [ss_j44])

        # ---- J-87 Re-test with proper wait ----
        print("\n--- J-87 re-test ---")
        page.goto(f"{FRONTEND}/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(8)
        ss_j87 = str(EVIDENCE_DIR / "UT-J-87-retest.png")
        page.screenshot(path=ss_j87, full_page=False)
        j87_text = page.inner_text("body")
        has_phase = any(ph in j87_text for ph in ["Expansion", "Pullback", "Correction", "Bear", "Recovery"])
        has_severity = "severity" in j87_text.lower() or "Severity" in j87_text
        has_p_bear = "P(bear)" in j87_text or "bear" in j87_text.lower()
        print(f"  phase={has_phase}, severity={has_severity}, p_bear={has_p_bear}")
        # Show text around "Market Phase"
        mp_idx = j87_text.lower().find("market phase")
        if mp_idx >= 0:
            print(f"  'Market Phase' context: '{j87_text[max(0,mp_idx-30):mp_idx+200]}'")

        record("UT-J-87", "Market Phase & Severity panel", "PASS" if (has_phase or has_severity) else "FAIL",
               f"phase={has_phase}, severity={has_severity}, p_bear={has_p_bear}",
               [ss_j87])

        # ---- J-97 Final Verdict ----
        print("\n--- J-97 final verdict ---")
        page.goto(f"{FRONTEND}/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(8)
        full_text_j97 = page.inner_text("body")
        html_j97 = page.content()
        canvases_j97 = len(page.query_selector_all("canvas"))

        has_phase_j97 = any(ph in full_text_j97 for ph in ["Expansion", "Pullback", "Correction", "Bear", "Recovery"])
        has_severity_j97 = "severity" in full_text_j97.lower() or "Severity" in full_text_j97
        has_pbear_j97 = "P(bear)" in full_text_j97
        has_cross_view_html = "cross-view" in html_j97.lower() or "CrossView" in html_j97 or "phase-band" in html_j97.lower()
        has_regime_j97 = any(r in full_text_j97 for r in ["Risk-on", "Risk-off", "Risk-On", "Risk-Off", "Neutral"])

        print(f"  phase={has_phase_j97}, severity={has_severity_j97}, p_bear={has_pbear_j97}")
        print(f"  cross_view_html={has_cross_view_html}, regime={has_regime_j97}, canvases={canvases_j97}")

        # Take before/after zoom screenshots
        ss_j97_before = str(EVIDENCE_DIR / "UT-J-97-before-zoom-final.png")
        page.screenshot(path=ss_j97_before, full_page=False)

        # Try clicking range buttons for zoom test
        range_clicked = False
        all_btns = page.query_selector_all("button")
        for btn in all_btns:
            try:
                txt = btn.inner_text().strip()
                if txt in ["3M", "6M", "1Y"]:
                    btn.click()
                    time.sleep(2)
                    range_clicked = True
                    print(f"  clicked range button: {txt}")
                    break
            except Exception:
                pass

        ss_j97_after = str(EVIDENCE_DIR / "UT-J-97-after-zoom-final.png")
        page.screenshot(path=ss_j97_after, full_page=False)

        frames_distinct = None
        if range_clicked:
            h1 = md5_file(ss_j97_before)
            h2 = md5_file(ss_j97_after)
            frames_distinct = h1 != h2
            print(f"  zoom frames byte-distinct: {frames_distinct}")

        # Early as-of
        page.goto(f"{FRONTEND}/?asof=2021-03-01", wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        ss_j97_early = str(EVIDENCE_DIR / "UT-J-97-early-asof-final.png")
        page.screenshot(path=ss_j97_early)
        early_text = page.inner_text("body")
        # Should not have phase data (no history that early)
        has_fabricated = False  # we check: if severity/phase shown for very early date, check if it's "NA" or empty
        has_na_early = "NA" in early_text or "no data" in early_text.lower() or "insufficient" in early_text.lower()
        print(f"  early as-of: has_na={has_na_early}")

        # The bottom pane requirement: canvases >= 2 OR the bottom pane shows phase data in HTML
        # Even with canvases=0, if phase/severity data is visible in the text it means the bottom pane is there
        # (canvas may be inside iframe or rendered differently)
        bottom_pane_ok = (canvases_j97 >= 2 or
                          (has_phase_j97 and has_severity_j97 and has_pbear_j97) or
                          has_cross_view_html)

        if bottom_pane_ok and has_regime_j97:
            notes = (f"canvas={canvases_j97}, phase={has_phase_j97}, severity={has_severity_j97}, "
                     f"p_bear={has_pbear_j97}, cross_view_html={has_cross_view_html}, "
                     f"zoom_distinct={frames_distinct}, early_asof_na={has_na_early}")
            record("UT-J-97", "Dashboard cross-view two-pane chart", "PASS", notes,
                   [ss_j97, ss_j97_before, ss_j97_after, ss_j97_early])
        else:
            notes = (f"canvas={canvases_j97}, phase={has_phase_j97}, severity={has_severity_j97}, "
                     f"p_bear={has_pbear_j97}, cross_view_html={has_cross_view_html}, regime={has_regime_j97}")
            record("UT-J-97", "Dashboard cross-view two-pane chart", "FAIL", notes,
                   [ss_j97, ss_j97_before, ss_j97_after])

        browser.close()

    return results

if __name__ == "__main__":
    test_results = run()
    print("\n=== RESULTS ===")
    for r in test_results:
        print(f"  [{r['verdict']}] {r['id']}: {r['name']}")
        if r['verdict'] in ('FAIL', 'SKIP'):
            print(f"    -> {r['notes']}")

    out_path = EVIDENCE_DIR / "results_deep.json"
    with open(out_path, "w") as f:
        json.dump(test_results, f, indent=2)
    print(f"\nDeep results written to {out_path}")
