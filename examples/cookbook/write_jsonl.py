"""
Prompt: "write these records to jsonl"

Run: python examples/cookbook/write_jsonl.py [output]
"""

from __future__ import annotations

import sys

from iterable import open_iterable

DEFAULT_ROWS = [
    {"id": 1, "name": "Ada"},
    {"id": 2, "name": "Grace"},
]


def main(path: str = "output.jsonl", rows: list[dict] | None = None) -> str:
    records = rows if rows is not None else DEFAULT_ROWS
    with open_iterable(path, mode="w") as dest:
        for row in records:
            dest.write(row)
    print(f"Wrote {path}")
    return path


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "output.jsonl")
