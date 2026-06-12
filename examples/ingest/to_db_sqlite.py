"""
Example: Ingest a file into SQLite using to_db.

Uses iterable.ingest.to_db with dbtype=sqlite.
Run: python examples/ingest/to_db_sqlite.py [path/to/data.csv] [path/to/db.sqlite]
"""

import os
import sys

from iterable.ingest import to_db


def main():
    data_path = sys.argv[1] if len(sys.argv) > 1 else "data.csv"
    db_path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/ingest_example.sqlite"
    table = "ingest_example"

    if not os.path.isfile(data_path):
        print(f"Data file not found: {data_path}. Create a CSV/JSONL or pass path.")
        return

    print(f"Ingesting {data_path} into SQLite table {table} at {db_path}")
    result = to_db(
        data_path,
        db_url=db_path,
        table=table,
        dbtype="sqlite",
        mode="insert",
        batch=1000,
        create_table=True,
    )
    print(f"Rows processed: {result.rows_processed}, inserted: {result.rows_inserted}")
    if result.errors:
        print(f"Errors: {result.errors[:5]}")


if __name__ == "__main__":
    main()
