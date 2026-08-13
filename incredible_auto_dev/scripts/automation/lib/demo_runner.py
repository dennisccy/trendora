#!/usr/bin/env python3
"""demo_runner.py — deterministic browser demo executor.

Reads an executable demo-script JSON (authored by the demo-narrator agent) and
drives Chrome via Playwright. NO model is in the execution loop, so it cannot
loop or stall on round-trips.

Modes:
  live          headed Chrome, press-Enter-to-advance, narration to the CLI.
  record        headless, auto-wait, screenshots → reports/demo/<id>/step-NN.png.
  session-live  same as live, for a whole-product (session) demo JSON.

The runner re-emits demo-script.md + demo-results.md byte-compatibly with the
existing HTML gallery renderer (render_iteration_summary.py), so that renderer
needs no changes.

Self-test (no browser, no network):
  python3 demo_runner.py self-test

Exit codes: 0 ok/soft-skip · 2 bad args/JSON, or (record/live) the `{{AUTO_UNSNAPSHOTTED_DATE}}`
sentinel could not be resolved (see `resolve_sentinel_date`) · 3 playwright missing · 4 no DISPLAY (live)
· 5 verify found ≥1 FAIL · 6 browser infrastructure failure (launch/crash — verify only;
callers route replay journeys back to the LLM lane so nothing is silently unverified)
· 7 verify: backend unreachable BEFORE any journey ran — every journey is written BLOCKED
(never FAIL; ops-hardening iter-39, see `probe_backend_health`/run_verify). Distinct from rc 6
(a browser that launched and then died mid-run): rc 7 means the browser was never even asked to
navigate anywhere, because the backend the app depends on never answered its own health check.
Callers route BLOCKED journeys back to the LLM lane exactly like rc 6, so nothing is silently
unverified — see the generic non-zero-rc fallback in lib/replay-lane.sh.
"""
from __future__ import annotations

import datetime
import json
import os
import sqlite3
import struct
import sys
import urllib.error
import urllib.request
import zlib
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

# ── pure logic (deterministic, browser-free) ─────────────────────────────────

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0"}
_VALID_ACTIONS = {"goto", "click", "fill", "expect", "wait_for"}


def normalize_url(base_url: str, url: str) -> str:
    """Resolve a step URL against the real base_url.

    Relative paths are joined onto base_url. Absolute URLs pointing at a local
    host (localhost/127.0.0.1) are rewritten onto base_url's host:port — this is
    the fix for the start scripts' offset dev-port (a hardcoded :3000 from a QA
    artifact would otherwise hit the wrong port). Genuinely external absolute
    URLs are left untouched.
    """
    base = urlsplit(base_url)
    u = urlsplit(url or "")
    if u.scheme and u.netloc:
        if (u.hostname or "") in _LOCAL_HOSTS:
            return urlunsplit((base.scheme, base.netloc, u.path or "/", u.query, u.fragment))
        return url
    path = u.path or "/"
    if not path.startswith("/"):
        path = "/" + path
    return urlunsplit((base.scheme, base.netloc, path, u.query, u.fragment))


def validate_script(data: object) -> list[str]:
    """Return a list of human-readable problems; empty list means valid."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["script is not a JSON object"]
    if not isinstance(data.get("schema_version"), int):
        errors.append("missing or non-integer schema_version")
    steps = data.get("steps")
    if data.get("not_yet"):
        # A "nothing to show yet" script legitimately has no steps.
        if steps is not None and not isinstance(steps, list):
            errors.append("steps must be a list when present")
        return errors
    if not isinstance(steps, list) or not steps:
        errors.append("missing or empty steps[]")
        return errors
    for i, step in enumerate(steps):
        where = f"step[{i}]"
        if not isinstance(step, dict):
            errors.append(f"{where} is not an object")
            continue
        action = step.get("action")
        if not isinstance(action, dict):
            errors.append(f"{where} missing action object")
            continue
        atype = action.get("type")
        if atype not in _VALID_ACTIONS:
            errors.append(f"{where} invalid action type {atype!r}")
            continue
        if atype == "goto" and not action.get("url"):
            errors.append(f"{where} goto requires url")
        if atype in ("click", "fill") and not isinstance(action.get("target"), dict):
            errors.append(f"{where} {atype} requires a target object")
        if atype == "fill" and not action.get("text"):
            errors.append(f"{where} fill requires text")
    return errors


def resolve_spec(target: object) -> list[tuple]:
    """Map a target hint to an ordered list of locator specs (primary first,
    then automatic degradation). Each spec is (kind, role_or_None, value).
    The Playwright layer tries them in order and uses the first that resolves.
    """
    if not isinstance(target, dict):
        return []
    if "role" in target:
        name = target.get("name", "")
        specs = [("role", target["role"], name)]
        if name:
            specs.append(("text", None, name))  # degrade role→text
        return specs
    if "text" in target:
        return [("text", None, target["text"])]
    if "label" in target:
        return [("label", None, target["label"]), ("placeholder", None, target["label"])]
    if "placeholder" in target:
        return [("placeholder", None, target["placeholder"])]
    if "testid" in target:
        return [("testid", None, target["testid"])]
    if "css" in target:
        return [("css", None, target["css"])]
    return []


def compute_verdict(any_captured: bool, has_soft_notes: bool, not_yet: bool) -> str:
    if not_yet:
        return "NOT_YET"
    if not any_captured:
        return "SKIPPED"
    if has_soft_notes:
        return "RECORDED_WITH_NOTES"
    return "RECORDED"


def compute_regression_verdict(results: list[dict]) -> str:
    """Overall verdict for a deterministic regression-replay run (verify mode).

    Unlike the showcase verdicts above, replay treats a journey's `expect`s as
    HARD assertions: FAIL if any journey failed; BLOCKED if the backend was
    unreachable before any journey ran (ops-hardening iter-39 — a DISTINCT class
    from FAIL: a journey verdict of FAIL means "this journey's own assertions did
    not hold", which is untrue when the backend never answered in the first
    place; conflating the two is exactly what let a downed backend read as
    regressions twice in this session, iter-38/t); SKIPPED if none ran or all
    were skipped (e.g. no golden script on file); otherwise PASS."""
    verdicts = [r.get("verdict") for r in results]
    if not verdicts:
        return "SKIPPED"
    if "FAIL" in verdicts:
        return "FAIL"
    if "BLOCKED" in verdicts:
        return "BLOCKED"
    if all(v == "SKIP" for v in verdicts):
        return "SKIPPED"
    return "PASS"


def resolve_backend_health_url(base_url: str, explicit: "str | None" = None) -> str:
    """The backend readiness URL `run_verify` must probe before trusting ANY replay verdict.

    Preference order: an explicit `--backend-health-url` (set by a caller, or a test), then a
    same-host guess built from `CHAIN_BACKEND_PORT` — the SAME env var every launch/QA script in
    this framework already uses to compute the backend's assigned port (see lib/common.sh's
    `ensure_phase_ports`), which is present in this process's environment by the time the
    pipeline invokes `--mode verify` — combined with this project's canonical readiness path,
    `GET /api/health` (Trendora goal.md: "computed only in `app.engine.readiness`, served only by
    `GET /api/health`"). Deliberately NOT the framework's generic `/health` default
    (lib/common.sh's `bqa_services_probe`): every Trendora route is namespaced under `/api`, so a
    bare `/health` 404s even on a perfectly healthy backend — reusing that default here would
    BLOCK every replay run unconditionally, which is worse than the bug this closes."""
    if explicit:
        return explicit
    base = urlsplit(base_url or "http://localhost:3000")
    port = os.environ.get("CHAIN_BACKEND_PORT", "8000")
    host = base.hostname or "localhost"
    return urlunsplit((base.scheme or "http", f"{host}:{port}", "/api/health", "", ""))


def probe_backend_health(url: str, timeout: float = 5.0) -> bool:
    """True iff `url` answers with EXACTLY HTTP 200 within `timeout` seconds.

    Any failure mode — connection refused, timeout, DNS error, a non-200 status — is honestly
    False. Deliberately STRICT (unlike the framework's permissive `bqa_services_probe`, which
    treats any 1xx-5xx as "alive" — a reasonable bar for "is uvicorn listening at all", but not
    for "is this app genuinely ready to serve a UI replay"): a half-up or wrong-port backend must
    BLOCK the replay lane, not silently pass it through to a false FAIL."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 — localhost only
            return resp.status == 200
    except (urllib.error.URLError, OSError, ValueError):
        return False



# ── sentinel-date resolver (ops-hardening iter-64) ────────────────────────────
#
# WHY: four consecutive rounds (iter-58, iter-59 x2, iter-62/63, iter-63-audit) hand-rotated
# J-05's golden onto a date that the SAME round's own replay lane then consumed, arming a
# guaranteed false FAIL on a currently-passing journey next round. The durable fix is a
# run-time self-selecting mechanism, not another hand rotation (J-05.json's own `_notes`
# call for this verbatim). A golden carrying the token below has that date resolved fresh,
# every replay, against whatever the DB's `scanner_runs` table looks like AT THAT MOMENT —
# so a date consumed by any run (this iteration's own drill, a prior replay, a manual
# verification) is automatically excluded, with no file edit required.

SENTINEL_TOKEN = "{{AUTO_UNSNAPSHOTTED_DATE}}"

# The benchmark symbol every `scanner_runs` row is computed against (its own `benchmark`
# column — confirmed live, 2026-08-11: every existing row reads "SPY", never anything else).
# A resolved date is useless for a real backfill unless a SPY bar exists for it, so the query
# below requires one explicitly.
_SENTINEL_BENCHMARK_SYMBOL = "SPY"

# A bounded historical window, not the full 1996-2026 basis. Deliberately starts AFTER SPY's
# own earliest row in this seed (measured 2026-08-11: SPY's first daily_prices bar is
# 2005-02-25 — a real, if unusual, property of this committed seed, not a gap: 1996-2004 has
# OTHER symbols' bars but no SPY at all, which would silently break a resolved date's backfill
# were it not excluded by the `_SENTINEL_BENCHMARK_SYMBOL` join below). 2005-03-01..2016-12-31
# carries 2,195 SPY trading days with zero `scanner_runs` rows as of this iteration (measured
# the same day) — a bounded slice of the committed seed, never a whole-table scan, with years
# of headroom at the historical ~1 consumed date/iteration rate before it would need widening.
_SENTINEL_WINDOW_START = "2005-03-01"
_SENTINEL_WINDOW_END = "2016-12-31"


def resolve_sentinel_date(db_path: "str | os.PathLike",
                          window_start: str = _SENTINEL_WINDOW_START,
                          window_end: str = _SENTINEL_WINDOW_END,
                          benchmark_symbol: str = _SENTINEL_BENCHMARK_SYMBOL) -> str:
    """Read-only resolution of `SENTINEL_TOKEN`: the earliest trading day inside
    `[window_start, window_end]` that BOTH carries a `daily_prices` bar for
    `benchmark_symbol` (the symbol every `scanner_runs` row is computed against — a date
    without one cannot produce a real backfill row) AND carries ZERO `scanner_runs` rows for
    that date, i.e. is eligible for a single-date J-05 backfill.

    Opened `mode=ro` — this never mutates the database. Fails EXPLICITLY (raises
    RuntimeError naming the reason) when the db file is missing or the window is exhausted
    (every eligible day in it already snapshotted) — the caller must never fall back to
    guessing or silently reusing a consumed date; per this iteration's spec, that failure is
    the whole point of the resolver over another hand-picked date."""
    path = Path(db_path)
    if not path.exists():
        raise RuntimeError(f"sentinel resolution failed: database not found at {path}")
    uri = f"file:{path.resolve()}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True)
    except sqlite3.OperationalError as exc:
        raise RuntimeError(f"sentinel resolution failed: could not open {path} read-only: {exc}") from exc
    try:
        row = conn.execute(
            "SELECT date FROM daily_prices WHERE symbol = ? AND date >= ? AND date <= ? "
            "AND date NOT IN (SELECT asof_date FROM scanner_runs) "
            "ORDER BY date ASC LIMIT 1",
            (benchmark_symbol, window_start, window_end),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise RuntimeError(
            "sentinel resolution failed: no eligible unsnapshotted trading day (with a "
            f"{benchmark_symbol} bar) in [{window_start}, {window_end}] — every eligible day "
            "in the window already has a scanner_runs row; widen the window rather than "
            "reusing a consumed date")
    return row[0]


def script_needs_sentinel(script: object, token: str = SENTINEL_TOKEN) -> bool:
    """True iff `token` appears anywhere in the script's JSON (any step's fill text, expect
    text, click-target text, or the script's own `name`) — checked structurally so no field
    is missed, never by assuming which fields might carry it."""
    return token in json.dumps(script)


def substitute_sentinel_in_script(script: dict, resolved_date: str,
                                  token: str = SENTINEL_TOKEN) -> dict:
    """Return a NEW script with every occurrence of `token` in every string value replaced by
    `resolved_date` — recursively, so fill targets, expect text, click-target text, and the
    script's own `name` field all receive the SAME resolved date, however deeply nested.
    `script` itself is left untouched."""
    def _walk(node):
        if isinstance(node, str):
            return node.replace(token, resolved_date) if token in node else node
        if isinstance(node, dict):
            return {k: _walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [_walk(v) for v in node]
        return node
    return _walk(script)


def resolve_and_substitute_sentinel(script: dict, db_path: "str | os.PathLike",
                                    token: str = SENTINEL_TOKEN) -> "tuple[dict, str | None]":
    """If `token` appears anywhere in `script`, resolve it ONCE against `db_path` and
    substitute the SAME resolved date everywhere it appears. Returns `(script, None)`
    unchanged when the token is absent (the common case — most goldens carry no sentinel).
    Propagates `resolve_sentinel_date`'s RuntimeError when the token IS present but
    resolution fails — callers must treat that as a real failure, never a silent SKIP."""
    if not script_needs_sentinel(script, token):
        return script, None
    resolved = resolve_sentinel_date(db_path)
    return substitute_sentinel_in_script(script, resolved, token), resolved


def default_sentinel_db_path(repo_root: "str | None") -> Path:
    """The committed dev DB the sentinel resolver reads. `repo_root` is the SAME value every
    caller already passes as `--repo-root` (demo-phase.sh, replay-lane.sh); fall back to a
    path derived from this file's own location so an unaugmented CLI call (e.g. a developer
    running the self-test or a manual `--mode verify`) still resolves correctly.

    Deliberately `Path(__file__).absolute()`, NOT `.resolve()`: `scripts/` is a git-tracked
    symlink to `incredible_auto_dev/scripts/` (same physical file, two paths), and `.resolve()`
    follows it — which would climb out through the framework subtree's OWN root
    (`incredible_auto_dev/`, which has no `apps/`) instead of this project's repo root. Every
    real caller invokes this file through the unresolved `scripts/...` path (bash's `pwd`
    stays logical by default), so `__file__` already carries the right ancestry without
    resolving it."""
    root = Path(repo_root) if repo_root else Path(__file__).absolute().parents[3]
    return root / "apps" / "backend" / "data" / "trendora.db"


def _today() -> str:
    return datetime.date.today().isoformat()


def render_results_md(phase_id: str, frontend_url: str, iteration, captured: list[dict],
                      soft_notes: list[str], verdict: str, mode: str) -> str:
    """Emit demo-results.md byte-compatibly with render_iteration_summary.py."""
    lines = [f"# Demo Results — {phase_id}", ""]
    lines.append(f"**Demo Verdict:** {verdict}")
    lines.append(f"**Date:** {_today()}")
    lines.append(f"**Frontend URL:** {frontend_url}")
    if iteration is not None:
        lines.append(f"**Iteration:** {iteration}")
    lines += ["", "## Captured Steps", "",
              "| Step | Title | Journey | New | Screenshot |",
              "|------|-------|---------|-----|------------|"]
    for s in captured:
        n = f"{int(s['n']):02d}"
        title = str(s.get("title", "")).replace("|", "\\|")
        journey = s.get("journey") or ""
        new = "yes" if s.get("new") else ""
        shot = s.get("screenshot", "") or ""
        lines.append(f"| {n} | {title} | {journey} | {new} | {shot} |")
    lines.append("")
    if soft_notes:
        lines += ["## Soft notes", ""]
        lines += [f"- {note}" for note in soft_notes]
        lines.append("")
    lines += ["## Environment", "",
              f"- **Frontend URL:** {frontend_url}",
              f"- **Browser:** Chromium via Playwright ({mode})",
              f"- **Demo mode:** {mode}", ""]
    return "\n".join(lines)


def render_regression_results_md(phase_id: str, frontend_url: str, iteration,
                                 results: list[dict], mode: str = "verify") -> str:
    """Emit a ui-test-results.md-compatible report for deterministic regression
    replay — byte-shaped like templates/ui-test-results.md so the goal-evaluator
    reads it exactly like the LLM browser-qa output (top `**Browser QA Verdict:**`
    line, one `UT-<journey>` row per journey, evidence screenshots). `results` is
    a list of {journey, name, verdict (PASS/FAIL/SKIP/BLOCKED), expected, actual, evidence}."""
    overall = compute_regression_verdict(results)
    total = len(results)
    n_pass = sum(1 for r in results if r.get("verdict") == "PASS")
    n_skip = sum(1 for r in results if r.get("verdict") == "SKIP")
    n_blocked = sum(1 for r in results if r.get("verdict") == "BLOCKED")
    lines = [f"# Regression Replay — {phase_id}", ""]
    lines.append(f"**Phase:** {phase_id}")
    lines.append(f"**Date:** {_today()}")
    lines.append("**Written by:** demo_runner.py (deterministic replay)")
    if iteration is not None:
        lines.append(f"**Iteration:** {iteration}")
    overall_line = f"**Overall:** {n_pass}/{total} journeys passed ({n_skip} skipped"
    overall_line += f", {n_blocked} blocked — backend unreachable" if n_blocked else ""
    overall_line += ")"
    lines += ["", "---", "",
              f"**Browser QA Verdict:** {overall}", "",
              overall_line, "",
              "---", "", "## Results Table", "",
              "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |",
              "|---------|------|------|----------|----------|--------|---------|----------|"]
    for r in results:
        tid = f"UT-{r.get('journey', '')}"
        name = str(r.get("name", "")).replace("|", "\\|")
        exp = str(r.get("expected", "")).replace("|", "\\|")
        act = str(r.get("actual", "")).replace("|", "\\|")
        ev = r.get("evidence", "none") or "none"
        lines.append(f"| {tid} | {name} | regression | P1 | {exp} | {act} | {r.get('verdict', '')} | {ev} |")
    lines.append("")
    failed = [r for r in results if r.get("verdict") == "FAIL"]
    skipped = [r for r in results if r.get("verdict") == "SKIP"]
    if failed:
        lines += ["## Failed Tests", ""]
        for r in failed:
            lines += [f"### UT-{r.get('journey', '')} — {r.get('name', '')}", "",
                      "**Verdict:** FAIL",
                      f"**Failure:** {r.get('actual', '')}",
                      f"**Evidence:** `{r.get('evidence', 'none')}`", ""]
    if skipped:
        lines += ["## Skipped Tests", ""]
        for r in skipped:
            lines += [f"### UT-{r.get('journey', '')} — {r.get('name', '')}", "",
                      "**Verdict:** SKIPPED",
                      f"**Reason:** {r.get('actual', '')}", ""]
    blocked = [r for r in results if r.get("verdict") == "BLOCKED"]
    if blocked:
        lines += ["## Blocked Tests", "",
                   "_Not a journey failure — the backend was unreachable before this journey (or any "
                   "other in this run) was ever replayed. Distinct from FAIL: FAIL means the journey's "
                   "own assertions did not hold; BLOCKED means they were never checked._", ""]
        for r in blocked:
            lines += [f"### UT-{r.get('journey', '')} — {r.get('name', '')}", "",
                      "**Verdict:** BLOCKED",
                      f"**Reason:** {r.get('actual', '')}", ""]
    lines += ["## Environment", "",
              f"- **Frontend URL:** {frontend_url}",
              f"- **Browser:** Chromium via Playwright (deterministic replay, {mode})",
              f"- **Test Date:** {_today()}", ""]
    return "\n".join(lines)


def _emit_script_step(lines: list[str], s: dict) -> None:
    n = f"{int(s['n']):02d}"
    tag = "  [NEW]" if s.get("new") else ""
    lines.append(f"### Step {n} — {s.get('title', '')}{tag}")
    lines.append("")
    if s.get("narration"):
        lines.append(f"- **Narration:** {s['narration']}")
    if s.get("action"):
        lines.append(f"- **Action:** {s['action']}")
    if s.get("point_out"):
        lines.append(f"- **Point out:** {s['point_out']}")
    if s.get("screenshot"):
        lines.append(f"- **Screenshot:** {s['screenshot']}")
    lines.append("")


def render_script_md(phase_id: str, frontend_url: str, iteration, steps: list[dict],
                     mode: str) -> str:
    """Emit a renderer-compatible demo-script.md from the JSON (single source of
    truth). The renderer keys off `### Step NN` headings and `- **Narration:**`
    lines; Highlights steps carry a screenshot, Full-tour steps are text-only."""
    hi = [s for s in steps if s.get("section", "highlights") != "full_tour"]
    full = [s for s in steps if s.get("section", "highlights") == "full_tour"]
    lines = [f"# Demo Script — {phase_id}", ""]
    lines.append(f"**Mode:** {mode}")
    lines.append(f"**Date:** {_today()}")
    lines.append(f"**Frontend URL:** {frontend_url}")
    if iteration is not None:
        lines.append(f"**Iteration:** {iteration}")
    lines += ["", "## Highlights", ""]
    for s in hi:
        _emit_script_step(lines, s)
    if full:
        lines += ["## Full tour (text only)", ""]
        for s in full:
            _emit_script_step(lines, s)
    return "\n".join(lines)


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_text_chunk(keyword: str, text: str) -> bytes:
    """One PNG `tEXt` chunk: length + type + (keyword NUL text) + CRC32."""
    payload = (keyword.encode("latin-1", "replace")[:79] + b"\x00"
               + text.encode("latin-1", "replace"))
    return (struct.pack(">I", len(payload)) + b"tEXt" + payload
            + struct.pack(">I", zlib.crc32(b"tEXt" + payload) & 0xFFFFFFFF))


def png_with_provenance(raw: bytes, entries: list[tuple[str, str]]) -> bytes:
    """Return `raw` with provenance `tEXt` chunks inserted directly after IHDR.

    WHY (ops-hardening iter-45, audit F1): verify mode captures ONE end-state
    screenshot per journey, so two journeys whose last step lands on the same
    page in the same state produce BYTE-IDENTICAL files — J-03 and J-04 both end
    on `/data`, and both captures hashed `9d77429b…`. The regression check that
    exists to prove every journey got its OWN capture (never one file re-cited by
    several journeys — the iter-43 defect) then fires on evidence that is in fact
    honest, and cannot distinguish that case from the dishonest one it targets.

    Stamping the journey's own identity into the file settles it by construction:
    each capture is unique because its provenance differs, and the PNG says which
    journey it belongs to when read directly. `tEXt` is a standard ANCILLARY
    chunk — decoders ignore what they don't know, so NOT ONE PIXEL changes. This
    annotates the file, never the page: overlaying a banner on the rendered page
    before capture would have altered the very evidence being recorded.

    Returns `raw` unchanged if it is not a PNG with a leading IHDR (never raises
    — evidence capture must not be able to fail a replay).
    """
    if not raw.startswith(_PNG_SIGNATURE) or len(raw) < 16 or raw[12:16] != b"IHDR":
        return raw
    ihdr_end = 8 + 8 + struct.unpack(">I", raw[8:12])[0] + 4  # sig + len/type + data + crc
    if ihdr_end > len(raw):
        return raw
    stamped = b"".join(_png_text_chunk(k, v) for k, v in entries)
    return raw[:ihdr_end] + stamped + raw[ihdr_end:]


# ── self-test (written first, TDD) ───────────────────────────────────────────
# Each _t_* function checks one behavior. The harness runs them all and reports
# every failure, so a fresh run shows the full RED surface at once.


def _t_normalize_url_relative() -> None:
    assert normalize_url("http://localhost:3017", "/items/new") == "http://localhost:3017/items/new"
    assert normalize_url("http://localhost:3017/", "items") == "http://localhost:3017/items"
    assert normalize_url("http://localhost:3017", "/") == "http://localhost:3017/"
    assert normalize_url("http://localhost:3017", "") == "http://localhost:3017/"
    assert normalize_url("http://localhost:3017", "/x?a=1") == "http://localhost:3017/x?a=1"


def _t_normalize_url_rewrites_localhost() -> None:
    # The port-offset fix: a hardcoded :3000 from QA artifacts must be rewritten
    # to the actual base_url (the offset dev-port).
    assert normalize_url("http://localhost:3017", "http://localhost:3000/items/new") == "http://localhost:3017/items/new"
    assert normalize_url("http://localhost:3017", "http://127.0.0.1:3000/x") == "http://localhost:3017/x"


def _t_normalize_url_keeps_external() -> None:
    # A genuinely external absolute URL is left untouched.
    assert normalize_url("http://localhost:3017", "https://example.com/x") == "https://example.com/x"


def _t_validate_accepts_good() -> None:
    data = {
        "schema_version": 1,
        "base_url": "http://localhost:3000",
        "steps": [
            {"n": 1, "action": {"type": "goto", "url": "/"}},
            {"n": 2, "action": {"type": "click", "target": {"role": "button", "name": "Save"}}},
            {"n": 3, "action": {"type": "fill", "target": {"label": "Title"}, "text": "Q3"}},
        ],
    }
    assert validate_script(data) == [], validate_script(data)


def _t_validate_rejects_missing_steps() -> None:
    assert validate_script({"schema_version": 1}) != []


def _t_validate_rejects_bad_action() -> None:
    data = {"schema_version": 1, "steps": [{"n": 1, "action": {"type": "frobnicate"}}]}
    assert validate_script(data) != []
    # goto without url, fill without text
    assert validate_script({"schema_version": 1, "steps": [{"n": 1, "action": {"type": "goto"}}]}) != []
    assert validate_script({"schema_version": 1, "steps": [
        {"n": 1, "action": {"type": "fill", "target": {"label": "x"}}}]}) != []


def _t_validate_accepts_not_yet() -> None:
    # A "nothing to show yet" script legitimately has no steps.
    assert validate_script({"schema_version": 1, "not_yet": True, "steps": []}) == []
    assert validate_script({"schema_version": 1, "not_yet": True}) == []


def _t_resolve_role_degrades_to_text() -> None:
    assert resolve_spec({"role": "button", "name": "Save"}) == [
        ("role", "button", "Save"), ("text", None, "Save")]


def _t_resolve_label_degrades_to_placeholder() -> None:
    assert resolve_spec({"label": "Title"}) == [
        ("label", None, "Title"), ("placeholder", None, "Title")]


def _t_resolve_simple_kinds() -> None:
    assert resolve_spec({"text": "Save"}) == [("text", None, "Save")]
    assert resolve_spec({"placeholder": "Email"}) == [("placeholder", None, "Email")]
    assert resolve_spec({"testid": "submit"}) == [("testid", None, "submit")]
    assert resolve_spec({"css": ".btn"}) == [("css", None, ".btn")]


def _t_verdict_matrix() -> None:
    assert compute_verdict(any_captured=True, has_soft_notes=False, not_yet=False) == "RECORDED"
    assert compute_verdict(any_captured=True, has_soft_notes=True, not_yet=False) == "RECORDED_WITH_NOTES"
    assert compute_verdict(any_captured=False, has_soft_notes=False, not_yet=False) == "SKIPPED"
    assert compute_verdict(any_captured=True, has_soft_notes=True, not_yet=True) == "NOT_YET"


def _t_results_md_roundtrip() -> None:
    import render_iteration_summary as R
    steps = [
        {"n": 1, "title": "Open dashboard", "journey": "J-04", "new": True,
         "screenshot": "reports/demo/x/step-01.png"},
        {"n": 2, "title": "Open the form", "journey": "", "new": False,
         "screenshot": "reports/demo/x/step-02.png"},
    ]
    md = render_results_md(phase_id="x", frontend_url="http://localhost:3000", iteration=3,
                           captured=steps, soft_notes=["Step 02 — toast did not appear"],
                           verdict="RECORDED_WITH_NOTES", mode="record")
    verdict, parsed, notes = R._parse_demo_results(md)
    assert verdict == "RECORDED_WITH_NOTES", verdict
    assert [s["number"] for s in parsed] == [1, 2], parsed
    assert parsed[0]["title"] == "Open dashboard"
    assert parsed[0]["is_new"] is True
    assert parsed[0]["journey"] == "J-04"
    assert parsed[0]["screenshot"] == "reports/demo/x/step-01.png"
    assert parsed[1]["is_new"] is False
    assert parsed[1]["journey"] == ""
    assert len(notes) == 1, notes


def _t_script_md_roundtrip() -> None:
    import render_iteration_summary as R
    steps = [
        {"n": 1, "title": "Open dashboard", "narration": "We open the home page.",
         "action": "Navigate to /", "point_out": "the sidebar",
         "screenshot": "reports/demo/x/step-01.png", "new": True},
        {"n": 2, "title": "Open the form", "narration": "We open the form.",
         "action": "Click New Report", "point_out": "a blank form",
         "screenshot": "reports/demo/x/step-02.png", "new": False},
    ]
    md = render_script_md(phase_id="x", frontend_url="http://localhost:3000", iteration=3,
                          steps=steps, mode="record")
    narr = R._parse_demo_script_narrations(md)
    assert narr.get(1) == "We open the home page.", narr
    assert narr.get(2) == "We open the form.", narr


def _t_regression_verdict_matrix() -> None:
    assert compute_regression_verdict([]) == "SKIPPED"
    assert compute_regression_verdict([{"verdict": "PASS"}, {"verdict": "PASS"}]) == "PASS"
    assert compute_regression_verdict([{"verdict": "PASS"}, {"verdict": "FAIL"}]) == "FAIL"
    assert compute_regression_verdict([{"verdict": "SKIP"}, {"verdict": "SKIP"}]) == "SKIPPED"
    assert compute_regression_verdict([{"verdict": "SKIP"}, {"verdict": "PASS"}]) == "PASS"
    assert compute_regression_verdict([{"verdict": "FAIL"}, {"verdict": "SKIP"}]) == "FAIL"
    # ops-hardening iter-39 (TC-5/TC-6): BLOCKED is a DISTINCT class from FAIL — an all-BLOCKED
    # run (backend unreachable) must never present as the same overall verdict as a real
    # regression, and a genuine FAIL must still win over a BLOCKED row if the two ever mix.
    assert compute_regression_verdict([{"verdict": "BLOCKED"}, {"verdict": "BLOCKED"}]) == "BLOCKED"
    assert compute_regression_verdict([{"verdict": "BLOCKED"}, {"verdict": "SKIP"}]) == "BLOCKED"
    assert compute_regression_verdict([{"verdict": "FAIL"}, {"verdict": "BLOCKED"}]) == "FAIL"


def _t_regression_results_md() -> None:
    results = [
        {"journey": "J-06", "name": "View dashboard", "verdict": "PASS",
         "expected": "e", "actual": "ok", "evidence": "reports/qa/x/J-06-verify.png"},
        {"journey": "J-07", "name": "Filter the table", "verdict": "FAIL",
         "expected": "e", "actual": 'step 03 expected "Results" did not appear',
         "evidence": "reports/qa/x/J-07-verify.png"},
        {"journey": "J-09", "name": "Export report", "verdict": "SKIP",
         "expected": "e", "actual": "no golden script on file", "evidence": "none"},
    ]
    md = render_regression_results_md("goal-x-iter-5", "http://localhost:3017", 5, results, "verify")
    # one journey FAILED → overall FAIL, with the marker line the goal-evaluator parses
    assert "**Browser QA Verdict:** FAIL" in md, md
    assert "## Results Table" in md
    # one UT row per journey, using the journey id as the test id
    for tid in ("UT-J-06", "UT-J-07", "UT-J-09"):
        assert tid in md, tid
    assert "## Failed Tests" in md and "## Skipped Tests" in md
    assert "1/3 journeys passed (1 skipped)" in md, md


def _t_blocked_results_md() -> None:
    # ops-hardening iter-39 (TC-5): an all-BLOCKED run renders a BLOCKED headline (never FAIL),
    # a distinct "## Blocked Tests" section (never conflated with "## Failed Tests"), and the
    # blocked count in the summary line.
    results = [
        {"journey": "J-01", "name": "J-01", "verdict": "BLOCKED",
         "expected": "backend answers GET http://localhost:1/api/health with HTTP 200 before replay",
         "actual": "backend unreachable: GET http://localhost:1/api/health did not answer 200",
         "evidence": "none"},
        {"journey": "J-03", "name": "J-03", "verdict": "BLOCKED",
         "expected": "backend answers GET http://localhost:1/api/health with HTTP 200 before replay",
         "actual": "backend unreachable: GET http://localhost:1/api/health did not answer 200",
         "evidence": "none"},
    ]
    md = render_regression_results_md("goal-x-iter-39", "http://localhost:3017", 39, results, "verify")
    assert "**Browser QA Verdict:** BLOCKED" in md, md
    assert "**Browser QA Verdict:** FAIL" not in md, md
    assert "## Blocked Tests" in md and "## Failed Tests" not in md, md
    assert "2 blocked — backend unreachable" in md, md
    for tid in ("UT-J-01", "UT-J-03"):
        assert tid in md, tid


def _t_resolve_backend_health_url() -> None:
    # explicit override always wins.
    assert resolve_backend_health_url("http://localhost:3017", "http://x:9/y") == "http://x:9/y"
    # no override, no CHAIN_BACKEND_PORT env -> falls back to the default port (8000) + this
    # project's real health path (/api/health, NOT the framework's generic /health -- every
    # Trendora route is namespaced under /api).
    saved = os.environ.pop("CHAIN_BACKEND_PORT", None)
    try:
        url = resolve_backend_health_url("http://localhost:3017", None)
        assert url == "http://localhost:8000/api/health", url
        os.environ["CHAIN_BACKEND_PORT"] = "9142"
        url2 = resolve_backend_health_url("http://localhost:3017", None)
        assert url2 == "http://localhost:9142/api/health", url2
    finally:
        if saved is None:
            os.environ.pop("CHAIN_BACKEND_PORT", None)
        else:
            os.environ["CHAIN_BACKEND_PORT"] = saved


def _t_probe_backend_health() -> None:
    # No server at all on this port (connection refused) -> honestly False, never an exception.
    assert probe_backend_health("http://127.0.0.1:1/api/health", timeout=1.0) is False

    # A real local HTTP server that answers exactly 200 -> True; a 404 (server up, wrong path,
    # exactly the pre-fix framework-default-path bug this closes) -> False.
    import http.server
    import threading

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - stdlib method name
            if self.path == "/api/health":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"{}")
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, *_a):  # noqa: D401 - silence per-request stderr noise
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert probe_backend_health(f"http://127.0.0.1:{port}/api/health", timeout=2.0) is True
        assert probe_backend_health(f"http://127.0.0.1:{port}/health", timeout=2.0) is False
    finally:
        server.shutdown()
        thread.join(timeout=2.0)


def _make_sentinel_fixture(tmp_dir: str, dates_with_bars: list, snapshotted_dates: tuple = (),
                           non_benchmark_dates: tuple = ()) -> str:
    """A throwaway sqlite fixture with the same two tables/columns the real committed DB
    carries (`daily_prices.date`/`.symbol`, `scanner_runs.asof_date`) — enough for
    `resolve_sentinel_date` to run its real query against, without touching
    `apps/backend/data/trendora.db`. `dates_with_bars` get a SPY row (the default benchmark);
    `non_benchmark_dates` get a bar for a DIFFERENT symbol only — reproducing the real
    committed seed's own shape (1996-2004 has other symbols' bars but no SPY at all)."""
    db_path = os.path.join(tmp_dir, "sentinel-fixture.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE daily_prices (id INTEGER PRIMARY KEY, symbol TEXT, date TEXT)")
    conn.execute("CREATE TABLE scanner_runs (id INTEGER PRIMARY KEY, asof_date TEXT)")
    for d in dates_with_bars:
        conn.execute("INSERT INTO daily_prices (symbol, date) VALUES (?, ?)", ("SPY", d))
    for d in non_benchmark_dates:
        conn.execute("INSERT INTO daily_prices (symbol, date) VALUES (?, ?)", ("AAPL", d))
    for d in snapshotted_dates:
        conn.execute("INSERT INTO scanner_runs (asof_date) VALUES (?)", (d,))
    conn.commit()
    conn.close()
    return db_path


def _t_resolve_sentinel_date_requires_benchmark_bar() -> None:
    # Real bug this test locks in (found live against apps/backend/data/trendora.db,
    # 2026-08-11): a date can have SOME symbol's bar without carrying a SPY bar (this
    # committed seed's own 1996-2004 span is exactly that shape) -- a resolver that only
    # checked "any daily_prices row" would hand back a date the real backfill/scanner_runs
    # computation cannot use (every scanner_runs row is computed against `benchmark`="SPY").
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_sentinel_fixture(
            tmp, dates_with_bars=["2005-01-05"], non_benchmark_dates=["2005-01-03", "2005-01-04"])
        got = resolve_sentinel_date(db, "2005-01-01", "2005-01-31")
        assert got == "2005-01-05", got  # the two non-SPY dates must be skipped, not returned


def _t_resolve_sentinel_date_picks_earliest_eligible() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_sentinel_fixture(
            tmp, ["2000-01-05", "2000-01-04", "2000-01-06"], snapshotted_dates=["2000-01-04"])
        got = resolve_sentinel_date(db, "2000-01-01", "2000-01-31")
        assert got == "2000-01-05", got  # earliest date that is NOT already snapshotted


def _t_resolve_sentinel_date_fails_when_window_exhausted() -> None:
    # Error case (Testing Requirements): zero eligible dates in the window must fail
    # explicitly, never silently reuse an already-snapshotted date.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_sentinel_fixture(tmp, ["2000-01-05"], snapshotted_dates=["2000-01-05"])
        try:
            resolve_sentinel_date(db, "2000-01-01", "2000-01-31")
            raise AssertionError("expected RuntimeError: window exhausted")
        except RuntimeError as exc:
            assert "no eligible" in str(exc), exc


def _t_resolve_sentinel_date_missing_db() -> None:
    try:
        resolve_sentinel_date("/nonexistent/path/does-not-exist-demo-runner-fixture.db")
        raise AssertionError("expected RuntimeError: db not found")
    except RuntimeError as exc:
        assert "not found" in str(exc), exc


def _t_resolve_sentinel_date_self_renews_after_consumption() -> None:
    # TC-3: given a throwaway sqlite fixture seeded with a scanner_runs row for the date the
    # resolver most recently returned, when the resolver is invoked again against that same
    # fixture, then it returns a DIFFERENT date (not the just-consumed one) with 0
    # scanner_runs rows for it -- proven at the unit level, not a second live 20-minute
    # browser replay (this iteration's own OUT OF SCOPE note).
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_sentinel_fixture(tmp, ["2000-01-05", "2000-01-06", "2000-01-07"])
        first = resolve_sentinel_date(db, "2000-01-01", "2000-01-31")
        assert first == "2000-01-05", first
        conn = sqlite3.connect(db)
        conn.execute("INSERT INTO scanner_runs (asof_date) VALUES (?)", (first,))
        conn.commit()
        conn.close()
        second = resolve_sentinel_date(db, "2000-01-01", "2000-01-31")
        assert second != first, (first, second)
        assert second == "2000-01-06", second


def _t_script_needs_sentinel_detects_token() -> None:
    assert script_needs_sentinel(
        {"steps": [{"action": {"type": "fill", "text": SENTINEL_TOKEN}}]}) is True
    assert script_needs_sentinel(
        {"steps": [{"action": {"type": "fill", "text": "2010-01-01"}}]}) is False


def _t_substitute_sentinel_in_script() -> None:
    script = {
        "name": f"... target date {SENTINEL_TOKEN} must have 0 snapshot rows ...",
        "steps": [
            {"n": 1, "action": {"type": "fill", "target": {"testid": "x"}, "text": SENTINEL_TOKEN}},
            {"n": 2, "action": {"type": "click", "target": {"text": SENTINEL_TOKEN}},
             "expect": {"text": f"Immutable snapshot — as of {SENTINEL_TOKEN}"}},
        ],
    }
    out = substitute_sentinel_in_script(script, "2000-01-05")
    assert SENTINEL_TOKEN not in json.dumps(out)
    assert out["steps"][0]["action"]["text"] == "2000-01-05"
    assert out["steps"][1]["action"]["target"]["text"] == "2000-01-05"
    assert out["steps"][1]["expect"]["text"] == "Immutable snapshot — as of 2000-01-05"
    assert "2000-01-05" in out["name"], out["name"]
    # the SAME resolved date landed everywhere the token appeared.
    assert SENTINEL_TOKEN in script["name"], "original script must be left untouched"


def _t_resolve_and_substitute_sentinel_noop_without_token() -> None:
    script = {"name": "plain", "steps": [{"n": 1, "action": {"type": "goto", "url": "/"}}]}
    out, resolved = resolve_and_substitute_sentinel(script, "/nonexistent/does-not-matter.db")
    assert out is script, "unchanged script object when the token is absent (no DB touched)"
    assert resolved is None


def _t_resolve_and_substitute_sentinel_propagates_failure() -> None:
    script = {"name": SENTINEL_TOKEN, "steps": [{"n": 1, "action": {"type": "goto", "url": "/"}}]}
    try:
        resolve_and_substitute_sentinel(script, "/nonexistent/does-not-matter.db")
        raise AssertionError("expected RuntimeError to propagate when the token IS present")
    except RuntimeError:
        pass


def _t_default_sentinel_db_path_repo_root() -> None:
    assert default_sentinel_db_path("/x/y") == Path("/x/y/apps/backend/data/trendora.db")


def _t_run_verify_blocked_when_backend_unreachable() -> None:
    # TC-5 end-to-end (no real browser launch reached — the probe short-circuits BEFORE
    # Playwright ever opens a page): backend unreachable -> rc 7, every journey BLOCKED, never
    # FAIL, and the written results file says so.
    import argparse
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        results_path = os.path.join(tmp, "results.md")
        opts = argparse.Namespace(
            scripts_dir=tmp, journeys="J-01,J-03", phase_id="goal-x-iter-39", iteration=39,
            evidence_dir=None, results=results_path, repo_root=tmp, timeout_ms=8000,
            backend_health_url="http://127.0.0.1:1/api/health",  # nothing listens on port 1
        )
        rc = run_verify(opts, "http://localhost:3017")
        assert rc == 7, rc
        text = Path(results_path).read_text(encoding="utf-8")
        assert "**Browser QA Verdict:** BLOCKED" in text, text
        assert "**Browser QA Verdict:** FAIL" not in text, text
        assert "UT-J-01" in text and "UT-J-03" in text, text
        assert "| BLOCKED |" in text and "| FAIL |" not in text, text


def _t_launch_chromium_retries() -> None:
    # A flaky launch succeeds on the retry; a dead one raises after N attempts
    # (no browser involved — fake pw objects).
    class _FlakyChromium:
        calls = 0
        @staticmethod
        def launch(**_kw):
            _FlakyChromium.calls += 1
            if _FlakyChromium.calls < 2:
                raise RuntimeError("Timeout 45000ms exceeded launching chromium")
            return "browser-handle"

    class _FlakyPW:
        chromium = _FlakyChromium

    assert _launch_chromium(_FlakyPW, headless=True, attempts=2) == "browser-handle"
    assert _FlakyChromium.calls == 2

    class _DeadChromium:
        calls = 0
        @staticmethod
        def launch(**_kw):
            _DeadChromium.calls += 1
            raise RuntimeError("boom")

    class _DeadPW:
        chromium = _DeadChromium

    try:
        _launch_chromium(_DeadPW, headless=True, attempts=2)
        raise AssertionError("expected the launch failure to propagate")
    except RuntimeError as exc:
        assert "boom" in str(exc)
    assert _DeadChromium.calls == 2


class _FakeLocator:
    """Duck-typed Playwright Locator, just enough surface for `_do_action`/`_find` to work
    against it: `.first`, `.wait_for(...)` (raises TimeoutError when `fail=True`, else
    no-ops), `.click(...)` / `.fill(...)` (spy-recorded)."""

    def __init__(self, spy: dict, name: str, fail: bool = False):
        self._spy = spy
        self._name = name
        self._fail = fail

    @property
    def first(self):
        return self

    def wait_for(self, state: str = "visible", timeout: float = 0):
        if self._fail:
            raise TimeoutError(f"fake: {self._name} did not become visible")

    def click(self, timeout: float = 0):
        self._spy["click_calls"] = self._spy.get("click_calls", 0) + 1
        self._spy.setdefault("clicked", []).append(self._name)

    def fill(self, text: str, timeout: float = 0):
        if self._fail:
            raise TimeoutError(f"fake: cannot fill {self._name}")
        self._spy.setdefault("filled", []).append((self._name, text))


class _FakePage:
    """Duck-typed Playwright Page — only the methods `_do_action`/`_settle_for_capture`
    actually call. Every method NOT defined here (e.g. `.locator()`, `.evaluate()`,
    `.wait_for_load_state()`) is absent on purpose: every real call site wraps those in a
    bare `except Exception: pass`, so a missing attribute is silently swallowed exactly like
    a real best-effort miss — no need to fake the whole Playwright surface."""

    def __init__(self, spy: dict, fail_target: "tuple | None" = None):
        self._spy = spy
        self._fail_target = fail_target

    def _loc(self, kind: str, value) -> _FakeLocator:
        return _FakeLocator(self._spy, f"{kind}:{value}", fail=(kind, value) == self._fail_target)

    def get_by_role(self, role: str, name: str = ""):
        return self._loc("role", (role, name))

    def get_by_text(self, text: str):
        return self._loc("text", text)

    def get_by_label(self, label: str):
        return self._loc("label", label)

    def get_by_placeholder(self, placeholder: str):
        return self._loc("placeholder", placeholder)

    def get_by_test_id(self, testid: str):
        return self._loc("testid", testid)

    def goto(self, url: str, wait_until: "str | None" = None, timeout: float = 0):
        self._spy.setdefault("goto", []).append(url)

    def wait_for_timeout(self, ms: int):
        pass

    def screenshot(self, path: "str | None" = None):
        self._spy.setdefault("screenshots", []).append(path)


class _FakeSettlingLocator:
    """Duck-typed Locator whose visibility depends on the page's own simulated phase — the minimum
    surface `_settle_for_capture`'s `exp`-aware wait (`_check_expect` -> `get_by_text(...).wait_for`)
    needs. See `_FakeSettlingPage` for the model this exercises."""

    def __init__(self, page: "_FakeSettlingPage", text: str):
        self._page = page
        self._text = text

    @property
    def first(self):
        return self

    def wait_for(self, state: str = "visible", timeout: float = 0):
        page = self._page
        if self._text == page.before_text:
            if page.phase != "before":
                raise TimeoutError(f"fake: {self._text!r} not visible in phase {page.phase!r}")
            return
        if self._text == page.gate_text:
            n = page.attempts.get(self._text, 0) + 1
            page.attempts[self._text] = n
            if n >= page.ready_after:
                page.phase = "after"
                return
            raise TimeoutError(f"fake: {self._text!r} not visible yet (poll {n}/{page.ready_after})")
        raise TimeoutError(f"fake: unexpected text {self._text!r}")


class _FakeAlwaysReadyLocator:
    """Always-visible, always-clickable no-op locator for a step's MUTATING control target (e.g. a
    'Start' button) in `_FakeSettlingPage` — always found and clicked; the state change it triggers is
    observed later via the page's gate-text poll count (see `_FakeSettlingLocator`), not synchronously
    at click time, mirroring how a real backfill's effect surfaces through a LATER read."""

    @property
    def first(self):
        return self

    def wait_for(self, state: str = "visible", timeout: float = 0):
        return

    def click(self, timeout: float = 0):
        return


class _FakeSettlingPage:
    """Models a step whose real (backend-driven) content becomes visible only after >= `ready_after`
    polls for its OWN expect text — an eventually-consistent read, the same shape a real async
    re-render/poll-tick produces. `before_text` is trivially visible while `phase == "before"`;
    `gate_text` only becomes visible (and flips `phase` to `"after"`) once it has been polled
    `ready_after` times — enough to distinguish a settle that actively re-polls the step's own `exp`
    from one that does not (ops-hardening iter-77 / iter-76/d: the byte-identical before/after
    walkthrough-frame defect). `screenshot()` records the phase AT CAPTURE TIME, so a test can assert
    the two captured frames reflect genuinely different states, not the same one twice."""

    def __init__(self, before_text: str, gate_text: str, ready_after: int = 2):
        self.phase = "before"
        self.before_text = before_text
        self.gate_text = gate_text
        self.ready_after = ready_after
        self.attempts: dict[str, int] = {}
        self.screenshots: list[tuple[str, str]] = []

    def get_by_text(self, text: str) -> _FakeSettlingLocator:
        return _FakeSettlingLocator(self, text)

    def get_by_role(self, role: str, name: str = "") -> _FakeAlwaysReadyLocator:
        return _FakeAlwaysReadyLocator()

    def goto(self, url: str, wait_until: "str | None" = None, timeout: float = 0):
        pass

    def wait_for_timeout(self, ms: int):
        pass

    def screenshot(self, path: "str | None" = None):
        self.screenshots.append((path, self.phase))


def _t_settle_for_capture_before_after_frames_differ_when_state_changes() -> None:
    """TC-9 (ops-hardening iter-77, iter-76/d): a state-changing step's 'after' capture must reflect
    the ACTUAL post-change content, never a stale pre-change frame identical to the 'before' capture —
    the exact defect observed in iter-76's recorded gallery (`reports/demo/goal-ops-hardening-iter-76/`
    step-05.png and step-06.png, and step-04.png/step-07.png, came back pairwise byte-identical).

    `_FakeSettlingPage`'s gate text only becomes visible on its SECOND poll. The record loop's own
    upstream `_check_expect` call (unrelated to this fix, unchanged) always performs poll #1 and always
    finds it not-yet-visible on this fixture (a soft note is expected and asserted below). Only
    `_settle_for_capture`'s NEW `exp`-aware re-poll (this iteration's fix) performs poll #2, which is
    the one that actually observes the change — so this test FAILS against the pre-fix
    `_settle_for_capture(page, budget_ms)` (no `exp` parameter at all, so the gate text is never polled
    a second time and the 'after' step's screenshot is captured before the change lands), and PASSES
    only once the fix threads `exp` through into an active re-poll."""
    import tempfile
    page = _FakeSettlingPage(before_text="No jobs yet", gate_text="Completed", ready_after=2)
    steps = [
        {"n": 1, "journey": "J-05", "title": "Before: job history is empty",
         "action": {"type": "goto", "url": "/data"}, "expect": {"text": "No jobs yet"}},
        {"n": 2, "journey": "J-05", "title": "After: the backfill has completed",
         "action": {"type": "click", "target": {"role": "button", "name": "Start"}},
         "expect": {"text": "Completed"}},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        _captured, soft_notes, _script_steps = _record_steps(
            page, steps, "http://localhost:3000", 4000, Path(tmp), None)

    assert len(page.screenshots) == 2, page.screenshots
    before_phase = page.screenshots[0][1]
    after_phase = page.screenshots[1][1]
    assert before_phase == "before", page.screenshots
    assert after_phase == "after", (
        "the after-step capture must reflect the real post-change state, not a stale frame "
        f"identical to the before capture: {page.screenshots}"
    )
    assert before_phase != after_phase, "before/after frames must not capture the same state"
    # The record loop's OWN first poll (before this fix's re-poll ever runs) genuinely misses on this
    # fixture, so a soft note for step 2 is the expected, honest behavior — not silently swallowed.
    assert any("02" in note and "did not appear" in note for note in soft_notes), soft_notes


def _t_run_record_never_clicks_after_failed_precondition() -> None:
    # TC-4: given a fake page/script fixture where step N's `fill` raises and step N+1 is a
    # `click` on `role: button`, when the record loop executes that script, then step N+1's
    # click is NEVER invoked (asserted via a call-count spy), a screenshot is still captured
    # for step N+1, and the results write-up carries a soft note naming the skip.
    import tempfile
    spy: dict = {}
    steps = [
        {"n": 1, "title": "Target one unsnapshotted historical trading day", "journey": "J-05",
         "action": {"type": "fill", "target": {"testid": "job-start-date"}, "text": "2010-11-22"}},
        {"n": 2, "title": "Start the backfill", "journey": "J-05",
         "action": {"type": "click", "target": {"role": "button", "name": "Start"}}},
    ]
    page = _FakePage(spy, fail_target=("testid", "job-start-date"))
    with tempfile.TemporaryDirectory() as tmp:
        captured, soft_notes, script_steps = _record_steps(
            page, steps, "http://localhost:3000", 4000, Path(tmp), None)
    assert spy.get("click_calls", 0) == 0, "the mutating click must never be invoked"
    assert len(captured) == 2, captured  # a screenshot is still captured for BOTH steps
    assert len(spy.get("screenshots", [])) == 2, spy
    assert any("step 02" in note.lower() and "skipped" in note.lower() for note in soft_notes), soft_notes
    assert len(script_steps) == 2


def _t_run_record_click_still_fires_without_a_prior_failure() -> None:
    # Control case: no preceding failure -> the mutating click IS performed normally.
    spy: dict = {}
    steps = [
        {"n": 1, "title": "Open the Data Manager", "action": {"type": "goto", "url": "/data"}},
        {"n": 2, "title": "Start the backfill", "action": {
            "type": "click", "target": {"role": "button", "name": "Start"}}},
    ]
    page = _FakePage(spy)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        captured, soft_notes, _script_steps = _record_steps(
            page, steps, "http://localhost:3000", 4000, Path(tmp), None)
    assert spy.get("click_calls", 0) == 1, "a click with no preceding failure must still fire"
    assert not any("skipped" in note.lower() for note in soft_notes), soft_notes


def _derive_demo_fixture() -> dict:
    # Matches the demo-narrator contract: every step carries a "journey" key,
    # "" on shared orientation steps (the untagged prefix).
    return {
        "schema_version": 1,
        "phase_id": "goal-x-iter-9",
        "name": "demo",
        "default_timeout_ms": 9000,
        "steps": [
            {"n": 1, "journey": "", "action": {"type": "goto", "url": "/"}, "narration": "open the app",
             "expect": {"text": "Home"}},
            {"n": 2, "journey": "J-07", "action": {"type": "click", "target": {"text": "Filters"}},
             "narration": "open filters"},
            {"n": 3, "journey": "J-07", "action": {"type": "expect"}, "expect": {"text": "Filter panel"},
             "timeout_ms": 4000},
            {"n": 4, "journey": "J-09", "action": {"type": "click", "target": {"text": "Export"}},
             "expect": {"text": "Exported"}},
        ],
    }


def _t_derive_happy() -> None:
    golden, reason = derive_golden_steps(_derive_demo_fixture(), "J-07")
    assert golden is not None, reason
    assert validate_script(golden) == [], golden
    # prefix (untagged step 1) + the 2 tagged steps, renumbered 1..3
    assert [s["n"] for s in golden["steps"]] == [1, 2, 3], golden["steps"]
    assert all(s["journey"] == "J-07" for s in golden["steps"])
    assert golden["steps"][0]["action"]["type"] == "goto"
    # demo-only fields are stripped
    assert all("narration" not in s for s in golden["steps"])
    assert golden["steps"][2]["timeout_ms"] == 4000
    assert golden["journey"] == "J-07" and golden["default_timeout_ms"] == 9000


def _t_derive_rejects_untagged_journey() -> None:
    golden, reason = derive_golden_steps(_derive_demo_fixture(), "J-99")
    assert golden is None and "no steps tagged" in reason, (golden, reason)


def _t_derive_rejects_no_expect() -> None:
    demo = _derive_demo_fixture()
    for s in demo["steps"]:
        if s.get("journey") == "J-07":
            s.pop("expect", None)
    golden, reason = derive_golden_steps(demo, "J-07")
    assert golden is None and "expect" in reason, (golden, reason)


def _t_derive_rejects_no_goto_open() -> None:
    demo = _derive_demo_fixture()
    demo["steps"] = demo["steps"][1:]   # drop the untagged goto prefix
    golden, reason = derive_golden_steps(demo, "J-07")
    assert golden is None and "goto" in reason, (golden, reason)


def _t_derive_rejects_invalid_demo() -> None:
    golden, reason = derive_golden_steps({"schema_version": 1, "steps": []}, "J-07")
    assert golden is None and "invalid" in reason, (golden, reason)
    golden, reason = derive_golden_steps({"schema_version": 1, "not_yet": True}, "J-07")
    assert golden is None, (golden, reason)


def _t_derive_prefix_without_journey_key() -> None:
    # Legacy/hand-written demos may omit the journey key entirely on setup
    # steps — the prefix scan must treat that the same as journey:"".
    demo = _derive_demo_fixture()
    del demo["steps"][0]["journey"]
    golden, reason = derive_golden_steps(demo, "J-07")
    assert golden is not None, reason
    assert golden["steps"][0]["action"]["type"] == "goto"


def _png_chunks(raw: bytes) -> list[tuple[bytes, bytes]]:
    """Parse a PNG into `[(type, data), …]` — the self-test's independent reader,
    so the stamp is verified by decoding it, never by trusting the writer."""
    out, i = [], len(_PNG_SIGNATURE)
    while i + 8 <= len(raw):
        n = struct.unpack(">I", raw[i:i + 4])[0]
        typ, data = raw[i + 4:i + 8], raw[i + 8:i + 8 + n]
        assert zlib.crc32(typ + data) & 0xFFFFFFFF == struct.unpack(">I", raw[i + 8 + n:i + 12 + n])[0], \
            f"chunk {typ!r} CRC mismatch — the stamped file is not a valid PNG"
        out.append((typ, data))
        i += 12 + n
    return out


def _tiny_png() -> bytes:
    """A minimal, valid 1x1 greyscale PNG — the fixture two 'identical captures' share."""
    def chunk(typ: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))
    return (_PNG_SIGNATURE
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\x00"))
            + chunk(b"IEND", b""))


def _t_png_provenance_makes_identical_captures_distinct() -> None:
    """iter-45 audit F1 — the exact J-03/J-04 case: two journeys, one identical
    end-state capture. After stamping, the files must differ, must each name their
    OWN journey, and must still be valid PNGs whose pixel data is untouched."""
    raw = _tiny_png()
    a = png_with_provenance(raw, [("Journey", "J-03"), ("Phase", "iter-45")])
    b = png_with_provenance(raw, [("Journey", "J-04"), ("Phase", "iter-45")])
    assert a != b, "two journeys' captures must not stay byte-identical after stamping"

    for stamped, jid in ((a, "J-03"), (b, "J-04")):
        chunks = _png_chunks(stamped)                      # asserts every CRC
        types = [t for t, _ in chunks]
        assert types[0] == b"IHDR" and types[-1] == b"IEND", types
        assert b"tEXt" in types
        texts = [d for t, d in chunks if t == b"tEXt"]
        assert any(d.startswith(b"Journey\x00") and d.endswith(jid.encode()) for d in texts), texts
        # NOT ONE PIXEL changed: every non-tEXt chunk is byte-identical to the original.
        assert [(t, d) for t, d in chunks if t != b"tEXt"] == _png_chunks(raw)


def _t_png_provenance_leaves_a_non_png_untouched() -> None:
    """Evidence capture must never be able to fail a replay: anything that is not
    a PNG with a leading IHDR comes back byte-for-byte unchanged, never an error."""
    assert png_with_provenance(b"", [("Journey", "J-03")]) == b""
    assert png_with_provenance(b"not a png at all", [("Journey", "J-03")]) == b"not a png at all"
    truncated = _tiny_png()[:12]
    assert png_with_provenance(truncated, [("Journey", "J-03")]) == truncated


_SELF_TEST_CHECKS = [
    _t_png_provenance_makes_identical_captures_distinct,
    _t_png_provenance_leaves_a_non_png_untouched,
    _t_normalize_url_relative,
    _t_normalize_url_rewrites_localhost,
    _t_normalize_url_keeps_external,
    _t_validate_accepts_good,
    _t_validate_rejects_missing_steps,
    _t_validate_rejects_bad_action,
    _t_validate_accepts_not_yet,
    _t_resolve_role_degrades_to_text,
    _t_resolve_label_degrades_to_placeholder,
    _t_resolve_simple_kinds,
    _t_verdict_matrix,
    _t_results_md_roundtrip,
    _t_script_md_roundtrip,
    _t_regression_verdict_matrix,
    _t_regression_results_md,
    _t_blocked_results_md,
    _t_resolve_backend_health_url,
    _t_probe_backend_health,
    _t_resolve_sentinel_date_picks_earliest_eligible,
    _t_resolve_sentinel_date_requires_benchmark_bar,
    _t_resolve_sentinel_date_fails_when_window_exhausted,
    _t_resolve_sentinel_date_missing_db,
    _t_resolve_sentinel_date_self_renews_after_consumption,
    _t_script_needs_sentinel_detects_token,
    _t_substitute_sentinel_in_script,
    _t_resolve_and_substitute_sentinel_noop_without_token,
    _t_resolve_and_substitute_sentinel_propagates_failure,
    _t_default_sentinel_db_path_repo_root,
    _t_run_verify_blocked_when_backend_unreachable,
    _t_launch_chromium_retries,
    _t_run_record_never_clicks_after_failed_precondition,
    _t_run_record_click_still_fires_without_a_prior_failure,
    _t_settle_for_capture_before_after_frames_differ_when_state_changes,
    _t_derive_happy,
    _t_derive_rejects_untagged_journey,
    _t_derive_rejects_no_expect,
    _t_derive_rejects_no_goto_open,
    _t_derive_rejects_invalid_demo,
    _t_derive_prefix_without_journey_key,
]


def _self_test(_argv: list[str] | None = None) -> int:
    passed = 0
    failed: list[tuple[str, str]] = []
    for check in _SELF_TEST_CHECKS:
        try:
            check()
            passed += 1
        except Exception as exc:  # noqa: BLE001 — report every failure
            failed.append((check.__name__, repr(exc)))
    for name, err in failed:
        print(f"  FAIL {name}: {err}", file=sys.stderr)
    print(f"[demo_runner self-test] {passed} passed, {len(failed)} failed")
    return 1 if failed else 0


# ── browser layer (Playwright; no model in the loop) ─────────────────────────

_PLAYWRIGHT_HELP = (
    "[demo_runner] Playwright (Python) is not available.\n"
    "  Install (one time, user scope):  python3 -m pip install --user playwright\n"
    "  Browsers cache at ~/.cache/ms-playwright; if missing run:\n"
    "      python3 -m playwright install chromium"
)


def _playwright_available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except Exception:
        return False


def _rel(path_abs: str, repo_root: str | None) -> str:
    if repo_root:
        try:
            return os.path.relpath(path_abs, repo_root)
        except ValueError:
            return path_abs
    return path_abs


def _locator_for(page, spec: tuple):
    kind, role, value = spec
    if kind == "role":
        return page.get_by_role(role, name=value)
    if kind == "text":
        return page.get_by_text(value)
    if kind == "label":
        return page.get_by_label(value)
    if kind == "placeholder":
        return page.get_by_placeholder(value)
    if kind == "testid":
        return page.get_by_test_id(value)
    return page.locator(value)  # css


def _find(page, target: dict, timeout_ms: int):
    """Resolve a target to a visible locator, trying degraded specs in order.
    Bounded: each spec gets a slice of the budget, so it can never spin."""
    specs = resolve_spec(target)
    if not specs:
        raise RuntimeError(f"unresolvable target {target!r}")
    per = max(800, timeout_ms // len(specs))
    last: Exception | None = None
    for spec in specs:
        loc = _locator_for(page, spec).first
        try:
            loc.wait_for(state="visible", timeout=per)
            return loc
        except Exception as exc:  # noqa: BLE001
            last = exc
    raise last or RuntimeError("not found")


def _check_expect(page, exp: dict, timeout_ms: int) -> bool:
    try:
        if "text" in exp:
            page.get_by_text(exp["text"]).first.wait_for(state="visible", timeout=timeout_ms)
            return True
        if "target" in exp:
            _find(page, exp["target"], timeout_ms)
            return True
    except Exception:
        return False
    return False


def _expect_desc(exp: dict) -> str:
    if "text" in exp:
        return f'"{exp["text"]}"'
    return str(exp.get("target", exp))


def _target_phrase(target: dict) -> str:
    if "role" in target and target.get("name"):
        return f'the "{target["name"]}" {target["role"]}'
    if "label" in target:
        return f'the "{target["label"]}" field'
    for k in ("text", "placeholder", "testid", "css"):
        if k in target:
            return f'"{target[k]}"'
    return "the element"


def _action_phrase(action: dict) -> str:
    """Human-readable one-liner for the demo-script.md `Action:` line."""
    t = action.get("type")
    if t == "goto":
        return f"Navigate to {action.get('url', '/')}"
    if t == "click":
        return f"Click {_target_phrase(action.get('target', {}))}"
    if t == "fill":
        return f'Type "{action.get("text", "")}" into {_target_phrase(action.get("target", {}))}'
    if t == "wait_for":
        return "Wait for the page to settle"
    if t == "expect":
        return f"Expect {_expect_desc(action)}"
    return str(t or "")


def _act_with_retry(page, action: dict, timeout_ms: int, kind: str) -> None:
    """click/fill with ONE retry on a TimeoutError, re-resolving the locator fresh.
    Both actions are idempotent in replay scripts (fill overwrites; clicks are
    navigational), and a single transient timeout on an otherwise-fine element
    spuriously FAILed the deterministic replay lane twice (ops-hardening iters
    12-13 — the LLM lane overturned it both times). Matched by exception NAME
    because playwright is imported lazily (lint mode runs without it installed)."""
    for attempt in (1, 2):
        try:
            loc = _find(page, action["target"], timeout_ms)
            if kind == "click":
                loc.click(timeout=timeout_ms)
            else:
                loc.fill(action.get("text", ""), timeout=timeout_ms)
            return
        except Exception as exc:  # noqa: BLE001
            if attempt == 2 or type(exc).__name__ != "TimeoutError":
                raise
            page.wait_for_timeout(500)  # brief settle, then the single retry


def _do_action(page, action: dict, base_url: str, timeout_ms: int) -> None:
    t = action.get("type")
    if t == "goto":
        page.goto(normalize_url(base_url, action.get("url", "/")),
                  wait_until="domcontentloaded", timeout=timeout_ms)
        try:
            page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 12000))
        except Exception:
            pass  # SPA may never go idle — best-effort
        return
    if t == "wait_for":
        if "ms" in action:
            page.wait_for_timeout(int(action["ms"]))
            return
        _find(page, action.get("target", {}), timeout_ms)
        return
    if t == "click":
        _act_with_retry(page, action, timeout_ms, "click")
        return
    if t == "fill":
        _act_with_retry(page, action, timeout_ms, "fill")
        return
    if t == "expect":
        if not _check_expect(page, action, timeout_ms):
            raise RuntimeError("expect not satisfied")
        return
    raise RuntimeError(f"unknown action type {t!r}")


def _highlight(page, loc) -> None:
    try:
        loc.scroll_into_view_if_needed(timeout=2000)
    except Exception:
        pass
    try:
        loc.evaluate(
            "el => { el.setAttribute('data-demo-prev', el.style.outline || '');"
            " el.style.outline = '3px solid #ff3b30'; el.style.outlineOffset = '2px'; }")
    except Exception:
        pass


def _unhighlight(page, loc) -> None:
    try:
        loc.evaluate("el => { el.style.outline = el.getAttribute('data-demo-prev') || ''; }")
    except Exception:
        pass


def _caption(page, text: str) -> None:
    try:
        page.evaluate(
            """(t) => { let b = document.getElementById('__demo_caption');
              if (!b) { b = document.createElement('div'); b.id='__demo_caption';
                b.style.cssText='position:fixed;left:0;right:0;top:0;z-index:2147483647;'
                  +'background:rgba(17,17,17,.92);color:#fff;font:16px/1.5 system-ui,sans-serif;'
                  +'padding:12px 18px;text-align:center;';
                document.body.appendChild(b); }
              b.textContent = t; }""", text)
    except Exception:
        pass


# Loading indicators that, while present, mean the page is mid-render — capturing
# now would screenshot an empty skeleton. Best-effort union; absent on most pages.
_LOADING_SELECTOR = (
    '[aria-busy="true"], [role="progressbar"], [data-loading="true"], '
    '.loading, .spinner, .skeleton, [class*="skeleton"], [class*="Skeleton"]'
)


def _settle_for_capture(page, budget_ms: int, exp: "dict | None" = None) -> None:
    """Best-effort wait for the page to finish loading — and, when `exp` is given, for the
    SPECIFIC post-action content the step names — before a screenshot, so the gallery never
    captures a spinner / empty skeleton, and (iter-77 fix) never captures the PREVIOUS state
    relabeled as the new one. NEVER raises — the demo is a showcase, not a gate.

    ops-hardening iter-77 (iter-76/d): the recorded gallery was producing byte-identical
    'before'/'after' frame pairs for state-changing steps (e.g. a background-compute window's
    active-vs-completed /data view). Root cause: this function only ran GENERIC settle
    heuristics (network idle / loading-indicator-hidden / fonts-ready / a flat paint pause)
    that are blind to WHICH content a given step actually cares about — all four can resolve
    instantly while the page is still showing the PRE-action state (a re-render that has not
    landed yet, a poll that has not ticked). It also silently RE-CAPPED whatever budget the
    caller passed down to a flat 12s, even when a step's own `timeout_ms` (honored everywhere
    else in this file, up to 20s — see `_default_timeout`/`_record_steps`) asked for more.

    The fix: when the caller passes the step's own `exp`(ect) — the same `{"text": ...}` /
    `{"target": ...}` shape `_check_expect` already uses to grade the step — that becomes the
    PRIMARY settle signal, actively (re-)polled for up to the caller's own budget (no longer
    silently truncated) before the generic heuristics run. `exp=None` (steps with no expect,
    e.g. `full_tour` framing shots) falls back to the prior generic-only behavior, budget cap
    included, unchanged.

    Four guards, each bounded by the budget: (0, new) the step's own expect condition becomes
    visible; (1) network goes idle so client-side fetches land; (2) any visible loading
    indicator disappears; (3) web fonts are ready, plus a short paint settle. An expect that
    never resolves within the budget is not an error here (the caller's own soft-note bookkeeping
    already covers that) — every guard, including the new one, falls through on timeout."""
    if exp:
        try:
            _check_expect(page, exp, max(1000, int(budget_ms)))
        except Exception:
            pass  # best-effort — the generic heuristics below still run regardless
    budget_ms = max(1000, min(int(budget_ms), 20000))
    try:
        page.wait_for_load_state("networkidle", timeout=budget_ms)
    except Exception:
        pass  # SPA may never go idle — best-effort
    try:
        loc = page.locator(_LOADING_SELECTOR)
        if loc.count() > 0:
            loc.first.wait_for(state="hidden", timeout=min(budget_ms, 8000))
    except Exception:
        pass  # no indicator, or it never resolved — best-effort
    try:
        page.evaluate("() => (document.fonts ? document.fonts.ready : null)")
    except Exception:
        pass
    try:
        page.wait_for_timeout(400)  # final paint settle
    except Exception:
        pass


def _default_timeout(script: dict, opts) -> int:
    raw = int(script.get("default_timeout_ms", opts.timeout_ms))
    return max(1000, min(raw, 20000))


def _write_skipped_results(opts, reason: str) -> None:
    if not opts.results:
        return
    md = render_results_md(opts.phase_id or "?", opts.base_url, opts.iteration,
                           [], [reason], "SKIPPED", opts.mode)
    Path(opts.results).parent.mkdir(parents=True, exist_ok=True)
    Path(opts.results).write_text(md, encoding="utf-8")


def run_lint(opts) -> int:
    """Validate golden replay scripts WITHOUT a browser (no playwright needed).

    Prints one line per requested journey: `<J-XX> ok` when the golden parses
    and validates, `<J-XX> invalid: <reason>` otherwise (a missing file counts
    as invalid). goal-iter-lean.sh uses this to quarantine broken goldens into
    the LLM lane BEFORE the replay partition — a broken golden used to surface
    only as a replay SKIP that nothing re-confirmed, silently leaving that
    journey unverified for the iteration. Always exits 0; callers decide per
    line."""
    scripts_dir = Path(opts.scripts_dir or ".")
    journeys = [j.strip() for j in (opts.journeys or "").split(",") if j.strip()]
    for jid in journeys:
        sp = scripts_dir / f"{jid}.json"
        if not sp.exists():
            print(f"{jid} invalid: no golden script on file")
            continue
        try:
            data = json.loads(sp.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"{jid} invalid: not valid JSON: {str(exc)[:100]}")
            continue
        errs = validate_script(data)
        if errs:
            print(f"{jid} invalid: " + "; ".join(errs)[:160])
        elif isinstance(data, dict) and data.get("not_yet"):
            print(f"{jid} invalid: marked not_yet")
        else:
            print(f"{jid} ok")
    return 0


def derive_golden_steps(demo: object, journey: str) -> "tuple[dict | None, str]":
    """SPEED-21: derive a candidate golden replay script for `journey` from an
    already-recorded demo script (same runner schema — verify ignores the
    demo-only fields). Copy + filter + renumber: the untagged PREFIX steps
    (shared setup before the first journey-tagged step) plus every step tagged
    with this journey; each kept step keeps only n/journey/action/expect/
    timeout_ms. Fail-closed — returns (None, reason) unless the demo
    validates, >=1 step is tagged for the journey, the derived sequence opens
    with a goto, and >=1 TAGGED step carries an expect (a golden with no
    assertions would pass vacuously). A returned script always passes
    validate_script."""
    errors = validate_script(demo)
    if errors:
        return None, "demo script invalid: " + "; ".join(errors)[:160]
    assert isinstance(demo, dict)  # validate_script guarantees this
    if demo.get("not_yet"):
        return None, "demo marked not_yet (no executable steps)"
    steps = demo.get("steps") or []
    # The demo-narrator contract has EVERY step carry a "journey" key, with ""
    # for shared orientation/setup steps — so "untagged" means a FALSY journey
    # value (missing, "", null), not a missing key.
    prefix: list = []
    for s in steps:
        if isinstance(s, dict) and not s.get("journey"):
            prefix.append(s)
        else:
            break
    tagged = [s for s in steps if isinstance(s, dict) and s.get("journey") == journey]
    if not tagged:
        return None, "no steps tagged for this journey"
    if not any(isinstance(s.get("expect"), dict) for s in tagged):
        return None, "no tagged step carries an expect (nothing to assert)"
    out_steps: list = []
    for i, s in enumerate(prefix + tagged, 1):
        ns: dict = {"n": i, "journey": journey, "action": s.get("action")}
        if isinstance(s.get("expect"), dict):
            ns["expect"] = s["expect"]
        if s.get("timeout_ms") is not None:
            ns["timeout_ms"] = s["timeout_ms"]
        out_steps.append(ns)
    first_action = out_steps[0].get("action") or {}
    if not isinstance(first_action, dict) or first_action.get("type") != "goto":
        return None, "derived sequence does not open with a goto"
    golden = {
        "schema_version": 1,
        "journey": journey,
        "name": str(demo.get("name") or journey),
        "default_timeout_ms": demo.get("default_timeout_ms", 8000),
        "steps": out_steps,
    }
    errors = validate_script(golden)
    if errors:
        return None, "derived script failed validation: " + "; ".join(errors)[:160]
    return golden, ""


def run_derive(opts) -> int:
    """SPEED-21 CLI: write candidate goldens (`<J-XX>.json.candidate` in
    --scripts-dir) derived from the --json demo for each --journeys id.
    Prints one parseable line per journey: `<J-XX> derived <path>` or
    `<J-XX> rejected: <reason>`. ALWAYS exits 0 — a rejected candidate is
    never a gate; the shell caller (replay_lane_autoderive_goldens) runs a
    REAL verify pass on every candidate before installing it."""
    journeys = [j.strip() for j in (opts.journeys or "").split(",") if j.strip()]
    if not opts.json or not opts.scripts_dir or not journeys:
        sys.stderr.write("[demo_runner] derive mode needs --json, --scripts-dir and --journeys; nothing derived.\n")
        return 0
    try:
        with open(opts.json, encoding="utf-8") as fh:
            demo = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        for jid in journeys:
            print(f"{jid} rejected: demo JSON unreadable: {str(exc)[:100]}")
        return 0
    outdir = Path(opts.scripts_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    for jid in journeys:
        golden, reason = derive_golden_steps(demo, jid)
        if golden is None:
            print(f"{jid} rejected: {reason}")
            continue
        cand = outdir / f"{jid}.json.candidate"
        cand.write_text(json.dumps(golden, indent=1) + "\n", encoding="utf-8")
        print(f"{jid} derived {cand}")
    return 0


def _launch_chromium(pw, headless: bool, attempts: int = 2, timeout_ms: int = 45000,
                     args: list | None = None):
    """Launch chromium with a bounded timeout and one fast retry.

    A cold chromium on a loaded machine intermittently exceeds Playwright's
    default 30s launch timeout (observed in a real session: one launch timeout
    turned a ~20-min browser-qa step into a ~40-min spike AND left the replay
    lane's journeys silently unverified). Bounded attempts turn that failure
    mode into ≤ ~90s before the caller's fallback engages."""
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return pw.chromium.launch(headless=headless, timeout=timeout_ms, args=args or [])
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            print(f"[demo_runner] chromium launch attempt {attempt}/{attempts} failed: "
                  f"{str(exc).splitlines()[0][:140]}", file=sys.stderr)
    assert last_exc is not None
    raise last_exc


def _record_steps(page, steps: list[dict], base_url: str, default_tmo: int,
                  out_dir: Path, repo_root: "str | None") -> "tuple[list[dict], list[str], list[dict]]":
    """Execute `steps` against an already-open `page`, one `_do_action` call per step,
    capturing a screenshot + soft note per the showcase's fail-open contract (never raises).

    Extracted out of `run_record` so the mutation guard below can be self-tested against a
    fake `page` without a real browser (the self-test harness promises "no browser, no
    network" — the real `run_record` still opens a real Playwright page and hands it here).

    Mutation guard (ops-hardening iter-63 lesson): once ANY step's `_do_action` raises, no
    LATER step in this same script whose action is a `click` on a `role: button` target is
    PERFORMED — the demo/showcase lane is not read-only, and a failed precondition step (e.g.
    a date field that couldn't be filled) must never be followed by a mutating click (e.g.
    "Start", which would launch a real, un-narrated backfill). The skipped step still gets its
    screenshot and a distinct soft note naming the skip reason — only the click itself is
    withheld."""
    captured: list[dict] = []
    soft_notes: list[str] = []
    script_steps: list[dict] = []
    precondition_failed = False
    for step in steps:
        n = int(step.get("n", 0))
        section = step.get("section", "highlights")
        tmo = max(1000, min(int(step.get("timeout_ms", default_tmo)), 20000))
        action = step["action"]
        is_mutating_click = (action.get("type") == "click"
                             and (action.get("target") or {}).get("role") == "button")
        if precondition_failed and is_mutating_click:
            acted = False
            soft_notes.append(
                f"Step {n:02d} — skipped {_action_phrase(action)}: a preceding step's "
                "precondition already failed in this script, so this mutating control was "
                "never invoked; captured the page anyway.")
        else:
            try:
                _do_action(page, action, base_url, tmo)
                acted = True
            except Exception as exc:  # noqa: BLE001 — showcase never raises out
                acted = False
                precondition_failed = True
                soft_notes.append(
                    f"Step {n:02d} — couldn't perform "
                    f"{action.get('type')} ({str(exc).splitlines()[0][:120]}); "
                    "captured the page anyway.")
        exp = step.get("expect")
        # The expect is the strongest "content has loaded" signal — wait for it
        # with the FULL step budget (not a 3s cap) so a slow-but-real render is not
        # captured mid-skeleton. Still only a soft note if it never appears.
        if acted and exp and not _check_expect(page, exp, tmo):
            soft_notes.append(
                f"Step {n:02d} — expected {_expect_desc(exp)} did not appear; recorded anyway.")
        shot_rel = ""
        if section != "full_tour":
            # Settle (network idle + loading indicators gone + paint) so the
            # gallery never captures a spinner / empty skeleton. iter-77: pass this
            # step's own `exp` so a state-changing step's capture actively waits for
            # ITS content, never a stale pre-action frame (iter-76/d fix).
            _settle_for_capture(page, tmo, exp)
            shot_abs = out_dir / f"step-{n:02d}.png"
            try:
                page.screenshot(path=str(shot_abs))
            except Exception:
                pass
            shot_rel = _rel(str(shot_abs), repo_root)
            captured.append({
                "n": n, "title": step.get("title", ""),
                "journey": step.get("journey", ""), "new": step.get("new", False),
                "screenshot": shot_rel,
            })
        script_steps.append({
            "n": n, "title": step.get("title", ""), "new": step.get("new", False),
            "narration": step.get("narration", ""), "point_out": step.get("point_out", ""),
            "action": _action_phrase(action), "section": section,
            "screenshot": shot_rel,
        })
    return captured, soft_notes, script_steps


def run_record(script: dict, opts, base_url: str) -> int:
    phase_id = opts.phase_id or script.get("phase_id") or "?"
    iteration = opts.iteration if opts.iteration is not None else script.get("iteration")
    out_dir = Path(opts.out_dir or ".").resolve()

    if script.get("not_yet"):
        if opts.results:
            md = render_results_md(phase_id, base_url, iteration, [], [], "NOT_YET", "record")
            Path(opts.results).parent.mkdir(parents=True, exist_ok=True)
            Path(opts.results).write_text(md, encoding="utf-8")
        print("[demo_runner] nothing to demo yet (NOT_YET).")
        return 0

    from playwright.sync_api import sync_playwright

    steps = script["steps"]
    default_tmo = _default_timeout(script, opts)
    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = _launch_chromium(pw, headless=True)
        ctx_kwargs: dict = {"viewport": {"width": 1280, "height": 800}}
        if opts.video:
            ctx_kwargs["record_video_dir"] = str(out_dir / "video")
            ctx_kwargs["record_video_size"] = {"width": 1280, "height": 720}
        context = browser.new_context(**ctx_kwargs)
        page = context.new_page()
        captured, soft_notes, script_steps = _record_steps(
            page, steps, base_url, default_tmo, out_dir, opts.repo_root)
        context.close()
        browser.close()

    verdict = compute_verdict(bool(captured), bool(soft_notes), not_yet=False)
    if opts.results:
        Path(opts.results).parent.mkdir(parents=True, exist_ok=True)
        Path(opts.results).write_text(
            render_results_md(phase_id, base_url, iteration, captured, soft_notes, verdict, "record"),
            encoding="utf-8")
    # demo-script.md is regenerated from the JSON (single source of truth) so its
    # captions never drift from what was actually recorded.
    if opts.script_fallback:
        Path(opts.script_fallback).parent.mkdir(parents=True, exist_ok=True)
        Path(opts.script_fallback).write_text(
            render_script_md(phase_id, base_url, iteration, script_steps, "record"), encoding="utf-8")
    print(f"[demo_runner] recorded {len(captured)} step(s) → {out_dir} (verdict: {verdict})")
    return 0


def run_live(script: dict, opts, base_url: str) -> int:
    phase_id = opts.phase_id or script.get("phase_id") or "?"
    if script.get("not_yet"):
        print("\n  Nothing to show yet — no working features to walk through.\n")
        return 0

    from playwright.sync_api import sync_playwright

    steps = script["steps"]
    total = len(steps)
    default_tmo = _default_timeout(script, opts)
    print(f"\n  Live walkthrough of {phase_id} — {total} step(s). "
          "A Chrome window will open; press Enter in THIS terminal to advance.\n")

    with sync_playwright() as pw:
        browser = _launch_chromium(pw, headless=False, args=["--start-maximized"])
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        for i, step in enumerate(steps, 1):
            title = step.get("title", "")
            tag = "  [NEW]" if step.get("new") else ""
            print(f"\n── Step {i:02d}/{total:02d} ─ {title}{tag}")
            if step.get("narration"):
                print(f"   {step['narration']}")
            tmo = max(1000, min(int(step.get("timeout_ms", default_tmo)), 20000))
            action = step["action"]
            loc = None
            target = action.get("target")
            if target:
                try:
                    loc = _find(page, target, min(tmo, 4000))
                    _highlight(page, loc)
                except Exception:
                    loc = None
            if opts.caption and step.get("narration"):
                _caption(page, step["narration"])
            try:
                input("   ▶ Press Enter (in this terminal) to perform this step… ")
            except EOFError:
                pass
            try:
                _do_action(page, action, base_url, tmo)
                # let content load before the human looks; iter-77: pass this step's own
                # `exp` too, same iter-76/d fix as the record path.
                _settle_for_capture(page, tmo, step.get("expect"))
                if step.get("point_out"):
                    print(f"   ↳ Notice: {step['point_out']}")
            except Exception as exc:  # noqa: BLE001
                print(f"   ⚠ Couldn't find that element — skipping this step. "
                      f"({str(exc).splitlines()[0][:120]})")
            finally:
                if loc is not None:
                    _unhighlight(page, loc)
        print("\n   That's the full tour.")
        try:
            input("   Press Enter to finish and close the browser… ")
        except EOFError:
            pass
        context.close()
        browser.close()
    return 0


def run_verify(opts, base_url: str) -> int:
    """Deterministic regression replay (no model in the loop).

    Replays each listed journey's stored golden script (`<scripts-dir>/<J-XX>.json`)
    in a FRESH browser context — so each journey's own sign-in/setup runs from a
    clean state and journeys never bleed into each other — treats every step's
    `expect` as a HARD assertion, captures one end-state screenshot per journey for
    evidence, and writes a ui-test-results.md the goal-evaluator consumes unchanged.

    Returns 0 when nothing failed, 5 when ≥1 journey FAILED (so the caller can
    re-confirm just those journeys with the LLM agent — guards against a brittle
    selector causing a false regression). A journey with no/invalid golden script
    is SKIP (the caller routes those to the LLM lane). Returns 7 when the backend
    was unreachable BEFORE any journey ran — every journey is written BLOCKED,
    never FAIL (ops-hardening iter-39: closes a real bug where a downed backend
    produced false FAIL rows against every journey, twice in this session,
    iter-38/t — see `probe_backend_health`/`resolve_backend_health_url`)."""
    from playwright.sync_api import sync_playwright

    scripts_dir = Path(opts.scripts_dir or ".")
    journeys = [j.strip() for j in (opts.journeys or "").split(",") if j.strip()]
    phase_id = opts.phase_id or "?"
    iteration = opts.iteration
    evidence_dir = Path(opts.evidence_dir) if opts.evidence_dir else None
    if evidence_dir:
        evidence_dir.mkdir(parents=True, exist_ok=True)

    def _write(results: list[dict]) -> None:
        if opts.results:
            Path(opts.results).parent.mkdir(parents=True, exist_ok=True)
            Path(opts.results).write_text(
                render_regression_results_md(phase_id, base_url, iteration, results, "verify"),
                encoding="utf-8")

    if not journeys:
        _write([])
        print("[demo_runner] verify: no journeys to replay (SKIPPED).")
        return 0

    # ops-hardening iter-39: probe the backend's OWN health endpoint ONCE, before opening a
    # browser or replaying a single journey. A journey verdict of FAIL means "this journey's own
    # assertions did not hold" — untrue, and misleading, when the backend never answered at all.
    # Every journey is written BLOCKED instead (a distinct verdict class the caller never confuses
    # with a real regression signal — see compute_regression_verdict / the rc=7 contract above).
    health_url = resolve_backend_health_url(base_url, getattr(opts, "backend_health_url", None))
    if not probe_backend_health(health_url):
        results = [{
            "journey": jid, "name": jid, "verdict": "BLOCKED",
            "expected": f"backend answers GET {health_url} with HTTP 200 before replay",
            "actual": f"backend unreachable: GET {health_url} did not answer 200",
            "evidence": "none",
        } for jid in journeys]
        _write(results)
        print(f"[demo_runner] verify: backend unreachable ({health_url}) — "
              f"{len(results)} journey(s) BLOCKED, not FAILed (rc 7).", file=sys.stderr)
        return 7

    results: list[dict] = []
    try:
        with sync_playwright() as pw:
            browser = _launch_chromium(pw, headless=True)
            for jid in journeys:
                sp = scripts_dir / f"{jid}.json"
                if not sp.exists():
                    results.append({"journey": jid, "name": jid, "verdict": "SKIP",
                                    "expected": "replay golden script",
                                    "actual": "no golden script on file", "evidence": "none"})
                    continue
                try:
                    data = json.loads(sp.read_text(encoding="utf-8"))
                except Exception as exc:  # noqa: BLE001
                    results.append({"journey": jid, "name": jid, "verdict": "SKIP",
                                    "expected": "replay golden script",
                                    "actual": f"golden script not valid JSON: {str(exc)[:120]}",
                                    "evidence": "none"})
                    continue
                errs = validate_script(data)
                if errs or data.get("not_yet"):
                    results.append({"journey": jid, "name": jid, "verdict": "SKIP",
                                    "expected": "replay golden script",
                                    "actual": "invalid golden script: " + "; ".join(errs) if errs
                                    else "golden script marked not_yet", "evidence": "none"})
                    continue
                if script_needs_sentinel(data):
                    try:
                        data, _resolved = resolve_and_substitute_sentinel(
                            data, default_sentinel_db_path(opts.repo_root))
                    except RuntimeError as exc:
                        results.append({"journey": jid, "name": jid, "verdict": "FAIL",
                                        "expected": "sentinel token resolves to a single "
                                                     "eligible unsnapshotted trading day",
                                        "actual": str(exc), "evidence": "none"})
                        continue
                name = data.get("name") or data.get("title") or jid
                steps = data.get("steps") or []
                default_tmo = _default_timeout(data, opts)
                context = browser.new_context(viewport={"width": 1280, "height": 800})
                page = context.new_page()
                verdict, actual = "PASS", "journey replayed end-to-end; all expects held"
                exp = None  # last step's expect, if any -- passed to the final evidence capture below
                for step in steps:
                    n = int(step.get("n", 0))
                    tmo = max(1000, min(int(step.get("timeout_ms", default_tmo)), 20000))
                    try:
                        _do_action(page, step["action"], base_url, tmo)
                    except Exception as exc:  # noqa: BLE001
                        verdict = "FAIL"
                        actual = (f"step {n:02d} could not perform "
                                  f"{step['action'].get('type')}: {str(exc).splitlines()[0][:140]}")
                        break
                    exp = step.get("expect")
                    if exp and not _check_expect(page, exp, tmo):
                        verdict = "FAIL"
                        actual = f"step {n:02d} expected {_expect_desc(exp)} did not appear"
                        break
                shot_rel = "none"
                if evidence_dir:
                    # iter-77: pass the last-executed step's own `exp` too (same iter-76/d fix as the
                    # record/live paths) so the evidence screenshot reflects the journey's real end
                    # state rather than a frame settled purely on generic network/paint heuristics.
                    _settle_for_capture(page, default_tmo, exp)
                    shot_abs = evidence_dir / f"{jid}-verify.png"
                    try:
                        page.screenshot(path=str(shot_abs))
                        shot_rel = _rel(str(shot_abs), opts.repo_root)
                        # iter-45 audit F1: stamp the capture with its OWN journey so two
                        # journeys ending on the same page in the same state can never be
                        # byte-identical (J-03/J-04 both end on /data and both hashed
                        # 9d77429b…). Ancillary `tEXt` only — no pixel is altered. Its own
                        # try: a stamping failure must never fail an otherwise-passing replay.
                        try:
                            shot_abs.write_bytes(png_with_provenance(shot_abs.read_bytes(), [
                                ("Journey", jid),
                                ("Phase", str(opts.phase_id or "")),
                                ("Created", datetime.datetime.now().isoformat(timespec="seconds")),
                                ("Source", "demo_runner.py --mode verify"),
                            ]))
                        except Exception:  # noqa: BLE001
                            pass
                    except Exception:  # noqa: BLE001
                        pass
                results.append({"journey": jid, "name": name, "verdict": verdict,
                                "expected": "journey replays end-to-end; all expects hold",
                                "actual": actual, "evidence": shot_rel})
                context.close()
            browser.close()
    except Exception as exc:  # noqa: BLE001
        # Browser INFRASTRUCTURE failure (launch timeout, mid-run crash) — not a
        # journey verdict. Record what did not get replayed and return 6 so the
        # caller (goal-iter-lean.sh) routes every replay journey back to the LLM
        # lane. Previously this crashed with rc=1 and the replay journeys were
        # silently left unverified for the iteration.
        done = {r["journey"] for r in results}
        for jid in journeys:
            if jid not in done:
                results.append({"journey": jid, "name": jid, "verdict": "SKIP",
                                "expected": "replay golden script",
                                "actual": "browser infrastructure failure: "
                                          + str(exc).splitlines()[0][:140],
                                "evidence": "none"})
        _write(results)
        print("[demo_runner] verify: browser infrastructure failure — routing replay "
              f"journeys to the LLM lane (rc 6): {str(exc).splitlines()[0][:140]}",
              file=sys.stderr)
        return 6

    _write(results)
    overall = compute_regression_verdict(results)
    n_fail = sum(1 for r in results if r["verdict"] == "FAIL")
    print(f"[demo_runner] verify: {len(results)} journey(s), {n_fail} failed (verdict: {overall})")
    return 5 if n_fail else 0


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("self-test", "--self-test"):
        return _self_test(argv[1:])

    import argparse
    p = argparse.ArgumentParser(prog="demo_runner.py", description="Deterministic browser demo executor.")
    p.add_argument("--json", default=None, help="path to the executable demo-script JSON (record/live)")
    p.add_argument("--mode", default="record", choices=["live", "record", "session-live", "verify", "lint", "derive"])
    p.add_argument("--base-url", default="http://localhost:3000")
    p.add_argument("--out-dir", default=None, help="screenshot dir, e.g. reports/demo/<id>")
    p.add_argument("--results", default=None, help="demo-results.md output path")
    p.add_argument("--script-fallback", default=None, help="demo-script.md path (written only if absent)")
    p.add_argument("--phase-id", default=None)
    p.add_argument("--iteration", default=None)
    p.add_argument("--video", action="store_true")
    p.add_argument("--caption", action="store_true")
    p.add_argument("--repo-root", default=None)
    p.add_argument("--timeout-ms", type=int, default=8000)
    p.add_argument("--scripts-dir", default=None,
                   help="verify mode: dir of per-journey golden scripts (<J-XX>.json)")
    p.add_argument("--journeys", default=None,
                   help="verify mode: comma-separated journey IDs to replay")
    p.add_argument("--evidence-dir", default=None,
                   help="verify mode: per-journey screenshot evidence dir")
    p.add_argument("--backend-health-url", default=None,
                   help="verify mode: explicit backend readiness URL to probe before replaying "
                        "(default: guessed from CHAIN_BACKEND_PORT + this project's /api/health)")
    opts = p.parse_args(argv)
    live = opts.mode in ("live", "session-live")
    verify = opts.mode == "verify"

    if opts.mode == "lint":
        return run_lint(opts)   # pure validation — needs no browser/playwright

    if opts.mode == "derive":
        return run_derive(opts)  # pure transform (SPEED-21) — no browser/playwright

    if not _playwright_available():
        sys.stderr.write(_PLAYWRIGHT_HELP + "\n")
        if not live and not verify:
            _write_skipped_results(opts, "Playwright (Python) not installed; demo skipped.")
        return 3

    if live and not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        if os.environ.get("CHAIN_DEMO_LIVE_FALLBACK_RECORD", "").lower() in ("1", "true", "yes"):
            opts.mode, live = "record", False
            sys.stderr.write("[demo_runner] No display — falling back to record mode.\n")
        else:
            sys.stderr.write(
                "[demo_runner] Live mode needs a display (X11/Wayland). Set DISPLAY, run record "
                "mode (./scripts/automation/demo.sh <id>), or set CHAIN_DEMO_LIVE_FALLBACK_RECORD=true.\n")
            return 4

    if verify:
        return run_verify(opts, opts.base_url or "http://localhost:3000")

    if not opts.json:
        sys.stderr.write("[demo_runner] --json is required for record/live modes.\n")
        return 2

    try:
        with open(opts.json, encoding="utf-8") as fh:
            script = json.load(fh)
    except FileNotFoundError:
        sys.stderr.write(f"[demo_runner] demo JSON not found: {opts.json}\n")
        if not live:
            _write_skipped_results(opts, f"demo JSON not found: {opts.json}")
        return 2
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"[demo_runner] demo JSON is not valid JSON: {exc}\n")
        if not live:
            _write_skipped_results(opts, f"demo JSON parse error: {exc}")
        return 2

    errors = validate_script(script)
    if errors:
        sys.stderr.write("[demo_runner] invalid demo script: " + "; ".join(errors) + "\n")
        if not live:
            _write_skipped_results(opts, "invalid demo script: " + "; ".join(errors))
        return 2

    if script_needs_sentinel(script):
        try:
            script, _resolved = resolve_and_substitute_sentinel(
                script, default_sentinel_db_path(opts.repo_root))
        except RuntimeError as exc:
            sys.stderr.write(f"[demo_runner] {exc}\n")
            if not live:
                _write_skipped_results(opts, str(exc))
            return 2

    base_url = opts.base_url or script.get("base_url") or "http://localhost:3000"
    if opts.phase_id is None:
        opts.phase_id = script.get("phase_id")
    if opts.iteration is None:
        opts.iteration = script.get("iteration")

    return run_live(script, opts, base_url) if live else run_record(script, opts, base_url)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
