"""
Prompt: "filter rows where name equals Mary" / "keep rows matching a condition"

Run: python examples/cookbook/filter_rows.py [path] [field] [value]
"""

from __future__ import annotations

import sys

from iterable import open_iterable


def main(path: str = "data.csv", field: str = "name", value: str = "Mary") -> list[dict]:
    kept: list[dict] = []
    with open_iterable(path) as source:
        for row in source:
            if str(row.get(field)) == value:
                kept.append(row)
                print(row)
    return kept


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data.csv"
    field = sys.argv[2] if len(sys.argv) > 2 else "name"
    value = sys.argv[3] if len(sys.argv) > 3 else "Mary"
    main(path, field=field, value=value)
