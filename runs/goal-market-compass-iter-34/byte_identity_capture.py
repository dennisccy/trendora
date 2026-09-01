#!/usr/bin/env python3
"""byte_identity_capture.py -- goal-market-compass iter-33 (TC-5): capture GET /api/compass and
GET /api/dashboard response bytes across the authorized 7-value as-of set, before and after the
J-09 bar-cache-bound code change, so the two capture directories can be diffed byte-for-byte.

The authorized as-of set (BACKGROUND, docs/phases/goal-market-compass-iter-33.md): the union every
stored golden actually uses -- {no param (frontier), "2026-08-12", "1996-02-01", "2025-04-15",
"2026-03-30", "2026-07-23", "2026-08-03", "2026-08-11"}. All 7 are already among the 18 distinct
as_of values in next_session_manifests (re-derived read-only at iter-32) so no call at any of them
can mint a new manifest row.

Usage: python3 byte_identity_capture.py <base_url> <out_dir>
Writes one file per (endpoint, as_of) pair: <out_dir>/<endpoint>__<as_of_or_frontier>.bin
"""
import os
import sys
import urllib.error
import urllib.request

AS_OF_VALUES = [
    None, "2026-08-12", "1996-02-01", "2025-04-15", "2026-03-30", "2026-07-23", "2026-08-03",
    "2026-08-11",
]
ENDPOINTS = ["/api/compass", "/api/dashboard"]


def main():
    base_url = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    for endpoint in ENDPOINTS:
        for as_of in AS_OF_VALUES:
            label = as_of if as_of else "frontier"
            url = base_url + endpoint + (f"?as_of={as_of}" if as_of else "")
            fname = os.path.join(out_dir, f"{endpoint.strip('/').replace('/', '_')}__{label}.bin")
            try:
                with urllib.request.urlopen(url, timeout=15) as resp:
                    body = resp.read()
                    status = resp.status
            except urllib.error.HTTPError as exc:
                body = exc.read()
                status = exc.code
            with open(fname, "wb") as fh:
                fh.write(body)
            print(f"{url} -> status={status} bytes={len(body)} -> {fname}")


if __name__ == "__main__":
    main()
