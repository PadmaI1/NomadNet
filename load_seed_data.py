#!/usr/bin/env python
"""
Load seed data into NomadNet database for UI testing.
Wipes existing rows in dependency order, then loads seed_data.sql in one
executescript() call so multi-statement SQL (with semicolons inside string
literals) is handled correctly.
"""

import sqlite3
import sys
from pathlib import Path

TABLES_IN_DELETE_ORDER = [
    "notification", "like", "comment", "location_follow", "follow",
    "post_media", "post", "location", "user", "country",
]


def load_seed_data():
    db_path = Path("instance/nomadnet.db")
    sql_path = Path("seed_data.sql")

    if not sql_path.exists():
        print(f"❌ Error: {sql_path} not found")
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        print("\U0001F9F9 Clearing existing data...")
        for table in TABLES_IN_DELETE_ORDER:
            cursor.execute(f"DELETE FROM {table}")
        conn.commit()

        print("\U0001F4E5 Loading seed data...")
        with open(sql_path, "r") as f:
            sql_script = f.read()

        cursor.executescript(sql_script)
        conn.commit()

        print("\n✅ Seed data loaded successfully!\n")

        print("=" * 60)
        print("DATABASE SUMMARY")
        print("=" * 60)

        cursor.execute("SELECT COUNT(*) FROM user")
        print(f"\n\U0001F465 Users: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM location")
        print(f"\U0001F4CD Locations: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM post")
        print(f"\U0001F4DD Posts: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM post_media")
        print(f"\U0001F5BC️  Post media: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM like")
        print(f"\U0001F44D Likes: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM comment")
        print(f"\U0001F4AC Comments: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM follow")
        print(f"\U0001F517 User follows: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM location_follow")
        print(f"\U0001F4CC Location follows: {cursor.fetchone()[0]}")

        print("\n" + "=" * 60)
        print("\U0001F389 DATA READY FOR UI TESTING")
        print("=" * 60)
        print("\nAll seeded accounts share the password: NomadNet2026!")
        print("Start the app: python app.py")
        print("Visit: http://localhost:5000\n")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error loading seed data: {e}")
        return False


if __name__ == "__main__":
    success = load_seed_data()
    sys.exit(0 if success else 1)
