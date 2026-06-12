# Ingest examples

Load data from files (or iterables) into databases using `iterable.ingest.to_db`.

## Scripts

- **to_db_postgresql.py** – Ingest a CSV/JSONL file into a PostgreSQL table.
- **to_db_sqlite.py** – Ingest a CSV/JSONL file into a SQLite table.

## Run

1. Ensure the database is running and the target table exists (or use `create_table=True`).
2. Pass source file and (optionally) connection URL as arguments or set defaults in the script.

```bash
# SQLite (file-based, no server needed)
python examples/ingest/to_db_sqlite.py data.csv

# PostgreSQL (set DB_URL or pass as second arg)
python examples/ingest/to_db_postgresql.py data.csv postgresql://user:pass@localhost:5432/mydb
```

## API

```python
from iterable import ingest

result = ingest.to_db(
    "data.csv",
    db_url="postgresql://user:pass@localhost:5432/mydb",
    table="my_table",
    dbtype="postgresql",
    mode="insert",       # or "upsert"
    upsert_key="id",    # for upsert
    batch=5000,
    create_table=False,
)
print(result.rows_inserted, result.rows_processed)
```

Supported `dbtype`: `postgresql`, `sqlite`, `duckdb`, `mysql`, `mongodb`, `elasticsearch`.
