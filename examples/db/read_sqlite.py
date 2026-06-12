"""
Example: Read from SQLite as an iterable.

Uses open_iterable(..., engine="sqlite") with iterableargs (table or query).
Run: python examples/db/read_sqlite.py [path/to/db.sqlite]
"""

import sys

from iterable.helpers.detect import open_iterable


def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/example.sqlite"
    with open_iterable(
        db_path,
        engine="sqlite",
        iterableargs={"table": "sqlite_master"},
    ) as source:
        print(f"Reading from SQLite: {db_path} (table: sqlite_master)")
        for i, row in enumerate(source):
            print(row)
            if i >= 4:
                print("... (first 5 rows)")
                break
    print("Done.")


if __name__ == "__main__":
    main()
