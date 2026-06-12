"""
Example: Ingest a file into PostgreSQL using to_db.

Uses iterable.ingest.to_db with dbtype=postgresql.
Run: python examples/ingest/to_db_postgresql.py [path/to/data.csv] [postgresql://...]
"""

import os
import sys

from iterable.ingest import to_db


def main():
    data_path = sys.argv[1] if len(sys.argv) > 1 else "data.csv"
    db_url = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("DB_URL", "postgresql://localhost:5432/testdb")
    table = "ingest_example"

    if not os.path.isfile(data_path):
        print(f"Data file not found: {data_path}. Create a CSV/JSONL or pass path.")
        return

    print(f"Ingesting {data_path} into PostgreSQL table {table}")
    try:
        result = to_db(
            data_path,
            db_url=db_url,
            table=table,
            dbtype="postgresql",
            mode="insert",
            batch=1000,
            create_table=False,
        )
        print(f"Rows processed: {result.rows_processed}, inserted: {result.rows_inserted}")
        if result.errors:
            print(f"Errors: {result.errors[:5]}")
    except Exception as e:
        print(f"Error: {e}. Ensure PostgreSQL is running and DB_URL is correct.")


if __name__ == "__main__":
    main()
