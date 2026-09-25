#!/usr/bin/env python
"""
Load seed data into NomadNet's configured database (whatever DATABASE_URL
points at - local SQLite or production Postgres) for UI testing.
Wipes existing rows in dependency order, then loads seed_data.sql.
"""

import sys
from pathlib import Path

from app import app, db

TABLES_IN_DELETE_ORDER = [
    "notification", "\"like\"", "comment", "location_follow", "follow",
    "post_media", "post", "location", "\"user\"", "country",
]


def load_seed_data():
    sql_path = Path("seed_data.sql")

    if not sql_path.exists():
        print(f"❌ Error: {sql_path} not found")
        return False

    with app.app_context():
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        is_sqlite = db.engine.dialect.name == "sqlite"

        try:
            print("\U0001F9F9 Clearing existing data...")
            for table in TABLES_IN_DELETE_ORDER:
                cursor.execute(f"DELETE FROM {table}")
            conn.commit()

            print("\U0001F4E5 Loading seed data...")
            sql_script = sql_path.read_text()

            if is_sqlite:
                # sqlite3's cursor.execute() only runs the first statement in
                # a multi-statement string - executescript() is needed to run
                # the whole file in one call.
                cursor.executescript(sql_script)
            else:
                # psycopg2 (Postgres) runs a full semicolon-separated script
                # through a normal execute() call.
                cursor.execute(sql_script)

            conn.commit()

            print("\n✅ Seed data loaded successfully!\n")

            print("=" * 60)
            print("DATABASE SUMMARY")
            print("=" * 60)

            cursor.execute("SELECT COUNT(*) FROM \"user\"")
            print(f"\n\U0001F465 Users: {cursor.fetchone()[0]}")

            cursor.execute("SELECT COUNT(*) FROM location")
            print(f"\U0001F4CD Locations: {cursor.fetchone()[0]}")

            cursor.execute("SELECT COUNT(*) FROM post")
            print(f"\U0001F4DD Posts: {cursor.fetchone()[0]}")

            cursor.execute("SELECT COUNT(*) FROM post_media")
            print(f"\U0001F5BC️  Post media: {cursor.fetchone()[0]}")

            cursor.execute("SELECT COUNT(*) FROM \"like\"")
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

            return True

        except Exception as e:
            conn.rollback()
            print(f"❌ Error loading seed data: {e}")
            return False

        finally:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    success = load_seed_data()
    sys.exit(0 if success else 1)
