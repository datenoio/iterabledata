"""
Prompt: "read this file in batches" / "process CSV in chunks"

Run: python examples/cookbook/read_bulk.py [path]
"""

from __future__ import annotations

import sys

from iterable import open_iterable


def main(path: str = "data.csv", batch_size: int = 2) -> list[list[dict]]:
    batches: list[list[dict]] = []
    with open_iterable(path) as source:
        while True:
            chunk = source.read_bulk(num=batch_size)
            if not chunk:
                break
            batches.append(chunk)
            print(f"batch {len(batches)}: {len(chunk)} rows")
    return batches


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data.csv")
