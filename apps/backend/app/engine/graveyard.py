"""The negative-results graveyard — the read-side composition of every NON-PASS referee verdict across
BOTH the canonical and staging certified-claims ledgers (goal-mcp-loop iter-31, J-19 / backlog B-902).

This module is the institutional-memory companion to `app.engine.evidence` ("what is proven") and
`app.engine.registry` ("what is registered"): it answers "what does NOT work", so a future model — or the
owner in month 9 — never re-derives a dead hypothesis from scratch. It is a PURE, engine-free read-compose
module (mirrors `app.engine.registry`'s shape): filesystem read + dict work only, no DB session, no
computation. It RECOMPUTES NOTHING — every verdict field is re-displayed exactly as the referee wrote it.

  - `resolve_staging_ledger_path()` — the staging ledger's path: the `STAGING_LEDGER_PATH` env override
    (the SAME literal name `run-goal.sh` already exports and `project-extensions/gates/verify_claim.py`
    already reads — deliberately NOT a new `TRENDORA_STAGING_LEDGER_PATH` name), else
    `config.evidence.staging_ledger_path` resolved against `REPO_ROOT`. Mirrors
    `app.engine.evidence.resolve_ledger_path()` exactly, for the staging side.
  - `build_graveyard_payload()` — reads BOTH ledgers (canonical via the EXISTING
    `app.engine.evidence.resolve_ledger_path()`; staging via `resolve_staging_ledger_path()` above),
    excludes forward-walk monitoring records, filters to NON-PASS verdicts (`FAIL` / `INSUFFICIENT`,
    status-driven — never a hardcoded count), tags each entry with its origin ledger, re-displays the
    deflation context (`verdict.deflation` / `verdict.deflation_divisor`) verbatim, and attaches
    registration lineage via the SAME `app.engine.registry.match_registration` the J-18 gate/registry-page
    use (reused, never reimplemented — a second selector-matcher is the exact failure mode B-902 calls
    out). A missing/empty ledger degrades to an empty graveyard, never a crash.
  - `REVISIT_PROTOCOL` — a single served constant (the B-406/§0 rule text) so every page/consumer reads
    the SAME re-test policy; carries no proven-language.

One deliberate contract evolution (logged in the iter-31 blueprint clarification): the iter-9/10/12
"staging ledger is internal-only, never served" invariant is NARROWED here — the staging ledger's NON-PASS
verdicts become browsable (the graveyard's whole purpose). The honesty fence stays intact: this module
shows ONLY non-PASS entries (staging carries 0 PASS rows today, and even if it ever did, a PASS entry is
filtered OUT here, never surfaced as proven), and it never touches `app.engine.evidence`,
`build_evidence_payload`, `proven_signals`, or either ledger's write path — read-only, always.
"""
from __future__ import annotations

import os
from pathlib import Path

from app.config import REPO_ROOT, get_config
from app.engine import evidence as evidence_mod
from app.engine.ledger import FORWARD_WALK_TYPE, read_entries
from app.engine.referee import STATUS_PASS
from app.engine.registry import load_registrations, match_registration

# The environment-variable NAME (the NAME only — never a path VALUE literal in code) the runtime staging
# ledger path may be overridden with. The SAME literal `run-goal.sh` exports and `verify_claim.py` reads
# (project-extensions/gates/verify_claim.py `_LEDGER_ENV["staging"]`) — deliberately reused rather than a
# new `TRENDORA_STAGING_LEDGER_PATH` name, since the harness never sets one.
STAGING_LEDGER_PATH_ENV = "STAGING_LEDGER_PATH"

# The two ledger-origin tags a graveyard entry may carry. Local literals (not imported from `app.mcp.tools`,
# which sits above the engine layer) — mirrors how `app.engine.ledger._PASS_STATUS` mirrors
# `app.engine.referee.STATUS_PASS` "so this module stays engine-free."
LEDGER_CANONICAL = "canonical"
LEDGER_STAGING = "staging"

# The re-test policy (backlog B-406 / §0), served as a single constant so every consumer (the graveyard
# page's panel, any future reader) agrees on the SAME wording. Descriptive governance text — NO
# proven-language (this is never a "Proven"/"Not yet proven" signal).
REVISIT_PROTOCOL: dict = {
    "rule": (
        "A referee FAIL/INSUFFICIENT is final for that hypothesis; a re-test requires a materially "
        "changed precondition (a new data span covering ≥2 additional OOS years, a data-basis "
        "change, or a genuinely different hypothesis) and must be registered as a NEW candidate citing "
        "the closed verdict."
    ),
}


def resolve_staging_ledger_path() -> str:
    """The staging ledger path: the `STAGING_LEDGER_PATH` env override if set, else
    `config.evidence.staging_ledger_path` resolved against `REPO_ROOT` when relative.

    This MUST resolve to the SAME file the post-decompose gate writes staging verdicts to (set by
    `run-goal.sh` alongside `LEDGER_PATH`/`TRENDORA_REGISTRY_PATH`), so the graveyard's staging rows are
    consistent with what the referee actually explored. No path literal lives here — the default lives in
    config (anti-goal: No magic numbers). Mirrors `app.engine.evidence.resolve_ledger_path()` exactly."""
    override = os.environ.get(STAGING_LEDGER_PATH_ENV)
    if override:
        return override
    configured = Path(get_config().evidence.staging_ledger_path)
    if not configured.is_absolute():
        configured = REPO_ROOT / configured
    return str(configured)


def _graveyard_row(entry: dict, ledger: str, registrations: list[dict]) -> dict:
    """Project ONE non-PASS ledger entry into a read-only graveyard row — read VERBATIM (nothing is
    recomputed). `lineage` is the matched registry row (or `None` for an honest unregistered selector-set),
    resolved via the SAME `registry.match_registration` the gate/registry-page use."""
    claim = entry.get("claim") if isinstance(entry.get("claim"), dict) else {}
    verdict = entry.get("verdict") if isinstance(entry.get("verdict"), dict) else {}
    return {
        "ledger": ledger,
        "claim": claim,                                    # the hypothesis (cohort selectors), verbatim
        "register_date": entry.get("register_date"),
        "horizon": entry.get("horizon"),
        "cohort_n": entry.get("cohort_n"),
        "control_n": entry.get("control_n"),
        "verdict": verdict,                                # status + reason + deflation context, verbatim
        "lineage": match_registration(claim, registrations=registrations),
    }


def _non_pass_rows(ledger_path: str, ledger: str, registrations: list[dict]) -> list[dict]:
    """Every NON-PASS, non-forward-walk entry in `ledger_path`, tagged `ledger` and lineage-attached.
    Status-driven (`verdict.status != PASS`), never a hardcoded count — a future PASS row disappears from
    this list automatically. A missing/empty file yields `read_entries`' own empty list (no crash)."""
    rows: list[dict] = []
    for entry in read_entries(ledger_path):
        if not isinstance(entry, dict) or entry.get("type") == FORWARD_WALK_TYPE:
            continue
        verdict = entry.get("verdict") if isinstance(entry.get("verdict"), dict) else {}
        if verdict.get("status") == STATUS_PASS:
            continue
        rows.append(_graveyard_row(entry, ledger, registrations))
    return rows


def build_graveyard_payload(canonical_path: str | None = None, staging_path: str | None = None) -> dict:
    """Compose the read-only `/api/research/graveyard` payload: `{"entries": [...], "revisit_protocol":
    {...}}`. `canonical_path` defaults to `app.engine.evidence.resolve_ledger_path()`; `staging_path`
    defaults to `resolve_staging_ledger_path()` — the endpoint's real, no-argument call shape. A test may
    pass explicit fixture paths instead (mirrors `app.engine.registry.load_registrations`'s optional-path
    pattern).

    `entries` is every NON-PASS (`FAIL` / `INSUFFICIENT`) entry from BOTH ledgers, forward-walk monitoring
    records excluded, each tagged with its origin ledger and lineage-attached via the SAME
    `registry.match_registration` the gate/registry-page use (loaded ONCE here and passed through, so a
    14-row graveyard does not re-read the registry file per entry). A missing/empty ledger (either or both)
    degrades to fewer/zero entries, never a crash (anti-goal: resilience to data-shape change)."""
    resolved_canonical = canonical_path if canonical_path is not None else evidence_mod.resolve_ledger_path()
    resolved_staging = staging_path if staging_path is not None else resolve_staging_ledger_path()
    registrations = load_registrations()
    entries = _non_pass_rows(resolved_canonical, LEDGER_CANONICAL, registrations) + _non_pass_rows(
        resolved_staging, LEDGER_STAGING, registrations
    )
    return {"entries": entries, "revisit_protocol": REVISIT_PROTOCOL}
