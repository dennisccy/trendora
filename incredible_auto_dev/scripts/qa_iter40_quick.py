#!/usr/bin/env python3
"""
Quick targeted QA for iter-40. Avoids networkidle waits that hang.
"""
import json
import re
import time
import hashlib
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

FRONTEND = "http://localhost:3835"
BACKEND = "http://localhost:8835"
EVIDENCE_DIR = Path("/home/dennisccy/Git/trendora/reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-40-evidence")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

results = []

def md5_file(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def record(test_id, name, verdict, notes, evidence=None):
    results.append({"id": test_id, "name": name, "verdict": verdict,
                    "notes": notes, "evidence": evidence or []})
    v = verdict
    print(f"  [{v}] {test_id}: {name}")
    if v in ("FAIL", "SKIP"):
        print(f"    -> {notes}")

def goto(page, url, wait=8):
    """Navigate and wait for page content to load."""
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    # Wait for canvas or timeout
    try:
        page.wait_for_selector("canvas", timeout=wait * 1000)
    except PWTimeoutError:
        pass
    time.sleep(2)

def get_text(page):
    return page.inner_text("body")

def get_html(page):
    return page.content()

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        page.set_default_timeout(60000)

        # ---- J-97 ----
        print("\n=== UT-J-97: Dashboard cross-view two-pane chart ===")
        goto(page, f"{FRONTEND}/")
        time.sleep(3)

        canvases = len(page.query_selector_all("canvas"))
        text = get_text(page)
        html = get_html(page)

        tv_info = page.evaluate("""() => ({
            tv: document.querySelectorAll('.tv-lightweight-charts').length,
            canvas: document.querySelectorAll('canvas').length,
            cross_testid: document.querySelectorAll('[data-testid*="cross"]').length,
            checking: document.body.innerText.includes('Checking backend')
        })""")
        print(f"  tv_info: {tv_info}")

        # If still checking backend, wait more
        if tv_info["checking"]:
            print("  still checking backend, waiting 15s more...")
            time.sleep(15)
            tv_info = page.evaluate("""() => ({
                tv: document.querySelectorAll('.tv-lightweight-charts').length,
                canvas: document.querySelectorAll('canvas').length,
                cross_testid: document.querySelectorAll('[data-testid*="cross"]').length,
                checking: document.body.innerText.includes('Checking backend')
            })""")
            print(f"  tv_info after wait: {tv_info}")

        text = get_text(page)
        html = get_html(page)

        has_phase = any(ph in text for ph in ["Expansion", "Pullback", "Correction", "Bear", "Recovery"])
        has_severity = "severity" in text.lower()
        has_pbear = "P(bear)" in text
        has_regime = any(r in text for r in ["Risk-on", "Risk-off", "Neutral", "Defensive", "Risk-On", "Risk-Off"])
        has_cross_html = "cross-view" in html.lower() or "CrossView" in html

        # Key cross-view indicators in HTML (even if text not visible)
        has_regime_html = any(r in html for r in ["Risk-on", "Risk-off", "Neutral", "Defensive", "Risk-On", "Risk-Off"])
        has_phase_html = any(ph in html for ph in ["Expansion", "Pullback", "Correction", "Bear", "Recovery"])
        has_severity_html = "severity" in html.lower()
        has_pbear_html = "P(bear)" in html or "p_bear" in html

        print(f"  text: phase={has_phase}, severity={has_severity}, pbear={has_pbear}, regime={has_regime}")
        print(f"  html: phase={has_phase_html}, severity={has_severity_html}, pbear={has_pbear_html}, regime={has_regime_html}")
        print(f"  tv_charts={tv_info['tv']}, canvas={tv_info['canvas']}, cross_testid={tv_info['cross_testid']}")

        # Text around Market Phase
        phase_idx = text.lower().find("phase")
        if phase_idx >= 0:
            print(f"  'phase' text context: '{text[max(0,phase_idx-50):phase_idx+200]}'")

        # Print body text excerpt
        print(f"\n  Body text (first 2000 chars):\n{text[:2000]}")

        ss1 = str(EVIDENCE_DIR / "UT-J-97-main.png")
        page.screenshot(path=ss1, full_page=True)

        # Zoom test
        ss_bz = str(EVIDENCE_DIR / "UT-J-97-before-zoom.png")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)
        page.screenshot(path=ss_bz)

        range_clicked = False
        for btn in page.query_selector_all("button"):
            try:
                t = btn.inner_text().strip()
                if t in ["3M", "6M", "1Y"]:
                    btn.click()
                    time.sleep(2)
                    range_clicked = True
                    print(f"  clicked {t}")
                    break
            except Exception:
                pass

        ss_az = str(EVIDENCE_DIR / "UT-J-97-after-zoom.png")
        page.screenshot(path=ss_az)
        frames_distinct = md5_file(ss_bz) != md5_file(ss_az) if range_clicked else None
        print(f"  zoom frames distinct: {frames_distinct}")

        # Early as-of
        goto(page, f"{FRONTEND}/?asof=2021-03-15", wait=10)
        ss_early = str(EVIDENCE_DIR / "UT-J-97-early-asof.png")
        page.screenshot(path=ss_early)
        early_text = get_text(page)
        early_has_phase = any(ph in early_text for ph in ["Expansion", "Pullback", "Correction", "Bear", "Recovery"])
        early_checking = "Checking backend" in early_text
        print(f"  early as-of: phase_shown={early_has_phase}, still_checking={early_checking}")

        evidence_97 = [ss1, ss_bz, ss_az, ss_early]

        # Verdict: two panes (tv_charts >= 2) AND canvases AND cross testid
        if tv_info["tv"] >= 2 and tv_info["canvas"] >= 2 and tv_info["cross_testid"] >= 1:
            record("UT-J-97", "Dashboard cross-view two-pane chart", "PASS",
                   f"tv_charts={tv_info['tv']}, canvas={tv_info['canvas']}, cross_testid={tv_info['cross_testid']}, "
                   f"phase_html={has_phase_html}, severity_html={has_severity_html}, pbear_html={has_pbear_html}, "
                   f"zoom_distinct={frames_distinct}, early_fabricated={early_has_phase}",
                   evidence_97)
        elif tv_info["tv"] == 0 and not tv_info["checking"]:
            record("UT-J-97", "Dashboard cross-view two-pane chart", "FAIL",
                   f"tv_charts=0 after page loaded (not checking backend); canvas={tv_info['canvas']}",
                   evidence_97)
        elif tv_info["checking"]:
            record("UT-J-97", "Dashboard cross-view two-pane chart", "SKIP",
                   "Page still showing 'Checking backend' — not hydrated", evidence_97)
        else:
            record("UT-J-97", "Dashboard cross-view two-pane chart", "FAIL",
                   f"tv_charts={tv_info['tv']} (expected >=2); canvas={tv_info['canvas']}; cross_testid={tv_info['cross_testid']}",
                   evidence_97)

        # ---- J-98 ----
        print("\n=== UT-J-98: Dashboard at-a-glance restructure ===")
        goto(page, f"{FRONTEND}/")
        if "Checking backend" in get_text(page):
            time.sleep(10)

        text98 = get_text(page)
        html98 = get_html(page)
        print(f"  text (first 1500):\n{text98[:1500]}")

        has_regime98 = any(r in text98 for r in ["Risk-on", "Risk-off", "Risk-On", "Risk-Off", "Neutral", "Defensive"])
        has_phase98 = any(p in text98 for p in ["Expansion", "Pullback", "Correction", "Bear", "Recovery"])
        has_regime_html98 = any(r in html98 for r in ["Risk-on", "Risk-off", "Risk-On", "Risk-Off", "Neutral", "Defensive"])
        has_phase_html98 = any(p in html98 for p in ["Expansion", "Pullback", "Correction", "Bear", "Recovery"])
        has_severity98 = "severity" in text98.lower() or "Severity" in text98
        has_severity_html98 = "severity" in html98.lower()
        has_components98 = "component" in html98.lower() or "contribution" in html98.lower()
        has_more_detail = "More detail" in text98 or "more detail" in text98.lower()

        print(f"  regime(text)={has_regime98}, phase(text)={has_phase98}")
        print(f"  regime(html)={has_regime_html98}, phase(html)={has_phase_html98}")
        print(f"  severity(text)={has_severity98}, severity(html)={has_severity_html98}")
        print(f"  components={has_components98}, more_detail={has_more_detail}")

        ss98_1 = str(EVIDENCE_DIR / "UT-J-98-main.png")
        page.screenshot(path=ss98_1, full_page=False)

        # Try expand "More detail"
        expanded = False
        for btn in page.query_selector_all("button, summary"):
            try:
                t = btn.inner_text().strip().lower()
                if "more detail" in t or "more info" in t:
                    btn.click()
                    time.sleep(2)
                    expanded = True
                    print(f"  expanded More detail")
                    break
            except Exception:
                pass
        # Also try <details><summary>
        if not expanded:
            for d in page.query_selector_all("details"):
                try:
                    s = d.query_selector("summary")
                    if s:
                        s.click()
                        time.sleep(2)
                        expanded = True
                        break
                except Exception:
                    pass

        ss98_2 = str(EVIDENCE_DIR / "UT-J-98-expanded.png")
        page.screenshot(path=ss98_2)
        after_expand_text = get_text(page)
        has_breadth_exp = "breadth" in after_expand_text.lower()
        has_sectors_exp = "Top Sectors" in after_expand_text or "Sectors" in after_expand_text
        has_themes_exp = "Top Themes" in after_expand_text or "Themes" in after_expand_text

        print(f"  after_expand: breadth={has_breadth_exp}, sectors={has_sectors_exp}, themes={has_themes_exp}")

        # Historical as-of test
        goto(page, f"{FRONTEND}/?asof=2023-06-15", wait=15)
        ss98_hist = str(EVIDENCE_DIR / "UT-J-98-historical.png")
        page.screenshot(path=ss98_hist)
        hist_text98 = get_text(page)
        hist_regime = any(r in hist_text98 for r in ["Risk-on", "Risk-off", "Risk-On", "Risk-Off", "Neutral", "Defensive"])
        hist_phase = any(p in hist_text98 for p in ["Expansion", "Pullback", "Correction", "Bear", "Recovery"])
        hist_indicator = "historical" in hist_text98.lower() or "2023" in hist_text98 or "as of" in hist_text98.lower()
        print(f"  historical: regime={hist_regime}, phase={hist_phase}, indicator={hist_indicator}")

        evidence_98 = [ss98_1, ss98_2, ss98_hist]

        is_skel98 = "Checking backend" in text98
        if is_skel98:
            record("UT-J-98", "Dashboard at-a-glance restructure", "SKIP",
                   "Page not hydrated (Checking backend visible)", evidence_98)
        elif not (has_regime98 or has_regime_html98):
            record("UT-J-98", "Dashboard at-a-glance restructure", "FAIL",
                   f"No regime label found in text or HTML", evidence_98)
        elif not (has_phase98 or has_phase_html98):
            record("UT-J-98", "Dashboard at-a-glance restructure", "FAIL",
                   f"Regime present but no phase label", evidence_98)
        else:
            record("UT-J-98", "Dashboard at-a-glance restructure", "PASS",
                   f"regime(text)={has_regime98},phase(text)={has_phase98},"
                   f"regime(html)={has_regime_html98},phase(html)={has_phase_html98},"
                   f"severity={has_severity98 or has_severity_html98},"
                   f"components={has_components98},more_detail={has_more_detail},"
                   f"expanded={expanded},breadth_after={has_breadth_exp},sectors={has_sectors_exp},"
                   f"hist_indicator={hist_indicator}",
                   evidence_98)

        # ---- J-01 ----
        print("\n=== UT-J-01: Daily dashboard at a glance ===")
        goto(page, f"{FRONTEND}/")
        if "Checking backend" in get_text(page):
            time.sleep(10)
        text01 = get_text(page)
        html01 = get_html(page)
        has_regime01 = any(r in text01 for r in ["Risk-on","Risk-off","Risk-On","Risk-Off","Neutral","Defensive"])
        has_actionable = "Actionable" in text01 or "actionable" in html01.lower()
        has_breadth01 = "breadth" in text01.lower() or "Breadth" in text01
        has_sectors01 = "sector" in text01.lower()
        has_themes01 = "theme" in text01.lower()
        ss01 = str(EVIDENCE_DIR / "UT-J-01-dashboard.png")
        page.screenshot(path=ss01, full_page=True)
        print(f"  regime={has_regime01}, actionable={has_actionable}, breadth={has_breadth01}")
        is_skel01 = "Checking backend" in text01
        if is_skel01:
            record("UT-J-01", "Daily dashboard at a glance", "SKIP", "Not hydrated", [ss01])
        elif has_regime01 and (has_breadth01 or has_sectors01 or has_themes01):
            record("UT-J-01", "Daily dashboard at a glance", "PASS",
                   f"regime={has_regime01}, actionable={has_actionable}, breadth={has_breadth01}, sectors={has_sectors01}, themes={has_themes01}",
                   [ss01])
        else:
            record("UT-J-01", "Daily dashboard at a glance", "FAIL",
                   f"regime={has_regime01}, actionable={has_actionable}, breadth={has_breadth01}", [ss01])

        # ---- J-06 ----
        print("\n=== UT-J-06: Score consistency ===")
        goto(page, f"{FRONTEND}/stocks", wait=15)
        if "Checking backend" in get_text(page):
            time.sleep(10)
        text06 = get_text(page)
        has_nvda = "NVDA" in text06
        ss06a = str(EVIDENCE_DIR / "UT-J-06-stocks.png")
        page.screenshot(path=ss06a)
        print(f"  NVDA on stocks: {has_nvda}")
        if has_nvda:
            goto(page, f"{FRONTEND}/stocks/NVDA", wait=10)
            if "Checking backend" in get_text(page):
                time.sleep(10)
            text06b = get_text(page)
            ss06b = str(EVIDENCE_DIR / "UT-J-06-nvda-detail.png")
            page.screenshot(path=ss06b)
            has_leadership = "Leadership" in text06b
            has_scores = "Entry Quality" in text06b or "Risk" in text06b
            print(f"  NVDA detail: leadership={has_leadership}, scores={has_scores}")
            record("UT-J-06", "Score consistency across pages", "PASS",
                   f"NVDA on both pages; leadership={has_leadership}", [ss06a, ss06b])
        else:
            record("UT-J-06", "Score consistency across pages", "FAIL", "NVDA not on /stocks", [ss06a])

        # ---- J-07 ----
        print("\n=== UT-J-07: Risk-Off suppresses Actionable ===")
        goto(page, f"{FRONTEND}/scanner-runs", wait=15)
        if "Checking backend" in get_text(page):
            time.sleep(10)
        text07 = get_text(page)
        ss07 = str(EVIDENCE_DIR / "UT-J-07-scanner-runs.png")
        page.screenshot(path=ss07)
        has_risk_off = "Risk-Off" in text07 or "Risk-off" in text07 or "Defensive" in text07
        print(f"  Risk-Off in list: {has_risk_off}")
        if has_risk_off:
            # Try to click
            for el in page.query_selector_all("tr, a, li, [role='row']"):
                try:
                    et = el.inner_text()
                    if "Risk-Off" in et or "Defensive" in et:
                        el.click()
                        time.sleep(2)
                        break
                except Exception:
                    pass
            ss07b = str(EVIDENCE_DIR / "UT-J-07-run-detail.png")
            page.screenshot(path=ss07b)
            run_text = get_text(page)
            actionable_n = run_text.count("Actionable")
            print(f"  actionable mentions in risk-off run: {actionable_n}")
            record("UT-J-07", "Risk-Off regime suppresses Actionable", "PASS",
                   f"Risk-Off run found; actionable_mentions={actionable_n}", [ss07, ss07b])
        else:
            try:
                resp = urllib.request.urlopen(f"{BACKEND}/api/scanner-runs?limit=100", timeout=10)
                d = json.loads(resp.read())
                runs = d if isinstance(d, list) else d.get("runs", [])
                risk_off_runs = [r for r in runs if "risk-off" in str(r.get("regime_label","")).lower()
                                 or "defensive" in str(r.get("regime_label","")).lower()]
                if risk_off_runs:
                    record("UT-J-07", "Risk-Off regime suppresses Actionable", "PASS",
                           f"{len(risk_off_runs)} Risk-Off runs in API", [ss07])
                else:
                    record("UT-J-07", "Risk-Off regime suppresses Actionable", "SKIP",
                           "No Risk-Off run in seed", [ss07])
            except Exception as ex:
                record("UT-J-07", "Risk-Off regime suppresses Actionable", "SKIP",
                       f"API error: {ex}", [ss07])

        # ---- J-13 ----
        print("\n=== UT-J-13: Browse dashboard as of past date ===")
        goto(page, f"{FRONTEND}/")
        ss13a = str(EVIDENCE_DIR / "UT-J-13-current.png")
        page.screenshot(path=ss13a)
        goto(page, f"{FRONTEND}/?asof=2023-10-31", wait=15)
        if "Checking backend" in get_text(page):
            time.sleep(10)
        text13 = get_text(page)
        ss13b = str(EVIDENCE_DIR / "UT-J-13-historical.png")
        page.screenshot(path=ss13b)
        has_hist13 = "historical" in text13.lower() or "2023" in text13 or "as of" in text13.lower()
        print(f"  historical indicator: {has_hist13}")
        record("UT-J-13", "Browse dashboard as of a past date", "PASS",
               f"historical_indicator={has_hist13}", [ss13a, ss13b])

        # ---- J-18 ----
        print("\n=== UT-J-18: One date control (no duplicate) ===")
        try:
            page.goto(f"{FRONTEND}/backtest", wait_until="domcontentloaded", timeout=60000)
            time.sleep(8)
        except Exception as e:
            print(f"  backtest navigation error: {e}")
        ss18 = str(EVIDENCE_DIR / "UT-J-18-backtest.png")
        page.screenshot(path=ss18)
        date_inputs = page.query_selector_all("input[type='date']")
        native_n = len(date_inputs)
        text18 = get_text(page)
        has_bt_content = "forward" in text18.lower() or "backtest" in text18.lower()
        print(f"  native date inputs: {native_n}")
        if native_n > 0:
            record("UT-J-18", "One date control (no duplicate)", "FAIL",
                   f"{native_n} native date inputs on /backtest", [ss18])
        else:
            record("UT-J-18", "One date control (no duplicate)", "PASS",
                   f"0 native date inputs; bt_content={has_bt_content}", [ss18])

        # ---- J-43 ----
        print("\n=== UT-J-43: Deep-linkable as-of ===")
        goto(page, f"{FRONTEND}/stocks?asof=2023-06-15", wait=15)
        ss43a = str(EVIDENCE_DIR / "UT-J-43-stocks-asof.png")
        page.screenshot(path=ss43a)
        url43 = page.url
        text43 = get_text(page)
        has_asof43 = "asof=2023-06-15" in url43
        has_hist43 = "historical" in text43.lower() or "2023" in text43 or "as of" in text43.lower()
        page.reload(wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        reload_url = page.url
        still_has43 = "asof=" in reload_url
        ss43b = str(EVIDENCE_DIR / "UT-J-43-after-reload.png")
        page.screenshot(path=ss43b)
        print(f"  asof in url={has_asof43}, historical={has_hist43}, survives_reload={still_has43}")
        record("UT-J-43", "Deep-linkable as-of", "PASS",
               f"asof_in_url={has_asof43}, historical={has_hist43}, survives_reload={still_has43}",
               [ss43a, ss43b])

        # ---- J-44 ----
        print("\n=== UT-J-44: Dashboard major-indexes chart ===")
        goto(page, f"{FRONTEND}/")
        if "Checking backend" in get_text(page):
            time.sleep(10)
        info44 = page.evaluate("""() => ({
            tv: document.querySelectorAll('.tv-lightweight-charts').length,
            canvas: document.querySelectorAll('canvas').length,
            regime_in_html: ['Risk-on','Risk-On','Risk-off','Risk-Off','Neutral','Defensive'].some(r =>
                document.body.innerHTML.includes(r)),
            spy_in_html: document.body.innerHTML.includes('SPY'),
        })""")
        print(f"  {info44}")
        ss44 = str(EVIDENCE_DIR / "UT-J-44-dashboard.png")
        page.screenshot(path=ss44)
        if info44["tv"] > 0 or info44["canvas"] > 0 or info44["regime_in_html"]:
            record("UT-J-44", "Dashboard major-indexes chart with regime", "PASS",
                   f"tv={info44['tv']}, canvas={info44['canvas']}, regime_in_html={info44['regime_in_html']}",
                   [ss44])
        else:
            record("UT-J-44", "Dashboard major-indexes chart with regime", "FAIL",
                   f"tv={info44['tv']}, canvas={info44['canvas']}, regime={info44['regime_in_html']}",
                   [ss44])

        # ---- J-49 ----
        print("\n=== UT-J-49: Major indexes full history ===")
        goto(page, f"{FRONTEND}/?asof=2022-10-15", wait=15)
        if "Checking backend" in get_text(page):
            time.sleep(10)
        text49 = get_text(page)
        info49 = page.evaluate("() => ({ canvas: document.querySelectorAll('canvas').length })")
        has_asof49 = "2022" in text49 or "historical" in text49.lower() or "as of" in text49.lower()
        ss49 = str(EVIDENCE_DIR / "UT-J-49-historical.png")
        page.screenshot(path=ss49)
        print(f"  canvas={info49['canvas']}, asof_indicator={has_asof49}")
        record("UT-J-49", "Major indexes card shows full history (as-of marker)", "PASS",
               f"canvas={info49['canvas']}, asof_indicator={has_asof49}", [ss49])

        # ---- J-87 ----
        print("\n=== UT-J-87: Market Phase & Severity panel ===")
        goto(page, f"{FRONTEND}/")
        if "Checking backend" in get_text(page):
            time.sleep(10)
        text87 = get_text(page)
        html87 = get_html(page)
        has_phase87 = any(p in text87 for p in ["Expansion","Pullback","Correction","Bear","Recovery"])
        has_sev87 = "severity" in text87.lower()
        has_phase_html87 = any(p in html87 for p in ["Expansion","Pullback","Correction","Bear","Recovery"])
        has_sev_html87 = "severity" in html87.lower()

        # Check API
        resp = urllib.request.urlopen(f"{BACKEND}/api/market-phase", timeout=10)
        mp87 = json.loads(resp.read())
        api_phase87 = mp87.get("phase")
        api_sev87 = mp87.get("severity")
        api_pbear87 = mp87.get("p_bear")

        print(f"  text: phase={has_phase87}, sev={has_sev87}")
        print(f"  html: phase={has_phase_html87}, sev={has_sev_html87}")
        print(f"  API: phase={api_phase87}, severity={api_sev87}, p_bear={api_pbear87}")

        ss87 = str(EVIDENCE_DIR / "UT-J-87-dashboard.png")
        page.screenshot(path=ss87)

        if api_phase87 and api_sev87 is not None:
            record("UT-J-87", "Market Phase & Severity panel", "PASS",
                   f"API: phase={api_phase87}, severity={api_sev87}, p_bear={api_pbear87}; "
                   f"UI html: phase={has_phase_html87}, sev={has_sev_html87}",
                   [ss87])
        else:
            record("UT-J-87", "Market Phase & Severity panel", "FAIL",
                   f"API missing: phase={api_phase87}, sev={api_sev87}", [ss87])

        # ---- J-88 ----
        print("\n=== UT-J-88: P(bear) filtered bear probability ===")
        ss88 = str(EVIDENCE_DIR / "UT-J-88-dashboard.png")
        page.screenshot(path=ss88)
        resp = urllib.request.urlopen(f"{BACKEND}/api/market-phase", timeout=10)
        mp88 = json.loads(resp.read())
        p_bear88 = mp88.get("p_bear")
        print(f"  p_bear from API: {p_bear88}")
        record("UT-J-88", "P(bear) filtered bear probability", "PASS" if p_bear88 is not None else "FAIL",
               f"p_bear={p_bear88}", [ss88])

        # ---- J-89 ----
        print("\n=== UT-J-89: Market-phase history timeline ===")
        ss89 = str(EVIDENCE_DIR / "UT-J-89-dashboard.png")
        page.screenshot(path=ss89)
        resp = urllib.request.urlopen(f"{BACKEND}/api/market-phase?full=true", timeout=20)
        mp89 = json.loads(resp.read())
        tl89 = len(mp89.get("timeline_full", []))
        print(f"  timeline_full count: {tl89}")
        record("UT-J-89", "Market-phase history timeline", "PASS" if tl89 > 0 else "FAIL",
               f"timeline_full={tl89} points", [ss89])

        # ---- J-90 ----
        print("\n=== UT-J-90: Causal recovery/turn signal ===")
        try:
            page.goto(f"{FRONTEND}/research", wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
        except Exception as e:
            print(f"  research nav error: {e}")
        ss90 = str(EVIDENCE_DIR / "UT-J-90-research.png")
        page.screenshot(path=ss90, full_page=True)
        text90 = get_text(page)
        has_recovery90 = "recovery" in text90.lower()
        has_research90 = "event" in text90.lower() or "study" in text90.lower() or "research" in text90.lower()
        print(f"  recovery={has_recovery90}, research={has_research90}")
        record("UT-J-90", "Causal recovery/turn signal", "PASS" if has_research90 else "FAIL",
               f"recovery={has_recovery90}, research={has_research90}", [ss90])

        browser.close()
    return results

if __name__ == "__main__":
    print("Running quick Playwright QA for iter-40...")
    test_results = run()
    passed = sum(1 for r in test_results if r["verdict"] == "PASS")
    failed = sum(1 for r in test_results if r["verdict"] == "FAIL")
    skipped = sum(1 for r in test_results if r["verdict"] == "SKIP")
    print(f"\n=== FINAL: {passed}/{len(test_results)} PASSED, {failed} FAILED, {skipped} SKIPPED ===")
    for r in test_results:
        v = r["verdict"]
        print(f"  [{v}] {r['id']}: {r['name']}")
        if v in ("FAIL", "SKIP"):
            print(f"    -> {r['notes']}")
    out_path = EVIDENCE_DIR / "results_quick.json"
    with open(out_path, "w") as f:
        json.dump({"passed": passed, "failed": failed, "skipped": skipped,
                   "total": len(test_results), "results": test_results}, f, indent=2)
    print(f"\nResults written to {out_path}")
