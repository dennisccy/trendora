#!/usr/bin/env python3
"""Post-decompose gate checker (Trendora policy).

Invoked by project-extensions/gates/post-decompose.sh from apps/backend with the
backend venv. Reads the iteration spec ($SPEC_PATH), extracts any "## Evidence
Claim" JSON block(s), and runs each through the referee's verify_edge against the
certified-claims ledger ($LEDGER_PATH).

    exit 0  => no claim, OR every claim CERTIFIED (PASS)        -> iteration may build
    exit 3  => a claim was NOT certified (FAIL / INSUFFICIENT)  -> block the iteration

A summary is written to $GATE_VERDICT_PATH when set. The referee counts independent
holdout DATES, so on a thin/coarse dataset it honestly returns INSUFFICIENT (which
blocks) rather than certifying an unprovable edge.
"""
import json
import os
import re
import sys
from datetime import date

# Run as a script, so the script's own dir (not the backend) is on sys.path by
# default — add the backend package dir so `app...` imports resolve regardless of cwd.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend")))

from sqlmodel import Session  # noqa: E402

from app.db import get_engine  # noqa: E402
from app.mcp import tools  # noqa: E402

# A "## Evidence Claim" section runs until the next "## " heading (or EOF).
_CLAIM_SECTION = re.compile(r"^##\s+Evidence Claim\b.*?(?=^\#\#\s|\Z)", re.MULTILINE | re.DOTALL)
# Each fenced ```json { ... } ``` block inside it is one claim.
_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def extract_claims(spec_text: str) -> list:
    claims = []
    for section in _CLAIM_SECTION.findall(spec_text):
        for block in _JSON_FENCE.findall(section):
            try:
                claims.append(json.loads(block))
            except json.JSONDecodeError:
                pass
    return claims


def _verdict_fields(v) -> tuple:
    """Pull (status, reason) out of verify_edge's return, tolerant of nesting."""
    if isinstance(v, dict):
        status = v.get("status") or (v.get("verdict") or {}).get("status")
        reason = v.get("reason") or (v.get("verdict") or {}).get("reason")
        return (status or "INSUFFICIENT"), (reason or "")
    return "INSUFFICIENT", str(v)


def main() -> int:
    spec_path = os.environ.get("SPEC_PATH", "")
    ledger_path = os.environ.get("LEDGER_PATH", "")
    verdict_path = os.environ.get("GATE_VERDICT_PATH", "")

    if not spec_path or not os.path.exists(spec_path):
        print(f"[gate] no spec at SPEC_PATH={spec_path!r} — passing through")
        return 0
    claims = extract_claims(open(spec_path, encoding="utf-8").read())
    if not claims:
        print("[gate] no '## Evidence Claim' block — not a data-derived iteration, passing through")
        return 0
    if not ledger_path:
        print("[gate] LEDGER_PATH unset — cannot certify a claim; BLOCKING (fail-closed)", file=sys.stderr)
        return 3

    register = date.today().isoformat()
    results, blocked = [], False
    with Session(get_engine()) as session:
        for claim in claims:
            try:
                status, reason = _verdict_fields(
                    tools.verify_edge(session, claim, ledger_path, register_date=register)
                )
            except Exception as exc:  # a malformed claim selector, etc. — never ship it
                status, reason = "INSUFFICIENT", f"verify_edge error: {exc}"
            results.append({"claim": claim, "status": status, "reason": reason})
            print(f"[gate] {status}: {claim}  ({reason})")
            if status != "PASS":
                blocked = True

    if verdict_path:
        try:
            with open(verdict_path, "w", encoding="utf-8") as fh:
                json.dump({"blocked": blocked, "results": results}, fh, indent=2)
        except OSError:
            pass
    return 3 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
