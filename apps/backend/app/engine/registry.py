"""The pre-registration registry — the read-side loader + exact-match checker (goal-mcp-loop iter-30,
J-18 / backlog B-901).

This module is the SINGLE source both `GET /api/research/registry` (via `app.api.registry`) and the
post-decompose gate (`project-extensions/gates/verify_claim.py`, a non-HTTP consumer) read through — so
the registry page a human browses and the machine check that refuses an unregistered Evidence Claim can
never disagree. It is a PURE, engine-free module (mirrors `app.engine.evidence`'s shape): filesystem I/O
+ dict comparison only, no DB session, no computation.

  - `load_registrations()` — every registered hypothesis, in append (registration) order. A missing/empty
    file is an empty list, never a crash (anti-goal: resilience to data-shape change).
  - `claim_selectors(claim)` — the EXACT selector-set one claim carries (`kind` + whichever
    `_CLAIM_SELECTOR_KEYS` are present + `horizon` + `direction`), the SAME shape every registry row's
    `selectors` field is stored as.
  - `match_registration(claim)` — the registry row whose `selectors` EXACTLY equal the claim's
    selector-set, or `None`. EXACT dict equality only — no fuzzy/superset matching (B-901's dominant
    named trap: fuzziness reopens the ad-hoc-mining door a pre-registration requirement is meant to close).

This module NEVER decides proven-ness (that is `app.engine.evidence`'s job alone, sourced from the
certified-claims ledger) and introduces NO proven-language: a registration's `status` ("registered" /
"tested" / "closed") is a descriptive PROCESS state, never a "Proven"/"Not yet proven" signal.

The registry PATH is config/env-driven (anti-goal: No magic numbers — no path literal here): the runtime
override `TRENDORA_REGISTRY_PATH`, else `config.evidence.registry.path` resolved against the repo root —
mirroring `app.engine.evidence.resolve_ledger_path()` exactly.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from app.config import REPO_ROOT, get_config

# The environment-variable NAME (the NAME only — never a path VALUE literal in code) the runtime registry
# path may be overridden with. Mirrors `app.engine.evidence.LEDGER_PATH_ENV`.
REGISTRY_PATH_ENV = "TRENDORA_REGISTRY_PATH"


def resolve_registry_path() -> str:
    """The pre-registrations file path: the `TRENDORA_REGISTRY_PATH` env override if set, else
    `config.evidence.registry.path` resolved against `REPO_ROOT` when relative.

    This MUST resolve to the SAME file the post-decompose gate reads (set by `run-goal.sh` alongside
    `LEDGER_PATH`/`STAGING_LEDGER_PATH`), so the registry page and the gate's cross-check are always
    reading identical state. No path literal lives here — the default lives in config (anti-goal: No
    magic numbers). Mirrors `app.engine.evidence.resolve_ledger_path()` exactly."""
    override = os.environ.get(REGISTRY_PATH_ENV)
    if override:
        return override
    configured = Path(get_config().evidence.registry.path)
    if not configured.is_absolute():
        configured = REPO_ROOT / configured
    return str(configured)


def load_registrations(path: str | None = None) -> list[dict]:
    """Every registered hypothesis, in append order. A missing file (or a file that does not exist yet)
    is an empty registry (`[]`), never a crash — the honest default before any backfill/registration has
    landed. Blank lines are skipped so a trailing newline never yields a phantom row.

    `path` defaults to `resolve_registry_path()` (the endpoint's call shape); a caller (tests, or the
    gate via `match_registration`) may pass an explicit path to read an isolated fixture file instead."""
    target = path if path is not None else resolve_registry_path()
    if not os.path.exists(target):
        return []
    rows: list[dict] = []
    with open(target, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# The claim selectors this module matches on — mirrors `app.mcp.tools._CLAIM_SELECTOR_KEYS` BYTE-FOR-BYTE.
# Kept as a local literal (not imported) so this module stays engine-free / pure, exactly like
# `app.engine.ledger._PASS_STATUS` mirrors `app.engine.referee.STATUS_PASS` "so this module stays
# engine-free." `app.mcp.tools` is the source of truth for this tuple; update both together.
_CLAIM_SELECTOR_KEYS = (
    "factor", "slice_kind", "decile", "regime", "sector", "condition", "cohort", "single_index",
    "subject", "view", "setup", "pattern", "phase", "dimension", "family", "velocity_sign",
    "regime_decile", "severity_decile", "factor_decile", "asof",
)


def claim_selectors(claim: dict) -> dict:
    """The EXACT selector-set one claim carries: `kind` + whichever `_CLAIM_SELECTOR_KEYS` the claim
    dict has present + `horizon` + `direction` (defaulting the direction to `"positive"`, mirroring
    `app.mcp.tools.verify_edge`'s own default when a claim omits it — every real Evidence Claim / ledger
    row carries `horizon` explicitly, so no default is applied there). Display-routing keys a claim may
    also carry (`signal`, `ledger`) are DELIBERATELY excluded — they route where a certified claim's
    badge/ledger lands, they are not part of the hypothesis identity a registration matches on."""
    selectors: dict = {"kind": claim.get("kind")}
    for key in _CLAIM_SELECTOR_KEYS:
        if key in claim:
            selectors[key] = claim[key]
    if "horizon" in claim:
        selectors["horizon"] = claim["horizon"]
    selectors["direction"] = claim.get("direction", "positive")
    return selectors


def match_registration(claim: dict, registrations: list[dict] | None = None) -> dict | None:
    """The registry row whose `selectors` EXACTLY equal `claim`'s selector-set (`claim_selectors`), or
    `None` when nothing matches — an unregistered hypothesis, OR a near-miss whose selectors differ by
    even one value (e.g. a decile or horizon off by one). EXACT dict equality only, deliberately: fuzzy
    or superset matching is B-901's named dominant trap (it would reopen the ad-hoc-mining door
    pre-registration exists to close).

    `registrations` defaults to `load_registrations()` (the committed/configured file) when omitted —
    the gate's real call shape (`match_registration(claim)`); a caller (unit tests) may pass an explicit
    fixture list instead so a loader test needs no on-disk file."""
    wanted = claim_selectors(claim)
    rows = load_registrations() if registrations is None else registrations
    for row in rows:
        if isinstance(row, dict) and row.get("selectors") == wanted:
            return row
    return None
