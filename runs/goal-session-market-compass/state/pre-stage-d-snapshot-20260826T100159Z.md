# Emergency recovery snapshot — taken before J-11 Stage D

**Classification: OWNER DISASTER-RECOVERY ARTIFACT.**
This is NOT the J-11 rollback or retry mechanism. On an ordinary Stage D/E/F/G
failure, follow the existing whole-attempt retry semantics in `docs/goal.md`.
Do NOT automatically restore this snapshot, and do NOT use its existence to
weaken any Stage G acceptance gate. Restoring it is an owner decision only.

## Identity

| Field | Value |
|---|---|
| Timestamp (UTC) | 2026-08-26T10:01:59Z |
| Source DB path | /home/dennis-chan/Git/trendora/apps/backend/data/trendora.db |
| Backup path | /home/dennis-chan/trendora-db-snapshots/trendora-pre-j11-stage-d-20260826T100159Z.db |
| Source byte size | 8365871104 |
| Backup byte size | 8365871104 |
| Backup SHA256 | c5629989afe2e17862bbf6636b6dfd48a2fcfda30ad4a4e0770dc43cb7e5ec52 |
| Method | SQLite Online Backup API — `sqlite3 "file:<src>?mode=ro" ".backup '<dest>'"` |
| Session | goal-session-market-compass, iteration 19 |
| Git HEAD | 5fe72f5c (goal(market-compass): authorize J-11 Stage D -> G recovery execution) |

## Pre-flight state (verified before the snapshot)

- Backend and frontend OFF — nothing listening on :8000 or :3000.
- No Data Manager, browser-QA, replay, demo-runner or playwright process running.
- No process holding the DB open (`lsof` reports no holders).
- `journal_mode = wal`; `PRAGMA wal_checkpoint` returned `0|0|0` (WAL empty,
  nothing to checkpoint). `trendora.db-wal` was 0 bytes on disk.
- The application was NOT booted to make this backup.
- Run carried `CHAIN_MAINTENANCE_ISOLATION=true` and `CHAIN_REQUIRE_FULL_DEPTH=true`.

## Verification

- **SQLite integrity check on the backup: `ok`** (`PRAGMA integrity_check`, 50s).
- Logical equivalence source vs backup:
  - tables: 25 == 25
  - scanner_runs: 3117 == 3117
  - daily_prices: 3310374 == 3310374
  - maintenance_boundaries: 1 == 1
  - schema digest (sha256 over sqlite_master name+sql):
    `cd5b595b7a0ef484960722a4c950468183a26220db61fae28017f7772af3341b` — MATCH.

Note: the backup's whole-file SHA256 differs from the source's. This is expected
and not a defect — the Online Backup API writes a fresh page layout rather than
copying bytes. Logical identity is established by the integrity check, the row
counts and the schema digest above.

## Zero-mutation confirmation for the live DB

| | Before | After |
|---|---|---|
| SHA256 | f9869920323cfbd4d2dfef8e5a2dff185540ca714a5559110ff5c7586acb4ddd | f9869920323cfbd4d2dfef8e5a2dff185540ca714a5559110ff5c7586acb4ddd |
| Byte size | 8365871104 | 8365871104 |
| mtime | 2026-08-26 00:49:26.627290732 +0100 | 2026-08-26 00:49:26.627290732 +0100 |
| `-wal` size / mtime | 0 / 00:49:31.894081799 | 0 / 00:49:31.894081799 |

**Whole-file SHA256 of the live database is byte-identical before and after.
Creating this backup caused zero mutation to the live DB.**

Full disclosure: `trendora.db-shm` (the WAL shared-memory index, 32768 bytes) has
an updated mtime (was 01:47:15, now 11:02:52). The read-only connection touched
that sidecar. Its size is unchanged, it holds no database content, it is rebuilt
from scratch on next open, and the main database file and the WAL are both
byte-identical. This does not affect database content.
