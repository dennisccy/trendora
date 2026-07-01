#!/usr/bin/env python3
"""Post-decompose gate checker (Trendora policy).

Invoked by project-extensions/gates/post-decompose.sh from apps/backend with the
backend venv. Reads the iteration spec ($SPEC_PATH), extracts any "## Evidence
Claim" JSON block(s), and runs each through the referee's verify_edge against the
target ledger.

Per-claim ledger routing (iter-9): each Evidence Claim MAY carry an optional
"ledger" key selecting which economy certifies it —

    "staging"   (the DEFAULT when the key is absent) -> the internal online-FDR
                exploration ledger ($STAGING_LEDGER_PATH). Exploration accumulates
                here WITHOUT tightening the user-facing canonical Bonferroni bar.
    "canonical" (explicit, for a deliberately promoted winner) -> the user-facing
                certified-claims ledger ($LEDGER_PATH), ALWAYS strict Bonferroni.

    exit 0  => no claim, OR every claim CERTIFIED (PASS)        -> iteration may build
    exit 3  => a claim was NOT certified (FAIL / INSUFFICIENT), OR a routing failure
               (unrecognized "ledger" value / the required *_LEDGER_PATH unset)
               -> block the iteration (FAIL-CLOSED — never a silent certification)

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

# The per-claim "ledger" routing vocabulary -> the env var carrying that ledger's path. A claim omitting
# the key defaults to STAGING (exploration); a promoted winner sets "canonical" explicitly. An unrecognized
# value is FAIL-CLOSED (never silently certified). The env indirection matches how run-goal.sh exports the
# two paths (LEDGER_PATH + STAGING_LEDGER_PATH) — no path literal lives here.
_LEDGER_ENV = {"staging": "STAGING_LEDGER_PATH", "canonical": "LEDGER_PATH"}
_DEFAULT_LEDGER = "staging"


def extract_claims(spec_text: str) -> list:
    claims = []
    for section in _CLAIM_SECTION.findall(spec_text):
        for block in _JSON_FENCE.findall(section):
            try:
                claims.append(json.loads(block))
            except json.JSONDecodeError:
                pass
    return claims


def resolve_claim_ledger(claim: dict) -> tuple:
    """Route ONE claim to its target ledger, FAIL-CLOSED. Returns ``(kind, env_name, path, error)``:

      * `kind`     — the claim's "ledger" value (default ``"staging"``);
      * `env_name` — the env var that must carry the path (``None`` for an unrecognized kind);
      * `path`     — the resolved ledger path (``None`` on any failure);
      * `error`    — a human-readable blocking reason, or ``None`` when routing succeeded.

    An UNRECOGNIZED kind and an UNSET required path are BOTH fail-closed (a blocking `error`), never a
    silent certification — the same discipline as the original LEDGER_PATH-unset guard, now per-claim."""
    kind = claim.get("ledger", _DEFAULT_LEDGER)
    if kind not in _LEDGER_ENV:
        return kind, None, None, (
            f"unrecognized ledger {kind!r} (valid: {sorted(_LEDGER_ENV)}) — fail-closed"
        )
    env_name = _LEDGER_ENV[kind]
    path = os.environ.get(env_name, "")
    if not path:
        return kind, env_name, None, f"{env_name} unset — cannot certify a {kind} claim (fail-closed)"
    return kind, env_name, path, None


def _verdict_fields(v) -> tuple:
    """Pull (status, reason) out of verify_edge's return, tolerant of nesting."""
    if isinstance(v, dict):
        status = v.get("status") or (v.get("verdict") or {}).get("status")
        reason = v.get("reason") or (v.get("verdict") or {}).get("reason")
        return (status or "INSUFFICIENT"), (reason or "")
    return "INSUFFICIENT", str(v)


def main() -> int:
    spec_path = os.environ.get("SPEC_PATH", "")
    verdict_path = os.environ.get("GATE_VERDICT_PATH", "")

    if not spec_path or not os.path.exists(spec_path):
        print(f"[gate] no spec at SPEC_PATH={spec_path!r} — passing through")
        return 0
    claims = extract_claims(open(spec_path, encoding="utf-8").read())
    if not claims:
        print("[gate] no '## Evidence Claim' block — not a data-derived iteration, passing through")
        return 0

    register = date.today().isoformat()
    results, blocked = [], False
    with Session(get_engine()) as session:
        for claim in claims:
            kind, _env_name, ledger_path, route_error = resolve_claim_ledger(claim)
            if route_error is not None:
                # Routing failure (unrecognized ledger / unset path) -> BLOCK, never a silent write.
                results.append({"claim": claim, "ledger": kind, "status": "BLOCKED", "reason": route_error})
                print(f"[gate] BLOCKED: {claim}  ({route_error})", file=sys.stderr)
                blocked = True
                continue
            try:
                status, reason = _verdict_fields(
                    tools.verify_edge(session, claim, ledger_path, register_date=register, ledger=kind)
                )
            except Exception as exc:  # a malformed claim selector, etc. — never ship it
                status, reason = "INSUFFICIENT", f"verify_edge error: {exc}"
            results.append({"claim": claim, "ledger": kind, "status": status, "reason": reason})
            print(f"[gate] {status} [{kind}]: {claim}  ({reason})")
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
