"""
Example: Read from PostgreSQL as an iterable.

Uses open_iterable(..., engine="postgres") with iterableargs (table or query).
Run: python examples/db/read_postgresql.py [postgresql://user:pass@host:5432/dbname]
"""

import os
import sys

from iterable import open_iterable


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DATABASE_URL", "postgresql://localhost:5432/postgres")
    with open_iterable(
        url,
        engine="postgres",
        iterableargs={
            "query": "SELECT * FROM pg_catalog.pg_tables LIMIT 10",
        },
    ) as source:
        print("Reading from PostgreSQL (pg_tables sample)")
        for i, row in enumerate(source):
            print(row)
            if i >= 4:
                print("... (first 5 rows)")
                break
    print("Done.")


if __name__ == "__main__":
    main()
