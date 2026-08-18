"""
Prompt: "read this CSV" / "stream a file without pandas"

Run: python examples/cookbook/read_file.py [path]
"""

from __future__ import annotations

import sys

from iterable import open_iterable


def main(path: str = "data.csv", limit: int = 5) -> list[dict]:
    rows: list[dict] = []
    with open_iterable(path) as source:
        for i, row in enumerate(source):
            if i >= limit:
                break
            rows.append(row)
            print(row)
    return rows


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data.csv")
