# Database reading examples

Read from SQL and NoSQL databases as iterables using `open_iterable(..., engine=...)`.

## Scripts

- **read_sqlite.py** – Iterate over a SQLite table.
- **read_postgresql.py** – Iterate over a PostgreSQL table (or query).
- **read_mysql.py** – Iterate over a MySQL table (or query).

## Run

1. Ensure the database is running and has data.
2. Set connection URL (or edit defaults in the script).

```bash
# SQLite (file path as URL)
python examples/db/read_sqlite.py /path/to/db.sqlite

# PostgreSQL
python examples/db/read_postgresql.py postgresql://user:pass@localhost:5432/mydb

# MySQL
python examples/db/read_mysql.py mysql://user:pass@localhost:3306/mydb
```

## API

```python
from iterable.helpers.detect import open_iterable

with open_iterable(
    "postgresql://user:pass@localhost:5432/mydb",
    engine="postgres",
    iterableargs={"table": "users", "query": "SELECT * FROM users LIMIT 10"},
) as source:
    for row in source:
        print(row)
```

Engines: `postgres`/`postgresql`, `sqlite`, `mysql`/`mariadb`, `mongo`/`mongodb`, `elasticsearch`, `mssql`/`sqlserver`, `clickhouse`.
