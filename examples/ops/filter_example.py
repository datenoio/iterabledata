"""
Example: Filter rows by expression and regex search.

Uses iterable.ops.filter: filter_expr() and search().
Run: python examples/ops/filter_example.py [path/to/data.csv]
"""

import sys

from iterable.helpers.detect import open_iterable
from iterable.ops import filter as filter_ops


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data.csv"
    try:
        with open_iterable(path) as source:
            rows = list(source)
    except FileNotFoundError:
        print(f"File not found: {path}. Using minimal demo data.")
        rows = [
            {"id": 1, "status": "active", "price": 99.5},
            {"id": 2, "status": "inactive", "price": 10.0},
            {"id": 3, "status": "active", "price": 150.0},
        ]

    print("--- filter_expr: status == 'active' and price > 50 ---")
    for row in filter_ops.filter_expr(rows, "`status` == 'active' and `price` > 50"):
        print(row)

    print("\n--- search: pattern 'active' in any field ---")
    for row in filter_ops.search(rows, "active"):
        print(row)


if __name__ == "__main__":
    main()
