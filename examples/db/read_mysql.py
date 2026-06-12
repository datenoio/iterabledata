"""
Example: Read from MySQL as an iterable.

Uses open_iterable(..., engine="mysql") with iterableargs (table or query).
Run: python examples/db/read_mysql.py [mysql://user:pass@host:3306/dbname]
"""

import os
import sys

from iterable.helpers.detect import open_iterable


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("MYSQL_URL", "mysql://localhost:3306/mysql")
    with open_iterable(
        url,
        engine="mysql",
        iterableargs={
            "query": "SELECT 1 AS n UNION SELECT 2 UNION SELECT 3",
        },
    ) as source:
        print("Reading from MySQL (simple query)")
        for row in source:
            print(row)
    print("Done.")


if __name__ == "__main__":
    main()
