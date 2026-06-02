"""Rewrite config.yaml's universe.symbols + stock_sectors + (pruned) themes from the committed screen
record (data/seed/universe.json). One-shot, DEV-RUN after `screen_universe.py --screen`.

The universe is now the config-recorded SCREEN result: this script makes config.yaml reflect the
resolved members (single source). It preserves every section header/comment OUTSIDE the three
generated blocks; only the machine-generated lists (the symbol list, the stock→sector map, and the
theme baskets pruned to surviving members) are replaced. Themes keep their slugs; a member that the
screen dropped is removed from its baskets so the existing `config.py` validation (every theme member
in the universe) holds. After writing, it re-loads + validates the config and prints a summary.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/apply_universe_to_config.py
    apps/backend/.venv/bin/python apps/backend/scripts/apply_universe_to_config.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
CONFIG_PATH = REPO_ROOT / "config.yaml"
UNIVERSE_JSON = BACKEND_DIR / "data" / "seed" / "universe.json"

sys.path.insert(0, str(BACKEND_DIR))
from app.config import load_config  # noqa: E402


def _q(ticker: str) -> str:
    """Quote a ticker only when bare YAML would misparse it (e.g. 'ON' -> True). Matches the existing
    config style (only the ambiguous ones are quoted)."""
    return f'"{ticker}"' if yaml.safe_load(ticker) != ticker else ticker


def _replace_block(lines: list[str], key: str, new_block: list[str]) -> list[str]:
    """Replace the lines AFTER the `key` line up to (not including) the next column-0 `#` comment with
    `new_block`. Used for the `  symbols:`, `themes:`, and `stock_sectors:` sections — each is bounded
    below by the next `# ----` divider, so section headers/comments are preserved."""
    try:
        start = next(i for i, line in enumerate(lines) if line.rstrip("\n") == key)
    except StopIteration as exc:
        raise SystemExit(f"anchor {key!r} not found in config.yaml") from exc
    end = start + 1
    while end < len(lines) and not lines[end].startswith("#"):
        end += 1
    return lines[: start + 1] + new_block + lines[end:]


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply universe.json screen result to config.yaml.")
    parser.add_argument("--dry-run", action="store_true", help="print the summary; do not write config.yaml")
    args = parser.parse_args()

    if not UNIVERSE_JSON.exists():
        raise SystemExit(f"{UNIVERSE_JSON} not found — run screen_universe.py --screen first")
    record = json.loads(UNIVERSE_JSON.read_text())
    members = record["members"]
    sector_by_symbol = {m["symbol"]: m["sector"] for m in members}
    symbols = sorted(sector_by_symbol)

    raw = yaml.safe_load(CONFIG_PATH.read_text())
    universe_set = set(symbols)
    themes_in = raw["themes"]
    pruned_themes: dict[str, list[str]] = {
        slug: [m for m in members_ if m in universe_set] for slug, members_ in themes_in.items()
    }
    empty_themes = [slug for slug, ms in pruned_themes.items() if not ms]
    dropped_members = sorted(
        {m for ms in themes_in.values() for m in ms} - universe_set
    )

    # Build the three generated blocks (preserving the surrounding comments / dividers).
    symbols_block = ["    # Resolved screen passers — generated from data/seed/universe.json by\n",
                     "    # scripts/apply_universe_to_config.py (the config-recorded screen result). Do not hand-edit.\n"]
    symbols_block += [f"    - {_q(s)}\n" for s in symbols]

    themes_block = [f"  {slug}: [{', '.join(_q(m) for m in ms)}]\n"
                    for slug, ms in pruned_themes.items()]

    sectors_block = ["  # Generated from data/seed/universe.json (every universe member -> its GICS sector).\n"]
    sectors_block += [f"  {_q(s)}: {sector_by_symbol[s]}\n" for s in symbols]

    lines = CONFIG_PATH.read_text().splitlines(keepends=True)
    lines = _replace_block(lines, "  symbols:", symbols_block)
    lines = _replace_block(lines, "themes:", themes_block)
    lines = _replace_block(lines, "stock_sectors:", sectors_block)
    new_text = "".join(lines)

    print(f"[apply] resolved universe: {len(symbols)} members")
    print(f"[apply] themes pruned; dropped {len(dropped_members)} prior theme members not in the screen "
          f"universe: {dropped_members[:20]}{' ...' if len(dropped_members) > 20 else ''}")
    if empty_themes:
        print(f"[apply] WARNING: themes left empty by pruning (will fail validation): {empty_themes}")

    if args.dry_run:
        print("[apply] --dry-run: config.yaml NOT written.")
        return 0

    CONFIG_PATH.write_text(new_text)
    # Validate the rewritten config loads (single source intact; every invariant holds).
    cfg = load_config(CONFIG_PATH)
    assert len(cfg.universe.symbols) == len(symbols), "universe.symbols count mismatch after rewrite"
    assert set(cfg.stock_sectors) >= universe_set, "stock_sectors missing some universe members"
    print(f"[apply] config.yaml rewritten + re-validated: {len(cfg.universe.symbols)} universe symbols, "
          f"{len(cfg.themes)} themes, every member sector + theme-membership invariant holds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
