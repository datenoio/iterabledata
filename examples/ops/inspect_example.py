"""
Example: Inspect dataset – count, head, tail.

Uses iterable.ops.inspect: count(), head(), tail().
Run: python examples/ops/inspect_example.py [path/to/data.csv]
"""

import sys

from iterable.ops import inspect as inspect_ops


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data.csv"
    try:
        total = inspect_ops.count(path, engine="duckdb")
    except Exception:
        total = inspect_ops.count(path)
    print(f"Count (total rows): {total}")

    print("\nHead (first 5 rows):")
    for row in inspect_ops.head(path, n=5):
        print(row)

    print("\nTail (last 3 rows):")
    for row in inspect_ops.tail(path, n=3):
        print(row)


if __name__ == "__main__":
    main()
