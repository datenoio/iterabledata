"""
Prompt: "how many rows in this file" / "count records in CSV"

Run: python examples/cookbook/count_rows.py [path]
"""

from __future__ import annotations

import sys

from iterable import open_iterable


def main(path: str = "data.csv") -> int:
    with open_iterable(path) as source:
        total = source.totals()
    print(f"rows: {total}")
    return total


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data.csv")
