"""Migrate bare collected_at timestamps to include Pacific timezone offset.

Older rows in vessel_snapshots and sailing_space_snapshots store collected_at
as bare ISO timestamps in Pacific local time (no offset suffix). This script
adds the correct -07:00 (PDT) or -08:00 (PST) suffix based on the date,
so all timestamps are unambiguous.

Usage:
    python scripts/migrate_collected_at_tz.py          # dry-run
    python scripts/migrate_collected_at_tz.py --apply  # actually update
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Allow running as a script from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import get_connection, init_db

PACIFIC = ZoneInfo("America/Los_Angeles")

TABLES = ["vessel_snapshots", "sailing_space_snapshots"]

BATCH_SIZE = 50_000


def pacific_offset(iso_str: str) -> str:
    """Return the Pacific timezone offset (-07:00 or -08:00) for a bare timestamp."""
    dt = datetime.fromisoformat(iso_str).replace(tzinfo=PACIFIC)
    offset = dt.strftime("%z")  # e.g. "-0700"
    return offset[:3] + ":" + offset[3:]  # e.g. "-07:00"


def migrate_table(conn, table: str, dry_run: bool) -> int:
    cur = conn.execute(
        f"""
        SELECT COUNT(*) FROM {table}
        WHERE collected_at NOT LIKE '%-07:00' AND collected_at NOT LIKE '%-08:00'
        """
    )
    total = cur.fetchone()[0]
    if total == 0:
        print(f"  {table}: no rows to migrate")
        return 0

    print(f"  {table}: {total:,} rows to migrate")

    if dry_run:
        # Show a few examples
        cur = conn.execute(
            f"""
            SELECT rowid, collected_at FROM {table}
            WHERE collected_at NOT LIKE '%-07:00' AND collected_at NOT LIKE '%-08:00'
            LIMIT 5
            """
        )
        for row in cur.fetchall():
            offset = pacific_offset(row[1])
            print(f"    {row[1]} → {row[1]}{offset}")
        return total

    updated = 0
    while updated < total:
        rows = conn.execute(
            f"""
            SELECT rowid, collected_at FROM {table}
            WHERE collected_at NOT LIKE '%-07:00' AND collected_at NOT LIKE '%-08:00'
            LIMIT {BATCH_SIZE}
            """
        ).fetchall()

        if not rows:
            break

        updates = []
        for rowid, collected_at in rows:
            offset = pacific_offset(collected_at)
            updates.append((collected_at + offset, rowid))

        conn.executemany(
            f"UPDATE {table} SET collected_at = ? WHERE rowid = ?", updates
        )
        conn.commit()
        updated += len(rows)
        print(f"    {updated:,}/{total:,} rows updated...")

    return updated


def main():
    parser = argparse.ArgumentParser(
        description="Add timezone offset to bare collected_at timestamps"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Actually update the database"
    )
    args = parser.parse_args()

    dry_run = not args.apply
    if dry_run:
        print("DRY RUN — pass --apply to update the database\n")
    else:
        print("APPLYING MIGRATION\n")

    init_db()
    conn = get_connection()

    try:
        for table in TABLES:
            count = migrate_table(conn, table, dry_run)
            if count and not dry_run:
                print(f"  {table}: {count:,} rows migrated")
    finally:
        conn.close()

    if dry_run:
        print("\nNo changes made. Run with --apply to update.")
    else:
        print("\nDone.")


if __name__ == "__main__":
    main()
